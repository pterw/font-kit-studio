### Spec Compliance (re-review of Minors 1 to 4 and the no-token check)
- PASS 1: the badge tooltip is asserted exactly against NPX_BADGE_TITLE (tests/test_studio_npx_hints.py:120-121), and it is also in the no-serve.py/no-fontkit-bridge.js loop (122-124).
- PASS 2: the vacuous `#bridgeHintServe` assertion is gone. The hint is asserted by exact text (116), and the hint, Sync title and badge title are checked for no `serve.py` or `fontkit-bridge.js`. The dead `bridgeHintServe.hidden = true` remains in fontkit-studio.html:3843 (harmless, not asked about).
- PASS 3: the comment "Only the two hostnames are known..." now sits directly above `BLOCKED_LOOPBACK_TEXT` (fontkit-studio.html:3792-3793); the npx comment and constants are above it.
- PASS 4: the empty inspector message is `SERVED_BY_PACKAGE ? NPX_EMPTY_INSPECTOR : <old string>` (fontkit-studio.html:4938). The new text is "Enter the URL of a localhost app, then press Connect Live App. npx fontkitstudio adds the bridge to the page itself." It is plain, has no serve.py, and goes through the existing `escapeAttr` into the template. The constant is static, so no token content reaches HTML. Tests: package case asserts exact text with `target` renamed away (tests:128-139); no-token case asserts the old text exactly (OLD_EMPTY) via a 404-only plain server.
- PASS no-token bytes: `git diff HEAD -- fontkit-studio.html` in C:/fks/t8b shows the old strings only as unchanged context or as the else-branch literal, identical text for the Sync miss (5685-5686), the empty inspector (4939), the badge title (3692) and the `#bridgeHint` HTML (not in the diff). The no-token tests assert the Sync title, the hint and the empty inspector text exactly.

### Checks run
- `PYTHONPATH=tests python -m unittest test_studio_npx_hints -v` in C:/fks/t8b -> Ran 5 tests, OK. Nothing left running.
- Mutation results are from the report (token ignored fails both package tests, 2 failures); I did not rerun.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_npx_hints.py:126-127: two blank lines inside the class before the new test (cosmetic; ruff default passes).

### Assessment
**Task quality:** Approved
**Reasoning:** All four minors are fixed and tested; no-token strings are unchanged byte for byte, and the 5 tests pass.
