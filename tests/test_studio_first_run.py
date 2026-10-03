"""First run in Studio (v0.2.1 Task 3): what a new user sees before anything is connected.

Two groups:
  * Fake-target tests (LiveCase): Studio on http://studio.test, a bridge-less page or the
    fake bridge on http://target.test, so every origin check runs in a real browser.
  * Dev-server tests (LiveIntegrationCase): the real scripts/serve.py, Studio over
    http://localhost and the real demo, for the demo offer and the favicon.
"""

import json
import re
import unittest
import urllib.parse
import urllib.request
import xml.dom.minidom

from support import ENGINES, HTML, REPO
from test_live_integration import CONNECTED, LiveIntegrationCase, free_ports
from test_studio_live import APP, EVIL, FAKE, TARGET, LiveCase

NEED_URL = "Enter your app's URL"
FULL_URL = 'Use a full URL starting with http:// or https://'
NO_BRIDGE_HINT = ('Either nothing is running there, or the page does not load fontkit-bridge.js. '
                  'Add <script src="fontkit-bridge.js"> after the page\'s own scripts, reload it, then press Connect Target.')
SERVE_LINE = 'Start the dev server: python scripts/serve.py'
BLOCKED = ('Browsers block a web page from reaching localhost. '
           'Open Studio from the dev server (python scripts/serve.py) or from the file on disk instead.')


def one_line(text):
    return re.sub(r'\s+', ' ', text).strip()


class TargetUrlFieldTests(LiveCase):
    def composer(self, engine, **options):
        page, errors = self.open(engine, target=None, **options)
        page.locator('#modeComposer').click()
        return page, errors

    def type_keys(self, page, text):
        page.locator('#targetAppUrl').click()
        page.keyboard.type(text, delay=20)

    def test_an_empty_field_disables_connect_with_the_reason_and_typing_enables_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                button = page.locator('#btnConnectTarget')
                self.assertTrue(button.is_disabled())
                self.assertEqual(button.get_attribute('title'), NEED_URL)
                self.assertTrue(page.locator('#targetUrlHint').is_visible())
                self.assertEqual(page.locator('#targetUrlHint').inner_text(), NEED_URL)
                self.type_keys(page, 'h')
                self.assertFalse(button.is_disabled())
                self.assertFalse(page.locator('#targetUrlHint').is_visible())
                self.assertNotEqual(button.get_attribute('title'), NEED_URL)
                page.keyboard.press('Backspace')
                self.assertTrue(button.is_disabled())
                self.assertTrue(page.locator('#targetUrlHint').is_visible())
                self.assertEqual(errors, [])

    def test_nothing_connects_to_a_hard_coded_default(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                page.locator('#targetAppUrl').press('Enter')
                page.locator('#viewTargetApp').click()
                page.wait_for_timeout(300)  # proves a negative: nothing may start loading
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Idle')
                self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                self.assertEqual(errors, [])

    def test_a_url_without_a_scheme_is_refused_and_nothing_loads(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                for probe in ('localhost:8001/demo/', 'example.com/app', '//example.com/app', 'demo/'):
                    self.connect(page, probe)
                    self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), FULL_URL, probe)
                    self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'), probe)
                    page.locator('#targetAppUrl').press('Enter')
                    self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'), probe)
                # A refused URL leaves a connected target alone.
                self.connect(page, FAKE)
                self.wait_connected(page)
                page.locator('#targetAppUrl').fill('example.com/app')
                page.locator('#btnConnectTarget').click()
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), FULL_URL)
                self.assertEqual(page.locator('#targetAppFrame').get_attribute('src'), FAKE)
                self.assertEqual(errors, [])

    def test_other_schemes_keep_their_own_refusal(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.connect(page, 'javascript:parent.__pwned=1')
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Invalid target URL')
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                self.assertEqual(errors, [])

    def test_importing_a_composition_with_a_live_target_enables_connect(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.assertTrue(page.locator('#btnConnectTarget').is_disabled())
                exported = self.export(page)
                self.import_document(page, {**exported, 'live': {'target': FAKE, 'revision': 1, 'overrides': {}}})
                self.assertEqual(page.locator('#targetAppUrl').input_value(), FAKE)
                self.assertFalse(page.locator('#btnConnectTarget').is_disabled())
                self.assertFalse(page.locator('#targetUrlHint').is_visible())
                # The import fills the field; it does not connect.
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                self.assertEqual(errors, [])

    def test_pop_out_with_an_empty_field_asks_for_a_url_and_opens_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                opened = []
                page.context.on('page', lambda new: opened.append(new.url))
                page.evaluate("() => { window.__opens = 0; const open = window.open; window.open = (...args) => { window.__opens += 1; return open.apply(window, args); }; }")
                page.locator('#bridgePopOut').click()
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), NEED_URL)
                page.wait_for_timeout(300)  # proves a negative: no window may open
                self.assertEqual(page.evaluate('window.__opens'), 0)
                self.assertEqual(opened, [])
                self.assertFalse(page.locator('#bridgePopoutPlaceholder').is_visible())
                self.assertEqual(errors, [])

    def test_a_recursion_block_leaves_the_field_empty_and_connect_disabled(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.connect(page, APP)
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Recursion blocked')
                self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                self.assertTrue(page.locator('#btnConnectTarget').is_disabled())
                self.assertEqual(errors, [])


class NoBridgeMessageTests(LiveCase):
    def test_no_bridge_names_the_origin_and_the_two_causes(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{TARGET}/no-bridge.html')
                self.wait_badge(page, '^Connecting…$')
                self.wait_badge(page, r'^No bridge answered at http://target\.test within 4 s\.$', timeout=7000)
                hint = page.locator('#bridgeHint')
                self.assertTrue(hint.is_visible())
                self.assertIn(NO_BRIDGE_HINT, one_line(hint.inner_text()))
                self.assertNotIn(SERVE_LINE, hint.inner_text())  # Studio is served, not a file
                self.assertEqual(errors, [])

    def test_a_studio_opened_from_disk_adds_the_dev_server_line(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{HTML.as_uri()}?target={urllib.parse.quote(TARGET + "/no-bridge.html", safe="")}')
                self.wait_badge(page, r'^No bridge answered at http://target\.test within 4 s\.$', timeout=7000)
                hint = one_line(page.locator('#bridgeHint').inner_text())
                self.assertIn(NO_BRIDGE_HINT, hint)
                self.assertIn(SERVE_LINE, hint)
                self.assertEqual(errors, [])

    def test_a_web_page_cannot_reach_localhost_and_studio_says_so(self):
        port = free_ports(1)[0]  # nothing listens here, as when the browser blocks the request
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'http://localhost:{port}/')
                self.wait_badge(page, '^' + re.escape(BLOCKED) + '$', timeout=7000)
                self.assertEqual(errors, [])

    def test_a_remote_target_is_not_blamed_on_localhost(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{EVIL}/no-bridge.html')
                self.wait_badge(page, r'^No bridge answered at http://evil\.test within 4 s\.$', timeout=7000)
                self.assertEqual(errors, [])


class NoDemoOfferTests(LiveCase):
    def test_nothing_is_prefilled_from_a_file_or_another_origin(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                # studio.test answers /__fontkit/status like the dev server does, but it is not loopback.
                page, errors = self.open(engine, target=None, sync=True)
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect Target')
                self.assertEqual(errors, [])
                context = self.context(engine, sync=True)
                page = context.new_page()
                page.goto(HTML.as_uri())
                page.locator('#modeComposer').click()
                page.wait_for_timeout(300)  # proves a negative: no prefill may arrive late
                self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect Target')


class FullscreenTests(LiveCase):
    def test_fullscreen_does_not_connect_to_the_typed_url(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)
                page.locator('#modeComposer').click()
                page.locator('#targetAppUrl').fill(FAKE)
                page.locator('#btnToggleFullscreen').click()
                page.wait_for_function('document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                page.wait_for_timeout(300)  # proves a negative: no load may start
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Idle')
                page.locator('#btnExitFullscreen').click()
                # Connecting is still one explicit press away.
                page.locator('#btnConnectTarget').click()
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertEqual(len(self.received(frame, 'design:hello')) >= 1, True)
                self.assertEqual(errors, [])

    def test_the_target_tab_still_connects_when_pressed(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)
                page.locator('#modeComposer').click()
                page.locator('#targetAppUrl').fill(FAKE)
                page.locator('#viewTargetApp').click()
                self.wait_connected(page)
                self.assertEqual(errors, [])


class DemoOfferTests(LiveIntegrationCase):
    def test_the_dev_server_offers_the_demo_and_connects_only_when_asked(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open(engine, query=False)
                target_requests = []
                page.on('request', lambda request: target_requests.append(request.url)
                        if f':{self.target_port}' in request.url else None)
                page.locator('#modeComposer').click()
                page.wait_for_function('(url) => document.querySelector("#targetAppUrl").value === url', arg=self.target)
                button = page.locator('#btnConnectTarget')
                self.assertEqual(button.inner_text(), 'Connect to the demo')
                self.assertFalse(button.is_disabled())
                page.wait_for_timeout(500)  # proves a negative: the offer must not connect by itself
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Idle')
                self.assertEqual(target_requests, [])
                button.click()
                self.wait_badge(page, CONNECTED)
                self.assertTrue(any(url.startswith(self.target) for url in target_requests), target_requests)
                self.assertEqual(page.errors, [])

    def served_status(self, target):
        """Studio's own dev server answers /__fontkit/status; here the answer is whatever the test says."""
        body = json.dumps({'sync': True, 'overrides': 'demo/fontkit-overrides.css', 'target': target})
        self.runtime_context_hook = lambda context: context.route(
            f'{self.studio}/__fontkit/status',
            lambda route: route.fulfill(status=200, content_type='application/json', body=body))

    def open_after_status(self, engine):
        page = self.open(engine, query=False)
        page.locator('#modeComposer').click()
        # Sync is enabled in the same step that decides the offer, so the decision is made by then.
        page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
        return page

    def test_a_hostile_status_target_is_never_offered(self):
        port = self.studio_port
        hostile = ('javascript:parent.__pwned=1', 'data:text/html,<script>parent.__pwned=1</script>', 'demo/',
                   '//evil.example/x', 'http://evil.example/', 'https://evil.example:8001/demo/',
                   f'ftp://localhost:{port}/x',
                   f'http://127.0.0.1:{port}/{HTML.name}', f'http://localhost:{port}/{HTML.name}?x=1', self.app)
        for engine in ENGINES:
            for probe in hostile:
                with self.subTest(engine=engine, status_target=probe):
                    self.served_status(probe)
                    page = self.open_after_status(engine)
                    self.assertEqual(page.locator('#targetAppUrl').input_value(), '')
                    button = page.locator('#btnConnectTarget')
                    self.assertTrue(button.is_disabled())
                    self.assertEqual(button.inner_text(), 'Connect Target')
                    self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                    self.assertIsNone(page.evaluate('window.__pwned'))
                    self.assertEqual(page.errors, [])

    def test_a_status_target_on_the_loopback_is_offered(self):
        # The control for the hostile cases: the route works, and a loopback demo under another alias is accepted.
        alias = self.target.replace('localhost', '127.0.0.1')
        for engine in ENGINES:
            for offered in (self.target, alias):
                with self.subTest(engine=engine, status_target=offered):
                    self.served_status(offered)
                    page = self.open_after_status(engine)
                    self.assertEqual(page.locator('#targetAppUrl').input_value(), offered)
                    self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect to the demo')
                    self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))

    def test_editing_the_prefilled_address_drops_the_demo_label(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open(engine, query=False)
                page.locator('#modeComposer').click()
                page.wait_for_function('(url) => document.querySelector("#targetAppUrl").value === url', arg=self.target)
                page.locator('#targetAppUrl').click()
                page.keyboard.press('End')
                page.keyboard.type('x', delay=20)
                self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect Target')
                page.keyboard.press('Backspace')
                self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect to the demo')
                self.assertEqual(page.errors, [])

    def test_a_target_in_the_address_wins_over_the_offer(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.assertEqual(page.locator('#targetAppUrl').input_value(), self.target)
                self.assertEqual(page.locator('#btnConnectTarget').inner_text(), 'Connect Target')

    def test_no_bridge_on_a_loopback_target_names_that_origin_and_is_not_blamed_on_localhost(self):
        (self.scratch / 'plain.html').write_text('<!doctype html><p>No script tag here.</p>', encoding='utf-8')
        plain = f'http://localhost:{self.target_port}/{self.scratch.relative_to(REPO).as_posix()}/plain.html'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open(engine, query=False)
                page.goto(f'{self.app}?target={urllib.parse.quote(plain, safe=":/")}')
                self.wait_badge(page, rf'^No bridge answered at http://localhost:{self.target_port} within 4 s\.$', timeout=15000)
                hint = one_line(page.locator('#bridgeHint').inner_text())
                self.assertIn(NO_BRIDGE_HINT, hint)
                self.assertNotIn(SERVE_LINE, hint)
                self.assertEqual(page.errors, [])


class FaviconTests(LiveIntegrationCase):
    def icon(self, html):
        match = re.search(r'<link\s+rel="icon"[^>]*href="(data:image/svg\+xml[^"]+)"', html)
        self.assertIsNotNone(match, 'no inline SVG <link rel="icon">')
        header, _, payload = match.group(1).partition(',')
        svg = urllib.parse.unquote(payload)
        xml.dom.minidom.parseString(svg)  # well-formed
        self.assertIn('<svg', svg)
        self.assertNotRegex(svg, r'(?i)(href|src)=|url\(')  # nothing it could fetch
        return svg

    def fetch(self, url):
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return response.read().decode('utf-8')

    def test_studio_and_the_demo_carry_an_inline_favicon(self):
        self.icon(self.fetch(self.app))
        self.icon(self.fetch(self.target))

    def test_no_favicon_file_is_requested_and_the_icon_needs_no_network(self):
        # Headless Chromium may never ask for a favicon, so the markup assertions above carry the proof;
        # this checks that when a page loads, nothing asks the server for /favicon.ico.
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open(engine)
                requests = []
                page.on('request', lambda request: requests.append(request.url))
                self.wait_badge(page, CONNECTED)
                href = page.evaluate('document.querySelector("link[rel~=icon]").href')
                self.assertTrue(href.startswith('data:image/svg+xml'), href[:40])
                frame_href = self.frame(page).evaluate('document.querySelector("link[rel~=icon]").href')
                self.assertTrue(frame_href.startswith('data:image/svg+xml'), frame_href[:40])
                self.assertEqual([url for url in requests if 'favicon' in url], [])
                self.assertEqual(page.errors, [])


if __name__ == '__main__':
    unittest.main()
