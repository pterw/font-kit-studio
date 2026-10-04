# R1 B5 brief: the proxy runner, WebSockets and the Bootstrap fixture

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B5, R1.5b; After: B4); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.5). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first). Builds on B4's
`startProxy` (`packages/fontkitstudio/src/proxy.js`, read it first) and PR A's
`startStudioServer` (`src/studio-server.js`).

## Goal

`runProxy()` is what `npx fontkitstudio http://localhost:3000` will run (B3b wires the
flag parsing): it starts the token-guarded Studio server, then the proxy in front of the
user's dev server, prints two lines, opens Studio in the browser unless told not to
(D051), and stops both on Ctrl-C. The proxy also passes WebSocket upgrades through, so the
app's own hot reload keeps working. A real browser proves the whole path on a static
Bootstrap 5 page served with `Content-Security-Policy: script-src 'self'; style-src 'self'`.

## Definition of done

- Node tests (`test/run-proxy.test.js`, additions to `test/proxy.test.js`,
  `test/open-browser.test.js`) and one Python browser module
  (`tests/test_one_command_proxy.py`) cover the behaviour below; each fails if its code is
  removed (RED, then GREEN).
- Mutation evidence, one at a time, with the failing test named: the Host check on
  upgrade; the Origin rewrite on upgrade; the `close()` of the Studio server in
  `runProxy`; the `open` flag (always open).
- The browser test blocks every `https://` request and asserts no CSP violation.

## Owns

`packages/fontkitstudio/src/run-proxy.js`, `src/open-browser.js`, the WebSocket upgrade
handling in `src/proxy.js` (add a handler; do not change B4's HTTP behaviour),
`test/run-proxy.test.js`, `test/open-browser.test.js`, `test/helpers/ws-upstream.js`,
`test/helpers/run-proxy.js`, upgrade cases appended to `test/proxy.test.js`;
`fixtures/bootstrap5-static/` (`index.html`, `app.css`, `vendor/bootstrap.min.css`,
`vendor/bootstrap.bundle.min.js`, `vendor/LICENSE`); `tests/test_one_command_proxy.py`;
`tests/helpers_csp_server.py`.

## Interface (binding; B3b and B6 build on it)

```js
// src/open-browser.js
export function browserCommand(platform, url): { command, args };
//   win32:  { command: 'rundll32', args: ['url.dll,FileProtocolHandler', url] }  (no shell: & and ? stay literal)
//   darwin: { command: 'open', args: [url] }
//   other:  { command: 'xdg-open', args: [url] }
export function openBrowser(url, { err = process.stderr, spawnFn = spawn, platform = process.platform } = {}): void;
//   spawns detached with stdio 'ignore' and unref()s; on the child's 'error' event (no
//   browser, SSH, container) writes one line to err:
//   'Font Kit Studio could not open a browser; open the URL above.\n'

// src/run-proxy.js
export async function runProxy({
  target,                       // user's dev server URL; startProxy validates it
  open = true,
  out = process.stdout, err = process.stderr,
  studioPort = 0,               // B3b's --studio-port; busy -> a free port with a message
  openUrl = openBrowser,        // tests pass a recorder
  studioFile, bridgeFile,       // tests only; default to the package's dist/
}): Promise<{ studioUrl, proxyOrigin, close(): Promise<void> }>;
```

## Behaviour

- **Start order.** `startStudioServer({ port: studioPort, studioFile })`. If `studioPort`
  is not 0 and the port is busy (`EADDRINUSE`), start on port 0 and write to `err`:
  `Font Kit Studio: port <studioPort> is busy, so Studio uses port <actual>; its saved settings stay with the old port.`
  Then `startProxy({ target, studio, bridgeFile })`. If the proxy rejects, close the
  Studio server before rethrowing (no server left running).
- **Output** to `out`, exactly two lines:
  `Font Kit Studio · dev only` and `Open: <studio.url(proxyOrigin + targetPath)>`, where
  `targetPath` is the target URL's `pathname + search` (`http://localhost:3000/app?x=1`
  gives `<proxy origin>/app?x=1`).
- **Open.** `open` true: `openUrl(studioUrl, { err })` once, after both lines are written.
- **Stop.** `runProxy` registers handlers for `SIGINT` and `SIGTERM` (and `SIGBREAK` when
  the platform is `win32`) that call `close()`. `close()` closes the proxy, then the
  Studio server, removes those handlers, and is idempotent (a second call resolves).
- **WebSocket upgrade** (`server.on('upgrade', ...)` in `proxy.js`): the same `Host` check
  (else write `HTTP/1.1 421 Misdirected Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n`
  and destroy the socket) and origin-form check (else 400 the same way); then
  `net.connect` to the target, write the request line, the headers with the same rewrites
  as HTTP (`host`, `origin`, `referer`; keep `upgrade`, `connection`,
  `sec-websocket-*`), a blank line and `head`, and pipe both ways. An error or close on
  either side destroys the other. `close()` of the proxy destroys every open upgraded
  socket (track them in a Set).
- **Bootstrap fixture.** `fixtures/bootstrap5-static/index.html` uses
  `vendor/bootstrap.min.css`, `vendor/bootstrap.bundle.min.js` (Bootstrap 5.3.8, taken
  from the npm tarball: `npm pack bootstrap@5.3.8` in a scratch dir, extract
  `package/dist/css/bootstrap.min.css`, `package/dist/js/bootstrap.bundle.min.js` and
  `package/LICENSE`; delete the `sourceMappingURL` comment lines so the page asks for no
  missing map) and `app.css`. No inline script, no inline style, no `style=` attribute,
  no external URL. Author ids: `data-design-id="bs.hero.title"` on an `<h1>`,
  `bs.hero.lead` on a `<p class="lead">`, `bs.hero.cta` on a `<button class="btn
  btn-primary">`. The vendored files are churn (D050).
- **CSP server** `tests/helpers_csp_server.py`: `start_csp_server(directory)` returns
  `(server, origin)`; a `ThreadingHTTPServer` on `127.0.0.1:0` serving files from
  `directory` with `Content-Security-Policy: script-src 'self'; style-src 'self'` on every
  response, `daemon_threads = True`, quiet `log_message`; the caller stops it with
  `server.shutdown()` and `server.server_close()`.
- **Node helper** `test/helpers/run-proxy.js` (for the Python test): argv = target,
  studioFile, bridgeFile; calls `runProxy({ target, open: false, studioFile, bridgeFile })`
  (stdout gets its two lines), then closes it when stdin ends and exits 0.

## Steps

- [ ] **1. Failing Node tests.**
  - `test/helpers/ws-upstream.js`: a `node:http` server on `127.0.0.1:0` whose `upgrade`
    handler answers the RFC 6455 handshake (`Sec-WebSocket-Accept` =
    base64(sha1(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')) with `node:crypto`), records
    the request headers, then echoes raw bytes (`socket.pipe(socket)`). No WebSocket
    library.
  - `test/proxy.test.js` (append): through the proxy, a raw `node:net` client sends the
    upgrade with `Host: 127.0.0.1:<proxy port>` and `Origin: <proxy origin>`, reads
    `101`, checks `Sec-WebSocket-Accept`, writes a frame's bytes and reads the same bytes
    back; the upstream saw its own host and its own origin. A wrong Host on upgrade gets
    `421` and the upstream saw no upgrade. `close()` with an open upgraded socket resolves
    and the client sees the socket end.
  - `test/run-proxy.test.js`: with a temp Studio file, a temp bridge file and an
    `startUpstream` (B4's helper) target `http://localhost:<port>/app?x=1`: the two lines
    exactly (parse the `Open:` URL: Studio origin, token, and `target` equal to
    `<proxy origin>/app?x=1`); a GET of that target through the proxy is tagged; with
    `open: true` the recorder got the Studio URL once, with `open: false` never;
    `process.emit('SIGINT')` closes both servers (requests then fail with
    `ECONNREFUSED`) and `process.listenerCount('SIGINT')` is back to its value before the
    run; a target `http://example.com` rejects with B4's text and no Studio server is left
    (its port refuses); `studioPort` set to a port another test server holds: Studio
    starts elsewhere and `err` has the busy-port line.
  - `test/open-browser.test.js`: `browserCommand` for `win32`, `darwin`, `linux` with a URL
    containing `&` and `?` keeps the URL as one argument, unchanged; `openBrowser` with a
    fake `spawnFn` returning an `EventEmitter` child (with `unref()`) emits `error`:
    `err` gets the could-not-open line; no real browser is ever launched.
  Run `npm --prefix packages/fontkitstudio test`: RED.
- [ ] **2. Implement** `open-browser.js`, `run-proxy.js` and the upgrade handler.
  `node:*` imports only; no shell (`spawn` with an args array and `shell: false`).
- [ ] **3. Fixture and CSP server** as above.
- [ ] **4. Browser test** `tests/test_one_command_proxy.py` (pattern:
  `tests/test_node_studio_server.py`; skip the class when `node` is not on PATH):
  start the CSP server on the fixture; start the helper with
  `[node, helper, f'http://localhost:{port}/index.html', str(support.HTML), str(support.REPO / 'fontkit-bridge.js')]`
  (stdin, stdout pipes, `text=True`), read the two lines, stop it in a cleanup (close
  stdin, wait 10 s, kill only that process on timeout). For each engine in `ENGINES`:
  `new_context(engine)`; `context.route('https://**/*', lambda r: r.abort())`;
  `context.add_init_script` that records `securitypolicyviolation` events into
  `window.__cspViolations` in every frame; open the `Open:` URL; wait until
  `#bridgeStatusBadge` text matches `^Connected \(\d+ targets?\)$`; click the title in
  `#targetAppFrame` until `#liveTargetName` names `bs.hero.title` (one retry, as
  `test_live_integration.click_in_target`); type `56` into `#liveFontSize` with keystrokes
  (click, Ctrl+A, `keyboard.type`); wait until the frame's title computed `font-size` is
  `56px`; assert `window.__cspViolations` is empty in the frame and in Studio, and no page
  error. Also fetch the page through the proxy with `urllib.request` and assert the
  `Content-Security-Policy` header equals the CSP server's exactly, and the body has the
  one tag. Run it, then `PYTHONPATH=tests python -m unittest test_support`.
- [ ] **5. GREEN**, then the four mutations, each restored by editing.
- [ ] **6. Gates for the code phase:** `npm --prefix packages/fontkitstudio test`;
  `PYTHONPATH=tests python -m unittest test_one_command_proxy test_support -v`;
  `python -m ruff check .`. The controller's gate-runners run suite-a and suite-b at
  landing.
- [ ] **7. Report** with a Handoff: the patch, a `progress.md` event draft, the commit
  subject `feat(dev): run the proxy with Studio and pass hot reload through` and a
  why-body (one command for apps that do not run on Vite; the app's own hot reload keeps
  working; proved on a page whose CSP allows only its own scripts and styles).

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B5-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B5-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B5-report.md`.
