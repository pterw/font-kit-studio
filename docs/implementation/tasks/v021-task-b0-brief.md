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
