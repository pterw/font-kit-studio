# v0.2.0 Task F review (read-only reviewer)

- Task F uncommitted. Scope: `font_kit_studio_v0.1.1.html`, `tests/test_studio_live.py`, `tests/fixtures/studio/**`, `tests/test_font_kit_studio_v011.py` (unchanged), report `v02-task-f-report.md`.
- Gates re-run: `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_studio_live test_font_kit_studio_v011 -v` -> **Ran 75 tests, OK** (190 s, Chromium only; Firefox not installed, D010). `python3 scripts/verify.py --static-only` -> PASS (86 unique static IDs, JS syntax, sha256 `94268d82...` identical to the report, provenance x3). Not run: `node --check`, full `discover` (not Task F files).
- Contract notes applied: D020 (css-order persistence) is accepted; verified for correctness only. Addendum 3 amendment (bulk manifests omit both `containers` and `siblings`) was checked, see Minor M1.

### Spec Compliance

- ✅ Arrange UI (Addendum 1 Task F): `#liveMoveFirst/Prev/Next/Last`, `#liveSiblingList` (draggable, tabindex, Alt+Up/Down per item), `#liveMoveContainer` + `#liveMoveInto`, strategy toggle only when `cssOrderAvailable`, default CSS order for framework-managed (`html:3990-4160`, `arrangeHtml`/`bindArrange`). Probed against the real bridge on `demo/index.html` (46 targets): Arrange rendered, Next moved the card, HTML tab showed the `Structure:` block, CSS-order toggle absent for non-flex parent.
- ✅ Keyboard: probed Alt+ArrowDown/Left with focus in `#liveText`, `#liveFontSize`, `#liveColorHex`, `#targetAppUrl`, `#composerKitIds` and `#liveMoveContainer`: 0 moves sent and `defaultPrevented === false` on every field (caret movement untouched). Alt+ArrowDown with focus on a plain inspector button moved the element. (`typingTarget`, `html:4296-4310`).
- ✅ Move anyway (Addendum 2): shown only for `framework-managed`/`framework` with `overridable !== false` (`noteMoveRejection`). Verified with `content-model`/`label-reference` + `overridable:true` from the target: no button. The real bridge's guard shape (`detail.guard/message/overridable/framework`, `fontkit-bridge.js:1125`) matches what Studio reads.
- ✅ Warnings are text only. Probe: guard name `<img onerror>`, guard message with `<img onerror><b>`, and a `design:warning` with `<img onerror>`: all rendered escaped, 0 `<img>` nodes, `window.__xss` never set. `renderWarnings` uses `textContent`/`replaceChildren`; guard HTML goes through `escapeAttr`.
- ✅ Pop-out URL gate: `popOutTarget` uses the same `resolveTarget` as Connect. Probed 13 payloads (`javascript:`, mixed-case, leading space, `data:`, `blob:`, `vbscript:`, `file:`, `ftp:`, `about:blank`, recursion variants, malformed IPv6): `window.open` called 0 times, each shows `Invalid target URL` or `Recursion blocked`. (A newline inside the field is turned into a space by the input element, giving a relative http URL; that is safe and identical to Connect.) `window.open` receives exactly `(href, "fontkit-target")`.
- ✅ Popup gating: a second same-origin window opened by the page (name `otherwin`) received 0 hellos, and its forged `design:warning` / `design:bridge-ready` to Studio were ignored (status unchanged, warning hidden). `acceptBridgeMessage` checks `event.source === targetWindow()` plus origin, version, session.
- ✅ `overlay`: popup got `design:mode {mode:"select", overlay:true}`; iframe mode sends `overlay:false` (covered by existing test). Real-bridge pop-out connected and drew its own outline nodes (3), and Dock reconnected the iframe and closed the popup.
- ✅ Interval hygiene (instrumented `setInterval/clearInterval`): 0 live 500 ms intervals after rejected payloads, after Dock, after popup close (x3 rounds), and after Connect while popped out; exactly 1 while popped out.
- ✅ Free fonts: `grep -i 'cqu4tvx\|YOUR_KIT_ID'` -> 0 hits; remaining `typekit` hits are the BYO loaders (`html:1543-1579, 2141`) and the Typekit allow-list. 16 families, `curl` of all 16 css2 URLs through the proxy: all HTTP 200. Hung (black-holed) `fonts.googleapis.com`: cards render in 0.16 s, typing and the Load buttons stay responsive, the 8 s "Still waiting... system fallbacks" status appears, no page errors (the browser load event stays pending while requests hang, nothing in Studio waits on it). Adobe BYO: entering `abc1def` requests exactly `https://use.typekit.net/abc1def.css` (Library and Composer). Old export with `gotham`, `ella-roman`, unknown key imports as `work-sans`, `instrument-serif`, `fraunces`; `kitIds` from the file are preserved (user data, not a default).
- ✅ `fontStylesheet`: library family -> css2 URL, other family -> `null`, other keys never carry it (existing test, re-run green).
- ✅ D017: `live.tokens` validated before any mutation (16 bad shapes in the test; probe confirmed export/canvas unchanged on rejection); `Reapply` replays them (test), `Accept` sets `savedTokens` from the target (`html:3637`) and the banner/status wording names overrides and tokens explicitly (`html:3646`, `3660-3666`).
- ✅ D020: CSS-order persistence correct in the main flows. Probe: saved order for a subset (`card.d:0`, `card.b:1`) replays as two `css-order` moves and the target ends `d, b, a, c`, with the CSS tab listing `order: 0/2/1/3` for all four (bridge writes every sibling). DOM moves stay session-only. `order` is excluded from patches (`delete patch.order`) and import validates integer -9999..9999.
- ✅ Regressions: Task C gating/typing/sync/banner/URL tests all green in the 75; legacy 20 untouched; 390 px: `scrollWidth == clientWidth == 390` in Composer/target view (with guard + 250-char warning), Library view, pop-out placeholder, Adobe preset. Runtime IDs unique in the arrange/pop-out states (verify static + test helper).
- ⚠️ At 320 px the document overflows to 368 px (`#deviceViewportBar`, `#btnToggleFullscreen`, which now also hosts the new Pop out button). Outside the required 390 px; not flagged as an issue.

### Strengths

- One URL gate (`resolveTarget`) shared by iframe and pop-out; one `targetWindow()` abstraction keeps source/origin gating identical in both modes.
- Guard semantics are conservative by construction: `FRAMEWORK_GUARDS` is an allow-list, so an unknown or hostile guard name can never show an override.
- One move in flight at a time and Arrange-only re-render with focus restoration are good, low-risk UX choices.
- Tests: RED evidence recorded, no new fixed sleeps except for negative assertions, fake target mirrors the real bridge's guard/reply shapes (verified against `fontkit-bridge.js`).
- Legacy Adobe families map to free look-alikes; offline loading degrades with a status instead of errors.

### Issues

**Critical:** none.

**Important**

- **I1. Reapply drops `fontStylesheet` for library families.** `reapplyStudioOverrides`, `html:~3600-3606` (`patch = {...want}` then `enqueueLiveOp({kind:"update", ...})`). Verified: select Fraunces on `hero.title` (patch had `fontStylesheet`), reload the target, press Reapply: the update patch is only `{fontFamily:'"Fraunces", serif'}`, and the target ledger `imports` stays `[]`. A target that does not itself link the synced overrides file therefore shows a system-fallback font after Reapply while the banner says Studio's state was applied and the CSS tab lists the `@import`. Fix: when building each replay patch, if `libraryFontForStack(want.fontFamily)` is a library font add `fontStylesheet: fontStylesheetUrl(font)` (and `null` for a non-library family, as the live handler does); add a test beside `test_css_order_moves_persist_in_live_json_and_reapply_after_a_reload`.

**Minor**

- **M1. Studio assumes bulk manifests carry `siblings: []`, not an omitted field (Addendum 3 amendment).** `normalizeArrangement`, `html:~3990`: `!Array.isArray(raw.siblings)` returns `null`, and `fetchFullArrangement` only re-selects when `arrangement.count > 0 && !siblings.length`. The fake target also sends `siblings: []` (`fake-target.html:165`). Verified by patching the fake to omit it (probe `reviewF-p5.py`): the initial select still fills the list, but after a bulk `design:targets` for the selected target Studio sends 0 re-selects, keeps a stale list, and Move buttons send 0 `design:move` (silent no-op). Fix: `const rawSiblings = Array.isArray(raw.siblings) ? raw.siblings : []` (and treat missing `containers` the same, which already works), update the fake to omit both fields, adjust `test_bulk_manifests_and_arrangement_only_targets`. The real bridge currently still sends `siblings: []` (`fontkit-bridge.js:2397`), so this only bites after Task E's amendment lands.
- **M2. Reapply does not clear a target-side `order` that Studio no longer has saved.** `delete patch.order` (`html:~3603`) also removes the `order: null` that the `have`-loop would have produced, and `reapplyOrders` only replays saved orders. Verified: target reordered by CSS order, import JSON whose `live.overrides` has no `order`, Reapply: banner hides, target keeps `c,a,b,d` while Studio's CSS/JSON have no `order`. Preview and persisted file then disagree until the next reload. Fix: for sibling groups whose target ledger has `order` but saved has none, send `design:reset` for those targets (or `order:null` if the bridge accepts it), and document the choice.
- **M3. ⚡ Sync to Live App sends library font stacks as tokens without `fontStylesheet`** (`compositionPatch`, `html:~4575`): the target gets `--font-display: "Fraunces", serif` but not the stylesheet, same class as I1. Legacy composition updates have no stylesheet key in the contract, so this is a contract gap to note rather than a Task F defect.
- **M4. Alt+Left/Alt+Right are also bound** (`html:~4305`) and `preventDefault`-ed while the Target App view has a selection, which suppresses browser Back/Forward on Windows/Linux. Plan only names Up/Down. Fix: restrict the global shortcut to Up/Down (keep Left/Right inside the sibling list only).
- **M5. A hung network keeps the page load event pending** (spinner) because link elements are inserted during the initial script (`applyTextSlotStyles` -> `ensureFontStylesheet`). No functional impact found; optional: defer composer font links to `requestIdleCallback`/after `load`.

### Contract-note opinions (report "Contract notes and deviations")

1. Guard names: agree; confirmed against `fontkit-bridge.js:1203-1339`. `label-reference` currently has no `overridable` field in the bridge (`:1339`); harmless since it is never forced.
2. CSS-order persistence: agree with D020; implementation is correct for full-group saves (probed), see M2 for the stale-order edge.
3. Bulk manifests / `arrangementOnly` excluded from the count: agree (`Connected (N)` counts editable targets). Align per M1.
4. `fontStylesheet: null` on non-library choice: consistent with the plan; real-bridge behaviour of `null` release is Task E's contract (the fake counts references the same way).
5. CSS tab note only when `structure` is non-empty: fine.
6. `design:mode` always carrying `mode` and `overlay`: agree; the real bridge accepted it (popout probe).
7. Pop-out keeps `window.opener` (required by the contract). A target page can therefore navigate Studio via `opener`; acceptable because the user chooses the target, but worth one README line (Task D).

### Assessment

Code quality: the HTML grew from 4084 to 4789 lines (+705 net, 178 KB -> 219 KB, about +23%); roughly 90 lines are the verbose 16-family table, ~370 are Arrange/pop-out/warnings, and the rest CSS and import/tokens. Still a single dependency-free file. No dead code introduced (every new symbol is referenced; `byName` has one use but pre-exists). Rule-of-three candidates: `live.selectedId ? arrangementOf(live.selectedId) : null` appears 5 times (extract `selectedArrangement()`), the reset-session block `resetSessionState(); live.sessionId = null; live.targets = new Map();` appears 3 times (plus the iframe variant), and the guarded `try { live.popup.focus() } catch` twice. `safeFontStylesheet` mirroring the bridge validator is intentional isolation (Rule 10). Tests are thorough (26 new, behavioural, no new fixed sleeps); the one gap is that none cover Reapply of a library font (I1) or an omitted-`siblings` bulk manifest (M1).

Everything listed as a check passes against real browsers and the real bridge, except I1 (a small, localized fix) and the Minors above. Real-bridge probe worked; no bridge-side failure was encountered, though the bridge was being edited concurrently.

**Task quality:** Approved with fixes

---

## Re-review after first changes (scoped, read-only)

HTML sha256 `33bde4ff...` confirmed (matches `verify.py`). Real bridge = committed Task E via `demo/index.html` on virtual origins. Probes: `reviewF-r1.py`, `r2.py`, `r3.py` in scratch.

**Gates:** `python3 -m unittest discover -s tests -v` with the FKS env vars (includes `test_studio_live` and `test_font_kit_studio_v011` at the 78 tests the report lists): **Ran 179 tests, OK** (277 s, Chromium only, D010). `verify.py --static-only`: PASS (86 unique IDs, JS syntax, sha `33bde4ff...`, provenance x3). Not run separately: `test_studio_live`+`v011` as their own invocation (covered by discover, same tree, same env).

**Correction to my first review:** my first Alt+Arrow probe attached a `once` keydown listener, which recorded the bare `Alt` keydown rather than the arrow. I re-ran it with the listener filtered to `Arrow*` keys: Alt+Left, Alt+Right and Alt+Shift+Left are `defaultPrevented === false` and send 0 moves; in the text fields tested (`#liveText`, `#liveFontSize`, `#liveColorHex`, `#targetAppUrl`, `#composerKitIds`, `#liveMoveContainer`) Alt+Arrow sends 0 moves; Alt+Up/Down with a button focused is `defaultPrevented === true` and moves once. The conclusions of the first review stand.

- **I1 fixed (real bridge).** Fraunces on `landing.hero.title`, reload target, Reapply: before reload the target had the Fraunces `<link data-fontkit-font>`; after reload `imports` = `[]` and computed `font-family` = the system serif stack; after Reapply `imports` = the Fraunces css2 URL and computed `font-family` = `Fraunces, serif`. Non-library family releases via `null` (test green).
- **M1 fixed (real bridge).** After connect, selecting `landing.feature.sync.title` fills the list (3, "Position 2 of 3"). Appending an element makes the bridge emit `design:targets`; list became 4, still correct, and Move Earlier worked (rev 1). With 120 added siblings (bulk >100) the list refilled to 123 with 14 containers and Move Last worked. No page errors.
- **M4 fixed.** Alt+Left/Right/Shift+Left not prevented, no move; the sibling-list item still handles Alt+Right itself.
- **Helpers:** `selectedArrangement()` (5 call sites) and `detachSession()` (armNoBridge, watchPopup, popOutTarget) are exact replacements; `connectTargetApp` correctly keeps its own variant (it sets `live.url`/origin and does not clear `targets`). No behaviour change; full suite green.

### Issues (new, in the M2 fix)

**Important**

- **R1. The Reapply reset-then-update is not transactional: a failed/rejected/aborted update leaves saved overrides empty, and auto-sync then PUTs an empty overrides file.** `reapplyStudioOverrides` (`html:~3593-3600`, `enqueueLiveOp({kind:"reset"})` then the update) plus the reset applied handler (`html:~3440`: `delete live.overrides[op.targetId]; syncOrderFromLedger(...)`), and `afterApplied` -> `scheduleAutoSync()` (`html:~3516`). The reset ack wipes Studio's saved entry for the target before the update has been acknowledged. Verified with the fake target (auto-sync on; `card.c` had css-order + fontSize 21; import JSON with only `fontSize` for it -> banner; set `fake.rejectNext`; Reapply): result `export()` has **no `live` at all**, banner gone, the target kept `font-size 14px`, and exactly one PUT whose body is `/* No live style overrides yet. */` (silent overwrite of the user's synced file). The success path is fine: same scenario without rejection ended with `{"card.c":{"fontSize":21}}`, one PUT carrying the right rule, and the real-bridge runs showed one PUT with the final content, so the 400 ms timer is re-armed by the update ack in the normal case. Other triggers of the same loss: a request timeout, a target reload between the two acks (no banner afterwards because both sides are empty), or an update reply slower than 400 ms. Fix: tag reset ops created by Reapply (`op.reapply = true`) and skip the `live.overrides` deletion and `syncOrderFromLedger` for them (Studio's saved state must not change until its own update acknowledges); additionally have `scheduleAutoSync` defer while `live.inFlight || live.queue.length`. Add a test with `fake.rejectNext` on the post-reset update asserting saved overrides and the PUT body are unchanged.

**Minor**

- **R2. Reset side effects (real bridge, `.actions` group of `landing.hero.cta`).** Text override: restored (saved text is re-sent; probed `Edited CTA` survives). The target's own **DOM move is silently undone**: DOM-move cta Last, css-order First, import JSON without `order`, Reapply: DOM went back to the original order and the HTML tab lost its structure block, while the banner never mentions structure (Rule 6 wording: preview-only state reverted without a stated choice). Narrow trigger (DOM move + stale order on the same target); fix by stating it in the banner text/status when the target ledger has `structure`, or by skipping the reset when the container has `structure` entries.
- **R3. Reset clears the whole css-order group, but replay is skipped for a group whose saved members already match the target.** Saved `{sibling:{order:0}}` (target already `0`) plus stale `cta`, Reapply: after the reset the sibling's saved order is deleted by `syncOrderFromLedger` and `reapplyOrders` skips the group (`list.every(... === ...)` uses the pre-reset `targetState`), so Studio's saved order and the preview both lose it (verified: saved after = only cta fontSize/text; target orders `0,0`). Only reachable from partial/hand-edited groups (the bridge writes order for every sibling), but it is silent loss of a saved value. Fix: when a reset is queued for a group, always replay that group's saved orders (drop the `every` early-return for reset groups).

No reset side effects found on other targets' text or on other containers' DOM order.

### Verdict

I1, M1, M4 and the helper extractions are verified fixed with the real bridge and the full suite (179 OK). The M2 fix is functionally right on the success path but is not safe on the failure path (R1 reaches an auto-sync PUT with empty overrides), which is a Rule 6 silent-overwrite.

**Task quality:** Approved with fixes (R1 must be fixed before commit; R2/R3 Minor)

---

## Re-review after second changes (scoped, read-only)

HTML sha256 `7361ec8a...` confirmed. **Gates:** `python3 -m unittest discover -s tests -v` with the FKS env vars: **Ran 182 tests, OK** (278 s, Chromium only, D010); `verify.py --static-only`: PASS (86 unique IDs, JS syntax, sha `7361ec8a...`, provenance x3). Probes `reviewF-s1..s3.py` (fake target) and `r1/r2/r3` (real committed bridge) in scratch.

- **R1 fixed (transactional Reapply), fake target with auto-sync on.** Scenario: `card.c` saved `{fontSize:21}`, target holds a stale css-order from a live move, import then Reapply.
  - *Rejection (`fake.rejectNext`)*: saved overrides stay `{"card.c":{"fontSize":21}}`; banner stays open and starts with "Reapply stopped (the target rejected it: unsupported-value). Studio's saved overrides were kept and nothing was written to the overrides file. ... press Reapply again."; the same text is in the code status; **0 PUTs**, also 0 after another second. Retry: succeeded, banner hidden, target `font-size 21px`, exactly 1 PUT carrying the saved rule.
  - *Timeout (replies held)*: during the 8 s wait banner visible and 0 PUTs; after the timeout "Reapply stopped (no response from the target)", saved intact, 0 PUTs; releasing the hold and pressing Reapply again succeeded with 1 PUT.
  - *Reload mid-Reapply*: saved intact, banner returns after the reload (conflict recomputed from unchanged saved state), 0 PUTs; retry succeeded with 1 PUT.
  - *Auto-sync never fires mid-sequence*: in every success run (fake and real bridge) there was exactly one PUT, sent after the last acknowledgement; `scheduleAutoSync` returns while `live.conflict` is open or ops are in flight/queued, and `finishReapply` re-arms it.
  - Reapply steps are tagged and pushed without merging (`enqueueLiveOp`), and the Reapply reset ack no longer touches `live.overrides` (`recordCanonical`).
- **R1, real bridge success path.** `landing.hero.cta` (text + font size + css-order saved, target css-order stale), Reapply: one PUT with `font-size: 21px` only, saved overrides equal the pre-Reapply Studio state, text survived, banner hidden, no page errors.
- **R2 verified.** The banner states, *before* the click, "Reapply will also reset the arrangement of one sibling group (a leftover CSS order can only be cleared that way)", and, when the ledger has structure for that container, adds ", which also undoes the DOM moves in them (see the HTML tab's structure blocks)" (real bridge, DOM move then css-order case). After Reapply the target's DOM and orders equal Studio's saved state (DOM back to original, orders cleared, saved = fontSize/text only), banner hidden, 1 PUT. At most one reset per sibling group (`staleOrderResets`).
- **R3 verified (real bridge).** Saved only the sibling's `order:0` (cta stale): after Reapply the sibling's order is replayed (target orders `1,0`, sibling first), saved overrides now hold orders for both siblings (the bridge assigns order to every sibling), and the one PUT carries `order: 1` for cta. No saved value lost.
- **Regression re-check with the real bridge:** I1 (Fraunces link and computed `font-family` return after Reapply), M1 (list fills on select; after `design:targets` it stays correct; with 120 added siblings it refills to 123 and Move Last works), M4 (Alt+Left/Right/Shift+Left not default-prevented and no move; Alt+Up/Down prevented and moves once; sibling-list item still handles its own Alt+Right).

**New issues:** none Critical or Important. Minor, informational only: the "Target reconnected." prefix still shows ahead of the "Reapply stopped" text after a timeout (cosmetic), and a successful retry of a partially replayed run may re-send steps the target already applied (idempotent by construction, no effect observed).

### Verdict

R1, R2 and R3 are fixed and verified on failure and success paths; I1/M1/M4 hold with the real bridge; the full suite (182) and static gate pass.

**Task quality:** Approved
