# Library and Composer audit brief

Date: 2026-10-08. Status: **complete; independently reviewed**.
Plan: [R2 prerequisites](../../plans/2026-10-03-r2-engine.md#r20-approve-prerequisites-and-freeze-the-work-order).
Baseline: published 0.3.1 at `13482685faff7519459804335ad54cfdc4f8dc0f`.
Use the current planning HEAD if only reviewed documentation has changed.

Execution branch: `docs/library-composer-audit`, from merged work-order PR #17
at `142aa9dc0273efc19e14a67d88f66726b6d665ae`. Approval and audit progress are
recorded in the [ledger](../progress.md#r2-engine-planning). No runtime changes.
Evidence acceptance: [final review](r2-task-audit-review.md#final-scoped-verdict-2026-10-08).

## Goal and scope

Audit the released Library and specimen Composer in a real browser. Inventory
every reachable state, capture evidence and identify rough, confusing or missing
behavior against [product direction](../../roadmap/product-direction.md) and
the [approved typography design](../../specs/2026-10-03-typography-system-design.md).
It informs R2 acceptance and R3's Composer work; it implements neither.

Read the earlier pattern, [first-run audit](../audit-2026-10-03-first-run-and-controls.md),
in full, plus this brief, R2 scope and global rules. Follow AGENTS roles and
test-quality rules. Start at the page's visible entry points and follow all
Library/Composer buttons, links, fields, menus and dialogs; do not use guessed
DOM states as evidence that a user can reach them.

## Ownership and setup

- Sole writable tracked output: `docs/implementation/audit-2026-10-08-library-composer.md`.
  Date the observations when performed; this filename identifies this work order.
- Raw screenshots, rendered measurements and commands:
  `.superpowers/sdd/r2-audit/`; list every screenshot path in the report.
- Use Chromium desktop and narrow phone viewport for the state inventory;
  targeted Firefox checks are advisory only when a relevant engine difference
  needs investigation. Do not run the full suite or download browsers.
- Run the existing localhost server with OS-assigned ports, using a fresh
  browser context. Use available agent-browser automation after reading its skill.
  Stop only the server/browser processes started for this task, by PID.
- Block external HTTPS. Use existing local demo or bundled fonts where possible.
  A blocked Google/Adobe request is a disclosed offline limit, not an app defect.
  Never enter credentials or make a third-party request for this audit.

The controller supplies actual branch/HEAD, graph project/generation, coverage
and source fallbacks at dispatch. The audit writes only its report and raw
scratch evidence. It does not edit runtime, docs, plans, decisions or the ledger;
commit, push, spawn, merge or request an external review. A denied tool call is
reported, never retried through a different tool. Other work may exist in the
checkout; never revert or appropriate it.

## State inventory and evidence

- Library: initial state, category/search/filter combinations, an empty result,
  all available list/detail layouts, local font preview controls and their visible
  changed result, selected family, keyboard navigation and reachable dialogs.
- Composer: initial/empty and populated state, each preset/layout, each slot
  kind, add/remove/reorder, numeric edits with real typing, responsive/overflow
  controls, specimen/preview, import success/refusal, output/export and Changes
  panel. Show the existing Changes-panel gap accurately; no proposed output UI.
- Shared: Library-to-Composer transitions, persistence/reload where available,
  first-run prompts, disabled controls/reasons, focus order, visible focus,
  contrast and desktop/phone clipping. Inspect rendered state and computed styles.
- If another reachable state is discovered, add it to the inventory and capture
  it; do not limit coverage to this initial list. If a listed state is absent,
  record absent rather than faking it. Every unvisited state carries a reason.

For each state, give its user-visible route, viewport, action sequence, screenshot
and observation. A finding includes reproducible steps, expected/actual rendered
behavior, severity, evidence and whether it is confirmed or limited by setup.
Separate existing behavior from future-design gaps. Group proposed work into R2,
R3, later or already covered by an existing task, with the relevant plan/spec link.
Do not turn aesthetic preference into a confirmed defect.

## Report and acceptance

The report contains baseline/commands/engine versions, complete state inventory,
findings ranked by severity, screenshots/measurements, external-request and
skipped-state limits, and recommendations with their phase ownership. It ends
with cleanup evidence and explicit residual coverage gaps. No "all states"
claim is allowed while reachable states remain unchecked.

Return a short dispatch summary and exact report path. The controller reads the
entire report, obtains independent scope/evidence review, updates the ledger and
any approved plan addendum, then commits the audited record atomically. Audit
findings do not authorize fixes or enlarge the engine's scope.
