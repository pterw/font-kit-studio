"""Role detection's real cross-origin request boundary."""
import json
import subprocess

from support import ENGINES
from role_support import EVIL, REPO, STUDIO, ROLE_PAGE, RoleBridgeCase


class RoleProtocolTests(RoleBridgeCase):
    def test_final_wire_payload_stays_bounded_near_exact_utf8_reply_limit(self):
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
                    self.assertEqual(page.evaluate('roleState'), ready['roleState'])
                    self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                    self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')

    def test_unavailable_actual_url_preserves_inspector_and_recovers_at_exact_boundary(self):
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
                self.assertEqual(blocked.evaluate('messages("design:bridge-ready")'), [])

    def test_detect_authentication_and_matching_revision_ignore_hostile_traffic(self):
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
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                self.assertTrue(ready['capabilities']['roleDetection'])
                self.assertNotIn('roleStylesheet', ready['capabilities'])
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
