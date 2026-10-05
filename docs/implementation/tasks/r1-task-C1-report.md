# C1 code report (mode: code, BASE 7376bd2, worktree C:/fks/tC1)

Patch: `.superpowers/sdd/r1-pr-b/task-C1-code.patch` (4 files, LF, `git apply --check -R` OK).
Files: `packages/fontkitstudio/src/run-vite.js`, `test/run-vite.test.js`, `test/cli.test.js`, `tests/test_one_command_vite.py`.

## Change
`runVite` now calls `process.chdir(projectDir)` before `vite.createServer` (comment says why) and passes no inline `root`,
so Vite finds the config there and resolves the config's own `root` against the working directory, as `vite` does.
Nothing else in runVite changed.

## RED / GREEN
- New test `test_a_config_root_below_the_project_folder_is_served` (temp project `fixtures/vite-react/.fks-*`, git-ignored, removed in a
  cleanup; config `root: 'app'` with `fontkitStudio()`; fetches the `target` of the Open: line).
- RED on the current code: `urllib.error.HTTPError: HTTP Error 404: Not Found`.
- GREEN after the fix: the test passes (body has `Root marker`, exactly one `/@fontkit/fontkit-bridge.js`).

## Side effect handled in tests (not in the product)
`process.chdir` inside the in-process Node tests left the process in a temp folder that the test then removed (EPERM on Windows;
3 failures first run). The Vite-runner tests in `run-vite.test.js` and `cli.test.js` now restore the starting directory before removing
the folder. The command itself is a one-shot process, so no restore is added in `runVite` (per the ruling).

## Gates (final tree)
- `npm --prefix packages/fontkitstudio test`: tests 199, pass 197, fail 0, skipped 2.
- `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_vite test_one_command_proxy test_vite_build_guarantee test_support`: Ran 41 tests, OK
  (both fixtures plus the new test; I ran `npm ci` for vite-react and vite7-react in the worktree).
- `python -m ruff check .`: all checks passed. pre-commit: not run (no config in the repo).
- No `.fks-*` folder is left; no process left running (the test stops its own command and checks both ports).

## Handoff
Commit subject: `fix(dev): keep the Vite config's own root when the command starts Vite`
Why-body: The command passed `root: projectDir` to Vite's createServer; inline config wins the merge, so a project whose
vite.config sets `root` (an app below the package.json folder) served the project folder instead. Starting Vite from the project folder, as
`vite` does, lets the config find itself and resolve its own root. A browser test runs the command on such a project.
progress.md line: `R1.4d fix (Codex P2): the command starts Vite from the project folder so a config's own root is honoured.`


## Landing (controller, 2026-10-04)

Review (`r1-task-C1-review.md`): Approved; its plan-mandated minor fixed at landing as the same class of bug (anti-pattern 12): `runVite` changed to the folder it was given, which is the folder the command runs in, not the project `loadVite` found above it, so a command run in a subfolder served the subfolder (404). It now changes to the discovered project folder, as Codex's finding asks. Test first: a project with `index.html` at its top, run from an empty `src/` subfolder, answered 404 before the fix and serves the page with one bridge tag after. The new tests read the target with a 15 s timeout. `test_one_command_vite` 4 OK with `test_support`; Node tests 204 run, 202 pass, 2 skipped; ruff clean.
