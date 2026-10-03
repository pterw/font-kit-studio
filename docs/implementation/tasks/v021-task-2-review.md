# v0.2.1 Task 2 review: First run, dev server

Reviewer: Leading. Brief and implementer report: `v021-task-2-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 2 and decisions 2 and 3.
Scope: the uncommitted changes to `scripts/serve.py`, `tests/test_preview_server.py` and
`README.md` (Quickstart and Dev server options) in the main tree at `5917f56`.

## Verdict

### Review (Leading, 2026-10-03)

**Verdict: Approved with fixes.** The behaviour matches the brief and no security
problem was found. One new test is flaky (reproduced), one claim is untested, and one
message is misleading in a corner case. Fixes 1 and 2 should land before commit; 3 is
small and optional; 4 is for the controller.

Scope read: `git diff HEAD` of `scripts/serve.py`, `tests/test_preview_server.py`,
`README.md` at `5917f56`. Tree state unchanged by this review (`git status` identical
before and after). All mutation work was done in a scratch copy of the repo under the
session scratchpad, never in the main tree or any worktree.

#### Gates run

- `python scripts/verify.py --static-only`: all PASS (89 unique IDs, inline JS syntax,
  3 provenance hashes). Unit and browser tests skipped by design.
- `python -m unittest tests.test_preview_server` (`FKS_ENGINES=chromium`): `Ran 32 tests ... OK`.
- Not run: full suite, `frontend_gate.py`, Firefox, `node --check` (no bridge change).

#### (1) Behaviour against the brief

- Busy port. I held a loopback socket on an OS-assigned port and started `serve.py` on it:
  - `--studio-port 33153` busy: stderr `serve.py: --studio-port 33153 is in use; pick another with --studio-port <port>`, exit 1, empty stdout.
  - `--target-port 33153` busy: stderr `serve.py: --target-port 33153 is in use; pick another with --target-port <port>`, exit 1, empty stdout.
  - If the target bind fails, the already-bound Studio server is closed (serve.py:305-306).
- `Open:` is last. Real run printed `Studio:`, `Target:`, `Sync:`, `Press Ctrl-C to stop.`, then
  `Open: http://localhost:38701/font_kit_studio_v0.1.1.html?target=http://localhost:47575/demo/`.
  Existing lines kept. SIGINT exit code 0, stderr empty.
- `--open`: `serve.py:318` calls `webbrowser.open(config.open_url)` once, only under `args.open`.
  The extra stderr hint only appears with `--open` and a failed launch. Nothing extra when off.
- Windows: `make_server` (serve.py:265-270) picks a subclass with `allow_reuse_address = False`
  when `sys.platform == "win32"`. Set on the class, which is correct because the option is
  read before bind. Linux/darwin path unchanged. Windows is code reading only (as reported).
- 421 HTML: only when `Accept` contains `text/html` (case-insensitive). I sent real requests
  (raw `http.client`, own `Host`/`Accept`):
  - `Host: <script>alert(1)</script>.test`, `Accept: text/html` -> 421, `text/html; charset=utf-8`,
    body is the static page listing `127.0.0.1:P`, `[::1]:P`, `localhost:P` and `--host &lt;address&gt;`.
    The hostile Host appears nowhere in the body.
  - `Accept: */*`, `application/json`, `application/xhtml+xml`, or no Accept -> 421 JSON
    `{"ok": false, "error": "Host header not allowed"}`.
  - Empty `Host` with `Accept: text/html` -> same static page.
  - PUT `/__fontkit/overrides.css` with a bad Host and `Accept: text/html` -> 421 HTML, no write.
  - Good Host -> normal 302 redirect, so the check did not break the allowed path.
  - Body has no `<script>`, `<link>`, `<img>`, `src=`, `@import`; Cache-Control no-store is inherited via `end_headers`.
- README: the Quickstart sentence ("the last line the command prints", `Target:` is the demo
  port, `--open`), the `--open` table row, the 421 sentence and the busy-port sentence all
  match the output I observed. Edits stay inside Quickstart and Dev server options. The
  busy-port example `--studio-port 8000 is in use; pick another with --studio-port <port>`
  is exactly what the code prints.

#### (2) Security

- `misdirected_page(accepted)` (serve.py:204) builds the body from `Config.hosts()` only
  (`localhost`, `127.0.0.1`, `[::1]`, and the operator's `--host`), each through
  `html.escape`. It never reads a request header. The `Host` the request carried is only
  compared, never printed. No attacker-controlled value reaches the body.
- `Accept` parsing is a substring test. It can be abused only to choose between two static
  bodies. `text/html;q=0` still gets HTML (harmless; confirmed). I found no way to get a header
  value into the page: `Accept: text/html"><script>x</script>` returned the identical static page.
- `--open` opens `config.open_url`, built in `Config.__init__` from `--host` (operator
  input) and the two port numbers. Nothing from a request, the page, the target or Studio's
  `?target=` reaches it. The URL is the server's own Studio URL; with `--host 0.0.0.0` or
  `127.0.0.1` it is `localhost`. No finding.
- Residual (not a defect): `--host` is operator-supplied, and the 421 page prints it
  (escaped). A DNS-rebinding page therefore learns the operator's chosen `--host` string. An
  attacker who rebinds to that address already knows it. No action.

#### (3) Test quality

Mutations run against a scratch copy (`serve.py` restored after each; `diff` confirmed):

| Mutation | Test that failed |
|---|---|
| echo request Host into the 421 page | `test_misdirected_browser_request_gets_a_readable_page` |
| 421 page for every request (drop the Accept check) | same test (the `application/json` and `*/*` subtests) |
| inject `<script>` into the page | same test (regex) |
| `--open` opens twice | `test_open_flag_opens_the_studio_url_once` |
| browser opened without `--open` | `test_browser_is_not_opened_without_the_flag` |
| `Press Ctrl-C` printed after `Open:` | `test_last_line_before_the_wait_is_the_url_to_open` |
| remove the `win32` branch | `test_windows_never_shares_a_port` (win32 subtest) |
| busy message omits the port | `test_busy_port_names_the_port_and_the_flag` (both subtests) |
| serve a 404 for the missing overrides file | `test_demo_loads_without_any_overrides_request_failing` (`[(.../fontkit-overrides.css, 404)] != []`) |
| **remove `html.escape` from `misdirected_page`** | **nothing failed (32 tests OK)** |

The Windows test is also good evidence for the right reason: it reads `SO_REUSEADDR` off the
bound socket, so it proves the option was set before bind. `$BROWSER` recording script: it
goes through the real `webbrowser` module, which runs a `GenericBrowser` command
synchronously (`Popen` then `wait`), so the log is written before `open()` returns and
before the process exits. That is robust on Linux CI. Residual risk: `webbrowser` splits
`$BROWSER` on `os.pathsep`, so an interpreter path containing `:` on POSIX would break it;
unlikely in CI. Windows behaviour of that test is unverified.

Findings:

1. **Flaky test (reproduced).** `test_last_line_before_the_wait_is_the_url_to_open`
   (tests/test_preview_server.py, the `Server()` then `server.read_out().splitlines()` lines).
   `main` starts the serve threads (serve.py:312-313) before it prints, and stdout to a file is
   block-buffered until the `Open:` line flushes (serve.py:317). `Server.wait_ready` returns
   as soon as an HTTP request is answered, so `read_out()` can run before any line is
   written. Under 4 busy CPU loops I got `IndexError: list index out of range` at
   `lines[-1]` on run 24 of a loop, and 1 failure in 40 on an earlier loop. The sibling
   `--open` tests are not affected (they read after `stop()`). Fix: read the output after
   `server.stop()` (stdout flushes on exit via `print("Stopped.", flush=True)`) and assert
   on the last line before `Stopped.`, or wait for the `Open:` line. CI shares 4 CPUs, so
   this will flake. Required before commit.
2. **Untested claim: escaping.** Removing `html.escape` passes all tests, because the default
   `--host` yields only safe names. Add a unit test that calls `load_serve().misdirected_page({'<img src=x onerror=1>:80'})` and
   asserts the markup is escaped (`&lt;img` present, `<img` absent). Cheap, no server needed.
   Should land with fix 1; it is the one security property the implementer claims that no
   test guards.
3. **Misleading message in a corner case (optional).** Any bind error other than
   EADDRINUSE is now attributed to the port flag. Observed:
   `--host no.such.host.invalid` prints `serve.py: --studio-port 8000 cannot listen: [Errno -2] Name or service not known`, and
   `--host 203.0.113.9` prints `--studio-port 8000 cannot listen: [Errno 99] Cannot assign requested address`. The cause there is `--host`,
   and the old text ("cannot listen: ...") was not wrong. Suggest printing
   `serve.py: cannot listen on {host}:{port} ({flag}): {error}` for non-EADDRINUSE errors, with one
   test using an unassignable `--host` (for example `203.0.113.9`). Optional; the brief only
   specified the busy case.
4. **Stale doc copy, outside owned files (controller).** `AGENTS.md:99` says "then open the
   printed Studio URL". It should say the `Open:` line (fix in the same commit per the
   anti-duplication rule). A grep for `Studio URL`, `cannot listen` and `printed Studio` found
   no other stale copy in `README.md`, `CONTRIBUTING.md`, `docs/` (outside the ledger) or code.

#### (4) Real behaviour

Done above with real processes: busy-port stderr for both flags, the full startup output,
and the 421 body for HTML, JSON, empty-Host and PUT requests. Every server was started on
OS-assigned free ports, stopped with SIGINT by PID in `finally` (exit 0), and no leftover
process remained.

#### (5) Items the implementer listed as unverified

- Windows `WSAEADDRINUSE` and second-bind refusal: still not verifiable here (Linux only).
  Unchanged.
- Real desktop browser launch for `--open`: not verifiable here (no display). The
  `$BROWSER` path proves the stdlib is called with the right URL exactly once.
- The characterization test for item 6 (no 404 for the overrides file) is genuine: I
  broke the empty-CSS branch in the scratch copy and it failed with the 404. It cannot be
  vacuous.
- The headed-browser `favicon.ico` 404 is out of this brief (Task 3 adds the favicon).

Files: `scripts/serve.py`, `tests/test_preview_server.py`, `README.md` (all reviewed, none edited).

## Re-review

Reviewer: Leading, 2026-10-03. Scope: the three fixes from "Fix round 1" in `v021-task-2-brief.md`
(main tree, HEAD `5917f56`, uncommitted). Read-only; mutations in a scratch copy only.

**Verdict: Approved.**

Gate: `python -m unittest tests.test_preview_server` (`FKS_ENGINES=chromium`) -> `Ran 34 tests ... OK`.
`python scripts/verify.py --static-only` -> all PASS. Full suite, frontend gate and Firefox not run.

1. **Flaky `Open:` test: fixed.** `test_last_line_before_the_wait_is_the_url_to_open` now calls
   `server.stop()` first and asserts exit code 0 (so a SIGKILL fallback, -9, would fail it), then reads
   stdout. The read cannot precede the flush: `main` installs the signal handlers before it starts the
   threads (serve.py:309-313), and `wait_ready` only returns once the threads answer, so SIGTERM always
   reaches the handler. The handler sets `stop`; `main` finishes its prints (the `Open:` line flushes),
   shuts down, and prints `Stopped.` with `flush=True`. The test reads only after the process has
   exited, so all output is on disk. It asserts the last line is `Stopped.` and the line before it is
   `Open: <Studio URL>`. Evidence: 20 of 20 passes idle, and 40 of 40 passes with four busy-loop
   processes (started and killed by PID); before the fix I reproduced a failure under the same load.
   Mutation (`Press Ctrl-C` printed after `Open:`) still fails this test.
2. **Escaping test: present and effective.** `test_misdirected_page_escapes_what_it_prints` calls
   `misdirected_page({'<img src=x onerror=1>:80'})` and asserts `&lt;img` present and `<img` absent.
   With `html.escape(name)` replaced by `name` in the scratch copy it fails:
   `'&lt;img' not found in '...<code><img src=x onerror=1>:80</code>...'`. This closes the one mutation
   that survived the first review.
3. **Bind message: fixed.** Non-EADDRINUSE errors now print
   `serve.py: cannot listen on <host>:<port> (<flag>): <error>`, and "in use" keeps its message
   (serve.py:303-306). `test_unbindable_host_names_the_host_not_the_port_flag` (`--host 203.0.113.9`)
   asserts host, port and flag appear, `pick another with` does not, exit 1, no traceback. With the old
   message restored in the scratch copy it fails
   (`... not found in 'serve.py: --studio-port 56689 cannot listen: [Errno 99] Cannot assign requested address'`).
   Residual: the test relies on `203.0.113.9` (TEST-NET-3) not being a local address, which holds on
   normal CI hosts; a host with a non-local-bind sysctl would break it. Acceptable.
4. **Nothing else changed.** A `diff` of the current `scripts/serve.py` against the version I reviewed
   differs only in the bind-error handler (lines 303-306); the busy-port, `Open:`, `--open`, 421 and
   win32 code is unchanged. The test diff adds only the two new tests and the reordered read in the
   `Open:` test. `AGENTS.md` now shows as modified in the tree (fix 4 of the first review, controller's).

No processes of mine remain; the CPU loops were killed by PID. Files reviewed: `scripts/serve.py`,
`tests/test_preview_server.py` (none edited).
