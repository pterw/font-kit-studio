# Task 16 code report (mode code, BASE 5443ff6)

Changed: `fontkit-studio.html` (lines 1053, 2148, 2149, 2156 only: sample field, Display, H1, Metadata) and
`tests/test_studio_first_run.py` (new class `FreshStudioDefaultCopy(LiveCase)` directly after `NoDemoOfferTests`).
Patch: `task-16-code.patch` (`git apply --check -R` passes). Nothing committed or staged.

Why, corrected (Review fix 3): a fresh Studio opens on `rowdemo`, which shows the old Metadata default and the old sample sentence,
but no Display; Display and H1 defaults appear only after a role switch or on the blank preset.

Import path: `hydrateSlot` (`fontkit-studio.html:2444`, `{ ...base, ...leaf }`) lets saved `text` override the default.

## Tests
- RED (unedited tree): `FreshStudioDefaultCopy` -> test 1 FAIL `'The sky remembers what we forget.' != 'The quick brown fox...'`;
  test 2 passed (characterization, no RED made).
- GREEN after edit: 2 tests OK.
- Break, test 2 (after the fix, `text:base.text` added at :2444, Display/Metadata in the saved file): FAIL `'Every life is a night sky.' not found in
  ['Type something worth reading.', 'JAN 01 ... ANYWHERE', ...]`. The failure shows the mutated importer's output, so the page loaded it. Restored.
- Break, test 1 (Display restored to the old text): FAIL `'Every life is a night sky.' != 'Type something worth reading.'`. Restored.
- Test 1 reads the canvas Metadata (`.slot-text` textContent, since inner_text applies the uppercase transform) before any role switch, then
  switches the selected slot to Display, H1, Metadata, Body, Lead, Caption via `#slotInspector [data-bind="role"]`.
- Focused runs (chromium, one module at a time): test_studio_first_run 26 OK; test_support 34 OK; test_font_kit_studio_v011 20 OK;
  test_studio_roles 114 OK; test_role_routes 52 OK; test_r2_integration 29 OK.
- `git grep -n -E "night sky|sky remembers|OTTAWA|MOMENTS" -- fontkit-studio.html` prints nothing.

No test outside the brief broke. No gate run, no mutate.py, no pre-commit (per dispatch). Nothing outside the owned regions.
The test file shows a CRLF warning from git for the working copy; the diff is 52 added lines only.

## Handoff
- Commit subject: `fix(studio): use neutral default copy`
- Body draft: A fresh Studio carried copy from the repository it was written in. The sample field, Display, H1 and Metadata defaults
  are now neutral; saved compositions keep their own text (hydrateSlot).
- CHANGELOG (Task 18, Unreleased): "Studio's default specimen text is now neutral; saved compositions keep their text."
