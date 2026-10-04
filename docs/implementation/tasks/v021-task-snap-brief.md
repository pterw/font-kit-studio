# v0.2.1 canvas snapshot race: brief and implementer report

Found by CI on PR #5 at `8cea6d5`. Implementer: Serif-2. Base: `8cea6d5`. Test-only.

## Problem

`test_studio_dead_controls.PresetSelectTests.test_apply_on_an_untouched_preset_says_there_is_nothing_to_reset`
failed once in CI: its canvas snapshots before and after Apply differed only in
`is-collapsed` and `grid-template-columns: 1fr`. Three other tests compare whole-canvas
markup the same way.

## Implementer report

Cause: Library is the default mode, so the Composer canvas first renders hidden at width 0
and every row starts collapsed; `switchMode("composer")` does not re-sync row layouts, and
the ResizeObserver expands them a frame later (`syncRowLayouts`). A raw `inner_html()`
snapshot taken in between differs from one taken after, with no change to the composition.
Only `is-collapsed` and the `grid-template-columns` inline style are width-derived.

Fix: `canvas_snapshot(page)` in `tests/support.py` clones `#composerCanvas`, strips the
width-derived class and style from the clone and returns its markup; ids, text and every
other style stay. All four sites use it (`test_studio_dead_controls`, `test_font_kit_studio_v011`,
two in `test_studio_live`). `CanvasSnapshotTest` (5 tests) proves a width change alone, and
showing the Composer, leave the snapshot equal, while a real re-render (new slot ids)
changes it; rows with different collapse widths and every preset are swept across seven
viewport widths. A guard test fails on a raw canvas-markup read in `tests/*.py`.

RED: with ResizeObserver callbacks held until the test's action, three of the four
unmodified sites fail with the CI signature (the fourth keeps its canvas hidden); four of
five helper tests fail against a raw-markup stub. GREEN: four of four sites and all helper
tests pass under the same stall; the originally failing test passes 30 of 30 at 1600 px and
at 390 px, and under six busy workers. Product mutations (a re-render on untouched Apply, late
validation after a render) still fail each site. Helper mutants (forgetting the class or the
style, stripping ids, returning nothing) each fail. `test_support test_studio_dead_controls
test_font_kit_studio_v011 test_studio_live`: 227 tests OK.

Accepted narrowing: a leak of canvas width alone is no longer caught by the snapshot; the
import tests still catch it through their `export()` assertions. Left for later: two
fixed sleeps before reading `is-collapsed` in `test_font_kit_studio_v011.py` (about lines 61
and 119).

## Review (2026-10-04)

Verdict: **Approved.** Root cause confirmed without any shim: the canvas is 0 px wide
while the Composer is hidden, `switchMode` does not re-sync row layouts, and the rows
expand only in the frame after the switch; the CI diff (+13 for ` is-collapsed`, -4 for
the track list) matches the earlier snapshot being the collapsed one. Under the hold model
the unpatched tests fail and the patched ones pass 80 of 80; under random ResizeObserver
jitter the unpatched tests fail 15 of 80 and the patched pass 80 of 80. A real re-render
(new slot ids) still fails the original test. Helper mutants are caught but for two. The
module-level `LiveCase` import adds no tests and leaks nothing (discover finds 780 unique
tests). `test_support test_studio_dead_controls test_font_kit_studio_v011 test_studio_live`:
227 tests OK.

Taken in a short follow-up: return the canvas's outer markup (`outerHTML`), so a leaked
canvas width is caught again at all three import sites; and widen the guard so any raw
`inner_html`, `outer_html` or `content` read, or an `innerHTML`/`outerHTML` evaluate,
outside the helper fails. Product-side alternative noted, not taken here: one
`syncRowLayouts()` call when the Composer is shown.
- Follow-up, closed by the controller on reading the diff: the snapshot is now the canvas's
  outer markup, so a leaked canvas width or colour changes it (a new test was RED with the
  inner markup) and the leak is caught again at all three import sites; the guard is an AST
  scan that fails any raw `inner_html`, `outer_html` or `content` read, and any
  `innerHTML`/`outerHTML` evaluate outside a target frame, in `tests/*.py` (0 today; 13
  flagged spellings tested); a new test pins the `selected` class in the snapshot.
  `test_support test_studio_dead_controls test_font_kit_studio_v011 test_studio_live`:
  232 tests OK.
