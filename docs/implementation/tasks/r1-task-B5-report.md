# B5 code report (mode: code, BASE 38e815a, worktree C:/fks/tB5)

Patch: `.superpowers/sdd/r1-pr-b/task-B5-code.patch` (`git apply --check -R` passes). Nothing committed.

## Steps
1. Failing Node tests: done. RED before the source existed: `node --test proxy/open-browser/run-proxy`
   gave `ERR_MODULE_NOT_FOUND` for `src/open-browser.js` and `src/run-proxy.js` and 4 failing upgrade cases in
   proxy.test.js (`ℹ fail 5`).
2. Implement: done (`src/open-browser.js`, `src/run-proxy.js`, `server.on('upgrade')` in `src/proxy.js`; B4's HTTP code untouched).
3. Fixture and CSP server: done (Bootstrap 5.3.8 from `npm pack`, sourceMappingURL lines removed, LF).
4. Browser test: done, 2 tests (Chromium): the proxied page keeps the CSP header exactly and has one tag;
   Studio selects `bs.hero.title`, types 56, frame font-size becomes 56px, no CSP violation in either document,
   no page error, `https://**` aborted.
5. GREEN + mutations: done (below).
6. Gates: done. 7. Report: this file.

## Evidence
- `npm --prefix packages/fontkitstudio test`: `ℹ tests 95 / pass 93 / fail 0 / skipped 2` (the 2 skips are not from B5 files; not investigated).
- `PYTHONPATH=tests python -m unittest test_one_command_proxy test_support -v`: `Ran 36 tests ... OK`.
- `python -m ruff check .`: `All checks passed!`.
- pre-commit not run (not requested for this task; the controller's gates apply).
- Mutations, one at a time, each restored by editing (`node --test test/proxy.test.js test/run-proxy.test.js`):
  - Host check on upgrade removed: `refuses a foreign Host with 421 and the dev server sees nothing` fails.
  - Origin/Referer rewrite on upgrade undone: `passes the handshake and the bytes through, as the dev server` fails.
  - `studio.close()` removed from `runProxy`'s close: `SIGINT closes both servers and the signal handlers go away` fails
    (run with `--test-force-exit`, since the leaked listener otherwise keeps the process alive).
  - `studio.close()` removed from the proxy-rejected path: `a rejected proxy closes the Studio server it started` fails.
  - `if (open)` -> `if (true)`: `open: true opens the Studio URL once ... open: false never` fails (the SIGINT test also fails as a cascade).
  - extra: proxy `close()` no longer destroys upgraded sockets: `close() destroys an open upgraded socket and resolves` fails (10 s test timeout).
- Browser test not mutated separately; it fails at setUp if `run-proxy.js` is absent.

## Deviations and notes
- Test timeouts: socket waits in the upgrade tests fail after 3 s and the close test has a 10 s timeout, so a broken
  guard fails instead of hanging.
- `tests/test_one_command_proxy.py` opens the helper with `encoding='utf-8'` (Windows decodes `·` wrongly otherwise).
- The inspector check uses `#liveTargetName` `data-target-id` (as `test_live_integration` does), not its text.
- Test `get()` in run-proxy.test.js uses `agent: false`: the global keep-alive agent turned a closed server into ECONNRESET.
- During mutation runs an earlier killed shell loop kept mutating files; I found and repaired `run-proxy.js` and one
  assertion line in run-proxy.test.js, then re-ran every mutation from a verified-clean tree.

## Self-review (anti-patterns)
- AP 1-4, 7 (trust boundary): upgrade has the Host (421) and origin-form (400) checks with hostile tests; no URL sink
  takes input that changes scheme or host (target host is fixed from the validated target).
- AP 13: every server, socket and child is closed in cleanups/`finally`; the Python helper is stopped by handle.
- AP 14: nothing skipped by design; the browser test skips only when `node` is missing (as the sibling module does).
- AP 15: no process state in files. Rule 7: https blocked in the browser test; no telemetry.
- Vendored Bootstrap and the fixture are churn (D050).

## Handoff
Patch files (lines added): src/open-browser.js 20, src/run-proxy.js 61, src/proxy.js +43, test/helpers/run-proxy.js 11,
test/helpers/ws-upstream.js 53, test/open-browser.test.js 56, test/run-proxy.test.js 213, test/proxy.test.js +139,
tests/helpers_csp_server.py 28, tests/test_one_command_proxy.py 120, fixtures/bootstrap5-static/index.html 20, app.css 7.
Churn (vendored): vendor/bootstrap.min.css 5 lines (232,066 bytes), vendor/bootstrap.bundle.min.js 6 lines (80,448 bytes),
vendor/LICENSE 21 lines. Material about 750 lines.

progress.md event draft: `B5 (R1.5b): runProxy starts Studio then the proxy, prints two lines, opens the browser unless
told not to, stops both on Ctrl-C/SIGTERM; the proxy passes WebSocket upgrades through with the same Host and origin
rules; proved in Chromium on a Bootstrap 5.3.8 page served with script-src 'self'; style-src 'self'.`

Commit subject: `feat(dev): run the proxy with Studio and pass hot reload through`

Body draft: One command for apps that do not run on Vite: `runProxy` starts the token-guarded Studio server and the
proxy, prints the URL to open and stops both on Ctrl-C. The proxy now passes WebSocket upgrades through with the same
Host and origin checks, so the app's own hot reload keeps working. Proved in a real browser on a Bootstrap 5 page
whose CSP allows only its own scripts and styles. Bootstrap 5.3.8 is vendored as churn.


## Landing (controller, 2026-10-04)

Review minor 1 fixed at landing with two upgrade tests: bytes written with the handshake (the upgrade `head`) reach the upstream and come back, and an upstream that closes ends the browser's socket. Removing the `head` write fails the first. Removing the upstream `close` handler does not fail the second, because `upstream.pipe(socket)` ends the browser's socket on its own; the handler also destroys both sockets and drops them from the set `close()` walks, and that second path is not separately tested. The other minors stay as recorded (upgrade origin forms covered by the shared header code, an unhandled rejection if the proxy's close ever rejected, a test title, a socket upgraded after `close()` began). Before review, a background mutation loop the code phase had left running was found hung in the worktree and stopped by PID; the worktree matched the patch and the sources matched the loop's pre-mutation backups. Node tests on Windows: 97 run, 95 pass, 2 skipped (B1's machine-dependent cases).
