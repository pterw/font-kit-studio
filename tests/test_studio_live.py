"""Studio-side live preview protocol tests (v0.2.0 Task C).

Studio is served at http://studio.test and a deterministic fake bridge target
(tests/fixtures/studio/fake-target.html) at http://target.test, so every
postMessage crosses a real origin boundary. The real fontkit-bridge.js is not
used here; the fake implements the plan's protocol contract.
"""

import json
import re
import time
import unittest
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from support import ENGINES, HTML, REPO, launch, route_virtual_origins

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'studio'
STUDIO = 'http://studio.test'
TARGET = 'http://target.test'
EVIL = 'http://evil.test'
HOST = 'http://host.test'
APP = f'{STUDIO}/{HTML.name}'
FAKE = f'{TARGET}/fake-target.html'


class LiveCase(unittest.TestCase):
    def setUp(self):
        self.runtime = sync_playwright().start()
        self.browsers = []

    def tearDown(self):
        for browser in self.browsers:
            browser.close()
        self.runtime.stop()

    # ---- harness -------------------------------------------------------
    def context(self, engine, sync=None, viewport=None, status_target='http://localhost:8001/demo/'):
        browser = launch(self.runtime, engine)
        self.browsers.append(browser)
        context = browser.new_context(viewport=viewport or {'width': 1600, 'height': 1200})
        context.route('https://**/*', lambda route: route.abort())
        route_virtual_origins(context, {STUDIO: REPO, TARGET: FIXTURES, EVIL: FIXTURES, HOST: FIXTURES})
        self.puts = []
        if sync is not None:
            def handler(route):
                request = route.request
                if request.url.endswith('/__fontkit/status') and request.method == 'GET':
                    route.fulfill(status=200, content_type='application/json',
                                  body=json.dumps({'sync': sync, 'overrides': 'demo/fontkit-overrides.css',
                                                   'target': status_target}))
                elif request.url.endswith('/__fontkit/overrides.css') and request.method == 'PUT':
                    body = request.post_data or ''
                    self.puts.append({'body': body, 'type': request.headers.get('content-type')})
                    route.fulfill(status=200, content_type='application/json',
                                  body=json.dumps({'ok': True, 'bytes': len(body.encode()), 'path': 'demo/fontkit-overrides.css'}))
                else:
                    route.fulfill(status=404, body='not found')
            # Registered after the file routes: Playwright runs the latest matching route first.
            context.route(f'{STUDIO}/__fontkit/**', handler)
        return context

    def open(self, engine, target=FAKE, sync=None, viewport=None, query=True,
             status_target='http://localhost:8001/demo/'):
        context = self.context(engine, sync=sync, viewport=viewport, status_target=status_target)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        url = f'{APP}?target={quote(target, safe="")}' if (query and target) else APP
        page.goto(url)
        return page, errors

    def connect(self, page, url=FAKE):
        page.locator('#modeComposer').click()
        page.locator('#targetAppUrl').fill(url)
        page.locator('#btnConnectTarget').click()

    def frame(self, page):
        handle = page.locator('#targetAppFrame').element_handle()
        deadline = time.time() + 5
        while time.time() < deadline:
            frame = handle.content_frame()
            if frame and frame.url.startswith(TARGET):
                try:
                    if frame.evaluate('Boolean(window.fake)'):
                        return frame
                except Exception:
                    pass
            page.wait_for_timeout(50)
        self.fail('fake target frame not available')

    def wait_badge(self, page, pattern, timeout=5000):
        page.wait_for_function('(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
                               arg=pattern, timeout=timeout)
        return page.locator('#bridgeStatusBadge').inner_text()

    def wait_connected(self, page):
        self.wait_badge(page, r'^Connected \(5 targets\)$')
        frame = self.frame(page)
        frame.wait_for_function('document.readyState === "complete"')
        page.wait_for_timeout(150)
        return self.wait_badge(page, r'^Connected \(5 targets\)$')

    def received(self, frame, kind=None):
        items = frame.evaluate('window.__received')
        return [item for item in items if kind is None or (isinstance(item['data'], dict) and item['data'].get('type') == kind)]

    def updates(self, frame):
        return [item['data'] for item in self.received(frame, 'design:update')]

    def select(self, page, frame, target_id='hero.title'):
        frame.evaluate('(id) => window.fake.select(id)', target_id)
        page.wait_for_selector('#liveTargetName')
        page.wait_for_function('(id) => document.querySelector("#liveTargetName").dataset.targetId === id', arg=target_id)

    def set_value(self, page, selector, value):
        page.locator(selector).fill(str(value))

    def wait_live(self, page):
        return self.wait_badge(page, r'^Live · rev \d+$')

    def export(self, page):
        page.locator('#exportJson').click()
        result = json.loads(page.locator('#exportDialogText').input_value())
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return result

    def import_document(self, page, data):
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json', 'buffer': json.dumps(data).encode()})
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        return page.locator('#composerStatus').inner_text()

    def session_id(self, frame):
        hellos = self.received(frame, 'design:hello')
        return hellos[-1]['data']['sessionId']

    def code(self, page, tab='Css'):
        page.locator(f'#codeTab{tab}').click()
        return page.locator('#liveCodeOutput').inner_text()

    def duplicates(self, page):
        return page.evaluate('''() => {
            const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
            return ids.filter((id, index) => ids.indexOf(id) !== index);
        }''')

    def spoofer(self, page):
        page.evaluate('''(src) => new Promise(resolve => {
            const frame = document.createElement('iframe');
            frame.id = 'spoofFrame';
            frame.style.cssText = 'position:fixed;width:1px;height:1px;left:0;top:0;opacity:0';
            frame.onload = () => resolve();
            frame.src = src;
            document.body.appendChild(frame);
        })''', f'{EVIL}/spoofer.html')
        return page.locator('#spoofFrame').element_handle().content_frame()


class StudioDefectTests(LiveCase):
    """Regression tests for Studio defects recorded in the v0.2.0 plan baseline."""

    def test_spoofed_messages_from_foreign_window_or_session_are_ignored(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)
                self.connect(page)
                frame = self.frame(page)
                page.wait_for_function('() => /Connected/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(400)
                badge = page.locator('#bridgeStatusBadge').inner_text()
                before = self.export(page)
                sid = self.session_id(frame)
                spoof = self.spoofer(page)
                forged = [
                    {'type': 'design:ready', 'protocolVersion': 1, 'sessionId': sid, 'revision': 40,
                     'targets': [{'id': f'evil.{i}'} for i in range(7)], 'changes': {'tokens': {}, 'targets': []}},
                    {'type': 'design:applied', 'protocolVersion': 1, 'sessionId': sid, 'requestId': 'req-x',
                     'revision': 99, 'targetId': 'hero.title', 'canonicalPatch': {'fontSize': 99}},
                    {'type': 'design:selected', 'protocolVersion': 1, 'sessionId': sid, 'targetId': 'hero.title',
                     'rect': {'x': 1, 'y': 1, 'width': 10, 'height': 10}},
                    {'type': 'design:select-slot', 'targetId': 'landing.hero.title', 'name': 'EVIL', 'role': 'display',
                     'currentText': 'pwned', 'computed': {'fontSize': '77px'}},
                ]
                for message in forged:
                    spoof.evaluate('(m) => window.spoof(m)', message)
                    page.evaluate('(m) => window.postMessage(m, "*")', message)
                # Right window and origin, wrong session or protocol version.
                for message in forged[:3]:
                    frame.evaluate('(m) => parent.postMessage({...m, sessionId: "fks-wrong"}, "*")', message)
                    frame.evaluate('(m) => { const c = {...m}; delete c.protocolVersion; parent.postMessage(c, "*"); }', message)
                page.wait_for_timeout(400)
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), badge)
                self.assertNotIn('7 targets', badge)
                self.assertNotIn('99', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(page.locator('#liveFontSize').count(), 0)
                self.assertEqual(page.locator('#bridgeOverlaySelected:visible').count(), 0)
                self.assertEqual(self.export(page), before)
                self.assertEqual(errors, [])

    def test_connect_does_not_broadcast_composition_or_restyle_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)
                self.connect(page)
                frame = self.frame(page)
                before = frame.evaluate('window.fake.styleOf("hero.title")')
                page.wait_for_function('() => /Connected/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                # Exercise the old auto-broadcast paths: view switches and Specimen edits.
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
                page.locator('#slotInspector [data-bind="size"]').fill('40')
                page.locator('#slotInspector [data-bind="size"]').dispatch_event('input')
                page.locator('#viewTargetApp').click()
                page.wait_for_timeout(600)
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(composition, [])
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title")'), before)
                self.assertEqual(frame.evaluate('window.fake.ledger()'), {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})
                self.assertEqual(errors, [])

    def test_send_path_has_single_anti_recursion_guard_and_never_posts_to_parent(self):
        source = HTML.read_text(encoding='utf-8')
        self.assertEqual(source.count('window.self !== window.top'), 1)
        send = re.search(r'function sendDesignMessage\(.*?\n  \}\n', source, re.S)
        self.assertIsNotNone(send)
        self.assertNotIn('window.self !== window.top', send.group(0))
        self.assertNotIn('window.parent', send.group(0))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{HOST}/host.html?studio={APP}')
                studio = None
                deadline = time.time() + 5
                while time.time() < deadline and studio is None:
                    studio = next((f for f in page.frames if f.url.startswith(APP)), None)
                    page.wait_for_timeout(50)
                self.assertIsNotNone(studio)
                studio.wait_for_selector('#composerCanvas', state='attached')
                studio.wait_for_function('() => document.readyState === "complete"')
                studio.locator('#modeComposer').click()
                # The guard still hides the recursive connector when Studio is embedded.
                self.assertFalse(studio.locator('#targetAppBridgeBar').is_visible())
                studio.locator('#btnSyncToApp').click()
                studio.locator('#applyPreset').click()
                page.wait_for_timeout(300)
                self.assertEqual(page.evaluate('window.__fromStudio'), [])
                self.assertEqual(errors, [])


class StudioProtocolTests(LiveCase):
    def test_handshake_status_badges_and_target_query(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                page = context.new_page()
                page.goto(APP)
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Idle')
                page.evaluate('''() => { window.__badges = [];
                    new MutationObserver(() => window.__badges.push(document.querySelector('#bridgeStatusBadge').textContent))
                      .observe(document.querySelector('#bridgeStatusBadge'), {childList:true, characterData:true, subtree:true}); }''')
                self.connect(page)
                self.wait_connected(page)
                badges = page.evaluate('window.__badges')
                self.assertIn('Connecting…', badges)
                self.assertIn('Bridge detected', badges)
                frame = self.frame(page)
                hellos = self.received(frame, 'design:hello')
                self.assertGreaterEqual(len(hellos), 1)
                for hello in hellos:
                    self.assertEqual(hello['origin'], STUDIO)
                    self.assertEqual(hello['data']['protocolVersion'], 1)
                    self.assertRegex(hello['data']['sessionId'], r'^fks-[0-9a-z]+$')
                # bridge-ready starts the session; the iframe load re-greets with that same session.
                self.assertEqual(len({h['data']['sessionId'] for h in hellos}), 1)
                self.assertEqual(hellos[-1]['data']['sessionId'], self.session_id(frame))

                # ?target= prefills, opens Composer -> Target App view and connects.
                page2 = context.new_page()
                errors = []
                page2.on('pageerror', lambda error: errors.append(str(error)))
                page2.goto(f'{APP}?target={FAKE}')
                self.assertTrue(page2.locator('#composerView').is_visible())
                self.assertEqual(page2.locator('#targetAppUrl').input_value(), FAKE)
                self.assertIn('active', page2.locator('#viewTargetApp').get_attribute('class'))
                self.assertTrue(page2.locator('#targetAppFrame').is_visible())
                self.wait_connected(page2)
                self.assertEqual(errors, [])

    def test_no_bridge_detected_after_timeout(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{TARGET}/no-bridge.html')
                self.wait_badge(page, '^Connecting…$')
                self.wait_badge(page, '^No bridge detected$', timeout=7000)
                hint = page.locator('#bridgeHint')
                self.assertTrue(hint.is_visible())
                self.assertIn('fontkit-bridge.js', hint.inner_text())
                self.assertEqual(errors, [])

    def test_live_inspector_seeds_from_computed_and_respects_editable(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                before = self.export(page)
                # A legacy select-slot message from the genuine target and session must not touch composer slots.
                frame.evaluate('''(sid) => parent.postMessage({type:'design:select-slot', protocolVersion:1,
                    sessionId: sid, targetId:'hero.title', name:'Hero', role:'display',
                    currentText:'pwned', computed:{fontSize:'77px'}}, '*')''', self.session_id(frame))
                self.select(page, frame, 'hero.title')
                self.assertEqual(self.export(page), before)
                self.assertEqual(page.locator('#liveTargetName').inner_text(), 'Hero title')
                self.assertEqual(page.locator('#liveFontSize').input_value(), '32')
                self.assertEqual(page.locator('#liveFontWeight').input_value(), '700')
                self.assertEqual(page.locator('#liveLineHeight').input_value(), '1.2')
                self.assertEqual(page.locator('#liveLetterSpacing').input_value(), '0.05')
                self.assertEqual(page.locator('#liveColor').input_value(), '#112233')
                self.assertEqual(page.locator('#liveColorHex').input_value(), '#112233')
                self.assertEqual(page.locator('#liveTextAlign').input_value(), 'start')
                self.assertEqual(page.locator('#liveTextTransform').input_value(), 'none')
                self.assertEqual(page.locator('#liveText').input_value(), 'Hello world')
                family = page.locator('#liveFontFamily')
                self.assertIn('Georgia', family.input_value())
                options = family.locator('option').all_inner_texts()
                self.assertIn('Fraunces', ' '.join(options))
                self.assertTrue(page.locator('#liveResetTarget').is_visible())
                # Image target: only exposed controls are shown.
                self.select(page, frame, 'brand.mark')
                self.assertEqual(page.locator('#liveFontSize').count(), 0)
                self.assertEqual(page.locator('#liveText').count(), 0)
                self.assertEqual(page.locator('#liveColor').count(), 1)
                # Constraint note for declared weights.
                self.select(page, frame, 'stat.badge')
                self.assertIn('400', page.locator('#liveWeightNote').inner_text())
                self.assertIn('800', page.locator('#liveWeightNote').inner_text())
                # Specimen view restores the unchanged slot inspector.
                page.locator('#viewSpecimenCanvas').click()
                self.assertEqual(page.locator('#liveFontSize').count(), 0)
                self.assertEqual(page.locator('#slotInspector [data-bind="type"]').count(), 1)
                self.assertEqual(self.duplicates(page), [])
                self.assertEqual(errors, [])

    def test_targeted_updates_canonical_values_and_rejection_reseed(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 56)
                self.wait_live(page)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '56px')
                update = self.updates(frame)[-1]
                sid = self.session_id(frame)
                self.assertEqual(update['sessionId'], sid)
                self.assertEqual(update['protocolVersion'], 1)
                self.assertEqual(update['targetId'], 'hero.title')
                self.assertEqual(update['patch'], {'fontSize': 56})
                self.assertEqual(update['baseRevision'], 0)
                self.assertRegex(update['requestId'], r'.+')
                # Canonicalised weight is reflected in the inspector.
                self.select(page, frame, 'stat.badge')
                self.set_value(page, '#liveFontWeight', 550)
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assertEqual(page.locator('#liveFontWeight').input_value(), '550')  # focused: not overwritten
                page.locator('#liveFontWeight').blur()
                page.wait_for_function('() => document.querySelector("#liveFontWeight").value === "600"')
                self.assertEqual(frame.evaluate('window.fake.styleOf("stat.badge").fontWeight'), '600')
                self.assertEqual(self.updates(frame)[-1]['baseRevision'], 1)
                # Locally invalid values are never sent; blur restores the acknowledged value.
                sent = len(self.updates(frame))
                self.set_value(page, '#liveFontSize', 1000)
                page.wait_for_timeout(250)
                self.assertEqual(len(self.updates(frame)), sent)
                self.assertEqual(page.locator('#liveFontSize').get_attribute('aria-invalid'), 'true')
                page.locator('#liveFontSize').blur()
                self.assertEqual(page.locator('#liveFontSize').input_value(), '20')
                # Target rejection: status shows the reason; the focused field is reseeded only on blur.
                frame.evaluate('window.fake.rejectNext = "unsupported-value"')
                self.set_value(page, '#liveFontSize', 25)
                self.wait_badge(page, '^Rejected: unsupported-value$')
                self.assertEqual(page.locator('#liveFontSize').input_value(), '25')
                page.locator('#liveFontSize').blur()
                self.assertEqual(page.locator('#liveFontSize').input_value(), '20')
                # Colour, text, alignment and transform.
                self.select(page, frame, 'hero.title')
                page.locator('#liveColorHex').fill('#FF0000')
                page.locator('#liveColorHex').dispatch_event('change')
                page.wait_for_function('() => document.querySelector("#liveColor").value === "#ff0000"')
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").color'), 'rgb(255, 0, 0)')
                page.locator('#liveText').fill('New headline')
                page.wait_for_function('() => /Live/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('#liveTextAlign').select_option('center')
                page.locator('#liveTextTransform').select_option('uppercase')
                deadline = time.time() + 5
                while time.time() < deadline and frame.evaluate('window.fake.styleOf("hero.title").textTransform') != 'uppercase':
                    page.wait_for_timeout(50)
                self.assertEqual(frame.evaluate('window.fake.textOf("hero.title")'), 'New headline')
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").textAlign'), 'center')
                # Reset target removes everything.
                page.locator('#liveResetTarget').click()
                page.wait_for_function('() => document.querySelector("#liveText").value === "Hello world"')
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '32px')
                resets = [item['data'] for item in self.received(frame, 'design:reset')]
                self.assertEqual(resets[-1]['targetId'], 'hero.title')
                self.assertEqual(resets[-1]['sessionId'], sid)
                self.assertEqual(errors, [])

    def test_single_in_flight_request_coalesces_pending_patches(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                frame.evaluate('window.fake.hold = true')
                for size in (40, 41, 42, 43):
                    self.set_value(page, '#liveFontSize', size)
                self.set_value(page, '#liveLineHeight', 1.5)
                page.wait_for_timeout(300)
                self.assertEqual([u['patch'] for u in self.updates(frame)], [{'fontSize': 40}])
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                patches = [u['patch'] for u in self.updates(frame)]
                self.assertEqual(patches, [{'fontSize': 40}, {'fontSize': 43, 'lineHeight': 1.5}])
                self.assertEqual([u['baseRevision'] for u in self.updates(frame)], [0, 1])
                self.assertEqual(page.locator('#liveFontSize').input_value(), '43')
                self.assertEqual(errors, [])

    def test_revision_conflict_is_retried_once(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                frame.evaluate('window.fake.bumpRevision()')
                self.set_value(page, '#liveFontSize', 50)
                page.wait_for_function('() => /^Live · rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                updates = self.updates(frame)
                self.assertEqual([(u['baseRevision'], u['patch']) for u in updates], [(0, {'fontSize': 50}), (1, {'fontSize': 50})])
                self.assertNotEqual(updates[0]['requestId'], updates[1]['requestId'])
                # Persistent conflicts stop after one retry.
                frame.evaluate('window.fake.conflictAlways = true')
                self.set_value(page, '#liveFontSize', 60)
                self.wait_badge(page, '^Rejected: revision-conflict$')
                page.wait_for_timeout(300)
                self.assertEqual(len(self.updates(frame)), 4)
                self.assertEqual(page.locator('#liveFontSize').input_value(), '60')
                page.locator('#liveFontSize').blur()
                self.assertEqual(page.locator('#liveFontSize').input_value(), '50')
                self.assertEqual(errors, [])

    def test_select_interact_toggle_and_studio_owned_overlay(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertIn('active', page.locator('#bridgeModeSelect').get_attribute('class'))
                frame.evaluate('window.fake.hover("hero.title")')
                hover = page.locator('#bridgeOverlayHover')
                hover.wait_for(state='visible')
                frame_box = page.locator('#targetAppFrame').bounding_box()
                rect = frame.evaluate('(() => { const r = document.querySelector("h1").getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; })()')
                box = hover.bounding_box()
                self.assertAlmostEqual(box['x'], frame_box['x'] + rect['x'], delta=1.5)
                self.assertAlmostEqual(box['y'], frame_box['y'] + rect['y'], delta=1.5)
                self.assertAlmostEqual(box['width'], rect['width'], delta=1.5)
                self.assertIn('Hero title', hover.inner_text())
                frame.evaluate('window.fake.hover(null)')
                hover.wait_for(state='hidden')
                self.select(page, frame, 'hero.lead')
                selected = page.locator('#bridgeOverlaySelected')
                selected.wait_for(state='visible')
                self.assertIn('Lead', selected.inner_text())
                frame.evaluate('window.scrollTo(0, 15)')
                frame.evaluate('window.fake.bounds("hero.lead")')
                lead_y = frame.evaluate('document.querySelector("p").getBoundingClientRect().y')
                page.wait_for_function('(y) => Math.abs(document.querySelector("#bridgeOverlaySelected").getBoundingClientRect().y - (document.querySelector("#targetAppFrame").getBoundingClientRect().y + y)) < 1.5', arg=lead_y)
                # Editor chrome never enters target markup.
                self.assertEqual(frame.evaluate('document.querySelectorAll("[id^=bridgeOverlay], .live-overlay").length'), 0)
                page.locator('#bridgeModeInteract').click()
                deadline = time.time() + 3
                while time.time() < deadline and frame.evaluate('window.fake.mode') != 'interact':
                    page.wait_for_timeout(50)
                self.assertEqual(frame.evaluate('window.fake.mode'), 'interact')
                modes = [item['data'] for item in self.received(frame, 'design:mode')]
                self.assertEqual(modes[-1]['mode'], 'interact')
                self.assertEqual(modes[-1]['sessionId'], self.session_id(frame))
                self.assertIn('active', page.locator('#bridgeModeInteract').get_attribute('class'))
                self.assertNotIn('active', page.locator('#bridgeModeSelect').get_attribute('class'))
                page.locator('#bridgeModeSelect').click()
                deadline = time.time() + 3
                while time.time() < deadline and frame.evaluate('window.fake.mode') != 'select':
                    page.wait_for_timeout(50)
                self.assertEqual(frame.evaluate('window.fake.mode'), 'select')
                # Hidden in Specimen view.
                page.locator('#viewSpecimenCanvas').click()
                self.assertFalse(selected.is_visible())
                self.assertFalse(hover.is_visible())
                self.assertEqual(errors, [])

    def test_code_panel_css_html_json_copy_and_download(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertIn('No text changes yet.', self.code(page, 'Html'))
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 56)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('#liveColorHex').fill('#ff0000')
                page.locator('#liveColorHex').dispatch_event('change')
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.select(page, frame, 'auto.h2.1')
                self.set_value(page, '#liveLetterSpacing', 0.1)
                page.wait_for_function('() => /rev 3$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.select(page, frame, 'hero.lead')
                page.locator('#liveText').fill('Changed lead')
                page.wait_for_function('() => /rev 4$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '3')
                css = self.code(page, 'Css')
                self.assertIn('/* Hero title (hero.title) */\n[data-design-id="hero.title"] {\n  font-size: 56px !important;\n  color: #ff0000 !important;\n}', css)
                self.assertIn('/* Features heading (auto.h2.1) — auto-discovered — add data-design-id for a stable selector */\n#features {\n  letter-spacing: 0.1em !important;\n}', css)
                self.assertNotIn('hero.lead', css)
                self.assertNotRegex(css, r'\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}')
                page.wait_for_timeout(1100)
                self.assertEqual(self.code(page, 'Css'), css)
                html = self.code(page, 'Html')
                self.assertIn('Changed lead', html)
                self.assertIn('data-design-id="hero.lead"', html)
                self.assertNotIn('Hello world', html)
                data = json.loads(self.code(page, 'Json'))
                self.assertEqual(data, {'target': FAKE, 'revision': 4, 'overrides': {
                    'hero.title': {'fontSize': 56, 'color': '#ff0000'},
                    'auto.h2.1': {'letterSpacing': 0.1},
                    'hero.lead': {'text': 'Changed lead'}}})
                page.locator('#codeTabCss').click()
                # http://studio.test is not a secure context, so record the Clipboard API call instead.
                page.evaluate('''() => Object.defineProperty(navigator, 'clipboard', {configurable: true,
                    value: {writeText: async (text) => { window.__copied = text; }}})''')
                page.locator('#liveCodeCopy').click()
                page.wait_for_function('() => /Copied/i.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertEqual(page.evaluate('window.__copied'), css)
                with page.expect_download() as info:
                    page.locator('#liveCodeDownload').click()
                download = info.value
                self.assertEqual(download.suggested_filename, 'fontkit-overrides.css')
                self.assertEqual(Path(download.path()).read_text(encoding='utf-8'), css)
                # Under a non-dev origin without the status endpoint, sync stays disabled.
                self.assertTrue(page.locator('#liveCodeSync').is_disabled())
                self.assertTrue(page.locator('#liveCodeAutoSync').is_disabled())
                self.assertEqual(errors, [])

    def test_sync_and_debounced_serialized_auto_sync(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                sync = page.locator('#liveCodeSync')
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                self.assertIn('demo/fontkit-overrides.css', sync.get_attribute('title'))
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 48)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                sync.click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertEqual(len(self.puts), 1)
                self.assertEqual(self.puts[0]['type'], 'text/css')
                self.assertEqual(self.puts[0]['body'], self.code(page, 'Css'))
                self.assertIn('font-size: 48px !important;', self.puts[0]['body'])
                # Auto-sync: delay each PUT so overlapping writes would be observable.
                page.evaluate('''() => { const native = window.fetch; window.__puts = {active:0, max:0, count:0};
                    window.fetch = async (url, options = {}) => {
                        if (options.method !== 'PUT') return native(url, options);
                        const s = window.__puts; s.active += 1; s.count += 1; s.max = Math.max(s.max, s.active);
                        await new Promise(r => setTimeout(r, 500));
                        try { return await native(url, options); } finally { s.active -= 1; }
                    }; }''')
                page.locator('#liveCodeAutoSync').check()
                page.wait_for_function('() => window.__puts.count >= 1')
                for size in (50, 51, 52):
                    self.set_value(page, '#liveFontSize', size)
                    page.wait_for_timeout(150)
                page.wait_for_function('() => /rev 4$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(450)
                for size in (60, 61):
                    self.set_value(page, '#liveFontSize', size)
                    page.wait_for_timeout(100)
                page.wait_for_function('() => /rev 6$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_function('() => window.__puts.active === 0 && /Saved/.test(document.querySelector("#liveCodeStatus").textContent)', timeout=8000)
                page.wait_for_timeout(700)
                stats = page.evaluate('window.__puts')
                self.assertEqual(stats['max'], 1)
                self.assertLessEqual(stats['count'], 4)
                self.assertIn('font-size: 61px !important;', self.puts[-1]['body'])
                self.assertEqual(self.puts[-1]['body'], self.code(page, 'Css'))
                # Composition tokens from the explicit Sync to Live App also reach the synced file.
                page.locator('#btnSyncToApp').click()
                page.wait_for_function('() => /rev 7$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                deadline = time.time() + 6
                while time.time() < deadline and '--font-display' not in self.puts[-1]['body']:
                    page.wait_for_timeout(100)
                self.assertIn('--font-display', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    def test_sync_disabled_under_file_url(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                browser = launch(self.runtime, engine)
                self.browsers.append(browser)
                page = browser.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(HTML.as_uri())
                page.locator('#modeComposer').click()
                page.locator('#viewTargetApp').click()
                sync = page.locator('#liveCodeSync')
                self.assertTrue(sync.is_disabled())
                self.assertIn('file://', sync.get_attribute('title'))
                self.assertTrue(page.locator('#liveCodeAutoSync').is_disabled())
                self.assertEqual(errors, [])

    def test_explicit_composition_sync_is_session_gated(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                page.wait_for_timeout(300)
                self.assertEqual([u for u in self.updates(frame) if 'targetId' not in u], [])
                page.locator('#btnSyncToApp').click()
                self.wait_live(page)
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(len(composition), 1)
                update = composition[0]
                self.assertEqual(update['sessionId'], self.session_id(frame))
                self.assertEqual(update['protocolVersion'], 1)
                self.assertEqual(update['baseRevision'], 0)
                self.assertIn('--font-display', update['patch']['tokens'])
                self.assertIsInstance(update['patch']['slots'], list)
                # Only fields the bridge reads are sent (it never reads familyRaw, canvasWidth or backgroundHex).
                self.assertEqual(set(update['patch']['layout']), {'order'})
                self.assertTrue(all('familyRaw' not in slot for slot in update['patch']['slots']))
                self.assertTrue(frame.evaluate('window.fake.ledger().tokens["--font-display"].length > 0'))
                hellos = self.received(frame, 'design:hello')
                self.assertTrue(all(h['origin'] == STUDIO for h in self.received(frame)))
                self.assertGreaterEqual(len(hellos), 1)
                self.assertEqual(errors, [])

    def test_restore_page_text_uses_session(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.lead')
                page.locator('#liveText').fill('Temporary')
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('#btnRestoreOriginalText').click()
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                restore = self.received(frame, 'design:restore-text')[-1]['data']
                self.assertEqual(restore['sessionId'], self.session_id(frame))
                self.assertEqual(frame.evaluate('window.fake.textOf("hero.lead")'), 'Lead copy for the page.')
                self.assertEqual(page.locator('#liveText').input_value(), 'Lead copy for the page.')
                self.assertIn('No text changes yet.', self.code(page, 'Html'))
                self.assertEqual(errors, [])


class StudioPersistenceTests(LiveCase):
    def test_reconnect_banner_reapply_and_accept(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                banner = page.locator('#liveReconnectBanner')
                self.assertFalse(banner.is_visible())
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 70)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                frame.evaluate('location.reload()')
                banner.wait_for(state='visible')
                frame = self.frame(page)
                self.wait_connected(page)
                # Never auto-applied.
                page.wait_for_timeout(300)
                self.assertEqual(self.updates(frame), [])
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '32px')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                deadline = time.time() + 5
                while time.time() < deadline and frame.evaluate('window.fake.styleOf("hero.title").fontSize') != '70px':
                    page.wait_for_timeout(50)
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '70px')
                self.assertEqual(self.updates(frame)[0]['patch'], {'fontSize': 70})
                # Reload again and accept the target state as canonical.
                frame.evaluate('location.reload()')
                banner.wait_for(state='visible')
                frame = self.frame(page)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {})
                self.assertNotIn('live', self.export(page))
                page.wait_for_timeout(200)
                self.assertEqual(self.updates(frame), [])
                self.assertEqual(errors, [])

    def test_live_field_export_import_round_trip_and_transactional_rejection(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertNotIn('live', self.export(page))
                self.select(page, frame, 'stat.badge')
                self.set_value(page, '#liveFontWeight', 790)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                exported = self.export(page)
                self.assertEqual(exported['version'], '0.1.1')
                self.assertEqual(exported['live'], {'target': FAKE, 'revision': 1, 'overrides': {'stat.badge': {'fontWeight': 800}}})
                self.assertNotIn('live', exported['composition'])
                before_canvas = page.locator('#composerCanvas').inner_html()
                bad_lives = [
                    42, [], {'target': FAKE, 'revision': 1, 'overrides': []},
                    {'target': 7, 'revision': 1, 'overrides': {}},
                    {'target': FAKE, 'revision': -1, 'overrides': {}},
                    {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': {'fontSize': 1000}}},
                    {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': {'bogus': 1}}},
                    {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': {'color': 'red; x: y'}}},
                    {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': {'fontFamily': 'url(x)'}}},
                    {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': 5}},
                ]
                for bad in bad_lives:
                    doc = {**exported, 'composition': {**exported['composition'], 'canvasWidth': '640'}, 'live': bad}
                    status = self.import_document(page, doc)
                    self.assertTrue(status.startswith('Import failed:'), (bad, status))
                    self.assertEqual(self.export(page), exported)
                    self.assertEqual(page.locator('#composerCanvas').inner_html(), before_canvas)
                # A valid live field replaces Studio's saved overrides; it is never auto-applied.
                good = {**exported, 'live': {'target': FAKE, 'revision': 9, 'overrides': {
                    'hero.title': {'fontSize': 44.444, 'textAlign': 'center', 'color': '#ABC'}}}}
                status = self.import_document(page, good)
                self.assertIn('Composition imported.', status)
                live = self.export(page)['live']
                self.assertEqual(live['overrides'], {'hero.title': {'fontSize': 44.44, 'textAlign': 'center', 'color': '#abc'}})
                self.assertEqual(live['revision'], 9)
                page.locator('#viewTargetApp').click()
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
                page.wait_for_timeout(200)
                self.assertEqual(len(self.updates(frame)), 1)
                # Legacy documents without live keep the receiving live state.
                legacy = {'version': '0.1.0', 'composition': {'slots': [{'type': 'text', 'text': 'legacy'}]}}
                self.assertIn('Composition imported.', self.import_document(page, legacy))
                self.assertEqual(self.export(page)['live']['revision'], 9)
                self.assertEqual(errors, [])

    def test_narrow_target_view_has_no_horizontal_overflow(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, viewport={'width': 390, 'height': 844})
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 44)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(250)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
                for selector in ('#liveCodePanel', '#slotInspector', '#bridgeModeSelect', '#liveCodeSync'):
                    box = page.locator(selector).bounding_box()
                    self.assertLessEqual(box['x'] + box['width'], 390.5, selector)
                self.assertEqual(self.duplicates(page), [])
                self.assertEqual(errors, [])


class StudioFixRound1Tests(LiveCase):
    """Behaviour tests written RED-first for review round 1 (docs/implementation/tasks/v02-task-c-review.md)."""

    PROBES = ('javascript:parent.__pwned=parent.location.origin;void 0',
              'data:text/html,<script>parent.__pwned="data"</script>',
              'file:///etc/hostname')

    def assert_not_loaded(self, page):
        self.assertIsNone(page.evaluate('window.__pwned'))
        src = page.locator('#targetAppFrame').get_attribute('src') or ''
        self.assertFalse(re.match(r'^(javascript|data|blob|file):', src, re.I), src)

    def test_c1_target_url_scheme_allow_list(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for probe in self.PROBES:
                    page, errors = self.open(engine, target=probe)
                    page.wait_for_timeout(300)
                    self.assert_not_loaded(page)
                    self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Invalid target URL')
                    self.assertEqual(errors, [])
                # Same-origin blob: and javascript: through the URL field (Connect button and Enter).
                page, errors = self.open(engine, target=None)
                blob = page.evaluate(
                    "() => URL.createObjectURL(new Blob(['<script>parent.__pwned=\"blob\"</' + 'script>'], {type: 'text/html'}))")
                for probe in (blob, self.PROBES[0]):
                    self.connect(page, probe)
                    page.wait_for_timeout(300)
                    self.assert_not_loaded(page)
                    self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Invalid target URL')
                    page.locator('#targetAppUrl').press('Enter')
                    page.wait_for_timeout(200)
                    self.assert_not_loaded(page)
                # Imported live.target with an unsafe scheme fails the whole import.
                exported = self.export(page)
                for bad in ('javascript:alert(1)', 'data:text/html,x', 'blob:http://studio.test/x'):
                    status = self.import_document(page, {**exported, 'live': {'target': bad, 'revision': 1, 'overrides': {}}})
                    self.assertTrue(status.startswith('Import failed:'), status)
                self.assertEqual(self.export(page), exported)
                self.assertEqual(errors, [])
                # A dev-server status.target with an unsafe scheme is never used to prefill.
                page, errors = self.open(engine, target=None, sync=True, status_target='javascript:parent.__pwned=1')
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                self.assertEqual(page.locator('#targetAppUrl').input_value(), 'http://localhost:8001/demo/')
                self.assert_not_loaded(page)
                self.assertEqual(errors, [])

    def test_i1_keystroke_numeric_entry_applies_typed_values(self):
        # (target, field, typed text, patch key, check)
        cases = (('hero.title', '#liveFontSize', '24', 'fontSize', ('fontSize', '24px')),
                 ('hero.title', '#liveFontWeight', '300', 'fontWeight', ('fontWeight', '300')),
                 ('hero.lead', '#liveLineHeight', '1.5', 'lineHeight', ('inline', '1.5')),
                 ('hero.lead', '#liveLetterSpacing', '0.08', 'letterSpacing', ('letterSpacing', '1.28px')))
        limits = {'fontSize': (4, 400), 'fontWeight': (1, 1000), 'lineHeight': (.5, 5), 'letterSpacing': (-.5, 2)}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                for target, selector, typed, key, (prop, rendered) in cases:
                    self.select(page, frame, target)
                    field = page.locator(selector)
                    field.click()
                    page.keyboard.press('ControlOrMeta+a')
                    page.keyboard.press('Backspace')
                    page.keyboard.type(typed, delay=120)
                    page.wait_for_timeout(400)
                    self.assertEqual(field.input_value(), typed, (target, key))
                    if prop == 'inline':
                        actual = frame.evaluate('(id) => document.querySelector(`[data-design-id="${id}"]`).style.lineHeight', target)
                    else:
                        actual = frame.evaluate('(id) => window.fake.styleOf(id)', target)[prop]
                    self.assertEqual(actual, rendered, (target, key))
                    self.assertNotRegex(page.locator('#bridgeStatusBadge').inner_text(), '^Rejected')
                    sent = [u['patch'][key] for u in self.updates(frame) if u.get('targetId') == target and key in u['patch']]
                    self.assertEqual(sent[-1], float(typed) if '.' in typed else int(typed))
                    self.assertTrue(all(limits[key][0] <= value <= limits[key][1] for value in sent), sent)
                    self.assertTrue(all(a != b for a, b in zip(sent, sent[1:])), (key, sent))
                self.assertEqual(errors, [])

    def test_i2_studio_overrides_are_persisted_and_accept_is_explicit(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 70)
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('#liveCodeAutoSync').check()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn('font-size: 70px !important;', self.puts[-1]['body'])
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertRegex(banner.inner_text(), r'(?is)accept target state.*replace')
                # While unresolved, Studio's saved overrides are what gets persisted.
                self.select(page, frame, 'hero.lead')
                page.locator('#liveColorHex').fill('#00ff00')
                page.locator('#liveColorHex').dispatch_event('change')
                page.wait_for_function('() => /Live/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                count = len(self.puts)
                page.locator('#liveCodeSync').click()
                deadline = time.time() + 5
                while time.time() < deadline and len(self.puts) == count:
                    page.wait_for_timeout(50)
                body = self.puts[-1]['body']
                self.assertIn('font-size: 70px !important;', body)
                self.assertIn('color: #00ff00 !important;', body)
                self.assertIn('font-size: 70px !important;', self.code(page, 'Css'))
                # Accept is explicit: it replaces saved overrides, stops auto-sync, and never rewrites the file by itself.
                page.wait_for_timeout(300)
                puts_before = len(self.puts)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertFalse(page.locator('#liveCodeAutoSync').is_checked())
                self.assertRegex(page.locator('#liveCodeStatus').inner_text(), r'(?i)replaced.*file')
                self.select(page, frame, 'stat.badge')
                self.set_value(page, '#liveFontWeight', 800)
                page.wait_for_function('() => /Live · rev/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(800)
                self.assertEqual(len(self.puts), puts_before)
                self.assertIn('font-size: 70px !important;', self.puts[-1]['body'])
                # Only an explicit Sync writes the accepted (smaller) state.
                page.locator('#liveCodeSync').click()
                deadline = time.time() + 5
                while time.time() < deadline and len(self.puts) == puts_before:
                    page.wait_for_timeout(50)
                self.assertNotIn('70px', self.puts[-1]['body'])
                self.assertIn('font-weight: 800 !important;', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    def test_every_control_message_carries_protocol_version_and_session(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                sid = self.session_id(frame)
                page.locator('#btnSyncToApp').click()
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('[data-live-target="hero.lead"]').click()
                page.wait_for_selector('#liveTargetName[data-target-id="hero.lead"]')
                self.set_value(page, '#liveText', 'Changed')
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.locator('#bridgeModeInteract').click()
                page.locator('#bridgeModeSelect').click()
                page.locator('#btnRestoreOriginalText').click()
                page.wait_for_function('() => /rev 3$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_selector('#liveResetTarget')
                page.locator('#liveResetTarget').click()
                page.wait_for_function('() => /rev 4$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_selector('[data-live-back]')
                page.locator('[data-live-back]').click()
                page.wait_for_timeout(300)
                messages = [item for item in self.received(frame) if item['fromParent']]
                kinds = {m['data']['type'] for m in messages}
                for kind in ('design:hello', 'design:update', 'design:select', 'design:mode', 'design:reset', 'design:restore-text'):
                    self.assertIn(kind, kinds)
                self.assertNotIn('design:highlight', kinds)
                for item in messages:
                    data = item['data']
                    self.assertEqual(item['origin'], STUDIO)
                    self.assertEqual(data.get('protocolVersion'), 1, data)
                    self.assertEqual(data.get('sessionId'), sid, data)
                restore = [m['data'] for m in messages if m['data']['type'] == 'design:restore-text'][-1]
                self.assertEqual(restore['baseRevision'], 2)
                self.assertTrue(restore['requestId'])
                composition = [m['data'] for m in messages if m['data']['type'] == 'design:update' and 'targetId' not in m['data']]
                self.assertEqual(len(composition), 1)
                self.assertEqual(errors, [])

    def test_i3_every_iframe_load_regreets_both_announce_orders(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for variant in (FAKE, f'{FAKE}?late=1'):
                    page, errors = self.open(engine, target=variant)
                    self.wait_connected(page)
                    for _ in range(2):
                        frame = self.frame(page)
                        sid = self.session_id(frame)
                        frame.evaluate('location.reload()')
                        page.wait_for_timeout(100)
                        self.wait_connected(page)
                        frame = self.frame(page)
                        hellos = [h['data']['sessionId'] for h in self.received(frame, 'design:hello')]
                        if 'late' in variant:
                            # load comes first: the new document is greeted with the session already in use.
                            self.assertEqual(hellos[0], sid)
                        else:
                            # bridge-ready comes first and starts a fresh session; load re-greets with it.
                            self.assertEqual(len(hellos), 2)
                            self.assertEqual(len(set(hellos)), 1)
                            self.assertNotEqual(hellos[0], sid)
                    frame.evaluate('(url) => { location.href = url; }', f'{TARGET}/no-bridge.html')
                    self.wait_badge(page, '^No bridge detected$', timeout=7000)
                    self.assertTrue(page.locator('#bridgeHint').is_visible())
                    self.assertEqual(page.locator('#liveFontSize').count(), 0)
                    self.assertEqual(errors, [])

    def test_a_text_overrides_compare_like_the_trimmed_bridge_ledger(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.lead')
                self.set_value(page, '#liveText', 'Changed lead  ')
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveText', 'Hello world, again')
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.set_value(page, '#liveText', 'Hello world')
                page.wait_for_function('() => /rev 3$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                # Text typed back to the original is no override.
                self.assertNotIn('hero.title', self.export(page)['live']['overrides'])
                # A bridge restart (fresh handshake, same page state) must not raise a false conflict.
                frame.evaluate('window.fake.reannounce()')
                page.wait_for_timeout(150)
                self.wait_connected(page)
                page.wait_for_timeout(200)
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_b_design_targets_replaces_the_target_list(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'stat.badge')
                frame.evaluate('window.fake.emitTargets(["hero.title", "hero.lead"])')
                page.wait_for_function('() => !document.querySelector("#liveTargetName")')
                page.wait_for_function('() => document.querySelectorAll("[data-live-target]").length === 2')
                ids = page.locator('[data-live-target]').evaluate_all('els => els.map(el => el.dataset.liveTarget)')
                self.assertEqual(ids, ['hero.title', 'hero.lead'])
                self.assertFalse(page.locator('#bridgeOverlaySelected').is_visible())
                self.assertEqual(errors, [])

    def test_c_live_import_rejects_values_css_would_reject(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)
                page.locator('#modeComposer').click()
                exported = self.export(page)
                for patch in ({'color': 'rgb()'}, {'color': 'hsl(1, 2, 3, 4, 5)'}, {'fontFamily': '123'}):
                    doc = {**exported, 'live': {'target': FAKE, 'revision': 1, 'overrides': {'hero.title': patch}}}
                    status = self.import_document(page, doc)
                    self.assertTrue(status.startswith('Import failed:'), (patch, status))
                    self.assertEqual(self.export(page), exported)
                good = {**exported, 'live': {'target': FAKE, 'revision': 1, 'overrides': {
                    'hero.title': {'color': 'rgb(1, 2, 3)', 'fontFamily': '"Gotham", sans-serif'}}}}
                self.assertIn('Composition imported.', self.import_document(page, good))
                self.assertEqual(errors, [])

    def test_i4_reload_that_loses_composition_tokens_raises_banner_not_a_smaller_file(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                page.locator('#liveCodeAutoSync').check()
                page.locator('#btnSyncToApp').click()
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                deadline = time.time() + 5
                while time.time() < deadline and not any(':root {' in put['body'] for put in self.puts):
                    page.wait_for_timeout(50)
                self.assertIn('--font-display', self.puts[-1]['body'])
                synced = len(self.puts)
                frame.evaluate('location.reload()')
                page.wait_for_timeout(100)
                self.wait_connected(page)
                frame = self.frame(page)
                # The target lost the tokens: that is a reconnect conflict, not a silent shrink.
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
                self.assertRegex(page.locator('#liveReconnectText').inner_text(), r'(?i)token')
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 50)
                page.wait_for_function('() => /Live · rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(800)
                for put in self.puts[synced:]:
                    self.assertIn('--font-display', put['body'])
                css = self.code(page, 'Css')
                self.assertIn('--font-display', css)
                self.assertIn('font-size: 50px !important;', css)
                # Reapply restores the tokens on the target through a tokens-only composition update.
                page.locator('#liveReapply').click()
                page.locator('#liveReconnectBanner').wait_for(state='hidden')
                deadline = time.time() + 5
                while time.time() < deadline and not frame.evaluate('Object.keys(window.fake.ledger().tokens).length'):
                    page.wait_for_timeout(50)
                tokens = frame.evaluate('window.fake.ledger().tokens')
                self.assertIn('--font-display', tokens)
                self.assertTrue(frame.evaluate(
                    'getComputedStyle(document.documentElement).getPropertyValue("--font-display").trim().length > 0'))
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(list(composition[-1]['patch'].keys()), ['tokens'])
                self.assertEqual(errors, [])

    def test_m3_late_reset_reply_reselects_like_the_normal_path(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.lead')
                page.locator('#liveText').fill('Temporary lead')
                page.wait_for_function('() => /rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                frame.evaluate('window.fake.hold = true')
                page.locator('#liveResetTarget').click()
                self.wait_badge(page, '^No response from target$', timeout=10000)
                selects = len(self.received(frame, 'design:select'))
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                self.wait_badge(page, r'^Live · rev 2$')
                deadline = time.time() + 3
                while time.time() < deadline and len(self.received(frame, 'design:select')) == selects:
                    page.wait_for_timeout(50)
                self.assertGreater(len(self.received(frame, 'design:select')), selects)
                page.wait_for_function('() => document.querySelector("#liveText").value === "Lead copy for the page."')
                self.assertEqual(errors, [])

    def test_m3_late_applied_after_timeout_updates_canonical_state(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                frame.evaluate('window.fake.hold = true')
                self.set_value(page, '#liveFontSize', 60)
                self.wait_badge(page, '^No response from target$', timeout=10000)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                self.wait_badge(page, r'^Live · rev 1$')
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {'hero.title': {'fontSize': 60}})
                self.assertIn('font-size: 60px !important;', self.code(page, 'Css'))
                self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# Wave 2 (Task F): arrangement UI, pop-out, free fonts, saved tokens (D017).
# ---------------------------------------------------------------------------
ARRANGE = f'{FAKE}?arrange=1'
SPOOFER = f'{EVIL}/spoofer.html'
GOOGLE_RE = re.compile(r'^https://fonts\.googleapis\.com/css2\?family=[A-Za-z0-9+:@;.,_-]+&display=swap$')
FREE_FAMILIES = {
    'fraunces': ('Fraunces', 'Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900'),
    'crimson-pro': ('Crimson Pro', 'Crimson+Pro:ital,wght@0,200..900;1,200..900'),
    'source-serif-4': ('Source Serif 4', 'Source+Serif+4:ital,opsz,wght@0,8..60,200..900;1,8..60,200..900'),
    'playfair-display': ('Playfair Display', 'Playfair+Display:ital,wght@0,400..900;1,400..900'),
    'instrument-serif': ('Instrument Serif', 'Instrument+Serif:ital@0;1'),
    'inter': ('Inter', 'Inter:wght@100..900'),
    'space-grotesk': ('Space Grotesk', 'Space+Grotesk:wght@300..700'),
    'dm-sans': ('DM Sans', 'DM+Sans:ital,wght@0,100..1000;1,100..1000'),
    'work-sans': ('Work Sans', 'Work+Sans:ital,wght@0,100..900;1,100..900'),
    'ibm-plex-sans': ('IBM Plex Sans', 'IBM+Plex+Sans:ital,wght@0,100..700;1,100..700'),
    'archivo': ('Archivo', 'Archivo:ital,wght@0,100..900;1,100..900'),
    'bricolage-grotesque': ('Bricolage Grotesque', 'Bricolage+Grotesque:opsz,wght@12..96,200..800'),
    'bebas-neue': ('Bebas Neue', 'Bebas+Neue'),
    'jetbrains-mono': ('JetBrains Mono', 'JetBrains+Mono:ital,wght@0,100..800;1,100..800'),
    'ibm-plex-mono': ('IBM Plex Mono', 'IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700'),
    'space-mono': ('Space Mono', 'Space+Mono:ital,wght@0,400;0,700;1,400;1,700'),
}
FREE_URLS = {key: f'https://fonts.googleapis.com/css2?family={fam}&display=swap' for key, (_, fam) in FREE_FAMILIES.items()}


class ArrangeCase(LiveCase):
    def wait_ready(self, page, count):
        """Both announce orders: wait for the load re-hello, then the connected badge."""
        self.wait_badge(page, rf'^Connected \({count} targets\)$')
        frame = self.frame(page)
        frame.wait_for_function('document.readyState === "complete"')
        frame.wait_for_function('window.__received.filter(i => i.data && i.data.type === "design:hello").length >= 2')
        self.wait_badge(page, rf'^Connected \({count} targets\)$')
        return frame

    def open_arrange(self, engine, viewport=None):
        page, errors = self.open(engine, target=ARRANGE, viewport=viewport)
        return page, errors, self.wait_ready(page, 11)

    def moves(self, frame):
        return [item['data'] for item in self.received(frame, 'design:move')]

    def dom(self, frame, container='cards'):
        return frame.evaluate('(key) => window.fake.domOrder(key)', container)

    def wait_list(self, page, ids):
        page.wait_for_function('(ids) => JSON.stringify([...document.querySelectorAll("#liveSiblingList [data-sibling-id]")]'
                               '.map(el => el.dataset.siblingId)) === JSON.stringify(ids)', arg=ids)


class StudioArrangeTests(ArrangeCase):
    def test_move_buttons_send_design_move_and_the_target_reorders(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.b')
                for selector in ('#liveMoveFirst', '#liveMovePrev', '#liveMoveNext', '#liveMoveLast', '#liveSiblingList',
                                 '#liveMoveContainer', '#liveMoveInto'):
                    self.assertEqual(page.locator(selector).count(), 1, selector)
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertIn('2 of 4', page.locator('#liveArrangeInfo').inner_text())
                self.assertIn('Cards', page.locator('#liveArrangeInfo').inner_text())
                page.locator('#liveMoveFirst').click()
                self.wait_list(page, ['card.b', 'card.a', 'card.c', 'card.d'])
                self.assertEqual(self.dom(frame), ['card.b', 'card.a', 'card.c', 'card.d'])
                message = self.moves(frame)[0]
                self.assertEqual((message['targetId'], message['to'], message['strategy']), ('card.b', {'index': 0}, 'dom'))
                self.assertEqual((message['protocolVersion'], message['sessionId']), (1, self.session_id(frame)))
                self.assertIsInstance(message['baseRevision'], int)
                self.assertEqual(page.locator('#liveMoveFirst').is_disabled(), True)
                self.assertEqual(page.locator('#liveMovePrev').is_disabled(), True)
                self.wait_badge(page, r'^Live · rev 1$')
                page.locator('#liveMoveNext').click()
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                page.locator('#liveMoveLast').click()
                self.wait_list(page, ['card.a', 'card.c', 'card.d', 'card.b'])
                self.assertEqual(self.dom(frame), ['card.a', 'card.c', 'card.d', 'card.b'])
                self.assertEqual([m['to'] for m in self.moves(frame)], [{'index': 0}, {'index': 1}, {'index': 3}])
                self.assertTrue(page.locator('#liveMoveNext').is_disabled())
                page.locator('#liveMovePrev').click()
                self.wait_list(page, ['card.a', 'card.c', 'card.b', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'index': 2})
                self.assertEqual(self.duplicates(page), [])
                self.assertEqual(errors, [])

    def test_sibling_list_escapes_names_supports_keyboard_and_drag_and_drop(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate("""() => { document.querySelector('[data-design-id="card.c"]').dataset.designName =
                    '<img src=x onerror="window.__xss=1">Card C'; }""")
                self.select(page, frame, 'card.a')
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                # Target-supplied names are text, never markup.
                self.assertEqual(page.locator('#liveSiblingList img').count(), 0)
                self.assertEqual(page.evaluate('window.__xss'), None)
                items = page.locator('#liveSiblingList [data-sibling-id]')
                self.assertEqual(items.nth(2).locator('.sibling-name').inner_text(), '<img src=x onerror="window.__xss=1">Card C')
                self.assertTrue(all(items.nth(i).get_attribute('draggable') == 'true' for i in range(4)))
                self.assertTrue(all(items.nth(i).get_attribute('tabindex') is not None for i in range(4)))
                # Alt+Up moves the focused item; focus follows the moved item through the re-render.
                page.locator('[data-sibling-id="card.c"]').focus()
                page.keyboard.press('Alt+ArrowUp')
                self.wait_list(page, ['card.a', 'card.c', 'card.b', 'card.d'])
                self.assertEqual(self.dom(frame), ['card.a', 'card.c', 'card.b', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['targetId'], 'card.c')
                self.assertEqual(self.moves(frame)[-1]['to'], {'index': 1})
                page.wait_for_function('() => document.activeElement && document.activeElement.dataset.siblingId === "card.c"')
                page.keyboard.press('Alt+ArrowDown')
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                page.wait_for_function('() => document.activeElement && document.activeElement.dataset.siblingId === "card.c"')
                # Plain arrows only move focus; they never move elements.
                count = len(self.moves(frame))
                page.keyboard.press('ArrowDown')
                page.wait_for_function('() => document.activeElement && document.activeElement.dataset.siblingId === "card.d"')
                self.assertEqual(len(self.moves(frame)), count)
                # Moving a sibling does not change the selected target.
                self.assertEqual(page.locator('#liveTargetName').get_attribute('data-target-id'), 'card.a')
                # Drag and drop (HTML5 DnD): upper half drops before, lower half after.
                page.locator('[data-sibling-id="card.d"]').drag_to(page.locator('[data-sibling-id="card.a"]'),
                                                                  target_position={'x': 10, 'y': 2})
                self.wait_list(page, ['card.d', 'card.a', 'card.b', 'card.c'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'before': 'card.a'})
                self.assertEqual(self.moves(frame)[-1]['targetId'], 'card.d')
                self.assertEqual(self.dom(frame), ['card.d', 'card.a', 'card.b', 'card.c'])
                box = page.locator('[data-sibling-id="card.c"]').bounding_box()
                page.locator('[data-sibling-id="card.d"]').drag_to(page.locator('[data-sibling-id="card.c"]'),
                                                                  target_position={'x': 10, 'y': box['height'] - 2})
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'after': 'card.c'})
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(errors, [])

    def test_alt_arrow_shortcuts_only_apply_in_the_target_view_and_never_inside_text_fields(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.b')
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                page.locator('#bridgeModeSelect').focus()
                # Alt+Left/Right stay the browser's Back/Forward: never moved, never default-prevented.
                page.evaluate('''() => { window.__alt = []; window.addEventListener('keydown',
                    e => { if (e.key.startsWith('Arrow')) window.__alt.push([e.key, e.defaultPrevented]); }); }''')
                count = len(self.moves(frame))
                page.keyboard.press('Alt+ArrowRight')
                page.keyboard.press('Alt+ArrowLeft')
                page.wait_for_function('() => window.__alt.length === 2')
                page.wait_for_timeout(250)
                self.assertEqual(page.evaluate('window.__alt'), [['ArrowRight', False], ['ArrowLeft', False]])
                self.assertEqual(len(self.moves(frame)), count)
                page.keyboard.press('Alt+ArrowDown')
                self.wait_list(page, ['card.a', 'card.c', 'card.b', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'index': 2})
                page.keyboard.press('Alt+ArrowUp')
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                page.keyboard.press('Alt+Shift+ArrowUp')
                self.wait_list(page, ['card.b', 'card.a', 'card.c', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'index': 0})
                count = len(self.moves(frame))
                # Typing fields keep Alt+Arrow for themselves.
                self.select(page, frame, 'hero.lead')
                page.locator('#liveText').focus()
                page.keyboard.press('Alt+ArrowDown')
                page.wait_for_timeout(250)
                self.assertEqual(len(self.moves(frame)), count)
                # Specimen view: no live shortcuts.
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#viewSpecimenCanvas').focus()
                page.keyboard.press('Alt+ArrowDown')
                page.wait_for_timeout(250)
                self.assertEqual(len(self.moves(frame)), count)
                self.assertEqual(errors, [])

    def test_move_into_another_container(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.b')
                options = page.locator('#liveMoveContainer option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                names = [name for _, name in options]
                self.assertIn('Sidebar', names)
                self.assertNotIn('Cards', names, 'the current container is not a destination')
                sidebar = next(value for value, name in options if name == 'Sidebar')
                page.locator('#liveMoveContainer').select_option(sidebar)
                page.locator('#liveMoveInto').click()
                page.wait_for_function('() => /Sidebar/.test(document.querySelector("#liveArrangeInfo").textContent)')
                self.assertEqual(self.moves(frame)[-1]['to'], {'container': sidebar})
                self.assertEqual(self.dom(frame, 'cards'), ['card.a', 'card.c', 'card.d'])
                self.assertEqual(self.dom(frame, sidebar), ['side.x', 'side.y', 'card.b'])
                self.wait_list(page, ['side.x', 'side.y', 'card.b'])
                self.assertIn('3 of 3', page.locator('#liveArrangeInfo').inner_text())
                self.assertEqual(errors, [])

    def test_css_order_strategy_toggle_and_framework_default(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                # A block container offers no CSS order: no toggle, always the DOM strategy.
                self.select(page, frame, 'side.x')
                self.wait_list(page, ['side.x', 'side.y'])
                self.assertEqual(page.locator('#liveMoveStrategyCss').count(), 0)
                page.locator('#liveMoveNext').click()
                self.wait_list(page, ['side.y', 'side.x'])
                self.assertEqual(self.moves(frame)[-1]['strategy'], 'dom')
                # A flex container offers it, defaulting to DOM.
                self.select(page, frame, 'card.b')
                self.assertEqual(page.locator('#liveMoveStrategyDom').get_attribute('aria-pressed'), 'true')
                self.assertEqual(page.locator('#liveMoveStrategyCss').get_attribute('aria-pressed'), 'false')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveNext').click()
                self.wait_list(page, ['card.a', 'card.c', 'card.b', 'card.d'])
                self.assertEqual(self.moves(frame)[-1]['strategy'], 'css-order')
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'], 'CSS order leaves the DOM untouched')
                self.assertEqual(frame.evaluate('window.fake.visualOrder("cards")'), ['card.a', 'card.c', 'card.b', 'card.d'])
                css = self.code(page, 'Css')
                self.assertIn('/* Card B (card.b) */\n[data-design-id="card.b"] {\n  order: 2 !important;\n}', css)
                self.assertIn('order: 1 !important;', css)
                self.assertNotIn('<!--', css)
                html = self.code(page, 'Html')
                self.assertIn('Structure: Sidebar', html, 'the DOM move shows; the CSS-order move adds no HTML block')
                self.assertNotIn('Cards', html)
                # Framework-managed parents default to CSS order.
                frame.evaluate('window.fake.framework = {cards: "react"}')
                self.select(page, frame, 'card.d')
                self.assertEqual(page.locator('#liveMoveStrategyCss').get_attribute('aria-pressed'), 'true')
                page.locator('#liveMovePrev').click()
                page.wait_for_function('() => /Live · rev 3$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assertEqual(self.moves(frame)[-1]['strategy'], 'css-order')
                self.assertNotIn('force', self.moves(frame)[-1])
                self.assertEqual(errors, [])

    def test_framework_guard_offers_move_anyway_and_other_guards_do_not(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.framework = {cards: "react"}')
                self.select(page, frame, 'card.b')
                page.locator('#liveMoveStrategyDom').click()
                page.locator('#liveMoveLast').click()
                guard = page.locator('#liveMoveGuard')
                guard.wait_for(state='visible')
                self.assertIn('managed by react', guard.inner_text())
                self.assertIn('Rejected', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(page.locator('#liveMoveForce').inner_text().strip(), 'Move anyway')
                self.assertNotIn('force', self.moves(frame)[-1])
                page.locator('#liveMoveForce').click()
                self.wait_list(page, ['card.a', 'card.c', 'card.d', 'card.b'])
                forced = self.moves(frame)[-1]
                self.assertEqual((forced['targetId'], forced['to'], forced['strategy'], forced['force']), ('card.b', {'index': 3}, 'dom', True))
                self.assertEqual(self.dom(frame), ['card.a', 'card.c', 'card.d', 'card.b'])
                self.assertFalse(guard.is_visible())
                # Other guards: reason shown, never a force button (and force is never sent).
                frame.evaluate('window.fake.framework = {}')
                frame.evaluate("""window.fake.guards = {'card.c': {guard: 'form-owner', overridable: false,
                    message: 'Moving this control would take it out of its form.'}}""")
                self.select(page, frame, 'card.c')
                page.locator('#liveMovePrev').click()
                guard.wait_for(state='visible')
                self.assertIn('take it out of its form', guard.inner_text())
                self.assertIn('form-owner', guard.inner_text())
                self.assertEqual(page.locator('#liveMoveForce').count(), 0)
                self.assertEqual(self.dom(frame), ['card.a', 'card.c', 'card.d', 'card.b'])
                self.assertEqual(len([m for m in self.moves(frame) if m.get('force')]), 1)
                # Even an overridable non-framework guard has no Move anyway.
                frame.evaluate("""window.fake.guards = {'card.c': {guard: 'label-reference', overridable: true,
                    message: 'A label would lose its control.'}}""")
                page.locator('#liveMovePrev').click()
                page.wait_for_function('() => /label would lose/.test(document.querySelector("#liveMoveGuard").textContent)')
                self.assertEqual(page.locator('#liveMoveForce').count(), 0)
                # The content-model guard (Addendum 3) is never overridable, whatever the target says.
                frame.evaluate("""window.fake.guards = {'card.c': {guard: 'content-model', overridable: true,
                    message: 'A block element cannot go inside a paragraph.'}}""")
                page.locator('#liveMovePrev').click()
                page.wait_for_function('() => /cannot go inside a paragraph/.test(document.querySelector("#liveMoveGuard").textContent)')
                self.assertIn('content-model', guard.inner_text())
                self.assertEqual(page.locator('#liveMoveForce').count(), 0)
                # A new selection clears the explanation.
                self.select(page, frame, 'card.a')
                self.assertFalse(guard.is_visible())
                self.assertEqual(errors, [])

    def test_runtime_warnings_reach_the_status_area_and_code_panel_as_text(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.assertFalse(page.locator('#bridgeWarning').is_visible())
                self.select(page, frame, 'hero.title')
                frame.evaluate('window.fake.warnNext = "TypeError: app exploded after the change"')
                self.set_value(page, '#liveFontSize', 50)
                page.locator('#bridgeWarning').wait_for(state='visible')
                self.assertIn('app exploded after the change', page.locator('#bridgeWarning').inner_text())
                self.assertIn('app exploded after the change', page.locator('#liveCodeWarnings').inner_text())
                # Hostile text stays text; a wrong session is ignored.
                frame.evaluate('window.fake.warn("<img src=x onerror=\\"window.__xss=1\\">boom", "hero.title", "r1")')
                page.wait_for_function('() => /boom/.test(document.querySelector("#liveCodeWarnings").textContent)')
                self.assertEqual(page.locator('#bridgeWarning img, #liveCodeWarnings img').count(), 0)
                self.assertEqual(page.evaluate('window.__xss'), None)
                frame.evaluate("""parent.postMessage({type: "design:warning", protocolVersion: 1, sessionId: "fks-wrong",
                    kind: "runtime-error", message: "forged warning"}, "*")""")
                page.wait_for_timeout(250)
                self.assertNotIn('forged warning', page.locator('#liveCodeWarnings').inner_text())
                frame.evaluate('window.fake.warn("x".repeat(900))')
                page.wait_for_function('() => document.querySelector("#liveCodeWarnings").textContent.includes("xxxxxxxx")')
                self.assertLessEqual(len(max(page.locator('#liveCodeWarnings li').all_inner_texts(), key=len)), 340)
                self.assertEqual(errors, [])

    def test_html_tab_shows_structure_and_css_tab_points_to_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.c')
                page.locator('#liveMoveFirst').click()
                self.wait_list(page, ['card.c', 'card.a', 'card.b', 'card.d'])
                html = self.code(page, 'Html')
                self.assertNotIn('No text changes yet.', html)
                self.assertIn('Structure: Cards', html)
                self.assertIn('Card C, Card A, Card B, Card D', html)
                self.assertIn('data-design-id="cards"', html)
                self.assertRegex(html, r'(?s)card\.c.*card\.a.*card\.b.*card\.d')
                self.assertNotIn('style=', html)
                css = self.code(page, 'Css')
                self.assertRegex(css, r'(?i)structural.*HTML tab')
                self.assertNotIn('@import', css)
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '1', 'one changed container')
                # Reset puts the structure back and the block disappears.
                page.locator('#liveResetTarget').click()
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.code(page, 'Html'), '<!-- No text changes yet. -->')
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertNotRegex(self.code(page, 'Css'), r'(?i)structural')
                self.assertEqual(errors, [])

    def test_css_order_moves_persist_in_live_json_and_reapply_after_a_reload(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.c')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveFirst').click()
                self.wait_list(page, ['card.c', 'card.a', 'card.b', 'card.d'])
                live = self.export(page)['live']
                self.assertEqual(live['overrides'], {'card.c': {'order': 0}, 'card.a': {'order': 1},
                                                     'card.b': {'order': 2}, 'card.d': {'order': 3}})
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 11)
                self.assertEqual(frame.evaluate('window.fake.visualOrder("cards")'), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.moves(frame), [], 'never auto-applied')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('JSON.stringify(window.fake.visualOrder("cards")) === JSON.stringify(["card.c","card.a","card.b","card.d"])')
                self.assertTrue(all(m['strategy'] == 'css-order' for m in self.moves(frame)))
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                # Reset clears the order overrides (the whole group) and the CSS.
                self.select(page, frame, 'card.c')
                page.locator('#liveResetTarget').click()
                page.wait_for_function('() => document.querySelector("#liveChangeCount").textContent === "0"')
                self.assertNotIn('order:', self.code(page, 'Css'))
                self.assertEqual(errors, [])

    def test_reapply_replays_font_stylesheets_and_clears_stale_orders(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                page.locator('#liveFontFamily').select_option(label='Fraunces')
                self.wait_badge(page, r'^Live · rev 1$')
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [FREE_URLS['fraunces']])
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 5)
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.ledger().imports.length === 1')
                patch = self.updates(frame)[-1]['patch']
                self.assertEqual(patch['fontStylesheet'], FREE_URLS['fraunces'])
                self.assertIn('"Fraunces"', patch['fontFamily'])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [FREE_URLS['fraunces']])
                self.assertEqual(errors, [])

    def test_reapply_of_a_non_library_family_releases_the_stylesheet(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, query=False)
                page.locator('#modeComposer').click()
                doc = self.export(page)
                doc['live'] = {'target': FAKE, 'revision': 1, 'overrides': {'hero.lead': {'fontFamily': 'Georgia, serif'}}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                self.connect(page)
                frame = self.wait_ready(page, 5)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                page.locator('#liveReapply').click()
                frame.wait_for_function('window.__received.some(i => i.data && i.data.type === "design:update")')
                patch = self.updates(frame)[-1]['patch']
                self.assertEqual(patch['fontFamily'], 'Georgia, serif')
                self.assertIn('fontStylesheet', patch)
                self.assertIsNone(patch['fontStylesheet'])
                self.assertEqual(errors, [])

    def test_reapply_clears_a_target_css_order_that_studio_no_longer_saves(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.c')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveFirst').click()
                self.wait_list(page, ['card.c', 'card.a', 'card.b', 'card.d'])
                doc = self.export(page)
                # Saved JSON without any order, but with other overrides so the conflict stays visible.
                doc['live']['overrides'] = {'hero.title': {'fontSize': 40}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.assertEqual(frame.evaluate('window.fake.visualOrder("cards")'), ['card.c', 'card.a', 'card.b', 'card.d'])
                page.locator('#liveReapply').click()
                frame.wait_for_function('JSON.stringify(window.fake.visualOrder("cards")) === JSON.stringify(["card.a","card.b","card.c","card.d"])')
                frame.wait_for_function('window.fake.styleOf("hero.title").fontSize === "40px"')
                self.assertEqual(self.export(page)['live']['overrides'], {'hero.title': {'fontSize': 40}})
                self.assertNotIn('order:', self.code(page, 'Css'))
                self.assertEqual(errors, [])

    def stale_order_setup(self, engine, sync=None, dom_move=False, target_id='card.c', clicks=('#liveMoveFirst',)):
        """Target holds a CSS order (and optionally a DOM move) that the imported saved JSON does not."""
        page, errors = self.open(engine, target=ARRANGE, sync=sync)
        frame = self.wait_ready(page, 11)
        self.select(page, frame, target_id)
        revision = 0
        if dom_move:
            page.locator('#liveMoveLast').click()
            revision += 1
            self.wait_badge(page, rf'^Live · rev {revision}$')
        page.locator('#liveMoveStrategyCss').click()
        for selector in clicks:
            page.locator(selector).click()
            revision += 1
            self.wait_badge(page, rf'^Live · rev {revision}$')
        return page, errors, frame

    def test_reapply_is_transactional_when_the_follow_up_is_rejected(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.stale_order_setup(engine, sync=True)
                doc = self.export(page)
                saved = {'card.c': {'fontSize': 21}}
                doc['live']['overrides'] = saved
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.locator('#liveCodeAutoSync').check()
                before = len(self.puts)
                frame.evaluate('window.fake.rejectNext = "unsupported-value"')
                page.locator('#liveReapply').click()
                self.wait_badge(page, r'^Rejected: unsupported-value$')
                page.wait_for_timeout(700)
                # Saved state is intact, the banner stays with a visible error, and no file shrank.
                self.assertEqual(self.export(page)['live']['overrides'], saved)
                self.assertTrue(banner.is_visible())
                self.assertIn('Reapply stopped', page.locator('#liveReconnectText').inner_text())
                for put in self.puts[before:]:
                    self.assertIn('font-size: 21px', put['body'])
                self.assertIn('font-size: 21px', self.code(page, 'Css'))
                # Retrying succeeds and then the file may be written.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.styleOf("card.c").fontSize === "21px"')
                page.wait_for_function('(n) => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)', arg=before)
                self.assertIn('font-size: 21px', self.puts[-1]['body'])
                self.assertEqual(self.export(page)['live']['overrides'], saved)
                self.assertEqual(errors, [])

    def test_reapply_states_that_it_resets_a_dom_moved_arrangement(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.stale_order_setup(engine, dom_move=True)
                original = ['card.a', 'card.b', 'card.c', 'card.d']
                doc = self.export(page)
                doc['live']['overrides'] = {'hero.title': {'fontSize': 40}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                text = banner.inner_text()
                self.assertRegex(text, r'(?i)reset.*arrangement')
                self.assertRegex(text, r'(?i)DOM')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('(o) => JSON.stringify(window.fake.domOrder("cards")) === JSON.stringify(o)', arg=original)
                self.assertEqual(frame.evaluate('window.fake.visualOrder("cards")'), original)
                self.assertEqual(self.export(page)['live']['overrides'], {'hero.title': {'fontSize': 40}})
                self.assertEqual(errors, [])

    def test_reapply_replays_a_partial_saved_order_group_after_the_reset(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.stale_order_setup(engine, target_id='card.a', clicks=('#liveMoveNext', '#liveMovePrev'))
                # Target: a0 b1 c2 d3 (CSS order). Saved: only card.a's order (already equal) plus an override on card.c,
                # so card.c's order is stale; resetting it clears the whole group.
                doc = self.export(page)
                doc['live']['overrides'] = {'card.a': {'order': 0}, 'card.c': {'fontSize': 30}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.styleOf("card.c").fontSize === "30px"')
                frame.wait_for_function('window.fake.ledger().targets.some(t => t.targetId === "card.a" && t.declarations.order === "0")')
                saved = self.export(page)['live']['overrides']
                self.assertEqual(saved['card.a'], {'order': 0})
                self.assertEqual(saved['card.c']['fontSize'], 30)
                self.assertEqual(errors, [])

    def test_bulk_manifests_and_arrangement_only_targets(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{ARRANGE}&only=1&bulk=1')
                frame = self.wait_ready(page, 11)
                # Sibling-only registrations are not editing targets: not counted, not listed.
                names = page.locator('.live-target-list button span').all_inner_texts()
                self.assertEqual(len(names), 11)
                self.assertNotIn('Side Z', names)
                # Bulk manifests carry no siblings; the selection brings the full list.
                self.select(page, frame, 'card.b')
                self.wait_list(page, ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertGreater(page.locator('#liveMoveContainer option').count(), 0)
                # ...and the sibling list keeps the arrangement-only element.
                self.select(page, frame, 'side.x')
                self.wait_list(page, ['side.x', 'side.y', 'side.z'])
                self.assertIn('Side Z', page.locator('#liveSiblingList').inner_text())
                # A bulk design:targets drops the full list; Studio asks for the selection again.
                selects = len(self.received(frame, 'design:select'))
                frame.evaluate('window.fake.emitTargets(["card.b", "side.x"])')
                frame.wait_for_function('(n) => window.__received.filter(i => i.data && i.data.type === "design:select").length > n', arg=selects)
                self.wait_list(page, ['side.x', 'side.y', 'side.z'])
                page.locator('#liveMoveLast').click()
                self.wait_list(page, ['side.y', 'side.z', 'side.x'])
                self.assertEqual(self.moves(frame)[-1]['to'], {'index': 2})
                # Bulk manifests omit both keys entirely (Addendum 3 amendment); the stale list is never trusted.
                self.assertTrue(frame.evaluate('window.fake.bulkOmitsKeys()'))
                self.assertEqual(errors, [])

    def test_move_retries_a_revision_conflict_once(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.a')
                frame.evaluate('window.fake.bumpRevision()')
                page.locator('#liveMoveNext').click()
                self.wait_list(page, ['card.b', 'card.a', 'card.c', 'card.d'])
                moves = self.moves(frame)
                self.assertEqual(len(moves), 2)
                self.assertEqual(moves[1]['baseRevision'], moves[0]['baseRevision'] + 1)
                self.assertNotEqual(moves[0]['requestId'], moves[1]['requestId'])
                self.assertEqual(errors, [])

    def test_narrow_layout_with_arrange_guard_and_popout_has_no_overflow(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine, viewport={'width': 390, 'height': 844})
                frame.evaluate('window.fake.framework = {cards: "react"}')
                self.select(page, frame, 'card.b')
                page.locator('#liveMoveStrategyDom').click()
                page.locator('#liveMoveLast').click()
                page.locator('#liveMoveGuard').wait_for(state='visible')
                frame.evaluate('window.fake.warn("TypeError: something quite long happened in the application code path", "card.b")')
                page.locator('#bridgeWarning').wait_for(state='visible')
                page.wait_for_timeout(250)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
                for selector in ('#liveArrange', '#liveSiblingList', '#liveMoveContainer', '#liveMoveInto', '#liveMoveFirst',
                                 '#liveMoveLast', '#liveMoveStrategyCss', '#liveMoveForce', '#liveMoveGuard', '#bridgeWarning',
                                 '#bridgePopOut', '#liveCodeWarnings'):
                    box = page.locator(selector).bounding_box()
                    self.assertIsNotNone(box, selector)
                    self.assertLessEqual(box['x'] + box['width'], 390.5, selector)
                self.assertEqual(self.duplicates(page), [])
                self.assertEqual(errors, [])


class StudioPopoutTests(ArrangeCase):
    def instrument_open(self, page, block=False):
        page.evaluate("""(block) => { window.__opens = []; const original = window.open.bind(window);
            window.open = (...args) => { window.__opens.push(args); return block ? null : original(...args); }; }""", block)

    def assert_window_open_call(self, page, url, calls=1):
        """The pop-out must ask for a separate window: a named target plus `popup` window features."""
        opens = page.evaluate('window.__opens')
        self.assertEqual(len(opens), calls, opens)
        self.assertEqual(opens[-1][:2], [url, 'fontkit-target'])
        self.assertEqual(len(opens[-1]), 3, 'window.open needs a features string, or browsers open a tab')
        features = dict(part.split('=') for part in opens[-1][2].split(','))
        self.assertEqual(features['popup'], 'yes')
        for key in ('width', 'height', 'left', 'top'):
            self.assertRegex(features[key], r'^\d+$', key)
        self.assertGreaterEqual(int(features['width']), 600)
        self.assertGreaterEqual(int(features['height']), 400)

    def pop_out(self, page):
        with page.expect_popup() as info:
            page.locator('#bridgePopOut').click()
        popup = info.value
        popup.wait_for_function('Boolean(window.fake)')
        return popup

    def modes(self, popup):
        return [i['data'] for i in popup.evaluate('window.__received')
                if isinstance(i['data'], dict) and i['data'].get('type') == 'design:mode']

    def test_pop_out_opens_the_named_window_and_the_inspector_edits_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                self.instrument_open(page)
                popup = self.pop_out(page)
                self.assert_window_open_call(page, FAKE)
                self.assertEqual(popup.evaluate('window.name'), 'fontkit-target')
                self.assertEqual(popup.url, FAKE)
                self.wait_badge(page, r'^Connected \(5 targets\)$')
                popup.wait_for_function('window.fake.overlay === true')
                modes = self.modes(popup)
                self.assertTrue(modes and modes[-1]['overlay'] is True and modes[-1]['mode'] == 'select', modes)
                # The iframe and its Studio overlay give way to a docked placeholder.
                placeholder = page.locator('#bridgePopoutPlaceholder')
                placeholder.wait_for(state='visible')
                self.assertTrue(page.locator('#bridgeFocusPopout').is_visible())
                self.assertTrue(page.locator('#bridgeDock').is_visible())
                self.assertFalse(page.locator('#targetAppFrame').is_visible())
                # Selecting in the pop-out edits through the same inspector; the popup's own page changes.
                popup.evaluate('window.fake.select("hero.title")')
                page.wait_for_function('() => document.querySelector("#liveTargetName") && document.querySelector("#liveTargetName").dataset.targetId === "hero.title"')
                self.assertFalse(page.locator('#bridgeOverlaySelected').is_visible(), 'the pop-out draws its own outline')
                self.set_value(page, '#liveFontSize', 50)
                popup.wait_for_function('getComputedStyle(document.querySelector("h1")).fontSize === "50px"')
                self.wait_badge(page, r'^Live · rev 1$')
                self.assertIn('font-size: 50px !important;', self.code(page, 'Css'))
                # Mode toggles keep overlay:true while popped out.
                page.locator('#bridgeModeInteract').click()
                popup.wait_for_function('window.fake.mode === "interact"')
                self.assertEqual((self.modes(popup)[-1]['mode'], self.modes(popup)[-1]['overlay']), ('interact', True))
                self.assertEqual(errors, [])

    def test_iframe_mode_sends_overlay_false_and_dock_returns_to_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                frame = self.wait_ready(page, 5)
                page.locator('#bridgeModeInteract').click()
                frame.wait_for_function('window.fake.mode === "interact"')
                self.assertIs(self.received(frame, 'design:mode')[-1]['data']['overlay'], False)
                page.locator('#bridgeModeSelect').click()
                popup = self.pop_out(page)
                self.wait_badge(page, r'^Connected \(5 targets\)$')
                popup.wait_for_function('window.fake.overlay === true')
                with popup.expect_event('close'):
                    page.locator('#bridgeDock').click()
                page.locator('#bridgePopoutPlaceholder').wait_for(state='hidden')
                self.assertTrue(page.locator('#targetAppFrame').is_visible())
                frame = self.wait_ready(page, 5)
                self.assertFalse(frame.evaluate('window.fake.overlay'))
                self.assertEqual(page.locator('#bridgeModeSelect').get_attribute('aria-pressed'), 'true')
                self.assertEqual(errors, [])

    def test_closing_the_popup_reports_disconnected_and_dock_recovers(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                popup = self.pop_out(page)
                self.wait_badge(page, r'^Connected \(5 targets\)$')
                popup.close()
                self.wait_badge(page, r'^Disconnected \(window closed\)$', timeout=6000)
                self.assertTrue(page.locator('#bridgePopoutPlaceholder').is_visible())
                page.locator('#bridgeDock').click()
                page.locator('#bridgePopoutPlaceholder').wait_for(state='hidden')
                self.wait_ready(page, 5)
                self.assertEqual(errors, [])

    def test_pop_out_validates_the_url_before_window_open(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                self.instrument_open(page)
                opened = []
                page.context.on('page', lambda new: opened.append(new.url))
                for probe in ('javascript:parent.__pwned=1;void 0', 'data:text/html,<script>1</script>', 'file:///etc/passwd',
                              'blob:http://studio.test/x', 'ftp://target.test/'):
                    page.locator('#targetAppUrl').fill(probe)
                    page.locator('#bridgePopOut').click()
                    self.wait_badge(page, r'^Invalid target URL$')
                    self.assertEqual(page.evaluate('window.__opens'), [], probe)
                page.wait_for_timeout(300)
                self.assertEqual(opened, [])
                self.assertFalse(page.locator('#bridgePopoutPlaceholder').is_visible())
                self.assertEqual(page.evaluate('window.__pwned'), None)
                # Studio itself cannot be popped out.
                page.locator('#targetAppUrl').fill(APP)
                page.locator('#bridgePopOut').click()
                self.wait_badge(page, r'^Recursion blocked$')
                self.assertEqual(page.evaluate('window.__opens'), [])
                self.assertEqual(errors, [])

    def test_blocked_popup_keeps_the_iframe(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                self.instrument_open(page, block=True)
                page.locator('#bridgePopOut').click()
                page.wait_for_function('() => /pop-?up/i.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assert_window_open_call(page, FAKE)
                self.assertTrue(page.locator('#targetAppFrame').is_visible())
                self.assertFalse(page.locator('#bridgePopoutPlaceholder').is_visible())
                self.assertEqual(errors, [])

    def test_pop_out_accepts_only_the_popup_at_the_expected_origin(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_ready(page, 5)
                popup = self.pop_out(page)
                self.wait_badge(page, r'^Connected \(5 targets\)$')
                popup.wait_for_function('window.fake.overlay === true')
                hellos = 'window.__received.filter(i => i.data && i.data.type === "design:hello").length'
                before = popup.evaluate(hellos)
                # A second window opened by Studio is not the expected source.
                with page.context.expect_page() as info:
                    page.evaluate("(url) => { window.open(url, 'evilwin'); }", SPOOFER)
                evil = info.value
                evil.wait_for_function('typeof window.spoofOpener === "function"')
                evil.evaluate('window.spoofOpener({type: "design:bridge-ready", protocolVersion: 1})')
                evil.evaluate('window.spoofOpener({type: "design:applied", protocolVersion: 1, sessionId: "fks-x", requestId: "r", revision: 99, targetId: "global", canonicalPatch: {}})')
                page.wait_for_timeout(300)
                self.assertEqual(popup.evaluate(hellos), before)
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Connected (5 targets)')
                # The popup navigating to a foreign origin loses its authority too.
                popup.goto(SPOOFER)
                popup.wait_for_function('typeof window.spoofOpener === "function"')
                popup.evaluate('window.spoofOpener({type: "design:applied", protocolVersion: 1, sessionId: "fks-x", requestId: "r", revision: 99, targetId: "global", canonicalPatch: {}})')
                popup.evaluate('window.spoofOpener({type: "design:bridge-ready", protocolVersion: 1})')
                page.wait_for_timeout(300)
                self.assertNotIn('99', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(errors, [])


class StudioFreeFontTests(LiveCase):
    def open_fonts(self, engine, block=False, viewport=None):
        context = self.context(engine, viewport=viewport)
        requested = []
        if not block:
            def stylesheet(route):
                requested.append(route.request.url)
                route.fulfill(status=200, content_type='text/css', body='/* stub */')
            context.route('https://fonts.googleapis.com/**', stylesheet)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(APP)
        return page, errors, requested

    def font_links(self, page):
        return page.evaluate('[...document.querySelectorAll("link[data-studio-font]")].map(el => el.href)')

    def test_defaults_are_free_and_adobe_is_an_opt_in_with_an_empty_field(self):
        source = HTML.read_text(encoding='utf-8')
        self.assertNotIn('cqu4tvx', source)
        self.assertNotIn('YOUR_KIT_ID', source)
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                page.locator('#modeComposer').click()
                self.assertEqual(page.locator('#composerKitIds').input_value(), '')
                self.assertEqual(page.locator('#kitPreset').input_value(), 'google')
                labels = page.locator('#kitPreset option').all_inner_texts()
                self.assertTrue(any('Google' in label for label in labels), labels)
                self.assertTrue(any('Bring your own Adobe kit' in label for label in labels), labels)
                self.assertFalse(any('cqu4tvx' in label for label in labels))
                self.assertEqual(page.evaluate('document.querySelectorAll("link[href*=typekit]").length'), 0)
                self.assertEqual(page.locator('#kitId').input_value(), '')
                exported = self.export(page)
                self.assertEqual(exported['kitIds'], [])
                self.assertNotIn('cqu4tvx', json.dumps(exported))
                # Choosing the Adobe preset prefills nothing and loads nothing.
                page.locator('#kitPreset').select_option('adobe')
                self.assertEqual(page.locator('#composerKitIds').input_value(), '')
                self.assertEqual(page.evaluate('document.querySelectorAll("link[href*=typekit]").length'), 0)
                page.locator('#composerKitIds').fill('abc123')
                page.locator('#loadComposerKits').click()
                self.assertEqual(page.evaluate('[...document.querySelectorAll("link[data-composer-kit]")].map(el => el.href)'),
                                 ['https://use.typekit.net/abc123.css'])
                self.assertEqual(errors, [])

    def test_first_load_is_silent_and_free_fonts_load_only_after_the_user_asks(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                external = []
                page.context.on('request', lambda request: external.append(request.url)
                                if not request.url.startswith((STUDIO, 'data:', 'blob:', 'about:')) else None)
                # First load: Library, then Composer, then a revisit of the Composer, all in fallback stacks.
                page.goto(APP)
                page.locator('#grid .card').first.scroll_into_view_if_needed()
                page.locator('#modeComposer').click()
                page.wait_for_function('() => document.querySelectorAll("#composerCanvas .flow-slot").length > 0')
                page.wait_for_timeout(300)  # proves nothing more arrives: a negative assertion
                self.assertEqual(external, [])
                self.assertEqual(requested, [])
                self.assertEqual(self.font_links(page), [])
                # The hints say what will happen before anything does.
                self.assertIn('fallback', page.locator('#freeFontStatus').inner_text())
                self.assertIn('Google Fonts', page.locator('#libraryFontHint').inner_text())
                self.assertIn('fallback', page.locator('#composerFontHint').inner_text())
                self.assertIn('Google Fonts', page.locator('#composerFontHint').inner_text())
                # The user asks: the families the page wanted, and the rest, now load.
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                self.assertEqual(sorted(set(requested)), sorted(FREE_URLS.values()))
                self.assertIn('Free fonts are on', page.locator('#composerFontHint').inner_text())
                # The choice is remembered per browser: a later visit loads without a click.
                requested.clear()
                page.goto(APP)
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length > 0')
                self.assertTrue(requested and set(requested) <= set(FREE_URLS.values()))
                self.assertIn('scroll into view', page.locator('#freeFontStatus').inner_text())
                self.assertEqual(errors, [])

    def test_choosing_a_family_in_the_live_inspector_counts_as_asking(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                requested = []
                def stylesheet(route):
                    requested.append(route.request.url)
                    route.fulfill(status=200, content_type='text/css', body='/* stub */')
                context.route('https://fonts.googleapis.com/**', stylesheet)
                page = context.new_page()
                page.goto(f'{APP}?target={quote(FAKE, safe="")}')
                self.wait_connected(page)
                self.assertEqual(requested, [], 'connecting a target asks for nothing')
                self.select(page, self.frame(page), 'hero.title')
                page.locator('#liveFontFamily').select_option(label='Fraunces')
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length > 0')
                self.assertIn(FREE_URLS['fraunces'], requested)
                page.goto(APP)  # remembered: the next visit does not need to ask again
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length > 0')

    def test_the_hints_only_promise_what_is_true_where_it_is_true(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                page.locator('#modeComposer').click()
                hint = page.locator('#composerFontHint').inner_text()
                self.assertNotIn('inspector', hint, 'the Composer hint must not describe an inspector it cannot promise')
                # The slot inspector does not load anything: it says so, beside the control.
                page.locator('#composerCanvas .flow-slot').nth(1).click(position={'x': 3, 'y': 3})
                note = page.locator('#slotInspector [data-fallback-note]')
                self.assertEqual(note.count(), 1)
                self.assertIn('fallback', note.inner_text())
                self.assertEqual(requested, [])
                # After the user asks, the note goes away: the families are loading.
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                self.assertEqual(page.locator('#slotInspector [data-fallback-note]').count(), 0)
                self.assertEqual(errors, [])

    def test_the_live_target_inspector_says_choosing_a_family_loads_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                context.route('https://fonts.googleapis.com/**',
                              lambda route: route.fulfill(status=200, content_type='text/css', body='/* stub */'))
                page = context.new_page()
                page.goto(f'{APP}?target={quote(FAKE, safe="")}')
                self.wait_connected(page)
                self.select(page, self.frame(page), 'hero.title')
                note = page.locator('#slotInspector [data-load-note]')
                self.assertEqual(note.count(), 1)
                self.assertIn('Google Fonts', note.inner_text())

    def test_switching_the_kit_preset_to_free_google_fonts_counts_as_asking(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                page.locator('#modeComposer').click()
                page.locator('#kitPreset').select_option('adobe')
                page.wait_for_timeout(200)  # proves nothing more arrives: a negative assertion
                self.assertEqual(requested, [], 'the Adobe preset asks Google for nothing')
                page.locator('#kitPreset').select_option('google')
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                self.assertEqual(sorted(set(requested)), sorted(FREE_URLS.values()))
                self.assertEqual(page.evaluate('localStorage.getItem("fontkit-free-fonts")'), 'yes')
                self.assertEqual(errors, [])

    def test_blocked_storage_still_loads_on_request_and_asks_again_next_visit(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                requested = []

                def stylesheet(route):
                    requested.append(route.request.url)
                    route.fulfill(status=200, content_type='text/css', body='/* stub */')
                context.route('https://fonts.googleapis.com/**', stylesheet)
                # Browsers that block site data throw from localStorage; Studio must not.
                context.add_init_script("""Object.defineProperty(window, 'localStorage', {
                    get() { throw new DOMException('blocked', 'SecurityError'); } });""")
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(APP)
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                self.assertEqual(sorted(set(requested)), sorted(FREE_URLS.values()))
                requested.clear()
                page.goto(APP)
                page.wait_for_timeout(300)  # proves nothing more arrives: a negative assertion
                self.assertEqual(requested, [], 'with storage blocked, consent cannot be remembered')
                self.assertEqual(errors, [])

    def test_library_has_sixteen_free_families_loaded_after_the_user_asks(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                cards = page.locator('#grid .card')
                self.assertEqual(cards.count(), 16)
                names = page.locator('#grid .card .family').all_inner_texts()
                self.assertEqual(sorted(names), sorted(name for name, _ in FREE_FAMILIES.values()))
                tags = set(page.locator('#filters .filter').all_inner_texts())
                self.assertTrue({'serif', 'sans', 'mono', 'display', 'variable'} <= tags, tags)
                variable = page.locator('#grid .card .var-controls').count()
                self.assertGreaterEqual(variable, 3)
                axes = set(page.locator('#grid .card .var-control label span:first-child').all_inner_texts())
                self.assertTrue({'wght', 'opsz'} <= axes, axes)
                # Nothing loads until the user asks.
                self.assertEqual(self.font_links(page), [])
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                links = self.font_links(page)
                self.assertEqual(sorted(links), sorted(FREE_URLS.values()))
                for href in links:
                    self.assertRegex(href, GOOGLE_RE)
                # Pressing it again does not duplicate.
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_timeout(150)
                self.assertEqual(len(self.font_links(page)), 16)
                self.assertEqual(sorted(set(requested)), sorted(FREE_URLS.values()))
                self.assertEqual(errors, [])

    def test_composer_waits_for_the_user_then_load_free_fonts_loads_all(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, requested = self.open_fonts(engine)
                page.locator('#modeComposer').click()
                page.locator('#composerCanvas .flow-slot').nth(1).click(position={'x': 3, 'y': 3})
                page.locator('#slotInspector [data-bind="family"]').select_option('bebas-neue')
                page.wait_for_timeout(200)  # proves nothing more arrives: a negative assertion
                self.assertEqual(self.font_links(page), [], 'picking a slot family in the Composer is not asking')
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font]").length === 16')
                self.assertEqual(sorted(self.font_links(page)), sorted(FREE_URLS.values()))
                page.wait_for_function('() => /Loaded 16\\/16/.test(document.querySelector("#composerStatus").textContent)')
                self.assertEqual(errors, [])

    def test_offline_loading_never_hangs_or_throws(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, _ = self.open_fonts(engine, block=True)
                page.locator('#modeComposer').click()
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => /could not|offline|unavailable/i.test(document.querySelector("#composerStatus").textContent)', timeout=6000)
                page.locator('#modeLibrary').click()
                page.locator('#loadFreeFontsLibrary').click()
                page.locator('#sampleText').fill('Still responsive offline')
                self.assertTrue(all(t == 'Still responsive offline' for t in page.locator('.big-sample').all_text_contents()))
                self.assertEqual(page.evaluate('document.querySelectorAll("link[data-studio-font]").length'), 16)
                self.assertEqual(errors, [])

    def test_composition_presets_use_free_families_and_legacy_keys_still_import(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, _ = self.open_fonts(engine)
                page.locator('#modeComposer').click()
                for preset in ('rowdemo', 'blank', 'asteria'):
                    page.locator('#compositionPreset').select_option(preset)
                    page.locator('#applyPreset').click()
                    page.wait_for_function('(name) => document.querySelector("#composerStatus").textContent.startsWith(name)',
                                           arg={'rowdemo': 'Editorial', 'blank': 'Blank', 'asteria': 'Asteria'}[preset])
                    families = set()
                    def walk(slots):
                        for slot in slots:
                            if slot.get('type') == 'row':
                                walk(slot['children'])
                            elif slot.get('type') == 'text':
                                families.add(slot['family'])
                    walk(self.export(page)['composition']['slots'])
                    self.assertTrue(families and families <= set(FREE_FAMILIES), (preset, families))
                    page.locator('#exportCss').click()
                    css = page.locator('#exportDialogText').input_value()
                    page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
                    self.assertRegex(css, r'--font-[a-z0-9-]+: "[A-Za-z0-9 ]+", [a-z-]+;')
                    for adobe in ('Gotham', 'Daith', 'Ella', 'Orpheus', 'Sentinel', 'gotham', 'daith'):
                        self.assertNotIn(adobe, css)
                # Exports from earlier versions carry Adobe family keys: they map to a free look-alike, not fonts[0].
                legacy = {'version': '0.1.0', 'composition': {'slots': [
                    {'type': 'text', 'family': 'gotham'}, {'type': 'text', 'family': 'daith-vf'},
                    {'type': 'text', 'family': 'azo-mono'}, {'type': 'text', 'family': 'unknown-family'}]}}
                self.assertIn('Composition imported.', self.import_document(page, legacy))
                imported = [slot['family'] for slot in self.export(page)['composition']['slots']]
                self.assertEqual(imported[:3], ['work-sans', 'fraunces', 'ibm-plex-mono'])
                self.assertIn(imported[3], FREE_FAMILIES)
                self.assertEqual(errors, [])

    def test_live_family_selection_sends_font_stylesheet_and_css_starts_with_import(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                context.route('https://fonts.googleapis.com/**',
                              lambda route: route.fulfill(status=200, content_type='text/css', body='/* stub */'))
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{APP}?target={quote(FAKE, safe="")}')
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                family = page.locator('#liveFontFamily')
                family.select_option(label='Fraunces')
                self.wait_live(page)
                update = self.updates(frame)[-1]
                self.assertEqual(update['targetId'], 'hero.title')
                self.assertEqual(update['patch']['fontStylesheet'], FREE_URLS['fraunces'])
                self.assertIn('"Fraunces"', update['patch']['fontFamily'])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [FREE_URLS['fraunces']])
                # Studio itself loads the stylesheet so its specimens render the family.
                self.assertIn(FREE_URLS['fraunces'], self.font_links(page))
                css = self.code(page, 'Css')
                self.assertTrue(css.startswith(f'@import url("{FREE_URLS["fraunces"]}");\n'), css)
                self.assertIn('font-family: "Fraunces"', css)
                # A second target with another family: both imports, ordered. Imports are released when no target uses them.
                self.select(page, frame, 'hero.lead')
                page.locator('#liveFontFamily').select_option(label='Inter')
                page.wait_for_function('() => /rev 2$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [FREE_URLS['fraunces'], FREE_URLS['inter']])
                lines = self.code(page, 'Css').split('\n')
                self.assertEqual(lines[:2], [f'@import url("{FREE_URLS["fraunces"]}");', f'@import url("{FREE_URLS["inter"]}");'])
                # Choosing the page's own (non-library) family releases the stylesheet: fontStylesheet null.
                page.locator('#liveFontFamily').select_option(index=0)
                page.wait_for_function('() => /rev 3$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                last = self.updates(frame)[-1]['patch']
                self.assertIn('fontStylesheet', last)
                self.assertIsNone(last['fontStylesheet'])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [FREE_URLS['fraunces']])
                # Other properties never carry a stylesheet.
                page.locator('#liveFontSize').fill('18')
                self.wait_badge(page, r'^Live · rev 4$')
                self.assertNotIn('fontStylesheet', self.updates(frame)[-1]['patch'])
                self.assertEqual(errors, [])


class StudioSavedTokensTests(LiveCase):
    TOKENS = {'--font-display': '"Fraunces", serif', '--font-sans': '"Inter", sans-serif'}

    def test_saved_composition_tokens_round_trip_through_the_live_json(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertNotIn('live', self.export(page))
                page.locator('#btnSyncToApp').click()
                self.wait_badge(page, r'^Live · rev 1$')
                exported = self.export(page)
                tokens = exported['live']['tokens']
                self.assertIn('--font-display', tokens)
                self.assertEqual(tokens, frame.evaluate('window.fake.ledger().tokens'))
                self.assertEqual(exported['live']['overrides'], {})
                # A new Studio session (reload) imports them as saved state and never applies them silently.
                page2, errors2 = self.open(engine, query=False)
                page2.locator('#modeComposer').click()
                self.assertIn('Composition imported.', self.import_document(page2, exported))
                self.assertEqual(self.export(page2)['live']['tokens'], tokens)
                self.connect(page2)
                self.wait_connected(page2)
                banner = page2.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame2 = self.frame(page2)
                self.assertEqual(self.updates(frame2), [])
                self.assertEqual(frame2.evaluate('window.fake.ledger().tokens'), {})
                self.assertIn('--font-display', self.code(page2, 'Css'))
                page2.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame2.wait_for_function('Object.keys(window.fake.ledger().tokens).length > 0')
                self.assertEqual(frame2.evaluate('window.fake.ledger().tokens'), tokens)
                self.assertEqual(errors + errors2, [])

    def test_invalid_saved_tokens_reject_the_whole_import(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, query=False)
                page.locator('#modeComposer').click()
                before = self.export(page)
                before_canvas = page.locator('#composerCanvas').inner_html()
                base = {'target': FAKE, 'revision': 1, 'overrides': {}}
                bad_tokens = [
                    [], 'x', 5, {'font-display': 'serif'}, {'--': 'serif'}, {'--bad name': 'serif'},
                    {'--font-display': 5}, {'--font-display': ''}, {'--font-display': 'serif; color: red'},
                    {'--font-display': 'a } b { c'}, {'--font-display': 'url(x)'}, {'--font-display': '<b>'},
                    {'--font-display': '/* x */'}, {'--font-display': 'x' * 301}, {'--font-display': 'a\nb'},
                    {'--Font-Display': 'serif'}, {'--font_display': 'serif'}, {'--' + 'a' * 121: 'serif'},
                    {'--font-display': 'expression(1)'}, {'--font-display': 'a\\b'},
                    {f'--t{i}': 'serif' for i in range(80)},
                ]
                for bad in bad_tokens:
                    doc = {**before, 'composition': {**before['composition'], 'canvasWidth': '640'}, 'live': {**base, 'tokens': bad}}
                    status = self.import_document(page, doc)
                    self.assertTrue(status.startswith('Import failed:'), (str(bad)[:60], status))
                    self.assertEqual(self.export(page), before)
                    self.assertEqual(page.locator('#composerCanvas').inner_html(), before_canvas)
                good = {**before, 'live': {**base, 'tokens': dict(self.TOKENS)}}
                self.assertIn('Composition imported.', self.import_document(page, good))
                self.assertEqual(self.export(page)['live']['tokens'], self.TOKENS)
                # A later import whose live field has no tokens replaces them, like overrides.
                later = {**before, 'live': {**base, 'overrides': {'hero.title': {'fontSize': 40}}}}
                self.assertIn('Composition imported.', self.import_document(page, later))
                self.assertNotIn('tokens', self.export(page)['live'])
                self.assertEqual(errors, [])


class StudioSharedRulesTests(LiveCase):
    """Studio and the bridge share one rule for custom-property names, CSS text and font stylesheets."""
    SHEET = 'https://fonts.googleapis.com/css2?'

    def test_ledger_tokens_and_imports_follow_the_bridge_rules(self):
        six = self.SHEET + '&'.join(f'family=Family{i}:wght@400;700' for i in range(6)) + '&display=swap'
        nine = self.SHEET + '&'.join(f'family=F{i}' for i in range(9))
        tilde = self.SHEET + 'family=A~B:wght@400&text=Hi%20there'
        euro = self.SHEET + 'family=Inter&text=%E2%82%AC'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{FAKE}?hostile=1')
                self.wait_connected(page)
                css = self.code(page, 'Css')
                # Tokens: lower-case names only, and none of the characters the bridge refuses.
                self.assertIn('--ok-font: Georgia, serif !important;', css)
                for bad in ('--url', '--expr', '--back', '--Upper', '--under_score', 'evil.example'):
                    self.assertNotIn(bad, css, bad)
                # Imports: up to 8 families like the bridge, `~` allowed, only the listed percent escapes.
                self.assertIn(f'@import url("{six}");', css)
                self.assertIn(f'@import url("{tilde}");', css)
                self.assertNotIn(nine, css)
                self.assertNotIn('%E2%82%AC', css)
                self.assertEqual(errors, [])


class StudioBlockedStorageTests(LiveCase):
    def test_blocked_local_storage_does_not_stop_start_up_or_auto_connect(self):
        """Browsers that block site data throw on the localStorage getter; Studio must render and connect anyway."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                context.add_init_script("""Object.defineProperty(window, 'localStorage', {
                    get() { throw new DOMException('The operation is insecure.', 'SecurityError'); } });""")
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{APP}?target={quote(FAKE, safe="")}')
                self.wait_connected(page)
                self.assertGreater(page.locator('.slot-text').count(), 0, 'the Composer rendered')
                # Loading a kit must not throw when it cannot remember the id.
                page.locator('#kitPreset').select_option('adobe')
                page.locator('#composerKitIds').fill('abc123')
                page.locator('#loadComposerKits').click()
                page.locator('#modeLibrary').click()
                page.locator('#kitId').fill('abc123')
                page.locator('#loadKit').click()
                page.wait_for_function('() => document.querySelector("#kitStatus").textContent.length > 0')
                self.assertEqual(errors, [])


class StudioRecursionGuardTests(LiveCase):
    def test_only_studio_itself_is_blocked_not_every_url_that_mentions_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                # An app that lives in a folder or query named like the project is an ordinary target.
                self.connect(page, f'{FAKE}?project=font-kit-studio')
                self.wait_connected(page)
                self.assertIn('project=font-kit-studio', page.locator('#targetAppFrame').get_attribute('src'))
                # Studio itself is blocked even with a different query string or fragment.
                for probe in (APP, f'{APP}?x=1', f'{APP}#panel'):
                    page.locator('#targetAppUrl').fill(probe)
                    page.locator('#btnConnectTarget').click()
                    self.wait_badge(page, r'^Recursion blocked$')
                    page.locator('#targetAppUrl').fill(f'{FAKE}?project=font-kit-studio')
                    page.locator('#btnConnectTarget').click()
                    self.wait_connected(page)
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
