# B3a code report (mode: code, BASE 401116c)

Files: fixtures/vite-react/**, fixtures/vite7-react/** (Vite 8.3.2 with rolldown 1.2.12; Vite 7.3.6
with esbuild 0.28.2), tests/fixture_support.py, tests/test_vite_build_guarantee.py,
.github/workflows/quality-gate.yml (new `fixtures` job appended after node-package), .gitignore (2 lines).
Steps 1-6 done; step 7 below. Both fixtures built by hand: JSX compiles, no errors.

## Evidence
- RED (node_modules renamed away, i.e. fixture not installed): the module SKIPS, 2 skipped:
  `skipped 'run npm ci in fixtures/vite7-react'` / `... vite-react`.
- With FKS_REQUIRE_FIXTURES=1 in the same state: FAILED (failures=2), text
  `fixtures/vite-react/node_modules is missing and FKS_REQUIRE_FIXTURES=1: run npm ci in fixtures/vite-react`
  (and vite7-react). node_modules renamed back afterwards.
- GREEN: `PYTHONPATH=tests python -m unittest test_vite_build_guarantee -v` -> 2 tests OK (2.3 s).
- Mutation (plugin edited in the worktree, restored by file copy; git status showed no plugin change):
  `apply: 'serve'` removed + transformIndexHtml returning the tag with placeholder origin
  http://127.0.0.1:1 -> FAILED (failures=2), `b'fontkit-bridge' found in index.html` on both Vite majors.
- Gates: `python -m unittest test_vite_build_guarantee test_support` -> Ran 36 tests, OK;
  `python -m ruff check .` -> All checks passed!; `npm --prefix packages/fontkitstudio test` -> ℹ pass 47, ℹ fail 0.
  `npm --prefix packages/fontkitstudio run prepack` runs fine (CI step).
- YAML checked with Python's yaml (import works here): jobs = quality-gate, node-package, fixtures.
- suite-a/suite-b not run (controller's gate-runners).

## Notes
- Positive control: some file contains `vite.hero.title`; index.html contains `<script type="module"`.
- Forbidden needle `Font Kit Studio` is absent from fixture text (App.jsx copy avoids it).
- Patch has no node_modules or dist; lockfile path strings containing "node_modules/" are normal.
- Working-tree files are LF; the repo's autocrlf prints "LF will be replaced by CRLF" warnings only.
- Anti-patterns: 14 (skip vs fail under FKS_REQUIRE_FIXTURES, shown); 13 (no servers started; subprocess
  is run to completion with timeout); 15 (no process state committed); 7/8 (scan reads real bundle,
  zero deps, no `support` import).

## Handoff
Commit subject: `test: build two Vite fixtures and prove the bridge stays out of builds`
Body: Users add fontkitStudio() to vite.config.js permanently, so `vite build` with it must ship
nothing of Font Kit Studio. Two React fixtures on Vite 8.3.2 and 7.3.6 build with the plugin
configured and the test scans every output file, with a positive control. A fixtures CI job
installs both and sets FKS_REQUIRE_FIXTURES=1 so it cannot pass by skipping.
progress.md event draft: "B3a (R1.4c): fixtures/vite-react (Vite 8.3.2) and fixtures/vite7-react
(7.3.6) added; test_vite_build_guarantee proves builds carry no trace of Studio (mutation: removing
apply:'serve' fails both); CI `fixtures` job added."
Churn (D050): fixtures/vite-react/package-lock.json 827, fixtures/vite7-react/package-lock.json 1151.
Material: 2221 total - 1978 lockfile = 243 lines incl. the 29-line CI job and copied fixture files.
Other per-file counts: tests/test_vite_build_guarantee.py 55, tests/fixture_support.py 27,
workflow +29, .gitignore +2, each fixture ~94 lines (package.json 8, config 5, index.html 12,
main.jsx 6, App.jsx 16, app.css 18).
Landing note: run `npm ci` in both fixtures before the focused tests (node_modules not in patch).


## Landing (controller, 2026-10-04)

Both review minors fixed at landing: a missing `node` now fails with "node is not on PATH; building the fixture needs it" instead of a TypeError, and the forbidden-string check uses `assertFalse(needle in data, ...)` so a failure names the file instead of dumping the bundle. `npm ci` in both fixtures, then `FKS_REQUIRE_FIXTURES=1 PYTHONPATH=tests python -m unittest test_vite_build_guarantee`: 2 tests OK.
