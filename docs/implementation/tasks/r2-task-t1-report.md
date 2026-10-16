# R2.T1 code report (MODE code, worktree C:/fks/tt1, BASE 9a4f164)

Changed: `tests/test_role_detection.py` only (staged in the scratch worktree; patch `task-t1-code.patch`, one path, `git apply --check -R` passes, LF only, +159/-100). The worktree copy was CRLF through autocrlf; I normalised to LF (index content is LF, no EOL diff).

## Per item
- **I-D1 suppression.** Before: leak check ran right after `await old` (~250 ms), before an uncancelled scan (~270 ms) could reply. After: detect/hello/reset run a fresh complete `detect` first, then check the log for `requestId == 'old'`; dispose measures a scan length (calibration `detect` on the same page) and waits on a condition (`wait_for_function`, raf polling) for 1.5x that since the request, then checks. Restored mutations (all fail the new test, bridge restored byte-exact in finally):
  - detect: removed `cancelRoleJobs()` in the detect handler -> FAIL (operation='detect', old reply in log).
  - hello: removed `cancelRoleJobs()` in the handshake AND narrowed `current()` to the generation check (the session check alone masks the leak) -> FAIL (operation='hello').
  - dispose: removed the cancel and the source/origin nulling in `dropSession` AND `current = () => true` (post()/studioAlive and source/session checks otherwise mask it) -> FAIL (operation='dispose').
  - Single-guard mutations (cancel only) pass because of layered guards (session, source, studioAlive). Reset was not separately mutated (same cancel mechanism as hello; shares the fresh-detect ordering).
- **I-D2 late native.** Before: `completed_before_native` recorded, complete old replies accepted. After: calibration scan on the same page, stimulus delay = fraction x its `elapsedMs` measured from the target's detect receipt, waited for on a rAF condition; premise asserted = no reply before the stimulus, the target saw the native event, and event delay < reply `elapsedMs`. A missed premise retries on a fresh page with fractions 0.5, 0.35, 0.2; if all miss, `self.fail` with the numbers. A premise-holding reply must be `complete False / page-changed` (the complete-old-rendering branch is removed). Post-completion epoch half unchanged. Mutations: (a) product, in worktree bridge: native listener bump off, and the end-of-scan style recheck and size check off -> 5 late-native tests FAIL (7 subtests, `(True, None) != (False, 'page-changed')`); (b) test: fractions (3,3,3) -> FAIL "native change never landed while the scan was pending" with the numbers (replied before native).
  Observed first-attempt numbers on BASE (chromium, ms): calibration 293-392, wait 147-196, native event delay 156-231, reply elapsed 181-240; every case premise-true on attempt 1 in the numbers run. A first reading that checked "no reply after the event" was wrong (a stale scan is answered page-changed within a slice of the event), so the premise compares event delay to reply `elapsedMs`.
- **M-D1:** each included parent in the direct-text test gets its own font size (except 'Ordinary body' and the unstyled outer 'Prefix'), assertion is the exact `{sampleText: elementCount}` map of 6 groups (7 elements counting Author body, Ordinary body, Prefix, Nested, Contents, Below viewport, Visible child).
- **M-D2:** dropped `>= 0` and `inner_text` assertions; added exact-limit complete cases 10,000 elements (elapsed 568 ms), 128 groups (25 ms), 8 variants (4.7 ms), 200-char identity (4.1 ms), each asserting complete, counts and `elapsedMs < 2000`. Over-limit cases unchanged in expectation; they now also assert 1 group for variants.
- **M-D3:** groups keyed by identity (and `next` by identity/kind) instead of `author, automatic = groups`; author-duplicate group found by identity.
- **M-D4:** both `print` lines removed (numbers reported here).
- **Docstrings:** all 17 test methods plus the shared helper's docstring, Given/When/Then.

## Addendum 11 / D063 comparisons (classification)
- line 26 `currentPageVersion > pageVersion` (unavailable URL via replaceState): author/URL change, kept `>`.
- line 84 (native focus pending scan): native, now `>=`.
- line 203 (late native helper): native, now `>=`.
- line 228 (`hello` roleState.pageVersion vs `stable.currentPageVersion` after native change): native, now `>=`.
- lines 424/426 (stale-evidence test): `revision` case `>=`; url, content and style cases keep `>`.
- line 438 `fresh.pageVersion == fresh.currentPageVersion`: fresh scan equality, unchanged.
`complete False` / `page-changed` stay asserted exactly everywhere. No equality asserted.

## Gates
Focused (three consecutive, `python -m unittest test_role_detection test_support -v`, chromium, FKS_REQUIRE_FIXTURES=1): Ran 51 tests OK in 122.1 s, 129.5 s, 137.7 s; no skips. Machine was loaded by the parallel worktree; thresholds not relaxed. `ruff check tests/test_role_detection.py`: All checks passed. `git diff --check`: exit 0 (only the CRLF autocrlf notice). Full suite not run (controller instruction). pre-commit not run (not requested by the dispatch).
Cleanup: bridge restored byte-exact after each mutation (asserted), scratch copies removed, no servers or processes started by me, no files outside the owned one in the worktree changed.

## Concerns
- The late-native tests cost about 3 s each per engine; a missed premise adds up to two retries.
- Under R2.3 (no wire pageVersion advance for native events) the `>=` comparisons still hold; the product-mutation I used touches an internal bump that R2.3 changes, so the mutation text will need adjusting on the integrated tree.

## Handoff
Ledger event: "R2.T1: detection tests hardened - suppression checked after a fresh scan or a measured scan length, five late-native tests assert the native change landed mid-scan (calibrated, retried, fail not pass), exact-limit complete cases, exact sampleText map, identity-keyed groups, prints removed, Given/When/Then docstrings; page-version comparisons relaxed to >= for native and revision cases per D063."
Commit subject (suggest): `test: assert pending-scan premises in role detection tests`
Body draft: Late native tests accepted scans that had already completed and the
suppression test looked for leaked replies before an uncancelled scan could
reply, so both passed vacuously on fast hosts. The native change is now timed
from a calibration scan and asserted to land mid-scan, the leak check follows a
fresh scan or a measured scan length, and count-only, order-dependent and
print-only checks are tightened. Native and inspector-revision page-version
comparisons are relaxed to >= for the D063 wire change.

## Controller integration (2026-10-16)

The one-path patch (sha256 `5864a3c9...`) applies cleanly with `--3way` on
`90e8a87`; the staged blob equals the writer's index blob. Landing gates on
the staged tree: `test_role_detection test_support` in Chromium with
`FKS_REQUIRE_FIXTURES=1` ran 51 tests in 149.273 s, OK, no skips; static and
provenance, `node --check`, product-tree Ruff, staged and unstaged whitespace
and the commit-message range pass; exact Ruff reports only the four findings in
the owner's untracked `.agents/` skill. On a scratch tree holding this patch
and the R2.3 candidate together, the R2.3 focused set plus this module ran 101
tests in 184.886 s, OK, no skips (Detect after Apply 1,183.5 ms), so the
relaxed comparisons hold under D063. Full suites, the frontend gate and the
Firefox canary belong to the settled wave.
