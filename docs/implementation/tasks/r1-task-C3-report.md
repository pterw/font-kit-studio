# C3 code report (mode: code, BASE 7fae4fa, worktree C:/fks/tC3)

Patch: `.superpowers/sdd/r1-pr-b/task-C3-code.patch` (3 files, LF, `git apply --check -R` OK).
Files: `packages/fontkitstudio/src/studio-server.js`, `test/studio-server.test.js`, `test/vite-plugin.test.js`.

## Change
- `allowedHosts(port)` (exported, pure): the three `host:port` forms; on port 80 also `127.0.0.1`, `localhost`, `[::1]`. The server uses it (compared lower-case, as before).
- `studioOrigin(host, port)` (exported, pure): `new URL('http://<host>:<port>').origin`, so `:80` is dropped and `::1` is bracketed. The server's `origin` and `url()` use it.
- The Origin check (`http://<request Host>`) already matches a browser's portless origin on port 80, so it needed no change.
- The CLI range is unchanged (80 still accepted).

## RED / GREEN
- RED (tests first): `node --test test/studio-server.test.js` -> `SyntaxError: The requested module '../src/studio-server.js' does not provide an export named 'allowedHosts'`.
- GREEN: studio-server and vite-plugin tests pass (66 pass, 0 fail).
- Mutations, foreground, restored by editing: `allowedHosts` returning portless forms for every port -> FAIL "allowedHosts: ..."; `studioOrigin` returning the raw string (keeps :80) -> FAIL "studioOrigin: ...".
- Not mutation-tested: that the server calls `allowedHosts`/`studioOrigin` on port 80 itself (port 80 cannot be bound without root). The non-80 server test checks `studio.origin === studioOrigin(...)` and the existing Host tests exercise the call site.
- Plugin test "accepts the origin of a Studio on port 80, which has no port" passes against the unchanged plugin (`checkLocalOrigin` already accepts `http://127.0.0.1`); it pins that behaviour and is not a RED test.

## Gates
`npm --prefix packages/fontkitstudio test`: tests 208, pass 206, fail 0, skipped 2. `python -m ruff check .`: all checks passed. No process left running.

## Handoff
Commit subject: `fix(dev): serve Studio on port 80 with the origin browsers use`
Why-body: A browser omits port 80 from the Host header and from the page origin, so `--studio-port 80` printed a URL that got 421 from Studio, and the bridge tag's data-allowed-origins (`http://127.0.0.1:80`) could never match. Studio now accepts the portless Host forms on port 80 and reports the origin as browsers write it. Both rules are small pure functions with unit tests, since port 80 cannot be bound in CI.
progress.md line: `R1.4d fix (Codex P2 round 2): Studio on port 80 accepts portless Host forms and reports the browser-form origin.`


## Landing (controller, 2026-10-04)

Review (`r1-task-C3-review.md`): Approved; the reviewer bound a real Studio server on port 80 on Windows: `origin` is `http://127.0.0.1`, `url()` has no `:80`, Host `127.0.0.1` and `127.0.0.1:80` answer 200, `evil.test` 421, and the plugin and the proxy accept the portless origin. Fixed at landing: the test named "refuses the portless Host" asserted no refusal; it now sends `Host: 127.0.0.1` to a server off port 80 and expects 421, and allowing portless hosts on every port fails it. Node tests on Windows: 208 run, 206 pass, 2 skipped.
