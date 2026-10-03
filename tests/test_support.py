"""The shared browser-test harness (tests/support.py) refuses an engine list that runs no browser."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent


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
