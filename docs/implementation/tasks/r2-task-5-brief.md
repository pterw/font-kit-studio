# R2.5 brief: honest preview and cascade limits

Plan task R2.5 in `docs/plans/2026-10-03-r2-engine.md`, as changed by Addendum 13
(R2.5 follows R2.3 in PR B; the bridge stays plain-adapter only). Binding:
the protocol contract (RoleOutcome, `design:roles-applied`), the "Computed
mismatch counts are authoritative" paragraph, D058, D061 and D063. R2.3's
pins are in `r2-task-3-brief.md`, "Additions after dispatch" items 3-4; this
brief changes only the `matched` pin and the loss reasons, as stated below.

Mode code. BASE `5041b84` (R2.3 landed at `68b2a87`). Worktree `C:/fks/t25`.

## Exact ownership

- `fontkit-bridge.js`: the outcome measurement only (`measureRoleOutcomes`,
  `roleMismatches` and new helpers it calls). Detection, apply/clear
  validation, install, receipts' envelope and the page-version rules stay as
  they are.
- New `tests/test_role_preview.py`.
- New fixture files under `tests/fixtures/bridge/` named `target-role-preview*.html`
  or `role-preview-*.css`, if a static page is clearer than runtime setup.
- `tests/test_role_stylesheet.py`: only assertions that the `matched` pin
  below changes. Name each changed assertion in the report.
- Read-only: `tests/role_support.py`, `tests/support.py`, every other test
  module, Studio, fixtures outside the names above, docs.

## Bridge facts at BASE

- `measureRoleOutcomes(job)` (generator, 8 ms slices, 2,000 ms from the
  measurement start, 10,000 eligible elements) walks the union of all roles'
  selectors once. An element is eligible when it has a direct text node that
  `renderedRoleText` accepts. Today `matched == checked`, and every loss is
  `{winningSelector: null, reason: 'complex-cascade'}`.
- Role CSS is normal priority (no `!important`) in the owned `<style>`,
  appended last in `<head>`. Inspector edits are inline `!important`
  (`setStyle`). Bridge font links (`bridgeFontLinks`) and the owned sheet are
  bridge-owned.
- `roleMismatches(style, props)` compares computed values with fixed
  tolerances; keep its comparisons.

## Required behaviour (pins)

1. **Counts.** Per role: `matched` is the number of distinct elements that the
   role's selector union matches in the document, counted in full even when
   the budget stops. `checked` is the number of eligible elements among them
   that were measured. `mismatched` is the number of checked elements that
   lost at least one property. `0 <= mismatched <= checked <= matched`. Zero
   matches is `matched: 0`, and an incomplete check is `complete: false` with
   `checked < matched`. Never count unchecked elements as losses.
2. **Loss entries.** Group losses by `(property, reason, winningSelector)`.
   Each group is one entry, and its `count` is the number of checked elements
   that lost that property for that reason. For each property, the counts sum
   to the elements that lost it. Order entries by ROLE_PROPERTY_KEYS, then by
   the contract's reason order, then by winningSelector (null first, then
   code-unit order).
3. **Reasons.** For each checked element and lost property, take the first
   rule that applies:
   1. `stylesheet-blocked`: the owned sheet is not active at measurement
      (disabled by the page, detached, or its rules no longer equal the
      reference parse). `winningSelector` is null.
   2. `inline`: the element's own `style` declares the property, at any
      priority (an inspector edit or an author inline style). Null.
   3. `complex-cascade`: an animation or transition from `getAnimations()`
      affects the property. Null.
   4. `author-rule` with a winning selector, only when it is proven. Collect
      readable style rules once per job, excluding the owned sheet and bridge
      font links:
      - Recurse into `@media` only when it matches, `@supports` only when
        `CSS.supports(conditionText)` holds, and `@import`.
      - A matching declaration inside `@layer`, `@container`, `@scope`, a
        nested rule or an unknown grouping rule makes this element's property
        complex-cascade.
      - A candidate is a rule whose `selectorText` matches the element and
        that declares the property.

      Proof: no active sheet is unreadable, every candidate's value is
      absolute and comparable, and exactly one distinct `selectorText` among
      the candidates has a value equal to the computed value and different
      from the role's value. Absolute and comparable means px lengths,
      unitless numbers, keywords, a family list compared with `familyNames`,
      or `normal` letter-spacing as 0. `em`, `rem`, `%`, `calc()` and `var()`
      are not comparable. Report that `selectorText`, CSSOM-serialized and at
      most 2,000 characters. A longer selector is null with complex-cascade.
   5. `inherited`: as in 4, but the only candidate declares `inherit` (or
      `unset` for these inherited properties), and the element's computed
      value equals its parent's. Report that candidate's selector.
   6. `unreadable-sheet`: no proof, and at least one active sheet's `cssRules`
      throws. Null.
   7. `budget-exceeded`: the loss was counted, but attribution stopped at the
      budget. Null. The outcome is then also `complete: false`.
   8. Otherwise `complex-cascade`. Null.

   Never guess a winner from the last matching selector, specificity
   arithmetic or document order. Do not read or change author sheets other
   than through CSSOM reads, and never write to the DOM to probe.
4. **Budget.** Attribution shares the existing 2,000 ms measurement budget
   and slices. Collecting candidate rules yields too. The large-page
   Apply-then-Detect path stays inside D058's timings: report the timings,
   and do not loosen any existing limit.
5. **Freshness.** It is unchanged. A page or style change during measurement
   still makes the receipt stale (D063).

## Tests (`tests/test_role_preview.py`, real bridge through `RoleBridgeCase`, Chromium)

- **RED first.** An author `.card p` rule beats the role's normal
  declaration. The receipt names `.card p` with `author-rule` and the
  computed count. At BASE it says complex-cascade/null.
- Inline `!important` inspector override gives `inline`. An author inline
  style gives `inline`. An `inherit` declaration gives `inherited`.
- Ordinary readable rules prove a winner. An inactive `@media` or
  `@supports` rule is never named; the active one is.
- `@layer` and a running animation give complex-cascade.
- An inaccessible cross-origin stylesheet (served from `EVIL` without CORS)
  gives `unreadable-sheet` with an exact count.
- The owned sheet disabled by the page after commit gives
  `stylesheet-blocked`. A CSP-blocked install is still a `design:rejected`
  `stylesheet-blocked`, never an applied success.
- Two candidates with equal values give complex-cascade. Relative units give
  complex-cascade.
- Count pins:
  - Zero matches.
  - Matched elements without text: `checked < matched`.
  - Deduplication across overlapping selectors and roles.
  - Grouping and order of the loss entries.
  - The 10,001-element page: `checked` 10,000, `matched` 10,001,
    `complete: false`.
- Rendered state: every reported count matches computed styles that the test
  reads itself. No test passes when attribution is deleted.
- Mutation probes, each restored by bytes in a `finally`:
  - remove the computed comparison;
  - remove deduplication;
  - remove the unknown branch (always author-rule);
  - remove the active `@media`/`@supports` check;
  - remove the unreadable-sheet check;
  - remove the selector length cap.
- Every test method gets a Given/When/Then docstring. Wait on conditions,
  never on fixed sleeps, except short waits that prove an absence.

## Focused gates

`$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'; python -m unittest test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -v`,
plus `node --check fontkit-bridge.js`, `python scripts/verify.py --static-only`,
`python -m ruff check . --exclude .agents` and `git diff --check`. The full
halves run at the settled wave.

## Report and done

Report at `.superpowers/sdd/r2/task-2.5-code-report.md`, patch at
`.superpowers/sdd/r2/task-2.5-code.patch` (full diff against BASE, new files
included). The report covers:

- RED and GREEN output and the focused counts;
- each mutation's failing line;
- the timings;
- every changed `test_role_stylesheet` assertion;
- a Handoff section for Studio (S2 phase 2: how `matched`, `checked` and each
  reason should read), with a CHANGELOG line and a ledger draft.

Done when losses are measured and explained honestly, a winner is named only
when proven, and the counts match rendered state.

## Additions after dispatch (2026-10-16)

These replace pins 1, 3 and 4 and the ownership list where they conflict.

1. **Closed world.** Name a winner only when every source that could set the
   property on that element is readable and enumerated. Anything else is
   `complex-cascade`, or `unreadable-sheet` where 3.6 applies. Each of these
   breaks the closed world for the element and property:
   - another role's rule in the owned sheet matches the element and declares
     the property;
   - `document.adoptedStyleSheets` is non-empty;
   - a `<link rel=stylesheet>` or `<style>` has no `.sheet` (pending or
     failed): treat it as unreadable;
   - `el.assignedSlot` is set;
   - a matching `all`, `font` or `var()`-based shorthand reads back an empty
     longhand, inline or in a rule;
   - `matches()` throws for a candidate selector (never "skip");
   - nested rules under a matching parent rule;
   - `@layer`, `@container`, `@scope`, or `@import` with `layer()`.

   `@import` with non-matching `media` or `supports`, a disabled sheet and an
   alternate sheet are inactive and never named. A `selectorText` that is a
   list is reported whole, as CSSOM serializes it.
2. **Reason order** (this replaces 3.2-3.3):
   1. `stylesheet-blocked`. The owned node also counts as blocked when it has
      a `media` attribute, has been moved into a shadow root, or is missing
      from `document.styleSheets`.
   2. `inline` for an inline `!important` declaration.
   3. `complex-cascade` for an animation or transition. Call
      `document.getAnimations()` once per job.
   4. `inline` for an inline normal declaration.
   5. The rest of pin 3 from 3.4 on.
3. **One value comparison**, shared with `roleMismatches`, so the two cannot
   drift:
   - lineHeight: a unitless number is multiplied by the computed font-size;
     an `inherited` lineHeight loss compares ratios;
   - the existing tolerances apply;
   - `bolder`, `lighter`, `larger`, `smaller` and the CSS-wide keywords other
     than the `inherit`/`unset` case in 3.5 are not comparable.
4. **Pin 1 fix.** `complete` is false only when the budget stops measuring.
   Matched elements without rendered text give `checked < matched` with
   `complete: true`.
5. **Performance.**
   - Collect and index rules lazily: only when the job has at least one loss,
     and by declared property.
   - Memoise `matches()` per element and rule.
   - Attribution has a sub-deadline of 1,000 ms after measurement starts.
     After it, counting continues and the remaining losses get
     `{winningSelector: null, reason: 'budget-exceeded'}`, with the outcome
     `complete: false`.
   - One timed test: 10,000 lost elements on the large page stay inside the
     2,000 ms budget, with exact counts.
6. **Reply cap.**
   - Keep at most 16 loss groups per role and property, the largest counts
     first.
   - Merge the rest into one `{winningSelector: null, reason: 'complex-cascade'}`
     group, so the counts still sum.
   - Add one hostile test near the 1 MiB receipt limit: many distinct long
     winning selectors.
7. **Ownership.** You may change `tests/test_role_stylesheet.py` assertions that
   pins 1-3 change: `matched` at line 207 (2 -> 3 for the hidden paragraph)
   and the `.card p` test at lines 221-233, which now expects `author-rule`
   with `.card p`.

   Also harden `SplitPageVersionTests.test_native_hover_during_a_scan_still_makes_it_page_changed_with_equal_versions`.
   It failed once on hosted Linux CI (run 38951345019): its premise passed but
   the scan completed. `scanStart` is recorded by a listener that may run
   after the bridge has already started the scan, so a hover just after the
   terminal check can still pass the premise. Time the hover from a
   calibration scan, as R2.T1 does: land it early and require a margin. The
   test must fail with a premise message when the hover is late. Name every
   changed assertion in the report.
8. **Size.** Aim for at most about 1,200 material lines (code, tests and
   fixtures). Prefer table-driven tests (one subtest per cascade case) over
   one method per case.
9. **Studio.** Studio's handling of `winningSelector` is not yours. In the
   Handoff, state that S2 must validate it as bounded text: at most 2,000
   characters, no control characters, rendered with `textContent`. It is
   never the role selector grammar.