# Task 10 code report (mode code, BASE 5443ff6, worktree the task's worktree)

Patch: task-10-code.patch (git diff, 6 files, +167/-6; nothing committed or staged; line endings kept as the files have them).

## Changed
- fontkit-bridge.js: `postWarning(kind, targetId, message, requestId = null)` after `noteRuntimeError`. Kinds list is inline in the method (no new constant, so no line outside the region). Posts nothing without `studioSource`, for a kind other than the three, or a non-string/empty message. `targetId` = non-empty string else `'global'`; `requestId` = string else `null`; message cut to `WARNING_MAX_LENGTH`.
- fontkit-studio.html (`noteWarning`, `renderWarnings`, `warningLabel`, one `WARNING_KINDS` const above `noteWarning`): accepts the four kinds, stores `kind`; banner `Note from the Live App[ about <name>]: <message>` for new kinds, runtime-error text byte-identical; list aria-label `Notes from the Live App` when the list is non-empty and holds no runtime-error, else `Runtime warnings from the Live App` (also when empty after Dismiss). `warningLabel` uses `Object.hasOwn`.
- fake-target.html `fake.warn(message, targetId, requestId, kind = "runtime-error")`.
- Tests: `PostedWarningTests` (3 tests) in test_bridge_runtime.py; `LiveAppNoteTests` (3) in test_studio_live.py; `StudioPostedWarningTests` (1) in test_studio_roles.py (after the role boundary class, before `FnvVectorTests`).

## Tests run (chromium, one module at a time)
- test_bridge_runtime.PostedWarningTests + RuntimeWarningTests + test_support: Ran 39, OK.
- test_studio_live.LiveAppNoteTests + the existing runtime-warnings Arrange test + test_support: Ran 38, OK.
- test_studio_roles.StudioPostedWarningTests: Ran 1, OK. ruff on the three test files: pass. `git diff --check`: clean.
- Not run (controller): test_role_routes, test_r2_integration, rest of test_studio_roles.

## Breaks shown failing (mutated file is what the browser loaded; each restored, tree re-verified green)
- drop `.slice` -> cap test fails; drop kind check -> unknown-kind test fails; drop 'global' fallback -> global/null test fails; default `requestId` undefined, or pass requestId through unchecked -> global/null test fails.
- Studio: drop `token-not-applied` from the set -> note test errors; label from first entry only -> runtime-label test fails; drop `Object.hasOwn` -> note test errors (`constructor`/`__proto__`); `innerHTML` for list items -> roles test fails; replace allowlist with a string check -> roles test fails (the test posts `made-up`/`constructor`/`__proto__` straight through `bridge.post`, so Studio's own check is exercised, not only the bridge's).
- Mutation harness: scratch/task-10-mut.py. No RED run at BASE was done separately; methods/kinds do not exist there.

## Notes
- Brief said `postWarning` gets an omitted/non-string requestId as `null`; an empty-string requestId is a string and passes through (spec: "the given string").
- Roles test reads the list via `text_content` and waits on list length: `#liveCodeWarnings` text and the stale banner text after Dismiss otherwise misled waits.
- Name oracle in the Studio test is `#liveTargetName` (page-read).

## Handoff
- Commit subject (ruling 3): `fix(bridge): carry three more warning kinds to Studio`. No CHANGELOG line (brief); frozen sender signature unchanged for Tasks 11/12.

## Follow-up: Given/When/Then docstrings
- Added a Given/When/Then docstring to each of the 7 tests this task added: 3 in `PostedWarningTests` (test_bridge_runtime.py), 3 in `LiveAppNoteTests` (test_studio_live.py), 1 in `StudioPostedWarningTests` (test_studio_roles.py). No assertion or code changed; fontkit-bridge.js and fontkit-studio.html untouched.
- `git diff --stat` before: tests +51 / +56 / +35 (167 insertions, 6 deletions in total). After: +60 / +65 / +39 (189 insertions, 6 deletions in total). The other three files are unchanged. The extra 22 lines are all docstrings; `git diff --check` clean; the files keep CRLF endings.
- `python -m ruff check` on the three test files: All checks passed. No browser run, since only docstrings changed. No patch written, per the brief.
