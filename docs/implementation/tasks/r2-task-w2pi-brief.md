# R2.W2PI brief: the real Studio applies the Body row on a real-sized Bootstrap 5 page

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 23, task R2.W2PI; D074. PR B2 wave W2, phase 4. BASE
`73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with every W2 patch applied first in the worktree, in this order (PATCH_DEP; the
controller names their SHA-256): `task-w2t-code.patch`, `task-w2sa-code.patch`, `task-w2b2-code-p2.patch`,
`task-w2b1-code.patch`, `task-w2sb-code.patch`, `task-w2sc-code.patch`, `task-w2pt-code-r1.patch`, `task-w2p-code.patch`,
`task-w2ps-code.patch`. Worktree `a scratch worktree`, task id `w2pi`. Line budget: about 90 gross lines.

Lands in ONE commit with R2.W2PT, R2.W2P and R2.W2PS. Dispatch only when the W2S-b, W2S-c, W2P and W2PS patches exist and
are Approved.

## Why

AGENTS.md requires at least one test per boundary that runs the real Studio against the real bridge. Addendum 23's Body
binding crosses that boundary twice (Detect's `page` binding, Apply's `['body']` request), and the existing Bootstrap 5
integration test (`tests/test_r2_integration.py` near 735-770 at BASE) binds Body to the fixture's ids, which hides the case
the change exists for: a page whose body text has no ids and no shared class.

## Owned files (exact)

- `tests/test_r2_integration.py`: one new test beside the Bootstrap 5 integration test, and that test itself only where
  Addendum 23 changes what it asserts (name each change and the rule that forced it).

Read-only: every other file.

## Read first

`constraints.md` (all of it); Addendum 23, D074; `tests/test_r2_integration.py` with the PATCH_DEPs applied (1-80, the
Bootstrap 5 test and its helpers); the fixture `fixtures/bootstrap5-static/index.html`.

## Requirements

1. On the Bootstrap 5 fixture with more than 32 added unclassed body-style paragraphs and list items without ids, the real
   Studio detects the Body row with its adapter line and an enabled Apply; applying a family and a size makes every body-
   style element compute the family and the size, except the fixture's `.btn` buttons, which keep `16px` (a literal:
   Bootstrap's `.btn{font-size:var(--bs-btn-font-size)}` is `1rem`). Oracle: the members are the elements whose computed
   style equals `body`'s, read in the browser BEFORE Apply (assert their count: the brief review measured 44 with 40
   added); the expected values are the typed ones (and `16px` for `.btn`). Wait for the rendered receipt line, and assert
   the request's Body role carries `selectors == ['body']`; the receipt line ends with exactly `; applies page-wide through Bootstrap's body variables, and inherited text is not measured` (the literal R2.W2PS writes); Clear restores each element's computed family
   and size byte-exact (read before Apply).
2. The existing Bootstrap 5 integration test still passes. Exactly one assertion changes: the font-size line
   `[f'{size}px'] * 4` becomes `['16px', '22px', '22px', '16px']` (both `.btn` elements, `bs5.button` and `bs.hero.cta`,
   keep 16px under a `body` binding; the nav link and the label take the typed 22px), and its docstring says so. Never
   drop the buttons from the tuple; nothing else in that test changes.

## Tests and mutants

Given/When/Then docstring whose Then is exactly what it asserts. RED, recorded three ways, each failing at an explicit
early assertion (never a hang): at BASE and with W2PS alone the Body row gets no role id and no controls; with W2P alone
Studio drops the `page` reply and stays on "Detecting text styles..." (assert the status within a bounded wait). Mutants
(restored byte-exact, SHA-256 before and after; PYTHONDONTWRITEBYTECODE=1): the bridge's page binding removed; Studio's
acceptance of `page` removed; the bridge's `body` plain block dropped (the fixture's `app.css` pins `body`'s family, so
the members keep it); Studio's receipt wording reverted. A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_r2_integration test_studio_roles test_role_adapters test_support`
(the last two prove the integrated W2P and W2PS patches together). Also `python -m ruff check tests/test_r2_integration.py`
and after staging by name `git diff --cached --check`.

## Report and handoff

Report: the requirements with their oracles; each mutant; the focused run (Ran line, OK, GATE line); gross lines. Patch
`task-w2pi-code.patch` holds only your changes on top of the PATCH_DEPs, with their SHA-256s. It shares R2.W2P's commit;
draft one body sentence.
