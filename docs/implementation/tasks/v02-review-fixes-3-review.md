# Review: v0.2.0 review fixes, round 3 (duplicate bridges, stable-id selectors)

Scope: every uncommitted change on b0c2204: `fontkit-bridge.js`,
`font_kit_studio_v0.1.1.html`, the bridge, Studio and integration tests, the
README lines (about 384 and 416) and the plan edits (line 90 and the new
Addendum 7 item). Record read: `v02-review-fixes-3-report.md`.

## Gates

| Gate | Result |
|---|---|
| `tests.test_bridge_runtime`, `tests.test_studio_live`, `tests.test_live_integration` (Chromium only, `PYTHONPATH=tests`) | 197 tests, OK |
| `python scripts/verify.py --static-only` | PASS |
| `node --check fontkit-bridge.js` | OK |

Firefox was not run. No process was left running.

## A. A second `new FontKitBridge(...)` returns the existing bridge

Verdict: the duplicate-bridge defect is fixed. One trust gap needs a decision
(Important 1).

Probed against the real bridge:
- Constructor returning another object, with a subclass: `class X extends
  FontKitBridge` gets the running instance from `super()`. `new X()` returns
  that instance (`instanceof X` is false) and any code in the subclass after
  `super()` runs against the live bridge. I set a marker and changed
  `options.autoDiscover` on the running bridge from a subclass. See Minor 3.
- Disposed bridge then a new one: the new one is created, becomes the global
  instance, and takes its options (`allowedOrigins` applied). Correct.
- Auto instance that connected, then the Studio went away: `everConnected`
  stays true, so a later `new FontKitBridge({allowedOrigins: [...]})` returns
  the old auto bridge and its options are ignored (Important 1).
- `initFontKitBridge` and `new`, both orders, no Studio yet: init first returns
  the auto bridge; a constructed bridge then replaces it and a later
  `initFontKitBridge()` returns the constructed one. Correct and unchanged.
- Two constructed bridges before any Studio connects: the second call is
  ignored (Minor 4).
- Pop-out window against the iframe: each window loads its own script and has
  its own global slot, so they are independent. Nothing shared, nothing to
  probe beyond reading.
- README claims: `window.FONTKIT_BRIDGE_OPTIONS` (read in `autoInit`),
  `data-allowed-origins` (read in `resolveAllowedOrigins`) and
  `data-auto-init="false"` (checked before auto-init) all exist in the code.
  The README wording matches the behaviour.

### Important

1. **A security option can be dropped after connect with only a console
   warning.** `fontkit-bridge.js:384-391`. Verified: after the auto bridge
   connected, `new FontKitBridge({allowedOrigins: ['https://only.test']})`
   returned the same instance and its `allowedOrigins` stayed `null`, which
   means "any origin that framed or opened the page is accepted"
   (`resolveAllowedOrigins`, `originAllowed`). An app that re-runs its setup
   (HMR, or a deliberately tightened configuration) believes it restricted
   Studios and did not. Narrowing is the safe direction, and Rule 5 puts safety
   above simplicity, so a warning alone is not enough for this option.
   Suggested: when the second call passes `allowedOrigins`, apply it only if it
   narrows the running list (never widen), and drop a pinned session whose
   origin is no longer allowed; keep ignoring every other option. Throwing is
   worse than either, because it breaks hot reload. At the least, make the
   warning name `allowedOrigins` and say it was not applied when it differs.
   The current bridge test asserts `origins` stays `None`, so it pins the
   unsafe case; add a narrowing case.

### Minor

2. The new tests wait a fixed 300 ms in three places (the bridge test, and the
   integration test before `__seen.ready`). These are absence checks (no second
   announcement, no second reply), which the test rules allow, and they sit
   behind positive waits. No action needed.
3. Subclasses of `FontKitBridge` silently mutate the live bridge, as above.
   Record it in the constructor comment or README note ("a subclass gets the
   running instance").
4. Two constructed bridges before any Studio connects: the second call is
   ignored, so an updated option set from a hot reload is lost until the page
   reloads. Replacing an unconnected constructed bridge, as is done for an
   unconnected auto one, would be the consistent rule. Optional.

## B. Stable ids with CSS-special characters

Verdict: correct and safe in everything I probed.

- Linear time: the shipped selector grammar (read from the page source) on
  adversarial text at 2,000, 20,000 and 200,000 characters: runs of `\`, `\\`,
  `\aaaaaa`, `\3b ` (with and without the second space), `\a`, mixed escape and
  quote runs, plain hex-letter runs, long near-misses ending in `{`, `;` or an
  open quote, and chains of attribute steps. The slowest was 4 ms; 30,000
  random strings of 50 to 1,950 characters peaked at 0.12 ms. The space after
  a hex escape is either consumed or not followed by a space, so each text
  matches one way.
- Correctness matrix (19 cases) all as intended: hex escapes and escaped
  quotes and backslashes accepted; raw `; { } < >`, a trailing backslash, an
  unknown escape, a line break in the value, `/*`, `url(`, a trailing rule or
  extra step all refused.
- Same element only: 29 ids against the real bridge (hex-lookalike text such
  as `\3b`, `\\3b`, `a\3b b`, `a;1`; quotes and backslashes; `url(x)!important`;
  `a/*b*/c`; `</style><script>`; a tab, CR LF, DEL and U+2028; an emoji and
  accented text; a 300 character id of mostly `;`). For each, the reported
  selector had length at most 1,204, passed the Studio grammar, matched exactly
  one element with `querySelectorAll`, and the same selector in a real
  stylesheet applied to that element and no other (27 elements carried the
  outline, one per id with a selector). Escapes parse the same in both paths
  because the bridge always ends a hex escape with the one consumed space.
- Non-BMP characters are left raw (both surrogates pass the character class)
  and matched. A lone surrogate cannot survive Playwright's argument
  encoding, so I could not test it; it is not an escape issue.
- Hostile names in comments: 23 hostile strings through `commentText` (`*/`,
  `/*`, `/*/`, `**/`, `//*`, `*` and `/` split by CR, LF, form feed or U+2028,
  `</style><script>`, `<!--`, `-->`, a bidi override) never ended or reopened
  the comment, never held a line break, `<` or `>`. Other comment sources
  (header URL, per-rule name and id) all go through it.
- 2,000 character limit: the length check runs before the grammar, so the work
  is bounded and linear; a bigger selector is skipped with the comment. A 300
  character id needs at most about 1,500 characters. A hostile target can only
  make its own rule longer (about 2 KB per target) and the file is written
  only by the user's Sync, so there is no new harm.
- Sibling sites: the CSS tab, Copy, Download, Sync and the fallback for an id
  Studio only knows from saved state all go through the same builder. The
  legacy slug lookup in the bridge (`[data-design-id*="${slugId}"]`) is built
  from a `[a-z0-9]`-only string and needs no change.

### Minor

5. An id containing U+0000 gets selector `\0 `, which CSS turns into U+FFFD, so
   the persisted rule matches nothing (verified: zero matches) and could match
   an element whose id holds U+FFFD at that place. HTML itself never produces a
   NUL in an attribute, only script does. Negligible; record it if the report
   lists limits.

## Test quality

- No vacuous tests: the bridge test checks the returned object, the warning,
  one `bridge-ready`, one `design:ready`, one `design:applied`, and a byte-exact
  reset; the integration test runs the real Studio against the real bridge. The
  selector tests check the rule in the CSS tab, the synced file, exact-element
  matching and the absence of raw characters. The grammar test runs the shipped
  regexes with a 50 ms bound.
- Missing: the narrowing case for `allowedOrigins` (Important 1), a disposed
  bridge followed by a new one, and a subclass. Cheap to add.

## The intermittent re-selection effect

I did not see it in 197 tests, so nothing to attribute. By reading, there is a
plausible cause for Addendum 7. After a reset, restore or move, Studio sends
`design:select` for `live.selectedId` from `afterApplied`
(`font_kit_studio_v0.1.1.html` lines 3618 and 3624), and `fetchFullArrangement`
does the same. `live.selectedId` only changes when the bridge's
`design:selected` reply arrives. If the user clicks another target after the
edit was sent but before that reply, `live.selectedId` is still the old target
when the acknowledgement arrives, so Studio asks the bridge to select the old
target again and it ends up selected. That fits "typed value lands on the
previous target". It is a hypothesis, not reproduced. The fix would remember the
user's latest requested selection and skip the re-select when it differs.

## Verdict

The selector work (B) is approved as is. The constructor work (A) fixes the
duplicate bridge, but silently ignoring a stricter `allowedOrigins` is a Rule 5
gap with a small fix.

**Task quality:** Approved with fixes

## Round 2 (scoped re-review of the repeated-construction fixes)

Gates (Chromium only, `PYTHONPATH=tests`): `tests.test_bridge_runtime` and
`tests.test_live_integration` 121 tests, OK; `verify.py --static-only` PASS (5
checks); `node --check fontkit-bridge.js` OK. No process left running.

### Important 1, resolved

- **Never widens.** Narrowing applies only when the request is a string or a
  list, is not `*`, and every requested origin is already allowed (an open
  bridge allows everything). Probed on a connected bridge: `*`, `[null]`,
  `'null'`, a list holding `null` plus an allowed origin, a larger list, a
  disjoint list and, after narrowing to `[]`, a request for the previous origin
  were all ignored, and the policy did not change.
- **Normalisation.** A trailing slash (`http://studio.test/`, `//`) is
  stripped, so it narrows correctly; duplicates collapse (`changed` is false
  when only duplicates differ). Comparison is case-sensitive, so an upper-case
  subset of a list is ignored (safe). See Minor 6 for the other direction.
- **Inert after the drop.** On a connected bridge with a pinned Studio at
  `studio.test`, narrowing to `other.test`: the session id is null, the page's
  link (a CTA anchor) works again (it was intercepted while connected), no
  overlay nodes exist, the inline edit stays on the page, and the ledger and
  change order still list the edited target. With the policy lifted from inside
  the page (a test-only step, since no API can widen), a new hello was
  accepted, the ledger showed the edit, and Reset restored the author's inline
  style byte for byte and the original text. So the originals survive the drop.

### Replacement rule, confirmed not a trust boundary

A bridge that no Studio has talked to is now replaceable, so a later
`new FontKitBridge()` without `allowedOrigins` swaps a restricted, unconnected
bridge for an open one. I agree with the controller's view. The origin check
protects the page from other windows (a framing or opening Studio); a script in
the page already has full page privilege and can set
`window.__fontkitBridge.allowedOrigins = null` directly, which I used in the
probe above. No party that can call the constructor is outside the page. The
deferred auto-init cannot do this either: `autoInit` returns when a bridge
exists, and `initFontKitBridge` returns the existing bridge, so only an
explicit `new` replaces.

Disposed bridges leave nothing behind: with `addEventListener` and
`removeEventListener` instrumented, two successive replacements kept the
count at the 8 listeners of the live bridge; both older bridges ended with 0
listeners, and no overlay node remained. The only other timers (discovery,
opener poll, animation frames) are cleared in `dispose`. A disposed bridge is
replaced with no "already exists" warning and answers one hello and one edit.

### Test quality

RED evidence in the report is plausible: before the change the policy stayed
`None`, and the tests assert the real `allowedOrigins`, the session id, absence
of replies and the page value, not just the warning. No new fixed sleeps; the
absence checks use the helper's 3 s wait, which is the allowed exception. The
subclass test records the documented behaviour (the subclass constructor runs
on the live bridge).

### Minor

6. Origins are compared case-sensitively and only trailing slashes are removed.
   Narrowing an open bridge to `['HTTP://STUDIO.TEST']` is applied, and then no
   real origin (always lower-case) matches, so the pinned Studio is dropped and
   nothing can connect until reload. This fails closed and the warning shows
   the list, and it predates the change (a constructor-time list behaves the
   same). Lower-casing in `parseOriginList` would fix both.
7. `narrowAllowedOrigins([])` applies and locks every Studio out until the page
   reloads, because nothing can widen again. That is the safe direction and the
   warning says "no origin"; if an HMR run builds an empty list by mistake the
   developer must reload. Optional: treat an empty list like a non-list.
8. `initFontKitBridge({ allowedOrigins })` after a bridge exists still ignores
   the option with a warning (the README steers to `data-auto-init="false"`),
   so it does not get the narrowing that `new` now gets. It predates this work
   and is documented, but the two entry points now differ. Optional: route it
   through the same narrowing.

**Task quality:** Approved
