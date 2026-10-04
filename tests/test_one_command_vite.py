"""Browser test for `fontkitstudio` run in a Vite project (R1.4d): the real command, on both fixtures.

The command runs the fixture's own Vite with the plugin added in memory. Each fixture's config
already holds a permanent `fontkitStudio()`, so the page must still carry exactly one bridge tag.
The hot-update test edits `src/app.css`: the fixtures have no React Fast Refresh, so a JSX edit
would reload the page and Studio would (rightly) ask before re-applying edits.
"""

import queue
import shutil
import signal
import socket
import subprocess
import sys
import threading
import unittest
from urllib.parse import parse_qs, urlsplit

import support
from fixture_support import FIXTURES, require_fixture
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
PACKAGE = support.REPO / 'packages' / 'fontkitstudio'
BIN = PACKAGE / 'bin' / 'fontkitstudio.js'
CONNECTED = r'^Connected \(\d+ targets?\)$'
TITLE = '[data-design-id="vite.hero.title"]'
BRIDGE_TAG = 'script[src="/@fontkit/fontkit-bridge.js"]'


def refused(port):
    with socket.socket() as sock:
        sock.settimeout(2)
        return sock.connect_ex(('127.0.0.1', port)) != 0


@unittest.skipIf(NODE is None, 'node is not on PATH; the command tests need it')
class OneCommandViteBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([NODE, str(PACKAGE / 'scripts' / 'bundle.js')], cwd=support.REPO, check=True)

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))

    def start(self, fixture):
        """Run the command in the fixture; return the Studio URL it prints."""
        require_fixture(self, fixture)
        flags = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {}
        proc = subprocess.Popen(
            [NODE, str(BIN), '--no-open'], cwd=FIXTURES / fixture, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8', **flags)
        self.lines = queue.Queue()
        self.collected = []
        self.studio_port = self.app_port = None
        self.addCleanup(self.stop, proc)
        for stream, name in ((proc.stdout, 'out'), (proc.stderr, 'err')):
            threading.Thread(target=self.pump, args=(stream, name), daemon=True).start()
        previous = None
        while True:
            try:
                name, line = self.lines.get(timeout=60)
            except queue.Empty:
                self.fail('no "Open:" line within 60 s; output so far:\n' + '\n'.join(self.collected))
            if name != 'out':
                continue
            if line.startswith('Open: '):
                break
            previous = line
        self.assertEqual(previous, 'Font Kit Studio · dev only', self.collected)
        self.assertFalse([x for x in self.collected if x.startswith('  Font Kit Studio: ')], self.collected)
        url = line[len('Open: '):]
        self.studio_port = urlsplit(url).port
        self.app_port = urlsplit(parse_qs(urlsplit(url).query)['target'][0]).port
        return url

    def pump(self, stream, name):
        for line in stream:
            line = line.rstrip('\r\n')
            self.collected.append(line if name == 'out' else f'err: {line}')
            self.lines.put((name, line))

    def stop(self, proc):
        """Stop only the command this test started, then check both ports are free."""
        try:
            if proc.poll() is None:
                proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    self.fail('the command did not stop')
            for port, what in ((self.studio_port, 'Studio'), (self.app_port, 'Vite')):
                if port is not None:
                    self.assertTrue(refused(port), f'{what} port still open after the command stopped')
        finally:
            proc.stdout.close()
            proc.stderr.close()

    def wait_badge(self, page, pattern, timeout=15000):
        page.wait_for_function(
            '(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
            arg=pattern, timeout=timeout)

    def select_title(self, page):
        """Click the title in the iframe; one retry covers the load-time re-hello, which clears it."""
        locator = page.frame_locator('#targetAppFrame').locator(TITLE)
        for attempt in (1, 2):
            locator.click()
            try:
                page.wait_for_function(
                    '(want) => { const el = document.querySelector("#liveTargetName"); return Boolean(el) && el.dataset.targetId === want; }',
                    arg='vite.hero.title', timeout=3000)
                return
            except PlaywrightTimeout:
                if attempt == 2:
                    raise

    def open_studio(self, engine, url):
        context = new_context(engine)
        self.contexts.append(context)
        context.route('https://**/*', lambda route: route.abort())   # no third-party contact
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        self.wait_badge(page, CONNECTED)
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        frame.wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        self.assertEqual(frame.locator(BRIDGE_TAG).count(), 1)
        return page, frame, errors

    def test_vite7_connects_with_one_bridge_tag(self):
        url = self.start('vite7-react')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                _, _, errors = self.open_studio(engine, url)
                self.assertEqual(errors, [])

    def test_vite_edits_live_and_keeps_the_edit_through_a_css_hot_update(self):
        css = FIXTURES / 'vite-react' / 'src' / 'app.css'
        original = css.read_bytes()
        self.addCleanup(css.write_bytes, original)   # registered before the write
        url = self.start('vite-react')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open_studio(engine, url)
                self.select_title(page)
                page.locator('#liveFontSize').click()
                page.keyboard.press('Control+A')
                page.keyboard.type('56', delay=60)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).fontSize === "56px"',
                    arg=TITLE, timeout=8000)
                css.write_bytes(original + b'\nbody { background-color: rgb(1, 2, 3); }\n')
                frame.wait_for_function(
                    '() => getComputedStyle(document.body).backgroundColor === "rgb(1, 2, 3)"',
                    timeout=15000)
                self.assertEqual(
                    frame.evaluate('(s) => getComputedStyle(document.querySelector(s)).fontSize', TITLE),
                    '56px')
                # After an edit the badge reads "Live · rev N": still connected, never idle or lost.
                self.assertIn(page.locator('#bridgeStatusBadge').get_attribute('data-state'), ('connected', 'live'))
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
