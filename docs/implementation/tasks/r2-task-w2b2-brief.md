# R2.W2B2 brief: display headings by class, names from every class, Detect under a variable preview, adapter pins

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 items 2 and 3 and its R2.W2B2 task, Addendum 21, D069, D073, the
binding contract's "Detection and performance". PR B2 wave W2. BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`. Worktree
`a scratch worktree` (detached at BASE; the controller creates it), task id `w2b2`. Two phases, each a new agent: **phase 1**
(bridge changes and their tests) codes beside R2.W2T and R2.W2L; **phase 2** (tests that kill the adapter mutants the review
found) starts in the same worktree from phase 1's patch. Line budget: phase 1 about 220 gross lines, phase 2 about 320;
explain any excess.

## Why

The whole-branch review (workspace `w2-review.md`; every item checked in source) found:

- **P6 (Addendum 22 item 2).** The heading step (`fontkit-bridge.js` 1815-1822) binds a display heading group to its tag
  first. For `<h1 class="display-1">` that is `h1`, which loses font-size and font-weight to Bootstrap's own
  `.display-1{font-weight:300;line-height:1.2;font-size:calc(1.625rem + 4.5vw)}` (vendored
  `fixtures/bootstrap5-static/vendor/bootstrap.min.css`) by specificity: the preview changed only the family.
- **P3 (Addendum 22 item 3, D073).** `run()` in `detectTextStyles` (1916-1934) turns the owned sheet off and on around every
  8 ms batch (`suspendRoleSheet` 1324-1339). With a `:root` variable block in the sheet each toggle restyles the whole
  document, so a batch reads 3-4 elements instead of about 75, and a re-Detect ends `time-budget`. Measured on the
  5,000-parent corpus with both body variables and `body { font-family: var(--bs-body-font-family) }`: no preview 260-360 ms,
  plain preview 1,000-1,700 ms complete, body preview with a family 12 of 12 runs `time-budget` after 38-246 of 5,000
  elements; a body role without a family, or with the page's own family, completes in 11 of 12 runs (one `time-budget` at
  2,005 ms each), and plain previews reach 1,982 ms: the existing plain-preview test (`test_role_stylesheet.py` 904) is
  itself marginal here, and a red there is not caused by this task. On real Bootstrap 5 with a real font the
  body preview ends `time-budget` from about 1,500 added text parents, while a plain preview finishes 2,500 in 0.4 s.
- **P8.** Bootstrap names are looked up in `group.sharedClasses` (1846), which 1807 has cut to 16, so a 17th shared class
  such as `btn` is never found and the group is named `Text`.
- **Test gaps (phase 2).** Each mutant below passes every test at BASE (T9 and T14 are gaps, not mutants):
  - T1: Apply evidence `found.body && found.sans` (1412) changed to `||`: 89 tests pass.
  - T2: deleting the `.display-N` accept line (241) or requiring two heading selectors: every adapter test passes.
  - T3: the heading level or display read from the first claim only (1809, 1810): 29 of 29 pass.
  - T4: mono for any group (`&& monos[0] === group` dropped at 1843): 37 of 37 pass, although all 19 groups become mono.
  - T5: heading claims and the heading step without Bootstrap 5 evidence (1805, 1815): the five bridge role modules pass.
  - T6: the variables read from `document.body` instead of `:root` (1276): 37 of 37 pass.
  - T7: heading before mono, the single-signature rule (1836), author-role groups taking adapters (1845), and the name
    priority and `BOOTSTRAP_NAMES` order (1846-1847): each mutant passes.
  - T9: `test_a_heading_tag_that_matches_a_non_member_binds_by_class_and_stays_plain` (132) applies a hand-written
    `['.h2']` role (146-149), not the detected group.
  - T14: no test shows the `:root` variables changing a rendered font. The fixture's `app.css` pins
    `body { font-family: sans-serif }`, so only custom-property read-backs prove the variable path.

## Owned files (exact)

- `fontkit-bridge.js`: the heading step in `roleBindings`, the name lookup (`roleBindings` and `suggestBootstrapAdapters`),
  and `run()` in `detectTextStyles` with whatever per-job flag it needs. Nothing else: R2.W2B1 changes the family rule,
  `verifyRoleSheet`, `handleRoleMutation` and `getCurrentTokens` after you, on your patch.
- `tests/test_role_adapters.py` (both phases).
- `tests/test_role_stylesheet.py`: only `BaselineDetectTests` (phase 1, one new test beside
  `test_detect_never_drops_the_preview_between_frames_on_the_5000_parent_corpus`). Keep its constants inside the test or
  its class: R2.W2B1 rewrites the module header (`EMPTY_HASH` at 10, `fnv1a32` at 38) after you.
- The `:root`-block predicate (do the accepted roles hold a `bootstrap5-body` or `bootstrap5-mono` role with a family?)
  is one named function, `rolesHaveRootBlock(roles)`, beside `roleCssBlocks`: R2.W2B1 calls it from `getCurrentTokens`
  instead of writing a second copy.

Read-only: `fontkit-studio.html`, `tests/role_contract.py`, `tests/role_support.py`, the fixtures and every other test.
Running worktrees beside yours in phase 1: `a scratch worktree` (R2.W2T: `tests/role_contract.py`, `tests/test_studio_roles.py`,
`tests/test_role_protocol.py`, `tests/test_r2_react.py`), `a scratch worktree` (R2.W2L: `tests/test_studio_live.py`) and
`a scratch worktree` (R2.W2S-a: Studio's serializer, `tests/test_r2_integration.py`); in phase 2, R2.W2B1 in `a scratch worktree` and
R2.W2S-b in `a scratch worktree`. Never touch them.

Addendum 23 (D074) changes this code after W2 lands, in R2.W2P: a `data-design-role` group gets no Bootstrap adapter, and
the Body group binds `body`. Do not implement or test that here; SIMPLIFY2 and SIMPLIFY5 (workspace `w2-review.md`) also
move to R2.W2P, after your phase 2 tests cover those lines.

## Read first

`constraints.md` (all of it); Addenda 17, 21 and 22; D058, D067, D069, D073; at BASE `fontkit-bridge.js` 168-311,
1266-1346, 1780-1849 and 1851-1994; `tests/test_role_adapters.py` (all, 519 lines); `tests/test_role_stylesheet.py` 1-80
and 870-945; `tests/role_support.py`; this brief's review (`task-w2b2-brief-review.md`: verified pages for T3-T7 and
T14). The review's mutant copies are in
`the scratchpad/cr23`
(`cr23-A-m*.js`, `cr23-main-M2..M5*.js`, `cr23-B-mut*-bridge.js`); they are against BASE line numbers.

## Phase 1: bridge changes and their tests

1. **Display class first (Addendum 22 item 2).** In the heading step, a group with one display class tries
   `.${display}` first and its level's `hN`/`.hN` only when the class does not fit; a level-only group is unchanged. The
   group keeps its name (`Heading N` when every member states the same level, else `Display N`) and `bootstrap5-heading`.
   Update the step's comment. Tests:
   - `test_the_heading_level_wins_over_a_display_class_when_the_tag_fits` (294) asserts the old order; it becomes the new
     rule (the group binds `[('.display-1', 'class', True)]`, still `Heading 1`, `bootstrap5-heading`). Rename it to say so.
     This is an existing test changed for an intended behaviour change: say so in the report.
   - `test_the_display_class_is_tried_when_the_heading_tag_matches_a_non_member` (302) still passes, but under the new
     order it covers the first leg (the class is tried first): rename it and rewrite its docstring to say so.
   - A new fallback test (characterization, green at BASE and after the swap, not RED): on `HEADING_PAGE`,
     `<h1 class="display-1" style="font-size: 41px">Shown</h1>` beside a non-member `<p class="display-1"
     style="font-size: 43px">Other</p>`; the `Shown` group is `Heading 1`, `bootstrap5-heading`, bound
     `[('h1', 'class', True)]` (the class does not fit, so the level is tried). Oracle: the markup.
   - A new Detect-then-Apply test with an observable result: the protocol page (`ROLE_PAGE`, no headings of its own) with
     the vendored Bootstrap 5 stylesheet linked before hello (`TARGET + '/fixtures/bootstrap5-static/vendor/bootstrap.min.css'`)
     and two `<h1 class="display-1">` without inline sizes. Apply the detected group as received (`received()`) with
     `fontSize` 41, `fontWeight` 700 and a family. Then both headings compute 41px and 700 and the family, and the receipt has
     no loss. The oracle is the requested values. At BASE this is RED (the headings stay 80px and 300).
2. **Names from every shared class (P8).** The Bootstrap name lookup uses every class all members share, not the 16 the
   reply carries. No new wire field. Test: on the protocol page with both variables (`HEADING_PAGE`), a
   `<button class="u0 ... u15 btn" style="font-size: 41px">` (16 utility classes, then `btn`) gets the name `Button`. RED at
   BASE (`Text`).
3. **Detect batches under a variable preview (Addendum 22 item 3, D073).** Only while the accepted roles include a `:root`
   block (a `bootstrap5-body` or `bootstrap5-mono` role with a family), each batch measures the restyle that suspending the
   sheet causes (one forced style and layout read of the document element right after `suspendRoleSheet`), resets the
   batch clock after that forced read, and then reads for `max(8, 2 * restyle)` ms instead of 8 (the review measured
   457-1,248 ms complete with the clock reset, against 768-1,248 ms without). Without such a block, `run()` behaves exactly as at BASE (no forced read, 8 ms).
   The preview is restored before every yield and the 2,000 ms budget is unchanged. Test in `BaselineDetectTests`, modelled
   on the 5,000-parent test at 904: before hello, add both body variables and `body { font-family: var(--bs-body-font-family) }`
   to `fixtures/large-page`; apply a `bootstrap5-body` role on `.g00` with a family other than the page's; sample every
   animation frame during the Detect. Then the reply is complete, scans 5,000 elements within 2,000 ms, spans more than two
   frames while the heartbeat advances, every sampled frame shows the preview's family (on `.g00` and on an element that
   takes its family only from the variable), and the `.g00` group reports the page's own family. RED at BASE
   (`time-budget`). Run it three times, and once beside another browser shard, and report every elapsed time; if it cannot
   pass reliably on Windows Chromium, stop and report the timings (the owner asked to be told).

4. **Comment slips.** `tests/test_role_adapters.py` 23 says `FIXTURE_GROUPS` holds (name, adapter); it holds names. The
   bridge comment at 1943 says "before any evidence"; the evidence read now comes first. Correct both.

Mutants (phase 1): the display-first order reverted (the changed test and the new Apply test fail); the level fallback
removed for display groups (`display ? choose([.display]) : levels.length && choose(levels)`; the new fallback test
fails); the lookup back on `sharedClasses` (the button test fails); the batch rule disabled (the new Detect test fails
`time-budget`); the restore skipped after a long batch (the frame samples fail). One accepted survivor, to record in the
report: the batch rule always on (it changes only timing for plain and absent previews, which no test can pin).

Known limit to name in the report (ALT3, not fixed here): a level-only heading group still binds its type selector,
which can lose to the app's own single-class rule; display-first fixes only `.display-N`.

## Phase 2: tests that kill the review's mutants (tests only, `tests/test_role_adapters.py`)

Start from phase 1's patch applied in the worktree; take mutants against that bridge (its line numbers). Each test asserts
what the page or the reply shows, with its oracle from the plan, the fixture markup or a literal:

- T1: on `ROLE_PAGE` with exactly one of the two body variables (each one in turn), Apply of a `bootstrap5-body` role is
  refused `unsupported-value` / `Unsupported adapter` and installs no owned sheet.
- T2: the accept side of `test_a_heading_role_must_name_one_level_or_one_display_class` (465) gains `['.display-1']` and
  `['.h3']`, each applied and rendering its size on the matching fixture elements, and `['h3']`: accepted
  (`design:roles-applied`, the owned node holds `h3 {...}`), a bare `<h3>` added with ADD_HTML computes the requested
  size, and `h3.h3` keeps 28px (Bootstrap's `.h3,h3` rule matched through `.h3` outranks the bare tag; assert the
  receipt's one `fontSize` loss as it states it). Mutants: `cr23-main-M3-no-display.js`, `cr23-B-mut2-bridge.js` (only the
  single-selector cases kill it).
- T3: the mixed level group of the test at 132 is named `Text` (assert the name), and a new mixed display group (two
  elements of one style, the `display-1` element first in document order, then one with no display class) is named
  `Text`. Mutants: `cr23-main-M4-level-first.js`, `cr23-main-M5-display-first.js`.
- T4: in the two-`<code>` test (166) exactly one group is `bootstrap5-mono` (the code group), the (16, 400) group is
  `bootstrap5-body` and every other group is plain; key groups by sample text (the code group collides with Small on size
  and weight). Mutant: `cr23-A-m2-mono-any-group.js` (all 19 become mono).
- T5: on the Bootstrap 4 fixture with ids stripped, each heading group binds what its markup allows without a heading step
  (its shared class when that fits, else a dom path), never `["hN", ".hN"]`. Take the expected bindings from the fixture's
  HTML.
- T6: a page that defines both variables on `body` only has no evidence. Give it two candidates, `<p>Inherits</p>` and
  `<button class="btn" style="font-size: 41px">Pressed</button>`, and assert per sample text (the page's own
  `data-design-role="Body"` group is named `Body` at BASE): both are plain and named `Text`, and Apply of a
  `bootstrap5-body` role is refused `Unsupported adapter`. Mutant: `cr23-A-m10-vars-from-body.js`.
- T7 (the review's verified pages; one page each on `HEADING_PAGE`, plus `:root { --bs-font-monospace: monospace }` where
  needed): a heading group whose family equals `--bs-font-monospace` is `bootstrap5-heading`, not mono; an author-role
  group of two variants whose first equals body's style stays plain; a heading title wins over an adapter name (bind the
  heading with a `data-design-id` so the heading step does not claim it), which wins over a class name (`<p class="btn">`
  equal to body's style is `Body`); and among classes the first `BOOTSTRAP_NAMES` entry wins (`class="btn lead"` is
  `Lead`). Do NOT test that a lone author-role paragraph equal to body's style gets `bootstrap5-body`: Addendum 23 makes
  it plain in R2.W2P. The plan fixes no adapter precedence, name priority or `BOOTSTRAP_NAMES` order; say in the report
  that these tests pin the current decisions as literals (sources: bridge comments 177 and 1832-1833, the test at 235).
- T9: the test at 132 applies the detected `.h2` group as received instead of a hand-written role. No new mutant: the
  binding assertion (141-142), not the render check, proves the exclusion (`.fs-6` is `!important`); say so in its
  docstring.
- T14: on the Bootstrap 5 fixture, after Apply of the detected Body group with a family, a
  `<div class="tooltip" role="tooltip">Tip text</div>` added with ADD_HTML (its family comes only from Bootstrap's
  variables; it is transparent, so not eligible text and the groups do not change) renders that family, and after Clear
  its own again. It characterizes the rendered effect; its mutant (`ROLE_VARIABLES = {}`) is shared with the table-case
  read-back test.

Every new or changed test has a Given/When/Then docstring whose Then is exactly what it asserts. Record, per new test, the
mutant it kills (the T-list mutants above, re-based on phase 1's bridge; the review's copies show the edits).

## Rules for both phases

Mutants run in the foreground, in your worktree or through `RoleSheetCase.open(..., bridge_source=...)`; the bridge is
restored byte-exact and its SHA-256 recorded before and after. Expected values never come from the bridge's own output.
A failing green is worse than a true red: report a red you cannot explain as red; never weaken, skip or retime a test.

## Focused gate

From the worktree, in Git Bash. Phase 1:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_role_adapters test_role_stylesheet test_role_detection test_role_preview test_support`.
Phase 2: `... focused test_role_adapters test_support`. Both: `node --check fontkit-bridge.js` (phase 1),
`python -m ruff check` on changed Python files, and after staging by name `git diff --cached --check`.

## Report and handoff

One report, `task-w2b2-code-report.md`, with a section per phase: each change and its RED (the failing assertion at BASE);
each mutant (command, failing tests and lines, SHA-256 before and after); the focused runs (Ran line, OK, GATE line); the
three Detect timings; gross and material lines. Patches: phase 1 `task-w2b2-code.patch` (against BASE), phase 2
`task-w2b2-code-p2.patch` (phase 1 plus phase 2, against BASE). Commit subject
`fix(bridge): bind display headings by class and keep Detect fast` (64 characters), a draft body (why, wrapped at 72, no
process narration), a draft CHANGELOG sentence under Unreleased in product terms (display headings now preview their size
and weight; re-detecting under a Body or Monospace preview finishes on large Bootstrap pages; Bootstrap names found past
16 shared classes), and the R2.W2B2 plan item.
