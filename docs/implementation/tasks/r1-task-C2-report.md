# C2 code report (Codex review fixes for B5; mode: code, base 7376bd2, worktree C:/fks/tC2)

Patch: `.superpowers/sdd/r1-pr-b/task-C2-code.patch` (`git diff 7376bd2`, LF). Nothing committed.
Files: src/run-proxy.js (+hash), src/open-browser.js (exit handling, once-only), test/run-proxy.test.js (+1 test),
test/open-browser.test.js (+4 tests).

## Changes
- (a) `studio.url(proxy.origin + pathname + search + hash)`: a hash route reaches Studio's `target`.
- (b) `report()` writes the could-not-open line at most once; called on `error` and on `exit` with a nonzero code or a
  signal. `detached`, `stdio: 'ignore'`, `shell: false` and `unref()` unchanged.

## RED (source files restored to HEAD, new tests kept)
`node --test --test-force-exit test/open-browser.test.js test/run-proxy.test.js`: `ℹ pass 13 / ℹ fail 4`:
`keeps a hash route in the proxied target`, the exit-1 and SIGTERM open-browser tests, plus the SIGINT test as a
cascade (the failed hash test leaves its run open, so the listener count is off). The exit 0 and error-then-exit
tests pass at HEAD by design (they guard against over-reporting).

## GREEN
`npm --prefix packages/fontkitstudio test`: `ℹ tests 204 / ℹ pass 202 / ℹ fail 0 / ℹ skipped 2`.

## Mutations (foreground, restored by copy)
- report on every exit (`if (code !== 0 || signal)` -> always): open-browser test `stays silent when the command exits 0` fails (`ℹ fail 1`).
- remove the `if (reported) return;` guard: `reports once when error is followed by exit` fails (`ℹ fail 1`).
- Hash: covered by the RED run (restoring HEAD's run-proxy.js).

## Note
An early run failed at file level because a `\n` inside my script became a real newline in a string literal
(SyntaxError); fixed before the RED/GREEN runs above. No processes left running.

## Handoff
Commit subject: `fix(dev): keep hash routes and report a browser that would not open`
Body draft: The Studio target dropped the URL fragment, so a hash-routed app opened at its root instead of the
requested route; the fragment is now kept. A browser command that starts but exits nonzero (xdg-open with no browser,
SSH, containers) printed nothing because only spawn errors were handled; it now writes the same one-line hint, at most
once per call.
progress.md line: `C2: Studio target keeps the hash route; openBrowser reports a command that exits nonzero or by signal, once.`


## Landing (controller, 2026-10-04)

Review (`r1-task-C2-review.md`): Approved, three minor findings. Fixed at landing: the hash test closes its run in `finally`, so a failing assertion cannot leave the proxy and Studio running (anti-pattern 13). Kept: a message literal repeated in the opener test; an `xdg-open` that exits 0 without opening a browser cannot be detected. Node tests on Windows: 204 run, 202 pass, 2 skipped.
