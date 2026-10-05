### Spec Compliance
- PASS: the budget is 2 s when CI == 'true' and 10 s otherwise (tests/test_friction.py:33), as the owner ruling says. The diff touches only tests/test_friction.py (import os at :8, comment :29-32, constant :33).
- PASS: the badge wait (BADGE_WAIT_MS = 90000, :34) is far above both 2 s and 10 s, so a slow start still reaches the budget assertion (:129-131) with its elapsed time. Only a Studio that never connects fails at the wait.
- PASS: GitHub Actions sets CI=true on every runner, so the comparison to the string 'true' is correct. A developer with CI=1 falls to the 10 s local budget, which is the safe direction.
- PASS: the output line still prints the effective budget (:127) and the assertion message names both numbers.
- PASS: no other file changed. The workflow already lists test_friction (quality-gate.yml:250), so the wiring is unchanged.
- CANNOT VERIFY FROM DIFF: the comment says the 0.8 s maximum came from the Windows cell. The ruling gives only the range 0.4 to 0.8 s over five cells and does not say which cell was slowest. The CI logs would confirm it. See Minor 1.

### Checks run
- Does the comment match the ruling's numbers? -> read the patch against the ruling in the dispatch -> "1.2 to 4.6 s seen" matches. 0.8 x 1.5 = 1.2, rounded up to 2, so the arithmetic holds. The Windows attribution is unverified (Minor 1).
- Does the test run with CI=true? -> `CI=true PYTHONPATH=tests python -m unittest test_friction` in the main checkout -> printed `friction: 1.2 s (budget 2 s)`, 1 test, OK. This ran alone, so the browser launch was cold. The process exited and I left nothing running.
- Is the browser shared and warm in CI? -> read tests/support.py (shared_runtime, shared_browser, new_context) and quality-gate.yml:250 -> one Playwright driver and one browser per engine live for the whole process. The CI command runs test_vite_build_guarantee, test_one_command_vite and test_one_command_proxy before test_friction. Unittest loads named modules in the order given. Those earlier browser tests have usually launched the browser already, so the launch (about 0.5 s per support.py's own comment) is mostly outside the timed region. The timed region still includes new_context and page creation (test_friction.py:105-109).
- Are Vite's deps already optimized by earlier tests? -> grep of the fixture tests and fixtures/vite-react -> test_one_command_vite starts Vite on fixtures/vite-react (three tests; project dirs sit inside that fixture, one test starts it in the fixture itself). The vite-react fixture has no vite.config cacheDir override, and no test removes the cache, so the cache under fixtures/vite-react/node_modules/.vite persists across the run. Vite's dep pre-bundling is therefore normally warm when test_friction runs. I did not confirm the cache directory exists after those tests, only that nothing deletes it.

### Strengths
- The CI budget is derived from measurement, and the comment says how. The local budget is stated as a stuck-start catcher, with the owner's date.
- Because the badge wait is 90 s, a budget miss reports the elapsed time rather than a timeout.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_friction.py:30 -- "(0.8 s, Windows)" names the slowest cell, but the ruling lists only the range. If the 0.8 s came from another cell, the comment is false. Check the CI log and fix the name if needed.
2. tests/test_friction.py:29-33 -- the 2 s CI budget is 2.5x the slowest single sample, and each cell has one sample from one run. The risks I see:
   - The margin depends on the warm-state ordering in the workflow's `unittest` list. Moving test_friction first, or running it alone (a CI re-run of one module, or `ONLY`), adds a cold browser launch of about 0.5 s plus a possible Vite dep re-optimization (a full page reload when Vite finds new deps). That could take a 0.8 s cell past 2 s. Locally, running alone cold still gave 1.2 s, so the single-module case is likely fine on a fast machine.
   - Hosted macOS and Windows runners are known for occasional multi-second stalls. A stall fails the job with no retry.
   - My judgement is that this will not flake in the normal ordered run. Treat the first few CI runs as the real evidence. If one cell goes over, raise the budget to 3 or 4 s rather than add retries. A comment line naming the dependence on order (earlier tests warm the browser and Vite's cache) would help the next reader.
3. tests/test_friction.py:34 -- the BADGE_WAIT_MS comment says "longer than the budget", which is still true. Consider noting it is 45x the CI budget, so the reader knows the two are meant to be far apart. Cosmetic only.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The edit matches the owner ruling exactly. CI detection is correct, the 90 s wait still exceeds both budgets, and the test runs green under CI=true. The only gaps are an unverified "Windows" attribution in a comment and a modest flake risk if the test order or warm state changes. Neither is a defect today.
