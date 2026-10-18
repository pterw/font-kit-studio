### Spec Compliance
- PASS: New scene runs after the guard scene's Escape, desktop only, Detect only (no Apply), waits by condition on `#roleStatus` and on `#roleVisited` === "Checked on 1 visited page. Other pages have not been checked." (capture.py:197-207).
- PASS: Mouse moved away before the click and again before the shot; panel clipped from the top of the page so the sticky tabs are not over it (capture.py:199, 211-214).
- PASS: Existing scenes untouched (diff of capture.py is one +19 hunk after line 195); servers/browser still closed in the existing `finally` blocks; loopback only (127.0.0.1 ports, localhost URLs); https guard route unchanged.
- PASS: README.md has exactly one added image line at line 195, after the first paragraph of `### Detected roles`; rest unchanged; file is CRLF (`file` says CRLF line terminators); `git diff --cached --check` clean.
- PASS (with Issue 1): the new PNG exists and was produced by the same run as the nine regenerated ones.
- FAIL: the alt text does not say the image shows a shortened list (see Important 1). Brief requirement 4 says "alt text says what is shown".

### Checks run
- Honesty of the new image -> opened C:/fks/tss/docs/assets/screenshots/detected-roles-desktop.png -> 1408x1754 panel: heading, Detect text styles button, status "Detected 22 roles from 63 eligible text parents on this page...", three role rows (title role-1; Text role-2 and role-3, each with selectors, "Near duplicates (kept separate): role-3, role-7, role-8, role-9, role-11, role-17, role-22" and edit fields), "Checked on 1 visited page..." with three entries (/demo/), Apply/Clear buttons, preview box, Reset. No sticky tabs, no hover ring, nothing cut off. Rows 4-22 are removed from the DOM view by `display:none` (capture.py:208-210); the status still says 22 roles and the near-duplicate lines name roles 7, 8, 9, 11, 17, 22 that are not shown. Studio eyebrow not in frame (fine).
- Retry (item 2) -> capture.py:200-207 and fontkit-studio.html:4431 -> Waits by condition (`wait_for_function`, POLL_MS), no sleep. Bounded: `for _ in range(3)`. No stale-text race: the Detect click handler sets status "Detecting text styles..." synchronously (html:4431) before the bridge reply, so on a retry the wait cannot match the previous "Incomplete detection" text. If all three fail, the following wait_for_function times out at Playwright's default 30 s and raises (loud, not silent). Fine.
- Other PNGs (item 3) -> opened live-app-desktop.png, pop-out-desktop.png, arrange-guard-desktop.png -> live-app shows eyebrow "FONT KIT STUDIO - V0.4.0", connected bridge, edited hero; pop-out shows the docked placeholder, 37 targets, top of Detected roles panel; guard shows theater mode, blocked-move warning. None blank, cut or showing a stray dialog.
- capture.py (item 4) -> `python -m ruff check docs/assets/screenshots/capture.py` in C:/fks/tss -> All checks passed. Scene adds 19 lines (brief said about 40).
- README (item 5) -> `git diff --cached -- README.md` with cat -A -> single `+![...](docs/assets/screenshots/detected-roles-desktop.png)` line plus its blank line, nothing else.
- Staged file list -> `git diff --cached --stat` -> README.md, capture.py, 9 changed PNGs and the new PNG; no stray files.

### Strengths
- The wait/retry logic is condition-based, bounded and does not race on stale status text.
- Scope is tight: one scene, one README line, only the allowed PNGs.

### Issues
#### Critical
None.

#### Important
1. README.md:195 (alt text) with capture.py:208-210 -- the image is a modified view that the alt text does not disclose. Rows 4-22 and visited entries 4-22 are hidden only for the shot, yet the visible status reads "Detected 22 roles", and the near-duplicate lines point at roles that are not in the image. A reader would take the three rows as the whole result, or wonder where role-7 is. Hiding rows is a reasonable way to get a README-sized picture (the full panel is about 8,800 px), so I do not rate the image itself misleading if the text is honest. Minimum fix: make the alt text say so, for example "The Detected roles panel after Detect on the demo app (first three of 22 roles shown): role rows with samples and counts, and the visited-pages summary". Alternative if the owner wants no editing of the view: clip only the top of the panel (heading, status, first row) without hiding anything, plus a separate crop of the visited-pages summary. The alt-text fix is one README line and stays within the brief's "exactly one new image line".

#### Minor
1. capture.py:208 -- the comment states the choice, but the report (not the README) is the only place the "3 of 22" fact lives; no caption sentence exists in the README either. The alt text fix above covers it.
2. Report claims "pixels changed: true for each" from git status only; per-image cause (version label vs font/anti-alias) is not separated. Sizes dropped 20-35% on most PNGs (e.g. arrange-desktop 175050 -> 130709), which suggests a different encoder or render, not only a label change. Images look correct, so this is a note only.
3. If all three Detect attempts end page-changed, the failure surfaces as a generic 30 s wait timeout, not a named error. Acceptable for a development script.
4. Report deviation 1 (first Detect after leaving fullscreen ends page-changed) is a product-visible behaviour that the controller may want to log (D063 / Addendum 27 item 6 already cover it); not a defect in this task.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The script, retry, regenerated images and README placement are sound, but the new README image shows 3 of 22 roles beside a "Detected 22 roles" status with alt text that does not say so. That is a user-facing honesty gap, fixed by changing the alt text.

## Controller fix at landing (2026-10-18)

Important 1 fixed by the controller as a one-line release-point doc edit (root CLAUDE.md: small, already-located doc
edits at a release point are done by the controller): the image's alt text now says the status line covers all 22
roles and only the first three role rows are shown, the rest of the list being cut from the image. No pixel or script
change. The four Minors are left as written in this review.
