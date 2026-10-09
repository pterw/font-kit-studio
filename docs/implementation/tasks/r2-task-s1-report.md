# R2.S1 code report - 2026-10-09

Code phase complete; source frozen for independent review. No implementation approval, commit, stage, push or root-source edit is claimed.
Writer checkout: C:/fks/r2studio, detached BASE 54e3163f38b9f800512580766ada1ce02e8fa0d4. Exactly three owned paths changed: fontkit-studio.html, tests/test_studio_roles.py, tests/test_r2_integration.py. Old r2bridge checkout remained untouched.
Patch: s1-code.patch (standard unified Git diff, including unstaged new files). Manifest: s1-manifest.json (canonical LF and raw SHA-256). Reverse `git apply --reverse --check` succeeds without applying anything.
Material: 728 additions + 2 deletions = 730 lines; zero vendor churn. Studio contributes 256/2; tests contribute 341 and 131 added lines. This report is kept compact to leave independent review/full-wave records within the controller's PR cap.

## Implemented boundary

Live App now has an accessible Detect text styles button, named live status, Light-DOM text only note and bounded text-only role rows. Rows show sample/count, normalized variants, stable/uncertain selectors, shared classes and separate near-duplicate flags.
Full author/style identity keys issue monotonic role-N IDs per current-origin lifetime; duplicate labels, changed scan IDs, reordered discovery and same-author variants do not remap them. The 128-ID limit is visible; an overflow does not reuse old IDs or silently store a partial collection.
Authenticated empty ready.roleState establishes document/version/URL. Missing capability or malformed role snapshot disables Detect with the binding unsupported notice. Session/load/reconnect invalidate pending observations; newer same-document role generations survive an older ready.
Detected replies require current authenticated source/origin/protocol/session, latest request, established document, nondecreasing versions and consistent URLs. Complete observations cannot contain null, exceed 10,000 elements/2,000 ms, substitute a URL without advancing generation, or claim mismatched captured/current identity.
Exact nested shapes, forbidden prototype keys, counts/sums, identity/signature consistency, selector grammar/native syntax/root exclusions, enums, references and UTF-8 reply/request limits are checked. Observed family strings follow producer normalization and whole-wire limits; Apply's 300-character family ceiling is not imposed on observations. Weight follows the producer's integer normalization.
Role responses/rejections stay outside the legacy mutation queue, revision, saved overrides, Changes/export ledger and Composer state. No Apply/Clear/property fields, stylesheet, persistence, route inventory or automatic replay was added.

## RED/GREEN history

Initial 2026-10-08 real cross-origin boundary RED: connected target rendered 16px, but no accessible Detect control (1 test, 1.111s, exit 1). First GREEN: 1 test/1.115s, two literal roles, unchanged author main DOM/style and zero live edits.
Older same-document ready RED: version 4 was reset to 0 and an older result settled the request (1 error/31.182s). Preserving the newer role identity yielded 5 tests/3.494s GREEN.
Complete elapsedMs 2001 RED: hostile receipt settled the pending request (1 error/4.322s). Bound enforcement yielded 10 tests/9.435s GREEN.
Qualified body root and real >300-character observed family RED: two missing validated/rendered snapshots (2 errors/7.851s); explicit final root-step rejection and producer-compatible family validation yielded 2 tests/1.730s GREEN. Legitimate body ancestor paths remain allowed.
Same-generation URL substitution RED (1 error/4.249s), followed by complete 10,001-element RED after the URL guard (1 error/4.237s), each arose from a hostile receipt settling the request. Both are rejected on the final source.
Harness-only failures are retained: the first nested-frame probe actually called postMessage from the target (3 tests/32.311s, 1 error); an actual child script fixed the premise (3/2.243s GREEN). Playwright's argument decoder later lost the __proto__ own key (13/14.185s, 1 error); JSON.parse now preserves literal wire keys, and JSON 1e400 supplies a real nonfinite probe (13/10.946s GREEN). These were not product RED claims.
First full focused run before final additions: 118 tests/141.785s, exit 0, no skips. Final focused run on frozen bytes: 120 tests/139.732s, exit 0, no skips. Fourteen owned tests are included; the remaining tests characterize existing import, dead-control and shared-harness behavior.

## Rendered evidence and mutations

Real Studio + real bridge use the existing read-only protocol fixture: Body/Author body and Text/Ordinary body each count one eligible parent; selectors are [data-design-role="Body"] and [data-design-id="ordinary.body"], with 16px/400/none/0em. No author DOM/style or Changes mutation follows Detect.
Actual initial 2,001-character route displays exactly `Role detection/preview unavailable: unsupported page URL.` and disables Detect. Real inspector keystrokes change 16 -> 27px; Reset restores 16px. Explicit Connect UI recovers on exact 2,000-character route, without replay. Public history mutation during a real pending scan supplies null current URL, empty rows and disabled unavailable status, never checked evidence.
Actual authored long family remains visible; native computed weight 450.5 is shown as the producer's 451. Peer cases cover wrong source/origin/session/version/document, superseded requests, stale generations, hostile credentials/foreign URLs, complete null, malformed shapes/variants/references/prototype keys, size limits, incomplete/rejected status, reordered namespaces/variants and collection limits.
HTTPS-prefix regex is installed before navigation, after a permanent earlier local CORS fulfillment fallback. Blank fetch canaries prove abort=2/fallback=0 and two blocked results. Initial connected app requests add no HTTPS font/telemetry load. No CSP bypass, browser download or second Playwright driver is used.
Enter/Space activation, retained button focus with visible outline, named status/list and literal rows pass at 1440x1000 and 390x1000. Status contrast is >=4.5:1; panel and document have no horizontal overflow. Screenshots s1-1440.png and s1-390.png were visually read; default theme only, not a full frontend gate.
Final foreground mutations: session trust (1 error/4.202s), latest-request guard (1 error/4.350s), older-ready generation guard (1 error/4.252s), author identity consistency (1 error/4.388s), text-only title (1 failure/1.183s, actual img inserted). Each native exit was 1; the first four prevent the required Current/Fresh/Validated rendered snapshot. All five restored the exact original UTF-8 bytes in finally, then final focused GREEN ran. Earlier five mutation logs are also retained.
Full outputs: s1-mutation-{trust,latest,generation,identity,text}-final.log; s1-focused-final.log; s1-static-final.log; s1-ruff-final.log; s1-whitespace-final.log. The earlier s1-focused.log uses PowerShell stderr formatting but its native unittest result was 118/OK/exit 0.

## Exact gates, cleanup and limits

Environment: PYTHONPATH=tests; FKS_ENGINES=chromium. Final command: `python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v` (120/139.732s/OK/exit 0).
`python scripts/verify.py --static-only`: exit 0; 101 unique IDs, executable inline JS syntax and all provenance hashes pass. `python -m ruff check tests/test_studio_roles.py tests/test_r2_integration.py`: exit 0. `git diff --check`: exit 0. New test files additionally have final LF and no trailing whitespace.
The surrounding final validation script exited 1 after those successful native gates because its extra whole-file whitespace assertion found unchanged BASE Studio line 3301 (current 3314, two spaces). Direct BASE/current comparison proves it pre-existed. Changed-line whitespace remains clean; no unrelated whitespace fix or repeated browser run followed.
Every owned context/canary closes via finally/addCleanup; shared runtimes exit with each finished unittest subprocess. Owned cases start no server/Vite/scratch fixture. Legacy focused tests manage their own server handles through existing teardown. No process-name kill, fixed sleep, rejected-call retry or retained mutation occurred.
Full Chromium halves, Node tests, frontend gate, Firefox canary and the first 5,000-element benchmark were not rerun here; the separate settled runner owns that evidence. No universal animation, whole-site, preview or future installed-state claim is made. S1 accepts the current producer's empty canonical role snapshot; later preview tasks extend it.
MCP project font-kit-studio-local was confirmed ready (2637 nodes/12760 edges, generation 2026-10-07T17:07:14Z). Parent inline-handler searches were complete but returned zero; this does not prove absence. Own coverage reported Studio/helpers metadata_changed, new tests missing/not_tracked and docs excluded. Current direct source plus rendered evidence is authoritative; no exhaustive graph claim.

## Self-review and product drafts

AP1-4: authenticated transport, pinned post origin, textContent and exact supported-origin URL checks. AP5-7: no saved-state adoption/capture or target interception added. AP8-10: ready/detected/rejected paths exercised, load/session invalidation retained, defaults unchanged. AP11-12: no protocol rename; binding contract drives both validators, qualified-root/observed-value siblings addressed without widening Apply. AP13-15: owned handles closed, omitted gates explicit, draft history describes product behavior only. Independent acceptance is still pending.
Draft CHANGELOG: `Live App can detect the connected page's rendered text styles and show read-only roles, samples, counts and selector stability, with honest incomplete and unsupported-page status.`
Draft ledger: `2026-10-09: R2.S1 adds explicit read-only detection inside Live App. Real connected-page RED became GREEN; latest authenticated generations, exact identities and unavailable-URL inspector/reset behavior are covered. Focused Chromium 120/139.732s/no skips plus static/Ruff/whitespace pass. Independent verdict and settled-wave evidence remain pending; binding Addenda 5/6 unchanged.`
Draft subject: `feat(studio): show detected text styles from the connected page`
Draft why-body: `Typography observations need an explicit, readable entry point in Studio. Show exact roles and binding limits only from authenticated current replies so stale or hostile results cannot replace the visible baseline. Keep the inspector usable when a route cannot supply valid role evidence.`

---

# R2.S1 select-all portability fix - 2026-10-09

Scoped correction complete and frozen for the same independent reviewer. Only C:/fks/r2studio/tests/test_r2_integration.py changed; detached HEAD remains 54e3163f38b9f800512580766ada1ce02e8fa0d4. The complete durable S1 review was read before editing.
Exactly two calls at lines 40/51 changed from Control+A to ControlOrMeta+A. UTF-8 byte replacement and its exact reversal prove no other byte changed; the file remains 131 lines. Delta against the frozen candidate is two added/two deleted lines, not a revised full BASE patch.
Basis: the review cites existing repository macOS select-all failures and the established portable alias. Existing Windows behavior is characterized GREEN; no manufactured RED or fresh macOS browser proof is claimed.
Current integration raw/canonical SHA-256: e1ceb66bf166283122c64c7384ff79fc1783952e453cac0218b762d3aa6e1987. All three source hashes, previous hashes and original artifact hashes are in s1-portability-manifest.json.
With PYTHONPATH=tests and FKS_ENGINES=chromium, `python -m unittest test_r2_integration.StudioRoleIntegrationTests.test_unavailable_actual_url_preserves_inspector_reset_and_supported_reconnect test_support -v` passed 35 tests in 17.831s, native exit 0, zero skips.
The affected real Studio/bridge case still edits 16 -> 27px, resets to 16px, preserves the unsupported-URL notice and explicitly reconnects at the exact supported route boundary. Shared support tests also pass.
`python -m ruff check tests/test_r2_integration.py`: native exit 0. `git diff --check`: native exit 0; its existing Studio line-ending warning is not a whitespace error. Full native command/output is preserved in s1-portability.log.
Studio and test_studio_roles.py remain byte-identical, including canonical hashes 2401ce67d9b5a39b62220e0a52caa0eee538af166d32d8f6ca16d90fa3de7fbe and 06d66ab8a3db47e4fa0a33ea028ba7f74fb36005d60726e67b2a37de8788284e. Original s1-code-report.md, s1-code.patch and s1-manifest.json remain byte-identical.
Owned canary/contexts close through existing finally/addCleanup; the completed unittest subprocess exits its shared browser/driver. No active owned invocation remains. Inherited support/server teardown completed normally; no new server, browser download, fixed sleep, process-name kill or source mutation was introduced.
The 120-test command, full halves, Node/frontend/Gecko and benchmark were not repeated. Scoped independent acceptance and the later dedicated wave remain pending. No root source/docs, old r2bridge, stage, commit, push or spawning operation occurred.
MCP status/coverage was refreshed: font-kit-studio-local ready 2637/12760, generation 2026-10-07T17:07:14Z; new modules not_tracked, Studio/support metadata_changed and review docs excluded. Current exact source/runtime supplies this scoped evidence; no exhaustive graph claim.

---

# S1 fullscreen correction - 2026-10-09

Scope: current root brief/Addendum 7/D062 and complete independent fullscreen diagnosis; writer C:/fks/r2studio, detached BASE 54e3163f38b9f800512580766ada1ce02e8fa0d4. Original S1/portability reports, patches and manifests remain unchanged.
Move only the seven-line Detected roles section after composer-shell, outside canvas-stage. Existing sibling-inert/Escape behavior covers it; IDs, text, CSS, JavaScript, protocol and legacy tests are unchanged.
One new real Studio/bridge test checks literal role-1/role-2 observations, status/row text, fluid/fixed geometry, reachable right edge, inert coverage, Escape, native Enter Detect and unchanged target DOM/page errors.
Genuine initial RED: connected detected rows collapsed fluid preview to 2 px (>500 required), 1/1.246 s/native 1 (s1-fullscreen-red.log). Existing independent 367.6875 px regression remains in pr-a-fullscreen-diagnosis-probe.log.
First GREEN: 1/1.306 s/native 0, fluid and fixed1440 both 518.0625 px, fixed scrollWidth1440/client878/right902/edge903/bottom543.0625 (s1-fullscreen-green.log).
Placement mutation: restored prior frozen HTML, height2 failure, 1/1.264 s/native 1; restored candidate raw SHA byte-identically (s1-fullscreen-mutation.log).
First focused outcome: 63/43.846 s/native 1, only RawMarkupGuard failed four new Studio innerHTML snapshots; all rendered/fullscreen checks passed. This was a test-quality failure, not product RED (s1-fullscreen-focused.log).
Corrected snapshots compare status/row text and public data-role-id, with literal IDs; no exemption or removed geometry/exit assertion. Before controller guidance arrived, repeated placement mutation also failed unchanged height assertion, 1/1.287 s/native 1 (s1-fullscreen-final-mutation.log); disclosed redundant run, bytes restored.
Final focused GREEN: 63/44.036 s, Chromium, zero skips/native 0, full output s1-fullscreen-final-focused.log. Read all results; unchanged width/fullscreen/first-run/Live App cases and RawMarkupGuard pass.
Exact command, cwd C:/fks/r2studio: PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_r2_integration test_studio_roles test_studio_stage.PreviewWidthTests test_studio_live.StudioFullscreenTests test_studio_first_run.FullscreenTests test_studio_visual.LiveAppViewTests test_support -v.
Fast checks: python -m ruff check tests/test_r2_integration.py tests/test_studio_roles.py; git diff --check: both native0, ordinary LF-to-CRLF warning only (s1-fullscreen-final-fast.log). Reverse delta apply --check native0; byte proof removes relocated block/new method and equals prior candidate exactly.
Inherited owned harness verifies blank fetch HTTPS canaries (abort2/fallback0) before real cross-origin load, retains permanent local fallback, closes contexts; no CSP bypass/font download/server launched. All invocations returned; focused runner PIDs46032/41528 reaped, mutation source restored, no owned runtime remains active.
Original desktop/narrow PNG bytes were restored after each focused run. Later screenshot-copy request arrived after final restoration; current relocated-panel PNGs were not retained. No extra browser run; scoped review/settled run must save its current screenshots under new names.
Delta s1-fullscreen.patch is AGAINST prior frozen S1/portability candidate (not BASE): 53 added/7 removed, 60 material lines, including one 46-line test; patch SHA and all three raw/canonical hashes in s1-fullscreen-manifest.json. Roles test remains byte-identical; no staging, commits, push, root source edits or denied calls.
Tier2 graph ready2637/12760, generation2026-10-07T17:07:14Z; relevant coverage metadata-changed/new tests untracked/docs excluded, no recorded ranges. Current source/runtime is authoritative; no new inline-JavaScript graph completeness claim.
AP self-review: trust/state/rendering code untouched; observations persist through inert/exit; native keyboard access returns; genuine rendered mutation, no fixed sleeps/threshold changes/shared-helper bypass. Source and outputs frozen pending scoped independent review.
Not run: full Chromium wave, Node/frontend gates, Firefox; dedicated settled runner follows approval. Screenshot gap above remains explicit; no new acceptance or release completion claimed.
Draft CHANGELOG: Keep detected role observations available after leaving fullscreen without reducing the Live App preview height.
Draft commit: fix(studio): preserve fullscreen preview height with detected roles. Why: Role observations shared the fixed-height preview column and consumed its available space; place them below the preview and inspector while retaining observations after Escape.
Draft ledger: Addendum7/D062 markup relocation plus real-boundary regression; initial rendered RED, test-quality failure and corrected 63-test GREEN preserved; scoped independent review and fresh frozen gates remain pending.
