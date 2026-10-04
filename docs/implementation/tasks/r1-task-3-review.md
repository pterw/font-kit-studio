### Spec Compliance
- PASS: Interface matches the brief: STUDIO_PATH, newToken (32 bytes base64url), startStudioServer options and return shape, url(target) (studio-server.js:13-37, 99-115).
- PASS: Check order is Host, Origin, method, URL parse (400), path, token (studio-server.js:64-88). A rebinding request with the right token gets 421 (test line 225-231).
- PASS: Table answers and fixed strings match the brief; every answer carries the three headers via NO_STORE (studio-server.js:16-20, 54-60); errors add Connection: close; HEAD sends no body.
- PASS: Constant-time compare with a length check first, no throw on length mismatch (studio-server.js:26-30). Repeated `token` is rejected (given.length !== 1).
- PASS: Non-loopback host rejects with the brief's wording; a missing file rejects with the path and "npm --prefix packages/fontkitstudio run prepack" (studio-server.js:38-49; test 278-288).
- PASS: No CLI wiring, no package.json change, only the four owned files. Imports are node:* and relative only (studio-server.js:2-5, serve-studio.js:3, test imports).
- PASS: Helper is the brief's text verbatim.
- PASS: Browser test uses ENGINES, new_context, close_contexts; condition-based wait; checks Referer and token absence in every recorded request; tokenless URL gives 403, no "Font Kit Studio v", and the recorder stays empty. The report names the proving request (GET /app/, Sec-Fetch-Dest: iframe).
- PASS: The late addition `context.route('https://**/*', abort)` in both browser tests (test_node_studio_server.py:416, 441) is allowed under global rule 7 and does not weaken the test.
- CANNOT VERIFY FROM DIFF: step 6 gates and the commit (deferred to landing, as the report says).

### Checks run
- Risk 1 (token, Referrer-Policy) -> read studio-server.js; no logging; no response body or header contains the token; NO_STORE is applied by `send` on all handler responses -> PASS. Node's own parser-level 400s (malformed request lines) bypass the handler and carry no Referrer-Policy; they hold no document and no token, so not a leak (Minor 2).
- Risk 1 (Referrer-Policy matters) -> copied t3 to the scratchpad, removed the Referrer-Policy header, ran test_node_studio_server -> test_app_sees_no_token_and_no_referer FAILED with `Referer: http://127.0.0.1:<port>/` on the iframe GET /app/. The report's claim is true.
- Risk 2 (order) -> read code; Host-before-token covered by test case 4 with the right token. Order between the other checks is not pinned by a test (Minor 1).
- Risk 3 (no reflection) -> all send() bodies are string literals (studio-server.js:66-87); the test compares the exact body strings.
- Risk 4 -> test 278-288 plus code read -> PASS.
- Risk 5 (empty Host) -> copied package to the scratchpad, changed the Host check to `requestHost !== '' && ...`, ran the node test -> the Host test fails (fail 1). Probe on a raw socket: both `Host: ` and `Host:` reach the handler and get 421 "Misdirected Request". So the test exercises the handler, not Node's parser. The report's note that plain `Host:` gets a 400 from Node's parser is wrong (Minor 3); the test itself is sound.
- Risk 6 -> Node: `after` closes the server and removes the temp dir; the two rejection cases fail before listen, so no server leaks. Python: nested finally, kills only self.proc, shuts the recorder and joins the thread. Gap: Minor 4.
- Risk 7 -> see the Referrer-Policy mutation above; test asserts on every recorded request (path and every header value) and on the tokenless case -> PASS.
- Risk 8 -> grep of imports -> node:* and relative only.
- 400 branch -> probe: `new URL('//', 'http://studio.invalid')` throws, and a raw `GET //` gets 400. The catch is real and works, but no test covers it (Minor 5).

Anti-Pattern Registry and Test Quality Rules (applicable items):
- AP 1, 2, 3, 4, 5, 6, 7, 8, 9, 10: not applicable (no postMessage, DOM, iframe.src sink, bridge, or defaults in this diff). The only URL sink is `url(target)`, which uses URLSearchParams; the server never navigates -> PASS.
- AP 11/12 (siblings): no renamed claim in this diff; the Host/Origin/method/token checks are each mutation-tested and the headers are asserted for every error class via assertHardened (test:184-188) -> PASS.
- AP 13 (server yours to stop): test:161-164 (after), test_node_studio_server.py:385-401 (tearDown), server bound to loopback on a free port; only own Popen handle killed -> PASS, with Minor 4 about setUp.
- AP 14: the report states that the full suite halves, frontend gate, static gate and pre-commit were not run -> PASS.
- AP 15: the drafted commit body has no process state -> PASS.
- Global rule 5 (trust boundary, hostile cases): wrong, missing, repeated, wrong-case and wrong-length token; foreign, wrong-port and empty Host; foreign and null Origin; non-GET methods; sibling and traversal paths -> PASS.
- Global rule 7: the server makes no outbound calls; the browser tests abort https -> PASS.
- Global rule 8: zero dependencies, one flat handler -> PASS.
- Test Quality Rules: happy-path-only boundary (no, hostile cases present); vacuous tests (no, mutations 4/4 plus 2 browser mutations); new fixed sleep (the 0.05s poll in wait_for is a condition poll, allowed); manufactured RED (no; RED was module-missing) -> PASS.

### Strengths
- Mutation evidence is real: I reproduced the Referrer-Policy mutation and an empty-Host mutation, and both fail the intended tests.
- The browser test checks the absence of the token in every header value of every request the recorder saw, and asserts the tokenless case recorded nothing.
- Error bodies are constants and checked for exact equality.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. test/studio-server.test.js:269-276 -- the 404 cases always send the right token, and no case pins the order of Origin/method/path against the token (for example a wrong token on a wrong path should be 404, a bad Host plus a bad Origin should be 421). A reorder of checks 2-5 would pass the tests. The brief did not require it.
2. studio-server.js -- Node-level 400s (malformed request line or headers) are produced before the handler and lack Referrer-Policy and Cache-Control. They carry no token and no document, so this is not a leak. A `clientError` handler or a comment would make "every response" literally true.
3. Report note about plain `Host:` returning 400 is wrong (probe shows 421). Do not copy that sentence into the landing report.
4. tests/test_node_studio_server.py:380-383 -- the token parse after the try block can raise (KeyError) and would leave the helper process and the recorder running, because unittest skips tearDown when setUp raises. Moving this into the try block, or using addCleanup, closes it.
5. studio-server.js:76-81 -- the 400 "Bad request." branch has no test; if the catch were removed, `GET //` would throw inside the handler and take down the process. Add one raw-socket case.
6. test/studio-server.test.js:271 -- `path.includes('?')` is never true; the ternary is dead code.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The implementation follows the brief and its check order, the token and header handling are correct, and the mutation evidence is real (I re-ran two mutations and both fail the intended tests). The remaining items are minor test-coverage and cleanup gaps.
