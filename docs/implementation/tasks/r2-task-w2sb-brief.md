# R2.W2S-b brief: Studio refuses the same families as the bridge

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 item 1, task R2.W2S (slice b of three); D072; the binding contract's
"Selector and value validation". PR B2 wave W2, phase 2, beside R2.W2B1 and R2.W2B2 phase 2 (disjoint files). BASE
`73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with two patches applied first in the worktree, in this order (PATCH_DEP; the
controller names their SHA-256): `task-w2t-code.patch` (R2.W2T: the table's `FAMILY_KEYWORDS`, `FAMILIES_REFUSED`,
`FAMILIES_ACCEPTED`) and `task-w2sa-code.patch` (R2.W2S-a). Your code does not depend on W2S-a's hunks (3920-3930 share
no context with `roleFamily`), but both edit `fontkit-studio.html`, and one file has one writer at a time (AGENTS.md), so
you start on its patch and write a delta. The controller creates `a scratch worktree` and links the npm fixtures. Task id `w2sb`. Line
budget: about 100 gross lines; explain any excess.

## Why

Studio's `roleFamily` (`fontkit-studio.html` 3883-3892 at BASE) mirrors the bridge: blocklist (3882), balanced quotes, then
`CSS.supports`. It accepts the CSS-wide keywords and, in Chromium, unquoted parentheses (`--x(`), so Apply is offered for a
family the bridge refuses once R2.W2B1 lands. Studio's rule exists so that "Apply is never offered for a value the bridge
will reject" (its comment at 3881). The same function also checks role families arriving in receipts and ready snapshots
(3905), so a hostile reply with such a family must be refused as malformed. SIMPLIFY6's test half: the Python mirror of
the serializer (`tests/test_studio_roles.py` 53-55 at BASE, 47-49 after W2T's patch) writes the `:root` block in two
statements; it becomes one conditional shaped like the bridge's `roleCssBlocks` (`fontkit-bridge.js` 292-295: a body or
mono role with a family writes its `:root` block, then its plain block), byte-identical output.

## Owned files (exact)

- `fontkit-studio.html`: `roleFamily` and the comments above it (3880-3892 at BASE), and `ROLE_FIELD_HELP.fontFamily`
  (3847), whose help text must name the new refusals (CSS-wide keywords; parentheses only inside quotes). Nothing else.
  (`README.md` near 572 states the family rule too: the controller updates it at landing.)
- `tests/test_studio_roles.py`: the field-validation test that holds the Font family rows (the `bounds` list near 752-764
  at BASE; R2.W2T's patch may move it), one row in the existing hostile receipt or ready table for a refused family, and
  the serializer mirror at 53-55 (SIMPLIFY6). Nothing in `StudioContractTableTests` (R2.W2T's).

Read-only: `fontkit-bridge.js`, `tests/role_contract.py`, `tests/test_r2_integration.py` (R2.W2S-c's), every other file.
Running worktrees beside yours: `a scratch worktree` (R2.W2B1) and `a scratch worktree` (R2.W2B2 phase 2). Never touch them.

## Read first

`constraints.md` (all of it); Addendum 22, D072; at BASE `fontkit-studio.html` 3876-3930 and 4100-4175 (how a field that is
not valid blocks Apply and says so); `tests/test_studio_roles.py` 40-60, 700-790 and the hostile receipt tables;
`tests/role_contract.py` with R2.W2T's patch (the refused-family constants, the definition of "outside quotes", the engine
notes).

## Requirements

1. Studio's `roleFamily` refuses a trimmed value equal to a CSS-wide keyword in any case and a value with `(` or `)` outside
   quotes (the scan the table defines), exactly as the bridge will; every case in `FAMILIES_ACCEPTED` still passes. A
   refused family makes the row's field not valid with the existing wording (`<row>: font family not valid (...)`), and
   Apply stays disabled.
2. The field-validation test gains every `FAMILIES_REFUSED` case (not valid) and every `FAMILIES_ACCEPTED` case (valid),
   read from the table, not copied.
3. A receipt (or ready snapshot) whose role family is a refused case is refused like any malformed reply: one row each
   for a keyword (`inherit`) and a dashed function (`--x(`) in the existing hostile receipt table, using its harness. The
   row's roles, `css` and digest must agree (recompute them through `canonical_css` and `with_css`, with `with_css` FIRST
   in the dict merge so it does not overwrite the changed role): a row that keeps the old css is refused for the css
   mismatch (`validAcceptedRoles`, 3936) and passes with no feature. The brief review measured it: old-css rows PASS at
   BASE, recomputed rows FAIL at BASE (the true RED). Oracle: the table's refused cases.
4. The serializer mirror is one conditional shaped like the bridge's `roleCssBlocks`; its output is unchanged.
No boundary field changes: R2.W2T's table already carries the family rows.

## Tests and mutants

Each new or changed test method keeps or gains a Given/When/Then docstring whose Then is exactly what it asserts. Mutants
(each in the foreground in your worktree, restored byte-exact, SHA-256 before and after; PYTHONDONTWRITEBYTECODE=1):
Studio's keyword check removed (the field test fails on the keyword rows); Studio's parenthesis check removed (it fails on
the dashed rows in Chromium; Firefox already refuses `--x(` through `CSS.supports`); a quote-blind parenthesis check (only
the accepted near-miss rows kill it); the receipt path not calling `roleFamily` (3905; the requirement-3 rows fail); the
mirror dropping `'fontFamily' in` or its final LF (`test_template_cases_follow_the_addendum_rules_and_carry_their_own_digests`
fails). Report each row's state at BASE in Chromium: 15 of 19 refused cases RED (8 keywords, 7 dashed); `generic(kai)`,
`Inter)`, `a), serif`, `Inter (Display)` GREEN from the start (refused by `CSS.supports`); all accepted rows GREEN. Never use a
case the engine already refuses to kill a mutant. A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_r2_integration.StudioRoleBridgeTests.test_studios_family_field_agrees_with_the_bridge_on_every_row test_support`
(the parity test runs against the BASE bridge here: its existing rows must still agree). Also
`python scripts/verify.py --static-only`, `python -m ruff check` on changed Python files, and after staging by name
`git diff --cached --check`.

## Report and handoff

Report: each requirement with its RED and oracle; each mutant (command, failing tests and lines, SHA-256 before and after);
the focused run (Ran line, OK, GATE line); gross and material lines. Patch: `task-w2sb-code.patch` holds only your changes
on top of the two PATCH_DEPs (stage the PATCH_DEP state first with `git apply --index`, write the patch with
`git diff --binary`, `git add -N` any new file, check with `git apply --check -R`), with the PATCH_DEP SHA-256s it was built
on. Commit subject `fix(studio): refuse the same role families as the bridge`, a draft body (why, wrapped at 72, no process
narration) and the R2.W2S plan item.
