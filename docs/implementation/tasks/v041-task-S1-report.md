# Task S1 code report (mode code, WORKTREE C:/fks/tstrip, BASE 5bd655e)

Status: DONE_WITH_CONCERNS. Patch: WORKSPACE/task-S1-code.patch (`git apply --check -R` OK). 7 files staged by name:
CHANGELOG.md, fontkit-studio.html, tests/fixtures/bridge/target.html, tests/test_studio_dead_controls.py,
tests/test_studio_import_link.py, tests/test_studio_live.py, tests/test_studio_roles.py. CRLF kept. No nested gate-run (skipped by override).

## Behaviours (all six present)
Preset removed (options rowdemo, blank; asserted in test_studio_live); palette renamed with hex unchanged; `LEGACY_COLOR_NAMES` Map with
`??` lookup (`currentColorName`) in hydrateSlot (all slot types, row children via recursion) and on the background in importCompositionJson;
fixture shows `Sample`; CHANGELOG bullet under Unreleased / Changed. New `SavedColourNameTests` (4 methods, Given/When/Then).

## import_link 83-86 fix (this round)
Linked page starts in Fonts mode; the canvas is reached with `#viewSpecimenCanvas` (as test_studio_live 289-290). Three further test-only changes
were needed, all in `check_late_ack_keeps_the_imported_tokens`/helper:
- `page.bring_to_front()` after `blank_document` (it opens a second page; without it the linked page's clicks time out).
- `wait_composition_updates` and a new wait for `--font-mono` to include "JetBrains Mono" use `polling=50` (default raf polling never fired
  although the count was 2 by direct evaluate).
- `page.locator('#viewTargetApp').click()` before `self.code(page, 'Css')`, because the code tabs are not visible in the Specimen view.
Both assertions the brief names stay: before_import has Fraunces display and JetBrains Mono mono (differs from the imported Inter/IBM Plex Mono
document). No assertion weakened; one wait added.

## Focused run (scratch/S1-focused-3.log, PYTHONPATH=tests, all rc=0)
test_studio_import_link 46 OK; test_studio_live 152 OK; test_studio_roles 114 OK; test_support, test_studio_controls, test_font_kit_studio_v011,
test_studio_review_findings, test_studio_first_run, test_bridge_runtime together 252 OK; test_studio_dead_controls 30 OK.
Not run: none of the brief's list. Earlier red run: scratch/S1-red.log (from the previous round, not redone).

## Mutants (scratch/S1-mut.py, logs S1-mut-bg|rowchild|gated.log; target class test_studio_dead_controls.SavedColourNameTests, 4 tests)
Script asserts the mutated text is on disk before the run and restores the original bytes in `finally`.
fontkit-studio.html SHA-256 before and after every run: 596e4184edb8294ec6ad1045d5af58c79eeac6577472ddcccaecc6f23798cf27 (identical).
- bg (background lookup removed): 2 errors, cases "background saved by Void" and "by Starlight".
- rowchild (`depth > 0` skips lookup): 1 error, case "a text slot nested in a row".
- gated (lookup only when colorSource === "saved"): 1 error, the custom-slot-switched-to-saved test.

## Moved tests / built state
Moved per the brief's table: dead_controls 21,77-80,93,110-114,168,234; import_link 50,83-86,204,294,308,407,421,436,521,533; live 2407,2411
(+ option-values assertion); roles 2304-2307. Rebuilt state or different evidence: import_link 83-86, dead_controls 77-80, 110-114, 234,
roles 2304-2307. Weaker for A: at import_link 294/308 A is now `blank` (Inter), so `assert_b_is_saved`'s `assertNotIn('Inter')` can no longer
tell a leaked A from B's own text if B shares Inter; it still catches a leaked rowdemo-derived Fraunces. (Reported as in brief; unchanged.)
import_link 521: no new confirm observed (suite passes).

## Sweep
`git grep -in asteria -- fontkit-studio.html tests`: only the 11 LEGACY_COLOR_NAMES lines (2132-2142, under a comment) and the behaviour-3 test
data/assertions in test_studio_dead_controls.py (261-279, 342, 350-363).

## Forward limit (O6)
A file exported after this change shows `#000000` for saved-source colours in a 0.4.0 Studio (names unknown there): accepted.

## Nested gate-runs
None (skipped by controller override).

## Handoff
Subject/body per brief for the landing; CHANGELOG already in the patch. Concerns: three extra test-only waits/steps listed above (bring_to_front,
polling=50, viewTargetApp); `git diff --cached --check` clean.

## Fix round (r2)

Test-only; no product code changed (fontkit-studio.html sha256 596e4184...cf27 before and after every mutant). Patch: task-S1-code-r2.patch. Focused log: scratch/S1-focused-4.log.

Changes:
- dead_controls PresetSelectTests: `#composerCanvas > .flow-slot` count asserted next to each `#slotCount` check (4, 5, 4) and in the accepted-replace test (5). Mutant "applyCompositionPreset skips renderComposer()" now fails: `AssertionError: 0 != 4` (scratch/S1-mut4-norender.log).
- dead_controls SAVED_NAME_CASES: added the background with source `custom` and `Asteria Starlight`. Mutant "background lookup gated on source saved" fails: `'' != 'Ice White'` (S1-mut4-bggated.log).
- dead_controls: one new method `test_each_of_the_eleven_old_names_maps_to_its_new_name_and_colour` with a typed table OLD_TO_NEW (11 old, new, rgb from the brief). Imports in two chunks (six then five): the page keeps only 8 text slots per import. Mutant Haze->Midnite fails on the painted-colour list, rgb(0,0,0) for rgb(11,16,34) (S1-mut4-haze.log).
- import_link 294/308: A is no longer `blank` (Inter, same as B's file). A is now an edit through the UI, first slot family `space-grotesk` (helper `edit_first_slot_family`); 308's queued edit is the same slot set to `dm-sans` (the rowdemo select would raise a replace-confirm after an edit). `assert_b_is_saved` also asserts `Space Grotesk` and `DM Sans` are absent from the saved CSS, and clicks `#viewTargetApp` first (the code panel is in the Live App view). Mutant "recordCanonical protection removed" (`if (op.importSuperseded)` -> `if (false)`) fails both tests: the CSS holds `--font-display: "Space Grotesk"` where Georgia is expected (S1-mut4-leak.log).
- Minor 2 left as is. Minor 3 correction: the click timed out in 1 run of 20 without `bring_to_front`, so `bring_to_front` guards an intermittent hang, not a constant one.

Mutants: each log shows before sha, mutated sha (differs, marker present in the file the tests load), failing assertion, and after sha equal to before (restored byte-exact).

Focused run (PYTHONPATH=tests): `python -m unittest test_studio_dead_controls test_studio_import_link test_support` -> `Ran 111 tests in 143.078s / OK`.
Not run: other modules (landing gate). Nested gate-runner skipped as ordered.
