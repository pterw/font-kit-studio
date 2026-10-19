"""Role round trips through the real `fontkitstudio` command, the Vite plugins and the proxies (R2.7I1).

Each case opens the real Studio over the command's own URL, presses Detect text styles, previews one
role by keystrokes, rerenders the page its own way, waits for Studio to say the page changed, detects
again, and clears.
Members of the existing one-command and fixture modules are borrowed by assignment (public ones only):
test_one_command_vite.OneCommandViteBrowserTest: start, pump, stop, wait_badge;
test_one_command_next.OneCommandNextBrowserTest: start_next, drain, tail, stop_next, start_command, wait_badge;
test_one_command_proxy.OneCommandProxyBrowserTest: stop_helper, wait_badge;
test_vite_build_guarantee.ViteBuildGuaranteeTests: build; test_r2_react.ReactCorpusTest: guarded_context.
"""

import re
import subprocess
import unittest
from collections import namedtuple

import support
import test_one_command_next as nxt
import test_one_command_proxy as prox
import test_one_command_vite as vite
import test_r2_react as react
import test_vite_build_guarantee as built
from fixture_support import require_fixture
from helpers_csp_server import start_csp_server
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts

OWNED = 'style[data-fontkit-role-styles]'
GUARD = {'aborted': 2, 'fallback': 0}
PAGE_CHANGED = 'The page changed since the last Detect; press Detect text styles. This page has not been checked.'
PROXY_CSP = "script-src 'self'; style-src 'self' 'unsafe-inline'"
SNAP = """() => {
    const props = ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform'];
    const rows = [...document.querySelectorAll('[data-design-id]')].map((el) => {
        const s = getComputedStyle(el);
        return [el.dataset.designId, props.map((p) => s[p])];
    });
    return [document.querySelector('main').outerHTML, rows, document.querySelectorAll('[style]').length];
}"""
Case = namedtuple('Case', 'title row label value prop before after css')
VITE = Case('[data-design-id="vite.hero.title"]', '[data-design-id="vite.hero.title"]', 'Size (px)', '48',
            'fontSize', '32px', '48px', 'font-size: 48px')
NEXT = Case('[data-design-id="next.hero.title"]', '[data-design-id="next.hero.title"]', 'Size (px)', '48',
            'fontSize', '40px', '48px', 'font-size: 48px')
BOOTSTRAP = Case('[data-design-id="bs.hero.title"]', '[data-design-id="bs.hero.title"]', 'Weight', '700',
                 'fontWeight', '500', '700', 'font-weight: 700')


class RoundTrip:
    """The shared Detect, preview, rerender, page-changed sentence, Detect, Clear sequence (not a TestCase)."""
    guarded_context = react.ReactCorpusTest.guarded_context

    def open_studio(self, engine, url, init_script=None):
        context, counts = self.guarded_context(engine)
        self.contexts.append(context)
        if init_script:
            context.add_init_script(init_script)
        page = context.new_page()
        errors, console_errors = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        page.goto(url)
        self.wait_badge(page, vite.CONNECTED, timeout=60000)
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        frame.wait_for_function('document.readyState === "complete"')
        self.wait_badge(page, vite.CONNECTED)
        return page, frame, errors, console_errors, counts

    def detect(self, page):
        page.get_by_role('button', name='Detect text styles', exact=True).click()
        page.wait_for_function('!document.querySelector("#roleStatus").textContent.startsWith("Detecting")')
        status = page.locator('#roleStatus').inner_text()
        self.assertTrue(status.startswith('Detected'), status)

    def computed(self, frame, case):
        return frame.evaluate(f'(s) => getComputedStyle(document.querySelector(s)).{case.prop}', case.title)

    def wait_computed(self, frame, case, want):
        frame.wait_for_function(
            f'([s, want]) => getComputedStyle(document.querySelector(s)).{case.prop} === want',
            arg=[case.title, want], timeout=15000, polling=50)

    def wait_owned(self, frame, count):
        frame.wait_for_function('([sel, n]) => document.querySelectorAll(sel).length === n', arg=[OWNED, count], polling=50)

    def wait_page_changed(self, page):
        page.wait_for_function(
            '(t) => document.querySelector("#roleStatus").textContent === t', arg=PAGE_CHANGED, timeout=15000)

    def round_trip(self, engine, url, case, rerender, init_script=None, restore=None):
        """Returns (errors, console_errors, counts, page, frame) after every step has been asserted."""
        frame = None
        try:
            page, frame, errors, console_errors, counts = self.open_studio(engine, url, init_script)
            self.detect(page)
            self.assertEqual(self.computed(frame, case), case.before)
            before = frame.evaluate(SNAP)
            row = page.locator('#roleRows > li', has_text=case.row)
            row.get_by_label(re.compile(r'^Preview this role for ')).check()
            field = row.get_by_label(re.compile(rf'^{re.escape(case.label)} for '))
            field.focus()
            field.press('ControlOrMeta+A')
            field.press_sequentially(case.value)
            page.get_by_role('button', name='Apply selected roles', exact=True).click()
            self.wait_computed(frame, case, case.after)
            self.wait_owned(frame, 1)
            page.wait_for_function(
                '(t) => document.querySelector("#rolePreviewCss").textContent.includes(t)', arg=case.css)
            applied = frame.evaluate(SNAP)
            self.assertEqual(applied[0], before[0])   # the preview is a stylesheet only
            title_id = case.title.split('"')[1]
            self.assertEqual([r for r in applied[1] if r[0] != title_id], [r for r in before[1] if r[0] != title_id])
            owned = frame.query_selector(OWNED)
            rerender(page, frame)
            self.assertEqual(self.computed(frame, case), case.after)
            self.assertTrue(owned.evaluate('el => el.isConnected'))
            self.assertEqual(frame.locator(OWNED).count(), 1)
            self.assertEqual(frame.evaluate('document.querySelectorAll("[style]").length'), before[2])
            rendered = frame.evaluate(SNAP)
            self.wait_page_changed(page)
            self.detect(page)
            page.get_by_role('button', name='Clear preview', exact=True).click()
            self.wait_owned(frame, 0)
            cleared = frame.evaluate(SNAP)
            self.assertEqual(cleared[0], rendered[0])
            self.assertEqual(cleared[1], before[1])
            self.assertEqual((cleared[2], rendered[2]), (before[2], before[2]))
            self.assertEqual(self.computed(frame, case), case.before)
            self.assertEqual(counts, GUARD)
            self.assertEqual(errors, [])
            return errors, console_errors, counts, page, frame
        finally:
            if restore is not None and frame is not None:
                restore(frame)


@unittest.skipIf(vite.NODE is None, 'node is not on PATH; the command tests need it')
class ViteEntrypointTests(RoundTrip, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([vite.NODE, str(vite.PACKAGE / 'scripts' / 'bundle.js')], cwd=support.REPO, check=True)

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))

    start = vite.OneCommandViteBrowserTest.start
    pump = vite.OneCommandViteBrowserTest.pump
    stop = vite.OneCommandViteBrowserTest.stop
    wait_badge = vite.OneCommandViteBrowserTest.wait_badge
    build = built.ViteBuildGuaranteeTests.build

    def click_twice(self, page, frame):
        page.locator('#bridgeModeInteract').click()
        page.wait_for_function('document.querySelector("#bridgeModeInteract").getAttribute("aria-pressed") === "true"')
        button = frame.locator('[data-design-id="vite.hero.cta"]')
        button.click()
        button.click()
        frame.wait_for_function(
            'document.querySelector(\'[data-design-id="vite.hero.cta"]\').textContent === "Clicked 2 times"',
            polling=50)

    def command_round_trip(self, fixture):
        url = self.start(fixture)
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.round_trip(engine, url, VITE, self.click_twice)

    def test_vite8_command_detect_apply_rerender_clear(self):
        """Given `fontkitstudio` run in fixtures/vite-react, when Studio detects, previews Size 48 on the title
        role, the page renders twice from a click, Studio shows the page-changed sentence, Detect is pressed
        again and Clear is pressed, then the title is 48px before and after the render with the same owned
        sheet and no style attribute, and Clear removes the sheet and restores every computed property and
        the markup."""
        self.command_round_trip('vite-react')

    def test_vite7_command_detect_apply_rerender_clear(self):
        """Given `fontkitstudio` run in fixtures/vite7-react, when Studio detects, previews Size 48 on the title
        role, the page renders twice from a click, Studio shows the page-changed sentence, Detect is pressed
        again and Clear is pressed, then the title is 48px before and after the render with the same owned
        sheet and no style attribute, and Clear removes the sheet and restores every computed property and
        the markup."""
        self.command_round_trip('vite7-react')

    def test_vite_builds_ship_neither_bridge_nor_role_css(self):
        """Given vite build of both fixtures with the permanent plugin in the config, when every output file is
        scanned, then none holds the bridge or Studio needles or the role sheet names and the build holds the
        app markup."""
        needles = built.FORBIDDEN + (b'fontkit-role-styles', b'design:roles-apply', b'design:roles-clear')
        for name in ('vite-react', 'vite7-react'):
            with self.subTest(fixture=name):
                files = [p for p in self.build(name).rglob('*') if p.is_file()]
                self.assertTrue(files, 'the build wrote no files')
                for path in files:
                    data = path.read_bytes()
                    for needle in needles:
                        self.assertFalse(needle in data, f'{needle!r} found in {name}/{path.name}')
                self.assertTrue(any(b'vite.hero.title' in p.read_bytes() for p in files),
                                'no output file carries the app markup, so the scan proves nothing')


@unittest.skipIf(prox.NODE is None, 'node is not on PATH; the proxy runner tests need it')
class ProxyEntrypointTests(RoundTrip, unittest.TestCase):
    stop_helper = prox.OneCommandProxyBrowserTest.stop_helper
    wait_badge = prox.OneCommandProxyBrowserTest.wait_badge

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))
        server, self.origin = start_csp_server(prox.FIXTURE, csp=PROXY_CSP)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)   # runs first
        port = server.server_address[1]
        self.proc = subprocess.Popen(
            [prox.NODE, str(prox.HELPER), f'http://localhost:{port}/index.html', str(support.HTML),
             str(support.REPO / 'fontkit-bridge.js')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
        self.addCleanup(self.stop_helper)
        self.assertEqual(self.proc.stdout.readline().strip(), 'Font Kit Studio · dev only')
        line = self.proc.stdout.readline().strip()
        self.assertTrue(line.startswith('Open: http://localhost:'), line)
        self.url = line[len('Open: '):]

    def replace_title(self, page, frame):
        old = frame.query_selector(BOOTSTRAP.title)
        frame.evaluate(
            """(s) => {
                const old = document.querySelector(s), fresh = document.createElement(old.localName);
                for (const a of old.attributes) fresh.setAttribute(a.name, a.value);
                fresh.textContent = old.textContent;
                old.replaceWith(fresh);
            }""", BOOTSTRAP.title)
        self.assertFalse(old.evaluate('el => el.isConnected'))

    def test_bootstrap_proxy_detect_apply_rerender_clear(self):
        """Given a Bootstrap 5 page behind the proxy whose policy allows its own scripts and inline styles (the
        strict style-src 'self' outcome, stylesheet-blocked, is proved in test_r2_integration.py), when Studio
        detects, previews Weight 700 on the title role, the page replaces its own title element, Studio
        shows the page-changed sentence, Detect is pressed again and Clear is pressed, then the title weight
        is 500, 700, 700 on the new node, the old node is disconnected, Clear removes the sheet and restores
        every computed property, and neither document records a CSP violation."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                _, _, _, page, frame = self.round_trip(
                    engine, self.url, BOOTSTRAP, self.replace_title, init_script=prox.RECORD_VIOLATIONS)
                self.assertEqual(frame.evaluate('window.__cspViolations'), [])
                self.assertEqual(page.evaluate('window.__cspViolations'), [])


@unittest.skipIf(nxt.NODE is None, 'node is not on PATH; the command tests need it')
class NextEntrypointTests(RoundTrip, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([nxt.NODE, str(nxt.PACKAGE / 'scripts' / 'bundle.js')], cwd=support.REPO, check=True)

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))
        require_fixture(self, 'next-app')

    start_next = nxt.OneCommandNextBrowserTest.start_next
    drain = nxt.OneCommandNextBrowserTest.drain
    tail = nxt.OneCommandNextBrowserTest.tail
    stop_next = nxt.OneCommandNextBrowserTest.stop_next
    start_command = nxt.OneCommandNextBrowserTest.start_command
    wait_badge = nxt.OneCommandNextBrowserTest.wait_badge

    def write_until_applied(self, frame, css, data, colour):
        """Rewrite until the hot update shows the lead colour: a lone write can be coalesced away."""
        waits = (1000, 1000, 1000, 1000, 10000)
        for wait in waits:
            css.write_bytes(data)
            try:
                frame.wait_for_function(
                    '([s, c]) => getComputedStyle(document.querySelector(s)).color === c',
                    arg=[nxt.LEAD, colour], timeout=wait, polling=50)
                return
            except PlaywrightTimeout:
                continue
        self.fail(f'the CSS never hot-updated to {colour} after {len(waits)} writes; last computed colour '
                  + frame.evaluate('(s) => getComputedStyle(document.querySelector(s)).color', nxt.LEAD))

    def test_next_proxy_detect_apply_rerender_clear(self):
        """Given Next.js dev behind `fontkitstudio <url>`, when Studio detects, previews Size 48 on the title
        role, globals.css hot-updates through the proxy, Studio shows the page-changed sentence, Detect is pressed
        again and Clear is pressed, then the title is 40px, 48px, 48px with the lead colour changed, the page
        not reloaded and the sheet unchanged, Clear removes the sheet and restores every computed property,
        and no hydration error is logged."""
        css = nxt.APP / 'app' / 'globals.css'
        original = css.read_bytes()
        changed = original.replace(b'rgb(51, 51, 51)', b'rgb(200, 0, 0)')
        self.assertNotEqual(changed, original)
        self.addCleanup(css.write_bytes, original)   # registered before the first write
        url = self.start_command(self.start_next())

        def hot_update(page, frame):
            frame.evaluate('window.__fksMarker = 1')
            self.write_until_applied(frame, css, changed, 'rgb(200, 0, 0)')
            self.assertEqual(frame.evaluate('window.__fksMarker'), 1)   # no reload

        for engine in ENGINES:
            with self.subTest(engine=engine):
                _, console_errors, _, _, _ = self.round_trip(
                    engine, url, NEXT, hot_update,
                    restore=lambda frame: self.write_until_applied(frame, css, original, 'rgb(51, 51, 51)'))
                self.assertEqual([m for m in console_errors if 'hydrat' in m.lower()], [])


if __name__ == '__main__':
    unittest.main()
