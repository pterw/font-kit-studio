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


class SeededReadoutCase(base.LiveCase):
    def seed(self, engine, **style):
        """Opens the fake target with inline styles on hero.lead and selects it."""
        page, errors = self.open(engine)
        self.wait_connected(page)
        frame = self.frame(page)
        frame.evaluate("""(style) => { const el = document.querySelector('[data-design-id="hero.lead"]');
            Object.assign(el.style, style); }""", style)
        self.select(page, frame, 'hero.lead')
        return page, errors, frame

    def override(self, page, key='color'):
        return self.export(page)['live']['overrides'].get('hero.lead', {}).get(key)


class ColourAlphaTests(SeededReadoutCase):
    TRANSLUCENT = 'rgba(108, 102, 118, 0.6)'

    def test_the_swatch_keeps_the_alpha_of_a_translucent_colour(self):
        """Given a colour with alpha 0.6 shown as #6c667699, When the swatch is set to #112233,
        Then the export holds #11223399 and the text box mirrors it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.seed(engine, color=self.TRANSLUCENT)
                self.assertEqual(page.locator('#liveColorHex').input_value(), '#6c667699')
                page.locator('#liveColor').fill('#112233')
                self.wait_live(page)
                self.assertEqual(self.override(page), '#11223399')
                self.assertEqual(page.locator('#liveColorHex').input_value(), '#11223399')
                self.assertEqual(errors, [])

    def test_typing_a_colour_in_the_text_box_is_sent_as_typed(self):
        """Given a translucent colour, When #112233 is typed in the text box,
        Then the export holds the opaque #112233."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.seed(engine, color=self.TRANSLUCENT)
                self.assertEqual(page.locator('#liveColorHex').input_value(), '#6c667699')
                box = page.locator('#liveColorHex')
                box.fill('#112233')
                box.press('Tab')
                self.wait_live(page)
                self.assertEqual(self.override(page), '#112233')
                self.assertEqual(errors, [])

    def test_the_swatch_writes_an_opaque_colour_when_the_colour_has_no_alpha(self):
        """Given an opaque colour, When the swatch is set to #112233, Then the export holds #112233."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.seed(engine, color='rgb(108, 102, 118)')
                self.assertEqual(page.locator('#liveColorHex').input_value(), '#6c6676')
                page.locator('#liveColor').fill('#112233')
                self.wait_live(page)
                self.assertEqual(self.override(page), '#112233')
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
