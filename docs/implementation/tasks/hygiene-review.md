### Spec Compliance
- PASS: H1 ruff. requirements-dev.txt pins ruff==0.16.10; ruff.toml has select ["F","E9"], py311, extend-exclude [".claude","work"]; CI step "Lint Python (ruff)" follows the static checks; the gate-list line is in AGENTS.md:118, CONTRIBUTING.md:19 and README.md:550 with identical wording; README CI paragraph (README.md:632) names it.
- PASS: H1 findings fixed: unused imports removed (test_studio_dead_controls, test_studio_visual), f-string without placeholder (test_bridge_runtime:1461), three dead variables removed.
- PASS: H2 serve.py: one tuple member added to the signal loop (scripts/serve.py:312-313), same handler, flat, commented.
- PASS: H2 test helper: UTF-8 on the stdout/stderr files, read_out/read_err and DEMO.read_text; PYTHONIOENCODING=utf-8 with the caller's env still winning; CREATE_NEW_PROCESS_GROUP on nt; stop() sends CTRL_BREAK_EVENT on nt with the required comment (tests/test_preview_server.py:72-117).
- PASS: H2 clipboard: CRLF replaced on the clipboard text only, with a comment naming the Windows clipboard (tests/test_live_integration.py:374).
- PASS: nothing added beyond the brief; no test skipped or weakened. The report's mutation (SIGBREAK removed gives 3221225786 != 0) is plausible and consistent with the code, not re-run by me.
- CANNOT VERIFY FROM DIFF: Windows green run of the six tests (gate-runners run the suite; the report gives Ran 34 OK).

### Checks run
- Risk 1, dead variables -> read all three tests at the staged version. `start` (test_bridge_runtime ~2867): never used later in the test (the test ends at reset-all, no `messages(..., start)`); `mark()` only reads log.length, no side effect. `studio` (dead_controls ~368): the test calls `get_by_role('button', name='Choose Studio')` directly twice, the variable was never read. `euro` (test_studio_live ~2471): the assertion uses the literal `'%E2%82%AC'` (line 2484), the variable was never read. None hid an assertion; the euro case is still asserted.
- Risk 2, SIGBREAK -> read serve.py:309-315; `hasattr(signal,'SIGBREAK')` is True here. On Linux the getattr fallback re-registers SIGTERM with an identical handler: harmless, idempotent. On Windows SIGBREAK is registered and the Ctrl-Break path sets `stop`, so the normal shutdown ("Stopped.", exit 0) runs; Ctrl-C (SIGINT) is untouched. Right behaviour; it is the only product change, as the plan's definition of done allows. The banner still says "Press Ctrl-C to stop." which stays true.
- Risk 3, helper -> read the staged helper. Callers of stop(): lines 491 (SIGINT then SIGTERM loop), 504, 531 plus close(). On Linux `creationflags=0`, `sig` is passed unchanged, so the SIGINT and SIGTERM iterations are still distinct. On Windows the loop sends Ctrl-Break twice, as the brief says. No leak: if the break is not delivered, `wait(timeout=10)` then `kill()` + `wait()`; close() calls stop() in `finally`. Process group isolation means the break does not reach the test runner.
- Risk 4, clipboard -> `shown` comes from `#liveCodeOutput` textContent (wait_code, test_live_integration:218-222), not normalized. A product change emitting CRLF in the shown text would make `shown` contain `\r\n` while the normalized clipboard would not, so it is still caught. Residual: a product bug that copies CRLF on Linux would now pass (see Minor).
- Risk 5, ruff -> `python -m ruff check .` -> "All checks passed!". `echo "import os" | python -m ruff check --stdin-filename x.py -` -> Found 1 error (the "deliberately unused import fails" criterion). `git ls-files -- 'work/*' '.claude/*'` -> empty, so the excludes hide no tracked code; both are untracked/gitignored (work/) or untracked (.claude/). requirements-dev.txt is installed in the workflow's "Install dependencies" step before the lint step. `git grep "node --check fontkit-bridge.js"` over live files: AGENTS.md, CONTRIBUTING.md, README.md (two places) all updated; no sibling gate list missed.
- Risk 6, UTF-8 on Linux -> explicit utf-8 on open/read_text equals the default on UTF-8 Linux and is stricter-correct elsewhere; PYTHONIOENCODING=utf-8 matches Python's UTF-8 default on Linux (and the C locale is coerced to UTF-8 since 3.7). Env construction `{**os.environ, 'PYTHONIOENCODING':..., **(env or {})}` replaces the earlier `None`-when-empty; the effect is identical apart from the new variable.

### Strengths
- The Windows fix keeps the test contract: the Linux code path is byte-for-byte the same signals and flags.
- Clipboard normalization is confined to the clipboard side, leaving `shown` strict.
- Cleanup path (kill fallback in stop/close) holds if Ctrl-Break fails.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_live_integration.py:374: the CRLF replacement runs on every platform, so on Linux a regression that put CRLF on the clipboard would no longer be caught. Guarding with `os.name == 'nt'` (or `sys.platform == 'win32'`) would keep Linux strict. The brief asked for the unconditional form, so this is a polish note only.
- scripts/serve.py:312: `getattr(signal, 'SIGBREAK', signal.SIGTERM)` is a compact trick; a reader must know the fallback is a duplicate. The comment helps; acceptable and as briefed.
- No CHANGELOG [Unreleased] line for the Ctrl-Break behaviour; not required by the brief.

### Plan-mandated (for the owner)
- [Minor] Unconditional CRLF normalization in the clipboard test (tests/test_live_integration.py:374) -- brief requires: "compare with `\r\n` replaced by `\n` on the clipboard text only, with a comment naming the Windows clipboard."

### Assessment
**Task quality:** Approved
**Reasoning:** Every brief step is implemented as asked, the three deleted variables were unused and hid no assertion, Linux behaviour is unchanged, the ruff gate works and its docs agree across AGENTS.md, CONTRIBUTING.md and README.md. Only polish notes remain.
