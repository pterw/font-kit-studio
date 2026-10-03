# v0.2.1 Task 2 brief: First run, dev server

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 2 and decisions 2 and 3.
Base: `d3a37e9` on `ccr-9eab25c9-mgatzt`. Implementer role: Ligature (tooling).

## Problems (audit, `docs/implementation/audit-2026-10-03-first-run-and-controls.md`)

`scripts/serve.py` (`main` at line 248, `make_server` at 240):

1. A busy port prints `serve.py: cannot listen: [Errno 98] Address already in use` with no
   port number and no flag to change it.
2. It prints a Studio URL and a Target URL and does not say which one to open.
3. It never opens a browser; the plan decides: no browser by default, `--open` on request.
4. A browser request that hits the Host check gets raw `421` JSON.
5. On Windows, `ThreadingHTTPServer.allow_reuse_address` is true by default, so a second
   server may bind a taken port (code reading, untested).
6. The audit says every target load logs a 404 for `demo/fontkit-overrides.css`. The
   server already answers a missing overrides file with empty CSS (`serve.py:150`,
   `test_missing_overrides_is_empty_css_on_both_ports`). Characterize this in a real
   browser: load the demo from the target port with no overrides file present and assert
   no 4xx response for that path. If a 404 still appears, find the path that misses and
   fix that; do not create the file on start.

## Required behaviour

- Busy port: the message names the port and the flag (`--studio-port 8000 is in use; pick
  another with --studio-port <port>`, likewise for the target port) and exits 1. Detect
  which of the two binds failed.
- Output: the last line printed before waiting is `Open: <Studio URL>` (the Studio URL
  with `?target=<demo URL>`), after the existing lines. Keep the existing lines; the
  lifecycle test reads them.
- `--open`: after both servers listen, call `webbrowser.open(<that Studio URL>)` once. Off
  by default. Print nothing extra when it is off.
- `421`: when the request's `Accept` header contains `text/html`, answer with a short HTML
  page (plain, no scripts, no external resources) that names the host the server accepts
  and says to pass `--host <address>` to allow another. Other requests keep the JSON.
- Windows: when `sys.platform == "win32"`, the servers are created with
  `allow_reuse_address = False`. Unit test by patching `sys.platform` and asserting on the
  server object; do not try to bind twice.
- README (`Quickstart` and `Dev server options` only): say that `Open:` is the line to use;
  add `--open` to the options table; note that on Windows `python` may be the Store stub
  and `py -3` or `python3` works.

## Tests (write first, watch them fail, then fix)

In `tests/test_preview_server.py`, next to `PreviewServerLifecycleTest` (read how
`test_prints_studio_url_and_shuts_down_cleanly` starts and stops `main`; reuse it):

- busy studio port and busy target port: hold a socket on an OS-assigned free port, run
  `main` with that port, assert exit 1 and that stderr names the port and the flag.
- the last printed line before the wait starts with `Open: ` and is the Studio URL with
  the demo target.
- `--open` calls `webbrowser.open` exactly once with that URL; without it, never.
- `421` with `Accept: text/html` returns `text/html` naming `--host`; without it, JSON.
- `allow_reuse_address` is False under a patched `win32` platform and unchanged elsewhere.
- the demo loads in Chromium from the target port with no overrides file and no response
  for `fontkit-overrides.css` has status >= 400 (use the browser fixtures already in this
  module's `DemoPageTest`).

## Owned files

`scripts/serve.py`, `tests/test_preview_server.py`, `README.md` (the two named sections
only). Touch nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_preview_server
```

Never run `playwright install`. Stop only processes you started, by PID; every server you
start is stopped in `finally` or `tearDown`. No `sleep` polling. Do not commit or push.
First command: `git rev-parse HEAD`; if it is not `d3a37e9`, run
`git merge --ff-only origin/ccr-9eab25c9-mgatzt` before editing.

## Report

Append your report under this heading in this file: RED evidence (test names and the
failure text), the fix (functions touched, with line numbers), GREEN evidence (test count
for the module), what you did not verify (Windows is code reading only; say so).
