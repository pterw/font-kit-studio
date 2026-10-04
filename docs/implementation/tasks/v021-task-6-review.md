# v0.2.1 Task 6 review: disabled with a reason

Reviewer: Leading. Base `16a07ce` plus the uncommitted Task 6 diff. Date: 2026-10-03.

Verdict: **Changes required** (one product fix; the rest are test follow-ups).
`test_studio_controls test_studio_live test_font_kit_studio_v011 test_studio_first_run
test_live_integration`: 258 tests OK in 375 s (Chromium); static checks and
`node --check` pass. Task 6 and Task 7 merge with no conflicts.

## Ruling on the `writeOverrides` guard

The guard refuses every write while saved state is empty. Probed with the real bridge and
`serve.py`: Auto-sync on, set a size of 52 px, Reset this element. The file kept
`font-size: 52px !important`, and a target reload brought 52 px back while the banner
counted 0 targets on both sides. Without Auto-sync, Sync to file was disabled after the
Reset, so Studio offered no way to clear the file. Studio never reads the file, so "empty"
cannot tell "never had anything" from "the user just emptied it".

Ruling (controller, confirmed by the reviewer on a scratch copy): refuse an empty write
only when Studio has never held non-empty saved state in this session. A flag set in
`renderLiveCode` whenever saved state is non-empty gates both `writeOverrides` and the
Sync to file disabled state. With it, Reset writes the empty file and the reload shows the
base size; a fresh session, and switching Auto-sync on in one, still refuse; the banner's
"the next Sync writes a smaller file" stays true.

## Findings

1. High. The guard (above).
2. High (test). The banner test in `tests/test_live_integration.py` (about line 440) still
   asserts the banner says Sync writes a smaller file, then asserts Sync is disabled and the
   file unchanged. Restore its original assertions.
3. Low-Medium (keyboard). A control that disables itself after a keyboard press (Reset,
   Restore Page Text, Load free fonts) drops focus to `<body>`.
4. Medium (visual, Task 8). Select and Interact are disabled in Specimen view but look the
   same; `.bridge-mode` buttons need a `:disabled` style.
5. Low (test). The anti-recursion test no longer drives the Sync handler; force a click to
   keep the runtime proof.
6. Low (visual, Task 8). The Sync to file hint runs on from the Auto-sync label.
7. Low (test gaps). Surviving mutations: Reset ignoring ledger and DOM-order entries; Load
   free fonts disabled while one family still loads; Sync to file with only tokens or only
   DOM order; Copy and Download with a page-ledger-only state; no `aria-describedby`; no
   refresh at the end of `renderLivePanels`.

Accepted: `ensureFontStylesheet` dispatching `fontkit:font-state`; `setSyncAvailability`
storing `live.syncTitle`; the changed existing tests that add an edit before Reset and wait
for the dev server through the title. Rule 5 is clean (`title` and `textContent` only).

Mutations: 21 run, 13 killed, 2 equivalent, 6 gaps (finding 7).

Not verified: Firefox, WebKit and phone layouts, the frontend gate, the full suite.

## Re-review of fix round 1 (2026-10-04)

Verdict: **Approved.** Findings 1, 2, 3, 5 and 7 are fixed. `test_studio_controls`: 32 tests
OK; `SyncAndReloadTests` (original banner assertions restored): 2 OK; static checks pass.

- `heldSavedState`, probed with the real bridge and `serve.py`: after Reset, Auto-sync
  writes the empty file and a target reload shows the base 60.96 px; without Auto-sync,
  Sync to file is enabled with an empty-write title and clears the file. A fresh session
  (and a Studio reload) still refuses, for the button and for Auto-sync over an existing
  file, which stays byte-identical. Low: first-connect adoption of a page ledger also sets
  the flag; the only effect is that a later explicit Sync can write an empty file, and its
  title says so.
- `moveFocusAway` fires only for the active element; a background refresh never moves
  focus from a text field mid-typing; disabling six view controls in one pass walks focus
  to the next enabled control with no loop.
- Every earlier survivor is killed. Low: moving focus also when enabling survives; nothing
  asserts that a focused, enabled control keeps focus across a refresh.
