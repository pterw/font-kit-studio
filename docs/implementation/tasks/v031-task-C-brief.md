# 0.3.1 Task C: release labels, documentation and evidence

Date: 2026-10-07. Base: `6485edf2eb19f02ab1bea8eaffd1c30b340ae41f`.
Branch: `fix/localhost-cookies`. Prior CI completed; its infrastructure-only retry is pending.

Controller inline task; implementation starts after A and B are committed and
the preceding exact-head CI is read. Binding plan: Task C and Addendum 2 in
docs/plans/2026-10-07-v0.3.1-localhost-cookies.md. D052 keeps the forwarder to R2.

## Owned files

- packages/fontkitstudio/package.json, fontkit-studio.html, fontkit-bridge.js
- font_kit_studio_v0.1.1.html (deadline wording only)
- fixtures/vite-ts/package-lock.json and live linked-version records
- Version assertions named in Task C and the test_studio_rename.py module
  docstring for D052; no unrelated test edits
- Plan Addendum 5: proxy.js refusal-message literal and matching assertions
  in test/{proxy,cli,run-proxy}.test.js; no validation logic changes
- Plan Addendum 6: quality-gate.yml and local configure-browser-apt action;
  bounded Ubuntu dependency setup, with existing engines/check order preserved
- Plan Addenda 7/8: the same action's official Ubuntu mirror list and separate
  pip, system-dependency and browser-download steps; no test inventory changes
- README.md, packages/fontkitstudio/README.md, CHANGELOG.md
- Active plan, ledger, phase pointers if required, verification-0.3.1.md,
  sweep-0.3.1.md and accepted C brief/report/review

Preserve historical release entries and evidence. No source rewriting,
dependencies, protocol or JSON format changes, forwarder deletion, merge,
tag or registry mutation. One controller writer; independent reviewers and
sweepers own only their records. Preserve untracked owner files.

## Work and acceptance

1. Set package/Studio/bridge labels to 0.3.1, linked lockfile record included.
   Preserve protocol1 and JSON0.1.1. Update the existing title/eyebrow assertions.
2. Date CHANGELOG0.3.1 and update both compare links. Keep the settings cost
   scoped to localhost apps using --studio-port in0.3.0.
3. Replace the signed-out claim with hostname mismatch and retained IPv6
   limitations. Correct proxy origin claims; keep storage/random-port/no-sync/
   standalone-restart limits. Name R2 as the forwarder removal point in both
   live copies. No README product-framing expansion.
4. Sweep live labels, lockfiles, loopback claims and process words. Separate
   dated records; report all hits and judge each corrected live claim.
5. Independent branch review and scoped fixes; then freeze source for the
   release gates. Install fixtures and bundle before gates. Full Chromium
   halves, Node package, static/provenance, bridge syntax, ruff, frontend,
   Firefox canary and commit-message checks; include test_support.
6. Record exact commands/counts/engines/skips/advisory results. Exact local
   ruff limitation remains owner-installed .agents; disclose it and the
   product-tree alternate without changing lint policy.
7. Gate-backed release readiness only; pre-merge evidence cannot claim tag
   hashes. Commit with why-body, push, wait/read exact-head CI and leave draft
   only when required checks pass. Report material/churn counts separately.

Owner merges, tags mergecommit v0.3.1 annotated, pushes tag and approves
npm-release. Postpublication npm/provenance/tag-derived asset checks remain
unchecked until those actions occur. No agent performs them.
