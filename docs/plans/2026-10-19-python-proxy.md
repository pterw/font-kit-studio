# Python proxy in serve.py: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> In this repository implementers never commit: code phases return a patch, the controller lands (AGENTS.md).

**Goal:** `python serve.py http://127.0.0.1:5000` opens Studio connected to a running app with no Node, no install
and no pasted script.

**Architecture:** `scripts/serve.py` gains an optional target URL. With it, serve.py runs Studio's server and a
standard-library reverse proxy that adds the bridge tag to HTML pages and serves the bridge, following the Node
proxy's tested behaviour (`packages/fontkitstudio/src/proxy.js`, `csp.js`). Design and exact strings:
[the spec](../specs/2026-10-19-python-proxy-design.md). Ships in 0.4.0 under R2 plan Addendum 29.

**Tech Stack:** Python 3.11 standard library only (`http.server`, `http.client`, `socket`, `selectors`, `re`),
`unittest` + Playwright for tests, Node `node:test` for the shared parity cases.

## Global Constraints

- serve.py stays one standard-library file; no new runtime or test dependency.
- Loopback only: target `http:` on `localhost`, `127.0.0.1` or `[::1]`; both servers bind loopback.
- Bridge path `/@fontkit/fontkit-bridge.js`; tag
  `<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="<Studio origin>"></script>`.
- Strings exactly as the spec's "Strings (exact)" section.
- Without a target URL, serve.py's behaviour and output are unchanged (existing `test_preview_server` stays green).
- Tests: Given/When/Then docstrings whose Then equals the assertions; independent oracles; one realistic mutant per
  new test shown failing; no fixed sleeps; free ports; servers stopped in `finally`; HTTPS blocked in browser tests
  (D059).
- One writer per file. PR line budget: material lines stay under 7,700 (D050, D065).

## File structure

| File | Responsibility | Task |
|---|---|---|
| `tests/fixtures/proxy-insert-cases.json` | Shared tag-placement cases (input page, expected output) | PX1 |
| `packages/fontkitstudio/test/proxy.test.js` | Node proxy reads the shared cases | PX1 |
| `scripts/serve.py` | Target URL, file lookup, proxy handler, warnings, WebSocket tunnel | PX2, then PX3 |
| `tests/test_serve_proxy.py` | Behaviour tests of the Python proxy | PX2, then PX3 |
| `tests/test_r2_entrypoints.py` | Real Studio + bridge through the Python proxy | PX4 |
| `.github/workflows/release.yml`, `tests/test_release.py` | Release ships `scripts/serve.py` as an asset | PX5 |
| README, CHANGELOG, verification, ledger | Docs and evidence | controller |

Parallel order: PX1 and PX5 start at once; PX2 starts on PX1's patch; PX3 and PX4 start on PX2's patch (PX4 also after
FU-RT and FU-CSSE, which own `tests/test_r2_entrypoints.py` first). Each task lands as its own commit.

### Task PX1: shared tag-placement cases

**Touches:** `tests/fixtures/proxy-insert-cases.json` (create), `packages/fontkitstudio/test/proxy.test.js`.
**After:** this plan's docs commit.

**Interfaces:**
- Produces: a JSON array of `{"name": str, "input": str, "expected": str}`, where `input`/`expected` are latin-1
  strings and the tag in `expected` is written as the literal `{TAG}` placeholder. Consumers replace `{TAG}` with
  their tag before comparing. PX2's Python test reads the same file.

- [ ] Step 1: write the JSON with these cases, each `expected` derived by hand from the spec rule: after `<head>`;
  `<HEAD lang="x">`; no head, after `<html>`; `<header>` but no `<head>` (tag after `<html>`, never after `<header>`);
  doctype only; UTF-8 BOM + doctype; no markers (tag at 0); empty page; a `<head>` inside a comment after a real
  `<head>` (first match wins).
- [ ] Step 2: in `proxy.test.js`, add one test that loads the file and asserts `insertTag(Buffer.from(input,
  'latin1'), TAG)` equals `expected` with `{TAG}` replaced, for every case. Run
  `npm --prefix packages/fontkitstudio test` and show it passing; show a mutant (`<head` regex changed to `<he`)
  failing.
- [ ] Step 3: the patch and report; commit subject `test: share the proxy's tag-placement cases`.

### Task PX2: serve.py target URL and HTTP proxy

**Touches:** `scripts/serve.py`, `tests/test_serve_proxy.py` (create). **After:** PX1 (its JSON as PATCH_DEP).

**Interfaces (produced, used by PX3 and PX4):**

```python
BRIDGE_PATH = "/@fontkit/fontkit-bridge.js"
TARGET_ERROR = "Font Kit Studio proxies only a local dev server (localhost, 127.0.0.1 or [::1])"
LOOPBACK_URL_HOSTS = ("localhost", "127.0.0.1", "[::1]")

def parse_target(url: str) -> urllib.parse.SplitResult:
    """The one check of the address to proxy; raises ValueError(TARGET_ERROR)."""

def insert_tag(page: bytes, tag: bytes) -> bytes:
    """After <head ...>, else <html ...>, else a leading (BOM +) doctype, else at 0. Byte-preserving."""
    for pattern in (rb"<head(\s[^>]*)?>", rb"<html(\s[^>]*)?>", rb"^(\xef\xbb\xbf)?\s*<!doctype[^>]*>"):
        found = re.search(pattern, page, re.IGNORECASE)
        if found:
            return page[:found.end()] + tag + page[found.end():]
    return tag + page

def rewrite_location(value: str, target_port: int, proxy_origin: str) -> str:
    """Absolute or //-relative http: Location under a loopback name and the target port -> proxy origin + rest."""

def find_asset(name: str) -> Path:
    """Next to serve.py first, then the repository root."""

def run_proxy(config, target, studio_origin) -> ThreadingHTTPServer:
    """The proxy server on config's proxy port; requests forwarded with http.client."""
```

`main(argv)` gains `parser.add_argument("target", nargs="?")`. With a target: Studio's server on `--studio-port`,
the proxy on `--target-port`, sync off, host names from the target (spec "Shape" item 2), output lines `Studio:`,
`App:`, `Press Ctrl-C to stop.`, `Open:`; a bad target prints `serve.py: ` + `TARGET_ERROR` to stderr and returns 1.

- [ ] Step 1: write `tests/test_serve_proxy.py` with a `FakeApp` (a `ThreadingHTTPServer` on a free port inside
  the test, routes: `/` HTML page, `/style.css`, `/redirect-abs` (Location `http://127.0.0.1:<app port>/x`),
  `/redirect-rel` (Location `/x`), `/cookie` (two `Set-Cookie` headers and a CSP header), `/echo-headers` (returns
  the request's `Host`, `Origin`, `Accept-Encoding` as JSON)) and a helper that starts the real serve.py with
  `--studio-port 0`-style free ports and the app URL, reads its `Open:` line and stops it in `finally` (reuse
  `tests/test_preview_server.py`'s process helpers where they fit). Tests, each with a Given/When/Then docstring:
  1. The HTML page through the proxy equals the app's page with exactly one tag inserted per `insert_tag`'s rule
     (oracle: the JSON cases for the rule, the spec tag literal for the bytes).
  2. `/style.css` through the proxy is byte-identical and carries no tag.
  3. `/redirect-abs` comes back with Location on the proxy origin; `/redirect-rel` unchanged.
  4. `GET /@fontkit/fontkit-bridge.js` (and with `?v=1`) returns the repository's `fontkit-bridge.js` bytes; the
     app never sees that request.
  5. `/cookie`: both `Set-Cookie` values and the CSP header arrive unchanged.
  6. `/echo-headers`: the app saw its own `Host`, `Accept-Encoding: identity` and an `Origin` rewritten from the
     proxy's origin to the app's.
  7. `https://127.0.0.1:5000`, `http://example.com` and `ftp://localhost` exit 1 with exactly the refusal line.
  8. App stopped: the proxy answers 502 with the spec's text; app restarted on the same port: the next request
     succeeds.
  9. Studio's server refuses a foreign `Host` (421) as today, in proxy mode too, and serves no repository file
     but Studio (`GET /README.md` is 404 in proxy mode).
  10. The JSON cases all pass through `insert_tag` (parity with PX1).
  11. Release layout: `serve.py`, `fontkit-studio.html` and `fontkit-bridge.js` copied alone into a temporary
      folder: proxy mode serves the tagged page and the bridge; without a URL it prints the spec's plain-mode
      line and exits 1.
  12. Host names: a `http://localhost:<port>` target gives `localhost` Studio and proxy addresses in the `Open:`
      line; `127.0.0.1` gives `127.0.0.1`; `[::1]` gives `127.0.0.1` (spec "Shape" item 2).
- [ ] Step 2: run them at BASE: all fail (no target argument). Record the output.
- [ ] Step 3: implement in serve.py: `parse_target`, `insert_tag`, `rewrite_location`, `find_asset`, the proxy
  handler (all methods forward; request headers per spec "Each request"; HTML buffered and tagged when the response
  is `text/html` with identity encoding, else streamed chunk by chunk with a `read1` loop; bridge path served
  locally), `Config` host names for proxy mode, and the `main` branch.
- [ ] Step 4: run `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_serve_proxy test_preview_server
  test_support -v`: all pass. Show one mutant per test failing (examples: tag inserted twice; CSS buffered and
  tagged; `Set-Cookie` folded into one header; `Origin` not rewritten; 502 handler crashing the server).
- [ ] Step 5: patch and report; commit subject `feat(dev): proxy a local app from serve.py without Node`.

### Task PX3: warnings and WebSocket tunnel

**Touches:** `scripts/serve.py`, `tests/test_serve_proxy.py`. **After:** PX2.

**Interfaces:**

```python
CSP_MESSAGE = ("Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the "
               "page's own scripts). Add 'self' to script-src while you develop.")
BRIDGE_TWICE_MESSAGE = ("Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not "
                        "connect, remove that script while you use serve.py.")

def blocks_same_origin_script(policy: str, page_origin: str) -> bool: ...   # port of csp.js blocksSameOriginScript
def meta_policies(html: str) -> list[str]: ...                              # port of csp.js metaPolicies
def loads_own_bridge(html: str) -> bool: ...                                # port of csp.js loadsOwnBridge
def tunnel(client: socket.socket, upstream: socket.socket) -> None: ...     # raw bytes both ways until either closes
```

- [ ] Step 1: tests (Given/When/Then): a page with `Content-Security-Policy: script-src 'none'` requested twice
  prints `CSP_MESSAGE` exactly once on stderr; the same for a `<meta http-equiv>` policy; a page that loads its own
  `/@fontkit/fontkit-bridge.js` prints `BRIDGE_TWICE_MESSAGE` once; a policy allowing `'self'` prints nothing; a
  WebSocket client (raw socket handshake in the test, no dependency) sends a frame through the proxy to a `FakeApp`
  echo endpoint and receives it back. Port the CSP cases from `packages/fontkitstudio/test/csp.test.js` as literal
  rows (oracle: the Node test's expectations).
- [ ] Step 2: run at PX2's patch: they fail. Record.
- [ ] Step 3: implement the three CSP functions (one-to-one with `csp.js`), call them on each HTML page before
  forwarding (once-per-run flags), and the `Upgrade: websocket` path: open a raw socket to the app, replay the
  request head, then `tunnel`.
- [ ] Step 4: run the PX2 command: all pass; mutants: warning printed per page; CSP directive order ignored
  (`default-src` beating `script-src`); tunnel closing after the first frame.
- [ ] Step 5: patch and report; commit subject `feat(dev): warn on blocked bridges and pass WebSockets in serve.py`.

### Task PX4: end-to-end through the Python proxy

**Touches:** `tests/test_r2_entrypoints.py` (a new `PythonProxyEntrypointTests(RoundTrip, unittest.TestCase)` class
only). **After:** PX2, FU-RT, FU-CSSE.

- [ ] Step 1: the class starts the real serve.py with a target: a static server for
  `fixtures/bootstrap5-static` started by the test on a free port (the same pages `ProxyEntrypointTests` uses), and
  runs `round_trip` with the same Bootstrap 5 case literals `ProxyEntrypointTests` uses (oracle: those literals and
  the fixture's `expected-styles.json`). No Node: no `skipIf(NODE is None)`.
- [ ] Step 2: show it failing at PX2's BASE without the proxy mode (refusal or no bridge), then passing with PX2;
  show a mutant (proxy tags nothing) failing at Detect.
- [ ] Step 3: run `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest
  test_r2_entrypoints.PythonProxyEntrypointTests test_support -v`. CI: the main suite runs it (no fixture install
  needed); confirm it is not skipped there.
- [ ] Step 4: patch and report; commit subject `test: run the role round trip through serve.py's proxy`.

### Task PX5: release asset

**Touches:** `.github/workflows/release.yml`, `tests/test_release.py`. **After:** this plan's docs commit.

- [ ] Step 1: a test in `tests/test_release.py` asserting the `gh release create` step lists `scripts/serve.py`
  beside `fontkit-studio.html fontkit-bridge.js` (oracle: the spec's packaging sentence). It fails at BASE.
- [ ] Step 2: add `scripts/serve.py` to that step's file list (the asset is named `serve.py`; use
  `scripts/serve.py#serve.py` only if `gh` needs the label form - check `gh release create --help`).
- [ ] Step 3: run `PYTHONPATH=tests python -m unittest test_release -v`; mutant: the line without serve.py fails.
- [ ] Step 4: patch and report; commit subject `ci: ship serve.py with the release assets`.

### Controller: docs and evidence

- [ ] README: a "No Node: the Python proxy" subsection beside the proxy command, the test-table row for
  `test_serve_proxy.py`, the known limits from the spec; CHANGELOG Unreleased line (folded into [0.4.0]); release
  verification records the downloaded `serve.py` asset's SHA-256 and a run of it from an empty folder against a
  local static page.
- [ ] Live check against the owner's app: `python scripts/serve.py http://127.0.0.1:5000`, Detect, Apply, Clear.
