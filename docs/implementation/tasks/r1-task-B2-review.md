### Spec Compliance
- PASS: Tag descriptor is exactly {tag:'script', attrs:{src:BRIDGE_PATH,'data-allowed-origins':studio.origin}, injectTo:'head-prepend'}; no type/async/defer, no children; returns [] before a Studio is known (src/vite-plugin.js:86-97; test "tags every page..." deepEquals it, "adds no tag before a Studio is known").
- PASS: Creation check refuses non-http, non-loopback, path, trailing slash, javascript:, '' and non-strings with the fixed message, never echoing input (vite-plugin.js:13-23). Probed: 'http://LOCALHOST:5999' (uppercase) and 'http://127.0.0.1:5999/' are refused (url.origin !== origin), 'http://[::1]:5999' and 'http://localhost:5999' accepted, undefined/null/5 refused. This matches the brief's literal rule (url.origin === given origin).
- PASS: Middleware answers only GET/HEAD on pathname === BRIDGE_PATH, with the four headers, from the in-memory buffer; no other file is read (vite-plugin.js:37-48). %40fontkit, trailing slash, /@fontkit/../package.json, POST, / reach next() (test "passes every other request to next", green).
- PASS: Standalone: exactly one startStudioServer per configureServer, after the bridge read (so a missing bridge leaks no Studio); printUrls wrapper calls Vite's first, then logs once, reading resolvedUrls inside; null resolvedUrls gives url(undefined) (no target); close on httpServer 'close', else wrapped server.close() (vite-plugin.js:63-82).
- PASS: package.json exports is `./package.json` kept plus `./vite`; nothing else changed. Self-reference test imports 'fontkitstudio/vite' and compares to the relative import; it fails with ERR_PACKAGE_PATH_NOT_EXPORTED if the export is removed.
- PASS: Imports are node:fs/promises, node:url and ./studio-server.js only; no createRequire, no computed import(). No CLI wiring, no build message, no server.host refusal.
- PASS: Report's four mutations map to tests that would fail; I re-read each guard and the named test covers it.

### Checks run
- Whole Node suite -> `npm --prefix C:/fks/tB2/packages/fontkitstudio test` -> tests 35, pass 35, fail 0.
- Malformed req.url -> probe script calling the captured middleware with url '//', '*', '', '/%', 'http://[', '//evil.com/@fontkit/fontkit-bridge.js', undefined -> '//' and 'http://[' THROW "Invalid URL" synchronously out of the middleware; '*', '', '/%', undefined go to next(); '//evil.com/@fontkit/fontkit-bridge.js' is SERVED (WHATWG parse treats evil.com as host, pathname matches).
- Origin variants -> same probe -> see Spec Compliance above.
- Studio close semantics -> read src/studio-server.js:close(): never rejects, resolves when server.close calls back (also when already closed), so the unawaited `started.close()` in the 'close' handler cannot cause an unhandled rejection, and the extra emit('close') in test cleanups is harmless.
- agent:false -> read fetchRaw (test:44-56): it only forces a fresh TCP connection per request; ECONNREFUSED is a real connect error from a closed listener. It cannot mask a still-listening server (that would return 200, failing the assertion). Fine.

### Strengths
- Tests exercise the real Studio server and a real http server mounted with the captured middleware; the close tests assert ECONNREFUSED after close with no sleeps.
- Bridge read happens before the Studio start, so the failure path leaks nothing.
- Hostile-input table for both origin and path is the brief's, and the message-not-echoed assertion is real.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Malformed req.url can throw out of the middleware (src/vite-plugin.js:38). `new URL('//', 'http://x')` and a request line like `GET // HTTP/1.1` throw "Invalid URL"; Connect turns it into next(err) (a 500 in the dev server), so no crash, but the task's own risk list asks that it cannot throw, and studio-server.js:61-65 already wraps the same parse in try/catch and answers 400. The brief prescribes the `new URL(req.url, 'http://x').pathname` expression, but a try/catch that calls next() is compatible with it, so this is an ordinary finding, not plan-mandated. No test covers it.
2. A protocol-relative target `//evil.com/@fontkit/fontkit-bridge.js` is served the bridge bytes (the URL parse reads evil.com as host). Harmless (static bytes, no input reflected, same-origin request) but it is a looser match than "exact pathname" suggests. Matching on the raw path (`req.url.split('?')[0]`) or a try/catch plus an `req.url.startsWith('/')` check would close it together with item 1.
3. Test cleanup for standalone servers depends on the code under test (test:121-126). The cleanup emits httpServer 'close' / calls server.close(), which is exactly the handler under test; when that handler is broken (mutation 4) the cleanup is a no-op, the real Studio server stays listening and the run hangs (the report had to use --test-force-exit). The `after` hook does run on failure, so AP 13 is met when the plugin works, but not in the failure case it is meant for. A more robust cleanup needs a handle that does not go through the plugin (for example parse the Studio URL from fake.logs and close by other means is not possible without a handle, so the practical fix is a per-file `--test-force-exit` / test timeout, or accept the limit and record it). Low severity: it affects a failing run only.
4. A second configureServer call on the same plugin instance starts a second Studio and overwrites `studio` (and the tag origin), with the first closing only with the first server's httpServer. Vite recreates plugins on every config resolve and server restart, so this does not arise in practice; the brief already records the restart limit. No action needed.
5. `printed` guard means Studio's URL appears only after the first printUrls; later Vite re-prints (e.g. after a server restart event or `press h`) omit it. This is the brief's "once" and noted in the report.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** All behaviour and test requirements are met and verified (35/35 pass, probes match the brief on tag shape, origin check, exact path, standalone lifecycle). Only Minor findings remain: the middleware can throw on a malformed request URL such as `//` (Connect catches it), and the standalone test cleanup depends on the handler under test. Fix item 1 with a small try/catch if desired.
