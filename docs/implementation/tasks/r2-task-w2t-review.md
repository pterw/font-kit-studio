### Spec Compliance
- PASS: Req 1, detected adapter. `group.get('adapter') in ADAPTERS` (role_contract.py, detected loop); docstring reworded to say `adapter` is the one non-KeyError field; rows `bootstrap9`, `None`, key removed (test_studio_roles.py self-test). The three inline adapter re-assertions are gone from test_role_protocol.py (old 346, 359, 372); `adapters` and its `assertTrue(adapters - {'plain'})` kept; two tests renamed and both Thens match their assertions. The first test (maximal groups) had no docstring Then about adapters.
- PASS: Req 2, header names "Addenda 13-18 (17: template bytes; 18: signatures per check), 20 and 22 (families)" and UTF-16 units.
- PASS: Req 3, 1,024 signatures. Old 136 test replaced and renamed (one test, not two); builder call `[table.ROLES, table.VARIANTS]`, sizes `r / 100`; asserts complete, `(len(groups), max signatures) == (ROLES, VARIANTS)`, one check `('k', CHECK_SIGNATURES)`, no violation; all numbers from the table (test_role_protocol.py new test). Timings reported: 785/793/801 ms and 760/801/834 ms under shard-2 load, reply 44.6% of REPLY_BYTES; Firefox stated as not verified.
- PASS: Req 4, `chars()` counts UTF-16 units with `sum(2 if ord(char) > 0xFFFF else 1 ...)` (not utf-16-le encode); numbers refuse bool; astral written as `chr(0x1F600)`; self-test rows for name 101 / id 51 / `fontWeight: True` plus the at-limit pass case; two Studio `rows` additions (`name in UTF-16 units` 100/101, `weight as a boolean` 1/True), row additions only.
- PASS: Req 5, `FAMILY_KEYWORDS`, `FAMILIES_REFUSED` (grouped, engine note per group, all required cases incl. `'  inherit  '`, `INHERIT`, `Revert-Layer`, `--x("a")`, `Inter)`, `a), serif`), `FAMILIES_ACCEPTED` (all 10 required). One-pass quote scan; applied to `str` only. Self-test loops over both tuples.
- PASS: Req 6, `fnv1a32` in the table (UTF-8, offset 2166136261, multiplier 16777619, `% 2 ** 32`, 8 hex digits); `test_studio_roles.py` and `test_r2_react.py` bind `EMPTY_HASH, fnv1a32 = table...` and drop their copies; `test_role_stylesheet.py` untouched. No new test, as briefed.
- PASS: Req 7, every listed site reads a table name (361/366/371, 445, 448, 1045, 760, 1316, 1055, 1069, 1078, 1240, 1123/1126/1127, 1936, 422). Stays as briefed: 1319, 1474-1476, `* 1050`, `* 700`. `NAMED_SELECTOR_CHARS` and its `STUDIO_SIDE_ONLY` row removed. Self-test docstring "46" -> "53": counted 48 rows + 5 controls = 53 (BASE 41 + 5 = 46).
- PASS: Req 8, docstring, `OWNED` and the locator at test_r2_react.py:551 use `style[data-fontkit-role-styles]`; the bridge sets that attribute (fontkit-bridge.js:1374).
- PASS: scope. Only the four owned files; tests only; no bridge/Studio source; test_role_stylesheet.py and test_role_preview.py untouched. 175 gross lines (114+61) within the 190 budget.
- PASS: addition beyond the brief, the `family that is not text` row (`fontFamily: 5`). The brief's own Req 5 mandates the `isinstance(value, str)` guard; without this row that guard would be an untested branch (constraints: no untested branch). Mutant M9 (drop the guard) turns it into an AttributeError error per the report. Keep it.

### Checks run
- Frozen worktree untouched -> sha256sum of the four test files and fontkit-bridge.js before and after -> identical; `git status` shows only the four staged files; `git diff --cached --check` clean.
- Mutants of the family rule (PYTHONDONTWRITEBYTECODE=1, mutated copies of role_contract.py in the scratchpad, shadowing the import by cwd, unittest of `StudioContractTableTests.test_the_checker_passes_...once`):
  - no `lower()` -> FAIL refused `INHERIT`, `Revert-Layer`.
  - no `strip()` -> FAIL refused `'  inherit  '`.
  - quote-blind (any quote counts as inside) -> FAIL refused `"Inter", --x(a)`.
  - keyword by prefix -> FAIL accepted `Inherit Sans`, `Initialism, serif`, `inherited`, `revert-layers`.
  - `(` only -> FAIL refused `Inter)`, `a), serif`.
- Mutants of the other table rules, same method: adapter check removed -> FAIL `adapter`, `adapter null`, `adapter missing`; `len(value)` for units -> FAIL `name in UTF-16 units`, `role id in UTF-16 units`; bool accepted -> FAIL `boolean weight`.
- Bridge-side mutant, reproduced through `RoleBridgeCase.open(bridge_source=...)` (in-memory copy of the bridge, patched in a scratch script; repo bridge untouched): control passes (OK, 2.4 s); capping a check at 1,023 signatures -> FAIL `[('k', 1023)] != [('k', 1024)]`.
- Builder mutant: `AUTHOR_ROLES` with `r / 10` (patched in a scratch script) -> FAIL `[('k', 268)] != [('k', 1024)]`.
- Studio `rows` additions are real checks of the table rule against Studio -> read fontkit-studio.html:3899-3911 (`validRoleProperties` requires `typeof value === "number"`) -> Studio refuses boolean weight; the row's `violations` assertion fails if the table accepts bool (M3). Not rerun in a browser; the report's L2/L3 runs and the full focused run (140 tests OK, 0 skips) are the evidence.
- Hidden skips -> grep skip/Skip in the four files, tests/role_support.py, tests/support.py; CI env -> none of the new or changed tests skips. The 1,024 test, the Studio rows and the self-test all run under hosted `FKS_ENGINES=chromium`. They are not in the Firefox canary list. Risk is timing only (see Assessment).
- Leftover literals -> grep in test_studio_roles.py -> only `'role-128'` (an id), `'d' * 201` (detail cut, stays), docstrings, and two `'811c9dc5'` inside JS fixture strings (lines 83, 100; not in the brief).

Checklist

1. Drift. Limits, enums and null rule: `ADAPTERS` (enum, None/missing refused) is the table's existing tuple, used unchanged; name 200 and id 100 units match the Studio `roleText(role.name, 200)` / `roleText(role.id, 100)` (fontkit-studio.html:3913-3914) and are asserted against real Studio at 100/101 astral; `FAMILY_CHARS` unchanged; `fontWeight` 1..1000, 0 places, no bool matches Studio:3908. The family rule has no side implementation yet (R2.W2B1/W2S); the table is the only home and its data is named for them. No drift found in touched fields.
2. Mutants. Eight table mutants and two test-data/bridge mutants reproduced (above); all killed.
3. Fake versus real. Adapter: real-bridge replies pass through `violations('detected')` in `RoleContractTableTests` (including a Bootstrap 5 fixture with non-plain adapters). UTF-16 and bool: checked against real Studio via the two new `rows`; not checked against the real bridge (the brief does not ask). Families: no real-peer case yet; the brief defers it to W2B1/W2S. 1,024 signatures: real bridge.
4. Hidden skips: none (above).
5. Test design. Recorded mutant per new test: yes (all items). Independent oracle: published vectors/digests for FNV (existing tests), contract text for families, chr(0x1F600) units arithmetic, table numbers for 1,024. Observable outcome: reply fields and violation lists. Given/When/Then: Thens match assertions (self-test docstring names loops, the boundary pairs and the count 53). Limits are imported from the table. One gap: the self-test docstring count 53 is not asserted by code (it was not before either).
6. Code. `family_refused` and `fnv1a32` are single definitions on the table side; validation (`family_refused`), the need/violation recording and rendering stay separate. `family_refused` has one caller but is also the table's public data-adjacent function for the later tasks and is tested through the loops, so I do not rate it a one-caller abstraction. No untested branch: each `or`/`and` of the rule is killed by a mutant (isinstance guard by M9). Within budget.

### Strengths
- Family data is named, grouped with engine notes (never `generic(kai)` to kill a mutant) and the self-test loops over every case, which killed all five rule mutants I reproduced.
- The 1,024 test asserts the page reached both limits before asserting the check, so a weak builder fails loudly; both builder and bridge-side mutants fail it.
- `fnv1a32` consolidation reuses the two existing oracle tests (published vectors and literal template digests) as its self-check; no new assertion that checks the table against itself.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- test_role_protocol.py (AUTHOR_ROLES comment): "the sizes stay distinct up to 100 roles of the same variant" is misleading, because the test uses 128 roles. `r / 100` stays below the step of 2 up to 199 roles; the claim should say so or drop the number.
- test_studio_roles.py self-test (the three `{**valid['role-state'], 'roles': [...]}` constructions in the refused, accepted and at-limit blocks): the same message-building expression appears three times in one method; a one-line local helper would remove it. Not a rule 10 finding (one method, not three functions) but easy to tidy.
- test_studio_roles.py Studio `weight as a boolean` row: the over-state's `canonicalCss` is built by the test's `canonical_css`, which would render `True`; Studio would refuse it on the css mismatch even without its `typeof` check. The row therefore proves the table rule and Studio's refusal, but not that Studio's number-type check is the reason. Acceptable for a drift check; no change needed.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every requirement is implemented as briefed within the line budget; I reproduced eight table mutants, the bridge 1,023 cap and the builder mutant, and each is killed. The frozen worktree is byte-identical after my runs. Only Minor polish remains. The 1,024-signature test is the one place hosted Linux could time out (800 ms of a 2,000 ms budget on Windows); the report discloses it and Firefox is unverified.
