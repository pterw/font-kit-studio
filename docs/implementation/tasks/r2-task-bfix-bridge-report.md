# PR B review fixes, bridge side (MODE code, BASE 2ba1e77, worktree C:/fks/t26)

Patch: `task-prb-bridge-code.patch` (full diff against 2ba1e77), sha256
`3040b2cc6639d06e41acf3cfddb93436c1a06e3ee4bba7a0fa2f20ce4ef515b4`.
Files: `fontkit-bridge.js` (+48/-17), `tests/test_role_stylesheet.py` (+89), `tests/test_role_detection.py` (+27),
`tests/test_role_preview.py` (+3, one table row). Studio files untouched.

Gates: `python -m unittest test_role_stylesheet test_role_preview test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests test_support -v`
(Chromium, FKS_REQUIRE_FIXTURES=1) -> `Ran 123 tests ... OK`. node --check, verify --static-only (provenance PASS, browser SKIP),
ruff --exclude .agents, git diff --check (plain and cached), pre-commit all pass.
D058 Apply-then-Detect on the 5,000-parent page: elapsedMs 833, complete, 5,000 scanned (BASE-era runs: 611-833 ms; limit 2,000 unchanged).

## Items
1. F3 transitions. While the owned sheet is suspended for the baseline read, a bridge-owned style
   `*, *::before, *::after { transition: none !important; }` (added to `roleOwned`, so it is not an author mutation and is
   not in the style stamp) is installed. DEVIATION from the brief: it bans transitions only, not animations, because removing
   an animation restarts it on restore. A per-slice flush on restore (getBoundingClientRect after re-enabling) made the 5,000-parent
   scan finish only 58 elements in 2 s, so the ban stays for the whole scan and `releaseRoleQuiet` runs once: it flushes the
   preview back in under the ban (no replayed transition) and removes the node. It is called from `finish`, `cancelRoleJobs`
   and `dispose`, so no exit leaves it behind.
   Test `TransitionBaselineTests.test_detect_with_a_live_preview_reads_the_baseline_on_a_page_with_transitions` (p transitions
   font-size; apply 30px; Detect).
   RED at BASE: `Lists differ: [30] != [16]`. Mutants: ban not installed (fails); release without flush (fails, a transition is left running).
   Limitation (corrected in fix round 1): Chromium does not cancel transitions that are already running (no transitioncancel);
   the ban only suppresses transitions that would start during a Detect.
2. F4 selectors. `named()` returns null for C0, DEL, C1, U+2028 and U+2029, so such a winner is `{null, complex-cascade}`.
   Table row `a winning selector with a C1 control character is never named` (`p.a\85`). RED at BASE: author-rule with the selector.
   Mutant: control-character filter removed (fails).
3. CR7. `applyWireframeMovement` settles the bridge's own writes before dispatching `design:order-changed`, and counts whatever
   the listeners wrote right after (`noteRoleMutations(takeRecords())`), so a later settle cannot drop them.
   Test `test_writes_made_by_an_order_changed_listener_advance_the_page_version` (also pins that the bridge's own reordering
   leaves the version alone). RED at BASE: the apply with the old version is accepted. Mutants: listener writes not counted
   (fails); own writes not settled before dispatch (fails, the reorder itself would count).
4. CR9. `postRoleReceipt(..., refreshed = false)`: the two call sites right after `roleJobFresh` pass `true`, so the stylesheets
   are not serialized again. No behaviour change; the existing receipt tests pass.
5. CR10. One module-level `ROLE_LOSS_REASONS` and `compareRoleLosses` serve `measureRoleOutcomes` (capped groups, final sort)
   and `fitRoleReceipt`. Mutant: reasons reordered (the grouping/order test fails).
6. D066 / Addendum 14 (released). `document.fonts.status` is out of `roleStyleStamp`; `observeRolePage` listens to
   `loading`, `loadingdone` and `loadingerror` on `document.fonts` and moves `roleNative` (the internal epoch) when active with a session.
   Tests (SplitPageVersionTests): `test_an_author_font_loading_after_a_commit_does_not_advance_the_wire_page_version`
   (an author @font-face behind a held route, released with a placeholder body; second apply and clear with the receipt's version
   are accepted) and `test_a_font_load_during_a_pending_scan_makes_it_page_changed_with_equal_versions` (a FontFace load
   part-way through a calibrated scan; hover-style timing with a premise message).
   RED at BASE: `1 != 0` (page version advanced) and `(True, None) != (False, 'page-changed')`.
   Mutants: fonts.status back in the stamp (commit test fails); font events not moving the epoch (scan test fails).
   No existing R2.T1 or R2.3 assertion needed changing: all pass unchanged.

RED log: scratchpad `red-t26.log` (5 failing tests at BASE). Mutant script `mutate-t26.py`; each mutant restored byte-exact with sha256 verified (all 8 killed).

## Fix round 1
Patch: `task-prb-bridge-code-r1.patch` (full diff against 2ba1e77), sha256 `aa4e7270a65558faf87155976962d12559c86f248309c051d9844027ba5c26b4`.
Focused gates: `Ran 126 tests ... OK`; Apply-then-Detect 765.5 ms; node --check, verify --static-only, ruff --exclude .agents,
git diff --check and pre-commit pass.

1. Exception safety. The detect `run` batch now has a `catch`: a page that throws inside the scan (test: `document.createTreeWalker`
   patched to throw) ends the job through `finish('page-changed')`, the existing reply shape, incomplete with reason `page-changed`
   (a throw means the page's evidence cannot be trusted; no new reason is invented). `finish` releases the ban first, so no exit
   leaves it behind. RED against the previous bridge: no reply (`KeyError: 'complete'` on the timed-out request).
   Mutant: catch removed -> fails.
2. Cancel path. Test `test_a_reset_during_a_scan_removes_the_transition_ban_at_once`: live preview on the large page, wait for the ban
   node mid-scan, send `design:reset`, assert no ban node. Mutant: `releaseRoleQuiet` removed from `cancelRoleJobs` -> fails.
3. Report corrected: Chromium does not cancel running transitions; the ban only suppresses transitions that would start during a Detect
   (see the limitation line in item 1 above).
4. Controller question: the ban is conditional. Final rule: it is installed only when the owned sheet is live and enabled
   (`this.roleSheet` exists, which holds at least one role rule; `suspendRoleSheet` returns before installing anything otherwise),
   and it spans the scan until `finish`, `cancelRoleJobs` or `dispose` releases it. Test
   `test_the_transition_ban_is_installed_only_while_a_preview_is_live` (a MutationObserver counts inserted ban nodes: 0 for a Detect
   with no preview; 1, and none left over, after a Detect with a preview). Mutant: ban installed with no preview -> fails.
Mutants restored byte-exact (sha256 verified), script `mutate-t26r1.py`; RED log `red-t26r1.log`.

## Controller integration (2026-10-16)

The final patch (`task-prb-bridge-code-r1.patch`, sha256 `aa4e7270...`) applies
onto `2ba1e77` with no conflict; each staged blob equals the code-phase worktree's
index. At landing the controller added a `console.warn` to the new detect-batch
`catch`, as the scoped re-review asked, matching the bridge's other catches.

- `test_role_stylesheet test_role_preview test_role_protocol test_role_detection test_support`
  (Chromium): Ran 124 tests in 160.702 s, OK.
- `test_bridge_runtime test_live_integration test_r2_integration` (Chromium, Studio at`
  `2ba1e77` against the fixed bridge): Ran 199 tests in 254.249 s, OK.
- Fast gates: static checks, `node --check` and product-tree Ruff pass, and
  `git diff --check` is clean. Exact Ruff reports only the four preserved findings
  in the owner's untracked `.agents/`.
