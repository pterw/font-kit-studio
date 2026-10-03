# v0.2.0 Task D review (read-only reviewer)

Task D uncommitted, on top of the Task F change. Reviewer made no repo edits other than this file. Everything below is direct source reading, runtime evidence, and library documentation (Vite, Next.js, Astro).

Commands run (Chromium only, `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`):

| Command | Result |
|---|---|
| `unittest discover -s tests -p test_live_integration.py -v` | 13 tests, OK, 36.5 s |
| `unittest discover -s tests -p test_preview_server.py -v` | 18 tests, OK, 5.9 s |
| `cd tests && unittest test_bridge_runtime.SiblingOnlyHitTestTests` (the only bridge tests that load the changed demo) | 3 tests, OK |
| After every run: `ps aux \| grep serve.py` | no process left |
| `git status --short` | only the Task D files; `work/` is gitignored and empty |

Mutation checks (scratch copies, repo untouched):

1. `scripts/serve.py` writes extra bytes: `SyncAndReloadTests` FAILED (written file differs from the CSS tab). Good.
2. Bridge `isSelecting()` ignores Interact mode: `InteractModeTests` ERRORED (timeout waiting for `location.hash`). Good.
3. Bookmarklet test with a wait for the 4 s "No bridge detected" badge before injecting (what a human does): still passes. The feature works late; the test just does not exercise it.

## Spec Compliance

Plan Task D items and Addenda 1 (1-4) and 2 (README positioning):

| Requirement | Verdict |
|---|---|
| Real serve.py on free ports + real Studio + real bridge + demo, `?target=` auto-connect, click `landing.hero.title`, change size/colour/text, assert iframe computed style/text, CSS/HTML/JSON, clipboard, sync writes file, reload keeps style + reconnect state, Interact nav link, restore text, reset | Met (13 tests, no fakes) |
| README preview workflow, code panel, sync, protocol summary, env vars, no stale claims | Met, with the inaccuracies listed below |
| Add1 #1 logo `<picture>` (light/dark `srcset`, `alt`, width) | Met; paths exist; assets render correctly (viewed `preview-light.png`) |
| Add1 #2 user-friendly framing, separate window, fonts plus reorganising buttons/cards, extension roadmap link | Met in intent. Two overstatements: pop-out "window ... beside" (I1) and the tagline "then copy the CSS" (M9) |
| Add1 #3 free fonts, Adobe bring-your-own, no `cqu4tvx` | Met. 16 Google families, all OFL. Kit field empty (asserted by a test). |
| Add1 #4 framework recipes, dev-only, marked illustrative | Mostly met. Plain HTML, Vite, Next, Astro, Tailwind present and marked. Vue/Svelte only via plain Vite (M6). |
| Add2 "Why fontkit" with category comparison, no unverifiable competitor claims | Met. No product named; each row is a category-level statement plus "where fontkit differs". |
| Add2 three-question FAQ (what/why, click-and-go, segmented-control-in-form safety) | Met |
| Security model, roadmap link | Met, minor wording issues (M3, M8) |

## Strengths

- The integration suite is real: subprocess `serve.py`, real cross-origin frames, real keystroke typing, computed-style assertions inside the iframe, file bytes compared to the CSS tab and to what the server serves, byte-for-byte `document.body.outerHTML` after Reset, and real clipboard read-back. Both mutations I tried were caught.
- Server lifecycle is clean (SIGTERM, kill fallback, scratch dir removed); no leftover process or file after four runs.
- The README is unusually well grounded: patch ranges, regexes, status strings, button ids, filenames, flag semantics, 421 behaviour, `--overrides` constraints, guard names and message list all match the code. It states what is not verified (Firefox, framework recipes, COOP).
- The bookmarklet is syntactically valid, side-effect-free when run twice (`window.__fontkitBridge` check) and proven to connect a script-less pop-out.
- Roadmap is candid ("idea, not implemented") and correctly identifies the parent/opener-only hello as the blocking transport problem; verified `isStudioWindow()` rejects `window.parent === window`, so an in-page relay really would be refused.
- Demo addition is realistic, offline, adds no script, and leaves the other targets intact (preview server and demo-dependent bridge tests pass).

## Issues

### Critical

None.

### Important

**I1. README.md:175 (and :26, :174-181): pop-out is a new tab by default, not a window "beside" Studio.** Studio calls `window.open(url, "fontkit-target")` with no window features (`font_kit_studio_v0.1.1.html:4381`), which browsers normally open as a tab. Side by side needs the user to drag the tab out. Fix line 175:
> **Pop out** opens your app in a second browser tab (or window, depending on your browser settings) and keeps Studio in the first one. Drag the new tab out into its own window if you want the two side by side. The page then runs at its real size, and nothing is inside an iframe, which helps with apps that refuse to be framed.

**I2. README.md pop-out section vs `pop-out-desktop.png`.** The screenshot is dominated by an orange "Target reconnected ... Nothing was applied automatically" banner, and the pop-out section never mentions it. The report says "The README explains it"; that is false for this section. Add after line 183:
> - When the pop-out opens (and when you dock back), Studio may show the [reconnect banner](#reconnect-banner) if it holds saved edits that the fresh page does not have. Nothing is applied until you choose Reapply or Accept.

**I3. README.md:380-386 bookmarklet instructions.**
- "paste it into the address bar" is wrong in practice: Chrome and Firefox strip a pasted `javascript:` prefix, so it does nothing (you must type the prefix). The DevTools console also warns and asks you to type "allow pasting".
- The URL hard-codes port 8000. Anything else on that port (a Django or webpack server, say) becomes script code in the page you click it on.

Replace step 3 with:
> 3. In that window, run the bookmarklet. Save the line below as a bookmark and click it. Or open the DevTools console and paste only the part after `javascript:` (Chrome asks you to type `allow pasting` first). Browsers remove `javascript:` from text pasted into the address bar. The script URL uses port 8000; if you started the server with another `--studio-port`, change it, and click it only on pages you trust.

**I4. README.md:522-524 and repo root: "MIT." with no LICENSE file.** (Task D report concern 1.) `LICENSE` must be added (MIT text), or the line changed to "License: not yet specified."

**I5. README.md:239 FAQ overstates the file mode.** "Studio also opens from a file and works with Copy and Download." Download from `file://` was not exercised (report) and line 56 only claims inspector, Changes panel and Copy. Fix: "...and works with the inspector and Copy."

**I6. README.md:165 and :248 overstate the label/ARIA guard.** `referenceBreak()` (`fontkit-bridge.js:1330-1360`) only blocks a control leaving the `<label>` that wraps it, and only flags `label[for]`, `aria-controls`, `aria-labelledby`, `aria-describedby` when the move crosses a root (shadow root or document), because `id` references in one document resolve regardless of position. An ordinary same-document move cannot break them. Fix row 165:
> | `label-reference`, `aria-reference` | Taking a control out of the `<label>` that wraps it, or moving an element across a shadow-DOM boundary so a `label for`, `aria-controls`, `aria-labelledby` or `aria-describedby` link would stop resolving. |

and line 248: "...splitting a radio group, taking a control out of its wrapping label, or putting a block element inside a paragraph or button is refused...".

### Minor

**M1. README.md:191** button text is "Reapply Studio overrides" (`font_kit_studio_v0.1.1.html:1068`), not "Reapply Studio's overrides".

**M2. README.md:38** "Python 3.10 or newer" is not backed by anything in the repo (no code needs it; I ran on 3.11). Say "Python 3 (developed and tested on 3.11)". Commands use `python`; add "use `python3` if `python` is not found".

**M3. README.md:457** "does not ... send anything" contradicts line 423 (`design:bridge-ready` goes to parent/opener with `'*'`). Fix: "...block clicks, or send anything except a data-free `design:bridge-ready` to the window that framed or opened it."

**M4. README.md:148** Alt+Arrow works while the Target App view is active and focus is not in a text field, the sibling list, or the iframe (key events inside the iframe never reach Studio; `font_kit_studio_v0.1.1.html:4296-4302`). Reword: "...while Studio (not the preview iframe) has focus and you are not typing in a field".

**M5. README.md:166** content-model also covers `summary` as a parent. The bridge also has a non-listed `css-order` guard (CSS order needs a flex/grid parent and cannot move between containers). Add both for completeness.

**M6. README.md:272-293 Vue/Svelte coverage.** Verified against current docs (Context7): the Vite `transformIndexHtml` shape (`() => [{ tag, attrs, injectTo: 'body' }]`), `apply: 'serve'`, and the SvelteKit caveat match the Vite guide. Next.js `next/script` in the App Router root layout, `strategy="afterInteractive"` (default; it injects the element client-side after hydration) and `process.env.NODE_ENV === 'development'` are valid; `React.ReactNode` without an import is what create-next-app generates. Astro 5 needs `is:inline` for a conditionally rendered script, so the recipe is right. Gaps: SvelteKit and Nuxt (the usual ways to run Svelte/Vue) get no snippet, and the Next recipe is App Router only. Suggest adding, marked illustrative:
```svelte
<!-- src/routes/+layout.svelte (SvelteKit), illustrative -->
<script>
  import { dev } from '$app/environment'
</script>
<svelte:head>
  {#if dev}<script src="http://localhost:8000/fontkit-bridge.js"></script>{/if}
</svelte:head>
<slot />
```
and one line for the Next Pages Router ("put the same `<Script>` in `pages/_app.tsx`").

**M7. README.md:331** "Put the output in a stylesheet that loads after Tailwind" is unnecessary: every generated declaration is `!important`. Say "any stylesheet works, because every declaration is `!important`".

**M8. README.md:461** "It listens on loopback" is only the default; with `--host 192.168.1.20` it listens on that interface. Say "By default it listens on loopback".

**M9. README.md:8** "then copy the CSS": DOM moves come out as HTML, not CSS. Say "then copy the CSS and HTML".

**M10. README.md:198-202 privacy.** Loading free fonts contacts Google Fonts (the visitor's IP goes to Google). One sentence saying so is warranted for a "free by default" claim.

**M11. Screenshots (all legible, all under 300 KB: max 168 KB; no PNG text chunks, no paths, emails or secrets; only an ephemeral `localhost:4xxxx` port in the CSS comment).**
- `target-app-desktop.png`, `code-panel-*.png`, `bridge-bar`: the "edit" typed by `capture.py` is 64px, -0.03em, #b4231f, which equals the demo's own values (`demo/index.html:73-75`), so the hero shows no visible change while the README says "Changes". Use a visibly different edit (e.g. 72px and a green) in `capture.py`.
- `arrange-guard-desktop.png`: the preview is cropped so the Subscribe button's selection label is cut off at the top; `arrange-desktop.png` and the mobile shots show sticky Library/Composer tabs overlapping content. Acceptable, but scrolling the preview so the whole form shows would be better.
- `target-app-mobile.png` shows an iframe about 350 px wide; fine as a layout proof.

**M12. Integration test hygiene (none causes a current failure).**
- `BookmarkletTests.BOOKMARKLET` is a hand-copied string. If the README snippet changes, the test still passes. Parse it from `README.md` (the `javascript:` line) instead; it also uses the target port while the README uses the Studio port.
- It injects immediately; add `self.wait_badge(page, r'^No bridge detected$', ...)` before `popup.evaluate` (I verified it passes).
- `popup.wait_for_event('close') if not popup.is_closed() else None` is racy (popup may close between the two calls, giving a 30 s timeout). Use `popup.wait_for_function`-free polling or `expect_event` wrapped around the Dock click.
- `click_in_target` swallows any exception on the first attempt; fine, but narrow it to `PlaywrightTimeoutError`.
- The plain-HTML README tag (absolute `http://localhost:8000/...`) is never exercised as written (the demo uses `../fontkit-bridge.js`); only the bookmarklet test loads an absolute URL.
- Firefox and the clipboard paths were not run (D010); the README says so.

**M13. docs/roadmap/browser-extension.md (technically sound; three precision fixes).**
- Permissions row omits `sidePanel`, which `chrome.sidePanel` requires. Add it.
- "Reusing [Studio] as-is may be too heavy" is understated: Studio is one HTML file with a large inline script, and MV3 extension pages forbid inline scripts under the default CSP. Say it cannot be reused unchanged and needs its script split into a file.
- Security says "The extension makes no network requests of its own", but the free-font library and `fontStylesheet` load Google Fonts CSS. Add "apart from the Google Fonts stylesheets the user asks for".
- `executeScript({ world: 'MAIN' })` needs Chrome 111 or newer; worth stating. Everything else (`activeTab` + `scripting`, temporary grant, a side panel being neither parent nor opener, content-script relay changing the trust model, Firefox deferred) is accurate and honest.

**M14. Demo change (accessible, offline, realistic).** Real `<label for>`, `<fieldset>` with `<legend>`, native radios kept (opacity 0, overlaid, visible `:focus-visible` ring on the pill), `required` email, `aria-labelledby` on the section, no script, no network (`test_demo_source_is_offline` passes). `action="#newsletter" method="get"` just reloads with a query string; fine for a demo. Nit: `.pill-group` labels have no `:hover` state; not worth changing.

## Claims verified true (no change needed)

Dev-server flags and defaults, 421 for LAN hosts, one `.css` file inside the repo, 1 MiB limit, `no-store`; status badge strings and the 4 s timeout; inspector control ranges and snapping; patch keys (`fontSize` 4-400, weight 1-1000, line height 0.5-5, tracking -0.5-2 em, `text` 5000, colour forms, `fontFamily` charset rules, Typekit and Google URL gates); download filenames; Move strategy names and defaults; guard ids `form-owner`, `radio-group`, `content-model`, `framework-managed` (only this one overridable with **Move anyway**); pop-out status messages (`Pop-up blocked: ...`, `Disconnected (window closed)`); Adobe kit preset text; `window.__fontkitBridge`, `FONTKIT_BRIDGE_OPTIONS`, `data-allowed-origins`, `data-auto-init`, `initFontKitBridge`, the option list; `--font-sans/-display` tokens; message list (all message types exist in the bridge); `git remote` URL; all links, anchors and image paths resolve; JSON `version` 0.1.1.

## Assessment

The tests are real, fail when the feature breaks, and are stable (single 36 s run, no fixed sleeps, nothing left behind). The README is accurate on nearly every command, flag, id, message and limit I checked, and meets every listed content requirement. The work to do is wording: the pop-out "window" claim, the unexplained reconnect banner in the pop-out screenshot, the bookmarklet paste instructions and fixed port, the guard overstatement for id references, the file-mode Download claim, and the missing LICENSE file. None changes code. Roadmap is honest and sound with three precision fixes.

**Task quality:** Approved with fixes

---

# Re-review after first changes (read-only)

Reviewed the uncommitted working tree on top of the docs commits following Task F. Direct source, runtime evidence and diffs only. I made no repo edits other than this appended section.

## Gates (Chromium only, `FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests` | **Ran 200 tests in 337.4 s, OK** |
| `python3 scripts/verify.py --static-only` | PASS: 86 unique IDs, 1 inline JS block, Studio sha256 `1b783e8c...76df`, provenance x3 |
| `node --check fontkit-bridge.js` | OK |
| `git diff --check` | clean |
| `ps aux \| grep serve.py` after every run | none; `work/` empty; `git status` shows only the expected files |

## My earlier items

| Item | Verdict |
|---|---|
| I1 pop-out is a real window | **Fixed.** `popoutFeatures()` (`font_kit_studio_v0.1.1.html:4402`) passes `popup=yes,width,height,left,top`, capped by the screen, name kept. Both the stubbed test and the real Chromium integration test assert the 3rd argument, and the integration test asserts the popup's `innerWidth/innerHeight` equal the requested size. README wording ("asks your browser... some settings open a tab") is accurate. |
| I2 reconnect banner explained | **Fixed** (README pop-out bullet; the pop-out screenshot is now taken before any edit, shows `Changes 0`, no banner). |
| I3 bookmarklet | **Fixed.** Wording is right (bookmark, or paste the part after `javascript:` into the console; address-bar paste explained; port-8000 and trust cautions). `BookmarkletTests` now parses the `javascript:` line and the plain `<script>` tag from README.md, swaps port 8000 for the test's Studio port, waits for Studio's own second "No bridge detected" like a person, and checks that running it twice adds one script. New test loads a page that has only the README tag, served from the scratch folder by the real server. |
| I4 LICENSE | README now says "License: not yet specified... all rights are reserved by the author." Honest; no file added at that point (a licence decision was pending). Accepted. |
| I5 Download from file | **Fixed** (FAQ now "works with the inspector and Copy"; line 56 consistent). |
| I6 guard rows | **Fixed and accurate.** The `label-reference`/`aria-reference` row matches `referenceBreak()`; `content-model` lists `summary` and "cannot be overridden"; `css-order` guard added; the seven `detail.reason` strings in the protocol table all exist in the bridge (checked each). |
| M1 Reapply label | **Fixed** ("Reapply Studio overrides"). |
| M2 Python | **Fixed** ("Python 3... developed and tested on 3.11... use `python3`"). |
| M3 "send anything" | **Fixed** (Security "Inert by default" now names `design:bridge-ready`). |
| M4 Alt+Arrow | **Fixed** (Studio focus, not typing in a field). |
| M5 content-model/css-order | **Fixed.** |
| M6 SvelteKit/Nuxt/Pages Router | **Added**, marked illustrative. SvelteKit `dev` from `$app/environment` in `<svelte:head>` and Nuxt `app.head.script` are valid in my knowledge; the client-only caveat is honest. Not run (stated). |
| M7 Tailwind `!important` | **Fixed.** |
| M8 "loopback by default" | **Fixed** (also `[::1]` dropped, as the sweep suggested). |
| M9 tagline | **Fixed** ("copy the CSS and HTML"). |
| M10 Google Fonts privacy | **Added.** |
| M11 screenshots | **Fixed**, see below. |
| M12 test hygiene | **Fixed**: README parsing, wait for the 4 s state, `expect_event('close')` around Dock, narrowed retry. |
| M13 roadmap | **Fixed** (`sidePanel`, Chrome 111, MV3 inline-script limit, Google Fonts network qualification). |
| M14 demo | unchanged, still fine. |

## Sweep items

| Item | Verdict |
|---|---|
| M1 inspect/ping | **Done.** `grep` for `design:inspect|design:ping|pong|inspect-result|handleInspect` in README, bridge, Studio, docs, tests is empty (only an unrelated "ping-pong" comment in a fixture). `capabilities.inspect` kept. |
| M2 "checked" text | Accurate except one understatement: it says the `data-allowed-origins` script attribute has "no test yet", but `tests/fixtures/bridge/target-restricted.html` uses it and `RESTRICTED_PAGE` is exercised in `test_bridge_runtime.py`. (The other listed options and `data-design-kind` truly have no test; the overlay, `data-auto-init`, `FONTKIT_BRIDGE_OPTIONS`, `allowedOrigins` claims are backed by fixtures.) See Minor R1. |
| S1 one token rule | **Done.** Bridge `TOKEN_NAME = /^--[a-z0-9-]{1,120}$/`, Studio `CUSTOM_PROPERTY` identical; `invalidTokenInPatch()` runs before anything is applied and replies `design:rejected` / `unsupported-value` with `detail.property`; the bridge test loops 13 bad tokens, asserts revision 0 and an untouched `documentElement.style`, and covers the `sans` shortcut and the 120-char boundary. The integration test refuses `--Brand-Ink`/`--brand_ink` at import, then valid token -> banner -> Reapply -> property set -> banner hides -> JSON keeps it. I accept the controller's ruling that values are rejected as well as names, and that `fontkit:change` still drops an unsafe font silently (legacy, no reject message). |
| S2/S3 | **Done.** One `unsafeCssText` (+ `{selector:true}` which strips only `\"` and `\\` pairs, so it cannot let a dangerous character through) used by font family, imported tokens and `safeCssText`. `safeFontStylesheet` and the percent-escape regex are now byte-identical to the bridge's (8 families, one `display`, one `text` up to 600, `~` allowed). Studio is slightly stricter (newline, comment markers, `!important`), which is the safe direction. Shared-rules test with a hostile ledger passes. |
| S6 | **Done.** `readStore`/`writeStore` are the only `localStorage` users (grep confirms); the throwing-getter test covers start-up, Composer render, auto-connect and both kit loaders. |
| S7 | Dead payload fields `familyRaw`, `layout.canvasWidth`, `layout.backgroundHex` removed and asserted absent. **`targetId`: judged acceptable but unfinished.** Nothing in Studio (nor the supplied v0.1.1) ever sets `slot.targetId`, so `targetId:slot.targetId` at `font_kit_studio_v0.1.1.html:4713` is always `undefined` and is dropped by `JSON`. The bridge's direct-id branch is legitimately kept (contract plus legacy tests). Either remove the field from Studio's payload or add a one-line comment saying it is an unused hook for the bridge branch; today it reads like a live field. Minor R6. |
| S8 | **Done** (`import os`, `list_ids` gone; unused-`byName` also gone). |
| Dead code removal | `registerElementTarget` (public in Spec 4.2 level 2) plus its `explicit` WeakMap removed. It had no caller, no test and no README mention, and no Spec text outside a plan defect note references it, so removal is consistent with the sweep; but it is a public-API deletion. Worth one line in `deviations.md` (the controller owns that). `FRAMEWORK_GUARDS` alias removed, fine. |
| Fake target | `data-design-name` now used (and `containerName()` reads it). |
| `.gitignore` | `.*.css.*.tmp` matches the `.{name}.XXXX.tmp` files `write_atomic` makes for any `*.css` overrides name. Correct. |
| Anti-recursion | I probed it in real Chromium. Studio's own URL with trailing slash, `?a=1`, `#x` and `/#x` -> `Recursion blocked`; a target with `?project=font-kit-studio` now connects. **Regression to note (Minor R2):** it compares only href-without-query/fragment, so the same document under another host alias is no longer blocked: `http://127.0.0.1:<port>/font_kit_studio_v0.1.1.html` and an upper-cased path both reach `Connecting...` (the old name regex blocked these). `http://localhost:<port>/` (which `serve.py` redirects to Studio) was never blocked. A nested Studio is only reachable by typing it, so this is low risk. Suggested fix: also block when the origin's hostname is a loopback alias (`localhost`, `127.0.0.1`, `[::1]`) with the same port as `location` and the path (case-insensitive, trailing slash and query ignored) equals `location.pathname`. The new test does not include a trailing-slash probe, although the logic handles it. |

## README: diff spot-check of every changed claim

Verified against code or runtime: `popup=yes` window request; "asks... the browser decides"; reconnect banner text; Sync to Live App disclosure (`orderContainers` includes `main`, and the bridge sets an unreported `transition`/`order` with `ledger:false`; "Reload the preview to undo it" is accurate and better than "Reset", which Studio has no global control for); composition token rule and rejection row; message tables (no inspect/ping/pong); the seven rejection reasons; `css-order` guard; "Restore Page Text in the bar" (button `#btnRestoreOriginalText`); bridge-ready sentence; privacy sentence; SvelteKit/Nuxt/Pages Router additions; the revised "how these recipes were checked" paragraph (except R1); roadmap text; license line. All links, anchors and images still resolve.

## Screenshots (viewed all nine; all under 170 KB, no text chunks, no personal data; only an ephemeral `localhost:3xxxx` port in a CSS comment)

- `target-app-desktop`: hero is visibly edited (72 px, -0.04 em, green) and the CSS panel matches; the hero lead is clipped at the preview's bottom edge (cosmetic).
- `arrange-desktop`: CTA selected, First/Earlier disabled, strategy toggle and sibling list readable. The Changes panel still shows the hero edit, which is fine.
- `arrange-guard-desktop`: now a clean shot: the whole newsletter form, the Subscribe selection label and the `form-owner` message are all visible.
- `pop-out-desktop`: no banner, `Changes 0`, docked placeholder with Focus pop-out/Dock back.
- `code-panel-desktop`, `bridge-bar-desktop`, `code-panel-mobile`, `target-app-mobile`: legible and consistent with the README text; `arrange-mobile` unchanged and fine.

## New issues

All Minor. Nothing blocks a commit.

- **R1. README.md:268** says the `data-allowed-origins` script attribute has "no test yet". It is covered by `tests/fixtures/bridge/target-restricted.html`. Fix: remove it from the untested list: "...the other options (`autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied`) and `data-design-kind` are implemented but have no test yet."
- **R2.** Anti-recursion host-alias regression (above).
- **R3. README.md patch-keys row `fontFamily`** omits `expression(` (the bridge also refuses it). Add "`url(` or `expression(`".
- **R4. README.md:34** "The font library is now free Google Fonts" uses release-history wording; "The font library is free Google Fonts" reads better.
- **R5.** `registerElementTarget` removal deserves a deviations line (public Spec 4.2 level 2 API deleted as dead code).
- **R6.** `targetId:slot.targetId` in Studio's composition payload is permanently `undefined`; remove it or comment it.
- **R7.** An invalid composition token now rejects the entire Sync to Live App, and Studio surfaces the rejection reason generically (`Rejected: unsupported-value`). Studio only ever sends the four `--font-*` roles plus validated tokens, so ordinary use cannot trigger it; no action beyond awareness.

## Verdict

All earlier Important items, the sweep's M1, M2, S1, S2/S3, S6, S7 (with R6), S8, the fake-target, `.gitignore` and the screenshot recapture are verified fixed with tests that exercise the real behaviour. README claims in the diff check out against code. The anti-recursion change keeps the required variants blocked but loosens host-alias protection (R2).

**Task quality:** Approved with fixes (all remaining items are Minor: R1-R6, none blocks commit)

---

# Re-review after second changes (read-only)

Reviewed the working tree after the Task D commit and the MIT `LICENSE` commit. Direct source and diffs only; no repo edits besides this section.

## Gates (Chromium only)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests` | **Ran 201 tests in 365.7 s, OK** |
| `python3 scripts/verify.py --static-only` | PASS: 86 unique IDs, 1 inline JS block, Studio sha256 `0d75f190...40ab`, provenance x3 |
| `node --check fontkit-bridge.js` / `git diff --check` | OK / clean |
| Leftovers | no `serve.py` process; `work/` empty; `git status` shows only the four modified files (README, Studio, integration test, Task D report) |

## Verdicts

- **R2 (self-embedding).** `isStudioDocument()` (`font_kit_studio_v0.1.1.html:3348`) blocks when either the href without query, fragment and trailing slash equals Studio's, or both hosts are in `["localhost","127.0.0.1","[::1]"]` with the same protocol and port and equal paths ignoring case and a trailing slash. Checked: `location.hostname` and `URL.hostname` both give `[::1]` in brackets, so the comparison is consistent; default ports compare as `""`; `file:` Studio falls back to the href comparison (hostname is empty, so the alias branch cannot fire); the pop-out goes through the same `resolveTarget()`. Not over-blocking: a different port, a different path (`/demo/`) and `?project=font-kit-studio` are all untouched. The new real-server test blocks `127.0.0.1`, `[::1]`, upper-cased path, upper-cased with query and fragment, trailing slash and `?x=1`, and asserts the demo on the other port through `127.0.0.1` with `?project=font-kit-studio` still connects. **Fixed.** Remaining notes (informational, no action required):
  - `http://localhost:<studio port>/` (which `serve.py` redirects to Studio) and a percent-encoded path such as `font%5Fkit...` are still not blocked; neither was blocked before round 1.
  - `serve.py` serves the repo on both ports, so `http://localhost:<target port>/font_kit_studio_v0.1.1.html` is Studio under another port and is now allowed (the pre-round-1 name regex blocked it). That is the deliberate price of not blocking unrelated apps on other ports; typing it nests Studio once, harmlessly.
- **R6.** `targetId:slot.targetId` is removed from the composition slot payload (`:4723`). It was always `undefined` and dropped by JSON, so the wire message is unchanged; the bridge's legacy `slot.targetId` branch and its tests are untouched. **Fixed.**
- **R1.** `data-allowed-origins` is now in the tested list (`target-restricted.html`); the untested list (`autoDiscover`, `autoDiscoverSemantic`, `enableClickToSelect`, `tokens`, `onApplied`, `data-design-kind`) matches my earlier grep. **Fixed.**
- **R3.** `fontFamily` row now lists `url(` and `expression(`, which matches `UNSAFE_CSS_STRING`. **Fixed.**
- **R4.** "The font library is free Google Fonts". **Fixed.**
- **License.** `LICENSE` exists (MIT, "Copyright (c) 2026 pterw"); README links it, and the OFL note about the logo outlines is true (`docs/assets/README.md` lists Source Serif 4, Fraunces, Courier Prime and Inter under OFL 1.1). No stale "not yet specified" text remains. **Fixed.**

No new issues found. R5 (a deviations line) and R7 remain open as records only.

## Verdict

**Task quality:** Approved
