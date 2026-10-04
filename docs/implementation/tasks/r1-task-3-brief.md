# R1.3 brief: Studio server and per-run token

Plan: `docs/plans/2026-10-03-r1-one-command.md` (R1.3); execution:
`docs/plans/2026-10-04-r1-pr-a-sdd.md`. Constraints:
`.superpowers/sdd/r1-pr-a/constraints.md` (read all of it first). Spec: design section 1
("Secure": loopback only, Host and Origin checks, a per-run token in Studio's URL so
another local page cannot drive it).

## Goal

`packages/fontkitstudio/src/studio-server.js` serves one file, the bundled Studio, on a
loopback port, only to requests that carry the run's random token and a loopback `Host`.
The token never leaves Studio's page: not in a `Referer` to the app or to a font host.

## Definition of done

- Node tests cover the good path and every hostile case in the table below; each fails if
  its check is removed (mutation evidence for token, Host, Origin and method checks).
- One real-browser test (Python, Chromium) opens Studio from this server with
  `?target=` pointing at a recording loopback server, and proves the app's requests carry
  no token and no `Referer`; and that a URL without the token shows no Studio.
- No CLI wiring (R1.4 does that) and no change to `package.json`.

## Owns

`packages/fontkitstudio/src/studio-server.js`,
`packages/fontkitstudio/test/studio-server.test.js`,
`packages/fontkitstudio/test/helpers/serve-studio.js`, `tests/test_node_studio_server.py`.

## Interface (binding; R1.4 builds on it)

```js
export const STUDIO_PATH = '/fontkit-studio.html';
export function newToken(): string;            // 32 random bytes, base64url (43 chars)
export async function startStudioServer({
  studioFile = new URL('../dist/fontkit-studio.html', import.meta.url),
  host = '127.0.0.1',                            // '127.0.0.1' | '::1' | 'localhost' only
  port = 0,                                      // 0 = a free port
  token = newToken(),
} = {}): Promise<{
  port: number, token: string, origin: string,   // origin: 'http://127.0.0.1:<port>'
  url(target?: string): string,                  // origin + STUDIO_PATH + ?token=..[&target=..]
  close(): Promise<void>,
}>;
```

## Behaviour (checks run in this order)

| Request | Answer |
|---|---|
| `Host` not one of `127.0.0.1:<port>`, `localhost:<port>`, `[::1]:<port>` (case-insensitive) | 421, text "Host header not allowed." |
| `Origin` present and not `http://<the request's Host>` | 403, "Origin not allowed." |
| Method other than GET or HEAD | 405, "Only GET and HEAD.", `Allow: GET, HEAD` |
| Path other than `STUDIO_PATH` | 404, "Not found. Open the URL the fontkitstudio command printed." |
| `token` query value missing or not equal (constant-time compare) | 403, "Missing or wrong token. Open the URL the fontkitstudio command printed." |
| Otherwise | 200, Studio's bytes, `text/html; charset=utf-8` |

Every answer carries `Cache-Control: no-store`, `Referrer-Policy: no-referrer`,
`X-Content-Type-Options: nosniff`. Error bodies are fixed `text/plain` strings and never
echo request input. Studio's file is read once at start; a missing file rejects
`startStudioServer` with an error naming the path and saying to run the bundle step
(`npm --prefix packages/fontkitstudio run prepack`). A non-loopback `host` rejects with
"refusing to bind <host>: Studio is served on loopback only".

## Steps

- [ ] **1. Failing Node tests** `test/studio-server.test.js`. Use `node:http` `request`
  (not `fetch`: it cannot set `Host`). Start the server on a temp Studio file holding a
  known marker (`<title>Font Kit Studio vT</title>`), close it in `after`. Cases:
  1. right token: 200, body equals the file's bytes, the three headers, content type;
  2. HEAD with the token: 200, empty body;
  3. no token; a wrong token of the same length; a wrong token of another length;
     `TOKEN=<right>` (wrong case); `token=<wrong>&token=<right>`: each 403 and the body
     lacks the marker;
  4. `Host: evil.test:<port>` with the right token (DNS rebinding): 421; `Host:
     127.0.0.1:<port+1>`: 421; empty `Host`: 421; `Host: LOCALHOST:<port>`: 200;
  5. `Origin: http://evil.test`: 403; `Origin: null`: 403; `Origin: http://127.0.0.1:<port>`
     with that Host: 200;
  6. POST, PUT, OPTIONS with the token: 405 with `Allow`;
  7. `/`, `/fontkit-studio.html/`, `/%2e%2e/etc/passwd`, `/fontkit-bridge.js`: 404;
  8. `startStudioServer({ host: '0.0.0.0' })` rejects; a missing `studioFile` rejects with
     the path in the message;
  9. `newToken()` returns 43 base64url characters and two calls differ;
  10. `url('http://localhost:5173/')` has `token` and `target` query values that parse back.
  Run: RED (module missing).

- [ ] **2. Implement** `src/studio-server.js` to the table. Use `timingSafeEqual` on
  equal-length buffers (compare lengths first), `new URL(req.url, 'http://studio.invalid')`
  for parsing (catch and answer 400 "Bad request."), `res.setHeader('Connection', 'close')`
  on errors, and `server.closeAllConnections()` before `server.close()` in `close()`.
  Keep it flat (global rule 8): one request handler, no framework, no router.

- [ ] **3. GREEN, then mutation evidence**: one at a time, remove the token check, the Host
  check, the Origin check and the method check; run; record the failing test name; restore.

- [ ] **4. Test helper** `test/helpers/serve-studio.js` (for the Python test):

```js
// Starts the Studio server for a browser test: argv = studioFile, target.
// Prints the Studio URL on one line and stops when stdin closes.
import { startStudioServer } from '../../src/studio-server.js';

const [studioFile, target] = process.argv.slice(2);
const server = await startStudioServer({ studioFile });
process.stdout.write(`${server.url(target)}\n`);
process.stdin.resume();
process.stdin.on('end', async () => { await server.close(); process.exit(0); });
```

- [ ] **5. Browser test** `tests/test_node_studio_server.py` (Chromium via `ENGINES`):
  - skip the class with a clear reason when `shutil.which('node')` is None;
  - a recording server: stdlib `ThreadingHTTPServer` on `127.0.0.1:0` that answers any GET
    with a tiny HTML page and appends `(path, headers)` to a list under a lock;
  - start the helper with `subprocess.Popen([node, helper, str(support.HTML),
    f'http://localhost:{rec_port}/app/'], stdin=PIPE, stdout=PIPE, text=True)`, read the URL
    line, and in `tearDown` close stdin, wait with a timeout, kill only that process if it
    did not exit, and shut the recorder;
  - test 1: open the URL in `new_context(engine)`; wait (condition, not sleep) until the
    recorder has a request for `/app/`; assert no recorded request has a `Referer` header
    and no recorded path or header value contains the token; assert the page title starts
    with `Font Kit Studio v`; collect `pageerror` events and assert none;
  - test 2: open the URL with the token removed: response status 403 and the body has no
    `Font Kit Studio v`.
  Studio's target field accepts `http://localhost:<port>/` targets; check that Studio
  really loads the iframe for `?target=` (it auto-connects; v0.2 Task C) and say in the
  report which request proved it.

- [ ] **6. Gates** (constraints.md). Commit subject:
  `feat(dev): serve Studio on loopback behind a per-run token`. Body: why (spec section 1:
  another local page must not drive Studio; the token must not leak to the app or a font
  host through `Referer`).

## Report

Code phase: `.superpowers/sdd/r1-pr-a/task-3-code-report.md`. Landing:
`docs/implementation/tasks/r1-task-3-report.md`.
