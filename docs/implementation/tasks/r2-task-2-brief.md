# R2 detection brief: protocol and read-only engine

Plan: docs/plans/2026-10-03-r2-engine.md R2.1 and R2.2. These land together;
no failing-test-only or future apply/clear acceptance skips. Dispatch requires
F1's reviewed oracle committed. The controller supplies worktree/BASE/outputs.

## Exact ownership

Own fontkit-bridge.js, tests/test_role_protocol.py, tests/role_support.py,
tests/fixtures/bridge/host-roles.html,
tests/fixtures/bridge/target-role-protocol.html and tests/test_role_detection.py.
In tests/test_bridge_runtime.py own only the expected capabilities dictionary
inside HandshakeTests.test_bridge_ready_carries_no_page_data_and_ready_describes_targets:
add roleDetection:true, preserving every existing assertion and capability.
F1 fixtures/oracles, old harness/fixtures and other bridge tests are read-only.
No Studio, package, CI, canary or shared documentation edits.

## Binding interfaces

Read the ENTIRE Binding protocol contract, R2.1/R2.2 tasks, constraints and
current bridge source around message authentication, hello, authorAttr, legacy
discovery, selector escaping, revision checks, reset and dispose before edits.
Contract field shapes, limits, identity, normalization and incomplete reasons
are authoritative; this brief does not redefine them. Advertise only detection.
Ready supplies authenticated document identity and empty roleState with the
empty digest 811c9dc5. No role stylesheet/apply/clear or automatic route notices
are implemented in PR A. Legacy reset/dispose/hello still cancel role jobs.

RoleBridgeCase subclasses the real BridgeCase with new owned host/target paths,
fresh shared-runtime contexts and verified HTTPS-prefix blocking before load.
Its owned HTTP route may add the real bridge auto-init script only to role-test
target HTML that lacks it. Do not mutate fixture files/builds, strip CSP or
bypass it with evaluate. Host request helpers pin source/origin/protocol/session,
match reply requestId, and advance revision only from authenticated matching
detected, roles-applied, legacy applied or rejected messages. Future reply types
are helper routing, not acceptance tests for unimplemented operations.

Give the target normal .body-copy 16px/1.5, author-role and ordinary author CSS
controls. Characterize legacy trust/handshake/inspector/reset/production GREEN
before edits. The first genuine RED is missing design:detected after valid hello
and detect. Preserve truthful unsupported behavior and additive compatibility.
Tests must render real styles/text with the real bridge, not assert messages
alone. Read-only detection additionally asserts unchanged author DOM/styles.

## Detection and safe bindings

Traverse eligible light-DOM direct-text parents once. Include below-viewport
text and range-rendered display:contents; independently test every documented
exclusion, nested/dedup case and transparent ancestor. Do not use legacy semantic
targets as the population or add author DOM attributes. Use authorAttr so
bridge hints never acquire author priority. Compare normalized literal F1
tuples/counts/variants, not results derived from the engine.

Validate exact request shapes and size, including knownRoles selectors. Verify
safe complete selector matches before preferring author roles/IDs/classes;
otherwise use safe unstable paths or bindingComplete:false. Hash-looking CSS
classes carry uncertainty, never universal compiler claims. Test escaped classes
and IDs, mixed-style broad selectors and valid zero matches. Exact author/style
identity namespaces, variant counts, duplicate names, discovery reorder and
near-duplicate boundary flags all follow the approved contract without merging.

Bound all stages, including binding and UTF-8 serialization. Exceeding element,
group, variant, identity, reply or time limits yields incomplete evidence. Test
hostile fields/prototype keys/oversize requests, unknown document and stale
messages without letting them establish identity or change author state.

## Cooperative work and freshness

Capture source/origin/session/document/page/revision/request generation and
check at every yield and terminal post. Read actual URL/content/style freshness;
a URL-only navigation during detection must invalidate before PR C hooks exist.
Same-session current invalidation replies page-changed with captured/current
identity. Superseded or wrong-session jobs cannot reply into a new session.
Latest detect supersedes older detect; accepted legacy mutation invalidates a
concurrent scan. Test hello/reset/dispose cancellation and stale URL/content/
style/revision cases through public behavior.

First complete scan of the loaded F1 5,000-element corpus must finish <=2,000ms
in desktop Chromium, including traversal/bindings/serialization. Target <=8ms
cooperative batches. Heartbeat advances and queued keystrokes render in the
native input before completion. No warm-up-only acceptance, retries until pass,
threshold increases or partial result counted as complete. Report the first
measurement and any failure candidly; investigate rather than hiding it.

Restored foreground mutations remove visibility, dedup, author priority,
threshold boundary, yielding and freshness guards. Each fails an independent
behavior assertion. Verify the HTTPS guard with a separate local canary and
retain an earlier local-fulfillment fallback throughout guard mutations. Restore
exact bytes in finally and close owned contexts/processes on every outcome.

## Focused acceptance and report

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_role_protocol test_role_detection test_r2_static_fixtures test_bridge_runtime.HandshakeTests test_support -v
python scripts/verify.py --static-only
node --check fontkit-bridge.js
python -m ruff check tests/test_role_protocol.py tests/role_support.py tests/test_role_detection.py tests/test_bridge_runtime.py
git diff --check
```

Independent reviewer probes new boundary, generation cases and FIRST full
benchmark. Full settled-wave gates stay with controller/gate runner; no full
Gecko suite. Return one owned-path patch and full report with RED/GREEN counts,
first benchmark/heartbeat/input observations, mutations, incomplete limits,
legacy characterization, cleanup and applicable AP checks. Draft product
CHANGELOG line, ledger, material/churn counts, commit subject and why-body.
Do not stage/commit/push/spawn. You are not alone; never revert another writer.
A denied call is reported and never retried through a different tool.
