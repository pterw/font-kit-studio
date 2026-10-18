# R2.RV code report (mode: code, BASE 362ffd1)

Changed: fontkit-bridge.js (capabilities gains `roleRevision: 1`), tests/test_bridge_runtime.py (exact capabilities
dict gains `'roleRevision': 1`; characterization update forced by req. 1), tests/test_role_protocol.py (new
`test_ready_advertises_role_revision_with_role_capabilities`). 17 insertions, 2 deletions gross. Req. 4 old-bridge test untouched.

RED (at BASE source, new test): `AssertionError: 'roleRevision' not found in {'inspect': True, ... 'roleStylesheet': True}`.
GREEN after req. 1: `Ran 3 tests ... OK`.

Mutants (fontkit-bridge.js SHA-256 before 913a4d0b27f45ce090fbd49abf9a0ff7564fa6af0e1d4a7274f5cc16cdedef35, after identical):
- `roleRevision: true`: new test fails `<class 'bool'> is not <class 'int'>`.
- `roleRevision: 2`: new test fails `2 != 1`; HandshakeTests runtime equality fails too.
Note: my first sed restore converted the file CRLF to LF (hash differed); I re-added CRLF and the hash matches the
original. The working copy is CRLF, the index LF (autocrlf); the patch is normalized.

Focused: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_protocol test_bridge_runtime.HandshakeTests test_support -v`
-> `Ran 54 tests ... OK`. `node --check fontkit-bridge.js` ok. ruff on both test modules: All checks passed.
`git diff --cached --check` clean. Chromium only (FKS_ENGINES=chromium); other engines not run.
Patch: task-rv-code.patch (3 files above); `git apply --check -R` passes. pre-commit not run (not requested by dispatch).

## Handoff
Subject: `feat(bridge): advertise the role contract revision`
Body draft:
Studio could not tell which role contract a bridge implements.
design:ready.capabilities now carries roleRevision: 1, the revision
Addendum 26 assigns to the contract shipped in 0.4.0, so Studio can
read replies tolerantly and send only fields the bridge knows.
Ledger line: The bridge now reports a role contract revision (1) in its ready capabilities.

## Controller integration
