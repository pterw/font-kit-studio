# Task 15 brief: stop the bridge reporting token names no app reads

Plan task 15, wave 2, mode code, BASE 5443ff6, worktree `the task's worktree`. Audit rows: G1-3 residue (record homes G1-3 to
`later`; the plan keeps this residue strip in 0.4.1). Line budget: about 45 gross lines (code 3, one fixture about 17,
one test about 25). One audit row, so one patch.

## Why

Font Kit Studio was first written inside another project. `LEGACY_TOKEN_KEYS` in `fontkit-bridge.js:124-128` still
lists that project's names: `--editorial-size`, `--mono-spacing`, `--accent-cyan`, `--accent-emerald`,
`--accent-purple`. `getCurrentTokens` (`fontkit-bridge.js:3863`, `const names = new Set(LEGACY_TOKEN_KEYS)` at 3865)
seeds its name set from that list, so a page that sets one of those names anywhere the other readers miss (for example
under `html[data-theme='x']`) has it reported in the handshake `tokens.css`. No app reads these names. At BASE a search
finds the five only in the bridge: no test, fixture or doc. The plan's cause holds at BASE; lines match the plan.

Kept on purpose, to be named in the commit body: `--brand-canvas` (Studio's CSS export writes it, at the plan's cited
`fontkit-studio.html:3212`; the export format does not change), `#main-content-flow` (`fontkit-bridge.js:4120`; README
documents it) and `resolveElementForSlot` (fixtures and the Sync path use it). They wait for the slot-placement plan.

## Owned files (exact)

- `fontkit-bridge.js`: lines 124-128 only (the `LEGACY_TOKEN_KEYS` array). No other region.
- `tests/test_bridge_runtime.py`: one new class inserted directly after `HandshakeTests` (ends at BASE line 340, before
  `class InitOptionTests` at 342), plus one new constant `LEGACY_TOKENS_PAGE` next to `ROOT_STYLE_PAGE` (BASE line 30).
- `tests/fixtures/bridge/target-legacy-tokens.html`: new file.
- `CHANGELOG.md`: none (not user visible). Everything else is read-only.

## Read first

- `fontkit-bridge.js` 120-129 and 3863-3893 (`getCurrentTokens`, including `isRootSelector`, which accepts only a bare
  `:root` or `html` selector, so `html[data-theme='x']` is skipped).
- `tests/test_bridge_runtime.py` 20-146 (`BridgeCase` harness: `open`, `hello`) and 260-340 (`HandshakeTests`, the
  `ready['tokens']['css']` shape).
- `tests/fixtures/bridge/target-root-style.html` (fixture model).

## Requirements

1. Remove `--editorial-size`, `--mono-spacing`, `--accent-cyan`, `--accent-emerald` and `--accent-purple` from
   `LEGACY_TOKEN_KEYS`. Leave `--font-sans`, `--font-serif`, `--font-mono`, `--font-display` and `--brand-canvas` in
   place, in their order. Oracle: the array literal after the edit, and requirement 2.
2. Behaviour, observed in the handshake. Given the new fixture, `design:ready` `tokens.css` has `--font-display` and
   `--accent-emerald` (declared in `:root`, found by the stylesheet reader) and has no `--accent-cyan` (declared only
   under `html[data-theme='x']`). Oracle: literal values in the fixture (`Georgia, serif`, `#00aa66`) and
   `assertNotIn`. A user sees only the page's own tokens in Studio, not names from another app.
3. Do not touch any other file or region of the bridge. No change to the protocol version (1) or export format.

## Fixture

`target-legacy-tokens.html`: `<html lang="en" data-theme="x">`; a `<style>` with `:root { --accent-emerald: #00aa66; }`
and `html[data-theme='x'] { --accent-cyan: #00cccc; --font-display: Georgia, serif; }`; one element
`<h1 data-design-id="legacy.title">Title</h1>`; `<script src="/fontkit-bridge.js"></script>`. Add an HTML comment
saying what the fixture is for, as `target-root-style.html` does.

## Tests

One new class `LegacyTokenNameTests(BridgeCase)` with one test per engine loop (follow `HandshakeTests`):

- `test_names_set_only_where_the_root_reader_misses_them_are_not_reported`. Docstring: Given a page that sets
  `--accent-cyan` and `--font-display` only under `html[data-theme='x']` and `--accent-emerald` in `:root`, When the
  bridge answers hello, Then `--font-display` and `--accent-emerald` are reported with their values and `--accent-cyan`
  is absent.
- RED (new behaviour): the `assertNotIn('--accent-cyan', ...)` fails at BASE, because the legacy list adds the name and
  its computed value is non-empty (`html[data-theme='x']` matches the element). Show that failure first.
- GREEN characterization: the `--accent-emerald` and `--font-display` assertions pass at BASE already. `--font-display`
  is in the kept list and `--accent-emerald` is found by the stylesheet reader. Do not manufacture RED for them.
- Realistic break: re-adding `'--accent-cyan'` to the array must fail the test; run that once and record it, then
  restore.

## Focused command

From `the task's worktree`, with a timeout of 300000 ms, one module only, no shards, no dev server:

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime test_support -v`

The landing also runs `test_studio_roles`, `test_role_routes` and `test_r2_integration`; the gate run does that, not
you (code phase runs only the files you change or that import the changed module).

## Patches

One audit row, so one patch: `task-15-code.patch`. Commit subject (59 characters):
`refactor(bridge): stop reporting token names no app reads`. The body names the three kept items above and says the
removed names had no consumer. No CHANGELOG line (no user-visible change). No process state, no attribution trailer
beyond what the dispatch gives.

## Open questions

None.

## Review fixes (binding: these govern over the text above)

1. The test covers all the removed names, parametrized, not only `--accent-cyan`, so re-adding any one fails it.
2. `--brand-canvas` is at `fontkit-studio.html:3216` at BASE, not 3212.
