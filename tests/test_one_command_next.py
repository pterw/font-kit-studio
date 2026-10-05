"""Browser test for `fontkitstudio <url>` in front of a real Next.js dev server (R1.7b).

Next runs from the fixture's own install. The proxy must pass Next's HMR WebSocket through, so a
CSS hot update reaches the page without a reload while Studio stays connected and keeps its edit.
Errors are collected with Playwright's `pageerror` and console events (the frame's console
messages arrive on the page's `console` event).
"""

import os
import queue
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlsplit

import support
from fixture_support import FIXTURES, require_fixture
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
PACKAGE = support.REPO / 'packages' / 'fontkitstudio'
BIN = PACKAGE / 'bin' / 'fontkitstudio.js'
APP = FIXTURES / 'next-app'
CONNECTED = r'^Connected \(\d+ targets?\)$'
TITLE = '[data-design-id="next.hero.title"]'
LEAD = '[data-design-id="next.hero.lead"]'
BRIDGE_TAG = 'script[src="/@fontkit/fontkit-bridge.js"]'
TITLE_ID = 'next.hero.title'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def refused(port):
    with socket.socket() as sock:
        sock.settimeout(2)
        return sock.connect_ex(('127.0.0.1', port)) != 0


def spawn_flags():
    return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {}


def interrupt(proc, what):
    """Stop only this process: Ctrl-Break on Windows, SIGINT elsewhere; kill on timeout."""
    if proc.poll() is None:
        proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise AssertionError(f'{what} did not stop on interrupt')


@unittest.skipIf(NODE is None, 'node is not on PATH; the command tests need it')
class OneCommandNextBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([NODE, str(PACKAGE / 'scripts' / 'bundle.js')], cwd=support.REPO, check=True)

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))
        require_fixture(self, 'next-app')

    def start_next(self):
        port = free_port()
        env = dict(os.environ, NEXT_TELEMETRY_DISABLED='1')
        proc = subprocess.Popen(
            [NODE, str(APP / 'node_modules' / 'next' / 'dist' / 'bin' / 'next'), 'dev',
             '--hostname', '127.0.0.1', '--port', str(port)],
            cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
            errors='replace', **spawn_flags())
        self.next_port = port
        self.next_output = []
        self.addCleanup(self.stop_next, proc)
        for stream in (proc.stdout, proc.stderr):
            threading.Thread(target=self.drain, args=(stream,), daemon=True).start()
        deadline = time.monotonic() + 120
        while True:
            self.assertIsNone(proc.poll(), 'next dev exited before answering; output tail:\n' + self.tail())
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=60) as response:
                    if response.status == 200:
                        return port
            except (urllib.error.URLError, OSError):
                pass
            self.assertLess(time.monotonic(), deadline,
                            'next dev did not answer 200 within 120 s; output tail:\n' + self.tail())
            time.sleep(0.5)

    def drain(self, stream):
        for line in stream:
            self.next_output.append(line.rstrip('\r\n'))

    def tail(self):
        return '\n'.join(self.next_output[-40:])

    def stop_next(self, proc):
        """Stop only the Next process this test started, then check its port refuses connections."""
        try:
            interrupt(proc, 'next dev')
            self.assertTrue(refused(self.next_port), 'Next port still open after next dev stopped')
        finally:
            proc.stdout.close()
            proc.stderr.close()

    def start_command(self, port):
        proc = subprocess.Popen(
            [NODE, str(BIN), f'http://localhost:{port}', '--no-open'], cwd=support.REPO,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', **spawn_flags())
        lines = queue.Queue()
        collected = []
        proxy_port = None

        def pump(stream, name):
            for line in stream:
                line = line.rstrip('\r\n')
                collected.append(f'{name}: {line}')
                lines.put((name, line))

        def stop():
            try:
                interrupt(proc, 'the command')
                if proxy_port is not None:   # no Open: line was read, so the port was never learned: skip
                    self.assertTrue(refused(proxy_port), 'proxy port still open after the command stopped')
            finally:
                proc.stdout.close()
                proc.stderr.close()

        self.addCleanup(stop)
        for stream, name in ((proc.stdout, 'out'), (proc.stderr, 'err')):
            threading.Thread(target=pump, args=(stream, name), daemon=True).start()
        while True:
            try:
                name, line = lines.get(timeout=60)
            except queue.Empty:
                self.fail('no "Open:" line within 60 s; output so far:\n' + '\n'.join(collected))
            if name == 'out' and line.startswith('Open: '):
                proxy_port = urlsplit(line[len('Open: '):]).port
                return line[len('Open: '):]

    def wait_badge(self, page, pattern, timeout=15000):
        page.wait_for_function(
            '(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
            arg=pattern, timeout=timeout)

    def select_title(self, page, want=TITLE_ID):
        """Click the title in the iframe; one retry covers the load-time re-hello, which clears it."""
        locator = page.frame_locator('#targetAppFrame').locator(TITLE)
        for attempt in (1, 2):
            locator.click()
            try:
                page.wait_for_function(
                    '(want) => { const el = document.querySelector("#liveTargetName"); return Boolean(el) && el.dataset.targetId === want; }',
                    arg=want, timeout=3000)
                return
            except PlaywrightTimeout:
                if attempt == 2:
                    raise

    def open_studio(self, engine, url):
        context = new_context(engine)
        self.contexts.append(context)
        context.route('https://**/*', lambda route: route.abort())   # no third-party contact
        page = context.new_page()
        errors, console_errors = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        page.goto(url)
        self.wait_badge(page, CONNECTED, timeout=60000)
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        frame.wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        return page, frame, errors, console_errors

    def test_next_edits_live_and_keeps_the_edit_through_a_css_hot_update(self):
        css = APP / 'app' / 'globals.css'
        original = css.read_bytes()
        self.addCleanup(css.write_bytes, original)   # registered before the write
        self.other_console_errors = []
        port = self.start_next()
        url = self.start_command(port)
        target = parse_qs(urlsplit(url).query)['target'][0]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, console_errors = self.open_studio(engine, url)
                self.assertEqual(frame.locator(BRIDGE_TAG).count(), 1)
                self.select_title(page)
                page.locator('#liveFontSize').click()
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('56', delay=60)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).fontSize === "56px"',
                    arg=TITLE, timeout=8000)
                frame.evaluate('window.__fksMarker = 1')
                changed = original.replace(b'rgb(51, 51, 51)', b'rgb(200, 0, 0)')
                self.assertNotEqual(changed, original)
                css.write_bytes(changed)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).color === "rgb(200, 0, 0)"',
                    arg=LEAD, timeout=30000)
                self.assertEqual(frame.evaluate('window.__fksMarker'), 1)   # no reload
                # After an edit the badge reads "Live · rev N": still connected, never idle or lost.
                self.assertIn(page.locator('#bridgeStatusBadge').get_attribute('data-state'), ('connected', 'live'))
                self.assertEqual(
                    frame.evaluate('(s) => getComputedStyle(document.querySelector(s)).fontSize', TITLE),
                    '56px')
                # A second edit proves the live channel survived (the badge state is sticky).
                page.locator('#liveFontSize').click()
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('48', delay=60)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).fontSize === "48px"',
                    arg=TITLE, timeout=8000)
                self.assertEqual(errors, [])
                self.other_console_errors.extend(m for m in console_errors if 'hydrat' not in m.lower())
                self.assertEqual([m for m in console_errors if 'hydrat' in m.lower()], [])
                css.write_bytes(original)   # the next engine starts from the original colour
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).color === "rgb(51, 51, 51)"',
                    arg=LEAD, timeout=30000)
        self.assert_one_tag(target)
        print('non-hydration console errors:', self.other_console_errors)

    def assert_one_tag(self, target):
        with urllib.request.urlopen(target, timeout=30) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode('utf-8')
        self.assertEqual(body.count('<script src="/@fontkit/fontkit-bridge.js"'), 1)


if __name__ == '__main__':
    unittest.main()
