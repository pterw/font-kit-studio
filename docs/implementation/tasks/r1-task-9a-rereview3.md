### Scope
Scoped re-review of 9a fix round 3 (the dist/LICENSE race class): task-9a-fix2.patch (8 files, against 2014319), applied tree C:/fks/t9a2.

### 1. No Node test writes the real dist/ or LICENSE
- PASS: I grepped `test/*.js` and `test/helpers/*.js` for `dist` and `LICENSE`, and `src/` and `test/` for `bundle(`, `npm pack` and `prepack`.
  - bundle.test.js: the first two tests use temp fake roots (`fakeRoot`, `fakePackage`). The pack test and the directory-link test now use `scratchPackage()` and remove the scratch in `finally`. The link test asserts the scratch copy starts without dist/ and LICENSE.
  - package.test.js: the tarball test bundles and packs a scratch copy.
  - cli.test.js: `before()` only asserts that the real dist/ exists (cli.test.js:47-49). It no longer calls `bundle()`.
  - The remaining `dist` hits are the `node_modules/vite/dist` fixtures and fake-root temp files.
  - Other test files hand explicit temp files to Studio, the proxy and the plugin.
  - The only writer of the real dist/ and LICENSE is now the `npm test` script, once, before any test file starts. Prepack in a publish job is out of this scope.
- Residual: Python fixture tests run `npm run prepack` on the real package directory. They are not Node tests and are not parallel with `node --test` in CI, where fixtures is a separate job. Outside this scope.

### 2. The guard is not vacuous
- PASS: I ran two mutations in a scratch copy of the package, kept in $TEMP and removed afterwards, not in C:/fks/t9a2.
  - Baseline after bundling: bundle.test.js `pass 4, fail 0`.
  - A: a test that `rmSync`s the scratch dist -> `fail 1`, "a test deleted or rewrote the real dist/ or LICENSE".
  - B: a test that rewrites LICENSE with identical bytes after a 20 ms wait -> `fail 1`, the same message. This shows the mtime comparison matters, because a bytes-only comparison would pass.
  - Restored: `pass 4, fail 0`.
- The guard records file name, bytes and mtime of LICENSE and of every dist/ file, plus the dist/ listing, at file load, and compares in an `after` hook. It is attached to the three files that touch the bundle (bundle, cli and package tests). It also catches a writer in an unguarded parallel file, provided the writer's run overlaps a guarded file's lifetime. That is good enough; a writer that ran strictly before or after the three files would go unseen, but would also not race them.

### 3. `npm test` on CI and the release job
- PASS: package.json `test` is `node scripts/bundle.js && node --test test/*.test.js`. `&&` works in sh and in cmd.exe, so it runs on the ubuntu, macOS and windows entries. On a fresh checkout `bundle.js` needs only the repository's root Studio, bridge and LICENSE, which the checkout holds. A clean-start run in a scratch repository with no dist/ or LICENSE printed "bundled Studio and the bridge at 0.2.1", then `tests 250, pass 248, fail 0`.
- PASS: quality-gate.yml's node-package job runs `npm test` (line 204) with `working-directory: packages/fontkitstudio`, so it gets the bundle step, and the fixtures jobs run `npm --prefix packages/fontkitstudio run prepack` themselves. Nothing in quality-gate.yml, release.yml, README or CONTRIBUTING spells the old script out; both docs say `npm --prefix packages/fontkitstudio test`, which still holds. The release publish job runs `npm run prepack` and `npm publish`, never `npm test`, so it is unaffected. Neither workflow was edited in this round except the release.yml bundle step from round 2.

### 4. Runs
- `npm --prefix C:/fks/t9a2/packages/fontkitstudio test` twice, Node 24.16.0: both `tests 250, pass 248, fail 0, skipped 2`. `PYTHONPATH=tests python -m unittest test_release`: 25 tests OK (the gate test passes here because 2014319 has `workflow_call`). No process left running. The worktree has 8 tracked changes, the patch's own; dist/ and LICENSE are gitignored.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. package.test.js:112-116: the new comment has one over-long line ("... (helpers/real-bundle-guard.js). The bundle step runs explicitly, ..."). Wrap it.
2. The pack test in bundle.test.js and the tarball test in package.test.js now both pack a scratch copy, so they overlap; the package.test.js one is the stricter. Consider dropping the looser one in a later cleanup.
3. Running `node --test test/cli.test.js` alone without a bundled dist/ now fails with a clear message. This is intended and documented in the message; noting it for contributors.

### Assessment
**Task quality:** Approved
**Reasoning:** No Node test writes the real dist/ or LICENSE any more. The guard fails on delete and on a same-byte rewrite, and the new test script works from a clean checkout. Nothing in either workflow depended on the old script, and both Node runs were green.
