# v0.2.0 Task C report: Studio protocol client, Live Target inspector, overlay, code panel

- Branch: the v0.2 PR branch, starting from the plan and shared-harness change; Task A was committed mid-task. Nothing was committed by this task.

## Files changed (owned files only)

| File | Change |
|---|---|
| `font_kit_studio_v0.1.1.html` | Replaced the bridge runtime with a contract-conformant protocol client. Added the live UI (badge states, hint, Select/Interact, overlay, reconnect banner, code panel), the Live Target inspector and the optional `live` export/import. |
| `tests/test_studio_live.py` | New. 18 tests in 3 classes (defects, protocol, persistence). |
| `tests/fixtures/studio/fake-target.html` | New. Deterministic fake that implements the bridge side of the contract. |
| `tests/fixtures/studio/no-bridge.html` | New. Target page with no bridge, used for the "No bridge detected" test. |
| `tests/fixtures/studio/spoofer.html` | New. Foreign-origin frame (`http://evil.test`) that posts forged protocol messages. |
| `tests/fixtures/studio/host.html` | New. Page that embeds Studio and records anything Studio posts to its parent. |
| `docs/implementation/tasks/v02-task-c-report.md` | This report. |

No changes to `tests/support.py`, `tests/test_font_kit_studio_v011.py`, `fontkit-bridge.js`, `demo/` or `scripts/`.

## Test harness

- Origins are set up with `route_virtual_origins`:
  - `http://studio.test` serves the repo root.
  - `http://target.test`, `http://evil.test` and `http://host.test` serve `tests/fixtures/studio`.
  - So every `postMessage` crosses a real origin boundary.
- The sync endpoints are Playwright context routes for `http://studio.test/__fontkit/**`. They are registered **after** the file routes because Playwright runs the most recently registered matching route first. They record each PUT body and its `Content-Type`.
- **Shared-harness defect (resolved).** Under Playwright 1.62, `support.route_virtual_origins` originally bound `root` to the `Request` (`handler(route, root=root)`), so every request failed. During the first pass my test file used a local `_SingleArgRoutes` adapter. `support.py` has since been fixed (it now builds handlers through a factory), and changes after first review removed the adapter (M1). The helper is now used directly.

## RED evidence (baseline Studio, before any HTML change)

Command:

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live -v
```

Result: `Ran 18 tests … FAILED (failures=4, errors=14)`. The three defect tests fail for the defect itself:

- `test_spoofed_messages_from_foreign_window_or_session_are_ignored`
  - Fails with `AssertionError: 'Live Synced (rev 99)' != 'Connected (5 targets)'`.
  - Baseline Studio accepted a forged `design:applied` from a foreign-origin frame and from its own window.
- `test_connect_does_not_broadcast_composition_or_restyle_target`
  - Fails with `AssertionError: Lists differ: [{'type': 'design:update', 'requestId': 'r[8965 chars]…] != []`.
  - The fake target received composition `design:update` messages on connect, view switches and Specimen edits, without any explicit sync.
- `test_send_path_has_single_anti_recursion_guard_and_never_posts_to_parent`
  - Fails with `AssertionError: 2 != 1`: there are two copies of the `window.self !== window.top` guard, one of them inside `sendDesignMessage`.
  - The same test also checks behaviour: an embedding host must receive nothing from Studio. Baseline posts every design message, plus a boot-time `design:hello`, to `window.parent`/`window.opener` with `"*"` (Spec §15).

The other 15 tests are contract tests for features that were missing. They failed with timeouts waiting for the new badge texts or IDs, or with `'Ready' != 'Idle'`. No RED was manufactured: those failures are absent features, not the defects.

Behaviours that baseline did not have at all, so they had no RED to show:

- Spoofed `design:selected`: baseline did not handle that message type.
- Legacy `design:select-slot` mutating slot role, text and size: covered in GREEN by `test_live_inspector_seeds_from_computed_and_respects_editable`. That test sends `design:select-slot` from the genuine target with the right session and asserts the composition export is unchanged. Baseline would have failed it, but the test errored earlier, while waiting for the connection badge.

## GREEN evidence

The commands below were run after implementation:

```
cd /home/user/font-kit-studio/tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -v
→ Ran 38 tests in 68.897s — OK   (18 new + 20 existing)

FKS_ENGINES=chromium … python3 -m unittest test_studio_live   (×3 consecutive runs)
→ OK, OK, OK

cd /home/user/font-kit-studio && python3 scripts/verify.py --static-only
→ PASS HTML IDs: 74 unique static IDs; PASS JavaScript syntax: 1 executable inline blocks;
  SHA-256 font_kit_studio_v0.1.1.html: 5ff9a69f8266623bca405c536eb7fb4bff5cd49543789a26a0c022749588aa15; provenance PASS ×3

git diff --check → clean
```

One regression turned up during GREEN and was fixed:

- **Symptom:** after selecting a different target, a `change` event from the previous inspector's colour field (still focused while being removed) patched the newly selected target.
- **Fix:** controls are now bound to the target id they were rendered for, and events from stale controls are dropped.
- **Evidence:** this was a real failure in `test_code_panel_css_html_json_copy_and_download`, where `#features` unexpectedly received `color: #ff0000`.

Firefox was not run because it is not installed here (D010).

## What was implemented (plan Task C checklist)

1. **Protocol client**
   - Origin and session: `expectedOrigin = new URL(url, location.href).origin`. A message is accepted only when all of these hold: `event.source === iframe.contentWindow`, `event.origin === expectedOrigin`, `protocolVersion === 1`, the type is a known bridge→Studio type, and `sessionId` matches (except `design:bridge-ready`).
   - Sending: Studio posts only to the iframe, with `targetOrigin = expectedOrigin` (`"*"` only for `"null"`). Every message is stamped with `protocolVersion: 1` and `sessionId`.
   - Session ids: a fresh `fks-<16 hex>` id for every handshake, generated with `crypto.getRandomValues`.
   - Request queue: one request in flight. Pending updates for the same target are merged; merging stops at a queued reset or restore. Composition updates are coalesced to the latest snapshot.
   - Revisions: `baseRevision` comes from the last `ready`/`applied`/`rejected` revision. A `revision-conflict` is retried exactly once, with a new `requestId`.
   - Rejection: the badge shows `Rejected: <reason>` and the inspector controls are reseeded from the target's manifest. Keys still pending are not overwritten.
   - Replies are matched by `requestId`. An 8 s timeout releases a stuck request.
2. **No broadcast on connect.**
   - `⚡ Sync to Live App` is the explicit composition sync and is session-gated.
   - After it is pressed, Specimen edits stream as composition updates until the next handshake. Each new session clears that link.
   - The misplaced guard block is removed from `sendDesignMessage`. Exactly one anti-recursion guard remains, at the end of the IIFE.
   - Studio no longer posts to `window.parent` or `window.opener`, and no longer sends the boot-time `design:hello` to its parent.
3. **Status badge.** States: `Idle`, `Connecting…`, `Bridge detected`, `Connected (N targets)`, `Live · rev N`, `Rejected: <reason>`, and `No bridge detected` after 4 s.
   - The last state also shows `#bridgeHint`, which explains how to add the script tag.
   - Other states: `No response from target`, `Invalid target URL`, `Recursion blocked`. The badge's `data-state` attribute drives its colour.
4. **`?target=`** prefills `#targetAppUrl`, opens Composer → Target App and connects. It is skipped when Studio is embedded.
5. **Select/Interact** via `#bridgeModeSelect` and `#bridgeModeInteract`, which use `.segmented` and `aria-pressed`.
   - Each toggle sends `design:mode`, and the mode is re-sent after `design:ready` if it is not `select`.
   - The hover overlay is suppressed in Interact mode.
6. **Studio-owned overlay.**
   - Placement: `#bridgeOverlayHover` and `#bridgeOverlaySelected`, each with a name label, live in a `pointer-events: none` layer inside `#targetAppContainer` (now `position: relative`). Rects are placed in target-viewport coordinates over the iframe.
   - Updates and visibility: the selected overlay follows `design:bounds`. Both overlays are hidden in Specimen view, before ready, and for invalid rects. The tests confirm nothing is injected into the target DOM.
7. **Live Target inspector** in `#slotInspector`, only while Target App view is active (a one-line guard at the top of `renderInspector`).
   - Without a selection, it shows a target list that sends `design:select`. Before ready, it shows a waiting or instruction message.
   - With a selection, it shows the target name (`#liveTargetName`), the id, and a note when the target is auto-discovered.
   - Controls are rendered only for capabilities in `editable`:
     - Typography: `#liveFontFamily` (current computed family plus every Studio library family as `cssStack`), `#liveFontSize`, `#liveFontWeight` with `#liveWeightNote` listing `constraints.fontWeights`, `#liveLineHeight`, `#liveLetterSpacing` (em), `#liveTextTransform`.
     - Alignment: `#liveTextAlign`.
     - Colour: `#liveColorHex` plus `#liveColor`.
     - Text: `#liveText`, only when `editable.text` is set and `kind` is `"text"`.
   - Also present: `#liveResetTarget` and an "All targets" back button.
   - Seeding from `computed`: px values become a line-height ratio or letter-spacing in em, and `rgb()`/`rgba()` become hex. Canonical values returned in `design:applied` are written back into the controls (for example, weight 550 is shown as 600).
   - Specimen view and the slot inspector are unchanged.
8. **Code panel `#liveCodePanel`** (Target App view only). It has tabs `#codeTabCss`, `#codeTabHtml` and `#codeTabJson`, output in `#liveCodeOutput` (a `<pre>`), and `#liveChangeCount`.
   - **CSS** is generated from the target's ChangeLedger, i.e. acknowledged state only. It contains a header comment, a `:root` block of tokens, and one rule per changed target headed `/* name (id) */`. Auto selectors carry the comment "— auto-discovered — add data-design-id for a stable selector". Every declaration gets `!important`. There are no timestamps.
     - Unsafe selectors or values (containing `{};<>`, comment markers, newlines or `!important`) are dropped.
   - **HTML** contains the cleaned `html` snippets of targets whose text changed, or `<!-- No text changes yet. -->`.
   - **JSON** is `{"target","revision","overrides"}`.
   - Actions:
     - **Copy** uses the Clipboard API, falling back to `execCommand`.
     - **Download** saves `fontkit-overrides.css`, `fontkit-changes.html` or `fontkit-overrides.json`.
     - **Sync:**
       - Under `file://` Studio does not call the status endpoint; Sync and Auto-sync are disabled with an explanatory title.
       - Otherwise Studio calls `GET /__fontkit/status` on its own origin and enables sync only when it returns `sync: true`.
       - **Sync to file** sends `PUT /__fontkit/overrides.css` with `Content-Type: text/css`, as the server requires.
       - Auto-sync is debounced 400 ms and serialized with a busy flag plus a queued flag, so writes never overlap and the latest state wins. Status moves through `Sync pending…`, `Saving…`, `Saved N bytes to <path>.` or `Sync failed: …`.
     - When the status response includes `target` and no `?target=` was given, it prefills the URL field.
9. **JSON `live` field and reconnect banner.**
   - Export adds `live: {target, revision, overrides}` only when there are canonical overrides.
   - Import validates `live` with the same key rules before anything is published, so a bad `live` field fails the whole import transactionally. Target ids are stored with `defineProperty`, so a `"__proto__"` id is safe.
   - On `design:ready`, the target ledger is converted back to canonical overrides and compared with Studio's saved overrides. If Studio has none, it adopts the target's state silently. If they differ, `#liveReconnectBanner` appears and nothing is applied:
     - `#liveReapply` sends minimal per-target patches, using `null` for keys present only on the target.
     - `#liveAcceptTarget` adopts the target ledger.

## UI decisions

- Visual language: existing CSS variables, `.btn`, `.segmented`, `.inspector-field`, `.inspector-note`, `.row-child-jump` and `.color-grid`. New styles live in one block marked "v0.2.0 — Live preview". Dark mode works through the existing variables.
- The bridge badge's inline styles were replaced by a `.bridge-badge` class.
- The mode toggle sits in the bridge bar next to the Specimen/Target App toggle.
- The code panel sits under the iframe inside `.canvas-stage`; the reconnect banner sits above the iframe.
- At 390 px there is no document overflow. The bar wraps, the code `<pre>` scrolls internally, and the inspector stacks below the preview. The test checks `scrollWidth` and the right edges of the panel, inspector, toggle and Sync button.
- The default target URL changed from `http://localhost:8000/` to `http://localhost:8001/demo/` to match Task A's port layout (Studio 8000, target 8001). It is also overwritten by `status.target` when present.

## Contract interpretation notes (please review)

1. **Hello on iframe load** — superseded in changes after first review (I3). Studio now re-greets on *every* load, using the current session id, and arms the no-bridge timer; it never skips. `design:bridge-ready` still starts a fresh session. See "Changes after first review".
2. **Composition streaming after an explicit sync.**
   - The prototype streamed every Specimen edit to the target. I read "⚡ Sync … remains the explicit composition sync" literally: nothing is sent until the button is pressed.
   - After that, edits stream for the rest of the session, which keeps the prototype's live-typing feature. A new handshake (reload or reconnect) ends it, so Studio never silently re-styles a reconnected target.
3. **Studio never posts to `window.parent` or `window.opener`.**
   - The contract says Studio posts to the iframe at `expectedOrigin`. The old "post everywhere with `*`" behaviour and the boot-time parent hello were removed.
   - No documented feature relied on them; README integration B is target-side injection, not Studio as a child.
4. **`design:select-slot` is no longer handled.**
   - `design:selected` never changes composer slots.
   - `highlightSlotInTarget` is kept for the existing image-upload path, but it only selects when the id is a known live target. Composer slot UUIDs never are, so in practice it is a no-op.
5. **Reconnect banner also appears on import.**
   - Importing a valid `live` field while connected and ready compares it with the target immediately and can show the banner. The Spec only mentions `design:ready`; this extends the same rule.
6. **Persisted revision is the canonical revision, not the live session revision.**
   - Exported `live.revision` and `live.target` are the revision and target of the last acknowledged canonical overrides.
   - After an import, they are the imported values until the next applied change. Importing does not change the session's `baseRevision`.
7. **Legacy imports and `live`.** A document without `live` keeps the receiving session's live overrides, mirroring how a missing `kitIds` field is handled. A present but invalid `live` field rejects the whole import.
8. **(Superseded in changes after first review, I2: the CSS now comes from Studio's saved overrides; the original note follows.) The code panel's CSS and HTML come from the target ledger; JSON comes from Studio's canonical overrides.**
   - While a reconnect conflict is open, the two can differ until it is resolved.
   - Auto-sync is suppressed while a conflict is open, on `design:ready` and on Accept, so a reload with an empty ledger never auto-wipes the overrides file. A manual Sync is still allowed.
9. **Text seeding.**
   - `#liveText` is seeded from Studio's saved text override when there is one; otherwise from the manifest's `text`.
   - The manifest `text` is trimmed and capped at 200 characters, so very long text shows truncated until it is edited.
10. **Restore and reset refresh the inspector by re-selecting.** After `design:restore-text` or `design:reset` is applied, Studio sends `design:select` for the current selection. The bridge's `design:selected` reply refreshes the inspector, because those replies may not carry a `target` manifest.

## Deviations

- Tests run in Chromium only; Firefox is not installed (D010).
- `support.route_virtual_origins` is adapted locally (see Test harness); a fix in the shared helper is recommended.
- The clipboard test stubs `navigator.clipboard.writeText`, because `http://studio.test` is not a secure context. Granting permission fails with "Permissions can't be granted in current context". Task D plans a real clipboard check on localhost, which is a secure context.

## Open concerns

- **Typed but uncommitted colour hex can be lost.** If the user types a hex value and selects another element in the preview without leaving the field first, the `change` event fires on the stale control and is dropped. This is deliberate, since the alternative patches the wrong target. The Colour picker and every other control apply on `input` or `change` immediately.
- **Edits made during a reload are dropped.** A user action queued between a session's `design:ready` and a new handshake (for example during a reload) is discarded with the old session's queue.
- **The fake fixture only approximates the real bridge.** Task D must confirm against the real `fontkit-bridge.js` that:
  - `design:applied` for targeted updates includes `target` and `changes`;
  - `rect` is in viewport coordinates;
  - ledger `declarations` use the CSS forms in the contract (`56px`, `0.1em`).
- **Hover overlay labels can overlap a selected box above them.** This is cosmetic only.

## Changes after first review (review: `v02-task-c-review.md`, plus additional compatibility items)

- **Repo state:** the round started with the Task C HTML at SHA-256 `5ff9a69f…aa15`, unchanged since the first report. Docs commits landed on the branch during the round.
- **What was touched:** only owned files. Nothing was committed.

### Files changed in this round

- `font_kit_studio_v0.1.1.html`
- `tests/test_studio_live.py`: 9 new tests and 3 adjusted ones.
- `tests/fixtures/studio/fake-target.html`, which gained:
  - `rejectNext`, which forces one rejection;
  - `?late`, which announces `bridge-ready` 60 ms after `load`, matching the real bridge's order;
  - `reannounce()`, a bridge restart that keeps page state;
  - `emitTargets(ids)`, which posts a full `design:targets` list;
  - ledger text that is trimmed and omitted when it equals the original, like the real bridge.
- This report.

### RED evidence

All runs used `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest …`.

**Run 1: the review findings, against the pre-fix HTML.** Result: `Ran 24 tests … FAILED (failures=6, errors=1)`.

| Finding | Test | Failure |
|---|---|---|
| C1 | `test_c1_target_url_scheme_allow_list` | `AssertionError: 'http://studio.test' is not None`. The `?target=javascript:parent.__pwned=parent.location.origin;void 0` probe ran in Studio's origin. |
| I1 | `test_i1_keystroke_numeric_entry_applies_typed_values` | `AssertionError: '324' != '24'`. Typed with `page.keyboard.type('24', delay=120)` over a 32px value. |
| I2 | `test_i2_studio_overrides_are_persisted_and_accept_is_explicit` | The banner text did not say that Accept *replaces* Studio's saved overrides. |
| I3 / M2 | `test_i3_every_iframe_load_regreets_both_announce_orders` | The reloaded document received a hello with a new session instead of the current one. |
| M3 | `test_m3_late_applied_after_timeout_updates_canonical_state` | A late `design:applied` was ignored, so the badge never reached `Live · rev 1`. |
| I1 (adjusted) | `test_targeted_updates_canonical_values_and_rejection_reseed` | `'600' != '550'`: the focused field was overwritten. |
| I1 (adjusted) | `test_revision_conflict_is_retried_once` | `'50' != '60'`: the focused field was reseeded. |

**Run 2: the I3 navigation case, as a scratch probe** (`taskc-i3-probe.py`, pre-fix HTML).
- Normal order passed.
- `fake-target.html?late=1` failed: after two reloads and a navigation to `no-bridge.html`, `Page.wait_for_function` timed out waiting for `No bridge detected`.

**Run 3: addenda (a)–(c),** written after the round-1 fixes and before their own fixes. Result: `FAILED (failures=2, errors=1)`.

| Addendum | Failure |
|---|---|
| (a) | `'hero.title' unexpectedly found in {… 'hero.title': {'text': 'Hello world'}}`. Text typed back to the original was kept as an override. |
| (b) | A timeout: removed targets lingered, because `design:targets` was merged rather than replaced. |
| (c) | `({'color': 'rgb()'}, 'Composition imported. …')`. An invalid colour was accepted on import. |

**Characterization only.** `test_every_control_message_carries_protocol_version_and_session` passed before any fix, in line with a clean field check. It covers:
- `hello`, targeted `update`, the ⚡ composition `update`, `select`, `mode`, `reset`, and `restore-text` (with `requestId`, `baseRevision`, and its applied reply);
- `design:highlight` is no longer sent at all.

### Fixes

- **C1: target URL schemes.**
  - `safeTargetUrl()` accepts only `http:` and `https:`, plus `file:` when Studio itself runs from `file:`.
  - It is enforced in `connectTargetApp`, which serves the URL field, the Connect button, Enter and the Target App view.
  - It is also enforced for `?target=`. An invalid value opens Composer, shows `Invalid target URL`, and loads nothing.
  - `live.target` on import must be absolute and pass the same check, otherwise the whole import fails.
  - `status.target` is used to prefill the URL field only when it passes the check.
  - Tested probes:
    - via `?target=`: `javascript:`, `data:` and `file:`;
    - via the URL field (Connect and Enter): a same-origin `blob:` and `javascript:`;
    - via import: `javascript:`, `data:` and `blob:` as `live.target`;
    - via the dev-server status: a `javascript:` `status.target`.
- **I1: number fields.**
  - Every `input` event is validated locally with `canonicalLiveValue`. Values that fail are marked `aria-invalid` and are not sent, so partial keystrokes never become requests.
  - Focused controls are never overwritten, whether by a canonical reflection or by a rejection reseed.
  - On `blur`, each control shows the acknowledged value: Studio's saved overrides layered over the manifest, unless a conflict is open, plus anything pending.
  - The keystroke test covers size `24`, weight `300`, line-height `1.5` and letter-spacing `0.08`. It asserts that every value sent was within the contract's range.
- **I2: overrides persistence.**
  - The synced and downloaded CSS is now built from **Studio's saved canonical overrides**. Selector, name and stability for each target come from a `targetMeta` map filled from manifests and ledgers. With no metadata, the CSS falls back to `[data-design-id="…"]` and marks the selector as assumed.
  - The HTML tab stays ledger-based. Tokens still come from the ledger.
  - The banner now says that "Accept target state replaces Studio's N targets of saved overrides with the target's state, and the overrides file only changes when you sync".
  - Accept turns auto-sync off and reports: "Saved overrides replaced… The overrides file is unchanged until you press Sync to file".
  - The test walks the reported sequence:
    1. auto-sync at 70px, then reload;
    2. with the conflict still open, edit and manually Sync: the PUT keeps 70px and adds the new rule;
    3. Accept, then edit another element: no PUT is sent, and the last body still has 70px;
    4. press Sync explicitly: the PUT now lacks 70px. That is the deliberate, announced choice.
- **I3 / M2: iframe load.**
  - On every iframe `load` Studio:
    - sets `ready = false` and drops the in-flight request and the stale rects;
    - re-sends `design:hello` with the current `sessionId`, creating one only when none exists;
    - shows `Connecting…` and arms the no-bridge timer.
  - `design:bridge-ready` and `design:ready` clear the timer.
  - When the timer fires, it resets the session and the target list and shows `No bridge detected` with the hint.
  - The `bridgeReadySinceLoad` and `bridgeSeen` flags are gone.
  - Queued edits survive a re-hello, and a kept selection is re-selected after `ready` so its bounds return.
  - `design:ready` and `design:selected` reseed the inspector in place when it already shows that target, so a duplicate ready no longer rebuilds it or steals focus.
  - Tests cover both announce orders through two reloads each, then navigation to a page with no bridge.
- **M3: late replies.** A timed-out op is kept as `live.timedOut`. If its `design:applied` arrives later, Studio still records the canonical patch and ledger, raises the revision monotonically, and schedules auto-sync. The test waits for the real 8 s timeout.
- **M4: dead code.** `highlightSlotInTarget` and both call sites (`moveSlot`, image upload) are removed. Those paths still call the session-gated `broadcastLiveState`.
- **M1: test adapter.** `_SingleArgRoutes` is removed; the fixed `support.route_virtual_origins(context, …)` is used directly.
- **Addendum (a): text compared like the bridge ledger.**
  - Text is compared trimmed.
  - A saved text equal to the target's original text (taken from the ledger's `originalText`, otherwise the manifest `text`) counts as no override, both for conflict detection and for Reapply.
  - After an applied text change, Studio drops the text key when the ledger reports no text change.
  - The test checks trailing whitespace and text typed back to the original, then restarts the bridge (`reannounce`): no banner appears.
- **Addendum (b): `design:targets`.** It replaces the target list, clears a selection or hover on a removed target, and refreshes the inspector.
- **Addendum (c): CSS validity on import.** Imported `fontFamily` and `color` must also pass `CSS.supports` (`font-family`, `color`). `rgb()`, a 5-argument `hsl()` and `123` are rejected; valid values are accepted.
- **Addendum (d), optional and done:** composition updates from ⚡ also trigger auto-sync, because their tokens change the CSS. This is asserted at the end of the sync test.
- **Adjusted tests:**
  - **Handshake test:** in the *fake's* order (`bridge-ready` before `load`) there is now one session per connect. `bridge-ready` starts it and the load re-hello reuses it. With the real bridge's order the first connect mints two sessions (see changes after second review, m2). The test previously asserted one distinct session per hello.
  - **Rejection reseed:** this is now driven by `rejectNext`, because out-of-range values are no longer sent at all. Reseeding is asserted on blur.

### GREEN evidence

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -v
→ Ran 47 tests in 118.536s — OK   (27 Task C + 20 existing)
… -m unittest test_studio_live   (×2 more runs) → Ran 27 tests … OK, OK
cd .. && python3 scripts/verify.py --static-only
→ PASS HTML IDs: 74 unique static IDs; PASS JavaScript syntax: 1 executable inline blocks;
  SHA-256 font_kit_studio_v0.1.1.html: 6f1fe8c2d4f360fca2c14da82104929d3ac7643f3ee8a44472b83b51ccd9085a; provenance PASS ×3
git diff --check → clean
```

Firefox was not run (D010).

### Notes and remaining concerns

- **Two hellos per connect is intended.** Corrected in changes after second review (m2). Two hellos share one session only in the fake's order, where `bridge-ready` arrives before `load`. With the real bridge, `load` arrives first: the load handler mints session A, then `bridge-ready` starts session B. Replies tagged A are dropped, so this is harmless. Studio reseeds the inspector in place for any duplicate `design:ready`.
- **Late-order reloads still change sessions.** In the late order, a reload first re-greets with the old session; `bridge-ready` then starts a new one. That handshake clears the selection, which is expected under the contract.
- **Number inputs can momentarily show more than the target.** For example, typing `1000` into Size sends `100` at the third keystroke and then shows `1000` flagged invalid. Blur restores `100`.
- **Composition tokens are not in Studio's saved overrides.** Superseded by changes after second review (I4): tokens are now kept in memory as saved state. They are still not part of the `live` JSON.
- **The CSS can name a selector before the target has been seen.** For an imported override with no manifest yet, the selector is assumed to be `[data-design-id="id"]`, and the CSS says so in a comment.

## Changes after second review (re-review: "Re-review after first changes" in `v02-task-c-review.md`)

- **Repo state:** the round started with the Task C HTML at SHA-256 `6f1fe8c2…085a`, unchanged since round 1.
- **Read first:** `AGENTS.md` and `docs/agents/global-rules.md`. I4 is a Rule 6 violation, "never silently overwrite", which is anti-pattern 5.
- **What was touched:** only owned files. Nothing was committed.
- **Files changed:**
  - `font_kit_studio_v0.1.1.html`;
  - `tests/test_studio_live.py`: 2 new tests and 1 strengthened test;
  - this report.

### RED evidence (pre-fix HTML `6f1fe8c2…`)

Command:

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest \
  test_studio_live.StudioFixRound1Tests.test_i4_reload_that_loses_composition_tokens_raises_banner_not_a_smaller_file \
  test_studio_live.StudioFixRound1Tests.test_m3_late_reset_reply_reselects_like_the_normal_path \
  test_studio_live.StudioFixRound1Tests.test_i1_keystroke_numeric_entry_applies_typed_values -v
→ Ran 3 tests — FAILED (failures=3)
```

| Finding | Test | Failure |
|---|---|---|
| I4 | `test_i4_…` | `AssertionError: False is not true`: no reconnect banner after a reload that lost the tokens. |
| m3 | `test_m3_late_reset_…` | `AssertionError: 0 not greater than 0`: no `design:select` after a late reset reply. |
| m1 | `test_i1_…` (new assertion: no consecutive duplicate values) | `('lineHeight', [1, 1, 1.5])`. |

The I4 test follows the reviewer's sequence exactly:
1. Turn auto-sync on, then press ⚡ Sync: the PUT contains `:root` / `--font-display`.
2. Reload the target.
3. Set `hero.title` to 50px.

### Fixes

- **I4: composition tokens are saved state.**
  - `live.savedTokens` holds the last *acknowledged* composition tokens. It is set from the ledger after a composition `design:applied`, and cleared by an applied global reset.
  - The synced and downloaded CSS (`liveCss`) and the change count use these saved tokens, not the session ledger.
  - The reconnect comparison now includes tokens. A reload that loses them raises the banner, and auto-sync stays suppressed while the conflict is open.
  - **Reapply** also sends a tokens-only composition update (`patch: {tokens}`, no slots or layout).
  - **Accept target state** replaces Studio's saved tokens along with its overrides. The banner and the code status both say "overrides and composition tokens".
  - The test asserts:
    - every PUT after the reload still contains `--font-display`;
    - the CSS panel keeps the tokens and adds the 50px rule;
    - Reapply restores the tokens on the target, both in its ledger and in its computed `--font-display`, through a tokens-only patch.
  - **Scope:** tokens are kept in memory only. They are not part of the `live` JSON schema, so they do not survive a Studio page reload or a JSON import. A deviation entry is needed if this is accepted.
- **m1: duplicate patches.** `queueLivePatch` drops a patch whose value equals the latest pending value for that target and key, or, outside a conflict, the acknowledged value. There is no debounce, so intermediate *valid* values such as 16 on the way to 160 still preview live.
- **m3: late reset or restore replies.** Normal and late replies now share one post-apply path, `afterApplied`, so a late reset or restore re-selects like the normal path. The test waits for the real 8 s timeout.
- **m2: report wording.** "Notes and remaining concerns" in changes after first review and the round-1 handshake-test note now say: with the real bridge, `load` arrives before `bridge-ready`, so the first connect mints two sessions, and replies tagged with the first are dropped. "One session per connect" holds only for the fake's order.

### GREEN evidence

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -v
→ Ran 49 tests in 126.368s — OK   (29 Task C + 20 existing)
… -m unittest test_studio_live   (×2 more runs) → Ran 29 tests … OK, OK
cd .. && python3 scripts/verify.py --static-only
→ PASS HTML IDs: 74 unique static IDs; PASS JavaScript syntax: 1 executable inline blocks;
  SHA-256 font_kit_studio_v0.1.1.html: 0e394191dd25e4257e50652f8ea15be859922802edff25452b6b5fdf321bdb21; provenance PASS ×3
git diff --check -- font_kit_studio_v0.1.1.html → clean
```

**Not run:**
- Firefox (D010).
- `node --check fontkit-bridge.js` and the full `discover` suite. Neither file is mine, and they are the gate runner's job.

**Test-quality note:** these tests use the fake target. The real-bridge boundary test required by the new `AGENTS.md` belongs to Task D (`tests/test_live_integration.py`).
