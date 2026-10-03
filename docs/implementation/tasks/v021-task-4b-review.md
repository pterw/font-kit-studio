# v0.2.1 Task 4b review: sans and mono tokens by tag

Reviewer: Leading. Brief and implementer report: `v021-task-4b-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 4 (decision 5) extended.
Scope: the token-fallback loop in `compositionPatch` and the `TokenFallbackTests` class in
`tests/test_studio_stage.py`, reviewed in the implementer's worktree at adca6b4 plus the change.

## Verdict

**Approved**

Reviewed in the implementer's worktree at adca6b4 plus the change (read-only; mutations ran on a scratch
copy that is deleted). Engines: chromium only (FKS_ENGINES=chromium); Firefox not run.

### Gates

- `python scripts/verify.py --static-only`: PASS (91 unique IDs, inline JS syntax, provenance).
- `python -m unittest tests.test_studio_stage`: 11 tests, OK (chromium).
- `python -m unittest tests.test_studio_live -k CompositionFont -k FreeFont`: 25 tests, OK (chromium).
- Not run by me: the full suite, `frontend_gate.py`, `node --check` (bridge untouched).

### 1. Decision 5 applied to all three tokens

`font_kit_studio_v0.1.1.html` `compositionPatch` (the loop right after the `--font-display` line, about
5300-5308). The role pass is untouched. For each of sans, serif and mono: skip if the role pass set the token,
else `state.slots.find(slot => slot.type === "text" && byFamily(slot.family).tags.includes(kind))`, else nothing.
`state.slots` holds top-level slots only, and `type === "text"` excludes Rows, so row children and Rows never
feed a token. `--font-display` (`slots[0]` fallback) and `slots`/`layout` building are unchanged in the diff.
Every one of the 15 library families carries exactly one of `serif`, `sans`, `mono` (lines 1185-1349), so the
tag test is total and unambiguous. Sheets: `withCompositionSheets` builds its list from the slot families plus
`tokenFontSheets({...live.savedTokens, ...patch.tokens})`, so an unsent token adds no sheet. Verified in the
RED evidence (the Fraunces token was the bug) and by the passing FreeFont/CompositionFont runs. Caveat, not
introduced here: a token that an earlier sync already put on the page stays in `live.savedTokens`, so its sheet
stays until Reset; "not sent" means "leave alone", exactly as the serif rule did in Task 4.

### 2. Precedence and behaviour differences

Old vs new, line by line: role pass identical (same code). Old fallbacks: sans `slots[1]`, serif first serif-tag
text slot (Task 4), mono `slots[3]`, each only `if (!tokens[x] && ...)`. New: same guard (`if (tokens[token]) return`),
then the tag search. Order sans, serif, mono does not matter, since the tokens are independent. Precedence is
preserved: role wins, then fallback. A role match that yields a falsy string cannot happen (cssStack is non-empty).

Differences on existing compositions (I traced the three presets by hand; fixtures under `tests/` build their own
slots and none asserts a default-preset sans or mono token; the suites I ran pass):

- asteria and blank: roles Body and Metadata set sans and mono; serif is the first serif slot (as after Task 4).
  No change.
- rowdemo, the default preset (Wordmark Fraunces, H1 Instrument Serif, Row[image, Body Inter], Metadata IBM Plex Mono):
  mono by role, unchanged. `--font-sans` used to be sent as `"Instrument Serif", serif` (slots[1], a serif
  used as the sans token). It is now not sent at all, because the only sans family sits in the Row child, which
  never feeds a token by the brief's rule. A user syncing the default preset to a target will notice the target's own
  sans text is no longer restyled to Instrument Serif. That is the intended fix, but it also means the row's
  Inter does not reach the page's sans token. Product call for the owner, not a defect.
- Any composition where slot 1 or slot 3 is a non-sans or non-mono family or a Row: tokens change or disappear
  as above. A composition whose slot 1 was a sans family and slot 3 a mono family: no change.

### 3. Test quality

Mutations on a scratch copy (all reverted; the worktree `git status` shows only the implementer's three files):

| Mutation | Result |
|---|---|
| Restore the `slots[1]` sans line, loop only serif and mono | 2 FAIL (sans-row case, no-sans case) |
| Restore the `slots[3]` mono line, loop only sans and serif | 2 FAIL (mono-row case, no-mono case) |
| Loop without the tag check (first text slot wins) | 6 FAIL (all but the role-wins test) |
| Drop `slot.type === "text"` (a Row falls back to Fraunces) | 1 FAIL (serif no-token test) |

Each new behaviour has a test that fails when it is removed. The serif tests that predate this task still pass
and still fail under the tag-check mutation.

`NO_ROLE_MONO = ('Footnote', ...)`: "footnote" matches none of the role pass's substrings (title, display, hero,
lead, body, deck, editorial, quote, narrative, serif, mono, data, caption, code), so the mono token can only come
from the tag fallback. 'Metadata' and 'Caption' match `data`/`caption` and would hide the fallback, so this is the
right way to test the fallback and does not hide a role-pass bug; the role pass itself is covered separately by
`test_a_role_match_still_wins_the_sans_and_mono_tokens` (Body on a serif family gives sans, Caption on Inter gives
mono; the tag-first order would fail it). The sans tests use 'Wordmark' and 'H1', which also match no role.

Tokens are read from what the fake target received after Sync to Live App (the `design:update` patch), and the
tests assert the family named, not only that a message was sent. The fake-target boundary is the same as the
existing serif tests; the real Studio/real bridge boundary is covered elsewhere in the suite.

Rename `SerifTokenTests` to `TokenFallbackTests`: grep over the worktree and the main tree finds the old name only
in a stale `.pyc` and in the historical `docs/implementation/tasks/v021-task-4-brief.md:90` (a task record; leave it,
or the controller may touch it up). Nothing imports or selects the class by name. Acceptable.

Nit (no action required): the appended comment block sits after two blank lines inside the class
(`tests/test_studio_stage.py` lines 185-186); one blank line matches the surrounding style. Docstring line 1 of
the module is now long (over 100 columns) but the file has no line-length gate.

### 4. Sleeps

No `sleep` or `wait_for_timeout` in `tests/test_studio_stage.py`; the new tests use the existing
`wait_connected`, `wait_live` and update counting.

### Docs and siblings (anti-pattern 12)

No remaining `slots[1]`/`slots[3]` index fallback in `compositionPatch`; the README does not describe the
fallback by position (README line 470 and the typography design only name the tokens). The plan's Task 4 text
(plan line 29, 112) describes the serif-only starting point; the controller should record Task 4b in the ledger.

### Verdict

Approved. No fixes required. Observations for the owner: the rowdemo difference above, and that a token an
earlier sync already placed on the target is not withdrawn when it stops being sent.
