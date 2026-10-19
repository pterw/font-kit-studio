"""Proxy mode of scripts/serve.py: the real script as a process in front of a small fake app."""

import base64
import contextlib
import errno
import gzip
import hashlib
import http.client
import io
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
import unittest.mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import REPO  # noqa: E402
from test_preview_server import free_ports, load_serve, request  # noqa: E402

SERVE = REPO / 'scripts' / 'serve.py'
CASES = REPO / 'tests' / 'fixtures' / 'proxy-insert-cases.json'
LIMIT = 8 * 1024 * 1024
BRIDGE_PATH = '/@fontkit/fontkit-bridge.js'
REFUSAL = 'serve.py: Font Kit Studio proxies only a local dev server (localhost, 127.0.0.1 or [::1])'
PLAIN_LINE = ('serve.py: the demo app needs the repository. To edit your own app, pass its address: '
              'python serve.py http://127.0.0.1:5000')
MISSING_LINE = ('serve.py: cannot find fontkit-studio.html or fontkit-bridge.js next to serve.py '
                'or in the repository')
PAGE = (b'<!doctype html><html><head><meta charset="utf-8"><title>caf\xc3\xa9</title></head>'
        b'<body>caf\xc3\xa9 \xff</body></html>')
CSS = b'a:before{content:"<head>"}'
GZIPPED = gzip.compress(PAGE, mtime=0)
CHUNKS = (b'<html><head><title>one', b'</title></head><body>two</body></html>')
BIG_EXACT = b'<head>' + b'x' * (LIMIT - 6)
BIG_OVER = b'<head>' + b'x' * (LIMIT - 5)
CSP_NONE = ('Content-Security-Policy', "script-src 'none'")
CSP_META = (b'<!doctype html><html><head><meta http-equiv="Content-Security-Policy" '
            b'content="default-src \'none\'"><title>meta</title></head><body>x</body></html>')
OWN_BRIDGE = (b'<!doctype html><html><head><script src="/vendor/fontkit-bridge.js"></script>'
              b'<title>own</title></head><body>x</body></html>')
CSP_MESSAGE = ("Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the "
               "page's own scripts). Add 'self' to script-src while you develop.")
BRIDGE_TWICE_MESSAGE = ('Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not '
                        'connect, remove that script while you use serve.py.')
WS_KEY = 'dGhlIHNhbXBsZSBub25jZQ=='  # RFC 6455 section 1.3
WS_ACCEPT = 's3pPLMBiTxaQ9kYGzzhZRbK+xOo='
WS_HELLO = bytes.fromhex('81 85 37 fa 21 3d 7f 9f 4d 51 58')  # the RFC's masked "Hello"
WS_ECHO = bytes.fromhex('81 05 48 65 6c 6c 6f')
REFUSAL_421 = b'HTTP/1.1 421 Misdirected Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'
REFUSAL_400 = b'HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'


def tag_for(origin):
    return (f'<script src="{BRIDGE_PATH}" data-allowed-origins="{origin}"></script>').encode()


def fetch(port, method, path, headers=None, body=None):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        return response.status, response.getheaders(), response.read()
    finally:
        conn.close()


def values(headers, name):
    return [value for key, value in headers if key.lower() == name.lower()]


def raw(port, data, shutdown=False):
    """Send raw bytes, return everything the server writes before it closes."""
    with socket.create_connection(('127.0.0.1', port), timeout=10) as sock:
        sock.sendall(data)
        if shutdown:
            sock.shutdown(socket.SHUT_WR)
        chunks = []
        while chunk := sock.recv(65536):
            chunks.append(chunk)
    return b''.join(chunks)


class FakeApp:
    """A dev server the proxy fronts; every request is recorded as (method, path, headers)."""

    def __init__(self, port=0):
        self.requests = []
        self.release = threading.Event()
        self.dropped = threading.Event()
        self.stopping = threading.Event()
        self.routes = {
            '/': lambda h: self.send(h, 200, [('Content-Type', 'text/html; charset=utf-8'),
                                              ('ETag', '"v1"'), ('Last-Modified', 'Mon, 01 Jan 2024 00:00:00 GMT'),
                                              ('Cache-Control', 'max-age=60'), ('X-App', 'yes')], PAGE),
            '/style.css': lambda h: self.send(h, 200, [('Content-Type', 'text/css')], CSS),
            '/redirect': lambda h: self.send(h, 302, [('Location', unquote(h.path.split('?to=', 1)[1]))], b''),
            '/cookie': self.cookie,
            '/echo-headers': self.echo,
            '/missing-html': lambda h: self.send(h, 404, [('Content-Type', 'text/html')], PAGE),
            '/not-modified': lambda h: self.send(h, 304, [('ETag', '"v1"')], b'', length=False),
            '/gzip': lambda h: self.send(h, 200, [('Content-Type', 'text/html'),
                                                  ('Content-Encoding', 'gzip')], GZIPPED),
            '/chunked': self.chunked,
            '/big-exact': lambda h: self.send(h, 200, [('Content-Type', 'text/html')], BIG_EXACT),
            '/big-over': lambda h: self.send(h, 200, [('Content-Type', 'text/html')], BIG_OVER),
            '/csp-header': lambda h: self.send(h, 200, [('Content-Type', 'text/html'), CSP_NONE], PAGE),
            '/csp-meta': lambda h: self.send(h, 200, [('Content-Type', 'text/html')], CSP_META),
            '/csp-self': lambda h: self.send(h, 200, [('Content-Type', 'text/html'),
                                                      ('Content-Security-Policy', "script-src 'self'")], PAGE),
            '/own-bridge': lambda h: self.send(h, 200, [('Content-Type', 'text/html')], OWN_BRIDGE),
            '/csp-404': lambda h: self.send(h, 404, [('Content-Type', 'text/html'), CSP_NONE], PAGE),
            '/csp-big': lambda h: self.send(h, 200, [('Content-Type', 'text/html'), CSP_NONE], BIG_OVER),
            '/stream': self.stream,
            '/endless': self.endless,
            '/upload': self.upload,
        }
        app = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):
                pass

            def handle_any(self):
                app.requests.append((self.command, self.path, self.headers))
                route = app.routes.get(self.path.split('?', 1)[0])
                try:
                    if route:
                        return route(self)
                    app.send(self, 404, [('Content-Type', 'text/plain')], b'app-404')
                except OSError:  # the proxy hung up on purpose (a client that left)
                    self.close_connection = True

            do_GET = do_HEAD = do_POST = handle_any

        class Server(ThreadingHTTPServer):
            allow_reuse_address = True
            daemon_threads = True

        self.server = Server(('127.0.0.1', port), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def send(self, h, status, headers, body, length=True):
        h.send_response(status)
        for pair in headers:
            h.send_header(*pair)
        if length:
            h.send_header('Content-Length', str(len(body)))
        h.end_headers()
        if h.command != 'HEAD':
            h.wfile.write(body)

    def cookie(self, h):
        self.send(h, 200, [('Set-Cookie', 'a=1; Path=/'), ('Set-Cookie', 'b=2; HttpOnly'),
                           ('Content-Security-Policy', "default-src 'self'; script-src 'self'"),
                           ('Content-Type', 'text/plain')], b'ok')

    def echo(self, h):
        seen = {name: h.headers.get_all(name) or []
                for name in ('Host', 'Accept-Encoding', 'Origin', 'Referer', 'Cookie')}
        self.send(h, 200, [('Content-Type', 'application/json')], json.dumps(seen).encode())

    def chunked(self, h):
        h.send_response(200)
        h.send_header('Content-Type', 'text/html')
        h.send_header('Transfer-Encoding', 'chunked')
        h.end_headers()
        for chunk in CHUNKS:
            h.wfile.write(b'%x\r\n%s\r\n' % (len(chunk), chunk))
        h.wfile.write(b'0\r\n\r\n')

    def stream(self, h):
        h.close_connection = True
        h.send_response(200)
        h.send_header('Content-Type', 'text/plain')
        h.send_header('Connection', 'close')
        h.end_headers()
        h.wfile.write(b'first')
        self.release.wait(10)
        h.wfile.write(b'second')

    def endless(self, h):
        h.close_connection = True
        h.send_response(200)
        h.send_header('Content-Type', 'text/plain')
        h.send_header('Connection', 'close')
        h.end_headers()
        try:
            while not self.stopping.is_set():
                h.wfile.write(b'x' * 65536)
        except OSError:
            self.dropped.set()

    def upload(self, h):
        body = h.rfile.read(int(h.headers['Content-Length']))
        self.send(h, 200, [('Content-Type', 'text/plain')], hashlib.sha256(body).hexdigest().encode())

    def close(self):
        self.stopping.set()
        self.release.set()
        self.server.shutdown()
        self.server.server_close()


def restart_app(port):
    deadline = time.time() + 5
    while True:
        try:
            return FakeApp(port)
        except OSError:
            if time.time() > deadline:
                raise
            time.sleep(0.05)


class Proxy:
    """scripts/serve.py <target> as a process; ready when its Open: line is written."""

    def __init__(self, target, serve=SERVE):
        work = REPO / 'work'  # gitignored scratch
        work.mkdir(exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(prefix='serve-proxy-', dir=work))
        self.studio, self.proxy = free_ports()
        self.out = open(self.scratch / 'stdout.txt', 'w+', encoding='utf-8')
        self.err = open(self.scratch / 'stderr.txt', 'w+', encoding='utf-8')
        self.proc = subprocess.Popen(
            [sys.executable, str(serve), target, '--quiet', '--studio-port', str(self.studio),
             '--target-port', str(self.proxy)],
            cwd=Path(serve).parent, stdout=self.out, stderr=self.err,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        try:
            self.wait_ready()
        except BaseException:
            self.close()
            raise
        parts = urlsplit(self.open_url)
        self.studio_origin = f'{parts.scheme}://{parts.netloc}'

    def wait_ready(self):
        deadline = time.time() + 15
        while True:
            match = re.search(r'^Open: (\S+)\n', self.read_out(), re.MULTILINE)
            if match:
                self.open_url = match.group(1)
                return
            if self.proc.poll() is not None:
                raise AssertionError(f'serve.py exited {self.proc.returncode}: {self.read_err()}')
            if time.time() > deadline:
                raise AssertionError('serve.py wrote no Open: line within 15 s')
            time.sleep(0.05)

    def read_out(self):
        self.out.flush()
        return (self.scratch / 'stdout.txt').read_text(encoding='utf-8')

    def read_err(self):
        self.err.flush()
        return (self.scratch / 'stderr.txt').read_text(encoding='utf-8')

    def stop(self):
        if self.proc.poll() is None:
            # Windows delivers a graceful stop to a child only as Ctrl-Break to its process group.
            self.proc.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGTERM)
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        return self.proc.returncode

    def close(self):
        self.stop()
        self.out.close()
        self.err.close()
        shutil.rmtree(self.scratch, ignore_errors=True)


def run_once(*args, serve=SERVE):
    """serve.py with free ports, expected to exit by itself; a server that never exits times out."""
    studio, proxy = free_ports()
    return subprocess.run(
        [sys.executable, str(serve), *args, '--quiet', '--studio-port', str(studio),
         '--target-port', str(proxy)],
        cwd=Path(serve).parent, capture_output=True, timeout=15, text=True, encoding='utf-8',
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})


class ProxyCase(unittest.TestCase):
    def start(self):
        """A FakeApp and a Proxy in front of it; both are stopped by cleanup, even on failure."""
        app = FakeApp()
        self.addCleanup(app.close)
        proxy = Proxy(f'http://127.0.0.1:{app.port}')
        self.addCleanup(proxy.close)
        return app, proxy


class PageTests(ProxyCase):
    def test_page_gets_one_tag(self):
        """Given an app page, when fetched through the proxy, then the body is the page with one
        tag after <head>, Content-Length is the new length, ETag and Last-Modified are gone,
        Cache-Control is no-store and the app's own X-App header is kept."""
        _, proxy = self.start()
        status, headers, body = fetch(proxy.proxy, 'GET', '/')
        expected = PAGE.replace(b'<head>', b'<head>' + tag_for(proxy.studio_origin), 1)
        self.assertEqual(status, 200)
        self.assertEqual(body, expected)
        self.assertEqual(values(headers, 'Content-Length'), [str(len(expected))])
        self.assertEqual((values(headers, 'ETag'), values(headers, 'Last-Modified')), ([], []))
        self.assertEqual(values(headers, 'Cache-Control'), ['no-store'])
        self.assertEqual(values(headers, 'X-App'), ['yes'])

    def test_stylesheet_passes_untouched(self):
        """Given a stylesheet whose text contains <head>, when fetched through the proxy, then
        the bytes, type and length equal the app's and no tag is added."""
        _, proxy = self.start()
        status, headers, body = fetch(proxy.proxy, 'GET', '/style.css')
        self.assertEqual((status, body), (200, CSS))
        self.assertEqual(values(headers, 'Content-Type'), ['text/css'])
        self.assertEqual(values(headers, 'Content-Length'), [str(len(CSS))])

    def test_location_rewrite(self):
        """Given redirects from the app, when fetched through the proxy, then a Location under a
        loopback name and the app's port moves to the proxy origin (network paths, no path, [::1],
        capitals and fragments included) and every other Location, unparseable ones included,
        is left as the app sent it."""
        app, proxy = self.start()
        site, other, own = app.port, app.port + 1, f'http://127.0.0.1:{proxy.proxy}'
        cases = (
            (f'http://127.0.0.1:{site}/x', f'{own}/x'),
            (f'//127.0.0.1:{site}/y', f'{own}/y'),
            (f'\\\\127.0.0.1:{site}/y', f'{own}/y'),
            (f'http://127.0.0.1:{site}', f'{own}/'),
            (f'http://[::1]:{site}/b', f'{own}/b'),
            (f'HTTP://LOCALHOST:{site}/u', f'{own}/u'),
            (f'http://127.0.0.1:{site}/f?q=1#frag', f'{own}/f?q=1#frag'),
            ('/x', '/x'),
            (f'http://127.0.0.1:{other}/z', f'http://127.0.0.1:{other}/z'),
            ('http://[::1/', 'http://[::1/'),
            ('http://127.0.0.1:abc/', 'http://127.0.0.1:abc/'),
        )
        for location, expected in cases:
            with self.subTest(location=location):
                status, headers, _ = fetch(proxy.proxy, 'GET', '/redirect?to=' + quote(location, safe=''))
                self.assertEqual((status, values(headers, 'Location')), (302, [expected]))

    def test_bridge_is_served_by_the_proxy(self):
        """Given the bridge path, when fetched with GET, with a query and with HEAD, then the
        repository's bridge bytes and Node's header set come back and the app sees nothing; a
        POST and a trailing-slash path reach the app."""
        app, proxy = self.start()
        bridge = (REPO / 'fontkit-bridge.js').read_bytes()
        for method, path in (('GET', BRIDGE_PATH), ('GET', BRIDGE_PATH + '?v=1'), ('HEAD', BRIDGE_PATH)):
            with self.subTest(method=method, path=path):
                status, headers, body = fetch(proxy.proxy, method, path)
                self.assertEqual(status, 200)
                self.assertEqual(body, b'' if method == 'HEAD' else bridge)
                self.assertEqual(values(headers, 'Content-Type'), ['text/javascript; charset=utf-8'])
                self.assertEqual(values(headers, 'Content-Length'), [str(len(bridge))])
                self.assertEqual(values(headers, 'Cache-Control'), ['no-store'])
                self.assertEqual(values(headers, 'X-Content-Type-Options'), ['nosniff'])
        self.assertEqual(app.requests, [])
        for method, path in (('POST', BRIDGE_PATH), ('GET', BRIDGE_PATH + '/')):
            with self.subTest(method=method, path=path):
                status, _, body = fetch(proxy.proxy, method, path)
                self.assertEqual((status, body), (404, b'app-404'))
        self.assertEqual([(m, p) for m, p, _ in app.requests],
                         [('POST', BRIDGE_PATH), ('GET', BRIDGE_PATH + '/')])

    def test_cookies_and_csp_pass_unchanged(self):
        """Given a response with two Set-Cookie headers and a CSP header, when fetched through
        the proxy, then the raw header list holds both cookies and the CSP exactly as sent."""
        _, proxy = self.start()
        _, headers, _ = fetch(proxy.proxy, 'GET', '/cookie')
        self.assertEqual(values(headers, 'Set-Cookie'), ['a=1; Path=/', 'b=2; HttpOnly'])
        self.assertEqual(values(headers, 'Content-Security-Policy'), ["default-src 'self'; script-src 'self'"])

    def test_request_headers_rewritten(self):
        """Given a request with the proxy's Host, Accept-Encoding gzip, br, an Origin and a
        Referer under the proxy and a Cookie, when the app echoes what it saw, then it got
        exactly one Host (its own) and one Accept-Encoding (identity), both addresses moved to
        the app's origin, the cookie untouched, and a foreign Origin stays as it was; a Referer
        that only starts with the proxy's address (a longer port) is forwarded unchanged."""
        app, proxy = self.start()
        own, site = f'http://127.0.0.1:{proxy.proxy}', f'http://127.0.0.1:{app.port}'
        headers = {'Accept-Encoding': 'gzip, br', 'Origin': own, 'Referer': own + '/from?q=1',
                   'Cookie': 'sid=abc'}
        seen = json.loads(fetch(proxy.proxy, 'GET', '/echo-headers', headers)[2])
        self.assertEqual(seen, {'Host': [f'127.0.0.1:{app.port}'], 'Accept-Encoding': ['identity'],
                                'Origin': [site], 'Referer': [site + '/from?q=1'], 'Cookie': ['sid=abc']})
        seen = json.loads(fetch(proxy.proxy, 'GET', '/echo-headers', {'Origin': 'http://evil.test'})[2])
        self.assertEqual(seen['Origin'], ['http://evil.test'])
        seen = json.loads(fetch(proxy.proxy, 'GET', '/echo-headers', {'Referer': own + '0/x'})[2])
        self.assertEqual(seen['Referer'], [own + '0/x'])

    def test_unreachable_app_answers_502_and_recovers(self):
        """Given a working proxy, when the app stops, then two requests in a row get 502 with
        the spec text; when the app is back on the same port, then the next request is 200."""
        app, proxy = self.start()
        port = app.port
        self.assertEqual(fetch(proxy.proxy, 'GET', '/style.css')[0], 200)
        app.close()
        for _ in range(2):
            status, headers, body = fetch(proxy.proxy, 'GET', '/')
            self.assertEqual(status, 502)
            self.assertEqual(body, f'Font Kit Studio cannot reach the dev server at http://127.0.0.1:{port}. '
                                   'Is it running?'.encode())
            self.assertEqual(values(headers, 'Content-Type'), ['text/plain; charset=utf-8'])
        revived = restart_app(port)
        self.addCleanup(revived.close)
        self.assertEqual(fetch(proxy.proxy, 'GET', '/style.css')[0], 200)

    def test_pass_through_rules(self):
        """Given HEAD, 304, a 404 page, gzip, a chunked page, and pages of exactly the limit and
        one byte more, when fetched through the proxy, then HEAD reaches the app as HEAD with no
        body and its headers intact; 304, the 404 page and gzip are untouched; the chunked page
        is tagged with a Content-Length and no Transfer-Encoding; the limit page is tagged; the
        larger page is byte-identical with no Cache-Control added."""
        app, proxy = self.start()
        tag = tag_for(proxy.studio_origin)
        status, headers, body = fetch(proxy.proxy, 'HEAD', '/')
        self.assertEqual((status, body, app.requests[-1][:2]), (200, b'', ('HEAD', '/')))
        self.assertEqual(values(headers, 'Content-Length'), [str(len(PAGE))])
        self.assertEqual((values(headers, 'ETag'), values(headers, 'Cache-Control')), (['"v1"'], ['max-age=60']))
        status, headers, body = fetch(proxy.proxy, 'GET', '/not-modified')
        self.assertEqual((status, body, values(headers, 'ETag')), (304, b'', ['"v1"']))
        self.assertEqual(fetch(proxy.proxy, 'GET', '/missing-html')[::2], (404, PAGE))
        status, headers, body = fetch(proxy.proxy, 'GET', '/gzip')
        self.assertEqual((body, values(headers, 'Content-Encoding')), (GZIPPED, ['gzip']))
        status, headers, body = fetch(proxy.proxy, 'GET', '/chunked')
        chunked = b''.join(CHUNKS).replace(b'<head>', b'<head>' + tag, 1)
        self.assertEqual(body, chunked)
        self.assertEqual(values(headers, 'Content-Length'), [str(len(chunked))])
        self.assertEqual(values(headers, 'Transfer-Encoding'), [])
        status, headers, body = fetch(proxy.proxy, 'GET', '/big-exact')
        self.assertEqual(body, BIG_EXACT.replace(b'<head>', b'<head>' + tag, 1))
        self.assertEqual(values(headers, 'Cache-Control'), ['no-store'])
        status, headers, body = fetch(proxy.proxy, 'GET', '/big-over')
        self.assertTrue(body == BIG_OVER, f'{len(body)} bytes, wanted {len(BIG_OVER)}')
        self.assertEqual(values(headers, 'Content-Length'), [str(LIMIT + 1)])
        self.assertEqual(values(headers, 'Cache-Control'), [])

    def test_streaming_is_not_held_back(self):
        """Given a response that sends one chunk and then waits, when the client has read that
        chunk through the proxy, then the first chunk reached the client before the response
        ended, the rest arrives after it and the connection ends with firstsecond; a proxy that
        closes or goes quiet before the first chunk fails with the bytes seen, it does not hang."""
        app, proxy = self.start()
        with socket.create_connection(('127.0.0.1', proxy.proxy), timeout=5) as sock:
            sock.sendall(f'GET /stream HTTP/1.0\r\nHost: 127.0.0.1:{proxy.proxy}\r\n\r\n'.encode())
            seen, deadline = b'', time.time() + 5
            while b'first' not in seen:
                chunk = sock.recv(65536)
                self.assertTrue(chunk and time.time() < deadline, f'no first chunk, saw {seen!r}')
                seen += chunk
            self.assertNotIn(b'second', seen)
            app.release.set()
            while chunk := sock.recv(65536):
                seen += chunk
        self.assertTrue(seen.endswith(b'firstsecond'))

    def test_request_body_reaches_the_app(self):
        """Given a 200,000 byte POST, when sent through the proxy, then the app received the
        same bytes (its SHA-256 equals the test's)."""
        _, proxy = self.start()
        body = bytes(range(256)) * 782
        status, _, answer = fetch(proxy.proxy, 'POST', '/upload', {'Content-Type': 'application/octet-stream'}, body)
        self.assertEqual((status, answer), (200, hashlib.sha256(body).hexdigest().encode()))

    def test_malformed_requests(self):
        """Given a chunked POST without a length, a request target that is not a path, a target
        with a non-ASCII byte and a bad Content-Length, then they answer 411, 400 Bad request.,
        400 Bad request. and 400 Bad request. with the app seeing no request, and a body that ends
        early gets no answer."""
        app, proxy = self.start()
        head = f'Host: 127.0.0.1:{proxy.proxy}\r\n'
        cases = (
            ('411', f'POST / HTTP/1.1\r\n{head}Transfer-Encoding: chunked\r\n\r\n'.encode(), b'HTTP/1.0 411'),
            ('star', f'OPTIONS * HTTP/1.1\r\n{head}\r\n'.encode(), b'HTTP/1.0 400'),
            ('latin1', f'GET /caf\xe9 HTTP/1.0\r\n{head}\r\n'.encode('latin-1'), b'HTTP/1.0 400'),
            ('length', f'POST / HTTP/1.0\r\n{head}Content-Length: abc\r\n\r\n'.encode(), b'HTTP/1.0 400'),
        )
        for name, data, line in cases:
            with self.subTest(name):
                answer = raw(proxy.proxy, data)
                self.assertTrue(answer.startswith(line), answer)
                if line.endswith(b'400'):
                    self.assertTrue(answer.endswith(b'Bad request.'), answer)
        self.assertEqual(app.requests, [])
        short = f'POST /upload HTTP/1.0\r\n{head}Content-Length: 10\r\n\r\nabc'.encode()
        self.assertEqual(raw(proxy.proxy, short, shutdown=True), b'')

    def test_client_leaving_mid_stream_is_quiet(self):
        """Given a response that never ends, when the client closes after its first bytes, then
        the app's connection is closed, the next request is 200 and stderr has no Traceback."""
        app, proxy = self.start()
        with socket.create_connection(('127.0.0.1', proxy.proxy), timeout=10) as sock:
            sock.sendall(f'GET /endless HTTP/1.0\r\nHost: 127.0.0.1:{proxy.proxy}\r\n\r\n'.encode())
            self.assertTrue(sock.recv(1024))
        self.assertTrue(app.dropped.wait(10))
        self.assertEqual(fetch(proxy.proxy, 'GET', '/style.css')[0], 200)
        proxy.stop()
        self.assertNotIn('Traceback', proxy.read_err())

    def test_stopping_with_a_stream_open_exits_cleanly(self):
        """Given a response that never ends and a client still reading it, when serve.py is
        told to stop, then it exits 0 and prints Stopped. (without daemon threads it waits for
        the stream and is killed after 10 s)."""
        _, proxy = self.start()
        with socket.create_connection(('127.0.0.1', proxy.proxy), timeout=10) as sock:
            sock.sendall(f'GET /endless HTTP/1.0\r\nHost: 127.0.0.1:{proxy.proxy}\r\n\r\n'.encode())
            self.assertTrue(sock.recv(1024))
            self.assertEqual(proxy.stop(), 0)
        self.assertIn('Stopped.', proxy.read_out())


class StudioServerTests(ProxyCase):
    def test_studio_server_serves_only_studio(self):
        """Given proxy mode, when Studio's server is asked, then a foreign Host is 421 JSON,
        /fontkit-studio.html is the repository file, /README.md, /demo/ and /scripts/serve.py
        are 404, the status reports sync false and the proxy URL, PUT of the overrides is 403;
        and the proxy answers a foreign Host with 421 Host header not allowed. without
        reaching the app."""
        app, proxy = self.start()
        status, headers, body = request(proxy.studio, 'GET', '/', headers={'Host': 'evil.test'})
        self.assertEqual((status, headers['content-type']), (421, 'application/json'))
        self.assertEqual(json.loads(body), {'ok': False, 'error': 'Host header not allowed'})
        status, _, body = request(proxy.studio, 'GET', '/fontkit-studio.html')
        self.assertEqual((status, body), (200, (REPO / 'fontkit-studio.html').read_bytes()))
        for path in ('/README.md', '/demo/', '/scripts/serve.py'):
            self.assertEqual(request(proxy.studio, 'GET', path)[0], 404, path)
        status, _, body = request(proxy.studio, 'GET', '/__fontkit/status')
        self.assertEqual(json.loads(body), {'sync': False, 'overrides': '',
                                            'target': f'http://127.0.0.1:{proxy.proxy}/'})
        status, _, body = request(proxy.studio, 'PUT', '/__fontkit/overrides.css', b'a{}',
                                  {'Content-Type': 'text/css'})
        self.assertEqual((status, json.loads(body)['error']), (403, 'sync is disabled (--no-sync)'))
        status, headers, body = request(proxy.proxy, 'GET', '/', headers={'Host': 'evil.test'})
        self.assertEqual((status, body), (421, b'Host header not allowed.'))
        self.assertEqual(headers['content-type'], 'text/plain; charset=utf-8')
        self.assertEqual(app.requests, [])

    def test_host_names_and_output(self):
        """Given localhost, 127.0.0.1 and [::1] targets, when serve.py starts, then it prints
        Studio, App (the target as typed), Press Ctrl-C and Open in that order, no Sync line,
        and Open names localhost for localhost and 127.0.0.1 otherwise, with the target's path
        and query in the proxy URL; a Studio port of 80 gives the origin http://localhost."""
        site = FakeApp()
        self.addCleanup(site.close)
        port = site.port
        cases = (
            (f'http://localhost:{port}', 'localhost', '/'),
            (f'http://127.0.0.1:{port}', '127.0.0.1', '/'),
            (f'http://[::1]:{port}/p?x=1#h', '127.0.0.1', '/p%3Fx%3D1%23h'),
        )
        for target, name, rest in cases:
            with self.subTest(target=target):
                proxy = Proxy(target)
                try:
                    lines = proxy.read_out().splitlines()
                finally:
                    proxy.close()
                opened = f'http://{name}:{proxy.studio}/fontkit-studio.html?target=http://{name}:{proxy.proxy}{rest}'
                self.assertEqual(lines[:4], [f'Studio:  {opened}', f'App:     {target}',
                                             'Press Ctrl-C to stop.', f'Open: {opened}'])
                self.assertFalse([line for line in lines if line.startswith('Sync:')])
        serve = load_serve()
        config = serve.Config.for_proxy('localhost', 80, 8001, serve.parse_target('http://localhost:5000'), True)
        self.assertEqual(config.studio_origin, 'http://localhost')


class TargetTests(unittest.TestCase):
    def test_non_loopback_targets_are_refused(self):
        """Given https, a remote host, another scheme and a malformed address as the target,
        when serve.py starts, then it exits 1, stderr is exactly the refusal line, stdout is
        empty and there is no Traceback."""
        for target in ('https://127.0.0.1:5000', 'http://example.com', 'ftp://localhost', 'http://[::1'):
            with self.subTest(target=target):
                result = run_once(target)
                self.assertEqual((result.returncode, result.stdout), (1, ''))
                self.assertEqual(result.stderr, REFUSAL + '\n')

    def test_both_servers_bind_loopback(self):
        """Given proxy mode, when main binds its servers and the second bind fails, then the
        Studio server and the proxy were each asked to bind 127.0.0.1 and nothing else."""
        serve, binds = load_serve(), []

        class Recorder:
            def __init__(self, address, handler):
                binds.append(address[0])
                if len(binds) == 2:
                    raise OSError(errno.EACCES, 'recorded, not bound')

            def server_close(self):
                pass

        serve.server_class = lambda: Recorder
        studio, proxy = free_ports()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = serve.main(['http://127.0.0.1:5000', '--quiet', '--studio-port', str(studio),
                               '--target-port', str(proxy)])
        self.assertEqual((code, binds), (1, ['127.0.0.1', '127.0.0.1']))

    def test_insert_tag_follows_the_shared_cases(self):
        """Given every case of proxy-insert-cases.json, when insert_tag runs on its latin-1
        input, then the output equals the case's expected page with {TAG} replaced."""
        serve = load_serve()
        tag = tag_for('http://127.0.0.1:1')
        for case in json.loads(CASES.read_text(encoding='utf-8')):
            with self.subTest(case['name']):
                expected = case['expected'].replace('{TAG}', tag.decode('latin-1')).encode('latin-1')
                self.assertEqual(serve.insert_tag(case['input'].encode('latin-1'), tag), expected)


class ReleaseLayoutTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='serve-release-px2-'))
        self.addCleanup(shutil.rmtree, self.folder, True)

    def copy(self, *names):
        for name in names:
            shutil.copy(REPO / ('scripts' if name == 'serve.py' else '.') / name, self.folder / name)
        return self.folder / 'serve.py'

    def test_release_layout_proxies_from_three_loose_files(self):
        """Given serve.py, Studio and the bridge copied alone into a folder, when run there with
        an app URL, then the proxied page is tagged and the bridge and Studio bytes equal the
        repository files."""
        serve = self.copy('serve.py', 'fontkit-studio.html', 'fontkit-bridge.js')
        app = FakeApp()
        self.addCleanup(app.close)
        proxy = Proxy(f'http://127.0.0.1:{app.port}', serve=serve)
        try:
            self.assertEqual(fetch(proxy.proxy, 'GET', '/')[2],
                             PAGE.replace(b'<head>', b'<head>' + tag_for(proxy.studio_origin), 1))
            self.assertEqual(fetch(proxy.proxy, 'GET', BRIDGE_PATH)[2], (REPO / 'fontkit-bridge.js').read_bytes())
            self.assertEqual(request(proxy.studio, 'GET', '/fontkit-studio.html')[2],
                             (REPO / 'fontkit-studio.html').read_bytes())
        finally:
            proxy.close()

    def test_release_layout_refusals(self):
        """Given the three loose files, when serve.py runs without a URL, then it exits 1 with
        stderr exactly the plain-mode line and empty stdout; given serve.py alone and an app
        URL, then it exits 1 with exactly the missing-file line and empty stdout."""
        serve = self.copy('serve.py', 'fontkit-studio.html', 'fontkit-bridge.js')
        result = run_once(serve=serve)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, '', PLAIN_LINE + '\n'))
        alone = Path(tempfile.mkdtemp(prefix='serve-alone-px2-'))
        self.addCleanup(shutil.rmtree, alone, True)
        shutil.copy(REPO / 'scripts' / 'serve.py', alone / 'serve.py')
        result = run_once('http://127.0.0.1:5000', serve=alone / 'serve.py')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, '', MISSING_LINE + '\n'))


class WebSocketApp:
    """A raw-socket WebSocket server (an http.server handler cannot hold the connection).

    mode 'echo': answer 101, then send every received frame back unmasked.
    mode 'push-close': answer 101, send one frame ("bye") and close.
    mode 'refuse': answer 400 with a body and close.
    Every request head is recorded in `heads`; `eof` is set when a client closes an echo connection.
    """

    def __init__(self, mode='echo'):
        self.mode = mode
        self.heads = []
        self.connections = 0
        self.eof = threading.Event()
        self.stopping = threading.Event()
        self.open = []
        self.listener = socket.socket()
        self.listener.bind(('127.0.0.1', 0))
        self.listener.listen()
        self.listener.settimeout(0.1)  # the accept loop polls the stopping flag
        self.port = self.listener.getsockname()[1]
        self.thread = threading.Thread(target=self.accept, daemon=True)
        self.thread.start()

    def accept(self):
        while not self.stopping.is_set():
            try:
                conn, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            conn.settimeout(10)
            self.connections += 1
            self.open.append(conn)
            threading.Thread(target=self.serve, args=(conn,), daemon=True).start()

    def serve(self, conn):
        try:
            data = b''
            while b'\r\n\r\n' not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, _, surplus = data.partition(b'\r\n\r\n')  # surplus is the first frame bytes
            self.heads.append(head.decode('latin-1'))
            if self.mode == 'refuse':
                conn.sendall(b'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 4\r\n\r\nnope')
                return
            key = re.search(r'^Sec-WebSocket-Key: (\S+)', head.decode('latin-1'), re.MULTILINE | re.IGNORECASE)
            accept = base64.b64encode(hashlib.sha1((key.group(1) + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
                                                   .encode()).digest()).decode()
            conn.sendall(f'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                         f'Sec-WebSocket-Accept: {accept}\r\n\r\n'.encode())
            if self.mode == 'push-close':
                conn.sendall(b'\x81\x03bye')
                return
            self.echo(conn, surplus)
        except OSError:
            pass
        finally:
            conn.close()

    def echo(self, conn, buffer):
        while True:
            while len(buffer) >= 6 and len(buffer) >= 6 + (buffer[1] & 0x7F):
                size = buffer[1] & 0x7F  # frames here are short and masked
                mask, payload = buffer[2:6], buffer[6:6 + size]
                conn.sendall(bytes([buffer[0], size]) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
                buffer = buffer[6 + size:]
            chunk = conn.recv(65536)
            if not chunk:
                self.eof.set()
                return
            buffer += chunk

    def stop(self):
        self.stopping.set()
        self.listener.close()
        for conn in self.open:
            conn.close()
        self.thread.join(5)


def masked(payload, mask=b'\x01\x02\x03\x04'):
    return bytes([0x81, 0x80 | len(payload)]) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))


def upgrade_request(port, path='/socket', host=None, origin=None, connection=('Upgrade',)):
    host = host or f'127.0.0.1:{port}'
    origin = origin or f'http://127.0.0.1:{port}'
    lines = ''.join(f'Connection: {value}\r\n' for value in connection)
    return (f'GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n{lines}'
            f'Sec-WebSocket-Key: {WS_KEY}\r\nSec-WebSocket-Version: 13\r\nOrigin: {origin}\r\n\r\n').encode()


def read_head(sock):
    data = b''
    while not data.endswith(b'\r\n\r\n'):
        chunk = sock.recv(1)
        if not chunk:
            raise AssertionError(f'closed before the end of the head: {data!r}')
        data += chunk
    return data.decode('latin-1')


def read_exact(sock, size):
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise AssertionError(f'closed after {data!r}, wanted {size} bytes')
        data += chunk
    return data


class CspPortTests(unittest.TestCase):
    """Every row of packages/fontkitstudio/test/csp.test.js, as a literal."""

    @classmethod
    def setUpClass(cls):
        cls.serve = load_serve()

    def blocks(self, policy, origin=None):
        return self.serve.blocks_same_origin_script(policy, origin)

    def test_policy_rows_without_an_origin(self):
        """Given the 20 policies of the Node suite, when blocks_same_origin_script judges each
        without an origin, then it returns exactly the Node suite's True or False."""
        rows = [
            ("script-src 'self'", False), ("default-src 'self'", False), ("script-src 'nonce-x'", True),
            ("script-src 'self' 'strict-dynamic'", True), ("default-src 'none'", True),
            ("script-src-elem 'self'; script-src 'none'", False),
            ("script-src-elem 'none'; script-src 'self'", True),
            ("script-src 'none'; default-src 'self'", True), ("style-src 'none'", False),
            ("img-src 'none'; default-src 'self'", False), ('', False), ('   ', False),
            ('script-src *', False), ('script-src http:', False), ('script-src https:', True),
            ("script-src 'self'; script-src 'none'", False), ("SCRIPT-SRC 'SELF'", False),
            ("Script-Src 'Nonce-x' 'STRICT-DYNAMIC'", True), ("script-src 'self', script-src 'none'", True),
            ("script-src 'self', style-src 'none'", False),
        ]
        self.assertEqual(len(rows), 20)
        for policy, blocked in rows:
            with self.subTest(policy=policy):
                self.assertIs(self.blocks(policy), blocked)

    def test_list_and_non_text_policies(self):
        """Given lists of policies and values that are not text, when judged, then a list blocks
        when any one blocks, an empty list does not, and None and 5 never block."""
        self.assertIs(self.blocks(["script-src 'self'", "script-src 'nonce-x'"]), True)
        self.assertIs(self.blocks(["script-src 'self'", "default-src 'self'"]), False)
        self.assertIs(self.blocks([]), False)
        self.assertIs(self.blocks([None, "script-src 'none'"]), True)
        for value in (None, 5):
            with self.subTest(value=value):
                self.assertIs(self.blocks(value), False)

    def test_policies_that_name_the_page_origin(self):
        """Given the 10 allowing and 20 blocking policies of the Node suite and the origin
        http://localhost:5173, when judged, then the first ten do not block and the other twenty do."""
        origin = 'http://localhost:5173'
        allows = [
            'script-src http://localhost:5173', 'script-src localhost:5173', 'script-src HTTP://LOCALHOST:5173',
            'script-src http://localhost:*', 'script-src localhost:*', 'script-src http://localhost:5173/',
            'script-src http://localhost:5173/@fontkit/',
            'script-src localhost:5173/@fontkit/fontkit-bridge.js',
            "script-src-elem localhost:5173; script-src 'none'",
            "default-src 'none'; script-src 'nonce-q' localhost:5173",
        ]
        blocks = [
            'script-src http://localhost:5174', 'script-src localhost', 'script-src http://127.0.0.1:5173',
            'script-src https://localhost:5173', 'script-src https://localhost:*', 'script-src localhost:5173/js/',
            'script-src localhost:5173/@fontkit/other.js', 'script-src localhost:5173/@fontkit',
            'script-src localhost:5173/@FONTKIT/', 'script-src localhost:5173/@fontkit/Fontkit-Bridge.js',
            'script-src *.localhost:5173', 'script-src *.localhost', 'script-src', 'script-src ;;',
            "script-src 'strict-dynamic' localhost:5173", 'script-src http://:5173', 'script-src localhost:abc',
            'script-src ://localhost:5173', 'script-src https:', "script-src-elem 'none'; script-src localhost:5173",
        ]
        self.assertEqual((len(allows), len(blocks)), (10, 20))
        for policy in allows:
            with self.subTest(allows=policy):
                self.assertIs(self.blocks(policy, origin), False)
        for policy in blocks:
            with self.subTest(blocks=policy):
                self.assertIs(self.blocks(policy, origin), True)

    def test_origin_edge_rows(self):
        """Given two policies, default ports, IPv6 and unusable origins, when judged, then every
        result equals the Node suite's: the second policy can block, port 80 matches only a page
        without a port, [::1] matches by name, and with no usable origin only self, * and http: allow."""
        origin = 'http://localhost:5173'
        self.assertIs(self.blocks("script-src localhost:5173, script-src 'nonce-q'", origin), True)
        self.assertIs(self.blocks(['script-src localhost:5173', "script-src 'none'"], origin), True)
        self.assertIs(self.blocks(['script-src localhost:5173', 'script-src localhost:*'], origin), False)
        self.assertIs(self.blocks('script-src localhost:80', 'http://localhost'), False)
        self.assertIs(self.blocks('script-src localhost', 'http://localhost'), False)
        self.assertIs(self.blocks('script-src localhost:80', origin), True)
        self.assertIs(self.blocks('script-src localhost:5173x', origin), True)  # not in the Node file: no partial match
        self.assertIs(self.blocks('script-src [::1]:5173', 'http://[::1]:5173'), False)
        self.assertIs(self.blocks('script-src localhost:5173', 'http://[::1]:5173'), True)
        for bad in (None, 'nonsense', 'https://localhost:5173', 5, 'http://localhost:abc', 'http://:5173'):
            with self.subTest(origin=bad):
                self.assertIs(self.blocks('script-src localhost:5173', bad), True)
                self.assertIs(self.blocks("script-src 'self'", bad), False)

    def test_meta_policies(self):
        """Given the Node suite's mixed-case page and its empty cases, when read, then only the two
        Content-Security-Policy tags are returned in order, a page without one, a non-string and an
        empty http-equiv give [], and a CSP tag with an empty content gives ['']."""
        page = '\n'.join([
            '<meta http-equiv="Content-Security-Policy" content="script-src \'self\'">',
            '<META CONTENT="default-src \'none\'" HTTP-EQUIV=\'content-security-policy\'>',
            '<meta http-equiv="Content-Security-Policy-Report-Only" content="default-src \'none\'">',
            '<meta http-equiv="refresh" content="5">',
            '<meta name="x" content="script-src \'none\'">',
        ])
        self.assertEqual(self.serve.meta_policies(page), ["script-src 'self'", "default-src 'none'"])
        self.assertEqual(self.serve.meta_policies('<p>hi</p>'), [])
        self.assertEqual(self.serve.meta_policies(None), [])
        self.assertEqual(self.serve.meta_policies('<meta http-equiv="" content="">'), [])
        self.assertEqual(self.serve.meta_policies('<meta http-equiv="Content-Security-Policy" content="">'), [''])

    def test_loads_own_bridge(self):
        """Given the Node suite's four positive and five negative pages, plus an empty src, when
        checked, then the positive ones return True and the others False."""
        for page in ('<script src="/vendor/fontkit-bridge.js"></script>',
                     "<SCRIPT async src='https://x.test/fontkit-bridge.min.js'>",
                     '<script src=fontkit-bridge.js></script>',
                     '<script\n  type="module"\n  src = "./fontkit-bridge.js?v=2"></script>'):
            with self.subTest(page=page):
                self.assertIs(self.serve.loads_own_bridge(page), True)
        for page in ('<script src="/app.js"></script>', '<script>var s = "fontkit-bridge.js";</script>',
                     '<p>fontkit-bridge.js</p>', '<link href="fontkit-bridge.js">', None, '<script src="">'):
            with self.subTest(page=page):
                self.assertIs(self.serve.loads_own_bridge(page), False)

    def test_messages_are_the_exact_texts(self):
        """Given the spec's strings, when compared, then CSP_MESSAGE and BRIDGE_TWICE_MESSAGE equal
        them character for character."""
        self.assertEqual(self.serve.CSP_MESSAGE, CSP_MESSAGE)
        self.assertEqual(self.serve.BRIDGE_TWICE_MESSAGE, BRIDGE_TWICE_MESSAGE)


class WarningTests(ProxyCase):
    def warnings(self, proxy):
        return proxy.read_err().splitlines()

    def test_csp_header_warns_once(self):
        """Given a page whose header blocks scripts, when fetched twice, then stderr holds the CSP
        message after the first fetch already, and exactly once after both."""
        _, proxy = self.start()
        fetch(proxy.proxy, 'GET', '/csp-header')
        self.assertEqual(self.warnings(proxy), [CSP_MESSAGE])
        fetch(proxy.proxy, 'GET', '/csp-header')
        proxy.stop()
        self.assertEqual(self.warnings(proxy), [CSP_MESSAGE])

    def test_csp_meta_warns_once(self):
        """Given a page whose meta tag blocks scripts, when fetched twice, then stderr holds the
        CSP message exactly once."""
        _, proxy = self.start()
        for _ in range(2):
            fetch(proxy.proxy, 'GET', '/csp-meta')
        proxy.stop()
        self.assertEqual(self.warnings(proxy), [CSP_MESSAGE])

    def test_allowing_and_plain_pages_are_silent(self):
        """Given a page with script-src 'self' and a page without a policy, when fetched, then
        stderr is empty."""
        _, proxy = self.start()
        fetch(proxy.proxy, 'GET', '/csp-self')
        fetch(proxy.proxy, 'GET', '/')
        proxy.stop()
        self.assertEqual(self.warnings(proxy), [])

    def test_own_bridge_warns_once(self):
        """Given a page that loads its own bridge, when fetched twice, then stderr holds the
        bridge-twice message exactly once."""
        _, proxy = self.start()
        for _ in range(2):
            fetch(proxy.proxy, 'GET', '/own-bridge')
        proxy.stop()
        self.assertEqual(self.warnings(proxy), [BRIDGE_TWICE_MESSAGE])

    def test_the_two_messages_have_their_own_flags(self):
        """Given a bridge page and a CSP page, when each is fetched twice in one run, then stderr
        holds the bridge-twice message once and the CSP message once, in that order."""
        _, proxy = self.start()
        for path in ('/own-bridge', '/csp-header', '/own-bridge', '/csp-header'):
            fetch(proxy.proxy, 'GET', path)
        proxy.stop()
        self.assertEqual(self.warnings(proxy), [BRIDGE_TWICE_MESSAGE, CSP_MESSAGE])

    def test_only_a_buffered_taggable_page_is_checked(self):
        """Given a blocking CSP on a HEAD, a 404 page and a page over the size limit, when each is
        fetched, then stderr is still empty after each one."""
        _, proxy = self.start()
        for method, path in (('HEAD', '/csp-header'), ('GET', '/csp-404'), ('GET', '/csp-big')):
            with self.subTest(method=method, path=path):
                fetch(proxy.proxy, method, path)
                self.assertEqual(self.warnings(proxy), [])

    def test_the_warning_does_not_change_the_response(self):
        """Given a page that warns, when fetched, then the body is the page with one tag, the
        status is 200 and the app's CSP header is passed unchanged."""
        _, proxy = self.start()
        status, headers, body = fetch(proxy.proxy, 'GET', '/csp-header')
        self.assertEqual(status, 200)
        self.assertEqual(body, PAGE.replace(b'<head>', b'<head>' + tag_for(proxy.studio_origin), 1))
        self.assertEqual(values(headers, 'Content-Security-Policy'), ["script-src 'none'"])
        self.assertEqual(values(headers, 'Content-Length'), [str(len(body))])


class SayTests(unittest.TestCase):
    def test_a_broken_stderr_does_not_turn_a_page_into_a_502(self):
        """Given a stderr whose write raises OSError and one that is closed (ValueError), when a
        CSP page is fetched through an in-process proxy, then each answers 200 with the tagged page."""
        serve = load_serve()
        app = FakeApp()
        self.addCleanup(app.close)
        closed = io.StringIO()
        closed.close()
        broken = types.SimpleNamespace(write=self.fail_write, flush=lambda: None)
        for name, stderr in (('OSError', broken), ('ValueError', closed)):
            with self.subTest(name):
                studio, port = free_ports()
                target = serve.parse_target(f'http://127.0.0.1:{app.port}')
                config = serve.Config.for_proxy('127.0.0.1', studio, port, target, True)
                server = serve.run_proxy(config, target, config.studio_origin)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with unittest.mock.patch.object(sys, 'stderr', stderr):
                        status, _, body = fetch(port, 'GET', '/csp-header')
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(5)
                self.assertEqual((status, body), (200, PAGE.replace(
                    b'<head>', b'<head>' + tag_for(config.studio_origin), 1)))

    @staticmethod
    def fail_write(text):
        raise OSError('stderr is gone')

    def test_the_line_is_written_while_the_lock_is_held(self):
        """Given a stderr whose write is parked, when say prints, then the said lock is held
        during the write (the race itself cannot be reproduced deterministically)."""
        serve = load_serve()
        entered, release = threading.Event(), threading.Event()

        def park(text):
            entered.set()
            release.wait(10)

        me = types.SimpleNamespace(said=set(), said_lock=threading.Lock())
        parked = types.SimpleNamespace(write=park, flush=lambda: None)
        with unittest.mock.patch.object(sys, 'stderr', parked):
            thread = threading.Thread(target=serve.ProxyHandler.say, args=(me, 'warning'))
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                self.assertTrue(me.said_lock.locked())
            finally:
                release.set()
                thread.join(10)


class TunnelTests(ProxyCase):
    def start_ws(self, mode='echo'):
        """A WebSocketApp and a Proxy in front of it, both stopped by cleanup."""
        app = WebSocketApp(mode)
        self.addCleanup(app.stop)
        proxy = Proxy(f'http://127.0.0.1:{app.port}')
        self.addCleanup(proxy.close)
        return app, proxy

    def connect(self, proxy, **kwargs):
        sock = socket.create_connection(('127.0.0.1', proxy.proxy), timeout=5)
        self.addCleanup(sock.close)
        sock.sendall(upgrade_request(proxy.proxy, **kwargs))
        return sock

    def test_frames_echo_through_the_proxy(self):
        """Given the RFC 6455 handshake sent through the proxy, when the RFC's masked Hello and
        then two more frames follow, then the client reads a 101 with the RFC's accept value and
        the unmasked echo of each frame on the same connection."""
        _, proxy = self.start_ws()
        sock = self.connect(proxy)
        head = read_head(sock)
        self.assertTrue(head.startswith('HTTP/1.1 101 '), head)
        self.assertIn(f'Sec-WebSocket-Accept: {WS_ACCEPT}\r\n', head)
        for frame, echo in ((WS_HELLO, WS_ECHO), (WS_HELLO, WS_ECHO), (masked(b'Hi'), b'\x81\x02Hi')):
            sock.sendall(frame)
            self.assertEqual(read_exact(sock, len(echo)), echo)

    def test_the_app_gets_the_rewritten_request_once(self):
        """Given an upgrade with the proxy's Host and Origin, when the app records it, then it saw
        one request: GET /socket HTTP/1.1, Host and Origin of the app, the key, Upgrade websocket,
        Connection Upgrade only, Accept-Encoding identity."""
        app, proxy = self.start_ws()
        sock = self.connect(proxy)
        read_head(sock)
        sock.sendall(WS_HELLO)
        read_exact(sock, len(WS_ECHO))
        self.assertEqual(len(app.heads), 1)
        first, *lines = app.heads[0].split('\r\n')
        seen = {}
        for line in lines:
            name, _, value = line.partition(': ')
            seen.setdefault(name.lower(), []).append(value)
        self.assertEqual(first, 'GET /socket HTTP/1.1')
        self.assertEqual(seen['host'], [f'127.0.0.1:{app.port}'])
        self.assertEqual(seen['origin'], [f'http://127.0.0.1:{app.port}'])
        self.assertEqual(seen['sec-websocket-key'], [WS_KEY])
        self.assertEqual((seen['upgrade'], seen['connection']), (['websocket'], ['Upgrade']))
        self.assertEqual(seen['accept-encoding'], ['identity'])

    def test_either_side_closing_ends_the_tunnel(self):
        """Given an open tunnel, when the client closes, then the app reads EOF; given an app that
        sends one frame and closes, then the client reads that frame and then EOF."""
        app, proxy = self.start_ws()
        sock = self.connect(proxy)
        read_head(sock)
        sock.close()
        self.assertTrue(app.eof.wait(10))
        _, proxy = self.start_ws('push-close')
        sock = self.connect(proxy)
        read_head(sock)
        self.assertEqual(read_exact(sock, 5), b'\x81\x03bye')
        self.assertEqual(sock.recv(1), b'')

    def test_foreign_host_and_bad_target_are_refused(self):
        """Given an upgrade with the Host evil.test and one with the target *, when sent, then the
        answers are exactly the 421 and the 400 refusals and the app saw no connection."""
        app, proxy = self.start_ws()
        self.assertEqual(raw(proxy.proxy, upgrade_request(proxy.proxy, host='evil.test')), REFUSAL_421)
        self.assertEqual(raw(proxy.proxy, upgrade_request(proxy.proxy, path='*')), REFUSAL_400)
        self.assertEqual(app.connections, 0)

    def test_the_apps_refusal_reaches_the_client_unchanged(self):
        """Given an app that answers an upgrade with a 400 and a body and closes, when sent through
        the proxy, then the client reads exactly those bytes and then EOF."""
        _, proxy = self.start_ws('refuse')
        answer = raw(proxy.proxy, upgrade_request(proxy.proxy))
        self.assertEqual(answer, b'HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n'
                                 b'Content-Length: 4\r\n\r\nnope')

    def test_unreachable_app_drops_the_connection_quietly(self):
        """Given a stopped app, when an upgrade arrives, then the client gets zero bytes, the next
        bridge request is 200 and stderr has no Traceback."""
        app, proxy = self.start_ws()
        app.stop()
        self.assertEqual(raw(proxy.proxy, upgrade_request(proxy.proxy)), b'')
        self.assertEqual(fetch(proxy.proxy, 'GET', BRIDGE_PATH)[0], 200)
        proxy.stop()
        self.assertNotIn('Traceback', proxy.read_err())

    def test_an_upgrade_on_the_bridge_path_goes_to_the_app(self):
        """Given an upgrade for the bridge path, when sent, then the client reads the app's 101 and
        the app saw that path; a plain GET of the path still returns the repository's bridge bytes."""
        app, proxy = self.start_ws()
        sock = self.connect(proxy, path=BRIDGE_PATH)
        self.assertTrue(read_head(sock).startswith('HTTP/1.1 101 '))
        self.assertEqual(app.heads[0].split('\r\n')[0], f'GET {BRIDGE_PATH} HTTP/1.1')
        status, _, body = fetch(proxy.proxy, 'GET', BRIDGE_PATH)
        self.assertEqual((status, body), (200, (REPO / 'fontkit-bridge.js').read_bytes()))

    def test_upgrade_needs_an_upgrade_token_in_connection(self):
        """Given Upgrade: websocket with Connection keep-alive, Upgrade, and with two Connection
        lines, when sent, then each gets a 101 and the app saw the Connection values joined by
        a comma and a space; given a GET with Upgrade: websocket and Connection: close, then the
        client gets the proxy's own HTTP/1.0 200 (a normal request), not the app's HTTP/1.1.
        Node's HTTP parser makes this rule: probed on Node 24.16.0, proxy.js only listens."""
        app, proxy = self.start_ws()
        for connection in (('keep-alive, Upgrade',), ('keep-alive', 'Upgrade')):
            sock = self.connect(proxy, connection=connection)
            self.assertTrue(read_head(sock).startswith('HTTP/1.1 101 '))
        seen = [[line for line in head.split('\r\n') if line.startswith('Connection:')] for head in app.heads]
        self.assertEqual(seen, [['Connection: keep-alive, Upgrade']] * 2)
        web = FakeApp()
        self.addCleanup(web.close)
        plain = Proxy(f'http://127.0.0.1:{web.port}')
        self.addCleanup(plain.close)
        with socket.create_connection(('127.0.0.1', plain.proxy), timeout=5) as sock:
            sock.sendall(upgrade_request(plain.proxy, path='/echo-headers', connection=('close',)))
            self.assertTrue(read_head(sock).startswith('HTTP/1.0 200 '))

    def test_bytes_sent_with_the_handshake_are_not_lost(self):
        """Given the handshake and the first frame sent in one write, when the app echoes, then
        the client reads the echo of that frame."""
        _, proxy = self.start_ws()
        with socket.create_connection(('127.0.0.1', proxy.proxy), timeout=5) as sock:
            sock.sendall(upgrade_request(proxy.proxy) + WS_HELLO)
            self.assertTrue(read_head(sock).startswith('HTTP/1.1 101 '))
            self.assertEqual(read_exact(sock, len(WS_ECHO)), WS_ECHO)


if __name__ == '__main__':
    unittest.main()
