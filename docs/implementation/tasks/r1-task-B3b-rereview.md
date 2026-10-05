### Spec Compliance
- PASS (item 1): proxy.js:30-48 exports ProxyTargetError and parseProxyTarget; startProxy calls it (proxy.js:~70) with the same text, so B4's behaviour and tests are unchanged (npm test: 129 tests, 127 pass, 0 fail, 2 skipped). cli.js:~84 calls parseProxyTarget(url) before runProxy, so before any server starts. cli.js:~100 maps `instanceof ProxyTargetError` to 2. No message-prefix match remains: grep for "proxies only" in src/ finds only the one throw at proxy.js:45.
- PASS (item 2): `localhost:3000` and `ftp://x` get `fontkitstudio: "<arg>" is not a URL. Give your dev server's address, such as http://localhost:3000`, exit 2 (cli.js:~76-87). Test "an address that parses but is not http or https..." asserts the exact text and status.
- PASS (item 3): run-vite.js:266-275 throws `Font Kit Studio could not tell which address Vite is serving on.`, and the catch closes Vite then Studio in `finally`. The test in run-vite.test.js asserts the exact message, that Vite's close ran, and that the Studio port can be bound afterwards. Through main it falls to the generic path, exit 1.
- PASS (item 4): the 50 ms sleep is gone. cli.test.js startCommand/stop emits SIGTERM, reads the Studio port from the `Open:` line, then polls with `refused(port)` until a connect is refused, under a 5 s deadline that fails the test. The wait is an awaited condition, not a delay.
- PASS: nothing else changed. `git diff d58eb99` in C:/fks/tB3b is byte-identical to task-B3b-code.patch (compared with diff, CR stripped). The only additions beyond the first round are the proxy.js/proxy.test.js changes and the new cli/run-vite tests the fixes need.

### Checks run
- Item 1 by hand, dist/ renamed to dist.off in C:/fks/tB3b (restored afterwards; ls shows both files back):
  - `node bin/fontkitstudio.js http://example.com` -> stderr is exactly the refusal text, exit 2, no "cannot read Studio".
  - With a port I held (node net server, PID-less, self-exited after 8 s), `http://example.com --studio-port 51618` and `https://localhost:3000 --studio-port 51618` -> refusal text only, exit 2, no "busy" line.
  - `localhost:3000` and `ftp://x` -> not-a-URL message, exit 2, with dist/ absent.
  - Control: a valid `http://localhost:3999 --no-open` with dist/ absent -> "cannot read Studio ... run the bundle step", exit 1. So the dist/ error still fires, but only once a target is accepted.
- Patch equals tree -> diff of regenerated `git diff d58eb99` against the patch file -> empty.
- `npm --prefix packages/fontkitstudio test` (foreground) -> 129 tests, 127 pass, 0 fail, 2 skipped. Matches the report.
- dist/ is git-ignored -> `git check-ignore -v packages/fontkitstudio/dist` -> .gitignore:8.
- Side effect of mine: `git add -N .` in C:/fks/tB3b to produce the diff; git status afterwards is identical to before (the same two intent-to-add files). Nothing else was edited, and nothing in the main checkout.

### Judgement: the kept "bundle dist/ if missing" step in cli.test.js
Acceptable, no studioFile seam needed. The dist/ directory is git-ignored build output, `bundle()` is the same step that `prepack` and CI run, and it is guarded by `existsSync`, so it does not touch an existing build. The step is no longer hiding a defect: the refusal tests need no dist/, and "with no dist/ at all, a refused URL still exits 2" proves it on a copy of bin, src and package.json. Only the in-process tests that really start Studio need the bundle. A seam on main would add a production API parameter just to avoid writing an ignored file. Not worth it.

### Strengths
- The no-dist test runs a copy of the package without dist/, so the original ordering defect (Studio read before the target was checked) cannot return unnoticed.
- The busy-port test asserts the exact stderr equals the refusal alone, which covers both "no fallback line" and "no cannot-read-Studio line".
- Tying exit 2 to `instanceof ProxyTargetError` replaces a wording-coupled string match with a type, so a change to the message text no longer changes the exit code.

### Issues
#### Critical
(none)
#### Important
(none)
#### Minor
1. Whitespace-only line at cli.js:~86 (after `throw new Error('scheme');`) and a blank line before `} catch` at run-vite.js:~268. Cosmetic.
2. cli.test.js stop(): if the `Open:` regex fails to match, `studioPort` is 0 and the wait is skipped silently instead of failing. Both runners print that line with 127.0.0.1 today, so it is not reachable now. `assert.ok(studioPort)` would make it loud.
3. `--bogus --help` still exits 2 (carried over from the first review, Minor 1). Not part of this round.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** All four fixes are in and verified by hand against the real bin with dist/ removed, with the exit codes and texts specified. The suite is green (127/129, 2 skipped) and the tree equals the regenerated patch. Only cosmetic Minor items remain.
