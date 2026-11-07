# Task 9a (S08) code report

Mode code, BASE 5443ff6, worktree the task's worktree. Patch: task-9-S08.patch (fontkit-studio.html, new tests/test_studio_guards.py). Nothing staged except `git add -N` of the new module.

## Changed
- `namesFamily` helper above `byFamily` (library family or LEGACY_FAMILIES key).
- `hydrateSlot(raw, depth=0, missing=null)`: `missing` is a Map slot -> family; a text slot whose non-empty family is unnamed is recorded just before the `byFamily` replacement. Row branch passes it down and, after the filter and truncation, deletes entries for children not kept (Review fix 6).
- `importCompositionJson`: passes a Map; the status gets one sentence per distinct family, first-seen order, appended after all existing text (after the dropped-edits sentence) so it covers the linked and unlinked branches.
- Fallback unchanged (fonts[0]).

## Tests (PYTHONPATH=tests FKS_ENGINES=chromium)
- test_studio_guards + test_support: 39 tests OK. test_studio_import_link: 46 OK. test_studio_live -k legacy_keys_still_import (pinned fallback): 1 OK.
- Tests: unknown family named once and exports fraunces; row child + top-level in first-seen order; row child cut by childCount not named; library/legacy/missing/non-string/empty give the plain status; linked import carries the sentence.
- Breaks shown failing (the mutated html is what the tests loaded; restored and verified identical with cmp):
  - warning list emptied: 3 fail (named-once, row/order, linked).
  - namesFamily always false (warn on any fallback): 3 fail (cut child, row/order, no-warning).
  - no delete of cut children: cut-child test fails.
  - no Set dedupe: named-once test fails.
- Not run: mutation with the append in one ternary branch only (the sentences sit outside the ternary, so that break cannot be written).
- The first-time RED (no sentence at BASE) is implied by M1 (empty list equals BASE behaviour).
- pre-commit not installed in this shell (command not found); not run.

## Notes
- Ordering: warning sentence follows the dropped-edits sentence. Brief said "after the existing status text".
- Nothing outside owned regions touched. CHANGELOG read-only.

## Handoff
CHANGELOG line: "Importing a composition that names a font the library lacks now says which font was replaced."
Commit subject: fix(studio): warn when an import names a family the library lacks

---

# Task 9b (C2-5c) code report

Mode code, phase 9b, BASE 5443ff6. Patch: task-9-C2-5c.patch (plain `git diff` over 9a's staged work: fontkit-studio.html, tests/test_studio_guards.py). Index untouched; nothing committed.

## Changed
- fontkit-studio.html: `carriedKey`, `carryKey`, `markCarried`, `hasUnsyncedEdits` above the Copy listener; the key is taken at the start of Copy, Download and in `writeOverrides` beside `liveCss()`; marked after clipboard write, after a successful execCommand copy, after Download, and right after the `throw` in `writeOverrides`; `beforeunload` listener after the Download listener (preventDefault + returnValue = "", no text).
- tests/test_studio_guards.py: `LeavePromptTests` (6 tests) using the synthetic cancelable beforeunload probe, one real `run_before_unload=True` close as positive control, no-prompt real closes wait for the page `close` event and assert `page.is_closed()` and no beforeunload dialog.

## Tests (PYTHONPATH=tests FKS_ENGINES=chromium)
- test_studio_guards + test_support: 45 OK. test_studio_controls: 34 OK. test_role_routes: 52 OK. test_studio_live -k choosing_a_family_in_the_live_inspector -k legacy_keys_still_import: 2 OK (no handler added to it).
- `page.reload` / `go_back` in tests: docstring hits only, no calls.
- Breaks shown failing (mutated html is what the tests loaded; restored, cmp identical):
  - listener name changed: positive control errors, plus 4 others.
  - no markCarried after clipboard write: Copy subTest fails. No mark in Download: Download subTest fails. No mark in writeOverrides: Sync and Copy/Download-flow tests fail.
  - "synced once" (`carriedKey === null`): Sync test and both carriers fail.
  - hasUnsyncedEdits without `!ledgerEmpty()`: fresh and Reset-all cases fail.
  - key taken after the response (`markCarried(carryKey())`): the mid-write test fails.
  - Not covered: the execCommand fallback mark (`if (copied) markCarried`) removed: tests pass (the stub makes clipboard succeed). Accepted.
- Failed-write test (500 reply) is a guard: it passes at BASE-behaviour of "no mark", and fails if a mark were put before the throw (not mutation-run).
- pre-commit not run (not installed in this shell).

## Handoff
CHANGELOG line: "Studio asks before a reload or close drops edits that were not synced, copied or downloaded."
Commit subject: fix(studio): confirm before a reload drops unsynced edits
Body must say: no existing test changed; the 22 `.reload(` calls reload the Live App frame, not the Studio tab; unhandled beforeunload is accepted by Playwright, so test_studio_live's page.goto test and the gate's touch-target and theme-contrast checks need no change.
Known limit (Review fix 5): one key covers every carrier, so a style edit followed by Download of the HTML tab closes silently; the plan accepts this.
