# R2.SK code report (MODE: code, worktree C:/fks/tsk, BASE bd20e43b)

Patch: `.superpowers/sdd/r2c/task-sk-code.patch` (`git apply --check -R` passes). Files: `fontkit-studio.html` (+95/-22),
`tests/role_contract.py` (+22/-1), `tests/test_studio_roles.py` (+431/-16). About 588 gross lines against the 640 budget.

## Steps

- R1 revision check, R2 tolerant reader (`roleShape`, `ROLE_WIRE`, `readRoleWire`, `readRoleReply`), the `safeRoleWire`
  nonfinite line, R3 Detect visible failure and rejection, R4 Detect timer, R5 Apply/Clear visible failure and rejection,
  R6 split, R7 `role_contract.py` (`ROLE_REVISION`, `UNKNOWN_KEY`, `TOLERANT_KINDS`, `with_unknown_keys`, docstring), R8 forced
  edits, R9 Minors: done. `ROLE_RECEIPT_KEYS` moved up beside the shape table (it is read at init). The `design:ready` call at
  5531 needed no edit. Valid-rejection timer cancel dropped per Revision 2. No fake-ready site beyond the four listed
  (re-ran `git grep roleDetection -- tests`).
- Tolerant readers run first in `acceptRoleReady`, `acceptDetectedRoles`, `acceptRoleReceipt`, `acceptResetRoleState`; the
  validators are unchanged and see only the copy; acceptors store and use only the copy. `design:rejected` stays strict.
- `safeRoleWire` nonfinite line: `if (typeof item === "number" && !Number.isFinite(item)) return false;`. Callers all safe;
  full focused runs pass.
- Forced edits (characterization changes forced by R2): ready test (dropped `'extra key'`; added `'extra role key'` row built by
  `snapshot_state`, and a separate `no roleRevision` step with recovery; docstring), hostile Detect shapes (dropped
  `'extra top-level key'`, `'extra group key'`; docstring), `hostile_receipts` (dropped `'loss extra key'`, `'extra receipt
  key'`; kept `'extra role key'`), reset replies (dropped `'extra key'`), M5 rename to
  `test_malformed_rejections_show_the_unreadable_status_and_leave_the_request_in_flight` with docstring and one
  `wait_status(UNREADABLE_REPLY)` before the settling receipt. Fake-ready caps got `roleRevision: 1` at `PEER`,
  `PEER_DETECT_ONLY`, `hybrid_page`, and the forged ready (still refused for its own reason: foreign origin).
- Minors taken: W2SB 1 (select refused families by property, `next(...)`), W2SB 2 (help text punctuation only; the pinned
  phrases at the 774/775 assertions still pass). Already fixed / left as the brief lists.

## Deviations (named)

- New class derives from `StudioLegacyCase` (a subclass of `StudioRoleCase`) for `legacy_in_flight`, `applied`, `quiet`.
- Exports need a saved legacy edit, which the peer cannot produce, so the tolerant-key test runs on the legacy fake target
  (`open_hybrid`, `saved_edit`, role-state via `rs.state` + `fake.reannounce()`); the JSON tab's acknowledged revision is
  aligned (as the existing exports test does) because a role op raises it by one. Request bytes are compared for the marker only
  (session ids differ per run). Plain and unknown-key runs are separate fresh sessions so every wait is on a state change.
- Absences ("nothing changed" for other request/document ids, late op, no pending) use `quiet` (300 ms), not a following
  positive: after an unreadable-or-valid status the same string would hide a wrongly handled message. Used also under the frozen clock.
- Test 2 sends one Detect per row (rows cleared by the bad ready), so the peer sees hello plus eight detects, not hello alone.
- Test 10's reset "unknown key in a role" row is invalid either way (a reset needs empty roles); it only pins the message.
- Test 9's oracle counts dicts by the regex `\{(?=["}])` (CSS braces are followed by `\n`), plus a literal message.

## Fake clock

`page.clock.install(time=0)` then `pause_at(1000)` before the click. With the clock paused `wait_for_function`, locator
`.click()`, frame `evaluate`, `wait_for_timeout` (Playwright side) and `inner_text` all worked in tests 6, 7, 8 (Playwright
1.62.0, chromium). `settle` was never called while paused. Time moves only through `page.clock.run_for`.

## RED at BASE (new tests against unchanged html; evidence in work/sk_red*.log)

- 1, 3, 5: GREEN characterizations (pass at BASE). 5 earns its value only through mutants 5a/5b.
- 2 RED: `TimeoutError ... wait_for_function` for all 8 values (ready accepted, UNSUPPORTED never shown).
- 4 RED: plain session passes, unknown-key session times out (all three kinds).
- 6 RED: `AssertionError: 'Detecting text styles…' != "Studio could not read the page's reply to Detect; ..."`; waits time out.
- 7 RED: `AssertionError: 'Detecting text styles…' != 'The page did not reply to Detect; this page has not been checked.'`
- 8 RED: all six phases time out waiting for the could-not-read string. 10 RED: receipt and reset parts; (a) ready parts GREEN at BASE.
- 9 RED: with BASE `role_contract.py` (`PYTHONPATH=work/sk_base;tests`): `AttributeError: module 'role_contract' has no attribute 'TOLERANT_KINDS'`.

## GREEN

```
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_roles test_support -v   -> Ran 137 tests ... OK
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_live test_role_protocol -v -> Ran 170 tests ... OK
```
After the last comment-only edit: `StudioRoleReplyTests test_support` Ran 44 OK. The rejection tests stayed green as predicted.

## Mutants (one per test; foreground; source restored byte-exact; log work/sk_mutants.log)

`fontkit-studio.html` SHA-256 before and after every html mutant: ac75c7fb011d1a62300c50bfec4cbcf640830978d073a68dac93fd1e6fba298b.
`tests/role_contract.py`: 66be3850c7cc08e505805f8f28bdfc257a56af4fa57d19acb297e0bfd817b831 before and after.

| Test | Mutant | Result |
|---|---|---|
| 1 | GROUP shape drops `adapter` | FAIL |
| 2 | `>= 1` to `>= 0`; `isSafeInteger` to `isFinite` | ERROR at '0'; ERROR at '1.5' and '2**53' |
| 3 | detect request gains `roleRevision` | FAIL (both revisions) |
| 4 | binding shape lists `futureField`; `selectorChecks` shape removed | ERROR all kinds; ERROR kind detected |
| 5 | nonfinite line removed; reader without `safeRoleWire` | ERROR nonfinite rows (detect, receipt); ERROR proto/constructor/prototype/oversize rows |
| 6 | no timer cancel on unreadable reply; none on unreadable rejection | FAIL; FAIL |
| 7 | identity guard removed; 9000 ms | FAIL; FAIL |
| 8 | unreadable branch settles; fires for a late op | FAIL (apply and clear phases); FAIL (time-out phases) |
| 9 | builder skips dicts in lists; also adds inside echoed roles | FAIL; FAIL |
| 10 | ROLE_INPUT tolerant | ERROR ready and receipt rows |

## Gates

`pre-commit run --files <3 files>`: whitespace, ruff, static checks Passed; node --check Skipped (no JS files).
`git diff --cached --check` exit 0. Full suite not run (settled wave).

## Handoff

- Commit subject: `feat(studio): read role replies tolerantly and report unreadable ones`.
- Draft body: Studio checked no role revision and a bridge one field ahead left Detect hanging. Studio now requires
  `capabilities.roleRevision` of 1 or more, reads the four role replies through a shape that drops unknown keys (echoed
  roles stay exact), and shows a status when a matching Detect, Apply or Clear reply is unreadable or Detect gets no reply
  in 8 s. Rejections stay strict but visible.
- Plan bookkeeping: ledger event; D075 cost note; Addendum 26 clarification that echoed roles (with properties) are strict;
  README role-section sentence at the release point. Not run here: Firefox, WebKit, hosted gates.
- Limits: a valid but stale Detect reply stays a silent drop, so 8 s later the status says "did not reply".

## Fix round 1 (test wording and report only; no product code changed)

Patch: `task-sk-code-r1.patch` (whole patch against BASE; `git apply --check -R` ok in C:/fks/tsk). `task-sk-code.patch` untouched.
Only `tests/test_studio_roles.py` changed (docstrings and one test name). Its SHA-256 is now 1d42d871...5057 (was 7afa9b44...);
`fontkit-studio.html` ac75c7fb... and `tests/role_contract.py` 66be3850... unchanged.

- Minor 1: test 4 renamed to `test_a_reply_with_unknown_keys_outside_echoed_roles_renders_exactly_like_the_plain_reply`.
  The docstring now claims only the tolerance (plain and unknown-key messages render identically). The export-equals-before,
  marker-not-in-text and marker-not-in-requests assertions are KEPT, none removed, and the docstring says they are regression
  guards that hold by construction today (Studio stores only the validated copy and exports no role data) and cannot fail
  until that changes. The proof that raw reply objects are never stored belongs to R2.6S. The surviving `roleView.rows =
  data.groups` mutant is therefore a known, accepted gap of this task, not a claim of the test.
- Minor 2: test 6 docstring no longer says "the old timer does nothing"; it now says the new Detect renders and keeps
  "Detected" after 9,000 ms, and that a replaced timer's inertness is proved by the 8-second test (test 7). No code line changed.
- Minor 3: `PEER_NO_REVISION` was not added. The brief listed it, but `peer_with_caps(...)` builds the no-revision, zero, 1.5 and
  2**53 peers inline in test 2, so an extra constant would be unused (dead) code.

Evidence (chromium, PYTHONPATH=tests, from tests/):
- `python -m unittest test_studio_roles.StudioRoleReplyTests` -> Ran 10 tests, OK. `-k renders_exactly_like -k
  unreadable_reply_to_detect` -> Ran 2, OK. `python -m unittest test_support` -> Ran 34, OK.
- Test 4 mutants re-run (foreground, html restored byte-exact, SHA before = after = ac75c7fb011d1a62300c50bfec4cbcf640830978d073a68dac93fd1e6fba298b):
  binding shape lists `futureField` -> ERROR (3 kinds: detected, roles-applied, role-state);
  `selectorChecks` shape loses `signatures` -> ERROR (detected, roles-applied; FAILED errors=2). Both still killed.
  (A first attempt hit a cp1252 read error, applied nothing and its OK was discarded; the runs above used utf-8.)

## Controller integration
