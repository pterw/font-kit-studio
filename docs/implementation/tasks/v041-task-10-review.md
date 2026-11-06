### Spec Compliance
- PASS: Req 1 sender. `postWarning(kind, targetId, message, requestId = null)` sits directly after `noteRuntimeError`; posts `{type, requestId, targetId, kind, message}` via `this.post`; cap `WARNING_MAX_LENGTH`; kind allowlist of the three; no studioSource -> nothing (via `post()`'s `studioAlive`, same as noteRuntimeError); review fix 2 rule (`targetId` non-empty string else 'global'; non-string/empty message posts nothing; non-string requestId -> null) (fontkit-bridge.js diff @2259-2271). `noteRuntimeError` untouched.
- PASS: Req 2/3/4 Studio. `WARNING_KINDS` (4 kinds), `kind` stored, unknown kind / empty message still ignored; banner `Note from the Live App[ about <label>]: <message>` for new kinds, runtime-error string byte-identical; aria-label `Notes from the Live App` only when list non-empty and has no runtime-error, else the old label, including empty after Dismiss (fontkit-studio.html diff @6399-6430). `warningLabel` uses `Object.hasOwn` (review fix 4). Dispatch case and markup untouched.
- PASS: Req 5 unchanged (300 cap, MAX_WARNINGS, Dismiss, textContent, session check). README/visual-test "Runtime error in the Live App" assertion text unchanged.
- PASS: Owned regions. Only the owned files are in the patch; test classes are placed where the brief says; `fake.warn` gains the `kind` parameter only. Patch `git apply --check` is clean against BASE 5443ff6 (checked on a `git archive` copy; the worktree already holds the changes); `git diff --check` clean; no stray file; nothing committed.
- PASS: Review fixes 1-4 present (roles test with hostile text, 900-char cap, `made-up`/`constructor`/`__proto__`, forged `fks-wrong` session; 'global'/null bridge test; list-holds-both-entries and empty-after-Dismiss label; `constructor`/`__proto__` targets in the name test).
- CANNOT VERIFY FROM DIFF: commit subject (nothing committed). Handoff gives `fix(bridge): carry three more warning kinds to Studio`, which matches ruling 3 and carries no process state.

### Checks run
- Focused modules (chromium, timeout each): PostedWarningTests + RuntimeWarningTests -> Ran 5, OK. LiveAppNoteTests + existing Arrange runtime-warnings test -> Ran 4, OK.
- Regressions the implementer left: `test_studio_roles` (all) -> Ran 115, OK. `test_role_routes` -> Ran 52, OK. `test_r2_integration` -> Ran 29, OK. Left for the wave gate: `test_studio_visual`, firefox/webkit engines, `test_bridge_runtime` beyond the two classes, `test_role_detection`.
- Mutants on a scratch copy (scratch/t10-rev; script scratch/task-10-rev-mut.py; the mutated file is the one the test loaded, since the harness edits the copy it runs in and restores it): drop kind check -> KILLED (unknown-kind test); drop slice -> KILLED (cap test); drop `edit-reapply-stopped` from the bridge list -> KILLED; requestId passed through unchecked -> KILLED (global/null test); non-string message accepted -> KILLED; Studio accepts any string kind -> KILLED (roles test); Studio drops a kind -> KILLED; label `every`->`some` -> KILLED; label ignores empty list -> KILLED; banner always "Runtime error" -> KILLED; "about" always shown -> KILLED. MISSED: drop the bridge's own `!this.studioSource` check -> equivalent, because `post()` returns on `!studioAlive()`; the test still covers the studioSource-null path end to end.
- Older Studio (D079): the BASE Studio's `noteWarning` returns for any kind other than `runtime-error`; also ran the new bridge against the BASE `fontkit-studio.html` with the roles test -> the list never gets an entry (30 s wait timeout), so the kinds stay silent and nothing throws.
- Global rule 5 / boundary (real Studio + real bridge): `StudioPostedWarningTests` runs `StudioRoleCase`, hostile `<img onerror>` text per kind, asserts text in banner and list, zero `img`, `window.__xss` undefined, 900 -> 300, and sends `made-up`/`constructor`/`__proto__` straight through `bridge.post` so Studio's own allowlist is exercised and not only the bridge's; forged `fks-wrong` message from the real frame is shown nowhere. The test dismisses first, so the "nothing shown" part starts from an empty list. innerHTML and allowlist-removal breaks are reported killed by the implementer; I reproduced the allowlist one. `typeof`/`includes` on an Array means `constructor`/`__proto__` kinds cannot hit the prototype.
- Wrong-origin and wrong-source cases for `design:warning` are not added by this task; they are the unchanged session check, covered elsewhere.

### Strengths
- The Studio allowlist is tested on its own, not hidden behind the bridge allowlist.
- Name test includes prototype-key targets, and the label state is asserted for mixed and empty lists.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The new tests carry no Given/When/Then docstring, though the plan's global constraint asks for one on each new test (the sibling roles tests have them; `RuntimeWarningTests` does not). Docstrings would be plain additions. (tests/test_bridge_runtime.py PostedWarningTests, tests/test_studio_live.py LiveAppNoteTests, tests/test_studio_roles.py StudioPostedWarningTests)
- `README.md:719` still says `design:warning` is only `kind: "runtime-error"` (anti-pattern 11). Not an owned file and nothing sends the kinds yet; it must be settled by the task that owns the README/ledger before the 0.4.1 release.
- The name oracle in `test_each_new_kind_shows...` is `#liveTargetName`, read from the same Studio metadata as the banner; it would not catch a wrong name used in both. The `constructor`/`__proto__` cases do pin the fallback.
- The kind list is an array literal rebuilt on each `postWarning` call; harmless.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The channel matches the frozen signature and the review fixes; the real-Studio hostile test kills the allowlist and textContent breaks, and the Studio, role-routes and R2 regressions I ran are green. Only polish items remain.
