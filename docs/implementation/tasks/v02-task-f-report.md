# v0.2.0 Task F report: Studio arrangement UI, pop-out, free fonts, saved tokens

- Branch: the v0.2 PR branch, starting from the Task C change. Nothing was committed by this task.
- Contract basis: plan "Protocol contract", Addendum 1, Addendum 2, and Addendum 3 (D019, arrived mid-task). Task E's report (`v02-task-e-report.md`) was reconciled with the fake target (see "Contract notes").

## Files changed (owned files only)

| File | Change |
|---|---|
| `font_kit_studio_v0.1.1.html` | Arrange section, strategy toggle, guards, warnings, pop-out, free-font library and loaders, kit presets, imports in the CSS tab, structure in the HTML tab, saved tokens in `live` JSON, `order` as saved state. |
| `tests/test_studio_live.py` | 26 new tests in `StudioArrangeTests` (12), `StudioPopoutTests` (6), `StudioFreeFontTests` (6), `StudioSavedTokensTests` (2); one old assertion changed (below). |
| `tests/fixtures/studio/fake-target.html` | Fake bridge side extended (below). |
| `tests/fixtures/studio/spoofer.html` | Added `spoofOpener` (posts to `window.opener`). |
| `tests/test_font_kit_studio_v011.py` | Not changed: none of its assertions encode the Adobe default. |
| this report | |

## Fake target (`fake-target.html`)

Implements, per Addenda 1-3 and Task E's real message shapes:
- `arrangement` in every manifest (`containerKey/Name/Selector`, `index`, `count`, visual-order `siblings`, `containers`, `cssOrderAvailable` from the parent's computed display, `frameworkManaged`).
- `design:move` with all `to` forms, `strategy`, `force`; `invalid-message` (`detail.field`), `unknown-target`, `unsupported-value` with `detail.reason`; guard rejections `{property:"move", guard, overridable, message, framework?}` (configure via `fake.guards` and `fake.framework`); css-order sets `order` on every sibling and records `declarations.order`.
- Ledger `structure` (cleaned container html, `order` names) and `imports` (reference counted; `null` and reset release).
- `fontStylesheet` validation (Google css2, Typekit) and acceptance.
- `design:warning` (`fake.warn`, `fake.warnNext`), `design:mode {overlay}` recording (`fake.overlay`), reset restoring DOM and order.
- Pop-out: talks to `window.opener` when it has no parent.
- Flags: `?arrange` (flex "Cards" with 4 targets, block "Sidebar" with 2), `?only` (adds an `arrangementOnly` sibling), `?bulk` (bulk manifests: empty `siblings`, no `containers`).
- The default 5-target page is unchanged. The one old assertion `fake.ledger() == {tokens, targets}` now includes `structure` and `imports` (as the real ledger does).

## RED / GREEN

RED (baseline Studio sha `0e394191…`, after the fake and tests existed, before any Studio change):

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest \
  test_studio_live.StudioArrangeTests test_studio_live.StudioPopoutTests \
  test_studio_live.StudioFreeFontTests test_studio_live.StudioSavedTokensTests
-> Ran 25 tests ... FAILED (failures=6, errors=19)   (every new test failed; the bulk test was added later)
```
Failure kinds: missing controls (`0 != 1 : #liveMoveFirst`, `Locator.click` timeouts on `#bridgePopOut`/`#loadFreeFonts`/Arrange buttons), `'cqu4tvx' unexpectedly found`, `22 != 16` library cards, `rowdemo` still on Adobe keys, `live.tokens` import accepted (`Composition imported.` for invalid tokens). The fake was edited mid-run (imports became reference-counted); only the family-selection test is affected.

The Addendum 3 test `test_bulk_manifests_and_arrangement_only_targets` was written after the code. I proved it can fail by temporarily removing the `arrangementOnly` filter and the re-select, which gave a timeout (FAILED errors=1), then restored the file.

GREEN:
```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011
-> Ran 75 tests (29 Task C + 26 new + 20 legacy) ... OK   (green on three consecutive full runs: 74, 74, then 75 tests after the Addendum 3 test was added; the first full run found the one Gotham assertion above)
python3 scripts/verify.py --static-only
-> PASS HTML IDs: 86 unique static IDs; PASS JavaScript syntax; sha256 94268d827cada855d1d795c3de26fa933fa03fe85480465f6e9c1634c4a3ebe4; provenance PASS x3
git diff --check on the owned files: clean
```
Not run: Firefox (D010), `node --check fontkit-bridge.js` and the full `discover` (not my files). A one-off scratch probe (not a test) connected Studio to Task E's real bridge on `demo/index.html`: Arrange appeared, a DOM move and the HTML structure block worked. No page errors.

No new fixed sleeps: new tests use `wait_for_function`/events. Short `wait_for_timeout` calls (250-300 ms) exist only for negative assertions (no move on shortcuts in text fields, forged messages ignored, popups not opened).

## Legacy-test assertion changes

- `tests/test_studio_live.py:333` (Task C test `test_live_inspector_seeds_from_computed_and_respects_editable`): `assertIn('Gotham', options)` became `'Fraunces'`, because the library no longer has Gotham. No assertion in `test_font_kit_studio_v011.py` changed.
- `test_studio_live.py:1041` still uses `"Gotham"` as an arbitrary CSS string in an import-validation probe; it does not depend on the library.

## UI decisions

- **Arrange** (in the Live Target inspector, before Reset; rendered for any target with an `arrangement`): `#liveArrange` with `#liveArrangeInfo` ("Position 2 of 4 in Cards"), `#liveMoveFirst/Prev/Next/Last` (disabled at the ends), `#liveSiblingList` (`<ol>`, items `li[data-sibling-id]`, `draggable`, `tabindex=0`), `#liveMoveContainer` (every container except the current one) with `#liveMoveInto`, `#liveMoveGuard`. Only this section is re-rendered after a move, and focus returns to the same item or button.
- **Keyboard:** on a list item, Alt+Up/Down (also Left/Right) moves that item; plain arrows, Home and End move focus; Enter or Space selects it. Globally, Alt+Arrow moves the selected element while the Target App view is active and focus is not in a text field, select or the list; Alt+Shift+Arrow goes to first/last. After a click in the iframe selects an element, Studio pulls focus back to `#targetAppContainer` so the shortcuts work.
- **Drag and drop:** HTML5 DnD; the upper half of an item drops `before`, the lower half `after`.
- **One move at a time:** while a move is in flight or queued, further moves are ignored (the sibling positions are stale until the reply).
- **Strategy toggle** (`#liveMoveStrategyDom` / `#liveMoveStrategyCss`) appears only when `cssOrderAvailable`. The default is CSS order when `frameworkManaged`, else DOM. The choice is kept per container for the session. "Move into" always sends `strategy: "dom"`. `strategy` is always sent explicitly.
- **Guards:** every `move` rejection shows `#liveMoveGuard` with the guard name and the target's message. `#liveMoveForce` ("Move anyway", sends `force: true`) exists only for `framework-managed` (the alias `framework` is also accepted) when `overridable !== false`. It never appears for `form-owner`, `radio-group`, `label-reference`, `aria-reference`, `content-model` or `css-order`. The block clears on a new selection, a strategy change or a successful move. Revision conflicts on moves are retried once, like updates.
- **Warnings:** `design:warning` (kind `runtime-error`, session-gated, text only, 300 chars) shows in `#bridgeWarning` (status area, with Dismiss) and as the last 5 items in `#liveCodeWarnings` (code panel). They are cleared on a new session.
- **HTML tab:** `<!-- Structure: <name> <selector> — child order: … -->` plus the container html for each `structure` entry, then the text snippets; the old "No text changes yet." placeholder remains when there is nothing. **CSS tab:** `@import url("…");` lines come first (before the header comment), then, only when `structure` is non-empty, a comment pointing to the HTML tab. The change count also counts changed containers.
- **Imports:** the CSS tab lists the ledger's `imports` plus the library families used by Studio's saved overrides, so the persisted CSS still loads them after a reload. URLs pass a Studio-side allow-list (Google css2 `family`/`display`/`text`, or a Typekit kit) before being emitted.
- **Pop-out:** `#bridgePopOut` validates with the same gate as Connect (`resolveTarget`: http(s) only, file: only from file:, never Studio itself), then calls `window.open(url, "fontkit-target")` (exactly two arguments). A blocked popup gives "Pop-up blocked…" and leaves the iframe alone. On success, the iframe is unloaded (`about:blank`) so only one copy of the app runs, and it is hidden together with Studio's overlay layer. `#bridgePopoutPlaceholder` with `#bridgeFocusPopout` and `#bridgeDock` takes its place. Studio accepts messages only from that window at the expected origin and posts only to it. After `design:ready` it sends `design:mode {mode, overlay:true}`. `closed` is polled every 500 ms and gives `Disconnected (window closed)`. Dock closes the popup and reconnects the iframe. Connecting a new URL while popped out docks first. Every `design:mode` Studio sends in iframe mode carries `overlay:false`.
- **Free fonts:** 16 families, each with a slug key, `css` name, `sheet` query, tags and styles. The stylesheet URL is `https://fonts.googleapis.com/css2?family=<sheet>&display=swap`. Library cards load their stylesheet when scrolled into view (IntersectionObserver). The Composer loads each family it renders. `#loadFreeFontsLibrary` and `#loadFreeFonts` load all 16 and report progress; failed links are retried on the next press and never throw. After 8 s a "still waiting" status is shown. Selecting a library family in the Live Target inspector sends `fontStylesheet` in the same patch; choosing the page's own family sends `fontStylesheet: null` so the bridge can release the import. Studio loads the stylesheet itself too.
- **Kit presets:** `Free Google Fonts (OFL)` (default), `Bring your own Adobe kit`, `Custom / manual`. `#composerKitIds` is empty and nothing is loaded for Adobe until the user presses Load. All `cqu4tvx` text and the `YOUR_KIT_ID` link are gone from the HTML (the old head comment and the Library deck, audit and footer copy were rewritten).
- **Presets:** rowdemo, blank and asteria use Fraunces, Instrument Serif, Source Serif 4, Playfair Display (italic), Inter, JetBrains Mono and IBM Plex Mono. Imports of compositions with Adobe family keys map to a free look-alike (`LEGACY_FAMILIES`, e.g. gotham to Work Sans, daith-vf to Fraunces); unknown keys fall back to the first family as before.
- **Narrow layout:** at 390 px, with the guard, warning, strategy toggle and sibling list visible, there is no horizontal overflow (tested for the document and each new control).

## Free font list (all verified HTTP 200 against fonts.googleapis.com)

| Key | Name | Tags | `family=` value (URL = `https://fonts.googleapis.com/css2?family=<value>&display=swap`) |
|---|---|---|---|
| fraunces | Fraunces | serif, display, variable (wght, opsz) | `Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900` |
| crimson-pro | Crimson Pro | serif, variable | `Crimson+Pro:ital,wght@0,200..900;1,200..900` |
| source-serif-4 | Source Serif 4 | serif, variable (wght, opsz) | `Source+Serif+4:ital,opsz,wght@0,8..60,200..900;1,8..60,200..900` |
| playfair-display | Playfair Display | serif, display, variable | `Playfair+Display:ital,wght@0,400..900;1,400..900` |
| instrument-serif | Instrument Serif | serif, display | `Instrument+Serif:ital@0;1` |
| inter | Inter | sans, variable | `Inter:wght@100..900` |
| space-grotesk | Space Grotesk | sans, technical, variable | `Space+Grotesk:wght@300..700` |
| dm-sans | DM Sans | sans, geometric, variable | `DM+Sans:ital,wght@0,100..1000;1,100..1000` |
| work-sans | Work Sans | sans, geometric, variable | `Work+Sans:ital,wght@0,100..900;1,100..900` |
| ibm-plex-sans | IBM Plex Sans | sans, technical | `IBM+Plex+Sans:ital,wght@0,100..700;1,100..700` |
| archivo | Archivo | sans, variable | `Archivo:ital,wght@0,100..900;1,100..900` |
| bricolage-grotesque | Bricolage Grotesque | sans, display, variable (wght, opsz) | `Bricolage+Grotesque:opsz,wght@12..96,200..800` |
| bebas-neue | Bebas Neue | sans, display | `Bebas+Neue` |
| jetbrains-mono | JetBrains Mono | mono, technical, variable | `JetBrains+Mono:ital,wght@0,100..800;1,100..800` |
| ibm-plex-mono | IBM Plex Mono | mono, technical | `IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700` |
| space-mono | Space Mono | mono, typewriter | `Space+Mono:ital,wght@0,400;0,700;1,400;1,700` |

All URLs use only characters the bridge accepts (`A-Za-z0-9+:@;.,_-`), one family per URL.

## D017

The validated `live` field gains optional `tokens` (object of CSS custom properties). Rules: at most 64 entries; name `/^--[A-Za-z0-9_-]{1,120}$/`; value a non-empty string up to 300 chars with no `; { } < > \`, `url(`, comment markers, `!important` or newlines. Any invalid entry fails the whole import transactionally (16 bad shapes tested). Export writes `live.tokens` from the saved (acknowledged) tokens, and a tokens-only state still exports a `live` object (`overrides: {}`). Import replaces the saved tokens, so a `live` without `tokens` clears them, like overrides. A fresh Studio session that imports tokens and connects to a target without them gets the reconnect banner; Reapply sends them and nothing is applied silently. `canonicalRevision`/`canonicalTarget` now update on composition acks too, so a tokens-only export carries the right target and revision (before, it exported `target: ""`, revision 0).

## Contract notes and deviations (please review)

1. **Guard names** come from Task E's report: `form-owner`, `radio-group`, `label-reference`, `aria-reference`, `content-model`, `framework-managed`, `css-order`. Studio treats the first six non-overridably and shows "Move anyway" only for `framework-managed` (and the alias `framework`).
2. **CSS-order moves are saved state.** The bridge reports css-order only as `declarations.order` on every sibling. Studio keeps `order` (integer, -9999..9999) in `live.overrides` per target, mirrored from the ledger after a css-order move or a reset (for that sibling group only). It therefore appears in the CSS tab and the synced file, in the `live` JSON (the import accepts `order`), and in reconnect comparison. Reapply replays saved orders as css-order `design:move`s (one per sibling, in saved order), never as a patch key. DOM moves are session-only, shown in the HTML tab. This extends the plan (it names no persistence for moves); the alternative would silently drop saved order rules from the file after a reload.
3. **Bulk manifests (Addendum 3):** Arrange data comes from selected/applied manifests. After `design:ready` or `design:targets` Studio re-sends `design:select` for the selection when its arrangement has `count > 0` but no `siblings`. `arrangementOnly` targets are excluded from the target list and from the `Connected (N targets)` count; they stay in the sibling list. I chose to exclude them from the badge count; the plan only says "default target list".
4. **Imports** are reference counted (Addendum 3 / Task E). Studio sends `fontStylesheet: null` when the user picks a non-library family so the import can be released. This follows the plan and Addendum 3 (`null` releases), not a separately verified bridge behaviour.
5. **CSS tab note** about structural moves appears only when the ledger has `structure` entries (reading "plus a comment noting…" literally for the moment it is true).
6. **`design:mode`** always includes `mode` plus `overlay`. Task E accepts either field optionally, so this is valid.
7. **Real bridge:** the plan forbids the real bridge in my tests, and I used it only for a scratch probe. Task D's integration test still has to cover pop-out and arrange against it.

## Open concerns

- Chromium only (D010). The Alt+Shift+Arrow shortcut may be intercepted by some OS/layout switchers; the buttons and list are the full-fidelity path.
- With more than 100 siblings the sibling list is empty until the selection response arrives; `Position i of n` still shows.
- A popup that is already open from an earlier Studio page load (same name `fontkit-target`) is re-navigated by `window.open`; Studio does not take over a popup it did not open.
- The no-bridge timer also arms for pop-outs; a popup blocked mid-way shows `No bridge detected` after 4 s.
- Library cards load stylesheets on scroll; with no `IntersectionObserver` all 16 load at once.
- Task C's `Open concerns` still apply (typed-but-uncommitted hex on a stale control is dropped).
- README (Task D) still has to drop Adobe-default wording and document the pop-out, arrange workflow and the free-font defaults.

## Changes after first review (review: `v02-task-f-review.md`, Approved with fixes)

M3 (composition sync has no stylesheet key, D021) and M5 were not touched, as instructed. Only owned files changed; nothing committed.

### RED (before any Studio change; fake and tests first)

`cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live.StudioArrangeTests`
-> `Ran 15 tests, FAILED (failures=1, errors=4)`:

| Finding | Test | Failure |
|---|---|---|
| I1 | `test_reapply_replays_font_stylesheets_and_clears_stale_orders` (exact repro: Fraunces, reload target, Reapply) | timeout: the target's `imports` stayed `[]` |
| I1 (non-library) | `test_reapply_of_a_non_library_family_releases_the_stylesheet` | `'fontStylesheet' not found in {'fontFamily': 'Georgia, serif'}` |
| M2 | `test_reapply_clears_a_target_css_order_that_studio_no_longer_saves` | timeout: the target kept `c,a,b,d` |
| M1 | `test_bulk_manifests_and_arrangement_only_targets` (fake bulk mode now omits both keys) | timeout: no re-select, stale list |
| M4 | `test_alt_arrow_shortcuts_only_apply_in_the_target_view_and_never_inside_text_fields` (now checks Alt+Left/Right) | the shortcut moved the element / was default-prevented |

### Fixes

- **I1:** every replayed update patch that carries `fontFamily` also carries `fontStylesheet`: the library URL for a library family, `null` otherwise. It is rebuilt from the saved family, so nothing new is stored.
- **M1:** `normalizeArrangement` treats a missing `siblings` as `[]` and flags the result `complete` only when `siblings` is non-empty and `containers` is an array. `fetchFullArrangement` re-selects whenever the selected arrangement is incomplete. The fake's bulk mode omits both keys (`fake.bulkOmitsKeys()` is asserted).
- **M2:** when the target has an `order` for a target that Studio no longer saves, Reapply sends `design:reset` for that target (queued first; it clears the whole order group), then the target's other saved values in full. I chose reset rather than `order: null` because `order` is not a patch key in the contract. Saved orders are replayed afterwards as before. Side effect: the reset briefly empties that target's saved overrides until the update acknowledgement restores them.
- **M4:** the global shortcut is Alt+Up/Down only (Shift for first/last). Alt+Left/Right is neither handled nor default-prevented; the sibling-list item keeps its own keys. The Task F test for this uses Alt+Down instead of Alt+Right.
- **Rule of three:** `selectedArrangement()` replaces the five `live.selectedId ? arrangementOf(live.selectedId) : null` copies; `detachSession()` replaces the three `resetSessionState(); live.sessionId = null; live.targets = new Map();` blocks. No behaviour change (full suite green).

### GREEN

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011
-> Ran 78 tests ... OK   (two consecutive runs)
python3 scripts/verify.py --static-only
-> PASS HTML IDs: 86 unique; PASS JavaScript syntax; sha256 33bde4fffaab9587bbe573a225c01891a46a8d543c8f4ecc37aeb92a09a8fa8d; provenance PASS x3
git diff --check on owned files: clean
```
Firefox not run (D010). The real bridge was not used in this round.

## Changes after second review (review: "Re-review after first changes" in `v02-task-f-review.md`)

Only owned files changed; nothing committed.

### RED (tests first, unchanged Studio `33bde4ff…`)

`cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live.StudioArrangeTests.<test>` (3 new tests) -> `FAILED (failures=1, errors=2)`:

| Finding | Test | Failure |
|---|---|---|
| R1 | `test_reapply_is_transactional_when_the_follow_up_is_rejected` (auto-sync on, `fake.rejectNext` on the follow-up) | `KeyError: 'live'`: the export has no saved overrides after the rejection (the reviewer's wipe) |
| R2 | `test_reapply_states_that_it_resets_a_dom_moved_arrangement` | banner text has no mention of the reset |
| R3 | `test_reapply_replays_a_partial_saved_order_group_after_the_reset` | timeout: card.a's saved order never returns to the target |

### Fixes

- **R1 (transactional Reapply):**
  - (a) Reset ops created by Reapply are tagged and their ack no longer deletes `live.overrides` or runs `syncOrderFromLedger`. Saved state changes only when the replayed update/move/composition acks arrive.
  - (b) `scheduleAutoSync` returns while a request is in flight or queued, and while `live.conflict` is open. The conflict now stays open for the whole Reapply and is cleared only when the last step is acknowledged (`finishReapply`, which then schedules the sync).
  - (c) A rejection, an 8 s timeout or a reload stops the run: remaining Reapply steps are dropped, saved state is kept, the banner stays open with "Reapply stopped (reason). Studio's saved overrides were kept and nothing was written to the overrides file…", and the code status shows the same error. A reload recomputes the conflict from the unchanged saved state, so the banner returns. Pressing Reapply again retries, and the test asserts the retry succeeds, the banner hides and the PUT carries the saved rule. In the rejection case no PUT is sent.
  - Reapply steps are never merged into other queued ops.
- **R2 (chosen: state it):** a CSS-order move cannot restore "no order" (it assigns `order` to every sibling), so the reset cannot be avoided. The banner now says "Reapply will also reset the arrangement of N sibling group(s) (a leftover CSS order can only be cleared that way)", adding "which also undoes the DOM moves in them (see the HTML tab's structure blocks)" when the ledger has structure for that container. At most one reset is queued per sibling group. After Reapply the preview equals Studio's saved state (test asserts DOM and visual order are original and saved overrides unchanged).
- **R3:** a group that was reset is always replayed, even when its saved members matched the target before the reset.

### GREEN

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -> Ran 81 tests OK
python3 -m unittest discover -s tests (same env) -> Ran 182 tests OK
python3 scripts/verify.py --static-only -> PASS (86 unique IDs, JS syntax, sha256 7361ec8a4004a0c230696506df1618b6ab9733ab937d9998877d6961b06b560c, provenance x3)
git diff --check on owned files: clean
```
Firefox not run (D010). Replay of a partial saved group assigns the bridge's order to every sibling, so the saved JSON afterwards holds an order for each sibling (the bridge writes all of them).
