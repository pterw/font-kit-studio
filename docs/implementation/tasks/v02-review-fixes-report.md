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
