# Task 8 brief: Studio wording that points at the wrong cause

Plan Task 8, wave 1. BASE `5443ff6`. Worktree `the task's worktree`. Audit rows A1-3b and A2-3b (one change), G2-7, D2-5 and C2-3c
(one change). Mode code; three patches, one per row group. Budget: about 60 gross lines of code and 110 of tests.
Rules: `../constraints.md` (O31 approves New strings 5, 7 and 8 as written). Protocol, export format and version labels do not change.

## Why

1. After the 4 s timeout Studio shows "No bridge answered at ... within 4 s." and `#bridgeHint` says the page may lack the script tag
   (`fontkit-studio.html:1122`; badge set at 4797; npx text `NPX_BRIDGE_HINT` at 4820). On an error page (404, 400) the proxy adds no
   bridge, so the user hunts for a tag that is not the cause. Studio cannot see the response status, so this is wording only.
2. Both Adobe kit fields append a `<link>` to Studio's own page and say "Loaded" (1802 `kitStatus`, 2392 `composerStatus`). Nothing sends
   the kit to the Live App, so "Loaded" reads as if the app got it.
3. The Sync to Live App flow never says Sync also restyles elements by role inline, while Changes, Copy and JSON carry the tokens only
   (README says so; `README.md:429` at BASE covers the Changes panel and Copy, not the inline restyling).

## Owned files (exact)

- `fontkit-studio.html`, only: `#bridgeHint` paragraph (line 1122); a new note element directly after `#syncToAppHint` (1194);
  `kitStatus.textContent` in the `link.onload` (1802); `composerStatus.textContent` in the kit `link.onload` (2392); `NPX_BRIDGE_HINT`
  (4820 and its use at 4873). Other tasks edit other regions of this file at the same time: 1051-1053, 1507, 2131-2168, 2532, 3736,
  5922, 6034, 6396-6424, 6847, 7197 are theirs.
- `tests/test_studio_wording.py` (new module, Addendum 1). One existing assertion changes: `tests/test_studio_npx_hints.py:116`
  (`assertEqual(... NPX_BRIDGE_HINT)`, with the constant at 24-25).
- Read-only: everything else. No CHANGELOG edit; Task 18 owns the ledger lines.

The plan cites hint assertions at `test_studio_first_run.py:26,177-193,359-360`, `test_live_integration.py:1838-1846`,
`test_studio_live.py:386-387,1203-1204`. At BASE those are `assertIn` or `is_visible` checks (first_run 180, 194, 361) and need no edit,
because the new sentence is appended. Only `test_studio_npx_hints.py:116` is an exact match. Name it in the commit body of patch 1.

## Read first

- `fontkit-studio.html` 1120-1123, 1191-1195, 1795-1806, 2380-2396, 3744-3749 (`setBridgeStatus`), 4817-4826, 4870-4874, 6955-6970.
- `tests/test_studio_npx_hints.py` 20-35, 105-120; `tests/test_studio_first_run.py` 170-195 (how a no-bridge page is opened).

## Requirements

1. (A1-3b, A2-3b) Append New string 5 verbatim, after one space, to the `#bridgeHint` text and to `NPX_BRIDGE_HINT`:
   `If this is an error page (404 or 400), the proxy adds no bridge to it; go back to a normal page.`
   On the served path the `#bridgeHint` text ends with that sentence, inside the paragraph and after the `bridgeHintServe` span's
   place (the span stays hidden when served). Under npx the hint is exactly the old npx text, a space, then the sentence.
   Oracle: the literal sentence, read from the visible hint after the badge says "No bridge answered at ... within 4 s." The badge
   text and `BLOCKED_LOOPBACK_TEXT` do not change; assert the badge literal still matches.
2. (G2-7) On load of either kit field, the status is New string 7 verbatim:
   `Loaded in Studio only. The Live App does not get this kit; add it to the app itself.` See Open question 1. The error texts
   ("Could not load kit ...") do not change. Oracle: the literal. A user who loads a kit sees it.
3. (D2-5, C2-3c) A visible, always-present one-line note next to the Sync to Live App button reads New string 8 verbatim:
   `Sync also restyles elements by role inline. Changes, Copy and JSON list the tokens only.` See Open question 2. Oracle: the literal,
   visible with no page connected. The Sync button, its disabled reason and `syncToAppHint` behave as before.

## Tests (`tests/test_studio_wording.py`, one class per patch, Given/When/Then docstrings)

Reuse the page-opening helpers and `test_support` the neighbouring modules use; do not invent a server. Each test runs per engine in
`ENGINES` as they do.

- Patch 1, RED: Given a served Studio and a target page with no bridge, When the 4 s badge appears, Then the hint contains string 5.
  Fails today: the hint ends at "Connect Live App." Second test, RED: Given `?token=` (npx mode), When the same, Then the hint equals
  the npx text plus string 5. Realistic break: appending to only one of the two paths fails one test.
- Patch 2, RED: Given the Adobe kit field with a kit id and the stylesheet request fulfilled (route it, no network), When it loads,
  Then `#kitStatus` reads string 7. One test for the Composer kit field (`composerStatus`, same route). Break: restoring "Loaded https://".
- Patch 3, RED: Given a freshly opened Studio, When the page is idle, Then the note beside `#btnSyncToApp` is visible with string 8.
  Break: hiding it behind `hidden` fails it.
- Updated: `test_studio_npx_hints.py:116` compares to the old npx text plus string 5, built in the test from two literals.

## Focused command (from `the task's worktree`, timeout 600 s)

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_wording test_studio_npx_hints test_studio_first_run test_support -v`
One module at a time if a run is slow; no shards; never start a dev server. Landings also run `test_studio_roles`, `test_role_routes`
and `test_r2_integration` (the controller does this).

## Patches (in this order, each on BASE plus the previous)

1. `task-8-A1-3b.patch`: `fix(studio): say an error page can be why no bridge answered`
2. `task-8-G2-7.patch`: `fix(studio): say an Adobe kit loads in Studio only`
3. `task-8-D2-5.patch`: `fix(studio): note that Sync also restyles roles inline`

No CHANGELOG line here (Task 18). Commit bodies carry no process state and no attribution trailer.

## Open questions

1. G2-7 and the Composer count. String 7 has no count, but `composerStatus` today shows "Loaded 1/2 Adobe kit stylesheets."
   Options: (a) string 7 verbatim on every load, dropping the count; (b) string 7 only when all kits loaded, keeping the count while
   partial; (c) a new string with the count (needs approval). Recommend (b): no unapproved text, progress kept, and the final line is
   the approved one.
2. D2-5 placement. The plan says "the Sync wording near 4814 and 6754", but those are `NPX_SYNC_TEXT` and the Sync to file reason,
   which are about Sync to file (CSS only) and cannot take a note about role restyling, so the plan's cause points at the wrong lines.
   Options: (a) a static `<div class="composer-status">` after `#syncToAppHint` (1194); (b) append to the success line in
   `syncToLiveApp` (6959), visible only after pressing Sync; (c) the button's `title`. Recommend (a): visible before the first press,
   no shared state. It sits in a region no other task owns.

## Controller rulings

1. Open question 1: use string 7 only once all kits have loaded, and keep the count while partial.
2. Open question 2: a static visible note after #syncToAppHint.

## Review fixes (binding: these govern over the text above)

1. Requirement 2 reads: the Adobe kit field shows string 7 on load. The Composer kit field shows string 7 when `loaded === ids.length`, and otherwise the existing `Loaded n/m Adobe kit stylesheets.`
2. Add one test with two ids (`abc123, def456`): the route handler stores the two `route` objects instead of fulfilling. The test fulfils the first, waits for `#composerStatus` to read `Loaded 1/2 Adobe kit stylesheets.`, then fulfils the second and waits for string 7. Break: an unconditional string 7 fails the `1/2` wait.
3. Fulfil routed stylesheets with `content_type='text/css'`, or `link.onload` may not fire.
4. Requirement 1: the served hint ENDS with string 5. Test with an end-of-text check on the whitespace-normalised visible hint, not `contains`.
5. Give the note the id `syncRoleNote`, and assert it shares a parent with `#syncToAppHint`.
6. Opened from disk, the shown span may end with a full stop, so the appended sentence does not run on.
7. The second patch-1 test stays, because the existing one needs Node and the package server; say so in its docstring. The sentence literal is defined once per test module, not shared.
