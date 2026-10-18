# R2.6S code report

## Phase A (mode: code, worktree C:/fks/t6s, BASE 2b70e29, patch `task-6s-code-a.patch`)

Patch files: `fontkit-studio.html` (+115/-26), `tests/role_contract.py` (+5/-3), `tests/test_role_routes.py` (new, 480),
`tests/test_studio_roles.py` (+44/-27). Budget: html 141 gross (budget 260), tests 480 new + 71 forced (budget 650). Reverse
apply check passes. Nothing committed.

### Status: DONE_WITH_CONCERNS (two existing tests outside F1-F6 fail; see Concerns)

### Per brief step
1. Field lists: done. `ROLE_RECEIPT_KEYS` deleted; `exactRoleFields` reads `ROLE_WIRE.detected/receipt/state.keys` at the four
   sites; `ROLE_WIRE.page` added. Mutant (report only): dropping `cssHash` from `ROLE_WIRE.state` fails
   `test_ready_requires_exact_snapshot_and_supported_capability` (16 errors, valid ready refused).
2. Stale-but-valid reply: done (exact owner text, timer cleared, `pending = null`, nothing stored).
3. roles-page reader `acceptRolesPage`: done, plus `BRIDGE_TYPES`, the switch case, `ROLE_WIRE.page`, `compareEvidence` inside
   `advanceRoleIdentity`.
4. Old request generation: GREEN characterization (first half of the test passes at BASE; the second half is RED there).
5-8. Collection, identity, route keys, replacement, limits, 256 KiB boundary: done (`storeRouteEvidence`, `buildRouteSnapshot`,
   `knownRolesFromCollection`, `detectRequest`, `clearRoleCollection`, `roleTupleText`, `renderRoleInventory`, `#roleVisited`,
   `#roleInventory`). The click-time refusal `Role detection request limit reached.` is KEPT (Revision 2 I1).
9. Cut (Revision 2). Equivalent mutant recorded below.
10-11. Real bridge: done (`RealBridgeRouteTests`, `RealBridgeSpaTests`; harness as briefed, no fixture edit).
Forced edits: F1 (roles-page case in `tolerant_session`; its later Detect uses page version 1 because the roles-page moved the
page to 1), F2, F3 (renamed `test_a_null_url_page_notice_disables_detect_and_apply_and_a_forged_one_changes_nothing`), F4 (sent
list is hello + 4 detects), F5, F6 (selector `'界' * 660`: Detect candidate 259,292 B fits, Apply request 266,593 B does not, 88
roles 183,295 B fit; computed with Python's encoder), and `role_contract.py` (`TOLERANT_KINDS`, `violations('roles-page')`).
Not done / deferred: nothing of phase A. No CSS added (the wrap test is GREEN with the existing `overflow-wrap:anywhere`, M9).

### RED at BASE (new tests; `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_routes`, log work/red6sa.log)
`Ran 17 tests ... FAILED (failures=13, errors=7)` (the real-bridge links test errored first on a `go` wait that I then
simplified; after the fix all 17 fail or error except the characterization half of the old-request test). Quoted:
- `AssertionError: '' != 'Checked on 5 visited pages. Other pages have not been checked.'` (route keys)
- `AssertionError: 'Detected 2 roles from 2 eligible text par[49 chars]ked.' != 'Collection limit reached; this page was not stored'` (limits)
- `AssertionError: 0 != 1 : ('serif: 32px / 700 / none / 0em', [])` (SPA real bridge: no inventory)
- `playwright TimeoutError` waiting for the stale / page-changed / unavailable statuses (stale, roles-page, null tests)
Forced tests at BASE: F5 `AssertionError: 'Detected 128 roles ...' != 'Collection limit reached; this page was not stored'` (RED);
F1 roles-page case TimeoutError (RED); F4, F6, F2 pass at BASE (characterization GREEN).

### GREEN
`test_role_routes test_support`: `Ran 51 tests in 36.703s  OK`.
`test_studio_roles test_r2_integration` (132 tests, 209 s): `FAILED (failures=2)`, the two below; everything else OK.

### Mutants (on-disk, foreground; fontkit-studio.html SHA-256 before = after in every run: 6e4182e2...e37f3)
BASE sha ac75c7fb...298b; final sha 6e4182e21f4bab5ae2ccc219a388b8ba58b1ca7e5419de106f04be222b4e37f3. Logs work/mut{A..F}_6sa.log.

| mutant | test that fails |
|---|---|
| stale: restore BASE silent `return` | stale test (status stays "Detecting text styles..."; ERROR on the wait) |
| stale: keep status, drop timer clear and `pending = null` | stale test (FAIL after run_for(9000)) |
| roles-page: skip `advanceRoleIdentity` | valid roles-page (apply pageVersion) |
| roles-page: status written over a pending Detect | pending-text test |
| skip document check / drop `>=` / foreign origin / skip same-version URL check / skip session check / skip hostile-key scan | hostile test, first failing row named: another document / an older version / a foreign origin / the same version with another URL / another session / a __proto__ key (later rows fail because the accepted message taints the shared state) |
| null URL refused | null test; also F3 test |
| roles-page strict keys | valid (unknown-key variant) and F1 tolerant test |
| drop `requestId` equality | old-request test |
| knownRoles from shown rows | equal-styles test |
| fresh id on every reply (remap) | reorder test |
| fold author-name case | case/Unicode test |
| no variant lines | variants test |
| sort query / drop hash | route-keys test (both) |
| label `white-space: nowrap` | wrap test at 1440 and 390 |
| revisit merges groups (append) | revisit test and SPA real-bridge test |
| 33 routes / 129 ids / 33 selectors / styles per selector / store anyway | limits test (the matching subtest each; store-anyway also F5) |
| compare with REQUEST_BYTES + 1 / current route's roles only | boundary test |
| validate by string length | F5 test |
| every route under every role | links real-bridge test |
| **equivalent:** snapshot also keeps `reply.groups` raw (`raw:` field) | none: `OK` for the tolerant test and the unknown-key variant. Reason: the tolerant copy already holds only listed keys and nothing renders, sends or exports the extra field; no observable differs, so no test is weakened for it (A9 is cut). |

### Gates
`python -m pre_commit run --files fontkit-studio.html tests/role_contract.py tests/test_studio_roles.py tests/test_role_routes.py`:
whitespace Passed, ruff Passed, node syntax Skipped (no .js), static checks Passed (after removing two unused imports found on
the first run). `git diff --cached --check`: clean. Not run (dispatch): full suite, Firefox, frontend gate, hosted CI.

### Concerns (reported, not edited)
1. Two existing tests outside F1-F6 fail because the real bridge now sends a roles-page after a viewport change (D063: fullscreen
   resizes the iframe) and Studio shows the page-changed sentence where the tests expect `Detected 2 roles ...`:
   `test_r2_integration.StudioRoleBridgeTests.test_fullscreen_with_a_populated_preview_keeps_its_height_inert_panel_and_observations`
   (line 722) and `StudioRoleIntegrationTests.test_fullscreen_preserves_roles_and_preview_height_through_escape` (line 45):
   `AssertionError: ... 'The page changed since the last Detect; p...' != 'Detected 2 roles from 2 eligible text par...'`. The new
   text is the brief's required behaviour; the controller must authorize a forced edit (the status element of `observations()`).
2. Evidence record semantics (M5): intended as stated in the rereview: the flag lives on the latest stored route; an incomplete or
   null-URL Detect reply does not call `compareEvidence` (only the refused reply and `advanceRoleIdentity` do); `resetRoleSession`
   does not mark it changed.
3. M6: the 128-roles Apply hint keeps the BASE wording ("Role collection limit reached (128 roles), so Apply is disabled.") for
   every overflow until phase C; tests pin it as `LIMIT_HINT`.
4. Not implemented (not in the brief): when a roles-page restores a supported URL after a null one, the status line keeps
   "Role detection/preview unavailable" until the next Detect or ready, although Detect becomes enabled. Phase B/C may want it.
5. The hostile roles-page test shares one armed state across rows, so after a first accepted message later rows also fail; the
   first failing subtest names the mutant's row.

### Handoff (for the landing)
- Subject: `feat(studio): keep session-only visited-page role evidence`. Body draft: Studio keeps what each Detect found for every
  visited page in memory, so a revisit replaces the page's entry and roles keep their ids across pages; it reads the page's
  route-change note, says when a stored page may be out of date, and refuses a page that would pass the collection or request
  limits instead of storing part of it. Session only; nothing is saved or exported.
- Addendum 25's R2.6S row must name `design:roles-page` in `TOLERANT_KINDS` and the `violations('roles-page')` branch
  (`tests/role_contract.py`), and the forced edits F1-F6 in `tests/test_studio_roles.py`. Reword `role_contract.py` `STUDIO_SIDE_ONLY['REQUEST_BYTES']`
  (Studio now pins the exact boundary in test_role_routes); I left it untouched (outside owned lines).
- Deviations for the D-record: no totals rendered; no `generation` counter; new-origin sentence at first valid ready; click-time
  refusal kept (I1). Not run here: Firefox, frontend gate, hosted CI.
- Focused commands for the landing (A split, M4): `... unittest test_role_routes test_support` and `... unittest test_studio_roles
  test_r2_integration` (the latter fails on the two tests in Concern 1 until authorized).

## Phase A fix round 1

Mode: code. Forced characterization edits F7 and F8 in tests/test_r2_integration.py only (no product code).

Cause confirmed (scratch probe 6sar1, deleted): a viewport-only change (`#btnDeviceDesktop` click, no fullscreen) adds
`design:roles-page` (pageVersion 1) to the inbound log, and `#roleStatus` goes from `Detected 2 roles from 2 eligible text
pa...` to `The page changed since the last Detect; ...`. Log before: bridge-ready, ready, ready, detected:0; after: plus
roles-page:1. D063 working as written.

Edits: new module constant `PAGE_CHANGED` (brief sentence verbatim). F7 `StudioRoleIntegrationTests.test_fullscreen_preserves_
roles_and_preview_height_through_escape` and F8 `StudioRoleBridgeTests.test_fullscreen_with_a_populated_preview_keeps_its_
height_inert_panel_and_observations`: after fullscreen, wait by condition (`#roleStatus` text equals PAGE_CHANGED), then the
same observations assertions compare to the baseline with only the status element replaced (F7 `(PAGE_CHANGED, rows)`; F8
`(preview, PAGE_CHANGED, rows, fields)`). Rows, preview, fields, height, inert, scroll, focus, re-Detect and author-DOM
assertions are unchanged. Docstring Thens updated to say the status reads the page-changed sentence.

Evidence: both tests failed before (status mismatch only), pass after (`Ran 2 tests ... OK`).
Focused: `test_role_routes test_support` Ran 51 OK; `test_studio_roles test_r2_integration` Ran 132 OK.
pre-commit (python -m pre_commit; bare command absent): file hooks Passed/Skipped; ruff passed; `git diff --cached --check` clean.
Worktree files are CRLF (autocrlf, index LF); edit preserved CRLF, patch is LF-normalized by git.
Patch: task-6s-code-a-r1.patch (whole phase A vs BASE; fontkit-studio.html, tests/role_contract.py,
tests/test_r2_integration.py, tests/test_role_routes.py, tests/test_studio_roles.py); `git apply --check -R` passes.
task-6s-code-a.patch untouched. No mutation run: these are modified existing tests, not new behaviour.

# R2.6S phase B code report (mode: code, worktree C:/fks/t6sb, BASE 2b70e29 + phase A patch `task-6s-code-a-r1.patch`)

Status: DONE_WITH_CONCERNS (three phase-A tests in `tests/test_role_routes.py` now fail by design of B; not edited, see Concerns).
Patches: `task-6s-code-ab.patch` (whole, vs BASE; `git apply --check -R` passes) and `task-6s-code-b-only.patch` (phase B alone vs the
phase A tree; made with `git diff --binary` before staging). Files: `fontkit-studio.html` (+37/-8), `tests/test_role_routes.py` (+188/-8).
Budget: html 45 gross (budget 140), tests 196 (budget 420). Nothing committed.

## Per brief step
1. Snapshot `checks` (`buildRouteSnapshot`), the four-state inventory (`roleRouteState`, `roleConflictLines`, `ROLE_ROUTE_TEXT`,
   `renderRoleInventory`) and one `compareEvidence` in the valid branch of `acceptRoleReady`. All retained roles are listed, labelled
   from identity. Precedence changed > conflict > checked > no match; conflict compares every found signature against that selector's
   reference styles (never rewritten); one `<selector>: expected <tuple>[; <tuple>], found <count> x <tuple>` line per outside style.
2-4. States, precedence, retained role without a row: `FourStateTests` (3 tests). 5. Changed: `ChangedStateTests` (subtests: higher
   version, another URL, null URL, reload, pending Detect; each then restored by a new stored Detect). 6. Late scans: `LateScanTests`
   (older page version, other document). 7. Drift: `RealBridgeDriftTests`. 8. Cut by Revision 2.

## RED / GREEN
RED on the phase A tree (`work/red6sb.log`, `red6sb2.log`): `Ran 6 tests ... FAILED (failures=10, errors=1)`. Quoted:
`AssertionError: {'checked': ['/one']} != {'checked': ['/one'], 'no-match': ['/two'], 'conflict': ['/three']}` (states),
`{'checked': ['/peer']} != {'changed': ['/peer']}` (each changed subtest and both late-scan subtests), `KeyError: 'conflict'` (drift,
re-run on the index copy of fontkit-studio.html after the final test edit). Late-scan tests are RED only on the changed list; the guard
itself already held at A (characterization), and its mutants below prove the test.
GREEN: `FourStateTests ChangedStateTests LateScanTests RealBridgeDriftTests`: `Ran 6 tests ... OK`.
Command 2 `test_studio_roles test_r2_integration test_support`: `Ran 166 tests in 211.812s OK`.
Command 1 `test_role_routes test_support`: `Ran 57 tests ... FAILED (failures=3)` (the three in Concerns; all new B tests pass).

## Mutants (on-disk, foreground, `work/mut6sb.py`; fontkit-studio.html SHA-256 before = after = e507c04e...06ee every run)
| mutant | failing test |
|---|---|
| no-match counted as checked | precedence test, states test |
| compare only the first signature | states test (/four: 16px first, 20px second) |
| reference rewritten by the latest page (stands for "compare against the latest page") | states test |
| append on revisit (old checks kept) | states test (/three revisit stays different style) |
| list under every matching state | precedence, states, retained-role tests |
| inventory built from `roleView.rows` | retained-role, precedence, states tests |
| changed shown as checked | all five changed subtests |
| roles-page overwrites the pending status | changed test, pending-Detect subtest |
| `acceptRoleReady` skips `compareEvidence` | changed test, reload subtest |
| drop the documentId/pending identity guard | late-scan, other-document subtest |
| store the stale reply | late-scan, older-version subtest (count 2) |
| drift: scratch `fontkit-bridge.js` without `sheet.disabled = true;` (replacement count asserted 1, served by `context.route` through a patched `route_virtual_origins`, repository bridge hash unchanged) | drift test: found `serif: 36px / 900 / none / -0.01em` |

## Deviations (rule forced each)
- B7 uses a weight 900 preview, not size 50, and the line names `[data-design-id="route.title"]`, not `.shared-title`. Reasons: the real
  bridge offers the design-id selector only for that role, and app.css `[data-view="detail"] .shared-title` (0,2,0) outranks the preview
  (0,1,0) for size, so the size mutant was invisible (probe: 36px with the sheet enabled; the mutated bridge passed the 50px test).
  The detail rules do not set weight, so a 900 preview persists after `#push-detail` and the unsuspended read would show it.
- `INVENTORY` JS in the test file gained `states` (heading and entries per state); `checked` keeps its shape.

## Gates
`python -m pre_commit run --files fontkit-studio.html tests/test_role_routes.py`: whitespace Passed, ruff Passed, node syntax Skipped
(no .js), static checks Passed. `git diff --cached --check` clean. Not run (dispatch): full suite, Firefox, frontend gate, CI.

## Concerns (reported, not edited; controller assigns the fix)
Three phase-A tests of `tests/test_role_routes.py` fail on B (log `work/final6sb.log`); each is A-era test data or expectation that B's
rules contradict:
1. `CollectionTests.test_equal_styles_on_two_routes_keep_one_id_and_each_selector`: `Lists differ: ['/one'] != ['/one', '/two']`.
   The default peer check reports the 16px STYLE for `.a`, outside the 22px reference, so /two is "different style". Fix: pass
   `found={('role-1','.a'): [(styled(22),1)]}` on /two.
2. `RolesPageReaderTests.test_a_null_page_url_clears_the_rows_and_keeps_the_earlier_inventory`: `Lists differ: [] != ['/peer']`. A null
   URL now marks the route changed (brief B5), so it moves from `Checked on:` to `Changed since checked:`. Fix: assert `/peer` under changed.
3. `RouteKeyTests.test_a_revisit_replaces_the_route_and_keeps_its_place`: `Tuples differ: (['/one','/two'], ['/one','/two']) != (['/one','/two'], [])`.
   Role Y has no group on the revisit but the default check reports `.body-copy` matching, so Y stays "checked" there (checked by a check
   with matchCount > 0, brief precedence). Fix: pass `found={}` on the revisit so Y finds nothing (then Y lists the route under no match).
Also: M6 old 128-roles hint wording stays until phase C. Phase A concern 4 (status after a null URL is restored by a roles-page) is
unchanged. Real bridge: after a stored Detect the role's `.shared-title` selector is not offered; roles use `[data-design-id=...]`.

## Handoff
Subject `feat(studio): show checked, no-match and conflicting pages per role`. Body draft: Studio now lists, for every role it has seen,
the visited pages where its style was checked, where nothing matched, where a page showed another style (with the expected and found
styles), and where the stored result may be out of date after the page moved or reloaded. A page that disagrees is reported even when
the role also appears there; a live preview never changes what the page is reported to have. Session only. Deviations for the D-record:
no totals rendered (reading of the plan), B7 uses a weight preview because the fixture's detail rule outranks a size preview. Not run
here: Firefox, frontend gate, hosted CI.

## Combined A+B fix round 1 (patch `task-6s-code-ab-r1.patch`, whole vs BASE 2b70e29; `git apply --check -R` passes)
Status: DONE. Files changed this round: `fontkit-studio.html` (+10/-4 vs the A+B tree), `tests/test_role_routes.py` (3 new tests, 3 corrected,
comments and a docstring). Earlier patches untouched. Focused runs (fontkit-studio.html SHA-256 6e89358d...c60d at the end; the
on-disk mutant runner restored it every time, before = after):
- `test_role_routes test_support`: `Ran 60 tests ... OK`. `test_studio_roles test_r2_integration`: `Ran 132 tests in 198.584s OK`.
- pre-commit on the two files: whitespace, ruff, static checks Passed (node syntax: no .js). `git diff --cached --check` clean.

### New tests (RED where behaviour is new; mutants on disk, `work`-free scratch `6sfr1`)
- A-I1 `test_a_roles_page_repeating_the_stored_page_says_nothing_and_a_newer_one_says_changed`: characterization (code was right,
  review probe), so GREEN on the old tree. Mutant `if (true) roleView.status = ROLE_PAGE_CHANGED` (the dropped `changed` gate): FAIL
  `'The page changed since ...' != 'Detected 1 roles from 1 eligible ...'`.
- A-PM1 `test_a_supported_page_after_an_unsupported_one_says_ready_without_a_route_and_changed_with_one` (two subtests). RED on the
  A+B tree: `TimeoutError: Page.wait_for_function` waiting for `Ready to detect text styles.` (status stayed unavailable). Fix: in
  `acceptRolesPage`, with a supported URL and no Detect pending, `changed` gives the page-changed sentence, else a status equal to
  `ROLE_UNAVAILABLE` becomes the new const `ROLE_READY` (the same text; the ready branch now uses the const, so the literal is not
  duplicated). Mutant: drop the `else if`: ERROR (timeout) in subtest `no stored route`; the stored-route subtest keeps the old rule.
- Minor 1 `test_a_roles_page_before_any_valid_ready_is_ignored` (an invalid ready leaves no identity): GREEN on the old tree
  (characterization). Mutant: `data = readRoleReply(...)` without `identity &&`: FAIL, page error `Cannot read properties of null
  (reading 'documentId')`.

### The three phase A tests B contradicts (decided against brief lines 94, 101 and 219 and the contract)
1. `test_equal_styles_on_two_routes_keep_one_id_and_each_selector`: B is right (brief line 101: a found signature outside the
   selector's reference styles is a conflict; the default peer check reports the 16px STYLE for `.a`, whose reference is 22px). Data
   fixed: `/two` passes `found={('role-1','.a'): [(22px, 1)]}`, so that page really shows the style; the assertion "one id per
   identity, both routes listed as checked, both selectors named" is unchanged (docstring Given adds the page showing the style).
   Mutant (ids made per route): FAIL, role-2 appears.
2. `test_a_null_page_url_clears_the_rows_and_keeps_the_earlier_inventory`: B is right (line 94: a null URL sets `changed`; line 219: "a
   null URL marks it changed"). Expectation: the route is listed under `Changed since checked:` (`listed == {'changed': ['/peer']}`)
   instead of `pages == ['/peer']`; the rows, disabled Detect/Apply, UNAVAILABLE text and visited count assertions are kept. Mutant
   (changed never chosen): FAIL `{'checked': ['/peer']} != {'changed': ['/peer']}`.
3. `test_a_revisit_replaces_the_route_and_keeps_its_place`: B is right (line 101: checked is a group or a check with matchCount > 0;
   the default check reports `.body-copy` matching for Y on both routes). Data fixed: `/two` and the revisit pass
   `found={('role-1','.body-copy'): [(STYLE,1)]}` so Y is not found there. Assertions kept (`pages` role-1 `['/one','/two']`, role-2
   `[]`, count 2) and added `listed(role-2) == {'no-match': ['/one','/two']}`. Mutant (`matchCount >= 0`, no-match counted as checked):
   FAIL `(['/one','/two'], ['/one','/two']) != (['/one','/two'], [])`.
No phase B code needed changing for these three.

### Other fixes
- Minor 2: the receipt shape in `ROLE_WIRE` is wrapped over several lines (no behaviour change; the contract and the full suites above hold).
- Minor 3 (report text): the landing text must name all eight forced edits F1-F8 (F7/F8 are in `tests/test_r2_integration.py`) and the
  two `tests/role_contract.py` edits (`roles-page` in `TOLERANT_KINDS` and its violations entry).
- Minor 4: Given of the query-order test now reads "?a=1&b=2 and ?b=2&a=1, the first also with #keep and #keep2 and the second also with #keep".
- Minor 5: a comment in the hostile roles-page test says the rows share one session, so the first failing row names the fault.
- A-PM2: the click-time `Role detection request limit reached.` refusal is pre-existing BASE code that the candidate check now makes
  unreachable; it stays unchanged and untested by this slice.

### Handoff additions
Commit-body lines: the Ready sentence returns after a null-URL page when nothing is stored (new const `ROLE_READY`, same text); three
phase A tests were adapted to B's rules (data for two, expectation for one), reasons above. Budget: html +6 net this round.

# R2.6S phase C code report (mode: code, task 6sc)

BASE 2b70e29; worktree C:/fks/t6sc with the A+B patch (task-6s-code-ab-r1.patch) applied and staged underneath. Nothing committed.

Patches (in the workspace):
- `task-6s-code-abc.patch`: whole patch against BASE (`git diff --cached --binary 2b70e29`), `git apply --check -R` passes in WORKTREE.
- `task-6s-code-c-only.patch`: phase C alone (working changes over the staged A+B), 2 files.

Files changed by phase C: `fontkit-studio.html` (+23/-2), `tests/test_role_routes.py` (+289/-4, new classes at the end of
the peer classes and the real-bridge class; the 4 removed lines are the module docstring, the import, and `LIMIT_HINT`, which
phase B marked "phase C rewords it"). Budget: about 25 html (120 allowed) and about 290 tests (480 allowed).

## Steps

1. `#roleNotice` (p, role=status, textContent, hidden when empty), `roleView.notice`: done. Set at the first valid ready of a
   new origin (new-origin sentence), or in the same-origin new-document branch (`else if rolePreview.documentId !== state.documentId`):
   not-applied sentence when `rolePreview.origin === live.expectedOrigin`, `rolePreview.roles.length > 0` (read before the ready
   overwrites) and `state.roles` empty, else cleared. The origin branch wins; a same-document ready never touches it.
   Cleared by the Detect click and by `installAcceptedRoles` with `announce` true (accepted Apply, Clear preview, reset).
2. New origin: sentence set after `roleView.origin` was non-null, `clearRoleCollection(false)` as before. Done.
3. `Clear visited pages` (`#roleClearVisited`, always enabled): cancels the pending Detect timer, `pending = null`, rows `[]`,
   `clearRoleCollection(true)`, status Ready/unavailable only when `identity` is non-null, notice `Visited pages cleared. The
   applied preview and inspector edits stay.`; sends nothing, leaves `rolePreview` alone. Done.
4. Apply-disabled hint reworded to `Collection limit reached, so Apply is disabled until you clear visited pages.`. Done.
5. Imported legacy JSON: no code touched. The test uses the legacy fake target with a saved inspector edit (see Deviations).
6. C6 hostile list trimmed per Revision 2 (`javascript:` URL and 2,001-character path, plus a 2,000-character control).

## Tests (13 new methods, all with Given/When/Then docstrings)

NewDocumentNoticeTests (5): reload notice + inventory kept + peer only hello; same-document ready/roles-page shows none and a
shown notice survives a same-document ready; needs-a-preview and page-lost-it conditions; lifetime (Detect click, acknowledged
Clear preview still shown until the receipt, acknowledged Apply). OriginTests (2): new origin and back; hostile URLs.
ClearVisitedTests (3): overflow then Clear (hint gone, role-129, Apply enabled); preview/counter/status/rows; pending Detect.
LegacyOutputTests (1). RealBridgeNoticeTests (3): reload (author's weight, notice, fresh explicit Apply), SPA push (still 900,
no notice), pop-out and dock.

## RED on the A+B tree (fontkit-studio.html swapped for the A+B bytes, SHA 6e89358d...), log work/red6sc.log

`Ran 13 tests ... FAILED (failures=7, errors=5)`. Examples:
- reload (peer and real bridge, pop-out): `AssertionError: '' != 'Role preview is not applied on this page.'`
- new origin: `Tuples differ: ('', '', []) != ('A new Live App origin started a new colle...', '', [])`
- overflow hint: `(False, 'Role collection limit reached (128 roles)...') != (False, 'Collection limit reached, so Apply is disabled...')`
- Clear tests, lifetime subtests, legacy test: `Locator.click: Timeout 30000ms exceeded` (no `Clear visited pages` button).
Characterization GREEN at A+B (labelled, not manufactured RED): `test_the_notice_needs_a_preview_the_page_held_and_a_new_page_that_lost_it`,
`test_a_complete_reply_with_a_script_url_or_an_oversize_route_stores_nothing`,
`test_a_route_change_in_one_document_keeps_the_preview_and_shows_no_notice` (they pin conditions the implementation must keep).

## GREEN on the C tree: `Ran 13 tests in 15.142s OK` (work/green6sc.log).

## Mutants (on-disk edit of fontkit-studio.html by work/mut6sc.py, foreground; SHA-256 af6e0f07...b9f69 equal before and after every run)

| Mutant | Result |
|---|---|
| notice on any same-document ready (`else if (true)`) | FAIL same-document test (2 subtests) |
| notice on any roles-page | FAIL same-document test and SPA real-bridge test |
| clear collection on pop-out / on dock (two mutants) | FAIL pop-out/dock test (both) |
| drop `roles.length > 0` / drop `!state.roles.length` | FAIL needs-a-preview test (each) |
| never show the not-applied notice | FAIL reload (peer) and reload (real bridge) |
| Detect click keeps the notice | FAIL lifetime (Detect click) |
| `installAcceptedRoles` keeps the notice | ERROR lifetime (timeout waiting for the notice to hide, 2 subtests) |
| keep routes across origins / keep `nextId` / no new-origin sentence | FAIL origin test (each) |
| accept 2,001-character path | FAIL hostile-URL test |
| Clear sends roles-clear / leaves Detect pending / resets `nextId` / keeps routes / no Ready status | FAIL the matching Clear test (each) |
| Clear keeps `limitReached` / old hint text | FAIL overflow test (each) |
| scratch: append route list to the Json tab | ERROR legacy test (compare after the routes, before Clear) |

Equivalent mutants (run, pass, reasoning):
- Drop `rolePreview.origin === live.expectedOrigin` from the not-applied condition: 3 tests pass. In the same-origin branch
  `rolePreview.roles` is non-empty only after a valid ready of this origin (an invalid ready at another origin installs an empty
  preview), so the origin clause cannot change the outcome.
- Accept `javascript:` by dropping only the origin check or only the protocol check: each passes, because two independent checks in
  `validRoleURL` refuse it (a `javascript:` URL has origin `null` and protocol `javascript:`). Dropping both (`return true`) FAILS the test.
- A9's raw-snapshot mutant is unchanged from phase A (equivalent).

## Focused gates (FKS_ENGINES=chromium, PYTHONPATH=tests, in C:/fks/t6sc)

- `unittest test_role_routes test_support`: `Ran 73 tests in 59.794s OK`
- `unittest test_studio_roles test_support`: `Ran 137 tests in 167.027s OK`
- `FKS_REQUIRE_FIXTURES=1 unittest test_r2_integration test_live_integration.SyncAndReloadTests test_support`: `Ran 65 tests in 68.559s OK`
No full suite (per the dispatch). Firefox, frontend gate and hosted CI not run.

pre-commit (`python -m pre_commit run --files fontkit-studio.html tests/test_role_routes.py`): trailing whitespace Passed;
ruff Passed; JavaScript syntax (node --check) Skipped (no .js files); static checks Passed. `git diff --cached --check` clean.

## Deviations and concerns

- Legacy-output test (C8): it uses the legacy fake target with a saved inspector edit (code tabs, downloads, JSON export, Sync
  PUT body compared before, after three routes, and after Clear). The JSON export is the import format, but no JSON import is
  performed: importing applies overrides to the target and shifts its revision, and the existing import test already covers that
  path. Tell me if a literal import step is required.
- The exports are compared after the routes (before Clear) as well as after Clear, because after Clear the route list is empty
  and a mutant appending it would be invisible.
- Pop-out is exercised with `page.expect_popup()` on the virtual origin; the bridge-served pop-out and the dock both work.
- Real-bridge note: the Apply must be acknowledged (preview status `Preview applied`) before the reload, otherwise Studio reports
  the request dropped and no notice is due; `apply_title` waits for it.
- Hint wording: phases A and B still carry the old 128-roles wording in their patches; phase C replaces it (test constant `LIMIT_HINT`).

## Handoff

Subject (brief): `feat(studio): clear visited pages and refuse evidence across origins`. Draft body: Studio now says when a
reloaded page no longer holds the role preview and never replays it; a new Live App origin starts an empty collection with a
visible notice and a fresh role counter; Clear visited pages forgets the evidence while keeping the applied preview, the
inspector edits and the role counter; the Apply-disabled hint says how to recover. Ledger: no legacy output changed. Deviations
for the D-record: no JSON import step in the legacy-output test (see above); the click-time `Role detection request limit reached.`
refusal is kept (Revision 2, I1).


## Combined A+B+C fix round (AB-I1 and the AB Minors) -> patch task-6s-code-abc-r1.patch

Worktree C:/fks/t6sc, BASE 2b70e29. Changed: fontkit-studio.html (helper only), tests/test_role_routes.py. No phase C hunk was changed
except where listed; earlier patches untouched. Scratch: ...\claude\6sfr2 (outside the repo).

- AB-I1: `ChangedStateTests.test_only_the_latest_route_turns_changed_and_changed_outranks_a_conflict` (two routes: /one checked, /two
  conflicting; a roles-page at version 3 on /two). Real code GREEN (characterization of existing behaviour). Mutants, on-disk edit
  of fontkit-studio.html, SHA-256 before af6e0f07...b9f69 and after identical on the pre-refactor tree; on the final tree a3938c56...dd42
  before and after each run:
  - M15 (drop `evidence.key === key`): FAIL (`changed` would list /one too).
  - M3 (conflict ahead of changed): FAIL (/two under `conflict`).
- M4: `test_a_ready_for_another_url_at_the_same_version_lists_the_route_as_changed` (valid ready, same document and version 0, URL
  `/other`). GREEN on real code; URL clause dropped -> FAIL.
- M13: `LimitTests` 33rd-route subtest now asserts role-1 lists /r0../r30 checked and /r31 changed after the refusal (the Then in
  the docstring says so; "earlier lists stay" removed because only the count was asserted). `compareEvidence` call after
  `ROLE_LIMIT` removed -> FAIL in the 33rd-route subtest.
- Real-bridge tests assert what they produce (probed, then pinned as literals): the links test lists base-title as checked
  index+article and conflict on conflict.html with the line `[data-design-id="route.title"]: expected serif: 32px / 700 / none / 0em,
  found 1 x serif: 40px / 600 / uppercase / 0.025em`, and the conflict-title role checked on conflict, different style on index; the
  SPA test lists the home role as `changed` right after `#replace-same`, then `conflict` and the same-view role `checked` after the
  new Detect (old assertions `pages == []` replaced by these stronger ones). Docstrings updated to match.
- Helper: `roleStyleKey(style)` (html, after `roleIdentityKey`) replaces the five `roleIdentityKey({ kind:"style", ... })` constructions
  (validRoleVariants, validDetectedGroup, storeRouteEvidence `styles`, and two in roleConflictLines); `grep 'kind:"style", style'` finds
  only the helper. Pure refactor: the full focused set passed before (75/137/65 OK, with the new tests) and after (same counts).
- Docstring gaps: the Changed test now says the route is checked again by a stored Detect after a newer roles-page, a reload, or the
  pending Detect's own reply; the Limit docstring is corrected as above.
- Focused (FKS_ENGINES=chromium): `test_role_routes test_support` Ran 75 OK; `test_studio_roles test_support` Ran 137 OK;
  `FKS_REQUIRE_FIXTURES=1 test_r2_integration test_live_integration.SyncAndReloadTests test_support` Ran 65 OK.
- pre-commit on the two files: whitespace, ruff, static checks Passed; JS syntax skipped. `git diff --cached --check 2b70e29` clean.
- Patch: `git apply --check -R` passes; files: fontkit-studio.html, tests/role_contract.py, tests/test_r2_integration.py,
  tests/test_role_routes.py (new), tests/test_studio_roles.py. Handoff additions: none beyond the earlier commit subject.


## Fix round 2 (C-I1, C-I2, owner "Keep their IDs", review Minors) -> patch task-6s-code-abc-r2.patch

Worktree C:/fks/t6sc, BASE 2b70e29, whole patch regenerated (`git diff --cached --binary 2b70e29 --output=...`); `git apply --check -R` passes;
earlier patches untouched. Files changed in this round: `fontkit-studio.html` (`clearRoleCollection` only, +5/-1 lines net), `tests/test_role_routes.py`.
fontkit-studio.html SHA-256 before this round a3938c56...dd42, now 1b03bbd0...a725; every mutant run restored it (printed equal). Scratch: scratchpad `6sfr3`.

- Keep their IDs (owner). `clearRoleCollection(keepCounter)`: with `keepCounter` true it keeps the identity -> role-N entries (and labels) whose id is in
  `rolePreview.roles`; routes, refs, evidence and drafts are still cleared (the next store re-seeds drafts from the applied preview); the new-origin call
  (`false`) keeps nothing; the counter rule is unchanged. Changed hunk: `clearRoleCollection` (comment + 4 lines).
  Tests (ClearVisitedTests): new `test_after_clear_visited_pages_the_applied_role_keeps_its_id_and_other_roles_get_new_ones` (Body applied as role-1, Other detected
  as role-2 not applied, Clear, Detect: request names only role-1 with no selectors, rows Body (role-1) / Other (role-3), Apply carries role-1 at 24 and role-3 at 30,
  no Removed line). Changed existing test: `...keeps_the_preview_and_the_counter` renamed `...keeps_the_preview_and_the_applied_roles_id`; its last Then was
  "names no known roles and issues role-2", now "names role-1 with no selectors and lists Body (role-1)" (the counter is pinned by the new test and the overflow test).
  RED on the unchanged HTML: `Ran 4 tests ... FAILED (failures=2)` (`[] != [{'id': 'role-1', 'selectors': []}]` in both). GREEN after: 4 OK.
  Mutants: Clear drops the accepted roles' mappings (`[]` for the applied set) -> FAIL both; Clear keeps every mapping -> FAIL (`[role-1, role-2] != [role-1]`, overflow
  test too); counter reset on Clear -> FAIL (`['Other (role-1)']`); labels not kept -> FAIL (`[] != ['Body (role-1)']`).
- C-I2: `OriginTests` test now waits for Ready and asserts `#roleNotice` empty right after the first connect, before any Detect (docstring updated). Characterization
  GREEN; mutant (unconditional `roleView.notice = ROLE_NEW_ORIGIN`, guard dropped) -> FAIL `'A new Live App origin ... cleared.' != ''`.
- C-I1: `LegacyOutputTests` now has `edited()`, `visit_routes()`, `import_legacy()` and the new test `test_an_imported_legacy_json_is_the_same_with_three_visited_pages_and_after_clear`:
  two sessions with the same inspector edit; a literal legacy 0.1.1 JSON (one H1 slot) is imported through `#importJsonFile`, in one session after three visited pages. Asserts
  the import status, code tabs, downloads, JSON export and Sync body are byte-identical between the sessions, also after Clear, that the import changed the tabs, and
  that the held session still counts three pages after the import. Slot ids are random per session and sit in the JSON export, so both sessions run with a counter-based
  `crypto.randomUUID` init script (`COUNTED_IDS`); the pre-import exports are asserted equal across the sessions as the control. Characterization GREEN (importer untouched).
  Mutants: JSON export appends the route list -> FAIL (both legacy tests); import status appends the route count -> FAIL (`...reselected.3 != ...0`); import clears the
  collection and re-renders -> FAIL (`'' != 'Checked on 3 visited pages...'`); import clears the collection without a render -> SURVIVES (stale DOM, nothing visible until
  the next render; the re-rendering variant above is the observable one); import bumps `nextId` -> SURVIVES (the counter is not an output; no later Detect in this test).
- Minors: (2) the first legacy test's baseline is now taken before any Detect (docstring says so). (3) both docstrings corrected (links test; notice-cleared test now names
  the two notices). (4) `apply_title` moved to `RealBridgeCase`; the drift test uses it and the `WEIGHT` constant (its local `weight` and the duplicate flow are gone).
  Drift test still passes. NOT taken: (1) the dead `rolePreview.origin === live.expectedOrigin` clause stays as a defence (the review allows either); (5) the inert
  `clearTimeout` stays because the brief asked for it and it does not change behaviour.
- Focused (FKS_ENGINES=chromium, in C:/fks/t6sc): `test_role_routes test_support` Ran 77 OK; `test_studio_roles test_support` Ran 137 OK;
  `FKS_REQUIRE_FIXTURES=1 test_r2_integration test_live_integration.SyncAndReloadTests test_studio_import_link test_support` Ran 111 OK.
- pre-commit on the two files: whitespace, ruff, static checks Passed; JS syntax skipped. `git diff --cached --check 2b70e29` clean.
- Handoff additions: the commit body should say Clear visited pages now keeps the ids of roles in the applied preview (owner ruling, 2026-10-18).

## Fix round 3

Mode code, worktree C:/fks/t6sc. Patch: task-6s-code-abc-r3.patch (whole, against BASE 2b70e29; `git apply --check -R` ok). Files: fontkit-studio.html, tests/role_contract.py, tests/test_r2_integration.py, tests/test_role_routes.py, tests/test_studio_roles.py (r2 set; this round touched only the html and test_role_routes.py).

- Important 1: `test_an_imported_legacy_json_is_the_same_...` now, after the import and the equality assertion and before Clear, visits `/r3` in the held session (hero lead group plus Other) and asserts the request's knownRoles == [role-1 with `[data-design-id="hero.lead"]`], visited(4), titles ['Body (role-1)', 'Other (role-2)']. Docstring extended.
  - Mutant "import clears the collection without a render" (`clearRoleCollection(true);` after `const incoming = data.composition;`): FAIL `[] != [{'id': 'role-1', 'selectors': ['[data-design-id="hero.lead"]']}]`.
  - Mutant "import bumps nextId" (`roleView.nextId++;` there): FAIL `['Body (role-1)', 'Other (role-3)'] != ['Body (role-1)', 'Other (role-2)']`.
  - Real code: LegacyOutputTests + OriginTests + test_support, 39 tests OK. (Both mutants were reported as surviving the r2 test; the review showed them observable. The report's "counter is not an output" was wrong.)
- Important 2: new `OriginTests.test_a_new_origin_keeps_no_role_of_an_applied_preview`: apply a preview on origin A, connect evil.test with a peer whose documentId is `other-origin-document` (PEER with the first-document id replaced), Detect Other; asserts documentId, knownRoles == [], row 'Other (role-1)'.
  - Mutant `new Set(true ? rolePreview.roles...` (flag ignored in the applied set): FAIL `[{'id': 'role-1', 'selectors': []}] != []` (Ran 7, only this test; Clear tests stay green).
  - Mutant new-origin call `clearRoleCollection(true)`: FAIL the new test and the fresh-counter test (`['Fresh (role-3)'] != ['Fresh (role-1)']`).
- Minor: `keepCounter` renamed `keepAppliedIds` (3 sites, fontkit-studio.html 4155-4161), behaviour unchanged. Focused set passed before (39 OK) and after (below).
- Mutation runner `6sfr4-mut.py` (scratchpad temp dir) restored the html byte-exact each time; SHA-256 1b03bbd0... before and after all mutants, changed only by the rename afterwards.
- Focused runs (FKS_REQUIRE_FIXTURES=1, after the rename): `test_role_routes test_support` Ran 78 OK; `test_studio_roles test_support` Ran 137 OK; `test_r2_integration test_live_integration.SyncAndReloadTests test_studio_import_link test_support` Ran 111 OK.
- Not run: full suite, pre-commit (per the override).
- Handoff: no change to the commit subject/body; add to the log entry that the import test now ends with a Detect after the import, and one test for a new origin with an applied preview.

## Controller integration
