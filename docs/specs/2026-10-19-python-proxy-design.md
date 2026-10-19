# Design: a Python proxy in serve.py for apps without Node

Status: **approved by the owner on 2026-10-19** (brainstorm sections 1-3). It ships in 0.4.0 (R2 PR C, plan
[Addendum 29](../plans/2026-10-03-r2-engine.md)); the work order is [the plan](../plans/2026-10-19-python-proxy.md).
A pip wrapper and the browser extension are later, separate work ([roadmap](../plans/2026-10-03-roadmap.md)).

## Problem

Studio edits a running app only when the bridge script is in its pages. Today that takes one of three things: a
script tag in the app's own templates, `npx fontkitstudio <url>` (a proxy that adds the tag, but needs Node 22.12 or
later), or a bookmarklet run by hand in a pop-out window. A developer with a Flask, Django or Jinja app usually has
Python but not always Node. Opening `fontkit-studio.html` and pointing it at the app is not enough: a page cannot add
a script to another origin's page, and the browser forbids it on purpose. Studio then says, correctly, `No bridge
answered at http://127.0.0.1:5000 within 4 s.` (checked against a real Flask app on 2026-10-19).

## Goal

One command, no install, no paste:

```
python serve.py http://127.0.0.1:5000
```

It opens Studio already connected to the app, the same way `npx fontkitstudio http://127.0.0.1:5000` does.

## Non-goals

HTTPS or non-loopback targets; rewriting URLs inside page bodies; service workers; a pip package (later, wrapping
the same file); the browser extension (R5, its own design); any change to Studio, the bridge or the protocol.

## Design

### Shape

`scripts/serve.py` gains one optional positional argument, the app's address. Without it, serve.py behaves exactly
as today (Studio, the demo app, Sync to file). With it:

1. Studio is served on `--studio-port` (default 8000) and the proxy on `--target-port` (default 8001), both on
   loopback.
2. Both use the target's host name, so the app's cookies keep working: `localhost` stays `localhost`, `127.0.0.1`
   stays `127.0.0.1`; an `[::1]` target uses `127.0.0.1` (the Node command's rule).
3. Sync to file is off: there is no overrides file in someone else's app. Studio's existing status check then shows
   Sync's existing "off" reason.
4. serve.py prints `Studio:`, `App:` (the proxied address) and the `Open:` line, Studio's URL with
   `?target=<proxy URL with the target's path>`, and opens it with `--open`.

serve.py stays one standard-library file. It finds `fontkit-studio.html` and `fontkit-bridge.js` next to itself
first, then in the repository. The GitHub release adds `serve.py` to the assets it already carries, so a user with no
clone downloads three files and runs one command. Without the repository, only the proxy mode works; the plain mode
says so (string below).

### Each request

To the app:

- `Host` becomes the target's host; `Accept-Encoding` becomes `identity`, so pages arrive uncompressed (the standard
  library has no Brotli, and the tag goes in without decompressing).
- An `Origin` or `Referer` under one of the proxy's own loopback origins is rewritten to the target's origin.
- Everything else passes unchanged, cookies included.

From the app:

- A 200 response to a GET that is `text/html` with identity encoding (the Node rule; HEAD, 304 and error pages pass
  untouched) is buffered and gets exactly one tag,
  `<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="<Studio origin>"></script>`, inserted after
  `<head>`, else after `<html>`, else after a leading doctype (with an optional UTF-8 byte-order mark), else at 0.
  The match is case-insensitive and byte-preserving (latin-1 semantics, the Node `insertTag` rule). `Content-Length`
  is recomputed.
- Before forwarding a page, the proxy reads the `Content-Security-Policy` header and `<meta http-equiv>` policies. If
  they block a same-origin script, it prints the CSP message once per run; if the page already loads its own
  `fontkit-bridge.js`, it prints the second message once per run. Headers pass through unchanged.
- Any other response streams through chunk by chunk as it arrives (`read1`), so live streams are not held back.
- A `Location` that is absolute or protocol-relative, `http:`, under any loopback name and the target's port, is
  rewritten to the proxy's origin; a relative one is left as it is.
- `GET /@fontkit/fontkit-bridge.js` (query ignored) is answered by the proxy with the bridge's bytes. Every other path
  goes to the app. The proxy serves no other local file.
- A WebSocket upgrade is tunnelled as raw bytes both ways (standard library `socket` and `selectors`).
- If the app does not answer, the proxy replies 502 with the Node text and keeps serving.

### Trust and lifecycle

- Loopback only: the target must be `http:` on `localhost`, `127.0.0.1` or `[::1]`; anything else exits 1 with one
  line. Both servers bind loopback.
- Studio's server keeps serve.py's existing `Host` (DNS-rebinding) and `Origin` checks. serve.py has no per-run token
  today, and this design adds none: Studio's server in proxy mode serves only Studio and its status check, and Sync is
  off, so there is nothing a token would protect that the `Host`/`Origin` checks do not.
- Ctrl-C (and Ctrl-Break on Windows) stops both servers through serve.py's existing stop path.

### Strings (exact)

Reused verbatim from the Node package:

- Refusal: `serve.py: Font Kit Studio proxies only a local dev server (localhost, 127.0.0.1 or [::1])`
  (the Node sentence with serve.py's usual `serve.py: ` prefix).
- CSP: `Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the page's own
  scripts). Add 'self' to script-src while you develop.`
- 502 body: `Font Kit Studio cannot reach the dev server at <target origin>. Is it running?`

New (approved by the owner with this spec, 2026-10-19):

- Bridge twice: `Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not connect, remove
  that script while you use serve.py.`
- Plain mode without the repository: `serve.py: the demo app needs the repository. To edit your own app, pass its
  address: python serve.py http://127.0.0.1:5000`
- Missing Studio or bridge file in proxy mode (exit 1): `serve.py: cannot find fontkit-studio.html or
  fontkit-bridge.js next to serve.py or in the repository`

## Testing

- `tests/test_serve_proxy.py` runs the real serve.py as a process on free ports in front of a small standard-library
  app server inside the test (an HTML page, a stylesheet, redirects, a strict-CSP page, a page that loads its own
  bridge, a WebSocket echo). About ten behaviour tests, one per contract point: one tag and the rest of the page byte
  for byte; other responses byte for byte; redirects; the bridge path and bytes; `Set-Cookie` and CSP headers
  unchanged; each warning once per run; refusal of non-loopback and `https:` targets with exit 1; a WebSocket round
  trip; 502 while the app is down and recovery after; `Host`/`Origin` refusals on Studio's server.
- Parity: tag placement cases live in `tests/fixtures/proxy-insert-cases.json`, read by both this module and the
  Node `proxy.test.js`.
- One real end-to-end case in `tests/test_r2_entrypoints.py`: real Studio and the real bridge through the Python
  proxy over the Bootstrap 5 static fixture: Detect, Apply, re-render, Clear. It needs no Node, so it runs in the
  blocking Chromium job on Linux and in the Windows run.
- Every new test has a Given/When/Then docstring whose Then states exactly what it asserts, an independent oracle
  (this spec's literals, the JSON cases, the repository's bridge bytes) and one realistic mutant shown failing. No
  fixed sleeps; servers stop in `finally`.

## Risks

- Two proxies can drift. The shared JSON cases cover the riskiest rule (tag placement); the rest is held by this
  spec's contract, tested on each side.
- `http.server` is not built for heavy traffic. It serves one developer's browser on loopback, which is its use.
- A request body sent without a length (a chunked upload) is refused with 411; the Node proxy streams it. Kept for
  simplicity (owner preference for KISS, 2026-10-19).
- The WebSocket tunnel writes with blocking sends: if both peers stop reading while both buffers are full, it stalls.
- An HTML page is buffered up to the Node proxy's size limit and tagged; a larger one streams through untagged, as
  the Node proxy does.
