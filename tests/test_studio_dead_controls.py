"""Dead or misleading controls (v0.2.1 Task 7).

Every test asserts what the person sees: the composition that was applied, the dialog and both of
its answers, the chips, the demo's visible text, the Move into select and button, the selection
after a sibling click, the Library label, the field text and message after a refusal, the colour
message and the colour that stayed applied.

Two groups:
  * Studio-only tests (LiveCase): Studio on http://studio.test, nothing connected.
  * Real-bridge tests (LiveIntegrationCase): the real scripts/serve.py, Studio and the real demo
    over `postMessage` across two origins (the demo buttons, Move into, the sibling click, the
    colour messages and the SVG note).
"""

import unittest

from support import ENGINES, canvas_snapshot
from test_live_integration import LiveIntegrationCase
from test_studio_live import APP, LiveCase

ASTERIA_BACKGROUND = 'rgb(3, 4, 9)'      # asteria preset: #030409
EDITORIAL_BACKGROUND = 'rgb(245, 241, 232)'   # rowdemo and blank presets: #f5f1e8
SIGNUP_SUBMIT = '.signup button[type="submit"]'
TITLE_SELECTOR = '[data-design-id="landing.hero.title"]'
FREE_FONTS_ON = 'Free fonts are on: families load as their cards scroll into view.'
COMPOSITION_UPDATES = ('window.__received.filter(item => item.data && item.data.type === "design:update"'
                       ' && !("targetId" in item.data))')


class StudioOnlyCase(LiveCase):
    def studio(self, engine, fonts=False):
        """Studio alone on studio.test. With `fonts`, Google Fonts answers with empty CSS so a load succeeds."""
        context = self.context(engine)
        if fonts:
            context.route('https://fonts.googleapis.com/**',
                          lambda route: route.fulfill(status=200, content_type='text/css', body='/* offline */'))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.dialogs = []
        page.goto(APP)
        page.locator('#modeComposer').click()
        return page, errors

    def answer_dialogs(self, page, accept):
        """Answer every dialog the same way and keep its text. Without a handler Playwright dismisses them."""
        def handler(dialog):
            page.dialogs.append({'type': dialog.type, 'message': dialog.message})
            dialog.accept() if accept else dialog.dismiss()
        page.on('dialog', handler)

    def canvas_background(self, page, expected=None):
        """The canvas colour. It fades in, so a test that knows what it expects waits for it."""
        if expected:
            page.wait_for_function('(want) => getComputedStyle(document.querySelector("#composerCanvas")).backgroundColor === want',
                                   arg=expected)
        return page.locator('#composerCanvas').evaluate('el => getComputedStyle(el).backgroundColor')

    def slot_texts(self, page):
        return page.locator('#composerCanvas .flow-slot, #composerCanvas [data-row-child]').evaluate_all(
            'els => els.map(el => el.textContent.trim())')

    def edit_first_slot(self, page, text):
        page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
        page.locator('#slotInspector [data-bind="text"]').fill(text)

    def preset_title(self, page):
        return page.locator('#composerStatus').inner_text()


class PresetSelectTests(StudioOnlyCase):
    def test_choosing_a_preset_applies_it_without_pressing_apply(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.assertEqual(self.canvas_background(page), EDITORIAL_BACKGROUND)
                page.locator('#compositionPreset').select_option('asteria')
                page.wait_for_function('() => /^Asteria/.test(document.querySelector("#composerStatus").textContent)')
                self.assertEqual(self.canvas_background(page, ASTERIA_BACKGROUND), ASTERIA_BACKGROUND)
                self.assertEqual(page.locator('#compositionPreset').input_value(), 'asteria')
                page.locator('#compositionPreset').select_option('rowdemo')
                page.wait_for_function('() => /^Editorial/.test(document.querySelector("#composerStatus").textContent)')
                self.assertEqual(self.canvas_background(page, EDITORIAL_BACKGROUND), EDITORIAL_BACKGROUND)
                self.assertEqual(page.dialogs, [], 'an untouched composition is replaced without a question')
                self.assertEqual(errors, [])

    def test_switching_after_edits_asks_and_cancel_keeps_the_edits_and_the_old_choice(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.answer_dialogs(page, accept=False)
                self.edit_first_slot(page, 'My own wordmark')
                page.locator('#compositionPreset').select_option('asteria')
                self.assertEqual(len(page.dialogs), 1)
                self.assertEqual(page.dialogs[0]['type'], 'confirm')
                self.assertIn('replace', page.dialogs[0]['message'].lower())
                self.assertIn('edits', page.dialogs[0]['message'].lower())
                self.assertEqual(page.locator('#compositionPreset').input_value(), 'rowdemo', 'the select goes back')
                self.assertEqual(self.canvas_background(page), EDITORIAL_BACKGROUND)
                self.assertIn('My own wordmark', self.slot_texts(page)[0])
                self.assertEqual(self.export(page)['composition']['slots'][0]['text'], 'My own wordmark')
                self.assertEqual(errors, [])

    def test_switching_after_edits_replaces_them_when_the_answer_is_yes(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.answer_dialogs(page, accept=True)
                self.edit_first_slot(page, 'My own wordmark')
                page.locator('#compositionPreset').select_option('asteria')
                page.wait_for_function('() => /^Asteria/.test(document.querySelector("#composerStatus").textContent)')
                self.assertEqual(len(page.dialogs), 1)
                self.assertEqual(self.canvas_background(page, ASTERIA_BACKGROUND), ASTERIA_BACKGROUND)
                self.assertEqual(page.locator('#compositionPreset').input_value(), 'asteria')
                self.assertNotIn('My own wordmark', page.locator('#composerCanvas').inner_text())
                self.assertEqual(errors, [])

    def test_a_cancelled_switch_asks_again_next_time_because_the_edits_are_still_there(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.answer_dialogs(page, accept=False)
                self.edit_first_slot(page, 'Kept')
                page.locator('#compositionPreset').select_option('blank')
                page.locator('#compositionPreset').select_option('blank')
                self.assertEqual(len(page.dialogs), 2, 'the edits are still there, so the question comes back')
                self.assertEqual(errors, [])

    def test_the_apply_button_resets_the_selected_preset_and_asks_before_replacing_edits(self):
        # Apply is kept: it is the only way to put the preset that is already selected back (the select
        # fires no change for the same value), so it does more than the select.
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.answer_dialogs(page, accept=False)
                self.edit_first_slot(page, 'My own wordmark')
                page.locator('#applyPreset').click()
                self.assertEqual(len(page.dialogs), 1)
                self.assertIn('My own wordmark', self.slot_texts(page)[0], 'Cancel keeps the edit')
                self.assertEqual(errors, [])

    def test_apply_on_an_untouched_preset_says_there_is_nothing_to_reset(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                self.answer_dialogs(page, accept=True)
                before = canvas_snapshot(page)
                page.locator('#applyPreset').click()
                self.assertRegex(self.preset_title(page), r'already applied')
                self.assertEqual(page.dialogs, [])
                # Re-applying the preset would regenerate every slot id, which the snapshot keeps; it leaves out what the
                # canvas width derives (the row's collapsed state), which settles a frame after the Composer opens.
                self.assertEqual(canvas_snapshot(page), before)
                # With an edit, the same button resets the preset.
                self.edit_first_slot(page, 'My own wordmark')
                page.locator('#applyPreset').click()
                self.assertEqual(len(page.dialogs), 1)
                page.wait_for_function('() => /applied\\. Every slot/.test(document.querySelector("#composerStatus").textContent)')
                self.assertNotIn('My own wordmark', page.locator('#composerCanvas').inner_text())
                self.assertEqual(errors, [])


class PresetEditsCountTests(StudioOnlyCase):
    """Everything the preset replaces counts as an edit, not only the slots."""

    def dismissed_switch(self, page):
        page.once('dialog', lambda dialog: (page.dialogs.append({'message': dialog.message}), dialog.dismiss()))
        page.locator('#compositionPreset').select_option('asteria')
        self.assertEqual(len(page.dialogs), 1)
        self.assertEqual(page.locator('#compositionPreset').input_value(), 'rowdemo')

    def test_a_canvas_width_edit_counts_as_an_edit(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.locator('#canvasWidth').select_option('1200')
                self.dismissed_switch(page)
                self.assertEqual(page.locator('#canvasWidth').input_value(), '1200', 'Cancel keeps the width')
                self.assertEqual(errors, [])

    def test_a_background_edit_counts_as_an_edit(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.locator('#canvasBgHex').fill('#112233')
                self.dismissed_switch(page)
                self.assertEqual(page.locator('#canvasBgHex').input_value(), '#112233', 'Cancel keeps the colour')
                self.assertEqual(self.canvas_background(page, 'rgb(17, 34, 51)'), 'rgb(17, 34, 51)')
                self.assertEqual(errors, [])

    def test_an_imported_composition_counts_as_edits(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                document = self.export(page)
                document['composition']['slots'][0]['text'] = 'Imported wordmark'
                self.import_document(page, document)
                self.assertIn('Imported wordmark', self.slot_texts(page)[0])
                self.dismissed_switch(page)
                self.assertIn('Imported wordmark', self.slot_texts(page)[0], 'Cancel keeps the import')
                self.assertEqual(errors, [])


class LinkedPresetTests(StudioOnlyCase):
    """A linked composition (Sync to Live App pressed) streams once per preset that is actually applied."""

    def linked(self, engine):
        page, errors = self.open(engine)
        page.dialogs = []
        self.wait_connected(page)
        frame = self.frame(page)
        page.locator('#btnSyncToApp').click()
        self.wait_live(page)
        page.locator('#viewSpecimenCanvas').click()
        return page, frame, errors

    def settled(self, page, frame, at_least):
        """The number of composition updates once at least `at_least` have arrived and no more follow."""
        # The target frame is hidden in the specimen view, where animation-frame polling never runs.
        frame.wait_for_function(f'{COMPOSITION_UPDATES}.length >= {at_least}', polling=50)
        page.wait_for_timeout(250)     # proves a negative: a stray extra update would show up within this time
        return frame.evaluate(f'{COMPOSITION_UPDATES}.length')

    def sent(self, page, frame, expected):
        count = self.settled(page, frame, expected)
        self.assertEqual(count, expected)
        return count

    def test_the_target_gets_one_update_per_applied_preset_and_none_for_the_ones_not_applied(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked(engine)
                self.sent(page, frame, 1)
                page.locator('#compositionPreset').select_option('asteria')       # untouched: applied, +1
                self.sent(page, frame, 2)
                page.locator('#applyPreset').click()                              # untouched: nothing to reset, +0
                self.assertRegex(self.preset_title(page), r'already applied')
                self.sent(page, frame, 2)
                self.edit_first_slot(page, 'My own wordmark')                     # the edit streams
                streamed = self.settled(page, frame, 3)
                page.once('dialog', lambda dialog: (page.dialogs.append(dialog.message), dialog.dismiss()))
                page.locator('#compositionPreset').select_option('blank')         # Cancel: +0
                self.assertEqual(len(page.dialogs), 1)
                self.sent(page, frame, streamed)
                page.once('dialog', lambda dialog: (page.dialogs.append(dialog.message), dialog.accept()))
                page.locator('#compositionPreset').select_option('blank')         # Accept: +1
                self.assertEqual(len(page.dialogs), 2)
                self.sent(page, frame, streamed + 1)
                self.assertEqual(errors, [])


class KitSelectTests(StudioOnlyCase):
    def test_custom_manual_leads_to_the_kit_field_and_prefills_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.locator('#kitPreset').select_option('custom')
                self.assertEqual(page.evaluate('document.activeElement.id'), 'composerKitIds')
                self.assertEqual(page.locator('#composerKitIds').input_value(), '')
                status = self.preset_title(page)
                self.assertRegex(status, r'(?i)kit')
                self.assertRegex(status, r'(?i)nothing is prefilled|press Load')
                page.locator('#composerKitIds').fill('abc1def')
                page.locator('#loadComposerKits').click()
                self.assertEqual(page.locator('link[data-composer-kit="true"]').evaluate_all('els => els.map(el => el.href)'),
                                 ['https://use.typekit.net/abc1def.css'])
                self.assertEqual(errors, [])


class OneCutCardTests(StudioOnlyCase):
    def test_a_font_with_one_cut_shows_no_style_chip_and_others_keep_theirs(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                page.locator('#modeLibrary').click()
                cards = page.locator('#libraryView .card').evaluate_all(
                    'els => els.map(el => ({name: el.querySelector(".family").textContent, cuts: el._font.styles.length,'
                    ' chips: [...el.querySelectorAll(".style-chip")].filter(c => c.offsetParent !== null).map(c => c.textContent)}))')
                single = [card for card in cards if card['cuts'] == 1]
                several = [card for card in cards if card['cuts'] > 1]
                self.assertTrue(single, 'the library has one-cut fonts, or this test proves nothing')
                self.assertTrue(several)
                self.assertEqual([card for card in single if card['chips']], [])
                self.assertTrue(all(len(card['chips']) == card['cuts'] for card in several), several)
                self.assertEqual(errors, [])


class LibraryLoadedLabelTests(StudioOnlyCase):
    FALLBACK = 'fallback fonts'

    def test_a_remembered_choice_and_a_fresh_ask_say_the_same_thing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                context.add_init_script('localStorage.setItem("fontkit-free-fonts", "yes")')
                context.route('https://fonts.googleapis.com/**',
                              lambda route: route.fulfill(status=200, content_type='text/css', body='/* offline */'))
                page = context.new_page()
                page.goto(APP)
                page.locator('#modeLibrary').click()
                self.assertEqual(page.locator('#freeFontStatus').inner_text(), FREE_FONTS_ON)

    def test_fonts_loaded_from_the_composer_are_reported_in_the_library(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine, fonts=True)
                page.locator('#modeLibrary').click()
                self.assertIn(self.FALLBACK, page.locator('#freeFontStatus').inner_text(), 'true before any load')
                page.locator('#modeComposer').click()
                page.locator('#loadFreeFonts').click()
                page.wait_for_function('() => /^Loaded \\d+\\/\\d+ free font stylesheets/.test(document.querySelector("#composerStatus").textContent)')
                page.locator('#modeLibrary').click()
                label = page.locator('#freeFontStatus').inner_text()
                self.assertRegex(label, r'^Loaded \d+/\d+ free font stylesheets')
                self.assertNotIn(self.FALLBACK, label)
                self.assertEqual(errors, [])

    def test_switching_the_kit_to_free_google_fonts_is_reported_too(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine, fonts=True)
                page.locator('#kitPreset').select_option('adobe')
                page.locator('#kitPreset').select_option('google')
                page.wait_for_function('() => /^Loaded \\d+\\/\\d+ /.test(document.querySelector("#composerStatus").textContent)')
                page.locator('#modeLibrary').click()
                self.assertNotIn(self.FALLBACK, page.locator('#freeFontStatus').inner_text())
                self.assertEqual(errors, [])

    def test_the_librarys_own_load_still_reports_its_progress(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine, fonts=True)
                page.locator('#modeLibrary').click()
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => /^Loaded \\d+\\/\\d+ free font stylesheets/.test(document.querySelector("#freeFontStatus").textContent)')
                self.assertNotIn(self.FALLBACK, page.locator('#freeFontStatus').inner_text())
                self.assertEqual(errors, [])


class RecursionBlockTests(StudioOnlyCase):
    def test_a_refused_address_stays_in_the_field_and_the_message_says_why(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.studio(engine)
                field = page.locator('#targetAppUrl')
                field.fill(APP)
                page.locator('#btnConnectTarget').click()
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), 'Recursion blocked')
                self.assertEqual(field.input_value(), APP, 'the person can see and correct what they typed')
                message = page.locator('#targetUrlProblem')
                self.assertTrue(message.is_visible())
                self.assertRegex(message.inner_text(), r'(?i)studio')
                self.assertRegex(message.inner_text(), r'(?i)itself|its own')
                self.assertIsNone(page.locator('#targetAppFrame').get_attribute('src'))
                # Correcting the address clears the message.
                field.fill('http://localhost:8001/demo/')
                self.assertFalse(message.is_visible())
                self.assertEqual(errors, [])


class DemoPlanTests(LiveIntegrationCase):
    def test_the_demo_plan_buttons_mark_the_chosen_plan_with_visible_text(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open(engine, query=False)
                page.goto(self.target)       # the demo on its own, no Studio
                solo = page.get_by_role('button', name='Choose Solo')
                solo.click()
                page.wait_for_function('() => /Solo chosen/.test(document.querySelector("#pricing").innerText)')
                self.assertEqual(page.locator('#pricing .plan').first.get_attribute('data-chosen'), 'true')
                self.assertEqual(page.get_by_role('button', name='Choose Studio').inner_text(), 'Choose Studio')
                page.get_by_role('button', name='Choose Studio').click()
                page.wait_for_function('() => /Studio chosen/.test(document.querySelector("#pricing").innerText)')
                self.assertNotIn('Solo chosen', page.locator('#pricing').inner_text(), 'one plan at a time')
                self.assertEqual(page.errors, [])

    def test_in_interact_mode_the_demo_buttons_work_through_studio_and_select_mode_still_selects(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                # Select mode: the click picks the element for editing and the app does not run it.
                page.frame_locator('#targetAppFrame').get_by_role('button', name='Choose Solo').click()
                page.wait_for_function('() => Boolean(document.querySelector("#liveTargetName"))')
                self.assertNotIn('Solo chosen', frame.locator('#pricing').inner_text())
                page.locator('#bridgeModeInteract').click()
                page.frame_locator('#targetAppFrame').get_by_role('button', name='Choose Solo').click()
                frame.wait_for_function('() => /Solo chosen/.test(document.querySelector("#pricing").innerText)')
                page.frame_locator('#targetAppFrame').get_by_role('button', name='Choose Studio').click()
                frame.wait_for_function('() => /Studio chosen/.test(document.querySelector("#pricing").innerText)')
                self.assertEqual(page.errors, [])


class LibraryLabelFromTheInspectorTests(LiveIntegrationCase):
    def test_picking_a_library_family_in_the_live_target_inspector_updates_the_library_label(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                page.locator('#modeLibrary').click()
                self.assertIn('fallback fonts', page.locator('#freeFontStatus').inner_text(), 'true before the ask')
                page.locator('#modeComposer').click()
                self.select_hero_title(page)
                page.locator('#liveFontFamily').select_option(label='Inter')
                page.locator('#modeLibrary').click()
                self.assertEqual(page.locator('#freeFontStatus').inner_text(), FREE_FONTS_ON)
                self.assertEqual(page.errors, [])


class ArrangeRealBridgeTests(LiveIntegrationCase):
    def test_move_into_starts_on_a_placeholder_and_stays_disabled_with_a_reason_until_a_container_is_chosen(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.click_in_target(page, SIGNUP_SUBMIT, '/Subscribe/')
                select = page.locator('#liveMoveContainer')
                button = page.locator('#liveMoveInto')
                self.assertEqual(select.input_value(), '', 'no container is preselected')
                self.assertIn('Choose', select.evaluate('el => el.selectedOptions[0].textContent'))
                self.assertTrue(button.is_disabled())
                reason = page.locator('#liveMoveIntoHint')
                self.assertTrue(reason.is_visible())
                self.assertRegex(reason.inner_text(), r'(?i)choose a container')
                self.assertRegex(button.get_attribute('title') or '', r'(?i)choose a container')
                options = select.locator('option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                solo = next((value for value, name in options if name == 'Solo'), None)
                self.assertIsNotNone(solo, options)
                select.select_option(solo)
                self.assertFalse(button.is_disabled())
                self.assertFalse(reason.is_visible())
                self.assertEqual(button.get_attribute('title') or '', '')
                select.select_option('')
                self.assertTrue(button.is_disabled(), 'going back to the placeholder disables it again')
                self.assertTrue(reason.is_visible())
                self.assertEqual(page.errors, [])

    def test_a_click_on_an_arrange_sibling_selects_that_element(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.click_in_target(page, '[data-design-id="landing.feature.sync.title"]', 'landing.feature.sync.title')
                sibling = page.locator('#liveSiblingList [data-sibling-id="landing.feature.sync.body"]')
                sibling.wait_for(state='visible')
                self.assertIsNone(sibling.get_attribute('aria-current'))
                sibling.click()
                self.inspector_target(page, 'landing.feature.sync.body')
                page.wait_for_function('() => { const el = document.querySelector("#liveSiblingList [aria-current=true]");'
                                       ' return Boolean(el) && el.dataset.siblingId === "landing.feature.sync.body"; }')
                self.assertEqual(page.errors, [])

    def test_the_chosen_container_survives_a_refresh_of_the_arrange_block(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.click_in_target(page, SIGNUP_SUBMIT, '/Subscribe/')
                select = page.locator('#liveMoveContainer')
                options = select.locator('option').evaluate_all('els => els.map(el => [el.value, el.textContent])')
                solo = next(value for value, name in options if name == 'Solo')
                select.select_option(solo)
                # The bridge refuses this move (a submit button leaves its form); the refusal re-renders the block.
                page.locator('#liveMoveInto').click()
                page.locator('#liveMoveGuard').wait_for(state='visible')
                self.assertEqual(page.locator('#liveMoveContainer').input_value(), solo)
                self.assertFalse(page.locator('#liveMoveInto').is_disabled(), 'Move into stays enabled')
                self.assertFalse(page.locator('#liveMoveIntoHint').is_visible())
                self.assertEqual(page.errors, [])


class ColourMessageTests(LiveIntegrationCase):
    def title_colour(self, frame):
        return self.style(frame, TITLE_SELECTOR, 'color')

    def count_colour_updates(self, frame):
        """Count the `design:update` messages with a colour that reach the page, as the page sees them."""
        frame.evaluate("""() => { if (window.__colourUpdates) return; window.__colourUpdates = [];
            window.addEventListener('message', (event) => { if (event.data && event.data.type === 'design:update'
                && event.data.patch && 'color' in event.data.patch) window.__colourUpdates.push(event.data.patch.color); }); }""")

    def colour_updates(self, frame):
        return frame.evaluate('window.__colourUpdates')

    def test_invalid_colour_text_says_so_next_to_the_field_and_keeps_the_applied_colour(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.count_colour_updates(frame)
                self.select_hero_title(page)
                field = page.locator('#liveColorHex')
                field.fill('#112233')
                field.press('Enter')
                self.wait_style(frame, TITLE_SELECTOR, 'color', 'rgb(17, 34, 51)')
                self.assertEqual(self.colour_updates(frame), ['#112233'])
                message = page.locator('#liveColorMessage')
                self.assertFalse(message.is_visible())
                field.fill('notacolour')
                field.press('Tab')
                message.wait_for(state='visible')
                self.assertIn('notacolour', message.inner_text())
                self.assertRegex(message.inner_text(), r'(?i)#112233|kept|still')
                self.assertEqual(message.evaluate('el => el.closest(".inspector-field") === document.querySelector("#liveColorHex").closest(".inspector-field")'), True)
                page.wait_for_timeout(300)     # proves a negative: nothing may reach the page later
                self.assertEqual(self.colour_updates(frame), ['#112233'], 'the invalid text was never posted to the page')
                self.assertEqual(self.title_colour(frame), 'rgb(17, 34, 51)')
                self.assertEqual(field.input_value(), '#112233', 'the field shows the colour that is applied')
                # A valid value clears the message and applies.
                field.fill('#ff0000')
                field.press('Enter')
                self.wait_style(frame, TITLE_SELECTOR, 'color', 'rgb(255, 0, 0)')
                self.assertFalse(message.is_visible())
                self.assertEqual(self.colour_updates(frame), ['#112233', '#ff0000'])
                self.assertEqual(page.errors, [])

    def test_the_colour_is_checked_when_the_value_is_committed_never_while_typing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.count_colour_updates(frame)
                self.select_hero_title(page)
                original = self.title_colour(frame)
                field = page.locator('#liveColorHex')
                message = page.locator('#liveColorMessage')
                field.click()
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('#123456', delay=60)    # every prefix on the way is not yet a colour
                self.assertFalse(message.is_visible(), 'no message while typing')
                page.wait_for_timeout(300)                 # proves a negative: nothing is sent per keystroke
                self.assertEqual(self.colour_updates(frame), [])
                self.assertEqual(self.title_colour(frame), original)
                page.keyboard.press('Enter')
                self.wait_style(frame, TITLE_SELECTOR, 'color', 'rgb(18, 52, 86)')
                self.assertEqual(self.colour_updates(frame), ['#123456'])
                # A half-typed value that is committed is refused, and the field goes back to the applied colour.
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('#12', delay=60)
                page.keyboard.press('Tab')
                message.wait_for(state='visible')
                self.assertIn('#12', message.inner_text())
                self.assertEqual(field.input_value(), '#123456')
                self.assertEqual(self.colour_updates(frame), ['#123456'])
                # Typing again clears the message (before anything is committed).
                field.click()
                page.keyboard.press('End')
                page.keyboard.type('x', delay=60)
                self.assertFalse(message.is_visible(), 'typing clears the message')
                # And a valid commit clears it without any typing.
                page.keyboard.press('ControlOrMeta+A')
                page.keyboard.type('#12', delay=60)
                page.keyboard.press('Tab')
                message.wait_for(state='visible')
                field.evaluate("""(el) => { el.value = '#abcdef'; el.dispatchEvent(new Event('change', { bubbles: true })); }""")
                self.wait_style(frame, TITLE_SELECTOR, 'color', 'rgb(171, 205, 239)')
                self.assertFalse(message.is_visible(), 'a valid commit clears the message')
                self.assertEqual(page.errors, [])

    def test_colour_on_an_svg_with_its_own_fills_says_the_fills_win(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.select_hero_title(page)
                self.assertEqual(page.locator('#liveColorSvgNote').count(), 0, 'text has no such note')
                self.click_in_target(page, '[data-design-id="landing.brand.mark"]', 'landing.brand.mark')
                note = page.locator('#liveColorSvgNote')
                note.wait_for(state='visible')
                self.assertRegex(note.inner_text(), r'(?i)fills')
                self.assertRegex(note.inner_text(), r'(?i)win')
                page.locator('#liveColorHex').fill('#ff0000')
                page.locator('#liveColorHex').press('Enter')
                self.wait_style(frame, '[data-design-id="landing.brand.mark"]', 'color', 'rgb(255, 0, 0)')
                # The note is true: the mark's own fill is untouched.
                self.assertEqual(frame.evaluate('getComputedStyle(document.querySelector(\'[data-design-id="landing.brand.mark"] rect\')).fill'),
                                 'rgb(20, 33, 61)')
                self.assertEqual(page.errors, [])


if __name__ == '__main__':
    unittest.main()
