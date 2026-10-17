### Spec Compliance
- PASS: Req 1, families. `unquotedParenthesis` plus the keyword regexp sit in `roleFamily` before `CSS.supports`; refusal is the existing `unsupported-value` / `Unsupported property value`; the rule is stated beside `balancedQuotes` and nothing wider (fontkit-bridge.js:192-208).
- PASS: Req 2, install count. `verifyRoleSheet` keeps connected, `textContent === css`, owner node, not disabled, and compares `sheet.cssRules.length === ruleCount`; the reference parse and the `CSSStyleSheet` dependency are gone; comment updated (1380-1387). The second caller `attributeLoss` passes `job.blocks`, which is `blocks.length` (1451, 1659), so it stays correct.
- PASS: Req 3, validate then read. `canonicalizeRoles(roles)` has no `evidence` parameter, returns `{roles, blocks, css}` or `{reason, detail}`, and holds the heading shape, selectors, values and the 128 KiB `size-limit` (261-283). The handler reads evidence only after it, only for a non-plain role, through `readWithoutRootPreview`, which suspends only when `rolesHaveRootBlock(this.roleAccepted.roles)` (1303-1307, 1431-1438). The comment above `handleRoleMutation` is rewritten and is accurate (1407-1411).
- PASS: Req 4, tokens. `getCurrentTokens` reads values inside `readWithoutRootPreview`, names collection unchanged (3762-3770); `rolesHaveRootBlock` is reused, not copied. `getCurrentTokens` has one caller (the hello, 1200), and `handleHello` calls `cancelRoleJobs()` first (1175), so releasing the ban there cannot cut a live Detect ban short.
- PASS: Req 5. `EMPTY_HASH` and `fnv1a32` are imported from `role_contract`; the local copies are removed.
- PASS: Req 6. `bootstrapVariables()` returns `{evidence, mono}`; Detect passes only `mono`; `bootstrapHeadingSelectors` is stated directly; the adapter clause is two statements. Behaviour unchanged (existing tests green in the report's focused run).
- PASS: Req 7, EFF1. One `JSON.stringify` per element keys a `Map` scoped per role and selector; `signatures` is still pushed in first-seen order and `count` increments as before, so output order and counts are unchanged. Timings in `timing-w2b1.log` (1 role: 976/1014/913 ms to 502/510/497; 3 roles: 1778/1554/1488 ms to 508/520/514).
- PASS: Budget. Gross 304 lines (246 added, 58 removed) against about 330. Files are exactly the two owned ones; the only edits to existing test content are the top imports and the removed hash helpers.
- FAIL (minor): the install-count test for non-Chromium engines passes with zero subtests instead of being skipped with a reason (test_role_stylesheet.py:1331-1332). See Minor 1.
- CANNOT VERIFY FROM DIFF: the Apply-only evidence mutant and the level-uniformity mutants. The brief leaves them to R2.W2B2 phase 2 and the controller.

### Checks run
- Checklist 1, drift:
  - Rule against the table: extracted `unquotedParenthesis` and the keyword regexp from the frozen bridge and ran them in node against `role_contract.family_refused`, over all `FAMILIES_REFUSED`, `FAMILIES_ACCEPTED` and `FAMILY_KEYWORDS` plus 20,000 random strings over the alphabet `" ' ( ) a , inherit Revert-Layer INITIAL unset x -`. Script `w2b1-review-fuzz.py`. Result: 0 mismatches; every refused row refused, every near miss accepted.
  - Studio's planned rule: plan Addendum 22 item 1 (docs/plans/2026-10-03-r2-engine.md:449-451) says "exactly a CSS-wide keyword ... in any case, or `(` or `)` outside quotes". The bridge matches it. `a scratch worktree` Studio is still in progress and its `roleFamily` (3883) has no new rule yet, so I could not compare against code there. That is not this task's drift; the brief names `test_studios_family_field_agrees...` for it.
  - Signature: `canonicalizeRoles(roles)` (261) has no evidence parameter.
- Checklist 2, mutants. Script `w2b1-review-mutate.py` serves a mutated copy of the final bridge through `RoleBridgeCase.open` and patches `test_role_stylesheet.BRIDGE`. The worktree files were hashed before and after: bridge 3a0f96a9...936d and tests 35d47d03...e98d, identical. `PYTHONDONTWRITEBYTECODE=1`. All ten mutants died:

  | Mutant | Killed by |
  |---|---|
  | keyword check removed | UnsafeFamilyTests refused test; `inherit`, `initial`, `unset` etc. applied |
  | paren check removed | same test; `--x(` applied for plain, `stylesheet-blocked` for bootstrap5-body |
  | count condition -> `true` | cut-sheet test: `roles-applied` != `stylesheet-blocked` |
  | evidence read moved before validation | ValidateBefore test (a) with bootstrap5-body: a `childList HEAD` ban record; it also made the family-preview count 2 != 1 |
  | size check moved after the evidence read | ValidateBefore test: a `childList HEAD` ban record for the oversized bootstrap5-body request |
  | read always suspends (EFF3) | evidence-read test, plain and no-family previews: 1 != 0 |
  | `rolesHaveRootBlock` without its `fontFamily` half | evidence-read test, no-family preview: 1 != 0 |
  | tokens read with the preview on | ReadyTokensTests: `('Inter','Inter') != ('Georgia','Georgia')` |
  | restore skipped | ReadyTokensTests: `'sans-serif' != 'Inter'` |
  | Map keyed by family alone | `test_role_protocol.RoleContractTableTests...signature_limit`: `[('k', 1)] != [('k', 1024)]` |

  - RED at the PATCH_DEP/BASE install check: ran `cut_sheet_is_blocked` against the staged PATCH_DEP bridge (`w2b1-review-red.py`). Result: `('design:roles-applied', None) != ('design:rejected', 'stylesheet-blocked')`. The brief's RED holds.
- Checklist 3, real bridge: every new test goes through `RoleSheetCase.open`, which loads the real `fontkit-bridge.js`. The two with `bridge_source=` serve the final bridge text, with one asserted edit (parenthesis check removed) or one prefixed statement (the constructor throws). No fake bridge or mocked reply.
- Checklist 4, hidden skips:
  - Focused run of the four new classes: 7 tests, OK, none skipped.
  - CI sets `FKS_ENGINES: chromium` for the role tests (quality-gate.yml:154,170,284,322). Firefox runs only `firefox_canary`. So hosted CI skips none of the new tests.
  - The install-count Chromium-only test has only a comment, not a skip. A local `FKS_ENGINES=firefox` or `webkit` run goes green with zero subtests (Minor 1).
- Checklist 5, tests:
  - Oracles. The families test compares against a literal pre-state (`['.body-copy {\n  font-family: Inter;\n}\n'], 'Inter'`) and the table rows. The near-miss test uses a literal computed family per row and asserts `set(NEAR_MISS_COMPUTED) == set(FAMILIES_ACCEPTED)`. The tokens oracle is `Georgia`, a literal and also a read taken before Apply.
  - Observer. `WATCH` observes `document.documentElement` with `subtree`, `childList`, `attributes` and `characterData`. The oversized request is 3 roles x 32 x 1,400-character selectors: over 128 KiB of canonical CSS and under 256 KiB of request. It gives `size-limit`, as asserted.
  - Tokens test. It asserts the owned node text equals the apply receipt's `canonicalCss`, the body role still computes `Inter`, and no `<style>` containing `transition: none` remains.
  - Page version. A probe (`w2b1-review-pv.py`) shows the re-hello with a `:root` preview leaves `pageVersion` at 0 (hello, hello again), so the suspend/ban write is not mistaken for a page change.
  - EFF1. The Map keeps the output order, and the existing 1,024-signature test passes unchanged.
  - Worktree state: byte-identical afterwards. `git diff` equals the delivered patch and `git diff --check` is clean. I started no server and no browser outside the test contexts, which close through `addCleanup`.
- Checklist 6, code:
  - No copy of `rolesHaveRootBlock`. Its callers are `readWithoutRootPreview` and Detect's `rooted` (1935).
  - Validation (`canonicalizeRoles`), state change (the handler) and the read (`readWithoutRootPreview`) stay apart. The `roleCssBlocks` call inside `canonicalizeRoles` is what the brief asks for, to compute the size limit.
  - Concern 4, the residue. The handler comment states it accurately: "a valid request refused for missing evidence can therefore still write". The report's CHANGELOG draft says "Apply no longer touches the document for a request it refuses as invalid", which is true. No docstring over-claims. The one over-claim is in the plan, outside this diff: docs/plans/2026-10-03-r2-engine.md:470, "a rejected request writes nothing to the page" (Minor 3).

### Strengths
- The validate-first and EFF3 tests prove both sides. The observer sees ban records for the old order, and the count of added `transition: none` styles is 0, 0 and 1 across plain, no-family and family previews. The no-family case kills the `fontFamily` half of `rolesHaveRootBlock`, the survivor from W2B2, as the brief wanted.
- The install-count RED is real. The same assertions fail on the PATCH_DEP install check and pass on the final one.
- The family rule is exactly the table's rule: 0 mismatches in 20,034 cases.
- The tokens test would fail for either half of the fix (preview left on, or restore skipped).

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. test_role_stylesheet.py:1331-1332: `if engine != 'chromium': continue` makes the cut-sheet test pass with zero assertions under `FKS_ENGINES=firefox` or `webkit`. The brief said "skip with that reason elsewhere", and constraints say every skipped engine is reported. Use `self.skipTest(reason)` or a skipped `subTest` so the reason shows in the output. No hosted job runs the role tests on those engines, so no CI green is affected.
2. fontkit-bridge.js:192-193: the comment above `unquotedParenthesis` also describes the keyword refusal, which lives in `roleFamily` as an inline regexp (207). Move the keyword half of the sentence next to the regexp. Cosmetic.
3. docs/plans/2026-10-03-r2-engine.md:470 (controller's file): "so a rejected request writes nothing to the page" is false for a valid request refused for missing evidence while a `:root` preview is live. It is true for invalid requests only. Qualify it when the controller books the task. The report already says so.
4. The brief's EFF1 evidence named the efficiency review's `cr23-EFF-r2-probe-checks2.py`, which is not in the scratchpad. The implementer substituted an equivalent 128 x 8 page and disclosed it. It was not re-run from the original.
5. The cut-sheet helper `cut_sheet_is_blocked(engine, source)` takes a source parameter but has one caller in the repo. The parameter exists for the RED run against BASE's source. Acceptable.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every requirement is implemented, and ten mutants (including the validate-first ones and EFF3's always-suspend) die against the new tests. The family rule matches the table on 20,034 cases, and the install-count RED is reproduced at the PATCH_DEP install check. The only findings are Minor: a silent non-Chromium pass in one test, comment placement, and a plan over-claim.
