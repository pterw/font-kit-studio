# Review: gate font measurement deadline

Verdict: **Approved**. Three optional nits, none blocking.

Scope reviewed: the uncommitted diff of `scripts/dev/_frontend_gate_network.py`,
the new `tests/test_frontend_gate_fonts.py`, and the "Gate font measurement
deadline" section of `docs/implementation/tasks/v02-review-fixes-report.md`.
Other modified files in the tree were ignored on purpose.

Branch `ccr-9eab25c9-mgatzt`, HEAD `7b7c542`, uncommitted work. Engine:
Chromium only (`FKS_ENGINES=chromium`, `/opt/pw-browsers/chromium`). Firefox
was not run.

## Gate evidence

- `python -m unittest tests.test_frontend_gate_fonts tests.test_frontend_gate_helpers tests.test_frontend_gate_report tests.test_frontend_gate_runner -v`:
  `Ran 157 tests in 4.140s` / `OK`. The new module alone: `Ran 5 tests in 3.526s` / `OK`.
- `python scripts/dev/frontend_gate.py --offline --engines chromium`:
  `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines, 0 FAIL lines`.
  Not run: the online free-fonts check (`check_free_fonts_load`). Offline mode
  skips it and Google Fonts is unreachable here, so the glue code at
  `_frontend_gate_network.py:252-253` was not exercised end to end. It is a
  one-line call to the tested `measure_font_faces`.
- `python scripts/verify.py --static-only`: `PASS HTML IDs: 88 unique static IDs`,
  `PASS JavaScript syntax`, three `PASS provenance` lines.
- `node --check fontkit-bridge.js`: ok.
- `check_commit_messages.py --range origin/main..HEAD`: `OK: 16 commits checked`.

## Probes

**Does the evaluate always settle?** Yes for every promise state a browser can
produce. Probed in Chromium with a 300 ms deadline (scratch script, outside
the repo):

| Case | Result | Time |
|------|--------|------|
| `fonts.load` pending for one family | that family `[0,0]`, others report | bounded |
| `fonts.ready` pending (test 2) | all `[0,0]` | bounded |
| `fonts.load` rejects | `{'A': [0,0], 'B': [0,0]}` | 0.0 s |
| `fonts.load` resolves after the deadline | `{'A': [0,0]}` | 0.3 s |
| `fonts.ready` rejects after the race returned | no `unhandledrejection` event | n/a |
| `fonts.ready` rejects before/during the race | `evaluate` raises `Error: r` | 0.0 s |
| `document.fonts` undefined | `evaluate` raises `TypeError` | 0.0 s |

The two raising cases do not hang. They are not reachable in Chromium or
Firefox (`ready` never rejects, `document.fonts` always exists) and the old
code raised the same way. `run_one` turns a raising check into a FAIL and the
run continues (`test_a_check_that_raises_is_a_fail_and_the_run_continues`
passes). See nit 1.

**Late-resolving load mutating the result after the race?** The loser of the
race keeps running and can write `results[family]` later
(`_frontend_gate_network.py:61-63`). In the "late" probe the late load
resolved 10 ms after the return and Python still saw `[0, 0]`: Playwright
serializes the returned object in the same task as the return, before any
timer or font event can run. So in practice the result is a snapshot, but the
code does not guarantee it. See nit 2.

**Retry path and FAIL reporting.** Unchanged for genuinely missing fonts. An
unanswered family stays `[0,0]`, so `settle_free_fonts` (`:215-233`) retries it
and `free_font_failures` (`:189-212`) reports it. Test 5 pins this with the
real browser: `retried == [['Hang One'], ['Hang One']]` and the failure line
`family Hang One resolved no loaded face from Google Fonts`. When all families
are unanswered the existing "none of the N library families produced a face"
message is used. That is the right text, because a stalled font network is the
likely cause.

**Worst-case time per gate run.** The free-fonts check costs at most
15 s (first measure) + (1 s pause + 30 s status wait + 15 s measure) +
(3 s pause + 30 s status wait + 15 s measure) = about 109 s per run. The gate
runs this check once per online run. CI has `timeout-minutes: 30`
(`.github/workflows/quality-gate.yml`), so this is well inside it. The
deadline of 15 s is generous against the 8 s at which Studio itself reports
"Still waiting".

**Is the faulthandler watchdog cancelled? Verified concretely.**
`setUp` arms `faulthandler.dump_traceback_later(30, exit=True)` and registers
`addCleanup(faulthandler.cancel_dump_traceback_later)` on the next line
(`tests/test_frontend_gate_fonts.py:55-56`). Cleanups run even when the test
fails or errors. Because `addCleanup` is LIFO and the cancel is registered
first, it runs last, after `browser.close`, so a hung browser close would
still be caught. Proof: I ran the module's 5 tests in a process, then slept
35 s in the same process. The process printed
`tests done ok= True` then `SURVIVED 35s after tests: watchdog cancelled`.
An uncancelled watchdog would have exited the process at 30 s. Each test also
finishes in well under 30 s, so the watchdog cannot fire on a healthy run
(5 tests in 3.5 s).

## Test quality (AGENTS.md rules)

Mutation checks, run through a scratch script that patched
`FONT_FACES_JS` in memory (repo files untouched):

- Race removed (`await measure()` only): the run hit
  `Timeout (0:00:30)!` and the watchdog exited the process with a stack dump.
  The tests do fail loudly if the deadline is removed. They are not vacuous.
- Per-family serial deadlines instead of one shared deadline: `FAIL:
  test_the_deadline_is_shared_not_spent_per_family`.
- No `[0, 0]` pre-fill (unresolved families omitted): 4 failures (tests 1, 2,
  3 and 5).

Other rules:

- Hostile case and real browser: all five tests run the real page in a real
  browser with a stalled promise. No fake counterpart. Right level for the
  claim.
- Rendered result asserted, not just that a call happened: results are compared
  with `assertEqual` on the exact dict.
- No new fixed sleeps. The retry test passes `lambda ms: None` for `pause`.
  Timing is measured with `time.monotonic`, not waited on.
- Engines come from `support.ENGINES` and `launch` (`:17`, `:50`). Each page
  test closes its browser through `addCleanup(browser.close)`, and the
  Playwright runtime is stopped in `tearDownClass`. No servers are started.
- Timing bounds: `BOUND_S = 5` against a 300 ms deadline is safe. The
  shared-deadline bound is `0.3 s * 4 = 1.2 s` for eight stalled families,
  which separates 0.3 s (shared) from 2.4 s (serial) with 4x headroom. It could
  flake on a badly loaded runner. See nit 3.

## Style

Matches the surrounding module: constants with a "why" comment, a thin
wrapper, tests in the repo's `unittest` + `support` pattern. The new
`measure_font_faces` signature line is 105 characters, equal to the existing
`settle_free_fonts` signature, so no new line-length precedent. The comments
explain why (the status wait does not bound the evaluate; all loads together
so one stalled family cannot hide others). The report section is accurate. It
says honestly that the online gate was not run, and the reproduction claim
(300 s with no deadline) is consistent with the 30 s watchdog result I got.

## Nits (optional, not blocking)

1. `FONT_FACES_JS` handles a hung promise but not a throw from
   `await document.fonts.ready` or a missing `document.fonts`. Both raise out
   of `evaluate` instead of returning missing counts. A `try/catch` inside
   `measure()` (or around the `race`) would make "return missing counts for
   unresolved families" total. Real browsers do not do this and the failure is
   not silent (it becomes a FAIL line), so leaving it is acceptable.
2. Make the snapshot explicit: `return JSON.parse(JSON.stringify(results))`
   or build a fresh object at the end. It costs one line and removes the need
   to reason about the late-mutation timing above.
3. The `* 4` bound in
   `test_the_deadline_is_shared_not_spent_per_family` could be widened (for
   example `DEADLINE_MS / 1000 * 6`, still under the 2.4 s serial figure only
   if the deadline stays at 300 ms) to reduce flake risk on a slow runner. Only
   worth doing if it ever flakes.
4. The report could state the ~109 s worst case so the next reader does not
   have to derive it.

## Round 2 (scoped re-review of nits 1-3 and the worst-case note)

Verdict: **Approved**. Nothing blocking. Engine: Chromium only.

Gate evidence:

- `python -m unittest tests.test_frontend_gate_fonts tests.test_frontend_gate_helpers tests.test_frontend_gate_report tests.test_frontend_gate_runner`:
  `Ran 158 tests in 4.866s` / `OK`. The new module runs 6 tests, all `ok`,
  including `test_a_rejected_ready_or_a_missing_fonts_api_leaves_every_family_missing`
  (two cases: rejected `ready`, `document.fonts` undefined).
- `python scripts/dev/frontend_gate.py --offline --engines chromium`:
  `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines, 0 FAIL lines`.
- Not re-run: static verify (no change to anything it checks). The online
  free-fonts check still cannot run here.

What changed, checked:

- Nit 1: an outer `catch` around the race (`_frontend_gate_network.py`, in
  `FONT_FACES_JS`) leaves results at `[0, 0]`. Mutation: removing the catch
  makes both new sub-cases `ERROR` (evaluate raises). The test is not vacuous.
- Nit 2: the return is a fresh copy built with `Object.fromEntries`. Mutation:
  returning `results` directly still passes all 6 tests. The copy cannot be
  pinned by a test, because a late write lands after Playwright has already
  serialized the value (shown in round 1). It is cheap hardening, so keep it,
  but it is untested by design. Not a defect.
- Nit 3: the shared-deadline bound is now `DEADLINE_MS / 1000 * 6` = 1.8 s. The
  serial mutant (eight sequential 300 ms deadlines, about 2.4 s) still fails
  `test_the_deadline_is_shared_not_spent_per_family`, so the wider bound still
  discriminates. The margin against serial is 0.6 s; if this test is ever
  loosened further it would stop telling the two apart.
- Report section: the "Hardening" and "Worst case" bullets are accurate
  (3 measurements x 15 s + 2 x 30 s + 1 s + 3 s = 109 s). The new test is not
  listed in the "Tests" bullet, which is a minor omission.

Concern probed: does the catch hide a JS bug as "Google Fonts unreachable"?

- Yes, in part. I put a typo before the loads (`document.fonts.reayd`). The
  gate then gets `{'A': [0,0], 'B': [0,0]}` and `free_font_failures` says
  "none of the 2 library families produced a face; Google Fonts is probably
  unreachable ... (rerun with --offline ...)". That is a misleading cause.
- It is not new in kind. The original code already caught every error inside
  the per-family loop and recorded `[0, 0]`, so a typo in the load call, or in
  `faces.filter`, was swallowed the same way and reported with the same
  message. The outer catch only adds the code before the loop (`ready`,
  `document.fonts`, the `map` call).
- Acceptable, for three reasons. The FAIL line still fires, so the gate cannot
  pass on a broken measurement. The unit tests catch such a bug first:
  `test_a_load_that_never_answers_is_missing_and_the_others_still_report`
  expects `Inter` and `Fraunces` to come back `[1, 1]` from a stubbed answering
  `load`, and a typo anywhere in the measure path turns those into `[0, 0]`.
  And the catch is limited to the cases the coordinator and Copilot asked for.
- Optional improvement, not required: have the in-page catch return the error
  text (for example under a reserved key) so the FAIL line can say "measurement
  threw: ..." instead of blaming the network. Skip it unless a real
  false-attribution shows up.
