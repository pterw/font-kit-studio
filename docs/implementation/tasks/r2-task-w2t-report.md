# R2.W2T code report (mode: code, base 73b3ba2b, worktree a scratch worktree)

Patch: `task-w2t-code.patch` (4 files, 114 insertions + 61 deletions = 175 gross, under the 190 budget; tests only; `git apply --check -R` passes).
Files: tests/role_contract.py, tests/test_studio_roles.py, tests/test_role_protocol.py, tests/test_r2_react.py.

## Per requirement (all done; nothing deferred except bookkeeping in Handoff)
1. Detected adapter: `need(group.get('adapter') in ADAPTERS, ...)`; docstring reworded (KeyError except `adapter`). Self-test rows `bootstrap9`, `None`, key removed. Three inline re-assertions deleted in RoleContractTableTests (one-style, one-variant, bootstrap5 tests); the variant test renamed `..._and_the_reply_still_fits_the_table`, the bootstrap5 test `..._posts_a_reply_the_table_allows_with_a_group_that_is_not_plain`; Thens reworded to what they assert; `adapters` kept for the non-plain assertion.
2. Header names Addenda 13-18 (17: template bytes; 18: signatures per check), 20 and 22 (families), and UTF-16 units.
3. 1,024 signatures: test at old 376 replaced and renamed `test_a_known_selector_over_the_most_styles_posts_a_check_of_the_signature_limit_the_table_allows`; builder `[table.ROLES, table.VARIANTS]`, sizes `r / 100`; asserts complete, `(len(groups), max signatures) == (ROLES, VARIANTS)`, one check `('k', CHECK_SIGNATURES)`, no violation.
4. `chars()` counts UTF-16 units (`sum(2 if ord(c) > 0xFFFF ...)`), numbers refuse `bool`. Self-test rows: astral name x101, id x51, `fontWeight: True`; loop-side pass at 100/50 astral. Studio limits-test rows added: `name in UTF-16 units` (100 / 101 astral) and `weight as a boolean` (1 / True).
5. Families: `FAMILY_KEYWORDS`, `FAMILIES_REFUSED` (grouped, engine note each), `FAMILIES_ACCEPTED` (10 near misses), module function `family_refused` (one-pass quote scan); applied only to `str` in the fontFamily branch. Self-test loops over both tuples plus a non-string family row (one violation, no raise).
6. `fnv1a32` in the table; `test_studio_roles.py` and `test_r2_react.py` bind `EMPTY_HASH, fnv1a32 = table...` and drop their copies. `test_role_stylesheet.py` untouched.
7. Literals replaced: 361, 366, 371 (ROLES), 445 (DOCUMENT_ID_CHARS), 448 and 1045 (ROUTE_CHARS), 760 and 1316 (FAMILY_CHARS), 1055 (CSS_BYTES), 1069 (CHECKED), 1078 and 1240 (WINNING_SELECTOR_CHARS), 1123/1126/1127/1936 (ROLES, REQUEST_BYTES), 422 (EMPTY_HASH). Stayed: 1319, 1474-1476, 362 (`* 1050`), the `700` selector size. `NAMED_SELECTOR_CHARS` and its STUDIO_SIDE_ONLY row removed. Self-test docstring "46" is now "53" (41+3+4 rows + 5 control rows).
8. React: docstring, `OWNED` and the locator use `style[data-fontkit-role-styles]`; `import role_contract as table` added.

## RED first (rows against the unchanged rules, table data present, rules absent)
`python -m unittest test_studio_roles.StudioContractTableTests.test_the_checker_passes_...once` -> `FAILED (failures=25)` (work/red-w2t.log):
defects `adapter`, `adapter null`, `adapter missing`, `name in UTF-16 units`, `role id in UTF-16 units`, `boolean weight`, and all 19 `refused=` families. The 10 `accepted=` near misses, the astral-at-limit case and `family that is not text` passed (expected: nothing refused them, and `chars()` already flags a non-string). GREEN after the rules: StudioContractTableTests `Ran 11 tests OK`.

## Mutants (foreground; stale-.pyc hazard removed with PYTHONDONTWRITEBYTECODE=1 and tests/__pycache__ deleted, after a same-size same-second mutant had reused a cached module; the reported runs are the clean ones)
role_contract.py SHA-256 before and after every run: `fb96c0acd2e72237815fbc82ae934b9417fb138e2b74fdc07e589baca04f68b0`.
Test T = `StudioContractTableTests.test_the_checker_passes_a_valid_message_of_each_kind_and_flags_each_single_defect_once`.
- M1 adapter rule off -> FAIL defects `adapter`, `adapter null`, `adapter missing`.
- M1b `group['adapter']` -> ERROR on `adapter missing` (KeyError).
- M2 `len(value)` for units -> FAIL `name in UTF-16 units`, `role id in UTF-16 units`.
- M3 bool accepted -> FAIL `boolean weight`.
- M4 no `lower()` -> FAIL refused `INHERIT`, `Revert-Layer`. M5 no `strip()` -> FAIL refused `'  inherit  '`.
- M6 keyword by prefix -> FAIL accepted `Initialism, serif`, `Inherit Sans`, `inherited`, `revert-layers`. M6b substring -> same plus `"inherit"`.
- M7 any quote counts as inside -> FAIL refused `"Inter", --x(a)`, `--x("a")`. M7b quotes ignored -> FAIL 5 accepted (`'Inter (Display)'`, `"Inter (Display)"`, `"A)"`, `"Inter's (x)"`, `'say "hi" (x)'`).
- M8 `(` only -> FAIL refused `Inter)`, `a), serif`. M9 drop the `isinstance(str)` guard -> ERROR on `family that is not text`.
- M10 fnv multiplier 16777618 -> FAIL `FnvVectorTests.test_the_digest_helper_matches_the_published_fnv1a_vectors` and all five cases of `test_template_cases_follow_the_addendum_rules_and_carry_their_own_digests` (the 2469 digest assertion).
- L2/L3 (real Studio): M2 and M3 each fail `test_role_input_limits_are_refused...` at rows `name in UTF-16 units` and `weight as a boolean`.
- B1 builder `r / 10` (test_role_protocol.py SHA before/after `df7e225a...e6c3`) -> FAIL on the new assertion.
- B2 bridge-side: copy of the bridge in memory (no file edit; repo bridge SHA `a7e81ca1...9a5f` unchanged) passed as `bridge_source`, capping a check at 1,023 signatures -> FAIL `[('k', 1023)] != [('k', 1024)]` (work/mutbridge-w2t.py).

## 1,024-signature test timings (Windows Chromium)
elapsedMs 785, 793, 801 (reply 468,167-468,181 bytes, 44.6% of REPLY_BYTES; budget 2,000 ms). Three more while `gate.sh shard-2` ran (plain-bridge-runtime tests, light browser load): 760, 801, 834. Neither limit passed. Firefox is not verified for this test (the review measured `time-budget` near 2,003 ms in 7 of 9 runs; the gate forces Chromium, D037). Hosted Linux may be slower: a `time-budget` there is a finding, not a reason to loosen the assertion.

## Gates
Focused: `sh .../gate.sh focused test_studio_roles test_role_protocol.RoleContractTableTests test_r2_react test_support` -> `Ran 140 tests in 402.418s`, `OK`, `GATE focused EXIT 0 IN 419s`, 0 skips (run on the final tree; later edits were mutants, each restored byte-exact). `python -m ruff check` on the four files: All checks passed. `git diff --cached --check`: clean. `python -m pre_commit run --files ...`: whitespace and ruff Passed, node/static Skipped (no files).

## Deviations / notes
- Test method renames (variant test, bootstrap5 test, 1,024 test) follow brief 1 and 3. The self-test's `family that is not text` row is an addition beyond the brief's list, covering the type guard (M9).
- Line endings: working files are CRLF (autocrlf); the patch is LF-normalised by git.
- Stray file `index` made by a shell redirect in my own mutant echo was deleted; scratch scripts are in git-ignored `work/`.

## Handoff
- Commit subject: `test: check adapters, UTF-16 lengths and families in the contract`
- Draft body: The contract table did not check a detected group's adapter, counted
  characters as code points where both sides count UTF-16 units, accepted
  booleans as numbers and had no family rule. It now checks all four,
  names the D072 family cases as data for the bridge and Studio tests,
  holds the one FNV-1a32, and the real bridge is driven to a
  1,024-signature check. Test modules read their limits and digest from the
  table instead of repeating them.
- Plan: tick R2.W2T; correct its Owns line for `tests/test_studio_roles.py` (constants, literals, self-test, limits rows, not "table imports only"). R2.W2S edits `test_studio_roles.py` after this patch; R2.W2B1 switches `test_role_stylesheet.py` to the table's `fnv1a32` and `EMPTY_HASH` and takes family cases from `FAMILIES_REFUSED`/`FAMILIES_ACCEPTED` (never `generic(kai)` to kill a mutant).

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
