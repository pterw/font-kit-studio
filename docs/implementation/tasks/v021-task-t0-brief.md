# v0.2.1 Task T0 brief: one test browser per engine per process

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task T0, addendum 4) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md` (ownership, contract). Implementer: Ligature.
Base: `e3e07ef`.

## Problem

`LiveCase` (`tests/test_studio_live.py`), `LiveIntegrationCase`
(`tests/test_live_integration.py`) and `BrowserCase` (`tests/test_font_kit_studio_v011.py`)
start a Playwright driver and launch a browser in every test's `setUp`, then close both.
About 44 test classes inherit from them. Launch costs about 0.5 s per test in Chromium here.

## Required

- `tests/support.py` keeps one driver and one browser per engine for the process, launched
  on first use and closed at interpreter exit. Each test gets a fresh `new_context()`,
  closed in `tearDown`, so cookies, storage and permissions stay isolated per test.
- The harness API does not change (binding): `self.context(engine, ...)`,
  `route_virtual_origins`, `launch` and every helper keep names, arguments and return
  values. No test body changes.
- Before changing anything, list every test that needs a fresh browser (closes the browser,
  launches with special options, relies on process-wide state). Known special launches:
  `tests/test_studio_live.py` near 638 and 2658, `tests/test_live_integration.py` near 1041
  and 1699, `tests/test_font_kit_studio_v011.py` near 98. Keep those on their own launch.
- A crash in one test must not poison the shared browser for the rest: if the shared
  browser is disconnected, the next test relaunches it.

## Tests

- In `tests/test_support.py`: two consecutive tests share the browser but not the context
  (storage set in one is absent in the next); a disconnected shared browser is replaced.
- Evidence: the touched modules before and after (same count, all pass) with wall time,
  run sequentially in the worktree.

## Owned files

`tests/support.py`; the browser setup and teardown of the three base classes;
`tests/test_support.py`. Nothing else.

## Implementer report

Implementer: Ligature. Worktree at base `e3e07ef`. Nothing committed. Engine: chromium only
(`FKS_ENGINES=chromium`, `FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`). Firefox and WebKit
were not available and were not run.

### Survey (`grep -n "sync_playwright\|launch(" tests/*.py`)

Per-test base classes (driver and browser started per test; now shared, fresh context per test):
- `LiveCase` setUp, tearDown and `context()` in `tests/test_studio_live.py` (about 30 subclasses, including `ArrangeCase`, `ImportLinkCase` and the classes in `test_studio_first_run.py`, `test_studio_import_link.py`, `test_studio_review_findings.py`, `test_studio_stage.py`).
- `LiveIntegrationCase` setUp, `open()` and `close_browsers` in `tests/test_live_integration.py` (also used by `test_studio_first_run.py`, `test_studio_import_link.py`, `test_studio_review_findings.py`).
- `BrowserCase` setUp, tearDown and `page()` in `tests/test_font_kit_studio_v011.py`.

Special launches inside tests (kept as their own `launch(self.runtime, engine)`, closed through `self.browsers`):
- `test_studio_live.py`: `test_sync_disabled_under_file_url` (about 638) and `test_the_selector_check_itself_is_fast_on_500_character_inputs` (about 2658).
- `test_live_integration.py`: `InteractModeTests.test_the_instrumented_app_works_normally_without_studio` (about 1041) and `OpenedFromFileTests.test_studio_opened_as_a_file_edits_a_served_target_but_cannot_sync` (about 1699).
- `test_font_kit_studio_v011.py`: `test_task5_offline_layouts_and_dynamic_ids` (about 98).
- All five are plain `launch(self.runtime, engine)` followed by `browser.new_page()`: no special options, no process-wide state.

setUpClass or own-driver sites outside the three base classes (own launches kept; only the driver changed, see "Deviation"):
- `test_bridge_runtime.py:56` `BridgeCase.setUpClass` (class-level driver, one browser per engine for the class).
- `test_frontend_gate_fonts.py:46` `FontMeasurementDeadlineTest.setUpClass`.
- `test_frontend_gate_theme_browser.py:32` `InPageAlphaTest.setUpClass`.
- `test_preview_server.py:626` and `:642` (`with sync_playwright()` inside two `DemoPageTest` tests).
- `test_frontend_gate_runner.py:414` only defines a fake `launch`; no Playwright.

### Before and after

Command: `PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python -m unittest test_studio_live test_live_integration test_font_kit_studio_v011 test_studio_first_run test_studio_import_link test_studio_review_findings test_studio_stage`, sequential, in this worktree.

- Before: `Ran 286 tests in 630.843s`, OK. Load average was 5.7 on 4 CPUs at the end, so other agents were running and the time is inflated. The log also had one `Task was destroyed but it is pending` / `TargetClosedError` noise block from the per-test driver stop.
- After: `Ran 286 tests in 403.532s`, OK. Load average 3.8 at the start, 1.6 at the end. The noise block is gone. Both runs shared the CPUs, so treat the ratio (about 36 percent less) as indicative, not exact.
- Whole suite after: `python -m unittest discover -s tests` gives `Ran 644 tests in 587.814s`, OK (includes 8 new tests in `test_support.py`).
- `python -m unittest test_support`: `Ran 14 tests`, OK (includes the Firefox canary loader check, `CanaryListTest`).
- `python scripts/verify.py --static-only`: PASS (provenance included).
- Order independence: `python -m unittest test_studio_stage test_bridge_runtime test_frontend_gate_fonts test_frontend_gate_theme_browser` gives 147 tests, OK.

### RED and GREEN

RED (new tests in `tests/test_support.py`, harness unchanged): `Ran 14 tests`, `FAILED (failures=6, errors=2)`.
- The three "share the browser but not the context" tests failed with `AssertionError: <Browser ...> is not <Browser ...> : the browser is shared between tests`.
- The three "disconnected browser is replaced" tests failed because the old tearDown raised when the test had closed the browser.
- `test_support_hands_out_a_working_browser_after_the_shared_one_disconnects` and `test_an_explicit_launch_is_still_a_separate_browser` errored with `AttributeError: module 'support' has no attribute 'shared_browser'`.

GREEN: after the implementation `Ran 14 tests ... OK`.

The probes run two consecutive tests of the real base class (`LiveCase`, `BrowserCase`, `LiveIntegrationCase`). Test 1 sets localStorage (and a cookie where the page is http) and records the browser and context. Test 2 asserts the same browser object, a different context, the first context gone from `browser.contexts`, and storage and cookie absent. The "disconnected" variant closes the browser between the two tests and asserts the second test gets a different, connected browser.

### Mutation

Temporarily changed `support.new_context` to cache and return one context per (browser, options) and `close_contexts` to close nothing. The three isolation tests failed (`AssertionError: unexpectedly identical: <BrowserContext ...>`), one per base class. With a cruder first mutation (cache not keyed by browser) all six harness tests failed. `support.py` was restored from a backup; `git diff --stat tests/support.py` shows only the 59 added lines, and `test_support` is 14 of 14 OK again.

### Implementation summary

`tests/support.py` gained `shared_runtime()` (one driver, lazy, stopped at exit), `shared_browser(engine)` (one browser per engine, relaunched if `is_connected()` is false), `new_context(engine, **options)`, `close_contexts(list)` (tolerates a context whose browser already went away, re-raises otherwise) and an `atexit` close. `launch`, `route_virtual_origins`, `ENGINES` and every existing helper keep their signatures. The base classes keep `self.runtime`, `self.browsers`, `context()`, `open()` and `page()`, and add `self.contexts`. No test body changed.

### Deviation (outside the owned files, needs the controller's call)

A live shared driver blocks any second `sync_playwright()` in the same process (`Error: It looks like you are using Playwright Sync API inside the asyncio loop`). The first full-suite run showed 4 errors from this: `test_frontend_gate_fonts.FontMeasurementDeadlineTest` and `test_frontend_gate_theme_browser.InPageAlphaTest` (setUpClass), and the two `test_preview_server.DemoPageTest` demo tests. `test_bridge_runtime.BridgeCase` passed only because it sorts first, so the suite would have depended on module order. I changed the driver line only, in five sites: `tests/test_bridge_runtime.py`, `tests/test_frontend_gate_fonts.py`, `tests/test_frontend_gate_theme_browser.py` and `tests/test_preview_server.py` (two tests; `with nullcontext(shared_runtime()) as runtime:` keeps the body indentation). Their own `launch()` calls and browsers stay. If the controller wants these out of the T0 diff, the only alternative is that no other module may start its own driver in the same process, which is not workable.

### Kept special launches and why

The five in-test `launch(self.runtime, engine)` calls listed above stay as the brief says. They are closed through `self.browsers` in tearDown. `launch(shared_runtime(), engine)` is how a test gets its own browser; `test_an_explicit_launch_is_still_a_separate_browser` pins that closing it leaves the shared browser up. The `BridgeCase`, fonts, theme and preview-server launches also stay own launches.

### Not verified

- Firefox and WebKit (not installed; the Firefox canary itself was not run, only its loader check).
- `scripts/dev/frontend_gate.py`, `check_commit_messages.py` and `node --check` were not run (not touched by this change).
- A real browser process crash (SIGKILL) was not simulated; the disconnect is simulated with `browser.close()`, which `is_connected()` reports the same way.
- Timing numbers are from a shared 4-CPU box with other agents running.

### Final `git diff --stat`

```
 tests/support.py                          |  59 +++++++++++++++
 tests/test_bridge_runtime.py              |   7 +-
 tests/test_font_kit_studio_v011.py        |  23 +++---
 tests/test_frontend_gate_fonts.py         |   9 +--
 tests/test_frontend_gate_theme_browser.py |   9 +--
 tests/test_live_integration.py            |  22 +++---
 tests/test_preview_server.py              |  10 +--
 tests/test_studio_live.py                 |  23 +++---
 tests/test_support.py                     | 115 ++++++++++++++++++++++++++++++
 9 files changed, 221 insertions(+), 56 deletions(-)
```

The brief copy `docs/implementation/tasks/v021-task-t0-brief.md` is new and untracked in this worktree.

## Fix round 1

Review: `docs/implementation/tasks/v021-task-t0-review.md` (Approved with fixes). Only
`tests/support.py` and `tests/test_support.py` changed.

- Finding 1: `CloseContextsTest` uses stub contexts and browsers. A close error on a disconnected
  browser is swallowed; on a connected browser it is raised.
- Finding 2: `close_contexts` now closes every context, clears the list, and raises the first
  real error at the end. A swallowed error does not hide a later real one.
- Finding 3: `new_context` replaces the cached browser (closing it best effort) and retries once
  when the first attempt raises; a second failure propagates. `NewContextRetryTest` covers the
  stale-browser retry, no second retry, and no relaunch of a healthy browser, using stub
  browsers (no real SIGKILL needed).
- Finding 4: header note in `tests/support.py`: take the driver from `shared_runtime()`, never
  call `sync_playwright()` directly.

RED (before the implementation, 7 new tests): 3 failed, 4 passed (characterization of the
existing swallow/raise branches). GREEN: `test_support` 21 tests OK.

Mutations (all caught): swallow every error (3 fail); never swallow (2 fail); no retry in
`new_context` (2 fail); do not clear the list (2 fail).

Gates: `test_support -v` 21 OK; `test_support test_font_kit_studio_v011 test_studio_stage
test_studio_review_findings` 64 OK; `StudioDefectTests`, `EditAndCodePanelTests`,
`InteractModeTests`, `OpenedFromFileTests` 8 OK; `verify.py --static-only` pass. Full suite not
run, as instructed. Not verified: real SIGKILL recovery through the retry path (stubs only),
Firefox, WebKit.

## Fix round 2

Finding 5 (retry too broad). Only `tests/support.py` and `tests/test_support.py` changed.

- `new_context` now retries only on a `playwright.sync_api.Error` when the browser is no longer
  connected or the message says "closed". Anything else (a `TypeError` from a bad option, an
  invalid-viewport `Error` on a live browser) propagates at once: no relaunch, the healthy
  browser and the test's earlier contexts stay up, and the error is not chained. The retry runs
  outside the `except` block, so a second failure is not chained to the first either.
- Existing retry tests stay green; their stub errors became `playwright.sync_api.Error` with a
  "closed" message, because a bare `RuntimeError` is by design no longer a crash signal.
- New: `test_an_error_that_is_not_a_crash_propagates_without_a_relaunch` (TypeError and a
  non-closed Playwright Error on a connected stub browser: `launch` not called, same error object,
  `__context__` None, browser not closed, one attempt) and
  `test_a_playwright_error_on_a_browser_that_is_gone_retries_whatever_it_says`.

RED before the change: the new propagate test failed for both error kinds; the "gone" test passed
(characterization). GREEN: `test_support -v` 23 tests OK. Mutations (both caught): retry on any
Playwright error (propagate test fails, Error case); retry on any exception (fails, both cases).
`verify.py --static-only` passes. Not verified: real SIGKILL through the retry branch, full suite,
Firefox, WebKit.
