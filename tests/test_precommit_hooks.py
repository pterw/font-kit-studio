"""The pre-commit and commit-msg hooks refuse what they promise to, in a real git commit.

Each test makes a scratch git repository in a temp folder, copies in this repository's
`.pre-commit-config.yaml` and the scripts its hooks call, runs `pre-commit install`, and
commits. The assertion is on the commit itself (made or not), not on the config text.

`pre-commit` is a dev requirement. Locally the module skips until it is installed; in CI
`FKS_REQUIRE_PRECOMMIT=1` turns a missing install into a failure, so CI cannot pass by
skipping (anti-pattern 14).
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / '.pre-commit-config.yaml'
SCRIPTS = ('scripts/dev/check_commit_messages.py', 'scripts/dev/check_js_syntax.py')
CLEAN_MESSAGE = 'docs: add a note\n\nThe note says why.\n'
AI_TRAILER = 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'


class PrecommitHookTests(unittest.TestCase):
    def setUp(self):
        if importlib.util.find_spec('pre_commit') is None:
            if os.environ.get('FKS_REQUIRE_PRECOMMIT') == '1':
                self.fail('pre-commit is not installed and FKS_REQUIRE_PRECOMMIT=1: '
                          'pip install -r requirements-dev.txt')
            self.skipTest('pip install -r requirements-dev.txt')
        scratch = Path(tempfile.mkdtemp(prefix='fks-hooks-'))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / 'repo'
        self.repo.mkdir()
        # pre-commit's cache lives beside the repository, never inside it. No global or system
        # git config reaches the scratch repository: a contributor's own core.hooksPath or
        # core.whitespace would otherwise change what these tests prove.
        self.env = dict(os.environ, PRE_COMMIT_HOME=str(scratch / 'pre-commit-home'),
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        HOME=str(scratch), USERPROFILE=str(scratch))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Hook Test')
        self.git('config', 'user.email', 'hooks@example.test')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.autocrlf', 'false')
        self.copy_config(CONFIG.read_text(encoding='utf-8'))
        for script in SCRIPTS:
            # Copied as LF text: a Windows checkout holds CRLF, which the whitespace hook
            # would rightly flag in a repository that does not convert line endings.
            self.write(script, (REPO / script).read_text(encoding='utf-8'))
        result = self.run_in_repo(sys.executable, '-m', 'pre_commit', 'install')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def copy_config(self, text):
        self.write('.pre-commit-config.yaml', text)

    def run_in_repo(self, *args):
        return subprocess.run(list(args), cwd=self.repo, env=self.env, capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=120)

    def git(self, *args):
        result = self.run_in_repo('git', *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)

    def commit(self, message=CLEAN_MESSAGE):
        """Stage everything and commit; return the result and whether a commit now exists."""
        self.git('add', '-A')
        result = self.run_in_repo('git', 'commit', '-q', '-m', message)
        made = self.run_in_repo('git', 'rev-parse', '--verify', '-q', 'HEAD').returncode == 0
        return result, made

    def test_a_clean_commit_goes_through(self):
        self.write('notes.txt', 'a line\n')
        result, made = self.commit()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(made)

    def test_trailing_whitespace_is_refused_and_nothing_is_committed(self):
        self.write('notes.txt', 'a line with a trailing space \n')
        result, made = self.commit()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(made, 'the commit was made despite the whitespace hook')
        self.assertIn('trailing whitespace', result.stdout + result.stderr)

    def test_an_ai_co_author_in_the_message_is_refused(self):
        self.write('notes.txt', 'a line\n')
        result, made = self.commit(f'{CLEAN_MESSAGE}\n{AI_TRAILER}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(made, 'the commit was made despite the commit-msg hook')
        self.assertIn('co-author', (result.stdout + result.stderr).lower())

    # A package file, which only the JavaScript hook matches (the static checks watch Studio,
    # the bridge and the provenance files, and need scripts/verify.py, absent here).
    @unittest.skipIf(shutil.which('node') is None, 'node is not on PATH; the JavaScript hook needs it')
    def test_package_javascript_with_a_syntax_error_is_refused(self):
        self.write('packages/fontkitstudio/src/good.js', 'export const ok = 1;\n')
        self.write('packages/fontkitstudio/src/bad.js', 'function (\n')
        result, made = self.commit()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(made)
        output = result.stdout + result.stderr
        # Both files reach the hook in one call; only the broken one is named.
        self.assertIn('check_js_syntax: FAIL packages/fontkitstudio/src/bad.js', output)
        self.assertNotIn('check_js_syntax: FAIL packages/fontkitstudio/src/good.js', output)

    @unittest.skipIf(shutil.which('node') is None, 'node is not on PATH; the JavaScript hook needs it')
    def test_valid_package_javascript_commits(self):
        self.write('packages/fontkitstudio/src/good.js', 'export const ok = 1;\n')
        self.write('packages/fontkitstudio/src/also-good.js', 'export const two = 2;\n')
        result, made = self.commit()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(made)

    def test_without_the_whitespace_hook_the_same_commit_would_go_through(self):
        # The control for the whitespace test: the refusal comes from that hook, not from
        # anything else in the setup.
        config = CONFIG.read_text(encoding='utf-8')
        start = config.index('      - id: whitespace')
        end = config.index('      - id: ruff')
        self.copy_config(config[:start] + config[end:])
        self.write('notes.txt', 'a line with a trailing space \n')
        result, made = self.commit()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(made)


if __name__ == '__main__':
    unittest.main()
