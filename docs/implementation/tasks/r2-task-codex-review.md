# PR #22 Codex review fixes, Studio: independent review (2026-10-17)

### Spec Compliance
- PASS: Fix 1. `design:ready` computes `sameDocument` (accepted preview has a documentId, same origin, and the ready's roleState.documentId equals it) before `acceptRoleReady`, then `live.revision = sameDocument ? Math.max(live.revision, readyRevision) : readyRevision` (fontkit-studio.html:5496-5504). A new document (or another origin, or no accepted preview, or a ready with no roleState) still adopts a lower revision. Targets, status, mode, selection, changes and the rest of the ready handler are untouched and still run.
- PASS: Fix 2. `serializeRoleSheet` (fontkit-studio.html:3917-3925) and `css === serializeRoleSheet(roles)` in `validAcceptedRoles` (:3932). `validAcceptedRoles` is the single gate for receipts (:4368), ready snapshots (:3972) and the reset-all reply (:4426), so all three are covered. The comment says R2.S3 must extend the serializer for the Bootstrap templates (global rule 10).
- PASS: Tests named in the brief exist: stale same-document ready, new-document adoption, hostile receipt rows, hostile ready, two real-bridge serialization checks (CJK quoted family plus every property; escaped class selector `.sm\:big`). The mutant that skips the equality check is killed (below).
- PASS: No scope creep. Only the three owned files changed; no commit; patch is the staged diff.
- PASS: Each new test has a Given/When/Then docstring.

### Checks run
- Serializer parity (check 2) -> scratchpad `ts4rev-fuzz.js`: extracted Studio's `serializeRoleSheet` and the bridge's `roleDeclaration`/`serializeRoleCss` from the frozen sources, ran 200,000 random role sets (random property subsets in shuffled insertion order, 1-2 selectors including an escaped `.sm\:big`, fontSize 4..400 at 2 places, lineHeight at 3, letterSpacing at 4 places with -0.5, 0, -0, 2, 0.0001, -0.0001, 1e-4, fontWeight integers, all four textTransform values, a CJK family), each round-tripped through JSON -> 0 differences. Edge probes: 1e21 fontSize, 1e-7 lineHeight, 0.0001em -> identical strings; empty roles -> both "". Numbers are formatted by the same JS template in both, and Studio's `roundTo(value)===value` check means the receipt value is already canonical. Property order, `Object.hasOwn` vs the bridge's `in`, `, ` join, indent and trailing `}\n` all match.
- Focused command 1 (test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support), Chromium, PYTHONPATH=tests, FKS_REQUIRE_FIXTURES=1, in C:/fks/ts4 -> `Ran 200 tests ... OK`.
- Focused command 2 (test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests test_studio_visual.LiveAppViewTests) -> `Ran 184 tests ... OK`.
- Worktree not modified: after the runs, sha256 of fontkit-studio.html is bd3beabd...d804, same as the report; test files unchanged; git status shows the same 3 staged M files.
- Mutants (check 4), run on a copy at C:/fks/ts4rev (since removed), source restored and hash-checked (`restored True`, bd3beabd...d804) after every run:
  - revision guard removed (`live.revision = readyRevision`) -> stale-ready test FAILED (failures=1).
  - guard turned into always-max (new document no longer adopts lower) -> new-document test FAILED (failures=1). The two tests pin the guard from both sides.
  - equality check removed -> hostile-receipt table test and hostile-ready test: `FAILED (failures=1, errors=2)`.
  - fontSize `px` dropped in the serializer -> real-bridge test ERROR (receipt never shown).
  - ROLE_PROPS order swapped (letterSpacing before lineHeight) -> real-bridge test ERROR.
  - 128 KiB limit `<=` -> `<` -> boundary test ERROR (limit-size receipt rejected); `<= limit + 1` -> boundary test ERROR (limit+1 receipt accepted, fence ignored). So that test still sits exactly at limit and limit+1.
  - selector join `", "` -> `","` -> StudioRoleApplyTests plus StudioRoleBridgeTests (36 tests) all OK: SURVIVES (see Minor 1).
- Changed existing tests (check 3), read at HEAD of the patch:
  - Hostile table: the fence is now distinguished by an outcome marker (`matched 100+index`) rather than extra CSS, a new request is issued per subtest, and the wait is on the marker text. If a hostile receipt were accepted, the request would settle with the hostile outcomes and the fence would be ignored, so the wait times out. Still tests what it meant to. The two new rows and the equality mutant above show it is not vacuous.
  - Wrong-session test: `marked` now differs by outcome (`matched 9`) instead of CSS; the real receipt is awaited via `matched 1,`; asserts `matched 9` is absent. Same logic, not vacuous.
  - 128 KiB: `sized_receipt` builds a real serialization of exactly `size` bytes (asserted by `assertEqual(len(css.encode()), size)`; over case asserted > limit); the bytes differ between over and fence only in selector padding of at most ~6 roles of <2000 chars, so the size limit is the only thing separating them. The two `<=` mutants above confirm it fails at both sides.
  - 1 MiB: padding moved from CSS into a second partial loss selector; the envelope is measured exactly (`assertEqual(measure(...), size)`) at limit and limit+1. The accepted case now waits on `matched 64,`, which cannot be left over from the previous (rejected) subtest, whose visible outcome is `matched 7,`. The old wait on status text (already true from the previous subtest) was the vacuity the author fixed. Not vacuous.
  - Literal markup test, renamed `..._in_names_and_details_...`: names and rejection detail with `<img ...>` still asserted as literal text (`assertIn(literal, shown['outcomes'])`, and the detail path after the rejected request). The CSS part was dropped: markup cannot occur in canonical CSS now, since selectors fail `UNSAFE_SELECTOR_TEXT`/`ROLE_SELECTOR_GRAMMAR` and families fail `ROLE_FAMILY_UNSAFE` (`<`, `>`). Dropping it is correct, not a weakening; the rename matches.
- Documentation sibling grep for "does not re-serialize" -> `docs/implementation/tasks/r2-task-s2-brief.md:170` still says "Studio checks hash, size and shapes; it does not re-serialize CSS". Not in the diff and controller-owned (report already lists bookkeeping as a concern); see Minor 3.

### Strengths
- The revision guard is scoped tightly (document id and origin) and both directions are pinned by tests that fail under their respective mutants.
- One validator (`validAcceptedRoles`) covers receipts, ready snapshots and reset-all; the serializer was fuzz-equal to the bridge for every property format I could construct.
- Boundary tests were rebuilt so the byte counts are asserted rather than assumed, and the previously weak 1 MiB wait was fixed.
- Per-subtest request in the hostile table removes cascade failures.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Selector join separator is untested. The `", "` join in `serializeRoleSheet` (fontkit-studio.html:3923) survives a mutation to `","`: no test in test_studio_roles.py or test_r2_integration.py has a role with two selectors (grep for two-element `selectors` lists found none), and the real-bridge tests use single-selector roles. If the join drifted, every multi-selector receipt would be rejected. Add one multi-selector role to the real-bridge CJK test or one canonical-css case with `['.a', '.b']`.
2. No test shows that a stale same-document ready still updates the rest of the ready (targets, status). The code does handle them (the guard touches only `live.revision`), but the "do not drop the ready" requirement is held by reading, not by a test.
3. `docs/implementation/tasks/r2-task-s2-brief.md:170` now contradicts the code ("it does not re-serialize CSS"). Controller bookkeeping; flag for the owner.
4. `canonical_css` in the tests formats numbers with Python, which differs from JS for floats like 1e-05 or 24.0. All current values are ordinary, so no failure, but a future test with such a value would be rejected by the strict check. Not worth acting on now.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Both fixes match the brief and the bridge's serializer byte for byte (200k-case fuzz plus edge probes, both focused commands green at 200 and 184 tests). The changed existing tests still pin the exact limit and limit+1 and the text-only rendering, and the new guards each die under a restored mutant; the only gap is an untested selector-join separator (Minor).

STATUS: COMPLETE

## Scoped re-review (fix round 1)

- Patch identity: sha256 of task-codex-code-r1.patch is e266eca3...b4c; `git diff --cached` in C:/fks/ts4 hashes to the same value, so the staged work is the reviewed patch.
- Check 3, nothing else changed: `diff task-codex-code.patch task-codex-code-r1.patch` shows only index/hunk-header renumbering plus additions in tests/test_r2_integration.py (the `TWO_SELECTOR_PAGE` constant and one new test). No line removed, no change to fontkit-studio.html or tests/test_studio_roles.py (their sha256 match the first review: bd3beabd...d804 and 86b72a1b...660c).
- Check 1: `test_a_receipt_for_a_role_with_two_selectors_equals_studios_serialization` opens a real-bridge page with two same-styled paragraphs, Detects, applies, asserts the request role has 2 selectors, asserts a ", " in the receipt's rule head (`css.split(' {')[0]`), waits for "Preview applied to 1 role", asserts `preview(page)['css'] == receipt canonicalCss` (byte for byte, since Studio shows the CSS only after its own serialization equals the receipt's), and that both paragraphs compute 24px. It has a Given/When/Then docstring.
- Check 2: on a copy (C:/fks/ts4rr1, removed), `role.selectors.join(", ")` changed to `join(",")` in `serializeRoleSheet`; the new test ERRORS with a Playwright 30 s `wait_for_function` timeout (receipt rejected, preview never shown); source restored, hash-checked (`restored True`). This closes Minor 1 of the first review.
- Run: `test_r2_integration test_support` (Chromium, PYTHONPATH=tests, FKS_REQUIRE_FIXTURES=1) in C:/fks/ts4: Ran 60 tests, OK. Worktree hashes and staged status unchanged afterwards.
- Minors 2 to 4 of the first review are unchanged (not in scope of this round).

**Verdict:** Approved. No Critical or Important findings.

STATUS: COMPLETE (re-review)
