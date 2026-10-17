"""Role detection's real cross-origin request boundary."""
import json
import subprocess

import role_contract as table
from support import ENGINES
from role_support import EVIL, REPO, STUDIO, ROLE_PAGE, TARGET, RoleBridgeCase
from test_role_stylesheet import RoleSheetCase, role


class RoleProtocolTests(RoleBridgeCase):
    def test_final_wire_payload_stays_bounded_near_exact_utf8_reply_limit(self):
        """Given 128 roles of 32 selectors, when detect replies near the 1 MiB limit, then no complete reply exceeds it and the page still renders 16px."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                roles = [{'id': str(i).zfill(30), 'selectors': ['.body-copy'] * 32} for i in range(128)]
                measured = self.detect(page, requestId='wire', knownRoles=roles)
                self.assertTrue(measured['complete'], {k: v for k, v in measured.items() if k not in ('groups', 'selectorChecks')})
                def wire_size(reply):
                    return len(json.dumps(reply, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))
                # Calibration measures framing bytes, not style tuples or an engine limit decision.
                # Each added ID byte appears in exactly 32 selector records; request ID pads by one byte.
                extra = (1024 * 1024 - 100 - wire_size(measured)) // 32
                for i, role in enumerate(roles):
                    role['id'] = str(i).zfill(30 + extra // 128 + (i < extra % 128))
                    self.assertLessEqual(len(role['id']), 100)
                complete_sizes, rejected = [], 0
                for padding in range(1, 201, 8):
                    reply = self.detect(page, requestId='r' * padding, knownRoles=roles)
                    self.assertLessEqual(wire_size(reply), 1024 * 1024)
                    if reply['complete']:
                        complete_sizes.append(wire_size(reply))
                        self.assertEqual(reply['selectorChecks'][0]['matchCount'], 2)
                    else:
                        self.assertEqual(reply['reason'], 'reply-limit')
                        rejected += 1
                self.assertGreater(rejected, 0)
                self.assertLess(1024 * 1024 - max(complete_sizes), 64)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')

    def test_correlated_hostile_url_receipts_cannot_advance_receiver_state(self):
        """Given a hostile matching receipt with a foreign, credentialed or null URL, when the real detect runs, then the receiver ignores it and takes the bridge's own reply."""
        for engine in ENGINES:
            for hostile in ('http://evil.test/path', 'http://alice:secret@target.test/path', None):
                with self.subTest(engine=engine, url=hostile):
                    page, frame = self.open(engine)
                    ready = self.hello(page)
                    frame.evaluate("""url => addEventListener('message', function spoof(event) {
                        if (event.data.type !== 'design:detect') return;
                        removeEventListener('message', spoof, true);
                        parent.postMessage({type:'design:detected',protocolVersion:1,sessionId:event.data.sessionId,
                            requestId:event.data.requestId,revision:999,documentId:event.data.documentId,
                            pageVersion:0,currentPageVersion:0,pageURL:url === null ? location.href : url,currentPageURL:url,
                            complete:true,reason:null,elapsedMs:1,scannedElements:0,groups:[],selectorChecks:[]}, event.origin);
                    }, true)""", hostile)
                    reply = self.detect(page)
                    self.assertEqual(reply['revision'], 0, reply)
                    self.assertEqual(reply['scannedElements'], 2)
                    self.assertEqual(page.evaluate('revision'), 0)
                    again = self.hello(page)
                    self.assertEqual((again['roleState'], again['revision']), (ready['roleState'], 0))
                    self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                    self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')

    def test_unavailable_actual_url_preserves_inspector_and_recovers_at_exact_boundary(self):
        """Given a real 2,001-character route, when detect, inspector edit and reset run, then detect is refused, the inspector works and the exact 2,000 route recovers."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                path = '/tests/fixtures/bridge/target-role-protocol.html'
                page, frame = self.open(engine, target=ROLE_PAGE + '?' + 'x' * (2000 - len(path)))
                self.assertEqual(frame.evaluate('location.pathname.length + location.search.length + location.hash.length'), 2001)
                ready = self.hello(page)
                self.assertIsNone(ready['roleState']['pageURL'])
                self.assertTrue(ready['capabilities']['roleDetection'])
                self.assertEqual((ready['roleState']['roles'], ready['roleState']['canonicalCss'], ready['roleState']['cssHash']),
                                 ([], '', '811c9dc5'))
                before = frame.locator('main').evaluate('el => el.outerHTML')
                rejected = self.detect(page)
                self.assertEqual((rejected['type'], rejected['reason']), ('design:rejected', 'unsupported-value'))
                self.assertEqual(rejected['detail'], 'Unsupported page URL')
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.update(page, 'ordinary.body', {'fontSize': 27})
                self.assertEqual(frame.locator('[data-design-id="ordinary.body"]').evaluate('el => getComputedStyle(el).fontSize'), '27px')
                self.request(page, {'type': 'design:reset'})
                self.assertEqual(frame.locator('[data-design-id="ordinary.body"]').evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertIsNone(self.hello(page, 'unsupported-again')['roleState']['pageURL'])
                prior_version = page.evaluate('roleState.pageVersion')
                frame.evaluate("() => history.replaceState(null, '', '/?' + 'y'.repeat(1999))")
                another = self.hello(page, 'unsupported-changed')['roleState']
                self.assertIsNone(another['pageURL'])
                self.assertGreater(another['pageVersion'], prior_version)
                frame.evaluate("() => history.replaceState(null, '', '/?' + 'x'.repeat(1998))")
                self.assertEqual(frame.evaluate('location.pathname.length + location.search.length + location.hash.length'), 2000)
                supported = self.hello(page, 'supported')['roleState']
                self.assertEqual(supported['pageURL'], frame.url)
                self.assertTrue(self.detect(page)['complete'])
                self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')

    def test_native_invalid_numeric_selectors_reject_and_escaped_forms_measure_rendering(self):
        """Given selectors .1 and #1, when sent, then they reject while the escaped forms match the rendered paragraph."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.locator('[data-design-id="ordinary.body"]').evaluate("el => {el.id='1'; el.classList.add('1');}")
                self.hello(page)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                for selector in ('.1', '#1'):
                    reply = page.evaluate("selector => request({type:'design:detect',knownRoles:[{id:'numeric',selectors:[selector]}]}, 200)", selector)
                    self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', 'unsupported-value'), reply)
                    self.assertEqual(self.errors(frame), [])
                    self.assertEqual(page.evaluate('revision'), 0)
                    self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                    self.assertTrue(self.detect(page)['complete'])
                escaped = self.detect(page, knownRoles=[{'id': 'numeric', 'selectors': [r'.\31 ', r'#\31 ']}])
                self.assertTrue(escaped['complete'], escaped)
                self.assertEqual([s['matchCount'] for s in escaped['selectorChecks']], [1, 1])
                self.assertEqual(frame.locator(r'#\31 ').inner_text(), 'Ordinary body')
                self.assertEqual(frame.locator(r'.\31 ').evaluate('el => getComputedStyle(el).fontSize'), '16px')

    def test_unsupported_old_bridge_and_script_csp_remain_truthful(self):
        """Given an old bridge or a script-blocking policy, when Studio connects, then no role capability appears and the page still renders its own styles."""
        old = subprocess.check_output(['git', 'show', '6a7327bd:fontkit-bridge.js'], cwd=REPO)
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, bridge_source=old)
                ready = self.hello(page)
                self.assertNotIn('roleDetection', ready['capabilities'])
                self.assertNotIn('roleState', ready)
                reply = page.evaluate('() => request({type:"design:detect",documentId:"unavailable"}, 100)')
                self.assertEqual(reply['type'], 'timeout')
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(self.update(page, 'ordinary.body', {'fontSize': 23})['type'], 'design:applied')
                self.assertEqual(frame.locator('[data-design-id="ordinary.body"]').evaluate('el => getComputedStyle(el).fontSize'), '23px')
                blocked, target = self.open(engine, headers={'content-security-policy': "script-src 'none'"})
                self.assertFalse(target.evaluate('Boolean(window.__fontkitBridge)'))
                self.assertEqual(target.locator('.body-copy').first.inner_text(), 'Author body')
                self.assertEqual(target.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(blocked.evaluate("log.filter(e => e.fromTarget && e.data && e.data.type === 'design:bridge-ready')"), [])

    def test_detect_authentication_and_matching_revision_ignore_hostile_traffic(self):
        """Given hostile detects from a wrong session, protocol, script or foreign frame, when a real
        detect runs, then no hostile reply appears in the Studio host log and the page is unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                start = self.mark(page)
                page.evaluate("""() => {
                    const detect = {type:'design:detect', protocolVersion:1, sessionId, requestId:'hostile',
                                    documentId:roleState.documentId, knownRoles:[]};
                    send({...detect, sessionId:'wrong'}); send({...detect, protocolVersion:2});
                }""")
                # Same-origin target script is a different source window; an evil-origin child is both wrong.
                frame.evaluate("""() => postMessage({type:'design:detect',protocolVersion:1,sessionId:'s1',
                    requestId:'hostile',documentId:__fontkitBridge.documentId,knownRoles:[]}, location.origin)""")
                with page.expect_event('framenavigated', predicate=lambda f: f.url.startswith(EVIL)) as navigation:
                    page.evaluate("""url => {
                        const child = document.createElement('iframe'); child.src = url; document.body.appendChild(child);
                    }""", EVIL + '/host-roles.html?target=' + frame.url)
                evil = navigation.value
                evil.evaluate("""([doc, origin]) => parent.frames[0].postMessage({type:'design:detect',
                    protocolVersion:1,sessionId:'s1',requestId:'hostile',documentId:doc,knownRoles:[]}, origin)""",
                    [ready['roleState']['documentId'], frame.url.split('/tests/')[0]])
                # Hostile ready/applied/detected receipts cannot advance helper revision.
                page.evaluate("""() => postMessage({type:'design:applied',protocolVersion:1,
                    sessionId,requestId:'unknown',revision:999}, location.origin)""")
                frame.evaluate("""studio => parent.postMessage({type:'design:applied',protocolVersion:1,
                    sessionId:'s1',requestId:'unknown',revision:999}, studio)""", STUDIO)
                reply = self.detect(page)
                self.assertTrue(reply['complete'], reply)
                self.assertEqual(page.evaluate('revision'), 0)
                self.assertFalse([m for m in self.messages(page, 'design:detected', start) if m['requestId'] == 'hostile'])
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')

    def test_reload_issues_new_document_and_unknown_identity_cannot_replace_ready(self):
        """Given a reload, when the old document ID is sent, then it is page-changed and the new ready identity stays."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                old = self.hello(page)['roleState']['documentId']
                self.update(page, 'ordinary.body', {'fontSize': 24})
                self.assertEqual(frame.locator('[data-design-id="ordinary.body"]').evaluate('el => getComputedStyle(el).fontSize'), '24px')
                frame.goto(frame.url)
                ready = self.hello(page, 's2')
                current = ready['roleState']['documentId']
                self.assertNotEqual(current, old)
                reply = self.detect(page, documentId=old)
                self.assertEqual(reply.get('reason'), 'page-changed')
                self.assertEqual(page.evaluate('roleState.documentId'), current)
                self.assertTrue(self.detect(page)['complete'])
                self.assertEqual(frame.locator('[data-design-id="ordinary.body"]').evaluate('el => getComputedStyle(el).fontSize'), '16px')

    def test_ready_identity_and_exact_hostile_requests_preserve_rendered_author_state(self):
        """Given a ready bridge, when each malformed detect arrives, then it is rejected with its reason and the page and revision are unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                self.assertTrue(ready['capabilities']['roleDetection'])
                self.assertTrue(ready['capabilities']['roleStylesheet'])
                state = ready['roleState']
                self.assertEqual(state, {'documentId': state['documentId'], 'pageVersion': 0,
                    'pageURL': frame.url, 'roles': [], 'canonicalCss': '',
                    'hashAlgorithm': 'fnv1a32', 'cssHash': '811c9dc5'})
                before = frame.locator('main').evaluate('el => el.outerHTML')
                cases = [({'surprise': True}, 'invalid-message'),
                         ({'constructor': {}}, 'invalid-message'),
                         ({'__proto__': {}}, 'invalid-message'),
                         ({'prototype': {}}, 'invalid-message'),
                         ({'baseRevision': 0}, 'invalid-message'),
                         ({'pageURL': 'http://evil.test/path'}, 'invalid-message'),
                         ({'pageURL': 'http://alice:secret@target.test/path'}, 'invalid-message'),
                         ({'documentId': 'unknown-document'}, 'page-changed'),
                         ({'requestId': ''}, 'invalid-message'),
                         ({'knownRoles': {}}, 'invalid-message'),
                         ({'knownRoles': [[]]}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': [float('nan')]}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'x' * 101, 'selectors': []}]}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['p'] * 33}]}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': []}] * 129}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['p'], 'prototype': {}}]}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['p']}] * 2}, 'invalid-message'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['.body-copy, p']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'body', 'selectors': [':root']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['html']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['p:nth-of-type(10000)']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['.body-copy/*x*/']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': 'body', 'selectors': ['p[data-anything="x"]']}]}, 'unsupported-value'),
                         ({'knownRoles': [{'id': str(i), 'selectors': ['.' + 'x' * 1999] * 32}
                                         for i in range(5)]}, 'size-limit')]
                for fields, reason in cases:
                    with self.subTest(fields=str(fields)[:100]):
                        reply = (page.evaluate('raw => request(JSON.parse(raw))',
                                               json.dumps({'type': 'design:detect', **fields}))
                                 if '__proto__' in fields else self.detect(page, **fields))
                        self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', reason), reply)
                        self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                        self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                        self.assertEqual(page.evaluate('revision'), 0)

    def test_valid_detect_returns_literal_rendered_baseline_without_author_changes(self):
        """Given the literal fixture, when detect runs, then it reports the rendered 16px baseline and leaves the author DOM unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                reply = self.detect(page)
                self.assertEqual(reply['type'], 'design:detected', reply)
                self.assertTrue(reply['complete'], reply)
                self.assertEqual(reply['scannedElements'], 2)
                self.assertEqual([g['elementCount'] for g in reply['groups']], [1, 1])
                self.assertEqual(reply['groups'][0]['signatures'], [{'style': {
                    'fontFamily': 'sans-serif', 'fontSize': 16, 'fontWeight': 400,
                    'textTransform': 'none', 'letterSpacing': 0}, 'count': 1}])
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(page.evaluate('revision'), 0)


# Pages for the contract table's bridge extremes, built with frame.evaluate after open and before hello.
# STYLE_GRID: `count` distinct styles (columns weights x the rest sizes, so every group is near the others). Style 0 is 32 elements
# whose data-design-id values make each selector `pad + 19` long; style 1 is one element with the given classes and text.
STYLE_GRID = """([count, columns, pad, classes, long]) => {
  const main = document.querySelector('main'); main.replaceChildren();
  for (let i = 0; i < count; i++) for (let k = 0; k < (i === 0 ? 32 : 1); k++) {
    const p = document.createElement('p'); p.textContent = i === 1 ? long : 'Style ' + i;
    p.style.fontSize = (16 + Math.floor(i / columns) / 100) + 'px'; p.style.fontWeight = String(400 + i % columns);
    if (i === 0) p.setAttribute('data-design-id', ('i' + k + '-').padEnd(pad, 'x'));
    if (i === 1) p.className = classes.join(' ');
    main.appendChild(p);
  }
}"""
# AUTHOR_ROLES: `roles` author roles of `variants` sizes each, every element with class k.
AUTHOR_ROLES = """([roles, variants]) => {
  const main = document.querySelector('main'); main.replaceChildren();
  for (let r = 0; r < roles; r++) for (let v = 0; v < variants; v++) {
    const p = document.createElement('p'); p.textContent = 'R' + r + ' V' + v; p.className = 'k';
    p.setAttribute('data-design-role', 'Role ' + r); p.style.fontSize = (10 + v * 2 + r / 10) + 'px'; main.appendChild(p);
  }
}"""
# WINNERS: `count` paragraphs of class t, each with its own author rule p.eN that sets all six properties.
WINNERS = """(count) => {
  const style = document.createElement('style'); const main = document.querySelector('main');
  for (let i = 0; i < count; i++) {
    style.textContent += `p.e${i} { font-size: 18px; font-weight: 300; line-height: 2; letter-spacing: 1px; text-transform: lowercase; font-family: monospace; }`;
    const p = document.createElement('p'); p.className = 't e' + i; p.textContent = 'Lost ' + i; main.appendChild(p);
  }
  document.head.appendChild(style);
}"""


# POSTED_BYTES: records the UTF-8 JSON size of every message the host page posts to the bridge, by wrapping its `send`.
POSTED_BYTES = """() => {
  window.postedBytes = []; const post = window.send;
  window.send = (msg) => { window.postedBytes.push(new TextEncoder().encode(JSON.stringify(msg)).length); return post(msg); };
}"""


class RoleContractTableTests(RoleSheetCase):
    """The real bridge driven to its reachable extremes against tests/role_contract.py."""

    def test_a_complete_scan_at_every_limit_posts_only_values_the_table_allows(self):
        """Given 128 distinct styles that are all near each other, a group of 32 elements with 2,000-character selectors, one
        element with 20 classes (one of 201 characters, one of 200) and a 300-character text, and 128 known roles of 32 selectors,
        when Studio detects, then the reply is complete with 128 groups and 4,096 checks, reaches each limit and the table finds
        no violation."""
        classes = [table.text(table.CLASS_CHARS + 1, 'L')] + table.class_names(1, table.CLASS_CHARS) + table.class_names(table.SHARED_CLASSES + 2, 8)
        known = [{'id': f'role-{i}', 'selectors': table.selectors(table.SELECTORS)} for i in range(table.ROLES)]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(STYLE_GRID, [table.ROLES, table.ROLES // table.VARIANTS, table.SELECTOR_CHARS - len('[data-design-id=""]'),
                                            classes, table.text(table.SAMPLE_CHARS + 100, 'S')])
                self.hello(page)
                reply = self.detect(page, knownRoles=known)
                groups = reply['groups']
                self.assertEqual((reply['complete'], len(groups), len(reply['selectorChecks'])), (True, table.ROLES, table.SELECTOR_CHECKS))
                self.assertEqual(max(len(g['nearDuplicateIds']) for g in groups), table.NEAR_DUPLICATES)
                self.assertEqual(max(len(g['selectors']) for g in groups), table.SELECTORS)
                self.assertEqual(max(len(b['value']) for g in groups for b in g['selectors']), table.SELECTOR_CHARS)
                self.assertEqual(max(len(g['sharedClasses']) for g in groups), table.SHARED_CLASSES)
                self.assertEqual(max(len(c) for g in groups for c in g['sharedClasses']), table.CLASS_CHARS)
                self.assertEqual(max(len(g['sampleText']) for g in groups), table.SAMPLE_CHARS)
                self.assertEqual(table.violations('detected', reply), [])

    def test_one_style_past_the_group_limit_stops_the_scan_at_128_groups_with_the_sample_cut(self):
        """Given 129 distinct styles and a 300-character text, when Studio detects, then the reply is incomplete with group-limit,
        carries 128 groups and a sample cut to 200 characters, and the table finds no violation; the scan stops before bindings,
        so only the group count and the sample text are reached."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(STYLE_GRID, [table.ROLES + 1, table.ROLES // table.VARIANTS, 100, [], table.text(table.SAMPLE_CHARS + 100, 'S')])
                self.hello(page)
                reply = self.detect(page)
                self.assertEqual((reply['complete'], reply['reason'], len(reply['groups'])), (False, 'group-limit', table.ROLES))
                self.assertEqual(max(len(g['sampleText']) for g in reply['groups']), table.SAMPLE_CHARS)
                self.assertEqual(table.violations('detected', reply), [])
                self.assertEqual({g.get('adapter') for g in reply['groups']} - set(table.ADAPTERS), set())

    def test_one_variant_past_the_limit_stops_the_scan_and_every_group_still_carries_an_adapter(self):
        """Given one author role of 9 sizes, when Studio detects, then the reply is incomplete with variant-limit and every
        group it carries has an adapter the table lists."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(AUTHOR_ROLES, [1, table.VARIANTS + 1])
                self.hello(page)
                reply = self.detect(page)
                self.assertEqual((reply['complete'], reply['reason']), (False, 'variant-limit'))
                self.assertTrue(reply['groups'])
                self.assertEqual({g.get('adapter') for g in reply['groups']} - set(table.ADAPTERS), set())
                self.assertEqual(table.violations('detected', reply), [])

    def test_a_bootstrap5_detect_posts_adapters_the_table_lists_and_at_least_one_is_not_plain(self):
        """Given the Bootstrap 5 fixture, when Studio detects, then the reply is complete, every group's adapter is one the table
        lists, at least one is not plain and the table finds no violation."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/bootstrap5-static/index.html')
                self.hello(page)
                reply = self.detect(page)
                self.assertTrue(reply['complete'], reply['reason'])
                adapters = {g.get('adapter') for g in reply['groups']}
                self.assertEqual(adapters - set(table.ADAPTERS), set())
                self.assertTrue(adapters - {'plain'}, adapters)
                self.assertEqual(table.violations('detected', reply), [])

    def test_a_known_selector_over_136_styles_posts_a_check_of_136_signatures_the_table_allows(self):
        """Given 17 author roles of 8 sizes that all carry one class and a known role for that class, when Studio detects, then
        the reply is complete, its one check carries 17 x VARIANTS = 136 signatures and the table finds no violation."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(AUTHOR_ROLES, [17, table.VARIANTS])
                self.hello(page)
                reply = self.detect(page, knownRoles=[{'id': 'k', 'selectors': ['.k']}])
                self.assertTrue(reply['complete'], reply['reason'])
                self.assertEqual([(c['roleId'], len(c['signatures'])) for c in reply['selectorChecks']], [('k', 17 * table.VARIANTS)])
                self.assertEqual(table.violations('detected', reply), [])

    def test_a_maximal_apply_posts_a_receipt_and_role_state_the_table_allows_and_one_role_more_is_rejected(self):
        """Given 128 roles with 100-character ids, 200-character names, 32 selectors, 300-character families, the maximum of every
        number and a 200-character request id, when Studio applies them, then the request as the bridge received it (the bytes its
        host page posts) is within 256 KiB and the receipt, the role state of a second hello and the invalid-message rejection
        of 129 roles all fit the table."""
        maxima = {key: high for key, (_, high, _) in table.NUMBER_RULES.items()}
        roles = [{'id': table.text(table.ROLE_ID_CHARS, f'role-{i}-'), 'name': table.text(table.NAME_CHARS, f'Name {i} '),
                  'selectors': ['.body-copy'] + table.selectors(table.SELECTORS - 1), 'adapter': 'plain',
                  'properties': {'fontFamily': table.text(table.FAMILY_CHARS), **maxima, 'textTransform': 'capitalize'}}
                 for i in range(table.ROLES)]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                page.evaluate(POSTED_BYTES)
                receipt = self.apply(page, roles, timeout=30000, requestId=table.text(table.REQUEST_ID_CHARS))
                posted = page.evaluate('postedBytes')
                self.assertEqual(len(posted), 1)
                self.assertTrue(table.wire(roles) <= posted[0] <= table.REQUEST_BYTES, posted)
                self.assertEqual(receipt['type'], 'design:roles-applied', receipt.get('reason'))
                self.assertEqual((len(receipt['roles']), len(receipt['outcomes'])), (table.ROLES, table.ROLES))
                self.assertEqual(table.violations('roles-applied', receipt), [])
                state = self.hello(page, 's2')['roleState']
                self.assertEqual(len(state['roles']), table.ROLES)
                self.assertEqual(table.violations('role-state', state), [])
                over = self.apply(page, [role(f'r{i}', [f'.s{i}'], fontSize=20) for i in range(table.ROLES + 1)])
                self.assertEqual((over['type'], over.get('reason')), ('design:rejected', 'invalid-message'))
                self.assertEqual(table.violations('rejected', over), [])

    def test_a_stale_base_revision_posts_the_revision_conflict_object_the_table_allows(self):
        """Given a bridge at revision 0, when Studio applies against base revision 7, then the rejection is a revision-conflict
        whose detail is exactly the base revision and the bridge revision, and the table finds no violation."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                stale = self.apply(page, [role(fontSize=20)], baseRevision=7)
                self.assertEqual((stale['type'], stale.get('reason'), stale.get('detail')),
                                 ('design:rejected', 'revision-conflict', {'baseRevision': 7, 'revision': 0}))
                self.assertEqual(table.violations('rejected', stale), [])

    def test_17_winning_author_rules_for_each_property_post_exactly_96_loss_entries_16_for_each_property(self):
        """Given one role over 17 paragraphs whose own author rules win all six properties, when Studio applies it, then the
        receipt counts 17 losers for each property in exactly 96 entries, 16 for each property, and the table finds no violation."""
        mine = {'fontFamily': 'Georgia', 'fontSize': 24, 'fontWeight': 700, 'lineHeight': 1.2, 'letterSpacing': 0.05, 'textTransform': 'uppercase'}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(WINNERS, table.LOSSES_PER_PROPERTY + 1)
                self.hello(page)
                receipt = self.apply(page, [role('t', ['.t'], **mine)])
                losses = receipt['outcomes'][0]['losses']
                self.assertEqual(sum(entry['count'] for entry in losses), len(table.PROPERTY_ORDER) * (table.LOSSES_PER_PROPERTY + 1))
                self.assertEqual(len(losses), table.LOSSES)
                self.assertEqual({prop: sum(1 for entry in losses if entry['property'] == prop) for prop in table.PROPERTY_ORDER},
                                 dict.fromkeys(table.PROPERTY_ORDER, table.LOSSES_PER_PROPERTY))
                self.assertEqual(table.violations('roles-applied', receipt), [])
