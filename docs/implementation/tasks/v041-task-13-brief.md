# Task 13 brief: exported selectors leave state classes out

Plan task 13, wave 2, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit row C2-8b (one row, one patch). Budget: about 70 gross
lines (about 15 in the bridge, about 55 in tests), plus one CHANGELOG line.

## Why

`selectorStep` writes every class of the target and of each ancestor (`fontkit-bridge.js:3268-3275` at BASE). A selector built while a
page toggle holds `.is-active` therefore contains it. After the page's own pill switch moves the class, the exported rule matches
nothing, and no warning says so. The audit's run: after the mode switch the visible heading read 33.86 px again (C2-8b). The cause
holds at BASE: `computeSelector` (3220-3266) calls `selectorStep` for every node up the chain, and the uniqueness loop (3256-3262)
tries the last 4 steps and extends up to the whole chain. `nth-of-type` in every step already keeps the full chain unique, so no
new fallback code is needed; the loop is the fallback.

The audited ScrobbleScope templates (read-only, `the app's templates` and `static`) use
`is-active` (11 hits), `tab-active` (11), `btn-active` (5) and `heatmap-stage-active` (4), and `has-durations` once. So the `-active`
suffix rule applies.

## Owned files (exact)

- `fontkit-bridge.js`: `selectorStep` (3268-3275) and one small helper placed directly before it. Nothing else. Do not touch
  `computeSelector`, `roleBindings` (1915-1968; its `.class` binding step at the `for (const name of shared)` loop is Detect's own
  role selector and stays as is), or the `computeSelector(el)` call in the `dom-path` step.
- `tests/test_bridge_runtime.py`: one new class inserted directly after `StableSelectorEscapeTests` (ends before `class
  AssetPlacementTests`, 1680 at BASE). Do not edit existing tests.
- `CHANGELOG.md`: one line under `[Unreleased]`.

Everything else is read-only. Other tasks edit `fontkit-bridge.js` and the test module in their own worktrees; stay in these regions.

## Read first

- `fontkit-bridge.js` 3208-3282 (`uniqueSelector`, `computeSelector`, `selectorStep`); 862-882 (class mutations bump `domVersion`,
  so the selector cache is rebuilt after a class flip).
- `tests/test_bridge_runtime.py` 51-146 (harness), 305-313 (the literal selectors of a plain page), 1650-1678 (model test).
- `tests/fixtures/bridge/target.html` (`section.cards > article.card`). Reuse it; do not add a fixture.

## Requirements

1. **State classes are dropped from every step** (target and ancestors). Final list, from Decision 5 and the audited templates: exactly
   `active`, `selected`, `current`, `open`, `show`, any name starting `is-` or `has-`, and any name ending `-active`. Not `hidden`, not
   `disabled`. Implement as one small predicate (one regex plus a set), applied in `selectorStep`'s class map. Oracle: the three
   tests below. Record this list in your report.
2. **Dropped class leaves the selector valid after a flip.** Oracle: the page's own DOM. With `is-active` on `section.cards`, the
   reported selector for `Card two`'s heading contains no `is-active`; after the class is removed (the flip) the same selector still
   matches exactly that element, and the applied computed style is still on it.
3. **Pages without a state class are byte-identical.** Oracle: the literal string already pinned at test line 309,
   `main:nth-of-type(1) > section.cards:nth-of-type(1) > article.card:nth-of-type(2) > h3:nth-of-type(1)`, plus the nav literal.
   The existing tests at 305-313 must pass unchanged.
4. **Not touched:** role selectors Detect builds (1927 at 5bd655e; the `roleBindings` region above), stable `data-design-id`
   selectors, and the id anchor logic. A class that only a state predicate matches is not removed from a selector for an element
   whose selector is `#id` or `[data-design-id=...]` (those paths do not use `selectorStep`).
5. **Studio, check only (no edit).** A 0.4.0 saved move whose container selector held a state class no longer equals the new
   selector. `structureHeld` (`fontkit-studio.html:3588`) then returns false, and the user gets the existing banner, headed
   "Live App reconnected." on reconnect (`CONFLICT_HEADINGS`, 5738-5742). No new string. Report that you read it; do not change
   Studio. Not a test (needs Studio plus a saved 0.4.0 file).

## Tests

Insert `class StateClassSelectorTests(BridgeCase)` after `StableSelectorEscapeTests`. Two tests, each looped over `ENGINES`
with the same `subTest` shape as the model test, each with a Given/When/Then docstring.

- `test_selector_built_under_a_state_class_survives_the_flip` (RED at BASE: the selector contains `is-active`, and the match count
  after the flip is 0). Given the stock page with `is-active` added to `section.cards` by `frame.evaluate`. When Card two's heading
  is selected (as in `StableSelectorEscapeTests`, but by `target_by_text`/ready target selector after a re-hello) and a change is
  applied. Then the selector has no `is-active`; after `classList.remove('is-active')` and a second `classList.add('is-active')`
  on a different section, `querySelectorAll(selector)` has length 1 and the computed style carries the edit. Realistic break:
  restore the unfiltered `classList` map; the test fails on the `is-active` assertion.
- `test_pages_without_state_classes_keep_their_selectors` (GREEN characterization, no RED). Given the stock page with a non-state
  class added (`hidden` on an ancestor, `disabled` on a button wrapper). When the ready list is read. Then the two literal selectors
  of line 309 and the `hidden`/`disabled` classes still appear in a selector for an element under them. Realistic break: widening
  the predicate to `hidden`; the test fails.

The `-active` suffix, `has-*` and the list are covered by the first test through one class; do not add one test per class name.

## Focused command

From `the task's worktree`:

`PYTHONPATH=tests FKS_ENGINES=chromium timeout 600 python -m unittest test_bridge_runtime.StateClassSelectorTests test_support -v`

Then once: `PYTHONPATH=tests FKS_ENGINES=chromium timeout 900 python -m unittest test_bridge_runtime test_support -v` (every selector
literal in the module must still pass). One module at a time, no shards, no dev server. Studio landing gates
(`test_studio_roles`, `test_role_routes`, `test_r2_integration`) run at the wave gate, not here.

## Patch

Single row: `task-13-code.patch`. Commit subject: `fix(bridge): leave state classes out of exported selectors` (56 chars). CHANGELOG
line under Unreleased/Fixed: "Exported selectors no longer carry state classes such as `is-active`, so a pasted rule still
matches after the page toggles them." Version labels, the protocol version (1) and the export format (`0.1.1`) do not change.

## Open questions

1. `has-*` drops `has-durations` (ScrobbleScope), which may be a content marker, not a toggle. Plan Decision 5 says any `has-*`;
   recommendation: follow the plan. Uniqueness is never at risk, because `nth-of-type` decides.
2. The plan's "falls back to the full chain" needs no code, as above. Recommendation: do not add a fallback branch; if the
   controller wants one, it is a separate task.

## Controller rulings

1. Open question 1: follow the plan; has-* counts, and the uniqueness loop keeps selectors unique.
2. Open question 2: no fallback branch.
3. CHANGELOG.md is read-only here: the line goes in the report's Handoff, for the controller, because several tasks would otherwise collide on it.

## Review fixes (binding: these govern over the text above)

1. One test covers every arm: test 1 puts a different state class on each link of the chain (`is-active` on `section.cards`, `tab-active` on `article.card`, `has-x` on `main`, `show` or `open` on a wrapper above the heading), asserts none appears in the selector, flips them all, and asserts the result below. Deleting the suffix rule, the `has-` rule or the set must fail it.
2. The oracle is the selector, not the inline style: after the flip, `querySelectorAll(selector)` has length 1 and that element is Card two's heading, asserted by text. Say how the second section is made (clone or insert), since the fixture has one.
3. Test 2: `disabled` goes on Card one's `article.card` and `hidden` on a new wrapper appended after the cards, so the two literals still hold. Keep only the retention assertions that are new.
4. Requirement 4: the dom-path fallback (bridge 1965) goes through `computeSelector`, so its output changes on pages with state classes. That is intended.
5. Requirement 5: the report's Handoff records a known limit, not "the banner covers it": a saved 0.4.0 DOM move whose container selector held a state class cannot be reapplied. Reapply is refused as a whole (`failReapply`, nothing sent), and the fix is to redo the move. On import the heading is "Imported state differs from the Live App."
