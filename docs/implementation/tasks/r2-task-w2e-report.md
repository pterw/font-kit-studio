# task-w2e code report

## Phase a (EFF4, tests/test_r2_react.py), mode code

PATCH_DEP task-w2t-code.patch sha256 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd (checked, applied
with `git apply --index` at BASE 73b3ba2). Patch `task-w2e-code.patch` is the UNSTAGED delta on that staged state;
`git apply --check -R` passes. Worktree a scratch worktree. Phase b not touched (tests/test_studio_roles.py unchanged).

Change (5+/5-, 1 file): both probes (`stop_vite`, `stop_host`) use `settimeout(0.25)` and the message
"owned ... listener answered; nothing should answer within 0.25 s" (assertNotEqual(connect_ex, 0) kept); the host thread
target is `partial(server.serve_forever, poll_interval=0.01)` (`partial` was already imported). File is CRLF; edit kept CRLF.

Timings, `focused test_r2_react` (Ran 10 tests), three runs each:
- before (W2T tree): 41.234 s, 42.693 s, 41.605 s
- after: 15.441 s, 15.860 s, 15.510 s

Mutant: `server.server_close()` replaced by `pass` in `stop_host`: `FAILED (failures=5)`, five host=True tests with
"AssertionError: 0 == 0 : owned host listener answered; ...", GATE EXIT 1. Restored byte-exact: SHA-256 before and after
3801a7352cd9bf013cb74da65f7aa3dd8fb5710d2ab576702b5633d63b665220 (PYTHONDONTWRITEBYTECODE=1). A first mutation attempt
did not apply (my LF pattern vs CRLF file; assert stopped it, nothing ran mutated).
Not covered by any test: a dead probe (one that never connects, e.g. a wrong port or zero timeout) stays green.
Known (brief review Minor 2): on Windows a live-listener connect can rarely exceed 0.25 s, so the probe may miss a leak
about once in a thousand; Linux CI catches it.

Focused: `gate.sh focused test_r2_react test_support`: `Ran 44 tests in 30.455s`, `OK`, `GATE focused EXIT 0 IN 31s`.
`python -m ruff check tests/test_r2_react.py`: All checks passed. `git diff --check`: exit 0. Not run: full suite
(per override), `git diff --cached --check` (my change is unstaged by instruction).

Gross lines: 10 (5+/5-).

## Handoff
Phase b stacks on this delta. Commit subject `test: shorten two slow role test helpers`. Draft body:
  Windows returns a refused loopback connect only after the full
  timeout, so each owned stop waited 2 s. A listener answers in under a
  millisecond, so the no-listener probes now wait 0.25 s. The test hosts
  serve with a 0.01 s poll so shutdown returns promptly. The react
  module drops from about 41 s to about 15.5 s locally.

## Phase b (EFF5, `tests/test_studio_roles.py` builder)

Mode code, worktree a scratch worktree. Phase a staged, then the four patches applied with `--index` after SHA-256 checks
(w2sa 5d9db7f7..., w2sb 28d09c80..., w2pt-r1 ad79281c..., w2ps-r1 51c35012..., all matched).
Change: the linear `while measure(full + 1, 1, 1) <= size` became a bisection with a derived bound (double `over`
until `measure(over,1,1) > size`, then bisect); no constant; 6 added / 3 removed lines. Patch
`task-w2e-code-p2.patch`, SHA-256 `fb7df0fc2db79e824dc3a7e5f1578a2be11bb6950c10f7c8606ba04a860da662`, delta on the
staged state, `git apply --check -R` ok, `git diff --check` clean, ruff clean. Only `tests/test_studio_roles.py`.

**Triples (finding).** On this integrated tree (W2T+W2SA+W2SB+W2PT+W2PS+phase a) the new bisection returns
(494, 649, 1) for 1 MiB + 1 and (494, 648, 1) for 1 MiB. The linear search on the same tree (scratch run, restored)
returns the identical triples, so the bisection is equivalent to the old code here. The brief-review oracle
(494, 667, 1) / (494, 666, 1) was measured on W2T's tree alone; `full` (494) matches it, `first` differs by 18
because W2SB/W2PS change the envelope size by 18 bytes. I did not weaken anything: the oracle numbers are not
reproducible on the integrated tree, and the old algorithm is the true oracle there. Controller to decide whether
the 667/666 record needs restating.

**Mutants** (scratch edits of the test file, CRLF-exact, PYTHONDONTWRITEBYTECODE=1, SHA-256 before/after both
4e7aa9016ba527c0af31122cccd5ee2e87a455fd4320cdd024c07b8fcec43c6d):
- bisection returns `full + 1`: RED, `AssertionError: 1050008 != 1048577` and `!= 1048576` (both sizes fail).
- `full - 1`: stays GREEN (Ran 2, OK), triples (493, 1999, 729) / (493, 1999, 728); only the triple comparison
  catches it (equivalent for the test), as the brief review said.
- an asserted-triple scratch with the 667/666 oracle failed on this tree for the reason above (first differs).

**Focused**: `gate.sh focused test_studio_roles test_support`: `Ran 127 tests in 142.583s`, `OK`,
`GATE focused EXIT 0 IN 143s`. Timings of the builder: not separately timed; the one_mib pair runs in 2.4 s
(was 6.3 s with the linear search on the same tree).
Gross lines: 9 (6 added, 3 removed).
Commit body hint: bisect the largest full with a bound grown from measure; same shape, 26 calls instead of 994.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
