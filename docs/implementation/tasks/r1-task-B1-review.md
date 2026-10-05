### Spec Compliance
- PASS: Interface matches the brief (TESTED_VITE_MAJORS, ProjectError with name set, findProjectDir, isViteProject, findVite, loadVite) (src/project.js:11-86).
- PASS: All four messages are verbatim from the table; "7 and 8" is built from TESTED_VITE_MAJORS (src/project.js:26, 63, 51, 70-72). No stack, parser text or file content in any message: readJson uses a bare `catch {}` (src/project.js:30-36); the resolve catch is bare too (src/project.js:61-66). Checked by hand: a vite package.json containing "garbage SECRET" gives only the "<path> is not valid JSON" text.
- PASS: Resolution goes through the project: createRequire(join(projectDir,'package.json')) (src/project.js:58-60). The package itself is never consulted. Vite 6 and 9 are refused, tested at project.test.js:35-45. `8.0.0-beta.2` parses to major 8 (checked by running it).
- PASS: Imports are node:fs, node:module, node:path and node:url only. package.json is untouched and there is no CLI wiring.
- PASS: Test items 1-9 of the brief are all present. The skip is narrow, see Checks.
- PASS: Existing tests in package.test.js are untouched; one test was added at the end.

### Checks run
- Full node suite in C:/fks/tB1 -> `npm test` -> tests 36, pass 35, fail 0, skipped 1. Matches the report.
- Skip scope -> read project.test.js:69-85 and :100-108 -> only the "findProjectDir says so when there is no package.json" test calls t.skip (line 78). The isViteProject no-package case is wrapped in `if (!packageJsonAbove(bare))` and is silently skipped inside a test reported as passing (see Minor 1).
- No-package branches are correct -> ran findProjectDir('C:/') and isViteProject('C:/') directly (the drive root has no package.json on this machine) -> got the exact brief text and `false`. The loop terminates at the root (`dirname(dir) === dir`). Linux /tmp: the walk goes /tmp then /, and CI has no /package.json, so CI runs both no-package cases.
- Guard regexes -> ran the three patterns on sample strings. `createRequire` import is caught. `import(x)`, ``import(`a`)`` and `import( x)` are caught. `require(x)` and `mod.require(p)` are caught. `import('node:fs')`, `import.meta.url` and `require('x')` do not false-positive. No existing file in bin/ or src/ other than project.js contains createRequire, import( or require(, so there is no false positive on the real tree. The exemption is exactly `join(PKG_DIR,'src','project.js')` and nothing else. The report's mutation (`await import(process.argv[2])` in cli.js) is caught by the second regex.
- Robustness edge cases, run by hand: a vite package.json with no version gives "This project uses Vite undefined ...". A project package.json of `null`, `[1]` or `"x"` gives isViteProject false and findVite works on a resolvable Vite. No crash and no leak.
- Temp dir cleanup -> counted `fks-*` entries in tmpdir before and after `node --test test/project.test.js` -> unchanged (329 and 329). No fixed sleeps in the diff.
- Test strength, by reading: the major check, the invalid-JSON catch, the not-installed catch and the subdirectory walk each have an exact-message assertion that fails if the code is removed. The loadVite test asserts real fake-module behaviour (createServer() === 'fake'), not a mock.

### Strengths
- Messages are asserted whole, and the hostile JSON case asserts there is no "SyntaxError" or `"name"` in the message.
- project.js is small and flat, and the one computed import is isolated and guarded.
- The loadVite test imports a real fake ESM module through the real createRequire path.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. project.test.js:107-108: the bare-dir `isViteProject(...) === false` assertion is silently skipped on machines with a package.json above tmpdir, inside a test that reports as passing. AP 14 wants a skip reported as a skip. Split it into its own test with t.skip, or reuse the same skip, so the skipped count shows both. Machine-independent option within the interface: `findProjectDir(parse(tmpdir()).root)` where the root has no package.json (true for C:\ here and / on Linux). This still depends on the machine, so it could only be an extra case, not a replacement.
2. src/project.js:67-68: a vite package.json with no `version` gives "Vite undefined". This is a corrupt or odd install, which is rare, and the brief does not specify it. A clearer message ("could not read Vite's version") would cost one line. It is not worth blocking.
3. src/project.js:70-80 (concern 2): findVite parses the project package.json before resolving Vite. The brief requires this (test 6 wants findVite to throw the invalid-JSON text), so it is correct. An unreadable project is reported before a missing Vite, which is the more useful order.
4. package.test.js (new guard): `import( 'x')` or `require( 'x')` with a space before the quote would false-positive, because `\s*` backtracks to zero. `import (x)` with a space before the paren is not caught. This is the brief's regex verbatim and only matters under unusual formatting. Do not change it here.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The implementation matches the brief's interface and the four messages exactly, resolves through the project, and the guard works on the real tree. Tests are RED-capable and clean up after themselves. Only minor test-reporting polish is left: the no-package cases are skipped on this machine and run on CI Linux.
