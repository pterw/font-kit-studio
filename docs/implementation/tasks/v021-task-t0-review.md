# v0.2.1 Task T0 review: one test browser per engine per process

Reviewer: Leading. Reviewed the uncommitted worktree diff on base `e3e07ef`.
Date: 2026-10-03.

Verdict: **Approved with fixes.** No blocking defect. The deviation is accepted.

## Deviation: driver line in five other sites

Accepted. A live `sync_playwright().start()` makes a second `sync_playwright()` in the
same process raise ("Sync API inside the asyncio loop"); after `.stop()` a new one works.
Only the driver line changed, at `tests/test_bridge_runtime.py:54`,
`tests/test_frontend_gate_fonts.py:45`, `tests/test_frontend_gate_theme_browser.py:31` and
two tests in `tests/test_preview_server.py`. Each keeps its own `launch()` and browser.
`nullcontext.__exit__` does nothing, so leaving the `with` does not stop the shared driver;
the `atexit` hook owns the stop.

## Checks

- Isolation is real. `route_virtual_origins` and `LiveCase.context` route on the context.
  Test routes, `add_init_script`, `grant_permissions`, downloads, cookies, storage and
  service workers all live on the context. Every direct `browser.new_page()` uses a
  browser the test launched itself. No test body closes the shared browser. The one
  clipboard test writes before it reads.
- Recovery works for `browser.close()` (tested) and for a real SIGKILL (probed three times):
  the crashed test's tearDown swallows `TargetClosedError`, `is_connected()` then reads
  False, and the next test relaunches.
- API unchanged: only setUp, tearDown, `context()`, `page()`, `open()` and
  `close_browsers` of the three base classes changed; no test body changed.
- Order and exit: a reordered run (preview server first) gave 153 tests OK in 146 s with no
  "Task was destroyed", `TargetClosedError` or traceback lines, and no browser left behind.

## Findings

1. **Low-Medium, test quality.** The tolerance branch of `close_contexts` is untested.
   Swallowing every error and never swallowing both leave all 8 `SharedBrowserTest` tests
   green, because `browser.close()` makes a later `context.close()` succeed. A real SIGKILL
   makes it raise. Fix: a test with a stub context whose `close()` raises, against a stub
   browser that reports connected and not connected.
2. **Low.** `close_contexts` stops at the first context that raises on a connected browser,
   so later contexts stay open and the list is not cleared. Fix: keep closing, raise the
   first error at the end.
3. **Low, informational.** After a SIGKILL, `is_connected()` stays True until Playwright
   dispatches the event. In unittest the crashed test's tearDown always runs first, so
   recovery works. Optional hardening: retry `new_context` once after a relaunch.
4. **Info.** `shared_runtime()` is now load-bearing: a new module that calls
   `sync_playwright()` directly errors whenever the shared driver is live, depending on
   module order. Document it in the `tests/support.py` header and in AGENTS.md.
   No other `sync_playwright` use remains in `tests/`.

## Mutations

| Mutation | Result |
|---|---|
| `shared_browser` never relaunches | 8 of 8 fail, caught |
| `close_contexts` closes nothing | 3 isolation tests fail, caught |
| New browser on every `shared_browser` call | 4 fail, caught |
| `LiveCase.context()` reuses one class-wide context | 2 fail, caught |
| `close_contexts` swallows every error | 8 of 8 pass, survived (finding 1) |
| `close_contexts` never swallows | 8 of 8 pass, survived (finding 1) |

## Gates

- `python scripts/verify.py --static-only`: pass. `node --check fontkit-bridge.js`: ok.
- `python -m unittest test_support -v`: 14 tests OK in 7.6 s.
- `python -m unittest discover -s tests -v`: 644 tests OK in 577 s (load 2.2 to 3.0 on
  4 CPUs, with another reviewer running). Before T0 the suite took about 746 s on a
  quieter box.

Not verified: Firefox and WebKit (not installed; the new tests run on Chromium only), the
frontend gate, a crash of the Playwright driver itself, and timing on a quiet box.

## Re-review of fix round 1 (2026-10-03)

Verdict: **Approved.** Findings 1 to 4 are resolved. The two surviving mutations now fail
(swallow everything: 3 fail; never swallow: 2 fail). Retry mutations are caught too: a
second failure swallowed, and a second retry, each fail
`test_a_second_failure_is_raised_not_retried_again`. `test_support`: 21 tests OK;
`test_font_kit_studio_v011 test_studio_stage`: 31 tests OK.

5. **Low, from the fix.** The `new_context` retry fires on any first failure. With a bad
   option (`bogus_option=1`) on a live shared browser, the healthy browser is closed and
   relaunched, the same `TypeError` is raised twice in a chained traceback, and a context
   the test made earlier dies with it. A second failure always propagates, so nothing is
   masked. Narrowing: retry only on a Playwright error that means the browser or target is
   closed. Controller ruling: narrow it, with a test that a non-crash error does not
   relaunch.

Not verified: the full suite, Firefox and WebKit, a real SIGKILL through the retry branch.

## Re-review of fix round 2 (2026-10-03)

Verdict: **Approved.** Finding 5 is resolved; only `new_context` in `tests/support.py` and
its tests changed. Against a live shared Chromium with a context already open,
`new_context('chromium', bogus_option=1)` raised the `TypeError` at once, unchained, with
no relaunch, and the earlier page stayed alive. A real SIGKILL with no tearDown in between
(stale `is_connected()`) recovered through the retry with one relaunch. `test_support`:
23 tests OK. Mutations caught: retry on any Playwright error; drop the "closed" check.

Remark (not blocking): the "closed" substring is a heuristic; a non-crash Playwright error
whose text says "closed" relaunches once, and a second failure still propagates.
