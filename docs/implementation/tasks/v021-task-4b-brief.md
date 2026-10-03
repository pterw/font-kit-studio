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

### Report (Kerning, Studio implementer)

Base: fast-forwarded the worktree from a6d2751 to origin/ccr-9eab25c9-mgatzt at adca6b4 before any edit.

**RED** (before the fix, `tests.test_studio_stage.TokenFallbackTests`, chromium, 4 of 8 failing):
- Row in slot 1, sans elsewhere: `--font-sans` was `"Fraunces", serif`.
- Row in slot 3, mono elsewhere (role "Footnote"): `--font-mono` was `"Fraunces", serif`.
- No mono family (slot 3 is Inter): `--font-mono` was `"Inter", sans-serif`, sent although no mono family exists.
- No sans family: `--font-sans` was `"Fraunces", serif`.
- The serif cases and the role-wins-the-token case already passed (characterization).
Test detail: roles "Metadata" and "Caption" match the mono role pass and would hide the fallback, so the mono tests use role "Footnote" (`NO_ROLE_MONO`).

**Fix** (`font_kit_studio_v0.1.1.html`, `compositionPatch`, token-fallback lines only): the `slots[1]` sans line, the serif block and the `slots[3]` mono line became one loop over `["sans", "serif", "mono"]`. For each token not set by the role pass, it takes the first top-level text slot whose `byFamily(slot.family).tags` includes the kind, else sends nothing. Row slots and row children never feed a token. The `--font-display` fallback (`slots[0]`) and everything else in the function are untouched.

**Tests** (`tests/test_studio_stage.py`, appended to the serif class, which I renamed `SerifTokenTests` to `TokenFallbackTests` and gave a one-line module docstring update, so the new cases reuse its fixtures without re-running the serif tests twice): sans with Row in slot 1; mono with Row in slot 3; no mono family sends no `--font-mono`; no sans family sends no `--font-sans`; role match still wins for sans and mono. Tokens are read from what the fake target received after Sync to Live App.

**GREEN**: `python -m unittest tests.test_studio_stage` with chromium only: 11 tests, OK. `python scripts/verify.py --static-only`: all PASS (unique IDs, inline JS syntax, provenance), full suite skipped by flag.

**Not verified**: Firefox (not run; FKS_ENGINES=chromium only); the full unittest suite and `scripts/dev/frontend_gate.py` (outside the brief's gates); `node --check fontkit-bridge.js` (bridge untouched). Slot 0 `--font-display` still falls back by index (out of scope per the brief). No commit or push made.
