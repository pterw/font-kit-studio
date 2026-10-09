# Unavailable current URL contract review

Date: 2026-10-08
Verdict: Approved
Scope: preparation contract only; no runtime acceptance.
Checkout: feat/r2-detection at 4aa264a9e38f17f897a93a3a8e99786a361c0900.

## Findings

No Critical, Important or Minor findings in the reviewed scope. The approved
fallback is consistent with the binding URL policy and preserves the existing
authentication and evidence boundaries.

- Plan lines 111-117 retain authenticated target origin, HTTP(S), no credentials
  and the 2,000-character pathname/search/hash cap for every non-null URL. Null
  is an unavailable actual current role URL, never a route key or checked-page
  identity. Exact shape, authentication and document/version checks remain
  mandatory. The updated ready and route clauses at lines 341-342 and 535-538
  remove the previous contradictory non-null absolutes.
- Plan lines 119-125 distinguish nullable ready from detection: ready retains
  implemented capabilities and the actual accepted canonical snapshot; R2.2
  remains empty roles/CSS with digest 811c9dc5. Initial unsupported Detect rejects
  safely. Valid-to-unsupported invalidation keeps the captured valid URL, sends
  currentPageURL:null and empty groups/selectorChecks, and yields no checked data.
- Plan lines 126-134 preserve the commit boundary. Apply cannot commit on an
  unavailable URL. A previously committed Apply retains its immutable accepted
  receipt with stale null measurement and empty outcomes. Authenticated Clear
  keeps normal document/page/revision checks and the explicit empty undo receipt
  exception (outcomesComplete:true, outcomeReason:null). Global and target reset
  retain their different effects. These agree with the base receipt contract at
  lines 356-378; successful undo is not checked-page evidence.
- Plan lines 135-149 prevent future null route keys, preserve earlier visited
  records, and require actual unsupported-to-unsupported URL changes to advance
  freshness. Obsolete jobs cannot learn identity. Studio disables Detect/Apply
  with the specified visible reason while authenticated inspector/undo remain
  available. Supported reconnect supplies fresh ready without automatic replay;
  complete detections and fresh Apply measurements cannot contain null.
- Task 2 lines 24-27 and 47-59 keep PR A limited to detection and nullable ready,
  with existing inspector/reset preserved. They explicitly defer Apply/Clear to
  PR B. S1 lines 51-58 similarly scope nullable status/detection and defer preview
  controls. The global-reset roleState acknowledgement remains R2.3 work at plan
  lines 785-788; neither current brief requires that future snapshot now.
- Plan lines 151-158 and both current briefs require real boundary tests,
  exact 2,000/2,001 boundaries, actual URL transitions, recovery and hostile URL
  strings. The future stylesheet, React role and Studio preview sections refer
  back to Addendum 5/D061 and preserve the PR B prerequisite. D061, constraints
  ruling 12, the approved scratch proposal and progress lines 10/69 agree.

## Reading and verification limits

Read AGENTS.md and global rules, the complete Addendum 5, URL-related binding
base clauses (envelope/limits, ready/messages/receipts, canonical undo and route
observation), R2.2/R2.3 scope, and the complete current five-document diff. Read
both current producer/S1 briefs in full, D061, Current state/latest URL event,
the full scratch URL proposal and constraints, and all appended unavailable-URL
sections in the three future briefs. The future stylesheet, React role and
Studio preview drafts were also read in full. No requested bounded contract
section remains unread. Unrelated plan sections, earlier ledger history and
other deviation records were outside this review.

Parent-supplied Tier 2 graph context identifies the docs subtree as excluded,
the bridge as metadata-changed and future modules as missing. Direct current
documents are the evidence here. No fresh child MCP, indexed completeness or
new runtime claim is made.

No code, implementation reports, CI receipts or new browser behavior were
accepted by this review. No tests, gates, browsers, mutations, staging, commits
or pushes ran. The ledger's 2,020-character Chromium probe is recorded historical
evidence, not independently reproduced here; its credential-location and other
engine limitations remain explicit. The writer's existing passing cases do not
establish the missing URL-policy implementation. R2.1/R2.2 remain open for that
implementation and independent real-boundary acceptance.

## Scoped documentation and CI follow-up (2026-10-08)

Verdict: Approved. No Critical, Important or Minor findings.

HEAD remains 4aa264a9e38f17f897a93a3a8e99786a361c0900. The durable
tasks/r2-url-contract-review.md was an exact text copy of the original verdict
before this append. The root holds the five controller document edits and that
new durable copy; no changing implementation source was read.

Task 2 lines 83-90 require public probes for native-invalid .1/#1 selectors,
escaped numeric positives, native pseudo-state changes during a pending scan,
stable subsequent rendering and final wire byte limits. Reproduction precedes
fixes; private-method hooks and manufactured RED remain forbidden. These enforce
existing selector/query validation, current computed evidence and the reply cap
(plan lines 238-252, 264, 382-394 and 446-476). Ownership at brief lines 9-16 is
unchanged: the same seven paths, with test_bridge_runtime.py limited to its one
capability dictionary. No stylesheet, Clear or global-reset snapshot work enters
PR A.

Progress line 71 explicitly labels selector exceptions and dynamic-style
freshness gaps as possible, unconfirmed until public probes, with no runtime
acceptance. Line 73 limits CI evidence to the committed native corpus and
excludes pending runtime/URL edits. The forward implementation/review gate stays
open.

Decoded the complete saved f3-ci-jobs.json: run 37871320511 is completed/success
at exact HEAD, all 12 jobs and every recorded step are completed/success. Bounded
f3-quality.log evidence agrees: lines 2192/2194 show 883 Chromium tests in
638.806 s, OK with 16 skips; lines 2289/2291 show 51 Firefox canary tests in
104.213 s, OK without skips. The 16 skipped cases are 11 legacy installed-matrix
cases, host refusal outside that matrix and four React corpus cases awaiting
R2.7I's installed job. Frontend summary line 1216 shows 30/30, seven blocking
passes, no advisory failures/skips and 332 REPORT lines; independent line counts
agree. Read bounded action warnings and the final watch annotations: Node
deprecation/action runtime notices, future Ubuntu-image migration and macOS
capacity notices do not change these completed outcomes.

This follow-up read the document delta, relevant unchanged contract clauses,
saved job states and bounded log/watch evidence. It did not independently read
every REPORT detail or matrix test log, rerun CI, reproduce the source hypotheses
or inspect the changing writer code. The controller's full-log read and watch
process exit are controller evidence. No new test, browser, mutation, source
edit, gate, staging, commit or push ran; only this review append was written.
