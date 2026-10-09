# R2 PR A settled-wave verification

Current gates: fresh corrected wave below passes; original stopped wave retained.

Date: 2026-10-09. Status: stopped; blocking Chromium failure, wave incomplete.
Branch: `feat/r2-detection`. HEAD: `54e3163f38b9f800512580766ada1ce02e8fa0d4`.
Scope: committed detector plus independently accepted, uncommitted S1 source.
The gates below ran sequentially once. No rerun or source fix was attempted.

## Frozen source and environment

The controller's [182-path manifest](../../.superpowers/sdd/r2/pr-a-frozen-source.json)
was not overwritten. Every raw and canonical-LF SHA-256 matched before and after
the stopped wave; branch/HEAD also matched. Only Studio and the two new S1 test
modules were dirty/untracked product source. Controller documentation was allowed
to change. [Before](../../.superpowers/sdd/r2/pr-a-wave-before-source.json) and
[after](../../.superpowers/sdd/r2/pr-a-wave-after-source.json) retain every hash.

| Critical file | Canonical-LF SHA-256 |
|---|---|
| fontkit-studio.html | 2401ce67d9b5a39b62220e0a52caa0eee538af166d32d8f6ca16d90fa3de7fbe |
| fontkit-bridge.js | 08fcdf50f350a9bbfd6fadbc5e7a9cedd637bccdf47cac76070f5580eac8896e |
| tests/test_studio_roles.py | 06d66ab8a3db47e4fa0a33ea028ba7f74fb36005d60726e67b2a37de8788284e |
| tests/test_r2_integration.py | e1ceb66bf166283122c64c7384ff79fc1783952e453cac0218b762d3aa6e1987 |

Preflight independently checked every direct installed dependency's package.json
for vite-react (Vite 8.3.2), vite7-react (7.3.6), vite-ts (8.3.2), next-app
(Next 16.3.8) and vite-react-css-modules (Vite 8.3.2). All were installed.
Playwright 1.62.0 matches requirements; Chromium and Firefox executable paths
exist. No dependency/browser installation or download ran. Full installed
versions and browser paths: [preflight](../../.superpowers/sdd/r2/pr-a-wave-preflight.json).

Each native gate received `PYTHONPATH=tests`, `FKS_REQUIRE_FIXTURES=1`,
`NEXT_TELEMETRY_DISABLED=1` and explicit `FKS_ENGINES=chromium`. Subprocess-local
environment values did not alter the shell environment. Full stdout/stderr and
native exits are retained by [runner](../../.superpowers/sdd/r2/pr-a-wave-run.py).

## Executed gates

Scratch prefix for every log and native receipt: `.superpowers/sdd/r2/pr-a-wave-`.
Each table key names `<key>.log` and `<key>-result.json` under that prefix.

| Key | Exact command | Native exit | Result |
|---|---|---:|---|
| static | `python scripts/verify.py --static-only` | 0 | 101 IDs; inline JS and all provenance pass; browser suite explicitly not run by this command |
| bridge-syntax | `node --check fontkit-bridge.js` | 0 | Pass |
| ruff-product | `python -m ruff check . --exclude .agents` | 0 | All checks passed |
| ruff-exact | `python -m ruff check .` | 1 | Four preserved owner-skill findings; exact gate fails |
| whitespace-working | `git diff --check` | 0 | Pass; normal LF-to-CRLF checkout warnings disclosed |
| whitespace-index | `git diff --cached --check` | 0 | Pass |
| messages-range | `python scripts/dev/check_commit_messages.py --range origin/main..HEAD` | 0 | Five commits checked |
| messages-candidate | `python scripts/dev/check_commit_messages.py --message-file .superpowers/sdd/r2/s1-commit-message.txt` | 0 | Actual candidate passes |
| suite-a | `python -m unittest discover -s tests -p 'test_[a-r]*.py' -v` | 0 | 529 Chromium tests, 513.787 s, OK, zero skips |
| suite-b | `python -m unittest discover -s tests -p 'test_[s-z]*.py' -v` | 1 | 394 Chromium tests, 517.645 s, one failure, zero errors/skips |

Exact Ruff findings are in the preserved untracked skill's scripts/scan.py:
unused json (21), typing.Set (23), re (24), and exclude_dirs_str (294).
No .agents file or lint policy was changed; product Ruff does not erase this
exact-gate limitation. Native wrapper elapsed times were 514.482 s and 518.118 s
for suite A/B respectively; unittest times above exclude launcher overhead.

The first complete 5,000-element detector benchmark in suite A reports 315.8 ms,
complete:true, heartbeat 96 to 100, inputDuring:"x", replyAlreadyArrived:false.
Traversal/bindings/serialization are included by the test. It meets the unchanged
2,000 ms limit, with native input rendered before reply; no warm-up retry ran.
All FIRST_SCAN and LATE_FOCUS diagnostics remain in the original suite A log.

## Blocking failure and unrun gates

`test_studio_stage.PreviewWidthTests.test_a_wide_preview_in_fullscreen_still_fills_the_height_and_scrolls`
fails its Chromium subtest at `tests/test_studio_stage.py:104`:
`assertGreater(fluid['container']['bottom'] - fluid['container']['top'], 500)`.
Observed height: **367.6875 px**; message: `fluid fills the layer too`.
The complete traceback is retained in suite B's log. Root cause and repeatability
are not established by this one outcome; it is not relabelled a flake.
The running unittest command finished its remaining cases/cleanup before stopping
the wave. No test/assertion, timing threshold or frozen source was changed.

Not run after the blocking failure:

- `npm.cmd --prefix packages/fontkitstudio test`: full Node/build/exclusion gate.
- `python scripts/dev/frontend_gate.py --engines chromium,firefox`: planned 30
  runs, seven blocking desktop Chromium checks and all advisory/touch reporting.
- `FKS_ENGINES=firefox python -m unittest firefox_canary -v`: advisory canary only.

There is no new frontend advisory/REPORT grouping or Firefox acceptance from this
wave because those commands did not run. Previous focused/CI results do not fill
these gaps. No full Gecko suite, repeated focused gate or benchmark-only run ran.

## Cleanup, limits and next action

All launched native gate processes were waited/reaped; none of their recorded
PIDs or direct children remained in the final [cleanup check](../../.superpowers/sdd/r2/pr-a-wave-cleanup.json).
Tests manage their contexts/servers; no exhaustive deep-descendant claim is made.
No manual server was started or process killed. Frozen bytes remained unchanged.
Preflight native exit was 0, but driver disposal emitted a pending-task and
TargetClosedError warning after executable-path inspection, without launching a
browser. Its exact text is preserved in [disposal log](../../.superpowers/sdd/r2/pr-a-wave-preflight-disposal.log);
it is disclosed rather than hidden by rerunning preflight.

Current manifest hashes and native/runtime output decide this verification; no
graph completeness or new structural claim is made. The initial nonexistent
preparation-review filename was corrected to the existing brief-review record;
there was no denied call or fallback around a denied action. No product source edits,
staging, commits, pushes, spawning, installs or publication occurred.
Next: controller reads this complete record and material logs, then assigns the
fullscreen failure investigation. Remaining gates require a justified continuation
against frozen source. This wave does not accept PR A or claim release/publication.

## Fresh corrected wave (2026-10-09)

Status: all blocking product gates pass; advisories read. Final PR review remains
separate. HEAD/branch remain the exact values above, with accepted D062/S1 source.
The new `pr-a-fullscreen-frozen-source.json` retains all 182 raw/canonical hashes;
`pr-a-finish-before-source.json` and `pr-a-finish-after-source.json` both match.
The original stopped wave, manifest and native logs are preserved unchanged.

| Changed/current source | Canonical-LF SHA-256 |
|---|---|
| fontkit-studio.html | 87fe35975258316de00cc6f4fc515333856804ee0918828e410eaf781ae9f702 |
| tests/test_r2_integration.py | ba34af973692818cb682372e4b8b34ceba493b9d1844d4752fffbbbad4ea7d9d |

Bridge and roles-test hashes remain the original values above. Preflight again
verifies all five installed fixtures and pinned Playwright 1.62.0/Chromium/Firefox.
No acquisition, driver launch or new disposal warning occurs during preflight.

Commands retain the exact forms above; the Node wrapper runs
`npm.cmd --prefix packages/fontkitstudio test`. Chromium uses PYTHONPATH=tests,
FKS_ENGINES=chromium, FKS_REQUIRE_FIXTURES=1 and NEXT_TELEMETRY_DISABLED=1;
Firefox changes only FKS_ENGINES to firefox. Phases run sequentially once.

| Gate | Native exit | Current result |
|---|---|---|
| Static/provenance | 0 | 101 IDs, inline JS and all three provenance blobs pass |
| Bridge syntax; product Ruff | 0 each | Pass |
| Exact Ruff | 1 | Same four preserved owner-skill findings; not passing |
| Working/index whitespace; range/candidate message | 0 each | Pass; range checks five commits |
| Chromium half A | 0 | 530 tests / 509.255 s, zero skips |
| Chromium half B | 0 | 394 tests / 526.954 s, zero skips |
| Node package | 0 | 271 total: 269 pass, two environmental skips / 10.396 s |
| Frontend Chromium/Firefox | 0 | 30/30; seven blocking pass; 23 advisory, no failures/skips |
| Firefox canary only | 0 | 51 tests / 115.568 s, zero skips; advisory under D037 |

The first complete 5,000-parent scan takes 284.4 ms, heartbeat 111 -> 115,
input x before reply. Native eligibility/hover/activation/release cases reject
pending stale evidence. Keydown and style-focus cases finish before their native
events and legitimately retain pre-event evidence; no blanket pending-proof claim.
Both populated-role fullscreen widths retain 518.0625 px; the unchanged original
failing fullscreen test passes. Next's existing non-hydration 404 is reported.
Node's two skips are no-package.json guards: a package exists above this machine's
temporary directory. They are not missing fixture or production-build coverage.
All 338 touch REPORT lines are read through the lossless 85-target register;
compact Detect is 131x34 in four touch profiles. These are D029 advisories.

Complete native receipts/stdout use `.superpowers/sdd/r2/pr-a-finish-*-result.json`
and matching `.log` paths. Frontend non-REPORT output and every original line are
retained in `pr-a-finish-frontend-summary.txt`; the lossless compact register is
`pr-a-finish-touch-groups.txt`. No failing run is hidden or rerun until passing.
All gates exit normally; native PIDs 60504/58240/45092/43668/56748 are absent on
post-wave inspection. Harness contexts/runtimes and owned servers close normally;
no exhaustive unrelated-process claim. Root source/HEAD/branch remain unchanged.
No full Gecko suite, npm publication, release/tag or future-source acceptance.
