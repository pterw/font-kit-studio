# Task 18 code report (docs only)

Mode code, BASE c0c4af6, worktree the task's worktree. Task 17 (39e5b41) is in the log. Nothing staged or committed.
Patch: task-18-code.patch (README.md, CHANGELOG.md; 21 insertions, 4 deletions). CRLF unchanged.

Per requirement (all done, all in README.md unless noted):
1. Tailwind bullet rewritten (bridge 2421-2425 text and trigger).
2. design:warning row lists four kinds, additive, protocolVersion 1. Per Review fix 1, edit-not-reapplied says auto-id element; edit-reapply-stopped says only that the page keeps re-creating an element (no auto-id claim).
3. Error-page bullet in "If Studio does not connect" (proxy.js isTaggable, statusCode 200).
4. Clear row: "A stale `pageVersion` is not a reason to refuse it." No "only". No other README sentence says Clear is refused for page-changed (grep: lines 233, 265, 338 concern Detect/Apply/resizing).
5. "Tested on." paragraph before Firefox status; link target exists.
6. Next.js paragraph ("seen once", no D-number).
7. `stat` sentence in Marking up (stat-title not listed); bridge line 120, AutoSelectorWholeNameTests at tests/test_bridge_runtime.py:3736.
8. Known limits bullet for a page that never stops changing.
9. Reapply bullet extended into three new Known gaps bullets (state-class move, B08/D2-11, B09).
10. CHANGELOG: the Clear and the three earlier lines already existed except three; added the a3050d3 (with Review fix 2 reason: "repair the markup differently"), f620df0 and 84df677 lines, before the existing Clear line (commit order). The Task 17 line was already present, so not duplicated.

Checks: git diff --check clean; no 0.4.2/Task/D-number in added lines; pre-commit (python -m pre_commit) hooks Passed; `PYTHONPATH=tests python -m unittest test_release test_support`: Ran 60, OK. test_live_integration reads README code fences only; fences untouched, not run.
Open questions 2-4 followed the controller rulings (nothing added to README for leave prompt or restore-text; no 310ad2b line).

Handoff: commit subject `docs: describe the 0.4.1 repairs and their limits`; body per brief; no log entries from me.
