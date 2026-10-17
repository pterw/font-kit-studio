# R2.4 code report (mode: code, worktree C:/fks/t4, BASE f2b438f)

Patch: `.superpowers/sdd/r2/task-4-code.patch` (`git apply --check -R` passes). Staged by name in the worktree, not committed.
Files: `fontkit-bridge.js` (+113/-21 net of CRLF), new `tests/test_role_adapters.py` (450 lines, 23 tests), `tests/test_role_protocol.py`
(`RoleContractTableTests`: +2 tests, one assertion), `tests/test_role_stylesheet.py` (rename + docstring + row label only).
Material lines: 597 added, 26 removed, 4 files (`git diff --cached --shortstat -B -M f2b438f -- . ':(exclude)*.md'`); budget about 1,200, under it.

## Brief steps
- Rule 1 (adapter on every group): `adapter: 'plain'` in the group literal in `collectRoleStyles`, overwritten by `suggestBootstrapAdapters`. Done.
- Rule 2 (evidence): `bootstrapVariables()` (new method) read at the top of `collectRoleStyles` with `styleSignature(document.body)`;
  at Apply in `handleRoleMutation` only when a role is non-plain, inside `suspendRoleSheet()` / `finally { restore(); releaseRoleQuiet(); }`. Done.
- Rules 3-4 (bindings, suggestions, names): heading step inside `roleBindings` (new `evidence` argument; it now returns `{title, heading}`);
  new `headingClaim`, `suggestBootstrapAdapters`, `BOOTSTRAP_NAMES`. Done.
- Rule 5 (serialization): `serializeRoleCss` replaced by `roleCssBlocks` (`ROLE_VARIABLES`); `canonicalizeRoles` keeps `role.adapter`; both
  `verifyRoleSheet` callers pass the block count (job gets `blocks`). Done.
- Rule 6 (Apply check): `canonicalizeRoles(roles, evidence)` + `bootstrapHeadingSelectors`. Done. Comment at the old line 168 updated.
- R2.3 conversions in `test_role_stylesheet.py`: test renamed `test_a_bootstrap5_adapter_is_rejected_where_the_page_has_no_bootstrap5_evidence`,
  docstring updated, row renamed `adapter-bootstrap-without-evidence` (expectation unchanged). Done.
- Shared-file steps (log, plan boxes, CHANGELOG): deferred to landing (Handoff).

## Evidence
RED = new tests against the BASE bridge (worktree file swapped for `git show f2b438f:fontkit-bridge.js` by `mutate-4.py base`, restored in
`finally`). Log: scratchpad `probe-4.log`. 25 of the 26 new/extended tests fail at BASE (KeyError 'adapter', 'design:rejected' !=
'design:roles-applied', names 'Text' != 'Heading 1', adapters set difference). One is a true GREEN characterization at BASE and is reported as
such, not as a red: `test_bootstrap5_adapters_are_rejected_on_bootstrap4_and_write_nothing` (BASE rejects every bootstrap5 adapter; its mutant
below fails it).
GREEN: `python -m unittest test_role_adapters` -> Ran 23 tests OK; then the brief's focused gate (below).

Mutants (one per test; `mutate-4.py mutants`; each ran `python -m unittest <test id>`; fontkit-bridge.js SHA-256 before AND after every
run: 66813402832462281659232a6c84e658ff2dc32e570e1c866a905bdff7b4a0b0, restored=True). Failing line, abridged:
- fixture suggestions/names: heading step before author ids (`if (!evidence && ids.every...`) -> `{(40,500): 'bootstrap5-heading', ...} != {(16,400): 'bootstrap5-body'}`
- remaining-class names: swap `btn`/`nav-link` names -> `'btn': ('Navigation link', ...)`
- id-less headings: drop the `.display-N` candidate -> `(['.display-1'], {'class'}, {True}, 'plain') != (... 'bootstrap5-heading')`
- fs-6 fallback: drop the member check and the coverage check of `choose()` -> `[('h2',...), ('.h2',...)], 'bootstrap5-heading') != ([('.h2', 'class', True)], 'plain')`
  (dropping only the member line passes, because the coverage line also rejects `h2`; both guards are pinned by the pair)
- heading apply: echo `adapter: 'plain'` -> receipt roles differ (`'plain'` != `'bootstrap5-heading'`)
- mono variant: raw-string family compare -> StopIteration (no group named Monospace)
- BS4 plain: `evidence = true` -> adapter set != {'plain'}; BS4 reject: skip the Apply check -> `('design:roles-applied', None, None) != ('design:rejected', 'unsupported-value', 'Unsupported adapter')`
- both variables: `body || sans` -> adapters differ (2 subtests); non-Bootstrap page: evidence also needs a bootstrap `<link>` -> `('plain','Text') != ('bootstrap5-body','Body')`
- ties: `bodies.length >= 1` -> `{'Role': 'bootstrap5-body', 'Auto': 'plain'} != {'Role': 'plain', 'Auto': 'plain'}`
- template cases: body variables in swapped order -> canonical CSS differs; detected group: blocks reversed -> `[data-design-id=...` != `:root {...`
- clear and inline-style: variables also written inline -> clear test fails (`design:rejected` != `design:roles-applied`); inline test `{'--bs-body-font-family': 'Inter'...} != {... 'Serif-Inline' ...}`
- var() loss: `fontSize` accepts a non-px declared value as the computed size -> losses become `author-rule` with a named selector (count 3 entry), not one `complex-cascade`
- 128 KiB: size check ignores the `:root` block -> `('design:roles-applied', None) != ('design:rejected', 'size-limit')`
- fallback: count roles not blocks -> `'design:rejected' != 'design:roles-applied'` (stylesheet-blocked)
- stale adapter and evidence-from-the-app: skip Apply check / read without suspending the sheet -> applied instead of rejected
- heading selectors: drop `bootstrapHeadingSelectors` -> applied instead of rejected; no-leak: drop `releaseRoleQuiet()` -> `1 != 0`
- live-preview Detect: no `suspendRoleSheet` in `run` -> groups show Inter/18 instead of sans-serif/16
- RoleContractTableTests: omit `adapter` from the group literal -> group-limit and variant-limit tests fail; skip `suggestBootstrapAdapters` -> BS5 test `{'plain'}` has no non-plain value.

## Gates (worktree, final tree)
`sh .../gate.sh focused test_role_adapters test_role_detection test_role_stylesheet test_role_preview test_role_protocol test_r2_react
test_r2_static_fixtures test_support` -> `Ran 172 tests in 200.954s` / `OK` / `GATE focused EXIT 0 IN 202s` (log: scratchpad `focused-4.log`).
`node --check fontkit-bridge.js` ok; `python -m ruff check` on the three test files: All checks passed;
`git diff --cached --check`: clean (LF-to-CRLF warning for the new file only); `python -m pre_commit run --files ...`: 4 hooks Passed.
Studio modules not run (as briefed). Mutant runs left no server or context open.

## Deviations / decisions
- Template `mixed` case: the brief says "the others: neither" variable changes; `mixed` holds a body and a mono role, so the test expects
  all three variables to change (literal values in `CASE_VARIABLES`). Rule: the case's own roles.
- A group counts as a body or mono "qualifier" on its signature alone, before precedence (so a heading group equal to body still blocks a
  second body qualifier). The brief leaves this open; the ties test pins the unambiguous cases only.
- Heading level claims: a tag/class level conflict, two `.hN` classes, or a `.hN` plus `.display-N` gives no heading claim (brief rule 3 + M-6).
- Group name for heading/display groups comes from the claim, set before the author-role and author-id steps, so id-bound heading groups are named.
- The var() and 128 KiB tests run on the four id selectors / long selectors directly (a detected body group would stop qualifying once the
  author rule changes its size).

## Handoff
Commit subject: `feat(bridge): suggest and apply Bootstrap 5 font roles` (lands with R2.S3; may change).
Draft body: Bootstrap 5 pages now get Bootstrap's own roles. The scan reads the computed body and mono variables from the app's CSS with
the preview off, suggests heading, body and mono adapters and names for Bootstrap classes, and echoes the adapter on every group, also in
limit replies. A body or mono role with a family writes its :root variable block before the plain block; Apply re-checks the evidence
and the heading selectors and rejects a stale adapter as unsupported. R2.S3 shows the adapter and re-sends it.
Plan: R2.4 items done (all). CHANGELOG wording is drafted by R2.S3; the bridge comment was updated. Log entry: R2.4 bridge adapters, 4 files.
Bridge functions changed (line ranges at this patch, for PATCH_DEP S3 / 7F2b):
- new const `ROLE_VARIABLES` 175-177, `BOOTSTRAP_NAMES` 178-180; new `bootstrapHeadingSelectors` 240-244
- `canonicalizeRoles(roles, evidence)` 248-270 (adapter check moved after the selector dedupe; output keeps `role.adapter`)
- `serializeRoleCss` removed; new `roleCssBlocks` 289-300; new `headingClaim` 304-311
- new method `bootstrapVariables` 1275-1279; `handleRoleMutation` 1389-1437 (evidence read, blocks, `blocks` on the job)
- `attributeLoss` 1636-1710 (passes `job.blocks`); `roleBindings(group, elements, query, evidence)` 1782-1828 (returns `{title, heading}`)
- new method `suggestBootstrapAdapters` 1832-1847; `collectRoleStyles` 1936-2031 (evidence read at the top, `adapter: 'plain'` in the literal, facts map, suggestion call)
- the one-line comment above `ROLE_PROPERTY_KEYS` (line 168) now reads "Bootstrap 5 adapters need page evidence (D068/D069)".
Bridge SHA-256 in the patch: 66813402832462281659232a6c84e658ff2dc32e570e1c866a905bdff7b4a0b0 (BASE: 18e40cb69ae4... as LF blob).
Note: the working-tree bridge keeps CRLF (autocrlf); the patch is LF.


## Fix round 1

Base of the round: patch SHA-256 767311d3...c866e verified. fontkit-bridge.js SHA-256 before: 66813402...a0b0; after: a7e81ca1fd057f391b41d019ab63d015d2491b7c9c87f56cd632196a7e189a5f (CHANGED, one hunk in `collectRoleBinding`'s heading step).
New patch: `task-4-code-r1.patch` (SHA-256 4c39e12c...4ac1), `git apply --check -R` passes. Whole patch: 668 added / 26 removed over 4 files (bridge 115/21, test_role_adapters 519/0, test_role_protocol 30/1, test_role_stylesheet 4/4).

- Important 1: new `HeadingClaimTests` with three tests: `<h2 class="h4">` alone (Text, plain, `.h4`); `<p class="display-2 h3">` beside a `span.h3` (Heading 3, plain, `.display-2`); `<p class="display-1 display-2">` (Text, plain, `.display-1`). They use the protocol page plus both variables, so the page is otherwise free of headings. Mutants killed: M13 (`levels.size >= 1`), M14 (`!marks.length` dropped), M15 (`shown.length >= 1`).
- Minor 1: `test_a_group_equal_to_the_body_style_that_shares_it_with_a_heading_group_gets_no_body_suggestion`; M18 (bodies counted after heading and mono) killed.
- Minor 2: the bridge WAS wrong against the ruling: the display class was never tried once a level existed. RED first: `test_the_display_class_is_tried_when_the_heading_tag_matches_a_non_member` failed with `('Heading 1','plain',[('.display-1',...)]) != ('Heading 1','bootstrap5-heading',...)`. Fix: the heading step tries the level candidates, then `.display-N`. GREEN afterwards. Branch 1 test: `test_the_heading_level_wins_over_a_display_class_when_the_tag_fits`. Mutants killed: no display fallback (branch 2 test), display tried first (both tests), display title first (both tests).
- Minor 3: the Thens of the fixture test (four body selectors) and the template-case test (body outcomes, Inter 18px, label) now state their assertions.
- Mutants run through `bridge_source` (scratchpad/4r1/mut4r1.py); the file was never edited for them; SHA-256 unchanged by them.
- Focused gate: `gate.sh focused ...` -> `Ran 178 tests ... OK`, `GATE focused EXIT 0`. `node --check` ok, `ruff check` passes, `git diff --cached --check` clean.

## Fix round 2

- Minor 2 done: the template-case docstring Then now reads "the receipt is complete, echoes the roles ...". Only change in the patch vs r1 (`task-4-code-r2.patch`, 857 lines, same 4 files, 668+/26-).
- Minor 1 NOT done: the mono half of the "Keep it literal" test cannot be written as the re-review describes. In `suggestBootstrapAdapters`, `monos` matches on the group's family names alone and `bodies` on the whole style. Any group equal to body's style when body's family is the mono family also qualifies as mono. So two groups sharing body's style are two monos, and neither takes mono (the two-monos tie), while bodies never get a chance. The draft test (body `font-family: monospace`, `<p>Auto</p>` beside `<p data-design-role="Intro">Role</p>`) failed on the real bridge with `{'Auto': 'plain', 'Role': 'plain'}`, not `Auto: bootstrap5-mono`. That is correct under the ruling's spirit but contradicts the premise "one takes mono".
- M18m (bodies exclude monos) is therefore an equivalent mutant: it only differs when a mono group is also body-equal, and then every other body-equal group is also mono, so `monos.length` is 2 and nothing changes. Direct run on the final tree: with the draft test present, M18m was killed only because the draft fails on the original too (meaningless). With the draft removed, the 29 tests pass on the original and M18m survives as an equivalent mutant. I removed the draft rather than weaken it.
- Focused: `cd C:/fks/t4/tests && FKS_REQUIRE_FIXTURES=1 python -m unittest test_role_adapters` -> Ran 29 tests OK.
- `git apply --check -R` on the new patch passes. fontkit-bridge.js SHA-256 before and after: a7e81ca1fd057f391b41d019ab63d015d2491b7c9c87f56cd632196a7e189a5f (unchanged).

## Controller integration

- Landed from `task-4-code-r2.patch` (SHA-256 `28513bdb...a568`) in one commit with R2.S3 (D068); no conflict.
- Review: Needs fixes (Important 1, three Minors). Fix round 1 added a test per rule-3 predicate and pinned two
  owner decisions (a body-style tie gives no body suggestion; a display heading binds its heading level first,
  then its display class); the bridge gained the display-class fallback the second decision needs, shown failing
  first. Fix round 2 corrected a docstring. Both scoped re-reviews are Approved. Accepted without change: the mono
  half of the tie decision has no observable case (its mutant is equivalent), and one mutant survives only on a
  page whose body font is the monospace font.
- The two owner decisions are recorded in plan Addendum 21.
- Landing gates, Windows, Chromium, `FKS_REQUIRE_FIXTURES=1`, with R2.4's, R2.S3's and R2.7F2b's patches on the
  integrated tree at `f2b438f`: the Studio modules, 194 tests in 257.343 s; the bridge role modules, 103 tests in
  160.264 s; the preview, protocol, React and integration modules, 74 tests in 118.011 s; all OK. Static and
  provenance, `node --check`, product-tree Ruff and whitespace pass; exact Ruff reports only the four preserved
  findings under `.agents/`.
- Material lines: 668 added, 26 removed (D065).
