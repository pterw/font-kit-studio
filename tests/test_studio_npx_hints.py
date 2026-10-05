"""Studio's hints under `npx fontkitstudio` (R1.8b).

Studio served by the package's own server (a per-run ?token=) has no /__fontkit/status and no
bridge to add by hand, so its Sync and bridge messages must not send the user to scripts/serve.py.
Under scripts/serve.py, or with no token, the messages stay as they were.
"""

import shutil
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import ENGINES, close_contexts, new_context  # noqa: E402
from test_preview_server import Server, free_ports  # noqa: E402

NODE = shutil.which('node')
HELPER = support.REPO / 'packages' / 'fontkitstudio' / 'test' / 'helpers' / 'serve-studio.js'

NPX_BRIDGE_HINT = ('npx fontkitstudio adds the bridge to the page itself. If Font Kit Studio does not '
                   'connect, the terminal where the command runs says why.')
NPX_SYNC = 'Sync to file is not available under npx fontkitstudio. Use Copy or Download in the CSS tab.'
OLD_SYNC = ('No Font Kit dev server answered /__fontkit/status. '
            'Run python scripts/serve.py to enable Sync to file.')
OLD_BRIDGE_START = 'Either nothing is running there, or the page does not load fontkit-bridge.js.'
OLD_BRIDGE_SCRIPT = '<script src="fontkit-bridge.js"></script>'
NPX_BADGE_TITLE = 'npx fontkitstudio adds the bridge to the page itself.'
NPX_EMPTY = ('Enter the URL of a localhost app, then press Connect Live App. '
             'npx fontkitstudio adds the bridge to the page itself.')
OLD_EMPTY = 'Enter the URL of a localhost app that loads fontkit-bridge.js, then press Connect Live App.'
CHECKING = 'Checking for the Font Kit dev server…'


class PlainStudioHandler(BaseHTTPRequestHandler):
    """Serves Studio and nothing else, like the package's server: /__fontkit/status is a 404."""

    def do_GET(self):
        if self.path.split('?')[0] != '/fontkit-studio.html':
            self.send_error(404)
            return
        body = support.HTML.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class HintsCase(unittest.TestCase):
    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))

    def open(self, engine, url):
        context = new_context(engine)
        self.contexts.append(context)
        context.route('https://**/*', lambda route: route.abort())   # no third-party contact
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        return page, errors

    def wait_no_bridge(self, page):
        page.locator('#bridgeStatusBadge').filter(has_text='No bridge answered').wait_for(timeout=9000)

    def sync_title(self, page):
        # The Sync button's title carries the reason it is off; the Sync hint line repeats it as text.
        return page.locator('#liveCodeSync').get_attribute('title')

    def wait_sync_checked(self, page):
        page.wait_for_function(
            'title => document.getElementById("liveCodeSync").title !== title', arg=CHECKING, timeout=9000)


@unittest.skipIf(NODE is None, 'node is not on PATH; the Studio server tests need it')
class UnderThePackageTest(HintsCase):
    def setUp(self):
        super().setUp()
        port = free_ports(1)[0]   # nothing listens here
        self.target = f'http://127.0.0.1:{port}/app/'
        self.proc = subprocess.Popen(
            [NODE, str(HELPER), str(support.HTML), self.target],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.addCleanup(self.stop_helper)
        self.url = self.proc.stdout.readline().strip()
        self.assertTrue(self.url.startswith('http://127.0.0.1:'), self.url)

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

    def test_the_hints_say_what_an_npx_user_can_do(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, self.url)
                self.wait_no_bridge(page)
                self.wait_sync_checked(page)
                hint = page.locator('#bridgeHint')
                self.assertTrue(hint.is_visible())
                self.assertEqual(' '.join(hint.inner_text().split()), NPX_BRIDGE_HINT)
                self.assertEqual(self.sync_title(page), NPX_SYNC)
                self.assertTrue(page.locator('#liveCodeSync').is_disabled())
                self.assertEqual(page.locator('#liveCodeSyncHint').text_content(), NPX_SYNC)
                badge_title = page.locator('#bridgeStatusBadge').get_attribute('title')
                self.assertEqual(badge_title, NPX_BADGE_TITLE)
                for text in (hint.inner_text(), self.sync_title(page), badge_title):
                    self.assertNotIn('serve.py', text)
                    self.assertNotIn('fontkit-bridge.js', text)
                self.assertEqual(errors, [])

    def test_the_empty_inspector_does_not_ask_for_a_bridge_script(self):
        # Opened with no target, Composer shows the empty Live App inspector.
        url = self.url.replace('&target=', '&unused=').replace('?target=', '?unused=')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, url)
                page.locator('#modeComposer').click()
                page.locator('#viewTargetApp').click()
                empty = page.locator('#slotInspector .empty-inspector')
                empty.wait_for(timeout=9000)
                self.assertEqual(empty.text_content(), NPX_EMPTY)
                self.assertEqual(errors, [])


class WithoutThePackageTest(HintsCase):
    def test_serve_py_keeps_its_bridge_hint_and_sync_wording(self):
        server = Server()
        self.addCleanup(server.close)
        gone = free_ports(1)[0]   # nothing listens here
        url = f'http://127.0.0.1:{server.studio}/fontkit-studio.html?target=http://127.0.0.1:{gone}/'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, url)
                self.wait_no_bridge(page)
                self.wait_sync_checked(page)
                hint = ' '.join(page.locator('#bridgeHint').inner_text().split())
                self.assertTrue(hint.startswith(OLD_BRIDGE_START), hint)
                self.assertIn(OLD_BRIDGE_SCRIPT, hint)
                self.assertNotIn('npx', hint)
                # Sync is on here; Auto-sync's title keeps the dev server's own sentence.
                auto = page.locator('#liveCodeAutoSync').get_attribute('title')
                self.assertIn('through the Font Kit dev server', auto)
                self.assertNotIn('npx', auto)
                self.assertNotEqual(self.sync_title(page), NPX_SYNC)
                self.assertEqual(page.locator('#bridgeStatusBadge').get_attribute('title'),
                                 'Add fontkit-bridge.js to the Live App page.')
                self.assertEqual(errors, [])

    def serve_plain(self):
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), PlainStudioHandler)
        httpd.daemon_threads = True
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 10)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)   # runs first: stops serve_forever before the join
        return httpd.server_address[1]

    def test_with_no_token_the_empty_inspector_keeps_its_wording(self):
        port = self.serve_plain()
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, f'http://127.0.0.1:{port}/fontkit-studio.html')
                page.locator('#modeComposer').click()
                page.locator('#viewTargetApp').click()
                empty = page.locator('#slotInspector .empty-inspector')
                empty.wait_for(timeout=9000)
                self.assertEqual(empty.text_content(), OLD_EMPTY)
                self.assertEqual(errors, [])

    def test_with_no_token_or_an_empty_one_the_old_wording_stays(self):
        port = self.serve_plain()
        gone = free_ports(1)[0]
        for query in (f'target=http://127.0.0.1:{gone}/', f'token=&target=http://127.0.0.1:{gone}/'):
            for engine in ENGINES:
                with self.subTest(engine=engine, query=query):
                    page, errors = self.open(engine, f'http://127.0.0.1:{port}/fontkit-studio.html?{query}')
                    self.wait_no_bridge(page)
                    self.wait_sync_checked(page)
                    self.assertEqual(self.sync_title(page), OLD_SYNC)
                    hint = ' '.join(page.locator('#bridgeHint').inner_text().split())
                    self.assertIn(OLD_BRIDGE_SCRIPT, hint)
                    self.assertNotIn('npx', hint)
                    self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
