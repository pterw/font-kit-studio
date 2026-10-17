# R2.W2PS code report (MODE code)

Patch `task-w2ps-code.patch` (delta on PATCH_DEP), sha256 `160e0f6fee4a92beb65d8de658deecaaa4e5fe72720a92d6f5d0125a077e4514`;
`git apply --check -R` passes; `git diff --check` clean; ruff clean on tests/test_studio_roles.py; `verify.py --static-only` PASS.
Files: `fontkit-studio.html` (+26/-8), `tests/test_studio_roles.py` (+198/-17); about 249 gross lines.
PATCH_DEP sha256 (checked, applied with `git apply --index` in order): w2t `2f1697fb...5cd`, w2sa `5d9db7f7...0d1`, w2sb `28d09c80...cf3a`,
w2pt-r1 `ad79281c86ad8015ef5c260fbe7224ba3bbf7b1905dba4d6ce88eeab65503ec7` (full: 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd,
5d9db7f7ab835a27fd6b6570077a7a3e667b9bb893ea923a5f10b680c5cd0fd1, 28d09c80fc5adf5dd6343a821468dc6b447e1a618634ee4d341c06d4d482cf3a).

## Validation sites touched (fontkit-studio.html)
- `validRoleSelector(value, bodyOk = false)`: `body` allowed only with `bodyOk` and exactly lowercase; the general root ban is unchanged.
- `validDetectedGroup`: reason enum gains `page`; bindings validated with `bodyOk` only for reason `page`; then Addendum 23 placement: a body group
  is exactly one `body`/page binding and complete; a mono group with any page binding is exactly code, kbd, pre, samp (in order) and complete;
  any other group has no page binding. New const `ROLE_PAGE_MONO`. `body` in any non-page binding stays refused by the root ban.
- `validDetectedReply`: selector checks use `validRoleSelector(check.selector, true)`; new per-reply rule, at most one body and one mono group.
- `validRoleInput`: a body role selects exactly `["body"]` (duplicates stay refused by the Set rule); other roles keep the root ban.
- `validAcceptedRoles`: at most one body and one mono role (receipts and ready snapshots both go through it).
- Receipt line: roles whose only selector is `body` end with the page-wide literal, never "no eligible text found".
- Not changed (by design): `buildRoleRequest` and the knownRoles builder (rows come only from the last validated reply),
  `acceptResetRoleState` (a reset-all reply must hold no roles; it calls `validAcceptedRoles` unchanged). Req 5: the Body row shows its binding and Adapter
  lines like any adapter row and Apply is enabled (proved by the new first test); no code was needed.

## Existing tests changed (rule that forced each)
All move to Addendum 23: a Bootstrap 5 body group binds exactly `body`/page and a body role selects `["body"]`.
- `StudioAdapterTests.body_row` (and its three tests `...body_case_receipt...`, `...unsupported_adapter_rejection...`, template tests): body group on PAGE_BODY.
- `test_each_adapter_renders...`: body row is an enabled page row (binding line `body — stable (page)`, no "Safe complete bindings unavailable.").
- `test_apply_sends_each_selected_groups_adapter...`: body group on PAGE_BODY, request selectors `['body']`.
- `test_a_groups_adapter_changed...`: first group is the page-bound body group (a body group on `.body-copy` is now malformed); second stays a heading.
- `test_ready_with_accepted_roles_...` (`gone` role): body role on `['body']`.
- `StudioContractTableTests`: self-test rows from W2PT's handoff pasted (+ the 3 additions from its follow-up; 74 defects, 5 valid_page rows, docstring);
  `every_reason` split into a plain group of the non-page reasons plus the page-bound body group (limits test docstring updated).
- `hostile_receipts`: 4 new rows (two body roles, two mono roles, body on a class, body on body twice).

## Baseline / after (test_studio_roles, 88 tests at BASE+deps)
- Before my change (PATCH_DEP only): Ran 88, FAILED (failures=3, errors=5), exactly the 8 W2PT listed (3 template ready snapshots, unsupported rejection, apply_sends, body_case receipt, every_reason binding reason and stable flag).
- After the HTML change alone: failures=3 errors=5, a different set: adds `each_adapter`, `adapter_changed`, `ready_with_accepted_roles` (the brief's), and the 3 template ready snapshots turn green.
- Final: `gate.sh focused test_studio_roles test_support`: Ran 127, OK, `GATE focused EXIT 0 IN 154s`.

## New tests, RED and mutants (HTML SHA-256 before and after every mutant: e3e59cbec86340bd9aa4c4fcf6de28e2c4cf1a6936149fc5df4cec9ee3f26805, identical)
Four new Studio tests and the self-test rows. RED on the PATCH_DEP HTML (no Studio change): page-bound body + mono, selector check on body, receipt line,
ready snapshot placement all ERROR (Ran 4, errors=4). The hostile Detect table passes at BASE too (the reply is refused for another reason); its rows are proved by mutants.
- page reason refused again: page-bound body, selector check, receipt line fail (3 errors).
- body exactness removed: hostile rows `body group on .btn`, `...with body and a class`, `...on the mono bindings`, `incomplete page binding` fail.
- receipt wording reverted: receipt line fails at checked=0 and checked=3.
- selector-check exception removed: selector check test fails.
- one body or mono group rule removed: `two body groups`, `two mono groups` fail.
- one body or mono role rule removed: snapshot `two body roles`, `two mono roles` fail.
- body role may select anything valid: snapshot and hostile-receipt `body role on a class` fail.
- body compared case-insensitively: SURVIVES alone, since the exactness rule (`pages[0] === "body"`) refuses `BODY` too; two independent guards, reported not hidden.
- page binding need not be complete: `incomplete page binding` fails. Mono order not checked: `mono page bindings in another order` fails.
Hostile-receipt rows were also exercised through the role-rule mutants (`two body roles` etc. in test_every_hostile_receipt).

## Handoff
Commit body paragraph: "Studio accepts the page bindings the table now states: a body group is exactly body (page), a mono group is its own binding or code, kbd, pre, samp (page), `body` is valid as a body role's one selector and in a selector check, and a reply or receipt holds at most one body and one mono group or role. A body role's receipt line says it applies page-wide through Bootstrap's body variables and inherited text is not measured."
CHANGELOG sentence: "A Bootstrap 5 Body role now shows, in the receipt, that it applies page-wide through Bootstrap's body variables and that inherited text is not measured, instead of 'no eligible text found for this role on this page'."
Scratch (git-ignored) in `a scratch worktree/work/` (`w2ps-*`).

## Follow-up 1

Mode code, worktree a scratch worktree; layout kept (4 deps staged, delta unstaged). New whole delta (working tree vs index): `task-w2ps-code-r1.patch` (2 files: fontkit-studio.html, tests/test_studio_roles.py; +230/-25 gross in the tests+html). `task-w2ps-code.patch` untouched.

Changes
- Important 1: the each_adapter test now makes the heading group `binding_complete=False` and expects `Adapter: Bootstrap 5 heading rule`, then `Safe complete bindings unavailable.`, then the shared classes. Docstring updated.
- Important 2a: Detect row `body group on a page binding that is not body` (`{**PAGE_BODY[0], 'value': 'code'}`). 2b: `['BODY']` rows `body role on BODY` in the ready-snapshot table and in `hostile_receipts`; docstrings name them.
- Minor 1 folded: Detect rows `mono group on the four page bindings, not complete` and `body page binding that is not stable`.
- Minor 3 folded: `ROLE_PAGE_MONO` moved above the Addendum 17 comment so `ROLE_ADAPTER_VARIABLES` has its comment again (html wording/position only). The shared two-adapter constant: left (two copies, one for groups and one for roles; out of scope for a follow-up).
- Minor 2 left: the two receipt rows are in the brief (it asked for both tables); they are documentation, the snapshot rows carry the count rule. Minor 4 left: not required by the brief, the `remaining` map already refuses it.

Evidence (focused runs, `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_roles -k <test>`, foreground, Studio file SHA-256 `56dd0108...ba7` before and after, "restored ok"; log scratchpad `w2ps-r1-mut2.log`, `w2ps-r1-mut3.log`). Baseline (no change) -> OK. Mutants, each FAILED on the new row:
- delete the "Safe complete bindings unavailable." line (html 4057) -> each_adapter FAIL.
- swap it with the Adapter line -> each_adapter FAIL.
- remove `pages[0] === "body"` -> hostile page binding, subtest `body group on a page binding that is not body`.
- remove `group.bindingComplete` from the mono branch -> subtest `mono group on the four page bindings, not complete`.
- page exempt from the stable rule -> subtest `body page binding that is not stable`.
- `role.selectors[0].toLowerCase() === "body"` -> ready-snapshot subtest `body role on BODY` and hostile receipt subtest `body role on BODY`.
(Note: the first mutant attempt of this round ran with the wrong module path and failed on import; discarded, redone with the gate's environment above. The failing hostile rows report as ERROR, a wait timeout inside the subtest, because the hostile reply rendered a row.)

Gates: `gate.sh focused test_studio_roles test_support` -> 127 tests OK (144 s); `verify.py --static-only` PASS; `ruff check` tests/test_studio_roles.py clean; `git diff --check` clean; `git apply --check -R` on the new patch passes.

Handoff: no change to the commit subject or log text beyond: the each_adapter test keeps the incomplete-binding line; hostile Detect table now has 17 rows; `BODY` role rows added to both role tables.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
