# R2.3 brief: validated role stylesheet and clean undo

Plan: [R2 plan](../../plans/2026-10-03-r2-engine.md) R2.3, binding protocol
contract and Addenda 5 and 9. PR B, branch `feat/r2-role-preview`, from main
`df28a1b` after PR A merged. The controller supplies the detached worktree,
BASE and output paths in the dispatch. Read the COMPLETE binding contract,
this task, the execution constraints, and the committed R2.2 report and review
([report](r2-task-2-report.md), [review](r2-task-2-review.md)) before edits.

## Exact ownership

Own `fontkit-bridge.js`, new `tests/test_role_stylesheet.py`, and new
apply/clear cases in `tests/test_role_protocol.py`. Existing cases there stay
unchanged except one intended edit: in
`test_ready_identity_and_exact_hostile_requests_preserve_rendered_author_state`
(line 193 at BASE) replace `assertNotIn('roleStylesheet', ...)` with
`assertTrue(ready['capabilities']['roleStylesheet'])`; keep its `roleState`
equality, which still holds before any apply. Report that edit by line.
In `tests/test_bridge_runtime.py` own only the capability
dictionary in
`HandshakeTests.test_bridge_ready_carries_no_page_data_and_ready_describes_targets`:
add `roleStylesheet: True`, keep `roleDetection` and every legacy capability.

Read-only: `tests/role_support.py`, `tests/fixtures/bridge/host-roles.html`,
`tests/fixtures/bridge/target-role-protocol.html`, every other test module,
fixture, Studio, package, workflow and shared record. If a missing harness seam
blocks a required case, return NEEDS_CONTEXT naming it; never widen ownership.

## Harness facts (checked at BASE)

- `RoleBridgeCase.open(engine, host, target, headers, bridge_source)` gives
  fresh contexts, the verified HTTPS-regex abort with an earlier local
  fulfilment fallback, and the real bridge in a cross-origin frame. `headers`
  sets explicit target response headers for CSP cases; CSP is never stripped.
- The host's `request()` awaits `design:roles-applied`, `design:applied` and
  `design:rejected` by requestId, fills `baseRevision` for non-detect
  messages, and advances `window.revision` only from authenticated matching
  replies. Apply/clear tests pass `documentId` and `pageVersion` themselves,
  as in the plan's illustrative R2.3 example.
- The host records `roleState` only from ready. Read the global-reset snapshot
  from the `design:applied` reply itself. The host does not validate
  roles-applied URLs; assert `currentPageURL` and identity in the test.
- No new fixture file. Page variants (same-ID author style, an author rule
  that wins, extra author nodes) are created by test-owned setup on existing
  read-only fixtures BEFORE hello, as R2.2 did for its corpus cases. The clean
  undo snapshot is taken after that setup and after hello.

## Bridge facts (checked at BASE) and required consequences

1. **Selector grammar exists.** `roleSelector(value, checkRoots)` and
   `exactRoleObject` (fontkit-bridge.js, role section) are the bridge's
   role-specific validators from R2.2. Reuse them on this side of the
   boundary; do not add a second selector grammar or widen legacy
   `PATCH_RULES`. Property checks follow the contract's ranges and decimals.
2. **The owned sheet must not invalidate itself** (Addendum 9). R2.2's
   `noteRoleMutations` bumps `pageVersion` on any DOM mutation outside the
   overlay, and `roleStyleStamp` hashes every readable sheet. Inserting,
   filling or removing the owned node must not change `pageVersion`, and the
   stamp excludes the owned sheet entirely (presence, rules and `disabled`
   flag). Otherwise every apply reports its own outcomes stale. Author DOM,
   author style and URL changes must still invalidate as before.
3. **Detect stays a baseline scan** (Addendum 9; contract "Implementation
   choices" and the detect row of the Messages table). While an accepted role
   sheet exists, detection disables only the owned sheet around each
   synchronous `iterator.next()` loop in `detectTextStyles` (not around
   `fresh()` or `finish()`) and restores it in `finally` before yielding.
   Every exit from that loop restores first, including the in-loop
   `finish('time-budget')` early return and an exception. It
   is never left disabled across a task, a timer or a paint. Groups and
   existing `selectorChecks` then report the app's baseline, with inspector
   edits included, not the preview.
4. **Cancellation is not suppression.** `cancelRoleJobs()` (called by hello,
   detect, both resets and `dropSession()`) cancels detection by generation.
   An accepted apply's outcome measurement is a separate job that detect
   neither cancels nor stales: detect changes neither revision nor
   pageVersion. A receipt goes stale only for a real change: a new revision
   (later apply, clear, legacy edit, either reset), a new pageVersion or a URL
   change. Then its single receipt has `outcomesComplete:false`,
   `outcomeReason:'page-changed'` and `outcomes:[]`. Only hello (which
   replaces the session without calling `dropSession()`, including a re-hello
   with the same session id), `dropSession()` (origin loss, dispose) or a new
   document suppress it. Use a separate session epoch bumped on exactly those
   paths, not the detection generation.
   Exactly one receipt per accepted apply reaches the still-current session
   and document. A detect sent during the frame wait must still leave a
   measured receipt.
5. **There is no bridge-side queue.** Ordering is message order plus the
   synchronous `baseRevision` check (`checkRequest`, `checkRevision`).
   Apply/clear use the same check and bump `revision` once on commit, but do
   NOT go through `acknowledge()`: it posts `design:applied`, attaches the
   legacy `changes` ledger and calls `options.onApplied`, and a role receipt
   must never settle a legacy request. Apply and clear call
   `refreshRolePage()` before comparing `documentId`/`pageVersion`/URL, as
   detect does. A detect running while apply commits already becomes
   incomplete through its revision check; keep that behavior.
6. **Adapters are R2.4.** Accept `adapter:'plain'` only. Any `bootstrap5-*`
   adapter rejects as `unsupported-value` with a fixed detail and changes
   nothing. No template or variable is emitted in R2.3.
6a. **Owned node markers.** The owned node is
   `<style id="fontkit-role-styles" data-fontkit-role-styles="">`, appended to
   `document.head` (the legacy discovery observer watches `document.body`).
   The bridge finds it only by its retained object reference, never by id or
   attribute, so an author node with the same id or attribute is never
   adopted, edited or removed.
6b. **Rejection reasons** follow R2.2's convention in
   `test_role_protocol.py` and `detectTextStyles`: shape, prototype keys,
   unknown enum members (including an unknown adapter), role and selector
   counts, and ID/label lengths are `invalid-message`; selector grammar and
   selector length, property values and the known but unimplemented
   `bootstrap5-*` adapters are `unsupported-value`; byte limits are
   `size-limit`; stale
   document/page/URL identity is `page-changed`; stale `baseRevision` is
   `revision-conflict`; a blocked install is `stylesheet-blocked`. Apply under
   a null current URL is `unsupported-value` with detail
   `Unsupported page URL`, as detect is.
6c. **Measurement budget.** Outcome measurement uses the detection limits:
   at most 10,000 eligible parents and 2,000 ms from the post-frame start.
   Past either, the receipt has `outcomesComplete:false`,
   `outcomeReason:'budget-exceeded'` and the true checked counts.
7. **Resets.** Global `design:reset` clears roles in the same single revision
   increment and its `design:applied` reply adds the empty `roleState`
   snapshot. Target-only reset leaves the role sheet and accepted state.
   `test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything`
   stays read-only and must keep passing.
8. **Ready and dispose.** `roleState()` returns the accepted roles,
   `canonicalCss` and `cssHash`, not the R2.2 constants. `dispose()` removes
   only the owned node. Re-hello keeps accepted state in ready; no replay.

## Required behavior and tests

No role inline writes, author-DOM changes or automatic replay. No proven
cascade attribution (R2.5), adapters (R2.4) or Studio controls (R2.S2).

Characterize first (passing): legacy inspector edit/reset, R2.2 detect, ready
identity, session/origin/protocol rejection. Genuine RED: a real
authenticated `design:roles-apply` leaves the target's computed font size
unchanged and gets no matching receipt; `design:roles-clear` gets none either.

- Whole-request validation before any DOM or accepted-state write: wrong
  source/origin/session/protocol (ignored), stale `baseRevision`
  (`revision-conflict`), wrong `documentId`/`pageVersion` (`page-changed`),
  unknown fields, `__proto__`/`constructor`/`prototype` keys, arrays in object
  positions, nonfinite numbers, duplicate IDs, invalid enums, null or empty
  `properties`, every limit in the contract table (128 roles, 32 selectors,
  2,000-character selectors, ID/label lengths, 256 KiB request, 128 KiB
  canonical CSS), and family strings with delimiters, escapes, comments,
  `url(`/`expression(`, `!important` or newlines. A partly invalid request
  changes nothing.
- Canonical CSS and FNV-1a32 golden bytes/digests: empty (`811c9dc5`),
  non-ASCII family, escaped utility class and escaped author ID/role
  selectors, deduplicated selectors in request order, fixed property order,
  LF, two-space indent, final LF. `canonicalCss` is the exact `textContent`.
- Also: `design:roles-apply` with `roles: []` (an apply receipt with empty
  roles/CSS/outcomes, one revision, owned node removed); a role with an empty
  `selectors` array (rejects); a family that fails `CSS.supports` or has an
  unbalanced quote (rejects; the legacy `safeCssString` is not sufficient for
  roles); canonical CSS exactly at 128 KiB (accepted) and one byte over
  (`size-limit`).
- One owned `<style>` held by object reference (fact 6a). An author node with
  the same id and attribute, present before hello, is never adopted, edited
  or removed. Install verification is CSSOM-only: the sheet is attached,
  enabled and its rules match the canonical CSS. It never depends on matches
  or losses; computed comparison belongs to outcomes. CSP `style-src` without
  `'unsafe-inline'` (explicit header) rejects as `stylesheet-blocked`, keeps
  the previous accepted CSS, roles, revision and rendering, and bypasses no
  policy. That header also blocks the fixture's own inline `<style>`, so the
  CSP case compares rendering before and after, not literal 16px/24px.
- Outcomes now: after a rendered frame and a freshness recheck, return
  measured `matched`/`checked`/`mismatched` per role over eligible rendered
  parents, deduplicated across the selector union, with zero matches as a
  real result. A deliberately winning author rule (for example `.card p` with
  higher specificity, set up before hello) yields a counted loss with
  `winningSelector:null` and reason `complex-cascade`. A test-owned page of
  10,001 matching parents, built before hello, shows `budget-exceeded` with
  the real checked count (fact 6c); no placeholder success.
- Commit point and receipt: real post-commit author mutation (public DOM or
  history change in the page, never a fabricated receipt) gives the applied
  receipt with captured revision/pageVersion, separate current values and
  stale outcomes; no rollback, no rejection. Then queue a real inspector edit
  and a clear behind it: every accepted operation gets its own authenticated
  reply, target computed styles match each step, revisions advance by one each.
- Round trips on a frozen page: apply, replace, repeat apply, clear, repeat
  clear (idempotent, empty receipt, `outcomesComplete:true`). After clear,
  author `outerHTML` and computed styles equal the pre-apply snapshot byte for
  byte, excluding only the owned node while it existed. Ready after re-hello
  carries the accepted snapshot without replaying anything.
- Unavailable URL (Addendum 5/D061): apply with a null current URL rejects and
  commits nothing; a committed apply whose URL then becomes unsupported gets
  `currentPageURL:null` with stale outcomes; clear and global reset work with
  null and return the empty snapshot. Use a real 2,001-character route and the
  exact 2,000 boundary.
- Detect after apply reports the 16px baseline while the target keeps
  rendering 24px. On the read-only `fixtures/large-page/index.html` corpus
  (as `test_role_detection` uses it), apply a role, then sample the applied
  element's computed size every animation frame during a multi-frame scan
  and show the preview never drops (fact 3). Report that scan's time and
  heartbeat: Apply-then-Detect must still meet D058's 2,000 ms and yield.
  This case is unmeasured so far; a miss is reported as a finding, never
  met by changing a threshold.
- One restored foreground mutation per new guard (trust, shape, size,
  atomicity, ownership, install verification, owned-mutation suppression,
  baseline disable/restore, receipt survives a detect), each failing a rendered or
  correlated-state assertion, with exact byte restoration in `finally`.

## Focused gates

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_role_stylesheet test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything test_support -v
python scripts/verify.py --static-only
node --check fontkit-bridge.js
python -m ruff check tests/test_role_stylesheet.py tests/test_role_protocol.py tests/test_bridge_runtime.py
git diff --check
```

`test_role_detection` runs because facts 2 and 3 touch detection. Full
suites, Node package, frontend gate and the advisory Firefox canary belong to
the settled wave, not this code phase. The first complete 5,000-parent scan
must still meet D058 in `test_role_detection`; report its time.

## Report and done

Return the owned-path patch and a full report: RED/GREEN with commands and
output, golden bytes/digests, hostile and mutation outcomes, receipt and
queue observations, CSP/ownership/undo evidence, first-scan time, counts,
limits, cleanup and an anti-pattern self-review. Draft the CHANGELOG line,
ledger event and commit why-body in a Handoff section; the controller owns
shared files. The Handoff also names the R2.3 test that asserts
`bootstrap5-*` rejection, so the R2.4 brief can take ownership of it, and
confirms for R2.S2 that only `plain` is accepted until R2.4. Note that
`git diff --check` does not see the new untracked module: stage it in the
worktree (as the patch step does) and run `git diff --cached --check`, and
report its output. No stage, commit, push or spawn. A denied tool call is reported,
never retried through a different tool. Done means rendered apply and clear,
atomic rejection, exact undo and baseline detection pass, prior
characterizations stay green, outcomes are honest and `roleStylesheet` is
advertised truthfully.
