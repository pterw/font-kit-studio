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

    def watch_handled(self, page):
        """Counts the messages Studio has finished handling (a 0 ms timer runs after every listener of the event)."""
        page.evaluate("""() => { window.__handled = 0;
            window.addEventListener('message', (event) => { if (event.source !== window) setTimeout(() => { window.__handled += 1; }, 0); }); }""")

    def wait_handled(self, page, count):
        page.wait_for_function('(count) => window.__handled >= count', arg=count)

    def sync_file(self, page):
        """Presses Sync to file and waits until the dev-server stub has answered (self.puts holds the new body)."""
        with page.expect_response(lambda response: response.request.method == 'PUT' and response.url.endswith('/__fontkit/overrides.css')):
            page.locator('#liveCodeSync').click()
        return self.puts[-1]['body']

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
                self.assertIn(self.ACCEPT, ' '.join(banner.inner_text().split()))
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                status = page.locator('#liveCodeStatus').inner_text()
                self.assertRegex(status, r'(?i)replaced')
                self.assertRegex(status, r'(?i)DOM order')
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {})
                self.assertNotIn('live', self.export(page))
                page.wait_for_timeout(200)
                self.assertEqual(self.updates(frame), [])
                self.assertEqual(errors, [])

    ACCEPT = "Accept target state replaces Studio's saved overrides, composition tokens and DOM order with what the page has now"

    def test_the_banner_explains_zero_live_edits_only_when_the_target_has_none(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 70)
                self.wait_badge(page, r'^Live · rev 1$')
                banner = page.locator('#liveReconnectBanner')
                # The target kept one of Studio's two saved edits: it does count live edits, so no "0 live edits" talk.
                self.select(page, frame, 'stat.badge')
                self.set_value(page, '#liveFontWeight', 600)
                self.wait_badge(page, r'^Live · rev 2$')
                doc = self.export(page)
                doc['live']['overrides'] = {'hero.title': {'fontSize': 70}, 'hero.lead': {'fontSize': 21}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner.wait_for(state='visible')
                partial = ' '.join(banner.inner_text().split())
                self.assertNotRegex(partial, r'0 live edits')
                self.assertIn(self.ACCEPT, partial)
                # The page also holds an edit Studio does not save (the badge), so Accept would not only drop things.
                self.assertNotRegex(partial, r'smaller file')
                # Saved state that is a superset of the page's: here the next Sync really does write a smaller file.
                doc['live']['overrides'] = {'hero.title': {'fontSize': 70}, 'stat.badge': {'fontWeight': 600}, 'hero.lead': {'fontSize': 21}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                superset = ' '.join(banner.inner_text().split())
                self.assertIn(self.ACCEPT, superset)
                self.assertRegex(superset, r'next Sync writes a smaller file')
                # A reload leaves the target with none: now the page can look right with 0 live edits.
                frame.evaluate('location.reload()')
                frame = self.frame(page)
                self.wait_connected(page)
                zero = ' '.join(banner.inner_text().split())
                self.assertIn('the live target has 0 targets changed', zero)
                self.assertRegex(zero, r'overrides file already styles the page')
                self.assertRegex(zero, r'0 live edits')
                # ... but not when the page holds composition tokens: those are edits the bridge counts.
                self.watch_handled(page)
                frame.evaluate('window.fake.setTokens({"--other-font": "Georgia, serif"})')
                frame.evaluate('window.fake.reannounce()')
                self.wait_handled(page, 2)
                tokens = ' '.join(banner.inner_text().split())
                self.assertIn('1 composition token', tokens)
                self.assertNotRegex(tokens, r'0 live edits')
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
                text = ' '.join(banner.inner_text().split())
                self.assertIn("Accept target state replaces Studio's saved overrides, composition tokens and DOM order with what the page has now", text)
                self.assertRegex(text, r'next Sync writes a smaller file', 'the saved edit is the only difference, so the claim is true')
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
                # Saved state that does not hold the DOM move (the export would, since DOM moves are saved).
                del doc['live']['structure']
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

    def test_reapply_keeps_a_saved_dom_move_while_it_clears_a_stale_css_order(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.stale_order_setup(engine, dom_move=True)
                dom_moved = frame.evaluate('window.fake.domOrder("cards")')
                self.assertEqual(dom_moved, ['card.a', 'card.b', 'card.d', 'card.c'])
                doc = self.export(page)
                # The saved state holds the DOM move but not the CSS order, which Reapply must clear with a reset.
                doc['live']['overrides'] = {'hero.title': {'fontSize': 40}}
                self.assertEqual(len(doc['live']['structure']), 1)
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertRegex(banner.inner_text(), r'(?i)reset.*arrangement')
                self.assertNotRegex(banner.inner_text(), r'(?i)undoes the DOM moves', 'the saved DOM move is replayed after the reset')
                # The page already holds the saved DOM order, as its own ledger reports it (in DOM order, like the bridge).
                self.assertEqual(frame.evaluate('window.fake.ledger().structure[0].orderIds'), dom_moved)
                before = len(self.received(frame, 'design:move')) + len(self.received(frame, 'design:reset'))
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('(o) => JSON.stringify(window.fake.domOrder("cards")) === JSON.stringify(o)', arg=dom_moved)
                self.assertEqual(frame.evaluate('window.fake.visualOrder("cards")'), dom_moved, 'the CSS order is gone')
                # The reset that clears the CSS order undid the DOM move on the page, so Reapply put it back afterwards.
                sent = [item['data'] for item in self.received(frame)
                        if isinstance(item['data'], dict) and item['data'].get('type') in ('design:move', 'design:reset')][before:]
                kinds = [(m['type'], m.get('strategy')) for m in sent]
                self.assertEqual(kinds[0], ('design:reset', None))
                self.assertIn(('design:move', 'dom'), kinds[1:], 'the saved DOM order is replayed after the reset')
                self.assertEqual(errors, [])

    def test_reapply_moves_a_reset_element_back_into_its_saved_container(self):
        """A saved move into another container plus a stale CSS order on the moved element: the reset sends the element
        back to the container it started in, so the replay has to name the container, not just an index."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=ARRANGE)
                frame = self.wait_ready(page, 11)
                self.select(page, frame, 'card.a')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveNext').click()
                self.wait_badge(page, r'^Live · rev 1$')
                options = page.locator('#liveMoveContainer option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                sidebar = next(value for value, name in options if name == 'Sidebar')
                page.locator('#liveMoveContainer').select_option(sidebar)
                page.locator('#liveMoveInto').click()
                self.wait_badge(page, r'^Live · rev 2$')
                saved_order = ['side.x', 'side.y', 'card.a']
                self.assertEqual(self.dom(frame, sidebar), saved_order)
                self.assertEqual(frame.evaluate('window.fake.ledger().targets.find(t => t.targetId === "card.a").declarations.order'), '1',
                                 'the CSS order is still on the moved element')
                doc = self.export(page)
                self.assertIn(['side.x', 'side.y', 'card.a'], [entry['ids'] for entry in doc['live']['structure']])
                # Saved state holds the move but no CSS order: the order on the target is stale and Reapply resets it.
                doc['live']['overrides'] = {'hero.title': {'fontSize': 40}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                before = len(self.received(frame, 'design:move'))
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.wait_list(page, saved_order)
                self.assertEqual(self.dom(frame, sidebar), saved_order, 'the element ended in the container it was saved in')
                self.assertNotIn('card.a', self.dom(frame, 'cards'))
                replay = self.moves(frame)[before:]
                card_a = [m for m in replay if m['targetId'] == 'card.a']
                self.assertEqual([m['to'] for m in card_a], [{'container': sidebar, 'index': 2}], 'moved by container, not by index')
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


class StudioReviewFixTests(LiveCase):
    """Review fixes for the state boundary: selectors, composition tokens, late replies."""

    def edit_size(self, page, frame, size):
        """Type a font size into the inspector and wait for the target's acknowledgement."""
        before = frame.evaluate('window.fake.revision')
        self.set_value(page, '#liveFontSize', size)
        self.wait_badge(page, rf'^Live · rev {before + 1}$')

    # -- 1. selectors with the child combinator -----------------------------
    ACCEPTED_SELECTORS = [
        'main:nth-of-type(1) > section.hero:nth-of-type(2) > h2:nth-of-type(1)',
        'body > div.wrap:nth-of-type(1) > h2.sm\\:text-lg:nth-of-type(3)',
        '#cards > article.card:nth-of-type(2)',
        '[data-design-id="a\\"b"] > p:nth-of-type(1)',
        '.w-1\\/2:nth-of-type(1) > span:nth-of-type(1)',
        '.\\[\\&\\>\\*\\]\\:p-4:nth-of-type(1) > p:nth-of-type(2)',
        '.a\\;b\\{c\\}d\\<e\\\\f:nth-of-type(1)',
        '.\\31 0 > b.a\\31  > i',
        '[data-design-id="hero\\3b alternate"]',
        '[data-design-id="a\\7b b\\7d \\3c c\\3e \\"d\\\\e"] > p:nth-of-type(1)',
        '[data-design-id="x\\"]\\7b \\7d  body\\7b color:red\\7d \\2f \\2a "]:nth-of-type(2)',
    ]
    REJECTED_SELECTORS = [
        'main > h2 { color: red } h3',
        'main > h2; color: red',
        'main > h2 } body { display: none',
        'main > h2 <script>',
        '[data-design-id="x"]{} body{color:red}/*"]',
        '[data-design-id="x\\"]{} body{color:red}"]',
        '[data-design-id="a<b"]',
        '[data-design-id="a{b"]',
        '[data-design-id="a;b"]',
        '[data-design-id="a\\3bb\\"]',
        '[data-design-id="a\\"]',
        'main > h2\\',
        'main > h2\\{',
        'main > url(https://evil.example/a)',
        'main > h2 /* x */',
        '[data-design-id="a;b"] > p',
        '> main',
        'main >',
        'main >> h2',
    ]

    def test_auto_target_selectors_with_the_child_combinator_reach_the_css_and_the_synced_file(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                self.select(page, frame, 'auto.h2.1')
                size = 40
                for selector in self.ACCEPTED_SELECTORS:
                    with self.subTest(selector=selector):
                        size += 1
                        frame.evaluate('([id, value]) => window.fake.setSelector(id, value)', ['auto.h2.1', selector])
                        self.edit_size(page, frame, size)
                        css = self.code(page, 'Css')
                        self.assertIn(f'\n{selector} {{\n  font-size: {size}px !important;\n}}', css)
                        self.assertNotIn('skipped', css)
                        self.assertIn('auto-discovered — add data-design-id for a stable selector', css)
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn(f'{self.ACCEPTED_SELECTORS[-1]} {{\n  font-size: {size}px !important;', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    def test_hostile_selectors_are_skipped_not_written(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'auto.h2.1')
                size = 40
                for selector in self.REJECTED_SELECTORS:
                    with self.subTest(selector=selector):
                        size += 1
                        frame.evaluate('([id, value]) => window.fake.setSelector(id, value)', ['auto.h2.1', selector])
                        self.edit_size(page, frame, size)
                        css = self.code(page, 'Css')
                        self.assertIn('skipped: the target reported no safe selector', css)
                        self.assertNotIn(f'font-size: {size}px', css)
                        for hostile in ('{ color: red }', '<script>', 'evil.example', '/* x */', 'display: none'):
                            self.assertNotIn(hostile, css)
                self.assertEqual(errors, [])

    # Adversarial runs of escapes: a grammar that can match the same text two ways takes exponential time on these.
    ADVERSARIAL = [
        '.' + '\\aaaaaa' * 11 + '{',
        '.' + '\\aaaaaa' * 70 + '{',
        '.' + 'a' * 10 + '\\ab' * 150 + '{',
        '.' + '\\a' * 250 + ';',
        'a' + ' > a\\1' * 90 + '\\',
        '.' + 'a' * 495 + '{',
        '[data-design-id="' + '\\aaaaaa' * 60 + '{"]',
        '[data-design-id="' + ' ' * 300 + '\\ab ' * 30 + '{"]',
        '[data-design-id="' + '\\a ' * 150 + '\\"]',
    ]

    def test_adversarial_escape_runs_do_not_freeze_studio_and_are_skipped(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'auto.h2.1')
                size = 40
                for selector in self.ADVERSARIAL:
                    with self.subTest(selector=selector[:30], length=len(selector)):
                        size += 1
                        frame.evaluate('([id, value]) => window.fake.setSelector(id, value)', ['auto.h2.1', selector])
                        started = time.time()
                        self.edit_size(page, frame, size)
                        css = self.code(page, 'Css')
                        page.evaluate('1 + 1')
                        self.assertLess(time.time() - started, 3, 'the page stayed responsive')
                        self.assertIn('skipped: the target reported no safe selector', css)
                        self.assertNotIn(f'font-size: {size}px', css)
                self.assertEqual(errors, [])

    def test_the_selector_check_itself_is_fast_on_500_character_inputs(self):
        """Runs the shipped regexes (read from the page source) on adversarial and valid text."""
        source = HTML.read_text(encoding='utf-8')
        start = source.index('  const UNSAFE_CSS_TEXT')
        end = source.index(': UNSAFE_CSS_TEXT.test(text);', start) + len(': UNSAFE_CSS_TEXT.test(text);')
        code = source[start:end] + '\nreturn unsafeCssText;'
        valid = ['.' + '\\31 ' * 120 + 'a', 'a' + ' > a:nth-of-type(1)' * 25, '.' + 'a\\;' * 160,
                 '[data-design-id="' + 'x\\"' * 120 + '"]', '[data-design-id="' + '\\3b ' * 120 + '"]',
                 '[data-design-id="' + '\\a  ' * 100 + 'x"]', '[data-design-id="' + '\\aaaaaa' * 60 + '"]']
        inputs = self.ADVERSARIAL + valid
        for engine in ENGINES:
            with self.subTest(engine=engine):
                browser = launch(self.runtime, engine)
                self.browsers.append(browser)
                page = browser.new_page()
                timings = page.evaluate("""([code, inputs]) => {
                    const check = new Function(code)();
                    return inputs.map(text => { const t = performance.now(); const unsafe = check(text, { selector: true });
                        return [text.length, performance.now() - t, unsafe]; });
                }""", [code, inputs])
                for length, elapsed, _ in timings:
                    self.assertLess(elapsed, 50, f'{length} characters took {elapsed:.1f} ms')
                self.assertEqual([unsafe for _, _, unsafe in timings[:len(self.ADVERSARIAL)]], [True] * len(self.ADVERSARIAL))
                self.assertEqual([unsafe for _, _, unsafe in timings[len(self.ADVERSARIAL):]], [False] * len(valid),
                                 'long but well-formed selectors are still accepted')

    # -- 2. composition tokens that exist only on the target -----------------
    LEFT_ON_TARGET = {'--font-display': '"Fraunces", serif', '--font-sans': '"Inter", sans-serif'}

    def saved_state_then_target_with_other_tokens(self, page, frame, saved_tokens=None, overrides=None):
        """Studio saves `saved_tokens`; the target (re-announced, not reloaded) holds tokens Studio does not save."""
        live = {'target': FAKE, 'revision': 0, 'overrides': overrides if overrides is not None else {'hero.title': {'fontSize': 50}}}
        if saved_tokens:
            live['tokens'] = saved_tokens
        self.assertIn('Composition imported.', self.import_document(page, {**self.export(page), 'live': live}))
        banner = page.locator('#liveReconnectBanner')
        banner.wait_for(state='visible')
        frame.evaluate('(values) => window.fake.setTokens(values)', self.LEFT_ON_TARGET)
        frame.evaluate('window.fake.reannounce()')
        page.wait_for_function('() => /the live target has \\d+ targets? changed and 2 composition tokens/.test('
                               'document.querySelector("#liveReconnectText").textContent)')
        self.assertEqual(self.updates(frame), [], 'reconnecting never applies anything by itself')
        return banner

    def test_reapply_removes_target_only_tokens_and_reports_success_only_when_they_are_gone(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                banner = self.saved_state_then_target_with_other_tokens(page, frame)
                self.assertNotIn('tokens', self.export(page)['live'])
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.assertEqual(frame.evaluate('window.fake.ledger().tokens'), {},
                                 'the target keeps no token Studio does not save')
                for name in self.LEFT_ON_TARGET:
                    self.assertEqual(frame.evaluate('(n) => document.documentElement.style.getPropertyValue(n)', name), '')
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(composition[-1]['patch'], {'tokens': {name: None for name in self.LEFT_ON_TARGET}})
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '50px')
                self.assertNotIn('tokens', self.export(page)['live'])
                self.assertNotIn(':root {', self.code(page, 'Css'))
                self.assertEqual(errors, [])

    def test_reapply_mixes_saved_tokens_with_null_for_target_only_ones(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                keep = {'--font-display': '"Crimson Pro", serif'}
                banner = self.saved_state_then_target_with_other_tokens(page, frame, saved_tokens=keep, overrides={})
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.assertEqual(frame.evaluate('window.fake.ledger().tokens'), keep)
                patch = [u for u in self.updates(frame) if 'targetId' not in u][-1]['patch']
                self.assertEqual(patch, {'tokens': {'--font-display': '"Crimson Pro", serif', '--font-sans': None}})
                self.assertEqual(self.export(page)['live']['tokens'], keep)
                self.assertEqual(errors, [])

    def test_reapply_does_not_report_success_while_the_target_keeps_a_token(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                banner = self.saved_state_then_target_with_other_tokens(page, frame)
                frame.evaluate('window.fake.keepNullTokens = true')   # a bridge that does not know null removes a token
                page.locator('#liveReapply').click()
                page.wait_for_function('() => /Reapply stopped/.test(document.querySelector("#liveReconnectText").textContent)')
                self.assertTrue(banner.is_visible(), 'the conflict stays open')
                self.assertRegex(page.locator('#liveReconnectText').inner_text(), r'(?i)token')
                self.assertEqual(frame.evaluate('window.fake.ledger().tokens'), self.LEFT_ON_TARGET)
                self.assertNotIn('tokens', self.export(page)['live'], "Studio's saved state is not replaced by the target's")
                # Once the target can remove them, the same button finishes the job.
                frame.evaluate('window.fake.keepNullTokens = false')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.assertEqual(frame.evaluate('window.fake.ledger().tokens'), {})
                self.assertEqual(errors, [])

    # -- 3. replies that arrive after several timeouts -----------------------
    def edit_two_targets_while_the_target_is_unresponsive(self, page, frame):
        """Edits hero.title (61) then hero.lead (17) with the target holding every reply, until both requests timed out."""
        frame.evaluate('window.fake.hold = true')
        # Two different targets, so the edits queue as two requests instead of coalescing.
        self.select(page, frame, 'hero.title')
        self.set_value(page, '#liveFontSize', 61)
        self.select(page, frame, 'hero.lead')
        self.set_value(page, '#liveFontSize', 17)
        # The first request times out (8 s) and the second is sent; then the second times out as well.
        self.wait_badge(page, '^No response from target$', timeout=15000)
        frame.wait_for_function('window.fake.heldCount() === 2')
        page.evaluate('() => { document.querySelector("#bridgeStatusBadge").textContent = "Waiting for the second request"; }')
        self.wait_badge(page, '^No response from target$', timeout=15000)

    def test_every_timed_out_request_stays_tracked_until_its_late_reply_arrives(self):
        """A target that applies the queued requests in order, whatever revision they were based on."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                frame.evaluate('window.fake.ignoreBaseRevision = true')
                self.edit_two_targets_while_the_target_is_unresponsive(page, frame)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                frame.evaluate('window.fake.release()')
                self.wait_badge(page, r'^Live · rev 2$')
                saved = json.loads(self.code(page, 'Json'))['overrides']
                self.assertEqual(saved, {'hero.title': {'fontSize': 61}, 'hero.lead': {'fontSize': 17}})
                css = self.code(page, 'Css')
                self.assertIn('font-size: 61px !important;', css)
                self.assertIn('font-size: 17px !important;', css)
                self.assertEqual(self.export(page)['live']['overrides'], saved)
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn('font-size: 61px !important;', self.puts[-1]['body'])
                self.assertIn('font-size: 17px !important;', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    def test_a_late_revision_conflict_is_shown_and_the_first_edit_is_kept(self):
        """The real outcome: the target applied the first request, then refused the second as based on an old revision."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                self.edit_two_targets_while_the_target_is_unresponsive(page, frame)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                frame.evaluate('window.fake.release()')
                # The second edit is reported, not lost without a word.
                self.wait_badge(page, '^Rejected: revision-conflict$')
                saved = json.loads(self.code(page, 'Json'))['overrides']
                self.assertEqual(saved, {'hero.title': {'fontSize': 61}}, 'only what the target applied is saved')
                css = self.code(page, 'Css')
                self.assertIn('font-size: 61px !important;', css)
                self.assertNotIn('17px', css)
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.lead").fontSize'), '16px')
                # The inspector shows what the page really has, not the refused value.
                self.assertEqual(page.locator('#liveFontSize').input_value(), '16')
                # Studio learned the target's revision from the late replies, so the user can simply enter it again.
                self.set_value(page, '#liveFontSize', 18)
                self.wait_badge(page, r'^Live · rev 2$')
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'],
                                 {'hero.title': {'fontSize': 61}, 'hero.lead': {'fontSize': 18}})
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn('font-size: 61px !important;', self.puts[-1]['body'])
                self.assertIn('font-size: 18px !important;', self.puts[-1]['body'])
                self.assertNotIn('17px', self.puts[-1]['body'])
                self.assertEqual(errors, [])


class StudioPromotedTargetTests(LiveCase):
    """An auto-discovered target that gets an author data-design-id keeps its saved edit, under the new id."""
    NEW_ID = 'features.heading'

    def watch_messages(self, page):
        """Counts the target's replies once Studio has finished handling them (a 0 ms timer runs after every listener)."""
        page.evaluate("""() => { window.__seen = { 'design:ready': 0, 'design:targets': 0 };
            window.addEventListener('message', (event) => { const type = event.data && event.data.type;
                if (type in window.__seen) setTimeout(() => { window.__seen[type] += 1; }, 0); }); }""")

    def wait_seen(self, page, type, count=1):
        page.wait_for_function('([type, count]) => window.__seen[type] >= count', arg=[type, count])

    def test_saved_override_follows_the_target_to_its_new_id_without_a_conflict(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'auto.h2.1')
                before = frame.evaluate('window.fake.revision')
                self.set_value(page, '#liveFontSize', 50)
                self.wait_badge(page, rf'^Live · rev {before + 1}$')
                css = self.code(page, 'Css')
                self.assertIn('#features {\n  font-size: 50px !important;', css)
                self.assertIn('add data-design-id for a stable selector', css)

                frame.evaluate('(ids) => window.fake.promote(...ids)', ['auto.h2.1', self.NEW_ID])
                # The edit is now filed under the new id, with the stable selector and no hint to add one.
                page.wait_for_function('(id) => document.querySelector("#liveCodeOutput").textContent.includes("(" + id + ")")',
                                       arg=self.NEW_ID)
                css = self.code(page, 'Css')
                self.assertIn(f'[data-design-id="{self.NEW_ID}"] {{\n  font-size: 50px !important;', css)
                self.assertNotIn('auto.h2.1', css)
                self.assertNotIn('add data-design-id', css)
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {self.NEW_ID: {'fontSize': 50}})
                self.assertEqual(self.export(page)['live']['overrides'], {self.NEW_ID: {'fontSize': 50}})
                self.assertEqual(page.locator('#liveChangeCount').text_content(), '1')
                # The inspector follows the same element.
                self.assertEqual(page.locator('#liveTargetName').get_attribute('data-target-id'), self.NEW_ID)

                # A reconnect compares saved and target state: they agree, so there is nothing to resolve.
                self.watch_messages(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_seen(page, 'design:ready')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(self.updates(frame)[-1]['targetId'], 'auto.h2.1', 'nothing was sent after the promotion')
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {self.NEW_ID: {'fontSize': 50}})
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn(f'[data-design-id="{self.NEW_ID}"] {{\n  font-size: 50px !important;', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    AUTO_ID = 'auto:p:body:7'
    AUTO_SELECTOR = 'body > p:nth-of-type(1)'

    def test_a_removed_author_id_moves_the_saved_override_to_the_auto_id_and_brings_the_hint_back(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.lead')
                before = frame.evaluate('window.fake.revision')
                self.set_value(page, '#liveFontSize', 21)
                self.wait_badge(page, rf'^Live · rev {before + 1}$')
                css = self.code(page, 'Css')
                self.assertIn('[data-design-id="hero.lead"] {\n  font-size: 21px !important;', css)
                self.assertNotIn('add data-design-id', css)
                self.assertFalse(page.locator('.live-target-id').inner_text().count('auto-discovered'))

                frame.evaluate('(args) => window.fake.demote(...args)', ['hero.lead', self.AUTO_ID, self.AUTO_SELECTOR])
                page.wait_for_function('(id) => document.querySelector("#liveCodeOutput").textContent.includes("(" + id + ")")', arg=self.AUTO_ID)
                css = self.code(page, 'Css')
                self.assertIn(f'{self.AUTO_SELECTOR} {{\n  font-size: 21px !important;', css)
                self.assertIn('add data-design-id for a stable selector', css)
                self.assertNotIn('data-design-id="hero.lead"', css)
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], {self.AUTO_ID: {'fontSize': 21}})
                self.assertEqual(self.export(page)['live']['overrides'], {self.AUTO_ID: {'fontSize': 21}})
                # The inspector follows the element and shows the unstable-selector hint again.
                self.assertEqual(page.locator('#liveTargetName').get_attribute('data-target-id'), self.AUTO_ID)
                self.assertIn('auto-discovered', page.locator('.live-target-id').inner_text())
                self.assertIn('add data-design-id', page.locator('.live-target-id').inner_text())

                # Saved and target state agree under the new id: no conflict, nothing sent, and the file gets the new selector.
                sent = len(self.received(frame, 'design:update'))
                self.watch_messages(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_seen(page, 'design:ready')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(len(self.received(frame, 'design:update')), sent)
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertIn(f'{self.AUTO_SELECTOR} {{\n  font-size: 21px !important;', self.puts[-1]['body'])
                self.assertEqual(errors, [])

    def test_a_removed_id_cannot_steal_the_saved_override_of_a_live_target(self):
        """The guard stays: a previousId that names a target still in the list moves nothing."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                before = frame.evaluate('window.fake.revision')
                self.set_value(page, '#liveFontSize', 50)
                self.wait_badge(page, rf'^Live · rev {before + 1}$')
                self.watch_messages(page)
                # A hostile or buggy manifest claims the live hero.title was replaced.
                frame.evaluate('window.fake.setPreviousId("auto.h2.1", "hero.title")')
                frame.evaluate('window.fake.emitAll()')
                self.wait_seen(page, 'design:targets')
                self.assertEqual(self.export(page)['live']['overrides'], {'hero.title': {'fontSize': 50}})
                self.assertEqual(errors, [])

    def test_a_saved_override_under_the_old_id_is_rekeyed_when_the_bridge_reports_the_promotion(self):
        """Studio opened after the promotion (an imported state still names the old id): the manifest bridges the two."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'auto.h2.1')
                before = frame.evaluate('window.fake.revision')
                self.set_value(page, '#liveFontSize', 50)
                self.wait_badge(page, rf'^Live · rev {before + 1}$')
                saved = self.export(page)
                frame.evaluate('(ids) => window.fake.promote(...ids)', ['auto.h2.1', self.NEW_ID])
                # A state saved under the old id is imported later; the next handshake names the id it became.
                self.assertIn('Composition imported.', self.import_document(page, saved))
                self.assertEqual(self.export(page)['live']['overrides'], {'auto.h2.1': {'fontSize': 50}})
                self.watch_messages(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_seen(page, 'design:ready')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'the saved edit is the target state')
                self.assertEqual(self.export(page)['live']['overrides'], {self.NEW_ID: {'fontSize': 50}})
                self.assertEqual(errors, [])

    def test_a_previous_id_naming_a_live_target_or_nothing_usable_never_moves_a_saved_override(self):
        """A buggy or hostile manifest must not drop the saved edit of a target that is still in the list."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                for target_id, size in (('hero.title', 50), ('auto.h2.1', 44)):
                    self.select(page, frame, target_id)
                    before = frame.evaluate('window.fake.revision')
                    self.set_value(page, '#liveFontSize', size)
                    self.wait_badge(page, rf'^Live · rev {before + 1}$')
                saved = {'hero.title': {'fontSize': 50}, 'auto.h2.1': {'fontSize': 44}}
                self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], saved)
                css_before = self.code(page, 'Css')
                sent = len(self.received(frame, 'design:update'))
                self.watch_messages(page)
                seen = 0
                for previous in ('hero.title', 5, '', None, ['hero.title'], 'auto.h2.1', 'never.seen'):
                    with self.subTest(previous=previous):
                        frame.evaluate('([value]) => window.fake.setPreviousId("auto.h2.1", value)', [previous])
                        frame.evaluate('window.fake.emitAll()')
                        seen += 1
                        self.wait_seen(page, 'design:targets', seen)
                        self.assertEqual(json.loads(self.code(page, 'Json'))['overrides'], saved)
                        self.assertEqual(self.export(page)['live']['overrides'], saved)
                self.assertEqual(self.code(page, 'Css'), css_before)
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                for rule in ('font-size: 50px !important;', 'font-size: 44px !important;'):
                    self.assertIn(rule, self.puts[-1]['body'])
                self.assertEqual(len(self.puts), 1, 'nothing was synced except by the explicit click')
                self.assertEqual(len(self.received(frame, 'design:update')), sent, 'nothing was sent to the target')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_a_saved_edit_re_keyed_for_an_id_the_page_never_listed_says_so_and_writes_nothing(self):
        """A manifest may name any previousId: the saved edit follows it only visibly, and nothing is synced by itself."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                doc = {**self.export(page), 'live': {'target': FAKE, 'revision': 0, 'overrides': {'footer.legal': {'fontSize': 77}}}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                self.watch_messages(page)
                frame.evaluate('window.fake.setPreviousId("auto.h2.1", "footer.legal")')
                frame.evaluate('window.fake.emitAll()')
                self.wait_seen(page, 'design:targets')
                self.assertEqual(self.export(page)['live']['overrides'], {'auto.h2.1': {'fontSize': 77}})
                status = ' '.join(page.locator('#liveCodeStatus').text_content().split())
                self.assertIn('Moved the saved edit for footer.legal to auto.h2.1 because the page reported it', status)
                page.wait_for_timeout(700)    # absence check: auto-sync is off and the conflict is open
                self.assertEqual(self.puts, [], 'nothing was written without a click')
                self.assertEqual(errors, [])

class StudioPromotedStructureTests(ArrangeCase):
    """A saved DOM order names children by id: when the page re-keys a child, the saved order follows it."""

    def test_the_saved_dom_order_follows_a_child_that_got_an_author_id(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'side.x')
                page.locator('#liveMoveLast').click()
                self.wait_badge(page, r'^Live · rev 1$')
                before = self.export(page)['live']['structure']
                self.assertEqual(before[0]['ids'], ['side.y', 'side.x'])
                self.watch_handled(page)
                frame.evaluate('window.fake.promote("side.x", "side.renamed")')
                self.wait_handled(page, 1)
                after = self.export(page)['live']['structure']
                self.assertEqual(after, [{**before[0], 'ids': ['side.y', 'side.renamed']}])
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'the saved order is what the page holds')
                self.assertEqual(errors, [])


class StudioDomMovePersistenceTests(ArrangeCase):
    """DOM-order moves are saved state: they survive a reload through Reapply, never silently (rule 6)."""
    CARDS = {'selector': '[data-design-id="cards"]', 'name': 'Cards'}

    def move_first(self, page, frame, card='card.c'):
        self.select(page, frame, card)
        page.locator('#liveMoveFirst').click()
        self.wait_badge(page, r'^Live · rev 1$')

    def test_a_dom_move_says_it_is_kept_in_studio_but_not_in_the_css_file(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                status = page.locator('#liveCodeStatus').inner_text()
                self.assertRegex(status, r'(?i)kept in Studio')
                self.assertRegex(status, r'(?i)HTML tab')
                self.assertRegex(status, r'(?i)not (in|written to) the CSS file')
                self.assertRegex(status, r'(?i)CSS order')
                # A CSS-order move is what the file keeps: it does not carry the warning.
                page.locator('#liveResetTarget').click()
                self.wait_badge(page, r'^Live · rev 2$')
                page.locator('#liveMoveStrategyCss').click()
                page.locator('#liveMoveFirst').click()
                self.wait_badge(page, r'^Live · rev 3$')
                self.assertNotRegex(page.locator('#liveCodeStatus').inner_text(), r'(?i)not (in|written to) the CSS file')
                self.assertEqual(errors, [])

    def test_dom_moves_are_saved_and_reapply_replays_them_after_a_reload(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                saved = {**self.CARDS, 'ids': ['card.c', 'card.a', 'card.b', 'card.d']}
                self.assertEqual(self.export(page)['live']['structure'], [saved])
                self.assertEqual(self.export(page)['live']['overrides'], {})
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 11)
                self.assertRegex(banner.inner_text(), r'(?i)DOM order')
                # Restoring a move stays an explicit choice.
                page.wait_for_timeout(300)
                self.assertEqual(self.moves(frame), [])
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.export(page)['live']['structure'], [saved], 'the saved move survives the reload')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('JSON.stringify(window.fake.domOrder("cards")) === JSON.stringify(["card.c","card.a","card.b","card.d"])')
                self.assertTrue(self.moves(frame))
                self.assertTrue(all(m['strategy'] == 'dom' for m in self.moves(frame)), self.moves(frame))
                # The HTML tab shows the structure block again, and the saved move is unchanged.
                self.assertIn('Structure: Cards', self.code(page, 'Html'))
                self.assertEqual(self.export(page)['live']['structure'], [saved])
                # Resetting the element drops the saved move with it.
                self.select(page, frame, 'card.c')
                page.locator('#liveResetTarget').click()
                page.wait_for_function('() => document.querySelector("#liveChangeCount").textContent === "0"')
                self.assertNotIn('live', self.export(page))
                self.assertEqual(errors, [])

    def test_a_reconnect_without_a_reload_finds_nothing_to_resolve(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                frame.evaluate('window.fake.reannounce()')
                page.wait_for_function('() => /Connected/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(300)
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'saved and target orders agree')
                self.assertEqual(self.dom(frame), ['card.c', 'card.a', 'card.b', 'card.d'])
                self.assertEqual(errors, [])

    def test_a_move_into_another_container_is_replayed_into_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.a')
                options = page.locator('#liveMoveContainer option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                page.locator('#liveMoveContainer').select_option(next(value for value, name in options if name == 'Sidebar'))
                page.locator('#liveMoveInto').click()
                self.wait_badge(page, r'^Live · rev 1$')
                structure = {entry['name']: entry['ids'] for entry in self.export(page)['live']['structure']}
                self.assertEqual(structure, {'Cards': ['card.b', 'card.c', 'card.d'], 'Sidebar': ['side.x', 'side.y', 'card.a']})
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 11)
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                key = frame.evaluate('window.fake.arrangementOf("card.a").containerKey')
                self.assertEqual(self.dom(frame, key), ['side.x', 'side.y', 'card.a'])
                self.assertEqual(self.dom(frame, 'cards'), ['card.b', 'card.c', 'card.d'])
                self.assertEqual(errors, [])

    def test_a_container_the_target_reorders_by_itself_is_not_saved_and_never_raises_a_conflict(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.reverse(window.fake.arrangementOf("side.x").containerKey)')
                self.assertEqual(len(frame.evaluate('window.fake.ledger().structure')), 1)
                self.move_first(page, frame)
                saved = self.export(page)['live']['structure']
                self.assertEqual([entry['name'] for entry in saved], ['Cards'], 'only what the user moved is saved')
                frame.evaluate('window.fake.reannounce()')
                page.wait_for_function('() => /Connected/.test(document.querySelector("#bridgeStatusBadge").textContent)')
                page.wait_for_timeout(300)
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'target-only reordering is not a difference')
                self.assertEqual(errors, [])

    def test_resetting_a_moved_element_that_came_from_another_container_drops_both_saved_containers(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.a')
                options = page.locator('#liveMoveContainer option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                page.locator('#liveMoveContainer').select_option(next(value for value, name in options if name == 'Sidebar'))
                page.locator('#liveMoveInto').click()
                self.wait_badge(page, r'^Live · rev 1$')
                self.assertEqual(len(self.export(page)['live']['structure']), 2)
                page.locator('#liveResetTarget').click()
                self.wait_badge(page, r'^Live · rev 2$')
                self.assertNotIn('live', self.export(page))
                self.assertEqual(self.dom(frame, 'cards'), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(errors, [])

    def test_accept_target_state_drops_saved_dom_moves(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 11)
                text = ' '.join(banner.inner_text().split())
                self.assertIn("Accept target state replaces Studio's saved overrides, composition tokens and DOM order with what the page has now", text)
                self.assertNotRegex(text, r'smaller file', 'a DOM move is not in the file, so Accept cannot shrink it')
                self.assertNotRegex(text, r'0 live edits', 'there are no saved overrides to explain')
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                status = page.locator('#liveCodeStatus').inner_text()
                self.assertRegex(status, r'(?i)DOM order')
                self.assertRegex(status, r'(?i)replaced')
                self.assertNotIn('live', self.export(page))
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.moves(frame), [])
                self.assertEqual(errors, [])

    def test_the_saved_moves_import_validated_and_wait_for_an_explicit_reapply(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                exported = self.export(page)
                good = [{**self.CARDS, 'ids': ['card.d', 'card.c', 'card.b', 'card.a']}]
                base = {'target': ARRANGE, 'revision': 3, 'overrides': {}}
                bad = [
                    'cards', {}, [7], [{'selector': 5, 'name': 'Cards', 'ids': ['card.a']}],
                    [{'selector': 'x', 'name': 'Cards', 'ids': 'card.a'}], [{'selector': 'x', 'name': 'Cards', 'ids': []}],
                    [{'selector': 'x', 'name': 'Cards', 'ids': [1, 2]}], [{'selector': 'x', 'name': 'Cards', 'ids': ['']}],
                    [{'selector': 'x', 'name': 'Cards', 'ids': ['a'] * 501}],
                    [{'selector': 'x' * 2001, 'name': 'Cards', 'ids': ['card.a']}],
                    [{'selector': 'x', 'name': 'Cards', 'ids': ['card.a', 'card.a']}],
                    [{'selector': 'x', 'name': 'Cards', 'ids': ['a']}] * 101,
                ]
                for structure in bad:
                    doc = {**exported, 'composition': {**exported['composition'], 'canvasWidth': '640'},
                           'live': {**base, 'structure': structure}}
                    status = self.import_document(page, doc)
                    self.assertTrue(status.startswith('Import failed:'), (structure, status))
                    self.assertEqual(self.export(page), exported)
                self.assertIn('Composition imported.', self.import_document(page, {**exported, 'live': {**base, 'structure': good}}))
                self.assertEqual(self.export(page)['live']['structure'], good)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page.wait_for_timeout(300)
                self.assertEqual(self.moves(frame), [], 'an import never moves the page by itself')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('JSON.stringify(window.fake.domOrder("cards")) === JSON.stringify(["card.d","card.c","card.b","card.a"])')
                self.assertEqual(errors, [])

    def test_a_bridge_without_order_ids_saves_no_dom_moves(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{ARRANGE}&noOrderIds=1')
                frame = self.wait_ready(page, 11)
                self.move_first(page, frame)
                self.assertNotIn('live', self.export(page))
                # The status says what really happened: nothing was saved, so Reapply cannot bring the move back.
                status = page.locator('#liveCodeStatus').inner_text()
                self.assertRegex(status, r'(?i)not saved')
                self.assertNotRegex(status, r'(?i)kept in Studio')
                self.assertNotRegex(status, r'(?i)Reapply puts it back')
                self.assertEqual(errors, [])

    def test_a_forced_move_is_kept_but_the_status_says_reapply_cannot_replay_a_guarded_move(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.framework = {cards: "react"}')
                self.select(page, frame, 'card.b')
                page.locator('#liveMoveStrategyDom').click()
                page.locator('#liveMoveLast').click()
                page.locator('#liveMoveGuard').wait_for(state='visible')
                page.locator('#liveMoveForce').click()
                page.wait_for_function('() => /Moved in the page markup/.test(document.querySelector("#liveCodeStatus").textContent)')
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assertRegex(status, r'(?i)kept in Studio')
                self.assertRegex(status, r'(?i)Reapply cannot replay a guarded move')
                self.assertNotRegex(status, r'(?i)Reapply puts it back')
                self.assertEqual(self.export(page)['live']['structure'][0]['ids'], ['card.a', 'card.c', 'card.d', 'card.b'])
                self.assertEqual(errors, [])

    # ---- what is saved: only a user's DOM move adds a container (K2, K3) ----------------------------------------
    def saved_cards(self, ids):
        return [{**self.CARDS, 'ids': ids}]

    def test_saved_dom_order_never_holds_what_the_import_would_refuse(self):
        """Studio's own export must import again: a name is clamped, an entry past an import limit is left out."""
        variants = {
            'a name over 200 characters': ("() => { window.fake.mapStructure = e => ({...e, name: 'N'.repeat(250)}); }", ['N' * 200]),
            'a selector over the limit': ("() => { window.fake.mapStructure = e => ({...e, selector: '#' + 'x'.repeat(2100)}); }", []),
            'an id over 300 characters': ("() => { window.fake.mapStructure = e => ({...e, orderIds: ['i'.repeat(301), ...e.orderIds.slice(1)]}); }", []),
            'more children than the import takes': ("() => { window.fake.mapStructure = e => ({...e,"
                " order: [...e.order, ...Array.from({length: 500}, (_, i) => 'n' + i)],"
                " orderIds: [...e.orderIds, ...Array.from({length: 500}, (_, i) => 'm' + i)]}); }", []),
            'an id another container already holds': ("() => { window.fake.extraStructure = [{containerKey: 'x', selector: '#again', stable: false,"
                " name: 'Again', html: '', order: ['c'], orderIds: ['card.c']}]; }", ['Cards']),
            'the same selector twice': ("() => { window.fake.extraStructure = [{containerKey: 'x', selector: '[data-design-id=\"cards\"]', stable: false,"
                " name: 'Twin', html: '', order: ['z'], orderIds: ['card.z']}]; }", ['Cards']),
        }
        for engine in ENGINES:
            for label, (script, names) in variants.items():
                with self.subTest(engine=engine, variant=label):
                    page, errors, frame = self.open_arrange(engine)
                    frame.evaluate(script)
                    self.move_first(page, frame)
                    exported = self.export(page)
                    saved = exported.get('live', {}).get('structure', [])
                    self.assertEqual([item['name'] for item in saved], names, label)
                    self.assertIn('Composition imported.', self.import_document(page, exported))
                    self.assertEqual(self.export(page).get('live'), exported.get('live'), 'Studio imports what it exported')
                    self.assertEqual(errors, [])

    def test_saved_dom_order_holds_at_most_one_hundred_containers(self):
        """The import takes 100 containers, so Studio saves no more; the page lists 99 or 100 older ones before the move."""
        script = ("(n) => { window.fake.priorStructure = Array.from({length: n}, (_, i) => ({containerKey: 'p' + i, selector: '#p' + i,"
                  " stable: false, name: 'P' + i, html: '', order: ['p' + i], orderIds: ['p.' + i]})); }")
        for engine in ENGINES:
            for older, saved in ((99, True), (100, False)):
                with self.subTest(engine=engine, older=older):
                    page, errors, frame = self.open_arrange(engine)
                    frame.evaluate(script, older)
                    self.move_first(page, frame)
                    live = self.export(page).get('live', {})
                    names = [item['name'] for item in live.get('structure', [])]
                    # Studio saves only what the user moved; the page's older containers are never adopted. The limit
                    # takes the first 100 the page reports, so the 101st (this move) is left out rather than saved
                    # into a document the import would refuse.
                    self.assertEqual(names, ['Cards'] if saved else [])
                    self.assertIn('Composition imported.', self.import_document(page, self.export(page)))
                    self.assertEqual(errors, [])

    def test_a_long_author_name_on_the_container_is_clamped_in_the_real_flow(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('document.getElementById("cards").setAttribute("data-design-name", "N".repeat(250))')
                self.move_first(page, frame)
                exported = self.export(page)
                self.assertEqual(exported['live']['structure'][0]['name'], 'N' * 200)
                self.assertIn('Composition imported.', self.import_document(page, exported))
                self.assertEqual(self.export(page)['live']['structure'], exported['live']['structure'])
                self.assertEqual(errors, [])

    def test_a_reset_never_saves_a_container_only_the_page_reordered(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.reverse("cards")')       # the page reorders Cards by itself: d c b a
                self.select(page, frame, 'card.b')
                page.locator('#liveResetTarget').click()
                self.wait_badge(page, r'^Live · rev 1$')
                self.assertEqual(len(frame.evaluate('window.fake.ledger().structure')), 1, 'the page still reports the container')
                self.assertNotIn('live', self.export(page), 'the user never moved anything')
                self.assertNotIn('Structure: Cards', self.code(page, 'Json'))
                self.assertEqual(errors, [])

    def test_connecting_to_a_page_that_reordered_a_container_adopts_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.reverse("cards")')
                self.watch_handled(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_handled(page, 2)           # bridge-ready, then ready
                self.assertEqual(len(frame.evaluate('window.fake.ledger().structure')), 1)
                self.assertNotIn('live', self.export(page))
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_accept_keeps_the_saved_containers_the_page_holds_and_never_adopts_page_only_ones(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                frame.evaluate('window.fake.reverse(window.fake.arrangementOf("side.x").containerKey)')   # page only
                frame.evaluate('window.fake.setTokens({"--other-font": "Georgia, serif"})')              # raises a conflict
                banner = page.locator('#liveReconnectBanner')
                self.watch_handled(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_handled(page, 2)
                banner.wait_for(state='visible')
                self.assertEqual(len(frame.evaluate('window.fake.ledger().structure')), 2)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(self.export(page)['live']['structure'], self.saved_cards(['card.c', 'card.a', 'card.b', 'card.d']),
                                 'Cards is what the page holds; the reordered Sidebar was never saved')
                self.assertEqual(errors, [])

    def test_the_banner_says_0_live_edits_only_when_the_page_holds_no_structure_either(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                doc = {**self.export(page), 'live': {'target': ARRANGE, 'revision': 0, 'overrides': {'hero.title': {'fontSize': 40}}}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertRegex(banner.inner_text(), r'0 live edits')
                frame.evaluate('window.fake.reverse("cards")')
                self.watch_handled(page)
                frame.evaluate('window.fake.reannounce()')
                self.wait_handled(page, 2)
                self.assertNotRegex(banner.inner_text(), r'0 live edits', 'the page holds a reordered container')
                self.assertEqual(errors, [])

    # ---- replay: what Reapply moves and what it says when it cannot (K4, K5, K8) --------------------------------
    def import_structure(self, page, structure, overrides=None):
        doc = {**self.export(page), 'live': {'target': ARRANGE, 'revision': 0, 'overrides': overrides or {}, 'structure': structure}}
        self.assertIn('Composition imported.', self.import_document(page, doc))
        page.locator('#liveReconnectBanner').wait_for(state='visible')

    def stopped(self, page):
        page.wait_for_function('() => /Reapply stopped/.test(document.querySelector("#liveReconnectText").textContent)')
        return ' '.join(page.locator('#liveReconnectText').inner_text().split())

    def test_reapply_with_no_container_for_the_selector_sends_nothing_and_says_why(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.import_structure(page, [{'selector': '#nowhere', 'name': 'Ghost', 'ids': ['card.b', 'card.a']}])
                page.locator('#liveReapply').click()
                text = self.stopped(page)
                self.assertIn('the page has no container for "Ghost"', text)
                self.assertRegex(text, r'Nothing was changed on the page')
                self.assertEqual(self.moves(frame), [])
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(len(self.export(page)['live']['structure']), 1, 'the saved order is kept')
                self.assertEqual(errors, [])

    def test_a_selector_that_now_matches_another_container_never_receives_the_saved_children(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                sidebar = frame.evaluate('window.fake.arrangementOf("side.x").containerKey')
                # The saved selector now names the Sidebar (the app changed); none of the saved children sit in it.
                selector = frame.evaluate('window.fake.arrangementOf("side.x").containerSelector')
                self.import_structure(page, [{'selector': selector, 'name': 'Cards', 'ids': ['card.d', 'card.c', 'card.b', 'card.a']}])
                page.locator('#liveReapply').click()
                text = self.stopped(page)
                self.assertIn('"Cards" no longer holds any of the elements Studio saved in it', text)
                self.assertRegex(text, r'Nothing was changed on the page')
                self.assertEqual(self.moves(frame), [], 'nothing was moved into the decoy')
                self.assertEqual(self.dom(frame, sidebar), ['side.x', 'side.y'])
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(errors, [])

    def test_a_saved_child_the_page_no_longer_has_gets_its_own_message(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.import_structure(page, self.saved_cards(['card.d', 'card.gone', 'card.c', 'card.b', 'card.a']))
                page.locator('#liveReapply').click()
                text = self.stopped(page)
                self.assertRegex(text, r'a saved child is no longer on the page \(card\.gone\)')
                self.assertNotRegex(text, r'(?i)changed it again|changing it again')
                self.assertRegex(text, r'All 4 Reapply steps were applied to the page')
                self.assertEqual(self.dom(frame), ['card.d', 'card.c', 'card.b', 'card.a'], 'what still exists was put in order')
                self.assertEqual(len(self.export(page)['live']['structure'][0]['ids']), 5, 'the saved order is kept')
                self.assertEqual(errors, [])

    def test_a_rejected_replay_names_the_element_the_guard_message_and_how_far_it_got(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate("""window.fake.guards = {'card.b': {guard: 'form-owner', overridable: false,
                    message: 'This move would take a form control out of its form.'}}""")
                self.import_structure(page, self.saved_cards(['card.d', 'card.c', 'card.b', 'card.a']),
                                      overrides={'hero.title': {'fontSize': 40}})
                page.locator('#liveReapply').click()
                text = self.stopped(page)
                self.assertIn('moving "Card B"', text)
                self.assertIn('This move would take a form control out of its form.', text)
                self.assertRegex(text, r'3 of 5 Reapply steps were already applied to the page')
                self.assertEqual(self.dom(frame), ['card.d', 'card.c', 'card.a', 'card.b'], 'the page is partly changed, as said')
                frame.wait_for_function('window.fake.styleOf("hero.title").fontSize === "40px"')
                self.assertEqual(self.export(page)['live']['structure'], self.saved_cards(['card.d', 'card.c', 'card.b', 'card.a']))
                self.assertEqual(errors, [])

    def test_reapply_names_the_container_when_a_page_puts_the_saved_order_back(self):
        """finishReapply checks the page's own report: every step was acknowledged, yet the order is not what was saved."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate('window.fake.undoMoves = true')
                saved = self.saved_cards(['card.d', 'card.c', 'card.b', 'card.a'])
                self.import_structure(page, saved)
                page.locator('#liveReapply').click()
                text = self.stopped(page)
                self.assertIn('the order of "Cards" on the page differs from the saved order even after Reapply moved its elements', text)
                self.assertRegex(text, r'All 4 Reapply steps were applied to the page')
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible(), 'the conflict stays open')
                self.assertEqual(self.export(page)['live']['structure'], saved)
                self.assertEqual(errors, [])

    def test_a_dom_move_triggers_no_auto_sync_and_the_file_only_gains_its_header_comment(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=ARRANGE, sync=True)
                frame = self.wait_ready(page, 11)
                page.wait_for_function('() => !document.querySelector("#liveCodeSync").disabled')
                with page.expect_response(lambda response: response.request.method == 'PUT'):
                    page.locator('#liveCodeAutoSync').check()               # auto-sync writes once when switched on
                before = self.puts[-1]['body']
                self.move_first(page, frame)
                page.wait_for_timeout(1000)                                # absence check: auto-sync waits 400 ms
                self.assertEqual(len(self.puts), 1, 'a DOM move changes no CSS, so nothing is written by itself')
                page.locator('#liveCodeAutoSync').uncheck()
                after = self.sync_file(page)
                comment = re.compile(r'\n\n/\* Structural DOM moves[^\n]*\*/')
                self.assertEqual(len(comment.findall(after)), 1)
                self.assertEqual(comment.sub('', after), before, 'the file differs only by the comment that points to the HTML tab')
                self.assertEqual(errors, [])

    def test_a_dom_move_status_says_it_adds_no_css_rules_to_the_file(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_first(page, frame)
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assertRegex(status, r'adds no CSS rules')
                self.assertNotRegex(status, r'(?i)writes nothing')
                self.assertEqual(errors, [])


class StudioSelectionOrderTests(ArrangeCase):
    """Studio's own re-select after a reset, restore or move never moves the selection back to an older target.

    The fake's `holdAll` keeps every reply in one ordered pipe, so the tests control the order in which Studio sees
    the acknowledgement and the later selection.
    """

    def held(self, frame):
        return frame.evaluate('window.fake.heldCount()')

    def wait_held(self, frame, count):
        frame.wait_for_function('(n) => window.fake.heldCount() >= n', arg=count)

    def release_one(self, page, frame):
        """Delivers the next held reply and waits until Studio has handled it."""
        before = page.evaluate('window.__handled')
        frame.evaluate('window.fake.release()')
        self.wait_handled(page, before + 1)

    def release_all(self, page, frame):
        """Delivers the pipe in order, including replies that Studio's own requests add while it drains."""
        for _ in range(20):
            if not self.held(frame):
                page.wait_for_timeout(60)  # absence check: nothing new was queued by what was just delivered
                if not self.held(frame):
                    return
            self.release_one(page, frame)
        self.fail('the pipe never drained')

    def shown(self, page):
        return page.locator('#liveTargetName').get_attribute('data-target-id')

    def selects(self, frame):
        return [item['data'] for item in self.received(frame, 'design:select')]

    def type_size(self, page, text):
        field = page.locator('#liveFontSize')
        field.click()
        page.keyboard.press('ControlOrMeta+a')
        page.keyboard.press('Backspace')
        page.keyboard.type(text, delay=60)

    def assert_next_edit_goes_to(self, page, frame, target_id, other_id):
        frame.evaluate('window.fake.holdAll = false')
        other_before = frame.evaluate('(id) => window.fake.styleOf(id).fontSize', other_id)
        sent = len(self.updates(frame))
        self.type_size(page, '23')
        frame.wait_for_function('(id) => window.fake.styleOf(id).fontSize === "23px"', arg=target_id)
        update = self.updates(frame)[-1]
        self.assertEqual((update['targetId'], update['patch']), (target_id, {'fontSize': 23}))
        self.assertTrue(all(item['targetId'] == target_id for item in self.updates(frame)[sent:]), 'no keystroke went to another target')
        self.assertEqual(frame.evaluate('(id) => window.fake.styleOf(id).fontSize', other_id), other_before, 'the other target is untouched')

    def reset_with_held_acknowledgement(self, page, frame):
        self.select(page, frame, 'card.a')
        self.watch_handled(page)
        frame.evaluate('window.fake.holdAll = true')
        page.locator('#liveResetTarget').click()        # the acknowledgement of this reset is held first
        self.wait_held(frame, 1)

    def test_a_target_picked_in_studio_before_the_acknowledgement_arrives_stays_selected(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.reset_with_held_acknowledgement(page, frame)
                page.locator('#liveSiblingList [data-sibling-id="card.b"]').focus()
                page.keyboard.press('Enter')                    # then the user picks Card B
                self.wait_held(frame, 2)
                self.release_one(page, frame)                   # the acknowledgement reaches Studio first
                self.wait_badge(page, r'^Live · rev 1$')
                self.release_all(page, frame)
                page.wait_for_function('() => document.querySelector("#liveTargetName").dataset.targetId === "card.b"')
                self.assertEqual(self.shown(page), 'card.b')
                # Studio never asked the page for the stale target again, and the page ends on the user's pick.
                self.assertEqual([item['targetId'] for item in self.selects(frame)], ['card.b'])
                self.assert_next_edit_goes_to(page, frame, 'card.b', 'card.a')
                self.assertEqual(errors, [])

    def test_a_click_in_the_page_before_the_acknowledgement_is_handled_stays_selected(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.reset_with_held_acknowledgement(page, frame)
                frame.evaluate('window.fake.select("card.b")')  # ... and the user clicks Card B in the page right after
                self.wait_held(frame, 2)
                self.release_one(page, frame)                   # Studio sees the acknowledgement, then the click
                self.wait_badge(page, r'^Live · rev 1$')
                self.release_all(page, frame)
                page.wait_for_function('() => document.querySelector("#liveTargetName").dataset.targetId === "card.b"')
                self.assertEqual(self.shown(page), 'card.b')
                # The refresh for the older target was answered after the click: the page is put back on the pick.
                self.assertEqual(self.selects(frame)[-1]['targetId'], 'card.b')
                self.assert_next_edit_goes_to(page, frame, 'card.b', 'card.a')
                self.assertEqual(errors, [])

    def test_a_pick_in_studio_while_the_refresh_is_in_flight_stays_selected(self):
        """The refresh was already sent when the user picks: its late answer must not bring the old target back."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.reset_with_held_acknowledgement(page, frame)
                self.release_one(page, frame)                   # the acknowledgement: Studio now asks for card.a again
                self.wait_held(frame, 1)                        # ... and the answer is held
                page.locator('#liveSiblingList [data-sibling-id="card.b"]').focus()
                page.keyboard.press('Enter')
                self.wait_held(frame, 2)
                self.release_one(page, frame)                   # the stale answer for card.a
                self.release_all(page, frame)
                page.wait_for_function('() => document.querySelector("#liveTargetName").dataset.targetId === "card.b"')
                self.assertEqual(self.selects(frame)[-1]['targetId'], 'card.b', 'the page is put back on the pick')
                self.assert_next_edit_goes_to(page, frame, 'card.b', 'card.a')
                self.assertEqual(errors, [])

    def test_back_while_the_refresh_is_in_flight_does_not_reopen_the_old_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.reset_with_held_acknowledgement(page, frame)
                self.release_one(page, frame)
                self.wait_held(frame, 1)                        # the refresh answer for card.a is held
                page.locator('[data-live-back]').click()
                self.wait_held(frame, 2)
                self.release_one(page, frame)                   # the stale answer arrives while Back is the user's choice
                self.assertEqual(page.locator('#liveTargetName').count(), 0, 'the inspector stays closed')
                self.release_all(page, frame)
                self.assertEqual(page.locator('#liveTargetName').count(), 0)
                self.assertEqual(self.selects(frame)[-1]['targetId'], None, 'the page ends with nothing selected too')
                self.assertEqual(errors, [])

    def test_a_click_in_the_page_within_one_round_trip_of_the_realign_is_not_overridden(self):
        """Studio's own corrective select is tracked too: a click that reached the page before it was handled wins."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.reset_with_held_acknowledgement(page, frame)
                frame.evaluate('window.fake.select("card.b")')  # the user clicks Card B in the page
                self.wait_held(frame, 2)
                self.release_one(page, frame)                   # acknowledgement: Studio asks for card.a again (refresh)
                self.release_one(page, frame)                   # the click: Card B
                self.wait_held(frame, 1)                        # the refresh answer (card.a) is in the pipe
                self.release_one(page, frame)                   # superseded: Studio puts the page back on Card B (realign)
                self.wait_held(frame, 1)                        # the page answers the realign
                frame.evaluate('window.fake.select("card.c", true)')   # a click that happened before the realign was handled
                self.release_all(page, frame)
                page.wait_for_function('() => document.querySelector("#liveTargetName").dataset.targetId === "card.c"')
                self.assertEqual(self.shown(page), 'card.c', 'the later click is not overridden by the answer to the realign')
                self.assertEqual(self.selects(frame)[-1]['targetId'], 'card.c', 'the page agrees')
                self.assert_next_edit_goes_to(page, frame, 'card.c', 'card.b')
                self.assertEqual(errors, [])

    def test_the_refresh_still_happens_when_nothing_else_was_picked(self):
        """Characterization: after a reset the selected target is asked for again, and the fresh manifest is shown."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.a')
                before = len(self.received(frame, 'design:select'))
                page.locator('#liveResetTarget').click()
                self.wait_badge(page, r'^Live · rev 1$')
                frame.wait_for_function('(n) => window.__received.filter(i => i.data && i.data.type === "design:select").length > n', arg=before)
                self.assertEqual(self.received(frame, 'design:select')[-1]['data']['targetId'], 'card.a')
                self.assertEqual(self.shown(page), 'card.a')
                self.assertEqual(errors, [])


class StudioFreeFontGateTests(LiveCase):
    """Importing or applying a document is not asking for free fonts (D032): only Load free fonts or an inspector pick is."""
    FRAUNCES = '"Fraunces", serif'

    def test_imported_override_fonts_wait_for_the_users_ask(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                doc = {**self.export(page), 'live': {'target': FAKE, 'revision': 0, 'overrides': {'hero.title': {'fontFamily': self.FRAUNCES}}}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                css = self.code(page, 'Css')
                self.assertNotIn('@import', css)
                self.assertIn('font-family: "Fraunces", serif !important;', css, 'the saved override itself is still shown')
                text = ' '.join(banner.inner_text().split())
                self.assertIn('Library fonts are not loaded until you press Load free fonts, which contacts Google Fonts;', text)
                self.assertIn("until then the page shows each font stack's fallback", text)
                self.assertNotIn('keeps its own fonts', text, 'the page shows the override stack, not its own fonts')
                # Sync to file writes the override but no @import (the page would otherwise contact Google Fonts on load).
                written = self.sync_file(page)
                self.assertIn('font-family: "Fraunces", serif !important;', written)
                self.assertNotIn('googleapis', written)
                self.assertRegex(page.locator('#liveCodeStatus').inner_text(), r"Load free fonts.*fallback")
                # Reapply sends the family without a stylesheet; the target loads nothing.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.ledger().targets.some(t => t.targetId === "hero.title")')
                self.assertEqual(self.updates(frame)[-1]['patch'], {'fontFamily': self.FRAUNCES})
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                # The user asks: now the sheet appears in the CSS, in the synced file and in the next Reapply.
                frame.evaluate('location.reload()')
                banner.wait_for(state='visible')
                frame = self.frame(page)
                self.wait_connected(page)
                page.locator('#loadFreeFonts').click()
                self.assertTrue(self.code(page, 'Css').startswith(f'@import url("{FREE_URLS["fraunces"]}");'))
                self.assertIn(f'@import url("{FREE_URLS["fraunces"]}");', self.sync_file(page))
                self.assertNotIn('Load free fonts', ' '.join(banner.inner_text().split()), 'the wording is only true before the ask')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.ledger().imports.length === 1')
                self.assertEqual(self.updates(frame)[-1]['patch'], {'fontFamily': self.FRAUNCES, 'fontStylesheet': FREE_URLS['fraunces']})
                self.assertEqual(errors, [])


class StudioCompositionFontTests(LiveCase):
    """Sync to Live App sends the stylesheets for the library fonts it sends (once the user has asked for free fonts)."""
    SHEET = re.compile(r'^https://fonts\.googleapis\.com/css2\?family=[A-Za-z0-9+:@;.,_-]+&display=swap$')
    # The default composition's families, in slot order: Fraunces, Instrument Serif, Inter, IBM Plex Mono.
    EXPECTED = ['Fraunces', 'Instrument+Serif', 'Inter', 'IBM+Plex+Mono']

    def sheets_sent(self, frame):
        return [update['patch'].get('fontStylesheets') for update in self.updates(frame) if 'targetId' not in update]

    def sync(self, page):
        page.locator('#btnSyncToApp').click()
        self.wait_badge(page, r'^Live · rev \d+$')

    def test_sync_sends_the_library_fonts_stylesheets_and_the_target_shows_them_as_imports(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()    # the user asks for free fonts
                self.sync(page)
                sent = self.sheets_sent(frame)
                self.assertEqual(len(sent), 1)
                self.assertTrue(all(self.SHEET.match(url) for url in sent[0]), sent)
                self.assertEqual([url.split('family=')[1].split(':')[0].split('&')[0] for url in sent[0]], self.EXPECTED)
                # What the target then reports, and what the code panel offers for the file.
                imports = frame.evaluate('window.fake.ledger().imports')
                self.assertEqual(imports, sent[0])
                css = self.code(page, 'Css')
                self.assertTrue(css.startswith(f'@import url("{sent[0][0]}");\n'), css[:200])
                for url in sent[0]:
                    self.assertIn(f'@import url("{url}");', css)
                self.assertEqual(errors, [])

    def test_without_the_users_ask_no_stylesheet_is_sent_and_the_status_says_why(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.sync(page)
                self.assertEqual(self.sheets_sent(frame), [None], 'the key is absent: the update carries tokens and slots only')
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                self.assertNotIn('@import', self.code(page, 'Css'))
                status = page.locator('#composerStatus').inner_text()
                self.assertRegex(status, r"Load free fonts.*fallback")
                self.assertEqual(errors, [])

    def test_loading_free_fonts_after_a_sync_resends_the_linked_composition_with_its_stylesheets(self):
        """The Composer promises the fonts load once the user presses Load free fonts; the linked composition must deliver."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.sync(page)
                self.assertEqual(self.sheets_sent(frame), [None], 'no consent yet: the first update carries no stylesheets')
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                page.locator('#loadFreeFonts').click()
                frame.wait_for_function('window.fake.ledger().imports.length > 0')
                sent = self.sheets_sent(frame)
                self.assertEqual(len(sent), 2, 'exactly one more composition update, sent by the consent')
                self.assertEqual([url.split('family=')[1].split(':')[0].split('&')[0] for url in sent[1]], self.EXPECTED)
                self.assertTrue(all(self.SHEET.match(url) for url in sent[1]), sent[1])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), sent[1], 'the page holds the links')
                self.assertEqual(errors, [])

    def test_loading_free_fonts_without_a_sync_sends_nothing_to_the_page(self):
        """Consent alone must not push Studio's composition into the app (Rule 6)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()
                self.assertTrue(page.evaluate('() => document.getElementById("freeFontStatus").textContent.length > 0'))
                page.wait_for_timeout(400)                # absence window: a stray send would arrive well within it
                self.assertEqual([u for u in self.updates(frame) if 'targetId' not in u], [])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                self.assertEqual(errors, [])

    def test_reapply_sends_the_stylesheets_for_the_saved_token_fonts_and_the_saved_css_imports_them(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()
                self.sync(page)
                tokens = self.export(page)['live']['tokens']
                self.assertTrue(tokens)
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.frame(page)
                self.wait_connected(page)
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                # The saved state alone already lists the fonts its tokens use, so a Sync now keeps them.
                saved_css = self.code(page, 'Css')
                self.assertRegex(saved_css, r'@import url\("https://fonts\.googleapis\.com/css2\?family=')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.ledger().imports.length > 0')
                sent = [u for u in self.sheets_sent(frame) if u]
                self.assertTrue(sent, 'Reapply carries the sheets with the tokens')
                self.assertTrue(all(self.SHEET.match(url) for url in sent[-1]))
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), sent[-1])
                self.assertEqual(errors, [])

    def import_saved_tokens(self, page, tokens):
        doc = {**self.export(page), 'live': {'target': FAKE, 'revision': 0, 'overrides': {}, 'tokens': tokens}}
        self.assertIn('Composition imported.', self.import_document(page, doc))
        page.locator('#liveReconnectBanner').wait_for(state='visible')

    def test_reapply_without_the_ask_carries_no_stylesheet_key_and_loads_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.import_saved_tokens(page, {'--font-display': '"Fraunces", serif'})
                self.assertNotIn('@import', self.code(page, 'Css'))
                page.locator('#liveReapply').click()
                page.locator('#liveReconnectBanner').wait_for(state='hidden')
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(len(composition), 1)
                self.assertEqual(composition[0]['patch'], {'tokens': {'--font-display': '"Fraunces", serif'}}, 'no fontStylesheets key')
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), [])
                self.assertEqual(frame.evaluate('window.fake.ledger().tokens'), {'--font-display': '"Fraunces", serif'})
                self.assertEqual(errors, [])

    def test_reapply_after_a_re_hello_keeps_the_sheets_the_page_still_holds(self):
        """A re-hello ends the composition link but not the page's sheets: Reapply must not release a slot-only one."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()
                self.sync(page)
                synced = self.sheets_sent(frame)[0]
                banner = page.locator('#liveReconnectBanner')
                self.watch_handled(page)
                frame.evaluate('window.fake.setTokens({"--extra-font": "Georgia, serif"})')   # a token Studio does not save
                frame.evaluate('window.fake.reannounce()')
                self.wait_handled(page, 2)
                banner.wait_for(state='visible')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                self.assertEqual(sorted(self.sheets_sent(frame)[-1]), sorted(synced), 'the same complete set a Sync sends')
                self.assertEqual(sorted(frame.evaluate('window.fake.ledger().imports')), sorted(synced), 'no sheet was released')
                self.assertEqual(errors, [])

    def test_reapply_with_the_ask_sends_the_complete_set_so_a_sheet_only_a_slot_uses_stays(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#loadFreeFonts').click()
                self.sync(page)
                synced = self.sheets_sent(frame)[0]
                self.assertEqual(len(synced), 4)
                # A saved override the page lacks opens a conflict without a reload (the composition stays linked).
                self.watch_handled(page)
                doc = {**self.export(page), 'live': {'target': FAKE, 'revision': 0, 'overrides': {'hero.title': {'fontSize': 40}}}}
                self.assertIn('Composition imported.', self.import_document(page, doc))
                self.wait_handled(page, 1)                 # the import streams the composition; the page acknowledges it
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                # Another editor then adds a token; Studio learns of it from the next acknowledgement.
                frame.evaluate('window.fake.setTokens({"--extra-font": "Georgia, serif"})')
                self.select(page, frame, 'hero.lead')
                self.set_value(page, '#liveFontSize', 21)
                self.wait_badge(page, r'^Live · rev \d+$')
                frame.wait_for_function('window.fake.styleOf("hero.lead").fontSize === "21px"')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                reapply = [u['patch'] for u in self.updates(frame) if 'targetId' not in u and 'slots' not in u['patch']]
                self.assertEqual(len(reapply), 1, 'the tokens-only update of Reapply')
                self.assertEqual(sorted(reapply[0]['fontStylesheets']), sorted(synced), 'the same complete set a Sync sends')
                self.assertNotIn('--extra-font', frame.evaluate('window.fake.ledger().tokens'))
                self.assertEqual(sorted(frame.evaluate('window.fake.ledger().imports')), sorted(synced), 'no sheet was released')
                self.assertEqual(errors, [])

    def test_a_typed_tracking_value_with_float_noise_is_rounded_before_it_is_sent(self):
        """0.1234 em is 123.4 thousandths; 0.1234 * 1000 alone is 123.39999999999999."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
                field = page.locator('#slotInspector [data-bind="tracking"]')
                field.click()
                page.keyboard.press('ControlOrMeta+a')
                page.keyboard.press('Backspace')
                page.keyboard.type('0.1234', delay=60)
                self.assertEqual(field.input_value(), '0.1234')
                page.locator('#viewTargetApp').click()
                self.sync(page)
                composition = [u for u in self.updates(frame) if 'targetId' not in u]
                self.assertEqual(composition[-1]['patch']['slots'][0]['tracking'], 123.4)
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
