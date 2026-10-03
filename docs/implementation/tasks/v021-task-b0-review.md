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
