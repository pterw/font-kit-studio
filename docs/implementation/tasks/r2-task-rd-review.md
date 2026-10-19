### Spec Compliance
- PASS: `### Detected roles` sits directly after `### Code panel` and before `### Arrange` (patch hunk at README.md 188-190 context). It carries intro, Requires line, Detect, bindings, adapters, Apply and Clear, receipts and losses, output boundary, visited pages, page changes, version differences and known limits.
- PASS: Revision 1 items I1-I5 are met. I1: "The panel is in the Live App view, below the preview. Before a page connects it reads `Connect a Live App to detect text styles.`" I2: seven-reason table. I3: entrypoint sentence claims only what the tests run (Vite 7 and 8 via the command, proxy with a policy that allows own scripts and inline styles, Next.js proxy, build ships nothing). I4: the `:root` block is written only when the role sets a family. I5: the stale "only accepts the values in the patch table above" (Security) and the inline-style line (Tailwind) are both fixed.
- PASS: Ruling 1 (line 44 keeps "0.3.0 or later", adds "need 0.4.0 or later"), ruling 2 (roadmap link, "not built"), ruling 3 (negative holds, see Checks), ruling 4 (no image link written).
- PASS: Only `README.md` and `packages/fontkitstudio/README.md` changed (`git diff --cached --name-only` in C:/fks/trd). CONTRIBUTING.md untouched; its only hit is the `supplied-v0.1.1` tag, which is true.
- PASS: Boundary. R3-R5 are never named as shipped. Roadmap reads "Font pairing, type scales and token output are not built" (matches product-direction.md R3 and R4). Roadmap and Known gaps link `docs/roadmap/product-direction.md`.
- NOTE (controller): `docs/roadmap/product-direction.md` lines 100-101 still say "Designed, not built: ... Role detection (R2)" and "Shipped (v0.2.1)". The README now links it next to "Role detection and preview ship in 0.4.0". Controller fixes at landing, as the dispatch states. Not a finding against this slice.

### Checks run
- Quoted-string verbatim (item 1) -> grep of Studio at BASE (`git show 5d28252:fontkit-studio.html`) lines 1250-1280, 3745-3761, 3874-3901, 4125-4131, 4202-4232, 4350, 4395-4413, 4498-4501, 4640-4668 -> all match, including `×` on the loss line (4413, README line 107 uses U+00D7), ASCII `x` on the "Different style on" line (4211, README line 132), `Light-DOM text only`, `Near duplicates (kept separate): ...`, `Safe complete bindings unavailable.`, `Shared classes:`, the four visited-page labels, the 8 s and stale Detect sentences, `Role preview; file output comes later`, `Reset all page edits`, and the seven loss reasons from `ROLE_LOSS_TEXT`. Exceptions are Minor 1 below.
- Fifteen-plus claims against source (item 1) -> bridge and Studio at BASE:
  - 2,000 ms, 10,000 elements, 128 groups, 8 variants, 200-char role name, 1 MiB reply (bridge 2054-2056, 2112-2131) -> true.
  - Near-duplicate thresholds: size 100 hundredths, weight 100, tracking 200 ten-thousandths (bridge 2144-2148) -> true.
  - 256 KiB request and 128 KiB sheet for `size-limit` (bridge 180, 296, 1532, 2001) -> true.
  - 250 ms coalescing (bridge 181); history wrapper limit comment (bridge 1368-1371) -> true.
  - 2,000-character route limit counts pathname + search + hash (bridge 1252, Studio 3793) -> true.
  - Field limits (Studio 3874-3879, `ROLE_NUMBERS`; bridge 245-250 rules) -> true.
  - Collection limits 128 roles / 32 pages / 32 selectors / 8 styles / 256 KiB, and Apply disabled until Clear (Studio 4190, 4350, 4159) -> true.
  - Clear keeps applied ids and counter, new origin restarts (Studio 4154-4161, Addendum 27 item 5) -> true.
  - Protocol rows: `design:detect` keys `requestId, documentId, knownRoles` (bridge 2002); roles-apply/clear keys (bridge 1531-1533); `roleRevision: 1`, `roleState` (bridge 1220-1221); six rejection reasons (plan 836-838, Studio 3896) -> true.
  - Panel placement: `#detectedRoles` follows the preview iframe and Changes panel in the Live App view (Studio 1213-1250) -> true.
  - 5,000 elements in 2 s on desktop Chromium (D058, plan 984) -> true as worded.
  - Strict `style-src 'none'` case (tests/test_r2_integration.py 625-645) and the proxy test with `style-src 'self' 'unsafe-inline'` (tests/test_r2_entrypoints.py:31) -> consistent with README line 31 and the Strict policies bullet.
- Heading-adapter sentence (item 6) -> bridge `bootstrapHeadingSelectors` 252-257, `roleCssBlocks` 315-323 (`ROLE_VARIABLES` has body and mono only), `suggestBootstrapAdapters` 1969-1990, D069 text "heading roles serialize as plain" -> TRUE. Heading binds a lone `.display-N` or one heading level (`hN` / `.hN`), and writes a plain rule with no `:root` block.
- Other adapter claims -> bridge 1411-1414 (evidence = both `--bs-body-font-family` and `--bs-font-sans-serif`), 1551 (adapter re-check at Apply), 269-277 (at most one body and one mono, body = exactly `body`), 1982-1990 (mono falls back to `code, kbd, pre, samp`), 1969 (author-role groups never qualify), D069 cost column (non-Bootstrap page with both variables is treated as Bootstrap 5) -> all true.
- Ruling 3, Sync and exports carry no role state -> grep of `rolePreview.css|roles` uses in Studio -> used only at 4032-4156 and 4383-4396; `liveCss/liveHtml/liveJson` (6576-6627) never read it; storage use is limited to kit ids (1296-1301) -> negative holds, no stop needed.
- Version skew sentence -> plan Addendum 26 items 1, 3, 4, 6 -> true, including the carve-out that echoed role values refuse on an unknown key.
- Coverage (item 2) -> `w3-known-limits.md` vs the patch -> all 4 Bootstrap items, history cache, `insertRule`, fullscreen/device width, session-only per-origin visited pages (no crawling), strict `style-src`, version skew, forwarder removal are present in user wording. Seven reasons present. Role revision 1 appears only in the Protocol table (Minor 4).
- Test-table completeness -> loop from the brief over `git ls-tree 5d28252 tests/` against the patched README (patch applied to a scratch copy named `rdrv-tree`) -> only `test_frontend_gate_helpers.py`, `_report.py`, `_runner.py` unlisted; the existing `test_frontend_gate_*.py` glob row covers them. Fifteen row clauses were compared with module docstrings (test_role_*, test_studio_roles, test_r2_*, test_release, test_localhost_cookies, test_studio_rename) -> each clause is supported by the docstring.
- Sweep (item 3) -> `grep -n -i` over the BASE README for versions, forwarder, role, inline, "only accepts", capabilities, "is now", "goes away" -> forwarder sentence, line 44, Protocol rows, test table (rename row), Known gaps, Roadmap, Patch keys, Security and Tailwind are all handled. Historical text (0.3.0/0.3.1 settings note, README 518 and package README 50; provenance links) is untouched. One sibling left, see Minor 3.
- Line endings and gates (item 5) -> Python byte count in C:/fks/trd: README.md 891 CRLF of 891 LF (pure CRLF); package README 0 CRLF of 64 (LF, as at BASE); `git diff --cached --check` rc=0; the forbidden-word grep shows only the pre-existing commit-message paragraph (README 862); the patch applies cleanly to the LF index copy. Tests that read README.md (`tests/test_live_integration.py:38`) take the script-tag and bookmarklet lines, which the diff does not touch.
- Anchors -> `### Detected roles` -> `#detected-roles` and `#### Preview, Apply and Clear` -> `#preview-apply-and-clear`; both resolve. The package README uses the absolute `https://github.com/pterw/font-kit-studio#detected-roles`, matching its existing link style. `docs/roadmap/product-direction.md` and `docs/plans/2026-10-03-r2-engine.md` exist at BASE.
- Process words (item 5) -> grep of added lines for R2-R5, D0xx, Addendum, slice, reviewer, model, agent -> none (only "rounded" matched "round").

### Strengths
- Every quoted Studio string matches BASE source character for character, apart from the two plural placeholders in Minor 1. The `×` / `x` split is correct.
- The report states where the code disagrees with the brief (checksum not shown, route-limit wording) and the README follows the code.
- Limits, reasons and thresholds are stated once and are checkable against named constants.
- The Security and Patch-keys corrections close the stale "patch table only" claim that the brief review flagged.
- No planning labels or process state in the README text.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. README.md "Receipts and losses" (patch line 97): the summary is quoted as `Preview applied to N role(s); M checked element(s) did not show it.` Studio prints "role" or "roles" and "element" or "elements" (Studio ~4650, `role${n === 1 ? "" : "s"}`), never "(s)". Write it as `Preview applied to N roles; M checked elements did not show it.` and say singular forms follow the count. The same goes for the rejection line: Studio appends a next-step sentence and detail after "the previous preview is kept." (`NEXT_STEPS`, `rejectionDetailText`), so the quote is a prefix.
2. README.md "Preview, Apply and Clear" (patch line 78): "The fields start empty and show the observed value as a placeholder." The Line height placeholder is the fixed text `e.g. 1.5` and the Case select shows `Unchanged (<observed>)` (Studio 4272-4285). Say "most fields".
3. README.md `design:reset` row (patch context line 177, "Removes overrides and undoes moves for one target, or for everything."): a global reset now also removes the role preview (plan 936-945; Studio 1278). The new "Reset all page edits" text is right, but this sibling row is now incomplete.
4. README.md "Version differences": does not name role revision 1 or say that a bridge advertising role capabilities without a valid `roleRevision` is treated as unsupported (Addendum 26 item 1). It appears only in the `design:ready` row. Coverage item 2 asks for "role revision 1" in the version-skew text. One clause would close it.
5. README.md "Visited pages" (patch lines 135): "Closing or reloading Studio forgets it. A same-origin reload, reconnect or pop-out keeps the list". The two "reload" uses mean different things (Studio vs the app). Write "reloading the app" in the second.
6. Style (AGENTS.md Markdown rules): the "Requires" paragraph (patch line 31) has a 50-word sentence and an unusual bold lead-in; "The heading `Role preview; file output comes later` is accurate." (patch line 123) says nothing a reader can use. Cut that sentence and split the long one.

### Plan-mandated (for the owner)
- None. Minor 1 follows the brief's literal `role(s)` text (brief Requirement 6: "`Preview applied to N role(s); M checked element(s) did not show it.` (4653)"), but the brief also says "Quote Studio's wording exactly". The implementer could have checked the source, so it stays under Minor, not here.

### Assessment
**Task quality:** Approved
**Reasoning:** I found no false factual claim in the added text. Quoted strings, limits, adapters (including the heading-adapter sentence, which D069 and the bridge both support), protocol rows, test-table clauses and the known limits all agree with BASE source and the plan. Line endings, anchors and owned-file scope are correct. The six Minors are polish and can wait for the landing pass.

## Scoped re-review (wording follow-up)

### Spec Compliance
- PASS: Minor 1 fixed as proposed. Summary now reads `Preview applied to N roles; M checked elements did not show it.` plus "role" and "element" singular at a count of 1 (README patch line 97). Rejection line keeps the Studio prefix and adds that `page-changed` and `revision-conflict` add a next-step sentence and any bridge detail (patch line 89).
- PASS: Minor 2 fixed. "Most fields start empty and show the observed value as a placeholder. Line height shows `e.g. 1.5`, and Case shows `Unchanged (<observed>)`." (patch line 78).
- PASS: Minor 3 fixed. `design:reset` row ends "A reset for everything also removes the role preview." (patch line 179).
- PASS: Minor 4 fixed. Version differences adds "Role messages use role revision 1. A bridge that advertises role capabilities without a valid `roleRevision` is treated as not supporting roles." (patch line 147).
- PASS: Minor 5 fixed. "Reloading the app, reconnecting or popping out on the same origin keeps the list" (patch line 135); Studio reload is now separate from app reload.
- PASS: Minor 6 fixed. "Requires" lead-in is now "It needs Studio and a bridge from 0.4.0 or later." and the long sentence is split; the useless "is accurate" sentence is removed (patch line 123).

### Checks run
- Truth of changed sentences -> `git show 5d28252:fontkit-studio.html`:
  - Summary (4653): `` `Preview applied to ${n} role${n === 1 ? "" : "s"}; ${lost} checked element${lost === 1 ? "" : "s"} did not show it.` `` -> matches, singular note true for both words.
  - Rejection (4661-4668): `` `Role preview ${op} rejected (${reason}); the previous preview is kept.${NEXT_STEPS[reason] || ""}${rejectionDetailText(data)}` ``; NEXT_STEPS has only `page-changed` and `revision-conflict`; detail is appended (4518-4522) -> true.
  - Placeholders (4281, 4286): `text("lineHeight", "Line height", "e.g. 1.5")` and `` `Unchanged (${observed.textTransform})` ``; other text fields use observed values (4277-4282) -> "Most fields" is true.
  - Reset (4551, 4684-4686): confirm text "...tokens and the role preview"; acknowledgement path installs empty roles "Role preview cleared by Reset all page edits." -> true. Button label `Reset all page edits` (1275).
  - Role revision -> plan Addendum 26 item 1 (lines 611-615): "contract as shipped in 0.4.0 ... is revision 1", and Studio treats a `design:ready` lacking a valid `roleRevision` as a bridge without role support -> true.
- Tests sentence split -> `git show 5d28252:tests/test_r2_entrypoints.py` -> all five entrypoint tests are named `*_detect_apply_rerender_clear` (Vite 7, Vite 8, Bootstrap proxy, Next proxy); the build test is separate. "The same steps" is true; Bootstrap "own scripts and inline styles" and "Next.js proxy" unchanged. No meaning change.
- Nothing else changed -> `diff task-rd-code.patch task-rd-code-r1.patch`. Hunks that differ: (a) index line (b) README.md patch line 31 Requires/tests paragraph (c) line 78 fields (d) line 89 Apply rejection (e) line 97 summary (f) line 123 heading sentence removed (g) line 135 visited pages (h) line 147 version differences (i) the Protocol-table hunk at 175-180: header shifts from -546,6 +682,9 to -544,8 +680,11 and gains context rows only because the `design:reset` row changed. The package README hunk (from line 274) is identical in both patches. No other differences.
- Working tree equals the patch -> `git diff 5d28252` of both READMEs in C:/fks/trd, CRLF stripped, md5 equal to `task-rd-code-r1.patch` stripped -> identical.
- Line endings -> Python byte count: README.md 891 CRLF of 891 LF (pure CRLF); packages/fontkitstudio/README.md 0 CRLF of 64 LF (LF). Both staged only; status shows no other files.

### Strengths
- Each fix quotes Studio exactly and is checkable at named lines.
- The report records its one deviation (splitting both sentences), and it is harmless.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
None.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** All six Minors are fixed as proposed, every changed sentence matches BASE Studio source and Addendum 26, the tests-sentence split keeps its meaning, no other hunk changed, and line endings are intact (README.md pure CRLF, package README LF).
