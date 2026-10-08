# Task A independent review

Date: 2026-10-07. Verdict: **Approved**.
Reviewed base: `6bd4a044294fd92f76ed14fada25048b6fcc0773` on
`fix/localhost-cookies`, plus the integrated staged Task A diff. No cookie-fix
commit exists at review time. Runtime source remained frozen during review.

## Scope and requirements

Read AGENTS.md and global-rules.md in full, the active plan's binding host
contract, Task A, Addenda 1-3, the complete task brief and implementation report,
the workspace constraints and the requesting-code-review skill. Read the five
changed startup modules and all seven changed Node test/helper files in full,
the three changed Python files, the workflow and the staged shared-record diff.
README's existing limitations are deferred explicitly to Task C.

Spec review precedes quality review. The implementation preserves the public
startup functions, asynchronous close, returned URL/origin/port behavior and the
IP-target matrix. Only a localhost app selects localhost for Studio/proxy.
Vite's final resolved local URL selects the host in the command and standalone
plugin. Real Vite 7 and 8 probes confirm the delayed startup works with Vite's
actual lifecycle, including standalone restart and startup failure.

Both localhost listeners are reserved before the returned URL is published.
Only EADDRNOTAVAIL/EAFNOSUPPORT allows IPv4-only startup. Occupied IPv6 retries
release provisional IPv4; fixed-port fallback keeps its warning and reserves
both families. Host, Origin and token checks remain, including port-80 helpers.
Bridge tags pin the returned Studio origin; command/permanent-plugin coexistence
and existing IP expectations remain covered.

The cookie harness runs the real command and bridge, sets cookies by visiting
the app in the same browser context, and asserts visible text produced by an
HTTP Cookie-header echo. It covers Vite and proxy, all three SameSite variants,
and Vite config reload. It blocks HTTPS and cleans up its process/context/temp
project. These are delivery assertions, not cookie-jar or raw-markup substitutes.

CI installs vite-react and bundles before the Firefox canary, which sets
FKS_REQUIRE_FIXTURES=1. The installed-fixture Chromium matrix includes the cookie
module. Missing fixture dependencies cannot quietly skip that Vite case in
those jobs. Firefox remains advisory. CHANGELOG correctly limits the one-time
settings transition to localhost users of --studio-port. Versions stay 0.3.0.

## Findings

No Critical, Important or Minor finding requiring a change in Task A.

The bounded 20-attempt retry is reasonable: persistent address collisions fail
instead of hanging. An independent fault probe exhausted all 20 attempts for
each public starter, observed EADDRINUSE, and rebound the provisional IPv4 port
while the foreign IPv6 listener still existed. Synchronous non-fallback listen
errors also reject with cleanup. Concurrent and repeated close calls resolve,
destroy active incomplete HTTP connections and release both ports.

The local listenLoopback helper appears twice, once per server. Global rule 10
permits duplication until its third occurrence; extracting it is not required
and would introduce an unowned runtime helper. No dependency is added.

## Independent verification

Commands ran on the integrated working tree; every command below exited 0.
Raw logs and the two additional probe scripts are ignored scratch under
`.superpowers/sdd/v0-3-1/A-review-*`.

```powershell
node --test --test-name-pattern='localhost|IPv6|configuration restart|failed delayed|standalone|Origin|Host|target hostname|Vite resolved|when Vite fails|no local address' packages/fontkitstudio/test/studio-server.test.js packages/fontkitstudio/test/proxy.test.js packages/fontkitstudio/test/run-proxy.test.js packages/fontkitstudio/test/run-vite.test.js packages/fontkitstudio/test/vite-plugin.test.js
$env:PYTHONPATH='tests'; $env:FKS_REQUIRE_FIXTURES='1'; $env:FKS_ENGINES='chromium'
python -m unittest test_localhost_cookies -v
node .superpowers/sdd/v0-3-1/A-review-real-lifecycle.mjs
node .superpowers/sdd/v0-3-1/A-review-retry-close.mjs
git diff --cached --check
git diff -- packages/fontkitstudio/src packages/fontkitstudio/test tests
```

- Targeted Node public seams: 55 tests, 55 pass, 0 fail, 0 skip. Includes both
  listener fault matrices, occupied IPv6, fallback, Host/Origin/token rejection,
  upgrades, resolved-host selection, restart and delayed-start failure.
- Chromium: 2 cookie tests, OK, 0 skips. Proxy and Vite visibly render
  `lax=kept; strict=kept; default=kept`; Vite repeats this after real config reload.
- Real lifecycle script: six successful groups, covering standalone final host,
  restart/new origin pinning/old-listener closure, failed Studio startup closing
  Vite with no tag, and command host/close on each of Vite 7 and 8.
- Retry/close script: six successful groups, covering exhausted conflicts,
  synchronous IPv6 errors and concurrent/repeated close with active incomplete
  HTTP connections for Studio and proxy. Both ports rebind after close.
- Whitespace check passes. No unstaged changes in the runtime/test paths.

The Vite 7 command probe printed a dependency-scan cancellation warning while
its dev server was being closed. All lifecycle assertions passed and the process
exited 0; this quick shutdown does not claim completion of dependency scanning
or replace the installed-fixture browser gates. PowerShell also formats native
stderr from unittest as NativeCommandError; the native exit was 0 and unittest
reported `Ran 2 tests ... OK`.

No prepack, bundle, source mutation, fixture-source mutation or dist mutation
was performed by this reviewer. Vite may update its ignored dependency cache.
All owned server handles/processes were closed in finally/cleanup. No commit,
push, stash, registry write or subagent dispatch was performed.

## Evidence limits and handoff

Live graph index status/coverage confirmed project `font-kit-studio-local`,
generation `2026-10-07T17:07:14Z`, 2637 nodes and 12760 edges. Changed startup
modules/helpers/Python paths report metadata_changed; Node test files are
excluded by fast-pattern, and CHANGELOG by skip-list. Current source reads and
runtime probes supply the review evidence; graph completeness is not claimed.

The full Node package, full focused Python group, Firefox canary, static/lint
and release gates belong to the independent gate runner/controller. This review
does not claim those were rerun here. Full Python halves and the frontend gate
were not run by this reviewer. No current hosted CI, release-point approval,
published version or tag verification is claimed. Task A is approved for its
landing after required independent gate evidence is accepted; Task C remains.
