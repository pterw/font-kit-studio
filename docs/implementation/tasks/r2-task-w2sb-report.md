# R2.W2S-b code report (MODE: code, task w2sb)

BASE 73b3ba2; worktree a scratch worktree with PATCH_DEP applied by `git apply --index`, in order:
1. task-w2t-code.patch sha256 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd (verified)
2. task-w2sa-code.patch sha256 5d9db7f7ab835a27fd6b6570077a7a3e667b9bb893ea923a5f10b680c5cd0fd1 (verified)

Patch: `task-w2sb-code.patch` (delta on that staged state), sha256 28d09c80fc5adf5dd6343a821468dc6b447e1a618634ee4d341c06d4d482cf3a;
`git apply --check -R` passes. Files: `fontkit-studio.html` (+7/-4), `tests/test_studio_roles.py` (+16/-5). 28 gross lines, all material.
The working copies are CRLF (autocrlf); edits kept the file's line endings, git normalizes to LF.

## Requirements
1. Done. `roleFamily` refuses a trimmed keyword (any case) via `ROLE_FAMILY_KEYWORDS`, and `(`/`)` outside quotes inside its existing
   one-pass quote loop (same semantics as the table's `family_refused`). `ROLE_FIELD_HELP.fontFamily` now says "not a CSS-wide keyword
   (inherit, initial, unset, revert, revert-layer), and parentheses only inside quotes". Comment above updated.
2. Done. `test_keystrokes_validate_every_intermediate_value_and_the_documented_bounds` appends every `FAMILIES_REFUSED` (not valid) and
   `FAMILIES_ACCEPTED` (valid) row from the table; for refused rows it also asserts the reason carries both help phrases. Docstring updated.
3. Done. Two rows in `hostile_receipts`: `table.FAMILIES_REFUSED[0]` (`inherit`) and `[8]` (`--x(`), built by `refused_family` with roles, css
   and digest agreeing (`with_css` first, role change last).
4. Done. Mirror `canonical_css` is `names = ADAPTER_VARIABLES.get(role['adapter'])` / `if names and 'fontFamily' in role['properties']:`, output unchanged.

## RED at BASE logic (Chromium, tests applied, source unchanged): log scratchpad/w2sb-red.log
- Field test: 8 keyword rows and 7 dashed rows FAIL on `enabled == valid` (True != False): true RED. The 4 CSS.supports-refused rows
  (`generic(kai)`, `Inter)`, `a), serif`, `Inter (Display)`) already got "not valid" and failed only on the new help-text assertion
  (red because the help wording is new). All 10 accepted rows GREEN (characterization).
- Receipt rows: both ERROR (the wait for the fence times out, hostile receipt wrongly accepted): true RED.
- GREEN after the source change: `gate.sh focused test_studio_roles test_r2_integration.StudioRoleBridgeTests.test_studios_family_field_agrees_with_the_bridge_on_every_row test_support`:
  `Ran 123 tests in 159.320s`, `OK`, `GATE focused EXIT 0 IN 160s`.

## Mutants (foreground, PYTHONDONTWRITEBYTECODE=1; script scratchpad/w2sb-mut.py; logs w2sb-m*.log). Restored byte-exact.
| mutant | file sha256 before = after | killed by |
|---|---|---|
| keyword check removed | fontkit-studio.html b8aff99f...1544 | field test: 8 keyword rows (FAILED failures=8) |
| paren check removed | same | field test: 7 dashed rows (failures=7) |
| quote-blind paren check (before the quote logic) | same | field test: accepted rows with quoted parentheses, e.g. `'Inter (Display)'`, `"A)"`, `'say "hi" (x)'` (failures=6) |
| `validRoleProperties` family branch without `roleFamily` (CSS.supports only) | same | hostile receipt test: both new rows (errors=2) |
| mirror without `'fontFamily' in` | tests/test_studio_roles.py 74692600...871a | `test_template_cases_follow_the_addendum_rules_and_carry_their_own_digests` (case body-without-family; error) |
| mirror final LF dropped (`''.join(blocks).rstrip()`) | same | same test, 5 cases (failures=5) |
Full hashes: html b8aff99f199758b79a95879997ddbfd312ea0fb3c377ca7a2cf1cf1d1dfd1544; tests 746926003503c358d845e7125fc451abdc6836932cd3cc3f316d0d209877871a.
No mutant used a case the engine already refuses.

## Other gates
`python scripts/verify.py --static-only`: provenance PASS, browser tests SKIP (static only). `ruff check tests/test_studio_roles.py`: All checks passed.
`git diff --check`: exit 0. pre-commit not run (shared scratch worktree; controller hooks at landing).

## Handoff
- Commit subject `fix(studio): refuse the same role families as the bridge`; plan item R2.W2S (Addendum 22 item 1, D072).
- Draft body: Studio accepted CSS-wide keywords and, in Chromium, unquoted parentheses in a role family, so Apply was offered for a value
  the bridge refuses. roleFamily now refuses both, the field help names the rules, and receipts or snapshots carrying such a family are
  malformed. The test serializer mirror follows the bridge's roleCssBlocks shape.
- Controller: README.md near 572 still states the old family rule; update at the release-point pass. Line budget: slice b is 28 gross.
- Deviation: the mirror mutant "final LF dropped" used `.rstrip()` on the joined output (equivalent effect).

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
