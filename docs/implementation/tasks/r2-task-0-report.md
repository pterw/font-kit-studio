# R2.0 report: approved work-order freeze

## Change

PR #18 merge `39ca945` is the fresh `feat/r2-detection` baseline. Addendum 3
records final engine work-order approval, freezes the existing protocol and
starts the planned PR A fixture phases. Roadmap status becomes active; D058's
unchanged threshold values become binding. R2.0 closes in this setup landing.
F1/F2a briefs assign disjoint owned files and rendered acceptance seams.
Execution constraints/checkpoint are local scratch; accepted records are durable.

## Evidence

- `python scripts/verify.py --static-only`: 96 unique IDs, executable inline
  syntax and three provenance blobs pass; unittest/browser explicitly skipped.
- `node --check fontkit-bridge.js`: exit 0.
- `python -m ruff check .`: four existing findings in preserved untracked
  .agents/skills/github-awesome-copilot-skills-acquire-codebase-knowledge/scripts/scan.py;
  this exact gate does not pass. Product-tree `--exclude .agents` passes.
- `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_support -v`:
  `Ran 34 tests in 19.242s`, `OK`. No new tests or feature RED/GREEN in setup.
- Whitespace and existing message range pass (0 commits); actual candidate
  message is checked at landing.
- Final audit head `3de7c0c` CI run 37863211400 passes all 12 jobs; no claim
  that those logs verify a future implementation. Full Python/Node/frontend
  and local Firefox were not rerun for this documentation-only change.

## Self-review and handoff

AP11/12: current approval copies reconcile; dated earlier events remain historical.
AP14: skipped gates/exact Ruff limitation named. AP15: history describes the
engine work order and its prerequisites; no model/session signatures. No code,
fixture, protocol field, release label or extra phase is added. No new deviation;
D058 status is updated conventionally. The [independent review](r2-task-0-review.md#final-scoped-verdict-2026-10-08)
is Approved after clarifying owned mutation targets and permanent local HTTPS
fallbacks. Its fresh support run passes 34 Chromium tests in 18.037s; constraints
are 7,438 bytes. The controller read the full verdict before the atomic landing.
Commit, push/new PR and F1/F2a dispatch follow landing checks.

Suggested subject: `docs: freeze the R2 detection work order`.
Why: the accepted fixture audit now supplies compatibility evidence, so the
approved engine contract and independent fixture phases can begin.
