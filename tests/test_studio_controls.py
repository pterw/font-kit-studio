"""A control that would do nothing says so (v0.2.1 Task 6).

Studio disables a control that has nothing to act on, puts the reason in its `title` (and in an adjacent hint
where a tooltip is easy to miss), and enables it again as soon as the state changes. Every test asserts what the
user sees: the rendered `disabled` state and the reason text, before and after the state changes.

The first groups use the deterministic fake target (tests/fixtures/studio/fake-target.html) through LiveCase. The
last group runs the real Studio against the real fontkit-bridge.js through the real scripts/serve.py, including
the one write that must never happen: Sync to file with an empty ledger over an existing overrides file.

Run one module by name with PYTHONPATH=tests:  python -m unittest test_studio_controls
"""

import base64
import re
import unittest

from support import ENGINES, HTML

from test_live_integration import CONNECTED, TITLE, LiveIntegrationCase
from test_studio_live import ARRANGE, STUDIO, TARGET, ArrangeCase, LiveCase

CONNECT_FIRST = re.compile(r'connect a page first', re.I)
NO_TEXT_EDITS = re.compile(r'nothing to restore', re.I)
NO_CHANGES_HERE = re.compile(r'no changes on this element', re.I)
LIVE_VIEW_ONLY = re.compile(r'only for the live app view', re.I)
ALREADY_LOADED = re.compile(r'already loaded', re.I)
NOTHING_TO_SAVE = re.compile(r'no changes to save yet', re.I)
ONE_CUT = re.compile(r'one cut only', re.I)
NO_IMAGE = re.compile(r'choose an image first', re.I)
POPOUT_CLOSED = re.compile(r'pop-out.*closed', re.I)
NO_DEV_SERVER = re.compile(r'dev server', re.I)
EMPTY_FILE = re.compile(r'empty overrides file', re.I)
CSS_PROMISED = r'demo/fontkit-overrides\.css'


def colour_source(name):
    return re.compile(rf'colour source is {name}', re.I)


# 1x1 PNG, so the image control has a file to take.
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
ANY_REASON = re.compile('|'.join(pattern.pattern for pattern in (
    CONNECT_FIRST, NO_TEXT_EDITS, NO_CHANGES_HERE, LIVE_VIEW_ONLY, ALREADY_LOADED, NOTHING_TO_SAVE, ONE_CUT, NO_IMAGE,
    POPOUT_CLOSED, re.compile(r'colour source is'))), re.I)


class ControlsMixin:
    """Assertions on the rendered state of one control: `disabled`, the reason in `title` and an optional hint."""

    def wait_disabled(self, page, selector, disabled, timeout=5000):
        page.wait_for_function('([selector, disabled]) => { const el = document.querySelector(selector);'
                               ' return Boolean(el) && el.disabled === disabled; }', arg=[selector, disabled], timeout=timeout)

    def assert_disabled(self, page, selector, reason, hint=None):
        self.wait_disabled(page, selector, True)
        title = page.locator(selector).get_attribute('title') or ''
        self.assertRegex(title, reason, f'{selector} is disabled without saying why')
        if hint:
            self.assertTrue(page.locator(hint).is_visible(), f'{hint} is not shown beside {selector}')
            self.assertRegex(page.locator(hint).inner_text(), reason)
            self.assertEqual(page.locator(selector).get_attribute('aria-describedby'), hint.lstrip('#'),
                             f'{selector} does not point at its hint')

    def assert_enabled(self, page, selector, hint=None, title=None):
        """Enabled, with no reason left over; `title` is the normal title the control gets back (none: no title)."""
        self.wait_disabled(page, selector, False)
        actual = page.locator(selector).get_attribute('title') or ''
        self.assertNotRegex(actual, ANY_REASON, f'{selector} is enabled but still carries a reason')
        self.assertRegex(actual, title or r'^$', f'{selector} did not get its own title back')
        if hint:
            self.assertFalse(page.locator(hint).is_visible(), f'{hint} still shows beside the enabled {selector}')
            self.assertIsNone(page.locator(selector).get_attribute('aria-describedby'), f'{selector} still points at its hint')

    def edit_size(self, page, frame, size=50, target_id='hero.title'):
        self.select(page, frame, target_id)
        self.set_value(page, '#liveFontSize', size)
        self.wait_live(page)

    def composer(self, engine, **options):
        """Studio in the Composer, nothing connected, the Specimen view showing."""
        page, errors = self.open(engine, target=None, **options)
        page.locator('#modeComposer').click()
        return page, errors

    def active(self, page):
        """Where keyboard focus is: the tag, the id and whether it is a data-live-back button."""
        return page.evaluate('''() => { const el = document.activeElement;
            return { tag: el.tagName, id: el.id, back: el.hasAttribute("data-live-back"), disabled: Boolean(el.disabled) }; }''')

    def first_slot(self, page):
        page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})


class NoTargetTests(ControlsMixin, LiveCase):
    def test_sync_to_live_app_is_disabled_until_a_page_connects_and_again_when_it_goes_away(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.assert_disabled(page, '#btnSyncToApp', CONNECT_FIRST, hint='#syncToAppHint')
                self.connect(page)
                self.wait_connected(page)
                self.assert_enabled(page, '#btnSyncToApp', hint='#syncToAppHint')
                # The page is replaced by one without a bridge: Studio is no longer connected to anything.
                self.connect(page, f'{TARGET}/no-bridge.html')
                self.assert_disabled(page, '#btnSyncToApp', CONNECT_FIRST, hint='#syncToAppHint')
                self.assertEqual(errors, [])

    def test_restore_page_text_needs_a_page_and_then_a_text_edit(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.assert_disabled(page, '#btnRestoreOriginalText', CONNECT_FIRST)
                self.connect(page)
                frame = self.frame(page)
                self.wait_connected(page)
                self.assert_disabled(page, '#btnRestoreOriginalText', NO_TEXT_EDITS)
                self.select(page, frame, 'hero.title')
                page.locator('#liveText').fill('A new headline')
                self.assert_enabled(page, '#btnRestoreOriginalText', title=r'^Restore original text in live web app$')
                page.locator('#btnRestoreOriginalText').click()
                frame.wait_for_function('window.fake.textOf("hero.title") === "Hello world"')
                self.assert_disabled(page, '#btnRestoreOriginalText', NO_TEXT_EDITS)
                self.assertEqual(errors, [])

    def test_a_style_edit_alone_leaves_restore_page_text_disabled(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.edit_size(page, frame)
                self.assert_disabled(page, '#btnRestoreOriginalText', NO_TEXT_EDITS)
                self.assertEqual(errors, [])

    def test_width_buttons_and_pointer_mode_are_for_the_live_app_view_only(self):
        buttons = ['#btnDeviceDesktop', '#btnDeviceLaptop', '#btnDeviceMobile', '#btnDeviceFluid',
                   '#bridgeModeSelect', '#bridgeModeInteract']
        titles = {'#btnDeviceDesktop': r'^Desktop \(1440px\)$', '#btnDeviceLaptop': r'^Laptop \(1024px\)$',
                  '#btnDeviceMobile': r'^Mobile \(390px\)$', '#btnDeviceFluid': r'^Fluid \(100%\)$',
                  '#bridgeModeSelect': r'^Clicks in the preview select', '#bridgeModeInteract': r'^Use the app normally'}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                for selector in buttons:
                    self.assert_disabled(page, selector, LIVE_VIEW_ONLY)
                self.connect(page)
                self.wait_connected(page)
                for selector in buttons:
                    self.assert_enabled(page, selector, title=titles[selector])
                page.locator('#viewSpecimenCanvas').click()
                for selector in buttons:
                    self.assert_disabled(page, selector, LIVE_VIEW_ONLY)
                page.locator('#viewTargetApp').click()
                for selector in buttons:
                    self.assert_enabled(page, selector, title=titles[selector])
                page.locator('#btnDeviceMobile').click()
                self.assertEqual(page.locator('#targetAppContainer').evaluate('el => el.style.width'), '390px')
                self.assertEqual(errors, [])


class ResetElementTests(ControlsMixin, LiveCase):
    def test_reset_is_disabled_until_the_selected_element_changes_and_follows_the_selection(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.set_value(page, '#liveFontSize', 50)
                self.assert_enabled(page, '#liveResetTarget')
                # Another element has nothing to reset, and the first one still has.
                self.select(page, frame, 'hero.lead')
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.select(page, frame, 'hero.title')
                self.assert_enabled(page, '#liveResetTarget')
                page.locator('#liveResetTarget').click()
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.title").fontSize'), '32px')
                self.assertEqual(errors, [])


class ChangesPanelTests(ControlsMixin, LiveCase):
    def test_sync_copy_and_download_wait_for_a_change_and_the_hint_says_why(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assert_disabled(page, '#liveCodeSync', NOTHING_TO_SAVE, hint='#liveCodeSyncHint')
                self.assert_disabled(page, '#liveCodeCopy', NOTHING_TO_SAVE)
                self.assert_disabled(page, '#liveCodeDownload', NOTHING_TO_SAVE)
                self.edit_size(page, frame)
                for selector in ('#liveCodeCopy', '#liveCodeDownload'):
                    self.assert_enabled(page, selector)
                self.assert_enabled(page, '#liveCodeSync', hint='#liveCodeSyncHint', title=r'demo/fontkit-overrides\.css')
                self.assertIn('font-size: 50px !important;', self.sync_file(page))
                # Resetting the element empties the ledger again. Studio held a saved state this session, so the file
                # may still hold it: Sync to file stays on, says it writes an empty file, and does.
                page.locator('#liveResetTarget').click()
                self.wait_disabled(page, '#liveResetTarget', True)          # the page has acknowledged the reset
                self.assert_enabled(page, '#liveCodeSync', hint='#liveCodeSyncHint', title=EMPTY_FILE)
                self.assert_disabled(page, '#liveCodeCopy', NOTHING_TO_SAVE)
                self.assert_disabled(page, '#liveCodeDownload', NOTHING_TO_SAVE)
                body = self.sync_file(page)
                self.assertIn('No live style overrides yet', body)
                self.assertNotIn('font-size', body)
                self.assertEqual(errors, [])

    def test_a_fresh_session_never_writes_when_auto_sync_is_switched_on(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                page.wait_for_function('() => !document.querySelector("#liveCodeAutoSync").disabled')
                page.locator('#liveCodeAutoSync').check()
                page.wait_for_function('() => /no changes to save yet/i.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertEqual(self.puts, [])
                self.assertEqual(errors, [])

    def test_without_a_dev_server_sync_to_file_says_so_but_copy_and_download_work(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)   # no /__fontkit/ routes: the status request 404s
                self.wait_connected(page)
                frame = self.frame(page)
                self.assert_disabled(page, '#liveCodeSync', NO_DEV_SERVER, hint='#liveCodeSyncHint')
                self.edit_size(page, frame)
                self.assert_disabled(page, '#liveCodeSync', NO_DEV_SERVER, hint='#liveCodeSyncHint')
                self.assert_enabled(page, '#liveCodeCopy')
                self.assert_enabled(page, '#liveCodeDownload')
                self.assertEqual(errors, [])


class PopoutTests(ControlsMixin, LiveCase):
    def test_focus_pop_out_needs_an_open_window(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                self.assert_disabled(page, '#bridgeFocusPopout', POPOUT_CLOSED)
                with page.expect_popup() as info:
                    page.locator('#bridgePopOut').click()
                popup = info.value
                popup.wait_for_function('Boolean(window.fake)')
                self.wait_badge(page, r'^Connected \(5 targets\)$')
                self.assert_enabled(page, '#bridgeFocusPopout')
                popup.close()
                self.wait_badge(page, r'^Disconnected \(window closed\)$', timeout=6000)
                self.assert_disabled(page, '#bridgeFocusPopout', POPOUT_CLOSED)
                self.assertTrue(page.locator('#bridgePopoutPlaceholder').is_visible())
                self.assertEqual(errors, [])


class FreeFontTests(ControlsMixin, LiveCase):
    LOAD = ('#loadFreeFontsLibrary', '#loadFreeFonts')
    TITLES = {'#loadFreeFontsLibrary': None, '#loadFreeFonts': r'^Load every free Google Fonts family'}

    def stylesheets(self, page):
        return page.evaluate('() => [...document.querySelectorAll("link[data-studio-font]")].map(link => link.dataset.state)')

    def test_load_free_fonts_is_disabled_once_every_family_has_loaded(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                context.route('https://fonts.googleapis.com/**',
                              lambda route: route.fulfill(status=200, content_type='text/css', body='/* offline */'))
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{STUDIO}/{HTML.name}')
                for selector in self.LOAD:
                    self.assert_enabled(page, selector, title=self.TITLES[selector])
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font][data-state=loaded]").length === 16')
                for selector in self.LOAD:
                    self.assert_disabled(page, selector, ALREADY_LOADED)
                self.assertEqual(errors, [])

    def test_a_failed_load_leaves_the_button_enabled_to_try_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None)   # every https request is aborted here
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font][data-state=error]").length === 16')
                for selector in self.LOAD:
                    self.assert_enabled(page, selector, title=self.TITLES[selector])
                self.assertEqual(errors, [])


class ColourSourceTests(ControlsMixin, LiveCase):
    def assert_fields(self, page, enabled, others, source):
        for selector in enabled:
            self.assert_enabled(page, selector)
        for selector in others:
            self.assert_disabled(page, selector, colour_source(source))

    def test_the_canvas_colour_fields_follow_the_chosen_source(self):
        fields = {'custom': '#canvasBgHex', 'tailwind': '#canvasBgFamily, #canvasBgShade', 'saved': '#canvasSavedColor'}
        names = {'custom': 'Custom hex', 'tailwind': 'Tailwind', 'saved': 'Saved palette'}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                for source in ('custom', 'tailwind', 'saved', 'custom'):
                    page.locator('#canvasBgSource').select_option(source)
                    live = [s.strip() for s in fields[source].split(',')]
                    dead = [s.strip() for other, value in fields.items() if other != source for s in value.split(',')]
                    self.assert_fields(page, live, dead, names[source])
                self.assertEqual(errors, [])

    def test_an_imported_source_updates_the_canvas_colour_fields(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                document = self.export(page)
                document['composition']['background']['source'] = 'saved'
                self.import_document(page, document)
                self.assert_fields(page, ['#canvasSavedColor'], ['#canvasBgHex', '#canvasBgFamily', '#canvasBgShade'], 'Saved palette')
                self.assertEqual(errors, [])

    def test_each_slot_colour_field_follows_that_slots_source(self):
        binds = {'custom': 'colorHex', 'tailwind': 'colorFamily, colorShade', 'saved': 'savedColor'}
        names = {'custom': 'Custom hex', 'tailwind': 'Tailwind', 'saved': 'Saved palette'}

        def field(bind):
            return f'#slotInspector [data-bind="{bind.strip()}"]'

        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.first_slot(page)
                for source in ('custom', 'tailwind', 'saved', 'custom'):
                    page.locator('#slotInspector [data-bind="colorSource"]').select_option(source)
                    for chosen, value in binds.items():
                        for bind in value.split(','):
                            if chosen == source:
                                self.assert_enabled(page, field(bind))
                            else:
                                self.assert_disabled(page, field(bind), colour_source(names[source]))
                # Selecting another slot shows that slot's own state, not the previous one's.
                page.locator('#composerCanvas > .flow-slot').nth(1).click(position={'x': 3, 'y': 3})
                self.assert_enabled(page, field('colorHex'))
                self.assert_disabled(page, field('savedColor'), colour_source('Custom hex'))
                self.assertEqual(errors, [])


class SlotInspectorTests(ControlsMixin, LiveCase):
    def test_style_cut_is_disabled_for_a_family_with_one_cut(self):
        cut = '#slotInspector [data-bind="styleIndex"]'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.first_slot(page)
                page.locator('#slotInspector [data-bind="family"]').select_option('inter')
                self.assert_disabled(page, cut, ONE_CUT)
                page.locator('#slotInspector [data-bind="family"]').select_option('fraunces')
                self.assert_enabled(page, cut)
                self.assertEqual(errors, [])

    def test_image_width_waits_for_an_image(self):
        width = '#slotInspector [data-bind="imageWidth"]'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.composer(engine)
                self.first_slot(page)
                page.locator('#slotInspector [data-bind="type"]').select_option('image')
                self.assert_disabled(page, width, NO_IMAGE)
                page.locator('#assetFile').set_input_files({'name': 'mark.png', 'mimeType': 'image/png', 'buffer': PNG})
                self.assert_enabled(page, width)
                # Another slot type has no width control at all, and coming back to the image keeps it enabled.
                page.locator('#composerCanvas > .flow-slot').nth(1).click(position={'x': 3, 'y': 3})
                self.first_slot(page)
                self.assert_enabled(page, width)
                self.assertEqual(errors, [])


class RealBridgeControlTests(ControlsMixin, LiveIntegrationCase):
    """Real Studio, real bridge, real dev server: the states follow what the real page acknowledged."""

    def test_restore_page_text_and_reset_follow_real_edits(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                original = frame.locator(TITLE).text_content().strip()
                self.assert_disabled(page, '#btnRestoreOriginalText', NO_TEXT_EDITS)
                self.select_hero_title(page)
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.type_into(page, '#liveText', 'Typed into the real page')
                self.wait_text(frame, TITLE, 'Typed into the real page')
                self.assert_enabled(page, '#btnRestoreOriginalText', title=r'^Restore original text in live web app$')
                self.assert_enabled(page, '#liveResetTarget')
                page.locator('#btnRestoreOriginalText').click()
                self.wait_text(frame, TITLE, original)
                self.assert_disabled(page, '#btnRestoreOriginalText', NO_TEXT_EDITS)
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.assertEqual(page.errors, [])

    def test_sync_to_file_follows_the_real_ledger_and_writes_what_it_holds(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                self.assert_disabled(page, '#liveCodeSync', NOTHING_TO_SAVE, hint='#liveCodeSyncHint')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '52')
                self.assert_enabled(page, '#liveCodeSync', hint='#liveCodeSyncHint', title=r'overrides\.css')
                self.sync(page)
                self.assertIn('font-size: 52px !important;', self.written())
                self.assertEqual(page.errors, [])

    def test_sync_to_file_with_an_empty_ledger_leaves_an_existing_file_byte_for_byte(self):
        original = b'/* written by hand */\r\n.keep-me { color: red; }\n\xe2\x9c\x93\n'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.write_bytes(original)
                page = self.connected(engine)
                self.assert_disabled(page, '#liveCodeSync', NOTHING_TO_SAVE)
                # Whatever re-enables the button (a stale page, a script), the write itself refuses.
                page.locator('#liveCodeSync').evaluate('(button) => { button.disabled = false; button.click(); }')
                page.wait_for_function('() => /no changes to save yet/i.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertEqual(self.overrides.read_bytes(), original)
                self.assertEqual(page.errors, [])

    def reload_and_wait(self, page):
        """Reloads the demo and waits for the new document to be connected (no conflict, so no banner to wait for)."""
        frame = self.frame(page)
        frame.evaluate('window.__before_reload = true; location.reload()')
        frame = self.frame(page)
        frame.wait_for_function('!window.__before_reload && document.readyState === "complete"')
        self.wait_badge(page, CONNECTED)
        return frame

    def test_auto_sync_writes_the_empty_file_after_the_user_resets_the_last_change(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                base = self.style(self.frame(page), TITLE, 'fontSize')
                page.locator('#liveCodeAutoSync').check()
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '52')
                self.wait_file('font-size: 52px')
                page.locator('#liveResetTarget').click()
                self.wait_file('No live style overrides yet')
                self.assertNotIn('font-size: 52px', self.written())
                # The page that loads next shows its own size: the file no longer carries the edit.
                frame = self.reload_and_wait(page)
                self.wait_style(frame, TITLE, 'fontSize', base)
                self.assertEqual(page.errors, [])

    def test_sync_to_file_clears_the_file_after_the_user_resets_the_last_change(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                base = self.style(self.frame(page), TITLE, 'fontSize')
                self.select_hero_title(page)
                self.type_into(page, '#liveFontSize', '52')
                self.sync(page)
                self.assertIn('font-size: 52px', self.written())
                page.locator('#liveResetTarget').click()
                self.wait_disabled(page, '#liveResetTarget', True)          # the page has acknowledged the reset
                self.assert_enabled(page, '#liveCodeSync', hint='#liveCodeSyncHint', title=EMPTY_FILE)
                page.locator('#liveCodeSync').click()
                self.wait_file('No live style overrides yet')
                self.assertNotIn('font-size: 52px', self.written())
                frame = self.reload_and_wait(page)
                self.wait_style(frame, TITLE, 'fontSize', base)
                self.assertEqual(page.errors, [])

    def test_a_fresh_session_refuses_auto_sync_over_an_existing_file(self):
        original = b'/* written by hand */\n.keep-me { color: red; }\n'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.overrides.write_bytes(original)
                page = self.connected(engine)
                page.wait_for_function('() => !document.querySelector("#liveCodeAutoSync").disabled')
                page.locator('#liveCodeAutoSync').check()
                page.wait_for_function('() => /no changes to save yet/i.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertEqual(self.overrides.read_bytes(), original)
                self.assertEqual(page.errors, [])


class SavedStateKindTests(ControlsMixin, ArrangeCase):
    """Every kind of saved state, alone, is something to save; and the page's own ledger is something to copy."""

    def moved_page(self, engine):
        page, errors = self.open(engine, target=ARRANGE, sync=True)
        frame = self.wait_ready(page, 11)
        self.select(page, frame, 'card.c')
        page.locator('#liveMoveFirst').click()       # a DOM move: no CSS, no override, only the container's order
        self.wait_badge(page, r'^Live · rev 1$')
        return page, errors, frame

    def test_saved_composition_tokens_alone_enable_sync_to_file(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                self.assert_disabled(page, '#liveCodeSync', NOTHING_TO_SAVE)
                page.locator('#btnSyncToApp').click()
                self.wait_live(page)
                self.assert_enabled(page, '#liveCodeSync', title=CSS_PROMISED)
                self.assert_enabled(page, '#liveCodeCopy')
                self.assertIn('--font-display', self.sync_file(page))
                self.assertEqual(errors, [])

    def test_a_saved_dom_move_alone_enables_sync_copy_and_download(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.moved_page(engine)
                self.assert_enabled(page, '#liveCodeSync', title=CSS_PROMISED)
                self.assert_enabled(page, '#liveCodeCopy')
                self.assert_enabled(page, '#liveCodeDownload')
                self.assertEqual(errors, [])

    def test_reset_follows_a_dom_move_of_that_element_only(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.moved_page(engine)
                self.assert_enabled(page, '#liveResetTarget')
                self.select(page, frame, 'side.x')
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.assertEqual(errors, [])

    def test_the_pages_own_ledger_alone_enables_reset_copy_and_download(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=ARRANGE, sync=True)
                frame = self.wait_ready(page, 11)
                before = self.export(page)
                self.edit_size(page, frame)                       # the page now holds an edit of the hero title
                # An import replaces Studio's saved overrides with the file's: one for another element the page does not hold.
                self.import_document(page, {**before, 'live': {'target': ARRANGE, 'revision': 1,
                                                               'overrides': {'stat.badge': {'fontSize': 30}}}})
                self.select(page, frame, 'hero.title')
                self.assertNotIn('hero.title', self.export(page)['live']['overrides'])
                self.assert_enabled(page, '#liveResetTarget')     # only the page's ledger says this element has a change
                # Resetting the saved one empties Studio's saved state; the page's ledger still holds the hero title.
                self.select(page, frame, 'stat.badge')
                self.assert_enabled(page, '#liveResetTarget')
                page.locator('#liveResetTarget').click()
                self.wait_disabled(page, '#liveResetTarget', True)
                self.assertNotIn('live', self.export(page))
                self.assert_enabled(page, '#liveCodeCopy')
                self.assert_enabled(page, '#liveCodeDownload')
                self.assertEqual(errors, [])


class RebuiltInspectorTests(ControlsMixin, LiveCase):
    def test_reset_stays_disabled_when_the_inspector_is_rebuilt_by_a_view_switch(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#viewTargetApp').click()
                page.wait_for_selector('#liveTargetName')
                self.assert_disabled(page, '#liveResetTarget', NO_CHANGES_HERE)
                self.assertEqual(errors, [])


class KeyboardFocusTests(ControlsMixin, LiveCase):
    """A control that disables itself after a keyboard press hands focus to a neighbour, not to the page."""

    def fonts_page(self, engine):
        context = self.context(engine)
        context.route('https://fonts.googleapis.com/**',
                      lambda route: route.fulfill(status=200, content_type='text/css', body='/* offline */'))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{STUDIO}/{HTML.name}')
        return page, errors

    def assert_focus_stays(self, page, panel):
        now = self.active(page)
        self.assertNotEqual(now['tag'], 'BODY', 'focus fell to the page')
        self.assertFalse(now['disabled'])
        self.assertTrue(page.evaluate('(panel) => Boolean(document.activeElement.closest(panel))', panel), (now, panel))
        page.keyboard.press('Shift+Tab')              # and the keyboard goes on from there
        self.assertNotEqual(self.active(page)['tag'], 'BODY')

    def test_reset_hands_focus_to_all_targets(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.edit_size(page, frame)
                page.locator('#liveFontSize').focus()
                for _ in range(60):                    # Tab to the button the way a keyboard user does (the arrange panel is in the way)
                    page.keyboard.press('Tab')
                    if self.active(page)['id'] == 'liveResetTarget':
                        break
                self.assertEqual(self.active(page)['id'], 'liveResetTarget')
                page.keyboard.press('Enter')
                self.wait_disabled(page, '#liveResetTarget', True)
                self.assertTrue(self.active(page)['back'], self.active(page))
                self.assert_focus_stays(page, '#slotInspector')
                self.assertEqual(errors, [])

    def test_restore_page_text_hands_focus_to_a_neighbour_in_the_bridge_bar(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.select(page, frame, 'hero.title')
                page.locator('#liveText').fill('A new headline')
                self.assert_enabled(page, '#btnRestoreOriginalText', title=r'^Restore original text')
                page.locator('#btnRestoreOriginalText').focus()
                page.keyboard.press('Enter')
                self.wait_disabled(page, '#btnRestoreOriginalText', True)
                self.assert_focus_stays(page, '#targetAppBridgeBar')
                self.assertEqual(errors, [])

    def test_load_free_fonts_hands_focus_to_a_neighbour_in_its_panel(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.fonts_page(engine)
                page.locator('#loadFreeFontsLibrary').focus()
                page.keyboard.press('Enter')
                self.wait_disabled(page, '#loadFreeFontsLibrary', True)
                self.assert_focus_stays(page, '.controls')
                self.assertEqual(errors, [])

    def test_the_composer_load_free_fonts_hands_focus_to_a_neighbour_in_its_panel(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.fonts_page(engine)
                page.locator('#modeComposer').click()
                page.locator('#loadFreeFonts').focus()
                page.keyboard.press('Enter')
                self.wait_disabled(page, '#loadFreeFonts', True)
                self.assert_focus_stays(page, '.composer-toolbar')
                self.assertEqual(errors, [])


class LoadingFamilyTests(ControlsMixin, LiveCase):
    def test_load_free_fonts_stays_enabled_while_one_family_is_still_loading(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                context = self.context(engine)
                held = []

                def fonts(route):
                    if 'Bebas' in route.request.url:
                        held.append(route)              # this family has not answered yet
                    else:
                        route.fulfill(status=200, content_type='text/css', body='/* offline */')

                context.route('https://fonts.googleapis.com/**', fonts)
                page = context.new_page()
                page.goto(f'{STUDIO}/{HTML.name}')
                page.locator('#loadFreeFontsLibrary').click()
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font][data-state=loaded]").length === 15')
                self.assertEqual(len(held), 1)
                for selector, title in (('#loadFreeFontsLibrary', None), ('#loadFreeFonts', r'^Load every free Google Fonts family')):
                    self.assert_enabled(page, selector, title=title)
                held[0].fulfill(status=200, content_type='text/css', body='/* offline */')
                page.wait_for_function('() => document.querySelectorAll("link[data-studio-font][data-state=loaded]").length === 16')
                for selector in ('#loadFreeFontsLibrary', '#loadFreeFonts'):
                    self.assert_disabled(page, selector, ALREADY_LOADED)


if __name__ == '__main__':
    unittest.main()
