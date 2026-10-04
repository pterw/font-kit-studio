# v0.2.1 Task 7 review: dead or misleading controls

Reviewer: Leading. Base `16a07ce` plus the uncommitted Task 7 diff. Date: 2026-10-03.

Verdict: **Approved with fixes.** All ten items behave as the brief says under real clicks;
the fixes are test gaps and one stale comment. No product change is required.

Gates (Chromium): static checks pass; `node --check` OK;
`test_studio_dead_controls test_studio_live test_font_kit_studio_v011 test_preview_server
test_studio_first_run test_studio_import_link`: 294 tests OK in 406 s;
`test_live_integration test_bridge_runtime test_studio_review_findings test_studio_stage`:
194 tests OK in 235 s.

## Rulings

- Item 1: edits are a signature of slots, canvas width and background against the baseline
  recorded at each preset apply; an import counts as edits; an undo back to the preset
  values does not ask (except slot text once touched). Cancel restores the select and sends
  nothing. Linked sync is sent once per applied preset (select untouched +1, Apply on an
  untouched preset +0, Cancel +0, Accept +1). The Apply button stays: the select fires no
  change for the already-selected preset, so Apply is the only reset to it.
- Item 9: validate on commit (change, Enter, blur), never per keystroke; typing clears the
  message. Typed `#123456` key by key shows no message and changes nothing until Enter.
- Item 8: Connect stays enabled; pressing it again with the same recursive address is
  refused each time and the frame is never loaded (`#`, query, `127.0.0.1` and path-case
  variants too).
- Rule 5: every new message goes through `textContent` or `escapeAttr`;
  `<img src=x onerror=alert(1)>` as colour text renders as text.
- Deviations (`setFreeFontStatus`, `#targetUrlProblem`, `refreshArrange` keeping the chosen
  container, the empty-value "No other containers" option) and the two changed existing
  tests are accepted.

## Findings

1. Medium. Item 9 "nothing is sent" is unproven: the test checks only the page colour,
   which the bridge would keep anyway. Sending the invalid text survives. Count
   `design:update` messages.
2. Medium. Item 9 has no keystroke-level test; pin the commit-time validation.
3. Medium. Item 1: dropping width and background from the signature survives; imports as
   edits and linked-sync counts are untested in the new module.
4. Low. `tests/test_live_integration.py:1621` still says "The guard resets the field".
5. Low. `refreshArrange` keeping the chosen container is untested (removing it survives).
6. Low. Item 7: the Live Target family-pick path to the Library label is untested.
7. Low, accepted. Slot text typed back to the original still counts as an edit.
8. Low. Two strings for the same loaded state ("Families load as their cards scroll into
   view." and "Free fonts are on: families load as their cards scroll into view.").
9. Low. Expect a textual conflict with Task 6 near `#targetUrlHint`.

## Mutations

| Mutation | Result |
|---|---|
| Signature of slots only | survived (3) |
| Cancel also applies | killed |
| Invalid colour also sent | survived (1) |
| No clear on input; no clear on valid change | each survived (the other path clears) |
| `refreshArrange` forgets the container | survived (5) |
| Chip threshold `< 3` | killed |
| No label write in `allowFreeFonts` | survived (6) |
| No clear at the start of `resolveTarget` | survived (input clears first) |

Not verified: Firefox and WebKit, the frontend gate, the full suite, the 390 px layout of
the new Move into hint beyond the existing test, a real Google Fonts load.

## Re-review of fix round 1 (2026-10-03)

Verdict: **Approved.** Findings 1 to 6 and 8 and the style nits are closed; the only product
change is the `FREE_FONTS_ON_STATUS` constant, defined before both uses. Every earlier
survivor is now killed, plus eight new mutations (Cancel broadcasting to a linked page,
Apply re-applying an untouched preset, width or background left out of the signature, an
import resetting the baseline, invalid text sent per keystroke, no consent on the inspector
family pick, a different remembered-path string). `test_studio_dead_controls
test_studio_live test_preview_server test_studio_first_run test_studio_import_link`:
282 tests OK in 371 s.

- The sibling click renders the inspector name, the list marker and the position text in
  one step (about 25 recorded runs). The test's earlier flake came from the shared helper
  `inspector_target`, which returns at once for a plain id, so the test read the list
  before Studio had rendered. That helper is outside Task 7 and is fixed separately.
- `polling=50` in the linked-preset test is needed (the hidden frame gets no animation
  frames) and cannot hide an extra send: each step waits for at least the count, then
  asserts the exact count.
- Low: the 250 ms wait near `tests/test_studio_dead_controls.py:237` needs its comment.
- Closed by the controller on reading the diff: the wait moved into a `settled` helper with its comment; `test_studio_dead_controls`: 26 tests OK.
