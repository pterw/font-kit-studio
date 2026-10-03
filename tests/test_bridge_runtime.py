"""Runtime tests for fontkit-bridge.js against the Protocol contract.

The Studio side is a small fixture host (tests/fixtures/bridge/host.html) served at
http://studio.test; the target page loads the real bridge from http://target.test.
Both are fake origins routed by Playwright, so postMessage is genuinely cross-origin.
"""

import json
import re
import unittest
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from support import ENGINES, REPO, launch, route_virtual_origins

FIXTURES = REPO / 'tests' / 'fixtures' / 'bridge'
STUDIO = 'http://studio.test'
TARGET = 'http://target.test'
EVIL = 'http://evil.test'
TARGET_PAGE = f'{TARGET}/tests/fixtures/bridge/target.html'
RESTRICTED_PAGE = f'{TARGET}/tests/fixtures/bridge/target-restricted.html'
RESTRICTED_UPPER_PAGE = f'{TARGET}/tests/fixtures/bridge/target-restricted-upper.html'
MANUAL_PAGE = f'{TARGET}/tests/fixtures/bridge/target-manual.html'
OPTIONS_PAGE = f'{TARGET}/tests/fixtures/bridge/target-options.html'
CONSTRUCTED_PAGE = f'{TARGET}/tests/fixtures/bridge/target-constructed.html'
ARRANGE_PAGE = f'{TARGET}/tests/fixtures/bridge/target-arrange.html'
SPA_PAGE = f'{TARGET}/tests/fixtures/bridge/target-spa.html'
TWICE_PAGE = f'{TARGET}/tests/fixtures/bridge/target-twice.html'
DEFERRED_PAGE = f'{TARGET}/tests/fixtures/bridge/target-deferred.html'
DEEP_PAGE = f'{TARGET}/tests/fixtures/bridge/target-deep.html'
ROOT_STYLE_PAGE = f'{TARGET}/tests/fixtures/bridge/target-root-style.html'

TITLE = 'landing.hero.title'
LEAD = 'landing.hero.lead'
CTA = 'landing.hero.cta'
BADGE = 'landing.stat.badge'
MARK = 'landing.mark'
PHOTO = 'landing.photo'
SLOT = 'landing.slot'
TITLE_STYLE = 'color: rgb(10, 20, 30); margin-top: 8px'

# Collects uncaught errors in every frame (the bridge runs inside the iframe).
ERROR_PROBE = (
    "window.__errors = [];"
    "window.addEventListener('error', (e) => window.__errors.push(String(e.message)));"
)

# Finds an element by exact data-design-id without building a selector.
BY_ID = "(id) => [...document.querySelectorAll('[data-design-id]')].find((el) => el.getAttribute('data-design-id') === id)"


class BridgeCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browsers = {engine: launch(cls.runtime, engine) for engine in ENGINES}

    @classmethod
    def tearDownClass(cls):
        for browser in cls.browsers.values():
            browser.close()
        cls.runtime.stop()

    # -- harness -----------------------------------------------------------

    def open(self, engine, host=STUDIO, target=TARGET_PAGE):
        context = self.browsers[engine].new_context(viewport={'width': 1200, 'height': 900})
        self.addCleanup(context.close)
        context.add_init_script(ERROR_PROBE)
        route_virtual_origins(context, {STUDIO: FIXTURES, EVIL: FIXTURES, TARGET: REPO})
        self.block_font_hosts(context)
        page = context.new_page()
        page.goto(f'{host}/host.html?target={target}')
        page.wait_for_function(
            "log.some((e) => e.fromTarget && e.data && e.data.type === 'design:bridge-ready')")
        frame = next(f for f in page.frames if f.url.startswith(TARGET))
        return page, frame

    def block_font_hosts(self, context):
        """Never touch the network: font stylesheets are fulfilled with empty CSS and recorded."""
        self.font_requests = []

        def fulfil(route, request=None):
            self.font_requests.append(route.request.url)
            route.fulfill(status=200, content_type='text/css', body='')

        context.route(re.compile(r'^https://(fonts\.googleapis\.com|use\.typekit\.net)/'), fulfil)

    def hello(self, page, session='s1'):
        ready = page.evaluate('(s) => hello(s)', session)
        self.assertEqual(ready.get('type'), 'design:ready', ready)
        return ready

    def request(self, page, msg):
        return page.evaluate('(m) => request(m)', msg)

    def update(self, page, target_id, patch, **extra):
        return self.request(page, {'type': 'design:update', 'targetId': target_id, 'patch': patch, **extra})

    def applied(self, page, target_id, patch, **extra):
        reply = self.update(page, target_id, patch, **extra)
        self.assertEqual(reply.get('type'), 'design:applied', reply)
        return reply

    def control(self, page, msg):
        page.evaluate('(m) => control(m)', msg)

    def mark(self, page):
        return page.evaluate('log.length')

    def messages(self, page, kind, start=0):
        return page.evaluate('([t, s]) => messages(t, s)', [kind, start])

    def wait_message(self, page, kind, start=0, where='true', timeout=3000):
        """Wait for a target message of a type; `where` is a JS expression over `d`."""
        return page.evaluate(
            f'([t, s, ms]) => waitFor((d) => d && d.type === t && ({where}), s, ms)'
            ".catch(() => ({type: 'timeout'}))",
            [kind, start, timeout])

    def element(self, frame, design_id, script):
        """Evaluate `script` (a function of el) against the element with design_id."""
        return frame.evaluate(f'([id]) => ({script})(({BY_ID})(id))', [design_id])

    def text(self, frame, design_id):
        return self.element(frame, design_id, '(el) => el.textContent')

    def computed(self, frame, design_id, prop):
        return self.element(frame, design_id, f'(el) => getComputedStyle(el).{prop}')

    def inline(self, frame, design_id, prop):
        return self.element(
            frame, design_id,
            f"(el) => [el.style.getPropertyValue('{prop}'), el.style.getPropertyPriority('{prop}')]")

    def style_attr(self, frame, design_id):
        return self.element(frame, design_id, "(el) => el.getAttribute('style')")

    def errors(self, frame):
        return frame.evaluate('window.__errors')

    def entry(self, changes, target_id):
        return next((e for e in (changes or {}).get('targets', []) if e['targetId'] == target_id), None)

    def target_by_text(self, ready, text):
        return next(t for t in ready['targets'] if t.get('text') == text)


class ConfirmedDefectTests(BridgeCase):
    """Regression tests for the defects recorded in the v0.2.0 plan baseline."""

    def test_restore_text_restores_original_text_without_throwing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'text': 'Edited title'})
                self.assertEqual(self.text(frame, TITLE), 'Edited title')

                reply = self.request(page, {'type': 'design:restore-text'})
                self.assertEqual(self.errors(frame), [])
                self.assertEqual(reply.get('type'), 'design:applied', reply)
                self.assertEqual(reply.get('targetId'), 'global')
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')

    def test_original_text_is_captured_once_across_rediscovery(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'text': 'First edit'})
                self.applied(page, TITLE, {'text': 'Second edit'})
                # Force rediscovery: a DOM mutation plus a fresh handshake.
                frame.evaluate("document.querySelector('main').append(Object.assign("
                               "document.createElement('h2'), {textContent: 'Late heading'}))")
                page.wait_for_timeout(250)
                ready = self.hello(page, 's2')
                entry = self.entry(ready.get('changes'), TITLE)
                self.assertIsNotNone(entry, ready.get('changes'))
                self.assertEqual(entry['originalText'], 'Make type sing')
                self.assertEqual(entry['text'], 'Second edit')

                reply = self.update(page, TITLE, {'text': None})
                self.assertEqual(reply.get('type'), 'design:applied', reply)
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')

    def test_clicks_are_not_intercepted_before_hello(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.locator(f'[data-design-id="{CTA}"]').click()
                self.assertEqual(frame.evaluate('location.hash'), '#clicked')
                frame.locator('#counter').click()
                self.assertEqual(frame.evaluate("document.querySelector('#counter').dataset.count"), '1')
                box = frame.locator(f'[data-design-id="{TITLE}"]').bounding_box()
                page.mouse.move(box['x'] + 10, box['y'] + 10)
                page.wait_for_timeout(250)
                kinds = page.evaluate('log.filter((e) => e.fromTarget).map((e) => e.data.type)')
                self.assertEqual(kinds, ['design:bridge-ready'])

    def test_sibling_frame_cannot_open_or_hijack_the_session(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                page.evaluate('(u) => addEvil(u)', f'{EVIL}/evil.html')
                evil = next(f for f in page.frames if f.url.startswith(EVIL))
                evil.evaluate("sendToTarget({type: 'design:hello', protocolVersion: 1, sessionId: 'evil'})")
                # Even with the real session id, a foreign source must be ignored.
                evil.evaluate(f"""sendToTarget({{type: 'design:update', protocolVersion: 1, sessionId: 's1',
                    requestId: 'x1', baseRevision: 0, targetId: '{TITLE}', patch: {{text: 'pwned', fontSize: 99}}}})""")
                evil.evaluate(f"""sendToTarget({{type: 'design:update', protocolVersion: 1, sessionId: 's1',
                    requestId: 'x2', baseRevision: 0, patch: {{tokens: {{'--font-display': 'Impact'}},
                    slots: [{{id: 'e', targetId: '{TITLE}', type: 'text', size: 99, text: 'pwned', textTouched: true}}]}}}})""")
                evil.evaluate("sendToTarget({type: 'design:restore-text', protocolVersion: 1, sessionId: 's1'})")
                page.wait_for_timeout(400)
                self.assertEqual(evil.evaluate('received'), [])
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '40px')
                self.assertEqual(self.messages(page, 'design:applied'), [])
                # The legitimate session is unaffected.
                reply = self.applied(page, TITLE, {'fontSize': 41})
                self.assertEqual(reply['revision'], 1)

    def test_wrong_session_or_protocol_version_is_ignored(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                base = {'type': 'design:update', 'requestId': 'w', 'baseRevision': 0,
                        'targetId': TITLE, 'patch': {'text': 'wrong'}}
                page.evaluate('(m) => send(m)', {**base, 'requestId': 'w1', 'protocolVersion': 1, 'sessionId': 's2'})
                page.evaluate('(m) => send(m)', {**base, 'requestId': 'w2', 'protocolVersion': 2, 'sessionId': 's1'})
                page.evaluate('(m) => send(m)', {**base, 'requestId': 'w3', 'protocolVersion': 1})
                page.wait_for_timeout(300)
                self.assertEqual(self.messages(page, 'design:applied'), [])
                self.assertEqual(self.messages(page, 'design:rejected'), [])
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')

                # A later hello from the same Studio replaces the session.
                self.hello(page, 's2')
                page.evaluate('(m) => send(m)', {**base, 'requestId': 'w4', 'protocolVersion': 1, 'sessionId': 's1'})
                page.wait_for_timeout(200)
                self.assertEqual(self.messages(page, 'design:applied'), [])
                reply = self.applied(page, TITLE, {'text': 'right'})
                self.assertEqual(reply['sessionId'], 's2')
                self.assertEqual(self.text(frame, TITLE), 'right')

    def test_allowed_origins_attribute_restricts_who_can_say_hello(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, _ = self.open(engine, host=EVIL, target=RESTRICTED_PAGE)
                reply = page.evaluate('() => hello("s1")')
                self.assertEqual(reply['type'], 'timeout')
                self.assertEqual(self.messages(page, 'design:ready'), [])

                page, _ = self.open(engine, host=STUDIO, target=RESTRICTED_PAGE)
                ready = self.hello(page)
                self.assertEqual([t['id'] for t in ready['targets'] if t['stable']], ['restricted.title'])


class HandshakeTests(BridgeCase):
    def test_bridge_ready_carries_no_page_data_and_ready_describes_targets(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                first = page.evaluate('log.find((e) => e.fromTarget)')
                self.assertEqual(first['data'], {'type': 'design:bridge-ready', 'protocolVersion': 1})
                self.assertEqual(first['origin'], TARGET)

                ready = self.hello(page)
                self.assertEqual(ready['protocolVersion'], 1)
                self.assertEqual(ready['sessionId'], 's1')
                self.assertEqual(ready['revision'], 0)
                self.assertEqual(ready['capabilities'], {
                    'inspect': True, 'patch': True, 'typography': True,
                    'text': True, 'tokens': True, 'reset': True})
                self.assertEqual(ready['viewport'], {'width': 1000, 'height': 600})
                self.assertIn('Georgia', ready['tokens']['css']['--font-display'])
                self.assertEqual(ready['tokens']['css']['--brand-ink'], '#111111')
                self.assertEqual(ready['changes'], {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})

                ids = [t['id'] for t in ready['targets']]
                self.assertEqual(len(ids), len(set(ids)))
                by_id = {t['id']: t for t in ready['targets']}
                title = by_id[TITLE]
                self.assertEqual(set(title), {'id', 'role', 'name', 'kind', 'tag', 'stable', 'selector',
                                              'editable', 'arrangement', 'text', 'computed'})
                self.assertRegex(title['arrangement']['containerKey'], r'^container:\d+$')
                self.assertEqual(title['arrangement']['containerSelector'], 'main:nth-of-type(1)')
                self.assertNotIn('siblings', title['arrangement'])
                self.assertLess(title['arrangement']['index'], title['arrangement']['count'])
                self.assertEqual((title['role'], title['name'], title['kind'], title['tag'], title['stable']),
                                 ('display', 'Hero title', 'text', 'h1', True))
                self.assertEqual(title['selector'], '[data-design-id="landing.hero.title"]')
                self.assertEqual(title['editable'], {'text': True, 'typography': True, 'color': True, 'alignment': True})
                self.assertEqual(title['text'], 'Make type sing')
                self.assertEqual(set(title['computed']), {'fontFamily', 'fontSize', 'fontWeight', 'lineHeight',
                                                          'letterSpacing', 'color', 'textAlign', 'textTransform'})
                self.assertEqual(title['computed']['fontSize'], '40px')
                self.assertEqual(by_id[BADGE]['constraints'], {'fontWeights': [400, 600, 800]})
                self.assertEqual(by_id[MARK]['kind'], 'image')
                self.assertFalse(by_id[MARK]['editable']['text'])
                self.assertFalse(by_id[MARK]['editable']['typography'])
                self.assertEqual(by_id['quote"back\\slash']['selector'], '[data-design-id="quote\\"back\\\\slash"]')

                card = self.target_by_text(ready, 'Card two')
                self.assertFalse(card['stable'])
                self.assertTrue(card['id'].startswith('auto:'))
                self.assertEqual(card['selector'],
                                 'main:nth-of-type(1) > section.cards:nth-of-type(1) > article.card:nth-of-type(2) > h3:nth-of-type(1)')
                self.assertEqual(self.target_by_text(ready, 'Features')['selector'],
                                 '#top > nav:nth-of-type(1) > a.nav-link:nth-of-type(1)')
                self.assertEqual(self.target_by_text(ready, 'Footer note')['selector'], '#footer-note')
                self.assertEqual(self.target_by_text(ready, 'Count')['selector'], '#counter')

                # Every selector resolves to exactly its own element.
                for target in ready['targets']:
                    hits = frame.evaluate(
                        "(s) => [...document.querySelectorAll(s)].map((el) => el.getAttribute('data-design-id'))",
                        target['selector'])
                    self.assertEqual(hits, [target['id']], target)
                origins = page.evaluate('[...new Set(log.filter((e) => e.fromTarget).map((e) => e.origin))]')
                self.assertEqual(origins, [TARGET])


    def test_first_hello_discovers_targets_once(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const bridge = window.__fontkitBridge;
                    const original = bridge.discoverTargets.bind(bridge);
                    window.__discoveries = 0;
                    bridge.discoverTargets = () => { window.__discoveries += 1; return original(); };
                }""")
                self.hello(page)
                self.assertEqual(frame.evaluate('window.__discoveries'), 1)
                self.hello(page, 's2')
                self.assertEqual(frame.evaluate('window.__discoveries'), 2)


class InitOptionTests(BridgeCase):
    """allowedOrigins must hold however the page configures the bridge."""

    def assert_restricted(self, engine, target):
        page, frame = self.open(engine, host=EVIL, target=target)
        self.assertEqual(page.evaluate('() => hello("s1")')['type'], 'timeout')
        self.assertEqual(self.messages(page, 'design:ready'), [])
        page, frame = self.open(engine, host=STUDIO, target=target)
        self.hello(page)
        self.assertEqual(self.messages(page, 'design:ready', 0)[0]['sessionId'], 's1')
        self.assertEqual(len(self.messages(page, 'design:ready')), 1)
        return page, frame

    def test_auto_init_opt_out_with_manual_init(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                _, frame = self.assert_restricted(engine, MANUAL_PAGE)
                self.assertTrue(frame.evaluate('window.__mine === window.__fontkitBridge'))
                # A later init with different options warns and returns the same instance.
                result = frame.evaluate("""() => {
                    const warnings = [];
                    const warn = console.warn;
                    console.warn = (...args) => warnings.push(args.join(' '));
                    try {
                        const again = initFontKitBridge({ allowedOrigins: ['*'] });
                        const plain = initFontKitBridge();
                        return { same: again === window.__mine && plain === window.__mine, warnings };
                    } finally {
                        console.warn = warn;
                    }
                }""")
                self.assertTrue(result['same'])
                self.assertEqual(len(result['warnings']), 1, result)

    def test_global_options_are_used_by_auto_init(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assert_restricted(engine, OPTIONS_PAGE)

    def test_constructed_instance_claims_the_global_slot(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                _, frame = self.assert_restricted(engine, CONSTRUCTED_PAGE)
                self.assertTrue(frame.evaluate('window.__mine === window.__fontkitBridge'))


class OriginListTests(BridgeCase):
    """Origins are compared case-insensitively, and initFontKitBridge narrows a running bridge like the constructor."""
    INIT = """(options) => {
        const seen = [];
        const warn = console.warn;
        console.warn = (...args) => seen.push(args.join(' '));
        const first = window.__fontkitBridge;
        const again = initFontKitBridge(options);
        console.warn = warn;
        return { same: again === first, seen, origins: first.allowedOrigins, session: first.sessionId };
    }"""

    def test_an_allowed_origin_written_in_mixed_case_still_matches_the_lower_case_origin_the_browser_reports(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, host=EVIL, target=RESTRICTED_UPPER_PAGE)
                self.assertEqual(page.evaluate('() => hello("s1")')['type'], 'timeout', 'a foreign origin is still refused')
                page, frame = self.open(engine, host=STUDIO, target=RESTRICTED_UPPER_PAGE)
                self.hello(page)
                self.assertEqual(self.applied(page, 'restricted.title', {'fontSize': 22})['type'], 'design:applied')
                self.assertEqual(frame.evaluate('window.__fontkitBridge.allowedOrigins'),
                                 ['http://studio.test', 'http://localhost:4173'])

    def test_a_mixed_case_list_narrows_like_its_lower_case_twin(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=RESTRICTED_PAGE)
                self.hello(page)
                call = RepeatedConstructionTests.CALL
                # Same origin, other spelling: applied (it narrows nothing further), and the session continues.
                result = frame.evaluate(call, {'allowedOrigins': ['HTTP://STUDIO.test/']})
                self.assertEqual(result['origins'], ['http://studio.test'])
                self.assertEqual(result['session'], 's1')
                self.assertIn('allowedOrigins narrowed to http://studio.test', result['seen'][0])
                # A different origin in capitals is still a wider list and is ignored.
                result = frame.evaluate(call, {'allowedOrigins': ['HTTP://EVIL.TEST']})
                self.assertEqual(result['origins'], ['http://studio.test'])
                self.assertIn('allowedOrigins ignored', result['seen'][0])

    def test_init_narrows_an_open_bridge_and_a_foreign_origin_is_then_refused(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, host=EVIL)
                self.assertIsNone(frame.evaluate('window.__fontkitBridge.allowedOrigins'), 'the bridge starts open')
                result = frame.evaluate(self.INIT, {'allowedOrigins': ['HTTP://Studio.test']})
                self.assertTrue(result['same'])
                self.assertEqual(result['origins'], ['http://studio.test'])
                self.assertEqual(len(result['seen']), 1)
                self.assertIn('allowedOrigins narrowed to http://studio.test', result['seen'][0])
                # The page that embeds the bridge is not an allowed Studio any more.
                self.assertEqual(page.evaluate('() => hello("s1")')['type'], 'timeout')
                self.assertEqual(self.messages(page, 'design:ready'), [])
                self.assertEqual(self.errors(frame), [])

    def test_init_narrows_a_running_connected_bridge_and_never_widens_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'fontSize': 55})
                # Open -> two origins is a narrowing; the pinned Studio is still allowed.
                result = frame.evaluate(self.INIT, {'allowedOrigins': ['http://studio.test', 'http://third.test']})
                self.assertEqual((result['origins'], result['session']), (['http://studio.test', 'http://third.test'], 's1'))
                for wider in (['*'], '*', ['http://studio.test', 'http://third.test', 'http://fourth.test']):
                    with self.subTest(wider=wider):
                        before = frame.evaluate('window.__fontkitBridge.allowedOrigins')
                        result = frame.evaluate(self.INIT, {'allowedOrigins': wider})
                        self.assertEqual(result['origins'], before)
                        self.assertEqual(len(result['seen']), 1)
                        self.assertIn('allowedOrigins ignored', result['seen'][0])
                result = frame.evaluate(self.INIT, {'allowedOrigins': ['http://studio.test']})
                self.assertEqual((result['origins'], result['session']), (['http://studio.test'], 's1'))
                self.assertEqual(self.applied(page, TITLE, {'fontSize': 60})['revision'], 2)
                # Narrowed away from the pinned Studio: its session ends, like with the constructor.
                result = frame.evaluate(self.INIT, {'allowedOrigins': []})
                self.assertEqual((result['origins'], result['session']), ([], None))
                self.assertEqual(self.update(page, TITLE, {'fontSize': 70})['type'], 'timeout')
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '60px')
                # Without the option nothing changes, and the old "options ignored" warning stays.
                result = frame.evaluate(self.INIT, {'enableHighlightOverlay': True})
                self.assertEqual(len(result['seen']), 1)
                self.assertIn('ignored', result['seen'][0])
                self.assertEqual(self.errors(frame), [])


class SessionLifecycleTests(BridgeCase):
    def test_closed_opener_studio_stops_click_interception(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.browsers[engine].new_context(viewport={'width': 1200, 'height': 900})
                self.addCleanup(context.close)
                route_virtual_origins(context, {STUDIO: FIXTURES, TARGET: REPO})
                studio = context.new_page()
                studio.goto(f'{STUDIO}/host.html')
                with context.expect_page() as popup_info:
                    studio.evaluate('(u) => openPopup(u)', TARGET_PAGE)
                popup = popup_info.value
                self.assertEqual(studio.evaluate('() => popupHello("p1")')['type'], 'design:ready')
                cta = f'[data-design-id="{CTA}"]'
                popup.locator(cta).click()
                self.assertEqual(popup.evaluate('location.hash'), '')  # select mode intercepts

                studio.close()
                popup.locator(cta).click()
                self.assertEqual(popup.evaluate('location.hash'), '#clicked')
                popup.locator('#counter').click()
                self.assertEqual(popup.evaluate("document.querySelector('#counter').dataset.count"), '1')


class TargetedUpdateTests(BridgeCase):
    def test_update_canonicalizes_and_applies_important_inline_styles(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.applied(page, TITLE, {
                    'fontFamily': '  "Courier New", monospace  ', 'fontSize': 56.456, 'fontWeight': 700.4,
                    'lineHeight': 1.23456, 'letterSpacing': 0.012345, 'color': '#FFAA00',
                    'textAlign': 'center', 'textTransform': 'uppercase'})
                self.assertEqual(reply['revision'], 1)
                self.assertEqual(reply['targetId'], TITLE)
                self.assertEqual(reply['sessionId'], 's1')
                self.assertEqual(reply['protocolVersion'], 1)
                self.assertEqual(reply['canonicalPatch'], {
                    'fontFamily': '"Courier New", monospace', 'fontSize': 56.46, 'fontWeight': 700,
                    'lineHeight': 1.235, 'letterSpacing': 0.0123, 'color': '#ffaa00',
                    'textAlign': 'center', 'textTransform': 'uppercase'})
                self.assertEqual(reply['target']['id'], TITLE)
                self.assertEqual(reply['target']['computed']['fontSize'], '56.46px')
                self.assertEqual(self.inline(frame, TITLE, 'font-size'), ['56.46px', 'important'])
                self.assertEqual(self.inline(frame, TITLE, 'letter-spacing'), ['0.0123em', 'important'])
                self.assertEqual(self.inline(frame, TITLE, 'line-height'), ['1.235', 'important'])
                self.assertEqual(self.computed(frame, TITLE, 'color'), 'rgb(255, 170, 0)')
                self.assertEqual(self.computed(frame, TITLE, 'fontWeight'), '700')
                self.assertEqual(self.computed(frame, TITLE, 'textTransform'), 'uppercase')
                self.assertEqual(self.errors(frame), [])

    def test_font_weight_snaps_to_declared_weights(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for requested, canonical in ((550, 600), (500, 400), (900, 800), (401, 400)):
                    reply = self.applied(page, BADGE, {'fontWeight': requested})
                    self.assertEqual(reply['canonicalPatch'], {'fontWeight': canonical})
                    self.assertEqual(self.computed(frame, BADGE, 'fontWeight'), str(canonical))

    def test_each_invalid_request_is_rejected_with_its_reason(self):
        long_text = 'x' * 5001
        cases = [
            (TITLE, {'margin': '0'}, 'unsupported-property', {'property': 'margin'}),
            (MARK, {'text': 'logo'}, 'unsupported-property', {'property': 'text'}),
            (TITLE, {'fontSize': 2}, 'unsupported-value', {'property': 'fontSize', 'requested': 2}),
            (TITLE, {'fontSize': '40'}, 'unsupported-value', {'property': 'fontSize', 'requested': '40'}),
            (TITLE, {'fontSize': float('inf')}, 'unsupported-value', {'property': 'fontSize'}),
            (TITLE, {'fontWeight': 0}, 'unsupported-value', {'property': 'fontWeight', 'requested': 0}),
            (TITLE, {'fontWeight': 1001}, 'unsupported-value', {'property': 'fontWeight'}),
            (TITLE, {'lineHeight': 0.4}, 'unsupported-value', {'property': 'lineHeight'}),
            (TITLE, {'lineHeight': 5.1}, 'unsupported-value', {'property': 'lineHeight'}),
            (TITLE, {'letterSpacing': -0.6}, 'unsupported-value', {'property': 'letterSpacing'}),
            (TITLE, {'letterSpacing': 2.5}, 'unsupported-value', {'property': 'letterSpacing'}),
            (TITLE, {'color': 'red'}, 'unsupported-value', {'property': 'color', 'requested': 'red'}),
            (TITLE, {'color': '#12345'}, 'unsupported-value', {'property': 'color'}),
            (TITLE, {'color': 'rgb(0, 0, 0); x'}, 'unsupported-value', {'property': 'color'}),
            (TITLE, {'color': 'url(x)'}, 'unsupported-value', {'property': 'color'}),
            (TITLE, {'fontFamily': ''}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': '   '}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': 'a;b'}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': 'a{b}'}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': 'a\\b'}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': 'Foo URL(x)'}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'fontFamily': 'f' * 301}, 'unsupported-value', {'property': 'fontFamily'}),
            (TITLE, {'textAlign': 'middle'}, 'unsupported-value', {'property': 'textAlign'}),
            (TITLE, {'textTransform': 'Uppercase'}, 'unsupported-value', {'property': 'textTransform'}),
            (TITLE, {'text': long_text}, 'unsupported-value', {'property': 'text'}),
            (TITLE, {'text': 42}, 'unsupported-value', {'property': 'text', 'requested': 42}),
            ('missing.target', {'fontSize': 20}, 'unknown-target', {}),
        ]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for target_id, patch, reason, detail in cases:
                    reply = self.update(page, target_id, patch)
                    self.assertEqual(reply.get('type'), 'design:rejected', (patch, reply))
                    self.assertEqual(reply['reason'], reason, patch)
                    self.assertEqual(reply['revision'], 0)
                    self.assertEqual(reply['targetId'], target_id)
                    self.assertEqual(reply['sessionId'], 's1')
                    for key, value in detail.items():
                        self.assertEqual(reply['detail'][key], value, patch)

                conflict = self.update(page, TITLE, {'fontSize': 20}, baseRevision=7)
                self.assertEqual((conflict['type'], conflict['reason']), ('design:rejected', 'revision-conflict'))
                self.assertEqual(conflict['detail'], {'baseRevision': 7, 'revision': 0})

                for bad in ({'patch': []}, {'patch': 'x'}, {'patch': None}, {'baseRevision': 'one'},
                            {'targetId': 42}, {'requestId': 9}):
                    reply = self.request(page, {'type': 'design:update', 'targetId': TITLE,
                                                'patch': {'fontSize': 20}, **bad})
                    self.assertEqual((reply.get('type'), reply.get('reason')),
                                     ('design:rejected', 'invalid-message'), bad)
                start = self.mark(page)
                page.evaluate('(m) => send(m)', {'type': 'design:update', 'protocolVersion': 1, 'sessionId': 's1',
                                                 'baseRevision': 0, 'targetId': TITLE, 'patch': {}})
                missing = self.wait_message(page, 'design:rejected', start)
                self.assertEqual((missing['reason'], missing['requestId']), ('invalid-message', None))

                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '40px')
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')
                self.assertEqual(self.messages(page, 'design:applied'), [])
                self.assertEqual(self.errors(frame), [])

    def test_rejected_patch_changes_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.update(page, TITLE, {'fontSize': 30, 'text': 'Nope', 'color': 'not-a-color'})
                self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'unsupported-value'))
                self.assertEqual(reply['detail']['property'], 'color')
                self.assertEqual(self.style_attr(frame, TITLE), TITLE_STYLE)
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '40px')

                reply = self.applied(page, BADGE, {'fontSize': 20})
                self.assertEqual(reply['revision'], 1)
                self.assertEqual([e['targetId'] for e in reply['changes']['targets']], [BADGE])

    def test_revision_increments_by_exactly_one_per_successful_mutation(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, _ = self.open(engine)
                self.hello(page)
                steps = [
                    ({'type': 'design:update', 'targetId': TITLE, 'patch': {'fontSize': 44}}, 'design:applied', 1),
                    ({'type': 'design:update', 'targetId': TITLE, 'patch': {'fontSize': 1}}, 'design:rejected', 1),
                    ({'type': 'design:update', 'targetId': TITLE, 'patch': {'text': 'T'}}, 'design:applied', 2),
                    ({'type': 'design:restore-text'}, 'design:applied', 3),
                    ({'type': 'design:reset', 'targetId': TITLE}, 'design:applied', 4),
                    ({'type': 'design:reset'}, 'design:applied', 5),
                    ({'type': 'design:update', 'patch': {'tokens': {'--brand-ink': '#222222'}}}, 'design:applied', 6),
                    ({'type': 'design:update', 'targetId': TITLE, 'patch': {}}, 'design:applied', 7),
                ]
                for msg, kind, revision in steps:
                    reply = self.request(page, msg)
                    self.assertEqual((reply['type'], reply['revision']), (kind, revision), msg)
                stale = self.update(page, TITLE, {'fontSize': 44}, baseRevision=2)
                self.assertEqual(stale['reason'], 'revision-conflict')
                self.assertEqual(stale['detail'], {'baseRevision': 2, 'revision': 7})
                ready = self.hello(page, 's2')
                self.assertEqual(ready['revision'], 7)

    def test_null_restores_the_original_inline_value(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'color': '#ff0000', 'fontSize': 50})
                self.assertEqual(self.inline(frame, TITLE, 'color'), ['rgb(255, 0, 0)', 'important'])

                reply = self.applied(page, TITLE, {'color': None})
                self.assertEqual(reply['canonicalPatch'], {'color': None})
                self.assertEqual(self.inline(frame, TITLE, 'color'), ['rgb(10, 20, 30)', ''])
                self.assertEqual(self.inline(frame, TITLE, 'font-size'), ['50px', 'important'])
                self.assertEqual(self.inline(frame, TITLE, 'margin-top'), ['8px', ''])
                self.assertEqual(self.entry(reply['changes'], TITLE)['declarations'], {'font-size': '50px'})

                reply = self.applied(page, TITLE, {'fontSize': None})
                self.assertEqual(reply['changes'], {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '40px')
                self.assertEqual(self.element(frame, TITLE, '(el) => el.style.cssText'),
                                 'color: rgb(10, 20, 30); margin-top: 8px;')

                # A badge without any author style gets its style attribute removed again.
                self.applied(page, BADGE, {'fontSize': 30})
                self.applied(page, BADGE, {'fontSize': None})
                self.assertIsNone(self.style_attr(frame, BADGE))

    def test_text_edits_leaf_and_mixed_content_and_restore_text_keeps_styles(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, LEAD, {'text': 'Fresh lead', 'fontSize': 22})
                self.assertEqual(self.element(frame, LEAD, '(el) => el.innerHTML'),
                                 'Fresh lead <strong>bold</strong> tail')
                reply = self.applied(page, CTA, {'text': 'Join now'})
                self.assertEqual(self.text(frame, CTA), 'Join now')
                lead = self.entry(reply['changes'], LEAD)
                self.assertEqual((lead['text'], lead['originalText']), ('Fresh lead', 'Lead copy'))

                reply = self.request(page, {'type': 'design:restore-text'})
                self.assertEqual((reply['type'], reply['targetId'], reply['canonicalPatch']),
                                 ('design:applied', 'global', {}))
                self.assertEqual(self.element(frame, LEAD, '(el) => el.innerHTML'),
                                 'Lead copy <strong>bold</strong> tail')
                self.assertEqual(self.text(frame, CTA), 'Get started')
                self.assertEqual(self.inline(frame, LEAD, 'font-size'), ['22px', 'important'])
                self.assertEqual([e['targetId'] for e in reply['changes']['targets']], [LEAD])
                lead = self.entry(reply['changes'], LEAD)
                self.assertIsNone(lead['text'])
                self.assertEqual(lead['declarations'], {'font-size': '22px'})

    def test_reset_one_target_or_everything(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'fontSize': 50, 'text': 'Reset me'})
                self.applied(page, BADGE, {'color': '#00ff00'})
                self.request(page, {'type': 'design:update', 'patch': {'tokens': {'--brand-ink': '#ff0000'}}})
                self.assertEqual(frame.evaluate("getComputedStyle(document.body).color"), 'rgb(255, 0, 0)')

                reply = self.request(page, {'type': 'design:reset', 'targetId': TITLE})
                self.assertEqual((reply['type'], reply['targetId'], reply['canonicalPatch'], reply['reset']),
                                 ('design:applied', TITLE, {}, True))
                self.assertEqual(self.style_attr(frame, TITLE), TITLE_STYLE)
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')
                self.assertEqual(self.computed(frame, BADGE, 'color'), 'rgb(0, 255, 0)')
                self.assertEqual([e['targetId'] for e in reply['changes']['targets']], [BADGE])
                self.assertEqual(reply['changes']['tokens'], {'--brand-ink': '#ff0000'})

                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual((reply['type'], reply['targetId'], reply['canonicalPatch'], reply['reset']),
                                 ('design:applied', 'global', {}, True))
                self.assertEqual(reply['changes'], {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})
                self.assertIsNone(self.style_attr(frame, BADGE))
                self.assertIsNone(frame.evaluate("document.documentElement.getAttribute('style')"))
                self.assertEqual(frame.evaluate("getComputedStyle(document.body).color"), 'rgb(17, 17, 17)')

                reply = self.request(page, {'type': 'design:reset', 'targetId': 'nope'})
                self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'unknown-target'))
                self.assertEqual(reply['revision'], 5)


class SelectionTests(BridgeCase):
    def test_select_mode_reports_hover_changes_and_click_selects(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                start = self.mark(page)
                box = frame.locator(f'[data-design-id="{TITLE}"]').bounding_box()
                page.mouse.move(box['x'] + 20, box['y'] + 10)
                hover = self.wait_message(page, 'design:hover', start, f"d.targetId === '{TITLE}'")
                self.assertEqual((hover['name'], hover['role'], hover['sessionId']), ('Hero title', 'display', 's1'))
                self.assertEqual(set(hover['rect']), {'x', 'y', 'width', 'height'})
                self.assertAlmostEqual(hover['rect']['y'], box['y'], delta=1)
                page.mouse.move(box['x'] + 30, box['y'] + 12)
                page.mouse.move(box['x'] + 40, box['y'] + 14)
                page.wait_for_timeout(150)
                self.assertEqual(len(self.messages(page, 'design:hover', start)), 1)

                # The header's own padding is no target (only its children are).
                header = frame.locator('#top').bounding_box()
                page.mouse.move(header['x'] + 2, header['y'] + 2)
                off = self.wait_message(page, 'design:hover', start, 'd.targetId === null')
                self.assertNotIn('rect', off)

                start = self.mark(page)
                frame.locator(f'[data-design-id="{CTA}"]').click()
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual(selected['targetId'], CTA)
                self.assertEqual(selected['target']['id'], CTA)
                self.assertEqual(set(selected['rect']), {'x', 'y', 'width', 'height'})
                self.assertEqual(frame.evaluate('location.hash'), '')

    def test_interact_mode_lets_the_page_behave_normally(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                page.wait_for_timeout(100)
                start = self.mark(page)
                frame.locator(f'[data-design-id="{CTA}"]').click()
                self.assertEqual(frame.evaluate('location.hash'), '#clicked')
                frame.locator('#counter').click()
                self.assertEqual(frame.evaluate("document.querySelector('#counter').dataset.count"), '1')
                box = frame.locator(f'[data-design-id="{TITLE}"]').bounding_box()
                page.mouse.move(box['x'] + 10, box['y'] + 10)
                page.wait_for_timeout(200)
                self.assertEqual(self.messages(page, 'design:selected', start), [])
                self.assertEqual([m for m in self.messages(page, 'design:hover', start) if m['targetId']], [])

                self.control(page, {'type': 'design:mode', 'mode': 'select'})
                page.wait_for_timeout(100)
                start = self.mark(page)
                frame.locator(f'[data-design-id="{TITLE}"]').click()
                self.assertEqual(self.wait_message(page, 'design:selected', start)['targetId'], TITLE)

    def test_select_message_scrolls_target_into_view_and_highlight_is_select(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                footer = self.target_by_text(ready, 'Footer note')['id']
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': footer})
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual(selected['targetId'], footer)
                self.assertGreater(frame.evaluate('scrollY'), 0)
                self.assertGreaterEqual(selected['rect']['y'], 0)
                self.assertLessEqual(selected['rect']['y'] + selected['rect']['height'], 600.5)

                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': None})
                cleared = self.wait_message(page, 'design:selected', start)
                self.assertIsNone(cleared['targetId'])

                start = self.mark(page)
                self.control(page, {'type': 'design:highlight', 'targetId': TITLE, 'slotIndex': 0, 'role': 'h1'})
                self.assertEqual(self.wait_message(page, 'design:selected', start)['targetId'], TITLE)

                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': 'no.such.target'})
                self.assertIsNone(self.wait_message(page, 'design:selected', start)['targetId'])
                # The Studio draws overlays: nothing is injected into the target DOM by default.
                self.assertEqual(frame.evaluate("document.querySelectorAll('[id^=\"fontkit-bridge\"]').length"), 0)

    def test_a_select_request_id_is_echoed_in_the_reply_and_only_when_it_is_a_sane_string(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                # The reply to a request names the request; a selection the page makes by itself does not.
                for target_id in (TITLE, None, 'no.such.target'):
                    with self.subTest(target=target_id):
                        start = self.mark(page)
                        self.control(page, {'type': 'design:select', 'targetId': target_id, 'requestId': 'fks-sel-7'})
                        reply = self.wait_message(page, 'design:selected', start)
                        self.assertEqual(reply.get('requestId'), 'fks-sel-7')
                        self.assertEqual(reply['targetId'], target_id if target_id == TITLE else None)
                start = self.mark(page)
                frame.evaluate(f"({BY_ID})('{LEAD}').click()")
                self.assertNotIn('requestId', self.wait_message(page, 'design:selected', start))
                # Hostile values are never echoed back as data: wrong types, empty, oversized.
                for bad in (7, True, {'a': 1}, ['x'], '', 'x' * 101):
                    with self.subTest(requestId=bad):
                        start = self.mark(page)
                        self.control(page, {'type': 'design:select', 'targetId': TITLE, 'requestId': bad})
                        self.assertNotIn('requestId', self.wait_message(page, 'design:selected', start))
                self.assertEqual(self.errors(frame), [])

    def test_bounds_follow_scroll_and_size_changes_of_the_selected_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': TITLE})
                selected = self.wait_message(page, 'design:selected', start)

                start = self.mark(page)
                frame.evaluate('window.scrollBy(0, 30)')
                bounds = self.wait_message(page, 'design:bounds', start)
                self.assertEqual(bounds['targetId'], TITLE)
                self.assertAlmostEqual(bounds['rect']['y'], selected['rect']['y'] - 30, delta=1)

                start = self.mark(page)
                self.applied(page, TITLE, {'fontSize': 90})
                grown = self.wait_message(page, 'design:bounds', start,
                                          f"d.rect.height > {selected['rect']['height'] + 20}")
                self.assertEqual(grown['targetId'], TITLE)

    def test_new_targets_are_announced_once_per_burst(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                start = self.mark(page)
                frame.evaluate("""() => new Promise((resolve) => {
                    [0, 15, 30].forEach((delay, i) => setTimeout(() => {
                        const h = document.createElement('h2');
                        h.textContent = 'Late ' + (i + 1);
                        document.querySelector('main').append(h);
                        if (i === 2) resolve();
                    }, delay));
                })""")
                announced = self.wait_message(page, 'design:targets', start)
                texts = [t['text'] for t in announced['targets']]
                self.assertTrue({'Late 1', 'Late 2', 'Late 3'} <= set(texts), texts)
                self.assertIn(TITLE, [t['id'] for t in announced['targets']])
                page.wait_for_timeout(300)
                self.assertEqual(len(self.messages(page, 'design:targets', start)), 1)

                # Mutations that add no new target are not announced.
                start = self.mark(page)
                frame.evaluate("document.body.append(document.createElement('div'))")
                page.wait_for_timeout(300)
                self.assertEqual(self.messages(page, 'design:targets', start), [])


class OverlayOptionTests(BridgeCase):
    def test_in_target_overlay_is_opt_in_and_never_leaks_into_targets_or_html(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=f'{TARGET}/tests/fixtures/bridge/target-overlay.html')
                self.assertEqual(frame.evaluate("document.querySelectorAll('[id^=\"fontkit-bridge\"]').length"), 0)
                ready = self.hello(page)
                self.assertEqual(sorted(t['id'] for t in ready['targets'] if t['stable']),
                                 ['overlay.body', 'overlay.title'])
                self.assertFalse([t for t in ready['targets'] if t['tag'] == 'div'])
                shown = "(id) => getComputedStyle(document.getElementById(id)).display"

                box = frame.locator('[data-design-id="overlay.body"]').bounding_box()
                start = self.mark(page)
                page.mouse.move(box['x'] + 5, box['y'] + 5)
                self.wait_message(page, 'design:hover', start, "d.targetId === 'overlay.body'")
                self.assertEqual(frame.evaluate(shown, 'fontkit-bridge-hover'), 'block')

                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': 'overlay.title'})
                self.wait_message(page, 'design:selected', start)
                self.assertEqual(frame.evaluate(shown, 'fontkit-bridge-overlay'), 'block')
                page.wait_for_timeout(250)
                self.assertEqual(self.messages(page, 'design:targets', start), [])

                reply = self.applied(page, 'overlay.title', {'fontSize': 30})
                self.assertNotIn('fontkit-bridge', self.entry(reply['changes'], 'overlay.title')['html'])
                self.assertEqual(self.errors(frame), [])


class ChangeLedgerTests(BridgeCase):
    def test_ledger_lists_changed_targets_with_selectors_and_cleaned_html(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                card = self.target_by_text(ready, 'Card two')
                self.applied(page, card['id'], {'color': '#ff0000'})
                self.applied(page, TITLE, {'fontSize': 56, 'text': 'New title'})
                reply = self.applied(page, card['id'], {'fontSize': 20})
                changes = reply['changes']
                self.assertEqual(changes['tokens'], {})
                self.assertEqual([e['targetId'] for e in changes['targets']], [card['id'], TITLE])

                auto = changes['targets'][0]
                self.assertEqual(set(auto), {'targetId', 'selector', 'stable', 'name', 'role', 'declarations',
                                             'text', 'originalText', 'html'})
                self.assertEqual(auto['selector'], card['selector'])
                self.assertFalse(auto['stable'])
                self.assertEqual(auto['declarations'], {'color': '#ff0000', 'font-size': '20px'})
                self.assertIsNone(auto['text'])
                self.assertEqual(auto['originalText'], 'Card two')
                self.assertEqual(auto['html'], '<h3>Card two</h3>')
                # The live element still carries the bridge-owned attributes.
                self.assertEqual(self.element(frame, card['id'], "(el) => el.getAttribute('data-design-id')"), card['id'])

                title = changes['targets'][1]
                self.assertEqual((title['selector'], title['stable'], title['name'], title['role']),
                                 ('[data-design-id="landing.hero.title"]', True, 'Hero title', 'display'))
                self.assertEqual(title['declarations'], {'font-size': '56px'})
                self.assertEqual((title['text'], title['originalText']), ('New title', 'Make type sing'))
                self.assertEqual(title['html'],
                                 '<h1 data-design-id="landing.hero.title" data-design-role="display" '
                                 f'data-design-name="Hero title" style="{TITLE_STYLE}">New title</h1>')

                # Text-only change: no declarations, cleaned html keeps the new text.
                reply = self.applied(page, CTA, {'text': 'Go'})
                cta = self.entry(reply['changes'], CTA)
                self.assertEqual((cta['declarations'], cta['text'], cta['originalText']), ({}, 'Go', 'Get started'))
                self.assertEqual(cta['html'], '<a class="btn" data-design-id="landing.hero.cta" href="#clicked">Go</a>')

                # Setting text back to the original drops the text from the ledger.
                reply = self.applied(page, CTA, {'text': 'Get started'})
                self.assertIsNone(self.entry(reply['changes'], CTA))

                # The ledger is part of every design:ready too.
                ready = self.hello(page, 's2')
                self.assertEqual([e['targetId'] for e in ready['changes']['targets']], [card['id'], TITLE])

    def test_ledger_html_strips_bridge_state_from_nested_targets(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                lead_html = self.element(frame, LEAD, '(el) => el.outerHTML')
                self.applied(page, LEAD, {'fontSize': 21})
                reply = self.applied(page, LEAD, {'text': 'Changed'})
                self.assertEqual(self.entry(reply['changes'], LEAD)['html'],
                                 lead_html.replace('Lead copy', 'Changed'))
                # A container target wrapping changed auto targets: their overrides and attrs are stripped.
                card = self.target_by_text(ready, 'Card one')
                self.applied(page, card['id'], {'color': '#123456', 'text': 'Card uno'})
                frame.evaluate("document.querySelector('.cards').setAttribute('data-design-id', 'landing.cards')")
                page.wait_for_timeout(250)
                self.hello(page, 's2')
                reply = self.applied(page, 'landing.cards', {'textAlign': 'center'})
                cards = self.entry(reply['changes'], 'landing.cards')
                self.assertNotIn('data-design-', cards['html'].replace('data-design-id="landing.cards"', ''))
                self.assertNotIn('!important', cards['html'])
                self.assertNotIn('#123456', cards['html'])
                self.assertIn('<h3>Card uno</h3>', cards['html'])
                self.assertTrue(cards['html'].startswith('<section class="cards" data-design-id="landing.cards">'))


class LegacyCompositionTests(BridgeCase):
    def test_composition_update_applies_slots_and_tokens_into_the_ledger(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                slot = {'id': 'slot-1', 'targetId': TITLE, 'index': 0, 'role': 'h1', 'type': 'text',
                        'fontFamily': 'Courier New, monospace', 'size': 52, 'weight': 700, 'lineHeight': 1.1,
                        'tracking': 20, 'align': 'center', 'colorHex': '#336699', 'transform': 'uppercase',
                        'text': 'Legacy title', 'textTouched': True}
                untouched = {'id': 'slot-2', 'targetId': BADGE, 'index': 1, 'role': 'metadata', 'type': 'text',
                             'size': 14, 'text': 'Preset poetry', 'textTouched': False}
                reply = self.request(page, {'type': 'design:update', 'patch': {
                    'tokens': {'--font-display': 'Courier New, monospace'},
                    'slots': [slot, untouched],
                    'layout': {'order': [{'id': 'slot-1', 'role': 'h1', 'index': 0},
                                         {'id': 'slot-2', 'role': 'metadata', 'index': 1}],
                               'canvasWidth': 800}}})
                self.assertEqual((reply['type'], reply['targetId'], reply['revision']), ('design:applied', 'global', 1))
                self.assertEqual(reply['canonicalPatch']['tokens'], {'--font-display': 'Courier New, monospace'})
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '52px')
                self.assertEqual(self.text(frame, TITLE), 'Legacy title')
                self.assertEqual(self.text(frame, BADGE), '42 fonts')

                changes = reply['changes']
                self.assertEqual(changes['tokens'], {'--font-display': 'Courier New, monospace'})
                title = self.entry(changes, TITLE)
                self.assertEqual(title['declarations'], {
                    'font-family': 'Courier New, monospace', 'font-size': '52px', 'font-weight': '700',
                    'line-height': '1.1', 'letter-spacing': '0.02em', 'color': '#336699',
                    'text-align': 'center', 'text-transform': 'uppercase'})
                self.assertEqual(title['text'], 'Legacy title')
                self.assertNotIn('transition', title['html'])
                self.assertNotIn('order', title['html'])
                self.assertEqual(self.entry(changes, BADGE)['declarations'], {'font-size': '14px'})

                ack_start = self.mark(page)
                self.control(page, {'type': 'fontkit:change', 'fonts': {'sans': 'Verdana, sans-serif'}})
                ack = self.wait_message(page, 'fontkit:ack', ack_start)
                self.assertEqual(ack['revision'], 2)
                self.assertEqual(ack['changes']['tokens']['--font-sans'], 'Verdana, sans-serif')
                self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--font-sans')"),
                                 'Verdana, sans-serif')

                reset = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reset['changes'], {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})
                self.assertEqual(self.text(frame, TITLE), 'Make type sing')
                self.assertEqual(self.style_attr(frame, TITLE), TITLE_STYLE)
                self.assertEqual(frame.evaluate("[...document.querySelectorAll('main > *')]"
                                                ".filter((el) => el.style.transition || el.style.order).length"), 0)


    def test_legacy_tokens_accept_only_safe_names_and_values(self):
        """One invalid token rejects the whole composition update: nothing is applied and nothing is acked as applied."""
        bad = {'--evil': 'url(https://evil.test/beacon)', '--Upper': 'x', '--under_score': 'x', '--semi': 'a;b',
               '--brace': 'a{b}', '--angle': 'a<b', '--slash': 'a\\b', '--expr': 'expression(alert(1))',
               '--blank': '   ', '--number': 3, 'not-a-token': 'x', '--': 'x', '--' + 'a' * 121: 'x'}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for name, value in bad.items():
                    with self.subTest(token=name[:12]):
                        reply = self.request(page, {'type': 'design:update', 'patch': {'tokens': {
                            '--ok-font': 'Georgia, serif', name: value}}})
                        self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'unsupported-value'))
                        self.assertEqual(reply['detail']['property'], 'tokens')
                        self.assertEqual(reply['revision'], 0)
                        self.assertEqual(frame.evaluate('document.documentElement.style.cssText'), '',
                                         'a rejected update changes nothing, not even its valid tokens')
                shortcut = self.request(page, {'type': 'design:update', 'patch': {'sans': 'url(x)'}})
                self.assertEqual((shortcut['type'], shortcut['reason'], shortcut['detail']['property']),
                                 ('design:rejected', 'unsupported-value', 'sans'))
                # The accepted shape: lower-case letters, digits and hyphens, up to 120 characters in total.
                longest = '--' + 'a' * 118
                reply = self.request(page, {'type': 'design:update', 'patch': {'tokens': {
                    '--ok-font': 'Georgia, serif', longest: '1px'}}})
                self.assertEqual(reply['type'], 'design:applied')
                self.assertEqual(reply['canonicalPatch']['tokens'], {'--ok-font': 'Georgia, serif', longest: '1px'})
                self.assertEqual(reply['changes']['tokens'], {'--ok-font': 'Georgia, serif', longest: '1px'})

                start = self.mark(page)
                self.control(page, {'type': 'fontkit:change', 'fonts': {'sans': 'url(x)', 'serif': 'Georgia'}})
                ack = self.wait_message(page, 'fontkit:ack', start)
                self.assertEqual(ack['changes']['tokens'], {'--ok-font': 'Georgia, serif', longest: '1px',
                                                            '--font-serif': 'Georgia'})


class TokenRemovalTests(BridgeCase):
    """Addendum 6: a null composition token removes Studio's override and restores the original value."""
    AUTHOR_STYLE = '--font-sans:  Georgia ;  color: navy'

    def tokens(self, page, patch, **extra):
        return self.request(page, {'type': 'design:update', 'patch': {'tokens': patch}, **extra})

    def root_style(self, frame):
        return frame.evaluate("document.documentElement.getAttribute('style')")

    def test_null_removes_the_override_and_restores_the_authors_inline_style_byte_for_byte(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ROOT_STYLE_PAGE)
                self.hello(page)
                self.assertEqual(self.root_style(frame), self.AUTHOR_STYLE)
                authored = frame.evaluate("document.documentElement.style.getPropertyValue('--font-sans')")
                self.assertEqual(authored.strip(), 'Georgia')

                reply = self.tokens(page, {'--font-sans': 'Verdana, sans-serif', '--extra': '12px'})
                self.assertEqual((reply['type'], reply['revision']), ('design:applied', 1))
                self.assertEqual(reply['changes']['tokens'], {'--font-sans': 'Verdana, sans-serif', '--extra': '12px'})
                self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--font-sans')"),
                                 'Verdana, sans-serif')

                # A token the author never set is removed outright; the other override stays.
                reply = self.tokens(page, {'--extra': None})
                self.assertEqual((reply['type'], reply['revision'], reply['targetId']), ('design:applied', 2, 'global'))
                self.assertEqual(reply['canonicalPatch'], {'tokens': {'--extra': None}})
                self.assertEqual(reply['changes']['tokens'], {'--font-sans': 'Verdana, sans-serif'})
                self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--extra')"), '')

                # Removing the last override gives the author's own inline value and attribute text back.
                reply = self.tokens(page, {'--font-sans': None})
                self.assertEqual((reply['type'], reply['revision']), ('design:applied', 3))
                self.assertEqual(reply['canonicalPatch'], {'tokens': {'--font-sans': None}})
                self.assertEqual(reply['changes']['tokens'], {})
                self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--font-sans')"), authored)
                self.assertEqual(self.root_style(frame), self.AUTHOR_STYLE)

                # The original is captured once: a second override and removal restores the same text.
                self.assertEqual(self.tokens(page, {'--font-sans': 'Courier New'})['type'], 'design:applied')
                self.assertEqual(self.tokens(page, {'--font-sans': None})['changes']['tokens'], {})
                self.assertEqual(self.root_style(frame), self.AUTHOR_STYLE)
                self.assertEqual(self.errors(frame), [])

    def test_null_restores_a_token_the_stylesheet_defines_and_leaves_no_style_attribute(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertIsNone(self.root_style(frame))
                self.assertEqual(self.tokens(page, {'--brand-ink': '#ff0000'})['changes']['tokens'], {'--brand-ink': '#ff0000'})
                self.assertEqual(frame.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand-ink').trim()"), '#ff0000')
                reply = self.tokens(page, {'--brand-ink': None})
                self.assertEqual(reply['changes']['tokens'], {})
                self.assertEqual(frame.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--brand-ink').trim()"), '#111111')
                self.assertIsNone(self.root_style(frame), 'the bridge leaves no style attribute behind')

    def test_unknown_names_are_ignored_and_invalid_names_still_reject_the_whole_update(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ROOT_STYLE_PAGE)
                self.hello(page)
                reply = self.tokens(page, {'--never-set': None, '--font-sans': 'Verdana'})
                self.assertEqual(reply['type'], 'design:applied')
                self.assertEqual(reply['canonicalPatch'], {'tokens': {'--font-sans': 'Verdana'}},
                                 'a null for a token that was never overridden is not reported')
                self.assertEqual(reply['changes']['tokens'], {'--font-sans': 'Verdana'})
                # The author's own inline custom property is not a Studio override, so null leaves it alone.
                reply = self.tokens(page, {'--font-sans': None, '--color-never': None})
                self.assertEqual(reply['changes']['tokens'], {})
                self.assertEqual(self.root_style(frame), self.AUTHOR_STYLE)
                for bad in ('--Upper', '--under_score', 'not-a-token', '--'):
                    with self.subTest(name=bad):
                        before = self.root_style(frame)
                        reply = self.tokens(page, {'--font-sans': 'Verdana', bad: None})
                        self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'unsupported-value'))
                        self.assertEqual(reply['detail']['property'], 'tokens')
                        self.assertEqual(self.root_style(frame), before, 'a rejected update changes nothing')
                self.assertEqual(self.errors(frame), [])

    def test_a_global_reset_still_restores_the_authors_inline_style(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ROOT_STYLE_PAGE)
                self.hello(page)
                self.assertEqual(self.tokens(page, {'--font-sans': 'Verdana', '--extra': '1px'})['type'], 'design:applied')
                self.assertEqual(self.tokens(page, {'--extra': None})['changes']['tokens'], {'--font-sans': 'Verdana'})
                reset = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reset['changes']['tokens'], {})
                self.assertEqual(self.root_style(frame), self.AUTHOR_STYLE)


class PromotedTargetTests(BridgeCase):
    """An edited auto-discovered element that later gets an author data-design-id keeps its edit under the new id."""
    NEW_ID = 'cards.one.title'
    CARD = "[...document.querySelectorAll('h3')].find((el) => el.textContent.trim() === 'Card one' || el.textContent.trim() === 'Edited card')"

    def edit_then_promote(self, page, frame, trigger):
        ready = self.hello(page)
        old = next(t for t in ready['targets'] if t['text'] == 'Card one' and t['tag'] == 'h3')
        self.assertFalse(old['stable'])
        self.assertTrue(old['id'].startswith('auto:'))
        reply = self.applied(page, old['id'], {'fontSize': 33, 'color': '#336699', 'text': 'Edited card'})
        self.assertEqual([entry['targetId'] for entry in reply['changes']['targets']], [old['id']])
        start = self.mark(page)
        frame.evaluate(f'({self.CARD}).setAttribute("data-design-id", "{self.NEW_ID}")')
        trigger(page, frame, start)
        return old

    def rediscover(self, page, frame, start):
        """A re-render elsewhere in the page: the next discovery run sees the attribute."""
        frame.evaluate("document.body.append(document.createElement('i'))")
        announced = self.wait_message(page, 'design:targets', start)
        self.assertNotEqual(announced['type'], 'timeout')

    def ledger_after_a_second_edit(self, page):
        # Any later update reports the ledger; the title is a different, author target.
        return self.applied(page, TITLE, {'fontSize': 41})['changes']

    def test_the_edit_follows_the_element_to_its_new_id_and_reset_restores_the_original_exactly(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                old = self.edit_then_promote(page, frame, self.rediscover)
                changes = self.ledger_after_a_second_edit(page)
                self.assertEqual([entry['targetId'] for entry in changes['targets']], [self.NEW_ID, TITLE],
                                 'the edit keeps its place in the change order, under the new id')
                entry = changes['targets'][0]
                self.assertEqual(entry['declarations'], {'font-size': '33px', 'color': '#336699'})
                self.assertEqual((entry['text'], entry['originalText']), ('Edited card', 'Card one'))
                self.assertTrue(entry['stable'])
                self.assertEqual(entry['selector'], f'[data-design-id="{self.NEW_ID}"]')
                self.assertNotIn('style=', entry['html'])
                self.assertIn(f'data-design-id="{self.NEW_ID}"', entry['html'])
                self.assertEqual(self.computed(frame, self.NEW_ID, 'fontSize'), '33px')

                # The manifest names the id it replaced, so a Studio holding the old id can follow it.
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': self.NEW_ID})
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual((selected['targetId'], selected['target']['id'], selected['target']['previousId']),
                                 (self.NEW_ID, self.NEW_ID, old['id']))
                self.assertTrue(selected['target']['stable'])
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': old['id']})
                self.assertIsNone(self.wait_message(page, 'design:selected', start)['targetId'], 'the old id is gone')

                # Reset of the new id restores the original captured before the first edit.
                reply = self.request(page, {'type': 'design:reset', 'targetId': self.NEW_ID})
                self.assertEqual((reply['type'], reply['reset']), ('design:applied', True))
                self.assertEqual([e['targetId'] for e in reply['changes']['targets']], [TITLE])
                self.assertIsNone(frame.evaluate(f'({self.CARD}).getAttribute("style")'))
                self.assertEqual(frame.evaluate(f'({self.CARD}).textContent'), 'Card one')
                self.assertEqual(frame.evaluate(f'({self.CARD}).getAttribute("data-design-id")'), self.NEW_ID)
                self.assertEqual(self.errors(frame), [])

    def test_a_fresh_studio_sees_the_edit_in_design_ready_and_the_old_id_is_gone(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                old = self.edit_then_promote(page, frame, self.rediscover)
                ready = self.hello(page, 's2')
                self.assertEqual([entry['targetId'] for entry in ready['changes']['targets']], [self.NEW_ID])
                ids = [t['id'] for t in ready['targets']]
                self.assertIn(self.NEW_ID, ids)
                self.assertNotIn(old['id'], ids)
                promoted = next(t for t in ready['targets'] if t['id'] == self.NEW_ID)
                self.assertEqual(promoted['previousId'], old['id'])
                self.assertTrue(all('previousId' not in t for t in ready['targets'] if t['id'] != self.NEW_ID),
                                'only a promoted target names a previous id')

    def test_reset_after_promotion_restores_the_authors_inline_style_byte_for_byte(self):
        authored = 'margin:  0 ;color: red'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(f"({self.CARD}).setAttribute('style', {json.dumps(authored)})")
                self.edit_then_promote(page, frame, self.rediscover)
                self.assertNotEqual(frame.evaluate(f'({self.CARD}).getAttribute("style")'), authored)
                reply = self.request(page, {'type': 'design:reset', 'targetId': self.NEW_ID})
                self.assertEqual(reply['type'], 'design:applied')
                self.assertEqual(frame.evaluate(f'({self.CARD}).getAttribute("style")'), authored)
                self.assertEqual(frame.evaluate(f'({self.CARD}).textContent'), 'Card one')
                self.assertEqual(reply['changes']['targets'], [])

    def test_setting_the_attribute_alone_is_enough_for_discovery(self):
        """An app that adds the attribute in place (no node is added or removed) is still noticed."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)

                def nothing(page, frame, start):
                    announced = self.wait_message(page, 'design:targets', start,
                                                  where=f"d.targets.some((t) => t.id === '{self.NEW_ID}')")
                    self.assertNotEqual(announced['type'], 'timeout')

                self.edit_then_promote(page, frame, nothing)
                changes = self.ledger_after_a_second_edit(page)
                self.assertEqual([entry['targetId'] for entry in changes['targets']], [self.NEW_ID, TITLE])


class DemotedTargetTests(BridgeCase):
    """An edited author target whose data-design-id is removed keeps its edit, under an auto id that names the old one."""
    BADGE_EL = f"({BY_ID})('{LEAD}')"

    def edit_then_remove(self, page, frame, trigger):
        ready = self.hello(page)
        self.assertTrue(next(t for t in ready['targets'] if t['id'] == LEAD)['stable'])
        self.applied(page, LEAD, {'color': '#445566'})
        self.applied(page, TITLE, {'fontSize': 33, 'text': 'Edited title'})
        start = self.mark(page)
        frame.evaluate(f'({self.BADGE_EL}).removeAttribute("data-design-id")')
        trigger(page, frame, start)

    def announced(self, page, start):
        message = self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.previousId === '{LEAD}')")
        self.assertNotEqual(message['type'], 'timeout', 'the removal was never announced')
        return next(t for t in message['targets'] if t.get('previousId') == LEAD)

    def attribute_alone(self, page, frame, start):
        self.announced(page, start)

    def rediscover(self, page, frame, start):
        frame.evaluate("document.body.append(document.createElement('i'))")
        self.announced(page, start)

    def test_removing_the_attribute_alone_moves_the_edit_to_an_auto_id_naming_the_old_one(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                # No other change in the page: the attribute removal itself must be noticed.
                self.edit_then_remove(page, frame, self.attribute_alone)
                message = self.wait_message(page, 'design:targets', 0, f"d.targets.some((t) => t.previousId === '{LEAD}')")
                target = next(t for t in message['targets'] if t.get('previousId') == LEAD)
                self.assertFalse(target['stable'])
                self.assertRegex(target['id'], r'^auto:p:')
                self.assertNotIn(LEAD, [t['id'] for t in message['targets']], 'the author id is gone')
                self.assertNotRegex(target['selector'], r'data-design-id="landing')

    def test_the_edit_keeps_its_originals_and_its_place_in_the_change_order(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.edit_then_remove(page, frame, self.rediscover)
                # Any later update reports the ledger; the badge is a different, author target.
                changes = self.applied(page, BADGE, {'fontWeight': 600})['changes']
                ids = [entry['targetId'] for entry in changes['targets']]
                self.assertEqual(len(ids), 3)
                self.assertRegex(ids[0], r'^auto:p:', 'the edit keeps its first place, under the new id')
                self.assertEqual(ids[1:], [TITLE, BADGE])
                entry = changes['targets'][0]
                self.assertEqual(entry['declarations'], {'color': '#445566'})
                self.assertFalse(entry['stable'])
                self.assertNotIn('data-design-id="landing.hero.lead"', entry['html'])
                self.assertNotIn('style=', entry['html'])
                self.assertEqual(frame.evaluate(f"document.querySelectorAll({json.dumps(entry['selector'])}).length"), 1)
                self.assertEqual(frame.evaluate(f"getComputedStyle(document.querySelector({json.dumps(entry['selector'])})).color"),
                                 'rgb(68, 85, 102)')

                # Reset of the new id restores the original inline style, captured before the first edit.
                reply = self.request(page, {'type': 'design:reset', 'targetId': ids[0]})
                self.assertEqual((reply['type'], reply['reset']), ('design:applied', True))
                self.assertEqual([e['targetId'] for e in reply['changes']['targets']], [TITLE, BADGE])
                self.assertIsNone(frame.evaluate(f"document.querySelector('p.lead').getAttribute('style')"))
                self.assertEqual(self.errors(frame), [])

    def test_a_fresh_studio_sees_the_demoted_target_and_the_old_id_is_gone(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.edit_then_remove(page, frame, self.rediscover)
                ready = self.hello(page, 's2')
                ids = [t['id'] for t in ready['targets']]
                self.assertNotIn(LEAD, ids)
                demoted = next(t for t in ready['targets'] if t.get('previousId') == LEAD)
                self.assertEqual(demoted['text'], 'Lead copy bold tail')
                self.assertEqual(sum('previousId' in t for t in ready['targets']), 1)
                self.assertEqual(self.entry(ready['changes'], demoted['id'])['declarations'], {'color': '#445566'})

    def test_the_selection_follows_the_element(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.control(page, {'type': 'design:select', 'targetId': LEAD})
                self.assertEqual(self.wait_message(page, 'design:selected', 0, f"d.targetId === '{LEAD}'")['targetId'], LEAD)
                start = self.mark(page)
                frame.evaluate(f'({self.BADGE_EL}).removeAttribute("data-design-id")')
                demoted = self.announced(page, start)
                # Selecting again by the new id works and names the old one; the old id is unknown.
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': demoted['id']})
                selected = self.wait_message(page, 'design:selected', start, f"d.targetId === '{demoted['id']}'")
                self.assertEqual(selected['target']['previousId'], LEAD)
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': LEAD})
                self.assertIsNone(self.wait_message(page, 'design:selected', start)['targetId'])

    def test_an_author_id_that_is_still_there_or_changed_is_not_a_removal(self):
        """Renaming to another author id is a promotion (the element keeps its edits); only a missing id is a demotion."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, LEAD, {'color': '#445566'})
                start = self.mark(page)
                frame.evaluate(f'({self.BADGE_EL}).setAttribute("data-design-id", "landing.hero.lead.renamed")')
                message = self.wait_message(page, 'design:targets', start, "d.targets.some((t) => t.id === 'landing.hero.lead.renamed')")
                renamed = next(t for t in message['targets'] if t['id'] == 'landing.hero.lead.renamed')
                self.assertTrue(renamed['stable'])
                self.assertEqual(renamed['previousId'], LEAD)
                self.assertFalse(any(t['id'].startswith('auto:p:') and t.get('previousId') for t in message['targets']))

    def test_giving_the_id_back_and_resetting_leaves_the_markup_byte_for_byte_as_it_was(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                original = frame.evaluate("document.querySelector('p.lead').outerHTML")
                self.hello(page)
                self.applied(page, LEAD, {'color': '#445566', 'text': 'Edited tail'})
                start = self.mark(page)
                frame.evaluate("document.querySelector('p.lead').removeAttribute('data-design-id')")
                self.announced(page, start)
                start = self.mark(page)
                frame.evaluate("document.querySelector('p.lead').setAttribute('data-design-id', 'landing.hero.lead')")
                back = self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.id === '{LEAD}' && t.previousId)")
                self.assertNotEqual(back['type'], 'timeout', 'the id coming back was never announced')
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual((reply['type'], reply['reset']), ('design:applied', True))
                self.assertEqual(frame.evaluate("document.querySelector('p.lead').outerHTML"), original)
                self.assertEqual(self.errors(frame), [])

    def test_an_authors_own_role_and_name_survive_the_round_trip(self):
        """Only attributes the bridge wrote are dropped when the author id comes back."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'color': '#445566'})
                start = self.mark(page)
                frame.evaluate("document.querySelector('h1').removeAttribute('data-design-id')")
                message = self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.previousId === '{TITLE}')")
                self.assertNotEqual(message['type'], 'timeout')
                frame.evaluate("document.querySelector('h1').setAttribute('data-design-id', 'landing.hero.title')")
                self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.id === '{TITLE}' && t.previousId)")
                self.assertEqual(frame.evaluate("[document.querySelector('h1').getAttribute('data-design-role'), "
                                                "document.querySelector('h1').getAttribute('data-design-name')]"),
                                 ['display', 'Hero title'])

    def test_removing_an_id_nothing_edited_still_leaves_one_target_for_the_element(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                start = self.mark(page)
                frame.evaluate(f'({self.BADGE_EL}).removeAttribute("data-design-id")')
                demoted = self.announced(page, start)
                self.assertFalse(demoted['stable'])
                self.assertEqual(frame.evaluate("document.querySelectorAll('p.lead').length"), 1)
                self.assertEqual(self.errors(frame), [])


class DemotedArrangementBranchTests(BridgeCase):
    """Removing an author id keeps an edited, role-hinted or semantic element an ordinary target; only a
    plain, unedited, non-semantic element (the badge span) is kept for arrangement alone."""

    def remove_id(self, page, frame, design_id):
        start = self.mark(page)
        self.element(frame, design_id, '(el) => { el.removeAttribute("data-design-id"); document.body.append(document.createElement("i")); }')
        message = self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.previousId === '{design_id}')")
        self.assertNotEqual(message['type'], 'timeout', 'the removal was never announced')
        return next(t for t in message['targets'] if t.get('previousId') == design_id)

    def assert_ready_agrees(self, page, demoted):
        ready = self.hello(page, 's2')
        again = next(t for t in ready['targets'] if t.get('previousId') == demoted['previousId'])
        self.assertEqual(again.get('arrangementOnly'), demoted.get('arrangementOnly'))
        return again

    def test_an_unedited_plain_span_is_kept_for_arrangement_only(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                demoted = self.remove_id(page, frame, BADGE)
                self.assertIs(demoted.get('arrangementOnly'), True)
                self.assertIs(self.assert_ready_agrees(page, demoted).get('arrangementOnly'), True)

    def test_the_same_span_after_an_edit_is_an_ordinary_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, BADGE, {'color': '#445566'})
                demoted = self.remove_id(page, frame, BADGE)
                self.assertNotIn('arrangementOnly', demoted)
                self.assertNotIn('arrangementOnly', self.assert_ready_agrees(page, demoted))

    def test_the_same_span_with_an_author_role_is_an_ordinary_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.element(frame, BADGE, '(el) => el.setAttribute("data-design-role", "stat")')
                demoted = self.remove_id(page, frame, BADGE)
                self.assertNotIn('arrangementOnly', demoted)
                self.assertEqual(demoted['role'], 'stat')
                self.assertNotIn('arrangementOnly', self.assert_ready_agrees(page, demoted))

    def test_a_semantic_element_is_an_ordinary_target_even_when_unedited(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                demoted = self.remove_id(page, frame, LEAD)
                self.assertNotIn('arrangementOnly', demoted)
                self.assertNotIn('arrangementOnly', self.assert_ready_agrees(page, demoted))

    def test_a_second_removal_does_not_read_the_bridges_own_role_as_an_author_hint(self):
        """Demote, give the author id back, remove it again: the span is still plain, so still arrangement-only."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertIs(self.remove_id(page, frame, BADGE).get('arrangementOnly'), True)
                start = self.mark(page)
                frame.evaluate("""() => document.querySelector('span[data-design-id^="auto:span"]')
                    .setAttribute('data-design-id', 'landing.stat.badge')""")
                back = self.wait_message(page, 'design:targets', start, f"d.targets.some((t) => t.id === '{BADGE}')")
                self.assertNotEqual(back['type'], 'timeout', 'the id coming back was never announced')
                self.assertNotIn('arrangementOnly', next(t for t in back['targets'] if t['id'] == BADGE))
                self.assertIs(self.remove_id(page, frame, BADGE).get('arrangementOnly'), True)

    def test_a_plain_span_that_leaves_the_page_and_comes_back_is_still_arrangement_only(self):
        """The role attribute the bridge wrote on the first demotion must not make the re-attached span ordinary."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertIs(self.remove_id(page, frame, BADGE).get('arrangementOnly'), True)
                spans = "[...window.__fontkitBridge.targets.values()].filter((r) => r.id.startsWith('auto:span'))"
                frame.evaluate("""() => { const el = document.querySelector('span[data-design-id^="auto:span"]');
                    window.__parent = el.parentNode; window.__span = el; el.remove(); }""")
                frame.wait_for_function(f"{spans}.length === 0")
                start = self.mark(page)
                frame.evaluate("window.__parent.append(window.__span)")
                back = self.wait_message(page, 'design:targets', start, "d.targets.some((t) => t.text === '42 fonts')")
                self.assertNotEqual(back['type'], 'timeout', 'the span coming back was never announced')
                self.assertIs(next(t for t in back['targets'] if t['text'] == '42 fonts').get('arrangementOnly'), True)


class StableSelectorEscapeTests(BridgeCase):
    """data-design-id values can hold any character; the selector the bridge reports never holds a raw special one."""
    IDS = ['hero;alternate', 'a{b}<c>"d\\e', 'x"]{} body{color:red}/*', 'url(x)!important', 'tab\there', 'new\nline', '\u00e9\u4e2d' + 'z' * 40]

    def test_selectors_use_css_escapes_and_match_exactly_their_element(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for design_id in self.IDS:
                    with self.subTest(id=design_id):
                        frame.evaluate("""([id]) => { const el = document.querySelector('#footer-note');
                            el.setAttribute('data-design-id', id); document.body.append(document.createElement('i')); }""", [design_id])
                        start = self.mark(page)
                        self.wait_message(page, 'design:targets', start, f'd.targets.some((t) => t.id === {json.dumps(design_id)})')
                        self.control(page, {'type': 'design:select', 'targetId': design_id})
                        target = self.wait_message(page, 'design:selected', start, f'd.targetId === {json.dumps(design_id)}')['target']
                        selector = target['selector']
                        self.assertTrue(target['stable'])
                        for raw in ';{}<>()/*!\n\t':
                            self.assertNotIn(raw, selector)
                        self.assertEqual(frame.evaluate(
                            '([s, id]) => { const found = [...document.querySelectorAll(s)];'
                            ' return [found.length, found[0] && found[0].getAttribute("data-design-id") === id]; }',
                            [selector, design_id]), [1, True], selector)
                        reply = self.applied(page, design_id, {'fontSize': 21})
                        self.assertEqual(self.entry(reply['changes'], design_id)['selector'], selector)
                        self.request(page, {'type': 'design:reset', 'targetId': design_id})


class AssetPlacementTests(BridgeCase):
    """Legacy image slots: assets render only as <img>, never as live SVG markup."""

    def place(self, page, target_id, url, width=30):
        reply = self.request(page, {'type': 'design:update', 'patch': {'slots': [
            {'id': 'img-slot', 'targetId': target_id, 'type': 'image', 'assetDataUrl': url,
             'imageWidth': width, 'opacity': 1}]}})
        self.assertEqual(reply.get('type'), 'design:applied', reply)
        return reply

    def test_svg_payloads_never_execute_in_the_target(self):
        payloads = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<script>window.__pwned = "script"</script><rect width="10" height="10"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<image href="missing.png" onerror="window.__pwned = \'image\'"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><foreignObject width="10" height="10">'
            '<img xmlns="http://www.w3.org/1999/xhtml" src="missing.png" onerror="window.__pwned = \'foreign\'"/>'
            '</foreignObject></svg>',
        ]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for svg in payloads:
                    for target_id in (MARK, SLOT, PHOTO):
                        self.place(page, target_id, 'data:image/svg+xml,' + quote(svg))
                        page.wait_for_timeout(150)
                page.wait_for_timeout(300)
                self.assertIsNone(frame.evaluate('window.__pwned'))
                self.assertEqual(frame.evaluate(
                    "document.querySelectorAll('main script, main foreignObject, main image').length"), 0)
                self.assertEqual(self.errors(frame), [])

    def test_base64_svg_from_read_as_data_url_replaces_an_inline_svg_until_reset(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                url = page.evaluate("""() => new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(new Blob(['<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30">'
                        + '<rect width="30" height="30" fill="red"/></svg>'], { type: 'image/svg+xml' }));
                })""")
                self.assertTrue(url.startswith('data:image/svg+xml;base64,'))
                reply = self.place(page, MARK, url, width=30)
                self.assertNotIn(MARK, [e['targetId'] for e in reply['changes']['targets']
                                        if 'flex' in str(e['declarations'])])
                probe = """() => {
                    const svg = document.querySelector('[data-design-id="landing.mark"]');
                    const img = svg.nextElementSibling;
                    return { display: getComputedStyle(svg).display, style: svg.getAttribute('style'),
                             inner: svg.querySelectorAll('img').length, tag: img.localName,
                             placed: img.classList.contains('fontkit-placed-asset'), src: img.getAttribute('src'),
                             width: img.getBoundingClientRect().width, loaded: img.complete && img.naturalWidth };
                }"""
                frame.wait_for_function(
                    "() => { const i = document.querySelector('.fontkit-placed-asset'); return i && i.complete; }")
                placed = frame.evaluate(probe)
                self.assertEqual((placed['display'], placed['inner'], placed['tag'], placed['placed'], placed['src']),
                                 ('none', 0, 'img', True, url))
                self.assertNotIn('flex', placed['style'])
                self.assertEqual(placed['loaded'], 30)
                self.assertEqual(placed['width'], 30)
                self.assertNotIn(':img:', ' '.join(
                    t['id'] for t in page.evaluate("() => hello('s2')")['targets']))

                self.request(page, {'type': 'design:reset'})
                self.assertEqual(frame.evaluate("document.querySelectorAll('.fontkit-placed-asset').length"), 0)
                self.assertIsNone(self.style_attr(frame, MARK))
                self.assertEqual(self.computed(frame, MARK, 'display'), 'inline')

    def test_only_png_and_svg_data_urls_are_placed(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                requests = []
                page.on('request', lambda request: requests.append(request.url))
                self.hello(page)
                original = self.element(frame, PHOTO, "(el) => el.getAttribute('src')")
                for url in ('javascript:window.__pwned=1', 'https://evil.test/beacon.png',
                            'data:text/html;base64,PHNjcmlwdD4=', 'data:image/gif;base64,R0lGODlhAQABAAAAACw=',
                            'DATA:image/png;base64,not base64!'):
                    for target_id in (PHOTO, SLOT, MARK):
                        self.place(page, target_id, url)
                self.assertEqual(self.element(frame, PHOTO, "(el) => el.getAttribute('src')"), original)
                self.assertEqual(self.element(frame, SLOT, '(el) => el.childNodes.length'), 0)
                self.assertEqual(frame.evaluate("document.querySelectorAll('.fontkit-placed-asset').length"), 0)
                self.assertEqual([u for u in requests if 'evil.test' in u], [])

                png = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEklEQVR42mP8z8Dw'
                       'nwEJMCHzAEFKAgS0PjzbAAAAAElFTkSuQmCC')
                self.place(page, PHOTO, png, width=24)
                self.place(page, SLOT, png, width=24)
                self.assertEqual(self.element(frame, PHOTO, "(el) => el.getAttribute('src')"), png)
                self.assertEqual(self.element(frame, SLOT, "(el) => el.querySelector('img.fontkit-placed-asset').getAttribute('src')"), png)
                self.request(page, {'type': 'design:reset'})
                self.assertEqual(self.element(frame, PHOTO, "(el) => el.getAttribute('src')"), original)
                self.assertEqual(self.element(frame, SLOT, '(el) => el.childNodes.length'), 0)
                self.assertIsNone(self.style_attr(frame, SLOT))


# Labels of an element's children in DOM order: author id, else element id, else text.
CHILD_LABELS = """(sel) => [...document.querySelector(sel).children]
    .filter((el) => !['SCRIPT', 'STYLE'].includes(el.tagName))
    .map((el) => {
        const id = el.getAttribute('data-design-id');
        return id && !id.startsWith('auto:') ? id : (el.id || el.textContent.trim());
    })"""

GROUP = ['arr.btn.a', 'arr.btn.b', 'arr.btn.c']
PLAIN = ['arr.p.1', 'arr.p.2', 'arr.p.3']
BULK_ARRANGEMENT_KEYS = {'containerKey', 'containerName', 'containerSelector', 'index', 'count',
                         'cssOrderAvailable', 'frameworkManaged'}
ARRANGEMENT_KEYS = BULK_ARRANGEMENT_KEYS | {'siblings', 'containers'}
DEMO_PAGE = f'{TARGET}/demo/'


class ArrangeCase(BridgeCase):
    def select_manifest(self, page, target_id):
        """The single-target manifest (full arrangement, with candidate containers)."""
        start = self.mark(page)
        self.control(page, {'type': 'design:select', 'targetId': target_id})
        return self.wait_message(page, 'design:selected', start, f"d.targetId === '{target_id}'")['target']

    def start(self, engine):
        page, frame = self.open(engine, target=ARRANGE_PAGE)
        ready = self.hello(page)
        return page, frame, ready

    def move(self, page, target_id, to, **extra):
        return self.request(page, {'type': 'design:move', 'targetId': target_id, 'to': to, **extra})

    def moved(self, page, target_id, to, **extra):
        reply = self.move(page, target_id, to, **extra)
        self.assertEqual(reply.get('type'), 'design:applied', reply)
        return reply

    def labels(self, frame, selector):
        return frame.evaluate(CHILD_LABELS, selector)

    def rejected(self, reply, reason):
        self.assertEqual(reply.get('type'), 'design:rejected', reply)
        self.assertEqual(reply['reason'], reason, reply)
        return reply.get('detail') or {}

    def auto_id(self, ready, selector):
        return next(t['id'] for t in ready['targets'] if t['selector'] == selector)


class ArrangementManifestTests(ArrangeCase):
    def test_manifest_arrangement_describes_siblings_containers_and_capabilities(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                by_id = {t['id']: t for t in ready['targets']}
                # Bulk manifests carry no candidate containers (they would grow quadratically).
                for target in ready['targets']:
                    self.assertEqual(set(target['arrangement']), BULK_ARRANGEMENT_KEYS, target['id'])
                selected_button = self.select_manifest(page, 'arr.btn.b')
                self.assertEqual(set(selected_button['arrangement']), ARRANGEMENT_KEYS)

                button = selected_button['arrangement']
                self.assertEqual((button['containerKey'], button['index'], button['count']), ('arr.group', 1, 3))
                self.assertEqual([s['id'] for s in button['siblings']], GROUP)
                self.assertEqual(set(button['siblings'][0]), {'id', 'name', 'tag'})
                self.assertEqual(button['siblings'][0]['tag'], 'button')
                self.assertEqual(button['containerSelector'], '[data-design-id="arr.group"]')
                self.assertTrue(button['containerName'])
                self.assertIs(button['cssOrderAvailable'], True)
                self.assertIsNone(button['frameworkManaged'])

                # A grid container without an author id gets a bridge-assigned key, and its
                # un-annotated card is registered so every sibling has an id.
                card = self.select_manifest(page, 'arr.card.2')['arrangement']
                self.assertRegex(card['containerKey'], r'^container:\d+$')
                self.assertEqual(card['containerSelector'], '#card-grid')
                self.assertEqual((card['index'], card['count']), (1, 4))
                self.assertIs(card['cssOrderAvailable'], True)
                self.assertTrue(card['siblings'][2]['id'].startswith('auto:'))
                self.assertTrue(all(s['id'] in by_id for s in card['siblings']))
                self.assertEqual(by_id['arr.card.1']['arrangement']['containerKey'], card['containerKey'])
                self.assertEqual((by_id['arr.btn.b']['arrangement']['index'], by_id['arr.btn.b']['arrangement']['count']), (1, 3))

                # script/style siblings are not part of the arrangement.
                plain = self.select_manifest(page, 'arr.p.2')['arrangement']
                self.assertEqual([s['id'] for s in plain['siblings']], PLAIN)
                self.assertIs(plain['cssOrderAvailable'], False)

                # Candidate destinations: order containers plus parents of >= 2 targets.
                containers = {c['key']: c for c in selected_button['arrangement']['containers']}
                for key in ('arr.group', 'arr.plain', 'arr.outside', 'arr.form', 'arr.seg', card['containerKey']):
                    self.assertIn(key, containers)
                    self.assertEqual(set(containers[key]), {'key', 'name'})
                    self.assertTrue(containers[key]['name'])
                self.assertEqual(len(containers), len(selected_button['arrangement']['containers']))

                for target_id, framework in (('arr.react.b', 'react'), ('arr.vue.b', 'vue'),
                                             ('arr.svelte.b', 'svelte'), ('arr.ng.b', 'unknown'),
                                             ('arr.react', 'react'), ('arr.btn.a', None)):
                    self.assertEqual(by_id[target_id]['arrangement']['frameworkManaged'], framework, target_id)

                # The same data arrives with selection and with every applied reply.
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': 'arr.btn.c'})
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual(selected['target']['arrangement']['index'], 2)
                reply = self.applied(page, 'arr.btn.c', {'fontSize': 12})
                self.assertEqual(reply['target']['arrangement']['siblings'][2]['id'], 'arr.btn.c')

    def test_bulk_manifests_never_carry_siblings_or_containers(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const list = document.createElement('div');
                    list.id = 'big-list';
                    for (let i = 0; i < 150; i += 1) {
                        const button = document.createElement('button');
                        button.textContent = 'Item ' + i;
                        list.appendChild(button);
                    }
                    document.querySelector('main').appendChild(list);
                }""")
                ready = self.hello(page)
                item = next(t for t in ready['targets'] if t['text'] == 'Item 70')
                arrangement = item['arrangement']
                self.assertEqual((arrangement['index'], arrangement['count']), (70, 150))
                self.assertNotIn('siblings', arrangement)
                self.assertNotIn('containers', arrangement)
                self.assertLess(len(str(ready)), 600000)
                # A selection (and every applied reply) carries the full list.
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': item['id']})
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual(len(selected['target']['arrangement']['siblings']), 150)
                self.assertEqual(selected['target']['arrangement']['siblings'][70]['id'], item['id'])
                reply = self.moved_in_big_list(page, item['id'])
                self.assertEqual(reply['target']['arrangement']['index'], 0)

    def moved_in_big_list(self, page, target_id):
        reply = self.request(page, {'type': 'design:move', 'targetId': target_id, 'to': {'index': 0}})
        self.assertEqual(reply['type'], 'design:applied', reply)
        return reply

    def test_sibling_only_registrations_are_flagged_and_stay_addressable(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                by_id = {t['id']: t for t in ready['targets']}
                card = next(t for t in ready['targets'] if t['text'] == 'Card three' and t['tag'] == 'article')
                grid = next(t for t in ready['targets'] if t['selector'] == '#card-grid')
                self.assertIs(card['arrangementOnly'], True)
                self.assertIs(grid['arrangementOnly'], True)
                # Author ids and semantic/role targets are ordinary targets.
                for target_id in ('arr.btn.a', 'arr.card.1', 'arr.p.1', 'arr.group'):
                    self.assertNotIn('arrangementOnly', by_id[target_id])
                heading = next(t for t in ready['targets'] if t['text'] == 'Card three' and t['tag'] == 'h3')
                self.assertNotIn('arrangementOnly', heading)
                # Still selectable and movable by id.
                selected = self.select_manifest(page, card['id'])
                self.assertIs(selected['arrangementOnly'], True)
                self.moved(page, card['id'], {'index': 0})
                self.assertEqual(self.labels(frame, '#card-grid')[0], 'Card three')

    def test_twenty_sections_of_a_hundred_targets_stay_near_linear(self):
        def build(frame, sections):
            frame.evaluate("""(sections) => {
                const host = document.createElement('div');
                for (let s = 0; s < sections; s += 1) {
                    const section = document.createElement('section');
                    for (let p = 0; p < 100; p += 1) {
                        const para = document.createElement('p');
                        para.textContent = 'S' + s + ' P' + p;
                        section.appendChild(para);
                    }
                    host.appendChild(section);
                }
                document.querySelector('main').appendChild(host);
            }""", sections)

        sizes = {}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for sections in (10, 20):
                    page, frame = self.open(engine)
                    build(frame, sections)
                    ready = self.hello(page)
                    sizes[sections] = len(json.dumps(ready))
                self.assertGreater(len(ready['targets']), 2000)
                self.assertLess(sizes[20] / sizes[10], 2.3, sizes)
                self.assertLess(sizes[20] / len(ready['targets']), 1500, sizes)
                self.assertLess(sizes[20], 3_000_000, sizes)

    def test_container_names_prefer_design_name_aria_label_heading_id_then_tag_class(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ARRANGE_PAGE)
                frame.evaluate("""() => {
                    document.querySelector('.plain').setAttribute('data-design-name', 'Plain list');
                    const long = document.createElement('h2');
                    long.textContent = 'A very long heading that goes on well past forty characters';
                    document.querySelector('.react-root').prepend(long);
                }""")
                self.hello(page)
                containers = {c['key']: c['name'] for c in
                              self.select_manifest(page, 'arr.btn.b')['arrangement']['containers']}
                self.assertEqual(containers['arr.plain'], 'Plain list')           # data-design-name
                self.assertEqual(containers['arr.group'], 'Actions')              # aria-label
                self.assertEqual(containers['arr.outside'], '#outside')           # no heading, has id
                self.assertEqual(containers['arr.seg'], 'fieldset.seg')           # tag.class
                grid = next(name for key, name in containers.items() if key.startswith('container:') and name == 'Card one')
                self.assertEqual(grid, 'Card one')                                # first heading text
                self.assertLessEqual(len(containers['arr.react']), 40)
                self.assertTrue(containers['arr.react'].startswith('A very long heading'))

    def test_ready_and_targets_messages_grow_near_linearly_with_the_page(self):
        def build(frame, sections):
            frame.evaluate("""(sections) => {
                const host = document.createElement('div');
                for (let s = 0; s < sections; s += 1) {
                    const section = document.createElement('section');
                    section.className = 'block-' + s;
                    for (let p = 0; p < 12; p += 1) {
                        const para = document.createElement('p');
                        para.textContent = 'Section ' + s + ' paragraph ' + p;
                        section.appendChild(para);
                    }
                    host.appendChild(section);
                }
                document.querySelector('main').appendChild(host);
            }""", sections)

        sizes = {}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for sections in (30, 60):
                    page, frame = self.open(engine)
                    build(frame, sections)
                    ready = self.hello(page)
                    sizes[sections] = len(json.dumps(ready))
                    self.assertGreater(len(ready['targets']), sections * 12)
                self.assertGreater(len(ready['targets']), 700)
                # Roughly doubling the page may not much more than double the message.
                self.assertLess(sizes[60] / sizes[30], 2.4, sizes)
                # About 1.7 KB per target here (the old per-target containers list made it 4.9 KB and growing).
                self.assertLess(sizes[60] / len(ready['targets']), 2500, sizes)
                self.assertLess(sizes[60], 2_000_000, sizes)
                # design:targets after a late addition is bulk too.
                start = self.mark(page)
                frame.evaluate("""() => {
                    const late = document.createElement('p');
                    late.textContent = 'Late paragraph';
                    document.querySelector('.block-3').appendChild(late);
                }""")
                announced = self.wait_message(page, 'design:targets', start)
                self.assertLess(len(json.dumps(announced)), 2_000_000)
                self.assertTrue(all('containers' not in t['arrangement'] for t in announced['targets']))

    def test_a_target_is_not_offered_itself_or_its_descendants_as_a_destination(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                form = self.select_manifest(page, 'arr.form')
                keys = [c['key'] for c in form['arrangement']['containers']]
                self.assertNotIn('arr.form', keys)
                self.assertNotIn('arr.seg', keys)
                self.assertIn('arr.group', keys)

    def test_move_and_overlay_and_fonts_are_ignored_before_hello(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ARRANGE_PAGE)
                before = frame.evaluate("document.querySelector('main').innerHTML")
                page.evaluate('(m) => send(m)', {
                    'type': 'design:move', 'protocolVersion': 1, 'sessionId': 's1', 'requestId': 'm1',
                    'baseRevision': 0, 'targetId': 'arr.btn.a', 'to': {'index': 2}})
                page.evaluate('(m) => send(m)', {
                    'type': 'design:mode', 'protocolVersion': 1, 'sessionId': 's1', 'overlay': True})
                page.evaluate('(m) => send(m)', {
                    'type': 'design:update', 'protocolVersion': 1, 'sessionId': 's1', 'requestId': 'm2',
                    'baseRevision': 0, 'targetId': 'arr.btn.a',
                    'patch': {'fontStylesheet': 'https://use.typekit.net/abc123.css'}})
                page.wait_for_timeout(300)
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), before)
                self.assertEqual(frame.evaluate("document.querySelectorAll('[id^=\"fontkit-bridge\"], link[data-fontkit-font]').length"), 0)
                self.assertEqual(self.messages(page, 'design:applied') + self.messages(page, 'design:rejected'), [])


class MoveTests(ArrangeCase):
    def test_move_by_index_reorders_the_dom_and_reports_the_canonical_move(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                reply = self.moved(page, 'arr.btn.a', {'index': 2})
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.b', 'arr.btn.c', 'arr.btn.a'])
                self.assertEqual((reply['targetId'], reply['revision']), ('arr.btn.a', 1))
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 2}})
                self.assertEqual(reply['target']['arrangement']['index'], 2)
                self.assertEqual([s['id'] for s in reply['target']['arrangement']['siblings']],
                                 ['arr.btn.b', 'arr.btn.c', 'arr.btn.a'])

                reply = self.moved(page, 'arr.btn.c', {'index': 0})
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.c', 'arr.btn.b', 'arr.btn.a'])
                self.assertEqual(reply['revision'], 2)

                # Moving to the position it already has is a successful no-op.
                reply = self.moved(page, 'arr.btn.c', {'index': 0})
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.c', 'arr.btn.b', 'arr.btn.a'])
                self.assertEqual((reply['revision'], reply['canonicalPatch']['move']['index']), (3, 0))

                # Auto-registered grid siblings move like any other.
                ready = self.hello(page, 's2')
                card = next(t for t in ready['targets'] if t['text'] == 'Card three' and t['tag'] == 'article')
                self.moved(page, card['id'], {'index': 0})
                self.assertEqual(self.labels(frame, '#card-grid'),
                                 ['Card three', 'arr.card.1', 'arr.card.2', 'arr.card.4'])
                self.assertEqual(self.errors(frame), [])

    def test_selectors_in_move_replies_describe_the_new_position(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                card = next(t for t in ready['targets'] if t['text'] == 'Card three' and t['tag'] == 'article')
                before = card['selector']
                reply = self.moved(page, card['id'], {'index': 0})
                after = reply['target']['selector']
                self.assertNotEqual(before, after)
                found = frame.evaluate("(sel) => [...document.querySelectorAll(sel)].map((el) => el.textContent.trim())", after)
                self.assertEqual(found, ['Card three'])
                structure = reply['changes']['structure'][0]
                self.assertEqual(frame.evaluate('(sel) => document.querySelectorAll(sel).length', structure['selector']), 1)

    def test_move_before_after_and_across_containers(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                reply = self.moved(page, 'arr.btn.c', {'before': 'arr.btn.a'})
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.c', 'arr.btn.a', 'arr.btn.b'])
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 0}})
                reply = self.moved(page, 'arr.btn.c', {'after': 'arr.btn.b'})
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP)
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 2}})

                # A reference in another container moves the target into that container.
                reply = self.moved(page, 'arr.btn.a', {'after': 'arr.p.1'})
                self.assertEqual(self.labels(frame, '.plain'), ['arr.p.1', 'arr.btn.a', 'arr.p.2', 'arr.p.3'])
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.b', 'arr.btn.c'])
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.plain', 'index': 1}})
                self.assertEqual(reply['target']['arrangement']['containerKey'], 'arr.plain')
                self.moved(page, 'arr.btn.a', {'before': 'arr.btn.b'})
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP)
                self.assertEqual(self.errors(frame), [])

    def test_move_into_a_container_appends_by_default_or_goes_to_the_index(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                reply = self.moved(page, 'arr.p.3', {'container': 'arr.group'})
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP + ['arr.p.3'])
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 3}})
                reply = self.moved(page, 'arr.p.2', {'container': 'arr.group', 'index': 0})
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.p.2'] + GROUP + ['arr.p.3'])
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 0}})
                # An index equal to the count appends; the same container with no index appends.
                self.moved(page, 'arr.p.1', {'container': 'arr.group', 'index': 5})
                self.assertEqual(self.labels(frame, '.btn-group')[-1], 'arr.p.1')
                reply = self.moved(page, 'arr.btn.a', {'container': 'arr.group'})
                self.assertEqual(self.labels(frame, '.btn-group')[-1], 'arr.btn.a')
                self.assertEqual(reply['canonicalPatch']['move']['index'], 5)
                self.assertEqual(self.labels(frame, '.plain'), [])
                self.assertEqual(self.errors(frame), [])

    def test_every_invalid_move_is_rejected_and_changes_nothing(self):
        cases = [
            # (message fields, reason, detail subset)
            ({'targetId': 'arr.btn.a'}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': []}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': 'last'}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': {}}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': {'foo': 1}}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 1, 'before': 'arr.btn.b'}}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': {'before': 'arr.btn.b', 'after': 'arr.btn.c'}}, 'invalid-message', {'field': 'to'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 'one'}}, 'invalid-message', {'field': 'to.index'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 1.5}}, 'invalid-message', {'field': 'to.index'}),
            ({'targetId': 'arr.btn.a', 'to': {'before': ''}}, 'invalid-message', {'field': 'to.before'}),
            ({'targetId': 'arr.btn.a', 'to': {'after': 7}}, 'invalid-message', {'field': 'to.after'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 5}}, 'invalid-message', {'field': 'to.container'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'arr.plain', 'index': 'x'}}, 'invalid-message', {'field': 'to.index'}),
            ({'targetId': 5, 'to': {'index': 1}}, 'invalid-message', {'field': 'targetId'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 1}, 'strategy': 5}, 'invalid-message', {'field': 'strategy'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 1}, 'force': 'yes'}, 'invalid-message', {'field': 'force'}),
            ({'targetId': 'no.such.target', 'to': {'index': 1}}, 'unknown-target', {'targetId': 'no.such.target'}),
            ({'targetId': 'arr.btn.a', 'to': {'before': 'no.such.target'}}, 'unknown-target', {'targetId': 'no.such.target'}),
            ({'targetId': 'arr.btn.a', 'to': {'after': 'no.such.target'}}, 'unknown-target', {'targetId': 'no.such.target'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 3}}, 'unsupported-value', {'reason': 'index-out-of-range'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': -1}}, 'unsupported-value', {'reason': 'index-out-of-range'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'arr.plain', 'index': 4}}, 'unsupported-value', {'reason': 'index-out-of-range'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'no.such.container'}}, 'unsupported-value', {'reason': 'unknown-container'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'container:999'}}, 'unsupported-value', {'reason': 'unknown-container'}),
            ({'targetId': 'arr.group', 'to': {'container': 'arr.group'}}, 'unsupported-value', {'reason': 'into-self'}),
            ({'targetId': 'arr.form', 'to': {'container': 'arr.seg'}}, 'unsupported-value', {'reason': 'into-descendant'}),
            ({'targetId': 'arr.group', 'to': {'before': 'arr.btn.a'}}, 'unsupported-value', {'reason': 'into-descendant'}),
            ({'targetId': 'arr.btn.a', 'to': {'before': 'arr.btn.a'}}, 'unsupported-value', {'reason': 'relative-to-self'}),
            ({'targetId': 'arr.btn.a', 'to': {'after': 'arr.btn.a'}}, 'unsupported-value', {'reason': 'relative-to-self'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'arr.img'}}, 'unsupported-value', {'reason': 'void-or-replaced-container'}),
            ({'targetId': 'arr.btn.a', 'to': {'container': 'arr.email'}}, 'unsupported-value', {'reason': 'void-or-replaced-container'}),
            ({'targetId': 'arr.btn.a', 'to': {'index': 1}, 'strategy': 'sideways'}, 'unsupported-value', {'property': 'strategy', 'requested': 'sideways'}),
        ]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                snapshot = frame.evaluate("document.querySelector('main').innerHTML")
                for fields, reason, expected in cases:
                    with self.subTest(fields=fields):
                        reply = self.request(page, {'type': 'design:move', **fields})
                        detail = self.rejected(reply, reason)
                        for key, value in expected.items():
                            self.assertEqual(detail.get(key), value, reply)
                        self.assertEqual(reply['revision'], 0)
                reply = self.request(page, {'type': 'design:move', 'targetId': 'arr.btn.a', 'to': {'index': 1},
                                            'baseRevision': 99})
                self.assertEqual(self.rejected(reply, 'revision-conflict'), {'baseRevision': 99, 'revision': 0})
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), snapshot)
                self.assertEqual(self.errors(frame), [])

    def test_ledger_structure_reports_changed_containers_and_reset_restores_the_order(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                self.assertEqual(ready['changes']['structure'], [])
                original = frame.evaluate("document.querySelector('main').innerHTML")
                original_group = frame.evaluate("document.querySelector('.btn-group').outerHTML")

                reply = self.moved(page, 'arr.p.3', {'container': 'arr.group', 'index': 0})
                structure = reply['changes']['structure']
                self.assertEqual([e['containerKey'] for e in structure], ['arr.plain', 'arr.group'])
                group = structure[1]
                self.assertEqual(set(group), {'containerKey', 'selector', 'stable', 'name', 'html', 'order', 'orderIds'})
                self.assertEqual((group['selector'], group['stable']), ('[data-design-id="arr.group"]', True))
                self.assertEqual(len(group['order']), 4)
                self.assertEqual(group['order'], [s['name'] for s in reply['target']['arrangement']['siblings']])
                # orderIds names the same children by target id, in the same order, so a saved order can be replayed.
                self.assertEqual(group['orderIds'], [s['id'] for s in reply['target']['arrangement']['siblings']])
                self.assertEqual(group['orderIds'][0], 'arr.p.3')
                self.assertEqual(len(group['orderIds']), len(group['order']))
                self.assertEqual(len(structure[0]['orderIds']), 2)
                self.assertTrue(group['html'].startswith('<div class="btn-group" data-design-id="arr.group"'))
                self.assertIn('Plain three', group['html'])
                self.assertNotIn('auto:', group['html'])
                self.assertNotIn('data-design-role', group['html'])
                self.assertNotIn('data-design-name', group['html'])
                self.assertNotIn('!important', group['html'])
                self.assertEqual(len(structure[0]['order']), 2)

                # Styles on moved children are stripped from the container html; the ledger keeps them.
                reply = self.applied(page, 'arr.btn.a', {'color': '#ff0000'})
                self.assertNotIn('#ff0000', reply['changes']['structure'][1]['html'])
                self.assertNotIn('color', reply['changes']['structure'][1]['html'])

                # Resetting the target puts it back in its original container and position.
                reply = self.request(page, {'type': 'design:reset', 'targetId': 'arr.p.3'})
                self.assertIs(reply['reset'], True)
                self.assertEqual(self.labels(frame, '.plain'), PLAIN)
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP)
                self.assertEqual(reply['changes']['structure'], [])
                self.assertEqual(reply['target']['arrangement']['containerKey'], 'arr.plain')
                self.assertEqual(reply['target']['arrangement']['index'], 2)

                # Moving back to the original position leaves no structure entry either.
                reply = self.moved(page, 'arr.btn.a', {'index': 2})
                self.assertEqual(len(reply['changes']['structure']), 1)
                reply = self.moved(page, 'arr.btn.a', {'index': 0})
                self.assertEqual(reply['changes']['structure'], [])

                # Reset-all restores every original order, byte for byte.
                self.moved(page, 'arr.btn.c', {'index': 0})
                self.moved(page, 'arr.p.1', {'container': 'arr.group'})
                self.moved(page, 'arr.card.4', {'index': 0})
                self.moved(page, 'arr.seg.c', {'index': 0})
                self.assertNotEqual(frame.evaluate("document.querySelector('main').innerHTML"), original)
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes'], {'tokens': {}, 'targets': [], 'structure': [], 'imports': []})
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), original)
                self.assertEqual(frame.evaluate("document.querySelector('.btn-group').outerHTML"), original_group)
                self.assertEqual(self.errors(frame), [])

    def test_children_the_app_adds_do_not_count_as_structural_changes(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                reply = self.moved(page, 'arr.btn.a', {'index': 2})
                self.assertEqual(len(reply['changes']['structure']), 1)
                frame.evaluate("""() => {
                    const extra = document.createElement('button');
                    extra.id = 'extra';
                    document.querySelector('.btn-group').appendChild(extra);
                }""")
                reply = self.moved(page, 'arr.btn.a', {'index': 0})
                self.assertEqual(reply['changes']['structure'], [])
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP + ['extra'])
                # App-added children are never rearranged by reset-all either.
                self.moved(page, 'arr.btn.c', {'index': 0})
                self.request(page, {'type': 'design:reset'})
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP + ['extra'])

    def test_reset_all_does_not_resurrect_children_the_app_removed(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                self.moved(page, 'arr.btn.a', {'index': 2})
                frame.evaluate("document.querySelector('[data-design-id=\"arr.btn.b\"]').remove()")
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['type'], 'design:applied')
                self.assertEqual(self.labels(frame, '.btn-group'), ['arr.btn.a', 'arr.btn.c'])
                self.assertEqual(self.errors(frame), [])


class CssOrderTests(ArrangeCase):
    def orders(self, frame):
        return frame.evaluate("""() => Object.fromEntries([...document.querySelectorAll('.btn-group > button')]
            .map((el) => [el.getAttribute('data-design-id'), getComputedStyle(el).order]))""")

    def test_css_order_strategy_records_order_declarations_without_touching_the_dom(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                before = frame.evaluate("document.querySelector('.btn-group').innerHTML")
                reply = self.moved(page, 'arr.btn.a', {'index': 2}, strategy='css-order')
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP)
                self.assertEqual(self.orders(frame), {'arr.btn.a': '2', 'arr.btn.b': '0', 'arr.btn.c': '1'})
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.group', 'index': 2}})
                self.assertEqual(reply['revision'], 1)
                self.assertEqual(reply['changes']['structure'], [])
                declarations = {e['targetId']: e['declarations'] for e in reply['changes']['targets']}
                self.assertEqual(declarations, {'arr.btn.a': {'order': '2'}, 'arr.btn.b': {'order': '0'},
                                                'arr.btn.c': {'order': '1'}})
                self.assertEqual(self.inline(frame, 'arr.btn.a', 'order'), ['2', 'important'])
                for entry in reply['changes']['targets']:
                    self.assertNotIn('style', entry['html'])

                # The manifest lists siblings in their visual order.
                arrangement = reply['target']['arrangement']
                self.assertEqual(arrangement['index'], 2)
                self.assertEqual([s['id'] for s in arrangement['siblings']], ['arr.btn.b', 'arr.btn.c', 'arr.btn.a'])

                # A second move is relative to the visual order.
                reply = self.moved(page, 'arr.btn.c', {'index': 0}, strategy='css-order')
                self.assertEqual(self.orders(frame), {'arr.btn.a': '2', 'arr.btn.b': '1', 'arr.btn.c': '0'})
                self.assertEqual(self.labels(frame, '.btn-group'), GROUP)

                # Resetting one of the group clears the whole css-order group.
                reply = self.request(page, {'type': 'design:reset', 'targetId': 'arr.btn.a'})
                self.assertEqual(reply['changes']['targets'], [])
                self.assertEqual(self.orders(frame), {'arr.btn.a': '0', 'arr.btn.b': '0', 'arr.btn.c': '0'})
                self.assertEqual(frame.evaluate("document.querySelector('.btn-group').innerHTML"), before)

                self.moved(page, 'arr.btn.b', {'before': 'arr.btn.a'}, strategy='css-order')
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes']['targets'], [])
                self.assertEqual(frame.evaluate("document.querySelector('.btn-group').innerHTML"), before)

    def test_css_order_works_in_grids_and_is_not_blocked_by_framework_ownership(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                reply = self.moved(page, 'arr.card.4', {'index': 0}, strategy='css-order')
                self.assertEqual(self.labels(frame, '#card-grid')[0], 'arr.card.1')
                self.assertEqual(len(reply['changes']['targets']), 4)
                reply = self.moved(page, 'arr.react.c', {'index': 0}, strategy='css-order')
                self.assertEqual(self.labels(frame, '.react-root'), ['arr.react.a', 'arr.react.b', 'arr.react.c'])
                self.assertEqual(reply['target']['arrangement']['frameworkManaged'], 'react')
                self.assertEqual(frame.evaluate("getComputedStyle(document.querySelector("
                                                "'[data-design-id=\"arr.react.c\"]')).order"), '0')
                self.assertEqual(frame.evaluate("getComputedStyle(document.querySelector("
                                                "'[data-design-id=\"arr.react.a\"]')).order"), '1')

    def test_css_order_is_rejected_where_it_cannot_work(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                detail = self.rejected(self.move(page, 'arr.p.2', {'index': 0}, strategy='css-order'),
                                       'unsupported-value')
                self.assertEqual(detail['guard'], 'css-order')
                self.assertEqual(detail['property'], 'strategy')
                detail = self.rejected(self.move(page, 'arr.btn.a', {'container': 'arr.plain'}, strategy='css-order'),
                                       'unsupported-value')
                self.assertEqual(detail['guard'], 'css-order')
                detail = self.rejected(self.move(page, 'arr.btn.a', {'after': 'arr.p.1'}, strategy='css-order'),
                                       'unsupported-value')
                self.assertEqual(detail['guard'], 'css-order')
                self.assertEqual(self.orders(frame), {'arr.btn.a': '0', 'arr.btn.b': '0', 'arr.btn.c': '0'})
                self.assertEqual(self.labels(frame, '.plain'), PLAIN)
                self.assertEqual(self.applied(page, 'arr.btn.a', {'fontSize': 14})['revision'], 1)


class MoveGuardTests(ArrangeCase):
    def guard(self, reply):
        detail = self.rejected(reply, 'unsupported-value')
        self.assertEqual(detail['property'], 'move')
        self.assertTrue(detail['message'])
        return detail

    def test_form_controls_cannot_leave_their_form_owner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                snapshot = frame.evaluate("document.querySelector('main').innerHTML")
                chip = next(t['id'] for t in ready['targets'] if t['text'] == 'Remember me' and t['tag'] == 'label')
                for target_id, to in (('arr.submit', {'container': 'arr.plain'}), ('arr.email', {'before': 'arr.p.1'}),
                                      (chip, {'container': 'arr.outside'}), ('arr.seg', {'container': 'arr.outside'})):
                    detail = self.guard(self.move(page, target_id, to))
                    self.assertEqual((detail['guard'], detail['overridable']), ('form-owner', False), target_id)
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), snapshot)

                # force does not override a form guard; css-order and in-form reorders are fine.
                detail = self.guard(self.move(page, 'arr.submit', {'container': 'arr.plain'}, force=True))
                self.assertEqual(detail['guard'], 'form-owner')
                self.moved(page, 'arr.submit', {'index': 0})
                self.assertEqual(self.labels(frame, '#signup')[0], 'arr.submit')
                # The whole form can move: its controls keep their owner.
                self.moved(page, 'arr.form', {'before': 'arr.p.1'})
                self.assertEqual(self.labels(frame, '.plain')[0], 'arr.form')
                self.assertEqual(self.errors(frame), [])

    def test_radio_inputs_cannot_leave_their_group_but_can_reorder_inside_it(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                radio = self.auto_id(ready, '#plan-b')
                detail = self.guard(self.move(page, radio, {'container': 'arr.form'}))
                self.assertEqual((detail['guard'], detail['overridable']), ('radio-group', False))
                self.moved(page, radio, {'index': 0})
                self.assertEqual(self.labels(frame, '.seg')[0], 'plan-b')
                self.assertTrue(frame.evaluate("document.getElementById('plan-a').checked"))
                self.assertEqual(self.errors(frame), [])

    def test_label_and_aria_references_must_still_resolve_after_the_move(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                # An input leaving the <label> that wraps it loses its implicit label.
                detail = self.guard(self.move(page, 'arr.remember', {'container': 'arr.seg'}))
                self.assertEqual((detail['guard'], detail['overridable']), ('label-reference', False))
                self.assertTrue(frame.evaluate(
                    "document.querySelector('[data-design-id=\"arr.remember\"]').labels.length === 1"))
                # Moving the label together with its input, or label[for] and aria targets, is fine.
                chip = next(t['id'] for t in ready['targets'] if t['text'] == 'Remember me' and t['tag'] == 'label')
                self.moved(page, chip, {'index': 0})
                self.moved(page, 'arr.seg.a', {'container': 'arr.outside'})
                self.moved(page, 'arr.outside.label', {'container': 'arr.plain'})
                self.assertEqual(frame.evaluate(
                    "document.querySelector('label[for=\"plan-a\"]').control.id"), 'plan-a')
                self.assertEqual(frame.evaluate(
                    "document.getElementById('email-label').closest('.plain') !== null"), True)

    def test_framework_managed_subtrees_need_force_unless_css_order_is_used(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                for target_id, framework in (('arr.react.b', 'react'), ('arr.vue.b', 'vue'),
                                             ('arr.svelte.b', 'svelte'), ('arr.ng.b', 'unknown')):
                    detail = self.guard(self.move(page, target_id, {'index': 0}))
                    self.assertEqual((detail['guard'], detail['overridable'], detail['framework']),
                                     ('framework-managed', True, framework), target_id)
                    self.assertEqual(self.request(page, {'type': 'design:move', 'targetId': target_id,
                                                         'to': {'index': 0}, 'force': False})['reason'],
                                     'unsupported-value')
                self.assertEqual(self.labels(frame, '.react-root'), ['arr.react.a', 'arr.react.b', 'arr.react.c'])

                # Moving something into a framework-managed container is the same guard.
                detail = self.guard(self.move(page, 'arr.btn.a', {'container': 'arr.react'}))
                self.assertEqual((detail['guard'], detail['framework']), ('framework-managed', 'react'))

                reply = self.moved(page, 'arr.react.b', {'index': 0}, force=True)
                self.assertEqual(self.labels(frame, '.react-root'), ['arr.react.b', 'arr.react.a', 'arr.react.c'])
                self.assertEqual(reply['canonicalPatch'], {'move': {'container': 'arr.react', 'index': 0}})
                self.moved(page, 'arr.vue.b', {'index': 0}, force=True)
                self.assertEqual(self.labels(frame, '[data-design-id="arr.vue"]'), ['arr.vue.b', 'arr.vue.a'])


class RuntimeWarningTests(ArrangeCase):
    def test_runtime_errors_after_an_update_or_move_are_reported_as_warnings(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                frame.evaluate("window.__throwMode = 'error'")
                start = self.mark(page)
                reply = self.applied(page, 'arr.btn.a', {'fontSize': 20})
                warning = self.wait_message(page, 'design:warning', start)
                self.assertEqual(set(warning), {'type', 'protocolVersion', 'sessionId', 'requestId', 'targetId',
                                                'kind', 'message'})
                self.assertEqual((warning['kind'], warning['requestId'], warning['targetId'], warning['sessionId']),
                                 ('runtime-error', reply['requestId'], 'arr.btn.a', 's1'))
                self.assertIn('app exploded after the change', warning['message'])
                self.assertLessEqual(len(warning['message']), 300)

                frame.evaluate("window.__throwMode = 'reject'")
                start = self.mark(page)
                reply = self.moved(page, 'arr.btn.a', {'index': 2})
                warning = self.wait_message(page, 'design:warning', start)
                self.assertEqual((warning['requestId'], warning['targetId']), (reply['requestId'], 'arr.btn.a'))
                self.assertIn('async app failure', warning['message'])

                frame.evaluate("window.__throwMode = 'long'")
                start = self.mark(page)
                self.applied(page, 'arr.btn.b', {'color': '#00ff00'})
                warning = self.wait_message(page, 'design:warning', start)
                self.assertLessEqual(len(warning['message']), 300)
                self.assertTrue(warning['message'].startswith('xxx') or 'xxx' in warning['message'])

    def test_errors_outside_the_one_second_window_or_after_a_rejection_are_not_reported(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                frame.evaluate("window.__throwMode = 'error'")
                start = self.mark(page)
                rejected = self.update(page, 'arr.btn.a', {'fontSize': 'huge'})
                self.assertEqual(rejected['type'], 'design:rejected')
                frame.evaluate("document.querySelector('[data-design-id=\"arr.btn.c\"]').style.color = 'red'")
                page.wait_for_timeout(200)
                self.assertEqual(self.messages(page, 'design:warning', start), [])

                frame.evaluate("window.__throwMode = null")
                self.applied(page, 'arr.btn.a', {'fontSize': 20})
                page.wait_for_timeout(1150)
                frame.evaluate("window.__throwMode = 'error'")
                start = self.mark(page)
                frame.evaluate("document.querySelector('[data-design-id=\"arr.btn.c\"]').style.color = 'blue'")
                page.wait_for_timeout(300)
                self.assertEqual(self.messages(page, 'design:warning', start), [])


class PopOutOverlayTests(BridgeCase):
    OVERLAY_NODES = "document.querySelectorAll('#fontkit-bridge-overlay, #fontkit-bridge-hover').length"

    def test_overlay_mode_draws_the_bridge_outline_and_removes_it_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.browsers[engine].new_context(viewport={'width': 1200, 'height': 900})
                self.addCleanup(context.close)
                context.add_init_script(ERROR_PROBE)
                route_virtual_origins(context, {STUDIO: FIXTURES, TARGET: REPO})
                studio = context.new_page()
                studio.goto(f'{STUDIO}/host.html')
                with context.expect_page() as popup_info:
                    studio.evaluate('(u) => openPopup(u)', TARGET_PAGE)
                popup = popup_info.value
                self.assertEqual(studio.evaluate('() => popupHello("p1")')['type'], 'design:ready')
                self.assertEqual(popup.evaluate(self.OVERLAY_NODES), 0)

                studio.evaluate("popupControl({type: 'design:mode', mode: 'select', overlay: true})")
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 2')
                for node in ('fontkit-bridge-overlay', 'fontkit-bridge-hover'):
                    self.assertEqual(popup.evaluate(
                        "(id) => getComputedStyle(document.getElementById(id)).pointerEvents", node), 'none')
                # The outlines are never discovered as targets.
                self.assertEqual(popup.evaluate(
                    "[...window.__fontkitBridge.targets.values()]"
                    ".filter((r) => r.element.closest('#fontkit-bridge-overlay, #fontkit-bridge-hover')).length"), 0)

                # Hover draws the dashed outline over the logical target.
                box = popup.locator(f'[data-design-id="{TITLE}"]').bounding_box()
                popup.mouse.move(box['x'] + 20, box['y'] + 10)
                popup.wait_for_function(
                    "getComputedStyle(document.getElementById('fontkit-bridge-hover')).display === 'block'")
                hover = popup.evaluate("(() => { const r = document.getElementById('fontkit-bridge-hover')"
                                       ".getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()")
                self.assertAlmostEqual(hover[1], box['y'], delta=3)
                self.assertAlmostEqual(hover[2], box['width'], delta=4)

                # Selection draws the solid outline.
                studio.evaluate(f"popupControl({{type: 'design:select', targetId: '{LEAD}'}})")
                popup.wait_for_function(
                    "getComputedStyle(document.getElementById('fontkit-bridge-overlay')).display === 'block'")
                lead = popup.locator(f'[data-design-id="{LEAD}"]').bounding_box()
                selected = popup.evaluate("(() => { const r = document.getElementById('fontkit-bridge-overlay')"
                                          ".getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()")
                self.assertAlmostEqual(selected[1], lead['y'], delta=3)

                # Overlay off: the nodes are removed, not just hidden.
                studio.evaluate("popupControl({type: 'design:mode', overlay: false})")
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 0')
                studio.evaluate("popupControl({type: 'design:mode', overlay: true})")
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 2')
                # The existing selection is drawn as soon as the overlay comes back.
                popup.wait_for_function(
                    "getComputedStyle(document.getElementById('fontkit-bridge-overlay')).display === 'block'")

                # A new session starts without an overlay.
                self.assertEqual(studio.evaluate('() => popupHello("p2")')['type'], 'design:ready')
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 0')
                studio.evaluate("popupControl({type: 'design:mode', overlay: true})")
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 2')

                # Malformed overlay values change nothing.
                studio.evaluate("popupControl({type: 'design:mode', overlay: 'yes'})")
                popup.wait_for_timeout(150)
                self.assertEqual(popup.evaluate(self.OVERLAY_NODES), 2)

                # The opener closing removes the overlay without any interaction.
                studio.close()
                popup.wait_for_function(f'{self.OVERLAY_NODES} === 0', timeout=5000)
                self.assertEqual(popup.evaluate('window.__errors'), [])

    def test_overlay_in_an_iframe_follows_the_same_rules(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'overlay': True})
                frame.wait_for_function(f'{self.OVERLAY_NODES} === 2')
                self.assertEqual(self.errors(frame), [])
                self.control(page, {'type': 'design:mode', 'overlay': False})
                frame.wait_for_function(f'{self.OVERLAY_NODES} === 0')
                self.control(page, {'type': 'design:mode', 'overlay': True})
                frame.wait_for_function(f'{self.OVERLAY_NODES} === 2')
                # Interact mode keeps the page usable and reports no hover, overlay or not.
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                page.wait_for_timeout(100)
                frame.locator(f'[data-design-id="{CTA}"]').click()
                self.assertEqual(frame.evaluate('location.hash'), '#clicked')
                self.hello(page, 's2')
                frame.wait_for_function(f'{self.OVERLAY_NODES} === 0')


GOOGLE = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap'
GOOGLE_2 = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;1,700&family=Fira+Code&display=swap'
TYPEKIT = 'https://use.typekit.net/abc123.css'
LINKS = "[...document.head.querySelectorAll('link[data-fontkit-font]')].map((l) => [l.rel, l.getAttribute('href')])"


class FontStylesheetTests(BridgeCase):
    VALID = [
        GOOGLE, GOOGLE_2, TYPEKIT,
        'https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wght@8..144,100..1000',
        'https://fonts.googleapis.com/css2?family=Inter&text=Hello%20World',
        'https://fonts.googleapis.com/css2?family=Inter',
        'https://fonts.googleapis.com/css2?family=Inter%3Awght%40400%3B700&text=a%2Cb%2Bc%20d',
        'https://use.typekit.net/abcdefghij.css',
        'https://use.typekit.net/ABCDEF.css',
    ]
    INVALID = [
        'http://fonts.googleapis.com/css2?family=Inter',
        'https://fonts.googleapis.com/css?family=Inter',
        'https://fonts.googleapis.com/css2',
        'https://fonts.googleapis.com/css2?',
        'https://fonts.googleapis.com/css2?family=Inter&subset=latin',
        'https://fonts.googleapis.com/css2?display=swap',
        'https://fonts.googleapis.com/css2?family=Inter&display=bogus',
        'https://fonts.googleapis.com/css2?family=In ter',
        'https://fonts.googleapis.com/css2?family=Inter&family=',
        'https://fonts.googleapis.com/css2?family=Inter#fragment',
        'https://fonts.googleapis.com/css2?family=<script>',
        'https://fonts.googleapis.com/css2?family=Inter"onload=x',
        'https://fonts.googleapis.com/css2?family=Inter\\x',
        'https://fonts.googleapis.com/css2?family=Inter&text=<b>',
        'https://fonts.googleapis.com/css2?family=Inter&family=Inter&family=Inter&family=Inter&family=Inter'
        '&family=Inter&family=Inter&family=Inter&family=Inter',
        'https://fonts.googleapis.com/css2?family=' + 'A' * 3000,
        'https://fonts.googleapis.com.evil.test/css2?family=Inter',
        'https://evil.test/css2?family=Inter',
        'https://user@fonts.googleapis.com/css2?family=Inter',
        'https://fonts.googleapis.com:8443/css2?family=Inter',
        'https://fonts.googleapis.com/css2/../css?family=Inter',
        ' https://fonts.googleapis.com/css2?family=Inter',
        'https://fonts.googleapis.com/css2?family=Inter\n',
        'https://use.typekit.net/abc12.css',
        'https://use.typekit.net/abcdefghijk.css',
        'https://use.typekit.net/abc-123.css',
        'https://use.typekit.net/abc123.css?x=1',
        'https://use.typekit.net/abc123.css#x',
        'https://use.typekit.net/abc123.js',
        'http://use.typekit.net/abc123.css',
        'https://p.typekit.net/p.css?s=1',
        'https://use.typekit.net.evil.test/abc123.css',
        'javascript:alert(1)',
        'data:text/css,body{color:red}',
        '//fonts.googleapis.com/css2?family=Inter',
        '', 5, True, ['https://use.typekit.net/abc123.css'], {'url': TYPEKIT},
        # Percent-escapes are limited to space, plus, comma, colon, semicolon and at.
        'https://fonts.googleapis.com/css2?family=x%0a&display=swap',
        'https://fonts.googleapis.com/css2?family=Inter&text=%3Cscript%3E',
        'https://fonts.googleapis.com/css2?family=Inter&text=%0a',
        'https://fonts.googleapis.com/css2?family=x%2F..%2F',
        'https://fonts.googleapis.com/css2?family=Inter&text=%22',
        'https://fonts.googleapis.com/css2?family=Inter&text=%27',
        'https://fonts.googleapis.com/css2?family=Inter&text=%00',
        'https://fonts.googleapis.com/css2?family=Inter&text=%5C',
        'https://fonts.googleapis.com/css2?family=Inter&text=%',
        'https://fonts.googleapis.com/css2?family=Inter&text=%2',
    ]

    def links(self, frame):
        return frame.evaluate(LINKS)

    def test_only_strictly_valid_font_stylesheet_urls_are_accepted(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for url in self.INVALID:
                    with self.subTest(url=url):
                        reply = self.update(page, TITLE, {'fontStylesheet': url})
                        self.assertEqual(reply['type'], 'design:rejected', url)
                        self.assertEqual((reply['reason'], reply['detail']['property']),
                                         ('unsupported-value', 'fontStylesheet'))
                        self.assertEqual(reply['detail']['requested'], url)
                self.assertEqual(self.links(frame), [])
                self.assertEqual(self.font_requests, [])
                self.assertEqual(frame.evaluate('window.__fontkitBridge.revision'), 0)

                # A bad stylesheet rejects the whole patch: nothing else is applied.
                reply = self.update(page, TITLE, {'fontSize': 20, 'fontStylesheet': 'https://evil.test/x.css'})
                self.assertEqual(reply['type'], 'design:rejected')
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '40px')

                for url in self.VALID:
                    with self.subTest(url=url):
                        reply = self.applied(page, TITLE, {'fontStylesheet': url})
                        self.assertEqual(reply['canonicalPatch'], {'fontStylesheet': url})
                        self.assertEqual(reply['changes']['imports'], [url])
                        self.assertEqual(self.links(frame), [['stylesheet', url]])
                        self.applied(page, TITLE, {'fontStylesheet': None})
                        self.assertEqual(self.links(frame), [])
                self.assertEqual(self.errors(frame), [])

    def test_stylesheets_are_injected_once_recorded_in_the_ledger_and_removed_by_reset(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.applied(page, TITLE, {'fontStylesheet': GOOGLE, 'fontFamily': 'Inter, sans-serif'})
                self.assertEqual(reply['canonicalPatch'], {'fontStylesheet': GOOGLE, 'fontFamily': 'Inter, sans-serif'})
                self.assertEqual(reply['changes']['imports'], [GOOGLE])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE]])
                frame.wait_for_function("() => document.querySelector('link[data-fontkit-font]').sheet !== null")
                self.assertEqual(self.font_requests, [GOOGLE])
                self.assertEqual(frame.evaluate(
                    "document.querySelector('link[data-fontkit-font]').hasAttribute('data-fontkit-font')"), True)

                # Same URL from another target: still one link, still one import.
                reply = self.applied(page, LEAD, {'fontStylesheet': GOOGLE})
                self.assertEqual(reply['changes']['imports'], [GOOGLE])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE]])

                reply = self.applied(page, TITLE, {'fontStylesheet': TYPEKIT})
                self.assertEqual(reply['changes']['imports'], [GOOGLE, TYPEKIT])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE], ['stylesheet', TYPEKIT]])

                # null drops a target's reference; an unreferenced stylesheet goes away.
                reply = self.applied(page, LEAD, {'fontStylesheet': None})
                self.assertEqual(reply['changes']['imports'], [TYPEKIT])
                self.assertEqual(self.links(frame), [['stylesheet', TYPEKIT]])
                reply = self.applied(page, LEAD, {'fontStylesheet': GOOGLE_2})
                self.assertEqual(reply['changes']['imports'], [TYPEKIT, GOOGLE_2])
                # Resetting a single target releases only its stylesheet.
                reply = self.request(page, {'type': 'design:reset', 'targetId': TITLE})
                self.assertEqual(reply['changes']['imports'], [GOOGLE_2])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE_2]])

                # The ledger is part of design:ready, and reset-all removes everything.
                self.applied(page, TITLE, {'fontStylesheet': GOOGLE})
                ready = self.hello(page, 's2')
                self.assertEqual(ready['changes']['imports'], [GOOGLE_2, GOOGLE])
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes']['imports'], [])
                self.assertEqual(self.links(frame), [])
                reply = self.applied(page, TITLE, {'fontStylesheet': TYPEKIT})
                self.assertEqual(self.links(frame), [['stylesheet', TYPEKIT]])
                self.assertEqual(self.errors(frame), [])

    def test_font_stylesheets_are_allowed_on_any_target_kind(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, MARK, {'fontStylesheet': TYPEKIT})
                self.assertEqual(self.links(frame), [['stylesheet', TYPEKIT]])


class CompositionFontStylesheetTests(BridgeCase):
    """A composition update may carry `fontStylesheets`: the library fonts it sends. They go through the same strict
    allow-list, injection, ledger and reset path as the per-target `fontStylesheet` key."""

    def composition(self, page, sheets, **patch):
        return self.request(page, {'type': 'design:update', 'patch': {**patch, 'fontStylesheets': sheets}})

    def links(self, frame):
        return frame.evaluate(LINKS)

    def test_the_sheets_of_a_composition_update_are_injected_recorded_and_reported(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.composition(page, [GOOGLE, GOOGLE_2, GOOGLE], tokens={'--font-display': 'Inter, sans-serif'})
                self.assertEqual((reply['type'], reply['targetId']), ('design:applied', 'global'))
                self.assertEqual(reply['canonicalPatch']['fontStylesheets'], [GOOGLE, GOOGLE_2], 'unique, in order')
                self.assertEqual(reply['canonicalPatch']['tokens'], {'--font-display': 'Inter, sans-serif'})
                self.assertEqual(reply['changes']['imports'], [GOOGLE, GOOGLE_2])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE], ['stylesheet', GOOGLE_2]])
                frame.wait_for_function("() => [...document.querySelectorAll('link[data-fontkit-font]')].every((l) => l.sheet !== null)")
                self.assertEqual(sorted(self.font_requests), sorted([GOOGLE, GOOGLE_2]))
                # A fresh Studio sees them in design:ready, and a tokens-only update leaves them alone.
                self.assertEqual(self.hello(page, 's2')['changes']['imports'], [GOOGLE, GOOGLE_2])
                reply = self.request(page, {'type': 'design:update', 'patch': {'tokens': {'--font-sans': 'Verdana'}}})
                self.assertNotIn('fontStylesheets', reply['canonicalPatch'])
                self.assertEqual(reply['changes']['imports'], [GOOGLE, GOOGLE_2])
                self.assertEqual(self.errors(frame), [])

    def test_each_update_is_the_complete_set_and_a_target_reference_keeps_a_sheet_alive(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.composition(page, [GOOGLE, GOOGLE_2])
                reply = self.composition(page, [GOOGLE_2, TYPEKIT])
                self.assertEqual(reply['changes']['imports'], [GOOGLE_2, TYPEKIT], 'the dropped sheet is released')
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE_2], ['stylesheet', TYPEKIT]])
                # A target that references the same sheet keeps it when the composition lets go, and vice versa.
                self.applied(page, TITLE, {'fontStylesheet': TYPEKIT})
                reply = self.composition(page, [])
                self.assertEqual(reply['changes']['imports'], [TYPEKIT])
                self.assertEqual(self.links(frame), [['stylesheet', TYPEKIT]])
                self.composition(page, [TYPEKIT])
                reply = self.applied(page, TITLE, {'fontStylesheet': None})
                self.assertEqual(reply['changes']['imports'], [TYPEKIT], 'the composition still needs it')
                reply = self.composition(page, [])
                self.assertEqual(reply['changes']['imports'], [])
                self.assertEqual(self.links(frame), [])
                self.assertEqual(self.errors(frame), [])

    def test_reset_all_removes_the_composition_sheets_and_a_targeted_reset_does_not(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.composition(page, [GOOGLE])
                reply = self.request(page, {'type': 'design:reset', 'targetId': TITLE})
                self.assertEqual(reply['changes']['imports'], [GOOGLE])
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes']['imports'], [])
                self.assertEqual(self.links(frame), [])
                # After a reset the same set can be sent again.
                self.assertEqual(self.composition(page, [GOOGLE])['changes']['imports'], [GOOGLE])
                self.assertEqual(self.links(frame), [['stylesheet', GOOGLE]])

    def test_a_bad_sheet_list_rejects_the_whole_update_and_changes_nothing(self):
        bad_lists = [
            [url for url in FontStylesheetTests.INVALID if isinstance(url, str)],
            'https://use.typekit.net/abc123.css', 5, True, {'a': 1}, None,
            [GOOGLE, 'https://evil.test/x.css'], [GOOGLE, 5], [GOOGLE, None], [[GOOGLE]],
            [f'https://use.typekit.net/abcdef{n:02d}.css' for n in range(17)],
        ]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for sheets in bad_lists[1:] + [[url] for url in bad_lists[0]]:
                    with self.subTest(sheets=str(sheets)[:60]):
                        reply = self.composition(page, sheets, tokens={'--font-display': 'Inter, sans-serif'})
                        self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'unsupported-value'), sheets)
                        self.assertEqual(reply['detail']['property'], 'fontStylesheets')
                        self.assertLessEqual(len(str(reply['detail']['requested'])), 200)
                self.assertEqual(self.links(frame), [])
                self.assertEqual(self.font_requests, [])
                self.assertEqual(frame.evaluate('window.__fontkitBridge.revision'), 0)
                self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--font-display')"), '',
                                 'a rejected update applies none of its tokens either')
                self.assertEqual(self.errors(frame), [])


class SpaRobustnessTests(BridgeCase):
    SPA_TITLE = 'spa.title'

    def title(self, frame, prop):
        return frame.evaluate(
            f"() => document.querySelector('[data-design-id=\"spa.title\"]').{prop}")

    def test_overrides_are_reapplied_when_a_rerender_replaces_the_element(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                self.applied(page, 'spa.title', {'fontSize': 50, 'color': '#ff0000', 'text': 'Edited'})
                frame.evaluate("window.__old = document.querySelector('[data-design-id=\"spa.title\"]')")
                start = self.mark(page)
                frame.evaluate('render()')
                self.assertTrue(frame.evaluate("window.__old !== document.querySelector('[data-design-id=\"spa.title\"]')"))
                frame.wait_for_function(
                    "() => { const h = document.querySelector('[data-design-id=\"spa.title\"]');"
                    " return h.style.fontSize === '50px' && h.textContent === 'Edited'; }")
                self.assertEqual(self.computed(frame, 'spa.title', 'color'), 'rgb(255, 0, 0)')
                self.assertEqual(self.inline(frame, 'spa.title', 'font-size'), ['50px', 'important'])
                # The untouched sibling is not styled, and the app saw no errors.
                self.assertEqual(self.style_attr(frame, 'spa.body'), None)
                self.assertEqual(self.errors(frame), [])

                # The ledger still reports it, against the new element's original text.
                ready = self.hello(page, 's2')
                entry = self.entry(ready['changes'], 'spa.title')
                self.assertEqual(entry['declarations'], {'font-size': '50px', 'color': '#ff0000'})
                self.assertEqual((entry['text'], entry['originalText']), ('Edited', 'Title v1'))

                # Reset-all cleans the replacement element, not just the old one.
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes']['targets'], [])
                self.assertIsNone(self.style_attr(frame, 'spa.title'))
                self.assertEqual(self.text(frame, 'spa.title'), 'Title v1')

    def test_a_burst_of_rerenders_is_debounced_into_one_reapplication(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                self.applied(page, 'spa.title', {'fontSize': 50})
                frame.evaluate('window.styleBatches = 0')
                frame.evaluate("""() => new Promise((resolve) => {
                    let n = 0;
                    const timer = setInterval(() => { render(); if (++n === 6) { clearInterval(timer); resolve(); } }, 4);
                })""")
                frame.wait_for_function(
                    "() => document.querySelector('[data-design-id=\"spa.title\"]').style.fontSize === '50px'")
                page.wait_for_timeout(400)
                self.assertLessEqual(frame.evaluate('window.styleBatches'), 2)
                self.assertEqual(self.errors(frame), [])

    def test_a_page_that_rerenders_on_every_style_change_cannot_trap_the_bridge_in_a_loop(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                self.applied(page, 'spa.title', {'fontSize': 50})
                frame.evaluate('window.pingPong = true; window.renders = 0; render();')
                last = -1
                for _ in range(30):
                    page.wait_for_timeout(700)
                    now = frame.evaluate('window.renders')
                    if now == last:
                        break
                    last = now
                else:
                    self.fail(f'bridge and page kept re-rendering: {last} renders')
                self.assertLessEqual(last, 12)
                # The bridge is still responsive after it gave up on that element.
                frame.evaluate('window.pingPong = false')
                reply = self.applied(page, 'spa.body', {'fontSize': 30})
                self.assertEqual(reply['type'], 'design:applied')

    def test_removing_the_selected_target_clears_the_selection(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': 'spa.body'})
                self.wait_message(page, 'design:selected', start, "d.targetId === 'spa.body'")
                start = self.mark(page)
                frame.evaluate("document.querySelector('[data-design-id=\"spa.body\"]').remove()")
                cleared = self.wait_message(page, 'design:selected', start)
                self.assertEqual(cleared, {'type': 'design:selected', 'protocolVersion': 1,
                                           'sessionId': 's1', 'targetId': None})
                page.wait_for_timeout(300)
                self.assertEqual(len(self.messages(page, 'design:selected', start)), 1)

    def test_a_replaced_selected_target_stays_selected_and_an_auto_target_removal_clears(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': 'spa.title'})
                self.wait_message(page, 'design:selected', start, "d.targetId === 'spa.title'")
                start = self.mark(page)
                frame.evaluate('render()')
                page.wait_for_timeout(500)
                self.assertEqual(self.messages(page, 'design:selected', start), [])
                # The selection now follows the new element: its geometry changes are reported.
                self.applied(page, 'spa.title', {'fontSize': 120})
                self.wait_message(page, 'design:bounds', start, "d.targetId === 'spa.title' && d.rect.height > 100")

                page, frame = self.open(engine)
                ready = self.hello(page)
                card = self.target_by_text(ready, 'Card two')
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': card['id']})
                self.wait_message(page, 'design:selected', start, f"d.targetId === '{card['id']}'")
                start = self.mark(page)
                frame.evaluate("document.querySelectorAll('.card')[1].remove()")
                self.assertIsNone(self.wait_message(page, 'design:selected', start)['targetId'])

    def test_loading_the_script_twice_keeps_a_single_instance(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TWICE_PAGE)
                frame.evaluate('window.__loadedAgain')
                self.assertTrue(frame.evaluate('window.FontKitBridge === window.__firstClass'))
                self.assertTrue(frame.evaluate('window.__fontkitBridge instanceof window.FontKitBridge'))
                self.assertEqual(len(self.messages(page, 'design:bridge-ready')), 1)
                self.hello(page)
                reply = self.applied(page, 'twice.title', {'fontSize': 33})
                page.wait_for_timeout(250)
                self.assertEqual(len(self.messages(page, 'design:ready')), 1)
                self.assertEqual(len(self.messages(page, 'design:applied')), 1)
                self.assertEqual(reply['revision'], 1)
                self.assertEqual(self.errors(frame), [])

    def test_a_later_constructed_instance_replaces_an_unconnected_auto_instance(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, host=EVIL, target=DEFERRED_PAGE)
                frame.wait_for_function('window.__mine')
                self.assertTrue(frame.evaluate('window.__auto !== window.__mine'))
                self.assertTrue(frame.evaluate('window.__mine === window.__fontkitBridge'))
                self.assertEqual(page.evaluate('() => hello("s1")')['type'], 'timeout')
                self.assertEqual(self.messages(page, 'design:ready'), [])

                page, frame = self.open(engine, host=STUDIO, target=DEFERRED_PAGE)
                frame.wait_for_function('window.__mine')
                ready = self.hello(page)
                self.assertEqual([t['id'] for t in ready['targets'] if t['stable']], ['deferred.title'])
                self.assertEqual(len(self.messages(page, 'design:ready')), 1)
                # The replaced instance is fully disposed: it no longer reacts to anything.
                self.assertEqual(frame.evaluate('window.__auto.active'), False)

    def test_a_connected_auto_instance_is_not_replaced(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                warnings = frame.evaluate("""() => {
                    const seen = [];
                    const warn = console.warn;
                    console.warn = (...args) => seen.push(args.join(' '));
                    const same = window.__fontkitBridge;
                    new FontKitBridge({ allowedOrigins: ['http://studio.test'] });
                    console.warn = warn;
                    return { seen, kept: same === window.__fontkitBridge };
                }""")
                self.assertTrue(warnings['kept'])
                self.assertEqual(len(warnings['seen']), 1)
                self.applied(page, TITLE, {'fontSize': 41})

    def test_a_second_constructed_bridge_after_connect_returns_the_connected_one(self):
        """An HMR re-run of `new FontKitBridge(...)` must not add a second bridge that also answers the Studio."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertEqual(len(self.messages(page, 'design:bridge-ready')), 1)
                self.applied(page, TITLE, {'fontSize': 55, 'color': '#336699'})
                self.assertNotEqual(self.style_attr(frame, TITLE), TITLE_STYLE)
                result = frame.evaluate("""() => {
                    const seen = [];
                    const warn = console.warn;
                    console.warn = (...args) => seen.push(args.join(' '));
                    const first = window.__fontkitBridge;
                    const again = new FontKitBridge({ allowedOrigins: ['http://studio.test'], enableHighlightOverlay: true });
                    const twice = new FontKitBridge();
                    console.warn = warn;
                    return { same: again === first && twice === first && window.__fontkitBridge === first,
                             instance: again instanceof FontKitBridge, seen,
                             overlay: first.options.enableHighlightOverlay === true,
                             origins: first.allowedOrigins };
                }""")
                self.assertTrue(result['same'], 'the constructor returns the connected instance')
                self.assertTrue(result['instance'])
                self.assertFalse(result['overlay'], 'the new options are not merged into the running bridge')
                self.assertEqual(result['origins'], ['http://studio.test'], 'an open bridge is narrowed by allowedOrigins')
                self.assertEqual(len(result['seen']), 2)
                self.assertIn('allowedOrigins narrowed to http://studio.test', result['seen'][0])
                self.assertIn('ignored: enableHighlightOverlay', result['seen'][0])
                self.assertIn('options were ignored', result['seen'][1])

                # No second bridge-ready, and a Studio that re-handshakes anyway gets one answer per request.
                page.wait_for_timeout(300)
                self.assertEqual(len(self.messages(page, 'design:bridge-ready')), 1)
                start = self.mark(page)
                self.hello(page, 's2')
                self.assertEqual(len(self.messages(page, 'design:ready', start)), 1)
                reply = self.applied(page, TITLE, {'fontSize': 60})
                page.wait_for_timeout(300)
                self.assertEqual(len(self.messages(page, 'design:applied', start)), 1)
                self.assertEqual(reply['changes']['targets'][0]['declarations']['font-size'], '60px')
                self.assertEqual(self.entry(reply['changes'], TITLE)['originalText'], 'Make type sing')

                # Reset restores the author's inline style byte for byte (one set of originals, captured once).
                reset = self.request(page, {'type': 'design:reset', 'targetId': TITLE})
                self.assertEqual(reset['type'], 'design:applied')
                self.assertEqual(self.style_attr(frame, TITLE), TITLE_STYLE)
                self.assertEqual(self.errors(frame), [])


class RepeatedConstructionTests(BridgeCase):
    """`new FontKitBridge(...)` again on a page that already has a bridge (HMR): what applies and what is ignored."""
    CALL = """(options) => {
        const seen = [];
        const warn = console.warn;
        console.warn = (...args) => seen.push(args.join(' '));
        const first = window.__fontkitBridge;
        const again = new FontKitBridge(options);
        console.warn = warn;
        return { same: again === first, seen, origins: first.allowedOrigins, session: first.sessionId };
    }"""

    def test_a_narrowing_allowed_origins_ends_a_pinned_session_at_a_now_disallowed_origin(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.applied(page, TITLE, {'fontSize': 55})
                result = frame.evaluate(self.CALL, {'allowedOrigins': ['http://other.test'], 'enableHighlightOverlay': True})
                self.assertTrue(result['same'])
                self.assertEqual(result['origins'], ['http://other.test'])
                self.assertIsNone(result['session'], 'the session of the disallowed origin is ended')
                self.assertEqual(len(result['seen']), 1)
                self.assertIn('allowedOrigins narrowed to http://other.test', result['seen'][0])
                self.assertIn('ignored: enableHighlightOverlay', result['seen'][0])
                # Inert: no more answers, no new session from that origin, and the page is the author's again.
                start = self.mark(page)
                reply = self.update(page, TITLE, {'fontSize': 70})
                self.assertEqual(reply['type'], 'timeout')
                self.assertEqual(page.evaluate("() => hello('s2')")['type'], 'timeout')
                self.assertEqual(self.messages(page, 'design:applied', start), [])
                self.assertEqual(self.computed(frame, TITLE, 'fontSize'), '55px', 'no further patch was applied')
                self.assertEqual(frame.evaluate('window.__fontkitBridge.active'), True)
                self.assertEqual(self.errors(frame), [])

    def test_narrowing_keeps_an_allowed_pinned_studio_and_never_widens(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                # Open -> two origins: applied. The pinned Studio is still allowed, so its session continues.
                result = frame.evaluate(self.CALL, {'allowedOrigins': ['http://studio.test', 'http://evil.test']})
                self.assertEqual(result['origins'], ['http://studio.test', 'http://evil.test'])
                self.assertEqual(result['session'], 's1')
                self.applied(page, TITLE, {'fontSize': 55})
                # Wider, or "any origin": ignored, and the warning says so.
                for wider in (['http://studio.test', 'http://evil.test', 'http://third.test'], ['*'], '*', ['http://third.test']):
                    with self.subTest(wider=wider):
                        result = frame.evaluate(self.CALL, {'allowedOrigins': wider})
                        self.assertEqual(result['origins'], ['http://studio.test', 'http://evil.test'])
                        self.assertEqual(result['session'], 's1')
                        self.assertEqual(len(result['seen']), 1)
                        self.assertIn('allowedOrigins ignored', result['seen'][0])
                # Narrower again: the intersection. The allowed Studio can still say hello and edit.
                result = frame.evaluate(self.CALL, {'allowedOrigins': ['http://studio.test']})
                self.assertEqual(result['origins'], ['http://studio.test'])
                ready = self.hello(page, 's2')
                self.assertEqual(ready['type'], 'design:ready')
                self.assertEqual(self.applied(page, TITLE, {'fontSize': 60})['revision'], 2)
                # An empty list narrows to nothing; a call without the option changes nothing.
                result = frame.evaluate(self.CALL, {})
                self.assertEqual(result['origins'], ['http://studio.test'])
                self.assertIn('options were ignored', result['seen'][0])
                result = frame.evaluate(self.CALL, {'allowedOrigins': []})
                self.assertEqual(result['origins'], [])
                self.assertIsNone(result['session'])
                self.assertEqual(self.errors(frame), [])

    def test_a_configured_bridge_is_never_widened_by_a_later_open_call(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=OPTIONS_PAGE)
                self.hello(page)
                self.assertEqual(frame.evaluate('window.__fontkitBridge.allowedOrigins'), ['http://studio.test'])
                for wider in ('*', ['*'], ['http://studio.test', 'http://evil.test'], 'http://evil.test'):
                    result = frame.evaluate(self.CALL, {'allowedOrigins': wider})
                    self.assertEqual(result['origins'], ['http://studio.test'], wider)
                    self.assertIn('allowedOrigins ignored', result['seen'][0])
                    self.assertTrue(result['same'])
                # Values that are not a list of origins are ignored too (never "narrowed" to nothing).
                for odd in (5, {'a': 1}, True):
                    result = frame.evaluate(self.CALL, {'allowedOrigins': odd})
                    self.assertEqual(result['origins'], ['http://studio.test'])
                    self.assertEqual(result['session'], 's1')
                self.assertEqual(self.applied(page, 'options.title', {'fontSize': 22})['type'], 'design:applied')

    def test_a_constructed_bridge_no_studio_has_talked_to_is_replaced_so_new_options_apply(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                result = frame.evaluate("""() => {
                    const auto = window.__fontkitBridge;
                    const mine = new FontKitBridge({ allowedOrigins: ['http://evil.test'] });
                    const later = new FontKitBridge({ allowedOrigins: ['http://studio.test'], enableHighlightOverlay: true });
                    return { autoDisposed: auto.disposed, mineDisposed: mine.disposed, latest: later === window.__fontkitBridge,
                             distinct: later !== mine, origins: later.allowedOrigins, overlay: later.options.enableHighlightOverlay };
                }""")
                self.assertEqual(result, {'autoDisposed': True, 'mineDisposed': True, 'latest': True, 'distinct': True,
                                          'origins': ['http://studio.test'], 'overlay': True})
                ready = self.hello(page)
                self.assertEqual(ready['type'], 'design:ready')
                self.assertEqual(len(self.messages(page, 'design:ready')), 1, 'only the latest bridge answers')
                # Once a Studio has talked to it, it is kept.
                self.assertEqual(frame.evaluate(self.CALL, {'enableHighlightOverlay': False})['same'], True)

    def test_a_disposed_bridge_is_replaced_by_the_next_new(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                result = frame.evaluate("""() => {
                    const first = window.__fontkitBridge;
                    first.dispose();
                    const seen = [];
                    const warn = console.warn;
                    console.warn = (...args) => seen.push(args.join(' '));
                    const next = new FontKitBridge({ enableHighlightOverlay: true, allowedOrigins: ['http://studio.test'] });
                    console.warn = warn;
                    return { replaced: next !== first && next === window.__fontkitBridge, seen,
                             overlay: next.options.enableHighlightOverlay, origins: next.allowedOrigins, active: next.active };
                }""")
                self.assertEqual(result['replaced'], True)
                self.assertEqual(result['seen'], [], 'a disposed bridge is not "an existing bridge": no warning')
                self.assertEqual(result['overlay'], True)
                self.assertEqual(result['origins'], ['http://studio.test'])
                self.assertEqual(self.hello(page, 's2')['type'], 'design:ready')
                self.assertEqual(self.applied(page, TITLE, {'fontSize': 52})['type'], 'design:applied')
                self.assertEqual(self.errors(frame), [])

    def test_new_of_a_subclass_returns_the_running_bridge_and_its_constructor_body_runs_on_it(self):
        """JavaScript semantics: whatever `super()` returns is `this`. Documented in the bridge docblock."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                result = frame.evaluate("""() => {
                    class Mine extends FontKitBridge { constructor(options) { super(options); this.mineRan = true; } }
                    const first = window.__fontkitBridge;
                    const warn = console.warn;
                    console.warn = () => {};
                    const sub = new Mine({ allowedOrigins: ['http://studio.test'] });
                    console.warn = warn;
                    return { same: sub === first, mineRan: first.mineRan === true, global: window.__fontkitBridge === first,
                             origins: first.allowedOrigins };
                }""")
                self.assertEqual(result, {'same': True, 'mineRan': True, 'global': True, 'origins': ['http://studio.test']})
                self.assertEqual(self.applied(page, TITLE, {'fontSize': 52})['type'], 'design:applied')


class LedgerHtmlTests(BridgeCase):
    def test_long_data_urls_are_abbreviated_in_ledger_html(self):
        png = ('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEklEQVR42mP8z8Dw'
               'nwEJMCHzAEFKAgS0PjzbAAAAAElFTkSuQmCC') + 'AAAA' * 3000
        url = 'data:image/png;base64,' + png
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.request(page, {'type': 'design:update', 'patch': {'slots': [
                    {'id': 'img-slot', 'targetId': PHOTO, 'type': 'image', 'assetDataUrl': url,
                     'imageWidth': 24, 'opacity': 1}]}})
                self.assertEqual(reply['type'], 'design:applied')
                self.assertEqual(self.element(frame, PHOTO, "(el) => el.getAttribute('src')"), url)
                html = self.entry(reply['changes'], PHOTO)['html']
                self.assertIn(f'src="data:image/png;base64,…({len(url)} bytes)"', html)
                self.assertNotIn('iVBORw0K', html)
                self.assertLess(len(html), 400)
                self.assertLess(len(str(reply['changes'])), 2000)
                # Short data URLs stay as they are.
                short = self.applied(page, LEAD, {'fontSize': 20})
                self.assertIn('Lead copy', self.entry(short['changes'], LEAD)['html'])
                self.request(page, {'type': 'design:reset'})
                self.assertIn('data:image/png;base64,iVBORw0KGgo', self.element(frame, PHOTO, "(el) => el.outerHTML"))


class LedgerHtmlDataUrlTests(BridgeCase):
    def test_any_long_data_attribute_is_abbreviated_even_with_spaces_and_quotes(self):
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'>"
               + "<rect x='1' y='1' width='5' height='5' fill='red'/> " * 40 + '</svg>')
        url = 'data:image/svg+xml,' + svg
        self.assertGreater(len(url), 1500)
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                reply = self.request(page, {'type': 'design:update', 'patch': {'slots': [
                    {'id': 'img-slot', 'targetId': PHOTO, 'type': 'image', 'assetDataUrl': url,
                     'imageWidth': 24, 'opacity': 1}]}})
                self.assertEqual(reply['type'], 'design:applied', reply)
                self.assertEqual(self.element(frame, PHOTO, "(el) => el.getAttribute('src')"), url)
                html = self.entry(reply['changes'], PHOTO)['html']
                self.assertIn(f'src="data:image/svg+xml,…({len(url)} bytes)"', html)
                self.assertNotIn('rect', html)


class LedgerHtmlAttributeScopeTests(BridgeCase):
    def test_only_real_data_urls_in_url_attributes_are_abbreviated(self):
        long_a = 'data:image/png;base64,' + 'A' * 400
        long_b = 'data:image/png;base64,' + 'B' * 500
        text = 'data: hello ' + 'this is just a long title ' * 20
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                frame.evaluate("""([a, b, text]) => {
                    const lead = document.querySelector('[data-design-id="landing.hero.lead"]');
                    lead.setAttribute('title', text);
                    lead.setAttribute('data-note', text);
                    lead.setAttribute('style', 'background: url(' + a + ')');
                    const img = document.createElement('img');
                    img.setAttribute('srcset', a + ' 1x, ' + b + ' 2x');
                    img.setAttribute('src', 'small.png');
                    img.setAttribute('alt', 'x');
                    lead.appendChild(img);
                    const link = document.createElement('a');
                    link.setAttribute('href', b);
                    link.textContent = 'dl';
                    lead.appendChild(link);
                }""", [long_a, long_b, text])
                reply = self.applied(page, LEAD, {'fontSize': 20})
                html = self.entry(reply['changes'], LEAD)['html']
                self.assertIn(f'title="{text}"', html)           # text attributes are left alone
                self.assertIn(f'data-note="{text}"', html)
                self.assertIn(f'srcset="data:image/png;base64,…({len(long_a)} bytes) 1x, '
                              f'data:image/png;base64,…({len(long_b)} bytes) 2x"', html)
                self.assertIn(f'href="data:image/png;base64,…({len(long_b)} bytes)"', html)
                self.assertIn('src="small.png"', html)
                self.assertNotIn('AAAA', html)
                self.assertNotIn('BBBB', html)


class AutoSelectorTests(BridgeCase):
    def test_auto_selectors_stay_unique_on_deep_repetitive_dom(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=DEEP_PAGE)
                ready = self.hello(page)
                deep = [t for t in ready['targets'] if t['tag'] == 'p']
                self.assertEqual(len(deep), 4)
                for target in deep:
                    matches = frame.evaluate(
                        """([sel, id]) => { const found = [...document.querySelectorAll(sel)];
                            return [found.length, found.length === 1 && found[0].getAttribute('data-design-id') === id]; }""",
                        [target['selector'], target['id']])
                    self.assertEqual(matches, [1, True], target['selector'])
                self.assertEqual(len({t['selector'] for t in deep}), 4)
                # The selector is also what the ledger reports, and it stays unique after DOM changes.
                reply = self.applied(page, deep[3]['id'], {'color': '#ff0000'})
                self.assertEqual(self.entry(reply['changes'], deep[3]['id'])['selector'], deep[3]['selector'])
                frame.evaluate("document.querySelector('main').prepend(document.createElement('div'))")
                page.wait_for_timeout(300)
                refreshed = self.hello(page, 's2')
                for target in refreshed['targets']:
                    found = frame.evaluate('(sel) => document.querySelectorAll(sel).length', target['selector'])
                    self.assertEqual(found, 1, target['selector'])


class LegacyLayoutStructureTests(BridgeCase):
    def test_legacy_layout_reorder_is_recorded_in_structure_and_undone_by_reset_all(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                original = frame.evaluate("document.querySelector('main').innerHTML")
                labels = frame.evaluate(CHILD_LABELS, 'main')
                self.assertEqual(labels[0], TITLE)
                reply = self.request(page, {'type': 'design:update', 'patch': {
                    'slots': [{'id': 'a', 'targetId': BADGE, 'type': 'text', 'size': 15, 'textTouched': False},
                              {'id': 'b', 'targetId': TITLE, 'type': 'text', 'size': 44, 'textTouched': False}],
                    'layout': {'order': [{'id': 'a', 'role': 'metadata', 'index': 0},
                                         {'id': 'b', 'role': 'h1', 'index': 1}]}}})
                self.assertEqual(reply['type'], 'design:applied')
                after = frame.evaluate(CHILD_LABELS, 'main')
                self.assertEqual(after[-2:], [BADGE, TITLE])
                structure = reply['changes']['structure']
                self.assertEqual(len(structure), 1)
                self.assertEqual((structure[0]['selector'], structure[0]['stable']), ('main:nth-of-type(1)', False))
                self.assertRegex(structure[0]['containerKey'], r'^container:\d+$')
                self.assertEqual(len(structure[0]['order']), len(after))
                self.assertTrue(structure[0]['html'].startswith('<main>'))
                self.assertNotIn('transition', structure[0]['html'])
                self.assertNotIn('order:', structure[0]['html'])
                self.assertNotIn('auto:', structure[0]['html'])

                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reply['changes']['structure'], [])
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), original)
                self.assertEqual(frame.evaluate(CHILD_LABELS, 'main'), labels)


class SiblingOnlyHitTestTests(BridgeCase):
    """Sibling-only registrations never win hover or click hit-testing."""

    def test_clicking_list_text_or_a_summary_does_not_select_the_wrapper(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=DEMO_PAGE)
                ready = self.hello(page)
                ul_id = frame.evaluate("document.querySelector('.plan ul').getAttribute('data-design-id')")
                summary_id = frame.evaluate("document.querySelector('details summary').getAttribute('data-design-id')")
                by_id = {t['id']: t for t in ready['targets']}
                self.assertIs(by_id[ul_id].get('arrangementOnly'), True)
                self.assertIs(by_id[summary_id].get('arrangementOnly'), True)

                start = self.mark(page)
                frame.locator('.plan ul li').first.click()
                page.mouse.move(5, 5)
                page.wait_for_timeout(300)
                self.assertEqual(self.messages(page, 'design:selected', start), [])
                self.assertEqual([m for m in self.messages(page, 'design:hover', start) if m['targetId'] == ul_id], [])

                # Select mode: the summary is not a target, so the page toggles it normally.
                frame.locator('details summary').first.click()
                page.wait_for_timeout(200)
                self.assertEqual(self.messages(page, 'design:selected', start), [])
                self.assertTrue(frame.evaluate("document.querySelector('details').open"))

                # Interact mode toggles it back.
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                page.wait_for_timeout(100)
                frame.locator('details summary').first.click()
                self.assertFalse(frame.evaluate("document.querySelector('details').open"))

                # Real targets still select, and the sibling-only ul stays addressable by id.
                self.control(page, {'type': 'design:mode', 'mode': 'select'})
                page.wait_for_timeout(100)
                start = self.mark(page)
                frame.locator('.plan h3').first.click()
                self.assertEqual(self.wait_message(page, 'design:selected', start)['target']['tag'], 'h3')
                start = self.mark(page)
                self.control(page, {'type': 'design:select', 'targetId': ul_id})
                selected = self.wait_message(page, 'design:selected', start)
                self.assertEqual(selected['targetId'], ul_id)
                self.assertIs(selected['target']['arrangementOnly'], True)

    def test_the_flag_and_the_hit_test_survive_rediscovery_moves_and_reconnects(self):
        flagged = "[...window.__fontkitBridge.targets.values()].filter((r) => r.arrangementOnly).length"
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=DEMO_PAGE)
                self.hello(page)
                count = frame.evaluate(flagged)
                self.assertGreater(count, 5)

                def check(label):
                    self.assertEqual(frame.evaluate(flagged), count, label)
                    start = self.mark(page)
                    self.control(page, {'type': 'design:mode', 'mode': 'select'})
                    frame.evaluate("document.querySelector('details').open = false")
                    frame.locator('.plan ul li').first.click()
                    frame.locator('details summary').first.click()
                    page.wait_for_timeout(150)
                    self.assertEqual(self.messages(page, 'design:selected', start), [], label)
                    self.assertTrue(frame.evaluate("document.querySelector('details').open"), label)

                check('after first hello')
                self.hello(page, 's2')
                check('after a second hello')
                frame.evaluate("document.querySelector('main').appendChild(document.createElement('div'))")
                page.wait_for_timeout(400)
                check('after a mutation')
                first = frame.evaluate("document.querySelector('.actions > *').getAttribute('data-design-id')")
                reply = self.request(page, {'type': 'design:move', 'targetId': first, 'to': {'index': 1}})
                self.assertEqual(reply['type'], 'design:applied', reply)
                page.wait_for_timeout(600)
                check('after a move')

    def test_a_semantic_element_registered_as_a_sibling_first_is_an_ordinary_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                # Added between discoveries, then looked at through a sibling's arrangement.
                frame.evaluate("""() => {
                    const late = document.createElement('h2');
                    late.textContent = 'Late semantic';
                    document.querySelector('main').appendChild(late);
                }""")
                self.control(page, {'type': 'design:select', 'targetId': TITLE})
                page.wait_for_timeout(50)
                ready = self.hello(page, 's2')
                late = next(t for t in ready['targets'] if t['text'] == 'Late semantic')
                self.assertNotIn('arrangementOnly', late)


class ContentModelGuardTests(ArrangeCase):
    def guard(self, reply):
        self.assertEqual(reply.get('type'), 'design:rejected', reply)
        self.assertEqual(reply['reason'], 'unsupported-value')
        return reply['detail']

    def test_block_elements_cannot_go_into_inline_or_phrasing_parents(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready = self.start(engine)
                snapshot = frame.evaluate("document.querySelector('main').innerHTML")
                heading = next(t['id'] for t in ready['targets'] if t['text'] == 'Card one' and t['tag'] == 'h3')
                for target_id, to in (('arr.p.1', {'container': 'arr.para'}),      # p in p
                                      ('arr.group', {'container': 'arr.link'}),    # div in a
                                      ('arr.p.2', {'container': 'arr.para.a'}),    # p in span
                                      (heading, {'container': 'arr.para'}),        # h3 in p
                                      ('arr.p.3', {'after': 'arr.para.b'}),        # p after a span: into the p
                                      ('arr.form', {'container': 'arr.btn.a'})):   # form in button
                    detail = self.guard(self.move(page, target_id, to))
                    self.assertEqual((detail['guard'], detail['overridable']), ('content-model', False), target_id)
                    self.assertEqual(detail['property'], 'move')
                    self.assertTrue(detail['message'])
                # force never overrides it, and css-order does not touch the DOM at all.
                detail = self.guard(self.move(page, 'arr.p.1', {'container': 'arr.para'}, force=True))
                self.assertEqual(detail['guard'], 'content-model')
                self.assertEqual(frame.evaluate("document.querySelector('main').innerHTML"), snapshot)
                self.assertEqual(self.request(page, {'type': 'design:update', 'targetId': 'arr.btn.a',
                                                     'patch': {'fontSize': 14}})['revision'], 1)

    def test_inline_into_inline_and_block_into_block_and_in_place_moves_are_allowed(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _ = self.start(engine)
                self.moved(page, 'arr.btn.a', {'container': 'arr.para'})       # button is not a block element
                self.moved(page, 'arr.para.b', {'container': 'arr.plain'})     # inline into a div
                self.moved(page, 'arr.p.1', {'container': 'arr.outside'})      # p into a div
                self.moved(page, 'arr.link.a', {'container': 'arr.para'})      # span into p
                self.moved(page, 'arr.para.a', {'index': 1})                   # reorder inside the p
                self.assertEqual(self.errors(frame), [])


class AttributeWriteTests(BridgeCase):
    def test_an_unchanged_style_or_attribute_value_is_never_rewritten(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                self.applied(page, 'spa.title', {'fontSize': 50})
                frame.evaluate("""() => {
                    window.__attrWrites = [];
                    new MutationObserver((records) => records.forEach((r) => window.__attrWrites.push(r.attributeName)))
                        .observe(document.getElementById('app'), { attributes: true, subtree: true });
                }""")
                self.applied(page, 'spa.title', {'fontSize': 50})
                frame.evaluate('window.__fontkitBridge.discoverTargets()')
                frame.evaluate('window.__fontkitBridge.discoverTargets()')
                page.wait_for_timeout(150)
                self.assertEqual(frame.evaluate('window.__attrWrites'), [])

    def test_an_app_that_rerenders_on_any_attribute_change_cannot_trap_the_bridge(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA_PAGE)
                self.hello(page)
                frame.evaluate('window.anyAttr = true; window.renders = 0; render();')
                page.wait_for_timeout(5500)
                before = frame.evaluate('window.renders')
                self.assertLess(before, 60)
                page.wait_for_timeout(3000)
                after = frame.evaluate('window.renders')
                self.assertLessEqual(after - before, 2, (before, after))
                # The bridge recovers once the app calms down.
                frame.evaluate('window.anyAttr = false')
                frame.evaluate('render()')
                page.wait_for_timeout(300)
                self.assertEqual(self.applied(page, 'spa.body', {'fontSize': 30})['type'], 'design:applied')


if __name__ == '__main__':
    unittest.main()
