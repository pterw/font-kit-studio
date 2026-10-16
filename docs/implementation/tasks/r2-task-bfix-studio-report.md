# PR B review fixes, Studio side (worktree C:/fks/ts3, BASE 2ba1e77)

Patch: `task-prb-studio-code.patch`, full diff against 2ba1e77. Files: `fontkit-studio.html`, `tests/test_studio_roles.py`, `tests/test_r2_integration.py`.
No bridge file touched. Gates (Chromium): first focused command `Ran 195 tests ... OK`; second `Ran 46 tests ... OK`; ruff clean; `verify.py --static-only` no FAIL;
`git diff --cached --check` clean. Mutants from `ts3-mut.py` (foreground, byte-exact restore asserted). No bridge mutant was needed.

| Item | Change | RED | Mutant |
|---|---|---|---|
| 1 F1/CR1 | `validRoleRejection` accepts a text detail, or for `revision-conflict` exactly `{baseRevision, revision}` (non-negative integers); the op settles, `data.revision` is adopted, the detail shows as text ("Detail: base revision 0, bridge revision 1") | real-bridge `test_a_revision_conflict_from_the_real_bridge_settles_at_once_and_the_next_apply_succeeds` (a raw clear from Studio's session moves the bridge revision, then Apply) ERRORED before the fix (8 s hang), passes after and the next Apply carries baseRevision 1 and renders 24px; fake-peer object-detail test also RED | object detail rejected again: killed (both) |
| 2 F2/F4/CR2/CR3 | `matched` uncapped, `checked`/`mismatched` <= 10,000, losses <= 96 | fake `test_outcome_limits_follow_what_the_bridge_can_send` and real `...more_than_sixty_four_loss_groups...` ERRORED before (receipt dropped, 8 s hang); `...ten_thousand_elements...` passes after | cap matched at 10,000: killed; losses 96 -> 64: killed |
| 3 F5/CR6 | `ROLE_FAMILY_UNSAFE` copied from the bridge (controls, DEL, `var( env( attr( url( expression(` with spaces, `! important`); help text updated | real `test_studios_family_field_agrees_with_the_bridge_on_every_row` (25 rows, Studio gate vs the bridge's verdict) FAILED on var/env/attr/tab rows | `(url|expression)` only: killed |
| 4 CR5 | composition coalescing stops at an untargeted reset, a restore or a role op | hybrid `test_a_composition_edit_is_not_merged_into_one_queued_before_a_reset_all` ERRORED before (merged, sent before the reset) | barrier removed: killed |
| 5 F6 | an invalid ready from another origin than the shown preview's clears it ("This bridge does not report a role preview, so none is shown."); same origin keeps the old CSS marked unconfirmed (phase 1 rule) | `test_another_apps_preview_is_cleared_when_a_bridge_that_cannot_report_one_connects` FAILED before | origin test off: killed |
| 6 F7 | `resetRoleSession` reports ROLE_DROPPED for a queued role op too | `test_a_role_op_that_never_left_the_queue_is_reported_dropped_when_the_session_ends` FAILED before | queued test removed: killed |
| 7 CR8 | outcome list re-rendered only when outcomes/roles change; the size probe is cached on a draft-version counter plus the state it reads; one `input` listener (checkbox and select fire it) | `test_typing_does_not_rebuild_the_outcome_list` FAILED before; existing tests prove behaviour | rebuild every render: killed |
| 8 CR10 | `validRoleRejection` is the one shape check for `rejectRoleDetect` and `rejectRoleOp` (uses `ROLE_REJECTIONS`) | covered by items 1 and the malformed-rejection table (extended with object-detail shapes, all still ignored) | n/a |

Notes
- Real-bridge 10,001 matched: the bridge only binds a role to what it measured, so no real Detect reaches more than 10,000 elements. The test page
  answers the first Detect itself with a `.b` class binding that 10,001 elements carry (the real bridge's reply then arrives for a settled request),
  and the real bridge answers Apply: receipt matched 10,001, checked 1, accepted and shown. A fake-peer case covers matched 250,000.
- Item 5 keeps the phase 1 rule for a same-origin invalid ready (preview kept, marked unconfirmed); only a different origin clears. Say if you want it cleared in both cases.
- CHANGELOG (users notice): "Role preview no longer gets stuck after a revision conflict or a receipt with many lost properties, refuses font stacks the bridge would reject,
  and no longer shows another app's preview after switching targets."
e616db0a63b32b13058997f0cf38fdd6c874ff2111546ec7f07a4c626d974a48

## Controller integration (2026-10-16)

The final patch (`task-prb-studio-code.patch`, sha256 `e616db0a...`) applies onto
`5b1fe46` (the bridge fixes) with no conflict; each staged blob equals the code-phase
worktree's index. A same-origin invalid ready keeps the earlier preview marked
unconfirmed, as phase 1 approved; only a ready from another origin clears it.
- `test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls`
  `test_support` (Chromium, with the fixed bridge): Ran 195 tests in 268.323 s, OK.
- `test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests`
  `test_studio_visual.LiveAppViewTests test_live_integration` (Chromium): Ran 236 tests in
  374.983 s, OK.
- Fast gates: static checks, `node --check` and product-tree Ruff pass, and
  `git diff --check` is clean. Exact Ruff reports only the four preserved findings
  in the owner's untracked `.agents/`.
