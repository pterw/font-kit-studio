### Spec Compliance
- PASS: startProxy interface, defaults and return shape match the brief (src/proxy.js:41-48, 238-250).
- PASS: start-up refusals in brief order with fixed texts; target/studio texts never echo input (proxy.js:49-83). Host refusal echoes `<host>` as the brief's text says; the host is a caller option, not request input.
- PASS: per-request order is Host (421), origin-form (400), exact bridge path, forward (proxy.js:211-228).
- PASS: forward rewrites only host, accept-encoding, origin, referer and drops the seven hop-by-hop headers; one keep-alive Agent, destroyed in close() (proxy.js:104-117, 89, 244).
- PASS: tagged/untagged split matches steps 5-7: 200 + exact text/html + identity encoding + non-HEAD; over-limit writes buffered bytes then pipes the rest; location rewrite on both paths; 502 fixed text (proxy.js:119-198).
- PASS: tag insertion on latin1 with head, html, doctype, 0 order; `<header>` not matched (proxy.js:31-39). Doctype fallback tolerating BOM/whitespace is a small addition, harmless.
- PASS: no WebSocket, runner, CLI or extra messages. Owns only the three listed files; imports are node:* only.
- PASS: all 13 test cases are present plus extras (HEAD of bridge, POST to bridge path, `OPTIONS *`, chunked overflow, body without length, foreign referer).
- CANNOT VERIFY FROM DIFF: the seven mutation runs (reported only). I read the tests and each asserts the guarded behaviour; I did not re-run the mutations.

### Checks run
- Suite -> `npm --prefix C:/fks/tB4/packages/fontkitstudio test` -> 52 pass, fail 0.
- Open proxy -> raw-socket probe (scratchpad/probe.mjs) -> `GET http://example.com/` with bad Host = 421; with good Host = 400; upstream saw nothing. `CONNECT` gets a silent socket close (no listener), with good or bad Host. `GET //example.com/x` is forwarded as a path to the fixed target with `host` = target (upstream log), so nothing can change the upstream host or port. Upstream host/port come only from `target` (proxy.js:85-87).
- Host first -> probe: empty Host (HTTP/1.0 no Host) 421; `evil@127.0.0.1:<port>` 421; duplicate Host headers use the first (Node), forwarded host is the single rewritten one. Host is checked before the request-line check (abs-form with bad Host = 421).
- Chunked upstream HTML without content-length, tagged -> probe -> client got content-length 127 and cache-control no-store, tag present. Correct. (Not covered by an existing test; see Minor 3.)
- Duplicate Set-Cookie -> probe -> both preserved on a tagged page.
- Upstream reset mid-body -> probe: tagged page gives an empty reset (no half page), untagged gives the bytes sent then a reset (the connection is destroyed, not a clean end). No uncaught exception.
- Client abort mid-request body and mid-response -> probe2 -> upstream connection count returns to 0, no uncaught exception.
- close() with open keep-alive client sockets, an in-flight hung request and a slow body -> probe2 -> resolves in ~1 ms, upstream sees 0 connections afterwards (agent destroyed, proxied requests destroyed).
- Origin under a localhost Host -> probe -> `Host: localhost:<port>` + `Origin: http://localhost:<port>` reaches upstream with the origin unchanged (see Minor 1).
- Trailing whitespace/CRLF -> grep -> LF only; one whitespace-only line at proxy.js:213.
- Leak on refusal tests -> read proxy.test.js:396-451: the refusal tests use `assert.rejects(startProxy(...))` with no cleanup. If the check regresses, startProxy resolves, a listening server is left, and `node --test` never exits. This is the hang the implementer saw (reported as "run then hangs").

### Strengths
- Proxy is small and flat; every decision sits in one place with the upstream target fixed at start-up.
- Raw `req.url` comparison for the bridge path (proxy.js:217) is better than a normalised pathname. A normalised URL would serve the bridge for `/@fontkit/../@fontkit/fontkit-bridge.js` and the brief itself says look-alike paths must go to the target. Browsers normalise before sending, so no real client is affected. The test pins it (proxy.test.js:249-264). Keep it.
- The Referer boundary (proxy.js:112-115) is correct and better: without it `http://127.0.0.1:123` would match a referer for port 1234, and a pointless rewrite would leak a wrong origin. Tested (proxy.test.js:337-344).
- Failure handling is correct: upstream errors destroy the response rather than ending it cleanly, `res.close` destroys the upstream request, the `req` error handler exists. No crash and no socket leak in probes.
- Tests compare bytes (UTF-8 `cafe` with accent around the tag, PNG random bytes, gzip bytes) and assert the recorded upstream URL for every look-alike path.

### Issues
#### Critical
(none)

#### Important
1. Test cleanup depends on the code under test being correct (AP 13). proxy.test.js:401-451 (target refusals, studio refusals, host `0.0.0.0`, missing bridge): a regression in any of these checks leaves a listening server (the host `0.0.0.0` case leaves a non-loopback listener), `after` does not know about it, and the whole test run hangs instead of failing. The Host check and similar mutation tests do fail cleanly, but the guard being tested is exactly the one whose failure hangs. Fix: a helper `refuses(options, expectedMessage)` that does `try { const p = await startProxy(options); closers.push(() => p.close()); assert.fail(...) } catch`, or start through a wrapper that pushes any resolved proxy onto `closers`, with `closers` drained in `after` (it already is). Also run `after` cleanup so `small`, `proxy` and `upstream` close even if one `close()` throws (proxy.test.js:93-99 awaits sequentially, so a throw skips the rest); `try/finally` or `Promise.allSettled` would do it.

#### Minor
1. Origin/Referer rewrite compares to the literal `http://127.0.0.1:<port>` (proxy.js:111-112) although the Host check also admits `localhost:<port>` and `[::1]:<port>`. Studio opens the 127.0.0.1 origin, so the normal path is covered; but a user who types `localhost:<port>` (or a Next.js server action, which compares Origin to Host) gets a mismatch with the rewritten Host. Rewriting when the origin equals any of the three allowed forms is safe (the Host check already established the request is for this proxy) and costs a few lines; the 3 allowed origins can be built next to `allowedHosts`. I would do it in B5 or now; brief-literal behaviour is not wrong. Add a test with `Host: localhost:<port>` + matching Origin.
2. proxy.js:213 is a whitespace-only line with four spaces. `allowedHosts` (proxy.js:212) is rebuilt on every request; build it once after `actualPort` is known.
3. Missing coverage the brief does not require but the risk list names: upstream reset mid-body, client abort, `close()` with a live keep-alive connection, `//host/path` forwarded as a path only, HTML without content-length tagged under the default limit (proxy.test.js only uses `/chunked` under `maxHtmlBytes: 64`), `host: '::1'` start-up. I probed all but the last by hand and they behave; one or two regression tests (reset mid-body; close with open connection) would lock the most valuable ones. The `upstream.js` helper cannot produce a reset today.
4. Hop-by-hop handling is by fixed list only; a `Connection: x-foo` token naming extra headers is not honoured (proxy.js:11-19, 104-108). Acceptable for a local dev proxy; noted.
5. Pages in a non-ASCII-compatible charset (UTF-16) are tagged at offset 0 with ASCII bytes, which corrupts them (proxy.js:31-39). Brief mandates this algorithm; unlikely for dev servers; no action.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Trust-boundary behaviour is correct in every probe (no open proxy, Host first, byte-exact passthrough, correct tagging and lengths, clean close, no crash on aborts), and both additions beyond the brief are improvements. The one Important is test hygiene: refusal tests leak a server when the guard regresses, so a real regression hangs the suite instead of failing it (AP 13), as the implementer's own mutation run showed. Verdict wording for the dispatcher: Approved with fixes (Important 1 plus Minor 1 recommended).
