"""Browser test for `fontkitstudio <url>` (R1.5b): Studio plus the proxy over a Bootstrap 5 page.

The page is served by tests/helpers_csp_server.py with Content-Security-Policy
`script-src 'self'; style-src 'self'`. The proxy runner (packages/fontkitstudio/src/run-proxy.js)
sits in front of it; Studio opens the proxied page in its iframe, selects the title, and sets its
font size, with no CSP violation in either document and no request to an https origin.
"""

import shutil
import subprocess
import unittest
import urllib.request
from urllib.parse import parse_qs, urlsplit

import support
from helpers_csp_server import CSP, start_csp_server
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
HELPER = support.REPO / 'packages' / 'fontkitstudio' / 'test' / 'helpers' / 'run-proxy.js'
FIXTURE = support.REPO / 'fixtures' / 'bootstrap5-static'
CONNECTED = r'^Connected \(\d+ targets?\)$'
TITLE = '[data-design-id="bs.hero.title"]'

RECORD_VIOLATIONS = """
window.__cspViolations = [];
document.addEventListener('securitypolicyviolation', (event) => {
  window.__cspViolations.push(event.violatedDirective + ' ' + event.blockedURI);
});
"""


@unittest.skipIf(NODE is None, 'node is not on PATH; the proxy runner tests need it')
class OneCommandProxyBrowserTest(unittest.TestCase):
    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))
        server, self.origin = start_csp_server(FIXTURE)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)   # runs first
        port = server.server_address[1]
        self.proc = subprocess.Popen(
            [NODE, str(HELPER), f'http://localhost:{port}/index.html', str(support.HTML),
             str(support.REPO / 'fontkit-bridge.js')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
        self.addCleanup(self.stop_helper)
        self.assertEqual(self.proc.stdout.readline().strip(), 'Font Kit Studio · dev only')
        line = self.proc.stdout.readline().strip()
        self.assertTrue(line.startswith('Open: http://localhost:'), line)
        self.url = line[len('Open: '):]
        self.proxied = parse_qs(urlsplit(self.url).query)['target'][0]

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
                    arg='bs.hero.title', timeout=3000)
                return
            except PlaywrightTimeout:
                if attempt == 2:
                    raise

    def test_page_through_the_proxy_keeps_its_csp_and_gets_the_one_tag(self):
        with urllib.request.urlopen(self.proxied) as response:
            body = response.read().decode('utf-8')
            self.assertEqual(response.headers['Content-Security-Policy'], CSP)
        self.assertEqual(body.count('<script src="/@fontkit/fontkit-bridge.js"'), 1)
        self.assertEqual(body.count('fontkit-bridge.js'), 1)

    def test_studio_edits_a_page_whose_csp_allows_only_itself(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = new_context(engine)
                self.contexts.append(context)
                context.route('https://**/*', lambda route: route.abort())   # no third-party contact
                context.add_init_script(RECORD_VIOLATIONS)
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(self.url)
                self.wait_badge(page, CONNECTED)
                frame = page.locator('#targetAppFrame').element_handle().content_frame()
                frame.wait_for_function('document.readyState === "complete"')
                self.wait_badge(page, CONNECTED)
                self.select_title(page)
                page.locator('#liveFontSize').click()
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('56', delay=60)
                frame.wait_for_function(
                    '(s) => getComputedStyle(document.querySelector(s)).fontSize === "56px"',
                    arg=TITLE, timeout=8000)
                self.assertEqual(frame.evaluate('window.__cspViolations'), [])
                self.assertEqual(page.evaluate('window.__cspViolations'), [])
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
