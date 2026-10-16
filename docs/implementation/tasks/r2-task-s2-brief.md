# R2.S2 brief: Studio role preview controls

Plan: [R2 plan](../../plans/2026-10-03-r2-engine.md) R2.S2, the binding
protocol contract, Addenda 5, 7, 9, 10, 11 and 12, and D061-D063. PR B, branch
`feat/r2-role-preview`. Read the COMPLETE binding contract, the
[R2.3 brief](r2-task-3-brief.md) with its additions, the
[S1 brief](r2-task-s1-brief.md), [report](r2-task-s1-report.md) and
[review](r2-task-s1-review.md), the execution constraints, and the Studio
sections named below before editing.

The task runs in two code phases by one Studio writer:

- **Phase 1** (now, BASE `aa48c52`, bridge is R2.2): everything testable with
  the fake peer in `tests/test_studio_roles.py` and with the real R2.2 bridge
  for capability gating. Write Studio against the frozen contract.
- **Phase 2** (after R2.3 lands; the controller supplies the new BASE with the
  phase 1 patch applied): real Studio/bridge cases in
  `tests/test_r2_integration.py` that need the R2.3 bridge. Phase 2's BASE
  contains R2.3; if R2.5 has landed by then it contains R2.5 too, and the
  dispatch says which. Most real-bridge cases will be characterization GREEN
  once phase 1 exists; say so rather than manufacturing RED. Landing needs
  R2.5 and R2.7F2b committed, per the plan.

## Exact ownership

Own `fontkit-studio.html`, `tests/test_studio_roles.py` and
`tests/test_r2_integration.py`. Everything else is read-only; a missing seam
returns NEEDS_CONTEXT naming it. Existing fullscreen tests stay unchanged. In
`test_r2_integration.py` remove the leftover `print` (line 31 at BASE) and the
screenshot written to an absolute path (line 148); screenshots are scratch
evidence outside committed test code. Every new test method gets a short
Given/When/Then docstring; existing tests in the two owned modules may gain
one where the audit lists them.

## S1 surface to build on (checked at BASE)

`roleView` (state; add accepted/draft state beside it, not inside
`pending`), `ROLE_UNSUPPORTED`, `ROLE_UNAVAILABLE`, `ROLE_REASONS`, validators
`roleText`, `roleCount`, `exactRoleFields`, `safeRoleWire`, `validRoleURL`,
`validRoleSelector`, `validRoleStyle`, `roleIdentityKey`; flow
`resetRoleSession`, `acceptRoleReady`, `renderDetectedRoles`,
`acceptDetectedRoles`, `rejectRoleDetect`; transport `sendDesignMessage`,
`acceptBridgeMessage`, `BRIDGE_TYPES`; queue `enqueueLiveOp`,
`pumpLiveQueue`, `dispatchLiveOp`, `handleReply`, `handleLateReply`,
`supersedeLiveOpsForImport`, `scheduleAutoSync`; DOM `#detectedRoles`,
`#detectTextStyles`, `#roleStatus`, `#roleRows`; helper `setDisabledReason`
with `data-hint-for` hints; numeric rules in `canonicalLiveValue`. Detailed
line references: `.superpowers/sdd/r2/s2-reconcile-memo.md` section a
(untracked: the dispatch gives its absolute root path, as for the audit).

Known S1 limits S2 must close:
1. `acceptRoleReady` accepts only the empty snapshot. A same-document
   re-hello after Apply carries accepted roles; accept a valid non-empty
   snapshot (exact RoleInput shapes, `cssHash` equal to FNV-1a32 of the
   UTF-8 `canonicalCss`, at most 128 KiB) as acknowledged state, with a
   newer-revision guard like the existing pageVersion guard. Never send it
   back. An invalid ready keeps S1's behavior (unsupported, Detect disabled)
   and the previously shown preview is marked unconfirmed, not silently
   kept as acknowledged.
2. `BRIDGE_TYPES` lacks `design:roles-applied`; add it. Leave
   `design:roles-page` out (PR C) and test that it changes nothing.
3. `dispatchLiveOp` ends in a `restore-text` fallback. New op kinds get
   explicit branches before it.
4. `renderDetectedRoles` rebuilds the list on each call. Draft inputs must
   keep focus and typed text across renders: keep drafts in a map keyed by
   issued `role-N` with exactly the lifetime of `roleView.ids`.

## Controls (inside `#detectedRoles` only; Addendum 7/D062)

Per detected row: an enabled checkbox, a family-stack text field, numeric
fields for size, weight, line height and tracking, and a text-transform
select. All start empty and unchecked; observed values appear only as
placeholders. Accepted roles seed their drafts (enabled, with accepted values)
so a later Detect does not silently drop them. An enabled role needs at least
one valid property. A typed but invalid field, or an enabled invalid row
beside valid ones, disables Apply with a visible reason naming the row and
field; a field is never silently dropped (the bridge rejects whole requests).

Validation mirrors the contract: family trimmed 1-300 characters, passes
`CSS.supports('font-family', value)`, balanced quotes, none of `; { } < >`
backslash, line breaks, comment markers, `url(`, `expression(`,
`!important`; fontSize 4-400 (2 dp), fontWeight 1-1000 integer, lineHeight
0.5-5 (3 dp), letterSpacing -0.5-2 em (4 dp), the four transforms. Do not
widen `canonicalLiveValue`; write a role-specific family check. Bounds: 128
roles, 32 selectors per role from the row's own bindings, name 200, id 100,
request 256 KiB UTF-8.

Apply selected roles is enabled only when the bridge advertises
`roleStylesheet`, identity is current with a non-null pageURL, no selected row
has `bindingComplete:false`, at least one role is enabled and valid, and the
128-ID collection limit has not been reached (a state flag with the lifetime
of `roleView.ids`, not the transient status text; its hint says the limit is
reached, since Clear visited pages is PR C). Each disabled state shows its reason in a
visible hint, not only a title. A bridge with `roleDetection` but no
`roleStylesheet` keeps Detect and shows `This bridge does not support role
preview.` for Apply and Clear. Apply sends `adapter:'plain'` only (R2.4 adds
others) and replaces the whole accepted set; its status names accepted roles
the new set removes. Clear preview is enabled when `roleStylesheet` is
advertised and identity is authenticated, including with a null URL. Detect
stays enabled while a role op is queued. Detection and editing never apply,
clear or replay anything.

**Reset all page edits** (Addendum 12): one explicit control inside
`#detectedRoles`, after the preview block. It is enabled whenever a ready
session exists, whether or not the legacy ledger has edits (a role preview
alone is enough; do not gate it on `ledgerEmpty()`). Pressing it shows a
`window.confirm`, like the preset replacement at `fontkit-studio.html:2475`,
whose text says it removes every live edit on the page (inspector edits,
text, moves, tokens and the role preview) and, when auto-sync is on, that
the synced overrides file will be rewritten without them; when sync is off,
that the next Sync writes the emptied state. Dismissing sends nothing.
Accepting enqueues one untargeted `design:reset`. No new write path.

Today `acceptApplied` has a half-built untargeted branch
(`fontkit-studio.html:4293-4297`) that only clears `live.overrides`. Finish
it: overrides, saved DOM order (`live.structure`), CSS-order state and
saved tokens end consistent with the emptied ledger, so no reconnect or
structure conflict banner appears. On the authenticated `design:applied`
with a valid empty `roleState` (pageURL may be null, Addendum 5), the
visible role preview clears and the accepted revision moves to the reply's.
If the ack has no or an invalid `roleState`, keep the preview shown and mark
it unconfirmed. It never runs on reconnect, import or any implicit path.
Clear preview, reset-all, a valid ready snapshot or a new document are the
only acknowledgements that change the shown preview.

The preview block has the exact heading `Role preview; file output comes
later`, a `pre` showing acknowledged `canonicalCss` (focusable, overflow auto
so the 390 px panel stays within width), and its own status region
(`role=status`, accessible name "Role preview status") separate from
`#roleStatus`. Detect rows are labelled as the page baseline measured without
the role preview. Role CSS never enters Copy, Download, JSON export or Sync:
assert those outputs are byte-identical before and after Apply.

## Queue and receipts

Role ops are queue kinds `roles-apply` and `roles-clear` in `live.queue`.
Roles and `documentId` are frozen at the click; `pageVersion` (from
`roleView.identity`) and `baseRevision` are read at dispatch. If the current
`documentId` differs at dispatch (a reload while the op waited), drop the op
with a visible status and send nothing: a new document needs an explicit
Apply. Role ops are
barriers for update coalescing and survive imports: not cleared from the
queue, not counted as dropped edits, and not marked `importSuperseded` when
in flight or timed out. A `design:roles-applied` settles only an in-flight or
timed-out role op with the same requestId and matching `operation`; a
`design:applied` never settles a role op and a receipt never settles a legacy
op; `design:detected` settles nothing. Role rejections go to a role handler:
no automatic retry (including revision-conflict), accepted preview and drafts
unchanged, reason shown as text with the next step for `page-changed` and
`revision-conflict`; a validated rejection raises `live.revision` like
settlement does. A receipt that fails validation is ignored: the op stays in
flight until it times out, and no state changes. Role settlement never writes `live.changes`, overrides,
tokens, structure or exports; it raises `live.revision` only upward, and when
the queue empties it calls `scheduleAutoSync()` so a skipped auto-sync is not
lost. A late receipt for a timed-out role op is still accepted when session,
document and operation match.

Accept a receipt only when the source, origin, session and protocol are
current; the whole reply is at most 1 MiB (`safeRoleWire`); keys are exactly
the contract's; `hashAlgorithm` is `fnv1a32`; `documentId` equals the sent and
current document; `pageVersion` equals the sent one; `currentPageVersion >=
pageVersion`; `revision` equals the op's `baseRevision + 1` (the controller pinned
with R2.3 that every accepted apply and clear bumps once, including a
repeated clear and `roles:[]`; phase 2 confirms it in the R2.3 report and
returns NEEDS_CONTEXT if it differs);
roles are valid RoleInputs whose ids equal the sent ids in order;
`canonicalCss` is at most 128 KiB with a matching FNV-1a32 `cssHash`
(Studio checks hash, size and shapes; it does not re-serialize CSS);
outcomes have exact RoleOutcome keys (including `complete`), unique ids
drawn from roles, `0 <= mismatched <= checked <= matched`, loss counts >= 1,
`losses[].property` one of the six RoleInput keys, the seven loss reasons,
and `winningSelector` null or a valid selector. Complete outcomes require
current version and URL equal to the captured ones and a non-null URL (the
captured URL is the `pageURL` in the identity the op was dispatched with;
the receipt has no captured URL field);
`page-changed` requires `outcomesComplete:false` and `outcomes:[]`;
`budget-exceeded` shows the true checked counts labelled incomplete and is
invalid with a null or changed URL; clear returns empty roles/CSS/outcomes
with `outcomesComplete:true` and `outcomeReason:null`, and may carry a null
URL (Addendum 5). A valid receipt advances `roleView.identity` from
`currentPageVersion`/`currentPageURL`, nondecreasing; a null URL makes the
identity's pageURL null (Detect/Apply disabled) while the preview stays. A
valid stale receipt installs the accepted state and shows exactly `Preview
applied; page changed before checks finished`. Nothing downgrades a newer
accepted revision or page generation, and nothing marks a route checked.
An inspector override that wins shows as a counted mismatch with the reason
the bridge reports, rendered from the receipt (before R2.5 that is
`complex-cascade`; R2.5 refines it to `inline`). Tests assert the count and
that the displayed reason equals the receipt's, not a hard-coded value.

Under Addendum 11 a native hover or an inspector edit no longer advances
pageVersion, so Apply after inspecting and a Clear queued behind an
inspector edit are expected to succeed against the R2.3 bridge.

## Tests

Phase 1 (fake peer and current bridge):
- Fix the audit's Studio findings in owned files
  (`.superpowers/sdd/r2/test-quality-audit.md`, I-S1 to I-S3, I-I1, M-S1 to
  M-S3): the fake `PEER` records every inbound message type and tests assert
  exactly which messages Studio sent; size limits use multi-byte selectors and
  oversize replies built from valid fields (1 MiB - 1 accepted shape, 1 MiB +
  1 rejected); add the missing Studio selector negatives; drop the always-true
  `assertIn('Body', snapshot)`; name the failing shape in the corruption test.
- Draft controls by keystrokes with intermediate values, validation bounds,
  focus survival across a Detect, disabled reasons, request shape and size,
  queue order and operation matching both ways, complete/stale/budget/
  null-URL/clear receipts, every hostile receipt and ready case listed in the
  memo section e, timeout and late receipt, no retry, import interplay,
  exports unchanged, text-only rendering, auto-sync re-arm, the reset-all
  control and its wording, accessibility (names, focus, status, contrast,
  390 px overflow), and real Studio with the R2.2 bridge showing Apply/Clear
  disabled with the reason while Detect still works.
- A reload while a role op is queued sends no roles-apply to the new
  document (the peer records none) and shows the dropped-op status.
- Auto-sync re-arm and the "Sync body unchanged by Apply" check need a sync
  endpoint: build it in-module with route interception; if that is too
  heavy, state the gap in the report.
- Phase 1 genuine RED: real Studio has no Apply control. Fake-peer GREEN.

Phase 2 (real R2.3 bridge): Apply by keystrokes renders 24px on
`[data-design-role="Body"]` while `[data-design-id="ordinary.body"]` stays
16px; Clear restores author `main` outerHTML and computed styles; replace,
repeat and idempotent clear; a real post-commit rerender gives the stale
status then a queued inspector edit and Clear both settle (use the
frame-wait or page-listener technique the R2.3 report confirms; otherwise
delay the receipt in the fake peer and say so); target-only reset
keeps the preview; reset-all clears it after its empty roleState
(confirm dismissed sends no reset; accepted sends exactly one); an inspector
edit made before Apply survives Apply and Clear and its winning override
appears as a counted mismatch with the receipt's reason; CSP
`stylesheet-blocked` keeps the previous preview; real 2,001-character URL and
valid-to-unsupported cases; Detect after Apply shows the baseline; ready
after re-hello shows the accepted snapshot. Repeat S1's fullscreen regression
with S2 controls populated: preview height above 500 px in fluid and fixed
1440 widths, `#detectedRoles` inert, preview and observations unchanged after
Escape, one restored placement mutation fails it.

One restored foreground mutation per new guard (operation match, receipt
identity/revision, hash check, null-URL rules, document check at dispatch, text-only rendering, drafts
surviving render, coalescing barrier, no ledger writes, plain-only adapter,
reset-all wording path). Never remove an assertion to make a mutation pass.
Studio markup is read through text, status and `data-role-id`, never raw
Studio innerHTML (test_support's guard).

## Focused gates

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v
python -m unittest test_studio_live.StudioProtocolTests test_studio_live.StudioReviewFixTests test_studio_live.StudioFixRound1Tests test_studio_stage.PreviewWidthTests test_studio_live.StudioFullscreenTests test_studio_first_run.FullscreenTests test_studio_visual.LiveAppViewTests -v
python scripts/verify.py --static-only
python -m ruff check tests/test_studio_roles.py tests/test_r2_integration.py
git diff --check
```

The frontend gate, full suites and the advisory Firefox canary run at the
settled wave.

## Report and done

Each phase returns the three-path patch and a full report: RED/GREEN with
commands and output, the audit items done, mutation outcomes, accessibility
and layout evidence, characterization of per-element reset persistence, and
cleanup. The Handoff drafts the CHANGELOG line, ledger event and commit
why-body; the controller owns shared files. No stage, commit, push or spawn.
A denied tool call is reported, never retried through a different tool. Done
means every new request and reply has real Studio/bridge rendered coverage as
well as hostile fake-peer cases, exports and legacy behavior are unchanged,
and no R3 pairing UI or new persistence is added.
