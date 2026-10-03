# v0.2.1 Task 5 brief: D035, import while linked

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 5. Ruling: D035 in
`docs/implementation/deviations.md`. Base: `3083e4d` on `ccr-9eab25c9-mgatzt`. Implementer
role: Kerning (Studio).

## Problem

When the composition is linked to the page (`live.compositionLinked`, set in `syncToLiveApp`,
5366), importing a composition JSON (`importCompositionJson`, 3003) is followed by the page's next
acknowledgement, which replaces the imported tokens with the page's tokens. The user's explicit
import loses to a background acknowledgement (Rule 6 over Rule 2; D035).

## Required behaviour

- An import while linked ends the link (`live.compositionLinked = false`) before the imported
  state is published, and the status says so ("Imported; the link to the page is off. Press Sync to
  Live App to send this composition.").
- The imported tokens are the saved state: the inspector, the JSON tab and the `live` field show
  them after any later `design:applied` or ledger message from the page.
- When the page's tokens differ from the imported ones, the reconnect banner shows with cause
  `import` (`CONFLICT_HEADINGS` already has an `import` key; use it) offering Reapply (send the
  imported composition) and Accept target state. When they do not differ, no banner.
- Sync to Live App after an import re-links and sends the imported composition with its complete
  stylesheet set (through the existing builder; respect the free-fonts ask, D031/D032).
- An import while not linked behaves as today (characterize).

## Tests: new module `tests/test_studio_import_link.py`

Fake target (subclass `LiveCase`): link, import a composition with different tokens, then have
the fake target send a late `design:applied` carrying the old tokens; assert the inspector values,
the JSON tab and the exported `live` field still hold the imported tokens, the link is off, the
status text is shown, and the banner is visible with the import heading. Same flow where the
page's tokens equal the imported ones: no banner. Reapply from the banner sends the imported
composition. Real Studio and real bridge (subclass `LiveIntegrationCase`): Sync, import, assert
the page keeps its current fonts (nothing is sent by the import), the banner appears, then press
Sync to Live App and assert the page's computed font changes to the imported family. The first
fake-target test must be RED before the fix.

## Owned files

`font_kit_studio_v0.1.1.html`: `importCompositionJson` and the functions it calls to publish an
imported state, the link flag handling in `syncToLiveApp`, and the acknowledgement handler's token
adoption (name the exact function in your report). `tests/test_studio_import_link.py` (new).
Do not touch `compositionPatch`, `withCompositionSheets`, connect or status code (other tasks).
Nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_studio_import_link          # only your module; two other agents share the CPUs
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep` polling.
Do not commit or push. First command: `git rev-parse HEAD`; if it is not the base above or
newer, run `git fetch origin ccr-9eab25c9-mgatzt && git merge --ff-only origin/ccr-9eab25c9-mgatzt`
before editing. Two other implementers edit other functions of the Studio file in their own
worktrees at the same time: stay inside your named functions and CSS blocks, add new code next
to them rather than at the end of the script, and never reformat or move code you do not own.
Tests go in your own new module (subclass `LiveCase` from `test_studio_live` or
`LiveIntegrationCase` from `test_live_integration` for fixtures; with `PYTHONPATH=tests` they
import as top-level modules). Test-first: write the tests, capture the failure text (RED), make
the smallest fix, run your module (GREEN). Behaviour that already works is characterized, never
made RED.

## Report

Append under this heading in this file: RED evidence (test names and failure text), the fix
(functions and lines), GREEN evidence (your module count), what you did not verify.
