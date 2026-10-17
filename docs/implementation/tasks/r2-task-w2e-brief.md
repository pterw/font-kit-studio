# R2.W2E brief: two slow test helpers prove the same thing faster

Owner decision 2026-10-17 ("Small slice in W2 (Recommended)"), from the PR B2 Efficiency review (workspace `w2-review.md`,
EFF4 and EFF5). Tests only; no product change. BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`. Worktree `a scratch worktree`
(npm fixtures linked by the controller), task id `w2e`. Two phases, each a new agent; one commit at landing. Line budget:
about 30 gross lines in all.
- **Phase a (EFF4, `tests/test_r2_react.py` only):** PATCH_DEP `task-w2t-code.patch` alone (the only other slice that
  edits that file). Patch `task-w2e-code.patch` (delta on W2T).
- **Phase b (EFF5, `tests/test_studio_roles.py` builder only):** a new agent in the same worktree after phase a, with
  `task-w2sa-code.patch`, `task-w2sb-code.patch`, `task-w2pt-code-r1.patch` and `task-w2ps-code.patch` applied on top
  first (W2S-b and W2PS edit other regions of that file; one writer at a time). Patch `task-w2e-code-p2.patch` (delta on
  all the PATCH_DEPs and phase a).

## Why

1. **EFF4.** `tests/test_r2_react.py` proves "no listener" after stopping a host with `connect_ex` under a 2 s timeout
   (`stop_host` near 214 at BASE, `stop_vite` near 157). On Windows a refused loopback connect returns only after the full
   timeout, so every stop waits 2 s; a listener answers in about 0.3 ms, so 0.25 s proves the same. `server.serve_forever`
   keeps its 0.5 s default poll, so `shutdown()` waits up to 0.5 s. Measured: the module takes 41.0 s locally, 18.7 s with
   both changes; CI on Linux is unaffected.
2. **EFF5.** The 1 MiB receipt builder in `tests/test_studio_roles.py` (near 1366 at BASE; the PATCH_DEPs may move it) finds
   the largest `full` by a linear search over a monotone `measure` (994 calls, 3.6-4.1 s); a bisection needs 26 calls
   (0.17-0.19 s) and returns identical `(full, first, second)` for both sizes.

## Owned files (exact)

- `tests/test_r2_react.py`: the two "no listener" probes and the `serve_forever` call(s) of its hosts. Nothing else.
- `tests/test_studio_roles.py`: the receipt builder's search. Nothing else.

Read-only: every other file. Running worktree beside yours: `a scratch worktree`. Never touch it.

## Requirements

1. (Phase a) Both probes use a 0.25 s timeout and keep asserting that nothing answered within it (on Windows a closed
   port returns 10035 after the full timeout, so word the message "nothing answered within 0.25 s", not "refused");
   hosts serve with `poll_interval=0.01`.
2. (Phase b) The builder's search is a bisection over the same monotone `measure`, with an upper bound derived from
   `measure` (grow it until `measure(hi) > size`), never a hard-coded constant: a too-small bound builds a different shape
   and the builder's own `assertEqual` still passes. Oracle, the linear search's triples measured by the brief review on
   W2T's tree: `(494, 667, 1)` for 1 MiB + 1 and `(494, 666, 1)` for 1 MiB; the bisection must return exactly these. The
   costs "994" and "26" calls are totals across both sizes.
3. No assertion is weakened, removed or retimed beyond requirement 1.

## Tests and mutants

No new test. Evidence: the module timings before and after (three runs each, local Windows); for requirement 2 the triples.
Mutants (restored byte-exact, SHA-256 before and after; PYTHONDONTWRITEBYTECODE=1): phase a, `server_close()` removed from
`stop_host` (a listener remains; the probe fails); report the dead-probe case (a probe that never connects) as uncovered
by any test. Phase b, a bisection returning `full + 1` (the 1 MiB test fails); and `full - 1`, which returns
`(493, 1999, 747)`, still sums to exactly 1 MiB and stays green: only the recorded triples catch it, so assert them in
the report's evidence run.
A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash. Phase a:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_r2_react test_support`
(about 20-45 s per module run; the six timing runs add about 3 minutes). Phase b: `... focused test_studio_roles
test_support` (about 4 minutes).
Also `python -m ruff check` on both files and after staging by name `git diff --cached --check`.

## Report and handoff

Report: the timings, the triples, each mutant, the focused run (Ran line, OK, GATE line), gross lines. Patch
`task-w2e-code.patch` holds only your changes on top of the PATCH_DEPs, with their SHA-256s. Commit subject
`test: shorten two slow role test helpers`, a draft body (why, wrapped at 72).
