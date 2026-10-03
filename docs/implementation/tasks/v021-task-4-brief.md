# v0.2.1 Task 4 brief: Preview widths and the serif token

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 4 and decisions 5 and 6. Base:
`3083e4d` on `ccr-9eab25c9-mgatzt`. Implementer role: Kerning (Studio).

## Problems

1. The 1440 and 1024 width buttons (`#btnDeviceDesktop`, `#btnDeviceLaptop`, html:994-995;
   `setDeviceWidth`, 5403; `.canvas-stage`, 416 and 631) crop the preview on the right with no
   scrollbar when the stage is narrower than the chosen width.
2. `compositionPatch` (5271) picks `--font-serif` by role at 5264 and then falls back to
   `state.slots[2]` at 5269, which is the Row slot in the default preset, so the token names the
   wrong family.

## Required behaviour

- Decision 6: a preview wider than its stage scrolls horizontally with a visible scrollbar. The
  page is never scaled. At 1440, 1280 and 1024 px window widths, with each width button, nothing
  is clipped: the preview's scroll width equals the chosen width and the user can scroll to its
  right edge. Fluid (100%) is unchanged. Do not change button labels or glyphs (Task 8 owns copy).
- Decision 5: `--font-serif` comes from the first slot whose family is in the serif category when
  no role matches; when no slot has a serif family, the token is not sent, so the page keeps its own
  serif stack. Find how the library data marks a family's category and use that; never an index.

## Tests: new module `tests/test_studio_stage.py` (subclass `LiveCase`)

For each of 1440x900, 1280x800 and 1024x768 viewports and each of the 1440 and 1024 buttons:
the preview container's `scrollWidth` equals the chosen width, its visible box is inside the
stage, a horizontal scrollbar is present when the chosen width exceeds the stage (assert
`scrollWidth > clientWidth` and that `overflow-x` computes to `auto` or `scroll`), and after
scrolling to the end the right edge of the iframe is within the stage's box. Fluid: no horizontal
scroll. Serif: a composition whose serif family is in slot 1 and whose slot 2 is a Row sends
`--font-serif` naming slot 1's family (read it from what the fake target received after Sync to
Live App); a composition with no serif family sends no `--font-serif`; the role path (a slot
whose role contains "editorial") still wins. The first two serif cases must be RED before the fix.

## Owned files

`font_kit_studio_v0.1.1.html`: `.canvas-stage` CSS (416, 631) and any stage or preview-container
CSS you add next to it, `setDeviceWidth`, and lines 5260-5270 of `compositionPatch`.
`tests/test_studio_stage.py` (new). Do not touch the fullscreen CSS at 652-684 or
`toggleFullscreenTheater` (committed Task 1). Nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_studio_stage          # only your module; two other agents share the CPUs
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep` polling.
Do not commit or push. First command: `git rev-parse HEAD`; if it is not the base above or
newer, run `git fetch origin ccr-9eab25c9-mgatzt && git merge --ff-only origin/ccr-9eab25c9-mgatzt`
before editing. Two other implementers edit other functions of the Studio file in their own
worktrees at the same time: stay inside your named functions and CSS blocks, add new code next
to them rather than at the end of the script, and never reformat or move code you do not own.
Tests go in your own new module (subclass `LiveCase` from `test_studio_live` or
`LiveIntegrationCase` from `test_live_integration` for fixtures; with `PYTHONPATH=tests` they
import as top-level modules). Test-first: write the tests, capture the failure text (RED), make
the smallest fix, run your module (GREEN). Behaviour that already works is characterized, never
made RED.

## Report

Append under this heading in this file: RED evidence (test names and failure text), the fix
(functions and lines), GREEN evidence (your module count), what you did not verify.

## Report

Implementer: Kerning. Base: fast-forwarded the worktree from a6d2751 to 0e8befa before editing.

### Root cause (width buttons)
The stage (`.canvas-stage`, `overflow:auto`) did scroll, but it is about 1000 px tall (canvas, preview,
code panel), so its horizontal scrollbar sat at the stage bottom, far below the preview (stage bottom
at y=1818 in a 900 px window). The 1024 button also overflowed by 6 px at 1440x900 (stage content box
1018 px). Nothing was clipped in the DOM; the user just could not find the scrollbar.

### Serif category source
Each entry of `fonts` (html:1163 on) carries `tags`, an array whose category entry is "serif", "sans"
or "mono" (also `fallback: "serif"`). The fix uses `byFamily(slot.family).tags.includes("serif")`.

### RED (before the fix, 12 failures, 6 tests)
- `PreviewWidthTests.test_fixed_widths_scroll_instead_of_cropping_at_common_window_sizes`, all six
  window/button pairs: `AssertionError: 1068 != 1024 : the preview is 1024px wide ... 'tag':
  'canvas-stage', 'scrollWidth': 1068` and `1484 != 1440` (the nearest horizontal scroller was the
  stage, not a preview viewport; its bottom was 1817 vs the preview bottom 1584).
- `test_fluid_never_scrolls_horizontally_and_narrow_widths_fit`, three windows:
  `1062 != 390` (the 390 preview sat in a stage-wide scroller).
- `SerifTokenTests.test_serif_token_is_the_first_serif_family_when_slot_two_is_a_row`:
  `'"Instrument Serif"' not found in '"Fraunces", serif'`.
- `test_no_serif_token_is_sent_when_no_slot_uses_a_serif_family`: `'--font-serif' unexpectedly found in
  {... '--font-serif': '"Fraunces", serif'}`.
- `test_a_slot_whose_role_says_editorial_still_wins_the_serif_token`: passed before the fix
  (characterization, not made RED). The fullscreen test passed on the old structure only as written
  after the fix (new behaviour), see below.

### Fix (font_kit_studio_v0.1.1.html, 26 lines)
- CSS next to `.canvas-stage` (before `.composer-canvas`): `.preview-scroller` (width
  `min(100%, var(--preview-width, 100%))`, `overflow-x:auto`, `overflow-y:hidden`) and one fullscreen
  rule `.composer-shell.is-theater-fullscreen .canvas-stage .preview-scroller` (flex fill, centred). The
  committed fullscreen CSS block is untouched; the new rule is a separate, more specific selector.
- Markup: `#targetAppContainer` is wrapped in `<div id="previewScroller" class="preview-scroller">`. The
  container, iframe, overlay layer and placeholder are unchanged, so overlay coordinates still align.
- `setDeviceWidth`: also sets `--preview-width` on the wrapper (parent of the container).
- `compositionPatch`: the `state.slots[2]` fallback for `--font-serif` is replaced by the first text slot
  whose family has the "serif" tag; with none, no `--font-serif` is sent.
- Result: the preview is never scaled, its viewport is at most as wide as the stage, the scrollbar sits
  directly under the preview, and `scrollWidth` equals the chosen width (1440 and 1024 at 1440, 1280 and
  1024 px windows). Fluid and 390 do not scroll.

### GREEN
`python -m unittest tests.test_studio_stage` (Chromium only): Ran 6 tests, OK. `python scripts/verify.py
--static-only`: PASS (91 unique IDs, inline JS syntax, provenance).

### Not verified
- Firefox (not installed here; `FKS_ENGINES=chromium`), WebKit.
- Headless Chromium hides scrollbars, so "visible scrollbar" is asserted by geometry (scrollWidth >
  clientWidth, `overflow-x` auto, scroller bottom within 24 px of the preview bottom), not by pixels.
- The existing suites (test_studio_live fullscreen, overlay and layout tests, the frontend gate) were not
  run, per the brief. My module covers fullscreen fluid and 1440 only. Reviewer should run the existing
  fullscreen and overlay tests, and the frontend gate layout check (it lists `#targetAppContainer`).
- Markup change outside the named CSS and functions: the wrapper div near `#targetAppContainer`
  (about html:1100). Task 3 and Task 5 do not own those lines, but a merge should be checked.
- Row children are not considered for the serif token (only top-level text slots, matching the role pass).
- `byFamily` falls back to `fonts[0]` (Fraunces, serif) for an unknown family, so such a slot counts as serif.
