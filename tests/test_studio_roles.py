"""Studio's read-only role boundary, with an explicitly authored peer."""
import json
import re
import unittest
from urllib.parse import quote

from support import ENGINES, HTML, REPO, new_context, route_virtual_origins

STUDIO = 'http://studio.test'
TARGET = 'http://target.test'
ROLE_PAGE = TARGET + '/tests/fixtures/bridge/target-role-protocol.html'
UNAVAILABLE = 'Role detection/preview unavailable: unsupported page URL.'
UNSUPPORTED = 'This bridge does not support role detection/preview.'

STYLE = {'fontFamily': 'sans-serif', 'fontSize': 16, 'fontWeight': 400,
         'textTransform': 'none', 'letterSpacing': 0}


def group(group_id='scan-a', name='Body', author='Body', style=None):
    style = style or STYLE.copy()
    return {'id': group_id, 'identity': {'kind': 'author-role', 'name': author} if author else {'kind': 'style', 'style': style},
            'suggestedName': name, 'authorRole': author, 'signatures': [{'style': style, 'count': 1}],
            'elementCount': 1, 'sampleText': 'Peer body', 'sharedClasses': ['body-copy'],
            'selectors': [{'value': '.body-copy', 'stable': True, 'reason': 'class'}],
            'bindingComplete': True, 'nearDuplicateIds': []}


PEER = '''<!doctype html><meta charset="utf-8"><style>.body-copy{font:16px sans-serif}</style>
<p class="body-copy">Peer body</p><script>
window.requests=[];window.session=null;window.host=null;
window.state={documentId:'peer-document',pageVersion:0,pageURL:location.href,roles:[],canonicalCss:'',hashAlgorithm:'fnv1a32',cssHash:'811c9dc5'};
window.send=(body, extra={})=>parent.postMessage({protocolVersion:1,sessionId:session,...body,...extra},host);
window.ready=()=>send({type:'design:ready',revision:0,capabilities:{roleDetection:true},roleState:state,targets:[],changes:{tokens:{},targets:[],structure:[],imports:[]}});
addEventListener('message',e=>{if(e.source!==parent||e.origin!=='http://studio.test')return;
 if(e.data.type==='design:hello'){session=e.data.sessionId;host=e.origin;ready()}
 else if(e.data.type==='design:detect') requests.push(e.data);
});
</script>'''


class StudioRoleCase(unittest.TestCase):
    def open(self, engine, target=ROLE_PAGE, peer=None, viewport=None):
        context = new_context(engine, viewport=viewport or {'width': 1440, 'height': 1100})
        self.addCleanup(context.close)
        route_virtual_origins(context, {STUDIO: REPO, TARGET: REPO, 'http://evil.test': REPO})
        counts = {'abort': 0, 'fallback': 0}
        def fallback(route):
            counts['fallback'] += 1
            route.fulfill(body='local', headers={'access-control-allow-origin': '*'})
        def abort(route):
            counts['abort'] += 1
            route.abort()
        context.route(re.compile(r'^https://', re.I), fallback)
        context.route(re.compile(r'^https://', re.I), abort)
        canary = context.new_page()
        try:
            results = [canary.evaluate('(u) => fetch(u).then(() => "fulfilled", () => "blocked")', u)
                       for u in ('https://isolation.invalid/', 'https://fonts.googleapis.com/css2?family=Local')]
            self.assertEqual(results, ['blocked', 'blocked'])
            self.assertEqual(counts, {'abort': 2, 'fallback': 0})
        finally:
            canary.close()
        if peer is not None:
            context.route(target, lambda route: route.fulfill(body=peer, content_type='text/html'))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{STUDIO}/{HTML.name}?target={quote(target, safe="")}')
        page.wait_for_function('document.querySelector("#bridgeStatusBadge").textContent.startsWith("Connected")')
        frame = next(f for f in page.frames if f.url.startswith(TARGET))
        frame.on('pageerror', lambda error: errors.append(str(error)))
        self.assertEqual(counts, {'abort': 2, 'fallback': 0})
        return page, frame, errors

    def detect(self, page):
        page.get_by_role('button', name='Detect text styles', exact=True).click()
        page.wait_for_function('!document.querySelector("#roleStatus").textContent.startsWith("Detecting")')
        return page.locator('#roleStatus').inner_text()

    def pending(self, page, frame):
        count = frame.evaluate('requests.length')
        page.get_by_role('button', name='Detect text styles', exact=True).click()
        frame.wait_for_function('(n) => requests.length > n', arg=count)
        return frame.evaluate('requests[requests.length-1]')

    def reply(self, request, groups=None, **changes):
        groups = [group()] if groups is None else groups
        return {'type': 'design:detected', 'requestId': request['requestId'], 'revision': 0,
                'documentId': 'peer-document', 'pageVersion': 0, 'pageURL': TARGET + '/peer',
                'currentPageVersion': 0, 'currentPageURL': TARGET + '/peer', 'complete': True, 'reason': None,
                'elapsedMs': 1, 'scannedElements': sum(g['elementCount'] for g in groups),
                'groups': groups, 'selectorChecks': [], **changes}

    def send(self, frame, reply, **envelope):
        # Playwright's object decoder assigns __proto__, losing that hostile own key.
        # JSON.parse preserves it; 1e400 is valid JSON for a nonfinite-number probe.
        body = json.dumps(reply).replace(': Infinity', ': 1e400')
        frame.evaluate('([body, extra]) => send(JSON.parse(body), extra)', [body, envelope])


class StudioRoleBoundaryTests(StudioRoleCase):
    def test_bounded_rows_collection_and_utf8_request_limit_are_visible(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                request = self.pending(page, frame)
                groups = [group(f'g-{i}', f'Role {i}', f'Author {i}') for i in range(128)]
                selectors = [{'value': '.' + c * 1050, 'stable': True, 'reason': 'class'} for c in ('a', 'b')]
                for item in groups:
                    item['selectors'] = selectors
                self.send(frame, self.reply(request, groups))
                page.wait_for_function('document.querySelector("#roleRows").children.length===128')
                self.assertEqual(page.locator('#roleRows > li').last.get_attribute('data-role-id'), 'role-128')
                page.get_by_role('button', name='Detect text styles').click()
                page.wait_for_function('document.querySelector("#roleStatus").textContent.includes("request limit")')
                self.assertEqual(frame.evaluate('requests.length'), 1)
                self.assertEqual(page.locator('#roleRows > li').count(), 128)
                frame.evaluate('ready()')
                page.wait_for_function('document.querySelector("#roleRows").children.length===0')
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, [group('new', 'New role', 'New author')]))
                page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Collection limit")')
                self.assertEqual(page.locator('#roleRows > li').first.get_attribute('data-role-id'), '')
                frame.evaluate('ready()')
                page.wait_for_function('document.querySelector("#roleRows").children.length===0')
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, [group('reordered', 'Existing role', 'Author 0')]))
                page.wait_for_function('document.querySelector("#roleRows").children.length===1')
                self.assertEqual(page.locator('#roleRows > li').first.get_attribute('data-role-id'), 'role-1')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_incomplete_and_rejected_detection_never_claim_checked_evidence(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, complete=False, reason='page-changed', currentPageVersion=4))
                page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Incomplete")')
                self.assertIn('this page has not been checked', page.locator('#roleStatus').inner_text())
                self.assertEqual(page.locator('#roleRows > li').count(), 1)
                request = self.pending(page, frame)
                self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': 99,
                                  'reason': 'unsupported-value', 'detail': '<img src=x onerror=alert(1)>'})
                page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Role detection rejected")')
                self.assertIn('this page has not been checked', page.locator('#roleStatus').inner_text())
                self.assertEqual(page.locator('#detectedRoles img').count(), 0)
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_navigated_target_window_cannot_use_its_new_origin_as_role_authority(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                session = frame.evaluate('session')
                page.context.route('http://evil.test/redirected', lambda route: route.fulfill(
                    body='<p style="font:16px sans-serif">Foreign page</p>', content_type='text/html'))
                frame.goto('http://evil.test/redirected')
                frame.evaluate('data=>parent.postMessage(data,"http://studio.test")',
                    {'type': 'design:ready', 'protocolVersion': 1, 'sessionId': session, 'revision': 0,
                     'capabilities': {'roleDetection': True}, 'roleState': {
                         'documentId': 'forged-document', 'pageVersion': 0, 'pageURL': TARGET + '/peer',
                         'roles': [], 'canonicalCss': '', 'hashAlgorithm': 'fnv1a32', 'cssHash': '811c9dc5'}, 'targets': []})
                page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                self.assertTrue(page.get_by_role('button', name='Detect text styles').is_disabled())
                self.assertNotIn('Ready to detect', page.locator('#roleStatus').inner_text())
                self.assertEqual(frame.locator('p').inner_text(), 'Foreign page')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_ready_requires_exact_empty_snapshot_and_supported_capability(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                original = frame.evaluate('state')
                invalid = [None, {**original, 'extra': True}, {**original, 'pageVersion': -1},
                           {**original, 'cssHash': '00000000'}, {**original, 'roles': [group()]},
                           {**original, 'canonicalCss': 'p{}'}, {**original, 'documentId': ''},
                           {**original, 'pageURL': 'http://evil.test/path'},
                           {**original, 'pageURL': 'http://user:secret@target.test/path'},
                           {**original, 'pageURL': TARGET + '/' + 'x' * 2000},
                           {**original, 'constructor': {}}]
                for state in invalid:
                    frame.evaluate('s=>{state=s;ready()}', state)
                    page.wait_for_function('document.querySelector("#roleStatus").textContent=== "This bridge does not support role detection/preview."')
                    self.assertTrue(page.get_by_role('button', name='Detect text styles').is_disabled())
                    self.assertEqual(page.locator('#roleRows > li').count(), 0)
                    frame.evaluate('s=>{state=s;ready()}', original)
                    page.wait_for_function('!document.querySelector("#detectTextStyles").disabled')
                frame.evaluate('()=>send({type:"design:ready",revision:0,targets:[],capabilities:{},roleState:state})')
                page.wait_for_function('document.querySelector("#detectTextStyles").disabled')
                self.assertEqual(page.locator('#roleStatus').inner_text(), UNSUPPORTED)
                self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
                self.assertEqual(errors, [])

    def test_older_ready_and_results_cannot_downgrade_current_generation(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, [group(name='Version four')], pageVersion=4, currentPageVersion=4))
                page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Version four")')
                frame.evaluate('ready()')
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, [group(name='Older')], pageVersion=3, currentPageVersion=3))
                self.send(frame, self.reply(request, [group(name='Fresh')], pageVersion=5, currentPageVersion=5,
                    selectorChecks=[{'roleId': 'role-1', 'selector': '.body-copy', 'matchCount': 1,
                                     'signatures': [{'style': STYLE.copy(), 'count': 1}]}]))
                page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Fresh")', timeout=3000)
                self.assertNotIn('Older', page.locator('#roleRows').inner_text())
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_identity_mapping_survives_reordering_labels_and_namespaces(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                first = [group(), group('scan-b', 'Body', None)]
                first[0]['nearDuplicateIds'] = ['scan-b']
                first[1]['nearDuplicateIds'] = ['scan-a']
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, first))
                page.wait_for_function('document.querySelector("#roleRows").children.length===2')
                self.assertEqual(page.locator('#roleRows > li').evaluate_all('els=>els.map(e=>e.dataset.roleId)'), ['role-1', 'role-2'])
                second = [group('other-style', 'Renamed', None), group('other-author', 'Renamed')]
                second[1]['signatures'] = [{'style': STYLE.copy(), 'count': 1},
                                           {'style': {**STYLE, 'fontSize': 24}, 'count': 1}]
                second[1]['elementCount'] = 2
                request = self.pending(page, frame)
                checks = [{'roleId': r['id'], 'selector': s, 'matchCount': 1,
                           'signatures': [{'style': STYLE.copy(), 'count': 1}]}
                          for r in request['knownRoles'] for s in r['selectors']]
                self.send(frame, self.reply(request, second, selectorChecks=checks))
                page.wait_for_function('document.querySelector("#roleRows").textContent.includes("24px")')
                self.assertEqual(page.locator('#roleRows > li').evaluate_all('els=>els.map(e=>e.dataset.roleId)'), ['role-2', 'role-1'])
                self.assertIn('2 eligible text parents', page.locator('#roleRows').inner_text())
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertEqual(errors, [])

    def test_latest_request_and_authenticated_document_only_can_render(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                old = self.pending(page, frame)
                current = self.pending(page, frame)
                hostile = self.reply(current, [group(name='Forged')])
                self.send(frame, self.reply(old, [group(name='Superseded')]))
                self.send(frame, hostile, sessionId='wrong-session')
                self.send(frame, hostile, protocolVersion=2)
                self.send(frame, {**hostile, 'documentId': 'unknown-document'})
                page.evaluate('(data)=>window.postMessage(data,location.origin)',
                              {**hostile, 'sessionId': current['sessionId'], 'protocolVersion': 1})
                frame.evaluate('data=>new Promise(resolve=>{let child=document.createElement("iframe");child.onload=resolve;child.srcdoc="<script>parent.parent.postMessage("+JSON.stringify(data)+",\\\"http://studio.test\\\")<"+"/script>";document.body.append(child)})',
                               {**hostile, 'sessionId': current['sessionId'], 'protocolVersion': 1})
                self.send(frame, self.reply(current, [group(name='Current')]))
                page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Current")', timeout=3000)
                text = page.locator('#roleRows').inner_text()
                self.assertNotIn('Forged', text)
                self.assertNotIn('Superseded', text)
                self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_exact_hostile_shapes_leave_rendered_snapshot_and_legacy_ledger_intact(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                request = self.pending(page, frame)
                self.send(frame, self.reply(request))
                page.wait_for_function('document.querySelector("#roleRows").children.length===1')
                snapshot = page.locator('#roleRows').inner_text()
                request = self.pending(page, frame)
                checks = [{'roleId': 'role-1', 'selector': '.body-copy', 'matchCount': 1,
                           'signatures': [{'style': STYLE.copy(), 'count': 1}]}]
                valid = self.reply(request, selectorChecks=checks)
                bad_group = group(name='Hostile')
                too_many = [group('many', 'Hostile many', 'Many'), group('last', 'Hostile last', 'Last')]
                too_many[0]['elementCount'] = 10000
                too_many[0]['signatures'][0]['count'] = 10000
                corruptions = [
                    {'pageURL': TARGET + '/different', 'currentPageURL': TARGET + '/different'},
                    {'scannedElements': 10001, 'groups': too_many},
                    {'extra': True}, {'groups': [{**bad_group, 'extra': True}]},
                    {'groups': [{**bad_group, 'identity': {'kind': 'author-role', 'name': 'Other'}}]},
                    {'groups': [{**bad_group, 'identity': {'kind': 'style', 'style': STYLE}, 'authorRole': None,
                                 'signatures': [{'style': {**STYLE, 'fontSize': 20}, 'count': 1}]}]},
                    {'groups': [{**bad_group, 'elementCount': 2}]}, {'groups': [bad_group, bad_group]},
                    {'groups': [{**bad_group, 'nearDuplicateIds': ['missing']}]},
                    {'groups': [{**bad_group, 'sampleText': 'x' * 201}]},
                    {'groups': [{**bad_group, 'sharedClasses': ['x'] * 17}]},
                    {'groups': [{**bad_group, 'signatures': [{'style': {**STYLE, 'fontSize': float('inf')}, 'count': 1}]}]},
                    {'groups': [{**bad_group, 'selectors': [{'value': '.1', 'stable': True, 'reason': 'class'}]}]},
                    {'groups': [{**bad_group, 'selectors': [{'value': '.a,.b', 'stable': True, 'reason': 'class'}]}]},
                    {'groups': [{**bad_group, 'selectors': [{'value': '[onclick="x"]', 'stable': True, 'reason': 'class'}]}]},
                    {'groups': [{**bad_group, 'selectors': [{'value': 'body', 'stable': True, 'reason': 'class'}]}]},
                    {'groups': [{**bad_group, 'selectors': [{'value': 'body:nth-of-type(1)', 'stable': False, 'reason': 'dom-path'}]}]},
                    {'pageURL': 'http://evil.test/path'}, {'currentPageURL': 'http://user:secret@target.test/path'},
                    {'currentPageURL': None}, {'reason': 'invented'}, {'elapsedMs': -1}, {'elapsedMs': 2001}, {'pageVersion': -1},
                    {'scannedElements': 10002}, {'selectorChecks': [{**checks[0], 'matchCount': 2}]},
                    {'groups': {'0': bad_group}},
                    *[{'groups': [{**bad_group, 'identity': {'kind': 'author-role', 'name': 'Body', key: {}}}]}
                      for key in ('constructor', '__proto__', 'prototype')],
                    {'padding': '界' * 400000}, {'groups': [{**bad_group, 'suggestedName': 'x' * 201}]},
                ]
                for change in corruptions:
                    self.send(frame, {**valid, **change})
                # Fence delivery through the same authenticated peer; an accepted invalid result
                # would have settled the request and prevented this complete literal snapshot.
                self.send(frame, {**valid, 'groups': [group(name='Validated')]})
                page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Validated")', timeout=3000)
                self.assertNotIn('Hostile', page.locator('#roleRows').inner_text())
                self.assertIn('Body', snapshot)
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_literal_markup_and_escaped_uncertain_selectors_remain_read_only_text(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                request = self.pending(page, frame)
                literal = '<img src="https://isolation.invalid/x" onerror="document.body.dataset.bad=1">'
                item = group(name=literal)
                item['sampleText'] = literal
                item['sharedClasses'] = [literal]
                item['selectors'] = [{'value': '.\\31 0', 'stable': False, 'reason': 'css-module'},
                                     {'value': '[data-design-role="a\\22 b"] > span:nth-of-type(2)', 'stable': False, 'reason': 'dom-path'}]
                self.send(frame, self.reply(request, [item]))
                page.wait_for_function('document.querySelector("#roleRows").children.length===1')
                self.assertIn(literal, page.locator('#roleRows').inner_text())
                self.assertIn('uncertain (css-module)', page.locator('#roleRows').inner_text())
                self.assertIn('.\\31 0', page.locator('#roleRows').inner_text())
                self.assertEqual(page.locator('#roleRows img').count(), 0)
                self.assertIsNone(page.locator('body').get_attribute('data-bad'))
                self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
                self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])
