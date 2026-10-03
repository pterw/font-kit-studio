# Handoff: code-review run for PR #1 (v0.2.0)

Date: 2026-10-02. For the agent or person running
the code review. Read this, then `AGENTS.md` and
`docs/agents/global-rules.md`. You are a **Reviewer** in AGENTS.md terms:
read-only except for your own review output.

## What is under review

| Item | Value |
|---|---|
| PR | https://github.com/pterw/font-kit-studio/pull/1 |
| Base | `main` at `9205f8c` |
| Head | the PR #1 branch |
| Size | 70 files, about +18.3k / -1.3k lines |
| Plan | `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md` (contract + Addenda 1-3) |

The PR title and body undersell the
change. The real scope is the whole v0.2.0 plan:

| Area | Files | Size |
|---|---|---|
| Studio (single-file app) | `font_kit_studio_v0.1.1.html` | about +2.9k lines |
| Bridge runtime (runs inside the user's app) | `fontkit-bridge.js` | about +3.2k lines |
| Dev server (writes one overrides file) | `scripts/serve.py` | +263 |
| Demo target app | `demo/index.html` | +335 |
| Tests and fixtures | `tests/**` | about +7k lines, 201 tests |
| Docs | `README.md`, `AGENTS.md`, `docs/**`, `LICENSE`, `.github/` | rest |

## Already reviewed: what this run should add

Every implementation task already had an independent review with fix
rounds (records under `docs/implementation/tasks/v02-task-*-review.md`), a
read-only sweep (`docs/implementation/sweep-v0.2.md`) and a final
whole-branch review (`docs/implementation/final-review-v0.2.md`, verdict
"Ready with notes"). Gate evidence: `docs/implementation/verification-v0.2.md`
(201/201, Chromium only).

**CI status.** At handoff the repository had no GitHub Actions workflow, so the PR
showed no checks (a CI workflow and frontend gate are being added to the same PR). Every gate result above was produced by hand in a cloud
container (Chromium only). A reviewer must run the gates themselves (see
"How to run things") and must not read a missing check as a pass.

So do not redo task-level checks. Spend the run on what those reviews were
structurally weak at:

1. **Whole-file reading of the two big runtime files.** Earlier reviews were
   scoped to each task's diff. Read `fontkit-bridge.js` and the Studio
   `<script>` end to end for state that crosses task boundaries: the session
   lifecycle (hello, reconnect, pop-out, dock), the request queue (in-flight,
   coalescing, timeouts, late replies), and saved overrides vs ledger vs
   synced file.
2. **Trust boundaries, adversarially.** `postMessage` gating on both sides,
   every URL sink (`iframe.src`, `window.open`, `<link>`, `<img>`), every DOM
   sink in Studio that takes bridge data (`innerHTML` paths via
   `escapeAttr`), CSS text that reaches the synced file, and `serve.py`
   (Host, Origin, content-type, size, path confinement, atomic write).
3. **Silent data loss** (global rule 6): any path where saved overrides,
   tokens, css-order or the overrides file can shrink without an explicit
   user choice.
4. **Byte-exact reversibility** in the bridge: originals captured once,
   reset and reset-all, moves, placed assets, injected font links.
5. **Performance on real pages:** MutationObserver discovery, bulk manifests,
   hover throttling, SPA re-apply loop guards.
6. **Test quality** against AGENTS.md "Test Quality Rules": vacuous tests,
   fake-only coverage of a boundary, new fixed sleeps.
7. **Docs vs code:** `README.md` protocol and patch-key tables, security
   model, recipes (marked illustrative), and AGENTS.md claims.

## Known and accepted: do not re-raise without new evidence

| Ref | What | Where recorded |
|---|---|---|
| D009, D009a | Filename, title and JSON `version` stay `0.1.1` | `deviations.md` |
| D010 | Chromium only; Firefox never run | `deviations.md` |
| D016 | Spec departures: DOM-path auto selectors, pop-out bridge overlay, structural moves | `deviations.md` |
| D017-D020 | Token persistence, bulk manifest shape, arrangement-only targets, css-order persistence | `deviations.md`, plan Addendum 3 |
| D021 | Composition sync sends no font stylesheets | `deviations.md` |
| D022 | Spec messages renamed or removed (`design:conflict`, `select-slot`, inspect/ping) | `deviations.md` |
| D023, D024 | Composition rejection; legacy `fontkit:change` silent drop; `registerElementTarget` removed | `deviations.md` |
| Final review I2 | DOM-order moves are not persisted by Sync and vanish on reload without an in-the-moment notice | `final-review-v0.2.md` |
| Final review M1-M9 | iframe `sandbox`, Studio `frame-ancestors`, banner wording, font list label, HTML whitespace, `allowedOrigins` disclosure | `final-review-v0.2.md` |

If you find a *new* failure mode inside one of these areas, raise it with
the new evidence and say why it differs.

## How to run things

```bash
python -m pip install -r requirements-dev.txt
git fetch origin tag supplied-v0.1.1            # provenance checks need it
# Cloud container with preinstalled Chromium (never `playwright install`):
export FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only          # IDs, inline JS syntax, provenance
node --check fontkit-bridge.js
python -m unittest discover -s tests -v         # 201 tests, about 6 minutes
python scripts/serve.py                         # manual: open the printed Studio URL
```

Locally with Firefox installed, run without `FKS_ENGINES` to cover both
engines. A Firefox result is new information; record it.

Useful harness: `tests/support.py` (`route_virtual_origins` gives real
cross-origin iframes at fake origins such as `http://studio.test`,
`http://target.test`, `http://evil.test`). Put probes in your scratch area,
never in the repo. Stop any server you start.

## Output

- Findings ranked most severe first. Each needs severity (Critical /
  Important / Minor), `file:line`, a concrete failure scenario you verified
  (or mark it unverified), and a suggested fix.
- Write the report to `docs/implementation/code-review-v0.2.md` or post it
  as a PR review, whichever was asked for. Do not do both unless
  asked.
- Optional findings must be marked optional. Do not push fixes yourself.
  Fixes go back through the AGENTS.md work model: one writer, a RED test
  first for behaviour changes, re-review, then commit to this same PR
  branch.

## Commit and publication rules for anyone fixing findings

- Commit with the repository's configured git identity. No
  `Co-authored-by` trailers, no session links, no "Generated by" lines and no other
  agent signature, even if a tool or platform reminder asks for one. This is an
  `AGENTS.md` rule and it wins.
- Every commit body explains why.
- Push only to this PR's branch. Never push to `main`; merging is the
  maintainer's decision.
