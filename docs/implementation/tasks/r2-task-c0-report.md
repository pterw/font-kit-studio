# R2.C0 code report (task c0, MODE code)

Recorded by the controller from the implementer's final reply.

**Status:** DONE_WITH_CONCERNS. Mode `code`, task c0, BASE `6af29325ac2ee0512b2a53266cf54a3bc8118f8d`, worktree `C:/fks/tc0`. Nothing committed; the three files are staged by name.

**Patch:** `C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/task-c0-code.patch`. It is 3 files (`tests/role_contract.py` new, `tests/test_studio_roles.py`, `tests/test_role_protocol.py`), LF only, and `git apply --check -R` passes in the worktree. No product code changed: `fontkit-bridge.js` and `fontkit-studio.html` are byte-identical to BASE.

**Gates:**
- Focused gate on the staged tree: `Ran 127 tests in 142.125s`, `OK`, `GATE focused EXIT 0 IN 142s`. At BASE the same command gave 112 tests, OK, so the 15 new tests are the whole difference.
- `ruff` on the three files and `git diff --cached --check` both pass.
- `python -m pre_commit run --files <3 files>`: whitespace and ruff passed; the js-syntax and static-check hooks had no matching files.

**Concerns:**
1. **Known drift (D070).** Studio drops a Detect reply whose `SelectorCheck` has more than 128 signatures; the table says 1,024. The Studio half of `CHECK_SIGNATURES` is red at BASE, so it is out of the patch and in the Handoff as R2.S3's RED test. The bridge half is in the patch.
2. **Size.** The staged diff is 708 insertions and 32 deletions (740 changed lines) against the brief's 450; see Deviations 1.
3. **Weak existing pin.** The `too many shared classes` row in `test_exact_hostile_shapes...` sends one class name 17 times, so Studio's duplicate rule refuses it even with the cap removed. The mutant `group.sharedClasses.length > 17` survives that test but is killed by the new `reply` test.
4. **A second drift, found in review.** Studio checks only the total of 96 losses per outcome, not 16 for each property (`LOSSES_PER_PROPERTY`). It is decided (Addendum 20, D071: Studio enforces 16) and handed to R2.S3 with its failing test; see "Fix round 1". Every other row of the table agrees with both sides.

## What changed

**`tests/role_contract.py`** (new, 255 lines):
- 36 limits with a source comment each, the enums, `NUMBER_RULES`, `STUDIO_SIDE_ONLY` (11 entries) and six builders.
- `wire` and the checker `violations(kind, message)` for `detected`, `roles-applied`, `rejected` and `role-state`; an unknown kind raises.
- The five literal `TEMPLATE_CASES`. I recomputed their bytes and digests with an independent script and they match the brief's Appendix B: `bf7cd581`, `3842c27b`, `a06c14e7`, `b623dd3c`, `9672a774`.

**`tests/test_studio_roles.py`**:
- Imports `role_contract as table`.
- 20 one-line replacements in the seven named tests, with no change of value.
- New class `StudioContractTableTests`, 9 tests (4 browser-free, 5 browser).

**`tests/test_role_protocol.py`**:
- Imports `RoleSheetCase` and `role` from `test_role_stylesheet`, as `test_role_detection.py` does.
- Three JS page builders.
- New class `RoleContractTableTests(RoleSheetCase)`, 6 tests.

## Inventory (Appendix A, updated)

Key: SR `test_studio_roles` (BASE lines), RI `test_r2_integration`, RS `test_role_stylesheet`, RP `test_role_preview`, RD `test_role_detection`, RPr `test_role_protocol`. New in this task:
- **SC** is `StudioContractTableTests`, with tests `input` (RoleInput through a ready snapshot), `reply` (detected-reply fields), `g128` (128 and 129 groups), `near` (127 near duplicates) and `outcome` (outcome counts).
- **RC** is `RoleContractTableTests`, with tests `scan`, `group`, `sigs`, `max`, `stale` and `loss`.

| Row | Studio (limit / past) | Bridge (limit / past) |
|---|---|---|
| ROLES 128 | detected SC g128, SR:349-381, 622-642 / SC g128; snapshot SC input, SR:1113-1131, 1322-1374 / SC input | apply RC max, RP:473-530 / RC max (129), RS:304; groups RC scan, RD:305-370 / RC group, RD:305-370 |
| SELECTORS 32 | detected SR:607-620 / SR:571; RoleInput SC input both | apply RC max, RS:438-465 / RS:302; emitted binding RC scan / not offered (the guard is unreachable; mutant `BW-selectors` survives everywhere) |
| SELECTOR_CHARS 2000 | SR:607-620 / SR:569; RoleInput SC input both | apply RS:384-397 / RS:354; emitted RC scan / past pinned by RS |
| NTH_MAX 9999 | SR:570, 607 | RS:347, 393; emitted not built |
| ROLE_ID_CHARS 100 | group id SC reply both; RoleInput SC input both | RC max / RS:298; RD:344, RPr:221 |
| NAME_CHARS 200 | suggested name and author name SC reply both (past also SR:581); RoleInput SC input both | RC max, RP:495-530 / RS:299 |
| SAMPLE_CHARS 200 | SC reply both (past also SR:553) | RC scan, RC group (a 300-char text is cut to 200) |
| SHARED_CLASSES 16 | SC reply both; SR:554 does not pin the cap alone (Concern 3) | RC scan (19 candidates, 16 sent) |
| CLASS_CHARS 200 | SC reply both | RC scan (200 kept, 201 dropped) |
| VARIANTS 8 | SC reply both | RD:305-370; RC sigs |
| NEAR_DUPLICATES 127 | limit SC near; past implied by 128 groups and unique ids | RC scan |
| CHECK_SIGNATURES 1024 | **limit RED at BASE** (R2.S3 test); past 1025 refused | RC sigs (136 signatures); the full 1,024 is not built |
| SELECTOR_CHECKS 4096 | gap (needs a 4,096-selector request and a roughly 600 KB reply; past implied) | RC scan (4,096 checks), RPr:10-40 |
| ELEMENTS 10000 (complete) | limit SC reply / SR:544, 576 | RD:305-370 |
| ELEMENTS_INCOMPLETE 10001 | SC reply both | RD:349-350 |
| TIME_BUDGET_MS 2000 | limit gap / SR:575 | RD:305-370; every complete reply in RC is checked |
| CHECKED 10000 | limit SC outcome / SR:1064, 1281 | RP:532-559, RS:239-260 |
| mismatched, loss count | limit SC outcome; loss count past SC outcome; mismatched past implied | RP:532-559 |
| LOSSES 96 and 16 per property | total SR:1271-1287; per property **drift** (not checked by Studio; RED test handed to R2.S3, D071) | RC loss (17 winners give 96 entries, 16 per property), RP:418-493 |
| WINNING_SELECTOR_CHARS 2000 | SR:1227-1251 / SR:1073-1078 | RP:193, RP:56 |
| NAMED_SELECTOR_CHARS | n/a | RP:443-471 |
| REQUEST_ID_CHARS 200 | n/a | RC max, RS:384-397 / RS:349 |
| DOCUMENT_ID_CHARS 200 | limit gap / SR:440 | n/a (the bridge makes a short id) |
| ROUTE_CHARS 2000 | RI:76-109 / SR:443, 1040 | RPr:66-98 |
| FAMILY_CHARS 300 | draft SR:755; snapshot SC input both | RC max / RS:332, RI:237 |
| NUMBER_RULES | draft SR:731-775; snapshot SC input (8 limits, 8 steps past) | maxima RC max / RS:308-318; minima at the limit: gap |
| REQUEST_BYTES 256 KiB | over only SR:622-642, 1113-1131; exact boundary gap. Studio's Apply probe uses the placeholder id `fks-req-000000`, so it refuses a few bytes before the bridge. This is not drift. | RC max (128,113 bytes, within); over RS:360, RPr:232-233; exact boundary gap |
| REPLY_BYTES 1 MiB | SR:644-669, 1340-1374 | RPr:10-40, RP:473-530 |
| CSS_BYTES 128 KiB | SR:1322-1337 | RS:438-465 |
| EMPTY_HASH | SR:694-700 | RPr:66-98, 196-243 |
| Rejection details | SR:1254-1268, 1437-1472, 1475-1496; RI:444-463 | RC stale (detail exactly `{baseRevision: 7, revision: 0}`), RI:444 |
| Enums | binding reason, stable flag and signature textTransform are new in SC reply; the rest unchanged | RD:239-303, 550-577; RC checks every reply against them |
| TEMPLATE_CASES | self-checked browser-free in SC; consumed by R2.4 and R2.S3 | — |

The full table is in the scratchpad: `inventory-c0.md`.

## New tests: what each asserts, oracle, mutants

Every test has a Given/When/Then docstring whose Then is exactly its assertions. "Mutants" are counts of one-line mutants, each killed in its own subtest row.

| Test | Asserts | Oracle | Mutants |
|---|---|---|---|
| SC template cases | digest = FNV-1a32 of the CSS; CSS minus the `:root` blocks = the plain serialization; the blocks = the adapter variables, in role order | Addendum 17 literals; `fnv1a32` (published vectors); `canonical_css`; a three-line variable table in the test | 5, one byte of each case |
| SC builders | exact lengths and counts, distinct values, losses in the contract's order, 16 per property | literals; `PROPERTY_ORDER` and `LOSS_REASONS` from the table | 8 |
| SC checker | `[]` for a valid message of each kind; exactly one string for each of 44 single defects (the brief's five plus one per rule); an unknown kind raises | table names | 5 valid-side plus 44 defects |
| SC `STUDIO_SIDE_ONLY` | every key is a table limit and has a reason | `getattr(table, name)` | 2 |
| SC `input` | for 14 rows: the table finds 1 violation one past and 0 at the limit; one past shows the unsupported reason with Detect disabled; the limit shows its CSS with Detect enabled | table names, builders, `NUMBER_RULES`; `canonical_css` | 28 (widened and tightened per row) |
| SC `reply` | for 12 rows: 0 violations and the rows render at the limit; 1 violation and only the fence row after a refusal | table names, builders, enums | 23 |
| SC `g128` | 128 rows render on a fresh page; 129 groups are refused and the fence is the only row | `ROLES` | 2 |
| SC `near` | 128 rows render and the first lists all 127 | `NEAR_DUPLICATES` | 2 |
| SC `outcome` | 10,000 checked, 10,000 mismatched and a loss count of 10,000 render; a count of 10,001 is refused, then the fence receipt renders | `CHECKED` | 7 |
| RC `scan` | premises first: complete, 128 groups, 4,096 checks, 127 near duplicates, 32 selectors of 2,000 characters, 16 shared classes of at most 200, samples of 200; then no violation | table names | 14 with `group` |
| RC `group` | 129 styles are incomplete with `group-limit`, 128 groups, sample cut to 200; the scan stops before bindings | `ROLES`, `SAMPLE_CHARS` | (included above) |
| RC `sigs` | complete; the one check has 17 x 8 = 136 signatures (over Studio's 128); no violation | `VARIANTS` | 1 |
| RC `max` | request within 256 KiB; receipt, second-hello role state and the 129-role `invalid-message` rejection fit | `NUMBER_RULES` maxima and every other name | 12 |
| RC `stale` | rejection `revision-conflict` with detail exactly `{baseRevision: 7, revision: 0}` | literals | 1 |
| RC `loss` | 17 losing rules per property give exactly 96 entries, 16 per property, and 102 losing elements in total | `LOSSES`, `LOSSES_PER_PROPERTY` | 2 |

Measured with the final tree:

| Message | Bytes |
|---|---|
| scan reply | 602,032 (44 ms; request 31,394) |
| 129-style reply | 57,822 |
| signatures reply | 40,714 |
| maximal apply request | 128,113 |
| maximal apply receipt | 231,403 |
| maximal apply role state | 208,344 |
| maximal apply CSS | 79,360 |
| loss receipt | 9,034 |

The 15 new tests take 8.3 to 8.7 s together over three runs, all OK.

## Mutants

I ran 153 mutants, one single-match replacement each. 148 were killed in their own subtest row; 5 survived, all expected.

- **Editing:** Studio and `role_contract.py` mutants edit the file in the worktree and restore the original bytes in `finally`. Bridge mutants are served through `RoleBridgeCase.open(bridge_source=...)`, so `fontkit-bridge.js` is never edited.
- **Command:** `python <scratch>/mutate-c0.py <module>` runs `PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest -v <test id>` from `C:/fks/tc0`, in the foreground.
- **SHA-256, identical before and after every run:**
  - `fontkit-studio.html`: `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804`
  - `tests/role_contract.py`: `24d67e4b2ec1a725c9641a1be31183249eddeefffa2da969eb636e88776da6f9`
  - `fontkit-bridge.js` (never edited): `f0290569aac08b3486ae96e9debe33d44e37780239e3201bd49c7c288dc34adc`
- **Failing lines**, all in `tests/test_studio_roles.py` except the bridge group, which is in `tests/test_role_protocol.py`:
  - Template digest: 2282.
  - Builders: 2292-2310.
  - Checker: 2373, 2376, 2377.
  - `STUDIO_SIDE_ONLY`: 2385, 2386.
  - `input`: 2414 for a widened limit, 2417 for a tightened one.
  - `reply`: 2461 for tightened, 2472 for widened.
  - `g128`: 2487, 2493.
  - `near`: 2508.
  - `outcome`: 2532, 2540.
  - Bridge class: 317-323, 336, 350, 370, 377, 388, 404.
- **Full per-mutant list:** `mutants-c0-summary.tsv` and `mutants-table-c0.txt` in the scratchpad.

Survivors:
- `DR-complete-w`: the complete-scan row has no past side here; the existing `test_exact_hostile_shapes...` kills the same mutant.
- `OC-checked-w`: killed by the existing `test_outcome_limits_follow_what_the_bridge_can_send`.
- `ND-w` and `OC-mismatched-w`: equivalent mutants, since 128 near duplicates need 129 groups and `mismatched <= checked <= 10000` already bounds mismatched.
- `DR-shared-w-existing`: the weak pin in Concern 3.

I also ran widened bridge mutants (one past the limit) for the rows the page cannot offer a value past, against the new class and against the existing hostile-request table (`test_role_stylesheet.AtomicRejectionTests`). They survive in the new class and are killed by the existing table, except the unreachable emitted-binding guard:
- Killed by the existing table: selector length 2,001, role id 101, name 201, 33 selectors, family 301, request id 201, and the four number maxima.
- Survives everywhere: `unique.length > 32`, the unreachable guard (equivalent).

## Deviations from the brief

None changes a value of the table.

1. **Size above 450.** Table 255 (brief 210): the checker applies every rule the brief lists, plus 11 `STUDIO_SIDE_ONLY` entries. Studio class 275 (brief 100): 14 and 12 table-driven rows that each use the table oracle, plus the checker's 44-row defect table (about 55 lines). I kept that table because a checker rule with no defect row would be an untested branch; the brief asked for five rows. The controller can trim to five and accept untested rules. Bridge class 145 (brief 100): three page builders (about 30 lines) plus the premises. Step 4: 32 lines (brief 25).
2. The docstring cites Addenda 13-18, not 13-17: `CHECK_SIGNATURES` comes from Addendum 18 / D070.
3. The checker has no count rule for `nearDuplicateIds`. It requires the ids to be unique and to name other groups of the reply, which bounds the count at 127. A separate count rule could not be tested alone.
4. The checker has no `NAMED_SELECTOR_CHARS` rule. The constant stays in the table as bridge-only and is listed in `STUDIO_SIDE_ONLY`; a rule would need a 262,144-character receipt and nothing isolates it.
5. `SELECTOR_CHECKS` is reached on the bridge side (128 known roles of 32 selectors give 4,096 checks) although step 3 does not list it.
6. The scan page's 20 classes include one of exactly 200 characters beside the one of 201 (still 20 classes). Without it, a mutant that tightens the class filter survives.
7. New waits use an 8 s timeout (15 s for the 128-row renders), within the module's existing 4 to 15 s.

## Literal limits left in other Studio tests

They stay as they are.

The six the review names:
- `test_bounded_rows_collection_and_utf8_request_limit_are_visible` (128)
- `test_apply_refuses_a_request_over_256_kib...` (129, `256 * 1024`)
- `hostile_receipts` (`128 * 1024`, 2000, 10001)
- `test_ready_requires_exact_snapshot_and_supported_capability` (201, 2000)
- `test_a_winning_selector_is_bounded_text...` (1999)
- `test_the_collection_limit_disables_apply...` (128)

Found by an AST scan, not in the review:
- `test_keystrokes_validate_every_intermediate_value_and_the_documented_bounds` (300 and 301, the draft family rows)
- `sized_receipt` (`'\u754c' * 300` and a 1990 padding bound)
- `test_role_rejections_keep_the_preview_and_drafts_show_next_steps_and_are_never_retried` (the 200-character rejection detail cut, which is not a table limit)

## Handoff

**Commit subject:** `test: add the role contract table and its parity checks`

**Draft body (wrapped at 72):**
```
Studio and the bridge each check the role messages against their own
copy of the limits, so a field or limit that changes on one side can
drift from the other without a failing test.

tests/role_contract.py writes the binding contract's limits, enums,
rejection detail shapes and builders for values at each limit and one
past it down once, with a checker that reports every value of a message
outside the table and the Bootstrap 5 template bytes as literal cases
for the serializers that follow. Studio's tests now pin every limit that
no test held at the limit and one past it: RoleInput fields in a ready
snapshot, the fields and counts of a detected reply and outcome counts.
The real bridge is driven to its reachable extremes and every message it
posts is checked against the same table. The existing boundary tests
read the table instead of repeating its numbers.
```

**RED test kept out of the patch.** R2.S3 adds it to `StudioContractTableTests`; it goes green once Studio accepts 1,024 signatures.
```python
    @per_engine
    def test_a_selector_check_of_1024_signatures_renders_and_one_more_is_refused(self, engine):
        """Given a detected role and a pending Detect, when the reply's selector check carries 1,024 signatures, then the table
        finds no violation and the row renders; when it carries 1,025, then the table finds one violation and the reply is
        refused: the fence reply that follows is the only row on the page."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        for count, refused in ((table.CHECK_SIGNATURES, False), (table.CHECK_SIGNATURES + 1, True)):
            with self.subTest(signatures=count):
                request = self.pending(page, frame)
                check = {'roleId': 'role-1', 'selector': '.body-copy', 'matchCount': count,
                         'signatures': [{'style': style, 'count': 1} for style in table.styles(count)]}
                reply = self.reply(request, [group(name='Refused' if refused else 'Limit')], selectorChecks=[check])
                self.assertEqual(len(table.violations('detected', reply)), 1 if refused else 0)
                self.send(frame, reply)
                if refused:
                    self.send(frame, self.reply(request, [group(name='Fence')]))
                    page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Fence")', timeout=8000)
                    self.assertEqual(page.locator('#roleRows > li').count(), 1)
                else:
                    self.settle(page, frame)
                    self.settle(page, frame)
                    status = page.locator('#roleStatus').inner_text()
                    self.assertTrue(status.startswith('Detected'), status)
        self.assertEqual(errors, [])
```
Failing output at BASE (Chromium): the 1,024 subtest fails with `AssertionError: False is not true : Detecting text styles…` at `self.assertTrue(status.startswith('Detected'), status)`; the 1,025 subtest passes; `Ran 1 test in 1.242s`, `FAILED (failures=1)`. The scratch copy is `red-checksignatures-c0.log`; the file I ran is `redtest_c0.py`, and the method above has the 8 s timeout instead of that file's 5 s.

**Plan items done (tick R2.C0's four).** Item 2's documented exceptions are in the Inventory: `CHECK_SIGNATURES` Studio half (the RED test), the implied past sides of `NEAR_DUPLICATES` and `mismatched`, and no Studio test at the limit for `SELECTOR_CHECKS`, exact `TIME_BUDGET_MS`, `DOCUMENT_ID_CHARS` and the exact `REQUEST_BYTES` boundary. Item 4's drift is `CHECK_SIGNATURES`.

**Draft ledger event (product terms only):** "2026-10-17 | R2.C0 (PR B2, W0): `tests/role_contract.py` holds the contract's limits, enums, builders, a checker and the Addendum 17 template cases; `StudioContractTableTests` and `RoleContractTableTests` check both sides against it (15 tests, no product change). One drift, already ruled (D070): Studio refuses a selector check of more than 128 signatures; its RED test goes with R2.S3." No deviation entry is needed. Closure text for Concern 3: "the shared-class cap is now pinned by `StudioContractTableTests`; the old row also fails on a repeated name."

**For later tasks:**
- R2.4 extends `RoleContractTableTests` with the emitted-adapter check.
- R2.S3 adds the RED test above.
- Both add the `adapter` field to the groups built through `group(...)`.
- Landing gates: `focused` = `test_studio_roles test_role_protocol test_support`, `python -m ruff check .`, `git diff --cached --check`.
- I did not touch `C:/fks/tt2`.

Scratch evidence (outside the repository, not committed): `mutants-c0-summary.tsv`, `mutants-table-c0.txt`, `mutants-c0-final-{contract,studio,bridge,bridgewide}.log`, `focused-staged-c0.log`, `baseline-c0.log`, `red-checksignatures-c0.log`, `probe-c0.log`, `inventory-c0.md`.

## Fix round 1

Patch: `C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/task-c0-code-r1.patch` (whole patch against BASE, LF only, `git apply --check -R` passes in `C:/fks/tc0`). The reviewed patch's staged hash was `b8da945e...592ed6` as ordered. Still three files; `fontkit-studio.html` and `fontkit-bridge.js` unchanged. Now 721 insertions and 32 deletions (was 708 and 32; `tests/role_contract.py` is 256 lines, was 255).

**What changed per finding**
- **I1 (owner ruling 2026-10-17, "Studio enforces 16").** Studio's total-only cap (`outcome.losses.length > 96`, html:4355) accepts 17 loss groups for one property. The Studio test, written to the contract, is kept OUT of the patch and is in the Handoff with its failing output (below). Corrected Concerns: there are two drifts, both decided: `CHECK_SIGNATURES` (D070) and `LOSSES_PER_PROPERTY` (the ruling; R2.S3 adds the Studio check). Concern 4 "No other drift" now reads: every other row agrees. Inventory row "LOSSES 96 and 16 per property", Studio side: "per property not checked by Studio: RED at BASE, R2.S3 test (ruling 2026-10-17)".
- **M1, decided with evidence.** The `checked` and `outcomes` rules each got a defect row (`checked` = CHECKED+1 with matched at the same value, so only the cap trips; `outcomes` = ROLES+1 copies). The total `losses` rule was deleted: an outcome can exceed 96 entries only by breaking the per-property rule (6 properties x 16) or by naming a property outside `PROPERTY_ORDER`, which the loss-enum rule flags, so the total could never trip alone. The 17-for-one-property row still flags exactly one. The checker test now has 46 defects and its docstring says "a row for each rule the checker applies", which is true. Constant `LOSSES` stays (the builder and loss tests use it).
- **M2.** `STUDIO_SIDE_ONLY` gained `NUMBER_RULES` (minima) and `EMPTY_HASH` (empty role state), each with a reason.
- **M3.** The bridge-side host page (`tests/fixtures/bridge/host-roles.html`) does not expose posted bytes, but its `window.send` is reassignable, so the test wraps it (new `POSTED_BYTES` constant, 5 lines, in the test module) and reads the UTF-8 JSON size of the one message the apply posts: `table.wire(roles) <= posted <= REQUEST_BYTES`. It measured 128113 bytes, equal to the earlier reconstruction. The docstring says "as the bridge received it (the bytes its host page posts)". The reconstructed request dict is gone.
- **M4.** Renamed to `test_a_known_selector_over_136_styles_posts_a_check_of_136_signatures_the_table_allows`; the docstring says 17 x VARIANTS = 136 and no longer mentions Studio's 128.
- **M5.** The test builds the set of the table's limit names (upper-case int or str, not bool) plus `NUMBER_RULES` and asserts each key with `assertIn`; the docstring says so.

**Mutants** (one-line change, only the affected test, file restored in `finally`, script `c0r1-mut.py`; SHA-256 before and after identical: `tests/role_contract.py` `821f3771a1049c4868e5ed47995eadfd8b25c20756d9b724db6dc1392bff6458`, `tests/test_role_protocol.py` `cda33a97202570f3bea1e37083e4e5e8b29bb1f4924d6aa6494d84ad181241a0`, `fontkit-studio.html` `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804`):

| Hunk | Mutant | Result |
|---|---|---|
| M1 `checked` row | delete the `checked` cap rule | test_studio_roles line 2378 `AssertionError: 0 != 1` (defect='checked') |
| M1 `outcomes` row | `ROLES` -> `ROLES + 1` in the count rule | line 2378 `0 != 1` (defect='outcomes') |
| M5 | key `NUMBER_RULES` -> `CASES` | line 2388 `'CASES' not found in {...}` |
| M2 | key `EMPTY_HASH` -> `EMPTY_HASHES` | line 2388 `'EMPTY_HASHES' not found` |
| M3 bound | `REQUEST_BYTES` 256 KiB -> 100 KiB | test_role_protocol line 378 `False is not true : [128113]` |
| M3 wrapper | recorded size `* 0` | line 378 `False is not true : [0]` |
| M1 deleted rule | none possible (rule removed); the kept `loss` row (17 for one property) still flags exactly one | covered by that row |
| M4 rename | no behaviour change; the renamed test passes in the focused run | n/a |
| I1 test (out of patch) | fix demo: html `losses.length > 96 ||` per-property count `> 16` (restored) | the RED test goes `Ran 1 test ... OK` |

**Focused output.** `sh .../tools/gate.sh focused test_studio_roles test_role_protocol test_support`: `Ran 127 tests in 139.086s`, `OK`, `GATE focused EXIT 0 IN 139s` (log `focused-c0r1.log` in the scratchpad). `python -m ruff check` on the three files: All checks passed. `git diff --cached --check`: exit 0.

**Whole patch's changed lines:** `tests/role_contract.py` +256; `tests/test_role_protocol.py` +154; `tests/test_studio_roles.py` +311 -32.

**Updated Handoff.** Commit subject unchanged: `test: add the role contract table and its parity checks`. Draft body: the earlier one plus this paragraph before its last sentence:
```
Two limits the table holds are not yet enforced by Studio, both decided:
a selector check of up to 1,024 signatures (D070) and 16 loss groups
for each role and property. Their Studio tests wait for R2.S3.
```
Ledger event: "two drifts, both decided: `CHECK_SIGNATURES` (D070) and `LOSSES_PER_PROPERTY` (owner ruling 2026-10-17, Studio enforces 16); both Studio RED tests go with R2.S3."

RED test 1 (CHECK_SIGNATURES) is unchanged, above. RED test 2, which R2.S3 adds to `StudioContractTableTests` (scratch file `redtest_c0r1.py`):
```python
    @per_engine
    def test_an_outcome_of_16_losses_for_each_property_renders_and_17_for_one_property_is_refused(self, engine):
        """Given an Apply in flight, when the receipt's outcome carries 16 loss groups for each of the six properties, then the
        table finds no violation and the counts render; when an outcome carries 17 for one property, then the table finds one
        violation and the receipt is refused: the fence receipt is what renders and the refused one never does."""
        rows = {'16 for each property': (outcome(matched=7, checked=7, losses=table.losses(table.LOSSES_PER_PROPERTY)), 'matched 7,', False),
                '17 for one property': (outcome(matched=8, checked=8, losses=table.losses(table.LOSSES_PER_PROPERTY + 1)[:table.LOSSES_PER_PROPERTY + 1]),
                                        'matched 9,', True)}
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        for label, (item, shown, refused) in rows.items():
            with self.subTest(row=label):
                request = self.apply_role(page, frame, '24' if not refused else '25')
                receipt = self.receipt(request, [item])
                self.assertEqual(len(table.violations('roles-applied', receipt)), 1 if refused else 0)
                self.send(frame, receipt)
                if refused:
                    self.send(frame, self.receipt(request, [outcome(matched=9, checked=9)]))
                page.wait_for_function('(text) => document.querySelector("#rolePreviewOutcomes").textContent.includes(text)', arg=shown, timeout=8000)
                if refused:
                    self.assertNotIn('matched 8,', page.locator('#rolePreviewOutcomes').inner_text())
        self.assertEqual(errors, [])
```
Failing output at BASE (Chromium, `red-losses-c0r1.log`): the `16 for each property` row passes; `(row='17 for one property', engine='chromium')` ERRORs at the wait for the fence receipt with `playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 8000ms exceeded.`, because Studio accepted the 17-loss receipt, which settled the request, so the fence receipt was ignored. `Ran 1 test in 9.364s`, `FAILED (errors=1)`. The Studio fix demo above turns it green.

## Controller integration

- Landed from `task-c0-code-r1.patch` (SHA-256 `ed1acd9b...74d5f2`), applied unchanged beside R2.T2's patch on the
  integrated W0 tree at `e2098ac`; no conflict (disjoint files).
- Review: Needs fixes (I1, M1-M5); fix round 1 resolved all six; the scoped re-review is Approved with one Minor (this
  report's Concerns item 4 and its LOSSES Inventory row still said "no other drift"), corrected in this record.
- I1 settled by owner decision: the 16 loss groups per role and property bind Studio too
  ([Addendum 20](../../plans/2026-10-03-r2-engine.md#addendum-20-loss-groups-per-property-2026-10-17), D071). R2.S3 adds
  the Studio check and lands this report's second Studio test with it, beside the `CHECK_SIGNATURES` test (D070).
- Landing gates, Windows, Chromium, `FKS_REQUIRE_FIXTURES=1`, both W0 patches applied: `test_studio_roles`, `test_support`
  and `test_release`, 137 tests in 130.603 s, OK; `test_role_protocol`, `test_r2_react` and R2.T2's three tests, 23 tests
  in 42.878 s, OK (the two runs side by side); static and provenance, `node --check`, product-tree Ruff and whitespace
  pass; exact Ruff reports only the four preserved findings under `.agents/`.
- Material lines: 721 added, 32 removed, in three test files (D065). Over the brief's 450, as Deviation 1 explains.
