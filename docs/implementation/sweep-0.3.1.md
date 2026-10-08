# 0.3.1 live-claim sweep

Date: 2026-10-07. Branch: `fix/localhost-cookies`; base `7598ebb`.
Scope: tracked Studio/bridge/forwarder, package source/tests/docs, fixture
package/lock records, README, CHANGELOG, active plan/roadmap, rules and ledger
Current state. Older dated records were separated, not exhaustively traversed.
Ignored dependencies and owner-local files were excluded. Literal source
search supplies the evidence; the graph generation predates these edits and
excludes docs, fixtures and Node test modules.

## Findings and disposition

| Claim | Evidence | Disposition |
|---|---|---|
| Live release labels | Studio title/eyebrow, bridge header, package.json, vite-ts linked lock record and existing title assertions | All read 0.3.1. Protocol 1 and JSON format 0.1.1 remain. |
| Old Studio filename removal | Forwarding stub, README, roadmap decision 2, rename-test docstring | R2 (0.4.0), per D052. Stub still preserves query/hash; independent Chromium probes pass. |
| Studio always uses IPv4 / localhost apps lose cookies | README Known limits and package README | Replaced with hostname matching and retained IPv6 mismatch. Localhost and IPv4 use their respective app host. |
| Proxy storage starts empty | Both READMEs | Retained: its random port gives the app separate origin storage. Cookies ignore ports. |
| Settings migration affects everyone | Both READMEs and CHANGELOG | Scoped to localhost users who pinned Studio's port in 0.3.0. Unpinned ports were already random. |
| Only standalone Vite prints a replacement URL | Both READMEs | Covers command and standalone modes after config restart, including fixed/random origin costs (D053). |
| Proxy refusal lists only localhost/IPv4 | proxy.js and existing proxy/CLI/runner message assertions | Corrected to include accepted [::1], with unchanged validation (D054/Addendum 5). |
| Historical tagging and CI-only Firefox in Current state | Ledger Current state | Removed obsolete pending-tag instruction and corrected local/CI canary status. |
| Process words in live product docs | README/package README/CHANGELOG and Current state | No model/session/authorization/review-round narrative. Ordinary product uses of "tool" and contributor signature policy are valid. |

## References deliberately retained

- Historical CHANGELOG 0.3.0 and prior release evidence describe their own
  release. Their old forwarding deadline is superseded by D052, not rewritten.
- README's minimum plugin version 0.3.0 remains a correct compatibility floor.
- The active plan's pre-C 0.3.0 requirement and dated events remain historical.
- Synthetic 0.3.0 strings in release-note tests are test input, not live labels.
- Numeric font-weight lists and unrelated dependency versions are not product
  versions. Linked fixture version records were checked separately.
- Loopback error examples introduced with "such as" remain valid examples;
  the proxy's exhaustive accepted-host error list needed correction.

No dependencies, source rewriting, product-framing expansion or new roadmap
phase resulted from the sweep. Release/tag hashes and publication were not
verified by this source consistency pass; release gates have separate evidence.
