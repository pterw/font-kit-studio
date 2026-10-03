# v0.2.1 Task A6 review: deep-review findings on the Addendum 7 diff

Reviewer: Leading. Brief and implementer report: `v021-task-a6-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task A6 (addendum 1).
Scope: the uncommitted Task A6 changes: `fontkit-bridge.js` (`parseOriginList`),
`font_kit_studio_v0.1.1.html` (`savedStructureFrom`, `duplicateIdNote`, `withCompositionSheets`,
`sheetLimitNote`, the one appended call in `syncToLiveApp`), `tests/test_bridge_runtime.py`
(two new classes) and the new `tests/test_studio_review_findings.py`. The same tree holds
Tasks 3 and 5 uncommitted, reviewed separately. Controller rulings on the implementer's
deviations: the duplicate id is not named (the bridge sends `''`; naming it is a contract change
for a later plan, recorded as a known limit); the 16-sheet guard cannot trigger with today's
library and stays as a guard; the `--font-sans` and `--font-mono` index fallbacks in
`compositionPatch` become Task 4b.

## Verdict

Reviewer: Leading. Verdict: **Approved with fixes** (one blocking test fix, three small ones; no production
defect that stops the commit). Chromium only (`FKS_ENGINES=chromium`); Firefox not run, not verified.

### Gates I ran

- `python scripts/verify.py --static-only`: PASS (93 unique IDs, inline JS syntax, provenance). `node --check fontkit-bridge.js`: OK.
- `python -m unittest tests.test_bridge_runtime tests.test_studio_review_findings`: Ran 136, OK (one pass; see fix 1,
  the Studio test below is flaky and happened to pass in that run).
- `python -m unittest tests.test_studio_live -k DomMove -k CompositionFont -k Structure`: Ran 45, 1 failure:
  `test_reapply_with_the_ask_sends_the_complete_set_so_a_sheet_only_a_slot_uses_stays` (`tests/test_studio_live.py:4220`)
  expects `Composition imported.` but gets Task 5's `Imported; the link to the page is off...`. That is Task 5's D035
  wording (the `wasLinked` import text in the Studio diff), not A6; it belongs to the Task 5 review/fix round.
  The implementer's 44 (DomMove and CompositionFont classes) were run before Task 5's change landed in the tree.
- Not run: full suite, frontend gate, Firefox.

### (1) Finding (a), duplicate-id child

Correct. `savedStructureFrom` (`font_kit_studio_v0.1.1.html:3298-3312`) keeps the length check against `order`
(`reported.length !== entry.order.length`), then filters `''`, so the container saves with the registered ids in order.
Hostile-payload checks are not weakened: the length match is still against the unfiltered list; uniqueness, the 300-char
limit and cross-container uniqueness now run on the registered ids only (`''` is not an id, so a repeated `''` rightly
no longer counts as a duplicate); `MAX_STRUCTURE_ENTRIES`, the selector limit and the 500/501 cap on `orderIds`
(`normalizeLedger`, `:3420`) are untouched; an all-`''` container is still dropped (`!list.length`); whatever it saves
satisfies `parseLiveStructure` (1-500 unique ids), so an export always imports.
Every reader of `orderIds` copes with `''`: `grep orderIds` finds only `savedStructureFrom`, `duplicateIdNote` (`:3322`,
guards equal length) and `normalizeLedger` (keeps `''` since it is a string). `planStructureReplay` (`:4286`),
`structureHeld`, `structureProblem`, `acceptTargetState`, `structureSentence` and `syncStructureFromLedger` only
ever see `savedStructureFrom` output (ids with no `''`, shorter than `order`), compared with `sameIds` against
`live.structure`. `structureRefusal` reads `entry.ids` of saved containers only. Probe on a scratch copy (deleted):
fake target with a `''` child, move, reload, re-apply the same `mapStructure`, click Reapply: banner hides, page order
`card.c, card.a, card.b, card.d`, export unchanged, no console errors. So replay works for the registered children.
Status: `duplicateIdNote` names the element and its container (not the id, per the controller ruling), is once per
container by selector, is cleared when the container has no untracked child again, text only (`setCodeStatus` uses
`textContent`; names clamped to 60 chars).
Observation, not a defect: replay places the registered ids at indexes 0..n-1, so after a Reapply the untracked child
may sit at a different place than before the reload (it is not Studio's state). Not checked against the real bridge.

### (2) Finding (b), 16 sheets

Correct for the cases tested: `patch.fontStylesheets = sheets.slice(0, 16)` in composition order (slots, rows'
children, then token fonts); `sheetsNotSent` is the remainder by library name; the Composer status is
`Not sent to the page (16-sheet limit): Extra 17, ...`; `syncToLiveApp` appends `sheetLimitNote()` after
`broadcastLiveState(true)` has already rebuilt the patch (synchronous), so Sync's own text no longer hides it;
16 or fewer gives `sheetsNotSent = []` and no text. State is correct on Reapply (the token-only update goes through
`withCompositionSheets`, same set), on import (the linked-import path calls `compositionPatch()` once; the unlinked
state sends nothing) and on the consent re-send (`:5197` calls `broadcastLiveState(true)`, which recomputes it).
Gaps:
- Consent re-send loses the message. I probed a 17-family composition synced before `Load free fonts`: the re-send does
  send 16 sheets and `sheetsNotSent` is right, but `loadAllFreeFonts(reportComposerFonts)` then writes
  `Loaded 0/33 free font stylesheets...` over the note. The next edit does not restore it (the list did not change),
  only the next Sync does. No test covers it.
- The "sent again" text is only written when the status still contains the note (`:5494`), and no test pins its wording
  (see fix 2).
- Names for sheets outside `fonts` fall back to "another font" (Typekit); acceptable.

### (3) Finding (c), origins

Correct. `parseOriginList` (`fontkit-bridge.js:377-382`) dedupes after lower-casing, first position wins;
`narrowAllowedOrigins` already deduped `next`, so the stored list and `current` now agree and the repeat reports
`changed: false` with the `allowedOrigins unchanged` sentence. The new test asserts no policy warning for two repeats,
the session survives, and a revision continues; the existing `test_init_narrows_...` and
`test_a_mixed_case_list_narrows_like_its_lower_case_twin` still pass and cover a genuine narrowing with its warning.

### (4) Rule 5

No `innerHTML` or markup parsing in the A6 hunks. Page-supplied names (`entry.order`, `entry.name`) reach the DOM only
through `setCodeStatus`/`textContent`, clamped. Sheet names come from Studio's own `fonts`, not the page.

### (5) Test quality and mutation checks

- Bridge characterization (`DuplicateIdOrderTests`) pins `['arr.p.3','arr.p.1','','arr.p.2']` and
  `len(order) == len(orderIds)`; real bridge; no sleeps.
- Mutation 1, restore the `!id` early return in `savedStructureFrom` (scratch copy): `test_a_dom_move_in_a_container_...`
  ERROR and `test_the_status_says_once_per_container_...` FAIL. Caught.
- Mutation 2, drop the dedupe in `parseOriginList` (scratch copy): `OriginListTests.test_case_only_duplicate_origins_...`
  FAIL, `Lists differ: ['http://studio.test', 'http://studio.test'] != ['http://studio.test']`. Caught.
- Mutation 3, drop `+ sheetLimitNote()` from `syncToLiveApp`: `test_seventeen_families_...` FAIL. Caught.
- Mutation 4, blank the "sent to the page again" sentence: **survived** (5 of 5 runs OK). The test asserts only the
  absence of `Extra 17` and `not sent`.
- No fixed sleeps in the new file. Tests assert rendered status text, the exported structure, and what the page received.
- Scratch copies removed; the tree is unchanged by me (only this file).

### (6) Extra families pushed onto `fonts`

Fair for the guard. The pushed entries are ordinary library entries before the document is imported, so the import
(`hydrateSlot` -> `byFamily`), `compositionPatch`, `fontStylesheetUrl`, `safeFontStylesheet` and the real bridge all run
as they would for a larger library; nothing is faked on the bridge side. I confirmed the premise: `fonts` has exactly 16
entries with `sheet`, so the cap cannot be reached today and the tests exercise a guard. Records should say so.

### Fixes required before commit

1. **Flaky test (blocking).** `tests/test_studio_review_findings.py:163-174`,
   `test_a_linked_edit_stops_the_status_naming_families_once_everything_is_sent`. It waits for "one more streamed
   composition" (`wait_streamed(frame, before + 1)`, `:170`) and then reads `streamed(frame)[-1]`. Studio sometimes
   sends a second, unchanged composition update before the family change; the count is then satisfied by the
   unchanged one, and `assertIn(self.sheet_for(17), sent)` (`:173`) fails. In isolation it failed 3 of 4 and 2 of 3 runs
   (it passed in the 136-test run). My instrumented run showed the failing case: two streams, both with `"Extra 1"`
   first and sheets 1-16. Fix: wait for the condition, for example a streamed update whose `slots[0].fontFamily`
   starts with `"Extra 2"` (add a `wait_for_function` like `wait_streamed`, filtered on that), then assert. Rule: no
   waits that can be satisfied by the wrong event. Same pattern in `sync_with` (`:124`) is harmless there (all streams
   carry the same content) but should use the same condition.
2. **Pin the "sent again" message.** Same test: after the wait, assert the status contains
   `sent to the page again` (and, for the Sync-line case, that the text before it, `Composition sent to the live app.`,
   is kept). Mutation 4 above must then fail.
3. **Consent re-send.** Either append `sheetLimitNote()` where the free-fonts handler reports (so `Loaded n/m ...` is
   followed by the note when `sheetsNotSent` is non-empty), or record in the review/ledger as a known limit: the
   status says it only after the next Sync. Add a test for the chosen behaviour (sync a 17-family composition, press
   `#loadFreeFonts`, assert 16 sheets were sent and what the status says).
4. **Real Studio against the real bridge for the duplicate-id move** (Test Quality Rules: the `''` contract is pinned
   on the bridge side by `DuplicateIdOrderTests` and on the Studio side only by the fake's `mapStructure`). Add one
   test in `tests/test_live_integration.py` (a page with a duplicate-id child; move; export shows the registered ids;
   status names the container). Also add the reload + Reapply case I probed by hand (it passes) to
   `tests/test_studio_review_findings.py`, since the brief asks that replay works.

Known limits to carry in the ledger (controller already ruled): the duplicate id is not named (bridge sends `''`);
the 16-sheet guard cannot trigger with today's library; `compositionPatch` index fallbacks go to Task 4b.

## Re-review (fix round 1)

Reviewer: Leading. Scope: the four required fixes, as committed in `0f410c0` (head of `ccr-9eab25c9-mgatzt`) and
described in the brief's "Fix round 1". **Verdict: Approved.** No further fix is required before the release point.
Chromium only; Firefox not run, not verified. All runs were in a detached worktree at `0f410c0` (removed afterwards;
the main tree was not touched except for this appended section).

### Gates (worktree, `FKS_ENGINES=chromium`)

- `python -m unittest tests.test_studio_review_findings -v`: Ran 11, OK (5 fake-target duplicate-id, 1 real-bridge,
  5 sheet-limit).
- `tests.test_bridge_runtime.OriginListTests` + `DuplicateIdOrderTests`: Ran 10, OK. Both classes are unchanged by the
  fix round (`git diff 2cb8276 0f410c0 -- tests/test_bridge_runtime.py` is the original two additions only).
- The formerly flaky `test_a_linked_edit_stops_the_status_naming_families_once_everything_is_sent`, run 10 times in
  isolation: **10 of 10 passed** (it failed about half the runs before the fix).
- Not re-run: `verify.py --static-only` (the release-point gate owns it), full suite, frontend gate, Firefox.

### The four fixes

1. **Flaky test: fixed.** `wait_first_slot` (`tests/test_studio_review_findings.py:214-223`) waits for a streamed
   composition whose first slot carries the wanted family and returns the last matching patch; `sync_with` (`:199-209`)
   and the linked-edit test use it, so no test reads `streamed(frame)[-1]` any more. It is a condition, not a count.
   No `sleep` or `wait_for_timeout` in the file.
2. **"Sent again" pinned: fixed.** The linked-edit test (`:249-267`) waits for and asserts `sent to the page again`,
   keeps `Composition sent to the live app.`, and still asserts no `Extra 17` and no `not sent`.
3. **Consent re-send: fixed.** `reportComposerFonts` now writes `text + sheetLimitNote()`
   (`font_kit_studio_v0.1.1.html` ~:2244). The test (`:269-288`) syncs before the ask (asserts no sheets sent and no
   note), presses Load free fonts, waits for the 16-sheet re-send, then asserts `Loaded 0/N ...` and the note naming
   `Extra 17`. It depends on the test network being offline (it waits for `could not load`), the same assumption the
   harness makes elsewhere; if the harness ever allowed Google Fonts the wait would need a different settle condition.
4. **Real Studio against the real bridge: fixed.** `RealBridgeDuplicateIdTests` (`:114-177`) serves the bridge's
   arrangement fixture through `scripts/serve.py`, adds a duplicate-id paragraph with a Playwright route on every
   load, moves `arr.p.3` first, and asserts the export holds `['arr.p.3','arr.p.1','arr.p.2']`, the status names the
   container and `Plain one again`, no banner, then reload + Reapply restores the registered order and the export is
   unchanged. The fake-target reload + Reapply case is `:53-72`. Hostile/other-boundary rules are not affected.

**Placement of fix 4.** It landed in `tests/test_studio_review_findings.py`, not `tests/test_live_integration.py`.
Acceptable: the class subclasses `LiveIntegrationCase` (`import test_live_integration as integration` does not make
the unittest loader collect those tests twice), it runs the same real-Studio/real-bridge harness, the brief's owned
files were the new file, and `test_live_integration.py` was under edit by other tasks. Keep the module docstring
pointer (it names the class). If the owner prefers all real-bridge tests in one module, moving the class later is
mechanical.

### Mutation results (worktree, restored with `git checkout` after each; `git status` clean)

| Mutation | Failing tests |
|---|---|
| M4: blank the "sent to the page again" sentence | `test_a_linked_edit_stops_the_status_naming_families_once_everything_is_sent` (ERROR, wait on the text times out). Earlier survivor is now caught. |
| M5: `reportComposerFonts` writes `text` without `sheetLimitNote()` | `test_the_consent_re_send_keeps_the_families_left_out_in_the_status` (FAIL) |
| M6: restore the whole-container drop in `savedStructureFrom` | `test_a_dom_move_in_a_container_with_a_duplicate_id_child_is_saved_for_the_registered_children`, `test_reapply_after_a_reload_puts_the_registered_children_back_in_the_saved_order`, `RealBridgeDuplicateIdTests.test_a_dom_move_beside_a_duplicate_id_child_is_saved_reported_and_reapplied_after_a_reload` (3 ERROR), `test_the_status_says_once_per_container_...` (FAIL) |

The three earlier mutations (dedupe, `sheetLimitNote` in Sync, `!id` early return) are covered by the same tests as in
the first review; the first review's bridge tests are unchanged and pass.

### Findings

- None blocking. The code change in the fix round is one line (`reportComposerFonts`); the rest is tests and records.
- Known limit, confirmed on the real bridge by the implementer and pinned by the test (`:171-175`): Reapply places the
  registered ids at indexes 0..n-1, so the untracked duplicate-id element moves from index 2 to the end of its
  container, and Studio does not mention it. It is not Studio's state, and fixing it needs the untracked child's
  position from the bridge (the same contract gap as naming the id). Two cautions: the test pins the current
  (undesirable) position as "observed", so a future fix will have to update that assertion on purpose; and the ledger
  should list it beside "the duplicate id is not named". Optional follow-up: one sentence in the Reapply result
  saying an untracked element may have moved.
- Minor, not required: `reportComposerFonts` appends `sheetLimitNote()` from whatever `sheetsNotSent` last held, so
  after the composition changes while unlinked the line can name families from the last send until the next Sync
  recomputes it. Same staleness class as the first review's note on unlinked edits; acceptable for a guard that the
  current 16-family library cannot trigger.

### Not verified

Firefox; the full `test_studio_live` suite (Task 5's `:4220` expectation mismatch from the first review is for the
Task 5 round, and I did not check whether it is now fixed); the frontend gate and `verify.py` at `0f410c0`; the
untracked child's position after Reapply on any page other than the arrangement fixture; behaviour with a network
that lets Google Fonts load.
