# Task 10 brief: a warning channel for outcomes the page cannot show

Plan Task 10, wave 2, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit rows B08, D2-11 and B19 share this
channel; this task adds only the channel and sends nothing. Budget: about 120 gross lines (about 45 source, 75 tests).
Recorded: D079 (`docs/implementation/deviations.md`, row at BASE) and New string 11 (approved, O31).

## Why

Studio's `noteWarning` drops every `design:warning` whose kind is not `runtime-error` (`fontkit-studio.html:6404`), and
its banner always starts "Runtime error in the Live App" (`:6421`). Tasks 11 and 12 must tell the user about a token that
changed no element (B08) and an edit lost when the app replaced or kept re-creating a node (D2-11, B19). Neither is a
runtime error, so reusing the kind would mislead (D079). The bridge also has no sender for them: its only warning
source is `noteRuntimeError` (`fontkit-bridge.js:2245-2258`), which needs a recent change watcher. The plan's cause
holds at BASE.

## Owned files (exact)

- `fontkit-studio.html`: `noteWarning` and `renderWarnings` only (`:6401-6429`, section comment at `:6401`). The
  dispatch case at `:5868` and the `<ul id="liveCodeWarnings" ... aria-label=...>` markup at `:1244` stay untouched.
- `fontkit-bridge.js`: one new method directly after `noteRuntimeError` (ends `:2258`), before the `design:update`
  section comment. No other line.
- `tests/fixtures/studio/fake-target.html`: `fake.warn` (`:284-286`) only.
- `tests/test_bridge_runtime.py`: a new class directly after `RuntimeWarningTests` (`:2462-2512`), before
  `PopOutOverlayTests`.
- `tests/test_studio_live.py`: a new class directly after `StudioArrangeTests` (starts `:1401`), subclassing
  `ArrangeCase`.

Everything else is read-only. No CHANGELOG line (nothing sends the kinds yet; the controller owns the ledger).

## Read first

`fontkit-studio.html:5860-5870, 6400-6431`; `fontkit-bridge.js:84-85, 1119-1127, 2239-2258`;
`tests/test_bridge_runtime.py:106-115, 1799-1815, 2462-2490`; `tests/test_studio_live.py:1376-1400, 1635-1660`;
`tests/fixtures/studio/fake-target.html:253, 284-286`; plan "Binding message contract".

## Requirements

1. **Sender, frozen for Tasks 11 and 12.** The bridge class gains
   `postWarning(kind, targetId, message, requestId = null)`, returning nothing. It posts
   `{type: 'design:warning', requestId, targetId, kind, message}` through `this.post`, with
   `message = String(message).slice(0, WARNING_MAX_LENGTH)`; `requestId` is the given string or `null`; `targetId` is
   the target's id or `'global'`. It posts nothing when `this.studioSource` is null (as `noteRuntimeError` does) or when
   `kind` is not one of `token-not-applied`, `edit-not-reapplied`, `edit-reapply-stopped`. `noteRuntimeError` is
   unchanged. Oracle: the literal message the test records from the page's `postMessage` log.
2. **Studio shows each new kind.** `noteWarning` accepts `runtime-error` and the three kinds above, stores the kind with
   the entry, and still ignores any other kind and any empty message. Oracle: the literal strings below.
3. **Banner text.** For a latest entry of a new kind the banner reads `Note from the Live App about <name>: <message>`,
   or `Note from the Live App: <message>` with no name (`targetId` empty or `global`). `<name>` is the target's
   name as `warningLabel` already resolves it. It does not contain "Runtime error". For `runtime-error` the banner is
   unchanged, byte for byte.
4. **List label.** Entries still render one `<li>` each, as now. The `liveCodeWarnings` accessible name is
   `Notes from the Live App` when every stored entry is a new kind, and the existing
   `Runtime warnings from the Live App` otherwise (set from `renderWarnings`; see Open questions).
5. **Unchanged.** The 300-character cap, `MAX_WARNINGS`, Dismiss, textContent-only rendering, the session check, and
   `tests/test_studio_visual.py:537`'s "Runtime error in the Live App" assertion.

## Tests

Bridge class `PostedWarningTests(ArrangeCase)`:

- `test_a_posted_warning_carries_the_kind_message_and_cap`: Given a connected bridge, When the page calls
  `window.__fontkitBridge.postWarning('edit-not-reapplied', 'arr.btn.a', 'x' * 900, 'r7')` for each of the three kinds,
  Then Studio's inbox shows `{kind, targetId, requestId: 'r7', sessionId: 's1'}` and a message of exactly 300 characters.
  RED: the method does not exist. Break: dropping the `slice`.
- `test_nothing_is_posted_for_an_unknown_kind_or_without_a_studio`: Given a connected bridge, When `postWarning('runtime-error', ...)`
  and `postWarning('made-up', ...)` run, Then no `design:warning` appears; and after the Studio source is cleared
  (`__fontkitBridge.studioSource = null`) a valid kind posts nothing. RED: the method does not exist. Break: dropping
  the kind check.

Studio class `LiveAppNoteTests(ArrangeCase)` (`fake.warn(message, targetId, requestId, kind = "runtime-error")`):

- `test_each_new_kind_shows_in_the_banner_and_list_with_the_target_name`: Given a connected Studio with a selected
  target, When the fake posts each new kind for `hero.title`, Then `#bridgeWarningText` equals
  `Note from the Live App about <name>: <message>` (name read from the target list in the page, not from source), the list
  has the message, `#liveCodeWarnings` has aria-label `Notes from the Live App`, and "Runtime error" is absent from both.
  RED: Studio ignores the kind. Break: dropping a kind from the accepted set.
- `test_an_unknown_kind_is_still_ignored`: Given the same page, When the fake posts kind `made-up`, Then the banner stays
  hidden. GREEN characterization (already true).
- `test_a_runtime_error_after_a_note_restores_the_runtime_label`: Given one note then one `runtime-error`, Then the banner
  starts "Runtime error in the Live App" and the list label is `Runtime warnings from the Live App`. RED for the label
  only. Break: setting the label once from the first entry.

The existing runtime-error tests (`test_studio_live.py:1633`, `test_bridge_runtime.py:2463`) must stay green unedited.

## Focused command

From `the task's worktree`, with a timeout of 600 s, one module at a time (never a shard, never a dev server):

```
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime.PostedWarningTests test_bridge_runtime.RuntimeWarningTests test_support -v
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_live.LiveAppNoteTests test_studio_live.StudioArrangeTests.test_runtime_warnings_reach_the_status_area_and_code_panel_as_text test_support -v
```

Landing also runs `test_studio_roles`, `test_role_routes` and `test_r2_integration` (controller).

## Patches

One audit-row-free commit, so one patch: `task-10-code.patch`. Subject (68 chars):
`fix(protocol): carry three more warning kinds from the bridge to Studio`. No CHANGELOG line. Tasks 11 and 12 start from
this patch and call `postWarning(kind, targetId, message, requestId)` exactly as frozen in requirement 1.

## Open questions

1. **Mixed list label.** The list holds up to five entries of any kind but has one label. Options: (a) all-notes gives
   the new label, otherwise the old one (specified above); (b) always the old label; (c) a per-entry prefix. The plan
   fixes only "list label for the three kinds". Recommendation: (a), since it uses New string 11 without per-item text
   the approved strings do not cover. Needs a controller yes before dispatch.
2. **Banner for a mixed list.** The banner follows the latest entry's kind (requirement 3). Recommended; say if not.

## Controller rulings

1. Open question 1: yes, as the brief specifies.
2. Open question 2: yes, the banner follows the latest entry's kind.
3. The commit scope is bridge: fix(bridge): carry three more warning kinds to Studio. protocol is not a scope in use.

## Review fixes (binding: these govern over the text above)

1. Owned files gain `tests/test_studio_roles.py`: one new class directly after the nearest related test, using `StudioRoleCase` (real Studio, real bridge). For each of the three kinds, `window.__fontkitBridge.postWarning(kind, 'global', ...)` with `<img src=x onerror="window.__xss=1">boom` appears as text in `#bridgeWarningText` and `#liveCodeWarnings`, with no `img` element and `window.__xss` undefined. A 900-character message reaches Studio at 300 characters. Kinds `made-up`, `constructor` and `__proto__` show nothing. A message forged with `sessionId` `fks-wrong` is not shown. Breaks: drop the kind allowlist; render with innerHTML.
2. `postWarning` argument rule, frozen for Tasks 11 and 12: `targetId` is `typeof targetId === 'string' && targetId ? targetId : 'global'`, and a non-string or empty `message` posts nothing. Add a bridge assertion for the `'global'` fallback and for an omitted `requestId` sent as `null`. An auto id no longer in the target list falls back to the raw id in Studio's label, which is accepted. Break: sending `null`.
3. `test_a_runtime_error_after_a_note_restores_the_runtime_label` asserts the list holds both entries, so it fails at BASE. State the label when the list is empty after Dismiss.
4. Use `Object.hasOwn` or a `Map` in `warningLabel`, and add `constructor` and `__proto__` targetIds to the Studio name test.

---

# Task 10 follow-up: Given/When/Then docstrings

The worktree `the task's worktree` holds Task 10's finished work, unstaged. Keep it. The plan requires a Given/When/Then docstring on every new test, and the new tests have none (`task-10-code-review.md`, Minor).

Add one to each test this task added, in `tests/test_bridge_runtime.py`, `tests/test_studio_live.py` and `tests/test_studio_roles.py`. Each says the behaviour it guards, in plain words, from what the test really does. Change no assertion and no code. Do not touch `fontkit-bridge.js` or `fontkit-studio.html`. Do not write a patch: the controller regenerates it from the worktree.

Run `python -m ruff check` on the three files. No browser run is needed, because only docstrings change: confirm that with `git diff --stat` before and after, in your report.
