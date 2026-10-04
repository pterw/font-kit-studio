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
