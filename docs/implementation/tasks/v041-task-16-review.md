### Spec Compliance
- PASS: New string 12 is verbatim. Plan (`scratch/t1revB/docs/plans/2026-11-06-v0.4.1-repairs.md:491-492`) gives `Type something worth reading.` (Display, H1), `The quick brown fox jumps over the lazy dog.` (field), `JAN 01 · 24 ITEMS · ANYWHERE` (Metadata). The patch has exactly these at fontkit-studio.html:1053, 2148, 2149, 2156. The Metadata line holds one U+00B7 pair in UTF-8 (byte check on the added lines).
- PASS: Requirement 3 / owned regions. The html diff is 4 changed lines (8 +/- lines), only those four. BRAND, H2, H3, Lead, Body, Accent, Caption, Code, Custom are untouched.
- PASS: Canvas colour untouched. `#030409` still at fontkit-studio.html:1171 and :2117 in the worktree, and the patch has no `030409` hunk.
- PASS: Requirement 5. `git grep -E "night sky|sky remembers|OTTAWA|MOMENTS" -- fontkit-studio.html` prints nothing at the worktree.
- PASS: Requirement 4 / saved text wins. `hydrateSlot` builds `{ ...base, ...leaf, type, id, assetDataUrl }` (fontkit-studio.html:2444), so a saved `text` overrides `makeTextSlot`'s default. Confirmed by the break below.
- PASS: Review fixes. The class is `FreshStudioDefaultCopy(LiveCase)` directly after `NoDemoOfferTests`. It switches roles through `#slotInspector [data-bind="role"]`. It asserts the fresh canvas Metadata before any switch. The report's Why sentence is corrected (rowdemo has Metadata but no Display).
- PASS: Patch applies. `git diff | git apply --check -R` passes in the worktree. The diff holds two files, no stray file. The commit subject in the handoff is `fix(studio): use neutral default copy`.
- Size: about 8 html lines and 52 test lines against a budget of about 6 and about 30. The test overrun is the Review-fix assertions (canvas Metadata, Lead and Caption, six roles). Not a defect.

### Checks run
- Focused module -> `cd the task's worktree && timeout 300 env PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_first_run.FreshStudioDefaultCopy -v` -> 2 tests OK. I did not re-run the Studio regression modules (the implementer ran them: roles 114, role_routes 52, r2_integration 29, v011 20); the wave gate keeps them.
- Break, saved text wins -> scratch copy `scratch/t16-review/` (html, tests, root files copied; worktree untouched). I changed fontkit-studio.html:2444 to `{ ...base, ...leaf, text:base.text, ... }`, confirmed by grep that the copy holds `text:base.text`, and ran the class. `test_saved_composition_keeps_its_old_text` FAILED: `'Every life is a night sky.' not found in ['Type something worth reading.', 'JAN 01 ... ANYWHERE', ...]`. The failure output shows the mutated importer's result, so the page loaded the mutant. Test 1 was not affected.
- Encoding risk -> `file` on the html shows UTF-8 with CRLF (as at BASE), and the added line holds the UTF-8 middle dot. The test file is UTF-8; git's CRLF warning concerns only the working copy.
- Fail-closed / stray state -> no process of mine is left running. Scratch lives under `scratch/`.

### Strengths
- Test 1 reads the canvas through `textContent`, not `inner_text`, so the uppercase transform on Metadata does not hide the literal. It also reads the Body, Lead and Caption defaults, so a stray change to those fails it.
- Test 2 imports a real exported document (`export` then `import_document`) with only two texts edited, so it exercises the real importer, not a hand-built fixture.
- Both tests assert `errors == []`.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_first_run.py:~66: the `assertIn` on the canvas Metadata would also pass if the rowdemo preset one day carried its own Metadata text equal to the literal. That is benign: it is the intended observation.
- Test 1 pins Body only to its first 30 characters. A change to the tail of the Body default would pass. Recorded, no fix needed.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The four default strings match New string 12 verbatim, nothing outside the owned lines changed (canvas colour included), and saved text still wins at hydrateSlot. The new class passes, and a mutated importer that prefers the default made the characterization test fail.
