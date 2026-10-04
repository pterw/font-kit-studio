# v0.2.1 Task 8 brief: visual quick wins and current version labels

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 8 and addendum 5) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md` (ownership). Source:
`docs/implementation/audit-2026-10-03-first-run-and-controls.md` ("P1: visual quick
wins"). Decision D039 (current version labels). Implementer: Kerning-8. Runs alone.

## Required

Visual (audit P1):

1. `.btn.primary` is styled as the one primary action in each area (at most one per panel).
2. One control-height scale for buttons, inputs and selects. Today they run from 26 to 45 px.
   `select` and `textarea` use `font: inherit`, so they stop rendering in 13 px Arial.
3. In the Live App view, fields that only affect the composition are hidden, and the header
   is compact, so the live page starts in the top half of a 900 px tall window. Today it
   starts at y = 865.
4. Inspector layout:
   - the breakpoint moves from 1100 to 900 px;
   - the column is 300 px wide, with a bounded height that scrolls;
   - the target list (2,400 px today) is bounded and grouped.
5. `:focus-visible` rings on every control. Today inputs set `outline: none`.
6. Contrast:
   - field borders reach at least 3:1;
   - `.tag`, placeholders and `.asset-placeholder` reach at least 4.5:1.
7. Copy:
   - one name for the user's page, "Live App", everywhere it is visible (today Target App,
     Live App and Live Target all appear);
   - no emoji in the bridge bar;
   - one glyph per action (`⛶` means both Fluid and Fullscreen today).
8. Carried over from the Task 6 review:
   - the Select and Interact buttons look disabled when they are (`.bridge-mode`
     `:disabled` style);
   - the Sync to file hint is set apart from the Auto-sync label.

Version labels (addendum 5, D039):

9. Studio's `<title>` and its eyebrow read `v0.2.1`.
10. Four user-facing messages name v0.1.1 as if it were the current version:
    - "Rows cannot contain rows in v0.1.1."
    - "Session-local in v0.1.1."
    - "Asset rejected: v0.1.1 accepts PNG and SVG only."
    - "Image assets must be reselected in v0.1.1."

    Each states its limit without a version.
11. Code-comment headers that call a block "v0.1.1" or "v0.2.0" name the version that
    introduced the block, for example "added in v0.2.0". None claims to be the current
    version.
12. The following stay as they are (D039):
    - the file name `font_kit_studio_v0.1.1.html`;
    - the export format `"version":"0.1.1"`;
    - every test, URL and doc that names the file.

## Owned

- In Studio (`font_kit_studio_v0.1.1.html`):
  - the `<style>` block;
  - visible labels, titles and messages;
  - the bridge-bar glyphs;
  - class attributes in the markup;
  - the one line in the existing view switch that sets a view class on a container, if
    item 3 needs it;
  - the four messages and the comment headers in items 10 and 11.
- `scripts/dev/_frontend_gate_*.py`: only when a threshold must move, and every change is
  reported with a reason. Never weaken a check silently.
- A new test module, `tests/test_studio_visual.py`.
- `CHANGELOG.md`: lines under Unreleased for every change a user notices (AGENTS.md,
  "Versions and releases").
- Existing tests that assert old labels, titles or "v0.1.1": change only those
  assertions, and list each one with the reason (the D033 precedent).

Must not touch:
- control-state logic (`refreshControlStates`, `setDisabledReason`);
- message handlers;
- persistence;
- the bridge;
- `README.md` (Task 9 owns it, along with the screenshots).

## Tests (`tests/test_studio_visual.py`, new)

The tests assert what the user sees: computed style, geometry, contrast ratios and text.
- A focus test tabs through the inspector and the bridge bar, and asserts a visible ring at
  each stop.
- A geometry test at 1440 x 900 asserts the live page's top is in the top half of the
  window in the Live App view.
- Contrast tests compute ratios from computed colours for `.tag`, placeholders,
  `.asset-placeholder` and field borders.
- One test checks the title and eyebrow text, and that none of the four messages contains
  "v0.1.1".

Name your RED tests before writing code.

## Gates

- `python scripts/verify.py --static-only`
- `node --check fontkit-bridge.js`
- `PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python -m unittest test_studio_visual test_studio_live test_font_kit_studio_v011 test_studio_first_run test_studio_controls test_studio_dead_controls -v`
- The offline frontend gate, desktop Chromium at 1440, 1280 and 1024:
  `FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python scripts/dev/frontend_gate.py`
  with whatever flags it offers to limit engines. Read its help first. Report the FAIL
  and REPORT counts before and after.
- The 390 px tests in `test_font_kit_studio_v011` must still pass. The product is
  desktop-first (D029), but those tests block.

## Report

Append "## Implementer report" to your worktree copy of this brief. Include:
- RED and GREEN per item;
- one mutation per item;
- frontend gate counts before and after;
- every existing assertion you changed, with the reason;
- the CHANGELOG lines you added;
- the final `git diff --stat`;
- what you did not verify.

## Implementer report

Implementer: Kerning-8. Base 5bccedb. Nothing committed. Owned files touched: Studio, `CHANGELOG.md`,
`tests/test_studio_visual.py` (new), and the existing assertions listed below. No gate script, bridge,
handler or persistence code changed.

### RED and GREEN, with one mutation per item

All 23 tests in `tests/test_studio_visual.py` were RED on 5bccedb (23 failures, for the reasons named
below), and are GREEN now. Each mutation below was applied alone to Studio, the named test failed
(KILLED), and the file was restored.

| Item | RED (before) | Mutation (killed) |
|---|---|---|
| 1 primary | `PrimaryActionTests`: the only primary in the bridge bar was Fullscreen; Library had none; `.btn.primary` had no fill | removed the fill; Fullscreen made primary again |
| 2 scale, font | `ControlScaleTests` (heights 26-45 px); `LiveAppControlScaleTests`; select/textarea were Arial 13.3px | standard step 40px; select/textarea lose `font: inherit` |
| 3 live view | top at 864.95; `#slotCount` visible; header 304px | removed `.composition-only` hide; removed `.deck` hide; never set `is-live-view` |
| 4 inspector | width 330; beside-preview test failed; `overflow-y: visible`; list 2,296px, ungrouped | breakpoint back to 1100; 330px; unbounded inspector; unbounded list; no groups |
| 5 focus | `outline: none` on fields; no ring on the stops | removed the global ring; `outline: none` back on text fields |
| 6 contrast | borders 1.34:1; `.tag` 4.30; asset placeholder 2.12 | border back to `--line`; `.tag` back to `--muted`; placeholder opacity .6; asset opacity .55 |
| 7 copy | "Target Application Bridge", "Target App"; emoji in the bar | old label; old inspector heading; emoji on 1440; same glyph on Fluid and Fullscreen |
| 8 carried over | Select/Interact opacity 1; hint above the Auto-sync row's bottom | removed `:disabled` style; hint back in the flex row |
| 9 title, eyebrow | `v0.1.1` | each put back |
| 10 messages | all four named v0.1.1 | rows message; import message put back (same test covers the four) |
| 11 comment headers | 4 headers claimed a version | "Font Kit Studio v0.1.1 - Flow Composer" put back |

Measured after: the live page top is at y = 414 (was 865) at 1440 x 900; header 55px (was 304);
inspector 300px wide; target list 360px max, two groups (12 marked, 25 found automatically).

### Frontend gate (Chromium only, `--offline`)

- Before (5bccedb, 1280 profile): 15 of 15 runs, 0 FAIL, 140 REPORT (2 theme contrast + 138 touch
  targets), 1 SKIP.
- After at 1440x900, 1280x720 and 1024x768 (desktop profile overridden by a scratch runner,
  `k8_gate_vp.py`): 15 of 15 runs, 0 FAIL, 166 REPORT, 1 SKIP at each width.
- The theme-contrast REPORTs are gone. The +26 REPORTs are all advisory touch targets (mobile 67 -> 82,
  wide touch 71 -> 84): the 28px compact step is under 44px. Not fixed (desktop-first, D029).
- The gate has only the 1280 desktop profile. "Before" at 1440 and 1024 was not run.
- Not changed: `scripts/dev/_frontend_gate_*.py` (no threshold moved).

### Test runs

- Brief's six-module command: 277 tests OK (before the last label fixes, rerun OK).
- Full `discover -s tests`, Chromium: 765 tests; 4 failures from my "live app" wording in
  `test_studio_review_findings`, fixed; that module then passes (12 tests). I did not re-run the whole
  suite after that one-line fix.
- `verify.py --static-only` passes; `node --check fontkit-bridge.js` passes.

### Existing assertions changed (all because a visible label changed)

- `test_font_kit_studio_v011.py`: the title assertion `v0.1.1` -> `v0.2.1` and its message (D039).
- `test_studio_first_run.py` (7): "Connect Target" -> "Connect Live App" (6, incl. the hint text);
  "Invalid target URL" -> "Invalid Live App URL" (1).
- `test_studio_live.py` (17): "Invalid target URL" (3), "No response from target" -> "...from the Live
  App" (4), "Target reconnected." -> "Live App reconnected." (2), "Imported state differs from the target."
  (2), "the live target has/holds" (5), "Accept target state" (3).
- `test_studio_import_link.py` (9): "No response from target" (4), "Imported state differs..." (2),
  "Accept target state" (2), "Composition imported. Image assets must be reselected in v0.1.1." (1).
- `test_live_integration.py` (4): "the live target has/holds" (3), "Accept target state" (1).
- `test_studio_review_findings.py` (3): "Composition sent to the live app." -> "...Live App."
- No `inspector_target` /regex/ wait broke.

### CHANGELOG lines (under Unreleased)

Changed: title/eyebrow v0.2.1 and version-free limits; one name "Live App"; one primary per panel and two
control heights; Live App view hides composition-only fields and shrinks the header; inspector 300px to
900px, bounded, grouped list; bridge bar without emoji, Select/Interact disabled look, Sync hint on its
own line. Fixed: focus rings; contrast (borders 3:1; tags, placeholders, asset placeholder 4.5:1).

### Judgement calls to confirm

- "Live App" rename covers the names and labels that call the page Target App, Live Target or Connect
  Target, plus the messages that contain them. Generic prose that says "the target" (about 25 strings,
  for example "The target refused the move", "Runtime error in the target", "Add fontkit-bridge.js to
  the target page") is unchanged. `?target=` (query parameter) and the gate's "Live Target inspector"
  section label are unchanged.
- Only the seven canvas fields are hidden in the Live App view (slots, canvas width, colour source,
  custom background, Tailwind family, shade, saved colour). Composition preset, Apply preset, Export/
  Import JSON, Export CSS, Load free fonts and Sync to Live App stay: existing real-bridge tests drive
  them in that view.
- Added: `.btn.active` border (the selected device button had no style), compact 28px step via CSS
  variables, `.slot-mini-btn` is now 28px, style chips and filter pills are 28px, the 1100 breakpoint
  split (toolbar rules stay at 1100, inspector rules move to 900).
- The ring is drawn against the panel around a control (outline offset), so the test measures it there.

### Not verified

- Firefox and the phone/touch layouts beyond the existing 390px tests and the advisory gate runs.
- The "before" gate at 1440 and 1024.
- Free-fonts load check (offline `--offline`).
- Real-font rendering: the live-page top (414) has about 36px of margin on this machine's fonts; another
  font set could wrap the two status lines.
- Visual review was by screenshots I looked at (light, dark, 390px), not by the owner.

### Fix round 1 (review: Approved with fixes)

- Finding 1: `.row-child-jump:focus-visible { outline-offset: -2px }` draws the ring inside the list buttons.
  New test tabs every target in the list (37) and checks the ring box lies inside each scrolling ancestor.
- Finding 2: the row grid is `minmax(0, max-content) minmax(0, 1fr)`: the name keeps its width, the id
  truncates first. New tests: all demo names fully visible; Composer row-child names fully visible.
- Finding 3: `.tag`, placeholder and field-border contrast now use the opacity chain (disabled controls are
  exempt). New grouping test posts a manifest entry without `stable`: it joins the marked group.
- Finding 5: 16 strings now say "the Live App" (pop-out text in markup and JS, runtime-warnings aria-label,
  bridge tooltip, children-ids note, two Reapply token reasons, "the Live App rejected", "DOM order to the
  Live App", "Waiting for the Live App's bridge.", "The Live App exposed no editable elements.", weights note,
  "only values the Live App acknowledges", "The Live App refused the move", "Runtime error in the Live App",
  exported CSS comment "skipped: the Live App reported no safe selector", "only http(s) Live App URLs").
  CHANGELOG "Target URL box" is now "Live App URL box". New `PageNameTests` scan shown and hidden text in
  five states for the user's page called "the target".
- Finding 6: Kit preset and Adobe kit ID fields are both `span-3` (the select no longer clips at 1280 or 1024;
  `ToolbarFitTests` measures it). Group heading is "Auto-discovered", matching the inspector note, the CSS
  export comment and the docs. The inspector note's wording is unchanged.
