"""scripts/dev/docs_only.py: when a pull request changes only Markdown.

Each case builds a real throwaway repository with a real merge commit and runs
the helper as CI does. Expected values come from the rules in the plan (every
changed path ends in .md, none is the root README.md or packages/*/README.md),
not from the helper.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / 'scripts' / 'dev' / 'docs_only.py'
GIT_ENV = {
    **os.environ,
    'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.com',
    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.com',
}


def git(cwd, *args):
    subprocess.run(['git', '-c', 'commit.gpgsign=false', *args], cwd=cwd, env=GIT_ENV,
                   check=True, capture_output=True)


def write(root, rel, text):
    path = Path(root, rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def make_merge(root, base_files, edits, deletes=(), renames=(), merge=True):
    """A base commit, a pull-request branch with the changes, and a merge of it.

    The merge's first parent is the base; `edits` are written on the branch.
    Without `merge`, the branch tip itself is HEAD (no second parent).
    """
    git(root, 'init', '-q', '-b', 'main')
    for rel in base_files:
        write(root, rel, 'base\n')
    git(root, 'add', '.')
    git(root, 'commit', '-q', '--allow-empty', '-m', 'base')
    git(root, 'checkout', '-q', '-b', 'pr')
    for rel, text in edits.items():
        write(root, rel, text)
    for rel in deletes:
        git(root, 'rm', '-q', rel)
    for old, new in renames:
        Path(root, new).parent.mkdir(parents=True, exist_ok=True)
        git(root, 'mv', old, new)
    git(root, 'add', '.')
    git(root, 'commit', '-q', '--allow-empty', '-m', 'change')
    if merge:
        git(root, 'checkout', '-q', 'main')
        git(root, 'merge', '-q', '--no-ff', '-m', 'merge', 'pr')


def run_helper(root, event='pull_request'):
    out = Path(root, 'github_output')
    env = {k: v for k, v in GIT_ENV.items() if k != 'GITHUB_EVENT_NAME'}
    env['GITHUB_OUTPUT'] = str(out)
    if event is not None:
        env['GITHUB_EVENT_NAME'] = event
    done = subprocess.run([sys.executable, str(HELPER)], cwd=root, env=env,
                          capture_output=True, text=True)
    return done, (out.read_text(encoding='utf-8') if out.exists() else '')


# (name, files at the base, edits, deletes, renames, expected output)
PRINTS = 'docs_only=true\n'
CASES = [
    ('markdown only', [], {'notes.md': 'x\n'}, (), (), PRINTS),
    ('docs guide alone', [], {'docs/guide.md': 'x\n'}, (), (), PRINTS),
    ('docs reference alone', [], {'docs/reference/x.md': 'x\n'}, (), (), PRINTS),
    ('AGENTS.md alone', [], {'AGENTS.md': 'x\n'}, (), (), PRINTS),
    ('a deleted markdown file is judged by its path', ['old.md'], {}, ['old.md'], (), PRINTS),
    ('a deleted code file is judged by its path', ['old.py'], {}, ['old.py'], (), ''),
    ('one md and one py', [], {'a.md': 'x\n', 'b.py': 'x\n'}, (), (), ''),
    ('root README alone', [], {'README.md': 'x\n'}, (), (), ''),
    ('package README alone', [], {'packages/fontkitstudio/README.md': 'x\n'}, (), (), ''),
    ('a README with a markdown file', [], {'README.md': 'x\n', 'a.md': 'x\n'}, (), (), ''),
    ('rename from code to markdown lists both paths', ['a.py'], {}, (), [('a.py', 'a.md')], ''),
    ('rename from markdown to code lists both paths', ['a.md'], {}, (), [('a.md', 'a.py')], ''),
    ('rename from README to another md lists both paths', ['README.md'], {}, (),
     [('README.md', 'docs/readme.md')], ''),
    ('markdown extension', [], {'a.markdown': 'x\n'}, (), (), ''),
    ('mdx extension', [], {'a.mdx': 'x\n'}, (), (), ''),
    ('unknown extension', [], {'a.xyz': 'x\n'}, (), (), ''),
    ('no extension', [], {'LICENSE': 'x\n'}, (), (), ''),
    ('an empty diff', [], {}, (), (), ''),
]


class DecisionTable(unittest.TestCase):
    def test_every_case(self):
        for name, base, edits, deletes, renames, expected in CASES:
            with self.subTest(name), tempfile.TemporaryDirectory() as root:
                make_merge(root, base, edits, deletes, renames)
                done, output = run_helper(root)
                self.assertEqual(output, expected, done.stderr)

    def test_a_head_that_is_not_a_merge_commit_prints_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            make_merge(root, [], {'a.md': 'x\n'}, merge=False)
            self.assertEqual(run_helper(root)[1], '')

    def test_an_event_other_than_pull_request_prints_nothing(self):
        for event in ('push', 'workflow_dispatch', 'workflow_call', '', None):
            with self.subTest(event), tempfile.TemporaryDirectory() as root:
                make_merge(root, [], {'a.md': 'x\n'})
                self.assertEqual(run_helper(root, event)[1], '')

    def test_a_git_failure_prints_nothing(self):
        with tempfile.TemporaryDirectory() as root:  # not a repository
            self.assertEqual(run_helper(root)[1], '')

    def test_an_error_is_not_a_skip(self):
        # A merge whose first parent cannot be read: the diff errors, so no output.
        with tempfile.TemporaryDirectory() as root:
            make_merge(root, [], {'a.md': 'x\n'})
            env = {**GIT_ENV, 'GITHUB_EVENT_NAME': 'pull_request',
                   'GITHUB_OUTPUT': str(Path(root, 'github_output')), 'PATH': ''}
            subprocess.run([sys.executable, str(HELPER)], cwd=root, env=env, capture_output=True)
            self.assertFalse(Path(root, 'github_output').exists()
                             and Path(root, 'github_output').read_text())


if __name__ == '__main__':
    unittest.main()
