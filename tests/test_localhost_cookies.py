"""Real command cookie delivery, observed in the framed app's HTTP echo."""

import json
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import support
from fixture_support import FIXTURES, require_fixture
from support import ENGINES, new_context

NODE = shutil.which('node')
PACKAGE = support.REPO / 'packages' / 'fontkitstudio'
COOKIES = ('lax=kept; Path=/; SameSite=Lax',
           'strict=kept; Path=/; SameSite=Strict', 'default=kept; Path=/')
PAGE = '''<!doctype html><html><head></head><body>
<h1 data-design-id="cookie.title">Cookie delivery</h1><p id="cookies">Loading</p>
<script>fetch('/echo').then(r => r.json()).then(values => {
  document.querySelector('#cookies').textContent = values.cookie || 'No cookies';
});</script></body></html>'''


class CookieHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/echo':
            body = json.dumps({'cookie': self.headers.get('Cookie', '')}).encode()
            content_type = 'application/json'
        else:
            body = PAGE.encode()
            content_type = 'text/html'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        if self.path == '/seed':
            for cookie in COOKIES:
                self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@unittest.skipIf(NODE is None, 'node is required for the real command')
class LocalhostCookiesTest(unittest.TestCase):
    def start(self, args, cwd):
        flags = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {}
        proc = subprocess.Popen([NODE, str(PACKAGE / 'bin' / 'fontkitstudio.js'),
                                 *args, '--no-open'], cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding='utf-8', **flags)
        self.addCleanup(self.stop, proc)
        lines = queue.Queue()
        collected = []
        self.command_lines = lines
        self.command_output = collected

        def pump(stream):
            for line in stream:
                collected.append(line.rstrip())
                lines.put(line.strip())
            lines.put(None)

        for stream in (proc.stdout, proc.stderr):
            threading.Thread(target=pump, args=(stream,), daemon=True).start()
        return self.read_open(proc)

    def read_open(self, proc=None):
        deadline = time.monotonic() + 45
        while True:
            try:
                line = self.command_lines.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                self.fail('No Open line: ' + '\n'.join(self.command_output))
            if line is None and proc is not None and proc.poll() is not None:
                self.fail('Command exited: ' + '\n'.join(self.command_output))
            if line and line.startswith('Open: '):
                return line[len('Open: '):]

    def stop(self, proc):
        try:
            if proc.poll() is None:
                proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    self.fail('Command did not shut down')
        finally:
            proc.stdout.close()
            proc.stderr.close()

    def assert_cookies(self, studio_url, app_url):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = new_context(engine)
                try:
                    context.route('https://**/*', lambda route: route.abort())
                    page = context.new_page()
                    page.goto(app_url + '/seed')
                    page.locator('#cookies').filter(has_text='strict=kept').wait_for()
                    page.goto(studio_url)
                    page.wait_for_function(
                        'document.querySelector("#bridgeStatusBadge").dataset.state === "connected"',
                        timeout=15000)
                    echo = page.frame_locator('#targetAppFrame').locator('#cookies')
                    echo.filter(has_not_text='Loading').wait_for()
                    rendered = echo.inner_text()
                    print(f'{engine} {app_url}: framed HTTP Cookie echo: {rendered}', flush=True)
                    # Gecko already delivers omitted-SameSite cross-site: preserve that evidence
                    # before asserting the Lax/Strict regression on the unchanged implementation.
                    if engine == 'firefox' and urlsplit(parse_qs(urlsplit(studio_url).query)['target'][0]).hostname == 'localhost':
                        self.assertIn('default=kept', rendered)
                    for name in ('lax', 'strict', 'default'):
                        self.assertIn(f'{name}=kept', rendered)
                    self.assertEqual(urlsplit(studio_url).hostname, 'localhost')
                    tag = page.frame_locator('#targetAppFrame').locator(
                        'script[src="/@fontkit/fontkit-bridge.js"]')
                    self.assertEqual(tag.count(), 1)
                    self.assertEqual(tag.get_attribute('data-allowed-origins'),
                                     f'http://{urlsplit(studio_url).netloc}')
                finally:
                    context.close()

    def test_proxy_keeps_localhost_sign_in_cookies(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), CookieHandler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        app = f'http://localhost:{server.server_port}'
        studio = self.start([app + '/index.html'], support.REPO)
        self.assert_cookies(studio, app)

    def test_vite_keeps_localhost_sign_in_cookies(self):
        require_fixture(self, 'vite-react')
        scratch = tempfile.TemporaryDirectory(prefix='fks-cookie-', dir=FIXTURES)
        self.addCleanup(scratch.cleanup)
        project = Path(scratch.name)
        # Dependencies belong to the installed fixture; only test-owned page/config are written.
        shutil.copy2(FIXTURES / 'vite-react' / 'package.json', project / 'package.json')
        (project / 'node_modules').symlink_to(FIXTURES / 'vite-react' / 'node_modules', target_is_directory=True)
        (project / 'index.html').write_text(PAGE, encoding='utf-8')
        plugin = (PACKAGE / 'src' / 'vite-plugin.js').as_posix()
        config = project / 'vite.config.js'
        config.write_text(
            f"import {{ fontkitStudio }} from '{plugin}';\n"
            'export default { server: {host: "localhost"}, plugins: [fontkitStudio(), {\n'
            'name: "cookie-endpoints", configureServer(server) {\n'
            'server.middlewares.use((req, res, next) => {\n'
            f'if (req.url === "/seed") {{ res.setHeader("Set-Cookie", {json.dumps(COOKIES)});\n'
            'res.writeHead(302, {Location: "/"}); res.end(); return; }\n'
            'if (req.url === "/echo") { res.setHeader("Content-Type", "application/json");\n'
            'res.end(JSON.stringify({cookie: req.headers.cookie || ""})); return; } next();\n'
            '}); }}]};\n', encoding='utf-8')
        studio = self.start([], project)
        app = parse_qs(urlsplit(studio).query)['target'][0].rstrip('/')
        self.assert_cookies(studio, app)
        # A config reload replaces Vite's server and plugin lifecycle, unlike a CSS HMR update.
        config.write_text(config.read_text(encoding='utf-8') + '// reload config\n', encoding='utf-8')
        restarted = self.read_open()
        self.assertNotEqual(restarted, studio)
        app = parse_qs(urlsplit(restarted).query)['target'][0].rstrip('/')
        self.assert_cookies(restarted, app)


if __name__ == '__main__':
    unittest.main()
