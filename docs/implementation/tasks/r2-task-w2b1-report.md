# R2.W2B1 code report (MODE code, task w2b1)

BASE 73b3ba2b2bbc00ee4f501a338e61ff422afed8ff. Worktree a scratch worktree, with both PATCH_DEPs applied and staged first.
PATCH_DEP SHA-256 (checked before applying):
- task-w2b2-code.patch ffd3bcffd888641fac66cace368443d85d1141b20c3bde5475874414077cd12b
- task-w2t-code.patch 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd

Patch: `.superpowers/sdd/r2/task-w2b1-code.patch` (delta over the staged PATCH_DEP state), SHA-256
f6bbdfb0c1e05eed5c7aae2a78105c32eb376859a1eeb48b35a1422d89f9a21c; `git apply --check -R` passes in the worktree.
Files: `fontkit-bridge.js`, `tests/test_role_stylesheet.py` (no new file). Gross 304 lines (246 added, 58 removed; budget about 330).
Final bridge SHA-256 (worktree, CRLF checkout) 3a0f96a9...936d; test file 35d47d03...e98d.

## Requirements

1. Families (D072): done. `unquotedParenthesis` (same one-pass scan as `balancedQuotes`) and the keyword regexp sit in `roleFamily`
   before `CSS.supports`. State at BASE in Chromium (probe `rows-w2b1.py`, log `rows-w2b1.log`): the 5 keywords, `INHERIT`,
   `Revert-Layer`, `  inherit  ` and the seven dashed rows are accepted (RED); `generic(kai)`, `Inter)`, `a), serif`,
   `Inter (Display)` are `unsupported-value` (GREEN, kill nothing); all ten near misses accepted (GREEN).
2. Install count: done. `verifyRoleSheet` is the four conditions plus `sheet.cssRules.length === ruleCount`; the reference parse and
   the `CSSStyleSheet` dependency are gone; comment rewritten. `attributeLoss`' second caller unchanged.
3. Validate, then read evidence: done. `canonicalizeRoles(roles)` returns `{roles, blocks, css}` or `{reason, detail}`; it holds the
   heading shape, selectors, values and the 128 KiB `size-limit` (no detail). `handleRoleMutation` then, for a non-plain role, reads
   evidence through new `readWithoutRootPreview(read)` (suspends and releases the ban only when
   `rolesHaveRootBlock(this.roleAccepted.roles)`; otherwise reads directly) and refuses `Unsupported adapter`. Comment above
   `handleRoleMutation` rewritten. Precedence note: no hostile-table row depends on the old order (rows assert the reason only; none
   holds two faults). What shifts: an invalid selector, an invalid value and `size-limit` now win over `Unsupported adapter`. Residual:
   a valid request refused for missing evidence still writes the ban when the preview holds a `:root` block. Addendum 22's and the
   CHANGELOG's "a rejected request writes nothing" is true for invalid requests only.
4. Tokens: done. `getCurrentTokens` reads the computed values inside `readWithoutRootPreview` (names collection unchanged). The
   owned-sheet skip is not added (equivalent, per the brief review). `ready.tokens` pin: `test_bridge_runtime.HandshakeTests` (ran, OK).
5. `test_role_stylesheet.py` imports `EMPTY_HASH` and `fnv1a32` from `role_contract`; its copies are removed.
6. SIMPLIFY1/3: done. `bootstrapVariables()` returns `{evidence, mono}`; Detect passes only `mono` to `suggestBootstrapAdapters(groups,
   facts, monoFamily, bodyStyle)`. `bootstrapHeadingSelectors`: a lone `.display-N`, else every selector `hN`/`.hN` of the first
   selector's level. The adapter clause is two statements (heading shape in `canonicalizeRoles`, evidence in the handler).
7. EFF1: done. The known-role selector check keys a `Map` by one `JSON.stringify(style)` per element; output order and counts unchanged.

## Tests added (all with Given/When/Then docstrings; expected values from the table or literals)

`UnsafeFamilyTests` (2), `InstallCountTests` (2, the cut-sheet one Chromium-only with the reason in a comment), `ValidateBeforeReadingTests`
(2), `ReadyTokensTests` (1). The near-miss test is a characterization (GREEN at BASE, no RED).

## RED at BASE's bridge (`red-w2b1.py`, log `red-w2b1.log`; bridge swapped in and restored byte-exact, SHA 3a0f96a9... before and after)

- Keywords and dashed rows test: fails (53 failing subtests across the four classes, 5 tests failing; near-miss test passes).
- Constructor throws: `design:rejected` != `design:roles-applied`.
- Validate-first: records `childList HEAD` (the ban) for the bootstrap5 requests; the evidence-read test fails on the plain and
  no-family previews (`1 != 0`).
- Tokens: second hello reports Inter (preview) instead of Georgia.
- Cut sheet: BASE's source passed through `bridge_source=`: `('design:roles-applied', None) != ('design:rejected', 'stylesheet-blocked')`.

## Mutants (`mutate-w2b1.py NAME`; foreground; bridge SHA-256 before and after both 3a0f96a94e5c...dd936d, identical for every run)

| Mutant | Test failing |
|---|---|
| keyword check removed | UnsafeFamilyTests refused-family test: `inherit`, `initial`, `unset`... applied |
| parenthesis check removed | same test: `--x(` and the dashed rows applied (`stylesheet-blocked` for the bootstrap5 `--x(`) |
| parenthesis refused even inside quotes | near-miss test: 5 quoted-paren rows `rejected` != `applied` |
| install count condition -> true | InstallCountTests cut-sheet: `applied` != `stylesheet-blocked` |
| install check constructs a `CSSStyleSheet` | InstallCountTests constructor test: `rejected` != `applied` |
| evidence read moved before validation | ValidateBeforeReadingTests (a)/(b): a record `childList HEAD` |
| size check moved after the evidence read | same test: the ban record |
| evidence read always suspends | evidence-read test: `1 != 0` for the plain and no-family previews |
| `rolesHaveRootBlock` without its `fontFamily` half (R2.W2B2's survivor) | evidence-read test, no-family preview: `1 != 0` |
| tokens read with the preview on | ReadyTokensTests: `('Inter','Inter') != ('Georgia','Georgia')` |
| restore skipped after the tokens read | ReadyTokensTests: `'sans-serif' != 'Inter'` (preview left disabled) |
| Map keyed by family alone | `test_role_protocol.RoleContractTableTests.test_a_known_selector_over_the_most_styles...`: `[('k', 1)] != [('k', 1024)]` |
| evidence `||` instead of `&&` (SIMPLIFY1) | `test_role_adapters.SuggestionTests.test_evidence_needs_both_variables` (2 subtests) |
| heading levels `some` instead of `every` | `EvidenceTests.test_a_heading_role_must_name_one_level_or_one_display_class` |
| `.display-N` branch dropped | `DisplayHeadingApplyTests` display Apply test |
| Apply evidence check dropped | `AtomicRejectionTests` row `adapter-bootstrap-without-evidence` (and the later rows that lean on rejection) |

Not proved here: the Apply-only evidence mutant (T1) and the level-uniformity mutants against phase 2's tests; the controller
re-runs them once R2.W2B2 phase 2 lands.

## EFF1 timings (`timing-w2b1.py`, log `timing-w2b1.log`; 128 groups x 8 variants, known role `.k`, Chromium; PATCH_DEP bridge vs final)

| known roles | before (3 runs, ms) | after (3 runs, ms) |
|---|---|---|
| 1 (1,024 signatures) | 976, 1014, 913 | 502, 510, 497 |
| 3 (3 x 1,024) | 1778, 1554, 1488 | 508, 520, 514 |

All complete (`reason: null`), signatures 1,024 each. (the efficiency review's `cr23-EFF-r2-probe-checks2.py` is not in the scratchpad; this is my own
equivalent page, the table's 128 x 8 author-role page of R2.W2T's test.)

## Gates

- Focused (brief's command): `Ran 177 tests in 230.789s`, `OK`, `GATE focused EXIT 0 IN 232s`.
- `node --check fontkit-bridge.js`: ok. `python -m ruff check tests/test_role_stylesheet.py`: All checks passed.
- `git diff --check` (worktree vs index): clean. No new files, so no `git add -N` needed.
- pre-commit not run (the brief asks for ruff on changed Python and node --check).

## Deviations / notes

- Line endings: the checkout is CRLF (core.autocrlf true); edits kept CRLF and the patch is LF-normalized by git.
- `test_role_adapters.py` 476 (`test_without_the_stylesheet_constructor_the_rule_count_is_the_block_count`) still passes; its rename is R2.W2P's.
- The constructor-throws test prefixes a statement to the bridge source through `bridge_source=` (the existing test's technique) instead of an init script.

## Handoff

Commit subject: `fix(bridge): refuse unsafe role families and count the installed rules`

Draft body (72 cols):

    A family that is a CSS-wide keyword or holds a parenthesis outside
    quotes is refused before CSS.supports, so it can no longer blank the
    Bootstrap 5 :root variables. The install check now requires one
    parsed rule per canonical block, so a sheet the parser cuts short is
    refused instead of acknowledged.

    Apply validates shapes, selectors, values and size before it reads
    the Bootstrap evidence, and suspends the preview for that read only
    when it holds a :root block. design:ready reports the page's own
    tokens while such a preview is installed. The known-role selector
    check keys its signatures by one serialization per element.

CHANGELOG draft: "Role families that are a CSS-wide keyword or hold a parenthesis outside quotes are refused. A role sheet the
browser parser cuts short is refused instead of acknowledged. `design:ready` reports the page's own tokens while a Bootstrap 5
preview is installed. Apply no longer touches the document for a request it refuses as invalid, and selector checks and Apply are
faster on large pages."

Plan item: R2.W2B1 (Addendum 22 item 1 and its bridge-fix paragraph). Correct its Owns line: drop `tests/test_role_adapters.py`.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
