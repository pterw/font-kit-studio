# R2.W2PS brief: Studio accepts the page bindings, checks placement and says Body is page-wide

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 23 items 4 and 5 (Studio side), task R2.W2PS; D074. PR B2 wave W2,
phase 3, beside R2.W2P (bridge) and R2.W2S-c. BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with these patches applied
first in the worktree, in this order (PATCH_DEP; the controller names their SHA-256): `task-w2t-code.patch`,
`task-w2sa-code.patch`, `task-w2sb-code.patch`, `task-w2pt-code-r1.patch` (the table's `page` reason, placement rules and
`['body']` template cases). Worktree `a scratch worktree`, task id `w2ps`. Line budget: about 300 gross lines; explain any excess.

Lands in ONE commit with R2.W2PT, R2.W2P and R2.W2PI. The BASE bridge never sends a `page` binding, so your tests drive
Studio with the harness's fake bridge replies (`tests/test_studio_roles.py`); the real-Studio, real-bridge proof is
R2.W2PI's.

## Why

Studio validates detected bindings (`validDetectedGroup`, `fontkit-studio.html` 3811-3834 at BASE: the reason enum at
3833, `validRoleSelector` at 3832) and selector checks (4255) with `validRoleSelector` (3779-3784), which refuses `body`
(3781-3782). A reply that fails is dropped silently (`acceptDetectedRoles` 4263-4267). So a bridge that binds Body to
`body` would leave Studio on "Detecting text styles..." for good. Studio must accept exactly what Addendum 23 allows and
refuse the rest, and its receipt line for a role bound to `body` (4203-4205: "no eligible text found") misreads a page-wide
role.

## Owned files (exact)

- `fontkit-studio.html`: `validDetectedGroup` and its binding check, `validDetectedReply` (its selector-check validation
  at 4255 and a new per-reply rule), `validRoleInput` (3912-3917) and `validAcceptedRoles` (3936), where receipts and ready
  snapshots are checked, and the receipt line at 4203-4205. Not `validRoleSelector`'s general root ban. No change is
  needed in `buildRoleRequest` or the knownRoles builder (rows come only from the last validated reply), nor in
  `acceptResetRoleState` (a reset-all reply must hold no roles); say so in the report. Name every site you touch.
- `tests/test_studio_roles.py`, including `StudioContractTableTests`: paste R2.W2PT's handed-over self-test rows (valid
  cases, defect rows, the `every_reason` split, the new defect count; see `task-w2pt-code-report.md` Handoff) and make
  them pass; plus the Studio tests R2.W2PT's report lists as newly failing (owner R2.W2PS).

Read-only: `fontkit-bridge.js`, `tests/role_contract.py`, `tests/test_r2_integration.py`. Running worktrees beside yours:
`a scratch worktree` (R2.W2P: bridge and bridge tests) and `a scratch worktree` (R2.W2S-c). Never touch them.

## Read first

`constraints.md` (all of it); Addendum 23, D074; `fontkit-studio.html` with the PATCH_DEPs: 3770-3840, 4195-4270 and the
Apply request builder; `tests/test_studio_roles.py` 2270-2370 (the adapter rows and lines) and its hostile Detect tables;
`tests/role_contract.py` with the PATCH_DEPs.

## Requirements

1. A detected group may carry `page` bindings only as Addendum 23 says: a `bootstrap5-body` group exactly
   `[{value: 'body', stable: true, reason: 'page'}]` (and every `bootstrap5-body` group must), a `bootstrap5-mono` group
   either its own complete binding or exactly `code`, `kbd`, `pre`, `samp` with `page`; `page` is stable; any other use
   makes the reply malformed (dropped like any other). A `page` binding requires `bindingComplete` true. `body` is valid
   nowhere else; a selector check (4255) for a known role whose sole selector is `body` is valid. Exact lowercase `body`
   only (`BODY` is refused). Studio keeps refusing duplicate selectors in a role (`validRoleInput`, 3915): canonical
   receipts and role state carry exactly `["body"]`, as R2.W2PT's table requires (`role_contract.py` 210-216 with W2PT's patch). (Only the
   bridge de-duplicates, a raw request; Studio never sends duplicates.)
   A Detect reply holding two `bootstrap5-body` or two `bootstrap5-mono` groups is malformed (the table's rule,
   `role_contract.py` 267-268 with W2PT's patch).
2. (Dropped: rows come only from the last validated reply, so Studio cannot build two body or mono roles; requirement 1's
   per-reply rule covers it.)
3. For a role whose only selector is `body`, the receipt line ends with exactly
   `; applies page-wide through Bootstrap's body variables, and inherited text is not measured` (whatever its checked count), and
   never with "; no eligible text found for this role on this page". Other roles' lines are unchanged. The literal is
   the oracle; R2.W2PI quotes the same text.
4. Studio's receipt, ready-snapshot and reset-all validators accept a `bootstrap5-body` role on exactly `['body']` and
   refuse, as malformed, a receipt or snapshot holding two `bootstrap5-body` or two `bootstrap5-mono` roles or a body role
   off `['body']` (the table's `roles_part()` rule).
5. The Body row shows its binding and adapter line like any adapter row, and Apply is enabled for it (at BASE a body group
   without a complete binding shows "Safe complete bindings unavailable.").

## Tests (each with a Given/When/Then docstring whose Then is exactly what it asserts, and one recorded mutant)

- A Detect reply with the page-bound Body group and the mono fallback is accepted: the rows render and Apply sends
  `selectors: ['body']` with `adapter: 'bootstrap5-body'` (RED at BASE: dropped, status stays "Detecting text styles...").
- Hostile Detect rows, one each, using the existing harness: `page` on a plain group; `page` on a heading group; a body
  group bound to `.btn`; a body group with `body` plus another binding; `BODY`; `body` in a plain group's bindings; a page
  binding with `bindingComplete` false; mono page bindings in another order; a mono group with three of the four; a mono
  group with the four plus a class binding; two body groups; two mono groups.
- A selector check on `body` for a known role is accepted (RED at BASE: the reply is dropped). Mutant: the 4255
  exception removed.
- Requirement 4's refusals, in the existing hostile receipt and ready-snapshot tables: two body roles, two mono roles, a
  body role on `[".btn"]`, a body role on `["body", "body"]`; and a receipt with one body role on `["body"]` accepted.
- The receipt line for a `body` role, asserted as rendered text; another role's line unchanged.
- Existing tests this change breaks: run ALL of `test_studio_roles` before and after, and list each new failure. The
  brief review found `body_row` and the three tests built on it; `test_each_adapter_renders...` (its body row expects
  "Safe complete bindings unavailable.", which a page-bound body group can no longer show: it becomes an enabled row);
  `test_a_groups_adapter_changed...` (an author-role body group, now plain under Addendum 23); and
  `test_ready_with_accepted_roles_shows_them...` (1779 at BASE: a `bootstrap5-body` role on `.body-copy`), plus the 6
  Studio tests R2.W2PT's report lists. Move each to the new rule and name the rule that forced it.
Mutants (each restored byte-exact, SHA-256 before and after): the `page` reason refused again; the body exactness rule
removed; the receipt wording reverted. A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_support`.
Also `python scripts/verify.py --static-only`, `python -m ruff check` on changed Python files, and after staging by name
`git diff --cached --check`.

## Report and handoff

Report: each requirement with its RED and oracle; each mutant; every existing test changed and why; every validation site
found; the focused run (Ran line, OK, GATE line); gross and material lines. Patch `task-w2ps-code.patch` holds only your
changes on top of the PATCH_DEPs (stage them first with `git apply --index` in order, write with `git diff --binary`, check
with `git apply --check -R`), with the PATCH_DEP SHA-256s. It shares R2.W2P's commit; draft its body paragraph and a
CHANGELOG sentence for the receipt line.
