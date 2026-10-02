# v0.2.0 Task D report: end-to-end integration, README, roadmap, screenshots

Branch: the v0.2 PR branch, based on the Task F change. Nothing is committed. Chromium only: Firefox is not installed (D010).

## Files changed

| File | Change |
|---|---|
| `tests/test_live_integration.py` | New. 13 tests in 9 classes, nothing faked. |
| `README.md` | Rewritten for users first (section list below). |
| `docs/roadmap/browser-extension.md` | New. Goals, non-goals, MV3 sketch, security, open questions. |
| `docs/assets/screenshots/` | New. 9 PNGs plus `capture.py` (regenerates them). |
| `demo/index.html` | Small realistic addition, no defect fix: a newsletter section with a real `<form>` (email field, a radio "segmented" pill group, a Subscribe button). It gives the guard test and the README FAQ a real form to point at. No inline script, no new author ids. `test_preview_server.py` still passes (18/18). |
| this report | |

No fix was made in `fontkit-bridge.js`, `font_kit_studio_v0.1.1.html` or `scripts/serve.py`. The integration tests found no defect in the real bridge, Studio or server, so there is no RED/GREEN app fix to record.

## Integration test design

- `scripts/serve.py` runs as a subprocess on two OS-assigned loopback ports (`free_ports()`, retried up to 3 times if a port is taken), with `--overrides work/live-integration-*/overrides.css` (inside the repo, gitignored). `tearDown` (via `addCleanup`) sends SIGTERM, waits, kills as a fallback, and removes the scratch directory. After the run `work/` is empty and no `serve.py` process remains.
- Real Studio over `http://localhost:<port>`, real `fontkit-bridge.js` inside `demo/index.html`, Chromium via `from support import ENGINES, launch`. Clipboard permissions are granted for the Studio origin and the real Clipboard API is read back.
- Two pieces of plumbing, both documented in the module docstring:
  1. `https://fonts.googleapis.com/**` is answered with empty CSS (recorded), every other https request is aborted, so the suite is offline.
  2. The demo always links `demo/fontkit-overrides.css`, but each test uses its own temp overrides path. The browser request for the demo's stylesheet is redirected (`route.continue_(url=...)`, same real server) to the temp path, so the browser still fetches what the real server wrote to disk.
- No new fixed sleeps. The only `time.sleep(0.05)` calls are polling loops (server banner, overrides-file condition wait). No `wait_for_timeout`. One bounded retry in `click_in_target` covers the load-time re-hello, which legitimately starts a new session and clears a selection made in the same instant.

### Coverage (all in `tests/test_live_integration.py`)

| Class.test | Proves |
|---|---|
| `EditAndCodePanelTests.test_target_query_connects_and_clicking_the_page_edits_it` | `?target=` auto-connect to `Connected (N targets)` (N >= 12); click `landing.hero.title` inside the iframe; keystroke typing of size (`56`), colour (`#0a7d3b`) and text; asserts the iframe's computed `fontSize`/`color` and `textContent`; Studio overlay is outside the target DOM; CSS, HTML and JSON tab contents (rule, cleaned snippet, exact `overrides` object). |
| `EditAndCodePanelTests.test_copy_uses_the_real_clipboard` | Real clipboard read-back equals the shown CSS, JSON and HTML tab text. Chromium only (Playwright clipboard permissions). |
| `SyncAndReloadTests.test_sync_writes_the_file_and_a_reload_keeps_the_style_and_asks_before_reapplying` | Nothing written before Sync; Sync writes the file on disk and the server serves identical bytes (`text/css`, `no-store`); text is not in the file; Auto-sync updates the file; reloading the iframe keeps the computed size from the stylesheet with no inline override, original text back, banner visible and nothing applied; Reapply restores inline style and text; reload again then Accept: banner hidden, JSON overrides `{}`, status says the file is unchanged, file bytes unchanged. |
| `InteractModeTests` (2) | Demo works without Studio (nav anchor navigates, no bridge DOM). In Select mode a nav click selects and does not navigate; in Interact mode the same click sets `location.hash` and scrolls; Select selects again. |
| `RestoreAndResetTests` | Restore Page Text brings the copy back and keeps the 30px style; Reset this element returns `document.body.outerHTML` byte for byte, JSON overrides `{}`, count 0. |
| `ArrangeTests` (3) | CTA "Later": DOM order swaps, HTML tab shows the `Structure:` block with the cleaned container (auto-registered sibling carries no bridge attributes), CSS tab points to the HTML tab; Reset restores the markup byte for byte. CSS-order strategy: DOM untouched, visual order and CSS `order: 1 !important` change, Reset clears. Guard: Subscribe button moved into the "Solo" plan is refused with the `form-owner` message, no "Move anyway", markup byte-identical. The demo now has a form, so this is not skipped. |
| `FontTests` | Free library font Fraunces: `fontStylesheet` link in the target head, the css2 request recorded, CSS tab and synced file start with `@import url("…")`; no Adobe kit prefilled; choosing the page's family releases the link. |
| `PopOutTests` | Pop out opens the named window; bridge draws its own outline there; click in the popup selects; Studio inspector edit changes the popup's computed style; Dock closes the popup, returns the iframe, shows the banner (saved edit waits), Reapply restores it, outline gone. |
| `BookmarkletTests` | The README bookmarklet code, run in a pop-out of a page with no script tag, makes Studio go from `No bridge detected` to `Connected` and edit works. Run via `evaluate`, not a real bookmark click. |
| `OpenedFromFileTests` | Studio opened as `file://` connects to the served demo and edits; Sync and Auto-sync are disabled with the dev-server hint; nothing written. |

Mutation check (not kept): replacing the bridge's `form-owner` guard result with `null` made the guard test fail (timeout waiting for `#liveMoveGuard`); the bridge was restored byte for byte (`git status` shows it unmodified).

## Gate evidence

All run from `/home/user/font-kit-studio` with `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`.

| Command | Result |
|---|---|
| `python3 scripts/verify.py --static-only` | PASS 86 unique static IDs; PASS 1 inline JS block; sha256 `7361ec8a4004a0c230696506df1618b6ab9733ab937d9998877d6961b06b560c` (Studio unchanged); provenance PASS x3 |
| `node --check fontkit-bridge.js` | OK |
| `git diff --check` | clean |
| `python3 -m unittest discover -s tests -v` | **Ran 195 tests in 316.248s, OK** (182 earlier + 13 new). Chromium only. |
| `python3 -m unittest tests.test_live_integration` | 13 tests OK; the earlier 11-test version passed 3 consecutive runs (about 29 s each) |
| `python3 -m unittest discover -s tests -p test_preview_server.py` | 18 OK after the demo change |

Not run: Firefox (not installed, D010).

First run of the integration file had 3 failures, all in my own assertions, fixed before the final runs: the demo's author `data-design-name` is legitimately in the HTML snippet; Chrome returns a computed `font-family` without quotes; an auto id for the Subscribe button is not stable, so the test matches the shown name.

## README section list

Header (logo `<picture>` light/dark, pitch, nav links, hero screenshot) · What it is · Quickstart (including "Open the Studio HTML file directly" and dev-server flags, `--host 0.0.0.0` gives LAN clients 421, non-default `--overrides` is not linked by the demo) · Workflows (Live Target inspector, Select vs Interact, Code panel, Arrange with strategies and guards, Pop-out window, Reconnect banner, Free fonts, Library and Composer) · Why fontkit (category table, no named products) · FAQ (the three mock questions) · Add fontkit to your app (plain HTML, Vite, Next.js, Astro, Tailwind, attributes, allowed origins, bookmarklet) · Protocol v1 (message tables written from the bridge and Studio source, patch keys) · Security model · Development and testing · Roadmap · Provenance · License.

Leftover grep on `README.md` and the roadmap: `select-slot`, `cqu4tvx`, `Typekit (`, `20 Playwright`, `YOUR_KIT`, `jsdelivr`: no matches. All relative links, images and anchors resolve.

## Recipes: verified vs illustrative

| Recipe | Status |
|---|---|
| Plain HTML script tag | Verified: the demo uses exactly this tag against the real bridge in every integration test. |
| Attributes (`data-design-id/role/name/weights/order-container/kind`) | Verified in the bridge suites and the demo; the README table was written from the source. |
| `allowedOrigins` (option, `data-allowed-origins`, `FONTKIT_BRIDGE_OPTIONS`, `data-auto-init="false"`) | Source and header read; behaviour covered by Task B/E bridge tests, not re-run here by a README snippet. |
| Bookmarklet | Verified by `BookmarkletTests` (code run via `evaluate` in a pop-out). Inside an iframe a bookmarklet cannot run, so the README says to use a pop-out. |
| Studio from `file://` | Verified by `OpenedFromFileTests` (edit, Copy status, sync disabled). Download from `file://` was not exercised, so the README claims only the inspector, Changes panel and Copy. |
| Vite plugin (`apply: 'serve'`, `transformIndexHtml` returning a tag descriptor with `injectTo: 'body'`) | **Illustrative.** Syntax checked against the Vite docs (Context7); no Vite project was installed or run. |
| Next.js (`next/script`, `strategy="afterInteractive"`, `process.env.NODE_ENV === 'development'`) | **Illustrative.** Checked against the Next.js docs; not run. |
| Astro (`import.meta.env.DEV && <script is:inline src=…>`) | **Illustrative.** Checked against the Astro docs (Astro 5 needs `is:inline` for conditional scripts); not run. |
| Tailwind note | Advice, not a tested recipe. |

I avoided a `import()` recipe: `serve.py` sends no CORS headers, so a cross-origin dynamic import of the bridge would fail; a script tag does not need CORS.

## Screenshots (`docs/assets/screenshots/`, all under 300 KB)

Real Studio connected to the real demo over `serve.py`, Chromium, regenerated by `capture.py` (`python3 docs/assets/screenshots/capture.py`, same env vars). I opened and looked at all of them.

| File | Size | Viewport | Shows |
|---|---|---|---|
| `target-app-desktop.png` | 164 KB | 1440x900 | Theater mode: preview with the hero title selected, Changes panel, inspector |
| `code-panel-desktop.png` | 29 KB | element | Changes panel, CSS tab with the three declarations |
| `bridge-bar-desktop.png` | 17 KB | element | Status badge, Select/Interact, Pop out, device buttons |
| `arrange-desktop.png` | 143 KB | 1440x900 | Arrange section for the CTA with strategy toggle and sibling list |
| `arrange-guard-desktop.png` | 119 KB | 1440x900 | Subscribe button blocked by the form-owner guard |
| `pop-out-desktop.png` | 168 KB | 1440x900 | Docked pop-out placeholder; also shows the reconnect banner |
| `target-app-mobile.png`, `code-panel-mobile.png`, `arrange-mobile.png` | 68, 64, 46 KB | 390x844 | Same views at phone width |

## Open concerns

1. **No LICENSE file.** The README says "MIT" (as the old README did), but there is no `LICENSE` file in the repo. A `LICENSE` file should be added or the line changed.
2. **Spec document is stale.** `font-kit-studio-v0.2.0-design-bridge-protocol-v1.md` (supplied product input, line 927) still describes `design:select-slot`. I did not edit it. The README links it as the "requirements" and points to the plan for the exact contract.
3. **Demo changed.** The newsletter form is an addition outside "fix only", allowed by the brief. If an unchanged demo is preferred, the guard test and the guard screenshot depend on it.
4. **Redirect plumbing.** Because the demo links only the default overrides path, the integration tests redirect that one request to the test's own overrides file. The server and file are real, but this is the one place the browser's request URL is rewritten.
5. **Unverified claims, stated as such in the README:** `Cross-Origin-Opener-Policy: same-origin` severing the pop-out link; pages with strict CSP refusing the bookmarklet; the framework recipes. Firefox is unverified for all v0.2 features.
6. **Pop-out and reconnect banner.** After a pop-out, or a dock back, Studio shows the reconnect banner whenever it holds saved edits the fresh page does not have. That is the intended no-silent-overwrite behaviour, and the tests assert it, but users may find it surprising the first time. The README explains it.
7. **Mobile screenshot of the target is a narrow iframe** (the app at about 350 px, 64 px headline); it shows the layout works, not a polished design.
8. **Known product gaps listed in the README:** D021 (composition sync has no stylesheet key), edits during a reload are dropped, DOM moves are not in the synced file.
9. **Task C/F carry-overs confirmed against the real bridge here:** `design:applied` and `design:selected` carry manifests, ledger declarations use CSS forms (`56px`), `rect` is in the iframe viewport (the Studio overlay lined up with the element in the screenshots), and pop-out plus arrange both work against the real bridge.

---

# Changes after first review (review `v02-task-d-review.md` and `sweep-v0.2.md`)

Base: the docs commits after Task F; nothing committed. `AGENTS.md`, `docs/agents/global-rules.md`, `progress.md` and `deviations.md` were not edited. Chromium only (D010).

This section supersedes the first report where they differ: the pop-out is now a real window request, the README no longer says the bookmarklet can be pasted into the address bar, the license line changed, and the demo-only claims about "6 recipes" now include SvelteKit and Nuxt.

## Gates after the round

All with `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`.

| Command | Result |
|---|---|
| `python3 scripts/verify.py --static-only` | PASS: 86 unique IDs, 1 inline JS block, Studio sha256 `1b783e8c4ff8035881ec14e630bb75f3d82d7441da2b698f05918f06b33d76df`, provenance x3 |
| `node --check fontkit-bridge.js` | OK |
| `git diff --check` | clean |
| `python3 -m unittest discover -s tests -v` | **Ran 200 tests in 334.2 s, OK** (195 before, plus 5 new test methods; the pop-out, token, composition and integration tests were also extended in place) |

New test methods: `StudioSharedRulesTests.test_ledger_tokens_and_imports_follow_the_bridge_rules`, `StudioBlockedStorageTests.test_blocked_local_storage_does_not_stop_start_up_or_auto_connect`, `StudioRecursionGuardTests.test_only_studio_itself_is_blocked_not_every_url_that_mentions_it`, `ImportedTokensTests.test_imported_tokens_use_the_bridge_rule_and_reapply_settles_with_no_lingering_banner`, `BookmarkletTests.test_the_readme_script_tag_loads_the_bridge_from_the_dev_server`. After the final run no `serve.py` process and no `work/` directory contents remain (an earlier scratch probe of mine had left one; I stopped it and deleted its folder).

## Code items (RED first, then GREEN)

| # | Item | RED | GREEN / change |
|---|---|---|---|
| 1 | Pop-out as a window | `StudioPopoutTests` (2 tests): `AssertionError: 2 != 3 : window.open needs a features string`. The assertion wraps `window.open` and parses the 3rd argument. | `popoutFeatures()` in Studio: `popup=yes,width=<=1280,height=<=860,left,top`, capped by the screen and offset 40 px from Studio; the name `fontkit-target` is kept. The real-Chromium integration test also asserts the popup's `innerWidth/innerHeight` equal the requested size (1280x820), which was reliable. |
| 2 | Delete `design:inspect` / `design:ping` | Pure deletion (no test sends them: `grep -rn "design:inspect\|design:ping\|pong\|inspect-result" tests` was empty before and after). | Removed both `case` branches and `handleInspect`. `capabilities.inspect` kept. Full suite green. README rows removed. |
| 3 / S1 | One token-name rule; bridge rejects | `LegacyCompositionTests.test_legacy_tokens_accept_only_safe_names_and_values` rewritten: 12 bad tokens plus the shortcut keys; against the old bridge it errored on every subtest (`KeyError: 'reason'`, the update was acked as applied). Studio: `test_invalid_saved_tokens_reject_the_whole_import` with `--Font-Display`, `--font_display`, a 121-char name failed (`Composition imported.`). | Bridge `TOKEN_NAME = /^--[a-z0-9-]{1,120}$/`; `invalidTokenInPatch()` runs before anything is applied and replies `design:rejected` / `unsupported-value` with `detail.property` (`tokens` or `sans/serif/mono/display`). It rejects invalid names and also invalid values, because the same silent drop existed for values (decision recorded below). Studio `CUSTOM_PROPERTY` is the same rule for imports and ledger tokens. Real-bridge loop test: an invalid name is refused at import; a valid token imports, the banner appears, Reapply sets the property in the target, the banner hides, JSON export keeps the token. |
| 4 / S2, S3 | `unsafeCssText`; font validator | `StudioSharedRulesTests` against a fake target with `?hostile=1`: `--url` (a `url(https://evil.example/a)` token) appeared in the synced CSS; the 6-family import was refused; `~` was refused. | One `unsafeCssText` (`UNSAFE_CSS_TEXT`: `; { } < > \`, newline, `url(`, `expression(`, comment markers, `!important`) used by `canonicalLiveValue` (font family), `parseLiveTokens` and `safeCssText`. Selectors pass `{selector:true}` so escaped quotes in `[data-design-id="a\"b"]` still work. `safeFontStylesheet` now matches the bridge: 1 to 8 families, one `display`, one `text` (600 max), the Addendum 3 percent allow-list, `~` allowed. |
| 5 / S6 | `readStore` / `writeStore` | `StudioBlockedStorageTests` (a throwing `localStorage` getter): never reached `Connected` (timeout), page error on start-up. | Four call sites use guarded helpers; the test now sees no pageerror, the Composer renders, `?target=` connects, loading a kit does not throw. |
| 6 / S7 and dead code | Composition payload, dead members | `test_explicit_composition_sync_is_session_gated` extended: against the old Studio `layout` had `backgroundHex`/`canvasWidth` (`'backgroundHex'` assertion failure, verified by running the test on the unmodified Studio). | Removed `familyRaw`, `layout.canvasWidth`, `layout.backgroundHex`. **`targetId` is not removed:** the bridge reads `slot.targetId` (`resolveElementForSlot`, `applySlotUpdate`) and the legacy bridge tests send it, so it stays; Studio never sets it, so it is a no-op field Studio side only. Deleted `registerElementTarget` with the `explicit` WeakMap, `byName`, and the `"framework"` alias (`grep` found no other users; suite green). |
| 7 / S8 | Test hygiene | n/a | Removed `import os` from `test_preview_server.py` and the unused `list_ids` helper. |
| 8 | Anti-recursion | `StudioRecursionGuardTests`: a target URL with `?project=font-kit-studio` was blocked (timeout). | Only Studio's own document (URL without query or fragment) is blocked. The existing self-embed tests (`APP`, popped-out `APP`) still pass, and the new test adds `APP?x=1` and `APP#panel`. |
| 9 | Fake target | n/a | Container names now use `data-design-name` (`containerName()` in the fake already read it; the markup used `data-container-name`). Suite green. |
| 10 | `.gitignore` | n/a | `.fontkit-overrides.css.*.tmp` became `.*.css.*.tmp`. |
| 11 | Integration test hygiene | n/a | `BookmarkletTests` now reads the `javascript:` line and the plain `<script>` tag from `README.md`, swaps the README's port 8000 for the test's Studio port, waits for Studio's own `No bridge detected` after the pop-out (like a person), and checks that running it twice adds no second script. A new test loads a page that carries only the README tag, served by the real server from the scratch folder. The racy close wait is `with popup.expect_event('close')` around the Dock click. `click_in_target` retries only on `PlaywrightTimeout`. `CONNECTED` accepts "1 target". |

Two surprises worth knowing:
- A page returned by `route.fulfill()` has an unknown address space, so Chromium blocked its request for `http://localhost:<port>/fontkit-bridge.js` (Private Network Access). The plain-tag test therefore writes its HTML into the scratch folder and lets the real server serve it.
- Existing tests whose meaning changed (not just assertions): the legacy token test (silent drop became rejection). `fontkit:change` (legacy, no reject message exists) still drops an unsafe font silently and acks; I left that and note it here.

## README and roadmap changes

Applied: pop-out wording (window request, the browser decides, the reconnect banner explained, no screenshot claim); bookmarklet (create a bookmark, or paste the part after `javascript:` into the console; why address-bar paste fails; port 8000 and origin cautions); Download-from-file claim removed (not tested); guard rows (label/aria precision, `content-model` with `summary`, `css-order`, move-rejection `detail.reason` values); exact Reapply label; Python wording (3 with 3.11 tested; use `python3`); bridge-ready contradiction; Alt+Arrow wording; Tailwind (`!important`, any stylesheet); "loopback by default", `[::1]` removed; tagline "CSS and HTML"; Google Fonts privacy sentence; Sync to Live App disclosure (sections reordered and given a `transition`, not shown in the Changes panel); Library "unchanged" replaced; Restore Page Text bullet; the "how these recipes were checked" text from the sweep (narrowed, I kept the claim narrow instead of adding option tests); Next.js Pages Router line; SvelteKit and Nuxt illustrative recipes (checked against the SvelteKit and Nuxt docs for `dev`/`svelte:head` and `app.head.script`; marked illustrative, with the SvelteKit client-only caveat); protocol tables (inspect/ping/pong/inspect-result rows removed; composition token rule and rejection added). License section: "License: not yet specified. The owner will add a `LICENSE` file; until then all rights are reserved by the author." **No LICENSE file was added, per instruction. Open for the owner.**

One difference from the planned wording: the Sync to Live App disclosure says "Reload the preview to undo it" instead of "Use Reset". Studio has no UI for a global reset (no code path creates a `design:reset` without a `targetId`; the per-element **Reset this element** is the only reset), and I probed that the sections get inline `order` and `transition` after pressing the button.

Roadmap: `sidePanel` permission added; Chrome 111 note for `world: "MAIN"`; MV3 inline-script problem stated (Studio cannot be reused unchanged); "no network requests" qualified with Google Fonts.

## Screenshots recaptured (`capture.py`, all under 170 KB)

- The edit is now visible: 72 px, -0.04em, `#0b6e4f` (the demo's own values are 60.96 px, -0.02em, `#14213d`).
- `pop-out-desktop.png` is taken before any edit, so no reconnect banner dominates it (the README explains the banner in text instead).
- Arrange and guard shots (desktop) use theater mode, so the form and the selection label are not cropped and the sticky Library/Composer tabs do not cover content; the narrow shots scroll 64 px below the tabs.
- I looked at the target-app, arrange, guard, pop-out and mobile shots after capture.

## Open concerns (updated)

1. **License:** no `LICENSE` file; README says so. Licence decision pending at the time (resolved in changes after second review).
2. `fontkit:change` still acks after silently dropping an unsafe font value (legacy path with no reject message). Candidate follow-up if the legacy path is kept.
3. `targetId` remains in the composition slot payload for the reason above.
4. Option and attribute coverage is still narrower than the implemented surface; the README now says exactly which are untested.
5. Firefox unverified (D010); framework recipes illustrative.
6. The Studio `sandbox` attribute idea and the other "nice to have" sweep items I was not asked to do (`design:order-changed` documentation, repeated font `styles` literals, Windows paths in old task records, S9 version label) are untouched.

---

# Changes after second review

Base: the Task D commit. Nothing committed by me. Chromium only (D010). I did not edit `LICENSE`.

| Item | RED | Change |
|---|---|---|
| R2 anti-recursion under loopback aliases and path case | New `RecursionGuardTests.test_studio_is_blocked_under_any_loopback_alias_or_path_case_but_other_ports_connect` (real Studio on `http://localhost:<port>`): `127.0.0.1`, `[::1]`, upper-cased path, trailing slash and query/fragment variants must give `Recursion blocked`. It failed against the round-1 guard (timeout on the `127.0.0.1` probe). | `isStudioDocument(url)`: same document ignoring query and fragment, or both hosts are loopback aliases (`localhost`, `127.0.0.1`, `[::1]`) with the same protocol and port and equal paths ignoring case and a trailing slash. The test also asserts that the demo on the other port through `127.0.0.1` with `?project=font-kit-studio` still connects; the existing `?project=font-kit-studio` test passes too. |
| R6 dead `targetId` | Pure deletion (JSON dropped the `undefined` anyway, so no RED is possible). | `targetId:slot.targetId` removed from Studio's composition slot payload. The bridge's legacy `slot.targetId` handling and its tests are untouched. |
| R1 | n/a (docs) | README: `data-allowed-origins` moved to the tested list (`target-restricted.html`); the untested list is now `autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied` and `data-design-kind`. |
| R3 | n/a | `fontFamily` patch-key row lists `url(` and `expression(`. |
| R4 | n/a | "The font library is free Google Fonts". |
| License | n/a | License section is now: "MIT. See [LICENSE](LICENSE). The logo outlines derive from SIL Open Font License 1.1 fonts; see docs/assets/README.md." Grep for "not yet specified" and "all rights reserved" in README, roadmap and assets README: no matches. This closes open concern 1 above. |

R5 (D024) and R7 are recorded decisions or awareness only.

## Gates

`FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`:

| Command | Result |
|---|---|
| `python3 scripts/verify.py --static-only` | PASS: 86 unique IDs, 1 inline JS block, Studio sha256 `0d75f19088b47df8ccde20443fcb334446ac6cc5d95f07d0151d40d9e42440ab`, provenance x3 |
| `node --check fontkit-bridge.js` | OK |
| `git diff --check` | clean |
| `python3 -m unittest discover -s tests -v` | **Ran 201 tests in 352.8 s, OK** (200 before plus the new recursion test). Run before the README-only license edit, which no test reads except the bookmarklet/script-tag snippets, both unchanged. |

No `serve.py` process and no `work/` contents left.
