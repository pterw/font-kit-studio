# 0.3.1 Task C independent review

Date: 2026-10-07. Verdict: **Approved**.
Branch: `fix/localhost-cookies`. HEAD: `6485edf2eb19f02ab1bea8eaffd1c30b340ae41f`.
Scope: final branch from `7598ebb`, with focused independent review of the
uncommitted C changes against `6485edf`. Approval covers the submitted source;
settled-source gates, commit, exact-head CI and publication remain pending.

## Spec review

Read AGENTS.md and global-rules.md in full, C brief/report, the binding plan
and Addenda 1-5, relevant deviations, A/B reports and independent reviews,
ledger Current state and the 0.3.1 events. Read the C source/test/doc diffs,
full forwarding stub, package metadata/README and version tests, and relevant
repository README and test-harness source. The earlier A/B approvals were
considered as bounded prior evidence; their full runtime probes were not repeated.

- `fontkit-studio.html:6,996`, `fontkit-bridge.js:3`,
  `packages/fontkitstudio/package.json:3` and
  `fixtures/vite-ts/package-lock.json:16` agree on 0.3.1. Browser assertions
  and public CLI version output match. Bridge protocol 1 and export format
  0.1.1 remain unchanged.
- `CHANGELOG.md:15` dates 0.3.1 and records localhost cookies, the settings
  transition limited to localhost users of `--studio-port`, and Vite restart
  behavior. Compare links at lines 261-262 are correct. The real release-note
  extractor returns this section without trailing link definitions.
- Both READMEs correctly state localhost/IP host selection, retained IPv6
  mismatch, unchanged Set-Cookie forwarding, random proxy-origin storage,
  unavailable sync, settings origins and opening the latest restart URL.
  These claims match the binding contract and A's real-browser/lifecycle evidence.
- `font_kit_studio_v0.1.1.html:6,9` retains query/hash forwarding and names R2
  as the removal point. README, roadmap and rename-test wording agree with D052.
  The unchanged forwarder behavior passes fresh Chromium tests.
- Addendum 5/D054 authorizes only the sibling refusal-text correction.
  No acceptance rule, listener logic or protocol behavior changed in C.

## Quality, security and findings

- Critical: none.
- Important: none.
- Minor: none unresolved.

The sweep's minor finding was confirmed: `packages/fontkitstudio/src/proxy.js:53`
omitted `[::1]` from its explanation although the existing allow-list accepted
that target. The controller corrected the single error string and all six
assertion copies under Addendum 5. Scoped re-review confirms one literal source
change and assertion-only test changes; Host/Origin checks and target validation
are intact. All 20 independently selected refusal/security tests pass.

Anti-pattern review: C adds no DOM sink, unvalidated URL assignment, wildcard
origin/bind, message handler, source write, state overwrite, personal default,
runtime dependency or fixed sleep. Historical release entries and supplied
provenance are preserved. The related host-message copies were fixed together
(AP12); unrun verification is disclosed (AP14). No process/model/signature
wording was introduced into product labels or release notes (AP15).

## Fresh independent verification

Every command below exited 0 on the working tree. No source was changed during
the initial probes; after the authorized wording correction, only its scoped
Node checks and final whitespace check were repeated.

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'
python -m unittest test_studio_visual.VersionLabelTests test_studio_rename test_font_kit_studio_v011.StructureTests test_release -v
node --test packages/fontkitstudio/test/versions.test.js
python scripts/dev/release_notes.py 0.3.1
node packages/fontkitstudio/bin/fontkitstudio.js --version
node --test --test-name-pattern='refus|not local|remote address|parseProxyTarget' packages/fontkitstudio/test/proxy.test.js packages/fontkitstudio/test/run-proxy.test.js packages/fontkitstudio/test/cli.test.js
git diff --check
```

- Python: 32 tests, OK, zero skips, 6.474 seconds; relevant browser assertions
  ran in Chromium using the existing shared support. The title/eyebrow and
  both forwarding paths were exercised. Release parser/workflow tests are
  non-browser checks. No manufactured RED or new test was added.
- Node versions: 3 pass, zero failures/skips.
- Node scoped refusals/security: 20 pass, zero failures/skips. Includes wrong
  Host/origin, non-local/HTTPS/malformed targets, refusal before startup,
  missing-dist refusal and WebSocket trust boundaries.
- Actual release-note extraction returns the dated 0.3.1 notes. CLI prints
  `0.3.1`. Final whitespace check passes; Git emits normal autocrlf warnings.

Only this review file was written. Existing tests own and close their browser
contexts/server handles/processes. No independent Playwright driver, browser
download, source/fixture mutation, commit, push, tag or registry write occurred.

## Evidence limits and handoff

Live MCP list_projects/index_status and path coverage confirm Tier 2 project
`font-kit-studio-local`, generation `2026-10-07T17:07:14Z`. Test discovery found
the version/forwarder symbols with complete relevant pagination. Source metadata
is changed; docs/fixtures/CHANGELOG and Node test files are deliberately excluded.
Direct current diffs, source reads and fresh tests supply the material evidence;
no complete graph verification is claimed.

Full Chromium halves, full Node package, frontend gate, Firefox canary,
test_support, static/provenance, bridge syntax, Ruff and commit-message gates
were **not run by this reviewer**. The gate runner/controller owns that single
settled-source release run. The recorded four Ruff findings in owner-installed
untracked `.agents` were not independently rerun or fixed here. The review does
not convert earlier gate results into current release evidence.

The source is Approved for the remaining release checks and landing after
accepted full gate evidence. This is not release readiness, CI approval or a
publication claim. Owner merge/tag/publication and post-publication checks remain
separate, as the plan requires.

## Addendum 6 scoped re-review: Ubuntu dependency acquisition

Date: 2026-10-07. Scoped verdict: **Approved**. No Critical, Important or
Minor finding. The prior source verdict remains Approved; hosted CI is pending.

Read the new composite action in full, the complete workflow delta against
`6485edf`, Addendum 6, D055 and updated C brief/report. The source/browser-test
tree is unchanged by this addition. This review writes only its own record and
does not interrupt or repeat the active settled-source browser gates.

The retry logs confirm the infrastructure diagnosis: Node 22 is canceled while
APT metadata acquisition logs ignored Azure-mirror requests, with no fixture
test step. The Node 26 retry reaches 14 fixture tests, including both cookie
tests. This describes the prior head's logs, not effectiveness of the new action.

`.github/actions/configure-browser-apt/action.yml:6-18` is one Linux-only bash
step. On macOS/Windows its runner.os condition is false, so the apt shell does
not execute. The static action has no inputs, interpolation, secret use, external
code fetch or permissive authentication option. It writes only the intended
apt configuration file and prints effective configuration. Its acquisition keys
and values match the current
[runner-image configuration](https://github.com/actions/runner-images/blob/main/images/ubuntu/scripts/build/configure-apt.sh)
for these x64 Ubuntu jobs; the desktop-metadata setting also matches upstream.
The observed stall is consistent with
[runner-images issue 14594](https://github.com/actions/runner-images/issues/14594).
The issue's failure-suppression workaround was not copied.

The three local calls follow checkout and immediately precede their respective
browser-install steps. Removing only those calls from parsed current YAML makes
the workflow identical to `6485edf`. Thus permissions, timeouts, tests, engines,
required/advisory status, existing action references and all other step ordering
are unchanged. Playwright still installs required signed system libraries via
`--with-deps`; no dependency removal or signature bypass was introduced.
The late `zzzz-fontkit-ci` name sorts after upstream's `zz-retries`.

Fresh independent checks, all passing:

- Inline Python/PyYAML parses both files, checks the composite schema shape,
  Linux guard, three call positions, exact four APT directives, lack of
  authentication bypasses, and full workflow equality after removing the calls.
- The extracted action script is supplied on stdin to
  `C:/Program Files/Git/bin/bash.exe --noprofile --norc -n`: exit 0.
  A separate stdin probe uses the explicit-shell `-e -o pipefail` flags and a
  failing sudo stub; it exits 73 and never reaches the apt-config stub. It writes
  no apt file and confirms write failure is not swallowed.
- `$env:PYTHONPATH='tests'; python -m unittest test_release -v`: 25 tests,
  OK, zero skips, exit 0, 1.533 seconds; no browser ran.
- `git diff --check -- .github/workflows/quality-gate.yml`: exit 0.
  A direct whitespace assertion passes for both YAML files. The new-file
  `git diff --no-index --check -- NUL .../action.yml` exits 1 for file differences
  and reports no whitespace error; that exit is not represented as a passing
  zero-exit command.

Live graph coverage still reports generation `2026-10-07T17:07:14Z`; workflow
metadata changed and the new action is untracked by that generation. Direct
current source and fresh parser/shell evidence support this scoped verdict.
The upstream sources were independently fetched during this review.

The punctuation-only comma correction in README's Firefox-status inventory
was read at line 707; it changes no coverage claim or browser behavior. The
retry-log assertion initially used UTF-8 and encountered a UTF-16 BOM; rerunning
with BOM-based decoding passed both log assertions and the YAML whitespace
checks. This local log-decoding error is not a CI or product failure.

No actual Ubuntu apt installation, hosted composite execution, GitHub semantic
action validator, full suite or browser gate ran in this scoped re-review.
The schema check is bounded structural validation, not a claim of a complete
GitHub validator. Hosted mirror fallback and final matrix completion require
the final exact-head CI. This necessary setup correction is approved for the
same release landing after the remaining gates; publication remains separate.
