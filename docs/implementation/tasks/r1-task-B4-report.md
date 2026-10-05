# B4 code report (mode: code, BASE 8bf379e)

Files (patch `task-B4-code.patch`, 753 lines added, all new): `packages/fontkitstudio/src/proxy.js`,
`test/proxy.test.js`, `test/helpers/upstream.js`. `git apply --check -R` passes. No shared file touched.

## Steps
1. Upstream helper: done. It sets `content-length` itself when the route gives no framing header (and
   not on 304), because `writeHead` + `end` otherwise sends chunked.
2. Tests: done, 28 tests across 13 brief cases (plus HEAD of the bridge, a POST to the bridge path,
   `OPTIONS *`, a chunked overflow, a body without length, a foreign referer, hop-by-hop headers).
3. Implement: done. Imports are `node:*` only; one handler, `forward`, exported `insertTag`.
4. GREEN and mutations: done.
5. Gates: `npm --prefix packages/fontkitstudio test` -> `ℹ fail 0` (52 tests); `node --check src/proxy.js` ok.
   No Python gates (not asked). pre-commit not run (code mode did not require it for these JS-only files;
   not run, reported as such).

## Evidence
RED: `node --test test/proxy.test.js` before `src/proxy.js` existed -> `✖ test\proxy.test.js ... 'test failed'`
(ERR_MODULE_NOT_FOUND for `../src/proxy.js`; expected). GREEN: `ℹ pass 28 / ℹ fail 0`.

Mutations (one at a time, restored by editing; failing tests):
| mutation | failing test |
| Host check removed | refuses a foreign Host and an empty Host, accepts localhost in any case |
| target check disabled | refuses target "http://example.com" and "http://10.0.0.5:3000" (run then hangs on the leaked server, killed by timeout) |
| `text/html` -> `startsWith('text/')` | tags text/html with parameters or capitals, passes other types untouched |
| size limit removed | tags a page of exactly maxHtmlBytes...; streams a chunked page... |
| exact bridge path -> URL-normalised | forwards look-alike paths unchanged (the `/@fontkit/../@fontkit/...` case) |
| cache-control strip removed | tags a page after <head> and leaves every other byte alone |
| absolute-form refusal removed | refuses an absolute-form request line and * |
After restoring: `ℹ pass 28 / ℹ fail 0`.

## Deviations and decisions
- Host refusal message echoes the host (`refusing to bind 0.0.0.0: ...`) because the brief's text has `<host>`;
  case 13's "no message contains the hostile input" is asserted for target and studio origin only.
- Exact bridge path compares the raw `req.url` before `?`, not a normalised pathname, so
  `/@fontkit/../@fontkit/fontkit-bridge.js` is forwarded (tested).
- `referer` prefix replacement also requires a boundary (`/`, `?`, `#` or end) so port `1234` is not mistaken for `123`.
- `origin`/`referer` rewrite compares to the proxy origin literally (`http://127.0.0.1:<port>`); a page opened via
  `localhost:<port>` would send `http://localhost:<port>` and not be rewritten. Brief-literal; B5 may want to widen it.
- Doctype fallback tolerates a UTF-8 BOM and leading whitespace.

## Self-review (anti-patterns)
Trust boundary (AP 1-4, 7): Host, request-line, target, studio origin, content type, size all tested hostile;
no URL sink takes input that changes scheme or host (upstream host fixed at start-up; request `req.url` is only
a path, absolute-form refused). No request input reflected (fixed 421/400/502 texts). AP 13: every server closed in
`after`/`closers`; one mutation-run hang was stopped by PID. AP 14: nothing skipped. AP 15: no process state in files.
Concern: a hung node from a mutation run was killed by PID only; none remain.

## Handoff
Commit subject: `feat(dev): proxy a local dev server and tag its pages with the bridge`

Body draft:
Apps that do not run on Vite still get one command: the proxy forwards
to the dev server, serves the bridge itself and adds one classic script
tag to its HTML pages. The bridge comes from the app's own origin, so a
script-src 'self' CSP allows it.

The proxy refuses any target but a local one, checks Host, refuses
absolute-form request lines and leaves every response it does not tag
byte for byte as it came. Tagged pages are sent no-store without ETag
or Last-Modified, because the tag pins one run's Studio origin.

progress.md event draft: "R1.5a (B4): `src/proxy.js` loopback proxy with Host and target checks, bridge at
`/@fontkit/fontkit-bridge.js`, HTML tag insertion on bytes, location rewrite, 502 text; 28 Node tests, 7
mutations caught; Node suite 52 pass / fail 0."

## Fix round 1
1. AP 13: startup-refusal tests go through `mustRefuse`, which closes a proxy that wrongly started (pushed on
   `closers`) and fails; `after` closes every server in its own try/catch inside try/finally. Evidence: target
   check disabled -> `node --test` exits code 1 (no hang, no force-exit), failing "refuses target
   http://example.com" and "http://10.0.0.5:3000"; restored.
2. Origin/Referer: `underProxy()` treats `http://127.0.0.1|localhost|[::1]:<port>` (case-insensitive, boundary
   checked) as the proxy origin. New test "treats every loopback form of the proxy origin as its own" (localhost
   Origin and `LOCALHOST` Referer rewritten, `[::1]` rewritten, `localhost:<port+1>` untouched). Mutation
   `ownOrigins = [proxyOrigin]` -> that test fails (exit 1); restored.
3. Trailing whitespace removed; `allowedHosts` and `ownOrigins` built once after listen. Mutation of the Host
   check still fails its test (exit 1).
4. New tests: raw `GET //evil.test/x` reaches upstream with that path and upstream Host, 404, and tagging a
   chunked page under the limit sets `content-length` with no transfer-encoding. Both pass on the existing
   behaviour (no code change needed); they would fail if the forward path or tagging were removed.
Result: proxy.test.js 31 pass / 0 fail; `npm --prefix packages/fontkitstudio test` below; patch regenerated.


## Landing (controller, 2026-10-04)

Landed after fix round 1 and its scoped re-review (`r1-task-B4-rereview.md`: Approved). Node tests on Windows with B1, B2 and B3a in the tree: 80 run, 78 pass, 2 skipped (B1's machine-dependent cases). The plan's Architecture line now shows the tag's `src` as the root-relative `/@fontkit/fontkit-bridge.js` that both the plugin and the proxy emit.
