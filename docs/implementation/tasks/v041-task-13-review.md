### Spec Compliance
- PASS: Req 1, state classes dropped from every step by one predicate (fontkit-bridge.js:3269-3271, applied in the class map at 3275). List is exactly active/selected/current/open/show, `is-`/`has-` prefix, `-active` suffix; `hidden` and `disabled` not matched. Recorded in the report.
- PASS: Req 2, test 1 asserts none of 4 state classes in the ready selector or the applied selector, flips all, inserts a second `section.cards.is-active` AFTER the first (insert, as the fix asks, and the report says so), and asserts `querySelectorAll(selector)` is 1 element with text "Card two" (test_bridge_runtime.py:34-71).
- PASS: Req 3, the existing literals at ~305-313 unchanged; test 2 repeats the line-309 and nav literals; full module run per the report (164 OK); I ran the focused class (36 OK).
- PASS: Req 4, `computeSelector`, `roleBindings`, the id/`data-design-id` paths untouched. Diff touches only `selectorStep` plus one helper placed directly before it.
- PASS: Req 5 / Review fix 5, the Handoff states the known limit (reapply refused as a whole via `failReapply`, redo the move; import heading "Imported state differs from the Live App."). No Studio edit, no new string.
- PASS: Review fixes 1-3: one test with a different state class on each link (main/section/article/h3), flip oracle is the selector plus text, `disabled` on Card one's article and `hidden` on a new wrapper appended after the cards.
- PASS: Patch. `git apply --check --cached` against a temporary index at BASE 5443ff6: applies. Patch is byte-identical to the worktree diff; two files only; CHANGELOG untouched (per ruling 3); subject `fix(bridge): leave state classes out of exported selectors`. Nothing committed yet.

### Checks run
- Selector uniqueness after the filter (D016) -> scratch probe `scratch/t13_probe.py`: stock page plus 5 added panels with `is-active`/`show`/`open` on panels, `tab is-active`, `x tab-active` anchors, and a `div.is-active > span.is-active` pair, where a state class alone told siblings apart -> every one of the 24 ready selectors matched exactly 1 element (`bad []`). Cause confirmed by reading 3231-3262: `nth-of-type` in each step, and the loop verifies `unique()` and extends.
- Callers of `selectorStep` -> grep -> single caller (`computeSelector`, 3251), `this` bound correctly.
- Regression for the shared function -> `test_role_detection` 21 OK; `test_studio_roles` 114 OK; `test_role_routes` 52 OK (chromium, one module at a time).
- Mutation (scratch copy `scratch/t13_copy`, loaded file asserted to hold the mutant, driver `scratch/t13_mut.py`), run against the new class:
  - no `has-` prefix: CAUGHT; no `-active` suffix: CAUGHT; set minus `open`: CAUGHT; widen to `hidden`: CAUGHT; widen to `disabled`: CAUGHT.
  - no `is-` prefix: MISSED (`is-active` is also matched by `-active$`).
  - set shrunk to only `open`, or minus any one of `show`, `active`, `selected`, `current`: MISSED.
  - Reproduced named break, unfiltered class map (the RED at BASE): the report says test 1 fails; the suffix/has mutants above confirm the test reacts to the filter.

### Strengths
- The oracle is the page's own DOM after the flip, with element identity by text; insert-not-clone is explained so nth-of-type indexes stay valid.
- Footprint is small and inside the owned region; pages without state classes are byte-identical (pinned literals).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_bridge_runtime.py:42: the set arm is guarded only through `open`; the other members (`active`, `selected`, `current`, `show`) and the bare `is-` prefix rule can each be removed without a failure (MISSED above). The brief's review fix 1 only requires "deleting the suffix rule, the has- rule or the set" to fail, which holds, and the brief says not to add a test per class, so this is recorded, not a follow-up. Cheap option if wanted: put `selected`/`show` on the two spare chain links and `is-x` (not `-active`) on one.
- Handoff only: `has-*` drops `has-durations` (ruling 1, intended).

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The filter is minimal, selectors stay unique (verified by a probe and the unchanged `nth-of-type` plus `unique()` loop), the shared-function regression modules (`test_role_detection`, `test_studio_roles`, `test_role_routes`) pass, and the tests fail on the unfiltered map, `has-`, suffix and set-deletion breaks and on widening to `hidden`/`disabled`. Only per-member set coverage is thin, which is Minor.
