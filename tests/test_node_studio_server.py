"""Browser test for the fontkitstudio Studio server (R1.3).

Studio is served by packages/fontkitstudio/src/studio-server.js behind a per-run token and opens
`?target=` pointing at a recording loopback server. The app must see no token and no Referer, and a
URL without the token must show no Studio.
"""

import shutil
import subprocess
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, urlunsplit

import support
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
HELPER = support.REPO / 'packages' / 'fontkitstudio' / 'test' / 'helpers' / 'serve-studio.js'


class Recorder(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(('127.0.0.1', 0), RecordingHandler)
        self.lock = threading.Lock()
        self.requests = []

    def snapshot(self):
        with self.lock:
            return list(self.requests)


class RecordingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        with self.server.lock:
            self.server.requests.append((self.path, dict(self.headers)))
        body = b'<!doctype html><title>Recorded app</title><p>app</p>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@unittest.skipIf(NODE is None, 'node is not on PATH; the Studio server tests need it')
class StudioServerBrowserTest(unittest.TestCase):
    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))
        self.recorder = Recorder()
        self.addCleanup(self.recorder.server_close)
        recorder_thread = threading.Thread(target=self.recorder.serve_forever, daemon=True)
        recorder_thread.start()
        self.addCleanup(recorder_thread.join, 10)
        self.addCleanup(self.recorder.shutdown)   # runs first: stops serve_forever before the join
        port = self.recorder.server_address[1]
        self.proc = subprocess.Popen(
            [NODE, str(HELPER), str(support.HTML), f'http://localhost:{port}/app/'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.addCleanup(self.stop_helper)
        self.url = self.proc.stdout.readline().strip()
        self.assertTrue(self.url.startswith('http://127.0.0.1:'), self.url)
        parts = urlsplit(self.url)
        query = parts.query.split('&')
        self.token = dict(pair.split('=', 1) for pair in query)['token']
        self.url_without_token = urlunsplit(
            parts._replace(query='&'.join(p for p in query if not p.startswith('token='))))

    def stop_helper(self):
        """Stop only the helper this test started: close stdin, wait, kill on timeout."""
        try:
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        finally:
            self.proc.stdout.close()

    def wait_for(self, condition, timeout=15.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return True
            time.sleep(0.05)
        return condition()

    def test_app_sees_no_token_and_no_referer(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = new_context(engine)
                self.contexts.append(context)
                context.route('https://**/*', lambda route: route.abort())   # no third-party contact
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                before = len(self.recorder.snapshot())
                page.goto(self.url)
                # Studio auto-connects to ?target=: its iframe's GET /app/ is the proof.
                self.assertTrue(
                    self.wait_for(lambda: any(p == '/app/' for p, _ in self.recorder.snapshot()[before:])),
                    'Studio never loaded the target in its iframe')
                recorded = self.recorder.snapshot()
                self.assertTrue(page.title().startswith('Font Kit Studio v'), page.title())
                for path, headers in recorded:
                    lowered = {name.lower(): value for name, value in headers.items()}
                    self.assertNotIn('referer', lowered, (path, headers))
                    self.assertNotIn(self.token, path)
                    for value in headers.values():
                        self.assertNotIn(self.token, value, (path, headers))
                self.assertEqual(errors, [])

    def test_url_without_the_token_shows_no_studio(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = new_context(engine)
                self.contexts.append(context)
                context.route('https://**/*', lambda route: route.abort())   # no third-party contact
                page = context.new_page()
                response = page.goto(self.url_without_token)
                self.assertEqual(response.status, 403)
                self.assertNotIn('Font Kit Studio v', response.text())   # the body the server sent
                self.assertEqual(self.recorder.snapshot(), [])


if __name__ == '__main__':
    unittest.main()
