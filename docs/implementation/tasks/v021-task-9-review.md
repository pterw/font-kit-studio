# v0.2.1 Task 9 review: README, names and screenshots

Reviewer: Leading. Base `ef7d3f2` plus the uncommitted Task 9 diff (applies unchanged on
`8cea6d5`). Date: 2026-10-04.

Verdict: **Approved with fixes.** Gates: static checks and `node --check` pass;
`test_preview_server test_studio_visual`: 66 tests OK; `test_live_integration`: 52 OK;
offline Chromium frontend gate OK (0 FAIL); `capture.py` runs clean. README, CONTRIBUTING
and `docs/assets/README.md` have no old page names left; 48 relative links, images and
anchors resolve. The first-run flow, every disabled control and its reason, the
Sync-to-file behaviour, the preset select, the free-fonts paragraph, the guard table,
keyboard moves, pop-out and the reconnect banner were checked in a real browser.

## Findings

1. Medium. README's Sync to Live App sentence (about line 234) says it sets only font
   tokens and tracking and that reordering never shows in the Changes panel. The bridge
   also restyles every element a text slot maps to (family, size, weight, line height,
   tracking, colour, alignment, case; text only when edited) and moves sections in the
   DOM when two or more match, which the HTML tab records; only the element styles and
   CSS `order` stay out of the Changes panel.
2. Medium. The Live App URL box is squeezed to 110-140 px in 11 of 15 states
   (`.bridge-bar .bridge-url { flex: 1 1 100px; min-width: 100px }`, older than Task 8,
   exposed by its compact controls); `live-app-desktop`, `bridge-bar-desktop` and
   `pop-out-desktop` show it. A 240 px floor keeps every state at 247 px or more. Nothing
   pins the width today.
3. Medium. `live-app-mobile.png` shows a stale selection outline: at 390 px the frame is
   scrolled out of view, its animation frames do not run, and the shot is taken before the
   bounds update. A capture-timing bug in `capture.py`; in normal use the outline catches
   up within about 60 ms.
4. Low. "**No** keeps them": the dialog is a native confirm with OK and Cancel.
5. Low. After a reset, Sync writes two comment lines (the header naming the Live App URL,
   then "No live style overrides yet."), not one.
6. Low. In fullscreen the bridge bar is covered, so "press Connect Live App" needs "leave
   fullscreen first".
7. Low. Only the tab title and the eyebrow carry the version, not the heading.
8. Low. The pop-out size is the available screen minus 80 px, clamped to 600-1280 by
   400-860, not "about 1280 by 860".
9. Low. "Reload the preview" names a control Studio does not have; pressing Connect Live
   App again reloads the frame.
10. Low. The literal "v0.2.1" in README prose and alt text drifts at every release.
11. Low. Old page names remain outside Task 9's files: AGENTS.md, global rules and the
    design spec (fixed by the controller), the frontend gate's printed section labels,
    `serve.py` and test docstrings, Studio code comments, and the pop-out placeholder that
    shows the window name `fontkit-target` as text.
12. Info. At 390 px the "No bridge answered" badge makes the page scroll sideways
    (pre-existing; advisory under D029).

Not verified: Firefox, the full suite, external links, pop-out size on a real screen.

## Re-review of fix round 1 (2026-10-04)

Verdict: **Approved with fixes** (Low items). Findings 1-11 are resolved.
`test_preview_server test_studio_visual test_live_integration test_studio_first_run`:
143 tests OK; the other Studio suites against the new CSS: 299 OK; offline Chromium gate
OK (the only change is the advisory phone line for the URL box, 140 to 314 px wide); 48
links resolve; no literal version left in README.

- The Sync to Live App list matches the bridge on the demo and on the fixture page, and
  pressing Connect Live App again restores every inline style, the section order, images,
  stylesheet links and texts in three scenarios.
- URL box: RED on the old rule (16 characters at 1440 px, idle, demo offered), GREEN on
  the new one; the smallest box is 247.5 px. The 34 px preview shift at the first edit is
  gone at 1440 and 1280 and stays at 1024 (pre-existing).
- `capture.py`: without the new wait the phone shot is byte-identical to the stale one;
  with it the outline covers all five title lines. All nine PNGs match the README.

Remaining:
- R1 (Low). The Sync list stops at text slots; image, spacer and rule slots also change
  the page, and a slot with no role match lands on the element at its position.
- R2 (Low). Nothing pins the pop-out placeholder without the window name.
- R3 (Low). `scripts/dev/_frontend_gate_layout.py` still prints "Composer target view"
  on 50 advisory lines (display only).
- R4-R9 (Info): one `subTest` per width and state in `UrlBoxFitTests`; clearer CHANGELOG
  wording for the URL box; "available screen"; two test comments with the old name; the
  desktop-hero wait is harmless; commit the URL box fix apart from the docs.
- Fix round 2, closed by the controller on reading the diff: the README's Sync to Live
  App text now covers how a slot finds its element (role, then position) and what image,
  spacer and rule slots do, matching the behaviour the reviewer saw in round 1; the pop-out
  placeholder is pinned (`assertNotIn('fontkit-target', ...)`, RED with the old text); the
  gate's layout labels say "Composer Live App view"; `UrlBoxFitTests` reports each width and
  state on its own (seven subtests fail on the old CSS); CHANGELOG and README wording fixed;
  two test comments renamed. Gate helper modules, `test_studio_visual` and
  `test_preview_server`: 228 tests OK; `test_bridge_runtime`: 128 OK.
