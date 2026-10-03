"""The shared browser-test harness (tests/support.py) refuses an engine list that runs no browser."""

import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
import support  # noqa: E402


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


if __name__ == '__main__':
    unittest.main()
