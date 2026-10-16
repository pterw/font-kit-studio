# R2.S2 code report (phases 1 and 2)

Mode: code. Worktree C:/fks/ts2, BASE 90e8a87f549245e65f19a6aa8ab53f0a00fd6ded (detached). Patch:
`task-s2a-code.patch` (3 files, +2170/-129; `git apply --check -R` passes; `git diff --cached --check` clean).
Files: `fontkit-studio.html`, `tests/test_studio_roles.py`, `tests/test_r2_integration.py`. No shared file touched.

## Controller corrections applied
1. Brief sentence now reads: a valid Apply or Clear receipt, reset-all, a valid ready snapshot or a new document are the only
   acknowledgements that change the shown preview. A role op in flight at reload is dropped with a visible status
   (`resetRoleSession` sets it; it survives the new ready) and its late receipt for the old document changes nothing
   (tests: reload in flight, reload queued).
2. Fake peer mirrors the pins: every accepted apply/clear bumps revision once (receipt revision = base + 1, also in the
   hybrid peer via `fake.bumpRevision()`); `losses[].property` is one of the six RoleInput keys; counts satisfy
   `0 <= mismatched <= checked <= matched`.
3. R2.3 note: matched always equals checked. Studio labels the numbers "checked N eligible text elements, mismatched M",
   never as selector reach, and still validates the full inequality. Zero shows "no eligible text found for this selector".

## What was built (Studio)
Controls inside `#detectedRoles` only: per-row checkbox, family, size, weight, line height, tracking, case (all empty,
observed values as placeholders, aria names "<field> for <name> (role-N)"); baseline label; Apply selected roles; Clear
preview; visible `data-hint-for` reasons; preview block (exact heading, focusable `pre` with overflow auto, own
`role=status` "Role preview status", removed-roles note, outcome list); Reset all page edits with `window.confirm`.
Drafts live in `roleDrafts` keyed by issued id, cleared with `roleView.ids`; rows rebuild only when a new result arrives and
focus/caret are restored. Queue kinds `roles-apply`/`roles-clear` with dispatch-time document check, barrier in coalescing,
import-safe, receipts/rejections via their own handlers, timeout and late receipt, `roleQueueIdle()` re-arms auto-sync.
`acceptRoleReady` accepts valid non-empty snapshots (digest, 128 KiB, RoleInputs, newer-revision guard) and marks the
preview unconfirmed on an invalid ready or reload. `BRIDGE_TYPES` gains `design:roles-applied` (not `roles-page`).
Untargeted-reset branch finished: overrides, `live.structure` (from the emptied ledger), saved tokens and
`reconcileSavedOverrides` so no banner appears; the reply's empty `roleState` clears the preview.

## Interpretations to confirm
- The removed-roles sentence is its own element (`#rolePreviewRemoved`, aria-live) so the stale status can stay exactly
  `Preview applied; page changed before checks finished`.
- The Json code tab and its Download show the page's acknowledged revision, which a role op raises by one (needed for the
  next baseRevision). The test asserts every byte identical except that one number (+1); the composition JSON export
  (canonicalRevision), CSS/HTML tabs, Download of CSS and the Sync body are fully identical.
- Invalid typed fields block Apply only for selected rows; unselected rows are flagged `aria-invalid` but not blocking.
- Fractional input is rounded to the contract decimals (like canonicalLiveValue); weight must be a whole number.
- Accepted roles whose issued id is not in the current rows are not carried: Apply replaces the set and names them as removed.
- No sync endpoint gap: built in-module with route interception.

## RED / GREEN
RED: the new tests run against BASE `fontkit-studio.html` (swapped in, foreground, restored byte-identical; `cmp` verified):
`Ran 60 tests ... FAILED (failures=2, errors=39)` (output kept in scratch `red-output.txt`). The 40 failing names are the
new behaviour tests (draft controls, validation, apply/receipts, hostile receipts, queue, rejections, timeout, reload, import,
reset-all, ready snapshots, capability gating, limit, text-only, accessibility, hybrid interplay, real-Studio R2.2 gating
`test_current_bridge_keeps_detect_and_says_why_apply_and_clear_are_off`: no Apply control, count 0). The 19 that passed at BASE
are preserved behaviour, characterized GREEN: the S1 boundary tests (with the new recorded-message, selector-negative,
size-limit and per-shape assertions), the digest-vector test and the existing fullscreen/long-family/URL/accessibility
integration tests.
GREEN (final tree, focused gates from the brief):
- `python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support` -> `Ran 167 tests ... OK`
- `python -m unittest test_studio_live.StudioProtocolTests test_studio_live.StudioReviewFixTests test_studio_live.StudioFixRound1Tests test_studio_stage.PreviewWidthTests test_studio_live.StudioFullscreenTests test_studio_first_run.FullscreenTests test_studio_visual.LiveAppViewTests` -> `Ran 46 tests ... OK`
- `python scripts/verify.py --static-only` -> provenance PASS lines, browser SKIP; `python -m ruff check tests/test_studio_roles.py tests/test_r2_integration.py` -> All checks passed; `git diff --check` -> exit 0.
Full suite not run (controller instruction). Chromium only (FKS_ENGINES=chromium); no other engine run.

## Audit items done
I-S1 (peer records every message; tests assert exact sent types), I-S2 (multi-byte request limit with a character-count
control; detected reply at 1 MiB and 1 MiB + 1 built from a valid font-family field; receipt at 1 MiB / +1 via valid loss
selectors; receipt CSS at 128 KiB / +1 with correct digests), I-S3 (pseudo-class, braces, semicolon, line break, comment,
at-rule, url(, expression(, 2,001 chars, nth-of-type 10000, 33 selectors; positives 2,000 chars, 9,999, 32 selectors),
I-I1 (screenshot to absolute path removed), M-I1 (print removed), M-S1 (ready table extended: algorithm, fractional version,
201-char document, non-array roles, roles not RoleInputs rewritten), M-S2 (always-true `assertIn('Body')` dropped), M-S3
(one subtest per hostile shape, each with a fence; the failing shape is named). Given/When/Then docstrings on all new tests
and the edited existing ones.

## Mutations (each foreground, source restored byte-exact in `finally`, bytes asserted equal)
All 25 killed: operation match, receipt revision, receipt identity (document/page version), digest check (hostile table +
ready), null-URL/complete-receipt rules, legacy reply settling a role op, dispatch document check, text-only outcomes, text-only
CSS, drafts surviving render, focus surviving render, coalescing barrier, badge/ledger write by the receipt handler,
plain-only adapter, reset-all wording path, auto-sync re-arm, import keeps role ops, import does not count role ops, reset-all
consumes roleState, reset-all saved-order sync, ready revision guard, limit flag, unconfirmed on invalid ready, Apply request
bytes, BRIDGE_TYPES entry. (Scripts and first-failure lines are in scratch `mut.py`, `mut*.out`.) The dispatch-time adapter
guard I first wrote was unreachable from the UI, so it was removed rather than left untested; plain-only is guarded at build.

## Accessibility and layout
Heading, two distinct named status regions, focusable `pre` with `overflow-x:auto` that scrolls inside itself, focus rings on
Apply/Clear/Reset, `aria-describedby` to the visible hint, contrast >= 4.5 for hint and both statuses, and no panel/page
overflow at 1440 and 390 px with an unbroken 250-character family. Per-element reset persistence characterized (hybrid):
targeted reset keeps the preview and, with Auto-sync off, writes nothing until the next Sync, which writes the state without the
element's edit.

## Deviations / gaps
- Fake-peer wait helpers use `polling=50`: Playwright's default rAF polling stalls in an off-screen cross-origin frame.
- Short fixed waits (300-450 ms) only to prove an absence (no resend, no early sync); everything else awaits a condition.
- Real Studio cases that need the R2.3 bridge are phase 2. The R2.2 gating test asserts the current bridge's capabilities and
  must be converted in phase 2 (see Handoff). `Preview this role` draft seeding assumes ids from an earlier Studio instance
  still map to the same role (not knowable from the wire).
- Untracked scratch only under the scratchpad; no server left running; every context closed by `addCleanup`.

## Handoff
Phase 2 must do (BASE 68b2a87 with this patch applied):
- Convert `test_current_bridge_keeps_detect_and_says_why_apply_and_clear_are_off`: R2.3 advertises `roleStylesheet`, so serve the
  bridge without that capability only if a stable test hook exists; otherwise drop it and keep the fake-peer
  `test_a_bridge_with_detection_only...` as the gating proof.
- Real-bridge cases: Apply by keystrokes (24px on `[data-design-role="Body"]`, `ordinary.body` 16px), Clear restores author
  `main` outerHTML/computed styles, replace/repeat/idempotent clear, real post-commit rerender (stale status, queued inspector
  edit and Clear settle), reset-all with the real empty roleState (dismissed sends none, accepted sends one), inspector edit
  surviving Apply/Clear with a counted mismatch and the receipt's reason, CSP `stylesheet-blocked`, 2,001-char URL and
  valid-to-unsupported, Detect-after-Apply baseline, ready after re-hello, fullscreen regression with populated S2 controls and
  one restored placement mutation. Confirm revision +1 on repeated clear and `roles: []` against the R2.3 report (Additions 3-4).
Drafts for shared files:
- CHANGELOG Unreleased: "Studio previews role styles: draft font family, size, weight, line height, tracking and case per
  detected role, Apply and Clear a page-only preview (never exported or synced), and Reset all page edits."
- Ledger event: "R2.S2 phase 1: Studio role preview controls, receipts, queue kinds and reset-all against fake peers; 25
  mutants killed; focused gates 167 + 46 tests OK, chromium only."
- Commit why-body: "Role previews must be explicit and acknowledged. Drafts stay separate from detected baselines and accepted state;
  Apply and Clear travel the existing revision queue and settle only from their own validated receipts, so a preview never
  touches saved overrides, exports or sync. Reset all page edits is the one explicit untargeted reset and clears the preview
  from the bridge's empty role state."

## Fix round 1
Patch: `task-s2a-code-r1.patch` (full diff against 90e8a87, 3 files, +2288/-129; `git apply --check -R` passes; `git diff --cached --check` clean).
Mutants ran from `s2a-r1-mut.py`, foreground, source restored byte-exact in `finally` (bytes asserted). The R2.2 gating test is untouched.

| Finding | New or changed test | Evidence |
|---|---|---|
| I1 page generation | `test_a_receipt_never_lowers_a_newer_page_generation_learned_from_a_detect` (route a: Detect reply at 5, Apply receipt at 0, next request carries 5) | GREEN on the fix; mutant (`pageVersion < current.pageVersion` removed) KILLED (FAIL) |
| I2 late legacy reply | `test_a_late_design_applied_with_a_timed_out_role_ops_id_does_not_settle_it` (Apply times out, `design:applied` with its id, then its receipt is rendered; badge unchanged) | GREEN; mutant (`\|\| isRoleOp(op)` removed) KILLED |
| m1 rounding | `test_typed_fractions_are_rounded_to_the_contract_decimals_in_the_sent_request` (12.346 -> 12.35, 1.2346 -> 1.235, 0.12346 -> 0.1235 on the sent request) | GREEN; mutant (`roundTo` dropped) KILLED |
| m2 handle | `exports()` reads with `Path(...).read_bytes()` | focused log has 0 ResourceWarning lines |
| m3 downloads | `exports()` now downloads each of Css, Html, Json tabs and compares all three (Json aligned on the one revision number) | docstring corrected; test GREEN |
| m4 unselected invalid field | Studio: per-row note `#roleNote-<id>` with the reason, `aria-describedby` on the field; asserted in the row-blocking test (visible text names row and field, says the row is not selected, hides and drops `aria-describedby` when fixed) | RED before the fix (`False is not true`), GREEN after |
| m5 ignored late receipt | Studio keeps `rolePreview.shown` and appends the "ignored" sentence; `test_an_ignored_late_receipt_keeps_the_status_and_counts_of_the_preview_still_shown` | RED before (status startswith failed), GREEN after |
| m6 removed note after reload | Studio: a ready installs state with `announce=false`; reload test asserts `#rolePreviewRemoved` is empty | RED before (`'Removed from the preview: Body.' != ''`), GREEN after |
| m7 wrong origin | `test_a_receipt_from_a_foreign_origin_while_the_op_is_in_flight_changes_nothing`: the frame navigates to `evil.test`, whose page is held loading (held image route) and posts a receipt with the right session and request id; Studio keeps "Applying role preview…" | GREEN; mutant (origin check in `acceptBridgeMessage` removed) KILLED |

The m4 change first failed the existing 128-row and limit tests (`Cannot set properties of null`): rows without an issued id have no draft note. Fixed with a guard, covered by those tests.
Gates after the final tree: first focused command `Ran 172 tests ... OK`; second `Ran 46 tests ... OK`; ruff clean; `verify.py --static-only` no FAIL; Chromium only; full suite not run.
Time cost: two new tests wait for the real 8 s request timeout (condition waits, no fixed sleeps).

## Phase 2
Worktree C:/fks/ts2b, BASE 4d3b0bba8ad75c333c2fb0c34821cd0222524999 (R2.3 and R2.5), phase 1 + fix round 1 applied first.
Patch: `task-s2b-code.patch`, full staged diff against 4d3b0bb, sha256 `e63f1826751e28e30aa03cbee9066c9bb550cdcb077a42cb27b67f2f05188210`
(3 files, +2658/-130 in total; phase 2 adds about 370 lines: Studio +35, tests about +335). `git apply --check -R` passes.

Studio changes: `winningSelector` is null or bounded text (1-2,000 characters, no control characters, `roleLossSelector`), shown only
through `textContent`; outcome lines read "matched N, checked M eligible text elements, mismatched K", with "N matched elements have no
rendered text and were not measured" when a complete outcome has `checked < matched`, and "no eligible text found" only when `checked` is 0;
every reason reads in plain words (author rule "overridden by <selector>", inline, inherited "inherits from parent via <selector>",
unreadable sheet, complex cascade, blocked sheet, "not attributed in time").

RED/GREEN
- RED (fake peer, before the Studio change): the bounded-text/plain-words test timed out because a receipt naming `.card p` was dropped as an
  invalid selector (the finding), and the apply and zero/stale/budget tests failed on the new wording ("matched N" absent, old reason texts).
  GREEN after: `Ran 15 tests ... OK` for the apply class.
- Hostile table: `loss selector body` removed from the rejected rows (valid text now); kept empty; added over 2,000 characters, line break, NUL and
  non-text selector (all rejected).
- Real bridge (`StudioRoleBridgeTests`, 12 tests): they passed on first run because Studio already handled the receipts; characterized GREEN,
  no manufactured RED. The `.card p` winner and the plain-words checks depend on the new code and are pinned by mutants (below).
- The R2.2 gating test was dropped (R2.3 advertises `roleStylesheet`); the fake-peer `test_a_bridge_with_detection_only_keeps_detect...` keeps
  the capability gate.

Real-bridge cases added: Apply by keystrokes (Body 24px, ordinary 16px, markup untouched) and Clear restoring markup and every computed style;
replace/repeat Apply and repeated Clear; raw empty `roles: []`; post-commit rerender (stale status, then an inspector edit and Clear settle);
inspector edit surviving Apply and Clear with a counted mismatch whose reason text derives from the receipt; author `.card p` winner shown as
text; Detect after Apply reads the 16px baseline; target-only reset keeps the preview; reset-all dismissed (no untargeted reset), accepted
(exactly one, preview and edit cleared, no banner, Apply works again); CSP `stylesheet-blocked` (a policy meta added after the first Apply,
then Detect, then Apply) keeps the previous preview and the page; initial 2,001-character route (Apply disabled with the reason, Clear works
with a null-URL receipt); valid route becoming unsupported after the commit; re-hello after another client replaced the roles; fullscreen
regression with a populated preview (fluid and fixed 1440).

Revision confirmation against the real bridge: Apply, replace, repeat, Clear, repeated Clear gave receipts with revisions 1, 2, 3, 4, 5 and a raw
`roles: []` apply gave revision 6 with empty roles, CSS and outcomes. Each accepted op raises the revision by one, including a repeated clear and
`roles: []`.

Mutants (script `s2b-mut.py`, foreground, byte-exact restore verified): winning-selector grammar reinstated (killed by the real `.card p` test and the
fake-peer test), selector length limit removed (killed by the hostile table), `matched` shown as `checked` (killed), author-rule text without the
selector (killed by the real test), role panel moved into the composer shell (killed by the populated fullscreen test).

Gates (final tree, Chromium): `python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support`
-> `Ran 184 tests ... OK`; the second focused command -> `Ran 46 tests ... OK`; ruff on the two test files clean; `verify.py --static-only` no FAIL;
`git diff --cached --check` exit 0. Full halves, frontend gate and Firefox canary not run (settled wave).

Notes: `open()` gained an `init` option (an init script on the Studio page; the integration tests use it to record bridge messages). The CSP case uses
a runtime `<meta>` policy because the bridge cannot be given a header after an accepted Apply; adding that element is a page change, so the test
takes a fresh Detect before the second Apply.

Handoff
- CHANGELOG line: "Studio can preview role fonts on a live page: draft values per detected role, Apply and Clear with matched and checked counts and a plain
  reason for each lost property (the winning author selector is shown as text), and a Reset all page edits control."
- Ledger draft: "R2.S2 landed: Studio role preview controls, queue kinds, receipts and reset-all; fake-peer and real-bridge coverage; winningSelector is
  bounded text; Json code tab revision +1 after a role op (brief addition 1); focused gates 184 + 46 OK."
- Commit body: "Studio previews role fonts without ever treating a request as state: drafts stay separate from detected baselines and accepted state,
  Apply and Clear travel the existing revision queue and settle only from their own validated receipts, and a preview never enters saved overrides,
  exports or sync. Outcomes show matched and checked counts and the plain reason each property lost, with the winning author selector shown as text.
  Reset all page edits is the one explicit untargeted reset and clears the preview from the bridge's empty role state."

## Phase 2 fix round 1
Patch: `task-s2b-code-r1.patch`, full diff against 4d3b0bb, sha256 `4acf99eb3d6727046c95be6f8ce355ef34f4c35d8ae2c159ca264582ea48176c`
(`git apply --check -R` passes, `git diff --cached --check` clean). Mutants from `s2b-r1-mut.py`, foreground, byte-exact restore asserted; `fontkit-bridge.js` unchanged in the patch.
1. C1 controls and separators: three hostile rows (U+0085, U+2028, U+2029). RED first: the rows were accepted (hostile test errored at "loss selector with a C1 control" and the next rows).
   Fix: `roleLossSelector` also rejects U+007F-U+009F, U+2028, U+2029. GREEN. Mutant (class narrowed back to U+007F) KILLED.
2. `test_role_css_never_reaches_the_code_tabs_downloads_exports_or_the_synced_file` (real bridge, Sync route): CSS/HTML/Json tabs, each tab's Download, the JSON export
   and the Sync body are byte-identical before and after a real Apply apart from the Json tab revision (+1); none contains `font-size: 24px`, the receipt's digest or the role
   selector. `exports()` and `sync_body()` moved to the shared base class. Characterization GREEN; mutant (preview CSS appended to the code tab) KILLED.
3. The replace/repeat test now asserts the target's computed size after each Apply (24, 25, 25) with the ordinary paragraph at 16px, and 16px after each Clear.
   Characterization GREEN; mutant (bridge `installRoleSheet` rewrites 25px to 24px on the install path) KILLED.
Gates (Chromium): first focused command `Ran 185 tests ... OK`; second `Ran 46 tests ... OK`; ruff clean.

## Controller integration (2026-10-16)

The final patch (`task-s2b-code-r1.patch`, sha256 `4acf99eb...`, phases 1 and 2
against `4d3b0bb`) applies with `git apply --3way` and no conflict. Each staged
blob equals the code-phase worktree's index; `fontkit-bridge.js` is unchanged.

- `test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support`
  (Chromium): Ran 185 tests in 248.703 s, OK.
- `test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests`
  `test_studio_visual.LiveAppViewTests` (Chromium): Ran 184 tests in 262.416 s, OK.
- The frontend gate, the full Chromium halves and the advisory Firefox canary run
  at the settled wave.
- Fast gates: static checks, `node --check` and product-tree Ruff pass, and
  `git diff --check` is clean on both the working tree and the index. Exact
  Ruff reports only the four preserved findings in the owner's untracked
  `.agents/`.
