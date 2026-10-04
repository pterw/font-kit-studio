# H2 brief: make the six Windows-only test failures pass

Plan: `docs/plans/2026-10-04-dev-hygiene-ruff-windows.md`. Constraints:
`.superpowers/sdd/hygiene/constraints.md` (read all of it first).

## Goal

The full Python suite passes on Windows 11 (Chromium), with the same tests still passing on
Linux. Fix causes, never skip or weaken a test.

## The six failures and their causes (from a run on main, b92b129)

1. `test_preview_server.DemoPageTest.test_demo_source_is_offline`: `DEMO.read_text()` uses
   the Windows default encoding (cp1252) and fails on UTF-8 bytes (`UnicodeDecodeError ...
   0x90`). Fix: read with `encoding='utf-8'`. Also give the `Server` helper's `read_out`
   and `read_err` (and the files they read) `encoding='utf-8'`, and start the child with
   `PYTHONIOENCODING=utf-8` so serve.py's output (it prints "·" and URLs) is UTF-8 on
   every platform.
2. `PreviewServerLifecycleTest.test_prints_studio_url_and_shuts_down_cleanly`:
   `send_signal(SIGINT)` raises "Unsupported signal: 2" on Windows.
3-5. `test_browser_is_not_opened_without_the_flag`, `test_last_line_before_the_wait_is_the_url_to_open`,
   `test_open_flag_opens_the_studio_url_once`: `send_signal(SIGTERM)` on Windows is
   `TerminateProcess`, so serve.py never runs its shutdown and exits 1, not 0.
   Fix for 2-5:
   - `scripts/serve.py`: also handle `signal.SIGBREAK` when the platform has it (Windows),
     with the same handler as SIGINT and SIGTERM. One line; keep the code flat. This is the
     graceful stop Windows can deliver to a child process (Ctrl-Break).
   - `tests/test_preview_server.py`: on Windows (`os.name == 'nt'`) start the child with
     `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`, and make `stop(sig)` send
     `signal.CTRL_BREAK_EVENT` for any requested signal (say so in a comment: Windows cannot
     deliver SIGINT or SIGTERM to a child gracefully). On other platforms nothing changes.
     In `test_prints_studio_url_and_shuts_down_cleanly`, keep looping over SIGINT and
     SIGTERM on Linux; on Windows the loop exercises CTRL_BREAK twice, which is fine.
   - If `CTRL_BREAK_EVENT` cannot reach the child in this environment (no console), report
     that with the exact error instead of working around it; do not skip the tests.
6. `test_live_integration.EditAndCodePanelTests.test_copy_uses_the_real_clipboard`: the
   Windows clipboard returns `\r\n` line endings, so `navigator.clipboard.readText()`
   differs from the shown text (`\n`). Fix in the test: compare with `\r\n` replaced by `\n`
   on the clipboard text only, with a comment naming the Windows clipboard. The product's
   copied text is unchanged.

## Owns

`scripts/serve.py` (the signal registration only), `tests/test_preview_server.py` (the
`Server` helper, the encoding fix and the lifecycle tests), `tests/test_live_integration.py`
(the clipboard assertion only).

## Steps

- [ ] Run each failing test on the base and record its failure line (RED).
- [ ] Apply the fixes above.
- [ ] GREEN: `PYTHONPATH=tests python -m unittest test_preview_server -v` and the clipboard
  test; then `PYTHONPATH=tests python -m unittest test_support`.
- [ ] Show the SIGBREAK line matters: remove it, run the lifecycle tests, record the
  failure (exit code 1 or a timeout), restore it.
- [ ] Do not run the full suite or the frontend gate; gate-runners do that at landing.
- [ ] Report with a Handoff: the progress.md event text and a commit subject
  (`fix(dev): stop serve.py cleanly on Windows and make the suite pass there`) with a
  why-body.

## Report

`.superpowers/sdd/hygiene/task-h2-code-report.md`; patch `.superpowers/sdd/hygiene/task-h2-code.patch`.
