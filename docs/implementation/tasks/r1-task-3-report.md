# Task 3 (R1.3) code report

Mode: code, worktree C:/fks/t3, BASE ec0d410. Patch: `.superpowers/sdd/r1-pr-a/task-3-code.patch`
(applies in reverse cleanly). Files (all new, 424 lines): `packages/fontkitstudio/src/studio-server.js`,
`test/studio-server.test.js`, `test/helpers/serve-studio.js`, `tests/test_node_studio_server.py`.

Steps 1-5 done. Step 6 (gates, commit) deferred to landing. No package.json change.

## Evidence
- RED: `node --test test/studio-server.test.js` -> ERR_MODULE_NOT_FOUND (src/studio-server.js), fail 1.
- GREEN: `npm --prefix packages/fontkitstudio test` -> tests 16, pass 16, "ℹ fail 0" (Node 24).
- Python: `PYTHONPATH=tests python -m unittest test_node_studio_server -v` -> Ran 2 tests, OK (Chromium).
- Mutations (one at a time, restored, 16/16 after):
  - token check removed -> "a missing or wrong token is 403 and shows no Studio"
  - Host check removed -> "a foreign, wrong-port or empty Host is 421; LOCALHOST is fine"
  - Origin check removed -> "a foreign or null Origin is 403; the same-origin Origin is fine"
  - method check removed -> "POST, PUT and OPTIONS are 405 with Allow"
  - Browser: dropping `Referrer-Policy` -> test_app_sees_no_token_and_no_referer fails (iframe
    request carries `Referer: http://127.0.0.1:<port>/`); token check removed ->
    test_url_without_the_token_shows_no_studio fails.
- Proof Studio loads the iframe for `?target=`: recorder got `GET /app/` with `Sec-Fetch-Dest: iframe`,
  `Host: localhost:<rec port>`.
- Not run (per dispatch): full Python halves, frontend gate, static. pre-commit not installed here.

## Notes / deviations
- Empty Host: node's http client replaces an empty `Host` header, so the Node test sends it over a raw
  socket (`Host: `; on a raw socket both `Host:` and `Host: ` reach the handler and get 421).
- Error responses set `Connection: close`; HEAD sends headers with the GET Content-Length and no body.
- Files are written LF; git warns they become CRLF on checkout (core.autocrlf=true, like the others).
- The Python test spells the Host check on `localhost` for the target, loopback recorder bound to 127.0.0.1.

## Handoff
- Commit subject: `feat(dev): serve Studio on loopback behind a per-run token`
- Body draft: Spec section 1: another local page must not be able to drive Studio, so the server binds
  loopback only, checks Host and Origin, and requires a per-run random token. Referrer-Policy: no-referrer
  keeps the token out of requests Studio's iframe makes to the app or a font host.
- Gates to run at landing: static, bridge-syntax, node-package (expect "ℹ fail 0", 16+ tests total in
  the package), suite-a/suite-b (diff touches tests/), commit-messages. Frontend gate not required.
- Shared-file drafts: progress line "R1.3 Studio server and per-run token landed (Node 16 tests incl. 10
  server cases, 2 Chromium tests)"; no CHANGELOG entry needed (internal dev package).

## Self-review against the Anti-Pattern Registry (added on the controller's update)
Read AGENTS.md "Anti-Pattern Registry" and docs/agents/global-rules.md. Applicable items:
- Rule 5 / AP 2-4, 7 (trust boundary): the server is a boundary and has hostile tests for wrong,
  missing, repeated, wrong-case and wrong-length token; foreign, wrong-port and empty Host; foreign
  and null Origin; non-GET methods; traversal-like and sibling paths. Error bodies are fixed strings
  and never echo input. The only URL sink is `url(target)`, which puts `target` in a query value via
  URLSearchParams; the server itself never navigates anywhere.
- Rule 7 (no third-party contact): the server serves one local file, no outbound calls. In the browser
  test, after review I added `context.route('https://**/*', abort)` so Studio cannot reach a font host
  during the run (re-ran: 2 tests OK). The recorder and helper bind 127.0.0.1 only.
- Rule 8 (zero deps, flat code): node:* imports only, one request handler, no framework.
- AP 12 (siblings): the Host/Origin/method/token checks were each mutated; the 405/404/403 headers are
  asserted for every error class through one `assertHardened` helper.
- AP 13 (servers): the Node test closes the server in `after`; the Python test shuts the recorder and
  closes the helper's stdin, waits, and kills only that Popen handle on timeout, in nested `finally`.
  setUp failure after starting anything calls tearDown.
- AP 14: not run, and said so: full Python suite halves, frontend gate, static gate, pre-commit.
- AP 15: no process state in the drafted commit text.

## Fix section (review Minor findings 1-4)
1. `setUp` in tests/test_node_studio_server.py now registers `addCleanup` for the contexts, the
   recorder (shutdown, join, server_close) and the helper (`stop_helper`) as each is created; the token
   parse can no longer leak either process. `tearDown` removed.
2. New Node test "checks run in order: Host, Origin, method, path, then token": wrong Origin plus wrong
   token gives 403 "Origin not allowed."; POST plus wrong token 405; wrong path plus wrong token 404.
   Mutation (path check removed) fails it and "any other path is 404".
3. Dead `includes('?')` ternary in the 404 test removed.
4. Report corrected: an empty `Host:` or `Host: ` both reach the handler on a raw socket and get 421.
   The test comment only says the http client replaces an empty Host, which stays true; no change needed.
Left as instructed: parser-level 400 headers; the untested 400 "Bad request." branch.
Run after fixes: `npm --prefix packages/fontkitstudio test` -> "ℹ tests 17 / ℹ pass 17 / ℹ fail 0";
`PYTHONPATH=tests python -m unittest test_node_studio_server -v` -> "Ran 2 tests in 1.977s / OK".
