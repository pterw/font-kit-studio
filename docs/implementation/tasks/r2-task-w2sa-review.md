### Spec Compliance
- PASS: Requirement 1 -- the test types 27 (not a native size), asserts len(request['roles']) == 16 / 2 and the plain adapters (tests/test_r2_integration.py:790-791), waits for the receipt AND Studio's status "Preview applied to N roles; 0 checked elements did not show it." (793-794), asserts every outcome (mismatched, losses) == (0, []) (796), matched sums 20 / 2 (797), and every element each role's selectors match computes 27px (798-801). The brief's literals (16, 20, 2, 2) are used; the "Adapter: " row count and the existing request assertions are kept.
- PASS: Requirement 2 -- the comment at fontkit-studio.html:3920 names `roleCssBlocks` (the bridge's function at fontkit-bridge.js:289).
- PASS: Requirement 3 -- `const names = ROLE_ADAPTER_VARIABLES[role.adapter]; const root = names && Object.hasOwn(role.properties, "fontFamily") ? ... : ""` (fontkit-studio.html:3925-3927); no other serializer change; the diff touches only the two owned files.
- PASS: Line budget -- 27 gross lines against about 90. No deviation claimed, none found.
- PASS: Commit text -- subject and draft body in the report name the Studio comment and the reshaping, and say the output is byte-identical.
- PASS: The brief review's fixes are folded in (27px, status wait, literal oracle, `Object.hasOwn`, the right mutant tests).

### Checks run
- Drift (checklist 1) -> read the patch against tests/role_contract.py (TEMPLATE_CASES) -> no wire field, limit, enum or null rule is touched on either side. 27 is inside the fontSize range of 4-400. The serializer's inputs and outputs are unchanged (see check 6). PASS, nothing to drift.
- Mutant A, bridge skips role-4 (checklist 2; reproduced in a scratch copy of the frozen worktree, `w2sa-review-repo`, SHA-256 a7e81ca1...9a5 before and after) -> `w2sa-review-mutate.py ... w2sa-review-mA.json` -> new test ERROR, TimeoutError at wait_status (test_r2_integration.py:794), in the bootstrap4 subtest. The BASE test file run against the same mutant: Ran 1, OK, so the mutant is invisible to BASE (RED confirmed). The implementer's finding is right: Studio refuses the receipt whose CSS does not match its serializer, so this mutant dies at the status wait, not at the 27px assertion.
- Mutant D, judging whether the 27px assertion is decorative (checklist 2) -> two bridge edits in the scratch copy: the installed `<style>` gets `media='not all'` (the rules are present and the rule count verifies, but nothing renders) AND `roleMismatches` is forced to `[]` (a bridge that lies in its receipt: matched, mismatched 0, status "0 did not show it") -> FAIL at test_r2_integration.py:801 (the `set(sizes) == {'27px'}` assertion) in both subtests, "Items in the first set but not the second". So the 27px assertion is not decorative: it is the only line that kills a bridge whose receipt and CSS agree with Studio but whose page does not render. The same sheet-disabled edit alone (mutant B) dies at the status wait (Timeout), as expected.
- Mutant E, Studio's conditional loses the `Object.hasOwn(..., "fontFamily")` half (reproduced; studio SHA 9d80fa42...cfe36 before and after) -> StudioAdapterTests + BS5 integration: the BS5 integration test PASSES (its only adapter row sets a family; a gap, not scope), and 2 tests ERROR with a wait timeout: `test_a_groups_adapter_changed_between_two_detects_is_what_the_next_request_carries` (test_studio_roles.py:2365) and `test_a_ready_snapshot_with_each_template_cases_literal_bytes_is_accepted_and_shown` (case 'body-without-family', :2380). Matches the report.
- Mutant F, Studio's `:root` block drops its final LF (reproduced) -> `test_a_bootstrap_5_body_row_applies_with_its_variables_and_clear_restores_the_page` FAIL at test_r2_integration.py:766 (the startswith assertion). The report's six StudioAdapterTests errors for this mutant were not re-run by me; the BS5 integration kill was.
- Fake versus real (checklist 3) -> read `start` (test_r2_integration.py:244) and `fixture_page` (727): `self.open(engine, init=CAPTURE, target=url4, peer=html4)` loads the real fontkit-studio.html and the bootstrap4-static fixture HTML with `<script src="/fontkit-bridge.js">`. Mutant A edits the real bridge file and the test reacts, which proves the real bridge is in the loop. PASS.
- Hidden skips (checklist 4) -> grep for skip / skipTest / skipUnless in test_r2_integration.py, test_studio_roles.py and support.py -> none. `per_engine` loops over ENGINES (default chromium; FKS_ENGINES selects more) and a missing browser fails at launch, not skips. The fixture is tracked in the repo. No new test would be skipped in hosted CI. The test is not new, only changed.
- Byte-identical serializer (checklist 6) -> scratch `w2sa-review-cmp.js` extracts `serializeRoleSheet` from `git show 73b3ba2:fontkit-studio.html` and from the staged `git show :fontkit-studio.html`, and compares them over 263 role sets: every adapter x all 64 property subsets as single roles, the five TEMPLATE_CASES roles dumped from tests/role_contract.py, and two large mixed sets -> 0 differences. The mixed case prints the expected `:root` and plain blocks.
- Unvalidated adapters -> `serializeRoleSheet` has one caller (fontkit-studio.html:3941) after `roles.every(validRoleInput)`, which requires `ROLE_ADAPTERS.includes(adapter)`. BASE and HEAD differ only for prototype-name adapters such as "toString", which never reach the function. No finding.
- Sibling copies of the corrected pointer -> grep `serializeRoleCss` -> only historical task reports and plan text under docs/ (history, not claims about HEAD); no live source or test copy.
- `python -m ruff check tests/test_r2_integration.py` -> All checks passed. `git diff --cached --check` -> exit 0. The frozen worktree status is only the two staged files, and fontkit-studio.html still has SHA 9d80fa42...cfe36.
- The full focused gate was not re-run; the report carries it (Ran 150 tests, OK). The single changed test ran green in my copy (Ran 1, OK, 4.5 s).

### Strengths
- The oracle is independent: the typed 27px (no fixture element computes it; 24 is Bootstrap 4's own h4) and the literals 16 / 20 / 2 / 2 measured by the brief review, not read back from the receipt.
- The three-layer assertion (receipt outcomes, Studio's status, rendered computed size) is each killable on its own: A dies at the status wait, D only at the 27px line.
- `set(sizes) == {'27px'}` also fails on an empty match (an empty set is not `{'27px'}`), so a selector that matches nothing cannot pass.
- The serializer reshaping is output-neutral on 263 sets, and the Studio mutant E is killed by named tests.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
- tests/test_r2_integration.py:777-780 -- the Then in the docstring omits two things the test asserts: the request role count (16 / 2) and the matched total (20 / 2). The docs rule says the Then equals the assertions. Add "16 (or 2) roles" and "matching 20 (or 2) elements" to the docstring.
- tests/test_r2_integration.py:799-800 -- the continuation line of the `frame.evaluate(...)` call is aligned past the open paren by hand and the call is one long line; cosmetic only (ruff passes).
- Gap, not scope: mutant E (the `Object.hasOwn(..., "fontFamily")` half) survives the real Bootstrap 5 integration test, because its single adapter row sets a family. The StudioAdapterTests do kill it, so the conditional is covered. No action for this task.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Both requirements and the byte-identical reshaping are met inside the line budget and the owned files. I reproduced mutants A, D, E and F: the BASE test misses A, the new test kills it, and the 27px rendered assertion is the sole killer of a bridge whose receipt agrees but whose page does not render. The only findings are a docstring that omits two asserted facts and a cosmetic line.
