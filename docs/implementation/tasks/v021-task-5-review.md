# v0.2.1 Task 5 review: D035, import while linked

Reviewer: Leading. Brief and implementer report: `v021-task-5-brief.md`. Ruling: D035.
Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 5.
Scope: the uncommitted Task 5 changes to `font_kit_studio_v0.1.1.html` (`endCompositionLink`,
`importCompositionJson`, `adoptImportedLive`, `reconcileImportedLinked`, the token adoption in
`recordCanonical`) and the new `tests/test_studio_import_link.py`, in the main tree at `0e8befa`.
The same tree holds Tasks 3 and 4 uncommitted, reviewed separately.

## Verdict

**Verdict: Approved with fixes.** The Task 5 code implements D035 and its own tests are strong, but the change breaks one
existing Chromium test (fix F1, required before commit) and has one reachable hole (F2) and one blind spot (F3) that I
recommend closing in the same pull request.

Reviewed 2026-10-03 on the main tree at `0e8befa` (uncommitted Tasks 3, 4 and 5), Chromium only (`FKS_ENGINES=chromium`,
`/opt/pw-browsers/chromium`). Firefox and the frontend gate were not run.

### Gates I ran

- `python scripts/verify.py --static-only`: PASS (IDs, inline JS syntax, provenance). `node --check fontkit-bridge.js`: OK.
- `python -m unittest tests.test_studio_import_link`: Ran 10, OK (28 s).
- `python -m unittest tests.test_studio_live` (full): Ran 152, 2 failures.
  - `StudioCompositionFontTests.test_reapply_with_the_ask_sends_the_complete_set_so_a_sheet_only_a_slot_uses_stays`
    fails deterministically (reproduced alone). It is a Task 5 regression: see F1.
  - `StudioFixRound1Tests.test_every_control_message_carries_protocol_version_and_session` failed once in the full run
    (`design:hello` carried a different `sessionId` than the one read earlier) and passed 2 of 2 when run alone. It does
    not import anything and does not touch Task 5 code; it ran while another agent's suite shared the CPUs. I treat it as a
    load flake, but it is a Task 3 (connect) test and should be watched at the release gate. Not verified beyond that.

### Findings that need action

**F1 (required). An existing test still asserts the old linked-import behaviour.**
`tests/test_studio_live.py:4207-4222`, `test_reapply_with_the_ask_sends_the_complete_set_so_a_sheet_only_a_slot_uses_stays`:
it syncs (so the composition is linked), imports a document, and expects `'Composition imported.'` (line 4220 in the current
file, 4218 before the other tasks' edits), then `wait_handled(page, 1)` "the import streams the composition; the page
acknowledges it". Under D035 the status is the new text and the import sends nothing, so the assertion fails and the
`wait_handled` would hang. The comment "the composition stays linked" is the old contract. The implementer's spot checks did
not include `StudioCompositionFontTests`. Fix: assert `STATUS`, drop the stream wait (a held `wait_handled` is not needed:
the banner is raised by the import itself), assert the banner heading is "Imported state differs from the target.", keep the
rest (token added by another editor, an inspector edit, Reapply sends the complete sheet set, banner hidden). The rest of the
test is about Reapply and should still hold. I did not edit it (read-only). I grepped every other `import_document` caller in
`test_live_integration.py`, `test_font_kit_studio_v011.py`, `test_studio_first_run.py` and `test_studio_stage.py`; all the
`test_live_integration` ones sit in classes the implementer ran (`CompositionSyncTests`, `FreeFontsAskTests`,
`StructureReplayTests`, `ImportedTokensTests`). I did not run the full `test_live_integration`, `test_studio_stage` or
`test_studio_first_run` modules, so the gate runner must.

**F2 (recommended, small). A Reapply queued or in flight at import time replays the pre-import state and wins.**
`endCompositionLink` (`font_kit_studio_v0.1.1.html:3024`) keeps `op.reapply` ops on purpose, and `recordCanonical` checks the
`op.reapply` branch before `importSuperseded` (3790 vs 3799). Probe on a scratch copy (fake target): import A (banner), press
Sync with the reply held, press Reapply (queued behind it), import B (different tokens, link ends), release. Result: the
Reapply op, built from A's saved tokens, is acknowledged and `live.savedTokens` becomes the page's tokens (A); B's tokens are
gone, the banner is hidden, nothing told the user. Exported `live.tokens` after: `--font-display: "Inter"` (A), expected
`Georgia, serif` (B). The same class applies to queued Reapply update/reset/move ops (an acknowledged `update` writes the old
override back into `live.overrides`). It needs a Reapply started and a silent or slow page across a file-picker round trip, so
it is narrow, and an unlinked import has the same hole today (pre-existing). But D035 says the import is the latest explicit
state, and Rule 6 ranks silent overwrite of user state above convenience. Recommendation: in the import (when wasLinked or
not), end any running Reapply: remove its queued ops (as `failReapply` does), mark in-flight and timed-out Reapply ops
`importSuperseded`, test `importSuperseded` first in `recordCanonical`, and set `live.reapply = null` without an error
banner. Covering test: the probe above as a fake-target test (assert exported `live.tokens` is B's after release).

**F3 (recommended). `reconcileImportedLinked` hides the user's own earlier edits that the import drops.**
Question 2, answered by probe. The asymmetry is right for what the implementer found: with the real bridge a linked
composition styles the page's own elements, which appear as changed targets Studio never saves. I confirmed it: on a scratch
copy, swapping `overridesHeld` for the symmetric `overridesEqual(...)` makes the real-bridge test fail (the banner never
clears after Sync). Tokens are compared symmetrically (`tokensEqual`), so page tokens the import does not mention are
surfaced: probe, page holds `--extra-font`, import omits it, banner visible. That part is correct.
The blind spot is overrides. Probe (fake target, linked): select `hero.lead`, set font size 21 (acknowledged, saved), export,
set `live.overrides` to `{}` in the file (tokens equal to the page's), import it. Result: no banner, the page still shows
`hero.lead` at 21px, Studio's saved overrides are `{}`. The user's own saved edit was dropped by the import and the page
keeps it, silently: Sync to file would then write a file without it and a reload loses it. That is exactly the "page state
the user would want to know about". Recommendation, minimal: when the import is made while linked, remember the target ids
that Studio held saved overrides for before the import (`Object.keys(live.overrides)` taken before `adoptImportedLive`
replaces them, plus ids named in the old `live.structure`), and in `reconcileImportedLinked` also count a page entry on one
of those ids that the new saved state does not hold as a difference. Targets Studio never saved keep being ignored (the
composition-driven ones). Clear the remembered ids on Accept, on a finished Reapply and when Sync re-links. Covering test:
the probe above, asserting the banner is visible and Reapply restores the page (resets `hero.lead`). If the owner prefers to
leave this, the comment above `reconcileImportedLinked` should say the blind spot in so many words.

### Answers to the review questions

**(1) D035 exactly: met.** The link is ended inside the `try`, after all validation and before `Object.assign(state, ...)`
(3058-3060), so a rejected import keeps the link (test `test_a_rejected_import_while_linked_keeps_the_link`). The status is
the D035 text. Imported tokens are the saved state: from the file's `live.tokens` or, when the file has none (or an empty
set), from `compositionPatch().tokens` read-only (3064-3074); they survive the held late `design:applied` (mutation 2 below
proves it). Banner with cause `import` only when the page differs (`reconcileImportedLinked` sets `conflictCause = "import"`
every time); equal tokens give no banner (test 3, both file shapes). Reapply is the existing `reapplyStudioOverrides` with the
saved (imported) tokens, so it sends a tokens-only update plus saved overrides and DOM order, not the slots, sizes, colours or
text of the imported composition: those go with Sync. The test name "sends the imported composition" and the plan wording
overstate this; the banner text already says "saved overrides, composition tokens and DOM order", so it is accurate to the
user. Suggest renaming the test to say tokens. Sync re-links and sends the complete stylesheet set through the untouched
`compositionPatch`/`withCompositionSheets` (tests 6 and 7, with the free-fonts ask). The unlinked import is unchanged
(characterization test, status text kept). Nothing in the import calls `broadcastLiveState` before the link is off.

**(2) Asymmetry:** see F3. Tokens and saved DOM order: symmetric enough and correct. Overrides: right for composition-styled
targets, wrong for ids Studio itself had saved before the import. Recommendation: narrow it as in F3 (do not make it fully
symmetric).

**(3) Superseded and dropped ops.**
- A late reply to a superseded request (in flight or in `live.timedOut`) goes through `afterApplied`, so it still updates
  `live.changes` (the page's real ledger), the status badge, the code panel and the banner (through
  `reconcileImportedLinked`), and calls `scheduleAutoSync`. All of that is the truthful page state; the saved tokens do not
  change. It also overwrites `live.canonicalRevision`/`canonicalTarget` (3810), which only feed the exported `live.revision`
  and `live.target`; after an import plus a late reply the export carries the page's revision for tokens that differ from it.
  Cosmetic, nothing reads it back; note only.
- A superseded reply that arrives after the user pressed Sync again can raise the banner for an instant; the new
  composition's acknowledgement clears it (the `import` re-evaluation branch). Fine.
- Dropped queued composition ops leave nothing stale: they carry no status text of their own, the debounce timer is cleared,
  and the saved state they would have recorded is the thing the import replaces. The status line and code panel are written
  by acknowledgements, so no acknowledgement means no stale text. Queued user ops of other kinds (an inspector update) are
  kept and, when acknowledged, record into `live.overrides`; that is correct for an edit made before the import only if the
  user still wants it, same class as F2, unchanged behaviour.
- Reapply ops at import time: see F2 (not handled sensibly).
- No test exercises a timed-out superseded request or a queued (not in-flight) composition op that gets dropped; only the
  in-flight case is covered. Suggest one test each (silent page past the request timeout, then reply; two quick composition
  edits so the second is queued).

**(4) The empty-saved edge.** The implementer's note is moot and its description is not what the code does. A linked import
always saves a non-empty token set: `compositionPatch` always sets `--font-display` when there is a slot, and the import
guarantees at least one slot. Probe: import `{"composition":{"slots":[{"type":"spacer"}]}}` while linked gives saved tokens
`{"--font-display":"Fraunces, serif"}` and the banner visible. Had the set been empty, `tokensEqual({}, pageTokens)` is false
for a page with tokens, so the conflict would be raised, not kept off. Nothing to fix; the report sentence should be struck.

**(5) Test quality.** Real Studio plus real bridge: `ImportWhileLinkedRealBridgeTests` (via `serve.py`, demo page) asserts
computed `fontFamily` of `.wordmark` stays Fraunces after the import, the badge revision is unchanged (nothing sent), the CSS
tab shows `--font-display: "Inter"`, then after Sync the computed family is Inter and the banner hides. Good. The fake-target
tests assert what the user sees: CSS tab `:root`, exported `live.tokens`, status text, banner visibility and heading, page
ledger tokens. Mutation checks on a scratch copy (`scratchpad/mut`, the tree untouched; file restored after each):
1. Skip `endCompositionLink` in the import: 8 of 10 fail (3 timeouts, 5 assertions, for example "3 != 2 the import sent
   nothing" and `'"Fraunces"' not found in '"Inter", sans-serif'`). Killed.
2. Let a superseded reply adopt tokens (branch `importSuperseded` disabled): both late-ack tests fail
   (`'--font-display: "Inter"' not found` in a CSS tab showing Fraunces and JetBrains Mono). Killed.
3. Extra: make `reconcileImportedLinked` compare overrides symmetrically: the real-bridge test fails. This justifies the
   asymmetry and is what keeps that test honest.
No new fixed sleeps beyond `wait_for_timeout` absence windows (200-300 ms) that each prove a send or banner did not happen,
which AGENTS.md allows; all other waits are conditions. No "message sent" assertion without a rendered check. Gaps: the two in
(3), F2 and F3 probes. Hostile-boundary rule: no new trust boundary is crossed (the import reads a local file; values still go
through the existing validators), so no hostile case is required.

**(6) Token choice after Task 4.** Confirmed. `--font-display` comes from a title/display/hero role match, else slot 0;
`--font-mono` from a mono/data/caption/code role match, else slot 3 (`compositionPatch`, 5401-5414); neither uses the serif
rule Task 4 changed. The page holds Fraunces and JetBrains Mono, the import Inter and IBM Plex Mono; the tests assert the exact
family strings (CSS tab and `live.tokens`), not just "tokens differ", and mutation 2 shows they fail when the import's tokens
are replaced.

### Anti-pattern and rule check

- Rule 6 (never silently overwrite): satisfied for the acknowledgement path (D035); F2 and F3 are the two places it is not.
- Rule 2: persistence is still built from acknowledged state; the import is explicit user state, not an acknowledgement.
- Anti-pattern 5 (silent overwrite): see F2, F3. 7 (intercepting when not attached): no change. 9 (flags): `importSuperseded`
  is a per-op marker, not a session flag; fine. 11 (stale docs): README has no text on import while linked or on the
  streaming link; add one sentence with the PR (in the Composer section near README line 229): importing while synced ends
  the link, shows the banner when the page differs, and Sync to Live App resumes it. 12 (siblings): the grep of other
  `import_document` callers is in F1.
- Comments explain why; style matches the surroundings; Task 3 and 4 code was not touched by Task 5 hunks.

### What I did not verify

Firefox, the frontend gate, the full `test_live_integration`, `test_studio_stage` and `test_studio_first_run` modules, the
phone and touch profiles, commit messages (nothing committed).
