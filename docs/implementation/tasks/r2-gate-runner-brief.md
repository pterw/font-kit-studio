# R2 PR A gate runner brief

Preparation only. Execution requires R2.1/R2.2 committed and S1 implementation
independently accepted, with integrated product source frozen in root. Controller
supplies expected HEAD, exact dirty source paths and canonical hashes at dispatch.
Read AGENTS.md, global rules, plan Addenda 3/5/6, execution constraints and this
brief in full. Never read the whole ledger; Current state/latest R2 events only.

## Ownership and safety

Own only docs/implementation/verification-r2-pr-a.md and named ignored gate logs
under .superpowers/sdd/r2/. No source/test/doc edits beyond that evidence record,
no staging/commit/push/spawn. You are not alone; never revert another writer.
Run in the root landing tree once controller declares source frozen. Verify
branch/HEAD/status and expected source hashes before and after the wave; unexpected
source changes invalidate evidence and return to controller. Preserve owner dirs.

Use existing pinned Playwright/browsers; do not download browsers or change APT,
pip, requirements, workflows or fixture dependencies. Verify all five required
fixture installations first (vite-react, vite7-react, vite-ts, next-app and
vite-react-css-modules). If any is missing, report blocked before suite; do not
claim acceptance through skips. Controller handles necessary setup separately.
Node package test rebundles ignored dist; other tests may create/remove their
owned scratch fixture copies. No tracked output may change. Stop only owned
processes by PID/handle and report denied cleanup; never retry through another tool.

## Gates and schedule

Run fast gates then full Chromium halves, Node package, frontend gate and Firefox
canary sequentially. Do not compete with another browser gate process. All exact
commands are in constraints.md; use FKS_REQUIRE_FIXTURES=1 for Chromium suites.
Set FKS_ENGINES explicitly per command and restore environment as needed.
The already completed task-focused checks are not repeated without a new failure,
source change or unresolved concern. Full Gecko suite is forbidden; canary only.

- Static/provenance, bridge syntax, product Ruff and whitespace must pass.
- Run exact Ruff separately; record the known four owner-skill findings. Do not
  alter .agents/ or call this exact gate passing while those findings remain.
- Run commit-message range plus the actual candidate message file supplied by
  controller. Current uncommitted product/evidence is expected, not an excuse to
  skip checks. No signatures or --no-verify.
- Run both specified Chromium suite halves once; record every failure/error/skip,
  count, time and native exit. A suspected integrated flake may receive exactly
  one identical rerun under constraints; retain both outcomes. Other failures
  return to controller/same implementer; no test/source edits by runner.
- Run npm.cmd --prefix packages/fontkitstudio test; record build/test totals and
  production exclusion. Do not publish/install arbitrary packages.
- Run frontend gate for chromium,firefox: desktop Chromium blocks. Read/report
  all advisory engine/profile findings, SKIPs and touch REPORT lines; use grouped
  scratch evidence without omissions for controller reading.
- Run firefox_canary only, advisory under D037; unavailable engine is explicitly
  not verified. A nonzero advisory result is reported, never silently omitted.

Use foreground long-running commands and wait on their process/session, not
sleep/status polling loops. Send concise progress at least each minute. Keep
ordinary full stdout/stderr logs and exact native exits in named scratch files.
No retries until pass, threshold increases, assertions removed or warm-cache-only
benchmark acceptance. The full suite's first complete detector benchmark remains
part of the evidence; quote its elapsed time and heartbeat/native-input result.

## Evidence and return

Write an ISO-dated verification record with bound branch/HEAD/source hashes,
commands, native exit codes, counts/times/engines, all skips and failures/advisories,
known exact-Ruff limitation, fixture status, source stability and process cleanup.
Label unrun gates honestly. Tests/gates are evidence for this exact frozen source,
not future commits or release publication. Do not mark plan tasks or release done.
Return the FULL report, log paths, a compact lossless gate summary and any blocker.
Controller reads it and material output before committing/pushing. No npm/tag/merge.
