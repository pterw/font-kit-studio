# R2.W2PT code report (MODE code)

Patch: `task-w2pt-code.patch` (delta on PATCH_DEP, one file: `tests/role_contract.py`, +36/-12 gross). PATCH_DEP
`task-w2t-code.patch` sha256 `2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd` (checked, applied with
`git apply --index`). Patch sha256 `df9527f0b2415e3134ab27fdb4d888d1395604ee364019cd35a82739a828d23f`; `git apply --check -R` passes;
`git diff --check` clean; `ruff check tests/role_contract.py` passes.

## Requirements
1. `BINDING_REASONS` and `STABLE_REASONS` gain `page` (done). New constants `PAGE_BODY` and `PAGE_MONO` (the four values in order).
2. Checker, in the group part: chain `page binding on a group that is neither body nor mono` -> `elif body: bindings == PAGE_BODY`
   (one need) -> `elif mono with any page binding: bindings == PAGE_MONO` -> `else: no binding value 'body'`; then `page binding needs
   bindingComplete`; after the groups, at most one body and one mono group per reply. In `roles_part()` (receipts, role state): at most
   one body and one mono role; a body role selects exactly `['body']`; any other role never lists `body`. Selector checks untouched.
   Known: a body group with the right values but `stable: False` gives 2 violations (exactness + existing stable rule); no row uses it.
3. Template cases `body`, `body-without-family`, `mixed` bind `['body']`; CSS written by hand from Addendum 17 item 1, hashed with
   `fnv1a32`, re-hashed by an independent snippet (identical): body `bb5252fb`, body-without-family `0f1b0795`, mixed `4d6ad066`.
   `mono` and `heading` unchanged.
4. Header cites Addendum 23.
Oracle: Addendum 23 items 1, 3, 4 text and literals; no side output.

## Harness and mutants (scratch: `w2pt-harness.py`, `w2pt-mutate.py`; 27 rows: 4 valid page, 19 defects, every_reason, 3 base valid)
Unmutated: 27/27 pass. Source SHA-256 before and after every mutant run: `6737d3ed5e16cf55688b6afc0a3b104947d008a907c959151a9de1797237506c`
(restored in finally; identical).
- `page` dropped from STABLE_REASONS: 12 rows fail (valid page groups, every_reason, defects gain a second violation).
- role count rule removed (<=9): `two body roles`, `two mono roles` fail.
- group count rule removed: `two body groups`, `two mono groups` fail.
- body-only `['body']` rule removed: `body role on other selectors`, `body role with a second selector` fail.
- body ban on other roles removed: `plain role on body`, `mono role on body` fail.
- page-first precedence removed (ban no longer an else): `page binding on a plain group` fails (2 violations).

## Focused run (PYTHONDONTWRITEBYTECODE=1)
`gate.sh focused test_role_protocol.RoleContractTableTests test_studio_roles.StudioContractTableTests test_support`:
Ran 53, FAILED (failures=3), `GATE focused EXIT 1`. The template check (test_studio_roles 2459) is green. The 3 reds:
- `test_role_protocol.RoleContractTableTests.test_a_bootstrap5_detect_posts_a_reply_the_table_allows_with_a_group_that_is_not_plain`:
  real BASE bridge replies a body group bound by `author-id` selectors; the table now demands `body`/`page`. Owner R2.W2P.
- `test_studio_roles...test_detected_reply_limits_render_at_the_limit_and_are_refused_one_past` rows `binding reason` and `stable flag`:
  `every_reason` puts `page` on a plain group (review C2). Owner R2.W2PS (replacement below).

`gate.sh focused test_role_adapters.ApplyTests test_studio_roles.StudioAdapterTests`: baseline (PATCH_DEP) Ran 15, OK. With the patch
Ran 15, failures=8, errors=5, all expected:
- Bridge, `design:rejected != design:roles-applied` on `body` (owner R2.W2P): ApplyTests inline_root_variable, clear_restores (case body,
  mixed), every_template_case (body, body-without-family, mixed), rule_count_is_the_block_count.
- Studio, snapshot timeouts, ready snapshot not accepted (R2.W2PS): StudioAdapterTests ready_snapshot_with_each_template_cases_literal_bytes
  (body, body-without-family, mixed).
- Studio timeouts (R2.W2PS): unsupported_adapter_rejection_keeps_the_template_preview (8 s), apply_sends_each_selected_groups_adapter (30 s).
- Studio assertion on old `.btn/.nav-link` selectors (R2.W2PS): the_body_case_receipt_shows_its_template_bytes.
No unclassified failure. Full suite not run (override).

## Handoff (for R2.W2PS, in `StudioContractTableTests`, tests/test_studio_roles.py)
Commit body sentence: "The contract table states the page binding, the exact body and mono bindings, one body and one mono role or
group, and `body` only as a body role's selector; the body template cases select `body`."

1. Self-test docstring: "each of 53 defects" -> "each of 72 defects" (53 + 19 below); the docstring may add "a page binding, a body or mono
   placement and a body selector" to the rule list.
2. Paste after `role = self.role_input()` / `bound = ...` inside the self-test (`group`, `outcome` already in scope; harness-verified):
```python
page_body = group('scan-body', 'Page text', None, adapter='bootstrap5-body', selectors=table.PAGE_BODY)
page_mono = group('scan-mono', 'Code', None, adapter='bootstrap5-mono', selectors=table.PAGE_MONO)
class_mono = group('scan-code', 'Code', None, adapter='bootstrap5-mono', selectors=[bound])
body_role = {**self.role_input('role-2', 'Page text', fontSize=24), 'selectors': ['body'], 'adapter': 'bootstrap5-body'}
mono_role = {**self.role_input('role-3', 'Code', fontSize=14), 'selectors': ['code'], 'adapter': 'bootstrap5-mono'}
page_apply = {**apply, 'roles': [body_role, mono_role]}
valid_page = [('detected', 'body and mono groups on the page bindings', self.reply(request, [page_body, page_mono])),
              ('detected', 'mono group on its own class binding', self.reply(request, [class_mono])),
              ('roles-applied', 'one body role on body and one mono role', self.receipt(page_apply)),
              ('role-state', 'one body role on body and one mono role', self.snapshot_state(page_apply['roles']))]
dom_body = {'value': 'body', 'stable': False, 'reason': 'dom-path'}
page_defects = [
    ('detected', 'page binding on a plain group', {'groups': [group(selectors=table.PAGE_BODY)]}),
    ('detected', 'page binding on a heading group', {'groups': [group(adapter='bootstrap5-heading', selectors=table.PAGE_MONO[:1])]}),
    ('detected', 'body group on a class binding', {'groups': [{**page_body, 'selectors': [bound]}]}),
    ('detected', 'body group on the mono bindings', {'groups': [{**page_body, 'selectors': table.PAGE_MONO}]}),
    ('detected', 'body group with body and a class binding', {'groups': [{**page_body, 'selectors': table.PAGE_BODY + [bound]}]}),
    ('detected', 'mono page group with three bindings', {'groups': [{**page_mono, 'selectors': table.PAGE_MONO[:3]}]}),
    ('detected', 'mono page group out of order', {'groups': [{**page_mono, 'selectors': table.PAGE_MONO[::-1]}]}),
    ('detected', 'mono page group with a class binding', {'groups': [{**page_mono, 'selectors': table.PAGE_MONO[:2] + [bound]}]}),
    ('detected', 'page binding that is not complete', {'groups': [{**page_body, 'bindingComplete': False}]}),
    ('detected', 'body as a plain binding', {'groups': [group(selectors=[dom_body])]}),
    ('detected', 'body as a mono class binding', {'groups': [{**class_mono, 'selectors': [dom_body]}]}),
    ('detected', 'two body groups', {'groups': [page_body, {**page_body, 'id': 'scan-body-2'}]}),
    ('detected', 'two mono groups', {'groups': [page_mono, {**page_mono, 'id': 'scan-mono-2'}]}),
    ('roles-applied', 'two body roles', {'roles': [body_role, {**body_role, 'id': 'role-9'}]}),
    ('roles-applied', 'body role on other selectors', {'roles': [{**body_role, 'selectors': ['.btn']}]}),
    ('role-state', 'two mono roles', {'roles': [mono_role, {**mono_role, 'id': 'role-9'}]}),
    ('role-state', 'body role with a second selector', {'roles': [{**body_role, 'selectors': ['body', '.btn']}]}),
    ('role-state', 'plain role on body', {'roles': [{**role, 'selectors': ['body']}]}),
    ('role-state', 'mono role on body', {'roles': [{**mono_role, 'selectors': ['body']}]}),
]
```
3. Add the 19 rows to the end of the `defects` list expression (after the `controls` comprehension: `defects = [...] + [...] + page_defects`),
   and add the valid loop beside the existing one:
```python
        for kind, name, message in valid_page:
            with self.subTest(valid=name, kind=kind):
                self.assertEqual(table.violations(kind, message), [])
```
   Each defect row yields exactly one violation (the loop `len(table.violations(kind, {**valid[kind], **change})) == 1` is unchanged).
   Violation texts: plain/heading page binding `group 'scan-a': page binding on a 'plain' group` (or `'bootstrap5-heading'`); body group
   wrong bindings `group 'scan-body': a body group binds exactly body/page, not [...]`; mono `a mono page group binds exactly code, kbd,
   pre, samp, not [...]`; incomplete `a page binding must be complete`; `body binding outside a body group`; `more than one
   bootstrap5-body group` / `...-mono group` / `... role`; `a bootstrap5-body role selects exactly body`; `body only as the one selector
   of a bootstrap5-body role`.
4. `every_reason` split (Detected-reply limits test): replace its definition with a two-group reply, and `binding reason` / `stable flag`
   keep using it:
```python
        every_plain = group(selectors=[{'value': f'.r{i}', 'stable': reason in table.STABLE_REASONS, 'reason': reason}
                                       for i, reason in enumerate(r for r in table.BINDING_REASONS if r != 'page')])
        every_reason = ([every_plain, group('scan-body', 'Page text', None, adapter='bootstrap5-body', selectors=table.PAGE_BODY)], {})
```
   (the two-group reply has scannedElements 2 from `reply()`; the row asserts `#roleRows > li` count equals 2 via `len(groups)`.) Until
   Studio accepts `page`, this row waits for "Detected" and times out (expected RED, R2.W2PS).

# Follow-up 1

Patch: `task-w2pt-code-r1.patch` (the WHOLE delta on PATCH_DEP, working tree vs index; replaces `task-w2pt-code.patch`, which is untouched).
sha256 `ad79281c86ad8015ef5c260fbe7224ba3bbf7b1905dba4d6ce88eeab65503ec7`; `git apply --check -R` passes; ruff and `git diff --check` clean;
one file, `tests/role_contract.py`, +40/-14 gross. Layout kept (`MM tests/role_contract.py`). PATCH_DEP sha unchanged.

## Code changes (Minor 3, Minor 4)
- New constant `PAGE_ADAPTERS = ('bootstrap5-body', 'bootstrap5-mono')`, used at the three former tuple literals (role count, page-binding
  chain, group count).
- `violations()` docstring now lists the page bindings, one body and one mono role or group, `body` only as a body role's selector, and
  that selector checks are exempt.
Mutant evidence (scratch `w2pt-r1-harness.py` 30 rows, `w2pt-r1-mutate.py`; source SHA-256 before and after every mutant
`382605b24c58e05e2ebb9853142d26e84e929d448bbaf91bafb2ab95d75b5d25`, identical; unmutated 30/30 pass):
- `PAGE_ADAPTERS` narrowed to body only: `valid body and mono groups on the page bindings`, `two mono groups`, `two mono roles` fail.
- `body` banned in selector checks: `valid a selector check on body` fails.
- exactness case-folded (`['BODY']` passes): `body role on BODY`, `body role with a second selector`, `body role with body twice` fail.
- exactness de-duplicating (`['body','body']` passes): `body role with body twice` fails.
- The six earlier mutants re-run: each still fails its rows (page not stable 13 rows; role count 2; group count 2; body-only 4; ban on other
  roles 2; page-first 1).
Docstring is prose; no mutant applies.

## Classification (Important 1): full list
Focused run on both trees (`gate.sh focused` on `git checkout-index` scratch copies, deleted afterwards): `test_role_adapters.SuggestionTests`,
`ApplyTests`, `EvidenceTests`, `test_studio_roles.StudioAdapterTests`, `StudioContractTableTests`, `test_role_protocol.RoleContractTableTests`
(the classes that read `case_roles`, `TEMPLATE_CASES` or `CASES`; `SuggestionTests` uses the unchanged `mono` case).
- PATCH_DEP only (staged tree): Ran 50, OK, `GATE focused EXIT 0`.
- With the delta: Ran 50, FAILED (failures=13, errors=6) = 19 reds, all new, all on the table's stated reason (`body` replaces `.btn/.nav-link`
  and the group part demands body/page), none unclassified:
  Bridge (owner R2.W2P, the BASE bridge refuses a body role on `['body']` or binds author-id selectors), 11:
  - ApplyTests: `inline_root_variable_beats_the_role_and_clear_keeps_the_attribute`; `clear_restores_the_variables_the_styles_and_the_dom`
    (body, mixed); `every_template_case_emits_its_exact_bytes...` (body, body-without-family, mixed); `without_the_stylesheet_constructor_the_rule_count_is_the_block_count`
  - EvidenceTests (the three the review found): `detect_with_a_live_bootstrap_preview_returns_the_groups_of_a_detect_without_it`,
    `no_transition_ban_survives_an_apply_over_a_live_preview`, `evidence_comes_from_the_page_and_not_from_the_live_preview` (ERROR KeyError 'canonicalCss')
  - test_role_protocol.RoleContractTableTests: `a_bootstrap5_detect_posts_a_reply_the_table_allows_with_a_group_that_is_not_plain`
  Studio (owner R2.W2PS), 8:
  - StudioAdapterTests: `ready_snapshot_with_each_template_cases_literal_bytes...` (body, body-without-family, mixed; ERROR timeouts),
    `unsupported_adapter_rejection_keeps_the_template_preview...` (ERROR), `apply_sends_each_selected_groups_adapter...` (ERROR),
    `the_body_case_receipt_shows_its_template_bytes...` (FAIL on old selectors)
  - StudioContractTableTests: `detected_reply_limits_render_at_the_limit_and_are_refused_one_past` rows `binding reason`, `stable flag` (page on a plain group;
    replaced by the `every_reason` split below)
  Total 11 + 8 = 19. This is the census of the six classes above, not of the suite (full suite not run, override).

## Handoff additions (supersede the Handoff above only where stated)
Add to the `valid_page` list (one row; needs `body_check` defined before it) and to `page_defects` (two rows); the defect count becomes 53 + 19 + 2 = 74
(docstring "each of 74 defects"); harness-verified, each defect gives exactly one violation, each valid row `[]`:
```python
body_check = {'roleId': 'role-1', 'selector': 'body', 'matchCount': 0, 'signatures': []}
# valid_page gains:
              ('detected', 'a selector check on body', self.reply(request, [page_body], selectorChecks=[body_check])),
# page_defects gains:
    ('roles-applied', 'body role on BODY', {'roles': [{**body_role, 'selectors': ['BODY']}]}),
    ('role-state', 'body role with body twice', {'roles': [{**body_role, 'selectors': ['body', 'body']}]}),
```
- `['BODY']` is refused (one violation). `['body','body']` as a role in a receipt or state is refused too (one violation): the bridge
  de-duplicates a REQUEST's selectors, so the passing case is the request `['body','body']` answered by the receipt role `['body']`, which the
  existing valid rows `one body role on body and one mono role` (roles-applied and role-state) already cover. No separate valid row was added
  (it would be a copy); W2PS asserts the request side against Studio, not the table.
- Do not use a body group with `stable: False` (or any wrong flag on the page binding) in an "exactly one violation" assert: it gives two
  (exactness and the stable rule).

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
