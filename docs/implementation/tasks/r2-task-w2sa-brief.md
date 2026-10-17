# R2.W2S-a brief: the Bootstrap 4 test asserts what renders; Studio's serializer names its twin

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 22, task R2.W2S (slice a of three: a, then b, then c). PR B2 wave W2,
phase 1, beside R2.W2T, R2.W2L and R2.W2B2 phase 1. BASE `73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`. Worktree
`a scratch worktree`, task id `w2sa`. Line budget: about 90 gross lines; explain any excess.

## Why

1. **A message-only test.** `test_every_request_from_the_bootstrap_4_fixture_and_the_plain_role_target_carries_the_plain_adapter`
   (`tests/test_r2_integration.py` 775-790) asserts only the request Studio sent (`press_apply` returns once the peer has
   it) and never what the page rendered. AGENTS.md forbids that ("Asserting that a message was sent without asserting what
   the page then rendered"); its Bootstrap 5 sibling waits for the receipt and reads computed fonts.
2. **Stale pointer.** The comment at `fontkit-studio.html` 3920 says Studio's serializer is "duplicated from the bridge's
   serializeRoleCss"; the bridge's function is `roleCssBlocks` (`fontkit-bridge.js` 289). The pair is kept byte-identical on
   purpose (global rule 10), so the pointer must name it.
3. **SIMPLIFY6 (workspace `w2-review.md`).** Studio's `:root` block (3925-3926) is written as two statements where the
   bridge's `roleCssBlocks` (292-295) has one conditional. Shaping Studio's like the bridge's makes the byte-identical pair
   easy to compare. Output must not change by one byte.

## Owned files (exact)

- `fontkit-studio.html`: the serializer comment at 3920 and the serializer body at 3920-3930 (SIMPLIFY6). Nothing else.
- `tests/test_r2_integration.py`: the Bootstrap 4 test above. Nothing else (R2.W2S-c adds `FAMILIES` rows later).

Read-only: `fontkit-bridge.js`, `tests/test_studio_roles.py` (R2.W2T owns it now), `tests/role_contract.py`, every other
file. Running worktrees beside yours: `a scratch worktree`, `a scratch worktree`, `a scratch worktree`. Never touch them.

## Read first

`constraints.md` (all of it); Addendum 22; at BASE `fontkit-studio.html` 3915-3935 and `fontkit-bridge.js` 286-300;
`tests/test_r2_integration.py` 1-60, 495-520 and 735-800 (the Bootstrap 5 sibling's receipt wait and computed reads);
`w2-review.md` SIMPLIFY6.

## Requirements

1. The Bootstrap 4 test types a size no fixture element computes before Apply (27px; 24px is Bootstrap 4's own h4 size, so
   a skipped block would be invisible), waits for each receipt AND for Studio's status
   `Preview applied to N roles; 0 checked elements did not show it.` (a receipt Studio refuses leaves it at "Applying role
   preview...": the receipt wait alone passes then), and asserts what the page renders: every element each role's request
   selectors match computes 27px. The receipt literals, measured at BASE by the brief review: every role `mismatched == 0`
   and `losses == []`, `matched` summing to 20 on the Bootstrap 4 fixture, 16 roles in its request (the role target's two
   likewise). Keep its existing request assertions.
2. The comment at 3920 names `roleCssBlocks`.
3. Studio's `:root` block is one conditional shaped like the bridge's, written with `Object.hasOwn` (Studio's idiom), with
   byte-identical output for every role. No other serializer change.

## Tests and mutants

The changed test keeps a Given/When/Then docstring whose Then is exactly what it asserts. Mutants (each in the foreground,
restored byte-exact, SHA-256 before and after): for requirement 1, the worktree's `fontkit-bridge.js` edited to skip one
role's plain block (this test's harness has no bridge-source hook) makes the Bootstrap 4 test fail on the rendered size;
for requirement 3, (a) a Studio serializer that drops the `:root` block's final LF fails the real Bootstrap 5 integration
test (`tests/test_r2_integration.py` near 745, at its `startswith(':root ...')` assertion) and the `StudioAdapterTests` in
`tests/test_studio_roles.py` (record which; the brief review saw six), and (b) the new conditional mutated to emit `:root`
for a body role with no `fontFamily` fails a named test (find it; if none fails, report that as a gap, do not add scope).
The template-digest test (2461) uses only the Python mirror and cannot catch a Studio change. A failing green is worse
than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_r2_integration test_support`.
The controller links the npm fixtures into the worktree before dispatch (`test_r2_integration` needs them); expect about
5-7 minutes. Also `python scripts/verify.py --static-only`, `python -m ruff check` on changed Python files, and after
staging by name `git diff --cached --check`.

## Report and handoff

Report: each requirement with its RED (requirement 1: the mutant passes the BASE test) and oracle; each mutant (command,
failing tests and lines, SHA-256 before and after); the focused run (Ran line, OK, GATE line); gross and material lines.
Patch `task-w2sa-code.patch` from BASE. Commit subject `test: assert what the Bootstrap 4 role preview renders` (the Studio
change is a comment and a byte-identical reshaping, so `test:` stays; the body names it), a draft body
(why, wrapped at 72, no process narration; name the Studio comment and serializer reshaping) and the R2.W2S plan item (the
box is ticked when slice c lands).
