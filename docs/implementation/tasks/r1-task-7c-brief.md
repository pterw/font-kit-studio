# R1 7c brief: no CSP warning for a policy that allows the bridge

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (7c, a follow-up to R1.6's messages).
Constraints: `.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first). Code:
`packages/fontkitstudio/src/csp.js`, the callers in `src/vite-plugin.js` (lines about 102
and 150) and `src/proxy.js` (about 122-127). Read all three first.

## Goal

The plugin and the proxy say once per run that a page's Content-Security-Policy blocks the
bridge (`CSP_MESSAGE`). Today any `script-src` without `'self'`, `*` or `http:` counts as
blocking. A source that names the page's own origin, for example `script-src
http://localhost:5173`, also allows the bridge (served at `/@fontkit/fontkit-bridge.js` from
that origin), so users get a false warning telling them to change a policy that is fine.

## Owns

- `packages/fontkitstudio/src/csp.js`;
- the two call sites in `src/vite-plugin.js` and `src/proxy.js`, and only what they need to
  pass the origin;
- `test/csp.test.js`;
- additions to `test/vite-plugin.test.js` and `test/proxy.test.js`.

## Interface (binding)

```js
// csp.js
export function blocksSameOriginScript(policy, pageOrigin) // pageOrigin optional, e.g. 'http://localhost:5173'
```

With `pageOrigin` undefined, behaviour is exactly today's (every existing test passes
unchanged).

## Rules (CSP Level 3 source matching, only as far as the bridge needs)

The deciding directive stays the first of `script-src-elem`, `script-src`, `default-src`
the policy sets. Then:
- `'strict-dynamic'` still blocks. With it, host-sources and `'self'` are ignored.
- `'self'`, `*`, `http:` allow, as today.
- A host-source allows when it matches `pageOrigin`, compared without case:
  - **Scheme:** an optional scheme must be `http:` (a page on http). `https://localhost:5173`
    does not match. A scheme-less source matches an http page.
  - **Host:** exact host (`localhost`, `127.0.0.1`, `[::1]`). `*.example.com` never matches
    a loopback page. `localhost` does not match `127.0.0.1`: the browser compares names, not
    addresses.
  - **Port:** an explicit port must equal the page's (default 80 when the page has none).
    `:*` matches any port. A missing port means the scheme's default, 80.
  - **Path:** none, or one that matches `/@fontkit/fontkit-bridge.js` (a path ending in `/`
    matches as a prefix; otherwise exact).
- Anything malformed counts as not matching, so the warning stays on (a false warning beats
  a missed one).

## Callers

- **Plugin:** pass the origin Studio opens the app at. Today's header check runs in
  `configResolved`, before the origin is known.
  - Keep the header policies, and decide once the server's URL is known: the first of
    `server.resolvedUrls.local` after listen, or the origin of the target URL the plugin
    gives Studio, whichever the code already has at `transformIndexHtml` time.
  - Meta policies are checked per page, as today.
  - Say in the report which origin you used and why it is the one the browser loads.
- **Proxy:** pass the proxy's own origin (`proxyOrigin`). The page is served from the
  proxy, so a policy naming the target's port really does block the bridge, and still
  warns.

## Tests

- **`test/csp.test.js` allows:**
  - the full origin;
  - a host and port;
  - a scheme-less host and port;
  - `localhost:*`;
  - a path prefix `/@fontkit/`;
  - the exact bridge path;
  - the same source in `script-src-elem` with a blocking `script-src`, because
    `script-src-elem` decides.
- **`test/csp.test.js` blocks (hostile cases):**
  - another port;
  - `127.0.0.1` for a `localhost` page;
  - `https://` with the same host and port;
  - path `/js/`;
  - `*.localhost`;
  - an empty `script-src`;
  - `'strict-dynamic'` together with a matching host;
  - a garbage source;
  - two policies where the second blocks (comma-separated, and an array).
- **Callers:**
  - In `test/vite-plugin.test.js`, a server whose `server.headers` CSP names its own origin
    prints no CSP warning; one that names another port warns once.
  - In `test/proxy.test.js`, a target page whose CSP names the target's own port warns,
    because the page is served from the proxy, and one naming the proxy's origin does not.
- **Mutations,** each shown failing and restored by editing:
  - drop the port comparison;
  - drop the scheme check;
  - drop the path rule;
  - pass no origin from the plugin.

## Definition of done

- RED, then GREEN: `npm --prefix packages/fontkitstudio test`.
- Also run `PYTHONPATH=tests python -m unittest test_one_command_vite test_one_command_proxy
  -v` with `npm ci` done for `fixtures/vite-react` and `fixtures/vite7-react` in your
  worktree. Its CSP assertions must still hold.
- Run `python -m ruff check .`.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-7c-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-7c-code.patch`.
- Handoff:
  - **CHANGELOG.** A line for `CHANGELOG.md` under Unreleased, in a `### Fixed` block, for
    example: "The CSP warning no longer fires for a `script-src` that names the dev server's
    own address."
  - **Ledger.** A `progress.md` event draft.
  - **Commit.** The subject `fix(dev): stop the CSP warning for a policy that allows the
    bridge`, with a why-body.
