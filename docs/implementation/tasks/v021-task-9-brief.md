# v0.2.1 Task 9 brief: docs, names and screenshots

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 9). Plan addendum 5 and D039
replace the plan's line about keeping "v0.1.1": Studio's title and eyebrow now read v0.2.1.
Implementer: Tracking-9. Runs alone, after Task 8.

## Required

1. **README matches the product at this branch head.**
   - The first-run flow:
     - the Live App URL box starts empty;
     - `serve.py` prints `Open:`, names a busy port, and opens a browser only with `--open`;
     - "Connect to the demo".
   - Controls that are disabled say why.
   - Explain what Sync to file does with nothing saved: a fresh session never writes, and
     after the user's own reset it clears the file.
   - The preset select applies on change and asks first.
   - The renamed labels, especially "Live App" (Connect Live App, Accept Live App state).
   - The current version label.
   - Grep the README for every old name and fix each one: Target App, Live Target,
     Connect Target, Accept target state, "the target" meaning the user's page, Target URL.
     Do not change protocol or code names (`?target=`, `targetId`, `data-live-target`).
2. **One name outside Studio.**
   - `scripts/serve.py` prints the demo address under `Target:`. Make that label say what
     it is: the demo app, shown next to the `Open:` line. Change only the printed label and
     its comment, plus the test assertions that pin it (`tests/test_preview_server.py`).
   - The demo's meta and footer say "demo target app" (`demo/index.html`, about lines 8
     and 334). Change only that wording.
3. **Screenshots.**
   - Regenerate every screenshot with `docs/assets/screenshots/capture.py`.
   - Rename `target-app-*.png` to `live-app-*.png`, and update every reference (README, the
     capture script, `docs/assets/README.md` if it lists them).
   - Check each image by eye: it must show Task 8's visuals and the v0.2.1 title.
4. **CONTRIBUTING.md.** Fix stale names or commands, if there are any.
5. **CHANGELOG.md.** Add a line under Unreleased for every change a user notices (the
   `serve.py` label, the demo wording). README-only edits need no line.

## Owned

- `README.md`, `CONTRIBUTING.md`
- `docs/assets/screenshots/` and `docs/assets/README.md`
- the printed label in `scripts/serve.py` and its assertions in `tests/test_preview_server.py`
- the demo's "demo target app" wording
- `CHANGELOG.md`

Must not touch: Studio, the bridge, any other test, and any agent-facing doc (`AGENTS.md`,
plans, the ledger).

## Gates

- `python scripts/verify.py --static-only`
- `node --check fontkit-bridge.js`
- `PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python -m unittest test_preview_server test_bridge_runtime test_live_integration -v`
- the capture script runs clean
- a link check: every relative link and image path in README, CONTRIBUTING and
  `docs/assets/README.md` resolves to a file

## Report

Append "## Implementer report" to this brief in your worktree. Include:
- each README section changed, with what it now says;
- the grep results before and after for the old names;
- the screenshots regenerated;
- the CHANGELOG lines;
- the final `git diff --stat`;
- what you did not verify.

## Implementer report

Implementer: Tracking-9. Base ef7d3f2. Nothing committed or staged. Two new PNGs are untracked
(`live-app-desktop.png`, `live-app-mobile.png`); the two `target-app-*.png` files are deleted in the
working tree.

### README sections changed

- Hero image: new alt text and `live-app-desktop.png`. The image is now the first screen of Studio at the
  top of the page, so it shows the "FONT KIT STUDIO - V0.2.1" eyebrow, the Live App Bridge bar and the
  inspector (the old image was fullscreen and showed no title).
- Quickstart step 1: the printed line is `Demo:` (was `Target:`); the command never opens a browser unless
  `--open`. Step 2: `?target=` opens the Composer in its Live App view and connects. Step 4: Copy and Sync to
  file stay disabled until a change. "Own app": Live App URL box and Connect Live App.
- "A few things Studio tells you on the way in", rewritten and extended: Studio opens on Library and the bridge
  bar is in Composer; empty Live App URL box with the disabled Connect Live App and its reason; the demo offer
  ("Connect to the demo", back to "Connect Live App" when the address is edited; Studio refuses its own
  address); the 4 s no-bridge message; the hosted-web note; fullscreen never connects, Exit button and Esc; a
  new bullet on disabled controls and their reasons (Sync to Live App, Restore Page Text, Reset this element,
  Copy, Download, Sync to file, Select, Interact, widths, Load free fonts, Focus pop-out, the printed hints).
- "Open the Studio HTML file directly": the file keeps its v0.1.1 name (D039), the title inside shows v0.2.1;
  Live App URL.
- Dev server options: "Studio and the demo app" (flag names unchanged).
- Workflows: "Live App inspector" heading; "the element keeps its edits" (was "the target"); alt texts; JSON tab
  line says `target` is the Live App's URL and the changes are keyed by element id (checked in the code:
  `target: live.url`).
- Code panel: new two-bullet block on Sync to file with nothing saved. A fresh session never writes (Sync
  disabled "No changes to save yet."; Auto-sync writes nothing and says so). After the user's own reset, Sync
  stays on, its tooltip says it writes an empty overrides file, and pressing it (or Auto-sync) replaces the
  file with `/* No live style overrides yet. */`. Checked against `emptyWriteRefused`, `heldSavedState` and
  `tests/test_studio_controls.py`.
- Reconnect banner and the guard text: "Accept Live App state" (3 places).
- Free fonts: "Live App inspector (Live App view)", "The Live App stays silent too".
- Library and Composer: "with or without a Live App"; "Specimen / Live App" and that the Live App view hides
  composition-only fields; the Composition preset select applies on change, asks "Replace your edits?" first
  (No keeps edits), and Apply preset re-applies after the same question or says there are no edits to reset;
  Library reports loaded fonts; width buttons listed in UI order (1440 / 1024 / 390 / Fluid) and work in the
  Live App view.
- Bookmarklet step 1: Connect Live App. Security: "Live App URLs". Frontend-gate table: "Live App inspector",
  "connected Live App view".
- Test files table: eight rows added for test modules that were missing (first_run, controls, dead_controls,
  import_link, stage, visual, review_findings, support).

### Old names in README (grep counts, before -> after)

- Target App 2 -> 0; Live Target 4 -> 0; Connect Target 3 -> 0; Accept target state 2 -> 0 (plus one more
  in the Code panel prose, fixed); Target URL 3 -> 0; `Target:` 1 -> 0; `target-app-*.png` 2 -> 0.
- Left on purpose: `?target=`, `--target-port`, the `Connected (N targets)` badge (Studio still prints it),
  `design:targets`, "targets" in the protocol tables, `"target"` in the JSON tab, `touch targets`, and "the
  target under the pointer" in the `design:hover` row (an element, protocol meaning).

### Outside Studio

- `scripts/serve.py`: the printed `Target:` line is now `Demo:` (same column), with a comment that it is context
  and the `Open:` line is the link to open. `tests/test_preview_server.py` asserts the `Demo:` line and that
  `Target:` is gone. The module docstring still says "target app" and "target port" (see not done).
- `demo/index.html`: meta description "demo app", footer "A demo app for Font Kit Studio."

### Screenshots (`docs/assets/screenshots/capture.py`, ran clean three times, last run is the one on disk)

Regenerated all nine: `live-app-desktop`, `live-app-mobile` (renamed), `arrange-desktop`, `arrange-guard-desktop`,
`arrange-mobile`, `bridge-bar-desktop`, `code-panel-desktop`, `code-panel-mobile`, `pop-out-desktop`. Capture script changes: output name `live-app-*`, and the desktop hero is now a
top-of-page viewport shot instead of the fullscreen one, so the v0.2.1 title is in it. Viewed each image:
Live App Bridge label, Connect Live App, disabled Restore Page Text, Select/Interact looking disabled,
"Live App" inspector heading, "37 TARGETS", grouped list "Marked with data-design-id", disabled Reset this
element and Move into, the "No changes to save yet." line (pop-out shot), the demo footer "A demo app for Font
Kit Studio". Only `live-app-desktop` and `pop-out-desktop` show the v0.2.1 title; the others are crops.

### CHANGELOG lines (Unreleased, Changed)

- "The dev server labels the demo app's address `Demo:` instead of `Target:`, and the demo's description and
  footer say "demo app" instead of "demo target app"."
- Two stale names in existing Unreleased lines: "Fullscreen no longer connects to the Live App URL." and "A Live
  App URL like `http:example.com` is refused ...".
- No line for README-only edits or the screenshots.

### CONTRIBUTING.md and docs/assets/README.md

No change needed. CONTRIBUTING has no old names or stale commands; `docs/assets/README.md` lists no screenshots.

### Gates

- `python scripts/verify.py --static-only`: all PASS (unique IDs, inline JS, provenance).
- `node --check fontkit-bridge.js`: ok.
- `test_preview_server test_bridge_runtime test_live_integration` (Chromium): 214 tests, OK.
- Also run: `test_studio_visual test_studio_dead_controls test_studio_first_run`: 82 tests, OK.
- Link check (`scratchpad/t9_links.py`): every relative link, image path and in-page anchor in README,
  CONTRIBUTING and `docs/assets/README.md` resolves. The two "missing" hits in `docs/assets/README.md` are the
  logo paths inside its copy-paste snippet, written relative to the repo root on purpose.
- Frontend gate, Firefox canary, full suite and commit-message check: not run.

### Final `git diff --stat` (tracked files)

```
 CHANGELOG.md                                      |   7 +-
 README.md                                         |  75 +++++++++++++---------
 demo/index.html                                   |   4 +-
 docs/assets/screenshots/*.png (7 modified, 2 deleted)
 docs/assets/screenshots/capture.py                |  11 ++--
 scripts/serve.py                                  |   3 +-
 tests/test_preview_server.py                      |   3 +-
 15 files changed, 60 insertions(+), 43 deletions(-)
```
Untracked: `docs/assets/screenshots/live-app-desktop.png`, `live-app-mobile.png`.

### Not verified, or not done

- Not verified in a run: the claims I kept unchanged from before (Sync to Live App reordering the page's main
  sections and adding a `transition`; the Free-fonts paragraph about Composer slot fallback; the guard table;
  Reapply order; the pop-out sizes; the Tailwind and framework recipes). Behaviour I changed or added was
  checked in code and against tests.
- Hosted-on-web Chromium blocking is covered by a test only through the fake missing-port case.
- `docs/roadmap/browser-extension.md:40` still says "the Live Target inspector". Outside my ownership.
- `scripts/serve.py` module docstring still says "target app" / "target port" (the brief limited me to the
  printed label and its comment). The `--target-port` flag name is unchanged.
- `bridge-bar-desktop.png` (Task 8 visual): in the connected 1440 px state the Live App URL box is squeezed to
  about 13 characters ("http://localh") because every control sits on one row. The pop-out shot wraps the
  row and shows the whole URL. Worth a look; not a README issue.
- `live-app-mobile.png`: the selection outline covers only the first two lines of the hero title (it looks
  stale after the font-size edit reflowed the title). The capture was not changed for this.

## Fix round 1

Implementer: Tracking-9. Review verdict "Approved with fixes" (`v021-task-9-review.md`). Same worktree, still
uncommitted and unstaged (the two `live-app-*.png` files show as intent-to-add, ` A`; nothing is staged).

### What changed, by finding

1. **Sync to Live App sentence (README).** Read `fontkit-bridge.js` (`handleCompositionUpdate`,
   `applyWireframeMovement`, `applySlotUpdate`) and ran the demo (`t9_sync.py`, `t9_sync2.py`, `t9_sync3.py`):
   with the default preset Sync sets three font tokens (no `--font-sans`), restyles three elements (wordmark,
   stat badge, hero title: family, size, weight, line height, tracking, colour, alignment, case, all inline and
   `!important`), adds `transition` to all six children of `<main>` and `order: 3` to the hero section. The
   section order does not change on the demo (only one child holds a mapped element). On
   `tests/fixtures/bridge/target.html` (several mapped children of `<main>`) the mapped children move in the
   DOM, in slot order, after the other children. The Changes panel then shows the tokens (CSS tab), the DOM
   move (HTML tab, plus the structural note in the CSS tab, and the count) and an edited slot text (HTML tab,
   checked by editing the H1 slot's text before Sync). It never shows the element styles, `order` or
   `transition` (CSS tab had 0 rules in every preset). The README now says all of that, as a short list.
2. **URL box.** Studio CSS `.bridge-bar .bridge-url`: `flex: 1 1 240px; min-width: 240px; max-width: 100%`, with a
   comment. New test `UrlBoxFitTests` in `tests/test_studio_visual.py` (next to `ToolbarFitTests`). CHANGELOG
   line under Fixed. Recorded deviation: Studio is outside Task 9's brief; the controller asked for this edit and
   no other writer was active in it. RED and GREEN below. All nine PNGs regenerated and viewed.
3. **Stale outline in `live-app-mobile.png`.** Confirmed with `t9_overlay.py`: at 390 px the outline is 124.8 px
   tall against a 374.4 px title when the shot is taken, and follows within 30 to 106 ms once the preview is
   visible (the bridge reports bounds from `requestAnimationFrame`, which a scrolled-out iframe does not run).
   `capture.py` now waits (`outline_follows_title`: overlay visible and within 2 px of the title's height) before
   the mobile shot, and before the desktop hero shot too.
4. **README:** "**Cancel** keeps them" (native confirm with OK and Cancel).
5. **README:** after a reset Sync writes two comments, the header that names the Live App's URL and
   `/* No live style overrides yet. */` (checked: `t9_reset_file.py`).
6. **README:** fullscreen covers the bridge bar (checked: it is `inert` and the preview frame is on top of the
   Connect button, `t9_fullscreen.py`), so "leave it with Exit or Esc, then press Connect Live App".
7. **README:** the version shows in the browser tab's title and in the line above Studio's heading.
8. **README:** pop-out size is the free screen less 80 px each way, from 600 x 400 up to 1280 x 860, offset
   40 px from Studio's window (checked with `window.open` stubbed under seven screen sizes, `t9_popout.py`).
9. **README:** "Reload the preview" now says "Press **Connect Live App** again to reload the preview" (quickstart
   step 5, and the Sync to Live App text). Checked: the frame reloads, the saved style stays, the reconnect banner
   appears, and everything Sync to Live App set in the page is gone (`t9_reload.py`, `t9_sync3.py`).
10. **README:** no literal "v0.2.1" in prose or alt text (the hero alt text and the file-name sentence).
11. **Old names.** Printed labels and docstrings: `_frontend_gate_theme.py` (docstring, section label "Live App
    inspector", the two synthetic warning texts), `_frontend_gate_live.py` (three docstring lines),
    `_frontend_gate_runtime.py` (docstring: "demo app"), `serve.py` docstring ("demo app", "demo port
    (--target-port)"), `test_preview_server.py` and `test_live_integration.py` docstrings. Studio comments at the
    seven listed places. The pop-out placeholder now reads "The Live App is open in its own window. Pick
    elements there; the inspector here edits them." (the window name `fontkit-target` stays in `window.open`).
    CHANGELOG: one sentence under Changed.
12. No action (informational).

### RED and GREEN for the URL box test

Test: `UrlBoxFitTests.test_the_address_box_holds_an_address_in_every_state_of_the_bar`. It measures how many
characters of the box's own monospace font fit between its padding (canvas `measureText('0')`), at 1440, 1280
and 1024 px, in four states (idle with the demo offered, idle with an empty box, `Connected (N targets)`,
`Live · rev N`), and fails if fewer than `len('http://localhost:12345/demo/')` = 28 fit or if the page scrolls
sideways.

- RED, old rule (`flex: 1 1 100px; min-width: 100px`):
  `AssertionError: 16 not greater than or equal to 28 : the address box fits 16 characters: 1440px, idle, the
  demo offered` (log: `scratchpad/t9_red_urlbox.log`).
- All twelve states on the old rule, characters that fit (`t9_urlbox_table.py`):
  1440: 16 / 19 / 50 / 12; 1280: 40 / 43 / 28 / 36; 1024: 15 / 18 / 22 / 12 (idle offered / idle empty /
  connected / live). Seven are under 28.
- GREEN, new rule (`flex: 1 1 240px; min-width: 240px`): `Ran 1 test ... OK`.
  The same twelve: 62 / 65 / 50 / 58; 40 / 43 / 39 / 36; 34 / 37 / 45 / 31. The smallest box is 247 px.
- No new sideways scroll at 390, 600, 768 and 900 px (connected: 40 / 47 / 31 / 49 characters on the new rule;
  the old rule gave 19 / 26 / 31 / 28), compared in one file by injecting the old rule (`t9_urlbox_narrow.py`).

### Screenshots regenerated and viewed after the change

`live-app-desktop` (full address in the box, "Live . rev 5" badge, eyebrow "V0.2.1", outline tight on the
title), `live-app-mobile` (outline now covers the whole title), `bridge-bar-desktop` (full address, controls wrap
to a second row), `pop-out-desktop` (full address; placeholder text without the window name; two comment lines in
the CSS tab; "No changes to save yet."), `code-panel-desktop`, `code-panel-mobile`, `arrange-desktop`,
`arrange-guard-desktop`, `arrange-mobile`.

### Gates (Chromium only)

- `python -m unittest test_preview_server test_studio_visual test_live_integration test_studio_first_run -v`
  (`PYTHONPATH=tests`, `FKS_ENGINES=chromium`): 143 tests OK, including the new one.
- Also: `test_studio_controls` 32 OK (the README's Sync-to-file claims) and `test_studio_live -k pop` 6 OK (the
  pop-out placeholder).
- `python scripts/verify.py --static-only`: all PASS. `node --check fontkit-bridge.js`: ok.
- Offline Chromium frontend gate (`--engines chromium --offline`): 15 of 15 runs finished, 0 FAIL, 166 REPORT,
  1 SKIP (free fonts load, by `--offline`). It differs from the pre-fix gate in one advisory line only:
  `input#targetAppUrl` is 314x28 (was 140x28).
- Link check over README, CONTRIBUTING and `docs/assets/README.md`: every relative link, image and anchor
  resolves (the two logo paths in the copy-paste snippet of `docs/assets/README.md` are relative to the repo
  root on purpose).

### Not verified, or left

- Firefox, other engines, the full suite and the commit-message check: not run.
- Pop-out size on a real screen (only `window.open` arguments under stubbed screen sizes); "Connect Live App
  again" in pop-out mode (it docks the window back; checked only with the iframe).
- `scripts/dev/_frontend_gate_layout.py` lines 170, 185 and 298 still say "Composer target view"; line 298 is
  the label printed on about 50 gate lines. It was not on the controller's list, so it is untouched.
- About forty Studio comments still say "the target" for the user's page (the protocol's own word); only the
  listed old names were changed. `tests/test_studio_live.py:305` (a test comment, "Target App view") and
  `docs/roadmap/browser-extension.md:40` are outside this round.
- The README's older statements that were not changed were not re-run (see the first report).

## Fix round 2

Implementer: Tracking-9. Re-review verdict "Approved with fixes" (Low items R1 to R7). Same worktree, still
uncommitted and unstaged.

- **R1 (README, Sync to Live App).** The list now covers every slot type the bridge applies and no longer says
  "four things". Checked against `fontkit-bridge.js` (`resolveElementForSlot`, `applySlotUpdate`, `placeAsset`) and
  in a real run on the demo and on three small pages (`t9_sync5.py`, `t9_sync6.py`):
  - A slot finds its element by its role (a `data-design-id` that contains the role's name, or a role word);
    with no match it takes the element at its own position in the page's `data-design-id` elements, in page
    order, counting auto-discovered ones. Seen: a Spacer slot at position 2 hit the third element and a Rule slot
    at position 3 the fourth; on a page with two marked elements the H1 slot also fell back to position 1.
  - Image slot (file chosen): `<img>` gets its `src` replaced (`srcset` removed) with width and opacity;
    an inline `<svg>` is hidden and the image goes right after it; any other element gets the image inside
    (and a lone emoji placeholder is cleared). Width and opacity are the slot's.
  - Spacer slot: `margin-top`. Rule slot: `width` (%), `border-top-width`, `border-color`.
  - None of these changes is listed as its own change in the panel. One correction to the controller's note: a
    placed image can appear inside a DOM move's snippet in the HTML tab, and an image put into a container that
    held only an emoji clears that text, so the container is listed as a text change. The README says both.
  - Connect Live App again removed every inline style and every placed image in the run.
- **R2 (pop-out placeholder).** `PageNameTests.test_no_text_in_any_state_calls_the_users_page_the_target` now also
  asserts `assertNotIn('fontkit-target', #bridgePopoutText text)`.
  - RED, with Studio's old text put back for the run: `AssertionError: 'fontkit-target' unexpectedly found in
    'The Live App is open in its own window ("fontkit-target"). Pick elements there; the inspector here edits
    them.'`
  - GREEN with the current text. The Studio file was restored byte for byte (same hash, `cmp`) after the run.
- **R3.** `_frontend_gate_layout.py` lines 170, 185 and 298 say "Composer Live App view" (labels and a docstring).
- **R4.** `UrlBoxFitTests` reports one subTest per width and state (plus one for page errors). On the old CSS the
  same run listed seven failing subTests at once (1440: offered 16, empty 19, live 12; 1024: offered 15, empty 18,
  connected 22, live 12); on the current CSS all pass.
- **R5.** CHANGELOG: "no longer shrinks to a sliver ... when the status badge and the buttons shared its row
  ... the other controls wrap to the next row instead". The CSS comment says the same.
- **R6.** README: "available screen".
- **R7.** One-line comment edits in `tests/fixtures/bridge/target.html` ("Live App fixture") and
  `tests/test_studio_live.py:305` ("Live App view"); nothing else in either file.

### Gates (Chromium only)

- `python -m unittest test_studio_visual test_preview_server test_frontend_gate_helpers test_frontend_gate_report
  test_frontend_gate_runner test_frontend_gate_fonts test_frontend_gate_theme_browser -v`: 228 tests OK. There is no
  `test_frontend_gate_layout` module; `test_frontend_gate_helpers` is the one that imports
  `_frontend_gate_layout`.
- `test_bridge_runtime` (it loads the edited fixture): 128 OK. `python -m py_compile tests/test_studio_live.py`: ok.
- `python scripts/verify.py --static-only`: all PASS. `node --check fontkit-bridge.js`: ok.
- Link check: every relative link, image and anchor resolves (the two logo paths in the snippet in
  `docs/assets/README.md` are root-relative on purpose).

### Not verified, or left

- The offline frontend gate and the screenshots were not re-run: only a CSS comment, README and CHANGELOG text,
  test code, three gate labels and two one-line test comments changed since the last run.
- Other engines, the full suite, the commit-message check: not run.
- The Sync to Live App text was checked on the demo and on small pages, not on a real framework app.
