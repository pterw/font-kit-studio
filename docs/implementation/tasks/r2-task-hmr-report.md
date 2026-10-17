# HMR restore fix (MODE code, BASE 9895585, worktree C:/fks/t27)

Patch: `task-hmr-code.patch`, sha256 `7ed5d794e042c58a86c5fcc7b7f11ff5d0f098ca903bf830044670bedaa1d257`.
Only file touched: `tests/test_r2_react.py` (staged in t27, not committed).

Change: in `test_css_module_hot_update_changes_computed_font_without_losing_app_state` the restore of `App.module.css` now writes the
original bytes, waits up to 1 s for the computed 40px, and writes again if it has not arrived, up to 5 attempts. After 5 it fails with
"the restored CSS never hot-updated after 5 writes; last computed size <size>". A comment states the cause: Vite coalesces changes to one
file inside a short window, so an immediate second write may produce no hot update. Added import: `playwright.sync_api.TimeoutError`.
The 44px write is the first change to the file, so it cannot hit the race and is unchanged.

Verification (Chromium, FKS_REQUIRE_FIXTURES=1, PYTHONPATH=tests):
- the test: 5 of 5 runs OK.
- RED: with `range(5)` changed to `range(1)` (one immediate restore), 3 of 3 runs fail with the new message; the file was restored
  byte-exact (sha256 verified) and the fixed version passes.
- `python -m unittest test_r2_react` in full: `Ran 5 tests ... OK`.
- ruff, git diff --check (plain and cached) and pre-commit pass.
- Worktree note: the detached t27 has no fixture node_modules, so I made a temporary junction to the root checkout's
  `fixtures/vite-react-css-modules/node_modules` and removed it (rmdir, target intact) afterwards.

Sweep of the other CSS hot-update round trips (none changed):
- `tests/test_one_command_vite.py::test_vite_edits_live_and_keeps_the_edit_through_a_css_hot_update`: one write to `app.css`, restored by
  `addCleanup` after the test ends. No back-to-back pattern.
- `tests/test_one_command_next.py`: writes the changed bytes, then waits for the colour, a reload-free marker check and a second
  typed edit (several seconds) before writing the original back and waiting for the colour. Not immediate.
- `tests/test_r2_static_fixtures.py`, `tests/test_live_integration.py`, `tests/test_one_command_proxy.py`: writes are scratch setup, not watched-file round trips.

## Controller integration (2026-10-16)

The patch (`task-hmr-code.patch`, sha256 `7ed5d794...`) applies onto `9895585`. As the
review's timeout Minor asked, the controller keeps the old 10 s budget on the last of
the five writes (1 s on the earlier ones) and takes the attempt count from that list.
The test then passed 3 of 3 runs.
