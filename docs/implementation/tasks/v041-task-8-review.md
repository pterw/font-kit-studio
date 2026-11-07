### Spec Compliance
- PASS: Patches apply in order at BASE 5443ff6 (git archive export, `git apply --check` then apply for A1-3b, G2-7, D2-5). Files touched: fontkit-studio.html, tests/test_studio_npx_hints.py (line 116 only, plus one ERROR_PAGE constant), tests/test_studio_wording.py. No stray files, no CHANGELOG.
- PASS: Req 1. String 5 is appended after one space to `#bridgeHint` (html:1122, after the bridgeHintServe span, which now ends with "." per review fix 6) and to `NPX_BRIDGE_HINT` (html:4820). Verbatim against plan line 483. Badge text and BLOCKED_LOOPBACK_TEXT untouched; tests assert the badge literal by regex.
- PASS: Req 2 / Review fix 1. `kitStatus` shows string 7 on load (html:1802); `composerStatus` shows string 7 only when `loaded === ids.length`, else the old `Loaded n/m ...` (html:2392). Verbatim against plan line 485. Error texts unchanged.
- PASS: Req 3 / fix 5. `<div id="syncRoleNote" class="composer-status">` directly after `#syncToAppHint` (html:1195), no `hidden`, string 8 verbatim against plan line 486.
- PASS (placement question): `#btnSyncToApp` exists only at html:1191, in the Composer toolbar, and the note is the next sibling after its hint, in the same container. A user reading the Sync flow meets the button only in Composer mode, so the note shows exactly where the flow is. The Live App view has no Sync to Live App button (the other Sync, `liveCodeSync`, is Sync to file, CSS only, which the note does not describe). Not a defect. Plan row D2-5 says "the Sync wording" without naming a place; the brief's ruling 2 settles it.
- PASS: Review fixes 2-7: two-id held-route test with `content_type='text/css'`; end-of-text check on normalised text; shared-parent assertion; second patch-1 test kept with the Node reason in its docstring; sentence literals defined per module (ERROR_PAGE in both the wording and npx-hints modules).

### Checks run
- Patch order/apply -> scratch git export of 5443ff6, three `git apply --check` + apply -> all applied.
- New strings 5, 7, 8 -> compared patch text with plan lines 483, 485, 486 -> identical.
- Focused tests, chromium, one at a time: test_studio_wording 6 OK; test_studio_roles 114 OK; test_role_routes 52 OK; test_r2_integration 29 OK. Left for the wave gate: test_studio_npx_hints, test_studio_first_run, test_support, test_live_integration, test_studio_live (implementer reports 5, 24, 34 OK).
- Break reproduced -> scratch copy of the worktree (scratch/t8-review, since deleted), removed string 5 from the served `#bridgeHint` and added `hidden` to `#syncRoleNote`, ran test_studio_wording -> exactly the served-hint test and the sync-note test FAILED; the others passed. The mutated html is what the tests load (APP is built from REPO/HTML in the copied tree; the failures prove it).
- Boundary rule -> no bridge or protocol change; all new text is static markup or `textContent`.

### Strengths
- The two-id test waits for `Loaded 1/2 Adobe kit stylesheets.` before releasing the second route, so an unconditional string 7 fails it.
- The served-hint test uses an end-of-text check, so appending in the middle fails it.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The disk-opened hint (span shown, ending "...serve.py</code>. If this is an error page") has no test; the "." is only exercised by markup. Recorded, no fix needed.
- Composer partial/final status could reset to the `Loaded n/m` text if kits load out of order after an error; unchanged behaviour at BASE, not caused by this task.

### Plan-mandated (for the owner)
- [Minor] Plan Task 8 lists `test_studio_first_run`, `test_live_integration`, `test_studio_live` hint assertions as needing edits; at BASE they are assertIn on the unchanged prefix and need none (brief already says so). Not a defect in the implementation.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** All three requirements and the seven review fixes are met with verbatim strings; patches apply in order; the new tests fail under the named breaks and the four regression modules I ran pass.
