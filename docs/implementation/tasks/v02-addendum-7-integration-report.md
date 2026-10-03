# Addendum 7 bridge and integration report

## Fix round 1 (2026-10-03)

Owner of this report: the bridge and integration implementer. Files touched: `fontkit-bridge.js`,
`tests/test_bridge_runtime.py`, `tests/test_live_integration.py`. Chromium only
(`FKS_ENGINES=chromium`); Firefox is not installed and was not run. RED evidence for the real-vs-real tests
was taken on a scratch copy of the tree with Studio as it was at the start of the round (before the Studio
fixes landed). Mutations were run on scratch copies only.

### L1. Bridge-written role and name are not author hints

**RED.** `DemotedTargetTests.test_giving_the_id_back_and_resetting_leaves_the_markup_byte_for_byte_as_it_was`:
after edit, id removed, id re-added and reset-all, the paragraph held `data-design-role="editorial"` and a stale
`data-design-name="P: &quot;Edited tail bold tail&quot;"`. A second removal on the unedited span
(`test_a_second_removal_does_not_read_the_bridges_own_role_as_an_author_hint`) came back ordinary instead of
arrangement-only, because the leftover bridge role was read as an author role.

**GREEN.** `demote` and `registerSibling` read the role through `authorAttr`. When `promote` gives an element an
author id, the role and name the bridge wrote are removed (`dropBridgeAttrs`); an author's own role and name stay
(`test_an_authors_own_role_and_name_survive_the_round_trip`, characterised as passing).

**Same class, one more site.** The role-only candidate loop in `discoverTargets` matched the bridge's own
`data-design-role` through the `[data-design-role]` selector. A plain span that left the page and came back was
registered as an ordinary target (probe: ordinary, id 12) instead of arrangement-only.
`test_a_plain_span_that_leaves_the_page_and_comes_back_is_still_arrangement_only` was RED, and the candidate loop now
skips an element whose only match is a bridge-written role (the sibling pass registers it if it still needs an id).
This was not in the brief; it is the same defect as L1 (anti-pattern 12).

### L2. Demote's two branches

New `DemotedArrangementBranchTests` (6 tests). All pass on the fixed bridge, no manufactured RED: an unedited plain
span is `arrangementOnly: true` in `design:targets` and in a fresh `design:ready`; the same span after an edit, with an
author `data-design-role`, and a semantic `<p>` are ordinary (no `arrangementOnly`).

Mutations on a scratch copy: `ordinary` forced to `true` fails 3 tests; forced to `false` fails
`test_the_same_span_after_an_edit_is_an_ordinary_target`. (The role and semantic cases are also corrected by the
promotion pass in the same discovery run, so only the edited case distinguishes the second mutation.)

### L3. Real Studio and real bridge (`tests/test_live_integration.py`)

| Test | Result on round-start Studio | Waits on |
|---|---|---|
| (a) `FreeFontsAskTests.test_imported_override_fonts_stay_off_the_network_until_the_user_asks` | RED: the CSS tab already carried `@import url("https://fonts.googleapis.com/...Fraunces...")` before any ask | K1 (landed, GREEN) |
| (b) `StructureReplayTests.test_a_container_the_page_reorders_by_itself_is_not_saved_by_a_reset_of_one_child` | RED: export held a `structure` entry for the hero container | K3 (landed, GREEN) |
| (c) `StructureReplayTests.test_reapply_puts_a_saved_dom_move_back_on_the_first_press_even_with_a_stale_css_order_in_the_page` | RED: first Reapply stopped; the page held the original order | K4 (landed, GREEN) |
| (d) `SelectionOrderTests` (extended): `window.__fontkitBridge.selectedId` equals the user's pick | Passes (characterised); the realign mutation (`if (false)`) times out | none |
| (e) `FreeFontsAskTests.test_reapply_without_the_ask_sends_saved_token_fonts_to_no_font_host` | Passes (characterised) | none |
| (f) `FreeFontsAskTests.test_reapply_keeps_the_stylesheet_only_a_composition_slot_needs` | RED: Inter's link released | K10 (see below, still RED) |
| (g) `StructureReplayTests.test_a_saved_container_the_app_no_longer_owns_is_not_filled_with_the_saved_children` | RED: `[['See how it works','Start your free trial','Decoy one','Decoy two'], []]` | K5 (landed, GREEN) |

Also added: `ArrangeTests.test_a_dom_move_adds_no_css_rule_to_the_synced_file` (rules byte-equal apart from comments;
passes, characterised).

Test plumbing, all in `LiveIntegrationCase`: `export`, `import_document` (de-duplicated from two classes) and
`rehello` (the target posts a marker after it answers the hello; messages from one window arrive in order, so no
guessed pause). (g) changes the served demo page between loads through a context route, so the app really has a
second container matching the saved selector. The decoy's links carry author ids on purpose: auto ids are numbered in
page order, and plain links would take the numbers the saved ones had.

Existing test updated: `test_the_banner_after_sync_and_reload_explains_zero_live_edits_and_what_accept_does` now
expects the K6 wording ("Accept target state replaces Studio's saved overrides, composition tokens and DOM order").

### L4. `release_all`

The 30 ms pacing is gone. `SelectionOrderTests.release_all` releases one held reply, makes the target post a marker,
and waits until Studio has counted it. One 60 ms absence window remains for the final nothing-queued check.

### Open: (f) and K10

With the ask, after Composer Sync and a re-hello without a reload, a Reapply that carries a token update sends
`fontStylesheets` for the token fonts only (`live.compositionLinked` is false after the re-hello). The bridge treats
the list as the complete set and releases Inter, which only a slot uses and which the page still holds. Reported to
Kerning with a suggested fix.

Separate observation: while the composition is linked, an import streams a composition update, and the
acknowledgement replaces the saved tokens with the page's. The tests avoid it by re-helloing first.

### Gates run

`node --check fontkit-bridge.js` OK. `tests.test_bridge_runtime`: 122 tests OK (114 at the start of the round).
`tests.test_live_integration`: 37 tests, 36 OK; the one failure is (f), waiting on K10 (Studio file last changed 03:37:42). No server or browser of mine is left running.

## Fix round 2 (2026-10-03)

### K13-rename

`CompositionSyncTests.test_tracking_values_with_float_noise_and_the_limits_stay_exact` is now
`test_imported_tracking_values_are_normalised_before_they_reach_the_page`. It imports a document whose tracking values
are `0.035` and `-0.2 + 0.1 + 0.1` (1.39e-17), syncs, and asserts the page holds `0.035em` and `0em`. That proves
import normalisation, not send-side rounding, so the old name overclaimed. Studio's send-side rounding (typing
`0.1234` sends `123.4`) is covered by Studio's own test. No bridge change. No behaviour changed, so there is no RED
phase: this is a rename of a passing test. No other file refers to the old name except the review and Kerning's
report, which are not mine.

### Gates run

`node --check fontkit-bridge.js` OK. `tests.test_bridge_runtime`: 122 tests OK. `tests.test_live_integration`: 37
tests OK, including the former open item (f), which now passes against Kerning's current Studio file (mtime
04:35:43 at the start of the run; it changed again at 04:37:21 during the run, so the integration result covers the
file as of the start of the run). Engine: chromium only. Firefox is not installed and was not run. No server or
browser of mine is left running.
