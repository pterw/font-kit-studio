# R2.W2T brief: the contract table checks what PR B2 added

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 (task R2.W2T), Addendum 17 item 3 (a field change updates the
table first), D070, D072. PR B2 wave W2, phase 1, beside R2.W2L and R2.W2B2 (disjoint files). BASE
`73b3ba2b2bbc00ee4f501a338e61ff422afed8ff` (adds Addendum 22). Worktree `a scratch worktree` (detached at BASE; the controller
creates it and links the npm fixtures), task id `w2t`. Tests only: no product file changes. Line budget: about 190 gross
lines (insertions plus deletions); explain any excess.

## Why

The whole-branch review (workspace `w2-review.md`, items T8, R1, R7, T13, S5; each checked in source) found the contract
table looser than the contract and than both sides, and test-side copies of contract facts:

1. `violations('detected', ...)` (`tests/role_contract.py` 180-200) never checks a group's `adapter`, the field PR B2 added
   (D068). The checker's self-test (`tests/test_studio_roles.py` 2501-2570, "a row for each rule the checker applies", 46
   defects) has no adapter row, so a reply whose group carries `bootstrap9`, `null` or no `adapter` passes the table. Three
   inline re-assertions in `RoleContractTableTests` (`tests/test_role_protocol.py` 346, 359, 372) exist only because the
   checker lacks the rule.
2. The header (`role_contract.py` 3) says the values come from "Addenda 13-18", but the table also encodes Addendum 17's
   template bytes and Addendum 20's per-property loss limit.
3. `CHECK_SIGNATURES` (1,024, D070) is neither reached by the real-bridge class nor listed in `STUDIO_SIDE_ONLY` (53-67).
   `RoleContractTableTests` builds 136 (`tests/test_role_protocol.py` 281: sizes `10 + v * 2 + r / 10` first collide at 21
   roles, 161 distinct of 168, and give 268 distinct sizes for 128 roles; the test at 376 asserts `17 * table.VARIANTS` at
   386). A review probe with sizes `10 + v * 2 + r / 100` reached one 1,024-signature check: complete, 468,181 reply bytes,
   no violation.
4. `chars()` (121) counts Python code points; Studio and the bridge count UTF-16 code units (JavaScript `length`), so a
   101-emoji name (202 units against `NAME_CHARS` 200, still 101 code points) passes the table. The `NUMBER_RULES` check
   (157) accepts booleans (`isinstance(True, int)`), which both sides refuse; `count()` (124) already excludes them.
5. D072 (Addendum 22 item 1) adds a family rule that the table carries first: a family that is exactly a CSS-wide keyword
   (`inherit`, `initial`, `unset`, `revert`, `revert-layer`, any case, after trimming) or holds `(` or `)` outside quotes is
   refused. R2.W2B1 (bridge) and R2.W2S (Studio) take their test cases from the table, so name the cases as data.
6. `fnv1a32` has three test copies (`tests/test_r2_react.py` 85, `tests/test_role_stylesheet.py` 38,
   `tests/test_studio_roles.py` 41) and `EMPTY_HASH` four (`role_contract.py` 34, `test_r2_react.py` 60,
   `test_role_stylesheet.py` 10, `test_studio_roles.py` 29). Global rule 10 abstracts at the third copy, within one side;
   FNV-1a32 is part of the binding contract, so the table is its test-side home.
7. Literal limits still sit beside table names in `tests/test_studio_roles.py`. The C0 report
   (`docs/implementation/tasks/r2-task-c0-report.md` 163-176, "Literal limits left in other Studio tests") lists nine
   tests; eight hold table limits (the ninth, the 200-character rejection detail cut, does not). Sites: 1055
   `128 * 1024 + 1` (`CSS_BYTES`), 1069 `10001` (`CHECKED`), 1078 `'.' + 'a' * 2000` (`WINNING_SELECTOR_CHARS`), 445
   `'d' * 201` (`DOCUMENT_ID_CHARS`), 448 and 1045 `'x' * 2000` (`ROUTE_CHARS`), 760 `'A' * 300` / `'A' * 301`
   (`FAMILY_CHARS`), 1316 `'\u754c' * 300` (`FAMILY_CHARS`), 361, 366, 371 `128` (`ROLES`), 1123 and 1126
   `range(1, 129)` (`ROLES`), 1127 `128 * 700` (`ROLES`) and `256 * 1024` (`REQUEST_BYTES`), 1240 `'.' + 'a' * 1999`
   (`WINNING_SELECTOR_CHARS`), 1936 `range(128)` (`ROLES`), and 422 `'811c9dc5'` (`EMPTY_HASH`). Not limits, and they
   stay: 1319 (`1990` padding), 1474-1476 (the 200-character detail cut), 362 (`* 1050`).
8. `tests/test_r2_react.py`: the module docstring (1) still says "role preview belongs to F2b", although the module holds
   it now; `OWNED` (51) and the locator at 557 select `#fontkit-role-styles` while `test_role_stylesheet.py` 7 selects
   `style[data-fontkit-role-styles]`. The post-Clear `== []` assertions are not vacuous (each test asserts `[css]` first: 530,
   584, 633, 696); the change makes the module use one selector.
9. Two items the ledger routed here: `NAMED_SELECTOR_CHARS` (`role_contract.py` 29) is dead (only a `STUDIO_SIDE_ONLY` key at
   59 uses it), and the self-test docstring count (2503, "46") changes with every row added.

RED against the unchanged table: items 1, 4 and 5 (a row fails before the rule exists). GREEN characterizations: items 3, 6,
7 and 8 (existing behaviour). The report gives RED-first evidence for items 1, 4 and 5 (the new rows failing on the unchanged
table) as well as the mutants.

## Owned files (exact)

- `tests/role_contract.py`.
- `tests/test_studio_roles.py`: the module constants `EMPTY_HASH` (29) and `fnv1a32` (41), which become the table's (bind
  them as `EMPTY_HASH, fnv1a32 = table.EMPTY_HASH, table.fnv1a32` beside the existing `import role_contract as table`, so
  the 12 uses stay as they are); the literals of item 7; the checker self-test at 2501 (new defect rows and loops); and the
  `rows` dict of `test_role_input_limits_are_refused_one_past_and_accepted_at_the_limit_in_a_ready_snapshot` (2580;
  row additions only, requirement 4). R2.W2S edits this file after you, on your patch: touch nothing else in it. The plan's
  Owns line for this task ("for table imports only") is the controller's to correct at landing.
- `tests/test_role_protocol.py`: only `RoleContractTableTests` and the page builder `AUTHOR_ROLES` at 281 (used only by this
  class: 354 and 382; change it in place).
- `tests/test_r2_react.py`: the docstring, `OWNED` (51), the locator at 557, and `EMPTY_HASH` and `fnv1a32` (bound from
  the table the same way, with `import role_contract as table` beside the other test imports). No shared helper for the
  refused-port probes (156-159 and 213-216): leave them as they are.

Read-only: `fontkit-bridge.js`, `fontkit-studio.html`, `tests/test_role_stylesheet.py` (R2.W2B2 and R2.W2B1 own it),
`tests/test_role_preview.py` (its literal 262144 at 470 stays) and every other file. Running worktrees beside yours:
`a scratch worktree` (R2.W2L, `tests/test_studio_live.py`) and `a scratch worktree` (R2.W2B2, `fontkit-bridge.js`,
`tests/test_role_adapters.py`, `tests/test_role_stylesheet.py`): never touch them.

## Read first

`constraints.md` (all of it); Addendum 22 and the "Envelope, limits and types" and "Selector and value validation" sections of
the plan; D070, D072; `docs/implementation/tasks/r2-task-c0-report.md` 163-176 ("Literal limits left in other Studio
tests"); `tests/role_contract.py` (all, 256 lines); at BASE `tests/test_studio_roles.py` 20-60, 699-705, 2461-2472 and
2490-2600, `tests/test_role_protocol.py` 270-300 and 330-395, `tests/test_r2_react.py` 1-100 and 140-220.

## Requirements

1. **Detected adapter.** `violations('detected', ...)` reports a group whose `adapter` is missing or not in `ADAPTERS`. Read it
   with `group.get('adapter')`: a missing key is `None`, the same single violation as the `None` row. It is the one
   exception to the checker's `KeyError` behaviour (every other field is read with `group[...]`), so reword the docstring
   sentence at 110-112 ("It does not compare key sets...") to say so. Self-test rows: `bootstrap9`, `None`, the key removed.
   In `RoleContractTableTests` delete the three inline adapter re-assertions at `test_role_protocol.py` 346, 359 and 372
   only (keep 371 and 373: `adapters` still feeds `assertTrue(adapters - {'plain'}, adapters)`), and reword the docstrings
   (and the test name at 348) so each Then equals what the test still asserts.
2. **Header.** It names every addendum the table encodes: "Addenda 13-18 (17: template bytes; 18: signatures per check), 20
   and 22 (families)" (Addendum 21 changes no table value), and says lengths are UTF-16 units.
3. **1,024 signatures on the bridge side.** Replace (rename) the test at `test_role_protocol.py` 376; do not keep both.
   The new test drives the real bridge to one selector check of exactly `table.CHECK_SIGNATURES` signatures (builder call
   `[table.ROLES, table.VARIANTS]`; builder sizes `10 + v * 2 + r / 100`, which stay distinct for 128 roles; one known role
   `.k`) and asserts: the reply is complete; `len(groups) == table.ROLES` and `max(len(g['signatures'])) == table.VARIANTS`
   (the page reached the limits); the one check's signature count equals `table.CHECK_SIGNATURES`; `table.violations(...)`
   is empty. Every number comes from the table. Measured by the brief review in Windows Chromium 151: complete, 468,181
   reply bytes (44.6% of `REPLY_BYTES`), `elapsedMs` 838-1,030 over about 20 runs and 46-51% of `TIME_BUDGET_MS` with four
   Chromium processes in parallel; the existing at-every-limit Detect takes 42-46 ms, so this test is about 20 times heavier
   (the 1,024-element scan alone is about 500 ms). Proceed. If your run passes `table.REPLY_BYTES` or the 2,000 ms budget in
   Chromium, stop and report it; do not list the limit as Studio-side only on your own. Report three timings and one under
   `shard-2` load (hosted Linux may be 1.5-2x slower; a `time-budget` there is a finding, never a reason to loosen the
   assertion). Firefox 153 reached `time-budget` (about 2,003 ms) in 7 of 9 probe runs; the gate forces Chromium (D037), so
   the report says Firefox is not verified for this test (anti-pattern 14).
4. **UTF-16 and booleans.** `chars()` counts UTF-16 code units: `sum(2 if ord(c) > 0xFFFF else 1 for c in value)` (never
   `len(value.encode('utf-16-le')) // 2`, which raises on a lone surrogate that a cut `sampleText` can carry); the number
   rule refuses `bool`. The oracle is Addendum 22's task line ("counts UTF-16 units") and the contract's TypeScript `string`
   and `number` types, not either side's code. Write astral characters as `chr(0x1F600)`, never as literal characters in
   source. Self-test rows: `chr(0x1F600) * 100` as a name passes `NAME_CHARS` (200 units); `* 101` fails (202 units, 101
   code points); the same pair for a role id (50 passes, 51 fails, against `ROLE_ID_CHARS` 100); `fontWeight: True`. Add two
   rows to the Studio limits test's `rows` dict beside `name` (2591) and `family` (2595): a name of 100 / 101 astral
   characters and `fontWeight` `1` / `True`, so the table's new rules are checked against real Studio.
5. **Families (D072).** Named data in the table, written from the contract text (never from either side's code):
   - `FAMILY_KEYWORDS = ('inherit', 'initial', 'unset', 'revert', 'revert-layer')`.
   - `FAMILIES_REFUSED`, in groups with a one-line engine note each. Keywords: every one in lower case, plus `INHERIT`,
     `Revert-Layer`, and a padded `'  inherit  '` (both CSS engines accept all of them). Dashed functions: `--x(`, `--x(a)`,
     `--x()`, `Inter, --x(`, `if(media(all): Inter`, `"Inter", --x(a)`, `--x("a")` (a quote and an unquoted parenthesis
     together; Chromium accepts them, Firefox's `CSS.supports` already refuses them). Table-only: `generic(kai)`, `Inter)`,
     `a), serif`, `Inter (Display)` (`CSS.supports` already refuses them in both engines today, so R2.W2B1 and R2.W2S must
     never use `generic(kai)` to kill a mutant; a lone `)` is covered only by the table).
   - `FAMILIES_ACCEPTED`, near misses that must still pass: `"inherit"`, `'Inter (Display)'`, `"Inter (Display)"`,
     `Initialism, serif`, `Inherit Sans`, `inherited`, `revert-layers`, `"A)"`, `"Inter's (x)"`, `'say "hi" (x)'`.
   "Outside quotes" is the scan both sides already use: one pass, a `"` or `'` opens a quote, only the same character closes
   it, no escapes (a backslash is refused elsewhere); a parenthesis counts only when no quote is open (bridge
   `balancedQuotes`, 184-190; Studio 3887-3890: read them for the definition, never to copy a rule). The roles part of the
   checker (the `fontFamily` branch at 152) applies the rule to a trimmed `str` only (`isinstance(value, str)`), so a
   non-string family stays the one violation from `chars()` and never raises `AttributeError`.
   Self-test: loop over every case of `FAMILIES_REFUSED` (exactly one violation each) and every case of `FAMILIES_ACCEPTED`
   (none). The mutants of the rule that the loops must kill: no `lower()`, no `strip()`, keyword by prefix or substring,
   quote-blind (any quote present counts as inside, or quotes ignored), and a check for `(` only.
6. **One FNV-1a32.** The table gains `fnv1a32(text)` from the contract (UTF-8 bytes, offset 2166136261, multiplier
   16777619, modulo 2^32, eight lowercase hex digits). No new test: the two existing tests become its self-check once the
   modules bind it. Their oracle is the published FNV-1a vectors (`''`, `a` -> e40c292c, `foobar` -> bf9cf968) in
   `FnvVectorTests` (`test_studio_roles.py` 699-705) and the literal digests of `TEMPLATE_CASES` in
   `test_template_cases_follow_the_addendum_rules_and_carry_their_own_digests` (2461-2472; 2469 asserts
   `fnv1a32(case['css']) == case['hash']`). `test_studio_roles.py` and `test_r2_react.py` bind `EMPTY_HASH` and `fnv1a32`
   from the table and drop their own; `test_role_stylesheet.py` keeps its copy (R2.W2B1 switches it).
7. **Literal limits.** Each literal of item 7 that is a contract limit, or one past it, reads the table name given there.
   A limit the table does not name yet is added to the table with its contract source; a literal that is not a contract
   limit stays. Remove the dead `NAMED_SELECTOR_CHARS` (`role_contract.py` 29) and its `STUDIO_SIDE_ONLY` row (59); the
   Studio test at 2570 only requires each key to be a table name, and `test_role_preview.py` 470 keeps its own literal.
8. **React module.** The docstring says in one line what the module covers now; `OWNED` and the locator at 557 use
   `style[data-fontkit-role-styles]`, the selector `test_role_stylesheet.py` uses.

## Tests and mutants

Every new or changed test method has a Given/When/Then docstring whose Then is exactly what it asserts. The self-test
docstring's "46" becomes the new row count, and its Then names the loops and the boundary pairs it also asserts. For each
new checker rule (items 1, 4, 5) a mutant of the rule in `role_contract.py` (removed or inverted) makes the self-test fail;
for item 5 the five mutants named there. For item 3, the builder back at `r / 10` makes the new assertion fail, and one
bridge-side mutant (a copy of the bridge outside the repo, passed through `bridge_source`, that caps a check at 1,023
signatures) makes it fail too. For item 6, a wrong multiplier in the table's `fnv1a32` makes `FnvVectorTests` and the digest
test at 2469 fail; the report names both. Each mutant runs in the foreground in your worktree; restore the file byte-exact
and record its SHA-256 before and after. A failing green is worse than a true red: a red you cannot explain is reported as red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_role_protocol.RoleContractTableTests test_r2_react test_support`
(the whole `test_studio_roles` module, because the constant and literal replacements reach across it). Also
`python -m ruff check` on the changed files and, after staging by name, `git diff --cached --check`.

## Report and handoff

Report: each requirement with its oracle and the lines changed; the RED-first evidence for items 1, 4 and 5; the self-test
rows and loops added; each mutant (command, failing test and line, SHA-256 before and after); the item 3 timings; the
focused run (Ran line, OK, GATE line); gross and material lines; Firefox not verified for the 1,024-signature test. Handoff:
the patch `task-w2t-code.patch`, the commit subject `test: check adapters, UTF-16 lengths and families in the contract`, a
draft body (why, wrapped at 72, no process narration) and the R2.W2T plan item.
