### Spec Compliance
- PASS: Item 1, display class first. `fontkit-bridge.js` heading step (patch 45) now tries `.${display}` before `levels`; comment rewritten; name and `bootstrap5-heading` unchanged. The changed test (renamed `test_the_display_class_wins_over_the_heading_level_when_the_class_fits`, test_role_adapters.py ~296) now asserts `[('.display-1','class',True)]`; the report names it as an intended edit of an existing test. The test at 302 is renamed and re-docstringed as the first leg. The fallback test (characterization) and the Apply test (`DisplayHeadingApplyTests`) exist as briefed.
- PASS: Item 2, names from every shared class. `result.classes = shared` (full list) set right after `group.sharedClasses = shared.slice(0, 16)`, read by `suggestBootstrapAdapters`. No wire field added; `sharedClasses` stays at 16 on both sides.
- PASS: Item 3, batch rule. `rolesHaveRootBlock(roles)` is a named function beside `roleCssBlocks` (bridge 303). `rooted` is computed once per Detect; only when true does `run()` do one `documentElement.getBoundingClientRect()` after `suspendRoleSheet()`, set `reading = max(8, 2 * elapsed)` and reset `slice`. `restore()` stays in `finally`, before the yield; the 2,000 ms check is unchanged. Test sits in `BaselineDetectTests` with its constants inside the test; the module header is untouched.
- PASS: Item 4, both comment slips corrected (test_role_adapters.py 23 -> "suggested name"; bridge "after the evidence read").
- PASS: Known limit (ALT3) and the accepted survivor (always-on) are named in the report. Draft commit subject is 64 characters.
- PASS: Scope. The patch touches only the three owned files; the worktree index equals the patch byte for byte. 113 added / 14 removed lines, under the 220 budget. `LINK_BOOTSTRAP5` and `BOOTSTRAP5_CSS` sit at the top of test_role_adapters.py, a file the brief owns.
- CANNOT VERIFY FROM DIFF: Firefox and WebKit runs of the new tests (the loops are over `ENGINES`; I ran Chromium only).

### Checks run
Drift checklist:
1. Drift -> read `tests/role_contract.py` 18 (`SHARED_CLASSES = 16`), `fontkit-studio.html` 3818 (`sharedClasses.length > 16`), bridge `slice(0, 16)` -> same limit on both sides, the table and the bridge; the patch adds no wire field (`classes` lives only in the bridge-internal `facts` Map and is not serialized). The enum and null rules are untouched. The new button test hard-codes `range(16)` instead of `table.SHARED_CLASSES` (Minor 1).
2. Mutants (reproduced by me through `RoleBridgeCase.open(bridge_source=...)` using a patched `open` in my own scratch runner `scratchpad/w2b2-review-mut.py`; nothing in the worktree was written; before/after `sha256sum -c` of bridge and tests reported no change). Control with the unmutated bridge: 9 adapter tests OK; Detect test OK at 426 ms.
   - display-first reverted -> `test_the_display_class_wins_over_...` FAIL (`[('h1',...)] != [('.display-1',...)]`) and the Apply test FAIL (mismatched 2 vs 0). Killed.
   - level fallback removed (`display ? choose([.display]) : levels.length && choose(levels)`) -> `test_the_heading_level_is_tried_when_the_display_class_matches_a_non_member` FAIL (plain / dom-path vs bootstrap5-heading / h1). Killed.
   - lookup back on `group.sharedClasses` -> button test FAIL (`Text` != `Button`). Killed. Also `result.classes = shared.slice(0, 16)` -> same FAIL. Killed.
   - batch rule off (`if (false && rooted)`) -> Detect test FAIL `time-budget`, 346 scanned, 2,034 ms. Killed.
   - restore skipped after a long batch -> Detect test FAIL (sampled pair set differs; 18 frames, reply complete, so the frame sampler is what kills it). Killed.
   - restore deferred past the yield (`setTimeout(restore, 0)`, my extra mutant) -> Detect test FAIL (sampled pair set differs). Killed. Restore-before-yield is therefore pinned.
   - Survivors: batch clock not reset after the forced read (`slice = performance.now()` removed) -> Detect test OK at 657 ms (Minor 2); predicate loosened to `ROLE_VARIABLES[role.adapter]` with no `fontFamily` test -> Detect test OK (Minor 2); always-on -> the report's accepted survivor.
3. Fake versus real -> read the three new test bodies -> all run the real bridge in a real page; no fake peer in this patch. PASS.
4. Hidden skips -> `grep skip` over tests/test_role_adapters.py and tests/role_support.py; read the new tests -> no skip decorator or `skipTest`; the vendored `bootstrap.min.css` and `fixtures/large-page` are tracked (`git ls-files`). None of the new tests would be skipped on hosted CI. They do run for every engine `FKS_ENGINES` selects, so hosted Firefox and WebKit run the timing test as well (CANNOT VERIFY above).
5. Tests (design Section 5) -> see Strengths and Issues. Mutant recorded per new test: yes, five of six in the report's table (the Apply test shares the display-first mutant; the fallback, button, Detect tests each have their own). Oracles: the markup, literals (`Button`, 41px, 700, `Georgia, serif`), the plan's 2,000 ms, and the fixture CSS (`.g00 { font-family: serif }`); none comes from bridge output. Observable outcomes: computed styles and reply fields. Then equals assertions except two extras (Minor 4). Limits from role_contract: not imported (Minor 1, Minor 3).
6. Code -> read the bridge diff and `roleCssBlocks` -> `rolesHaveRootBlock(roles)` exists at 303 with the exact name and a `roles` argument, as R2.W2B1 needs. New constants of `BaselineDetectTests` are inside the test (`css`, `add_style`). Validation (`rolesHaveRootBlock`), state (`run`) and rendering are separate. No third copy; one second copy (Minor 5).
7. Implementer's concern: is anything on the plain-preview 5,000-parent test's path? -> read `run()`. For a plain role `rooted` is false (`ROLE_VARIABLES['plain']` is undefined), `reading` stays 8, `slice` is taken at the same point as at BASE, and the only added work is one boolean test per batch plus one `some()` per Detect. Nothing else changed on that path. I ran that existing test three times on the patched bridge: 725 / 744 / 692 ms, complete, 5,000 scanned, 43-46 frames. The one earlier red in a loaded run is the marginal-test noise the brief already names, not this patch. Nothing was loosened.
8. Gates -> `node --check fontkit-bridge.js` ok; `python -m ruff check` on both test files: All checks passed; `git diff --cached --check` ok; `git diff --cached` equals the patch file.

### Strengths
- Every guard in the patch except the clock reset and the family half of the predicate has a mutant I reproduced as killed; the Detect test kills both restore mutants, so the frame sampler genuinely sees a dropped preview (it samples `.g00` and `#corpus`, and `#corpus` takes its family only through the variable).
- The Apply test's oracle is the requested values on real Bootstrap 5 CSS, and it is red at BASE and under the display-first mutant.
- The fallback test pins the second leg of display-first that the brief review (I2) found uncovered.
- The batch rule changes nothing for plain or absent previews (no forced read, 8 ms), so the existing plain Detect test is not on the changed path.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_role_adapters.py:344 hard-codes `range(16)` although the module imports `role_contract as table` and `table.SHARED_CLASSES == 16` exists (role_contract.py:18). If the limit rose, the test would stop proving the 17th-class case and still pass. Use `range(table.SHARED_CLASSES)`.
2. Two surviving mutants not named in the report: the clock reset after the forced read (657 ms still passes; it is a margin choice, not behaviour any test can pin) and the `'fontFamily' in role.properties` half of `rolesHaveRootBlock` (a family-less body role only changes timing). The report lists only "always on" as accepted. Record both as accepted survivors, or the second as an untested branch.
3. tests/test_role_stylesheet.py (new Detect test): `5000` and `2000` are literals, not `table.ELEMENTS`/`table.TIME_BUDGET_MS`. The sibling test does the same and the brief forbids touching the module header where an import would go, so this is accepted; mention it.
4. Docstring Then clauses omit two assertions: the Apply test asserts `adapter == 'bootstrap5-heading'`, and the Detect test asserts the receipt type and that the owned sheet is enabled at the end.
5. `rolesHaveRootBlock` repeats the condition `ROLE_VARIABLES[role.adapter] && 'fontFamily' in role.properties` from `roleCssBlocks` (two copies, the report discloses it). Acceptable now; R2.W2B1 must call the function and not add a third.
6. `reading = max(8, 2 * restyle)` has no upper cap: a very slow restyle (say 400 ms) gives an 800 ms batch with no frame in between. That is the specified D073 rule and the 2,000 ms check still ends the job, so it is not a defect, only a stated edge.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** All four brief items are implemented as written, every new guard I tried (display-first, level fallback, full class list, batch rule, restore before yield) is killed by a real-bridge test with an independent oracle, and the plain-preview test is not on the changed path. Remaining notes are Minor.

## Phase 2 review

Reviewed: `task-w2b2-p2-delta.patch` (one file, `tests/test_role_adapters.py`, +122/-7 gross) against the frozen worktree `a scratch worktree` (phase 1 + phase 2). I did not change the worktree: `fontkit-bridge.js` SHA-256 `9b2f9592...8170c9` and `tests/test_role_adapters.py` SHA-256 `55a96f18...270242` were the same before and after, and `git status` was identical. Mutants ran from a scratch runner that feeds a mutated bridge string through `RoleSheetCase.open(bridge_source=...)` (scratch: `scratchpad/w2b2p2-review/w2b2p2-review-run.py`, `PYTHONDONTWRITEBYTECODE=1`, Chromium only). No browser or server was left running.

### Spec Compliance
- PASS: T1 `test_apply_evidence_needs_both_variables` (delta 164-172): each variable alone, body role refused `unsupported-value` / `Unsupported adapter`, `owned == []`.
- PASS WITH NOTE: T2. The brief says the accept side of `test_a_heading_role_must_name_one_level_or_one_display_class` "gains" the cases; the implementer added two new tests (delta 174-198) and left that test (now line 630) untouched. All asked behaviour is there (`.display-1`, `.h3`, `h3` accepted and applied; bare `<h3>` 30px; `h3.h3` 28px; one `fontSize` loss). Only the form differs, and the report does not record it. Minor 1.
- PASS: T3 (name `Text` added to the test at 132, plus the new mixed display test with the `display-1` element first in document order).
- PASS: T4 (non-plain groups are exactly `one` mono and `Get started` body, keyed by sample text).
- PASS: T5 (Bootstrap 4, ids stripped, expected bindings read from the fixture markup).
- PASS: T6 (variables on `body` only; both candidates `Text`/plain; body role refused; no owned node).
- PASS: T7 (five scenarios as literals; no lone-author-role-paragraph test, per Addendum 23; the docstring says the plan fixes no precedence or name priority).
- PASS: T9 (the test at 132 applies `self.received(two, fontSize=36)`; the docstring says the binding assertion, not the render check, proves the exclusion).
- PASS: T14 (tooltip added with ADD_HTML, no group has its text, `Inter` while applied, its own family after Clear).
- PASS: `range(table.SHARED_CLASSES)` at line 414 (closes phase 1 Minor 1).
- PASS: no bridge, fixture or other-test change in the delta.

### Checks run (the checklist)
1. Drift -> read the delta's file list and grep `table.` in the module -> tests only (no `fontkit-bridge.js`, `role_contract.py`, `role_support.py` or fixture touched). The one limit the new tests depend on, the 16-class cap, comes from `table.SHARED_CLASSES` (`role_contract.py:18`, used at test line 414). The other numbers in the new tests (41px, 30px, 36px, 43px) are request values and oracles, not limits.
2. Mutants (against the phase 1 bridge; each string replace asserted to match exactly once; the new test run alone; `none` control green each time):
   - T1 `Boolean(found.body && found.sans)` -> `||`: `test_apply_evidence_needs_both_variables` FAILS, both CSS subtests (`roles-applied` != `design:rejected`).
   - T2 `.display-N` accept line deleted: the display/level test FAILS (selector `.display-1`); the bare-tag test passes, as expected.
   - T2 `&& selectors.length === 2` added in `bootstrapHeadingSelectors`: both new tests FAIL (the `.h3` case; the `h3` case).
   - T3 level from `claims[0]` only: the test at 132 FAILS (`Heading 6` != `Text`); the new display test passes.
   - T3 display from `claims[0]` only: `test_a_group_that_mixes_a_display_class_with_none_is_named_text` FAILS (`Display 1` != `Text`); the test at 132 passes. Each half has its own killer.
   - T4 `&& monos[0] === group` dropped: the two-code test FAILS (the non-plain groups are all mono).
   - T5 pair (claims pushed unconditionally and the heading step `if (true)`): FAILS (`h1`+`.h1` != `.h1`). T5 claims half alone: passes. T5 step half alone: passes. T5 realistic single-point defect, `evidence` replaced by `true` in the `roleBindings(...)` call (bridge 2000): FAILS. Each half alone is an equivalent mutant: `result.title` is read only in `suggestBootstrapAdapters`, which runs only when `evidence` is true (2001), and the step's `levels` and `display` come from `claims`, which is empty without evidence. So the pair is the only observable edit, and the one realistic single edit that reaches it (passing `true`) is killed. No test is missing.
   - T6 variables read from `document.body`: FAILS (`Inherits` -> `('Body','bootstrap5-body')`, `Pressed` -> `Button`).
   - T7: mono before heading FAILS (scenario 1); one-signature rule relaxed to `>= 1` FAILS (scenario 2, `Intro` -> `bootstrap5-body`); `if (group.authorRole) continue;` removed FAILS (scenario 2, `Text` != `Intro`); `BOOTSTRAP_NAMES` reversed FAILS (scenario 5, `Button` != `Lead`); adapter name before title FAILS (scenario 3, `Body` != `Heading 2`); class name before adapter name FAILS (scenario 4, `Button` != `Body`). Six of six killed, each by its own scenario.
   - T14 `ROLE_VARIABLES = {}`: the tooltip test FAILS (the system font stack != `Inter`).
   - T9: no mutant by design; the binding assertion remains in the test and the docstring states it.
   - Implementer's concerns: T5 pair (answered above: equivalent halves, nothing missing); T9 (accepted as briefed); T7 pins literals the plan does not fix (accepted: the docstring says so, and no pin collides with Addendum 23, since scenario 2 only shows an author-role group stays plain and scenario 3 uses `data-design-id`).
3. Fake versus real -> read every new test: all go through `self.start` / `self.one` -> `RoleSheetCase.open` -> the real `fontkit-bridge.js` in a real page; no stub, mock or recorded reply. The mutant runs also show that it is the bridge under test that fails.
4. Hidden skips -> grep `skip|Skip|expectedFailure` in the module: none. The new tests loop `ENGINES` (default Chromium; `FKS_ENGINES` selects more) and none is gated on engine, CI flag or font. No new test would be skipped on hosted CI.
5. Tests -> see "Item 5 detail" below.
6. Code -> no new helper, constant or import in the delta (the tests use `adapted`, `received`, `rejected_adapter`, `owned`, `one`, `sample`, `ADD_STYLE`, `ADD_HTML`, `BOTH_VARIABLES`); gross 122 added / 7 removed, under the 320 budget.
- Unmutated module with warnings as errors -> `python -W error -m unittest test_role_adapters` in the worktree tests dir -> `Ran 40 tests in 16.424s`, `OK`, no stray output.
- `git diff --cached --check` -> clean.

Item 5 detail:
- Oracles: T1/T6 literals (`Unsupported adapter`, `Text`, `Inter`); T2 request values (30px) and Bootstrap's own 28px for `h3.h3`; T3 `Text`; T4 sample texts from the fixture; T5 expected bindings read from `fixtures/bootstrap4-static/index.html` lines 13-28 (`h1.h1` to `p.display-4`; `h5.h5` and `h5.card-title` share no class, hence two dom paths for Heading 5); T7 literals; T14 `Inter`. No expected value comes from the bridge's own reply.
- Outcomes are observable: reply types and details, computed font family and size, group fields, owned-node text.
- Given/When/Then: every new docstring's Then matches its assertions. T2's `['h3']` test asserts the reply type, `owned[0]` starts `h3 {`, the bare `<h3>` computes 30px (`h3:not(.h3)`), `h3.h3` computes 28px, and the outcomes tuple `[(2, 1, ['fontSize'])]` (matched 2, mismatched 1, exactly one `fontSize` loss).

### Strengths
- Every mutant in the brief's T-list, plus six T7 variants, fails the test written for it; the two T3 halves are killed by different tests, so neither is a duplicate.
- T5's expected bindings come from the fixture markup, and the Heading 5 case (two unstable dom paths) is asserted rather than skipped.
- T7 states in its docstring that the order is a pinned decision, so a later reader will not mistake it for a plan requirement.
- T14 proves the variable path in a rendered font (the tooltip takes its family only from `--bs-font-sans-serif`), both applied and after Clear.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_role_adapters.py:630-642 and delta 174-198: the brief asked the existing accept side to "gain" `['.display-1']`, `['.h3']` and `['h3']`; the implementer wrote two new tests instead and the report does not list this as a departure. Harmless (arguably cleaner, since the bare-tag case needs ADD_HTML and a receipt check), but it should be recorded.
2. Delta 52-67 (T5): the Heading 5 branch asserts `len == 2` and `{('dom-path', False)}` but not that neither value is an `hN` tag, while the docstring says "none binds an hN tag". The T5 pair mutant would change the count and reasons, so this is not a hole, only a Then slightly wider than its assertion.
3. Delta 140-155 (T14): `assertNotEqual(own, 'Inter')` would also pass if the tooltip family were empty; the Clear round-trip back to `own` is what matters and it is asserted. Cosmetic.
4. The report says "about +125 / -5"; the delta is +122 / -7. Cosmetic.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Tests only, real bridge throughout, no skips. Each T-list mutant I reproduced (T1, T2 both, T3 both, T4, T5 pair and its realistic single-edit form, T6, six T7 variants, T14) fails its own new test, and the unmutated module is green with warnings as errors. T5's two halves are equivalent mutants (no test is missing), and only Minor notes remain.
