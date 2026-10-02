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

    def test_the_default_is_chromium_and_firefox(self):
        result = import_support(None)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, 'chromium,firefox'), result.stderr)


if __name__ == '__main__':
    unittest.main()
