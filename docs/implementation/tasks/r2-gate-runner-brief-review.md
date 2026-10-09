# R2 PR A gate runner preparation review

Date: 2026-10-08
Verdict: Approved
Scope: brief preparation only; no gate execution or implementation acceptance.
Checkout: feat/r2-detection at 4aa264a9e38f17f897a93a3a8e99786a361c0900.

## Findings

No Critical, Important or Minor findings in this preparation scope.

- Brief lines 3-5 require committed R2.1/R2.2, independently accepted S1 and
  frozen integrated root product source before execution. Lines 14-16 require
  expected branch/HEAD/status and source hashes before and after the wave;
  unexpected changes invalidate the evidence. The runner is not authorized to
  start the full wave during the current focused implementation work.
- Brief lines 11-25 limit writes to verification-r2-pr-a.md and named ignored
  logs, preserve owner files, prohibit source fixes/staging/publication/spawning,
  and require existing pinned browsers and all five installed fixtures. Missing
  installs block before suites; FKS_REQUIRE_FIXTURES=1 prevents fixture skips
  from becoming acceptance. Ignored package rebundling and test-owned scratch
  creation/cleanup are permitted, with no tracked output changes. Cleanup is by
  owned PID/handle; a denied action is reported without a different-tool retry.
- Brief lines 29-45 and constraints lines 75-81/116-131 schedule sequential full
  Chromium halves once at the settled wave. Focused writer checks and independent
  behavior review stay separate. Only one identical suspected-flake rerun is
  allowed, with both outcomes retained; other failures return to the controller
  and same implementer. No full Firefox suite or browser downloads are allowed.
- Brief lines 36-52 retain static/provenance, syntax, product Ruff, both whitespace
  checks, commit range and actual candidate message, Node package tests, frontend
  chromium/firefox and advisory Firefox canary. The known four exact-Ruff skill
  findings remain disclosed; .agents is preserved and exact Ruff is not called
  passing. Frontend desktop Chromium blocks; all remaining profiles/engines,
  including the full planned 30-run wave's advisory and touch REPORT output,
  remain read and reported. A failed/unavailable advisory engine is not silently
  omitted or relabelled blocking.
- Brief lines 54-69 require full stdout/stderr, native exits, failures/skips,
  counts/times/engines, first complete detector benchmark and responsiveness,
  source stability and owned cleanup. Thresholds and retry restrictions stay
  fixed. The controller must read the complete report and material output before
  committing/pushing. Evidence is bound to the tested source, not a future
  commit or publication, and the runner cannot close plan/release tasks.
- Plan Addendum 6 (lines 160-170), its progress-table row and ledger line 81 record
  the execution-ownership steering before dispatch. They preserve focused and
  independent acceptance, product scope, thresholds and engines; no new deviation
  is introduced. The pending focused failure and next actions remain writer work.

## Dispatch prerequisites and limits

Approval does not authorize immediate execution. The controller must supply the
frozen expected HEAD, complete dirty/untracked product-source path/hash inventory,
actual candidate message and collision-free named scratch log paths at dispatch,
after the prerequisites above are satisfied. Fixture/browser availability and
the source manifest are checked by the future runner, not established here.

Read the full draft brief, current constraints, AGENTS.md and global rules;
read Addendum 6, its progress row, owned gate/scheduling clauses, Current state
and the latest relevant R2 steering records. No requested preparation section
remains unread. Earlier unrelated ledger history and changing implementation
source were not reviewed for acceptance. Parent graph coverage says docs/scratch
and the future verification file are excluded; direct documents decide this
review. No child MCP access, graph completeness or new structural claim is made.

No tests, gates, browsers, installs, source mutations, staging, commits, pushes
or spawning occurred. Only this preparation review was written. Existing CI and
focused evidence do not substitute for the future frozen-wave execution.
