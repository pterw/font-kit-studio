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
