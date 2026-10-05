### Spec Compliance
- PASS: runProxy start order, Studio closed when the proxy rejects (src/run-proxy.js:27-33), exact two lines (run-proxy.js:63-64), Studio URL target = proxy origin + pathname + search (run-proxy.js:36-37), open once after both lines and only when `open` (run-proxy.js:65), busy-port fallback text matches the brief character for character (run-proxy.js:23-25).
- PASS: signals SIGINT/SIGTERM (+SIGBREAK on win32) registered after both servers are up; close() removes them first, closes proxy then Studio (Studio in `finally`), memoised so a second call resolves (run-proxy.js:39-54).
- PASS: open-browser.js is spawn with an args array, `shell: false`, `detached`, `stdio: 'ignore'`, `unref()`, one-line message on 'error' (open-browser.js:12-20); URL is one argv entry on all three platform branches.
- PASS: upgrade handler (proxy.js:243-282): Host check (421) and origin-form check (400) both run before `connect()`; headers go through B4's `forwardHeaders` so host/origin/referer rewrites are identical to HTTP, including every loopback form of the proxy origin; `connection`/`upgrade` re-added; request line, headers, blank line, then `head` written on connect; pipes both ways; `error`/`close` on either side calls `drop` which destroys both and removes both from the Set; proxy `close()` destroys the Set (proxy.js:303). B4's HTTP code untouched (diff shows only an import, the new block and one line in close()).
- PASS: fixture: no inline script/style, no `style=`, no external URL (grep clean); ids `bs.hero.title` (h1), `bs.hero.lead` (p.lead), `bs.hero.cta` (button.btn.btn-primary); Bootstrap 5.3.8 headers in both vendored files, MIT LICENSE present, 0 sourceMappingURL, LF only.
- PASS: CSP server matches the brief (127.0.0.1:0, CSP on every response, daemon_threads, quiet log, caller shuts down). Node helper matches the brief (argv, open:false, closes on stdin end, exit 0).
- PASS: Python test is real: real Studio file, real fontkit-bridge.js, CSP header from the CSP server, `https://**/*` aborted, init script records securitypolicyviolation in every frame, Connected regex, title selection with one retry, keystroke typing, computed font-size 56px (fixture starts at 40px, so the wait is meaningful), violation lists empty in frame and Studio, no pageerror, CSP header equality and one tag via urllib. No page.content()/innerHTML. No fixed sleeps (`delay=60` is keystroke pacing, not a wait).
- PASS: no deviation from the brief needing a rule; the implementer's notes (utf-8 pipe decoding, `agent: false`, socket-wait timeouts) are test-side and sound.

### Checks run
- Upgrade, head bytes, Origin under another loopback form, upstream-close propagation -> scratch probe (outside the worktree) sending handshake + "HEADBYTES" in one write with Host localhost:<port> and Origin http://[::1]:<port> -> head bytes echoed back, upstream saw Origin http://127.0.0.1:<up> and its own Host, client socket closed when the upstream went away. Behaviour correct.
- Full node package suite -> `npm --prefix C:/fks/tB5/packages/fontkitstudio test` -> tests 95, pass 93, fail 0, skipped 2; the 2 skips are project.test.js:89,119 ("package.json above tmpdir"), not B5 files.
- Browser module -> `PYTHONPATH=tests python -m unittest test_one_command_proxy -v` -> 2 tests OK in real Chromium; process exited, no helper left behind.
- `python -m unittest test_support` -> 34 OK. `python -m ruff check .` -> All checks passed.
- Vendored files -> head of both, grep sourceMappingURL, CR count, LICENSE head -> 5.3.8, MIT, 0 map lines, LF.
- Cleanup order in Python setUp (LIFO): stop_helper (close stdin, wait 10 s, kill by handle, close stdout), server.shutdown, server_close, close_contexts. Correct.
- Listener/socket leak: upgraded Set is emptied by `drop`; `close()` destroys survivors; Agent is destroyed in the server.close callback; free agent sockets are unref'd by Node, so no process hold. Reasoned from source, plus the `close() destroys an open upgraded socket` test passing.
- Mutations were not re-run by me (read-only worktree); I judged each reported mutation against the assertions: Host check removal -> test expects exact 421 bytes, would get 101; Origin rewrite undone -> `seen.headers.origin === ws.origin` fails; studio.close removal -> `refuses(running.studioUrl)` fails; `if (true)` -> `quiet.opened` non-empty fails. All hold.

### Strengths
- The 421/400 tests assert the exact response bytes and that the upstream saw no upgrade.
- The close test proves the upgraded socket ends, with a 10 s guard so a regression fails instead of hanging.
- The SIGINT test restores-and-compares listener counts for every platform signal and drives the real handler through `process.emit`.
- The `open` test snapshots what `out` held at the moment `openUrl` ran, so it proves "after both lines".
- The rejected-proxy test frees a known port and rebinds it, a behavioural check of "no server left".

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- packages/fontkitstudio/test/proxy.test.js (WebSocket upgrade block): two guards in the brief's behaviour have no test: forwarding of `head` (proxy.js:277) and "upstream error/close destroys the client socket" (proxy.js:272-273). Deleting either leaves the suite green (my probe shows both work today). The handshake test writes the request alone, so `head` is always empty; the only close test starts from the proxy side. Add one case writing handshake plus a few bytes in one write, and one that closes the upstream and expects the client socket to end.
- proxy.test.js upgrade tests send Origin/Referer only in the 127.0.0.1 form; the other loopback forms rely on the shared `forwardHeaders` (covered by B4's HTTP tests), so this is safe but not asserted on upgrade.
- run-proxy.js:44-47 and the signal handlers: `close` is registered directly as the handler, so a rejected `proxy.close()` becomes an unhandled rejection with no message. Unlikely (the proxy close never rejects), but a `.catch` writing one line to `err` would be tidier.
- run-proxy.test.js "a target that is not local rejects...": the title says no Studio server is left but the body checks only empty out/err; the next test is the one that proves the port is freed. Rename or fold.
- Cleanup (AP 13): with `studio.close()` removed the failing test leaves a listener, so `node --test` fails the test and then waits for the event loop; the implementer is right that it needs `--test-force-exit` to terminate. The failure is reported, not masked, and the normal run leaks nothing; acceptable. If CI wall-clock matters, the package test script could pass `--test-force-exit` (not owned by B5, so not asked for).
- proxy.js close(): an upgrade event that fires after `close()` has iterated the Set would add a socket that is not destroyed. Needs a connection accepted just before close; negligible.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The brief is met in the code and I confirmed the upgrade path, head bytes, close propagation and the browser run directly. The remaining gaps are small test additions, not wrong behaviour.
