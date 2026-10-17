# HMR restore fix: independent review (2026-10-16)

Patch task-hmr-code.patch sha256 7ed5d794... (15 insertions, 4 deletions, tests/test_r2_react.py only, against 9895585; the staged tree in C:/fks/t27 has the same stat). No repo file was edited. The test ran from the ROOT checkout (fixture node_modules present) using scratch copies of the BASE test file outside the repo: the patch applied with `patch -p1` to `git show 9895585:tests/test_r2_react.py`, plus variants named hmrrev_*.py (scratchpad hmrrev/tests). Root `git status` stayed clean (the test works in a `.fks-` temp copy of the fixture). ASCII only.

### Spec Compliance
- PASS: The restore loop is bounded and condition-based (checks 1).
- PASS: It still proves the restore and fails loudly (check 2).
- PASS with a note: A rewrite cannot mask a failure of the FIRST hot update, only Vite's dropped second one (check 3).
- PASS: The sibling claim holds (check 4).

### Checks run
- Patched test, 6 runs (Chromium): 6 OK. Instrumented copy (prints the attempt that succeeded), 8 runs: attempt 1 in 2 runs, attempt 2 in 6 runs. So on this Windows machine the dropped second change is the common case, not a rare race, and the rewrite is what makes the test pass.
- Mutant `range(1)` (one immediate restore, the old behaviour with the new failure path): 5 of 5 runs fail with `AssertionError: the restored CSS never hot-updated after 5 writes; last computed size 44px`. This reproduces the root cause independently of the writer.
- Mutant "never reaches the target" (wait for `41px`): the test fails after all attempts with `...never hot-updated after 5 writes; last computed size 40px` in 8.8 s total. The loud failure path works and ends the loop.
- ruff on tests/test_r2_react.py: All checks passed; `git diff --cached --check` rc=0 in t27.
- Sibling sweep (grep of every `write_bytes`/`write_text` in tests/ plus the surrounding code of the two CSS hot-update tests).

### 1. Bounded, condition-based, no fixed sleep
`for attempt in range(5)` with a 1,000 ms `wait_for_function` per attempt: at most 5 writes and about 5 s of waiting (plus the byte-restore assertion after each write). The wait is a condition (`getComputedStyle(h1).fontSize === "40px"`) with a timeout, not a sleep; there is no `time.sleep` in the patch. Only `PlaywrightTimeoutError` is swallowed; any other Playwright error (page crash, navigation) propagates. `old_title.dispose()` stays in the inner `finally`. Note the budget: the old restore waited up to 10 s once, the new one waits up to 5 s in total; see Minor 1.

### 2. It still proves the restore and fails loudly
The loop exits only through `break` after the computed size is `40px`; otherwise the `for ... else` runs `self.fail(...)` with the last observed size. The size 40px can only appear if the restored CSS was hot-applied (the page was at 44px after the first change and no other code resets it), so a CSS that never hot-updates cannot pass (mutants above). The following `assert_styles(page)` is unchanged and still checks the original signature after the finally. The byte-exact restore assertion (`css.read_bytes() == original`) runs after every write.

### 3. Can the rewrite mask a real hot-update defect?
- The first update (44px, single write, 10 s timeout) is untouched, so a defect that stops CSS-module hot updates altogether, or one that makes the first change miss, is not masked; the restore also still has to land within 5 writes, so "updates only once" or "never updates after the first" fails (the `never` mutant shows the failure; a stuck watcher would produce the same 44px message).
- What the rewrite does tolerate is exactly the observed Vite 8.3.2 behaviour, that a second change to the same file within a short window yields no update. That is Vite's watcher and not Fontkit Studio's code (the page under test is the React fixture; the bridge is not part of this assertion), and the product never writes this file. A genuine regression of the form "every second save needs a repeat save" would now pass, which is an accepted trade for this test; it is not a product behaviour R2 claims.
- Minor 2 below makes a systematic change in that behaviour visible instead of silent.

### 4. Sibling tests: claim verified
`write_bytes`/`write_text` grep: the only watched-file round trips are in test_one_command_vite.py (line 204 cleanup registration, line 216 one write of `original + body rule`; the restore is `addCleanup` after the whole test), test_one_command_next.py (changed bytes written at 211, then a colour wait, a reload marker check and a typed second edit lasting seconds before the original is written back at 231 and awaited) and this test. Others write scratch setup (test_localhost_cookies 169 reloads a config but is not a CSS hot-update; test_studio_controls rewrites an overrides file that no dev server watches; test_r2_static_fixtures and the preview-server tests write fixtures before serving). No other test writes the same watched file twice back to back. Side observation, out of scope: in the Vite one-command test the second engine rewrites bytes identical to the first engine's write (no file change) and its page loads the already-changed CSS, so that engine's hot-update wait is trivially satisfied; harmless here because focused runs use Chromium only.

### Strengths
- Minimal, local fix with a RED reproduced and a loud, informative failure message that includes the last computed size.
- Comment names the cause and the version; the byte-restore assertion is kept.

### Issues
#### Critical / Important
(none)

#### Minor
1. The attempt wait is a flat 1 s, so the total budget shrank from 10 s to about 5 s. If a slow CI host needs more than a second for even a single legitimate update the loop rewrites four times and could fail where the old test waited 10 s. Make the last attempt wait longer (for example `timeout=5000 if attempt == 4 else 1000`) or compute the first wait from the first update's observed latency.
2. Make the retry visible: with 6 of 8 runs needing the second write, the test is now silently relying on it. Record the attempt count (a failed `assertLessEqual(attempt, 3)` is too strict, but a one-line `print` like the repository's other measurement prints, or a docstring note) so a drift to "always the fifth write" shows up in CI logs. Also the failure text hard-codes "5 writes"; use `attempt + 1` so a changed bound stays truthful (my `range(1)` mutant still printed "5").

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** The loop is bounded and condition-based, it passes only when the restored CSS actually hot-updates (and fails loudly otherwise, reproduced both with the old single-write behaviour and an unreachable target), it leaves the first update and the product untouched, and the sibling claim holds. Two small hardening points remain.

**Verdict: Approved**

STATUS: COMPLETE
