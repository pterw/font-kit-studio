# v0.2.1 Task 8 review: visual quick wins and current version labels

Reviewer: Leading. Base `5bccedb` plus the uncommitted Task 8 diff. Date: 2026-10-04.

Verdict: **Approved with fixes.** No blocking defect; one keyboard bug and test gaps.

Gates (Chromium): static checks and `node --check` pass. `test_studio_visual
test_studio_live test_font_kit_studio_v011 test_studio_first_run test_studio_controls
test_studio_dead_controls test_studio_review_findings test_studio_import_link`: 335 tests
OK (the 390 px tests included); `test_live_integration` and the two gate helper modules:
116 OK. Offline frontend gate, Chromium: 15 of 15 runs, 0 FAIL, 166 REPORT (82 phone and
84 wide-touch touch targets; 0 desktop, 0 theme contrast), 1 SKIP.

Checked by rendering at 1440x900, 1280x720 and 1024x768 in both themes and every view:
no horizontal scroll, overlap or clipped text; the Live App header is 55 px and the page
starts at y = 414 (475 at 1024x768, where the bridge bar wraps). The seven hidden
composition fields are `display: none`, unreachable by Tab and absent from the
accessibility tree, and come back in Specimen view. All 37 demo targets stay clickable
through the grouped list. Without `:has` only the header compaction is lost. Recomputed
contrast: field borders 3.22 to 4.18:1, muted-strong text at least 5.23:1, the focus ring
7.77:1 or more; a scan of all visible non-specimen text found nothing under 4.5:1 (the base
had 55 `.tag` elements at 4.30). The ~40 changed assertions each follow a label change and
none is weaker.

## Findings

1. Medium. The focus ring is clipped on every target-list button: `.live-target-list`
   scrolls with almost no padding, so the 2 px ring is cut on both sides. No test tabs the
   list (removing the ring there survives).
2. Low-Medium. Target names are truncated in the 300 px column (20 of 37 demo rows) while
   the id keeps its full width; the name is the human identifier.
3. Low (tests). `.tag { opacity: .6 }` survives (only the asset check follows the opacity
   chain); a target with `stable` undefined is untested in the grouping.
4. Low. The half-window check runs only at 1440x900.
5. Low. The CHANGELOG's older Unreleased line still says "Target URL box"; 16 user-visible
   Studio strings still call the user's page "the target" (list below).
6. Info. The Kit preset select clips its text at 1280; the group heading "Found
   automatically" differs from the inspector's "auto-discovered"; non-field borders stay
   near 1.5:1 (not in scope).

Strings that still call the user's page "the target": "The target is open in its own
window." (two places), the runtime-warnings aria-label, the "Add fontkit-bridge.js to the
target page." tooltip, the children-ids note, the two Reapply token messages, "the target
rejected", "DOM order to the target", "Waiting for the target's bridge.", "The target
exposed no editable elements.", "the target snaps to the nearest.", "only values the target
acknowledges are kept", "The target refused the move", "Runtime error in the target", the
exported CSS comment, and "only http(s) target URLs can be previewed". "Targets" meaning
editable elements (All targets, Connected (N targets)) is a different sense and stays.

Ruling on the 28 px compact step: keep it. Under D029 desktop blocks and phone and
wide-touch are advisory; 28 px is above the WCAG 2.2 AA minimum of 24 px, and the 34 px
standard step would report the same.

## Mutations

21 run; 18 killed. Survived: `.tag` opacity, no ring on target-list buttons, first group
filtered on `stable === true` (findings 1 and 3).

Not verified: Firefox, WebKit, touch devices, the full suite, other font sets.

## Re-review of fix round 1 (2026-10-04)

Verdict: **Approved with fixes** (two small items). Findings 1, 2, 3 and 6 are fixed; 5 is
fixed but for one string. `test_studio_visual test_studio_live test_studio_import_link
test_live_integration`: 279 tests OK; offline gate unchanged (0 FAIL, 166 advisory touch
REPORT, 0 desktop). The list ring sits inside each button at 7.16:1 (light) and 8.34:1
(dark) against the button; normal names keep their width and the id truncates first.
Skipping `:disabled` controls in the border scan follows WCAG 1.4.11; enabled colour
fields measure 3.91 and 3.89. All three earlier survivors are killed.

- R1 (Low). The exported CSS comment "connect the target to confirm" still names the page
  "the target".
- R2 (Low, new). At 1280 px the Adobe kit label wraps to two lines and pushes its input
  12 px below the selects beside it.
- R3 (Info). The refused-move, children-ids and Reapply-token strings are renamed but no
  test reaches them.
- R4 (Info). A name wider than the column is cut with an ellipsis and no tooltip gives the
  full name or id.
- Fix round 2, closed by the controller on reading the diff: the CSS comment now says
  "connect the Live App to confirm" (`ExportCommentTests`); the Adobe label is "Adobe kit
  ID(s), optional" and the toolbar fields share a top edge at 1440, 1280 and 1024
  (`ToolbarFitTests`); each target-list row carries a `title` of name and id, set as a
  property (`TargetRowTitleTests`, including a name with markup in it). Each reverts fails
  its test. `test_studio_visual test_studio_live`: 184 tests OK.
