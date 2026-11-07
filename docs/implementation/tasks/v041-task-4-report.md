# Task 4 code report (B09-b)

Mode code, worktree the task's worktree, BASE 5443ff6, nothing committed. Patch: task-4-code.patch (fontkit-bridge.js, tests/test_bridge_runtime.py).

## Changed
- `fontkit-bridge.js`: `setText` (leaf) records `state.wrote = {node: el.firstChild, value: text}` (node null when text is ''). New `leftAsWritten(el, state)`: null node means no children; else exactly one child, the same node, same `data`. `restoreText`: leaf and not left as written -> keep the app's content, `textState.delete(el)` (review fix 1), then the existing `textElements.delete`. Otherwise restores as before. Comment at 714 updated with `wrote`.
- Tests: class `ResetAfterAppRewriteTests` after `TargetedUpdateTests`, in `test_bridge_runtime.py`, four tests:
  1. keeps the app text (two rewrites: `firstChild.nodeValue`, and `el.textContent =` per fix 4), ledger text entry None;
  2. edit again after a kept rewrite then Reset shows the app string (fix 1);
  3. Reset all: TITLE follows the page, CTA is `Get started`;
  4. emoji placeholder cleared by an `inside` image, then Reset: emoji back, no frame errors (fix 2; no existing test covered it, so this is new).

## Evidence
- RED at BASE (tests only, unmodified source): 4 failures: `'Make type sing' != 'App wrote this'` for node value, text content, later-edit and reset-all. The emoji test passes at BASE, as expected (existing behaviour guard).
- GREEN: `ResetAfterAppRewriteTests` 4 OK.
- Mutant (only `textElements.delete`, no `textState.delete`): the later-edit test failed `'Make type sing' != 'App wrote this'`. The mutated code is what the test loaded. Restored; `grep "// mutant"` finds 0.
- Not run as RED mutants: unconditional restore (equals BASE, the RED above); skip-all-leaf restore (CTA assertion in the reset-all test, by construction, not executed).
- `python -m unittest test_bridge_runtime`: 132 tests OK. `test_support`: 34 OK. `check_js_syntax.py fontkit-bridge.js` ran with no output (OK). Chromium only.

## Notes
- Accepted limit (fix 3): `design:restore-text` on an element with an `inside` image appended keeps the image and skips the emoji restore (child count differs). Reset via `resetElement` removes the image first, so the emoji is restored (test 4).
- Mixed content untouched (leaf only, ruling 1).
- Git warns about LF to CRLF in the test file (autocrlf); the diff is clean at 77 insertions.
- Nothing outside owned regions; the one-line comment at 714 was allowed by fix 4.

## Handoff
CHANGELOG (Unreleased): "Reset this element now shows the app's current text when the app rewrote an edited paragraph, instead of the text captured when the edit began."
Commit subject: `fix(bridge): reset an edited text to what the app now shows`
