### Spec Compliance
- PASS: Integrity. `git -C a scratch worktree diff --cached --stat` = 10 files, 1154 insertions(+), 252 deletions(-); `git diff --binary` sha256 7285916eac82b446d703c7f4b4b64eb894e87ca3833cee8f05bc378c4740b9b6 = the patch file's (6935 bytes both). Re-checked after my runs: unchanged. (`MM` on tests/test_r2_integration.py is the expected staged-W2SA plus unstaged-delta state.)
- PASS: Requirement 2. The existing Bootstrap 5 test changes only its font-size line to `['16px', f'{size}px', f'{size}px', '16px']` (tests/test_r2_integration.py patch line 20) and its docstring (patch lines 8-12). The buttons stay in the tuple; nothing else in that test changes.
- PASS: Requirement 1. New test (patch lines 28-78) adds 20 `<p>` and 20 `<li>` before `</main>`. It reads the members in the browser before Apply by computed family, size, weight, line height, letter spacing and transform equal to body's, and asserts 44 members with 2 `.btn`. Expected values are the typed family and `22px`, with literal `16px` for `.btn`. It asserts: a role id, Apply enabled, request roles == `[('bootstrap5-body', ['body'])]`, the rendered status line, the whole Body line ending with the page-wide literal, member styles, and after Clear member styles, `main` markup and empty preview CSS.
- PASS: Early assertions, not hangs. Detect and receipt waits are bounded 15 s browser polls returning the text, so a hang becomes an assertion failure (reproduced: the RED runs below end at assertions in about 16 s).
- PASS: Budget. +55/-2 gross against about 90.
- PASS (recorded, not a deviation): the report states two REDs differ from the brief's guess (see concern 1).
- CANNOT VERIFY: Firefox/WebKit are not installed here, so the cross-engine run of the new test is unverified. CI runs the focused set on Chromium (`FKS_ENGINES: chromium`); Firefox is a separate canary job.

### Checks run
- Integrity -> `git diff --cached --stat | tail`; `git diff --binary | sha256sum` vs `sha256sum` of the patch; `git status --short` -> exact match (above).
- Clean green on a scratch copy of the frozen tree (tar without .git; PYTHONDONTWRITEBYTECODE=1; FKS_ENGINES=chromium) -> the new test alone: Ran 1, OK, 2.2 s.
- Mutant 1, bridge page binding removed (`bind(group, ['body'])` call deleted) -> FAIL `'Detected' not found in 'Detecting text styles...'`. Reproduced.
- Mutant 2, Studio's acceptance of `page` removed (`"page"` taken out of the allowed-reason list) -> same assertion. Reproduced.
- Mutant 3a, bridge `body` plain block dropped (`if (role.adapter !== 'bootstrap5-body')` guard on the plain `blocks.push`) -> FAIL at `'Preview applied to 1 role; 0 checked elements did not show it.' not found in 'No response to apply; ...'`. Reproduced. This is the report's status-assertion failure, not the family one.
- Mutant 3b, the same block written on `html` -> identical status failure. The Studio reply check rejects the receipt, because `canonicalCss` no longer matches what Studio computed.
- Mutant 4, Studio receipt wording reverted (`pageWide.has(...)` replaced by `false`) -> FAIL on the assertEqual of the outcome line (page-wide suffix missing). Reproduced.
- Mutant 5 (mine), preview `<style>` inserted first in `head` instead of appended -> FAIL at the member-style assertion: `[['sans-serif','16px'], ...] != [['Georgia, serif','16px'], ...]`. See concern 2.
- Concern 1, W2PS alone: bridge reversed with `git apply -R --include=fontkit-bridge.js task-w2p-code.patch` on the scratch copy -> FAIL `'Detected' not found in 'Detecting text styles...'`. Reproduced. It is not "no role id" as the brief said.
- BASE RED and W2P-alone RED were not reproduced by me. My attempt to reverse the W2PS Studio patches on the scratch copy did not apply cleanly (patch order), so I rely on the report for those. The report's explanation matches the observed W2PS-alone behaviour.
- `python -m ruff check tests/test_r2_integration.py` -> All checks passed. `git diff --cached --check` and `git diff --check` -> clean.
- Fixtures -> `fixtures/bootstrap5-static` is a vendored static page (vendor/bootstrap.min.css, app.css); no npm fixture is needed, so there are no hidden skips. The new test has no skip or conditional. It lives in test_r2_integration, run by shard-5 and the focused set.
- All scratch copies deleted; the frozen worktree untouched (hash re-verified). No browser or server left running.

### Strengths
- The oracle is independent of the code under test: members come from computed styles in the browser before Apply, with the count asserted at 44. A vacuous loop is impossible.
- The test is a true boundary test: the real Studio, the real bridge and the real Bootstrap 5 fixture, with no mocks. It covers Detect's `page` binding, Apply's `['body']` request, the page-wide receipt text and Clear.
- Every mutant I ran went red at an explicit assertion in 2-17 s. None passed green or hung.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_r2_integration.py (patch lines 28-32): `MEMBERS` and `STYLES` are class attributes wedged between two tests, rather than module constants or local strings. Pure placement; harmless.
2. The new test asserts the exact status string and the full outcome line, but not the preview CSS content while applied (only emptiness after Clear). The existing Bootstrap 5 test asserts the `:root` prefix, so the `:root` block is covered. The `body` plain block's content is guarded only through the Studio/bridge `canonicalCss` agreement and the member styles. Acceptable.
3. The existing test's docstring now carries a long line (patch line 10) with a parenthetical; ruff accepts it. Cosmetic.

### Judgement on the two concerns
- Concern 1 (W2PS alone gives "Detecting", not "no role id"): the recorded RED is honest and the brief's expectation is wrong. I reproduced it. The W2PS Studio validator (fontkit-studio.html ~3842-3846) returns false for a `bootstrap5-body` group lacking exactly one complete `body`/`page` binding. The old bridge's unbound Body group is therefore a dropped reply, not a row without an id. The test still fails at an explicit assertion, with no hang. Version skew with an old bridge is parked for PR C (Addendum 23). Only the BASE case (both patches reversed) reaches "no role id" per the report. Not a defect of the task.
- Concern 2 (dropped body plain block fails at the status, not the family assertion): the mutant is a true red but is caught earlier by the install/receipt check, so that mutant does not exercise the family assertion. The family/size assertion is not decorative: my mutant 5 (preview sheet placed before the app's own stylesheets, so `app.css` pins `body`'s family) reaches it and fails there with `sans-serif` versus `Georgia, serif`. Any realistic break that leaves Studio and bridge in agreement (cascade position, specificity, a wrong selector written by both sides) lands on that assertion. A wrong selector in the bridge alone is caught earlier by the `canonicalCss` check. The brief's expectation for mutant 3 was inaccurate; the report discloses that.

### Plan-mandated (for the owner)
- [Minor] The brief predicts mutant 3 ("the members keep it") fails at the family assertion, and says that BASE and W2PS-alone both give "no role id". Both predictions were wrong in practice (status failure; "Detecting"). The implementer recorded the observed behaviour. Brief lines: "the bridge's `body` plain block dropped (the fixture's `app.css` pins `body`'s family, so the members keep it)" and "at BASE and with W2PS alone the Body row gets no role id and no controls". No code change needed; correct the brief text if it is reused.

### Assessment
**Task quality:** Approved
**Reasoning:** The delta is intact (byte-identical to the staged state), small (+55/-2), and matches the brief's oracles. I reproduced the page-binding, Studio-acceptance, body-block and receipt-wording mutants, and a cascade-order mutant, all red at explicit assertions with files restored byte-exact. The two disclosed divergences from the brief are honest and correctly judged. Only Chromium was run; Firefox/WebKit were not available to me.
