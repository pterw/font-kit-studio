# Task A implementation report

Date: 2026-10-07. Base: `6bd4a044294fd92f76ed14fada25048b6fcc0773`.
Checkout: `C:/fks/v031-a` (detached). Ready for independent review; not a release verdict.

## Behavior delivered

Localhost targets now advertise localhost for both Studio and proxy. IP targets, including
`[::1]`, retain the previous advertised 127.0.0.1 behavior. Vite command and standalone
plugin choose from Vite's final resolved local URL after listen, rather than assuming a host
before Vite starts. Command/permanent-plugin coexistence still adds one bridge tag.
Middleware mode uses the resolved host configuration when no app URL exists.

Each server advertised as localhost reserves 127.0.0.1 and ::1 on the same port before
returning its origin. Occupied IPv6 closes provisional IPv4 and retries a free port;
retries stop after 20 conflicts. Only EADDRNOTAVAIL/EAFNOSUPPORT permits IPv4-only startup.
Other errors clean up and reject. Fixed Studio-port conflicts retain the existing warning,
and fallback reserves both addresses. Listener code is local to each server under global
rule 10. No runtime dependency or new helper source file was added.

Close frees both listeners, active HTTP connections and proxy upgrades. Host/Origin/token
guards and origin-pinned tags remain. Existing HTTP, redirect, headers and WebSocket
tests pass. Vite config restart closes the old Studio and prints a usable new token URL;
returned runner URL properties reflect the latest run. Real Vite config reload also
preserves rendered cookie delivery.

## Regression and characterization evidence

The first browser test ran the real command with --no-open against unchanged runtime.
Cookies were set by a same-context visit to localhost, then visibly rendered by a framed
page fetching its own HTTP Cookie-header echo. https requests were blocked. No
document.cookie, raw markup, fake bridge or preloaded cookie jar supplied delivery evidence.

| Original runtime | Chromium | Firefox |
|---|---|---|
| Vite | No cookies: Lax/Strict/omitted absent | default=kept: omitted passes; Lax/Strict absent |
| Proxy | No cookies: all absent | No cookies: all absent |

The initial RED log records four failing browser subtests. Its Firefox-proxy omitted-cookie
precondition followed the original brief's assumption; observed behavior disproved it.
The controller accepted the split and corrected the work order. GREEN requires all three
cookies in both modes and both engines. See A-cookie-red.log, A-cookie-green.log and
A-real-restart.log. The final canary reruns both paths, including real configuration reload.

A-original-ip-characterization.log temporarily restores the original five modules from HEAD,
probes localhost/127.0.0.1/[::1] through public runProxy, and proves original IP advertisement,
path/query/hash preservation and Studio/bridge HTTP 200. Existing security guards also pass
on original source. All five source files were restored byte for byte in finally.
This follow-up characterization was performed after the first cookie GREEN, not claimed as
earlier chronological RED. Final table tests preserve those IP expectations.

Separate vertical-slice RED logs: A-dual-red.log and A-proxy-dual-red.log demonstrate the
missing IPv4 localhost listener; A-restart-red.log demonstrates the stale post-restart URL.
Their focused GREEN logs and the final suites prove the corrected behavior.

## Focused gates

Fixture installs: `npm ci --prefix fixtures/vite-react` (18 packages) and
`npm ci --prefix fixtures/vite7-react` (17 packages), exit 0. Prepack/bundle exit 0.
The cookie page/config lives in a temporary test-owned project using the installed
fixture dependencies. Tracked fixture source has no final diff.

| Command | Result | Evidence |
|---|---|---|
| npm --prefix packages/fontkitstudio test | exit 0; 271 discovered, 269 pass, 0 fail, 2 skip | A-node-final-green.log |
| PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 FKS_ENGINES=chromium python -m unittest test_localhost_cookies test_one_command_vite test_one_command_proxy test_node_studio_server test_support -v | exit 0; 44 tests in 41.159s; OK; no skips | A-focused-final.log |
| PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 FKS_ENGINES=firefox python -m unittest firefox_canary -v | exit 0; 51 tests in 114.081s; OK; no skips; advisory | A-firefox-final.log |
| python scripts/verify.py --static-only | exit 0; IDs, JS syntax and all three provenance hashes pass | A-fast-final.log |
| node --check fontkit-bridge.js | exit 0 | A-fast-final.log |
| python -m ruff check . | exit 0 in scratch | A-fast-final.log |
| python -m ruff check . --exclude .agents | exit 0 | A-fast-final.log |
| git diff --check | exit 0 | A-fast-final.log |
| python scripts/dev/check_commit_messages.py --range origin/main..HEAD | exit 0 | A-fast-final.log |

The two Node skips are existing project-discovery cases because a package.json exists above
AppData/Local/Temp. They are not fixture or cookie skips. The scratch worktree lacks the
controller's untracked installed-skill Ruff errors; controller lint must be reported separately.

Intermediate Node failures were diagnosed rather than hidden: localhost expectations needed
the three files authorized by Addendum 3; the new WebSocket test exposed shared fixture
request-count assumptions. A-node-first.log and A-node-final.log retain those failures.
Generated-test syntax/Windows default decoding issues were corrected before final gates.
No product behavior RED was manufactured from these harness failures.

Full Python halves, frontend gate, release verification and hosted CI were not run by this
implementer, as the work order requires focused gates only. Controller integration and
independent review remain.

## Mutation sensitivity

22 distinct guards were mutated one at a time in foreground Node subprocesses. The Python
harness saved source bytes, replaced one exact string, ran the selected public-seam tests,
captured stdout/stderr, restored in finally, and asserted byte equality. Every mutation was
caught. See A-mutations.log for the exact replacements and full commands; individual raw
output is in A-mutation-<name>.log.

| Mutation | Source | Test-name pattern | Exit/outcome |
|---|---|---|---|
| studio-dual | studio-server.js | `localhost reserves` | 1: assertion/startup failure |
| proxy-dual | proxy.js | `localhost proxy reserves` | 1: assertion/startup failure |
| studio-ipv6-unavailable | studio-server.js | `IPv6 EADDRNOTAVAIL\|IPv6 EAFNOSUPPORT` | 1: assertion/startup failure |
| proxy-ipv6-unavailable | proxy.js | `IPv6 EADDRNOTAVAIL\|IPv6 EAFNOSUPPORT` | 1: assertion/startup failure |
| studio-ipv6-other-error | studio-server.js | `IPv6 EACCES` | 1: assertion/startup failure |
| proxy-ipv6-other-error | proxy.js | `IPv6 EACCES` | 1: assertion/startup failure |
| studio-retry | studio-server.js | `retries an occupied` | 1: assertion/startup failure |
| proxy-retry | proxy.js | `retries an occupied` | 1: assertion/startup failure |
| studio-partial-cleanup | studio-server.js | `IPv6 EACCES` | 1: assertion/startup failure |
| proxy-partial-cleanup | proxy.js | `IPv6 EACCES` | 1: assertion/startup failure |
| proxy-host-selection | run-proxy.js | `target hostname selects` | 1: assertion/startup failure |
| fixed-port-host | run-proxy.js | `IPv6-only fixed` | 1: assertion/startup failure |
| vite-host-selection | vite-plugin.js | `standalone pins the final` | 1: assertion/startup failure |
| bridge-origin | vite-plugin.js | `standalone pins the final` | 1: assertion/startup failure |
| restart-url | run-vite.js | `configuration restart` | 1: assertion/startup failure |
| host-guard | studio-server.js | `localhost listeners retain` | 1: assertion/startup failure |
| origin-guard | studio-server.js | `localhost listeners retain` | 1: assertion/startup failure |
| token-guard | studio-server.js | `localhost listeners retain` | 1: assertion/startup failure |
| upgrade-second-family | proxy.js | `localhost proxy forwards` | 1: assertion/startup failure |
| studio-close | studio-server.js | `localhost reserves` | 124: failed assertion, then timeout |
| proxy-close | proxy.js | `localhost proxy reserves` | 124: failed assertion, then timeout |
| plugin-start-failure | vite-plugin.js | `failed delayed Studio startup` | 1: assertion/startup failure |

Close mutations produced the expected failed refusal assertions but deliberately left an
HTTP listener alive, so the subprocess exceeded its 8-second bound. Python subprocess.run
killed and waited for that owned Node process (exit recorded as 124), then restored source.
No process-name kill or background mutation loop was used. Initial EACCES broad-fallback
mutations also timed out because an unexpected successful startup escaped test cleanup.
The test added independent handle cleanup, then reran those mutations; final logs show
ordinary exit-1 assertion failures. The final full Node run is unmutated and green.

## Scope, changed expectations and self-review

Patch: 15 owned files, 784 additions / 102 deletions (886 changed lines), no formatting-only
mass rewrite. This revises the 400-600-line estimate because both servers need the fault
matrix, all target kinds, lifecycle/tag guards, and a 177-line browser HTTP harness.
No shared file, version label, tracked fixture, user app, registry setting or controller
runtime source was edited. New test intent-to-add is the only index mutation.

Existing expectations changed only for localhost app targets: CLI Open URLs and cleanup
port parsing, runProxy bridge-tag origin, standalone-plugin Open lines, and the Bootstrap
proxy browser Open assertion. Fake Vite now invokes real plugin hooks and resolves URLs
during listen; plugin tests await listen instead of assuming eager Studio startup.
The pre-existing WebSocket assertion now measures one request relative to its starting
count and inspects the latest request. IP/refusal cases remain covered.

Anti-pattern review: no wildcard bind or known-origin wildcard post, no new DOM markup
sink, no protocol change, no source rewrite or state overwrite, no telemetry/dependency,
no personal default, no raw browser markup read, no new sleeps. Every owned server/helper
has handle-based cleanup. No commit/push/stash/spawn/tag/registry mutation occurred.

Graph evidence is qualified: parent Tier 2 discovery at font-kit-studio-local generation
2026-10-07T17:07:14Z was used for routing. Live list_projects/index_status and coverage
checks confirm that project, but it indexes the controller rather than scratch. Startup
files/helpers/Python support report metadata_changed; Node test files are excluded by
fast-pattern; the new cookie module is missing there. Direct scratch source/diff and
runtime evidence support this implementation. No claim of complete graph verification
or scratch indexing is made.

## Draft controller-owned text

CHANGELOG Fixed:
- Localhost apps keep sign-in cookies inside Font Kit Studio in Vite and proxy modes.
- For a localhost app, users who pinned Studio with --studio-port start with fresh Studio
  settings once because its host changes from 127.0.0.1 to localhost. Without a pinned
  port, settings already follow the random Studio port each run.

README limitations:
Studio follows localhost app URLs; use the same hostname when signing in and when running
the app in Studio. Cookies for localhost and IP aliases remain separate. Proxy-origin
localStorage/IndexedDB/service workers still belong to the proxy origin and do not migrate
from the normal app port. Random proxy and unpinned Studio ports change between runs.

CI draft:
Include test_localhost_cookies in the installed-fixture Chromium job. Install vite-react
and bundle the package before Firefox canary; set FKS_REQUIRE_FIXTURES=1 so cookie tests
cannot silently skip. Firefox remains advisory.

Ledger draft:
Localhost Studio/proxy origins and dual loopback reservations implemented. Chromium focused
44 OK; Node 269 pass/2 environment skips; Firefox advisory canary 51 OK. All 22 mutation
guards caught. IP behavior, trust checks and config restart preserved. Full integrated
gates and independent review pending; link this report instead of duplicating the matrix.

Commit draft:
fix(dev): preserve localhost sign-in cookies in Studio

Keep the app, Studio and proxy on the localhost site so framed requests
retain sign-in cookies. Reserve both loopback address families before
publishing a URL, and refresh Studio after Vite configuration restarts.
## Controller integration evidence

The patch applied cleanly to fix/localhost-cookies at 6bd4a04. Independent
review is Approved, with no material findings; see v031-task-A-review.md.
The integrated source remained frozen during the landing gates:

- Node package: 271 tests, 269 pass, 0 fail, two existing temporary-directory
  project-discovery skips.
- Chromium focused group, including test_release and test_support: 69 tests
  in 42.785 seconds, OK, no skips.
- Firefox canary: 51 tests in 116.285 seconds, OK, no skips; advisory.
- Static/provenance, bridge syntax, whitespace, prepack and commit-message
  range pass. The candidate commit message passes its separate check.
- Exact Ruff reports four findings solely in the untracked owner-installed
  skill. Product-tree Ruff with .agents excluded passes; no lint-policy or
  owner-file change was made.

The full Chromium halves and frontend gate remain required for Task C and
were not run for this landing. Raw integration logs remain in ignored
.superpowers/sdd/v0-3-1/A-integrated-*.log. No release or publication is claimed.
