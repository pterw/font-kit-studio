### Spec Compliance
- PASS: portless Host forms accepted on port 80 only, via exported pure allowedHosts(port) (studio-server.js:17-20), used at the Host check (studio-server.js:70).
- PASS: origin reported in browser form via exported studioOrigin(host, port) = new URL(...).origin (studio-server.js:23-25), used for server.origin and url() (studio-server.js:103).
- PASS: CLI range unchanged (diff touches only studio-server.js and two test files).
- PASS: both functions unit-tested (studio-server.test.js new describe block).
- PASS: no Co-authored-by or signature in the drafted commit text; no shared files touched.

### Checks run
- Probe 1, real bind on port 80 -> scratch script calling startStudioServer({ port: 80 }) from C:/fks/tC3 -> it BOUND. origin = http://127.0.0.1, url() = http://127.0.0.1/fontkit-studio.html?token=... (no :80). Host 127.0.0.1 -> 200; Host 127.0.0.1:80 -> 200; Host localhost -> 200; Host [::1] -> 200; Host evil.test -> 421; Host evil.test:80 -> 421; Host 127.0.0.1:81 -> 421. Server closed in finally; no node process left.
- Probe 2, Origin on port 80 -> same script -> Host 127.0.0.1 + Origin http://127.0.0.1 -> 200; Origin http://evil.test -> 403; Origin http://127.0.0.1:81 -> 403; Origin null -> 403. Origin http://127.0.0.1:80 -> 403, which is fine: browsers never send :80 in Origin.
- Probe 3, rebinding guard on other ports -> same script on port 0 (got 52812) -> Host 127.0.0.1, localhost, [::1] without port -> 421; only 127.0.0.1:52812 -> 200; evil.test and 127.0.0.1:81 -> 421. Guard intact.
- Probe 4, consumers of studio.origin -> scratch script with origins http://127.0.0.1, http://localhost, http://[::1] against fontkitStudio() (checkLocalOrigin at vite-plugin.js:26-35, tag attr at :154) and startProxy() (studio validation at proxy.js:80-95, tag at :111) -> all three accepted; data-allowed-origins carries the portless form unchanged. run-proxy.js and run-vite.js only call studio.url(...) and studio.close(), and run-proxy.js:17 uses studio.port, which is still the real port. Nothing parses the origin for a port.
- Probe 5 -> npm --prefix C:/fks/tC3/packages/fontkitstudio test -> tests 208, pass 206, fail 0, skipped 2.
- Docs sibling grep (port 80 / studio-port in live md and js) -> no claim about port 80 or the origin form that the change makes false.

### Strengths
- Portless hosts are added only when port === 80; the check is exact, so the DNS-rebinding guard is unchanged elsewhere (verified live).
- Origin check needed no change: it compares to http://<request Host>, which already matches a browser's portless origin.
- Real port-80 bind verified end to end here, closing the gap the report said could not be tested.

### Issues
#### Critical
(none)
#### Important
(none)
#### Minor
- studio-server.test.js (third new test, "a server on another port reports the suffixed origin and refuses the portless Host"): the title claims a refusal that the body never asserts (it only checks origin and url prefix). Either add a raw request with Host 127.0.0.1 expecting 421, or drop "and refuses the portless Host" from the title. The refusal is real (probe 3), so this is naming only.
- The server's own use of allowedHosts on port 80 is not covered by a test (port 80 cannot be bound in CI); the unit test of allowedHosts(80) plus the non-80 refusal carry it. Acceptable and reported honestly.
- The vite-plugin test "accepts the origin of a Studio on port 80" passes against unchanged code (pins existing behaviour); the report says so. Fine.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** Port 80 binds here and behaves exactly as ruled: portless Host accepted on 80 only, origin and url() in browser form, Origin check intact, and every origin consumer accepts the portless form. Full package suite passes; only a naming nit in one test.
