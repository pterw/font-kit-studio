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
