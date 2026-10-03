# v0.2.0 Task B report: bridge runtime protocol hardening and change ledger

Branch: the v0.2 PR branch, starting from the plan and shared-harness change. Task A, the `support.py` fix and a plan addendum were committed while this task was in progress. No commits, pushes or branches were made by this task.

## Files changed (owned files only)

| File | Change |
|---|---|
| `fontkit-bridge.js` | Rewritten against the Protocol contract. The legacy slot, layout and asset helpers are kept, now routed through recording setters. |
| `tests/test_bridge_runtime.py` | New: 24 tests in 7 classes. |
| `tests/fixtures/bridge/host.html` | New. Studio-side host with these helpers on `window`: `send`, `hello`, `request`, `control`, `waitFor`, `messages`, `addEvil` and the `log` array. |
| `tests/fixtures/bridge/target.html` | New. Target page with author targets, auto targets, a mixed-content paragraph, an SVG, an id containing quote and backslash, a spacer and a footer. It loads the real `/fontkit-bridge.js`. |
| `tests/fixtures/bridge/target-restricted.html` | New. Bridge script tag with `data-allowed-origins="http://studio.test http://localhost:4173"`. |
| `tests/fixtures/bridge/target-overlay.html` | New. Opts out of auto-init and constructs the bridge with `enableHighlightOverlay: true`. |
| `tests/fixtures/bridge/evil.html` | New. Hostile sibling frame used for spoofing. |
| `docs/implementation/tasks/v02-task-b-report.md` | This report. |

Test origins, served by `route_virtual_origins`:
- `http://studio.test` and `http://evil.test` serve `tests/fixtures/bridge`.
- `http://target.test` serves the repo root.

That gives real cross-origin `postMessage`. The hostile cases use two setups:
- a sibling iframe at `evil.test` inside the Studio host;
- the host page itself served from `evil.test` and framing the restricted target.

## RED evidence (original bridge, unchanged)

Command (from `tests/`):
`FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime -v`

Before the RED run I checked `git diff --quiet -- fontkit-bridge.js`: the bridge was unchanged. Result: `Ran 23 tests … FAILED (failures=15, errors=8)`. The overlay test was added after GREEN (see below).

Key failures for the four confirmed defects:

1. **restore-text crash.** `test_restore_text_restores_original_text_without_throwing` failed with `AssertionError: Lists differ: ['Uncaught TypeError: this.handleRestoreText is not a function'] != []`. That error was captured inside the target frame.
2. **initialText re-capture.**
   - `test_original_text_is_captured_once_across_rediscovery` failed with `AssertionError: unexpectedly None`. The old bridge has no ledger, and its `text: null` does nothing.
   - Since that failure also reflects missing features, I ran a direct probe of the old internals (scratch script, not a test). Output:
     - after hello: `'Make type sing'`
     - after text edit: `'Edited'`
     - after rediscovery hello: `'Edited'`
   - So the original is lost straight after the first edit: the edit itself triggers the MutationObserver, which calls `registerElementTarget` again.
3. **Standalone click interception.** `test_clicks_are_not_intercepted_before_hello` failed with `AssertionError: '' != '#clicked'`. The link click was prevented with no Studio connected.
4. **No origin/session gating.**
   - `test_sibling_frame_cannot_open_or_hijack_the_session`: the evil frame received `design:ready`.
   - `test_wrong_session_or_protocol_version_is_ignored`: an update with the wrong session id was applied.
   - `test_allowed_origins_attribute_restricts_who_can_say_hello`: `'design:ready' != 'timeout'`.

The other contract tests failed on missing behaviour, for example:
- `bridge-ready` leaks `sessionId`;
- no `canonicalPatch` weight snapping (`{} != {'fontWeight': 600}`);
- revision starts at 3 after hello and update;
- a `KeyError` on `changes`, `reason` or `targets`;
- mixed-content text destroys `<strong>`;
- `null` does not restore the inline colour.

Harness note: the first RED attempt errored in every test with `TypeError: unsupported operand type(s) for /: 'Request' and 'str'`.
- Cause: in the shared `tests/support.py`, the route handler was declared as `handler(route, root=root)`, and Playwright passes `(route, request)` to two-parameter handlers.
- It was worked around temporarily with a local adapter; the shared `support.py` was then fixed and the adapter removed.
- The final tests call `route_virtual_origins(context, …)` directly.

## GREEN evidence

Command (from `/home/user/font-kit-studio/tests`):
`FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime -v`

Result: `Ran 24 tests in 17.9s — OK`. I also ran it 3 more times, all OK, with no flakes observed.

Tests by class:
- **ConfirmedDefectTests** (6): restore-text, original text captured once, no interception before hello, sibling-frame spoofing, wrong session or protocolVersion, allowedOrigins.
- **HandshakeTests** (1): `bridge-ready` carries no page data; full `design:ready` shape; manifest fields, constraints and editable flags; every selector resolves to exactly its own element; replies come from the target origin.
- **TargetedUpdateTests** (8):
  - canonicalization and `!important` application;
  - nearest declared weight (550→600, 500→400, 900→800, 401→400);
  - all 27 rejection cases plus revision-conflict, invalid-message variants, and a missing requestId (reply carries `requestId: null`);
  - atomicity;
  - exact revision increments;
  - `null` restores the original inline value (and removes a style attribute that wasn't there before);
  - leaf and mixed-content text, with restore-text keeping styles;
  - reset of one target, of everything, and of an unknown target.
- **SelectionTests** (5): hover (sent once per target, `null` off-target); click-select with no navigation; interact mode; `design:select` scrolls into view; `null` and unknown ids; `design:highlight` treated as select; bounds on scroll and resize; one `design:targets` per burst and none for irrelevant mutations.
- **OverlayOptionTests** (1): `enableHighlightOverlay: true` draws the hover and selection overlays. They are never discovered as targets, never cause a `design:targets` message, and never appear in ledger html.
- **ChangeLedgerTests** (2): order by first change; author and auto selectors; declarations without `!important`; `text` only when changed; cleaned html (author style text restored exactly, auto attributes and overrides stripped, including inside a container target); ledger included in `design:ready`.
- **LegacyCompositionTests** (1):
  - composition `design:update` (tokens, slots, layout) applies and records declarations, text and tokens;
  - `textTouched:false` text is ignored;
  - wireframe `transition`/`order` styles are kept out of the ledger;
  - `fontkit:change` is acknowledged with the ledger;
  - reset-all undoes all of it.

Other checks:
- `node --check fontkit-bridge.js`: OK.
- `node -e "require('./fontkit-bridge.js')"` exports `FontKitBridge`, `initFontKitBridge` and `PATCH_RULES`.
- `python3 -m unittest test_preview_server` (Task A): 18 OK.
- A smoke probe against `demo/index.html` passed:
  - 34 targets, all 12 author ids present;
  - tokens reported;
  - the badge weight 550 became 600;
  - the ledger html for the title was cleaned;
  - all selectors resolve uniquely;
  - no errors.
- I did not run Firefox; it isn't installed here (D010).

## Contract interpretation notes (please review)

Wherever the contract was silent or ambiguous, I picked the most literal reading.

1. **Revision.** Starts at `0`. `design:hello` does not change it. Overrides and revision persist across sessions (a re-hello shows the existing ledger in `design:ready`).
2. **Protocol version.** Every incoming `design:*` and `fontkit:*` message must carry `protocolVersion: 1`, or it is silently ignored. This includes legacy `fontkit:change` and `design:highlight`. The prototype Studio's `design:restore-text` (sent without `sessionId`/`protocolVersion`) is therefore ignored until Task C's client sends both.
3. **Pinning.** Once pinned, a hello is accepted only from the same window and the same origin; it replaces the session. A hello from another window, even another allowed one, is ignored until the page reloads.
   - Each hello resets the mode to `select` and clears the selection.
   - An empty `allowedOrigins` denies everyone, with a console warning. `'*'` means unrestricted.
4. **Rejection precedence:** `invalid-message` → `revision-conflict` → `unknown-target` → `unsupported-property`, with every key checked before any value → `unsupported-value`.
   - `invalid-message` covers: non-string or empty `requestId` (any string or number is echoed back), non-integer `baseRevision`, bad `targetId`, and a non-object `patch`.
5. **Empty targeted patch `{}`** is accepted as a successful no-op and increments the revision.
6. **Legacy composition update.** `requestId` is required. `baseRevision` is optional, but if present it must match.
   - `restore-text`: both `requestId` and `baseRevision` are optional, checked only if present; the reply carries `requestId: null` if none was sent.
   - Restore-text and reset reply with `canonicalPatch: {}`.
7. **Editable flags gate keys.** Using a key on a target whose `editable` flag is false gives `unsupported-property` (detail `property`). This applies even to `null`.
   - `kind: "image"` only for `img`, `svg`, `picture`, `canvas` and `video`, or an explicit `data-design-kind`. The prototype's id-substring heuristic (`id.includes('mark')`) is dropped: it classified `landing.brand.wordmark` as an image.
   - Image targets: only `svg` gets `color`. Text kind: `text` is editable only for a leaf or an element with a direct non-empty text node, so children are never destroyed.
8. **Stricter validation.** Besides the contract's character rules, `color` and `fontFamily` must pass `CSS.supports`. For example `rgb()` or a font name like `123abc` is rejected rather than accepted but not applied.
9. **Weight ties** resolve to the lower allowed weight (500 between 400 and 600 → 400).
10. **Text.**
    - A mixed-content edit replaces the first non-empty direct text node and keeps that node's leading and trailing whitespace.
    - Ledger `text` and `originalText` are trimmed. Manifest `text` is whitespace-collapsed, trimmed and capped at 200 characters.
    - `text` is non-null only if the trimmed current text differs from the original. Setting the original text back drops the entry.
11. **Originals.**
    - Captured once per element (WeakMap) right before the bridge first touches it. For style, that is a snapshot of all inline properties plus the raw attribute text. For text, it is the leaf's original child nodes, or the chosen text node and its data.
    - Restore puts the original nodes back, so it is exact.
    - When the inline style returns to its snapshot, the author's exact attribute text is put back, or the attribute is removed if there was none.
12. **Selectors for auto targets.**
    - `#id`, or a path of at most 4 entries. The id anchor counts as one entry. The path stops before `body`.
    - Each step includes all classes and always includes `:nth-of-type(n)`.
13. **`design:select` with an unknown id** clears the selection and replies `design:selected {targetId: null}`.
    - The off-screen test for `scrollIntoView({block:"nearest"})` is "not fully inside the viewport".
    - Bounds keep being reported in interact mode; only hover and select messages stop.
    - Switching to interact sends a final `hover {targetId:null}` first, if a hover was active.
14. **`design:targets`.**
    - Carries the full current manifest list.
    - Sent whenever the set of target ids changes (additions or removals) after a trailing 120 ms debounce, which is ≥100 ms. There is a 1 s maximum wait so continuous mutations can't starve it.
    - Discovery itself only runs at hello, on that debounce, or on an exact-id miss.
15. **Before hello the bridge is fully passive.** It does no discovery and adds no DOM attributes or observers; it only sends `bridge-ready`. Auto `data-design-id`, `data-design-role` and `data-design-name` are added at the first hello, tracked as bridge-owned and stripped from ledger html.
16. **Legacy wireframe styles.** `transition`/`order` from layout and the asset container's `display`/`align` go through the recording setter as bridge-owned but **not** as ledger declarations. Reset restores them and html cleaning strips them. Slot typography, spacer and rule styles **are** ledger declarations. Legacy slot ids are no longer registered as targets.
17. **Legacy messages.**
    - `fontkit:change` increments the revision and replies `fontkit:ack {revision, changes}`.
    - The `design:select-slot` message is no longer sent; `design:selected` replaces it.
    - `design:inspect-result` now carries `rect` and `target` (manifest) instead of `bounds` and partial `computed`. No caller exists in the repo.
18. **Duplicate author ids.** The first in document order wins and the bridge warns once (Spec §4.1). Disconnected targets are pruned at discovery.

## Deviations

None from the contract on purpose. Items 8 and 16 are stricter than, or add to, the contract text; they are listed for the reviewer.

Implementation note: Chromium's lazy CSSOM → attribute sync re-created `style=""` after `removeAttribute('style')`. This was found by `test_reset_one_target_or_everything`. The fix reads the attribute once before removing or restoring it (commented in `restoreStyleAttribute`).

## Open concerns

- **The legacy layout path reorders the DOM.** The prototype's `applyWireframeMovement` (`main` children are physically re-appended) is kept as instructed. Reset restores its inline styles but not the DOM order. This is relevant to Task E's move/structure work.
- **SPA re-renders.** If an author target's element is replaced, its overrides stay on the detached node and drop out of the ledger. They are not re-applied to the new element. That is Task E scope (SPA/HMR robustness).
- **Plan addendum.** The addendum committed during this task (arrangement, `design:move`, `overlay` mode, `fontStylesheet`) is wave-2 Task E and was not implemented here.
- **Firefox** was not run (D010).
- **Task C must send** `protocolVersion: 1` and `sessionId` on every control message, including restore-text, highlight and the legacy composition sync. Otherwise the bridge ignores them silently, by design (Spec §15).

## Changes after first review (review: `v02-task-b-review.md`, verdict "Changes required")

Base: the plan and Task A/G changes, Task B still uncommitted. Same rules as before: owned files only, no commits.

### Files changed in this round
- `fontkit-bridge.js`: the fixes below and the new header section on initialisation.
- `tests/test_bridge_runtime.py`: 9 new tests in the new classes `InitOptionTests`, `SessionLifecycleTests` and `AssetPlacementTests`, plus additions to `HandshakeTests` and `LegacyCompositionTests`.
- `tests/fixtures/bridge/`:
  - New pages: `target-manual.html` (`data-auto-init="false"` plus `initFontKitBridge({allowedOrigins})`), `target-options.html` (`window.FONTKIT_BRIDGE_OPTIONS`), `target-constructed.html` (`new FontKitBridge({allowedOrigins})` after the script tag).
  - `target.html`: new `landing.photo` (`<img>`, PNG data URL) and `landing.slot` (empty container) targets.
  - `host.html`: `openPopup` and `popupHello` helpers.
  - `target-overlay.html`: now uses `data-auto-init="false"` instead of the `__fontkitBridge = 'manual'` hack.

### RED (before any bridge change)
Command (from `tests/`):
`FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime.InitOptionTests test_bridge_runtime.SessionLifecycleTests test_bridge_runtime.AssetPlacementTests test_bridge_runtime.HandshakeTests test_bridge_runtime.LegacyCompositionTests test_bridge_runtime.OverlayOptionTests`

Result: `Ran 12 tests … FAILED (failures=9)`.

| Review item | Test | RED failure |
|---|---|---|
| Critical 1 | `test_svg_payloads_never_execute_in_the_target` | `AssertionError: 'foreign' is not None`: the payload scripts ran in the target origin. |
| Important 3 | `test_base64_svg_from_read_as_data_url_replaces_an_inline_svg_until_reset` | `('flex', 1, 'p', False, None) != ('none', 0, 'img', True, 'data:image/svg+xml;base64,…')`. The `<img>` was appended inside the `<svg>`, and the svg was forced to `display:flex`. |
| Minor 9 | `test_only_png_and_svg_data_urls_are_placed` | The `<img>` src became `'DATA:image/png;base64,not base64!'`: arbitrary URLs were accepted. |
| Important 2, option path | `test_global_options_are_used_by_auto_init` | `'design:ready' != 'timeout'`: `evil.test` connected. |
| Important 2, constructor path | `test_constructed_instance_claims_the_global_slot` | `'design:ready' != 'timeout'`: `evil.test` connected through the auto instance. |
| Important 2, second init | `test_auto_init_opt_out_with_manual_init` | `0 != 1` warnings: a second `initFontKitBridge(options)` silently ignored its options. |
| Minor 4 | `test_legacy_tokens_accept_only_safe_names_and_values` | `--evil: url(https://evil.test/beacon)`, `--Upper`, `--semi`, … were all accepted. |
| Minor 5 | `test_closed_opener_studio_stops_click_interception` | `'' != '#clicked'`: clicks were still intercepted after the opener Studio closed. |
| Minor 6 | `test_first_hello_discovers_targets_once` | `2 != 1` discovery passes on the first hello. |

Note on the manual-init RED: with the script at the end of `<body>`, the manual `initFontKitBridge({allowedOrigins})` already ran before the deferred auto-init. So the evil-origin assertion in that test passed even before the fix; only the warning assertion failed. The constructor and `FONTKIT_BRIDGE_OPTIONS` paths were genuinely open.

### Fixes
- **Critical 1, Important 3, Minor 9 (assets).**
  - Removed the DOMParser/importNode/replaceWith path. No HTML-parsing sink remains in the file (grep for `DOMParser|importNode|replaceWith|innerHTML|insertAdjacentHTML` finds nothing).
  - `safeAssetUrl()` accepts only these URLs; anything else (http(s), `javascript:`, other `data:` types, malformed base64) is ignored:
    - `data:image/png;base64,<base64>`;
    - `data:image/svg+xml[;charset=…][;base64],…`, with base64 checked when declared.
  - Every placement renders through an `<img class="fontkit-placed-asset">`:
    - An `<img>` target gets a recorded `src` swap; `srcset` is removed if present.
    - An inline `<svg>` target is hidden (`display:none`, bridge-owned, not a ledger declaration), with an `<img>` sibling inserted after it.
    - A container gets an `<img>` child.
  - Placed images are excluded from discovery.
  - Reset (one target or all) removes them and restores the `src`/`srcset` attributes, styles and placeholder text. Originals are captured once per element.
- **Important 2 (init options).**
  - The script tag can opt out with `data-auto-init="false"`.
  - Auto-init reads `window.FONTKIT_BRIDGE_OPTIONS` when it runs.
  - The constructor claims `window.__fontkitBridge` if it is empty, and warns if another instance already exists.
  - `initFontKitBridge(options)` with options that differ from the existing instance's own (by reference) warns and returns the existing instance. Calling it with no options does not warn.
  - All of this is documented in the file header.
- **Minor 4 (legacy tokens).**
  - Names must match `--[a-z0-9-]+`.
  - Values go through `safeCssString()`: trimmed, 1–300 characters, and none of `; { } < > \`, `url(` or `expression(`. `fontFamily` now uses the same helper.
  - This applies to composition `tokens`, the `sans`/`serif`/`mono`/`display` shortcuts and `fontkit:change`.
- **Minor 5 (closed opener).** `studioAlive()` checks `studioSource.closed` on each click, pointer move, post and hello. If the Studio window is closed, the session is dropped (unpinned, mode reset, selection cleared), so clicks are no longer intercepted and a new Studio can say hello.
- **Minor 6 (double discovery).** The first hello discovers once, via `activate()`; later hellos rediscover once.

### GREEN
- `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime`: `Ran 33 tests … OK`. Run 3 times, all OK.
- `… python3 -m unittest test_bridge_runtime test_preview_server`: `Ran 51 tests … OK`.
- `node --check fontkit-bridge.js`: OK. CommonJS `require` still exports `FontKitBridge`, `initFontKitBridge` and `PATCH_RULES`.
- The demo smoke probe (real bridge on `demo/index.html`) passes: selectors unique, no errors.

### Deferred (as instructed) and remaining notes
- **Minor 7, legacy layout reorder:** not undone by reset. Left for Task E's move/structure work. Studio should not claim reset fully reverts an explicit composition sync.
- **Minor 8, auto-selector uniqueness:** an unanchored path can still be ambiguous on deep DOMs (no uniqueness check yet). Left for Task E.
- **Asset ledger visibility.** An `<img>` target's asset width and opacity appear as ledger declarations. A placed `<img>` beside a hidden inline `<svg>` is bridge-owned and does not appear in the svg's ledger `html`. Placed assets are legacy composition behaviour, outside the targeted-patch contract.
- **Contract note received:** ledger `text` stays trimmed; Studio trims before comparing.
