# R2.W2S-a code report (MODE code, task w2sa, BASE 73b3ba2)

Changed (staged in a scratch worktree, patch `task-w2sa-code.patch`): `fontkit-studio.html` (+4/-3), `tests/test_r2_integration.py` (+16/-4).
Gross 27 lines (budget 90); material 27. Worktree files are CRLF (autocrlf); the index and patch are LF.

## Requirements
1. Done. The Bootstrap 4 / role-target test types 27 (not a native size), asserts `len(request['roles'])` is 16 / 2, plain adapters,
   waits `wait_for_receipt` AND Studio status `Preview applied to N roles; 0 checked elements did not show it.`, asserts every outcome
   `mismatched == 0` and `losses == []`, `matched` sums to 20 / 2, and every element each role's request selectors match computes 27px.
   Given/When/Then docstring updated. Oracle: the brief-review's measured literals, not the code under test.
2. Done. Comment now names `roleCssBlocks`.
3. Done. `const names = ROLE_ADAPTER_VARIABLES[role.adapter]; const root = names && Object.hasOwn(role.properties, "fontFamily") ? ... : "";`
   Output unchanged (BS5 integration and all StudioAdapterTests pass).

## Evidence
GREEN: `python -m unittest test_r2_integration.StudioRoleBridgeTests -k bootstrap_4_fixture` -> Ran 1, OK.

Mutants (scripts `mutate-w2sa.py`, foreground, restored in finally; SHA-256 before = after):
- bridge-skip-role-4 (`fontkit-bridge.js` `roleCssBlocks` gets `if (role.id === 'role-4') continue;`), SHA a7e81ca1fd057f391b41d019ab63d015d2491b7c9c87f56cd632196a7e189a5f both times.
  RED: the BASE test (copy of HEAD's file, size 24) -> Ran 1, OK (mutant invisible). New test -> ERROR, target='bootstrap4',
  TimeoutError at `wait_status` (line 794): Studio refuses the receipt whose CSS disagrees with its serializer, so the status never
  reads "Preview applied". The rendered-size assertion is not reached by this mutant; the status wait catches it first.
- studio-drop-root-lf (`.join("")}}\n` : ""` -> `}}` : ""`), SHA 9d80fa420cceeb85f08309256bb965f51b2ca977a1cf8355dbc196dfc65cfe36 both times.
  Fails: `test_a_bootstrap_5_body_row_applies_with_its_variables_and_clear_restores_the_page` (line 766, startswith assertion) and 6
  StudioAdapterTests errors: `test_a_ready_snapshot_with_each_template_cases_literal_bytes_is_accepted_and_shown` (body, mono, mixed),
  `test_an_unsupported_adapter_rejection_keeps_the_template_preview_the_drafts_and_sends_nothing_again`,
  `test_apply_sends_each_selected_groups_adapter_in_row_order_and_shows_the_template_bytes_of_the_receipt`,
  `test_the_body_case_receipt_shows_its_template_bytes_and_a_receipt_with_the_plain_bytes_is_ignored`.
- studio-root-without-fontfamily (condition reduced to `names`), same SHA before/after. The BS5 integration test PASSES (gap there:
  its only adapter row sets a family). Killed by StudioAdapterTests:
  `test_a_ready_snapshot_with_each_template_cases_literal_bytes_is_accepted_and_shown` (case='body-without-family') and
  `test_a_groups_adapter_changed_between_two_detects_is_what_the_next_request_carries`.

## Gates
- `gate.sh focused test_studio_roles test_r2_integration test_support`: `Ran 150 tests in 210.797s`, `OK`, `GATE focused EXIT 0 IN 211s`.
- `verify.py --static-only`: provenance PASS lines, browser SKIP. `ruff check tests/test_r2_integration.py`: All checks passed.
- `git diff --cached --check`: exit 0. Patch `git apply --check -R`: ok.

## Handoff
Commit subject: `test: assert what the Bootstrap 4 role preview renders`. Draft body:

    The Bootstrap 4 and role-target test asserted only the request
    Studio sent. It now types 27px, which no fixture element computes,
    waits for the receipt and Studio's "Preview applied" status, and
    checks the receipt outcomes and the computed size of every element
    each role's selectors match.

    Studio's serializer comment now names the bridge's roleCssBlocks,
    and its :root block is one conditional shaped like the bridge's.
    The output is byte-identical; only the shape and the comment change.

Plan: R2.W2S box stays unticked until slice c lands. No contract-table change. Budget note: slices a+b+c total 200 vs original 140.
Deviation: none. Note the bridge mutant fails at the status wait, not at the size assertion.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
