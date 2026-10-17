### Spec Compliance
- PASS: `page` accepted, placement rules, per-reply one body / one mono group, selector-check exception, `validRoleInput` body exactness, `validAcceptedRoles` one body / one mono role, receipt line: all present and equal to the table and to the bridge side (fontkit-studio.html:3781, 3834-3847, 3932-3933, 3956, 4213, 4225-4226, 4270, 4277).
- PASS: receipt line literal in the test is character for character the brief's (and W2PI's brief line 39): `; applies page-wide through Bootstrap's body variables, and inherited text is not measured` (tests/test_studio_roles.py new receipt test). Other roles' lines unchanged (asserted in the same test).
- PASS: pasted self-test rows: 74 defects (53 + 21), 5 valid_page rows; checked by running the test with a print in a scratch copy: `NDEF 74 5 21`, no duplicate (kind, name), the test is green, each defect row gives exactly one violation.
- PASS: Req 5 (Body row shows its binding and Adapter line, Apply enabled) is carried by the new first test; no code needed; reported as such.
- PASS: not touched, as the brief says: `buildRoleRequest`, knownRoles builder, `acceptResetRoleState` (stays empty-only; reaches `validAcceptedRoles`).
- PASS: no hidden skip added (no `skipTest`, bare `continue` or `return` in the diff).
- PASS: budget: +224/-25 gross in two files, about 249, under 300.
- FAIL (see Important 1, 2): two existing/new behaviours have no failing test.
- CANNOT VERIFY FROM DIFF: the real-Studio, real-bridge proof is R2.W2PI's (next slice). Every test here drives Studio with the harness's fake bridge replies; none of them proves the bridge sends what Studio now accepts. I did read `a scratch worktree/fontkit-bridge.js` 1870-1890 (read-only): the body group binds `[{value:'body', stable:true, reason:'page'}]` with `bindingComplete = true`, the mono fallback binds code, kbd, pre, samp (page, stable) with `bindingComplete = true`, and `sole()` yields at most one body and one mono group. That agrees with Studio's rules.

### Checks run
- Drift against `tests/role_contract.py` 208-216, 244-268 and task-w2p-brief.md reqs 1, 3, 4, 5 -> read both -> Studio equals the table row by row: `page` only on a body or mono group (3847 `return !pages.length`); body exactly one stable `body`/page, complete (3843); mono page bindings exactly the four in order, complete (3844-3845); exact lowercase (3782, 3843, 3932); no duplicates (Set at 3837 and 3931); one body and one mono group (4270) and role (3956); `body` valid in a selector check (4277). Bridge side agrees (canonical `['body']`; Studio never sends duplicates, only the bridge de-duplicates a raw request).
- Every validation site -> `grep validRoleSelector|validRoleInput|validAcceptedRoles|validDetectedGroup|validDetectedReply` in the frozen worktree -> all callers covered: `validRoleSelector` (3835 binding, 3933 role selector wrapped in an arrow so `.every`'s index is not read as `bodyOk`, 4277 check); `validRoleInput` only at 3955; `validAcceptedRoles` at 3999 (ready), 4400 (receipt), 4458 (reset-all state); `validDetectedGroup` at 4261. No other `.every(validRoleSelector)` remains.
- Mutants, on scratch copies of the tree (`w2ps-review-c1..c4` in the scratchpad; chromium; classes StudioAdapterTests, StudioContractTableTests, StudioRoleApplyTests, StudioRoleStateTests, StudioRoleBoundaryTests, 65 tests); the Studio file restored byte-exact after each (SHA-256 `e3e59cbe...6805`, asserted in the driver); the frozen worktree's Studio file and tests re-hashed afterwards: identical to before:
  - `page` reason refused again -> 10 errors: page-bound body + mono, selector check, receipt line, each_adapter, adapter_changed, apply_sends, unsupported_rejection, body_case_receipt, and the `binding reason` and `stable flag` limit rows -> KILLED.
  - receipt line reverted to the old clause -> receipt test fails at checked=0 and checked=3 -> KILLED. Wording changed by a comma -> same two fail -> KILLED. Page-wide line only when checked=0 -> checked=3 fails -> KILLED.
  - selector-check exception removed -> selector check test, adapter_changed, limit rows fail -> KILLED.
  - `body` exactness removed (`selectors.length === 1 && pages[0] === "body"`) -> only `body group with body and a class` fails -> KILLED (by one row).
  - `selectors.length === 1` removed alone -> `body group with body and a class` fails -> KILLED.
  - `pages[0] === "body"` removed alone -> 65 tests OK -> SURVIVES (Important 2).
  - page binding need not be complete (body group) -> `incomplete page binding` fails -> KILLED. Same for a mono group (`group.bindingComplete` removed from the mono branch) -> OK -> SURVIVES (Minor 1).
  - mono order -> `mono page bindings in another order` fails; mono length -> `mono group with the four and a class` fails -> KILLED.
  - page binding allowed on other groups -> `page on a plain group`, `page on a heading group` fail -> KILLED.
  - one body / one mono group rule removed -> `two body groups`, `two mono groups` fail -> KILLED.
  - one body / one mono role rule removed -> only the ready-snapshot `two body roles`, `two mono roles` fail; the hostile-receipt rows of the same names do NOT fail (Minor 2).
  - body role may select anything valid -> snapshot and hostile-receipt `body role on a class` fail -> KILLED. `bodyOk` tied to the adapter instead -> same two fail -> KILLED.
  - `bodyOk` always true on bindings -> `body in a plain group`, `body in a mono group` and ~27 existing hostile rows fail -> KILLED.
  - `validRoleInput` compared case-insensitively (`['BODY']` accepted) -> 65 tests OK -> SURVIVES (Important 2).
  - page binding exempt from the stable rule -> 65 tests OK -> SURVIVES (Minor 1).
  - "Safe complete bindings unavailable." render line deleted -> 65 tests OK -> SURVIVES; Adapter line and that line swapped -> OK -> SURVIVES (Important 1).
  - case-insensitive `validRoleSelector` bodyOk alone -> OK (survives, as the report says); case-insensitive `pages[0]` alone -> OK (survives); both together -> `BODY` row fails -> KILLED. Judged below.
- Implementer's concern 1 (case-insensitive survives alone) -> read 3781-3847 and 4270-4280 -> on the binding path both guards are on the same value: bodyOk's exact `===` (3782) and `pages[0] === "body"` (3843) each refuse `BODY` alone. The second is the one that carries meaning (it also refuses `code` as a body page binding); the first is defence in depth. On the selector-check path `BODY` is refused by the `remaining` key map (a known role cannot hold `BODY`), so bodyOk's strictness is unobservable there too. So the mutant is behaviourally equivalent today, not a test gap by itself; the `BODY` row only proves the pair. Nothing to change on this count, but see Important 2: the guard that matters (`pages[0]`) is itself unkilled.
- Implementer's concern 2 (hostile Detect table also passes at BASE) -> the rows are refused at BASE for another reason (unknown reason / root ban). Given the mutants they still prove the new rules, with the gaps listed: 11 of 14 rows are killed by a named mutant (page on plain, page on heading, body with a class, BODY (pair), body in plain, body in mono, incomplete, mono order, mono four+class, two body groups, two mono groups). Not killed by any mutant alone: `body group on .btn`, `body group on the mono bindings`, `mono three of the four` (each is also refused by a neighbouring guard, so the row is correct but redundant), and the missing rows named in Important 2. Rows are fine as evidence; they are not RED at BASE, and the report says so.
- Existing tests moved -> read the diff hunks for body_row, each_adapter, apply_sends, adapter_changed, ready_with_accepted_roles, hostile_receipts, every_reason -> each is forced by Addendum 23 (a body group is exactly body/page, a body role is exactly `['body']`); the report names the rule for each. One weakening beyond the rule: each_adapter (Important 1).
- ruff -> `python -m ruff check --no-cache tests/test_studio_roles.py` on the scratch copy -> All checks passed.
- Third copy of a rule -> read the diff -> the list `["bootstrap5-body", "bootstrap5-mono"]` appears twice (4270 and 3956), one for groups and one for roles; the string `"body"` is compared at 3782, 3843, 3932, 4213. Two copies, not three; Minor 3.

### Strengths
- Validation is split cleanly: binding syntax (`validRoleSelector`), placement (end of `validDetectedGroup`), per-reply and per-set counts in the two sites that already own cross-item rules, and the receipt line is a render-only change computed from accepted state.
- The `.every(selector => validRoleSelector(selector))` wrapper avoids the index-as-`bodyOk` trap.
- Hostile Detect rows check the rendered page (the fence is the only row, no row says Hostile), not a mock.
- The pasted self-test rows and the `every_reason` split follow W2PT's handoff exactly; 74/5/21 verified.

### Issues
#### Critical
None.

#### Important
1. Coverage of an existing behaviour was removed beyond what the rule forced. At BASE `test_each_adapter_renders...` was the only test that asserted the rendered line "Safe complete bindings unavailable." and its order after the Adapter line (BASE test line 2306). The rule forces only the Body row to become complete; the change dropped the assertion everywhere. Mutants "delete the line (fontkit-studio.html:4057)" and "swap it with the Adapter line (4056)" both pass all 65 tests. Fix: keep one adapter row (heading or mono) with `binding_complete=False` and a non-page binding in that test, and expect `Adapter: ...` then `Safe complete bindings unavailable.` (tests/test_studio_roles.py, the each_adapter test, around the `groups =` list and `expected =` list). The docstring now only mentions the line in the negative.
2. The core placement rule has conjuncts that no test pins. (a) `pages[0] === "body"` (fontkit-studio.html:3843): a body group whose single binding is `{value:'code' (or '.btn'), stable:true, reason:'page'}` is accepted with the guard removed; the hostile "body group bound to `.btn`" row uses reason `class` and is refused because there is no page binding at all. Add a row: body group bound `[{...PAGE_BODY[0], 'value': '.btn'}]` (and the same shape in the self-test is not needed, the table row `body group on a class binding` is the class form). (b) Exact lowercase on the role path (3932): `['BODY']` as a body role's selector in a ready snapshot or receipt is accepted with `.toLowerCase()` added; the brief says "Exact lowercase `body` only (`BODY` is refused)" and the new Studio hostile rows for roles have `['.btn']` and `['body','body']` only. Add `['BODY']` to the snapshot table and `hostile_receipts` (the table's own `body role on BODY` row tests the checker, not Studio).

#### Minor
1. Two stated rules are untested in Studio: a mono page group with `bindingComplete: false` (3845; mutant survives; only the body form has a row) and a page binding with `stable: false` (3837 plus the page reason; mutant "page exempt from the stable rule" survives; the brief review's optional Minor 7). One row each in the hostile Detect table.
2. The hostile-receipt rows `two body roles` and `two mono roles` (tests/test_studio_roles.py, `hostile_receipts` shapes) cannot fail for the count rule: the receipt is refused first by `data.roles.length !== sent.length` (fontkit-studio.html:4407 area), because the request sent one role. With the count rule deleted they stay green; the ready-snapshot rows do kill it. The brief asked for these rows in both tables, so this is a limit of the brief, not an error; they are near-duplicates and a later reader should not rely on them. The report's phrase "exercised through the role-rule mutants" does not say they failed; they did not.
3. fontkit-studio.html:3866-3867: the new `ROLE_PAGE_MONO` constant was inserted between the comment "The variables a Bootstrap 5 body or mono role sets beside its own rule (Addendum 17)..." and `ROLE_ADAPTER_VARIABLES`, so the comment now sits over the wrong constant and `ROLE_ADAPTER_VARIABLES` lost its comment. Move the constant above the comment. Also the two-adapter literal list at 3956 and 4270 could share one constant.
4. No hostile selector-check row for `BODY` or `body` on a role whose selectors are other (the `remaining` map refuses it today); not required by the brief.

### Plan-mandated (for the owner)
- [Minor] The two receipt rows `two body roles` and `two mono roles` are unreachable as receipts against the one-role request the hostile table builds -- brief requires: "Requirement 4's refusals, in the existing hostile receipt and ready-snapshot tables: two body roles, two mono roles, a body role on [".btn"], a body role on ["body","body"]". The snapshot rows carry the rule; the owner may drop the receipt pair or accept it as documentation.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The Studio rules match the table and the bridge exactly and the main behaviours (page-bound Body accepted, selector check, receipt line, role placement) are killed by real mutants. But the change removed the only test of the "Safe complete bindings unavailable." line and its order, and `pages[0] === "body"` and exact lowercase on the role path survive deletion, so two stated rules are not pinned; each fix is one or two rows. The real-Studio, real-bridge proof is R2.W2PI's.

## Re-review (follow-up 1)

### Spec Compliance
- PASS: Important 1 fixed. The each_adapter test now makes the heading row `binding_complete=False` and expects `Adapter: Bootstrap 5 heading rule`, then `Safe complete bindings unavailable.`, then the shared classes (tests/test_studio_roles.py each_adapter hunk). The Body row stays complete and page-bound.
- PASS: Important 2 fixed. Detect row `body group on a page binding that is not body` (value `code`, reason page) and `BODY` role rows in both the ready-snapshot table (`body role on BODY`) and `hostile_receipts` (`body role on BODY`); the self-test also gained a `body role on BODY` defect row, and the defect count in the docstring is 74.
- PASS: Minor 1 folded (two Detect rows), Minor 3 folded (constant moved). Minor 2 and 4 left with reasons; both reasons hold (Minor 2 is plan-mandated, Minor 4 not required).
- PASS: Studio's rules did not change. I diffed the HTML hunks of `task-w2ps-code.patch` against `task-w2ps-code-r1.patch`: the only differences are the position of `ROLE_PAGE_MONO` and its neighbouring comment (a comment now sits over `ROLE_ADAPTER_VARIABLES` again). Validation code, receipt line and counts are byte-for-byte the same, so the earlier verdict that Studio equals `tests/role_contract.py` and W2P stands. `tests/role_contract.py` is unchanged in the delta.

### Checks run
- Frozen worktree untouched -> sha256 before and after: fontkit-studio.html `56dd0108...ba7`, tests/test_studio_roles.py `d823ef4b...4e9`, git status identical -> unchanged. All mutants ran on a scratch copy (`w2ps-rereview` in the scratchpad), the Studio file restored and re-hashed after each ("restored ok"), `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests FKS_ENGINES=chromium`.
- Unmutated scratch baseline, the five touched tests (hostile page binding, ready snapshot placement, every hostile receipt, each_adapter, checker self-test) -> Ran 5, OK.
- Mutant: delete the "Safe complete bindings unavailable." render line (fontkit-studio.html:4057) -> each_adapter FAIL (list differs, the line missing) -> KILLED.
- Mutant: swap that line with the Adapter line (4056-4057) -> each_adapter FAIL (order differs) -> KILLED.
- Mutant: remove `pages[0] === "body"` (3843) -> ERROR on subtest `body group on a page binding that is not body` only -> KILLED.
- Mutant: `role.selectors[0].toLowerCase() === "body"` on the role path (3932) -> ERROR on ready-snapshot subtest `body role on BODY` and hostile-receipt subtest `body role on BODY`, nothing else -> KILLED in both tables.
- Mutant: remove `group.bindingComplete` from the mono branch -> ERROR on subtest `mono group on the four page bindings, not complete` only -> KILLED (earlier Minor 1).
- Mutant: page binding exempt from the stable rule -> ERROR on subtest `body page binding that is not stable` only -> KILLED (earlier Minor 1).
- ERROR instead of FAIL -> read the failing output and the pattern -> see below.

### The ERROR-instead-of-FAIL note
Honest, not hiding. Each ERROR header carries the subtest label (`shape='body group on a page binding that is not body'`, `case='body role on BODY'`, `shape='body role on BODY'`), and only the mutated rows error; the neighbouring rows in the same loop still pass, so the failing rule is identifiable. The trace is a `Page.wait_for_function` TimeoutError: when Studio wrongly accepts the hostile reply it settles the pending request, the following fence reply is then ignored, and the wait for "Fence" times out. An ERROR exits non-zero and fails the gate exactly like a FAIL. The cost is a slower red (8 s, 4 s per row) and a message that does not state "hostile row rendered" directly. It is the same wait-for-fence pattern the file already uses (lines 599, 666, 2532, 2876, 2964 and 6 at BASE), so it is the file's convention, not a new weakness. Minor only, and not worth a change.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- Left as is, by design: the two-adapter list `["bootstrap5-body", "bootstrap5-mono"]` still appears in two sites (groups at 4270, roles at 3956); the reasons given (one for groups, one for roles) hold. The hostile-receipt rows `two body roles` and `two mono roles` still cannot fail for the count rule (earlier Plan-mandated item); unchanged.

### Plan-mandated (for the owner)
- Unchanged from the first review (the two receipt rows).

### Assessment
**Task quality:** Approved
**Reasoning:** Both Important findings are closed by tests that fail under the named mutants, each naming its row; the fix changed no validation rule, only a comment position in the HTML, so the match with the table and W2P stands.
