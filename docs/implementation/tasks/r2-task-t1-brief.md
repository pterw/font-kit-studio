# R2.T1 brief: harden the merged detection tests

Plan: [R2 plan](../../plans/2026-10-03-r2-engine.md) Addendum 10. PR B, branch
`feat/r2-role-preview`. The controller supplies the detached worktree, BASE
and output paths. Read the binding contract sections "Detection and
performance" and "Role identity and collection algorithm", Addendum 5, D058,
and the audit sections I-D1, I-D2 and M-D1 to M-D4 in
`.superpowers/sdd/r2/test-quality-audit.md`. Verify each finding in the
source before changing anything.

## Exact ownership

Own only `tests/test_role_detection.py`. Product code, the harness
(`tests/role_support.py`, host/target fixtures), fixtures and every other test
module are read-only. A running R2.3 task edits `fontkit-bridge.js`; your
tests run against BASE and will be re-run on the integrated tree at landing.

## Required changes

1. **Suppression timing (I-D1).** In
   `test_latest_detect_hello_reset_and_dispose_suppress_old_jobs`, check for a
   leaked `old` reply only after a point by which an uncancelled scan would
   have replied: after the fresh complete detect for detect/hello/reset, and
   for dispose after waiting at least one measured scan length on a
   condition. Prove the check can fail: with cancellation removed for one
   operation (restored mutation), the test must fail.
2. **Late native premise (I-D2).** The five `test_late_native_*` tests must
   assert that the native change landed while the scan was still pending,
   instead of accepting an already complete reply. Derive the stimulus delay
   from a calibration scan on the same page (for example half its
   `elapsedMs`), or grow the work so the scan spans the stimulus; never a
   fixed sleep. If, after a bounded calibration, the premise still cannot be
   established, the test must fail or skip with an explicit reason, never
   pass. Keep the separate post-completion epoch half as it is.
3. **Minor tightening.** M-D1: assert the set of `sampleText` values, not only
   the count of 7. M-D2: drop the always-true assertions and add exact-limit
   complete cases (10,000 elements, 128 groups, 8 variants, 200-character
   identity) beside the existing over-limit ones, if the fixtures can reach
   them without new files. M-D3: key groups by identity, not reply order.
   M-D4: drop the diagnostic `print` lines; report the numbers instead.
4. **Docstrings.** Each test method gets one Given/When/Then sentence naming
   the intended behaviour, in the style of
   `tests/test_bridge_runtime.py:1161`.

Do not weaken any assertion, threshold or budget. A test that becomes RED
against BASE exposes a product defect: stop and report it with the output;
do not fix product code.

## Focused gates

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_role_detection test_support -v
python -m ruff check tests/test_role_detection.py
git diff --check
```

Run the module three times in a row to show the reworked timing tests are
stable; report each run's count, time and any skip with its reason.

## Report and done

Return the one-path patch and a report: per item, before/after assertion,
the restored mutation that proves the new check can fail, the three run
results, calibration numbers for item 2 and cleanup. Draft the ledger event
and commit why-body in a Handoff section. No stage, commit, push or spawn. A
denied tool call is reported, never retried through a different tool. Done
means each reworked test can fail for the behaviour it names, passes three
times on BASE, and nothing outside the owned file changed.
