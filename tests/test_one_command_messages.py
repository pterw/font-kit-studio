"""Refusals and page checks of `fontkitstudio` (R1.6).

* A Vite server opened to the network is refused by the real command: one plain line, exit 1,
  no stack, nothing left running.
* Rule 4: through the proxy a Bootstrap page gets exactly the one script tag, and its body is
  the body served directly, before and after a live edit.
* A page whose Content-Security-Policy blocks the bridge is reported once on the terminal and
  Studio does not connect.
"""

import queue
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import support
from fixture_support import FIXTURES, require_fixture
from helpers_csp_server import start_csp_server
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
PACKAGE = support.REPO / 'packages' / 'fontkitstudio'
BIN = PACKAGE / 'bin' / 'fontkitstudio.js'
HELPER = PACKAGE / 'test' / 'helpers' / 'run-proxy.js'
BOOTSTRAP = FIXTURES / 'bootstrap5-static'
HOST_ERROR = 'Font Kit Studio runs only on localhost; remove --host or server.host to use it'
CSP_MESSAGE = (
    "Font Kit Studio: this page's Content-Security-Policy blocks the bridge "
    "(it does not allow the page's own scripts). Add 'self' to script-src while you develop."
)
CONNECTED = r'^Connected \(\d+ targets?\)$'
TITLE = '[data-design-id="bs.hero.title"]'
BRIDGE_TAG = 'script[src="/@fontkit/fontkit-bridge.js"]'
BODY_ELEMENTS = (
    "[...document.body.querySelectorAll('*')]"
    ".map(e => e.tagName + '#' + e.id + '.' + e.className)"
)


@unittest.skipIf(NODE is None, 'node is not on PATH; the command tests need it')
class HostRefusalTest(unittest.TestCase):
    def test_a_server_opened_to_the_network_is_refused_in_one_line(self):
        require_fixture(self, 'vite-react')
        project = Path(tempfile.mkdtemp(prefix='.fks-', dir=FIXTURES / 'vite-react'))
        self.addCleanup(shutil.rmtree, project, ignore_errors=True)
        plugin_url = (PACKAGE / 'src' / 'vite-plugin.js').as_uri()
        (project / 'package.json').write_text(
            '{"name": "fks-host-probe", "private": true, "type": "module", "devDependencies": {"vite": "*"}}\n',
            encoding='utf-8', newline='\n')
        (project / 'vite.config.js').write_text(
            f"import {{ fontkitStudio }} from '{plugin_url}'; "
            "export default { plugins: [fontkitStudio()], server: { host: true } };\n",
            encoding='utf-8', newline='\n')
        result = subprocess.run(
            [NODE, str(BIN), '--no-open'], cwd=project, capture_output=True, text=True,
            encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr.count(HOST_ERROR), 1, result.stderr)
        self.assertEqual(result.stderr.strip(), HOST_ERROR)
        self.assertNotRegex(result.stderr, r'(?m)^\s+at ')
        self.assertNotIn('Open:', result.stdout)


@unittest.skipIf(NODE is None, 'node is not on PATH; the proxy runner tests need it')
class ProxiedPageTest(unittest.TestCase):
    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))

    def serve(self, csp=None):
        """Start a CSP server on the Bootstrap fixture and the proxy runner in front of it.
        Returns (direct page URL, Studio URL, proxied page URL, stderr lines)."""
        server, origin = start_csp_server(BOOTSTRAP) if csp is None else start_csp_server(BOOTSTRAP, csp)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)   # runs first
        proc = subprocess.Popen(
            [NODE, str(HELPER), f'{origin}/index.html', str(support.HTML),
             str(support.REPO / 'fontkit-bridge.js')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding='utf-8')
        errors = queue.Queue()
        self.addCleanup(self.stop_helper, proc)
        threading.Thread(target=lambda: [errors.put(line.rstrip('\r\n')) for line in proc.stderr],
                         daemon=True).start()
        self.assertEqual(proc.stdout.readline().strip(), 'Font Kit Studio · dev only')
        line = proc.stdout.readline().strip()
        self.assertTrue(line.startswith('Open: http://127.0.0.1:'), line)
        studio = line[len('Open: '):]
        return f'{origin}/index.html', studio, parse_qs(urlsplit(studio).query)['target'][0], errors

    @staticmethod
    def stop_helper(proc):
        """Stop only the helper this test started: close stdin, wait, kill on timeout."""
        try:
            proc.stdin.close()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        finally:
            proc.stdout.close()
            proc.stderr.close()

    def new_page(self, engine):
        context = new_context(engine)
        self.contexts.append(context)
        context.route('https://**/*', lambda route: route.abort())   # no third-party contact
        return context.new_page()

    def wait_badge(self, page, pattern, timeout=15000):
        page.wait_for_function(
            '(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
            arg=pattern, timeout=timeout)

    def open_studio(self, page, url):
        page.goto(url)
        self.wait_badge(page, CONNECTED)
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        frame.wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        return frame

    def select_title(self, page):
        """Click the title in the iframe; one retry covers the load-time re-hello, which clears it."""
        locator = page.frame_locator('#targetAppFrame').locator(TITLE)
        for attempt in (1, 2):
            locator.click()
            try:
                page.wait_for_function(
                    '(want) => { const el = document.querySelector("#liveTargetName"); return Boolean(el) && el.dataset.targetId === want; }',
                    arg='bs.hero.title', timeout=3000)
                return
            except PlaywrightTimeout:
                if attempt == 2:
                    raise

    def test_the_proxied_page_gains_only_the_one_script_tag(self):
        direct_url, studio_url, proxied_url, errors = self.serve()
        for engine in ENGINES:
            with self.subTest(engine=engine):
                direct = self.new_page(engine)
                direct.goto(direct_url)
                direct.wait_for_load_state('load')
                proxied = self.new_page(engine)
                proxied.goto(proxied_url)
                proxied.wait_for_load_state('load')
                before = direct.evaluate(BODY_ELEMENTS)
                self.assertGreater(len(before), 3, 'the page body looks empty')
                self.assertEqual(proxied.evaluate(BODY_ELEMENTS), before)
                self.assertEqual(direct.locator(f'head {BRIDGE_TAG}').count(), 0)
                self.assertEqual(proxied.locator(f'head {BRIDGE_TAG}').count(), 1)
                self.assertEqual(proxied.locator('[data-fontkit-font]').count(), 0)

                studio = self.new_page(engine)
                frame = self.open_studio(studio, studio_url)
                self.select_title(studio)
                studio.locator('#liveFontSize').click()
                studio.keyboard.press('Control+A')
                studio.keyboard.type('56', delay=60)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).fontSize === "56px"',
                    arg=TITLE, timeout=8000)
                self.assertEqual(frame.evaluate(BODY_ELEMENTS), before)
        self.assertTrue(errors.empty(), 'the helper wrote to stderr for a page with no problem')

    def test_a_policy_that_blocks_the_bridge_is_reported_once_and_studio_stays_unconnected(self):
        _, studio_url, proxied_url, errors = self.serve(csp="script-src 'nonce-abc'")
        for engine in ENGINES:
            with self.subTest(engine=engine):
                studio = self.new_page(engine)
                studio.goto(studio_url)
                frame = studio.locator('#targetAppFrame').element_handle().content_frame()
                frame.wait_for_function('document.readyState === "complete"')
                with self.assertRaises(PlaywrightTimeout):   # a negative needs a short wait
                    self.wait_badge(studio, CONNECTED, timeout=5000)
                self.assertEqual(frame.locator(BRIDGE_TAG).count(), 1)
        self.assertEqual(errors.get(timeout=10), CSP_MESSAGE)
        with self.assertRaises(queue.Empty):
            errors.get(timeout=1)
        self.assertTrue(proxied_url.startswith('http://127.0.0.1:'))


if __name__ == '__main__':
    unittest.main()
