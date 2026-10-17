# R2.W2PT brief: the contract table states Addendum 23's bindings and placement

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 23 (D074), tasks R2.W2P and R2.W2PS (this is their shared table slice);
the binding contract's `SelectorBinding` type and "Selector and value validation". PR B2 wave W2, phase 2, beside R2.W2B1,
R2.W2B2 phase 2 and R2.W2S-b. BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with `task-w2t-code.patch` (R2.W2T) applied
first in the worktree (PATCH_DEP; the controller names its SHA-256). Worktree `a scratch worktree`, task id `w2pt`. Line budget:
about 120 gross lines; explain any excess.

This slice lands in ONE commit with R2.W2P, R2.W2PS and R2.W2PI: until both sides accept `body`, the new template cases
fail on both. Your own focused run is therefore expected to show those template cases RED against the BASE bridge and
Studio; record which, and why. Everything else stays green.

## Why

Addendum 23 adds the binding reason `page`, makes `body` valid only as the one selector of a `bootstrap5-body` role, lets a
mono group bind `code`, `kbd`, `pre` and `samp`, and allows at most one body and one mono role per request. The table
(`tests/role_contract.py`) is the shared oracle both sides' tests read (R2.C0); it must state these first, so R2.W2P (bridge)
and R2.W2PS (Studio) build on one source.

## Owned files (exact)

- `tests/role_contract.py`: `BINDING_REASONS`, `STABLE_REASONS`, the template cases (about 236-250 at BASE: every
  `bootstrap5-body` role binds exactly `['body']`; keep the `mono` case on `['code']`), and the checker `violations()`
  (detected-group rules in the group part, placement rules in `roles_part()`, which covers receipts and role state).

Not owned: the table's self-test lives in `tests/test_studio_roles.py` `StudioContractTableTests` (2495-2581 at BASE:
its defect list, the "53 defects" docstring, and the `every_reason` row at 2641-2665 that puts every `BINDING_REASONS`
entry on one plain group). R2.W2S-b writes that file beside you, so R2.W2PS (phase 3, on your patch, same commit) adds
the rows. You hand them over: the Handoff section lists, verbatim and ready to paste, one valid case per new rule (a
detected Body group bound `body`/`page`, a mono group on the four page bindings, a receipt holding one body role on
`['body']`), one defect row per rule with its exact expected violation text, the `every_reason` split (a plain group
with the non-page reasons plus a body group bound `body`/`page`), and the new defect count.

Read-only: every other file. Running worktrees beside yours: `a scratch worktree`, `a scratch worktree`, `a scratch worktree`. Never touch
them.

## Read first

`constraints.md` (all of it); Addenda 17, 22 and 23; D069, D074; `tests/role_contract.py` with R2.W2T's patch applied (all of
it); the plan's `SelectorBinding` and "Selector and value validation".

## Requirements

1. `BINDING_REASONS` gains `'page'`; `STABLE_REASONS` gains it (a page binding is stable).
2. The checker refuses (exactly one violation each; the page rule is checked first, and a group that fails it is not
   checked again by the body rule, so a plain group bound `body`/`page` is one violation; the body-binding exactness is
   one `need`): a detected group with a `page` binding whose adapter is neither
   `bootstrap5-body` nor `bootstrap5-mono`; a `bootstrap5-body` group whose bindings are not exactly
   `[{'value': 'body', 'stable': True, 'reason': 'page'}]`; a `bootstrap5-mono` page binding other than the four values
   `code`, `kbd`, `pre`, `samp` (in that order); a request or role state with two `bootstrap5-body` or two
   `bootstrap5-mono` roles, or a `bootstrap5-body` role whose selectors are not exactly `['body']`; and `body` as a selector
   of any other role or group binding (selector checks are exempt: a known role whose sole selector is `body` is valid); a
   mono group with any `page` binding that does not have exactly the four; a `page` binding on a group whose
   `bindingComplete` is false; and two `bootstrap5-body` or two `bootstrap5-mono` groups in one Detect reply.
3. The template cases bind every `bootstrap5-body` role to `['body']`, and their recorded CSS and digests are recomputed
   from the contract's template text (Addendum 17 item 1), never from a side's output: write the expected CSS by hand from
   the rule, then hash it with the table's `fnv1a32`.
4. The table header names Addendum 23 beside the addenda it already cites.

## Tests and mutants

Prove the checker with a scratch harness (named `w2pt-*` in the scratchpad, not committed) that runs every handed-over
valid case (no violation) and defect row (exactly its one violation). Mutants (each restored byte-exact, SHA-256 before
and after): `page` dropped from `STABLE_REASONS`; the count rule removed; the `['body']` rule removed; the page-first
precedence removed; record which harness rows fail (each must fail at least one). `fnv1a32`'s own oracle is the
published vectors in `FnvVectorTests`. Expected values come from Addendum 23's text and literals. A
failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_role_protocol.RoleContractTableTests test_studio_roles.StudioContractTableTests test_support`.
Then run `test_role_adapters.ApplyTests test_studio_roles.StudioAdapterTests` once on the PATCH_DEP state (baseline)
and once with your patch. List every test that newly fails, with its failure line and owner (a bridge test -> R2.W2P, a
Studio test -> R2.W2PS; both land in this commit). The table-internal template check (`test_studio_roles.py` 2459) must
be green. Any other new failure is a defect: stop and report it. Also `python -m ruff check tests/role_contract.py` and after
staging by name `git diff --cached --check`.

## Report and handoff

Report: each requirement with its oracle; each mutant (command, failing rows, SHA-256 before and after); the focused run
with every failure classified; gross lines. Patch `task-w2pt-code.patch` holds only your changes on top of the PATCH_DEP
(stage it first with `git apply --index`, write the patch with `git diff --binary`, check with `git apply --check -R`),
with the PATCH_DEP SHA-256. No commit subject: it lands inside R2.W2P's commit; draft one sentence for that commit's body.
