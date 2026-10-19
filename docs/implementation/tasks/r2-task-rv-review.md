### Spec Compliance
- PASS: Req 1. Only the `capabilities` literal changed in the bridge, gaining `roleRevision: 1` after `roleStylesheet` (fontkit-bridge.js:1210 in the patch). No other bridge line is touched.
- PASS: Req 2. tests/test_bridge_runtime.py:276 adds `'roleRevision': 1` to the exact dict; nothing else in that file changed. The report names it as a forced characterization update.
- PASS: Req 3. `test_ready_advertises_role_revision_with_role_capabilities` is in `RoleProtocolTests` (tests/test_role_protocol.py:12-25 in the patch), with a Given/When/Then docstring. It loops over ENGINES and calls `self.hello(page)`. It asserts roleDetection is truthy, the key is present, `type(...) is int` and `== 1`, then re-greets and repeats the type and value checks. The int type check is made with `assertIs(type(...), int)`, so `True` fails, and the test does not claim to catch a JS 1.0.
- PASS: Req 4. The old-bridge test is untouched in the diff and passes (see Checks).
- PASS: No file outside the three owned files changed (`git diff --cached --stat` shows exactly three files). Nothing was added beyond the brief.

### Checks run
- Checklist 1, drift. Addendum 26 item 1 (docs/plans/2026-10-03-r2-engine.md, line 611) says "roleRevision is a positive safe integer ... The contract as shipped in 0.4.0, design:roles-page included, is revision 1". constraints.md ruling 13 (D075) says "capabilities.roleRevision is 1". The code advertises integer literal 1, and the test asserts int type and value 1. The value and type agree with the plan. The "positive safe integer" range rule is a Studio-side validation concern (R2.SK). The bridge only emits the constant 1, so nothing is missing here.
- Checklist 2, mutants. I wrote a scratch script outside the repo (scratchpad/rv_mutant.py). It reads fontkit-bridge.js from C:/fks/trv, replaces `roleRevision: 1` in memory and passes the bytes through `RoleBridgeCase.open(bridge_source=...)` by wrapping `open`. Results on chromium:
  - control (no mutation): OK.
  - `roleRevision: true`: FAIL, `<class 'bool'> is not <class 'int'>`.
  - `roleRevision: 2`: FAIL, `2 != 1`.
  - key removed (renamed): FAIL, `'roleRevision' not found in {...}`.
  - `roleRevision: 1.5`: FAIL, `<class 'float'> is not <class 'int'>`.
  - value changing on re-greet (a counter): FAIL, `2 != 1`. This proves the re-greet assertion is live.
  - The frozen worktree stayed byte-identical: the SHA-256 of fontkit-bridge.js before and after is 913a4d0b27f45ce090fbd49abf9a0ff7564fa6af0e1d4a7274f5cc16cdedef35, which matches the report's hash. `git status` is unchanged. The `roleRevision: 2` runtime equality failure was not reproduced by me. It follows directly from the exact-dict `assertEqual`, and the report records it.
- Checklist 3, fake versus real. `RoleBridgeCase.open` without `bridge_source` injects `/fontkit-bridge.js` from REPO (= C:/fks/trv) into the target page (tests/role_support.py:49-56). `hello` is `page.evaluate('hello(s)')`. The test uses no fake bridge. The `bridge_source` route in my mutants did take effect, since the `true` mutant failed. That shows the real-bridge path is the one under test.
- Checklist 4, hidden skips. `grep skip` in tests/test_role_protocol.py and tests/role_support.py found nothing. The new test has no skip decorator and no engine gate beyond `ENGINES`. Hosted CI sets FKS_ENGINES: chromium or firefox (.github/workflows/quality-gate.yml:155,171,198,285,323), so it runs on those engines and skips none. Locally I ran chromium only, as the report states. Firefox and webkit were not run by me or by the implementer. That is a coverage gap to report, not a hidden skip.
- Req 4 and neighbours: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest ...test_unsupported_old_bridge_and_script_csp_remain_truthful ...test_ready_advertises_role_revision_with_role_capabilities test_bridge_runtime.HandshakeTests` -> Ran 4 tests, OK.
- `git diff --cached --check` -> clean. The line budget is 17 insertions and 2 deletions (19 gross) against about 30, so it is within budget.
- Checklist 5, tests.
  - Recorded mutant: the report records `true` and `2`, which the brief required, and I reproduced extra ones above.
  - Independent oracle: the expected value is the literal 1 from Addendum 26, not read from code.
  - Observable outcome: the test asserts the wire reply from the real bridge via the host's hello.
  - Given/When/Then: the Then reads "roleRevision is the int 1 beside roleDetection both times". The assertions are roleDetection truthy, key present, int type, value 1, on the first and second greeting. They match the Then.
  - Not a near-duplicate: the runtime equality test is existing characterization; the new test adds the type, one-way and re-greet checks.
- Checklist 6, code. Only the capabilities literal changed; budget kept.

### Strengths
- The type check is `assertIs(type(x), int)`, so `True` and floats fail, and I confirmed both by mutant.
- The re-greet assertion is proven live by a value-drift mutant.
- The change is minimal, with the byte-restore hash evidence recorded.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The one-way rule is asserted only for `roleDetection`. `roleStylesheet` is also advertised and Addendum 26 item 1 binds it as well ("advertises roleDetection or roleStylesheet also advertises roleRevision"). The brief said roleDetection, so the implementer followed it. A one-line `capabilities['roleStylesheet']` check is optional polish and not required.
- The report lists chromium only. The firefox and webkit engines were not run, and hosted CI runs firefox. The change is an engine-independent literal, so the risk is low.

### Plan-mandated (for the owner)
- [Minor] Addendum 25's R2.RV row (docs/plans/2026-10-03-r2-engine.md:591) does not name tests/test_bridge_runtime.py, though requirement 1 forces its exact-equality update. The brief owns the update, and the landing amends the row, as the dispatch context says. Brief requires: "`tests/test_bridge_runtime.py`: only the exact `ready['capabilities']` equality at 273-276."

### Assessment
**Task quality:** Approved
**Reasoning:** The bridge change is a one-literal edit that matches Addendum 26 item 1. The new test runs on the real bridge and I killed five in-memory mutants (bool, 2, key removed, float, re-greet drift) with the frozen worktree hash unchanged. It has no skips and its Then equals its assertions.
