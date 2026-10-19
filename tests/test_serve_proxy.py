"""Proxy mode of scripts/serve.py: the real script as a process in front of a small fake app."""

import gzip
import hashlib
import http.client
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
import unittest
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

    def __init__(self, target, *extra, serve=SERVE):
        work = REPO / 'work'  # gitignored scratch
        work.mkdir(exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(prefix='serve-proxy-', dir=work))
        self.studio, self.proxy = free_ports()
        self.out = open(self.scratch / 'stdout.txt', 'w+', encoding='utf-8')
        self.err = open(self.scratch / 'stderr.txt', 'w+', encoding='utf-8')
        self.proc = subprocess.Popen(
            [sys.executable, str(serve), target, '--quiet', '--studio-port', str(self.studio),
             '--target-port', str(self.proxy), *extra],
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
    def start(self, target=None, **kwargs):
        """A FakeApp and a Proxy in front of it; both are stopped by cleanup, even on failure."""
        app = FakeApp()
        self.addCleanup(app.close)
        proxy = Proxy(target or f'http://127.0.0.1:{app.port}', **kwargs)
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
        the app's origin, the cookie untouched, and a foreign Origin stays as it was."""
        app, proxy = self.start()
        own, site = f'http://127.0.0.1:{proxy.proxy}', f'http://127.0.0.1:{app.port}'
        headers = {'Accept-Encoding': 'gzip, br', 'Origin': own, 'Referer': own + '/from?q=1',
                   'Cookie': 'sid=abc'}
        seen = json.loads(fetch(proxy.proxy, 'GET', '/echo-headers', headers)[2])
        self.assertEqual(seen, {'Host': [f'127.0.0.1:{app.port}'], 'Accept-Encoding': ['identity'],
                                'Origin': [site], 'Referer': [site + '/from?q=1'], 'Cookie': ['sid=abc']})
        seen = json.loads(fetch(proxy.proxy, 'GET', '/echo-headers', {'Origin': 'http://evil.test'})[2])
        self.assertEqual(seen['Origin'], ['http://evil.test'])

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
        self.assertEqual(body == BIG_OVER, True)
        self.assertEqual(values(headers, 'Content-Length'), [str(LIMIT + 1)])
        self.assertEqual(values(headers, 'Cache-Control'), [])

    def test_streaming_is_not_held_back(self):
        """Given a response that sends one chunk and then waits, when the client has read that
        chunk through the proxy, then the rest is released and arrives after it: the first chunk
        reached the client before the response ended."""
        app, proxy = self.start()
        with socket.create_connection(('127.0.0.1', proxy.proxy), timeout=5) as sock:
            sock.sendall(f'GET /stream HTTP/1.0\r\nHost: 127.0.0.1:{proxy.proxy}\r\n\r\n'.encode())
            seen = b''
            while b'first' not in seen:
                seen += sock.recv(65536)
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
        400 Bad request. and 400 Bad request., and a body that ends early gets no answer."""
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


if __name__ == '__main__':
    unittest.main()
