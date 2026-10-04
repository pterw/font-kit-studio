### Spec Compliance
- PASS: isMain canonicalises both sides with realpathSync, so a symlink/junction run now bundles (packages/fontkitstudio/scripts/bundle.js:21-22). The link test passes at HEAD of the worktree.
- PASS: importing bundle.js from a test does not bundle (argv[1] is the test file, realpath differs). Verified: `node -e "import('./scripts/bundle.js')"` imports silently; the existing 3 bundle tests pass.
- PASS: only the 2 files named; no dist/ or LICENSE in the patch; no scope creep.
- PASS: argv[1] undefined/empty short-circuits to a falsy isMain, so no realpathSync call.

### Checks run
- realpathSync throw in normal invocations -> ran `node --test test/bundle.test.js` (4/4 pass, incl. the npm pack test that runs prepack with a real script path) -> no throw; test runner children always get an existing file as argv[1].
- Abnormal argv[1] -> `node -e "import('./scripts/bundle.js')" nonexistent` and `echo "import(...)" | node -` -> both throw ENOENT at import (argv[1] = 'nonexistent' / '-'). Not a normal invocation (see Minor 1).
- Other test files affected by the test deleting dist/ and LICENSE in the real package dir -> grep dist/LICENSE/bundle in test/*.js -> only bundle.test.js uses dist; package.test.js only checks pkg.files. Tests in one file run sequentially, and files that run in parallel do not read dist. Safe.
- .gitignore coverage -> `git check-ignore -v dist LICENSE` in packages/fontkitstudio -> both ignored (.gitignore:8, :9). Temp link dir lives in os.tmpdir() and is removed in finally. `git status` in the worktree shows only the 2 staged files.
- Link removal in finally -> rmSync(link,{force:true}) then recursive rmSync(linkDir); package dir intact afterwards (later tests and package.json still read). rm unlinks links rather than following them, on Windows junctions and POSIX dir symlinks.
- Linux/macOS -> read only (cannot run here): symlinkSync(target, path, 'dir') is valid on POSIX (type ignored); on macOS tmpdir is under the /var -> /private/var link, which realpath handles. No platform-specific assumption seen.

### Strengths
- The test deletes dist/ and LICENSE first, so a stale copy cannot pass, and compares bytes (deepEqual on Buffers) against the repo's fontkit-studio.html.
- The report's mutation check (old bundle.js makes this test fail) is credible: without the realpath, argv[1] is the link path and the guard is false, so no dist/ is created and readFileSync throws.
- Cleanup is in finally, and the link is a junction on Windows (no admin rights).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. bundle.js:22 -- realpathSync(process.argv[1]) throws ENOENT at import if argv[1] is not an existing path (`node -` from stdin, or `node -e "..." arg`). The old resolve() check could not throw. Normal flows (tests, npm prepack, bin) are unaffected, but a one-line guard (try/catch returning false, or existsSync) would make import never throw. Low risk; not required.
2. bundle.test.js:50-52 -- asserts only dist/fontkit-studio.html. The LICENSE (named in the Codex finding) and fontkit-bridge.js are deleted/created but not asserted; an assertion that LICENSE exists after the run would pin the "missing LICENSE" half of the finding at little cost.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The fix canonicalises both paths, import has no side effect, and the new test is a real regression test (clean slate, byte compare, finally cleanup, cross-platform link type, artifacts gitignored). Only two Minor polish points remain.
