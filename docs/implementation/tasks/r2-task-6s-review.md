### Spec Compliance
- PASS: Field lists consolidated. `ROLE_RECEIPT_KEYS` is gone; `ROLE_WIRE.detected/receipt/state.keys` are read at the four sites (fontkit-studio.html:4055, 4385, 4547, 4617) and `ROLE_WIRE.page` exists (3997). The old inline lists equal the shape keys. Nested lists were left as written, as the brief says.
- PASS: roles-page reader `acceptRolesPage` (4524-4531). It uses the tolerant copy (`readRoleReply`, so size, hostile keys and non-finite numbers are refused anywhere), requires identity, the same document, a count `>=` the identity version, `validRoleURL(.., true)`, and refuses the same version with another URL. It then runs `advanceRoleIdentity` and sends nothing. A null URL clears the rows and shows the unavailable text. `design:roles-page` is in `BRIDGE_TYPES` and the switch.
- PASS: drift against `tests/role_contract.py`. `TOLERANT_KINDS` has `'roles-page'`. `violations('roles-page', ..)` adds the pageVersion count and inherits the shared message-bytes, documentId and pageURL route checks (role_contract.py:221-230). F2 runs it through `with_unknown_keys`. The bridge posts exactly type, protocolVersion, sessionId, documentId, pageVersion and pageURL (fontkit-bridge.js:1347), the same keys as `ROLE_WIRE.page`.
- PASS: stale-but-valid Detect reply. The text at html:3750 equals the owner's wording in w2-carryovers.md byte for byte. The branch (4433-4435) clears the timer, sets `pending = null` and stores nothing. The test asserts the text after the reply and again after `run_for(9000)`.
- PASS: collection model (4130-4170). Checked against ruling 1 (reference styles counted per role across selectors), ruling 7 and Revision 2 I1.
  - Whole-candidate validation is present: ids <= 128, routes <= 32, selectors per role <= 32, styles per role <= 8.
  - The request estimate is padded to a 200-NUL documentId and the longest requestId, and tested with `safeRoleWire(.., 256 KiB)`.
  - A refusal stores nothing, consumes no id (nextId is assigned only on commit), sets `limitReached`, shows the exact text, keeps the rows and calls `compareEvidence` with the reply's identity.
  - `knownRolesFromCollection` is one function for the click and the candidate check, with no truncation.
  - The click-time refusal is kept (html:4373), per Revision 2 I1.
  - Revisit is `routes.set(key, fresh)`; refs only grow.
  - A new origin goes through `clearRoleCollection(false)`.
- PASS: texts. `ROLE_PAGE_CHANGED`, `ROLE_LIMIT` and the count sentences (singular and plural) match the brief.
- PASS: owned scope. The patch (identical to `git diff --cached` at the worktree) touches only the html ranges, `role_contract.py`, the new test module and the forced-edit test files. No CSS was added (M9). Budget: html 141 of 260; tests 480 new plus about 100 forced (71 + 21 + 8) of 650.
- PASS: forced edits F1-F8 are each justified by a ruling or the contract (see Check 3). The Handoff text in the report lists F1-F6 only; the landing must also name F7 and F8 (Minor 3).
- FAIL (Important 1): the `evidence?.changed` condition of brief step 3 (html:4529) has no behavioural test.

### Checks run
- Drift (item 1) -> read `role_contract.py` 150-300, `ROLE_WIRE` at html 3972-3997, bridge post at fontkit-bridge.js:1347 -> consistent (see Spec Compliance).
- Frozen worktree integrity -> `sha256sum -c` of `fontkit-studio.html` and `tests/test_role_routes.py` before and after all runs, and `cmp` of `git diff --cached --binary BASE` against `task-6s-code-a-r1.patch` -> OK and SAME. `git diff --cached --check` clean. All mutation ran on a copy under the scratchpad (`6sarv/wt`, hash-equal at copy time), restored in `finally`, and the copy's hash was re-verified after each run.
- Baseline on the copy -> `unittest test_role_routes` -> `Ran 17 tests ... OK` (21.7 s).
- Mutant M1, roles-page without the 1 MiB size limit (`safeRoleWire(raw, 1e12)`) -> hostile test -> FAIL, the first failing row is `one byte over 1 MiB` (status flips to the page-changed sentence). Killed, and the size row discriminates.
- Mutant M2, the candidate-request padding changed from 200 NUL to 200 `x` (breaks the worst-case bound of Revision 2 I1) -> `RequestBoundaryTests` -> FAIL (`Detected 100 roles` where the limit text is expected). Killed; the Python oracle with a 200-NUL documentId is independent of Studio.
- Mutant M3, stale reply without `clearTimeout` and `pending = null` -> stale test -> FAIL (`The page did not reply to Detect...` after `run_for(9000)`). Killed.
- Mutant M4, reference styles counted per selector instead of per role (ruling 1) -> `LimitTests` -> FAIL, subtest `9th reference style`. Killed.
- Mutant M5, knownRoles truncated to 127 -> `test_role_routes` plus `StudioRoleBoundaryTests` -> FAIL (`127 != 128`, F4's test). Killed; "no truncation" is pinned.
- Mutant M8, the page-changed status without `roleCollection.evidence?.changed` -> all of `test_role_routes` -> `Ran 17 ... OK`. SURVIVES. Probe (scratch `test_6sarv_probe`): after a stored Detect at version 0, a roles-page for version 0 and the same URL leaves "Detected 1 roles ..." with the real code, but the mutant shows "The page changed since the last Detect ...". That is a false claim. 6B1 says a roles-page may carry the version a Detect reply carries.
- Declared equivalent mutant -> reproduced a stronger variant than the report's (`raw: data.groups`, the untrusted message, assigned to a global and added to the snapshot) -> `test_a_reply_with_unknown_keys_outside_echoed_roles_renders_exactly_like_the_plain_reply` plus `CollectionTests` -> `Ran 5 ... OK`. Nothing reads the extra field, so it is unobservable through request bytes, the panel text or exports. Accepted as equivalent (ruling 4 and the Revision 2 cut of A9). The report named `reply.groups`, the tolerant copy, which is trivially safe; the real risk is `data.groups` and it is equivalent as well.
- Item 6 probes -> scratch probe on the copy ->
  - With a stored route: after a null roles-page (v1) and a supported one (v2), the status is the page-changed sentence and Detect is enabled.
  - With no stored route (ready, null page, supported page): the status stays "Role detection/preview unavailable: unsupported page URL." while Detect is enabled and the Apply gate shows its normal hint. See Plan-mandated.
- F1-F8 line-by-line compare -> read the patch hunks and the worktree files. Details in Check 3.
- Hidden skips and sleeps -> `grep skip|sleep|wait_for_timeout|time\.` in `test_role_routes.py` -> none. Waits are `wait_for_function`, `settle` (two animation frames) and `clock.run_for`.
- Third copy of logic -> read the patch. `roleTupleText` is shared by the row, the inventory lines and the labels. `knownRolesFromCollection` and `detectRequest` are single-sourced. The literal `256 * 1024` appears twice (click and candidate), which is not a third copy. `readRoleWire` shapes are single-sourced.
- Check 5, fake versus real -> the real bridge is used for navigation by link (`RealBridgeRouteTests`) and for the same-URL content change that produces a real roles-page (`RealBridgeSpaTests`), and F7 and F8 also run the real bridge. Peers are used only for replies a bridge never sends (stale, hostile, over-limit, 129th role, boundary). Appropriate.

#### Check 3, F1-F8
- F1 adds an `elif kind == 'roles-page'` case; nothing is removed. The later Detect uses version 1 because the roles-page moved the page to 1 (forced by Addendum 26 and the reader). The docstring change is the one the brief prescribes.
- F2 adds the dict entry and the 4-tuple; it only extends the pin.
- F3: the old assertions (status unchanged, Detect enabled, Apply `pageVersion` 0) are kept verbatim for the forged variant (wrong session id). The authenticated null notice adds new assertions. Nothing weakened.
- F4: one shared selector (140 KB) instead of two (270 KB, refused by ruling 7). The `role-128`, 128-row, `Collection limit`, reordered `role-1` and "only hello and detects" assertions are kept. The old "request limit" wait and `requests.length == 1` become `requests.length == 2` with 128 `knownRoles`. The sent list is hello plus 4 detects (Revision 2 I4). A stronger assertion replaces the old one.
- F5: the character-count guard is kept. The 100-role reply and its 100 `knownRoles` are kept. The 128-role reply now asserts the exact limit text and 128 rows, and Detect still sends (3 requests, 100 `knownRoles`). I checked the F5 sizes with Python's encoder: 128 roles with `'界' * 700` give a 274,668 B request (refused), and 660 gives 259,308 B (fits).
- F6: 660 instead of 700 characters keeps the Detect candidate under 256 KiB (259,308 B) so the route is stored. The Apply request (about 266.6 KB) still exceeds the limit, and the character-count guard, the `256 KiB` reason, the unselect-to-fit and the Apply-sends branches are kept. It differs from the brief's wording ("adapt exactly as F5") but preserves the test's purpose; it is a justified characterization edit.
- F7 and F8: every survival assertion (rows, role ids, preview, draft fields, height > 500, inert, scroll geometry, focus, re-Detect and author DOM) is kept. Only the status expectation changes: `changed = (PAGE_CHANGED, rows)` in F7, and the same tuple with the status element replaced in F8. The added `wait_for_function` waits on a condition (the status text), not on time. It is a wait, not an assertion, and it adds no mask: if the sentence never appears the test times out. The final `observations() == observed` after re-Detect in F7 is kept. Both follow D063 and the controller ruling.

### Strengths
- The 256 KiB boundary test builds its expected size with Python's own `json.dumps(..., ensure_ascii=False)` (independent oracle) and checks the stored side by value (`knownRoles == roles`). It would fail for the padding, the `+1` and the current-route-only mutants (M2 confirmed).
- The hostile roles-page table is broad (13 rows). Its size row is genuinely tied to the 1 MiB limit (M1).
- The real-bridge tests take their oracle from `expected-styles.json` and computed styles, not from Studio's data.
- Candidate validation is atomic: nothing is committed, no id consumed and nextId is untouched on refusal. Validation, state and rendering are in separate functions.

### Issues
#### Critical
None.

#### Important
1. **The `evidence?.changed` gate of the page-changed status is untested; a false "page changed" claim is possible** (html:4529; `tests/test_role_routes.py`). Brief step 3 says to show the sentence only `if evidence?.changed`. Mutant M8 (drop that condition) passes all 17 tests and `F1`/`F2`. The code is right today (probe: same version and URL after a stored Detect leaves "Detected..."), but nothing proves it, and the scenario is real: the 6B1 brief says a roles-page may equal the version a Detect reply carries or arrive after it. Without the gate Studio would tell the user the page changed when it did not. Add a test: stored Detect at version v, then a roles-page for version v and the same URL leaves the status and the inventory unchanged (and, optionally, no stored route plus a roles-page shows no sentence). The mutant is the dropped condition.

#### Minor
1. No test covers a roles-page that arrives with no identity (before a valid ready, or after a reset). Brief step 3 says "Invalid or no identity: ignored, no status". The guard is `identity && readRoleReply(...)` at html:4525, and dropping it would throw a TypeError at the next line. Add a one-case peer test.
2. The receipt shape is now one very long physical line (html:3993-3994, `receipt:roleShape([...], { roles:[...], outcomes:[roleShape([...` ). Wrap it for readability; the behaviour is unchanged.
3. The report's Handoff names the forced edits as F1-F6 (report lines 97-98), but the patch also holds F7 and F8 in `tests/test_r2_integration.py`. The landing text and Addendum 25's amendment must name all eight (and the two `role_contract.py` edits), or the commit body will not list every changed existing test.
4. `test_query_order_and_hash_make_separate_routes_in_first_visit_order`: the docstring says "each with #keep and #keep2", but the five paths are `?a=1&b=2`, `?b=2&a=1`, two with `#keep` and one with `#keep2`. The assertions are fine; reword the Given.
5. The hostile roles-page test shares state across rows, so after a first wrongly accepted row the later rows also fail (the report's concern 5). Each row's mutant is still caught by its own row, but a failure message names only the first row; nothing to fix beyond a comment in the test.

### Plan-mandated (for the owner)
- [Minor] After a null-URL roles-page, a later supported-URL roles-page leaves the status line at "Role detection/preview unavailable: unsupported page URL." when no route has been stored (html:4529; probe: Detect becomes enabled and the Apply gate uses its normal hint, but the text stays). With a stored route the sticky `changed` flag shows the page-changed sentence, so the common case is fine. This is not an implementer defect: brief step 3 says "Valid: ... with no Detect pending and a non-null URL, if `evidence?.changed` set the status ..." and gives no rule for the return from a null URL. Classification: a gap in the brief and contract (D061 and Addendum 5 name only the entry into the null state). The report disclosed it. Decide whether phase B/C should set the Ready sentence when the supported URL returns and the status is the unavailable text.
- [Minor] The click-time refusal `Role detection request limit reached.` (html:4373) is kept but unreachable (the padded estimate is an upper bound) and, after F4 and F5, no test pins it. Brief requires: "AND the existing click-time refusal `Role detection request limit reached.` stays (it is not deleted)" (Revision 2 I1). Dead and untested by design; the owner may drop it later.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Phase A matches the brief and the contract: field lists, tolerant roles-page reader, whole-route limits with the padded 256 KiB check, the stale wording, the forced edits (F1-F8 weaken nothing), and my five reproduced mutants were killed. One brief-stated condition, the `evidence?.changed` gate on the page-changed sentence, is covered by no test and the surviving mutant makes Studio claim a change that did not happen (Important 1). Fix that and the task can be approved.

## Review of phases A+B

### Spec Compliance
- PASS: Phase A items of task-6s-review-a.md and task-6s-followups.md are resolved.
  - A-I1: `test_a_roles_page_repeating_the_stored_page_says_nothing_and_a_newer_one_says_changed` (tests/test_role_routes.py:624) asserts the status and the Checked-on list are unchanged after a repeat roles-page, then the page-changed sentence after version 1. I reproduced the mutant `if (true) roleView.status = ROLE_PAGE_CHANGED` (the dropped `changed` gate): FAIL `'The page changed since ...' != 'Detected 1 roles ...'`.
  - A-PM1: html:4563 (`else if (roleView.status === ROLE_UNAVAILABLE) roleView.status = ROLE_READY`), const `ROLE_READY` is the same text as before (no new wording), the ready branch uses the const. Two subtests (no stored route -> Ready; stored route -> page-changed). Mutant (drop the `else if`) -> ERROR timeout in subtest 'no stored route'; reproduced.
  - A-PM2: the click-time refusal is unchanged and the report says it stays untested. PASS.
  - Minor 1: `test_a_roles_page_before_any_valid_ready_is_ignored`. Mutant `data = readRoleReply(...)` without `identity &&` -> FAIL, page error `Cannot read properties of null`; reproduced.
  - Minor 2: the receipt shape is wrapped over six lines (html diff 52-56). Minor 3: the report's fix round names F1-F8 and both role_contract edits. Minor 4: docstring Given now matches the five paths. Minor 5: comment at test_role_routes.py:699. All taken.
- PASS: Phase B state model matches the brief and the contract (checklist 1 below).
- PASS: the three phase A tests changed by the fix round (checklist 3 below) follow brief lines 94, 101, 219 and keep each test's intent; none is weakened.
- PASS: forced deviation B7. The brief's size-50 preview on `.shared-title` cannot prove the property; weight 900 on `[data-design-id="route.title"]` can (checks below). Recorded in the report with its reason.
- PASS: scope. Patch touches only the briefed html ranges, `tests/role_contract.py`, the new test module and the forced-edit test files. Budget: html +152/-28 (A+B budget about 400), new tests 715 (budget about 1,070) plus about 90 forced edits.
- FAIL (Important 1): two rules the brief states in Model 9 and B5 survive every test: `changed` applies only to the route equal to `evidence.key`, and `changed` outranks `conflict`.

### Checks run
- Frozen worktree integrity -> `sha256sum` of `fontkit-studio.html` (6e89358d...c60d), `fontkit-bridge.js` (44b6f54c...a13d), `tests/test_role_routes.py` (5e2cbc4b...6a) at the start and after every run, `git status --short` unchanged; `git diff --cached --binary BASE` equals `task-6s-code-ab-r1.patch` (`cmp` SAME) -> OK. All mutation ran on a `git checkout-index` copy under `scratchpad/6sabrv/wt`; the runner `6sabrv-mut.py` asserts the replacement count and restores bytes in `finally`; hashes re-verified.
- Baseline on the copy -> `unittest test_role_routes test_support` -> `Ran 60 tests in 45.5s OK`.
- Mutant M1 (A-I1, `changed` gate dropped, `RolesPageReaderTests`) -> FAIL as above. Killed.
- Mutant M2 (B7 drift: `sheet.disabled = true;` removed from the copy's `fontkit-bridge.js`, replacement count 1, `RealBridgeDriftTests`) -> FAIL `... found 1 x serif: 36px / 900 / none / -0.01em` vs expected `/ 700 /`. Killed.
- B7 deviation judged by probe (scratch test `test_6sabrv_probe`, deleted): the brief's literal variant (Apply size 50 on the title role, `#push-detail`, Detect) -> computed size after the push is `36px` with the sheet enabled, and the conflict line is `... found 1 x serif: 36px / 700 / none / -0.01em` on the real AND on the mutated bridge. Cause: `app.css` `[data-view="detail"] .shared-title` (0,2,0) outranks the preview (0,1,0). So the size variant cannot see the mutant; the weight variant (the detail rules set no weight) can. Also the real bridge offers `[data-design-id="route.title"]`, not `.shared-title`, for that role (the line in the test passes unmutated). Forced, and the weight version still proves "selector drift under an active preview cannot mask baseline drift": the unsuspended read would show 900; the test asserts the baseline 700 and `assertNotIn('900', inventory)`.
- Mutant M7 (stale late reply stored: `if (false) {` for the version guard, `LateScanTests`) -> FAIL (`Detected 1 roles ...` instead of the out-of-date sentence). Killed.
- Mutant M8c (both document guards of `acceptDetectedRoles` dropped) -> FAIL in subtest 'another document'. Killed. Each guard alone (M8a pending.documentId, M8b current.documentId) survives `LateScanTests` and, for M8b, all 103 `test_studio_roles` tests. I then probed the realistic case (a reload of the peer while a Detect is pending, then the old document's reply): both unmutated and M8b ignore it, because `resetRoleSession` clears `roleView.pending` on a new document. So the two guards are redundant defenses, not a hole. No finding.
- Mutant M9 (no-match counted as checked) -> FAIL in the precedence, four-state and revisit tests. Killed.
- Mutant M10 (append on revisit) -> FAIL in `test_a_revisit_replaces_the_route_and_keeps_its_place` and the four-state test. `RealBridgeSpaTests` still passes under it (Minor 3).
- Mutant M11 (ids per route) -> FAIL in `CollectionTests` (both tests). Killed.
- Mutant M12 (null URL does not mark changed) -> FAIL in the null-URL test and the 'a null URL' subtest. Killed.
- Mutant M5 (document clause of `compareEvidence` dropped) -> FAIL, subtest 'a reload'. Killed. Mutant M6 (version clause dropped) -> FAIL in 7 tests. Killed.
- Mutant M16 (`changed` not reset when a route is stored) -> FAIL in 5 subtests plus both real-bridge route tests. Killed.
- SURVIVOR M3 (`changed` and `conflict` swapped in `roleRouteState`) -> `Ran 26 tests OK`. See Important 1.
- SURVIVOR M15 (`changed = roleCollection.evidence?.changed`, the key check dropped, so every stored route turns changed) -> `Ran 26 tests OK`. See Important 1.
- SURVIVOR M4 (URL clause of `compareEvidence` dropped) -> `Ran 26 tests OK`. See Minor 1.
- SURVIVOR M13 (no `compareEvidence` after a refused Detect, html:4475) -> `Ran 26 tests OK`. See Minor 2.
- Real multi-page flow probe (index, article, conflict, index by link clicks, then print the inventory) -> the base-title role is `Checked on:` index and article and `Different style on:` conflict.html with `[data-design-id="route.title"]: expected serif: 32px / 700 / none / 0em, found 1 x serif: 40px / 600 / uppercase / 0.025em`. The state is real; the test (test_role_routes.py:1102) asserts only the checked lists (Minor 3).
- Hidden skips, sleeps, output -> `grep sleep|wait_for_timeout|skip|expectedFailure|time\.` in tests/test_role_routes.py -> none. Waits are `wait_for_function`, `settle` (two animation frames, used as short absence waits) and `clock.run_for`. `git diff --cached --check BASE` clean. Focused run printed no stray output.
- Third copy of a logic -> read the html diff -> `roleIdentityKey({ kind:"style", style ... })` is written three times (html:138 `styles`, and twice in `roleConflictLines`), see Minor 4. The tuple text, `knownRolesFromCollection`, `detectRequest` and `ROLE_ROUTE_TEXT` are single-sourced.

#### Checklist
1. Drift -> PASS.
   - States and precedence: `roleRouteState` (html diff 170-177) is changed > conflict > checked (a group, or a check with `matchCount > 0`) > no match, null when the role has neither group nor check. Equals Model 9; the order is only partly pinned (Important 1).
   - Evidence record `{key, documentId, pageVersion, changed}` set only on a stored route, compared in `advanceRoleIdentity`, the valid ready and a refused reply; cleared by `clearRoleCollection`. Equals Model 8 and the M5 narrowing.
   - Tuple format `roleTupleText`: `serif: 32px / 700 / none / 0em`; new lines use the literal ASCII `x` (`found 1 x ...`, `1 x ...`); the existing row keeps `×` (test_role_routes.py:790 asserts both).
   - Strings verbatim: `Checked on:`, `No match on:`, `Different style on:`, `Changed since checked:`, `<selector>: expected <tuple>[; <tuple>], found <count> x <tuple>`, page-changed, stale and limit sentences, all equal to brief/owner text.
   - Retained roles: the inventory iterates `roleCollection.labels`, so a role with no row on the current page is listed by its label (author name or tuple text); test at test_role_routes.py:976 asserts it.
   - Summary: `Checked on N visited page(s). Other pages have not been checked.`, singular for 1 (ruling 3), N = stored routes, unchanged by the changed state, hidden when none (ruling 8). The tests assert visited(1) .. visited(5).
2. Mutants -> see Checks run: A-I1 and B7 reproduced and killed; late-scan, no-match, append, ids, null URL, document and version clauses killed; four survivors named.
3. A -> B -> C late scan -> PASS. `LateScanTests` stores /a, leaves a Detect pending for /b, moves the page to /c at version 3 by a roles-page, then sends B's complete reply for version 2 (and one naming another document). The count stays 1, /a is `Changed since checked:` only, no `Late` role appears, and the status is the out-of-date sentence or the pending text. Killed by M7 (stale stored) and M8c (guards dropped). The realistic reload case is stopped by `resetRoleSession` clearing `pending`; probed above.
4. Fake versus real -> mostly PASS. Real Studio + real bridge: navigation by link clicks, SPA same-URL change (a real roles-page), and the drift test with a real preview and the real bridge. Peers are used for stale, hostile, over-limit, boundary and state-table replies, which a bridge never sends in those shapes. The peer `Changed` tests send roles-pages and reloads that a real bridge also produces; the real SPA test waits for the page-changed status but does not assert the `Changed since checked:` list (Minor 3).
5. Hidden skips none; every new test has a Given/When/Then docstring and the Then matches its assertions, with one wording gap (Minor 5); no fixed sleeps; budget within; validation (`storeRouteEvidence`), state (`roleCollection`) and rendering (`roleRouteState`, `renderRoleInventory`) are apart; one third-copy finding (Minor 4).

#### Checklist item: the three changed phase A tests
- `test_equal_styles_on_two_routes_keep_one_id_and_each_selector` (test_role_routes.py:744): only the data changes (`/two` passes `found={('role-1','.a'): [(22px,1)]}`) and the Given says so. The default peer check reports 16px for `.a` whose reference is 22px, a real conflict by brief line 101 (conflict outranks checked). Assertions are the same: one id, both routes in the checked list, both selectors in `knownRoles`. M11 (ids per route) still kills it. Not a weakening.
- `test_a_null_page_url_clears_the_rows_and_keeps_the_earlier_inventory` (:710): rows, Detect/Apply disabled, UNAVAILABLE text, visited(1) all kept; `pages == ['/peer']` becomes `listed == {'changed': ['/peer']}`. Brief line 94 and line 219 ("a null URL marks it changed") require the move; "keeps the earlier inventory" now means the route stays listed (under changed) and the count stays. Stronger, not weaker. M12 kills it.
- `test_a_revisit_replaces_the_route_and_keeps_its_place` (:826): data only (`found=only_x`, so Y is not found on /two or on the revisit); the original assertions (count 2, role-1 `['/one','/two']`, role-2 `[]`) are kept and `listed(role-2) == {'no-match': ['/one','/two']}` is added. Without the data change the default check makes Y "checked" by brief line 101. M9 and M10 both kill it. Not a weakening.

### Strengths
- The boundary and limit tests use Python's own encoder and literals as the oracle; the four-state tests use literal tuples, not Studio's data.
- B7 is a real-bridge test with a real preview and a mutant check (replacement count asserted), and the weight choice is justified by CSS specificity that I confirmed by probe.
- Candidate validation stays atomic: nothing is committed on refusal. The stale-reply and null-URL status wording are the exact owner/brief sentences.
- The fix round used two characterization tests that I reproduced as RED/GREEN-correct (A-I1 GREEN on the old tree; A-PM1 RED on A+B).

### Issues
#### Critical
None.

#### Important
1. **Two stated rules of the `changed` state are pinned by no test** (html:4205 `roleRouteState` `const changed = roleCollection.evidence?.changed && roleCollection.evidence.key === key; ... changed ? "changed" : lines.length ? "conflict" : ...`; tests/test_role_routes.py `ChangedStateTests`, `FourStateTests`). Model 9 says `changed` is "the route equals `evidence.key` and `evidence.changed`" and ranks changed above conflict. I reproduced two mutants that pass all 60 tests:
   - M15, drop the key check: every stored route becomes "Changed since checked" when the page moves. `ChangedStateTests` and `LateScanTests` use one route, so nothing sees it. A user who visited three pages would be told all three are out of date after one SPA click; the earlier, still true, evidence would be hidden.
   - M3, swap changed and conflict: a conflicting route whose page has since moved shows "Different style on:" instead of "Changed since checked:". Brief Model 9 puts changed first because the snapshot no longer describes the page.
   Fix: one peer test with two stored routes where the latest has a conflict and a roles-page with a higher version arrives: assert the earlier route stays under `Checked on:` and the latest is listed only under `Changed since checked:` (not under `Different style on:`). Mutants: M15 and M3.

#### Minor
1. **The URL clause of `compareEvidence` is untested** (`|| pageURL !== evidence.key`; M4 survives). The "another URL" subtest also raises the version, and `acceptRolesPage` refuses a same-version URL change, so the clause is reachable only through a ready or receipt. Add a valid ready with the same document and version and another URL (peer `ready_with(snapshot_state(pageURL=...))`), or drop the clause.
2. **`compareEvidence` after a refused Detect reply is untested** (html:4475; M13 survives). Model 8 names it. The case: a refused route for another URL (the 33rd route) must move the last stored route to `Changed since checked:`, with no roles-page sent. One assertion in the 33rd-route subtest of `LimitTests` would cover it.
3. **The real-bridge tests do not assert B's states they can produce.** `RealBridgeRouteTests` (test_role_routes.py:1102) checks only the checked lists, while the real flow gives the base-title role a `Different style on:` entry for conflict.html (probe above). `RealBridgeSpaTests` (:1118) no longer discriminates "append on revisit" after B: under M10 the old home-title role lands under `conflict` and `pages(...) == []` still holds. Assert `listed(...)` there (conflict for the old role; changed right after `#replace-same`).
4. **Third copy of the style identity key** in html: `roleIdentityKey({ kind:"style", style ... })` at `styles` (storeRouteEvidence) and twice in `roleConflictLines`, and the reference-set build is written twice. A `styleKey` helper would remove the third copy (constraints: a third copy is a finding).
5. **Docstring wording**: `test_a_moved_page_lists_the_route_as_changed...` says a new stored Detect restores the route; the 'a null URL' / 'a higher version' subtests do so through a roles-page then a Detect, which the docstring does not mention. Also `LimitTests` says "earlier lists stay" but asserts the earlier count and titles only after the refusal.

### Plan-mandated (for the owner)
None. The B7 deviation was forced, recorded and judged above; as a departure from the brief it is not plan-mandated. (The brief text "Apply a size (50) ... never 50px" cannot detect its own mutant on this fixture; the owner may want to correct the brief.)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Phase A items are resolved, the three adapted tests are legitimate, B7 and the A-I1 gate are killed by their mutants, and the late-scan guard holds. But the `changed` state's scoping to the latest route and its precedence over conflict are stated in the brief and survive every test (M15, M3), so a wrong claim about earlier pages could ship green. One small multi-route test fixes it.

## Review of phase C and the A+B follow-ups

### Spec Compliance
- PASS: AB follow-ups of task-6s-followups.md ("From task-6s-review-ab.md") are resolved.
  - AB-I1: `test_only_the_latest_route_turns_changed_and_changed_outranks_a_conflict` (tests/test_role_routes.py:613). I reproduced M15 (drop `evidence.key === key`): FAIL `{'changed': ['/one', '/two']} != {'checked': ['/one'], 'changed': ['/two']}`; and M3 (conflict ahead of changed): FAIL `{'checked': ['/one'], 'conflict': ['/two']} != ...`. Both killed.
  - Minor M4 (URL clause of `compareEvidence`): `test_a_ready_for_another_url_at_the_same_version_lists_the_route_as_changed` (:627). Mutant dropping `|| pageURL !== evidence.key`: FAIL `{'checked': ['/peer']} != {'changed': ['/peer']}`. Killed.
  - Minor M13 (`compareEvidence` after a refused reply): `LimitTests` 33rd-route subtest (:443) now asserts `/r31` under `changed`. Mutant removing the call: FAIL in subtest limit='33rd route'. Killed.
  - Minor 3 (real-bridge tests assert the lists they produce): :922-924, :938-945, :971-972 assert `listed`/`lines`; values checked in checklist 3.
  - Minor 4 (`roleStyleKey`): see the refactor check below. Minor 5 (docstrings): the Changed docstring (:579-582) now names the three ways a Detect is stored again; the Limit docstring (:433-436) says what is asserted. Both match their assertions.
- PASS: `roleStyleKey` is a pure refactor. `grep 'kind:"style"'` on the HTML finds only the helper (html:3818). The five former constructions now call it with the same style object: `validRoleVariants` (3826), `validDetectedGroup` (3850), `styles` in `storeRouteEvidence` (4181), `roleConflictLines` (4203, 4205). `.map(roleStyleKey)` passes (value, index, array) but the helper takes one parameter, so keys are identical. `diff` of task-6s-code-abc.patch against -abc-r1.patch: the only HTML hunks that differ are these five sites plus the helper line; the rest is line-number drift.
- PASS: Phase C matches the brief and contract (checklist 1).
- PASS: scope and budget. Phase C is +23/-2 HTML (120 allowed) and about 290 test lines (480 allowed); whole test_role_routes.py is 1,033 lines (budget about 1,550); `git diff --cached --check 2b70e29` clean; ruff clean on the test file; no hunk outside the briefed ranges; the one extra edit (LIMIT_HINT constant) was marked "phase C rewords it" in phase B.
- FAIL (Important 1): Done-when "imported legacy JSON unchanged" and brief C8 are not proven; the legacy test never imports (checklist 2).
- FAIL (Important 2): the brief's explicit guard "when `roleView.origin` was non-null" (html:4080) is not pinned by any test (mutant C5 survives all 41 tests).

### Checks run
- Frozen worktree integrity -> `sha256sum` and `git status --short` in C:/fks/t6sc at start and end, and `git diff --cached --binary 2b70e29 | cmp - task-6s-code-abc-r1.patch` -> SAME; html a3938c56...dd42, test_role_routes.py 5d79d527...d78ddd, fontkit-bridge.js 44b6f54c...a13d, unchanged. All mutation ran on a `git checkout-index --prefix` copy under the scratchpad `6scrv/wt` (outside the repository); the runner `6scrv/mut6scrv.py` asserts the replacement count is exactly 1 and restores the bytes in `finally`; it printed `SHA before == after: True` after every run.
- Baseline on the copy -> `unittest test_role_routes.ChangedStateTests` -> 3 tests OK; `unittest test_role_routes` (all 41) -> OK, before each survivor run.
- M15, M3, M4, M13 -> as above, all FAIL (killed).
- Mutant C1 (a new document that did not lose a preview keeps the old notice: `: ""` -> `: roleView.notice`) -> `test_role_routes` -> 1 FAIL, `test_pop_out_and_dock_keep_the_inventory_and_the_pop_out_shows_the_notice` (the dock must clear the notice). Killed; only that one test pins the "any other new document clears it" rule.
- Mutant replay (the not-applied branch also sends `design:roles-apply`) -> peer reload test + real-bridge reload test -> FAIL `['design:hello', 'design:roles-apply'] != ['design:hello']`. Killed: "no automatic replay" is observable on the peer.
- Mutant LEG (sync PUT body gets the route list appended, `body:css + "/* " + routes + " */"`) -> `LegacyOutputTests` -> FAIL (`'/*  */' != '/* http://target.test/hybrid.html */'`). Killed.
- SURVIVOR C5 (`if (roleView.origin !== null) roleView.notice = ROLE_NEW_ORIGIN;` -> unconditional) -> `unittest test_role_routes` -> `Ran 41 tests OK`. See Important 2. `grep roleNotice tests/` finds it only in test_role_routes.py, and every `notice == ''` assertion there (:672, :693, :714, :720, :762, :999, :1011) is taken after a Detect click, which clears the notice, so the first-connect state is never observed.
- SURVIVOR C3 (`roleDrafts.clear()` removed from `clearRoleCollection`) -> `test_role_routes` OK. Not a finding: the origin case is the BASE behaviour pinned by test_studio_roles.py:862-880 (old origin's ticked draft must not show at the new origin), and for Clear visited pages (counter kept) a stale draft is unobservable because its id is never reissued.
- Declared equivalent mutant "drop `rolePreview.origin === live.expectedOrigin`" -> reasoned at source. In the same-origin branch (`roleView.origin === live.expectedOrigin`), `rolePreview.roles` is non-empty only after an `installAcceptedRoles` at this origin: every install sets `origin:live.expectedOrigin`; non-empty roles come only from a valid ready (which also sets `roleView.origin`) or a receipt/reset (needs `roleView.identity`, set only by a valid ready); an invalid ready at another origin installs empty roles. So the clause cannot change the outcome. Accepted as equivalent (Minor 1: dead clause).
- Declared equivalent mutants "javascript: origin-only / protocol-only" -> read `validRoleURL` (html:~3780): `["http:","https:"].includes(url.protocol) && url.origin === live.expectedOrigin`. `javascript:alert(1)` has origin "null" and protocol "javascript:", so each clause alone refuses it; the test fails only when both go (report). Accepted as equivalent.
- Probe (scratch test `test_6scrv_probe`, in the copy only) -> peer: apply 24px on Body, Clear visited pages, Detect, then Apply 30px on the new row -> after Clear the new row `role-2` is NOT ticked (role-1's draft is gone, `seedRoleDrafts` seeds only issued ids); the Apply request carries only `role-2`; the preview ends with `removed: 'Removed from the preview: Body.'`. See Plan-mandated 1.
- Hidden skips, sleeps, output -> `grep skip|sleep|wait_for_timeout|expectedFailure|time\.` in tests/test_role_routes.py -> none. Waits are `wait_for_function`, `settle` (two animation frames, used as short absence waits) and `clock`. Output pristine in the runs above.
- Hostile URL coverage -> `validRoleURL` read; `javascript:` and the 2,001-character path in `test_a_complete_reply_with_a_script_url_or_an_oversize_route_stores_nothing` (:773) with the 2,000-character control (stored). Foreign origin / credentials are in the existing hostile-shape table (test_studio_roles.py:586), as Revision 2 allows.
- New control -> `grep role-actions|roleClear` in other tests -> no test enumerates the button row; `.role-actions` is `flex-wrap: wrap` (html:790), and test_r2_integration.py:146 (`scrollWidth<=clientWidth`) is in the reported 65-test run.

#### Checklist
1. Phase C behaviour -> PASS, with evidence:
   - Not-applied notice only for a NEW documentId with accepted roles: html:4083-4084 (`else if (rolePreview.documentId !== state.documentId)` and `roles.length > 0 && !state.roles.length`). A re-hello (same documentId) skips the branch: test :681 first subtest (`rev = 1; ready()` then a roles-page, notice '', peer got only hello/detect/roles-apply) and second subtest (a shown notice survives `ready()`). C1 and a same-document variant (report) killed.
   - No automatic replay; explicit Apply required: :677 (`sent == ['design:hello']` after the reload) and the replay mutant above; real bridge :990 (author's weight 700 after `frame.reload`-style reload, then `apply_title` works again with the weight 900 and no notice).
   - SPA-held CSS remains: :1003 (weight still 900 after `#push-detail`, notice '' ; "notice on any roles-page" mutant killed per report).
   - Full reload (peer :667, real bridge :990); dock/pop-out: :1015 (the inventory titles and `visited(1)` survive both; the pop-out shows the author's weight and the notice, the dock clears it; C1 killed here).
   - Cross-origin refusal: :773 (script URL, 2,001-character path store nothing; control stored).
   - New origin resets the counter and shows the approved sentence, `roleView.origin` the only origin: `roleCollection` has no origin field (html:3760); the branch is html:4079-4082; :756 asserts NEW_ORIGIN, empty count and inventory, `Fresh (role-1)` at the new origin, and the same again on return. Caveat: the guard for the first-ever connect is untested (Important 2).
   - Clear visited pages: `clearRoleCollection(true)` keeps the counter (:793 `role-129`, :809 `role-2`), clears evidence and drafts, cancels the pending Detect (:828 late reply ignored, status READY), keeps the applied preview and sends nothing (:809 preview text equal, sent list unchanged), shows CLEARED (:818) and hides `#roleVisited`; button enabled before any Detect (:814). The legacy test (:844) additionally holds the inspector edit across Clear.
   - Apply-disabled hint verbatim: html:4345 equals brief 252-253; `LimitTests.refused` asserts it exactly (:429).
   - Owner-approved strings verbatim: NOT_APPLIED, NEW_ORIGIN, CLEARED, LIMIT_HINT in html:3756-3758 and 4345 compared character by character with brief lines 240, 245-246, 251, 252-253.
   - Notice lifetime: cleared by the Detect click (html:4415) and by `installAcceptedRoles` with `announce` (html:4045); never by a same-document ready. :724 pins the Detect click, the acknowledged Clear preview (still shown while only requested) and the acknowledged Apply.
2. Legacy outputs -> NOT proven (Important 1). `LegacyOutputTests` (:844) compares the three code tabs, their downloads, the JSON export and the Sync PUT body before and after three routes and Clear, with a saved inspector edit on the legacy fake target; the LEG mutant above shows it has teeth for those outputs. But the brief (C8) lists four things: "imported legacy JSON, saved overrides, code tabs and sync PUT bodies"; the Done-when says "imported legacy JSON unchanged". No test imports a legacy JSON while a collection exists. The existing import suites (test_studio_import_link.py, the task4 import tests in test_font_kit_studio_v011.py, test_studio_controls.py:256/353, test_live_integration.py:915-948/1713-1739) never populate the collection, so they cannot show that a populated collection leaves an import unchanged. The report's reason ("importing applies overrides to the target and shifts its revision") is not an obstacle: the comparison can be made against the state right after the import. Residual risk is low (the importer is untouched, `roleCollection` sits outside `resetSessionState`), which is why this is one Important with a small fix and not Critical.
3. Independent oracle -> PASS. The "probed literals" of the fix round are all derived from the fixture, not from Studio:
   - Tuples: `tuple_text(ORACLE[...])` from expected-styles.json `signatures` (base-title serif/32/700/none/0; conflict-title serif/40/600/uppercase/0.025; detail-title serif/36/700/none/-0.01; same-title cursive/24/500/none/0.015), which match app.css:5 (`.shared-title` 32px 700), :8 (`[data-page="conflict"]` 40px 600 uppercase 0.025em), :12 (`[data-view="detail"]` 36px -0.01em), :19 (`[data-view="same"]` cursive 24px 500 0.015em). The ASCII format `serif: 32px / 700 / none / 0em` is the brief's tuple text.
   - Selector `[data-design-id="route.title"]` (:923): the only value not in the oracle JSON (which lists `.shared-title`). It is derivable from the fixture HTML, which puts `data-design-id="route.title"` on the title h1 of every page (index.html:18, article.html:18, conflict.html:18, spa.html:28), and from plan line 516 ("Groups bound by `data-design-id` are style groups"); article.html's title has class `article-title`, which is why a `data-design-id` binding, not `.shared-title`, is the one that matches all pages. Accepted; a different bridge preference would fail the test visibly, not silently.
   - Routes and lists: base-title role checked on index and article, different style on conflict (app.css:8 vs :5); conflict-title role checked on conflict and different style on index; `unvisited.html` never listed; after `#replace-same` the SPA home role is `changed`, then `conflict` with the same-title role `checked` (spa.js `replace-same` renders view `same`); drift route key `spa.html?route=detail` (spa.js push-detail) and the detail tuple from the oracle. First-visit order index, article, conflict is the click order.
   - Weight 900 and the author's weight: `str(ORACLE['base-title']['fontWeight'])` and the computed style in the frame/popup (not Studio data).
4. Mutants -> M15, M3, M4, M13, C1, replay, LEG killed; C5 survives; C3 not a finding; equivalents judged above (rolePreview.origin clause and the two javascript: single-clause mutants are correctly declared equivalent). The report's own table (notice on any ready/roles-page, pop-out/dock clearing, dropped `roles.length`/`state.roles` conditions, Detect click and `installAcceptedRoles` keep the notice, origin mutants, Clear mutants, Json tab) was not re-run in full; the ones I re-ran agree.
5. Fake versus real; skips; Given/When/Then; sleeps; budget; layering -> PASS with Minors.
   - Real Studio + real bridge: reload, SPA push, pop-out/dock, link navigation, SPA replace, drift. Peers only where a bridge cannot send the shape (hostile and over-limit replies, hello without roles).
   - Every new test has a Given/When/Then docstring; Then equals the assertions except the small wordings in Minor 3. No fixed sleeps. Validation (`storeRouteEvidence`), state (`roleCollection`) and rendering (`roleRouteState`, `renderRoleInventory`, `renderDetectedRoles`) stay apart; the notice rule is five lines inside `acceptRoleReady` and has no second copy. Third copies: none in the HTML after `roleStyleKey` (`roleIdentityKey(group.identity)` x3 and `detectRequest` are single-purpose calls); two in tests, Minor 4.

### Strengths
- The AB-I1 test is a real two-route test with an independent expected dict; M15 and M3 fail on it with the exact list difference.
- The replay oracle (the peer's own `received` list after a real reload) is observable and needs no hook; the replay mutant fails it.
- The fixture literals of the real-bridge tests come from the oracle JSON and CSS, so the test cannot agree with a wrong bridge by construction.
- The Clear handler and `clearRoleCollection(true)` share one function with the new-origin path (`clearRoleCollection(false)`); the counter rule is one boolean and is pinned from both sides (:756 resets, :793 and :809 keep).
- The refactor is minimal and the full patch diff shows nothing else moved in the fix round.

### Issues
#### Critical
None.

#### Important
1. **Legacy-output test has no import step** (tests/test_role_routes.py:844-869; brief C8, plan R2.6S Done-when "imported legacy JSON unchanged"). The test proves the exports, downloads and Sync body are unchanged, but not that a legacy JSON import is unchanged by a session with visited pages and Clear; the existing import suites never hold a collection. Fix: in the same test (or a sibling), import a legacy JSON 0.1.1 file (e.g. the one the test's own JSON export produced, through `#importJsonFile` `set_input_files`) before any route, capture the exports and Sync body right after the import, run three routes and Clear, and assert byte equality again (keep the "after the routes" comparison). Mutant: the scratch Json-tab/Sync append already used.
2. **Untested guard: no new-origin sentence at the first connect** (html:4080 `if (roleView.origin !== null) roleView.notice = ROLE_NEW_ORIGIN;`; brief Phase C item 3 "when `roleView.origin` was non-null"; mutant C5 passes all 41 tests). Without the guard a user's first connect would read "visited pages from the previous origin were cleared" when there was none: a false claim. Fix: in `OriginTests` (:756) assert `self.notice(page) == ''` straight after the first connect, before the first Detect click (the click clears the notice, which is why every current `''` assertion is blind to this). Mutant C5.

#### Minor
1. Dead clause: `rolePreview.origin === live.expectedOrigin` (html:4084) cannot change the outcome (reasoned above, declared equivalent by the report). Keep as a defence or drop it; either way it is an untested clause by design.
2. Legacy test baseline is taken after one Detect (:852-857: `before` includes one stored route), not "before any Detect" as the brief says. It still catches appended output because Clear removes it (LEG mutant failed), but the docstring ("before" and "after") should say so, or the baseline should be taken before the Detect.
3. Docstring wording: `test_pages_visited_by_links...` (:903-907) says the index and conflict pages "render the oracle's literal styles", but only the index font size (:910) and the conflict text-transform (:915) are asserted. `test_the_notice_is_cleared...` (:725) says "Given the notice" but two of three subtests use the Clear-visited notice, not the not-applied one.
4. Two copies of the weight-900 apply flow and of the computed-weight expression in tests: `RealBridgeDriftTests` (:957-964, with a local `weight` equal to the `WEIGHT` constant at :28) and `RealBridgeNoticeTests.apply_title` (:978-987). Move `apply_title` to `RealBridgeCase` and use it in both.
5. `clearTimeout` in the Clear handler (html:4431) is inert in practice (the timer returns at once when `roleView.pending !== pending`, html:4422); removing it survives every test. Harmless; the brief asked for it.

### Plan-mandated (for the owner)
- [Minor] After Clear visited pages, a new Detect gives the same style a new id (the counter is kept) and the applied preview's role has no row or draft, so the next Apply replaces the preview and says "Removed from the preview: Body." (probe: peer, Apply 24px, Clear visited pages, Detect, tick role-2 and size 30, Apply: request carries only `role-2`, preview status `removed` set). The "applied preview ... stay" sentence is true until the next Apply; the user loses the edit handle for the applied values. (html:4153-4157; tests :809 pins the kept preview but not this continuation) -- brief requires: "`clearRoleCollection(keepCounter)` empties routes, refs, labels, evidence, `roleView.ids` and `roleDrafts`" and "Clear visited pages (C) calls `clearRoleCollection(true)`: it does not end the lifetime, so an accepted role's `role-N` is never reissued (ruling 5)". An owner decision: either accept it, or re-seed the drafts of preview roles after Clear (needs an identity-to-role link the brief does not store).

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The AB follow-ups are all resolved (M15, M3, M4, M13 killed; `roleStyleKey` is a pure refactor) and Phase C behaves as the brief and contract say, with independent fixture oracles. Two Importants remain: the legacy-output test never imports a legacy JSON (brief C8 and the Done-when), and the first-connect guard of the new-origin sentence survives every test (mutant C5, a false claim to the user). Both are small test additions.

## Scoped re-review 1

### Spec Compliance
- PASS: C-I1 legacy import. `test_an_imported_legacy_json_is_the_same_with_three_visited_pages_and_after_clear` (tests/test_role_routes.py:922) imports the literal `LEGACY` 0.1.1 JSON (:872) through `#importJsonFile` `set_input_files` (`import_legacy`, :894) in a plain and a held session (three routes), asserts the status, code tabs, downloads, JSON export and Sync body are equal between the sessions (:937), equal again after Clear (:940), that the import changed the tabs (:935) and that the held session still reads three pages (:936). Pre-import exports are asserted equal across the sessions as the control (:932). The counter-based `crypto.randomUUID` (`COUNTED_IDS`) is identical in both sessions, so it makes slot ids comparable and cannot hide a difference in the collection's output (mutants below).
- FAIL (Important 1): the test does not kill two collection-touching import mutants that are observable through the next Detect (see Issues).
- PASS: C-I2. `OriginTests` waits for Ready and asserts `#roleNotice` empty right after the first connect (:1289-1290 of the patch, test_role_routes.py:759-761); the guard-dropping mutant fails it (Checks).
- PASS with FAIL (Important 2): "Keep their IDs". `clearRoleCollection` (fontkit-studio.html:4155-4162) keeps ids and labels only for roles in `rolePreview.roles`, clears routes/refs/evidence/drafts, leaves the counter alone on Clear; the new-origin call keeps nothing. Pinned for Clear; "a new origin keeps nothing" with an applied preview is not pinned by any test.
- PASS: the fix round changed nothing else (hunk list in Checks).

### Checks run
- Frozen worktree integrity -> `git status --short` and `sha256sum` in C:/fks/t6sc -> five staged files as reported, html 1b03bbd0...a725; never edited. All mutation ran on a copy in the scratchpad `6srr-copy` (html, bridge, tests, fixtures/multi-page only); runner `6srr-mut.py` asserts one replacement and restores bytes in `finally`; it printed `restored 1b03bbd0` after every run.
- Baseline on the copy -> `unittest test_role_routes.LegacyOutputTests OriginTests ClearVisitedTests` -> Ran 8 OK.
- Patch diff r1 vs r2 (`diff task-6s-code-abc-r1.patch task-6s-code-abc-r2.patch`), every hunk: (a) fontkit-studio.html `clearRoleCollection`: comment, `applied`/`kept`/`labels` lines, restore loop (the other html hunks differ only in line-number offsets and the index hash); (b) tests/test_role_routes.py: import adds `hybrid_page`; docstring of the notice-lifetime test (Minor 3); `OriginTests` docstring plus the first-connect wait/assert (C-I2); Clear test renamed, docstring and last two assertions (owner ruling); new keeps-their-IDs test; `LegacyOutputTests` gets `LEGACY`, `ROUTES`, `COUNTED_IDS`, `edited`, `visit_routes`, `import_legacy`, the first legacy test reshaped (baseline before any Detect, Minor 2) and the new import test; `apply_title` moved from `RealBridgeNoticeTests` to `RealBridgeCase`; links-test docstring (Minor 3); drift test uses `apply_title` and `WEIGHT` (Minor 4). Nothing else in any other file.
- C-I1 teeth -> mutants on the copy, `LegacyOutputTests`: import status appends `roleCollection.routes.size` -> FAIL (`...reselected.3 != ...0`); `showExport` appends the route keys -> FAIL in both legacy tests; clear collection AND re-render after import -> FAIL (`'' != 'Checked on 3 visited pages...'`). Killed.
- Declared survivor "import clears the collection without a re-render" -> mutant `clearRoleCollection(true);` after `const incoming = data.composition;` -> committed `LegacyOutputTests` OK (survives). Observable: scratch test `test_6srr_after_import_next_detect` (held session, import, then Detect of `/r3` with the hero group plus an `Other` group) is OK on real code (knownRoles `[role-1, hero.lead]`, `Checked on 4 visited pages`, titles `Body (role-1)`, `Other (role-2)`) and FAILS on the mutant (`[] != [{'id': 'role-1', 'selectors': ['[data-design-id="hero.lead"]']}]`; page count 1; titles `Body (role-2)`, `Other (role-3)`). So the report's "nothing visible until the next render" is the whole point: the stale DOM (:936) is what the test reads.
- Declared survivor "import bumps nextId" -> mutant `roleView.nextId++;` there -> committed tests OK (survives); same scratch test FAILS (`['Body (role-1)', 'Other (role-3)'] != [..., 'Other (role-2)']`). The counter is an output: the role-N ids of a later Detect's rows and Apply request. The report's "the counter is not an output" is false.
- C-I2 -> mutant `if (roleView.origin !== null) roleView.notice = ROLE_NEW_ORIGIN;` -> `roleView.notice = ROLE_NEW_ORIGIN;` -> `OriginTests` -> FAIL (`'A new Live App origin started a new colle[55 chars]red.' != ''`). Killed.
- Keep their IDs, mutants on `ClearVisitedTests` + `OriginTests`: applied set always empty -> FAIL (`[] != [{'id': 'role-1', 'selectors': []}]`, both Clear tests); keep every mapping -> FAIL (`[role-1, role-2] != [role-1]`; overflow test too); counter reset on Clear (`roleView.nextId = 0` unconditional) -> FAIL (`['Other (role-1)']`, and overflow `Fresh (role-1) != Fresh (role-129)`); labels not kept -> FAIL (`['Other (role-3)'] != ['Body (role-1)', 'Other (role-3)']`). Killed.
- New origin keeps nothing -> mutant `new Set(rolePreview.roles.map(...))` (ignores `keepCounter`) -> `ClearVisitedTests` + `OriginTests` -> Ran 6 OK (survives). Scratch `test_6srr_new_origin_after_apply_keeps_nothing` (apply a preview on origin A, connect origin B with a different documentId, Detect Body): real code OK (`knownRoles == []`); mutant FAILS (`[{'id': 'role-1', 'selectors': []}] != []`, origin A's role id sent to origin B). Note for the fixer: the peer at B must carry a different documentId, or `acceptRoleReady` drops its ready (fontkit-studio.html:4070, `data.revision < rolePreview.revision`); that is a fixture matter, not a defect of this change.
- Counter pinned elsewhere after the renamed test dropped `role-2` -> `test_after_clear_visited_pages_the_applied_role_keeps_its_id_and_other_roles_get_new_ones` (Other is role-3, role-2 not reused) and `test_clear_visited_pages_after_an_overflow_lifts_the_limit_hint_and_enables_apply` (role-129); both fail under the counter-reset mutant. The renamed test is a characterization update to the ruling, not a weakening: it now asserts the stronger `knownRoles == [{'id': 'role-1', 'selectors': []}]` and `Body (role-1)`.
- Minor 1 / Minor 5 not taken -> brief line 249 ("timer cleared") and the review's own Minor 1 text ("Keep as a defence or drop it; either way") -> both reasons sound.
- Output / skips -> no new sleeps or skips in the diff; `init=` option of `open()` pre-exists (tests/test_studio_roles.py:127).

### Strengths
- The import test compares two live sessions byte for byte rather than against literals, so it cannot agree with a wrong importer; the status-suffix and export-suffix mutants fail it with exact diffs.
- The keeps-their-IDs test pins five things at once (only the applied id kept, other mapping dropped, counter not reused, drafts re-seeded so Apply carries role-1 at 24, no Removed line); four mutants of `clearRoleCollection` fail it.
- C-I2 is a one-assertion fix that kills the guard mutant.

### Issues
#### Critical
None.

#### Important
1. **Two import mutants survive although the next Detect shows them** (tests/test_role_routes.py:922-941; C-I1 "the import touches or drops the collection"). Both "import clears the collection without a render" and "import bumps nextId" pass the committed tests and fail a Detect after the import (Checks). The assertion at :936 (`visited_text(held) == visited(3)`) reads a DOM the mutant never re-rendered. Killing assertion: in the held session, after the import and before Clear, visit a fourth route (`/r3`) with `group(selectors=HERO_LEAD)` plus a new group; assert the request `knownRoles == [{'id': 'role-1', 'selectors': ['[data-design-id="hero.lead"]']}]`, `visited_text == visited(4)` and titles `['Body (role-1)', 'Other (role-2)']` (the same Detect in the plain session would need no collection; compare to literals). The "surviving" status in the report is wrong for both; they are observable.
2. **"A new origin keeps nothing" is not pinned once a preview is applied** (fontkit-studio.html:4156; tests/test_role_routes.py:757 `OriginTests`). The Keep-their-IDs change made the new-origin call depend on the `keepCounter` flag to avoid carrying the previous origin's applied ids. Ignoring the flag (mutant above) leaves all 6 Clear/Origin tests green, yet origin B's first Detect then names origin A's `role-1` in `knownRoles`: evidence crossing origins, which this feature exists to prevent. `OriginTests` never applies a preview before switching (applied set empty either way). Fix: in the origin test (or a sibling), apply a preview on A, connect B (different documentId), Detect, assert `knownRoles == []` and the first role is `role-1` from B's own counter reset.

#### Minor
1. The parameter is still named `keepCounter` (fontkit-studio.html:4155) although it now also decides whether applied mappings and labels are kept; a rename (for example `keepApplied`) or one comment sentence would stop the next reader missing that the new-origin call also relies on it.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** C-I2 and the Keep-their-IDs behaviour are correct and well pinned for Clear, and the fix touched nothing else; but the import test misses two collection-touching mutants that the next Detect exposes (the report calls them unobservable, which is wrong), and "a new origin keeps nothing" has no test once a preview is applied. Both are small test additions.

## Scoped re-review 2

### Spec Compliance
- PASS: Important 1 closed. The import test now ends with a Detect of /r3 in the held session after the import and before Clear (tests/test_role_routes.py, test_an_imported_legacy_json_is_the_same_..., r3 lines 1481-1484). Both mutants fail it (see Checks).
- PASS: Important 2 closed. New OriginTests.test_a_new_origin_keeps_no_role_of_an_applied_preview (r3 lines 1304-1317).
- PASS: Minor closed. keepCounter is now keepAppliedIds at all three sites (fontkit-studio.html:4155, 4156, 4161); no keepCounter remains (grep); behaviour unchanged.
- PASS: the fix changed nothing else. diff of r2 vs r3 patches has exactly these hunks, nothing more: (1) html index line; (2) html rename, 3 lines in clearRoleCollection; (3) test_role_routes.py index/size line; (4) new test in OriginTests; (5) import-test docstring; (6) import-test 4 added lines (request, knownRoles, visited(4), titles).
- PASS: Given/When/Then of both tests equal their assertions. Import docstring: fourth route Detect names only role-1 with hero lead selector, counts four pages, lists Body (role-1) and Other (role-2) = the three added assertions. New-origin docstring: different document id, no known roles, Other (role-1) = documentId, knownRoles, title assertions. No fixed sleeps in the added lines.
- PASS: expected values follow from the test's own data, not the code. The held session visits ROUTES (3 routes, each group(selectors=HERO_LEAD)), so role-1 holds exactly the hero lead selector; /r3 repeats that group (matches role-1) and adds Other, which is the second identity, role-2; 3 + 1 = visited(4). In the origin test the applied role is role-1, and the other origin starts at zero, so Other is role-1 with no known roles.

### Checks run
- Import mutant "clearRoleCollection(true) after const incoming = data.composition" -> copy of the frozen tree at scratchpad 6srr2-copy (outside the repo), mutate html, run the import test on chromium -> FAIL: `[] != [{'id': 'role-1', 'selectors': ['[data-design-id="hero.lead"]']}]`.
- Import mutant "roleView.nextId++ at the same place" -> same method -> FAIL: `['Body (role-1)', 'Other (role-3)'] != ['Body (role-1)', 'Other (role-2)']`.
- Real code -> import test + OriginTests (4 tests) -> OK.
- Flag-ignoring mutant `new Set(true ? rolePreview.roles.map...` -> OriginTests on the copy -> FAIL only test_a_new_origin_keeps_no_role_of_an_applied_preview: `[{'id': 'role-1', 'selectors': []}] != []`. The other two OriginTests pass.
- Does the test really connect a second origin with a different documentId? -> read the test: switch_to('http://evil.test/peer', PEER with 'peer-document' replaced by 'other-origin-document'); it asserts request['documentId'] == 'other-origin-document' (it would fail on a no-op replace), knownRoles == [], and title 'Other (role-1)' (the restarted id).
- Rename sites -> grep keepCounter|keepAppliedIds in the frozen html -> only keepAppliedIds, 3 lines, calls at 4081 (false) and 4438 (true) unchanged.
- Patch isolation -> diff r2 vs r3 patches -> hunks as listed above.
- Focused runs in C:/fks/t6sc (FKS_ENGINES=chromium, FKS_REQUIRE_FIXTURES=1): `test_role_routes test_support` Ran 78 OK; `test_studio_roles test_support` Ran 137 OK; `test_r2_integration test_live_integration.SyncAndReloadTests test_studio_import_link test_support` Ran 111 OK.
- The frozen worktree was not edited (git status unchanged: M html, role_contract, test_r2_integration, test_studio_roles; A test_role_routes). Mutants lived only in the scratch copy (my mutation script normalised CRLF in the copy only; irrelevant to the result).

### Strengths
- Both import mutants that survived r2 now fail with messages that name the observable difference (known roles, row id), so the test pins "import neither clears the collection nor bumps the counter".
- The new-origin test uses a distinct documentId, so it exercises the origin branch and not the same-origin document branch.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
None.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** All three findings are fixed with tests that fail under the named mutants and pass on the real code; the round changed only the rename and the two test edits, and the three focused runs are green (78, 137, 111).
