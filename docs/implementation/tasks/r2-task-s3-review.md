# R2.S3 code review (task gate)

Patch `task-s3-code-r1.patch`, SHA-256 85645bd7...f08f, verified equal to `git diff --cached --binary f2b438f -- <3 files>`
in `C:/fks/ts3`. Frozen worktree untouched: `fontkit-studio.html` 9a5d9c11..., `fontkit-bridge.js` a7e81ca1..., patch hash
unchanged after my runs. Mutants and reruns ran in a copy under the scratchpad (`s3rv`).

### Spec Compliance
- PASS: Behaviour 1. `validDetectedGroup` lists `adapter` in the exact key list and requires `ROLE_ADAPTERS.includes(group.adapter)`
  (fontkit-studio.html:3811-3814); null, number, missing and `'bootstrap9'` are refused whole-reply (test fence, mutants below).
- PASS: Behaviour 2. `buildRoleRequest` sends `adapter:group.adapter` (:4124).
- PASS: Behaviour 3. One `<p>` via the existing `paragraph` helper (textContent), after the binding lines and before
  `Safe complete bindings unavailable.` (:4037), non-plain only, label from the Studio-owned `ROLE_ADAPTER_LABELS` keyed by the
  validated value. The three labels equal the brief's strings.
- PASS: Behaviour 4. `serializeRoleSheet` emits the `:root` block (body: two variables in the order body-font-family then
  font-sans-serif; mono: one) only when the role has `fontFamily`, then the unchanged plain block, per role in request order,
  never merged; heading and plain unchanged; comment updated (:3920-3935).
- PASS: Behaviour 5. No Studio change, no `Unsupported adapter` special case.
- PASS: Behaviour 6. `validRoleVariants(check.signatures, check.matchCount, 1024)` is the one-argument change (:4256).
- PASS: Behaviour 7. `validRoleOutcome` adds `ROLE_PROPS.every(prop => count <= 16)` and nothing else (:4368).
- PASS: Owned files. Only the three paths changed. `group()` gains `adapter='plain'` last; `canonical_css` learns the templates;
  the self-check covers all five cases (`canonical_css(case['roles']) == case['css']`); `MANY_MATCHES` literal gains
  `adapter: 'plain'`. Material lines 347 added / 16 removed against "about 500".
- PASS: Deviation recorded (item 7 below): the only other existing test touched is the 1 MiB one, forced by D071 as the
  controller ruled; the brief's own allowance covers the self-check and `MANY_MATCHES`.
- PASS: Fake peer bullets all present: four adapters render, refusal rows, request pass-through in order plus the receipt shown,
  adapter change between two Detects, five accepted snapshots, the body case as a receipt, the refused wrong-bytes snapshots
  (including the two with a `:root` block put before the literal) and the rejection characterization.
- PASS: Real-bridge bullets: Bootstrap 5 Detect/Apply/Clear and the Bootstrap 4 plus plain-target requests, served at the
  fixture URL with the bridge tag added; no page written under `fixtures/`.
- CANNOT VERIFY FROM DIFF: the Handoff commit-body text is a draft only; I judged the CHANGELOG line (checklist 8).

### Checklist

**1. Drift**
- `DetectedGroup.adapter`: four values, no null, required. `ROLE_ADAPTERS` (:3851) equals `role_contract.ADAPTERS` by reading
  both. Killed by `test_a_group_without_one_of_the_four_adapters_refuses_the_whole_reply` (missing, bootstrap9, null, 7) and the
  render test; mutants `enum-string` and `null-ok` fail it (reproduced).
- Pass-through: `StudioAdapterTests.test_apply_sends_each_selected_groups_adapter...` and the changed-between-Detects test; mutant
  `send-plain` fails 4 tests (reproduced).
- Bytes: Studio == `TEMPLATE_CASES` by `test_a_ready_snapshot_with_each_template_cases_literal_bytes...` (five cases accepted)
  and the body case as receipt. The bridge == `TEMPLATE_CASES` by R2.4's
  `test_role_adapters.ApplyTests.test_every_template_case_emits_its_exact_bytes...` (tests/test_role_adapters.py:326-335,
  all five cases, `canonical css and digest equal the case`). Read the bridge: `roleCssBlocks` (fontkit-bridge.js:288-300) and
  `ROLE_VARIABLES` (:175) have the same variable order, indentation and block order as Studio. The real-bridge body test
  (Studio accepts a receipt only on byte equality) passes against the final bridge. Mono, heading and mixed bytes are equal
  to the bridge only through `TEMPLATE_CASES` (transitive), not by a direct Studio-versus-bridge run.
- 1,024 accepted / 1,025 refused: `test_a_selector_check_of_1024_signatures_renders_and_one_more_is_refused`; mutants
  `limit-128` and `limit-1025` fail it (reproduced).
- 17 losses for one property refused: see Issues M1; mutants `losses-total-only` and `losses-le-17` fail it (reproduced), one
  per-property mutant survives.

**2. Mutants reproduced** (copy outside the repository, `fontkit-studio.html` SHA-256 9a5d9c11... before and after every
run, restored in finally). 19 mutants run by me:
swap body variables (5 errors), mono variable under the body name (snapshot test), `:root` without the family check
(2 errors), `:root` for heading (7 errors), enum weakened to string (bootstrap9 row), null accepted (null row), adapter
line on plain rows (render test FAIL), send `plain` (3 FAIL + 1 error), limit 128 (FAIL), limit 1025 (error), per-property
check removed (error), `<= 17` (error), per-property check on 5 of 6 properties via `slice(1)` (error), 1 MiB limit
+1 and -1 (both error in the 1 MiB test), real-bridge: send `plain` (BS5 test FAIL), always `bootstrap5-body`
(BS4/plain test FAIL in both subtests), no `:root` block (BS5 test FAIL). One mutant SURVIVED (below, M1). Not
reproduced: the `rejectRoleOp` mutants (clear preview, enqueue again), the missing-adapter-defaults-to-plain mutant and the
merge-two-root-blocks mutant; I rely on the report's logs for those.

**3. Fake versus real.** Real Studio against the real bridge across origins (target.test): Bootstrap 5 fixture, the one row
with an Adapter line, request role `bootstrap5-body`, four body-tuple elements render the typed family and size, both
`--bs-*` variables compute to the family, Studio accepts the bridge's real receipt (byte equality), preview starts with the
`:root` block, Clear restores variables, computed family/size and `main` outerHTML, preview empty. Bootstrap 4 fixture and
the plain role target send only `plain`. Asserted only against the fake peer: refusal of missing/bootstrap9/null/number
adapters, mono and heading and mixed and body-without-family bytes, wrong-bytes snapshot refusals, request order for a plain
plus body pair, adapter change between Detects, the rejection (`Unsupported adapter`, unreachable in the real flow, the
reasoning in the report matches M-1 of the brief review), the 1,024/1,025 signature check, the 16/17 loss check, the 1 MiB
receipt. The mono and heading adapters are never produced by the real bridge in any S3 test (R2.4's tests cover the
bridge side).

**4. Hidden skips.** None. No skip decorator, `skipTest` or `expectedFailure` in the diff. `test_r2_integration` runs in the
hosted Chromium `discover` step; the two real-bridge cases need only `fixtures/bootstrap4-static` and `bootstrap5-static`,
both tracked in git (no npm), so `FKS_REQUIRE_FIXTURES` does not turn them into skips. All new tests run under `per_engine`,
so they run on whichever engines `FKS_ENGINES` selects (Chromium on the blocking step).

**5. Tests.** Oracles are independent: `TEMPLATE_CASES` literals and hashes, `LEAD_BLOCK`/`BODY_ROOT` literals, the brief's
labels, `table.*` builders. `canonical_css` (template-aware) is used only to build receipts whose bytes are not asserted, and
it is pinned to all five literals by the self-check. Assertions are observable (row paragraphs, `#rolePreviewCss`, status
text, requests on the wire, computed styles). I compared each Then to its assertions: they match (the BS4/plain docstring
omits the `>= 2 roles` assertion, trivial). The report's claim that the GREEN-at-BASE split is unreachable is right: the
shared `group()` carries `adapter`, which BASE refuses, and each refusal test needs a Fence reply built from that same
`group()` that BASE also refuses, so the refusal rows time out at BASE like the RED rows; the tests that mix RED and GREEN
cases (accepted snapshots, wrong-bytes) cannot be split without a second code path. Accepting mutants as the evidence is
correct, and I reproduced the mutants for those rows. Fine.

**6. Code.** Validation (`validDetectedGroup`, `validRoleOutcome`), serialization (`serializeRoleSheet`, a pure function) and
rendering (one line in the row block) stay in separate functions; the request builder only copies the field. No second copy
of any logic inside Studio (`ROLE_ADAPTER_VARIABLES` and `ROLE_ADAPTER_LABELS` each have one reader). Studio +18/-8 against
"about 40". Inline `1024` and `16` match the file's style (`128 * 1024`, `10000`, `96`). Test-side nits in M2 and M4.

**7. The 1 MiB deviation.** `build()` now takes `PROPERTY_ORDER[n % 6]` for each padding loss; the test name, `limit =
table.REPLY_BYTES`, the `measure` loop, the sizes (limit+1, limit), the `assertEqual(measure(...), size)` and the final
waits are byte-identical to BASE. Chunks of 64 give at most 11 per property. Reproduced: the mutants "receipt limit
1 MiB + 1" and "1 MiB - 1" both fail this test (size=1048577 and size=1048576 subtests), so it still fails one byte past
the limit and still accepts exactly 1 MiB. Rule forcing it: D071 (Addendum 20, owner ruling) makes the old 64-losses-of-one-
property padding invalid. Acceptable.

**8. CHANGELOG replacement.** Proposed: "Detected groups carry the adapter the page suggests (plain, or one of three Bootstrap
5 adapters); Studio sends it back unchanged and accepts the Bootstrap 5 variable template in receipts and snapshots."
True at HEAD of the combined R2.4 + R2.S3 commit (grep: the only sibling claim is CHANGELOG.md:27-28, "Only the plain adapter is
accepted so far."; nothing else in the product files, README or docs says it). The text is about Studio and the bridge but
reads as protocol jargon ("receipts and snapshots") rather than what a user gets; see M5. The second draft line (the three
`Adapter: ...` labels) is exact.

### Checks run
- Patch equality and frozen worktree -> `git diff --cached --binary ... | sha256sum`, `git status`, `sha256sum` -> equal to
  85645bd7..., worktree files unchanged after my runs.
- Baseline of new tests in a copy -> `python -m unittest` of `StudioAdapterTests`, both contract tests and the 1 MiB test ->
  `Ran 11 tests`, OK.
- 19 mutants listed above -> `scratchpad/mutate-s3rv.py` (foreground, restore in finally, SHA before/after printed) -> all
  killed except `losses-skip-texttransform`.
- Real-bridge cases in the copy (baseline and three mutants) -> `test_r2_integration.StudioRoleBridgeTests` (2 tests) -> OK;
  mutants fail as listed.
- Bridge bytes -> read `roleCssBlocks`/`ROLE_VARIABLES` in fontkit-bridge.js and `ApplyTests` in `tests/test_role_adapters.py`.
- Duplicate helpers -> `git grep "def quiet"` at BASE: `StudioLegacyCase.quiet` (test_studio_roles.py:1398) is identical to
  the new `StudioAdapterTests.quiet`.
- Hosted skips -> `git ls-files fixtures/bootstrap*-static`, workflow lines 140-175, grep for skip -> none.
- Stale claims -> grep for "caps at 128|until R2.S3|plain adapter" -> `tests/role_contract.py:21` and CHANGELOG.md:27-28.

### Strengths
- Expected bytes are literals from `TEMPLATE_CASES`; refusals are built per case (plain bytes for body/mono/mixed, a foreign
  `:root` block for body-without-family and heading) and the accepted/refused pair kills the order, name and merge mutants.
- The refusal tests use a Fence reply, so a Studio that dropped only the bad group or accepted the whole reply fails.
- The Bootstrap 5 real-bridge case asserts computed fonts, computed variables, bridge-accepted bytes and an exact Clear round
  trip; the `has=` locator bug found in phase 2 was fixed in the test, not around it.
- The 1 MiB edit is minimal and the test still pins both sides of the limit.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- M1. `test_an_outcome_of_16_losses_for_each_property_renders_and_17_for_one_property_is_refused` builds the refused row as
  `table.losses(17)[:17]`, which is 17 losses of the first property (`fontFamily`) only (tests/test_studio_roles.py:2785). A
  per-property check that skips any other property still passes: mutant `ROLE_PROPS.filter(p => p !== "textTransform").every(...)`
  survives (reproduced, OK). Suggest one 17-loss row per property in `PROPERTY_ORDER` (a subTest each). The first-property mutant
  and the total-only mutant are killed.
- M2. `StudioAdapterTests.quiet` (test_studio_roles.py, added before `StudioContractTableTests`) is a verbatim second copy of
  `StudioLegacyCase.quiet`; subclass `StudioLegacyCase` or reuse it. `wait_css` and `wrong_bytes` each have one caller.
- M3. The four-adapter tests hard-code the strings instead of iterating `table.ADAPTERS` (the brief names `ADAPTERS` as an
  oracle); a fifth adapter added to the table would not turn a Studio test red.
- M4. The module now holds `ADAPTER_VARIABLES` and `ROOT_BLOCK` beside the same mapping and regex local to the existing
  self-check test (two copies in one file); acceptable as an independent oracle, but note it.
- M5. CHANGELOG draft: "receipts and snapshots" is protocol vocabulary. A product-terms line would say what the user sees, for
  example "Bootstrap 5 pages: the body, monospace and heading text styles are suggested with their adapter, shown on the row, and
  previewed with Bootstrap's own variables." The controller writes it.
- M6 (outside S3's files, for the controller). `tests/role_contract.py:21` still says "Studio caps at 128 until R2.S3"; false
  after this change. S3 may not edit that file (read-only in the brief).

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every behaviour item and bullet of the brief is built, the drift items hold against `TEMPLATE_CASES` and the
final bridge, the real-bridge cases run and kill their mutants, and I reproduced 18 of 19 mutants killed; the one survivor
(per-property check on a single property) is a narrow gap, Minor, with a cheap fix.

## Scoped re-review: fix round 1

### Spec Compliance
- PASS: M1. The refused row is one 17-loss outcome per property in table.PROPERTY_ORDER (tests/test_studio_roles.py:2764-2770), each built as the 17 entries of that property from table.losses(17); every row asserts table.violations == 1; each request gets a distinct size (24 + rows so far, :2775).
- PASS: M2. StudioAdapterTests subclasses StudioLegacyCase (:2285); its own quiet, wait_css and wrong_bytes are gone; quiet is called once (:2451) and resolves to StudioLegacyCase.quiet (300 ms, same as the removed copy). The inlined wait and the two dicts are the removed helpers' bodies verbatim.
- PASS: M3. The render test builds groups, expected paragraphs and the row count from table.ADAPTERS (:2301-2310). Judgement on the failure mode below (adequate; one optional Minor).
- PASS: M4. One ADAPTER_VARIABLES (:38) and one ROOT_BLOCK (:2274); the self-check test uses both (:2467-2472); the local `variables` and `root` are removed (grep shows no other copy of the mapping or the regex).
- PASS: fontkit-studio.html and tests/test_r2_integration.py are byte-identical between the patches (diff of the two patches starts at line 169, the first line of the test_studio_roles.py hunk header; everything above is the other two files). Only tests/test_studio_roles.py changed.
- PASS: the staged diff in C:/fks/ts3 hashes to 4ccc9fa5...a74, the stated patch hash. fontkit-studio.html there is still 9a5d9c11...
- PASS: Given/When/Then of the two changed tests matches their assertions. Refused-row test: Then "one violation, receipt refused, fence receipt renders, refused never does" = violations == 1, wait for 'matched 9,', assertNotIn 'matched 8,'. Render test: Then = the per-row paragraph lists and the row count. Bytes test and self-check docstrings unchanged and still true.

### Checks run
- M1 mutant reproduced -> copy of the frozen worktree (without .git/work) in the scratchpad (s3rr_copy), fontkit-studio.html patched there with `ROLE_PROPS.filter(p => p !== "<prop>").every(...)` for textTransform, fontSize, letterSpacing, run with FKS_ENGINES=chromium -> unmutated copy: OK; each mutant: ERROR at the matching subTest (row='17 for textTransform' / 'fontSize' / 'letterSpacing'), Page.wait_for_function Timeout 8000ms, FAILED (errors=1). The review's original surviving mutant (textTransform) is now killed. Copy file restored; frozen worktree html hash re-read, unchanged.
- Stale-text race on rows 2+ (a previous row's 'matched 9,' satisfying the wait early) -> the mutant runs above time out on the mutated row, so the outcomes text is cleared by each new Apply; the wait is not satisfied by stale text.
- M3 fifth adapter -> in the copy, ADAPTERS in tests/role_contract.py given 'bootstrap5-extra', ran StudioAdapterTests -> 8 tests, exactly one ERROR: the render test, TimeoutError at `self.detected(page, frame, groups)` (waiting for "Detected"), 30 s. The other seven pass.
- M2 inheritance risk (method overrides) -> ast listing of method names -> StudioAdapterTests shares no method name with StudioLegacyCase or StudioRoleCase (empty intersection), so nothing is shadowed; StudioLegacyCase adds only applied, legacy_in_flight, quiet, select_for_apply.
- Lint -> ruff check tests/test_studio_roles.py in the worktree -> All checks passed; git status shows no new files from it.
- Focused suite not rerun; the report's `Ran 122 tests OK` is not independently reproduced, but the two changed tests and the whole StudioAdapterTests class ran green in my copy.

### Strengths
- The M1 test now kills a per-property skip for any of the six properties, and each row has its own distinct request size, so no row can pass on a previous row's state.
- The render test and its expected values derive from the same table.ADAPTERS loop, so the row count and the paragraph list cannot drift apart.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- m1 (optional). A fifth adapter in table.ADAPTERS turns the render test red as a 30 s wait_for_function timeout in `detected` (tests/test_studio_roles.py:2303), not as an assertion. It is red in the right test, named for adapters, so I judge it clear enough; a one-line message or a `self.assertIn(adapter, ADAPTER_LINES)` before opening the page would make the cause (new adapter, Studio refuses it, ADAPTER_LINES lacks it) readable without a trace. The docstring (:2292) still says "each of the four adapters". Not blocking.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** M1-M4 are fixed as described; the textTransform mutant that survived before now fails (reproduced, plus two more properties), the other files are unchanged, and nothing new breaks. Only an optional readability polish remains.
