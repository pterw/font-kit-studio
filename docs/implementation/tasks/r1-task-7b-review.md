### Spec Compliance
- PASS: Fixture files as briefed: next 16.3.8, react and react-dom 19.3.0 exact, plain JSX, no tsconfig, `dev` script, no external content (fixtures/next-app/package.json, app/*.jsx, app/globals.css; title 40px, lead rgb(51, 51, 51)).
- PASS: `.gitignore` gets exactly `fixtures/*/.next/` (.gitignore:13).
- PASS: Next started with the briefed command, cwd=fixtures/next-app, NEXT_TELEMETRY_DISABLED=1, polled for 200 with a 120 s deadline, stopped by handle with Ctrl-Break and kill on timeout (tests/test_one_command_next.py:1103-1121, 1080-1089).
- PASS: Command run on `http://localhost:<port>` with `--no-open`, `Open:` line read (test:1123-1152). https routed to abort (test:1176). Errors via Playwright `pageerror` plus page `console` events, which the report and docstring name (test:1179-1180).
- PASS: Badge Connected regex before the edit (test:1182,1185); selection with one retry (1159-1171); keystroke entry of 56 (1200-1202); 56px wait (1203).
- PASS: Hot update: marker set (1206), css rewritten, lead colour wait 30 s (1210-1212), then marker, badge, title 56px asserted (1213-1218). Raw page asserts exactly one bridge tag through the proxy target (1227-1231).
- PASS: Deviation recorded: post-hot-update badge uses data-state in (connected, live) instead of the Connected text. The rule it relies on is real (see Checks); same assertion as test_one_command_vite.py:224.
- PASS: No change outside owned files; proxy untouched (git diff shows only the 7 owned files).
- PASS: Definition of done evidence is present in the report: npm 10.8.2 and 29 s install, GREEN x3, both mutations with failing lines, test_support, ruff.
- CANNOT VERIFY FROM DIFF: the two mutation runs (upgrade socket destroy; wrong id). Not re-run; I ran only the GREEN test, once. The failing line cited (test:179 in the report, a wait on the lead colour) matches the code at 1210 as a hot-update wait.

### Checks run
- Whole module, once: `PYTHONPATH=tests python -m unittest test_one_command_next -v` in C:/fks/t7b -> 1 test, OK, 4.07 s.
- Orphan processes after the run: Get-CimInstance Win32_Process filtered on the t7b path, and node.exe list -> only my own bash/powershell shells; the remaining node processes are unrelated MCP/Adobe ones. No next, next-server or worker left.
- Fixture restored byte for byte: `git diff --stat` in C:/fks/t7b after the run -> empty (only an autocrlf warning); globals.css matches the index. Cleanup order is LIFO: command stopped, Next stopped, css restored (the css restore is registered before the write, test:1191).
- Badge soundness: `setBridgeStatus` call sites in fontkit-studio.html (3689-3695, 4200, 4723 and the others) -> the only values are connected, live (after an applied edit, line 4200), connecting, detected, idle, missing, rejected, error. Accepting {connected, live} therefore excludes every loss, error and reject state. Sound for "not lost, not errored".
- HMR over the proxy: the marker (`window.__fksMarker`) set in the frame must survive, so a reload fails the assertion at 1213; the colour change can only arrive via Next's HMR socket, and the report's mutation (destroy sockets in the upgrade handler, proxy.js:299) fails exactly at that wait. Together they prove an update by HMR through the proxy WebSocket with no reload.
- Hydration/page-error: `page.on('pageerror')` and `console` handlers are attached before `page.goto` (test:1179-1181), so load-time hydration messages are captured, and the assertions at 1219-1220 are real (empty-list checks on collected lists). No positive control for the hydration filter exists; see Minor.
- CI draft against `.github/workflows/quality-gate.yml` -> the fixtures job uses `pip install -r requirements-dev.txt` and `playwright install --with-deps chromium` (lines 229-230); the draft matches.
- Out-of-scope per controller ruling, not flagged: untracked fixtures/next-app/AGENTS.md and CLAUDE.md.

### Strengths
- Process hygiene is correct: both processes are started in their own process group and stopped by handle, with kill on timeout, and none survived the run.
- The hot-update proof has three independent legs (colour changed, marker survived, title edit kept) and a mutation tied to the WebSocket handler.
- The CSS is restored in cleanup and between engines, and the fixture was clean after the run.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- tests/test_one_command_next.py:1215 -- the post-hot-update badge check is weak evidence that Studio is still connected. "live" is set at fontkit-studio.html:4200 after the edit and is sticky, so a bridge that dropped silently after the edit would still read "live". The title staying 56px (1216-1218) is DOM state in the frame and does not prove the channel. A stronger check is a second live edit after the hot update (for example size 48 applies). Same pattern as the vite test, so not a regression, and it is no reason to block.
- tests/test_one_command_next.py:1109 -- Next's stdout and stderr go to DEVNULL, so a failure ("next dev exited before answering", the 120 s timeout) carries no diagnostics. Consider a drained pipe, as the command helper does.
- tests/test_one_command_next.py (cleanup, 1080-1089 and 1136-1141) -- unlike test_one_command_vite.py:101-103, the ports of Next and the proxy are not checked to be free after stopping. The process check came out clean, but the test would not catch an orphaned next-server listener, and the kill-on-timeout path signals only the parent.
- tests/test_one_command_next.py:1220 -- console errors that are not hydration-related are dropped without being quoted. The brief (step 6) asks that unrelated overlay logs be quoted in the report; the report does not say whether any appeared.
- Brief says write the changed css with LF; the test preserves the file's own line endings (a replace on the original bytes). This is better for byte-for-byte restore and harmless; noted only as a literal departure.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every briefed step is implemented, and the one deviation (connected or live badge state) is sound and matches the Vite test. The module passes, the HMR/no-reload proof is real, and no process or fixture changes were left behind. Findings are Minor polish only.
