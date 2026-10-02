# Final whole-branch review: v0.2.0 batch

Scope: the whole v0.2.0 branch against its base `9205f8c` (`main`), as at the PR #1 head at review time: 68 files, +17,849 / -1,288. Date: 2026-10-02. Read-only review.

Method: direct source reading, the plan with Addenda 1-3, the progress record, the deviations, the sweep and every `v02-task-*-review.md`. One end-to-end Playwright probe against `scripts/serve.py` (free ports) with Chromium at `/opt/pw-browsers/chromium` and Google Fonts routed to empty CSS. One HTTP probe of `serve.py`. The probes ran in a `git archive` copy of the head in a scratch directory, so no repo file was touched. Both servers were stopped. The full suite was not run here (see `verification-v0.2.md`). Gates run: `node --check fontkit-bridge.js` OK; `python3 scripts/verify.py --static-only` PASS (86 unique IDs, 1 inline JS block, provenance x3, Studio sha256 `0d75f190...40ab`, the same sha the Task D round 2 review recorded); `git diff --check` over the branch clean. Chromium only; Firefox was not run (D010).

## Verdict

**Ready with notes.**

There is no Critical issue. Every requirement is delivered or delivered with a stated limit. The end-to-end flow works as one product, with zero console errors. The trust boundaries hold under the probes I ran. I would not block the merge. Read "Release notes" first: Firefox is unverified, the real-framework recipes were never run, and DOM-order moves are not persisted by Sync.

## Requirements coverage

| Requirement | Status | Evidence |
|---|---|---|
| Live edits show in a localhost preview of a web app | Delivered | `scripts/serve.py` (two loopback ports, Host/Origin checks), `demo/index.html`, Studio `?target=` auto-connect. Probe: "Connected (37 targets)", title changed to Fraunces 72px, iframe computed style `Fraunces, serif / 72px`. Test `test_live_integration.py:242` `test_target_query_connects_and_clicking_the_page_edits_it`. |
| Shows changed CSS and HTML to sync or copy | Delivered | Code panel `#liveCodePanel` (`font_kit_studio_v0.1.1.html:1086-1103`): CSS / HTML / JSON tabs, Copy, Download, Sync to file, Auto-sync. Probe: clipboard held 503 chars, overrides file written ("Saved 503 bytes"), HTML tab showed the structure block for the moved CTA. Tests `test_live_integration.py:293` (real clipboard), `:313` (sync + reload + banner). |
| README with the logo | Delivered | `README.md:1-6` (`<picture>` light/dark), `docs/assets/fontkit-logo-{light,dark}.svg` (outlined paths, no text/script), licences in `docs/assets/README.md`, Task G report. Sans-serif `t` correction applied. Previews were viewed when the logo was made; the SVGs were not re-rendered in this review. |
| Free fonts, no Adobe kit out of the box | Delivered | 16 Google Fonts OFL families (probe: 16 plus "Current"), kit field empty, no Typekit link on load. `cqu4tvx` and `YOUR_KIT_ID` appear only in tests asserting absence, the plan and review records, and the preserved supplied tag. Tests `test_studio_live.py:1902` `test_defaults_are_free_and_adobe_is_an_opt_in_with_an_empty_field`, `:1931`, `:1961`, `:1994`, `:2029`; demo is offline (`test_demo_source_is_offline`). Adobe stays opt-in (`font_kit_studio_v0.1.1.html:3019`, `:1569`). |
| Production-grade bridge | Partially delivered | Hardened to the contract: session/origin pinning, atomic validated patches, inert until hello, SPA/HMR handling, hostile-input tests (83 bridge tests, e.g. `test_bridge_runtime.py:2161` double-load, `:1335` inert-before-hello, `:2400` rediscovery). Gap: no test runs a real React/Vite/Next/Vue/Svelte/Astro app. The README labels those recipes "illustrative" and says how they were checked (`README.md:268`), which is honest. Options `autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied` and `data-design-kind` have no test (README says so). |
| Separate window (pop-out) | Delivered (Chromium) | `#bridgePopOut`, `popoutFeatures()` (`:4412`), `window.open` only with a validated URL (`:4427`). Probe: pop-out opened at the target URL, placeholder text shown, picking the hero lead in the pop-out filled the inspector, Dock closed the window and reconnected ("Connected (37 targets)"). Tests `test_live_integration.py:566`, `test_studio_live.py:1746`, `:1816`, `:1854`. Browsers may open a tab instead; README says so (`README.md:176`). |
| Reorganize buttons and cards with UX guards | Delivered | Arrange section (First/Earlier/Later/Last, sibling list, Move into, DOM/CSS strategy), guards `form-owner`, `radio-group`, `label-reference`, `aria-reference`, `content-model`, `framework-managed` (+ Move anyway), `css-order`, runtime-error warnings. Probe: the CTA moved after the ghost button, HTML tab shows the container. Tests `test_bridge_runtime.py:1356-1743`, `test_live_integration.py:461`, `:492`, `:513`. Limit: DOM moves are not written by Sync (see Issues I2). |
| Extension roadmap | Delivered (as a roadmap) | `docs/roadmap/browser-extension.md` (goals, non-goals, MV3 sketch, security, open questions); linked from `README.md:552`. States "idea, not implemented". |
| AI-ready repo docs | Delivered | `AGENTS.md` (roles, bootstrap, gates, commit rules, anti-pattern registry), `docs/agents/global-rules.md` (10 rules, conflict order), `CLAUDE.md` (imports both), progress record, deviations, PR template. The sweep corrected them. Minor drift remains (Consistency). |
| MIT license | Delivered | `LICENSE` (MIT, "Copyright (c) 2026 pterw"), `README.md:565-567`, D025. The holder line can be changed. |

## End-to-end probe

Setup: `scripts/serve.py --studio-port <free> --target-port <free> --quiet`, Studio opened at `?target=http://localhost:<target>/demo/`, Chromium 1500x950, Google Fonts routes fulfilled with empty CSS, clipboard permission granted. Script: a scratch probe.

| Step | Result |
|---|---|
| Connect | Badge "Connected (37 targets)". No page errors, no console errors or warnings in the whole run. |
| Select hero title | Click inside the cross-origin iframe; inspector "Hero title". |
| Font to a library font | Picked Fraunces. Iframe computed `font-family: Fraunces, serif`. CSS tab starts with the `@import` for the Fraunces css2 URL (offline route returned empty CSS, no hang, no error). |
| Size | Typed `72` key by key. Iframe computed `72px`. CSS tab shows `font-size: 72px !important`. |
| Move CTA | Selected the hero CTA; Arrange showed "Position 1 of 2 in div.actions", First/Earlier disabled, DOM/CSS toggle present. Later moved it to position 2. HTML tab: `<!-- Structure: ... child order: A: "See how it works", Hero call to action -->` plus the container HTML. Badge "Live · rev 4". |
| Copy CSS | Real clipboard read-back: 503 chars; status "Copied CSS to the clipboard." |
| Sync to file | Button enabled; "Saved 503 bytes to demo/fontkit-overrides.css." File holds the `@import`, the title rule and a comment that DOM moves are not CSS. |
| Reload the iframe | The title keeps Fraunces 72px (now from the stylesheet). Banner: "Target reconnected. Studio has saved overrides for 1 target and 0 composition tokens; the live target has 0 targets changed ... Nothing was applied automatically." with **Reapply Studio overrides** and **Accept target state**. |
| Reapply | Banner hid; badge "Live · rev 1"; CSS tab unchanged for the title. The DOM-moved CTA was not restored and the structure block disappeared from the HTML tab (see I2). |
| Pop-out | `ctx.expect_page` got a window at the target URL; placeholder "The target is open in its own window ("fontkit-target")..." with the badge still "Connected (37 targets)". Selecting the hero lead in the pop-out showed "Hero lead" in Studio's inspector. |
| Dock | Pop-out closed, placeholder hidden, badge "Connected (37 targets)". |

First-time-user rough edges (none blocks):

1. **A DOM move silently disappears on reload.** Sync writes only a comment for it, the reload restores the original order, and after Reapply the HTML tab no longer shows the move. The README says "Not saved by Sync" (`README.md:135`, table at `:154`), but the banner and the status line do not say it at the moment it matters. A first-time user who moves a button, syncs and reloads loses the move with no message at that point.
2. **The banner appears right after a Sync + reload**, although the page already looks correct (the stylesheet applied the style). The text "the live target has 0 targets changed" is accurate (the bridge ledger counts only bridge overrides) but reads like a conflict. Choosing **Accept target state** here would adopt an empty state, and a later **Sync to file** would then write an empty file. It is explicit and worded ("the overrides file only changes when you sync"), and Task C fixed the silent version of this, so it is a wording trap, not a defect.
3. **The inspector's Family list starts with the full computed font stack** ("Current — "Iowan Old Style", "Palatino Linotype", ..."), which is long and noisy.
4. **Container names can be odd.** Before the CTA was selected, the stale title selection showed "Position 2 of 4 in Client work, without the status meeting…": the container is named after the headline text, as Addendum 3 prescribes (first heading inside). Accurate to the contract, unclear to a user.
5. **HTML snippet whitespace.** The HTML tab keeps the source's indentation/blank lines inside the container (`<div class="actions">` followed by a whitespace-only line). Cosmetic.
6. **Version label.** The window title and eyebrow say v0.1.1 for a v0.2.0 release (D009a records it).

Good error states I saw or confirmed in source: `No bridge detected` plus an add-the-script hint (`#bridgeHint`), pop-up blocked message, `Disconnected (window closed)`, reapply failure keeps saved state and retries, sync disabled with an explanation under `file://`.

## Security

Verified in this review (HTTP probe of `serve.py`, source reading, and the probe above):

| Check | Result |
|---|---|
| `PUT /__fontkit/overrides.css` with `Host: evil.test` | 421 |
| PUT with `Origin: http://evil.test` and with `Origin: null` | 403 each |
| PUT with `Content-Type: text/plain` | 415 |
| PUT on the target port, and `/__fontkit/status` on the target port | 404 (endpoints are studio-port only) |
| `GET /../../etc/passwd`, encoded traversal, `/.git/config` | 404 |
| CORS headers on any response | none (a hostile page cannot read or preflight-pass a write) |
| Console errors after connect, select, move, sync, reload, pop-out, dock | none |

Sink and boundary review (source): Studio and bridge both gate every message on source window, origin, protocol version and session (`acceptBridgeMessage`, `isFromSession`); `iframe.src` and `window.open` take only `resolveTarget()` output (http/https, `file:` only from `file:`, never Studio itself under any loopback alias); text goes in as `textContent`; assets render only as `<img>` PNG/SVG; one `unsafeCssText` gate on Studio's side; one validator set on the bridge's side; font stylesheets restricted to Google Fonts css2 and Typekit kit URLs with a strict percent-escape list. The sweep's clean-area findings stand and I found nothing that contradicts them.

Residual risks worth disclosing (none Critical):

- **`#targetAppFrame` has no `sandbox` attribute** (`font_kit_studio_v0.1.1.html:1073`). A framed page you chose to load could try to navigate Studio's top window (Chromium requires a user gesture for a cross-origin frame doing this). The sweep listed the `sandbox` flag as a nice-to-have; it was not done. The pop-out `window.opener` exposure is documented (`README.md:506`).
- **Studio is served without `X-Frame-Options` or `frame-ancestors`**, so a hostile site could frame `http://localhost:8000/...` while the server runs. It can only trigger actions on user clicks and writes only the single overrides file with Studio-validated CSS. Low.
- **Default bridge accepts a hello from any parent or opener origin and pins the first one** (`fontkit-bridge.js:27`, `:337`). A hostile page that frames your dev app could pin first and edit it. The bridge is dev-only by documentation; `allowedOrigins` closes this (`README.md:397`) but is not the default. The README does not call out the clickjack-style scenario.
- **PUT without an `Origin` header is accepted** (`scripts/serve.py:144`; confirmed with a bare PUT: 200). Browsers always send Origin on cross-origin writes, so only a local non-browser process can do this. The plan's contract says "if an Origin header is present"; this matches it.
- **`serve.py` serves the whole repository on both ports** (README says so, `README.md:504`). Fine on loopback; `--host` other than loopback widens it.
- **Synced overrides file is CSS the target app loads.** Studio limits it to validated selectors and values, but a malicious target's ledger is what Studio serialises. The gate is strict (no `url(`, braces, comments, `!important`), and the only `@import` targets are Google Fonts or Typekit. Low.
- **Third-party request:** Google Fonts stylesheets send the user's IP and font names to Google when a font loads (`README.md:206`).

## Consistency

Docs versus code (after the sweep): the README tables for messages, patch keys, guard names and reasons match the bridge (sweep tabulation and Task D re-review checked each); `design:inspect`, `design:ping` and `registerElementTarget` are removed from code and docs (D022, D024). `AGENTS.md`, `global-rules.md`, the plan and the README agree with each other on the free-font rule. Remaining drift:

- `docs/implementation/deviations.md` D019 says bulk manifests omit "`containers` and empty `siblings` over 100 children". Addendum 3 (as amended) says bulk manifests omit both entirely. The plan owns the contract; D019a records the correction.
- The plan's last two checkboxes (gate runner, final review) were unchecked at the time of writing, pending `verification-v0.2.md` and this file. All other plan checkboxes (A, B, C, D, E, F, G, sweeper) match git and the review files.
- Every recorded deviation has a ruling or an explicit "Deferred" (D021, tracked in `README.md:544`). None is left without a decision.
- The Spec file still describes `design:conflict`, `design:select-slot` and the in-target badge as default (D022 records this; the Spec is supplied input and was not edited).

## Release notes

Before merging to `main`:

- **Gate evidence.** See `verification-v0.2.md`; its test count (201, Chromium only) is the figure to rely on before merging.
- **Firefox is untested for everything in v0.2.0** (D010; README says so at `README.md:544`). The default `FKS_ENGINES` still lists Firefox, so a local run will exercise it for the first time. Expect possible differences in `window.open` popup features, clipboard, `CSS.supports` and iframe focus handling.
- **Real frameworks were not run.** The Vite, Next.js, Astro, SvelteKit and Nuxt recipes in the README are labelled illustrative. SPA and HMR behaviour is tested only on fixtures.
- **Deferred D021:** the "Sync to Live App" composition button sends font stacks as tokens without stylesheets, so a free font used only that way may not load in the target. Targeted inspector edits do load them.
- **DOM-order moves are not persisted by Sync** and are lost on reload (I2); CSS-order moves are persisted (D020). **Sync to Live App** also reorders main sections and adds a `transition`, which does not show in the Changes panel (README `:214`).
- **Known limits** (README "Known gaps"): edits made while the page reloads are dropped; rows hold 2-4 leaf slots; nested rows and JPEG are out of scope. Content-model guard checks only the moved element's own tag (E review).
- **Naming:** the file and window still say v0.1.1 (D009, D009a); the composition JSON `version` stays `0.1.1`; the new `live` field is additive.
- **Spec departures** (D016, D022): auto-discovered DOM-path selectors are persisted and labelled unstable; pop-out lets the bridge draw an outline; structural moves exist; `design:rejected`/`revision-conflict` replaces `design:conflict`; `design:select-slot` is gone. The Spec file itself is unedited.
- **Security posture to accept:** dev-only bridge with default any-origin pin; unsandboxed preview iframe; Studio not frame-protected; loopback-only server serving the whole repo.

I would not block the merge on any of the above.

## Issues

### Critical

None.

### Important

- **I2. DOM-order moves vanish on reload without a message at that moment.** `font_kit_studio_v0.1.1.html:3760-3766` (`resetNotice`) only discloses DOM-move loss when a CSS-order reset also undoes it; `:4498` writes only a CSS comment. Probe: move, Sync, reload, Reapply, and the structure block is gone from the HTML tab. Suggested fix: when a reload leaves Studio with DOM moves in its last-seen ledger that the new target does not report, say so in the banner ("Your DOM moves are not in the overrides file; copy the HTML tab before you reload, or use CSS order"). Documentation already says "Not saved by Sync" (`README.md:135`, `:154`).
- **I3. "Production grade" is verified on fixtures, not on real frameworks, and on Chromium only.** Evidence above. Not a code defect; the claim should be read as "tested contract and robustness cases", and the README wording already limits it. Closing it needs a real Vite/React and Next run and a Firefox run.

### Minor

- **M1.** `font_kit_studio_v0.1.1.html:1073`: add `sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"` (no top navigation) after testing with the real bridge, as the sweep suggested.
- **M2.** `docs/implementation/deviations.md` D019 contradicts the amended Addendum 3 (bulk manifests omit siblings entirely); D019a now records the correction.
- **M3.** README "Limiting which Studio can connect" (`README.md:397-400`) should say that without `allowedOrigins` any page that frames or opens your dev app can become its editor, and recommend setting it.
- **M4.** The banner wording after Sync + reload (probe step "Reload the iframe") invites a wrong choice. Suggest adding "The page already shows your saved styles from the stylesheet" when the page's computed styles match, or at least a line telling users to press Reapply (not Accept) to keep the file.
- **M5.** The Family dropdown's first option is the whole computed font stack (`font_kit_studio_v0.1.1.html` `#liveFontFamily`, built near `:4014`); show only the first family name and keep the full stack in a `title`.
- **M6.** HTML tab snippets keep whitespace-only lines from the source (probe output); normalise blank lines in the cleaned container HTML (bridge `cleanHtml`).
- **M8.** Studio is served with no `X-Frame-Options` or `frame-ancestors` (`scripts/serve.py`, response headers). Add `Content-Security-Policy: frame-ancestors 'none'` on the studio port only (the target port must stay frameable).
- **M9.** The README Firefox sentence and `AGENTS.md` environment notes are accurate; record the first Firefox run result in the verification records when it exists.
