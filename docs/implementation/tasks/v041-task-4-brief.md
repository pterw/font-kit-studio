# Task 4 brief: Reset shows what the app now shows after it rewrote an edited text

Plan task 4, wave 1, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit row `B09-b` (one row, one patch). Budget: about 60
gross lines (about 15 in `fontkit-bridge.js`, about 45 in the test). Rules: `../constraints.md` "Rules for every agent"; O31 needs no
string here (no new user-facing string).

## Why

A user edits a paragraph's text in Studio, the app then rewrites that string from its own state, and the user presses Reset. Reset
puts back the nodes captured when the edit began, so the page shows the old text while the app's state says another. It stays wrong
until the app's next update. Seen on the Next app, leaf paragraph (`B09-b`, audit row 107).

Cause, re-read at BASE: `captureText` (`fontkit-bridge.js:3005-3018`) stores a leaf's original `childNodes` and `textContent`.
`setText` (3020-3033) replaces the content with `el.textContent = text`, so the page's own text node leaves the DOM. When the app
then updates the string it writes to the node now in `el` (a React single-string update sets that node's `nodeValue`), and
`restoreText` (3035-3044) removes whatever is in `el` and re-appends the stale original nodes. The plan's cause holds at BASE.
`B09` itself (an overwritten edit while it is live) stays a documented limit; do not try to fix it.

## Owned files (exact)

- `fontkit-bridge.js`, lines 3005-3044 only: `captureText`, `setText`, `restoreText`. Other tasks edit other regions of this file at the
  same time (plan Addendum 1); do not touch them.
- `tests/test_bridge_runtime.py`: one new class inserted directly after `TargetedUpdateTests.test_reset_one_target_or_everything`
  (class `TargetedUpdateTests`, BASE lines 620-845; the method ends at 845), named `ResetAfterAppRewriteTests(BridgeCase)`.
- Everything else is read-only. No CHANGELOG, docs or `progress.md` edits (the controller owns them).

## Read first

- `fontkit-bridge.js` 3000-3045 (above), plus callers of `restoreText`: 2317 (`text: null` patch), 2432 (reset all), 2449
  (`handleRestoreText`), 3050 (`resetElement`). All reach `restoreText`; none needs a change.
- `fontkit-bridge.js` 3086-3108 (`currentText`, `originalText`, `textChanged`) and 3421 (re-render re-apply): they read `textState`;
  keep their results unchanged.
- `tests/test_bridge_runtime.py`: `BridgeCase` (51-146), `test_restore_text_restores_original_text_without_throwing` (150), and
  `test_reset_one_target_or_everything` (815-845) for the helpers (`self.open`, `self.hello`, `self.applied`, `self.request`,
  `self.text`, `self.element`, `TITLE`, `LEAD`, `CTA`).
- `docs/implementation/audit-2026-11-06-real-apps.md` rows `B09-b` (107) and `B09` (116).

## Requirements

1. Leaf element, app rewrote the text after the edit. Record in `setText` the text node the bridge wrote and its value (the
   state the bridge left). In `restoreText`, if the element's content is no longer exactly that (the node was replaced or its value
   changed by the app), leave the app's current content in place and only clear the bridge's bookkeeping (`textElements.delete`).
   Oracle: the literal string the test page wrote. Observable: Reset this element leaves that string visible.
2. Reset all (`design:reset` with no `targetId`) and `design:restore-text` behave the same, since they call `restoreText`. Oracle: a
   second element rewritten the same way ends with the page's string; one unrewritten edited element ends with its original text.
3. Unchanged cases: an edited element the app never touched resets to its original nodes exactly as today (original text and node
   identity); an unedited element is untouched; a multi-node child (`LEAD`, mixed content) keeps its edit through data changes as in
   `test_text_edits_leaf_and_mixed_content_and_restore_text_keeps_styles`. Those tests must still pass unmodified.
4. After a rewrite-then-Reset the ledger no longer lists the text edit for that element (`entry['text']` is `None` or the entry is
   gone), as after any Reset. Oracle: the reply's `changes` from the Reset request.

## Tests

New class `ResetAfterAppRewriteTests`, each test looping `ENGINES` like its neighbours. Per test a Given/When/Then docstring.

- `test_reset_keeps_the_text_the_app_wrote_after_the_edit` (RED at BASE: Reset puts back `Make type sing`, not the app's string).
  Given `TITLE` edited to `Edited title`; When the page sets `el.firstChild.nodeValue = 'App wrote this'` in the frame and the user
  sends `design:reset` for `TITLE`; Then `self.text(frame, TITLE) == 'App wrote this'` and the ledger has no text entry for it.
  Realistic break: restoring the captured nodes unconditionally (today's code) fails it.
- `test_reset_all_follows_the_app_for_rewritten_text_and_restores_the_rest` (RED for the rewritten element; GREEN for the other).
  Given `TITLE` rewritten by the page after its edit and `CTA` edited and untouched; When the user sends `design:reset` with no
  target; Then `TITLE` shows the page's string and `CTA` shows `Get started`. Realistic break: a guard that skips every leaf
  restore fails the `CTA` assertion.
- No new test for "no rewrite restores the original" or the multi-node case: existing tests named in requirement 3 already
  characterize them (GREEN, run them as is).

Run RED by stashing nothing: write the tests first, run them against unmodified source, quote the two failures, then fix.

## Focused command

From `the task's worktree`, bounded to 600 seconds:

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime test_support -v`

Studio landings run `test_studio_roles`, `test_role_routes` and `test_r2_integration`; this task changes only the bridge, so the
controller runs those at the wave gate. One test module at a time; never start a dev server. Also run
`python scripts/dev/check_js_syntax.py fontkit-bridge.js`.

## Patches

One patch, `task-4-code.patch`. Commit subject: `fix(bridge): reset an edited text to what the app now shows`. CHANGELOG line for
the controller to add under Unreleased: "Reset this element now shows the app's current text when the app rewrote an edited
paragraph, instead of the text captured when the edit began."

## Open questions

1. Mixed content (non-leaf: `state.node.data = state.originalData`, 3040). The plan's behaviour names a leaf paragraph only.
   Options: (a) leaf only, as seen in the audit; (b) apply the same "has the app changed what the bridge wrote" check to the first
   text node. Recommend (a): `B09-b` was observed only on a leaf, no audit evidence exists for (b), and (b) is a second code path
   without a failing case.
2. How to tell "the app rewrote". Recommended: compare the element's current child nodes and `textContent` with the single text node
   and string the bridge wrote. If the owner wants a stricter rule (for example, a mutation observer), that is a larger change;
   not recommended for this size.

## Controller rulings

1. Open question 1: leaf only, as the brief recommends; mixed content stays out of scope.
2. Open question 2: compare the current child nodes and textContent with what the bridge wrote.

## Review fixes (binding: these govern over the text above)

1. In the keep branch of `restoreText`, also `this.textState.delete(el)`, so the next edit recaptures what the page shows now. Add an assertion: edit, the app rewrites to S, Reset keeps S, edit again, Reset, and the page shows S. A variant that only deletes `textElements` must fail it.
2. `setText(el, '')` (called at 4337) leaves no text node. Record `null` in that case; "unchanged" then means `el.childNodes.length === 0`, and Reset must not throw or skip the emoji restore. Name the existing test that covers clearing an emoji then Reset in requirement 3's run, or add one assertion if none exists.
3. Accepted limit: `design:restore-text` with an `inside` image appended keeps the image and skips the emoji restore. Say so in the report.
4. Add an input where the app replaces the node through `el.textContent = '...'`, so a check on `data` alone fails. You may make the one-line edit to the `textState` shape comment at 714.
