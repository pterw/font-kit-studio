"""Studio wording that has to point at the real cause (v0.4.1 Task 8)."""

import re
import unittest
import urllib.parse

from support import ENGINES
from test_studio_live import APP, TARGET, LiveCase

ERROR_PAGE = 'If this is an error page (404 or 400), the proxy adds no bridge to it; go back to a normal page.'
NPX_TEXT = ('npx fontkitstudio adds the bridge to the page itself. If Font Kit Studio does not '
            'connect, the terminal where the command runs says why.')
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


if __name__ == '__main__':
    unittest.main()
