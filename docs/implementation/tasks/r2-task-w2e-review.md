# task-w2e review: Phase a (EFF4, tests/test_r2_react.py)

Reviewer read-only. Frozen worktree a scratch worktree left byte-identical (test_r2_react.py SHA-256 3801a735...5220 before and
after; `git diff` hash a5c9111b... equals the SHA-256 of task-w2e-code.patch; `git diff --cached` hash 2f1697fb... equals
the W2T PATCH_DEP). Phase b not reviewed.

### Spec Compliance
- PASS: both probes use `settimeout(0.25)` and still assert `assertNotEqual(connect_ex(...), 0)` (tests/test_r2_react.py:151-152, 208-209).
- PASS: messages say "owned ... listener answered; nothing should answer within 0.25 s", not "refused" (:153, :210).
- PASS: the host serves with `poll_interval=0.01` via `partial(server.serve_forever, poll_interval=0.01)` (:195); it is the module's only `serve_forever` (grep).
- PASS: no assertion weakened beyond the timeout and poll interval (requirement 3); owned region only; no new test (brief).
- PASS: size 5+/5-, 10 gross lines, within the ~30-line budget. File stays CRLF.
- PASS: drift: tests only, one file, no product change.

### Checks run
- Patch matches tree -> sha256 of `git diff` in a scratch worktree vs the patch file -> identical; staged diff equals W2T patch hash.
- Mutant (`server.server_close()` -> `pass` in `stop_host`) -> scratch copy of the tree (fixtures as a junction to the frozen
  fixtures, CRLF-preserving byte replace, count asserted 1, PYTHONDONTWRITEBYTECODE=1), `python -m unittest test_r2_react` ->
  `Ran 10 tests`, `FAILED (failures=5)`, five host tests with "AssertionError: 0 == 0 : owned host listener answered; nothing
  should answer within 0.25 s". Matches the report. Scratch removed (junction removed first; frozen fixtures still 9 entries).
- Fake versus real -> unchanged: the probe still hits the real listener port of the real ThreadingHTTPServer.
- Hidden skips -> diff contains no skip, no env gate; on Linux a closed port gives ECONNREFUSED at once and a leaked listener
  answers (rc 0), so the probes still run and still catch a leak.
- Timings -> re-ran `gate.sh focused test_r2_react` in the frozen worktree: `Ran 10 tests in 14.444s`, `OK`, `GATE focused
  EXIT 0 IN 15s`. Report claims 15.4-15.9 s after, 41.2-42.7 s before; plausible (5 host stops x ~2 s probe + vite stops
  saved, plus 0.5 s poll waits). The before figure matches the brief's 41.0 s. I did not re-run "before".

### Strengths
- The mutant evidence is real: the probe fails exactly on the thing it exists to guard, with the new message.
- Residual Windows risk is correctly described in the report (brief review Minor 2) and is small in effect: a systematic
  leak, which is what the mutant models, leaks in every one of the five host tests, so missing it needs five independent
  misses at about 1 in 1,000 each. Only a rare intermittent leak could slip locally, and Linux CI refuses/answers
  exactly. The 2 s probe was safer per miss, but the saving (about 26 s of 41 s) justifies the trade.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The dead-probe case (a probe that never connects) stays green; reported as uncovered by any test, as the brief asks. Not a defect of this change.
- The Vite probe (`stop_vite`, :151) has no mutant evidence here; the brief asks only for the `stop_host` mutant, and the code is the same 5-line shape. Optional.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved (Phase a)
**Reasoning:** The change is exactly the requested 0.25 s probe timeout, wording and 0.01 s poll, with no assertion weakened. The `server_close()` mutant fails five host tests with the new message, and the module runs green in about 14-15 s.

## Phase b review (EFF5, tests/test_studio_roles.py builder), patch task-w2e-code-p2.patch

### Spec Compliance
- PASS: tests only. The patch (sha256 fb7df0fc..., matches the file) touches only `tests/test_studio_roles.py`, one hunk in the
  receipt builder (6 added, 3 removed). `git diff` of the frozen worktree is byte-equal to the patch (CR-stripped sha match); no other file moved.
- PASS: requirement 2, bisection over the same `measure`, bound derived: `over` doubles while `measure(over, 1, 1) <= size`,
  so the bound is found by `measure(hi) > size`; no constant. The `rest/first/second` lines and the final `assertEqual(measure(full, first, second), size)` are untouched.
- PASS: requirement 3, no assertion weakened, removed or retimed. Budget: phase a 10 + phase b 9 = 19 gross lines, under about 30.
- PASS (with a correction to the record): equivalence with the linear search. See Checks; the 18 shift is not caused by any PATCH_DEP.
- Deviation recorded: the brief's oracle triples (667/666) were not matched, and the report says so. The deviation is legitimate; the
  oracle stated in the brief ("the linear search's triples") was measured from an offline model, not the live request.

### Checks run
- Equivalence offline (scratch `w2e-b-review-triples.py`, tests/ rebuilt from BASE with each PATCH_DEP applied in turn: w2t, w2sa,
  w2sb, w2pt-r1, w2ps-r1; staged blobs of test_studio_roles/role_contract/test_role_protocol/test_r2_integration matched the worktree
  index modulo CRLF; the new block was lifted verbatim from the worktree file and exec'd) -> at every stage linear and bisection both give
  (494, 667, 1) / (494, 666, 1), sums exact, per-loss 2,078 bytes; calls per size 496 linear vs 19 bisection. So no PATCH_DEP changes the triple in the offline model.
- Equivalence live (scratch copy of the worktree with fontkit-studio.html, fontkit-bridge.js and tests/; one test run in Chromium
  with a TRIPLE print inserted before the final assertEqual): staged state (linear, no phase b) -> (494, 649, 1) and (494, 648, 1);
  worktree file (bisection) -> identical (494, 649, 1) and (494, 648, 1). Test OK in both: 5.6 s linear vs 1.8 s bisection.
  This is the oracle the brief asked for ("same triple as the linear search on the same tree"): met.
- Explain the 18 shift -> same live run with BASE fontkit-studio.html and only W2T's tests (BASE+W2T) still gives (494, 649, 1) with
  sessionId 'fks-df638312cfeac7e5' (20 chars). The brief review's offline model used sessionId 's1' (2 chars): 18 bytes, and
  `measure` puts the sessionId in the envelope once. So the shift comes from the real page's session id, not from W2SB/W2PS or any PATCH_DEP.
  The report's cause ("W2SB/W2PS change the envelope size by 18 bytes") is wrong; its conclusion (the old algorithm is the oracle, equal here) is right.
  The recorded triples in the brief should be restated as (494, 649, 1) / (494, 648, 1) live (667/666 are an offline artefact).
  Session ids are 'fks-' + 16 hex, fixed length, so the live triple is stable run to run.
- Mutant `full + 1` (scratch, after the bisection): RED, `AssertionError: 1050008 != 1048577` and `!= 1048576` (failures=2).
  Reproduced.
- Mutant `full - 1` (scratch): GREEN (`Ran 1 test ... OK`), full 493 for both sizes. Reproduced; caught only by comparing triples.
- Upper bound derived -> read the hunk (file lines 1377-1382): no literal bound; edge `measure(1,1,1) > size` leaves full=0 (same as the old loop);
  the invariant `measure(0,1,1) <= size` stays implicit, as before. `measure` is monotone here (checked by the identical triples and 2,078 per loss).
- Budget / assertions -> diff read; ruff clean (`All checks passed!`), `git diff --check` and `git diff --cached --check` both rc 0.
- Focused run -> not re-run; the report's `Ran 127 tests ... OK, GATE EXIT 0` is the evidence, and I ran the one affected test live twice.
- Scratch copies deleted; frozen worktree test file sha256 unchanged (4e7aa901...).

### Strengths
- The bound grows from `measure`, so a contract change that shrinks a loss cannot silently freeze a wrong shape.
- Same shape and same triples as the linear search in the live run; the test drops from 5.6 s to 1.8 s.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Report cause of the 18-byte shift is wrong (see Checks): it is the live sessionId length (20 vs the offline model's 2), not W2SB or W2PS. Fix the
   record only; no code change.
2. The `full - 1` mutant stays green and no test pins the triple. Should the test assert it? No: the triple is a property of the live session id,
   the roles and the CSS, so a literal would break on unrelated envelope changes, and the shape `(493, 1999, 727)`-style is still an exact 1 MiB
   receipt, so the test's claim (the boundary) holds. The brief put the triple comparison in the evidence run; that is done (equal to the linear search
   live). Optional hardening, if the owner wants the bisection's maximality enforced: one line `self.assertGreater(measure(full + 1, 1, 1), size)` after the search
   would turn `full - 1` red without a literal; I do not require it.
3. The call count is about 19 per size (doubling then bisection), not the brief's 26 total; the brief's figure assumed a fixed bound of 1200. Still about 12x fewer than 496; no action.

### Plan-mandated (for the owner)
- [Minor] The brief's oracle triples `(494, 667, 1)` / `(494, 666, 1)` (requirement 2) are an offline-model artefact (sessionId 's1'); live they are `(494, 649, 1)` /
  `(494, 648, 1)`. -- brief requires: "the bisection must return exactly these". The implementer could not meet this without breaking the other
  requirement ("the same triple as the linear search" is the real oracle), and reported it; the brief text should be corrected.

### Assessment
**Task quality:** Approved (Phase b)
**Reasoning:** The bisection is a minimal, derived-bound replacement that returns exactly the linear search's triples on the live integrated tree (reproduced in Chromium), `full + 1` is red and `full - 1` is an equivalent mutant caught only by the triple comparison, as the brief expects. The one error is the report's explanation of the 18-byte shift (session id length, not a PATCH_DEP), which touches the record, not the code.
