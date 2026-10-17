# R2.7Ia brief: React fixture in hosted CI

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.7Ia (Addendum 16 item 3; placement settled by
Addendum 17). Owner: the controller. BASE: `deb3636c1f369c83af817b911af26786a923d09c`.

## Why

Hosted CI skipped `tests/test_r2_react.py`'s four corpus cases, because no job installed
`fixtures/vite-react-css-modules`. A Vite change-coalescing race in its hot-update test stayed hidden
until a local settled wave. PR B2 adds React role cases to this module (R2.7F2b), so they must block on
hosted CI before they are written.

## Change

Only `.github/workflows/quality-gate.yml`, job `quality-gate`, after the step
`Run tests (Chromium, blocking)`:

1. `Install the React CSS-module fixture`: `npm ci --prefix fixtures/vite-react-css-modules`.
2. `React CSS-module fixture tests (blocking, never skipped here)`: `python -m unittest test_r2_react -v`
   with `FKS_ENGINES=chromium`, `FKS_REQUIRE_FIXTURES=1`, `PYTHONPATH=tests`.
3. Both steps carry `if: ${{ !cancelled() }}`, like the steps around them; neither has
   `continue-on-error`, so a failure fails the blocking job.

Every existing install, step and test stays as it is.

## Placement

The plan names two places: Addendum 16 item 3 says "the Vite matrix", task R2.7Ia says "the job that runs
the Chromium suite". Addendum 17 settles it for this job, because:

- `FKS_REQUIRE_FIXTURES=1` cannot be set on the suite step: the other fixtures are not installed there,
  so their 12 other disclosed skips would become failures. A dedicated step after the suite keeps the
  suite unchanged and runs the module once.
- This job's log is the one read for test counts after each push, so the five cases show there.
- Running a hot-update timing test on hosted macOS and Windows on every push would add flake risk to a
  blocking check; local Windows settled waves cover Windows.
- The matrix install with the entry-point cases stays in R2.7I (PR C).

## Acceptance

- The workflow parses; the two steps sit between the suite and the cookie-fixture step.
- Locally: `test_release` (parses the workflows) and `test_r2_react` with `FKS_REQUIRE_FIXTURES=1` pass;
  pre-commit passes on the file.
- Exact-head hosted CI: the new step reports `Ran 5 tests` and OK in job `quality-gate`; the suite step's
  skip names are recorded (the four corpus cases stay among them, since the suite runs first).
