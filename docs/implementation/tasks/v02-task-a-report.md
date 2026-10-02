# v0.2.0 Task A report: preview server and demo target app

Plan: `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md`, Task A.
Branch: the v0.2 PR branch, starting from the plan and shared-harness change. Nothing is committed.

## Files changed (only owned files)

| file | change |
|---|---|
| `scripts/serve.py` | new: stdlib dev server, one `ThreadingHTTPServer` per port, run in threads |
| `demo/index.html` | new: offline "Halyard" product landing page (target app) |
| `tests/test_preview_server.py` | new: 15 unittest cases, including one Playwright demo check |
| `.gitignore` | added `demo/fontkit-overrides.css` |
| `docs/implementation/tasks/v02-task-a-report.md` | this report |

`demo/fontkit-overrides.css` was not created and is gitignored. `fontkit-bridge.js`, Studio HTML, `tests/support.py` and the other tasks' files were not touched.

## Behaviour summary

- **CLI flags:** `--host 127.0.0.1 --studio-port 8000 --target-port 8001 --overrides demo/fontkit-overrides.css --no-sync --quiet`. `--quiet` turns off the per-request log only; the banner still prints.
- **Banner:** `Studio:  http://localhost:<studio>/font_kit_studio_v0.1.1.html?target=http://localhost:<target>/demo/`, then the Target URL, the Sync state and a "Press Ctrl-C to stop" line.
- **Both ports:**
  - Both serve the repository root.
  - `/` redirects (302) to the Studio URL on the studio port and to `/demo/` on the target port.
  - Directory listings and any dot-prefixed path segment (`.git`, `.gitignore`, temp files) return 404. Paths are checked after normalisation, so `/demo/../.git/config` is also 404.
- **Studio port only:**
  - `GET /__fontkit/status` returns `{"sync", "overrides" (repo-relative), "target": "http://localhost:<target>/demo/"}`.
  - `PUT /__fontkit/overrides.css` returns `{"ok": true, "bytes": n, "path": "<repo-relative>"}`.
  - Checks run in this order:
    1. sync disabled: 403
    2. `Origin` present and not one of `http://localhost:<studio>`, `http://127.0.0.1:<studio>` (or `http://<host>:<studio>` for a custom host): 403
    3. Content-Type not `text/css` (parameters allowed): 415
    4. no or invalid Content-Length: 411/400
    5. Content-Length over 1 MiB (1048576): 413, sent without reading the body
    6. short body: 400
  - Error responses close the connection.
  - Writes are serialised by a lock. Each write goes to a `mkstemp` file in the same directory, then `fsync`, then `os.replace`.
- **Target port:** every `/__fontkit/*` returns 404, for both GET and PUT.
- **Overrides fallback:** a missing overrides file, requested at `/<repo-relative path>`, is served as an empty `text/css; charset=utf-8` 200 on both ports.
- **Cache-Control:** every response carries `no-store`, including errors and redirects.
- **`--overrides` validation:**
  - A relative path resolves against the repo root, not the current directory.
  - Startup is refused with exit code 2 and an argparse error that names `--overrides` when the path resolves outside the repo, is the repo itself, is in or is a hidden (dot) path, is not `.css`, or is a directory.
  - Equal ports are also refused. A port already in use exits 1.
- **Shutdown:** SIGINT and SIGTERM handlers set a stop event, then both servers `shutdown()` and `server_close()`, and the process prints `Stopped.` and exits 0. Handlers are installed explicitly because a background job of a non-interactive shell inherits SIGINT as ignored. I hit that case manually: the first version ignored `kill -INT`.

**Demo (`demo/index.html`):**
- One page with inline CSS: `:root` sets `--font-display` and `--font-sans` (system font stacks), plus colour tokens.
- `<link rel="stylesheet" href="fontkit-overrides.css">` comes after the app `<style>`, then `<script src="../fontkit-bridge.js"></script>` at the end of the body. There are no inline scripts.
- **Author targets** (`data-design-id`, `data-design-role`, `data-design-name`):
  - `landing.brand.mark` (inline SVG)
  - `landing.brand.wordmark`
  - `landing.hero.title`, `landing.hero.lead`, `landing.hero.cta`
  - `landing.stat.badge` (`data-design-weights="400 600 800"`)
  - `landing.feature.{sync,preview,export}.{title,body}`
- **Un-annotated semantic content** for auto-discovery: a hero side card, section `h2`s and intros, a testimonial blockquote, pricing plans with `ul`/`li` and `button`s, FAQ `details`/`summary`, and a footer.
- **Nav** uses real in-page anchors (`#features`, `#pricing`, `#faq`; the brand link goes to `#top`). It is responsive below 820px.

## RED evidence (before `scripts/serve.py` and `demo/index.html` existed)

Command:
```
cd /home/user/font-kit-studio && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest tests.test_preview_server -v
```
Key output:
```
test_demo_loads_from_target_port ... FAIL
test_demo_source_is_offline ... ERROR   FileNotFoundError: ... demo/index.html
test_no_sync_rejects_writes ... FAIL     serve.py exited 2: can't open file '.../scripts/serve.py'
test_prints_studio_url_and_shuts_down_cleanly ... FAIL   (same)
test_refuses_overrides_outside_repo ... FAIL   'overrides' not found in "...can't open file..."
setUpClass (PreviewServerTest) ... ERROR  serve.py exited 2: can't open file '.../scripts/serve.py'
Ran 5 tests ... FAILED (failures=4, errors=2)
```
- **Fixture leak found by the first RED run:** a failed server start left `work/preview-server-*` directories behind. I fixed the fixture so it cleans up when startup fails, then re-ran. The result was the same RED set (`FAILED (failures=4, errors=2)`), with no leftovers.
- **`test_root_redirects` had no RED run.** I added it together with the root redirect, after the first GREEN run, so it has only GREEN evidence.

## GREEN evidence

```
cd /home/user/font-kit-studio && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest discover -s tests -p test_preview_server.py -v
...
Ran 15 tests in 4.667s
OK
```
The `python3 -m unittest tests.test_preview_server -v` form also passed: 14/14 before the redirect test was added. The test module adds `tests/` to `sys.path`, so both invocation forms work.

Additional checks:
- **Mutation check:** I disabled the Origin guard in `serve.py` temporarily. `test_put_rejects_foreign_origin` then failed (`FAILED (failures=1)`). I restored the file and confirmed the guard line is back.
- **Manual run:**
  - `python3 scripts/serve.py --studio-port 18000 --target-port 18001` printed the expected banner.
  - `HEAD /demo/fontkit-overrides.css` on the target port returned 200 `text/css`, length 0.
  - The status JSON was correct.
  - `kill -INT` gave `Stopped.` and the process exited.
- **Informational, not part of the suite:** with the bridge as it stood on disk at that moment, the demo loaded with no page errors. After auto-discovery it had 34 `[data-design-id]` elements.

## Deviations and interpretations

1. **`status.target`** is `http://localhost:<target>/demo/` (the demo URL, the same as the printed `?target=`). The plan says "target base url", which is ambiguous; Task C/D should use this value as is.
2. **415 for a non-`text/css` PUT.** The plan lists the request as `Content-Type: text/css`, but its error list has only 403 and 413. A plain `fetch(url, {method: 'PUT', body: string})` sends `text/plain;charset=UTF-8` and would get 415, so **Task C must set `Content-Type: text/css`**.
3. **Additions not named in the plan:**
   - dot-path 404s
   - directory listings disabled
   - `/` redirects
   - the overrides path must be `.css` and not hidden
   - equal ports refused
   - 411/400 for a missing, invalid or short body
4. **The Playwright demo check stubs `/fontkit-bridge.js`** with a one-line script, because Task B is rewriting the bridge concurrently. The test still proves the `../fontkit-bridge.js` tag resolves to the served `/fontkit-bridge.js` URL (the stub runs). It also checks:
   - every request stays on the target origin
   - the overrides stylesheet returns 200
   - all 12 author ids are present and unique
   - the overrides `<link>` is the last stylesheet and the bridge script follows it
   - the CSS custom properties are set
   - the badge has its weights
   - the mark is an SVG
   - nav anchors resolve to ids, and a click on `#features` works
   - there are at least 8 un-annotated semantic elements

   An HTTP test separately checks that `/fontkit-bridge.js` is served with a JavaScript content type. Running the real bridge end to end is left to Task D.
5. **Test scratch** lives under `work/` (gitignored) in per-server `mkdtemp` directories, removed in teardown. An empty `work/` directory may be left behind.

## Open concerns

- **No Host-header or DNS-rebinding check.** The server binds to loopback by default, and cross-origin browser PUTs already fail CORS preflight (OPTIONS is not implemented, so it returns 501). Using `--host 0.0.0.0` exposes the repo read-only, and the PUT endpoint is still gated by Origin when that header is present. Requests without an `Origin` header (curl, other local processes) are accepted by design, as the plan specifies.
- **Responses are HTTP/1.0** (the `SimpleHTTPRequestHandler` default), so there is no keep-alive. This is fine for dev use.
- **Firefox was not run** because it is not installed here (D010). The tests themselves are engine-agnostic.

## Changes after first review (review: `v02-task-a-review.md`, verdict "Approved with fixes")

### Changes

| # | finding | change |
|---|---|---|
| 1 | No Host-header check (DNS rebinding) | `Handler.host_allowed()` runs first in `do_GET`/`do_HEAD`/`do_PUT`. Accepted values (case-insensitive) are `localhost`, `127.0.0.1`, `[::1]` and the configured `--host` (unless that is `0.0.0.0`/empty), each paired with the port of the server receiving the request. A bare name is accepted only on port 80. Anything else, including a missing Host or the other port's value, gets **421** with JSON `{"ok": false, "error": "Host header not allowed"}`, `no-store`, and the connection closed. |
| 2 | Write failure gave an empty reply | `write_atomic` is wrapped in `try/except OSError` and returns **500** JSON `{"ok": false, "error": "write failed: <strerror>"}` via `fail()`. The temp file is still removed by `write_atomic`. |
| 3 | No socket timeout | `Handler.timeout = 30`. |
| 4 | `python3 -m unittest tests.test_font_kit_studio_v011` failed | Only the import header of `tests/test_font_kit_studio_v011.py` changed: added `import sys` plus the same `sys.path.insert(0, <tests dir>)` used by `test_preview_server.py`, before `from support import …`. |
| 5 | Hidden check used `urlsplit(...).path` | `clean_path()` now splits the raw `self.path` on `?` then `#`, then `unquote(errors="surrogatepass")` and `posixpath.normpath`, exactly as `translate_path` does. The `urlsplit` import was removed. |
| nit | Temp-file pattern | `.gitignore` gains `.fontkit-overrides.css.*.tmp`, the `mkstemp` name for the default overrides file. |
| nit | IPv6 names | `::`/`::1` removed from the `--host` → `localhost` URL mapping, because the server is IPv4-only. |

### New and extended tests (`tests/test_preview_server.py`)
- **`test_host_header_allow_list`:**
  - These Host values get 200 on both ports: `localhost:<port>`, `127.0.0.1:<port>`, `LOCALHOST:<port>`, `[::1]:<port>`.
  - These Host values get 421 with JSON and `no-store` on both ports: `evil.test:<port>`, `evil.test`, `localhost:<other port>`, bare `localhost`, `127.0.0.1.evil.test:<port>`. This holds for `GET /demo/`, `GET /__fontkit/status` and `PUT /__fontkit/overrides.css`, and the overrides file is never written.
- **`test_write_failure_returns_json_500`:**
  - Setup: `--overrides work/<tmp>/blocker.css/overrides.css`, where `blocker.css` is a file.
  - The PUT gets 500 with JSON `ok: false`, `write failed …` and `no-store`.
  - No temp file is left behind, the server keeps serving, and stderr has no traceback.
- **`test_hidden_check_uses_the_served_path`:** a unit test of `Handler.clean_path`, loaded with `importlib`.
  - `//.git/HEAD`, `//.git/config?x`, `/a/../.git/HEAD#f` and `/%2egit/HEAD` are all rejected (`None`).
  - `//__fontkit/status?x=1` gives `/__fontkit/status`, and `/demo/?v=2#top` gives `/demo`.
- **`test_dot_paths_are_not_served`** is extended with `//.git/HEAD`, `/%2egit/HEAD` and `//.git/config?x=1` over HTTP. These already returned 404 before the fix, because Python 3.11.15's `parse_request` collapses leading slashes, so they are characterization only. The genuine RED for finding 5 is the unit test above.

### RED evidence (tests added before the fixes)
```
FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest discover -s tests -p test_preview_server.py -v
test_write_failure_returns_json_500 ... ERROR   http.client.RemoteDisconnected: Remote end closed connection without response
test_hidden_check_uses_the_served_path ... FAIL AssertionError: '/HEAD' is not None : //.git/HEAD
test_host_header_allow_list ... FAIL            AssertionError: 200 != 421 : (49247, 'evil.test:49247', 'GET', '/demo/')
test_dot_paths_are_not_served ... ok            (characterization, see above)
Ran 18 tests in 5.952s
FAILED (failures=2, errors=1)

python3 -m unittest tests.test_font_kit_studio_v011
ImportError: Failed to import test module: test_font_kit_studio_v011
ModuleNotFoundError: No module named 'support'
```
- **Finding 3 (timeout) has no RED test.** A behavioural test would take 30 s. Instead I characterized it after the change:
  - `Handler.timeout == 30` when the module is loaded.
  - A manual probe sent PUT headers with `Content-Length: 100` and a 7-byte body, then stalled. The server dropped the connection after 30.0 s and wrote nothing. The probe directory was removed afterwards.

### GREEN evidence
```
export FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python3 -m unittest discover -s tests -p test_preview_server.py -v      -> Ran 18 tests in 5.888s  OK
python3 -m unittest discover -s tests -p test_font_kit_studio_v011.py   -> Ran 20 tests in 33.845s OK
python3 -m unittest tests.test_font_kit_studio_v011                     -> Ran 20 tests in 33.972s OK
python3 -m unittest tests.test_preview_server                           -> Ran 18 tests in 5.938s  OK
```

### Notes
- **Who the Host allow-list blocks:** with `--host 0.0.0.0`, a LAN client that uses the machine's IP in the Host header now gets 421. Only loopback names, and an explicit non-wildcard `--host`, are accepted. This is intended: the guard is against DNS rebinding.
- **The demo always links `demo/fontkit-overrides.css`**, so a non-default `--overrides` path is written but not linked. This is worth one line in the Task D README (reviewer nit).
- **Status of the remaining reviewer nits:** the IPv6 mapping nit is addressed (the names were removed, not supported). The project docs were not touched (the README line above is for Task D).
