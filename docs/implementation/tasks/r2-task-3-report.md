# R2.3 code report (mode: code, worktree C:/fks/t23, BASE 9a4f164)

Patch: `.superpowers/sdd/r2/task-2.3-code.patch` (`git apply --check -R` passes). Files:
fontkit-bridge.js (+361/-), tests/test_role_stylesheet.py (new, 1039 lines),
tests/test_role_protocol.py, tests/test_bridge_runtime.py (capability dict only).
Nothing committed, pushed or run outside the worktree. Full suite NOT run (controller order).

## What changed
Bridge: role helpers (`roleShapeError`, `canonicalizeRoles`, `serializeRoleCss`, `fnv1a32`, family
grammar), `handleRolesApply/Clear` (shared `handleRoleMutation`), owned `<style id="fontkit-role-styles"
data-fontkit-role-styles="">` appended to head and held by object reference (WeakSet `roleOwned`),
CSSOM-only install verification (attached, enabled, rules equal a reference parse), receipts with
frame wait + budgeted measurement, session epoch, baseline disable/restore in detect, global-reset
`roleState`, `roleStylesheet:true`, dispose removes only the owned node. test_role_protocol.py
line 193 -> now line 208 after docstring insertions: `assertNotIn('roleStylesheet', ...)` became
`assertTrue(ready['capabilities']['roleStylesheet'])`.

## RED / GREEN
RED on BASE bridge (helpers not wired): `python -m unittest test_role_stylesheet.ApplyAndClearTests.<apply>
<clear>` -> `KeyError: 'roleStylesheet'` and `KeyError: 'revision'` (reply was the helper's `timeout`;
no receipt, computed size stayed 16px). GREEN after implementation: whole module passes (41 tests incl.
protocol). The split-counter tests were written after the code; their RED equivalent is the restored
mutations below (reverting to the old behaviour fails them). Characterization (legacy, R2.2, ready
identity, rejection) stayed green throughout.

## Final focused run (chromium only; Firefox/WebKit not run)
`PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest test_role_stylesheet
test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests
test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything test_support -v`
-> Ran 101 tests, FAILED (failures=9). All 9 are in test_role_detection.py and ONLY the version-number
comparison `assertGreater(reply['currentPageVersion'], reply['pageVersion'])` at lines 182 (7 subcases),
81 and 398 (the T1 relaxation). Every other test passes. `reason: page-changed` assertions there pass.
Also: ruff on the three test files: All checks passed; `node --check`: 0; `verify.py --static-only`: 0
(browser SKIP); `git diff --cached --check`: exit 0 (untracked module staged first).
First complete 5,000 scan (test_role_detection): 294.7 ms (earlier runs 408 ms, 407.8 ms), heartbeat 97->101,
input before reply. Apply-then-Detect on the same corpus: 804.7 / 969.2 / 1094.8 ms across three runs
(limit 2000), 49-67 animation frames sampled, every sample 40px, baseline group 20px, heartbeat advanced
(e.g. 97->156). No D058 miss.

## Golden bytes and digests
- Empty: `''`, `811c9dc5`.
- `.body-copy {\n  font-size: 24px;\n}\n` -> `226b1831`.
- Non-ASCII/escaped corpus (test constant GOLDEN_CSS): digest `4435df78`:
```
.md\:text-xl, [data-design-id="a\"b"], [data-design-role="H\e9 ro"] {
  font-family: "Zoë Sans", "日本語", serif;
  font-size: 32.46px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.body-copy {
  font-size: 18px;
}
```
Rules follow each other with no blank line. Digests are cross-checked by an independent Python FNV.

## Rulings I had to choose (please confirm in review)
- Reason mapping: shape/prototype keys/counts/lengths/unknown enum (textTransform and adapter) and
  empty `selectors`/`properties` -> `invalid-message`; selector grammar/length/type, property value type,
  range, nonfinite and family -> `unsupported-value`; `bootstrap5-*` -> `unsupported-value`.
  Check order: size, shape, revision-conflict, document/page identity, null URL, values, CSS 128 KiB.
- Fixed detail strings: `Unsupported page URL`, `Unsupported adapter`, `Unsupported selector`,
  `Unsupported property value`. revision-conflict detail is the existing `{baseRevision, revision}`.
- Family: also rejects `var(`/`env(`/`attr(`; unbalanced quotes; CSS.supports fails.
- Receipt `roles` hold the canonical roles (deduped selectors, rounded numbers, fixed key order).
- Loss `property` uses RoleInput key names (camelCase). `matched == checked` always in R2.3; budget
  stops at the 10,001st eligible parent so the 10,001-parent page reports checked 10,000.
- Apply with `roles: []` replies as an apply receipt, outcomesComplete true; it, clear and a repeated
  clear each bump revision by exactly one (asserted).
- Outcome counts satisfy 0 <= mismatched <= checked <= matched (asserted in the `apply` helper).
- Receipt timing: one rAF with a 250 ms timer fallback, then 8 ms slices, 2,000 ms from post-frame.

## Addendum 11 / D063 split counters (own section)
Rule implemented: the wire `pageVersion` moves only for URL change, author DOM/text/attribute mutation
(not bridge attributes, not owned node, not the bridge's own writes), and `roleStyleStamp` changes
(minus the owned sheet). Bridge-originated writes: `handleMessage` flushes earlier author records
(`refreshRolePage`), runs the handler, then `settleOwnWrites()` drops the records of the handler's own
writes; `acknowledge()` also settles before `options.onApplied`; global reset settles before building
its snapshot. Native listeners and the two render-only revalidation sites in `collectRoleStyles` (the
two former `this.pageVersion += 1; return 'page-changed'`) now bump internal `roleNative`, not on the
wire. Detect job and role receipt capture `roleNative` and compare it with revision/pageVersion/URL.
Limitation: asynchronous bridge writes outside message handlers (SPA re-apply from the discovery
observer) still count as ordinary mutations. Tests (SplitPageVersionTests + queue test): hover/click
between Detect and Apply accepted; DOM change and URL change rejected `page-changed`; inspector edit
and global reset keep the version; queued apply -> inspector edit -> Clear with Studio's last version is
ACCEPTED (revisions 1,2,3, stale apply receipt `page-changed`, computed 24/27 then 16/27); native hover
during a scan -> `page-changed` with equal versions; pointer event before the receipt frame -> stale
receipt with equal versions (page-dispatched `PointerEvent`, not a trusted event); animation-only render
change -> `page-changed` with equal versions.

## Mutations (each foreground, bytes restored in finally, SHA-256 verified; final bridge sha256 of the
mutation run `f64443de...` pre-split-counter-render change)
| Guard removed | Failing assertion |
|---|---|
| trust (isFromSession) | `1 != 0` revision after untrusted senders |
| shape (exact keys) | roles-applied != design:rejected invalid-message (4 cases) |
| size (256 KiB, role path) | roles-applied != rejected size-limit (after fixing a test that the CSS cap masked) |
| size (128 KiB `>` to `>=`) | exact-128KiB apply rejected |
| atomicity (skip bad value) | partly invalid request accepted |
| ownership (adopt by id) | owned list lacks the author node |
| install verification | CSP cases: apply accepted/errored instead of stylesheet-blocked |
| owned-mutation suppression | receipt revision/page `1 != 0`, outcomes stale |
| owned sheet stamp exclusion | same stale-receipt failure |
| baseline disable | detect sizes `[24, 27] != [16, 27]` |
| baseline restore (finally) | rendered `16px != 24px`, sampler sees baseline |
| receipt survives detect (epoch on cancel) | `timeout != design:roles-applied` |
| hello epoch | receipt delivered after hello |
| own-writes settle | version `1 != 0` and queued Clear errors |
| native epoch in detect | scan complete instead of page-changed |
| native epoch in receipt | receipt measured instead of stale |
| native listener | scan complete instead of page-changed |
| render-only wire bump | versions `1 != 0` (run after final edit; restored) |
The first size mutation survived (the oversized request also exceeded 128 KiB of CSS); fixed by using
duplicate selectors, then it fails.

## Context-file items
1. I-P3 done: `a:hover`, raw `{` `;` `}`, line break, at-rule, `url(`, `expression(`, comment, 2,001
   selector (2,000 positive), nth-of-type 10000 (9999 positive, plus 0), 201-char requestId (200 positive).
2. I-P1 done: existing detect test reads the evil child's `log` and the target frame's own inbox for the
   hostile requestId; the new untrusted apply/clear test does the same.
3. M-P1/M-P3 done: raw `log` read for bridge-ready; the correlated URL test compares a fresh bridge
   ready instead of the host's own `roleState`.
4. I-P2 infeasible: a credentialed target makes `RoleBridgeCase.open` raise `StopIteration` (frame url
   no longer starts with TARGET); a foreign-origin target times out (virtual routes map only
   STUDIO/EVIL/TARGET and the frame lookup is TARGET-prefixed). No harness edit made.
5. Docstrings added to all nine existing test_role_protocol tests (docstring-only apart from items 2, 3
   and line 208).

## Not covered / caveats
Chromium only. Cross-origin CSP only via header and a late meta tag. `fontStatus` changes (web font load)
would still advance pageVersion. Stamp excludes only the owned sheet. Roles `name` must be 1-200 chars.

# Handoff
- CHANGELOG Unreleased: "Role preview: the bridge now applies validated role fonts from one owned
  stylesheet and clears them exactly (`design:roles-apply`, `design:roles-clear`); only the plain
  adapter is accepted."
- Ledger event (2026-10-16): R2.3 owned role stylesheet and clean undo landed; split page-version
  counters (D063) applied; focused chromium tests, 18 restored mutations; T1 relaxes
  test_role_detection version comparisons (lines 81, 182, 398).
- Commit subject: `feat: apply and clear validated role stylesheets in the bridge`.
  Body: explain that role CSS lives in one bridge-owned node found by reference, is validated whole
  before any write, verified through the CSSOM, replaced only after verification, and undone exactly;
  detect keeps measuring the app baseline; bridge-originated writes and native pseudo-state no longer
  advance the wire page version (they move revision or an internal epoch).
- Test asserting `bootstrap5-*` rejection (for R2.4 ownership):
  `test_role_stylesheet.ApplyAndClearTests.test_only_the_plain_adapter_is_accepted_until_framework_adapters_land`
  (plus the `adapter-bootstrap` row of the hostile table). For R2.S2: only `plain` is accepted until R2.4.
- Studio brief facts: loss `property` = RoleInput keys; every accepted apply/clear (including repeat clear
  and `roles: []`) bumps revision by one; counts satisfy 0 <= mismatched <= checked <= matched; fixed
  details listed above; reasons per the mapping above; clear/global-reset snapshots may carry
  `currentPageURL`/`pageURL` null; global-reset `design:applied` carries `roleState`.
- T1 landing: 9 test_role_detection failures are only `currentPageVersion > pageVersion` comparisons.

## Fix round 1
Patch: `task-2.3-code-r1.patch` (full diff against 9a4f164, `git apply --check -R` passes; supersedes
`task-2.3-code.patch`). Focused command: Ran 102 tests, failures 9, all in test_role_detection and only
the `currentPageVersion > pageVersion` comparisons (no other failure). ruff, `node --check`,
`verify.py --static-only` exit 0; `git diff --cached --check` exit 0. First scan 280.8 ms; Apply-then-
Detect 992.2 ms, 61 frames, heartbeat 108->169.

1. Important 1 done. Bridge font links are tracked in a WeakSet (`bridgeFontLinks`, filled in
   `ensureFontLink`) and excluded from `roleStyleStamp` like the owned sheet. New
   `BridgeFontLinkTests`: inspector `fontStylesheet` edit (locally fulfilled route, wait on the link's
   sheet), then apply and a clear carrying the pre-edit version are accepted, a global reset keeps the
   version in its snapshot and a later apply is accepted. Mutation (exclusion removed): `'design:rejected'
   != 'design:roles-applied'`. Restored.
2. Important 2 done. A fresh detect precedes each case, so the URL case can fail on its own. Re-run
   mutants: removing `refreshRolePage()` in `handleRoleMutation` and removing the URL-driven bump
   (`location.href !== this.roleURL`) each fail this test (`roles-applied != rejected page-changed`).
3. Important 3 done. The per-message pre-handler stamp is replaced by
   `this.noteRoleMutations(this.roleObserver.takeRecords())` (no stylesheet serialization). Post-handler
   settle kept.
4. Minor 1 done. The added reads of the evil child's `log` and the target frame's `__seen` are removed
   from both files; the host-log assertions stay. I-P1 was a false audit premise: the bridge posts only
   to its pinned Studio window, so a bypass would show in the host log, which the pre-existing filter
   already reads.
5. Minor 2 done. One consistent ordering: `acknowledge()` settles before `options.onApplied` and sets
   `ownSettled`; `handleMessage` settles after the handler only if nothing settled, so an author
   callback's mutations are no longer dropped. Not mutation-tested (no author callback fixture in this
   task's ownership).
6. Minor 3 done. The hover test records the scan start and the first `pointerover` time in the frame and
   asserts `hoverAt - scanStart < reply.elapsedMs`, so a late hover fails with a premise message.
7. Minor 4/7 done: stale-receipt docstring says the pointer event is page-dispatched; the markers test
   has a "when" clause.
8. Minor 8 not changed. A throw inside measurement is unreachable (selectors are validated at apply time),
   and none of the contract's closed outcomeReason values ('page-changed', 'budget-exceeded') is truthful
   for an internal error; adding a value is forbidden. Left as is.

## Fix round 2
Patch: `task-2.3-code-r2.patch` (full staged diff against 9a4f164, round 1 included), sha256
`2ba85e758fff4a359bcec0c17263da451e14407299bb547b4bea8d4e1738176c`; `git apply --check -R` passes.
Focused command: Ran 103 tests, failures 9, all in test_role_detection and only the
`currentPageVersion > pageVersion` comparisons (0 failures elsewhere). ruff, `node --check`,
`verify.py --static-only`, staged `git diff --cached --check` exit 0.

1. `ownSettled` ordering tested. New `SplitPageVersionTests.test_author_callback_mutation_during_an_acknowledged_edit_still_advances_the_wire_page_version`:
   the frame sets `__fontkitBridge.options.onApplied` to append an author paragraph, an inspector update is
   acknowledged, and the next detect's `currentPageVersion` must exceed the value before the edit.
   Mutant (end-of-handler settle made unconditional: `if (ownWrites) this.settleOwnWrites();`), foreground,
   bytes restored and SHA-256 verified:
   RED  `MUTANT ... exit 1  FAIL: test_author_callback_mutation_... AssertionError: 0 not greater than 0`
   GREEN `restored bridge exit 0  Ran 1 test ... OK`.
2. Queue test made deterministic with no sleep: the apply receipt may be stale (`False, 'page-changed', []`)
   or measured (`True, None, [body 2/2/0 complete]`); the test asserts either, plus the revision sequence
   1, 2, 3 and the renderings (24/27 then 16/27).
3. test_role_protocol docstring now says "no hostile reply appears in the Studio host log".

## Controller integration (2026-10-16)

The final patch (`task-2.3-code-r2.patch`, sha256 `2ba85e75...`) applies with
`git apply --3way` onto `239ffee` (R2.T1 landed) with no conflict. Each staged
blob equals the code-phase worktree's index. On the integrated tree,
`test_role_detection` passes in full: the nine version comparisons that failed
at `9a4f164` are the at-least comparisons R2.T1 relaxed under D063.

- `test_role_stylesheet test_support` (Chromium): Ran 74 tests in 35.655 s, OK.
- `test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests
  test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything`
  (Chromium): Ran 29 tests in 120.442 s, OK.
- Fast gates: static checks, `node --check` and product-tree Ruff pass, and
  `git diff --check` is clean on both the working tree and the index. Exact
  Ruff reports only the four preserved findings in the owner's untracked
  `.agents/`.
- Firefox and WebKit were not run for this landing; the advisory Firefox canary
  and the full Chromium halves run at the settled wave.