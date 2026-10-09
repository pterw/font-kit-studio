# R2 F3 independent implementation review

Date: 2026-10-08. Verdict: **Approved**.
Reviewed root branch: `feat/r2-detection`; HEAD:
`6a7327bd2d901f4c668c476a8048658f82c682b6`.
Writer BASE: `653d71610b409e59d542391b7010bcc8bd61c3a8`.

## Scope and verdict

Read the complete F3 brief, durable implementation report and 277-line writer
report, execution constraints, R2.7F3 and relevant binding detection/route
sections. Read all nine current fixture/test files and support.py lines 1-151.
Reviewed only F3. Concurrent F2 staged work and bridge work are outside this
verdict and were not edited or incorporated into F3 acceptance.

Critical: none. Important: none. Minor: none.

## Verified behavior and test quality

- `expected-styles.json:5-59` supplies 14 literal five-property signatures
  and 13 snapshots. `test_r2_route_fixtures.py:98-133` compares rendered
  eligible parents, exact ID sets, bindings, visible text, author roles and
  computed signatures to those literals. Population includes all visible
  navigation/action controls: eight ordinary parents, 14 settled SPA parents
  and 15 pending parents. Expected signatures are not captured at runtime.
- `test_r2_route_fixtures.py:135-181` exercises actual document links, the
  reused `.shared-title` conflict, article zero-match input and absence of
  default unvisited/preload requests. Its separate fresh unvisited baseline
  is explicitly fixture evidence, not an engine checked-page claim.
- `spa.js:31-57` uses native push/replace/back/forward/hash behavior without
  history wrappers or router dependencies. Tests at lines 196-250 verify
  URL, computed typography, history length and rendered restoration.
- `spa.js:45-54` exposes pending state with old content, then replaces real
  nodes on the resolver's animation frame. Tests at lines 252-301 require
  pending/settled and aria-busy changes, detached original handles, exact
  same-URL state/query-order/hash preservation and fragment-free HTTP
  request counts. There is no fixed test sleep or synthetic bridge event.
- `test_r2_route_fixtures.py:59-93` uses fresh shared-runtime contexts,
  earlier local HTTPS fulfillment and a later abort guard. Two HTTPS fetch
  canaries on a separate blank page prove interception before navigation. The
  earlier fallback survives guard deletion. Contexts and retained handles
  close in finally; tearDown provides a context safety net. No server or
  framework process is started.
- New missing-element/control assertions are credible behavior RED;
  native cross-origin history refusal is correctly GREEN characterization.
  The complete writer report records 26 restored foreground mutations,
  including all conflict properties, navigation, node replacement, pending
  state, preload, population and guard deletion. Rejections are 17 assertion
  failures and nine condition/URL timeouts. I read this evidence and checked
  the corresponding assertions; I did not rerun these 26 mutations or alter
  root source to recreate their historical RED results.

## Fresh independent verification

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_route_fixtures test_support -v
# The enclosing shell explicitly returns the native Python exit code.
```

Result: **43 tests in 23.842s, OK, exit 0, no skips**, Chromium only
(nine F3 tests plus 34 support tests).

- Scoped F3 Ruff and product-tree Ruff (`--exclude .agents`): exit 0,
  All checks passed.
- Exact `python -m ruff check .`: exit 1; the four preserved untracked-skill
  findings in scan.py at lines 21, 23, 24 and 294. No F3 finding.
- Static-only verifier: 96 unique IDs, one executable inline block and all
  three provenance blobs pass; full browser acceptance explicitly skipped.
- Node syntax checks for spa.js and fontkit-bridge.js: exit 0.
- Working/staged whitespace checks: exit 0. Existing commit-message range:
  OK, two commits checked. Candidate message remains a controller check.

A separate read-only Chromium keyboard probe used its own locally routed
origin and verified its HTTPS guard before app load. Enter on Replace same URL,
Push detail, Back and Forward restored the exact reordered query/hash and
same-URL history state with cursive family and 36px detail size. Enter on Home
performed real document navigation. No unvisited or external fixture request
occurred. Owned context closed; all nine root source hashes remained unchanged.

The probe's initial preflight incorrectly assumed root LF bytes and stopped
before opening a browser. Direct inspection established Windows checkout CRLF
in all nine root files; canonical CRLF-to-LF comparison then matched the
writer's LF source exactly. Thus raw checkout bytes differ, while canonical
source bytes agree. Source count is 574 authored lines, zero churn. Patch hash
matches `68ddbc63026c863a7db2ad8d345467b870f957258d8779a4296a7c3b777afdc8`.

## Limits and handoff

Parent-supplied Tier 2 coverage identifies docs/fixtures as excluded, the
future test as missing and support metadata as changed at graph generation
`2026-10-07T17:07:14Z`. Reviewer graph reconfirmation was unavailable:
`tools.mcp__codebase_memory_mcp__index_status is not a function`. No alternate
tool retry or fresh graph-verification claim follows. Current direct source
and rendered behavior establish this bounded verdict.

Full Python/Node suites, frontend gate and Firefox were not run for this
fixture slice. Detector freshness, authenticated messages, visited inventory,
BFCache, CSSOM/HMR and wrapper cleanup remain later runtime acceptance.
No production-engine, release or future CI claim is made.

The controller may close R2.7F3 in the separate atomic reviewed landing with
its ledger/plan updates and landing checks. Only this review file was written;
no source edits, staging, commit, push, process interruption or remote review
was performed. Owner files and concurrent work remain preserved.

## Scoped closure review (2026-10-08)

**Approved.** Closure HEAD is `c8fe803`, after the accepted React corpus
landing. Read the complete updated F3 report and exact staged plan/ledger
delta. Only the four F3 checkboxes close; other task checklists and the binding
contract stay unchanged. Root 43/24.543s and independent 43/23.842s acceptance,
writer mutation evidence, keyboard probe, Ruff limitations and canonical
newline qualification agree with the saved verdict. Prior-head CI remains
explicitly pending and required before the F3 commit; no future CI pass follows.

Checked all nine staged source blobs against the reviewed writer bytes and
normalized root files: exact canonical equality, with no source change.
Verified all 69 local link paths in the original four closure records and both
whitespace checks. Staging now contains 14 explicit paths: the original 13 F3
paths plus one F2a report completion-metadata correction.

The initial F3 closing paragraph still described review as required; the
controller corrected it to Approved/closed with its separate landing pending.
Read the full F2a report and its three-line staged delta: it records the
already committed `c8fe803` corpus and removes the same stale pending-review
wording. Local commit evidence supports that status. This review covers only
that F2a completion metadata, without reopening F2a behavior or source.

No remaining finding or new scope follows. No browser, full gate or mutation
rerun was needed for closure. Only this review file was edited; its append
must be restaged by the controller before the atomic landing.

## Final CI-record closure (2026-10-08)

**Approved.** Current HEAD remains `c8fe803`. The saved job receipt matches
that exact SHA and reports 12 completed successful jobs. Its quality log agrees
with the new ledger event: 874 Chromium tests in 573.751s with 16 fixture skips,
51 Firefox canary tests in 91.635s, and frontend 30/30 with seven blocking
passes, zero advisory/failure/skip lines and 332 touch-target reports.

Read the skipped-case records, receipt, completed watch tail, new CI ledger
event and final F3 report status/closing wording. The ledger distinguishes
11 legacy installed-matrix cases, host refusal outside that matrix and four
new React browser cases awaiting R2.7I. It claims neither hosted React corpus
acceptance nor hosted verification of the still-uncommitted F3 source.
The earlier pending event remains historical; the new event records completion.

All nine staged F3 canonical source blobs still equal the reviewed writer/root
source. The same 14 explicit staged paths remain. F3's status is independently
Approved and its fixture task is closed; commit/push are subsequent controller
actions. No new finding, scope, browser/test run or source change follows.
Only this review append was written; the controller must read and restage it.
