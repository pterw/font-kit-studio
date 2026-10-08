# 0.3.1 Task B independent review

Date: 2026-10-07. Verdict: **Approved**.
Scope: the uncommitted workflow diff against `281a61c` on
`fix/localhost-cookies`, plus the Task B brief and report.

## Findings

- Critical: none.
- Important: none.
- Minor: none.

## Scope and compatibility

A fresh comparison against HEAD confirmed exactly three changed action
references in `release.yml` and eight in `quality-gate.yml`. Normalizing only
checkout/setup-node references made the parsed workflow structures identical.
No inputs, permissions, triggers, job ordering, environment, run commands or
other actions changed. All release actions retain full SHA pins and major
comments; the quality gate retains major tags.

- `release.yml:23-35`: `npm-release`, gate dependency, OIDC permission,
  Node 24 and registry URL remain intact. The publish and release ordering,
  tag/version check and CHANGELOG validation remain unchanged.
- `quality-gate.yml:35-53`: full history and tags remain enabled, preserving
  provenance and commit-message checks. Node selection remains 22 here.
- `quality-gate.yml:197-201`, `223-229`, `260-266`: matrix Node selection
  and both explicit npm caches retain their inputs and lockfile paths.

The tagged upstream action manifests declare node24. Their READMEs document
runner 2.327.1 as the runtime minimum. These workflows use hosted latest
images; actual runner execution remains a CI check, not a local claim.
Checkout's credential relocation preserves ordinary authenticated Git commands;
these workflows use no container action requiring the additional runner minimum.
Its v7 fork restriction concerns `pull_request_target` and `workflow_run`, neither
of which these workflows use. This compatibility conclusion is an inference
from the workflow triggers and the
[checkout migration notes](https://github.com/actions/checkout/blob/v7.0.1/README.md).

Setup-node's removed `always-auth` input is unused. Automatic npm caching needs
package-manager metadata in the repository-root package.json; that file is
absent here, and the package metadata also declares no package manager. Jobs
without an explicit cache therefore acquire no new automatic cache. Explicit
fixture caches remain supported. See the
[setup-node migration notes](https://github.com/actions/setup-node/blob/v7.0.0/README.md).
Removal of the dummy auth-token export does not remove an existing credential:
the release workflow supplies none and retains trusted publishing. Upstream
also documents that publishing path in its
[v7 release notes](https://github.com/actions/setup-node/releases/tag/v7.0.0).

## Fresh verification and limits

- `$env:PYTHONPATH='tests'; python -m unittest test_release -v`: 25 tests,
  OK, exit 0. These are parser/subprocess tests; no browser engine ran.
- Parsed before/after YAML comparison: equal except the 11 approved references.
- `git diff --check -- .github/workflows/release.yml .github/workflows/quality-gate.yml`:
  exit 0. Git emitted its usual autocrlf conversion warnings.
- Graph project `font-kit-studio-local`, generation `2026-10-07T17:07:14Z`:
  coverage reports no recorded parse gap for workflows/test_release, but
  metadata changed; docs are excluded. Review relies on direct current source
  and fresh tests, not graph completeness. No index mutation performed.

The controller's baseline 59 release/support tests are reported in its task
record; they are not this review's independent result. Full suite, test_support,
static/provenance, lint, Node package, frontend and Firefox gates were not run
by this reviewer. The controller owns landing gates. Hosted CI and actual
publishing were not exercised; release approval remains with the maintainer.
No denied tool calls occurred. Only this review file was written.
