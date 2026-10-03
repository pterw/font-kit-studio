# v0.2.0 Task E report: bridge arrangement, pop-out overlay, font stylesheets, framework robustness

Branch: the v0.2 PR branch, after the Task B and Task C changes. Task E is still uncommitted. No commits or pushes were made by this task. `font_kit_studio_v0.1.1.html`, `tests/test_studio_live.py` and `tests/fixtures/studio/**` also show as modified in `git status`; those belong to concurrent Studio work (Tasks C/F), not Task E.

## Files changed

| File | Change |
|---|---|
| `fontkit-bridge.js` | About +1085/-56 lines: arrangement manifest, `design:move`, structure and imports ledger, overlay mode, font stylesheets, SPA/HMR robustness, carry-overs R1, R2, M7/R3, M8. |
| `tests/test_bridge_runtime.py` | 34 new tests in 11 new classes (ArrangementManifest, Move, CssOrder, MoveGuard, RuntimeWarning, PopOutOverlay, FontStylesheet, SpaRobustness, LedgerHtml, AutoSelector, LegacyLayoutStructure), plus 3 more added during implementation. Existing tests adjusted for the new contract fields (see Deviations). `open()` now routes `fonts.googleapis.com` and `use.typekit.net` to empty CSS and records the requests, so no test touches the network. |
| `tests/fixtures/bridge/host.html` | `popupSession` and `popupControl()` helpers. |
| `tests/fixtures/bridge/target-arrange.html` | New. Button group (flex), card grid (`display:grid`, one card without an author id), plain order container with a `<script>` child, form with segmented control (radios plus `label[for]`), implicit-label checkbox, outside container (with an `<img>` and an aria target), React/Vue/Svelte fake subtrees (`__reactFiber$test`, `__vue__`, `__svelte_meta`) and an Angular-style `ng-version` subtree. It also holds a MutationObserver that throws or rejects on demand (`window.__throwMode`). |
| `tests/fixtures/bridge/target-spa.html` | New. `render()` replaces the whole `#app` subtree; opt-in ping-pong re-render; style-batch counter. |
| `tests/fixtures/bridge/target-twice.html`, `target-deferred.html`, `construct-restricted.js`, `target-deep.html` | New. Script loaded three times; deferred scripts for R1; two identical deep trees for M8. |
| `docs/implementation/tasks/v02-task-e-report.md` | This report. |

## RED evidence

Tests were written first. Before any bridge change I confirmed `git diff --quiet -- fontkit-bridge.js` (the bridge was unchanged).

Command (from `tests/`): `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime`

Result: `Ran 67 tests in 301.915s — FAILED (failures=102, errors=10)`. The count includes subtests. 34 tests are new; 30 of them failed and 4 were already green (see below). Four existing tests failed only because the ledger and manifest gained fields.

| Area | Test (class.method) | RED failure |
|---|---|---|
| Arrangement | `ArrangementManifestTests.test_manifest_arrangement_…` and `test_a_target_is_not_offered_…` | `KeyError: 'arrangement'` |
| Move | `MoveTests.test_move_by_index…`, `…before_after…`, `…into_a_container…`, `…ledger_structure…`, `…reset_all_does_not_resurrect…` | `'timeout' != 'design:applied'` (no `design:move` handler); structure: `KeyError: 'structure'` |
| Move rejections | `MoveTests.test_every_invalid_move_is_rejected…` (33 subtests) | `'timeout' != 'design:rejected'` |
| css-order | `CssOrderTests` (3 tests) | `'timeout' != 'design:applied'` / `'design:rejected'` |
| Guards | `MoveGuardTests` (4 tests) | `'timeout' != 'design:rejected'`; `StopIteration` where the sibling radio and label were not yet targets |
| Warnings | `RuntimeWarningTests.test_runtime_errors_after_…` | no `design:warning` message |
| Overlay | `PopOutOverlayTests` (2 tests) | `TimeoutError: wait_for_function` (no overlay nodes appear on `design:mode {overlay:true}`) |
| Font stylesheets | `FontStylesheetTests` (3 tests, 48 subtests) | `('unsupported-property', 'fontStylesheet') != ('unsupported-value', 'fontStylesheet')`; `'design:rejected' != 'design:applied'` |
| SPA re-apply | `SpaRobustnessTests.test_overrides_are_reapplied…`, `…debounced…` | `TimeoutError`: the replacement element never gets its style |
| Selected replaced | `SpaRobustnessTests.test_a_replaced_selected_target_stays_selected…` | `[{'type': 'design:selected', …, 'targetId': None}] != []`: a re-render wrongly cleared the selection |
| Script twice | `SpaRobustnessTests.test_loading_the_script_twice…` | `False is not true`: the second load replaced `window.FontKitBridge` |
| R1 | `SpaRobustnessTests.test_a_later_constructed_instance_replaces…` | `False is not true`: the open auto instance stays |
| R2 | `LedgerHtmlTests.test_long_data_urls_are_abbreviated…` | `'src="data:image/png;base64,…(12122 bytes)"' not found in '<img … src="data:image/png;base64,iVBORw0KGgo…`: the full data URL was in the ledger html |
| M7/R3 | `LegacyLayoutStructureTests` | `KeyError: 'structure'` |
| M8 | `AutoSelectorTests.test_auto_selectors_stay_unique…` | `Lists differ: [3, False] != [1, True]`: one auto selector matched 3 elements |
| Existing, new fields | `HandshakeTests`, `TargetedUpdateTests` x2, `LegacyCompositionTests` | `{'tokens': {}, 'targets': []} != {'tokens': {}, 'targets': [], 'structure': [], 'imports': []}` |

Already green at RED, so characterization only (never manufactured):
- `test_move_and_overlay_and_fonts_are_ignored_before_hello`: session gating already makes the bridge inert.
- `test_errors_outside_the_one_second_window_or_after_a_rejection_are_not_reported`: no warnings were sent at all.
- `test_removing_the_selected_target_clears_the_selection`: it only passes by a race (the `ResizeObserver` fires before discovery prunes the record). `emitBounds` now looks up a replacement and `syncSelection` runs after discovery, so removal is reported either way.
- `test_a_connected_auto_instance_is_not_replaced`.

Two more RED checks done with a temporary revert, then restored:
- `MoveTests.test_selectors_in_move_replies_describe_the_new_position` fails without the `domVersion` bump after a DOM move: `'#card-grid > article.card:nth-of-type(3)' == '#card-grid > article.card:nth-of-type(3)'`, a stale selector.
- `ArrangementManifestTests.test_bulk_manifests_leave_out_the_sibling_list_of_very_large_groups` fails with `BULK_SIBLINGS_MAX` disabled: the list has about 150 siblings x 150 targets.

## GREEN evidence

Command (from `tests/`): `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server -v`

Result: `Ran 88 tests in 70.188s — OK` (70 bridge, 18 preview server). All 33 earlier bridge tests still pass. The new SPA, warning and overlay classes were run 3 times with no flakes. `node --check fontkit-bridge.js` passes. `require('./fontkit-bridge.js')` still exports `FontKitBridge`, `initFontKitBridge` and `PATCH_RULES` (which now includes `fontStylesheet`). Firefox is not installed (D010) and was not run.

Smoke on the real `demo/index.html` (scratch probe, not in the repo): 46 targets, every selector resolves to exactly its own element, no framework detected, no page errors. Pathological probe with 1500 sibling buttons: hello in 1.5 s with a 1.6 MB ready message, move and update about 0.15 s each.

## Message shapes (real output, JSON from the test harness)

Every message carries `protocolVersion: 1` and, except `bridge-ready`, `sessionId`. Fields not changed by Task E are omitted below.

### `TargetManifest.arrangement` (single-target form: `design:selected.target`, `design:applied.target`; amended in changes after first review, see below)

```json
{
 "containerKey": "arr.group",
 "containerName": "Actions",
 "containerSelector": "[data-design-id=\"arr.group\"]",
 "index": 1,
 "count": 3,
 "siblings": [{"id": "arr.btn.a", "name": "BUTTON: \"Alpha\"", "tag": "button"}, {"id": "arr.btn.b", "name": "BUTTON: \"Beta\"", "tag": "button"}, {"id": "arr.btn.c", "name": "BUTTON: \"Gamma\"", "tag": "button"}],
 "containers": [{"key": "container:1", "name": "Card one"}, {"key": "arr.group", "name": "Actions"}, {"key": "container:2", "name": "Card one"}, {"key": "arr.plain", "name": "div.plain"}],
 "cssOrderAvailable": true,
 "frameworkManaged": null
}
```

(`containers` shortened to 4 of 11 entries here.) Notes:
- `frameworkManaged` is one of `null | "react" | "vue" | "svelte" | "unknown"`. `"unknown"` is used for an Angular `ng-version` subtree.
- `siblings` and `index` are in layout order. For a flex or grid parent that is the visual order (stable sort by computed `order`); otherwise it is DOM order. `index` is the target's position in that list.
- `containers` omits the target itself and its descendants.

### `design:move` (Studio to bridge)

```json
{"type": "design:move", "protocolVersion": 1, "sessionId": "s1", "requestId": "r1", "baseRevision": 0,
 "targetId": "arr.p.3", "to": {"container": "arr.group", "index": 0}, "strategy": "dom", "force": false}
```

- `to` is exactly one of `{index}`, `{before}`, `{after}`, `{container, index?}`.
- `strategy` (`"dom"` default, or `"css-order"`) and `force` are optional.

### `design:applied` for a move

```json
{"type": "design:applied", "protocolVersion": 1, "sessionId": "s1", "requestId": "r1", "revision": 1,
 "targetId": "arr.p.3",
 "canonicalPatch": {"move": {"container": "arr.group", "index": 0}},
 "target": {"id": "arr.p.3", "…": "full TargetManifest with a fresh arrangement"},
 "changes": {
  "tokens": {},
  "targets": [],
  "structure": [
   {"containerKey": "arr.plain", "selector": "[data-design-id=\"arr.plain\"]", "stable": true,
    "name": "DIV: \"Plain one Plain two ig…\"",
    "html": "<div class=\"plain\" data-design-order-container=\"true\" data-design-id=\"arr.plain\">…</div>",
    "order": ["P: \"Plain one\"", "P: \"Plain two\""]},
   {"containerKey": "arr.group", "selector": "[data-design-id=\"arr.group\"]", "stable": true,
    "name": "DIV: \"Alpha Beta Gamma\"",
    "html": "<div class=\"btn-group\" data-design-id=\"arr.group\" role=\"group\" aria-label=\"Actions\">\n    <p data-design-id=\"arr.p.3\">Plain three</p><button …>Alpha</button> …</div>",
    "order": ["P: \"Plain three\"", "BUTTON: \"Alpha\"", "BUTTON: \"Beta\"", "BUTTON: \"Gamma\""]}
  ],
  "imports": []
 }}
```

- `structure` is ordered by first change, with the source container before the destination.
- `order` holds element names in current DOM order. The names are the same strings as `arrangement.siblings[].name`.
- `canonicalPatch.move.index` is the final index in the destination's layout order.
- A css-order move returns the same `canonicalPatch` shape with no `strategy` field, `structure: []`, and one `changes.targets` entry per sibling, each with `declarations: {"order": "0"}` and so on. Example entry: `{"targetId": "arr.p.3", "selector": "[data-design-id=\"arr.p.3\"]", "stable": true, "name": "P: \"Plain three\"", "role": "body", "declarations": {"order": "0"}, "text": null, "originalText": "Plain three", "html": "<p data-design-id=\"arr.p.3\">Plain three</p>"}`.

### `design:rejected` for a move

`reason` is `invalid-message`, `revision-conflict`, `unknown-target` or `unsupported-value`, with these `detail` shapes:

```json
{"reason": "invalid-message", "detail": {"field": "to"}}
{"reason": "unknown-target", "targetId": "arr.btn.a", "detail": {"targetId": "no.such.target", "field": "to.before"}}
{"reason": "unsupported-value", "detail": {"property": "to", "requested": {"index": 9}, "reason": "index-out-of-range", "count": 4}}
{"reason": "unsupported-value", "detail": {"property": "to", "requested": {"container": "zzz"}, "reason": "unknown-container"}}
{"reason": "unsupported-value", "detail": {"property": "strategy", "requested": "sideways"}}
```

- `invalid-message` `detail.field` is `to`, `to.index`, `to.before`, `to.after`, `to.container`, `targetId`, `strategy` (non-string) or `force` (non-boolean).
- `detail.reason` for `unsupported-value` on `to` is one of `index-out-of-range`, `unknown-container`, `into-self`, `into-descendant`, `relative-to-self`, `void-or-replaced-container`, `unarrangeable-reference`.
- `unknown-target` for a `before`/`after` reference puts the unknown id in `detail.targetId`; the top-level `targetId` is the moving target.

Guard rejections (`reason: "unsupported-value"`, `detail.guard` always present):

```json
{"detail": {"property": "move", "requested": {"index": 0}, "guard": "framework-managed", "overridable": true, "framework": "react",
            "message": "This part of the page is managed by react; it may undo a DOM move. Use the CSS order strategy, or move anyway."}}
{"detail": {"property": "move", "requested": {"container": "arr.plain"}, "guard": "form-owner", "overridable": false,
            "message": "This move would take a form control out of its form, so it would no longer be submitted with it."}}
{"detail": {"property": "strategy", "requested": "css-order", "guard": "css-order", "overridable": false,
            "message": "The CSS order strategy needs a flex or grid parent."}}
```

Guard names: `form-owner`, `radio-group`, `label-reference`, `aria-reference`, `framework-managed` (the only overridable one, with `force: true`; its detail has `framework`), and `css-order` (parent not flex or grid, or destination in another container).

### `design:mode` with overlay (Studio to bridge)

```json
{"type": "design:mode", "protocolVersion": 1, "sessionId": "p1", "mode": "select", "overlay": true}
```

- `mode` and `overlay` are each optional, but at least one must be present.
- A malformed value (for example `overlay: "yes"`) ignores the whole message.
- There is no reply. The bridge's outline is `#fontkit-bridge-overlay` (selection) and `#fontkit-bridge-hover`, both `pointer-events: none`.

### `design:warning`

```json
{"type": "design:warning", "protocolVersion": 1, "sessionId": "s1", "requestId": "r9", "targetId": "arr.btn.c",
 "kind": "runtime-error", "message": "Uncaught Error: app exploded after the change"}
```

- `message` is at most 300 chars. A rejected promise gives `Unhandled promise rejection: <reason>`.
- It is sent for `error` and `unhandledrejection` within 1000 ms after an applied `design:update` (targeted or composition) or `design:move`.
- It goes to the most recent applied request only. `targetId` is `"global"` for composition updates.
- `design:reset` and `design:restore-text` do not start a window.

### `fontStylesheet`

```json
{"type": "design:applied", "…": "…", "targetId": "arr.btn.c",
 "canonicalPatch": {"fontStylesheet": "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"},
 "changes": {"tokens": {}, "targets": [], "structure": [], "imports": ["https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap"]}}
{"type": "design:rejected", "requestId": "r11", "revision": 4, "reason": "unsupported-value", "targetId": "arr.btn.c",
 "detail": {"property": "fontStylesheet", "requested": "http://x"}}
```

The DOM gets `<link rel="stylesheet" href="…" data-fontkit-font="">`, appended to `<head>`.

### Selected target removed

```json
{"type": "design:selected", "protocolVersion": 1, "sessionId": "s1", "targetId": null}
```

## Contract interpretation notes

I picked the most literal reading wherever the contract was silent. Please review these.

1. **Every sibling is a normal target.** "Each sibling is registered (auto if needed)" is taken literally: sibling elements get `data-design-id`, `data-design-role` and `data-design-name` (bridge-owned, stripped from ledger html), and they appear in `design:ready` and `design:targets`.
   - Consequence: hovering or clicking any container in the page now selects the nearest registered ancestor-or-self, so containers and cards are selectable. I changed one existing test that used a bare `div` as its "no target" area.
   - A bridge attribute that the author or a framework later overwrites with a different value is treated as the author's (the bridge now remembers the value it wrote).
2. **Container keys.** The key is the container's author `data-design-id`; a bridge-added auto id is not used. Otherwise it is `container:<n>`, assigned in first-seen order and stable for the page's lifetime. Any connected element whose author `data-design-id` equals the key is an accepted `container`, not only the listed candidates.
3. **Layout order.** See the arrangement note above: `siblings` and `index` are in layout order. `design:move` positions use the same list, with the moving element removed from it.
   - `index` is the final index, range `0..count-1`.
   - For a container, an index equal to the destination's current child count appends; the default (no index) also appends.
   - A DOM append goes after the last sibling element, so it stays before trailing scripts.
4. **`before` and `after` may name a target in another container.** The move then goes into that container. A reference equal to the target is `relative-to-self`; a reference inside the target is `into-descendant`. I reject both rather than treat them as no-ops.
5. **Malformed versus unsupported.**
   - Type errors in `to`, `strategy` or `force` are `invalid-message` with `detail.field`.
   - A well-typed but unsupported value is `unsupported-value`: strategy outside `dom` and `css-order`, index out of range, unknown container, self, descendant, void or replaced container.
   - Void or replaced containers: `img`, `input`, `svg` and the rest of the `NO_CHILDREN` set in the code.
6. **Guards.**
   - **Form owner.** Only moves that take a control out of its current owner count. `form="…"` controls are exempt, and controls whose owner form is inside the moved subtree are unaffected. Moving an ownerless control into a form is allowed, because the contract says "out of". The checked controls are `input, select, textarea, button, fieldset, output`, or any element containing one.
   - **Radio group.** A move is blocked when same-name radios (same form owner) remain outside the moved subtree and the destination is not inside their lowest common ancestor.
   - **Label and aria.**
     - Implemented and tested: the implicit-label case, a control leaving the `<label>` that wraps it. This gives `label-reference`.
     - Implemented but not testable here: the root-scoped id check (`getRootNode`) for `label[for]`, `aria-controls`, `aria-labelledby` and `aria-describedby`, in both directions (references from the moved subtree, and references to ids inside it). Every container this bridge can address is in the main document, so same-document id references cannot break (the resolving root does not change). The `getRootNode` code path therefore cannot be reached by any move today, and has no test. This is the one place where the contract is satisfied but unreachable.
   - **Framework.** Checked on the moved element's ancestors and on the destination parent. `force: true` overrides only this guard.
   - **Order.** Hard guards come first, then the framework guard, so a user who forces a framework move still sees any hard guard.
   - **css-order.** It skips all DOM guards, because the DOM is untouched.
7. **css-order details.**
   - The strategy needs a flex or grid parent and the same container.
   - It writes `order: <i>` (`!important`) on every arrangeable sibling, so every sibling gets a ledger entry.
   - Resetting any member of the group (`design:reset` with its `targetId`) clears `order` on the whole group; reset-all clears it with all other styles.
   - Later css-order moves are relative to the visual order, which is what the manifest reports.
8. **`structure`.**
   - A container is listed while its element order differs from the original it had when the bridge first touched it. Elements the app adds are ignored.
   - Once the order matches again, the entry disappears, the snapshot is dropped, and the whitespace and text nodes are put back exactly.
   - Reset-all restores every captured container's child nodes (text included), byte for byte (the tests compare `innerHTML`).
   - A per-target reset puts the element back before its original successor (or at the end), which may not restore whitespace nodes exactly until the container is fully back to its original element order.
   - Containers touched by the legacy layout reorder (M7/R3) take part in the same mechanism.
9. **Overlay.**
   - It exists while the page option `enableHighlightOverlay` is on or `overlay: true` was received. It is removed on `overlay: false`, on any new `design:hello`, and when the session drops.
   - A session pinned to `window.opener` is polled every 500 ms, so closing the opener removes the overlay without any interaction. Interaction is not needed.
10. **Font stylesheets.**
    - Strict string matching, no URL parsing.
    - Google Fonts: `https://fonts.googleapis.com/css2?` plus 1 to 8 `family=`, at most one `display=` (`auto|block|swap|fallback|optional`) and at most one `text=`. Values use `A-Za-z0-9+:;,@.-_~` and `%XX`. Total length is at most 2000.
    - Typekit: `https://use.typekit.net/<6-10 alnum>.css`.
    - Whitespace, fragments, ports, user info, other hosts and other params are all rejected.
    - The patch key is allowed on every target kind (no `editable` group).
    - **Reference model.** One `<link>` per distinct URL, referenced by targets. `null`, a different URL on the same target, or a target reset releases that target's reference, and a link with no references is removed. `imports` therefore lists only stylesheets still in use, ordered by first injection. Reset-all removes everything.
11. **SPA re-apply.**
    - Only author-id (stable) targets are re-applied. The old detached element's ledger declarations and text are copied to the replacement. This covers legacy composition styles and css-order too.
    - The replacement is discovered via the MutationObserver with a 30 ms trailing debounce (instead of 120 ms) when the removed subtree held overrides.
    - Loop guard: at most 5 re-applications per target per 2 s, then a single `console.warn`.
    - A removed element's overrides wait up to 10 s for a replacement.
    - A selected target replaced by a re-render stays selected on the new element.
    - If an element is removed with no replacement, `design:selected {targetId: null}` is sent after discovery.
12. **Double load.** A second load never replaces `window.FontKitBridge` or `window.initFontKitBridge`, and creates no second instance (the first class stays; an HMR re-execution does not pick up new code until a page reload).
13. **R1.** `new FontKitBridge()` replaces the existing instance only when that instance was auto-created and no Studio has ever said hello. The old instance is fully disposed: listeners, observers, timers and overlay removed. Otherwise the old warning stays and both instances answer.
14. **R2.** Ledger html abbreviates any `data:` URL longer than 256 chars inside attribute values to `data:<mime>;<enc>,…(<N> bytes)`, where N is the full length of the URL. Short ones are untouched.
15. **M8.** An auto selector is `#id` if the element has a unique id; otherwise a path of at least 4 steps (the nearest unique ancestor id counts as one), extended upward until `querySelectorAll(selector)` matches exactly the element. The path is anchored with `body >` only if no shorter form is unique.
    - Selectors are cached per element, keyed by a DOM-version counter bumped on childList and class/id mutations, and by the bridge's own moves.

## Deviations

1. **`siblings` is empty in bulk manifests of very large groups.** `design:ready` and `design:targets` carry `arrangement.siblings: []` when a sibling group has more than 100 elements (`count` and `index` stay correct). The contract requires `siblings` in every manifest, but with it a 1500-item list would send about 1500 x 1500 entries (hundreds of MB). `design:selected`, `design:applied` and `design:inspect-result` always carry the full list, which is what an Arrange UI needs. Studio should read the list from the selected manifest.
2. **Existing tests changed** because of the contract's new fields, not because behaviour regressed:
   - four ledger-shape assertions now expect `structure` and `imports`;
   - the manifest key-set assertion now includes `arrangement`;
   - the hover test no longer uses a bare `div.spacer` as its off-target region (siblings are now targets), and uses the header's padding instead.
3. **`design:ready.capabilities`** is unchanged (the contract lists six keys and the existing test asserts them). Studio can detect arrangement support from `target.arrangement`.
4. `canonicalPatch.move` carries only `container` and `index`, as the contract says, so a css-order move cannot be told apart by that field; Studio knows the strategy it sent.

## Open concerns

- **Message size.** `containers` is repeated in every target's arrangement. The demo's 46 targets give an 88 KB `design:ready`. Studio only needs it on the selected target; if size becomes a problem, moving `containers` to a single top-level field is a contract change to be decided (decided in Addendum 3).
- **Hover and click behaviour.** Making every sibling a target changes what is selectable in the page. Studio may want a "prefer text targets" hover rule.
- **No guard against invalid HTML content models** (for example a `<p>` into a `<ul>`, a `<tr>` out of a `<table>`). Only the contract's guards are implemented.
- **Per-target reset** after a DOM move may not restore whitespace text nodes exactly until the container is fully back to its original order.
- **A pop-out whose opener is a frame** is out of scope; the poll applies to `window.opener` only.
- **Not verified:** the `getRootNode`-scoped label/aria code path (see note 6). Firefox was not run.
- **Studio-side items for Task F:**
  - send `protocolVersion` and `sessionId` on every message;
  - after a css-order move, `siblings` order is visual;
  - `force` is only meaningful for the `framework-managed` guard;
  - a `design:warning` arrives after `design:applied`, within about 1 s.

## Changes after first review (review: `v02-task-e-review.md`, "Approved with fixes"; plan Addendum 3, D019)

Base: the changes after changes after first review (docs commits), Task E still uncommitted. Own files only, no commits. Each change had a failing test first.

Command (from `tests/`): `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server`
Result after the fixes: `Ran 98 tests in 90.249s — OK` (80 bridge, 18 server). `node --check fontkit-bridge.js` passes. The new SPA, hit-test and attribute-write classes ran 3 times with no flakes. Firefox is not installed.

### RED (before any bridge change, run on the 17 affected tests)

`FAILED (failures=16, errors=1)`.

| Item | Test | RED failure |
|---|---|---|
| I1 | `ArrangementManifestTests.test_manifest_arrangement_…` | `Items in the first set but not the second: 'containers' : arr.group` |
| I1 | `ArrangementManifestTests.test_ready_and_targets_messages_grow_near_linearly_with_the_page` | `2.83 not less than 2.4 : {30: 1349903, 60: 3815783}` (780 targets: 3.8 MB, 4.9 KB per target) |
| arrangementOnly | `test_sibling_only_registrations_are_flagged_and_stay_addressable` | `KeyError: 'arrangementOnly'` |
| arrangementOnly | `SiblingOnlyHitTestTests.test_clicking_list_text_or_a_summary_does_not_select_the_wrapper` (demo) | `None is not True` (the flag is missing; the old code also selected the `ul` and the `summary`, per the review's measurements) |
| content-model | `ContentModelGuardTests.test_block_elements_cannot_go_into_inline_or_phrasing_parents` | `'design:applied' != 'design:rejected'` |
| M2 | `FontStylesheetTests.test_only_strictly_valid_font_stylesheet_urls_are_accepted` | 8 subtests: `%0a`, `%2F`, `%5C`, `%3C…%3E`, `%27`, `%22`, `%00` were accepted |
| M1 | `LedgerHtmlDataUrlTests.test_any_long_data_attribute_is_abbreviated…` | the `data:image/svg+xml,<svg xmlns='…' …>` payload (1.5 KB, raw spaces and quotes) was in the ledger html in full |
| M3 | `AttributeWriteTests.test_an_app_that_rerenders_on_any_attribute_change_cannot_trap_the_bridge` | `24 not less than or equal to 2 : (46, 70)`: the loop kept going (46 renders in 5.5 s, 24 more in the next 3 s) |
| M5 | `test_container_names_prefer_design_name_aria_label_heading_id_then_tag_class` | `'DIV: "Alpha Beta Gamma"' != 'Actions'` |

Already green at RED (characterization only): `test_a_semantic_element_registered_as_a_sibling_first_is_an_ordinary_target`, `test_inline_into_inline_and_block_into_block_and_in_place_moves_are_allowed`, and `test_an_unchanged_style_or_attribute_value_is_never_rewritten` (Chromium does not emit a mutation record for a same-value `style.setProperty`; the guard is kept for browsers that do, and for attributes).

### Changes

1. **I1, bulk manifests.** In `design:ready` and `design:targets`, `arrangement` has no `containers` key; `siblings` is `[]` when the parent has more than 100 element children (as before). `design:selected`, `design:applied` and `design:inspect-result` carry the full arrangement. Size test on a generated DOM (30 and 60 sections of 12 paragraphs, 780 targets): `design:ready` is 678 KB and 1.33 MB (ratio 1.96), about 1.7 KB per target, against 1.35 MB and 3.82 MB before. The test asserts ratio < 2.4, < 2500 bytes per target and < 2 MB, and that a later `design:targets` post is bulk too. I did not build the review's exact 718-target page; the generated one gives the same effect (the per-target `containers` list is gone).
2. **`arrangementOnly: true`.**
   - A record created only because it is a sibling of a target (no author id, no `data-design-role`, not matching the semantic selectors) gets `arrangementOnly: true`. The manifest key is present only when true.
   - `closestTarget` skips these records, so hover and click fall through to the next ordinary target ancestor, or to nothing; with nothing, the click is not intercepted, so the page handles it. Interact mode never intercepted clicks.
   - They stay addressable by id for `design:select` and `design:move`, and their selected manifest carries the flag.
   - The flag is cleared if a discovery pass or `registerElementTarget` finds the element is semantic or explicit after all.
   - Demo test: clicking a `.plan ul li` selects nothing and produces no hover for the `ul`; clicking the FAQ `summary` in Select mode selects nothing and the `<details>` toggles; Interact mode toggles it back; an `h3` still selects, and `design:select` on the `ul` id works.
3. **Content-model guard.** `detail.guard: "content-model"`, `overridable: false`, `property: "move"`, only for `strategy: "dom"`. It fires when the moved element is one of div, p, section, article, aside, header, footer, nav, ul, ol, table, form, figure, h1-h6, blockquote or details and the destination parent is one of p, h1-h6, span, a, button, label or summary. It checks the destination parent only (an `a` that already holds a block child can still be reordered, since a move inside the same parent is skipped). It sits after the form, radio and label/aria guards and before the framework guard, so `force: true` does not override it. Example detail: `{"property": "move", "requested": {"container": "arr.para"}, "guard": "content-model", "overridable": false, "message": "A <p> cannot be placed inside a <p>; the browser would repair the markup differently."}`.
4. **M2.** Percent-escapes in `family=` and `text=` are limited to `%20 %2B %2C %3A %3B %40` (either hex case); everything else, including a bare `%` or `%2`, is `unsupported-value`.
5. **M1.** Any attribute whose value starts with `data:` (leading whitespace allowed) and is longer than 256 chars is abbreviated whole, to `data:<mime>;<enc>,…(<N> bytes)` with N the full value length, even with raw spaces and quotes. Other attributes keep the in-value `data:` URL replacement (`srcset`, `url()`).
6. **M3.**
   - Bridge-owned attributes and inline style properties are not written when the value is already identical.
   - Mutation-triggered rediscovery now backs off: when it runs more than 10 times in 2 s, the wait grows 250 ms, 500 ms, 1 s, 2 s, 4 s up to 8 s while the storm lasts, with one `console.warn`. A quiet period resets it.
   - The test uses an app that re-renders on any attribute mutation anywhere in the page, with an auto heading the bridge decorates on every render. Over 5.5 s it renders about 46 times; in the next 3 s at most 2 more, and the bridge still answers a normal update after the app calms down. It slows the loop to one run per few seconds rather than stopping it outright.
7. **M5.** `containerName` is now `data-design-name`, then `aria-label`, then the first heading text inside (at most 40 chars, with an ellipsis), then `#id`, then `tag.class`. This also changes `structure[].name`.

### Message shape changes (Task F should match these)

Bulk manifest arrangement (inside `design:ready.targets[]` and `design:targets.targets[]`; amended in changes after second review: no `siblings` and no `containers` at all, whatever the group size):

```json
{"containerKey": "arr.group", "containerName": "Actions", "containerSelector": "[data-design-id=\"arr.group\"]",
 "index": 1, "count": 3, "cssOrderAvailable": true, "frameworkManaged": null}
```

The single-target form (selected, applied, inspect-result) adds `"siblings": [...]` and `"containers": [{"key": "arr.plain", "name": "div.plain"}, ...]` as in the example above.

Sibling-only target (any manifest):

```json
{"id": "auto:ul:generic:12", "role": "generic", "name": "GENERIC (UL)", "kind": "text", "tag": "ul", "stable": false,
 "arrangementOnly": true, "…": "rest as before"}
```

New guard rejection:

```json
{"type": "design:rejected", "reason": "unsupported-value", "targetId": "arr.p.1",
 "detail": {"property": "move", "requested": {"container": "arr.para"}, "guard": "content-model", "overridable": false,
            "message": "A <p> cannot be placed inside a <p>; the browser would repair the markup differently."}}
```

Everything else in the first-round shapes is unchanged.

### Deviations and notes

- I kept the unreachable `getRootNode` label/aria branch untouched, as instructed, and did nothing for M4 beyond the content-model guard (no `li`/`tr`/`option` rules).
- Deviation 1 of the first round is now Addendum 3 (bulk `siblings` and `containers`). The "hover and click" open concern is addressed by `arrangementOnly`. The 88 KB demo `design:ready` shrinks accordingly.
- M3 backoff slows rather than halts a hostile loop. With no breaker, a page that mutates on every bridge write still costs one discovery every 8 s.
- Existing tests changed in this round: the arrangement manifest tests read `containers` from a selected manifest, because bulk manifests no longer carry them.

## Changes after second review (re-review I2, plan Addendum 3 amendment, M1 over-reach)

Base: the Addendum 3 amendment (bulk manifests omit `containers` and `siblings`), Task E still uncommitted. Own files only, no commits.

Command (from `tests/`): `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server`
Result: `Ran 101 tests in 92.232s — OK` (83 bridge, 18 server). `node --check fontkit-bridge.js` passes. The hit-test and arrangement classes were run again with no flake. Firefox is not installed.

### RED (before any bridge change; 6 of 14 selected tests failed)

| Item | Test | RED failure |
|---|---|---|
| I2 | `SiblingOnlyHitTestTests.test_the_flag_and_the_hit_test_survive_rediscovery_moves_and_reconnects` (demo: hello, second hello, appended node, `design:move`; re-check the flag count, the `li` hit-test and the `summary` toggle each time) | `AssertionError: 0 != 12 : after a second hello` |
| Bulk | `ArrangementManifestTests.test_twenty_sections_of_a_hundred_targets_stay_near_linear` | `7221.96 not less than 1500 : {10: 7201748, 20: 14588368}` |
| Bulk | `test_bulk_manifests_never_carry_siblings_or_containers`, `test_manifest_arrangement_describes_…`, `HandshakeTests…` | `'siblings' unexpectedly found in {…}` |
| M1 | `LedgerHtmlAttributeScopeTests.test_only_real_data_urls_in_url_attributes_are_abbreviated` | `title="data: hello this is just a long title …"` came back as `title="data:…(532 bytes)"`, and the two-candidate `srcset` collapsed to one |

### Changes

1. **I2.** In discovery, a known sibling-only record loses `arrangementOnly` only when the element has an author-supplied `data-design-role` (the bridge-written one no longer counts) or is semantic by the bridge's own rule. After a second hello, a mutation, and a `design:move`, the demo still has the same 12 flagged records, clicking a `.plan ul li` selects nothing, and the FAQ `summary` toggles in Select mode.
2. **Bulk manifests (Addendum 3 amendment).** `design:ready` and `design:targets` carry no `arrangement.siblings` and no `arrangement.containers`; the 100-sibling cap logic is gone. They keep `containerKey`, `containerName`, `containerSelector`, `index`, `count`, `cssOrderAvailable` and `frameworkManaged`. I kept `containerSelector` (a short string, not in your list of kept fields; say if Studio wants it dropped). Selected, applied and inspect-result manifests are unchanged and carry the full `siblings` and `containers`. Parent-level container key, name and selector are cached per parent while building a bulk list. Measured on 10 and 20 sections of 100 target children (1020 and 2020 targets): `design:ready` is 793 KB and 1.58 MB, about 780 bytes per target and a ratio of 1.99, against 7.2 MB and 14.6 MB before.
3. **M1 scope.** Abbreviation now applies only to real data URLs: the whole value of `src`, `href`, `poster`, `action`, `data` and `xlink:href`; each `srcset` candidate separately (`data:…(N bytes) 1x, data:…(M bytes) 2x`); and `url(data:…)` inside `style`. Text attributes (`title`, `data-*`, and so on) are never touched. Tests cover both the abbreviated and the untouched cases.

### Not done

- The optional hard breaker (stop mutation-triggered rediscovery until the next hello after N backoff cycles) is not implemented. Reaching a sensible trip point takes about 5 s of storm, and a legitimate page with a sustained burst of added elements (a ticker) could trip it and leave later targets undiscovered until a Studio reconnect. The exponential backoff from round 1 stays as the only protection.
