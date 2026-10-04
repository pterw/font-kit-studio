# R1 B2 brief: the Vite plugin

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B2, R1.4b); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.4). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first).

## Goal

`packages/fontkitstudio/src/vite-plugin.js` exports `fontkitStudio()`, a Vite plugin that,
in `vite dev` only, serves the bundled bridge from the app's own origin and adds one
classic script tag to every HTML page:

```html
<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="http://127.0.0.1:<studio port>"></script>
```

Same origin, so a `script-src 'self'` CSP allows it; no inline script; the bridge reads
`data-allowed-origins` from `document.currentScript`, so the tag must stay a classic
script (no `type="module"`, no `async`, no `defer`).

The CLI (B3b) passes the Studio server it started. Used on its own in a `vite.config`
(the permanent setup), the plugin starts its own Studio server and prints Studio's URL.

## Definition of done

- Node tests in `test/vite-plugin.test.js` cover every behaviour below with small fakes
  (no Vite installed). Each fails if its code is removed (RED, then GREEN).
- Mutation evidence, one at a time, with the failing test named in the report: `apply`
  removed; the exact-path match loosened to `startsWith('/@fontkit/')`; the origin check
  removed; the close handler removed.
- `package.json` `exports` gains `"./vite": "./src/vite-plugin.js"`; a test imports the
  plugin through the package's own name (`import('fontkitstudio/vite')`, Node's
  self-reference) and gets the same function.
- No CLI wiring, no build-time message (B6), no `server.host` refusal (B6).

## Owns

`packages/fontkitstudio/src/vite-plugin.js`, `packages/fontkitstudio/test/vite-plugin.test.js`,
and the `exports` field of `packages/fontkitstudio/package.json` (nothing else in it).

## Interface (binding; B3a, B3b and B6 build on it)

```js
export const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';
export function fontkitStudio(options = {}): {
  name: 'fontkit-studio',
  apply: 'serve',
  configureServer(server): Promise<void>,
  transformIndexHtml(html): HtmlTagDescriptor[],
};
// options.studio:     { origin, url(target) } from startStudioServer (PR A). Optional.
// options.bridgeFile: path or file: URL of the bridge; default
//                     new URL('../dist/fontkit-bridge.js', import.meta.url).
// options.studioFile: passed to startStudioServer in standalone mode (tests only).
```

B4's proxy defines the same `BRIDGE_PATH` literal in `src/proxy.js` (the two tasks run in
parallel). Two copies are allowed under global rule 10; each task's tests assert the
literal, so a drift fails a test.

## Behaviour

- **Creation.** If `options.studio` is given, `new URL(options.studio.origin)` must have
  protocol `http:`, hostname `127.0.0.1`, `localhost` or `[::1]`, and
  `url.origin === options.studio.origin` (no path, no trailing slash). Otherwise throw
  `Error('Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000')`.
  Never echo the given value.
- **`configureServer(server)`** (async; Vite awaits it):
  1. Read the bridge file once (`readFile`). If it is missing, throw
     `Error('Font Kit Studio cannot read the bridge at <path>; run npm --prefix packages/fontkitstudio run prepack')`.
  2. Standalone (no `options.studio`): `studio = await startStudioServer({ studioFile })`
     (pass `studioFile` only when given). Wrap `server.printUrls` so that after Vite's own
     lines it logs, once, through `server.config.logger.info`:
     `  Font Kit Studio: <studio.url(server.resolvedUrls.local[0])>`. Vite sets
     `resolvedUrls` before it calls `printUrls`, so read it inside the wrapper. If
     `resolvedUrls` is null, log `studio.url()` (no target). Close the Studio server when
     `server.httpServer` emits `close`; if `httpServer` is null (middleware mode), close it
     when `server.close()` is called (wrap it, then call the original).
  3. `server.middlewares.use(handler)`: for `GET` or `HEAD` whose pathname
     (`new URL(req.url, 'http://x').pathname`) is exactly `BRIDGE_PATH`, answer 200 with the
     bridge bytes (empty body for HEAD) and `Content-Type: text/javascript; charset=utf-8`,
     `Content-Length`, `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`. Every
     other request calls `next()` untouched. Never read any other file.
- **`transformIndexHtml()`** returns
  `[{ tag: 'script', attrs: { src: BRIDGE_PATH, 'data-allowed-origins': studio.origin }, injectTo: 'head-prepend' }]`
  once a Studio is known, else `[]`.
- **`apply: 'serve'`**: Vite leaves the plugin out of `vite build` (the build guarantee
  B3a tests).

## Steps

- [ ] **1. Failing tests** `test/vite-plugin.test.js`. A fake Vite dev server:

```js
import { EventEmitter } from 'node:events';

function fakeViteServer({ local = 'http://localhost:5173/', withHttpServer = true } = {}) {
  const logs = [];
  const handlers = [];
  const server = {
    config: { logger: { info: (line) => logs.push(line) } },
    httpServer: withHttpServer ? new EventEmitter() : null,
    middlewares: { use: (fn) => handlers.push(fn) },
    resolvedUrls: null,
    printUrls() { logs.push('vite urls'); },
    async close() { logs.push('vite closed'); server.httpServer?.emit('close'); },
  };
  return { server, logs, handlers, listen() { server.resolvedUrls = { local: [local], network: [] }; } };
}
```

  Mount a captured middleware on a real `node:http` server on `127.0.0.1:0` (its
  fallback answers 404 `next`), and request it with `node:http` `request`. Write a temp
  bridge file (`// bridge marker\n`) and a temp Studio file (`<title>Font Kit Studio vT</title>`)
  in a `mkdtempSync` dir; remove it in `after`. Cases:
  1. `name` is `'fontkit-studio'` and `apply` is `'serve'`;
  2. with `studio: { origin: 'http://127.0.0.1:5999', url: (t) => ... }`: the tag
     descriptor deep-equals the shape above; `attrs` has no `type`, `async` or `defer`;
     the descriptor has no `children` (no inline script);
  3. `GET /@fontkit/fontkit-bridge.js` and `GET /@fontkit/fontkit-bridge.js?v=1`: 200, the
     bridge bytes, the four headers; `HEAD`: 200, empty body;
  4. `GET /`, `GET /@fontkit/other.js`, `GET /@fontkit/../package.json`,
     `GET /@fontkit/fontkit-bridge.js/`, `GET /%40fontkit/fontkit-bridge.js` and
     `POST /@fontkit/fontkit-bridge.js`: each reaches `next()` (404 `next`);
  5. origins refused at creation, each with the fixed message and without the input in it:
     `http://example.com:5999`, `https://127.0.0.1:5999`, `http://10.0.0.5:5999`,
     `http://127.0.0.1:5999/path`, `javascript:alert(1)`, `''`;
  6. standalone: `configureServer` on the fake (with `studioFile`), `listen()`, then
     `server.printUrls()` twice: logs hold `vite urls` twice and exactly one
     `Font Kit Studio: ` line; its URL loads with 200 and the Studio marker (the target
     query is `http://localhost:5173/`); `transformIndexHtml` now carries that Studio's
     origin; `httpServer.emit('close')`, then a request to the Studio URL fails with
     `ECONNREFUSED` (await the close; no sleep);
  7. standalone with `withHttpServer: false`: `await server.close()` closes the Studio
     server (same `ECONNREFUSED` check);
  8. a missing `bridgeFile`: `configureServer` rejects with the prepack text;
  9. `transformIndexHtml` before any Studio is known (standalone, before
     `configureServer`) returns `[]`;
  10. `(await import('fontkitstudio/vite')).fontkitStudio === fontkitStudio`.
  Run `node --test test/vite-plugin.test.js` from `packages/fontkitstudio`: RED.

- [ ] **2. Implement** `src/vite-plugin.js`. Import only `node:*` and `./studio-server.js`
  (the import guard; no `createRequire`, no computed `import()`, which B1's new guard
  reserves for `src/project.js`). Flat code: one factory, one middleware function.

- [ ] **3. `package.json`**: `"exports": { "./package.json": "./package.json", "./vite": "./src/vite-plugin.js" }`.

- [ ] **4. GREEN**, then the four mutations, each restored by editing (no `git stash`).

- [ ] **5. Gates for the code phase:** `npm --prefix packages/fontkitstudio test` (the
  whole Node suite; quote the `fail 0` line), `node --check src/vite-plugin.js`. No Python
  gates.

- [ ] **6. Report** with a Handoff: the patch, a `progress.md` event draft, the commit
  subject `feat(dev): add the Vite plugin that serves and tags the bridge` and a why-body
  (the bridge comes from the app's own origin so a `script-src 'self'` CSP allows it; the
  tag pins Studio's origin without an inline script; `apply: 'serve'` keeps it out of
  every build). Note in the report: a Vite config restart creates a new plugin instance and
  so a new standalone Studio URL (known limit; the CLI path is not affected).

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B2-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B2-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B2-report.md`.
