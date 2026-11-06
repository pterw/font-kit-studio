"""Inspector readouts tell the truth (0.4.1 audit rows S01, S02, S03)."""

import unittest

import test_studio_live as base
from support import ENGINES

ARRANGE = base.ARRANGE
NO_CHANGES = 'No changes on this element.'


class ResetAfterReloadTests(base.ArrangeCase):
    def reload_with_saved_move(self, engine):
        page, errors, frame = self.open_arrange(engine)
        self.select(page, frame, 'card.c')
        page.locator('#liveMoveFirst').click()
        self.wait_badge(page, r'^Live · rev 1$')
        frame.evaluate('location.reload()')
        page.locator('#liveReconnectBanner').wait_for(state='visible')
        frame = self.wait_ready(page, 11)
        return page, errors, frame

    def test_reset_stays_enabled_for_an_element_with_a_saved_move_after_a_reload(self):
        """Given a DOM move saved and the page reloaded, When the moved card is selected,
        Then Reset this element is enabled and gives no 'No changes' reason."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.reload_with_saved_move(engine)
                saved = self.export(page)['live']['structure']
                self.assertTrue(any('card.c' in entry['ids'] for entry in saved), 'the saved move survived the reload')
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
                self.select(page, frame, 'card.c')
                reset = page.locator('#liveResetTarget')
                self.assertTrue(reset.is_enabled())
                self.assertNotIn(NO_CHANGES, reset.get_attribute('title') or '')
                self.assertNotIn(NO_CHANGES, page.locator('[data-hint-for="liveResetTarget"]').all_inner_texts())
                unmoved = 'hero.lead'
                self.assertFalse(any(unmoved in entry['ids'] for entry in self.export(page)['live']['structure']))
                self.select(page, frame, unmoved)
                self.assertFalse(page.locator('#liveResetTarget').is_enabled())
                self.assertEqual(errors, [])

    def test_reset_stays_disabled_for_an_element_with_nothing_saved(self):
        """Given nothing overridden, moved or saved, When a card is selected,
        Then Reset this element is disabled with its reason."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.select(page, frame, 'card.c')
                reset = page.locator('#liveResetTarget')
                self.assertFalse(reset.is_enabled())
                self.assertIn(NO_CHANGES, reset.get_attribute('title') or '')
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
