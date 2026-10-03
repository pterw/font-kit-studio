# v0.2.1 Task 1 review: Fullscreen exit

Reviewer: Leading. Brief and implementer report: `v021-task-1-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 1.
Scope: the uncommitted changes to `font_kit_studio_v0.1.1.html` (theater CSS, the Exit
button, `setTheaterInert`, `toggleFullscreenTheater`) and `tests/test_studio_live.py`
(`StudioFullscreenTests`) in the main tree at `5917f56`.

## Verdict

Verdict: **Approved with fixes** (three small fixes; none blocks the desktop behaviour the plan asks for).

Gates run (Chromium only, `FKS_ENGINES=chromium`; Firefox and `frontend_gate.py` not run):
`python scripts/verify.py --static-only` PASS; `-k Fullscreen` 3 tests OK; whole
`tests.test_studio_live` 151 tests OK (311 s).

### 1. Brief conformance: met

- Exit control: `#btnExitFullscreen` (html:1081) is the first child of `.composer-shell`, shown only under
  `.is-theater-fullscreen` (css 669-684), `position:absolute; z-index:2`, so it sits in the fixed theater layer.
  `elementFromPoint` at its centre returns the button at 1600, 1440, 1280, 1100 and 1024 wide.
- Click exits and selects nothing: covered by the test at test_studio_live.py:4361 (capture-phase click counter in
  the target frame stays 0, no `design:select`, no message at all reaches the target, badge unchanged).
- Covered toolbar `inert` in fullscreen and not after: test at :4392 (attribute, focus refusal, Tab loop, `[inert]`
  count 0 after exit). Esc: test at :4416. Label logic and the Esc handler are unchanged (html:5441, 5464).
- No connect, font-load or target messaging was touched (diff is CSS, one button, `setTheaterInert`, the toggle).

### 2. Robustness of `right: 372px` (html:677)

Probe (scratch, 1440x900 etc.; screenshots in the scratchpad `fs-*.png`):

| Viewport | Button box (x..right) | Inspector x | Hit at centre | Overlaps inspector | Off-screen |
|---|---|---|---|---|---|
| 1600x1200 | 1066..1228 | 1250 | Exit | no | no |
| 1440x900 | 906..1068 | 1090 | Exit | no | no |
| 1280x800 | 746..908 | 930 | Exit | no | no |
| 1100x800 | 566..728 | 750 | Exit | no | no |
| 1024x768 | 490..652 | 674 | Exit | no | no |
| 390x844 (advisory) | -144..18 | 40 | none (null) | no | **yes** |

- The 1100px breakpoint (css 619-621, `.composer-shell {grid-template-columns:1fr}`) does not move the button: the
  fullscreen rule uses `!important` and keeps the `1fr 340px` grid, so the 22px gap to the inspector holds down to
  1024. Between 1100 and 1024 the inspector rises from y=65 to y=10, and the button (y 18-48) is still left of it.
- Phone width: the 340px inspector leaves about 20px for the preview, so `right: 372px` puts the button 144px off
  the left edge. The Exit control is unreachable by pointer and touch (there is no Esc on a phone), and the
  focus-on-entry lands on an off-screen button. Before this change the phone user also had no exit (toggle covered),
  so this is not a regression, and phone is advisory (D029), but the stated goal is "always on top".
- Visual: the button floats over the top-right corner of the preview (about 160x30px) and hides whatever the target
  draws there (for example a login or menu button). Acceptable, but worth knowing.

### 3. `setTheaterInert` coverage

In fullscreen the inert set is exactly: `HEAD`, `HEADER`, `NAV.mode-nav`, `#libraryView`, `SECTION.composer-toolbar`,
`#exportDialog` (siblings of the shell, of `#composerView`'s inner wrapper and of `body`). The shell itself, the
inspector, canvas stage, reconnect banner, overlay layer, pop-out placeholder, live code panel and the target iframe
are not inert (the ancestors on the path, `.wrap`, `#composerView`, `BODY`, `HTML`, are not inert either).

- The bridge bar, status badge, Pop out, Select/Interact and device buttons live in `.composer-toolbar`, so they are
  inert in fullscreen. They are visually covered by the shell anyway, so nothing visible lost usability; the Select/
  Interact and device buttons were unusable by mouse in fullscreen before too. Not a defect, but record it: a screen
  reader loses the `aria-live` badge while fullscreen is on (Studio-side status changes are silent until exit).
- Nothing inert hides a path that must stay usable: `#exportDialog` can only be opened from toolbar buttons
  (`exportJson`/`exportCss`, html:3042-3043), so no modal opens while it is inert.
- Exit removes exactly what was set: author-set `inert` is skipped on entry and survives exit (probe: footer
  `inert` preserved); counts are 6, 6, 0 across enter/Esc/enter/Esc; Esc with focus inside `#slotInspector`
  (`liveFontFamily`) leaves 0 inert and focus on `#btnToggleFullscreen`. `setTheaterInert(false)` runs before the
  focus move, so the toggle is focusable when it receives focus.
- Nit: `HEAD` is marked inert because the loop climbs to `body` and marks its siblings. Harmless, but the climb could
  stop at `document.body`. Not required.
- Pre-existing, not in scope: Esc is a `window` keydown, so it does nothing while focus is inside the cross-origin
  preview iframe. The new Exit button is now the mouse way out in that state.

### 4. Test quality

Mutations on a scratch copy of the repo (`scratchpad/mut`, discarded; repo file diffed identical to the original):

| Mutation | Result |
|---|---|
| A: remove `setTheaterInert(isFull)` | inert test FAILS (`unexpectedly None`), others pass |
| B2: Exit `z-index: 2` to `-1` | click test FAILS (`elementFromPoint` check, `False is not true`); inert test errors |
| C: exit does not remove `inert` | Esc test FAILS (`6 != 0`) and inert test FAILS |
| D: Esc handler disabled | Esc test FAILS (`True is not false`) |
| B: `right:0; z-index:-1` | passes (see fix 1) |
| B3: `right: 340px` (button overlaps inspector column) | passes (see fix 1) |
| E: remove both `.focus()` handoffs | passes (see fix 2) |

- The 40-Tab loop is deterministic and meaningful: with inert disabled, Tab reaches the toolbar at press 16, well
  inside 40 (focusable count is fixed by the fake target, no selection). It would go vacuous only if the inspector
  grew past 40 stops before the toolbar; the `.focus()` refusal assertion backs it independently. No fixed sleeps
  in the new tests (the only one is the pre-existing 150 ms in `wait_connected`).
- The Esc test's final `enter` plus `assertTrue(is_fullscreen)` is a re-entry check; fine, not vacuous.
- Each new assertion fails without the fix (the Exit button does not exist before it; the inert attribute is absent
  before it). The "Esc exits" and `[inert]==0` assertions pass before the fix by design, and the brief says so.

### 5. Accessibility

- Accessible name is its text "Exit fullscreen (Esc)" (plus a title); a real `<button>`. Focus ring: the browser
  default `outline: auto` shows (`:focus-visible` matched, screenshot `fs-focus.png`); no site CSS removes it.
- Focus goes to the Exit button on entry and back to the toggle on exit (Esc and click paths both checked), which is
  sensible. This behaviour has no test (mutation E passes).
- The button is inside the shell, so a screen reader reaches it first in the fullscreen reading order.

### Fixes (each cheap, none changes the contract)

1. `font_kit_studio_v0.1.1.html:677` `right: 372px` assumes the 340px inspector column and breaks at phone width
   (button at x = -144 at 390px; no pointer or touch way out). Anchor it so it cannot leave the screen, for example
   `left: 18px` (top-left of the preview, away from the inspector at every width), or
   `right: max(372px, ...)`/`left: max(18px, ...)`. Add a test that, at 1024x768 and 390x844, the button's box lies
   inside the viewport and `elementFromPoint` at its centre is the button; at 1024x768 also assert its box does not
   intersect `#slotInspector`'s box (at 1600x1200 the button sits above the inspector's top, so the current test
   cannot detect an overlap: mutation B3 passes). Phone result may stay advisory per D029, but the fix is a
   one-line CSS change.
2. `font_kit_studio_v0.1.1.html:5448` and `:5451` (focus handoff) are untested. Add to
   `test_the_covered_toolbar_is_inert_in_fullscreen_and_live_again_after_exit` (test_studio_live.py:4392) an assertion
   that `document.activeElement.id` is `btnExitFullscreen` right after entry and `btnToggleFullscreen` after exit,
   and the same after Esc in `test_escape_still_exits_...` (:4416). Mutation E must then fail.
3. Optional nit, `font_kit_studio_v0.1.1.html:5426`: stop the ancestor walk at `document.body` so `<head>` is not
   marked inert. Covered by the existing `[inert]` count checks.

If fix 1 is not taken, record in the ledger that the Exit control is unreachable at phone width in fullscreen.
Not verified by me: Firefox, `frontend_gate.py`, other test modules, a real (non-fake) bridge target.

## Re-review

Reviewer: Leading. Scope: the three fixes from the first verdict, checked in the main tree at `f60bc19`
(uncommitted Studio file and `tests/test_studio_live.py`).

Verdict: **Approved**.

Gates: `python -m unittest tests.test_studio_live -k Fullscreen` runs 4 tests, OK (Chromium only; nothing wider
run, Firefox not run).

1. **Anchoring: fixed.** `font_kit_studio_v0.1.1.html:677` is `left: 18px`; the comment at 669-671 matches.
   `test_the_exit_control_stays_on_screen_and_clear_of_the_inspector_at_every_width` (1024x768 and 390x844) asserts the
   box is inside the viewport, `elementFromPoint` at the centre is the button, no intersection with `#slotInspector`
   at 1024, and a click exits. Mutations on a scratch copy (`scratchpad/mut2`, discarded; repo file diffed identical
   after):
   - B (`right:0; z-index:-1`): FAILS at both widths (`False is not true : a pointer finds the button`).
   - B3 (`right: 340px`): FAILS at 1024 (`button {x: 521.6...} must not overlap the inspector {x: 674, ...}`) and at
     390 (`-112.39 not greater than or equal to 0`).
   - Advisory, not a defect: at 390 the button (x 18..180, y 18..48) is on screen and wins the hit test, but it
     sits over the top-left of the inspector (x 40..380, y 10..367), covering part of the "Target App" title row. The
     test deliberately skips the overlap check below 1024. Acceptable under D029 (phone is advisory).
2. **Focus handoff: tested.** The inert test asserts `activeElement.id` is `btnExitFullscreen` after entry and
   `btnToggleFullscreen` after click-exit; the Esc test asserts both as well. Mutation E (both `.focus()` calls
   removed) FAILS in both tests (`'' != 'btnExitFullscreen'`).
3. **`<head>` not inert: fixed.** The walk at `:5426` is `node !== document.body`. The inert test asserts
   `document.head` has no `inert`; a mutation putting the walk back to `document.documentElement` FAILS that
   assertion (`<head> is not page content`). Probe at 1440x900, two enter/Esc rounds: the inert set is
   `HEADER, NAV, DIV#libraryView, SECTION (toolbar), DIALOG#exportDialog` on each entry and the count is 0 after
   each Esc.
4. **Nothing else changed in the Studio file.** The scratchpad `task1.patch` (html part) applied to `5917f56`, diffed
   against the current file, differs in exactly three lines: the CSS comment (671), `right: 372px` to `left: 18px`
   (677) and `document.documentElement` to `document.body` (5426). No sleeps were added to the new test.

Not verified: Firefox, `frontend_gate.py`, the wider suite, a real (non-fake) bridge target.
