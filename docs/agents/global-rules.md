# Global Business Rules

These are the product and engineering rules every change to fontkit should
respect. They are judgement rules, not a mechanical invariant engine: most are
checked by tests and review. `AGENTS.md` owns session procedure, commit format
and the anti-pattern registry; this file owns the "what must stay true" and
how to break ties.

## What wins when two rules conflict

Apply in this order. Higher wins.

1. **Safety of the user's app and data (Rules 5, 6).** Never execute untrusted
   input, never silently overwrite the running app or the user's files.
2. **The running app owns rendering; Studio owns persistence (Rules 1, 2).**
3. **Single source of truth (Rule 9).**
4. **Isolation of the target boundary (Rule 4).**
5. **Rule of three (Rule 10).**
6. **Simple runtime code (Rule 8).**

How cheap or fast a change is never decides correctness. If two rules cannot
both hold as written, stop and ask the owner; do not document an exception
into existence while the rule it breaks still reads as absolute.

## 1. The running app owns the page

- Studio instruments a live app; it never becomes the app's renderer, CMS or
  build system.
- The bridge decides whether a patch is valid, applies it, and reports the
  canonical result. Studio shows what the target acknowledged, not what it
  requested.
- fontkit does not rewrite source code. Its outputs (overrides CSS, changed
  HTML snippets, JSON) are artifacts the user reviews and applies.

*Checked by:* review; contract tests in `tests/test_bridge_runtime.py`.

## 2. Studio persists only acknowledged state

- Live edits stream immediately; persistence (overrides file, JSON export) is
  built from acknowledged canonical state, debounced and serialized.
- Never overlap writes to the same file; the latest acknowledged state wins.

*Checked by:* `tests/test_studio_live.py` sync tests; dev-server write tests.

## 3. Explicit contracts beat inferred DOM paths

- Author `data-design-id` values are the stable API. Prefer them everywhere.
- Auto-discovered targets work, but their selectors are labelled unstable in
  the inspector and the CSS export (and `stable:false` in the ledger), with a
  hint to add a `data-design-id`. Persisting such DOM-path selectors bends
  Spec section 2.3 on purpose for zero-hook use; see D016.
- The protocol contract in the active plan is the shared truth between Studio
  and bridge. Change it in the plan first, then in both sides.

*Checked by:* review; ledger selector tests.

## 4. Editor chrome never leaks into the target

- Hover and selection outlines live in Studio's overlay. The only exception is
  pop-out mode (and the page option `enableHighlightOverlay`), where the
  bridge draws a non-interactive outline that it removes on exit and strips
  from every export (D016).
- Bridge-added attributes and inline overrides are stripped from exported
  HTML; the author's own attributes and styles are preserved.

*Checked by:* cleaned-HTML ledger tests; review.

## 5. Every boundary is a trust boundary

- Cross-window messages are validated by source window, origin, protocol
  version and session before use. `design:bridge-ready` and `design:hello`
  carry no session; hello is accepted only from the parent or opener.
- Values crossing the boundary are allow-listed (CSS values via validation and
  `CSS.supports`, URLs by scheme and host, text via `textContent`).
- Untrusted markup is never parsed into a live document.
- The dev server binds loopback, checks `Host` and `Origin`, limits size and
  writes atomically to one configured path.

*Checked by:* hostile-origin and hostile-payload tests; review.

## 6. Never silently overwrite either side

- Connecting, reconnecting or reloading must not push Studio state into the
  app, or app state into the user's saved overrides, without an explicit
  choice the user can read.
- Structural edits (moving buttons, cards, form controls) are reversible and
  guarded: refuse or warn when a move would break form ownership, radio
  groups, label/aria references, content-model rules or framework-managed
  DOM. Offer CSS `order` where layout allows (it is the default for
  framework-managed parents). Structural moves go beyond Spec section 19 by
  owner decision (D016).

*Checked by:* reconnect and guard tests; review.

## 7. Free, generic defaults

- Out of the box fontkit uses free OFL fonts and an offline demo. No personal
  kit IDs, keys or accounts are prefilled.
- Opening Studio contacts no third party. Free fonts load only after the user
  asks (Load free fonts, remembered per browser, or picking a library family
  in the Live Target inspector); until then specimens use local fallbacks
  (D028).
- Paid or account-bound providers (Adobe Fonts) are opt-in, bring-your-own.

*Checked by:* the frontend gate's network-isolation check; review; grep for
credentials and kit IDs.

## 8. Simple runtime, strict tests

- Studio stays a single HTML file with no runtime dependencies or build step.
  The bridge stays dependency-free. Dev tooling uses the Python stdlib.
  Google Fonts stylesheets load only after the user asks (Rule 7); offline or
  before that, the fallback stacks are used.
- Preserve what users already have: Library mode, the Composer, existing leaf
  controls and import/export compatibility. Composer rows hold 2-4 leaf slots;
  nested rows and JPEG assets stay out of scope.
- Keep runtime code flat and predictable; put rigour into tests (real browsers,
  real cross-origin frames) rather than defensive layers.
- The product is desktop-first: in the frontend gate, desktop Chromium
  blocks; other engines and phone or touch layouts are reported as advisory
  (D029). The Chromium test suite still blocks, including the Composer's
  existing 390px mobile-layout tests.

*Checked by:* `scripts/verify.py`; layout tests; review.

## 9. Single source of truth for docs

- Each fact has one owner document; ownership and the copy rule are in
  `AGENTS.md` ("Document Roles").
- Current code and committed records beat memory, chat and unpublished
  reviews.

*Checked by:* review; grep when a fact changes.

## 10. Rule of three

- Duplication is acceptable until the third occurrence. Studio and bridge
  intentionally each validate patch values on their own side of the
  boundary; that is isolation, not a DRY violation.
- Abstract only when a third copy appears, and only within one side of the
  boundary.

*Checked by:* review.
