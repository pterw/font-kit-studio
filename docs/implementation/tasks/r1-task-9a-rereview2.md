### Scope
Scoped re-review of 9a fix round 2 (CI): task-9a-fix2.patch against 2014319, applied tree C:/fks/t9a2.

### 1. The race explanation
- PASS: it is correct. bundle.test.js:55-60, "running the script through a directory link still bundles", runs `rmSync(join(packageDir,'dist'))` and `rmSync(join(packageDir,'LICENSE'))` on the real package directory, then re-runs bundle.js. The pre-fix tarball test (package.test.js, fix 1) ran `npm pack --dry-run` on that same directory. `node --test test/*.test.js` runs files in separate parallel processes, so the delete can fall between prepack's copy and packlist's read. The CI symptom, exactly LICENSE and both dist files missing and nothing else, is the signature of this race. A "prepack skipped" cause would have failed every matrix entry, not only Node 26. Within one file the tests are sequential, so bundle.test.js's own pack test (bundle.test.js:34-48) cannot race with its own link test.

### 2. The npm claim
- PASS, as far as read-only checks go. I tried docs.npmjs.com's scripts page; it returned no readable text, so I did not get a docs quote. Empirical check instead: npm 10.8.2 locally, in a scratch copy in $TEMP (since removed) with `dist/` and `LICENSE` deleted. `npm pack --dry-run --json` ran prepack and listed LICENSE and both dist files, so `--dry-run` does not skip the lifecycle. I did not repeat the implementer's runs on npm 11.5.1 through 11.21.0 or re-read the 11.21.0 source (libnpmpack runs prepack before the tarball is built; publish packs through it). Two pieces of evidence point the same way: the CI failure appeared only on one matrix entry, and the implementer reports identical results on six npm versions. The publish does not depend on the claim now, because of the explicit bundle step below.

### 3. The fixes
- PASS: release.yml adds "Bundle Studio and the bridge" (`working-directory: packages/fontkitstudio`, `run: npm run prepack`) before "Publish to npm". `test_studio_is_bundled_before_publishing` finds exactly one such step by exact `run` equality, asserts its index is below the publish step's and asserts the working directory. A step changed to `echo skipped` yields zero matches and fails. Prepack running twice (the explicit step, then npm's own) is idempotent: it copies files and runs `checkVersions` again. This does not weaken the label guard.
- PASS: the tarball test packs a scratch copy. The copy holds the root Studio, bridge and LICENSE, plus the package's `bin`, `src`, `scripts`, `package.json` and `README.md`, in a temp repo layout. It runs `node scripts/bundle.js`, then `npm pack --dry-run --json`, and removes the copy in `finally`. Nothing it reads or writes is the real `dist/` or `LICENSE`, so it cannot race. bundle.js resolves REPO_ROOT as `<dir>/../..`, which is the scratch root, and `checkVersions` ran against it (the test passes). Failures throw, since `execFileSync` and `execSync` throw on a non-zero exit.
- PASS: the expected list is now filtered to `*.js` and `*.d.ts`, so a stray `src/x.txt` is in the tarball but not in the expected list, and the assertion fails. The same holds for a stray subdirectory under `src/` or `bin/`. The earlier version took every entry of `src/` and `bin/` from the same listing as the tarball, so a stray file could never fail it. This is a real fix of a vacuous part of the test. The implementer's mutation (`src/stray.txt`) is consistent with what I read.
- Reading: a stray top-level package-directory file is not shipped, because `files` is a whitelist, so it does not need to be in the copy. A `test/` entry in `files` is still caught by "declares what npm needs" (package.test.js:60), as the report says.

### 4. Other writers and readers of dist/ and LICENSE
- Grepped test/*.js and src/*.js. The only deleters are bundle.test.js:59-60 (the link test). The other writers are bundle.test.js (fake package dirs in temp, safe), cli.test.js:45 (`bundle()` only when `dist/fontkit-studio.html` is missing) and the new scratch copy.
- Readers of the real dist/ by default path: src/studio-server.js:38, src/proxy.js:73, src/vite-plugin.js:51. The test files pass explicit temp files, with one exception: cli.test.js starts Studio through the default `dist/fontkit-studio.html` (its own comment, cli.test.js:44, says so). The explicit-file users are proxy.test.js, run-proxy.test.js, studio-server.test.js (through helpers/serve-studio.js), vite-plugin.test.js (explicit or missing paths) and open-browser.test.js.
- Residual (see Minor 1): cli.test.js can still read the real dist while bundle.test.js's link test has it deleted. This predates 9a and this round. It is the same race class as the CI failure, but it is a much smaller window (a single read, not a prepack-then-pack sequence).

### 5. Repeated green runs
- `npm --prefix C:/fks/t9a2/packages/fontkitstudio test` three times on Node 24.16.0 and npm 10.8.2: every run `tests 250, pass 248, fail 0, skipped 2`. No process was left running, and the worktree's tracked changes are unchanged. I could not reproduce the race, so these runs show the tests are stable here, not that the race is gone. Gone for the pack test is what the scratch copy gives.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. A pre-existing tail of the same race: the link test in bundle.test.js (lines 55-67) deletes and rebuilds the real `dist/` and `LICENSE`. cli.test.js reads the real `dist/` through the default path, so a rare run could fail with a "cannot read Studio" error. The same fix as for the tarball test would remove it: run the link test against a scratch copy of the package, and leave the real directory alone. Out of 9a's scope, but cheap, so record it as a follow-up.
2. My first review judged the two pack tests' parallel prepack as a small risk. That was wrong in effect (CI hit it); the scratch copy resolves it for the new test.

### Assessment
**Task quality:** Approved
**Reasoning:** The race explanation matches the code, the explicit bundle step is tested, and the tarball test is isolated from the real directory and no longer vacuous for stray files. Three runs are green. The only residual is a pre-existing, narrower race (cli.test.js against the link test), recorded as Minor.
