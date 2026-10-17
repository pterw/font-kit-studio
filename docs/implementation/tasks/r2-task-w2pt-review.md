### Spec Compliance
- PASS: `BINDING_REASONS` and `STABLE_REASONS` gain `page` (tests/role_contract.py:39-40 in the delta; frozen file line 21-22 of the patch hunk).
- PASS: the checker refuses each item of requirement 2 with exactly one violation, page rule first, `elif` chain so a plain group bound body/page is one violation; body exactness is one `need` (role_contract.py:245-258 at HEAD of the frozen tree; roles_part 208-214; group count 265-266). Verified by my own run of all 19 handed-over defect rows (each len == 1) and 4 valid page rows (each []).
- PASS: placement rules sit in `roles_part()` (receipts and role state), not a request kind that does not exist (brief review I4). Selector checks untouched.
- PASS: template cases `body`, `body-without-family`, `mixed` bind `['body']`; `mono` and `heading` unchanged. CSS hand-written from Addendum 17 item 1; I re-hashed it with an independent FNV-1a32 snippet: bb5252fb, 0f1b0795, 4d6ad066 (and `''` -> 811c9dc5). Matches the table.
- PASS: header cites Addendum 23.
- PASS: owned files only (one file, `git diff --numstat` 36/12 = 48 gross lines, budget about 120). ruff clean, `git diff --check` clean, no non-ASCII in the file.
- PASS: Handoff correct and ready to paste (see Checks run): defect count 53 + 19 = 72 verified, rows paste unchanged, `every_reason` split verified.
- FAIL (report, not code): the report's "No unclassified failure" is not true for the slice; three W2P-owned reds in `test_role_adapters.EvidenceTests` are missing (Issues, Important 1).

### Checks run
- Frozen worktree untouched -> sha256 of tests/role_contract.py and tests/test_studio_roles.py before and after all my work (6737d3ed...506c unchanged), `git status` unchanged -> byte-identical. All scripts ran on a copy (`scratchpad/w2pt-review-copy`, `w2pt-review-base`), `PYTHONDONTWRITEBYTECODE=1`.
- Patch/DEP identity -> sha256sum of task-w2pt-code.patch and task-w2t-code.patch -> df9527f0...d23f and 2f1697fb...5cd, equal to the report and the dispatch.
- Drift against Addendum 23 items 1, 3, 4 and the W2P/W2PS briefs -> read all three -> body exactly `[{'value':'body','stable':True,'reason':'page'}]` (PAGE_BODY); mono `code,kbd,pre,samp` in order (PAGE_MONO); one body and one mono role (roles_part) and group (Detect) each; `body` banned in every other role and group binding (else-branch, mono-with-pages exactness, body exactness, page-first branch); selector checks exempt (I built a detected reply with a selectorCheck on `body`: `[]`); `['BODY']` on a body role -> one violation (exactness); `['body','body']` on a body role -> one violation. The latter is a receipt/state shape (the bridge's canonicalizeRoles dedupes, fontkit-bridge.js:251 `new Set`), so the table is right to refuse it; W2P's "de-duplicates and passes" applies to the request only. W2PS req 4 does not say this; see Minor 2.
- Mutants (item 2) -> `w2pt-review-mutate.py` on the copy, all six reproduced; SHA-256 6737d3ed...506c before and after: `page` not stable -> 12 rows fail; role count (<=9) -> `two body roles`, `two mono roles`; group count (<=9) -> `two body groups`, `two mono groups`; `['body']` rule removed -> `body role on other selectors`, `body role with a second selector`; body ban on other roles removed -> `plain role on body`, `mono role on body`; page-first precedence removed -> `page binding on a plain group` (2 violations). Every mutant fails at least one row; a flag-everything checker fails the 4 valid page rows and the base valid rows.
- Handoff pasted for real -> script `w2pt-review-paste.py` extracts the three python blocks from the report, indents them into a copy of tests/test_studio_roles.py (rows after `role = self.role_input()`, `+ page_defects`, valid loop, docstring 53 -> 72, `every_reason` split) -> `StudioContractTableTests.test_the_checker_passes_...` and the template-case test: Ran 2, OK. Defect count by regex: 48 literal + 5 controls + 19 = 72.
- `every_reason` split -> built the two-group reply with `self.reply(...)`: violations `[]`, scannedElements 2; the `binding reason` (`invented`) and `stable flag` (`class`, False) past rows each still give exactly 1 violation. Not run against Studio (needs W2PS).
- Classification of the failures -> read w2pt-base.log (Ran 15, OK), w2pt-change.log (8 failures, 5 errors) and w2pt-focused.log (3 failures); each of the 16 reds is on the table's stated reason and the owners are right (bridge test -> W2P, Studio test -> W2PS). The three focused reds: `test_role_protocol` 361 fails with "a body group binds exactly body/page, not [author-id bindings]" (BASE bridge; W2P), and `every_reason` `binding reason`/`stable flag` fail at test_studio_roles.py:2665 with "page binding on a 'plain' group" (W2PS replacement). Table-internal template check (2459) green (I ran it).
- Unlisted readers of the table -> `grep` of TEMPLATE_CASES/case_roles/violations over tests/*.py, then class attribution: `test_role_adapters.EvidenceTests` calls `case_roles('body')` at lines 486, 490, 500, 501, 514 and was in neither command. Ran it on the change copy: Ran 5, FAILED (failures=2, errors=1): `test_detect_with_a_live_bootstrap_preview_returns_the_groups_of_a_detect_without_it` and `test_no_transition_ban_survives_an_apply_over_a_live_preview` (`design:rejected != design:roles-applied`), `test_evidence_comes_from_the_page_and_not_from_the_live_preview` (KeyError 'canonicalCss'). Ran it on the PATCH_DEP-only copy: Ran 5, OK. So these three are new, owned by W2P. `SuggestionTests` (`case_roles('mono')`, unchanged case) and the other table readers (test_role_protocol RoleContractTableTests: ran in the focused gate; test_r2_react: only EMPTY_HASH/fnv1a32) are not affected.
- Hidden skips (item 4) -> grep of the delta for skip/xfail: none; no tests added to the owned file.
- Fake versus real (item 3) -> n/a for the table: it has no fake/real pair; its oracle is Addendum 23's text and literals.
- Code (item 6) -> read the delta: PAGE_BODY and PAGE_MONO are defined once and used by the checker only; the one-body/one-mono rule exists once for roles and once for groups (different data). Within budget (48 of about 120).

### Strengths
- The page rule chain is one `need` per group per rule family, so every Handoff defect row yields exactly one violation, and the harness proves it for all 19 rows plus the six mutants.
- The Handoff is exact: the three blocks paste into the real self-test unchanged, give 72 defects, and pass.
- Template CSS and digests are hand-written and independently re-hashed; the report's mutant SHA-256s are honest and reproducible.

### Issues
#### Critical
None.

#### Important
1. Report claims "No unclassified failure" but omits three new W2P-owned failures: `test_role_adapters.EvidenceTests` (lines 486-514 call `case_roles('body')`; `test_detect_with_a_live_bootstrap_preview_returns_the_groups_of_a_detect_without_it`, `test_no_transition_ban_survives_an_apply_over_a_live_preview`, `test_evidence_comes_from_the_page_and_not_from_the_live_preview`). They are green at PATCH_DEP and red with the patch (my run). The brief's command listed only `ApplyTests` and `StudioAdapterTests` (the brief review's I2 had named lines 486-514), so the code is not at fault, but the report's classification of "every new failure" is incomplete. Fix: add them to the Bridge list (owner R2.W2P: the BASE bridge refuses a body role on `['body']`), and state that the slice's red set is the 3 + 13 + these 3 reds, not a complete census of the suite (full suite not run).

#### Minor
1. The Handoff has no valid row for "selector checks are exempt" (a detected reply whose selectorCheck is on `body`, matchCount 0, no signatures). It is a rule in the brief and the table accepts it today (I checked), but a mutant that bans `body` in `selectorChecks` would pass the pasted rows. Add one valid `detected` row, or accept the gap and say so.
2. `['body','body']` and `['BODY']` have no row. The table refuses both on a body role (one violation each, via the exactness `need`). W2PS req 4 does not say that Studio refuses a duplicated `body` in a receipt; the table does, so a W2PS test that sends it must expect a refusal. One sentence in the Handoff would remove the ambiguity.
3. `('bootstrap5-body', 'bootstrap5-mono')` appears as a tuple literal three times (role_contract.py:208, 247, 265 at HEAD of the frozen tree). Not a third copy of one rule, but a one-line constant would make a later adapter change one edit.
4. The `violations()` docstring (line 152-157) still lists what the checker covers without the page, body/mono placement and `body` rules.
5. On the implementer's concern (item 5): a body group with the right values but `stable: False` gives two violations ("a body group binds exactly body/page, not [...]" and "binding 'page' stable: False"; I ran it). That is two independent rules both true, and the brief fixes the exactness as one `need`; collapsing them would need the exactness test to ignore `stable`, which departs from "exactly `[{...,'stable': True,...}]`". It does not clash with W2PS's hostile rows: its five listed rows (page on plain, body on `.btn`, body plus another, `body` in a plain group, mono in another order) are one violation each (rows 1, 3, 5, 10 and 7 of the Handoff). Judgement: acceptable as recorded. The Handoff should tell W2PS, in one line, not to use a wrong-flag page binding in an assert-one row; today only the report's "Known" line says so.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The table change itself is correct, within budget, matches Addendum 23 and both consumer briefs, survives all six mutants, and its Handoff pastes and passes as written. The one Important is the report: it declares no unclassified failures while three W2P-owned `EvidenceTests` reds exist; it needs an amendment, not a code change.

## Re-review (follow-up 1)

Scope: the Important, Minors 1-5, and the lines the fix changed (patch `task-w2pt-code-r1.patch`, sha256 ad79281c...3ec7, equal to the dispatch; the frozen worktree `tests/role_contract.py` is 382605b2...5d25, the sha the report names, and `git status` there is unchanged by me).

### Spec Compliance
- PASS: Important 1 is fixed in the report. Its "Classification" section lists 19 reds (11 bridge, 8 Studio) and the three `EvidenceTests` are now in the Bridge list; it says plainly that the census covers six classes and not the suite.
- PASS: Minor 1 (selector-check exemption row), Minor 2 (`['BODY']` and `['body','body']` rows plus the sentence on request versus receipt), Minor 3 (`PAGE_ADAPTERS`, role_contract.py:45, used at 210, 249, 267), Minor 4 (docstring, 155-158) and Minor 5 (last Handoff bullet: no wrong-flag page binding in an assert-one row).
- PASS: the table's refusal of `['body','body']` on a role in a receipt or state agrees with Addendum 23 item 4 ("selectors are exactly `["body"]`"), with task-w2p-brief.md:73-74 (de-duplication applies to the REQUEST at the bridge) and with task-w2ps-brief.md:49-51 ("canonical receipts and role state carry exactly `["body"]`, as R2.W2PT's table requires ... Only the bridge de-duplicates, a raw request"). No drift.

### Checks run
- Census (Important) -> `git checkout-index` of the frozen worktree's index into a scratch copy (`w2pt-rereview-staged`, PATCH_DEP only, role_contract.py fb96c0ac...) and a copy with the worktree file over it (`w2pt-rereview-full`, 382605b2...); `gate.sh focused` on `test_role_adapters.SuggestionTests ApplyTests EvidenceTests`, `test_studio_roles.StudioAdapterTests StudioContractTableTests`, `test_role_protocol.RoleContractTableTests`, `PYTHONDONTWRITEBYTECODE=1`, both run once, in parallel -> staged: Ran 50, OK, exit 0; full: Ran 50, FAILED (failures=13, errors=6), 19 reds. My list of the 19 equals the report's list one for one (ApplyTests 1+2+3+1 = 7, EvidenceTests 3, RoleContractTableTests 1 = 11 bridge; StudioAdapterTests 3+1+1+1 = 6, StudioContractTableTests rows `binding reason` and `stable flag` = 2; 8 Studio). Owners are right. Not run: the full suite.
- Class set complete? -> grep of tests/ and scripts/ for `role_contract`, `TEMPLATE_CASES`, `case_roles`, `BINDING_REASONS`, `STABLE_REASONS`, `.violations(`, and for importers of the three modules -> table readers are only test_role_adapters (case_roles: Suggestion/Apply/Evidence; line 334 loop and 423-427 `CSS_BYTES`, both in ApplyTests), test_studio_roles (`CASES` and `TEMPLATE_CASES` at 2267-2459 and `violations` 2567-2793, classes StudioAdapterTests and StudioContractTableTests only), test_role_protocol (RoleContractTableTests only) and test_r2_react (`EMPTY_HASH`, `fnv1a32` only). test_r2_integration imports only helpers from test_studio_roles (no table value). No other reader.
- Handoff additions pasted -> `w2pt-rereview-harness.py` (my review harness plus the report's `body_check`, the valid row and the two defect rows, verbatim) on a copy -> 30 rows, 0 failed: the new valid row gives `[]`, `body role on BODY` and `body role with body twice` give exactly one violation each.
- Mutants (reproduced with `w2pt-rereview-mutate.py`, source sha 382605b2...5d25 before and after) -> `PAGE_ADAPTERS` body only: 3 rows fail (valid body and mono groups, two mono groups, two mono roles); body banned in selector checks: `valid a selector check on body` fails; exactness case-folded: `body role on BODY` fails; exactness de-duplicating: `body role with body twice` fails; `page` not stable: 13 rows fail; body ban on other roles removed: 2 rows; page-first removed: 1 row; role count <=9: 2 rows; group count <=9: 2 rows. Every mutant is caught by a named row; the two new rows are what catch the case-fold and de-dup mutants and the selector-check ban.
- Hygiene -> `ruff check` on the full copy: All checks passed; `git diff --check` clean (only the CRLF warning that was there already); no non-ASCII in the file; `git diff --numstat` 40/14 on one file.
- Scratch trees `w2pt-rereview-staged`, `-full`, `-mut` deleted; logs and scripts left in the scratchpad.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. task-w2ps-brief.md:50 and :53 cite `role_contract.py` 212 and 265-266. At the frozen tree the rules sit at 210-216 (role count, exactness, ban) and 267-268 (group count), because the first round's lines moved by the `PAGE_ADAPTERS` edit. The cited rule text is still right; only the line numbers drifted. Re-cite by rule name when W2PS is dispatched.
2. role_contract.py:157, the second line of the docstring's new text is 206 characters; the file has other lines over 140 and ruff passes, so this is polish only (wrap it).

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The 19-red census is complete and reproduced independently (staged OK, full 13+6, same list as the report), the five Minors are closed with rows that nine mutants confirm, and the `['body','body']` handling agrees with Addendum 23 item 4 and both consumer briefs. Only two Minors remain (stale line cites in the W2PS brief, one long docstring line).
