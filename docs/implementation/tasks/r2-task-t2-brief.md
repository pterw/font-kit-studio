# R2.T2 brief: handshake-order tests

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.T2 and Addendum 19. PR B2, wave W0 (beside R2.C0, disjoint files). BASE
`e2098ac0c97642b8315ea77fb7b3eb053868a7a1` (adds Addendum 19 and task R2.T2). Worktree `C:/fks/tt2` (detached at BASE; the
controller creates it), task id `t2`. Line budget: about 120 gross lines (insertions plus deletions); explain any excess.
This brief has passed its brief review (`task-t2-brief-review.md`, Ready with fixes, all folded in below).

## Why

The Windows baseline at `deb3636` failed once in
`test_studio_live.StudioProtocolTests.test_handshake_status_badges_and_target_query` (`AssertionError: 2 != 1`
at its single-session assertion). Studio sends `design:hello` on every iframe load, with its current session
or a new one when it has none, and starts a fresh session on `design:bridge-ready`
(`fontkit-studio.html`: `startHandshake`, `connectTargetApp` and the frame's `load` listener). For a
cross-origin iframe the browser does not order the target's bridge-ready message against the iframe's load
event. When the load event reaches Studio first, Studio greets with S1 and then, on bridge-ready, with S2, as
designed. The test asserted the other order only. A probe that forces load-first with the fake target's
existing `?late` switch gives two sessions in 3 of 3 runs, and one session in 3 of 3 with the normal announce;
the test passes 3 of 3 alone. The default variant of
`StudioFixRound1Tests.test_i3_every_iframe_load_regreets_both_announce_orders` has the same assumption after
each reload (it asserts exactly two hellos sharing one new session). The behaviour is right; the oracles
assume an order the browser does not guarantee.

## Owned files (exact)

In `tests/test_studio_live.py` only: the two tests above, and at most two small `LiveCase` methods that only they use
(the held-load routes; the wait-and-release). Keep `LiveCase.open`'s signature: `test_support.py` imports `LiveCase`.
Read-only: `fontkit-studio.html`, `tests/fixtures/studio/fake-target.html` (it already has `?late`), `tests/support.py`,
every other test.

## Read first

`constraints.md` (all of it); the brief review `task-t2-brief-review.md` (its "Evidence by check" section 2 lists every
seam with its line at BASE, section 3 the probes behind the hold mechanism); at BASE: `fontkit-studio.html` 4438-4499
(`newSessionId`, `sendDesignMessage`, `acceptBridgeMessage`, `startHandshake`), 4612-4649 (`connectTargetApp`, the frame
`load` listener) and 5490-5494 (the `design:bridge-ready` case); `tests/fixtures/studio/fake-target.html` 31-32, 253-263
and 524-533; `tests/test_studio_live.py` 31-157, 279-315, 1090-1116 and 1292 (`ArrangeCase.wait_ready`); the hold
precedent `tests/test_studio_roles.py:1209-1223`.

A reference draft from the brief review exists outside the repository:
in the session scratchpad (`t2br-tree-impl/tests/test_studio_live.py`)
(`hold_load`, `release_when_greeted` and both tests; +86/-29). It applies the three Important fixes but not the order
log, the exactness additions, the sleep replacement or the docstrings below. You may start from it; every requirement,
mutant and run in this brief is still yours to do and show.

## Forcing each order

**Bridge-ready first: hold the iframe's load.**

- Connect with `page, errors = self.open(engine, target=None)`, then register the two routes on `page.context`, then
  `self.connect(page)`. A hold registered before `open`'s `goto` with `?target=` deadlocks it: the parent's load event
  waits for the iframe's. Keep `open`'s `pageerror` listener: both tests end in `assertEqual(errors, [])`.
- The routes, registered after the module's virtual-origin routes so they take precedence (Playwright runs matching routes
  in reverse registration order): a copy of `fake-target.html`, read from the fixture file, with one
  `<img src="/fks-hold-load.gif">` added before its one `</body>` (assert there is exactly one), served at the exact
  `FAKE` URL string with no wildcard, so `?late=1` and `no-bridge.html` stay on the module's routes; and the image URL
  routed to `lambda route: held.append(route)` (Playwright cannot wrap a builtin method).
- Release, for the first document and for each reloaded one: poll `held` by condition, up to 5 s, as
  `tests/test_studio_roles.py:1214-1217` does, then assert `len(held) == 1` with the message
  `'the page requested its held image'`; then wait in the frame for
  `document.readyState !== "complete" && window.__received.some(i => i.data && i.data.type === "design:hello")` (the
  held document stays `interactive`, while the page before a reload is `complete`, so the old document cannot satisfy
  it); then fulfil the stored route (a tiny GIF, an empty 200 or a 204). Never wait for a hello with a new session id: a
  mutant would then time out instead of failing its assertion. Release before `wait_connected`, which waits for
  `readyState === "complete"`.

**Load first:** the existing `?late` switch (the fake announces 60 ms after its own load event, `fake-target.html:524`;
the review measured a 58.6-73.9 ms margin over about 130 runs, idle and loaded).

**The order premise, in both variants.** Before `connect`, install one recorder on Studio's page, and clear its two
lists before each reload:

```js
window.__order = []; window.__ready = [];
document.querySelector('#targetAppFrame').addEventListener('load', () => window.__order.push('load'));
addEventListener('message', e => {
  const type = e.data && e.data.type;
  if (type === 'design:bridge-ready') window.__order.push('bridge-ready');
  if (type === 'design:ready') window.__ready.push(e.data.sessionId);
});
```

After the second hello has arrived, assert `window.__order == ['bridge-ready', 'load']` (held) or
`['load', 'bridge-ready']` (late), before any session assertion. A lost race or a missing hold then fails at the premise,
never at a session count.

**Reading the hellos.** Read them only after
`frame.wait_for_function('window.__received.filter(i => i.data && i.data.type === "design:hello").length >= 2')` on the
current document, as `ArrangeCase.wait_ready` does, never on `wait_connected`'s fixed sleep. In the load-first reload,
first wait for the new document: take `origin = frame.evaluate('performance.timeOrigin')` before the reload, then
`frame.wait_for_function('(origin) => performance.timeOrigin !== origin', arg=origin)`. This replaces the fixed
`page.wait_for_timeout(100)` after the reload (`tests/test_studio_live.py:1100`).

## Assertions

Each expected value is a literal, the order log above, or the session the fake stamps on its `design:ready` replies
(`fake-target.html:253-263`, recorded in `window.__ready`). `self.session_id(frame)` reads the last hello, so comparing the
last hello with it cannot fail: never use it as the bridge's session.

- Handshake, bridge-ready first: exactly two hellos, both with one session; the badge sequence includes `Connecting…` and
  `Bridge detected`; every hello has origin `STUDIO`, protocol 1 and a session matching `^fks-[0-9a-z]+$`; the last hello's
  session equals `window.__ready[-1]`.
- Handshake, load first: exactly two hellos `[S1, S2]` with `S1 != S2`; `S2` equals `window.__ready[-1]`; the same badge and
  shape assertions.
- The `?target=` half moves to its own `self.context(engine)` page (a context-level hold would block its `goto`); its
  assertions are unchanged.
- Reload, bridge-ready first: after each reload, exactly two hellos, both with one new session that differs from the
  session before the reload.
- Reload, load first: after each reload, exactly two hellos, `hellos[0]` equals the session before the reload and
  `hellos[1]` differs from it.
- Each test method keeps its name and gets a Given/When/Then docstring whose Then is exactly what it asserts.

Before editing, run `git grep -n -E "design:hello|session_id\(" -- tests/test_studio_live.py` and list in the report every
other test that counts hellos or sessions after a connect or reload against the fake target, with whether it assumes one
order (the review's pre-scan at BASE found none). Fix none of them here; the controller decides.

## Mutants (each foreground; `fontkit-studio.html` edited temporarily in your worktree, restored in `finally`, SHA-256 before and after)

1. Line 4496: `live.sessionId = newSessionId();` becomes `live.sessionId = live.sessionId || newSessionId();`.
   Expected: the load-first handshake fails (one session where two are required) and the bridge-ready-first reload fails
   (`assertNotEqual`: the session did not change). Do not use the literal no-op `live.sessionId = live.sessionId`:
   `connectTargetApp` clears the session (line 4620), so it sends no hello at bridge-ready and the held variant times out
   instead of failing an assertion.
2. Line 4644: `if (!live.sessionId) live.sessionId = newSessionId();` becomes `live.sessionId = newSessionId();`.
   Expected: the bridge-ready-first handshake fails (`2 != 1` sessions), the bridge-ready-first reload fails (`2 != 1`) and
   the load-first reload fails (`hellos[0]` is not the session before the reload).
3. The test's hold removed (the image fulfilled at once): both tests fail at the premise (`0 != 1 : the page requested its
   held image`, or the order log), never at a session assertion.

For each mutant, record the command, every failing test and line, and the SHA-256 before and after.

## Focused gate

From the worktree, in Git Bash:
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_studio_live.StudioProtocolTests.test_handshake_status_badges_and_target_query test_studio_live.StudioFixRound1Tests.test_i3_every_iframe_load_regreets_both_announce_orders test_support`
Run it five times in a row, all green. Then once under load: run the same command while
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" shard-2` runs beside it from the
same worktree in a second shell (shard-2's modules use no npm fixture; background it, wait for both, then report both
results). Also `python -m ruff check tests/test_studio_live.py` and, after staging by name, `git diff --cached --check`.

## Report and handoff

Report: the root cause in one paragraph (cite the Studio lines); the hold mechanism; each assertion's oracle; the order log
seen in each variant; the three mutants (command, failing lines, SHA-256 before and after); the five repeated runs and the
loaded run; the sibling list; gross and material lines. Handoff: the patch, the commit subject
`test: force both announce orders in the handshake tests`, a draft body (why, wrapped at 72, no process narration), and
the R2.T2 plan items done. The plan's R2.T2 "Owns" line says "one local helper"; the controller updates it to the two
`LiveCase` methods at landing.
