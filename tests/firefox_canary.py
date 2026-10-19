"""Firefox canary: the few browser tests CI runs on Gecko (D037).

The full suite runs on Chromium only. Gecko gets a short canary of the
places an engine difference would hurt most: the bridge's trust boundary
(hostile frames, forged sessions and versions, handshake, origin list,
session lifecycle, targeted updates), real Studio
against the real bridge in a cross-origin frame (edit, code panel, sync,
reload), and Studio's own rendering. Three role smoke tests cover selector
hostility, a real Studio apply and clear, and route announcements. The
frontend gate covers layout,
contrast, privacy and the live edit flow on Firefox separately.

The file name does not match `test*.py`, so `discover` never collects it.
Run it with:

    PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v

`test_support.CanaryListTest` fails the Chromium suite when a name here no
longer loads, so a renamed class cannot quietly empty the canary.
"""
import json

from support import ENGINES
from test_role_route_bridge import KEYS, SPA, RoleRouteCase
from test_role_stylesheet import PLAIN_24, role
from test_studio_roles import APPLY, CLEAR, ROLE_PAGE, StudioLegacyCase

# Studio records the bridge messages it receives, so a test can read them.
CAPTURE = """window.__s2b = { session: null, inbound: [] };
addEventListener('message', e => { const d = e.data; if (d && d.protocolVersion === 1 && e.origin === 'http://target.test') {
  if (d.sessionId) __s2b.session = d.sessionId; __s2b.inbound.push(JSON.parse(JSON.stringify(d))); } });"""
HOSTILE_SELECTORS = ('.a, .b', ':root', 'body', '.on-body', 'p[title="x"]', 'p:hover', '.a{', '.a;', '.a}', '.a\n.b')
SIZE = 'el => getComputedStyle(el).fontSize'
BODY_ROLE, ORDINARY = '[data-design-role="Body"]', '[data-design-id="ordinary.body"]'


class BridgeRoleSmokeTests(RoleRouteCase):
    def test_role_selector_hostility_is_rejected_whole_and_keeps_the_preview(self):
        """Given an accepted 24px preview, when each hostile selector, and a role with an own __proto__ key, is sent
        as a one-role apply, then each reply is design:rejected (unsupported-value for selectors, invalid-message for
        the key) at revision 1, the owned CSS stays the 24px rule, the body copy renders 24px, main is unchanged and
        the page has no errors."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("document.body.classList.add('on-body')")
                self.hello(page)
                self.assertEqual(self.apply(page, [role(fontSize=24)])['revision'], 1)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                state = page.evaluate('roleState')
                proto = json.dumps({'type': 'design:roles-apply', 'documentId': state['documentId'],
                                    'pageVersion': state['pageVersion'], 'roles': [{**role(fontSize=30), '__proto__': {}}]})
                cases = [(s, 'unsupported-value', lambda s=s: self.apply(page, [role(selectors=[s], fontSize=30)]))
                         for s in HOSTILE_SELECTORS]
                cases.append(('__proto__', 'invalid-message', lambda: page.evaluate('raw => request(JSON.parse(raw), 3000)', proto)))
                for label, reason, send in cases:
                    with self.subTest(case=label):
                        reply = send()
                        self.assertEqual((reply['type'], reply.get('reason'), reply['revision']), ('design:rejected', reason, 1), reply)
                        self.assertEqual(self.owned(frame), [PLAIN_24])
                        self.assertEqual(self.size(frame), '24px')
                        self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(self.errors(frame), [])

    def test_a_same_document_route_change_is_announced_with_a_fresh_page_version(self):
        """Given the role page after hello, when pushState changes the query, then exactly one roles-page carries the
        new URL, a greater version, the six literal keys and the ready's document, the body text stays and detect
        reports that version; and when the SPA renders 'same', one roles-page keeps the URL with a greater version."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("history.pushState({a: 1}, '', '?route=x')")
                got = self.notices(page, start)
                self.assertEqual(self.urls(got), [ROLE_PAGE + '?route=x'])
                self.assertGreater(got[0]['pageVersion'], ready['roleState']['pageVersion'])
                self.assertEqual(set(got[0]), KEYS)
                self.assertEqual(got[0]['documentId'], ready['roleState']['documentId'])
                self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')
                self.assertEqual(self.detect(page)['pageVersion'], got[0]['pageVersion'])
                page, frame, ready, start = self.start(engine, SPA)
                frame.evaluate("render('same')")
                got = self.notices(page, start)
                self.assertEqual(self.urls(got), [SPA])
                self.assertGreater(got[0]['pageVersion'], ready['roleState']['pageVersion'])


class StudioRoleSmokeTests(StudioLegacyCase):
    def test_real_studio_apply_and_clear_round_trip(self):
        """Given the real Studio detecting the role page, when Body is checked, given 24 by keystrokes and applied,
        then the Body paragraph renders 24px, the ordinary one 16px, main is byte-equal and the preview CSS has
        font-size: 24px; and after Clear the status reads Preview cleared., the CSS is empty, both sizes and main equal
        their earlier values and the page has no errors."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, init=CAPTURE)
                self.assertIn('Detected', self.detect(page))

                def look():
                    return (frame.locator('main').evaluate('el => el.outerHTML'),
                            frame.locator(BODY_ROLE).evaluate(SIZE), frame.locator(ORDINARY).evaluate(SIZE))

                before = look()
                self.control(page, 'Preview this role').check()
                self.type_value(self.control(page, 'Size (px)'), '24')
                self.button(page, APPLY).click()
                page.wait_for_function('__s2b.inbound.some(m => m.type === "design:roles-applied")')
                self.assertEqual(look()[1:], ('24px', '16px'))
                self.assertEqual(look()[0], before[0])
                self.assertIn('font-size: 24px', self.preview(page)['css'])
                self.button(page, CLEAR).click()
                self.wait_status(page, 'Preview cleared.')
                self.assertEqual(self.preview(page)['css'], '')
                self.assertEqual(look(), before)
                self.assertEqual(errors, [])


CANARY = (
    'test_bridge_runtime.ConfirmedDefectTests',
    'test_bridge_runtime.HandshakeTests',
    'test_bridge_runtime.OriginListTests',
    'test_bridge_runtime.SessionLifecycleTests',
    'test_bridge_runtime.TargetedUpdateTests',
    'test_live_integration.EditAndCodePanelTests',
    'test_live_integration.SyncAndReloadTests',
    'test_font_kit_studio_v011.BrowserCase',
    'test_localhost_cookies.LocalhostCookiesTest',
    'firefox_canary.BridgeRoleSmokeTests',
    'firefox_canary.StudioRoleSmokeTests',
)


def load_tests(loader, standard_tests, pattern):
    return loader.loadTestsFromNames(CANARY)
