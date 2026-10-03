# v0.2.1 Task A6 brief: deep-review findings on the Addendum 7 diff

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task A6 (addendum 1). Source: the
owner's deep review of PR #3 (the review-only copy of PR #2), findings 1-3; finding 4 is D035,
Task 5. Base: `0e8befa` on `ccr-9eab25c9-mgatzt`. Implementer role: Ligature (bridge and the
two Studio functions named below). Two other Studio writers are active in other functions;
stay inside yours.

## Findings, verified in the current tree

(a) **Duplicate `data-design-id` drops a container's saved order.** `buildStructure` maps each
child to its id for `orderIds` (`fontkit-bridge.js:1573`); a child whose id another target
already uses is refused by `registerAuthor` (console warning at ~2114, Spec 4.1) and becomes
`''`. Studio's `savedStructureFrom` (`font_kit_studio_v0.1.1.html:3295`) returns early when
any id is falsy, so the whole container is never saved and a save in progress is lost, with
no message.
Required: Studio keeps the container and the registered children in their order, skips the
untracked child, and once per container shows in the Changes panel status that an element
with a duplicate `data-design-id` is not tracked (name the id, text-only). Keep `orderIds`
aligned with `order` in the bridge (the contract); do not change the bridge for this finding
unless a test proves Studio cannot do it alone, and say why if so. Mind `MAX_STRUCTURE_ENTRIES`
and the 300-character id limit as they are.

(b) **Stylesheets cut to 16 silently.** `withCompositionSheets` (~5447-5461) does
`sheets.slice(0, MAX_COMPOSITION_SHEETS)` (3125). The bridge rejects a longer list
(`checkCompositionSheets`) and treats the list as complete, releasing every sheet not named,
so a composition with more than 16 library families (8 slots, row children with their own
families) shows the rest in fallback fonts on the page with no message.
Required: Studio still sends at most 16 (the contract), chooses them in composition order,
and the Composer status says which families were not sent ("Not sent to the page (16-sheet
limit): Family A, Family B"). No change to the bridge or the limit. Do not touch
`compositionPatch` (Task 4 owns its serif lines).

(c) **Case-only duplicate origins cause a false "policy changed" warning.** `parseOriginList`
(`fontkit-bridge.js` ~378) lower-cases but does not dedupe; `allowedOrigins:
['http://studio.test', 'HTTP://STUDIO.test']` stores two entries, and `initFontKitBridge`
with the same options then reports a policy change that did not happen (`narrowRunningBridge`,
412).
Required: dedupe in `parseOriginList` (order kept); the repeat call reports `changed: false`
and logs no policy warning. Existing tests at `tests/test_bridge_runtime.py:391-434` cover the
case-insensitive comparison; extend next to them.

## Tests (write first, watch them fail, then fix)

- `tests/test_bridge_runtime.py` (append): (c) as above; for (a), a characterization test that
  a container with a duplicate-id child reports `''` at that position in `orderIds` and the
  other ids intact (this is the contract Studio must cope with).
- `tests/test_studio_review_findings.py` (new; subclass `LiveCase` from `test_studio_live`;
  the fake target fixture must be able to present a duplicate-id child, extend
  `tests/fixtures/studio/fake-target.html` only if nothing else lets you): (a) a DOM move in a
  container with one duplicate-id child is saved in `live.structure` with the registered ids,
  survives export and import, and the status names the duplicate id; (b) a composition with 17
  or more library families sends exactly 16 stylesheets and the Composer status names the
  families left out, and a composition with 16 or fewer shows no such text.

## Owned files

`fontkit-bridge.js` (`parseOriginList` only), `font_kit_studio_v0.1.1.html`
(`savedStructureFrom`, `withCompositionSheets`, and one status call each),
`tests/test_bridge_runtime.py` (append only), `tests/test_studio_review_findings.py` (new),
`tests/fixtures/studio/fake-target.html` (only if needed, additive). Nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only && node --check fontkit-bridge.js
python -m unittest tests.test_bridge_runtime tests.test_studio_review_findings
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep` polling.
Do not commit or push. First command: `git rev-parse HEAD`; if behind
`origin/ccr-9eab25c9-mgatzt`, fast-forward before editing. The main tree holds uncommitted
Tasks 3-5 in other Studio functions; your worktree will not, and that is fine: your functions
do not depend on theirs.

## Report

Append under this heading: RED evidence (test names and failure text), the fix (functions
and lines), GREEN evidence (counts for both modules), what you did not verify.

## Report

Implementer: Ligature. Base `af7ec76` (the worktree started at `a6d2751`; fast-forwarded to
`origin/ccr-9eab25c9-mgatzt` before any edit). Nothing committed or pushed.

### RED evidence (before the fix)

- `tests.test_bridge_runtime.OriginListTests.test_case_only_duplicate_origins_are_stored_once_and_the_same_options_again_change_nothing`:
  `Lists differ: ['http://studio.test', 'http://studio.test'] != ['http://studio.test']`.
- `tests.test_bridge_runtime.DuplicateIdOrderTests.test_a_duplicate_id_child_reports_an_empty_id_...`: a
  characterization, written first and passing: the bridge reports `['arr.p.3', 'arr.p.1', '', 'arr.p.2']` and keeps
  `order` the same length (my first run failed only on my own wrong guess of the name format, fixed in the test).
- `DuplicateIdChildTests.test_a_dom_move_in_a_container_with_a_duplicate_id_child_is_saved_...`: `KeyError: 'live'`
  (nothing saved).
- `DuplicateIdChildTests.test_the_status_says_once_per_container_...`: status read "This move is not saved: the
  target's bridge does not report its children's ids"; no duplicate-id text.
- `SheetLimitTests.test_seventeen_families_send_sixteen_sheets_...` and `..._exactly_seventeen`: the update already
  carried 16 sheets (the cut is silent) but the status had no "Not sent to the page" text.

### The fix

- `fontkit-bridge.js`: `parseOriginList` drops case-only repeats after lower-casing (first position wins). The repeat
  call now reports `unchanged` and logs no policy-change warning.
- `font_kit_studio_v0.1.1.html`:
  - `savedStructureFrom`: skips `''` entries of `orderIds` and saves the container with the registered ids in order
    (length check against `order` kept; all-untracked container, duplicate registered ids, 300-char and 100-container
    limits unchanged).
  - New `duplicateIdNote()` (right after it) and one appended call in `domMoveNotice`'s return: once per container
    (by selector, until the container has no untracked child again), text only, names the child and the container.
  - `withCompositionSheets`: still sends `sheets.slice(0, 16)` in composition order; the rest go into a new
    module-level `sheetsNotSent` (declared beside `MAX_COMPOSITION_SHEETS`); new `sheetLimitNote()`. Status is set when
    the list changes during a streamed edit, and `syncToLiveApp` appends `sheetLimitNote()` (one appended call;
    otherwise Sync's own text overwrites the note). When a later edit sends everything again, the note is replaced by
    "Every library font of the composition is sent to the page again."

### Deviations to note

1. **The id is not named in finding (a)'s status.** Studio cannot learn it: the bridge reports `''` at that position
   and no id. The status names the element (the bridge's name for it, e.g. `DIV: "Card"`) and its container, and says
   its data-design-id is a duplicate. Naming the id needs an additive bridge field (for example a list of
   `{index, id}` of untracked children) and a contract change in the plan first. I did not touch the bridge
   (the brief's bar was "a test proves Studio cannot do it alone"); this is that proof, decision is the controller's.
   Recovering it from `entry.html` by position was rejected: `order` skips non-arrangeable children (scripts), so
   position does not align, and parsing the markup breaks rule 5.
2. **Finding (b) cannot happen with today's library.** `fonts` holds exactly 16 families with a `sheet`, and the list
   is de-duplicated, so a composition never has more than 16 distinct sheets. The Studio change is the guard for a
   larger library. The tests append extra families to the global `fonts` array at run time (the script is a classic
   script, so `fonts` is reachable) to reach 17 to 19 sheets; they do not fake the bridge.
3. Side observation, not changed (Task 4's `compositionPatch`): `compositionPatch` builds `--font-sans`/`--font-serif`/
   `--font-mono` from `state.slots[1..3]` even when that slot is a row (a row has no `family`, so `byFamily` falls
   back to the first library font, Fraunces). That adds a Fraunces sheet to the set for such compositions. My tests
   avoid it by putting four text slots first.
4. The fake target needed no change (`mapStructure` already lets a test present the `''` entry).

### GREEN evidence

- `python -m unittest tests.test_bridge_runtime tests.test_studio_review_findings`: Ran 136 tests, OK (chromium only;
  128 in `test_bridge_runtime` including 2 new, 8 in `test_studio_review_findings`).
- Also, because `savedStructureFrom` and `domMoveNotice` are shared: `tests.test_studio_live.StudioDomMovePersistenceTests`
  and `StudioCompositionFontTests`: 44 tests, OK.
- `python scripts/verify.py --static-only`: PASS (90 unique IDs, inline JS syntax, provenance). `node --check
  fontkit-bridge.js`: OK.

### Not verified

- Firefox (engine not installed here; `FKS_ENGINES=chromium` only).
- The full `test_studio_live` suite, `test_live_integration`, the frontend gate and the commit-message check were not
  run (brief limited the run; other implementers edit nearby Studio functions, so a merge needs the full gate).
- Real bridge against real Studio for the duplicate-id move (the bridge side is pinned by the characterization test
  and Studio side by the fake target's `mapStructure`; no test runs both together).

## Fix round 1

Review verdict "Approved with fixes" (`v021-task-a6-review.md`). Four items, test-first. Chromium only.

1. **Flaky test (blocking).** `test_a_linked_edit_stops_the_status_...` waited for "one more streamed composition" and
   read the last one. It now waits for a condition: a streamed update whose `slots[0].fontFamily` matches the edited
   family (`wait_first_slot`), and reads the last matching patch. `sync_with` uses the same wait (family `Extra 1`
   after the import) and returns that patch, so no test reads `streamed(frame)[-1]` any more. The test loops 20 times:
   **20 passed, 0 failed.**
2. **"Sent again" text pinned.** The same test waits for and asserts `sent to the page again`, keeps
   `Composition sent to the live app.`, and still asserts no `Extra 17` or `not sent`. Mutation (the sentence in
   `withCompositionSheets` blanked to `""`, on the real file with a backup, restored and compared with `cmp`): the test
   fails (`Page.wait_for_function: Timeout` on the text). Nothing left behind.
3. **Consent re-send.** RED: `test_the_consent_re_send_keeps_the_families_left_out_in_the_status` failed with the status
   `Loaded 0/33 free font stylesheets; 33 could not load ...` and no note. Fix: `reportComposerFonts` (~:2225) now writes
   `text + sheetLimitNote()` (one appended call). GREEN: the status keeps `Not sent to the page (16-sheet limit): Extra 17`
   after the progress line settles. The test syncs a 17-family composition before the ask (asserts no sheets sent and
   no note), presses Load free fonts, waits for the 16-sheet re-send, then asserts the status.
4. **Real Studio against the real bridge.** New `RealBridgeDuplicateIdTests(LiveIntegrationCase)` in
   `tests/test_studio_review_findings.py` (`tests/test_live_integration.py` untouched). It serves
   `tests/fixtures/bridge/target-arrange.html` from the real `scripts/serve.py` and adds, through a Playwright route
   on the page response, a second paragraph that repeats `arr.p.1`'s id inside `arr.plain` (so the duplicate is on
   every load). A DOM move of `arr.p.3` to first saves `live.structure` ids `['arr.p.3','arr.p.1','arr.p.2']`; the
   status names the container and `Plain one again`, says "Not tracked (duplicate data-design-id)", and still says the
   move is kept; no banner. After reload and Reapply the registered children are `Plain three, Plain one, Plain two`
   and the export is unchanged. The fake-target class gained `test_reapply_after_a_reload_puts_the_registered_children_back_in_the_saved_order`.
   Mutation (the old `savedStructureFrom` behaviour restored: a container with `''` is dropped, backup restored and
   compared): all of the real-bridge test and 3 of 4 duplicate-id fake-target tests fail (3 errors, 1 failure of 6 run).

   **Observation on Reapply and the untracked child (real bridge): confirmed.** Before the reload the page order was
   `Plain three, Plain one, Plain one again, Plain two`. After the reload and Reapply it is
   `Plain three, Plain one, Plain two, Plain one again`: Reapply places the registered ids at indexes 0..n-1, so the
   untracked child ends at index 3 instead of 2. The user sees: the banner clears, the registered children are in the
   saved order, no warning, and the duplicate-id element has moved to the end of its container. It is not Studio's
   state (the status said it is not tracked), but it is a visible page change that Studio does not mention. The test
   pins it (`index('Plain one again') == 3`, "observed"). Fixing it would mean Reapply indexes counting untracked
   children, which needs their positions from the bridge (the same contract gap as naming the id); not done here.

GREEN: `python -m unittest tests.test_bridge_runtime tests.test_studio_review_findings`: Ran 139, OK (128 + 11).
`python scripts/verify.py --static-only`: PASS. Not run: Firefox, full `test_studio_live`, frontend gate.
