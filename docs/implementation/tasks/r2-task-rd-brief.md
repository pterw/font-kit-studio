# R2.RD brief: README and package README document the 0.4.0 text-role feature accurately

Plan: `docs/plans/2026-10-03-r2-engine.md` task "R2 release point: 0.4.0", first checkbox (sweep live claims; document
detector exclusions, cascade limits, session-only routes and role-preview output boundaries), and Addendum 24 item 1
(known limits in the README's role section); Addenda 26 and 27 for the wording. Wave W3. BASE
`5d28252fb6acf52b1287d7f90054d70b49ae249e`. Worktree `C:/fks/trd` (detached at BASE; the controller creates it), task id
`rd`. Line budget: about 160 gross lines added or changed, Markdown only (D065: not material). Documentation slice: no
RED/GREEN. Every sentence you write must be checkable against a source fact named below or one you find at BASE.

## Why

The README at BASE says nothing about text-style roles: no `Detected roles` section, no role messages in "Protocol v1"
(`README.md` 522-583), no word on visited pages. It also still says the old Studio file name "is now a small page that
forwards" and "goes away at R2 (0.4.0)" (`README.md` 101) and lists `test_studio_rename.py` as a forwarder test (647),
but R2.FW removed the file (`git ls-tree 5d28252` shows no `font_kit_studio_v0.1.1.html`). The test table (636-660)
omits 18 modules (list them with the loop in Requirement 9). A reader cannot learn what Detect measures, what Apply
guarantees, or where the evidence stops.

## Owned files (exact)

- `README.md` (edit in the places named below; a new `### Detected roles` section under `## Workflows`).
- `packages/fontkitstudio/README.md`: one short added paragraph (Requirement 8).
- `CONTRIBUTING.md`: read it; edit only a line that is false at BASE. At BASE it has no role, version or forwarder claim
  (grep confirms), so expect no edit. Say so in the report.

Read-only: everything else. Not owned: `CHANGELOG.md`, `docs/plans`, `docs/implementation`, `docs/roadmap`, any
non-Markdown file, version labels (R2.RL sets 0.4.0). You may write "0.4.0" in prose that describes this release. Do not
touch screenshots; Requirement 11 names the images the controller regenerates.

## Read first

`constraints.md`; `.superpowers/sdd/r2c/w3-known-limits.md` (every item appears below or is left out with a reason);
`AGENTS.md` "Markdown Authoring Rules" (plain English, short sentences, active voice, ISO dates; the README may use richer
formatting) and anti-pattern 15 (no process state: no model, tool, reviewer or round counts in the README).
At BASE: all of `README.md`; plan 957-1080 (detection, identity, route observation), 829-925 (messages), Addenda 24, 26
and 27 (553-664); `docs/implementation/deviations.md` D058-D076; `docs/roadmap/product-direction.md` 88-113 ("Where it
stands"); `fontkit-studio.html` 1250-1280 (panel), 3744-3760 and 3885-3905 (texts), 4106-4145 (rows), 4202-4252
(inventory), 4390-4415 (outcomes), 4640-4670 (applied message and rejections); `fontkit-bridge.js` 301, 1220, 1272-1290,
1371, 1861, 2048-2056, 2112.

## Requirements

Each cites its source fact. Quote Studio's wording exactly where marked; do not paraphrase a string a user sees. Where a
fact below is a pointer, confirm it at BASE (`git show 5d28252:<path>`) before writing; if the code disagrees, write what
the code does and list the disagreement under Open questions.

1. **New `### Detected roles` section** placed directly after
   `### Code panel` (`README.md` 166-190) and before `### Arrange`. Open with what it is, one short paragraph: Detect reads
   every distinct text style on the page, groups exact matches into roles, and lets you preview new values for a role
   through one stylesheet the bridge owns. Studio writes nothing to your source or files from it. Source: plan 957-969,
   925-930; Studio panel `fontkit-studio.html` 1250-1280 (heading `Detected roles`; the panel shows after Studio connects).
   Add a "Requires" line: Studio and a bridge from 0.4.0 or later; npm users run `fontkitstudio` 0.4.0 or later (the bridge
   ships in the package).

2. **Detect.** Button `Detect text styles`. Say what it counts and excludes, from plan 957-969:
   counts text in the page's light DOM, one eligible parent element once, including text below the fold; excludes
   `head`, `script`, `style`, `template`, `noscript`, editor overlays and placed assets, `display:none`,
   `visibility:hidden` or `collapse`, zero-area text and fully transparent ancestor chains. Not covered, stated as a bullet
   list: form values and placeholders, generated pseudo-element text, shadow-root internals, nested frames and SVG text.
   Studio prints `Light-DOM text only` (1255); use those words. Two styles are the same role only when family, size,
   weight, case and tracking match exactly (D058, plan 962-969); sizes round to two decimals. A role named with
   `data-design-role` keeps one identity even if its elements differ, and Studio lists the variants and counts. Near
   duplicates are flagged and never merged (D058: family and case equal, size within 1 px, weight within 100, tracking
   within 0.02 em); row text `Near duplicates (kept separate): ...` (4140).
   Incomplete scans: a scan that stops early says so and its page is not marked checked. Use the exact status
   `Incomplete detection (<reason>); this page has not been checked.` (4498) with the bridge reasons
   `time-budget` (more than 2,000 ms, bridge 2048-2054), `element-limit` (more than 10,000 eligible elements, 1861/2112),
   `reply-limit` (reply over the 1 MiB limit, 2056) and `page-changed`. Say a page of 5,000 eligible elements finishes in
   2 seconds on desktop Chromium (D058; do not promise it elsewhere).
   Say detected values are the page baseline, measured with the role preview off (Studio line 1256).

3. **Roles and bindings.** What a row shows: name and id (`role-N`), eligible parent count and a sample, each style with
   its count, each selector marked `stable` or `uncertain` with its reason (4118-4124), `Safe complete bindings
   unavailable.` when Apply is disabled for the row (4129), `Shared classes:` when a class also styles other text. State
   the preference order: author role or ID, then a class whose matches are exactly the group, then a checked DOM path
   (plan 971-975); CSS-module-looking classes carry an uncertainty note, not a promise of compiler detection. A row with no
   safe complete binding stays visible and cannot be applied; Studio never falls back to a broad selector.
   Role ids are `role-N`, issued in order and kept while the collection lives; a new origin restarts them
   (Addendum 27 item 5).

4. **Adapters.** One short subsection or table. Plain adapter: one rule per role. Bootstrap 5 (D068-D069, D074): on a page
   whose computed `:root` variables show Bootstrap 5, the bridge suggests an adapter and Studio shows
   `Adapter: Bootstrap 5 body variables`, `Adapter: Bootstrap 5 monospace variable` or `Adapter: Bootstrap 5 heading
   rule` (labels at `fontkit-studio.html` 3881-3883; plain shows no line). Body binds `body`; Monospace binds `code`,
   `kbd`, `pre` and `samp` when the group has no complete binding of its own; Heading binds the heading level or display
   class. For Body and Monospace the bridge writes a `:root` block of `--bs-body-font-family` and `--bs-font-sans-serif`
   (Body) or `--bs-font-monospace` (Monospace) before the role's own rule, so inherited text follows. Bootstrap 4 and
   unknown frameworks get plain rules only. The bridge checks the adapter again at Apply and refuses one the page no
   longer supports. A request holds at most one Body and one Monospace role. Author roles stay plain.

5. **Apply and Clear.** Fields and exact limits (`fontkit-studio.html` 3874-3879, plan 904-912): family 1 to 300
   characters (no `; { } < >`, backslash, control characters, comments, `!important`, `url(`, `expression(`, `var(`,
   `env(` or `attr(`; not `inherit`, `initial`, `unset`, `revert` or `revert-layer`; a parenthesis only inside quotes: D072),
   size 4 to 400 px, weight whole number 1 to 1000, line height 0.5 to 5, tracking -0.5 to 2 em, case `none`, `uppercase`,
   `lowercase` or `capitalize`. Fields start empty with the observed value as placeholder; nothing previews until the row
   is ticked (`Preview this role`, 4262-4266). Studio never sends text, colour, alignment, order, images, font
   stylesheets or custom properties as a role. Buttons `Apply selected roles`, `Clear preview`, `Reset all page edits`
   (the last asks first and removes every live edit including the role preview: 1275-1279, 4548-4556).
   Apply replaces the whole role set in one step or changes nothing; a refusal keeps the previous preview and says
   `Role preview apply rejected (<reason>); the previous preview is kept.` (4666). Reasons: `invalid-message`,
   `unsupported-value`, `revision-conflict`, `page-changed`, `stylesheet-blocked`, `size-limit` (3896). Clear removes only
   the bridge's own stylesheet: author DOM, inline styles, inspector edits, text, tokens and font links stay (plan 936-941).
   A page whose `style-src` forbids inline styles (no `'unsafe-inline'`) blocks the sheet: Apply shows
   `stylesheet-blocked` and keeps the previous preview (`tests/test_r2_integration.py` 625-645). Needs no policy change;
   do not suggest weakening the policy.

6. **Receipts, losses and what a count means.** The page measures the result after Apply; Studio shows what the page
   confirmed. Exact texts: `Preview applied to N role(s); M checked element(s) did not show it.` (4653), then per role
   `<name> (<id>): matched A, checked B eligible text elements, mismatched C` (4407). Define: `matched` = elements the
   role's selectors reach; `checked` = eligible rendered text among them that was measured; `mismatched` = checked
   elements whose computed value is not the previewed value. Matched elements with no rendered text are not failures
   (4410). Loss lines `<count> x <property>: <reason>` with the seven reasons verbatim from `ROLE_LOSS_TEXT` (3888-3895):
   `overridden by <selector>`, `overridden by inline style`, `inherits from parent via <selector>`, `a stylesheet could not
   be read`, `overridden; source not provable`, `the page disabled the preview sheet`, `not attributed in time`. Add the
   rule behind them: a losing page rule is reported, not fixed with `!important` (plan 893-895). At most 16 losses per
   property are listed (D071). Incomplete cases: `Preview applied; checks incomplete (budget-exceeded).` and `Preview
   applied; page changed before checks finished` (4651, 3883). A preview whose page re-rendered is shown as applied with a
   stale measurement; press Detect, then Apply again to recheck (plan 913-923, 4661).
   Say: the check reads computed styles, so it proves the requested value reached the element, not which physical font file
   painted; no claim about glyphs (plan 1358).

7. **Role-preview output boundary.** Heading text in Studio is `Role preview; file output comes later` (1268). State: the
   panel shows the exact stylesheet text the page holds, with its checksum; Copy, Download, Sync to file, the Changes
   panel, exported JSON and saved overrides do not carry role preview (`fontkit-studio.html` 3743, "Role observations
   never enter the mutation queue, saved overrides or exports"; confirm Sync and the export paths by reading them). Writing
   role output to files is future work (R4 in `docs/roadmap/product-direction.md`; do not link planned releases as if
   shipped). Reload, reconnect and pop-out do not push the preview back: the new document has none, and you press Apply
   again (plan 1060-1063, 4994 `ROLE_DROPPED`).

8. **Visited pages** (own subsection `#### Visited pages`). Exact Studio wording users see, each with its source:
   summary `Checked on N visited pages. Other pages have not been checked.` (`Checked on 1 visited page. Other pages have
   not been checked.` for one; hidden until a page is stored: Addendum 27 item 3, 4232); list labels `Checked on:`, `No
   match on:`, `Different style on:` (line `<selector>: expected <tuple>, found <count> x <tuple>`) and `Changed since
   checked:` (4202, 4209); `The page changed since the last Detect; press Detect text styles. This page has not been
   checked.` (3754); `The page's reply to Detect was out of date; press Detect text styles again; this page has not been
   checked.` (3752); `Collection limit reached; this page was not stored` (3755) and `Collection limit reached, so
   Apply is disabled until you clear visited pages.` (4350); `A new Live App origin started a new collection; visited
   pages from the previous origin were cleared.` (3757); `Visited pages cleared. The applied preview and inspector edits
   stay.` (3758). Explain in plain words: you move through the app yourself and press Detect on each page; Studio keeps the
   latest result per page (path, query and hash), replacing it on a revisit. The page list is session-only and per
   origin: nothing is saved, exported or sent to your app except the known role selectors in the next Detect; closing or
   reloading Studio forgets it. There is no crawling and no whole-site count; "N visited pages" are pages you pressed
   Detect on. Limits: 128 roles, 32 selectors per role, 8 distinct reference styles per role and 32 pages; a page that
   would pass a limit, or make the next Detect request exceed 256 KiB, is refused as a whole and earlier evidence stays
   (plan 1034-1041, Addendum 27 items 1-2, D076). `Clear visited pages` forgets the evidence and keeps the applied preview
   and the ids of roles in it (Addendum 27 item 5). A different Live App origin starts a new collection. Same-origin
   reload, reconnect and pop-out keep the page list but need Apply again.

9. **Page changes and what the bridge notices.** State the page version rule in user terms (D063, D066): URL, rendered
   content, author styles and viewport changes mark earlier results as out of date; the bridge's own writes, hover and
   focus, and font loading do not. Route changes through `pushState`, `replaceState`, back and forward, hash changes and
   the browser's back/forward cache are noticed automatically and coalesced to at most one note per 250 ms
   (`fontkit-bridge.js` 1272-1290, 1371; R2.6B1/R2.6B2 reports). Known limits, each one bullet, user wording:
   - App code that saved the browser's own `history.pushState` or `replaceState` before the bridge connected bypasses the
     bridge's wrapper. The next Detect, Apply or Clear, `popstate`, `hashchange` or a render still notices (6b1 Handoff).
   - CSS added with `insertRule` and no visible DOM change is not announced; press Detect again (plan 1067-1069). A page
     frozen without a `pageshow` event is also seen only by the next Detect (6b2 Handoff).
   - Studio's fullscreen and device-width buttons resize the page, which counts as a page change (D063): Studio shows the
     page-changed sentence and asks for a fresh Detect; role rows and the applied preview stay (Addendum 27 item 6).
   - A page whose address is over the 2,000-character route limit shows `Role detection/preview unavailable: unsupported
     page URL.` (3748, D061); the inspector still works.

10. **Cascade limits (Addendum 24 item 1; all four, user wording).** Put them in a `#### Known limits` list:
    - A Bootstrap 5 Body or Monospace receipt measures only the role's own selectors. Text that inherits the `:root`
      variables outside them changes without being measured. Studio says so on the Body row: `applies page-wide through
      Bootstrap's body variables, and inherited text is not measured` (4408).
    - A component with its own size rule (Bootstrap's `.btn`) keeps its size under a Body role.
    - A later author `body { ... }` rule of equal specificity outranks the Body block.
    - An element that declares the font variables again and is read directly (`<body data-bs-theme>`, a tooltip) shows the
      same blind spot.
    Then also: shared-class groups, `complex-cascade` (above), cross-origin stylesheets the page cannot read, and `@layer`,
    animations and inactive media rules are reported as unknown or as losses, never guessed (plan 1340-1356).
    Version skew (D075, Addendum 26): Studio and a bridge of another 0.4.x/later release keep working when a reply gains
    fields (role revision 1; Studio ignores unknown reply keys and stores none). A bridge without `roleRevision`: Studio
    shows `This bridge does not support role detection/preview.` A reply Studio cannot read is shown:
    `Studio could not read the page's reply to Detect; this page has not been checked.`, `Studio could not read the page's
    reply; the preview on the page may differ from what Studio shows.`, and a Detect with no answer within 8 seconds:
    `The page did not reply to Detect; this page has not been checked.` A bridge that is older than 0.4.0 has no role
    support; update the bridge script or `fontkitstudio`. Exported JSON stays `0.1.1`; protocol stays 1.

11. **Entrypoints.** Say in one sentence, in the new section, that Detect, Apply, re-render and Clear work the same through
    `npx fontkitstudio`, the Vite plugin on Vite 7 and 8, the loopback proxy (checked on a Bootstrap 5 page under a strict
    Content-Security-Policy) and the proxy in front of Next.js (source: `tests/test_r2_entrypoints.py`, R2.7I1 report).
    Do not change the existing Quickstart or recipes except Requirement 12. Say a Vite `build` ships no bridge and no role
    CSS (same report).

12. **Sweep fixes in existing text** (each a real stale claim):
    a. `README.md` 101: replace the forwarder sentence. New text: the old name `font_kit_studio_v0.1.1.html` was removed in
       0.4.0; move bookmarks to `fontkit-studio.html` (query and hash are kept only if you retype them; the old file no
       longer forwards). Keep the rest of the line (version in the tab title; opening from disk).
    b. `README.md` 44: keep "0.3.0 or later" for the command, and add that text-style roles need 0.4.0 or later.
    c. Protocol v1 (`README.md` 522-583): add to "Studio to bridge" rows `design:detect`, `design:roles-apply`,
       `design:roles-clear` with their fields from plan 831-835; to "Bridge to Studio" rows `design:detected`,
       `design:roles-applied`, `design:roles-page`; extend the `design:ready` row with `roleState` and capabilities
       `roleDetection`, `roleStylesheet`, `roleRevision` (value 1 in 0.4.0; bridge `fontkit-bridge.js` 1220); extend the
       `design:rejected` row with `page-changed`, `stylesheet-blocked`, `size-limit`. Add one sentence: requests stay strict
       (the bridge refuses unknown request fields); replies are read tolerantly (Addendum 26). Link the plan, not a copy of
       its tables (anti-duplication rule).
    d. Test table (`README.md` 636-660): fix the `test_studio_rename.py` row to what it now asserts (read
       `tests/test_studio_rename.py` at BASE: the new file opens directly with its query and hash, and the old file is
       absent). Add one row per missing module, one clause each, after reading its docstring or first tests. Find them with:
       `for f in $(git ls-tree --name-only 5d28252 tests/ | grep 'test_.*\.py$' | sed 's#tests/##'); do git show
       5d28252:README.md | grep -q "$f" || echo $f; done`. Do not invent a covers-clause you did not read.
    e. "Known gaps" (`README.md` 700-715) and "Roadmap" (716-720): state that role detection and preview ship in 0.4.0 and
       pairing, scales, token output and the extension (R3 to R5) are not built; link `docs/roadmap/product-direction.md`.
       Never present R3-R5 as shipped. No release-date claim beyond what the CHANGELOG states.
    f. Sweep every other README line that names a version, the file name, `roleDetection` or R2: run
       `git grep -n -i -E "0\.3\.[01]|0\.2\.|v0\.1\.1|R2|role" 5d28252 -- README.md packages/fontkitstudio/README.md
       CONTRIBUTING.md`. Leave historical statements (the 0.3.1 cookie note at 518 is a dated upgrade note) and the
       provenance links; report each hit you leave and why.

13. **Package README** (`packages/fontkitstudio/README.md`): add one paragraph under "Use it": from 0.4.0 the bridge in the
    package also supports text-style roles (Detect, preview and clear in Studio's Live App view); it changes nothing in
    your project; link to the root README section `#detected-roles` (check the anchor GitHub makes from your heading).
    Do not mention roadmap releases.

14. **Screenshots (controller step, not yours).** Name in the report which README images would change because of your
    text: none of the existing six change on their own (`live-app-desktop.png`, `live-app-mobile.png`,
    `code-panel-*.png`, `arrange-*.png`, `pop-out-desktop.png`, `bridge-bar-desktop.png`) unless the Live App view's layout
    changed with the Detected roles panel (Addendum 7, D062 puts the panel below the preview). Say whether a new image of
    the Detected roles panel is needed; propose the `capture.py` step (`docs/assets/screenshots/capture.py`) and its
    file name, but write no image link in the README for a file that does not exist. Reference nothing you cannot
    resolve.

15. **Known-limits coverage (from `w3-known-limits.md`).** Included: Requirements 10 (four BS5 items), 9 (history cache,
    `insertRule`, fullscreen/device width), 8 (visited pages, per origin), 5 (strict `style-src`), 10 (version skew). The
    forwarder item is Requirement 12a. Nothing is left out. If you leave a line out, say why in the report.

## Verification (your report must show it)

- A table of every user-visible string you quote in the README and the `file:line` at BASE where it appears. Run:
  `for s in <each quoted string>; do git show 5d28252:fontkit-studio.html | grep -c -F "$s"; done` (use a short script in
  the session scratchpad named `rd-strings.py`; write it with the Write tool). Each count must be at least 1. A string
  built by template (`Checked on ${n} visited page`) is checked by its constant parts; say so.
- Line endings: tracked Markdown is CRLF in this working tree and LF in the index. Edit with a byte-level script that
  asserts exactly one match per replacement and pure CRLF afterwards; count endings with Python, not `grep -c`. Write
  multi-line Python with the Write tool, never a heredoc.
- `git diff --check` clean; no `Co-authored-by`, model, tool, reviewer or round-count words in the added text; run
  `git grep -n -i -E "claude|codex|copilot|sonnet|reviewer|fix round" -- README.md packages/fontkitstudio/README.md` on
  your tree and show it unchanged from BASE.
- Anchors: every new in-page link resolves to a heading you wrote or kept (`#detected-roles`, `#code-panel` and so on);
  list them.
- Gates (none run browsers): `python scripts/verify.py --static-only` (it must still pass; the README is not checked by it,
  but report it) and `git diff --check`. Other gates are not run; say so.

## Focused command

None (documentation only). Run the two checks above from `C:/fks/trd`.

## Handoff

Commit subject: `docs: document text-style roles, visited pages and their limits` (max 72). Body draft (wrap 72): why a
reader needs it (Detect, preview and the visited-page list shipped without any README text; stale forwarder and protocol
text), no process state. Return in the report: the string table, the list of test-table rows added, the screenshot
question, each README hit left alone with its reason, and the lines you changed outside the new section. The landing adds
the CHANGELOG entry, the label sweep and the screenshot regeneration.

## Open questions

1. **Package version wording.** The command line at README 44 says `fontkitstudio` 0.3.0 or later. Options: (a) keep 0.3.0
   for the command and add "roles need 0.4.0" (Requirements 1 and 12b), (b) raise the sentence to 0.4.0. Recommend (a): the
   command itself did not change in 0.4.0.
2. **Roadmap link depth.** Requirement 7 names R4 only as "future work". Options: link `docs/roadmap/product-direction.md`
   or name no release. Recommend the link, with the words "not built".
3. **Sync and export negatives.** Requirement 7 says Sync and exports do not carry role preview. If reading the sync and
   export paths shows any carries role state, stop and report; do not soften the sentence.

## Controller rulings (2026-10-18)

1. As recommended: keep "0.3.0 or later" for the command and add that role detection and preview need 0.4.0.
2. As recommended: link `docs/roadmap/product-direction.md` with the words "not built"; never name R3-R5 as shipped.
3. As recommended: if Sync or an export carries role state, stop and report; never soften the sentence.
4. Screenshots: no image is regenerated in this slice; whether to add a Detected roles image is decided at the
   release-point screenshot step.

## Revision 1 (2026-10-18; brief review findings folded by the controller, `task-rd-brief-review.md`)

- I1 (requirement 1): the Detected roles panel is in the Live App view and, before a connection, reads
  `Connect a Live App to detect text styles.` (fontkit-studio.html ~4099). Say that; do not say it appears only after
  Studio connects.
- I2 (requirement 2): list all seven incomplete-scan reasons: `time-budget`, `element-limit`, `group-limit` (128
  groups), `variant-limit`, `identity-limit`, `reply-limit`, `page-changed` (bridge ~2118-2131, Studio ~3761), each in
  plain words.
- I3 (requirement 11): the entrypoint tests run the one command over the Vite 7 and 8 fixtures (not the permanent
  plugin), and the proxy test serves `style-src 'self' 'unsafe-inline'` (tests/test_r2_entrypoints.py:31). Word the
  sentence to claim only that, and keep it consistent with the strict `style-src` known limit.
- I4 (requirement 4): the Bootstrap 5 body/mono `:root` variable block is written only when the role sets a font
  family (D069); otherwise only the plain block.
- I5 (requirement 12f): also fix README ~593 ("The bridge only accepts the values in the patch table above.", now stale
  for role values) and ~442 (inline styles), and widen the sweep regex so siblings of these claims are found.
- Minors: adopt each of the review's ten Minor fixes as written; if one cannot be done, say why in the report.
