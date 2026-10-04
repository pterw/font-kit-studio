# v0.2.1 Task 7 brief: dead or misleading controls

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 7) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md` (ownership, contract with Task 6). Source:
`docs/implementation/audit-2026-10-03-first-run-and-controls.md` (P1, "Dead or
misleading"). Implementer: Kerning-7. Runs beside Task 6.

## Required

1. **Composition preset select** applies on change. If applying it would replace slot
   edits the user made since the last preset, Studio asks first (a `confirm()` is
   acceptable); Cancel keeps the edits and puts the select back to its previous value. If
   the Apply button then only re-applies the selected preset, remove it; if it does more,
   keep it and report what.
2. **"Custom / manual" kit**: wire it to an existing manual kit field if one exists (a
   single handler change); otherwise remove the option. Report which and why. Never add a
   prefilled kit ID (Rule 7).
3. **One-cut cards**: the single "Regular" chip is hidden.
4. **Demo "Choose Solo" and "Choose Studio"** (`demo/index.html`) act: pressing one marks
   that plan chosen with visible text. The demo is an app the bridge must leave alone, so
   these buttons show that Interact mode works.
5. **"Move into"** has no preselected container: the select starts on a placeholder, and
   the Move into button is disabled with a reason until a container is chosen. This is the
   one disabled state you own (SDD contract).
6. **A click on an Arrange sibling** selects that element (the same as selecting it on the
   page).
7. **Library** says which fonts are loaded, including fonts loaded from the Composer;
   never "fallback fonts" after a load.
8. **Recursion block** keeps the user's typed text in the field and says why the value was
   refused.
9. **Invalid colour text** shows a message next to the field; the previous valid colour
   stays applied.
10. **Colour on an SVG with its own fills** shows a note that the SVG's fills win.

## Owned

Studio (`font_kit_studio_v0.1.1.html`): the preset select's change handler and
`applyCompositionPreset`, the kit select, the one-cut chip rendering, the arrange block of
`renderLiveInspector` and the Arrange sibling click handler, the Library loaded-state label,
the recursion-block and invalid-colour messages, the SVG-fills note. `demo/index.html`.
New test module `tests/test_studio_dead_controls.py`.

Must not touch: `refreshControlStates` and `setDisabledReason` (Task 6, new), the `title`
attributes and hints of static controls (Task 6), the `<style>` block (Task 8). If you need
a disabled reason on a Task 6 control, stop and report it. `requestSelection`, `refreshSelection`, `sendTrackedSelection` and the
`design:selected` case belong to a selection-race fix running beside you: call them, never
edit them. If a message needs a style, use
an existing class.

## Tests (`tests/test_studio_dead_controls.py`, new)

Each item asserts what the user sees: the applied composition (computed style in the
specimen or target), the dialog and both of its answers, hidden chips, the demo's visible
chosen text, the Move into select's value and button state, the selection after a sibling
click, the Library label text, the field text and message after a recursion block, the
colour message and the unchanged applied colour, the SVG note. Item 4 and item 6 run
against the real bridge in a cross-origin frame. Name your RED tests before writing code.
Characterize items that already work as passing.

Changes to existing tests are allowed only when the old behaviour is the defect; list each
one with why. Grep the README and tests for every removed control or renamed label.

## Gates

`python scripts/verify.py --static-only`; `node --check fontkit-bridge.js`;
`PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python -m unittest test_studio_dead_controls test_studio_live test_font_kit_studio_v011
test_preview_server -v`. Do not run the full suite. Task 6 runs browser tests beside you on
4 shared CPUs.

## Report

Append "## Implementer report" here (your worktree copy): RED and GREEN per item, a mutation
per behaviour, the decisions on items 1 and 2, deviations, changed existing tests, final
`git diff --stat`, and what you did not verify.

## Implementer report

Kerning-7. Worktree at 16a07ce. Nothing committed or staged.

New module `tests/test_studio_dead_controls.py` (18 tests). RED run before any product change: 16 of 17
tests failed or timed out (the one that passed is the Library's own load, a characterization). GREEN: all 18
pass in Chromium. One mutation per behaviour, all 16 killed (script patched, ran the named tests, restored).

| Item | RED | Mutation killed |
|---|---|---|
| 1 preset select | select did nothing; 0 dialogs; Apply replaced edits silently | handler emptied; confirm skipped; select not restored on Cancel; Cancel applies anyway |
| 2 Custom kit | focus stayed on `modeComposer` | custom branch disabled |
| 3 one-cut chips | Inter, Space Grotesk, Bricolage Grotesque, Bebas Neue showed "Regular" | threshold `< 1` |
| 4 demo plans | no text change (real server, standalone and Interact mode through Studio) | click handler removed |
| 5 Move into | value was `container:7`, button enabled | placeholder removed; button never enabled |
| 6 sibling click | selection stayed on the title (real bridge) | click listener removed |
| 7 Library label | "Specimens show fallback fonts..." after a Composer load | status write removed |
| 8 recursion | field emptied, no reason | field cleared; message hidden |
| 9 invalid colour | no message (real bridge) | validation disabled |
| 10 SVG note | no note (real bridge) | note never shown; note on every target |

Decisions: the Apply button is kept (it is the only way to re-apply the already-selected preset, a reset,
because the select fires no change for the same value; it now asks before replacing edits and says "already
applied" on an untouched preset). "Custom / manual" is wired to the existing `#composerKitIds` field (focus plus
status; nothing prefilled).

Deviations: `setFreeFontStatus` added in `allowFreeFonts`/`loadAllFreeFonts` (the Library label's only writers);
new `#targetUrlProblem` element before `#targetUrlHint` (possible conflict with Task 6); the SVG note shows for
every SVG target because the manifest carries no fills information; `refreshArrange` keeps the chosen container;
"No other containers" option has an empty value.

Changed existing tests: `test_studio_first_run.py` recursion test renamed and inverted (the emptied field was the
defect); `test_studio_import_link.py` `test_sync_after_an_import_relinks_...` accepts the new replace-edits dialog.

Gates (Chromium; Firefox not run): static verify PASS; `node --check` OK; dead_controls + studio_live +
font_kit_studio_v011 + preview_server 224 OK; live_integration + review_findings + stage + first_run +
import_link 136 OK. Not verified: frontend gate, full suite (including `test_bridge_runtime.py`), Firefox/WebKit,
phone layout of the new hint beyond the existing 390 px arrange test.

### Fix round 1 (review findings 1-6, 8 and style)

Tests added to `tests/test_studio_dead_controls.py` (now 26): design:update counting for invalid colour
text; a keystroke-level colour test (no message and nothing sent while typing, Enter applies, `#12` plus Tab
shows the message and resets the field, typing clears it, a valid commit clears it); width, background and
import count as preset edits; linked-sync counts (+1, +0, +0, +1) against the fake target; the chosen Move
into container survives a re-render (a refused move); the Live Target family pick updates the Library label;
the remembered-choice and fresh-ask label are one string (`FREE_FONTS_ON_STATUS`). The stale comment at
`tests/test_live_integration.py:1621` now says the field keeps the refused address. The sibling-click test
now waits for `aria-current` to follow (it once read the list a moment before it re-rendered).
Mutations now killed: signature of slots only; invalid colour also sent; no clear on input; no clear on
valid change; `refreshArrange` forgets the container; no label write in `allowFreeFonts`; remembered path
with another string; Apply on an untouched preset re-applies; Cancel also applies.
