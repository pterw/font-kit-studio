### Spec Compliance
- PASS: runVite calls process.chdir(projectDir) inside the try before vite.createServer and passes no inline root; nothing else in runVite changed (packages/fontkitstudio/src/run-vite.js:24-29). Matches the controller ruling.
- PASS: Test changes are confined to the side effect of the chdir (cwd restore in run-vite.test.js and cli.test.js) plus one new browser test (tests/test_one_command_vite.py:145-165). No unrequested product change.
- PASS (with a note, see Minor 1): the Codex wording "discovered project directory" is met only when the command is run from the folder that holds the config. The ruling says chdir(projectDir), and the implementer did exactly that.

### Checks run
- New test is real -> copied the package to scratchpad with run-vite.js from 7376bd2, built a temp project (package.json + vite.config.js with root 'app' + fontkitStudio() + app/index.html) under fixtures/vite-react/.fks-probe, ran main() in process against both trees and fetched the Open: target -> OLD: HTTP 404, no marker, 0 bridge tags. NEW: HTTP 200, marker present, exactly 1 bridge tag.
- Cleanup of the new test's .fks-* folder -> read start() and test (addCleanup(rmtree) is registered before start() registers stop, so LIFO runs stop first, rmtree second); .gitignore:12 `fixtures/*/.fks-*/` ignores it; `git status --ignored | grep fks` after the Python run and after my probe -> empty. PASS.
- Config with no root still serves project folder -> `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_vite -v` -> 3 tests OK (new test, vite7, vite-react live-edit). PASS.
- Subfolder run -> same probe with cwd = <project>/sub (package.json + config one level up) -> NEW: 404 and process cwd is sub. OLD code: also 404. So a subfolder run does not serve the discovered project, before or after this change. runVite is given cli.js's `cwd` (cli.js:93), and the dir loadVite discovers (project.js:85-89) is dropped (run-vite.js:18 destructures only `vite`). See Minor 1.
- Does anything after runVite depend on the old cwd -> read cli.js, proxy.js, studio-server.js, vite-plugin.js, open-browser.js. Studio and bridge default files are `new URL(..., import.meta.url)` (absolute), cli.js reads package.json by import.meta.url, startStudio runs before the chdir, openBrowser spawns with no relative path. No cwd dependence found. Only the string-typed studioFile/bridgeFile test seams would resolve relative paths against the new cwd (bridgeFile is read lazily, vite-plugin.js:111-113); the tests pass absolute paths. Not a product issue.
- Node tests restore cwd robustly? -> read run-vite.test.js and cli.test.js hunks. run-vite.test.js: startDir captured at module load (before any test), restored first line of both finally blocks. cli.test.js: startDir captured per startCommand call, restored in stop(), which every caller invokes in finally (lines 225,233,249,261,268). A failed assertion still restores. Weakness: if main() throws inside startCommand before returning, stop is never created (main returns codes, so this is theoretical). PASS.
- Full node suite -> `npm --prefix C:/fks/tC1/packages/fontkitstudio test` -> tests 199, pass 197, fail 0, skipped 2 (skips not introduced by this diff; they are not in changed files).

### Strengths
- The new test hits the real regression through the real command and a real Vite, asserts status 200, the marker text and exactly one bridge tag; it was 404 on the old code (verified independently).
- chdir sits inside the existing try, so a failing chdir still closes Studio.
- Test cwd restore is in finally and ordered before temp-folder removal.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Subfolder runs are not helped (run-vite.js:18,27). `isViteProject(cwd)` walks up to the package.json, so the command accepts a subfolder, but runVite then chdirs to the subfolder, where Vite finds no config and serves the subfolder (404). Verified identical before the change, so not a regression. The Codex text says "Start Vite from the discovered project directory"; a one-line follow-up (`const { vite, projectDir: found } = await loadVite(projectDir)` then chdir(found)) would honour it fully. Suggest the controller decide whether to fold it in or record it; no test covers it today.
2. Python test uses `urllib.request.urlopen(target)` with no timeout (tests/test_one_command_vite.py:157); a stalled server would hang until the suite is killed. Add `timeout=30`.
3. The new test only exercises vite-react (Vite 8?); the vite7 fixture is not exercised for a config root. Low risk, same createServer API.

### Plan-mandated (for the owner)
- [Minor] Subfolder runs still serve the subfolder, because the ruling chdirs to the cli's cwd rather than the discovered dir (run-vite.js:27) -- brief requires: "process.chdir(projectDir) before createServer ... nothing else about runVite changes."

### Assessment
**Task quality:** Approved
**Reasoning:** The fix is minimal and correct for the reported case (404 before, 200 with marker and one bridge tag after, verified by an independent probe). No cwd-dependent code follows the chdir, and the in-process tests restore cwd in finally. The only gap is the subfolder case, which is pre-existing and ruling-mandated.
