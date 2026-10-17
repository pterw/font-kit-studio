# R2.W2L brief: one announce-order helper, no polling sleep

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 (task R2.W2L), Addendum 19 and task R2.T2 (the three handshake tests
it fixed). PR B2 wave W2, phase 1, beside R2.W2T and R2.W2B2 (disjoint files). BASE
`73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`. Worktree `a scratch worktree` (detached at BASE; the controller creates it), task id
`w2l`. Tests only: no product file changes. Line budget: about 90 gross lines; explain any excess.

## Why

The whole-branch review (workspace `w2-review.md` items T12 and R6; checked in source) found two things in the tests R2.T2
landed:

1. `LiveCase.wait_greeted` (`tests/test_studio_live.py` 183-198) waits for the held image request with a fixed-interval poll,
   `for _ in range(100): if held: break; page.wait_for_timeout(50)`, then asserts `len(held) == 1`. AGENTS.md (Test Quality
   Rules) forbids new fixed sleeps where an event or condition can be awaited, and on a slow runner the 5 s cap fails a
   correct run.
2. The same seven-line setup (record the order, hold the load or not, connect with or without `?late=1`, wait to be greeted,
   check the order) is written out three times: `test_handshake_status_badges_and_target_query` (320, setup at 329-339),
   `test_every_control_message_carries_protocol_version_and_session` (1099, setup at 1105-1115) and
   `test_i3_every_iframe_load_regreets_both_announce_orders` (1164, setup at 1170-1177). A third copy is a finding (global
   rule 10). If one copy drifted, its test would force a different order than its name and docstring claim.

## Owned files (exact)

In `tests/test_studio_live.py` only: the three tests above, `LiveCase.hold_load` (171), `LiveCase.wait_greeted` (183) and at
most one new `LiveCase` method that forces an announce order for the three tests. Keep `LiveCase.open`'s signature
(`test_support.py` imports `LiveCase`), `ORDER_RECORDER` and the module constants. Read-only: `fontkit-studio.html`,
`tests/fixtures/studio/fake-target.html`, `tests/support.py` and every other file. Running worktrees beside yours:
`a scratch worktree` and `a scratch worktree`: never touch them.

## Read first

`constraints.md` (all of it); the R2.T2 brief and report (`docs/implementation/tasks/r2-task-t2-brief.md`,
`r2-task-t2-report.md`: how each order is forced and why); at BASE `tests/test_studio_live.py` 25-200, 315-360,
1095-1215.

## Requirements

1. **No poll.** The held image request is awaited by an event, not by a fixed-interval loop. The brief review
   (`task-w2l-brief-review.md`, Important 1-3) measured the naive form as racy: Playwright resolves an `expect_request`
   waiter before the route handler has run `held.append`, so reading `held` right after the event failed 4 of 12 runs under
   load. Use this design:
   - (a) Enter the waiter BEFORE the trigger, and make the trigger part of the helper: `wait_greeted` (or the new method)
     takes a `trigger` callable (the connect click; for the i3 test, `location.reload()` plus its existing
     `performance.timeOrigin` wait), and runs `with page.expect_request(<held image URL>, timeout=20_000): trigger()`.
   - (b) The event means "the page asked", not "the handler ran": make one round trip to the browser (an explicit
     `page.evaluate('0')` with a one-line comment saying why) before reading `held`.
   - (c) Then, in this order: `assertEqual(len(held), 1, 'the page requested its held image')`, the existing
     readyState/hello frame wait, then the release (`held.pop().fulfill(...)`). This order makes every mutant below fail at
     an assertion, not time out.
   - Catch the waiter's timeout (`from playwright.sync_api import TimeoutError as PlaywrightTimeout`, the repo convention;
     the import line is in scope) and call `self.fail('the page never requested its held image')`.
   - No `wait_for_timeout` remains in `hold_load`, `wait_greeted` or the new method (a structural check; say so in the
     report with the grep).
   The helper owns clearing the order recorder's lists before each reload (1181 at BASE today), so a second round never
   asserts stale entries.
2. **One setup.** One `LiveCase` method forces a given announce order (`('load', 'bridge-ready')` or the reverse) and returns
   what the three tests need: the frame, and the held request list or a way to answer it (the i3 test answers the hold
   again on each reload). The handshake test installs its badge observer before connecting: the helper either takes that
   step or the test installs it before calling the helper; choose the simpler. Each test keeps every assertion it has at
   BASE; only the setup moves.
3. **Same strength.** The three tests still force each order deterministically and assert it exactly, as R2.T2 requires.

## Mutants (each in the foreground; `fontkit-studio.html` or the test file edited in your worktree, restored in `finally`, SHA-256 before and after)

Re-run R2.T2's mutants against the refactored tests (they prove the tests kept their power):

1. `fontkit-studio.html` 4506 (in `startHandshake`) `live.sessionId = newSessionId();` becomes
   `live.sessionId = live.sessionId || newSessionId();`: the load-first handshake fails (one session where two are required).
2. 4654 (the frame's `load` listener) `if (!live.sessionId) live.sessionId = newSessionId();` becomes
   `live.sessionId = newSessionId();`: the
   bridge-ready-first handshake fails (`2 != 1` sessions).
3. The hold removed (the image answered at once): every bridge-ready-first variant fails at the order premise, never at a
   session assertion.

4. Requirement 1's timeout path: in the served copy of the fake target, change the held image's `<img src="/fks-hold-load.gif">`
   to another URL, so the page never requests the awaited URL; the wait fails with `the page never requested its held image`
   (a FAIL, not Playwright's TimeoutError).

Oracle (the review's BASE table, every failure at an assertion): M1 fails 4 subtests (handshake[load first],
every-control[load first], i3[bridge-ready first], i3[load first]); M2 fails 4 (handshake[bridge-ready first],
every-control[bridge-ready first], i3[bridge-ready first], i3[load first]); M3 fails 3 (one per test, at the `held`
assertion); mutant 4 fails 3 (one per test, at the `self.fail` message). The refactored tests must fail the same
(test, subTest) sets, each at an assertion; record the new line numbers, each mutant's command and SHA-256 before and after.

Sibling, report only (AGENTS.md anti-pattern 12): the same poll exists in `tests/test_studio_roles.py` near 1219-1222
(R2.W2T's file); list it in the report, do not fix it. Note: the every-control test's setup is at 1109-1115 (1105-1106 are
docstring).

## Focused gate

From the worktree, in Git Bash, five times in a row, all green:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_studio_live.StudioProtocolTests.test_handshake_status_badges_and_target_query test_studio_live.StudioFixRound1Tests.test_every_control_message_carries_protocol_version_and_session test_studio_live.StudioFixRound1Tests.test_i3_every_iframe_load_regreets_both_announce_orders test_support`
(confirm the class names first). Then once under load, beside
`sh ".superpowers/sdd/r2/tools/gate.sh" shard-2` from the same worktree in a
second shell (background it, wait for both, report both results). Also `python -m ruff check tests/test_studio_live.py` and,
after staging by name, `git diff --cached --check`. The worktree's files are CRLF (autocrlf); write the patch with
`git diff --cached --binary <BASE> --output=...` so it stays LF.

## Report and handoff

Report: the new wait and the helper; each mutant (command, failing tests and lines, SHA-256 before and after); the five
repeated runs and the loaded run; gross and material lines. Handoff: the patch `task-w2l-code.patch`, the commit subject
`test: await the held image and share the announce-order setup`, a draft body (why, wrapped at 72, no process narration)
and the R2.W2L plan item.
