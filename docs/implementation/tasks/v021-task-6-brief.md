# v0.2.1 Task 6 brief: disabled with a reason

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 6) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md` (ownership, contract with Task 7). Source:
`docs/implementation/audit-2026-10-03-first-run-and-controls.md` (P1, first paragraph).
Implementer: Kerning-6. Runs beside Task 7.

## Problem

Controls that would do nothing stay enabled and give no reason, so users think Studio is
broken. One of them, Sync to file with an empty ledger, writes a placeholder over the
user's existing overrides file (Rule 6).

## Required

A control that would do nothing is `disabled`, with the reason in its `title`, and in an
adjacent hint element where a title alone is easy to miss (Sync to Live App, Sync to file).
It is enabled again as soon as the state changes. The list:

| Control | Disabled while | Reason says (wording yours, plain English) |
|---|---|---|
| Sync to Live App | no target connected | connect a page first |
| Restore Page Text | no target, or no text edits | nothing to restore |
| Reset this element | the selected element has nothing to reset | no changes on this element |
| Width buttons; Select / Interact | Specimen view | only for the Live App view |
| Load free fonts | fonts already loaded | already loaded |
| Sync to file, Copy, Download | the ledger is empty | no changes to save yet |
| Colour fields | they do not match the chosen colour source (toolbar and every slot) | which source is active |
| Style / cut | the family has one cut | one cut only |
| Image Width | no image chosen | choose an image first |
| Focus pop-out | the pop-out window is closed | the pop-out is closed |

Sync to file must not write a placeholder over an existing file when the ledger is empty,
by any path (button or automatic sync). If that write happens in a function outside your
ownership, guard it there with the smallest change and record it as a deviation in your
report.

## Design (binding, from the SDD plan)

- A new `refreshControlStates()` decides every state above, and a new
  `setDisabledReason(el, reason)` sets `disabled`, `title` and the hint (`reason` null
  re-enables and restores the control's normal title).
- Call `refreshControlStates()` once at each existing refresh point (connect, disconnect,
  selection, ledger change, view switch, font load, pop-out open and close). Do not
  restructure those functions.
- You may edit the `title` attributes and add hint elements next to static controls in the
  markup.

## Owned

Studio (`font_kit_studio_v0.1.1.html`): `refreshControlStates`, `setDisabledReason`, the
one-line calls at refresh points, `title` attributes and adjacent hint elements of static
controls. New test module `tests/test_studio_controls.py`.

Must not touch: the arrange block of `renderLiveInspector`; the preset select, kit select,
one-cut chip rendering, Arrange sibling click, Library loaded label, recursion-block and
invalid-colour messages, SVG-fills note (all Task 7); the `<style>` block (Task 8). If you
need a disabled reason on a Task 7 control, stop and report it. `requestSelection`, `refreshSelection`, `sendTrackedSelection` and the
`design:selected` case belong to a selection-race fix running beside you: call them, never
edit them.

## Tests (`tests/test_studio_controls.py`, new)

For each control: the rendered `disabled` state and the reason text (title and hint) in the
state that earns it, then enabled again after the state changes. Use the real Studio and
the demo target through `LiveCase` (`tests/test_studio_live.py`) or `LiveIntegrationCase`;
at least one case runs against the real bridge. One test proves Sync to file with an empty
ledger leaves an existing overrides file byte for byte unchanged. Name your RED tests before
writing code. Characterize controls that already behave correctly as passing.

Changes to existing tests (an assertion that relied on an enabled control) are allowed
only when the old behaviour is the defect; list each one with why.

## Gates

`python scripts/verify.py --static-only`; `node --check fontkit-bridge.js`;
`PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python -m unittest test_studio_controls test_studio_live test_font_kit_studio_v011 -v`.
Do not run the full suite. Task 7 runs browser tests beside you on 4 shared CPUs.

## Report

Append "## Implementer report" here (your worktree copy): RED and GREEN per control, a
mutation per behaviour, deviations, changed existing tests, final `git diff --stat`, and
what you did not verify.

## Implementer report

Implementer: Kerning-6. Base `16a07ce`. Not committed.

### What changed

Studio (`font_kit_studio_v0.1.1.html`)
- New `setDisabledReason(el, reason)` (sets `disabled`, `title`, the adjacent `[data-hint-for]` hint and
  `aria-describedby`; `null` re-enables and restores the control's normal title) and
  `refreshControlStates()` (decides every control in the table), with `savedStateEmpty()`,
  `ledgerEmpty()`, `elementHasChanges()` and `applyColourSource()` beside them.
- Two hint elements in the markup: `#syncToAppHint` and `#liveCodeSyncHint`.
- `refreshControlStates()` is called at: `renderLiveCode` (ledger), `renderLivePanels` (connect, disconnect,
  view switch to Live App, pop-out open and close), `refreshLiveInspector` (selection), the iframe `load`
  handler (page reload), `renderInspector` (slot inspector, view switch to Specimen), the `renderCanvas`
  wrapper (slot colour source), `updateCanvasBackground` (toolbar colour source, import), `setSyncAvailability`
  (dev server answer), and two `document` events for fonts (`fontkit:free-fonts-allowed`, new
  `fontkit:font-state`).
- Definitions used: Sync to Live App and Restore Page Text follow `live.ready`; Restore also needs a ledger target
  with `text !== null`; Reset needs a saved override, a ledger entry with declarations or text, or a DOM-order
  entry naming the element; Load free fonts is disabled only when consent is given AND every library
  stylesheet link is in state `loaded` (after a failed load it stays enabled so the user can retry); Sync to
  file needs the dev server (its own reason is kept) and a non-empty saved state (overrides, saved tokens,
  DOM moves: what the Changes count shows); Copy and Download need the same or any page ledger entry.

### Deviations (recorded)

1. **`writeOverrides` (outside the Task 6 list)**: guarded with the smallest change, one line at the top of the
   write loop: `if (savedStateEmpty()) { setCodeStatus(...); break; }`. It covers Sync to file and Auto-sync,
   including a write queued while the ledger emptied. Consequence the owner should know: after a user resets
   the last change with Auto-sync on, the file keeps the previous edit (it is not rewritten to a placeholder),
   and the status line says so. This follows the brief ("by any path").
2. `ensureFontStylesheet` (top-level script, not named in any ownership row): its two link listeners now also
   dispatch `fontkit:font-state`, so the Load buttons can follow the loaded state. No other change there.
3. `setSyncAvailability` no longer sets the Sync button's `disabled` and `title` itself; it stores
   `live.syncTitle` and calls `refreshControlStates()` (the title is the normal title and the dev-server reason).
4. Reasons for the width buttons say "Live App view" and name no button label, so Task 8's rename stays true.

### Changed existing tests (each relied on a control the brief makes disabled; the old behaviour is the defect)

- `test_studio_live.py`
  - New constant `DEV_SERVER_ANSWERED` replaces 7 waits for `#liveCodeSync` to become enabled (with an empty
    ledger it is now disabled by design; "Checking..." leaving its title is the signal). Same constant used in
    `test_studio_first_run.py` (2 waits, plus the import).
  - `test_send_path_has_single_anti_recursion_guard...`: asserts Sync to Live App is disabled instead of
    clicking it with nothing connected.
  - `test_sync_and_debounced_serialized_auto_sync`: the "title names the file" assertion moves after the first
    edit (the button names the file only when there is something to write).
  - `test_every_control_message_carries_protocol_version_and_session`: a font-size edit before Reset (revs 4, 5).
  - `test_library_has_sixteen...`: "pressing again does not duplicate" now waits for the buttons to be disabled
    and then forces one press to keep the no-duplicate check.
  - `test_a_reset_of_an_unrelated_target_*` (2), `test_a_reset_never_saves_a_container_only_the_page_reordered`:
    the element gets a real edit first, so Reset has something to do (revisions shift by one).
  - `test_a_dom_move_triggers_no_auto_sync...`: Auto-sync with an empty ledger no longer writes on switch-on
    (that write was the placeholder defect); the baseline write now comes from a font-size edit. `move_first`
    gained a `rev=1` keyword.
  - `StudioSelectionOrderTests` (6 tests, via `reset_with_held_acknowledgement` and
    `test_the_refresh_still_happens...`): a font-size edit on card.a before Reset; later revision waits are
    `rev 2`. **The selection-race agent edits the same class: expect a merge overlap there.**
- `test_live_integration.py` (real bridge; found by running the module, 41 of 43 passed unchanged):
  - `test_a_click_right_after_a_reset_keeps_the_clicked_target_selected_and_edited`: types a font size and waits for
    Reset to enable before the held reset.
  - `test_the_banner_after_sync_and_reload_explains_zero_live_edits_and_what_accept_does`: after Accept the page
    holds nothing, so Sync to file is now disabled ("No changes to save yet") and the file stays as synced; the
    old "Sync then writes a smaller file" tail is replaced by that. **Product follow-up for the owner:** the banner
    still says "so the next Sync writes a smaller file" (`acceptShrinksFile` in `renderReconnectBanner`, not mine).
    When the accepted state is empty that sentence is no longer true: Sync is disabled instead of writing a
    placeholder. A wording change in the banner (or a decision that Accept-to-empty may write) is the owner's call.
- `test_font_kit_studio_v011.py::test_row_controls_and_leaf_inspectors`: chooses an image (1x1 PNG constant
  added) before filling Width.

### New tests: `tests/test_studio_controls.py` (19 tests, 5 against the real bridge and real `serve.py`)

RED (unchanged Studio, Chromium): 18 of 19 fail, by the missing `disabled` state or hint:

| Control | RED test | Result before |
|---|---|---|
| Sync to Live App | `test_sync_to_live_app_is_disabled_until_a_page_connects_and_again_when_it_goes_away` | fail |
| Restore Page Text | `test_restore_page_text_needs_a_page_and_then_a_text_edit`, `test_a_style_edit_alone_leaves_restore_page_text_disabled`, real bridge `test_restore_page_text_and_reset_follow_real_edits` | fail |
| Reset this element | `test_reset_is_disabled_until_the_selected_element_changes_and_follows_the_selection` (+ real bridge test above) | fail |
| Width buttons, Select/Interact | `test_width_buttons_and_pointer_mode_are_for_the_live_app_view_only` | fail |
| Load free fonts (both buttons) | `test_load_free_fonts_is_disabled_once_every_family_has_loaded` | fail |
| Load free fonts after a failed load | `test_a_failed_load_leaves_the_button_enabled_to_try_again` | passes before: characterization |
| Sync to file, Copy, Download | `test_sync_copy_and_download_wait_for_a_change_and_the_hint_says_why`, `test_without_a_dev_server_sync_to_file_says_so_but_copy_and_download_work` (hint missing), real bridge `test_sync_to_file_follows_the_real_ledger_and_writes_what_it_holds` | fail |
| Sync to file never overwrites | `test_sync_to_file_with_an_empty_ledger_leaves_an_existing_file_byte_for_byte`, `test_auto_sync_never_writes_a_placeholder_when_the_ledger_empties` | fail (placeholder written) |
| Colour fields | `test_the_canvas_colour_fields_follow_the_chosen_source`, `test_an_imported_source_updates_the_canvas_colour_fields`, `test_each_slot_colour_field_follows_that_slots_source` | fail |
| Style / cut | `test_style_cut_is_disabled_for_a_family_with_one_cut` | fail |
| Image Width | `test_image_width_waits_for_an_image` | fail |
| Focus pop-out | `test_focus_pop_out_needs_an_open_window` | fail |

GREEN (changed Studio): `test_studio_controls` 19/19; with `test_studio_live` and `test_font_kit_studio_v011`
together 191 tests OK (19 + 152 + 20), Chromium only. Also run green: `test_studio_first_run`,
`test_studio_review_findings`, `test_studio_stage`, `test_studio_import_link` (93 tests). `verify.py
--static-only` PASS (95 unique IDs), `node --check fontkit-bridge.js` OK.

### Mutations (each applied to the Studio file, the new module run, then restored; all KILLED)

M1 Sync to Live App always enabled; M2 Restore ignores text edits; M2b Restore ignores the connection; M3 Reset
always enabled; M4 view controls always enabled; M5 Load free fonts never disabled; M5b Load free fonts disabled on
consent alone; M6 Sync to file ignores the empty ledger; M6b Sync to file ignores the dev server; M6c write guard
removed (both byte-for-byte and auto-sync tests die); M7 Copy ignores the ledger; M7b Download ignores the ledger;
M8 toolbar colour fields always enabled; M9 slot colour fields always enabled; M10 Style/cut never disabled; M11
Image Width never disabled; M12 Focus pop-out never disabled; M13 hints never shown; M14 normal title not restored
on re-enable (killed after adding title assertions; it survived first); M16 no refresh in `renderLiveCode`; M18 no
refresh in `updateCanvasBackground`; M19 no refresh on a font sheet event.
Survivors were removed, not kept: a call in `renderPopoutState` (every path also reaches `renderLivePanels`) and one
at the end of `switchToSpecimenView` (`renderInspector` already refreshes; the no-slot early return is unreachable).

### Not verified

- Firefox and WebKit: not run. Full suite, frontend gate and commit-message check: not run (brief).
- `test_bridge_runtime`, `test_preview_server`, the frontend gate and the gate's tests were not run. Reading
  the gate: `_frontend_gate_live.py` presses Reset after an edit (still enabled) and `_frontend_gate_network.py`
  presses Load free fonts again only for families that failed (still enabled), so neither should change; unverified.
- No visual check: Select/Interact (not `.btn`) has no `:disabled` style, so it is disabled but looks unchanged;
  the `<style>` block is Task 8's. The hint spans reuse `.composer-status` and `.live-code-status`.
- Disabled-button tooltips are Chromium behaviour; the hint elements are the fallback for Sync to Live App and Sync to file.
- Restore Page Text is enabled from the page's ledger, so a text edit made by composition Sync is counted only once
  the page reports it.

### Incident to relay

The shared scratchpad is one directory for all agents. Another agent's `mutate.py` replaced mine mid-session and
my second invocation ran it: it flipped one line of `demo/index.html` in the worktree `agent-a121c95cbf269fb5c`
for the length of one `DemoPlanTests` run and restored it in a `finally`. Tell that agent if a demo test failed
spuriously around then. My scripts now use a `k6_` prefix.

### Fix round 1 (review verdict "Changes required")

1. **`writeOverrides` guard (finding 1).** New `live.heldSavedState`, set in `renderLiveCode` whenever saved state is
   non-empty. `emptyWriteRefused()` is `savedStateEmpty() && !live.heldSavedState`; it gates the refusal in
   `writeOverrides` and the Sync to file disabled reason. When Sync to file is enabled with empty state its title says
   it writes an empty overrides file. Rewritten tests: `test_auto_sync_writes_the_empty_file_after_the_user_resets_the_last_change`
   (real bridge: file becomes the placeholder, a reload shows the base size), `test_sync_to_file_clears_the_file_after_the_user_resets_the_last_change`
   (no Auto-sync), the fake-target Sync/Copy/Download test (after Reset Sync is enabled and writes the placeholder, Copy
   and Download stay disabled). A fresh session still refuses: byte-for-byte test kept, plus
   `test_a_fresh_session_refuses_auto_sync_over_an_existing_file` and `test_a_fresh_session_never_writes_when_auto_sync_is_switched_on`.
2. **Banner test (finding 2).** The Accept-then-Sync assertions in `test_the_banner_after_sync_and_reload_explains_zero_live_edits_and_what_accept_does`
   are back to the originals (Sync writes a smaller file). Only that test body changed in this round.
3. **Focus (finding 3).** `setDisabledReason` calls `moveFocusAway(el)` when the element is `document.activeElement`: focus
   goes to the next usable control in the same panel (`#slotInspector`, `#targetAppBridgeBar`, `.controls`,
   `.composer-toolbar`, `.live-code-panel`), else the last one before it. `KeyboardFocusTests` (4): Reset (Tab to the button,
   Enter, focus lands on All targets), Restore Page Text, Load free fonts in the Library and in the Composer; each also
   presses Shift+Tab afterwards (Tab from the last control of the page leaves the document, so it proves nothing).
4. **Anti-recursion test (finding 5).** Forces a click on Sync to Live App (`disabled = false; click()`), after asserting it is disabled.
5. **Gaps (finding 7).** Added `SavedStateKindTests`, `RebuiltInspectorTests`, `LoadingFamilyTests`; `assert_disabled`/`assert_enabled`
   now check `aria-describedby` against the hint.

RED before the product change (unchanged Studio, new tests): the three guard tests, the banner test and the 4 focus tests
fail; the gap tests (tokens only, DOM order only, Reset clauses, loading family, rebuilt inspector) pass on the old code
by design and are killed by the mutations below. One test needed a different set-up: `import_document` with an empty
`live` does not clear Studio's saved overrides, so the page-ledger-only state is made by importing an override for another
element and then resetting it.

GREEN: `test_studio_controls`, `test_studio_live`, `test_live_integration.SyncAndReloadTests`: 186 tests OK (Chromium).
`verify.py --static-only` PASS, `node --check fontkit-bridge.js` OK.

Mutations (each KILLED by `test_studio_controls`): N1 Reset ignores the page ledger; N2 Reset ignores DOM order; N3 Load
free fonts disabled while a family still loads; N4 saved tokens do not count; N5 DOM order does not count; N6 Copy/Download
ignore the page ledger; N7 no `aria-describedby`; N8 no refresh at the end of `renderLivePanels`; N9 held state never
remembered; N10 held state always true; N11 focus not moved; N12 no title for the empty write; N13 write guard removed;
N14 focus never moves after the element.

Not run this round: the rest of `test_live_integration`, `test_studio_first_run`, `test_font_kit_studio_v011`, Firefox, the
frontend gate, the full suite. Findings 4 and 6 (CSS) are Task 8's and untouched.
