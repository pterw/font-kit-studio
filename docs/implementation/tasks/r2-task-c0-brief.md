# R2.C0 brief: the contract table and parity checks

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.C0 and Addendum 17 item 3; the binding contract
("Binding protocol contract", including Addendum 16's `DetectedGroup.adapter` line) and D063-D070.
PR B2, wave W0. BASE `6af29325ac2ee0512b2a53266cf54a3bc8118f8d` (carries Addenda 17-18 and D069-D070 as
committed); worktree `C:/fks/tc0` (detached at BASE). Task id `c0`. Line budget: about 450 material
lines (table about 210, two classes about 100 each, step 4 about 25); explain any excess.

## Why

PR B's per-task reviews missed drift between Studio and the bridge that two whole-branch reviews then
found (the revision-conflict detail shape, the `matched`/`checked`/loss caps). PR B2 adds a field and a
serializer on both sides. One table of the contract's limits, enums and shapes, which tests on both sides
import, makes such drift a failing test. This task builds the table and checks both sides against it. It
changes no product code.

## Owned files (exact)

- Create `tests/role_contract.py`.
- `tests/test_studio_roles.py`: add one class, `StudioContractTableTests(StudioRoleCase)`; and, in the seven
  existing tests named in step 4 only, replace the literal limits with the table's names.
- `tests/test_role_protocol.py`: add one class, `RoleContractTableTests(RoleSheetCase)`, importing
  `RoleSheetCase` and `role` from `test_role_stylesheet` as `test_role_detection.py` imports its helpers.

Read-only: everything else, including `fontkit-bridge.js` and `fontkit-studio.html` (except temporary,
restored mutants, see Test rules), `tests/support.py`, `tests/role_support.py` and the other test modules
(importing their helpers is allowed).

## Read first

`constraints.md` (all of it); the plan's binding contract and Addenda 16-17; D068-D070; the review of this
brief, `task-c0-brief-review.md` (its Appendix A is the inventory of existing pins at BASE, Appendix B the
literal template bytes, Appendix C the probes); and at BASE: `tests/test_studio_roles.py` (helpers
`group`, `canonical_css`, `fnv1a32`, `loss`, `outcome`, the peer, `StudioRoleCase.open/pending/reply/send/
detected/receipt/ready_with/snapshot_state/role_input/preview/gate/press_apply`), `tests/role_support.py`,
`tests/test_role_stylesheet.py` (`role`, `RoleSheetCase.apply/clear`), `tests/test_bridge_runtime.py`
(`BridgeCase.hello/request`) and `tests/test_role_detection.py:314-341` (pages built with `frame.evaluate`).

## 1. The table: `tests/role_contract.py`

A module docstring says the values come from the plan's binding contract and Addenda 13-17, and, where the
plan is silent, from the R2.5 brief (`docs/implementation/tasks/r2-task-5-brief.md`, pins and additions),
the PR B fix brief (`r2-task-bfix-brief.md`) and the PR B review (`r2-pr-b-review.md`), never from
`fontkit-bridge.js` or `fontkit-studio.html`. Each constant has a one-line comment naming its source.

| Name | Value | Contract source |
|---|---|---|
| `ROLES` | 128 | role/group count per scan and request; knownRoles |
| `SELECTORS` | 32 | selectors per role |
| `SELECTOR_CHARS` | 2000 | selector length |
| `NTH_MAX` | 9999 | `:nth-of-type(n)` |
| `ROLE_ID_CHARS` / `NAME_CHARS` | 100 / 200 | role and group ids; label, suggested name and author-role name |
| `SAMPLE_CHARS` / `SHARED_CLASSES` / `CLASS_CHARS` | 200 / 16 / 200 | sample text; shared classes |
| `VARIANTS` | 8 | signature variants per author role |
| `NEAR_DUPLICATES` | 127 | other groups in one reply (`ROLES - 1`) |
| `CHECK_SIGNATURES` | 1024 (`ROLES * VARIANTS`) | style signatures per `SelectorCheck` (D070, Addendum 18); Studio caps at 128 until R2.S3 |
| `SELECTOR_CHECKS` | 4096 (`ROLES * SELECTORS`) | selector checks per reply |
| `ELEMENTS` | 10000 | `scannedElements` of a complete reply |
| `ELEMENTS_INCOMPLETE` | 10001 | `scannedElements` of an incomplete reply: `element-limit` reports the first element past the limit |
| `TIME_BUDGET_MS` | 2000 | `elapsedMs` of a complete reply |
| `CHECKED` | 10000 | `checked` per outcome (R2.5); `matched` has no cap; a loss `count` is at most `CHECKED` |
| `LOSSES_PER_PROPERTY` / `LOSSES` | 16 / 96 | loss groups per role and property; per outcome (R2.5) |
| `WINNING_SELECTOR_CHARS` | 2000 | `winningSelector`; no C0, DEL, C1, U+2028 or U+2029 characters |
| `NAMED_SELECTOR_CHARS` | 262144 | named winning-selector characters per receipt (R2.5; bridge side only) |
| `REQUEST_ID_CHARS` / `DOCUMENT_ID_CHARS` | 200 / 200 | `requestId`, `documentId` |
| `ROUTE_CHARS` | 2000 | route text (path, search and hash) |
| `FAMILY_CHARS` | 300 | trimmed `RoleInput` family |
| `REQUEST_BYTES` / `REPLY_BYTES` / `CSS_BYTES` | 256 KiB / 1 MiB / 128 KiB | UTF-8 JSON; canonical CSS |
| `EMPTY_HASH` | `'811c9dc5'` | FNV-1a32 of the empty string |

Enums as tuples: `CASES`, `ADAPTERS`, `BINDING_REASONS` (with `STABLE_REASONS = ('author-role',
'author-id', 'class')`: a binding is stable exactly when its reason is one of them), `LOSS_REASONS` (the
contract's order), `OUTCOME_REASONS` (`None`, `'page-changed'`, `'budget-exceeded'`), `DETECT_REASONS` (the
seven incomplete reasons), `REJECTION_REASONS`, and `PROPERTY_ORDER`. `NUMBER_RULES`: `{'fontSize': (4, 400,
2), 'fontWeight': (1, 1000, 0), 'lineHeight': (0.5, 5, 3), 'letterSpacing': (-0.5, 2, 4)}` (min, max,
decimals). `FAMILY_CHARS` and `NUMBER_RULES` apply to `RoleInput` properties only (requests, receipt roles,
role state); an observed `StyleSignature` family is unbounded and its measured size only nonnegative.
`STUDIO_SIDE_ONLY`: a dict from table names to a one-line reason, for each limit the bridge-side class does
not reach in a test (step 3).

Builders (pure functions, no browser; each returns valid contract values of exact size):

- `text(length, prefix='t')`: `prefix` padded with `'a'` to exactly `length` characters.
- `class_selector(length)`: a valid role selector of exactly `length` characters (`'.' + 'a' * ...`).
- `selectors(count)`: `count` distinct valid class selectors.
- `class_names(count, length)`: `count` distinct class names, each exactly `length` characters.
- `styles(count)`: `count` distinct valid `StyleSignature` dicts.
- `losses(per_property)`: `per_property` distinct `author-rule` loss entries (count 1, distinct winning
  selectors) for each of the six properties, in the contract's loss order.

Checker: `violations(kind, message)` returns a list of strings, one per value outside the table, for `kind`
in `'detected'`, `'roles-applied'`, `'rejected'` and `'role-state'`. It checks counts, lengths, UTF-8 byte
sizes (the message as posted, `json.dumps(..., ensure_ascii=False, separators=(',', ':'))`), enum membership,
number ranges and decimals, `scannedElements` (at most `ELEMENTS` when `complete`, at most
`ELEMENTS_INCOMPLETE` otherwise), `elapsedMs` of a complete reply, the stable/reason rule, the contract's
invariants (variant counts sum to `elementCount`; `mismatched <= checked <= matched`; ids unique;
near-duplicate ids name other groups of the reply), and the rejection detail shape: absent, a string, or,
for `revision-conflict` only, exactly `{baseRevision, revision}` with nonnegative integers. It does not
compare key sets: both sides already validate exact field lists, and R2.4 adds the adapter check.

Template cases (Addendum 17 item 1): `TEMPLATE_CASES`, a tuple of dicts `{'name', 'roles', 'css', 'hash'}`
whose `css` and `hash` are literals written from the addendum's rules, never produced by code, each `css`
written with explicit `\n` escapes in a single-quoted string (the checkout has `core.autocrlf=true`):

1. `body`: role-1 `bootstrap5-body`, selectors `['.btn', '.nav-link']`, `fontFamily: 'Inter'`,
   `fontSize: 18`: the addendum's example bytes.
2. `mono`: role-1 `bootstrap5-mono`, selectors `['code']`, `fontFamily: '"JetBrains Mono"'`.
3. `body-without-family`: role-1 `bootstrap5-body`, selectors `['.btn', '.nav-link']`, only
   `fontWeight: 500` (plain bytes only).
4. `heading`: role-1 `bootstrap5-heading`, selectors `['h2', '.h2']`, `fontFamily: 'Fraunces'`,
   `fontSize: 32` (plain bytes).
5. `mixed`: role-1 `plain`, selectors `['.lead']`, `fontSize: 20`; then the `body`, `mono` and `heading`
   roles as role-2, role-3 and role-4 (two `:root` blocks, never merged).

Names are short ASCII; every role is a valid `RoleInput`. The review's Appendix B gives the bytes and
digests your literals must equal. These cases are data for W1 (R2.4 and R2.S3 assert their serializers
against them).

## 2. Studio side: `StudioContractTableTests`

Start from the review's Appendix A (existing pins at BASE). Write the report's Inventory as that table
updated with your additions: for every row, the tests that pin it at the limit and one past it, on the
Studio side and on the bridge side, or `gap`. Then add tests for the Studio-side gaps, as subtests in
shared loops, each assertion with the table's names and builders:

- RoleInput limits through a ready snapshot (`ready_with` + `snapshot_state`, overriding `role_input`'s
  fixed selectors with a dict merge): a role id of `ROLE_ID_CHARS` and one more; a name of `NAME_CHARS` and
  one more; `SELECTORS` selectors and one more; a selector of `SELECTOR_CHARS` and one more; `ROLES + 1`
  roles; a family of `FAMILY_CHARS` and one more; each `NUMBER_RULES` minimum and maximum, and one step
  past each. At the limit the snapshot's CSS is what `#rolePreviewCss` shows and Detect is enabled; one
  past it Studio shows `This bridge does not support role detection/preview.`, Detect is disabled, and the
  next valid ready recovers (the observable of `test_ready_requires_exact_snapshot_and_supported_capability`).
- Detected-reply limits (`pending`, `reply`, `send`, then a fence reply as in
  `test_exact_hostile_shapes_leave_rendered_snapshot_and_legacy_ledger_intact`); build every group with
  `group(...)` or `{**group(...), ...}`, never a literal, and use a fresh page for each 128-group reply (the
  collection holds 128 issued ids): `ROLES + 1` groups; a group id of `ROLE_ID_CHARS` and one more; a
  suggested name and an author name of `NAME_CHARS`; a sample of `SAMPLE_CHARS`; `SHARED_CLASSES` classes;
  a shared class of `CLASS_CHARS` and one more; `VARIANTS` and `VARIANTS + 1` variants on an author-role
  group (counts summing to `elementCount`); `NEAR_DUPLICATES` ids on one group across `ROLES` groups (the
  one-past side is implied by `ROLES` plus uniqueness: record it as implied, and its mutant is `> 127` to
  `> 126`); `scannedElements` of a complete `ELEMENTS` reply renders, an incomplete `ELEMENTS_INCOMPLETE`
  renders and one more is refused; an unknown binding reason, a stable/reason mismatch and an unknown
  `textTransform` in a signature are refused. At the limit the rows render; one past it the fence renders
  and nothing of the refused reply does.
- Outcome rows not yet pinned: `checked == CHECKED` renders; `mismatched` and a loss `count` of `CHECKED`
  render and one more is refused.
- Rejection details: no new test (pinned by `test_a_revision_conflict_with_the_bridges_object_detail_settles_the_op_and_adopts_the_revision`,
  `test_role_rejections_keep_the_preview_and_drafts_show_next_steps_and_are_never_retried`,
  `test_malformed_rejections_are_ignored_and_leave_the_request_in_flight`, and against the real bridge
  `test_a_revision_conflict_from_the_real_bridge_settles_at_once_and_the_next_apply_succeeds`).
- Browser-free self-checks: for every `TEMPLATE_CASES` entry `hash == fnv1a32(css)` (this module's own
  `fnv1a32`); `css` with its `:root {...}\n` blocks removed equals `canonical_css(roles)`; the removed
  blocks, in order, equal the variable lines of each body (`--bs-body-font-family`, then
  `--bs-font-sans-serif`) and mono (`--bs-font-monospace`) role that sets a family, from a three-line table
  in the test. The builders return exact sizes and distinct values; `violations` returns `[]` for one
  hand-written valid message per kind and exactly one string for each single-defect copy (groups `ROLES +
  1`, a sample of `SAMPLE_CHARS + 1`, an unknown reason, a conflict detail with an extra key, a 17th loss
  for one property); every `STUDIO_SIDE_ONLY` key is a table name.
- `REQUEST_BYTES` at the exact boundary: record in the Inventory that Studio's Apply probe uses a
  placeholder request id and so refuses a few bytes earlier than the bridge; this is not drift.

## 3. Bridge side: `RoleContractTableTests`

Drive the real bridge to its reachable extremes and assert `violations(kind, message) == []` for every
message it posts. Build pages with `frame.evaluate` after `open` and before `hello`, as
`test_role_detection.py:314-341` does. For each page, assert its premises with the table's names first: a
bridge extreme whose premise is not asserted is vacuous.

- A complete scan at the limits: `ROLES` distinct styles (8 sizes 16.00-16.07px x 16 weights 400-415, so
  every group is near the other 127); among them one group of 32 elements whose `data-design-id` values are
  padded so each selector is `SELECTOR_CHARS` long, and one group of a single element with 20 classes (one
  of them `CLASS_CHARS + 1` long) and a text node of 300 characters. Premises: `len(groups) == ROLES`,
  `max(len(nearDuplicateIds)) == NEAR_DUPLICATES`, `max(len(selectors)) == SELECTORS` with a value of exactly
  `SELECTOR_CHARS`, `max(len(sharedClasses)) == SHARED_CLASSES` with none over `CLASS_CHARS`,
  `max(len(sampleText)) == SAMPLE_CHARS`.
- `ROLES + 1` distinct styles: `reason == 'group-limit'`, `len(groups) == ROLES`. This reply stops before
  bindings, so only the group count and the sample text are reached; the docstring says so.
- A known role selector over many styles: 17 author roles (`data-design-role`) x `VARIANTS` sizes, every
  element with class `k`, `knownRoles: [{'id': 'k', 'selectors': ['.k']}]`. Premise: the one check has
  `17 * VARIANTS` signatures (over Studio's current 128); then the reply fits the table
  (`CHECK_SIGNATURES` = 1,024, D070). The Studio half of this row (a check of `CHECK_SIGNATURES` signatures
  renders, one more is refused) is RED at BASE: write it, keep it out of the patch, and put it in the
  Handoff as R2.S3's RED test.
- A maximal apply: `ROLES` roles, each with an id of `ROLE_ID_CHARS`, a name of `NAME_CHARS`, `SELECTORS`
  distinct selectors, a family of `FAMILY_CHARS`, the maxima of `NUMBER_RULES`, and a request id of
  `REQUEST_ID_CHARS`; assert the request is within `REQUEST_BYTES`; the receipt fits; then
  `self.hello(page, 's2')` and the ready's `roleState` fits (`'role-state'`). Apply `ROLES + 1` roles: the
  `invalid-message` rejection fits.
- A stale `baseRevision`: the `revision-conflict` rejection's detail is the object shape and fits.
- The loss cap: one role over 17 paragraphs and 17 author rules (`p.eN`), each losing all six properties:
  exactly `LOSSES` loss entries, `LOSSES_PER_PROPERTY` per property, and the receipt fits.

Limits not reached here go in `STUDIO_SIDE_ONLY` with the reason.

## 4. Existing boundary tests read the table

In `tests/test_studio_roles.py`, replace the literal limit values with the table's names, with no change in
value or behaviour, in exactly these seven tests:
`test_exact_hostile_shapes_leave_rendered_snapshot_and_legacy_ledger_intact`,
`test_selector_boundaries_accept_2000_characters_nth_9999_and_32_selectors` (its `range(30)` becomes
`range(SELECTORS - 2)`),
`test_request_limit_counts_utf8_bytes_not_characters`,
`test_detected_reply_at_one_mib_is_accepted_and_one_byte_more_is_not`,
`test_outcome_limits_follow_what_the_bridge_can_send`,
`test_a_receipt_css_at_128_kib_is_accepted_and_one_byte_more_is_not`,
`test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not`.
Only values that are table limits change (for example `1024 * 1024` -> `REPLY_BYTES`,
`'x' * 201` -> `'x' * (SAMPLE_CHARS + 1)`). Test names and docstrings stay. List in the report every literal
limit left in other tests (the review names six: `test_bounded_rows_collection_and_utf8_request_limit_are_visible`,
`test_apply_refuses_a_request_over_256_kib_counted_in_utf8_bytes_and_names_the_limit`, `hostile_receipts`,
`test_ready_requires_exact_snapshot_and_supported_capability`,
`test_a_winning_selector_is_bounded_text_and_every_reason_reads_in_plain_words`,
`test_the_collection_limit_disables_apply_with_a_visible_reason_for_the_life_of_the_ids`); they stay as they are.

## Test rules for this task

- Existing behaviour is characterized GREEN. A row where either side accepts one past the limit, refuses the
  limit, or emits a value outside the table is drift: write the test to the contract, keep it out of the
  patch (every commit lands green), put it in the report's Handoff with its failing output, and return
  DONE_WITH_CONCERNS. Never change a test to match the code. D070 already settles the one known drift
  (`CHECK_SIGNATURES`); its Studio half is that kind of handoff test.
- Each new test method has a Given/When/Then docstring whose Then is exactly what it asserts. Each table
  row in a table-driven test gets its own recorded mutant (a one-line change, only that subtest run), not
  one per method. Studio mutants edit `fontkit-studio.html` in your worktree temporarily, restored in
  `finally`, SHA-256 before and after; bridge mutants are served through
  `RoleBridgeCase.open(bridge_source=...)` (the file is never edited); a template self-check mutant changes
  one byte of a case's `css`.
- Expected values come from the table, literals or this brief, never from the code under test.
- Import the table as `import role_contract as table` (Ruff selects F: no star imports, no unused names).

## Focused gate

From the worktree, in Git Bash:
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_role_protocol test_support`
(it sets `PYTHONPATH=tests`, Chromium and `FKS_REQUIRE_FIXTURES=1`). No npm fixture is needed. Also
`python -m ruff check tests/role_contract.py tests/test_studio_roles.py tests/test_role_protocol.py`, and
after staging by name, `git diff --cached --check`.

## Report and handoff

Report sections: Inventory (Appendix A updated: row -> pinning tests per side, or gap); what changed, by
file; per new test or table row, its docstring Then, its oracle and its mutant (command, failing line,
SHA-256 before and after); focused output (`Ran` line and `OK` or the failures); material lines added;
deviations with the rule that forced them. Handoff: the patch path, the commit subject `test: add the role
contract table and its parity checks`, a draft body (why, no process narration, wrapped at 72), any red
drift test kept out of the patch, and the R2.C0 plan items that are done.
