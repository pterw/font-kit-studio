# R2.S1 independent implementation review

Date: 2026-10-09. Verdict: **Approved with fixes**.
Only the Minor test portability correction below remains before landing.
No Critical or Important product finding was identified.

## Scope and frozen source

Reviewed the complete S1 context, durable brief, 52-line report, three-file
diff/current new tests, binding protocol/R2.S1, Addenda 5/6, constraints,
AGENTS/global rules and requesting-code-review instructions. Current ledger and
history agree: R2.1/R2.2 are committed; S1 is in flight and remains unchecked.
BASE/HEAD: `54e3163f38b9f800512580766ada1ce02e8fa0d4`, feat/r2-detection.
The completed detector verdict was not changed.

Independent manifest checks before/after verification confirm frozen raw and
canonical bytes. Studio canonical SHA-256:
`2401ce67d9b5a39b62220e0a52caa0eee538af166d32d8f6ca16d90fa3de7fbe`;
raw SHA-256:
`a06fe2aeef6498ef02e3c461d2d7b39e813c3ed05479dd63c9fb3b2a49ccd73e`.
Role tests raw/canonical:
`06d66ab8a3db47e4fa0a33ea028ba7f74fb36005d60726e67b2a37de8788284e`.
Integration tests raw/canonical:
`46cbea9acc0c6034af9df0d7466f8ac8631edd0e12a1f66dccbf79ff02365c5a`.

Fresh Tier 2 MCP status/coverage: font-kit-studio-local, ready, generation
2026-10-07T17:07:14Z, 2,637 nodes/12,760 edges. Existing source/helper metadata
changed; new modules are not tracked and fixtures/docs are excluded. No recorded
parse ranges does not prove completeness. Inline role functions are not supplied
by the old graph; complete current diff/source and runtime checks are authority.

## Minor: use the portable select-all alias

**tests/test_r2_integration.py:40 and :51** press `Control+A` before typing.
The repository already corrected this pattern to `ControlOrMeta+A` after actual
macOS fixture failures: Ctrl+A moved the caret rather than selecting all, causing
digits to append. These two new calls reintroduce that known portability issue.
Use `ControlOrMeta+A` in both owned calls; there are no additional select-all
siblings in these two new modules. This is a source/history-supported finding,
not a fresh macOS browser reproduction. Windows acceptance passes unchanged.
Return the test-only correction to the same writer and reviewer before landing.

## Implementation assessment

Studio adds only Detect and read-only rows. Full author/style keys keep separate
namespaces, duplicate labels, variants and stable monotonic bounded role IDs.
Authenticated ready establishes identity; only latest matching current replies
can replace rows. Source/origin/session/protocol checks remain at the transport
boundary. Exact shapes, UTF-8 limits, duplicate identities/IDs, count sums,
references, selector syntax/root exclusions, version/URL equality and complete
time/element bounds are validated. Observations retain producer normalization
without applying future Apply property ceilings to measured family/size/tracking.

Rows use textContent and preserve button focus. Unsupported/null URLs show D061's
exact notice while inspector/reset/reconnect remain usable. Incomplete results
do not claim checked evidence. Role responses do not settle the legacy queue,
alter Changes/export, replay edits, write persistence or install a stylesheet.
No Apply/Clear controls, route inventory or future installed-state claim appears.

## Independent verification

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'
python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v
```

**120 tests in 140.349s, OK, native exit 0, zero skips, Chromium only.** Full
output read; fourteen owned cases plus existing import/control/support coverage.
Real boundary checks render the two literal Body/Text roles, 16px/400/none/0em,
author-role/ID bindings and unchanged author DOM/Changes. Real 2,001/2,000 route
cases preserve inspector typing 16->27px, reset16px and explicit reconnect;
pending valid-to-unsupported detection clears rows and disables Detect.
Hostile/stale/unknown-document/old-ready/latest-request, exact shape/UTF-8/count/
identity/variant/reference, markup, capability and collection cases all pass.

Keyboard Enter/Space, retained focus/outline, named status/list, >=4.5:1 status
contrast and no panel/document horizontal overflow pass at 1440 and 390 widths.
Both newly generated `s1-1440.png`/`s1-390.png` were visually inspected: readable
rows, wrapped selectors and visible focus. This is default-theme evidence.

Additional fixed inline public probes, native exit 0, 2.266s, fresh contexts:
real Studio/bridge at 1440 and 390 display actual computed 450px/1350px tracking
as 450px/3em observations, retain keyboard focus/no overflow/Changes0 and author
DOM. Author removal of the ordinary paragraph gives a real zero-match prior
binding and fresh one-role result retaining role-1. Supplemental authored peer
rejects fractional weight, duplicate full identity and qualified body.root;
the same pending request then renders a valid body > p binding. No private
validator hooks, fake bridge used for real-boundary acceptance or source edits.

Fast gates: static101 IDs/inline JS/provenance, `node --check fontkit-bridge.js`,
owned-module Ruff, product Ruff excluding .agents, working/staged whitespace and
`check_commit_messages.py --range origin/main..HEAD` (five commits) all exit 0.
Exact `python -m ruff check .` exits 1 only for the four preserved owner skill
scan.py findings at :21 json/:23 Set/:24 re/:294 exclude_dirs_str. No fixes.

Writer's five final rendered guard mutations each exit 1 and exact restoration
are reported evidence, not independent mutation reruns. The extra writer
whole-file whitespace assertion failed after successful native gates on unchanged
BASE content; current changed-line checks pass. No claimed product RED from
the disclosed harness/escaping mistakes or that surrounding-script exit.

## Limits and cleanup

HTTPS guards/canaries run before navigation with permanent earlier local fallback;
owned cases show two aborts, zero fallback hits and no unrequested external load.
All reviewer browser contexts/canaries/shared browser/driver close normally;
the inherited legacy focused cases own their server teardown. No new server,
source/index/branch/HEAD change, denied-call retry, deletion, commit or push.
Only this review file was authored. The source stayed frozen through all checks.

Full halves, Node package, frontend gate, Firefox canary and first 5,000 benchmark
were not run here; dedicated settled-wave evidence remains pending under Addendum
6. Prior-head CI is historical and does not accept this Studio change. No macOS,
Firefox, dark-theme/full-frontend or universal rendering-tracking claim. After
the two key-alias corrections, affected real cases plus support/fast checks are
sufficient for scoped re-review; another identical 120-test run is not required.

## Scoped portability re-review (2026-10-09)

**Current verdict: Approved.** The initial verdict above is preserved; its only
Minor finding is resolved. Read the complete durable correction and scratch
report/manifest/native log. Independent raw-byte reversal proves exactly two
Control+A -> ControlOrMeta+A replacements at integration-test :40/:51, with no
other byte change or select-all sibling. Studio and role tests remain byte-identical
to the initially reviewed candidate, and all original scratch artifacts retain
their hashes. Integration raw/canonical SHA-256 is now
`e1ceb66bf166283122c64c7384ff79fc1783952e453cac0218b762d3aa6e1987`.
All three current manifest hashes match again after verification; HEAD unchanged.

Independent command, PYTHONPATH=tests and FKS_ENGINES=chromium:

```powershell
python -m unittest test_r2_integration.StudioRoleIntegrationTests.test_unavailable_actual_url_preserves_inspector_reset_and_supported_reconnect test_support -v
```

**35 tests in 23.180s, OK, native exit 0, zero skips; full output read.** The real
case preserves unsupported-URL status, native 16->27px typing, reset to16px and
explicit reconnect at the exact 2,000-character supported boundary. Scoped Ruff
and working/staged whitespace exit0. Writer's full log separately records
35/17.831s/exit0; it is reported evidence, not the independent measurement.
Fresh graph status/coverage retains the same generation and disclosed limitations;
direct byte/source/runtime evidence decides this correction.

The completed subprocess closed contexts/canary/shared browser/driver normally.
Only this review was appended; no source/index/HEAD/branch mutation or extra server.
No new finding or macOS runtime claim. Original120 checks, full halves, Node,
frontend, Firefox, benchmark and guard mutations were not repeated; unchanged
runtime retains the initial review evidence and the dedicated wave remains pending.

## Scoped fullscreen correction review (2026-10-09)

**Approved under Addendum 7/D062.** Read the complete amended brief/report,
two-path delta/manifest, genuine height RED, both restored placement mutations,
disclosed RawMarkupGuard failure and corrected writer's 63-test output. Current source
matches the manifest. Independent line-preserving reverse proof restores the
prior raw Studio hash; removing only the 46-line test restores prior integration.
Only those two files differ from the old 182-file freeze; CSS/JS/bridge/legacy tests
and the roles test remain unchanged. Studio canonical SHA is
`87fe35975258316de00cc6f4fc515333856804ee0918828e410eaf781ae9f702`;
integration SHA `ba34af973692818cb682372e4b8b34ceba493b9d1844d4752fffbbbad4ea7d9d`.

Independent Chromium command, PYTHONPATH=tests:

```powershell
python -m unittest test_r2_integration test_studio_roles test_studio_stage.PreviewWidthTests test_studio_live.StudioFullscreenTests test_studio_first_run.FullscreenTests test_studio_visual.LiveAppViewTests test_support -v
```

**63/44.302s/OK/native0/zero skips**, complete focused log read at
`.superpowers/sdd/r2/s1-fullscreen-review-focused.log`. Both real fullscreen
widths retain 518.0625px height; fixed1440/client878/right902/edge903/bottom543.0625.
Covered roles are inert, Escape preserves text/IDs and returns keyboard access.
Separate guarded real post-exit Enter renders newly authored 23px tuples, retains
author role-1/focus, Changes 0 and no errors (native0; s1-fullscreen-review-native.log).
Saved/viewed `s1-fullscreen-review-{1440,390}.png`; original PNG bytes restored
in finally. Static 101/provenance, bridge syntax, scoped Ruff and whitespace pass.
Current source bytes remain exact; contexts/canaries/shared runtimes close.
Fresh graph coverage retains disclosed stale/untracked/excluded limitations.
No new finding, source/index edit or fresh macOS/Gecko/full-wave claim. Original
120/72, full halves, Node/frontend/Firefox and benchmark were not repeated;
fresh dedicated settled gates and final PR review remain required.
