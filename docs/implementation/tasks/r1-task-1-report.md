# R1.1 report: package skeleton

Mode: serial. Base 75f2c20. Commits: 60411ac `feat(dev): add the fontkitstudio package
skeleton`, 4a1f5f0 `test(dev): accept a CRLF shebang in the package test`. Recorded by the
controller from the implementer's reply (the implementer did not write this file).

## What changed

`packages/fontkitstudio/` with `package.json` (0.2.1, ESM, bin, engines `>=22.12`, files
`bin/ src/ dist/`, test script), `README.md`, `bin/fontkitstudio.js`, `src/cli.js`,
`test/package.test.js`, `test/cli.test.js`; a `node-package` job in
`.github/workflows/quality-gate.yml` (Ubuntu Node 22/24/26, macOS and Windows Node 24).
Bookkeeping: one progress.md event; R1.1 ticked in the R1 plan.

## Evidence

- RED: before the bin existed, the package test failed with ENOENT on `bin/fontkitstudio.js`.
- GREEN: 6 of 6 Node tests pass on Node 24; `--version` prints `0.2.1`.
- Dependency guard bites: adding `dependencies` failed with "dependencies must stay empty".
- Import guard bites: `import 'left-pad'` failed with "imports left-pad: only node:* and
  relative imports are allowed".
- Workflow YAML parsed with PyYAML: jobs `quality-gate` and `node-package`.

## Gates (Chromium; Windows 11 local)

- static PASS; bridge-syntax PASS; node-package PASS (`fail 0`); commit-messages PASS
  ("OK: 2 commits checked").
- suite-a, suite-b and the frontend gate do not apply to this diff (constraints `when:`),
  but ran before that rule arrived:
  - suite-a: 416 tests, 4 failures and 2 errors (`test_preview_server`: 3 failures, 2
    errors including a charmap decode error and "Unsupported signal: 2";
    `test_live_integration.test_copy_uses_the_real_clipboard`: `\r\n` vs `\n`). Not
    checked on the base commit by the implementer.
  - suite-b: 372 tests OK.
  - frontend gate: failed with a Playwright `Browser.removeBrowserContext` protocol
    error on a Firefox run.
- pre-commit: not installed here; not run.

## Deviations

- The shebang assertion accepts `\r?\n` (second commit): on Windows, autocrlf checks the
  bin out with CRLF, and the strict check would fail the Windows CI job.

## Concerns

- Node 24's reporter prints `ℹ fail 0`, not `# fail 0`; the gate's quote line was wrong.
- A CRLF shebang in a tarball packed on Windows would break the bin on Linux and macOS
  (`env: node\r`); the publish job must run on Linux, or the package must be checked out
  with LF (follow-up for R1.2b: `.gitattributes`).
