### Spec Compliance
- PASS: Token signal is `Boolean(new URLSearchParams(location.search).get("token"))`, read once, no probing; empty token is false (fontkit-studio.html:3790).
- PASS: Sync miss under the package says "Sync to file is not available under npx fontkitstudio. Use Copy or Download in the CSS tab." (fontkit-studio.html:3791-3793, 5683-5684). It does reach the catch: the package server answers /__fontkit/status (no token, so 403, else 404) and `!response.ok` throws (studio-server.js:89-91, 98-ish; fontkit-studio.html:5665). Control stays disabled; test checks title, hint line and is_disabled.
- PASS: `#bridgeHint` gets the exact brief wording, via `textContent` (fontkit-studio.html:3842). The script-tag advice and the `#bridgeHintServe` span are gone under the package. "Font Kit Studio" is used where the product is named (D040).
- PASS: Badge tooltip changed to "npx fontkitstudio adds the bridge to the page itself." (fontkit-studio.html:3692). It was the same script-tag advice, so this is in scope. The const is read only when `hint` is true; `setBridgeStatus(..., true)` is called only from the no-bridge timer (3767), after line 3790 has run, so there is no TDZ risk.
- PASS: `BLOCKED_LOOPBACK_TEXT` is unreachable under the package. It needs `isBlockedLoopbackReach` (3808), which returns false when Studio's hostname is loopback. The package server only binds loopback and rejects any Host not in `allowedHosts` with 421 (studio-server.js:43, 72-73). Left unchanged, with a comment, and the reason is in the report as the brief asked.
- PASS: Without a token every string is byte for byte as before (the `else` branches are the original literals; the hint HTML is untouched). Tests cover no token, an empty token and serve.py.
- PASS: Text goes through `textContent`/`title`. The token value itself is never rendered or used beyond truthiness, so a hostile `token` value (or `serve.py?token=x`) can only switch wording.
- PASS: No new content beyond the brief except the badge tooltip, which is allowed.

### Checks run
- Does the Sync miss really happen under the package -> read studio-server.js:56-101 -> yes, any path other than /fontkit-studio.html is 404, and tokenless requests are 403.
- Can BLOCKED_LOOPBACK_TEXT show under the package -> read fontkit-studio.html:3808-3812 and studio-server.js:43,72 -> no (loopback host only).
- Other package-visible strings with serve.py or bridge advice -> grep fontkit-studio.html for serve.py, bridge.js, dev server -> remaining ones are file:// Sync text (5661; no token on file://, so not reachable under the package), the BLOCKED text (unreachable), and 4937 (see Minor).
- Is a target always present under the package -> run-proxy.js:44 and run-vite.js:47 always pass a target to `studio.url()`.
- Tests -> `PYTHONPATH=tests python -m unittest test_studio_npx_hints -v` in C:/fks/t8b -> Ran 3 tests, OK.
- Mutation shown in the report (`SERVED_BY_PACKAGE = false`) fails the package test with the exact bridge-hint mismatch. I did not rerun it. Mutating the other way (always true) would break both serve.py and no-token tests, which assert old text.
- Other tests that read these strings (test_studio_first_run SERVE_LINE and BLOCKED, test_live_integration) are in the report's OK list; I did not rerun them.

### Strengths
- Package test uses the package's own helper and a port with no listener; assertions are on rendered text and attributes, never page source. The no-token handler (`PlainStudioHandler`) gives a real 404 for status without needing serve.py.
- Both signs of the token are guarded: package wording with a token, old wording without or with an empty one, and serve.py unchanged.
- Cleanup is by handle (stdin close, wait, kill on timeout; server shutdown, close and join).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_npx_hints.py:166-170: the badge tooltip is only checked with `assertNotIn`, so an empty title or any wrong wording passes. The `NPX_BRIDGE_TITLE` string is never asserted exactly (the brief did not ask, but the implementer added the string). Add `assertEqual(badge title, "npx fontkitstudio adds the bridge to the page itself.")`.
- tests/test_studio_npx_hints.py:170: `#bridgeHintServe` is detached from the DOM once `bridgeHint.textContent` is set (fontkit-studio.html:3842), so `is_visible()` is False vacuously. It would pass if the code forgot to hide the span. The meaningful assertion is already the exact hint text. Drop it or assert the element count is 0. The `bridgeHintServe.hidden = true` in 3842 acts on a detached node and is dead code.
- fontkit-studio.html:3788-3793: the new comment and constants were inserted between the comment "Only the two hostnames are known..." (3787) and its `BLOCKED_LOOPBACK_TEXT` const (3794), separating them.
- fontkit-studio.html:4937: the empty-state inspector line "Enter the URL of a localhost app that loads fontkit-bridge.js..." can show under the package if the user disconnects, and the package adds the bridge itself. It names no serve.py and is not wrong, so it is out of the brief's list. Mention it for the owner.
- With `file://` and a token the hint would use npx wording while Sync keeps serve.py wording (hostile or odd URL only; wording only).

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every package-visible message either has package wording or is shown unreachable (loopback-only host check). The token is a pure wording switch, text goes through textContent, and no-token strings are unchanged. Tests assert rendered text under both servers and fail when the token is ignored; only minor test-strength gaps remain.
