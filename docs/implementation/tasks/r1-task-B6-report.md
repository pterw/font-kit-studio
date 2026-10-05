# B6 code report (mode: code, BASE 0e5e19b, worktree C:/fks/tB6)

Patch: `.superpowers/sdd/r1-pr-b/task-B6-code.patch` (14 files, +728/-15; `git apply --check -R` passes).
Files: `.gitignore`; src: `csp.js` (new), `proxy.js`, `run-proxy.js`, `run-vite.js`, `vite-plugin.js`;
Node tests: `csp.test.js` (new), `proxy.test.js`, `run-proxy.test.js`, `vite-plugin.test.js`;
Python: `tests/test_one_command_messages.py` (new), `test_one_command_vite.py`,
`test_vite_build_guarantee.py`, `helpers_csp_server.py` (`csp` parameter, default unchanged).

## Steps
1. Failing Node tests: done first. RED: `npm test` -> 3 test files fail with
   `ERR_MODULE_NOT_FOUND ... src/csp.js` (pass 74, fail 3), the expected failure before any code.
1b. Host refusal through the real command: done (`HostRefusalTest`).
2. Implement: done. Messages are module-level exports (`BUILD_LINE`, `HOST_ERROR`, `START_LINE` in
   vite-plugin.js; `BRIDGE_TWICE_MESSAGE`, `CSP_MESSAGE` in csp.js, shared by plugin and proxy).
3. Browser tests: done (`ProxiedPageTest`, Chromium).
4. GREEN and four mutations: done (below). 5. Gates: done except pre-commit. 6. Handoff: below.
Item 6 of the behaviour (untested Vite major, non-Vite folder): `test/cli.test.js` already asserts the
full texts (lines 64-71, 82-89); no new test added.

## Design points (need no ruling, listed for review)
- Warnings go through a `log(line)` option: `startProxy({ log })` (default stderr), `fontkitStudio({ log })`
  (default: Vite's `config.logger.warn`, else stderr). `runProxy` and `runVite` pass `err`.
- Pages are checked when tagged: the proxy only on buffered (taggable) pages; the plugin in
  `transformIndexHtml`, and its `server.headers` check is read in `configResolved`. A stood-down plugin says nothing.
- The host refusal is checked in `configResolved` before the stand-down test, so the command's own copy refuses.
- Standalone start lines replace the old `  Font Kit Studio: <url>` line with `  Font Kit Studio · dev only` + `  Open: <url>`.

## Evidence
GREEN: `npm --prefix packages/fontkitstudio test` -> `ℹ tests 197, pass 195, fail 0` (2 skipped, as before).
`PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_messages test_one_command_vite
test_one_command_proxy test_vite_build_guarantee test_support` -> `Ran 43 tests ... OK`.
`python -m ruff check .` -> `All checks passed!`. Not run: pre-commit (`pre-commit: command not found`),
the full Python suites and the frontend gate (the dispatch did not ask; the diff touches `tests/`, so the
landing's suite-a/suite-b gates apply).

Mutations (each foreground, restored by copying the saved file back; `grep` confirms no residue):
| Mutation | Result |
|---|---|
| host check `if (false && ...)` in vite-plugin.js configResolved | node vite-plugin: fail 14; Python HostRefusalTest: the command runs on (host true), 60 s timeout, error |
| build line guard `if (false)` in `apply` | node vite-plugin: fail 1; `test_vite_build_guarantee`: 2 failures |
| proxy CSP check `if (false) warnOnce(CSP_MESSAGE)` | node proxy+run-proxy: fail 4; Python blocking-policy browser test: error |
| plugin CSP and own-bridge warnings `if (false)` | node vite-plugin: fail 4 |
| proxy own-bridge warning `if (false)` | node proxy: fail 2 |
`csp.js` itself is pinned by 27 value tests in `csp.test.js`.

## Self-review (anti-patterns)
- AP 13: every helper process is stopped in `addCleanup` (stdin close, wait, kill own PID on timeout);
  CSP servers shut down; host test uses `subprocess.run` with a timeout and removes its `.fks-*` folder
  (`git status` shows no `.fks-*`). AP 14: `require_fixture` fails under `FKS_REQUIRE_FIXTURES=1`.
- Rule 4/D051: the browser test compares `body` element lists (direct, proxied, after a live edit) and
  head tag counts; no bridge change. Rule 6/AP 1-4: warnings print fixed texts only; nothing from the
  page or request is echoed; the CSP and meta parsing only reads. Messages say "Font Kit Studio".
- A negative wait of 5 s (Studio never connects under the blocking CSP) is the one allowed short wait.
- Concerns: `config.server.host` is checked on the resolved config only, so a `--host` flag cannot arise
  (the command uses `createServer`); a CSP given by the app's own middleware (not `server.headers`) is
  not seen by the plugin, only by meta tags. Chromium only (ENGINES default).

## Handoff
- Commit subject: `feat(dev): explain every refusal and keep the command off the network`
- Why-body: Every way the command can fail now ends in one plain line saying what happened and what to do.
  A Vite server opened with host or server.host is refused before it listens, and Studio is closed first.
  vite build with the plugin says it added nothing, once. Pages that already load their own bridge or
  carry a Content-Security-Policy that blocks it are reported once per run, in the plugin and the proxy.
  Nothing new reaches the user's page (D051). Standalone plugin mode prints the same two start lines
  as the command.
- progress.md event draft: `B6 (R1.6) landed: refusals and failure messages. Host refusal (server.host
  other than localhost/127.0.0.1/::1), build line, own-bridge and CSP warnings (src/csp.js), start lines;
  rule 4 browser test on the proxied Bootstrap page. Node 195 pass; 43 Python tests in the five named modules.`
- CHANGELOG: the command's "Added" line needs no change; optional clause: "refuses a Vite server opened to
  the network, and says once when a page's own bridge or Content-Security-Policy may stop Studio connecting."
- Landing checks: re-measure counts; `.gitignore` gets `fixtures/*/.fks-*/`; run the suite-a/suite-b gates.


## Landing (controller, 2026-10-04)

Review: Approved, five minor findings. One fixed at landing: `server.host: '[::1]'` is loopback and is now accepted (added to the allowed list and its test). Kept as recorded: a 1 s negative wait in the CSP browser test (it proves Studio does not connect); the head check counts the bridge tag rather than comparing every other head child; a host-source policy such as `script-src http://localhost:5173` warns in plugin mode although the bridge would load (the brief's rule is 'self', * or http:); a CSP set by the app's own middleware is seen only through meta tags. CHANGELOG: the command's Added entry now says it refuses a Vite server opened to the network and names a page whose own bridge or CSP may stop Studio connecting. Node tests on Windows: 199 run, 197 pass, 2 skipped.
