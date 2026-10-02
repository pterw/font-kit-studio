# v0.2.0 Task C review: Studio protocol client, inspector, overlay, code panel

- **Reviewer:** read-only independent reviewer.
- **State:** Task C is uncommitted in the working tree.
- **Scope:**
  - `git diff -- font_kit_studio_v0.1.1.html`
  - `tests/test_studio_live.py`
  - `tests/fixtures/studio/**`
  - `docs/implementation/tasks/v02-task-c-report.md`
- **Requirements:** the plan's "Protocol contract", "Dev server endpoints" and "Task C" sections. Addendum 1 was ignored. Spec sections checked: §2, §5, §7–10, §13–16.

## Commands run

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -v
→ Ran 38 tests in 70.586s — OK

cd .. && python3 scripts/verify.py --static-only
→ PASS HTML IDs: 74 unique static IDs; PASS JavaScript syntax; provenance PASS ×3
→ SHA-256 font_kit_studio_v0.1.1.html 5ff9a69f…aa15, which matches the report
```

### Throwaway probes

The probes are scratch files named `reviewC-probe.py` to `reviewC-probe5.py`, with fixtures in `reviewC-fx/`. Each one copies `fake-target.html` with a single change, served from a separate `http://probe.test` origin. All run in Chromium.

| # | Probe | Result |
|---|---|---|
| 0 | Fixed `support.route_virtual_origins` used directly, without `_SingleArgRoutes` | Connects: `Connected (5 targets)`, no page errors |
| 1 | Type `24` key by key (`press_sequentially`, 120 ms delay) into `#liveFontSize` on `hero.title` (computed 32px) | Field ends as **`324`**; patches sent `[{fontSize:2},{fontSize:324}]`; target renders **324px** |
| 2 | Open Studio at `?target=javascript:parent.__pwned=parent.location.origin;void 0` | `window.__pwned === "http://studio.test"`: **script ran in Studio's origin** |
| 3 | Target name `<img src=x onerror=…>Hero`; check target list, hover and selection | No `<img>` in inspector or overlay; the name shows as literal text; no execution |
| 4 | Bridge posts `bridge-ready` after `load` (late bridge), then the iframe navigates to a page with no bridge | Badge stays **`Connected (5 targets)`** after 5.5 s; no "No bridge detected" |
| A | Same navigation with the normal order (bridge-ready before load) | `No bridge detected`, which is correct |
| B | Sync is on: edit to 70px → Sync → reload → Accept target state → edit another element (auto-sync) | The last PUT body **no longer contains `70px`**; the overrides file loses the earlier change |
| C | Request held past the 8 s timeout, then the late `design:applied` is released | Target renders 60px; Studio JSON `overrides: {}`; field shows 32 |
| 3/5 | Real `fontkit-bridge.js` and `demo/index.html` (Task B done): send every message type, then reload ×3 and navigate to a page with no bridge | Every Studio message carries `protocolVersion: 1` and the current `sessionId`; two hellos on every connect; badge stays **`Connected (34 targets)`** on the page with no bridge |

## Spec Compliance

### Message gating and transport

- ✅ **Origin, source, version, type and session gating.** `acceptBridgeMessage` at `font_kit_studio_v0.1.1.html:3035-3042` checks `event.source === iframe.contentWindow`, `event.origin === expectedOrigin`, `protocolVersion === 1`, a known `BRIDGE_TYPES` type, and `sessionId` (except for `bridge-ready`).
  - The test at `tests/test_studio_live.py:175-211` covers four spoof sources: a foreign-origin frame, Studio's own window, the right frame with a wrong session, and the right frame with no `protocolVersion`.
- ✅ **Studio posts only to the iframe, at `expectedOrigin`.** See `:3028-3033`; `"*"` is used only for a `"null"` origin. `postMessage` appears exactly once in the file. The boot-time parent hello and the parent/opener posts are gone.
  - The behavioural host test is at `tests/test_studio_live.py:234-263`.
- ✅ **Fresh `fks-<16 hex>` session per handshake.** See `:3021-3025` and `:3051-3056`.

### Request handling

- ✅ **One request in flight; pending patches coalesce per target, stopping at a reset or restore.** See `:3112-3134`.
- ✅ **Revision tracking.** The revision comes from `ready`, `applied` and `rejected` (`:3183`, `:3281`).
- ✅ **A revision conflict is retried exactly once, with a new `requestId`.** See `:3197-3201`. Tests at `:411-453`.
- ⚠️ **Rejection reseeds the control.** This works, but it combines badly with sending partially typed values; see Important I1 (`:3203-3204`, `:3408-3412`).

### Connect behaviour

- ✅ **No composition broadcast on connect.** `broadcastLiveState` sends only after an explicit ⚡ Sync (`:3748-3754`, `:3756-3768`).
- ✅ **The ⚡ button still works and is session-gated.** Tests at `:213-232` and `:622-644`.
- ✅ **Exactly one anti-recursion guard.** It is at `:3881`, and it is gone from `sendDesignMessage`.

### Pages and inspector

- ✅ **All the listed badge states exist.** "No bridge detected" appears after 4 s with `#bridgeHint`.
  - ⚠️ One edge case with a late bridge leaves the badge stale; see Minor M2.
- ✅ **`?target=`** prefills the URL, switches to Composer → Target App and connects. It is skipped when Studio is embedded (`:3906-3912`).
  - ❌ It does not restrict the URL scheme; see Critical C1.
- ✅ **Select/Interact toggle.** It uses `aria-pressed`, and the mode is re-sent after `ready` (`:3285`).
- ✅ **Studio-owned overlays** sit in a `pointer-events:none` layer and are hidden in Specimen view and before ready (`:3324-3341`). The test checks that nothing is injected into the target DOM.
- ✅ **`design:selected` never touches composer slots** (`:3300-3305`).
  - `design:select-slot` is not handled.
  - The test at `:321-326` sends a genuine-session `select-slot` and confirms the export is unchanged.
- ✅ **Specimen inspector unchanged.** `renderInspector` has a single guard at `:2436`. Test at `:351-354`.
- ✅ **Live inspector shows only `editable` controls,** seeded from `computed` (px → em or ratio, rgb → hex). Canonical values are reflected back (550 is shown as 600).

### Code panel

- ✅ **CSS:**
  - header comment, `:root` tokens and one rule per changed target, each headed `/* name (id) */`;
  - auto-discovered annotation and `!important` on every declaration;
  - no timestamps;
  - unsafe selectors and values are dropped (`:3512-3538`).
- ✅ **HTML:** snippets, or `<!-- No text changes yet. -->` (`:3540-3544`).
- ✅ **JSON:** `{target, revision, overrides}` (`:3546-3548`).
- ✅ **Output is set with `textContent`.**
- ⚠️ The CSS source is the target's session ledger, not Studio's canonical state; see Important I2.

### Sync

- ✅ `GET /__fontkit/status` is called on Studio's own origin; sync is disabled under `file://` with an explanatory title (`:3616-3639`).
- ✅ `PUT` sends `Content-Type: text/css` (`:3652`).
- ✅ Auto-sync is debounced 400 ms and serialized with a busy flag plus a queued flag. The test confirms `max active = 1`.

### `live` import and export

- ✅ **Import is transactional.** `parseLiveField` runs before anything is published (`:2788`, `:2911-2930`), and the test covers 10 bad shapes.
- ✅ **`__proto__` ids are safe;** they are stored through `setOwn`.

### Reconnect banner

- ✅ **The banner never auto-applies.** `reconcileSavedOverrides` only compares (`:3210-3222`).
- ✅ **Reapply** sends minimal patches, with `null` for keys present only on the target.
- ✅ **Accept** adopts the target state. Tests at `:666-702`.

### Layout and safety

- ✅ **Layout:** no horizontal overflow at 390 px, and IDs are unique (test `:753-768`, plus `verify.py`).
- ✅ **XSS through bridge data.** Every target-supplied string that reaches `innerHTML` goes through `escapeAttr`. This covers the name, id, role and tag in the list and the selected view, and the badge text that carries the rejection reason (`:3427`, `:3433-3439`, `:3445-3475`). Weights are filtered to finite numbers. Overlay labels and code output use `textContent`. Probe 3 confirms no injection.
- ✅ **No leaks on reconnect.**
  - There is one window `message` listener.
  - The inspector's listeners die with its replaced `innerHTML`.
  - `requestTimer` and `noBridgeTimer` are cleared on every handshake or re-arm, and `live.targets` is replaced on `ready`.

## Strengths

- **The gating is complete.** It is exactly the contract's predicate, and the RED evidence is genuine: it shows baseline accepting a forged `design:applied`.
- **The request queue is small and correct.** Coalescing respects reset and restore barriers, the conflict retry is guarded by `op.retried`, and `reflectCanonical` and `reseedLiveControls` never overwrite keys that are still pending.
- **A real regression was found and fixed during GREEN.** A `change` from a stale control could patch the wrong target. Controls are now bound to the target they were rendered for (`:3414-3419`).
- **The fake target is deterministic** and faithful to the contract. It covers hold/release, `bumpRevision`, `conflictAlways`, ledger and HTML cleaning, and runs in a real cross-origin setup.
- **XSS discipline is consistent:** `escapeAttr` for every bridge string in templates, `textContent` everywhere else.
- **Persistence edge cases are handled carefully:** an invalid `live` field fails the whole import, `__proto__` ids are safe, and auto-sync is suppressed while a conflict is open.

## Issues

### Critical

**C1. `?target=` runs `javascript:` URLs in Studio's origin, a reflected XSS that is new in Task C.** (`font_kit_studio_v0.1.1.html:3070-3091`, `:3906-3912`)

- **Cause:** `connectTargetApp` accepts any URL that `new URL()` parses and assigns it to `targetAppFrameEl.src`. Before the first navigation, the iframe's document is the initial `about:blank`, which inherits Studio's origin. A `javascript:` src therefore runs with full access to `parent`.
- **Verified failure (probe 2):** `http://studio.test/font_kit_studio_v0.1.1.html?target=javascript:parent.__pwned=parent.location.origin;void 0` leaves `window.__pwned === "http://studio.test"` in Studio.
- **Impact:** on the dev server, a crafted link can do anything Studio can do:
  - `PUT /__fontkit/overrides.css` succeeds, because the `Origin` matches, so the link can write arbitrary CSS into the repo's overrides file;
  - it can read `localStorage`.
- **Other paths to the same sink:**
  - the URL box with Enter or Connect (self-XSS);
  - an imported `live.target`, which prefills the box at `:3227`.
- **Fix:**
  - In `connectTargetApp`, accept only `http:` and `https:`, plus `file:` when Studio itself is `file:`. Anything else should show `Invalid target URL`.
  - Apply the same check to `parseLiveField`'s `target` and to `status.target`.
  - Add a test with `?target=javascript:…`.

### Important

**I1. Partially typed numbers are sent, rejected, and the reseed corrupts what the user is typing.** (`:3478-3486` together with `:3203-3204` and `:3408-3412`)

- **Cause:**
  - `bindNumber` sends a patch on every `input` event, even when the value fails Studio's own `canonicalLiveValue` rules.
  - Typing a font size of 10–39 or 100–399 therefore first sends `fontSize: 1`, `2` or `3`, which the target rejects as `unsupported-value`.
  - The rejection calls `reseedLiveControls`, which writes the computed value back into the field the user is still typing in.
- **Verified failure (probe 1):** on `hero.title` (32px), clearing the field and typing `2`, `4` gives a field value of `"324"`. Studio sends `[{fontSize:2},{fontSize:324}]` and the target renders **324px**, which becomes the acknowledged canonical value.
- **Why the tests miss it:** they use `fill()`, which sets the whole value in one event.
- **Fix:**
  - In `bindNumber`, run `canonicalLiveValue(key, value)` locally and skip sending (with no reseed) while the value is out of range, so an incomplete value is not a request.
  - Do not reseed a control that is focused because of a rejection of a value Studio has already discarded locally. Alternatively, reseed on `blur`/`change`.
  - Add a keystroke-level test (`press_sequentially('24')` → field `24`, target `24px`).

**I2. "Accept target state" followed by any edit makes auto-sync drop earlier synced overrides from the file.** (`:3247-3254`, `:3512-3538`, `:3641-3671`; report decision 8)

- **Cause:**
  - `liveCss()`, which is what gets synced, is built only from the target's session ChangeLedger.
  - After a target reload, the ledger is empty. With the real demo, earlier styles are still visible, but they come from the linked `fontkit-overrides.css`, not from inline overrides.
  - Accepting the target state sets `live.overrides = {}`.
  - The next acknowledged edit triggers auto-sync, which rewrites the file with only the new rule.
- **Verified failure (probe B, fake target with the sync endpoint mocked):**
  1. Edit `hero.title` to 70px and press Sync: the PUT contains `70px`.
  2. Reload the target; the banner appears. Press Accept target state.
  3. Change `hero.lead`'s colour: the next auto-sync PUT body contains only the `hero.lead` rule.
  4. On the next reload, the title loses 70px.
- **Why it matters:** the banner says "Nothing was applied automatically", but nothing warns that Accept will clear the synced file. This conflicts with Spec §2.2/§5.2 (Studio is the persistence authority) and §16 (never silently overwrite either side).
- **Fix, either of:**
  - (a) Generate the synced CSS from Studio's canonical `live.overrides`, mapping keys to CSS through `LIVE_CSS` and taking selectors from the manifest or ledger. Keep using the ledger for the HTML tab.
  - (b) At minimum, make Accept disable auto-sync and say clearly that the overrides file still holds the previous state until the next sync, then require an explicit Sync.
- **Test:** add one at Task C or D level: sync → reload → accept → edit, then assert the PUT body.

**I3. A stale `bridgeReadySinceLoad` flag makes Studio skip the load handshake, so it can show `Connected` to a page with no bridge.** This is reachable with the real bridge. (`:3095-3102`, `:3270-3275`)

- **Cause:**
  - The real `fontkit-bridge.js` initialises on `DOMContentLoaded` and announces at `:299`/`:441`. In practice Studio handles the iframe's `load` *before* `bridge-ready`; probes 4 and 5 below show two hellos on every connect.
  - So `bridge-ready` sets `bridgeReadySinceLoad = true` *after* that document's load. The next document's `load` sees the flag, skips the handshake, and leaves `live.ready` true with the old session.
  - A reload still recovers, because the reloaded bridge sends `bridge-ready` again.
- **Verified failure (real bridge and demo):**
  - Connect → three reloads (each stays `Connected (34 targets)`).
  - Then navigate the preview to a page with no bridge (`/tests/fixtures/studio/no-bridge.html`).
  - After 5.5 s the badge still reads **`Connected (34 targets)`**, and "No bridge detected" never appears.
  - Any edit then goes nowhere until the 8 s request timeout.
  - The same happens with the fake fixture changed to announce late (probe 4). The unmodified fake announces first, so the existing tests cannot catch it.
- **Fix:**
  - On `load`, never skip outright. If a bridge-ready handshake is already running, keep the current `sessionId`: set `ready = false`, re-send `design:hello` with the *same* session and arm the no-bridge timer. The bridge replaces the session on every hello, and the same id cannot race.
  - Otherwise start a fresh handshake.
  - Add a test with the fake announcing after `load`, followed by navigation to `no-bridge.html`.

### Minor

**M1. `_SingleArgRoutes` is now redundant.** (`tests/test_studio_live.py:28-40`, `:59`)

- It still works, and the suite passes with it.
- Probe 0 shows the fixed `support.route_virtual_origins` (`handler(route, request=None)`) connects correctly when given the context directly.
- **Fix:** delete the adapter and pass `context`. Also update the report's "Shared-harness defect" paragraph to say it has been fixed.

**M2. Moved to Important I3** (see the follow-up below). With the real Task B bridge, this ordering is the normal case.

**M3. A late reply after the 8 s timeout is discarded.** (`:3144-3150`, `:3181`)

- **Verified failure (probe C):** the target applied 60px, but Studio's canonical overrides stay `{}` and the field shows 32. Studio and target disagree until the next reply carries a full ledger, and the JSON overrides stay wrong until that key is edited again.
- **Fix:** keep the timed-out op's `requestId` for one cycle. If its `design:applied` arrives later, still run `recordCanonical` and the ledger update.

**M4. `highlightSlotInTarget` is effectively dead.** (`:3702-3705`, callers at `:2325` and `:2661`)

- Composer slot UUIDs are never bridge target ids, so the function never sends anything.
- The callers still pass the now-unused `index` and `role` arguments.
- **Fix:** remove it or simplify the callers. This is cosmetic.

**M5. Report count does not match the brief.** The report has **10** "Contract interpretation notes", not the 6 the brief mentions. All 10 are reviewed below.

## Decisions review

1. **Skip the load hello when bridge-ready already started a handshake.**
   - **Agree** with the goal of avoiding two racing sessions.
   - The implementation has the stale-flag defect in I3, which is reachable with the real bridge. Re-greeting on load with the *same* session id would satisfy the plan's "hello on bridge-ready and on load" without the race.
2. **Composition streaming after an explicit ⚡ Sync, ending at the next handshake.**
   - **Agree.** It keeps the prototype's live typing.
   - Nothing restyles the target without a click, and a reconnect never silently re-styles it (Spec §16).
   - Optional: show a small "streaming composition" indicator so the linked state is visible.
3. **Never post to `window.parent` or `window.opener`.**
   - **Agree.** The contract and Spec §15 require it, no documented feature depended on it, and the host test proves it.
4. **Drop `design:select-slot`; `design:selected` never touches composer slots.**
   - **Agree.** The old handler mutated slot text, role and size from unvalidated messages.
   - Clean up the dead helper (M4).
5. **The reconnect banner also appears on import.**
   - **Agree.** This is the same "never silently overwrite" rule from Spec §16, applied consistently.
6. **Persisted `live.revision` and `live.target` are the canonical ones.**
   - **Agree.** Spec §6 and §14 say to preserve the last acknowledged revision.
   - Importing correctly leaves the session `baseRevision` alone.
7. **A legacy import without `live` keeps the session overrides; an invalid `live` rejects the whole import.**
   - **Agree.** It mirrors how a missing `kitIds` field is handled, and the transactional rejection is tested.
8. **CSS and HTML come from the target ledger; JSON comes from Studio's canonical overrides.**
   - **Partially disagree.** Using the ledger for the HTML tab is right, since only the target knows the cleaned markup.
   - The *synced* CSS, though, is persisted state. Under Spec §2.2/§5.2 it should come from Studio's canonical overrides. Today the split causes the data loss in I2.
   - Suppressing auto-sync during an open conflict is good, but it is not enough once the user presses Accept.
9. **Text seeding from the saved override, else the manifest's trimmed 200-character text.**
   - **Agree.** Truncation is a contract limit. Optionally, note in the UI when the seeded text is truncated.
10. **Re-select after restore or reset to refresh the inspector.**
    - **Agree.** Task D must confirm that the real bridge answers `design:select` with a `target` manifest. Otherwise the inspector would keep stale values.

## Follow-up: message stamping against the real bridge (Task B, done)

The question: the real bridge silently ignores any control message without `protocolVersion: 1` and the current `sessionId`. Does every message Studio sends carry both?

**Source check:**
- There is exactly one `postMessage` in the file (`:3032`), inside `sendDesignMessage` (`:3028-3033`).
- It returns early when there is no `sessionId`, and stamps every message as `{...msg, protocolVersion:1, sessionId:live.sessionId}`.
- All nine send sites go through it: `:3059` hello, `:3151` queue dispatch (update, composition, reset, restore-text), `:3192`/`:3438`/`:3505`/`:3704` select, and `:3285`/`:3694` mode.
- Studio no longer sends `design:highlight` at all. The legacy highlight path, `highlightSlotInTarget`, now sends `design:select`.
- The hello carries `sessionId` as well as `protocolVersion`, which Spec §7.3 and the contract table require.

**Runtime check (`reviewC-probe3.py`):**
- Setup: real Studio at `http://studio.test`, real `fontkit-bridge.js` and `demo/index.html` at `http://target.test`, a capture-phase recorder installed in the target frame, Chromium.
- Steps and results:
  - connect: `Connected (34 targets)`;
  - select from the target list;
  - targeted `fontSize` 56 → `Live · rev 1`, and the iframe computes 56px;
  - targeted `text` → rev 2;
  - Interact, then Select;
  - ⚡ Sync to Live App → rev 3;
  - ↻ Restore Page Text → rev 4: the iframe text and `#liveText` both return to the original;
  - Reset this element → rev 5, and the size returns to the original;
  - All targets (`design:select` null).
- Messages received from Studio:
  - hello ×2, select ×4, update ×3 (targeted plus composition), mode ×2, restore-text ×1, reset ×1;
  - **none** is missing `protocolVersion: 1` or `sessionId`;
  - every non-hello message carries the *current* session;
  - every update, reset and restore-text carries a string `requestId` and an integer `baseRevision`.
- **Restore Page Text** sent `{protocolVersion:1, sessionId:<current>, requestId:"fks-req-4", baseRevision:3}`. Studio matched the bridge's `design:applied` by `requestId` (`:3181`), moved the badge to rev 4, removed saved `text` overrides (`:3166-3171`) and re-selected to refresh the inspector (`:3191-3193`).
- **Errors:** no page errors. The only console errors were two 404s, both expected in this harness: `/__fontkit/status` (no dev server) and `demo/fontkit-overrides.css`.

**Result:** no message is missing a field, so nothing in this check is flagged Important. The probe did turn up the duplicate-hello ordering behind I3.

## Assessment

The protocol client meets the contract on everything security- and correctness-sensitive that was asked about:

- origin, source and session gating, including spoofs from the right window with the wrong session;
- no `"*"` posts to parent or opener;
- a single in-flight request with per-target coalescing and one conflict retry;
- no broadcast on connect;
- a `design:selected` path that does not touch the composer;
- a transactional `live` import;
- a reconnect banner that never auto-applies;
- escaped bridge strings;
- no overflow at 390 px, and unique IDs.

All 38 tests pass, and the static verify passes.

Against the real Task B bridge, every message Studio sends carries `protocolVersion: 1` and the current `sessionId`, and Restore Page Text works end to end.

Four verified defects block approval:

- **C1:** the new `?target=` parameter is a reflected `javascript:` XSS in Studio's origin, which can write the overrides file through the dev server. The fix is a one-line scheme allow-list.
- **I1:** typing a font size key by key applies the wrong value (`24` becomes 324px).
- **I2:** "Accept target state" followed by auto-sync silently drops previously synced overrides from the file.
- **I3:** with the real bridge, a stale load-skip flag leaves Studio `Connected` to a page that has no bridge.

All four have small, local fixes, and each needs a behaviour test written first (RED).

**Task quality:** Changes required

---

## Re-review after first changes

- **Scope:** read-only re-review of the report's "Changes after first review" section and `git diff -- font_kit_studio_v0.1.1.html tests/test_studio_live.py tests/fixtures/studio`.
- **State:** The Task C HTML is uncommitted, SHA-256 `6f1fe8c2…085a`, which matches the report.

### Commands

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011
→ Ran 47 tests in 119.387s — OK
cd .. && python3 scripts/verify.py --static-only
→ PASS HTML IDs (74 unique) · PASS JavaScript syntax · provenance PASS ×3
git diff --check -- font_kit_studio_v0.1.1.html → clean
```

The probes are scratch files: `reviewC-r1-schemes.py`, `reviewC-r1-behaviour.py`, `reviewC-r1-real.py` and `reviewC-r1-tokens.py`.

### Original findings

#### ✅ C1: target URL schemes (`safeTargetUrl` at `:2908-2913`)

`new URL()` normalises the scheme, removing leading C0 controls and spaces and any tab or newline inside it, and lowercases it. The check then allows only `http:` and `https:` (`file:` only when Studio itself is `file:`).

**Probe matrix:** 12 payloads × 6 paths, with **0 failures**.

Payloads:
- `javascript:` in mixed case, with leading space and tab, with leading `\x01\x02` or `\x00`, and with a tab or newline inside the scheme;
- `data:` and `DATA:`;
- a fake `blob:`;
- `vbscript:` and `VBScript:`.

Paths:
- `?target=`;
- the URL field via Connect, via Enter, and via switching to the Target App view;
- `live.target` on import;
- dev-server `status.target`.

Results:
- `window.__pwned` was never set.
- No non-http `src` was ever assigned.
- Every import failed, and the URL field was never prefilled with a payload.
- A **real** same-origin `blob:` URL containing a script, typed into the field, gave `Invalid target URL` with no `src`.
- `?target=` with a bad scheme shows `Invalid target URL` and a composer note (`:4049-4059`).

#### ✅ I1: key-by-key numeric entry

Typed with `press_sequentially` at 120 ms per key:

| Target, field, typed | Field (focused → blurred) | Target result |
|---|---|---|
| `hero.title`, size `24` | `24` → `24` | 24px; only `{fontSize:24}` was sent |
| `hero.title`, size `160` | `160` → `160` | 160px |
| `hero.title`, weight `300` | `300` → `300` | 300 |
| `hero.title`, line-height `1.5` | `1.5` → `1.5` | applied |
| `hero.title`, letter-spacing `0.08` | `0.08` → `0.08` | applied |
| `hero.title`, letter-spacing `-0.05` | `-0.05` → `-0.05` | applied |
| `stat.badge`, weight `550` | `550` → `600` | 600 |

- Out-of-range partial values are no longer sent; they are marked with `aria-invalid` (`:3597`).
- Focused controls are not overwritten (`:3490`).
- No page errors.
- With the real bridge, typing `48` gives 48px and the field shows `48`.

#### ✅ I2: persisted CSS and Accept

- `liveCss()` now builds from Studio's canonical `live.overrides` plus `targetMeta` (`:3654-3685`).
- I re-ran sync → reload → Accept → edit:
  - the banner now says Accept "replaces Studio's 1 target of saved overrides … and the overrides file only changes when you sync";
  - Accept turns auto-sync off and says so;
  - the edit afterwards produced **0 PUTs**, and the last file body still contains `70px`.

#### ✅ I3 / M2: iframe load always re-greets (`:3112-3126`)

- **Real bridge and demo:** two reloads stayed `Connected (34 targets)`. Navigating to `no-bridge.html` gave **`No bridge detected`**, with the hint, within 5.5 s. Navigating back gave `Connected (34 targets)`.
- **Fake with late announce (`?late=1`):** two reloads stayed connected, and navigating to a page with no bridge gave `No bridge detected`.

#### ✅ M3: late replies (`handleLateReply`, `:3220-3231`)

A timed-out op's late `design:applied` now updates the ledger, the canonical overrides and the revision, which only ever increases. It also schedules auto-sync. This is covered by the report's test.

#### ✅ M4 and M1: cleanup

- `highlightSlotInTarget` and its call sites are gone.
- `_SingleArgRoutes` is gone; the test uses `route_virtual_origins(context, …)` directly at `tests/test_studio_live.py:45`.

### Task B compatibility addenda

- ✅ **(a) Trimmed text comparison.**
  - `effectiveOverrides` and `originalTextFor` (`:3263-3283`) compare saved text, trimmed, with the original.
  - `recordCanonical` drops a text override when the ledger reports no text change (`:3190-3194`).
- ✅ **(b) `design:targets` replaces the list** (`:3406-3417`). It clears a removed selection or hover and refreshes the inspector.
- ✅ **(c) `CSS.supports` on `live` import** (`:2931-2934`). Only `font-family` and `color` are checked, which matches the free-form keys; the others are already enumerated or numeric.
- ✅ **(d) ⚡ composition triggers auto-sync.**
  - `handleReply` now calls `scheduleAutoSync()` unconditionally, and it is still suppressed while a conflict is open.
  - See I4: the tokens this writes are not retained across a reload.

### B↔C smoke with the real bridge (Task B, re-fixed)

**Steps and results:**
- connect: `Connected (34 targets)`;
- select from the list;
- type size `48`: 48px;
- text edit;
- Interact, then Select;
- ⚡ Sync;
- ↻ Restore Page Text: `#liveText` returns to the original text;
- Reset: 65.28px, the original;
- JSON `overrides: {}`.

**Messages Studio sent:**
- hello ×2, select ×3, update ×4, mode ×2, restore-text ×1, reset ×1;
- every message after the handshake carries `protocolVersion: 1` and the current `sessionId`.

**The one exception is the very first hello.** On first connect the real bridge's `load` arrives before `bridge-ready`. The load handler mints session A because none exists yet, and then `bridge-ready` starts session B.
- This is harmless: replies tagged A are dropped.
- It does contradict the report's "one session per connect" for the real bridge's order; see m2.

No page errors.

### New issues

#### Important

**I4. After ⚡ Sync, a target reload, then one ordinary edit, auto-sync silently drops the composition tokens from the overrides file.** (`liveCss` `:3655-3660`, `reconcileSavedOverrides` `:3286-3296`; open concern 4 in the report)

- **Verified (`reviewC-r1-tokens.py`, fake target, sync endpoint mocked, auto-sync on):**
  1. ⚡ Sync to Live App: the PUT contains `:root { --font-display: … }`.
  2. Reload the target: **no banner** appears and auto-sync stays on, because `reconcileSavedOverrides` compares only targeted overrides, and those are empty.
  3. Change `hero.title` to 50px: auto-sync PUTs a body **without `:root`**.
- **Why it matters:** with the real demo, the `--font-*` tokens disappear from `fontkit-overrides.css` on the next reload. Nothing warns the user, which conflicts with Spec §16 (never silently overwrite).
- This is the I2 data-loss pattern again, for tokens.
- **A new `live` field is not needed**, because the Studio page itself is not reloaded. Either:
  - (a) keep the last *acknowledged* composition tokens in Studio's in-memory state (`live.savedTokens`, set from the ledger after a composition `design:applied`), use them in `liveCss`, and include them in the reconnect comparison, so a reload with empty ledger tokens raises the banner; or
  - (b) at minimum, do not auto-sync while Studio has previously synced tokens and the ledger has none.
- **Test:** add a RED test for exactly the three steps above.

#### Minor

- **m1. Intermediate *valid* partial values are still applied live.** Typing `160` sends 16 first, and weight `300` sends 3, then 30. Each creates a revision and briefly restyles the target.
  - The final value is right, and auto-sync is debounced, so this is acceptable as "live preview".
  - An optional ~150 ms debounce on numeric `input` events, or dropping a value identical to the last one sent (`0.08` sent `letterSpacing: 0` three times), would cut traffic.
- **m2. The report's "one session per connect in normal order" holds only for the fake's order.** With the real bridge, two sessions are minted on first connect, as described above. Harmless; correct the report wording.
- **m3. `handleLateReply` does not re-select after a late reset or restore** (`:3220-3231`). `handleReply` does (`:3241-3243`), so the inspector may show stale values until the next selection. Found by reading only; low impact.

### Opinion on the report's open concerns

1. **Two hellos per normal-order connect: acceptable.** The bridge answers both, and Studio reseeds the inspector in place, so focus is not stolen. The wording needs the m2 correction for the real bridge.
2. **Late-order reloads change sessions: acceptable.** This follows the contract: `bridge-ready` starts a fresh handshake, so the selection is cleared. I verified that the state recovers to `Connected`.
3. **A number field can briefly show more than the target accepted** (`1000` typed, `100` applied): **acceptable.**
   - The field is marked `aria-invalid`, and blur restores the acknowledged value.
   - Consider a short "max 400" note through the field's `title`.
4. **Composition tokens are not in the saved overrides: disagree that this can wait.**
   - It is a verified silent file overwrite (I4).
   - The reload case can be fixed **in memory**, without a new `live` field.
   - Persisting tokens across a Studio page reload or import can stay deferred, with a deviation entry.
5. **Assumed selector for an imported override before the target is seen: acceptable.** It is commented in the CSS, the id is escaped, and the selector goes through `safeCssText`.

### Verdict

Every original finding is fixed and verified, including against the real bridge: C1, I1, I2, I3/M2, M3, M4 and M1. Addenda (a)–(d) are implemented. The suites pass (47 OK), and the static verify passes.

One new Important remains: I4, the silent token loss after a reload. It needs a small in-memory fix with a RED test, or an explicit deferral recorded as a deviation, before commit.

**Task quality:** Approved with fixes

---

## Re-review after second changes

- **Scope:** read-only re-review of the report's "Changes after second review" section.
- **State:** The Task C HTML is uncommitted, SHA-256 `0e394191dd25e4257e50652f8ea15be859922802edff25452b6b5fdf321bdb21`, which matches the report.
- **Out of scope:** "saved tokens in memory only, not in the `live` JSON" is accepted as deviation D017, carried to Task F, so it is not flagged here.

### Commands

```
cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011
→ Ran 49 tests in 126.014s — OK
cd .. && python3 scripts/verify.py --static-only
→ PASS HTML IDs (74 unique) · PASS JavaScript syntax · provenance PASS ×3
git diff --check -- font_kit_studio_v0.1.1.html → clean
```

The new probe is `reviewC-r2-probe.py`; I also re-ran `reviewC-r1-schemes.py` and `reviewC-r1-real.py`. All are scratch files.

### ✅ I4: composition tokens are kept and the token loss is surfaced

- **Code:**
  - `live.savedTokens` is set only from an acknowledged composition reply, or an acknowledged global reset (`:3207`).
  - `liveCss` and the change count use it (`:3675`, `:3726`).
  - The reconnect comparison includes tokens (`:3290-3298`).
  - Reapply sends a tokens-only composition patch (`:3325-3326`).
  - Accept replaces the saved tokens (`:3336`).

**My exact probe, on the fake target with the sync endpoint mocked:**

| Step | Result |
|---|---|
| Auto-sync on → ⚡ Sync | 1 PUT, containing `:root` and `--font-display` |
| Reload the target | **Banner shown:** "Studio has saved overrides for 0 targets and 4 composition tokens; the live target has … 0 composition tokens. Nothing was applied automatically." |
| 50px edit while the conflict is open | **0 PUTs** (auto-sync suppressed). The CSS panel keeps `:root` and adds the 50px rule. |
| Reapply | Sends **one** tokens-only update (`patch` keys `['tokens']`; the 50px is already on the target, so no targeted patch). The banner hides, the target's `--font-display` is restored, and its ledger shows all 4 tokens. |
| Auto-sync after Reapply | 1 PUT; every PUT so far has the tokens, and the last has 50px |
| Reload again → Accept | Auto-sync is turned off. Status: "Saved overrides and composition tokens replaced by the target's state … The overrides file is unchanged until you press Sync to file". 0 PUTs. The CSS panel shows `/* No live style overrides yet. */`, an explicit and announced choice. |

No page errors.

**With the real bridge:**
- Steps: ⚡ Sync, title to 50px, then reload. The harness has no overrides stylesheet, so the target comes back empty.
- The badge shows `Connected (34 targets)` and **the banner appears**.
- Reapply → `Live · rev 2`, the banner hides, the target's `--font-display` equals its value before the reload, and the title is 50px.
- The real bridge therefore accepts the tokens-only composition patch.

### ✅ m1: duplicate patches are dropped, intermediates still preview

`queueLivePatch` is at `:3545-3551`. Typed key by key:

| Field, typed | Patches sent |
|---|---|
| letter-spacing `0.08` | `[0, 0.08]`; round 1 sent `0` three times |
| line-height `1.5` | `[1, 1.5]`; round 1 sent `[1, 1, 1.5]` |
| size `160` | `[16, 160]` |
| weight `300` | `[3, 30, 300]` |

- Valid intermediate values still preview, as intended.
- There are no consecutive duplicates.
- The final field values are correct.

### ✅ m3: a late reset reply re-selects

The shared `afterApplied` is at `:3223-3232`. Probe:
1. Hold the target's replies.
2. Reset this element.
3. Wait for `No response from target` (the real 8 s timeout).
4. Release the reply.

Result: `Live · rev 2`, exactly **1** `design:select` sent after the late reply, and the field and the target are both back at 32px.

### Round-1 regressions: none

- **C1:** the scheme matrix (12 payloads × 6 paths, plus a real same-origin `blob:`) has **0 failures**.
- **I3:**
  - Real bridge: two reloads stay `Connected (34 targets)`. Navigating to `no-bridge.html` gives `No bridge detected` with the hint. Navigating back reconnects.
  - Fake with late announce (`?late=1`): same results.
- **Real-bridge B↔C smoke:**
  - typing 48 gives 48px and the field shows `48`;
  - text edit;
  - Interact/Select;
  - ⚡ Sync;
  - Restore Page Text brings the original text back;
  - Reset gives 65.28px, the original;
  - JSON `overrides: {}`.
- **Messages:**
  - every message after the handshake carries `protocolVersion: 1` and the current `sessionId`;
  - the only exception is the first-connect hello on the losing session, the documented m2 behaviour;
  - no page errors.
- **m2:** the report wording now matches the real bridge's announce order.

### New issues

None found at Critical, Important or Minor level.

### Verdict

Every finding from the review and both later sets of changes is resolved and verified:
- C1, I1, I2, I3/M2 and I4;
- M3, M4, M1, m1, m2 and m3;
- addenda (a)–(d).

The verification covered unit tests, the fake target, and the real Task B bridge. D017 (tokens kept in memory only) is accepted.

**Task quality:** Approved
