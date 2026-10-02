# v0.2.0 Task B review: bridge runtime protocol hardening and change ledger

Reviewer: independent, read-only (Task B). Task B changes uncommitted. The scope is `git diff -- fontkit-bridge.js`, `tests/test_bridge_runtime.py`, `tests/fixtures/bridge/**` and `docs/implementation/tasks/v02-task-b-report.md`. I checked them against the plan's "Protocol contract" and "Task B", plus Spec §2, §4, §7–10, §15 and §16. Addenda 1/2, Task C's own quality, and `docs/assets/**` are out of scope.


## Commands and results

- `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server -v`: **Ran 42 tests in 23.4s, OK** (24 bridge tests, 18 server tests).
- `node --check fontkit-bridge.js`: exit 0.
- Scratch probes (Chromium, `route_virtual_origins`), kept outside the repo:
  - `reviewB-smoke.py`: real Studio and the real bridge on the demo, across two origins.
  - `reviewB-security.py`: pre-hello passivity, SVG injection, `allowedOrigins` option paths, value-injection attempts, rejection order, re-hello pile-up.

### Spec Compliance

| Item | Status | Evidence |
|---|---|---|
| `protocolVersion: 1` required on every inbound message; outbound stamped with `protocolVersion` and `sessionId` | ✅ | `fontkit-bridge.js:479`, `:465-473` |
| hello only from parent/opener | ✅ | `:448-452`, `:521` |
| `allowedOrigins` restricts hello | ⚠️ | The `data-allowed-origins` path works (`:215-227`; test plus probe). The constructor option is defeated by auto-init (Important #2). |
| hello pins source, origin and session; re-hello from the same source replaces the session; other control messages must match all three | ✅ | `:458-463`, `:520-533`, `:485` |
| Posts go to the pinned origin (`*` only when the origin is `"null"`); `bridge-ready` goes to parent/opener with `*` and carries no page data | ✅ | `:469`, `:441-446` |
| Before hello: no DOM writes, no click interception, no hover/selection | ✅ | Listeners are inert (`:286-300`, `:1308-1310`). Discovery, observers and overlay start only in `activate()` (`:303-320`). Probe: 0 auto attributes and no overlay before hello. |
| Targeted patch table: all 9 keys, ranges, rounding, weight snapping, colour/family rules | ✅ | `:95-164`. `CSS.supports` adds extra strictness (`:81-84`, `:103`, `:142`). |
| Rejection reasons and details: `unsupported-property {property}`, `unsupported-value {property, requested}`, `unknown-target`, `revision-conflict {baseRevision, revision}`, `invalid-message` | ✅ | `:546-579`, `:606-651` |
| Order: invalid-message → revision-conflict → unknown-target → unsupported-property (all keys first) → unsupported-value | ✅ | The contract leaves the order open. Probe: `{fontSize:'x', bogus:1}` gives `unsupported-property bogus`; unknown target plus a stale revision gives `revision-conflict`. |
| Atomicity; +1 revision per successful update/reset/restore; `null` restores the original inline value or text | ✅ | Validation completes before any write (`:629-651`); `:582-583`; `:783-804`, `:856-866` |
| select / mode / reset / restore-text / highlight-as-select | ✅ | `:1353-1401`, `:714-748`, `:1368-1375` |
| hover (rAF-throttled, only on logical change), selected, bounds (rAF, ResizeObserver, scroll/resize), targets (debounced 120 ms with a 1 s max wait) | ✅ | `:1312-1341`, `:1403-1423`, `:1141-1153` |
| ChangeLedger shape, order by first change, `declarations` without `!important`, `text` only when changed, cleaned `html` | ✅ | `:891-962`. Smoke: `56px` and `0.1em` arrive verbatim. |
| Selectors: author `[data-design-id="…"]` with escaping; auto `#id` or a ≤4-step `tag.class:nth-of-type` path | ✅ | `:966-992` |
| Originals captured once (WeakMap) | ✅ | `:755-767`, `:826-839`; the RED test reproduced the old re-capture |
| Overlays off by default; Studio draws them (Spec §2.4) | ✅ | `:236`, `:330-331` |
| Legacy composition / `fontkit:change` session-gated and recorded in the ledger | ⚠️ | It works (`:670-708`, `:1438-1446`), but the legacy SVG placement is a script-injection sink (Critical #1) and does not work for base64 data URLs (Important #3). |
| Tests use two distinct fake origins | ✅ | `tests/test_bridge_runtime.py:50-61`, `tests/fixtures/bridge/host.html` |

### Strengths

- The contract is implemented closely. Every rejection path has a dedicated test (27 cases plus conflict and invalid-message variants) that also asserts nothing changed and the revision stayed put.
- Original-state handling is careful. There is one inline-style snapshot per element, the author's style attribute text is restored exactly, and a leaf's original child nodes are re-attached rather than re-serialised. The Chromium lazy style-attribute quirk is handled and commented (`:797-804`).
- Pre-hello passivity is complete. Discovery, observers and the bridge's own attributes all wait for the first hello. Probe confirmed: 0 auto attributes and no overlay before hello.
- No HTML sinks on the targeted path:
  - `text` uses `textContent` or `Text.data` only (`:845`, `:850`). In the smoke test, `Hello <b>x</b>` rendered as escaped text and was escaped again in the ledger html.
  - `cssText` is only ever assigned constant strings.
  - Every patched value goes through `style.setProperty` after `CSS.supports`.
- No feedback loops:
  - The MutationObserver watches `childList` only, while bridge attribute and style writes don't touch `childList`.
  - Overlay nodes are filtered out.
  - `design:targets` is sent only when the set of ids changes.
- No pile-up: listeners are installed once in `init()` and `activate()` is idempotent. Probe: after 5 re-hellos, one `design:select` produced exactly one `design:selected`.
- The report is honest and detailed, with RED evidence for all four confirmed defects and a clear list of interpretations.

### Issues

#### Critical

1. **Legacy SVG placement runs script in the target origin, and by default any framing origin can trigger it.** `fontkit-bridge.js:1646-1660`
   - **Scenario (verified, `reviewB-security.py`):**
     - A page on `http://evil.test` frames the target. With the default config (no `allowedOrigins`) it says hello, gets `design:ready` with 14 targets, and becomes the pinned Studio.
     - It sends a composition `design:update` with `slots:[{type:'image', targetId:'landing.mark', assetDataUrl:'data:image/svg+xml,<url-encoded svg>'}]`.
     - `DOMParser` plus `importNode` plus `replaceWith` inserts the markup live into the target document, and the page then runs it. Each of these executed with `document.domain === 'target.test'`:
       - `<svg><script>…</script></svg>`
       - `<svg><image href=x onerror=…>`
       - `<foreignObject><img onerror=…>`
     - (`<svg onload>` did not fire.)
   - **Impact:** this goes beyond the contract's "any origin may restyle" default. It is full script execution in the dev app's origin: cookies, storage, authenticated API calls. Any site the developer visits can trigger it while the dev server is running, because dev servers rarely send `X-Frame-Options`. A legitimate Studio user who uploads an untrusted SVG triggers it too.
   - **History:** the sink predates Task B (old `fontkit-bridge.js:746-747` at HEAD). Task B kept it on the session-gated legacy path.
   - **Fix:** never adopt parsed SVG markup into the live DOM. Replace the inline `<svg>` with an `<img src="data:image/svg+xml…">`; SVG loaded as an image cannot run script. Carry over `data-design-id` and the record mapping, as is already done. Only `data:image/png` and `data:image/svg+xml` URLs should be accepted for `img`/container placement.
   - **Test:** add a regression test in `LegacyCompositionTests` that sends a payload with `<script>` and `onerror` and asserts no marker global is set.

#### Important

2. **The `allowedOrigins` constructor option is silently ineffective.** `fontkit-bridge.js:1697-1714` and `:242`
   - Auto-init always runs (at DOMContentLoaded when the script sits at the end of `<body>`). A page that writes `new FontKitBridge({allowedOrigins:['http://studio.test']})` therefore also gets an unrestricted global instance.
   - **Verified:** `evil.test` received `design:ready` from the auto instance. `window.__mine !== window.__fontkitBridge`, and the auto instance has `allowedOrigins === null`.
   - Calling `initFontKitBridge({allowedOrigins})` after auto-init returns the existing unrestricted instance and ignores the options. Verified: evil hello → `design:ready`, `__allowed === null`.
   - The only opt-out is the undocumented `window.__fontkitBridge = 'manual'` hack that the overlay fixture uses.
   - **Fix:**
     - Support an explicit opt-out on the script tag (e.g. `data-auto-init="false"`) and document it in the header.
     - Have the constructor claim `global.__fontkitBridge` when it is unset, so a later auto-init becomes a no-op.
     - Make `initFontKitBridge(options)` `console.error` (or throw) when called with options after an instance already exists.
   - **Test:** add one for the option path from a hostile parent.

3. **Inline-SVG replacement does nothing for what Studio actually sends, and changes layout instead.** `fontkit-bridge.js:1646-1648`
   - Studio reads uploads with `FileReader.readAsDataURL` (`font_kit_studio_v0.1.1.html:2664`), which produces `data:image/svg+xml;base64,…`. The bridge runs `decodeURIComponent` on the base64 text, so parsing fails, and execution falls through to the container branch.
   - That branch appends an `<img>` inside the `<svg>` (not rendered) and forces `display:flex !important; align-items; justify-content` on the `<svg>`.
   - **Verified:** `base64 svg -> applied, replaced? False`. The mark's style became `… display: flex !important; align-items: center !important; justify-content: center !important;`.
   - This predates Task B. The fix for #1 (swap in an `<img>` with the data URL) fixes this as well.

#### Minor

4. **Legacy token values are unvalidated** (`fontkit-bridge.js:812-817`). Any value that `setProperty` accepts for a custom property gets in. Verified: `--evil: url(https://evil.test/beacon)` was accepted and reported in `changes.tokens`. Studio's `safeCssText` does not block `url(`, so Sync would write it into `overrides.css`. Fix: reject `url(`, `expression(`, `<`, `>` and `\` in token values, as for `fontFamily`.
5. **Clicks stay intercepted after an opener Studio closes** (`fontkit-bridge.js:1308-1310`). When the Studio is `window.opener` and is closed, `studioSource` is dead but select mode keeps preventing clicks on targets. Fix: in `isSelecting()`, treat `studioSource.closed` as disconnected. This matters for the wave-2 pop-out.
6. **Double discovery on first hello** (`fontkit-bridge.js:533-534`). `activate()` already calls `discoverTargets()`. Harmless, but it is a second full querySelectorAll pass.
7. **Reset does not undo the legacy layout reorder** (`fontkit-bridge.js:1492-1497`). `main` children physically re-appended by the legacy layout code stay reordered after `design:reset`. This is acknowledged in the report and deferred to Task E. Studio should not claim that reset fully reverts an explicit composition sync.
8. **Unanchored auto selectors can be ambiguous on deep DOMs** (`fontkit-bridge.js:966-982`). With no id ancestor within 4 steps, a path like `div:nth-of-type(1) > p:nth-of-type(2)` can match several elements. The contract allows this and Studio annotates auto selectors; a uniqueness check plus a comment in the CSS would be cheap.
9. **`img`/container placement accepts any URL scheme** (`fontkit-bridge.js:1638`, `:1687`). Not a script vector, but it allows arbitrary remote loads. Restrict to `data:image/(png|svg+xml)`.

### Cross-task compatibility (B↔C)

Message-level match: no blocking mismatches. Studio (`font_kit_studio_v0.1.1.html`) against the bridge:

| Concern | Studio | Bridge | Result |
|---|---|---|---|
| `protocolVersion: 1` and `sessionId` on every control message | `:3028-3033` stamps every send | `:479`, `:485`, `:522` | ✅ |
| hello on `bridge-ready` and on iframe `load` | `:3270-3275`, `:3095-3102` | answers every hello | ✅ |
| update / composition / reset / restore-text fields (`requestId`, `baseRevision`, `targetId`, `patch`) | `:3134-3143` | `:606-748` | ✅ |
| `design:applied` fields: `requestId`, `revision`, `targetId` (`"global"` for composition/restore), `canonicalPatch`, `target`, `changes` | `:3179-3195`, `:3154-3176` | `:582-591`, `:667`, `:707`, `:731`, `:747` | ✅ |
| `design:rejected` `reason`; retry once on `revision-conflict` | `:3196-3204` | `:546-556` | ✅ |
| `hover` / `selected` / `bounds` / `targets` | `:3292-3316` | `:1331-1340`, `:1400`, `:1422`, `:1149` | ✅ |
| Rect is in the target's viewport CSS px; Studio places the overlay at frame offset plus rect | `:3324-3335` | `:187-190` | ✅ (smoke: overlay at 60,209.77 = frame 40,−12.11 + rect 20,221.88; same width and height) |
| Ledger value formats (`56px`, `0.1em`, lowercase hex) to `ledgerToOverrides` via `parseFloat` | `:2979-2992` | `:111`, `:133`, `:778` | ✅ |
| Mode reset on hello; Studio re-sends a non-default mode on ready | `:3285` | `:529` | ✅ |
| `design:select-slot` removed | not in `BRIDGE_TYPES` (`:2854`) | no longer sent | ✅ (README `:129`, `:142` still documents it; Task D) |

Minor mismatches (non-blocking; most belong to C or D):

- **a. Text canonical vs ledger text.**
  - Bridge: `canonicalPatch.text` is the raw string (`fontkit-bridge.js:161`), but ledger `text` is trimmed and omitted when it equals the original (`fontkit-bridge.js:874-885`, `:931`).
  - Studio: stores the raw canonical text in `live.overrides` (`font_kit_studio_v0.1.1.html:3157-3163`) and compares it with `ledgerToOverrides` (`:2989`, `:3216`, `:3233-3241`).
  - **Effect:** text with leading or trailing whitespace, or text typed back to the original, makes `overridesEqual` false. That gives a spurious reconnect banner, and `reapplyStudioOverrides` re-sends the text each time.
  - **Fix (Studio side):** trim before comparing, and drop `text` entries equal to the ledger or manifest original.
- **b. Pruned targets linger in Studio.** The bridge prunes disconnected targets and sends the full list in `design:targets` (`fontkit-bridge.js:1110-1115`, `:1149`). Studio only merges (`font_kit_studio_v0.1.1.html:3310-3314`), so removed targets stay in its list. Fix in C: replace the map.
- **c. Import accepts values the bridge rejects.** Studio's `canonicalLiveValue` (`font_kit_studio_v0.1.1.html:2890-2909`) has no `CSS.supports` check, while the bridge has one (`fontkit-bridge.js:103`, `:142`). An imported `live` value like `color: "rgb()"` passes import but is rejected on reapply as `Rejected: unsupported-value`. That is acceptable, but C could mirror the check.
- **d. Composition ops skip auto-sync.** Declarations from a composition sync (e.g. `margin-top`, `width`, `border-*`) show up in the CSS panel, but Studio does not schedule an auto-sync for composition ops (`font_kit_studio_v0.1.1.html:3195`). That's consistent with "explicit sync"; just noting it.

**Smoke result (`reviewB-smoke.py`, Chromium):**
- Setup: `http://studio.test/font_kit_studio_v0.1.1.html?target=http://target.test/demo/`.
- Badge: `Connected (34 targets)`.
- Clicking `[data-design-id="landing.hero.title"]` in the iframe opened the inspector "Hero title", seeded with size `64.56`.
- Setting `#liveFontSize` to 56 made the iframe's computed font-size `56px`.
- `#liveCodeOutput` showed `/* Hero title (landing.hero.title) */ [data-design-id="landing.hero.title"] { font-size: 56px !important; }`.
- Adding tracking 0.1, colour `#FF0000` and text `Hello <b>x</b>`:
  - CSS showed `letter-spacing: 0.1em !important; color: #ff0000 !important;`.
  - The iframe text was escaped (`Hello &lt;b&gt;x&lt;/b&gt;`).
  - The HTML tab showed cleaned `<h1 id="hero-title" data-design-id=… >Hello &lt;b&gt;x&lt;/b&gt;</h1>`.
  - The JSON tab showed canonical overrides; the badge read `Live · rev 8`.
- `#liveResetTarget` brought back the original `<h1>` with no `style` attribute; CSS reverted to "No live style overrides yet."
- The only console errors were two expected 404s (`/__fontkit/status` and `fontkit-overrides.css` aren't served by the virtual router).
- **PASS.**

### Contract-reading opinions (report §"Contract interpretation notes")

1. **Revision starts at 0, is unchanged by hello, and persists across sessions.** Agree. Studio's reconnect reconciliation depends on the ledger in `design:ready`.
2. **`protocolVersion` required on everything, including legacy messages.** Agree (the contract says "all messages"). Studio stamps every send, so nothing is lost.
3. **Pin to the first window until reload; hello resets mode and selection; empty `allowedOrigins` denies; `*` allows any.** Agree for wave 1. The wave-2 pop-out will need a defined re-pin path when the controlling window changes. See also Minor #5.
4. **Rejection precedence.** Reasonable and tested. Rejecting a numeric `requestId` matches Spec §9.1 (`requestId: string`).
5. **An empty patch `{}` is a successful no-op that increments the revision.** Acceptable and consistent with "each successful update +1". Studio never sends one.
6. **Legacy composition `requestId` required, `baseRevision` optional; restore-text fields optional.** Agree. Studio sends both anyway.
7. **Editable flags gate keys (including `null`); image kind by tag or `data-design-kind`; text editable only for a leaf or an element with a direct text node.** Agree. Dropping the `id.includes('mark')` heuristic fixes `landing.brand.wordmark`. Gating `null` is defensible because a non-editable key can never have been set.
8. **Stricter validation with `CSS.supports`.** Agree; it prevents "accepted but not applied". Note that `fontFamily: "var(--x)"` is still accepted (harmless). See mismatch (c) for keeping Studio's import in step.
9. **Weight ties resolve to the lower weight.** Fine. Spec §5.4 doesn't specify ties.
10. **Ledger/manifest text trimmed; mixed-content keeps the surrounding whitespace.** Fine for the bridge, but it causes mismatch (a). Either Studio trims, or the contract should state that ledger `text` is trimmed.
11. **Originals captured right before the first touch; exact restore.** Agree; this is the best reading of "captured once".
12. **Auto selector ≤4 entries, classes plus `:nth-of-type` always.** Within the contract. See Minor #8 on uniqueness.
13. **Unknown `design:select` clears the selection; bounds continue in interact mode; switching to interact sends a final `hover null`.** Agree.
14. **`design:targets` carries the full list on any change in ids, 120 ms trailing debounce, 1 s max wait.** Agree. Studio should replace its map rather than merge (b).
15. **Fully passive before hello.** Agree; verified.
16. **Legacy wireframe styles are bridge-owned but kept out of the ledger.** Agree. The DOM reorder, though, is neither recorded nor undone (Minor #7).
17. **`design:select-slot` dropped; `inspect-result` shape changed.** Agree; there are no consumers. The README still documents `select-slot` (Task D).
18. **Duplicate author ids: first wins, warn once.** Agree with Spec §4.1.

### Assessment

The targeted protocol path is correct, well tested and compatible with Task C's client:
- session/origin gating;
- validation and atomicity;
- revisions;
- change ledger;
- cleaned HTML;
- hover/selection/bounds.

The real cross-origin smoke run passes end to end. Two security problems block approval:
- The legacy SVG placement path inherited from the prototype inserts attacker-controlled SVG markup into the live document. That is script execution in the target origin, and with the default `allowedOrigins` any framing site can trigger it (Critical #1).
- The `allowedOrigins` constructor and `initFontKitBridge` option paths are silently overridden by auto-init (Important #2).

Both fixes are small and local: swap in an `<img>` for SVG placement, and add an auto-init opt-out with instance claiming. Each needs a failing behaviour test first, per AGENTS.md.

**Task quality:** Changes required

## Re-review after first changes

Scope: the "Changes after first review" section of `v02-task-b-report.md`, plus `git diff -- fontkit-bridge.js tests/test_bridge_runtime.py tests/fixtures/bridge` (still uncommitted). Read-only.

### Commands and results
- `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server -v`: **Ran 51 tests in 42.8s, OK** (33 bridge, 18 server).
- `node --check fontkit-bridge.js`: exit 0.
- `grep -n "DOMParser|importNode|replaceWith|innerHTML|insertAdjacentHTML|outerHTML =" fontkit-bridge.js`: no matches. No HTML-parsing sink remains, and `cssText` is only assigned constant strings (`:1785`).
- Scratch probes: `reviewB-security2.py` (SVG payloads, URL acceptance, reset, tokens, init paths, closed opener), `reviewB-reset.py` (per-target reset) and `reviewB-smoke.py` (B↔C).

### Item-by-item verification

| Review item | Status | Evidence |
|---|---|---|
| Critical 1: SVG script injection | ✅ Fixed | See [SVG payloads](#svg-payloads) below. |
| Important 3: base64 SVG / layout breakage | ✅ Fixed | `readAsDataURL`-style base64 SVG renders as an `<img>`. The original `<svg>` is `display:none !important` (bridge-owned, not in the ledger) and is no longer forced to `flex`. Test `test_base64_svg_from_read_as_data_url_replaces_an_inline_svg_until_reset`. |
| Minor 9: URL schemes | ✅ Fixed | `safeAssetUrl` (`:117-126`). See [URL acceptance](#url-acceptance) below. |
| Reset restores everything placement touches | ✅ | See [Reset after placement](#reset-after-placement) below. |
| Important 2: init options | ✅ Fixed for the documented paths | See [Init paths](#init-paths) below. |
| Minor 4: legacy tokens | ✅ Fixed | See [Token validation](#token-validation) below. |
| Minor 5: closed opener | ✅ Fixed | See [Closed opener](#closed-opener) below. |
| Minor 6: single discovery | ✅ Fixed | `:603-605`: `activate()` on the first hello, `discoverTargets()` on later ones. Test `test_first_hello_discovers_targets_once` wraps `discoverTargets` and counts 1, then 2. |
| Minors 7 and 8 | Deferred to Task E as agreed | Unchanged. See note R3 under Remaining notes. |

#### SVG payloads

The hostile parent at `evil.test` used the default config, so hello was still accepted, as the contract allows. Each payload went in twice against `landing.mark`, once URL-encoded and once as base64. Nothing executed: the `window.__x` marker stayed `null`.

Payloads tried:
- `<svg onload>`
- `<svg><script>`
- `<image onerror>`
- `<foreignObject><img onerror>`
- `<a href="javascript:">`
- `<use href="data:…#x">`
- `<animate onbegin>`
- `<set attributeName="href" to="javascript:">`

What the page ended up with:
- No `script`, `foreignObject` or `a[href^=javascript]` nodes were inserted.
- The only change is one `img.fontkit-placed-asset` with the SVG data URL as its `src`.
- I also clicked the placed image in interact mode: nothing ran.

The new test `test_svg_payloads_never_execute_in_the_target` covers the three original payloads on the svg, container and img targets.

#### URL acceptance

Accepted on both the container target (`landing.slot`) and the `<img>` target (`landing.photo`):
- `data:image/png;base64,…`
- `data:image/svg+xml,…` (URL-encoded)
- `data:image/svg+xml;charset=utf-8;base64,…`

Ignored: nothing is placed and the photo `src` is unchanged:
- `https:`
- `javascript:`
- `blob:`
- `data:image/jpeg`
- `data:text/html`
- `data:image/png,` without base64
- PNG with invalid base64
- uppercase `DATA:`
- an SVG declared `;base64` whose body is not valid base64

#### Reset after placement

- **Reset-all:** placing on `landing.photo`, `landing.slot` and `landing.mark`, then a global `design:reset`, brings back a byte-identical snapshot (outerHTML of all three, parent child counts, 0 placed images).
  - The `<img>` `src` attribute is restored through `setAttr`/`restoreAttrs` (`:957-977`); `srcset` too, when present.
  - Placed `<img>` nodes are removed and the svg's `display` override is cleared.
- **Per-target reset:** this also restores the target exactly. I checked the img `src` and styles, the container's flex styles and its child `<img>`, and the svg's `display` and its sibling `<img>`.
  - One residue remains: the legacy wireframe `transition` and `order` styles. A composition update writes them onto **every** `main` child, and a per-target reset clears only that target, so siblings keep them.
  - This is the already-deferred legacy layout behaviour (Minor 7), not something placement leaves behind.

#### Init paths

From a hostile `evil.test` parent:

| Setup | Result | Instance check |
|---|---|---|
| Fixture `data-auto-init="false"` with `initFontKitBridge({allowedOrigins})` | evil times out; `studio.test` gets `design:ready` | — |
| Fixture `window.FONTKIT_BRIDGE_OPTIONS` | evil times out; `studio.test` gets `design:ready` | — |
| Fixture `new FontKitBridge({allowedOrigins})` after the script tag | evil times out; `studio.test` gets `design:ready` | the constructed instance is `window.__fontkitBridge` |
| My earlier inline-construct page | evil times out | — |
| `defer` script with inline `FONTKIT_BRIDGE_OPTIONS` beforehand | evil times out | — |
| `defer` with `data-auto-init="false"` and a manual init | evil times out | — |
| `initFontKitBridge({allowedOrigins})` after auto-init | still connects | logs `initFontKitBridge(): a bridge already exists, options ignored…`, as documented |

#### Token validation

- Names must match `/^--[a-z0-9-]+$/` (`:81`). Values go through `safeCssString` (`:107-113`).
- Rejected (canonical patch and ledger contain only the accepted ones):
  - `--font-display: x; } body {…`
  - `--evil: url(…)`
  - `--Upper`
  - `--exp: expression(1)`
  - `--bs` containing a backslash
  - `--lt: <b>`
  - the `display: url(x)` shortcut
- Accepted: `--ok: "  Georgia, serif  "`, stored trimmed as `Georgia, serif`.
- `fontkit:change` with `sans: url(x)` is ignored, while `mono: Courier` is applied.

#### Closed opener

`studioAlive()` / `dropSession()` (`:511-529`) are checked in `isSelecting`, `post` and `handleHello`.

Probe on a pop-out target:
- While the opener Studio is alive, a CTA click is intercepted (`location.hash` stays `''`).
- After `page.close()` of the opener, the same click navigates to `#clicked`.

Test `test_closed_opener_studio_stops_click_interception`.

### Remaining notes (non-blocking)

- **R1 (Minor): construct-after-auto-init with `defer`/`async` still leaves an open instance.** `fontkit-bridge.js:325-328` and `:1826-1836`.
  - **Scenario (verified):** `<script defer src="fontkit-bridge.js">` followed by a deferred `new FontKitBridge({allowedOrigins:['http://studio.test']})`.
    - Deferred scripts run while `readyState === 'interactive'`, so auto-init has already run synchronously.
    - The constructor warns: "Another bridge instance already exists; both will answer the Studio."
    - The open auto instance still answers `evil.test` with `design:ready`.
  - The documented paths (`data-auto-init="false"` or `FONTKIT_BRIDGE_OPTIONS`) are safe, and the case is warned and documented, so this is no longer Important.
  - **Optional hardening:** when the existing global instance was auto-created and is still unpinned, have the constructor take its place, e.g. a `dispose()` that removes its listeners and observers.
- **R2 (Minor, perf): large data URLs travel in every reply.**
  - When an `<img>` target holds a placed asset, the target becomes dirty (`width` and `opacity` are ledger declarations). Its ledger `html` then carries the full data URL in every `design:applied` and `design:ready`.
  - Probe: a 200 KB asset produced a 200,100-character `html` entry. The cap is 8 MiB per asset (`:58`).
  - **Possible fix:** abbreviate `data:` URLs in ledger `html` (e.g. `src="data:image/png;base64,…(N bytes)"`), or mark placement width and opacity `ledger:false`. This is legacy composition only, so it can wait for Task E.
- **R3 (Minor, already deferred as Minor 7): every composition update restyles all `main` children.** Any composition update, including one with a single image slot, writes `transition`/`order` onto every `main` child and may reorder them. A per-target reset leaves those sibling styles, and no reset undoes the reorder. This stays with Task E.

### B↔C smoke (re-run)

`reviewB-smoke.py` against the current concurrent Studio: **PASS**, identical to round 0.
- Badge: `Connected (34 targets)`.
- Clicking the hero title in the iframe then setting `#liveFontSize` to 56 gave a computed `56px`, and the CSS panel showed `[data-design-id="landing.hero.title"] { font-size: 56px !important; }`.
- Tracking and colour came through as `0.1em` and `#ff0000`.
- The text edit was escaped in both the iframe and the HTML tab. The JSON tab was correct and the badge read `Live · rev 8`.
- The overlay lined up as frame offset + rect, and reset restored the original `<h1>`.
- No new protocol mismatches. The round-0 Studio-side notes (a)–(d) belong to Task C.

### Assessment (changes after first review)

All Critical and Important findings are fixed, each with a behaviour test that was RED first, and every requested variant was checked at runtime:
- the SVG script-injection sink is gone, and assets render only through `<img>`;
- only PNG/SVG data URLs are accepted;
- placement is fully restored by reset;
- the documented init-option paths are enforced, and option misuse is warned;
- tokens are validated;
- a closed opener unpins the session;
- discovery runs once per hello.

What remains are three Minor notes (R1–R3); none blocks the commit.

**Task quality:** Approved
