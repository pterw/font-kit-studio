# Task 6 brief: three inspector readouts tell the truth (S01, S02, S03)

Plan Task 6, wave 1, `BASE 5443ff6`, worktree `the task's worktree`. Audit rows S01, S02, S03. Mode code, three patches. Budget: about 70 gross
lines of source (`fontkit-studio.html`) and about 150 of tests. O31 approves New string 13, so S03 does not wait.

## Why

All lines are at BASE (plan lines moved by the Asteria removal).

- S01. `elementHasChanges` (`fontkit-studio.html:7202-7206`) tests `live.changes.structure` (the ledger, filled by this session's moves). After a
  reload a saved DOM move lives only in `live.structure` (entries `{selector, name, ids}`, 3510-3540, 5199), so the check is false. The
  banner says the move is saved, but `refreshControlStates` (7219) disables "Reset this element" with "No changes on this element."
- S02. For `rgba(108,102,118,0.6)`, `liveSeed` (5906-5930) gives `color: "#6c667699"` (`cssColorToHex`, 3727-3740). The text box shows
  that, but `colorInputValue` (3741) cuts it to `#6c6676` for the swatch. The swatch `input` handler (6100-6105) sends
  `event.target.value`, always `#rrggbb`, so a swatch touch writes an opaque colour. `LIVE_COLOR` (3401) already accepts `#rrggbbaa`.
- S03. `liveSeed` returns `1.2` when `lineHeight` is `normal` (5927, `!Number.isFinite(lineNum) ? 1.2`). The field (6050) shows 1.2, and
  the first keystroke writes a value from that invented base. The plan's cause holds at BASE.

## Owned files (exact)

- `fontkit-studio.html`: `elementHasChanges` (7202-7206); the swatch `input` handler and `colourMessage` neighbours (6100-6105);
  `liveSeed` lineHeight line (5927) and the line-height field markup (6050) plus whatever `setLiveControl` (5955-5972) needs to
  show an empty field. No other region (Tasks 7 to 10 and 16 edit the same file at once in their own worktrees).
- New `tests/test_studio_readouts.py`. Do not edit `tests/test_studio_live.py`; its line 408 assertion of `1.2` is for a set line
  height and must stay green.

## Read first

`fontkit-studio.html` 3727-3741, 5906-5975, 6040-6125, 7196-7222; `tests/test_studio_live.py` 44-160 (`LiveCase`, `select`, `export`),
1376-1400 (`ArrangeCase`, `open_arrange`), 3139-3175 (reload plus Reapply). Import the bases as `import test_studio_live as base` and
subclass `base.LiveCase`/`base.ArrangeCase`, so unittest does not collect the old classes twice.

## Requirements

1. S01. After a saved DOM move and a reload, with the moved element selected, `#liveResetTarget` is enabled. Oracle: the literal
   absence of the disabled reason "No changes on this element." and `is_enabled()`. Count `live.structure` entries whose `ids`
   include the id. A page with no override, no ledger entry and no saved move still shows the disabled button (guard).
2. S02. For `computed.color = 'rgba(108, 102, 118, 0.6)'`, setting the swatch (`#liveColor`) to `#112233` sends `#11223399`
   (alpha `0x99` of the seed, same rounding as `cssColorToHex`). Oracle: a literal, `export()['live']['overrides'][id]['color'] == '#11223399'`.
   Typing in `#liveColorHex` stays as the user typed it (typing `#112233` writes opaque). A colour with no alpha is unchanged
   (swatch writes `#rrggbb`). The rule: no edit changes alpha unless the user typed a new alpha. Read alpha from the seeded or last
   acknowledged value (`liveValues(target.id).color`), not from the picker.
3. S03. For `computed.lineHeight = 'normal'`, `#liveLineHeight` has an empty value and `placeholder` `normal` (New string 13, verbatim).
   Nothing is queued or exported until the user types; opening and selecting leaves `export()['live']['overrides']` empty. After the user
   types `1.4`, the export holds `1.4`. A set line height (`24px` at 16px size, or `1.5`) still shows its number (existing 408 test).
   Do not add a line-height default elsewhere; Studio shows what is acknowledged. After an override exists, the field shows that
   number, not the placeholder.

## Tests

All in `tests/test_studio_readouts.py`, one per behaviour, each with a Given/When/Then docstring, run for each engine in `ENGINES`.

- S01 (RED): Given the arrange fixture with a DOM move saved, When the page reloads and the moved card is selected, Then Reset is enabled.
  Fails today because the check reads only the ledger. Guard (GREEN characterization): with nothing saved, Reset stays disabled with
  the reason text.
- S02 (RED): Given a selected target whose computed colour is `rgba(108, 102, 118, 0.6)` (use the `design:select-slot` postMessage as
  `test_studio_live.py` ~400 does), When the swatch is set to `#112233`, Then the export colour is `#11223399`. Fails today: `#112233`.
  GREEN second test: typing `#112233` in the text box exports `#112233`.
- S03 (RED): Given computed lineHeight `normal`, When the target is selected, Then the field is empty with placeholder `normal` and the export
  has no override; When `1.4` is typed, Then the export holds 1.4. Fails today: the value is `1.2`. One realistic break: restoring the
  `1.2` fallback fails the first assertion.

## Focused command

From `the task's worktree`, with a timeout of 600 seconds:

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_readouts test_support -v`

Run one module at a time, no shards, no dev server. Before handing over, also run `test_studio_live`, `test_studio_roles`,
`test_role_routes` and `test_r2_integration`, each alone.

## Patches

One per row, in this order, each with its own tests:

1. `task-6-S01.patch`: `fix(studio): keep Reset enabled for an element with a saved move`. CHANGELOG: `Reset this element stays available
   after a reload when the element has a saved move.`
2. `task-6-S02.patch`: `fix(studio): keep a colour's alpha when its swatch is used`. CHANGELOG: `Moving the colour swatch keeps the
   alpha of a translucent colour.`
3. `task-6-S03.patch`: `fix(studio): do not invent a line height for normal`. CHANGELOG: `An element whose line height is normal shows an
   empty line-height field instead of 1.2.`

`CHANGELOG.md` is controller-owned (Task 18): put these lines in the report's Handoff, do not edit the file. Patch 1 creates the new test
module; patches 2 and 3 append their classes to it.

## Open questions

- None blocking. Recommendation for the shared test module: patch 1 creates it, so the three patches must apply in order.

## Controller rulings

1. Open question: accepted. Patch 1 creates the module, and the three patches apply in the order the brief lists.

## Review fixes (binding: these govern over the text above)

1. Do not use `design:select-slot`: Studio ignores it, and `test_studio_live.py` ~400 exists to prove that. Seed S02 and S03 by setting inline style on a text target in the frame (for example `hero.lead`: `el.style.color='rgba(108, 102, 118, 0.6)'`, `el.style.lineHeight='normal'`), then `frame.evaluate('window.fake.select(id)')`. Each test first asserts the seed arrived: the text box reads `#6c667699`, and the field is empty with placeholder `normal`.
2. S02: after a swatch move the text box `#liveColorHex` mirrors the sent value (`#11223399`), with one assertion. When the acknowledged colour has alpha but `cssColorToHex` returns an empty string (for example `hsla(...)`), no alpha is added; state that limit in the report.
3. S01: the oracle reads the `title` of `#liveResetTarget` and the `[data-hint-for]` hint. Assert first that `export()['live']['structure']` still holds the id after the reload and the banner is visible, so a lost saved move cannot pass for a fixed one.
4. S03: typing goes through `bindNumber` per keystroke, so read the export after the acknowledgement (wait for the `Live . rev N` badge), not right after `type`.
5. The `liveSeed` span is 5914-5934 at BASE. Task 7's `familyOptions` edit at 6046 sits four lines from your markup edit at 6050: stay on your lines.

---

# Task 6 follow-up: an unmoved element stays disabled

The worktree `the task's worktree` holds Task 6's finished work, unstaged. Keep it. See the Minor in `task-6-code-review.md`.

**Finding.** Nothing tests that an element outside every saved move keeps Reset disabled after a reload. Changing the S01 check to "any saved move enables Reset" passes every test.

**Do this.** Extend the existing S01 test in `tests/test_studio_readouts.py` with one more step, not a new test: after the reload, select an element that has no saved entry, and assert `#liveResetTarget` is disabled. Assert first that this element's id is not in `export()['live']['structure']`.

Show the break failing: change the S01 check to "any saved move", run the test, show it fails on the code the test loaded, then restore. Touch only that test file. Run `test_studio_readouts` once. Do not write a patch: the controller regenerates the row patches from the worktree. Append to the REPORT what changed, the test count and the break shown.
