# v0.2.1 Task 6 brief: disabled with a reason

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 6) and
`docs/plans/2026-10-03-v0.2.1-pr-b-sdd.md` (ownership, contract with Task 7). Source:
`docs/implementation/audit-2026-10-03-first-run-and-controls.md` (P1, first paragraph).
Implementer: Kerning-6. Runs beside Task 7.

## Problem

Controls that would do nothing stay enabled and give no reason, so users think Studio is
broken. One of them, Sync to file with an empty ledger, writes a placeholder over the
user's existing overrides file (Rule 6).

## Required

A control that would do nothing is `disabled`, with the reason in its `title`, and in an
adjacent hint element where a title alone is easy to miss (Sync to Live App, Sync to file).
It is enabled again as soon as the state changes. The list:

| Control | Disabled while | Reason says (wording yours, plain English) |
|---|---|---|
| Sync to Live App | no target connected | connect a page first |
| Restore Page Text | no target, or no text edits | nothing to restore |
| Reset this element | the selected element has nothing to reset | no changes on this element |
| Width buttons; Select / Interact | Specimen view | only for the Live App view |
| Load free fonts | fonts already loaded | already loaded |
| Sync to file, Copy, Download | the ledger is empty | no changes to save yet |
| Colour fields | they do not match the chosen colour source (toolbar and every slot) | which source is active |
| Style / cut | the family has one cut | one cut only |
| Image Width | no image chosen | choose an image first |
| Focus pop-out | the pop-out window is closed | the pop-out is closed |

Sync to file must not write a placeholder over an existing file when the ledger is empty,
by any path (button or automatic sync). If that write happens in a function outside your
ownership, guard it there with the smallest change and record it as a deviation in your
report.

## Design (binding, from the SDD plan)

- A new `refreshControlStates()` decides every state above, and a new
  `setDisabledReason(el, reason)` sets `disabled`, `title` and the hint (`reason` null
  re-enables and restores the control's normal title).
- Call `refreshControlStates()` once at each existing refresh point (connect, disconnect,
  selection, ledger change, view switch, font load, pop-out open and close). Do not
  restructure those functions.
- You may edit the `title` attributes and add hint elements next to static controls in the
  markup.

## Owned

Studio (`font_kit_studio_v0.1.1.html`): `refreshControlStates`, `setDisabledReason`, the
one-line calls at refresh points, `title` attributes and adjacent hint elements of static
controls. New test module `tests/test_studio_controls.py`.

Must not touch: the arrange block of `renderLiveInspector`; the preset select, kit select,
one-cut chip rendering, Arrange sibling click, Library loaded label, recursion-block and
invalid-colour messages, SVG-fills note (all Task 7); the `<style>` block (Task 8). If you
need a disabled reason on a Task 7 control, stop and report it. `requestSelection`, `refreshSelection`, `sendTrackedSelection` and the
`design:selected` case belong to a selection-race fix running beside you: call them, never
edit them.

## Tests (`tests/test_studio_controls.py`, new)

For each control: the rendered `disabled` state and the reason text (title and hint) in the
state that earns it, then enabled again after the state changes. Use the real Studio and
the demo target through `LiveCase` (`tests/test_studio_live.py`) or `LiveIntegrationCase`;
at least one case runs against the real bridge. One test proves Sync to file with an empty
ledger leaves an existing overrides file byte for byte unchanged. Name your RED tests before
writing code. Characterize controls that already behave correctly as passing.

Changes to existing tests (an assertion that relied on an enabled control) are allowed
only when the old behaviour is the defect; list each one with why.

## Gates

`python scripts/verify.py --static-only`; `node --check fontkit-bridge.js`;
`PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python -m unittest test_studio_controls test_studio_live test_font_kit_studio_v011 -v`.
Do not run the full suite. Task 7 runs browser tests beside you on 4 shared CPUs.

## Report

Append "## Implementer report" here (your worktree copy): RED and GREEN per control, a
mutation per behaviour, deviations, changed existing tests, final `git diff --stat`, and
what you did not verify.
