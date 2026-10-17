# R2.W2B1 brief: refuse unsafe families, count the installed rules, validate before reading evidence, report the page's tokens

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22 item 1 and its paragraph of bridge fixes, task R2.W2B1; D072; the
binding contract's "Selector and value validation" and "Canonical CSS, ownership and undo". PR B2 wave W2, phase 2, beside
R2.W2B2 phase 2 (disjoint files). BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with two patches applied first in the
worktree (PATCH_DEP, unstaged; the controller names their SHA-256 in the dispatch): `task-w2b2-code.patch` (R2.W2B2 phase 1:
the bridge's heading step, names and Detect batches) and `task-w2t-code.patch` (R2.W2T: the table's refused-family data and
`fnv1a32`). Worktree `a scratch worktree`, task id `w2b1`. Line budget: about 330 gross lines (EFF1, EFF3 and SIMPLIFY1/3 included); explain any excess.

## Why

The whole-branch review (workspace `w2-review.md` items P1, P2, P4, P5, P10, R1, S7; each checked in source) found, at BASE:

1. **Families (D072).** `roleFamily` (`fontkit-bridge.js` 192-197) accepts a CSS-wide keyword and an unquoted parenthesis:
   `CSS.supports('font-family', v)` is true for `inherit`, `initial`, `unset`, `revert`, `revert-layer` and, in Chromium,
   for dashed functions such as `--x(` and `--x(a)` and for an unclosed `if(`; the blocklist (181) stops only
   `url|expression|var|env|attr` before `(`. `roleCssBlocks` (293-295) writes the family into the Bootstrap 5 `:root`
   block, where a keyword or `--x(a)` blanks the variables and the whole page falls back to the browser's default font.
2. **The install check sees nothing it exists for.** `verifyRoleSheet` (1355-1368) compares the node's parsed rules with a
   reference parse of the same text whenever `CSSStyleSheet` exists, so a sheet the parser cuts short passes; the block
   count is used only in the fallback (1366), which no real browser reaches (every engine has the `CSSStyleSheet`
   interface, and where it cannot be constructed `new CSSStyleSheet()` throws into the `catch`, so every Apply is refused
   there). Verified: the request [plain `.lead` with family `--x(` and 30px, plain `.small` 11px, `bootstrap5-body` with
   `Inter` 18px] on the Bootstrap 5 fixture is acknowledged with all four blocks in `canonicalCss`, while the owned sheet
   holds one rule, `.lead { }`; nothing renders and the outcomes blame an author rule. The contract says a blocked sheet
   is a failed install, not an applied success.
3. **A rejected request writes to the page.** The Apply-time evidence read (1408-1414: `suspendRoleSheet`,
   `bootstrapVariables`, restore, `releaseRoleQuiet`) runs before `canonicalizeRoles` (1415) validates selectors and values.
   With a live preview, a request holding a `bootstrap5-*` role plus an invalid selector appends and removes the
   transition-ban `<style>` in `<head>` (two mutation records) and forces a layout, while the same request with plain roles
   writes nothing. The comment at 1387-1388 and the CHANGELOG promise validation before any write.
4. **Ready reports the preview as the page's tokens.** `getCurrentTokens` (3709-3740), sent in `design:ready` on every hello
   (1181), collects custom-property names from every stylesheet, the owned role sheet included, and reads computed `:root`
   values with the preview on. With a body or mono preview, a re-hello reports the preview's `--bs-*` values, and on a page
   without `--bs-font-monospace` that name appears. Every other reader of `document.styleSheets` skips owned sheets
   (`roleStyleStamp` near 1252, `collectAuthorRules` near 1619). In-repo Studio does not read `ready.tokens` (it parses
   `changes.tokens`); integrators may, and the README documents the field.
5. **The last hash copy.** `tests/test_role_stylesheet.py` keeps its own `EMPTY_HASH` (10) and `fnv1a32` (38); R2.W2T moved
   both into the table.

## Owned files (exact)

- `fontkit-bridge.js`: the family rule (`ROLE_FAMILY_UNSAFE`, `balancedQuotes`, `roleFamily`, 181-197), `canonicalizeRoles`
  (246-270) only as far as validation-before-evidence needs, `verifyRoleSheet` and `installRoleSheet` (1353-1381),
  `handleRoleMutation` (1387-1437) and `getCurrentTokens`; for requirement 6, `bootstrapVariables` and its callers
  (`collectRoleStyles`, `suggestBootstrapAdapters`, which R2.W2B2 phase 1 also edited: build on its version) and
  `bootstrapHeadingSelectors`; for requirement 7, the known-role selector check in `detectTextStyles` (near 2012). Line
  numbers are at BASE; R2.W2B2's patch moves the lines after about 1780, so find the later functions by name.
- `tests/test_role_stylesheet.py`, except `BaselineDetectTests`' test that R2.W2B2 added.

Read-only: `fontkit-studio.html` (R2.W2S-b changes Studio's family rule beside you, from the same table),
`tests/role_contract.py`, `tests/test_role_adapters.py` (R2.W2B2 phase 2 owns it now), every other file. Running worktrees
beside yours: `a scratch worktree` (R2.W2B2 phase 2, `tests/test_role_adapters.py`) and `a scratch worktree` (R2.W2S-b, Studio): never
touch them. Addendum 23 (D074) adds R2.W2P after you; it changes `canonicalizeRoles` again (one body and one mono role per
request). Do not implement that here.

## Read first

`constraints.md` (all of it); Addenda 17 and 22, D068, D069, D072; the contract sections named above; at BASE
`fontkit-bridge.js` 168-300, 1324-1437, 1615-1640 and 3700-3745; `tests/test_role_stylesheet.py` 1-120 and its hostile
tables; `tests/role_contract.py` with R2.W2T's patch (the names it gives the refused-family cases and the near misses).

## Requirements

1. **Families (D072).** `roleFamily` refuses a trimmed value that equals a CSS-wide keyword in any case, and a value with
   `(` or `)` outside quotes (the scan the table defines), before `CSS.supports`. The refusal is the existing
   `unsupported-value` / `Unsupported property value`, and the previous preview, roles and revision stay. Every case in
   `FAMILIES_ACCEPTED` still passes; every case in `FAMILIES_REFUSED` (and `FAMILY_KEYWORDS`) is refused. Write the rule
   plainly beside `balancedQuotes`; do not widen it to anything the table does not list. The report lists each row's state
   at BASE in Chromium: the keywords and the seven dashed rows are RED; `generic(kai)`, `Inter)`, `a), serif` and
   `Inter (Display)` are already refused by `CSS.supports` (GREEN, they kill nothing); near misses are GREEN.
2. **Count the installed rules.** The install check requires the parsed rule count to equal the block count in every engine;
   drop the reference parse and its `CSSStyleSheet` dependency. Keep the other conditions (connected, `textContent === css`,
   a sheet whose `ownerNode` is the node, not disabled). Update the comment above it.
3. **Validate, then read evidence (and only when it matters).** `canonicalizeRoles(roles)` loses its `evidence`
   parameter: it checks shapes, selectors, values, heading shapes, and computes the blocks and the 128 KiB `size-limit`.
   Only then, when a role is not plain, `handleRoleMutation` reads the Bootstrap evidence and refuses an unsupported adapter
   with `Unsupported adapter` as today. The evidence read suspends the role sheet only when the accepted preview holds a
   `:root` block (`rolesHaveRootBlock` of the accepted roles; EFF3 in `w2-review.md`: a plain block is font-only and cannot
   set the variables, so the read is exact without suspending); otherwise it reads directly, with no ban and no forced
   layout. So a request invalid in any way, an oversized one included, is refused without any write to the document.
   Report: no existing hostile-table row depends on the old detail order (the brief review checked: rows assert the reason
   only, none holds two faults); the shift is that an invalid selector or value now wins over an unsupported adapter; and
   a valid request refused for missing evidence still writes the ban when the preview holds a `:root` block. Rewrite the
   comment above `handleRoleMutation` (1387-1388 and 1408 at BASE, review item S7) to say this. R2.W2P (Addendum 23)
   builds on this signature.
4. **Tokens.** When the accepted roles hold a `:root` block (call R2.W2B2's `rolesHaveRootBlock(roles)`; never write a
   second copy), `getCurrentTokens` reads the values with the role sheet suspended (as the evidence read does, releasing the
   ban after). With a plain preview or none, it does exactly what it does at BASE. (No owned-sheet skip: the brief review
   showed it changes nothing, because the owned sheet's names read empty and are dropped.) `ready.tokens` has no row in the
   table (not a role-protocol field): its pin is `test_bridge_runtime.HandshakeTests` (278-279); Studio does not read it,
   integrators do (README near 556).
5. `test_role_stylesheet.py` imports `EMPTY_HASH` and `fnv1a32` from the table and drops its own.
6. **SIMPLIFY1 and SIMPLIFY3 (workspace `w2-review.md`), behaviour unchanged.** `bootstrapVariables()` returns
   `{evidence, mono}` so the evidence conjunction is written once (Detect passes only `mono` on); `bootstrapHeadingSelectors`
   is stated directly (a lone `.display-N`; else every selector `hN` or `.hN` of the first selector's level), and
   `canonicalizeRoles`' mixed `&&`/`||` adapter clause becomes two statements. In your worktree these tests cover the lines:
   the Detect one-variable test (`test_role_adapters.py` 216), the heading-shape loop (465), the
   `adapter-bootstrap-without-evidence` row and R2.W2B2 phase 1's display Apply test; name which fail under one mutant of
   each. The Apply-only evidence mutant and the level-uniformity mutants are proved by R2.W2B2 phase 2's tests, which run
   beside you: the controller re-runs those mutants once both land.
7. **EFF1, the known-role selector check (`w2-review.md`).** The check matches each element's style to earlier signatures
   with two `JSON.stringify` calls per pair (O(matched x signatures)); key a `Map` by one stringify per element, same output
   order and counts. Evidence: R2.W2T's 1,024-signature test (on your PATCH_DEP) before and after (three timings each), and
   the two- and three-known-role page from the efficiency review's probe (`cr23-EFF-r2-probe-checks2.py` in the scratchpad) completing.

## Tests (each with a Given/When/Then docstring whose Then is exactly what it asserts, and one recorded mutant)

- Families: every refused case in the table is refused for a plain role and for a `bootstrap5-body` role on a page with
  evidence; the previous preview stays byte-exact (owned sheet text and a computed style read before and after); every near
  miss is accepted and renders, asserted against a literal expected computed family per case (browsers re-serialize
  quotes). Mutants: the keyword check removed; the parenthesis check removed (only the dashed rows kill it, Chromium only).
- Install count (Chromium only: Firefox's `CSS.supports` already refuses `--x(`; skip with that reason elsewhere): through
  `bridge_source=` with a copy of YOUR final bridge whose parenthesis check is removed by one asserted string replacement,
  the request [plain `--x(` role, plain second role] is refused `stylesheet-blocked`, leaves no owned node and keeps the
  previous preview. RED: the same assertions with `bridge_source=` BASE's bridge source (BASE has no parenthesis check, and
  its install check acknowledges the cut sheet). And with `CSSStyleSheet` present but throwing when constructed (an init
  script before the bridge loads), a valid Apply is accepted and renders (RED at BASE: refused). Mutant: the count condition
  removed.
- Validate first: with a live preview holding a `:root` block on a page with both body variables, a `MutationObserver` on
  `documentElement` (subtree, child list and attributes) records nothing while (a) a request holding a `bootstrap5-body`
  role and an invalid selector, and (b) an oversized (`size-limit`) request holding a `bootstrap5-body` role, are each
  refused; the same requests with plain roles are the control. RED at BASE (two records each). And with a plain preview,
  and again with a `bootstrap5-body` preview that sets no family (no `:root` block: this kills the `fontFamily` half of
  `rolesHaveRootBlock`, which survived R2.W2B2's tests), a valid `bootstrap5-body` Apply records no transition-ban
  `<style>` (EFF3; RED at BASE). Mutants: the evidence read moved
  back before validation; the size check moved after it; the read always suspending.
- Tokens: on a page with both body variables and no `--bs-font-monospace`, after Apply of a `bootstrap5-body` and a
  `bootstrap5-mono` role with families, a new hello's `ready.tokens.css` holds the page's own body-variable values (read
  before Apply: the oracle) and no `--bs-font-monospace`; and after that re-hello the owned node's text is unchanged, the
  preview's family still computes, and no `transition: none` style remains. RED at BASE. Mutants: values read with the
  preview on; the restore skipped.
- Selector check (EFF1): the existing selector-check tests and R2.W2T's 1,024-signature test pass unchanged; record the
  timings. Mutant: the Map keyed by something coarser (for example the family alone) fails a selector-check test.

Routed elsewhere: `test_role_adapters.py` 434 (`test_without_the_stylesheet_constructor_the_rule_count_is_the_block_count`)
names a fallback that no longer exists; R2.W2P renames it (it owns that file next). Do not edit it.

Mutants run in the foreground, in your worktree or through `RoleSheetCase.open(..., bridge_source=...)`; restore byte-exact
and record SHA-256 before and after. Expected values never come from the bridge's own output. A failing green is worse than
a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_role_stylesheet test_role_adapters test_role_protocol test_role_preview test_role_detection test_bridge_runtime.HandshakeTests test_r2_integration.StudioRoleBridgeTests.test_studios_family_field_agrees_with_the_bridge_on_every_row test_support`
(the last proves Studio and the new bridge still agree on every existing family row). Also `node --check fontkit-bridge.js`,
`python -m ruff check` on changed Python files, and after staging by name `git diff --cached --check`.

## Report and handoff

Report: each requirement with its RED and oracle; each mutant (command, failing tests and lines, SHA-256 before and after);
the precedence note of requirement 3; the focused run (Ran line, OK, GATE line); gross and material lines. Patch:
`task-w2b1-code.patch` holds only your changes on top of the two PATCH_DEPs (stage the PATCH_DEP state first, for example
`git apply --index` both, then write the patch with `git diff --binary` after `git add -N` for any new file; check it with
`git apply --check -R`), and record the PATCH_DEP SHA-256s it was built on. Commit subject
`fix(bridge): refuse unsafe role families and count the installed rules`, a draft body (why, wrapped at 72, no process
narration), a draft CHANGELOG sentence in product terms (families refused, a sheet the parser cuts short is refused,
`design:ready` reports the page's own tokens, faster Apply and known-role checks on large pages) and the R2.W2B1 plan item.
