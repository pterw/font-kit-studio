# Task 16 brief: neutral default copy in Studio (G2-18)

Plan Task 16, wave 2, BASE `5443ff6`, worktree `the task's worktree`, audit row G2-18 (the text half only), mode code. Budget: about 40 gross
lines (about 6 in `fontkit-studio.html`, about 30 in one new test class). Constraints: `../constraints.md` rules 1-9 and O31 (New string 12
approved as written, 2026-11-06). One patch, one commit.

## Why

A fresh Studio shows copy from the repository Studio was written in. At BASE, `fontkit-studio.html:1053` sets the specimen field to
"The sky remembers what we forget."; `:2148` and `:2149` give `Display` and `H1` the text "Every life is a night sky."; `:2156` gives
`Metadata` "SEP 17 · 24 MOMENTS · OTTAWA". Cause re-read at BASE and it still holds. The plan's line numbers (1051, 2131-2141) have moved by
+2 and +15; use the BASE lines here. Search at BASE for "night sky", "sky remembers", "OTTAWA", "MOMENTS" finds only `fontkit-studio.html`
(these four lines), the dated protocol document (`font-kit-studio-v0.2.0-design-bridge-protocol-v1.md:160`), the plan, and the v0.2 evidence
JSON. None is in `tests/`. A search of `tests/`, `fontkit-bridge.js` and `scripts/` for every other default (`BRAND`, "Things worth
remembering", "September observations", "Some moments refuse", "only in retrospect", "Figure 01", "Custom specimen text", "Write down one
small") finds no test that asserts a ROLE_DEFAULTS text (`BRAND` in `tests/test_studio_live.py:4354` is an unrelated token dict).

## Owned files (exact)

- `fontkit-studio.html`: line 1053 (the `sampleText` input `value`), and lines 2148, 2149, 2156 inside `ROLE_DEFAULTS` (2146-2159). Nothing
  else. The `#030409` canvas colour is not in this task (the colour-rename PR owns it; `tests/test_studio_dead_controls.py:21` pins
  `rgb(3, 4, 9)`). Do not touch `BRAND`, `Wordmark`, `H2`, `H3`, `Lead`, `Body`, `Accent`, `Caption`, `Code`, `Custom`: the plan approves
  replacements for three strings only (New string 12), and those other texts are not another product's name or place.
- Tests: put the new class in `tests/test_studio_first_run.py` as a new class inserted directly after its nearest
  related test (the one that loads a fresh Studio), never at the end of the file. If that module has no fresh-load test to sit after, use
  `tests/test_studio_controls.py` the same way and say so in the report.
- Everything else is read-only. Other tasks change `fontkit-studio.html` at the same time in their own worktrees (Addendum 1), so stay in
  these lines.

## Read first

- `fontkit-studio.html` at BASE: 1050-1054; 2146-2159; 2184-2200 (`makeTextSlot`, takes `def.text`); 3015-3025 (role change copies
  `def.text`); 1495 (`sampleInput`, how the field feeds the specimen).
- Locate, with grep, where an imported or saved composition sets a slot's text (the import path), to confirm the saved text overrides the
  default. Report the line.
- `tests/test_studio_first_run.py` and `tests/test_support.py` for the page-launch helpers.

## Requirements

1. The `sampleText` field's initial value is exactly `The quick brown fox jumps over the lazy dog.` Oracle: the literal, read with
   `input_value()` on a fresh load. Observer: the specimen field a user sees.
2. `ROLE_DEFAULTS.Display.text` and `.H1.text` are exactly `Type something worth reading.` and `Metadata.text` is exactly
   `JAN 01 · 24 ITEMS · ANYWHERE` (U+00B7 middle dots, as the old line had; keep the file's existing encoding). Oracle: the literals above;
   observe the text of a slot made from each role (add a `Display`, an `H1` and a `Metadata` slot through the UI, or switch an existing
   slot's role, and read the slot's text field).
3. No other default text, size, element or style changes. Oracle: the Body, Lead and Caption slot texts keep today's literals (read in the
   same page run).
4. A saved composition that carries the old text loads with that text unchanged (the saved text wins). Oracle: import a minimal
   composition whose text slots contain "Every life is a night sky." and "SEP 17 · 24 MOMENTS · OTTAWA"; the slot text fields show those
   exact strings. This already works; it is a characterization, not a RED.
5. After the edit, `git grep -n -E "night sky|sky remembers|OTTAWA|MOMENTS" -- fontkit-studio.html` prints nothing.

## Tests

One new class, `FreshStudioDefaultCopy`, two tests, each with a Given/When/Then docstring.

- `test_fresh_studio_shows_the_neutral_copy` (RED before the fix: the field reads the old sentence, the Display slot the old text). Given a
  freshly opened Studio, when a Display, an H1 and a Metadata slot exist and the specimen field is read, then the field and the three slot
  texts equal the New string 12 literals and a Body slot text is still its old literal. Break shown failing: restore the old Display text.
- `test_saved_composition_keeps_its_old_text` (GREEN characterization, passes before and after). Given a composition file whose text slots
  carry the old sentences, when it is imported, then the slot fields show those sentences. Break shown failing: make the importer prefer
  `ROLE_DEFAULTS[role].text` over the saved text.

Run the RED step first on the unedited tree and keep its output; do not manufacture RED for the second test.

## Focused command

From `the task's worktree`, bounded:

`timeout 300 env PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_first_run test_support -v`

Then one module at a time, each with its own timeout: `test_studio_roles`, `test_role_routes`, `test_r2_integration` (landing always runs
these three). No shards, no dev server.

## Patches

One patch, `task-16-code.patch`. Commit subject: `fix(studio): use neutral default copy`. CHANGELOG line (controller adds it under
Unreleased in Task 18): "Studio's default specimen text is now neutral; saved compositions keep their text."

## Open questions

1. Where the new class goes if `test_studio_first_run.py` has no fresh-load test: recommend `test_studio_controls.py`, the nearest module that
   opens a fresh page. Not blocking.
2. The `rowdemo` preset may carry its own slot texts, so a fresh start may not show `Display` text at all. If so, requirement 2 is observed
   by adding a role slot, as written above. Not blocking; the implementer reports what `rowdemo` shows.

## Controller rulings

1. Open question 1: yes, tests/test_studio_controls.py if test_studio_first_run.py has no fresh-load test.
2. Open question 2: as the brief does, add role slots and read their text.

## Review fixes (binding: these govern over the text above)

1. Put the class `FreshStudioDefaultCopy(LiveCase)` in `tests/test_studio_first_run.py`, directly after `NoDemoOfferTests`. Do not use `tests/test_studio_controls.py`.
2. There is no control to add a slot by role. The first slot is selected on load: use `#slotInspector [data-bind="role"]` `select_option('Display')`, then read `[data-bind="text"]`, and repeat for H1, Metadata, Body, Lead and Caption.
3. A fresh Studio opens on `rowdemo`, which shows the Metadata default but no Display. Add an assertion on the fresh canvas's Metadata text before any role switch, and correct the Why sentence in your report.
4. Helpers are in `tests/support.py`. Add `test_font_kit_studio_v011` to the run list, because the longer sample renders at narrow widths. Apply the remaining Minor items in `task-16-brief-review.md`.
