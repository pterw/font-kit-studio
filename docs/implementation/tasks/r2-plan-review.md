# R2 work-order preparation review

Date: 2026-10-08. Verdict: **Changes required**.

Review target: the uncommitted documentation draft on `docs/r2-engine-plan`,
HEAD `dc1da5369034e4ca2891753e9c3f86bbef92b61e`. The released base is
`13482685faff7519459804335ad54cfdc4f8dc0f`; the publication closeout is a
separate reviewed commit. No runtime change was reviewed as implemented.

## Spec compliance

The draft covers the approved design's R2 scope: detection, suggested roles,
author hints, adapters, role CSS, honest preview, visited pages and performance.
The D058 thresholds are represented accurately as draft choices, without
claiming approval of the full work order. The separate audit is concrete and
still awaiting approval; writing its brief does not claim audit evidence.

The proposed Detect/list and explicit Apply/Clear surface supplies a real
Studio path for each new protocol boundary. R3 picker/pairing/scale/inspector
migration and R4 output/state formats remain separate. The plan assigns
structured input and hostile validation to both sides, deterministic canonical
CSS to the bridge, and measured mismatch counts rather than universal cascade
attribution. It preserves legacy inspector state and explicit reconnect choices.

The three Important findings below concern missing binding semantics. They
must be resolved in the draft before it is presented as an executable work
order. They are confirmed documentation gaps; their runtime consequences have
not been reproduced because R2 is not implemented.

## Findings

### Important F1: PR A cannot establish the promised document freshness from ready

Evidence: `docs/plans/2026-10-03-r2-engine.md:201-207`, `:514-517`,
`:548-549`, `:607-609`, `:642-654`.

The contract introduces `design:ready.roleState` with documentId/pageVersion,
but its implementation is assigned to R2.3: "Add ... roleState on ready."
R2.S1 lands in PR A after R2.2 and must "reject wrong generations". R2.2
also promises cancellation and correct page generation, while the history
invalidation hooks are not assigned until R2.6B in PR C. A first detected
reply cannot independently establish that its claimed document is the current
one, and URL-only SPA changes need a guard before route hooks arrive.

Current source confirms no generation identity in ready
(`fontkit-bridge.js:957-965`). Studio accepts ready at
`fontkit-studio.html:4720-4744`; a protocol session is transport identity,
not document/route identity. The plan already distinguishes these identities.

Correction: assign the authenticated ready identity to R2.2, including an
explicit empty role snapshot if roleStylesheet is unavailable. Have S1 bind
detect requests/replies to that ready identity and current pending request.
Assign minimum URL/content/style freshness guards to R2.2: recheck actual URL
and relevant generation at every yield and terminal result. R2.6B can then
add automatic history notifications and selector-page evidence without being
a prerequisite for PR A's basic detection safety. Add PR A tests for an unknown
document, old generation, and a URL-only change during cooperative detection.

### Important F2: post-commit invalidation has no terminal mutation outcome

Evidence: `docs/plans/2026-10-03-r2-engine.md:113-124`, `:175-180`,
`:209-216`, `:540-547`, `:624-629`.

The plan requires revalidation before committing and before posting, while
"Bridge outcomes wait for a rendered frame". Apply must install CSS before
that measurement. A normal app rerender, text mutation or SPA navigation in
the same session can change pageVersion after installation but before the
reply. The contract does not say whether the installed sheet/revision is
rolled back, whether an accepted mutation is acknowledged with incomplete
outcomes, or whether its reply is suppressed. The only role loss reason for
an incomplete measurement is budget-exceeded; page-changed is absent there.

Suppressing an acknowledgement after acceptance leaves Studio without the
canonical state it must show. Returning rejected while retaining new CSS
contradicts the unchanged-state rejection contract. This matters to the
existing queue: `fontkit-studio.html:3982-4010` waits for a correlated reply
and, after timeout, advances later operations using the last known revision;
`:4269-4292` settles the operation from its terminal reply.

Correction: define the mutation commit point and exactly one terminal reply
for same-document/session operations. A workable policy is to commit once,
acknowledge canonical accepted roles/CSS/revision, and mark only rendered
outcomes incomplete/stale when post-commit page evidence changes, with a
bounded page-changed reason and a refresh path. Old document/session replies
remain suppressed because their transport is no longer current. Alternatively
specify full rollback before a rejection, including revision and prior CSS.
An immutable operation receipt can carry the captured commit identity and
separate current identity; Studio must settle that receipt without treating
its stale measurement as current checked-page evidence. Keep the committed
roles/CSS/revision immutable, authenticate the receipt's source/session, match
its request/type, and prohibit an older receipt from replacing newer canonical
state. Separate page-evidence validation from mutation-queue settlement.
Choose one policy and bind it on both sides. Test a real rerender between
installation and measurement followed by a queued inspector edit or clear;
assert canonical state, revision and eventual queue settlement.

### Important F3: multi-page role identity and collection bounds are undefined

Evidence: `docs/plans/2026-10-03-r2-engine.md:130-138`, `:164-174`,
`:193-194`, `:290-301`, `:315-342`, `:660-679`.

The wire types provide group/role IDs, and Studio must replace route snapshots,
aggregate counts, send knownRoles, and flag a selector matching another style.
No binding rule defines how IDs are constructed or how groups from separate
documents map to the same collected role. Suggested names are not unique;
automatic group order can change. Author roles with divergent signatures
must also remain one identity rather than becoming another role. The research
report explicitly distinguishes role identity from signature, but the draft
does not freeze that distinction into its contract.

The 128 role/group limit is also not assigned to the complete session
collection. Thirty-two valid route snapshots can together contain more than
128 different groups; knownRoles cannot safely grow indefinitely or silently
drop some retained role checks.

Correction: define collision-free author/automatic identity rules and the
Studio mapping algorithm, independent of display name and enumeration order.
Bind same-author-role/different-signature conflicts, automatic equal-style
groups with different selector bindings, and a reused selector with changed
baseline. State whether 128 limits the collection or each route, how knownRoles
is bounded, and the visible overflow behavior that preserves earlier evidence.
One workable mapping uses full identity keys (exact author-role name in a
separate namespace, otherwise the exact normalized style tuple) and Studio-issued
session role IDs. Do not use suggested labels, scan order or a hash alone as
identity. Retain selector/count contributions per route, replacing rather than
appending them on revisit; evaluate selector reuse against prior baseline
signatures even when it produces a new automatic style identity. Any collection
overflow must bound retained contributions and knownRoles without claiming that
omitted selectors were checked.
Assign these rules to R2.2's IDs and R2.6S's collection tests. Include reordered
discovery, same names with different bindings, author-role style drift, and
collection overflow across individually valid pages.

## Execution feasibility checked

- F2a is a standalone fixture characterization in PR A; F2b adds role tests
  after R2.4 in PR B. S1 is Detect only; S2 lands after measured bridge outcomes.
  These staged tasks avoid a cross-PR completion cycle.
- R2.3 requires measured match/property losses immediately, using unknown
  attribution where appropriate. R2.5 adds proven selectors and finer reasons.
  It does not authorize placeholder all-success replies.
- The owned role host/harness explicitly awaits detected, roles-applied and
  rejected by requestId. That is necessary: current host.html only awaits
  legacy applied/rejected. Existing helper files remain read-only.
- Fixture paths, lockfiles, upstream provenance, literal style oracles,
  scratch HMR, production cleanliness and installed CI acceptance are assigned.
  Vite 8.3.2/7.3.6 and Next 16.3.8 match current fixture source. Final CI work
  explicitly adds install and module lines to the existing matrix/Next jobs.
- Bridge and Studio writers own disjoint runtime files, land serially, and
  use independent review. Shared harness, workflow and canary ownership is named.
  PR estimates and the 7,700 stop point remain below the 8,000 material cap.
- Tests distinguish genuine missing behavior from passing characterization.
  Reset and handshake class/method references name existing source. The new
  RoleBridgeCase is explicitly produced by R2.1 rather than assumed to exist.
- Canonical node identity, rejected replacement retention, clear/global versus
  target reset/dispose semantics, CSP refusal, baseline sheet restoration,
  selector conflicts and mismatch/unknown attribution are planned.
- Gecko remains a bounded advisory canary, not the full suite. The release
  point assigns versions, forwarder removal, bookmark documentation, provenance,
  sweep and publication checks without claiming publication or merge authority.

## Evidence and checks

Read in full: AGENTS.md, global rules, preparation brief/report, the 905-line
plan, audit brief, approved typography design, both research reports and
workspace constraints. Read handoff sections 2/5/6 and complete supporting
diffs for deviations, roadmap, Current state and the R2 event. Read targeted
current bridge/Studio, browser helpers, host fixture, handshake tests, support
guard, integration harness, fixture pins and workflow source. Current source
overrides the research snapshots.

Graph Tier 2: list_projects confirmed `font-kit-studio-local` at this root;
index_status is ready, generation `2026-10-07T17:07:14Z`. Bridge symbol lookup
and handleMessage trace were complete at depth 1 (11 callees, one caller);
the exact snippet was read. Coverage checked every evidence path. Runtime/test
metadata is changed with no recorded missed ranges; docs, fixtures and scratch
reports are excluded. Direct current-source reads supply material evidence.
No exhaustive graph or runtime verification claim is made.

Reviewer reran:

- `git diff --check`: exit 0; checkout LF/CRLF warnings only.
- `python scripts/verify.py --static-only`: 96 unique IDs, one executable inline
  block, all three supplied-v0.1.1 provenance hashes pass. Browser acceptance
  is explicitly skipped by that command.
- `node --check fontkit-bridge.js`: exit 0.
- `python scripts/dev/check_commit_messages.py --range origin/main..HEAD`:
  `commit-message check: OK: 1 commit checked`.
- Exact `python -m ruff check .`: four findings in the preserved untracked
  `.agents/.../scripts/scan.py` (F401 json/Set/re and F841 exclude_dirs_str).
  The exact gate does not pass. `python -m ruff check . --exclude .agents`:
  `All checks passed!`; this is a separately disclosed product-tree check.

Not run: full Python suite, Node package suite, frontend gate, Firefox canary,
browser probes/downloads, runtime mutation tests, the Library/Composer audit,
candidate commit-message check or publication/external review. They are outside
this read-only documentation review or belong to the controller's landing.
New tests: zero. Engines verified: none. No tool call was denied. No server or
browser process was started. Only this review file was written; no commit,
push, merge, npm write or subagent dispatch was performed.

After F1-F3 are resolved, obtain a scoped re-review. Audit-brief approval,
audited evidence reconciliation and final work-order approval remain separate
prerequisites to runtime dispatch.

## Scoped re-review: contract corrections

Date: 2026-10-08. Verdict: **Changes required** for the new task dependency
below. F1-F3 are resolved in the proposed contract. HEAD remains `dc1da53` on
`docs/r2-engine-plan`; no R2 runtime implementation or audit is claimed.

Read the full revised protocol/identity sections, affected R2.1/R2.2/R2.3/S1/
S2/R2.6 tasks, acceptance example, PR dependency diagram, preparation report
and new R2 ledger event. Graph coverage again confirms these documents are
excluded; current source bytes were read directly. `git diff --check` passes
with checkout LF/CRLF warnings. Runtime gates were not repeated for these
documentation corrections; no browser engine is verified.

F1: resolved at plan `:117-137`, `:218-225`, `:617-624`, `:723-724`.
R2.2 now supplies authenticated ready identity before S1 and performs minimum
URL/content/style freshness checks before the later notification hooks.
Complete/incomplete replies distinguish captured and current identity; an
unknown document or superseded/older reply cannot establish identity.

F2: resolved at plan `:239-261`, `:653-655`, `:743-745`. The synchronous
verified install/accepted-state/revision update is the commit point. A
same-session/document operation always receives an immutable terminal receipt;
page-changed outcomes are empty and explicitly incomplete. Queue settlement,
canonical revision acceptance and checked-page freshness are separate. Tests
cover rerender followed by a queued inspector edit/clear. The contract also
adds an authenticated empty snapshot to the legacy global-reset reply.

F3: resolved at plan `:143-159`, `:167-186`, `:361-415`, `:621-622`,
`:788-791`. Namespaced full keys, reply-local group IDs and Studio session IDs
are distinct. Per-route replacement, reference selector signatures, author
variants and equal-style/different-binding contributions are explicit. Whole
collection overflow rejects the new snapshot visibly, preserving prior evidence
without silently truncating knownRoles. Collection clear leaves accepted preview
and inspector state intact and invalidates pending collection work.

### Important F4: R2.3 completion now depends on the later Studio preview slice

Plan `:653-655` asks R2.3 to assert "visible canonical CSS ... on both sides";
`:661-662` asks it to assert "Studio's cleared preview state". R2.3 owns bridge
and bridge-host tests. Real Studio preview controls are introduced in S2, whose
landing requires R2.5 (`:732-734`); R2.5 depends on R2.4, which depends on R2.3.
The new visible Studio assertion therefore creates a completion cycle.

Correction: R2.3 verifies canonical receipt, revisions, queue-compatible ordering,
target computed undo and the authenticated empty roleState using its owned host.
Assign visible real Studio receipt/global-reset assertions to S2, alongside its
existing post-commit settlement test. Keep the binding global-reset contract.

### Minor F5: route RED wording no longer matches the earlier detection guarantees

Plan `:763-764` still proposes RED because history changes do not invalidate
a pending scan. R2.2 now supplies that cancellation at `:128-130`, `:619-620`.
Correction: characterize preserved cancellation as passing. Use the new automatic
roles-page notification and selector-page evidence as the genuine route RED.

### Minor F6: the detect example omits its newly required documentId

Plan `:867-869` discards ready and sends detect without documentId, while the
binding request at `:210` requires ready's documentId. R2.1's helper contract
at `:509-511` explicitly fills envelope/revision but does not explicitly promise
ready-document filling. Correction: capture ready and pass its roleState.documentId
in the example, or bind the owned helper to fill that field by default while
allowing hostile tests to override it.

These follow-on corrections require only task/example wording, not new runtime
scope or another audit. No other material issue was found within this re-review's
bounded scope. Only this review file was written; no denied call, process start,
commit, push, merge, npm write or subagent dispatch occurred.

## Final scoped verdict: task and example corrections

Date: 2026-10-08. Verdict: **Approved** for the documentation draft. This is
the current review verdict; the earlier findings remain as the dated review
record. All F1-F6 are resolved. This approves the proposed work-order documents
for landing, not the owner's final product-plan approval or runtime dispatch.

Reread the final corrected task/harness/example source:

- F4 resolved at plan `:653-663`, `:744-754`: R2.3 owns authenticated host
  receipts, target computed styles/revisions and the global-reset empty snapshot.
  S2 owns real Studio queue settlement and visible reset state after its preview
  controls exist. There is no longer a completion cycle through R2.5/S2.
- F5 resolved at plan `:766-768`: existing scan cancellation is passing
  characterization; missing automatic roles-page/refresh evidence is the RED.
- F6 resolved at plan `:872-875`: detect explicitly supplies authenticated ready's
  documentId. The stylesheet example now opens its owned protocol fixture,
  characterizes the 16px baseline and verifies the change to 24px; it cannot pass
  from an accidental matching style in the large-page corpus.
- The role host now explicitly awaits legacy applied as well as the new replies
  (`:509-511`), supporting mixed inspector/reset/role probes. R2.6S's code phase
  and landing prerequisite are separated explicitly (`:784-786`).

No remaining Critical, Important or Minor finding within the reviewed scope.
`git diff --check` passes on the final source with only checkout LF/CRLF warnings.
No full suite/browser or audit was run for this final documentation check.
The earlier disclosed exact Ruff limitation remains. Only this review file was
written; HEAD/branch and ownership are unchanged. Audit-brief approval, audited
evidence reconciliation and final owner approval remain prerequisites to R2.

## Bookkeeping confirmation

Date: 2026-10-08. Verdict remains **Approved**. Verified the final preparation
report, Current state, R2 final-verdict ledger event and dated plan ledger row.
They consistently distinguish independent documentation approval from pending
audit evidence and final product-plan approval. No R2 task is marked complete.
The report/ledger verdict links resolve to the existing final scoped verdict
heading above. The protocol fixture's explicit 16px/line-height:1.5 baseline
and empty-CSS digest wording agree with the reviewed examples and contract.

Read the recorded planning-gates.json command output. The final report preserves
the exact Ruff failure and separately labels the passing product-tree check;
it makes no runtime or engine claim. The recorded link scan predates the final
review link and reports 28. A fresh documentation-only rerun now reports:
`PASS planning links/tasks: 29 existing relative links; no completed R2 task or placeholder`.
Coverage confirms these records remain excluded from the graph; direct files
and command output supply this confirmation. HEAD remains `dc1da53` on
`docs/r2-engine-plan`. No runtime gates were repeated, no new finding remains,
and only this review record was written.
