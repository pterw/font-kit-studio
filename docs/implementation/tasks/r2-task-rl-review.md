### Spec Compliance
- PASS: Studio title and eyebrow read 0.4.0 (fontkit-studio.html:6, :1014); label text only.
- PASS: bridge header line 3 reads 0.4.0 (fontkit-bridge.js:3); comment only.
- PASS: package.json version 0.4.0 (packages/fontkitstudio/package.json:3).
- PASS: vite-ts lock linked record 0.4.0, one value, hand edit (fixtures/vite-ts/package-lock.json:16); diff is exactly one line.
- PASS: new assertions in StructureTests.test_version_and_existing_model (tests/test_font_kit_studio_v011.py:534-539): bridge first 10 lines contain header, `const PROTOCOL_VERSION = 1;`, package.json version == 0.4.0. `REPO` added to the existing import line; no helper added.
- PASS: tests/test_studio_visual.py:470-471 updated to 0.4.0.
- PASS: deviation (Studio-source `version:"0.1.1"` assertion dropped) is allowed by the controller note and is covered at runtime (see checklist 3).
- PASS: staged set is exactly the six owned files; 14 added / 9 removed = 23 lines, within the 25 budget. No Markdown changed.
- PASS: git diff --cached --check clean; CRLF kept in the CRLF files (no stray \r in the patch; per-file diffs are 1-2 lines).

### Checklist
1. Labels and unchanged versions.
   - title/eyebrow/bridge header/package.json/lock: see Spec Compliance; `grep 0.3.1` over those five files plus tests/*.py returns nothing.
   - Cross-check that already exists in the package: scripts/versions.js checkVersions compares title, eyebrow and bridge header to package.json. I ran `node scripts/bundle.js` on a scratch copy and it printed "bundled Studio and the bridge at 0.4.0", so all three labels agree with the package.
   - Protocol 1: fontkit-bridge.js:76 `const PROTOCOL_VERSION = 1;`, asserted by the new line in test_version_and_existing_model (test_font_kit_studio_v011.py:537). Export format 0.1.1: fontkit-studio.html:3146 unchanged, asserted at runtime by test_font_kit_studio_v011.py:240 and test_studio_live.py:917.
2. Mutants, reproduced by me on a git checkout-index copy under scratchpad/rlrv_a (not the worktree). Baseline: 5 tests OK. Each mutant was reverted before the next.
   - bridge header 0.3.1 -> test_version_and_existing_model FAIL (header assertion).
   - PROTOCOL_VERSION = 2 -> test_version_and_existing_model FAIL.
   - lock 0.3.1 -> LinkedPackageLockTests FAIL (only that).
   - package.json 0.3.1 -> test_version_and_existing_model AND LinkedPackageLockTests FAIL.
   - eyebrow 0.3.1 -> VersionLabelTests FAIL (chromium).
   Note: the copy has LF endings (core.autocrlf=true on checkout-index), so my SHA-256 before/after differed after the first sed; content equals the worktree after stripping \r (diff clean). This is an artifact of my copy, not of the change.
3. Runtime pins: test_font_kit_studio_v011.py:240 `self.assertEqual(exported['version'], '0.1.1')` and test_studio_live.py:917 `self.assertEqual(exported['version'], '0.1.1')` both exist at HEAD and assert on a real export. The source-text assertion would add nothing they do not already catch. Confirmed.
4. cli.test.js: its `before` hook (test/cli.test.js:47-49) only asserts dist/fontkit-studio.html exists, which is why the worktree fails without a build. The version test (:161-163) uses `version` read from package.json via src/cli.js:8; nothing in src/test hard-codes 0.3.1 or 0.4.0 (grep empty). I ran `node scripts/bundle.js` then `node --test test/cli.test.js test/package.test.js` on the scratch copy: 34 tests, 34 pass, 0 fail. So the failure in the worktree is only the missing dist/, and the label change does not affect it.
5. Nothing beyond the brief: six files, no Markdown, no other lockfile touched.

### Checks run
- Focused command from the brief in C:/fks/trl -> 39 tests, OK (I ran it; no skip with FKS_REQUIRE_FIXTURES=1).
- Five mutants as above -> each fails the intended tests.
- Bundle + node tests on scratch copy -> pass.
- Grep for stale 0.3.1 in owned files and tests -> none.

### Strengths
- The protocol/format assertions are characterization and are placed in the same method as the label assertions, so a future label bump cannot silently move them.
- Lock edit is one value; LinkedPackageLockTests ties it to package.json.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- The title assertion stays an `assertTrue(... in source ...)` with a message; a failure prints only the message, not the actual title. Unchanged from BASE, not worth changing here.
- The implementer did not show the bridge-header and package assertions failing as a pre-edit RED (title fails first in the same method); their mutants (c) and (d) cover it, and I reproduced both.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** All five live labels are 0.4.0, protocol 1 and export format 0.1.1 are still pinned, the new assertions fail under every mutant I reproduced, and the diff is within the owned files and line budget. The cli.test.js failure is only the unbuilt dist/; with a bundle it passes.
