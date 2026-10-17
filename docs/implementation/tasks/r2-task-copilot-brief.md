# PR #22 Copilot review fix, bridge (controller, 2026-10-17)

BASE `f11055e`. Worktree `C:/fks/t28`. You own `fontkit-bridge.js` (only
`familyNames` and its comparison callers) and `tests/test_role_preview.py`
(new rows only). Rules: `.superpowers/sdd/r2/constraints.md`. The controller
checked the finding in source. A separate Studio fix runs in parallel in
`C:/fks/ts4`; do not touch Studio files.

## Finding (Copilot comment 4300483997, `fontkit-bridge.js:204`)

- `familyNames(value)` (~194-205) parses a font-family list, honouring quotes,
  and returns `names.join(',')`. A quoted family that contains a comma
  therefore collides with two separate families:
  - the requested `"A,B"` (one family) and an author's `A, B` (two families)
    both become `A,B`;
  - `roleMismatches` and the attribution comparison then report no
    font-family loss, although the computed family list differs.
- Callers, all of them comparisons: ~1467 (computed value), ~1489 (candidate
  rule value) and ~1500 (requested value). No stored or wire value uses the
  result.

## Fix

- Return a serialization that keeps list boundaries, for example
  `JSON.stringify(names)`.
- Equivalent quoted and unquoted names still compare equal: `"Georgia"` and
  `Georgia`, and different whitespace.
- Keep the quote parsing exactly as it is.

## Tests (`tests/test_role_preview.py`, real bridge, Given/When/Then)

1. RED first: a role whose family is `"A,B", serif` meets an author rule
   `font-family: A, B, serif` that wins. The receipt reports a fontFamily
   loss with the exact count. At BASE it reports none.
2. Equality is preserved: a requested `"Georgia", serif` against a computed
   `Georgia, serif` gives no loss.
3. Kill the mutant that restores `join(',')`.

## Gates and output

- Run only:
  `python -m unittest test_role_preview test_role_stylesheet test_role_protocol test_support -v`,
  with `PYTHONPATH=tests`, `FKS_ENGINES=chromium` and `FKS_REQUIRE_FIXTURES=1`.
- Also run `node --check fontkit-bridge.js`.
- Never commit.
- Output:
  - `.superpowers/sdd/r2/task-copilot-code.patch`: the full staged diff
    against `f11055e`;
  - `.superpowers/sdd/r2/task-copilot-code-report.md`: RED/GREEN, the
    mutant, the counts and the sha256.
