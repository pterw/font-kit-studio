# Task 9 brief: Studio guards (an import warning, and a leave prompt only when edits would be lost)

Plan Task 9, wave 1, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit rows S08 and C2-5c. Budget: about 260 gross lines in all
(S08 about 90, C2-5c about 170), tests included; Markdown not counted. Rules: `../constraints.md` (O31 approves New string 9; string 10 has no text).
Two patches, so each row lands as its own commit.

## Why

- **S08.** An imported composition whose text slot names a family the library lacks silently gets the first library font.
  `hydrateSlot` replaces it at `fontkit-studio.html:2453` (`slot.family = byFamily(slot.family).family`); `byFamily` falls back to
  `fonts[0]` at 2183. That fallback is pinned on purpose (`tests/test_studio_live.py:2427-2434`: `unknown-family` imports with a status
  containing `Composition imported.` and a family from `FREE_FAMILIES`) and stays. Only the silence goes. The plan's lines 2166-2168 are
  now 2181-2183.
- **C2-5c.** Studio has no `beforeunload` handler (grep `unload` finds only a comment at 6435). Reloading or closing the Studio tab drops
  the Changes ledger and Studio's saved overrides with no prompt.

## Owned files (exact)

- `fontkit-studio.html`, only these regions at BASE:
  - 2181-2183 (`byFamily`; a small helper may go directly above it);
  - `hydrateSlot` 2420-2470: its signature, the recursive call at 2431, and the line at 2453;
  - `importCompositionJson` 3296 (the `hydrateSlot` map) and 3328-3331 (the status text);
  - 6683-6722: a new `let` and two small helpers go directly above `q("liveCodeCopy")` (6692); one call in each success path of the Copy
    (6692-6711) and Download (6713-6721) listeners; the new `beforeunload` listener goes directly after the Download listener and before
    the `// ---- dev-server sync` comment (6723);
  - `writeOverrides` 6764-6793: capture the key beside `const css = liveCss()` and mark it carried in the success branch (6781).
  Do not touch the `live` object literal (2313-2326), `savedStateEmpty`/`ledgerEmpty` (7185, 7196) or the file's end: other tasks edit them.
- New `tests/test_studio_guards.py` (Addendum 1). Existing tests change only where a requirement below says so.
- Read-only: `CHANGELOG.md` (Task 18 owns it; put the lines in the report's Handoff), every other file.

## Read first

`fontkit-studio.html` 2171-2183, 2420-2470, 3278-3335, 6609-6625 (`liveCss`), 6692-6800, 7185-7200. `tests/test_studio_live.py` 26,
141-153 (`export`, `import_document`), 1355 (`FREE_FAMILIES`), 2410-2436. `tests/test_studio_controls.py` 49-80 (`ControlsMixin`,
`edit_size`) and 199-225 (the Sync, Copy, Download test and `sync_file`).

## Requirements

### Commit 1: S08

1. Importing a composition whose text slot (top level or inside a row) names a non-empty string family that is neither a library family
   nor a key of `LEGACY_FAMILIES` appends, after the existing status text, one sentence per distinct such family, in first-seen order,
   exactly `{family} is not in the library, so the first library font is used.` Oracle: the literal sentence in `#composerStatus`
   for family `ghost-face`; the status still contains `Composition imported.`; two slots naming `ghost-face` give the sentence once.
2. The fallback is unchanged: the slot exports the first library family (`fraunces`, `fonts[0]` at 1318). Oracle: `self.export(page)`.
3. No sentence for a library family, a legacy key (`gotham`, which maps to `work-sans`), a missing `family`, or a non-string `family`: none
   of them names a family. Oracle: the status equals `Composition imported. Image assets must be reselected.` exactly.
4. Presets and every other `hydrateSlot` caller behave as before. Suggested shape: `hydrateSlot(raw, depth=0, missing=null)` takes an
   optional `Set`, passes it to the recursive call, and adds the family just before 2453 when `missing` is given; `importCompositionJson`
   passes a `Set` and appends the sentences in both branches of the status ternary (linked and not linked). Keep complexity low.

### Commit 2: C2-5c

State defined from what exists. "Holds something" is `!ledgerEmpty()` (7196: saved overrides, saved tokens, DOM order, or a ledger entry).
Added state, named: `let carriedKey = null`, a string snapshot, in the 6683 block. `carryKey()` returns
`JSON.stringify([live.overrides, live.savedTokens, live.structure, live.changes])`. `markCarried(key)` sets `carriedKey = key`.
`hasUnsyncedEdits()` is `!ledgerEmpty() && carryKey() !== carriedKey`.

5. Studio registers `window.addEventListener("beforeunload", ...)` that, only when `hasUnsyncedEdits()`, calls `event.preventDefault()`
   and sets `event.returnValue = ""`. Studio supplies no text. Oracle: with an edit made and not carried, closing the page with
   `run_before_unload=True` raises a dialog of type `beforeunload`.
6. No prompt when nothing is held: a fresh Studio, and a Studio after Reset all page edits. Oracle: no `beforeunload` dialog.
7. After Sync to file, Copy or Download succeeds, no prompt. The key is taken when the output is built (in `writeOverrides` beside
   `const css = liveCss()`, not after the response) and marked carried only on success, so a failed write and an edit made mid-write still
   prompt. Auto-sync goes through `writeOverrides` and counts. Oracle: no dialog after each carrier.
8. A further edit after a carry prompts again. Oracle: edit, Sync, no dialog; edit again, dialog.

Existing tests: all 22 `.reload(` hits at BASE are `frame.evaluate('location.reload()')`, which reloads the Live App frame, not the
Studio tab (live 15, roles 3, controls 1, role_routes 1, live_integration 1, review_findings 1; the plan listed 21 and omitted
`test_studio_review_findings.py`). Studio's `beforeunload` should not fire for them. Prove it: grep for `page.reload`, `.go_back` and a
second `page.goto(` on a page holding edits (none found at BASE for the first two), and run `test_studio_controls` and `test_role_routes`
unchanged. If any existing test does hit a prompt, give it a dialog handler or show it holds no edits, and name it for the commit body.
Confirm how Playwright treats an unhandled `beforeunload` dialog (it auto-dismisses, which cancels the navigation) before relying on it.

## Tests (new module `tests/test_studio_guards.py`; imports `ControlsMixin` and `LiveCase` as `test_studio_controls.py` does)

Chromium only is enough. Each test has a Given/When/Then docstring.

- `S08` warns naming the family (RED: no sentence today). Break it covers: the warning dropped or naming the wrong slot.
- `S08` stays quiet for a library family, a legacy key, and no family (GREEN characterization of requirement 3; break: warn on any fallback).
- `C2-5c` positive control (RED): edit a size with `edit_size`, click in Studio first (the browser prompts only after a gesture), close with
  `run_before_unload=True`, expect one `beforeunload` dialog. Dismiss it, then close the page normally.
- Fresh Studio and Reset all (GREEN, one test): no dialog. Reset all needs `window.confirm` accepted by the handler.
- Sync then no prompt, then a further edit prompts (RED; break: a "synced once" flag that never clears). Use `sync_file`.
- Copy and Download each, as subTests, then no prompt (RED; break: only Sync marks carried). Download uses `page.expect_download`.

## Focused command

From `the task's worktree`: `PYTHONPATH=tests FKS_ENGINES=chromium timeout 600 python -m unittest test_studio_guards test_support -v`, then
`test_studio_controls` and `test_role_routes` one module at a time. No dev server is started; the module uses the harness's fixtures only.

## Patches

- `task-9-S08.patch`: `fix(studio): warn when an import names a family the library lacks`. Includes the new module with the S08 tests.
- `task-9-C2-5c.patch`, on the first patch: `fix(studio): confirm before a reload drops unsynced edits`. The body names any existing test it
  changed (expected: none) and says the 22 reloads target the Live App frame.
- Handoff for Task 18 (CHANGELOG, not edited here): "Importing a composition that names a font the library lacks now says which font was
  replaced." and "Studio asks before a reload or close drops edits that were not synced, copied or downloaded."

## Open questions

1. Where S08 shows: recommend appending to `#composerStatus` (the same line already carries the dropped-edits sentence); a separate
   warning element would be a new UI the plan does not list. Say if you want one.
2. A file with many distinct unknown families makes a long status. Recommend naming all, in first-seen order; capping needs a rule the plan lacks.
3. A freshly imported document with a `live` field prompts on reload, since it holds saved overrides no carrier has carried. Recommend keeping
   this: the overrides are lost on reload.

## Controller rulings

1. Open question 1: append the S08 warning to #composerStatus.
2. Open question 2: name them all in first-seen order; no cap.
3. Open question 3: keep the prompt, because the overrides are lost on reload.

## Review fixes (binding: these govern over the text above)

1. Two phases, each a new agent: 9a is S08 and returns `task-9-S08.patch`; 9b is C2-5c, starts from 9a's patch and returns `task-9-C2-5c.patch`. Each dispatch names its phase, and each phase does only its row.
2. "No dialog" right after `page.close(run_before_unload=True)` proves nothing: the call returns before the dialog arrives (measured: empty list at once, dialog 0.5 s later), and a page that does not prompt closes. So every no-prompt assertion waits for the page `close` event and asserts `dialogs == []` and `page.is_closed()`, or uses a synthetic cancelable `beforeunload` probe where the page must stay open. See that probe in `task-9-brief-review.md`.
3. Each carrier test asserts its precondition on the same page: the probe is true after the edit, false after the carry, and true again after a fresh edit. One real `run_before_unload=True` close stays as the positive control. Copy, Download and Sync no-prompt tests are not RED at BASE: treat them as guards, and show them failing under the listed breaks.
4. The Playwright claim in the brief is wrong. With no listener Playwright accepts the dialog and navigation continues; only a dismissing `page.on('dialog')` cancels. `tests/test_studio_live.py:2260-2267` and the frontend gate's `check_touch_targets` and `check_theme_contrast` go through the prompt unhandled and need no change. Add no dialog handlers to existing tests.
5. Known limit for the report's Handoff: one key covers every carrier, so a style edit followed by Download of the HTML tab closes silently. The plan accepts this.
6. Warn only for slots in the hydrated result, after the row truncation. Apply the remaining Minor items in `task-9-brief-review.md`, including the linked-import case and the focused command's additions.
