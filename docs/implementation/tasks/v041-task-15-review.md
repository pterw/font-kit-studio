### Spec Compliance
- PASS: Req 1. LEGACY_TOKEN_KEYS is now '--font-sans', '--font-serif', '--font-mono', '--font-display', '--brand-canvas', in the original order; only lines 124-128 changed (fontkit-bridge.js:124-127).
- PASS: Req 2. The fixture has --accent-emerald in :root and the other names only under html[data-theme='x']. The test asserts the literal values 'Georgia, serif' and '#00aa66', and assertNotIn for the removed names (tests/test_bridge_runtime.py:343-357).
- PASS: Req 3. No other region, file, protocol version or export format changed. The worktree status shows exactly the three expected paths.
- PASS: Review fix 1 for four of the five names, and the controller accepted the deviation for --accent-emerald (see Checks). Re-adding any one of cyan, purple, editorial-size or mono-spacing fails the test. Review fix 2 is a commit-body matter, not in the patch; the report cites 3216.
- PASS: The fixture is a superset of the brief (extra names --accent-purple, --editorial-size, --mono-spacing). That is needed for fix 1 and has no side effect.
- CANNOT VERIFY FROM DIFF: the commit subject and body. Nothing is committed; the report states the subject and the three kept items.

### Checks run
- Removed names have no consumer -> grep of the worktree for the five names (excluding .git) -> hits only in the plan doc, the new fixture and the new test. None in fontkit-studio.html, README or other tests.
- Patch applies to BASE -> `git apply --check -R` against the worktree (HEAD 5443ff6) -> clean. The forward check was not run because the fixture is intent-to-add in the index. The worktree holds only the 3 expected paths and no stray file.
- Focused module -> `PYTHONPATH=tests FKS_ENGINES=chromium timeout 280 python -m unittest test_bridge_runtime` in the task's worktree -> Ran 129 tests, OK (134s).
- Break reproduction -> scratch copy scratch/t15-review/ (bridge + tests; support.py's REPO resolves to the copy, so the mutated bridge is what was loaded). Re-added each removed name alone after '--brand-canvas', one run per name:
  - '--accent-cyan' -> FAILED, "'--accent-cyan' unexpectedly found in {...}"
  - '--accent-purple' -> FAILED
  - '--editorial-size' -> FAILED
  - '--mono-spacing' -> FAILED
  - '--accent-emerald' -> OK (Ran 1 test). The report also says the old array restored all together fails with 4 subtests.
- Controller ruling on --accent-emerald -> confirmed true. The :root rule is read by getCurrentTokens' stylesheet collector (isRootSelector accepts :root; fontkit-bridge.js:3866-3875), so the name is reported whether or not it is in the list. Re-adding it is unobservable, so the deviation is genuine and is not a finding.
- Precondition -> the test asserts --font-display and --accent-emerald are present before the absence checks, so a page that fails to load or an empty tokens object cannot pass vacuously. The per-name subTest does not mask failures.
- Not run: test_role_detection, test_studio_roles, test_role_routes, test_r2_integration. None import a changed symbol (the only change is the LEGACY_TOKEN_KEYS array), so they are left to the wave gate.

### Strengths
- The test asserts the observable handshake `tokens.css`, per engine and per removed name, and fails for each of four independent re-adds.
- The positive assertions double as a precondition and a characterization of the kept path.
- The change is minimal and stays inside the owned regions.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The test's docstring and the fixture say "four other names", which is accurate. A reader will not see from the test why --accent-emerald is not in the absence loop. It is in the positive assertion and the fixture puts it in :root, so a one-line comment would help. Recorded only; no fix needed.

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The array edit matches the requirement exactly. The test observes the handshake and fails for each removable name when it is re-added. The --accent-emerald deviation is confirmed unobservable, as ruled.
