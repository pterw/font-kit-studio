# Sweep report: v0.2.0 batch

Scope: read-only sweep. Date: 2026-10-02. The v0.2 branch after the Task F change, plus the then-uncommitted Task D files (README, demo newsletter form, `tests/test_live_integration.py`, roadmap, screenshots, `v02-task-d-*.md`).
Method: direct source reading, grep, and one Playwright probe against the real server, Studio, bridge and demo (Chromium only, `FKS_ENGINES=chromium`, `/opt/pw-browsers/chromium`). Firefox was not run. The probe server was started with `--no-sync` on free ports and stopped afterwards. No repo file was changed except this report.

Gate results (run during the sweep): `python3 scripts/verify.py --static-only` PASS (86 unique static IDs, 1 inline JS block, 3 provenance hashes); `node --check fontkit-bridge.js` PASS; `git diff --check` clean. The full unittest suite was not run in the sweep (see `verification-v0.2.md`).

## Must fix before release

**M1. Two bridge message handlers have no sender and no test (anti-pattern 8).**
- `fontkit-bridge.js:804-809` handles `design:inspect` (`handleInspect`, line 2673) and `design:ping` (replies `design:pong`). `README.md:415-416` and `:432` document them.
- Evidence: Studio never sends either (`grep "design:inspect\|design:ping" font_kit_studio_v0.1.1.html` is empty), and no file under `tests/` sends them (`grep -rn "design:inspect\|design:ping\|design:pong\|inspect-result" tests` is empty). The plan contract (Protocol contract and Addenda 1-3) does not list them either. `AGENTS.md` registry entry 8 says every message type needs a test that sends it.
- Fix, smallest first: delete the two `case` branches, `handleInspect`, and the README rows at 415, 416 and 432 (the `capabilities.inspect: true` flag in the contract can stay; it means "manifests are reported"). Or keep them and add one bridge test each that sends the message and asserts the reply fields (`found`, `rect`, `target` for inspect; `revision` for pong), plus a plan addendum that adds them to the contract. Deleting is cheaper and matches the contract.

**M2. README overstates what the tests ran (anti-pattern 14).**
- `README.md:263`: "The plain HTML recipe, the attributes, the options and the bookmarklet were run in tests against the real bridge."
- Evidence: the bookmarklet is tested (`tests/test_live_integration.py:599`). Of the options listed at README line 372, only `allowedOrigins` (via `FONTKIT_BRIDGE_OPTIONS`, `target-options.html`) and `enableHighlightOverlay` (`target-overlay.html`) have a test. I found no test for `autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied`, the `data-allowed-origins` script attribute (README line 358) or the `data-design-kind` attribute (README line 345). (`grep -n "autoDiscover\|enableClickToSelect\|onApplied\|data-allowed-origins\|data-design-kind" tests/*.py tests/fixtures/*/*` has no hit outside the README and the bridge.)
- Fix: either add one fixture-based test per untested option/attribute, or narrow the sentence (exact text under "Doc updates", item 1).

**M3. `docs/agents/global-rules.md` still says Tasks E and F are uncommitted.** Rules 4, 6 and 7 carry "target state ... until committed" caveats that are now false (Tasks E and F are committed), and Rule 7's caveat claims "the Studio still prefills the old kit ID", which is untrue (probe: `#composerKitIds` value is `""`, 0 typekit links, 16 free fonts). Agents read this file as binding, so a false "still prefills" line sends them looking for a defect that is gone. Exact replacement text under "Doc updates", item 2.

## Should fix

**S1. Studio and bridge disagree on custom-property names; the bridge drops silently.**
- Studio accepts `^--[A-Za-z0-9_-]{1,120}$` (`font_kit_studio_v0.1.1.html:3119`, `:3185`). The bridge accepts only `^--[a-z0-9-]+$` (`fontkit-bridge.js:121`, used at `:1605`).
- `handleCompositionUpdate` (`fontkit-bridge.js:1009-1018`) skips an invalid token without rejecting, so Studio gets `design:applied` for a patch that was only partly applied (the dropped name is missing from `canonicalPatch.tokens`). Reachable through `live.tokens` in an imported composition JSON followed by Reapply. Studio's own composition sync only sends `--font-sans/serif/mono/display`, so normal use is unaffected.
- I did not run the import-then-Reapply path, so whether it produces a persistent "differs" banner is unverified.
- Fix: make both sides use one rule (lowercase-only is simplest; change Studio's two regexes) and have the bridge reject a composition patch that contains an invalid token name (`unsupported-property`, `detail.property`), as targeted patches do. Add a test for each side.

**S2. Studio's "same allow-list as the bridge" font-stylesheet validator is not the same.**
- Comment at `font_kit_studio_v0.1.1.html:3145` says it matches the bridge. Differences: Studio allows at most 4 `family=` params (`:3155`), the bridge 8 (`fontkit-bridge.js:131`); Studio's `text=` pattern allows any `%XX` (`:3001`), the bridge only `%20 %2B %2C %3A %3B %40` (Addendum 3); Studio's `family` pattern lacks `~` and `%`, the bridge allows both.
- Impact is low (Studio only builds `family=...&display=swap` URLs; all 16 library URLs pass both validators, checked in the probe). A hostile or odd imported URL passes Studio and is then rejected by the bridge, which is handled.
- Fix: change the comment to "stricter than or equal to the bridge for the URLs Studio builds", or tighten Studio's `text` pattern to the Addendum 3 list.

**S3. Studio's CSS-text gate is weaker than the bridge's, and exists in three copies.**
- `font_kit_studio_v0.1.1.html:3060` (`/[;{}<>\\]|url\(/i`), `:3121` (adds newline and comment checks) and `safeCssText` at `:3138-3139` (`/[{};<>\n\r]|\/\*|\*\/|!important/i`, no `url(` and no backslash check). Rule 10 (rule of three) is reached on the Studio side.
- Real gap: token values from the target's ledger (`normalizeLedger`, `:3185`) are only checked by `safeCssText` before `liveCss()` writes `--name: value !important` into the synced overrides file (`:4454-4457`). A target that reports `--x: url(https://evil.example/a)` gets that line into the file. Custom properties do not fetch by themselves, so this is low severity, but it differs from the bridge's own `UNSAFE_CSS_STRING` (`fontkit-bridge.js:120`).
- Fix: one `unsafeCssText` helper in Studio with `/[;{}<>\\\n\r]|url\(|expression\(|\/\*|\*\/|!important/i`, used at all three places.

**S4. Spec departures that are not recorded in `deviations.md`.** `AGENTS.md` (Proposal and Design Rules 2) and registry entry 11 want departures recorded. D016 covers only three. Not recorded:
- Spec 6 `design:conflict` is implemented as `design:rejected` with `reason: "revision-conflict"` (plan contract; bridge `checkRevision`).
- Spec 7.4 `capabilities.assets` is not reported; the bridge reports `text` and `reset` instead (`fontkit-bridge.js:842`, plan contract).
- Spec 8 `kind` values `svg | container | component`, `editable.spacing/asset/visibility` and `constraints.fontFamilies` are not implemented (`kind` is `text | image`).
- Spec 10 `design:select-slot` was removed; selection is `design:select` / `design:selected`. Spec line 927 still describes the old message.
- Suggested entry: `| D022 | Ruling: protocol v1 follows the plan contract where it differs from the Spec: revision conflicts use design:rejected/revision-conflict; capabilities are {inspect, patch, typography, text, tokens, reset}; kind is text or image; design:select-slot is removed in favour of design:select/selected. | Plan contract and Addenda 1-3; README protocol tables. | A Spec-strict consumer would not recognise these messages; add aliases then. |`

**S5. The legacy composition path edits the target more than the README says.** Probe: connect to the demo, press **Sync to Live App** with the default preset. Result: all 6 `<main>` sections get an inline `transition: transform 0.3s ..., opacity 0.2s, order 0.25s` and the hero gets `order: 3` (in a flex or grid `main` that reorders the page). The CSS and HTML tabs show nothing ("No text changes yet"), so the user cannot see or export it. Cause: `applyWireframeMovement` (`fontkit-bridge.js:2699-2750`), required by Spec 8.3 and kept by the plan ("existing slot/token behaviour"), so this is contract-conformant, not a defect. The gap is disclosure: `README.md` (Library and Composer bullet, "Known gaps") does not mention it. Suggested README sentence is in "Doc updates", item 5. Owner decision: keep Spec 8.3 behaviour, or drop the `layout.order` handling from composition sync now that Arrange exists.

**S6. `localStorage` is read and written without try/catch, which kills Studio start-up when storage is blocked.**
- `font_kit_studio_v0.1.1.html:1579` (top-level script) and `:4846` (inside the Composer IIFE); writes at `:1571` and `:2150`. These lines come from v0.1.1, but v0.2's `?target=` auto-connect at `:4859` runs after line 4846, so it is skipped too.
- Probe: with `window.localStorage` getter throwing `SecurityError`, `pageerror` "denied" fires and 0 `.slot-text` elements render (the Library's 16 cards still render). Chrome with "block all cookies" and some embedded browsers behave this way.
- Fix: wrap each access in `try { ... } catch (_) {}`, with a small `readStore`/`writeStore` pair (four call sites). Add a test using the same init-script trick.

**S7. Dead payload fields in the composition message, which make the old slot heuristics the only live path.**
- `font_kit_studio_v0.1.1.html:4677` sends `targetId: slot.targetId`; slots never carry `targetId` (the only other use of that name for slots is this line), so the bridge's direct-id branch in `resolveElementForSlot` (`fontkit-bridge.js:2764-2770`) is unreachable from Studio and every composition slot is matched by the substring heuristics (`data-design-id*=...`, `h1, h2`, index fallback at `:2810-2818`). Also unused by the bridge: `familyRaw` (`:4679`), `layout.canvasWidth` and `layout.backgroundHex` (`:4696`).
- Fix: drop the unused fields; decide whether the heuristics stay (see S5). If they stay, add a comment in the bridge that they serve only the Composer sync.

**S8. Test hygiene.** `tests/test_preview_server.py:6` has an unused `import os` (only a comment mentions `os.replace`). `tests/test_studio_live.py:1178` defines `list_ids` and nothing calls it.

**S9. Version labels.** The UI says "Font Kit Studio v0.1.1" (`font_kit_studio_v0.1.1.html:6`, `:881`) while README and plan call the release v0.2.0. This is deliberate for the filename and JSON version (D009, and `tests/test_font_kit_studio_v011.py:527` asserts the title), but D009 does not mention the visible title. Either add "visible title and eyebrow stay v0.1.1" to D009 or bump both label and test.

## Doc updates

1. **`README.md:263`** replace the first sentence with:
   > **How these recipes were checked.** The plain HTML recipe, the `data-auto-init`, `FONTKIT_BRIDGE_OPTIONS` and `allowedOrigins` settings, the overlay option and the bookmarklet were run in tests against the real bridge. The other options (`autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied`), the `data-allowed-origins` script attribute and `data-design-kind` are implemented but have no test yet.

   (Keep the rest of the paragraph about Vite, Next.js and Astro.)

2. **`docs/agents/global-rules.md`** (agents' binding rules):
   - Rule 4, lines 59-62: replace with
     > - Hover and selection outlines live in Studio's overlay. The only exception is pop-out mode (and the page option `enableHighlightOverlay`), where the bridge draws a non-interactive outline that it removes on exit and strips from every export (D016).
   - Rule 6, lines 87-91 (the structural-edits bullet): replace with
     > - Structural edits (moving buttons, cards, form controls) are reversible and guarded: refuse or warn when a move would break form ownership, radio groups, label/aria references, content-model rules or framework-managed DOM. Offer CSS `order` where layout allows (it is the default for framework-managed parents). Structural moves go beyond Spec section 19 (D016).

     (Reason for the wording change: the old text says "prefer CSS order"; `moveStrategy` at `font_kit_studio_v0.1.1.html:4098` defaults to DOM order unless the parent is framework-managed, and README line 157 says the same.)
   - Rule 7, lines 100-101: delete the bullet "(Target state from plan Addendum 1, Task F; until committed, the Studio still prefills the old kit ID.)" and put nothing in its place.
   - Rule 8, first bullet: append "Optional Google Fonts stylesheets load on demand from the network; offline, the fallback stacks are used." (README line 202 already says this; the rule currently reads as "no network at all".)

3. **`AGENTS.md` Document Roles table** (line 28 and a new row):
   - Replace the `docs/assets/` row with: `| \`docs/assets/\` | **Brand and screenshots** | README logo SVGs and their font licences, logo previews, and README screenshots (\`screenshots/\`, regenerated by \`screenshots/capture.py\`). |`
   - Add: `| \`docs/roadmap/\` | **Roadmap** | Ideas that are not built (for example the browser extension). Nothing here is a commitment. |`
   - Add to the Gate evidence row or a new row: `docs/implementation/sweep-*.md` | **Sweep reports** | Read-only consistency passes before a release point.

4. **`docs/implementation/progress.md` "Current state"**: update it to say Tasks A, B, C, E, F, G are committed and reviewed, Task D is in review, and the remaining work is the sweep fixes, the gate runner (`verification-v0.2.md`) and the final whole-branch review. Chromium only (D010).

5. **`README.md` Library and Composer bullets (lines 34 and 204):**
   - Line 34: replace "Both are unchanged and need no bridge." with "Both still work without a bridge. The font library is now free Google Fonts; see [Free fonts](#free-fonts)."
   - Add to the line 210 bullet (**Sync to Live App**): "It also reorders the page's main sections by slot order and adds a short CSS `transition` to them (Design Bridge spec section 8.3). That does not show in the Changes panel. Use **Reset** to undo it."
   - Add one bullet to the Select/Interact or Code panel section for the **Restore Page Text** button (`#btnRestoreOriginalText`): "**Restore Page Text** puts every changed text back and keeps styles." The old README documented it and the new one does not.

6. **`docs/implementation/deviations.md`**: add D022 (see S4) and extend D009 per S9.

7. **Spec file** (supplied input, recommend only): line 327-328 says a stale revision returns `design:conflict`; line 927 describes `design:select-slot`; section 10 item 2 describes the in-target HUD badge as the default. A short "Implementation notes" appendix pointing at D022 would stop later agents from re-adding these. Do not edit it.

## Nice to have

- Add `sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"` (no `allow-top-navigation`) to `#targetAppFrame` (`font_kit_studio_v0.1.1.html:1073`) so a framed page cannot navigate Studio's top window. The bridge needs scripts and its own origin only, not top navigation. Test with the real bridge first (pop-out and Sync are unaffected). The pop-out `window.opener` exposure is already documented in README Security.
- Studio `FRAMEWORK_GUARDS` (`:4058`) contains `"framework"`, which the bridge never emits (it uses `framework-managed`). Remove the alias.
- Unused constant `byName` (`:1926`; also in the supplied v0.1.1 file) and the 8 repeated `styles: [{label:"Regular"...}]` literals in the new font table (extract one constant).
- Anti-recursion check `/font_kit_studio|font-kit-studio/i` (`:3331`) blocks any target URL containing "font-kit-studio", for example a project served from a folder of that name. Compare against Studio's own URL only.
- `fake-target.html` names containers with `data-container-name` (lines 53, 65, 138), an attribute the real bridge does not read (Addendum 3 order: `data-design-name`, `aria-label`, first heading, `#id`, `tag.class`). Use `data-design-name` in the fake so it models the real contract.
- README protocol tables do not list the `detail.reason` values for move rejections (`unknown-container`, `into-self`, `into-descendant`, `relative-to-self`, `void-or-replaced-container`, `unarrangeable-reference`, `index-out-of-range`) or the `css-order` guard that the bridge emits at `fontkit-bridge.js:1199-1202`.
- `design:order-changed` is dispatched as a `CustomEvent` on the target window (`fontkit-bridge.js:2753`, Spec 8.3), has no listener in the repo and is not in the README. Document it in one line or drop it with S5.
- README Dev-server notes list `[::1]` as an accepted `Host`; `ThreadingHTTPServer` listens on IPv4 only here, so `[::1]` can never arrive. Harmless; reword or ignore.
- `.gitignore` covers `.fontkit-overrides.css.*.tmp` only for the default overrides name; a custom `--overrides foo/bar.css` leaves `.bar.css.*.tmp` after a crashed write. Use `.*.css.*.tmp`.
- Rule 10 (rule of three) elsewhere: three copies of `crypto.randomUUID ? ... : slot-...` (v0.1.1 code) and five `sendDesignMessage({ type:"design:select", targetId:live.selectedId })` calls. Extract if touched again.

## Message tabulation (item 1)

Legend: sent = code path that posts it; handled = code path that acts on it; doc = README table; plan = contract; fake = `tests/fixtures/studio/fake-target.html`; test = a test under `tests/` sends or asserts it.

Studio to bridge

| Type | Sent by | Handled by | Doc | Plan | Fake | Test | Verdict |
|---|---|---|---|---|---|---|---|
| `design:hello` | Studio (3310, 3370) | bridge 794, fake | yes | yes | yes | yes | ok |
| `design:update` targeted | Studio (3414) | bridge, fake | yes | yes | yes | yes | ok |
| `design:update` composition | Studio (3415) | bridge, fake (tokens only) | yes | yes | partial | yes | ok; see S1, S5, S7 |
| `design:select` | Studio | bridge, fake | yes | yes | yes | yes | ok |
| `design:mode` | Studio (4642) | bridge, fake | yes | yes (+overlay, Addendum 1) | yes | yes | ok |
| `design:move` | Studio (3418) | bridge, fake | yes | yes (Add. 1-3) | yes | yes | ok |
| `design:reset` | Studio | bridge, fake | yes | yes | yes | yes | ok |
| `design:restore-text` | Studio (3421) | bridge, fake | yes | yes | yes | yes | ok |
| `design:highlight` | tests only | bridge 798, fake | yes (legacy) | yes (legacy) | yes | yes | ok (legacy) |
| `fontkit:change` | tests only | bridge 810 | yes (legacy) | yes ("keep working") | no | yes | ok (legacy) |
| `design:inspect` | nobody | bridge 804 | yes | no | no | no | handled, documented, never sent, never tested: M1 |
| `design:ping` | nobody | bridge 807 | yes | no | no | no | same: M1 |

Bridge to Studio

| Type | Sent by | Handled by | Doc | Plan | Verdict |
|---|---|---|---|---|---|
| `design:bridge-ready` | bridge 702-703 | Studio 3760 | yes | yes | ok |
| `design:ready` | bridge 842 | Studio 3765 | yes | yes | ok |
| `design:applied` | bridge `acknowledge` | Studio 3788 | yes | yes | ok |
| `design:rejected` | bridge `reject` | Studio 3789 | yes | yes | ok |
| `design:hover`, `selected`, `bounds`, `targets` | bridge | Studio 3790-3815 | yes | yes | ok |
| `design:warning` | bridge | Studio 3811 | yes | Addendum 2 | ok |
| `design:inspect-result`, `design:pong` | bridge replies to M1 messages | Studio ignores (not in `BRIDGE_TYPES`, 3011) | yes | no | sent but never handled, follows M1 |
| `fontkit:ack` | bridge reply to `fontkit:change` | Studio ignores | yes | no | legacy, tested at bridge level |
| `design:order-changed` (CustomEvent, not postMessage) | bridge 2753 | nobody | no | no | Spec 8.3 only; see Nice to have |

Spec only, absent from code and README on purpose: `design:conflict` (replaced by `design:rejected`/`revision-conflict`), `design:select-slot` (removed; tests send it as a hostile message and assert it is ignored: `test_studio_live.py:185`, `:315`). README mentions neither (registry 11 satisfied for README; Spec text and `deviations.md` are the gap, S4).

Fields, guard names, patch keys and ranges: the targeted patch table matches across plan, bridge (`PATCH_RULES`, from line 214), Studio (`canonicalLiveValue`, 3052-3071), fake (`canonical`) and README (`fontSize` 4-400, `fontWeight` 1-1000, `lineHeight` 0.5-5, `letterSpacing` -0.5-2, color forms, `textAlign`, `textTransform`, `text` 5000, `fontStylesheet`). Differences: bridge also rejects `expression(` in `fontFamily` and applies `CSS.supports`; Studio does not (the bridge's rejection is handled). Studio-only `order` (CSS-order persistence) is never sent as a patch key (`:3647`) and the fake and bridge both answer `unsupported-property` for it. Guard names emitted by the bridge are `form-owner`, `radio-group`, `label-reference`, `aria-reference`, `content-model`, `framework-managed`, `css-order`; README lists all except `css-order`. Only `framework-managed` is overridable and only it shows **Move anyway** (Studio 4216). `design:ready` capabilities in bridge and fake are identical to the plan.

## Clean areas

- **Security sinks.** Bridge: no `innerHTML`, `insertAdjacentHTML`, `outerHTML =`, `document.write`, `eval`, `new Function`, string `setTimeout`, `DOMParser`, `window.open` or `location` use. `postMessage(..., '*')` appears only for `design:bridge-ready` (data-free, lines 702-703) and the opaque `null` origin (line 763). `link.href` (line 1509) takes only `safeFontStylesheet` output; placed images take only `safeAssetUrl` PNG/SVG data URLs; overlay text uses `textContent`. Studio: every `innerHTML` with data from the target or an import goes through `escapeAttr` (`:3954`, `:3961-3965`, `:4005`, `:4123-4158`); `normalizeArrangement` caps lengths and allow-lists `frameworkManaged`; numeric template values in the v0.1.1 inspector (`:2611-2653`) come from import validation (Task 4 review). `iframe.src` and `window.open` take only `resolveTarget()` output (http/https, `file:` only from `file:`, never Studio itself); `link.href` for Typekit uses a sanitised id; the Studio CSS builder skips selectors and values that fail `safeCssText`, and `@import` URLs pass `safeFontStylesheet`. The only `postMessage` in Studio is `sendDesignMessage`, pinned to `expectedOrigin` (`"*"` only for `"null"`). There is one `message` listener in Studio and the bridge uses one handler. `demo/index.html` has no script except the bridge tag and no external resource. `scripts/serve.py`: loopback bind, Host check (421), Origin check on PUT (403), 1 MiB limit (413), `Content-Type: text/css` required (415), hidden path segments refused, atomic write under a lock, overrides path confined to the repo and `.css`, no directory listing, 30 s socket timeout.
- **Hygiene.** IDs unique (static check, plus a runtime duplicate-ID scan of Studio after connecting, selecting an element and opening Arrange, of Studio standalone, and of the demo: all empty). No tracked `__pycache__`, `.tmp`, `work/` or scratch files; `git status --ignored` shows only the two `__pycache__` directories as ignored; `work/` is empty; `demo/fontkit-overrides.css` absent. No credentials, tokens or personal e-mail in tracked source. `cqu4tvx` and `YOUR_KIT_ID` do not appear in Studio, bridge, demo or README. All README images, relative links and anchors resolve; every file under `docs/assets/screenshots` is referenced by the README or is `capture.py`; every fixture under `tests/fixtures` is used by a test.
- **Console.** One probe (Chromium): Studio with `?target=` connected to the real demo through the real server and bridge reached "Connected (37 targets)" with zero console errors or warnings, zero page errors and zero failed non-network requests; selecting a title, selecting the hero CTA and opening Arrange added none. Demo standalone: no errors, bridge object present, only the 12 author `data-design-*` targets in the markup (inert until hello). Studio opened with no target: no errors. Google Fonts requests were answered with empty CSS during the probe, so the offline path was exercised.
- **Free defaults.** 16 library fonts, all with a `css2` sheet URL that passes both validators; Adobe kit field empty, no Typekit link on load.
- **Registry check on the final tree.** 1 (trusting `event.data.type`): Studio `acceptBridgeMessage` and bridge `isFromSession` check source, origin, version and session; clean. 2 (`"*"`): see Security sinks; clean. 3 (untrusted markup): clean. 4 (unvalidated URLs): clean. 5 (silent overwrite): reconnect banner, no composition broadcast on connect, Reapply transactional (D020); clean. 6 (capture original once): WeakMaps (`styleState`, `textState`, `explicit`, `bridgeAttrs`); clean. 7 (intercepting without editor): `studioAlive()` gates click handling (line 2534); clean. 8 (unexercised handlers): **fails for `design:inspect` and `design:ping` (M1)**; all other types have a test. 9 (flags instead of idempotent handshake): Studio re-sends hello on every load; the bridge answers every hello; clean. 10 (personal defaults): clean. 11 (stale docs after protocol change): README is consistent with the code except the items above; `select-slot` is gone from README. 12 (fix the class): the S3 and S2 items are the sibling copies of earlier fixes. 13 (servers): the probe server was stopped (`pgrep serve.py` empty). 14 (claiming verification): **fails in README line 263 (M2)**; the README's own "Known gaps" and "Firefox status" are honest.
- **Dead code in the bridge.** Reference-count scan of every function, method and constant in `fontkit-bridge.js` found one method with no caller: `registerElementTarget` (line 1919, with its `explicit` WeakMap). It is public API from Spec 4.2 level 2 and reached only through `window.__fontkitBridge.registerElementTarget(...)`; it is not in the README and has no test. Decide: add a one-line README mention and a test, or remove it with `explicit`. (Left out of M1 because it is not a message handler.) In-target overlay code, theater and device controls are live features (pop-out overlay, README "Library and Composer", plan "preserve theater/device controls") and are not leftovers. No `fontkit:change` sender exists in Studio, but the handler is a contract-listed legacy path with tests.
- **Dead code in Studio.** Reference-count scan found only `byName` (S-level nice-to-have) and `initComposer` (a named IIFE). No leftover `design:select-slot`, `fontkit:` or `design:highlight` use in Studio.
- **Contract between Studio and the real bridge** was exercised by the probe (handshake, select, arrange list, composition sync) and by the existing real-bridge tests; the fake target tracks the contract except the container-name attribute noted above.

Not verified in this sweep: Firefox (not installed, D010); framework recipes (Vite, Next.js, Astro) which the README itself labels illustrative; the full unittest suite; the `data-allowed-origins` and `data-design-kind` runtime behaviour (no test exists, see M2); the S1 import-then-Reapply loop.
