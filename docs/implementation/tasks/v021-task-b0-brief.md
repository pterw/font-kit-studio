# v0.2.1 Task B0 brief: a late edit reply after an import

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task B0, addendum 2) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md`. Implementer: Kerning-B0. Base: `e3e07ef`.
Found in the re-review of Task 5 (`v021-task-5-review.md`, R1); it predates v0.2.1.

## Problem (Rule 6)

A user edit sent before an import and acknowledged after it overwrites the imported
override: saved state and the page both show the edit, for linked and unlinked imports.
Only composition and Reapply ops are marked `importSuperseded` (`endCompositionLink`,
`endRunningReapply`), so an ordinary `update` ack is still recorded by `recordCanonical`.

## Required

- `importCompositionJson` marks every in-flight and timed-out op `importSuperseded`, so a
  late acknowledgement or rejection only redoes the import's comparison with the page
  (the same path superseded composition and Reapply ops already use, including
  `handleReply` and `handleLateReply`).
- A queued user edit that the import drops is reported in the status, never dropped
  silently.
- If the page now differs from the imported state, the reconnect banner shows, as for the
  other superseded ops.

## Tests (append to `tests/test_studio_import_link.py`)

- Hold the page's reply, set a font size on `hero.lead`, import a file whose `overrides`
  set `hero.lead` to a different size, release the reply: saved state is the imported
  value; the banner shows because the page holds the edit; Reapply puts the imported value
  on the page. Linked and unlinked imports.
- A queued edit dropped by the import: the status says so.
- RED before the fix, GREEN after; one mutation per behaviour.

## Owned

Studio: `importCompositionJson`, `endCompositionLink`, `endRunningReapply`, the op
bookkeeping in `enqueueLiveOp`. `tests/test_studio_import_link.py` (append). Nothing else.

## Implementer report

Kerning-B0. Base `e3e07ef`. Changes left uncommitted.

### What changed

- `font_kit_studio_v0.1.1.html`: new `supersedeLiveOpsForImport()` (line 3050), called from
  `importCompositionJson` (3094) right after `endRunningReapply()` / `endCompositionLink()`. It marks every
  in-flight and timed-out op `importSuperseded` whatever its kind, drops the queue, and returns how many queued
  user edits (not Reapply, not composition) it dropped. The import status appends
  " N queued edit(s) that had not reached the page was/were dropped." (3119) only when N > 0.
  Existing superseded paths (`recordCanonical`, `handleReply`, `handleLateReply`, `reconcileAfterImport`) are
  unchanged and now also serve ordinary update, move, reset and restore ops.
- `endCompositionLink`, `endRunningReapply` and `enqueueLiveOp` needed no change.
- `tests/test_studio_import_link.py`: new class `LateEditReplyTests` (7 tests).

### RED then GREEN

RED (before the Studio change): 6 of 7 failed. Saved overrides were `{'hero.lead': {'fontSize': 21}}` instead of 30
(linked, unlinked, timed-out cases); the rejected edit was sent twice (2 != 1); both queued-edit status tests
failed on the missing sentence. The characterization test (no queued edits keeps the plain status) passed.
GREEN: `LateEditReplyTests` 7/7.

### Mutations (LateEditReplyTests, Chromium)

- M1 remove the supersede marking: 5 fail (linked ack, unlinked ack, timeout ack, rejected edit, queued-edit
  status test).
- M2 report 0 dropped edits: 2 fail (both status tests).
- M3 keep the queue: 1 fails (the queued edit is sent after the release).
File restored after each mutation (byte-identical to the fixed copy).

### Gates (Chromium only)

- `unittest test_studio_import_link test_studio_live test_live_integration`: 226 tests OK.
- `scripts/verify.py --static-only`: exit 0. `node --check fontkit-bridge.js`: exit 0.

### Not verified

Firefox, the full suite, the frontend gate and the commit-message check were not run. The queued-edit status
wording is mine; the brief gave none.

## Fix round 1

Verdict was Approved with fixes. Same worktree, uncommitted. All new tests are in `LateEditReplyTests`
(`tests/test_studio_import_link.py`), which now has 16 tests.

### Studio changes (font_kit_studio_v0.1.1.html)

- `supersedeLiveOpsForImport(replacesOverrides)` (line 3052): with no `live` field in the file it does nothing
  (only the composition and Reapply ops end, via `endCompositionLink` and `endRunningReapply`, as before). With
  one it marks every in-flight and timed-out op, drops the queue, and returns `{ dropped, sent }` where `sent` is the
  in-flight and timed-out user `update` ops. The queue filter has a comment saying it states intent (F4).
- `rememberSavedBeforeImport(sentEdits)` (line 3066): also remembers the non-null patch values of those sent edits in
  `live.importDropped.overrides`, so `reconcileImportedLinked` flags a page that still holds a value the import does
  not save.
- `importCompositionJson` (line 3105): passes `liveCandidate !== null`, then calls `rememberSavedBeforeImport` when
  linked.

### RED and GREEN per finding

- F1a (linked import with `overrides: {}`): RED before the change (no banner, edit left on the page); GREEN after.
  Banner shows, Reapply puts the page back, saved stays `{}`.
- F1b (import without `live`): RED for the linked case and for the queued edit (it was dropped); GREEN after: the edit
  is saved normally and nothing is dropped. The unlinked no-`live` test already passed before the change, because with
  nothing saved the first acknowledgement is adopted. I made it discriminating by saving a `hero.title` override first.
  Its RED is shown by mutation A.
- F2 (reset acknowledged, reset rejected, move): these characterize behaviour the first patch already had, so there is
  no RED against the code. Each fails under mutation C (only `update` ops marked).
- F3 (plural): new test with two queued edits (`hero.lead` line height, `hero.title` size) expects
  "2 queued edits that had not reached the page were dropped."
- F4: comment only.
- F5: both 200 ms waits are now commented as absence windows.

### Mutations (LateEditReplyTests, 16 tests, Chromium; file restored byte-identical)

- A supersede also without `live`: 3 fail (linked no-live, unlinked no-live, queued edit kept).
- B sent edits not remembered: 1 fails (empty-overrides banner test).
- C only `update` ops marked: 3 fail (reset ack, reset rejected, move).
- D no marking at all: 9 fail.
- E dropped count not reported: 3 fail (queued status linked and unlinked, plural).
- F queue not dropped: 1 fails (queued edit never sent).
- G plural wording: 1 fails.

### Unlinked path, as asked

An unlinked import compares in `reconcileSavedOverrides("import")`, which flags any difference between all saved
overrides and the page, so it needs no `importDropped` entry. One case differs. When the import leaves nothing saved
on any side (empty overrides, no tokens, no structure), that function adopts what the page acknowledges, the same
rule as a first connect, so the held edit is saved and no banner shows. This is pinned by
`test_an_unlinked_import_with_empty_overrides_after_a_held_edit` as a characterization. It is existing behaviour of a
function outside my scope; flag it if you want it changed.

### Gates (Chromium)

- `unittest test_studio_import_link test_studio_live test_live_integration`: 235 tests OK.
- `scripts/verify.py --static-only`: exit 0. `node --check fontkit-bridge.js`: exit 0.

### Not verified

The move test asserts the saved DOM order stays the imported one and that the page kept the move. It does not assert
whether the banner shows: `reconcileImportedLinked` only remembers saved DOM order, not sent moves, so I expect no
banner there (blind spot, not probed). Firefox, the full suite and the frontend gate were not run.

## Fix round 2

Same worktree, uncommitted. `LateEditReplyTests` now has 22 tests.

### Studio changes (font_kit_studio_v0.1.1.html)

- `recordCanonical` (line 3845): in the `importSuperseded` branch, when the latest import was linked
  (`live.importLinked`) and the op is a user `move` (not Reapply), it calls `rememberMoveHeldByPage(op, data)` before
  `reconcileAfterImport()`.
- New `rememberMoveHeldByPage(op, data)` (line 3908): reads the ledger the reply already refreshed and records the
  page's order in `live.importDropped`: for a css-order move the group's `order` values (same sources as
  `syncOrderFromLedger`), for a DOM move the touched containers' entries (`structureTouchedBy` over
  `savedStructureFrom(live.changes.structure)`). `reconcileImportedLinked` then flags it. Nothing else changed.

### RED and GREEN

- R1 RED before the change: 5 of 22 failed on "the page holds an order the import does not save" (DOM move banner,
  DOM move Reapply, CSS-order move banner, CSS-order move after a timeout, Accept after a CSS-order move). The rejected
  move test and the R2 same-target test passed (characterization). GREEN after: 22/22.
- Reapply after a late CSS-order move puts the saved order (none) back: the page's CSS order goes, saved overrides `{}`.
- Accept target state after a late CSS-order move adopts the page's order (4 `order` overrides). After a late DOM move
  it clears the banner and saves no DOM order (Accept never adopts a container only the page reordered).
- Reapply after a late DOM move clears the banner but moves nothing: with no saved DOM order there is nothing to put
  back, so the page keeps the moved order. Pinned by a characterization test; worth the owner's attention.
- Rejected move after an import: not sent again, page unchanged, no banner, no "Rejected" status. Timed-out move
  acknowledged late: banner shows (CSS-order case).
- R2: the same-target test (saved `lineHeight`, sent `fontSize` equal to what the import saves) passes and kills a
  "replace instead of merge" mutation. The null-patch test could not be written: Studio's own controls never send a
  null patch (only Reapply does, and those ops are excluded from `sent`), so the `value !== null` filter is not
  reachable from the UI and no black-box test can kill a mutation of it. Left as defensive code.
- R3: left as is, characterization test kept. R4: untouched. 300 ms wait near the old line 635 is now commented.

### Mutations (22 tests, Chromium; file restored byte-identical)

- A supersede also without live: 3 fail. B sent edits not remembered: 1 fails.
- C only update ops marked: 8 fail (reset, move acknowledged, rejected, timed out, Accept). D no marking: 14 fail.
- E count not reported: 3 fail. F queue not dropped: 1 fails. G plural: 1 fails.
- H moves not remembered (R1): 5 fail. I css-order branch skipped: 3 fail. J DOM branch skipped: 2 fail.
- K sent values replace instead of merge: 1 fails.

### Gates (Chromium)

- `unittest test_studio_import_link test_studio_live`: 198 tests OK (`test_studio_arrange` does not exist; the arrange
  tests are in `test_studio_live`). `test_live_integration` was not re-run this round.
- `scripts/verify.py --static-only`: exit 0. `node --check fontkit-bridge.js`: exit 0.

### Not verified

Real-bridge run of the move cases, text edits, Firefox, the frontend gate, the full suite, `test_live_integration` this
round.
