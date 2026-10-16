# R2.5 independent review (2026-10-16)

Patch task-2.5-code.patch sha256 5b62f881... equals the staged tree in C:/fks/t25 (BASE 5041b84; git diff --cached | sha256sum = 5b62f881a61dafa8). t25 was not edited. Mutations ran only through RoleBridgeCase.open(bridge_source=...); probes and mutation drivers are scratchpad files with the suffix t25rev (probe_t25rev.py, probe2-4_t25rev.py, mutate_t25rev.py, red_t25rev.py). ASCII only.

### Spec Compliance
- PASS: Ownership. fontkit-bridge.js changes only `roleMismatches`/`measureRoleOutcomes` and new helpers (`roleComputed`, `roleSame`, `roleDeclared`, `collectAuthorRules`, `attributeLoss`); detection, validation, install, envelope and page-version rules are untouched. New files are test_role_preview.py and role-preview-evil.css (allowed name). test_role_stylesheet.py changes are exactly three hunks (matched 2->3 at the union test, the `.card p` test, the hover test), all named in the report and justified by Additions 1 and 7.
- PASS: Counts (pin 1, Addition 4). `matched` is the distinct selector-union size, `checked` the measured eligible elements, `complete` false only when the budget stops measuring or attribution. Verified by the new tests and by my own runs: 10,001 page gives matched 10001 / checked 10000 / complete false; matched elements without rendered text give checked < matched with complete true; overlapping selectors and roles count once per role.
- PASS: Reason order (Addendum 2) and the two judgement calls (see Concerns judged below). Loss grouping and order (pin 2), selector cap 2,000 (pin 3.4), shared comparison (Addendum 3) are implemented as written.
- FAIL: Closed world (Addendum 1) is not closed: attribution can name a selector that did not win (Important 1; Minor 1, 2).
- FAIL: Reply cap (Addendum 6) does not keep the receipt under the 1 MiB contract limit; the required hostile test is not near that limit (Important 2).
- FAIL (partial): Tests for several brief pins are missing although cheap and deterministic (Important 3).
- PASS: Hover hardening (Addendum 7): calibration scan, early timed move, premise message on a late hover. No margin is required beyond `delay < elapsedMs` (Minor 3).
- PASS: Handoff for Studio states `winningSelector` is bounded text rendered with textContent, never the role selector grammar.

### Checks run
- Focused command (Chromium): test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -> Ran 98 tests, OK (50.8 s). APPLY_THEN_DETECT elapsedMs 833, complete, scanned 5000, 51 frames, heartbeat 107->158 (report: 779.7). D058 limit 2,000 unchanged.
- RED: test_role_preview against the BASE bridge (git show 5041b84:fontkit-bridge.js through the seam) -> 13 tests, 20 failing subtests (report says 14); the `.card p` loss at BASE is complex-cascade/null. RED is genuine.
- 10,000 lost elements, one rule (probe3 test_ten_k_time): receipt round trip 0.30-0.33 s three times, exact `main .bulk` author-rule count 10000, complete.
- Honest budget with a heavy sheet (probe3 test_big_sheet_budget: 5,000 candidate font-size rules plus 10,000 losses): 1.29 s, outcomesComplete false / budget-exceeded, 160 losses named, 9,840 `budget-exceeded`, checked 10000, counts sum. The sub-deadline works and degrades honestly.
- Hover test: 24 of 24 passes (4 concurrent loops of 6).
- Closed-world probes through the real bridge (probe_t25rev.py, probe4_t25rev.py):
  - nested rule under a parent that does not match the element: `main .card { & p.card-copy { font-size: 18px } } div p { font-size: 18px }` -> loss named `div p`, author-rule. Editing `div p` to 20px leaves the computed size at 18px, so `div p` never won. BREACH.
  - shadow host: `.host { font-size: 18px }` plus an open shadow root with `:host { font-size: 18px !important }` -> loss named `.host`. Editing `.host` to 20px leaves 18px. BREACH.
  - pending `@import url(/pending-import.css)` beside a readable `.card p` rule -> named `.card p` (no unreadable flag for a pending import).
  - inline `style="font: var(--f)"` beside a readable rule -> complex-cascade (guard works).
  - `@namespace x ...; x|p.card-copy {...}` -> complex-cascade; `querySelector('x|p')` throws SyntaxError in Chromium, so `matches()` throws deterministically for this selector.
  - `@import url(data:...) layer` -> complex-cascade (layerName supported in this Chromium); data: imports load under test.
  - owned node moved into a shadow root by a page MutationObserver -> both losses `stylesheet-blocked`, 16px rendered, matched 2.
  - `performance.now` skewed by 1,500 ms from a `document.getAnimations` hook (page-side setup) -> loss `budget-exceeded`, outcome complete false, deterministic.
  - `.card p { all: unset; font-size: 18px }` -> named `.card p` (correct); `.card{18px} .card p{font-size: unset}` -> inherited (correct).
  - author `p { font-size: 18px !important }` with `style="font-size: 19px"` -> reason `inline`, but the rule wins (see Plan-mandated).
- Receipt size (probe3 test_reply_size): 8 roles x 16 elements, each element losing six properties to a distinct 1,990-character winning selector -> 96 loss entries per role (cap respected) and a roles-applied receipt of 1,608,040 bytes, delivered to the host. Contract limit for replies: 1 MiB (1,048,576).
- Mutation survivors (mutate_t25rev.py, whole test_role_preview, each run through the seam; controls owners, media_attr, dup_text_eq and cap_room each fail 1 test, so the harness bites). Mutants that SURVIVE (0 failures): drop `inlineHidden`; drop the `states.includes('throw')` guard; drop `opaque` (`all`); drop the font-shorthand `hidden` branch (partly equivalent: the case falls to "no candidate"); `unset` removed from the inherit regex; `@import layer()` complexity (`rule.layerName`); the 1,000 ms attribution deadline; the `found.budget` check; owned-node `getRootNode() === document`; owned sheet present in `document.styleSheets`; `texts.size === 1` in the inherited branch; the inherited lineHeight ratio comparison; the `@import supports()` skip; the `sheet.disabled` skip; and the "largest counts first" sort (`count_sort`). The `transition` mutant also survives but may be equivalent (keyframes of a CSSTransition carry the property).
- `git diff --cached --check` and ruff were reported by the writer; I re-ran only the focused tests and probes.

### Concerns judged (focus item 3: the report's two reason-order calls)
- Call 1: a matching declaration under @layer/@container/@scope/unknown grouping, a matching parent with nested rules, and an animation give complex-cascade even when an unreadable sheet exists. ACCEPTED. Pin 3.4 states these make the property complex-cascade inside step 4, which precedes step 6 (unreadable-sheet), and the animation rule is step 2.3.
- Call 2: every other closed-world breach (adopted sheet, slot, hidden shorthand, another role, `matches()` throw, non-comparable value, no candidate) goes to the "no proof" path: unreadable-sheet if any active sheet is unreadable or sheet-less, otherwise complex-cascade; the adopted-sheet-only case is therefore complex-cascade. ACCEPTED. Addendum 1 says "complex-cascade, or unreadable-sheet where 3.6 applies", and 3.6 is exactly "no proof and an active sheet's cssRules throws". The implementation matches the brief; nothing to change.

### Strengths
- Value comparison is genuinely shared (`roleComputed`/`roleSame` serve both `roleMismatches` and attribution) and `roleMismatches` keeps its prior tolerances.
- Attribution is lazy (rules collected only when a loss needs them), memoised per element and rule, and time-boxed; both the sub-deadline and the 2,000 ms budget degrade to explicit `budget-exceeded` with counts that still sum.
- The table-driven cascade test is dense and checks computed size, counts and the exact loss entry per situation on one shared page; the RED at BASE is real.
- The group cap logic (pool, room, merge) is correct for the 15/16/17-group edges (checked by reading and by the 40-paragraph test).

### Issues
#### Critical
(none)

#### Important
1. **Nested style rules are not enumerated, so a non-winning selector can be named** (fontkit-bridge.js:1465, 1539). `visit` never descends into a style rule's own `cssRules`, and the only nested guard asks whether the element matches the PARENT rule's selector (`found.nested.some(entry => hit(entry) === 'yes')`). A nested rule such as `.card { & p { ... } }` applies to the paragraph while its parent matches the card, not the paragraph, so the guard stays silent and the nested rule is simply invisible. Probe above: the receipt names `div p` while the nested rule wins; editing the named rule changes nothing, which is exactly the harm the closed-world rule exists to prevent (a user would be told to edit a rule that has no effect). CSS nesting is mainstream. The brief's wording ("nested rules under a matching parent rule") is necessary but not sufficient; the Addendum 1 principle (every source readable and enumerated) governs and the implementer could satisfy both by treating any active style rule with child rules as breaking the closed world for every element (conservative), or by resolving nested selectors. Not plan-mandated. Fix: flag `found.nested` entries as complex for all elements (or resolve `&`), and add a case to the CASCADE table (`main .card { & p.card-copy {...} } div p {...}` expects complex-cascade/null); mutation: restore the old behaviour and watch the case fail.
2. **A receipt can exceed the 1 MiB reply limit, and the hostile test does not approach it** (fontkit-bridge.js:1610-1625; tests/test_role_preview.py:290-312). The cap is 16 groups per role and property, but the contract limit is on the whole reply (Binding contract table: reply 1 MiB). With six properties and 2,000-character selectors one role already carries ~190 KB; eight roles reach 1.6 MB (measured 1,608,040 bytes, posted without any reply-limit handling). Studio's role wire check rejects anything over 1 MiB, so a hostile or merely large page can make an accepted apply never settle. The required test ("near the 1 MiB receipt limit") builds one role of about 54 KB and asserts `< 1 MiB`, which cannot fail. Not plan-mandated: the brief asks for at most 16 per role and property, and a lower overall bound is compatible with it. Fix: after building outcomes, measure the serialized receipt and, while it exceeds the limit, merge named groups (smallest counts first) into the unnamed complex-cascade group (or drop names for the largest selectors), keeping counts summed; make the hostile test use enough roles (the probe shape: 8 roles x 16 elements x 6 properties) to cross 1 MiB before the fix and stay under it after.
3. **Brief pins with no test, although each has a deterministic trigger** (tests/test_role_preview.py). The report admits `matches()` throwing, `@import layer()`, the owned node in a shadow root and the 1,000 ms attribution deadline are untested and says no deterministic trigger was found. All four have one, proven by my probes: (a) `@namespace x url(http://www.w3.org/1999/xhtml); x|p.card-copy {...}` makes `matches()` throw (expect complex-cascade, never a skip); (b) a page-injected `@import url("data:text/css,...") layer;` (expect complex-cascade); (c) a page MutationObserver that moves the owned node into a shadow root after install (expect stylesheet-blocked, 16px); (d) a page-side `performance.now` skew installed through the `document.getAnimations` hook (expect `budget-exceeded`, outcome complete false). Further brief-listed guards survive mutation with no test: inline `font`/`all` hiding the longhand, `all` in a rule, `unset` as an inherit keyword, the inherited lineHeight ratio, multiple inherit selectors, a disabled author sheet and an `@import supports()`/media skip (Addendum 1 says these are "inactive and never named"), the owned sheet missing from `document.styleSheets`, and pin 6's "largest counts first" (the cap test's triple winners happen to sort first lexicographically, so the count sort is unobserved). Constraints require one restored mutation per new guard. Fix: add the cases to the CASCADE table and the cap test (make the triples sort last), run the survivors list above as restored mutants.

#### Minor
1. **Shadow-root host styles are another unenumerated source** (fontkit-bridge.js:1543). An open shadow root with `:host { font-size: 18px !important }` beats the document rule (inner context wins for important) yet the receipt names `.host` (probe above). The check `el.assignedSlot` covers slotted children but not the host. Add `el.shadowRoot` to the breach list; closed roots cannot be detected, so also state in the Handoff that author-rule is proven against document-level CSS only.
2. **A pending `@import` is not treated as unreadable** (fontkit-bridge.js:1475-1476). For `<link>`/`<style>` without a sheet the brief says unreadable, and the code does that; an import rule whose `styleSheet` is null is silently skipped, so the probe names `.card p` while a stylesheet is still loading. Set `found.unreadable` when `rule.styleSheet` is null after the media/supports checks. Also guard `rule.layerName !== undefined` support (an engine without it would treat a layered import as unlayered).
3. **Hover test requires no margin** (tests/test_role_stylesheet.py, hover test). The brief says land early and require a margin; the premise is only `delay < elapsedMs`, and `elapsedMs` includes reply serialization, so a hover in that last window still passes. Stable here (24/24 at 0.5 of the calibrated time), and a late hover does fail with a message, so this is hardening, not a bug. Suggest requiring `delay <= 0.8 * reply.elapsedMs` or comparing to a recorded terminal time.
4. `test_a_csp_blocked_install_is_a_rejection_never_an_applied_success` repeats the existing R2.3 CSP test (the report says so); keep it only because the brief lists it.
5. The report's RED count (14 failures) differs from my reproduction (20 failing subtests). Not material.
6. `attributeLoss` computes `getPropertyPriority` before the animation check as the brief orders, but `hit()` for the nested guard can return 'throw' and is ignored (`=== 'yes'` only); a throwing parent selector should also give complex-cascade.

### Plan-mandated (for the owner)
- [Minor] An author `!important` rule that beats an inline normal declaration is reported as `inline` (probe: `p { font-size: 18px !important }` with `style="font-size: 19px"` -> reason inline/null, while the rule wins). Brief requires: "`inline` for an inline normal declaration." placed before "The rest of pin 3 from 3.4 on" (Addendum 2, items 4-5), so the implementer followed the order exactly; the order itself mislabels the winner. A fix needs the owner to move the inline-normal check after the rule scan (or add an important-rule check before it).

### Assessment
**Task quality:** Changes required
**Reasoning:** The counting, grouping, comparison sharing and budget behaviour are sound and well measured (10,000 losses 0.3 s, Apply-then-Detect 833 ms, honest `budget-exceeded`), but the core promise fails twice: attribution can name a rule that never won (nested rules), and a legal page can push the receipt past the 1 MiB contract limit with a hostile test that cannot detect it; in addition several brief pins that have deterministic triggers are untested (survivors listed). Each fix is small and local to the measurement code and `test_role_preview.py`.

**Verdict: Changes required**

STATUS: COMPLETE

## Scoped re-review (fix round 1)

Patch task-2.5-code-r1.patch sha256 9809d350... equals the staged tree in C:/fks/t25 (git diff --cached | sha256sum = 9809d350f93156b0). t25 not edited; mutations through the open() bridge_source seam only (mutate_t25rr1.py); probes probe_t25rr1.py plus the round-0 probes re-run (scratchpad). ASCII only.

### Disposition of the first-round findings
- Important 1 (nested rules misattribute): RESOLVED. A readable nested style rule that declares the property now makes that property complex-cascade for every element (`found.nestedProps`, collected around fontkit-bridge.js:1451-1456, checked at 1551). My counterexample (`main .card { & p.card-copy {font-size:18px} } div p {font-size:18px}`) now reports complex-cascade/null; the parent-match guard is gone. A nested rule declaring only other properties does not spoil a proof (table row, correct and conservative per ruling 10). Mutant `nestedprops` (guard removed) fails a test.
- Important 2 (receipt over 1 MiB): PARTLY RESOLVED, one residual Important (Issues 1). My 1,608,040-byte case (8 roles x 16 elements x 6 properties, 1,990-character selectors) now gives a 281,573-byte receipt; per role and property the counts still sum to 16 and mismatched is 16 for every role (probe SUMS_OK True). `test_named_selectors_are_bounded_across_the_whole_receipt` builds that shape, asserts named text between 200,000 and 262,144 characters, counts summing and the receipt under 1 MiB; mutant `receipt_bound` (bound removed) fails it, so it can now fail.
- Important 3 (untested pins): RESOLVED for the four triggers. Each has a test and a restored mutant that fails: `matches()` throw (row 'matches() throws' via `@namespace x|p`, with an assertion that `querySelector('x|p')` throws; mutant throw_guard), layered `@import` (data: import declaring `.card p`; mutant layer), owned node moved into a shadow root (third action of the blocked test; stylesheet-blocked, 16px, exact count), the 1,000 ms attribution deadline (page-side `performance.now` skew; mutant deadline; counts exact, `budget-exceeded`, outcome complete false). Also killed now: shadowroot, important_cand, pending_import, count_sort (the triples now sort last). Survivors are judged below.
- Plan-mandated (important beats inline): RESOLVED per ruling 12. `p { font-size: 18px !important }` with `style="font-size: 19px"` now reports author-rule `.card p` (probe), and inline is reported only when the value is comparable, equals the computed value and no matching readable important candidate exists; mutant important_cand fails.
- Minor 1 (open shadow host): RESOLVED. `el.shadowRoot` joins the breach list; the `:host !important` probe now gives complex-cascade/null; table row added; mutant shadowroot fails. The closed-root limit is stated in the report's Handoff addition.
- Minor 2 (pending `@import`, `layerName` support): RESOLVED. A null `styleSheet` is unreadable (probe now unreadable-sheet; the table row asserts the pending import has no sheet); `!('layerName' in rule)` counts as layered. Mutant pending_import fails.
- Minor 3 (hover margin): RESOLVED. The hover must land within the first half of the calibrated scan (`delay <= calibration/2` and `< elapsedMs`), fractions 0.3/0.2/0.1, premise message kept; 24 of 24 passes (4 concurrent loops of 6).
- Minor 4 (duplicate CSP test), 5 (RED count), 6 (throwing nested parent): ACCEPTED or moot (the CSP row is listed in the brief; the nested guard no longer calls `matches()`).

### Judging the writer's surviving mutants and the skipped item
- (a) `getRootNode() === document` on the owned node: ACCEPTED as an equivalent mutant. Alone it survives, and so does removing `Array.from(document.styleSheets).includes(node.sheet)` alone, but removing BOTH fails the shadow-moved case (`both_root_and_styles` -> 1 failure). They are defence in depth.
- (b) rule-level `all` detection: ACCEPTED, engine-dependent. Chromium expands `all` into longhands (`unset`), so `roleDeclared` returns null and the row 'a rule with all hides the longhand' passes through the non-comparable path whether or not the `all` branch exists. The branch is unverifiable in Chromium; Firefox and WebKit were not run.
- Skipped shadow-root-element minor: CONFIRMED, there is no code path. Probe: role selector `.inner` for a `<p class=inner>` inside an open shadow root -> `{"matched": 0, "checked": 0, "mismatched": 0, "complete": true, "losses": []}`. `document.querySelectorAll` does not pierce shadow roots, so the first sentence of ruling 13 cannot occur; shadow-tree text is simply not measured. The Handoff should say so (detection is already light-DOM only).

### Checks run
- Focused command (Chromium): test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -> Ran 100 tests, OK (51.1 s).
- Round-0 probes re-run on the new tree: nested counterexample, shadow host, pending import, important-beats-inline, 8-role reply (all as above).
- Mutants (whole test_role_preview, seam). Killed: shadowroot, nestedprops, important_cand, pending_import, layer, throw_guard, deadline, receipt_bound, count_sort, both_root_and_styles. Survived: root_node alone and in_styleSheets alone (equivalent, see (a)), found_budget (partial rules returned by collection) and collect_deadline (the 1,000 ms check inside rule collection).

### Issues
#### Important
1. **The whole-receipt bound does not bound the serialized receipt** (fontkit-bridge.js:1640-1655). Ruling 11 requires "A serialized receipt stays under the 1 MiB reply limit"; the implementation bounds only the total characters of named selectors (262,144). Size also grows with the number of loss entries, which the per-role-and-property cap of 16 lets reach 128 x 6 x 16 = 12,288. Probe (probe_t25rr1.py T.test_shared_short_names): 128 roles, 16 shared rules `p.e0`..`p.e15`, one paragraph per role per rule, every paragraph losing all six properties -> a `design:roles-applied` of 1,102,467 bytes compact (about 1.2 MB with default separators), 12,288 entries, a few tens of thousands of named characters, so the character bound never engages; it is delivered unmerged. It needs a hostile page and 128 roles, so it is far less reachable than the round-0 case, but it violates an explicit ruling sentence and the contract limit, and Studio's role wire check rejects such a receipt. Not plan-mandated: the implementer could also bound entries or serialized length without departing from the ruling. Fix: after the character pass, measure the serialized outcomes (or count entries) and keep merging the smallest named groups, then the smallest unnamed ones, into the role/property complex-cascade group until under about 900,000 bytes; add the shared-short-name shape to the hostile test so it crosses 1 MiB before the fix.

#### Minor
2. The two collection-time budget paths (`found.budget` at fontkit-bridge.js:1539 and the check inside `visit` at 1473) survive mutation. They are deterministically testable like the attribution deadline: a page-side hook on `matchMedia` (called once per sheet during collection) that skews `performance.now`, with a sheet of at least 65 rules so the 64-rule yield checks the deadline; expect `budget-exceeded` for the first loss and outcome complete false.
3. Behaviour change to note (acceptable): an inline-normal loss now goes through rule collection before it is reported `inline`, so after the 1,000 ms deadline, or when a matching layered or nested declaration exists for that property, it reports `budget-exceeded` or `complex-cascade` instead. Conservative and consistent with ruling 12; S2 should not assume `inline` is always attributable.

### Assessment
**Task quality:** Approved with fixes
**Reasoning:** Every first-round finding is fixed and now fails the right mutant (nested misattribution, the round-0 oversized receipt, the four deterministic triggers, important-beats-inline, hover margin, shadow host, pending import), the writer's two survivors and the skipped shadow-element item hold up, and 100 focused tests pass. One defect remains: the receipt bound counts named characters only, so a 128-role page with short shared selectors still produces a receipt over 1 MiB (Important 1, a small local fix); add the collection-deadline tests (Minor 2) in the same pass.

**Verdict: Approved with fixes**

STATUS: COMPLETE (re-review)

## Scoped re-review (fix round 2)

Patch task-2.5-code-r2.patch sha256 3442e08f... equals the staged tree in C:/fks/t25 (git diff --cached | sha256sum = 3442e08fbfd97262). t25 not edited; mutants through the open() bridge_source seam (mutate_t25rr2.py); probes probe_t25rr2.py and probe2_t25rr2.py (scratchpad). The interdiff against r1 is `fitRoleReceipt`, its call in `postRoleReceipt`, the two-row deadline test and the new 1 MiB test; nothing else changed. ASCII only.

### Disposition of my fix-round-1 residuals
- Important 1 (receipt bound counted only named characters): RESOLVED.
  - My 128-role case (16 shared rules, every paragraph losing six properties, 12,288 entries): receipt as received by the host is now 1,041,363 bytes (compact UTF-8, envelope included), 11,568 entries, every role and property sums to 16 and mismatched is 16 for all 128 roles; the first role keeps its 96 names (collapse runs from the last role backwards).
  - My second case: the same page with 128 roles whose ids are 93 characters and whose names are 199 CJK characters plus one letter (a larger echoed `roles`): 1,041,215 bytes, counts sum, first role keeps 96 names.
  - Removing the size check (`fit_check`) fails the new test (`1101442 not less than or equal to 1048576`), so the test can fail; collapsing from the first role (`fit_from_first`) also fails it.
- Minor 2 (collection-deadline paths): RESOLVED. The deadline test is now two rows: skew before collection and skew from a `matchMedia` hook while a 70-rule sheet is collected. Mutants: the check inside `visit` (`visit_check`) fails (the first loss would be named `.card p` instead of budget-exceeded), the `found.budget` check in `attributeLoss` (`found_budget`) fails.
- Minor 3 (inline-normal after collection): unchanged, accepted last round.

### Checks against the controller's questions
1. UTF-8 bytes, not JS length: CONFIRMED. `bytes` is `TextEncoder().encode(JSON.stringify(value)).length`. Direct call of `fitRoleReceipt` from the frame with one named selector of 360,000 CJK characters: JS length 360,303 (under the limit) but 1,080,303 bytes -> collapsed to 309 bytes; 400,000 characters likewise. The mutant that measures `JSON.stringify(...).length` instead (`js_length`) SURVIVES the repo tests (see Minor 1), so the byte measure is correct but unpinned.
2. Bounded serialization: CONFIRMED. A synthetic 128-outcome receipt of 1,805,128 characters (96 named entries each) was fitted to 1,035,970 bytes with 186 `JSON.stringify` calls: 128 initial, 1 envelope, then one re-measure per collapsed outcome (at most two passes), so at most 3n+1 calls. The last role ends fully unnamed, the first keeps names.
3. The break in the sheet loop (`if (found.budget) break;` after `visit`): the writer's "equivalent" claim is CORRECT. Mutant `sheet_break` survives, and reading the code shows why: once `found.budget` is set, `visit` returns at its first loop iteration, `attributeLoss` checks `found.budget` before any other use of `found`, and `unreadable` is not consulted after it. The break only skips cheap `cssRules` reads and `matchMedia` calls for the remaining sheets. Keep it as an optimisation; it needs no test.
4. The second collapse pass: UNREACHABLE within the limits, confirmed by arithmetic. After pass 1 every named group is merged, so each role has at most six properties x five unnamed reasons (inline, unreadable-sheet, complex-cascade, stylesheet-blocked, budget-exceeded; author-rule and inherited are always named) = 30 entries, 128 roles = 3,840 entries of about 96 bytes = 369 KB; outcome frames 23 KB; echoed `roles` at most about 240 KB (selectors are bounded by the 128 KiB canonical-CSS cap, plus ids and names) and `canonicalCss` at most 128 KiB, about 192 KB escaped; the sum is about 0.83 MB, under 1 MiB. Mutant `second_pass` survives. A deterministic test is feasible only by calling `__fontkitBridge.fitRoleReceipt(message)` directly with a synthetic message (as my probe does); it cannot be reached through the real page.

### Checks run
- Focused command (Chromium): test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -> Ran 101 tests, OK (50.1 s).
- Mutants (whole test_role_preview): killed fit_check, fit_from_first, visit_check, found_budget; survived sheet_break (equivalent), second_pass (unreachable), js_length (unpinned).

### Issues
#### Critical / Important
(none)

#### Minor
1. The byte-versus-length measure is untested (mutant `js_length` survives), and the dead second pass is untested. Both can be pinned in one small test that calls `__fontkitBridge.fitRoleReceipt` with a synthetic message (a CJK named selector whose string length is under the limit and whose bytes are over, and an outcome set whose pass-1 collapse is still over the limit). Alternatively delete the second pass, since it cannot be reached.
2. The fit measures the message before `post()` adds `protocolVersion` and `sessionId`. Probe: a message the fit leaves untouched at 1,048,574 bytes is 1,048,611 bytes on the wire (session id `s1`; up to about 235 bytes more with a 200-character id), over Studio's 1 MiB check on the received data. The window is a few hundred bytes wide and effectively unreachable, but the fix is trivial: add the envelope to the measured base (or reserve 512 bytes in the limit).

### Assessment
**Task quality:** Approved
**Reasoning:** The residual receipt-size defect is fixed: my 128-role case and a second adversarial case with long ids and CJK names both fit in 1 MiB with counts summing, the new test fails without the size check and without the last-to-first order, the measure is UTF-8 bytes, serialization is bounded, the two collection-deadline rows kill their mutants, and the writer's equivalent-mutant claim about the sheet-loop break is right. Two small pinning and margin items remain (Minor 1 and 2) and can be handled with the landing or a later pass.

**Verdict: Approved**

STATUS: COMPLETE (re-review 2)

## Scoped re-review (fix round 3)

Patch task-2.5-code-r3.patch sha256 1a601761... equals the staged tree in C:/fks/t25 (git diff --cached | sha256sum = 1a6017612969f7b5). t25 not edited; mutants through the open() bridge_source seam (mutate_t25rr3.py); probe_t25rr3.py (scratchpad). ASCII only.

### Item 4: nothing else changed since r2
The interdiff r2 -> r3 is exactly three things: `const limit = 1048576 - 1024;` in `fitRoleReceipt`, the collapse loop condition `total > limit` (was `total > 1048576`), and one new test. Everything else differs only in hunk offsets. RESOLVED.

### Item 1: the posted receipt never exceeds 1 MiB (probe on the real host)
Sweep of the same fixture shape (128 roles, 14 shared rules, CJK names) with the name padding moved so that the pre-fit size straddles the new threshold (1,047,552). Sizes are compact UTF-8 bytes of the receipt as the host received it (envelope included):
- pre-fit 1,048,547 (over the threshold) -> collapsed, posted 1,041,974;
- pre-fit 1,047,557 (just over) -> collapsed, posted 1,040,984;
- pre-fit 1,047,545 (just under) -> not collapsed, posted 1,047,582, that is +37 bytes for `protocolVersion` and `sessionId` (`s1`), still 994 bytes under 1 MiB;
- pre-fit 1,047,534 / 1,047,522 / 1,047,396 -> not collapsed, posted 1,047,571 / 1,047,559 / 1,047,433.
No case exceeds 1,048,576. The 1,024-byte headroom covers a 200-character session id (about +235 bytes) with room to spare. RESOLVED. (Counts sum to 14 per role and property in the repo test; the earlier 128-role and long-id cases from re-review 2 are unchanged by this round.)

### Item 2: the new test fails on both mutants
`test_the_receipt_fit_counts_utf8_bytes_and_leaves_room_for_the_posted_envelope`, run through the seam against the whole test_role_preview module:
- bytes measured as `JSON.stringify(value).length` (`js_length`) -> 1 failure, `1048585 not less than or equal to 1048576`;
- headroom removed (`const limit = 1048576;`, `headroom`) -> 1 failure, the same assertion.
Both reproduced by me. RESOLVED. (The fit-removed mutant is also covered: the hook would find no fit to wrap and the test would error.)

### Item 3: the fixture premise is asserted and cannot pass vacuously
The test wraps `fitRoleReceipt` to record the pre-fit receipt, then asserts before the behaviour: string length under 1 MiB minus 1 KiB (so the length mutant would not collapse), UTF-8 length plus 37 above 1 MiB (so the old limit would post an oversized receipt), and UTF-8 length at most 1 MiB (so the receipt is not already collapsed by the old rule). If the hook never runs `window.beforeFit` is undefined and the subscripting raises, so a missing fit fails loudly too. Pre-fit bytes were 1,048,546-1,048,548 over 12 runs: the premise window is [1,048,539, 1,048,576], so there is 1-2 bytes of observed variation (the `documentId` carries a random base-36 suffix, `Math.random().toString(36).slice(2)`) against 8 bytes of margin on the low side and 28 on the high side. A larger drift fails the premise with a message rather than passing. RESOLVED.

### Checks run
- Focused command (Chromium): test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -> Ran 102 tests, OK (57.8 s).

### Issues
#### Critical / Important
(none)

#### Minor
1. The docstring of the new test says "100-character CJK names" while the code builds 199-200 character names (and the report quotes a different string length); the premise assertions are correct, only the prose is stale. Fix the wording when convenient.
2. The premise window is 37 bytes wide and tuned by hand (ids of 3-4 CJK characters, names of 199-200). It fails loudly when the envelope or ids drift, as required, but a drift of 9 or more bytes toward shorter output (for example a shorter `documentId` format) would need retuning; the test comment says so.

### Assessment
**Task quality:** Approved
**Reasoning:** The 1 KiB headroom makes the posted receipt, envelope included, stay under 1 MiB across the whole threshold window on the real host, the new test fails on both the string-length and the no-headroom mutants, its premise is asserted before the behaviour, and the interdiff contains nothing else.

**Verdict: Approved**

STATUS: COMPLETE (re-review 3)
