# R2.7Ia report: React fixture in hosted CI

Implemented by the controller at BASE `deb3636c1f369c83af817b911af26786a923d09c` on
`feat/r2-role-adapters`. Brief: `r2-task-7ia-brief.md`.

## Change

`.github/workflows/quality-gate.yml` (+16 lines), job `quality-gate`, directly after
`Run tests (Chromium, blocking)`:

- `Install the React CSS-module fixture`: `npm ci --prefix fixtures/vite-react-css-modules`.
- `React CSS-module fixture tests (blocking, never skipped here)`: `python -m unittest test_r2_react -v`
  with `FKS_ENGINES=chromium`, `FKS_REQUIRE_FIXTURES=1` and `PYTHONPATH=tests`.

Both run `if: ${{ !cancelled() }}` without `continue-on-error`. No other step, install or test changed.

## Evidence (local, Windows, Chromium)

- Parse: `yaml.safe_load` places the steps in order: `Run tests (Chromium, blocking)`,
  `Install the React CSS-module fixture`, `React CSS-module fixture tests (blocking, never skipped here)`,
  `Prepare the localhost cookie fixture`; the new step's env is exactly the three variables above.
- Node line: the job sets up Node 22; the fixture's Vite 8.3.2 requires `^20.19.0 || >=22.12.0`.
- `test_release` (parses every workflow) and `test_r2_react`, with `FKS_REQUIRE_FIXTURES=1`:
  `Ran 30 tests in 13.932s`, `OK`.
- `test_r2_react` alone in a scratch worktree with linked fixtures: `Ran 5 tests in 13.671s`, `OK`, no
  skips.
- `pre-commit run --files .github/workflows/quality-gate.yml`: the whitespace hook passes; the others
  have no files to check. `git diff --check`: exit 0.
- Before the change, hosted CI run 38989714639 (`2845822`) skipped 16 tests in the suite step:
  `test_r2_react` 4, `test_one_command_vite` 4, `test_vite_build_guarantee` 2, `test_vite_types` 2,
  `test_friction`, `test_localhost_cookies`, `test_one_command_messages` and `test_one_command_next`
  1 each.

## Not verifiable locally

GitHub Actions does not run locally. The first exact-head CI run must show `Ran 5 tests` and `OK` in
job `quality-gate`'s new step, with the same 16 suite skips; that is recorded at the landing.

## Controller integration

- Review: Approved, no Critical or Important findings. Minor 1 applied at landing: the step comment now
  says the four fixture cases run only once (the install-contract case also runs in the suite step).
  Minor 2 concerned only the review package's line endings; the landed change is unaffected.
- Landing checks on the final workflow, Windows: `test_release` and `test_r2_react` with
  `FKS_REQUIRE_FIXTURES=1`, the whitespace hook and `git diff --check`. Exact-head hosted CI is recorded
  with the first push of this wave.
