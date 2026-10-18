# R2.RV brief: the bridge advertises its role revision

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 25 (slice R2.RV, wave W0) and Addendum 26 item 1 (D075). BASE
`362ffd11e726011f3ca3c932e93a6e4c3d8c967d`. Worktree `C:/fks/trv` (detached at BASE; the controller creates it), task id
`rv`. Line budget: about 30 gross lines; explain any excess.

## Why

Studio cannot tell which role contract a bridge implements: `design:ready.capabilities` only says `roleDetection: true`
and `roleStylesheet: true` (`fontkit-bridge.js` 1210). Addendum 26 adds an integer revision so Studio can read replies
tolerantly and send only fields the bridge knows. The Studio side (R2.SK) refuses role support when the revision is
missing, so this slice lands first and every W1 slice starts from it.

## Owned files (exact)

- `fontkit-bridge.js`: only the `capabilities` object literal in the `design:ready` post (1210).
- `tests/test_bridge_runtime.py`: only the exact `ready['capabilities']` equality at 273-276.
- `tests/test_role_protocol.py`: one new test method in `RoleProtocolTests`, and nothing else.

Read-only: everything else, including `tests/role_contract.py` (R2.SK adds the revision row there) and `fontkit-studio.html`.

## Read first

`constraints.md` (all of it); the plan's Addendum 26 and "Messages" (the `design:ready.capabilities` paragraph); at BASE
`fontkit-bridge.js` 1195-1225, `tests/test_role_protocol.py` 1-80 and 120-140, `tests/test_bridge_runtime.py` 255-285.

## Requirements

1. `design:ready.capabilities` gains `roleRevision: 1`, beside `roleDetection` and `roleStylesheet`. No other field,
   message or behaviour changes. Oracle: Addendum 26 item 1, "The contract as shipped in 0.4.0 ... is revision 1".
2. `tests/test_bridge_runtime.py` 273-276: the exact capabilities dict gains `'roleRevision': 1`. This is a
   characterization update forced by requirement 1; name it in the report.
3. New test in `RoleProtocolTests` (`test_ready_advertises_role_revision_with_role_capabilities`, Given/When/Then
   docstring): on the real bridge, for each engine, after `self.hello(page)`, assert
   `ready['capabilities']['roleRevision'] == 1` with `type(...) is int` (a `True` must fail; Playwright returns a JS
   `1.0` as Python int, so do not claim to catch it), and the one-way rule: since `roleDetection` is advertised,
   `roleRevision` is present. Then send a second hello (re-greeting, as the existing
   tests do with `self.hello(page)` again) and assert the revision is unchanged.
4. The old-bridge case at `tests/test_role_protocol.py` 123-141 (`git show 6a7327bd:fontkit-bridge.js`) stays as it is
   and must still pass (it asserts no `roleDetection` and no `roleState`). Do not edit it.

## TDD

RED: run the new test at BASE; it fails on the missing key (quote the KeyError or assertion line). GREEN after
requirement 1. Mutants, each shown failing then restored byte-exact with SHA-256 before and after:
`roleRevision: 1` -> `roleRevision: true` (the new test fails on the type check); `roleRevision: 1` -> `roleRevision: 2`
(both the new test and the runtime equality fail).

## Focused command

```
cd C:/fks/trv && PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_protocol test_bridge_runtime.HandshakeTests test_support -v
```

During RED and the mutants, run only the new test for speed:
`python -m unittest test_role_protocol.RoleProtocolTests.test_ready_advertises_role_revision_with_role_capabilities test_bridge_runtime.HandshakeTests -v`
(same environment). Run the full focused command once on the final tree.
Also `node --check fontkit-bridge.js`.

## Handoff (for the landing)

Commit subject: `feat(bridge): advertise the role contract revision`. Draft a why-body (wrap at 72) and a ledger event
line in product terms (no process state).
