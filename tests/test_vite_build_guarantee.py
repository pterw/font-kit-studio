"""`vite build` with fontkitStudio() in the config ships nothing of Font Kit Studio."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from fixture_support import FIXTURES, require_fixture, vite_bin

NODE = shutil.which('node')
BUILD_LINE = 'Font Kit Studio · dev only: not added to this build'
FORBIDDEN = (b'fontkit-bridge', b'@fontkit', b'data-allowed-origins', b'Font Kit Studio')


class ViteBuildGuaranteeTests(unittest.TestCase):
    def build(self, name):
        require_fixture(self, name)
        self.assertIsNotNone(NODE, 'node is not on PATH; building the fixture needs it')
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        result = subprocess.run(
            [NODE, str(vite_bin(name)), 'build', '--outDir', out, '--emptyOutDir'],
            cwd=FIXTURES / name,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        # The permanent plugin in the config says, once, that it added nothing.
        self.assertEqual(result.stdout.count(BUILD_LINE), 1, result.stdout)
        return Path(out)

    def check(self, name):
        out = self.build(name)
        files = [p for p in out.rglob('*') if p.is_file()]
        self.assertTrue(files, 'the build wrote no files')
        for path in files:
            data = path.read_bytes()
            for needle in FORBIDDEN:
                # assertFalse, not assertNotIn: a failure names the file instead of dumping the bundle.
                self.assertFalse(needle in data, f'{needle!r} found in {path.name}')
        # Positive control: the scan read the real bundle and the real page.
        self.assertTrue(
            any(b'vite.hero.title' in p.read_bytes() for p in files),
            'no output file carries the app markup, so the scan proves nothing',
        )
        index = (out / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<script type="module"', index)

    def test_vite_8_build_has_no_trace_of_studio(self):
        self.check('vite-react')

    def test_vite_7_build_has_no_trace_of_studio(self):
        self.check('vite7-react')


if __name__ == '__main__':
    unittest.main()
