### Spec Compliance
- PASS: Build line. `apply(config, { command })` is a function returning `command === 'serve'`; prints BUILD_LINE once per process, only on build (vite-plugin.js apply, diff lines 232-238). Exact text asserted in vite-plugin.test.js and, via the real Vite 7 and 8 builds, `result.stdout.count(BUILD_LINE) == 1` in test_vite_build_guarantee.py; both pass in my run.
- PASS: Host refusal. `configResolved` throws HOST_ERROR for anything outside [undefined, 'localhost', '127.0.0.1', '::1'] (vite-plugin.js:243). Node tests cover true, '0.0.0.0', '::', two LAN addresses, a hostname and '' (refused) and the four accepted values, for both the standalone and the command's instance. Real bin: exit 1, `stderr.strip() == HOST_ERROR`, no `at ` line, process ended (HostRefusalTest passes).
- PASS: The check sits before the stand-down test and before `if (!standalone) return`, so a CLI run whose project config sets server.host:true is refused (the command's own copy throws). The implementer's choice is right: after the stand-down it would let the CLI run on an open host whenever the config also carries the plugin. Studio is closed first by the existing catch in run-vite.js (server is undefined, studio.close() runs); cli.js prints only `error.message` and returns 1.
- PASS: Start lines. Standalone prints `  Font Kit Studio · dev only` then `  Open: <url>` (vite-plugin.js:130-131). Node test pins order, once, and text.
- PASS: Existing-bridge warning. `loadsOwnBridge` matches a `<script ... src=...fontkit-bridge...>` (any quoting, case, spacing); `data-src`, inline text, `<link>` do not match. The plugin checks the html given to `transformIndexHtml` before its tag is returned, and the proxy checks the buffered original before `insertTag`, so our own injected tag (`/@fontkit/fontkit-bridge.js`) can never trigger it. Tag is still added; once across two pages (plugin and proxy tests).
- PASS: CSP check. Precedence script-src-elem > script-src > default-src, first occurrence of a directive wins, `'strict-dynamic'` blocks, none of 'self' / * / http: blocks, case-insensitive, several policies (comma, array, meta) block if any does, Report-Only header ignored (proxy tests, plugin tests), report-only meta not read. 27 value cases in csp.test.js. Exact text constants asserted.
- PASS: Warnings once per run through the new `log` option; runProxy and runVite pass `err`, so they never reach stdout (run-proxy.test.js asserts err only). By hand on fixtures/vite-react with the real command: two page loads, one tag each, no warning on stdout or stderr.
- PASS: Items 6 and 7. cli.test.js already asserts the two full texts (report names lines 64-71, 82-89); no new element, attribute or style is added.
- PASS: Rule-4 browser test. Body element lists equal direct vs proxied, head has 0 vs 1 bridge tag, no `[data-fontkit-font]`, body list still equal inside the frame after a live 56px edit; the stderr of a clean page is empty. CSP variant: nonce-only policy, helper stderr shows CSP line exactly once (second `get` raises Empty), tag present in frame, badge never Connected within 5 s.
- PASS: B3b's dedupe assertion (test_one_command_vite.py:73-78) now counts `Font Kit Studio · dev only` == 1 and `Open:` == 1 after stripping indentation, and rejects any indented line. It stays meaningful: a standalone copy that did not stand down would add an indented pair and make both counts 2.
- PASS: `.gitignore` has `fixtures/*/.fks-*/`; after the run no `.fks-*` folder exists in the worktree and `git status` shows no stray files.
- PASS: No "fontkit" bare in new messages other than the mandated `fontkit-bridge.js` / `npx fontkitstudio` inside the briefed texts.

### Checks run
- Whole Node package -> `npm --prefix C:/fks/tB6/packages/fontkitstudio test` -> tests 197, pass 195, fail 0, skipped 2.
- Python modules -> `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_messages test_one_command_vite test_vite_build_guarantee -v` -> 7 tests OK. `test_support` -> 34 OK. `ruff check .` -> All checks passed.
- Real command, no false warning -> ran bin in fixtures/vite-react, fetched the proxied target page twice -> start lines `Font Kit Studio · dev only` / `Open: ...`, no stderr, no warning. Stopped by PID (my first script crashed on a cp1252 print and left PID 9352 running; I killed it by PID and re-checked: no node process mentioning tB6 remains).
- Sibling copies of the old standalone start line `  Font Kit Studio: <url>` and of `apply: 'serve'` -> grep of live md/js/py -> only point-in-time briefs, reports and progress records (frozen by ruling 5); no live doc is made false.
- Guards in tests -> grep for `page.content`, `innerHTML`, `sleep`, `wait_for_timeout` in tests/test_one_command_messages.py -> none.
- I did not rerun the report's mutations; I read the assertions behind each (exact-text, count, exit status, negative wait) and they would fail if the check were removed.

### Strengths
- csp.js is a pure module with 27 value cases covering precedence, case, lists and non-strings; plugin and proxy share the same message constants, so the texts cannot drift.
- The host test goes through the real bin with a temp project in the fixture and asserts the whole of stderr, not just a substring, so a stack or a second line fails it.
- The proxy's own-bridge and CSP checks run on the original buffer, so our injected tag cannot cause a self-warning.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_one_command_messages.py:950-951: `errors.get(timeout=1)` to prove "once" is a second fixed negative wait (1 s); the brief names the 5 s wait as the only one. Cheap and bounded, but a stricter option is to stop the helper first and read its drained stderr.
- tests/test_one_command_messages.py:922-924: "head gained only the one tag" is shown as count 0 vs 1 of the bridge tag plus no `[data-fontkit-font]`, not as an equal list of the other head children. Matches the brief's wording; a head child-list comparison (minus the tag) would be a stronger rule-4 proof.
- src/csp.js:36-38: a host-source policy such as `script-src http://localhost:5173` (or `localhost:*`) warns in plugin mode, though the bridge is served from that same origin and is allowed. Rare in dev setups, the warning text only says "add 'self'", and the brief's rule is exactly 'self' / * / http:, so this is a known limit, not a defect. In proxy mode that policy does block, so the warning is right there. `script-src 'self' 'unsafe-eval'` correctly does not warn.
- src/vite-plugin.js:243: `'[::1]'` (the bracketed form some users write for server.host) is refused although it is loopback. Brief lists `'::1'` only, so this errs safe; the error text tells the user what to remove.
- Plugin's `server.headers` is the only plugin-side header source; a CSP set by the app's own middleware is seen only through meta tags. The implementer named this; fine.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every briefed text and behaviour is implemented and pinned by tests that fail without the check, the real command refuses a network host in the one line with exit 1 and no stack, and normal pages produce no warning. Only minor polish remains.
