# R2.W2S-c code report (MODE code, task w2sc)

BASE 73b3ba2b; worktree a scratch worktree. PATCH_DEP SHA-256s (all matched, applied with `git apply --index` in order):
w2t 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd; w2sa 5d9db7f7ab835a27fd6b6570077a7a3e667b9bb893ea923a5f10b680c5cd0fd1;
w2b2 ffd3bcffd888641fac66cace368443d85d1141b20c3bde5475874414077cd12b; w2b1 f6bbdfb0c1e05eed5c7aae2a78105c32eb376859a1eeb48b35a1422d89f9a21c;
w2sb 28d09c80fc5adf5dd6343a821468dc6b447e1a618634ee4d341c06d4d482cf3a.

Patch: `task-w2sc-code.patch` (delta on the five staged PATCH_DEPs; sha256 ff419a4bb5ab93af539a0a09e278397763fdde7629281602700ee1045f001a6c;
`git apply --check -R` passes). Only `tests/test_r2_integration.py`: 2 insertions, 1 deletion (3 gross lines).

## Requirements
1. Done. `import role_contract as table` added before `from support import ...`; `FAMILIES` gains
   `[(v, False) for v in table.FAMILIES_REFUSED] + [(v, True) for v in table.FAMILIES_ACCEPTED]` (19 refused, 10 accepted, read by
   name from the table; the oracle is the table, not either side's output). The parity test iterates `FAMILIES` unchanged.
2. Done, no edit: the docstring's Then ("Apply is enabled exactly when the bridge accepts the value") is what the Apply-state
   assertion checks; the raw-reply assertion is not in the Then (brief review Minor 5, ownership not widened).
No RED run by me: with the W2S-b Studio and W2B1 bridge both in place the new rows are GREEN; the reviewer's measured RED on BASE Studio
(15 rows) was not repeated. The 4 table-only refused rows (`generic(kai)`, `Inter)`, `a), serif`, `Inter (Display)`) are GREEN on
both sides already (CSS.supports refuses them) and kill no mutant.

## Mutants (single test `test_r2_integration.StudioRoleBridgeTests.test_studios_family_field_agrees_with_the_bridge_on_every_row`,
Chromium, foreground, PYTHONDONTWRITEBYTECODE=1; script and log `w2sc_mut.py`, `w2sc-mut.log` in the scratchpad)
Source SHA-256 before = after for every mutant (fontkit-studio.html b8aff99f..., fontkit-bridge.js 3a0f96a9...; full hashes after:
b8aff99f199758b79a95879997ddbfd312ea0fb3c377ca7a2cf1cf1d1dfd1544, 3a0f96a94e5cf0f23a19e188eaabf8255af992256b0d9df03ce3792107dd936d).
| mutant | rows failed | assertion |
|---|---|---|
| Studio keyword check removed | the 8 keyword rows | Apply state (True != False) |
| bridge keyword check removed | the 8 keyword rows | raw reply (applied vs rejected) |
| Studio parenthesis check removed | the 7 dashed rows | Apply state |
| bridge parenthesis check removed (`unquotedParenthesis` call) | the 7 dashed rows | raw reply |
| bridge keyword regex without `$` | `Initialism, serif`, `Inherit Sans`, `inherited`, `revert-layers` | raw reply (False != True, rejected) |
| Studio paren scan ignoring quotes | the 5 quoted accepted rows (`'Inter (Display)'`, `"Inter (Display)"`, `"A)"`, `"Inter's (x)"`, `'say "hi" (x)'`) | Apply state (False != True) |
| bridge paren scan ignoring quotes | the same 5 quoted rows | raw reply (rejected) |

## Gates
Focused: `sh .../tools/gate.sh focused test_r2_integration test_support` -> `Ran 62 tests in 72.232s`, `OK`, `GATE focused EXIT 0 IN 73s`.
`python -m ruff check tests/test_r2_integration.py` -> All checks passed. `git diff --check` -> exit 0 (delta unstaged; the controller's
`git diff --cached --check` runs at landing).

## Handoff
Subject: `test: prove Studio and the bridge refuse the same families`
Draft body: The family parity test only covered the older refusals, so
nothing showed the real Studio and the real bridge agree on CSS-wide
keywords and parentheses outside quotes (D072). Add every refused and
accepted case from the contract table, so a change on either side that
drifts, or that refuses a near miss, fails a row.
Tick the R2.W2S plan item at this landing (controller). Note: the worktree files are CRLF; the patch is LF-clean (git normalises).

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
