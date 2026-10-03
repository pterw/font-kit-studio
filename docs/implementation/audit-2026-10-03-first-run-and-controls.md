# Audit: first run, controls and visual fit (2026-10-03)

Read-only audits of `main` at 62fcc1f, run after the owner reported that buttons
seemed to do nothing and the demo would not load. Three passes: every control in every
reachable state (real clicks in Chromium), every way a newcomer can start the demo, and
the visual design at 1440, 1280 and 1024 px (390 advisory). Firefox, WebKit, Windows and
macOS were not tested. This is the scope proposal for the fit-and-finish pull request;
nothing here is built yet.

## P0: broken or trapping

1. **Fullscreen cannot be left with the mouse.** The inspector covers "Exit (Esc)" in
   theater mode, so a click selects a page element instead; the covered toolbar stays
   focusable. Fix: put Exit in the theater layer and make the covered toolbar `inert`.
2. **First run fails silently or with the wrong advice.**
   - Studio opened from disk with no server shows "No bridge answered. Add
     fontkit-bridge.js ..." although nothing is listening; Studio cannot tell "no server"
     from "no bridge".
   - A busy port 8000 or 8001 prints only `cannot listen: [Errno 98] Address already in
     use`, naming no port and offering no flag. On Windows, `SO_REUSEADDR` may let a
     second server start on a taken port (code reading, untested).
   - `serve.py` prints a Studio and a Target URL without saying which to open, and opens
     no browser; Studio without `?target=` does not offer the demo.
   - An empty URL field silently connects to `http://localhost:8001/demo/` and logs a
     `postMessage` origin error.
   - Every target load logs a 404 for `demo/fontkit-overrides.css` (git-ignored, absent
     in a fresh clone), and a headed browser may log a `favicon.ico` 404.
   - Remote or `--host 0.0.0.0` use gets raw `421` JSON; a Studio hosted on the web cannot
     reach `localhost` in Chromium and says nothing.
   - README says only "Python 3"; `python` may be Python 2 or the Windows Store stub.
3. **The 1440 and 1024 width buttons crop the page** on the right, with no scrollbar.

## P1: controls that do nothing, or say the wrong thing

Disable with a visible reason (and assert the rendered disabled state in tests):
Sync to Live App and Restore Page Text with no target; Restore Page Text with no text
edits; Reset this element with nothing to reset; the width buttons and Select/Interact
in Specimen view; Load free fonts once loaded; Sync to file, Copy and Download with an
empty ledger (Sync currently overwrites an existing file with a placeholder); colour
fields that do not match the chosen colour source (toolbar and every slot); "Style /
cut" with one cut; image Width before an image is chosen; Focus pop-out once the window
is closed.

Dead or misleading: the Composition preset select does nothing until Apply, and Apply
then replaces edits without asking; "Custom / manual" kit does nothing; the single
"Regular" chip on four cards; the demo's "Choose Solo" and "Choose Studio"; "Move into"
preselects the logo link; a click on an Arrange sibling does nothing; Library still says
"fallback fonts" after fonts were loaded from Composer; Fullscreen connects as a side
effect; a URL that is not absolute is loaded relative to Studio; recursion blocking
replaces the user's text; invalid colour text is dropped without a message; colour on an
SVG with its own fills changes nothing visible.

Also: `compositionPatch` takes `--font-serif` from `state.slots[2]`, which is the Row
slot in the default preset, so the token falls back to Fraunces.

## P1: visual quick wins (about five hours)

- `.btn.primary` has no CSS, so no action reads as primary.
- One control-size scale: buttons run from 26 to 45 px; `select` and `textarea` miss
  `font: inherit` and render 13 px Arial.
- In Target App view, hide composition-only fields and compact the header; the live page
  starts at y = 865 of 900 today.
- Inspector: breakpoint 1100 to 900 px, a 300 px column, a bounded height; bound and
  group the 2,400 px target list.
- `:focus-visible` rings (inputs set `outline: none`) and field borders of at least 3:1.
- Contrast: `.tag` 4.30:1, placeholders about 4.1:1, `.asset-placeholder` 2.12:1.
- Copy: one name for "your page" (Target App, Live App, Live Target), no emoji in the
  bridge bar, one glyph per action (`⛶` means both Fluid and Fullscreen), drop "V0.1.1".

## P2: structural (plan with R1 and R3, not in this pull request)

Split the Composer into "Compose" and "Your page" modes; a grouped, searchable inspector;
a slim app shell with the hero as the Library's empty state; a plain-language reconnect
card; design tokens for spacing, radius, type and control height.
