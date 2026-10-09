# R2 PR A independent branch review

Date: 2026-10-09. **Source review complete; final verdict pending settled gates.**
Branch: `feat/r2-detection`. BASE: `39ca9457dd119e8bc43b97c6b41dbaf1d1a50740`.
HEAD: `54e3163f38b9f800512580766ada1ce02e8fa0d4`, plus the accepted S1 delta.

## Scope and evidence

Reviewed PR A's full material change inventory against the approved binding
contract, Addenda 3-6, D058/D060/D061 and execution constraints. Read current
AGENTS/global rules and requesting-code-review skill. Prior complete task
reports/verdicts and their accepted source/runtime evidence remain applicable;
this pass does not reopen those tasks or claim their historical runs as fresh.
Re-read the complete current bridge/Studio branch deltas, role helper/host,
relevant fixture oracles, approval/ownership changes and closure records.

Independent read-only SHA-256 comparison checks every one of the frozen
manifest's 182 files: raw and canonical LF hashes all match. All 42 changed
product/test/fixture/attribute paths, including the two untracked S1 tests,
belong to that manifest. Package, workflow, server/tooling, demo, provenance
and existing Bootstrap 5 vendor paths have no branch delta. No owner files
were read as product changes or modified.

Fresh MCP index status confirms `font-kit-studio-local`, ready, 2637 nodes /
12760 edges. Coverage generation is `2026-10-07T17:07:14Z`: bridge/Studio/legacy
test metadata changed, new role tests/helper not tracked, fixtures/docs excluded.
No parser gaps are recorded; this does not establish completeness. Current
direct source and previously verified rendered behavior decide these claims.

## Findings and contract review

No new Critical, Important or Minor source finding. Earlier detector native-state
freshness and S1 select-all portability findings are resolved in their durable
task reviews; their original RED evidence remains preserved.

- `fontkit-bridge.js:933` dispatches Detect only after the existing authenticated
  source/origin/protocol/session check. `:1152` validates exact bounded input;
  `:1230` validates native query syntax cooperatively before using selectors.
  Escaped positive selectors and numeric invalid selectors have behavior tests.
- `fontkit-bridge.js:988` advertises only `roleDetection:true`. `:1017` supplies
  the empty accepted role snapshot and authenticated document/page identity.
  No role stylesheet, Apply/Clear handler, adapter or route notice is shipped.
- `fontkit-bridge.js:1083/:1243` count eligible direct-text parents rather than
  semantic discovery targets. Author roles use authorAttr, exact tuples retain
  variants, binding match sets are verified and near duplicates never merge.
  `:1116` distinguishes author bindings, ordinary classes, uncertain CSS modules
  and unstable paths without changing the author's DOM.
- `fontkit-bridge.js:1043/:1067/:1181` check native events, observable content,
  readable stylesheet state, URL/revision and current job/session generations.
  The second population/style pass at `:1305` detects changed rendering.
  `:1191` bounds terminal payload and includes serialization elapsed time;
  incomplete/stale results cannot assert a complete snapshot.
- Cancellation on hello/session drop/reset and disposal remains owned and
  idempotent. Native listeners use passive capture with exact stored removal
  options; ordinary text input keys are not blanket invalidation events.
- `fontkit-studio.html:3812/:3872/:3909` require authenticated ready identity,
  latest request, monotonic generation, exact nested shapes/counts/references,
  whole UTF-8 limits and canonical supported-origin URLs. Full role identity,
  rather than scan IDs/labels/digests, maps to bounded monotonic session IDs.
- `fontkit-studio.html:3830` renders observations through textContent. Explicit
  unavailable/incomplete/collection-limit status preserves honest coverage.
  `:3929/:4999` isolate role rejections from the legacy mutation queue. Reconnect
  and load discard pending observations without applying saved edits.
- D061 null is confined to unavailable current identity/invalidation. Complete
  null results are rejected; actual unsupported URLs remain unavailable rather
  than truncated or substituted. The old inspector/reset stays usable.
- Existing import/export selectors, persistence, acknowledged Changes, font
  loading, Composer, version labels and protocol/JSON versions are unchanged.
  No preview controls, visited inventory, history wrappers or silent replay leak
  into this detection slice.

## Fixtures, records and accepted focused evidence

Literal static oracles retain the exact 5000-parent, 20-style, 250-per-style
benchmark, nested/range exclusions and native input/heartbeat acceptance. React
characterizations prove real keyed replacement and scratch CSS HMR, not Fast
Refresh. F3's literal native history corpus is fixture evidence, not a checked
visited-page inventory. Owned harnesses verify blank HTTPS fetch canaries with
an earlier local fulfillment fallback and close contexts/process handles.

Fresh byte inspection matches Bootstrap 4 CSS 162264 bytes / `f886516f...`,
licence 1131 bytes / `53d2513c...` and documented exact Bootstrap 5 checkout
forms. Read-only git attributes show scoped Bootstrap 4 `text: unset`; existing
Bootstrap 5 vendors are unchanged. Named churn is the 827-line generated React
lock plus 29 upstream Bootstrap 4 vendor lines, not authored runtime work.

Prior independent approvals retain F1 44 tests, F2a 39, F3 43, detector 72 and
S1 120, all Chromium with zero skips. This reviewer previously ran detector
72/142.316s (first complete 5000 scan 341.9ms, input before reply), S1
120/140.349s and scoped portability 35/23.180s; their full durable reviews own
probe details and limitations. No browser or runtime gate is repeated here.

Current task closure is exactly R2.0, R2.1/R2.2, F1/F2a/F3 and four S1 items.
F2b, R2.3-R2.6, S2, installed CI integration and release remain unchecked.
CHANGELOG promises read-only detection only. Candidate commit has a product
subject/why-body without signatures. Independently checked 118 local Markdown
link paths in changed tracked records: none missing. PR B still requires owner
merge of A and a fresh updated-main branch; no 0.4.0 release readiness follows.

## Settled-wave result and final disposition

Pending the dedicated runner's complete verification report, material gate
summaries and final controller bookkeeping. This source-only pass starts no
browser/server, changes only this review, and performs no stage/commit/push.

## Bounded fullscreen diagnosis (2026-10-09)

**Important, confirmed: the S1 section shrinks the fullscreen preview.**
`fontkit-studio.html:1215` places Detected roles in the same fixed-height flex
column as previewScroller and liveCodePanel (`:718/:469`). Settled B fails the
existing `test_studio_stage.py:104`: 394 tests/517.645s/native1, zero skips,
one failure. Read the complete traceback and native receipt. This supersedes
the initial source-only no-finding result for this layout behavior.

Under systematic-debugging, independently ran that existing single case once
with a guarded context: 1 test/1.401s/FAIL/native1, height 367.6875px. At
1280x800, stage height stays780px and code217.9375px; new unsupported roles
height138.375px plus margin12px consumes150.375px. Fresh public fluid and fixed
1440px measurements agree. Transiently hiding only that new section restores
preview/scroller518.0625px; restoring its exact hidden attribute returns367.6875px.
Routed accepted HEAD54e3163 HTML independently measures518.0625px at both widths.
This is deterministic product layout regression, not an assertion/timing flake.

Script/log: `.superpowers/sdd/r2/pr-a-fullscreen-diagnosis-probe.{py,log}`.
All three contexts prove HTTPS abort2/fallback0 before app navigation; earlier
local fulfillment remains installed. Contexts/shared browser/driver close, no
server is started and all182 frozen raw hashes still match. No disk source/test
mutation, fixed sleep addition, retry-until-pass or threshold change occurred.
Return to the same Studio writer to preserve fullscreen preview height while
keeping role controls usable. Final PR verdict remains held for correction and
the remaining dedicated gates; Node/frontend/Firefox have not yet run.

## Fullscreen correction disposition (2026-10-09)

The confirmed Important layout finding is **resolved in scoped review** under
Addendum 7/D062. Exact markup relocation puts roles after composer-shell; no
CSS/JS/bridge/legacy-test delta follows. Same reviewer's real 63/44.302s/native0
has zero skips and restores 518.0625px fluid/fixed height with reachable scroll
edge. Inert/exit observations and fresh native Enter 23px rendering pass;
source hashes/screenshots/cleanup and complete evidence belong to
[the scoped S1 verdict](r2-task-s1-review.md#scoped-fullscreen-correction-review-2026-10-09).
Original failure and causal diagnosis above remain historical. No remaining
scoped finding; **final PR verdict still pending fresh frozen settled gates**.

## Final PR A verdict (2026-10-09)

**Approved.** No outstanding product finding. The confirmed fullscreen defect
is resolved; its failed wave and causal diagnosis remain above. Acceptance covers
PR A's fixtures, read-only detector and Studio observations under Addenda 3-7.

Read the complete fresh verification, all 13 native receipts and material
stdout, including Firefox, Ruff, Node skips and the lossless 85-target register
covering 338 touch reports. Exact commands and retained logs belong to
[fresh gate evidence](../verification-r2-pr-a.md#fresh-corrected-wave-2026-10-09).
Chromium passes 530/509.255s plus 394/526.954s: 924 tests, zero skips. First
complete 5,000-parent scan is 284.4ms, heartbeat 111 -> 115, input before reply.
Both populated fullscreen widths retain 518.0625px; the unchanged old test passes.
Native cases that complete before their stimulus validate pre-event evidence.
Node passes 269/271 in 10.396s; two Temp-ancestor package guards skip.
Frontend completes 30/30: seven blocking pass, 23 advisory, no failures/skips.
Detect's 131x34 touch size follows S1's compact styling and remains a disclosed
D029 advisory; keyboard/focus and narrow rendering evidence remains valid.
Firefox canary passes 51/115.568s, zero skips. Static/provenance, syntax, product
Ruff, whitespace and message checks pass; exact Ruff exits 1 for the same four
preserved owner-skill findings. Remaining gates ran sequentially under the
controller after runner unavailability before Node launch; no failed run is hidden.

Independently rehashed all 182 frozen files: current raw/canonical bytes and both
wave receipts match, at HEAD 54e3163 on feat/r2-detection. Current S1 closure,
Addendum 7/D062, CHANGELOG and candidate message agree; Current state now names
completed gates and pending final review. Reviewed native PIDs are absent;
this final read-only pass started no browser/server. No full Gecko, fresh macOS,
universal animation tracking, publication or future PR B acceptance is claimed.

## Scoped Graphify documentation audit (2026-10-09)

**Approved:** the four-section triage correctly declines ten visible advisories
at review 5466236663/check 113690963759, exact 60ed912. Independently read every
cited range: AGENTS' current/add/tearDown/open guidance, CLAUDE workflow prose,
CONTRIBUTING setup and README36-122 match unchanged CLI10-100/serve277-326/options.
PR-base diff is empty for those references, support and all package source.
CLAUDE's canonical SHA remains d4932f74a1d78b1ee7f3a2eddb97b4503267d629089afe1a3171be854d059595; no protected edit occurred.
Both bodies omit ten further items; live annotations/comments are empty, so
those items remain unchecked. Refreshed Tier2 coverage is stale/excluded;
direct source decides. Zero tests/corrections; no hosted-CI acceptance here.

## Publication-record review (2026-10-09)

**Approved.** Complete four-document delta and candidate message agree with
run 37890551427 at 60ed912: twelve completed successful jobs; Chromium
924/657.884s with sixteen disclosed install skips, Firefox 51/89.739s without
skips, frontend 30/30 and 336 reports. Reviewed job/quality evidence confirms
168ms/input-before scan and 518.0625px fullscreen; fast CI's pre-event native
completions establish no pending-invalidation proof. All 182 current canonical
hashes still match. No tests rerun or resources started; this accepts records
for 60ed912, not the future documentation commit, owner merge or PR B.
