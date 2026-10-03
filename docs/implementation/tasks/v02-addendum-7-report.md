# Addendum 7 implementer report: known-limit fixes

Branch `ccr-9eab25c9-mgatzt`, base HEAD `18856ac`. Chromium only (`FKS_ENGINES=chromium`); Firefox not run.
Files changed: `fontkit-bridge.js`, `font_kit_studio_v0.1.1.html`, `tests/test_bridge_runtime.py`,
`tests/test_studio_live.py`, `tests/test_live_integration.py`, `tests/fixtures/studio/fake-target.html`,
`tests/fixtures/bridge/target-restricted-upper.html` (new). Nothing is committed.

Baseline before any change: `tests.test_bridge_runtime` 99 tests OK.

## 1. DOM-order moves survive a reload

**RED.** Bridge: `test_ledger_structure_reports_changed_containers...` failed with "Items in the second set but not the
first: 'orderIds'". Studio (fake target), `StudioDomMovePersistenceTests`: 5 of 7 failed (`KeyError: 'live'` on export,
no "kept in Studio" status, the accept test never showed the banner, a malformed `live.structure` import was accepted).
Real Studio + real bridge, `ArrangeTests.test_a_dom_move_survives_sync_and_reload_through_an_explicit_reapply`, against
the old Studio: timeout waiting for the "kept in Studio" status.

**Fix.**
- Bridge: each ledger `structure` entry gains `orderIds` (child target ids, same order as `order`). Additive.
- Studio saves DOM moves as `live.structure = [{selector, name, ids}]`, kept in the `live` JSON and the JSON tab (only
  when non-empty).
- It mirrors the bridge ledger for the containers a move or reset touched. Reset of everything clears it.
- A saved container the page does not hold is a reconnect conflict. Containers only the page reorders (a composition
  sync) are never saved and never raise a conflict.
- Reapply replays the saved order after its resets. The container is found by its selector (keys like `container:3`
  change on every load). A child already in the container moves by `{index}`, one elsewhere by `{container, index}`.
- Reapply succeeds only when the page's ledger holds the saved order. If a container cannot be found it sends nothing
  and says so.
- A DOM move sets the status line: "Moved in the page markup. The move is kept in Studio (Reapply puts it back after a
  reload) and the HTML tab shows it, but it is not in the CSS file: Sync to file writes CSS only. CSS order is the move
  strategy the CSS file keeps." A CSS-order move says Sync writes it as order rules. A DOM move does not trigger
  auto-sync, since no CSS changed.
- The banner adds "Studio also saved DOM order changes in N containers; the live target holds H of them."
- The Reapply notice no longer claims it undoes a DOM move when that move is saved.

**GREEN.** `StudioDomMovePersistenceTests` 9 tests OK (explicit Reapply, re-parenting into another container, Accept
drops it, hostile imports rejected transactionally, an older bridge without `orderIds` saves nothing, target-only
reordering ignored, reset drops both containers). Real vs real integration test OK. Bridge `orderIds` test OK.

**Existing test changed.** `test_reapply_states_that_it_resets_a_dom_moved_arrangement` now deletes `live.structure`
from its imported JSON (the export now holds the DOM move). New `test_reapply_keeps_a_saved_dom_move_while_it_clears_a_stale_css_order`
covers the other case.

**Limits.**
- A DOM move that needed **Move anyway** (framework guard) is replayed without `force`, so the guard rejects it and
  Reapply stops with the reason.
- Mixing CSS order and DOM order in one flex container can replay by visual index.
- A container with no manifest in the page (an empty container) cannot be placed.
- While a conflict is open, a DOM move refreshes only the containers it touched, like saved CSS order.

## 2. Reconnect banner wording

**RED.** Fake and real tests: `overrides file already styles the page` and `Accept target state makes Studio drop saved
overrides` not found in the banner.

**Fix.** The banner now says Reapply "sends Studio's saved overrides and tokens to the target, so you can keep editing
them". It says "Accept target state makes Studio drop saved overrides and composition tokens the target does not have,
so the next Sync writes a smaller file; the overrides file only changes when you sync." When the page reports 0 changed
targets but Studio has saved ones, it adds: "If you synced, the overrides file already styles the page, and the bridge
counts only edits made through Studio, so it reports 0 live edits; that is why the page can look right."

**GREEN.** The real test syncs, reloads, reads the banner, then accepts, syncs again and checks the file really shrank.
The fake test shows the 0-live-edits sentence only when the target has none. `test_i2_...` asserted the old
"accept target state ... replace" wording and was updated to the new wording.

## 3. Removed author id

**RED.** Bridge `DemotedTargetTests`: 5 of 6 failed ("the removal was never announced"). Real vs real test: timeout
waiting for an `auto:` id. Studio: no failure.

**Fix.** Bridge `demote(record)`, reusing `promote`. The record moves to an auto id, keeping originals, overrides, change
order, font refs and selection, and the manifest carries `previousId` naming the removed author id. An attribute removal
now schedules rediscovery (an empty id counts as removed). An element nobody edited, with no role and not semantic, stays
a target for arrangement only. Studio needed no code change: `followPromotedTargets` already re-keys by `previousId`, and
the guard that a `previousId` naming a live target is ignored is unchanged.

**GREEN.** Bridge 6 tests (rename to another author id characterised as a promotion). Studio fake tests: saved override
moves to the auto id, the unstable hint returns, no conflict, the file gets the new selector, and a hostile `previousId`
naming a live target moves nothing. Real vs real `DemotedTargetTests` OK.

## 4. Wrong-element edit after an acknowledgement

**Reproduced.** The fake target's new `holdAll` pipe keeps replies in order. Two cases fail against the old Studio, with
the selection stuck on the older target: (a) the user picks a sibling in Studio while a reset acknowledgement is in
flight; (b) the user clicks another element in the page right after the reset. A real-bridge test using a pipe hook
appended to the served script reproduced (b) too (RED against the old Studio: timeout waiting for the lead to be selected).

**Fix.**
- Studio keeps `live.intent`, the user's latest selection (a click, or a request Studio sent for them). Its own
  re-select after a reset, restore, move or bulk manifest goes through `refreshSelection()`, which sends nothing when
  the user picked something else.
- Refresh requests carry a `requestId`. If a refresh reply arrives after the user picked something else, Studio keeps
  the pick and sends `design:select` for it to realign the page.
- All other selection requests go through `requestSelection()`.
- Bridge, additive: `design:select` accepts an optional `requestId` (string up to 100 chars), echoed in the resulting
  `design:selected`. Other values are not echoed.

**GREEN.** `StudioSelectionOrderTests` 3 OK (including the characterisation that a refresh still happens when nothing
else was picked). Real-bridge test OK. Bridge `test_a_select_request_id...` OK (hostile ids not echoed).
**Limit:** an older bridge that does not echo `requestId` keeps the old behaviour.

## 5. Origin lists

**RED.** Four `OriginListTests` failed (mixed-case `data-allowed-origins` refused the real studio; `initFontKitBridge`
never narrowed and only warned "options ignored").

**Fix.** `parseOriginList` lower-cases. A shared `narrowRunningBridge` is used by both the constructor and
`initFontKitBridge`, so init narrows an existing bridge (any state) and never widens it, with the same warning text.

**GREEN.** `OriginListTests` OK (new fixture `target-restricted-upper.html`; hostile origins refused after init narrows;
widening ignored; an empty list ends the session). `InitOptionTests` and `RepeatedConstructionTests` still OK.

## 6. Composition tracking

**Reproduced** (real Studio + real bridge): tracking 0.32em on the wordmark arrived as 0.00032em; the title's -0.025em
arrived as -0.00145px instead of -1.45px.

**Fix.** The bridge contract is thousandths of an em (`/1000`, and an existing bridge test sends 20 for 0.02em), so
Studio now sends `roundTo(tracking * 1000, 3)`. The bridge is unchanged.

**GREEN.** `CompositionSyncTests`: title -1.45px, badge 0.88px, inline values `-0.025em` and `0.08em`. A second test
with float noise (0.035, -0.2+0.1+0.1) gives exactly `0.035em` and `0em`. Both fail against the old Studio.

## 7. Composition Sync loads library-font stylesheets (D021)

**RED.** Bridge `CompositionFontStylesheetTests` (4 tests): the update was not understood or rejected. Studio fake
`StudioCompositionFontTests` (3 tests): no sheets sent, saved CSS had no `@import`, no status. Real vs real test against
the old build: no `link[data-fontkit-font]` in the target.

**Fix.**
- Bridge, additive: a composition `design:update` accepts `fontStylesheets`, a list of at most 16 URLs, each through the
  same strict allow-list as the per-target `fontStylesheet` key. One bad value rejects the whole update with
  `unsupported-value` (`detail.property: "fontStylesheets"`) and changes nothing, not even the tokens.
- The list is the complete set. Dropped sheets are released. A sheet stays while a target or the composition refers to
  it. It appears in `changes.imports`, and reset-all clears it. `canonicalPatch.fontStylesheets` echoes the unique list.
  An omitted key leaves the set alone.
- Studio sends the library fonts of the text slots and row children, in slot order.
- Reapply's token update carries the sheets of the library fonts its saved tokens name. The CSS tab and the synced file
  `@import` them, so a reload still shows them.
- **Rule 7 decision (please confirm).** Sheets are sent only if the user has already asked for free fonts (Load free
  fonts, or an earlier inspector pick). Sync is not one of the actions rule 7 lists as asking. Otherwise the update
  carries no key and the Composer status says: "The target keeps its own fonts until you press Load free fonts, which
  contacts Google Fonts." If you want Sync itself to count as asking, call `allowFreeFonts()` in `syncToLiveApp`.

**GREEN.** Bridge 4 tests, fake 3 tests, real vs real 2 tests (sheets load and appear as `@import`; with no ask, no
link and no request).

## Contract changes (for the plan)

All additive.
1. `ChangeLedger.structure[].orderIds: [targetId]`, parallel to `order`.
2. `design:select` optional `requestId` (string, 1 to 100 chars), echoed in `design:selected`.
3. Composition `design:update` optional `fontStylesheets` (see item 7).
4. Composition slot `tracking` is in thousandths of an em (existing bridge behaviour). Studio now converts.
5. `TargetManifest.previousId` also appears when an author id was removed (target demoted to an auto id).
6. Studio-only: the optional `live.structure` field (`[{selector, name, ids}]`, 1 to 100 entries, 1 to 500 unique ids
   each, selectors up to 2000 chars). It lives in the composition JSON `live` field, so the JSON version stays 0.1.1.

## Doc text I need changed (not edited by me)

- `README.md:135` and the Arrange table (`README.md:154`, "Not saved by Sync"). Replace with: "DOM moves also live in the
  HTML tab. Studio keeps them in its saved state and the `live` JSON, so Reapply puts them back after a reload, but
  Sync does not write them; CSS-order moves are plain CSS (`order`), so they are in the stylesheet." The table row for
  DOM order becomes: "HTML tab (a 'Structure' block). Kept in Studio and replayed by Reapply; not written by Sync."
- `README.md:195`, the Reapply row: add "and DOM-order moves are replayed in order".
- Reconnect banner section (`README.md:~190`): add a paragraph that after Sync and a reload the page may already look
  right (the synced file styles it) while the bridge counts 0 live edits, and that Accept target state makes Studio drop
  saved overrides the page does not have, so the next Sync writes a smaller file.
- `README.md:104`: add that removing an author `data-design-id` moves the edit to an auto id and brings back the
  unstable-selector hint.
- `README.md:416`: add that origins are compared without case, and that `initFontKitBridge({ allowedOrigins })` on an
  existing bridge narrows it like `new FontKitBridge`.
- `README.md:455` (composition row): add `fontStylesheets` (up to 16 allow-listed URLs, the complete set; one bad value
  rejects the update) and that `slots[].tracking` is in thousandths of an em. `README.md:456`: `design:select` takes an
  optional `requestId` echoed in `design:selected`. `README.md:474`: `previousId` also covers removal of an author id.
  Where the ledger is described: `structure[].orderIds`.
- `README.md:594` (Known gaps, D021) and `README.md:215` ("sends font stacks without stylesheets"): replace with "Sync
  to Live App also sends the stylesheets for library fonts, once you have pressed Load free fonts."
- `docs/implementation/deviations.md`: close D021 as fixed in Addendum 7; extend D020 so DOM moves are also saved and
  replayed (a Move anyway move is replayed without force). Record two test edits: `test_i2_...` (banner wording) and
  `test_reapply_states_that_it_resets_a_dom_moved_arrangement` (imports without `structure`).
- Plan Addendum 7: tick the seven boxes and add the contract changes above.

## Gates

Run on the final tree, with `PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`.
Chromium only; Firefox was not run and is not verified.

| Gate | Result |
|---|---|
| `python3 -m unittest tests.test_bridge_runtime` | 114 tests OK (baseline 99) |
| `python3 -m unittest tests.test_studio_live` | 101 tests OK (baseline 89) |
| `python3 -m unittest tests.test_live_integration` | 30 tests OK |
| `python3 -m unittest discover -s tests` | 476 tests OK |
| `python3 scripts/dev/frontend_gate.py --offline --engines chromium` | SUMMARY OK: 15 of 15 runs finished, 6 blocking passed, 0 failed, 1 skipped (free fonts load, skipped by `--offline`); touch-target REPORT lines only |
| `python3 scripts/verify.py --static-only` | PASS: 88 unique IDs, 1 inline JS block, 3 provenance hashes |
| `node --check fontkit-bridge.js` | OK |

Not run: Firefox, the free-fonts-load gate check (needs the network), real Vite/React/Next apps, the commit-message
check (nothing is committed). The Studio suite was also run once mid-way with one failure (`test_i2_...`, old banner
wording), which was fixed and re-run green. No server or browser process of mine is left running.

The owner confirmed the item 7 default: Sync to Live App does not count as asking for free fonts.

## Fix round 1 (2026-10-03)

Studio side (Kerning). Files: `font_kit_studio_v0.1.1.html`, `tests/test_studio_live.py`,
`tests/fixtures/studio/fake-target.html`. Chromium only (`FKS_ENGINES=chromium`); Firefox is not installed and was not
run. RED means the new test failed against the Studio of the first pass; "characterized" means production already did
the right thing and the test now pins it (mutation notes say which edit makes it fail).

Fixture changes (fake target): `orderIds` and `order` now follow the DOM like the bridge's `childElements`; new hooks
`undoMoves` (a page that puts a DOM move back while acknowledging it), `mapStructure` and `extraStructure` (ledger
entries the bridge could report: oversized names, selectors, ids, repeated ids), and `select(id, front)` (a page event
that happened before the replies already in the held pipe).

| Item | RED (first-pass Studio) | GREEN |
|---|---|---|
| K1 | `test_imported_override_fonts_wait_for_the_users_ask`: the CSS tab started with `@import url("https://fonts.googleapis.com/css2?family=Fraunces...`. | CSS tab and synced file carry no `@import` until Load free fonts; the Reapply patch is `{fontFamily}` without `fontStylesheet`; after Load free fonts both appear. Banner, save status and a Reapply status say "The target keeps its own fonts until you press Load free fonts..." (shared constant with the Composer). Load free fonts re-renders the live panels (new `fontkit:free-fonts-allowed` event). |
| K2 | `...clamped_in_the_real_flow`: saved name had 250 characters; variant test: name, selector and id over the limits were saved. | `savedStructureFrom` clamps the name to 200 and skips entries past the selector, id (300), child (500) or repeated-id limits; exports import again. The 100-entry cap is in the code but no test reaches it (a user cannot save more than 100 containers in a test run). |
| K3 | Reset of one child after a page-only reorder saved `live.structure`; re-hello with nothing saved adopted it; Accept adopted it. | Only a user move adds a container. Reset only refreshes or drops saved ones; connect with nothing saved adopts none; Accept keeps saved containers the page holds exactly and drops the rest. The unreachable global-reset branch is deleted (Studio sends no global reset; a comment says what one would need). |
| K4 | With the fake's `orderIds` in DOM order, `test_reapply_keeps_a_saved_dom_move_while_it_clears_a_stale_css_order` timed out waiting for the banner to hide (Reapply's own reset undid the move and the failure blamed the page). | `planStructureReplay` replays any saved container whose group Reapply resets or that holds a reset element; the test now also checks the sequence (reset first, then DOM moves) and that the ledger is in DOM order. |
| K5 | A selector naming another container: failure text was "the page's DOM order still differs..." and nothing said what happened; a missing saved child showed the same text. | A saved container is replayed only if one of its saved children sits in the matched container (else "the container "X" no longer holds any of the elements Studio saved in it", nothing sent). Failure text names the step ("moving "Card B""), includes the bridge's `detail.message`, and says how far Reapply got ("3 of 5 Reapply steps were already applied to the page, so it is partly changed", "All 4 ... applied", "Nothing was changed on the page"). A saved child the page lacks: "a saved child is no longer on the page (card.gone)"; otherwise "the order of "Cards" on the page differs from the saved order even after Reapply moved its elements; something on the page may be changing it again". |
| K6 | Banner and Accept status named only overrides and tokens; "smaller file" always; "0 live edits" whenever 0 changed targets. | Banner and status say Accept "replaces Studio's saved overrides, composition tokens and DOM order with what the page has now"; "smaller file" only when the saved set is a superset of the page's; the "0 live edits" sentence only when the page holds no changed targets, tokens or structure. `test_i2_*` and both Accept tests assert the wording, including DOM order. |
| K7 | The status said the move was "kept in Studio (Reapply puts it back...)" with an older bridge and for a forced move. | The notice is built from `live.structure`: "not saved" (older bridge); "kept in Studio, but Reapply cannot replay a guarded move" (Move anyway). Both asserted. |
| K8 | M7 and M8 survived (see mutation list); M1 and M11 characterized. | New tests: auto-sync on, DOM move: no PUT, and the synced file differs from the file before the move only by the header comment; finishReapply's failure path (`undoMoves`); "page has no container" sends zero moves; previousId re-keys `live.structure` ids. |
| K9 | Characterized (production already did this): last `design:select` names the user's pick; no stale select after a pick; a refresh in flight then Studio pick; Back while a refresh is in flight; `assert_next_edit_goes_to` types with keystrokes and checks the fake's computed font size and the other target. | Mutations c, j and o each fail one of these tests. |
| K10 | Without the ask: characterized (no key, ledger imports `[]`). With the ask: first flow (re-hello, saved token the page lacks) sent 3 sheets while the page held 4 (the Inter sheet would be released). | Reapply with the ask sends the union of the composition's sheets and the saved token sheets, linked or not. Brief said "when a composition is linked"; a re-hello ends the link but the page keeps its sheets, so the condition would release them (the real-bridge test in `test_live_integration.py` rehellos). Two tests: re-hello, and a conflict while linked. |
| K11 | `test_a_click_in_the_page_within_one_round_trip_of_the_realign_is_not_overridden` timed out (the shown target ended on the answer to the realign, not on the later click). | The realign is a tracked request (`sendTrackedSelection`), superseded by a later pick. |
| K12 | `...re_keyed_for_an_id_the_page_never_listed...`: status empty. | "Moved the saved edit for footer.legal to auto.h2.1 because the page reported it."; no PUT without a click. |
| K13 | Characterized. | Studio test types `0.1234` in the Composer tracking field and asserts `123.4` arrives (`0.1234 * 1000` is `123.39999999999999`); mutation p fails it. The integration test `test_tracking_values_with_float_noise_and_the_limits_stay_exact` only proves import normalisation; renaming it is Ligature's file (see notes). |
| K14 | n/a | `release_all` waits for Studio to handle each released reply (a counted message listener); one 60 ms absence window remains for the final "nothing queued" check. |
| K15 | n/a | The DOM-move status says the move "adds no CSS rules (the file only gains a comment that points to the HTML tab)". |

Mutation check on a scratch copy (each edit made one test fail, none survived except as noted): refresh guard (c), no
supersede (j), no realign (o), untracked realign, Reapply always sends sheets (g2), token-only sheets (g3, g4), no
roundTo (p), DOM move auto-syncs (M1), structureHeld off (M7), missing-container branch off (M8), no structure re-key
(M11), liveImports ungated, Reapply fontStylesheet ungated, no name clamp, no selector/id limit, repeated-id check
off, reset adds containers, Accept adopts, connect adopts, no reset replay, no holds-none check, no gone-child
message, no progress sentence, no detail message, shrink always, 0-live-edits condition, kept always, force ignored,
no re-key status. Survivors: the 100-entry cap and a repeated-selector check. The selector check was deleted (the
merge in `syncStructureFromLedger` already keeps one container per selector); the cap is kept because the brief names
it, and is untested.

Decision to confirm: K10 sends the composition's sheets in Reapply whether or not the composition is linked (above).

Gates (final tree, Chromium only): `python3 -m unittest tests.test_studio_live`: Ran 125 tests, OK (first-pass
report: 101). `python3 scripts/verify.py --static-only`: PASS (88 unique IDs, 1 inline JS block, 3 provenance
hashes). Not run here: the full discover suite, the frontend gate, Firefox. No server or browser process of mine is
left running.

## Fix round 2 (2026-10-03)

Studio side (Kerning). Files: `font_kit_studio_v0.1.1.html`, `tests/test_studio_live.py`,
`tests/fixtures/studio/fake-target.html`. Chromium only (`FKS_ENGINES=chromium`); Firefox is not installed and was not
run. Mutations were made on the live file and restored byte for byte (checked with `cmp`).

| Item | RED | GREEN |
|---|---|---|
| K1-wording | `test_imported_override_fonts_wait_for_the_users_ask` asserting the new sentence failed against the old banner text ("The target keeps its own fonts until you press Load free fonts..."). | The shared note now reads "Library fonts are not loaded until you press Load free fonts, which contacts Google Fonts; until then the page shows each font stack's fallback." It is the one constant behind the reconnect banner, the Reapply status, the sync-to-file status and the Composer sync status. The banner test also asserts the old claim is gone; the Reapply and save-status assertions now require the "fallback" half. Comments that said the page "keeps its own fonts" now say it shows the stack's fallback. The Ligature tests only match "Load free fonts", so they need no change. |
| K4-residual | Characterized (production already did the right thing); new `test_reapply_moves_a_reset_element_back_into_its_saved_container`: a CSS-order move, then a move into Sidebar, leaves a stale order on the moved element; saved state holds Sidebar `[side.x, side.y, card.a]` and no order; Reapply resets it (the reset returns it to Cards) and must replay it by container. Dropping `&& !resetIds.has(id)` makes it fail (Reapply never finishes: the element is sent as `{index}` and stays in Cards, so the banner stays). | The clause is reachable and kept. The test asserts the replayed move is `{container: <sidebar>, index: 2}` and the DOM ends `[side.x, side.y, card.a]` with Cards without it. |
| K2-residual (a) | New `test_saved_dom_order_holds_at_most_one_hundred_containers` (fake hook `priorStructure`: containers the page reports before the user's move). 99 older ones: the move is saved; 100 older ones: it is left out, and the export imports again. Removing the 100-entry cap fails the 100 case. | Cap is now tested at its boundary. |
| K2-residual (b) | Equivalent mutant: `list.length > MAX_STRUCTURE_IDS` was redundant with `list.length !== entry.order.length` (the ledger keeps 500 names and 501 ids). | Clause removed; the comment says the length check rejects a container with more than 500 children. Removing the length check now fails `test_saved_dom_order_never_holds_what_the_import_would_refuse` (variant "more children than the import takes"), so that check carries the limit. The earlier report line that the child-count mutation was killed referred to a different edit; this is the right one. |

Fixture: `fake.priorStructure` (ledger entries listed before the page's own), documented next to `extraStructure`.

Gates (final tree, Chromium only): `python3 -m unittest tests.test_studio_live`: Ran 127 tests, OK.
`python3 scripts/verify.py --static-only`: PASS (unique IDs, inline JS, 3 provenance hashes). Not run here: the full
discover suite, the frontend gate, Firefox. No server or browser process of mine is left running.
