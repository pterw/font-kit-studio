### Spec Compliance
- PASS: `//` Location is resolved (as `http:` + value) and rewritten target -> proxy origin with path/query/hash kept (proxy.js:135-151). Probe: `//localhost:P/x` and `//127.0.0.1:P/x?a#b` -> `<proxy>/x...`.
- PASS: other origins untouched: `//evil.test/x`, `//localhost:<P+1>/x`, `https://localhost:P/x`, `//localhost:P.evil.test/x`, `//localhost.evil.test:P/x`, `//localhost:P@evil.test/x` (userinfo trick) all forwarded unchanged. Relative `/login` untouched.
- PASS: backslash forms: `\\localhost:P/x`, `/\localhost:P/x`, `\/localhost:P/x`, `http:\\localhost:P/x` are rewritten (WHATWG treats `\` as `/` for http); `\\evil.test/x` untouched; single `\localhost:P/x` correctly left alone (it is a path, not a network path).
- PASS (extension, noted): loopback-name equivalence on the target's port. It was not in the controller ruling, but it is declared in the report, small, and consistent with the Origin/Referer side (underProxy maps all of the proxy's loopback names to the target; this maps all of the target's loopback names to the proxy). It also fixes `http://localhost:P` when the target is `127.0.0.1:P`.
- PASS: scope: only `rewriteLocation` and its tests changed.

### Checks run
- RED real -> read old code (`parseUrl('//localhost:..')` has no base, throws, caught, header returned unchanged) against the new assertions in proxy.test.js:458-461 -> they fail on old code; the report's RED output matches. No edits made (read-only).
- Full package test -> `npm --prefix C:/fks/tC4/packages/fontkitstudio test` -> tests 204, pass 202, fail 0, skipped 2 (skips not in this diff).
- Hostile/edge Locations through a real proxy + fake upstream (scratchpad probe, 35 values, process stopped) -> results as listed above; also `//127.1:P`, `//0x7f.1:P`, `//LOCALHOST:P`, `///localhost:P/x`, `//[::1]:P/x`, `//user:pw@localhost:P/x` all -> proxy origin (credentials dropped), which is what a browser would reach; `//`, `//:`, `http://`, `//localhost:99999/x`, empty-host forms -> unchanged, no throw.
- Can the loopback equivalence map a non-target server -> proxy.js:139-146: the output is always `proxyOrigin + path`, never input-derived host; match requires http + loopback name + exactly targetPort. Only conceivable mismatch is a different listener on the same port under another loopback family (::1 vs 127.0.0.1), and the redirect came from the target itself. Not an open-redirect widening.
- Malformed Location never throws -> `parseUrl` wraps `new URL` in try/catch; the only other operations are a regex test and string concatenation of URL-normalised parts. Probe values above (`//`, `//:`, port 99999) returned 302 normally.

### Strengths
- Single decision point; the protocol check cannot be bypassed by `//` forms because the synthetic scheme is fixed to `http:`.
- Test covers rewrite via `localhost` and `127.0.0.1` names, foreign host, foreign port, and keeps the existing absolute/relative/other assertions.

### Issues
#### Critical
(none)
#### Important
(none)
#### Minor
- Test gaps against the new guards: no assertion for backslash-prefixed values, for the `location.protocol !== 'http:'` guard (e.g. `https://127.0.0.1:P/x`), or for an absolute `http://localhost:P` alias on a `127.0.0.1` target (proxy.test.js:458-461). Mutations removing the `[\\/]` part of the regex, the protocol check, or the alias would survive. One or two more upstream routes would close it.
- A tab/newline inside the value (`/<TAB>/localhost:P/x`) is stripped by browser URL parsing into a network path but is not detected here (probed: forwarded unchanged). Requires an upstream that emits a control character in Location; negligible.
- Trailing-dot host `//localhost.:P/x` is not mapped (browser resolves it to loopback). Negligible.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** The fix does what the Codex finding and the ruling ask, is safe on every hostile input probed, never throws, and the full package suite passes; only test-coverage polish remains.
