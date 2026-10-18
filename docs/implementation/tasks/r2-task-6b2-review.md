### Spec Compliance
- PASS: pageshow/pagehide listeners added in observeRolePage through `this.listen`, guarded `this.active && this.studioSource`, bump `roleNative` and call `scheduleRolePage()`; no `bumpRolePage()` call (fontkit-bridge.js:1275-1279 in the patch, 8 lines).
- PASS: the two bridge comments are fixed: "Addendum 23 item 4" (Addendum 23 item 4 is "Apply checks placement", plan line 522); the keyword-refusal sentence now sits above `roleFamily`, which holds the keyword regexp (fontkit-bridge.js:193-203).
- PASS: classes LifecycleTests, DelayedRenderAndHmrTests, StaleScanTests, RevisionOneKeysTests exist; 3b dropped as the brief says; 3c not added with a stated reason (M3a and M3c mask each other, brief 3c allows this). One extra StaleScanTests test (M2 killer) is within the brief's "a survivor gets the cheapest new test in StaleScanTests".
- PASS: other-module edits are only the named ones: PlacementTests single test (test_role_adapters.py:726), InstallCountTests skip moved inside subTest (test_role_stylesheet.py:1335), comment above AUTHOR_ROLES (test_role_protocol.py:295). role_contract.py, Studio files untouched.
- PASS: budget 8+3 bridge, 9, 2, 296+1 test_role_route_bridge, 2+2 = 325 gross (git diff --cached --numstat), under 375. LF endings, ASCII only, `git diff --cached --check` clean, ruff clean on the four test files, `node --check` ok.
- PASS: W2B2 1 and the two stale comments are closed at HEAD (grep: `range(table.SHARED_CLASSES)` at test_role_adapters.py:420; "before any evidence" and "transition ban the read set" absent). The report said W2B2 1 was "not re-verified"; I verified it.

### Checklist (requested)

1. Drift: PASS. I compared the literals with the plan type block (plan lines 757-796) and Messages table (808, 811, 812, 817-819) one by one. Detected: 13 body keys + `type protocolVersion sessionId`. Group: 12 keys. Style signature: 5. Binding: 3. Check: 4. Identity: `kind name` and `kind style`. Applied: 14 body keys + envelope. Role: 5. Outcome: 6. Loss: 4. roleState: 7. Page notice: 3 + envelope. All equal; the live bridge matches (the 4 tests pass). Reproduced the failure on both sides with in-memory mutants: added `debug: 1` to `roleState()` -> `test_the_ready_role_state_...` fails; removed `scannedElements` -> `test_the_detected_reply_...` fails; added `debug: 1` to the page notice -> `test_the_page_notice_has_exactly_the_six_keys` fails. Nested lists are asserted non-empty before nested keys are compared (detected: groups, selectorChecks, signatures, selectors, check signatures; receipt: roles, outcomes, losses; state: roles). Unchecked on purpose: RoleInput.properties (optional keys), and only the first role, outcome and loss are compared.
2. pageshow/pagehide follow ruling 1: PASS. The handler moves only `roleNative` and schedules; `bumpRolePage` mutant is killed by 1b and 1c (4 failures). 1b dispatches persisted pagehide then pageshow on an unchanged page: 600 ms silence and a Detect at the ready's version. The registration spy (1d) shows adds [1,1], and after dispose every bridge add has a matching remove, the page's control listener is never removed and still fires. Non-vacuous: the direct `window.addEventListener` mutant fails only 1d (reproduced). Registered once is held by the existing `if (this.roleObserver) return;` guard in observeRolePage; the test uses one hello only, so a second hello is not exercised (observation, not a defect; the guard is R2.6B1 code).
3. Mutants reproduced by me with `RoleBridgeCase.open(bridge_source=...)` (own runner, scratchpad `6b2rv-mut.py`; bridge SHA-256 before and after both `3f7f063a...5f47`):
   - M2 `current()` without the generation check: `StaleScanTests.test_a_selector_refused_inside_the_scan_...` fails (1 failure). The same mutant survived 55 existing tests (test_role_detection, test_role_preview, PlacementTests, RouteAnnouncementTests, SessionAndDetectTests), so the added test is the first killer.
   - handler without `roleNative += 1`: 3 failures, all 1c subtests. `pageshow` only: 1c "pagehide alone" and 1d fail. `bumpRolePage()` in the handler: 1b and 1c x3. Direct `addEventListener`: 1d only.
   - M3a (`fresh()` without refresh): the new 3a test fails (so it is a killer, not only the existing tests). M3b (no `job.native`): 1c x3 fail.
   - 2a/2b: `subtree: false` kills 2a, both 2b subtests and the preview test; dropping `attributes` kills only the href swap; `attributes` only kills the text replace and the preview test. Extra mutant of mine: `isOwnedRoleMutation` returning false kills the preview test alone, so that test proves its own claim (the report's table does not record that mutant).
   - BODY test: `soleBody` lowercasing kills `test_detect_refuses_a_known_role_on_uppercase_body`.
   - Equivalents, judged at source: M1 equivalent (`sessionId` is assigned only in `dropSession` and `handleHello`, 1089 and 1203, and both call `cancelRoleJobs()` first, which moves `roleGeneration`; M1 also survived StaleScan+Lifecycle in my run). M2b equivalent (`documentId` assigned once, constructor line 662). M3c equivalent (`roleURL` is written only in the constructor and in `refreshRolePage`, which bumps the version whenever `location.href !== roleURL`; `fresh()` refreshes first; M3c survived my run). M5 equivalent (`roleJobAlive` also checks `job.epoch === this.roleEpoch`; `roleEpoch` moves in both session-change sites). None is a missed test.
4. Fake versus real: PASS. All tests drive the real bridge on the real Studio-origin host. The only substitute is the dispatched PageTransitionEvent, stated in the LifecycleTests docstring and the report; the bridge listener comment explains the behaviour. I confirmed the multi-statement `HIDE; SHOW` script fires both events in order (probe `6b2rv-probe.py`: log ['hide','show']).
5. Hidden skips: none new. No new `skipTest`. All new tests use repo fixtures (role page, SPA, large page, Bootstrap 5 fixture), none npm-installed. The only skip is the existing Firefox one, now inside the subTest; I confirmed with `FKS_ENGINES=firefox,chromium` that Firefox is reported `skipped=1` and `cut_sheet_is_blocked` still runs for chromium. Under the default (chromium) and hosted CI nothing changes.
6. Tests: PASS. Every new test has a recorded or reproduced mutant (above). Oracles are literals or plan key sets, never read from the bridge. Outcomes are wire messages, URLs, computed sizes, owned-sheet bytes. Given/When/Then Thens equal the assertions in all 13 new tests (checked docstring against body each time). Sleeps: only the 300/600 ms absence waits. Ran the four new classes: 13 tests OK.
7. Code: PASS. Changes only in owned places. Comments say why. W2P 2, W2B1 2, W2P 1, W2P 4/W2B1 1 correctly taken. W2T bound 200 is arithmetically right (sizes `10 + 2v + r/100` collide across variants when roles differ by 200, so r in 0..199 is distinct) -- see Minor 2 for wording.

### Checks run
- Four new classes -> `python -m unittest ...LifecycleTests ...DelayedRenderAndHmrTests ...StaleScanTests ...RevisionOneKeysTests` in C:/fks/t6b2 -> 13 tests OK.
- Mutant sweep above -> `6b2rv-m.sh` in scratchpad -> results as listed.
- M2 against existing modules -> 55 tests -> OK (survives), so new killer is needed and valid.
- Hidden skip risk -> firefox,chromium run of the InstallCountTests cut-sheet test -> skipped=1, chromium body ran.
- CRLF/ASCII -> index vs HEAD CR counts, non-ASCII grep on the cached diff -> LF, ASCII.
- Bridge unchanged on disk -> sha256sum before/after -> identical.

### Strengths
- 1d observes registrations directly with a handler-identity control, so it separates `this.listen` from a leaked `addEventListener`, which no wire assertion can.
- The 1c subtests each have their own mutant (roleNative bump, pageshow-only), and the `pagehide`-only subtest is what kills the pageshow-only mutant.
- Key-set tests fail on both an added and a removed key at several nesting levels (reproduced), with non-empty nested-list guards.
- The M2 killer is a genuine synchronous-ordering case (reject posted, then `finish` runs in the same task), and the equivalent-mutant reasoning checks out at source.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_role_route_bridge.py:641 and :757: the "open LARGE, hello, mode interact, mark, `request({type: "design:detect"})`, assert no `design:detected` yet" preamble now exists three times in the file (existing test at :527, 1c, 3a). Constraints: "a third copy within one side is a finding". Low risk; a small helper would remove it. The brief's own text prescribed each pattern.
2. tests/test_role_protocol.py:295-296: the comment says sizes stay distinct "up to 200 roles of the same variant". Within one variant sizes are distinct for any role count; the collision is across variants (v+1 against r-200). The bound is right, the phrase "of the same variant" is misleading.
3. fontkit-bridge.js:1275-1276 comment says the refresh bumps "only if the URL, styles or viewport moved"; `refreshRolePage` also drains author DOM mutation records. Wording only; matches the brief's text.
4. 1c and 3a rely on the 5,000-element scan still being in flight when `frame.evaluate` runs; the only guard is the immediate `messages == []` check. A very fast machine gives a red, not a false green. The same pattern is in the existing test at :518.
5. The report's mutant table omits the `isOwnedRoleMutation` mutant that kills the preview test uniquely (I reproduced it); the preview test's recorded killers are shared with 2b.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The 8-line bridge change follows ruling 1 exactly, and every new test fails on a reproduced realistic mutant, including M2 against the added test and the registration, key-drift and body mutants. The four equivalent mutants are unobservable at source and survived my runs. Only Minor polish remains.
