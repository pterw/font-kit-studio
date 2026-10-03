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

### Implementer report (Ligature, 2026-10-03)

Base: the worktree started at `a6d2751`; fast-forwarded to `5917f56` (origin/ccr-9eab25c9-mgatzt)
before editing. Not committed.

**RED** (`python -m unittest tests.test_preview_server`, 32 tests, 7 failures, written before the fix):

- `test_busy_port_names_the_port_and_the_flag` (both subtests): stderr was
  `serve.py: cannot listen: [Errno 98] Address already in use`, expected
  `--studio-port <port> is in use; pick another with --studio-port <port>` (same for target).
- `test_last_line_before_the_wait_is_the_url_to_open`: last line was `Press Ctrl-C to stop.`.
- `test_open_flag_opens_the_studio_url_once`: `serve.py: error: unrecognized arguments: --open`.
- `test_browser_is_not_opened_without_the_flag`: no `Open:` line in stdout.
- `test_misdirected_browser_request_gets_a_readable_page`: `'text/html' not found in 'application/json'`.
- `test_windows_never_shares_a_port` (`win32` subtest): `True is not False` (the linux and darwin
  subtests already passed as characterization of the unchanged default).
- Item 6 characterization `test_demo_loads_without_any_overrides_request_failing`: PASSED before any
  code change (Chromium, no overrides file, no response for `fontkit-overrides.css` with status >= 400,
  the empty sheet applies, the file is not created). No server code was changed for it.

**Fix** (`scripts/serve.py`):

- `main` (about lines 275-330): binds the studio and target servers one at a time, so the failing
  one is known. `EADDRINUSE` (and `WSAEADDRINUSE` when the platform has it) prints
  `serve.py: --studio-port N is in use; pick another with --studio-port <port>` (likewise
  `--target-port`) and exits 1; other bind errors print `serve.py: <flag> N cannot listen: <error>`.
  A server already bound is closed before returning. New `--open` flag. After the existing lines it
  prints `Open: <url>` last (`Press Ctrl-C to stop.` is no longer flushed on its own; the `Open:` print
  flushes both), then calls `webbrowser.open` once when `--open` is set. If that returns False it
  writes a one-line hint to stderr (only with `--open`).
- `Config.__init__` (line 51): new `open_url` (Studio URL with `?target=`), one source for the printed
  line and the `--open` call.
- `Handler.host_allowed` (line 131) and new `misdirected_page` (line 204): a 421 whose request
  `Accept` contains `text/html` gets a short script-free, resource-free HTML page naming the accepted
  hosts (from config, escaped; the request's Host is never echoed) and saying to pass `--host`. Other
  requests keep the JSON answer.
- `make_server` (line 262): when `sys.platform == "win32"`, uses a `ThreadingHTTPServer` subclass with
  `allow_reuse_address = False`. It is set on the class because the option only counts before bind.
- `README.md`: Quickstart (use the `Open:` line, `--open`, Windows Store stub and `py -3`), and Dev
  server options (`--open` row, the 421 page, busy-port message).
- `tests/test_preview_server.py`: `Server` takes an `env` argument (used to point `$BROWSER` at a
  recording script, so `--open` is tested through the real `webbrowser` module, not a mock);
  `load_serve()` helper; the six tests above plus the characterization test.

**GREEN**: `python -m unittest tests.test_preview_server` -> `Ran 32 tests ... OK`
(chromium only; `FKS_ENGINES=chromium`). `python scripts/verify.py --static-only` -> all PASS,
unit/browser tests skipped by design. The full suite, `frontend_gate.py` and Firefox were not run.

**Not verified**:

- Windows behaviour is code reading only. The test patches `sys.platform` on Linux and asserts
  `allow_reuse_address` and, as a stronger check, the bound socket's `SO_REUSEADDR` option. It does not
  prove that a second bind on a taken port fails on Windows, nor that `WSAEADDRINUSE` is what Windows
  raises.
- `--open` is tested with `$BROWSER` set to a script; a real desktop browser launch was not exercised.
- The audit also mentions a headed-browser `favicon.ico` 404. Not in this brief; left alone.
- Doc copies outside my ownership that mention the old output: `AGENTS.md` line 99 ("open the printed
  Studio URL"). The controller may want it to say the `Open:` line.

## Fix round 1

Review verdict "Approved with fixes". Three fixes, same owned files, not committed.

1. **Flaky `test_last_line_before_the_wait_is_the_url_to_open` (required).** The test read stdout right
   after `wait_ready`, but stdout goes to a file and is only flushed with the `Open:` line, which can be
   printed after the ports listen. It now calls `server.stop()` first (the process has exited, so all
   output is flushed), asserts the final line is `Stopped.`, then checks that the line before it is
   `Open: <Studio URL>`. Proof: 40 of 40 passes in a loop on an idle machine, and 40 of 40 with four
   busy-loop processes competing for the CPUs (those four were started and killed by PID).
2. **Untested escaping.** New `test_misdirected_page_escapes_what_it_prints` calls
   `load_serve().misdirected_page({'<img src=x onerror=1>:80'})` and asserts `&lt;img` is present and
   `<img` is absent. It passes on the real code. On a scratch copy of `serve.py` with `html.escape(name)`
   replaced by `name`, the same two checks give `&lt;img present: False` and `<img absent: False`, so the
   test fails under that mutation. The mutation is not in the tree.
3. **Misleading bind message.** RED: `test_unbindable_host_names_the_host_not_the_port_flag`
   (`--host 203.0.113.9`) failed with stderr
   `serve.py: --studio-port 58251 cannot listen: [Errno 99] Cannot assign requested address`.
   Fix in `main` (`scripts/serve.py`, bind-error handler): "address in use" keeps its message; any other
   `OSError` prints `serve.py: cannot listen on <host>:<port> (<flag>): <error>`. The test asserts the host
   and port appear and that `pick another with` does not.

GREEN: `python -m unittest tests.test_preview_server` -> `Ran 34 tests ... OK` (chromium only).
`python scripts/verify.py --static-only` passes (tests skipped by design). Full suite, frontend gate and
Firefox were not run.
