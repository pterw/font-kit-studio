"""Studio's role boundary and preview controls, against explicitly authored peers.

Two peers stand in for a bridge: PEER, a one-paragraph page that records every message Studio sends and answers
only what a test tells it to, and HYBRID, the legacy fake target with the same role hooks, for the cases that need a
real inspector edit. Neither applies a role: what the target renders is asserted in test_r2_integration.py.
"""
import functools
import json
import re
import unittest
from pathlib import Path
from urllib.parse import quote

from support import ENGINES, HTML, REPO, new_context, route_virtual_origins

STUDIO = 'http://studio.test'
TARGET = 'http://target.test'
ROLE_PAGE = TARGET + '/tests/fixtures/bridge/target-role-protocol.html'
PEER_URL = TARGET + '/peer'
HYBRID_URL = TARGET + '/hybrid.html'
UNAVAILABLE = 'Role detection/preview unavailable: unsupported page URL.'
UNSUPPORTED = 'This bridge does not support role detection/preview.'
NO_PREVIEW = 'This bridge does not support role preview.'
STALE = 'Preview applied; page changed before checks finished'
APPLY = 'Apply selected roles'
CLEAR = 'Clear preview'
RESET_ALL = 'Reset all page edits'
EMPTY_HASH = '811c9dc5'
FIXTURE = REPO / 'tests' / 'fixtures' / 'studio' / 'fake-target.html'

STYLE = {'fontFamily': 'sans-serif', 'fontSize': 16, 'fontWeight': 400,
         'textTransform': 'none', 'letterSpacing': 0}
PROPERTY_ORDER = ('fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform')
CSS_NAMES = {'fontFamily': 'font-family', 'fontSize': 'font-size', 'fontWeight': 'font-weight',
             'lineHeight': 'line-height', 'letterSpacing': 'letter-spacing', 'textTransform': 'text-transform'}
CSS_UNITS = {'fontSize': 'px', 'letterSpacing': 'em'}


def fnv1a32(text):
    """The contract's digest, written out here so tests do not borrow Studio's."""
    value = 0x811c9dc5
    for byte in text.encode('utf-8'):
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return f'{value:08x}'


def canonical_css(roles):
    """The canonical sheet for the roles in the binding format; Studio re-serializes the roles and requires these bytes."""
    blocks = []
    for role in roles:
        lines = [f'{", ".join(role["selectors"])} {{']
        for key in PROPERTY_ORDER:
            if key in role['properties']:
                lines.append(f'  {CSS_NAMES[key]}: {role["properties"][key]}{CSS_UNITS.get(key, "")};')
        lines.append('}')
        blocks.append('\n'.join(lines) + '\n')
    return ''.join(blocks)


def group(group_id='scan-a', name='Body', author='Body', style=None, selectors=None, binding_complete=True):
    style = style or STYLE.copy()
    selectors = selectors if selectors is not None else [{'value': '.body-copy', 'stable': True, 'reason': 'class'}]
    return {'id': group_id, 'identity': {'kind': 'author-role', 'name': author} if author else {'kind': 'style', 'style': style},
            'suggestedName': name, 'authorRole': author, 'signatures': [{'style': style, 'count': 1}],
            'elementCount': 1, 'sampleText': 'Peer body', 'sharedClasses': ['body-copy'],
            'selectors': selectors, 'bindingComplete': binding_complete, 'nearDuplicateIds': []}


def per_engine(test):
    @functools.wraps(test)
    def run(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                test(self, engine)
    return run


# The peer records every message Studio sends in `received` (detect requests also in `requests`) and answers nothing
# on its own beyond the handshake: a test sends each reply, so it controls ordering and content.
PEER_TEMPLATE = '''<!doctype html><meta charset="utf-8"><style>.body-copy{font:16px sans-serif}</style>
<p class="body-copy">Peer body</p><script>
let n=1;try{n=+(sessionStorage.getItem('doc')||0)+1;sessionStorage.setItem('doc',n)}catch(e){}
window.received=[];window.requests=[];window.session=null;window.host=null;window.rev=0;window.caps=__CAPS__;
window.state={documentId:n===1?'peer-document':'peer-document-'+n,pageVersion:0,pageURL:location.href,roles:[],canonicalCss:'',hashAlgorithm:'fnv1a32',cssHash:'811c9dc5'};
window.send=(body, extra={})=>parent.postMessage({protocolVersion:1,sessionId:session,...body,...extra},host);
window.ready=()=>send({type:'design:ready',revision:rev,capabilities:caps,roleState:state,targets:[],changes:{tokens:{},targets:[],structure:[],imports:[]}});
addEventListener('message',e=>{if(e.source!==parent||e.origin!=='http://studio.test')return;
 received.push(JSON.parse(JSON.stringify(e.data)));
 if(e.data.type==='design:hello'){session=e.data.sessionId;host=e.origin;ready()}
 else if(e.data.type==='design:detect') requests.push(e.data);
});
</script>'''
PEER = PEER_TEMPLATE.replace('__CAPS__', '{roleDetection:true,roleStylesheet:true}')
PEER_DETECT_ONLY = PEER_TEMPLATE.replace('__CAPS__', '{roleDetection:true}')
PEER_LEGACY = PEER_TEMPLATE.replace('__CAPS__', '{}')

# The legacy fake target, with the role capabilities and a ready roleState added at serve time. The two replacements
# fail loudly if the fixture changes; the fake keeps answering legacy ops (and holds replies on request).
_READY_CAPS = 'capabilities: { inspect: true, patch: true, typography: true, text: true, tokens: true, reset: true },'
HYBRID_SHIM = '''<script>
window.requests=[];window.rs={session:null,host:null,state:{documentId:'hybrid-document',pageVersion:0,pageURL:location.href,roles:[],canonicalCss:'',hashAlgorithm:'fnv1a32',cssHash:'811c9dc5'}};
Object.defineProperty(window,'received',{get:()=>window.__received.map(r=>r.data)});
rs.send=(body,extra={})=>parent.postMessage({protocolVersion:1,sessionId:rs.session,...body,...extra},rs.host);
addEventListener('message',e=>{if(e.source!==parent||e.origin!=='http://studio.test')return;
 if(e.data&&e.data.type==='design:hello'){rs.session=e.data.sessionId;rs.host=e.origin}
 if(e.data&&e.data.type==='design:detect')requests.push(e.data)});
</script>'''


def hybrid_page():
    source = FIXTURE.read_text(encoding='utf-8')
    assert source.count(_READY_CAPS) == 1 and source.count('</body>') == 1, 'fake-target.html changed shape'
    source = source.replace(_READY_CAPS, _READY_CAPS[:-2] + ', roleDetection: true, roleStylesheet: true }, roleState: window.rs.state,')
    return source.replace('</body>', HYBRID_SHIM + '</body>')


class StudioRoleCase(unittest.TestCase):
    page_url = PEER_URL

    def open(self, engine, target=ROLE_PAGE, peer=None, viewport=None, sync=False, init=None):
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
        self.puts = []
        if sync:
            def dev_server(route):
                request = route.request
                if request.url.endswith('/__fontkit/status') and request.method == 'GET':
                    route.fulfill(status=200, content_type='application/json',
                                  body=json.dumps({'sync': True, 'overrides': 'demo/fontkit-overrides.css', 'target': None}))
                elif request.url.endswith('/__fontkit/overrides.css') and request.method == 'PUT':
                    body = request.post_data or ''
                    self.puts.append(body)
                    route.fulfill(status=200, content_type='application/json',
                                  body=json.dumps({'ok': True, 'bytes': len(body.encode()), 'path': 'demo/fontkit-overrides.css'}))
                else:
                    route.fulfill(status=404, body='not found')
            # Registered after the file routes: Playwright runs the latest matching route first.
            context.route(f'{STUDIO}/__fontkit/**', dev_server)
        if peer is not None:
            context.route(target, lambda route: route.fulfill(body=peer, content_type='text/html'))
        self.page_url = target
        page = context.new_page()
        if init:
            page.add_init_script(init)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{STUDIO}/{HTML.name}?target={quote(target, safe="")}')
        page.wait_for_function('document.querySelector("#bridgeStatusBadge").textContent.startsWith("Connected")')
        frame = next(f for f in page.frames if f.url.startswith(TARGET))
        frame.on('pageerror', lambda error: errors.append(str(error)))
        self.assertEqual(counts, {'abort': 2, 'fallback': 0})
        return page, frame, errors

    def open_hybrid(self, engine, sync=False):
        return self.open(engine, HYBRID_URL, hybrid_page(), sync=sync)

    # ---- what the peer saw -----------------------------------------------------------------------------------
    def sent(self, frame):
        return [message['type'] for message in frame.evaluate('received')]

    def ops(self, frame, kind):
        return [message for message in frame.evaluate('received') if message['type'] == kind]

    def wait_for_ops(self, frame, kind, count):
        frame.wait_for_function('([kind, count]) => received.filter(m => m.type === kind).length >= count', arg=[kind, count], polling=50)

    def settle(self, page, frame):
        """Waits for messages already posted by the peer to have been handled (same-source order is guaranteed)."""
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')

    # ---- detection ---------------------------------------------------------------------------------------------
    def detect(self, page):
        page.get_by_role('button', name='Detect text styles', exact=True).click()
        page.wait_for_function('!document.querySelector("#roleStatus").textContent.startsWith("Detecting")')
        return page.locator('#roleStatus').inner_text()

    def pending(self, page, frame, keep_focus=False):
        count = frame.evaluate('requests.length')
        if keep_focus:
            page.evaluate('document.querySelector("#detectTextStyles").click()')
        else:
            page.get_by_role('button', name='Detect text styles', exact=True).click()
        frame.wait_for_function('(n) => requests.length > n', arg=count, polling=50)
        return frame.evaluate('requests[requests.length-1]')

    def reply(self, request, groups=None, **changes):
        groups = [group()] if groups is None else groups
        return {'type': 'design:detected', 'requestId': request['requestId'], 'revision': 0,
                'documentId': request['documentId'], 'pageVersion': 0, 'pageURL': self.page_url,
                'currentPageVersion': 0, 'currentPageURL': self.page_url, 'complete': True, 'reason': None,
                'elapsedMs': 1, 'scannedElements': sum(g['elementCount'] for g in groups),
                'groups': groups, 'selectorChecks': self.checks(request), **changes}

    def checks(self, request):
        """One baseline check per selector the request named, as a complete scan must report."""
        return [{'roleId': role['id'], 'selector': selector, 'matchCount': 1,
                 'signatures': [{'style': STYLE.copy(), 'count': 1}]}
                for role in request['knownRoles'] for selector in role['selectors']]

    def send(self, frame, reply, **envelope):
        # Playwright's object decoder assigns __proto__, losing that hostile own key.
        # JSON.parse preserves it; 1e400 is valid JSON for a nonfinite-number probe.
        body = json.dumps(reply).replace(': Infinity', ': 1e400')
        frame.evaluate('([body, extra]) => (window.send || rs.send)(JSON.parse(body), extra)', [body, envelope])

    def detected(self, page, frame, groups=None, **changes):
        """One Detect round trip; returns the request. Waits until the result is shown."""
        request = self.pending(page, frame)
        self.send(frame, self.reply(request, groups, **changes))
        page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected")')
        return request

    # ---- draft controls and the preview ---------------------------------------------------------------------
    def control(self, page, label, role='role-1', name='Body'):
        return page.get_by_label(f'{label} for {name} ({role})', exact=True)

    def type_value(self, locator, value):
        locator.focus()
        locator.press('ControlOrMeta+A')
        if value == '':
            locator.press('Backspace')
        else:
            locator.press_sequentially(value)

    def button(self, page, name):
        return page.get_by_role('button', name=name, exact=True)

    def hint(self, page, button_id):
        node = page.locator(f'#{button_id}')
        return node.inner_text() if node.is_visible() else ''

    def gate(self, page):
        """Whether Apply is enabled, and the visible reason when it is not."""
        return self.button(page, APPLY).is_enabled(), self.hint(page, 'roleApplyHint')

    def preview(self, page):
        return {'css': page.locator('#rolePreviewCss').text_content(),
                'status': page.get_by_role('status', name='Role preview status').inner_text(),
                'removed': page.locator('#rolePreviewRemoved').inner_text() if page.locator('#rolePreviewRemoved').is_visible() else '',
                'outcomes': page.locator('#rolePreviewOutcomes').inner_text()}

    def apply_role(self, page, frame, size='24', role='role-1', name='Body'):
        """Selects the role, types its size by keystrokes, presses Apply and returns the request the peer received."""
        self.control(page, 'Preview this role', role, name).check()
        self.type_value(self.control(page, 'Size (px)', role, name), size)
        return self.press_apply(page, frame)

    def press_apply(self, page, frame):
        count = len(self.ops(frame, 'design:roles-apply'))
        self.button(page, APPLY).click()
        self.wait_for_ops(frame, 'design:roles-apply', count + 1)
        return self.ops(frame, 'design:roles-apply')[-1]

    def clear_preview(self, page, frame):
        count = len(self.ops(frame, 'design:roles-clear'))
        self.button(page, CLEAR).click()
        self.wait_for_ops(frame, 'design:roles-clear', count + 1)
        return self.ops(frame, 'design:roles-clear')[-1]

    def receipt(self, request, outcomes=None, **changes):
        """A valid receipt for the request the peer received (apply or clear)."""
        apply = request['type'] == 'design:roles-apply'
        roles = request['roles'] if apply else []
        css = canonical_css(roles)
        if outcomes is None:
            outcomes = [{'id': role['id'], 'matched': 1, 'checked': 1, 'mismatched': 0, 'complete': True, 'losses': []}
                        for role in roles]
        return {'type': 'design:roles-applied', 'requestId': request['requestId'], 'operation': 'apply' if apply else 'clear',
                'revision': request['baseRevision'] + 1, 'documentId': request['documentId'],
                'pageVersion': request['pageVersion'], 'currentPageVersion': request['pageVersion'],
                'currentPageURL': self.page_url, 'roles': roles, 'canonicalCss': css, 'hashAlgorithm': 'fnv1a32',
                'cssHash': fnv1a32(css), 'outcomesComplete': True, 'outcomeReason': None, 'outcomes': outcomes, **changes}

    def with_css(self, receipt, css):
        return {**receipt, 'canonicalCss': css, 'cssHash': fnv1a32(css)}

    def wait_status(self, page, text):
        page.wait_for_function('(t) => document.querySelector("#rolePreviewStatus").textContent.includes(t)', arg=text)

    def snapshot_state(self, roles, **changes):
        css = canonical_css(roles)
        return {'documentId': 'peer-document', 'pageVersion': 0, 'pageURL': PEER_URL, 'roles': roles, 'canonicalCss': css,
                'hashAlgorithm': 'fnv1a32', 'cssHash': fnv1a32(css), **changes}

    def role_input(self, role_id='role-1', name='Body', **properties):
        return {'id': role_id, 'name': name, 'selectors': ['.body-copy'], 'adapter': 'plain',
                'properties': properties or {'fontSize': 24}}

    def ready_with(self, page, frame, state, revision=0, **caps):
        frame.evaluate('([s, r]) => { state = s; rev = r; ready() }', [state, revision])
        page.wait_for_function('document.querySelector("#roleStatus").textContent !== ""')
        self.settle(page, frame)

    def exports(self, page):
        """Everything Studio can hand over: each code tab and its Download, and the JSON export."""
        result = {}
        for tab in ('Css', 'Html', 'Json'):
            page.locator(f'#codeTab{tab}').click()
            result[tab] = page.locator('#liveCodeOutput').inner_text()
            with page.expect_download() as download:
                page.locator('#liveCodeDownload').click()
            result[f'download{tab}'] = Path(download.value.path()).read_bytes().decode('utf-8')
        page.locator('#exportJson').click()
        result['export'] = page.locator('#exportDialogText').input_value()
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return result

    def sync_body(self, page):
        with page.expect_response(lambda response: response.request.method == 'PUT'):
            page.locator('#liveCodeSync').click()
        return self.puts[-1]

    def switch_to(self, page, url, html, ready_status='Ready to detect text styles.'):
        """Connects Studio to another origin served by `html`; returns that origin's frame once Studio shows `ready_status`."""
        page.context.route(url, lambda route: route.fulfill(body=html, content_type='text/html'))
        field = page.get_by_role('textbox', name='Live App URL', exact=True)
        field.focus()
        field.press('ControlOrMeta+A')
        field.press_sequentially(url)
        page.get_by_role('button', name='Connect Live App', exact=True).click()
        page.wait_for_function('(text) => document.querySelector("#roleStatus").textContent === text', arg=ready_status)
        self.page_url = url
        return next(f for f in page.frames if f.url == url)

    def unchanged_page(self, frame):
        self.assertEqual(frame.locator('p').inner_text(), 'Peer body')
        self.assertEqual(frame.locator('p').evaluate('el=>getComputedStyle(el).fontSize'), '16px')


class StudioRoleBoundaryTests(StudioRoleCase):
    def test_bounded_rows_collection_and_utf8_request_limit_are_visible(self):
        """Given 128 detected roles with long selectors, when Detect repeats, then the oversize request is refused
        and the collection limit keeps new roles out, while the peer only ever received hello and detect."""
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:detect', 'design:detect'])
                self.unchanged_page(frame)
                self.assertEqual(errors, [])

    def test_incomplete_and_rejected_detection_never_claim_checked_evidence(self):
        """Given an incomplete and then a rejected detect, when Studio shows them, then neither claims the page was
        checked, the literal detail is text, and Studio sent only hello and two detects."""
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:detect'])
                self.unchanged_page(frame)
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

    def test_ready_requires_exact_snapshot_and_supported_capability(self):
        """Given a connected peer, when ready arrives with a malformed snapshot or without role capabilities, then
        Studio shows the unsupported reason and disables Detect, and a good ready recovers it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                original = frame.evaluate('state')
                invalid = {'null': None, 'extra key': {**original, 'extra': True}, 'negative version': {**original, 'pageVersion': -1},
                           'fractional version': {**original, 'pageVersion': 1.5},
                           'wrong digest': {**original, 'cssHash': '00000000'},
                           'other algorithm': {**original, 'hashAlgorithm': 'sha256'},
                           'roles are not RoleInputs': {**original, 'roles': [group()]},
                           'roles not an array': {**original, 'roles': {}},
                           'css without roles': {**original, 'canonicalCss': 'p{}', 'cssHash': fnv1a32('p{}')},
                           'empty document': {**original, 'documentId': ''},
                           '201-character document': {**original, 'documentId': 'd' * 201},
                           'foreign url': {**original, 'pageURL': 'http://evil.test/path'},
                           'credential url': {**original, 'pageURL': 'http://user:secret@target.test/path'},
                           'over-long url': {**original, 'pageURL': TARGET + '/' + 'x' * 2000},
                           'prototype key': {**original, 'constructor': {}}}
                for name, state in invalid.items():
                    with self.subTest(snapshot=name):
                        frame.evaluate('s=>{state=s;ready()}', state)
                        page.wait_for_function('document.querySelector("#roleStatus").textContent=== "This bridge does not support role detection/preview."')
                        self.assertTrue(page.get_by_role('button', name='Detect text styles').is_disabled())
                        self.assertEqual(page.locator('#roleRows > li').count(), 0)
                        frame.evaluate('s=>{state=s;ready()}', original)
                        page.wait_for_function('!document.querySelector("#detectTextStyles").disabled')
                frame.evaluate('()=>send({type:"design:ready",revision:0,targets:[],capabilities:{},roleState:state})')
                page.wait_for_function('document.querySelector("#detectTextStyles").disabled')
                self.assertEqual(page.locator('#roleStatus').inner_text(), UNSUPPORTED)
                self.assertEqual(set(self.sent(frame)), {'design:hello'})
                self.unchanged_page(frame)
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:detect'])
                self.unchanged_page(frame)
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:detect'])
                self.unchanged_page(frame)
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:detect'])
                self.unchanged_page(frame)
                self.assertEqual(errors, [])

    def test_exact_hostile_shapes_leave_rendered_snapshot_and_legacy_ledger_intact(self):
        """Given a pending detect, when each malformed or hostile reply for it arrives followed by one valid fence
        reply, then the fence is what renders (so the hostile one was not accepted), the failing shape is named by
        its subtest, and no hostile text renders."""
        too_many = [group('many', 'Hostile many', 'Many'), group('last', 'Hostile last', 'Last')]
        too_many[0]['elementCount'] = 10000
        too_many[0]['signatures'][0]['count'] = 10000
        def hostile(**changes):
            return [{**group(name='Hostile'), **changes}]
        def selector(value, stable=True, reason='class'):
            return hostile(selectors=[{'value': value, 'stable': stable, 'reason': reason}])
        shapes = {
            'foreign route': {'pageURL': TARGET + '/different', 'currentPageURL': TARGET + '/different'},
            'more elements than the limit': {'scannedElements': 10001, 'groups': too_many},
            'extra top-level key': {'extra': True}, 'extra group key': {'groups': hostile(extra=True)},
            'identity differs from authorRole': {'groups': hostile(identity={'kind': 'author-role', 'name': 'Other'})},
            'style identity differs from signature': {'groups': hostile(
                identity={'kind': 'style', 'style': STYLE}, authorRole=None,
                signatures=[{'style': {**STYLE, 'fontSize': 20}, 'count': 1}])},
            'count differs from variants': {'groups': hostile(elementCount=2)},
            'duplicate group': {'groups': [group(name='Hostile'), group(name='Hostile')]},
            'near duplicate missing': {'groups': hostile(nearDuplicateIds=['missing'])},
            'sample text too long': {'groups': hostile(sampleText='x' * 201)},
            'too many shared classes': {'groups': hostile(sharedClasses=['x'] * 17)},
            'nonfinite size': {'groups': hostile(signatures=[{'style': {**STYLE, 'fontSize': float('inf')}, 'count': 1}])},
            'selector starts with digit': {'groups': selector('.1')},
            'selector list': {'groups': selector('.a,.b')},
            'other attribute': {'groups': selector('[onclick="x"]')},
            'root tag': {'groups': selector('body')},
            'root path': {'groups': selector('body:nth-of-type(1)', False, 'dom-path')},
            'pseudo-class': {'groups': selector('a:hover')},
            'raw braces': {'groups': selector('.a{}')},
            'raw semicolon': {'groups': selector('.a;')},
            'line break': {'groups': selector('.a\n.b')},
            'comment': {'groups': selector('.a/*x*/')},
            'at-rule': {'groups': selector('@media x')},
            'url function': {'groups': selector('.a url(x)')},
            'expression function': {'groups': selector('.a expression(1)')},
            '2001-character selector': {'groups': selector('.' + 'a' * 2000)},
            'nth-of-type 10000': {'groups': selector('p:nth-of-type(10000)', False, 'dom-path')},
            '33 selectors': {'groups': hostile(selectors=[{'value': f'.c{i}', 'stable': True, 'reason': 'class'} for i in range(33)])},
            'foreign page url': {'pageURL': 'http://evil.test/path'},
            'credential current url': {'currentPageURL': 'http://user:secret@target.test/path'},
            'null current url': {'currentPageURL': None}, 'invented reason': {'reason': 'invented'},
            'negative time': {'elapsedMs': -1}, 'slow complete scan': {'elapsedMs': 2001}, 'negative version': {'pageVersion': -1},
            'scanned over limit': {'scannedElements': 10002}, 'check count mismatch': 'checks',
            'groups as object': {'groups': {'0': group(name='Hostile')}},
            'constructor in identity': {'groups': hostile(identity={'kind': 'author-role', 'name': 'Body', 'constructor': {}})},
            'proto in identity': {'groups': hostile(identity={'kind': 'author-role', 'name': 'Body', '__proto__': {}})},
            'prototype in identity': {'groups': hostile(identity={'kind': 'author-role', 'name': 'Body', 'prototype': {}})},
            'over-long name': {'groups': hostile(suggestedName='x' * 201)},
        }
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                self.detected(page, frame)
                checks = [{'roleId': 'role-1', 'selector': '.body-copy', 'matchCount': 1,
                           'signatures': [{'style': STYLE.copy(), 'count': 1}]}]
                total = 1
                for name, change in shapes.items():
                    with self.subTest(shape=name):
                        request = self.pending(page, frame)
                        total += 1
                        valid = self.reply(request, [group(name='Base')], selectorChecks=checks)
                        change = {'selectorChecks': [{**checks[0], 'matchCount': 2}]} if change == 'checks' else change
                        self.send(frame, {**valid, **change})
                        # The fence goes through the same authenticated peer. An accepted invalid result would have
                        # settled the request and the fence would never render.
                        self.send(frame, {**valid, 'groups': [group(name='Fence')]})
                        page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Fence")', timeout=4000)
                        self.assertNotIn('Hostile', page.locator('#roleRows').inner_text())
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertEqual(self.sent(frame), ['design:hello'] + ['design:detect'] * total)
                self.unchanged_page(frame)
                self.assertEqual(errors, [])

    def test_selector_boundaries_accept_2000_characters_nth_9999_and_32_selectors(self):
        """Given detected selectors at the documented limits, when the reply arrives, then each renders as text."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                limits = [{'value': '.' + 'a' * 1999, 'stable': True, 'reason': 'class'},
                          {'value': 'p:nth-of-type(9999)', 'stable': False, 'reason': 'dom-path'}]
                limits += [{'value': f'.c{i}', 'stable': True, 'reason': 'class'} for i in range(30)]
                self.detected(page, frame, [group(selectors=limits)])
                text = page.locator('#roleRows').inner_text()
                self.assertIn('p:nth-of-type(9999)', text)
                self.assertIn('.' + 'a' * 1999, text)
                self.assertIn('.c29', text)
                self.assertEqual(errors, [])

    def test_request_limit_counts_utf8_bytes_not_characters(self):
        """Given roles whose selectors are multi-byte, when the known-roles request would pass a character count but
        pass 256 KiB as bytes, then Detect refuses; with fewer roles the same selectors are sent."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                selector = [{'value': '.' + '界' * 700, 'stable': True, 'reason': 'class'}]
                many = [group(f'g-{i}', f'Role {i}', f'Author {i}', selectors=selector) for i in range(128)]
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, many[:100]))
                page.wait_for_function('document.querySelector("#roleRows").children.length===100')
                request = self.pending(page, frame)
                self.assertEqual(len(request['knownRoles']), 100)
                self.send(frame, self.reply(request, many))
                page.wait_for_function('document.querySelector("#roleRows").children.length===128')
                characters = len(json.dumps(many, ensure_ascii=False))
                self.assertLess(characters, 256 * 1024, 'a length-based limit would let this through')
                page.get_by_role('button', name='Detect text styles').click()
                page.wait_for_function('document.querySelector("#roleStatus").textContent.includes("request limit")')
                self.assertEqual(frame.evaluate('requests.length'), 2)
                self.assertEqual(errors, [])

    def test_detected_reply_at_one_mib_is_accepted_and_one_byte_more_is_not(self):
        """Given a valid detected reply padded through a legitimate font-family field, when it is exactly 1 MiB or
        1 MiB + 1 bytes, then only the first renders."""
        limit = 1024 * 1024
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, TARGET + '/peer', PEER)
                for size, accepted in ((limit, True), (limit + 1, False)):
                    with self.subTest(size=size):
                        request = self.pending(page, frame)
                        def build(n):
                            style = {**STYLE, 'fontFamily': 'P' * n}
                            return self.reply(request, [group(name='Padded', style=style)])
                        def measure(n):
                            envelope = {'protocolVersion': 1, 'sessionId': request['sessionId'], **build(n)}
                            return len(json.dumps(envelope, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
                        padding = size - measure(0)
                        self.assertEqual(measure(padding), size)
                        self.send(frame, build(padding))
                        if accepted:
                            page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Padded")', timeout=15000)
                        else:
                            self.send(frame, self.reply(request, [group(name='Fence')]))
                            page.wait_for_function('document.querySelector("#roleRows").textContent.includes("Fence")', timeout=15000)
                            self.assertNotIn('Padded', page.locator('#roleRows').inner_text())
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
                self.assertEqual(self.sent(frame), ['design:hello', 'design:detect'])
                self.unchanged_page(frame)
                self.assertEqual(errors, [])


class FnvVectorTests(unittest.TestCase):
    def test_the_digest_helper_matches_the_published_fnv1a_vectors(self):
        """Given the standard FNV-1a 32-bit test vectors, when the test helper hashes them, then it matches, so the
        receipts built from it are checked against the contract and not against Studio's own function."""
        self.assertEqual([fnv1a32(text) for text in ('', 'a', 'foobar')], [EMPTY_HASH, 'e40c292c', 'bf9cf968'])
        self.assertEqual(fnv1a32('界'), fnv1a32('界'.encode('utf-8').decode('utf-8')))
        self.assertNotEqual(fnv1a32('界'), fnv1a32('?'))


class StudioRoleDraftTests(StudioRoleCase):
    @per_engine
    def test_each_detected_row_has_empty_unchecked_draft_controls_with_observed_values_as_placeholders(self, engine):
        """Given a detected Body role observed at 16px sans-serif, when its row renders, then the checkbox is
        unchecked, every field is empty with the observed value only as a placeholder, each control has an
        accessible name, all of it sits inside the detected-roles panel, and Apply says what is missing."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.assertFalse(self.control(page, 'Preview this role').is_checked())
        observed = {'Font family': 'sans-serif', 'Size (px)': '16', 'Weight': '400', 'Line height': 'e.g. 1.5', 'Tracking (em)': '0'}
        for label, placeholder in observed.items():
            field = self.control(page, label)
            self.assertEqual((field.input_value(), field.get_attribute('placeholder')), ('', placeholder), label)
        case = self.control(page, 'Case')
        self.assertEqual(case.input_value(), '')
        self.assertEqual(case.locator('option').first.inner_text(), 'Unchanged (none)')
        self.assertEqual(page.locator('[data-role-field]').count(), page.locator('#detectedRoles [data-role-field]').count())
        self.assertIn('Detected values are the page baseline, measured without the role preview.',
                      page.locator('#detectedRoles').inner_text())
        enabled, reason = self.gate(page)
        self.assertFalse(enabled)
        self.assertIn('Tick Preview this role', reason)
        self.assertTrue(self.button(page, CLEAR).is_enabled())
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect'])
        self.unchanged_page(frame)
        self.assertEqual(errors, [])

    @per_engine
    def test_keystrokes_validate_every_intermediate_value_and_the_documented_bounds(self, engine):
        """Given a selected role, when a size is typed one key at a time and each bound is typed in full, then Apply
        follows validity after every keystroke and names the row and field when it is disabled."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.control(page, 'Preview this role').check()
        size = self.control(page, 'Size (px)')
        size.focus()
        trail = []
        for key in '401':
            size.press(key)
            trail.append(self.gate(page)[0])
        self.assertEqual(trail, [True, True, False])
        self.assertIn('Body (role-1): size not valid', self.gate(page)[1])
        size.press('Backspace')
        self.assertTrue(self.gate(page)[0])
        bounds = [('Size (px)', '3.99', False), ('Size (px)', '4', True), ('Size (px)', '400', True), ('Size (px)', '400.01', False),
                  ('Size (px)', '12.345', True), ('Size (px)', '-', False), ('Size (px)', '1e2', False),
                  ('Weight', '0', False), ('Weight', '1', True), ('Weight', '1000', True), ('Weight', '1001', False),
                  ('Weight', '450.5', False), ('Weight', '-5', False),
                  ('Line height', '0.49', False), ('Line height', '.5', True), ('Line height', '5', True), ('Line height', '5.01', False),
                  ('Tracking (em)', '-0.51', False), ('Tracking (em)', '-0.5', True), ('Tracking (em)', '2', True),
                  ('Tracking (em)', '2.01', False), ('Tracking (em)', '0.12345', True),
                  ('Font family', 'Georgia, serif', True), ('Font family', '"Times New Roman", serif', True),
                  ('Font family', '  Georgia  ', True), ('Font family', 'A' * 300, True), ('Font family', 'A' * 301, False),
                  ('Font family', "'Unbalanced", False), ('Font family', 'a;b', False), ('Font family', 'a{b', False),
                  ('Font family', 'a}', False), ('Font family', 'a<b', False), ('Font family', 'a>b', False),
                  ('Font family', 'a\\b', False), ('Font family', 'url(x)', False), ('Font family', 'expression(1)', False),
                  ('Font family', 'a /* c */', False), ('Font family', 'Georgia !important', False), ('Font family', '$$$', False)]
        self.type_value(size, '')
        for label, value, valid in bounds:
            with self.subTest(field=label, value=value):
                field = self.control(page, label)
                self.type_value(field, value)
                enabled, reason = self.gate(page)
                self.assertEqual(enabled, valid, reason)
                if not valid:
                    name = 'font family' if label == 'Font family' else label.split(' (')[0].lower()
                    self.assertIn(f'Body (role-1): {name} not valid', reason)
                    self.assertEqual(field.get_attribute('aria-invalid'), 'true')
                self.type_value(field, '')
        self.control(page, 'Case').select_option('uppercase')
        self.assertTrue(self.gate(page)[0])
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect'])
        self.assertEqual(errors, [])

    @per_engine
    def test_an_invalid_or_empty_selected_row_blocks_apply_beside_valid_ones_and_names_itself(self, engine):
        """Given three detected rows, when one selected row has an invalid field, none, or no safe selectors, then
        Apply is disabled with a reason naming that row and field, and recovers when the row is fixed or cleared."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        text_selector = [{'value': '[data-design-id="ordinary.body"]', 'stable': True, 'reason': 'author-id'}]
        loose = group('scan-c', 'Loose', None, style={**STYLE, 'fontSize': 20}, selectors=[], binding_complete=False)
        self.detected(page, frame, [group(), group('scan-b', 'Text', None, selectors=text_selector), loose])
        self.control(page, 'Preview this role').check()
        self.type_value(self.control(page, 'Size (px)'), '24')
        self.assertTrue(self.gate(page)[0])
        second = self.control(page, 'Preview this role', 'role-2', 'Text')
        second.check()
        weight = self.control(page, 'Weight', 'role-2', 'Text')
        self.type_value(weight, 'abc')
        enabled, reason = self.gate(page)
        self.assertFalse(enabled)
        self.assertIn('Text (role-2): weight not valid', reason)
        self.assertEqual(weight.get_attribute('aria-invalid'), 'true')
        self.assertIsNone(self.control(page, 'Size (px)').get_attribute('aria-invalid'))
        self.type_value(weight, '700')
        self.assertTrue(self.gate(page)[0])
        self.type_value(weight, '')
        self.assertIn('Text (role-2) needs at least one value', self.gate(page)[1])
        self.type_value(weight, 'abc')
        second.uncheck()
        self.assertTrue(self.gate(page)[0], 'an unselected row is not part of the request')
        self.assertEqual(weight.get_attribute('aria-invalid'), 'true')
        note = page.locator('#roleNote-role-2')
        self.assertTrue(note.is_visible())
        self.assertIn('Text (role-2): weight not valid', note.inner_text())
        self.assertIn('not selected, so nothing is sent for it', note.inner_text())
        self.assertEqual(weight.get_attribute('aria-describedby'), 'roleNote-role-2')
        self.type_value(weight, '700')
        self.assertTrue(note.is_hidden())
        self.assertIsNone(weight.get_attribute('aria-describedby'))
        self.type_value(weight, 'abc')
        third = self.control(page, 'Preview this role', 'role-3', 'Loose')
        third.check()
        self.assertIn('Loose (role-3) has no safe complete selectors', self.gate(page)[1])
        third.uncheck()
        self.assertTrue(self.gate(page)[0])
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect'])
        self.assertEqual(errors, [])

    @per_engine
    def test_drafts_keep_focus_text_and_caret_across_a_detect_result_and_follow_issued_ids(self, engine):
        """Given a draft being typed while a Detect is pending, when the result re-renders the rows (reordered), then
        the same field keeps focus, text and caret and keeps taking keystrokes; drafts survive a same-origin ready
        and are dropped with the issued ids when another origin connects."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.control(page, 'Preview this role').check()
        size = self.control(page, 'Size (px)')
        size.focus()
        size.press_sequentially('2')
        request = self.pending(page, frame, keep_focus=True)
        size.press_sequentially('4')
        self.send(frame, self.reply(request, [group('scan-x', 'Text', None), group('scan-y', 'Body')]))
        page.wait_for_function('document.querySelector("#roleRows").children.length===2')
        active = page.evaluate('''() => ({field: document.activeElement.dataset.roleField,
            row: document.activeElement.closest("li").dataset.roleId, value: document.activeElement.value,
            caret: document.activeElement.selectionStart})''')
        self.assertEqual(active, {'field': 'fontSize', 'row': 'role-1', 'value': '24', 'caret': 2})
        self.assertEqual(page.locator('#roleRows > li').evaluate_all('els=>els.map(e=>e.dataset.roleId)'), ['role-2', 'role-1'])
        page.keyboard.press('8')
        self.assertEqual(self.control(page, 'Size (px)').input_value(), '248')
        page.keyboard.press('Backspace')
        self.assertTrue(self.control(page, 'Preview this role').is_checked())
        frame.evaluate('ready()')
        page.wait_for_function('document.querySelector("#roleRows").children.length===0')
        self.detected(page, frame)
        self.assertEqual(self.control(page, 'Size (px)').input_value(), '24')
        self.assertTrue(self.control(page, 'Preview this role').is_checked())
        other = 'http://evil.test/peer'
        page.context.route(other, lambda route: route.fulfill(body=PEER, content_type='text/html'))
        field = page.get_by_role('textbox', name='Live App URL', exact=True)
        field.focus()
        field.press('ControlOrMeta+A')
        field.press_sequentially(other)
        page.get_by_role('button', name='Connect Live App', exact=True).click()
        page.wait_for_function('document.querySelector("#bridgeStatusBadge").textContent.startsWith("Connected") && document.querySelector("#roleStatus").textContent==="Ready to detect text styles."')
        frame = next(f for f in page.frames if f.url.startswith('http://evil.test'))
        self.page_url = other
        self.detected(page, frame)
        self.assertFalse(self.control(page, 'Preview this role').is_checked())
        self.assertEqual(self.control(page, 'Size (px)').input_value(), '')
        self.assertEqual(errors, [])


def loss(prop='fontSize', count=1, selector=None, reason='author-rule'):
    return {'property': prop, 'count': count, 'winningSelector': selector, 'reason': reason}


def outcome(**fields):
    return {'id': 'role-1', 'matched': 3, 'checked': 3, 'mismatched': 0, 'complete': True, 'losses': [], **fields}


class StudioRoleApplyTests(StudioRoleCase):
    @per_engine
    def test_apply_sends_the_exact_plain_request_and_shows_only_the_acknowledged_receipt(self, engine):
        """Given a Body role with every property typed by keystrokes, when Apply is pressed, then the peer receives
        exactly one plain roles-apply with the trimmed canonical values and nothing renders as accepted until the
        receipt arrives; the receipt's CSS, status and counts then render and nothing else changes."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        badge = page.locator('#bridgeStatusBadge').inner_text()
        detect_status = page.locator('#roleStatus').inner_text()
        self.control(page, 'Preview this role').check()
        for label, value in (('Font family', '  Georgia, serif  '), ('Size (px)', '24'), ('Weight', '700'),
                             ('Line height', '1.5'), ('Tracking (em)', '0.05')):
            self.type_value(self.control(page, label), value)
        self.control(page, 'Case').select_option('uppercase')
        self.button(page, APPLY).click()
        self.wait_for_ops(frame, 'design:roles-apply', 1)
        request = self.ops(frame, 'design:roles-apply')[0]
        self.assertTrue(request.pop('requestId').startswith('fks-req-'))
        self.assertTrue(request.pop('sessionId'))
        self.assertEqual(request, {
            'type': 'design:roles-apply', 'protocolVersion': 1, 'baseRevision': 0, 'documentId': 'peer-document',
            'pageVersion': 0, 'roles': [{'id': 'role-1', 'name': 'Body', 'selectors': ['.body-copy'], 'adapter': 'plain',
            'properties': {'fontFamily': 'Georgia, serif', 'fontSize': 24, 'fontWeight': 700, 'lineHeight': 1.5,
                           'letterSpacing': 0.05, 'textTransform': 'uppercase'}}]})
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['status']), ('', 'Applying role preview…'))
        request = self.ops(frame, 'design:roles-apply')[0]
        receipt = self.receipt(request)
        self.send(frame, receipt)
        self.wait_status(page, 'Preview applied to 1 role')
        shown = self.preview(page)
        self.assertEqual(shown['css'], receipt['canonicalCss'])
        self.assertEqual(shown['status'], 'Preview applied to 1 role; 0 checked elements did not show it.')
        self.assertIn('Body (role-1): matched 1, checked 1 eligible text elements, mismatched 0', shown['outcomes'])
        self.assertEqual(page.locator('#roleStatus').inner_text(), detect_status)
        self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), badge)
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        self.assertEqual(self.control(page, 'Size (px)').input_value(), '24')
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:roles-apply'])
        self.unchanged_page(frame)
        self.assertEqual(errors, [])

    @per_engine
    def test_complete_zero_match_stale_budget_and_clear_receipts_render_their_own_state(self, engine):
        """Given a sequence of applies, when the peer answers with losses, a zero-element result, a stale receipt, a
        budget-limited one and a clear, then each renders its own counts and reasons as the receipt states them, a
        stale receipt keeps the accepted CSS and advances the page version, and Clear empties the preview."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        self.send(frame, self.receipt(request, [outcome(mismatched=2, losses=[
            loss('fontSize', 2, '.hero > p', 'author-rule'), loss('fontWeight', 1, None, 'inline')])]))
        self.wait_status(page, 'Preview applied to 1 role; 2 checked elements did not show it.')
        text = self.preview(page)['outcomes']
        self.assertIn('Body (role-1): matched 3, checked 3 eligible text elements, mismatched 2', text)
        self.assertIn('2 × fontSize: overridden by .hero > p', text)
        self.assertIn('1 × fontWeight: overridden by inline style', text)
        request = self.apply_role(page, frame, '25')
        self.send(frame, self.receipt(request, [outcome(matched=0, checked=0)]))
        page.wait_for_function('document.querySelector("#rolePreviewOutcomes").textContent.includes("no eligible text found")')
        request = self.apply_role(page, frame, '25')
        self.send(frame, self.receipt(request, [outcome(matched=4, checked=0)]))
        page.wait_for_function('document.querySelector("#rolePreviewOutcomes").textContent.includes("matched 4, checked 0")')
        text = self.preview(page)['outcomes']
        self.assertIn('no eligible text found', text)
        request = self.apply_role(page, frame, '25')
        self.send(frame, self.receipt(request, [outcome(matched=5, checked=3)]))
        page.wait_for_function('document.querySelector("#rolePreviewOutcomes").textContent.includes("matched 5, checked 3")')
        text = self.preview(page)['outcomes']
        self.assertIn('2 matched elements have no rendered text and were not measured', text)
        self.assertNotIn('no eligible text found', text)
        request = self.apply_role(page, frame, '26')
        stale = self.receipt(request, [], currentPageVersion=request['pageVersion'] + 3, outcomesComplete=False, outcomeReason='page-changed')
        self.send(frame, stale)
        self.wait_status(page, STALE)
        shown = self.preview(page)
        self.assertEqual((shown['status'], shown['css'], shown['outcomes']), (STALE, stale['canonicalCss'], ''))
        self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
        request = self.apply_role(page, frame, '27')
        self.assertEqual(request['pageVersion'], 3)
        budget = self.receipt(request, [outcome(matched=5, checked=2, mismatched=1, complete=False,
                                                losses=[loss('fontSize', 1, None, 'complex-cascade')])],
                              outcomesComplete=False, outcomeReason='budget-exceeded')
        self.send(frame, budget)
        page.wait_for_function('document.querySelector("#rolePreviewOutcomes").textContent.includes("Checks incomplete (budget-exceeded)")')
        text = self.preview(page)['outcomes']
        self.assertIn('matched 5, checked 2 eligible text elements, mismatched 1 (incomplete)', text)
        self.assertIn('1 × fontSize: overridden; source not provable', text)
        request = self.clear_preview(page, frame)
        self.send(frame, self.receipt(request))
        self.wait_status(page, 'Preview cleared.')
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['outcomes'], shown['removed']), ('', '', 'Removed from the preview: Body.'))
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        self.unchanged_page(frame)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_stale_receipt_with_an_unsupported_url_keeps_the_preview_and_disables_detect_and_apply(self, engine):
        """Given a committed apply whose page then moved to an unsupported URL, when the stale receipt carries a null
        URL, then the CSS stays shown, Detect and Apply are disabled with the unavailable reason, Clear stays
        enabled, and a null-URL clear receipt empties the preview."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        receipt = self.receipt(request, [], currentPageVersion=1, currentPageURL=None, outcomesComplete=False, outcomeReason='page-changed')
        self.send(frame, receipt)
        self.wait_status(page, STALE)
        self.assertEqual(self.preview(page)['css'], receipt['canonicalCss'])
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(page.locator('#roleStatus').inner_text(), UNAVAILABLE)
        self.assertEqual(page.locator('#roleRows > li').count(), 0)
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        self.assertTrue(self.button(page, CLEAR).is_enabled())
        request = self.clear_preview(page, frame)
        self.assertEqual(request['pageVersion'], 1)
        self.send(frame, self.receipt(request, currentPageURL=None))
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(errors, [])

    @per_engine
    def test_ready_with_an_unsupported_url_disables_apply_but_keeps_clear_and_shows_the_accepted_preview(self, engine):
        """Given a ready whose page URL is unavailable and which carries an accepted role, when Studio shows it, then
        the preview is visible, Apply and Detect are disabled with the unavailable reason, Clear works and its
        null-URL receipt is accepted."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        state = self.snapshot_state([self.role_input()], pageURL=None)
        self.ready_with(page, frame, state, revision=2)
        self.assertEqual(self.preview(page)['css'], state['canonicalCss'])
        self.assertEqual(page.locator('#roleStatus').inner_text(), UNAVAILABLE)
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        request = self.clear_preview(page, frame)
        self.assertEqual((request['baseRevision'], request['pageVersion']), (2, 0))
        self.send(frame, self.receipt(request, currentPageURL=None))
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(self.sent(frame), ['design:hello', 'design:roles-clear'])
        self.assertEqual(errors, [])

    def hostile_receipts(self, request):
        """Receipts that break one rule of the contract each, built from the request the peer received."""
        role = request['roles'][0]
        ok = self.receipt(request)
        first = ok['outcomes'][0]
        base = request['baseRevision']
        def drop(key):
            return {k: v for k, v in ok.items() if k != key}
        def with_role(**changes):
            return {'roles': [{**role, **changes}]}
        def with_outcome(**changes):
            return {'outcomes': [{**first, **changes}]}
        shapes = {
            'wrong request id': {'requestId': 'fks-req-9999'}, 'wrong operation': {'operation': 'clear'},
            'revision unchanged': {'revision': base}, 'revision skips ahead': {'revision': base + 2},
            'negative revision': {'revision': -1}, 'wrong document': {'documentId': 'other-document'},
            'wrong captured version': {'pageVersion': 3, 'currentPageVersion': 3},
            'current before captured': {'currentPageVersion': request['pageVersion'] - 1},
            'complete but page moved': {'currentPageVersion': request['pageVersion'] + 1},
            'complete but route moved': {'currentPageURL': TARGET + '/other'},
            'complete with null route': {'currentPageURL': None},
            'foreign route': {'currentPageURL': 'http://evil.test/x'},
            'credential route': {'currentPageURL': 'http://user:pw@target.test/peer'},
            'over-long route': {'currentPageURL': TARGET + '/' + 'x' * 2000},
            'script route': {'currentPageURL': 'javascript:alert(1)'},
            'budget with null route': {'outcomesComplete': False, 'outcomeReason': 'budget-exceeded', 'currentPageURL': None},
            'budget with moved route': {'outcomesComplete': False, 'outcomeReason': 'budget-exceeded', 'currentPageURL': TARGET + '/other'},
            'stale with outcomes': {'outcomesComplete': False, 'outcomeReason': 'page-changed'},
            'complete flag with a reason': {'outcomeReason': 'page-changed'},
            'incomplete flag without a reason': {'outcomesComplete': False},
            'invented reason': {'outcomesComplete': False, 'outcomeReason': 'invented', 'outcomes': []},
            'wrong digest': {'cssHash': '00000000'}, 'other algorithm': {'hashAlgorithm': 'sha256'},
            'css edited without its digest': {'canonicalCss': 'x'},
            'css over 128 KiB with its own digest': self.with_css(ok, 'a' * (128 * 1024 + 1)),
            'css unrelated to the roles with its own digest': self.with_css(ok, 'p { color: red; }\n'),
            'css with the roles plus an extra rule and its own digest': self.with_css(ok, ok['canonicalCss'] + 'p { color: red; }\n'),
            'no roles for an apply': {'roles': [], 'canonicalCss': '', 'cssHash': EMPTY_HASH, 'outcomes': []},
            'role id differs': {**with_role(id='role-9'), **with_outcome(id='role-9')},
            'extra role': {'roles': [role, {**role, 'id': 'role-2'}]},
            'body selector': with_role(selectors=['body']), 'unknown adapter': with_role(adapter='nope'),
            'empty properties': with_role(properties={}), 'colour property': with_role(properties={'color': 'red'}),
            'family with semicolon': with_role(properties={'fontFamily': 'a;b'}),
            'size out of range': with_role(properties={'fontSize': 3}), 'extra role key': with_role(extra=1),
            'proto key in role': with_role(**{'__proto__': {}}),
            'duplicate outcome': {'outcomes': [first, first]}, 'outcome for an unknown role': with_outcome(id='role-9'),
            'checked above matched': with_outcome(matched=1, checked=2),
            'mismatched above checked': with_outcome(matched=2, checked=2, mismatched=3),
            'negative count': with_outcome(mismatched=-1), 'count above ten thousand': with_outcome(matched=10001, checked=10001),
            'nonfinite count': with_outcome(matched=float('inf')),
            'outcome without complete': {'outcomes': [{k: v for k, v in first.items() if k != 'complete'}]},
            'complete not a boolean': with_outcome(complete='yes'),
            'constructor in outcome': with_outcome(constructor={}),
            'loss count zero': with_outcome(losses=[loss(count=0)]),
            'loss property as css name': with_outcome(losses=[loss(prop='font-size')]),
            'loss reason invented': with_outcome(losses=[loss(reason='invented')]),
            'loss selector empty': with_outcome(losses=[loss(selector='')]),
            'loss selector over 2000 characters': with_outcome(losses=[loss(selector='.' + 'a' * 2000)]),
            'loss selector with a line break': with_outcome(losses=[loss(selector='.a' + chr(10) + '.b')]),
            'loss selector with a null character': with_outcome(losses=[loss(selector='.a' + chr(0))]),
            'loss selector with a C1 control': with_outcome(losses=[loss(selector='.a' + chr(0x85))]),
            'loss selector with a line separator': with_outcome(losses=[loss(selector='.a' + chr(0x2028))]),
            'loss selector with a paragraph separator': with_outcome(losses=[loss(selector='.a' + chr(0x2029))]),
            'loss selector not text': with_outcome(losses=[loss(selector=5)]),
            'loss extra key': with_outcome(losses=[{**loss(), 'extra': 1}]),
            'extra receipt key': {'extra': True},
        }
        hostile = {name: {**ok, **change} for name, change in shapes.items()}
        hostile['missing digest'] = drop('cssHash')
        hostile['missing outcomes'] = drop('outcomes')
        return ok, hostile

    @per_engine
    def test_every_hostile_receipt_is_ignored_until_the_valid_fence_settles_the_request(self, engine):
        """Given an Apply in flight on a page at version 2, when each hostile or inconsistent receipt arrives followed
        by one valid fence receipt, then the fence is what the preview shows (so the hostile one changed nothing and
        left the request in flight); the failing shape is named by its subtest."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame, pageVersion=2, currentPageVersion=2)
        request = self.apply_role(page, frame, '24')
        names = list(self.hostile_receipts(request)[1])
        for index, name in enumerate(names):
            with self.subTest(shape=name):
                if index:
                    request = self.apply_role(page, frame, '24')   # a new request each time, so one failing shape cannot cascade
                ok, hostile = self.hostile_receipts(request)
                marker = 100 + index
                fence = {**ok, 'outcomes': [outcome(matched=marker, checked=marker)]}
                self.send(frame, hostile[name])
                self.send(frame, fence)
                page.wait_for_function('(text) => document.querySelector("#rolePreviewOutcomes").textContent.includes(text)',
                                       arg=f'matched {marker},', timeout=4000)
                self.assertEqual(self.preview(page)['css'], ok['canonicalCss'])
                self.assertEqual(self.preview(page)['status'], 'Preview applied to 1 role; 0 checked elements did not show it.')
        self.assertEqual(errors, [])

    @per_engine
    def test_apply_refuses_a_request_over_256_kib_counted_in_utf8_bytes_and_names_the_limit(self, engine):
        """Given 128 selected roles whose multi-byte selectors are under 256 KiB as characters but over it as UTF-8,
        when Apply is considered, then it is disabled with the request-limit reason; unselecting enough rows makes
        the same selectors fit and Apply sends them."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        roles = [self.role_input(f'role-{i}', f'Author {i}', fontSize=20) for i in range(1, 129)]
        self.ready_with(page, frame, self.snapshot_state(roles), revision=0)
        selector = [{'value': '.' + '界' * 700, 'stable': True, 'reason': 'class'}]
        self.detected(page, frame, [group(f'g-{i}', f'Author {i}', f'Author {i}', selectors=selector) for i in range(1, 129)])
        self.assertLess(len(json.dumps(roles, ensure_ascii=False)) + 128 * 700, 256 * 1024)
        enabled, reason = self.gate(page)
        self.assertFalse(enabled)
        self.assertIn('256 KiB', reason)
        for i in range(1, 41):
            self.control(page, 'Preview this role', f'role-{i}', f'Author {i}').uncheck()
        self.assertTrue(self.gate(page)[0])
        request = self.press_apply(page, frame)
        self.assertEqual(len(request['roles']), 88)
        self.assertEqual(errors, [])

    @per_engine
    def test_typed_fractions_are_rounded_to_the_contract_decimals_in_the_sent_request(self, engine):
        """Given fractions typed with more decimals than the contract allows, when Apply is pressed, then the request
        carries them rounded to 2 (size), 3 (line height) and 4 (tracking) decimals."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.control(page, 'Preview this role').check()
        for label, value in (('Size (px)', '12.346'), ('Line height', '1.2346'), ('Tracking (em)', '0.12346')):
            self.type_value(self.control(page, label), value)
        request = self.press_apply(page, frame)
        self.assertEqual(request['roles'][0]['properties'], {'fontSize': 12.35, 'lineHeight': 1.235, 'letterSpacing': 0.1235})
        self.assertEqual(errors, [])

    @per_engine
    def test_a_receipt_never_lowers_a_newer_page_generation_learned_from_a_detect(self, engine):
        """Given an Apply in flight and a Detect that reports page version 5, when the Apply's receipt reports
        version 0, then the receipt is accepted but the next request still carries version 5."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        detect = self.pending(page, frame)
        self.send(frame, self.reply(detect, pageVersion=5, currentPageVersion=5))
        page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected")')
        self.send(frame, self.receipt(request))
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(self.press_apply(page, frame)['pageVersion'], 5)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_late_design_applied_with_a_timed_out_role_ops_id_does_not_settle_it(self, engine):
        """Given an Apply that timed out, when a legacy design:applied carrying its request id arrives, then it
        changes nothing, and the Apply's own late receipt is still accepted and rendered."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.startsWith("No response to apply")', timeout=20000)
        badge = page.locator('#bridgeStatusBadge').inner_text()
        self.send(frame, {'type': 'design:applied', 'requestId': request['requestId'], 'revision': 1, 'targetId': 'global',
                          'canonicalPatch': {}, 'changes': {'tokens': {}, 'targets': [], 'structure': [], 'imports': []}})
        self.settle(page, frame)
        self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), badge)
        receipt = self.receipt(request)
        self.send(frame, receipt)
        page.wait_for_function('(css) => document.querySelector("#rolePreviewCss").textContent === css', arg=receipt['canonicalCss'])
        self.assertEqual(self.preview(page)['status'], 'Preview applied to 1 role; 0 checked elements did not show it.')
        self.assertEqual(errors, [])

    @per_engine
    def test_an_ignored_late_receipt_keeps_the_status_and_counts_of_the_preview_still_shown(self, engine):
        """Given a timed-out Apply and a newer Apply that was accepted with losses, when the first one's late receipt
        arrives, then the CSS and counts stay and the status gains a note that the late receipt was ignored."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        first = self.apply_role(page, frame, '24')
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.startsWith("No response to apply")', timeout=20000)
        second = self.apply_role(page, frame, '25')
        accepted = self.receipt(second, [outcome(mismatched=2, losses=[loss()])])
        self.send(frame, accepted)
        self.wait_status(page, 'Preview applied to 1 role; 2 checked elements did not show it.')
        self.send(frame, self.receipt(first))
        self.wait_status(page, 'late acknowledgement for an older preview was ignored')
        shown = self.preview(page)
        self.assertTrue(shown['status'].startswith('Preview applied to 1 role; 2 checked elements did not show it.'))
        self.assertEqual(shown['css'], accepted['canonicalCss'])
        self.assertIn('matched 3, checked 3 eligible text elements, mismatched 2', shown['outcomes'])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_receipt_from_a_foreign_origin_while_the_op_is_in_flight_changes_nothing(self, engine):
        """Given an Apply in flight and the target frame navigating to another origin whose page loads slowly, when
        that page posts a receipt with the right session and request id before it finishes loading, then Studio
        ignores it because of its origin."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        message = {**self.receipt(request), 'protocolVersion': 1, 'sessionId': request['sessionId']}
        script = ('<img src="/hold.png"><script>parent.postMessage(' + json.dumps(message) + ', "http://studio.test")</script>')
        held = []
        page.context.route('http://evil.test/hold.png', lambda route: held.append(route))
        page.context.route('http://evil.test/receipt.html', lambda route: route.fulfill(body=script, content_type='text/html'))
        frame.evaluate('setTimeout(() => { location.href = "http://evil.test/receipt.html" }, 0)')
        for _ in range(200):
            if held:
                break
            page.wait_for_timeout(50)
        self.assertTrue(held, 'the foreign page is still loading')
        self.settle(page, frame)
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['status']), ('', 'Applying role preview…'))
        for route in held:
            route.fulfill(status=204)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_winning_selector_is_bounded_text_and_every_reason_reads_in_plain_words(self, engine):
        """Given a receipt whose losses name author selectors (descendant, list, pseudo-class, root-based, markup, and
        exactly 2,000 characters) and every other reason, when it settles, then it is accepted, each selector shows only
        as text and each reason reads in plain words."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        markup = '<img src=x onerror="document.body.dataset.bad=1">'
        long = '.' + 'a' * 1999
        named = [loss('fontSize', 1, selector, 'author-rule') for selector in ('.card p', 'h1, .card p', 'a:hover', 'body p', markup, long)]
        others = [loss('fontSize', 1, 'body', 'inherited'), loss('fontWeight', 1, None, 'inline'),
                  loss('lineHeight', 1, None, 'unreadable-sheet'), loss('letterSpacing', 1, None, 'complex-cascade'),
                  loss('textTransform', 1, None, 'stylesheet-blocked'), loss('fontFamily', 1, None, 'budget-exceeded')]
        self.send(frame, self.receipt(request, [outcome(matched=12, checked=12, mismatched=12, losses=named + others)]))
        self.wait_status(page, 'Preview applied to 1 role; 12 checked elements did not show it.')
        text = self.preview(page)['outcomes']
        for selector in ('.card p', 'h1, .card p', 'a:hover', 'body p', markup, long):
            self.assertIn(f'1 × fontSize: overridden by {selector}', text)
        for line in ('1 × fontSize: inherits from parent via body', '1 × fontWeight: overridden by inline style',
                     '1 × lineHeight: a stylesheet could not be read', '1 × letterSpacing: overridden; source not provable',
                     '1 × textTransform: the page disabled the preview sheet', '1 × fontFamily: not attributed in time'):
            self.assertIn(line, text)
        self.assertEqual(page.locator('#detectedRoles img').count(), 0)
        self.assertIsNone(page.locator('body').get_attribute('data-bad'))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_revision_conflict_with_the_bridges_object_detail_settles_the_op_and_adopts_the_revision(self, engine):
        """Given an Apply that the bridge rejects as a revision conflict with its real detail object, when the
        rejection arrives, then the op settles at once, the status gives the next step and both revisions as text, and
        the next Apply is based on the bridge's revision."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': 7, 'reason': 'revision-conflict',
                          'detail': {'baseRevision': 0, 'revision': 7}})
        self.wait_status(page, 'rejected (revision-conflict)')
        status = self.preview(page)['status']
        self.assertIn('press the button again', status)
        self.assertIn('Detail: base revision 0, bridge revision 7', status)
        self.assertEqual(self.press_apply(page, frame)['baseRevision'], 7)
        self.assertEqual(errors, [])

    @per_engine
    def test_outcome_limits_follow_what_the_bridge_can_send(self, engine):
        """Given a receipt that matches 250,000 elements and lists 96 loss entries (16 groups for each of six
        properties), when it arrives, then Studio accepts and shows it; a 97th entry or more than 10,000 checked
        elements is refused."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        props = ('fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform', 'fontFamily')
        losses = [loss(prop, 1, f'main p.c{i}', 'author-rule') for prop in props for i in range(16)]
        self.send(frame, self.receipt(request, [outcome(matched=250000, checked=96, mismatched=96, losses=losses + [loss()])]))
        self.send(frame, self.receipt(request, [outcome(matched=250000, checked=10001, mismatched=1)]))
        self.send(frame, self.receipt(request, [outcome(matched=250000, checked=96, mismatched=96, losses=losses)]))
        self.wait_status(page, 'Preview applied to 1 role; 96 checked elements did not show it.')
        text = self.preview(page)['outcomes']
        self.assertIn('matched 250000, checked 96 eligible text elements, mismatched 96', text)
        self.assertEqual(text.count(' × '), 96)
        self.assertEqual(errors, [])

    @per_engine
    def test_receipts_from_the_wrong_session_protocol_or_source_change_nothing(self, engine):
        """Given an Apply in flight, when a valid-looking receipt arrives with another session, protocol, from the
        Studio window itself or from a nested frame, then none settles it; only the real peer's receipt does."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        receipt = self.receipt(request)
        marked = {**receipt, 'outcomes': [outcome(matched=9, checked=9)]}
        self.send(frame, marked, sessionId='wrong-session')
        self.send(frame, marked, protocolVersion=2)
        page.evaluate('(data)=>window.postMessage(data,location.origin)', {**marked, 'sessionId': request['sessionId'], 'protocolVersion': 1})
        frame.evaluate('data=>new Promise(resolve=>{let child=document.createElement("iframe");child.onload=resolve;child.srcdoc="<script>parent.parent.postMessage("+JSON.stringify(data)+",\\\"http://studio.test\\\")<"+"/script>";document.body.append(child)})',
                       {**marked, 'sessionId': request['sessionId'], 'protocolVersion': 1})
        self.send(frame, receipt)
        page.wait_for_function('document.querySelector("#rolePreviewOutcomes").textContent.includes("matched 1,")', timeout=4000)
        self.assertNotIn('matched 9', self.preview(page)['outcomes'])
        self.assertEqual(errors, [])

    def sized_receipt(self, request, size):
        """A receipt for the request whose canonical CSS is exactly `size` UTF-8 bytes of real serialization: a multi-byte
        family per role, padded by selector length (the page may report other properties than were sent; ids must match)."""
        roles = [{**role, 'selectors': ['.body-copy'], 'properties': {'fontFamily': '\u754c' * 300}} for role in request['roles']]
        missing = size - len(canonical_css(roles).encode('utf-8'))
        for role in roles:
            add = min(missing, 1990)
            role['selectors'] = ['.' + 'a' * (len('body-copy') + add)]
            missing -= add
        css = canonical_css(roles)
        self.assertEqual(len(css.encode('utf-8')), size)
        return {**self.receipt(request), 'roles': roles, 'canonicalCss': css, 'cssHash': fnv1a32(css)}

    @per_engine
    def test_a_receipt_css_at_128_kib_is_accepted_and_one_byte_more_is_not(self, engine):
        """Given 128 accepted roles and an Apply in flight, when the receipt's canonical CSS (a real serialization with
        multi-byte family names) is one byte over 128 KiB it is ignored, and at exactly 128 KiB it is what renders."""
        limit = 128 * 1024
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        roles = [self.role_input(f'role-{i}', f'Author {i}', fontSize=20) for i in range(1, 129)]
        self.ready_with(page, frame, self.snapshot_state(roles), revision=0)
        self.detected(page, frame, [group(f'g-{i}', f'Author {i}', f'Author {i}') for i in range(1, 129)])
        request = self.press_apply(page, frame)
        over = self.sized_receipt(request, limit + 1)
        fence = self.sized_receipt(request, limit)
        self.assertGreater(len(over['canonicalCss'].encode('utf-8')), limit)
        self.send(frame, over)
        self.send(frame, fence)
        page.wait_for_function('(css) => document.querySelector("#rolePreviewCss").textContent === css', arg=fence['canonicalCss'], timeout=10000)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not(self, engine):
        """Given 128 accepted roles seeded from ready and a receipt padded through valid loss selectors and CSS, when
        the reply is exactly 1 MiB or 1 MiB + 1 bytes, then only the first settles the Apply."""
        limit = 1024 * 1024
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        roles = [self.role_input(f'role-{i}', f'Author {i}', fontSize=20) for i in range(1, 129)]
        self.ready_with(page, frame, self.snapshot_state(roles), revision=0)
        self.detected(page, frame, [group(f'g-{i}', f'Author {i}', f'Author {i}') for i in range(1, 129)])
        for size, accepted in ((limit + 1, False), (limit, True)):
            with self.subTest(size=size):
                request = self.press_apply(page, frame)
                def build(full, first, second):
                    losses = [loss(selector='.' + 'a' * 1999) for _ in range(full)] + [loss(selector='.' + 'a' * first), loss(selector='.' + 'a' * second)]
                    chunks = [losses[n:n + 64] for n in range(0, len(losses), 64)]
                    outcomes = [outcome(id=f'role-{i + 1}', mismatched=len(c), matched=len(c), checked=len(c), losses=c)
                                for i, c in enumerate(chunks)]
                    return self.receipt(request, outcomes)
                def measure(*shape):
                    envelope = {'protocolVersion': 1, 'sessionId': request['sessionId'], **build(*shape)}
                    return len(json.dumps(envelope, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
                full = 0
                while measure(full + 1, 1, 1) <= size:
                    full += 1
                rest = size - measure(full, 1, 1)
                first = 1 + min(rest, 1998)
                second = 1 + rest - (first - 1)
                self.assertEqual(measure(full, first, second), size)
                self.send(frame, build(full, first, second))
                if accepted:
                    wanted = 'matched 64,'
                else:
                    self.send(frame, self.receipt(request, [outcome(matched=7, checked=7)]))
                    wanted = 'matched 7,'
                page.wait_for_function('(text) => document.querySelector("#rolePreviewOutcomes").textContent.includes(text)', arg=wanted, timeout=15000)
        self.assertEqual(errors, [])


EMPTY_LEDGER = {'tokens': {}, 'targets': [], 'structure': [], 'imports': []}


class StudioLegacyCase(StudioRoleCase):
    def legacy_in_flight(self, page, frame):
        """Reset all page edits, accepted: a legacy op the peer receives and does not answer yet."""
        count = len(self.ops(frame, 'design:reset'))
        page.once('dialog', lambda dialog: dialog.accept())
        self.button(page, RESET_ALL).click()
        self.wait_for_ops(frame, 'design:reset', count + 1)
        return self.ops(frame, 'design:reset')[-1]

    def applied(self, request, **changes):
        return {'type': 'design:applied', 'requestId': request['requestId'], 'revision': request['baseRevision'] + 1,
                'targetId': 'global', 'canonicalPatch': {}, 'reset': True, 'changes': EMPTY_LEDGER, **changes}

    def quiet(self, page):
        """A short wait that proves something did not happen; nothing can be awaited for an absence."""
        page.wait_for_timeout(300)

    def select_for_apply(self, page, size='24'):
        self.control(page, 'Preview this role').check()
        self.type_value(self.control(page, 'Size (px)'), size)


class StudioRoleQueueTests(StudioLegacyCase):
    @per_engine
    def test_a_role_op_queues_behind_a_legacy_op_and_each_reply_settles_only_its_own_kind(self, engine):
        """Given a legacy reset in flight and Apply queued behind it, when a role receipt carries the reset's id and
        later a design:applied carries the Apply's id, then neither settles anything; Detect still goes out while
        Apply waits; each op is sent only after its own predecessor's matching reply, with the current revision."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.select_for_apply(page)
        reset = self.legacy_in_flight(page, frame)
        self.button(page, APPLY).click()
        self.quiet(page)
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:reset'])
        self.pending(page, frame)
        self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
        lookalike = self.receipt({'type': 'design:roles-apply', 'requestId': reset['requestId'], 'baseRevision': reset['baseRevision'],
                                  'documentId': 'peer-document', 'pageVersion': 0, 'roles': [self.role_input()]})
        self.send(frame, lookalike)
        self.quiet(page)
        self.assertEqual(self.ops(frame, 'design:roles-apply'), [])
        self.send(frame, self.applied(reset))
        self.wait_for_ops(frame, 'design:roles-apply', 1)
        apply = self.ops(frame, 'design:roles-apply')[0]
        self.assertEqual(apply['baseRevision'], 1)
        self.send(frame, self.applied(apply))
        self.send(frame, self.reply(self.ops(frame, 'design:detect')[-1], requestId=apply['requestId']))
        self.button(page, CLEAR).click()
        self.quiet(page)
        self.assertEqual(self.ops(frame, 'design:roles-clear'), [])
        self.send(frame, self.receipt(apply))
        self.wait_for_ops(frame, 'design:roles-clear', 1)
        self.assertEqual(self.ops(frame, 'design:roles-clear')[0]['baseRevision'], 2)
        self.assertEqual(errors, [])

    @per_engine
    def test_role_rejections_keep_the_preview_and_drafts_show_next_steps_and_are_never_retried(self, engine):
        """Given an accepted preview, when each rejection reason answers a second Apply, then the status names the
        reason and that the previous preview is kept, page-changed and revision-conflict say what to do next, the
        preview and typed drafts are unchanged and nothing is sent again."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        first = self.apply_role(page, frame, '24')
        accepted = self.receipt(first)
        self.send(frame, accepted)
        self.wait_status(page, 'Preview applied to 1 role')
        steps = {'invalid-message': '', 'unsupported-value': '', 'size-limit': '', 'stylesheet-blocked': '',
                 'page-changed': 'press Detect text styles, then try again', 'revision-conflict': 'press the button again'}
        for reason, step in steps.items():
            with self.subTest(reason=reason):
                request = self.apply_role(page, frame, '30')
                sends = len(self.ops(frame, 'design:roles-apply'))
                self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'],
                                  'revision': request['baseRevision'], 'reason': reason})
                self.wait_status(page, f'Role preview apply rejected ({reason}); the previous preview is kept.')
                self.assertIn(step, self.preview(page)['status'])
                self.quiet(page)
                self.assertEqual(len(self.ops(frame, 'design:roles-apply')), sends)
                self.assertEqual(self.preview(page)['css'], accepted['canonicalCss'])
                self.assertEqual(self.control(page, 'Size (px)').input_value(), '30')
        request = self.apply_role(page, frame, '31')
        self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': request['baseRevision'] + 5,
                          'reason': 'revision-conflict', 'detail': '<img src=x onerror=alert(1)>'})
        self.wait_status(page, 'Detail: <img src=x onerror=alert(1)>')
        self.assertEqual(page.locator('#detectedRoles img').count(), 0)
        request = self.apply_role(page, frame, '32')
        self.assertEqual(request['baseRevision'], first['baseRevision'] + 6, 'a validated rejection raises the revision')
        self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': request['baseRevision'],
                          'reason': 'invalid-message', 'detail': 'd' * 300})
        self.wait_status(page, 'Detail: ' + 'd' * 200)
        self.assertNotIn('d' * 201, self.preview(page)['status'])
        self.assertEqual(errors, [])

    @per_engine
    def test_malformed_rejections_are_ignored_and_leave_the_request_in_flight(self, engine):
        """Given an Apply in flight, when rejections with an extra key, an unknown reason, a non-text detail or a bad
        revision arrive before a valid receipt, then only the receipt settles it."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        good = {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': 0, 'reason': 'size-limit'}
        conflict = {'baseRevision': 0, 'revision': 3}
        for name, change in {'extra key': {'extra': 1}, 'unknown reason': {'reason': 'invented'}, 'detail not text': {'detail': 5},
                             'negative revision': {'revision': -1}, 'text revision': {'revision': 'x'},
                             'object detail on another reason': {'detail': conflict},
                             'conflict detail with an extra key': {'reason': 'revision-conflict', 'detail': {**conflict, 'extra': 1}},
                             'conflict detail missing a key': {'reason': 'revision-conflict', 'detail': {'revision': 3}},
                             'conflict detail negative': {'reason': 'revision-conflict', 'detail': {'baseRevision': -1, 'revision': 3}},
                             'conflict detail text': {'reason': 'revision-conflict', 'detail': {'baseRevision': '0', 'revision': 3}}}.items():
            with self.subTest(shape=name):
                self.send(frame, {**good, **change})
        receipt = self.receipt(request)
        self.send(frame, receipt)
        page.wait_for_function('(css) => document.querySelector("#rolePreviewCss").textContent === css', arg=receipt['canonicalCss'])
        self.assertNotIn('rejected', self.preview(page)['status'])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_silent_peer_times_out_the_role_op_and_a_late_receipt_is_still_accepted(self, engine):
        """Given an Apply nobody answers, when the request times out, then the status says so and the preview is
        unchanged; a receipt that arrives late for the same session, document and operation is accepted."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.startsWith("No response to apply")', timeout=20000)
        self.assertEqual(self.preview(page)['css'], '')
        receipt = self.receipt(request)
        self.send(frame, receipt)
        page.wait_for_function('(css) => document.querySelector("#rolePreviewCss").textContent === css', arg=receipt['canonicalCss'])
        self.assertEqual(self.preview(page)['status'], 'Preview applied to 1 role; 0 checked elements did not show it.')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_role_timeout_releases_the_queue_for_the_next_role_op(self, engine):
        """Given an Apply nobody answers and a Clear queued behind it, when the Apply times out, then the Clear is
        sent with the unchanged revision."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.apply_role(page, frame, '24')
        self.button(page, CLEAR).click()
        self.quiet(page)
        self.assertEqual(self.ops(frame, 'design:roles-clear'), [])
        self.wait_for_ops(frame, 'design:roles-clear', 1)
        self.assertEqual(self.ops(frame, 'design:roles-clear')[0]['baseRevision'], 0)
        self.assertEqual(errors, [])

    def reload_peer(self, page, frame):
        frame.evaluate('setTimeout(() => location.reload(), 0)')
        page.wait_for_function('document.querySelector("#roleStatus").textContent === "Ready to detect text styles."')
        self.settle(page, frame)

    @per_engine
    def test_a_reload_while_a_role_op_is_queued_sends_nothing_to_the_new_document(self, engine):
        """Given Apply queued behind a legacy op, when the page reloads, then the new document receives only hello
        and Studio says the request was dropped and an explicit Apply is needed."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.select_for_apply(page)
        self.legacy_in_flight(page, frame)
        self.button(page, APPLY).click()
        self.quiet(page)
        self.reload_peer(page, frame)
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("dropped")')
        self.assertIn('Apply or Clear again', self.preview(page)['status'])
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_reload_while_a_role_op_is_in_flight_drops_it_and_the_old_receipt_changes_nothing(self, engine):
        """Given an Apply in flight, when the page reloads, then Studio shows the dropped status, the new document
        gets no roles-apply, and a receipt for the old document's request changes nothing."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        self.reload_peer(page, frame)
        self.assertIn('dropped: the page reloaded or reconnected before it was acknowledged', self.preview(page)['status'])
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.send(frame, self.receipt(request))
        self.quiet(page)
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.assertEqual(errors, [])

    def export_json(self, page):
        page.locator('#exportJson').click()
        document = json.loads(page.locator('#exportDialogText').input_value())
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return document

    @per_engine
    def test_an_import_leaves_a_queued_role_op_queued_and_does_not_count_it_as_a_dropped_edit(self, engine):
        """Given Apply queued behind a legacy op, when a document with live overrides is imported, then the import
        status does not count the Apply as a dropped edit and the Apply is still sent once the legacy op settles."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.select_for_apply(page)
        reset = self.legacy_in_flight(page, frame)
        self.button(page, APPLY).click()
        self.quiet(page)
        document = self.export_json(page)
        document['live'] = {'target': PEER_URL, 'revision': 0, 'overrides': {}}
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json', 'buffer': json.dumps(document).encode()})
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        status = page.locator('#composerStatus').inner_text()
        self.assertIn('imported', status.lower())
        self.assertNotIn('dropped', status)
        self.send(frame, self.applied(reset))
        self.wait_for_ops(frame, 'design:roles-apply', 1)
        self.assertEqual(errors, [])


class StudioResetAllTests(StudioLegacyCase):
    def accept_reset_all(self, page, frame):
        messages = []
        count = len(self.ops(frame, 'design:reset'))
        page.once('dialog', lambda dialog: (messages.append(dialog.message), dialog.accept()))
        self.button(page, RESET_ALL).click()
        self.wait_for_ops(frame, 'design:reset', count + 1)
        return messages[0], self.ops(frame, 'design:reset')[-1]

    def empty_state(self, **changes):
        return {'documentId': 'peer-document', 'pageVersion': 0, 'pageURL': PEER_URL, 'roles': [], 'canonicalCss': '',
                'hashAlgorithm': 'fnv1a32', 'cssHash': EMPTY_HASH, **changes}

    @per_engine
    def test_reset_all_is_enabled_inside_the_panel_asks_first_and_dismissing_sends_nothing(self, engine):
        """Given a ready session with no edits, when Reset all page edits is pressed and the confirmation is
        dismissed, then nothing is sent; the control sits inside the detected-roles panel and was enabled without
        any legacy change."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.assertEqual(page.locator('#detectedRoles #roleResetAll').count(), 1)
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        self.assertTrue(self.button(page, RESET_ALL).is_enabled())
        messages = []
        page.once('dialog', lambda dialog: (messages.append(dialog.message), dialog.dismiss()))
        self.button(page, RESET_ALL).click()
        self.quiet(page)
        self.assertEqual(len(messages), 1)
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.assertEqual(errors, [])

    @per_engine
    def test_reset_all_confirmation_wording_follows_the_sync_state(self, engine):
        """Given Sync off and then Auto-sync on, when the confirmation opens, then it says every live edit is
        removed (inspector edits, text, moves, tokens and the role preview) and either that the next Sync writes the
        emptied state or that the synced overrides file will be rewritten without them."""
        removed = 'removes every live edit on the page: inspector edits, text, moves, tokens and the role preview'
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        messages = []
        page.once('dialog', lambda dialog: (messages.append(dialog.message), dialog.dismiss()))
        self.button(page, RESET_ALL).click()
        self.assertIn(removed, messages[0])
        self.assertIn('the next Sync writes the emptied state', messages[0])
        self.assertNotIn('rewritten', messages[0])
        page, frame, errors = self.open(engine, PEER_URL, PEER, sync=True)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        page.locator('#liveCodeAutoSync').check()
        page.once('dialog', lambda dialog: (messages.append(dialog.message), dialog.dismiss()))
        self.button(page, RESET_ALL).click()
        self.assertIn(removed, messages[1])
        self.assertIn('the synced overrides file will be rewritten without them', messages[1])
        self.assertNotIn('next Sync', messages[1])
        self.assertEqual(errors, [])

    @per_engine
    def test_accepted_reset_all_sends_one_untargeted_reset_and_a_valid_empty_role_state_clears_the_preview(self, engine):
        """Given an accepted preview, when Reset all page edits is accepted, then exactly one untargeted
        design:reset is sent, the preview stays until the reply's empty roleState arrives, then it clears, the
        removed role is named and the next Apply is based on the reply's revision."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        receipt = self.receipt(request)
        self.send(frame, receipt)
        self.wait_status(page, 'Preview applied to 1 role')
        message, reset = self.accept_reset_all(page, frame)
        self.assertEqual(set(reset), {'type', 'protocolVersion', 'sessionId', 'requestId', 'baseRevision'})
        self.assertEqual(len(self.ops(frame, 'design:reset')), 1)
        self.assertEqual(self.preview(page)['css'], receipt['canonicalCss'])
        self.send(frame, self.applied(reset, roleState=self.empty_state()))
        self.wait_status(page, 'Role preview cleared by Reset all page edits.')
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['outcomes'], shown['removed']), ('', '', 'Removed from the preview: Body.'))
        self.assertEqual(self.apply_role(page, frame, '25')['baseRevision'], reset['baseRevision'] + 1)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_reset_all_reply_with_an_unsupported_url_still_clears_the_preview(self, engine):
        """Given an accepted preview, when the reset-all reply's empty roleState has a null URL (Addendum 5), then
        the preview clears and Detect and Apply become unavailable."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        self.send(frame, self.receipt(request))
        self.wait_status(page, 'Preview applied to 1 role')
        reset = self.accept_reset_all(page, frame)[1]
        self.send(frame, self.applied(reset, roleState=self.empty_state(pageVersion=1, pageURL=None)))
        self.wait_status(page, 'Role preview cleared by Reset all page edits.')
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_reset_all_reply_without_a_valid_empty_role_state_keeps_the_preview_unconfirmed(self, engine):
        """Given an accepted preview, when the reset-all reply carries no roleState or an invalid, non-empty, foreign
        or older one, then the preview stays shown and is marked unconfirmed, and a later receipt confirms it."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        request = self.apply_role(page, frame, '24')
        self.send(frame, self.receipt(request))
        self.wait_status(page, 'Preview applied to 1 role')
        replies = {'no roleState': {}, 'extra key': {'roleState': self.empty_state(extra=1)},
                   'roles not empty': {'roleState': self.snapshot_state([self.role_input()])},
                   'other document': {'roleState': self.empty_state(documentId='other')},
                   'wrong digest': {'roleState': self.empty_state(cssHash='00000000')},
                   'foreign url': {'roleState': self.empty_state(pageURL='http://evil.test/x')},
                   'older revision': {'roleState': self.empty_state(), 'revision': 0}}
        for name, change in replies.items():
            with self.subTest(reply=name):
                css = self.preview(page)['css']
                reset = self.accept_reset_all(page, frame)[1]
                self.send(frame, self.applied(reset, **change))
                page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.startsWith("Unconfirmed")')
                self.assertIn('could not be confirmed', self.preview(page)['status'])
                self.assertEqual(self.preview(page)['css'], css)
                if name == 'older revision':
                    continue   # the bridge's revision went backwards here: nothing realistic follows
                request = self.press_apply(page, frame)
                self.send(frame, self.receipt(request))
                page.wait_for_function('!document.querySelector("#rolePreviewStatus").textContent.startsWith("Unconfirmed")')
        self.assertEqual(errors, [])


class StudioPrbFixTests(StudioLegacyCase):
    @per_engine
    def test_another_apps_preview_is_cleared_when_a_bridge_that_cannot_report_one_connects(self, engine):
        """Given an applied preview on one origin, when Studio connects to another origin whose bridge reports no role
        support, then the first app's CSS and counts are gone and the status says no preview is shown."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.send(frame, self.receipt(self.apply_role(page, frame, '24')))
        self.wait_status(page, 'Preview applied to 1 role')
        self.switch_to(page, 'http://evil.test/peer', PEER_LEGACY, UNSUPPORTED)
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['outcomes']), ('', ''))
        self.assertEqual(shown['status'], 'This bridge does not report a role preview, so none is shown.')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_role_op_that_never_left_the_queue_is_reported_dropped_when_the_session_ends(self, engine):
        """Given Apply queued behind an unanswered legacy op, when Studio connects to another origin, then the status
        says the request was dropped instead of still reading 'Applying role preview'."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.control(page, 'Preview this role').check()
        self.type_value(self.control(page, 'Size (px)'), '24')
        self.legacy_in_flight(page, frame)
        self.button(page, APPLY).click()
        self.assertEqual(self.preview(page)['status'], 'Applying role preview…')
        self.switch_to(page, 'http://evil.test/peer', PEER)
        status = self.preview(page)['status']
        self.assertIn('dropped', status)
        self.assertNotIn('Applying', status)
        self.assertEqual(errors, [])

    @per_engine
    def test_typing_does_not_rebuild_the_outcome_list(self, engine):
        """Given a shown preview with outcomes, when a key is typed in a draft field, then the outcome nodes are the
        same nodes afterwards, and the draft and Apply state still follow the key."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.send(frame, self.receipt(self.apply_role(page, frame, '24')))
        self.wait_status(page, 'Preview applied to 1 role')
        page.evaluate('document.querySelector("#rolePreviewOutcomes li").dataset.kept = "1"')
        self.type_value(self.control(page, 'Weight'), '7')
        self.assertEqual(page.locator('#rolePreviewOutcomes li').first.get_attribute('data-kept'), '1')
        self.assertEqual(self.control(page, 'Weight').input_value(), '7')
        self.assertTrue(self.gate(page)[0])
        self.type_value(self.control(page, 'Weight'), '0')
        self.assertFalse(self.gate(page)[0])
        self.assertEqual(errors, [])


class StudioRoleStateTests(StudioRoleCase):
    @per_engine
    def test_ready_with_accepted_roles_shows_them_seeds_drafts_and_is_never_sent_back(self, engine):
        """Given a same-document ready that carries two accepted roles, when Detect later shows one of them, then the
        preview shows the page's CSS as reported, that row's draft is already selected with the accepted values, the
        snapshot was never sent back, and Apply replaces the set and names the role it removes."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        gone = {**self.role_input('role-9', 'Gone'), 'adapter': 'bootstrap5-body', 'properties': {'fontFamily': 'Georgia, serif'}}
        state = self.snapshot_state([self.role_input('role-1', 'Body', fontSize=24, fontWeight=700), gone])
        self.ready_with(page, frame, state, revision=3)
        shown = self.preview(page)
        self.assertEqual(shown['css'], state['canonicalCss'])
        self.assertEqual(shown['status'], 'The page reports an accepted role preview; its checks were not repeated.')
        self.assertEqual(shown['outcomes'], '')
        self.detected(page, frame)
        self.assertTrue(self.control(page, 'Preview this role').is_checked())
        self.assertEqual((self.control(page, 'Size (px)').input_value(), self.control(page, 'Weight').input_value()), ('24', '700'))
        self.assertEqual(self.ops(frame, 'design:roles-apply'), [])
        self.assertTrue(self.gate(page)[0])
        request = self.press_apply(page, frame)
        self.assertEqual(request['baseRevision'], 3)
        self.assertEqual([role['id'] for role in request['roles']], ['role-1'])
        self.send(frame, self.receipt(request))
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(self.preview(page)['removed'], 'Removed from the preview: Gone.')
        self.assertEqual(errors, [])

    @per_engine
    def test_an_older_ready_cannot_replace_a_newer_accepted_preview_but_a_new_document_does(self, engine):
        """Given an accepted snapshot at revision 5, when an older-revision snapshot of the same document arrives it
        changes nothing, a newer one replaces it, and a snapshot for a new document replaces it whatever its
        revision."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        newer = self.snapshot_state([self.role_input(fontSize=24)])
        older = self.snapshot_state([self.role_input(fontSize=30)])
        self.ready_with(page, frame, newer, revision=5)
        self.ready_with(page, frame, older, revision=4)
        self.assertEqual(self.preview(page)['css'], newer['canonicalCss'])
        self.ready_with(page, frame, older, revision=6)
        self.assertEqual(self.preview(page)['css'], older['canonicalCss'])
        self.ready_with(page, frame, self.snapshot_state([], documentId='peer-document-2'), revision=0)
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['status']), ('', 'No role preview applied.'))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_stale_ready_of_the_same_document_never_lowers_the_revision_the_next_apply_carries(self, engine):
        """Given an accepted preview at revision 5, when a ready of the same document arrives with revision 4, then the
        preview is unchanged and the next Apply carries baseRevision 5, not 4."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        newer = self.snapshot_state([self.role_input(fontSize=24)])
        older = self.snapshot_state([self.role_input(fontSize=30)])
        self.ready_with(page, frame, newer, revision=5)
        self.ready_with(page, frame, older, revision=4)
        self.assertEqual(self.preview(page)['css'], newer['canonicalCss'])
        self.detected(page, frame)
        self.assertEqual(self.press_apply(page, frame)['baseRevision'], 5)
        self.assertEqual(self.preview(page)['css'], newer['canonicalCss'])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_ready_for_a_new_document_adopts_its_lower_revision(self, engine):
        """Given an accepted preview at revision 5, when a ready of a new document arrives with revision 1, then the
        next Apply carries baseRevision 1: a reload restarts the bridge's counter."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.ready_with(page, frame, self.snapshot_state([self.role_input(fontSize=24)]), revision=5)
        self.ready_with(page, frame, self.snapshot_state([], documentId='peer-document-2'), revision=1)
        self.detected(page, frame)
        self.assertEqual(self.apply_role(page, frame, '24')['baseRevision'], 1)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_ready_whose_css_is_not_its_roles_serialization_is_not_shown_even_with_a_matching_digest(self, engine):
        """Given valid roles reported with unrelated CSS and that CSS's own digest, when the ready arrives first on an
        empty preview and again over an accepted one, then nothing is shown as acknowledged: the empty preview stays
        empty, the accepted CSS stays, marked unconfirmed, and Detect and Apply are off."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        state = self.snapshot_state([self.role_input(fontSize=24)])
        hostile = self.with_css(state, 'p { color: red; }\n')
        before = self.preview(page)
        self.ready_with(page, frame, hostile, revision=1)
        self.assertEqual(self.preview(page), before)
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.ready_with(page, frame, state, revision=2)
        self.assertEqual(self.preview(page)['css'], state['canonicalCss'])
        self.ready_with(page, frame, hostile, revision=3)
        shown = self.preview(page)
        self.assertEqual(shown['css'], state['canonicalCss'])
        self.assertTrue(shown['status'].startswith('Unconfirmed'))
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNSUPPORTED))
        self.assertNotIn('color: red', page.locator('#rolePreviewCss').text_content())
        self.assertEqual(errors, [])

    @per_engine
    def test_an_invalid_ready_marks_the_shown_preview_unconfirmed_and_a_valid_one_confirms_it(self, engine):
        """Given an accepted snapshot, when a ready arrives with a wrong digest, then the preview stays but is marked
        unconfirmed, Detect and Apply are disabled with the unsupported reason; a valid ready confirms it."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        state = self.snapshot_state([self.role_input()])
        self.ready_with(page, frame, state, revision=1)
        self.ready_with(page, frame, {**state, 'cssHash': '00000000'}, revision=2)
        shown = self.preview(page)
        self.assertEqual(shown['css'], state['canonicalCss'])
        self.assertTrue(shown['status'].startswith('Unconfirmed'))
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNSUPPORTED))
        self.ready_with(page, frame, state, revision=3)
        self.assertFalse(self.preview(page)['status'].startswith('Unconfirmed'))
        self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
        self.assertEqual(errors, [])

    @per_engine
    def test_a_reload_replaces_the_shown_preview_with_the_new_documents_state(self, engine):
        """Given an accepted preview, when the page reloads, then the new document's ready replaces the shown
        preview with its own empty state and nothing is replayed."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        self.send(frame, self.receipt(self.apply_role(page, frame, '24')))
        self.wait_status(page, 'Preview applied to 1 role')
        frame.evaluate('setTimeout(() => location.reload(), 0)')
        page.wait_for_function('document.querySelector("#roleStatus").textContent === "Ready to detect text styles."')
        shown = self.preview(page)
        self.assertEqual((shown['css'], shown['status']), ('', 'No role preview applied.'))
        self.assertEqual(shown['removed'], '', 'the new document dropped it; Studio removed nothing')
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.assertEqual(errors, [])

    @per_engine
    def test_the_page_notice_message_changes_nothing(self, engine):
        """Given a detected page, when a design:roles-page notice arrives (PR C), then Studio's identity, rows and
        statuses are unchanged: the next Apply still carries the old page version."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame)
        status = page.locator('#roleStatus').inner_text()
        self.send(frame, {'type': 'design:roles-page', 'documentId': 'peer-document', 'pageVersion': 5, 'pageURL': None})
        self.settle(page, frame)
        self.assertEqual(page.locator('#roleStatus').inner_text(), status)
        self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
        self.assertEqual(self.apply_role(page, frame, '24')['pageVersion'], 0)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_bridge_with_detection_only_keeps_detect_and_explains_why_apply_and_clear_are_off(self, engine):
        """Given a bridge that advertises roleDetection but not roleStylesheet, when Studio connects, then Detect
        works while Apply and Clear are disabled with the visible reason that the bridge does not support role
        preview, and no preview message is ever sent."""
        page, frame, errors = self.open(engine, PEER_URL, PEER_DETECT_ONLY)
        self.assertEqual(self.gate(page), (False, NO_PREVIEW))
        self.assertTrue(self.button(page, CLEAR).is_disabled())
        self.assertEqual(self.hint(page, 'roleClearHint'), NO_PREVIEW)
        self.detected(page, frame)
        self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
        self.control(page, 'Preview this role').check()
        self.type_value(self.control(page, 'Size (px)'), '24')
        self.assertEqual(self.gate(page), (False, NO_PREVIEW))
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect'])
        self.assertEqual(errors, [])

    @per_engine
    def test_the_collection_limit_disables_apply_with_a_visible_reason_for_the_life_of_the_ids(self, engine):
        """Given 128 issued role ids and a further role refused, when the page is re-detected after a ready, then
        Apply stays disabled with a hint that says the limit is reached."""
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame, [group(f'g-{i}', f'Role {i}', f'Author {i}') for i in range(128)])
        frame.evaluate('ready()')
        page.wait_for_function('document.querySelector("#roleRows").children.length===0')
        request = self.pending(page, frame)
        self.send(frame, self.reply(request, [group('new', 'New role', 'New author')]))
        page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Collection limit")')
        frame.evaluate('ready()')
        page.wait_for_function('document.querySelector("#roleRows").children.length===0')
        self.detected(page, frame, [group('again', 'Existing', 'Author 0')])
        self.select_first(page)
        enabled, reason = self.gate(page)
        self.assertFalse(enabled)
        self.assertIn('limit', reason)
        self.assertEqual(self.ops(frame, 'design:roles-apply'), [])
        self.assertEqual(errors, [])

    def select_first(self, page):
        self.control(page, 'Preview this role', 'role-1', 'Existing').check()
        self.type_value(self.control(page, 'Size (px)', 'role-1', 'Existing'), '24')

    @per_engine
    def test_literal_markup_in_names_and_details_renders_only_as_text(self, engine):
        """Given a role named with markup and a rejection detail with a tag (the canonical CSS cannot carry markup: the
        roles' selectors and families refuse it), when they render, then they are literal text: no image element, no
        script side effect."""
        literal = '<img src="https://isolation.invalid/x" onerror="document.body.dataset.bad=1">'
        page, frame, errors = self.open(engine, PEER_URL, PEER)
        self.detected(page, frame, [group(name=literal)])
        request = self.apply_role(page, frame, '24', name=literal)
        receipt = self.receipt(request)
        self.send(frame, receipt)
        self.wait_status(page, 'Preview applied to 1 role')
        shown = self.preview(page)
        self.assertEqual(shown['css'], receipt['canonicalCss'])
        self.assertIn(literal, shown['outcomes'])
        request = self.apply_role(page, frame, '25', name=literal)
        self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': 1,
                          'reason': 'unsupported-value', 'detail': literal})
        self.wait_status(page, 'rejected (unsupported-value)')
        self.assertIn(literal, self.preview(page)['status'])
        self.assertEqual(page.locator('#detectedRoles img').count(), 0)
        self.assertEqual(page.locator('#detectedRoles pre').count(), 1)
        self.assertIsNone(page.locator('body').get_attribute('data-bad'))
        self.assertEqual(errors, [])

    def contrast(self, page, selector):
        colors = page.locator(selector).evaluate('''el => { let c = getComputedStyle(el), p = el;
            while (p && getComputedStyle(p).backgroundColor === "rgba(0, 0, 0, 0)") p = p.parentElement;
            return [c.color, getComputedStyle(p).backgroundColor]; }''')
        def luminance(color):
            parts = [float(x) / 255 for x in color[color.index('(') + 1:color.index(')')].split(',')[:3]]
            values = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in parts]
            return sum(c * w for c, w in zip(values, (.2126, .7152, .0722)))
        light, dark = sorted(map(luminance, colors), reverse=True)
        return (light + .05) / (dark + .05)

    @per_engine
    def test_preview_names_focus_contrast_and_width_hold_on_desktop_and_a_narrow_panel(self, engine):
        """Given a populated preview with an unbroken 250-character family, when rendered at 1440 and 390 px, then
        the heading and both status regions have their accessible names, the CSS block is focusable and scrolls
        inside itself, controls take a visible focus ring, the disabled reason is readable and described by
        Apply, and nothing overflows the panel or page."""
        family = 'F' * 250
        for width in (1440, 390):
            with self.subTest(width=width):
                page, frame, errors = self.open(engine, PEER_URL, PEER, viewport={'width': width, 'height': 1000})
                self.detected(page, frame)
                self.control(page, 'Preview this role').check()
                self.type_value(self.control(page, 'Font family'), family)
                self.type_value(self.control(page, 'Size (px)'), '24')
                request = self.press_apply(page, frame)
                self.send(frame, self.receipt(request))
                self.wait_status(page, 'Preview applied to 1 role')
                self.assertEqual(page.get_by_role('heading', name='Role preview; file output comes later').count(), 1)
                detect_status = page.get_by_role('status', name='Role detection status')
                preview_status = page.get_by_role('status', name='Role preview status')
                self.assertEqual((detect_status.count(), preview_status.count()), (1, 1))
                self.assertNotEqual(detect_status.get_attribute('id'), preview_status.get_attribute('id'))
                block = page.locator('#rolePreviewCss')
                block.focus()
                self.assertTrue(block.evaluate('el => el === document.activeElement'))
                self.assertEqual(block.evaluate('el => getComputedStyle(el).overflowX'), 'auto')
                self.assertTrue(block.evaluate('el => el.scrollWidth > el.clientWidth'))
                for name in (APPLY, CLEAR, RESET_ALL):
                    button = self.button(page, name)
                    button.focus()
                    self.assertGreater(float(button.evaluate('el => parseFloat(getComputedStyle(el).outlineWidth)')), 0)
                self.assertTrue(page.locator('#detectedRoles').evaluate('el => el.scrollWidth <= el.clientWidth'))
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                self.control(page, 'Preview this role').uncheck()
                enabled, reason = self.gate(page)
                self.assertFalse(enabled)
                self.assertEqual(self.button(page, APPLY).get_attribute('aria-describedby'), 'roleApplyHint')
                for selector in ('#roleApplyHint', '#rolePreviewStatus', '#roleStatus'):
                    self.assertGreaterEqual(self.contrast(page, selector), 4.5, selector)
                self.assertEqual(errors, [])


HERO_LEAD = [{'value': '[data-design-id="hero.lead"]', 'stable': True, 'reason': 'author-id'}]


class StudioRoleLegacyInterplayTests(StudioLegacyCase):
    """Role ops beside real inspector edits, on the legacy fake target (which answers the legacy ops)."""
    page_url = HYBRID_URL

    def badge(self, page, pattern):
        page.wait_for_function('(p) => new RegExp(p).test(document.querySelector("#bridgeStatusBadge").textContent)', arg=pattern)

    def select(self, page, frame, target_id='hero.lead'):
        frame.evaluate('(id) => fake.select(id)', target_id)
        page.wait_for_function('(id) => document.querySelector("#liveTargetName")?.dataset.targetId === id', arg=target_id)

    def edit(self, page, field, value):
        self.type_value(page.locator(f'#{field}'), value)

    def hybrid_ready(self, engine, sync=False, groups=None):
        page, frame, errors = self.open_hybrid(engine, sync=sync)
        self.detected(page, frame, groups or [group(selectors=HERO_LEAD)])
        return page, frame, errors

    def bridge_ops(self, frame):
        kinds = ('design:update', 'design:roles-apply', 'design:roles-clear', 'design:reset')
        return [(m['type'], m.get('patch'), m.get('baseRevision')) for m in frame.evaluate('received') if m['type'] in kinds]

    def settle_role(self, page, frame, request):
        """Answers a role request the way a bridge sharing this fake's revision counter would."""
        receipt = self.receipt(request)
        self.assertEqual(frame.evaluate('fake.bumpRevision()'), receipt['revision'])
        self.send(frame, receipt)
        return receipt

    @per_engine
    def test_role_ops_are_barriers_for_update_coalescing_and_later_edits_use_the_receipts_revision(self, engine):
        """Given an inspector edit in flight, another queued, Apply queued and a third edit made after it, when the
        replies are released, then the target sees the edits and the Apply in click order (the third edit is not
        merged across the Apply) and the last edit is based on the receipt's revision."""
        page, frame, errors = self.hybrid_ready(engine)
        self.select_for_apply(page)
        self.select(page, frame)
        frame.evaluate('fake.hold = true')
        self.edit(page, 'liveFontSize', '9')
        self.wait_for_ops(frame, 'design:update', 1)
        self.edit(page, 'liveFontWeight', '7')
        self.button(page, APPLY).click()
        self.edit(page, 'liveLetterSpacing', '1')
        frame.evaluate('fake.hold = false; fake.release()')
        self.wait_for_ops(frame, 'design:roles-apply', 1)
        self.assertEqual([(kind, patch) for kind, patch, _ in self.bridge_ops(frame)], [
            ('design:update', {'fontSize': 9}), ('design:update', {'fontWeight': 7}), ('design:roles-apply', None)])
        request = self.ops(frame, 'design:roles-apply')[0]
        receipt = self.settle_role(page, frame, request)
        self.wait_for_ops(frame, 'design:update', 3)
        last = self.bridge_ops(frame)[-1]
        self.assertEqual(last[:2], ('design:update', {'letterSpacing': 1}))
        self.assertEqual(last[2], receipt['revision'])
        self.badge(page, rf'^Live · rev {receipt["revision"] + 1}$')
        self.assertEqual(errors, [])

    @per_engine
    def test_an_inspector_edit_survives_apply_and_target_only_reset_keeps_the_preview(self, engine):
        """Given a saved inspector edit, when a role is applied, then the saved overrides and the change count stay;
        a target-only reset then removes only that edit and the role preview, its status and CSS stay as they were."""
        page, frame, errors = self.hybrid_ready(engine)
        self.select(page, frame)
        self.edit(page, 'liveFontSize', '9')
        self.badge(page, r'^Live · rev 1$')
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '1')
        request = self.apply_role(page, frame, '24')
        receipt = self.settle_role(page, frame, request)
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '1')
        self.assertEqual(frame.evaluate('fake.styleOf("hero.lead").fontSize'), '9px')
        shown = self.preview(page)
        page.get_by_role('button', name='Reset this element', exact=True).click()
        self.badge(page, rf'^Live · rev {receipt["revision"] + 1}$')
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        self.assertEqual(self.preview(page), shown)
        self.assertEqual(errors, [])

    @per_engine
    def test_code_download_export_and_the_synced_file_are_byte_identical_before_and_after_apply(self, engine):
        """Given a saved inspector edit, when a role is applied and acknowledged, then the CSS, HTML and JSON tabs,
        the bytes each tab downloads, the JSON export and the body Sync to file writes are byte-identical to before, and
        none of them contains the role CSS."""
        page, frame, errors = self.hybrid_ready(engine, sync=True)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        self.select(page, frame)
        self.edit(page, 'liveFontSize', '9')
        self.badge(page, r'^Live · rev 1$')
        before = self.exports(page)
        before_sync = self.sync_body(page)
        request = self.apply_role(page, frame, '24')
        receipt = self.settle_role(page, frame, request)
        self.wait_status(page, 'Preview applied to 1 role')
        after = self.exports(page)
        after_sync = self.sync_body(page)
        # The Json tab also shows the page's acknowledged revision, which a role op legitimately raises by one; it is
        # not saved state. Compared with that one number aligned, everything else must be byte-identical.
        revision = lambda text: re.sub(r'"revision": \d+', '"revision": N', text)
        self.assertEqual(json.loads(after['Json'])['revision'], json.loads(before['Json'])['revision'] + 1)
        aligned = lambda found: {**found, 'Json': revision(found['Json']), 'downloadJson': revision(found['downloadJson'])}
        self.assertEqual(aligned(after), aligned(before))
        self.assertEqual(after_sync, before_sync)
        self.assertIn('font-size: 9px', before_sync)
        for text in (*after.values(), after_sync):
            self.assertNotIn('font-size: 24px', text)
            self.assertNotIn(receipt['cssHash'], text)
        self.assertEqual(errors, [])

    @per_engine
    def test_an_edit_acknowledged_while_a_role_op_waits_still_auto_syncs_once_the_role_op_settles(self, engine):
        """Given Auto-sync on, an edit in flight and Apply queued behind it, when the edit is acknowledged, then the
        file is not written yet (a request is queued), and when the Apply's receipt arrives the skipped auto-sync
        runs and writes the edit."""
        page, frame, errors = self.hybrid_ready(engine, sync=True)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        page.locator('#liveCodeAutoSync').check()
        self.quiet(page)
        self.select_for_apply(page)
        self.select(page, frame)
        frame.evaluate('fake.hold = true')
        self.edit(page, 'liveFontSize', '9')
        self.wait_for_ops(frame, 'design:update', 1)
        self.button(page, APPLY).click()
        frame.evaluate('fake.hold = false; fake.release()')
        self.wait_for_ops(frame, 'design:roles-apply', 1)
        self.quiet(page)
        self.quiet(page)
        self.assertEqual(self.puts, [])
        request = self.ops(frame, 'design:roles-apply')[0]
        with page.expect_response(lambda response: response.request.method == 'PUT'):
            self.settle_role(page, frame, request)
        self.assertIn('font-size: 9px', self.puts[-1])
        self.assertNotIn('Hostile', self.puts[-1])
        self.assertEqual(errors, [])

    def quiet(self, page):
        page.wait_for_timeout(450)

    @per_engine
    def test_targeted_reset_rewrites_the_synced_file_only_through_the_user_chosen_sync(self, engine):
        """Characterization of the per-element reset that Reset all page edits mirrors: with Auto-sync off a
        targeted reset writes nothing, and the next Sync writes the state without the reset element's edit."""
        page, frame, errors = self.hybrid_ready(engine, sync=True)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        self.select(page, frame)
        self.edit(page, 'liveFontSize', '9')
        self.badge(page, r'^Live · rev 1$')
        with page.expect_response(lambda response: response.request.method == 'PUT'):
            page.locator('#liveCodeSync').click()
        self.assertIn('font-size: 9px', self.puts[-1])
        page.get_by_role('button', name='Reset this element', exact=True).click()
        self.badge(page, r'^Live · rev 2$')
        self.quiet(page)
        self.assertEqual(len(self.puts), 1)
        with page.expect_response(lambda response: response.request.method == 'PUT'):
            page.locator('#liveCodeSync').click()
        self.assertNotIn('font-size', self.puts[-1])
        self.assertEqual(errors, [])

    @per_engine
    def test_reset_all_empties_overrides_tokens_and_saved_order_without_a_conflict_banner(self, engine):
        """Given a saved size override, a saved DOM move and a CSS order, when Reset all page edits is accepted and
        acknowledged, then the change count, the exported live state and the code tabs are empty and no reconnect or
        structure conflict banner appears; a role preview with no roleState in the reply stays, unconfirmed."""
        page, frame, errors = self.open(engine, HYBRID_URL + '?arrange', hybrid_page())
        self.detected(page, frame, [group(selectors=HERO_LEAD)])
        self.select_for_apply(page)
        self.select(page, frame, 'card.c')
        self.edit(page, 'liveFontSize', '21')
        self.badge(page, r'^Live · rev 1$')
        page.locator('#liveMoveLast').click()
        self.badge(page, r'^Live · rev 2$')
        page.locator('#liveMoveStrategyCss').click()
        page.locator('#liveMoveFirst').click()
        self.badge(page, r'^Live · rev 3$')
        request = self.press_apply(page, frame)
        receipt = self.settle_role(page, frame, request)
        self.wait_status(page, 'Preview applied to 1 role')
        live = self.export_state(page)
        self.assertTrue(live['overrides'] and live['structure'], live)
        page.once('dialog', lambda dialog: dialog.accept())
        self.button(page, RESET_ALL).click()
        self.badge(page, rf'^Live · rev {receipt["revision"] + 1}$')
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        live = self.export_state(page)
        self.assertEqual((live.get('overrides', {}), live.get('structure', [])), ({}, []))
        self.assertTrue(page.locator('#liveReconnectBanner').is_hidden())
        self.assertEqual(frame.evaluate('fake.textOf("hero.lead")'), 'Lead copy for the page.')
        shown = self.preview(page)
        self.assertEqual(shown['css'], receipt['canonicalCss'])
        self.assertTrue(shown['status'].startswith('Unconfirmed'))
        self.assertEqual(errors, [])

    def flow(self, frame):
        out = []
        for message in frame.evaluate('received'):
            if message['type'] == 'design:update':
                out.append('update' if 'targetId' in message else 'composition')
            elif message['type'] == 'design:reset':
                out.append('reset')
        return out

    @per_engine
    def test_a_composition_edit_is_not_merged_into_one_queued_before_a_reset_all(self, engine):
        """Given a linked composition, an inspector edit in flight, a composition edit queued and Reset all page edits
        queued behind it, when the composition changes again, then the new composition is queued after the reset and
        is sent after it, so the page ends with the composition rather than empty."""
        page, frame, errors = self.hybrid_ready(engine)
        page.on('dialog', lambda dialog: dialog.accept())
        page.locator('#btnSyncToApp').click()
        self.wait_flow(frame, ['composition'])
        self.select(page, frame)
        frame.evaluate('fake.hold = true')
        self.edit(page, 'liveFontSize', '9')
        self.wait_flow(frame, ['composition', 'update'])
        page.locator('#compositionPreset').select_option('asteria')
        page.locator('#applyPreset').click()
        self.button(page, RESET_ALL).click()
        page.locator('#compositionPreset').select_option('blank')
        page.locator('#applyPreset').click()
        frame.evaluate('fake.hold = false; fake.release()')
        self.wait_flow(frame, ['composition', 'update', 'composition', 'reset', 'composition'])
        self.assertTrue(frame.evaluate('Object.keys(fake.ledger().tokens).length > 0'))
        self.assertEqual(errors, [])

    def wait_flow(self, frame, expected):
        frame.wait_for_function('(expected) => JSON.stringify(received.filter(m => m.type === "design:update" || m.type === "design:reset").map(m => m.type === "design:reset" ? "reset" : ("targetId" in m ? "update" : "composition"))) === JSON.stringify(expected)',
                                arg=expected, polling=50)

    def export_state(self, page):
        page.locator('#exportJson').click()
        document = json.loads(page.locator('#exportDialogText').input_value())
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return document.get('live', {})
