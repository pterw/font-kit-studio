### Spec Compliance
- PASS: B14 req 1. BLOCK_ELEMENTS gains the eight tags (fontkit-bridge.js:94-96 in patch); line 2673 untouched; test builds nodes in the page before hello, asserts guard content-model, overridable False, main innerHTML unchanged, and the set_content oracle (parent is not the p). The div-into-em/code/strong test builds parents directly in main (review fix 5).
- PASS: G1-5 req 2. Only the `stat` entry changed to `.stat`; five other `[class*=...]` entries intact. Fixture has each div in its own `<section>` (review fix 3); test asserts 1 target, no data-design* on static/status.
- PASS: B01 req 3. Flag `warnedUnreadOrigins` directly above resolveAllowedOrigins; warns only when no option, no script read, and `script[data-allowed-origins]` exists; message is New string 4 verbatim (checked against the brief text); return value unchanged.
- PASS: Review fixes 1, 2, 4. `new FontKitBridge()` is called before hello and `__warns` is asserted; the module imports fine (hello from EVIL gets design:ready); option and `*` cases assert `[]`, option case asserts a timeout.
- PASS: owned files. Only fontkit-bridge.js regions named, tests/test_bridge_runtime.py, three new fixtures; test_role_detection.py and CHANGELOG untouched.
- Deviation, accepted: page constants (MODULE_BUNDLE_PAGE, CLASSIC_CAPTURE_PAGE, STAT_NAMES_PAGE) beside ARRANGE_PAGE, and fixtures switching on `location.hash` (#options, #star) instead of extra fixtures. Reported in the report; see Checks for the effect on parallel tasks.

### Checks run
- Patches apply in order, each as a working commit -> `git archive 5443ff6` into scratch/t5rev, `git apply --check` then apply B14, G1-5, B01 in sequence -> all three applied cleanly; final fontkit-bridge.js and tests/test_bridge_runtime.py are byte-identical to the task's worktree, and the three fixtures match modulo CRLF. Each patch is self-contained: the G1-5 patch adds only STAT_NAMES_PAGE and B01 adds the other two constants, so none references a name from a later patch. No stray files; subjects carry no process state.
- Focused tests (the 3 new classes) in the task's worktree under chromium -> 7 tests OK in 9s. The full focused command was not re-run; the report shows 51 OK. Left for the wave gate: test_role_detection, Firefox/WebKit engines.
- Mutations on the scratch export (code that the tests load, baseline run first): drop `hr` KILLED; drop `main` KILLED; drop `li` KILLED; restore `[class*="stat"]` KILLED; drop flag check KILLED; drop `warnedUnreadOrigins = true` KILLED; warn even when an option is given KILLED; change message text KILLED; **remove the `document.querySelector('script[data-allowed-origins]')` condition: MISSED** (see Issues).
- Parallel tasks -> `git apply --check` of task-4-code.patch (and tasks 2, 3) against the patched export: all apply cleanly, so the constants block and the class placement do not collide with Task 4. Tasks 10 and 13 have no patch yet and were not checked.
- Hash-switched fixtures -> `open()` passes the target as a `host.html?target=` query, so `%23options` decodes to a `#options` hash in the iframe; the option case proves the option reached the bridge (a hello from EVIL times out). Fixtures are new files, owned by this task, so no other task can collide with them.

### Strengths
- The B14 oracle (a real parser run for each tag) shows why the guard is right, and drops of single tags fail.
- The once-per-page flag is genuinely exercised: the second construction happens before hello (verified by the two flag mutants being killed).

### Issues
#### Critical
None.
#### Important
1. tests/test_bridge_runtime.py (UnreadOriginListTests, patch B01) -- no test covers "no `script[data-allowed-origins]` anywhere, so nothing is warned". Removing that condition from the `else if` (every page that sets no list would then log "could not be read from this script") passes all three new classes (mutant MISSED, confirmed above). That is requirement 3's second guard and the most common real page. Fix: one more case in `test_a_classic_script_tag_keeps_its_list_and_warns_nothing`, e.g. a page with the `__warns` wrapper and a plain bridge script tag with no attribute (a `#none` branch in target-classic-capture.html, or a capture of the module fixture without the attribute), asserting `__warns == []` and hello from EVIL gives design:ready.
#### Minor
- Blank-line drift in tests/test_bridge_runtime.py: two blank lines between methods inside ContentModelGuardTests (B14); one blank line before and three after AutoSelectorWholeNameTests (G1-5); three after UnreadOriginListTests and NEW_STRING_4 sits between two classes (B01). Cosmetic.
- B14 test: `parser_page` is not closed if an assertion fails before `parser_page.close()`; the page is torn down with the context, so no leak beyond a failing run.
- Page constants are not in alphabetical or related order (STAT_NAMES_PAGE after ARRANGE_PAGE, the two B01 constants between them). Tasks 10 and 13, if they add constants beside ARRANGE_PAGE, may need a trivial context merge; no semantic conflict.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** All three requirements and the five review fixes are met and the patches apply in order and cleanly beside Task 4; one explicit guard of the B01 warning (no script tag with the attribute means no warning) is untested, and a mutant that removes it passes every new test.

---

### Spec Compliance
- PASS: the finding is covered by one new subTest (case='no origin tag') in the existing characterization test, not a new test (tests/test_bridge_runtime.py:632-636).
- PASS: it asserts first that the page has no tag (`document.querySelectorAll('script[data-allowed-origins]').length == 0`, line 634), so it cannot pass on a page that carries the attribute. The fixture reads `#none` and omits the attribute (target-classic-capture.html); had the hash not reached the page, the count would be 1 and the assertion would fail.
- PASS: it asserts the bridge booted (`design:ready` from hello, line 635) before `__warns == []` (line 636), so a page where the script never loaded cannot pass.
- PASS: only tests/test_bridge_runtime.py and this task's own fixture changed; fontkit-bridge.js is untouched in this round (the worktree diff to it is Task 5's B01 work).

### Checks run
- Condition removed -> scratch copy of the task's worktree, with ` && document.querySelector('script[data-allowed-origins]')` dropped from the `else if` at fontkit-bridge.js:578 (now `else if (!warnedUnreadOrigins) {`), then `python -m unittest test_bridge_runtime.UnreadOriginListTests` from its tests/ dir -> FAILED (failures=1): subTest engine='chromium', case='no origin tag' fails at line 636, `['[FontKitBridge] data-allowed-origins could not be read ...'] != []`. The other subTests still pass, which matches the original finding.
- Real worktree -> same command in the task's worktree/tests -> Ran 2 tests, OK.
- Worktree state after the run -> `git status --short` -> unchanged (M fontkit-bridge.js, M tests/test_bridge_runtime.py, three untracked fixtures); the mutation was applied only to the scratch copy.

### Strengths
- The page-identity guard (tag count 0) plus the booted check make the case hard to pass on the wrong page.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
None new.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The new subTest fails when the tag condition is removed and passes on the real code. It asserts the page has no tag and that the bridge booted, so it cannot pass on the wrong page.
