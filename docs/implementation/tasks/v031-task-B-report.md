# 0.3.1 Task B report

Changed only checkout/setup-node action references in the two workflows.
Inputs, permissions, job ordering, triggers and environment approval are intact.

## Upstream evidence (2026-10-07)

- [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1):
  `3d3c42e5aac5ba805825da76410c181273ba90b1`.
- [setup-node v7.0.0](https://github.com/actions/setup-node/releases/tag/v7.0.0):
  `820762786026740c76f36085b0efc47a31fe5020`.
- GitHub API tag refs for both the exact release tag and floating v7 resolved
  to the listed commit. Both tagged action.yml files declare node24.
- Tagged READMEs require runner 2.327.1 or later. The hosted latest images used
  by these workflows will be checked by CI. Checkout's safer fork handling for
  pull_request_target/workflow_run does not affect the triggers used here.

## Evidence

Baseline `PYTHONPATH=tests python -m unittest test_release test_support`: 59
tests, OK, Chromium. Existing behavior characterized; no RED manufactured.
Post-change same command: 59 tests, OK, Python exit 0, Chromium.
Static/provenance, bridge syntax, `ruff check . --exclude .agents` and diff
whitespace pass. The exact Ruff limitation is recorded in the ledger.
Full runtime gates are skipped for this workflow-only diff; no new Firefox
claim. Independent review: Approved; its fresh release tests count 25.

## Self-review

AP14: local runtime gates are explicitly skipped; no new browser claim.
AP15: product CI intent belongs in the commit; execution detail stays here.
No trust boundary, source write, dependency or public UI change.
