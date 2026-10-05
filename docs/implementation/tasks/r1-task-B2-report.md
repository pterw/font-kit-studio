# B2 code report (mode: code)

Files (patch `task-B2-code.patch`, LF, `git apply --check -R` passes):
- `packages/fontkitstudio/src/vite-plugin.js` (new, 100 lines)
- `packages/fontkitstudio/test/vite-plugin.test.js` (new, 11 tests)
- `packages/fontkitstudio/package.json` (`exports` only: adds `./vite`)

## Steps
1 failing tests: done. RED: `node --test test/vite-plugin.test.js` -> ERR_MODULE_NOT_FOUND for
  `src/vite-plugin.js`, `ℹ fail 1` (module absent, as expected).
2 implement: done (imports only `node:*` and `./studio-server.js`; no createRequire, no computed import()).
3 package.json exports: done.
4 GREEN: `ℹ pass 11 / ℹ fail 0`, three runs in a row (stable).
  Mutations, one at a time, each restored by copying the saved file back:
  - `apply` removed -> "is named fontkit-studio and applies to serve only" fails.
  - exact path -> `startsWith('/@fontkit/')` -> "passes every other request to next" fails.
  - origin check removed (hostname and `url.origin` comparison) -> "refuses an origin that is not a local http origin" fails.
  - close handler removed -> "standalone: starts Studio, prints its URL once, closes with the dev server"
    and "standalone without resolved URLs prints Studio without a target" fail.
5 gates: `node --check src/vite-plugin.js` OK; `npm --prefix packages/fontkitstudio test`:
  `ℹ tests 35 / ℹ pass 35 / ℹ fail 0`. No Python gates, pre-commit not run (controller gates).
6 report: this file.

## Notes and deviations
- fetchRaw uses `agent: false`: Node 24's default keep-alive agent reused a socket and gave
  ECONNRESET instead of ECONNREFUSED after Studio closed. Not a plugin issue.
- Mutation 4 leaves the real Studio server listening, so that run hangs; I ran it with
  `--test-force-exit` and `timeout 60`. A first, unforced run hung and I stopped it by PID
  (my own node processes only). A failing standalone test can leak a Studio server for the same
  reason; the normal green run exits cleanly.
- The ECONNREFUSED check right after `emit('close')` needs no sleep: `server.close()` stops listening synchronously.
- Known limit (from brief): a Vite config restart makes a new plugin instance and a new
  standalone Studio URL; the CLI path is unaffected.
- `printUrls` in standalone mode prints Studio's line only on the first call (once, per brief).
- Studio line target: `server.resolvedUrls.local[0]`, or no target when resolvedUrls is null.

## Self-review (anti-patterns)
- Trust boundary: middleware matches the exact pathname only, GET/HEAD only, reads no other file,
  serves in-memory bytes; the origin guard rejects non-http, non-loopback and any path/trailing
  slash, and the error never echoes the input (test asserts it). Response body is the bridge, never request input.
- AP 13: every test server is closed in `after`; standalone tests also register a cleanup.
- No fixed sleeps. No Python tests touched, so `test_support` not needed.

## Handoff
Commit subject: `feat(dev): add the Vite plugin that serves and tags the bridge`

Body draft:
```
Serve the bundled bridge from the app's own origin so a script-src
'self' CSP allows it, and tag every page with one classic script whose
data-allowed-origins pins Studio's origin, with no inline script.
apply: 'serve' keeps the plugin out of every vite build. Used alone in
a vite.config the plugin starts its own Studio server and prints its
URL after Vite's own lines.
```

progress.md event draft: "R1.4b (B2): `fontkitstudio/vite` exports `fontkitStudio()`; dev-only Vite
plugin serves `/@fontkit/fontkit-bridge.js` and injects the classic script tag; standalone mode
starts and closes its own Studio server. 11 Node tests; mutations on apply, exact path, origin
check and close handler each caught."


## Landing (controller, 2026-10-04)

Review minors 1 and 2 fixed at landing: the middleware compares the raw path before any query with `BRIDGE_PATH` instead of parsing it with `new URL`, so a request path such as `//[` can no longer throw out of the middleware (Connect answered 500) and `//evil.test/@fontkit/fontkit-bridge.js` is no longer served the bridge. Two new cases in the pass-to-next test; restoring the `new URL` parse fails the `//evil.test` case. Minor 3 (a broken close handler leaves the standalone test's Studio server running, so a failing run hangs instead of failing) stays: it affects only a failing run. Minors 4 and 5 are accepted behaviour. Node tests on Windows: 49 run, 47 pass, 2 skipped (B1's machine-dependent cases).
