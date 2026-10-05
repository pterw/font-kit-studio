### Spec Compliance
- PASS: Important 1 (clock per engine) is fixed. Each engine's subTest sets `started` just before its own `start()` (test_friction.py:98-101), which does the Popen and reads `Open:` (:55-82). It stops at connected plus title, prints its own `friction:` line and checks the budget (:115-123), and stops its own command in `finally` (:125). A later engine no longer includes an earlier one. The brief still holds: the clock starts just before Popen, stdin is DEVNULL, and the test is one method per engine.
- PASS: Minor 1 (browser launch inside the timed region). Kept on purpose with a comment (:96-97). The brief's order is unchanged, so this is a ruling for the controller, and the comment says so. Accepted.
- PASS: Minor 2 (failure-path read). `text_content(timeout=1000)` with an `<unreadable>` fallback (:110-113), so the intended message and the output are kept.
- PASS: Minor 3 (`Open:` wait). It polls every 0.5 s, fails at once with the joined output when the process exits (:66-75), and has a 90 s deadline (:76-77).
- PASS: Minor 4. `assertRegex` replaces `assertTrue(re.match)` (:117), and the unused `import re` is gone.

### Checks run
- Patch against tree -> compared the patch's added lines with C:/fks/t7a/tests/test_friction.py -> identical.
- Green run -> `PYTHONPATH=tests python -m unittest test_friction -v` in C:/fks/t7a -> OK, 1 test in 1.4 s; nothing left running.
- Double stop (finally, then the addCleanup safety net) -> read stop() (:46-59) -> safe: the second call sees `poll() is not None`, and closing a closed pipe is a no-op.
- The report's multi-engine and mutation evidence (chromium,chromium; budget 0.1; pages?; bogus flag) -> not re-run; the logic matches the code read above.

### Strengths
- The per-engine start makes the printed time and the budget check true for every engine, and a crashed command now fails in under a second with its output.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. `pump` (:38-40) writes to `self.lines`, and `start()` rebinds `self.lines` for each engine (:51). A previous command's pump thread could still deliver a trailing line (for example a shutdown message) into the next engine's queue, which would show up in that engine's `collected` output. It cannot trigger a false `Open:` match, because the old `Open:` line was already consumed. Only a failure message could be misleading, and only in the multi-engine case. A fix is to pass the queue to the pump as an argument. Not blocking.
2. The `<unreadable>` fallback has no test (the report says so). It is a diagnostic branch only; acceptable.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The Important finding is fixed with per-engine commands and clocks, and the four Minors are fixed or reasonably kept with a comment. Only a multi-engine-only, diagnostic-only nit remains.
