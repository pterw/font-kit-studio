# Task 5 brief: three small bridge fixes (B14, G1-5, B01)

Plan task 5, wave 1, `BASE 5443ff6`, worktree `the task's worktree`, mode code. Audit rows B14, G1-5, B01 (all S3). Budget: about 90 gross
lines (source about 15, tests and fixtures about 75). Three commits, three patches, in this order: B14, G1-5, B01. Rules: `../constraints.md`
(O27 to O31, O38 to O41 apply; O31 approves New string 4 as written, so B01 waits for nothing).

## Why

1. B14. Moving a `li`, `pre`, `dl`, `fieldset`, `figcaption`, `hr`, `main` or `dt` into a `<p>` is applied, then Chromium's parser re-nests
   it on reload, so the saved layout differs from what the user saw. The guard at `fontkit-bridge.js:2673` tests `BLOCK_ELEMENTS`
   (94-95), which lacks these eight tags. A `div` is already refused there with guard `content-model`.
2. G1-5. `SEMANTIC_SELECTORS` (114-120) ends in `'[class*="stat"]'` (line 119), a substring match: `static`, `status`, `state` each become a
   target and get `data-design-*` attributes written into the app's DOM (used at 3488 and 3541).
3. B01. A hashed `type="module"` bundle has no `document.currentScript` (line 74 is null). `resolveAllowedOrigins` (568-577) then looks
   for `script[src*="fontkit-bridge"][data-allowed-origins]` (571), which a hashed bundle name never matches. The list is lost, `null` is
   returned ("any origin") and nothing is said.

## Owned files (exact)

- `fontkit-bridge.js`, only: lines 94-95 (`BLOCK_ELEMENTS`), line 119 (the `stat` entry), lines 566-577 (`resolveAllowedOrigins`
  and its comment), and one module-level `let` flag directly above `resolveAllowedOrigins`. Line 2673 is read-only: the existing test
  is unchanged and the guard needs no edit there. Other tasks edit other regions of this file at once (Addendum 1).
- `tests/test_bridge_runtime.py`: new class `ContentModelGuardTests` additions only as a new test method directly after
  `test_block_elements_cannot_go_into_inline_or_phrasing_parents` (3465 at BASE); a new class `AutoSelectorWholeNameTests` directly after
  `AutoSelectorTests` (3305); a new class `UnreadOriginListTests` directly after `OriginListTests` (388). Never at a file end.
- New fixtures: `tests/fixtures/bridge/target-stat-names.html`, `tests/fixtures/bridge/target-module-bundle.html`,
  `tests/fixtures/bridge/target-classic-capture.html`.
- `tests/test_role_detection.py`: the plan lists it, but no row needs it (grep shows no `stat` class there). Do not touch it.
- No CHANGELOG edit: the controller owns the ledger lines and Task 18 states the G1-5 limit. Everything else is read-only.

## Read first

- `fontkit-bridge.js` 91-97, 110-121, 562-577 (all at BASE), and 2670-2677 for the message text.
- `tests/test_bridge_runtime.py` 3455-3500 (guard tests, the `ArrangeCase` helpers `start`, `move`, `rejected` at 1799-1830),
  247-258 (restricted fixture use), 3305-3328.
- `tests/fixtures/bridge/target-arrange.html` (88 lines; `arr.para` is a `<p>` at line 59) and `target-restricted.html`.

## Requirements

1. B14. `BLOCK_ELEMENTS` gains `li`, `pre`, `dl`, `fieldset`, `figcaption`, `hr`, `main`, `dt`. Moving any of them into `arr.para` is
   rejected `unsupported-value`, guard `content-model`, `overridable: false`, same message shape as a `div`, and the DOM is unchanged.
   Oracle: the test also loads the same markup into a fresh page via `page.set_content` (a second run, the real parser) and asserts the
   parser had re-nested each tag outside the `<p>` (its `parentElement` is not the `<p>`), which is why the guard is right. A `div` into `em`,
   `code` or `strong` stays allowed (`moved` returns `design:applied`). Add the needed `<li>`, `<pre>`, `<dl>`, `<fieldset>`,
   `<figcaption>`, `<hr>`, `<main>`, `<dt>` and `<em>`/`<code>`/`<strong>` nodes as a new fixture section only if `target-arrange.html`
   lacks them; prefer building the nodes in the page with `frame.evaluate` and giving them `data-design-id` before `hello`, to keep fixtures untouched.
2. G1-5. Replace `'[class*="stat"]'` with `'.stat'`; leave the five other `[class*=...]` entries exactly as they are. Oracle: literal. In
   `target-stat-names.html` (`<div class="static">`, `<div class="status">`, `<div class="stat">`, each with text, no `data-design-id`), `hello`
   returns exactly one target whose element has class `stat`, and the `static` and `status` elements have no attribute starting `data-design`.
3. B01. When `resolveAllowedOrigins` was called with no option, no script was read (neither `currentScript` nor the lookup supplied
   an attribute), and `document.querySelector('script[data-allowed-origins]')` exists, call `console.warn` once with exactly New string 4:
   `[FontKitBridge] data-allowed-origins could not be read from this script, so any origin is accepted. Pass allowedOrigins in window.FONTKIT_BRIDGE_OPTIONS.`
   A module-level flag makes it once per page load. Return value unchanged (`null`). The rest of the message contract (ways out:
   `window.FONTKIT_BRIDGE_OPTIONS`, `new FontKitBridge({allowedOrigins})`) is carried by the README later; the console string is only New string 4. No new message type, no wire change.
   A classic tag that was read (including `data-allowed-origins="*"`, which parses to `null`) warns nothing.

## Tests

Each new test has a Given/When/Then docstring and loops `for engine in ENGINES` like its neighbours.

- B14, `test_these_block_elements_cannot_go_into_a_paragraph_and_the_parser_would_re_nest_them` (GREEN after the fix; RED before: the move
  is `design:applied`). Given the arrange page with one node of each tag, When each is moved into `arr.para`, Then each is rejected
  `content-model`, the `main` innerHTML is unchanged, and `set_content` shows the parser re-nested it. One realistic break: delete one tag
  from the set; that tag's subcase fails.
- B14, `test_a_div_can_still_go_into_em_code_and_strong` (GREEN characterization, already works): Given those three parents, When a `div` is
  moved into each, Then `design:applied` and `errors(frame)` is `[]`. Do not manufacture RED.
- G1-5, `test_only_the_whole_class_stat_is_discovered` (RED: three targets today). Break: restore `[class*="stat"]`.
- B01, `test_a_module_bundle_that_carries_the_origin_list_warns_once_and_accepts_any_origin` (RED: no warning today). The fixture
  `target-module-bundle.html` has a classic inline script first that wraps `console.warn` into `window.__warns`, then
  `<script type="module" data-allowed-origins="http://studio.test">import '/fontkit-bridge.js';</script>`. The import creates no script element, so
  `currentScript` is null and the lookup misses, exactly like a hashed bundle. Check that the bridge boots as a module; if it does not, report under Open questions.
  Then: after `hello` from `EVIL`, the reply is `design:ready` (any origin accepted), and `window.__warns` equals the one New string 4 literal.
  Break: drop the flag check; a repeated call adds a second line (assert length 1 after a `new FontKitBridge()` too).
- B01, `test_a_classic_script_tag_keeps_its_list_and_warns_nothing` (GREEN characterization). `target-classic-capture.html` is
  `target-restricted.html` plus the same `__warns` wrapper. Then `__warns` is `[]` and a hello from `EVIL` times out, as at 250-253.

## Focused command

From `the task's worktree`: `PYTHONPATH=tests FKS_ENGINES=chromium timeout 600 python -m unittest test_bridge_runtime.ContentModelGuardTests test_bridge_runtime.AutoSelectorWholeNameTests test_bridge_runtime.UnreadOriginListTests test_bridge_runtime.OriginListTests test_bridge_runtime.AutoSelectorTests test_support -v`
One module, no shards, no dev server. Studio landings do not apply (bridge-only), so the plan's three Studio modules are not run here.
Show RED output for the three new-behaviour tests before the fix.

## Patches

Return `task-5-B14.patch`, `task-5-G1-5.patch`, `task-5-B01.patch`, each self-contained (its own tests and fixtures), applied in that order.
Commit subjects:

- `fix(bridge): refuse more block elements inside a paragraph`
- `fix(bridge): discover a stat class by whole name`
- `fix(bridge): warn when the allowed-origins list cannot be read`

No CHANGELOG line from this task. Known cost to hand the controller (Task 18): a DaisyUI `stat-title`, `stat-value` or `stat-desc` no
longer matches by the word `stat` alone.

## Open questions

1. B01 "did not read": the plan says "a `script[data-allowed-origins]` that the bridge did not read and the origin list is null". I read it
   as: no option, no attribute read, and any `script[data-allowed-origins]` exists (so an unrelated tag could cause a false warning, and
   `*` from an option must not warn). Alternative: warn only if the tag also has a `type="module"` attribute. Recommend the plan's wider rule; it errs toward telling the user.
2. `tests/test_role_detection.py` is named in the plan's Touches but nothing needs it. Recommend leaving it untouched.

## Controller rulings

1. Open question 1: the plan's wider rule, with no type=module requirement.
2. Open question 2: leave tests/test_role_detection.py alone.

## Review fixes (binding: these govern over the text above)

1. In the B01 module test, call `new FontKitBridge()` through `frame.evaluate` BEFORE the `hello`. After a hello the constructor returns the running bridge and adds its own warning, so the flag is never exercised. Assert `__warns` is exactly `[NEW_STRING_4]` after that second construction, and only then send `hello` from EVIL and assert `design:ready`.
2. If the module import is refused, check the `.js` MIME type from `tests/support.py:146` before blaming the bridge.
3. G1-5 fixture: each of the `static`, `status` and `stat` divs sits in its own wrapper. As siblings they cannot give one target, because the sibling pass (3517-3525) registers every sibling. Handoff for Task 18: a real `.stat` still writes ids onto its siblings.
4. B01: one more case in the characterization test loads the module fixture with `FONTKIT_BRIDGE_OPTIONS = {allowedOrigins: 'http://studio.test'}`, and another uses a `*` classic tag; each asserts `__warns == []`. The option case also asserts a hello from `EVIL` times out. Break: a warning decided on the final null result.
5. B14: build the `em`, `code` and `strong` parents directly in `main`, outside any `p`, or the test pins the bug. "The `main` innerHTML is unchanged" means `document.querySelector('main').innerHTML`, taken after the nodes are built, outer `main` only.

---

# Task 5 follow-up: a page with no origin tag stays silent

The worktree `the task's worktree` holds Task 5's finished work, unstaged. Keep it. Read `task-5-code-review.md`, the Important finding only.

**Finding.** No test covers a page with no `script[data-allowed-origins]`. With that condition removed from the `else if` in the B01 change, every new test still passes, and every default page would log the "could not be read" warning.

**Do this.** Extend the existing characterization test in `UnreadOriginListTests` with one case, as a parametrized case or subTest rather than a new test: a page with no `script[data-allowed-origins]` tag, on which the bridge boots, ends with `__warns == []`. Use an existing fixture if one fits; otherwise the smallest change to the fixtures this task already added. Assert first that the page really has no such tag, so the case cannot pass on the wrong page.

Show the break failing: remove that condition, run the case, and show it fails on the mutated code the test loaded, then restore the code.

Touch only `tests/test_bridge_runtime.py` and, if needed, this task's own fixtures. No change to `fontkit-bridge.js`. Do not write a patch: the controller regenerates the row patches from the worktree. Run `test_bridge_runtime` once.

Append to the REPORT what changed, the test count, and the break shown.
