# 0.3.1 Task B: workflow action runtimes

Plan: [Task B](../../plans/2026-10-07-v0.3.1-localhost-cookies.md).
Base: `281a61c`. Scope: controller inline changes to
`.github/workflows/release.yml` and `.github/workflows/quality-gate.yml` only.

Upgrade every checkout/setup-node reference to its current supported major.
Verify tags and SHAs upstream before editing. Keep release.yml full SHA pins
with major comments; keep quality-gate.yml tags. Preserve inputs, permissions,
triggers, environment approval, job ordering and trusted publishing. Do not
change any other action. No new product behavior or manufactured RED test.

Characterize the release constraints with `test_release` and `test_support`
before/after. Run static/provenance, bridge syntax, lint, whitespace and message
checks. Runtime suites, package tests, frontend gate and Firefox are skipped
locally because the diff cannot affect their runtime. CI verifies hosted runner
compatibility on the task branch.

Independent review is read-only except its review record and precedes commit.
The controller records the report, ledger and plan completion in the same
commit; no merge, release tag or registry write.
