# Task 7 brief: sync reads and dead code in Studio

Plan Task 7, wave 1, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit rows S09, G2-6, G2-19. Budget: about 60 gross lines
(about 10 of source, about 50 of test). Three patches, one per row. Rules: `../constraints.md` (O27 to O31, O38 to O41 bind).

## Why

- **S09.** Sync to Live App sets `--font-display` from `state.slots[0]` when no slot role matched title, display or hero
  (`fontkit-studio.html:6852`). When the first slot is a Row or an Image it has no family, so `byFamily(undefined)` returns `fonts[0]`
  (`:2181-2183`), a family no text slot uses. The sibling fallback right below (`:6853-6860`) already reads "the first text slot ... a slot's
  position says nothing". The display fallback must do the same. The plan cites 6847; at BASE the line is 6852 (6847 is the role branch).
- **G2-6.** `cssStack` (`:1505-1508`) spreads `f.aliases`; `grep aliases` finds only that line in `fontkit-studio.html` and
  `fontkit-bridge.js`. No library font defines it.
- **G2-19.** The inspector's `const familyOptions` (`:6039`) shadows the function `familyOptions(select, selected)` (`:2536`, called at
  `:3128` and `:3324`). The audit cites 6040 and 2532; the plan's 6034 is the enclosing render function.

## Owned files (exact)

- `fontkit-studio.html`: `cssStack` (1505-1508); the local at 6039 and its one use in the template at 6046 (the `${familyOptions}`
  inside the Family select; grep the render function 6034-6100 for other uses of the local); the fallback line 6852 in `compositionPatch`
  (6841-6860). Nothing else. Do not touch the function at 2536.
- `tests/test_studio_sync_reads.py` (new, Addendum 1), for S09 only.
- `CHANGELOG.md`: no line (S09 changes a token only when a Row or Image sits first and the first text family differs from Fraunces;
  the controller writes ledger lines). State this in the report.

Everything else is read-only. Other tasks edit `fontkit-studio.html` at the same time; stay inside the lines above.

## Read first

- `fontkit-studio.html` at BASE: 1505-1508, 2181-2183, 2185-2200 (`makeTextSlot`), 2285-2301 (`rowdemo`), 2759-2765 (`moveSlot`),
  6034-6046, 6841-6865.
- `tests/test_studio_live.py`: `LiveCase` (44-130), `StudioCompositionFontTests` (4168-4215) for `open`, `sync`, `updates`.
- `docs/implementation/audit-2026-11-06-real-apps.md`: rows S09 (124), G2-6 (167), G2-19 (175).

## Requirements

1. **S09 (patch 1).** In `compositionPatch`, the `--font-display` fallback uses the first slot with `type === "text"`, and sends nothing
   if there is none. Observable: with a Row or Image first, the synced `--font-display` is the first text slot's stack. Oracle: a second run
   of the same composition without the move gives the same token (literal compared to a second run, not to the code).
   Keep the loop and the sans, serif, mono fallbacks unchanged.
2. **G2-6 (patch 2).** `cssStack` returns `"<f.css || f.family>", <f.fallback>`; the `aliases` read is gone. Oracle: before the change, on
   BASE, dump `fonts.map(cssStack)` in the page (`page.evaluate`) into the report; after, the dump is identical (all library fonts). No new
   test: no behaviour changes.
3. **G2-19 (patch 3).** Rename the inspector local to `familyChoices` (all its uses). The function at 2536 is no longer shadowed. Oracle:
   the Family select in the live inspector still lists every library font by name (existing live-inspector tests plus the landing tests
   below); no page error. No new test.

## Tests

New module `tests/test_studio_sync_reads.py`, one class, one test. Copy the harness needs from `test_studio_live.py` (import `LiveCase`
and `ENGINES` as that file does; see its header for the import form).

- `test_display_token_ignores_a_row_placed_first`
  - Given: the default `rowdemo` composition, connected to the fake target, with the first text slot (Wordmark) changed to a family other
    than Fraunces in the inspector. `fonts[0]` is Fraunces and a Row has no family, so keeping Fraunces would pass without the fix.
  - When: Sync is run once as is (control), then the Row is moved to the top with its Up button (twice, `Move up`) and Sync is run again.
  - Then: both syncs send the same `--font-display` token, equal to the chosen family's stack read from the first sync (not
    Fraunces). On BASE the second differs: RED, because `state.slots[0]` is the Row and `byFamily(undefined)` gives Fraunces.
  - The realistic break: restoring `state.slots[0]`.
  - Use `self.updates(frame)` as `StudioCompositionFontTests.sheets_sent` does and read `patch['tokens']['--font-display']` of the last
    two composition updates (those without `targetId`).

G2-6 and G2-19 are refactors: show GREEN before and after, never manufactured RED. No mutation file is created.

## Focused command

From `the task's worktree`:
`PYTHONPATH=tests FKS_ENGINES=chromium timeout 600 python -m unittest test_studio_sync_reads test_support -v`

Then, one module at a time, the landing tests: `test_studio_roles`, `test_role_routes`, `test_r2_integration`, and
`test_studio_controls`. Run `test_studio_live` only by class if the inspector Family select is exercised there (grep `liveFontFamily`).
No shards, no dev server.

## Patches

Order and subjects (each at most 72 characters; no process state):

1. `task-7-S09.patch`: `fix(studio): take the display family from the first text slot` (source change plus the new test module).
2. `task-7-G2-6.patch`: `refactor(studio): drop the unused font aliases read`.
3. `task-7-G2-19.patch`: `refactor(studio): stop shadowing familyOptions`.

Each patch applies on BASE alone and in order. Report for each: the files, the focused result, and the G2-6 before/after dump.

## Open questions

1. The Row's missing family falls back to `fonts[0]`, which is Fraunces, the same as the default Wordmark. On the default preset the bug
   is therefore invisible, so the test changes the first text slot's family first. Recommendation: keep this test design. Alternative: import
   a composition JSON with a non-Fraunces first text slot (more setup, same oracle).
2. Plan names `tests/test_studio_live.py` and `tests/test_studio_controls.py` as touched; Addendum 1 sends new tests to
   `tests/test_studio_sync_reads.py`. Recommendation: follow Addendum 1 (the brief does).

## Controller rulings

1. Open question 1: keep the design; the test changes the first text slot to another family first.
2. Open question 2: follow Addendum 1; new tests go in tests/test_studio_sync_reads.py.

## Review fixes (binding: these govern over the text above)

1. After the first Sync each Move up sends an automatic update, so the sequence is sync1, auto(move1), auto(move2), sync2. The FIRST composition update is the control and the LAST, after the second Sync, is the moved run. Assert both equal each other and the chosen family's stack, and that the chosen stack differs from the Fraunces stack.
2. `self.sync(page)` returns early on the second call, because the badge already matches. Wait on your own condition: poll `len(self.updates(frame))` to the expected count, and assert that count (4 for this sequence) before reading.
3. "The inspector" means the composer's `#slotInspector [data-bind="family"]`, not `#liveFontFamily`.

---

# Task 7 follow-up: assert the chosen family's stack

The worktree `the task's worktree` holds Task 7's finished work, unstaged. Keep it. See the Important finding in `task-7-code-review.md`, and Review fix 1 in `task-7-brief.md`.

**Finding.** `tests/test_studio_sync_reads.py:41-42` asserts only that the first and last tokens match and that the first differs from Fraunces. It never asserts the token is the chosen family's stack. With the fallback changed to the last text slot, the test still passes.

**Do this.** In that test, assert the token equals the chosen family's stack, taken from an independent literal for that family (`"JetBrains Mono", monospace` if that is the chosen one), not from the code under test.

Show the break failing: change the fallback to the last text slot, run the test, show it fails on the code the test loaded, then restore. Touch only that test file. Run `test_studio_sync_reads` once. Do not write a patch: the controller regenerates the row patches.

Append to the REPORT what changed and the break shown, and add this CHANGELOG line to its Handoff, adjusted if the wording is wrong: the synced display font now follows the first text slot when a Row or Image sits first. (Controller ruling: S09 gets a CHANGELOG line, since a user with a Row or Image first sees the change. This replaces the brief's "no line".)
