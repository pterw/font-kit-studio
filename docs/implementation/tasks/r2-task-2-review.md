# R2.1/R2.2 independent implementation review

Date: 2026-10-08. Initial verdict: **Changes required**.
Current verdict: **Approved**, after the scoped re-review below.

## Scope and snapshot

Reviewed the integrated seven-path implementation on `feat/r2-detection`, HEAD
`4aa264a9e38f17f897a93a3a8e99786a361c0900`, against the full task brief, full
362-line durable and scratch implementer reports, binding protocol/detection
contracts, R2.1/R2.2 ownership, D058, Addendum 5/D061 and execution Addendum 6.
AGENTS.md, global rules, constraints and requesting-code-review instructions
apply. This is detector/bridge acceptance, not Studio S1 or future Apply acceptance.

All seven integrated files matched the detached producer's canonical LF bytes
before and after verification. ROOT has CRLF checkout bytes; raw equality is not
claimed. Bridge canonical SHA-256:
`fbd85d8a84c0e158b2fb8df0740139033b4483f862cd94370522095995780839`.
ROOT bridge raw SHA-256:
`1d00271b81fa32e343aa23064afe1850f0553bd579c3b5ec29167a12fab20f39`.
The host's canonical hash is
`f00574a6712f6a36b265e82df58bca396b81d05546fa0f8c1de9d9d2ccc4c3eb`;
its ROOT raw hash is
`0d316150ce7b225197052be452d553a46b8add3b6843bb6298caa92aaf591c36`.

Fresh Tier 2 MCP context: `font-kit-studio-local`, ready, generation
2026-10-07T17:07:14Z, 2,637 nodes/12,760 edges. Relevant existing source has
metadata changes; new role modules are not tracked and fixtures/docs are excluded
or untracked. Coverage checks do not prove completeness. Direct full current
source and canonical-copy verification are authority for this patch; the old
legacy handler traces do not establish new detector correctness.

## Important finding: late native style changes produce complete stale evidence

**fontkit-bridge.js:1298-1311**, especially the yield at :1302 and single check
at :1305. The second rendered pass checks each parent once while yielding
between parents. A parent checked near the beginning can change through native
pseudo-state while the rest of that pass continues. Focus does not mutate DOM,
rule text or URL, so the terminal generation check can still certify the earlier
tuple as current. The new early-focus regression at
`tests/test_role_detection.py:58` does not cover this later window.

Confirmed through the public host request and native Playwright focus, using the
real bridge and real 5,000-parent fixture. Before hello, add only authored CSS:
`body:focus-within .g00 {font-size:35px}`. Start `request({type:'design:detect'})`,
await 16 changes of the fixture's existing animation-frame heartbeat, then focus
the actual Responsiveness probe textbox. Observe the public detect message and
native focus timestamps in the target. No bridge internals or browser methods are
replaced. The first complete stale result was:

```json
{"mode":"style-only","beats":16,"completedBeforeFocus":false,
 "focusDelayMs":306.7,"elapsedMs":506,"complete":true,"reason":null,
 "count":5000,"pageVersion":0,"currentPageVersion":0,
 "current":{"size":"35px","visibility":"visible"},
 "oldGroupCount":250,"badComplete":true}
```

The reply retained the exact original serif/20px/400/none/0 identity with 250
members while the group's current rendered size was 35px. Focus occurred about
199 ms before reported completion, not after the reply or in its delivery gap.
The public host had not received a completion before focus. Author main DOM,
revision zero and absence of page errors were checked after the result.

The probe declared modes `style-only` and `eligibility-only`, heartbeat delays
`0,4,8,12,16,20`, an 80-second bound and stop on first confirmed mismatch. These
are fixed stimuli, not retries until a preferred result. Earlier style-only
parameters returned incomplete/page-changed:

| Heartbeat delay | Native focus after detect (ms) | Reply elapsed (ms) | Result |
|---|---:|---:|---|
| 0 | 59.9 | 310.2 | page-changed |
| 4 | 99.8 | 284.9 | page-changed |
| 8 | 164.5 | 272.6 | page-changed |
| 12 | 251.9 | 279.9 | page-changed |
| 16 | 306.7 | 506.0 | complete stale tuple |

The ordinary foreground inline Python probe exited 1 after 21.684 seconds,
closing every fresh context and the shared browser/driver in finally blocks.
It stopped at the first failure, so delay 20 and eligibility-only were not run.

Reproduction uses `RoleBridgeCase.open('chromium',
target=TARGET+'/fixtures/large-page/index.html')`, `hello`, public interact mode,
and the following public operations (fresh context for each fixed delay):

```python
# PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1
frame.evaluate("""() => {
  const style=document.createElement('style');
  style.textContent='body:focus-within .g00 {font-size:35px}';
  document.head.appendChild(style);
  window.probeTimes={};
  addEventListener('message',e=>{
    if(e.data?.type==='design:detect') probeTimes.detect=performance.now();
  });
  document.querySelector('#responsiveness').addEventListener('focus',()=>{
    probeTimes.focus=performance.now();
  });
}""")
case.hello(page)
case.control(page, {'type':'design:mode','mode':'interact'})
mark=case.mark(page)
page.evaluate("() => {window.probePending=request({type:'design:detect'});}")
frame.evaluate("""beats => new Promise(resolve => {
  const start=fixtureProbe.heartbeat;
  function tick(){
    if(fixtureProbe.heartbeat-start>=beats) resolve();
    else requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})""", 16)
completed_before=bool(case.messages(page,'design:detected',mark))
frame.get_by_role('textbox',name='Responsiveness probe',exact=True).focus()
reply=page.evaluate('probePending')
# Compare reply identities/counts with current .g00 computed style and timestamps.
# The observed failure also required focusDelayMs < reply.elapsedMs - 30.
# Always case.doCleanups(); finally close support._close_shared().
```

This violates the binding stale-evidence rule at plan :259-264 and constraints
rule 10. A complete reply is eligible for checked evidence, so this is material
incorrect evidence, rather than a request for universal instantaneous rendering
tracking. Fix the observable late native-state window within owned runtime/test
paths and retain a regression with separate style and eligibility stimuli.
Another identical cooperative pass alone merely moves the window.

No Critical or separate Minor finding is asserted. The rule-heavy stylesheet
enumeration concern remains a source-based performance limitation, not a runtime
failure established in this review.

## Verification and working behavior

Independent ordinary foreground command, after the controller released its
benchmark/browser phase:

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_role_protocol test_role_detection test_r2_static_fixtures test_bridge_runtime.HandshakeTests test_support -v
```

**67 tests in 125.390 seconds, OK, zero skips, Chromium only.** Full output read.
The first independent complete 5,000-parent scan was **363 ms**, with heartbeat
128 -> 132, native typed `x` acknowledged before reply, replyAlreadyArrived false,
complete true and exactly 5,000 scanned parents. Literal 20 x 250 groups, bindings,
rendered styles and unchanged author DOM were checked by that test.

The focused run independently exercises native `.1`/`#1` correlated rejection,
escaped selector recovery, early native style/eligibility invalidation, Color 4
zero alpha and zero-height/border clipping, exact URL ceiling and unsupported-URL
null shapes/recovery, stale/superseded jobs, hostile source/origin/session/payload,
reload/reset/dispose, limits and near-1-MiB UTF-8 replies. Near-cap receipt tests
include a success within 64 bytes below the cap and rejection above it. Helper
guard canaries retain local HTTPS fulfillment behind the abort guard. Passing
these checks does not resolve the separately reproduced late-window failure.

Source inspection supports the final wire-size scalar delta: only bounded ASCII
terminal scalars change after full serialization/UTF-8 sizing, and no asynchronous
yield occurs before posting. Legacy runtime dictionary changes are confined to
the narrow roleDetection capability assertion. The helper authenticates received
identity/URLs; production injection is not introduced. CHANGELOG describes
read-only bridge detection and unsupported-route inspector availability, without
claiming Studio UI, role application or persistence. Controller Addendum 6 changes
gate timing, not acceptance criteria; R2.1/R2.2 remain open pending acceptance.

Independent fast checks:

| Command | Result |
|---|---|
| `python scripts/verify.py --static-only` | PASS: 96 IDs, inline JS and provenance; explicit browser SKIP |
| `node --check fontkit-bridge.js` | PASS, exit 0 |
| `python -m ruff check . --exclude .agents` | PASS |
| `python -m ruff check .` | Exit 1, four preserved owner skill findings |
| `git diff --check`; `git diff --cached --check` | Both exit 0 |
| `python .superpowers/sdd/r2/verify-detector-copy.py` | All seven canonical LF hashes match, before/after |

Exact Ruff findings are the unchanged untracked skill
`.agents/skills/github-awesome-copilot-skills-acquire-codebase-knowledge/scripts/scan.py`:
unused json :21, Set :23, re :24, and exclude_dirs_str :294. No fixes applied.

Full Chromium halves, frontend gate, full Node package, Firefox canary and commit
message gates were not run by this reviewer; settled-wave acceptance remains
pending. No Firefox or other-engine claim. Bounded rule-heavy CSS stress and the
separate eligibility-only late-window probe were not run after the blocker.
Writer mutation/production results were read in full but are not independent
reviewer reruns. No source/index/HEAD/branch mutations, server launches, denied
cleanup retries or fixture-copy deletion occurred. Only this review file changed.

## Required next step

Return the confirmed Important finding to the same source owner. Re-review the
frozen fix with the late native-state regression, relevant focused checks and the
remaining bounded probes. **This candidate is not approved for landing.**

## Scoped native-state re-review (2026-10-08)

Verdict: **Approved** for the corrected R2.1/R2.2 implementation. The Important
finding above is resolved for the reproduced native interaction window. The
earlier rejected snapshot, genuine failure and measurements remain historical
evidence. No new Critical, Important or Minor finding is asserted.

Read the full updated brief, full 536-line durable report (including the original
362-line report and complete correction), full 167-line fix delta, binding
contract/R2.1/R2.2, Addenda 5/6 and constraints. Independently decoded the saved
byte snapshot in memory, verified its hashes, and compared canonical contents:
only bridge and detection tests changed; the other five files are unchanged.
No snapshot payload was printed or source restored/edited by this reviewer.

Current bridge raw and canonical SHA-256:
`08fcdf50f350a9bbfd6fadbc5e7a9cedd637bccdf47cac76070f5580eac8896e`.
Current detection-test raw and canonical SHA-256:
`449cc67fc2817775d606dd34211b4caa7db279dc321efdbdd98896eefe75c38d`.
All seven canonical copies matched the frozen producer before/after verification;
the other five ROOT raw files still differ only through checkout newline forms.
HEAD/branch remain `4aa264a9e38f17f897a93a3a8e99786a361c0900`/feat/r2-detection.

The eight runtime lines at fontkit-bridge.js:1048-1055 advance the page generation
on passive capture focusin/out, pointerover/out/down/up/cancel, and filtered
button Space/Enter keydown/up. They run only with active session/source and
continue after completion, rather than relying on another yielding final pass.
Ordinary textbox keys/input are excluded. Existing listen :590-592 preserves
options and dispose :620-634 removes the exact registered handlers and cancels
jobs. Repeated observation does not duplicate listeners. No preventDefault,
author DOM patch, new capability or session/authentication relaxation is added.

Detection tests :88-216 add separate style/eligibility focus, already-hovered
pointer activation, Space activation, hover and release cases. They use real
native controls and capture-phase public timestamps. Valid earlier completion
must retain the exact literal pre-event tuple/count; a native change more than
30ms before completion cannot certify old rendering. Subsequent stable Detect,
opposite native state, authenticated ready epoch BEFORE another Detect, literal
rendering, author DOM, revision and error checks remain. The earlier pending
observation moves before focus; it no longer rejects a legitimate fast rejection.

After the controller's integrated browser gates closed, independently reran:

```powershell
$env:PYTHONPATH='tests'; $env:FKS_ENGINES='chromium'; $env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_role_protocol test_role_detection test_r2_static_fixtures test_bridge_runtime.HandshakeTests test_support -v
```

**72 tests, 142.316s, OK, zero skips, Chromium only; full output read.** FIRST
complete 5,000 scan: **341.9 ms**, heartbeat 103->108, native input `x` before reply,
replyAlreadyArrived:false, all 20 literal groups/bindings and author DOM checked.

Independent suite native observations included:

| Stimulus | Native / reply elapsed (ms) | Result |
|---|---:|---|
| Style-only focus |293.1 /301.6|page-changed, generation0->1 |
| Hover |272.7 /285.7|page-changed, generation0->1 |
| Already-hovered pointerdown |259.9 /273.3|page-changed, generation2->3 |
| Pointerup |285.0 /297.4|page-changed, generation3->4 |
| Eligibility focus |294.2 /287.0|valid earlier complete; recovery/epoch checked |
| Space down/up |338.3 /279.4;339.1 /314.0|valid earlier complete; recovery/epoch checked |

A separate ordinary foreground inline probe declared exactly style-only and
eligibility-only focus at 16 heartbeat frames, followed by one 3,000-rule stress.
Style reply completed at 300 ms before native focus at 308.3 ms; it retained the
correct earlier 20px tuple/count 250. Stable 35px/count 5,000 and opposite-state
ready epoch 2 passed. Eligibility native 285.3 ms/reply 286.7 ms returned
page-changed/epoch 0->1 with g00 hidden; stable count 4,750 then native blur/public
ready epoch 2/recovered count 5,000 passed. Author DOM, revision 0/no errors checked.

My inline stress setup initially decoded a Python newline escape inside a JS
string, causing Frame.evaluate SyntaxError before any stress Detect. This was a
reviewer probe error, not product RED. All resources closed after 12.483s. Changing
only the in-memory CSS join to an empty separator allowed the first actual stress
scan, without a warm-up/retry benchmark or source edit. It parsed exactly 3,000
extra unused CSS rules and completed 5,000/20x250 in **372.3 ms**, heartbeat 92->96,
native input `x` before reply; author DOM/revision 0/no errors preserved. Exit 0,
all resources closed after 3.498s. The recorded maximum frame gap of 450 ms includes
pre-Detect setup and is not a measured generator-slice duration.

Static 96 IDs/inline-JS/provenance, node syntax, product Ruff and both whitespace
checks independently pass again. Exact Ruff still reports ONLY the same four
owner skill findings :21/:23/:24/:294 recorded above. Canonical-copy verification
passes again after all probes. Fresh MCP status/coverage reconfirm the same ready
generation and metadata_changed/not_tracked/excluded limitations; direct source
remains authority, without a fresh detector-graph completeness claim.

Writer's genuine focus/pointer/Space REDs, four final guard-group mutations and
earlier timing-only failures were read in full. Those mutations and controller
legacy 18/production 2 are reported evidence, not additional reviewer reruns.
No test/source/index/branch/HEAD changes, servers, held buttons/keys, denied
cleanup retries or fixture-copy deletions. Reviewer changed only this verdict;
all borrowed contexts and shared browser/driver closed normally in finally.

This approves the scoped bridge/helper detection implementation. It does not
prove universal animation/opaque-sheet/native rendering tracking or a strict 8ms
adversarial stylesheet bound; synchronous rule stamping remains as documented.
Full Chromium halves, full Node package, frontend/advisory Firefox, commit gates,
and real Studio S1 acceptance remain with their named owners. No future Apply,
adapter, persistence, checked-page UI or settled-wave completion is claimed.
