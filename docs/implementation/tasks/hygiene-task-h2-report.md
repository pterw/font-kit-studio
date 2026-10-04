# H2 code report (mode: code, base c426172)

Files: scripts/serve.py, tests/test_preview_server.py, tests/test_live_integration.py.
Patch: .superpowers/sdd/hygiene/task-h2-code.patch (`git apply --check -R` passes).

## Steps
- RED on base: demo_offline `UnicodeDecodeError: 'charmap' ... 0x90`; lifecycle
  `ValueError: Unsupported signal: 2`; three `AssertionError: 1 != 0`; clipboard `\r\n` vs `\n` diff.
- Fixes applied as briefed: utf-8 reads/open files, `PYTHONIOENCODING=utf-8` (caller env still wins),
  `CREATE_NEW_PROCESS_GROUP` on nt, `stop()` sends `CTRL_BREAK_EVENT` on nt (commented),
  serve.py registers `getattr(signal, 'SIGBREAK', signal.SIGTERM)` (flat, one extra tuple member,
  with a comment), clipboard text `.replace('\r\n', '\n')` with Windows comment.
- CTRL_BREAK_EVENT reached the child here; no workaround needed.
- GREEN: `PYTHONPATH=tests python -m unittest test_preview_server -v` -> Ran 34, OK;
  clipboard test + test_support -> Ran 35, OK. Lifecycle class re-run after restore: Ran 10, OK.
- Mutation (SIGBREAK removed): 4 lifecycle tests FAIL `AssertionError: 3221225786 != 0`
  (0xC000013A, STATUS_CONTROL_C_EXIT: killed by Ctrl-Break). Restored.
- Not run: full suite, frontend gate (per brief). Firefox not exercised.
- `python -m ruff check` on the 3 files: 28 errors, none from this diff's lines as far as seen
  (pre-existing; ruff cleanup is another task). Not fully attributed line by line.

## Notes
- Working copy is CRLF (autocrlf); index is LF. I wrote LF; patch diff is clean (no whole-file churn).

## Anti-pattern self-review
- AP 13 (processes stopped): Server.close still stops via stop() with kill fallback; unchanged.
- AP 14 (not-run reporting): no skips added; unrun items listed above.
- No test weakened: only encodings, the signal delivery, and clipboard newline normalisation on
  the clipboard side only. Linux paths unchanged (creationflags=0, same signals).
- AP 15: no process state in docs.

## Handoff
Commit subject: `fix(dev): stop serve.py cleanly on Windows and make the suite pass there`
Body: serve.py now treats SIGBREAK like SIGINT and SIGTERM, the one graceful stop Windows
can send a child. The preview-server tests start the child in its own process group and send
Ctrl-Break on Windows, read files as UTF-8, and the clipboard test normalises the Windows
CRLF. This clears the six known Windows-only failures; Linux behaviour is unchanged.
progress.md event: "H2: the six Windows-only test failures fixed (UTF-8 reads, Ctrl-Break stop
with SIGBREAK handler in serve.py, clipboard CRLF); suite-a baseline on Windows is now empty."
Also: drop the "known Windows baseline" lesson once landed.
