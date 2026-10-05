# R1 B4 brief: the loopback proxy

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B4, R1.5a); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.5). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first).

## Goal

`packages/fontkitstudio/src/proxy.js` puts a loopback proxy in front of a dev server that
is not Vite (Next.js, Rails, a static server). It forwards everything to that server, serves
the bridge itself at `/@fontkit/fontkit-bridge.js`, and adds one classic script tag to HTML
pages:

```html
<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="<studio.origin>"></script>
```

The bridge is served from the proxy's origin, which is the app's origin as the browser
sees it, so a `script-src 'self'` CSP allows it. The proxy is a trust boundary (global
rule 5): it binds loopback, checks `Host`, never becomes an open proxy, never reads a local
file other than the bridge, and leaves every response it does not tag byte for byte as it
came.

## Definition of done

- Node tests in `test/proxy.test.js` cover every behaviour and every hostile case below,
  against a real upstream `node:http` server. Each fails if its check is removed.
- Mutation evidence, one at a time, with the failing test named in the report: the Host
  check, the target check, the `text/html` check, the size limit, the exact bridge path,
  the cache-header strip on tagged pages, and the absolute-form refusal.
- No WebSocket upgrade handling (B5), no runner or CLI (B5, B3b), no messages beyond the
  ones below (B6).

## Owns

`packages/fontkitstudio/src/proxy.js`, `packages/fontkitstudio/test/proxy.test.js`,
`packages/fontkitstudio/test/helpers/upstream.js`.

## Interface (binding; B5 and B6 build on it)

```js
export const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';
export async function startProxy({
  target,                      // 'http://localhost:3000/' etc.; loopback http only
  studio,                      // { origin } from startStudioServer (PR A)
  bridgeFile = new URL('../dist/fontkit-bridge.js', import.meta.url),
  host = '127.0.0.1',          // '127.0.0.1' | '::1' | 'localhost' only
  port = 0,
  maxHtmlBytes = 8 * 1024 * 1024,
}): Promise<{ origin, port, close(): Promise<void> }>;   // origin: 'http://127.0.0.1:<port>'
```

B2's plugin defines the same `BRIDGE_PATH` literal (the two tasks run in parallel; global
rule 10 allows two copies; each task's tests assert the literal).

## Behaviour

Start-up (each a rejection of `startProxy`; fixed text, never the input):

- `target` must parse with `new URL`, protocol `http:`, hostname `localhost`, `127.0.0.1`
  or `[::1]`; else `Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)`.
- `studio.origin`: same rule as the plugin (`http:`, loopback hostname, no path); else
  `Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000`.
- `host` not loopback: `refusing to bind <host>: the proxy runs on loopback only`.
- Bridge file unreadable: `Font Kit Studio cannot read the bridge at <path>; run npm --prefix packages/fontkitstudio run prepack`.

Per request, in this order:

1. `Host` (lower-cased) must be `127.0.0.1:<port>`, `localhost:<port>` or `[::1]:<port>`;
   else 421 `Host header not allowed.` (as PR A's Studio server).
2. `req.url` must start with `/` (origin-form). An absolute-form request line
   (`GET http://example.com/ HTTP/1.1`) or `*` answers 400 `Bad request.`: the proxy only
   ever talks to its one target.
3. `GET` or `HEAD` with pathname exactly `BRIDGE_PATH` (query allowed): 200, the bridge
   bytes, `text/javascript; charset=utf-8`, `Cache-Control: no-store`,
   `X-Content-Type-Options: nosniff`. Everything else goes to the target, including
   `/@fontkit/../x` and `/%40fontkit/fontkit-bridge.js` (the proxy never maps a path to a
   local file).
4. Forward with `node:http` `request` to the target's hostname (strip `[` `]` for `::1`)
   and port, the same method and `req.url`, the request body piped, and the request
   headers with these changes only: `host` = the target's host; `accept-encoding` =
   `identity`; `origin` equal to the proxy origin becomes the target origin; a `referer`
   starting with the proxy origin gets that prefix replaced by the target origin (so the
   app's own same-origin checks keep working); hop-by-hop headers dropped (`connection`,
   `keep-alive`, `proxy-connection`, `te`, `trailer`, `transfer-encoding`, `upgrade`).
   Use one `new http.Agent({ keepAlive: true })` per proxy and `destroy()` it in `close()`.
5. Response, tagged: status 200, `content-type` media type (before `;`, trimmed,
   lower-cased) exactly `text/html`, no `content-encoding` (or `identity`), method not
   `HEAD`, and the body at most `maxHtmlBytes`. Buffer it, insert the tag, and send it with
   every upstream header unchanged except: `content-length` set to the new length,
   `transfer-encoding` removed, `etag` and `last-modified` removed, and
   `cache-control: no-store` set. (A cached tagged page would pin the previous run's
   Studio origin; a 304 against its ETag would bring it back.) The CSP header is never
   touched.
6. Response, untouched: anything else, and HTML that passes `maxHtmlBytes` while being
   read: write the upstream status and headers as they came and stream the body (the
   bytes already buffered first, then the rest), byte for byte.
7. `location` header: an absolute URL whose origin is the target origin is rewritten to
   the proxy origin (path, query and hash kept); relative or other-origin locations are
   left alone. This applies to tagged and untouched responses.
8. Upstream unreachable or reset before the head: 502, `text/plain`,
   `Font Kit Studio cannot reach the dev server at <target origin>. Is it running?`.

Tag insertion works on bytes (`buf.toString('latin1')`, splice, `Buffer.from(s, 'latin1')`)
so every other byte is preserved whatever the page's encoding. Insert right after the first
`/<head(\s[^>]*)?>/i` (it must not match `<header>`); with no `<head>`, after the first
`/<html(\s[^>]*)?>/i`; with neither, after a leading `<!doctype ...>`; else at offset 0.

`close()` closes the server (`closeAllConnections()` first) and destroys the agent.

## Steps

- [ ] **1. Upstream helper** `test/helpers/upstream.js`: `startUpstream(routes)` starts a
  `node:http` server on `127.0.0.1:0`; `routes` maps a pathname to
  `{ status, headers, body }` (body a Buffer or string; a function `(req) => ...` allowed);
  unknown paths answer 404 `not found`. It records `{ method, url, headers, body }` for
  every request. Returns `{ origin, port, requests, close() }`.

- [ ] **2. Failing tests** `test/proxy.test.js`. Requests use `node:http` `request` with an
  explicit `Host` (fetch cannot set it); for an absolute-form line or an empty Host use a
  raw `node:net` socket. Close every server in `after`. Cases:
  1. HTML page with `<head>`: the tag sits right after `<head>`, `content-length` is the
     new byte length, the body is otherwise byte-identical (use a page with `café`
     in UTF-8 and compare the bytes around the tag), `etag` and `last-modified` gone,
     `cache-control: no-store`, the upstream `content-security-policy` unchanged;
  2. HTML with `<header>` and no `<head>`, with `<html lang="en">`: tag after `<html ...>`;
     a fragment with neither, starting `<!doctype html>`: tag after the doctype;
  3. `text/html; charset=utf-8` and `TEXT/HTML` are tagged; `application/xhtml+xml`,
     `application/json`, `text/javascript`, `text/css`, `image/png` (random bytes) pass
     byte for byte with their headers, untagged;
  4. a 404 HTML and a 304 pass through untouched; a `HEAD` for an HTML page is forwarded
     and answers the upstream headers with no body and no tag;
  5. HTML of exactly `maxHtmlBytes` (set it to 64 in the test) is tagged; 65 bytes pass
     through byte for byte with the upstream `content-length`;
  6. `content-encoding: gzip` HTML (gzip a page with `node:zlib`) passes through byte for
     byte, untagged; the upstream saw `accept-encoding: identity`;
  7. `GET /@fontkit/fontkit-bridge.js` and `?v=1`: the bridge bytes and headers, and the
     upstream saw no request; `/@fontkit/../package.json`, `/%40fontkit/fontkit-bridge.js`
     and `/..%2f..%2fetc/passwd` reach the upstream with the path unchanged (assert the
     recorded `url`) and the answer is the upstream's;
  8. Host: `evil.test:<port>` 421 and the upstream saw nothing; `localhost:<port>` and
     `LOCALHOST:<port>` reach the upstream; an empty Host (raw socket) 421;
  9. absolute-form `GET http://example.com/ HTTP/1.1` with a good Host (raw socket): 400,
     and the upstream saw nothing;
  10. forwarding: POST with a JSON body arrives with the same method, path, query, body
      and `content-type`; the upstream saw `host` = its own host; `origin` equal to the
      proxy origin arrived as the upstream origin, `origin: http://evil.test` arrived
      unchanged; a `referer` under the proxy origin arrived under the upstream origin;
  11. `location: <upstream origin>/login?next=/a#x` comes back as
      `<proxy origin>/login?next=/a#x`; `location: /login` and
      `location: http://example.com/` unchanged;
  12. a stopped upstream (start one, note its origin, close it, then proxy to it): 502
      with the fixed text naming that origin;
  13. start-up refusals: targets `http://example.com`, `http://10.0.0.5:3000`,
      `https://localhost:3000`, `file:///etc/passwd`, `localhost:3000`, `''`; studio
      origins `http://example.com:5000` and `http://127.0.0.1:5000/x`; host `0.0.0.0`;
      a missing bridge file. Each rejects with its fixed text, and no message contains
      the hostile input except where the table says `<path>`.
  Run `node --test test/proxy.test.js` from `packages/fontkitstudio`: RED.

- [ ] **3. Implement** `src/proxy.js` to the behaviour above. Imports: `node:*` only (the
  import guard; no `createRequire` or computed `import()`). Flat: one request handler, one
  `forward` function, one `insertTag(buffer, tag)` function.

- [ ] **4. GREEN**, then the seven mutations, each restored by editing (no `git stash`).

- [ ] **5. Gates for the code phase:** `npm --prefix packages/fontkitstudio test` (the
  whole Node suite; quote the `fail 0` line), `node --check src/proxy.js`. No Python gates.

- [ ] **6. Report** with a Handoff: the patch, a `progress.md` event draft, the commit
  subject `feat(dev): proxy a local dev server and tag its pages with the bridge` and a
  why-body (apps that do not run on Vite still get one command; the bridge comes from the
  app's origin so a `script-src 'self'` CSP allows it; the proxy refuses anything but a
  local target, checks Host and leaves every response it does not tag untouched; tagged
  pages are not cached because the tag pins one run's Studio origin).

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B4-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B4-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B4-report.md`.
