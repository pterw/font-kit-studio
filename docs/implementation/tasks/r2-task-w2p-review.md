### Spec Compliance
- PASS: Req 1, Body binds the page. `suggestBootstrapAdapters` gives the one body-style group `bootstrap5-body` and `[{value:'body', stable:true, reason:'page'}]`, complete, set there and not in `choose`/`roleBindings` (fontkit-bridge.js, diff hunk "@@ -1848,22 +1861,32"). Body test asserts the literal receipt `{id:'detected', matched 1, checked 0, mismatched 0, complete True, losses []}`, a CSS literal (BODY_CSS), and computed-before reads plus literals (40 `<p>` start at 16px, `.btn` keeps `16px`), and Clear equals the pre-Apply snapshot (tests/test_role_adapters.py, `test_a_detected_body_group_binds_the_page_...`). The own-text page gives `checked 1`.
- PASS: Req 2, author roles. The list is filtered by `!group.authorRole`, so such groups get no adapter in either branch and do not count; names are kept because they never enter the naming loop. The heading branch is covered by a heading-shaped author group.
- PASS: Req 3, mono fallback. `code, kbd, pre, samp` in that order, `reason page`, `stable true`, complete, only when the group has no complete binding. The `.snippet` group keeps its binding. With a `span.font-monospace` the group has 41 elements and the receipt matches 40.
- PASS: Req 4, placement. The pre-pass runs before the selector loop and before the evidence read. It refuses with `unsupported-value` / `Unsupported adapter` on more than one body or mono role, and on a body role whose de-duplicated selectors are not exactly `["body"]` (`BODY` refused, `["body","body"]` accepted and echoed as `["body"]`). `body` stays `Unsupported selector` in plain and mono roles, and the memoized map is never seeded with `body`.
- PASS: Req 5, known Body role. `soleBody` (exact lowercase, one selector) is applied at all three Detect sites (sync check, cooperative check, post-scan root-match rejection). `roleSelector` is untouched. The fixture gives matchCount 0 and no signatures; with own text it gives 1, one signature of count 1, 16px, weight 400. `['body','.btn']` and `['html']` are still refused.
- PASS: Owned files and scope. Only `fontkit-bridge.js` and the three owned test files changed. No `roleSelector` change and no new test files.
- PASS: Drift with W2PT's table (tests/role_contract.py:44-45, 213-216, 248-257) and W2PS (tw2ps `fontkit-studio.html`). All three agree on these rules:
  - body is exactly `[{body, page, stable}]`, complete;
  - mono is its own complete binding or exactly the four tags in order;
  - one body and one mono role or group;
  - `body` only as a body role's sole selector; a Studio request never has duplicates, and only the bridge de-duplicates;
  - exact lowercase;
  - Studio's selector-check validator (`validRoleSelector(check.selector, true)`) accepts `body` for any known role, and the bridge only for a sole `body`. That is a superset on the Studio side only, so there is no reply the bridge sends that Studio drops.
- PASS: SIMPLIFY2/5 behaviour unchanged. `choose([])` returns false before any `yield` or write, so the two-list heading loop equals the old short-circuit `||`. `sole(test)` equals the old `monos`/`bodies` length-1 filters.
- PASS: Hidden skips. The only skip in the diff is the install-count test's `skipTest(...)` with a reason (test_role_stylesheet.py:1336). Nothing else was skipped, and `test_role_stylesheet` ran 51 tests with no skips on Chromium.
- PASS: Budget. 262 added and 82 removed is 344 gross, under about 400.
- PASS: Fake versus real. These are real-bridge tests in the role harness page `host-roles.html`, which is not `fontkit-studio.html`. The real-Studio, real-bridge proof (including Studio accepting the `page` binding, and its receipt line) belongs to R2.W2PI. Studio's rules were compared by reading the W2PS diff only.

### Checks run
- Frozen state -> sha256 of the bridge and the three test files before and after all my runs -> identical. Nothing was written in `a scratch worktree`.
- Control -> `w2p-review-run.py none` (scratch runner, patches `RoleBridgeCase.open` to serve a mutated bridge through `bridge_source=`) -> `test_role_adapters` Ran 45 OK; `test_role_stylesheet` Ran 51 OK; the detection literal-identities test OK.
- Mutants through `bridge_source`, module `test_role_adapters` unless noted:
  - page binding replaced by old steps -> 5 fail: body, own-text, tooltip, author, fixture suggestion.
  - author groups take adapters, body branch (author groups counted, name skip kept) -> author test fails on both the fixture and the heading-shaped subtest.
  - author groups take adapters, heading branch ONLY (sole computation still filtered) -> only the `heading-shaped` subtest fails (got `bootstrap5-heading`). The branch is pinned independently.
  - count rule removed -> placement rows `two body roles`, `two mono roles` fail, and later rows cascade.
  - `["body"]` rule removed -> 9 rows fail.
  - case sensitivity removed -> `BODY` row fails (the rows after it cascade).
  - de-duplication removed -> placement test errors (the `["body","body"]` acceptance).
  - mono fallback removed -> 2 subtests fail. Fallback always overriding a complete binding -> the `.snippet` subtest fails. Wrong tag order -> 2 fail.
  - body binding reported incomplete -> body test and fixture suggestion test fail.
  - known-role exception removed, one of the three sites at a time (sync, cooperative, root-match) -> each makes the known-Body test error, in both subtests.
  - `soleBody` loosened to `includes('body')` -> the `['body','.btn']` row fails.
  - `checked.set('body', true)` exemption -> only the `body role + plain role both on body` row fails (the control the review asked for).
  - evidence check removed, modules `test_role_adapters,test_role_stylesheet` (Ran 96) -> all six edited evidence tests fail: the no-evidence loop, the `adapter-bootstrap-without-evidence` row, BS4, body-only variables, apply-needs-both and the stale adapter. They would not fail through the placement rule, so the `['body']` moves are the right ones. The Atomic table also cascades.
  - SURVIVOR: `soleBody` with `.toLowerCase()` (known role `['BODY']` made valid in Detect) -> no test fails. See Minor 1.
- Tie concern -> read `collectRoleStyles` (bridge 2016-2024 at the worktree) -> style groups are keyed by `{kind:'style', style}` and so have exactly one signature; author-role groups are excluded from `list`. At most one group can equal `bodyStyle`. No tie path remains for body, and none is reachable through a heading or mono group either, since the tie was a count of groups equal to body. The mono tie (`sole`) is real and still tested (`two monospace groups`).
- Existing-test changes -> read each hunk (below).

### Existing tests changed (judged)
- `test_role_adapters`: fixture suggestion, template case, detected-Body, inline-root, declared-sizes, 128 KiB and the renamed constructor test follow the page binding or the placement rule. Each now asserts literals. The template case's label flips from `sans-serif` to `Inter/18px`, forced by body inheritance and stated in the docstring.
- Declared-sizes: moved to a plain role. The test proves a lost size is one complex-cascade entry, and that is adapter-independent. Still proves its name.
- Constructor test: renamed to say "rule count equals block count"; it expects `[(1,0),(2,2)]` for the three-block sheet and the loss on the plain role. Sound.
- Ties scenario 1 removed: confirmed impossible (above), and the docstring says so. The author test covers the old author-vs-style interaction.
- BS4, body-only-variables and the apply-evidence tests, plus `test_role_stylesheet` 181 and the 306 row: body moved to `['body']`. Verified by the evidence-check mutant that they still fail without the evidence rule.
- `UnsafeFamilyTests`, `wide_roles`, ValidateBefore and transition-ban tests: the body role is moved to `['body']` and the fault each names is unchanged. The oversized request stays over 128 KiB (three plain roles).
- Tokens test: the final read is `body` (`[data-design-id="role.body"]` sets its own family). Still proves "a root preview stays installed". Not weakened.
- Large-page Detect test (`.g00` -> `body` and `#corpus`): forced, since `.g00` keeps its own serif. `readWithoutRootPreview` suspends the whole sheet, so a sample of `body` still catches a dropped preview. Small loss: `#corpus` no longer isolates the variable path (see Minor 3). Not a weakening of the test's name.
- `test_role_detection` Body expectation: now asserts the exact page binding, then skips the id comparison for that group only.

### Strengths
- Each new rule has a test whose mutant dies, including the awkward ones: the memoized-`checked` exemption, the heading branch alone, and the case/dedup rows. The placement rows run on an evidence-present page and check reason, detail, owned text, revision and a computed read.
- The body oracle is a literal pair (`.btn` keeps `16px`) plus computed-before reads. It is not derived from the bridge's output.
- Bridge, table and Studio agree rule for rule. The Body suggestion cannot disagree with the placement rule, since both are exactly `["body"]`.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. A known role on `['BODY']` is not tested in Detect (and `['body','body']` is refused there). A `soleBody` that lowercased would pass every test. Studio rejects `BODY`, so a skewed bridge would send a reply Studio drops. Add one hostile row to the known-role test. (tests/test_role_adapters.py, `test_detect_accepts_a_known_role_on_body_alone...`)
2. Comment says "Addendum 23 item 3" for the placement pre-pass; placement is item 4 (item 3 is the mono fallback). (fontkit-bridge.js:266, `canonicalizeRoles` comment)
3. `test_detect_under_a_body_variable_preview...` now samples `body` and `#corpus`; both get Georgia from the owned `body{}` rule, so `#corpus` is no longer a variable-only witness. An element with `font-family: var(--bs-body-font-family)` would keep it. Optional.
4. `skipTest` sits inside the `for engine in ENGINES` loop, so with `FKS_ENGINES=firefox,chromium` it skips before chromium runs. It matches the brief's wording; a per-engine skip inside `subTest` would be exact.
5. The mono fallback "even where some of the four tags belong to other groups" has no test beyond the `span.font-monospace` over-claim case.

### Plan-mandated (for the owner)
- [Minor] The Body row's members include `.btn`, so a size set on Body never reaches them (family does), and an author `body{}` rule of equal specificity placed later outranks it with no receipt signal. Concerns 2 and 3 in the report; they belong in the release-point docs and in R2.W2PI requirement 1 (its oracle still says every body-style element computes the size). Not a defect in this task's code.

### Assessment
**Task quality:** Approved
**Reasoning:** The bridge matches Addendum 23 items 1-4, the table and W2PS rule for rule. Every mutant I tried is killed by a real-bridge test, except one lowercasing of the known-role exception, which is Minor. The changed existing tests are forced by the rules and keep their names' meaning. Addendum 21's body tie is unreachable, and the mono tie remains and is tested.
