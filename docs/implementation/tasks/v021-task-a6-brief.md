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
