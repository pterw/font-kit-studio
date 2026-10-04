# Task 2b code report (MODE: code, BASE 880666c, worktree C:/fks/t2b)

Patch: `.superpowers/sdd/r1-pr-a/task-2b-code.patch` (`git apply --check -R` passes in the worktree).
Files (10): .gitattributes (new), .gitignore, fontkit-bridge.js (+1 header line),
packages/fontkitstudio/{package.json (prepack), scripts/versions.js, scripts/bundle.js,
test/versions.test.js, test/bundle.test.js, test/helpers/fake-root.js, test/package.test.js}.
Renormalized paths: `git add --renormalize packages/fontkitstudio` changed no blob (index was
already LF); only the working copies were CRLF. No dist/ or LICENSE in the patch (ignored).

## Steps
1. Bridge header: done; `node --check fontkit-bridge.js` exit 0.
2-3. versions tests + versions.js: done. fakeRoot lives in test/helpers/fake-root.js, imported by both tests.
   RED: `npm test` -> `Cannot find module .../scripts/versions.js` and `.../bundle.js`, `ℹ pass 6 ℹ fail 2`.
4-5. bundle tests + bundle.js, prepack script, .gitignore: done. `npm pack --dry-run` does run prepack on npm 10.8.2.
   Deviation: its stdout carries prepack's own line before the JSON (first run failed with
   `Unexpected token 'o', "fontkitstud"... is not valid JSON`), so the test parses from the first
   line that starts with `[` (`stdout.search(/^\[/m)`).
   GREEN: `ℹ tests 12 / pass 12 / fail 0`.
6. Guard bites: bridge header set to 0.2.0 -> `ℹ fail 2`: `fontkitstudio: version mismatch: package is 0.2.1, but bridge header is 0.2.0`
   and the versions deepEqual (`'bridge header': '0.2.0'` vs `'0.2.1'`). Restored; `ℹ fail 0`.
7. .gitattributes `packages/fontkitstudio/** text eol=lf`. `git ls-files --eol packages/fontkitstudio`
   before: every file `i/lf w/crlf attr/` (cli.test, package.test, README, bin, cli.js; package.json too).
   After renormalize and rewriting the working copies to LF: all 11 files `i/lf w/lf attr/text eol=lf`.
   Strict assertion `bin.startsWith('#!/usr/bin/env node\n')` restored. Bite: CRLF on bin line 1 ->
   `ℹ fail 1`, `AssertionError: the bin needs an LF node shebang`; restored, fail 0.
8. Import guard: filter `/\.(c|m)?js$/`; SPECIFIER built from four patterns (import/export ... from,
   `import('x'` with or without options, `require('x')`, `createRequire(...)('x')`).
   RED with the old guard: `export * from 'left-pad';` in src/y.js -> guard test passes (gap);
   `import 'left-pad';` in src/x.mjs with the old `.js` filter -> passes (gap).
   (Putting the export line in cli.js would instead break the cli tests, so a separate file was used.)
   GREEN with the new guard, one file each, all fail naming left-pad: `export * from`, `export { a } from`,
   `import 'x'` in .mjs, `createRequire(..)('x')` in .cjs, `import('x', {with})` in .js, `require('x')` in .cjs.
   Negative control (`export const a = 'x'`, relative re-export, `import('node:fs')`) passes. All probe files removed.

## Gates (from C:/fks/t2b)
- static: `python scripts/verify.py --static-only` exit 0, last line `SKIP unittest/browser tests: --static-only; full acceptance not checked`.
- bridge-syntax: `node --check fontkit-bridge.js` exit 0.
- node-package: `ℹ tests 12`, `ℹ pass 12`, `ℹ fail 0`.
- frontend-gate, Python suite halves: NOT RUN (per dispatch; gate-runners run them at landing).
- commit-messages: not run (no commit made). pre-commit: not installed, skipped.

## Self-review (anti-patterns)
- Test quality: each new test fails without its code (RED shown for versions, bundle, shebang, guard).
- AP 11-12 (sibling copies): version labels are read from one place (versions.js LABELS); the bridge
  header is the only new label. Grepped nothing else states the bridge version.
- AP 13: no server started. The pack test spawns npm synchronously; temp dirs are in os tmpdir.
- AP 14: frontend gate, suites, commit-messages, pre-commit reported not run.
- AP 15: no process state in committed files.
- Zero deps: scripts use node:* only. Loopback n/a.
- Concern: the pack test writes dist/ and LICENSE into the package dir (git-ignored) as a side effect of prepack.
- Note: sed -i left worktree fontkit-bridge.js as LF; index blob unaffected (autocrlf).

## Handoff
- progress.md event (draft): "R1.2b: bundle step copies Studio, the bridge and LICENSE into the package's dist/
  after checking package, Studio title/eyebrow and bridge header versions agree (D041); package files pinned to
  LF via .gitattributes; import guard now covers export-from, dynamic import with options, require and
  createRequire, in .js/.mjs/.cjs."
- No CHANGELOG line. Tick plan checkboxes for R1.2b.
- Commit subject: `feat(dev): bundle Studio and the bridge at one checked version`.
  Body: the package ships Studio and the bridge at matching versions (spec 1.1) so a page never talks to a
  Studio from another release; the check runs before anything is copied. Also pins the package to LF line
  endings so the bin shebang survives a Windows checkout, and closes the import guard's gaps.
- Landing: the frontend gate applies (bridge changed by one comment line).

## Codex P2 fix (BASE 221a0a4, worktree C:/fks/t2b-fix)
Patch: `.superpowers/sdd/r1-pr-a/task-2b-fix-codex.patch` (reverse-apply check passes). Files:
packages/fontkitstudio/scripts/bundle.js, packages/fontkitstudio/test/bundle.test.js. No dist/ or LICENSE in it.
- Test added: links the package dir (junction on Windows, 'dir' elsewhere) in a temp folder, deletes dist/ and
  LICENSE, runs `node <link>/scripts/bundle.js`, asserts exit 0 and dist/fontkit-studio.html equals the repo's
  Studio bytes; link and temp dir removed in `finally`.
- RED (current code): `✖ running the script through a directory link still bundles`, `ℹ tests 24 / pass 23 / fail 1`.
- Fix: `isMain = process.argv[1] && realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url))`.
- GREEN: `ℹ tests 24 / pass 24 / fail 0`.
- Mutation (old bundle.js restored): `ℹ pass 23 / fail 1`, the link test fails; fix restored, `pass 24 / fail 0`.
- Not run: frontend gate, Python suites, pre-commit (not installed).
