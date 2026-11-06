### Spec Compliance
- PASS: Req 1-2. `--studio-port 0` / `--target-port 0` return 2 and print New string 6 verbatim (flag in both places) to stderr, nothing on stdout (scripts/serve.py:726-729 in patch; test asserts exact literal + one newline, tests/test_serve_proxy.py:43-51).
- PASS: Req 3. Both 0 names `--studio-port` (first in the loop) and has no "must differ" (test_two_zero_ports_are_not_called_equal, :53-59).
- PASS: Req 4 / Review fix 1. Equality check untouched (still parser.error); the test catches SystemExit, asserts code 2 and `assertIn` on the must-differ text (:61-66). Review fix 1 asks for `assertRaises(SystemExit)`; the helper catches SystemExit and compares the code, which has the same observable effect (a non-raising return of 2 would also pass, but that is not a realistic break here). Minor only.
- PASS: Req 5. Loop sits immediately before the equality check; order after the target/asset exits is kept (Controller ruling 2).
- PASS: Review fix 2: all three tests use the same bind recorder through `run_main`, and assert `binds == []`.
- PASS: Review fix 3: expected stderr is the literal plus "\n".
- PASS: Owned regions. Source change only in `main()` at the equality check; no constant added (brief says "if needed"); tests only add `ArgumentTests` after `TargetTests`; CHANGELOG untouched, draft in Handoff.
- PASS: Budget: 4 source + 45 test lines, near the ~40 estimate; no stray file.

### Checks run
- Patch applies to BASE -> `git apply --check --cached` (index is BASE) -> APPLIES; worktree diff is byte-identical to the patch; `git status` shows only the two files.
- Focused tests -> `python -m unittest test_serve_proxy.ArgumentTests -v` -> 3 OK. Whole `test_serve_proxy` (FKS_ENGINES=chromium, PYTHONPATH=tests) -> 48 OK. `test_support` left to the report (34 OK claimed); the change cannot touch it.
- Other defects -> mutate script on a scratch copy outside the repo (deleted afterwards), the mutated serve.py is the one `load_serve` imports (SERVE path is relative to the copy's tests dir) -> killed: zero check after equality (two-zero test), studio-only check (target flag subtest), return 1 instead of 2 (all), message to stdout instead of stderr (all), equality check deleted (equal-ports test), wrong flag name in the second slot of the message (target subtest), check disabled (all). MISSED: `port <= 0` (negative ports); not a requirement of the brief, and the wording "0 is not accepted" would be wrong for -1 anyway.
- Regressions: `test_studio_roles`, `test_role_routes`, `test_r2_integration` do not exercise `serve.main` argument handling or the port-0 path; not run, left for the wave gate.
- Boundaries: no Studio/bridge crossing; no HTML/JS text.
- Line length: no added line over 120 chars; no lint config found.
- RED at BASE: not re-run by me; the report's RED claim is plausible by reading (BASE has no zero check, the two-zero case reports "must differ"), and the mutations above show each test fails when the behaviour is removed.

### Strengths
- Every test pins stdout, binds and exact stderr, so a fall-through to a real bind, a wrong stream, or a wrong flag name all fail.
- Bind recorder keeps a regression from opening a real port.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- Negative ports (`--studio-port -1`) still go through; out of scope here, recorded only.
- `run_main` catches SystemExit rather than using `assertRaises` as Review fix 1 words it; the equal-ports test would also pass if the code returned 2. No verdict depends on it.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The port-0 refusal matches New string 6 exactly, runs before the equality check and keeps the old message; tests are non-vacuous and killed 7 of 8 candidate defects (the one miss is out of scope).
