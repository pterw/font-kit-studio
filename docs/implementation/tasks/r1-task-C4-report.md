# C4 code report (mode: code, BASE 7fae4fa, worktree C:/fks/tC4)

Changed: `packages/fontkitstudio/src/proxy.js` (`rewriteLocation` only) and `test/proxy.test.js`.
Patch: `task-C4-code.patch`.

Change: a Location starting with `//` (or `\`, which browsers treat the same) is resolved as `http:` + value,
then handled like an absolute one. Relative locations (`/login`, `login`) still fail to parse and stay untouched.

Choice: "on the target" now means scheme `http:`, a loopback hostname (`localhost`, `127.0.0.1`, `[::1]`) and the
target's port, not literal origin equality. Why: the Origin/Referer rewrite already treats loopback names as one
server, the target is always loopback, and an app may redirect to `//localhost:3000` while being proxied at
`127.0.0.1:3000` (the tests do exactly that). This also applies to absolute `http://localhost:<port>` locations.
A different port or host (`//example.com/x`, `//localhost:<port+1>/x`) is left alone.

Tests added (case "rewrites a location..."): `//localhost:<up>/login?next=/a#x` -> `<proxy>/login?next=/a#x`;
`//127.0.0.1:<up>/x` -> `<proxy>/x`; `//example.com/x` unchanged; `//localhost:<up+1>/x` unchanged; `/login` unchanged.

RED: with `networkPath = false` (old behaviour) the test fails: actual `//localhost:55802/login?next=/a#x`,
expected `http://127.0.0.1:55803/login?next=/a#x`. Mutation: port check replaced by `false` -> fails on the
`//localhost:<up+1>` case. GREEN: proxy.test.js 44 pass / 0 fail.
Gate: `npm --prefix packages/fontkitstudio test` -> see reply (fail 0); `node --check` ok. No servers left running.

## Handoff
Subject: `fix(dev): keep protocol-relative redirects inside the proxy`
Body: A dev server may redirect with a network-path Location such as
//localhost:3000/login. The proxy parsed it without a base, rejected it
and forwarded it unchanged, so the browser left the proxy and the
redirected page never got the bridge tag. Resolve such locations as
http: URLs and rewrite those on the target's loopback names and port to
the proxy origin; other hosts and relative locations stay untouched.
progress.md: "Codex P2 (PR #10): proxy rewrites protocol-relative Location headers on the target to the proxy origin; 5 location cases tested."


## Landing (controller, 2026-10-04)

Review (`r1-task-C4-review.md`): Approved; the reviewer sent 35 Location values through a real proxy: network-path, backslash and `http:\` forms of the target are rewritten with query and hash kept; other hosts, other ports, `https:`, relative paths and host tricks (`localhost:P.evil.test`, `localhost:P@evil.test`) stay untouched; malformed values never throw. The loopback extension (any loopback name on the target's own port counts as the target) mirrors the Origin and Referer mapping. Tests added at landing for the review's coverage gaps: a backslash network-path redirect is rewritten, an `https:` location on the target's host and port is left alone, and an absolute `http://localhost:<port>` location on a `127.0.0.1` target is rewritten. Kept as recorded: a tab inside the value and a trailing-dot host are not mapped. Node tests on Windows: 208 run, 206 pass, 2 skipped.
