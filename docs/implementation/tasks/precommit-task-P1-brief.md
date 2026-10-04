# P1 brief: check a commit message before the commit exists

Plan: `docs/plans/2026-10-04-dev-precommit-hooks.md` (P1). Constraints:
`C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/precommit/constraints.md`
(read all of it first).

## Goal

`scripts/dev/check_commit_messages.py` today reads commits that already exist (`--range`,
`--base`, or the last commit). A `commit-msg` hook needs it to check the message git is
about to write, from the file git passes the hook. Add `--message-file PATH`, which runs
the same rules on that text, so the rule against agent signatures is enforced before a
commit exists, for every contributor.

## Definition of done

- `--message-file PATH` checks the text with `check_message` (the same function the range
  mode uses; no second copy of any rule, anti-pattern 12).
- Lines whose first character is `#` are ignored before checking: git runs the
  `commit-msg` hook before it strips its comment lines, so an editor-written message still
  holds them. Confirm this with a real `git commit` in a scratch repository and say in the
  report what you saw (a rejected trailer inside a `#` line must not block the commit).
- Output: one `FAIL message: <reason>` line per finding, then
  `commit-message check: FAIL: the message carries agent or process signatures` (exit 1),
  or `commit-message check: OK: message checked` (exit 0). A file that cannot be read:
  `commit-message check: ERROR: <reason>` on stderr, exit 1.
- `--message-file` with `--range` or `--base` is a usage error (argparse, exit 2).
- The range mode and every existing test are unchanged.

## Owns

`scripts/dev/check_commit_messages.py`, `tests/test_commit_messages.py` (add a test class;
do not edit the existing ones). Update the module docstring's usage block with the new
form.

## Steps

- [ ] **1. Failing tests** in a new `MessageFileTests` class (temp files via
  `tempfile.TemporaryDirectory`, written with `open(..., 'w', encoding='utf-8', newline='\n')`;
  call `main([...])` and capture stdout/stderr with `contextlib.redirect_stdout`/`stderr`):
  1. a clean message (`feat(dev): add a thing\n\nWhy it matters.\n`): exit 0, the OK line;
  2. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` trailer: exit 1, a
     `FAIL message:` line naming the co-author, the FAIL summary;
  3. `Claude-Session: https://claude.ai/code/session_x` trailer: exit 1;
  4. a `🤖 Generated with [Claude Code](https://claude.com/claude-code)` line: exit 1;
  5. a human co-author `Co-authored-by: Claude Monet <claude@monet.example>`: exit 0;
  6. the trailer from case 2 inside a comment line (`# Co-Authored-By: Claude ... <noreply@anthropic.com>`)
     plus git's usual comment block (`# Please enter the commit message ...`): exit 0;
  7. a missing file: exit 1, the ERROR line on stderr, nothing on stdout;
  8. `--message-file x --range a..b` and `--message-file x --base origin/main`: `SystemExit`
     with code 2.
  Run `PYTHONPATH=tests python -m unittest test_commit_messages -v`: RED.
- [ ] **2. Implement**: add the argument (mutually exclusive with `--range` and `--base`
  through an argparse group, or a check that calls `parser.error`); read the file as UTF-8
  with `errors='replace'`; drop `#` lines; call `check_message`; print as above. Keep it
  flat: one small function and one branch in `main`.
- [ ] **3. GREEN**, then mutations, one at a time, in the foreground: drop the `#`-line skip
  (case 6 fails); make the message mode return OK without checking (cases 2-4 fail);
  remove the mutual exclusion (case 8 fails).
- [ ] **4. A real hook, by hand**: in a scratch repository outside the repo (`git init`),
  write `.git/hooks/commit-msg` that runs
  `python "<repo>/scripts/dev/check_commit_messages.py" --message-file "$1"`; commit with
  `-m` and an AI co-author trailer (refused, nothing committed: `git log` has no commit),
  with a clean message (committed), and once through an editor-like flow
  (`GIT_EDITOR` set to a small script that appends a `#` comment line holding the trailer;
  committed). Record the commands and outcomes in the report.
- [ ] **5. Gates for the code phase**: `python -m ruff check .`; `PYTHONPATH=tests python -m
  unittest test_commit_messages test_support -v`; `python scripts/verify.py --static-only`.
- [ ] **6. Report** with a Handoff: the patch, a `progress.md` event draft, the commit
  subject `feat(dev): check a commit message before the commit exists` and a why-body.

## Report

Code phase: `.superpowers/sdd/precommit/task-P1-code-report.md`, patch
`.superpowers/sdd/precommit/task-P1-code.patch` (both under
`C:/Users/peter/Python Projects/font-kit-studio`). Landing:
`docs/implementation/tasks/precommit-task-P1-report.md`.
