### Spec Compliance
- PASS: Rule 1. `adapter: 'plain'` sits in the group literal (fontkit-bridge.js, `collectRoleStyles`, patch line 241) and `suggestBootstrapAdapters` overwrites it after the binding pass. The limit replies return before binding, so they carry it. Mutant M11 (literal omits it) fails 3 RoleContractTableTests.
- PASS: Rule 2. The scan reads `bootstrapVariables()` and `styleSignature(document.body)` at the top of `collectRoleStyles`, inside the first batch, where `run` already suspended the sheet. Apply reads only when a non-plain role is present, after the page-changed and URL checks, with `suspendRoleSheet(); try {...} finally { restore(); releaseRoleQuiet(); }`.
- PASS: Rules 3 and 4, with the exceptions in Issues and the owner gap in item 7b. Order is author role, author id, heading (evidence only), classes, dom-path. A failed heading step falls through to the class step.
- PASS: Rule 5. `roleCssBlocks` emits the `:root` block and then the plain block. `canonicalizeRoles` keeps `role.adapter`. Both `verifyRoleSheet` callers pass the block count (M6 and M10 killed).
- PASS: Rule 6. `Unsupported adapter` is raised when there is no evidence or when the heading selectors are not what the heading step can emit. The check runs before anything is written.
- PASS: Rule 7 and owned files. Only the four owned files changed. `role_contract.py`, `role_support.py` and the fixtures are untouched. The edits in `test_role_stylesheet.py` (rename, docstring, row label) and `test_role_protocol.py` (`RoleContractTableTests` plus one assertion) match what the brief allows. The bridge comment is updated.
- PASS: Budget. 597 added and 26 removed over 4 files, against about 1,200.
- CANNOT VERIFY FROM DIFF: the commit body and the shared-file steps. These are deferred to landing.

### Checks run
- Patch identity: `sha256sum task-4-code.patch` equals 767311d3...c866e, and `git diff --cached f2b438f` in C:/fks/t4 hashes the same. `git status` and the SHA-256 of fontkit-bridge.js (66813402...a0b0) and tests/test_role_adapters.py (2ee01d49...2a92) were identical before and after every probe and mutant. `git diff --cached --check` is clean.
- Green: `python -m unittest test_role_adapters` -> Ran 23 OK. `ApplyAndClearTests.test_a_bootstrap5_adapter_is_rejected_where_the_page_has_no_bootstrap5_evidence`, `AtomicRejectionTests` and `RoleContractTableTests` -> Ran 15 OK. I did not run the focused gate; the report carries it.
- Mutants, served through `bridge_source` by scratchpad/4rv/mut4rv.py (a copy of the bridge with one replacement, patched into `RoleBridgeCase.open`). Killed:
  - M1 Apply evidence check removed -> 3 tests fail (`('design:roles-applied', None, None)` != rejected).
  - M2 one-variable evidence -> `test_evidence_needs_both_variables`, both subTests.
  - M3 no `releaseRoleQuiet` at Apply -> `1 != 0`.
  - M4 body tie ignored -> `{'Role': 'bootstrap5-body', ...}`.
  - M5 Apply read not suspended -> `test_evidence_comes_from_the_page_and_not_from_the_live_preview`.
  - M6 and M10 role count instead of block count -> `stylesheet-blocked` in the fallback test.
  - M7 `:root` block for a heading role -> `heading` and `mixed` template cases.
  - M8 raw mono family compare -> error in the mono test.
  - M9 two names swapped -> `test_one_element_per_remaining_class_is_named_by_its_class`.
  - M11 above.
  - M16 and M17 loosened heading Apply check -> `test_a_heading_role_must_name_one_level_or_one_display_class`.
  - M19 candidate filter removed -> the `Head` scenario of the ties test.
- Mutants that survived all 23 tests: M13, M14, M15 and M18. See Issues and item 7b.
- Characterization at BASE: scratchpad/4rv/base4rv.py serves `git show f2b438f:fontkit-bridge.js`. `test_bootstrap5_adapters_are_rejected_on_bootstrap4_and_write_nothing` passes. BASE rejects every non-plain adapter with `Unsupported adapter`, which is what the test asserts. The Bootstrap 4 plain test and the clear test fail at BASE (`KeyError: 'adapter'`, `design:rejected`), so those are true reds.
- D063: after applying the body template, the reply's `pageVersion`, its `currentPageVersion` and a following Detect's `currentPageVersion` are all 0. Suspend and release use only the `roleOwned` node, so bridge writes move only the internal epoch. The clear test and the second Apply in the no-ban test also send the stored version and are accepted.
- Hidden skips: `grep skip|REQUIRE_FIXTURES` in tests/support.py, tests/role_support.py and the new module finds no skip. The Bootstrap 4 and 5 fixtures and their vendored CSS are tracked files (`git ls-files`), and no new test uses a `node_modules` fixture. `test_r2_react` is outside this patch.

#### Checklist
1. Drift: PASS. Both sides of the byte contract come from `tests/role_contract.py`.
   - Template bytes: `test_every_template_case_emits_its_exact_bytes...` applies `table.TEMPLATE_CASES` per name and compares `roles`, `canonicalCss` and `cssHash` against the case.
   - `ADAPTERS`: the protocol tests check every group's adapter against `table.ADAPTERS`. `DetectedGroup.adapter` values are exactly the four.
   - Re-check: `rejected_adapter` asserts `('design:rejected', 'unsupported-value', 'Unsupported adapter')` in the Bootstrap 4, stale-adapter, heading-selector and evidence-from-the-app tests. M1 and M5 kill the re-check.
2. Mutants: reproduced M1 to M19 myself (list above). The frozen worktree stayed byte-identical.
3. Fake versus real: the bridge is the real file in real Chromium. The Studio side is the fake host `tests/fixtures/bridge/host-roles.html` and its `request()`. That leaves to R2.S3's real-Studio cases:
   - Studio's exact-field validation of `DetectedGroup.adapter`, including on incomplete replies.
   - Studio's own `serializeRoleSheet` giving the same bytes as the bridge's `canonicalCss` for the `:root` templates. Studio accepts a receipt only when they are equal.
   - Studio sending the suggested adapter back unchanged.
   - Studio's display of the `Unsupported adapter` rejection.
4. Hidden skips: none new. Every test in `test_role_adapters.py` and the two added protocol tests run on hosted CI (static, tracked fixtures; no install).
5. Tests: the oracles are independent. They are `TEMPLATE_CASES`, `FIXTURE_GROUPS` and `CASE_VARIABLES` literals, the `DETECTED_CSS` literal written from Addendum 17, the 128 KiB sheet built in the test, and `expected-styles.json`. Most Thens equal the assertions; see Minor 3. The one GREEN characterization is true (check above).
6. Code: within budget. `D063` rules kept (check above). `bootstrapHeadingSelectors`, `headingClaim` and `suggestBootstrapAdapters` each have one caller. They are named, small and carry real rules, so I do not count them against the task. The untested branches are Issue 1.
7. Judgment calls:
   - (a) The mixed case expects all three variables to change. This is what the contract says. Addendum 17 item 1 gives body both variables and mono `--bs-font-monospace`. `TEMPLATE_CASES['mixed']` holds a body role and a mono role, each with a family, and its css contains both `:root` blocks. The brief's "the others: neither" was loose wording. The implementer's reading follows the table the brief names as oracle. Not a gap.
   - (b) A group qualifies on its style alone, before the heading precedence. Not contradicted by the text. It is the literal reading of "the one group whose text style equals body's" and of the brief's "a group that qualifies twice takes heading, then mono, then body". It is still a gap the owner should rule on, because Addendum 17 item 2 does not say whether a group already taken by heading or mono counts toward the tie. Two readings:
     - A (implemented): the tie is counted on style alone.
     - B: the tie is counted after heading and mono have taken their groups.
     - Observable difference: the protocol page with both variables plus `<h2 style="font-size:1em;font-weight:400">Head</h2>` and `<p data-design-role="Intro">Role</p>`. Both groups equal body's style. Under A, `Head` is `bootstrap5-heading` and `Role` is `plain` (probe output: `('Role','Intro','plain')`). Under B, `Role` is `bootstrap5-body`.
     - The same happens with a mono-qualifying group plus an author-role group of the same style.
     - Mutant M18 (reading B) survives all 23 tests, so neither reading is pinned.

### Strengths
- Evidence is read from the app's own CSS in both paths. M5 shows the Apply-time suspension matters, and M3 shows the transition-ban release matters.
- The template tests drive the whole `TEMPLATE_CASES` table, plus the detected group as received against a literal written from the addendum.
- Incomplete replies carry `adapter`. A BASE-passing characterization is reported as such and does pass at BASE.
- The 128 KiB test computes the exact boundary including the `:root` block. It cannot pass if the check ignores that block (the report's mutant).

### Issues
#### Critical
(none)

#### Important
1. Three predicates of brief rule 3 are implemented in `headingClaim` (fontkit-bridge.js, patch lines 84-93) with no test, and their mutants survive. All 23 tests pass for each of these: M13 an element whose tag level and class level differ (`<h2 class="h4">`) takes the first level; M14 a `.display-N` element that also carries an `.hN` class still counts as display; M15 an element with several `.display-N` classes still counts as display. The brief states each rule ("an element whose tag level and class level differ is not a heading-level candidate", "every element carries the same `.display-N` class and no `.hN`"). Under M13, a group of `<h2 class="h4">` elements would be suggested `bootstrap5-heading` bound to `h2`, which is wrong on routine Bootstrap markup. Add one variant per rule (an id-less page with `<h2 class="h4">`, `<p class="display-2 h3">`, `<p class="display-1 display-2">`) asserting the group stays `plain` and is not bound by the heading step.

#### Minor
1. The tie semantics of item 7b are unpinned (M18 survives). After the owner rules, add one test with a heading or mono group and an author-role group of equal style.
2. Brief rule 3 does not say what a group of `<h1 class="display-1">` is. This is Bootstrap's documented display markup, and the implementation gives the level step precedence: the group is named `Heading 1` and tries `h1`. In my probe, with a stray `p.display-1` in the page it fell back to a dom-path as `plain`. No test covers a tag plus display class. Record the intended precedence once the owner decides.
3. Docstring Thens miss assertions:
   - The fixture test also asserts the body group's four selectors.
   - The template-case test also asserts the body case's outcomes (matched 3, checked 3).
   Add them to the Then or drop the assertions.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The behaviour, the byte contract and the Apply re-check are correct, and all of the new guards I mutated were killed except the three `headingClaim` predicates. Those survive the whole new test module (Issue 1), and a failing mutant for them is the unfinished piece. The owner decision on item 7b is separate and does not block.

## Scoped re-review: fix round 1

### Spec Compliance
- PASS: Important 1 closed. `HeadingClaimTests` has one test per rule-3 predicate (patch lines 530-560): tag level vs class level (`<h2 class="h4">`), display beside an hN class (`<p class="display-2 h3">` beside `span.h3`), two display classes on one element. Each asserts the exact group name, adapter and selectors. Each mutant dies (see Checks).
- PASS: Minor 1 for the heading half of the ruling. `test_a_group_equal_to_the_body_style_that_shares_it_with_a_heading_group_gets_no_body_suggestion` asserts `Head` is `bootstrap5-heading`, `Role` is `plain`, and no group is `bootstrap5-body`. That is the owner's "Keep it literal" outcome. Reading B (bodies counted after heading) is killed.
- PASS: Minor 2. `test_the_heading_level_wins_over_a_display_class_when_the_tag_fits` asserts two `h1.display-1` give `Heading 1`, `bootstrap5-heading`, `[h1]`. `test_the_display_class_is_tried_when_the_heading_tag_matches_a_non_member` asserts the display group is `Heading 1`, `bootstrap5-heading`, `[.display-1]`, and the plain h1 beside it is `Heading 1`, `plain`, bound only by `dom-path`. Both match the "Heading level" ruling exactly.
- PASS: Bridge change does only what the ruling says (fontkit-bridge.js `roleBindings`, heading step). Before: the candidates were `hN` and `.hN`, or `.display-N` only when there was no level. After: the level candidates are tried, then `.display-N` if the group states one. `choose` has no side effects on failure (it returns false before it sets `selectors` or `bindingComplete`), so the fall-through is safe. Naming is unchanged (`result.title` still prefers the level). The rest of the binding order is unchanged.
- PASS: No earlier test changed its expectation. The two patches differ only in the index lines, the hunk-count lines, the bridge heading step (lines 191-196 of the r1 patch), the new `HeadingClaimTests` block, and two docstring Thens. Every other line is byte-identical.
- PASS: Minor 3. Both docstrings now equal their assertions (checked against the test bodies). The fixture test states "bound to the four body ids, in order", which `assertEqual([...], BODY_SELECTORS)` checks. The template-case test states matched 3, checked 3, mismatched 0, no losses, Inter 18px, label sans-serif 16px, which is the `outcomes` and `font` assertions.
- PASS: Nothing else changed between the patches. Patch SHA-256 and the staged diff hash equal 4c39e12c...4ac1.

### Checks run
- Frozen worktree identity -> `git diff --cached | sha256sum` in C:/fks/t4 -> `4c39e12ca1a3...34ac1`, equal to the r1 patch. `git status` and SHA-256 of fontkit-bridge.js (a7e81ca1...9a5f) and tests/test_role_adapters.py (08f8be50...2d2c) were the same before and after all runs. No server was started.
- Green -> `python -m unittest test_role_adapters` in C:/fks/t4/tests (`FKS_REQUIRE_FIXTURES=1`) -> Ran 29 OK (23 plus the 6 new). Only chromium ran here (`ENGINES`).
- Mutants, served through `bridge_source` by scratchpad/4rr/mut4rr.py (the bridge is CRLF; the script normalises). Killed by the new tests:
  - M13 `levels.size >= 1` -> `test_a_tag_level_that_differs_from_its_class_level_is_not_a_heading` (`('Heading 2','bootstrap5-heading',[h2])` != `('Text','plain',[.h4])`).
  - M14 `display` ignores hN marks -> `test_a_display_class_beside_a_heading_class_is_not_a_display_heading`.
  - M15 `shown.length >= 1` -> `test_two_display_classes_on_one_element_are_not_a_display_heading`.
  - M18h bodies counted after heading -> the body-tie test.
  - Nofall (display fallback removed) -> `test_the_display_class_is_tried_when_the_heading_tag_matches_a_non_member` and the existing `test_without_author_ids_headings_bind_their_tag_and_class_and_are_heading_suggestions`.
  - Dispfirst (display tried before the level) -> `test_the_heading_level_wins_over_a_display_class_when_the_tag_fits`.
  - Titlefirst (display title before the level title) -> both display tests.
- RED reproduced -> Old mutant (the round-0 heading step restored) -> `test_the_display_class_is_tried_when_the_heading_tag_matches_a_non_member` fails with `('Heading 1','plain',[('.display-1','class',True)]) != ('Heading 1','bootstrap5-heading', ...)`. This is the report's RED text, and the branch-1 test passes under Old, so it is a guard only.
- Survivor -> M18m (the body tie counted after mono has taken its group) -> all 29 pass. See Minor 1.
- D063 -> the diff touches only the heading step in detection and the tests. No page-version code, reply field or Apply path is in the diff, so the round-0 check (version 0 after body template, Detect, clear and second Apply accepted) still holds. Not re-run.

### Strengths
- The display-heading ruling is pinned on both branches (tag fits, tag does not fit) with the owner's observable outcomes, and the plain neighbour in the second case is asserted too.
- The three predicate tests use an otherwise heading-free page, so a mutant cannot hide behind another group's binding.

### Issues
#### Critical
(none)

#### Important
(none)

#### Minor
1. The "Keep it literal" ruling names "heading or mono", but only the heading half is tested. M18m (the body tie counts groups after mono takes its group) survives all 29 tests. Add the mono variant: both variables plus `--bs-font-monospace`, a group whose style equals both body's and the mono family (or a mono-qualifying group) beside an author-role group of body's style, asserting neither gets `bootstrap5-body`. The code path is the same (`bodies` is counted on style alone), so this is a pin against a future change, not a present defect.
2. The template-case docstring Then omits `complete: True`, which the outcomes assertion checks. Add "complete" or drop it from the assertion.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** Every finding from the first review is closed. The three predicate tests and the display-heading tests each fail on their mutants, the RED is real and the bridge change does only what the ruling says. The remaining items are the mono half of the tie ruling and one omitted word in a docstring.

## Scoped re-review: fix round 2

### Spec Compliance
- PASS: r1 -> r2 differs in two lines only (`diff task-4-code-r1.patch task-4-code-r2.patch`): the blob hash line of tests/test_role_adapters.py, and the template-case docstring Then, which now reads "the receipt is complete, echoes the roles ..." (patch line 592). That closes the earlier Minor 2 (the test asserts `complete` is true; checked as the prior review did).
- PASS: fontkit-bridge.js is unchanged. `sha256sum C:/fks/t4/fontkit-bridge.js` = a7e81ca1fd057f391b41d019ab63d015d2491b7c9c87f56cd632196a7e189a5f, matching the report. The r2 patch SHA-256 is 28513bdb...a568 as stated.
- PASS: Minor 1 not done, and the reason holds. Mono matches on `familyNames` alone (fontkit-bridge.js:1838); body matches on the whole style (1839). A body-equal group has body's exact fontFamily string, so it is a mono candidate iff body's family is the mono family. Hence when body's family is not mono, bodies and monos are disjoint, and when it is mono, every body-equal group is a mono candidate. A second body-equal group therefore means monos.length >= 2 and nobody takes mono. "Two body-equal groups where one takes mono" cannot be built, so the mono half of "Keep it literal" cannot be tested as the earlier review described.
- PASS: the bridge still matches the ruling. Verified on the page (below): two body-equal groups on a monospace body give neither group a body suggestion. A heading that also equals the body style takes heading, and the body-equal author-role group stays plain. A lone group equal to both is mono and nothing is body, which the existing scenario 4 pins (test_role_adapters.py:248).

### Checks run
- Does M18m (bodies exclude the group mono takes) differ observably from the real bridge? -> copied the frozen tree to scratch (`4rr2/wt`), added `tests/test_4rr2.py`, mutated line 1839 to `&& !(monos.length === 1 && monos[0] === group)`, ran test_4rr2 and test_role_adapters (32 tests) -> all OK, and the three probe pages gave the same results as the real bridge. Equivalent. Reasoning: a group excluded from bodies this way is the unique mono, so no other body-equal group exists (it would be a second mono), so bodies would be {that group} and body is never reached for it anyway.
- Page: monospace body, `<p>Auto</p><p data-design-role="Intro">Role</p>` -> Auto plain, Role plain (the two-monos tie; ruling met).
- Page: monospace body, `<h2 style="font-size:1em;font-weight:400">Head</h2>` plus the Role paragraph -> Head bootstrap5-heading, Role plain (ruling met).
- Page: monospace body, `<p>Auto</p><code style="font-size:14px">Other</code>` -> real bridge gives Auto bootstrap5-body, Other plain. A stronger mutant B (bodies exclude every mono-qualifying group, `!monos.includes(group)`) turns Auto plain, and still passes all 29 tests. B is not M18m; it is a different, untested behaviour. See Minor 1.
- The frozen worktree stayed byte-identical: `sha256sum -c` on fontkit-bridge.js and tests/test_role_adapters.py -> OK; `git status --short` unchanged (M fontkit-bridge.js, A tests/test_role_adapters.py, M test_role_protocol.py, M test_role_stylesheet.py). No server was started. Scratch files are under scratchpad/4rr2.

### Strengths
- The implementer tried the draft test, saw it fail on the real bridge, and removed it instead of weakening it to a green that pins nothing. The equivalence argument holds when checked against the code and by direct runs.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Mutant B above survives. When body's family is the mono family, a lone body-equal group beside another mono-family group of a different style is `bootstrap5-body` (monos tie, bodies = 1). No test pins this, and no test is required for the ruling; a mutant that stops a mono-qualifying group from falling through to body would pass. Optional test: monospace body, `<p>Auto</p>` plus a 14px `<code>`, assert Auto is bootstrap5-body and Other is plain. This does not block the task.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The r2 delta is the one docstring line and the bridge hash is unchanged. The M18m equivalence claim is correct (I could not find a page where it and the real bridge differ), and the bridge's behaviour matches the "Keep it literal" ruling on the pages I built. One Minor (a different mutant that survives) is optional.
