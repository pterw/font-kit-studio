# R2.W2B2 code report

## Phase 1

Mode code, worktree `a scratch worktree` (HEAD = BASE 73b3ba2, detached). Patch: `.superpowers/sdd/r2/task-w2b2-code.patch`
(`git apply --check -R` passes). Files: `fontkit-bridge.js` (+23/-9), `tests/test_role_adapters.py` (+47/-5),
`tests/test_role_stylesheet.py` (+43). Gross 113 added / 14 removed, under the 220 budget. Worktree files are CRLF
(autocrlf), the index is LF; the patch is LF.

### Brief steps
1. Display class first: done. Heading step tries `.display-N` first, then `hN`/`.hN`; comment rewritten.
   - Changed test (intended behaviour change, existing test edited): `..._heading_level_wins_over_a_display_class_when_the_tag_fits`
     is now `test_the_display_class_wins_over_the_heading_level_when_the_class_fits` (binds `.display-1`, still Heading 1,
     `bootstrap5-heading`).
   - Renamed `..._display_class_is_tried_when_the_heading_tag_matches_a_non_member` to
     `test_the_display_class_is_tried_first_when_the_heading_tag_matches_a_non_member`, docstring says it covers the first leg.
   - New fallback test (characterization, green at BASE and after): `test_the_heading_level_is_tried_when_the_display_class_matches_a_non_member`.
   - New `DisplayHeadingApplyTests.test_applying_a_detected_display_group_renders_its_size_and_weight_over_bootstraps_display_rule`
     (vendored Bootstrap 5 linked before hello, two `h1.display-1`, detected group applied as received).
2. Names from every shared class: done. `roleBindings` result carries `classes` (the full shared list, set after the loop);
   `suggestBootstrapAdapters` reads `facts.get(group).classes`. No wire change. Test:
   `test_a_shared_class_past_the_sixteenth_still_names_the_group`.
3. Batch rule: done. `rolesHaveRootBlock(roles)` sits beside `roleCssBlocks`. `run()` computes `rooted` once per Detect;
   only when true it does one `documentElement.getBoundingClientRect()` after `suspendRoleSheet()`, sets
   `reading = max(8, 2 x elapsed)`, and restarts the batch clock after the read. Otherwise the code path is BASE's (8 ms).
   Test: `BaselineDetectTests.test_detect_under_a_body_variable_preview_finishes_and_never_drops_the_preview` (constants
   inside the test; the module header is untouched).
4. Comment slips: done (`FIXTURE_GROUPS` comment says names; bridge comment now "after the evidence read").
   `LINK_BOOTSTRAP5` and `BOOTSTRAP5_CSS` constants were added at the top of test_role_adapters.py (phase 2 owns that file).

### RED at BASE (BASE bridge swapped in by `work/mutate-w2b2.py base`, restored after)
```
FAIL ..._shared_class_past_the_sixteenth_still_names_the_group: ('Text','plain') != ('Button','plain')
FAIL ..._display_class_wins_over_the_heading_level_when_the_class_fits: [('h1','class',True)] != [('.display-1','class',True)]
FAIL ..._applying_a_detected_display_group_...: [(2, 2, [fontSize complex-cascade ...])] != [(2, 0, [])]
FAIL ..._detect_under_a_body_variable_preview...: BODY_PREVIEW_DETECT complete false, time-budget, scanned 309, 2028 ms
```
The fallback test passes at BASE (characterization, not RED).

### Mutants (each run: `python work/mutate-w2b2.py <name>`; bridge SHA-256 before = after = `9b2f9592fc4d317c44ed689ad938666a42eba24171a81352324df009868170c9`)
| mutant | failing test | result |
|---|---|---|
| display-first reverted | display_class_wins..., applying_a_detected_display_group... | 2 FAIL |
| level fallback removed (`display ? choose([.display]) : levels.length && choose(levels)`) | heading_level_is_tried_when_the_display_class_matches_a_non_member (plain, dom-path) | 1 FAIL |
| lookup back on `group.sharedClasses` | shared_class_past_the_sixteenth... ('Text') | 1 FAIL |
| batch rule disabled (`if (false && rooted)`) | detect_under_a_body_variable_preview (time-budget, 372 scanned, 2012 ms) | 1 FAIL |
| restore skipped after a long batch (`finally { if (reading === 8) restore(); }`) | same test: sampled frames show the dropped family pair | 1 FAIL |
| batch rule always on (`rooted = true`) | none: BaselineDetectTests, SuggestionTests, ApplyTests 21 tests OK | accepted survivor (timing only for plain and absent previews) |

### Detect test timings (new test, Windows Chromium, `BODY_PREVIEW_DETECT`)
Solo x3: 522.5 / 425.9 / 444.4 ms, complete, 5,000 scanned, 12 / 11 / 11 frames, heartbeat +12 / +11 / +10.
Beside `test_role_detection` (another Chromium): 476.4 ms, 10 frames. In the final focused run: 439.3 ms. BASE: time-budget
after 309 scanned (2,028 ms). No reliability problem seen; nothing weakened or retimed.

### Focused gate and checks
`gate.sh focused test_role_adapters test_role_stylesheet test_role_detection test_role_preview test_support`:
`Ran 150 tests in 158.488s`, `OK`, `GATE focused EXIT 0 IN 159s`. node --check ok; ruff on the two test files passed;
`git diff --cached --check` ok; pre-commit hooks (whitespace, ruff, node syntax, static checks) Passed.

**Disclosure (red reported as red):** the first full focused run (442 s, run while the machine was also running my other
work) failed once: the existing `test_detect_never_drops_the_preview_between_frames_on_the_5000_parent_corpus` (plain
preview, `rooted` false so this path is BASE's) ended `time-budget`. Run alone three times it passed (863, 995, 877 ms) and in
the final focused run 799 ms. This is the marginal test the brief and review already name (1,008-1,982 ms observed); I did not
change it.

### Known limit (ALT3, not fixed)
A level-only heading group still binds its type selector (`hN`, `.hN`), which can lose to the app's own single-class rule;
display-first fixes only `.display-N`.

### Self-review
Each new test fails under its mutant (table). `Then` clauses match assertions. No new helper path, no shared files edited.
One small cost: `rolesHaveRootBlock` repeats `roleCssBlocks`' `ROLE_VARIABLES && 'fontFamily' in properties` condition
(two copies, same side, within the rule).

### Handoff
- Commit subject: `fix(bridge): bind display headings by class and keep Detect fast`
- Draft body (wrap 72): "A display heading previewed only its family, because its tag lost font-size and weight to
  Bootstrap's .display-N rule; it now binds the display class first and falls back to its level. A Body or Monospace
  preview wrote a :root block that restyled the page on every Detect batch, so a re-Detect read 3-4 elements per batch and
  timed out; batches now measure that cost and read for twice it. Bootstrap names were looked up in the 16 classes the reply
  carries; they now use every shared class."
- CHANGELOG (Unreleased): "Display headings now preview their size and weight; re-detecting under a Body or Monospace
  preview finishes on large Bootstrap pages; Bootstrap names are found past 16 shared classes."
- Plan item: tick R2.W2B2 phase 1; phase 2 (tests) is still open.
- Scratch: `work/mutate-w2b2.py`, `work/probe-w2b2-*.log` in the git-ignored worktree work/ folder.

## Phase 2: tests that kill the review's mutants (tests only, `tests/test_role_adapters.py`)

Mode code, worktree `a scratch worktree`. Only `tests/test_role_adapters.py` changed in phase 2 (about +125 / -5 lines, under the 320
budget); the bridge SHA-256 is `9b2f9592...8170c9` before and after every mutant run (runner `work/mutate-w2b2p2.py`, scratch
logs `work/mut-w2b2p2-{a,b,c}.log`, git-ignored). Mutants edit the worktree bridge and restore it byte-exact in `finally`;
Chromium only (`FKS_ENGINES=chromium`). All new tests were green at phase 1's bridge on the first run (gap tests, not RED);
each is shown failing under its mutant below. Mutants are against phase 1's bridge (the `-a` and `-b` logs).

| Item | Test (class) | Mutant | Fails |
|---|---|---|---|
| T1 | `test_apply_evidence_needs_both_variables` (EvidenceTests) | 1417 `found.body && found.sans` -> `\|\|` | that test, both CSS cases (2 of 2); 38 others pass |
| T2 | `test_a_heading_role_with_one_display_class_or_one_level_class_is_accepted_and_renders`, `test_a_heading_role_with_the_bare_tag_is_accepted_and_loses_to_bootstraps_class_rule` (EvidenceTests) | `.display-N` accept line (bridge 241) deleted | the first (and phase 1's Apply test) |
| T2 | same two | requires `selectors.length === 2` (cr23-B-mut2) | both new tests (single-selector cases) |
| T3 | `test_a_heading_tag_that_matches_a_non_member_...` (name `Text` added), `test_a_group_that_mixes_a_display_class_with_none_is_named_text` | level read from `claims[0]` only (1815) | the first |
| T3 | the second | display read from `claims[0]` only (1816) | the second |
| T4 | `test_two_code_elements_...` (non-plain groups are exactly `one` mono, `Get started` body) | `&& monos[0] === group` dropped (1850) | that test |
| T5 | `test_without_heading_evidence_each_heading_group_binds_what_its_markup_allows` | claims pushed and heading step run without evidence (both edits, 1810 and 1821) | that test |
| T6 | `test_variables_defined_on_body_only_are_no_evidence` | variables read from `document.body` (1281) | that test |
| T7 | `test_adapter_precedence_and_name_priority_are_pinned_as_the_bridge_decides_them` | mono before heading (1849-1850); `one` on the first signature; `continue` at 1852 removed; `BOOTSTRAP_NAMES` reversed; adapter name before title; class name before adapter name | that test each (the `continue` mutant also fails the phase 0 fixture-names test) |
| T9 | `test_a_heading_tag_that_matches_a_non_member_binds_by_class_and_stays_plain` now applies the detected group as received | none (as briefed: the binding assertion proves the exclusion, `.fs-6` is `!important`; its docstring says so) | n/a |
| T14 | `test_a_detected_body_role_changes_the_family_of_an_element_that_takes_it_only_from_the_variable` (ApplyTests) | `ROLE_VARIABLES = {}` | that test (also 11 existing: the table-case and read-back tests share the mutant) |

Notes. T5: each half of the mutant alone survives (claims without the step bind nothing, the step without claims has no level),
so the killing mutant is the pair, which is the brief's "heading claims and the heading step". T7 pins current decisions as
literals (sources: bridge comments at 177 and 1839-1840, the test at 235); the plan fixes no adapter precedence, name priority or
`BOOTSTRAP_NAMES` order. Not tested, per the brief: a lone author-role paragraph equal to the body style (Addendum 23).
T2 for `['h3']` follows the review's I1 text: accepted, owned node starts `h3 {`, bare `<h3>` computes 30px, `h3.h3` keeps 28px,
receipt (matched 2, mismatched 1, one `fontSize` loss). Extra from phase 1's review (Minor 1): `range(16)` is now
`range(table.SHARED_CLASSES)`.

Runs. Unmutated `python -m unittest test_role_adapters`: `Ran 40 tests in 18.280s`, `OK`. Focused gate
(`gate.sh focused test_role_adapters test_support`): `Ran 74 tests in 32.668s`, `OK`, `GATE focused EXIT 0 IN 33s`.
`python -m ruff check tests/test_role_adapters.py`: All checks passed. `git diff --cached --check`: ok. Full suite not run.

Patch: `task-w2b2-code-p2.patch` (phase 1 + phase 2 against BASE; `git apply --check -R` in the worktree passes; files:
`fontkit-bridge.js`, `tests/test_role_adapters.py`, `tests/test_role_stylesheet.py`). `task-w2b2-code.patch` untouched.

Handoff additions: plan item R2.W2B2 phase 2 done; the two phase 1 survivors the review named (batch clock reset, family half of
`rolesHaveRootBlock`) remain accepted survivors, untouched here.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
