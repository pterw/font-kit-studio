# R2.1/R2.2 detection code report

Date: 2026-10-08. Worktree: C:/fks/r2bridge. BASE:
6a7327bd2d901f4c668c476a8048658f82c682b6 (detached, unchanged).
Status: final source verified and frozen for independent implementation review.
The earlier unavailable-URL contract hold was resolved by binding Addendum 5/
D061 and the updated ROOT producer brief. Review acceptance remains pending.
No staging, commits, pushes, spawning or root application occurred.

## Changes and ownership

Exactly seven owned paths appear in detection-code.patch:
fontkit-bridge.js; tests/test_role_protocol.py; tests/role_support.py;
tests/fixtures/bridge/host-roles.html; tests/fixtures/bridge/target-role-protocol.html;
tests/test_role_detection.py; tests/test_bridge_runtime.py.
The last file changes only HandshakeTests' capability expectation, retaining
all prior capabilities/assertions. No Studio, shared helper, CI, package,
fixture-support, vendor, oracle, documentation or npm edits occurred.

The additive protocol-1 handler validates the exact detect envelope and bounded
known-role array/selector shapes. It advertises only roleDetection and supplies
empty roles/CSS/FNV state in authenticated ready. The real bridge measures direct
rendered light-DOM text parents, exact five-property style identities and author
role variants; it returns safe verified complete bindings or bindingComplete:false.
It does not change author DOM/styles or install a role stylesheet.

Source locations: grammar/exact envelope helper fontkit-bridge.js:148-168;
instance generation fields :478; dispatch :937; ready :996; URL/observation
:1017-1065; normalization/population :1067-1106; bindings :1108-1142;
validation/cooperative job/final wire :1144-1220; native selector checking and
collection :1222-1312; accepted reset cancellation :1538/:1549. Owned host
URL receipt validation tests/fixtures/bridge/host-roles.html:15-35.
Hello, dropped sessions and dispose cancel jobs.

The job captures source, origin, session, document, page version, actual URL,
revision and generation. Each asynchronous batch and terminal post revalidate
these. Native traversal/style/query operations run in cooperative ~8ms batches;
the 2,000ms clock also includes bindings, selector checks and UTF-8 reply sizing.
Native browser/style/layout/JSON operations cannot be preempted in mid-call;
this is an 8ms target, not a universal maximum for an adversarial app.
Final UTF-8 serialization above 1MiB returns reply-limit with empty evidence.
Sizing follows current-field/null-evidence updates and adjusts for the exact
ASCII scalar byte delta after elapsed/time-budget updates. The elapsed clock
starts before envelope validation, freshness stamping and all job stages; a
deadline miss at terminal sizing remains incomplete.

## Read and evidence boundaries

Read the full task brief, constraints, global rules, relevant complete binding
contract/R2.1/R2.2/D058, bootstrap state/history, README protocol context and
current detached runtime, legacy harness, F1 tests and independent literal
Bootstrap/large-page oracles. TDD, systematic-debugging and verification skills
were read and used. On continuation, read CURRENT ROOT constraints/producer
brief, Addendum 5/relevant URL clauses/D061, full URL contract review (Approved)
and full preliminary detection review (source hypotheses, Changes required).
The controller arranges independent review; this implementer
cannot spawn or stage under AGENTS.md.

Tier 2 parent evidence was supplied and current MCP index status reconfirmed:
font-kit-studio-local, ready 2637 nodes/12760 edges, generation
2026-10-07T17:07:14Z. Coverage checked all owned paths/evidence, including
correct Bootstrap oracle paths and the production-plugin test. Fixtures/docs
and the Node plugin test are excluded; future role tests were missing; bridge,
legacy runtime tests and Studio had metadata changes without recorded gaps.
Current detached source was read directly. No complete/fresh graph claim for
new code, excluded sources, or the detached worktree is made.

## Test-first and characterization evidence

Before runtime edits, legacy trust/handshake/inspector/reset/selection/composition
characterization was GREEN: 18 Chromium tests, 12.766s. The command uses
ConfirmedDefectTests, HandshakeTests, SessionLifecycleTests,
TargetedUpdateTests.test_reset_one_target_or_everything, SelectionTests and
LegacyCompositionTests from test_bridge_runtime. It passed after the initial implementation: 18 tests, 12.404s; after all
continuation changes: 18 tests, 15.860s, OK.

The first real valid hello/detect baseline was RED: one test, 6.986s,
missing design:detected/timeout; after the handler, GREEN: one test, 1.017s.
Exact hostile fields/limits then failed 13 rejection subcases (one test,
1.046s); validator slice GREEN: two tests, 1.590s. Population RED 15!=6,
then three tests GREEN 1.674s. Safe bindings RED empty selectors, then four
tests GREEN 3.316s. Near-boundary RED missing g00/g01 relation, then literal
Bootstrap and pairwise boundary tests GREEN: two tests, 4.751s.
Accepted reset cancellation was genuinely RED: old scan returned page-changed
instead of being suppressed; explicit reset cancellation made the complete
latest-detect/hello/reset/dispose test GREEN. Existing URL/content/CSSOM/revision
invalidation and six limits were characterized GREEN rather than manufactured RED.
An explicitly visible child under a hidden ancestor was then genuinely RED
6!=7, fixed by checking element visibility separately from ancestor display/
opacity, and GREEN: one test, 1.020s. Final population is seven parents.

Honest corrections: one mistaken unittest method name errored at discovery;
corrected name passed. A near-flag generator edit initially failed node syntax
(missing parenthesis) and was corrected before testing. Freshness fixture
assertions initially used the wrong nested text and inserted CSS at rule index
zero; source inspection showed the actual nested literal and cascade order,
which were corrected. A reply-limit probe originally produced only ~250KiB;
the valid 128-role/32-selector request now amplifies repeated 100-char IDs and
literal signatures above 1MiB. Playwright argument decoding dropped an own
__proto__ key; transporting that hostile object as literal JSON text preserved
it and confirmed rejection. These were not product regressions or genuine REDs.

Production exclusion was characterized after bridge edits, not before:
node --test --test-name-pattern='build|serve only'
packages/fontkitstudio/test/vite-plugin.test.js: two tests, two suites,
0 failures/skips. Existing plugin.apply is false for build and true for serve;
no package/build files changed. No claim of a new production bundle build.
Old BASE bridge served through the owned route lacks capability/state and
truthfully ignores detect while its real inspector update renders 23px.
A script-src none header prevents bridge auto-init while author text/16px CSS
still render; F1 route injection does not strip or bypass CSP.

## Continuation: public RED/GREEN and URL ruling

The initial report froze URL work with the conflict explicitly unresolved; no
fallback was guessed. After approved Addendum 5/D061, initial actual route length
2001 was RED (ready raw URL instead of null; one test 1.196s). Nullable ready,
fixed safe initial unsupported-value detail, valid-to-unsupported captured valid/
current null plus empty evidence, raw null-to-null epoch tracking, exact 2000
supported boundary, reconnect and legacy 27px update/reset16px are now tested.
Combined actual-URL/numeric cases GREEN: two tests, 1.748s. Valid-to-unsupported
history navigation is scheduled through the public detect message, not a private
engine hook; author rendering remains literal 20px and fresh reconnect completes.
No unsupported actual URL is posted, sanitized, omitted or used as checked data.

P1 source hypothesis was reproduced: native-invalid .1 timed out rather than
correlated rejection (one test 1.244s). Cooperative native selector validation
before collecting evidence now rejects .1/#1, with no target error or author
DOM/revision change. Escaped numeric class/ID positives each match one rendered
16px ordinary body; a fresh valid detect still completes. No grammar broadening.

P2 original actionability click observation occurred after the reply already
arrived; it was not a product RED. Actual native focus through Locator.focus
then proved stale complete4750 under old cached20px while current text35px and
g19 hidden, unchanged DOM/CSS-rule generation0 (one test 4.059s RED).
Cooperative final direct-text population/tuple revalidation detects this change
and increments current pageVersion above captured. Native focus plus first new
5000 benchmark GREEN: two tests, 8.262s; later stable focused rendering completes
4750 against35px. This is a rendered pseudo-state proof, not fabricated clock data.

Color4 alpha0 and zero-height overflow initially each counted3 instead of literal
2 (one test 1.267s, two failures). Alpha parsing and text-range clipping passed
with population (two tests, 1.643s). A zero-height box with2px border then exposed
an additional3!=2 RED (one test 1.722s); intersection with scaled client padding
box rather than border box fixed it (one test 1.662s GREEN). Below-viewport and
display:contents text remain eligible.

Hostile matching target-origin receipts containing a foreign/credential URL or
complete current null initially advanced helper revision999 (three subcases;
combined with already-working valid-to-unavailable, two tests10.997s RED).
Owned receiver validation now retains authentication and rejects those receipts;
one test1.583s GREEN. The final null case uses a valid captured URL and current
null with complete:true, independently proving that invalid complete shape.
This harness is a tested receiver boundary, not a claim that Studio S1 is built.
Browsers cannot set foreign-origin location by same-origin history. Controller's
actual Chrome credential probe stripped userinfo, so actual credential location
retention is NOT characterized here; literal hostile credential receipts are.

The final-wire public sweep reproduced1048588 bytes above1048576 despite the
intermediate check (one test11.388s RED). Exact final scalar sizing after all
wire updates passed (one test15.398s GREEN). Each complete reply is independently
UTF-8 sized, matchCount2/styles16px rendered; valid IDs/selectors are calibrated
against framing bytes, then request ID padding sweeps the boundary. This is not
a benchmark warm-up or retry-until-pass. At least one reply-limit occurs and the
largest complete reply is within64 bytes below the cap.

Final focused67 run initially failed once in123.594s: seven-parent population/
rendering passed, but baseline outerHTML preceded legacy delayed auto-discovery
of nodes authored after hello. That discovery adds normal bridge hints. Moving
this owned test's author setup before hello lets first discovery settle before
the baseline; single test GREEN1.148s. No legacy runtime, fixed wait, threshold
or author-preservation assertion was removed. This was a test setup race, not
misreported detection DOM mutation. An accidental Ruff invocation included the
JS file and yielded Python syntax errors; corrected exact Python-only command
passed. Both command mistakes/failures remain recorded.

## First complete scan and responsiveness

The first complete 5,000-parent scan before yielding binding/collection work:
131.3ms, complete5000, heartbeat134->139, input x, but replyAlreadyArrived:true.
It FAILED the independent native-input-before-completion assertion. No partial
or fast-but-unresponsive result was accepted. This was investigated and changed.
The first corrected implementation scan: 136.8ms, complete5000, heartbeat115->119,
input x, replyAlreadyArrived:false; one test 3.791s GREEN. No warm-up-only
measurement, threshold increase, or unchanged retry-until-pass was used.
Later fresh contexts are regression evidence, not replacements for that history:
combined new modules 356ms (heartbeat146->149); final focused run 209.8ms
(heartbeat143->147). Both complete5000 and queued keystroke acknowledgement x
before reply. First post-revalidation measurement was388.6ms, heartbeat160->164,
inputx before reply (the two-test8.262s run above). With all alpha/clipping/wire
guards, first fresh final measurement382.1ms, heartbeat121->126; after the owned
population setup correction,509.2ms, heartbeat148->152. Both complete5000 with
inputx before reply. These preserve the initial responsiveness failure and first
corrected136.8ms; neither replaces them. Literal oracle assertions include 20 exact groups/tuples, 250
parents each, complete safe .g00-.g19 bindings and unchanged author main DOM.

## Independent rendered coverage and incomplete results

Bootstrap 4/5 whole literal identity/signature/count/variant and binding-match
oracles pass. Coverage includes below-viewport, display:contents ranges,
direct-text dedup, nested text, every named exclusion, transparent ancestors,
visibility inheritance, zero area, form values/placeholders, pseudo text,
shadow roots, nested frames and SVG. Hash-looking class uncertainty is explicit;
no universal compiler hash stability is asserted. Escaped class/ID/author role,
trimmed case-sensitive role namespaces, duplicate suggested names, discovery
reorder, broad mixed-style selector fallback, zero matches and a 40-parent
unbound group are rendered/DOM-preservation checks. Near duplicates remain
pairwise inclusive flags, never merged or transitively collapsed.

Element-limit reports 10001 visited eligible parents; group-limit retains 128
groups; variant-limit retains eight variants; a 201-char role is identity-limit.
Reply amplification above 1MiB produces reply-limit without oversized evidence.
A real 2.1s application contention interval produces time-budget, not a fake
clock or relaxed threshold. URL/text/CSSOM/accepted inspector revision changes
produce page-changed with captured/current identity; a fresh request completes
against the changed rendering. Latest detect, hello, reset and dispose suppress
older replies. Reload issues a new document; unknown old identity cannot replace
ready. Wrong source/origin/session/version and unsolicited/unmatched high-revision
messages preserve the author DOM/16px rendering and helper revision.

## Foreground mutations and restoration

Every mutation ran an ordinary foreground unittest child with its context cleanup;
owned file bytes were restored in finally and compared exactly. No sleep loops,
process-name kills, background mutation scripts or shared helper edits.

| Guard removed | Independent failure |
|---|---|
| Population visibility (final) | 25 != 7; one test 1.110s |
| Direct-parent dedup (final) | 8 != 7; one test 1.162s |
| Element visibility inheritance | 9 != 7; one test 1.131s |
| authorAttr priority | 'title' != None; one test 1.123s |
| Inclusive size boundary | g00/g02 near flag false; one test 3.702s |
| 8ms yielding | complete117.5ms but replyAlreadyArrived true; one test 4.009s |
| Freshness | four complete:true vs page-changed failures; one test 16.029s |
| HTTPS abort guard | abort0/fallback2 vs abort2/fallback0; one test 0.803s |

The first author-priority mutation survived the normal author-ID test because
that test contains no bridge-generated role hint. This was reported, and the
existing escaped/hash corpus now explicitly proves a genuine legacy title hint
remains an automatic identity; the same mutation fails that independent assertion.
Earlier population mutations against the six-parent version failed 24!=6/7!=6.
The permanent earlier HTTPS local CORS fulfillment fallback remained installed
throughout its mutation; all HTTPS traffic aborted or locally fulfilled, with
no external contact. Separate unchanged
blank-page fetch canaries prove both HTTPS-prefix aborts without error-page close
lifecycle changes. All mutations restored; final bridge SHA-256
fbd85d8a84c0e158b2fb8df0740139033b4483f862cd94370522095995780839;
role_support SHA-256 2072867e6e195ee9abd1faf0542364b4cdf4ce4697f5f8e1c1ae11c3e2146e10.

Continuation restored foreground mutations (same ordinary -m unittest form):

| Guard removed | Independent failure / test duration |
|---|---|
| Actual URL route bound | authenticated ready timeout; one test8.582s error |
| Null current URL evidence clearing | timeout != design:detected; one test9.965s |
| Native selector validation | timeout != unsupported-value; one test1.401s |
| Rendered tuple revalidation | complete:true != page-changed; one test4.188s |
| Color4 alpha0 | 3 != 2; one test1.738s |
| Overflow range clipping | two 3 != 2 failures; one test1.683s |
| Receiver URL validation | three revision999 != 0 failures; one test1.510s |
| Final wire size guard | 1048581 > 1048576; one test13.044s |

Every child exited normally/nonzero; source restored in finally and SHA compared
exactly. Bridge hash above unchanged; host SHA-256
f00574a6712f6a36b265e82df58bca396b81d05546fa0f8c1de9d9d2ccc4c3eb.
No mutation survived except the historical initial author-priority probe already
disclosed and corrected. Test setup moved after these mutations; it changes no
runtime guard. No denied call, stop/kill/retry variant or shared helper changes.

## Final focused gates

All commands ran from C:/fks/r2bridge. PYTHONPATH=tests,
FKS_ENGINES=chromium and FKS_REQUIRE_FIXTURES=1 for focused acceptance:

    python -m unittest test_role_protocol test_role_detection test_r2_static_fixtures test_bridge_runtime.HandshakeTests test_support -v

Initial freeze:60 tests,95.811s,OK,no skips. Final continuation gate:67 tests,130.398s,OK,no skips,exit0.
New role modules independently passed14 tests,
75.092s before the final visibility-edge addition to that population test.
Final legacy command (18 tests,15.860s,OK,exit0):

    python -m unittest test_bridge_runtime.ConfirmedDefectTests test_bridge_runtime.HandshakeTests test_bridge_runtime.SessionLifecycleTests test_bridge_runtime.TargetedUpdateTests.test_reset_one_target_or_everything test_bridge_runtime.SelectionTests test_bridge_runtime.LegacyCompositionTests -v

Production-plugin characterization: two Node tests, 0 failures/skips.

    python scripts/verify.py --static-only
    node --check fontkit-bridge.js
    python -m ruff check tests/test_role_protocol.py tests/role_support.py tests/test_role_detection.py tests/test_bridge_runtime.py
    git diff --check
    git diff --cached --check

All exit0. Static checks:96 unique IDs, inline JS syntax, provenance PASS;
explicit SKIP unittest/browser tests for static-only is not suite acceptance.
Ruff: All checks passed. Git only warns existing autocrlf conversion on tracked
files; new authored files are UTF-8/LF. No staged changes. Report and patch reflect all restored source.
The separate legacy command overlapped the beginning of the final focused run;
it completed before the final5000 test. No source mutation occurred in either.
Full suite, full package build/tests, frontend gate and Firefox were not run;
the settled-wave controller/gate runner owns those. No npm installs or builds.

## Cleanup, resolved contract and AP review

All browser invocations exited normally; fresh contexts use addCleanup(context.close)
and the process-wide shared runtime. Blank canary closes in finally. No server,
Vite process, output tree, new scratch copy or additional browser driver started.
No invocation needed interruption/reaping in this detection task. No denied call.
Previous F2a ignored-copy/denied-deletion history belongs to its report; this task
did not delete or modify those copies. Seven owned paths only remain dirty.

AP1/2: source/origin/protocol/session checks and pinned post origin preserved.
AP3/4: no untrusted markup/URL sink introduced; owned HTML injection is literal
external script and preserves CSP. AP5/6: read-only detection, no silent replay,
no new original capture. AP7/8/9: observers attach after valid hello; detect
exercised; generation cancellation and repeated hello tested. AP10/11/12: no
personal defaults or legacy protocol renames, duplicated grammar intentional
per binding boundary. AP13/14/15: owned cleanup, engines/gates accurately scoped,
product-facing commit draft contains no process state.

Resolved URL contract: approved Addendum5/D061 preserves capability/legacy
inspector with authenticated ready null, rejects initial Detect safely and emits
only captured valid/current null stale evidence with empty vectors. Actual raw
URL continues internal epoch comparison. Exact boundary and recovery tests pass.

Remaining platform limits: CSS-rule freshness stamping synchronously enumerates
readable stylesheet text before each8ms generator slice; this JavaScript work is
included in the overall2000ms clock but is not itself yielded. Native layout/
query/serialization also cannot be preempted. Normal first5000 responsiveness is
proved; no claim of a strict8ms adversarial stylesheet bound. Full rule-heavy
stress, continuously changing animation, opaque cross-origin stylesheet changes
and universal atomic rendered snapshots were not characterized. The confirmed
native focus stale-complete case is fixed and independently mutation-proved;
these remaining source/platform risks stay candid for independent review.

## Material counts and controller drafts

Patch parses as standard Git unified diff, including all untracked new files,
without staging. git apply --stat (read-only): seven files,1191 insertions,
2 deletions; material1193. No generated lock/vendor churn. Patch1306 lines;
SHA-256 9b19621ca10f3b660667962107dca12acf75881a8f4afda8c7c8f3ff2353f4b1.
No root application. This full report is additional material if promoted to records.

Draft CHANGELOG: Add read-only typography role detection with exact style groups,
safe bindings and explicit incomplete or stale results. Keep the existing
inspector available when a route cannot be represented safely for role detection.
Draft ledger: R2.1/R2.2 add authenticated read-only role measurement and bounded
cooperative checks. Link task report/review; record final67 Chromium tests/counts,
initial and continuation RED/GREEN/first measurements, 16 restored guard mutations
and Addendum5 URL behavior. Do not mark plan boxes completed until independent
implementation review approves; controller owns all shared records.
Draft commit subject:
feat(bridge): detect rendered typography roles without changing the page
Draft why-body:
Typography varies across semantic elements and framework classes.
Measure direct-text parents with exact identities and safe bindings so
Studio can offer roles without accepting partial or stale evidence.
Bound background work while preserving existing inspector edits.

Exact future focused CI command is the 67-test command above with PYTHONPATH=tests,
FKS_ENGINES=chromium and FKS_REQUIRE_FIXTURES=1. No new dependency/install step is
needed. Full settled-wave gate commands remain those in constraints.md; no CI,
Firefox canary or shared test-support changes were made.

## Late native-state correction (2026-10-08)
The original candidate's early-focus freshness claim is superseded by this
correction and the independent late-window finding. Independent acceptance
is still pending; the initial results above remain historical evidence.

Date: 2026-10-08. Detached worktree C:/fks/r2bridge, unchanged BASE
6a7327bd2d901f4c668c476a8048658f82c682b6. Source frozen; final focused gate passed: 72 tests in193.291s,exit0,no skips.
Independent scoped review remains required. Original
[original candidate report](r2-task-2-report.md) and original full patch are
preserved, including initial131.3ms responsiveness failure, corrected136.8ms,
all earlier RED/GREEN/limits/URL/cancellation/mutation and cleanup evidence.
Read the full current ROOT producer brief and durable independent review
(docs/implementation/tasks/r2-task-2-review.md, Changes required) before edits.

## Fix and evidence boundary

Only fontkit-bridge.js and tests/test_role_detection.py differ from the original
seven-path freeze. Eight runtime lines attach passive capture listeners after
valid hello: focusin/out, pointerover/out, pointerdown/up/cancel and keydown/up.
Runtime guard: fontkit-bridge.js:1049; native cases/helper: tests/test_role_detection.py:88.
Keyboard invalidation is filtered to Space/Enter on button controls; ordinary
textbox input and keys remain excluded. Native state changes advance pageVersion
through the whole job lifetime, including after a completed scan. Existing
listen/dispose cleanup handles ownership; no event default is intercepted.
The second rendered pass alone had a yielding late window; another pass was not
added. All earlier session/authentication/cancellation and Addendum5/D061 shapes
are unchanged. No universal animation/platform tracking claim.

Tier2 MCP status reconfirmed ready2637/12760; generation2026-10-07T17:07:14Z.
All seven paths plus current brief/review coverage checked: metadata_changed or
not_tracked; fixtures/docs excluded, no recorded parser gap. Current source and
public browser behavior are authority; no fresh detector graph proof claimed.
Before edits, original seven canonical hashes and exact bytes were saved in
ignored original byte snapshot (`.superpowers/sdd/r2/detection-late-fix-snapshot.json`).

## Native RED/GREEN

Each case uses real bridge, authored CSS before hello, existing fixture heartbeat,
public authenticated Detect and native controls. Separate style-only and
eligibility-only focus cases retain computed rendering, literal text, unchanged
main DOM, revision0/no page errors, later stable counts/tuples and public epochs.

| Genuine RED stimulus | Native delay / complete elapsed | Current rendering / stale epoch |
|---|---|---|
| Focus, style only,16beats |309.7 /541.1ms|35px,complete old20px;0/0|
| Focus, eligibility only,16beats |312.3 /502.8ms|hidden g00,complete5000;0/0|
| Pointerdown already hovered/focused,16beats |275.5 /469.5ms|35px,complete old20px;2/2|
| Space on already focused empty button,20beats |345.2 /506.2ms|35px,complete old20px;1/1|

Focus RED:2tests9.094s; pointer RED:1test4.325s; Space RED:1test4.654s.
Earlier Space16beats was truthfully GREEN through rendered revalidation
(278.7/310.5ms,page-changed); no fabricated keyboard RED. Enter20beats before
the keyboard guard retained actual20px/complete20px250 evidence,505.3ms,epoch1/1;
native held Enter did not retain :active in this Chrome probe. No Enter RED claim.

Initial focus fix GREEN4tests50.072s, including cancellation matrix and FIRST5k
521ms,heartbeat135->141,inputx before completion. After pointer addition and
exact UTF-8 restoration,4tests18.459s: style309.9/312.2ms,eligibility292.2/294.2ms,
pointer273/298.5ms,all page-changed/advanced epoch; FIRST5k546.5ms,183->188,inputx.
Keyboard-inclusive5tests22.644s GREEN: Space353.1/374.7ms,epoch1->2; FIRST5k
495.4ms,125->130,inputx. Hover/pointerup/Spaceup characterization1test14.845s GREEN
with real35->20px release and advanced epochs. Direct native mouse.move replaced
locator.hover actionability delay; characterized1test13.503s GREEN.

Robust final scoped7tests67.103s GREEN; FIRST5k507.8ms,140->145,inputx before reply.
No warm-up-only acceptance, unchanged retries until pass, forced delays or changed
2000ms/8ms/duplicate thresholds. These measurements supplement original history.
Final focused FIRST5k:523ms,heartbeat135->141,inputx acknowledged before reply,
complete5000 with all20 literal groups/bindings and author main unchanged.

## Timing quality and restored mutations

Public detect timestamps now capture before the real bridge's bubble handler.
A native event at least30ms before completion cannot certify old rendering.
A scan that correctly finishes before a fixed16/20beat stimulus is accepted only
with exact pre-event literal serif/20px (or held35px) tuple250 and count5000.
Every case additionally changes native state after a stable completed scan,
asserts actual opposite rendering and an advanced authenticated ready epoch BEFORE
another stable Detect. No minimum scan duration or private-method hooks.

First mutation set: focus8.968s(two stale failures), pointer18.132s(down/up stale),
keyboard18.483s(Space down/up stale). Initial hover13.299s failed timing only:
locator delay427.7ms followed already-finished419.1ms; not stale-evidence proof.
Direct-hover attempt11.436s had a delivery-gap-scale279.1/279.2ms complete plus
another case's legitimate earlier completion324.1ms; not accepted as strong proof.
Capture-phase start,30ms margin and public post-completion epochs correct these
premises without slowing detection. These failed premises remain disclosed.

Final ordinary foreground mutations, exact restoration in finally:

| Removed native guard group | Independent >30ms stale failure / test duration |
|---|---|
| Focus |317.4/547.9ms and309.3/495.3ms;2tests9.300s|
| Hover |273.5/439.7ms;1test21.541s|
| Pointer activation |281/503ms;1test4.532s|
| Button keyboard |337.8/506.2ms;1test4.613s|

All four exit1 for actual stale evidence, not pending preconditions. Exact restored
bridge SHA25608fcdf50f350a9bbfd6fadbc5e7a9cedd637bccdf47cac76070f5580eac8896e.
Earlier release mutations also prove pointerup285.7/515.7ms and Spaceup337.5/510.4ms
stale complete. Guard groups cover both transitions; no shared helper edits.

Corrections retained: initial test used wrong nested g00 text (2tests9.315s failed
literal), corrected from readonly app.js before genuine RED. Default Windows
text decoding altered non-ASCII bytes; the next edit errored and its command then
tested unchanged focus-only code (4tests17.803s,activation stillRED). Original
UTF-8 bytes were restored from the snapshot and only8 lines reapplied; DELTA proves
no unrelated churn. Enter probe initially lacked PYTHONPATH (no browser launched);
correct environment probe exited0. Initial MCP call lacked project and attempted
stdout snapshot JSON truncated; corrected status and durable byte snapshot precede
all source edits. No denial or alternate-tool retry.

Pre-robustness72test gate162.659s failed solely because the OLD early-focus test
checked no reply AFTER focus: correct page-changed51.7ms/epoch1 had arrived.
Pending observation moved BEFORE focus; rendered/typing/version assertions remain.
That run's FIRST5k501.3ms,157->162,inputx passed. Final gate below follows this
scoped test correction and robustness changes, not an unchanged retry.

## Final commands, cleanup and handoff

From C:/fks/r2bridge, PYTHONPATH=tests,FKS_ENGINES=chromium,FKS_REQUIRE_FIXTURES=1:

    python -m unittest test_role_protocol test_role_detection test_r2_static_fixtures test_bridge_runtime.HandshakeTests test_support -v

Final result: 72 tests in193.291s,OK,exit0,no skips,Chromium only. No future-operation skips. Static96IDs/inlineJS/provenance
PASS (explicit static-only browser SKIP); node --check bridge, exact four owned
Python Ruff files,git diff --check and cached diff--check all exit0 after freeze.

    python scripts/verify.py --static-only
    node --check fontkit-bridge.js
    python -m ruff check tests/test_role_protocol.py tests/role_support.py tests/test_role_detection.py tests/test_bridge_runtime.py
    git diff --check
    git diff --cached --check

Full wave/frontend/Firefox/package/commit gates not run; controller owns them.
Original legacy18/production2 results remain in the original report, not rerun here.
All completed browser invocations exited normally,contexts closed; canaries keep
permanent HTTPS local fallback. Native held buttons/keys have owned cleanup before
context close. No server/new driver/process kill/stage/commit/push/spawn/root source
edit/application. Snapshot retained; no rejected deletion retry. AP checks remain
original; passive invalidation preserves native input, auth and read-only author DOM.
Synchronous CSS stamping/rule-heavy/continuous-animation limits remain unchanged.

DELTA only against original frozen candidate:2files,138adds/1delete,139material,
167patch lines,0vendor/lockchurn. ignored delta patch (`.superpowers/sdd/r2/detection-late-fix.patch`)
SHA256b9360030f70856e2c87f3c90e6759523d46ead90235e491eaf8099ab094c92e9.
Do not reapply original full6a patch to ROOT. Controller may verify/copy updated
owned files using canonical manifest below; independent scoped re-review pending.
Draft ledger: native-state invalidation spans cooperative measurement; record
actual REDs, final counts/first benchmark and restored guard proof; task stays
unchecked until approved. Draft CHANGELOG: preserve read-only detection accuracy
across native focus/hover/activation. Draft commit subject:
fix(bridge): invalidate typography measurements on native state changes
Why: Native interaction can change earlier measured text while a job yields.
Advance its page generation so stale tuples cannot become checked evidence.
Exact future focused command remains above; no new module/install/CI step.

## Canonical LF manifest

fontkit-bridge.js
fbd85d8a84c0e158b2fb8df0740139033b4483f862cd94370522095995780839 -> 08fcdf50f350a9bbfd6fadbc5e7a9cedd637bccdf47cac76070f5580eac8896e
tests/test_role_protocol.py
f1dcf4d6a70fdfe507856ee033a088455b005980af1776f7b55be4d32264545b -> f1dcf4d6a70fdfe507856ee033a088455b005980af1776f7b55be4d32264545b
tests/role_support.py
2072867e6e195ee9abd1faf0542364b4cdf4ce4697f5f8e1c1ae11c3e2146e10 -> 2072867e6e195ee9abd1faf0542364b4cdf4ce4697f5f8e1c1ae11c3e2146e10
tests/fixtures/bridge/host-roles.html
f00574a6712f6a36b265e82df58bca396b81d05546fa0f8c1de9d9d2ccc4c3eb -> f00574a6712f6a36b265e82df58bca396b81d05546fa0f8c1de9d9d2ccc4c3eb
tests/fixtures/bridge/target-role-protocol.html
fea2df27fd5d6a6aa26d3fc230fc39ff5b78c7a0e108e695c4335d96c871d2f5 -> fea2df27fd5d6a6aa26d3fc230fc39ff5b78c7a0e108e695c4335d96c871d2f5
tests/test_role_detection.py
14e637fc02265edb3c2d7fccf01da11b218d45a2a1e22963a79056bd022e1e83 -> 449cc67fc2817775d606dd34211b4caa7db279dc321efdbdd98896eefe75c38d
tests/test_bridge_runtime.py
0215412c6a0668060a1c247fb5a7cef0f30e2a09c5b026dff1aa53b035dabed2 -> 0215412c6a0668060a1c247fb5a7cef0f30e2a09c5b026dff1aa53b035dabed2
