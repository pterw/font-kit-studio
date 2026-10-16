# R2.T1 independent review

Independent review of the R2.T1 patch against its brief, 2026-10-16.


### Spec Compliance
- PASS: I-D1 suppression timing. Leak check moved after a fresh complete detect (detect/hello/reset) and, for dispose, after a condition wait (wait_for_function, raf polling) of 1.5x a measured scan length (tests/test_role_detection.py:392-411). No fixed sleep.
- PASS: I-D2 late native premise. Five tests go through start_pending_native_change / check_late_native_focus; stimulus delay is a fraction of the calibration scan's own elapsedMs, awaited on a rAF condition from the target's detect receipt; premise asserted (no reply before the stimulus, event seen, event delay < reply elapsedMs); three fractions then self.fail with the numbers (check_late_native_focus, for/else). The accept-a-complete-reply branch is gone; post-completion epoch half untouched.
- PASS: M-D1 exact {sampleText: elementCount} map (7 literal entries). M-D2 vacuous asserts dropped, exact-limit cases for 10000 / 128 / 8 / 200 added with literal expectations. M-D3 identity-keyed groups. M-D4 both prints gone (grep: no print( in the file).
- PASS: Docstrings. 17 test methods carry one Given/When/Then sentence; they match what the bodies assert.
- PASS: Ownership. Staged diff is one path, tests/test_role_detection.py; sha256 of `git diff --cached -- tests/test_role_detection.py` equals the supplied patch (5864a3c9...).
- PASS: >= relaxations are only where D063 / Addendum 11 changes behaviour: lines 84, 203 (native), 228 (hello after native), 445 (revision). Line 26 (URL), 447 (url/content/style), 459 (fresh equality) keep their strictness. complete False / 'page-changed' still asserted exactly everywhere; nothing else weakened (the removed lines are the always-true scannedElements>=0, inner_text, the complete-old-reply branch and the 30 ms slack, all of which only loosened the test).

### Checks run
- Whole module on the staged tree (chromium, FKS_REQUIRE_FIXTURES=1) -> 17 tests OK in 130.5 s, no skips.
- ruff check tests/test_role_detection.py -> All checks passed; `git diff --cached --check` -> clean; grep wait_for_timeout|sleep|print( -> none.
- Premise fails loudly (item 1/2): temp copy of the module (scratchpad, -revt1) with fractions (3,3,3), style-only late-native test -> FAIL "native change never landed while the scan was pending" with all three attempts' numbers (repliedBeforeNative true). No silent pass or skip.
- Premise can fail on a real defect (item 1): temp runner serving a mutated bridge via bridge_source (repo untouched):
  - listener bump at fontkit-bridge.js:1053 removed alone -> style-only and eligibility-only late-native tests FAIL, `(True, None) != (False, 'page-changed')` (better than the report: a single guard suffices, not the three the report removed).
  - end-of-scan recheck removed alone -> pass (layered, expected). Both removed -> FAIL.
- Suppression mutations (temp runner): detect handler cancel removed -> FAIL at the new leak check (old reply, elapsedMs 337). hello cancel removed + current() narrowed to the generation -> FAIL at the new leak check, 4 of 4 runs (old reply elapsedMs ~929). dispose: cancel + source/origin/session nulling removed + current=()=>true -> FAIL at `messages(...) == []`, 2 of 2 runs. Reset cancel removed (single guard) -> FAIL, but at the pre-existing `old.type == 'timeout'` assertion (old is answered page-changed at 1 ms), not at the new check.
- Calibration soundness (item 2): attempt-1 numbers from the failing-premise run: calibration 266-310 ms, second scan reply elapsed 255-289 ms. Fraction 0.5 puts the stimulus at about 130-155 ms of a ~260 ms scan; 0.35 and 0.2 are further inside. A product failure (premise true, reply complete) is not retried: the loop only retries when the premise is false, so the retry cannot hide a defect.
- Independent probe of the hello leak check (scratchpad probe, same mutation, 3 reps, quiet) -> old reply was not in the log at the point the fresh detect returned (old scan ran ~1.2 s after hello and was cancelled by the fresh detect). Could not reproduce the real test's 4/4 catch with the probe, so treated as a weakness note (Minor 1), not a defect.

### Strengths
- Premise is stated in observable terms (event delay vs reply elapsedMs) and checked on the exact reply, so a stale scan answered "within a slice" cannot be mistaken for a completed one; failure message carries the numbers.
- Retries only on a false premise, never on an assertion failure, so the loop is not a flake mask.
- Exact-limit cases use literal limits and literal identities/sample texts; the sampleText map is a literal dict.
- dispose wait is a condition (raf-polled) derived from a measured scan, not a sleep.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
1. tests/test_role_detection.py:~399 (comment "A fresh complete scan finishing is a point by which an uncancelled old scan has replied") is not true for hello/reset: the fresh detect cancels any live old job on arrival (fontkit-bridge.js:1174), so it is a proof point only if the old scan replied before that arrival. The real test caught the hello mutation 4 of 4 times here, and reset-without-cancel is caught by the older timeout assertion, so nothing is vacuous in practice; but on a quiet host the hello/reset leak check relies on timing. Cheap hardening: apply the dispose branch's 1.5x scan-length wait before the fresh detect for hello/reset too. (The brief says "after the fresh complete detect", so the implementer followed it; the improvement is additive.)
2. tests/test_role_detection.py:~620 comment "each included parent has its own style except the two ordinary ones" is misleading: the map shows 7 groups of count 1, so Prefix and Ordinary body do not share a group either. The report also says "6 groups". Wording only.
3. New `elapsedMs < 2000` on exact-limit cases is redundant with complete=True (the bridge forces time-budget past 2000 ms) and adds no independent failure mode; harmless.
4. Report said the reset suppression case was not separately mutated; it is caught only by the pre-existing timeout assertion, not by the new leak check. Noted for the record; no action.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Each reworked late-native test now fails for a real invalidation defect and fails loudly (not passes or skips) when the pending-scan premise misses; suppression mutations for detect, hello and dispose fail at the new check, relaxations are confined to D063 cases, and exact-limit and sampleText expectations are literal. Only polish items remain.

STATUS: COMPLETE
