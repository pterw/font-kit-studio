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
