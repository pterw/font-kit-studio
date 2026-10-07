# 0.3.1 Task C report

Date: 2026-10-07. Base: `6485edf` on `fix/localhost-cookies`.
Task brief: [C brief](v031-task-C-brief.md). [Independent review](v031-task-C-review.md)
is Approved, including the CI setup correction. Local release checks are complete;
final exact-head CI remains pending.

## Changes

- Studio title/eyebrow, bridge header and package version read 0.3.1.
  The linked vite-ts lock record and existing browser title assertions match.
  Protocol 1 and JSON format 0.1.1 are unchanged.
- CHANGELOG dates 0.3.1 and adds compare links. The host-transition settings
  cost is limited to localhost users who pinned Studio's port in 0.3.0.
- Both READMEs describe matched localhost cookies, retained IPv6 mismatch,
  random proxy storage, saved-settings origins and the latest Vite restart URL.
  Proxy requirements include the already accepted IPv6 loopback address.
- D052's R2 deadline is applied to the forwarding stub, README, roadmap pointer
  and rename-test docstring. Forwarding behavior and assertions are unchanged.
- Current state no longer promises an already completed historical tag or
  says the Firefox canary runs only in CI. D053 records the Vite restart choice.
- Addendum 5/D054 correct the proxy refusal message to include accepted IPv6
  loopback. Existing message assertions supply RED (11 wording mismatches)
  and GREEN (91 Node tests, no skips). The allow-list and refusal logic stay.
- Addendum 6/D055 apply bounded Linux APT acquisition and skip desktop metadata
  before the three browser-install jobs, through one local composite action.
  This follows the upstream runner-image correction for the reproduced stall.
  Required libraries, signatures, engines, test order and status remain intact.

## Evidence so far

All four fixtures installed with npm ci; the Node test command bundled the
0.3.1 source first. Node: 271 tests, 269 pass, zero fail, two existing no-project
environment skips. No new test or manufactured RED is needed for label/docs
edits: existing version and browser assertions characterize the release labels.

Task A's cookie/lifecycle implementation already has its own Approved review.
Fresh focused review passes 32 Python/Chromium label, forwarder and release
tests, three Node versions and 20 Node refusal/security tests. The setup-only
review passes 25 release tests plus YAML/Bash and failure-propagation checks;
it runs no browser. The live-claim sweep is complete. Full Chromium half A
passes 474 tests and half B passes 385 (859 total, no Python skips). Frontend
finishes 30/30 with seven blocking passes, zero advisory failures and 334 touch
reports. Firefox canary passes 51 with no skips (advisory). Static/provenance,
bridge syntax, product-tree lint, pre-commit, whitespace and message checks pass.
Exact Ruff retains the four known owner-skill findings. Evidence:
[verification](../verification-0.3.1.md). CI setup changes no browser-test inventory.

## Scope and limits

No runtime validation or connection behavior changed in C. Historical versions,
synthetic release-test fixtures, supplied provenance, export/protocol versions and owner files stay
intact. No merge, tag or publication occurred. Pre-merge evidence cannot claim
release-tag asset hashes. Exact Ruff has four known findings in an untracked
owner-installed skill; product-tree lint is recorded separately.

The prior head's CI timed out in Ubuntu dependency downloads; only those jobs
were retried. Node 26 passed 14 fixture tests; Node 22 repeated the APT stall.
Both retry logs were read before the setup correction. Hosted effectiveness
remains pending final CI. Browser checks remain
focused at implementation landings, with one full release run and an advisory
Firefox canary (plan Addendum 4).
