# v0.2.0 review fixes: selectors, composition tokens, late replies

Plan: Addendum 6 in `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md`.

## 1. Synced CSS keeps rules for path selectors

**Problem.** The bridge gives an auto-discovered target without a unique id a
path selector such as `main:nth-of-type(1) > section.hero:nth-of-type(2) > h2`.
Studio checked selectors with the declaration-value filter, which rejects `>`,
so the CSS tab, Copy, Download and Sync replaced the rule with a "skipped"
comment and the edit was lost from the saved file.

**Change.** Selectors now have their own validation in
`font_kit_studio_v0.1.1.html` (`SELECTOR_GRAMMAR`). It accepts what the bridge
generates: tag, `#id`, `.class`, `[data-design-id="..."]` (only `\"` and `\\`
escapes inside the quotes), `:nth-of-type(n)`, joined by ` > `. Identifiers may
carry CSS escapes, so utility classes such as `.sm\:flex` and `.w-1\/2` work.
It still rejects `{ } ; < >`, other backslashes, line breaks, comment markers,
`!important` and `url(`. Declaration-value validation is unchanged.

**Tests.** `StudioReviewFixTests` (fake target reports accepted and hostile
selectors) and `AutoDiscoveredSelectorTests` (real bridge, demo: edit the
"Solo" pricing heading, check the CSS tab, the synced file, and that the written
selector matches exactly that heading).

## 2. Reapply makes the target's tokens equal the saved set

**Problem.** A composition update never deletes an omitted token. When the
target held a token Studio's saved state did not have, Reapply sent nothing (or
only overwrote saved names), then cleared the conflict and reported success
while the app kept the token.

**Change.**
- `fontkit-bridge.js`: a `null` token value in a composition update removes
  Studio's override (`removeToken`). The target's original inline value, or its
  absence, comes back exactly, because the original is captured once before the
  first write. The token leaves the ledger. A name that was never overridden is
  ignored; invalid names still reject the whole update.
- Studio: Reapply sends every saved token plus `null` for every target-only
  token (`reapplyTokenPatch`). Success is reported only when the target's
  ledger tokens equal the saved set (`finishReapply`); otherwise Reapply stops
  with a message naming the leftover tokens, the conflict stays open, and
  Studio's saved tokens are not replaced by the target's (`failReapply`).

**Tests.** Bridge: `TokenRemovalTests` (byte-exact restore of an inline style
with unusual spacing, stylesheet-defined token, unknown and invalid names,
global reset). Studio with the fake target (now supports `null`):
target-only tokens removed, saved tokens mixed with `null`, and a target that
keeps the token never reports success. Real bridge:
`ImportedTokensTests.test_import_reconnect_reapply_removes_a_token_the_saved_state_no_longer_has`.

## 3. Late acknowledgements after several timeouts

**Problem.** Studio remembered only the most recent timed-out request. With two
or more queued edits and an unresponsive target, the second timeout replaced the
first, so the first request's late acknowledgement was dropped and that edit
was missing from saved overrides and synced CSS.

**Change.** Timed-out requests are kept in a `Map` keyed by request id
(`live.timedOut`) until the late reply arrives or the session ends. A late
acknowledgement for any tracked id is applied; a late rejection is only
forgotten.

**Test.** `test_every_timed_out_request_stays_tracked_until_its_late_reply_arrives`:
the fake holds replies through two timeouts, then both late acknowledgements are
released; both edits appear in saved state, the CSS tab, the JSON export and the
synced PUT body.

## Changes after review

**Selector check cannot stall Studio.** The first selector grammar let a hex
escape and plain identifier characters (hex digits are both) match the same
text in several ways, so a hostile selector reported by a target, such as a
dot followed by eleven `\aaaaaa` escapes and a brace, froze the page for about a
minute. Identifiers now match each text in exactly one way: a backslash plus a
non-hex character, a backslash plus six hex digits, or a backslash plus one to
five hex digits not followed by another hex digit (each with one optional
trailing space), or a plain character. The check is linear. Tests:
`test_adversarial_escape_runs_do_not_freeze_studio_and_are_skipped` (the page
stays responsive and the rule is skipped) and
`test_the_selector_check_itself_is_fast_on_500_character_inputs`, which runs the
shipped regexes on adversarial and long valid inputs and requires each to finish
in under 50 ms.

**Escaped special characters in class names.** A backslash followed by any
non-hex character is now an escaped character inside an identifier, so real
bridge output for utility classes such as `.\[\&\>\*\]\:p-4` is kept. The same
characters unescaped (`{ } ; < >`), a trailing backslash, line breaks, comment
markers and `url(` are still refused. Test:
`AutoDiscoveredSelectorTests.test_class_names_with_escaped_selector_characters_keep_the_edit`
(real bridge and demo; the persisted selector matches exactly the edited
heading and reaches the synced file), plus escaped-character selectors in the
fake-target matrix.

**Late rejections are reported.** When a request that timed out is later
refused by the target, Studio now shows `Rejected: <reason>` and re-reads the
inspector controls from the page, instead of forgetting it silently. Nothing is
retried: the user moved on while the target was silent. With a target that
enforces revisions, the first edit is saved, the second shows
`Rejected: revision-conflict` with the page's real value in the inspector, and
entering it again works because Studio took the target's revision from the late
replies. Test: `test_a_late_revision_conflict_is_shown_and_the_first_edit_is_kept`.
The earlier end-to-end test (a target that applies both queued requests) stays,
and both tests now wait for the second timeout by condition instead of a fixed
pause.

## Promoted targets

**Problem.** An element edited as an auto-discovered target can later get an
author `data-design-id` (for example when the app follows Studio's "add a
data-design-id" hint). Discovery then registered it under the new id, but the
acknowledged change stayed listed under the old id, which no longer exists. The
change ledger dropped it while the inline override stayed on the page, so the
next handshake reported no change. Studio then opened a false reconnect conflict,
or a fresh Studio lost the edit.

**Bridge** (`fontkit-bridge.js`, `promote`). When discovery re-registers the same
element under a new id, the edit moves with it: its place in the change order and
its font stylesheet reference, plus the selection and hover when they pointed at
the old id. The captured originals (inline style, text, moves) are keyed by
element and are never captured again, so Reset of the new id restores exactly what
the page had before the first edit (the author's inline `style` byte for byte,
the original text). The ledger reports the target under the new id with the stable
selector. Discovery also runs when an author `data-design-id` is set in place, so
a promotion that adds or removes no node is noticed without waiting for another
page change.

**Contract addition (additive, implemented).** A target manifest may carry
`previousId: "<old id>"` once its element was promoted. It appears in
`design:ready`, `design:targets`, `design:selected` and `design:applied`
manifests, and only on promoted targets. Studios that do not know the field
ignore it.

**Studio** (`followPromotedTargets`). When a manifest names a `previousId`
Studio holds a saved override for, the override is re-keyed to the new id (merged
under any override already saved for the new id), the target's metadata is
dropped for the old id, and the inspector selection follows. This runs on
`design:ready` before the reconnect comparison and on `design:targets`, so the CSS
tab and exports show the stable selector without the "add data-design-id" hint,
and a reconnect finds saved and live state in agreement. Nothing is sent to the
page and nothing is written to the overrides file by the re-keying itself.

**Limits.** An edit request already queued for the old id when the promotion
happens is rejected as `unknown-target` and shown as such; the user enters it
again. Only the most recent previous id is reported if an element is promoted
twice. A Studio whose saved state names an old id the bridge never reports (the
page was reloaded after the promotion, so the id is gone) cannot map it; that is
an ordinary reconnect conflict the user resolves with Reapply or Accept.

**Tests.** Bridge: `PromotedTargetTests` (edit as auto target, set the author id,
run discovery, ledger under the new id in its original place, previous id in the
manifest, byte-exact reset including an oddly spaced inline style, fresh handshake,
attribute-only discovery). Studio with the fake target (now supports promotion):
`StudioPromotedTargetTests` (saved override re-keyed with no conflict; a state
saved under the old id re-keyed at the next handshake). Real bridge:
`AutoDiscoveredSelectorTests.test_promoting_the_target_to_an_author_id_keeps_the_edit_and_raises_no_conflict`.

## Gate font measurement deadline

- Problem: `FONT_FACES_JS` in `scripts/dev/_frontend_gate_network.py`
  awaited `document.fonts.ready` and then each `document.fonts.load()` in
  turn. The 30 s status wait before it does not bound that evaluate, and
  `page.evaluate` has no timeout. A promise that never settles stalled the
  gate, so the retry, the REPORT and FAIL lines and the test suites after it
  never ran.
- Reproduced: with `document.fonts.load` pending for one family, the
  measurement was still running after 300 s (killed by hand); a 30 s
  watchdog in the new test ended the run with a stack dump.
- Change: the in-page measurement races against one shared deadline
  (`FONT_MEASURE_DEADLINE_MS`, 15 s per measurement, passed in by
  `measure_font_faces`). Every family starts as `[0, 0]`, and the loads run
  together so one stalled family cannot hide the others. Unanswered
  families stay missing, so `settle_free_fonts` retries them and
  `free_font_failures` reports them as before.
- Tests: `tests/test_frontend_gate_fonts.py` runs the measurement in real
  browsers against a pending `load`, a pending `ready`, eight stalled
  families sharing one deadline, an answering page that must not wait for
  the deadline, and the retry and failure reporting end to end.
- Hardening: a rejecting `document.fonts.ready` or a page with no
  `document.fonts` also returns all-missing counts instead of raising, and
  the result is a copy so a late load cannot change it.
- Worst case: one stalled attempt costs 15 s, so the online free-fonts
  check is bounded at about 109 s (3 measurements, 2 status waits of 30 s,
  1 s and 3 s backoffs).
- Not run: the online gate cannot pass in this sandbox (Google Fonts is
  unreachable, so it reports the documented "none of the 16 library
  families produced a face" failure after the bounded retries).

### Limits of promotion handling

- An author-to-author rename (an element whose `data-design-id` changes from
  one author id to another) carries the element's edits to the new id. An app
  that reuses one DOM node for different items therefore carries the edits
  across items.
- Removing the author attribute from a promoted element is not noticed: the
  ledger keeps reporting the stable selector.
- The bridge keeps `previousId` on the record for the session. After a page
  reload a saved override under a stale auto id could be re-keyed if a manifest
  still names it; the case is narrow, and the guard below keeps it from touching
  any target that is still in the list.

### Round 2

- **A `previousId` naming a live target no longer moves its override.**
  `followPromotedTargets` ignores a `previousId` that is empty, not a string, equal
  to the target's own id, or the id of any target in the same manifest list. A
  manifest giving `auto.h2.1` the previous id `hero.title` used to drop the saved
  `hero.title` edit while it stayed live on the page, so the next sync would have
  written a file without it.
  - RED: `test_a_previous_id_naming_a_live_target_or_nothing_usable_never_moves_a_saved_override`
    failed 8 sub-tests before the change (saved overrides lost `hero.title`; the
    CSS tab lost its rule).
  - GREEN: it passes. Both saved overrides and the CSS tab are unchanged for seven
    hostile or unusable values (a live id, a number, an empty string, null, a list,
    its own id, an unknown id). Nothing is sent to the target, and the only write is
    the explicit Sync click, which contains both rules.
- **No fixed pauses.** The two re-announce tests now wait until Studio has finished
  handling `design:ready`, using a counter that a zero-delay timer increments after
  every message listener ran, instead of 300 and 400 ms sleeps.
