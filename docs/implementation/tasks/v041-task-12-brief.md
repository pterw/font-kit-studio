# Task 12 brief: tell Studio when the page costs an edit its re-application (D2-11, B19)

Plan Task 12, wave 3, mode code. BASE `5443ff6`, worktree `the task's worktree`. PATCH_DEP task-10-code.patch (apply it to the
worktree first, uncommitted; it adds `postWarning` to `fontkit-bridge.js` and the Studio side). Audit rows D2-11 and B19.
Budget: about 80 gross lines in total (about 10 source, 70 tests), split about evenly across the two rows.
Recorded: D079 (the three kinds), New strings 2 and 3 (approved, O31).

## Why

`stashLost` returns at once for a record that is not `stable` (`fontkit-bridge.js:3395`), so an auto-id element that the
app removes while it carries an edit is dropped silently by the removal loop in `discoverTargets` (`:3461-3466`). Studio's
Changes list still shows the edit and the export still carries the rule, but the page no longer shows it (audit D2-11,
PokeCipher). Separately, when `reapplyFrom` reaches `REAPPLY_MAX` it only calls `console.warn` (`:3406-3411`), so the user
sees an edit vanish from the page with no word from Studio (B19). Both causes hold at BASE (the plan's 3395-3466 is
3394-3466 here). Task 10's patch moves later lines by its added method (about 14 lines): find code by name, not number.

## Owned files (exact)

- `fontkit-bridge.js`: `stashLost` (`:3394-3398`) and, in `reapplyFrom`, the `if (!this.warnedLoops.has(...))` block
  (`:3408-3411`). No other line. Do not edit `postWarning` or the removal loop.
- `tests/test_bridge_runtime.py`: two new classes, each directly after the end of `SpaRobustnessTests` (it ends before
  `RepeatedConstructionTests`, `:3074`), `LostEditWarningTests(BridgeCase)` then `ReapplyStoppedWarningTests(BridgeCase)`.
  Existing tests, including `:2908`, stay unedited.
- Read-only: everything else (fixtures included; `target-spa.html` already has an author `spa.title`, an auto `h2.auto-heading`,
  `render()` and the `pingPong` switch).

## Read first

`fontkit-bridge.js:3338-3350, 3394-3418, 3454-3468`; `tests/test_bridge_runtime.py:51-146, 2854-2945`;
Task 10 brief "Review fixes" 2 (the frozen argument rule); plan "Binding message contract".

## Requirements

Call `this.postWarning(kind, targetId, message)` exactly as Task 10 froze it (omit `requestId`; it goes out as `null`).

### Row D2-11 (first patch)

1. Restructure `stashLost` so that a removed (`!isConnected`), dirty (`isDirty`) record that is not `stable` posts
   `postWarning('edit-not-reapplied', record.id, 'The page replaced this element, so its edit could not be re-applied. The edit is still in the export.')`
   and returns without stashing. The `stable` path behaves as before, byte for byte. Oracle: the literal message and
   `targetId` the page posts after `render()` removes an edited auto heading.
2. No warning when the removed record is clean, or when it is an author id that is re-applied. Oracle: one `render()` that
   replaces an edited `spa.title` and an untouched auto heading posts no `design:warning` (GREEN characterization).
3. Nothing else moves: the removed target leaves the target list as at BASE, and no new message type appears.
   (The export is Studio's; this task changes only what the bridge sends.)

Tests (class `LostEditWarningTests`; open `SPA_PAGE`, `self.hello(page)`, find the auto heading with
`self.target_by_text(ready, 'Auto heading')`):

- `test_an_edit_lost_to_a_replaced_auto_id_element_is_reported`: Given an edited auto heading (`applied` with
  `{'fontSize': 40}`), When the page calls `render()`, Then one `design:warning` arrives with `kind`
  `edit-not-reapplied`, the heading's `targetId`, `requestId` null and the literal message above. RED: no warning is sent.
  Break: restoring the early `return` for non-`stable` records.
- `test_a_replaced_author_element_or_an_unedited_auto_element_posts_no_warning`: Given an edited `spa.title` and an
  unedited auto heading, When `render()` runs and 500 ms pass, Then `self.messages(page, 'design:warning', start)` is `[]`
  and `spa.title` still has font-size `50px`. GREEN characterization. Break: dropping the `isDirty` or the
  `stable` test so every removal warns.

### Row B19 (second patch, on top of the first)

4. In `reapplyFrom`, inside the existing `!this.warnedLoops.has(record.id)` block, after the `console.warn` (kept), call
   `postWarning('edit-reapply-stopped', record.id, 'The page keeps re-creating this element, so its edits are no longer re-applied. They stay in the export.')`.
   `REAPPLY_MAX`, `REAPPLY_WINDOW_MS` and the guard's behaviour do not change. Once per target per stop: the warning
   follows `warnedLoops`, which a later successful re-application resets. Oracle: the literal message; a second count
   after the page is quiet.

Test (class `ReapplyStoppedWarningTests`):

- `test_the_loop_guard_stopping_an_edit_is_reported_once`: Given an edited `spa.title` and `window.pingPong = true`, When
  `render()` starts the loop and the bridge gives up, Then exactly one `design:warning` with kind `edit-reapply-stopped`,
  `targetId` `spa.title`, requestId null and the literal message arrives, and still one after `page.wait_for_timeout(1500)`.
  RED: nothing is sent. Break: dropping the `warnedLoops` test (many warnings). Wait for it with
  `self.wait_message(page, 'design:warning', start, "d.kind === 'edit-reapply-stopped'")`; end with
  `window.pingPong = false`. Do not copy `:2908`'s render-count loop.

## Focused command

From `the task's worktree`, timeout 600 s, one module, no shard, no dev server:

```
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime.LostEditWarningTests test_bridge_runtime.ReapplyStoppedWarningTests test_bridge_runtime.SpaRobustnessTests test_bridge_runtime.PostedWarningTests test_support -v
```

Landing also runs `test_studio_roles`, `test_role_routes`, `test_r2_integration` (controller).

## Patches

Two, in this order (the second is generated against the tree with the first applied):

1. `task-12-D2-11.patch`: `fix(bridge): warn when an auto-id element's edit is lost`. CHANGELOG (controller, Task 18):
   `Live edit now tells you when the app replaces an element whose edit could not be re-applied; the edit stays in the export.`
2. `task-12-B19.patch`: `fix(bridge): tell Studio when the re-render loop guard stops an edit`. CHANGELOG (controller):
   `Live edit now tells you when the app keeps re-creating an element and its edits stop being re-applied.`

## Open questions

1. **Moves.** `isDirty` counts style and text only, so an auto element that was only moved or re-ordered, then removed, gets
   no warning. The plan says "unsaved overrides"; recommendation: keep to `isDirty` (same test the stable path uses).
2. **Re-attached node.** An auto node the page detaches and attaches again within one discovery debounce is not removed at
   scan time; one detached across scans is warned about and then registered again under a new auto id. Accepted;
   recommendation: no special case.

## Controller rulings

1. Open question 1: keep isDirty; moved-only elements stay out of scope.
2. Open question 2: leave it, with no special case.

## Review fixes (binding: these govern over the text above)

1. The B19 test as written cannot catch its break, because the page goes quiet after the guard fires (measured). Use this sequence: after the first warning, set `pingPong=false`, apply a second edit to `spa.title` (for example `fontSize: 44`), call `render()`, wait about 800 ms, and assert the count is still 1. It gives 1 with the guard and 2 without it. Drop the "many warnings" claim.
2. Test 2 reads the current `[data-design-id="spa.title"]` after the 500 ms wait, which is a different node from before `render()`; the 50px check is the precondition for the empty-list claim.
3. Test 1 waits a short time after the first message before counting, so a double post fails.
4. "The heading's `targetId`" is the manifest key `id` in `ready['targets']`.
