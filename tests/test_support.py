"""The shared browser-test harness (tests/support.py).

It refuses an engine list that runs no browser, shares one browser per engine, and snapshots the
canvas without the markup that Studio derives from the canvas width. A guard keeps raw reads of
a page's markup out of the other tests.
"""

import ast
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
import support  # noqa: E402
from test_studio_live import LiveCase  # noqa: E402


def import_support(engines):
    """Import tests/support.py in a fresh interpreter with FKS_ENGINES set (None: unset)."""
    env = {key: value for key, value in os.environ.items() if key != 'FKS_ENGINES'}
    if engines is not None:
        env['FKS_ENGINES'] = engines
    return subprocess.run(
        [sys.executable, '-c', 'import support; print(",".join(support.ENGINES))'],
        cwd=TESTS, env=env, capture_output=True, text=True, timeout=60)


class EngineSelectionTest(unittest.TestCase):
    # Loop-based browser tests ('for engine in ENGINES') pass without running a browser when
    # ENGINES is empty, so an empty selection must fail at import instead.
    def test_an_empty_selection_is_an_error_not_zero_browsers(self):
        for value in ('', ',', ' , ,', '   '):
            with self.subTest(FKS_ENGINES=value):
                result = import_support(value)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('FKS_ENGINES selects no browser engine', result.stderr)

    def test_an_unknown_engine_is_rejected_by_name(self):
        for value in ('bogus', 'chromium,bogus', 'chrome'):
            with self.subTest(FKS_ENGINES=value):
                result = import_support(value)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('unknown engine', result.stderr)
                self.assertIn(value.split(',')[-1], result.stderr)

    def test_known_engines_are_accepted(self):
        for value, expected in (('chromium', 'chromium'), ('chromium, firefox', 'chromium,firefox'),
                                ('webkit', 'webkit'), ('Firefox,', 'firefox')):
            with self.subTest(FKS_ENGINES=value):
                result = import_support(value)
                self.assertEqual((result.returncode, result.stdout.strip()), (0, expected), result.stderr)

    def test_the_default_is_chromium_only(self):
        # The full suite runs on Chromium; Firefox runs the canary in firefox_canary.py (D037).
        result = import_support(None)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, 'chromium'), result.stderr)


class SharedBrowserTest(unittest.TestCase):
    # The browser tests share one driver and one browser per engine for the whole process and give
    # each test a fresh context (v0.2.1 T0). The probes below run two consecutive tests of a real
    # base class, so the claim is about the harness the suites actually use.
    ENGINE = 'chromium'

    @classmethod
    def setUpClass(cls):
        if cls.ENGINE not in support.ENGINES:
            raise unittest.SkipTest(f'{cls.ENGINE} is not in FKS_ENGINES')

    @staticmethod
    def run_probe(base, open_page, between=None):
        """Run two consecutive tests of `base`; the first leaves state behind, the second looks for it."""
        seen = {}

        class Probe(base):
            def test_1_leave_state(self):
                page = open_page(self)
                page.evaluate('localStorage.setItem("probe", "left")')
                if page.url.startswith('http'):  # cookies need a web origin; file:// pages keep storage only
                    page.context.add_cookies([{'name': 'probe', 'value': 'left', 'url': page.url}])
                seen['browser'], seen['context'] = page.context.browser, page.context
                if between:
                    between(seen)

            def test_2_look_for_it(self):
                page = open_page(self)
                seen['second_browser'], seen['second_context'] = page.context.browser, page.context
                seen['storage'] = page.evaluate('localStorage.getItem("probe")')
                seen['cookies'] = page.context.cookies()
                seen['contexts'] = list(page.context.browser.contexts)
                seen['browser_connected'] = seen['browser'].is_connected()

        suite = unittest.TestSuite([Probe('test_1_leave_state'), Probe('test_2_look_for_it')])
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
        return seen, result, stream.getvalue()

    def assert_shared_browser_fresh_context(self, base, open_page):
        seen, result, output = self.run_probe(base, open_page)
        self.assertTrue(result.wasSuccessful(), output)
        self.assertIs(seen['second_browser'], seen['browser'], 'the browser is shared between tests')
        self.assertTrue(seen['browser_connected'], 'the shared browser stays up between tests')
        self.assertIsNot(seen['second_context'], seen['context'])
        self.assertNotIn(seen['context'], seen['contexts'], "tearDown closes the first test's context")
        self.assertIsNone(seen['storage'], 'storage set by the first test is absent in the second')
        self.assertEqual([c for c in seen['cookies'] if c['name'] == 'probe'], [])

    def assert_replaces_a_disconnected_browser(self, base, open_page):
        seen, result, output = self.run_probe(base, open_page, between=lambda s: s['browser'].close())
        self.assertTrue(result.wasSuccessful(), output)
        self.assertFalse(seen['browser'].is_connected())
        self.assertIsNot(seen['second_browser'], seen['browser'])
        self.assertTrue(seen['second_browser'].is_connected())
        self.assertIsNone(seen['storage'])

    def test_studio_live_tests_share_the_browser_but_not_the_context(self):
        import test_studio_live
        self.assert_shared_browser_fresh_context(test_studio_live.LiveCase, lambda t: t.open(self.ENGINE)[0])

    def test_v011_tests_share_the_browser_but_not_the_context(self):
        import test_font_kit_studio_v011
        self.assert_shared_browser_fresh_context(test_font_kit_studio_v011.BrowserCase,
                                                 lambda t: t.page(self.ENGINE)[0])

    def test_live_integration_tests_share_the_browser_but_not_the_context(self):
        import test_live_integration
        self.assert_shared_browser_fresh_context(test_live_integration.LiveIntegrationCase,
                                                 lambda t: t.open(self.ENGINE))

    def test_a_disconnected_browser_is_replaced_for_the_next_live_test(self):
        import test_studio_live
        self.assert_replaces_a_disconnected_browser(test_studio_live.LiveCase, lambda t: t.open(self.ENGINE)[0])

    def test_a_disconnected_browser_is_replaced_for_the_next_v011_test(self):
        import test_font_kit_studio_v011
        self.assert_replaces_a_disconnected_browser(test_font_kit_studio_v011.BrowserCase,
                                                    lambda t: t.page(self.ENGINE)[0])

    def test_a_disconnected_browser_is_replaced_for_the_next_integration_test(self):
        import test_live_integration
        self.assert_replaces_a_disconnected_browser(test_live_integration.LiveIntegrationCase,
                                                    lambda t: t.open(self.ENGINE))

    def test_support_hands_out_a_working_browser_after_the_shared_one_disconnects(self):
        first = support.shared_browser(self.ENGINE)
        self.assertIs(support.shared_browser(self.ENGINE), first, 'one browser per engine')
        first.close()
        self.assertFalse(first.is_connected())
        second = support.shared_browser(self.ENGINE)
        self.assertIsNot(second, first)
        self.assertTrue(second.is_connected())
        context = second.new_context()
        try:
            page = context.new_page()
            page.goto('data:text/html,<title>ok</title>')
            self.assertEqual(page.title(), 'ok')
        finally:
            context.close()

    def test_an_explicit_launch_is_still_a_separate_browser(self):
        # Tests that need their own browser keep calling launch(); closing it must not touch the shared one.
        shared = support.shared_browser(self.ENGINE)
        own = support.launch(support.shared_runtime(), self.ENGINE)
        try:
            self.assertIsNot(own, shared)
        finally:
            own.close()
        self.assertTrue(shared.is_connected())


class CloseContextsTest(unittest.TestCase):
    # A crashed browser makes context.close() raise; that must not fail the test that crashed it.
    # A close that fails on a live browser is a real error and must surface, after the rest closed.
    class Browser:
        def __init__(self, connected):
            self.connected = connected

        def is_connected(self):
            return self.connected

    class Context:
        def __init__(self, browser, error=None):
            self.browser, self.error, self.closed = browser, error, False

        def close(self):
            self.closed = True
            if self.error:
                raise self.error

    def test_a_close_error_on_a_disconnected_browser_is_swallowed(self):
        contexts = [self.Context(self.Browser(False), RuntimeError('target closed'))]
        support.close_contexts(contexts)
        self.assertEqual(contexts, [])

    def test_a_close_error_on_a_connected_browser_is_raised(self):
        contexts = [self.Context(self.Browser(True), RuntimeError('real failure'))]
        with self.assertRaisesRegex(RuntimeError, 'real failure'):
            support.close_contexts(contexts)

    def test_every_context_is_closed_and_the_first_error_is_raised_at_the_end(self):
        live = self.Browser(True)
        first, second, third = (self.Context(live, RuntimeError('first')), self.Context(live, RuntimeError('second')),
                                self.Context(live))
        contexts = [first, second, third]
        with self.assertRaisesRegex(RuntimeError, 'first'):
            support.close_contexts(contexts)
        self.assertEqual([first.closed, second.closed, third.closed], [True, True, True])
        self.assertEqual(contexts, [], 'the list is cleared so a second tearDown does not retry them')

    def test_a_swallowed_error_does_not_hide_a_later_real_one(self):
        gone, live = self.Browser(False), self.Browser(True)
        contexts = [self.Context(gone, RuntimeError('gone')), self.Context(live, RuntimeError('real'))]
        with self.assertRaisesRegex(RuntimeError, 'real'):
            support.close_contexts(contexts)


class NewContextRetryTest(unittest.TestCase):
    # After a browser crash, is_connected() can stay True until Playwright dispatches the event,
    # so the first new_context() on the cached browser raises. One relaunch and retry recovers.
    class Browser:
        def __init__(self, error=None):
            self.error, self.closed, self.contexts_made = error, False, 0

        def is_connected(self):
            return not self.closed

        def new_context(self, **options):
            self.contexts_made += 1
            if self.error:
                raise self.error
            return ('context', options)

        def close(self):
            self.closed = True

    @staticmethod
    def closed_error(message):
        from playwright.sync_api import Error
        return Error(message)

    def setUp(self):
        from unittest import mock
        self.mock = mock
        self.cache = mock.patch.dict(support._shared['browsers'], clear=True)
        self.cache.start()
        self.addCleanup(self.cache.stop)

    def test_a_stale_browser_is_replaced_and_the_call_retried_once(self):
        stale, fresh = self.Browser(self.closed_error('Target page, context or browser has been closed')), self.Browser()
        support._shared['browsers']['chromium'] = stale
        with self.mock.patch.object(support, 'launch', return_value=fresh) as launch, \
                self.mock.patch.object(support, 'shared_runtime', return_value=object()):
            self.assertEqual(support.new_context('chromium', viewport=None), ('context', {'viewport': None}))
        self.assertEqual(launch.call_count, 1)
        self.assertTrue(stale.closed, 'the stale browser is dropped')
        self.assertIs(support._shared['browsers']['chromium'], fresh)

    def test_a_second_failure_is_raised_not_retried_again(self):
        from playwright.sync_api import Error
        stale, also_bad = (self.Browser(self.closed_error('Target closed: first')),
                           self.Browser(self.closed_error('Target closed: second')))
        support._shared['browsers']['chromium'] = stale
        with self.mock.patch.object(support, 'launch', return_value=also_bad) as launch, \
                self.mock.patch.object(support, 'shared_runtime', return_value=object()):
            with self.assertRaisesRegex(Error, 'second'):
                support.new_context('chromium')
        self.assertEqual(launch.call_count, 1)
        self.assertEqual(also_bad.contexts_made, 1)

    def test_an_error_that_is_not_a_crash_propagates_without_a_relaunch(self):
        # A bad option must not close a healthy shared browser (and the earlier contexts of the same
        # test with it), nor raise the same error twice in a chained traceback.
        from playwright.sync_api import Error
        for error in (TypeError("new_context() got an unexpected keyword argument 'bogus_option'"),
                      Error('BrowserContext.new_context: Invalid viewport size')):
            with self.subTest(error=type(error).__name__):
                healthy = self.Browser(error)
                support._shared['browsers']['chromium'] = healthy
                with self.mock.patch.object(support, 'launch') as launch:
                    with self.assertRaises(type(error)) as caught:
                        support.new_context('chromium', bogus_option=1)
                launch.assert_not_called()
                self.assertIs(caught.exception, error)
                self.assertIsNone(caught.exception.__context__, 'not chained to a first attempt')
                self.assertFalse(healthy.closed, 'the healthy browser is left up')
                self.assertEqual(healthy.contexts_made, 1)
                self.assertIs(support._shared['browsers']['chromium'], healthy)

    def test_a_playwright_error_on_a_browser_that_is_gone_retries_whatever_it_says(self):
        stale, fresh = self.Browser(self.closed_error('Connection terminated')), self.Browser()
        reports = iter([True, False])   # still "connected" when handed out, gone by the time it fails
        stale.is_connected = lambda: next(reports, False)
        support._shared['browsers']['chromium'] = stale
        with self.mock.patch.object(support, 'launch', return_value=fresh), \
                self.mock.patch.object(support, 'shared_runtime', return_value=object()):
            self.assertEqual(support.new_context('chromium'), ('context', {}))

    def test_a_healthy_browser_is_not_relaunched(self):
        healthy = self.Browser()
        support._shared['browsers']['chromium'] = healthy
        with self.mock.patch.object(support, 'launch') as launch:
            support.new_context('chromium')
        launch.assert_not_called()


class CanaryListTest(unittest.TestCase):
    # CI runs firefox_canary.py on Gecko in an advisory step, where a name that no longer
    # loads would go unnoticed. Resolving the list here makes that fail the Chromium suite.
    def test_every_canary_name_is_a_test_class_with_tests(self):
        # loadTestsFromName does not raise for a missing name; it returns a placeholder test
        # that errors only when run. Resolve each name to the class itself instead.
        import importlib
        import firefox_canary
        self.assertTrue(firefox_canary.CANARY)
        for name in firefox_canary.CANARY:
            with self.subTest(name=name):
                module_name, _, class_name = name.partition('.')
                cls = getattr(importlib.import_module(module_name), class_name, None)
                self.assertTrue(isinstance(cls, type) and issubclass(cls, unittest.TestCase), name)
                self.assertGreater(unittest.TestLoader().loadTestsFromTestCase(cls).countTestCases(), 0)

    def test_the_canary_is_not_collected_by_discover(self):
        # The canary loads tests from other modules, so collecting it would run those tests
        # twice under the same ids.
        stack = [unittest.TestLoader().discover(str(TESTS))]
        ids = []
        while stack:
            item = stack.pop()
            if isinstance(item, unittest.TestSuite):
                stack.extend(item)
            else:
                ids.append(item.id())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('test_support.CanaryListTest.test_the_canary_is_not_collected_by_discover', ids)


class CanvasSnapshotTest(LiveCase):
    """canvas_snapshot() drops the markup Studio derives from the canvas width and keeps what the composition says.

    The width changes for real (a viewport change, Library to Composer), and each test that equates snapshots first
    shows that the raw markup moves with it. Without that premise an equal snapshot would prove nothing.
    """
    # Three rows that collapse at different canvas widths, so one sweep flips every one of them somewhere.
    ROWS = [
        {'type': 'row', 'childCount': 2, 'collapseAt': 400, 'ratios': [1, 3], 'gap': 10,
         'children': [{'type': 'spacer'}, {'type': 'text', 'text': 'Alpha'}]},
        {'type': 'row', 'childCount': 3, 'collapseAt': 700, 'ratios': [2, 1, 1], 'gap': 20,
         'children': [{'type': 'spacer'}, {'type': 'text', 'text': 'Beta'}, {'type': 'rule'}]},
        {'type': 'row', 'childCount': 2, 'collapseAt': 900, 'ratios': [1, 1], 'gap': 30,
         'children': [{'type': 'text', 'text': 'Gamma'}, {'type': 'text', 'text': 'Delta'}]},
    ]
    COLLAPSE_AT = tuple(row['collapseAt'] for row in ROWS)
    # Viewport widths. The canvas is narrower and not in step with them (the layout changes at 1100px and 900px).
    WIDTHS = (1600, 1200, 1000, 900, 700, 500, 390)
    ROW_COLLAPSED = 'document.querySelector("#composerCanvas .row-layout").classList.contains("is-collapsed")'

    @staticmethod
    def ids(html):
        return re.findall(r'data-(?:row-)?id="([^"]+)"', html)

    @staticmethod
    def without_ids(html):
        return re.sub(r'(data-(?:row-)?id=")[^"]+', r'\1', html)

    @staticmethod
    def selected(html):
        """The ids of the slots, top-level and row children, whose wrapper carries the selected class."""
        return re.findall(r'class="(?:row-child )?flow-slot selected" data-id="([^"]+)"', html)

    def studio(self, engine, composer=True):
        page, errors = self.open(engine, query=False)
        if composer:
            page.locator('#modeComposer').click()
        return page, errors

    def raw(self, page):
        return page.locator('#composerCanvas').inner_html()

    def settle(self, page):
        """Two animation frames: the ResizeObserver callback for a resize is delivered in the frame after it."""
        page.evaluate('() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))')

    def wait_for_rows(self, page):
        """Every imported row has caught up with the width: collapsed exactly when the canvas is at or below its collapseAt."""
        page.wait_for_function('''(thresholds) => {
            const canvas = document.querySelector('#composerCanvas');
            const width = canvas.getBoundingClientRect().width;
            const rows = [...canvas.querySelectorAll('.row-layout')];
            return rows.length === thresholds.length
                && rows.every((row, i) => row.classList.contains('is-collapsed') === (width <= thresholds[i]));
        }''', arg=list(self.COLLAPSE_AT))

    def sweep(self, page, caught_up):
        """Raw markup, snapshot and per-row collapsed flags at every width, read once `caught_up(page)` has returned."""
        raws, snapshots, collapsed = [], [], []
        for width in self.WIDTHS:
            page.set_viewport_size({'width': width, 'height': 900})
            caught_up(page)
            raws.append(self.raw(page))
            snapshots.append(support.canvas_snapshot(page))
            collapsed.append(page.locator('#composerCanvas .row-layout').evaluate_all(
                'rows => rows.map(row => row.classList.contains("is-collapsed"))'))
        return raws, snapshots, collapsed

    def test_a_width_change_alone_changes_the_raw_markup_but_not_the_snapshot(self):
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.wait_for_function(f'() => !{self.ROW_COLLAPSED}')
                wide_raw, wide = self.raw(page), support.canvas_snapshot(page)
                page.set_viewport_size({'width': 500, 'height': 900})
                page.wait_for_function(f'() => {self.ROW_COLLAPSED}')
                narrow_raw, narrow = self.raw(page), support.canvas_snapshot(page)
                self.assertNotEqual(wide_raw, narrow_raw, 'the raw markup follows the width, so it cannot be compared')
                self.assertIn('is-collapsed', narrow_raw)
                self.assertIn('grid-template-columns: 1fr;', narrow_raw)
                self.assertEqual(wide, narrow)
                for derived in ('is-collapsed', 'grid-template-columns'):
                    self.assertNotIn(derived, wide)
                # Everything else stays: the composition's text, the row and its other inline styles.
                self.assertIn('Image and prose, finally allowed to speak sideways.', wide)
                self.assertIn('class="row-layout" data-row-id="', wide)
                self.assertIn('gap: 32px; align-items: center;', wide)
                self.assertEqual(errors, [])

    def test_the_snapshot_is_the_same_before_and_after_the_composer_is_shown(self):
        # Studio renders the canvas while the Composer is hidden (width 0), so the row is collapsed until the first
        # frame after the Composer opens. A test that snapshots right after switching modes can land on either side.
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine, composer=False)
                self.assertFalse(page.locator('#composerView').is_visible())
                hidden_raw, hidden = self.raw(page), support.canvas_snapshot(page)
                self.assertIn('is-collapsed', hidden_raw)
                page.locator('#modeComposer').click()
                page.wait_for_function(f'() => !{self.ROW_COLLAPSED}')
                shown_raw, shown = self.raw(page), support.canvas_snapshot(page)
                self.assertNotEqual(hidden_raw, shown_raw)
                self.assertNotIn('is-collapsed', shown_raw)
                self.assertEqual(hidden, shown)
                self.assertEqual(errors, [])

    def test_a_real_re_render_changes_the_snapshot_even_when_the_composition_is_back_to_the_preset(self):
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                original = support.canvas_snapshot(page)
                # Apply on an untouched preset renders nothing, so an equal snapshot is not the result of ignoring too much.
                page.locator('#applyPreset').click()
                self.assertRegex(page.locator('#composerStatus').inner_text(), r'already applied')
                self.assertEqual(support.canvas_snapshot(page), original)
                # With an edit, Apply puts the preset back: the same text again, but new slot ids.
                page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
                page.locator('#slotInspector [data-bind="text"]').fill('My own wordmark')
                self.assertIn('My own wordmark', support.canvas_snapshot(page))
                page.once('dialog', lambda dialog: dialog.accept())
                page.locator('#applyPreset').click()
                page.wait_for_function('() => /applied\\. Every slot/.test(document.querySelector("#composerStatus").textContent)')
                rerendered = support.canvas_snapshot(page)
                self.assertNotIn('My own wordmark', rerendered)
                self.assertNotEqual(rerendered, original)
                self.assertTrue(self.ids(original) and set(self.ids(original)).isdisjoint(self.ids(rerendered)), 'every id is new')
                self.assertEqual(self.without_ids(rerendered), self.without_ids(original), 'the ids are the only difference')
                self.assertEqual(errors, [])

    def test_a_changed_canvas_width_or_colour_changes_the_snapshot_without_a_row_collapsing(self):
        # The canvas element's own declared style follows the composition (canvasWidth, background), not the layout width.
        # 720px is still above the editorial row's 700px collapse point, so the markup inside the canvas does not move:
        # only a snapshot that includes the canvas element itself sees the change.
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.wait_for_function(f'() => !{self.ROW_COLLAPSED}')
                inner, before = self.raw(page), support.canvas_snapshot(page)
                page.locator('#canvasWidth').select_option('720')
                page.wait_for_function('() => Math.round(document.querySelector("#composerCanvas").getBoundingClientRect().width) === 720')
                self.assertFalse(page.evaluate(f'() => {self.ROW_COLLAPSED}'), 'the row stays expanded at 720px')
                self.assertEqual(self.raw(page), inner, 'the markup inside the canvas cannot see the new width')
                resized = support.canvas_snapshot(page)
                self.assertNotEqual(resized, before)
                self.assertIn('width: min(100%, 720px)', resized)
                page.locator('#canvasBgHex').fill('#112233')
                self.assertEqual(self.raw(page), inner, 'nor the new colour')
                recoloured = support.canvas_snapshot(page)
                self.assertNotEqual(recoloured, resized)
                self.assertIn('background: rgb(17, 34, 51)', recoloured)
                self.assertEqual(errors, [])

    def test_the_snapshot_keeps_which_slot_is_selected(self):
        # Selection is not derived from the width, so the `selected` class stays and moves with the click.
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                slots = page.locator('#composerCanvas > .flow-slot').evaluate_all('els => els.map(el => el.dataset.id)')
                children = page.locator('#composerCanvas .row-child').evaluate_all('els => els.map(el => el.dataset.id)')
                self.assertGreater(len(slots), 1)
                self.assertGreater(len(children), 1)
                initial = support.canvas_snapshot(page)
                self.assertEqual(self.selected(initial), [slots[0]], 'applying a preset selects its first slot')
                page.locator('#composerCanvas > .flow-slot').nth(1).click(position={'x': 3, 'y': 3})
                second = support.canvas_snapshot(page)
                self.assertEqual(self.selected(second), [slots[1]])
                self.assertNotEqual(second, initial)
                page.locator('#composerCanvas .row-child').nth(1).click(position={'x': 3, 'y': 3})
                child = support.canvas_snapshot(page)
                self.assertEqual(self.selected(child), [children[1]])
                self.assertIn(f'class="row-child flow-slot selected" data-id="{children[1]}"', child)
                self.assertEqual(errors, [])

    def test_rows_that_collapse_at_different_widths_snapshot_the_same_at_every_width(self):
        # Each row flips at its own width. If the canvas gains markup that follows the width and that support.py does
        # not name, the snapshots here differ and point at it.
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.assertIn('Composition imported.', self.import_document(
                    page, {'version': '0.1.1', 'composition': {'slots': self.ROWS}}))
                raws, snapshots, collapsed = self.sweep(page, self.wait_for_rows)
                for index, collapse_at in enumerate(self.COLLAPSE_AT):
                    self.assertEqual({flags[index] for flags in collapsed}, {True, False},
                                     f'the sweep must collapse and expand the row that collapses at {collapse_at}px')
                self.assertGreater(len(set(raws)), 1)
                self.assertEqual(len(set(snapshots)), 1)
                for text in ('Alpha', 'Beta', 'Gamma', 'Delta'):
                    self.assertIn(text, snapshots[0])
                self.assertEqual(errors, [])

    def test_every_shipped_preset_snapshots_the_same_at_every_width(self):
        for engine in support.ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                presets = page.locator('#compositionPreset option').evaluate_all('options => options.map(o => o.value)')
                self.assertGreater(len(presets), 1)
                for preset in presets:
                    with self.subTest(preset=preset):
                        page.set_viewport_size({'width': self.WIDTHS[0], 'height': 900})
                        page.locator('#compositionPreset').select_option(preset)
                        _, snapshots, _ = self.sweep(page, self.settle)
                        self.assertEqual(len(set(snapshots)), 1, f'the {preset} preset follows the width in the markup')
                        self.assertIn('flow-slot', snapshots[0])
                self.assertEqual(errors, [])


# Reading a page's markup raw is how the canvas race got into the tests: the text moves with the layout width as well as
# with the composition. Studio's canvas goes through support.canvas_snapshot(); this rule keeps the other spellings out.
# A target app's markup is different: the bridge round-trips it byte for byte, so those tests compare it raw on purpose,
# through a `frame`, and calls on a `frame` are not flagged. A script held in a variable is not seen.
RAW_MARKUP_READS = ('inner_html', 'outer_html', 'content')
RAW_MARKUP_EVALUATORS = ('evaluate', 'evaluate_all', 'evaluate_handle', 'eval_on_selector', 'eval_on_selector_all')
TARGET_FRAME = 'frame'
RAW_MARKUP_EXEMPT = ('support.py', 'test_support.py')   # the helper itself, and the tests that show why it exists


def raw_markup_reads(source):
    """(line, call) for every raw read of a page's markup in the Python `source`, in line order."""
    def receiver(node):
        # page.locator(...).evaluate and self.page.evaluate lead back to their first name; a held locator is its own name.
        while isinstance(node, (ast.Attribute, ast.Call, ast.Subscript)):
            node = node.func if isinstance(node, ast.Call) else node.value
        return node.id if isinstance(node, ast.Name) else None

    reads = []
    for call in ast.walk(ast.parse(source)):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)):
            continue
        name = call.func.attr
        if name in RAW_MARKUP_READS:
            reads.append((call.lineno, f'.{name}()'))
        elif name in RAW_MARKUP_EVALUATORS and receiver(call.func.value) != TARGET_FRAME:
            script = ' '.join(part.value
                              for argument in (*call.args, *(keyword.value for keyword in call.keywords))
                              for part in ast.walk(argument) if isinstance(part, ast.Constant) and isinstance(part.value, str))
            if 'innerHTML' in script or 'outerHTML' in script:
                reads.append((call.lineno, f'.{name}() reading innerHTML or outerHTML'))
    return sorted(reads)


def raw_markup_offenders(directory):
    """'file:line call' for every raw read in the test modules of `directory`, except in RAW_MARKUP_EXEMPT."""
    return [f'{path.name}:{line} {call}'
            for path in sorted(Path(directory).glob('*.py')) if path.name not in RAW_MARKUP_EXEMPT
            for line, call in raw_markup_reads(path.read_text(encoding='utf-8'))]


class RawMarkupGuardTest(unittest.TestCase):
    FLAGGED = (
        "page.inner_html('#composerCanvas')",
        "page.locator('#composerCanvas').inner_html()",
        "page.locator('#composerCanvas').outer_html()",
        "canvas = page.locator('#composerCanvas')\nbefore = canvas.inner_html()",   # a held locator
        'page.content()',
        'studio.content()',   # Studio inside a host page
        '''page.evaluate("document.querySelector('#composerCanvas').innerHTML")''',
        '''page.evaluate("() => document.body.outerHTML")''',
        '''page.eval_on_selector("#composerCanvas", "el => el.innerHTML")''',
        '''page.eval_on_selector_all(".flow-slot", "els => els.map(el => el.outerHTML)")''',
        '''page.locator("#composerCanvas").evaluate("el => el.innerHTML")''',
        '''canvas.evaluate("el => el.outerHTML")''',
        '''page.locator("#composerCanvas").evaluate(\n    "el => "\n    "el.innerHTML")''',   # over several lines
    )
    NOT_FLAGGED = (
        '''frame.evaluate("document.querySelector('main').innerHTML")''',   # a target app is compared raw on purpose
        '''frame.evaluate("document.body.outerHTML")''',
        "page.locator('#composerCanvas').inner_text()",
        '''page.evaluate("document.title")''',
        'canvas_snapshot(page)',
        'note = "page.inner_html() and page.content()"',   # text, not a call
        '# page.content()',
    )

    def test_every_spelling_of_a_raw_read_is_flagged(self):
        for source in self.FLAGGED:
            with self.subTest(source=source):
                self.assertEqual(len(raw_markup_reads(source)), 1)

    def test_text_attributes_and_a_target_frame_are_not_flagged(self):
        for source in self.NOT_FLAGGED:
            with self.subTest(source=source):
                self.assertEqual(raw_markup_reads(source), [])

    def test_a_scan_names_the_file_and_line_and_exempts_the_helper_and_its_tests(self):
        with tempfile.TemporaryDirectory() as scratch:
            scratch = Path(scratch)
            (scratch / 'test_offender.py').write_text(
                "canvas = page.locator('#composerCanvas')\nbefore = canvas.inner_html()\nafter = page.content()\n")
            (scratch / 'test_clean.py').write_text('before = canvas_snapshot(page)\n')
            for exempt in RAW_MARKUP_EXEMPT:
                (scratch / exempt).write_text('page.content()\n')
            self.assertEqual(raw_markup_offenders(scratch),
                             ['test_offender.py:2 .inner_html()', 'test_offender.py:3 .content()'])

    def test_no_test_reads_a_pages_markup_raw(self):
        self.assertEqual(raw_markup_offenders(TESTS), [],
                         'compare support.canvas_snapshot(page) for the canvas; elsewhere assert text, attributes or counts, '
                         "not markup (a target app's markup goes through a `frame`)")


if __name__ == '__main__':
    unittest.main()
