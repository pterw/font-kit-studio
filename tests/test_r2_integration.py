"""The actual Studio and bridge render literal baseline role observations."""
import json
import re

import role_contract as table
from support import ENGINES, REPO
from test_studio_roles import (APPLY, CLEAR, RESET_ALL, ROLE_PAGE, STALE, TARGET, UNAVAILABLE, StudioLegacyCase,
                               StudioRoleCase, per_engine)


class StudioRoleIntegrationTests(StudioRoleCase):
    def test_fullscreen_preserves_roles_and_preview_height_through_escape(self):
        """Given detected roles, when the preview goes fullscreen in fluid and fixed widths and back with Escape, then
        the preview stays above 500 px, the panel is inert while fullscreen, its rows are unchanged and its status reads
        the page-changed sentence once the resize reaches Studio as a roles-page (a viewport change moves the page version)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine, viewport={'width': 1280, 'height': 800})
                self.assertIn('Detected 2 roles', self.detect(page))
                def observations():
                    return (page.locator('#roleStatus').inner_text(),
                            page.locator('#roleRows > li').evaluate_all('rows=>rows.map(row=>[row.dataset.roleId,row.textContent])'))
                observed = observations()
                self.assertEqual([row[0] for row in observed[1]], ['role-1', 'role-2'])
                author = frame.locator('main').evaluate('el=>el.outerHTML')
                changed = (PAGE_CHANGED, observed[1])
                for width in ('#btnDeviceFluid', '#btnDeviceDesktop'):
                    page.locator(width).click()
                    page.locator('#btnToggleFullscreen').click()
                    page.wait_for_function('document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                    page.wait_for_function('(text) => document.querySelector("#roleStatus").textContent === text', arg=PAGE_CHANGED)
                    info = page.evaluate('''() => {
                        const s=document.querySelector('#previewScroller'), f=document.querySelector('#targetAppFrame');
                        s.scrollLeft=s.scrollWidth;
                        return {height:document.querySelector('#targetAppContainer').getBoundingClientRect().height,
                            right:f.getBoundingClientRect().right, edge:s.getBoundingClientRect().right,
                            bottom:s.getBoundingClientRect().bottom, width:s.scrollWidth, client:s.clientWidth};
                    }''')
                    self.assertGreater(info['height'], 500)
                    self.assertLessEqual(info['bottom'], 800)
                    self.assertLessEqual(info['right'], info['edge'] + .5)
                    if width == '#btnDeviceFluid':
                        self.assertEqual(info['width'], info['client'])
                    else:
                        self.assertEqual(info['width'], 1440)
                        self.assertGreater(info['width'], info['client'])
                    self.assertTrue(page.locator('#detectedRoles').evaluate('el=>!!el.closest("[inert]")'))
                    self.assertEqual(observations(), changed)
                    page.keyboard.press('Escape')
                    page.wait_for_function('!document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                    self.assertEqual(observations(), changed)
                    button = page.get_by_role('button', name='Detect text styles', exact=True)
                    self.assertTrue(button.is_visible())
                    button.focus()
                    self.assertTrue(button.evaluate('el=>el===document.activeElement'))
                button.press('Enter')
                page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected 2 roles")')
                self.assertEqual(observations(), observed)
                self.assertEqual(frame.locator('main').evaluate('el=>el.outerHTML'), author)
                self.assertEqual(errors, [])

    def test_observed_long_family_is_not_limited_like_an_apply_property(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine)
                family = 'LocalFace' + 'a' * 320 + ', sans-serif'
                frame.locator('.body-copy').evaluate_all('(els,family)=>els.forEach(el=>el.style.fontFamily=family)', family)
                frame.locator('.body-copy').evaluate_all('els=>els.forEach(el=>el.style.fontWeight="450.5")')
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el=>getComputedStyle(el).fontFamily'), family)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el=>getComputedStyle(el).fontWeight'), '450.5')
                before = frame.locator('main').evaluate('el=>el.outerHTML')
                page.get_by_role('button', name='Detect text styles').click()
                page.wait_for_function('document.querySelector("#roleRows").children.length===2', timeout=3000)
                self.assertIn(family, page.locator('#roleRows').inner_text())
                self.assertIn('16px / 451 / none / 0em', page.locator('#roleRows').inner_text())
                self.assertEqual(frame.locator('main').evaluate('el=>el.outerHTML'), before)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_unavailable_actual_url_preserves_inspector_reset_and_supported_reconnect(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                path = '/tests/fixtures/bridge/target-role-protocol.html'
                target = ROLE_PAGE + '?' + 'x' * (2000 - len(path))
                page, frame, errors = self.open(engine, target)
                self.assertEqual(frame.evaluate('location.pathname.length+location.search.length'), 2001)
                page.wait_for_function('document.querySelector("#roleStatus").textContent.includes("unsupported page URL")')
                self.assertEqual(page.get_by_role('status', name='Role detection status').inner_text(), UNAVAILABLE)
                self.assertTrue(page.get_by_role('button', name='Detect text styles').is_disabled())
                frame.locator('[data-design-id="ordinary.body"]').click()
                size = page.locator('#liveFontSize')
                size.focus()
                size.press('ControlOrMeta+A')
                size.press_sequentially('27')
                frame.wait_for_function('getComputedStyle(document.querySelector("[data-design-id=\\"ordinary.body\\"]")).fontSize==="27px"')
                page.get_by_role('button', name='Reset this element', exact=True).click()
                frame.wait_for_function('getComputedStyle(document.querySelector("[data-design-id=\\"ordinary.body\\"]")).fontSize==="16px"')
                self.assertEqual(frame.locator('.body-copy').nth(1).inner_text(), 'Ordinary body')
                self.assertEqual(page.locator('#roleStatus').inner_text(), UNAVAILABLE)
                # Reconnect explicitly to the exact accepted route boundary; no replay.
                accepted = ROLE_PAGE + '?' + 'x' * (1999 - len(path))
                field = page.get_by_role('textbox', name='Live App URL', exact=True)
                field.focus()
                field.press('ControlOrMeta+A')
                field.press_sequentially(accepted)
                page.get_by_role('button', name='Connect Live App', exact=True).click()
                page.wait_for_function('!document.querySelector("#detectTextStyles").disabled')
                frame = next(f for f in page.frames if f.url.startswith('http://target.test'))
                self.assertEqual(frame.evaluate('location.pathname.length+location.search.length'), 2000)
                self.assertIn('Detected 2 roles', self.detect(page))
                self.assertEqual(frame.locator('.body-copy').nth(1).evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_real_scan_invalidated_into_unsupported_url_never_reports_checked(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine)
                self.assertIn('Detected 2 roles', self.detect(page))
                before = frame.locator('main').evaluate('el=>el.outerHTML')
                frame.evaluate('''() => addEventListener('message', function change(e) {
                    if(e.data.type!=='design:detect')return;
                    removeEventListener('message',change);
                    history.pushState(null,'','/?'+ 'x'.repeat(1999));
                })''')
                self.assertEqual(self.detect(page), UNAVAILABLE)
                self.assertEqual(frame.evaluate('location.pathname.length+location.search.length'), 2001)
                self.assertEqual(page.locator('#roleRows > li').count(), 0)
                self.assertTrue(page.get_by_role('button', name='Detect text styles').is_disabled())
                self.assertEqual(frame.locator('main').evaluate('el=>el.outerHTML'), before)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(errors, [])

    def test_desktop_and_narrow_roles_have_keyboard_focus_readable_text_and_no_panel_overflow(self):
        for engine in ENGINES:
            for width in (1440, 390):
                with self.subTest(engine=engine, width=width):
                    page, frame, errors = self.open(engine, viewport={'width': width, 'height': 1000})
                    button = page.get_by_role('button', name='Detect text styles', exact=True)
                    button.focus()
                    button.press('Space')
                    page.wait_for_function('document.querySelector("#roleRows").children.length===2')
                    self.assertTrue(button.evaluate('el=>el===document.activeElement'))
                    self.assertGreater(float(button.evaluate('el=>parseFloat(getComputedStyle(el).outlineWidth)')), 0)
                    self.assertEqual(page.get_by_role('list', name='Detected text roles').get_by_role('listitem').count(), 2)
                    self.assertIn('Other pages have not been checked.', page.get_by_role('status', name='Role detection status').inner_text())
                    self.assertTrue(page.locator('#detectedRoles').evaluate('el=>el.scrollWidth<=el.clientWidth'))
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                    colors = page.locator('#roleStatus').evaluate('el=>{let c=getComputedStyle(el),p=el;while(p&&getComputedStyle(p).backgroundColor==="rgba(0, 0, 0, 0)")p=p.parentElement;return [c.color,getComputedStyle(p).backgroundColor]}')
                    def luminance(color):
                        parts = [float(x) / 255 for x in color[color.index('(')+1:color.index(')')].split(',')[:3]]
                        values = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in parts]
                        return sum(c * w for c, w in zip(values, (.2126, .7152, .0722)))
                    light, dark = sorted(map(luminance, colors), reverse=True)
                    self.assertGreaterEqual((light + .05) / (dark + .05), 4.5, colors)
                    self.assertEqual(frame.locator('.body-copy').first.evaluate('el=>getComputedStyle(el).fontSize'), '16px')
                    self.assertEqual(errors, [])

    def test_real_connected_detect_renders_author_and_style_roles_without_edits(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open(engine)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                button = page.get_by_role('button', name='Detect text styles', exact=True)
                self.assertTrue(button.is_visible(), 'Connected Studio has no accessible Detect control')
                button.focus()
                button.press('Enter')
                page.wait_for_function('document.querySelector("#roleRows").children.length === 2')
                rows = page.locator('#roleRows > li')
                self.assertEqual(rows.count(), 2)
                self.assertIn('Body', rows.nth(0).inner_text())
                self.assertIn('Author body', rows.nth(0).inner_text())
                self.assertIn('[data-design-role="Body"]', rows.nth(0).inner_text())
                self.assertIn('1 eligible text parent', rows.nth(0).inner_text())
                self.assertIn('Ordinary body', rows.nth(1).inner_text())
                self.assertIn('[data-design-id="ordinary.body"]', rows.nth(1).inner_text())
                self.assertIn('16px / 400 / none / 0em', rows.nth(1).inner_text())
                self.assertIn('Light-DOM text only', page.locator('#detectedRoles').inner_text())
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertEqual(errors, [])


# The Studio page records every bridge message it receives, so a test can read the receipts and the session.
CAPTURE = """window.__s2b = { session: null, inbound: [] };
addEventListener('message', e => { const d = e.data; if (d && d.protocolVersion === 1 && e.origin === 'http://target.test') {
  if (d.sessionId) __s2b.session = d.sessionId; __s2b.inbound.push(JSON.parse(JSON.stringify(d))); } });"""
PAGE_CHANGED = 'The page changed since the last Detect; press Detect text styles. This page has not been checked.'
# What each RoleOutcome reason reads as, per the R2.5 handoff.
REASON_TEXT = {'author-rule': 'overridden by', 'inline': 'overridden by inline style', 'inherited': 'inherits from',
               'unreadable-sheet': 'a stylesheet could not be read', 'complex-cascade': 'overridden; source not provable',
               'stylesheet-blocked': 'the page disabled the preview sheet', 'budget-exceeded': 'not attributed in time'}
CARD_PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><title>Card</title>
<style>.card p { font-size: 20px; font-family: serif; } .role { font-size: 16px; }</style>
<main><div class="card"><p class="role" data-design-role="Body">Card text</p></div></main>
<script src="/fontkit-bridge.js"></script></html>"""
ESCAPED_PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><title>Escaped</title>
<style>.sm\\:big { font-size: 20px; }</style>
<main><p class="sm:big">Escaped text</p></main>
<script src="/fontkit-bridge.js"></script></html>"""
TWO_SELECTOR_PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><title>Two</title>
<main><p class="alpha">One</p><p class="beta">Two</p></main>
<script src="/fontkit-bridge.js"></script></html>"""
LONG_URL = '/?' + 'x' * 1999
# The real bridge binds a role only to what it measured, so no Detect it makes can reach more than 10,000 elements. This
# page answers the first Detect itself (the real bridge's own reply then arrives for a request already settled) with a
# class binding that 10,001 elements carry, and leaves Apply and its receipt to the real bridge.
MANY_MATCHES = ("""<!doctype html><html lang="en"><meta charset="utf-8"><title>Many</title><main id="m"><p class="b">x</p></main>
<script>for (let i = 0; i < 10000; i++) { const d = document.createElement('div'); d.className = 'b'; d.hidden = true; d.textContent = 'h'; m.append(d); }
let session = null;
addEventListener('message', e => {
  if (e.source !== parent || !e.data) return;
  if (e.data.type === 'design:hello') session = e.data.sessionId;
  if (e.data.type !== 'design:detect') return;
  const b = window.__fontkitBridge, url = location.href;
  parent.postMessage({ type: 'design:detected', protocolVersion: 1, sessionId: session, requestId: e.data.requestId, revision: b.revision,
    documentId: b.documentId, pageVersion: b.pageVersion, pageURL: url, currentPageVersion: b.pageVersion, currentPageURL: url,
    complete: true, reason: null, elapsedMs: 1, scannedElements: 1, selectorChecks: [], groups: [{ id: 'g1',
      identity: { kind: 'author-role', name: 'Body' }, suggestedName: 'Body', authorRole: 'Body', elementCount: 1, sampleText: 'x',
      signatures: [{ style: { fontFamily: 'serif', fontSize: 16, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }, count: 1 }],
      sharedClasses: ['b'], selectors: [{ value: '.b', stable: true, reason: 'class' }], bindingComplete: true, nearDuplicateIds: [], adapter: 'plain' }] },
    'http://studio.test');
}, true);</script>
<script src="/fontkit-bridge.js"></script></html>""")
MANY_LOSSES = ("""<!doctype html><html lang="en"><meta charset="utf-8"><title>Losses</title><main id="m"></main>
<script>
const rules = [];
for (let i = 0; i < 30; i++) {
  const k = i % 4;
  rules.push(`main p.c${i} { font-size: ${10 + k}px; font-weight: ${100 * (k + 1)}; line-height: ${1 + k / 10};`
    + ` letter-spacing: ${k}px; text-transform: ${['lowercase', 'uppercase', 'capitalize', 'none'][k]};`
    + ` font-family: ${['Arial', 'Georgia', 'Courier', 'Verdana'][k]}; }`);
  const p = document.createElement('p'); p.className = 'c' + i; p.dataset.designRole = 'Body'; p.textContent = 'Paragraph ' + i; m.append(p);
}
const style = document.createElement('style'); style.textContent = rules.join(' '); document.head.append(style);
</script><script src="/fontkit-bridge.js"></script></html>""")
FAMILIES = [('Georgia, serif', True), ('"Times New Roman", serif', True), ('Source Serif 4', False), ('variable-font', True),
            ('var(--f)', False), ('var (--f)', False), ('env(x)', False), ('attr(x)', False), ('url(x)', False), ('url (x)', False),
            ('expression(1)', False), ('expression (1)', False), ('Georgia !important', False), ('Georgia ! important', False),
            ('a;b', False), ('a{b', False), ('a<b', False), ('a' + chr(92) + 'b', False), ('a/* c */b', False), ("'Unbalanced", False),
            ('A' * 301, False), ('Georgia' + chr(9) + 'serif', False), ('Georgia' + chr(127), False), ('Georgia' + chr(1), False),
            ('"quoted' + chr(9) + 'name"', False)] + [(v, False) for v in table.FAMILIES_REFUSED] + [(v, True) for v in table.FAMILIES_ACCEPTED]


class StudioRoleBridgeTests(StudioLegacyCase):
    """The real Studio against the real bridge: what the target renders, and what Studio shows of the receipt."""

    def start(self, engine, **options):
        page, frame, errors = self.open(engine, init=CAPTURE, **options)
        self.assertIn('Detected', self.detect(page))
        self.record(frame)
        return page, frame, errors

    def look(self, frame):
        """Author markup and every paragraph's computed text style."""
        return (frame.locator('main').evaluate('el => el.outerHTML'),
                frame.locator('main p').evaluate_all('els => els.map(el => { const c = getComputedStyle(el); return '
                    '[c.fontFamily, c.fontSize, c.fontWeight, c.lineHeight, c.letterSpacing, c.textTransform]; })'))

    def size(self, frame, selector):
        return frame.locator(selector).evaluate('el => getComputedStyle(el).fontSize')

    def receipts(self, page):
        return page.evaluate("__s2b.inbound.filter(m => m.type === 'design:roles-applied')")

    def names(self, page):
        return page.locator('#roleRows > li strong').evaluate_all('els => els.map(el => el.textContent)')

    def edit_inspector(self, page, frame, target, value):
        frame.locator(f'[data-design-id="{target}"]').click()
        field = page.locator('#liveFontSize')
        self.type_value(field, value)
        frame.wait_for_function('([id, px]) => getComputedStyle(document.querySelector(`[data-design-id="${id}"]`)).fontSize === px',
                                arg=[target, f'{value}px'], polling=50)

    def apply_body(self, page, frame, size='24'):
        request = self.apply_role(page, frame, size)
        self.wait_for_receipt(page, request)
        return request

    def wait_for_receipt(self, page, request):
        page.wait_for_function('(id) => __s2b.inbound.some(m => m.type === "design:roles-applied" && m.requestId === id)', arg=request['requestId'])

    def ops(self, frame, kind):
        return [m for m in frame.evaluate('window.__got || []') if m['type'] == kind]

    def untargeted_resets(self, frame):
        return [m for m in self.ops(frame, 'design:reset') if 'targetId' not in m]

    def record(self, frame):
        frame.evaluate("if (!window.__got) { window.__got = []; addEventListener('message', e => { if (e.data && e.data.type) __got.push(e.data); }); }")

    def wait_for_ops(self, frame, kind, count):
        frame.wait_for_function('([kind, count]) => (window.__got || []).filter(m => m.type === kind).length >= count', arg=[kind, count], polling=50)

    def apply_role(self, page, frame, size='24', role='role-1', name=None):
        name = name or self.names(page)[int(role.split('-')[1]) - 1].rsplit(' (', 1)[0]
        self.control(page, 'Preview this role', role, name).check()
        self.type_value(self.control(page, 'Size (px)', role, name), size)
        count = len(self.ops(frame, 'design:roles-apply'))
        self.button(page, APPLY).click()
        self.wait_for_ops(frame, 'design:roles-apply', count + 1)
        return self.ops(frame, 'design:roles-apply')[-1]

    def clear_preview(self, page, frame):
        count = len(self.ops(frame, 'design:roles-clear'))
        self.button(page, CLEAR).click()
        self.wait_for_ops(frame, 'design:roles-clear', count + 1)
        return self.ops(frame, 'design:roles-clear')[-1]

    def raw(self, page, message):
        """A request posted as Studio's window would, with its session; returns the bridge's reply."""
        request_id = message['requestId']
        page.evaluate('([m]) => document.querySelector("#targetAppFrame").contentWindow.postMessage({...m, protocolVersion: 1, sessionId: __s2b.session}, "http://target.test")', [message])
        page.wait_for_function('(id) => __s2b.inbound.some(m => m.requestId === id)', arg=request_id)
        return page.evaluate('(id) => __s2b.inbound.find(m => m.requestId === id)', request_id)

    @per_engine
    def test_apply_by_keystrokes_renders_on_the_role_and_clear_restores_the_author_page(self, engine):
        """Given the real bridge, when Body is given 24px by keystrokes and applied, then that paragraph renders 24px
        while the ordinary one stays 16px and the markup is untouched, the receipt's CSS and counts show, and Clear
        returns every computed style and the markup to what they were."""
        page, frame, errors = self.start(engine)
        before = self.look(frame)
        badge = page.locator('#bridgeStatusBadge').inner_text()
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        self.assertEqual((self.size(frame, '[data-design-role="Body"]'), self.size(frame, '[data-design-id="ordinary.body"]')), ('24px', '16px'))
        self.assertEqual(self.look(frame)[0], before[0])
        shown = self.preview(page)
        self.assertIn('font-size: 24px', shown['css'])
        self.assertIn('Body (role-1): matched 1, checked 1 eligible text elements, mismatched 0', shown['outcomes'])
        self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), badge)
        self.clear_preview(page, frame)
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(self.look(frame), before)
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(errors, [])

    @per_engine
    def test_studio_shows_the_real_receipt_so_its_serialization_equals_the_bridges(self, engine):
        """Given the real bridge and a role given every property by keystrokes (a quoted non-ASCII family, fractional
        size and tracking), when it is applied, then the preview shows the bridge's canonical CSS byte for byte: Studio
        accepts a receipt only when its own serialization of the roles equals those bytes."""
        page, frame, errors = self.start(engine)
        self.control(page, 'Preview this role', 'role-1', 'Body').check()
        for label, value in (('Font family', '"界 Sans", Georgia, serif'), ('Size (px)', '24.5'), ('Weight', '700'),
                             ('Line height', '1.25'), ('Tracking (em)', '0.05')):
            self.type_value(self.control(page, label, 'role-1', 'Body'), value)
        self.control(page, 'Case', 'role-1', 'Body').select_option('uppercase')
        request = self.press_apply(page, frame)
        self.wait_for_receipt(page, request)
        css = self.receipts(page)[-1]['canonicalCss']
        self.assertIn('  font-family: "\u754c Sans", Georgia, serif;\n  font-size: 24.5px;\n  font-weight: 700;\n'
                      '  line-height: 1.25;\n  letter-spacing: 0.05em;\n  text-transform: uppercase;\n}\n', css)
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(self.preview(page)['css'], css)
        self.assertEqual(frame.locator('[data-design-role="Body"]').evaluate('el => getComputedStyle(el).fontSize'), '24.5px')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_receipt_for_an_escaped_class_selector_equals_studios_serialization(self, engine):
        """Given a page whose only text has the class sm:big, when the role the real bridge detects for it (selector
        .sm\\:big) is applied, then the preview shows the bridge's canonical CSS with the escaped selector byte for byte."""
        page, frame, errors = self.open(engine, TARGET + '/escaped', ESCAPED_PAGE, init=CAPTURE)
        self.assertIn('Detected', self.detect(page))
        self.record(frame)
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        css = self.receipts(page)[-1]['canonicalCss']
        self.assertEqual(css, '.sm\\:big {\n  font-size: 24px;\n}\n')
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(self.preview(page)['css'], css)
        self.assertEqual(frame.locator('p').evaluate('el => getComputedStyle(el).fontSize'), '24px')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_receipt_for_a_role_with_two_selectors_equals_studios_serialization(self, engine):
        """Given a page whose two same-styled paragraphs the real bridge groups under two selectors, when that role is
        applied, then the preview shows the bridge's canonical CSS, whose rule joins both selectors with a comma and a
        space, byte for byte."""
        page, frame, errors = self.open(engine, TARGET + '/two', TWO_SELECTOR_PAGE, init=CAPTURE)
        self.assertIn('Detected', self.detect(page))
        self.record(frame)
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        self.assertEqual(len(request['roles'][0]['selectors']), 2)
        css = self.receipts(page)[-1]['canonicalCss']
        self.assertIn(', ', css.split(' {')[0])
        self.wait_status(page, 'Preview applied to 1 role')
        self.assertEqual(self.preview(page)['css'], css)
        self.assertEqual(frame.locator('p').evaluate_all('els => els.map(el => getComputedStyle(el).fontSize)'), ['24px', '24px'])
        self.assertEqual(errors, [])

    @per_engine
    def test_replace_repeat_and_clear_each_raise_the_revision_by_one_and_empty_roles_does_too(self, engine):
        """Given the real bridge, when Studio applies, replaces, repeats, clears and clears again, and a raw empty
        roles-apply follows, then every receipt carries the previous revision plus one and the empty ones carry no
        roles, CSS or outcomes; the target renders each step's size and, after Clear, the author's."""
        page, frame, errors = self.start(engine)
        for size in ('24', '25', '25'):
            self.wait_for_receipt(page, self.apply_role(page, frame, size))
            self.assertEqual(self.size(frame, '[data-design-role="Body"]'), f'{size}px')
            self.assertEqual(self.size(frame, '[data-design-id="ordinary.body"]'), '16px')
        for _ in range(2):
            self.wait_for_receipt(page, self.clear_preview(page, frame))
            self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '16px')
        found = self.receipts(page)
        self.assertEqual([m['revision'] for m in found], [1, 2, 3, 4, 5])
        self.assertEqual([m['operation'] for m in found], ['apply'] * 3 + ['clear'] * 2)
        last = found[-1]
        self.assertEqual((last['roles'], last['canonicalCss'], last['outcomes'], last['outcomesComplete']), ([], '', [], True))
        state = page.evaluate('__s2b.inbound.find(m => m.type === "design:ready").roleState')
        empty = self.raw(page, {'type': 'design:roles-apply', 'requestId': 'raw-empty', 'baseRevision': 5,
                                'documentId': state['documentId'], 'pageVersion': last['currentPageVersion'], 'roles': []})
        self.assertEqual((empty['type'], empty['revision'], empty['roles'], empty['canonicalCss'], empty['outcomes']),
                         ('design:roles-applied', 6, [], '', []))
        self.assertEqual(errors, [])

    @per_engine
    def test_role_css_never_reaches_the_code_tabs_downloads_exports_or_the_synced_file(self, engine):
        """Given a saved inspector edit and a real Apply, when the code tabs, their downloads, the JSON export and the
        body Sync to file writes are compared with their state before the Apply, then they are byte-identical apart
        from the Json tab's acknowledged revision (one higher), and none contains the role's CSS."""
        page, frame, errors = self.start(engine, sync=True)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        self.edit_inspector(page, frame, 'ordinary.body', '27')
        page.wait_for_function('document.querySelector("#liveChangeCount").textContent === "1"')
        before, before_sync = self.exports(page), self.sync_body(page)
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        receipt = self.receipts(page)[-1]
        self.assertIn('font-size: 24px', receipt['canonicalCss'])
        after, after_sync = self.exports(page), self.sync_body(page)
        revision = lambda text: re.sub(r'"revision": \d+', '"revision": N', text)
        self.assertEqual(json.loads(after['Json'])['revision'], json.loads(before['Json'])['revision'] + 1)
        aligned = lambda found: {**found, 'Json': revision(found['Json']), 'downloadJson': revision(found['downloadJson'])}
        self.assertEqual(aligned(after), aligned(before))
        self.assertEqual(after_sync, before_sync)
        self.assertIn('font-size: 27px', before_sync)
        for text in (*after.values(), after_sync):
            self.assertNotIn('font-size: 24px', text)
            self.assertNotIn(receipt['cssHash'], text)
            self.assertNotIn('data-design-role', text)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_revision_conflict_from_the_real_bridge_settles_at_once_and_the_next_apply_succeeds(self, engine):
        """Given another client that moved the bridge's revision, when Studio applies on its stale revision, then the
        real bridge's revision-conflict (with its object detail) settles the op without waiting for a timeout, the status
        names both revisions and the next step, and pressing Apply again renders the preview."""
        page, frame, errors = self.start(engine)
        state = page.evaluate('__s2b.inbound.find(m => m.type === "design:ready").roleState')
        moved = self.raw(page, {'type': 'design:roles-clear', 'requestId': 'raw-move', 'baseRevision': 0,
                                'documentId': state['documentId'], 'pageVersion': state['pageVersion']})
        self.assertEqual(moved['revision'], 1)
        self.apply_role(page, frame, '24')
        self.wait_status(page, 'rejected (revision-conflict)')
        status = self.preview(page)['status']
        self.assertIn('Detail: base revision 0, bridge revision 1', status)
        self.assertIn('press the button again', status)
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '16px')
        request = self.press_apply(page, frame)
        self.assertEqual(request['baseRevision'], 1)
        self.wait_for_receipt(page, request)
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '24px')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_role_matching_more_than_ten_thousand_elements_is_shown_with_its_full_matched_count(self, engine):
        """Given a class binding that 10,001 elements carry, one of them rendering text, when the role is applied to the
        real bridge, then its receipt (matched 10,001, checked 1) is accepted and Studio shows both counts."""
        page, frame, errors = self.open(engine, TARGET + '/many', MANY_MATCHES, init=CAPTURE)
        self.record(frame)
        self.assertIn('Detected', self.detect(page))
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        outcome = self.receipts(page)[-1]['outcomes'][0]
        self.assertEqual((outcome['matched'], outcome['checked']), (10001, 1))
        self.assertIn('matched 10001, checked 1 eligible text elements', self.preview(page)['outcomes'])
        self.assertEqual(errors, [])

    @per_engine
    def test_an_outcome_with_more_than_sixty_four_loss_groups_is_accepted(self, engine):
        """Given thirty paragraphs that each override all six properties through their own rule, when the role is
        applied, then the bridge reports more than 64 loss entries for the one role and Studio accepts the receipt and
        lists every entry."""
        page, frame, errors = self.open(engine, TARGET + '/losses', MANY_LOSSES, init=CAPTURE)
        self.record(frame)
        self.assertIn('Detected', self.detect(page))
        self.control(page, 'Preview this role', 'role-1', 'Body').check()
        for label, value in (('Font family', 'Palatino'), ('Size (px)', '40'), ('Weight', '900'), ('Line height', '3'), ('Tracking (em)', '0.5')):
            self.type_value(self.control(page, label, 'role-1', 'Body'), value)
        self.control(page, 'Case', 'role-1', 'Body').select_option('none')
        request = self.press_apply(page, frame)
        self.wait_for_receipt(page, request)
        count = len(self.receipts(page)[-1]['outcomes'][0]['losses'])
        self.assertGreater(count, 64)
        self.assertEqual(self.preview(page)['outcomes'].count(' × '), count)
        self.assertEqual(errors, [])

    @per_engine
    def test_studios_family_field_agrees_with_the_bridge_on_every_row(self, engine):
        """Given a table of family values, when each is entered in Studio and sent raw to the real bridge, then Apply
        is enabled exactly when the bridge accepts the value, so no value is offered that the bridge rejects."""
        page, frame, errors = self.start(engine)
        state = page.evaluate('__s2b.inbound.find(m => m.type === "design:ready").roleState')
        self.control(page, 'Preview this role', 'role-1', 'Body').check()
        field = self.control(page, 'Font family', 'role-1', 'Body')
        revision = 0
        for index, (value, accepted) in enumerate(FAMILIES):
            with self.subTest(family=repr(value)):
                if value.isprintable():
                    self.type_value(field, value)
                else:
                    field.evaluate('(el, v) => { el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); }', value)
                reply = self.raw(page, {'type': 'design:roles-apply', 'requestId': f'raw-family-{index}', 'baseRevision': revision,
                    'documentId': state['documentId'], 'pageVersion': state['pageVersion'],
                    'roles': [{'id': 'role-1', 'name': 'Body', 'selectors': ['[data-design-role="Body"]'], 'adapter': 'plain',
                               'properties': {'fontFamily': value}}]})
                revision = reply['revision']
                self.assertEqual(reply['type'] == 'design:roles-applied', accepted, reply)
                self.assertEqual(self.gate(page)[0], accepted, self.gate(page)[1])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_page_that_rerenders_after_the_commit_gives_the_stale_status_and_later_ops_still_settle(self, engine):
        """Given a page that changes its markup right after the bridge commits an Apply, when the receipt arrives,
        then Studio shows the stale status with the accepted CSS, and a following inspector edit and Clear both
        settle."""
        page, frame, errors = self.start(engine)
        frame.evaluate("addEventListener('message', e => { if (e.data && e.data.type === 'design:roles-apply') document.querySelector('main').append(document.createElement('hr')); })")
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        self.wait_status(page, STALE)
        stale = self.receipts(page)[-1]
        self.assertEqual((stale['outcomesComplete'], stale['outcomeReason'], stale['outcomes']), (False, 'page-changed', []))
        self.assertGreater(stale['currentPageVersion'], stale['pageVersion'])
        self.assertIn('font-size: 24px', self.preview(page)['css'])
        self.edit_inspector(page, frame, 'ordinary.body', '27')
        self.clear_preview(page, frame)
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual((self.size(frame, '[data-design-role="Body"]'), self.size(frame, '[data-design-id="ordinary.body"]')), ('16px', '27px'))
        self.assertEqual(errors, [])

    @per_engine
    def test_an_inspector_edit_survives_apply_and_clear_and_its_win_is_a_counted_mismatch_with_the_receipts_reason(self, engine):
        """Given an inspector edit of 27px on a paragraph, when a role asks for 24px on it, then the target keeps
        27px, Studio shows one mismatch whose reason is the one in the receipt, and Clear leaves the edit and the
        markup exactly as they were."""
        page, frame, errors = self.start(engine)
        self.edit_inspector(page, frame, 'ordinary.body', '27')
        before = self.look(frame)
        request = self.apply_role(page, frame, '24', role='role-2')
        self.wait_for_receipt(page, request)
        receipt = self.receipts(page)[-1]
        outcome = receipt['outcomes'][0]
        self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched']), (1, 1, 1))
        loss = outcome['losses'][0]
        self.assertEqual(self.size(frame, '[data-design-id="ordinary.body"]'), '27px')
        text = self.preview(page)['outcomes']
        self.assertIn('matched 1, checked 1 eligible text elements, mismatched 1', text)
        self.assertIn(f'1 × {loss["property"]}: {REASON_TEXT[loss["reason"]]}', text)
        self.clear_preview(page, frame)
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(self.look(frame), before)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_winning_author_rule_is_named_by_its_selector_and_shown_as_text(self, engine):
        """Given a page whose `.card p` rule outranks the role's selector, when 24px is applied, then the target keeps
        20px, the receipt names `.card p`, and Studio shows that selector in plain words as text."""
        page, frame, errors = self.open(engine, TARGET + '/card', CARD_PAGE, init=CAPTURE)
        self.record(frame)
        self.assertIn('Detected', self.detect(page))
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        loss = self.receipts(page)[-1]['outcomes'][0]['losses'][0]
        self.assertEqual((loss['reason'], loss['winningSelector']), ('author-rule', '.card p'))
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '20px')
        self.assertIn(f'1 × fontSize: overridden by {loss["winningSelector"]}', self.preview(page)['outcomes'])
        self.assertEqual(errors, [])

    @per_engine
    def test_detect_after_apply_reads_the_baseline_and_leaves_the_preview_alone(self, engine):
        """Given an applied 24px preview, when Detect runs again, then the rows still read the page baseline of 16px
        while the target renders 24px, and the accepted CSS and status are unchanged."""
        page, frame, errors = self.start(engine)
        self.wait_for_receipt(page, self.apply_role(page, frame, '24'))
        shown = self.preview(page)
        self.assertIn('Detected', self.detect(page))
        self.assertIn('16px / 400 / none / 0em', page.locator('#roleRows > li').first.inner_text())
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '24px')
        self.assertEqual(self.preview(page), shown)
        self.assertEqual(errors, [])

    @per_engine
    def test_target_only_reset_keeps_the_preview_and_reset_all_clears_it_after_its_empty_role_state(self, engine):
        """Given an inspector edit and an applied preview, when Reset this element runs, then only the edit goes and the
        preview stays; Reset all page edits dismissed sends nothing, accepted sends exactly one reset and clears the
        edit and the preview after the bridge's empty role state, and Apply works again."""
        page, frame, errors = self.start(engine)
        self.edit_inspector(page, frame, 'ordinary.body', '27')
        self.wait_for_receipt(page, self.apply_role(page, frame, '24'))
        shown = self.preview(page)
        page.get_by_role('button', name='Reset this element', exact=True).click()
        frame.wait_for_function('getComputedStyle(document.querySelector("[data-design-id=\\"ordinary.body\\"]")).fontSize === "16px"', polling=50)
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '24px')
        self.assertEqual(self.preview(page), shown)
        self.edit_inspector(page, frame, 'ordinary.body', '27')
        page.once('dialog', lambda dialog: dialog.dismiss())
        self.button(page, RESET_ALL).click()
        self.quiet(page)
        self.assertEqual(self.untargeted_resets(frame), [])
        self.assertEqual(self.preview(page), shown)
        page.once('dialog', lambda dialog: dialog.accept())
        self.button(page, RESET_ALL).click()
        self.wait_status(page, 'Role preview cleared by Reset all page edits.')
        self.assertEqual(len(self.untargeted_resets(frame)), 1)
        self.assertEqual((self.size(frame, '[data-design-role="Body"]'), self.size(frame, '[data-design-id="ordinary.body"]')), ('16px', '16px'))
        self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
        self.assertTrue(page.locator('#liveReconnectBanner').is_hidden())
        self.wait_for_receipt(page, self.apply_role(page, frame, '26'))
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '26px')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_blocked_stylesheet_is_rejected_and_the_previous_preview_is_kept(self, engine):
        """Given an accepted preview and a page that then forbids inline styles, when a second Apply is attempted,
        then the rejection says stylesheet-blocked and that the previous preview is kept, and the page and the
        shown CSS are unchanged."""
        page_html = (REPO / 'tests' / 'fixtures' / 'bridge' / 'target-role-protocol.html').read_text(encoding='utf-8')
        page, frame, errors = self.open(engine, TARGET + '/csp', page_html, init=CAPTURE)
        self.record(frame)
        self.assertIn('Detected', self.detect(page))
        self.wait_for_receipt(page, self.apply_role(page, frame, '24'))
        shown = self.preview(page)
        frame.evaluate("document.head.append(Object.assign(document.createElement('meta'), {httpEquiv: 'Content-Security-Policy', content: \"style-src 'none'\"}))")
        self.assertIn('Detected', self.detect(page))   # the policy element is a page change: take its version first
        self.type_value(self.control(page, 'Size (px)', 'role-1', 'Body'), '30')
        self.button(page, APPLY).click()
        self.wait_status(page, 'Role preview apply rejected (stylesheet-blocked); the previous preview is kept.')
        self.assertEqual(self.preview(page)['css'], shown['css'])
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '24px')
        self.assertEqual(errors, [])

    @per_engine
    def test_an_unsupported_actual_url_disables_apply_but_clear_still_works(self, engine):
        """Given the real page at a 2,001-character route, when Studio connects, then Apply is disabled with the
        unavailable reason, Clear is enabled and its receipt (which may carry a null URL) is accepted."""
        path = '/tests/fixtures/bridge/target-role-protocol.html'
        page, frame, errors = self.open(engine, ROLE_PAGE + '?' + 'x' * (2000 - len(path)), init=CAPTURE)
        page.wait_for_function('document.querySelector("#roleStatus").textContent.includes("unsupported page URL")')
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        self.record(frame)
        request = self.clear_preview(page, frame)
        self.wait_for_receipt(page, request)
        receipt = self.receipts(page)[-1]
        self.assertEqual((receipt['operation'], receipt['currentPageURL'], receipt['outcomesComplete']), ('clear', None, True))
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_route_that_becomes_unsupported_after_the_commit_keeps_the_preview_and_clear_undoes_it(self, engine):
        """Given an Apply whose page moves to a 2,001-character route right after the commit, when the stale receipt
        arrives with a null URL, then the CSS stays, Detect and Apply are disabled, and Clear removes the styles."""
        page, frame, errors = self.start(engine)
        frame.evaluate("addEventListener('message', e => { if (e.data && e.data.type === 'design:roles-apply') history.pushState(null, '', '/?' + 'x'.repeat(1999)); })")
        request = self.apply_role(page, frame, '24')
        self.wait_for_receipt(page, request)
        self.wait_status(page, STALE)
        self.assertIsNone(self.receipts(page)[-1]['currentPageURL'])
        self.assertIn('font-size: 24px', self.preview(page)['css'])
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        self.clear_preview(page, frame)
        self.wait_status(page, 'Preview cleared.')
        self.assertEqual(self.size(frame, '[data-design-role="Body"]'), '16px')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_re_hello_shows_the_snapshot_the_page_holds_and_sends_nothing_back(self, engine):
        """Given a preview applied through Studio and then replaced on the page by another client, when the same
        session says hello again, then the ready snapshot replaces the shown preview with the page's CSS, flagged as
        reported rather than measured, and Studio sends no roles request of its own."""
        page, frame, errors = self.start(engine)
        self.wait_for_receipt(page, self.apply_role(page, frame, '24'))
        state = page.evaluate('__s2b.inbound.find(m => m.type === "design:ready").roleState')
        last = self.receipts(page)[-1]
        role = {'id': 'role-1', 'name': 'Body', 'selectors': ['[data-design-role="Body"]'], 'adapter': 'plain', 'properties': {'fontSize': 30}}
        other = self.raw(page, {'type': 'design:roles-apply', 'requestId': 'raw-other', 'baseRevision': last['revision'],
                                'documentId': state['documentId'], 'pageVersion': last['currentPageVersion'], 'roles': [role]})
        self.assertEqual(other['type'], 'design:roles-applied')
        self.assertIn('font-size: 24px', self.preview(page)['css'])
        count = len(self.ops(frame, 'design:roles-apply'))
        page.evaluate('() => document.querySelector("#targetAppFrame").contentWindow.postMessage({type: "design:hello", protocolVersion: 1, sessionId: __s2b.session}, "http://target.test")')
        page.wait_for_function('document.querySelector("#rolePreviewCss").textContent.includes("font-size: 30px")')
        shown = self.preview(page)
        self.assertEqual(shown['status'], 'The page reports an accepted role preview; its checks were not repeated.')
        self.assertEqual((shown['outcomes'], shown['removed']), ('', ''))
        self.assertEqual(len(self.ops(frame, 'design:roles-apply')), count)
        self.assertEqual(errors, [])

    @per_engine
    def test_fullscreen_with_a_populated_preview_keeps_its_height_inert_panel_and_observations(self, engine):
        """Given an applied preview with draft values, when the preview goes fullscreen in fluid and fixed 1440 widths
        and back with Escape, then it stays above 500 px, the panel is inert, and the rows, CSS and preview status read the
        same afterwards while the role status reads the page-changed sentence once the resize reaches Studio as a roles-page
        (a viewport change moves the page version)."""
        page, frame, errors = self.open(engine, init=CAPTURE, viewport={'width': 1280, 'height': 800})
        self.record(frame)
        self.assertIn('Detected', self.detect(page))
        self.wait_for_receipt(page, self.apply_role(page, frame, '24'))
        def observations():
            return (self.preview(page), page.locator('#roleStatus').inner_text(),
                    page.locator('#roleRows > li').evaluate_all('rows => rows.map(row => [row.dataset.roleId, row.textContent])'),
                    page.locator('#roleRows [data-role-field]').evaluate_all('els => els.map(el => el.type === "checkbox" ? el.checked : el.value)'))
        observed = observations()
        changed = (observed[0], PAGE_CHANGED, *observed[2:])
        for width in ('#btnDeviceFluid', '#btnDeviceDesktop'):
            page.locator(width).click()
            page.locator('#btnToggleFullscreen').click()
            page.wait_for_function('document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
            page.wait_for_function('(text) => document.querySelector("#roleStatus").textContent === text', arg=PAGE_CHANGED)
            height = page.locator('#targetAppContainer').evaluate('el => el.getBoundingClientRect().height')
            self.assertGreater(height, 500, width)
            self.assertTrue(page.locator('#detectedRoles').evaluate('el => !!el.closest("[inert]")'))
            self.assertEqual(observations(), changed)
            page.keyboard.press('Escape')
            page.wait_for_function('!document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
            self.assertEqual(observations(), changed)
        self.assertEqual(errors, [])

    def fixture_page(self, name):
        """A fixture's own HTML with the bridge added, served at the fixture's URL so its vendor files and CSS resolve."""
        html = (REPO / 'fixtures' / name / 'index.html').read_text(encoding='utf-8').replace('</body>', '<script src="/fontkit-bridge.js"></script></body>')
        return TARGET + f'/fixtures/{name}/index.html', html

    def computed(self, frame, ids, prop):
        """The computed value of one CSS property for each element carrying one of the data-design-ids."""
        return frame.evaluate('([ids, prop]) => ids.map(id => getComputedStyle(document.querySelector(\'[data-design-id="\' + id + \'"]\')).getPropertyValue(prop))',
                              [ids, prop])

    def root_variables(self, frame):
        return frame.evaluate('() => ["--bs-body-font-family", "--bs-font-sans-serif"].map(name => getComputedStyle(document.documentElement).getPropertyValue(name).trim())')

    @per_engine
    def test_a_bootstrap_5_body_row_applies_with_its_variables_and_clear_restores_the_page(self, engine):
        """Given the Bootstrap 5 fixture under the real bridge, when the one row with an Adapter line is given a family and a
        size and applied, then its request role carries bootstrap5-body, the four body-tuple elements render the family and
        the sizes 16px, 22px, 22px and 16px, the root's two variables compute to the family and the preview CSS starts with the :root block (the two .btn
        elements keep 16px, as under a body binding a component with its own size rule does); when Clear is
        pressed, then the variables, the four elements' family and size and main's markup equal their values from before
        and Studio shows no preview."""
        family, size = 'Georgia, serif', 22
        body_tuple = ['bs5.button', 'bs5.navigation', 'bs5.label', 'bs.hero.cta']
        url, html = self.fixture_page('bootstrap5-static')
        page, frame, errors = self.start(engine, target=url, peer=html)
        adapter_lines = page.locator('#roleRows > li p', has_text=re.compile(r'^Adapter: '))
        self.assertEqual(adapter_lines.count(), 1)
        row = page.locator('#roleRows > li').filter(has=page.locator('p', has_text=re.compile(r'^Adapter: ')))
        role, name = row.get_attribute('data-role-id'), row.locator('strong').inner_text().rsplit(' (', 1)[0]
        before = (self.computed(frame, body_tuple, 'font-family'), self.computed(frame, body_tuple, 'font-size'),
                  self.root_variables(frame), frame.locator('main').evaluate('el => el.outerHTML'))
        self.control(page, 'Preview this role', role, name).check()
        self.type_value(self.control(page, 'Font family', role, name), family)
        self.type_value(self.control(page, 'Size (px)', role, name), str(size))
        request = self.press_apply(page, frame)
        self.assertEqual([item['adapter'] for item in request['roles']], ['bootstrap5-body'])
        self.wait_for_receipt(page, request)
        self.assertEqual(self.computed(frame, body_tuple, 'font-family'), [family] * 4)
        self.assertEqual(self.computed(frame, body_tuple, 'font-size'), ['16px', f'{size}px', f'{size}px', '16px'])
        self.assertEqual(self.root_variables(frame), [family] * 2)
        self.assertTrue(self.preview(page)['css'].startswith(f':root {{\n  --bs-body-font-family: {family};\n  --bs-font-sans-serif: {family};\n}}\n'))
        self.clear_preview(page, frame)
        page.wait_for_function('document.querySelector("#rolePreviewCss").textContent === ""')
        self.assertEqual((self.computed(frame, body_tuple, 'font-family'), self.computed(frame, body_tuple, 'font-size'),
                          self.root_variables(frame), frame.locator('main').evaluate('el => el.outerHTML')), before)
        self.assertEqual(self.preview(page)['css'], '')
        self.assertEqual(errors, [])

    MEMBERS = """() => { const key = el => { const c = getComputedStyle(el); return [c.fontFamily, c.fontSize, c.fontWeight, c.lineHeight, c.letterSpacing, c.textTransform].join('|'); };
        const body = key(document.body);
        return [...document.querySelectorAll('main *')].map((el, index) => [el, index]).filter(([el]) => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())
            && key(el) === body).map(([el, index]) => [index, el.matches('.btn')]); }"""
    STYLES = """(indices) => { const all = document.querySelectorAll('main *'); return indices.map(i => [getComputedStyle(all[i]).fontFamily, getComputedStyle(all[i]).fontSize]); }"""

    @per_engine
    def test_the_bootstrap_5_body_row_applies_to_body_text_that_has_no_ids_or_shared_class_and_clear_restores_it(self, engine):
        """Given the Bootstrap 5 fixture with 40 more unclassed paragraphs and list items without ids under the real bridge,
        when Detect runs, the one Adapter row is given a family and a size and applied, then the row has a role id and an
        enabled Apply, the request's Body role selects exactly body, the receipt line is the Body line ending page-wide, and
        every element that computed body's style before (44) computes the family and 22px except the .btn ones, which keep
        16px; when Clear is pressed, then each of them computes its family and size from before and main's markup is as before."""
        family, size = 'Georgia, serif', 22
        url, html = self.fixture_page('bootstrap5-static')
        html = html.replace('</main>', '<p>One</p>' * 20 + '<ul>' + '<li>Item</li>' * 20 + '</ul></main>')
        page, frame, errors = self.open(engine, init=CAPTURE, target=url, peer=html)
        page.get_by_role('button', name='Detect text styles', exact=True).click()
        def shown(selector, wanted):
            """The element's text once it holds the wanted text, or what it holds after 15 s."""
            return page.evaluate("""([selector, wanted]) => new Promise(done => { const start = Date.now(), poll = () => { const text = document.querySelector(selector).textContent;
                if (text.includes(wanted) || Date.now() - start > 15000) done(text); else setTimeout(poll, 50); }; poll(); })""",
                                 [selector, wanted])
        status = shown('#roleStatus', 'Detected')
        self.assertIn('Detected', status)
        self.record(frame)
        members = frame.evaluate(self.MEMBERS)
        self.assertEqual(len(members), 44)
        indices = [index for index, _ in members]
        buttons = [button for _, button in members]
        self.assertEqual(buttons.count(True), 2)
        before = (frame.evaluate(self.STYLES, indices), frame.locator('main').evaluate('el => el.outerHTML'))
        row = page.locator('#roleRows > li').filter(has=page.locator('p', has_text=re.compile(r'^Adapter: ')))
        self.assertEqual(row.count(), 1)
        role, name = row.get_attribute('data-role-id'), row.locator('strong').inner_text().rsplit(' (', 1)[0]
        self.assertIsNotNone(role)
        self.control(page, 'Preview this role', role, name).check()
        self.type_value(self.control(page, 'Font family', role, name), family)
        self.type_value(self.control(page, 'Size (px)', role, name), str(size))
        self.assertTrue(self.button(page, APPLY).is_enabled())
        request = self.press_apply(page, frame)
        self.assertEqual([(item['adapter'], item['selectors']) for item in request['roles']], [('bootstrap5-body', ['body'])])
        self.wait_for_receipt(page, request)
        self.assertIn('Preview applied to 1 role; 0 checked elements did not show it.', shown('#rolePreviewStatus', 'Preview applied to 1 role; 0 checked elements did not show it.'))
        self.assertEqual(page.locator('#rolePreviewOutcomes li p').all_inner_texts(), [
            f"{name} ({role}): matched 1, checked 0 eligible text elements, mismatched 0; applies page-wide through Bootstrap's body variables, and inherited text is not measured"])
        self.assertEqual(frame.evaluate(self.STYLES, indices), [[family, '16px' if button else f'{size}px'] for button in buttons])
        self.clear_preview(page, frame)
        page.wait_for_function('document.querySelector("#rolePreviewCss").textContent === ""')
        self.assertEqual((frame.evaluate(self.STYLES, indices), frame.locator('main').evaluate('el => el.outerHTML')), before)
        self.assertEqual(errors, [])

    @per_engine
    def test_every_request_from_the_bootstrap_4_fixture_and_the_plain_role_target_carries_the_plain_adapter(self, engine):
        """Given the Bootstrap 4 fixture and the plain role target under the real bridge, when every detected row is selected
        with a size no element computes before and Apply is pressed, then each role in the request carries plain, no row
        shows an Adapter line, every receipt outcome has mismatched 0 and no losses, Studio reports that no checked element
        failed to show it, and every element the request selectors match computes the typed size."""
        url4, html4 = self.fixture_page('bootstrap4-static')
        size = 27
        for label, options, roles, matched in (('bootstrap4', {'target': url4, 'peer': html4}, 16, 20), ('role target', {}, 2, 2)):
            with self.subTest(target=label):
                page, frame, errors = self.start(engine, **options)
                self.assertEqual(page.locator('#roleRows > li p', has_text=re.compile(r'^Adapter: ')).count(), 0)
                for index, name in enumerate(self.names(page), start=1):
                    name = name.rsplit(' (', 1)[0]
                    self.control(page, 'Preview this role', f'role-{index}', name).check()
                    self.type_value(self.control(page, 'Size (px)', f'role-{index}', name), str(size))
                request = self.press_apply(page, frame)
                self.assertEqual(len(request['roles']), roles)
                self.assertEqual({item['adapter'] for item in request['roles']}, {'plain'})
                self.wait_for_receipt(page, request)
                self.wait_status(page, f'Preview applied to {roles} roles; 0 checked elements did not show it.')
                outcomes = self.receipts(page)[-1]['outcomes']
                self.assertEqual([(item['mismatched'], item['losses']) for item in outcomes], [(0, [])] * roles)
                self.assertEqual(sum(item['matched'] for item in outcomes), matched)
                for role in request['roles']:
                    sizes = frame.evaluate('(selectors) => [...document.querySelectorAll(selectors.join(", "))].map(el => getComputedStyle(el).fontSize)',
                                           role['selectors'])
                    self.assertEqual(set(sizes), {f'{size}px'}, role['id'])
                self.assertEqual(errors, [])
