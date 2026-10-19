# R2.6B2 code report (mode code, worktree C:/fks/t6b2, BASE 2b70e29)

Patch: `.superpowers/sdd/r2c/task-6b2-code.patch` (`git apply --check -R` passes). Files: `fontkit-bridge.js` (+8/-3: pageshow/pagehide
listeners and two comments), `tests/test_role_route_bridge.py` (+296: `LifecycleTests`, `DelayedRenderAndHmrTests`, `StaleScanTests`,
`RevisionOneKeysTests`), `tests/test_role_adapters.py` (+9), `tests/test_role_stylesheet.py` (2/2), `tests/test_role_protocol.py` (2/2).
317 insertions + 8 deletions = 325 gross lines against the budget of 375. `tests/role_contract.py`, Studio files: untouched.

Real BFCache does not occur under Playwright Chromium (back reloads, `persisted` is false, the target is an iframe). The dispatched
`pageshow`/`pagehide` events stand in for it, so 1a-1d prove the handler wiring only, not the browser's restore. A page frozen with no
`pageshow` is seen only by the next Detect (README line for the release point).

## Steps

Done: req 1 (1a-1d), 2 (2a, 2b both subtests, plus the preview variant), 3a, 4, 5 (sweep), 6 (Minors). 3b dropped as the brief says (cite
`test_role_detection.test_latest_detect_hello_reset_and_dispose_suppress_old_jobs`). 3c not added: M3a is killed by existing tests and
M3c is equivalent, so the wrapper-free path is proved (see table). Added beyond the brief's list: one `StaleScanTests` test for M2 (below).
Deferred to landing: log entry, plan boxes, README, nothing else.

## RED at BASE (bridge unchanged; log `work/6b2-red-lifecycle.log`)

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest -v test_role_route_bridge.LifecycleTests` -> `Ran 4 tests`, `FAILED (failures=5)`:
- 1a `...pageshow_alone_announces...`: `AssertionError: Lists differ: [] != ['http://target.test/tests/fixtures/bridge/target-role-protocol.html?route=bf']` (no listener, no notice).
- 1c, three subtests (pagehide then pageshow, pagehide alone, pageshow alone): `('design:detected', True, None) != ('design:detected', False, 'page-changed')` (BASE replies complete).
- 1d: `{'adds': [0, 0], 'removes': 0, 'unmatched': 0} != {'adds': [1, 1], 'removes': 0, 'unmatched': 2}` (BASE registers nothing).
- 1b ran GREEN at BASE (characterization of the one rule).
GREEN after the 8-line change: `Ran 4 tests ... OK`.
Ran GREEN at BASE by design (characterization): 2a, 2b (all three), 3a, the M2 test, all of `RevisionOneKeysTests`, the `BODY` test (never run at BASE with a
failure to show; the brief's observed reply is recorded here: `{'type': 'design:rejected', ..., 'reason': 'unsupported-value'}`, probed at the patched tree
whose Detect path is unchanged).

## Mutants (in-memory via `RoleBridgeCase.open(bridge_source=...)` patched by `work/6b2-mut.py`; the bridge on disk was never edited)

SHA-256 of `fontkit-bridge.js`, before the sweep and after: `3f7f063a5256f9be365930b4d8d38f3072eeb093fdff137d097818acc5bf5f47` both times
(the file includes my 8-line change; it was not written during the sweep). Existing modules run per sweep mutant: test_role_detection,
test_role_stylesheet, test_role_route_bridge, test_role_preview (132-133 tests, about 3.5 min each).

| Mutant | Result | Killed by |
|---|---|---|
| 1a handler loop removed | killed (5 failures) | 1a, 1c x3, 1d |
| 1b handler calls `bumpRolePage()` | killed (4) | 1b (unchanged page), 1c x3 (reply versions differ) |
| 1c `roleNative` bump removed | killed (3) | 1c x3 |
| pageshow only | killed (2) | 1c `pagehide alone` subtest, 1d |
| `addEventListener` not `this.listen` | killed (1) | 1d only (no wire assertion can) |
| 2a observer `subtree: false` | killed (4) | 2a (missing second notice), both 2b subtests, preview test |
| 2b drop `attributes` | killed (1) | 2b `href swap` |
| 2b `attributes` only (drop characterData+childList) | killed (2) | 2b `text replace`, preview test |
| 4 `debug: 1` in `roleState()`, detected top level, group, loss, page notice; `scannedElements` removed | each killed (1 failure) | the matching `RevisionOneKeysTests` test |
| BODY: `soleBody` lowercases | killed (1) | `test_detect_refuses_a_known_role_on_uppercase_body` |
| M1 `current()` without session | survives all 132 | equivalent (`sessionId` changes follow `cancelRoleJobs()` which moves the generation) |
| M2 without generation | survived all 132 existing | KILLED by new `test_a_selector_refused_inside_the_scan_leaves_only_the_rejection_behind` (rejection in the iterator, 1 failure) |
| M2b without documentId | survives (133) | equivalent (`documentId` set once in the constructor) |
| M3a `fresh()` without refresh | killed (4) | `test_role_detection` style-only change and null-URL tests, new 3a |
| M3b without `job.native` | killed (11) | `SplitPageVersionTests` font and hover, `test_late_native_style_only_focus...`, 1c x3 |
| M3c without `job.pageURL === location.href` | survives (133) | equivalent: `fresh()` refreshes first, which already advances the version for a URL change |
| M4 `finally { restore(); }` emptied | killed (8) | `BaselineDetectTests`, `CommitReceiptAndQueueTests`, `OwnershipAndInstallTests` |
| M4b `run` without `suspendRoleSheet()` | killed (5+1 error) | `TransitionBaselineTests`, `BaselineDetectTests` x2, preview test |
| M5 Apply's `roleJobAlive` without session | survives (132) | equivalent: it also checks `job.epoch === this.roleEpoch`, which moves with every session change |
| M6 history guard / dispose without `removeRoleHistory` / saved descriptor not restored | killed (1 / 3 / 1 error) | `InstallAndRemovalTests` (R2.6B1 table) |

Survivor notes: M1, M2b, M3c and M5 are declared equivalent by the runs above; no test added for them. The 3a test dies to M3a (URL-only change then
the version check) and M3b-free paths are covered elsewhere. A native-push-in-listener test (3c) was written, found unable to kill any single mutant
(M3a and M3c mask each other), and removed.

## Focused gates (chromium only)

- A `test_role_route_bridge test_role_protocol test_support`: `Ran 97 tests ... OK`.
- B `test_role_adapters.PlacementTests test_role_stylesheet.InstallCountTests ...BaselineDetectTests test_role_detection test_role_preview test_r2_route_fixtures`: `Ran 57 tests ... OK`.
- C `test_bridge_runtime.HandshakeTests`: `Ran 2 tests ... OK`.
- `FKS_ENGINES=firefox,chromium` on the parser-cut test: `OK (skipped=1)` with the Firefox subtest reported skipped and Chromium's subtest run.
- `node --check`: ok. `ruff check . --exclude .agents`: All checks passed. `git diff --cached --check`: clean.
- pre-commit (staged files): trailing whitespace, ruff, node syntax, static checks all Passed (other hooks not shown applied to these files).
- Not run: full suite (settled wave), Firefox engine tests, other engines.

## Minors table verdicts

W2P 2 taken (comment now "item 4"). W2B1 2 taken (keyword sentence moved above `roleFamily`). W2P 1 taken (new `PlacementTests` test; probed reply
`design:rejected` / `unsupported-value`; lowercase `soleBody` mutant killed). W2P 4 / W2B1 1 taken (skip inside `subTest`; Firefox skipped, Chromium runs).
W2T taken with the exact bound: the test's sizes are `10 + 2v + r/100` and two (v, r) pairs collide only when roles differ by 200, so the sizes are distinct
for r in 0..199: "up to 200 roles" (derived from `AUTHOR_ROLES` itself; `table.ROLES` is 128, inside it). W2B2 1 closed at BASE (`range(table.SHARED_CLASSES)`, not
re-verified beyond the brief). Stale comments closed at BASE. W2B2 2/3/4 left (accepted survivors). W2P 3, W2P 5, W2B1 3/4/5, W2E, W2L, W2PI, W2PS, W2SB, W2SC,
Heading grammar third copy, T9, T13 left as in the brief.

## Live key-set mismatches

None: every literal in `RevisionOneKeysTests` equals the keys the live bridge posts at every level checked, and `table.violations` returns `[]` for
detected, roles-applied and both role-state forms.

## Notes

- `tests/test_role_route_bridge.py` has LF endings in the working tree (the other touched files are CRLF); bytes preserved per file.
- Open: `test_the_bridge_registers...` uses an in-memory prefix spy and the page's control handler by identity, as Revision 2 asks.

## Handoff

Commit subject: `feat(bridge): treat back/forward cache restores as route events`

Draft body (wrap 72): "A page restored from the back/forward cache keeps its JS state
but had no listener for it. The bridge now moves its internal epoch on
pageshow and pagehide and schedules a refresh, so a Detect that
straddles a freeze ends page-changed and a URL the restored page holds
is announced. The wire pageVersion still advances only when the URL,
styles or viewport really changed. Adds route-evidence guard, delayed
render, hot update and revision-1 key-set tests, plus the review
comment and test fixes."

Plan boxes: the last three R2.6B checkboxes (baseline selector evidence, route test list, guard mutants). Log entry: product terms as in the brief's Handoff
plus the mutant table above and the Playwright BFCache statement. README (release point): add that CSSOM `insertRule` without a DOM change and a page frozen
without a `pageshow` event are seen only by the next Detect.

## Controller integration
