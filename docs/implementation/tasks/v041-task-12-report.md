# Task 12 code report (D2-11, B19)

Mode code, worktree the task's worktree (Task 10 patch staged, left alone; my work unstaged).
Patches (plain `git diff`, ordered): `task-12-D2-11.patch` (fontkit-bridge.js `stashLost` + `LostEditWarningTests`), then `task-12-B19.patch` (`reapplyFrom` postWarning + `ReapplyStoppedWarningTests`). `postWarning` untouched.
Note: fontkit-bridge.js and the test file are CRLF; edits keep CRLF, `git diff --check` clean.

## Tests
Focused command (brief's list, chromium): Ran 49 tests, OK.

RED (before source): LostEditWarningTests test 1 failed `0 != 1 : []`; B19 test errored (no warning, `KeyError: 'kind'` on the timeout reply); test 2 passed (characterization).
Breaks (mutated code is what the tests loaded, restored after each):
- stashLost early `return` for non-stable restored: test 1 fails `0 != 1`.
- `isDirty` test dropped: test 2 fails (a warning is posted for the clean heading).
- B19 `warnedLoops` test replaced by `if (true)`: fails `2 != 1` (two edit-reapply-stopped warnings; follows Review fix 1 sequence).

## Deviations
- Dropping the `stable` test (brief's other break for test 2) not run; the early-return and isDirty breaks cover both decisions.
- B19 test follows Review fixes 1-3 (second edit + render after quiet, count stays 1; 300 ms settle in test 1; test 2 checks the new node's 50px).

## Handoff
CHANGELOG (Task 18): D2-11 `Live edit now tells you when the app replaces an element whose edit could not be re-applied; the edit stays in the export.` B19 `Live edit now tells you when the app keeps re-creating an element and its edits stop being re-applied.`
Subjects: `fix(bridge): warn when an auto-id element's edit is lost`; `fix(bridge): tell Studio when the re-render loop guard stops an edit`.
Landing still runs test_studio_roles, test_role_routes, test_r2_integration. Scratch files removed (leftover empty-ish dir scratch/t12-rev is not mine to judge: it was not created by me).
