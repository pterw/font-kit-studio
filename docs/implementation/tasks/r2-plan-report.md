# R2 work-order preparation report

Date: 2026-10-08. Branch: `docs/r2-engine-plan`; released base `1348268`.
Status: draft prepared and independently reviewed; final verdict **Approved**.
Final product-plan approval and audit evidence remain pending.

## Changes

The R2 outline now has binding proposed protocol/types/limits, canonical role
CSS, baseline detection, honest computed outcomes, route freshness and bounded
visited-page evidence. Owned fixtures/harness and staged bridge/Studio tasks
support three implementation PRs. The release point remains 0.4.0; role renaming,
pairing, exports, state format and inspector migration stay in later phases.

The separate Library/Composer audit has a concrete read-only brief. D058 records
the chosen draft thresholds. Current state and roadmap say planned/draft,
awaiting audit evidence and final approval; no engine code has changed.

## Source and self-review

Read the orientation documents and approved design. Current bridge/Studio,
browser helpers, fixture/workflow source and two complete read-only research
reports inform the contract. Graph Tier 2: font-kit-studio-local, generation
2026-10-07T17:07:14Z. Relevant source metadata changed; docs/fixtures are excluded.
Direct current-source reads supply the evidence; no graph completeness claim.

The ownership matrix, reply queue, host harness and capability expectations
avoid implementer stalls. Fixture baseline and integration stages complete
separately; successful existing behavior is characterized, never forced RED.
One writer per shared runtime file; disjoint code phases and serial landings.
Target author DOM round trips accompany computed styles; every new boundary
requires real Studio/bridge and hostile cases. No raw CSS, source writes,
automatic replay, third-party font request or unreviewed runtime change.

## Verification and remaining work

RED/GREEN and mutations: not applicable to a documentation-only draft.
New tests: 0; no browser engine verified. Full suites, frontend and Firefox
are not run for this change. Audit, plan approval and all R2 tasks remain open.

Fresh planning checks (2026-10-08):

| Command | Observed result |
|---|---|
| python scripts/verify.py --static-only | PASS: 96 unique IDs, one executable inline block, all three provenance hashes; browser acceptance explicitly SKIP |
| node --check fontkit-bridge.js | exit 0, no output |
| python -m ruff check . | FAIL: four existing untracked skill scan.py findings, F401 json/Set/re and F841 exclude_dirs_str |
| python -m ruff check . --exclude .agents | All checks passed!; separately disclosed product-tree gate |
| git diff --check | exit 0; LF/CRLF checkout warnings only |
| python scripts/dev/check_commit_messages.py --range origin/main..HEAD | commit-message check: OK: 1 commit checked (publication closeout before this landing) |
| python scripts/dev/check_commit_messages.py --message-file .superpowers/sdd/r2-plan/plan-message.txt | commit-message check: OK: message checked |
| python .superpowers/sdd/r2-plan/check-plan-docs.py | Existing relative links and all task headers resolve; no completed R2 task or placeholder |

Existing handshake/reset/integration class references also pass a direct AST
existence check. Raw command output is planning-gates.json in the ignored
workspace. [Final review](r2-plan-review.md#final-scoped-verdict-task-and-example-corrections)
is Approved; the entire dispatch report and scoped verdict were read before
landing. No browser test, engine implementation or audit is claimed here.

## Contract corrections

The first review identifies three missing binding semantics. The draft now
assigns authenticated ready identity and minimum scan freshness to R2.2;
separates immutable mutation receipts from post-commit measurement freshness;
and defines full author/style identity keys, Studio role IDs, per-route
contributions and whole-collection bounds. Target global reset also returns
the empty role snapshot to Studio. These are proposed work-order details,
not runtime fixes or additional approved implementation.
Follow-on task/example corrections remove the staged Studio completion cycle,
keep already-working scan cancellation as passing, and supply ready identity
plus a distinct fixture baseline in the protocol examples. All findings resolve.
