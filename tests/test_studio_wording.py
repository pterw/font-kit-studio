"""Studio wording that has to point at the real cause (v0.4.1 Task 8)."""

import re
import unittest
import urllib.parse

from support import ENGINES
from test_studio_live import APP, TARGET, LiveCase

ERROR_PAGE = 'If this is an error page (404 or 400), the proxy adds no bridge to it; go back to a normal page.'
NPX_TEXT = ('npx fontkitstudio adds the bridge to the page itself. If Font Kit Studio does not '
            'connect, the terminal where the command runs says why.')
KIT_STUDIO_ONLY = 'Loaded in Studio only. The Live App does not get this kit; add it to the app itself.'
NO_BRIDGE_BADGE = r'^No bridge answered at http://target\.test within 4 s\.$'


def one_line(text):
    return re.sub(r'\s+', ' ', text).strip()


class NoBridgeErrorPageTests(LiveCase):
    def test_the_served_hint_ends_with_the_error_page_sentence(self):
        """Given a served Studio and a page with no bridge, When the 4 s badge appears,
        Then the visible hint ends with the error-page sentence."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=f'{TARGET}/no-bridge.html')
                self.wait_badge(page, NO_BRIDGE_BADGE, timeout=7000)
                self.assertTrue(one_line(page.locator('#bridgeHint').inner_text()).endswith(ERROR_PAGE))
                self.assertEqual(errors, [])

    def test_the_npx_hint_is_the_npx_text_and_the_sentence(self):
        """Given ?token= (npx mode; the Node-based npx test needs the package server, this one does not),
        When the 4 s badge appears, Then the hint is the npx text, a space, the sentence."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                target = urllib.parse.quote(f'{TARGET}/no-bridge.html', safe='')
                page.goto(f'{APP}?token=t&target={target}')
                self.wait_badge(page, NO_BRIDGE_BADGE, timeout=7000)
                self.assertEqual(one_line(page.locator('#bridgeHint').inner_text()), f'{NPX_TEXT} {ERROR_PAGE}')
                self.assertEqual(errors, [])


class AdobeKitStudioOnlyTests(LiveCase):
    def open_with_kit_routes(self, engine):
        """Open Studio with every typekit stylesheet request held in self.held; no network."""
        context = self.context(engine)
        self.held = []
        context.route('https://use.typekit.net/**', lambda route: self.held.append(route))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(APP)
        return page, errors

    def release(self, route):
        route.fulfill(status=200, content_type='text/css', body='/* kit */')

    def wait_text(self, page, selector, text):
        page.wait_for_function('([s, t]) => document.querySelector(s).textContent === t', arg=[selector, text],
                               timeout=5000)

    def test_the_adobe_kit_field_says_the_kit_loads_in_studio_only(self):
        """Given the Adobe kit field with a kit id and its stylesheet fulfilled,
        When the stylesheet loads, Then #kitStatus says the Live App does not get it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open_with_kit_routes(engine)
                page.locator('#kitId').fill('abc123')
                page.locator('#loadKit').click()
                self.wait_held(page, 1)
                self.release(self.held[0])
                self.wait_text(page, '#kitStatus', KIT_STUDIO_ONLY)
                self.assertEqual(errors, [])

    def wait_held(self, page, count):
        for _ in range(100):
            if len(self.held) >= count:
                return
            page.wait_for_timeout(50)
        self.fail(f'expected {count} kit stylesheet requests, saw {len(self.held)}')

    def test_the_composer_kit_field_says_the_kit_loads_in_studio_only(self):
        """Given the Composer kit field with one kit id and its stylesheet fulfilled,
        When it loads, Then #composerStatus says the Live App does not get it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open_with_kit_routes(engine)
                page.locator('#modeComposer').click()
                page.locator('#composerKitIds').fill('abc123')
                page.locator('#loadComposerKits').click()
                self.wait_held(page, 1)
                self.release(self.held[0])
                self.wait_text(page, '#composerStatus', KIT_STUDIO_ONLY)
                self.assertEqual(errors, [])

    def test_the_composer_kit_field_says_it_once_every_kit_has_loaded(self):
        """Given two kit ids (abc123, def456), When the first stylesheet loads, Then the count shows;
        When the second loads, Then the composer says the kits load in Studio only."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open_with_kit_routes(engine)
                page.locator('#modeComposer').click()
                page.locator('#composerKitIds').fill('abc123, def456')
                page.locator('#loadComposerKits').click()
                self.wait_held(page, 2)
                self.release(self.held[0])
                self.wait_text(page, '#composerStatus', 'Loaded 1/2 Adobe kit stylesheets.')
                self.release(self.held[1])
                self.wait_text(page, '#composerStatus', KIT_STUDIO_ONLY)
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
