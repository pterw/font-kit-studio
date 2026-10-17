# Task 2.5 code report (MODE code, BASE 5041b84, worktree C:/fks/t25)

Patch: `.superpowers/sdd/r2/task-2.5-code.patch` (4 files, about 650 material lines).
Files: `fontkit-bridge.js` (measurement only: `roleMismatches`, `measureRoleOutcomes`, new
`roleComputed`, `roleSame`, `roleDeclared`, `collectAuthorRules`, `attributeLoss`),
new `tests/test_role_preview.py`, new `tests/fixtures/bridge/role-preview-evil.css`,
`tests/test_role_stylesheet.py` (3 assertions, hover test).

## Brief steps
All pins and the Additions 1-9 are done. Deviations and judgement calls are listed below.

## RED / GREEN
- RED (new tests, BASE bridge restored, same test file): `python -m unittest test_role_preview`
  gave `Ran 13 tests ... FAILED (failures=14)`. Example: `.card p` loss was
  `'reason': 'complex-cascade', 'winningSelector': None` where `author-rule` / `.card p` was expected;
  10,001 page gave `matched 10000` not 10001; no-text case `matched 2` not 4.
  Log: scratchpad `red-t25.log`. Characterized GREEN already at BASE: nothing manufactured
  (the CSP rejection is covered in the existing test and is not repeated here).
- GREEN: `PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -v`
  -> `Ran 98 tests in 53.958s  OK` (Chromium only; no skips).
- `node --check fontkit-bridge.js` ok; `python scripts/verify.py --static-only` provenance PASS, browser SKIP;
  `python -m ruff check . --exclude .agents` All checks passed; `git diff --check` and `--cached --check` exit 0;
  `python -m pre_commit run --files <4 files>` all hooks Passed.

## Mutations (restored by bytes in finally, sha256 verified; script scratchpad `mutate-t25.py`)
Every mutation was killed by `test_role_preview` (hover by its own test):
computed comparison removed (2 fail); deduplication removed (overlapping selectors/roles test);
unknown branch always author-rule (13 fail); active @media check removed; active @supports check removed;
unreadable-sheet check removed (2); selector length cap removed (cap test); plus closed-world guards:
other-role owner, assignedSlot, adopted sheets, nested parent, layer complex flag, animation, inline !important,
stylesheet-blocked, pending-sheet detection, 16-group cap. Hover: window moved to 3.0x scan time fails with
`the hover never landed while the scan was pending: [...]`.

## Timings
- 10,000 lost elements, one author rule (`test_ten_thousand_attributed_losses...`): complete, exact counts,
  whole test (page build + apply) 1.3 s.
- Existing Apply-then-Detect on the 5,000-parent page: `APPLY_THEN_DETECT elapsedMs 779.7, complete true, scanned 5000`
  (D058 limit 2,000 unchanged).

## Changed `test_role_stylesheet.py` assertions
1. `test_zero_matches_are_a_real_measured_result...`: union `matched` 2 -> 3 (hidden paragraph matched, not checked); docstring reworded.
2. `test_a_winning_author_rule_is_a_counted_loss...` (renamed `..._named_as_the_proven_winner`): card loss now
   `winningSelector '.card p'`, reason `author-rule`; docstring updated.
3. `SplitPageVersionTests.test_native_hover_during_a_scan_...`: rewritten with a calibration scan, a hover timed at
   0.5/0.35/0.2 of its elapsedMs, and a failing premise message (see mutation above).

## Judgement calls / limits
- A matching declaration under @layer/@container/@scope/unknown grouping, a matching parent with nested rules, and
  animations give `complex-cascade` even when an unreadable sheet exists. Other closed-world breaches (adopted sheets,
  slot, shorthand hiding a longhand inline or in a rule, another role declaring the property, a `matches()` throw,
  a non-comparable value, no candidate) take the "no proof" path: `unreadable-sheet` if any sheet is unreadable or
  sheet-less, else `complex-cascade`. The adopted-sheet case is reported `complex-cascade` (no unreadable sheet).
- A failed (aborted or 404) `<link>` keeps an empty readable sheet in Chromium, so only a pending/sheet-less node counts
  as unreadable; the test holds a request open and aborts it in cleanup.
- Not covered by a test: `matches()` throwing (no portable selector reproduces it), `@import layer()`, an owned node
  moved into a shadow root, the 1,000 ms attribution sub-deadline (`budget-exceeded` loss reason) and Firefox.
  These branches are in the code, with no deterministic trigger found.
- Role selector grammar forbids the descendant combinator, so the other-role case uses `.{c} > p`.

## Handoff
- Studio (S2 phase 2): show `matched` as "elements this role matches"; `checked` as "measured (rendered text)",
  so `checked < matched` with `complete: true` means unmeasured elements without rendered text, not a failure;
  `complete: false` only means the budget stopped measuring or attribution (reason `budget-exceeded`). Reasons:
  author-rule "overridden by <selector>"; inline "overridden by inline style"; inherited "inherits from parent via
  <selector>"; unreadable-sheet "a stylesheet could not be read"; complex-cascade "overridden; source not provable";
  stylesheet-blocked "the page disabled the preview sheet"; budget-exceeded "not attributed in time". Losses are
  capped at 16 groups per role and property, the remainder merged into one unnamed complex-cascade group.
  S2 must validate `winningSelector` as bounded text (at most 2,000 characters, no control characters) and render it
  with `textContent`; it is never the role selector grammar (it may be a selector list or contain descendant combinators).
- CHANGELOG line: "Role preview receipts now count matched and checked elements separately and explain each
  lost property (author rule with its selector, inline style, inherited, unreadable stylesheet, complex cascade,
  blocked stylesheet)."
- Ledger draft (D065): Pin 1 `matched` is the distinct selector-union count; closed-world naming; reason order
  stylesheet-blocked, inline !important, animation, inline, rules; one shared value comparison; attribution
  sub-deadline 1,000 ms; 16 groups per role/property.
- Plan checkboxes: R2.5 task items (tick at landing). Commit subject suggestion:
  `feat(bridge): explain role preview losses and count matches honestly`.

## Fix round 1
Patch: `task-2.5-code-r1.patch` (full diff against 5041b84), sha256 `9809d350f93156b014a9b820fd6d781622099e03e902df347642a2fe25689438`.
Material about 790 lines (bridge +245/-25, tests 476 + 39/-22, fixture 2).

Changes
1. Nested rules: any readable nested style rule that declares the property makes it complex-cascade for every element
   (`found.nestedProps`); the parent-match guard is gone. Nested rules declaring other properties do not spoil a proof.
2. Receipt budget: named `winningSelector` text across all outcomes is capped at 262,144 characters; the largest counts
   keep names, the rest merge into the role/property `{null, complex-cascade}` group (counts still sum). 16-group cap kept.
3. New deterministic tests (table rows or one method each): `matches()` throw via `@namespace x|p`; layered `@import`;
   pending `@import` and pending link; adopted sheet; nested declaration; disabled author sheet and inactive
   (print / unsupported supports) imports never named; owned node moved into a shadow root and media attribute and disabled
   (stylesheet-blocked); the 1,000 ms deadline through a `performance.now` skew (budget-exceeded, complete false);
   inline `font: var()`; `unset`; two inheriting selectors; inherited lineHeight ratio; largest-first sort (triples now sort last).
4. Inline normal is `inline` only when its value is comparable and equals the computed value and no matching
   `!important` author candidate exists; otherwise it falls through (important author rule is then named by the proof,
   an uncomparable inline gives complex/unreadable fallback).
5. Minors: open shadow host (`el.shadowRoot`) breaks the closed world; a pending `@import` (null `styleSheet` or throwing
   `cssRules`) is unreadable; `layerName` unsupported counts as layered; hover test now lands in the first half of the
   calibrated scan (fractions 0.3/0.2/0.1, premise requires delay <= half of calibration) with a premise message.
   Skipped: elements inside a shadow root (never matched, since selection uses `document.querySelectorAll`, so no code path);
   CSP test duplicate kept (brief lists it).

RED (new/changed tests against the round-0 bridge, log `red-r1-t25.log`): 6 failing subtests: nested non-spoil row,
important-beats-inline row, shadow-host row, whole-receipt bound (receipt exceeded 1 MiB), pending import, nested declaration.
The rest (throw, layered import, shadow-moved owned node, deadline, disabled/inactive sheets, unset, ratio, sort) pass at once:
they characterise behaviour that already worked, and are pinned by the mutants below.

GREEN: `python -m unittest test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -v`
(Chromium, FKS_REQUIRE_FIXTURES=1) -> `Ran 100 tests ... OK`; APPLY_THEN_DETECT elapsedMs 745.3. node --check, verify
--static-only (provenance PASS, browser SKIP), ruff --exclude .agents, git diff --check (plain and cached) and pre-commit all pass.

Mutants (script `mutate-r1-t25.py`, byte restore in finally, sha256 verified): all 35 failed a test except two,
including: nested declaration check, receipt budget (the hostile test fails when it is removed), important-candidate
check, shadowRoot, pending import, matches() throw guard, layered import (after making the data import declare `.card p`),
attribution deadline, disabled author sheet, inline shorthand guard, `unset`, single-selector inherit, lineHeight ratio,
inactive import skip, largest-first sort, hover margin (fractions 0.9 fail with the premise message), plus the round-0 list.
Survivors, judged equivalent: (a) `getRootNode() === document` on the owned node: the sibling check
"sheet present in document.styleSheets" already catches a shadow-moved node; (b) rule-level `all` detection: Chromium
expands `all` into longhands (`unset`), so the unreadable-longhand branch never triggers for `all` there.
Untested guards: `found.budget` during collection (needs a very large sheet; reviewer probe covers it).

Handoff addition: author-rule is proven against document-level CSS only; closed shadow roots are undetectable.

## Fix round 2
Patch: `task-2.5-code-r2.patch` (full diff against 5041b84), sha256 `3442e08fbfd97262ff00fe31cff8f176915919a4343d5c9a2a1692d4b7742a1f`.

1. Receipt size (Important). `postRoleReceipt` now calls new `fitRoleReceipt`: each outcome is serialized once (UTF-8 bytes of
   compact JSON, plus the envelope with `outcomes: []`, which includes the echoed roles and canonicalCss). If the total exceeds
   1,048,576 it collapses from the last role backwards, first merging every named group into one `{null, complex-cascade}`
   entry per role and property, then (second pass, if still over) merging all remaining entries per role and property. Only the
   collapsed outcome is re-measured. Counts always sum; contract order is kept. The 16-group and 262,144-character caps stay.
   Test `test_a_receipt_with_thousands_of_entries_is_collapsed_to_fit_one_mebibyte`: the reviewer's shape (128 roles, 16 short
   shared rules, 12,288 entries). RED against the round-1 bridge: `AssertionError: 1101443 not less than or equal to 1048576`.
   GREEN: at most 1 MiB, every role/property sums to 16, first role keeps names, last role fully unnamed.
   Mutants: size check removed (fails), collapse from the first role (fails). The second pass is not reachable in Chromium
   within the limits (128 roles x 6 properties x 7 reasons of unnamed entries plus both echoes fits), so it has no test.
2. Collection deadline (Minor). The deadline test is now a two-row table: the `getAnimations` skew (before collection) and a
   `matchMedia` skew with a 70-rule sheet (during collection, so the 64-rule check in `visit` trips). Mutants: the check inside
   `visit` removed (fails), the `found.budget` check in `attributeLoss` removed (fails). The break in the sheet loop after
   `visit` survives and is equivalent: the next `visit` call returns at once when `found.budget` is set.

Gates: `python -m unittest test_role_preview test_role_stylesheet test_role_protocol test_bridge_runtime.HandshakeTests test_support -v`
-> `Ran 101 tests ... OK` (Chromium, FKS_REQUIRE_FIXTURES=1; APPLY_THEN_DETECT 611.5 ms); node --check, verify --static-only
(provenance PASS, browser SKIP), ruff --exclude .agents, git diff --check (plain and cached) and pre-commit pass. Mutants restored
byte-exact (sha256 verified); script `mutate-r2-t25.py`, RED log `red-r2-t25.log`.

## Fix round 3
Patch: `task-2.5-code-r3.patch` (full diff against 5041b84), sha256 `1a6017612969f7b5bad3913b886c6424ee1a3b404c36639024172e67ee3b6ff6`.

1. Envelope headroom: I chose "fit to 1 MiB minus 1 KiB" (`limit = 1048576 - 1024` in `fitRoleReceipt`). The bridge adds
   protocolVersion and sessionId (about 37 bytes) when it posts; 1 KiB covers that with room. Serializations stay bounded:
   one per outcome plus one for the envelope, and one more per collapsed outcome.
2. New test `test_the_receipt_fit_counts_utf8_bytes_and_leaves_room_for_the_posted_envelope`: 128 roles with 199-200 character
   CJK names and 3-4 character CJK id suffixes (14 short shared rules per role). A hook on `fitRoleReceipt` records the receipt
   before fitting; the test asserts the premise (string length 994,900-ish, under the limit; UTF-8 length 1,048,548, within 37
   bytes of 1 MiB so the posted fields would push it over), then that the posted receipt is at most 1 MiB and every role and
   property still sums to 14.
   RED against the round-2 bridge: `AssertionError: 1048585 not less than or equal to 1048576`.
   Mutants (restored byte-exact, script `mutate-r3-t25.py`, sha256 verified): bytes replaced by string length -> fails
   (1048584 over 1 MiB); headroom removed -> fails (same); fit removed -> fails (the hook finds no fit to wrap).
   The premise bytes are deterministic for this fixture; if the envelope or ids change, retune name and id padding.

Gates: focused command -> `Ran 102 tests ... OK`; node --check, verify --static-only (provenance PASS, browser SKIP), ruff
--exclude .agents, git diff --check (plain and cached), pre-commit all pass.

## Controller integration (2026-10-16)

The final patch (`task-2.5-code-r3.patch`, sha256 `1a601761...`) applies with
`git apply --3way` onto `2eff32d`, a docs-only change after the code-phase BASE
`5041b84`, with no conflict. Each staged blob equals the code-phase worktree's
index. The controller also corrected one docstring in `tests/test_role_preview.py`:
the CJK names are 199-200 characters, not 100.
- `test_role_preview test_role_stylesheet test_support` (Chromium): Ran 91 tests in 45.674 s, OK.
- `test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests`
  `test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything test_live_integration`
  (Chromium): Ran 81 tests in 229.009 s, OK.
- Firefox and WebKit were not run for this landing; the advisory Firefox canary
  and the full Chromium halves run at the settled wave.
- Fast gates: static checks, `node --check` and product-tree Ruff pass, and
  `git diff --check` is clean on both the working tree and the index. Exact
  Ruff reports only the four preserved findings in the owner's untracked
  `.agents/`.
