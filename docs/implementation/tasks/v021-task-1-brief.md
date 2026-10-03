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
