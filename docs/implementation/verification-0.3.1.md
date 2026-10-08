# 0.3.1 release verification

Date: 2026-10-07. Branch: `fix/localhost-cookies`; base `7598ebb`.
Status: pre-merge implementation verified; readiness-record CI pending.
No tag or publication exists for this patch.
This evidence covers the settled 0.3.1 working tree following `6485edf`.
CI-only APT setup changed under Addenda 6-8 while app/browser-test source stayed
frozen; its focused review and hosted execution are recorded separately.

## Environment and preparation

Windows, Python 3.13.3, Node 24.16.0, npm 10.8.2. Playwright 1.62.0,
Ruff 0.16.10, pre-commit 4.6.2. Chromium and Firefox already installed.
All four fixtures installed before the package was bundled or browsers tested:

```powershell
npm ci --prefix fixtures/vite-react
npm ci --prefix fixtures/vite7-react
npm ci --prefix fixtures/vite-ts
npm ci --prefix fixtures/next-app
npm --prefix packages/fontkitstudio test
```

Preparation exits 0. Final settled package run: `tests 271`, `pass 269`,
`fail 0`, `skipped 2`. The two no-project cases skip because a package.json
above the temporary directory prevents that environment; not product failures.
No other Node skip or cancellation. Package dependencies stay empty.

## Release commands and results

The runner sets these values before discovery (module-specific PYTHONPATH
does not replace discovery):

```powershell
$env:PYTHONPATH = 'tests'
$env:FKS_ENGINES = 'chromium'
$env:FKS_REQUIRE_FIXTURES = '1'
$env:FKS_REQUIRE_PRECOMMIT = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
python -m unittest discover -s tests -p 'test_[a-r]*.py' -v
python -m unittest discover -s tests -p 'test_[s-z]*.py' -v
python scripts/dev/frontend_gate.py --engines chromium,firefox
$env:FKS_ENGINES = 'firefox'
python -m unittest firefox_canary -v
```

- Chromium A: `Ran 474 tests in 372.592s`, `OK`, exit 0, no skips.
  Includes the rendered localhost cookie cases, real Vite/Next fixtures,
  release/workflow checks and title assertions. The Next hydration diagnostic
  reports one 404 resource message; its assertions pass.
- Chromium B: `Ran 385 tests in 534.630s`, `OK`, exit 0, no skips.
  Combined Chromium: 859 tests, including test_support and all installed
  fixture paths; no Python skip in either half.
- Frontend gate: `SUMMARY OK: 30 of 30 planned runs finished. Blocking: 7 runs,
  7 passed, 0 failed, 0 skipped. Advisory: 23 runs, 0 ADVISORY lines.
  334 REPORT lines, 0 SKIP lines, 0 FAIL lines`, exit 0. Desktop Chromium
  blocks; other profiles/Firefox are advisory (D029). The reports describe
  touch targets below 44px; they are not failures or silently omitted findings.
- Firefox canary: `Ran 51 tests in 121.100s`, `OK`, exit 0, no skips,
  advisory under D037. Both cookie modes render all three values. Full Gecko
  suite not run.

Run once on settled app source; no repeated full browser runs for documentation
or CI setup changes. Focused independent review evidence is in
[C review](tasks/v031-task-C-review.md), with cookie/lifecycle evidence in
[A report](tasks/v031-task-A-report.md) and [A review](tasks/v031-task-A-review.md).

## Fast checks

Final settled commands:

```powershell
python scripts/verify.py --static-only
node --check fontkit-bridge.js
python -m ruff check .
python -m ruff check . --exclude .agents
python -m pre_commit run --all-files
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
git diff --check
```

Static passes 96 unique IDs, inline JavaScript syntax and all three
supplied-v0.1.1 provenance hashes, exit 0. Bridge syntax passes silently, exit 0.
Pre-commit's four file hooks pass; whitespace passes. Commit-message range:
`commit-message check: OK: 3 commits checked`; candidate release message also
passes --message-file. Static-only does not claim browser acceptance.
The exact Ruff command exits 1 with four known findings only in an
untracked owner-installed skill: F401 json/typing.Set/re and F841 exclude_dirs_str.
The product-tree alternate returns `All checks passed!`, exit 0; no tracked
lint policy or skill file changed. This exact local gate is not reported green.
All wrapper processes exited. Runtime/test diffs retain only the approved
changes; no additional fixture source modification remains.

## Pre-merge checkout and bundle bytes

These are current checkout/bundle SHA-256, **not release-tag hashes**. The bundle
matches source byte for byte. Future release assets must be extracted from the
annotated merge tag with core.autocrlf=false and verified after publication.

| File | Current SHA-256 |
|---|---|
| fontkit-studio.html and package dist copy | 1c42e7b516744512026f10d141a0ab868dbfffe4840f41a8b1f2f1621ae4d9d7 |
| fontkit-bridge.js and package dist copy | 61baed79e6341d1ca85a453d85fc1a4c5d7e9d590f92aaf93d1222e82976554b |

## CI and release boundary

The preceding cookie-fix head `6485edf`, run 37664612240, passed ten jobs and
timed out in Ubuntu APT setup on Node 22/26. Failed jobs alone were retried:
Node 26 passes 14 Chromium fixture tests with no skips; Node 22 again times out
before browser download/tests. Quality job Chromium 859 OK (12 fixture skips,
11 covered by matrix), Firefox 51 OK/no skips and frontend 30/30/no advisory failures
were read. This is not an all-green CI claim for that head.

Addendum 6/D055 apply the upstream bounded APT configuration. The hosted run
below tests that initial correction, including its advisory results.

Release head `6ada9b3`, run 37672052396, completes with 11 successful jobs and
one Ubuntu Node 22 fixture timeout. Its guardrail step prints all four intended
APT values. Pip finishes at 19:07:20Z; APT starts at 19:07:21Z, falls back from
Azure for InRelease metadata, then tries Azure again for Packages/Translation
indexes. Output stops at 19:07:42Z until cancellation at 19:22:26Z. No Chromium
download or fixture test begins on that runner. This is APT setup failure,
not evidence of a browser-CDN failure or a guardrail override by Playwright.
The pinned installer's apt-get calls supply no overriding APT options.

That run's completed Quality Gate is read: Chromium `Ran 859 tests in 588.799s`,
`OK (skipped=12)`; the skips need fixtures and the matrix covers 11. Firefox
canary `Ran 51 tests in 95.592s`, `OK`, no skips; both cookie modes pass.
Frontend: 30/30, seven blocking passes, 332 touch-target reports, zero advisory,
skip or failure lines. Linux Node 24 fixture tests pass 14 with no skips and
the Next.js fixture passes; all other package/fixture jobs pass.

Addenda 7/8 and D056/D057 refine setup: use the official archive in the existing
runner mirror list and separate pip, install-deps and browser downloads.
App/browser-test source remains identical to the settled release run. Fresh
static/provenance, bridge syntax, product lint, pre-commit, whitespace and
message-range checks pass (four commits); exact Ruff retains the same four
owner-skill findings. Independent scoped review is Approved: another 25 release
tests OK/no skips, exact YAML normalization and Bash branch/failure checks pass.
No full local browser rerun. Hosted effectiveness was pending at scoped review;
the following exact-head run establishes it.

The refinement is committed as `f7d23ba`; [run 37674885926](https://github.com/pterw/font-kit-studio/actions/runs/37674885926)
is successful on that exact SHA. All 12 jobs pass. The Node 22 action log shows
the effective four APT values and the 34-byte official-archive mirror list;
metadata and packages come from archive.ubuntu.com, with no Azure attempts.
System dependencies complete in 18s, Chromium downloads in 8s, then 14 fixture
tests pass (`10.471s`, no skips). Node 26 completes those phases in 59s and 11s,
then passes 14 fixture tests (`15.079s`, no skips). Mac/Windows fixtures, Next.js
and all five Node package jobs pass. Required installation errors are not suppressed.

Quality Gate logs read: Chromium `Ran 859 tests in 625.167s`, `OK (skipped=12)`;
the matrix covers 11 fixture skips. The omitted host-refusal browser test
(`test_one_command_messages.HostRefusalTest.test_a_server_opened_to_the_network_is_refused_in_one_line`)
passes in local release half A with fixtures installed; it does not run in the
CI matrix. No CI coverage is claimed for that case. Firefox canary `Ran 51 tests
in 103.433s`, `OK`, no skips, both cookie modes pass. Frontend: 30/30, seven
blocking passes, 332 touch-target reports and zero advisory/skip/failure lines.
Advisories and setup warnings were read. Setup-python@v5 and upload-artifact@v4
still emit Node 20 runtime notices; they are outside the checkout/setup-node scope.

The remaining readiness-record landing changes documentation only. It receives
fast checks and independent review, with no new local browser run. Read its
exact-head CI and advisories before taking PR #15 out of draft. Implementation
readiness is established by the run above; no release-tag hashes are claimed.

Owner merge, annotated v0.3.1 tag, npm-release approval, registry/provenance checks
and tag-derived release-asset hashes remain unperformed.
