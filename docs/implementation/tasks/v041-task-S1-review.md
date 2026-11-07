# Task S1 review (BASE 5bd655e, tree a scratch folder, patch staged; labels stay 0.4.0)

Verdict: APPROVED WITH FIXES (two small test-only edits; no product-code change). In the template's words: Task quality = Needs fixes.

### Spec Compliance
- PASS: Preset gone. `compositionPreset` offers rowdemo, blank; `asteria` key removed; unknown key still falls back to rowdemo (fontkit-studio.html:2491, unchanged). test_studio_live asserts option values ['rowdemo', 'blank'] (patch 534-535).
- PASS: Palette renamed in the brief's order; all 11 hex values and all 5 defaults (2212, 2227, blank, rowdemo, state.background) match the table (patch 46-56, 82, 91, 115, 124, 133). `LEGACY_COLOR_NAMES` pairs match the O9 table pair for pair (patch 60-71).
- PASS: Behaviour 3. One Map lookup `currentColorName` (`.get(name) ?? name`, so `constructor` stays). It runs in `hydrateSlot` after `slot.align`, before the colour-source check, for every slot type and every source (2467); row children go through `hydrateSlot(child, 1)` (2431); the background is covered in `importCompositionJson` after its string defaults (3293). `Asteria` is in the product file only in those 11 lines, under a one-line comment. No UI shows it.
- PASS: Behaviour 4: Nonesuch and constructor export unchanged; render is the BASE rendering (test at dead_controls 369-387).
- PASS: Real 0.4.0-shaped file. I took a BASE-page (5bd655e html) export, set the background to source saved / Asteria Vesper and every non-row slot to colorSource saved with rotating old names, and imported it into BASE and into HEAD (copies in scratch). Computed colours of the canvas and all 5 slots are identical; the HEAD export equals the BASE export once the 11 names are renamed, apart from random slot ids; HEAD export holds 0 "Asteria". (S1-rev-shape.py / S1-rev-shape-head.py, outputs S1-rev-shape-*.json.)
- PASS: Fixture shows `Sample`; CHANGELOG bullet is verbatim from the brief, under `## [Unreleased]` / `### Changed`, no "Asteria"; no dated entry touched.
- PASS: Scope. 7 files, all in the brief's Touches list. No version label, export format, bridge or doc change (the only "0.4.0" strings added are in a code comment and two test docstrings, not labels). CRLF kept in all 7 files (LF-only line count 0 at BASE and in the index). `git diff --cached --check` clean.
- PASS: Anti-pattern 15: no PID, port or process state in the diff (grep of the added lines).
- PASS: Moves per the table (dead_controls 21,77-80,93,110-114,168,234; import_link 50,83-86,204,294,308,407,421,436,521,533; live 2407,2411; roles 2304-2307). Cancel/Accept at dead_controls 244/249 select rowdemo as the brief says; roles 2304-2307 is blank then rowdemo.
- PASS with note: the report lists the extra late-ack test changes (bring_to_front, polling=50, mono wait, viewTargetApp) as concerns; assessed below.

### Checks run
All against copies under WORKSPACE/scratch (S1-rev-*, built from the staged tree; never the worktree). Runner S1-rev-run.py prints the SHA of the html it serves, whether the mutation marker is in that file, and `support.HTML` of the copy (it resolves to the copy's own fontkit-studio.html), so the mutated file is what the test loaded.
- Late-ack test still proves its behaviour -> mutant "protection removed in recordCanonical" (`if (op.importSuperseded)` -> `if (false)`, html sha 034a90d9a3ec) x10 each of the 2 late-ack tests -> 20/20 FAIL, failing on `--font-display: "Inter"` not found in the CSS, where the page's Fraunces/JetBrains had become the saved state. That is the behaviour the test names.
- Mutant "mark in endCompositionLink removed" (3229, sha eff99c1f0750) -> without-live-field test 10/10 FAIL; with-live-field test 10/10 PASS. Expected, not a gap: with a `live` field `supersedeLiveOpsForImport` (3254) marks the same op, so that path is protected twice and only the recordCanonical mutant reaches both tests.
- Unmutated tree, same two tests x10 -> 20/20 PASS. Every run was killed or passed every time; no intermittent kill.
- Is `polling=50` real? -> removed it (variant no_polling) -> both tests hang to 32 s and error. Probe (S1-rev-probe.py): after the click on #viewSpecimenCanvas the Live App iframe's parent is display:none, 0x0, and `requestAnimationFrame` in that frame never fires (500 ms), while in the Live App view it does. So the default raf polling of `frame.wait_for_function` cannot run once the test leaves the Live App view. The reason is real (the new flow must be in the Specimen view to click a slot); it hides no defect. The race is not hidden: `fake.hold = true` is set before the edit, the held ack is released only after the import, and the protection mutants fail on exactly the late-ack assertion.
- Is `bring_to_front` real? -> removed (no_front) x10 each: 19/20 pass, one 31 s timeout. A hedge against an intermittent hang, justified; keep it.
- Is the new mono wait needed? -> removed (no_monowait) x10 each -> 20/20 pass. It is redundant: the fake logs the message and applies its tokens in the same synchronous handler (fake-target.html:529-533), so `wait_composition_updates(frame, 2)` already implies the ledger holds JetBrains Mono, and the `assertIn('"JetBrains Mono"', before_import['--font-mono'])` right after states the precondition. It does not wait past the race (the ack is held). Minor only.
- Does the moved 77-80 test still fail for other breakages? -> mutant "applyCompositionPreset skips renderComposer()" (S1-rev-mutA) -> `test_choosing_a_preset_applies_it_without_pressing_apply` PASSES (see Important 1). At BASE the same mutant fails it through the canvas-background check.
- Are `Object.hasOwn`/Map semantics tested? -> mutant `Object.fromEntries(map)[name] || name` -> KILLED (constructor case). Mutant "skip for non-text slots" (`type === "text"` only) -> KILLED (rule/image cases). Per-type mutants (rule only, image only) were not run; the non-text mutant above covers both together.
- Is the "whatever the colour source" rule tested for the background? -> mutant `if (background.source === "saved") background.saved = ...` (S1-rev-m-bggated, sha bf6e90e161) -> SURVIVES the whole SavedColourNameTests class (see Important 2). With the fix below added the mutant is killed (AssertionError '' != 'Ice White') and HEAD passes.
- Mapping typos per name -> mutants Haze->Midnite, Vesper->Lavender, Abyss->Ink Black, Mist->Slate Mis all SURVIVE; Void->Deep Navy is killed. The 4 names never appear in any test (Minor 1).
- CRLF / scope / sweep -> `git diff --cached --stat`, `--check`, CR counts, `git grep -in asteria` -> as in Spec Compliance.
- Focused suite not rerun (report carries it; landing gate runs the rest).

### Strengths
- The late-ack test keeps both assertions the brief names and is killed 20/20 by the real protection mutants; the rebuilt state (edit Metadata to jetbrains-mono through the UI) keeps before and imported tokens different on both axes.
- `currentColorName` is a Map with `??`, placed once in `hydrateSlot` and once for the background; the row children rely on the existing recursion, with no second copy.
- The new test class types the new names and hex values itself rather than reading the page, and has a palette-order test over all 11.
- Real-shape file round trip is identical at the pixel level and in the export.

### Issues
#### Critical
None.

#### Important
1. tests/test_studio_dead_controls.py:76-83 (`test_choosing_a_preset_applies_it_without_pressing_apply`, brief row "77-80") -- weakened. Its only evidence is `#slotCount` and the select value, and `slotCount` is set in `syncCompositionControls()` before `renderComposer()` runs (fontkit-studio.html:2496-2497, 2526). A preset that updates state and the controls but never repaints the canvas passes the test; at BASE the canvas-background check caught that. (Other tests in the class do fail on that mutant, but this test's own name, "applies it", loses its rendering proof.) The brief allowed "and/or the canvas"; the "do not weaken" rule governs, and the canvas evidence was cheap. Fix: after each of the three `slotCount` assertions at lines 76, 79 and 83 add the matching rendered count (4, 5, 4), for example

   ```
   self.assertEqual(page.locator('#composerCanvas > .flow-slot').count(), 4)
   ```
   after line 76, `... 5)` after line 79, `... 4)` after line 83. Probe: the selector counts 4 on rowdemo and 5 on blank, and 0 on the no-render mutant, so the assertion fails exactly there. The same assertion can be added after line 114 (`'5'`) for the accepted-replace test.
2. tests/test_studio_dead_controls.py:262-284 (`SAVED_NAME_CASES`) -- the background case set only has `source: "saved"`. The brief says the lookup applies "whatever the colour source", and a 0.4.0 export carries the old name in `background.saved` with source custom in almost every file (the default). A lookup gated on the background source survives all four tests while leaving "Asteria Starlight" in the export and an empty Saved selection. Fix: add this case before the `'a rule slot'` row (line 275), CRLF line endings:

   ```
       ('the background of a file whose colour source is custom', 'Asteria Starlight', 'Ice White', 'rgb(245, 241, 232)',
        [{'type': 'text', 'role': 'Body', 'text': 'Probe'}],
        {'source': 'custom', 'saved': 'Asteria Starlight'}, CANVAS, 'background-color', False),
   ```
   Verified in scratch: passes on HEAD, fails against the background-gated mutant.

#### Minor
1. The new import test covers 7 of the 11 old names (Void, Starlight, Gold, Verdant, Tender, Serene, Electric); a typo in the Map value for Haze, Vesper, Abyss or Mist is not caught (four mutants survive). The brief asked for two names, so this is not a defect against it; a loop over all 11 on one slot each (or one text slot per name) would close it cheaply.
2. tests/test_studio_import_link.py:432 -- the added `--font-mono includes "JetBrains Mono"` wait is redundant (20/20 pass without it) and the next lines assert the same thing; harmless. Keep or drop. If kept, the comment on line 424 is the only explanation; no comment says why the wait polls (the Live App iframe is hidden in the Specimen view, so raf never fires). Suggested comment above lines 402 and 432: `# polling=50: in the Specimen view the Live App frame is hidden and runs no animation frames`.
3. Report says "clicks time out without bring_to_front"; measured: 1 of 20 runs times out, so it is an intermittent hang, not constant. The change is right.

### Plan-mandated (for the owner)
- [Minor] import_link 294/308 "A" is now `blank` (Inter), so `assert_b_is_saved`'s `assertNotIn('Inter')` cannot tell a leaked A from B's own text if B uses Inter -- brief requires: "`asteria` becomes `blank`; ... `assert_b_is_saved` still catches a leaked A through `assertNotIn('Inter')`. Report which assertions become weaker for A." Reported by the implementer; not an implementer defect.

### Source conflicts (for the controller)
- None found. Note only: the brief's table row for 77-80 permits "`#slotCount` ... and/or the canvas", while its text says "Do not weaken a test" (Important 1); the implementer chose the weaker allowed option.

### Assessment
**Task quality:** Needs fixes (verdict word: Approved with fixes)
**Reasoning:** The product change is correct and complete (Map lookup reached by every slot type, row children and the background; real 0.4.0-shaped file renders and exports identically; scope, line endings and changelog as briefed), and the late-ack test was strengthened, not weakened, by its rebuilt state: the protection mutants fail it 20/20 and `polling=50` is needed because the Live App frame is hidden in the Specimen view. Two test gaps remain that the tests do not catch: the preset-select test no longer proves a repaint, and no case covers an old name on a non-saved background; both fixes above are three lines each and verified in scratch.

STATUS: COMPLETE


## Re-review

Scope: the r2 fix round only, comparing `task-S1-code.patch` with `task-S1-code-r2.patch` (BASE 5bd655e, tree `a scratch folder`).

**Verdict: Approved**

### Checks run
- Product code unchanged: `sha256` of `fontkit-studio.html` is `596e4184...cf27`, the value the report gives before and after every mutant. The staged diff is byte-identical to `task-S1-code-r2.patch`. The r1 to r2 diff touches only `test_studio_dead_controls.py` and `test_studio_import_link.py`.
- No assertion weakened: in `test_studio_dead_controls.py` the r1 to r2 diff is additions only. In `test_studio_import_link.py`, A changed from the `blank` preset to a UI family edit (`space-grotesk`), and the queued edit at line 308 changed from `rowdemo` to `dm-sans`, which avoids the replace-confirm. No assertion was removed, and `assert_b_is_saved` gained `assertNotIn` checks for `Space Grotesk` and `DM Sans`.
- Line endings: both test files are fully CRLF (747 of 747 and 1042 of 1042 lines). `git diff --cached --check` is clean.
- Focused run, foreground: `PYTHONPATH=tests python -m unittest test_studio_dead_controls test_studio_import_link` gave `Ran 77 tests in 125.966s OK`.
- Mutants, on copies outside the repo; each log prints the mutated sha and that `support.HTML` resolves to the copy.

| Mutant | Result |
|---|---|
| Background lookup gated on `source === "saved"` | Killed: `AssertionError: '' != 'Ice White'` |
| Wrong mapping: Haze to Midnite | Killed: painted `rgb(0, 0, 0)` for `rgb(11, 16, 34)` |
| Wrong mapping: Vesper to Lavender | Killed: painted `rgb(184, 162, 218)` for `rgb(144, 157, 208)` |
| Wrong mapping: Abyss to Ink Black | Killed: painted list differs |
| Leaked A: `if (op.importSuperseded) {` in `recordCanonical` changed to `if (false) {` | Killed: both the 294 and 308 tests fail |
| `applyCompositionPreset` skips `renderComposer()` | Killed: `test_choosing_a_preset_applies_it_without_pressing_apply` fails with `0 != 4` |

### Rulings
Important 1, Important 2, all 11 old names, and the `import_link` weakness are met. Minor 2 is left as ruled. The `bring_to_front` sentence is corrected.

### Issues
None (Critical 0, Important 0, Minor 0 new).

STATUS: COMPLETE
