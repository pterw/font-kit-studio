# v0.2.0 Task A review: preview server and demo target app

Reviewer: independent, read-only. Base: the plan and shared-harness change. Task A changes are uncommitted in the working tree.
Scope: `scripts/serve.py`, `demo/index.html`, `tests/test_preview_server.py`, `.gitignore`, `docs/implementation/tasks/v02-task-a-report.md`, `tests/support.py` and the harness switch in `tests/test_font_kit_studio_v011.py` (the plan and shared-harness change).

**Commands run:**
- `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest discover -s tests -p test_preview_server.py -v`: `Ran 15 tests in 5.165s OK`
- `... python3 -m unittest discover -s tests -p test_font_kit_studio_v011.py`: `Ran 20 tests in 35.642s OK`
- I started `serve.py` manually on free ports and probed it with curl and nc. The probe servers and files I created (`work/review-probe/`) were stopped and removed afterwards.

## Spec Compliance

**`scripts/serve.py`**
- ✅ **CLI flags.** `--host 127.0.0.1`, `--studio-port 8000`, `--target-port 8001`, `--overrides demo/fontkit-overrides.css` and `--no-sync` are present (scripts/serve.py:187-195). The extra `--quiet` is harmless.
- ✅ **Python stdlib only**, with one `ThreadingHTTPServer` per port (scripts/serve.py:178-183, 206-218).
- ✅ **Banner.** It prints `http://localhost:<studio>/font_kit_studio_v0.1.1.html?target=http://localhost:<target>/demo/` (scripts/serve.py:42-45, 220). The test checks the exact string (tests/test_preview_server.py:284-286).
- ✅ **Overrides path.** It must resolve inside the repo (scripts/serve.py:162-175). Symlinks are resolved at startup, the path must not be the repo root, hidden or a directory, and it must end in `.css`. Tests cover an absolute path outside the repo, `../`, `demo/../../`, a non-`.css` file and a `.git/` path (tests/test_preview_server.py:291-302).
- ✅ **`GET /__fontkit/status`** is served on the studio port only and returns `{sync, overrides, target}` (scripts/serve.py:95-100).
- ✅ **`PUT /__fontkit/overrides.css`** is accepted on the studio port only (scripts/serve.py:109-135). A sync-disabled server answers 403 (116-117). An `Origin` that is present but not the studio origin gets 403 (118-120). A body over 1 MiB gets 413 before the body is read (129-130). The success response is `{"ok": true, "bytes": n, "path": …}` (135).
- ✅ **Atomic write.** It uses `mkstemp` in the same directory, then `fsync`, then `os.replace`, all under a lock. The temp file is removed on failure (scripts/serve.py:142-159). The test checks the exact bytes and the inode change, and that no temp file is left behind (tests/test_preview_server.py:180-208).
- ✅ **`Cache-Control: no-store`** is set on every response, including `send_error` and redirects, through the `end_headers` override (scripts/serve.py:54-56). Tests check this on success, error and 404 responses.
- ✅ **Missing overrides file.** It is served as an empty `text/css` 200 on both ports, including with a query string (scripts/serve.py:103-104; tests/test_preview_server.py:246-252).
- ✅ **Target port has no `/__fontkit/*` endpoints**, for GET or PUT (scripts/serve.py:95-100, 111-115; tests/test_preview_server.py:254-262).
- ⚠️ **415 for a non-`text/css` PUT** (scripts/serve.py:121-122). This is consistent with the contract's `Content-Type: text/css`, but the contract does not list 415. The report flags it (deviation 2). Task C's client (not yet written: `grep __fontkit font_kit_studio_v0.1.1.html` finds nothing) must send `Content-Type: text/css`. This should be added to the contract or to the Task C brief.
- ⚠️ **`status.target`** is the demo URL `http://localhost:<target>/demo/`, not a bare base URL. This is a reasonable reading of "target base url" and the report discloses it (deviation 1).

**`demo/index.html`**
- ✅ **Offline.** There are no `http(s):`, protocol-relative, `@import` or `url(` references (checked with grep and with the test at tests/test_preview_server.py:306-312). The Playwright check confirms that every request stays on the target origin.
- ✅ **Author targets:**
  - `landing.brand.mark` is an inline SVG (demo/index.html:146).
  - `landing.brand.wordmark` (152).
  - `landing.stat.badge` has `data-design-weights="400 600 800"` (170-171).
  - `landing.hero.title`, `.lead` and `.cta` (172-179).
  - Six feature-card targets (205-222).
- ✅ **Un-annotated semantic content** for auto-discovery: the hero card, section heads, blockquote, pricing plans and buttons, FAQ `details`/`summary`, and the footer.
- ✅ **CSS custom properties** `--font-display` and `--font-sans` (demo/index.html:10-11).
- ✅ **Nav anchors work.** `#features`, `#pricing` and `#faq` resolve to section ids (157-159, 196, 235, 266), and `#top` resolves to `<main id="top">` (166). The test clicks `#features` and checks `location.hash`.
- ✅ **Stylesheet order.** `<link rel="stylesheet" href="fontkit-overrides.css">` comes after the app `<style>` (demo/index.html:140), and the test asserts it is the last stylesheet.
- ✅ **Bridge script.** `<script src="../fontkit-bridge.js"></script>` follows the link (294).

**Tests, `.gitignore` and harness**
- ✅ **Tests.** They cover every item in the Task A test list. Real RED evidence is recorded in the report. The one test without RED evidence (`test_root_redirects`) is disclosed honestly and covers an extra behaviour.
- ✅ **`.gitignore`** adds `demo/fontkit-overrides.css`.
- ✅ **`tests/support.py`** provides `ENGINES`, `launch` (with the executable override) and `route_virtual_origins`. The resolve-and-parents check blocks traversal. The v0.1.1 suite switch in the shared-harness change is mechanical: `ENGINES` and `launch` replace the hard-coded engines and launches, and the suite still runs 20/20 OK.

**Security posture (verified by probes against a running server)**
- ✅ **Path traversal and hidden files:** blocked. `/.git/HEAD`, `//.git/config`, `/%2egit/HEAD`, `/.%67it/HEAD`, `/demo%2f..%2f.git%2fHEAD`, `/demo/%2e%2e/.git/HEAD`, `/../../etc/passwd` and `/%2e%2e/%2e%2e/etc/passwd` all return 404. Directory listing is off (`/scripts/` returns 404).
  - The `//` form is safe because Python 3.11.15's `parse_request` collapses leading slashes before `clean_path` runs. On an older stdlib, `urlsplit` would treat `//.git/config` as a netloc. See Minor 5.
- ✅ **CSRF and Origin:**
  - A foreign `Origin` returns 403, including the target port origin, `https://localhost:<studio>` and `null`.
  - A cross-origin browser PUT also fails preflight: `OPTIONS` returns 501.
  - Chunked transfer with no Content-Length returns 411. A negative Content-Length returns 400.
- ✅ **Host binding:** the default is `127.0.0.1`. With `--host ::1` the server exits cleanly with `cannot listen`.
- ✅ **Symlinks for the overrides path:** resolved at startup, and an out-of-repo target is rejected. `os.replace` replaces a symlink created later rather than writing through it. The repo contains no other symlinks (`find -type l` is empty).
- ✅ **Request size:** a body over 1 MiB gets 413 without being read, and the connection is closed.
- ⚠️ **DNS rebinding:** there is no Host header check. GET with `Host: evil.test:<port>` returns 200. PUT under the same rebinding is still refused, because the browser sends `Origin: http://evil.test:<port>` and gets 403. See Minor 1.

## Strengths

- **Small and readable server.** Endpoint gating is strict and correct (studio-only, exact path match after normalisation), and errors close the connection.
- **Correct atomic write.** It uses a same-directory temp file, fsync and `os.replace`, a lock for serialisation, cleanup on failure, and a dot-prefixed temp name, which is never served.
- **Clean `--overrides` validation.** Relative paths resolve against the repo, not the current directory, and the errors name the flag.
- **Clean signal handling.** It handles SIGINT and SIGTERM, including the inherited-ignored SIGINT case found during implementation. The test checks exit code 0 and no traceback.
- **Behavioural tests, not presence checks.**
  - Exact bytes and an inode change for the atomic swap.
  - A boundary test at exactly 1 MiB (accepted) and 1 MiB + 1 (rejected, file untouched).
  - Five foreign-origin variants.
  - A real Playwright load of the demo from the target port, with the bridge stubbed because Task B is rewriting it concurrently.
- **Well-designed demo.** It is realistic and fully offline, with a good mix of authored and auto-discoverable elements and a responsive layout.
- **Honest report.** The RED evidence, missing RED for the redirect test, the mutation check, deviations and open concerns are all disclosed.

## Issues

### Critical
None.

### Important
None verified.

### Minor

1. **No Host header allow-list, so repo files are readable under DNS rebinding** (scripts/serve.py:91-105). This is verified: `curl -H 'Host: evil.test:<port>' http://127.0.0.1:<port>/README.md` returns 200.
   - **Scenario:** a malicious site the developer visits while `serve.py` runs rebinds its hostname to 127.0.0.1. It can then read any non-dot file in the repo, including `work/` scratch and the status JSON.
   - **What still holds:** writes stay protected by the Origin check, and the exposure is no worse than `python -m http.server`. The report discloses it under Open concerns.
   - **Fix:** in `do_GET`/`do_PUT`, reject requests whose `Host` (port included) is not one of `localhost`, `127.0.0.1`, `[::1]` or the configured `--host`, paired with the server's own port. Respond 421 or 403 and add one test. This is cheap defence in depth that common dev servers (Vite, webpack-dev-server) apply.

2. **A failed write gives an empty reply instead of a JSON error** (scripts/serve.py:134, 142-159). This is verified with `--overrides work/review-probe/o.css/x.css`, where the parent is a file.
   - **Result:** the PUT gets `curl: (52) Empty reply from server`. The stderr traceback ends in `FileExistsError`.
   - **Other real causes:** a read-only directory, `EACCES` or a full disk (`ENOSPC`).
   - **Effect:** Studio sees an opaque network failure rather than `{"ok": false, "error": …}`.
   - **Fix:** wrap `write_atomic` in `try/except OSError as e: return self.fail(500, f"write failed: {e.strerror}")`.

3. **No socket timeout** (scripts/serve.py:50). `Handler.timeout` is unset, so the stdlib default is `None`. A client that declares `Content-Length: 1048576` and then stalls holds a worker thread in `rfile.read` indefinitely.
   - **Impact:** low on loopback, because the threads are daemon threads and shutdown still works.
   - **Fix:** set `timeout = 30` on `Handler`.

4. **The v0.1.1 suite can no longer be run by module path** (tests/test_font_kit_studio_v011.py:10, from the shared-harness change). `from support import …` has no `sys.path` insert, so `python3 -m unittest tests.test_font_kit_studio_v011…` now fails with `ModuleNotFoundError: No module named 'support'` (verified).
   - The documented `discover -s tests` form works.
   - `tests/test_preview_server.py:17` inserts the path itself, so the two modules are inconsistent.
   - **Fix:** add the same `sys.path.insert` to `test_font_kit_studio_v011.py`, or document discover as the only supported form.

5. **`clean_path` relies on the stdlib collapsing a leading `//`** (scripts/serve.py:62-68). `urlsplit("//.git/config").path` is `/config`, while `translate_path` would map the same request to `.git/config`. This is safe on the Python 3.11.15 used here, because `parse_request` has normalised leading slashes since the gh-87389 fix (verified: 404). An unpatched older interpreter would bypass the dot-path check.
   - **Fix:** apply the hidden-segment check to the same string `translate_path` uses, for example `self.path.split('?', 1)[0].split('#', 1)[0]` after unquote and normpath, instead of `urlsplit(...).path`. Add `//.git/HEAD` to `test_dot_paths_are_not_served`.

6. **Nits:**
   - `Config` maps `--host ::1`/`::` to `localhost` (scripts/serve.py:42), but the `ThreadingHTTPServer` is IPv4-only, so those hosts can never bind. Drop them from the mapping or set `address_family` for IPv6 hosts.
   - A SIGKILL during a write can leave `demo/.fontkit-overrides.css.*.tmp` behind. It is never served, but it is not gitignored. Consider adding `demo/.fontkit-overrides.css.*.tmp`.
   - The demo always links `fontkit-overrides.css`. A non-default `--overrides` path will be written but not linked by the demo. This is expected, but worth one line in the Task D README.

## Assessment

**Task quality: Approved with fixes**

- **Every Task A requirement is met and demonstrated:**
  - All the "Dev server endpoints" contract items.
  - The demo, with all named author targets, offline, overrides link order and bridge include.
  - `.gitignore`.
  - Tests first, with RED and GREEN evidence.
- **Results:**
  - 15/15 preview tests pass.
  - The shared harness switch keeps the v0.1.1 suite at 20/20.
  - All the traversal, hidden-file, Origin, size and target-port probes behave correctly.
- **No Critical or Important defect was found.**
- **Recommended before Task D integration (small, local fixes):**
  - Minor 1, the Host allow-list. Writes are already protected, but the user explicitly cares about DNS rebinding.
  - Minor 2, a JSON 500 on write failure, so Studio's sync status can show a real error.
- **Handled outside Task A code:**
  - The 415 / `Content-Type: text/css` requirement must be passed to Task C.
- **Optional:** Minors 3 to 6.

## Re-review after first changes

Scope: the "Changes after first review" section of `v02-task-a-report.md`, `scripts/serve.py`, `tests/test_preview_server.py`, the `tests/test_font_kit_studio_v011.py` import header and `.gitignore`. The base now includes a docs-only commit. Task A remains uncommitted. `font_kit_studio_v0.1.1.html` also shows as modified now; that is Task C's concurrent work and is out of scope here. I modified no repository file except this review. Probe servers and `work/review-probe2/` were stopped and removed.

### Suites run
Commands were run with `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium` exported. Firefox is not installed (D010).
- `python3 -m unittest discover -s tests -p test_preview_server.py`: `Ran 18 tests in 5.825s OK`
- `python3 -m unittest tests.test_font_kit_studio_v011`: `Ran 20 tests in 33.519s OK`. This module-path form failed before the fix; I reproduced the `ModuleNotFoundError` in the first review.
- `python3 -m unittest tests.test_preview_server`: `Ran 18 tests in 6.373s OK`

### Per-finding verification
- ✅ **Minor 1, Host allow-list** (scripts/serve.py:50-56, 106-111, 113-115, 133-135).
  - **Gate:** `host_allowed()` runs first in GET, HEAD and PUT. It compares against `{localhost, 127.0.0.1, [::1], configured --host}`, each paired with the port of the server that received the request. A bare name is accepted only on port 80.
  - **Raw-socket probes on the studio port:**
    - Return 421 with JSON and `no-store`: missing Host, empty Host, an HTTP/1.0 request with no Host, `localhost.:<port>`, `localhost:0<port>`, and a first Host header `a`.
    - Return 200: `localhost:<port>`, and the same with trailing whitespace, which is stripped.
    - An absolute-form request line `GET http://evil.test/demo/` with a valid Host never reaches a file: it returns 404.
  - **New test** `test_host_header_allow_list` covers both ports, a foreign host, a bare host, the other port, the `127.0.0.1.evil.test` suffix trick and case-insensitivity. It checks GET and PUT, and that the overrides file is never written.
  - **Ordinary use is not broken:**
    - In Chromium, Studio opened from `http://localhost:<S>/` and from `http://127.0.0.1:<S>/` followed the redirect and loaded with no page errors and no HTTP status of 400 or above. A same-origin `fetch('/__fontkit/status')` returned 200, and a `PUT` with `text/css` returned 200 `{"ok": true, "bytes": 9}`. The file was written.
    - A demo iframe loaded and rendered its 12 author ids for each Studio→target pairing: `localhost→localhost`, `127.0.0.1→127.0.0.1` and `127.0.0.1→localhost`. The bridge was stubbed.
    - The suite's Playwright demo load (`test_demo_loads_from_target_port`) passes.
- ✅ **Minor 2, JSON 500 on write failure** (scripts/serve.py:160-163). `OSError` now becomes `fail(500, "write failed: <strerror>")`, with `no-store` and the connection closed. `write_atomic` still removes its temp file. `test_write_failure_returns_json_500` reproduces my blocker-file scenario. It asserts 500 with JSON, no stray files, that the server is still serving, and that stderr has no traceback. The test passes.
- ✅ **Minor 3, socket timeout** (scripts/serve.py:62). `Handler.timeout = 30`. Manual probe: PUT headers with `Content-Length: 100`, 3 body bytes, then a stall. The server closed the connection after 30.0 s and the overrides file was left unchanged. There is no automated test; a 30 s test is reasonable to skip, and the report characterizes it honestly.
- ✅ **Minor 4, module-path import** (tests/test_font_kit_studio_v011.py:4, 11-12). `git diff` shows only `import sys`, a `sys.path.insert(0, <tests dir>)` and a `# noqa: E402` on the `support` import. No test body changed. The module-path form now runs 20/20.
- ✅ **Minor 5, hidden check uses the served path** (scripts/serve.py:72-83).
  - `clean_path` now splits the raw `self.path` on `?` then `#`, then unquotes with `surrogatepass` and runs `normpath`, mirroring `translate_path`. `urlsplit` is gone.
  - `test_hidden_check_uses_the_served_path` tests the function directly, which is the genuine RED, independent of the stdlib's `//` collapsing. Cases: `//.git/HEAD`, `//.git/config?x`, `/a/../.git/HEAD#f` and `/%2egit/HEAD` are rejected; `//__fontkit/status?x=1` and `/demo/?v=2#top` are normalised. The HTTP-level `//` cases are correctly labelled characterization only.
- ✅ **Nit, temp-file pattern** (.gitignore:6). `git check-ignore` confirms that `demo/.fontkit-overrides.css.abc123.tmp` and `demo/fontkit-overrides.css` are ignored and `demo/index.html` is not.
- ✅ **Nit, IPv6 names** (scripts/serve.py:43). `::` and `::1` are no longer mapped to `localhost`. The server is IPv4-only, and `--host ::1` still exits with "cannot listen".
- ✅ **Contract unchanged:** status, PUT, Origin, 413, 415, `no-store`, the empty-overrides fallback and the target-port 404s all still pass their existing tests.

### Residual observations (no action required)
- **Duplicate `Host` headers:** only the first one is checked. Browsers never send duplicates, and the first value must still be an allowed one, so this is harmless.
- **`--host 0.0.0.0`:** LAN clients that use the machine's IP now get 421. The report documents this as intended. Task D's README should say that remote access requires an explicit `--host <ip>`.
- **README line for Task D (open):** the earlier nit still applies. A non-default `--overrides` path is written but not linked by the demo.
- **Task C dependency (open):** Task C must send `Content-Type: text/css`, or it gets 415.

### Verdict
**Task quality: Approved.** All five Minor findings and both nits were fixed and verified concretely. There are RED tests for 1, 2, 4 and 5, and an honest characterization for 3. Both suites are green, including the module-path form. The Host allow-list does not affect normal localhost or 127.0.0.1 use of Studio, the status and sync endpoints, or the cross-origin demo load. No new issues were found.
