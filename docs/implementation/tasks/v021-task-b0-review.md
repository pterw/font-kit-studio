# v0.2.1 Task B0 review: a late edit reply after an import

Reviewer: Leading. Patch reviewed: the implementer's first round on `3468cac`
(new `supersedeLiveOpsForImport`, called from `importCompositionJson`; `LateEditReplyTests`, 7 tests).

## Verdict

**Approved with fixes.** The brief's own case (same target, different value) works, linked and
unlinked; the existing superseded paths in `recordCanonical`, `handleReply` and
`handleLateReply` handle every op kind unchanged.

## Findings

- **F1 (Rule 6, fix).** A linked import whose file does not save the edited target (`live`
  with empty overrides, or no `live` field) leaves the late-acknowledged edit on the page,
  unsaved, with no banner. The edit never reached `live.overrides`, so it is not in
  `live.importDropped`. Before the patch the linked empty-`live` case saved the edit, so this
  is a small regression. Ruling (controller): an import with `live` remembers superseded
  user `update` patches like saved values, so the banner flags them; an import without
  `live` does not replace overrides and supersedes only composition and Reapply ops.
- **F2 (test gap, fix).** Only `update` ops are tested; marking only `update` survives.
  Add a reset and a move held across an import, and a late rejected reset.
- **F3 (minor, fix).** Plural status wording is correct but untested.
- **F4 (note).** The drop filter in `supersedeLiveOpsForImport` never matches, because
  `endRunningReapply` and `endCompositionLink` remove those ops first. Kept with a comment.
- **F5 (minor, fix).** Two uncommented 200 ms waits in the new tests.

## Mutations

| Mutation | Result |
|---|---|
| Mark only `update` ops | survives (F2) |
| Count every queued op as dropped | survives (F4) |
| Mark only the in-flight op, not timed-out ones | killed (timeout test) |

Gates: `LateEditReplyTests` 7/7 and `test_studio_import_link` 31 tests OK (Chromium).
Not verified: Firefox, the full suite, the frontend gate, move and restore ops beyond the
reset probe, text edits, a Reapply running during an import with the new ordering.

## Re-review of fix round 1 (2026-10-03)

Verdict: **Approved with fixes.** F1 to F5 are addressed; gates pass
(`test_studio_import_link test_studio_live`: 192 tests OK on Chromium; static checks and
`node --check` exit 0). Firefox, the frontend gate and the full suite were not run.

- F1: fixed. Sent `update` ops are returned by `supersedeLiveOpsForImport` and remembered
  by `rememberSavedBeforeImport(sentEdits)`, so a linked import with `overrides: {}` shows
  the banner and Reapply reverts the page. An import without `live` no longer supersedes
  user edits; queued edits are kept.
- F2: reset (acknowledged and rejected) and move are tested. The move test does not assert
  the banner (R1 below).
- F3: plural wording asserted. F4: comment added. F5: both 200 ms waits commented; the
  300 ms wait near `tests/test_studio_import_link.py:635` is not (cosmetic).

Mutations (LateEditReplyTests, 16 tests): remembering null patch values too survives;
not merging sent values with already-remembered ones survives; remembering and marking
only the in-flight op is killed.

Findings:

- **R1 (Rule 6, blocking).** A linked import carrying `live` does not flag a move sent
  before it. Probed on `?arrange=1`: for both a DOM move and a CSS-order move, the page
  keeps the move, saved state is `{}`, and no banner shows. Before B0 the acknowledged move
  was saved, so this is the same shape as F1. Fix: in the `importSuperseded` branch of
  `recordCanonical`, when the composition was linked and the op is an acknowledged `move`,
  remember the page's resulting order (CSS `order` values for the siblings, or the
  container's structure entry) in `live.importDropped`, so `reconcileImportedLinked`
  flags it.
- **R2 (tests, optional).** Add a test that releases a property (null patch) before an
  import, and one with a saved override and a sent edit on the same target, so the two
  surviving mutations are killed.
- **R3 (recorded, not fixed here).** An unlinked import that saves nothing at all adopts a
  late acknowledged edit as saved, with no banner (`reconcileSavedOverrides` adopts when
  nothing is saved on any side, as on a first connect). Acceptable: the adopted value is the
  user's own edit and nothing is lost. The linked case now shows a banner, so the two
  paths differ. One rule would mean skipping the adopt-when-empty branch for
  `cause === "import"`.
- **R4 (pre-existing, recorded).** An unlinked import with non-empty saved state does not
  flag a DOM move the page holds, because `structureHeld` only checks that saved entries
  are held. The same holds on a plain reconnect.

Not verified: rejected and timed-out move paths, text edits, real-bridge runs of the new
cases, Firefox, the frontend gate, the full suite.

## Re-review of fix round 2 (2026-10-03)

Verdict: **Approved.** `test_studio_import_link test_studio_live test_live_integration`:
241 tests OK (Chromium); static checks and `node --check` pass.

- R1 fixed. `rememberMoveHeldByPage` (called from `recordCanonical` for a superseded user
  move after a linked import) reads the ledger the reply already refreshed: a CSS-order
  move remembers the sibling group's `order` values, a DOM move remembers only the touched
  containers. No false banner when the imported file already saves the resulting order
  (probed for both kinds). Reapply moves are skipped.
- R2 fixed for the same-target case. The null-patch test is not needed: only Reapply and
  font-stylesheet release send null values, and neither reaches `rememberSavedBeforeImport`.
- Reapply after a late DOM move clears the banner while the page keeps the moved order.
  Not a Rule 6 hole: nothing is overwritten on either side, and Reapply only replays saved
  DOM order (D020). The same happens before B0 when an imported file drops a saved DOM
  order. What is weak is the wording: `finishReapply` does not say the page still holds a
  DOM order Studio does not save. Follow-up, outside B0: name the container and suggest a
  reload, without failing the Reapply.

Surviving mutations (none blocking): dropping the `!op.reapply` guard (benign, the same
content is remembered elsewhere); dropping the `live.importLinked` guard; remembering only
the moved target's order; remembering every page container. The last two need page-only
reorders the test page cannot produce through the UI.

Not verified: Firefox, the frontend gate, the real bridge for the move cases, a late move
after an unlinked import, text edits.
