# v0.2.1 selection-race fix: brief and implementer report

Found by CI on PR #5 at `7df06c7`. Implementer: Serif. Base: `7df06c7`.

## Problem

`tests/test_live_integration.py`
`SelectionOrderTests.test_a_page_click_after_the_bridge_handled_the_list_pick_still_wins`
failed once in CI (Chromium): the inspector showed `landing.hero.title`, the title the user
clicked in the page, then `landing.hero.lead`, an older list pick. 25 of 25 local runs
passed. An old answer must never move the selection away from the user's newer pick, and
Studio and the bridge must end on the same target.

## Owned

Studio: `requestSelection`, `refreshSelection`, `sendTrackedSelection`, the
`design:selected` case and the handshake line that clears `live.refreshes`.
`tests/test_live_integration.py`: the "picks Studio sends for the user" section.

## Implementer report

Root cause: `design:ready` clears `live.refreshes` on every handshake, including the
load-time re-hello. A `design:select` Studio sent before that ready and the bridge answers
after it has no entry, and the `design:selected` handler took any reply without an entry
for the user's own choice: it moved `selectedId` and `intent` and superseded everything
else. Failing order: Studio sends `select(lead, fks-sel-1)`; the frame's load sends hello;
Studio receives `design:ready` and clears the entries; the user clicks the title (bridge
posts `selected(title)`, no id); the bridge answers `fks-sel-1` with the lead; Studio moves
to the lead and nothing realigns. The same gap applies to an entry evicted past 20. The CI
message order is inferred from the code, not captured.

Fix (Studio only; bridge and protocol unchanged): `ownRequestSeq(id)` returns the sequence
number of an id Studio issued (`fks-sel-N`, N at most `live.selectSeq`). A reply with no
entry but an own id is an answer, superseded when its target differs from `live.intent`,
so the existing superseded branch realigns. A reply with no id or a foreign id is still the
user's choice.

RED: new `test_a_page_click_wins_over_a_list_pick_the_bridge_answers_after_a_re_handshake`
(stash the list pick at the bridge, dispatch a `load` on the frame, wait for the new ready,
click the title, release): `'landing.hero.lead' != 'landing.hero.title' : the bridge`.
GREEN, and 20 of 20 in a loop. Mutation: disabling the own-id branch fails the new test.
`test_live_integration test_studio_live`: 196 tests OK (Chromium). Not verified: the CI
order itself, CPU-loaded runs, the full suite, the frontend gate, Firefox.

## Review (2026-10-03)

Verdict: **Approved with fixes.** The mechanism is confirmed. The reviewer also forced the
CI-shaped variant (a `refreshSelection` for the lead whose entry a second ready clears,
then a title click): it fails on base with the CI message and passes 20 of 20 patched under
CPU burners. Own-id recognition cannot be abused by a target beyond one extra
`design:select` per forged message; ids outside Studio's range behave as before.
`test_live_integration test_studio_live`: 196 tests OK.

- **F1 (medium-low).** The `design:ready` line that re-sends a kept selection overwrites a
  non-null `intent`. With the patch, a sibling pick in flight across a re-hello is
  realigned back to the old selection (before the patch the pick won). Fix: keep a non-null
  `intent`.
- The new test covers only the list-pick variant; add the refresh-across-ready variant.
- Surviving mutation: marking every own late reply superseded (behaviourally equivalent).

Not established: that this race is what fails CI. CI failed 2 of 2 since `bc25096` and was
green at `3adc1b9`; no local configuration reproduces it (single CPU, CPU burners, CDP
throttling, the headless shell, the whole module). The fix round adds a message trace to
the selection tests' failure message so the next CI failure shows the real sequence.

## Fix round 1 (2026-10-03)

- F1: the `design:ready` line sets `intent` from `selectedId` only when `intent` is null.
  New `test_a_sibling_pick_the_bridge_answers_after_a_re_handshake_keeps_the_pick`: RED on
  the first patch (`'landing.hero.cta' != 'auto:a:button:6'`), GREEN after. Mutation:
  restoring the unconditional assignment fails only this test.
- CI-shaped test `test_a_page_click_wins_when_two_re_handshakes_forget_a_refresh_the_bridge_answers_late`:
  pick the lead, stash the bridge's handling, two synthetic loads (each ready re-sends the
  lead; the second clears the first entries), click the title, release. RED on base
  `7df06c7` with the CI message; its trace shows `selected(title)` followed by replies for
  `fks-sel-2` to `fks-sel-6`, all for the lead. GREEN with the fix.
- Diagnostics: a `trace(page)` helper records every `design:*` message Studio receives
  (time, `requestId`, `targetId`) and every frame `load`; `assert_selected_everywhere`
  includes the trace in its failure message.
- Each new test passes 20 of 20. `test_live_integration test_studio_live`: 198 tests OK.

## Re-review of fix round 1 (2026-10-03)

Verdict: **Approved.** F1 is correct; restoring the unconditional assignment fails only the
sibling test. The CI-shaped test is RED on base and GREEN patched; removing the post-ready
refresh fails it through its stash-count wait. The trace listener runs after Studio's own
handler, so it does not change the order under test, and it lives only in the test's page.
On base its output reads: `selected fks-sel-1 (lead)`, load, ready, load, ready, `selected`
with no id (title), then `selected fks-sel-2..6` for the lead. The four selection tests pass
20 of 20 each on two CPUs; `test_live_integration test_studio_live`: 198 tests OK.
Surviving mutation: dropping the `intent === null` fallback (no path reaches it; defensive).
The CI failure is still not reproduced locally; CI on the fixed head decides.

## The CI cause: a wait that never waited (2026-10-03)

CI failed again at `5696899`, and the new trace showed `selected(lead, fks-sel-1)`, then
`selected(title)`, then `hover(title)`: no late reply. The cause was the test helper
`LiveIntegrationCase.inspector_target`. Playwright's `wait_for_function` drops dict keys
whose value is `None` (`page.evaluate` keeps them as `null`), so `want.name` was undefined,
`new RegExp(undefined)` matched every name, and every plain-id wait returned at once.
`assert_selected_everywhere` then read `#liveTargetName` before Studio had rendered the
bridge's `design:selected`. The selection-order fix above still closes a real race (forced
on base), but it was not the CI failure.

Fix (test-only, implementer Tracking-H): `inspector_target` passes only the key that
applies and the predicate tests `typeof want.name === "string"`. `InspectorWaitTests`
(5 tests) pin the helper; `test_the_inspector_checks_wait_for_a_bridge_that_reports_a_selection_late`
delays `design:selected` to Studio by 150 ms. RED on the old helper: the wrong-id wait did
not time out, the late-render wait read the old target, and the delayed-selection test
failed with the CI message. GREEN after. A sweep of every `wait_for_function` `arg` in
`tests/` and `scripts/` found no other dict carrying `None`. With real waits, all 51
`test_live_integration` tests still pass. Review: Approved (the reviewer reproduced the key
dropping in Playwright 1.62 and the RED/GREEN). `SelectionOrderTests`: 20 of 20 runs.
