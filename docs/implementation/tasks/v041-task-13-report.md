# Task 13 code report (C2-8b, state classes in selectors)

Mode code, BASE 5443ff6, worktree the task's worktree. Nothing committed. Patch: task-13-code.patch (2 files, +76/-1).

## Changed
- `fontkit-bridge.js`: new `isStateClass(cls)` directly before `selectorStep`; `selectorStep` filters classes through it.
  Predicate: `/^(is|has)-|-active$/` plus the set `active, selected, current, open, show`. `hidden` and `disabled` are not state classes.
  Role selectors, `computeSelector`, `roleBindings` untouched.
- `tests/test_bridge_runtime.py`: `StateClassSelectorTests` after `StableSelectorEscapeTests`, two tests.
  Test 1 puts `has-x` on main, `is-active` on section.cards, `tab-active` on Card two's article, `open` on its h3; asserts none is in the
  reported or applied selector; flip = remove all four and insert a new `section.cards.is-active` AFTER the first section (insert, not clone,
  so nth-of-type indexes stay); asserts `querySelectorAll(selector)` is 1 element with text "Card two".
  Test 2 puts `disabled` on Card one's article and a `div.hidden` wrapper (with an h4) after the cards; asserts the two literals
  (line 309 and nav) plus `article.card.disabled` and `div.hidden` retained.

## Tests
- `PYTHONPATH=tests FKS_ENGINES=chromium timeout 600 python -m unittest test_bridge_runtime.StateClassSelectorTests test_support`: Ran 36, OK.
- `test_bridge_runtime test_support`: Ran 164, OK (all existing literals pass).
- Mutations, each loaded by the test run (file edited, then restored; verified by `git diff --stat`):
  - class map unfiltered: test 1 FAIL
  - `-active$` removed: test 1 FAIL
  - `has` removed from prefix rule: test 1 FAIL
  - set removed (`false`): test 1 FAIL
  - `hidden` added to the set: test 2 FAIL
  (RED at BASE equals the unfiltered mutation.)

## Requirement 5 (read only)
Read `structureHeld` (fontkit-studio.html:3588) and the reconnect path; Studio not changed.

## Handoff
CHANGELOG line, Unreleased/Fixed: "Exported selectors no longer carry state classes such as `is-active`, so a pasted rule still matches after the page toggles them."
Commit subject: `fix(bridge): leave state classes out of exported selectors`.
Known limit: a saved 0.4.0 DOM move whose container selector held a state class cannot be reapplied. Reapply is refused as a whole
(`failReapply`, nothing sent); the fix is to redo the move. On import the heading is "Imported state differs from the Live App."
Also: the dom-path fallback goes through `computeSelector`, so its output changes on pages with state classes (intended).
`has-*` also drops `has-durations` (ruling 1); uniqueness stays guaranteed by nth-of-type.
Git warns LF->CRLF on fontkit-bridge.js (autocrlf only); no content change beyond the hunk.
