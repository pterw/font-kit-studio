### Spec Compliance
- PASS: Req 1, the measuring covers the token writes only. `before` is taken at fontkit-bridge.js:2376 (patch line "const before"), before `patch.tokens` and the four shortcuts. `after` is taken once, before the "// 2. Live Movement" comment. No movement or slot restyle enters the comparison.
- PASS: Req 2 and review fix 1. A name counts only if `setToken` returned a value, it differs from `tokenOverrides.get(name)`, it is one of the four Studio names, and it is not already in `written`. The warning goes through `postWarning('token-not-applied','global',msg,data.requestId)`, once, before `acknowledge`. The message equals New string 1 with names joined by ", ". My probe confirmed the warning precedes `design:applied` on the wire.
- PASS: Req 3 (unchanged values skipped) and review fix 3 (third Sync names only the changed token).
- PASS: Req 4. `target.html` Sync posts no warning, and the h1 family differs before and after.
- PASS: Req 5. Replies, `canonicalPatch`, the ledger and the write order are unchanged. `computedFontFamilies` only reads. `postWarning` is untouched.
- PASS: Owned regions. The edits sit in the 1-to-2 span of `handleCompositionUpdate`, the new method directly after `removeToken`, the new fixture (16 lines) and the new class directly after `LegacyCompositionTests`. The method is named for what it does, per review fix 4.
- PASS: Patch. With a temporary index holding `task-10-code-r1.patch` on 5443ff6, `git apply --check --cached task-11-code.patch` succeeds. The patch equals the worktree's unstaged `git diff` byte for byte and has no stray file. The commit subject given in the report is clean (56 characters, no process state).
- PASS: Report states the accepted limit (fix 6), the Task 4 adjacency (fix 5) and the test 4 deviation (fix 3).

### Checks run
- Patch applies on task 10 r1 -> temp index in C:/fks, `read-tree 5443ff6`, `apply --cached` r1, `apply --check --cached` task 11 -> OK. I removed the temp index file afterwards.
- Focused module (brief's command, minus test_support) -> TokenNotAppliedTests + LegacyCompositionTests + TokenRemovalTests on chromium -> 11 tests OK.
- Regressions -> `test_studio_roles` 115 OK, `test_role_routes` 52 OK, `test_r2_integration` 29 OK. These are one module at a time on chromium. I did not run `test_bridge_runtime` in full, or other engines; those are for the wave gate.
- Sync must not stop (your named risk) -> scratch probe `scratch/t11-rev/probe.py`, run against the task's worktree -> on the terminal page, syncs of `{}`, `{'slots': []}`, `{'tokens': {}}` and `{'tokens': {'--editorial-size': '20px'}}` all reply `design:applied`, with no warning and no page errors (`window.__errors` empty). A four-name Sync: the `design:warning` index is before the final `design:applied`, with no page errors. A null removal (`--font-sans: None`) after a warned Sync still replies `design:applied` and adds no warning.
- Mutation (scratch copy `scratch/t11-rev/repo`; PYTHONPATH pointed at its tests, and each mutant file was re-read to equal what I wrote) -> 13 mutants against TokenNotAppliedTests:
  - KILLED: never post (4 failures), second pass after slots, drop changed-value filter, drop name filter, `if (true)` guard (2 failures), always warn, length-only compare, first-element-only compare, empty `before`, wrong targetId, null requestId, join separator.
  - MISSED: dropping `!written.includes(name)`. See Minor 1.
- Reproduced a named break myself: the "second pass after slot loop" mutant fails the slot test, as the brief's oracle requires.

### Strengths
- The measurement point is correct and the slot test proves the restyle happened (Courier computed) while the warning still fires, so the ordering oracle is real.
- The compare is strict across every element, and it mutated dead when weakened (length-only, first-only).
- Sync behaviour with no tokens is unchanged: the acknowledgement arrives and there are no page errors.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. Review fix 1 says each name counts once when `patch.tokens` and the shortcut both send it. No test guards this (mutant `no_dedupe` MISSED). It matters only when the two carry different values for the same name (for example `tokens['--font-sans'] = A` plus `sans = B`): then the message would repeat the name. Studio does not send that today, and the warn decision is unaffected. One extra assertion would close it.
2. `computedFontFamilies()` runs unconditionally at the top of every composition Sync, including ones with no tokens (slots-only). Brief Req 3 says a Sync without changed tokens "need not measure". The cost is one 15-25 ms pass per 5,000 elements, and ruling 3 and the report already state it. It is not a defect, only wasted work on slot-only Syncs.
3. The `before` pass has no try/catch. A throw in `getComputedStyle` would stop a Sync before any write, but I found no realistic path to one.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The measuring sits strictly around the token writes. The warning is correct, fires once, and precedes the acknowledgement. Sync with no tokens still acknowledges, and the three Studio regression modules pass. The tests killed 12 of 13 candidate defects. The one missed (name de-duplication) is Minor.
