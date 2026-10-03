# v0.2.1 Task 1 brief: Fullscreen exit

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 1. Base: `d3a37e9` on
`ccr-9eab25c9-mgatzt`. Implementer role: Kerning (Studio).

## Problem

In theater fullscreen (`.composer-shell.is-theater-fullscreen`, CSS at lines 639-666,
toggle at 5403-5420 of `font_kit_studio_v0.1.1.html`) the inspector covers the toolbar
that holds `btnToggleFullscreen` ("Exit (Esc)"). A mouse click where the button is lands
on the preview and selects a page element. The covered toolbar's controls stay focusable,
so Tab reaches controls the user cannot see. Esc works; the mouse does not.

## Required behaviour

1. While fullscreen is on, an Exit control is rendered inside the theater layer, above
   the preview and the inspector, and a click on it leaves fullscreen and selects nothing.
2. The covered toolbar (and anything else fullscreen hides under the inspector) carries
   the `inert` attribute while fullscreen is on, and loses it on exit.
3. Esc still exits. The button label logic at line 5405 stays truthful.
4. No connect, no font load and no message to the target as a side effect (that is Task 3's
   concern; do not touch the connect code).

## Tests (write first, watch them fail, then fix)

In `tests/test_studio_live.py`, Chromium, with the fake target fixture already used there:

- Enter fullscreen through the UI. Read the Exit control's bounding box and click its
  centre with `page.mouse.click`. Assert fullscreen is off and that no target became
  selected (the inspector shows no selection, the status badge did not change to a
  selection, and the fake target recorded no `design:select`).
- In fullscreen, call `.focus()` on a toolbar button under the inspector and assert it is
  not `document.activeElement`; assert the toolbar has `inert`. After exit, assert the
  attribute is gone and the button focuses.
- Esc still exits (characterize; expected to pass before the fix).

## Owned files

`font_kit_studio_v0.1.1.html` (theater CSS and the fullscreen toggle and key handlers
only), `tests/test_studio_live.py`. Touch nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_studio_live -k Fullscreen   # your tests, then the module
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep`
polling. Do not commit or push. First command: `git rev-parse HEAD`; if it is not
`d3a37e9`, run `git merge --ff-only origin/ccr-9eab25c9-mgatzt` before editing.

## Report

Append your report under this heading in this file: RED evidence (test names and the
failure text), the fix (functions and CSS touched, with line numbers), GREEN evidence
(test count for the module), what you did not verify.

### Implementer report (Kerning)

Base: worktree started at a6d2751 (older than the brief); fast-forwarded to 5917f56 on ccr-9eab25c9-mgatzt before editing. Not committed.

**RED** (`python -m unittest tests.test_studio_live -k Fullscreen`, new class `StudioFullscreenTests`, tests/test_studio_live.py:4346):
- `test_the_exit_control_is_a_visible_button_above_the_preview_that_leaves_fullscreen_and_selects_nothing`: ERROR, `Locator.wait_for: Timeout 30000ms exceeded. waiting for locator("#btnExitFullscreen") to be visible`.
- `test_the_covered_toolbar_is_inert_in_fullscreen_and_live_again_after_exit`: FAIL, `AssertionError: unexpectedly None` (the `inert` attribute on `.composer-toolbar` in fullscreen).
- `test_escape_still_exits_fullscreen_and_lifts_the_inert_state`: passed before the fix (characterized; its inert assertion holds trivially before the fix).

**Fix** (`font_kit_studio_v0.1.1.html`):
- CSS 669-684: `.theater-exit` is `display:none`, and shown absolutely positioned (top 18px, right 372px, z-index 2) only under `.is-theater-fullscreen`, so it sits above the preview and left of the inspector column.
- HTML 1081: new `#btnExitFullscreen` as the first child of `.composer-shell` (inside the theater layer, since the fixed layer covers the toolbar that holds `btnToggleFullscreen`).
- JS 5396-5470: `setTheaterInert(on)` marks every sibling of the shell and of its ancestors (toolbar, header, other modes) `inert`, tracking only what it set and removing exactly those on exit. `toggleFullscreenTheater` calls it, moves focus to the Exit button on entry and back to the toggle on exit, and the Exit button click calls the same toggle. The label logic ("Exit (Esc)" / "Fullscreen") and the Esc handler are unchanged. No connect, font-load or messaging code touched.

**GREEN:** `-k Fullscreen`: 3 tests OK. Whole `tests.test_studio_live` module: 151 tests OK, Chromium only. `python scripts/verify.py --static-only`: PASS (90 unique IDs, inline JS syntax, provenance).

Test strength: the click test checks `elementFromPoint` at the Exit centre, then clicks with `page.mouse.click`, and asserts that fullscreen is off, that a capture-phase click listener injected in the target frame saw 0 clicks (the fake target has no click-to-select, so this is the real hit-test proof), that no `liveTargetName` appears, no `design:select` was received, and no message at all reached the target. The inert test also Tabs 40 times in fullscreen and asserts focus never lands inside the toolbar.

**Not verified:** Firefox (not run, `FKS_ENGINES=chromium`); `frontend_gate.py` (contrast/layout/phone profiles) and the other test modules (not mine to run, shared CPUs); visual placement of the Exit button over a real wide-content target (no screenshot taken); phone-width fullscreen layout.

## Fix round 1

Review: docs/implementation/tasks/v021-task-1-review.md (Approved with fixes). Not committed. Scratch mutation copy lived outside the repo and was discarded; the worktree file was never mutated.

**1. Exit button anchoring (required).** New test `test_the_exit_control_stays_on_screen_and_clear_of_the_inspector_at_every_width` (1024x768 and 390x844: box inside the viewport, `elementFromPoint` at the centre is the button, and at 1024 no intersection with `#slotInspector`; it also clicks the button and asserts fullscreen is off).
- RED before the fix: 390 wide, `AssertionError: -144.390625 not greater than or equal to 0` (1024 passed, as expected for the old `right: 372px`).
- Fix: html:677 `right: 372px` replaced by `left: 18px`; the CSS comment at 669-670 now says it anchors the top-left of the preview so it stays on screen at any width and never meets the inspector.

**2. Focus handoffs (should fix).** Assertions added to the inert test and the Esc test: `document.activeElement.id` is `btnExitFullscreen` right after entry, and `btnToggleFullscreen` after click-exit and after Esc-exit. They passed at once (the handoff code already existed), so this is characterization, not RED; the mutation below proves they bite.

**3. Nit.** The inert test now asserts `document.head` has no `inert` while fullscreen is on.
- RED before the fix: `AssertionError: True is not false : <head> is not page content`.
- Fix: html:5420-5427 ancestor walk now stops at `document.body` (`node !== document.body`); `HEAD` is no longer marked. The enter/Esc/enter counts are unchanged (everything set is removed; `[inert]` is 0 after exit).

**Mutations** (scratch copy, `-k Fullscreen`, Chromium):
- B (`right: 0; z-index: -1`): FAILS, size test at 1024 and 390, `False is not true : a pointer finds the button`.
- B3 (`right: 340px`): FAILS, 1024 `button {x: 521.6..684} must not overlap the inspector {x: 674, y: 10, ...}`, and 390 `-112.39 not greater than or equal to 0`.
- E (remove both `.focus()` calls): FAILS, inert test and Esc test, `AssertionError: "" != "btnExitFullscreen"`.
- E2 (remove only the return-focus call): FAILS, `"btnExitFullscreen" != "btnToggleFullscreen"` (Esc test) and `"" != "btnToggleFullscreen"` (inert test).

**GREEN:** `-k Fullscreen`: 4 tests OK. Whole `tests.test_studio_live`: 152 tests OK (Chromium only, 313 s). `python scripts/verify.py --static-only`: PASS.

**Not verified:** Firefox, `frontend_gate.py`, other test modules, a screenshot of the new top-left position over a real target (the button now hides whatever the target draws in its top-left corner instead of the top-right).
