# R2.W2S-c brief: the real Studio and the real bridge agree on the refused families

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 item 1, task R2.W2S (slice c of three); D072. PR B2 wave W2, phase 3.
BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with five patches applied first in the worktree, in this order
(PATCH_DEP; the controller names their SHA-256 in the dispatch): `task-w2t-code.patch`, `task-w2sa-code.patch`,
`task-w2b2-code.patch` (R2.W2B2 phase 1), `task-w2b1-code.patch` (the bridge refuses the families) and
`task-w2sb-code.patch` (Studio refuses them). Worktree `a scratch worktree` (the controller creates it and links the npm fixtures), task id `w2sc`. Line budget: about 10
gross lines.

## Why

D072 requires both sides to refuse the same family values. The parity test
`test_studios_family_field_agrees_with_the_bridge_on_every_row` (`tests/test_r2_integration.py` at
BASE: `FAMILIES` at 233-237, the parity test at 499-521) runs the real Studio against the real bridge, but `FAMILIES` holds none of the new cases, so nothing proves the two
sides agree on them.

## Owned files (exact)

- `tests/test_r2_integration.py`: `FAMILIES` and one import line (`import role_contract as table`, if absent). Nothing
  else.

Read-only: every other file, `tests/role_contract.py` included.

## Read first

`constraints.md` (all of it); D072; `tests/test_r2_integration.py` 1-60, 225-240 and 495-560 with the PATCH_DEPs applied;
`tests/role_contract.py` (the refused-family constants and engine notes).

## Requirements

1. `FAMILIES` gains every `FAMILIES_REFUSED` case (`False`) and every `FAMILIES_ACCEPTED` case (`True`), read from the table,
   not copied, so the parity test proves both sides agree on each.
2. Its docstring's Then still says exactly what it asserts.

## Tests and mutants

Mutants (each in the foreground, restored byte-exact, SHA-256 before and after; PYTHONDONTWRITEBYTECODE=1), each side on
each rule: Studio's keyword check removed and the bridge's keyword check removed (each fails the 8 keyword rows); Studio's
parenthesis check removed and the bridge's (each fails the 7 dashed rows, Chromium only); and two over-refusal mutants
that only the accepted rows kill: the bridge's keyword rule without its end anchor (refuses `inherited`, `Inherit Sans`),
and a parenthesis scan that ignores quotes (refuses `"Inter (Display)"`). Record which rows each mutant fails. The brief
review measured, before your change, 15 rows RED on BASE Studio with the W2B1 bridge and 4 refused rows GREEN on both
sides (`generic(kai)`, `Inter)`, `a), serif`, `Inter (Display)`: they kill nothing). A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_r2_integration test_support`.
Also `python -m ruff check tests/test_r2_integration.py` and after staging by name `git diff --cached --check`.

## Report and handoff

Report: the requirement with its oracle; each mutant (command, failing rows, SHA-256 before and after); the focused run
(Ran line, OK, GATE line); gross lines. Patch: `task-w2sc-code.patch` holds only your changes on top of the five PATCH_DEPs
(stage them first with `git apply --index`, write the patch with `git diff --binary`, check with `git apply --check -R`),
with the PATCH_DEP SHA-256s. Commit subject `test: prove Studio and the bridge refuse the same families`, a draft body (why,
wrapped at 72) and the R2.W2S plan item (tick its box at this landing).
