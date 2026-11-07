# Task 6 code report (S01, S02, S03)

Mode code, BASE 5443ff6, worktree the task's worktree, nothing committed or staged (only `git add -N` on the new test module).
Patches in , ordered, each on the one before (checked: all three apply in order to a BASE copy and give the same fontkit-studio.html):
`task-6-S01.patch`, `task-6-S02.patch`, `task-6-S03.patch`.

## Changes
- `fontkit-studio.html` (about 12 lines): `elementHasChanges` also checks `live.structure` ids (S01); the swatch `input` handler
  appends the alpha byte of `cssColorToHex(liveValues(id).color)` when that is `#rrggbbaa`, and the text box mirrors the sent value (S02);
  `liveSeed` returns `""` for a non-finite line height and the field has `placeholder="normal"` (S03). `setLiveControl` needed no change:
  it already writes `""`.
- New `tests/test_studio_readouts.py` (S01 patch creates it; S02 and S03 append): `ResetAfterReloadTests` (2), `ColourAlphaTests` (3), `LineHeightNormalTests` (2).
  Seeding follows Review fix 1 (inline style on hero.lead, then `fake.select`), each test asserting the seed arrived first.

## RED (each with the fix absent; the browser loads the working-tree HTML, so the mutated code is what ran)
- S01: `AssertionError: False is not true` at `reset.is_enabled()`; the earlier saved-move and banner assertions passed.
- S02: `AssertionError: '#112233' != '#11223399'`.
- S03: `AssertionError: '1.2' != ''` at the empty-field assertion.
GREEN after each fix: `test_studio_readouts` 7 tests OK (chromium).

## Focused runs (chromium, each alone)
test_studio_readouts 7 OK; test_support 34 OK; test_studio_live 152 OK; test_studio_roles 114 OK; test_role_routes 52 OK; test_r2_integration 29 OK.

## Notes
- S02 limit: when the acknowledged colour has alpha but `cssColorToHex` returns "" (for example `hsla(...)`), no alpha is added and the swatch writes opaque.
- Not shown failing: the alpha-less swatch test and the 24px line-height test are guards (green before and after).
- A byte-compare of the test module after `git apply` against the worktree differed (probably CRLF conversion in `git apply`/autocrlf); the HTML matched exactly.
- Nothing outside the owned regions was touched; `tests/test_studio_live.py` unchanged.
- Did not run pre-commit or `mutate.py` (dispatch rules).

## Handoff (CHANGELOG lines, Task 18)
- S01: Reset this element stays available after a reload when the element has a saved move.
- S02: Moving the colour swatch keeps the alpha of a translucent colour.
- S03: An element whose line height is normal shows an empty line-height field instead of 1.2.

## Follow-up (an unmoved element stays disabled)
- Changed only `tests/test_studio_readouts.py`: the existing S01 test `test_reset_stays_enabled_for_an_element_with_a_saved_move_after_a_reload`
  gained a final step: after the reload it asserts `hero.lead` is not in `export()['live']['structure']`, selects it, and asserts `#liveResetTarget` is disabled.
- Count: `test_studio_readouts` 7 tests OK (unchanged count, no new test), chromium, run alone.
- Break shown: `elementHasChanges` changed to `|| live.structure.length > 0` (any saved move). The test failed at the new
  assertion, `AssertionError: True is not false` (`self.assertFalse(page.locator('#liveResetTarget').is_enabled())`), on the mutated HTML the browser loaded.
  Restored the original line; rerun 7 OK. No patch written (per brief).
