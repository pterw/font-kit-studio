### Spec Compliance
- PASS: new file tests/test_friction.py only; nothing else owned or touched (patch stat, one new file).
- PASS: require_fixture first, node skipIf, bundle.js in setUpClass untimed (test_friction.py:41-45, 71).
- PASS: clock starts just before Popen with stdin=DEVNULL, --no-open, cwd fixtures/vite-react (:75-78); spawn/pump/stop copied, not imported; Ctrl-Break/SIGINT, kill on timeout (:55-68).
- PASS: reads to `Open: <url>`, https routes aborted before navigation (:88-95); clock stops after badge matches CONNECTED and TITLE is attached in #targetAppFrame (:99-108).
- PASS: stderr line `friction: X.X s (budget 60 s)` (:109); FRICTION_BUDGET_S = 60 with comment (:35-37); assertLessEqual with message naming both numbers (:111-113); badge wait 90 s, failure message carries badge text (:106).
- PASS: one test method, subTest per engine; cleanup through addCleanup.
- FAIL (against intent, not letter): with several ENGINES the one command start and one clock are shared, so a later engine's reported time is wrong (see Important 1).
- CANNOT VERIFY FROM DIFF: the three mutation runs (budget 0.1, pages? pattern, node_modules renamed). Their logic checks out on reading: budget assert at :111, wait failure at :98-107, require_fixture at :71. I did not re-run them.

### Checks run
- Green run -> `PYTHONPATH=tests python -m unittest test_friction -v` in C:/fks/t7a -> OK, `friction: 1.6 s (budget 60 s)`, nothing left running.
- Multi-engine clock -> read :75, :91-113 -> `started` is set once, `elapsed` is computed inside the engine loop from the same `started`.
- CI engine config -> grep FKS_ENGINES in .github/workflows/quality-gate.yml -> the jobs set chromium (lines 145, 233) and firefox (163, separate canary job). Which job will run test_friction is the controller's wiring (not decided here); default is chromium only.
- AGENTS rules -> no fixed sleeps, no page.content(), no writes to the fixture, https blocked, process stopped by handle in addCleanup. OK.

### Strengths
- Closed stdin plus a timed run makes a hidden prompt show up as a failure at the Open: wait or the badge wait, not as a hang.
- Budget miss and never-connected are separate failures with different messages (budget text vs badge text and process output).

### Issues
#### Critical
None.

#### Important
1. The clock is not per engine (test_friction.py:75, 91, 108). The implementer's concern is real. `started` and the single process are shared, so for engine N the figure is "command start to engine N connected", which includes engines 1..N-1 (page load, assertions, their cleanup) plus engine N's browser launch. It matters for the budget in two ways. The 60 s now is loose enough to hide it. But the budget is going to be reset to first green CI plus 50 percent, perhaps 5 to 10 s, and then a second engine (Firefox/WebKit launches are slow) can fail the budget with no real regression. The printed `friction:` line would also lie. It is not moot just because the default is Chromium: FKS_ENGINES is the repo's supported switch. Fix without leaving the brief: move the Popen/Open-line/clock into the per-engine loop, so each subTest starts its own command (brief: "run per engine in ENGINES"), with the stop in a per-engine cleanup. Or run only `ENGINES[0]` for timing. Either is small. Do not just add a comment: the number is wrong, not unclear.

#### Minor
1. Browser launch is inside the timed region on a first run (the lazy `new_context(engine)` at :93 comes after Popen). A user's browser is already open, so this adds noise to the figure the budget is derived from. Running `new_context` once before the Popen (or a warm-up page) would fix it. The brief lists the order, so the controller may want to rule on it.
2. The failure branch at :105 calls `text_content()` on the badge with Playwright's default 30 s timeout. If the badge is absent, that raises a second PlaywrightTimeout and the intended message (with process output) is lost. Pass `timeout=1000` or catch it.
3. The Open: wait at :84 reuses BADGE_WAIT_MS as a per-line timeout and does not notice the process exiting, so a command that crashes before printing waits up to 90 s with no time reported. Poll `proc.poll()` or break on EOF.
4. :110 `assertTrue(re.match(...))` is redundant after the wait and gives no message; use assertRegex.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The spec is met and the test is sound for the default Chromium run, but the shared clock gives wrong times for any later engine, and that will matter once the budget is tightened from CI. It is a small fix, so Approved with fixes is the controller's term for this verdict.
