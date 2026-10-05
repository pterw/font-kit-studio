# Task 7a code report (mode: code)

Changed: `tests/test_friction.py` (new, one test method, per engine in ENGINES). Patch: `.superpowers/sdd/r1-pr-c/task-7a-code.patch` (`git apply --check -R` passes).
Ran `npm ci --prefix fixtures/vite-react` in C:/fks/t7a first. Nothing committed.

## Brief steps
All done. Spawn/pump/stop copied from test_one_command_vite (not imported); stdin=DEVNULL; clock starts just before Popen; stops when badge matches `^Connected \(\d+ targets?\)$` and `#targetAppFrame` holds `vite.hero.title`; stderr line `friction: X.X s (budget 60 s)`; `FRICTION_BUDGET_S = 60`; badge wait 90 s, fails with badge text on timeout; https routes aborted; cleanup via addCleanup.

## Evidence
- GREEN, 3 runs: `friction: 4.6 s`, `2.0 s`, `1.4 s` (first included cold caches).
- Mutation budget 0.1: `AssertionError: 1.469... not less than or equal to 0.1 : the one command took 1.5 s to connect; the budget is 0.1 s`.
- Mutation pattern `pages?` (with badge wait cut to 5000 ms to keep the run short): `AssertionError: Studio never showed '^Connected \\(\\d+ pages?\\)$'; badge says 'Connected (3 targets)'` (fails at the wait, not the budget).
- node_modules renamed away: plain run `OK (skipped=1)`; with FKS_REQUIRE_FIXTURES=1: `AssertionError: fixtures/vite-react/node_modules is missing and FKS_REQUIRE_FIXTURES=1 ...`. Folder restored; all mutations restored by editing (constants re-checked by grep).
- `PYTHONPATH=tests python -m unittest test_friction test_support`: Ran 35 tests, OK.
- `python -m ruff check .`: All checks passed. `python -m pre_commit run --files tests/test_friction.py`: whitespace and ruff passed; JS/static hooks skipped (no files).
- Full suite not run (only a new test file; focused gates per the brief).

## Self-review
- AP 13: process stopped in addCleanup by handle (Ctrl-Break / SIGINT, kill on timeout). AP 14: skip becomes failure under FKS_REQUIRE_FIXTURES=1 (shown). Rule 7: https aborted. Rule 6: nothing written to the fixture. No fixed sleeps. No `page.content()`.
- Not vacuous: each guard mutated above.
- Concern: `ENGINES` loops share one command start and one clock, so a second engine's time includes the first's; with the default Chromium only this is moot.

## Handoff
- CI: add `test_friction` to the fixtures job's `unittest` list in `.github/workflows/quality-gate.yml`.
- progress.md event draft: "R1.7a: tests/test_friction.py runs the one command on the Vite + React fixture with stdin closed and fails if Studio is not connected within FRICTION_BUDGET_S (60 s, to be reset from the first green CI run plus 50 percent). Local runs 1.4 to 4.6 s."
- Commit subject: `test: hold the one-command start to a time budget`
- Body draft: "The promise is one command and no setup. Nothing measured how long that takes, so a slow or stuck start could ship unnoticed. The test runs the real command with no person in the loop, times it to a connected Studio with the page's title in the frame, and fails over a budget. The budget is a first guess for the controller to set from CI."

## Fix round 1
- Important 1: each engine's subTest now spawns its own command, reads `Open:`, starts its clock at spawn, stops at Connected plus the title attached, and stops that process in `finally` before the next engine. The `friction:` line and the budget check are per engine. A comment says browser launch and context creation stay inside the timed region on purpose (a user's browser launch is part of the friction).
- Minor: the badge-text read on failure has `timeout=1000` and falls back to `'<unreadable>'`; the `Open:` wait polls every 0.5 s, fails at once with the collected output when the process exits, and otherwise stops at a 90 s deadline; `assertRegex` replaces `assertTrue(re.match)`; unused `import re` removed.
- Evidence: two default runs OK (`friction: 1.2 s (budget 60 s)`). `FKS_ENGINES=chromium,chromium` printed two friction lines (1.2 s, 0.7 s), so the clock is per engine. Mutations re-shown and restored: budget 0.1 gives the budget message; `pages?` (wait cut to 5 s) gives `never showed ... badge says 'Connected (3 targets)'`; a bogus CLI flag gives `the command exited (2) before "Open:"; output:` in 0.7 s. The `<unreadable>` fallback is not exercised by a test.
- `test_friction test_support`: Ran 35, OK. ruff: all checks passed. Patch regenerated at the same path; `git apply --check -R` passes.
