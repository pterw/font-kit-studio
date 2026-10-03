# Review: Addendum 7, known-limit fixes

Verdict: **Approved with fixes**. Nothing blocks, but eleven should-fix items and a
list of nits must go through one fix round and a scoped re-review before the commit.
All seven Addendum 7 items work in their main flow. The defects sit in edge
combinations, in user-facing wording, in one Rule 7 path that this work left open,
and in tests that would stay green if the feature were deleted.

Date: 2026-10-03.

## Scope and base

- Branch `ccr-9eab25c9-mgatzt`, HEAD `4b539cf`. The work under review is the working
  tree against HEAD: `font_kit_studio_v0.1.1.html`, `fontkit-bridge.js`,
  `tests/test_bridge_runtime.py`, `tests/test_live_integration.py`,
  `tests/test_studio_live.py`, `tests/fixtures/studio/fake-target.html` (6 files,
  +1523 / -70) plus the untracked `tests/fixtures/bridge/target-restricted-upper.html`
  and the implementer report `docs/implementation/tasks/v02-addendum-7-report.md`.
- The report names `18856ac` as its base. Five docs-only commits landed after it
  (ending at `4b539cf`); none touches code, so the diff is unaffected.
- `docs/implementation/deviations.md` also shows a working-tree change: the new
  **D032** row. It matches the controller's ruling recorded below. It is not part of
  the code under review.
- Plan section: "Addendum 7 -- known-limit fixes (2026-10-03)" in
  `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md`. Rulings read: D016, D020,
  D021, D028, D031 (and D032).
- Engine: Chromium only. **Firefox is not installed here and was not run.** The
  review was done by three independent dimension reviews (structure and Rule 6;
  trust boundaries and network; state correctness and test quality), each finding
  re-checked by an adversarial verifier. This file is the merged verdict.

## Gates

Run on the final working tree by the gate runner. Not re-run for this review.

| Gate | Result |
|---|---|
| `python scripts/verify.py --static-only` | PASS: 88 unique HTML IDs, 1 inline JS block, provenance PASS for 3 `supplied-v0.1.1` blobs |
| `node --check fontkit-bridge.js` | PASS |
| `python -m unittest discover -s tests -v` (Chromium) | `Ran 476 tests in 454.212s` / `OK` |
| `frontend_gate.py --engines chromium --offline` | `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped.` Skipped: free fonts load (`--offline`). 140 REPORT lines: one light-theme contrast report (`span.tag`, 4.30:1) and 138 touch-target lines (phone and wide touch, advisory) |
| `frontend_gate.py --engines chromium` (online) | `SUMMARY FAIL`, one FAIL: `free fonts load [desktop, chromium]`. See below |
| `check_commit_messages.py --range origin/main..HEAD` | `OK: 29 commits checked` (this work is not committed, so it is not covered) |

**Free-fonts check: not verified here.** The gate's headless Chromium is launched
without this session's proxy, so it cannot reach Google Fonts. A direct request
through the proxy reached `fonts.googleapis.com` (HTTP 200), so the network is up;
the check is an environment limit of this sandbox, not a code failure and not an
outage. CI runs the gate online. Until CI has run it, the free-fonts load check is
reported as not run.

Not run at all: Firefox (unit suite and gate); the advisory phone and wide-touch
profiles on Firefox; real Vite, React or Next apps.

Run by the leading reviewer for this verdict (Chromium, `PYTHONPATH=tests`):
`tests.test_studio_live.StudioFixRound1Tests.test_i2_studio_overrides_are_persisted_and_accept_is_explicit`,
`tests.test_studio_live.StudioArrangeTests.test_reapply_states_that_it_resets_a_dom_moved_arrangement`,
`tests.test_studio_live.StudioArrangeTests.test_reapply_keeps_a_saved_dom_move_while_it_clears_a_stale_css_order`,
`tests.test_bridge_runtime.MoveTests.test_ledger_structure_reports_changed_containers_and_reset_restores_the_order`:
`Ran 4 tests in 6.374s` / `OK`. I also re-read every cited `file:line` in the Studio
file against the tree (all matched) and confirmed in the bridge and the fake target
that `orderIds` follows DOM order in the bridge (`fontkit-bridge.js:1569-1575`) and
visual order in the fake (`fake-target.html`, `visualSiblings`). That difference is
what hides R3.

## Controller rulings recorded here

1. **Imported override fonts reach Google (R1).** The owner delegated the call; the
   controller ruled option (a): override-derived library-font sheets are gated on the
   free-fonts ask, like the token path. Recorded as **D032**: importing or applying a
   document does not count as asking for free fonts. Basis: D028 and D031 already list
   the asking actions; a JSON document can come from someone else; the ask is
   remembered per browser, so returning users are unaffected.
2. **Replay failure wording and Accept wording (R4, R5)** were downgraded to nit by
   the verifier. The controller sends their cheap parts to the fix round as required:
   Accept's wording is the core of Addendum 7 item 2, and R4's container guard stops
   Reapply re-parenting saved children into a container the page no longer owns
   (Rule 6).
3. **One defect, not three (R7):** Studio exports `live.structure` that its own
   import refuses (found three times, in two dimensions).
4. **One defect, not two (R8):** Reapply's composition update replaces the sheet set
   with token sheets only (found twice).
5. All remaining nits go to the fix round when cheap. The pacing waits stay a nit
   and the duplicated drain helper stays duplicated (two copies, rule of three).
6. The fix round is split by file ownership: the **Studio implementer** owns
   `font_kit_studio_v0.1.1.html`, `tests/test_studio_live.py` and the fake target; the
   **bridge implementer** owns `fontkit-bridge.js`, `tests/test_bridge_runtime.py`,
   `tests/test_live_integration.py`, `tests/support.py` and `tests/fixtures/bridge/`.
   Where a Studio fix needs a real-bridge test, the bridge implementer writes the
   failing test first and the Studio implementer then makes it pass.

## Addendum 7 items

### 1. DOM-order moves survive a reload: met, with fixes (R2, R3, R4, R6, R7, R9)

Works in the normal flow. Real Studio plus real bridge on the demo: a DOM move is
saved as `live.structure`, survives Sync and reload, and an explicit Reapply puts it
back; the HTML tab keeps its Structure block (probe A, and
`ArrangeTests.test_a_dom_move_survives_sync_and_reload_through_an_explicit_reapply`).
Auto-sync wrote nothing after a DOM move (probe F1: no write over 1.2 s; the synced
file differed only by the header comment that already exists at HEAD).

Rule 6, push direction, was probed in both handshake orders (import before connect,
connect before import), then reload, hash navigation and Accept (probe H1, H2): the
bridge revision stayed 0, the DOM did not change, nothing was sent. Reapply and Accept
are the only senders. A crafted import that moves a form submit button into another
container was rejected by the real form-owner guard, with the page unchanged (probe I1).

Defects: Reset can save a container that only the page reordered (R2); Reapply can
undo the saved move with its own stale-order reset and then fail on the first press
(R3); replay failures say too little and a selector that now matches a different
container receives the saved children (R4); the status line promises Reapply will
restore a move in two cases where it will not (R6); Studio's own export can be
refused by its own import (R7); several new branches have no failing test (R9).

### 2. Reconnect banner wording: met for the 0-live-edits case, with a fix (R5)

The banner explains that a synced file already styles the page while the bridge
counts 0 live edits, and says Accept makes Studio drop saved overrides so the next
Sync writes a smaller file. The claim is real:
`SyncAndReloadTests.test_the_banner_after_sync_and_reload_explains_zero_live_edits_and_what_accept_does`
syncs, reloads, accepts, syncs again and asserts the 56px rule is gone and the file is
shorter. But the banner and the Accept status say nothing about the saved DOM order
that Accept also drops, and the "drop ... smaller file" sentence is only true when the
page holds fewer edits than Studio. See R5.

### 3. Removed author id: met

`demote(record)` reuses `promote`. Probes: edit, remove the id, re-add the id, reset
all gives the original text and style back (originals are captured once, per
element); change-order place, font-stylesheet reference and selection follow the new
auto id; remove and re-add in one tick is not a demotion; an empty id counts as
removed; a removed element takes the normal removal path with no page errors; the
bridge's own attribute writes do not re-trigger discovery; the ledger HTML never holds
bridge attributes. Studio re-keys the saved edit through `previousId`, shows the
unstable-selector hint again and raises no conflict (fake tests). Open points are
test gaps (R9, R11) and nits (N3, N5).

### 4. Wrong-element edit after an acknowledgement: met, with test gaps (R10)

Reproduced first against the old Studio with an ordered reply pipe; the real-bridge
test types keystroke by keystroke and asserts the computed font size on the lead. Every
`design:select` Studio sends now goes through `requestSelection` or `refreshSelection`
(grep: no direct sends). Replies that cross converge without a realign loop. The
production code is correct; two of its three guards are not pinned by any test (R10).

### 5. Origin lists: met, no findings

Mixed-case `data-allowed-origins` now matches the lower-case browser origin; trailing
slashes are stripped; `:80` and path variants fail closed. `initFontKitBridge` narrows
an existing bridge in any state and never widens it; `'*'`, `new FontKitBridge('*')`,
`[null]` and odd option types change nothing; `''` or `[]` narrows to empty and fails
closed; a Studio at an excluded origin loses its session and is refused afterwards.
The bridge stays inert before a valid hello (the observer exists only after
activation).

### 6. Composition tracking: met

Root cause confirmed: the bridge contract is thousandths of an em (an existing bridge
test sends 20 for 0.02em) and Studio sent em. Studio now sends
`roundTo(tracking * 1000, 3)`; the bridge is unchanged. Division is exact for every
3-decimal value from -0.2 to 1 (the UI step is 0.005) and for zero and negative zero.
The Composer CSS and composition JSON still hold em, so exports stay compatible.
Remaining: a test-name overclaim and float noise for 4-decimal imported values (N6).

### 7. Composition Sync loads library-font stylesheets (D021): met, with fixes (R1, R8)

The bridge side is sound. `fontStylesheets` uses the same `safeFontStylesheet`
allow-list as the per-target key: a 43-URL hostile corpus (`javascript:`, `data:`,
userinfo, look-alike hosts, CR/LF, `file:`, `blob:`, protocol-relative, odd Typekit
forms) produced zero parity differences. More than 16 entries, non-strings, nested
values and objects reject the whole update with `unsupported-value`, the revision does
not move, and tokens do not change either. Reference counting across two targets plus
the composition, reset-all and the `canonicalPatch` echo were verified.

D031 holds for Sync and for token fonts: with no ask, Composer Sync sent no sheet,
wrote no `@import` and made no request, and a reload made none either; after
**Load free fonts**, 4 links loaded, 4 requests were made and 4 `@import` lines were
listed. One sibling path was left open (R1), and Reapply can release sheets that a
Sync loaded (R8).

## The three changed existing tests

| Test | Change | Ruling |
|---|---|---|
| `tests/test_bridge_runtime.py::MoveTests.test_ledger_structure_reports_changed_containers_and_reset_restores_the_order` | Key set gains `orderIds`; four assertions added (ids equal the arrangement sibling ids in order, first id `arr.p.3`, lengths match `order`) | Justified. An additive contract change; the old intent is kept and strengthened. Renaming `orderIds` turns it red. |
| `tests/test_studio_live.py::test_i2_studio_overrides_are_persisted_and_accept_is_explicit` | Banner regex `accept target state.*replace` became `accept target state makes studio drop saved overrides` | Justified by Addendum 7 item 2, but it must change again with R5. The new regex pins wording that omits DOM order and is weaker on what Accept does (the old pattern checked "replace"). After R5 it must pin the corrected sentence and name DOM order. |
| `tests/test_studio_live.py::StudioArrangeTests.test_reapply_states_that_it_resets_a_dom_moved_arrangement` | Imported JSON now deletes `live.structure` | Justified. Studio's export now holds the DOM move, so the old scenario needs saved state without it. Intent kept. The new companion `test_reapply_keeps_a_saved_dom_move_while_it_clears_a_stale_css_order` is not vacuous, but it passes only because the fake reports `orderIds` in visual order; the real bridge fails the same scenario (R3). |

No changed test hides a regression. Two of the three need follow-up edits in the fix
round.

## Required fixes

All are should-fix. Each starts with a failing test, in the file named. Where the item
is a test gap, the failing evidence is a one-line mutation of the production code that
must turn the new test red (the implementer runs it and records the result).

### R1. Imported override fonts reach Google without an ask (Rule 7, D032)

- Where: `font_kit_studio_v0.1.1.html:4806-4815` (`liveImports`, override loop) and
  `:3885-3890` (Reapply sets `patch.fontStylesheet` for library fonts), against the
  gate that exists at `:5094-5103` (`tokenFontSheets`).
- Evidence: real Studio plus real bridge, nothing stored under `fontkit-free-fonts`.
  Import a document whose override names Fraunces and whose token names Instrument
  Serif. The CSS tab and the file written by Sync begin with
  `@import url("https://fonts.googleapis.com/css2?family=Fraunces...")`; the token font
  wrote no `@import`. Reloading the target then requested that URL, and Reapply
  requested it too and added a `link[data-fontkit-font]`. Studio itself made no request.
  The override loop is identical at HEAD, so this predates Addendum 7, but the new D031
  gate covers only one of two sibling paths (anti-pattern 12).
- Fix: gate override-derived sheets in `liveImports()` and in Reapply's per-target
  update on `freeFontsAllowed`. When the ask is missing, omit the `fontStylesheet` key
  (do not send `null`, which would release a sheet). Say in the status that the page
  keeps its own font until Load free fonts. Update D028 and D031 text only through the
  controller's D032.
- Tests first: (bridge implementer, `test_live_integration.py`, real vs real) import
  naming a library font in an override and a token with no ask: CSS tab and Sync file
  have no `fonts.googleapis.com`, reload and Reapply make no request to it; after
  **Load free fonts** the `@import` appears and the request is made. (Studio
  implementer, `test_studio_live.py`, fake) Reapply without the ask sends no
  `fontStylesheet` on override updates and no `fontStylesheets` on the composition
  update, and the ledger imports stay `[]`. This also closes the missing negative
  test for the Reapply path (mutation `compositionFontSheets()` always sent survived).

### R2. Containers only the page reordered get saved by a Reset (Rule 6)

- Where: `font_kit_studio_v0.1.1.html:3686-3702` (`syncStructureFromLedger`); report
  section 1 claims such containers "are never saved".
- Evidence: real Studio plus real bridge on the demo. The hero text container was
  reordered with the bridge's own `captureOrder`, as a composition sync does. The user
  then only edited the title size and pressed Reset. The export then held
  `live.structure=[{selector:'#top > section.hero ... > div:nth-of-type(1)', ids:[...]}]`.
  The cause: the Reset adds the target's container to `touched`, and the real bridge's
  single-element reset leaves a composition-reordered container in the ledger. The
  fake's reset restores the container, so the fake cannot show it. The saved container
  later raises a reconnect banner and a replay the user never asked for. Nothing is
  written by Sync, so impact is limited.
- Fix: only a user move (`op.kind` is `move` and not `reapply`) may add a container to
  `live.structure`. A Reset may only drop or refresh containers that are already
  saved. Adoption on connect and Accept stay as they are: adopting the page's state
  matches how overrides and tokens are adopted. Correct the code comment at `:3686`
  and the report claim so they say "a Reset or a composition sync never adds a
  container".
- Tests first: (bridge implementer, `test_live_integration.py`, real vs real)
  reverse a container's children as a composition sync does, edit a child elsewhere,
  Reset, export: no `live.structure`. (Studio implementer, fake) the same, with a
  fake switch that makes Reset leave the container reordered.

### R3. Reapply can undo the saved DOM move with its own stale-order reset

- Where: `font_kit_studio_v0.1.1.html:3982-3999` (`planStructureReplay` skips a
  container whose ledger ids already equal the saved ids) against `:3853-3890` (resets
  are sent first); failure text at `:3918`; fake `orderIds` in
  `tests/fixtures/studio/fake-target.html`.
- Evidence: real vs real. Move the CTA by DOM, then by CSS order, export, import with
  overrides replaced (a stale CSS order remains, saved structure kept), press Reapply.
  The first press reset the CTA (it carries the stale order), which also undid the
  saved DOM order; the plan had already skipped the container because the real
  ledger's DOM-order `orderIds` equalled the saved ids. Result: DOM order
  `['Start your free trial','See how it works']` and the status "Reapply stopped (the
  page's DOM order still differs from the order Studio saved; the page may have changed
  it again)". A second press succeeded. The banner's reset notice did not warn either.
  The new companion test passes only because the fake reports `orderIds` in visual
  order. No saved state is lost, so should-fix.
- Fix: in `planStructureReplay`, always replay a saved container that holds a child of
  a group Reapply resets (as `reapplyOrders` does with its reset groups). Make the
  fake's `orderIds` follow DOM order like the bridge. Reword the failure so it does not
  blame the page for Reapply's own reset. Make the reset notice say when the move is
  saved and will be replayed.
- Tests first: (Studio implementer) change the fake to DOM-order `orderIds`: the
  existing companion test then fails, which is the RED. (bridge implementer, real vs
  real) the scenario above must succeed on the first press with the saved order in
  place.

### R4. Replay failures are vague, and a container that now matches a different element receives the children

- Where: `font_kit_studio_v0.1.1.html:3772-3781` (`the target rejected it: <reason>`),
  `:3938-3946` (`failReapply`), `:3910-3920`, `:3961-3999` (`containerKeyForSelector`,
  `planStructureReplay`).
- Evidence: fake, guard on `card.b`: Reapply stops half-way (cards `d,c,a,b`, title
  already 40px) with only "the target rejected it: unsupported-value": no element, no
  container, no guard message, no word that the page was partly changed. Real bridge:
  after save and reload the app changed so the saved auto selector matched a decoy
  `.actions`. Reapply moved both original buttons out of the real container into the
  decoy, then said "the page may have changed it again", which blames the page for
  Reapply's own moves. A saved child that no longer exists makes every press stop with
  the same text. The verifier called this a nit (the reason code is the existing
  contract; unstable selectors are labelled by D016); the controller sends the cheap
  parts as required.
- Fix: (a) name the element or container and the bridge's `detail` message in the
  failure text and say how many replay steps were already applied. Tell "a saved child
  is no longer on the page" apart from "the order changed again". (b) Before sending
  a container's moves, require that at least one saved id currently sits in the matched
  container; otherwise treat the container as missing and send nothing.
- Tests first (Studio implementer, `test_studio_live.py`, fake): a selector that now
  matches a container holding none of the saved ids sends no move and says the
  container is missing; a guard rejection names the element and the reason and says
  that earlier steps were applied.

### R5. Banner and Accept status do not say what Accept drops (Addendum 7 item 2)

- Where: `font_kit_studio_v0.1.1.html:4051-4062` (banner), `:4016-4017` (Accept
  status).
- Evidence: structure-only saved state, 0 overrides: the banner says "Accept target
  state makes Studio drop saved overrides and composition tokens the target does not
  have, so the next Sync writes a smaller file". Accept in fact drops the saved DOM
  order (probe H1: the saved `live` is `None` afterwards), no file gets smaller because
  DOM moves are never in the file, and where the target holds a different value Accept
  replaces it rather than drops it. The Accept status names only overrides and tokens.
- Fix: say in the banner and in the Accept status that Accept replaces Studio's saved
  overrides, composition tokens and DOM order with what the page has now. Keep the
  plan's "drop ... smaller file" sentence, but only where it is true (the page holds
  fewer edits than Studio's saved set).
- Tests first: update `test_i2_...` to pin the corrected sentence and DOM order (keep
  the old `replace` meaning in the pattern); add a banner-text assertion to
  `test_accept_target_state_drops_saved_dom_moves` (Studio implementer, fake) and name
  DOM order in the real banner test (bridge implementer).

### R6. DOM-move status promises a restore that will not happen

- Where: `font_kit_studio_v0.1.1.html:3733-3747` (`domMoveNotice`).
- Evidence: (a) fake with `?noOrderIds=1` (an older bridge): after a DOM move the
  status says "The move is kept in Studio (Reapply puts it back after a reload)" while
  the export holds no `live` field. (b) A move made with **Move anyway** (`op.force`)
  is saved from the ledger but replayed without `force`, so the bridge guard rejects
  it and Reapply stops; the status still says Reapply puts it back (probe on the fake
  with a framework guard). The report records both limits; the user-facing text
  contradicts them.
- Fix: build the notice from what was saved. Say "kept" only when `live.structure`
  now holds the container. For an older bridge say that this target's bridge cannot
  report child ids, so the move is not saved. For a forced move say it is kept in
  Studio but Reapply cannot replay a guarded move.
- Tests first (Studio implementer, fake): assert the status text in
  `test_a_bridge_without_order_ids_saves_no_dom_moves`; add a `fake.guards` plus Move
  anyway case that reads the status line.

### R7. Studio's own export can be refused by its own import

- Where: `font_kit_studio_v0.1.1.html:3186-3213` (`parseLiveStructure` limits: name
  200, id 300, selector 2000, 500 ids, 100 entries) against `:3217-3225`
  (`savedStructureFrom`) and `:3296-3315` (`normalizeLedger`); the bridge's
  `containerName` returns an author `data-design-name` unshortened
  (`fontkit-bridge.js:2521-2527`).
- Evidence: a 250-character `data-design-name` on the cards container plus one DOM
  move. The export holds a 250-character name; importing that same file fails with
  "Import failed: live.structure[0].name must be a text of at most 200 characters." The
  whole document is refused, overrides and tokens included. Ids are capped at 300 by
  the bridge so they match; a selector over 2000 characters or more than 100 saved
  containers would fail the same way (code path). A container with more than 500
  children is cut to 500 by `normalizeLedger`, passes the length-equality check and is
  saved as if complete. The trigger is unusual and the import fails closed, so
  should-fix, not blocking.
- Fix: in `savedStructureFrom`, clip `name` to 200; skip (do not save) a container
  whose selector exceeds 2000 characters or whose child count is cut at 500; cap the
  list at 100 entries.
- Test first (Studio implementer, fake): export then import round trip with a
  250-character container name, and with a container over 500 children.

### R8. Reapply's composition update replaces the whole sheet set with token sheets only

- Where: `font_kit_studio_v0.1.1.html:3895`; bridge `setCompositionSheets`
  (`fontkit-bridge.js:~1668`). The list is the complete set by contract.
- Evidence (code path, not reproduced end to end): Sync sends the sheets of every text
  slot and row child; Reapply sends only the sheets of fonts named by saved tokens (at
  most four roles). A slot-only family loses its `<link>` while its elements keep the
  inline font. Reachable only when Reapply runs on a page that still holds the Sync's
  sheets (a re-hello or an import conflict without a reload); the next Sync restores
  them.
- Fix: send the union of `compositionFontSheets()` and `tokenFontSheets()`, subject to
  the R1 gate, or omit the key.
- Test first (Studio implementer, fake): after the ask, Reapply's composition update
  still carries a slot-only sheet.

### R9. New structure behaviours that no test would miss

- Where: `font_kit_studio_v0.1.1.html:3733-3736` (a DOM move must not call
  `scheduleAutoSync`), `:3918` (the `structureHeld` check in `finishReapply`),
  `:3865-3870` (a missing container sends nothing), `:4774-4777` (`previousId` re-keys
  `live.structure` ids), `:3631-3634` (reset-all branch of `syncStructureFromLedger`).
- Evidence: on a private copy, four one-line mutations each left 37 targeted tests
  green: a DOM move also schedules auto-sync; the `structureHeld` check disabled; the
  "page has no container" branch disabled; the `previousId` re-key of structure ids
  disabled. Mutations that were caught: non-conflict mirroring, import, Accept, the
  reset notice. A grep over `tests/` finds no assertion on "has no container", "DOM
  order still differs", "cannot be placed" or "may have changed it again". The
  real test's "Sync writes no new kind of content" is only `assertNotIn('order:', ...)`.
  The reset-all call is unreachable from the UI (the only two `kind:"reset"` senders,
  `:3879` and `:4374`, both set `targetId`).
- Fix: add the tests below; drop the unreachable reset-all call or leave a comment
  saying why it stays.
- Tests: auto-sync on, DOM move, assert no PUT within a short absence window (an
  allowed short wait); a missing container sends zero messages and states why; the
  `finishReapply` structure failure; `previousId` re-keys the structure ids; the synced
  file is byte-equal before and after a DOM move apart from the existing header
  comment. Each new test must fail under its mutation. (Studio implementer for the
  fake tests, bridge implementer for the real byte-equal test.)

### R10. Selection-order guards are not pinned

- Where: `font_kit_studio_v0.1.1.html:4121` (realign after a superseded refresh),
  `:3525-3542` (`refreshSelection` guard, `requestSelection` superseding);
  `tests/test_live_integration.py:482-512`, `tests/test_studio_live.py:3053-3135`.
- Evidence: deleting the realign line leaves all 4 selection tests green. A probe built
  from the real-bridge scenario printed `STUDIO landing.hero.lead BRIDGE
  landing.hero.lead` on the baseline and `STUDIO landing.hero.lead BRIDGE
  landing.hero.title` on the mutant: the page stays selected on the stale target. The
  test asserts only Studio's inspector and the outgoing update. Reducing the
  `refreshSelection` guard to `if (!targetId) return;` also stays green; the fake then
  received `[('card.b',None),('card.a','fks-sel-1'),('card.b',None)]` instead of
  `[('card.b',None)]`, so a stale `design:select` is sent. (The mutation that stops
  `requestSelection` from superseding outstanding refreshes can only be killed by a
  transient-state assertion; treat that part as optional.)
- Fix: tests only.
- Tests: (bridge implementer, real vs real) assert `window.__fontkitBridge.selectedId`
  is `landing.hero.lead` after the pipe drains. (Studio implementer, fake) assert that
  no `design:select` for the stale target was sent after the pick; add a case that
  holds replies, releases the reset acknowledgement so the refresh goes out, then
  picks another target or presses Back, and assert the next edit goes to the pick.

### R11. Demote's arrangement-only branch is not tested

- Where: `fontkit-bridge.js:2149-2156`; `tests/test_bridge_runtime.py:1391-1402`.
- Evidence: setting `const ordinary` to `true` or to `false` leaves 7 demote tests
  green. The only demote test removes the id from `LEAD`, a semantic `<p>`. A probe on
  the unedited `<span>` `landing.stat.badge` gives `arrangementOnly: true`, which the
  report claims but no test asserts; with `false`, an edited target becomes
  arrangement-only and drops out of the picker, hover and click.
- Fix: tests only.
- Tests (bridge implementer): an unedited non-semantic span without a role gives
  `arrangementOnly: true` after its id is removed; the same span after an edit, or
  with `data-design-role`, or a semantic element, stays an ordinary target in
  `design:targets` and `design:ready`.

## Nits

All go to the fix round when cheap. Studio file unless a bridge file is named.

- **N1.** `font_kit_studio_v0.1.1.html:4054`: the "0 live edits" sentence fires on
  `count && !targetCount` (changed targets only), so a page that holds tokens or DOM
  order but no changed targets still gets it. Say "0 changed targets" or also require
  no held tokens or structure.
- **N2.** `:4824-4826`: after a DOM move the synced file gains the existing header
  comment, so "Sync writes nothing new" is not byte-true. Word the claim as "no new CSS
  rules" (plan item 1 and the report).
- **N3.** `:4770-4790` (`followPromotedTargets`): a manifest can re-key a saved
  override whose id was never live (`previousId: 'footer.legal'` moved a saved
  override to `auto.h2.1`, no file write, auto-sync blocked by the conflict flag). The
  live-id guard holds, and an imported old-id state is the documented legitimate case,
  so do not require that the id was seen. Add a status line when a re-key happens and a
  hostile test for a non-live, never-seen saved id (`test_studio_live.py:2829-2866`).
- **N4.** `font_kit_studio_v0.1.1.html:4121`: the realign `design:select` carries no
  `requestId`, so a page click that lands within one round trip is overridden (Studio
  and page still agree). Send it with refresh-style tracking.
- **N5.** `fontkit-bridge.js:2153` and `:2296`: after demote and re-add, bridge-written
  `data-design-role` and `data-design-name` stay in the live DOM, and `demote` and
  `registerSibling` use `hasAttribute('data-design-role')` where `registerAuto` uses
  `authorAttr`. Use `authorAttr` in both; optionally drop bridge-written role and name
  on promote. (The ledger HTML stays clean; text and style restore correctly.)
- **N6.** `font_kit_studio_v0.1.1.html:5057`, `tests/test_live_integration.py:585-607`:
  the float-noise tracking test cannot reach the send-side rounding (removing
  `roundTo` stays green, because the import normalises). Four-decimal values from a
  JSON import still reach the bridge noisy: `-0.1969` becomes
  `-0.19690000000000002em` in the ledger and the synced file (rendering is identical).
  Rename the test or drop `roundTo`; for tidy files, round the em value in the bridge
  after the division (`fontkit-bridge.js:3034`).
- **N7.** `tests/test_studio_live.py:3080-3087`: the selection-order fake tests assert
  the outgoing message and the inspector name, and use `fill()` for the final edit.
  Also assert `fake.styleOf(target_id)` shows 23px and the other target is unchanged.
- **N8.** `tests/test_studio_live.py:3066-3075`, `tests/test_live_integration.py:495-504`:
  `wait_for_timeout(60)` and `(30)` in the reply drain loop. Pacing, not an
  absence-check proof; a premature exit can only weaken a test, never fail it falsely.
  Left as a nit by ruling; the helper stays duplicated (two copies).

## Raised and refuted

No finding was refuted in full. These parts did not survive verification:

- Structure S1, adoption paths: adoption of the whole ledger on connect with nothing
  saved, and in Accept, matches how overrides and tokens are already adopted. Not
  defects. R2 rests on the Reset path alone.
- Structure S6, ids: the id half of "ids over 300 characters fail import" does not
  hold, because the bridge caps ids at `MAX_ID_LENGTH = 300`, equal to Studio's limit.
  Only name, selector and count remain (R7).
- State T2, the superseding half: a `requestSelection` that stops superseding
  outstanding refreshes is close to equivalent for the final state, because bridge
  replies arrive in order. Only the stale-send half is required (R10).
- Pacing waits (State T5): downgraded to a nit (N8).

## Cleared risks

- **Rule 6, both directions.** Studio sends nothing on connect, reload, hash
  navigation, import or Accept; Reapply is the only sender. Replayed moves go through
  the normal move path without `force`, so the bridge's form-owner guard held with the
  page unchanged. Radio, label and aria guards use the same code path (not separately
  probed). The framework-managed guard is the recorded limit.
- **Untrusted structure data.** A crafted `live.structure` (11 hostile shapes: wrong
  types, over 100 entries, over 500 ids, duplicate ids and selectors, a 201-character
  name, null entry, object ids, null structure) is refused transactionally with the
  export unchanged. `__proto__` and `constructor` keys and ids are inert. The selector
  is never evaluated or used as CSS or markup: Studio compares it as a string and the
  bridge resolves the container by key, so `:has()`, `*`, `html` and `script`
  selectors only fail to match. Text is rendered through `textContent`.
- **Stylesheet allow-list.** Parity with the per-target key over a 43-URL corpus;
  atomic rejection; limit of 16; reference counting; reset-all; `canonicalPatch` echo;
  an omitted key leaves the set alone and `[]` clears it.
- **`requestId` on `design:select`.** Only strings of 1 to 100 characters are echoed.
  Markup text and `__proto__` are echoed as inert strings and used in Studio only as a
  Map key. Replies go through the pinned origin. Studio's handling is bounded (refresh
  map capped at 20, one corrective select per superseded reply).
- **Anti-pattern 6 under demote.** Originals are keyed by element and captured once;
  demote moves only record-keyed state. **Anti-pattern 7:** the demotion observer
  exists only after activation.
- **Rule 7 for Composer Sync, reload and the token path.** No Google contact before
  the ask; after the ask the sheets load. Studio itself never contacts Google.
- **Test quality that holds.** Real Studio plus real bridge covers each new boundary
  (DOM move and Reapply, banner and the file shrinking, demote, selection order,
  tracking, sheets with and without the ask). Hostile cases exist for origins,
  `requestId`, sheet lists, structure imports and `previousId` naming a live target.
  Reapply, Accept and the banner count are asserted by what the page then rendered,
  not by messages alone. No fixed sleep stands in for a condition apart from N8.
- **Recorded limits, not findings:** Move anyway replayed without force (its text is
  R6); mixed CSS and DOM order replaying by visual index; empty containers; an older
  bridge keeping the old selection behaviour; a DOM move while a conflict is open
  refreshing only the containers it touched.

## Probes behind this verdict

Run for this verdict (leading reviewer): the four targeted tests above, the
`file:line` re-read of 12 Studio ranges, the bridge and fake `orderIds` comparison, and
the doc-drift greps below. Nothing in the repository was edited apart from this file;
git state was not touched; no server or browser of mine was left running.

Run by the dimension reviews and verifiers (Chromium, scratch copies of the tree
outside the repository, all cleaned up): real-vs-real probes for a composition-sync
reorder followed by a Reset (R2), a stale CSS order plus a saved DOM move (R3), a
selector matching a decoy container and a missing saved child (R4), the hostile
submit-button import (cleared), both handshake orders and Accept (cleared), a
300-character container name round trip (R7), an import naming library fonts with no
ask (R1), Composer Sync with and without the ask, a 43-URL stylesheet corpus,
`requestId` and ref-counting probes, mixed-case and narrowing origin probes, demote
edge cases, and a selection-order probe with an ordered reply pipe; fake-target probes
for Reapply stopping at a guard, a missing container, `?noOrderIds=1`, Move anyway and
a hostile `previousId`; 20-odd one-line mutations of the production code, of which the
survivors are listed in R9 to R11 and R1. Firefox was not run.

## Verdict

**Approved with fixes.** No finding breaks a global rule outright: Studio never
contacts Google by itself (R1 needs D032 for the target side), nothing is silently
pushed into the app or the file, and no user data is lost. The fix round is R1 to R11
and the nits. The same writers fix them in the file split above, then a scoped
re-review covers: the failing-first tests for R1 to R8, the mutation checks for R9 to
R11, the banner and status wording, and the doc list below. Do not commit before that
re-review passes and the gates are re-run on the final tree (including the online
free-fonts check, which only CI can verify).

## Documentation drift (anti-pattern 11)

Checked: `README.md`, `CONTRIBUTING.md`, `docs/roadmap/` (both files), `docs/specs/`
and `font-kit-studio-v0.2.0-design-bridge-protocol-v1.md`, searched for `orderIds`,
`requestId`, `fontStylesheets`, tracking units, `previousId`, `live.structure`, "Not
saved by Sync", "without stylesheets", D021, the banner wording, `allowedOrigins`,
`initFontKitBridge`, DOM order and the Accept and Reapply wording.

The implementer's list ("Doc text I need changed") covers `README.md:104, 135, 154,
190ish, 195, 416, 455, 456, 474, 594`, the plan boxes and contract, and
`deviations.md` D020, D021 and the two test edits. It is right on those. Corrections
and additions:

### Stale locations the implementer's list does not cover

| Location | Stale text | Needed change |
|---|---|---|
| `README.md:129` (JSON tab row) | `{ "target", "revision", "overrides" }` | Add the optional `structure` (saved DOM order, shown only when a DOM move is saved). Code: `liveJson()`, `font_kit_studio_v0.1.1.html:4868-4872`. |
| `README.md:219` | "It can carry an optional `live` field with your saved overrides and tokens." | Add "and saved DOM order (`live.structure`)". Code: `serializableState`, `:2915-2919`. |
| `README.md:195` (Reapply row) | "...the banner says so, and that also undoes DOM moves in that group." | The list item only adds "DOM-order moves are replayed in order". The old clause must also be reworded: Reapply clears a stale CSS order with a reset, which undoes a DOM move only when that move is not saved; a saved DOM move is replayed afterwards (and, until R3 is fixed, a first press may fail). Matches the in-app notice at `font_kit_studio_v0.1.1.html:4023-4030`. |
| `README.md:196` (Accept row) | "Studio adopts what the page has now." | Add that Accept also replaces saved DOM order (and that saved overrides and tokens the page does not hold are dropped). The list covers the banner paragraph, not this table row. |
| `README.md:167` and `:256` (`framework-managed` guard, **Move anyway**) | "offers **Move anyway** only for that guard" | Add that a move made with Move anyway is kept in Studio but Reapply replays without force, so the guard rejects it and Reapply stops with the reason (recorded limit; same wording as R6). |
| `README.md:203` (Free fonts, "Studio is silent until you ask") | Lists Load free fonts, the Kit preset switch and an inspector pick as the asking actions | State D031 and D032: pressing Sync to Live App, importing a composition and applying one with Sync or Reapply do not count as asking; their library-font sheets load only after Load free fonts or an inspector pick. |
| `README.md:127` (CSS tab row) and `:204` | "`@import` lines for any free fonts first" / "the CSS tab starts with the matching `@import`" | After R1 the `@import` for imported overrides appears only once free fonts were asked for. Add "once you have asked for free fonts" to one of the two. |
| `README.md:215` | The list cites "sends font stacks without stylesheets" here, but that text is at `:594`. Line 215 says Sync "sets the page's font tokens" | Add that Sync also loads the stylesheets of library fonts after Load free fonts, and that tracking now arrives at the right size. No "without stylesheets" text exists at 215. |
| `README.md:468-469` (ledger) | The list asks for `structure[].orderIds` "where the ledger is described" | The README has no field-level ledger description (it only says "the change ledger"). Either add one sentence naming `structure[].orderIds`, or drop that item. |

### Spec drift (flag only; the Spec is product input and is not edited)

`font-kit-studio-v0.2.0-design-bridge-protocol-v1.md` does not define, and so
disagrees with the implementation on, these additive extensions: `requestId` on
`design:select` and its echo in `design:selected` (section 10.4, `DesignSelected` at
lines 583-595 has only `targetId` and `rect`); a `fontStylesheets` list and thousandths-of-an-em
`slots[].tracking` on the legacy composition update (sections 9.1-9.3, lines 470-495,
define only `targetId` and `patch`); `previousId` on a manifest (promotion and now
removal); and `orderIds` in the ledger. The Spec at lines 924-927 also still names
`design:select-slot`, which the code removed earlier. The contract changes belong in
the plan's binding contract (controller), as the report already says.

### No drift found

`CONTRIBUTING.md`, `docs/roadmap/browser-extension.md`, `docs/roadmap/product-direction.md`
and `docs/specs/2026-10-03-typography-system-design.md` mention none of the changed
behaviours or fields. (The typography design mentions "tracking" at lines 88 and 145 as
a role property, not as the composition unit.) `AGENTS.md` and
`docs/agents/global-rules.md` Rule 7 already list the asking actions and agree with
D031 and D032; no change needed. The in-app texts that changed (banner, DOM-move
status, reset notice) are covered by R3, R5 and R6.

### Still to do in the controller's own files

`docs/implementation/progress.md` "Current state" (line 7) and a dated ledger event for
the review and fix rounds; the plan's Addendum 7 checkboxes and contract list; D020 and
D021 as the implementer listed; D032 is already in the working tree.

## Re-review, fix round 1 (2026-10-03)

Both sides were re-reviewed: Studio (Kerning's files) and bridge plus integration tests (Ligature's files).

### Gates

| Gate | Result | Closing line or evidence |
|------|--------|--------------------------|
| `python scripts/verify.py --static-only` | pass, exit 0 | 88 unique HTML IDs; JS syntax (1 block); 3 provenance hashes plus SHA-256 line; closes with "SKIP unittest/browser tests: --static-only; full acceptance not checked" |
| `node --check fontkit-bridge.js` | pass, exit 0 | no output |
| `python -m unittest discover -s tests -v` | pass | "Ran 515 tests in 477.056s", OK; Chromium only; no failures, so no solo re-runs |
| `python scripts/dev/frontend_gate.py --engines chromium --offline` | pass, exit 0 | "SUMMARY OK: 15 of 15 planned runs finished"; blocking 7 runs, 6 passed, 0 failed, 1 skipped; advisory 8 runs, 0 ADVISORY lines; 140 REPORT lines (touch targets), 0 FAIL lines |

Not run, and not verified:

- Firefox: not installed, so no Firefox suite or gate run.
- The online free-fonts check ("free fonts load [desktop, chromium]"): skipped by `--offline`, because the gate's Chromium cannot reach fonts.googleapis.com.
- `scripts/dev/check_commit_messages.py --range origin/main..HEAD`: not run this round.

### Studio items

| Id | State | Evidence |
|----|-------|----------|
| K1 | resolved | Free-font sheets (imports, token sheets, Reapply stylesheet) are gated on the user's ask; StudioFreeFontGateTests pass; mutations k1a-k1e killed |
| K2 | resolved | Saved DOM order is clamped (name, selector, id length, repeated ids); mutations k2a, k2b, k2c, k2e killed; residuals filed as K2-residual |
| K3 | resolved | Only a move saves a container; reset, connect and Accept adopt none; k3a-k3d killed |
| K4 | resolved, with residual | Reset groups are replayed before DOM moves; k4a killed; k4b survives (see K4-residual) |
| K5 | resolved | Replay refuses a container holding none of the saved children; failure text names the element and progress; k5a-k5e killed |
| K6 | resolved | Accept wording says it replaces overrides, tokens and DOM order; shrink claim only when true; k6a-k6f killed |
| K7 | resolved | Move status says when a DOM move is not saved or cannot be replayed; k7a, k7b killed |
| K8 | resolved | Four earlier survivors now have killing tests (k8a-k8d) |
| K9 | resolved | Selection-order tests assert the last select and where the next typed edit lands; k9c, k9j, k9o, k9p killed |
| K10 | resolved | Reapply sends the union of slot and token sheets only after the ask; k10a, k10b killed; the deviation (sheets sent whether or not the composition is linked) is sound and is accepted |
| K11 | resolved | The realign is tracked and superseded by a later pick; k11 killed |
| K12 | resolved | Re-keying a promoted target is announced in the status; k12 killed |
| K13 | open (test name, bridge side) | Studio rounding is covered and k13 is killed there; the integration test keeps a misleading name (see K13-rename) |
| K14 | resolved | release_one waits for Studio to handle the reply; no 30 ms pacing remains |
| K15 | resolved | DOM-move status says the move adds no CSS rules; k15 killed |

### Bridge and integration items

| Id | State | Evidence |
|----|-------|----------|
| L1 | resolved | A bridge-written role or name is dropped on promote and never re-read as the author's; an author's own attributes survive; 14 bridge tests OK; L1b-L1g killed; L1a is an equivalent mutant |
| L2 | resolved | Demoted arrangement branch is checked via design:targets and a fresh ready; mutations i, i2, i3 killed; i4, i5 are equivalent (discovery corrects them before anything is posted) |
| L3a | resolved | Imported override fonts stay off the network until the ask; K1a, K1b killed |
| L3b | resolved | A container the page reordered alone is not saved by a reset of one child; K3 killed |
| L3c | resolved | Reapply restores a saved DOM move on the first press despite a stale CSS order; K4 killed |
| L3d | resolved | Selection order after the realign is asserted; mutation o killed |
| L3e | resolved | Reapply without the ask sends no token font to any font host; g2 killed |
| L3f | resolved | Reapply keeps the sheet only a Composer slot needs; K10, K10b killed |
| L3g | resolved | A saved container the app no longer owns is not filled; K5 killed |
| L4 | resolved | release_all uses an in-order flush marker; one 60 ms absence window remains |

### Mutation re-checks

- Killed: k1a-k1e, k2a, k2b, k2c, k2e, k3a-k3d, k4a, k5a-k5e, k6a-k6f, k7a, k7b, k8a-k8d, k9c, k9j, k9o, k9p, k10a, k10b, k11, k12, k15, K13 (Studio test), L1b-L1g, i, i2, i3, g2, K3, K4, K5, K10, K10b, o.
- Survived, equivalent: L1a, i4, i5, k2d (the child-count clause is redundant with the order and orderIds length check).
- Survived, a real gap: k4b (see K4-residual); k2f (the 100-entry cap is untested); the same rounding mutation against the integration test named in K13-rename.
- Out of scope, noted only: c and j against the integration class (covered by Studio fake tests); K3b in the integration class.
- Baseline: `tests.test_studio_live` in a private copy, 125 tests OK (Chromium only); `tests.test_live_integration`, 37 tests OK.

### Open items

| Id | Owner | Severity | What |
|----|-------|----------|------|
| K4-residual | kerning | should-fix | The clause `&& !resetIds.has(id)` in planStructureReplay has no test. Without it, a saved cross-container move with a stale CSS order on the moved element is sent as an index and lands in the wrong container after the reset. Check reachability first; then add a fake test (saved Sidebar [side.x, side.y, card.a], stale order on card.a, Reapply, card.a ends in the Sidebar) or delete the clause. |
| K2-residual | kerning | nit | Remove the redundant child-count clause (Rule 8) or say in the comment that the length mismatch rejects over-limit containers; test the 100-entry cap if reachable, or mark it defensive and untested. |
| K1-wording | kerning | nit | FONTS_WAIT_NOTE says the target keeps its own fonts, but without the ask the page shows the override stack's local or generic fallback. Reword (and the matching test assertions and comments), or the controller rules the Composer wording stays and closes it. |
| K13-rename | ligature | nit | Rename `test_tracking_values_with_float_noise_and_the_limits_stay_exact` to what it proves (imported tracking values are normalised before they reach the page). |

### Observations, not items

- While the composition is linked, an acknowledged composition update overwrites the saved tokens with the page's tokens. The line is unchanged from HEAD; Kerning decides whether it is a bug.
- Legacy select-slot heuristics can still match a bridge-written role. This predates the round.
- Rules 5-7 and the anti-pattern registry: nothing new on either side. All Google Fonts contact is gated on the user's ask (D032); new status text goes through textContent.

### Round verdict

**Changes required.** The gates pass and both sides were re-reviewed, but K4-residual (should-fix) is open: new replay behaviour has no test that fails when it is removed. The three nits do not block. Fix K4-residual with Kerning, then run a scoped re-review.

## Re-review, fix round 2 (2026-10-03)

Scope: the four items left open by fix round 1 (K4-residual, K2-residual,
K1-wording, K13-rename). Both sides (Studio, and bridge plus integration)
were re-reviewed.

### Gates

| Gate | Command | Result |
|------|---------|--------|
| Static | `python scripts/verify.py --static-only` | PASS HTML IDs: 88 unique static IDs; PASS JavaScript syntax: 1 executable inline blocks; PASS provenance (3 supplied-v0.1.1 blobs); SKIP unittest/browser tests (--static-only). Exit 0. |
| Bridge syntax | `node --check fontkit-bridge.js` | No output, exit 0. |
| Unit and browser suite | `python -m unittest discover -s tests -v` | Ran 517 tests in 481.078s, OK. No FAIL or ERROR lines, so no re-runs. |
| Frontend gate | `python scripts/dev/frontend_gate.py --engines chromium --offline` | SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines (touch targets), 1 SKIP line, 0 FAIL lines. Exit 0. |

Engines: Chromium only (`FKS_ENGINES=chromium`).

Not run:

- Firefox. It is not installed here, so no Firefox suite or gate run was done and none is claimed.
- The gate's online free-fonts check. `--offline` skipped it, because the gate's Chromium cannot reach fonts.googleapis.com from this container.
- `scripts/dev/check_commit_messages.py`. Nothing is committed yet.

### Items

| Id | Status | Evidence |
|----|--------|----------|
| K4-residual | Resolved | `test_reapply_moves_a_reset_element_back_into_its_saved_container` (tests/test_studio_live.py:1732) runs unmutated. It asserts the rendered DOM (Sidebar ends [side.x, side.y, card.a]; Cards no longer holds card.a) and the replayed move {container: sidebar, index: 2}. No fixed sleeps. |
| K2-residual | Resolved | The 100-container cap has a test that fails without it. The redundant child-count clause is gone. The 500-child limit is now carried by the length-mismatch check, which has a killing test. |
| K1-wording | Resolved | FONTS_WAIT_NOTE (font_kit_studio_v0.1.1.html:1454) now says library fonts are not loaded until Load free fonts and that the page shows each stack's fallback meanwhile. One constant feeds the banner, Reapply, save and Composer statuses. Both tests that check the wording fail when it is reverted. |
| K13-rename | Resolved | tests/test_live_integration.py:623 is now `test_imported_tracking_values_are_normalised_before_they_reach_the_page`, with no docstring and no leftover "float noise" wording in tests. The test passes alone and is not vacuous. |

### Mutation re-checks

All mutants ran in private copies under `work/`. The shared tree was not edited.

| Mutant | Test | Result |
|--------|------|--------|
| Drop `&& !resetIds.has(id)` in planStructureReplay | test_reapply_moves_a_reset_element_back_into_its_saved_container | Killed. Reapply never completes, so the test errors. |
| Remove the 100-entry cap (`saved.length >= MAX_STRUCTURE_ENTRIES`) | test_saved_dom_order_holds_at_most_one_hundred_containers | Killed. The older=100 subtest fails. |
| Remove `list.length !== entry.order.length` | test_saved_dom_order_never_holds_what_the_import_would_refuse | Killed. The "more children than the import takes" variant fails. |
| Revert FONTS_WAIT_NOTE to "the target keeps its own fonts" | test_imported_override_fonts_wait_for_the_users_ask; test_without_the_users_ask_no_stylesheet_is_sent_and_the_status_says_why | Killed. Both fail. |
| Tracking send side without rounding (`slot.tracking * 1000`) | the renamed integration test | Survived, as stated in round 1. The test no longer claims send-side rounding. Studio's own test (test_studio_live.py:3813) covers it. |
| Tracking send side without x1000 and rounding | the renamed integration test | Killed (3.5e-05em versus 0.035em). |

### Open items

| Id | Owner | Severity | Detail |
|----|-------|----------|--------|
| R2-deviations-wording | kerning (controller-owned file) | nit | `docs/implementation/deviations.md` D031 (line 25) and D032 (line 26) still say the target "keeps its own fonts" until Load free fonts is pressed. Without the ask, the override font-family stack is still sent or written, so the page shows that stack's fallback. Reword both to match FONTS_WAIT_NOTE (AGENTS.md anti-duplication). Does not block the code. |

### Observations, not items

- The 100-entry cap counts page-reported containers the user never moved. With 100 older page-only containers, the user's own move is left out of the export. A test pins this on purpose, the comment says so, and the export still imports. Accepted edge case, not a regression.
- Rules 5-7 and the anti-pattern registry: nothing new on either side. Without the user's ask no stylesheet is sent and the status says why (D032). No new fixed sleeps. Both new Studio tests assert rendered or DOM state, not only sent messages.

### Round verdict

**Approved.** No blocking or should-fix item is open. The gates pass (Chromium only; Firefox not run) and both sides were re-reviewed. The one open nit (R2-deviations-wording) should be fixed in the same commit as the work.

## Review: composition fonts after consent (2026-10-03)

Scope: the uncommitted change on head 62fcc1f. `font_kit_studio_v0.1.1.html:4948` (the `fontkit:free-fonts-allowed`
handler now also calls `broadcastLiveState(true)`), two tests in `StudioCompositionFontTests`
(`tests/test_studio_live.py`), and the report section "Review fix: composition fonts after consent".

### Findings

- **Rule 6 holds.** `broadcastLiveState` returns unless `live.ready && live.compositionLinked` (`:5256`).
  `compositionLinked` is set only by the Sync button (`:5273`) and cleared by every session reset (`:3441`), so
  consent alone pushes nothing into a page whose composition was not linked. A re-hello ends the link, so a
  reconnect followed by consent sends nothing either. Mutation check: replacing the call with an ungated
  `enqueueLiveOp` makes `test_loading_free_fonts_without_a_sync_sends_nothing_to_the_page` fail with the full
  composition message in the diff.
- **Dispatch paths.** `allowFreeFonts` (`:1496`) dispatches the event only on the first transition to consent
  (`asked`, `:1497-1504`). Callers: Library and Composer Load free fonts (`:1547`, `:2218` via `loadAllFreeFonts`),
  Kit preset "Free Google Fonts" (`:2212`), inspector library pick (`:4466`). A second click, and remembered
  consent on page load (`:1451`, set before the listener exists), dispatch nothing, so there is no re-broadcast
  at a surprising time and no double send. The Kit preset change does not re-render the canvas, so no debounced
  send follows. The inspector pick sends the (linked) composition once, then its own element update; the bridge
  keeps composition sheets and per-target sheet references separately and reference-counted
  (`fontkit-bridge.js:1636-1670`), so the two do not release each other.
- **Races.** The send goes through `enqueueLiveOp`. A queued composition op is replaced in place (`:3590-3593`),
  an in-flight one is left alone, and `broadcastLiveState(true)` clears any pending debounce timer, so the
  consent send cannot overlap or double an in-flight composition request.
- **Rule 7, D031, D032 hold.** The ask is still only the explicit actions; Sync, import and Reapply do not count.
  The extra send happens only after the user pressed one of them, and `compositionPatch` adds `fontStylesheets`
  only when `freeFontsAllowed` is true (`:5210`), which `allowFreeFonts` sets before dispatching.
- **Tests.** Mutation in a private copy (`work/leading-consent/mut`, shared tree untouched): deleting
  `broadcastLiveState(true)` makes the resend test time out waiting for `ledger().imports` (FAIL); the no-sync
  test passes, as expected for a characterization of the boundary, and fails under the ungated mutation above.
  Both tests assert page state (the fake page's imports, the exact sheet list and family order, exactly one extra
  update, an absence window for the negative case), not only sent messages.
- **Pre-existing, not introduced here (note only).** Streaming composition updates send `compositionFontSheets()`
  (slot fonts only) as the complete set, while Reapply sends `composedFontSheets()` (slots plus saved-token fonts).
  A linked composition that follows a Reapply of saved library-font tokens can therefore release the token sheet
  on any update, including this one. The consent send behaves like every other streaming update.

### Required before commit

- **R1 (should-fix): no real Studio + real bridge test for this boundary.** AGENTS.md "Test Quality Rules"
  requires at least one test per boundary against the real bridge, and forbids protocol features covered only by
  a fake counterpart. Both new tests run against the fake page (`window.fake`). `CompositionSyncTests`
  (`tests/test_live_integration.py:553`) covers sync-after-consent and sync-without-consent, and
  `FreeFontsAskTests` (`:647`) covers the ask for imports and Reapply, but nothing covers sync first, then Load
  free fonts. Add to `CompositionSyncTests`: connect, Sync without consent, assert zero `link[data-fontkit-font]`
  and no font requests; click `#loadFreeFonts`; wait until `link[data-fontkit-font]` hrefs equal `self.SHEETS`;
  assert the four sheets were requested. Optionally add the unsynced twin: consent without Sync leaves zero links
  in the target. The report's gate line should then name the integration module too.
- **R2 (nit): ledger.** Add the ledger event in `docs/implementation/progress.md` in the same commit
  (AGENTS.md, Commit Rules 1). The report states that the full suite and the frontend gate were not run by the
  task; the results below are the evidence.

Coverage note: the new tests drive only the Composer `#loadFreeFonts` path. The other paths share
`allowFreeFonts`, so the single dispatch point is covered, but the Library button, Kit preset and inspector pick are
not exercised for this behaviour. Acceptable.

### Gates (current tree, Chromium only, Firefox not run)

- `python scripts/verify.py --static-only`: PASS (88 unique IDs, inline JS syntax, 3 provenance hashes).
- `node --check fontkit-bridge.js`: exit 0.
- `python -m unittest discover -s tests` (PYTHONPATH=tests, FKS_ENGINES=chromium): `Ran 519 tests in 512.933s` / `OK`.
- `python scripts/dev/frontend_gate.py --engines chromium --offline`: `SUMMARY OK: 15 of 15 planned runs finished.
  Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP
  lines, 0 FAIL lines`. The skip is the "free fonts load" check, skipped by `--offline`. REPORT lines are
  touch-target notes on advisory profiles.
- Not run: `check_commit_messages.py` (nothing committed), Firefox, the online free-fonts gate check.

### Verdict

**Approved with fixes.** The one-line change is correct and respects Rules 6 and 7; the tests are real, and one
is mutation-checked both ways. Add R1 (the real-bridge test) and R2 before the commit.

## Review: Copilot findings C1-C5 and the composition sheet set (2026-10-03)

Scope: the staged diff on head 1ffce91 (`font_kit_studio_v0.1.1.html`, `fontkit-bridge.js`, three test modules; 821
insertions, 63 deletions). Five fixes written in parallel worktrees, merged. The unstaged `README.md` edit was read
only for claims about the staged behaviour. The original findings are the six review threads on PR #2.

### Verdict

**Approved with fixes.** Every finding is fixed and the fixes do not conflict with each other. One required code fix
(R1) is a sibling of C1 that the merge left open, with a one-line change and a test to write first. Two required
non-code items (R2 wording, R3 records). Gaps (a) and (b) are ruled below: (a) is a recorded limit; (b) is required
when the reply names its container (the real bridge always does) and a recorded limit when it does not.

### Each finding, re-run against the merged code

| Id | Result | Evidence |
|----|--------|----------|
| C1 | Fixed | The verifier's probes (`work/verify-copilot/copy/tests/test_probe_copilot.py`, run in `work/leading-pr2/copy`): after an in-session reorder and an unrelated reset, `live.structure` equals what the user saved and the banner is visible (fake page and real bridge). Code: `syncStructureFromLedger` (`font_kit_studio_v0.1.1.html:3722`) keeps an untouched saved entry (`:3727`), `structureTouchedBy` (`:3748`) names what an op may change, and `structureHeld` raises `live.conflict` (`:3738`). |
| C2 | Fixed | Both probes: the duplicate id (Cards [b c d] + Sidebar [x y a], then moving card.d) leaves the saved list as it was, and 100 saved containers plus a move stay at 100; both exports import again. `structureRefusal` (`:3764`) runs on the merged list before `live.structure` is replaced (`:3736-3737`); `domMoveNotice` says "This move is not saved" and why (`:3818-3823`). |
| C3 | Fixed | Probe: the object the bridge was built from, edited and passed back to `initFontKitBridge`, narrows (`['a','b']` to `['a']`; also in place, string and replace modes in the new tests). `fontkit-bridge.js:3146-3162` drops the identity check from the decision and keeps it only for the warning. |
| C4 | Fixed | Probes: a text-only saved edit no longer says "smaller file"; text plus font size still does. `cssOnlyOverrides` (`:4183`) feeds `acceptShrinksFile` (`:4196`) and the "0 live edits" sentence (`:4232`). Every `LIVE_CSS` key counts, `order` included, so a saved CSS-order edit still counts as in the file. |
| C5 | Fixed | Probe: a list pick handled by the real bridge after a newer page click ends with the inspector and `bridge.selectedId` both on the click. `requestSelection` (`:3547`) goes through the only `design:select` sender (`sendTrackedSelection`, `:3568`); the bridge echoes `requestId` for found and null targets (`fontkit-bridge.js:2795-2826`). |
| Sheet set | Fixed | `withCompositionSheets` (`:5293`) is the only builder; Sync and linked edits (via `compositionPatch`, `:5279`), the consent re-send (`broadcastLiveState(true)`) and Reapply's token update (`:3989`) all go through it. `compositionFontSheets` and `composedFontSheets` have no remaining reference outside review records. |

### Required before commit

**R1 (required, code): a reset that names its container must not use the stale-ledger heuristic.** Gap (b), wider than
the implementer wrote.

- Where: `structureTouchedBy`, `font_kit_studio_v0.1.1.html:3756-3758`. The comment (`:3744-3747`) says the heuristic is
  for a reply that does not name the container (`target` is optional). The code applies it to every reset.
- Why it matters: the real bridge always sends `target` for a targeted reset (`fontkit-bridge.js:1207`), so
  `containerBefore` and `after` already identify the containers the reset touched. The heuristic then adds "a saved
  container the last ledger listed and this one does not". When the app put another saved container back by itself
  since the last acknowledgement, that container is dropped with no banner. That is C1 again (a saved container the
  op did not touch is lost to an in-session page change), and Rule 6 outranks Rule 8.
- Reproduced (private copy, shared tree untouched): Cards [c a b d] and Sidebar [y x] saved by two DOM moves; the app
  restores Cards; reset of side.y with no acknowledged edit between. Result with the fake's reply extended to carry
  `target` (as the real bridge's does): `live.structure` is empty and the banner is hidden. Same result without
  `target`. The existing test `test_a_reset_of_one_saved_element_does_not_drop_another_saved_container_the_page_had_put_back`
  passes only because an acknowledged edit (rev 3) refreshes the ledger before the reset; its own comment says so.
- Exact change: `if (op.kind === "reset" && !after) {` at `:3756`, and reword the comment to say the heuristic is for
  a reply that names no container.
- Verified in `work/leading-pr2/fixb`: with that change the probe keeps Cards and shows the banner (Sidebar goes, as
  the reset put it back); a cross-container reset that names its container still drops both containers (probe
  result: no saved structure, no banner); `StudioDomMovePersistenceTests` and `StructureReplayTests` (34 tests) pass.
- Failing test to write first, in `StudioDomMovePersistenceTests` next to the test named above:
  `test_a_reset_that_names_its_container_does_not_drop_a_saved_container_the_page_put_back_since_the_last_reply`.
  Fixture: in `tests/fixtures/studio/fake-target.html:615` the reset reply gains
  `...(d.targetId && fake.resetNamesTarget ? { target: manifest(byId.get(d.targetId)) } : {})`. Steps: open the
  arrange target, set `window.fake.resetNamesTarget = true`; DOM-move card.c first (rev 1); DOM-move side.y first
  (rev 2); `restore_cards_in_the_page`; select side.y and press Reset (rev 3), with no edit in between. Assert: the
  export's `live.structure` equals `saved_cards(CARDS_AS_SAVED)`; the banner is visible and says "the live target holds
  0 of them"; the page DOM of Cards is the restored order (Studio did not touch it); Reapply then puts
  `CARDS_AS_SAVED` back and hides the banner. Add a companion that passes today (characterization, not manufactured
  RED): with `resetNamesTarget`, DOM-move card.a into Sidebar, reset card.a, assert both saved containers are gone.

**R2 (required, wording): the README over-promises gap (a).** Unstaged `README.md` (Live edits section, new bullet): "If the
page itself changes the order of a container Studio saved ..., Studio keeps its saved order and raises the reconnect
banner". The banner is raised when the next DOM move or reset is acknowledged, and at reconnect; an acknowledged edit
does not raise it (ruling (a)). Say so, in the same sentence. Also, in the Accept row, "a smaller CSS file only when the
page holds fewer style edits" leaves out tokens (`acceptShrinksFile` counts them) and carries a doubled parenthesis.

**R3 (required, records), per Commit Rules 1:** a ledger event in `docs/implementation/progress.md` for these fixes (scope,
tests added, the evidence below, engines), and one decision entry in `deviations.md` for the two rulings below. The
staged diff holds neither. Not run by this review: the full suite and the frontend gate (the baseline run was
using the machine), Firefox, `check_commit_messages.py`. Record them as not run, not as passed.

### Rulings on the two gaps

**(a) An acknowledged edit after an in-session reorder raises no banner: recorded limit, not required.**

- Nothing is overwritten or dropped: Studio's saved order stays as saved, and every path that reads it (move, reset,
  Reapply, export, reconnect) is now correct. Probe: reorder in session, acknowledged font-size edit: banner hidden,
  saved order unchanged; after a reload the banner appears.
- The signal cannot be complete anyway: with no acknowledgement at all, an in-session reorder is also invisible. A check in
  `acceptApplied` would make the banner depend on which message came next, and it would fire during a Reapply run (the
  page does not yet hold the saved order) and after a user's own Sync that reorders a saved container.
- Copilot's sentence ("surface any mismatch when processing the new ledger") is met where the ledger is processed for
  the structure: `syncStructureFromLedger`. Record in `deviations.md`: the mismatch is raised at the next acknowledged DOM
  move or reset and at reconnect; cost if wrong: the banner can come late, never a lost order.

**(b) A reset whose reply omits `target`, after the app restored another saved container: recorded limit.** For a reply
that names no container, Studio cannot tell the container the reset put back from one the app restored; the heuristic
(`:3756-3758`) is the only source, and the existing test `test_resetting_a_moved_element_that_came_from_another_container_drops_both_saved_containers`
needs it (mutation: removing the line fails that test and no other in `StudioDomMovePersistenceTests`). Any acknowledgement between refreshes the
ledger and avoids the loss. The bundled bridge always names the container, and R1 closes the real case. Record the
limit beside (a).

### Interactions between the merged fixes

| Pair | Finding |
|------|---------|
| C1 conflict and C4 banner | A structure-only mismatch gives `acceptShrinksFile() === false` (no "smaller file" promise) and no "0 live edits" sentence (the page has edits in session; the sentence also needs `!live.changes.structure.length`). No clash. The banner heading is still the static "Target reconnected." (`:1070`), now also shown for a mismatch raised in session. Nit N1. |
| C1 conflict and auto-sync | An open conflict holds auto-sync (`scheduleAutoSync`, `:5200`), so a structure-only mismatch also holds CSS auto-sync until Reapply or Accept. The new test pins it (one PUT only). This is the existing conflict rule and the conservative side of Rule 2; noted so the owner knows. |
| C1 and C2 | A refused move still raises the conflict when the page differs from what is saved (`structureHeld` is false), so the user sees the banner and the status. Exception, by design: 100 saved containers that the page holds, and a move in a 101st: status line only, no banner. |
| C5 and the structure code | The move and reset paths re-select through `refreshSelection` (tracked, `:3556-3560`); `requestSelection` supersedes them; the in-order prune (`:4301`) drops older unanswered entries so they cannot block a realign. A bridge that never echoes `requestId` still follows every pick (test with the echo removed). `sendDesignMessage` returns false without a session, so nothing is tracked then. |
| Sheet set and the consent re-send | One builder. Without the ask the key is absent (mutation: ungated builder killed). With it, the set is slots, then `{...savedTokens, ...patch.tokens}` fonts, capped at 16; a replaced token's font is released (mutation killed). The consent send, Sync, linked edits and Reapply send the same kind of set, which resolves the note in the previous review. |
| C3 | Independent of the Studio fixes. |

### Rules and decisions

- Rule 5: Studio sends only through `sendDesignMessage` (pinned origin, `:3418-3423`); the echoed `requestId` is a
  bounded string; narrowing never widens (test `...never_widens_it`).
- Rule 6: C1 and C2 stop the silent adoption and the unexportable merge, except R1. A refused move is announced
  ("This move is not saved ..."), not dropped quietly.
- Rule 7, D031, D032: unchanged. No stylesheet key without the ask; the Composer and imported-JSON paths still wait.
- Anti-pattern 12 (class, not instance): R1 is the sibling of C1 that was left. Anti-pattern 11: R2.
- No new fixed sleeps. Two short absence windows (400 ms and 1000 ms) prove that nothing was sent; that is the allowed
  exception. All 27 added tests assert rendered or page state (shown target and the next edit's destination, DOM
  order, exported structure, imports and `link` elements in the target, banner and status text).

### Evidence

Every command ran in `work/leading-pr2/copy` (a private copy of the staged tree), `PYTHONPATH=tests`,
`FKS_ENGINES=chromium`.

| Run | Result |
|-----|--------|
| Verifier probes (9, `test_probe_copilot.py`) | All scenarios behave as fixed (the C3 probe asserts `1 == 0` on purpose and prints the allow-lists). |
| The 27 tests added by the five fixes | Ran 27 tests in 64.164s, OK. |
| Affected classes: `StudioSelectionOrderTests`, `StudioPersistenceTests`, `StudioCompositionFontTests`, `StudioDomMovePersistenceTests`, `OriginListTests`, integration `SelectionOrderTests`, `StructureReplayTests`, `CompositionSyncTests`, `FreeFontsAskTests` | Ran 85 tests in 152.596s, OK. |
| `python scripts/verify.py --static-only`, `node --check fontkit-bridge.js`, `git diff --cached --check` | PASS, exit 0, no whitespace errors. |
| Gap (a) and (b) probes (`test_probe_leading.py`) | (a): banner hidden after an acknowledged edit, saved order unchanged, banner after reload. (b): Cards dropped, no banner, with and without `target`; with the R1 change Cards is kept and the banner shows. |

Mutations (each in its own copy, one test run per line):

| Mutant | Killed by |
|--------|-----------|
| C1: untouched saved entries adopted again (drop `:3727`) | the three unrelated-reset tests (Studio x2, real bridge) |
| C1: no conflict raised (`:3738-3741` removed) | the same three, plus the duplicate-id test |
| C1: stale-ledger line removed (`:3757`) | `test_resetting_a_moved_element_that_came_from_another_container_drops_both_saved_containers` only |
| C2: duplicate-id check removed; limit check removed; "elsewhere" wording removed | the matching C2 test each |
| C3: identity check restored; warning always printed | the edited-subset tests (three modes), the page-global test; the two quiet tests |
| C4: no `cssOnlyOverrides` in `acceptShrinksFile`; "0 live edits" sentence on `count` again | `test_a_saved_text_only_edit_is_not_promised_...` each |
| C5: `requestSelection` untracked; prune removed; supersede removed | the two Studio and two integration ordering tests; `test_a_request_the_target_never_answered_...`; `test_back_while_the_refresh_is_in_flight_...` |
| Sheet set: token fonts left out; saved (not merged) tokens; ask gate removed | the two token tests; the replaced-token test; the no-ask test |

All killed. Nothing survived.

### Nits (not blocking)

- N1: the banner heading "Target reconnected." (`:1070`) is false for a mismatch raised in session. A neutral heading
  ("Target and Studio differ.") needs a screenshot refresh in the README, so it can follow in its own change.
- N2: `README.md:420` says a console warning always reports what `initFontKitBridge` applied or ignored; the call with the
  object the bridge was built from is now quiet unless it narrowed. Add that clause.
- N3: the refusal for C2 is covered only against the fake page. The real bridge covers C1 and C5; adding a C2 case needs
  two reorderable saved containers in the demo page. Acceptable now.

## Re-review: R1 reset heuristic, banner headings, docs (2026-10-03)

Scope: the unstaged diff on top of the staged tree (`font_kit_studio_v0.1.1.html` +30/-11 unstaged, fake target
fixture, `tests/test_studio_live.py` +53, `README.md`, `deviations.md` D034, `progress.md` event). Branch
`ccr-9eab25c9-mgatzt`, HEAD `1ffce91`; no git state touched. Probes and mutants ran in private copies under
`work/leading-pr2b/` (`copy`, `mut-*`); the gates ran once on the shared tree after the probes.

### Verdict

**Approved with fixes.** R1 is closed and the heading cannot go stale. Two small required items, neither a code
change: one test assertion (a mutant of the new heading code survives) and the test count in the ledger.

### R1: closed

- The guard is `if (op.kind === "reset" && !after)` at `font_kit_studio_v0.1.1.html:3761`, and the comment above it
  (`:3746-3751`) now says the guess is for a reply that names no container. Siblings: `structureBefore` is read only
  here (`:3761-3762`, set at `:3794`); no other path uses the stale-ledger guess.
- My earlier probe (Cards [c a b d] and Sidebar [y x] saved, the app restores Cards, reset of side.y with no
  acknowledged edit between), run against the current tree with the fake's reply extended by `resetNamesTarget`:
  `live.structure` keeps Cards, the Sidebar goes (the reset put it back), the banner is visible.
- With `target` omitted the probe still drops Cards with no banner. That is the limit recorded as D034 (b), and
  `test_resetting_a_moved_element_that_came_from_another_container_drops_both_saved_containers` (default fake, no
  `target`) is what needs the guess.
- Against the real bridge (`test_probe_r1_real.py` in the copy; the demo has two reorderable containers, `.actions`
  and the hero): CTA moved next, `landing.hero.lead` moved, the app restores `.actions` in session, reset of the lead.
  Result: `.actions` stays saved, the hero entry goes, banner visible, heading "The page changed a saved DOM order."
  The bundled bridge does name the container for every attached element (`fontkit-bridge.js:1207`, `:2619-2627`),
  so D034 (b)'s "always names it" holds.
- Tests: `test_a_reset_that_names_its_container_does_not_drop_a_saved_container_the_page_put_back_since_the_last_reply`
  (`tests/test_studio_live.py:3242`) asserts exported structure, banner text, heading, page DOM (Studio did not touch
  it) and that Reapply restores the order. The companion (`:3275`) is a characterization that passes without the fix
  and asserts both containers go and no banner shows. Fixture switch at `fake-target.html:58-60`, `:619`, default off.

### Banner heading: cannot go stale; one test gap

State: `live.conflictCause` (`:2133`). It is set in exactly two places. `reconcileSavedOverrides(cause)` (`:3903-3904`)
sets it on every call, before it recomputes `live.conflict`: `design:ready` passes the default "reconnect", an import
while the target is ready passes "import" (`:3928`). `syncStructureFromLedger` (`:3739-3743`) sets "page" only when no
conflict is open. `live.conflict` becomes true only in those two places; it becomes false only in Reapply (`:4024`),
Accept (`:4159`) and a reconcile that finds no difference. `renderReconnectBanner` writes the heading on every render
(`:4234`).

| Scenario | Result (probe, private copy) |
|----------|------------------------------|
| page conflict, Reapply, reload | banner "Target reconnected." (reconcile overwrites the old cause) |
| page conflict, Accept, a new in-session reorder and reset | "The page changed a saved DOM order." (conflict was closed, so the new cause is set) |
| page conflict open, then an import | "Imported state differs from the target." (the import replaced the saved state, so it is the new cause) |
| import conflict open, then an in-session reorder and reset | stays "Imported state differs from the target." |
| import conflict, then a reload | "Target reconnected." |
| fresh reload (existing test `:3076`) | "Target reconnected." (default cause) |

The three heading assertions (`:3076`, `:3265`, `:3342`) read rendered text. The wording is true for each cause and the
text after it still says "Nothing was applied automatically" and offers Reapply or Accept (Rule 6). A refused move in a
conflict that is already open keeps that conflict's heading. The screenshots in `docs/assets/screenshots/` show the
reconnect heading, which is unchanged.

Mutants (own copy each, `StudioDomMovePersistenceTests`, 32 tests, Chromium):

| Mutant | Result |
|--------|--------|
| R1 guard: `&& !after` removed | killed by the new R1 test only |
| "page" cause never set | killed by the new R1 test |
| `reconcileSavedOverrides("import")` without the cause | killed by the import test |
| `live.conflictCause = cause;` removed | killed by the import test |
| heading line removed (static text) | killed by the R1 test and the import test |
| **`if (!live.conflict)` dropped: an open conflict is relabelled "page"** | **survives** |

**F1 (required, test only).** The last mutant is the rule that an open conflict keeps the cause it was raised with
(`:3741`, comment at `:3740`). Nothing pins it. Add one assertion to
`test_a_move_made_while_a_conflict_is_open_is_not_saved_when_it_would_name_an_element_twice`, after the line
`self.assertEqual(self.dom(frame), ['card.d', 'card.a', 'card.b', 'card.c'], 'the page has the move')` (`:3459`):

```python
self.assertEqual(page.locator('#liveReconnectHeading').inner_text(), 'Target reconnected.', 'an open conflict keeps its cause')
```

Verified: it passes on the current tree and fails on the mutant ("The page changed a saved DOM order." != "Target
reconnected."). No code change.

### Docs, ledger and decision against the code

| Item | Result |
|------|--------|
| README `:137` (page changes a saved container) | Matches `:3657-3665` and `:3741`: the banner comes at the next DOM move (not a CSS-order move, not a Reapply step) or targeted reset, and at reconnect; an acknowledged style edit does not raise it (D034 a). Nit, not blocking: "While that banner is open" is incomplete for the 100-container limit, where 100 saved containers that the page holds raise no banner and the move is still not saved with a status line. |
| README `:198` (Accept) | Matches `acceptShrinksFile` (`:4196-4210`): CSS keys only (order included), tokens counted, text excluded. Nit: "text edits are not in the CSS file, and the banner says when" reads as if the banner announces dropped text edits; it announces the smaller file. Optional reorder. |
| README `:420` | Matches `fontkit-bridge.js:3146-3162` (quiet only for the original object when nothing narrowed). |
| D034 (a), (b) | Match my two rulings and the code (`:3741`, `:3761`); product terms only (anti-pattern 15 clear). |
| Ledger event (`progress.md`) | Bullets match the code and tests, except the count below. |

**F2 (required, record).** `docs/implementation/progress.md:69` says "546 tests". The tree holds 548 (HEAD 519, the
five fixes 27, the two R1 tests 2). Collected and run: 548. Change it to 548 (anti-patterns 11 and 14).

### Gates (full current tree, staged and unstaged; Chromium only; Firefox is not installed here and was not run)

- `python scripts/verify.py --static-only`: PASS (89 unique IDs, inline JS syntax, 3 provenance hashes), exit 0.
- `node --check fontkit-bridge.js`: exit 0. `git diff --check` and `git diff --cached --check`: clean.
- `python -m unittest discover -s tests -v` (`PYTHONPATH=tests`, `FKS_ENGINES=chromium`, log
  `work/leading-pr2b/suite.log`): `Ran 548 tests in 549.991s` / `OK`. No failure, nothing re-run.
- `python scripts/dev/frontend_gate.py --engines chromium --offline`: `SUMMARY OK: 15 of 15 planned runs finished.
  Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines,
  0 FAIL lines` (the skip is the online free-fonts check; the REPORT lines are touch-target notes).
- Not run: `check_commit_messages.py` (nothing committed), Firefox, the online free-fonts check.
- Processes: the suite (PID 20967) and the probe and mutant runs have exited; nothing of mine is left running.
