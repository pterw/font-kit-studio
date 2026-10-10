"""The actual Studio and bridge render literal baseline role observations."""
from pathlib import Path

from support import ENGINES
from test_studio_roles import ROLE_PAGE, UNAVAILABLE, StudioRoleCase


class StudioRoleIntegrationTests(StudioRoleCase):
    def test_fullscreen_preserves_roles_and_preview_height_through_escape(self):
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
                for width in ('#btnDeviceFluid', '#btnDeviceDesktop'):
                    page.locator(width).click()
                    page.locator('#btnToggleFullscreen').click()
                    page.wait_for_function('document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                    info = page.evaluate('''() => {
                        const s=document.querySelector('#previewScroller'), f=document.querySelector('#targetAppFrame');
                        s.scrollLeft=s.scrollWidth;
                        return {height:document.querySelector('#targetAppContainer').getBoundingClientRect().height,
                            right:f.getBoundingClientRect().right, edge:s.getBoundingClientRect().right,
                            bottom:s.getBoundingClientRect().bottom, width:s.scrollWidth, client:s.clientWidth};
                    }''')
                    print('FULLSCREEN', engine, width, info)
                    self.assertGreater(info['height'], 500)
                    self.assertLessEqual(info['bottom'], 800)
                    self.assertLessEqual(info['right'], info['edge'] + .5)
                    if width == '#btnDeviceFluid':
                        self.assertEqual(info['width'], info['client'])
                    else:
                        self.assertEqual(info['width'], 1440)
                        self.assertGreater(info['width'], info['client'])
                    self.assertTrue(page.locator('#detectedRoles').evaluate('el=>!!el.closest("[inert]")'))
                    self.assertEqual(observations(), observed)
                    page.keyboard.press('Escape')
                    page.wait_for_function('!document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                    self.assertEqual(observations(), observed)
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
                    output = Path('C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2')
                    page.locator('#detectedRoles').screenshot(path=str(output / f's1-{width}.png'))
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
