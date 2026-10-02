# Review: v0.2.0 review fixes (state boundary and tooling)

Scope: the uncommitted changes on PR #1 (base a165c4e): `font_kit_studio_v0.1.1.html`,
`fontkit-bridge.js`, `scripts/serve.py`, `scripts/dev/_frontend_gate_assets.py`,
`scripts/dev/check_commit_messages.py`, `tests/support.py`, the test fake, the new
tests and fixtures, the README protocol line and Addendum 6. Records read:
`v02-review-fixes-report.md`, `v02-review-fixes-2-report.md`.

## Gates

| Gate | Result |
|---|---|
| `python3 -m unittest discover -s tests -v` (Chromium only) | 402 tests, OK |
| `python3 scripts/dev/frontend_gate.py --engines chromium --offline` | SUMMARY OK, 15 of 15 runs, 0 FAIL, 1 SKIP (needs the network, as `--offline` says) |
| `python3 scripts/verify.py --static-only` | PASS (IDs, inline JS, provenance) |
| `node --check fontkit-bridge.js` | OK |
| `check_commit_messages.py --range origin/main..HEAD` | OK, 13 commits (the uncommitted work has no message yet) |

Firefox and the phone and wide-touch profiles were not run (Firefox is not
installed here). Nothing below is verified on Firefox.

Mutation checks (scratch copy only):
- Timed-out requests reduced to a single slot: the late-reply test fails
  (`{'hero.lead': 17}` instead of both edits).
- The `finishReapply` ledger comparison disabled: the "target keeps a token"
  test errors.
- The `real_path_servable` call removed from `serve.py`: 5 of 6 symlink tests
  fail; the "still served" test stays green.

## Findings

1. P1, synced CSS dropped `>` selectors: ⚠️ correct for real output, but the
   new grammar introduced a hang (Issue 1).
   - Real bridge output: 45 selectors from the deep, repetitive fixture plus
     injected Tailwind-style and odd-id elements. 40 were accepted, all
     unique, longest 147 characters. `sm:flex`, `w-1/2`, `2xl:p-4`, `!p-4`,
     `é中`, an emoji class and `#odd\:id\.1` all pass.
   - Injection matrix, all rejected: `a{}b`, `a;b`, `/* */`, `</style><script>`,
     trailing backslash, `\{`, `url(`, a newline, `[data-design-id="a}b"]`,
     `a > > b`, leading or trailing `>`, `:hover`, `a b`.
     `[data-design-id="a\"b"]` is accepted.
   - Other places Studio builds CSS: the fallback selector for an id also goes
     through the grammar; declaration and token values use the unchanged
     filter. No second site rejects valid input.
   - But: Issue 1 (hang) and Issue 4 (some real class names rejected).
2. P1, Reapply and `null` tokens: ✅
   - Bridge: `removeToken` restores the root's captured original. Test
     `TokenRemovalTests` checks `--font-sans:  Georgia ;  color: navy` byte for
     byte after override and remove, after a second cycle, and after a global
     reset. The ledger omits the token. A stylesheet-defined token returns to
     its value and leaves no `style` attribute. Unknown names with `null` are
     ignored and not reported. Invalid names still reject the whole update with
     nothing changed.
   - Studio: `reapplyTokenPatch` sends saved tokens plus `null` for
     target-only ones. `finishReapply` compares the ledger with the saved set.
     With the comparison disabled the test fails, so a bridge that ignores
     `null` cannot make Studio report success. A bridge that rejects `null`
     (older bridge: `safeCssString(null)` is undefined) ends in `failReapply`
     through the rejection path. Saved tokens are not replaced by the target's
     (`recordCanonical` only adopts the ledger when the names match).
   - Real Studio against the real bridge:
     `test_import_reconnect_reapply_removes_a_token_the_saved_state_no_longer_has`
     passes, including root `style` attribute back to null.
   - README line and Addendum 6 agree with the code.
3. P2, late acknowledgement after two timeouts: ⚠️ fix correct, test partly unrealistic
   - A `Map` by request id, cleared with the session, applied for any tracked
     id; a late rejection is only forgotten. Other reply paths are fine: the
     iframe-load path drops `inFlight` on purpose (a new document cannot answer
     the old request) and request ids never repeat.
   - See Issue 3 for the test.
4. High, `serve.py` followed links: ✅
   - Both ports and both GET and HEAD are covered (`do_HEAD = do_GET`, and the
     tests loop both). A symlinked overrides file, a link to an outside or
     hidden directory, and a directory `index.html` link all return 404.
     Links that stay inside the repository are still served. PUT writes with
     `os.replace`, which replaces a link rather than following it.
   - The check-then-open gap is real (the handler calls `translate_path` again
     to open). It needs someone who can already write links into the repository
     while the loopback server runs, and the report states it. Acceptable for a
     development tool.
5. Medium, case-insensitive logo scans: ✅
   - `@import`, `url(`, `https?://` and the namespace allow-list compare
     case-insensitively. Tags and `href` were already lower-cased. The gate's
     other scans work on browser-normalised URLs. No other case-sensitive scan
     found.
6. Medium, colour alpha in the paint judge: ✅
   - Own alpha times measured opacity, then composited. Text path is not
     affected and now has a characterisation test.
7. Medium, commit-check word boundary: ⚠️
   - Passes as required: Claude Proctor, Claude Codeyville, Claude Opusville,
     Gemini Haikuson, Gemini Flashman, Claude Sonnenberg, GPT Ultrasound.
     Fails as required: Claude 3.5 Sonnet, Claude Opus 4.1, GPT-4o,
     Gemini 2.5 Pro, Claude Sonnet, Claude Code, Claude-Opus-4, ChatGPT Turbo.
   - New false negative, see Issue 5.
8. Medium, empty or unknown `FKS_ENGINES`: ✅
   - Import fails for `''`, `','`, blank, `bogus`, `chrome`. `Firefox,` and
     `chromium, firefox` normalise. The gate's own parser still falls back to
     both engines on blank input, which is a different tool and is documented.

## Test fake flags

- `keepNullTokens`: models a bridge that accepts and ignores `null`. It cannot
  make a test pass that the real bridge would fail; it only proves Studio does
  not report success. The real bridge removes the token (checked in the real
  Studio against real bridge test).
- `ignoreBaseRevision`: this does hide real behaviour (Issue 3).

## Issues

### Critical

None.

### Important

1. A hostile target can freeze Studio through the new selector grammar.
   `font_kit_studio_v0.1.1.html:3062` (`SELECTOR_IDENT`). The alternative
   `\\[0-9a-f]{1,6} ?` and the plain `[\w...]` alternative both match hex
   digits, so a run of escapes such as `\aaaaaa\aaaaaa...` can be split in six
   ways each, and a non-matching tail makes the match exponential. Measured with
   the shipped regex in Node: 72 characters, 1.5 s; 79 characters, 8.9 s; each
   extra escape multiplies the time by about six. Reached in Studio: a target
   manifest reporting `'.' + '\\aaaaaa'.repeat(11) + '{'` as a selector, then one
   edit, froze the page for 52 s (the test harness timed out at 5 s). The
   selector goes to the grammar in `liveCss` (`:4596` and `:4598`, twice per
   rule per render) after only a 500 character cap, so a 500 character selector
   never returns. The old filter was linear. This is a hostile payload at a
   trust boundary (Rules 1 and 5; anti-pattern 1 family).
   Suggested fix, checked in Node: make the hex escape unambiguous with
   `\\[0-9a-f]{1,6}(?![0-9a-f]) ?|\\[0-9a-f]{6}(?=[0-9a-f])`. With it the
   70-escape hostile string, a 492-character valid one and a 505-character
   invalid one all finish in under 3 ms, and `.\31 0`, `.a\31  > b` and
   `.\aaaaaaa` still pass. Add a test that sends a long escape run and asserts
   the page stays responsive and the rule is skipped.

### Minor

2. `docs/plans/...live-preview-code-sync.md` Addendum 6 checkboxes are still
   unchecked and `docs/implementation/progress.md` has no event for this work
   (AGENTS commit rule 1). Controller job before commit.
3. The late-reply test does not match the real bridge.
   `tests/test_studio_live.py` (`test_every_timed_out_request_stays_tracked...`)
   sets `ignoreBaseRevision`, so both late acknowledgements apply and both
   edits are saved. The real bridge checks the base revision: the second
   request was based on revision 0 and is answered `revision-conflict` after
   the first lands. Without the flag I measured saved overrides of
   `{'hero.title': 61}` only, badge `Live · rev 1`, no page errors. The fix is
   still needed and still tested (mutation fails), but the test claims an end
   state the real bridge never reaches. Add a variant without the flag that
   asserts the first edit is saved and the second is not, and not lost
   silently from the wording the user sees. The test also waits a fixed
   `wait_for_timeout(9000)` for the second timeout (AGENTS test rules prefer an
   awaited condition; the second timeout has no separate observable today).
4. Some real class names still lose their rule. Verified with real bridge
   output: classes containing an escaped `>`, `;`, `{`, `}`, `<` or `\`
   produce unique, valid selectors that the grammar rejects, for example
   `main:nth-of-type(1) > p.x.\[\&\>\*\]\:p-4:nth-of-type(6)` (a Tailwind
   arbitrary variant). The edit is skipped with the "no safe selector"
   comment, which is the same loss as the original finding, only rarer. Either
   accept the escaped forms inside identifiers (they are inert inside a CSS
   file) or record the limit in the README next to the stable-id advice.
5. The word boundary created a new false negative: `Claude Opus4.1`,
   `Claude Sonnet4` (a digit glued to the model word) now pass, and used to be
   caught. `scripts/dev/check_commit_messages.py:69`. Use `(?![a-z])` instead
   of `\b`; Proctor, Codeyville and the other human names still pass.
   (`GPT4` with no separator was never caught.)

**Task quality:** Changes required

## Re-review (scoped, after the fixes to Issues 1, 3, 4 and 5)

### Gates

| Gate | Result |
|---|---|
| `python3 -m unittest discover -s tests -v` (Chromium only) | 406 tests, OK |
| `frontend_gate.py --engines chromium --offline` | SUMMARY OK, 15 of 15 runs, 0 FAIL, 1 SKIP (network check) |
| `verify.py --static-only` | PASS |
| `node --check fontkit-bridge.js` | OK |
| `check_commit_messages.py --range origin/main..HEAD` | OK, 13 commits |

Firefox and the phone and touch profiles were not run (Firefox is not installed here).

### Issue 1, selector check can no longer stall Studio: resolved

- The shipped identifier now has disjoint alternatives: a plain character, a
  backslash plus six hex digits, a backslash plus one to five hex digits not
  followed by another hex digit (each with one optional space), or a backslash
  plus a non-hex character. No text can match in two ways.
- Timing, with the regexes read from the page source and run in Node. Shapes
  tried at 500, 5,000 and 50,000 characters: runs of `\aaaaaa`, `\aaaaa`, `\a`,
  `\a ` (backslash, hex, space), `a\aa b\31 0` (plain and escape mixed),
  `\ ` and `\  ` (backslash and space), plain hex-letter runs, 500-character
  near-misses ending in `{`, `;` or `<`, a long chain of ` > ` steps each ending
  in a hex escape, repeated `:nth-of-type(1)`, attribute values full of `\"` and
  `\\`, repeated `.a` and `#a.b`, and Unicode with escapes. The slowest single
  run was 2.4 ms and time grows linearly (49,996 characters: about 1.5 ms).
  40,000 random strings of 100 to 500 characters (a hostile alphabet, and
  structured fragments with a hostile tail) peaked at 0.06 ms.
- In the page: the 11-escape selector that froze Studio for 52 s is now skipped
  within 0.1 s, as is a 492-character run of `\aaaaaa`. The rule is replaced by
  the "no safe selector" comment and the edit size is not written.
- Real bridge output on the deep, repetitive fixture, plus injected utility
  classes and an odd id: 45 selectors, 0 rejected, all unique, longest 147
  characters.
- Test strength: `test_the_selector_check_itself_is_fast_on_500_character_inputs`
  reads the shipped regexes from the page source, so it tests the real code.
  With the old ambiguous identifier restored in a scratch copy, the pair of new
  tests did not fail cleanly: the page froze and the run had to be killed after
  300 s. That is a detection (CI would stop at the harness timeout), not a clean
  red. Minor, no action needed.

### Issue 4, escaped specials accepted, unescaped still refused: resolved

- Accepted now: `.x\;y`, `.x\{y\}`, `.x\<y\>`, `.a\\b`, `.\[\&\>\*\]\:p-4`,
  `.\!p-4`, `.\32xl\:p-4`, `.\aaaaaaa`, `.\31 0`, `#odd\:id\.1`, accented and
  emoji classes, `[data-design-id="a\"b"] > p:nth-of-type(1)`.
- Still refused: `.x;y`, `.x{y}`, `.x<y`, `.a>b`, `a{}b`, `</style><script>`, a
  trailing backslash, a backslash before a line break, `/* */`, `url(`,
  `a > > b`, leading or trailing `>`, `:hover`, `a b`, `[data-design-id="a;b"]`,
  `[data-design-id="a\x"]`.
- `\/\*` (escaped slash and star) is accepted. It is inert in a CSS file and
  does not form a comment marker, so this is correct.
- The real-bridge test with a `[&>*]:p-4` and an `a;b{c}` class keeps the edit
  in the CSS tab and the synced file, and the persisted selector matches exactly
  the edited heading.

### Issue 3, late conflict: resolved

- A late rejection now shows `Rejected: <reason>` and re-reads the inspector
  from the page (moves go through the move-rejection notice). Nothing is
  retried, which is right: the user moved on while the target was silent.
- `test_a_late_revision_conflict_is_shown_and_the_first_edit_is_kept` uses the
  fake with real revision rules. It asserts the badge, saved state `{title: 61}`
  only, CSS without `17px`, the page's real value (16 px) in the inspector, and
  that entering the value again works at revision 2 and reaches the synced PUT
  body. This matches what I measured against the same scenario earlier.
- The fixed 9 s sleep is gone. The shared helper waits for the first timeout
  badge and for both held replies, stamps the badge with a marker text, and
  waits for the second timeout to restore "No response from target". Another
  status change could only make the wait time out, never pass early.
- The older end-to-end test with `ignoreBaseRevision` stays and is described as
  a target that applies queued requests in order. That is now an honest
  description. It still takes about 16 s because it waits for two real 8 s
  timeouts.

### Issue 5, commit check: resolved

- `Claude Opus4.1`, `Claude Sonnet4`, `Claude Haiku3` and `Claude Opus_4` now
  fail. Also failing: Claude 3.5 Sonnet, Claude Opus 4.1, GPT-4o, Gemini 2.5 Pro,
  Claude Sonnet, Claude Code, Claude-Opus-4, ChatGPT Turbo, Gemini Flash.
- Passing: Claude Proctor, Claude Codeyville, Claude Codey, Claude Opusville,
  Gemini Haikuson, Gemini Flashman, Claude Turbotsky, GPT Ultrasound,
  Claude Sonnenberg, Claude Prokopiou, Claude Procter-Smith.
- No false positives and no false negatives in my matrix. (`GPT4` with no
  separator remains uncaught, as before.)

### Remaining items

- Minor 2 (Addendum 6 checkboxes and the ledger event) is the controller's job
  before the commit and is still open.
- Nothing new found.

**Task quality:** Approved
