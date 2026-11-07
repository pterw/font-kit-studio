# Task 3 brief: correct the publication record's claim about files changed after d49158b

Plan task 3 (PUB), wave 1, mode code (docs only). BASE `5443ff6`, worktree `the task's worktree`. Audit row: `PUB`.
Line budget: about 4 gross lines changed in one file (Markdown, not counted by D065).

## Why

`docs/implementation/verification-r2.md:5-6` at BASE says `d49158b` is "the last product-code commit; only the
screenshot script changed after it". That is false. Between `d49158b` and the published `v0.4.0` (annotated tag on
`c006e6c`; product code identical to the gated tree `5e8af0f`, per lines 137-138) the product files Studio, bridge,
`scripts/serve.py` and the npm package changed. Re-read at BASE: the cause still holds, and the sentence is on lines 5-6
exactly. Lines 7 onward are right; do not touch them. A reader of the record would trust a tree they did not test.

## Owned files (exact)

- `docs/implementation/verification-r2.md`, lines 5-6 only (the sentence beginning "This evidence covers the settled PR C tree").

Everything else is read-only: no CHANGELOG line (no user notices a record fix), no `progress.md`, no `deviations.md`
(the controller owns them), no change to the audit file.

## Read first

- `docs/implementation/verification-r2.md` lines 1-8 and 135-140 at BASE (`git show 5443ff6:<path>`).
- Audit row `PUB` (`docs/implementation/audit-2026-11-06-real-apps.md:127`).
- Format model: `docs/implementation/tasks/v041-task-S1-brief.md`.

## Requirements

1. Measure first, from the repo, with `v0.4.0` as the published commit (the tag exists locally and `d49158b` is its ancestor):
   - `git diff --stat d49158b..v0.4.0 -- fontkit-bridge.js fontkit-studio.html scripts/serve.py packages`
   - `git log --oneline d49158b..v0.4.0 -- fontkit-bridge.js fontkit-studio.html scripts/serve.py packages | wc -l`

   Oracle: the command output, not the audit's 7/3/549. My run at BASE printed 8 commits, 4 files, 565 insertions(+),
   63 deletions(-) (the 4 files: `fontkit-bridge.js`, `fontkit-studio.html`, `packages/fontkitstudio/test/proxy.test.js`,
   `scripts/serve.py`). Re-run and use what it shows. The audit's 3 files / 549 is the same command without `packages`.
2. Reword the sentence so it states that later commits touched product files, the Python proxy `scripts/serve.py` among
   them, and gives the measured commit, file and insertion counts and the pathspec used. Keep "the release-point docs committed after it" and the whole-branch
   review round with final gates on `5e8af0f` meaning intact. Suggested text (adjust numbers to your measurement):

   > This evidence covers the settled PR C tree: the code at `d49158b`, plus the later product changes (8 commits touching 4 files,
   > 565 insertions, among them the Python proxy in `scripts/serve.py`; counted over `fontkit-bridge.js`, `fontkit-studio.html`,
   > `scripts/serve.py` and `packages` from `d49158b` to `v0.4.0`), the release-point docs committed after it, and the whole-branch review round
   > below, whose final gates ran on `5e8af0f`. Earlier R2 evidence: ...

   Keep the "Earlier R2 evidence" tail on line 7 unchanged; wrap near 120 columns as the file does. ASCII, LF endings.
3. Do not call `d49158b` "the last product-code commit" any more. Check with
   `git grep -n "last product-code commit" -- docs/implementation/verification-r2.md`: no hit in lines 1-8 afterwards.
   (Other files quote the audit's old wording in dated records; leave them.)

## Tests

None. Docs only, no test is added or changed. The change is checked by: (a) the report quoting the two commands and their
output verbatim; (b) `git diff --stat` showing one file, lines 5-6 region only; (c) `pre-commit run --files
docs/implementation/verification-r2.md` clean. No dev server, no gate run beyond what the code-phase rules require, no suite.

## Focused command

`cd the task's worktree && timeout 120 pre-commit run --files docs/implementation/verification-r2.md`

## Patches

Single-row task: return `task-3-code.patch`. Commit subject (72 characters or fewer):
`docs: correct which files changed after the last 0.4.0 product commit`
Body: one or two lines on why (later commits touched product files, counts re-measured). No CHANGELOG line.

## Open questions

- Which pathspec counts as "product files"? Options: (a) bridge, studio, `serve.py` and `packages`: 8 commits, 4 files,
  565 insertions; (b) the same without `packages`: 3 files, 549 insertions (the audit's figures; commit count differs by
  the test-only `packages` edit). Recommendation: (a), as the plan says, and state the pathspec in the sentence so the
  figure is reproducible.
- Which end commit? Recommendation: `v0.4.0` (the published commit; identical product code to `ffd2343` and `5e8af0f`).

## Controller rulings

1. Open question 1: include packages, as the plan says, and name the paths in the sentence so the counts can be reproduced.
2. Open question 2: the range ends at v0.4.0.

## Review fixes (binding: these govern over the text above)

1. You own lines 5-7, keeping the text from "Earlier R2 evidence" on unchanged. The `git diff --stat` check reads accordingly.
2. The sentence says "product and package-test files", because one of the four files is a package test. The Why section's "the npm package changed" means its test.
3. The edge-case check reads "no hit in the file".
