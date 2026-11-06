# Audit: Font Kit Studio on two real apps (2026-11-06)

Observations of released 0.4.0 on `main` at `5bd655e1cf5b891b960902d7836b3e756bcbb625`, run against two apps it was not tuned
for: ScrobbleScope (Flask, Jinja2 templates, Tailwind 4 with DaisyUI, vanilla JavaScript, Typekit fonts) and PokeCipher
(Next.js 16, React 19, Tailwind 4, shadcn components, `next-themes`, `next/font`). It feeds the 0.4.1 plan. It fixes nothing and
changes no product file.

## Summary

Font Kit Studio attaches to both apps with no hooks, by `serve.py` and by the npm package. Pages, cookies, fonts, polls
and stopping behave as they do without it, apart from one added script tag. Tagged HTML also gets `Cache-Control: no-store`
and loses its `etag`. Detect finds the real type system on both apps. On ScrobbleScope's `/`, Preview, Apply and Clear leave
the page as it was; they were not run on `/results`. On PokeCipher a refused Clear can leave the preview on the page
(`D2-10`). Inspector edits, resets, structural moves and the exported CSS work. The
exported CSS reproduced the edits on a direct page of both apps.

What does not work is mostly where a real app differs from the shape Studio was written against. Sync to Live App writes fixed
token names that PokeCipher does not read, and says it applied them. PokeCipher's blinking cursor makes Detect, Apply and Clear
report "page changed". An edit on a node React replaces is lost without a word. After the app rewrites an edited text, Reset
puts back stale text. Auto-discovery skips most form text. Error pages get no bridge, and the hint blames the wrong cause. Studio
lists none of the page's CSS tokens.

**Severity key.** S1: a real user cannot finish the flow. S2: a wrong or misleading result, or lost work. S3: a rough edge with
a way out. S4: a note. No S1 was found.

Fix first: the four S2 defects, which take six rows because `B08-b` and `D2-11-b` are the full repairs of `B08` and
`D2-11`. In this order: `C1-1` (the first Detect fails on any page with a closed `<details>`; S3, but it is the first thing a user meets on any such page), then `D2-10` (a repeating text change makes Clear refuse and leave the preview on the page), `D2-11` (an
edit on a node the app replaces is lost with no warning) and `B09-b` (Reset puts back stale text), then the warning on
`B08` (Sync reports tokens applied that PokeCipher does not read). The 24 rows homed to 0.4.1 are the next release's list.

A finding is a row whose independent check confirmed it or found it overstated (counted at the checked severity), a row from a
live run with status defect or gap that no check rejected, or a row from a code read that no check covered (counted in its own
column). Rows that were false, or that repeat documented behaviour, are listed once under Known and documented or under Checked
and rejected, and never counted. Rows that describe one defect are merged and counted once. Two rows (`B08-b`, `D2-11-b`) are
repair rows for a counted finding and are counted like any other row.

| Severity | Checked on a run or by an independent check | Source read only | Total |
|---|---|---|---|
| S1 | 0 | 0 | 0 |
| S2 | 6 | 0 | 6 |
| S3 | 20 | 10 | 30 |
| S4 | 16 | 22 | 38 |
| Total | 42 | 32 | 74 |

The findings table has 74 rows. By home: 24 for 0.4.1, 4 for 0.4.2, 3 to size at 0.4.2 and 43 for later.

## Scope and method

Commit `5bd655e` (0.4.0 plus its publication record). IDs number the audit's own checks: A for attach, B for the line-by-line
read of the bridge, C and D for Studio on ScrobbleScope and on PokeCipher, E, G and H for code and record reads, F for rows
carried over from the earlier audits, S for the line-by-line read of Studio. D followed by a digit is also a decision number in
`docs/implementation/deviations.md`; the context says which.

- Engine: Chromium 151 only, driven through Playwright at 1440 x 900, a fresh context per script, on Windows 11. The npm package
  was `fontkitstudio@0.4.0` on Node 24. `serve.py` ran in proxy mode with `--no-sync`.
- ScrobbleScope was served by its own dev server on port 5000 and reached directly and through each path. A small number of
  Last.fm lookups ran (at most three per run) for one account and one period.
- PokeCipher was served as its production build with its API up. One run under `next dev` supplied the hydration row
  `D1-10a` and was not repeated. Production has no hot reload and no development overlays, so those were not reached.
- Basis column below: `checked` is a live run or an independent check; `source` is a code read that no check covered. Rows
  from the code reads of the proxy and CLI count as `source` even where a command was run (for example `E-1a`).
- Rows labelled "independent check" were re-run in a browser, or in a probe page that loads the real bridge, before the verdict
  was written. Rows from a line-by-line read that no check covered are marked "source read only".
- Not reached: absolute `Location` rewriting (neither app sends one), streaming and WebSocket (ScrobbleScope has none; production
  PokeCipher has none), cookies and CSRF on PokeCipher (none), a second route and client navigation on PokeCipher, reload and
  reconnect on PokeCipher, Sync to file on PokeCipher.
- `/results` gap: on ScrobbleScope's `/results`, Detect ran, but Apply, Clear and reset were not run there. Live inspector edits
  were run on `/` only.

## Attach results

`serve.py` and the npm package against ScrobbleScope, item by item, then both against PokeCipher (production).

| Item | serve.py on ScrobbleScope | npm 0.4.0 on ScrobbleScope | Same? | Both paths on PokeCipher |
|---|---|---|---|---|
| Command and time | Four lines, `Open:` last, at 0.28 s; Studio connected 0.54 s later | Two lines, `Open:` after about 3.3 s on a cold cache; no `App:` line | Different output and ports | serve.py `Open:` at 0.22 s; npm at 2.62 s; connected 0.6 s later |
| Fidelity of `/`, `/results`, `/heatmap` | Same fonts, text, console (no errors), failed requests (none); +1 element, +1 request, +97 bytes (the tag); `/heatmap_data` byte-equal | Same; `/` screenshot identical | Same | Same fonts, 0 console errors; 221 vs 222 elements, 15 vs 16 requests |
| Error pages (404, 400) | Identical to direct; no bridge | Identical, but the console reason phrase changes case (`Not Found`) | Same, apart from case | Not requested |
| Bridge | One tag first in `<head>` on 200 pages; asset served by the proxy; `Connected (44 targets)`; back navigation reconnects | Same; `Connected (44 targets)` on `/`, 53 on `/results` | Same | One tag; `Connected (21 targets)` |
| Error page in Studio | "No bridge answered ... within 4 s", hint blames a missing tag | Same, with an npm hint | Same (see the first S3 row) | Not reached |
| Headers | Tagged HTML gets `Cache-Control: no-store` and a new `Content-Length`; static files, 404, 400 untouched | Same on HTML; two `Date` headers on static files come back as one comma-joined value | Different on static files | `no-store` replaces `s-maxage`; `etag` dropped; gzip decoded on both; serve.py also closes the connection |
| Sessions and CSRF | Cookie kept; empty form 200 with message; no token gives 400; a real lookup works | Same | Same | None to test |
| Redirects | Not reached: the only redirect is relative | Not reached | Not reached | Not reached |
| Polling | 40 `/progress` samples equal to direct in status and length | 148 side-by-side polls, bodies equal | Same | `/api/names` equal on both paths |
| Fonts | Six Typekit faces load; requests go from the browser, not the proxy | Same | Same | Press Start 2P and VT323 load alike; Studio's own page makes no third-party request on load |
| Stopping | `Stopped.`, exit 0 in 0.5 to 1.2 s | All four processes gone in 2.35 s | Same result | serve.py exit 0 in 0.52 s; npm all processes gone, no forced kill |

## Findings

Sorted by severity, then by basis; within those, roughly by surface. The Home column
names the rule that decided it. `0.4.1`: a repair of behaviour that exists today and misleads or loses work, or a small fix
(a warning, a message or a one-line fix counts). `0.4.2`: the pip wrapper, listing page tokens and wider auto-discovery.
`size at 0.4.2`: decided when the 0.4.2 plan is written; bundled into 0.4.2 only if the work proves small. `later`: new
capability and structure notes.
**Four rows belong to 0.4.2: `E-15`, `C2-2d`, `C2-3a` and `B17`.** Applies to: ScrobbleScope, PokeCipher, both, any app,
neither (mechanism real, no occurrence found on either app) and none (record text). A line number alone is
`fontkit-bridge.js`, `fontkit-studio.html` or `scripts/serve.py` as the row's first cause names it. `PUB` is the record-text
row (no source ID).

| ID | Sev | Basis | Applies to | What a user sees | Cause at BASE | Evidence | Home |
|---|---|---|---|---|---|---|---|
| B08, D2-4, G1-4, G2-10 | S2 | checked | PokeCipher (ScrobbleScope partly) | Sync: Sync to Live App writes fixed names (`--font-display`, `--font-sans`, `--font-serif`, `--font-mono`) and reports them applied; PokeCipher text reads `--font-terminal` and `--font-pixel`, so no element changes and Changes shows 3. On ScrobbleScope `--font-display` lands but body text does not follow | fontkit-studio.html:6836-6857; fontkit-bridge.js:124-128, 2981-2987 | Production run: families equal before and after Sync. PokeCipher's compiled CSS has no `--font-sans` reader. The line-by-line read (B08) said Studio lists `--font-terminal`; that is unconfirmed, because the live runs (D2-4, C2-3a) show Studio lists no page tokens | 0.4.1 (warning when a token is written and no element changed) |
| B08-b | S2 | checked | PokeCipher | Sync: the full repair of the row above, writing the token names the page reads | same as above | needs the page token list (C2-3a) | later (new capability) |
| D2-10, S06 | S2 | checked | PokeCipher | Detect: PokeCipher's cursor text changes about every 600 ms and the bridge counts it as a page change. All 4 Detects ended "The page changed since the last Detect"; in 8 Apply and Clear cycles 3 Clears and 1 Apply were refused, and a refused Clear left the preview on the page. A class change on `<html>` during Detect ends a press the same way (S06; injected, no real trigger on either app) | fontkit-bridge.js:1265-1269, 1321, 1545; fontkit-studio.html:4477 | Production, twice; the cursor span toggles 10 times in 6 s with Studio absent | 0.4.1 (repair: a repeating text change must not refuse Clear) |
| D2-11 | S2 | checked | PokeCipher | Live edit: a size and text edit on a node React removes (the output line after Encode) is gone after Clear; the new node has the app's size; Changes still shows 1; no warning. The export still carries the rule | fontkit-bridge.js:3395, 3462-3466 | Production, twice identical. The re-render recovery (tests/test_bridge_runtime.py:2861) runs only for author ids; auto ids are dropped | 0.4.1 (warning) |
| D2-11-b | S2 | checked | PokeCipher | Live edit: the full repair, re-applying the edit to the re-created node of an auto-id target | same as above | as above | later (new capability) |
| B09-b | S2 | checked | PokeCipher | Live edit: after the app rewrote an edited text, Reset this element shows the old text while the app's state says otherwise, until the next update | fontkit-bridge.js:3005-3044 | Production, twice identical (hint line, type a name, Reset). Found while checking B09 | 0.4.1 (repair: restore what the app shows) |
| A1-3b, A2-3b | S3 | checked | ScrobbleScope | Attach: on an error page (404, 400) the proxy adds no bridge; Studio says "No bridge answered within 4 s" and tells the user to add the script tag. Going back reconnects | scripts/serve.py:567; packages/fontkitstudio/src/proxy.js:223-227 | Both paths on `/nope` and `/loading`. Pinned untagged by tests/test_serve_proxy.py:111 and packages/fontkitstudio/test/proxy.test.js:266 | 0.4.1 (message: name the error page) |
| B01 | S3 | checked | neither | Attach: a hashed `type="module"` bundle that carries `data-allowed-origins` loses the list; any origin is accepted and nothing says so. A classic script tag keeps it | fontkit-bridge.js:74, 571 | Probe page. Neither app loads the bridge as a bundle. Ways out: `window.FONTKIT_BRIDGE_OPTIONS` or `new FontKitBridge({allowedOrigins})` | 0.4.1 (warning when the list cannot be read) |
| C1-1 | S3 | checked | ScrobbleScope | Detect: the first press after Connected ends "Incomplete detection (page-changed)" though nothing changed; the second completes. Text in a closed `<details>` is not drawn at the start of the scan and is at the end. Also on the bundled demo | fontkit-bridge.js:2175-2185 | `/`: 5 of 5 fresh runs fail once, then 19 roles from 53 parents. Opening the disclosure first makes the first press complete. `/results` has no `<details>` and completed. S06 is not the cause (no mutation was recorded) | 0.4.1 (repair) |
| B04, C1-11 | S3 | checked | both | Detect: a Tailwind utility class is shared by unrelated elements, so roles bind through short or very long dom-path selectors (`.text-xl`; arbitrary-value chains of 300+ characters marked uncertain); a group over 32 members gets no binding | fontkit-bridge.js:1927, 1960-1965 | Probe: 12 `text-sm` paragraphs give 12 selectors, 40 give none. ScrobbleScope `/results` Detect lists the long chains. Apply through them was not tried on `/results` | later (structure: Tailwind-aware binding) |
| B13 | S3 | checked | neither | Detect: a CSS Modules class in a scheme the pattern misses (`Button_root__a1B2c`, `Button__root--a1B2c`) is bound as durable; after the next build the role matches nothing, unmarked | fontkit-bridge.js:1961 | Pattern run on 7 names. Next's current scheme is from memory, not measured. Tests pin the Vite form only (tests/test_role_detection.py:279). No CSS Modules in either app | later (the scheme must be measured first) |
| B17 | S3 | checked | neither | Discovery: a `<p>` outside `header`, `main`, `article`, `section` is never a selectable target (next to a heading it is arrangement-only). Both apps keep `<p>` in `main`. Related to C2-2d (same list, other elements) | fontkit-bridge.js:114-120 | Probe page, 3 shapes | 0.4.2 (same list as C2-2d) |
| D1-10a | S3 | checked | PokeCipher | Attach: under `next dev`, the bridge's auto attributes reach the page before hydration, so React logs a hydration mismatch on the `h1` (`data-design-id`, `data-design-role`, `data-design-name`) and does not patch it up. Absent in three production loads | fontkit-bridge.js:3425-3435 | One dev-server run through Studio; three production loads clean | 0.4.1 (repair; size confirmed in the plan) |
| C2-2d | S3 | checked | ScrobbleScope | Discovery: on `/`, 23 spans, 10 labels, 6 `dt`, 6 `dd`, 2 `em` and 2 `small` with visible text are not targets; clicking a label selects nothing | fontkit-bridge.js:114-120 | Run on `/` (44 targets). Related to B17 | 0.4.2 (wider auto-discovery) |
| B09 | S3 | checked | PokeCipher (heading case: shape only; seen live on a paragraph, B09-b) | Live edit: for a heading with one string child, Studio's text edit is overwritten when the app changes the string; an unchanged string keeps it. A multi-node child keeps the edit through data changes. Related to B09-b | fontkit-bridge.js:3020-3033 | React 19.2.4 page in Chromium. The leaf paragraph edit held in production | later (structure) |
| S01 | S3 | checked | any app | Live edit: after a reload Studio still holds a saved DOM move (the banner says so), yet "Reset this element" is disabled with "No changes on this element." | fontkit-studio.html:7197-7201 | Fixture app, twice; the same flow as C2-7a on ScrobbleScope. Reapply or Accept is the way out | 0.4.1 (one-line fix: test the saved order too) |
| S02 | S3 | checked | neither | Live edit: for `rgba(108,102,118,0.6)` the text box reads `#6c667699` and the swatch `#6c6676`; moving the swatch writes an opaque colour | fontkit-studio.html:3736 | Fixture, twice. ScrobbleScope source has alpha colours; none was shown on a target | 0.4.1 (small fix) |
| S03 | S3 | checked | neither | Live edit: for an element whose line height is `normal`, the inspector shows 1.2; the first keystroke writes 1.25 | fontkit-studio.html:5922 | Fixture, twice. tests/test_studio_live.py:408 only covers a set line height | 0.4.1 (small fix) |
| S04 | S3 | checked | neither | Live edit: an app that re-renders a hand-written `data-design-id` node six or more times in 2 s loses the edit after the bridge's cap; the page shows its own size, the inspector 60, Changes 1, no banner; re-entering the same value sends nothing | fontkit-bridge.js:86-88, 3403-3412; fontkit-studio.html:5997-5998 | Fixture: 14 re-renders at 200 ms, twice. Neither app writes author ids; PokeCipher's cursor would not reach the cap | later (a value Studio cannot confirm; the repair is not a warning) |
| B14 | S3 | checked | neither | Move: the guard misses `li`, `pre`, `dl`, `fieldset`, `figcaption`, `hr`, `main`, `dt` moved into a `<p>`; the move is applied and the parser re-nests it on reload | fontkit-bridge.js:2673, 94-96 | Chromium with the real parser. A `div` into `em`, `code` or `strong` stays nested and is fine | 0.4.1 (small fix: extend the list) |
| B15, G1-3 | S3 | checked | both (shape only) | Sync: a Body slot restyles the first element whose `data-design-id` contains "body", not the slot's own paragraph; slot lookups use ids named after one earlier app's layout (`hero.title`, `brand.wordmark`). Studio does send this path | fontkit-bridge.js:4181-4245, 4196-4198, 4120 | Probe: three `<p>` give one restyled. The substring rule is documented (README.md:420). ScrobbleScope Sync sent no top-level Body slot, so no paragraph changed | later (new capability: slot placement) |
| S07 | S3 | checked | any app | Sync: with Colour source set to Tailwind (not the default), Sync writes `oklch(...)` inline; the inspector cannot show, replay or export it. See the oklch row below | fontkit-studio.html:6864 | Frame inspected, twice | size at 0.4.2 |
| S09 | S3 | checked | ScrobbleScope | Sync: with a Row or Image slot first, `--font-display` is set to a family no text slot uses | fontkit-studio.html:6847 | Preset with the Row moved up, twice; control without the move | 0.4.1 (small fix: skip non-text slots) |
| C2-3a | S3 | checked | both | Studio: lists none of the page's CSS tokens, though the bridge sends them in the handshake; Changes stays empty until an edit | fontkit-bridge.js:3863; fontkit-studio.html (no reader of the list) | ScrobbleScope and PokeCipher runs; search of Studio finds only the ledger | 0.4.2 (lists page tokens) |
| C2-8b | S3 | checked | ScrobbleScope | Export: selector chains carry state classes (`.is-active`, `.active`); after the page's own pill switches, the pasted rule matches nothing and no warning says so | fontkit-bridge.js:3220-3278 | Run: after the mode switch the visible heading read 33.86 px again | 0.4.1 (repair of what users export) |
| PUB | S3 | checked | none | Record: the publication record sentence about the last product-code commit says only the screenshot script changed after it; seven later commits touched three product files (549 insertions, the Python proxy among them). Later lines of the same file are right | docs/implementation/verification-r2.md:5-6 | Ancestry check and diff stat | 0.4.1 (small fix: reword) |
| E-1a | S3 | source | any app | Attach: `serve.py <url> --studio-port 0 --target-port 0` exits 2 "must differ", though 0 means OS-assigned for npm | scripts/serve.py:726-727 | Argument-error run | 0.4.1 (message) |
| E-1b | S3 | source | any app | Attach: npm refuses `--studio-port 0`, though omitting the flag means 0. Pinned as intended | packages/fontkitstudio/src/cli.js:22-30 | Argument-error run; packages/fontkitstudio/test/cli.test.js:107-108 | later (contract change) |
| G1-2 | S3 | source | any app | Code: `design:highlight`, `fontkit:change` and `fontkit:ack` are handled but Studio never sends them (documented as legacy) | fontkit-bridge.js:4028, 4104 | Search of Studio: no hits | later (structure) |
| G1-5 | S3 | source | ScrobbleScope | Discovery: `[class*="stat"]` also matches `static`, `status`, `state`; each match becomes a target and gets attributes written into the app's DOM | fontkit-bridge.js:114-120, 3425-3441 | Templates carry such classes; count not measured | 0.4.1 (small fix: whole class names) |
| G1-7, G2-9 | S3 | source | neither | Live edit: colour edits accept hex, `rgb()` and `hsl()` only; `oklch()`, `lab()` and named colours are refused or seed the picker `#000000`. No `oklch` computed colour was seen on either app | fontkit-bridge.js:130-131, 477; fontkit-studio.html:3396, 3736 | Code read; related to S07 | size at 0.4.2 |
| G1-9, G2-11 | S3 | source | both | Detect: Bootstrap 5 is the only framework adapter; Tailwind, DaisyUI, shadcn and `next/font` get plain selector rules; an unknown adapter value makes Studio refuse the whole reply | fontkit-bridge.js:172; fontkit-studio.html:3839, 3886-3892 | Code read; Detect worked with plain rules on both apps | size at 0.4.2 |
| G1-10 | S3 | source | neither | Detect: the stylesheet walk stops after 1,000 ms and then reports `budget-exceeded` instead of a selector | fontkit-bridge.js:1731, 1794 | Code read; Detect finished on ScrobbleScope | later (structure) |
| G1-11 | S3 | source | neither | Code: each page-change message serialises every rule of every stylesheet, at most every 250 ms | fontkit-bridge.js:1303-1311, 181 | Code read; not measured | later (structure) |
| G2-7 | S3 | source | ScrobbleScope | Studio: both Adobe kit fields add a link to Studio's own page and say "Loaded", but nothing uses the kit; the Live App never gets it | fontkit-studio.html:1795-1803, 2376-2386 | Search for consumers finds none | 0.4.1 (message) |
| G2-8 | S3 | source | both | Live edit: the Family menu holds 16 library fonts plus a "Current" entry; Typekit and `next/font` families can be seen but not chosen | fontkit-studio.html:6040-6041 | Code read | later (new capability) |
| B03 | S4 | checked | neither | Tokens: only `:root` and `html` rule heads are read; a name declared only under `html.dark`, `[data-theme]` or `:where(:root)` is missed | fontkit-bridge.js:3866 | Probe; no such name found in either app | later |
| B10 | S4 | checked | neither | Live edit: a style change anywhere (an `<html>` class flip) sends no new target list; the shown computed values refresh on selection or the next acknowledgment | fontkit-bridge.js:851, 1283 | Probe. PokeCipher's theme flip changes no font or text colour | later |
| B11, G1-6 | S4 | checked | PokeCipher | Targets: a class containing `mark`, `logo` or `icon` (`wordmark`) gives role `image` and id `auto:h1:image:1`; `leading-tight` gives role editorial. The editors follow the kind, so only the label is wrong | fontkit-bridge.js:3317, 3899-3935 | Probe; the id was seen on PokeCipher's heading in production | later |
| B16 | S4 | checked | neither | Targets: every `<svg>` is a target (40 icons, 40 rows). By design; costs list length | fontkit-bridge.js:118 | Probe; tests/test_bridge_runtime.py:1681-1740 pins svg targets | later |
| B18 | S4 | checked | neither | Sync: placing an image in a container clears a short emoji label and writes flex layout outside the ledger. Documented | fontkit-bridge.js:4336-4342 | Probe; README.md:429 | later |
| B19 | S4 | checked | neither | Live edit: an element re-created more than five times in 2 s stops getting its overrides and drops out of the ledger; Studio is not told. The loop guard is pinned by a test | fontkit-bridge.js:3406 | Probe; tests/test_bridge_runtime.py:2908 | 0.4.1 (message to Studio) |
| B20 | S4 | checked | neither | Live edit: a token registered with `@property` and `inherits: false` is written on `<html>` and reported applied, but descendants do not follow | fontkit-bridge.js:2984 | Probe. Tailwind registers only `--tw-*` names | later |
| A2-4b, E-10 | S4 | checked | ScrobbleScope | Attach: npm rebuilds headers from Node's merged list; two `Date` headers on static files return as one comma-joined value, and reason phrases change case. No visible effect | packages/fontkitstudio/src/proxy.js:246, 267 | Header comparisons on static files; serve.py keeps pairs (tests/test_serve_proxy.py:386) | later |
| C1-4 | S4 | checked | ScrobbleScope | Detect: Typekit families show as lowercase slugs, correct but not marked as Typekit or loaded | none: the computed stack is shown as is | Run on `/` | later |
| C1-10 | S4 | checked | ScrobbleScope | Detect: a role id matches across pages by its style values, so "role-12" is tabs on `/` and album info on `/results` yet reads "Checked on / and /results" | fontkit-studio.html:3825 | One run, not repeated | later |
| C2-5c | S4 | checked | any app | Studio: reloading the Studio tab drops unsynced edits with no prompt | no `beforeunload` handler in fontkit-studio.html | Run; search finds none | 0.4.1 (warning) |
| C2-9, D2-8 | S4 | checked | both | Studio: choosing one library family makes Studio's page request four Google stylesheets and the frame two more; the note says only "loads it from Google Fonts" | fontkit-studio.html:3635, 6089 | Runs on both apps | later |
| D1-12 | S4 | checked | PokeCipher | Attach: `fontkitstudio` with no address detects Vite only; a Next project gets a usage error naming the address form | packages/fontkitstudio/src/project.js:11, 44 | Run: exit 2 | later (npm project detection for Next, not page discovery) |
| D2-5, C2-3c | S4 | checked | any app | Sync: Sync also restyles elements by role inline with `!important` (heading, buttons, spans); Changes, Copy and JSON carry only the tokens. The README says so | fontkit-bridge.js:4252-4284 | PokeCipher and ScrobbleScope, twice each; README.md:429 | 0.4.1 (message: one-line note) |
| S05 | S4 | checked | any app | Export: after a reload with a saved DOM move, the JSON tab holds `structure` while the HTML tab says "No text changes yet." and the counter reads 0 | fontkit-studio.html:6647, 6657 | Fixture, twice. The HTML tab shows the page's markup by design | later |
| S08 | S4 | checked | neither | Studio: an imported composition naming a family the library lacks gets the first library family, with no warning | fontkit-studio.html:2166-2168 | Two imports. Pinned on purpose (tests/test_studio_live.py:2427-2434) | 0.4.1 (warning) |
| B06 | S4 | source | neither | Detect: for variable-valued declarations (`var(--font-sans)`) the receipt names no winning rule and reports `complex-cascade`; roles still apply | fontkit-bridge.js:1678, 1840 | Read from source only; deliberate in the code | later |
| E-4 | S4 | source | any app | Attach: serve.py's `--target-port` is the proxy's own port (8001; Studio 8000); npm picks it; fixed defaults can clash | scripts/serve.py:699-700, 731 | Code read | later |
| E-6 | S4 | source | any app | Attach: for a `localhost` target serve.py binds 127.0.0.1 only; npm holds both address families | scripts/serve.py:75, 91 | Code read; not observed | later |
| E-7 | S4 | source | any app | Attach: serve.py answers over HTTP/1.0 with `Connection: close`; npm keeps connections alive | scripts/serve.py:504-511, 545 | Code read; not measured | later |
| E-9 | S4 | source | any app | Attach: serve.py drops hop-by-hop headers from the app's reply; npm passes them on untagged pages | scripts/serve.py:540-543; packages/fontkitstudio/src/proxy.js:246, 267 | Code read | later |
| E-11 | S4 | source | any app | Attach: if the app drops mid-page, serve.py sends a 502 text page; npm resets the connection | scripts/serve.py:661, 667; packages/fontkitstudio/src/proxy.js:242 | Code read | later |
| E-12 | S4 | source | neither | Attach: the tag goes after the first `<head` in the text, so a `<head>` inside an earlier comment or script receives it and no bridge loads | scripts/serve.py:348; packages/fontkitstudio/src/proxy.js:63 | `insert_tag` import: the tag lands inside the comment | later |
| E-15 | S4 | source | any app | Attach: serve.py has no `--version`; npm has one. The wrapper's post-release check needs one | scripts/serve.py:695-707 | Code read | 0.4.2 (pip wrapper only) |
| E-17 | S4 | source | any app | Attach: the proxy handler sets no socket timeout; the Studio handler sets 30 s | scripts/serve.py:495-498, 119 | Code read | later |
| G1-12 | S4 | source | neither | Code: several loops are super-linear (sibling manifests, ledger HTML on each applied message) | fontkit-bridge.js:3817-3861, 3119 | Code read; not measured | later |
| G1-17 | S4 | source | any app | Code: while connected, the bridge wraps `history.pushState` and `replaceState`; documented in a code comment only | fontkit-bridge.js:1373-1401 | Code read | later |
| G2-2 | S4 | source | neither | Code: Composer, Live and Roles share one closure of about 5,450 lines | fontkit-studio.html:1825 | Code read | later (structure) |
| G2-3 | S4 | source | neither | Code: the longest functions are `renderInspector` (247 lines) and the `message` listener (114 lines) | fontkit-studio.html:2869-3115, 5769-5882 | Code read | later (structure) |
| G2-6 | S4 | source | neither | Code: `cssStack` reads `f.aliases`, which no library font defines | fontkit-studio.html:1507 | Search finds one use | 0.4.1 (one-line fix) |
| G2-12 | S4 | source | any app | Studio: only `react`, `vue`, `svelte` count as framework-managed; another framework's parent gets the DOM strategy with no warning | fontkit-studio.html:3361, 6154 | Code read | later |
| G2-13 | S4 | source | any app | Studio: any `?token=` in its URL selects the npm wording for Sync | fontkit-studio.html:4814, 6754 | Code read | later |
| G2-14 | S4 | source | neither | Code: `renderCanvas` and `applyCompositionPreset` are replaced by wrappers later; the order matters | fontkit-studio.html:7103-7115 | Code read | later (structure) |
| G2-15 | S4 | source | neither | Code: the role inventory render is bounded by caps but can reach about 17 million steps | fontkit-studio.html:4238-4266 | Code read; not measured | later (structure) |
| G2-16 | S4 | source | neither | Code: Reapply of E edits builds text in about E squared steps | fontkit-studio.html:4979-4984 | Code read; not measured | later (structure) |
| G2-17 | S4 | source | neither | Code: the `design:targets` handler keeps the whole list, uncapped | fontkit-studio.html:5867-5872 | Code read; not measured | later (structure) |
| G2-18 | S4 | source | neither | Studio: default texts and canvas colour come from the repository Studio was written in | fontkit-studio.html:2131, 1172, 1053 | Code read | later |
| G2-19 | S4 | source | neither | Code: a local `familyOptions` shadows the function of that name | fontkit-studio.html:2532, 6040 | Code read | 0.4.1 (one-line fix) |

## What works

- Both apps attach with no hooks by either path; the page matches the direct page apart from the one tag.
- Detect on ScrobbleScope finds its real type system: 19 roles from 53 parents on `/`, 21 from 100 on `/results`; stacks match
  the computed `font-family` exactly. On PokeCipher it finds 15 groups, pixel-font headings and terminal body text.
- Detect changes nothing in the page. Preview, Apply and Clear on `/` leave computed styles, head, attributes and sheets as they
  were, twice.
- Inspector family, size and colour edits apply and reset; a bad colour is refused with a message; text edits on a leaf node work.
- Exported CSS, added to a direct page of either app, gave the same computed values as the edited page.
- Edits on nodes the app keeps survive a theme swap, a re-render and Sync on PokeCipher; an edited heading survives
  ScrobbleScope's theme toggle.
- A reload shows the reconnect banner and applies nothing silently; Reapply on another page is refused and keeps the saved state.
- Structural moves are reversible: DOM order on a plain parent, CSS order on a flex or React-managed parent, Reset restores.
- Select mode does not navigate; Interact mode does.
- Studio's own page makes no third-party request on load. Stopping is clean on both paths.

## Checked and rejected

- `B02` (false): a page's own `new FontKitBridge({allowedOrigins})` with `data-auto-init="false"` does take effect, because a bridge
  no Studio has talked to is replaced on purpose.
- `B12` (false): the role pattern is built with the `i` flag, so `foreignObject` and `clipPath` selectors pass.
- `D2-12` (false): the colour left on PokeCipher's sprites toggle after Reset all is a pending CSS transition that Chromium does
  not start in an off-screen frame. It resolves when the frame is scrolled into view and reproduces with Studio absent.
- `S06` as the cause of `C1-1` (false): during the failing press no page mutation was recorded. The cause is the closed `<details>`
  text. The `S06` mechanism is real and is merged into `D2-10`.
- False parts of rows that stay as findings: `B15` does not hold that Studio never sends the composition path (it does);
  `B20`'s `syntax: "<*>"` is invalid CSS and the token then works; `B09`'s claim that React writes to a detached node is wrong for
  a single string; `B08`'s claim that Studio lists `--font-terminal` is unconfirmed.

Known and documented, not counted: `B05` (a loss inside `@layer` is reported without a selector; README states `@layer` shows up
as unknown or as a loss); `B07` (a `var()` family is refused by decision D072, pinned by tests/test_role_stylesheet.py:322);
`G1-8` (a token written inline on `<html>` outranks a theme rule, decision D063, and edits survived theme swaps on both apps);
`G1-16` (auto ids and selectors are labelled unstable, decision D016).

Noted, not counted (wording or documentation only): `C2-5b` (the reconnect banner says "If you synced..." when sync is off);
`E-16` (under `serve.py` proxy mode Studio says sync is disabled by `--no-sync` though no such flag was passed; not checked
in a browser); `E-5` (the `serve.py` Studio port has a Host check only, while npm adds a token, an Origin check and a 405).

## Earlier audits

98 rows from the earlier audits were re-checked against the tree: 71 done, 4 partial, 16 open, 7 moot. The 20 open or partial
rows include no S1 or S2: 5 are S3 and 15 are S4. These are not counted above, except the record sentence (`PUB`).
Open rows that still matter: `F2-LC-01` (a new Custom text slot is #eef2ff on a #f5f1e8 canvas, contrast about 1.008:1),
`F2-LC-02` (Composer and axis controls have no accessible name), `F2-LC-03` (no keyboard way to select a canvas slot),
`F2-LC-04` (typing an invalid colour drops the previous one with no message), and the record sentence (`LC-01` to `LC-04`
are in `docs/implementation/audit-2026-10-08-library-composer.md`). The first four were assigned
to the pairing-system work (R3). The 15 S4 rows are design gaps and small test or record notes.

## Coverage against claims

The README names only Vite 7 and 8, React, Next.js 16, Bootstrap 4 and 5 and Tailwind (as advice). Each named stack has a test:
Vite 7.3.6 and 8.3.2 fixtures, a React app, a Next.js 16.3.8 fixture through the npm path, Bootstrap 4 and 5.3.8 static pages.
Nothing tests Tailwind 4 (only escaped class names in a synthetic page), DaisyUI, Jinja or Flask (a server-rendered app with
sessions, CSRF and redirects), shadcn, `next-themes` or `next/font`. The Python proxy is tested in front of Bootstrap 5 and a stub
server, not Next. PokeCipher runs Next 16.2.6 and React 19.2.4 against the fixture's 16.3.8 and 19.3.0. Vue and Svelte guards are
tested with hand-set markers, and the SvelteKit limit in the README has no test.

What these two apps add: the first run of `serve.py` and npm in front of Flask and in front of Next, the first Detect on Tailwind 4
with DaisyUI and on shadcn, and the first Studio session on a React 19 production build. They show that zero-hook attach holds
on both. The problems they expose are the fixed token names, the discovery lists, cursor-style re-rendering, and the Tailwind
selector chains, none of which a fixture covers.

## Limits

- Chromium only; no Firefox or WebKit run.
- ScrobbleScope: a small number of lookups for one account and one period; `/results` Apply, Clear and reset were not run.
- PokeCipher: production build only, apart from the single `next dev` run behind `D1-10a`, and one route; reload, reconnect
  and Sync to file were not reached; hot reload and development overlays were not reached.
- Hydration was checked on three production loads, which were clean. Under `next dev` the mismatch in `D1-10a` was seen once
  and not repeated, so whether it occurs on every development load was not established.
- Sync to file was not run on either app: `serve.py` ran with `--no-sync` and proxy mode has no file sync.
- `S01` to `S05` were reproduced on a fixture page, not on the two apps; live inspector edits on ScrobbleScope ran on `/` only.
- Rows marked "source read only" were not run. B05 and B06 were read from source only.
- The mislabelled-element check (`B11`) was not run through Studio on a real image slot.
- Timing and performance rows (`E-7`, `G1-11`, `G1-12`, `G2-15` to `G2-17`) are not measured.
- The `B13` scheme for Next's current CSS Modules output is from memory, not measured.
