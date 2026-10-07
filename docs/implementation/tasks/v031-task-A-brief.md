# 0.3.1 Task A: localhost cookies and loopback reservation

Binding work order: [Task A and host contract](../../plans/2026-10-07-v0.3.1-localhost-cookies.md).
Rules: `AGENTS.md`, `docs/agents/global-rules.md` and
`.superpowers/sdd/v0-3-1/constraints.md` in the controller checkout.

## Ownership and outputs

One implementer, in detached `C:/fks/v031-a` at the Task B landing commit.
Own only these files in that worktree:

- `packages/fontkitstudio/src/studio-server.js`
- `packages/fontkitstudio/src/proxy.js`
- `packages/fontkitstudio/src/run-proxy.js`
- `packages/fontkitstudio/src/run-vite.js`
- `packages/fontkitstudio/src/vite-plugin.js`
- Matching `studio-server`, `proxy`, `run-proxy`, `run-vite` and `vite-plugin`
  test files in `packages/fontkitstudio/test/`
- `packages/fontkitstudio/test/cli.test.js` and `test/helpers/fake-project.js`
  (plugin lifecycle fakes and localhost URL expectations; plan Addendum 3)
- New `tests/test_localhost_cookies.py`
- `tests/firefox_canary.py`
- `tests/test_one_command_proxy.py` (localhost URL expectation only)

No other source files or shared-file edits. Tests may create a temporary cookie
page/config in a scratch copy of an existing fixture (not tracked fixture edits).
Install fixtures in the worktree with npm ci. Return:

- Patch: controller `.superpowers/sdd/v0-3-1/A.patch`, includes new test files.
- Report: controller `.superpowers/sdd/v0-3-1/A-report.md`.
- Logs: controller `.superpowers/sdd/v0-3-1/A-*.log`.

You are not alone in the repository. Preserve others' edits; do not commit,
push, spawn, stash, merge, tag or write npm credentials. A denied tool call is
reported, never retried through a different tool. Do not write CLAUDE.md,
MEMORY-local.md, .claude/ or ~/.claude/. Stop only processes you start, by PID
or handle; servers and scratch files need finally/addCleanup cleanup.

## Binding behavior

1. A localhost app gives Studio and the proxy localhost advertised origins.
   Keep today's behavior for IP targets, including `[::1]`. Prove final host
   selection from Vite's resolved local URL in both command and standalone plugin.
   Preserve command/permanent-plugin coexistence, configuration restart and close.
2. Before publishing a localhost URL reserve IPv4 127.0.0.1 and IPv6 ::1 on the
   same port. Never bind wildcard addresses. With port zero and occupied IPv6,
   close provisional IPv4 and retry a new port. Only EADDRNOTAVAIL/EAFNOSUPPORT
   allows IPv4-only startup. Other errors clean up and fail. Fixed Studio port
   conflicts keep the existing fallback warning; the fallback also reserves both.
3. Host/Origin/token rejection and origin-pinned bridge tags remain intact for
   accepted aliases. Startup/close must free both listeners and proxy upgrades.
   Preserve target path/query/fragment, redirects, HTTP and WebSocket forwarding.
4. Existing public startup/runner signatures and returned origin/url/port/close
   remain callable. Host may be threaded through existing startup options.
   Any new tracked helper file requires a plan addendum before editing it.

## Tests first

Use the tdd and systematic-debugging skills. Public seams already agreed in
the plan: server startup and requests, runner URLs, plugin tags, rendered app.
Characterize working IP cases; do not manufacture RED for them.

- First add the real-command regression, then run unchanged code in Chromium
  and Firefox, Vite and proxy modes. Lax/Strict rendered delivery fails today;
  omitted-SameSite already works in Firefox Vite mode and is characterized as
  passing. Firefox proxy mode loses all three cookies before the fix.
- Use support.py's shared browser runtime; fresh contexts and cleanup. Block
  https://**. Seed cookies by visiting the app in the same browser context,
  start the real command with --no-open and assert Studio connects and the frame
  visibly renders all three values from an HTTP Cookie-header echo. Never
  replace HTTP-delivery evidence with document.cookie or page source.
- The temporary Vite page/config can expose set-cookie and echo endpoints;
  the page renders a same-origin fetch of the echo. Proxy may use a Python
  upstream. Keep both cases insensitive to the app URL's random port.
- Node tests cover every target kind, both dual binds, injected IPv6-unavailable
  errors, occupied IPv6, partial-start cleanup, fixed-port fallback and hostile
  origin/host. An already listening ::1 server must never receive the request
  made to the returned Studio URL. Probe the final injected allowed origin.
- Add both cookie cases to firefox_canary. Chromium blocks; Firefox evidence
  is advisory. Run firefox_canary (not a separate Firefox full suite).
- Implement one behavior slice at a time. Run one foreground mutation per new
  guard, restore source, report exact failures and GREEN outcomes. No loops of
  background mutation runs. Changes to existing expectations need a rationale.

## Focused gates

Install required Vite fixture(s), bundle the package, then run:

```powershell
npm --prefix packages/fontkitstudio test
$env:PYTHONPATH='tests'
$env:FKS_REQUIRE_FIXTURES='1'
$env:FKS_ENGINES='chromium'
python -m unittest test_localhost_cookies test_one_command_vite test_one_command_proxy test_node_studio_server test_support -v
$env:FKS_ENGINES='firefox'
python -m unittest firefox_canary -v
```

Run only focused tests and relevant fast checks in the code phase; do not run
the full halves. Redirect long logs, propagate the native test exit code
explicitly on PowerShell, and quote counts/verdicts in the report. No claim of
passing for skipped fixture cases. At three failures at one boundary, or an
unowned file dependency, stop and report evidence rather than silently widening.

## Report and handoff

Changes, RED/GREEN matrix, mutations, commands/counts/engines, altered existing
expectations, anti-pattern self-review and limits. Draft shared-file text only:

- CHANGELOG: localhost apps keep sign-in cookies; only localhost users with
  --studio-port face one-time loss of prior Studio settings when its host changes.
- CI: install required fixture and bundle for Firefox canary; include cookie
  module in installed-fixture job. Controller owns workflow edits.
- README: remaining alias mismatch, proxy-origin storage and random-port limits.
- Ledger and a product commit subject/why-body with no signatures.

Done: Chromium cookie cases and focused guards pass, Firefox results reported,
patch/report ready for independent review. No release/version label changes here.
