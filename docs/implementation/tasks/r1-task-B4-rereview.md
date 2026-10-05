### Spec Compliance
- PASS: Fix 1. Refusal tests go through `mustRefuse` (proxy.test.js:443-453), which pushes a wrongly started proxy onto `closers` and then fails. `after` (proxy.test.js:429-441) closes proxy, small, upstream and all closers, each in its own try/catch, inside try/finally that always removes the temp dir. A regressed guard fails AND exits (see Checks).
- PASS: Fix 2. `underProxy` (proxy.js:113-121) matches the three loopback forms of the proxy's own origin (`ownOrigins`, proxy.js:254), lowercases the value for the compare, and requires a boundary (end, `/`, `?`, `#`). Origin rewrites only on exact match (proxy.js:130); Referer rewrites on prefix plus boundary (proxy.js:131-134). Test at proxy.test.js:712-736 covers localhost Origin, `LOCALHOST` Referer, `[::1]`, and `localhost:<port+1>` untouched; "evil.test" origin untouched at proxy.test.js:703-710.
- PASS: Fix 3. No trailing whitespace in the three files (grep ' $' -> 0 each; no CR). `allowedHosts` and `ownOrigins` are built once after listen (proxy.js:252-254). The Host check is still the first per-request check (proxy.js:230-231, before the origin-form check at 232) and still tested (proxy.test.js:641-657).
- PASS: Fix 4. `//evil.test/x` test (proxy.test.js:738-747) uses a raw socket, asserts 404, that upstream received exactly one more request with url `//evil.test/x` and Host = upstream host. Chunked HTML under the limit test (proxy.test.js:570-580) asserts exact tagged bytes, `content-length` equal to the new length, and no `transfer-encoding`; the `/chunked-small` route is truly chunked (upstream.js:304 leaves it unframed-by-length).
- PASS: Nothing else changed. The tree equals the regenerated patch byte for byte (`git diff 8bf379e -- packages` vs task-B4-code.patch: no difference). proxy.js outside the fix areas matches what the prior review read (everything shifted by about +8 lines from the added state; Host/request-line/bridge/forward/tagging/502/close logic is the same). Same three files only, imports node:* only.

### Checks run
- Regressed guard fails and exits -> in C:/fks/tB4 disabled the target check in proxy.js (replaced the condition with `false`), ran `node --test test/proxy.test.js` with no force-exit under `timeout 60` -> exit=1, six `refuses target ...` tests fail, ran to completion in about 6 s (no hang); restored.
- Same for other refusals -> host `0.0.0.0` guard off: exit=1 in 6 s, "refuses to bind a non-loopback host" fails; studio validation off: exit=1, three studio refusal tests fail; bridge read error swallowed: exit=1, "refuses a missing bridge file" fails. No hang in any; each restored.
- Origin/Referer -> mutated `ownOrigins` to the single 127.0.0.1 origin: "treats every loopback form..." fails; removed `toLowerCase`: same test fails; removed the boundary check: "leaves a foreign origin and a foreign referer alone" fails (port 1234 vs 123 style case).
- Host first -> removed the Host 421 line: "refuses a foreign Host and an empty Host..." fails.
- Chunked tagging -> removed the `content-length` set and the `transfer-encoding` delete: "tags a chunked page under the limit and sets its length" and the basic tag test fail.
- `//` path -> replaced `path: req.url` with `new URL(req.url, targetOrigin).pathname`: look-alike, forwarding and the new `//evil.test/x` test fail; replaced with a `//`-only normalisation: the new test fails (it times out at 6 s because upstream never sees the request, which is still a failure). New test has teeth.
- Suite -> `npm test` in C:/fks/tB4/packages/fontkitstudio -> 55 pass, fail 0.
- Tree after probes -> `git diff 8bf379e -- packages` vs the patch -> identical; proxy.js restored from backup each time.

### Strengths
- `mustRefuse` makes the test cleanup independent of the code under test; a regressed guard now produces a clean failure and a clean exit.
- `underProxy` is one small function used by both headers, so Origin and Referer cannot drift apart.

### Issues
#### Critical
(none)
#### Important
(none)
#### Minor
1. The `//evil.test/x` test proves nothing contacted evil.test only indirectly (upstream saw the path as a path, Host fixed). That is sufficient, since the request target host is fixed at start-up (proxy.js:155-157); no change needed.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** All four fixes are present and each is caught by a mutation that fails and exits without a hang. The tree equals the regenerated patch, the suite is 55 pass / 0 fail, and nothing outside the fixes changed.
