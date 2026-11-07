# Task 11 brief: warn when Sync wrote a token and no element changed

Plan Task 11, wave 3, mode code. BASE `5443ff6`, worktree `the task's worktree`. PATCH_DEP task-10-code.patch (apply it first; it
supplies `postWarning`). Audit rows B08, D2-4, G1-4, G2-10 (one row group, one commit). Budget: about 95 gross lines
(about 30 source, 65 tests plus one small fixture page).
Recorded: D079 (the kinds) and New string 1 (approved, O31).

## Why

Studio's Sync sends `--font-display`, `--font-sans`, `--font-serif`, `--font-mono` (`fontkit-studio.html:6836-6857`). The
bridge writes them in `handleCompositionUpdate` (`fontkit-bridge.js:2361-2380`, `setToken` at `:2981-2987`) and acknowledges
them (`:2393`), so Changes lists them. A page that reads other names (the Next app reads `--font-terminal` and
`--font-pixel`) changes nothing, yet the user is told "applied" (audit row B08). The plan's cause holds at BASE: nothing in
`handleCompositionUpdate` compares the page before and after the token write. The role restyle (`applySlotUpdate`, `:4252`,
inline with `!important`) runs at `:2391`, after the token writes at `:2361-2380`; a measurement taken after it would
never fire where a slot matches an element.

## Owned files (exact)

- `fontkit-bridge.js`: `handleCompositionUpdate` from the `// 1. Global CSS tokens` comment (`:2361`) to the
  `// 2. Live Movement` comment (`:2382`) for the measuring, plus the one `postWarning` call before the `acknowledge` at
  `:2393`; and one new small method directly after `removeToken` (`:2991-2997`, confirm the end at BASE), no other line.
  `setToken` itself stays unchanged. Task 10 owns `postWarning` (after `noteRuntimeError`); do not touch it.
- `tests/fixtures/bridge/target-terminal.html`: new file, minimal (below).
- `tests/test_bridge_runtime.py`: a new class directly after `LegacyCompositionTests` (`:1109-1195`), before
  `TokenRemovalTests` (`:1197`), subclassing `BridgeCase`.

Everything else is read-only. Other tasks edit other regions of the same two files in parallel worktrees.

## Read first

`fontkit-bridge.js:2329-2393, 2975-3000, 4252-4262`; Task 10's patch (`postWarning` and its argument rule, frozen);
`tests/test_bridge_runtime.py:51-146, 1109-1145, 2462-2490`; `tests/fixtures/bridge/target.html:12-17, 29, 45`.

## Requirements

1. **Measure the token write only.** In `handleCompositionUpdate`, before the first token write, record every element's
   computed `font-family` in one pass over `document.querySelectorAll('*')`; after the last token write (the `patch.tokens`
   loop and the four direct shortcuts) and before step 2 (`applyWireframeMovement`, `:2382`) record it again. Nothing from
   step 2 or 3 (movement, slot restyle) may enter the comparison. Oracle: test 2 below, where a slot restyles an element
   after the tokens.
2. **Warn when nothing moved.** If at least one token written in this call has a name starting `--font-`, and no element's
   computed `font-family` differs between the two passes, call
   `this.postWarning('token-not-applied', 'global', message, data.requestId)` once. If any element differs, post nothing.
   `message` is New string 1 verbatim, `Sync wrote {names}, but no element on the page changed. This page may read other
   token names.`, with `{names}` the written `--font-` names in the order written, joined by `, `. A written name is one
   `setToken` returned a value for. Post it before `acknowledge`, so the warning precedes the `design:applied` reply on the
   wire. Observed: the page's `postMessage` log holds one `design:warning` with `kind: 'token-not-applied'`.
3. **Only tokens that changed count.** A token whose canonical value equals the override the bridge already holds is not
   a written name for this rule (read `this.tokenOverrides.get(name)` before `setToken`). A Sync that writes no such token
   does not warn and need not measure. Oracle: a literal second Sync with identical values (test 3). See Open question 1.
4. **No warning on a page that reads a token.** On `target.html` (its `h1` reads `--font-display`, `:16`) a Sync of the four
   fixed names with a value that differs from the page's own posts nothing. Oracle: the h1's computed `font-family`, read
   by the test before and after the Sync, differs.
5. **Unchanged:** every reply, `canonicalPatch`, the ledger, the revision, and the order of the writes. The measuring
   reads computed style only and writes nothing to the page.

## Fixture (new file)

`tests/fixtures/bridge/target-terminal.html`, copied in shape from `target.html` but at most 20 lines: the bridge script
tag exactly as `target.html:45`, `:root { --font-terminal: monospace; }`, `body, h1 { font-family: var(--font-terminal); }`,
and one `<h1 data-design-id="landing.hero.title" data-design-role="display">Make type sing</h1>`. It reads no
`--font-display`, `--font-sans`, `--font-serif` or `--font-mono`. Add `TERMINAL_PAGE` next to the page constants only if
the implementer's new class needs one at module level; otherwise define it in the class (the constants block is not owned).

## Tests

New class `TokenNotAppliedTests(BridgeCase)`, using the page's `postMessage` log (`self.messages`) and
`self.computed(frame, TITLE, 'fontFamily')`. A sync helper in the class sends
`{'type': 'design:update', 'patch': {'tokens': FOUR}}` with `FOUR` the four fixed names set to `Courier New, monospace`,
`Georgia, serif`, `Arial, sans-serif` and `Verdana, sans-serif` (literals).

- `test_a_sync_to_a_page_that_reads_other_names_warns_and_names_the_tokens`: Given the terminal page, When the four names are
  synced, Then the h1's computed family is unchanged (read before and after), the reply is `design:applied`, and exactly
  one `design:warning` has `kind` `token-not-applied`, `targetId` `global`, the reply's `requestId`, `sessionId` `s1`, and
  `message` equal to the literal New string 1 with `--font-display, --font-sans, --font-serif, --font-mono` substituted.
  RED: no warning is sent. Break: never posting.
- `test_a_role_slot_that_restyles_an_element_does_not_hide_the_warning`: Given the terminal page, When the same Sync
  carries a text slot `{'id': 's', 'targetId': TITLE, 'type': 'text', 'fontFamily': 'Courier New, monospace', 'size': 30}`,
  Then the h1's computed family becomes the Courier stack (proving a restyle happened) and the one warning is still
  posted. RED: no warning. Break: taking the second pass after the slot loop (`:2391`).
- `test_a_sync_to_a_page_that_reads_a_synced_name_posts_no_warning`: Given `target.html`, When the four names are synced
  (display differs from its `Georgia, serif`), Then the h1's computed family differs after, and no `design:warning`
  appears. GREEN characterization (nothing warns at BASE). Break: warning whenever tokens are written.
- `test_syncing_the_same_values_again_does_not_warn_a_second_time`: Given the terminal page after the first Sync warned,
  When the identical Sync is sent again, Then the log holds one `token-not-applied` warning in total. RED: the second
  Sync would warn too if requirement 3 were missing (here nothing warns at BASE, so RED only against a naive
  implementation; say so in the report). Break: dropping the changed-value filter.

## Focused command

From `the task's worktree`, with a timeout of 600 s, one module, no shard, no dev server:

```
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime.TokenNotAppliedTests test_bridge_runtime.LegacyCompositionTests test_bridge_runtime.TokenRemovalTests test_support -v
```

Landing also runs `test_studio_roles`, `test_role_routes`, `test_r2_integration` (controller).

## Patches

One row group, so one patch: `task-11-code.patch`. Commit subject (56 chars), the plan's text:
`fix(bridge): warn when a synced token changes no element`.
CHANGELOG line for the Handoff (the file is read-only here; the controller adds it under Unreleased, Fixed):
`- Sync to Live App now tells you when it wrote font tokens and no element on the page changed, which happens when the page reads other token names.`

## Open questions

1. **Repeat Sync and unchanged values.** Comparing before and after cannot tell "page ignores the token" from "token
   already held this value", so a second identical Sync would warn on a page that does read the token. Requirement 3 skips
   unchanged values. Cost: a page that ignores the token warns once, not on every Sync. Recommendation: as written.
2. **Which tokens count.** Requirement 2 counts only `--font-` names, since the comparison is computed `font-family`; a
   Sync of `--editorial-size` alone cannot move it and must not warn. The plan says "tokens", unqualified. Recommendation: as written.
3. **Cost on large pages.** Two passes over every element, each one style recalculation. Recommendation: no cap
   (linear, once per Sync); say so if a cap is wanted.

## Controller rulings

1. Open question 1: yes, skip values the bridge already holds, so a page that ignores a token warns once.
2. Open question 2: yes, only --font- names count.
3. Open question 3: as written, unless the brief review shows a real cost on a large page.

## Review fixes (binding: these govern over the text above)

1. Supersedes ruling 2: the check counts only the four names Studio sends (`--font-display`, `--font-sans`, `--font-serif`, `--font-mono`), not any `--font-` prefix, because `--font-size-*` and `--font-weight-*` do not move `font-family` and would warn falsely. Each name counts once, even if `patch.tokens` and the direct shortcut both send it.
2. Add one test on the terminal page with three Syncs: tokens `{'--editorial-size': '20px'}`, a slots-only patch, and `{'sans': 'Verdana, sans-serif'}`. The first two warn zero times; the third warns once and names `--font-sans`. Breaks: drop the name filter; drop the "at least one written" guard.
3. Replace test 4's "one total" with a third Sync where exactly one of the four values changes: it warns again and names only that token.
4. Corrected citations at BASE: the Studio sender is `fontkit-studio.html:6841-6861`, and `removeToken` ends at 2996. Name the new method for what it does: a helper returning the computed `font-family` values as an array.
5. Your insertion point is two unchanged lines from Task 4's 3000-3045 region: say so in the report's Handoff. Measured cost is 15-25 ms per Sync on 5,000 elements, so ruling 3 stands.
6. Accepted limit, stated in the report: a token used only in pseudo-elements, shadow roots or script, or a first write equal to the page's own value, may warn; New string 1's wording allows for that.
