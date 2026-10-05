### Spec Compliance
- PASS: `blocksSameOriginScript(policy, pageOrigin)` has the binding signature; with no or an unusable origin it behaves as before (csp.js:62-70; the old 'self'/'*'/'http:' tests are untouched, and a new test covers undefined, 'nonsense', https and a number).
- PASS: deciding directive is still the first of script-src-elem / script-src / default-src (csp.js:40-47); 'strict-dynamic' still blocks before any host matching (csp.js:48).
- PASS: scheme is http or none (csp.js:30), exact host (31), port equal or `:*` or default 80 (29, 32), path none / prefix ending in `/` / exact bridge path (33-34). Malformed gives no match (28, 17-20). Page origin that is not http gives no match (csp.js:16).
- PASS: plugin keeps header policies (vite-plugin.js:103) and decides at transformIndexHtml with headers plus that page's meta policies together (vite-plugin.js:152-160). Meta is per page as before.
- PASS: proxy passes `proxyOrigin` (proxy.js:126). The page is served from the proxy, so a policy naming the target still warns.
- PASS: tests listed in the brief are present: csp allows (10) and blocks (18, including hostile cases, two policies as comma list and array), plugin own-origin / other-port-once / meta / before-listen, proxy target-port warns and proxy-origin does not. The report shows the four mutations; not rerun by me (see Checks).
- PASS: nothing outside Owns changed (6 files, all owned). Zero dependencies kept.
- CANNOT VERIFY FROM DIFF: the Python one-command tests (6 OK) and ruff, taken from the report.

### Checks run
- Origin choice, standalone -> vite-plugin.js:131-133 -> Studio's "Open:" line uses `server.resolvedUrls.local[0]`, the same value the plugin reads at vite-plugin.js:156. Same origin.
- Origin choice, command mode -> run-vite.js:35,47 -> `appUrl = server.resolvedUrls.local[0]` of the same server object that `configureServer` stored in `viteServer` (standDown is false in command mode, vite-plugin.js:111-112). Read lazily at transform time, so after listen. Same origin.
- Origin when unknown (middleware mode, before listen, https server) -> `new URL(undefined)` throws, caught, origin undefined; https gives no origin -> old behaviour, warning stays. Fail-safe.
- Proxy origin -> proxy.js:339 `proxyOrigin = http://<host>:<actualPort>`, and run-proxy.js:44 builds Studio's URL from `proxy.origin`. The browser loads the page at the proxy origin. `proxyOrigin` is a `let` assigned before any request is served (TDZ not a risk; it is already used at proxy.js:149).
- CSP3 matching, hostile inputs against the real function (`node` on csp.js, scratch probe, about 55 cases). Allowed correctly: scheme-less on http page, `:80` / no port against a port-80 page, `:*`, `LOCALHOST` case, exact bridge path, `/` and `/@fontkit/` prefixes, 'none' mixed with a matching host (CSP3 ignores 'none' unless alone), `'unsafe-inline'` + matching host, script-src-elem over script-src, default-src fallback.
- Blocks correctly (warning stays): other port, port prefix/suffix (`51730`, `517`), `localhost.`, `localhost` vs `127.0.0.1`, https scheme, `https:`, `data://`, `*:5173`, `http://*:5173`, userinfo (`user@localhost`), `@evil.com`, `host:5173:5173`, `http://localhost:`, `.evil.com` suffix, `'strict-dynamic'` in any case, path `/js/`, `/@`, `//`, `/../`, bridge path with trailing `/`, `?x`, `#x`, `.jsx`, `%40fontkit/`, first-directive-wins (`script-src 'none'; script-src ok`), `script-src-elem 'none'` over a matching `script-src`, `__proto__` / `constructor` as hosts, NUL byte, a non-http page origin (`ws:`), array with non-strings. `[::1]` matches itself; `[0:0:0:0:0:0:0:1]` does not (false warning, safe).
- Case in the path -> probe -> `script-src localhost:5173/@FONTKIT/` and `.../@FONTKIT/FONTKIT-BRIDGE.JS` return false (allowed). See Minor 1.
- Tests -> `npm --prefix C:/fks/t7c/packages/fontkitstudio test` -> pass 243, fail 0, skipped 2; nothing left running.
- Docs -> grep for `script-src` in live .md/.py outside point-in-time dirs -> CSP_MESSAGE text is unchanged and still matches tests/test_one_command_messages.py:34; no doc claims the old rule. Nothing to correct.
- Mutations -> not rerun; the tests exercise every mutated guard directly (port: `localhost:5174`/`localhost` blocks; scheme: `https://` blocks; path: `/js/` blocks; plugin no origin: own-origin test expects no line).

### Strengths
- Fails closed: any unparsable source, non-http page origin or missing origin leaves the warning on; no probe produced a false negative apart from Minor 1.
- Plugin and proxy origin choices match what Studio opens, in both modes, and the proxy case is tested the right way round (target port warns, proxy origin does not).
- Header and meta policies are still evaluated independently and combined with `some`, so one blocking policy of several still warns.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. csp.js:42 + 34 -- the whole policy is lower-cased before matching, so the path of a source is compared without case. CSP3 compares paths case-sensitively, so `script-src localhost:5173/@FONTKIT/` blocks the bridge in a browser (the path is `/@fontkit/...`) but returns "allowed" here: a false negative (confirmed by probe). Contrived (needs a wrong-case path in a policy), and the brief's "compared without case" invites it, but the fix is cheap: keep the original-case path (for example match the path against the un-lowered source, or lower-case only scheme and host) and add a blocks case such as `localhost:5173/@FONTKIT/`.
2. csp.js:10 -- `*:5173` and `http://*:5173` (valid CSP3, wildcard host) are treated as not matching, so they still warn although a browser would allow. Safe direction (false warning), noted only so a later reader does not take it as a bug.

### Plan-mandated (for the owner)
- None. (Minor 1 is arguably invited by the brief's "compared without case", but that phrase is about the page origin; the implementer could have kept the path case-sensitive, so it is listed as an ordinary finding.)

### Assessment
**Task quality:** Approved
**Reasoning:** The behaviour matches the brief, fails closed on every hostile input I tried, and the plugin and proxy pass the origin the browser really loads; the one false negative found (wrong-case path) is Minor and contrived.
