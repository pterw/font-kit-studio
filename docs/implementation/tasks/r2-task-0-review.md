# R2.0 independent review: execution work-order freeze

Date: 2026-10-08. Final verdict: **Approved**.
Initial verdict: Approved with fixes; scoped resolution is recorded below.
Reviewed branch: `feat/r2-detection`; BASE/HEAD:
`39ca9457dd119e8bc43b97c6b41dbaf1d1a50740`.

## Initial scope and findings

Review covers the uncommitted R2.0 documentation setup, complete task-0 brief
and report, complete execution constraints/checkpoint, complete approved plan,
changed roadmap/decisions/current ledger and complete F1/F2a briefs. It does
not reopen the accepted product design or Library/Composer audit.

Critical: none. Important: two brief clarifications below. Minor: none.

1. **Important: name an owned missing-install mutation seam.**
   `docs/implementation/tasks/r2-task-f2a-brief.md:47-58` requires the existing
   `fixture_support.require_fixture` fail-closed behavior and a mutation that
   removes the missing-install condition, while lines 11-14 prohibit shared
   harness changes. The condition itself currently lives in
   `tests/fixture_support.py:14-23`, outside this writer's ownership. The
   mutation target is therefore unresolved, rather than permission to edit
   that helper. Before dispatch, specify mutation of an owned startup wrapper
   or equivalent local seam in `tests/test_r2_react.py`; exercise the real
   imported helper against a missing fixture with `FKS_REQUIRE_FIXTURES=1`.
   Its existing behavior is a passing characterization. Preserve shared
   helper bytes and assert the startup outcome, rather than deleting an
   assertion or manufacturing feature RED.

2. **Important: keep local interception active when mutating HTTPS guards.**
   `docs/implementation/tasks/r2-task-f2a-brief.md:51-58` calls for a local
   canary and guard removal, but does not require a separate fallback that
   survives removal of the regex guard. F1's corresponding canary at
   `docs/implementation/tasks/r2-task-f1-brief.md:58-72` is also subject to
   the constraints' per-guard mutation requirement. A normally intercepted
   HTTPS canary alone does not prove that the mutation cannot contact its
   URL when interception is deliberately removed. Before dispatch, require
   an earlier local-fulfillment fallback route in the disposable canary
   context, followed by the regex guard; keep the fallback active throughout
   mutation and distinguish its hit from a guard hit. Restrict mutations to
   the owned test module, restore it precisely, and never navigate the app
   page to the canary. This clarifies D059 without expanding product scope.

## Confirmed setup properties

- The binding protocol body matches BASE after only its two approval-wording
  replacements. Threshold values, messages, limits, ownership, three PRs and
  release scope are unchanged.
- Exactly four checkboxes are closed, all under R2.0. Later fixture/runtime,
  installed-CI and release checkboxes remain open. R2.0 closure describes
  this reviewed work-order landing; review, commit and dispatch are still
  explicitly pending. It is not evidence of a future commit or CI run.
- Current plan/roadmap/D058/ledger approval status agrees. Earlier dated
  draft/audit addenda and events remain historical records.
- F1 and F2a exact file lists are disjoint and agree with their plan tasks.
  Unknown-version scratch variants use F1-owned source. Existing BS5 vendor
  bytes and hero semantics are protected. F2a does not own workflow/canary
  integration or later role-preview acceptance.
- Both briefs require literal rendered oracles, computed styles, real
  keystrokes/state replacement, source HMR, genuine new-behavior RED, passing
  existing characterizations and restored foreground mutations. F1 keeps
  threshold/nested cases within the same 5,000-parent/20-tuple corpus and
  defers the actual detector budget to R2.2. F2a preserves compiler uncertainty
  and does not claim React Fast Refresh.

## Fresh verification

- `python scripts/verify.py --static-only`: exit 0; 96 unique IDs, one inline
  executable block and all three provenance blobs pass. Browser suite SKIP
  is explicit.
- `node --check fontkit-bridge.js`: exit 0.
- `python -m ruff check .`: exit 1; the same four preserved untracked-skill
  findings in `scan.py` at lines 21, 23, 24 and 294.
- `python -m ruff check . --exclude .agents`: exit 0, All checks passed.
- `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_support -v`:
  Ran 34 tests in 18.037s, OK; process completed with exit 0.
- Both working and staged whitespace checks pass. Existing message range:
  OK, 0 commits checked. Candidate message remains a controller landing check.
- A read-only script checked 71 local Markdown link paths across the changed
  documents and new briefs/report: none missing. It also compared the binding
  body with BASE and verified that only R2.0 has closed checkboxes.

Full Python suites, Node package tests, frontend gate and Firefox canary were
not rerun for this documentation-only review. Earlier hosted CI in the report
is historical evidence, not independently fetched or future-head verification.

Tier 2 graph project `font-kit-studio-local` is ready at generation
`2026-10-07T17:07:14Z`. Coverage checks identify docs/fixtures/workspace as
excluded and relevant existing source metadata as changed without recorded
ranges. Direct current documents and the relevant fixture-support/Vite startup
source establish this bounded review; no graph completeness claim is made.

## Handoff

Clarify the two mutation instructions, then obtain scoped re-review before
the controller's work-order commit and fixture dispatch. No code or fixture
implementation defect is claimed. Only this review file was written; no
staging, commit, push, remote review or other-file edit was performed.

## Final scoped verdict (2026-10-08)

**Approved.** Both Important findings are resolved; no Critical, Important or
Minor finding remains in this R2.0 setup scope.

Re-read both fixture briefs and execution constraints in full after the
controller's clarification. F2a now identifies only its owned HTTPS-abort
guard as the guard mutation target, and treats the existing shared
`require_fixture` missing-install behavior as GREEN characterization.
There is no new wrapper, shared-helper mutation or manufactured RED.

Both briefs and constraints now require an earlier locally fulfilling HTTPS
fallback to remain installed during canary and guard mutations. The later
abort guard has its own intercept count; removing it fails that assertion
while the fallback still handles the request locally. The canary remains
separate from app loading. This is an execution clarification within approved
D059 and existing owned files, without a product/contract/split change.

Constraints size is 7,438 bytes, below 8,192 bytes. Branch/HEAD remain the
reviewed BASE, and fresh whitespace checks pass after clarification. No source
changed, so the completed fast checks and 34-test Chromium support run above
were not repeated. The controller may land the reviewed work order after its
candidate-message and landing checks, then dispatch the named fixture writers
from the committed prerequisites. No future commit or CI success is asserted.

## Bookkeeping closure (2026-10-08)

**Approved.** Read the final task-0 report handoff and new ledger event
`R2.0 work order reviewed`. Both agree with the scoped verdict and completed
34-test Chromium support run (18.037s); the report records the verified
7,438-byte constraints size. The review link resolves to the existing scoped
verdict. Exact Ruff limitations and skipped gates remain explicit. Commit,
push, draft PR and fixture dispatch are next actions, not claimed successes.
No new scope, ruling, source change or remaining finding follows; completed
verification above remains applicable without another gate or browser run.
