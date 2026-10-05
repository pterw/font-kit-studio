"""Type check for `fontkitstudio/vite` (R1.8a): the real TypeScript compiler, on a strict fixture.

`fixtures/vite-ts` imports the plugin as a Vite project's `vite.config.ts` would. Without the
shipped declaration `tsc` fails with TS7016; `bad-usage.ts` proves the types are not `any`.
"""

import shutil
import subprocess
import unittest

from fixture_support import FIXTURES, require_fixture

NODE = shutil.which('node')
FIXTURE = FIXTURES / 'vite-ts'
TSC = FIXTURE / 'node_modules' / 'typescript' / 'bin' / 'tsc'


def run_tsc(*args):
    return subprocess.run(
        [NODE, str(TSC), *args],
        cwd=FIXTURE,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=120,
    )


@unittest.skipUnless(NODE, 'node is not installed')
class ViteTypesTests(unittest.TestCase):
    def setUp(self):
        require_fixture(self, 'vite-ts')

    def test_strict_vite_config_type_checks(self):
        result = run_tsc('-p', '.')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_misuse_is_a_type_error_not_any(self):
        result = run_tsc('-p', 'tsconfig.bad.json')
        self.assertNotEqual(result.returncode, 0, 'bad-usage.ts type-checked: types are any?')
        self.assertIn('bad-usage.ts', result.stdout)
        self.assertIn('TS2322', result.stdout)


if __name__ == '__main__':
    unittest.main()
