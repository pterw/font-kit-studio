# v0.2.1 Task 4 review: Preview widths and the serif token

Reviewer: Leading. Brief and implementer report: `v021-task-4-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 4, decisions 5 and 6.
Scope: the uncommitted changes to `font_kit_studio_v0.1.1.html` (`.preview-scroller` CSS, the
`#previewScroller` wrapper, `setDeviceWidth`, the serif fallback in `compositionPatch`) and the
new `tests/test_studio_stage.py`, in the main tree at `0e8befa`.

## Verdict

**Verdict: Approved** (two non-blocking suggestions at the end; no fix is required to commit).

Method. The main tree now also holds the in-flight Task 3 and Task 5 edits to the same Studio file, so I
reproduced Task 4 alone: a scratch export of `0e8befa` plus exactly the Task 4 hunks (26 changed lines,
the same four places the implementer lists) plus `tests/test_studio_stage.py`. Gate results below come
from that isolated copy unless marked "main tree". All runs: Chromium only (`FKS_ENGINES=chromium`,
`/opt/pw-browsers/chromium`); Firefox and WebKit not installed here, not run.

### Gates

| Gate | Result |
|---|---|
| `python scripts/verify.py --static-only` (main tree and isolated copy) | PASS: 91 unique IDs, inline JS syntax, provenance |
| `python -m unittest tests.test_studio_stage` | Ran 6, OK (main tree and isolated copy) |
| `python -m unittest tests.test_studio_live`, isolated Task 4 copy | Ran 152, OK (overlay, pop-out, arrange and fullscreen tests pass with the wrapper) |
| `python -m unittest tests.test_studio_live`, main tree | Ran 152, 1 FAIL, see "Main-tree failure" |
| `python scripts/dev/frontend_gate.py --offline`, isolated copy | SUMMARY OK: 15 of 15 runs, blocking 7 (6 passed, 1 skipped), 0 advisory lines, 0 FAIL |
| `frontend_gate.py` without `--offline` | FAIL on "free fonts load" only: Google Fonts unreachable from this container. Not run online; not verified. |

Main-tree failure (not Task 4): `StudioCompositionFontTests.test_reapply_with_the_ask_sends_the_complete_set_so_a_sheet_only_a_slot_uses_stays`
(`tests/test_studio_live.py:4218`) fails deterministically (3 of 3 reruns) with `'Composition imported.' not found in
'Imported; the link to the page is off. Press Sync to Live App ...'`. That string is new in the working tree
(`font_kit_studio_v0.1.1.html:3080`, import-while-linked wording) and is absent from `HEAD`; it is the Task 5
(D035) change. The same module passes 152/152 on HEAD plus Task 4. The Task 5 owner has to update that test
or the wording. First run of the module in the main tree reported an error (a 7 s `wait_for_function`
timeout) instead; the rerun showed the same test failing, so that was load-related variance on top of it.

### (1) Decision 6: never scaled, scrollbar under the preview

Evidence is `tests/test_studio_stage.py` (six window/button pairs) plus my own browser probe
(`scratchpad/t4/tests/probe_overlay.py`, real Studio, real bridge, demo app, real `scripts/serve.py`).

| Window | Button | `#previewScroller` scrollWidth / clientWidth | Result |
|---|---|---|---|
| 1440x900 | 1440 | 1440 / 1018 | scrolls; right edge reached (scrollLeft 422) |
| 1440x900 | 1024 | 1024 / 1018 | scrolls 6 px; reached |
| 1280x800 | 1440 | 1440 / 858 | scrolls; reached (582) |
| 1280x800 | 1024 | 1024 / 858 | scrolls; reached (166) |
| 1024x768 | 1440 | 1440 / 946 | scrolls; reached (494) |
| 1024x768 | 1024 | 1024 / 946 | scrolls; reached (78) |
| any | Fluid | stage width / same | no scroll |
| any | 390 | 390 / 390 | no scroll |

- No transform or zoom anywhere in the diff: the container keeps `width: 1440px` or `1024px`, so inspector
  measurements still equal page measurements. The scroller is `min(100%, var(--preview-width))` wide, and its
  bottom edge is the preview's bottom edge, so the scrollbar sits directly under the preview (the old
  failure: the stage scrolled, its bar was at the stage bottom, y=1818 in a 900 px window).
- Fullscreen (`test_a_wide_preview_in_fullscreen_still_fills_the_height_and_scrolls`, 1280x800): fluid and
  1440 both fill the layer height (container taller than 500 px), 1440 scrolls, the box stays within 800 px,
  the right edge is reachable. The committed fullscreen CSS block is untouched; one new, more specific rule
  handles the wrapper.
- Screenshots in the scratchpad: `shots/win1280-btn1440.png` (selection and label drawn correctly over the
  scrolled-right preview, "Start free" button), `win1024-btn1024.png`, `win1440-btn1440.png`, `win1280-btn0.png`.
- Observation, not a defect: `overflow-x: auto` is implied by `overflow-y: hidden` (CSS computes the other axis
  to `auto`), so the explicit declaration is redundant but harmless and states the intent.

### (2) The wrapper: overlay alignment and the gate

- Overlay layer is `position:absolute; inset:0` inside `#targetAppContainer`, so it scrolls with the iframe by
  construction. Probe: scroll the preview fully right, hover then click the rightmost element in the demo, compare
  `#bridgeOverlayHover` and `#bridgeOverlaySelected` boxes with the element's box (iframe offset added), then scroll back to
  zero and compare again. Deviation 0.00 px in all three windows for 1440, 1024 and Fluid.
- 390 shows a constant 5.00 px deviation. It is pre-existing: the identical probe on a scratch copy of `HEAD`
  (no wrapper) gives the same 5.00 px at 390, so Task 4 did not cause it. Likely the demo's own mobile layout
  moving after the click (I did not chase it). It is outside this task; worth an audit line for a later task.
- The gate's `#targetAppContainer` mention is `HIDDEN_ON_LOAD` in `scripts/dev/_frontend_gate_layout.py:73`: it
  asserts the container computes `display: none` before a connect. The wrapper does not change what that
  measures (the container itself is still the element that is hidden), and the gate passes. It is not a
  width check, so it neither covers nor breaks the new behaviour; `check_no_horizontal_overflow` treats the new
  scroller as a clipping ancestor, which is correct. The gate never presses the 1440/1024 buttons, so only
  `tests/test_studio_stage.py` guards decision 6.

### (3) Decision 5: serif token

- Source is `fonts[].tags` ("serif", "sans" or "mono", one category per family; 5 serif, 8 sans, 3 mono entries
  at html:1187 on). Using it is right; it matches the decision text ("in the serif category") and no index
  remains: the `state.slots[2]` fallback is gone. Only top-level text slots are scanned, matching the role
  pass above it; the decision says "slot", and Row children are not a regression (the old code ignored them).
  Row children are not considered: acceptable, and worth one sentence in the ledger.
- Unknown family, `byFamily` returns `fonts[0]` (Fraunces, serif). Recommendation: keep it, do not special-case.
  Reasons: (a) Studio's own specimen renders that slot as Fraunces, and the display, sans and mono tokens
  already send `cssStack(byFamily(...))`, so a skip rule would make serif the only token that disagrees with
  what the user sees; (b) an unknown family is only reachable by a hand-edited import (legacy names are
  mapped by `LEGACY_FAMILIES`), and import normalization is the right place to reject it, not the token
  builder; (c) a skip rule adds a branch and a second definition of "unknown" (the Rule 8 and Rule 10
  direction is flat code). Cost if wrong: a hand-edited file with an unknown family before a real serif
  family would send Fraunces instead of the real one. Accepted.
- Test results: the first two serif tests were RED before the fix and I reproduced the RED by mutation (below);
  the role path test is characterization, correctly not made RED.

### (4) Test quality

Mutations on a scratch copy only (never the main tree; restored by `cmp` after each):

| Mutation | Stage module result |
|---|---|
| Drop only `overflow-x: auto` | Survives (6 OK): an equivalent mutant, `overflow-y: hidden` forces the x axis to `auto`. |
| Drop `overflow-x: auto` and `overflow-y: hidden` | Killed: `1462 != 1440`, `1062 != 1024`, `1062 != 390` (the nearest scroller falls back to the stage) across all windows, plus the fullscreen test. |
| `width: min(100%, var(--preview-width))` becomes `width: 100%` | Killed: `test_fluid_never_scrolls...` fails `1018 != 390` in all three windows (the 390 preview then sits in a stage-wide scroller). |
| Restore the `state.slots[2]` fallback | Killed: `'"Instrument Serif"' not found in '"Fraunces", serif'` and `'--font-serif' unexpectedly found`. |

- Hostile or edge cases for scroll are not trust-boundary cases, so no hostile requirement applies. The serif
  tests drive the real Studio's output as received by the fake bridge target (the Sync to Live App update); the
  real-Studio-against-real-bridge rule is met by the unchanged live integration suite and my probe, since the
  token path is Studio-side only.
- No new fixed sleeps in `test_studio_stage.py`; it relies on the shared `wait_connected` (existing 150 ms).
- Headless Chromium hides scrollbars, so the geometry proxy is right: `scrollWidth == chosen`,
  `scrollWidth > clientWidth`, computed `overflow-x` in (`auto`, `scroll`), scroller bottom within 24 px of the
  preview bottom (a visible bar adds about 15 px; the old bug put it ~230 px away), `scrollLeft > 0` after
  scrolling to the end, iframe right edge within the stage and the scroller. This would catch the original defect.

### Suggestions (not required for approval)

1. `tests/test_studio_stage.py:66-71`: the `else` branch ("a preview that fits does not scroll") is dead
   for the current matrix, because all six pairs exceed the stage. Either drop it or add a pair that fits
   (for example 1024 in a 1440 wide window with a collapsed inspector). Minor.
2. `README.md:231` (device buttons): add that a preview wider than the stage scrolls sideways and is never
   scaled. The sentence is not wrong today, so it is not a stale-doc defect (Anti-Pattern 11), only incomplete.
   Task 4 does not own the README; leave it to a docs pass.

### Not verified

Firefox and WebKit; the online free-fonts gate check; pixel-level scrollbar rendering (headless hides it);
the fullscreen layout on a real GPU window; interplay with Task 3 and Task 5 beyond the main-tree suite
failure listed above (the wrapper markup merged cleanly into the main tree).
