# v0.2.1 Task 4b brief: sans and mono tokens by tag, not by index

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 4 (decision 5) extended; found by
Task A6's implementer. Base: the current head of `ccr-9eab25c9-mgatzt`. Implementer role:
Kerning (Studio).

## Problem

Task 4 replaced the `state.slots[2]` fallback for `--font-serif` with the first text slot whose
family carries the `serif` tag. `compositionPatch` still derives `--font-sans` from
`state.slots[1]` and `--font-mono` from `state.slots[3]` by index. When that slot is a Row (a
row has no family), `byFamily` falls back to Fraunces, so the page receives a serif as its sans
or mono token and Studio loads Fraunces' stylesheet for nothing. Anti-pattern 12: fix the class,
not the instance.

## Required behaviour

Apply decision 5's rule to all three tokens: a role match first (the existing role pass), else
the first top-level text slot whose family carries the matching tag (`sans`, `serif`, `mono`),
else the token is not sent. Row slots and row children never feed a token. No other change to
`compositionPatch`; `withCompositionSheets` (Task A6, uncommitted in the main tree, not in your
worktree) is not yours.

## Tests: append to `tests/test_studio_stage.py` (it already covers the serif rule; same fixtures)

RED first: a composition with a Row in slot 1 and a sans family elsewhere sends `--font-sans`
naming that family, not Fraunces; a Row in slot 3 with a mono family elsewhere sends `--font-mono`
naming it; a composition with no mono family sends no `--font-mono`; the serif cases still pass.
Read the token from what the fake target received after Sync to Live App.

## Owned files

`font_kit_studio_v0.1.1.html`: the token-fallback lines of `compositionPatch` only.
`tests/test_studio_stage.py` (append). Nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_studio_stage
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep` polling.
Do not commit or push. First command: `git rev-parse HEAD`; fast-forward to
`origin/ccr-9eab25c9-mgatzt` if behind. Other writers are active in other Studio functions.

## Report

Append under this heading: RED evidence, the fix (lines), GREEN count, what you did not verify.
