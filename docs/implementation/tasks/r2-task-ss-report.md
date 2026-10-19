# R2.SS code report (mode: code, worktree C:/fks/tss, BASE d49158b)

Patch: `.superpowers/sdd/r2c/task-ss-code.patch` (`git apply --check -R` passes). Files: README.md,
docs/assets/screenshots/capture.py, 9 changed PNGs, new detected-roles-desktop.png.

## What changed
- capture.py (+19 lines): new desktop scene after the guard scene's Escape. Mouse to (0,0); click Detect, wait by
  condition for `Detected N roles from` or `Incomplete detection`, retry up to 3 times; then wait for the summary
  `Checked on 1 visited page. Other pages have not been checked.`; hide `#roleRows`/`#roleInventory` items beyond the
  third (22 roles would make an 8,800 px image); scroll to top; `page.screenshot(full_page=True, clip=<panel box>)`.
- README.md: one image line after the first paragraph of `### Detected roles` (CRLF kept: 893 CRLF, 893 LF).

## Deviations (reality vs brief)
1. The first Detect after leaving theater mode always ended `Incomplete detection (page-changed)` (mouse move, waiting
   for theater class removal and frame load did not help); a second Detect is complete. The scene retries by condition.
   This may be worth a controller look: the page is still settling after theater exit (viewport change).
2. Element screenshot of the whole panel was 1408x8841 px (22 roles, sticky tabs over the top): unusable. The scene hides
   rows 4+ of the two lists (screenshot only, no Apply) and clips the panel via a full-page clip, which avoids the
   sticky tabs. The image therefore shows 3 of 22 roles; the status line still says "Detected 22 roles".

## Evidence
- Run: `python docs/assets/screenshots/capture.py`, exit 0, no output (no warnings; an earlier `\d` SyntaxWarning was
  fixed by `[0-9]`).
- Written files (bytes), all regenerated; "pixels changed" is true for each (git shows M): arrange-desktop 130709,
  arrange-guard-desktop 101214, arrange-mobile 33888, bridge-bar-desktop 12926, code-panel-desktop 17679,
  code-panel-mobile 51644, live-app-desktop 118645, live-app-mobile 61884, pop-out-desktop 104711, new
  detected-roles-desktop 147160 (1408x1754). Reason: stale v0.2.1/v0.3.1 label in BASE images (live-app, pop-out, and
  any with Studio chrome); I did not diff individual pixels per image, so which ones differ only by anti-aliasing or
  fonts is not separated out.
- Viewing detected-roles-desktop.png: panel from heading "Detected roles" with the Detect text styles button, status
  "Detected 22 roles from 63 eligible text parents on this page. Other pages have not been checked.", then three role
  rows (title role-1 "Halyard"; Text role-2 5 parents; Text role-3 5 parents) each with sample text, counts ("5 x
  system-ui..."), selectors, near-duplicates and the edit fields; then "Checked on 1 visited page. Other pages have
  not been checked." and three visited-page entries (/demo/). Nothing cut off, no sticky tabs, no hover ring. Studio's
  eyebrow is not in frame.
- `python -m ruff check docs/assets/screenshots/capture.py`: All checks passed!
- `git diff --check`: exit 0 (CRLF warning only). README pure CRLF: yes.
- `PYTHONPATH=tests python -m unittest test_live_integration.BookmarkletTests`: Ran 2 tests, OK.
- pre-commit (capture.py, README.md): trailing whitespace Passed, ruff Passed, JS syntax and static checks Skipped.
- Processes: script closes browser and serve.py in finally; work/ scratch removed. `tasklist` shows 9 chrome entries
  that I cannot attribute to my run (I did not record PIDs; likely the user's browser). No other action taken.

## Handoff
Subject: `docs: add a Detected roles screenshot and refresh the others`
Body: The README's Detected roles section had no picture of the panel,
and the existing images showed stale version labels (live-app-desktop
read v0.2.1). Add a capture scene that runs Detect on the demo app and
shoots the panel with role rows and the visited-pages summary, and
regenerate every image with the same script run.

## Controller integration
