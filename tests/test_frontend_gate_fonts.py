"""The free-fonts measurement in a real browser: a font call that never answers must not hang the gate.

`document.fonts.ready` and `document.fonts.load()` can stay pending (a stalled
stylesheet, a blocked proxy). `page.evaluate` has no timeout of its own, so an
unbounded measurement would stall the gate until the CI job timed out, before
the retry, the REPORT and FAIL lines or the test suites ran. The measurement
shares one deadline; a family that has not answered by then is missing.
"""

import faulthandler
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ENGINES, launch  # noqa: E402
from scripts.dev import _frontend_gate_network as network  # noqa: E402

DEADLINE_MS = 300
BOUND_S = 5          # far above the deadline, far below the 15 s default and any CI timeout
WATCHDOG_S = 30      # a regression ends the run here, loudly, instead of hanging it

# Answers like a loaded face for every family except those named Hang, which never answers.
HANGING_LOAD = """() => {
    document.fonts.load = (spec) => spec.includes('Hang')
        ? new Promise(() => {})
        : Promise.resolve([{status: 'loaded'}]);
}"""
HANGING_READY = """() => {
    Object.defineProperty(document.fonts, 'ready', {value: new Promise(() => {})});
}"""
REJECTED_READY = """() => {
    Object.defineProperty(document.fonts, 'ready', {value: Promise.reject(new Error('no fonts'))});
}"""
NO_FONTS_API = """() => {
    Object.defineProperty(document, 'fonts', {value: undefined});
}"""


class FontMeasurementDeadlineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.runtime = sync_playwright().start()

    @classmethod
    def tearDownClass(cls):
        cls.runtime.stop()

    def setUp(self):
        # A blocked sync Playwright call ignores SIGALRM, so the watchdog is faulthandler's:
        # it prints every thread's stack and exits the process.
        faulthandler.dump_traceback_later(WATCHDOG_S, exit=True)
        self.addCleanup(faulthandler.cancel_dump_traceback_later)

    def page(self, engine, script=None):
        browser = launch(self.runtime, engine)
        self.addCleanup(browser.close)
        page = browser.new_page()
        page.set_content('<!doctype html><title>fonts</title>')
        if script:
            page.evaluate(script)
        return page

    def measure(self, page, families, deadline_ms=DEADLINE_MS):
        started = time.monotonic()
        results = network.measure_font_faces(page, families, deadline_ms)
        return results, time.monotonic() - started

    def test_a_load_that_never_answers_is_missing_and_the_others_still_report(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.page(engine, HANGING_LOAD)
                results, elapsed = self.measure(page, ['Inter', 'Hang One', 'Fraunces'])
                self.assertEqual(results, {'Inter': [1, 1], 'Hang One': [0, 0], 'Fraunces': [1, 1]})
                self.assertLess(elapsed, BOUND_S)

    def test_a_ready_promise_that_never_resolves_leaves_every_family_missing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.page(engine, HANGING_READY)
                results, elapsed = self.measure(page, ['Inter', 'Fraunces'])
                self.assertEqual(results, {'Inter': [0, 0], 'Fraunces': [0, 0]})
                self.assertLess(elapsed, BOUND_S)

    def test_a_rejected_ready_or_a_missing_fonts_api_leaves_every_family_missing(self):
        for engine in ENGINES:
            for name, script in (('rejected ready', REJECTED_READY), ('no document.fonts', NO_FONTS_API)):
                with self.subTest(engine=engine, case=name):
                    page = self.page(engine, script)
                    results, elapsed = self.measure(page, ['Inter', 'Fraunces'])
                    self.assertEqual(results, {'Inter': [0, 0], 'Fraunces': [0, 0]})
                    self.assertLess(elapsed, BOUND_S)

    def test_the_deadline_is_shared_not_spent_per_family(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.page(engine, HANGING_LOAD)
                families = [f'Hang {n}' for n in range(8)]
                results, elapsed = self.measure(page, families)
                self.assertEqual(set(results), set(families))
                self.assertLess(elapsed, DEADLINE_MS / 1000 * 6, 'eight stalled families wait once, not eight times (serial is x8)')

    def test_a_measurement_that_answers_does_not_wait_for_the_deadline(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.page(engine)
                # A family nothing declares resolves with no faces straight away.
                results, elapsed = self.measure(page, ['No Such Family'], deadline_ms=10000)
                self.assertEqual(results, {'No Such Family': [0, 0]})
                self.assertLess(elapsed, BOUND_S)

    def test_unanswered_families_reach_the_retry_and_failure_reporting(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.page(engine, HANGING_LOAD)
                retried = []
                results = network.settle_free_fonts(
                    lambda only: network.measure_font_faces(page, only or ['Inter', 'Hang One'], DEADLINE_MS),
                    retried.append, lambda ms: None)
                self.assertEqual(retried, [['Hang One'], ['Hang One']], 'the missing family is retried, bounded')
                self.assertEqual(network.free_font_failures(results),
                                 ['family Hang One resolved no loaded face from Google Fonts'])


if __name__ == '__main__':
    unittest.main()
