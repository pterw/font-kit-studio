# B3b code report (mode: code, BASE d58eb99, worktree C:/fks/tB3b)

Patch: `.superpowers/sdd/r1-pr-b/task-B3b-code.patch` (9 files, +687/-25; `git apply --check -R` passes).
Files: `.github/workflows/quality-gate.yml`, `packages/fontkitstudio/src/{cli,run-proxy,run-vite(new),vite-plugin}.js`,
`test/{cli,run-vite(new),vite-plugin}.test.js`, `tests/test_one_command_vite.py` (new).

## Steps
1. Node tests: done (cli.test.js 24 tests total; vite-plugin dedupe tests; extra run-vite.test.js).
2. Implement: done. `startStudio({studioPort, studioFile, err})` extracted unchanged into run-proxy.js, used by both runners.
3. Browser test: done (both fixtures, Chromium). `test_support` passes (in the 40-test run below).
4. CI: done, but as an added step (see deviations).
5. Mutations: done, foreground, one at a time, each restored by editing.
6. Gates: below. pre-commit is NOT RUN: `.pre-commit-config.yaml` does not exist in the worktree or repo
   (`python -m pre_commit` says "is not a file"; the `pre-commit` binary is not installed). Ruff ran instead.

## Evidence
- RED: the new tests were written after the implementation (I did not stage a RED first). Run against BASE
  sources (copy of the package with BASE cli/run-proxy/vite-plugin, no run-vite.js) the three new/changed
  Node test files fail wholesale (the first ones fail at import/setup), which proves little. The per-guard
  mutations below are the real proof.
- Mutations (all restored; `node --test --test-force-exit`):
  1. dedupe check (`standDown = false && ...`): FAIL `test/vite-plugin.test.js` "a standalone instance stands down
     when the command added its own..."; browser `test_vite7_connects_with_one_bridge_tag` fails on the extra
     `  Font Kit Studio: ` line.
  2. `--no-open` ignored (`open: true` to runVite): FAIL `cli.test.js` "a Vite project opens the browser on the Open:
     URL unless --no-open". Same for the proxy branch: FAIL "a URL argument runs the proxy and opens unless --no-open".
  3. Vite-project check skipped (`if (false && !isViteProject(cwd))`): FAIL "a folder that is not a Vite project
     exits 2..." and "--no-open and --studio-port do not turn a non-Vite folder...".
  4. (extra) runVite no longer closes Studio when Vite fails: FAIL `run-vite.test.js` "when Vite fails to start,
     Studio is closed before the error is rethrown".
- Gates (final tree, worktree):
  - `npm --prefix packages/fontkitstudio test`: `ℹ tests 124 / pass 122 / fail 0 / skipped 2` (2 skips are not mine).
  - `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_vite test_one_command_proxy test_vite_build_guarantee test_support -v`: `Ran 40 tests ... OK`.
  - `python -m ruff check .`: `All checks passed!`
  - `git status` shows the fixtures untouched (app.css restored). The ports of both fixtures are refused after stop (asserted in the test's cleanup).

## Deviations (each forced by the brief or the code)
- CSS hot update instead of JSX edit (the brief's recorded deviation): test edits `src/app.css`.
- "Badge still Connected" after the CSS edit: the badge text becomes `Live · rev N` after any edit
  (fontkit-studio.html lines 4200 vs 4723), so the test asserts `data-state` is `connected` or `live`, not the
  `Connected (N targets)` text.
- `main` takes an extra optional `openUrl` in its options (test seam, passed through to both runners;
  undefined means the real opener). Without it `--no-open` could only be tested by opening a real browser.
  The brief's `{ out, err, cwd }` is a subset.
- `test/run-vite.test.js` added (not in Owns): covers the Vite-refusal-before-Studio and Studio-closed-on-failure guards.
- CI: added a separate step "Install the test tools and Chromium" before the fixture tests step (the brief says
  "in the fixtures job, before the fixture tests step"); the tests step got `FKS_ENGINES: chromium` and the 3-module command.
- Exit code for proxy refusal: `main` maps an error whose message starts with `Font Kit Studio proxies only a local
  dev server` to 2 (matching proxy.js's text); other errors from runProxy are 1; `ProjectError` is 1. If proxy.js
  changes that message, the cli test "an https or remote address exits 2" fails.
- `--help`/`--version` now win wherever they stand in argv (before: only as the sole argument).
- cli.test.js `before` bundles Studio into the gitignored `dist/` when missing: proxy refusals start Studio first
  (runProxy order, B5), which reads the bundled copy.
- The in-process cli tests close their servers by `process.emit('SIGTERM')` (the runners' own handlers).

## Self-review (anti-patterns)
- AP 13: every process/server started is stopped: browser test stops by CTRL_BREAK_EVENT/SIGINT, kills only its
  PID on timeout and fails; Node tests close Studio via the runner's handler or inject failure paths.
- AP 14: fixtures `require_fixture` honoured; with FKS_REQUIRE_FIXTURES=1 never skips. pre-commit not run (reported).
- AP 1-4/7 trust boundary: the URL argument only reaches `startProxy`, which refuses https/remote; tested with
  `https://localhost:3000` and `http://example.com`; no message prints a stack; Vite is loaded only by project.js.
- Rule 6: nothing written to the project; the plugin is added in memory (`createServer({plugins})`).
- Rule 7: browser test routes `https://**` to abort; `--no-open` always; no test opens a real browser.
- AP 11-12: grepped the old inline fallback in run-proxy.js; only `startStudio` remains.
- Concern: the Firefox engine was not run (ENGINES defaults to Chromium; CI sets FKS_ENGINES=chromium).

## Handoff
Commit subject: `feat(dev): run Studio with the project's Vite or a proxy in one command`

Body draft:
```
`npx fontkitstudio` now runs the project's own Vite with the plugin added
in memory (nothing is written to the project), or the proxy when given a
URL. Both print two lines, open Studio unless --no-open, and stop
cleanly on Ctrl-C. A plugin already in the project's config stands down
when the command adds its own, so a page carries one bridge tag.
Studio's start with the port fallback is now one exported function used
by both runners. Browser tests run the real command on both fixtures;
the fixtures job installs Chromium and runs them.
```
progress.md event draft: `R1.4d (B3b) landed: fontkitstudio runs the project's Vite with the plugin in memory or the
proxy for a URL; --no-open, --studio-port; dedupe so one bridge tag; browser tests on the Vite 7 and 8 fixtures.`
Deviation to log: CSS hot update (not JSX) in the hot-update test; badge asserted by data-state (connected/live).

CHANGELOG [Unreleased] Added draft:
- `npx fontkitstudio`: in a Vite project (7 or 8) it runs the project's own dev server with Studio added in memory;
  with a local dev server's address it runs Studio through a proxy. `--no-open` prints the URL instead of opening
  the browser; `--studio-port <n>` keeps Studio on one port.
- The Vite plugin stands down when `fontkitstudio` already added it, so a page carries one bridge tag.

Landing checklist: tick plan B3b boxes; the `fixtures` job now has a separate install step (check the CI diff).

## Fix round 1
Files added to the patch scope: `src/proxy.js`, `test/proxy.test.js` (item 1 only). Patch regenerated against d58eb99 (`git apply --check -R` OK).
RED/GREEN here is by mutation of the fix (restored by editing, foreground, `node --test --test-force-exit`); the GREEN run is the final one.

1. Refuse before any server starts. `proxy.js` exports `ProxyTargetError` and `parseProxyTarget(target)` (same text, `startProxy` calls it; B4's tests unchanged and green). `cli.js` calls it before `runProxy` and maps `instanceof ProxyTargetError` to exit 2; the message-prefix match is gone.
   Tests: "a refused URL beside a busy --studio-port exits 2 with the refusal and no fallback line"; "with no dist/ at all, a refused URL still exits 2" (runs a copy of bin/src/package.json with no dist/); `parseProxyTarget` unit test in proxy.test.js.
   RED (call removed from cli.js): both new cli tests FAIL. GREEN: pass.
   The cli.test.js `before` bundle step stays: the in-process tests that really start Studio (Vite stub open/--no-open, `--studio-port` pass-through, proxy open/--no-open) read dist/ because `main` has no studioFile seam. No refusal test needs it.
2. A parseable non-http(s) positional (`localhost:3000`, `ftp://x`) gets the not-a-URL message, exit 2. Test: "an address that parses but is not http or https...". RED (check removed): FAIL; GREEN: pass.
3. Missing `resolvedUrls.local[0]`: runVite closes Vite and Studio and throws `Font Kit Studio could not tell which address Vite is serving on.` (cli exit 1 via the generic path). Test in run-vite.test.js with a stub Vite: asserts message, Vite closed, Studio port free. RED (guard removed): FAIL (TypeError instead); GREEN: pass.
4. The 50 ms sleep is gone: in-process tests poll the Studio port (from the Open: line) until a connect is refused, with a 5 s deadline. Behaviour-only refactor; no RED applies.
`--bogus --help` still exits 2.

Gates (final tree): `npm --prefix packages/fontkitstudio test`: tests 129, pass 127, fail 0, skipped 2. Fixture/browser run: `Ran 40 tests ... OK`. ruff: all checks passed. Fixtures unchanged in `git status`. pre-commit still not run (no config in repo).


## Landing (controller, 2026-10-04)

Landed after fix round 1 and its scoped re-review (`r1-task-B3b-rereview.md`: Approved). At landing: one line of trailing whitespace removed from `cli.js`; CHANGELOG `[Unreleased]` gains the command and the plugin under Added. Kept as recorded: `--bogus --help` exits 2 (an invalid argument before `--help` is still an error); the Vite browser test's `stop()` skips its port check when no `Open:` line was seen (the test has already failed in that case). Process note: the tests were written after the code in the first pass, so RED is shown by mutating each guard, not by a run before the code existed. Node tests on Windows: 129 run, 127 pass, 2 skipped (B1's machine-dependent cases).
