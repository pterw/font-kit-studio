"""Preview dev server (scripts/serve.py) and demo target app (demo/index.html)."""

import http.client
import importlib.util
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ENGINES, REPO, launch, shared_runtime  # noqa: E402

SERVE = REPO / 'scripts' / 'serve.py'
DEMO = REPO / 'demo' / 'index.html'
LIMIT = 1024 * 1024
AUTHOR_TARGETS = (
    'landing.brand.mark', 'landing.brand.wordmark', 'landing.hero.title', 'landing.hero.lead',
    'landing.hero.cta', 'landing.stat.badge',
    'landing.feature.sync.title', 'landing.feature.sync.body',
    'landing.feature.preview.title', 'landing.feature.preview.body',
    'landing.feature.export.title', 'landing.feature.export.body',
)


def free_ports(count=2):
    sockets = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(('127.0.0.1', 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def request(port, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        return response.status, {k.lower(): v for k, v in response.getheaders()}, response.read()
    finally:
        conn.close()


def load_serve():
    spec = importlib.util.spec_from_file_location('fks_serve_module', SERVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Server:
    """A scripts/serve.py subprocess on free ports with an overrides file inside the repo."""

    def __init__(self, *extra, overrides=None, env=None):
        work = REPO / 'work'  # gitignored scratch
        work.mkdir(exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(prefix='preview-server-', dir=work))
        self.overrides = overrides or self.scratch / 'overrides.css'
        self.rel = self.overrides.relative_to(REPO).as_posix()
        self.studio, self.target = free_ports()
        self.out = open(self.scratch / 'stdout.txt', 'w+')
        self.err = open(self.scratch / 'stderr.txt', 'w+')
        self.proc = subprocess.Popen(
            [sys.executable, str(SERVE), '--quiet', '--studio-port', str(self.studio),
             '--target-port', str(self.target), '--overrides', self.rel, *extra],
            cwd=REPO, stdout=self.out, stderr=self.err,
            env={**os.environ, **env} if env else None)
        try:
            self.wait_ready()
        except BaseException:
            self.close()
            raise

    def wait_ready(self):
        deadline = time.time() + 15
        while True:
            if self.proc.poll() is not None:
                raise AssertionError(f'serve.py exited {self.proc.returncode}: {self.read_err()}')
            try:
                request(self.studio, 'GET', '/__fontkit/status')
                request(self.target, 'GET', '/')
                return
            except OSError:
                if time.time() > deadline:
                    raise AssertionError('serve.py did not start listening within 15 s')
                time.sleep(0.05)

    def read_out(self):
        self.out.flush()
        return (self.scratch / 'stdout.txt').read_text()

    def read_err(self):
        self.err.flush()
        return (self.scratch / 'stderr.txt').read_text()

    def stop(self, sig=signal.SIGTERM):
        if self.proc.poll() is None:
            self.proc.send_signal(sig)
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

    def put(self, body, origin=None, port=None, content_type='text/css'):
        headers = {'Content-Type': content_type}
        if origin is not None:
            headers['Origin'] = origin
        return request(port or self.studio, 'PUT', '/__fontkit/overrides.css', body, headers)


class PreviewServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server()

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def setUp(self):
        if self.server.overrides.exists():
            self.server.overrides.unlink()

    def assert_no_store(self, headers):
        self.assertEqual(headers.get('cache-control'), 'no-store')

    def test_both_ports_serve_repo_files(self):
        s = self.server
        for port in (s.studio, s.target):
            status, headers, body = request(port, 'GET', '/font_kit_studio_v0.1.1.html')
            self.assertEqual(status, 200)
            self.assertIn('text/html', headers['content-type'])
            self.assertEqual(body, (REPO / 'font_kit_studio_v0.1.1.html').read_bytes())
            self.assert_no_store(headers)
            status, headers, body = request(port, 'GET', '/demo/')
            self.assertEqual(status, 200)
            self.assertIn('text/html', headers['content-type'])
            self.assertIn(b'data-design-id="landing.hero.title"', body)
            self.assert_no_store(headers)
            status, headers, _ = request(port, 'GET', '/fontkit-bridge.js')
            self.assertEqual(status, 200)
            self.assertIn('javascript', headers['content-type'])

    def test_root_redirects(self):
        s = self.server
        status, headers, _ = request(s.studio, 'GET', '/')
        self.assertEqual(status, 302)
        self.assertEqual(headers['location'], '/font_kit_studio_v0.1.1.html'
                         f'?target=http://localhost:{s.target}/demo/')
        status, headers, _ = request(s.target, 'GET', '/')
        self.assertEqual((status, headers['location']), (302, '/demo/'))

    def test_dot_paths_are_not_served(self):
        for port in (self.server.studio, self.server.target):
            for path in ('/.git/HEAD', '/.gitignore', '/demo/../.git/config', '//.git/HEAD',
                         '/%2egit/HEAD', '//.git/config?x=1'):
                status, headers, _ = request(port, 'GET', path)
                self.assertEqual(status, 404, (port, path))
                self.assert_no_store(headers)

    def test_hidden_check_uses_the_served_path(self):
        # Independent of the interpreter's own leading-slash collapsing in parse_request:
        # clean_path must see the same path translate_path serves.
        spec = importlib.util.spec_from_file_location('fks_serve', SERVE)
        serve = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(serve)
        clean = lambda raw: serve.Handler.clean_path(SimpleNamespace(path=raw))
        for raw in ('//.git/HEAD', '//.git/config?x', '/a/../.git/HEAD#f', '/%2egit/HEAD'):
            self.assertIsNone(clean(raw), raw)
        self.assertEqual(clean('//__fontkit/status?x=1'), '/__fontkit/status')
        self.assertEqual(clean('/demo/?v=2#top'), '/demo')

    def test_default_port_origins_and_hosts_omit_the_port(self):
        # A browser never sends ":80": a page on http://localhost sends `Origin: http://localhost`
        # and `Host: localhost`. Checked on the config, since binding port 80 needs root.
        spec = importlib.util.spec_from_file_location('fks_serve_config', SERVE)
        serve = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(serve)
        overrides = REPO / 'demo' / 'fontkit-overrides.css'
        for host in ('127.0.0.1', 'localhost', ''):
            with self.subTest(host=host):
                config = serve.Config(host, 80, 8001, overrides, True, True)
                for origin in ('http://localhost', 'http://127.0.0.1'):
                    self.assertIn(origin, config.origins)
                self.assertIn('localhost', config.hosts(80))
                self.assertIn('localhost:80', config.hosts(80), 'an explicit :80 is harmless')
        config = serve.Config('127.0.0.1', 8000, 8001, overrides, True, True)
        self.assertEqual(config.origins, {'http://localhost:8000', 'http://127.0.0.1:8000'})
        self.assertNotIn('http://localhost', config.origins, 'a non-default port always carries it')
        self.assertEqual(config.hosts(8001), {'localhost:8001', '127.0.0.1:8001', '[::1]:8001'})

    def test_host_header_allow_list(self):
        s = self.server
        for port in (s.studio, s.target):
            for host in (f'localhost:{port}', f'127.0.0.1:{port}', f'LOCALHOST:{port}',
                         f'[::1]:{port}'):
                status, _, _ = request(port, 'GET', '/demo/', headers={'Host': host})
                self.assertEqual(status, 200, host)
            other = s.target if port == s.studio else s.studio
            for host in (f'evil.test:{port}', 'evil.test', f'localhost:{other}', 'localhost',
                         f'127.0.0.1.evil.test:{port}'):
                for method, path in (('GET', '/demo/'), ('GET', '/__fontkit/status'),
                                     ('PUT', '/__fontkit/overrides.css')):
                    status, headers, body = request(
                        port, method, path, b'x' if method == 'PUT' else None,
                        {'Host': host, 'Content-Type': 'text/css'})
                    self.assertEqual(status, 421, (port, host, method, path))
                    self.assertIn('application/json', headers['content-type'])
                    self.assertIs(json.loads(body)['ok'], False)
                    self.assert_no_store(headers)
        self.assertFalse(s.overrides.exists())

    def test_misdirected_page_escapes_what_it_prints(self):
        page = load_serve().misdirected_page({'<img src=x onerror=1>:80'})
        self.assertIn('&lt;img', page)
        self.assertNotIn('<img', page)

    def test_misdirected_browser_request_gets_a_readable_page(self):
        s = self.server
        for port in (s.studio, s.target):
            html_headers = {'Host': f'evil.test:{port}', 'Accept': 'text/html,application/xhtml+xml'}
            for method in ('GET', 'HEAD'):
                status, headers, body = request(port, method, '/demo/', headers=html_headers)
                self.assertEqual(status, 421, (port, method))
                self.assertIn('text/html', headers['content-type'])
                self.assert_no_store(headers)
                if method == 'GET':
                    page = body.decode()
                    self.assertIn('--host', page)
                    self.assertIn(f'localhost:{port}', page, 'names the host it accepts')
                    self.assertNotIn('evil.test', page, 'the request Host is never echoed back')
                    self.assertIsNone(re.search(r'<script|<link|<img|src=|@import', page, re.I))
            # Anything that did not ask for HTML keeps the JSON answer.
            for accept in ('application/json', '*/*'):
                status, headers, body = request(
                    port, 'GET', '/demo/', headers={'Host': f'evil.test:{port}', 'Accept': accept})
                self.assertEqual(status, 421, accept)
                self.assertIn('application/json', headers['content-type'])
                self.assertIs(json.loads(body)['ok'], False)

    def test_status_endpoint_on_studio_port(self):
        status, headers, body = request(self.server.studio, 'GET', '/__fontkit/status')
        self.assertEqual(status, 200)
        self.assertIn('application/json', headers['content-type'])
        self.assert_no_store(headers)
        self.assertEqual(json.loads(body), {
            'sync': True, 'overrides': self.server.rel,
            'target': f'http://localhost:{self.server.target}/demo/'})

    def test_put_writes_exact_bytes_atomically(self):
        s = self.server
        first = b'/* first */\n[data-design-id="landing.hero.title"] { color: #ff0000 !important; }\n'
        status, headers, body = s.put(first)
        self.assertEqual(status, 200)
        self.assertIn('application/json', headers['content-type'])
        self.assert_no_store(headers)
        self.assertEqual(json.loads(body), {'ok': True, 'bytes': len(first), 'path': s.rel})
        self.assertEqual(s.overrides.read_bytes(), first)
        inode = s.overrides.stat().st_ino

        second = ':root { --font-sans: "Inter Tight", sans-serif; }\r\n/* ünïcode ✓ */'.encode()
        status, _, body = s.put(second, origin=f'http://localhost:{s.studio}')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['bytes'], len(second))
        self.assertEqual(s.overrides.read_bytes(), second)
        # os.replace swaps in a new file rather than rewriting the old one in place.
        self.assertNotEqual(s.overrides.stat().st_ino, inode)
        self.assertEqual(sorted(p.name for p in s.overrides.parent.iterdir()),
                         sorted(['overrides.css', 'stdout.txt', 'stderr.txt']))

        status, headers, body = request(s.studio, 'GET', '/' + s.rel)
        self.assertEqual((status, body), (200, second))
        self.assertIn('text/css', headers['content-type'])
        self.assert_no_store(headers)

        status, _, _ = s.put(b'', origin=f'http://127.0.0.1:{s.studio}')
        self.assertEqual(status, 200)
        self.assertEqual(s.overrides.read_bytes(), b'')

    def test_put_rejects_foreign_origin(self):
        s = self.server
        for origin in ('http://evil.test', f'http://localhost:{s.target}',
                       f'http://127.0.0.1:{s.target}', f'https://localhost:{s.studio}', 'null'):
            status, headers, _ = s.put(b'body { color: red; }', origin=origin)
            self.assertEqual(status, 403, origin)
            self.assert_no_store(headers)
        self.assertFalse(s.overrides.exists())

    def test_put_size_limit(self):
        s = self.server
        status, _, body = s.put(b'a' * LIMIT)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['bytes'], LIMIT)
        s.overrides.unlink()

        conn = http.client.HTTPConnection('127.0.0.1', s.studio, timeout=10)
        try:
            conn.putrequest('PUT', '/__fontkit/overrides.css')
            conn.putheader('Content-Type', 'text/css')
            conn.putheader('Content-Length', str(LIMIT + 1))
            conn.endheaders()
            response = conn.getresponse()
            self.assertEqual(response.status, 413)
            self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        finally:
            conn.close()
        self.assertFalse(s.overrides.exists())

    def test_put_requires_css_content_type(self):
        status, _, _ = self.server.put(b'x', content_type='text/plain;charset=UTF-8')
        self.assertEqual(status, 415)
        self.assertFalse(self.server.overrides.exists())
        status, _, _ = self.server.put(b'x', content_type='text/css; charset=utf-8')
        self.assertEqual(status, 200)

    def test_missing_overrides_is_empty_css_on_both_ports(self):
        self.assertFalse(self.server.overrides.exists())
        for port in (self.server.studio, self.server.target):
            status, headers, body = request(port, 'GET', '/' + self.server.rel + '?v=1')
            self.assertEqual((status, body), (200, b''))
            self.assertIn('text/css', headers['content-type'])
            self.assert_no_store(headers)

    def test_target_port_has_no_fontkit_endpoints(self):
        s = self.server
        for method, path in (('GET', '/__fontkit/status'), ('PUT', '/__fontkit/overrides.css'),
                             ('GET', '/__fontkit/overrides.css')):
            status, headers, _ = request(s.target, method, path, b'x' if method == 'PUT' else None,
                                         {'Content-Type': 'text/css'})
            self.assertEqual(status, 404, (method, path))
            self.assert_no_store(headers)
        self.assertFalse(s.overrides.exists())


class PreviewServerSymlinkTest(unittest.TestCase):
    """A link inside the repository must not carry a request to a file the URL check would refuse.

    clean_path() judges the URL, but the file system follows links: the served file is the
    resolved one, so that is the path that has to stay inside the repository and not be hidden.
    """

    SECRET = b'private contents that must never be served\n'

    @classmethod
    def setUpClass(cls):
        cls.server = Server()

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def setUp(self):
        # Links live in a directory of their own inside the repository (the server's scratch
        # directory, under the git-ignored work/), the targets outside it or hidden.
        outside = tempfile.TemporaryDirectory(prefix='preview-outside-')
        self.addCleanup(outside.cleanup)
        self.outside = Path(outside.name)
        (self.outside / 'secret.txt').write_bytes(self.SECRET)
        (self.outside / 'index.html').write_bytes(self.SECRET)
        self.links = Path(tempfile.mkdtemp(prefix='links-', dir=self.server.scratch))
        self.addCleanup(shutil.rmtree, self.links, ignore_errors=True)
        self.url = '/' + self.links.relative_to(REPO).as_posix()
        self.hidden = self.links / '.private'
        self.hidden.mkdir()
        (self.hidden / 'secret.txt').write_bytes(self.SECRET)
        (self.hidden / 'index.html').write_bytes(self.SECRET)

    def assert_refused(self, path):
        for port in (self.server.studio, self.server.target):
            for method in ('GET', 'HEAD'):
                status, headers, body = request(port, method, self.url + path)
                self.assertEqual(status, 404, (port, method, path))
                self.assertNotIn(self.SECRET, body, (port, method, path))
                self.assertEqual(headers.get('cache-control'), 'no-store')

    def test_a_file_symlink_to_outside_the_repo_is_refused(self):
        (self.links / 'outside.txt').symlink_to(self.outside / 'secret.txt')
        self.assert_refused('/outside.txt')

    def test_a_directory_symlink_to_outside_the_repo_is_refused(self):
        (self.links / 'outdir').symlink_to(self.outside, target_is_directory=True)
        self.assert_refused('/outdir/secret.txt')

    def test_an_alias_of_a_hidden_file_is_refused(self):
        (self.links / 'alias.txt').symlink_to(self.hidden / 'secret.txt')
        (self.links / 'aliasdir').symlink_to(self.hidden, target_is_directory=True)
        self.assert_refused('/alias.txt')
        self.assert_refused('/aliasdir/secret.txt')
        self.assert_refused('/aliasdir/')

    def test_an_index_html_symlink_in_a_directory_is_refused(self):
        for name, target in (('out', self.outside / 'index.html'), ('hid', self.hidden / 'index.html')):
            (self.links / name).mkdir()
            (self.links / name / 'index.html').symlink_to(target)
            self.assert_refused(f'/{name}/')

    def test_a_symlinked_overrides_file_is_not_read_through(self):
        s = self.server
        s.overrides.symlink_to(self.outside / 'secret.txt')
        try:
            for port in (s.studio, s.target):
                status, _, body = request(port, 'GET', '/' + s.rel)
                self.assertEqual(status, 404, port)
                self.assertNotIn(self.SECRET, body)
        finally:
            s.overrides.unlink()

    def test_ordinary_files_and_links_that_stay_inside_are_still_served(self):
        (self.links / 'plain.txt').write_bytes(b'plain\n')
        (self.links / 'site').mkdir()
        (self.links / 'site' / 'index.html').write_bytes(b'<p>site</p>\n')
        (self.links / 'inner.txt').symlink_to(self.links / 'plain.txt')
        for port in (self.server.studio, self.server.target):
            for path, expected in (('/plain.txt', b'plain\n'), ('/site/', b'<p>site</p>\n'),
                                   ('/inner.txt', b'plain\n')):
                status, _, body = request(port, 'GET', self.url + path)
                self.assertEqual((status, body), (200, expected), (port, path))
            status, _, body = request(port, 'GET', self.url + '/missing.txt')
            self.assertEqual(status, 404)


class PreviewServerLifecycleTest(unittest.TestCase):
    def test_no_sync_rejects_writes(self):
        server = Server('--no-sync')
        try:
            status, _, body = request(server.studio, 'GET', '/__fontkit/status')
            self.assertEqual(status, 200)
            self.assertIs(json.loads(body)['sync'], False)
            status, headers, _ = server.put(b'body {}', origin=f'http://localhost:{server.studio}')
            self.assertEqual(status, 403)
            self.assertEqual(headers.get('cache-control'), 'no-store')
            self.assertFalse(server.overrides.exists())
        finally:
            server.close()

    def test_write_failure_returns_json_500(self):
        work = REPO / 'work'
        work.mkdir(exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix='preview-blocked-', dir=work))
        try:
            (scratch / 'blocker.css').write_text('a file, not a directory')
            server = Server(overrides=scratch / 'blocker.css' / 'overrides.css')
            try:
                status, headers, body = server.put(b'body { color: red; }')
                self.assertEqual(status, 500)
                self.assertIn('application/json', headers['content-type'])
                self.assertEqual(headers.get('cache-control'), 'no-store')
                data = json.loads(body)
                self.assertIs(data['ok'], False)
                self.assertIn('write failed', data['error'])
                self.assertEqual(sorted(p.name for p in scratch.iterdir()), ['blocker.css'])
                status, _, _ = request(server.studio, 'GET', '/__fontkit/status')
                self.assertEqual(status, 200)
                self.assertNotIn('Traceback', server.read_err())
            finally:
                server.close()
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def test_prints_studio_url_and_shuts_down_cleanly(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            server = Server()
            try:
                self.assertEqual(server.stop(sig), 0, server.read_err())
                expected = (f'http://localhost:{server.studio}/font_kit_studio_v0.1.1.html'
                            f'?target=http://localhost:{server.target}/demo/')
                self.assertIn(expected, server.read_out())
                self.assertNotIn('Traceback', server.read_err())
            finally:
                server.close()

    def test_last_line_before_the_wait_is_the_url_to_open(self):
        server = Server()
        try:
            # Stdout goes to a file and is flushed with the Open: line, which can land after the
            # ports start listening. Read it once the process has exited.
            self.assertEqual(server.stop(), 0, server.read_err())
            lines = server.read_out().splitlines()
            self.assertEqual(lines[-1], 'Stopped.')
            lines = lines[:-1]
            expected = (f'Open: http://localhost:{server.studio}/font_kit_studio_v0.1.1.html'
                        f'?target=http://localhost:{server.target}/demo/')
            self.assertEqual(lines[-1], expected, lines)
            self.assertTrue(lines[0].startswith('Studio:'), 'the existing lines are kept')
            self.assertTrue(any(line.startswith('Target:') for line in lines))
            self.assertTrue(any(line.startswith('Sync:') for line in lines))
        finally:
            server.close()

    def run_with_fake_browser(self, *flags):
        """Run serve.py with $BROWSER set to a script that records the URL it was given."""
        work = REPO / 'work'
        work.mkdir(exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix='preview-browser-', dir=work))
        try:
            log = scratch / 'opened.txt'
            script = scratch / 'fake_browser.py'
            script.write_text('import sys\nopen(sys.argv[1], "a").write(sys.argv[2] + "\\n")\n')
            server = Server(*flags, env={'BROWSER': f'"{sys.executable}" "{script}" "{log}" %s'})
            try:
                expected = (f'http://localhost:{server.studio}/font_kit_studio_v0.1.1.html'
                            f'?target=http://localhost:{server.target}/demo/')
                self.assertEqual(server.stop(), 0, server.read_err())  # open() has returned by exit
                opened = log.read_text().splitlines() if log.exists() else []
                return opened, expected, server.read_out()
            finally:
                server.close()
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def test_open_flag_opens_the_studio_url_once(self):
        opened, expected, out = self.run_with_fake_browser('--open')
        self.assertEqual(opened, [expected])
        self.assertIn(f'Open: {expected}', out)

    def test_browser_is_not_opened_without_the_flag(self):
        opened, expected, out = self.run_with_fake_browser()
        self.assertEqual(opened, [])
        self.assertIn(f'Open: {expected}', out)
        self.assertNotIn('browser', out.lower(), 'nothing extra is printed when --open is off')

    def test_busy_port_names_the_port_and_the_flag(self):
        for busy_flag, other_flag in (('--studio-port', '--target-port'),
                                      ('--target-port', '--studio-port')):
            with self.subTest(busy=busy_flag), socket.socket() as held:
                held.bind(('127.0.0.1', 0))
                held.listen()
                busy = held.getsockname()[1]
                free = free_ports(1)[0]
                result = subprocess.run(
                    [sys.executable, str(SERVE), '--quiet', busy_flag, str(busy),
                     other_flag, str(free)],
                    cwd=REPO, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(f'{busy_flag} {busy} is in use; pick another with {busy_flag} <port>',
                              result.stderr)
                self.assertNotIn(other_flag, result.stderr, 'only the port that failed is named')
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_unbindable_host_names_the_host_not_the_port_flag(self):
        port = free_ports(1)[0]
        result = subprocess.run(
            [sys.executable, str(SERVE), '--quiet', '--host', '203.0.113.9',
             '--studio-port', str(port)],
            cwd=REPO, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f'cannot listen on 203.0.113.9:{port} (--studio-port)', result.stderr)
        self.assertNotIn('pick another with', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_windows_never_shares_a_port(self):
        serve = load_serve()
        config = serve.Config('127.0.0.1', 8000, 8001, REPO / 'demo' / 'fontkit-overrides.css',
                              True, True)
        for platform, reuse in (('win32', False), ('linux', True), ('darwin', True)):
            with self.subTest(platform=platform), mock.patch.object(sys, 'platform', platform):
                server = serve.make_server(config, '127.0.0.1', 0, True)  # port 0: nothing taken
                try:
                    self.assertIs(bool(server.allow_reuse_address), reuse)
                    # The option only counts when it is set before bind, so read the socket.
                    self.assertEqual(
                        server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) != 0, reuse)
                finally:
                    server.server_close()

    def test_refuses_overrides_outside_repo(self):
        with tempfile.TemporaryDirectory() as outside:
            for path in (str(Path(outside) / 'x.css'), '../outside.css', 'demo/../../x.css',
                         'font_kit_studio_v0.1.1.html', '.git/hooks/x.css'):
                ports = free_ports()
                result = subprocess.run(
                    [sys.executable, str(SERVE), '--quiet', '--studio-port', str(ports[0]),
                     '--target-port', str(ports[1]), '--overrides', path],
                    cwd=REPO, capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0, path)
                self.assertIn('overrides', result.stderr.lower(), path)
                self.assertEqual(list(Path(outside).iterdir()), [])


def route_demo_stylesheet(page, server):
    """Send the demo's `fontkit-overrides.css` request to the server's scratch overrides path."""
    page.route(f'http://localhost:{server.target}/demo/fontkit-overrides.css',
               lambda route: route.continue_(url=f'http://localhost:{server.target}/{server.rel}'))


class DemoPageTest(unittest.TestCase):
    def test_demo_source_is_offline(self):
        source = DEMO.read_text()
        self.assertIsNone(re.search(r'''(?:src|href|action)\s*=\s*["']?\s*(?:[a-z]+:)?//''', source, re.I))
        self.assertIsNone(re.search(r'url\(\s*["\']?\s*(?:[a-z]+:)?//', source, re.I))
        self.assertIsNone(re.search(r'@import', source, re.I))
        self.assertIn('<link rel="stylesheet" href="fontkit-overrides.css">', source)
        self.assertIn('<script src="../fontkit-bridge.js"></script>', source)

    def test_demo_loads_from_target_port(self):
        from contextlib import nullcontext

        # Sync off and a scratch overrides path that is never created: the demo's stylesheet
        # request is routed there, so the checkout's own demo/fontkit-overrides.css (which
        # Sync to file creates) never takes part.
        server = Server('--no-sync')
        try:
            with nullcontext(shared_runtime()) as runtime:  # a second driver cannot start beside the shared one
                for engine in ENGINES:
                    with self.subTest(engine=engine):
                        self.check_demo(runtime, engine, server)
        finally:
            server.close()

    def test_demo_loads_without_any_overrides_request_failing(self):
        from contextlib import nullcontext

        # The server's own scratch overrides path is the file under test. The checkout's
        # demo/fontkit-overrides.css (Sync to file creates it) is never read or touched.
        server = Server('--no-sync')
        overrides = server.overrides
        self.assertFalse(overrides.exists(), 'the scratch overrides file starts missing')
        try:
            with nullcontext(shared_runtime()) as runtime:  # a second driver cannot start beside the shared one
                for engine in ENGINES:
                    with self.subTest(engine=engine):
                        browser = launch(runtime, engine)
                        try:
                            page = browser.new_page()
                            route_demo_stylesheet(page, server)
                            seen = []
                            page.on('response', lambda res: seen.append((res.url, res.status)))
                            page.goto(f'http://localhost:{server.target}/demo/', wait_until='load')
                            sheet = [item for item in seen if item[0].endswith('/' + server.rel)]
                            self.assertTrue(sheet, f'the demo requests the scratch overrides stylesheet: {seen}')
                            self.assertEqual(sheet, [(f'http://localhost:{server.target}/{server.rel}', 200)])
                            self.assertEqual(
                                page.evaluate("document.querySelector('link[href=\"fontkit-overrides.css\"]')"
                                              ".sheet !== null"), True, 'the empty sheet applied')
                        finally:
                            browser.close()
            self.assertFalse(overrides.exists(), 'loading the demo never creates the file')
        finally:
            server.close()

    def check_demo(self, runtime, engine, server):
        browser = launch(runtime, engine)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors, requests, responses = [], [], {}
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda req: requests.append(req.url))
            page.on('response', lambda res: responses.__setitem__(res.url.split('?')[0], res.status))
            route_demo_stylesheet(page, server)
            # The bridge is being rewritten concurrently: only prove the tag resolves to the
            # served file, without executing it.
            bridge = f'http://localhost:{server.target}/fontkit-bridge.js'
            page.route(bridge, lambda route: route.fulfill(
                status=200, content_type='text/javascript', body='window.__bridgeStub = true;'))
            page.goto(f'http://localhost:{server.target}/demo/', wait_until='load')
            self.assertEqual(errors, [])
            self.assertTrue(page.evaluate('window.__bridgeStub === true'))
            origin = f'http://localhost:{server.target}/'
            self.assertEqual([url for url in requests if not url.startswith(origin)], [])
            self.assertEqual(responses.get(f'{origin}{server.rel}'), 200)

            info = page.evaluate('''ids => {
                const present = ids.filter(id => document.querySelectorAll(
                    `[data-design-id="${id}"]`).length === 1);
                const link = document.querySelector('link[href="fontkit-overrides.css"]');
                const styles = [...document.querySelectorAll('style, link[rel="stylesheet"]')];
                const root = getComputedStyle(document.documentElement);
                const badge = document.querySelector('[data-design-id="landing.stat.badge"]');
                const anchors = [...document.querySelectorAll('nav a[href^="#"]')];
                const authored = new Set(document.querySelectorAll('[data-design-id]'));
                return {
                    present,
                    overridesLast: styles[styles.length - 1] === link,
                    bridgeAfterLink: !!(link.compareDocumentPosition(
                        document.querySelector('script[src="../fontkit-bridge.js"]'))
                        & Node.DOCUMENT_POSITION_FOLLOWING),
                    display: root.getPropertyValue('--font-display').trim(),
                    sans: root.getPropertyValue('--font-sans').trim(),
                    weights: badge && badge.getAttribute('data-design-weights'),
                    mark: document.querySelector('[data-design-id="landing.brand.mark"]').tagName,
                    anchors: anchors.length,
                    brokenAnchors: anchors.map(a => a.getAttribute('href'))
                        .filter(h => h.length < 2 || !document.getElementById(h.slice(1))),
                    plain: [...document.querySelectorAll('h2, h3, p, li, button, blockquote, summary')]
                        .filter(el => !authored.has(el)).length,
                };
            }''', list(AUTHOR_TARGETS))
            self.assertEqual(info['present'], list(AUTHOR_TARGETS))
            self.assertTrue(info['overridesLast'])
            self.assertTrue(info['bridgeAfterLink'])
            self.assertTrue(info['display'])
            self.assertTrue(info['sans'])
            self.assertEqual(info['weights'], '400 600 800')
            self.assertEqual(info['mark'].lower(), 'svg')
            self.assertGreaterEqual(info['anchors'], 3)
            self.assertEqual(info['brokenAnchors'], [])
            self.assertGreaterEqual(info['plain'], 8)

            page.locator('nav a[href="#features"]').click()
            page.wait_for_function("location.hash === '#features'")
        finally:
            browser.close()


if __name__ == '__main__':
    unittest.main()
