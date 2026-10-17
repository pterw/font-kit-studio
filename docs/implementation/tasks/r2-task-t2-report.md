# R2.T2 code report (task t2, MODE code)

BASE `e2098ac0c97642b8315ea77fb7b3eb053868a7a1`, worktree `C:/fks/tt2` (detached at BASE, nothing committed, no other path touched).
Status: DONE_WITH_CONCERNS (a sibling that assumes one order, the line budget, two new module names; all below).
Patch: `.superpowers/sdd/r2/task-t2-code.patch`, one file, `tests/test_studio_live.py`, +101/-40 (`git apply --check -R` passes in the
worktree; it also applies forward onto BASE content and reproduces the staged blob). `fontkit-studio.html` is unchanged.
Scratch (scratchpad, every name ends `-t2`/`_t2`): `red_t2.py`, `probe_t2.py`, `mutate-t2.py`, `late_siblings_t2.py`, `burn_runs_t2.py`
and their `*-t2.log` files.

## Root cause
Studio greets the target at two points, and for a cross-origin iframe the browser does not order them. `connectTargetApp` clears the
session (`fontkit-studio.html:4620`). A `design:bridge-ready` message (case at 5490-5494) runs `startHandshake`, which makes a new
session (4496) and sends a hello (4497). The frame's `load` listener (4634-4649) keeps the session in use or makes one (4644) and
sends a hello (4646). Bridge-ready first: both hellos carry one session. Load first: the load makes S1, then bridge-ready replaces it
with S2 (two sessions). BASE asserted only the first order (`:302` handshake, `:1110` reload default variant).

## What was done, per brief step
- Hold (bridge-ready first): `LiveCase.hold_load(context)` serves a copy of `fake-target.html` (read from the fixture, one `</body>`
  asserted) with `<img src="/fks-hold-load.gif">` before it, at the exact `FAKE` string, and routes the image to
  `lambda route: held.append(route)`. Registered on `page.context` after `self.open(engine, target=None)`, before `self.connect(page, ...)`,
  so `open`'s `pageerror` listener stays and `?late=1`/`no-bridge.html` stay on the module's routes.
- Release: `LiveCase.wait_greeted(page, held=None)` polls `held` up to 5 s, asserts `len(held) == 1` ("the page requested its held image"),
  waits in the frame for `readyState !== "complete" && window.__received.some(hello)`, fulfils the route (204), then waits for >= 2 hellos
  on the current document and the Connected badge. It runs for the first document and each reload; `wait_connected` is not used.
- Load first: the fake's `?late=1` (60 ms after its load event).
- Order premise: module constant `ORDER_RECORDER` (the brief's recorder, `?.` instead of a local) is installed before `connect`; the lists
  are cleared before each reload; `window.__order` is asserted against the variant's pair before any session assertion
  (`ANNOUNCE_ORDERS`, a module constant; both tests loop `product(ENGINES, ANNOUNCE_ORDERS)`).
- Reload wait: `performance.timeOrigin` before the reload, `frame.wait_for_function('(origin) => ...', arg=...)` after it; the
  `wait_for_timeout(100)` is gone. The `?target=` half runs in its own `self.context(engine)`; its assertions are unchanged.
- Both tests keep their names and have Given/When/Then docstrings.

## Oracles
| Assertion | Oracle |
|---|---|
| events Studio's page saw, in order | literal pair per variant, recorded by the page (`window.__order`) |
| exactly two hellos; origin STUDIO, protocol 1, `^fks-[0-9a-z]+$`; badges Connecting and Bridge detected | literals |
| handshake sessions: one (bridge-ready first), two (load first) | literals 1 and 2 |
| last hello's session | `window.__ready[-1]`, the session the fake stamps on its last `design:ready` (`fake-target.html:253-263`); not `session_id()` |
| reload: bridge-ready first, one session that differs from `sid`; load first, `hellos[0] == sid`, `hellos[1] != sid` | `sid` = last hello of the document before the reload |

## Order logs seen (`probe_t2.py`)
```
bridge-ready first (held)  while held: held=1 readyState=interactive order=['bridge-ready'] hellos=1
                           settled: order=['bridge-ready','load'] hellos=[S1,S1] ready=[S1,S1]
                           reload 1 and 2: order=['bridge-ready','load'], two hellos on one new session each
load first (late)          settled: order=['load','bridge-ready'] hellos=[S1,S2] ready=[S1,S2]
                           reload 1 and 2: order=['load','bridge-ready'], hellos=[session before, new]
```

## RED (reproduced flake, before any edit; BASE assertions, `?late=1` forced through `connect`/`open` by `red_t2.py`)
`PYTHONPATH="tests;<scratchpad>" python -m unittest red_t2.ForcedLoadFirstHandshake.test_handshake_status_badges_and_target_query`
3 of 3: `test_studio_live.py", line 302 ... AssertionError: 2 != 1`.
`... red_t2.ForcedLoadFirstReload.test_i3_every_iframe_load_regreets_both_announce_orders` 3 of 3: `line 1110 ... AssertionError: 2 != 1`.
Control, the two BASE tests with the normal announce: 3 of 3 `Ran 2 tests ... OK`.

## GREEN
Gate (from `C:/fks/tt2`): `sh .../tools/gate.sh focused <the two ids> test_support`, five runs in a row:
`Ran 36 tests in 24.8-25.6 s`, `OK`, `GATE focused EXIT 0 IN 25-26s`, 5 of 5. Loaded: `gate.sh shard-2` in the background, the same
focused command beside it, three times: 3 of 3 `Ran 36 tests ... OK` (26.0, 27.1, 25.3 s); shard-2 ended `Ran 180 tests in 234.032s OK`,
`GATE shard-2 EXIT 0 IN 234s`. Extra (the two tests only): 6 of 6 beside 8 CPU burners (12 s each) and 6 of 6 beside 28 burners on 16
logical CPUs (22-36 s each); the burners exit by themselves and none is left running. `python -m ruff check tests/test_studio_live.py`:
All checks passed. `git diff --cached --check`: clean. `pre-commit` is not installed here: not run (ruff and the whitespace check are
its two hooks that apply to this file).

## Mutants (`python mutate-t2.py <n>` = edit by bytes, `python -m unittest -v <the two ids>` in `C:/fks/tt2`, restore in `finally`)
`fontkit-studio.html` SHA-256 before and after mutants 1 and 2: `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804`
(identical). `tests/test_studio_live.py` before and after mutants 3 and 4: `09d8b9ecbe38d9af008eae6adbbd452decac8797464f82c9f1a00a876bbbfe86`
(identical). `git diff --exit-code` was clean after each.
| # | Edit | Failing (file line) |
|---|---|---|
| 1 | `fontkit-studio.html:4496` `live.sessionId = live.sessionId \|\| newSessionId();` (mutated SHA `25450bf7...2cda`) | handshake load-first `:351` `1 != 2`; reload bridge-ready-first `:1172` assertNotEqual(hellos[0], sid); reload load-first `:1168` assertNotEqual(hellos[1], sid) |
| 2 | `:4644` `live.sessionId = newSessionId();` (`58d20141...d531`) | handshake bridge-ready-first `:351` `2 != 1`; reload bridge-ready-first `:1171` `2 != 1`; reload load-first `:1167` hellos[0] != sid |
| 3 | `hold_load`: `lambda route: route.fulfill(status=204)` (`da68e55e...498e`) | both tests at `wait_greeted:191` `AssertionError: 0 != 1 : the page requested its held image` (handshake `:338`, reload `:1154`); never at a session assertion |
| 4 (extra) | both `f'{FAKE}?late=1' if late else FAKE` become `FAKE` (`0698d8b9...95be`) | both load-first variants at the order premise (`:339`, `:1162`) `Lists differ: ['bridge-ready', 'load'] != ['load', 'bridge-ready']` |

## Sibling tests (`git grep -n -E "design:hello|session_id\(" -- tests/test_studio_live.py` at BASE; none fixed)
The brief's pre-scan found none. One test assumes bridge-ready first. I forced every target a sibling opens to `?late=1`
(`late_siblings_t2.py`, patching `LiveCase.open` in memory):
- ASSUMES bridge-ready first: `StudioFixRound1Tests.test_every_control_message_carries_protocol_version_and_session` (BASE 1048-1088). It
  compares the session of every parent message, both hellos included, with the last hello's (BASE 1082). Forced load-first: fails 4 of 4,
  `AssertionError: 'fks-A' != 'fks-B'` at `data.get('sessionId'), sid` (now `:1133`). It is the same class of flake. Suggested fix (needs
  a plan change): only non-hello messages and the last hello must carry `sid`.
- Order-agnostic (take the last hello, `>= 1`, or a before/after count; all pass forced load-first): `StudioDefectTests.test_spoofed_messages_from_foreign_window_or_session_are_ignored`
  (194), `StudioProtocolTests.test_live_inspector_seeds_from_computed_and_respects_editable` (338), `...test_targeted_updates_canonical_values_and_rejection_reseed`
  (384), `...test_select_interact_toggle_and_studio_owned_overlay` (521), `...test_explicit_composition_sync_is_session_gated` (673, 682),
  `...test_restore_page_text_uses_session` (699), `StudioArrangeTests.test_move_buttons_send_design_move_and_the_target_reorders` (1328;
  `ArrangeCase.wait_ready` 1292 already waits for 2 hellos), `StudioPopoutTests.test_pop_out_accepts_only_the_popup_at_the_expected_origin` (2057).
- Outside the module (read, not run): `test_studio_first_run.py:250` (`>= 1`), `test_studio_visual.py:516` (last hello),
  `test_studio_roles.py` shims (PEER never announces, so exactly one hello by design; HYBRID takes the latest hello).

## Lines, deviations, concerns
- Gross 141 (+101/-40) against "about 120"; all material (no Markdown, no churn). Of the 101 insertions, 41 are shared infrastructure
  (import and constants 12, the two methods 29) and 11 are docstring lines. The 115-line reference draft had no order log, exactness,
  sleep replacement or docstrings; `product(...)` keeps the handshake body at its old indentation (12 unchanged lines are not re-indented).
- New top-level names beyond "two methods": `ANNOUNCE_ORDERS`, `ORDER_RECORDER`, `from itertools import product`. Both tests need the same
  recorder and pair; the alternative is a second inline copy of the recorder.
- `wait_connected` (150 ms sleep) is still used by the unchanged `?target=` half. The poll in `wait_greeted` is a condition poll with a
  50 ms tick, as `test_studio_roles.py:1214-1217`.
- Residual non-determinism: load-first rests on the fake's 60 ms timer after its own load event. A lost race fails loudly at the
  order premise (mutant 4), never at a session count. The final file ran green 20 of 20 times (5 idle, 3 beside shard-2, 6 and 6 under burners).

## Handoff
- Commit subject: `test: force both announce orders in the handshake tests`
- Draft body (wrapped at 72):
```
For a cross-origin iframe the browser does not order the target's
design:bridge-ready message against the frame's load event. Studio
greets the target at both: bridge-ready starts a fresh session, and
the load event greets with the session in use. The handshake test and
the reload test asserted only the bridge-ready-first order, so they
failed whenever the load event reached Studio first.

Force each order and assert it exactly. Bridge-ready first holds the
iframe's load open with a test-served copy of the fake target that
carries one unanswered image request; load first uses the fake's late
announce. Studio's page records the order it saw, which is checked
before any session count, and the session of every design:ready reply,
the bridge's own record that the last hello is compared with. Hellos
are read only once two have arrived, and a reload waits for the new
document by its time origin instead of a fixed sleep.
```
- Plan R2.T2: tick all three boxes (force each order; assert each exactly; keep the other assertions and list siblings, which is the
  sibling section above). Update the "Owns" line from "one local helper" to the two `LiveCase` methods `hold_load` and `wait_greeted`
  plus the module constants `ANNOUNCE_ORDERS` and `ORDER_RECORDER`.
- Ledger entry (suggested): R2.T2 handshake-order tests; RED = BASE assertions under forced load-first fail 3 of 3 (`2 != 1` at :302 and
  :1110); GREEN = focused gate 5 of 5 plus 3 loaded beside shard-2; mutants of `startHandshake` (4496) and the load listener (4644) fail
  three assertions each, a removed hold fails both tests at the premise; sibling `test_every_control_message_carries_protocol_version_and_session`
  assumes bridge-ready first and is open for a plan change. No CHANGELOG line (test-only).
- Landing gates: `focused` = the two ids plus `test_support`; `shard-1` (whole `test_studio_live`) at the settled wave.

## Fix round 1 (third test: `test_every_control_message_carries_protocol_version_and_session`)
Mode code, worktree `C:/fks/tt2`. Entry check: `git diff --cached --binary <BASE>` hashed `d5a99657...a94d` as given. Only
`tests/test_studio_live.py` changed. The worktree file is CRLF (autocrlf; the index is LF), edited preserving CRLF.
- Changed: the test body runs per `product(ENGINES, ANNOUNCE_ORDERS)` exactly like the two fixed tests (open `target=None`,
  `ORDER_RECORDER`, `hold_load` for bridge-ready first, `?late=1` for load first, `wait_greeted`), with `window.__order == order`
  asserted before anything else. Every other assertion is unchanged. Given/When/Then docstring added.
- Oracle per order (the fake's stamp, `window.__ready[-1]`, never `session_id(frame)`): both orders, exactly two hellos among the Studio
  messages and the second equals `__ready[-1]`. Bridge-ready first: the first hello equals the second, so every message carries that one
  session. Load first: first != second (S1 != S2), and every message after the second hello carries `__ready[-1]` (S2); the first hello is
  excluded from the per-message session check. Protocol version and origin are still checked on all messages.
- The `wait_for_timeout(300)` only waited for the back click's `design:select` (null) to arrive, so it became
  `frame.wait_for_function` on the number of `design:select` records exceeding the count taken before the click. Consequence: the
  `assertNotIn('design:highlight')` now holds as of the back select's arrival, not 300 ms later (it never proved a long absence).
- Mutants (run in `C:/fks/tt2/tests`, `python -m unittest` on the one test, restored in `finally`; helper `t2r1_mut.py`, scratchpad):
  | # | Edit | Result |
  |---|---|---|
  | 1 | `fontkit-studio.html:4496` `live.sessionId = live.sessionId \|\| newSessionId();` | `:1148` assertNotEqual (load first, S1 == S2: `'fks-e475...' == 'fks-e475...'`) |
  | 2 | `:4644` `live.sessionId = newSessionId();` | `:1150` assertEqual(first, second), bridge-ready first (`'fks-86f7...' != 'fks-45d0...'`) |
  | 3 | `hold_load`: `route.fulfill(status=204)` instead of `held.append(route)` | `wait_greeted:191` `0 != 1 : the page requested its held image` (premise, via `:1114`) |
  `fontkit-studio.html` SHA-256 before and after 1 and 2: `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804` (identical).
  `tests/test_studio_live.py` before and after 3: `e2d29db1ec40862107a87b898d63c63bc5ba83b548959ecd80f927ecfe172b67` (identical).
  The earlier two tests' code is untouched by this round, so their mutants are not re-run.
- Runs: the focused command (now with the third id; `Ran 37 tests`) five in a row: 5 of 5 `OK`, `GATE focused EXIT 0 IN 27-28s`.
  Beside `gate.sh shard-2` (background, same worktree), twice: both `Ran 37 tests ... OK` (27.7, 28.4 s); shard-2 `Ran 180 tests in
  233.689s OK`, `GATE shard-2 EXIT 0 IN 234s`. `python -m ruff check tests/test_studio_live.py`: All checks passed. `git diff --cached
  --check`: clean. pre-commit is not installed here (not run).
- Patch: `task-t2-code-r1.patch` (whole patch against BASE, LF, SHA-256 `31a44a44...81dd`), `git apply --check -R` passes. Lines for the whole
  patch: gross 182 (+133/-49), all material (one file, no Markdown, no churn); this round added 32 and removed 9 over the first patch.
- Deviations: the module constants `ANNOUNCE_ORDERS`, `ORDER_RECORDER` and `from itertools import product` (and the two helpers) are shared
  by three tests instead of a second or third copy of the recorder; no new names this round.

### Handoff update
- Commit subject unchanged: `test: force both announce orders in the handshake tests`. Body: replace the first paragraph's second sentence
  with "The handshake test, the reload test and the every-control-message test asserted only the bridge-ready-first order, so they failed
  whenever the load event reached Studio first." and append: "The every-control-message test takes its session oracle from the fake's
  own design:ready stamp, expects the superseded session only on the first hello when load came first, and waits for the back click's
  select instead of a fixed sleep."
- Plan R2.T2: the sibling-list box is now satisfied by fixing the one sibling in this task; ledger: three tests, mutants as above.
  Land `task-t2-code-r1.patch` (replaces `task-t2-code.patch`).

## Controller integration

- Landed from `task-t2-code-r1.patch` (SHA-256 `31a44a44...81dd`) on the integrated W0 tree, after R2.C0; no conflict.
- Review: Approved with three Minors: the module constants are recorded as a deviation in this report; 141 gross lines
  against about 120 (now 182 with the third test); the third test, which assumed the same order, is fixed in this task by
  owner decision (plan R2.T2 and Addendum 19 amended). The scoped re-review of the third test is Approved with two Minors,
  both recorded without change: no message lies between the two hellos in the load-first order today, and Studio has no
  code that can send `design:highlight`.
- Landing gates: the same integrated run as R2.C0's; the three handshake tests passed in the 23-test run (42.878 s) while
  the 137-test run went on beside it.
- Material lines: 133 added, 49 removed, in `tests/test_studio_live.py` (D065).
