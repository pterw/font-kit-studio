### Spec Compliance
- PASS: Req 1. A text slot (top level or row child) with a non-empty string family that is neither a library family nor a LEGACY_FAMILIES key gets `{family} is not in the library, so the first library font is used.` appended once per distinct family, first-seen order (fontkit-studio.html:2457 records, :3337 appends via `new Set(map.values())`). Verbatim string. Test `test_an_unknown_family_is_named_once...` and `test_a_row_child_is_named...` assert the exact status.
- PASS: Req 2. Fallback unchanged: `byFamily` untouched, `slot.family = byFamily(...)` still runs after the record (:2458). Export asserts `['fraunces','fraunces']`; pinned `test_studio_live -k legacy_keys_still_import` passes.
- PASS: Req 3. Library, legacy key (`gotham`), missing, non-string (`7`) and empty family give exactly `Composition imported. Image assets must be reselected.` (`test_no_warning_when_no_family_is_lost`). A non-string is reset to the base family earlier in `hydrateSlot`, and `slot.family &&` skips the empty string.
- PASS: Req 4 and Review fix 6. `hydrateSlot(raw, depth=0, missing=null)`; presets and other callers pass nothing and behave as before. A Map slot->family (a deviation from the suggested Set, allowed by "suggested shape") lets the row branch delete entries for children filtered or cut by `childCount` (:2438-2439). `test_a_row_child_cut_by_the_row_count_is_not_named` covers it.
- PASS: Both import paths. The sentences are concatenated after the whole ternary and the dropped-edits sentence (:3335-3337), so they follow plain and linked text alike. Plain and linked each have a test (`test_the_warning_follows_the_linked_import_status_too` asserts `STATUS + GHOST`).
- PASS: Owned regions only. The patch touches `namesFamily` above `byFamily`, `hydrateSlot`, the `.map` at the old 3296 and the status at the old 3328-3331; plus the new `tests/test_studio_guards.py`. No CHANGELOG, no stray file (`grep '^+++'` shows two files).
- PASS: Text goes through `textContent` (existing assignment). A family name from the file cannot become markup.
- Note (not a finding): the sentence follows the dropped-edits sentence, not directly after the base text. Brief says "after the existing status text"; this reads as consistent with it.

### Checks run
- Patch applies: `git archive 5443ff6` to scratch/t9a-rev, `git apply --check` then `git apply` -> applied cleanly.
- Focused module: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_guards -v` from the copy -> 5 tests OK. (Loader count is 5, so importing `ImportLinkCase` does not pull its tests in.)
- Pinned fallback: `-m unittest test_studio_live -k legacy_keys_still_import` -> 1 OK.
- Break reproduced (a): in a scratch copy, `namesFamily` without the `LEGACY_FAMILIES` clause -> `test_no_warning_when_no_family_is_lost` FAILS (gotham warned). The mutated html is what the tests loaded (the copy is the cwd the module reads).
- Break reproduced (b): dropped `slot.family &&` from the guard -> the same test FAILS (empty family warned).
- Not re-run by me: the report's other breaks (empty list, no delete, no dedupe, always-false). The empty-list and always-false breaks are plainly caught by the exact-status assertions; I did not re-measure them.
- Regressions: Studio-only change to the import status and `hydrateSlot` arity; `test_studio_roles`, `test_role_routes`, `test_r2_integration` and the full `test_studio_import_link` were not run by me (the report cites import_link 46 OK). Left for the wave gate. Brief-review check found only `test_studio_import_link.py:687,697` asserting the exact status, from library-family exports.
- Processes: I started none that remain; the scratch copies were removed except t9a-rev.

### Strengths
- The row case is handled at the right place: entries are removed after the filter and truncation, so the warning matches the hydrated result.
- Tests assert the exact `#composerStatus` string and the exported family, not a mock.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. `test_the_warning_follows_the_linked_import_status_too` and the plain tests do not cover a mixed case (warning plus dropped-edits sentence), so the ordering after the dropped-edits sentence is unguarded. No verdict depends on it.
2. A nested `row` inside a row child cannot reach the Map as a row (depth 1 hydrates as a text slot), so the `filter(type !== "row")` removal path is not exercised; harmless.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every S08 requirement and Review fix 6 are met in the owned regions, the sentence appears on both import paths, the pinned fallback is intact, and two independent breaks I applied fail the new tests.

---

### Spec Compliance
- PASS: Patch applies. `git apply --check` of task-9-S08.patch then task-9-C2-5c.patch on a temporary index built from BASE 5443ff6 succeeded; stat is fontkit-studio.html and tests/test_studio_guards.py only; worktree index untouched.
- PASS: Req 5 -- `beforeunload` listener calls preventDefault and sets returnValue = "" only when `hasUnsyncedEdits()`, no text (fontkit-studio.html patch hunk after Download listener).
- PASS: Req 6 -- `hasUnsyncedEdits = !ledgerEmpty() && carryKey() !== carriedKey`; fresh and Reset-all covered (test_nothing_held_closes_without_asking_even_after_reset_all).
- PASS: Req 7 -- key taken beside `liveCss()` in writeOverrides and at the start of Copy/Download; marked only after the awaited success (after clipboard write, after execCommand true, after Download click, after the `throw` check in writeOverrides). Auto-sync goes through writeOverrides.
- PASS: Req 8 -- Sync, Copy and Download tests assert edit -> carry -> fresh edit on the same page.
- PASS: Review fixes 2-4 -- no-prompt assertions use the synthetic probe, or a real close waiting on `expect_event('close')` plus `is_closed()`. No dialog handler added to an existing test; existing tests unchanged.
- PASS: Owned regions -- the `live` literal, savedStateEmpty/ledgerEmpty and file end untouched.

### Checks run
- Probe fidelity -> read PROBE and the listener: the probe dispatches a cancelable `beforeunload` on `window` and returns `defaultPrevented`, so it runs the registered handler. No copy of the logic. Pass.
- Probe true / false / true on one page -> test_sync_takes_the_edit_and_a_further_edit_asks_again and test_copy_and_download_each_take_the_edit (both carriers) assert all three; failed-write and mid-write assert true. Pass.
- Real-close no-prompt waits -> `assert_closes_silently` uses `page.expect_event('close')`, `is_closed()`, and filters recorded dialogs. Pass. (Fresh case has no gesture, so a real dialog would not show there anyway; the probe assertion before it carries that case.)
- Nothing unsaved must not prompt -> scratch probe (deleted) on Studio with no Live App (`target=None`, no query): probe false. Composer import of an exported doc: probe false. Library view had no visible checkbox to click, so Library was not exercised; by code, `hasUnsyncedEdits` reads only live.overrides, savedTokens, structure, changes, and ledgerEmpty reads the same, so Library and Composer state cannot raise it. Fresh Studio and Reset-all are in the module.
- Failed-write break (item 3) -> scratch copy of the tree outside the repo, `markCarried(key);` inserted before the `window.fetch` in writeOverrides, copy confirmed to carry it (line 6804), ran test_studio_guards.LeavePromptTests: test_a_failed_write_still_asks FAILS (`False is not true`), 5 others pass. The guard catches the break. Scratch removed.
- Focused runs (worktree the task's worktree, FKS_ENGINES=chromium): test_studio_guards 11 OK; test_studio_roles 114 OK; test_r2_integration 29 OK.
- Not run: test_studio_controls and test_role_routes (the report has 34 and 52 OK); left for the wave gate.

### Strengths
- Probe-based assertions are immediate, deterministic and use the real handler; the one real close is a positive control with a gesture.
- Mid-write test fails under the key-after-response break (report), and the failed-write guard fails under a premature mark (run here).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_guards.py (copy/download test): the clipboard is stubbed with `writeText`, so the `execCommand` fallback line `if (copied) markCarried(key)` is untested. Item 3: a user could plausibly ship the omission (any browser or context without the async clipboard API, then a successful Copy still prompts on close), but the effect is one extra, avoidable prompt, not lost data, and the code at HEAD is correct. A cheap test would set `navigator.clipboard` to undefined and stub `document.execCommand` to return true. Record, not a follow-up.
- tests/test_studio_guards.py (mid-write test): `while not held: page.wait_for_timeout(20)` has no bound; a missing request would hang until the outer timeout. Minor.
- No test opens the Library or Composer with changes through real UI interaction; by code they cannot raise the prompt (see Checks).

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The handler, key timing and carriers match the brief, the tests assert on the real handler with the three-state precondition on one page, and the failed-write break is caught. The only gap is the untested execCommand fallback mark, which is correct in code and costs at most an extra prompt.
