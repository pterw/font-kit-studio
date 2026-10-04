"""End-to-end: real Studio + real bridge + demo app, served by the real scripts/serve.py.

Nothing here is faked. A `scripts/serve.py` subprocess runs on two OS-assigned loopback
ports (Studio on one, the demo app on the other, so they stay cross-origin), and
Chromium loads the real Studio over http://localhost, which makes the real clipboard
available. Studio talks to `fontkit-bridge.js` inside `demo/index.html` over real
`postMessage`.

Two pieces of test plumbing, both explained where they appear:
  * Google Fonts requests are answered with empty CSS, so the suite stays offline.
  * The demo always links `demo/fontkit-overrides.css`, but each test writes to its own
    temporary overrides path inside the repo. The request for the demo's stylesheet is
    redirected (same server, new path) to that file, so the browser still fetches what the
    real server wrote to disk.
"""

import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ENGINES, HTML, REPO, close_contexts, launch, new_context, shared_runtime  # noqa: E402

SERVE = REPO / 'scripts' / 'serve.py'
TITLE = '[data-design-id="landing.hero.title"]'
CONNECTED = r'^Connected \(\d+ targets?\)$'
README = (REPO / 'README.md').read_text(encoding='utf-8')


def readme_snippet(pattern, what):
    """A code line from the README, so the test runs what the README tells users to run."""
    match = re.search(pattern, README, re.M)
    assert match, f'README has no {what}'
    return match.group(1)


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


class LiveIntegrationCase(unittest.TestCase):
    def setUp(self):
        work = REPO / 'work'  # gitignored scratch
        work.mkdir(exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(prefix='live-integration-', dir=work))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.overrides = self.scratch / 'overrides.css'
        self.rel = self.overrides.relative_to(REPO).as_posix()
        self.proc = None
        self.start_server()
        self.addCleanup(self.stop_server)
        self.runtime = shared_runtime()   # one driver and one browser per engine per process (support.py)
        self.browsers = []                # browsers a test launches itself; closed below
        self.contexts = []                # one fresh context per test, closed below
        self.addCleanup(self.close_browsers)

    # ---- server --------------------------------------------------------
    def start_server(self):
        for _ in range(3):  # a port can be taken between "free" and "bound"
            self.studio_port, self.target_port = free_ports()
            self.log = open(self.scratch / 'serve.log', 'w+')
            self.proc = subprocess.Popen(
                [sys.executable, str(SERVE), '--quiet', '--studio-port', str(self.studio_port),
                 '--target-port', str(self.target_port), '--overrides', self.rel],
                cwd=REPO, stdout=self.log, stderr=subprocess.STDOUT)
            deadline = time.time() + 15
            while time.time() < deadline and self.proc.poll() is None:
                self.log.seek(0)
                if 'Press Ctrl-C' in self.log.read():
                    break
                time.sleep(0.05)
            else:
                self.proc.wait(timeout=5) if self.proc.poll() is None else None
                continue
            break
        self.log.seek(0)
        output = self.log.read()
        self.assertIsNone(self.proc.poll(), f'serve.py did not start:\n{output}')
        self.studio = f'http://localhost:{self.studio_port}'
        self.target = f'http://localhost:{self.target_port}/demo/'
        self.app = f'{self.studio}/{HTML.name}'

    def stop_server(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()  # serve.py handles SIGTERM and prints "Stopped."
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.log.close()

    def close_browsers(self):
        try:
            close_contexts(self.contexts)
        finally:
            for browser in self.browsers:
                browser.close()

    def written(self):
        return self.overrides.read_text(encoding='utf-8') if self.overrides.exists() else ''

    def served_overrides(self):
        with urllib.request.urlopen(f'http://localhost:{self.target_port}/{self.rel}', timeout=5) as response:
            return response.status, response.headers, response.read().decode('utf-8')

    # ---- browser -------------------------------------------------------
    def open(self, engine, viewport=None, query=True):
        context = new_context(engine, viewport=viewport or {'width': 1440, 'height': 900})
        self.contexts.append(context)
        if engine == 'chromium':  # the real clipboard works on localhost once permitted
            context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=self.studio)
        self.font_requests = []

        def fonts(route):
            self.font_requests.append(route.request.url)
            route.fulfill(status=200, content_type='text/css', body='/* offline */')

        context.route('https://fonts.googleapis.com/**', fonts)
        context.route('https://**/*', lambda route: route.abort() if 'fonts.googleapis.com' not in route.request.url
                      else fonts(route))
        context.route(f'http://localhost:{self.target_port}/demo/fontkit-overrides.css',
                      lambda route: route.continue_(url=f'http://localhost:{self.target_port}/{self.rel}'))
        if getattr(self, 'runtime_context_hook', None):
            self.runtime_context_hook(context)
        page = context.new_page()
        page.errors = []
        page.on('pageerror', lambda error: page.errors.append(str(error)))
        page.goto(f'{self.app}?target={quote(self.target, safe=":/")}' if query else self.app)
        return page

    def wait_badge(self, page, pattern, timeout=10000):
        page.wait_for_function('(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
                               arg=pattern, timeout=timeout)

    def connected(self, engine, **options):
        """Open Studio with ?target= and wait until it reports Connected and the demo has loaded."""
        page = self.open(engine, **options)
        self.wait_badge(page, CONNECTED)
        self.frame(page).wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        return page

    def frame(self, page):
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        self.assertTrue(frame.url.startswith(self.target), frame.url)
        return frame

    def inspector_target(self, page, target, timeout=3000):
        """Wait until the inspector shows `target`: an id, or a regex matched against the shown name."""
        # Pass only the key that applies and test for it with typeof: wait_for_function turns a None
        # value into a missing key (`undefined`), so a `name: None` placeholder cannot be told from a regex.
        page.wait_for_function(
            '(want) => { const el = document.querySelector("#liveTargetName"); if (!el) return false;'
            ' return typeof want.name === "string" ? new RegExp(want.name).test(el.textContent)'
            ' : el.dataset.targetId === want.id; }',
            arg={'name': target.strip('/')} if target.startswith('/') else {'id': target},
            timeout=timeout)

    def click_in_target(self, page, selector, target):
        """Click inside the iframe; Studio selects it. One retry covers the load-time re-hello,
        which starts a fresh session and clears the selection."""
        locator = page.frame_locator('#targetAppFrame').locator(selector)
        for attempt in (1, 2):
            locator.click()
            try:
                self.inspector_target(page, target)
                return
            except PlaywrightTimeout:
                if attempt == 2:
                    raise

    def select_hero_title(self, page):
        self.click_in_target(page, TITLE, 'landing.hero.title')

    def type_into(self, page, selector, text, delay=60):
        page.locator(selector).click()
        page.keyboard.press('Control+A')
        page.keyboard.type(text, delay=delay)

    def style(self, frame, selector, prop):
        return frame.evaluate('([s, p]) => getComputedStyle(document.querySelector(s))[p]', [selector, prop])

    def wait_style(self, frame, selector, prop, expected, timeout=8000):
        frame.wait_for_function(
            '([s, p, v]) => { const el = document.querySelector(s); return Boolean(el) && getComputedStyle(el)[p] === v; }',
            arg=[selector, prop, expected], timeout=timeout)

    def wait_text(self, frame, selector, expected, timeout=8000):
        frame.wait_for_function(
            '([s, v]) => { const el = document.querySelector(s); return Boolean(el) && el.textContent.trim() === v; }',
            arg=[selector, expected], timeout=timeout)

    def tab(self, page, name):
        page.locator(f'#codeTab{name}').click()
        return page.locator('#liveCodeOutput').text_content()

    def wait_code(self, page, name, needle, timeout=8000):
        page.locator(f'#codeTab{name}').click()
        page.wait_for_function('(s) => document.querySelector("#liveCodeOutput").textContent.includes(s)',
                               arg=needle, timeout=timeout)
        return page.locator('#liveCodeOutput').text_content()

    def wait_file(self, needle, timeout=8000):
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            if needle in self.written():
                return self.written()
            time.sleep(0.05)
        self.fail(f'{needle!r} never appeared in the overrides file:\n{self.written()}')

    def sync(self, page):
        sync = page.locator('#liveCodeSync')
        page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
        sync.click()
        page.wait_for_function('() => /^Saved \\d+ bytes to /.test(document.querySelector("#liveCodeStatus").textContent)')
        return page.locator('#liveCodeStatus').text_content()

    def export(self, page):
        page.locator('#exportJson').click()
        data = json.loads(page.locator('#exportDialogText').input_value())
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return data

    def import_document(self, page, data):
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json', 'buffer': json.dumps(data).encode()})
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        return page.locator('#composerStatus').inner_text()

    def rehello(self, page, frame):
        """The bridge announces itself again (a reconnect without a reload). Returns once Studio has handled the
        new handshake: the target posts a marker after it has answered the hello, and messages from one window
        arrive in order."""
        page.evaluate("""() => { window.__rehello = 0;
            window.addEventListener('message', (event) => { if (event.data && event.data.type === 'test:rehello') window.__rehello += 1; }); }""")
        frame.evaluate("""() => window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'design:hello') window.parent.postMessage({ type: 'test:rehello' }, '*'); })""")
        frame.evaluate('window.parent.postMessage({type: "design:bridge-ready", protocolVersion: 1}, "*")')
        page.wait_for_function('() => window.__rehello >= 1')

    def reload_target(self, page):
        self.frame(page).evaluate('location.reload()')
        page.locator('#liveReconnectBanner').wait_for(state='visible')
        frame = self.frame(page)
        frame.wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        return frame


class InspectorWaitTests(unittest.TestCase):
    """`inspector_target` must really wait. Playwright's wait_for_function drops dict keys whose value
    is None (the predicate sees `undefined`, not `null`), so a predicate that told "no regex" apart with
    `!== null` matched every name and the wait returned at once for any plain id."""

    inspector_target = LiveIntegrationCase.inspector_target  # the helper under test; it uses only `page`

    def setUp(self):
        shared_runtime()
        context = new_context('chromium')
        self.addCleanup(context.close)
        self.page = context.new_page()
        self.page.set_content('<span id="liveTargetName" data-target-id="landing.hero.lead">Hero lead</span>')

    def test_a_plain_id_that_is_not_shown_times_out(self):
        with self.assertRaises(PlaywrightTimeout):
            self.inspector_target(self.page, 'landing.hero.title', timeout=500)

    def test_a_regex_that_does_not_match_the_shown_name_times_out(self):
        with self.assertRaises(PlaywrightTimeout):
            self.inspector_target(self.page, '/^Hero title$/', timeout=500)

    def test_the_shown_id_returns(self):
        self.inspector_target(self.page, 'landing.hero.lead', timeout=500)

    def test_a_regex_that_matches_the_shown_name_returns(self):
        self.inspector_target(self.page, '/^Hero lead$/', timeout=500)

    def test_the_wait_holds_until_the_inspector_renders_the_target(self):
        self.page.evaluate("""() => setTimeout(() => {
            const el = document.getElementById('liveTargetName');
            el.dataset.targetId = 'landing.hero.title'; el.textContent = 'Hero title'; }, 300)""")
        self.inspector_target(self.page, 'landing.hero.title', timeout=3000)
        self.assertEqual(self.page.evaluate('document.getElementById("liveTargetName").dataset.targetId'),
                         'landing.hero.title')


class EditAndCodePanelTests(LiveIntegrationCase):
    def test_target_query_connects_and_clicking_the_page_edits_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                count = int(page.locator('#bridgeStatusBadge').text_content().split('(')[1].split()[0])
                self.assertGreaterEqual(count, 12, 'the demo has 12 author targets plus auto-discovered ones')
                self.assertEqual(page.locator('#targetAppUrl').input_value(), self.target)
                self.assertTrue(page.locator('#viewTargetApp').evaluate('el => el.classList.contains("active")'))
                frame = self.frame(page)
                original_text = frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).textContent.trim()')
                self.assertEqual(frame.evaluate('document.querySelectorAll("[data-fontkit-font]").length'), 0)

                self.select_hero_title(page)
                self.assertEqual(page.locator('#liveTargetName').text_content(), 'Hero title')
                # The Studio draws the selection; nothing is injected into the app's DOM.
                page.locator('#bridgeOverlaySelected').wait_for(state='visible')
                self.assertEqual(frame.evaluate('document.querySelectorAll("#fontkit-bridge-overlay, #fontkit-bridge-hover").length'), 0)

                # Keystroke-level typing: every intermediate value ("5", then "56") is a real update.
                self.type_into(page, '#liveFontSize', '56')
                self.wait_style(frame, TITLE, 'fontSize', '56px')
                self.type_into(page, '#liveColorHex', '#0a7d3b')
                page.keyboard.press('Tab')
                self.wait_style(frame, TITLE, 'color', 'rgb(10, 125, 59)')
                self.type_into(page, '#liveText', 'Plan the work, skip the meetings.', delay=15)
                self.wait_text(frame, TITLE, 'Plan the work, skip the meetings.')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertEqual(self.style(frame, TITLE, 'fontSize'), '56px')
                self.assertNotEqual(original_text, 'Plan the work, skip the meetings.')
                self.assertEqual(page.errors, [])

                # CSS tab: one rule for the stable selector, declarations as the target applied them.
                css = self.wait_code(page, 'Css', 'color: #0a7d3b !important;')
                self.assertIn('/* Hero title (landing.hero.title) */\n[data-design-id="landing.hero.title"] {', css)
                self.assertIn('font-size: 56px !important;', css)
                self.assertNotIn('add data-design-id', css, 'a stable author selector needs no warning')
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')
                # HTML tab: the changed element, cleaned of bridge attributes.
                html = self.wait_code(page, 'Html', 'Plan the work, skip the meetings.')
                self.assertIn('data-design-id="landing.hero.title"', html)
                self.assertNotIn('style=', html)
                self.assertNotIn(original_text, html)
                # JSON tab: acknowledged overrides keyed by target id.
                data = json.loads(self.wait_code(page, 'Json', '"text"'))
                self.assertEqual(data['target'], self.target)
                self.assertIsInstance(data['revision'], int)
                self.assertGreaterEqual(data['revision'], 3)
                self.assertEqual(data['overrides'], {'landing.hero.title': {
                    'fontSize': 56, 'color': '#0a7d3b', 'text': 'Plan the work, skip the meetings.'}})
                self.assertEqual(page.errors, [])

    def test_copy_uses_the_real_clipboard(self):
        for engine in ENGINES:
            if engine != 'chromium':
                continue  # clipboard permissions are a Chromium-only Playwright feature
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '48')
                self.wait_style(self.frame(page), TITLE, 'fontSize', '48px')
                for tab, needle in (('Css', 'font-size: 48px !important;'), ('Json', '"fontSize": 48'), ('Html', 'No text changes yet.')):
                    shown = self.wait_code(page, tab, needle)
                    page.locator('#liveCodeCopy').click()
                    page.wait_for_function('() => /^Copied /.test(document.querySelector("#liveCodeStatus").textContent)')
                    self.assertEqual(page.evaluate('navigator.clipboard.readText()'), shown, tab)
                    page.evaluate('navigator.clipboard.writeText("")')
                    page.evaluate('document.querySelector("#liveCodeStatus").textContent = ""')
                self.assertEqual(page.errors, [])


class SyncAndReloadTests(LiveIntegrationCase):
    def test_sync_writes_the_file_and_a_reload_keeps_the_style_and_asks_before_reapplying(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                original = frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).textContent.trim()')
                self.assertEqual(self.written(), '', 'nothing is written before the user syncs')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '56')
                self.wait_style(frame, TITLE, 'fontSize', '56px')
                self.type_into(page, '#liveText', 'Fewer meetings.', delay=15)
                self.wait_text(frame, TITLE, 'Fewer meetings.')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertEqual(self.written(), '', 'editing alone never writes the file')

                # Sync to file: the dev server writes the CSS Studio shows.
                self.assertIn('Saved', self.sync(page))
                shown = self.tab(page, 'Css')
                written = self.written()
                self.assertEqual(written.strip(), shown.strip())
                self.assertIn('[data-design-id="landing.hero.title"] {', written)
                self.assertIn('font-size: 56px !important;', written)
                self.assertNotIn('Fewer meetings', written, 'text changes go in the HTML tab, not the stylesheet')
                status, headers, body = self.served_overrides()
                self.assertEqual((status, headers['Cache-Control'], body), (200, 'no-store', written))
                self.assertTrue(headers['Content-Type'].startswith('text/css'))

                # Auto-sync follows later edits without another click.
                page.locator('#liveCodeAutoSync').check()
                self.type_into(page, '#liveFontSize', '52')
                self.wait_style(frame, TITLE, 'fontSize', '52px')
                self.wait_file('font-size: 52px !important;')
                self.assertNotIn('font-size: 56px', self.written())
                page.locator('#liveCodeAutoSync').uncheck()

                # Reload the iframe: the stylesheet still styles the page with no bridge override.
                frame = self.reload_target(page)
                self.wait_style(frame, TITLE, 'fontSize', '52px')
                self.assertIsNone(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).getAttribute("style")'),
                                  'the size comes from the stylesheet, not an inline override')
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).textContent.trim()'), original)
                # Nothing is applied behind the user's back: the banner waits for a choice.
                banner = page.locator('#liveReconnectBanner')
                self.assertTrue(banner.is_visible())
                self.assertIn('Reapply', banner.text_content())
                self.assertIn('Accept', banner.text_content())
                self.assertIsNone(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).getAttribute("style")'))
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).textContent.trim()'), original)

                # Reapply: Studio's saved state goes back into the page (inline override plus the text).
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.wait_text(frame, TITLE, 'Fewer meetings.')
                frame.wait_for_function(f'document.querySelector({json.dumps(TITLE)}).style.fontSize === "52px"')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertIn('font-size: 52px !important;', self.tab(page, 'Css'))

                # Accept: the page's own state becomes the saved state, and the file is left alone.
                before = self.written()
                frame = self.reload_target(page)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(json.loads(self.tab(page, 'Json'))['overrides'], {})
                self.assertIn('unchanged until you press Sync to file', page.locator('#liveCodeStatus').text_content())
                self.wait_text(frame, TITLE, original)
                self.assertEqual(self.written(), before)
                self.assertEqual(page.errors, [])


    def test_the_banner_after_sync_and_reload_explains_zero_live_edits_and_what_accept_does(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '56')
                self.wait_style(self.frame(page), TITLE, 'fontSize', '56px')
                self.sync(page)
                synced = self.written()
                self.assertIn('font-size: 56px !important;', synced)
                frame = self.reload_target(page)
                self.wait_style(frame, TITLE, 'fontSize', '56px')
                self.assertIsNone(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).getAttribute("style")'),
                                  'the page looks right because the file styles it, not because of a live edit')
                banner = page.locator('#liveReconnectBanner')
                text = ' '.join(banner.text_content().split())
                self.assertIn('the Live App has 0 targets changed', text)
                # Why the page looks right although the bridge counts nothing.
                self.assertRegex(text, r'overrides file already styles the page')
                self.assertRegex(text, r'0 live edits')
                self.assertRegex(text, r'counts only edits (made )?through Studio')
                # What Accept does, in plain words.
                self.assertRegex(text, r"Accept Live App state replaces Studio's saved overrides, composition tokens and DOM order")
                self.assertRegex(text, r'next Sync writes a smaller file')
                # The words are true: accepting and syncing really does shrink the file.
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(self.written(), synced, 'accepting alone writes nothing')
                self.sync(page)
                self.assertNotIn('font-size: 56px', self.written())
                self.assertLess(len(self.written()), len(synced))
                self.assertEqual(page.errors, [])


class DemotedTargetTests(LiveIntegrationCase):
    LEAD = '[data-design-id="landing.hero.lead"]'

    def test_removing_an_author_id_keeps_the_edit_and_brings_back_the_unstable_hint(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.click_in_target(page, self.LEAD, 'landing.hero.lead')
                self.type_into(page, '#liveFontSize', '30')
                self.wait_style(frame, self.LEAD, 'fontSize', '30px')
                self.wait_badge(page, r'^Live · rev \d+$')
                css = self.wait_code(page, 'Css', 'font-size: 30px !important;')
                self.assertIn('[data-design-id="landing.hero.lead"] {', css)
                self.assertNotIn('add data-design-id', css)
                self.assertNotIn('auto-discovered', page.locator('.live-target-id').text_content())

                # The app (or its author) drops the attribute from the edited element.
                frame.evaluate(f'document.querySelector({json.dumps(self.LEAD)}).removeAttribute("data-design-id")')
                page.wait_for_function('() => /auto:/.test(document.querySelector("#liveTargetName").dataset.targetId)', timeout=8000)
                css = self.wait_code(page, 'Css', 'add data-design-id for a stable selector')
                self.assertNotIn('data-design-id="landing.hero.lead"', css)
                self.assertIn('font-size: 30px !important;', css)
                self.assertIn('auto-discovered', page.locator('.live-target-id').text_content())
                overrides = json.loads(self.tab(page, 'Json'))['overrides']
                self.assertEqual(len(overrides), 1)
                (new_id, patch), = overrides.items()
                self.assertTrue(new_id.startswith('auto:'), new_id)
                self.assertEqual(patch, {'fontSize': 30})
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'saved and live state agree')
                # The page still shows the edit, and Reset on the followed target restores the original.
                paragraph = frame.evaluate('[...document.querySelectorAll("p")].find(p => p.style.fontSize === "30px") !== undefined')
                self.assertTrue(paragraph)
                page.locator('#liveResetTarget').click()
                page.wait_for_function('() => document.querySelector("#liveChangeCount").textContent === "0"')
                self.assertEqual(frame.evaluate('[...document.querySelectorAll("p")].filter(p => p.style.fontSize === "30px").length'), 0)
                self.assertEqual(page.errors, [])


class SelectionOrderTests(LiveIntegrationCase):
    """The real bridge's replies are kept in an ordered pipe (a test-only hook appended to the served script), so the
    order in which Studio sees the acknowledgement of a reset and the user's next click is under the test's control."""
    PIPE = """
;(function () {
  const proto = window.FontKitBridge.prototype, send = proto.post, pipe = [];
  window.__hold = false;
  proto.post = function (message) { if (window.__hold) pipe.push([this, message]); else send.call(this, message); };
  window.__pending = () => pipe.length;
  window.__types = () => pipe.map((item) => item[1].type);
  window.__release = () => { const next = pipe.shift(); if (next) send.call(next[0], next[1]); return pipe.length; };
})();
"""
    # Test-only: the bridge can be told to keep the design:select messages it receives and handle them later, so a pick
    # Studio sent for the user can be handled after a newer click in the page (a busy page does exactly that).
    STASH = """
;(function () {
  const proto = window.FontKitBridge.prototype, handle = proto.handleSelect, stash = [];
  window.__defer = false;
  proto.handleSelect = function (id, requestId) { if (window.__defer) stash.push([this, id, requestId]); else handle.call(this, id, requestId); };
  window.__stashed = () => stash.length;
  window.__runStashed = () => { stash.splice(0).forEach(([bridge, id, requestId]) => handle.call(bridge, id, requestId)); };
})();
"""
    LEAD = '[data-design-id="landing.hero.lead"]'

    def open(self, engine, viewport=None, query=True):
        bridge = (REPO / 'fontkit-bridge.js').read_text(encoding='utf-8') + self.PIPE + self.STASH
        self.runtime_context_hook = lambda context: context.route(
            f'http://localhost:{self.target_port}/fontkit-bridge.js',
            lambda route: route.fulfill(status=200, content_type='application/javascript', body=bridge))
        return super().open(engine, viewport=viewport, query=query)

    def release_all(self, page, frame):
        """Deliver every held reply, one at a time, and wait until Studio has handled each one.

        After a release the target posts a marker message to Studio. Messages from one window arrive in order, so
        when Studio has seen the marker it has finished reacting to the reply (including anything that reaction
        queued in the pipe), and the next release is safe without a guessed pause."""
        page.evaluate("""() => { window.__flushed = 0;
            window.addEventListener('message', (event) => { if (event.data && event.data.type === 'test:flush') window.__flushed += 1; }); }""")
        for released in range(1, 41):
            if not frame.evaluate('window.__pending()'):
                page.wait_for_timeout(60)   # absence check: nothing new was queued by what was just delivered
                if not frame.evaluate('window.__pending()'):
                    return
            frame.evaluate('window.__release()')
            frame.evaluate('window.parent.postMessage({type: "test:flush"}, "*")')
            page.wait_for_function('(count) => window.__flushed >= count', arg=released)
        self.fail('Studio kept queueing replies: the pipe never drained')

    def test_a_click_right_after_a_reset_keeps_the_clicked_target_selected_and_edited(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.select_hero_title(page)
                lead_before = self.style(frame, self.LEAD, 'fontSize')
                title_before = self.style(frame, TITLE, 'fontSize')
                self.type_into(page, '#liveFontSize', '40')               # Reset is disabled until the element has a change
                page.wait_for_function('() => !document.querySelector("#liveResetTarget").disabled')
                frame.evaluate('window.__hold = true')
                page.locator('#liveResetTarget').click()                  # the target acknowledges the reset first ...
                page.frame_locator('#targetAppFrame').locator(self.LEAD).click()   # ... the user clicks the lead right after
                frame.wait_for_function('window.__pending() >= 2')
                while 'design:applied' in frame.evaluate('window.__types()'):   # Studio sees the acknowledgement first ...
                    frame.evaluate('window.__release()')
                self.wait_badge(page, r'^Live · rev \d+$')                       # ... and only then the click
                self.release_all(page, frame)
                frame.evaluate('window.__hold = false')
                page.wait_for_function('() => document.querySelector("#liveTargetName").dataset.targetId === "landing.hero.lead"')
                # Studio's refresh reply came after the click; it keeps the click and realigns the page with it.
                frame.wait_for_function('window.__fontkitBridge.selectedId === "landing.hero.lead"')
                # The next typed value lands on the lead, not on the title that was selected before.
                self.type_into(page, '#liveFontSize', '31')
                self.wait_style(frame, self.LEAD, 'fontSize', '31px')
                self.assertEqual(self.style(frame, TITLE, 'fontSize'), title_before)
                self.assertNotEqual(lead_before, '31px')
                self.assertEqual(page.locator('#liveTargetName').text_content(), 'Hero lead')
                self.assertEqual(page.errors, [])

    # ---- picks Studio sends for the user, handled by the bridge later than a newer click in the page ----------
    def trace(self, page):
        """Record what Studio receives from the target (every design:* message, with its requestId and target) and
        every load of the target frame, so a failure below can show the order that produced it. Call it right after
        connected()."""
        page.evaluate("""() => {
            const started = performance.now(), log = window.__trace = [];
            const note = (entry) => log.push(Object.assign({ at: Math.round(performance.now() - started) }, entry));
            window.addEventListener('message', (event) => {
                const data = event.data;
                if (data && typeof data.type === 'string' && data.type.startsWith('design:')) {
                    note({ message: data.type, requestId: data.requestId, targetId: data.targetId });
                }
            });
            document.querySelector('#targetAppFrame').addEventListener('load', () => note({ load: 'targetAppFrame' }));
        }""")

    def trace_text(self, page):
        try:
            lines = page.evaluate('() => (window.__trace || []).map((entry) => JSON.stringify(entry))')
        except Exception as error:   # the page may be gone; the assertion below still matters more
            return f'(no trace: {error})'
        return 'Studio received, in order:\n' + '\n'.join(lines)

    def assert_selected_everywhere(self, page, frame, target_id):
        """The inspector and the bridge's own selection both end on `target_id` (the realign needs a round trip)."""
        try:
            frame.wait_for_function('(id) => window.__fontkitBridge.selectedId === id', arg=target_id, timeout=3000)
        except PlaywrightTimeout:
            pass   # the assertions below name what was selected instead
        try:
            self.assertEqual(frame.evaluate('window.__fontkitBridge.selectedId'), target_id, 'the bridge')
            self.inspector_target(page, target_id)
            self.assertEqual(page.locator('#liveTargetName').get_attribute('data-target-id'), target_id, 'the inspector')
        except (AssertionError, PlaywrightTimeout) as error:
            raise AssertionError(f'{error}\n{self.trace_text(page)}') from None

    def test_a_page_click_wins_over_a_list_pick_the_bridge_handles_late(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                lead_before = self.style(frame, self.LEAD, 'fontSize')
                frame.evaluate('window.__defer = true')
                page.locator('[data-live-target="landing.hero.lead"]').click()     # the user picks the lead in Studio (older)
                frame.wait_for_function('window.__stashed() === 1')
                self.select_hero_title(page)                                         # then clicks the title in the page (newer)
                frame.evaluate('window.__defer = false; window.__runStashed()')     # the bridge now handles the older pick
                self.assert_selected_everywhere(page, frame, 'landing.hero.title')
                # The next typed value lands on the title the user clicked, not on the lead picked earlier.
                self.type_into(page, '#liveFontSize', '31')
                self.wait_style(frame, TITLE, 'fontSize', '31px')
                self.assertEqual(self.style(frame, self.LEAD, 'fontSize'), lead_before)
                self.assertEqual(page.locator('#liveTargetName').text_content(), 'Hero title')
                self.assertEqual(page.errors, [])

    def test_a_page_click_wins_over_a_list_pick_the_bridge_answers_after_a_re_handshake(self):
        """The list pick is still waiting at the bridge when the target's load re-sends hello and Studio sees the new
        design:ready (which forgets every request asked before it). The user then clicks the title in the page. The
        bridge finally answers the old pick: that answer is still the old request's, not a new choice."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                lead_before = self.style(frame, self.LEAD, 'fontSize')
                frame.evaluate('window.__defer = true')
                page.locator('[data-live-target="landing.hero.lead"]').click()     # the user picks the lead in Studio (older)
                frame.wait_for_function('window.__stashed() === 1')
                page.evaluate('document.querySelector("#targetAppFrame").dispatchEvent(new Event("load"))')   # the re-hello
                self.wait_badge(page, CONNECTED)                                     # ... answered by a new design:ready
                self.select_hero_title(page)                                         # then the click on the title (newer)
                frame.evaluate('window.__defer = false; window.__runStashed()')     # the bridge now answers the older pick
                self.assert_selected_everywhere(page, frame, 'landing.hero.title')
                self.type_into(page, '#liveFontSize', '31')
                self.wait_style(frame, TITLE, 'fontSize', '31px')
                self.assertEqual(self.style(frame, self.LEAD, 'fontSize'), lead_before)
                self.assertEqual(page.locator('#liveTargetName').text_content(), 'Hero title')
                self.assertEqual(page.errors, [])

    CTA = '[data-design-id="landing.hero.cta"]'

    def test_a_sibling_pick_the_bridge_answers_after_a_re_handshake_keeps_the_pick(self):
        """The user picks a sibling in the Arrange list; the bridge has not handled it when the target's load re-sends
        hello. The new design:ready must not reset what the user last picked to the target it kept selected."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                siblings = page.locator('#liveSiblingList [data-sibling-id]').evaluate_all('els => els.map(el => el.dataset.siblingId)')
                other = next(item for item in siblings if item != 'landing.hero.cta')
                frame.evaluate('window.__defer = true')
                page.locator(f'#liveSiblingList [data-sibling-id="{other}"]').focus()
                page.keyboard.press('Enter')                                          # the user picks the sibling (newest)
                frame.wait_for_function('window.__stashed() === 1')
                page.evaluate('document.querySelector("#targetAppFrame").dispatchEvent(new Event("load"))')   # the re-hello
                self.wait_badge(page, CONNECTED)
                frame.evaluate('window.__defer = false; window.__runStashed()')
                self.assert_selected_everywhere(page, frame, other)
                self.assertEqual(page.errors, [])

    def test_a_page_click_wins_when_two_re_handshakes_forget_a_refresh_the_bridge_answers_late(self):
        """The CI-shaped order: the first ready re-sends the kept selection (the lead) as a tracked refresh, the second
        ready forgets that request, and the bridge answers it after the user clicked the title."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                page.locator('[data-live-target="landing.hero.lead"]').click()
                self.inspector_target(page, 'landing.hero.lead')
                frame.evaluate('window.__defer = true')
                page.evaluate('document.querySelector("#targetAppFrame").dispatchEvent(new Event("load"))')
                self.wait_badge(page, CONNECTED)
                frame.wait_for_function('window.__stashed() === 2')                  # the kept selection, re-sent as a refresh (twice: also for its bulk manifest)
                page.evaluate('document.querySelector("#targetAppFrame").dispatchEvent(new Event("load"))')
                self.wait_badge(page, CONNECTED)
                frame.wait_for_function('window.__stashed() === 4')                  # the second ready forgot the first refreshes
                self.select_hero_title(page)
                frame.evaluate('window.__defer = false; window.__runStashed()')
                self.assert_selected_everywhere(page, frame, 'landing.hero.title')
                self.assertEqual(page.errors, [])

    def test_the_inspector_checks_wait_for_a_bridge_that_reports_a_selection_late(self):
        """The bridge's design:selected reaches Studio 150 ms late. The helpers must wait for the inspector to
        show the click instead of reading it before Studio has rendered the report."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                frame.evaluate("""() => {
                    const proto = window.FontKitBridge.prototype, send = proto.post;
                    proto.post = function (message) {
                        if (message && message.type === 'design:selected') setTimeout(() => send.call(this, message), 150);
                        else send.call(this, message);
                    };
                }""")
                page.locator('[data-live-target="landing.hero.lead"]').click()
                self.inspector_target(page, 'landing.hero.lead')
                self.select_hero_title(page)
                self.assert_selected_everywhere(page, frame, 'landing.hero.title')
                self.assertEqual(page.errors, [])

    def test_a_page_click_after_the_bridge_handled_the_list_pick_still_wins(self):
        """Characterization: the bridge handled the pick first, so nothing is stale."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                title_before = self.style(frame, TITLE, 'fontSize')
                page.locator('[data-live-target="landing.hero.lead"]').click()
                self.inspector_target(page, 'landing.hero.lead')
                self.select_hero_title(page)
                self.assert_selected_everywhere(page, frame, 'landing.hero.title')
                self.type_into(page, '#liveFontSize', '29')
                self.wait_style(frame, TITLE, 'fontSize', '29px')
                self.assertNotEqual(title_before, '29px')
                self.assertEqual(page.errors, [])

    def test_a_page_click_wins_over_all_targets_the_bridge_handles_late(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.trace(page)
                frame = self.frame(page)
                title_before = self.style(frame, TITLE, 'fontSize')
                self.select_hero_title(page)
                frame.evaluate('window.__defer = true')
                page.locator('[data-live-back]').click()                             # "All targets" (older) ...
                frame.wait_for_function('window.__stashed() === 1')
                page.frame_locator('#targetAppFrame').locator(self.LEAD).click()   # ... then a click on the lead in the page
                self.inspector_target(page, 'landing.hero.lead')
                frame.evaluate('window.__defer = false; window.__runStashed()')
                self.assert_selected_everywhere(page, frame, 'landing.hero.lead')
                self.type_into(page, '#liveFontSize', '33')
                self.wait_style(frame, self.LEAD, 'fontSize', '33px')
                self.assertEqual(self.style(frame, TITLE, 'fontSize'), title_before)
                self.assertEqual(page.errors, [])


class CompositionSyncTests(LiveIntegrationCase):
    BADGE = '[data-design-id="landing.stat.badge"]'

    def sync_composition(self, page):
        page.locator('#btnSyncToApp').click()
        self.wait_badge(page, r'^Live · rev \d+$')

    def test_synced_tracking_arrives_in_em_not_a_thousand_times_smaller(self):
        """The Composer's tracking is in em (0.32 means 0.32em); the page must get exactly that."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                saved = page.evaluate(
                    '() => { document.querySelector("#exportJson").click();'
                    ' const doc = JSON.parse(document.querySelector("#exportDialogText").value);'
                    ' document.querySelector("#exportDialog").close(); return doc.composition.slots.map(s => [s.role, s.size, s.tracking]); }')
                tracking = {role: (size, em) for role, size, em in saved if em is not None}
                self.assertEqual(tracking['H1'], (58, -0.025), saved)
                self.assertEqual(tracking['Metadata'], (11, 0.08), saved)
                self.sync_composition(page)
                title = float(self.style(frame, TITLE, 'letterSpacing').removesuffix('px'))
                badge = float(self.style(frame, self.BADGE, 'letterSpacing').removesuffix('px'))
                self.assertAlmostEqual(title, -0.025 * 58, delta=0.01)   # -1.45px
                self.assertAlmostEqual(badge, 0.08 * 11, delta=0.01)     # 0.88px
                # The page's change record agrees: the declaration is the em value the Composer showed.
                declared = frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).style.letterSpacing')
                self.assertEqual(declared, '-0.025em')
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(self.BADGE)}).style.letterSpacing'), '0.08em')
                self.assertEqual(page.errors, [])

    SHEETS = [f'https://fonts.googleapis.com/css2?family={family}&display=swap' for family in (
        'Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900', 'Instrument+Serif:ital@0;1',
        'Inter:wght@100..900', 'IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700')]

    def test_sync_loads_the_stylesheets_of_the_library_fonts_it_sends_once_free_fonts_were_asked_for(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                self.assertEqual(self.font_requests, [], 'opening Studio and the target contacts no font host')
                page.locator('#loadFreeFonts').click()    # the user asks for free fonts
                self.font_requests.clear()               # (Studio's own specimens load them now)
                self.sync_composition(page)
                links = frame.evaluate('[...document.querySelectorAll("link[data-fontkit-font]")].map(el => el.href)')
                self.assertEqual(links, self.SHEETS)
                frame.wait_for_function('[...document.querySelectorAll("link[data-fontkit-font]")].every(el => el.sheet !== null)')
                for url in self.SHEETS:
                    self.assertIn(url, self.font_requests)
                # The code panel offers the same imports for the file, and the file gets them on Sync.
                css = self.wait_code(page, 'Css', '@import')
                self.assertTrue(css.startswith(f'@import url("{self.SHEETS[0]}");'), css[:200])
                self.sync(page)
                written = self.written()
                for url in self.SHEETS:
                    self.assertIn(f'@import url("{url}");', written)
                self.assertEqual(page.errors, [])

    def test_sync_without_the_ask_loads_no_stylesheet_in_the_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.sync_composition(page)
                self.assertEqual(frame.evaluate('document.querySelectorAll("link[data-fontkit-font]").length'), 0)
                self.assertEqual(self.font_requests, [])
                self.assertIn('Load free fonts', page.locator('#composerStatus').text_content())
                self.assertEqual(page.errors, [])

    def record_target_font_requests(self, page):
        """Font-host requests made by the target page itself (not by Studio's own specimens), as they happen.
        The context route in open() records every font request but cannot say which frame asked."""
        requests = []
        page.on('request', lambda request: requests.append(request.url)
                if request.url.startswith('https://fonts.googleapis.com/') and request.frame.url.startswith(self.target) else None)
        return requests

    def test_loading_free_fonts_after_a_sync_sends_the_linked_composition_with_its_stylesheets_to_the_page(self):
        """The Composer promises the fonts load once the user presses Load free fonts: the real bridge must get them."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                target_requests = self.record_target_font_requests(page)
                self.sync_composition(page)                   # no consent yet
                self.assertEqual(frame.evaluate('document.querySelectorAll("link[data-fontkit-font]").length'), 0)
                self.assertEqual(self.font_requests, [], 'the sync alone contacts no font host, from Studio or the page')
                self.assertEqual(target_requests, [])
                page.locator('#loadFreeFonts').click()
                frame.wait_for_function('document.querySelectorAll("link[data-fontkit-font]").length > 0')
                links = frame.evaluate('[...document.querySelectorAll("link[data-fontkit-font]")].map(el => el.href)')
                self.assertEqual(links, self.SHEETS, 'the consent re-sent the linked composition with its sheets')
                frame.wait_for_function('[...document.querySelectorAll("link[data-fontkit-font]")].every(el => el.sheet !== null)')
                for url in self.SHEETS:
                    self.assertIn(url, target_requests, 'the page itself fetched the sheet')
                self.assertEqual(page.errors, [])

    def test_loading_free_fonts_without_a_sync_loads_no_stylesheet_in_the_page_until_the_user_syncs(self):
        """Consent alone never pushes Studio's composition into the app (Rule 6): only a sync does."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                target_requests = self.record_target_font_requests(page)
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => document.getElementById("freeFontStatus").textContent.length > 0')
                page.wait_for_timeout(400)               # absence window: a stray send would arrive well within it
                self.assertEqual(frame.evaluate('document.querySelectorAll("link[data-fontkit-font]").length'), 0)
                self.assertEqual(target_requests, [])
                self.assertNotEqual(self.font_requests, [], "Studio's own specimens did load (the consent took effect)")
                # The same page, bridge and consent still deliver the sheets once the user syncs.
                self.sync_composition(page)
                frame.wait_for_function('document.querySelectorAll("link[data-fontkit-font]").length > 0')
                links = frame.evaluate('[...document.querySelectorAll("link[data-fontkit-font]")].map(el => el.href)')
                self.assertEqual(links, self.SHEETS)
                self.assertEqual(page.errors, [])

    def test_imported_tracking_values_are_normalised_before_they_reach_the_page(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                page.locator('#exportJson').click()
                doc = json.loads(page.locator('#exportDialogText').input_value())
                page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
                for slot in doc['composition']['slots']:
                    if slot['role'] == 'H1':
                        slot['tracking'] = 0.035
                    if slot['role'] == 'Metadata':
                        slot['tracking'] = -0.2 + 0.1 + 0.1   # 1.3877787807814457e-17, not zero, as a slider might leave it
                page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
                page.locator('#importJsonFile').set_input_files({
                    'name': 'composition.json', 'mimeType': 'application/json', 'buffer': json.dumps(doc).encode()})
                page.wait_for_function('() => /imported/i.test(document.querySelector("#composerStatus").textContent)')
                self.sync_composition(page)
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(TITLE)}).style.letterSpacing'), '0.035em')
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(self.BADGE)}).style.letterSpacing'), '0em')
                self.assertAlmostEqual(float(self.style(frame, TITLE, 'letterSpacing').removesuffix('px')), 0.035 * 58, delta=0.01)
                self.assertEqual(page.errors, [])


class FreeFontsAskTests(LiveIntegrationCase):
    """Nothing reaches a font host until the user asks (Load free fonts, or a library pick in the inspector):
    not through imported overrides, not through imported tokens, not through Reapply (Rule 7, D028, D031, D032)."""
    FRAUNCES = 'https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900&display=swap'
    LINKS = 'document.querySelectorAll("link[data-fontkit-font]")'

    def links(self, frame):
        return frame.evaluate(f'[...{self.LINKS}].map(el => el.href)')

    def test_imported_override_fonts_stay_off_the_network_until_the_user_asks(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                base = self.export(page)
                live = {'target': self.target, 'revision': 1,
                        'overrides': {'landing.hero.title': {'fontFamily': '"Fraunces", serif'}}}
                self.assertIn('Composition imported.', self.import_document(page, {**base, 'live': live}))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                # The saved rule names the family; no stylesheet for it is offered or written without the ask.
                css = self.wait_code(page, 'Css', 'font-family: "Fraunces", serif !important;')
                self.assertNotIn('googleapis', css)
                self.sync(page)
                self.assertIn('font-family: "Fraunces", serif !important;', self.written())
                self.assertNotIn('googleapis', self.written())
                frame = self.reload_target(page)
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'getComputedStyle(document.querySelector({json.dumps(TITLE)})).fontFamily.includes("Fraunces")')
                self.assertEqual(self.links(frame), [], 'Reapply adds no stylesheet link before the ask')
                self.assertEqual(self.font_requests, [], 'no request to a font host before the ask')
                self.assertNotIn('googleapis', self.tab(page, 'Css'))

                # The ask: the stylesheet shows up in the file, and a reload plus Reapply loads it in the page.
                page.locator('#loadFreeFonts').click()
                self.font_requests.clear()            # (Studio's own specimens load now)
                self.wait_code(page, 'Css', f'@import url("{self.FRAUNCES}");')
                self.sync(page)
                self.assertTrue(self.written().startswith(f'@import url("{self.FRAUNCES}");'), self.written()[:200])
                frame = self.reload_target(page)
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'[...{self.LINKS}].some(el => el.href === {json.dumps(self.FRAUNCES)})')
                self.assertEqual(self.links(frame), [self.FRAUNCES])
                self.assertIn(self.FRAUNCES, self.font_requests)
                self.assertEqual(page.errors, [])

    def test_reapply_without_the_ask_sends_saved_token_fonts_to_no_font_host(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                base = self.export(page)
                token = 'document.documentElement.style.getPropertyValue("--font-display")'
                live = {'target': self.target, 'revision': 1, 'overrides': {},
                        'tokens': {'--font-display': '"Instrument Serif", serif'}}
                self.assertIn('Composition imported.', self.import_document(page, {**base, 'live': live}))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'{token} === \'"Instrument Serif", serif\'')
                self.assertEqual(self.links(frame), [])
                self.assertEqual(self.font_requests, [])
                self.assertEqual(page.errors, [])

    def test_reapply_keeps_the_stylesheet_only_a_composition_slot_needs(self):
        """With the ask, Composer Sync loads a sheet for every library font its slots use. A later Reapply that
        carries a token update must not release the sheet that only a slot refers to."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()
                page.locator('#btnSyncToApp').click()
                self.wait_badge(page, r'^Live · rev \d+$')
                synced = sorted(self.links(frame))
                self.assertEqual(len(synced), 4, synced)
                self.rehello(page, frame)       # the composition is no longer linked; the page keeps its sheets
                base = self.export(page)
                tokens = base['live']['tokens']
                inter = next(url for url in synced if 'family=Inter' in url)
                self.assertFalse(any('Inter' in value for value in tokens.values()), 'only a slot uses Inter')
                live = {**base['live'], 'tokens': {**tokens, '--brand-ink': '#123456'}}
                self.assertIn('Composition imported.', self.import_document(page, {**base, 'live': live}))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('document.documentElement.style.getPropertyValue("--brand-ink") === "#123456"')
                self.assertEqual(sorted(self.links(frame)), synced, 'the slot-only sheet is still loaded after Reapply')
                self.assertIn(inter, self.links(frame))
                self.assertEqual(page.errors, [])


class StructureReplayTests(LiveIntegrationCase):
    """DOM-order moves saved in Studio, replayed by an explicit Reapply, against the real bridge."""
    ACTIONS = '.actions'
    CTA = '[data-design-id="landing.hero.cta"]'
    SAVED = ['See how it works', 'Start your free trial']
    ORIGINAL = ['Start your free trial', 'See how it works']

    def order(self, frame, container=None):
        return frame.evaluate(f'[...document.querySelector("{container or self.ACTIONS}").children].map(el => el.textContent.trim())')

    def wait_order(self, frame, expected):
        frame.wait_for_function(
            '(want) => [...document.querySelector(".actions").children].map(el => el.textContent.trim()).join("|") === want.join("|")',
            arg=expected)

    def dom_move_the_cta(self, page, frame):
        self.click_in_target(page, self.CTA, 'landing.hero.cta')
        page.locator('#liveMoveNext').click()
        self.wait_order(frame, self.SAVED)

    HERO_TEXT = '[data-design-id="landing.hero.title"]'

    def hero_children(self, frame):
        return frame.evaluate(f'[...document.querySelector({json.dumps(self.HERO_TEXT)}).parentElement.children]'
                              '.map(el => el.getAttribute("data-design-id") || el.className)')

    def test_a_container_the_page_reorders_by_itself_is_not_saved_by_a_reset_of_one_child(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                before = self.hero_children(frame)
                # What a composition sync does to the page: the bridge reorders a container the user never touched.
                frame.evaluate("""() => {
                    const container = document.querySelector('[data-design-id="landing.hero.title"]').parentElement;
                    container.setAttribute('data-design-order-container', 'true');
                    window.__fontkitBridge.applyWireframeMovement([
                        { id: 'a', targetId: 'landing.hero.lead', index: 0 }, { id: 'b', targetId: 'landing.hero.title', index: 1 }]);
                }""")
                self.assertNotEqual(self.hero_children(frame), before, 'the page reordered the container itself')
                title_size = self.style(frame, TITLE, 'fontSize')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '50')
                self.wait_style(frame, TITLE, 'fontSize', '50px')
                page.locator('#liveResetTarget').click()
                self.wait_style(frame, TITLE, 'fontSize', title_size)
                page.locator('#codeTabJson').click()
                page.wait_for_function('() => !document.querySelector("#liveCodeOutput").textContent.includes("fontSize")')
                self.assertNotIn('structure', self.export(page).get('live', {}),
                                 'Studio saves a container only because the user moved something in it')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(page.errors, [])

    def test_a_reset_of_an_unrelated_target_keeps_a_saved_dom_order_the_app_changed_in_session(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.dom_move_the_cta(page, frame)
                saved = self.export(page)['live']['structure']
                self.assertEqual(len(saved), 1)
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                # The app puts its action row back in its own order (a re-render): no handshake, no message to Studio.
                frame.evaluate('() => { const row = document.querySelector(".actions"); row.appendChild(row.firstElementChild); }')
                self.wait_order(frame, self.ORIGINAL)
                title_size = self.style(frame, TITLE, 'fontSize')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '50')
                self.wait_style(frame, TITLE, 'fontSize', '50px')
                page.locator('#liveResetTarget').click()
                self.wait_style(frame, TITLE, 'fontSize', title_size)
                page.locator('#codeTabJson').click()
                page.wait_for_function('() => !document.querySelector("#liveCodeOutput").textContent.includes("fontSize")')
                banner = page.locator('#liveReconnectBanner')
                self.assertEqual(self.export(page).get('live', {}).get('structure'), saved,
                                 'an unrelated reset neither drops nor replaces what Studio saved')
                banner.wait_for(state='visible', timeout=3000)
                self.assertIn('the Live App holds 0 of them', ' '.join(banner.inner_text().split()))
                self.assertEqual(self.order(frame), self.ORIGINAL, 'Studio did not touch the page')
                # The mismatch is the user's to resolve: Reapply puts the saved order back.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.wait_order(frame, self.SAVED)
                self.assertEqual(self.export(page)['live']['structure'], saved)
                self.assertEqual(page.errors, [])

    def test_reapply_puts_a_saved_dom_move_back_on_the_first_press_even_with_a_stale_css_order_in_the_page(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.dom_move_the_cta(page, frame)
                # Then a CSS-order move of the same element: the page now holds both kinds of change.
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMovePrev').click()
                frame.wait_for_function(f'getComputedStyle(document.querySelector({json.dumps(self.CTA)})).order !== "0"'
                                        f' || [...document.querySelectorAll("{self.ACTIONS} > *")].some(el => getComputedStyle(el).order !== "0")')
                saved = self.export(page)
                self.assertEqual(len(saved['live']['structure']), 1, 'the DOM move is saved')
                self.assertTrue(any('order' in patch for patch in saved['live']['overrides'].values()), 'the CSS order is saved')
                # The saved state is replaced by one that no longer holds the CSS order but keeps the DOM move.
                live = {**saved['live'], 'overrides': {'landing.hero.title': {'fontSize': 44}}}
                self.assertIn('Composition imported.', self.import_document(page, {**saved, 'live': live}))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                try:
                    banner.wait_for(state='hidden')
                except PlaywrightTimeout:
                    self.fail(f'the first Reapply did not settle; the page holds {self.order(frame)}; '
                              f'status: {page.locator("#liveCodeStatus").text_content()}')
                self.wait_style(frame, TITLE, 'fontSize', '44px')
                self.assertEqual(self.order(frame), self.SAVED, 'the first press leaves the saved DOM order in the page')
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(self.CTA)}).style.order'), '',
                                 'the stale CSS order is gone')
                self.assertEqual(self.export(page)['live']['structure'], saved['live']['structure'])
                self.assertEqual(page.errors, [])

    # The decoy's links carry author ids on purpose: auto ids are numbered in page order, so plain links would take
    # the numbers the saved ones had and the saved ids would then name the decoy's children.
    DECOY = ('<div class="actions"><a class="btn btn-ghost" href="#one" data-design-id="decoy.one">Decoy one</a>'
             '<a class="btn btn-ghost" href="#two" data-design-id="decoy.two">Decoy two</a></div>\n          ')

    def open(self, engine, viewport=None, query=True):
        """The demo page can change between loads: once `app_changed` is set, a second `.actions` container
        comes first in the hero, so the selector Studio saved now names it."""
        self.app_changed = False

        def serve_the_app(route):
            response = route.fetch()
            body = response.text()
            if self.app_changed:
                body = body.replace('<div class="actions">', self.DECOY + '<div class="actions">', 1)
            route.fulfill(response=response, body=body,
                          headers={**response.headers, 'content-length': str(len(body.encode('utf-8')))})

        self.runtime_context_hook = lambda context: context.route(
            re.compile(rf'^http://localhost:{self.target_port}/demo/(index\.html)?$'), serve_the_app)
        return super().open(engine, viewport=viewport, query=query)

    def all_containers(self, frame):
        return frame.evaluate('[...document.querySelectorAll(".actions")].map(el => [...el.children].map(c => c.textContent.trim()))')

    def test_a_saved_container_the_app_no_longer_owns_is_not_filled_with_the_saved_children(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.dom_move_the_cta(page, frame)
                saved = self.export(page)['live']['structure']
                self.assertEqual(len(saved), 1)
                self.sync(page)
                self.app_changed = True
                frame = self.reload_target(page)
                self.assertTrue(frame.evaluate('document.querySelector(arguments[0]) === document.querySelector(".actions")'
                                               .replace('arguments[0]', json.dumps(saved[0]['selector']))),
                                'the test app really makes the saved selector land on the first container, the decoy')
                before = self.all_containers(frame)
                self.assertEqual(before, [['Decoy one', 'Decoy two'], self.ORIGINAL])
                page.locator('#liveReapply').click()
                page.wait_for_timeout(500)   # absence check: nothing may be moved into the decoy, or out of the real container
                self.assertEqual(self.all_containers(frame), before)
                self.assertEqual(self.export(page)['live']['structure'], saved, 'Studio keeps what it saved')
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible(), 'nothing was replayed, so the choice is still open')
                self.assertEqual(page.errors, [])


class InteractModeTests(LiveIntegrationCase):
    def test_the_instrumented_app_works_normally_without_studio(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                browser = launch(self.runtime, engine)
                self.browsers.append(browser)
                page = browser.new_page()
                page.goto(self.target)
                page.locator('.site-nav a[href="#pricing"]').click()
                page.wait_for_function('location.hash === "#pricing"')
                self.assertEqual(page.evaluate('document.querySelectorAll("#fontkit-bridge-overlay, #fontkit-bridge-hover").length'), 0)

    def test_select_mode_selects_links_and_interact_mode_follows_them(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                link = '.site-nav a[href="#pricing"]'
                self.assertEqual(page.locator('#bridgeModeSelect').get_attribute('aria-pressed'), 'true')
                # Select mode: the click selects the link and does not navigate.
                page.frame_locator('#targetAppFrame').locator(link).click()
                page.wait_for_function('() => document.querySelector("#liveTargetName") && /Pricing/.test(document.querySelector("#liveTargetName").textContent)')
                self.assertEqual(frame.evaluate('location.hash'), '')
                # Interact mode: the same click works like in the real app.
                page.locator('#bridgeModeInteract').click()
                self.assertEqual(page.locator('#bridgeModeInteract').get_attribute('aria-pressed'), 'true')
                page.frame_locator('#targetAppFrame').locator(link).click()
                frame.wait_for_function('location.hash === "#pricing"')
                frame.wait_for_function('window.scrollY > 0 || document.scrollingElement.scrollTop > 0')
                # Back to Select: links are selectable again.
                page.locator('#bridgeModeSelect').click()
                page.frame_locator('#targetAppFrame').locator('.site-nav a[href="#faq"]').click()
                page.wait_for_function('() => /FAQ/.test(document.querySelector("#liveTargetName").textContent)')
                self.assertEqual(frame.evaluate('location.hash'), '#pricing')
                self.assertEqual(page.errors, [])


class RestoreAndResetTests(LiveIntegrationCase):
    def test_restore_page_text_keeps_styles_and_reset_returns_the_page_byte_for_byte(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                lead = '[data-design-id="landing.hero.lead"]'
                before = frame.evaluate('document.body.outerHTML')
                original = frame.evaluate(f'document.querySelector({json.dumps(lead)}).textContent')
                self.click_in_target(page, lead, 'landing.hero.lead')
                self.type_into(page, '#liveFontSize', '30')
                self.wait_style(frame, lead, 'fontSize', '30px')
                self.type_into(page, '#liveText', 'Short copy.', delay=15)
                self.wait_text(frame, lead, 'Short copy.')
                self.wait_badge(page, r'^Live · rev \d+$')

                # Restore Page Text: copy returns, typography stays.
                page.locator('#btnRestoreOriginalText').click()
                frame.wait_for_function(f'document.querySelector({json.dumps(lead)}).textContent !== "Short copy."')
                self.assertEqual(frame.evaluate(f'document.querySelector({json.dumps(lead)}).textContent'), original)
                self.assertEqual(self.style(frame, lead, 'fontSize'), '30px')
                self.assertIn('font-size: 30px !important;', self.tab(page, 'Css'))
                self.assertNotIn('Short copy.', self.tab(page, 'Html'))

                # Reset this element: back to the original page, down to the bytes.
                page.locator('#liveResetTarget').click()
                frame.wait_for_function(f'document.querySelector({json.dumps(lead)}).style.fontSize === ""')
                self.assertNotEqual(self.style(frame, lead, 'fontSize'), '30px')
                self.assertEqual(json.loads(self.tab(page, 'Json'))['overrides'], {})
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '0')
                self.assertEqual(frame.evaluate('document.body.outerHTML'), before)
                self.assertEqual(page.errors, [])


class ArrangeTests(LiveIntegrationCase):
    ACTIONS = '.actions'
    CTA = '[data-design-id="landing.hero.cta"]'

    def order(self, frame):
        return frame.evaluate(f'[...document.querySelector("{self.ACTIONS}").children].map(el => el.textContent.trim())')

    def test_move_the_cta_next_shows_structure_in_the_html_tab_and_reset_undoes_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                before = frame.evaluate('document.body.outerHTML')
                self.assertEqual(self.order(frame), ['Start your free trial', 'See how it works'])
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                self.assertIn('1 of 2', page.locator('#liveArrangeInfo').text_content())
                page.locator('#liveMoveNext').click()
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").lastElementChild.matches({json.dumps(self.CTA)})')
                self.assertEqual(self.order(frame), ['See how it works', 'Start your free trial'])
                html = self.wait_code(page, 'Html', 'Structure:')
                self.assertIn('class="actions"', html)
                self.assertLess(html.index('See how it works'), html.index('Start your free trial'))
                # The ghost link was auto-registered as a sibling; the bridge's own attributes never reach the snippet.
                self.assertIn('<a class="btn btn-ghost" href="#features">See how it works</a>', html)
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')
                self.assertIn('HTML tab', self.wait_code(page, 'Css', 'HTML tab'))
                # The sibling list follows the new order.
                items = page.locator('#liveSiblingList [data-sibling-id]').evaluate_all('els => els.map(el => el.dataset.siblingId)')
                self.assertEqual(items[-1], 'landing.hero.cta')

                page.locator('#liveResetTarget').click()
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").firstElementChild.matches({json.dumps(self.CTA)})')
                self.assertEqual(self.order(frame), ['Start your free trial', 'See how it works'])
                self.assertIn('No text changes yet.', self.tab(page, 'Html'))
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '0')
                self.assertEqual(frame.evaluate('document.body.outerHTML'), before)
                self.assertEqual(page.errors, [])

    def test_a_dom_move_survives_sync_and_reload_through_an_explicit_reapply(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                original_page = frame.evaluate('document.body.outerHTML')
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                page.locator('#liveMoveNext').click()
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").lastElementChild.matches({json.dumps(self.CTA)})')
                moved = ['See how it works', 'Start your free trial']
                self.assertEqual(self.order(frame), moved)
                # The status line says where the move lives at the moment it is made.
                page.wait_for_function('() => /kept in Studio/.test(document.querySelector("#liveCodeStatus").textContent)')
                status = page.locator('#liveCodeStatus').text_content()
                self.assertRegex(status, r'not in the CSS file')
                self.assertRegex(status, r'CSS order')
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')

                # Sync writes no new kind of content for it.
                self.sync(page)
                self.assertNotIn('order:', self.written())
                saved = self.export(page)['live']['structure']
                self.assertEqual(len(saved), 1)
                self.assertEqual(saved[0]['ids'][-1], 'landing.hero.cta')
                self.assertEqual(len(saved[0]['ids']), 2)

                # A reload puts the markup back; Studio asks and applies nothing by itself.
                frame = self.reload_target(page)
                self.assertEqual(self.order(frame), ['Start your free trial', 'See how it works'])
                banner = page.locator('#liveReconnectBanner')
                self.assertIn('DOM order', banner.text_content())
                page.wait_for_timeout(300)
                self.assertEqual(self.order(frame), ['Start your free trial', 'See how it works'])
                self.assertEqual(self.export(page)['live']['structure'], saved)

                # Reapply replays the saved move, and the HTML tab shows the structure block again.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").lastElementChild.matches({json.dumps(self.CTA)})')
                self.assertEqual(self.order(frame), moved)
                html = self.wait_code(page, 'Html', 'Structure:')
                self.assertLess(html.index('See how it works'), html.index('Start your free trial'))
                self.assertEqual(self.export(page)['live']['structure'], saved)

                # Reset undoes the move and drops it from the saved state.
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                page.locator('#liveResetTarget').click()
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").firstElementChild.matches({json.dumps(self.CTA)})')
                self.assertNotIn('live', self.export(page))
                self.assertEqual(frame.evaluate('document.body.outerHTML'), original_page)
                self.assertEqual(page.errors, [])

    def test_a_dom_move_adds_no_css_rule_to_the_synced_file(self):
        """The file holds CSS only: after a DOM move its rules are exactly what they were (comments may differ)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '50')
                self.wait_style(frame, TITLE, 'fontSize', '50px')
                self.sync(page)
                before = self.written()
                self.assertIn('font-size: 50px !important;', before)
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                page.locator('#liveMoveNext').click()
                frame.wait_for_function(f'document.querySelector("{self.ACTIONS}").lastElementChild.matches({json.dumps(self.CTA)})')
                self.sync(page)
                rules = lambda css: re.sub(r'/\*.*?\*/', '', css, flags=re.S).split()
                self.assertEqual(rules(self.written()), rules(before))
                self.assertEqual(page.errors, [])

    def test_css_order_strategy_changes_the_look_but_not_the_dom(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.click_in_target(page, self.CTA, 'landing.hero.cta')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveNext').click()
                frame.wait_for_function(f'getComputedStyle(document.querySelector({json.dumps(self.CTA)})).order === "1"')
                self.assertEqual(self.order(frame), ['Start your free trial', 'See how it works'], 'the DOM is untouched')
                visual = frame.evaluate(f'[...document.querySelector("{self.ACTIONS}").children]'
                                        '.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)'
                                        '.map(el => el.textContent.trim())')
                self.assertEqual(visual, ['See how it works', 'Start your free trial'])
                css = self.wait_code(page, 'Css', 'order: 1 !important;')
                self.assertIn('[data-design-id="landing.hero.cta"] {', css)
                self.assertIn('No text changes yet.', self.tab(page, 'Html'))
                page.locator('#liveResetTarget').click()
                frame.wait_for_function(f'getComputedStyle(document.querySelector({json.dumps(self.CTA)})).order === "0"')
                self.assertEqual(page.errors, [])

    def test_a_form_control_cannot_be_moved_out_of_its_form(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                before = frame.evaluate('document.body.outerHTML')
                self.click_in_target(page, '.signup button[type="submit"]', '/Subscribe/')
                options = page.locator('#liveMoveContainer option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                solo = next((value for value, name in options if name == 'Solo'), None)
                self.assertIsNotNone(solo, options)
                page.locator('#liveMoveContainer').select_option(solo)
                page.locator('#liveMoveInto').click()
                guard = page.locator('#liveMoveGuard')
                guard.wait_for(state='visible')
                self.assertIn('form', guard.text_content().lower())
                self.assertEqual(page.locator('#liveMoveForce').count(), 0, 'form guards cannot be overridden')
                self.assertEqual(frame.evaluate('Boolean(document.querySelector("form.signup button[type=submit]"))'), True)
                self.assertEqual(frame.evaluate('document.body.outerHTML'), before, 'a rejected move changes nothing')
                self.assertEqual(page.errors, [])


class FontTests(LiveIntegrationCase):
    FRAUNCES = 'https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900&display=swap'

    def test_a_free_library_font_loads_its_stylesheet_in_the_target_and_the_synced_css(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.select_hero_title(page)
                options = page.locator('#liveFontFamily option').evaluate_all('els => els.map(el => el.textContent)')
                self.assertIn('Fraunces', options)
                self.assertNotIn('Gotham', options)
                self.assertEqual(page.locator('#composerKitIds').input_value(), '', 'no Adobe kit is prefilled')
                page.locator('#liveFontFamily').select_option(label='Fraunces')
                frame.wait_for_function(f'getComputedStyle(document.querySelector({json.dumps(TITLE)})).fontFamily.includes("Fraunces")')
                link = frame.evaluate('[...document.querySelectorAll("link[data-fontkit-font]")].map(el => el.href)')
                self.assertEqual(link, [self.FRAUNCES])
                self.assertIn(self.FRAUNCES, self.font_requests)
                css = self.wait_code(page, 'Css', '@import')
                self.assertTrue(css.startswith(f'@import url("{self.FRAUNCES}");\n'), css)
                self.assertIn('font-family: "Fraunces", serif !important;', css)
                self.sync(page)
                self.assertTrue(self.written().startswith(f'@import url("{self.FRAUNCES}");'))
                self.assertIn('font-family: "Fraunces", serif !important;', self.written())
                # Choosing the page's own family again releases the stylesheet.
                page.locator('#liveFontFamily').select_option(index=0)
                frame.wait_for_function('document.querySelectorAll("link[data-fontkit-font]").length === 0')
                page.wait_for_function('() => !document.querySelector("#liveCodeOutput").textContent.includes("@import")')
                self.assertEqual(page.errors, [])


class PopOutTests(LiveIntegrationCase):
    def test_pop_out_edits_the_real_window_and_dock_returns_to_the_iframe(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                page.evaluate("""() => { window.__opens = []; const original = window.open.bind(window);
                    window.open = (...args) => { window.__opens.push(args); return original(...args); }; }""")
                with page.expect_popup() as info:
                    page.locator('#bridgePopOut').click()
                popup = info.value
                # A features string is what makes browsers open a separate window instead of a tab.
                opens = page.evaluate('window.__opens')
                self.assertEqual(len(opens), 1)
                self.assertEqual(opens[0][:2], [self.target, 'fontkit-target'])
                features = dict(part.split('=') for part in opens[0][2].split(','))
                self.assertEqual(features['popup'], 'yes')
                popup.wait_for_function('Boolean(window.__fontkitBridge)')
                # The new window really has the requested size, not Studio's own.
                self.assertEqual(popup.evaluate('[innerWidth, innerHeight]'),
                                 [int(features['width']), int(features['height'])])
                self.assertEqual(popup.url, self.target)
                self.assertEqual(popup.evaluate('window.name'), 'fontkit-target')
                placeholder = page.locator('#bridgePopoutPlaceholder')
                placeholder.wait_for(state='visible')
                self.assertFalse(page.locator('#targetAppFrame').is_visible())
                self.wait_badge(page, CONNECTED)
                # The pop-out has no Studio overlay layer, so the bridge draws its own outline there.
                popup.wait_for_function('Boolean(document.querySelector("#fontkit-bridge-overlay"))', timeout=10000)

                popup.locator(TITLE).click()
                self.inspector_target(page, 'landing.hero.title')
                self.type_into(page, '#liveFontSize', '44')
                self.wait_style(popup, TITLE, 'fontSize', '44px')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertIn('font-size: 44px !important;', self.tab(page, 'Css'))
                self.assertEqual(popup.evaluate('document.querySelectorAll("#fontkit-bridge-overlay").length'), 1)

                # Dock: the popup closes, the iframe returns and the saved edit waits for a choice.
                with popup.expect_event('close'):  # registered before the click, so it cannot be missed
                    page.locator('#bridgeDock').click()
                placeholder.wait_for(state='hidden')
                page.locator('#targetAppFrame').wait_for(state='visible')
                self.wait_badge(page, CONNECTED)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.assertIn('Reapply', page.locator('#liveReconnectBanner').text_content())
                frame = self.frame(page)
                frame.wait_for_function('document.readyState === "complete"')
                self.assertNotEqual(self.style(frame, TITLE, 'fontSize'), '44px')
                self.assertEqual(frame.evaluate('document.querySelectorAll("#fontkit-bridge-overlay").length'), 0)
                page.locator('#liveReapply').click()
                self.wait_style(frame, TITLE, 'fontSize', '44px')
                self.assertEqual(page.errors, [])


class AutoDiscoveredSelectorTests(LiveIntegrationCase):
    def test_a_target_without_an_id_keeps_its_edit_in_the_css_panel_and_the_synced_file(self):
        """The bridge's path selectors contain the child combinator; the edit must not be skipped."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                solo = '#pricing .plan:first-child h3'
                self.click_in_target(page, solo, '/Solo/')
                self.assertEqual(page.locator('#liveTargetName').get_attribute('data-target-id') is not None, True)
                self.assertIn('add data-design-id', page.locator('.live-target-id').text_content())
                self.type_into(page, '#liveFontSize', '37')
                self.wait_style(frame, solo, 'fontSize', '37px')
                self.wait_badge(page, r'^Live · rev \d+$')
                css = self.wait_code(page, 'Css', 'font-size: 37px !important;')
                self.assertNotIn('skipped', css)
                match = re.search(r'auto-discovered — add data-design-id for a stable selector \*/\n(.+) \{\n  font-size: 37px !important;', css)
                self.assertIsNotNone(match, css)
                selector = match.group(1)
                self.assertIn(' > ', selector, 'the demo gives this heading a path selector')
                # The persisted rule really addresses that heading, and only it.
                self.assertEqual(frame.evaluate('(s) => [...document.querySelectorAll(s)].map(el => el.textContent.trim())', selector),
                                 ['Solo'])
                self.assertIn('Saved', self.sync(page))
                self.assertIn(f'{selector} {{\n  font-size: 37px !important;', self.written())
                self.assertEqual(self.written().strip(), self.tab(page, 'Css').strip())
                self.assertEqual(page.errors, [])

    def test_class_names_with_escaped_selector_characters_keep_the_edit(self):
        """Tailwind arbitrary variants such as `[&>*]:p-4` are escaped by the bridge with `\\>`, `\\[` and `\\&`."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                solo = '#pricing .plan:first-child h3'
                frame.evaluate("""(s) => {
                    document.querySelector(s).classList.add('[&>*]:p-4', 'a;b{c}');
                    document.body.append(document.createElement('i'));  // a DOM change: the bridge recomputes its selectors
                }""", solo)
                self.click_in_target(page, solo, '/Solo/')
                self.type_into(page, '#liveFontSize', '38')
                self.wait_style(frame, solo, 'fontSize', '38px')
                self.wait_badge(page, r'^Live · rev \d+$')
                css = self.wait_code(page, 'Css', 'font-size: 38px !important;')
                self.assertNotIn('skipped', css)
                match = re.search(r'add data-design-id for a stable selector \*/\n(.+) \{\n  font-size: 38px !important;', css)
                self.assertIsNotNone(match, css)
                selector = match.group(1)
                self.assertIn('\\[\\&\\>\\*\\]\\:p-4', selector, 'the escaped class is in the persisted selector')
                self.assertEqual(frame.evaluate('(s) => [...document.querySelectorAll(s)].map(el => el.textContent.trim())', selector),
                                 ['Solo'])
                self.assertIn('Saved', self.sync(page))
                self.assertIn(f'{selector} {{\n  font-size: 38px !important;', self.written())
                self.assertEqual(page.errors, [])

    def test_promoting_the_target_to_an_author_id_keeps_the_edit_and_raises_no_conflict(self):
        """The app follows Studio's hint and adds a data-design-id to the heading that was edited as an auto target."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.unlink(missing_ok=True)
                page = self.connected(engine)
                frame = self.frame(page)
                solo = '#pricing .plan:first-child h3'
                new_id = 'pricing.solo.title'
                original_size = self.style(frame, solo, 'fontSize')
                self.assertIsNone(frame.evaluate('(s) => document.querySelector(s).getAttribute("style")', solo))
                self.click_in_target(page, solo, '/Solo/')
                self.type_into(page, '#liveFontSize', '37')
                self.wait_style(frame, solo, 'fontSize', '37px')
                self.wait_badge(page, r'^Live · rev \d+$')
                css = self.wait_code(page, 'Css', 'add data-design-id for a stable selector')
                old_id = re.search(r'/\* [^(]*\((auto:[^)]+)\)', css).group(1)
                self.assertEqual(list(json.loads(self.tab(page, 'Json'))['overrides']), [old_id])

                # The attribute is set in place: no node is added or removed.
                frame.evaluate('([s, id]) => document.querySelector(s).setAttribute("data-design-id", id)', [solo, new_id])
                css = self.wait_code(page, 'Css', f'[data-design-id="{new_id}"] {{')
                self.assertIn('font-size: 37px !important;', css)
                self.assertNotIn(old_id, css)
                self.assertNotIn('add data-design-id', css.split(new_id)[1].split('}')[0])
                self.assertEqual(json.loads(self.tab(page, 'Json'))['overrides'], {new_id: {'fontSize': 37}})
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')
                self.wait_style(frame, solo, 'fontSize', '37px')

                # A reconnect (the bridge announces itself again) finds Studio and the page in agreement.
                page.evaluate("""() => { window.__readySeen = 0; window.addEventListener('message', (event) => {
                    if (event.data && event.data.type === 'design:ready') setTimeout(() => { window.__readySeen += 1; }, 0); }); }""")
                frame.evaluate('window.parent.postMessage({type: "design:bridge-ready", protocolVersion: 1}, "*")')
                page.wait_for_function('() => window.__readySeen === 1')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'no false conflict')
                self.assertEqual(json.loads(self.tab(page, 'Json'))['overrides'], {new_id: {'fontSize': 37}})
                self.assertEqual(self.written(), '', 'nothing was written behind the user\'s back')

                # The edit is still live: Reset restores the heading exactly, and the synced file has the stable rule.
                self.click_in_target(page, solo, new_id)
                self.type_into(page, '#liveFontSize', '39')
                self.wait_style(frame, solo, 'fontSize', '39px')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertIn('Saved', self.sync(page))
                self.assertIn(f'[data-design-id="{new_id}"] {{\n  font-size: 39px !important;', self.written())
                self.assertNotIn('auto:', self.written())
                page.locator('#liveResetTarget').click()
                self.wait_style(frame, solo, 'fontSize', original_size)
                self.assertIsNone(frame.evaluate('(s) => document.querySelector(s).getAttribute("style")', solo))
                self.assertEqual(page.errors, [])


class DuplicateBridgeTests(LiveIntegrationCase):
    def test_a_second_new_fontkitbridge_after_connect_changes_nothing_for_the_studio(self):
        """An HMR re-run of `new FontKitBridge()`: one bridge answers, and Reset still restores the original."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                original_size = self.style(frame, TITLE, 'fontSize')
                original_style = frame.evaluate('(s) => document.querySelector(s).getAttribute("style")', TITLE)
                original_html = frame.evaluate('document.body.innerHTML')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '56')
                self.wait_style(frame, TITLE, 'fontSize', '56px')
                self.wait_badge(page, r'^Live · rev \d+$')
                page.evaluate("""() => { window.__seen = { ready: 0, applied: 0 };
                    window.addEventListener('message', (event) => { const type = event.data && event.data.type;
                        const key = type === 'design:ready' ? 'ready' : type === 'design:applied' ? 'applied' : null;
                        if (key) setTimeout(() => { window.__seen[key] += 1; }, 0); }); }""")
                warned = frame.evaluate("""() => { const seen = []; const warn = console.warn;
                    console.warn = (...args) => seen.push(args.join(' '));
                    const first = window.__fontkitBridge; const again = new FontKitBridge({ enableHighlightOverlay: true });
                    console.warn = warn; return [again === first, seen.length]; }""")
                self.assertEqual(warned, [True, 1])
                # Nothing new announces itself, so Studio does not re-handshake with a second bridge.
                self.assertEqual(frame.evaluate('document.querySelectorAll("#fontkit-bridge-overlay").length'), 0)
                # Studio re-handshakes anyway when asked to (a reload of the page's script, say): one answer.
                frame.evaluate('window.parent.postMessage({type: "design:bridge-ready", protocolVersion: 1}, "*")')
                page.wait_for_function('() => window.__seen.ready >= 1')
                page.wait_for_timeout(300)
                self.assertEqual(page.evaluate('window.__seen.ready'), 1)
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                # An edit gets exactly one acknowledgement, and Reset restores what the author had.
                self.select_hero_title(page)
                page.locator('#liveFontSize').fill('52')   # one input event, so one request
                self.wait_style(frame, TITLE, 'fontSize', '52px')
                self.wait_badge(page, r'^Live · rev \d+$')
                self.assertEqual(page.evaluate('window.__seen.applied'), 1)
                page.locator('#liveResetTarget').click()
                self.wait_style(frame, TITLE, 'fontSize', original_size)
                self.assertEqual(frame.evaluate('(s) => document.querySelector(s).getAttribute("style")', TITLE), original_style)
                self.assertEqual(frame.evaluate('document.body.innerHTML'), original_html)
                self.assertEqual(page.errors, [])


class StableIdSelectorTests(LiveIntegrationCase):
    STABLE_IDS = [
        ('hero;alternate', '#pricing .plan:nth-child(1) h3'),
        ('a{b}<c>"d\\e', '#pricing .plan:nth-child(2) h3'),
        ('x"]{} body{color:red}/*', '#pricing .plan:nth-child(1) .price'),
    ]

    def test_stable_ids_with_css_special_characters_keep_their_rule_and_stay_safe(self):
        """The bridge writes such ids as CSS escapes, so the persisted rule is valid and holds no raw `; { } < >`."""
        for engine in ENGINES:
            for design_id, locator in self.STABLE_IDS:
                with self.subTest(engine=engine, id=design_id):
                    self.overrides.unlink(missing_ok=True)
                    page = self.connected(engine)
                    frame = self.frame(page)
                    page.evaluate("""() => { window.__targets = 0; window.addEventListener('message', (event) => {
                        if (event.data && event.data.type === 'design:targets') setTimeout(() => { window.__targets += 1; }, 0); }); }""")
                    frame.evaluate('([s, id]) => document.querySelector(s).setAttribute("data-design-id", id)', [locator, design_id])
                    # The bridge announces the promoted target and Studio has handled it before anything is clicked.
                    page.wait_for_function('() => window.__targets >= 1')
                    self.click_in_target(page, locator, design_id)
                    page.locator('#liveFontSize').fill('41')
                    self.wait_style(frame, locator, 'fontSize', '41px')
                    css = self.wait_code(page, 'Css', 'font-size: 41px !important;')
                    self.assertNotIn('skipped', css)
                    match = re.search(r'\n(\[data-design-id="(?:[^"\\\n]|\\.)*"\]) \{\n  font-size: 41px !important;', css)
                    self.assertIsNotNone(match, css)
                    selector = match.group(1)
                    for raw in ';{}<>':
                        self.assertNotIn(raw, selector)
                    # On the target page the persisted selector finds exactly the edited element.
                    self.assertEqual(frame.evaluate(
                        '([s, id]) => { const found = [...document.querySelectorAll(s)];'
                        ' return [found.length, found[0] && found[0].getAttribute("data-design-id") === id]; }',
                        [selector, design_id]), [1, True], selector)
                    # What a stylesheet parser sees: one rule block, and nothing a <style> element could end early.
                    code = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
                    self.assertEqual((code.count('{'), code.count('}')), (1, 1))
                    self.assertNotIn('body', re.sub(r'"(?:[^"\\]|\\.)*"', '""', code))
                    for raw in '<>':
                        self.assertNotIn(raw, css)
                    self.assertIn('Saved', self.sync(page))
                    self.assertEqual(self.written().strip(), css.strip())
                    self.assertEqual(page.errors, [])


class ImportedTokensTests(LiveIntegrationCase):
    def test_imported_tokens_use_the_bridge_rule_and_reapply_settles_with_no_lingering_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                base = self.export(page)
                live = {'target': self.target, 'revision': 1, 'overrides': {}}
                # Names the bridge would drop (upper case, underscore) are refused at import, not later.
                for bad in ('--Brand-Ink', '--brand_ink'):
                    status = self.import_document(page, {**base, 'live': {**live, 'tokens': {bad: '#123456'}}})
                    self.assertTrue(status.startswith('Import failed:'), (bad, status))
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                status = self.import_document(page, {**base, 'live': {**live, 'tokens': {'--brand-ink': '#123456'}}})
                self.assertIn('Composition imported.', status)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertEqual(frame.evaluate('document.documentElement.style.getPropertyValue("--brand-ink")'), '',
                                 'importing never applies anything by itself')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('document.documentElement.style.getPropertyValue("--brand-ink") === "#123456"')
                self.assertEqual(self.export(page)['live']['tokens'], {'--brand-ink': '#123456'})
                self.assertIn('--brand-ink: #123456 !important;', self.wait_code(page, 'Css', '--brand-ink'))
                self.assertEqual(page.errors, [])


    def test_import_reconnect_reapply_removes_a_token_the_saved_state_no_longer_has(self):
        """The target keeps a token Studio's saved state lost (a live state imported without tokens)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                base = self.export(page)
                live = {'target': self.target, 'revision': 1, 'overrides': {'landing.hero.title': {'fontSize': 44}}}
                banner = page.locator('#liveReconnectBanner')
                token = 'document.documentElement.style.getPropertyValue("--brand-ink")'
                # Save a token and put it on the real page through Reapply.
                self.assertIn('Composition imported.',
                              self.import_document(page, {**base, 'live': {**live, 'tokens': {'--brand-ink': '#123456'}}}))
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'{token} === "#123456"')
                self.wait_style(frame, TITLE, 'fontSize', '44px')
                # A live state without tokens replaces the saved set; the page still holds the token.
                self.assertIn('Composition imported.', self.import_document(page, {**base, 'live': live}))
                banner.wait_for(state='visible')
                self.assertEqual(frame.evaluate(token), '#123456', 'importing never changes the page')
                # The bridge announces itself again (a reconnect without a reload), then the user presses Reapply.
                frame.evaluate('window.parent.postMessage({type: "design:bridge-ready", protocolVersion: 1}, "*")')
                page.wait_for_function('() => /the Live App has \\d+ targets? changed and 1 composition token\\b/.test('
                                       'document.querySelector("#liveReconnectText").textContent)')
                self.assertEqual(frame.evaluate(token), '#123456', 'reconnecting never changes the page')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'{token} === ""')
                self.assertIsNone(frame.evaluate('document.documentElement.getAttribute("style")'),
                                  'the root has the inline style it had before Studio touched it')
                self.assertNotIn('tokens', self.export(page)['live'])
                self.assertNotIn('--brand-ink', self.tab(page, 'Css'))
                self.wait_style(frame, TITLE, 'fontSize', '44px')
                self.assertFalse(banner.is_visible())
                self.assertEqual(page.errors, [])


class RecursionGuardTests(LiveIntegrationCase):
    def test_studio_is_blocked_under_any_loopback_alias_or_path_case_but_other_ports_connect(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                port, name = self.studio_port, HTML.name
                for probe in (f'http://127.0.0.1:{port}/{name}', f'http://[::1]:{port}/{name}',
                              f'http://localhost:{port}/{name.upper()}', f'http://127.0.0.1:{port}/{name.upper()}?x=1#y',
                              f'{self.app}/', f'{self.app}?x=1'):
                    page.locator('#targetAppUrl').fill(probe)
                    page.locator('#btnConnectTarget').click()
                    self.wait_badge(page, r'^Recursion blocked$')
                    # The field keeps the refused address; connect to the demo again before the next probe.
                    page.locator('#targetAppUrl').fill(self.target)
                    page.locator('#btnConnectTarget').click()
                    self.wait_badge(page, CONNECTED)
                # The demo on the other port is an ordinary target, even through a loopback alias.
                page.locator('#targetAppUrl').fill(f'http://127.0.0.1:{self.target_port}/demo/?project=font-kit-studio')
                page.locator('#btnConnectTarget').click()
                self.wait_badge(page, CONNECTED)
                self.assertEqual(page.errors, [])


class BookmarkletTests(LiveIntegrationCase):
    """The README's own snippets, with its port (8000, the Studio dev server) swapped for this test's Studio port."""

    def readme_with_port(self, snippet):
        self.assertIn('localhost:8000', snippet)
        return snippet.replace('localhost:8000', f'localhost:{self.studio_port}')

    def test_the_readme_script_tag_loads_the_bridge_from_the_dev_server(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                tag = self.readme_with_port(readme_snippet(r'^(<script src="http://localhost:8000/fontkit-bridge\.js"></script>)$',
                                                           'plain HTML script tag'))
                page = self.open(engine, query=False)
                # A page that has only the README's tag, served by the real server from the scratch folder in the repo.
                (self.scratch / 'plain.html').write_text(
                    f'<!doctype html><html><body><h1 id="t">Plain page</h1><p>Hello.</p>{tag}</body></html>', encoding='utf-8')
                plain = f'http://localhost:{self.target_port}/{self.scratch.relative_to(REPO).as_posix()}/plain.html'
                page.goto(f'{self.app}?target={plain}')
                self.wait_badge(page, CONNECTED)
                frame = page.locator('#targetAppFrame').element_handle().content_frame()
                frame.wait_for_function('document.readyState === "complete"')
                page.frame_locator('#targetAppFrame').locator('#t').click()
                self.inspector_target(page, '/Plain page/')
                self.type_into(page, '#liveFontSize', '40')
                self.wait_style(frame, '#t', 'fontSize', '40px')
                self.assertEqual(page.errors, [])

    def test_injecting_the_bridge_into_a_pop_out_connects_a_page_without_the_script_tag(self):
        bookmarklet = readme_snippet(r'^javascript:(.+)$', 'bookmarklet line')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                code = self.readme_with_port(bookmarklet)
                page = self.open(engine, query=False)
                bridge = f'http://localhost:{self.target_port}/fontkit-bridge.js'
                withhold = lambda route: route.fulfill(status=404, body='')  # noqa: E731  the page "has no script tag"
                page.context.route(bridge, withhold)
                page.goto(f'{self.app}?target={quote(self.target, safe=":/")}')
                self.wait_badge(page, r'^No bridge answered at ')
                self.assertTrue(page.locator('#bridgeHint').is_visible())
                with page.expect_popup() as info:
                    page.locator('#bridgePopOut').click()
                popup = info.value
                popup.wait_for_load_state()
                self.assertEqual(popup.evaluate('typeof window.__fontkitBridge'), 'undefined')
                # Like a person: wait until Studio gives up on the page, then run the bookmarklet's code.
                self.wait_badge(page, r'^No bridge answered at ', timeout=15000)
                page.context.unroute(bridge, withhold)
                popup.evaluate(code)
                self.wait_badge(page, CONNECTED)
                popup.locator(TITLE).click()
                self.inspector_target(page, 'landing.hero.title')
                self.type_into(page, '#liveFontSize', '40')
                self.wait_style(popup, TITLE, 'fontSize', '40px')
                # Running it twice does nothing new.
                popup.evaluate(code)
                injected = f'http://localhost:{self.studio_port}/fontkit-bridge.js'
                self.assertEqual(popup.evaluate('(src) => [...document.scripts].filter((el) => el.src === src).length', injected), 1)
                self.assertEqual(page.errors, [])


class OpenedFromFileTests(LiveIntegrationCase):
    def test_studio_opened_as_a_file_edits_a_served_target_but_cannot_sync(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                browser = launch(self.runtime, engine)
                self.browsers.append(browser)
                page = browser.new_page(viewport={'width': 1440, 'height': 900})
                page.route('https://**/*', lambda route: route.abort())
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{HTML.as_uri()}?target={quote(self.target, safe=":/")}')
                self.wait_badge(page, CONNECTED)
                frame = self.frame(page)
                frame.wait_for_function('document.readyState === "complete"')
                self.click_in_target(page, TITLE, 'landing.hero.title')
                self.type_into(page, '#liveFontSize', '50')
                self.wait_style(frame, TITLE, 'fontSize', '50px')
                self.assertTrue(page.locator('#liveCodeSync').is_disabled())
                self.assertTrue(page.locator('#liveCodeAutoSync').is_disabled())
                self.assertIn('dev server', page.locator('#liveCodeSync').get_attribute('title'))
                self.assertIn('font-size: 50px !important;', self.wait_code(page, 'Css', 'font-size: 50px'))
                self.assertEqual(self.written(), '')
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
