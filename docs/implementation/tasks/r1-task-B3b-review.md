### Spec Compliance
- PASS: argument cases and exit codes (unknown flag 2, bad port 2, two positionals 2, not-a-URL 2, no Vite project 2, ProjectError 1); both `--studio-port n` and `--studio-port=n` parse; texts match the brief verbatim (packages/fontkitstudio/src/cli.js:48-131). cli.test.js asserts text and status through the real bin.
- PASS: USAGE matches the brief text (cli.js:34-42).
- PASS: runVite follows the brief: project's Vite via loadVite, plugin in memory via createServer({plugins}), config still loaded, printUrls, two lines, same signals as runProxy, close() idempotent (`closing ??=`), handlers removed, Studio closed if Vite fails (src/run-vite.js:194-248).
- PASS: dedupe hook as specified (vite-plugin.js: api flag only when `options.studio`; configResolved stands down only for a `fontkit-studio` plugin with `fromCommand === true`; configureServer and transformIndexHtml both honour it).
- PASS: startStudio extracted unchanged from runProxy and called by both runners (run-proxy.js:6-22, 33; run-vite.js:205). No copy remains.
- PASS: browser test follows the brief (both fixtures, one bridge tag, live edit 56px, CSS hot update keeps edit, ports refused after stop, no page.content()).
- PASS: CI job installs requirements-dev and Chromium, sets FKS_ENGINES and FKS_REQUIRE_FIXTURES, runs the three modules (quality-gate.yml:203-212). The install is a separate step, not folded into an existing one: harmless, and reported.
- FAIL (see Important 1): a refused URL is not refused before a server starts.
- Deviations recorded: CSS instead of JSX (brief-mandated); data-state connected|live (justified: badge text becomes "Live - rev N" after an edit; acceptable); extra `openUrl` seam; extra run-vite.test.js.

### Checks run
- Order of work -> read run-proxy.js:33 and proxy.js:50-57 -> `startStudio` runs before `startProxy` validates the target. Confirmed by hand: with a busy port, `fontkitstudio http://example.com --studio-port <busy>` printed "port N is busy, so Studio uses port M; its saved settings stay with the old port." and then the refusal, exit 2. A refused URL therefore binds a Studio server and prints a misleading fallback line first.
- Same defect without dist/ -> reasoned from studio-server.js:30-40: a missing bundle makes `https://x` fail with "cannot read Studio ... run the bundle step", exit 1, not the refusal (exit 2). The implementer's own cli.test.js `before` bundles dist/ to hide this.
- `localhost:3000` (no scheme) -> run by hand -> `new URL` parses it as scheme "localhost:", so it reaches the proxy and gets "proxies only a local dev server (localhost or 127.0.0.1)", exit 2. Correct exit, but the message is baffling for a user who typed localhost. Not in the brief.
- `--bogus --help` -> run by hand -> exit 2 with the unknown-argument error: "--help wins anywhere" is only true when no earlier argument is an error.
- npm test in C:/fks/tB3b -> 124 tests, pass 122, fail 0, skipped 2.
- `test_one_command_vite` with FKS_REQUIRE_FIXTURES=1 -> 2 tests OK in 10 s.
- Dedupe mutation (`standDown = false && ...`) re-run in the foreground -> vite-plugin.test.js: "a standalone instance stands down ..." FAILS (1 fail); browser `test_vite7_connects_with_one_bridge_tag` FAILS on the extra `  Font Kit Studio: http://127.0.0.1:...` line (a second Studio really started). Restored by editing; diff stat back to 687/-25. The mutation evidence is credible for this guard. I did not re-run the --no-open and Vite-check mutations; their assertions (opened list, exact stderr and status) are direct, and I read them.
- CI -> read workflow lines 170-212 and requirements-dev.txt -> playwright is pinned there; setup-python and setup-node precede; OK.
- Leftover processes -> none started by me remain (hand runs exited by themselves).

### Strengths
- The dedupe test uses real plugin objects and a fake config.plugins, and includes look-alikes (no api, fromCommand false, other name), so the guard is tested from both sides.
- The browser test proves the real front door: Ctrl-Break/SIGINT, process exit within 15 s, both ports refused afterwards, kill-by-PID on timeout with a failure.
- Close path in runVite is correct: Vite closed first, Studio in `finally`, idempotent, handlers removed.
- run-vite.test.js "Studio closed when Vite fails" checks the port is actually free, not that a mock was called.

### Issues
#### Critical
(none)

#### Important
1. Refusals happen after Studio has started, and `main` recognises them by message prefix (cli.js:114, 129; run-proxy.js:33). A refused https/remote URL binds a Studio server, can print the "port busy" fallback line, and fails with exit 1 and a "cannot read Studio" message when dist/ is missing. The product's front door should say "no" before it does any work. The coupling `error.message.startsWith('Font Kit Studio proxies only a local dev server')` (cli.js:49, 129) breaks silently if proxy.js's wording changes: the refusal would turn into exit 1. The implementer saw both and worked around the first by bundling dist/ in a test `before`. Fix: export one `parseProxyTarget(target)` (or `assertProxyTarget`) from proxy.js that throws a `ProxyTargetError` (or sets `error.code = 'EPROXYTARGET'`), call it from `startProxy` and from `main`/`runProxy` before `startStudio`, and map the class/code to exit 2. Then drop the bundling workaround in cli.test.js `before`, and add a test that a refused URL binds nothing (e.g. refusal with a busy `--studio-port` prints no fallback line).

#### Minor
1. `--help`/`--version` "win anywhere" is not uniform: an earlier unknown flag or bad port returns its error first (cli.js:63-74, `--bogus --help` -> exit 2). Either say "wins unless an earlier argument is invalid" or scan for them first. The choice itself (win anywhere) is acceptable and conventional.
2. `localhost:3000` is accepted by `new URL` and refused with a message that names localhost as allowed. Suggest the brief's not-a-URL hint or a scheme-less retry; out of this brief's text, so a follow-up.
3. `appUrl = server.resolvedUrls.local[0]` can be undefined if the project's config binds a specific non-loopback host; the failure then comes from `studio.url(undefined)` and is cryptic (run-vite.js:216-226). Closing is handled correctly, only the message is poor.
4. cli.test.js stops in-process servers with `process.emit('SIGTERM')` and a 50 ms sleep (cli.test.js startCommand). It works but is a fixed sleep and depends on the runner's own handler; awaiting `close()` would be cleaner, but the runners' return value is not exposed through `main`.
5. `openUrl` seam on `main` and the extra test/run-vite.test.js: acceptable. The seam is optional, undefined falls to the runner default, and it makes `--no-open` testable without a browser. Both are recorded in the report.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The command, plugin dedupe, startStudio extraction, tests and CI are correct, and the dedupe mutation fails as claimed. One Important issue stands: URL refusals run after Studio starts and are matched by message prefix. The fix is small, and it also removes the dist/ workaround in the CLI tests. Everything else is Minor.
