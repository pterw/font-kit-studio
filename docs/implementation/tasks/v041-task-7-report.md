# Task 7 code report (mode code, BASE 5443ff6, worktree the task's worktree)

Patches (, in order, each on the one before; chain verified on a clean BASE copy, final file identical to the worktree):
1. task-7-S09.patch: fix(studio): take the display family from the first text slot (fontkit-studio.html compositionPatch; new tests/test_studio_sync_reads.py)
2. task-7-G2-6.patch: refactor(studio): drop the unused font aliases read (cssStack)
3. task-7-G2-19.patch: refactor(studio): stop shadowing familyOptions (inspector local -> familyChoices, 2 uses)

## S09
`compositionPatch` now takes the first slot with type "text" for the --font-display fallback (none: nothing sent). Test
`test_display_token_ignores_a_row_placed_first` follows the brief plus Review fixes: sets Wordmark to jetbrains-mono in the specimen
inspector, Sync (control), Move up twice, Sync again; waits on `len(updates)` = 4; compares first and last composition update tokens.
Assertions: first != Fraunces stack; last == first; no page error.
RED (fix reverted, the test loaded the mutated page): `AssertionError: '"Fraunces", serif' != '"JetBrains Mono", monospace'`. GREEN with fix: 1 test OK.
Note: the pre-sync family pick sends no update of its own; counts are 1 (sync1), 3 (after two moves), 4 (sync2).

## G2-6
Before/after `fonts.map(cssStack)` in the page (16 fonts, Fraunces ... Space Mono): byte-identical (cmp). Dumps in
scratch/t7-dump-before.txt and t7-dump-after.txt. No new test.

## G2-19
Renamed the local; function at the old line 2536 untouched, no page error. No new test.

## Tests (chromium, one module at a time)
test_studio_sync_reads 1 OK; test_support 34 OK; test_studio_roles 114 OK; test_role_routes 52 OK; test_r2_integration 29 OK;
test_studio_controls 34 OK; test_studio_live classes StudioArrangeTests, StudioFreeFontTests, StudioProtocolTests (the ones using liveFontFamily) 44 OK.
No full suite, no mutate.py, no gate run, no commit or stage (only `git add -N` of the new test file, as the rules allow).

## Outside the regions
None. CHANGELOG.md untouched. A temporary tests/zz_t7_dump.py was used for the dump and deleted.

## Handoff
CHANGELOG: no line from me. S09 changes the synced --font-display only when a Row or Image sits first and the first text family is not Fraunces; controller writes the ledger line.
Worktree still holds all three changes uncommitted (git diff = patches 1+2+3 combined).

## Follow-up (task 7-fix1): assert the chosen family's stack
Changed only tests/test_studio_sync_reads.py: added the independent literal `JETBRAINS_MONO = '"JetBrains Mono", monospace'`; the test now asserts `tokens[0] == JETBRAINS_MONO` (the control carries the chosen stack) and `tokens[-1] == JETBRAINS_MONO` (replacing last == first). The earlier first != Fraunces check stays.
Break shown (the mutated page is what the test loaded): fallback changed to `state.slots.filter(slot => slot.type === "text").pop()` (last text slot). Result: FAIL `AssertionError: '"IBM Plex Mono", monospace' != '"JetBrains Mono", monospace' : the control must carry the chosen family stack`. Old assertions would have passed it.
Restored to `state.slots.find(slot => slot.type === "text")`; test_studio_sync_reads rerun: 1 OK. No patch written (controller regenerates). Nothing staged or committed.

### Handoff addendum
CHANGELOG line (replaces "no line from me"; controller ruling S09): "The synced display font now follows the first text slot when a Row or Image sits first."
