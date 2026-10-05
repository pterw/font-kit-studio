### Spec Compliance
- PASS: (a) the hash is appended to the target URL given to studio.url (packages/fontkitstudio/src/run-proxy.js:44).
- PASS: (b) open-browser.js:16-25 reports on 'error' and on 'exit' with code !== 0 or a signal, through one guarded report(); at most one line per call. detached, stdio 'ignore', shell false and unref() are unchanged (open-browser.js:15, 26).
- PASS: only the four named files changed; no other source touched; versions, deps and shared files untouched.

### Checks run
- Hash reaches Studio's `target` intact -> node probe: searchParams.set('target', origin+path+search+hash) gives `...?target=http%3A%2F%2F127.0.0.1%3A9%2Fapp%3Fx%3D1%23%2Fsettings`, and searchParams.get decodes to `http://127.0.0.1:9/app?x=1#/settings` -> intact. The new test asserts the same on running.studioUrl.
- Studio keeps a fragment -> read fontkit-studio.html:6165-6171 (reads `target` from location.search, safeTargetUrl, connectTargetApp), 3421-3426 (new URL(...) keeps hash; only the scheme is checked), 3871-3875 (iframe.src = resolved.href, hash kept; expectedOrigin = origin), 3776-3778 (isStudioDocument strips ?/# only for the self-embed compare). Studio neither strips nor rejects a hash. The fragment is never sent to the proxy (client-side only), so proxy forwarding is unaffected.
- No new URL-sink risk -> the hash is appended after a URL parse of the CLI argument and is URL-encoded into one query value; scheme and host cannot change.
- Sibling path: run-vite.js:42 passes the Vite appUrl, which carries no user hash; no change needed.
- `exit` listener on an unref'd detached child -> read open-browser.js: a listener does not ref the handle, so it cannot keep the command alive. If the command has already stopped, the event never fires and nothing prints. While it runs (Studio/proxy servers hold the loop open), a late line goes to stderr only. No consequence that matters.
- No duplicate after error then exit -> `reported` flag (open-browser.js:17-19); test 'reports once when error is followed by exit' covers it.
- Tests -> `npm --prefix C:/fks/tC2/packages/fontkitstudio test`: tests 204, pass 202, fail 0, skipped 2. Did not re-run the RED/mutations; by reading, the exit-1, signal and hash tests cannot pass at HEAD (no exit listener, no hash in URL), 'stays silent on exit 0' fails if the code check is dropped, and the once-only test fails if the guard is dropped. The report's RED/mutation results are consistent with that.

### Strengths
- Exit semantics are exact: code 0 silent, nonzero or signal reported, once.
- Tests drive the real function through the fake child's EventEmitter and assert the exact stderr line; the hash test asserts the decoded target value, not just a call.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
- packages/fontkitstudio/test/open-browser.test.js:45 duplicates the message literal from the existing test at line 42 (LINE constant is defined after it); could share the constant. Cosmetic.
- packages/fontkitstudio/test/run-proxy.test.js:113-118: `running.close()` is not in a finally, so a failed assertion leaks the run and cascades into the later SIGINT test (the report notes this cascade). Matches the surrounding tests' pattern; fixing it would be an improvement, not a defect of this change.
- Real-world note, not a defect: some xdg-open setups exit 0 without a browser, and a terminal browser can make it exit 0 later; the fix cannot catch those, which is within what the Codex finding asked.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Both Codex P2 findings are fixed minimally and correctly; Studio's own target handling preserves the fragment, the exit handler cannot hold the process open or double-print, and the new tests would fail without the fixes.
