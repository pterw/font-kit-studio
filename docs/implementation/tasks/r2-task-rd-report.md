# R2.RD code report (mode: code, worktree C:/fks/trd, BASE 5d28252)

Status: DONE_WITH_CONCERNS (concerns are the open questions below; none blocks).

## What changed (patch: `.superpowers/sdd/r2c/task-rd-code.patch`, 2 files, +171/-9)

- `README.md` (+169/-9): new `### Detected roles` section (11 subsections) between Code panel and Arrange; edits outside it listed below.
- `packages/fontkitstudio/README.md` (+2): one paragraph under "Use it", after the flag table, with the absolute link `https://github.com/pterw/font-kit-studio#detected-roles`.
- `CONTRIBUTING.md`: read, not edited. Its only hit is line 24 (`supplied-v0.1.1` tag fetch), which is true. No role, version or forwarder claim.
- Line endings: README.md stays pure CRLF (891/891 by Python count); package README stays LF (it was LF at BASE: 0 CRLF). Every replacement asserted exactly one match.

## Sections of the new text, by brief requirement

Subsections: What Detect reads (R2), Roles and bindings (R3), Adapters (R4 + I4), Preview, Apply and Clear (R5), Receipts and losses (R6), Role preview output (R7), Visited pages (R8), Page changes (R9), Version differences (R10 skew), Known limits (R9 limits + R10 cascade, said once at the end). The intro and "Requires" paragraph carry R1 and R11 (I1, I3). Planning labels (D-numbers, Addenda, R3-R5, handoff names) appear nowhere in the README text (grep of added lines: none).

## Edits outside the new section

| README line at BASE | Change |
|---|---|
| 44 | Kept "0.3.0 or later" for the command, added that text-style roles need 0.4.0 (ruling 1). |
| 101 | Forwarder sentence replaced (removed in 0.4.0, no longer forwards, bookmarks move, query/hash kept only if retyped). |
| 442 (Tailwind) | Added: role preview uses one bridge-owned stylesheet instead of inline styles. |
| 536-566 Protocol v1 | Rows `design:detect`, `design:roles-apply`, `design:roles-clear`; `design:detected`, `design:roles-applied`, `design:roles-page`; `design:ready` extended (`roleState`, three capabilities, `roleRevision` 1); `design:rejected` extended with `page-changed`, `stylesheet-blocked`, `size-limit`; one paragraph on strict requests and tolerant replies linking the plan. |
| 583 (Patch keys) | Added: these keys are for the inspector; roles use own messages (stale-claim sibling of 593). |
| 593 (Security) | "only accepts the values in the patch table above" extended to the six role properties; added what Detect sends (sample up to 200 characters, selectors, computed styles; kept in memory). |
| 636-660 test table | `test_studio_rename.py` row fixed; 15 rows added (below). |
| 709-715 Known gaps | One bullet: role preview never written to a file; visited-page list lost on close or reload. |
| 716 Roadmap | One sentence: role detection and preview ship in 0.4.0; font pairing, type scales and token output are not built. The existing extension sentence and roadmap link stay. |

Test rows added (module: clause source): test_localhost_cookies (module docstring + `COOKIES` tuple), test_role_detection, test_role_stylesheet, test_role_preview, test_role_adapters, test_role_protocol (class names + first test), test_role_route_bridge (docstring), test_role_routes (docstring), test_studio_roles (docstring), test_r2_integration (the four test docstrings I read: fullscreen, reset-all, blocked stylesheet, unsupported URL), test_r2_react (module docstring + test docstrings 450/495/542), test_r2_route_fixtures and test_r2_static_fixtures (module docstrings), test_r2_entrypoints (docstring, test names), test_release (docstring). Not added: `test_frontend_gate_helpers.py`, `_report.py`, `_runner.py`, already covered by the existing glob row `test_frontend_gate_*.py` (brief-review Minor 5), so 15 rows, not 18.

## Sweep (R12f, widened per I5): hits left alone

`git grep -n -i -E "0\.3\.[01]|0\.2\.|v0\.1\.1|R2|role|only accepts|inline style|no page data|is now|goes away" 5d28252 -- README.md packages/fontkitstudio/README.md CONTRIBUTING.md`

- README 270-271 (Composer "role" = slot role), 454, 461 (`data-design-role` attribute), 644 (`font tokens follow a slot's role`): different meaning, true.
- README 518 and package README 50: the dated 0.3.0 to 0.3.1 settings note (kept, historical).
- README 524 and 724-725: protocol requirement file names (`...v0.2.0...`) and provenance links; names of files that exist.
- README 530, 555, 591 "no page data": about `design:bridge-ready`, still true.
- README 620, 722 and CONTRIBUTING 24: the `supplied-v0.1.1` tag and original file; true.
- README 705 (CI text, matched `role`/`R2` inside other words) states no version, file name or capability falsely.
- README 442 and 593 were stale and are fixed (I5). README 313, 335 (CI runs), 359: still true.

## Verification

String table (every quoted user-visible string, checked with `rd-strings.py` against `git show 5d28252:fontkit-studio.html`; templates checked by their constant parts, shown whole where they matched as written). Result: `all strings found 0` (zero misses). All 71 rows count at least 1:

| String | count | line | | String | count | line |
|---|---|---|---|---|---|---|
| Detected roles | 1 | 1251 | | Detect text styles | 6 | 1252 |
| Connect a Live App to detect text styles. | 3 | 1253 | | Light-DOM text only | 1 | 1255 |
| Detected values are the page baseline, measured without the role preview. | 1 | 1256 | | Apply selected roles / Clear preview / Clear visited pages | 1 each | 1261-1263 |
| Reset all page edits | 6 | 1275 | | Role preview; file output comes later | 1 | 1268 |
| This bridge does not support role detection/preview. | 1 | 3747 | | Role detection/preview unavailable: unsupported page URL. | 1 | 3748 |
| Studio could not read the page's reply to Detect... | 1 | 3749 | | The page did not reply to Detect... | 1 | 3750 |
| Studio could not read the page's reply; the preview on the page may differ... | 1 | 3751 | | The page's reply to Detect was out of date... | 1 | 3752 |
| The page changed since the last Detect... | 1 | 3754 | | Collection limit reached; this page was not stored | 1 | 3755 |
| A new Live App origin started a new collection... | 1 | 3757 | | Visited pages cleared. The applied preview and inspector edits stay. | 1 | 3758 |
| reasons list (seven) | 1 | 3761 | | Bootstrap 5 body variables / monospace variable / heading rule | 1 each | 3882-3883 |
| rejection list (six) | 1 | 3896 | | Preview applied; page changed before checks finished | 1 | 3900 |
| Role preview request dropped... | 1 | 3901 | | ROLE_LOSS_TEXT: seven reasons plus "overridden by an author rule" and "inherits from its parent" | 1 each | 3889-3895 |
| Safe complete bindings unavailable. | 1 | 4129 | | Shared classes: / Near duplicates (kept separate): | 1 each | 4130, 4131 |
| stable / uncertain | 1 | 4125 | | Adapter: + label | 1 | 4128 |
| Checked on: / No match on: / Different style on: / Changed since checked: | 1 | 4202 | | `<selector>: expected ..., found <count> x <tuple>` | 1 | 4211 |
| Checked on ${count} visited page{s}. Other pages have not been checked. | 1 | 4232 | | Collection limit reached, so Apply is disabled... | 1 | 4350 |
| Checks incomplete (budget-exceeded)... (behaviour only) | 1 | 4399 | | `<name> (<id>): matched A, checked B eligible text elements, mismatched C` | 1 | 4407 |
| ...applies page-wide through Bootstrap's body variables, and inherited text is not measured | 1 | 4408 | | `<count> × <property>: <reason>` (U+00D7) | 1 | 4413 |
| Incomplete detection (<reason>); this page has not been checked. | 1 | 4498 | | Detected N roles from M eligible text parents on this page... | 1 | 4501 |
| Preview applied; checks incomplete (budget-exceeded). | 1 | 4652 | | Preview applied to N role(s); M checked element(s) did not show it. | 1 | 4653 |
| NEXT_STEPS (page-changed, revision-conflict) | 1 each | 4661, 4662 | | Role preview apply rejected (<reason>); the previous preview is kept. | 1 | 4668 |

Claims and their proof (code at BASE, plan, or test):

| Claim | Proof |
|---|---|
| Panel is in Live App view, hidden otherwise | `fontkit-studio.html` 4098 `section.hidden = !live.viewActive`; before connect status 3746/4058 (I1) |
| Detect skips head/script/style/template/noscript, overlays, hidden, zero-area, transparent; not form values, pseudo text, shadow roots, frames, SVG | plan "Detection and performance"; Studio 1255 |
| Exact five-property match, size to two decimals; role variants listed | plan "Detection"; bridge 2120-2130 |
| Near-duplicate thresholds (family, case, 1 px, 100, 0.02 em) | bridge 2144-2148; deviations D058 |
| Seven incomplete reasons and their limits (2,000 ms, 10,000, 128 groups, 8 styles, 200-char name, 1 MiB) | bridge 2048-2056, 2112, 2118, 2123, 2131 |
| 5,000 elements in 2 s on desktop Chromium | plan budget paragraph; D058 |
| Binding preference; unsafe row cannot be applied | plan 975-979; Studio 4129, `buildRoleRequest` 4322 |
| Bootstrap 5 evidence from computed `:root` variables, non-Bootstrap page with both variables treated as Bootstrap 5 | D069 (cost column) |
| Body binds `body`; Mono falls back to `code, kbd, pre, samp`; author roles plain; one Body and one Mono | D074; Studio `ROLE_PAGE_MONO` 3884 |
| `:root` block only when the role sets a family | D069 (I4) |
| Field limits | Studio `ROLE_FIELD_HELP` 3874-3879, `ROLE_NUMBERS` |
| Whole set or nothing; Clear removes only the owned sheet | plan 827-845, 943-946 |
| `size-limit` = request over 256 KiB or sheet over 128 KiB | bridge 296, 1532, 2001 |
| Blocked stylesheet case | `tests/test_r2_integration.py` 625-645 (`style-src 'none'`) |
| Loss rule: reported, never `!important`; max 16 per role and property | plan 861; D071 |
| Receipt definitions; unmeasured line | Studio 4403-4413 comments and code |
| Panel shows stylesheet text; Copy/Download/Sync/exports carry no role state | `liveCss`, `liveHtml`, `liveJson`, `doc.live` (3149-3151), Sync PUT body `liveCss()` read at 6741-6746; comment 3743 (ruling 3: negative holds, no stop) |
| Reload/reconnect does not push preview back | Studio 4055, 4075-4079, 5752; plan 1060-1063 |
| Visited pages: latest per route, session only, limits 128/32/8/32/256 KiB, Clear keeps preview | Studio comment 3759; plan 1034-1041; Addendum 27 items 1, 2, 5; D076 |
| Route events noticed, at most one note per 250 ms | bridge 181, 1323-1342, 1272-1290, 1371-1385 |
| Route over 2,000 characters = path+search+hash | bridge 1252; Studio 3793 |
| Version skew rules | Addendum 26 items 1-4 and 6; Studio `ROLE_*` 3747-3752 |
| History-cache, `insertRule`, fullscreen/device-width limits | bridge comment 1368-1371; plan 1067-1069; Addendum 27 item 6 |
| Entrypoint sentence (command on Vite 7/8, Bootstrap proxy with `style-src 'self' 'unsafe-inline'`, Next proxy, build ships nothing) | `tests/test_r2_entrypoints.py` 31, 141-197, 206-254, 255-300 (I3) |
| `test_studio_rename.py` row | the three tests at BASE: opens with query/hash, opens bare, old file absent |

Gates (run in C:/fks/trd): `python scripts/verify.py --static-only` exit 0 (`PASS provenance` lines, `SKIP unittest/browser tests`); `git diff --check` and `git diff --cached --check` clean; `PYTHONPATH=tests python -m unittest test_live_integration.BookmarkletTests` (the README-reading tests; they read the untouched script-tag and bookmarklet lines): `Ran 2 tests ... OK`. pre-commit on both files: `no trailing whitespace or conflict markers in staged lines.......Passed`; ruff, node syntax and static checks `Skipped` (no files to check). Forbidden-word grep: one hit (the commit-message check paragraph, README 703 at BASE, 862 now), unchanged. Other gates not run (no browsers beyond the two README tests).

Anchors: `#detected-roles` (my heading, used in README lines 44 and 442 and 583 and known gaps, and in the package README as the absolute URL), `#preview-apply-and-clear` (my heading, used in Security). No other new link. New relative links resolve: `docs/roadmap/product-direction.md`, `docs/plans/2026-10-03-r2-engine.md` (both exist at BASE).

## Screenshots (R14, controller step)

None of the six existing images changes because of this text. A new image of the Detected roles panel is optional and decided at the release point (ruling 4). Proposal: a `capture.py` step that connects the demo, presses Detect text styles and shoots the `#detectedRoles` section, saved as `docs/assets/screenshots/detected-roles-desktop.png`. No image link was written.

## Open questions and deviations

1. **Checksum not shown.** The brief (R7) says the panel shows the stylesheet "with its checksum". `renderRolePreview` (4382) writes only `rolePreview.css`; the hash is compared internally. The README says the panel shows the exact stylesheet text and says nothing about a checksum (code wins).
2. **Brief said loss lines use `x`**; Studio prints `×` (U+00D7) at 4413; the README uses `×`. The visited-page conflict line does use ASCII `x`; kept as is.
3. **Route limit wording**: the brief (R9) listed `Role detection/preview unavailable...` for "over the 2,000-character route limit"; written as path, query and hash together (brief-review Minor 2).
4. **Roadmap page contradiction (Minor 9, for the landing).** `docs/roadmap/product-direction.md` lines 100-101 still say "Designed, not built: ... Role detection (R2)" and "Shipped (v0.2.1)". The README now links it next to "ships in 0.4.0". The controller owns that file's update.
5. The Body-row note about page-wide variables appears in Studio only on a role whose single selector is `body` (4399-4408); the README says so and states that other Body or Monospace roles still do not measure inherited text.
6. The Heading adapter binding sentence comes from the plan and D069, not from a test I read.

## Handoff

- Commit subject: `docs: document text-style roles, visited pages and their limits`
- Body draft: Detect, preview and the visited-page list shipped with no README text, and the README still described the removed forwarder file, the old protocol and an incomplete test table. Add a Detected roles section (what Detect counts and leaves out, bindings, adapters, Apply limits, receipts and losses, the output boundary, visited pages, page changes, version differences and known limits), add the role messages to Protocol v1, fix the stale forwarder, security and Tailwind sentences, and list the missing test modules.
- CHANGELOG entry, label sweep, screenshots and the roadmap line (Open question 4) stay with the landing.

## Fix round 1

Mode: code. Six Minor findings fixed in `README.md` only (package README unchanged). Patch: `task-rd-code-r1.patch` (whole diff against BASE 5d28252; `git apply --check -R` ok). `task-rd-code.patch` untouched.

| # | Change | Studio line (BASE) |
|---|---|---|
| 1 | Summary now `Preview applied to N roles; M checked elements did not show it.` with a note that "role"/"element" are singular at a count of 1. Rejection quote kept as the prefix, plus a sentence that `page-changed` and `revision-conflict` add a next-step sentence and any bridge detail follows | 4653; 4661-4662 (`NEXT_STEPS`), 4518-4522 (`rejectionDetailText`), 4668 |
| 2 | "Most fields start empty ...; Line height shows `e.g. 1.5`, and Case shows `Unchanged (<observed>)`." | 4281, 4286 |
| 3 | `design:reset` row: "A reset for everything also removes the role preview." | 4551, 4686 |
| 4 | Version differences: "Role messages use role revision 1. A bridge that advertises role capabilities without a valid `roleRevision` is treated as not supporting roles." | 4064 |
| 5 | Visited pages: "Reloading the app, reconnecting or popping out on the same origin keeps the list" | (prose only) |
| 6 | "Requires" bold lead-in dropped; split into "It needs ..." and "..., because the bridge ships in the package."; the 47-word tests sentence also split ("They run the same steps through ..."); sentence "The heading `Role preview; file output comes later` is accurate." removed | (prose only) |

Gates (in C:/fks/trd, README.md staged):
- `python scripts/verify.py --static-only`: all PASS lines, ends `SKIP unittest/browser tests: --static-only`.
- `git diff --check`, `git diff --cached --check`: no output.
- `PYTHONPATH=tests python -m unittest test_live_integration.BookmarkletTests`: Ran 2 tests, OK.
- pre-commit on both READMEs: whitespace hook Passed; other hooks skipped (no matching files).
- Line endings: README.md 891 CRLF of 891 LF (pure CRLF); package README 0 CRLF (LF).

Deviation: the review's Minor 6 names one 50-word sentence; I split both the "Requires" sentence and the tests sentence that follows it.

## Controller integration
