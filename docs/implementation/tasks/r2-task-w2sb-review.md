### Spec Compliance
- PASS: Req 1. `roleFamily` refuses a trimmed CSS-wide keyword in any case and `(`/`)` outside quotes, inside the existing one-pass quote loop (fontkit-studio.html:3884-3894 in the frozen tree); the existing wording "font family not valid (...)" is reused (4126, 4175) and Apply is gated on it.
- PASS: Req 1 help text. `ROLE_FIELD_HELP.fontFamily` (3847) names "not a CSS-wide keyword (inherit, initial, unset, revert, revert-layer)" and "parentheses only inside quotes"; the field test asserts both phrases on every refused table row (tests/test_studio_roles.py:773-775).
- PASS: Req 2. The field test appends every `FAMILIES_REFUSED` (not valid) and `FAMILIES_ACCEPTED` (valid) row read from the table (test_studio_roles.py:760-761), not copied.
- PASS: Req 3. Two rows in `hostile_receipts` (1067-1068), built by `refused_family` (1034-1036): `with_css` FIRST, role change last, css from `canonical_css` of the changed role, digest from `with_css`. Shared path confirmed: `validRoleProperties` -> `roleFamily(value) === value` (3908) is reached by receipts (3984), the 4382 reply path and ready snapshots (4440) via `validAcceptedRoles`.
- PASS: Req 4. The mirror is `names = ADAPTER_VARIABLES.get(role['adapter'])` / `if names and 'fontFamily' in role['properties']:`, the shape of the bridge's `roleCssBlocks` (fontkit-bridge.js 292-295). Output unchanged: StudioContractTableTests and the 3-test control run pass.
- PASS: Scope. Only `roleFamily` and its comments, `ROLE_FIELD_HELP.fontFamily`, and the three named test regions changed. Nothing in `StudioContractTableTests`; no boundary field change.
- NOTE: `FAMILIES_REFUSED[0]` and `[8]` are index-addressed (test_studio_roles.py:1067-1068). The index is correct today (`inherit`, `--x(`). See Minor.

### Checks run
- Drift, table rows -> node harness (scratchpad/w2sb-review-drift.js) that slices `ROLE_FAMILY_UNSAFE` + `roleFamily` out of Studio (frozen tree) and out of the bridge (a scratch worktree, W2B1 patch: `balancedQuotes`, `unquotedParenthesis`, `roleFamily`), with `CSS.supports`/`cssSupports` stubbed to true, so only the new rule is compared -> all 19 `FAMILIES_REFUSED` rows refused by both with supports=true (so every refused row, including the 4 CSS.supports ones, is refused by the rule itself), all 10 `FAMILIES_ACCEPTED` rows accepted by both, 0 mismatches.
- Drift, random -> same harness, 30,029 strings (seeded LCG; alphabet of keywords in 3 cases, `(`, `)`, both quotes, spaces, NBSP, EM SPACE, dotted/dotless I, long s, Kelvin sign, `url`/`var`, `!important`, comment markers, backslash, braces, control characters, long strings of 295-304 characters with a trailing `(`) -> Studio and bridge agree on accept/refuse AND on the returned trimmed string: 0 mismatches. Then w2sb-review-oracle.py compares Studio against `tests/role_contract.family_refused` plus empty/length/unsafe/balanced-quote conditions (the JS regex result is passed in so Python `re` differences cannot leak in): 30,000 strings, 8,082 oracle-accepted, 0 mismatches. Differences between `toLowerCase().includes` (Studio) and `/^...$/i` (bridge) were reasoned through for U+0130, U+017F and U+212A (none maps onto a keyword letter) and the random alphabet includes them.
- Mutants, run on a scratch copy (scratchpad/w2sb-review-wt, PYTHONDONTWRITEBYTECODE=1, chromium); sha256 of the changed file equal before and after each run; control run of the three target tests unmutated: OK. The frozen worktree was checked byte-identical at the end (`sha256sum -c`: both files OK; git status unchanged).
  - keyword check removed -> field test FAILED failures=8 (the 8 keyword rows).
  - paren check removed -> field test failures=7 (`--x(`, `--x(a)`, `--x()`, `Inter, --x(`, `if(media(all): Inter`, `"Inter", --x(a)`, `--x("a")`).
  - quote-blind paren check (`/[()]/.test(text)` added) -> field test failures=6: `'Inter (Display)'`, `"Inter (Display)"`, `"A)"`, `"Inter's (x)"`, `'say "hi" (x)'` plus the test-level failure. Only accepted near-misses kill it, as the brief says.
  - receipt path not calling `roleFamily` (3908 replaced by length + `ROLE_FAMILY_UNSAFE` + `CSS.supports`, so `a;b` stays refused) -> hostile receipt test errors=2: exactly 'family that is a CSS-wide keyword' and 'family that is a dashed function'. This also proves the rows' roles, css and digest agree: if the css or digest had disagreed, the receipt would still be refused under the mutant and the rows would stay green.
  - mirror without `'fontFamily' in` -> `test_template_cases_follow_the_addendum_rules_and_carry_their_own_digests` ERROR on case `body-without-family`.
  - mirror final LF dropped via `.rstrip()` -> same test, failures=5 (body, mono, body-without-family, heading, mixed).
  - BASE logic (both Studio checks removed, new help text and tests kept) -> 15 failures + 2 errors: 8 keyword + 7 dashed rows RED, both receipt rows ERROR; the 4 CSS.supports rows, `generic(kai)`, `Inter)`, `a), serif`, `Inter (Display)`, GREEN; all accepted rows GREEN. This matches the brief's 15 of 19. (At the true BASE the 4 CSS.supports rows would also fail on the help-text assertion, because the old help lacks the phrases; the report says so, and that red is legitimate because the help wording is a requirement.)
- `.rstrip()` substitute -> read `canonical_css` (test_studio_roles.py:43-58): every block ends with exactly one `\n` and nothing else trails, so `.rstrip()` removes exactly the final LF; mutation shows 5 cases failing. Equivalent; the deviation is recorded in the report. Judged acceptable.
- Hidden skips -> `git diff HEAD -- tests/test_studio_roles.py fontkit-studio.html` searched for skip/Skip: the only hit is the data string 'revision skips ahead'. None added.
- Whitespace -> `git diff --check` and `git diff --cached --check` rc 0.
- Sibling copies of the old rule -> grep of README.md, docs and the html for "balanced quotes"/"valid font stack": only the Studio comment and help (both updated); README near 572 is the controller's (brief says so). No other Studio copy of the keyword list: `revert-layer` appears once in the html (3884) and nowhere in test_studio_roles.py (read from the table).
- Process hygiene -> my runs were foreground and synchronous; no server or browser left by me (the chrome/node processes in tasklist are the user's, not headless_shell from my runs).

### Checklist
1. Drift: Studio equals bridge and `role_contract` on every table row and on 30,029 random strings; 0 mismatches (above).
2. Mutants: 6 of 6 reproduced, killed by the expected tests and rows; receipt-path mutant included; `.rstrip()` substitute is equivalent. Frozen tree untouched.
3. Fake versus real: the receipt rows and the field rows run against the fake-peer harness (PEER page, Studio's own validator). They prove Studio refuses the family; they do not prove the real bridge refuses it, nor Studio+real-bridge parity. That proof is R2.W2S-c's next slice (`test_r2_integration`, with the W2B1 bridge). The existing parity test `test_studios_family_field_agrees_with_the_bridge_on_every_row` runs here against the BASE bridge and only its old rows are in force.
4. Hidden skips: none added.
5. Tests: receipt roles/css/digest agree (shown by the receipt mutant); help text at 3847 names the refusals and the field test asserts both phrases; the Given/When/Then Thens match: the field test's Then ("Apply follows validity after every keystroke, names the row and field when it is disabled, and a refused table family gets help naming the keyword and parenthesis rules") is what it asserts. The two receipt rows live in a test whose docstring is unchanged and still true ("each hostile or inconsistent receipt ... changed nothing").
6. Code: no third copy (one keyword list in Studio, a deliberate cross-boundary copy under rule 10; the tests read the table); 28 gross lines (11 html, 21 tests net of context; `git diff --numstat` 7/4 and 16/5 on the delta) against about 100.

### Strengths
- The paren scan folds into the existing quote loop, so Studio has one scan, the same pass as the bridge's `unquotedParenthesis` and the table's `family_refused`.
- The receipt rows are true REDs that cannot pass for the wrong reason: css and digest are recomputed, and the receipt mutant proves it.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_roles.py:1067-1068 index the table (`FAMILIES_REFUSED[0]`, `[8]`). A reorder of the table would silently pick another case (still a refused family, so the row stays a valid refusal row, but the shape name "keyword"/"dashed function" could lie). Selecting by property (first with `family.lower() in table.FAMILY_KEYWORDS`, first with `'(' in family`) would be sturdier. Not blocking.
- fontkit-studio.html:3847: the help reads "... or url( expression( var( env( attr(, not a CSS-wide keyword (...)": a comma follows a token that ends in a parenthesis. Wording only; the test pins the two phrases, so it can be tidied without risk.
- fontkit-studio.html:3880-3882: the comment says "the bridge's ROLE_FAMILY_UNSAFE and family checks". True once W2B1 lands (checked in a scratch worktree); at BASE the bridge lacks the keyword and parenthesis checks. Landing order is the controller's; no change needed if W2B1 lands in the same wave.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The rule is identical to the bridge's and the contract table's on every table row and 30,000 random strings, every requested mutant fails exactly the tests it should (including the receipt path), and the change is 28 lines with no hidden skips. The only open items are Minor test-polish points, plus the real-bridge parity proof, which is R2.W2S-c's.
