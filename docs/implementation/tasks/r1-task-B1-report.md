# B1 code report (mode: code, BASE 8bf379e, worktree C:/fks/tB1)

Files: packages/fontkitstudio/src/project.js (new), test/project.test.js (new),
test/helpers/fake-project.js (new), test/package.test.js (+1 guard test, existing untouched).
All steps 1-6 done; step 7 = this report. No package.json change, no CLI wiring.

## Evidence
- RED: `node --test test/project.test.js` before project.js existed: `ℹ fail 1` (module missing).
- GREEN: project + package tests `ℹ pass 14 / fail 0`; whole suite `npm --prefix packages/fontkitstudio test`:
  `ℹ tests 36, pass 35, fail 0, skipped 1`. `node --check` ok on the three new files.
- Mutations (each restored by editing):
  - major check removed: fails `findVite refuses Vite 6.4.0` and `9.0.0`.
  - JSON catch removed: fails `a package.json that is not JSON is a ProjectError without parser text`.
  - `await import(process.argv[2]);` appended to src/cli.js: fails `only src/project.js loads code by a
    computed path` ("cli.js has a computed import()").
- Patch: `git apply --check -R` passes.

## Deviations / notes
- The skipped test is the brief's allowed one: `C:\Users\peter\package.json` exists above the temp dir, so
  "findProjectDir with no package.json" is skipped here (`package.json above <tmpdir>`). The "false with no
  package.json" case inside the isViteProject test is guarded the same way, so on this machine the
  no-package branches are NOT exercised (AP 14: not run). They run on CI/clean machines.
- findVite reads the project's package.json (via readJson) before resolving Vite, so invalid JSON throws the
  ProjectError as the table requires (resolution alone never parses it).
- Vite package.json without a usable version falls to the untested-major message with `undefined`; not specified
  by the brief, left minimal.
- Pre-commit/Python gates not run (no Python changes, per brief).

## Self-review (anti-patterns)
Trust boundary: project package.json parser text and stack never reach the message (tested). No URL sink
(entryUrl from pathToFileURL of a resolved path). Temp dirs removed in test.after. Zero deps; only node:* imports.
AP 13: no processes started. AP 14: reported skip above. AP 15: none.

## Handoff
progress.md event draft: "R1.4a (B1): src/project.js finds the project folder, detects a Vite project and loads
the project's own Vite (7 and 8 only, D043); the computed import lives only there and package.test.js guards it."
Commit subject: `feat(dev): find and check the project's own Vite`
Body: The command must use the project's own Vite, not a bundled one (D030), so
project.js resolves it from the project folder and loads it. Untested majors
are refused with a message naming 7 and 8 (D043). One file holds the computed
import so the import guard keeps meaning something.
(No attribution lines.)


## Landing (controller, 2026-10-04)

Review minors 1 and 2 fixed at landing: the bare-folder `isViteProject` case is its own test and reports a skip where a `package.json` sits above the temp dir (it was silently skipped inside a passing test); a Vite `package.json` with no `version` now gives "Font Kit Studio cannot read the version of Vite in <folder>. Run npm install there, then try again." instead of "Vite undefined" (new test; removing the check fails it). Minor 4 (the guard regex misses `import (x)` with a space) is the brief's regex and stays. Node tests on Windows: project.test.js 11 pass, 2 skipped (this machine has a package.json above the temp dir; CI runs both).
