# P1 code report (mode: code, BASE 8e393ba, worktree C:/fks/tP1)

Files: `scripts/dev/check_commit_messages.py` (docstring usage + `check_message_file` + one branch in `main`), `tests/test_commit_messages.py` (new `MessageFileTests`, 8 tests). Patch: `task-P1-code.patch` (LF, 2 files, +108/-1; `git apply --check -R` passes).

Steps: 1 done, 2 done, 3 done, 4 done, 5 done, 6 below. Nothing committed.

## RED
`PYTHONPATH=tests python -m unittest test_commit_messages.MessageFileTests` -> `Ran 8 tests ... FAILED (errors=7)` (unrecognized `--message-file`, argparse exit 2). The 8th (combine with range/base) passed for the wrong reason in RED (argparse exits 2 on the unknown flag); mutation M3 proves it is real.

## GREEN
`PYTHONPATH=tests python -m unittest test_commit_messages` -> `Ran 29 tests ... OK` (21 existing unchanged + 8).

## Mutations (foreground, one at a time, restored after each)
- M1 drop the `#` skip: first run SURVIVED (OK). Cause: `# Co-Authored-By:` is already not matched by the co-author regex (anchored `^\s*`). Only the banner rule tolerates a leading `#` (`^\W*generated`). Fix: case 6 also holds `# Generated with Claude Code`, with a comment explaining why. Re-run M1: `FAILED (failures=1)` test_comment_lines_are_ignored.
- M2 `reasons = []`: failures=3 (co-author, session, banner tests).
- M3 exclusion removed: failures=2 (both subTests).

## Step 4: real hook (scratch repo under $TEMP, removed)
Hook: `python ".../check_commit_messages.py" --message-file "$1"`.
- `git commit -m "feat: x" -m "Why." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"` -> printed FAIL lines, exit 1, `git log`: "does not have any commits yet".
- clean `-m` -> OK line, committed (76468e4).
- editor flow (GIT_EDITOR script writes message plus `# Co-Authored-By: Claude ...` and `# Generated with Claude Code` comment lines): hook saw the `#` lines (the hook runs before git strips them), printed OK, exit 0, committed; stored body is just "Why." (git stripped the comments afterwards). So a trailer inside a `#` line does not block the commit.

## Gates
- `python -m ruff check .` -> All checks passed!
- `PYTHONPATH=tests python -m unittest test_commit_messages test_support` -> Ran 63 tests, OK
- `python scripts/verify.py --static-only` -> exit 0, last line `SKIP unittest/browser tests: --static-only; full acceptance not checked`
- pre-commit not run (not in the brief's gates; not run, AP 14). Full suites suite-a/b not run in this phase.

## Deviations / notes
- Working-copy files were CRLF (autocrlf); I normalised both owned files to LF (index is LF, patch has no CR).
- Mutual exclusion is a `parser.error` check in `main` (not an argparse group) because `--range` and `--base` were previously combinable; that behaviour is unchanged.
- `--repo` is ignored in message mode.

## Self-review (anti-patterns)
AP 8: every mode exercised (8 tests, each branch mutated). AP 12: one `check_message` serves both modes; no copied rule. AP 14: unrun gates listed above. AP 15: no process state in the diff. Test case 6 strengthened beyond the brief because it was vacuous for the trailer.

## Handoff
- Commit subject: `feat(dev): check a commit message before the commit exists`
- Body: A commit-msg hook has to judge the message git is about to write, not a commit that exists. Add --message-file, which runs the same check_message rules as the range mode, ignores `#` lines (git strips them only after the hook runs), and refuses to combine with --range or --base. Agent signatures are now caught before the commit exists, for every contributor.
- progress.md event draft: "P1: check_commit_messages.py gains --message-file (same rules, `#` lines ignored); 8 tests, 3 mutations killed; verified with a real commit-msg hook in a scratch repo (trailer refused, clean and editor-flow commits pass)."
- Landing: apply patch, re-run test_commit_messages + test_support, then the gates.

## Fix round 1 (controller ruling: check every line, `#` lines included)

Done: (1) `#`-line skip, and its docstring/usage mention, removed; `check_message_file` now calls `check_message(text)` on the whole file. (2) Case 6 replaced by `test_gits_standard_editor_comment_block_passes` and `test_signatures_in_comment_lines_are_refused`. (3) `test_an_indented_trailer_is_refused` added. (4) Real hook re-run.

RED (tests first, skip still present): `FAILED (failures=1)`, only `test_signatures_in_comment_lines_are_refused`; the git-comment-block test and the indented-trailer test passed already (expected: the skip hides nothing there, and the shared checker allows leading whitespace). GREEN after removing the skip: first run failed on my own assertion (below); after correcting it, `Ran 10 tests ... OK`.

FINDING (shared checker, not changed): `check_message` does NOT refuse `# Co-Authored-By: Claude <noreply@anthropic.com>`. CO_AUTHOR is anchored `^\s*co-authored-by`, so a `#` prefix hides it; only the banner rule tolerates a leading non-word char (`^\W*generated`). So of the two comment lines in the controller's case (b), the banner is refused and the commented co-author is not. Git does not read a `#`-prefixed line as a trailer, so the risk is a stray text line in history, not a real trailer; if the controller wants it refused, `CO_AUTHOR` needs `^\W*` (a change to check_message, outside this fix). Test (b) therefore asserts exit 1 and exactly one FAIL, the banner.

Mutation: re-adding a `#` skip (crudely, joining kept lines with "x") fails 5 tests including `test_signatures_in_comment_lines_are_refused`; restored, 10 OK.

Real hook (scratch repo, removed): `git commit -m "feat: x" -m "# Generated with Claude Code"` -> `FAIL message: AI generation banner: # Generated with Claude Code`, exit 1, no commit. Clean `-m` -> OK, exit 0. The earlier editor-flow claim in this report (comment trailer commits fine) is superseded: a `# Generated with ...` line in the editor now refuses.

Gates: `python -m ruff check .` All checks passed!; `PYTHONPATH=tests python -m unittest test_commit_messages test_support -v` Ran 65 tests, OK. Patch regenerated vs 8e393ba (LF, 2 files, +125/-1, `git apply --check -R` passes).

Handoff update: commit body should say every line is checked (git keeps `#` lines for -m and -F); drop the "ignores # lines" wording. progress.md draft: replace "`#` lines ignored" with "every line checked, comment lines included".


## Landing (controller, 2026-10-04)

The re-review found that `git commit -v` hands the hook the staged diff below git's scissors line, so with every line checked, committing a diff that holds a signature-like line (this repository's own checker tests do) would be refused. Git drops everything from the scissors line on before it stores the message, so `--message-file` now cuts the text there too. Test first: a message whose diff below the scissors line carries a `Generated with [Claude Code](...)` line passes (RED before the cut), and a banner above the line is still refused. The first version of that test used diff lines the rules never match and passed before the fix; it was replaced. `test_commit_messages` 33 OK, with `test_support` 67 OK; ruff clean.
