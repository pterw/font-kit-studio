# Task 2 code report (E-1a, serve.py refuses port 0)

Mode code, worktree the task's worktree, BASE 5443ff6. Nothing committed. Patch: task-2-code.patch (scripts/serve.py +4, tests/test_serve_proxy.py +45).

## Changed
- scripts/serve.py main(): a loop over (--studio-port, --target-port) just before the equality check. Port 0 prints New string 6 verbatim to stderr and returns 2. No new constant (string is built from the flag; about 4 lines). Equality check unchanged (parser.error).
- tests/test_serve_proxy.py: class ArgumentTests after TargetTests, with a shared helper run_main (bind recorder, redirected stdout/stderr, catches SystemExit) and the three brief tests. Per Review fixes: equal-ports test checks code 2, no binds, empty stdout, and `assertIn` on the must-differ text; the stderr there carries the usage block.

## Tests
- RED at BASE code (tests added first): 3 failures (both subtests of the flag test, plus the two-zero test); `--studio-port 0` reached the bind (code 1, one bind recorded). Equal-ports test passed (characterization).
- GREEN: `test_serve_proxy.ArgumentTests` 3 OK; `test_serve_proxy` 48 OK; `test_support` 34 OK (FKS_ENGINES=chromium, PYTHONPATH=tests).
- Breaks, each run against the mutated serve.py the tests loaded, then restored:
  - zero check moved after equality: `test_two_zero_ports_are_not_called_equal` FAILS (1 failure).
  - only --studio-port checked: `test_a_zero_port_is_refused_by_flag_name` FAILS for flag='--target-port' (1 failure).
- Restored; ArgumentTests 3 OK afterwards.

## Outside my regions / concerns
None. No browser or server started. Pre-existing tests unaffected.

## Handoff
CHANGELOG line: "serve.py now refuses `--studio-port 0` and `--target-port 0` by name instead of reporting two ports as equal."
Commit subject: `fix(serve): refuse port 0 by name instead of calling two ports equal`
