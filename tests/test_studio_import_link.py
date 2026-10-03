"""Importing a composition while it is linked to the page (v0.2.1 Task 5, D035).

An import is the user's latest explicit state. While the composition is linked (the user pressed Sync to Live
App and Studio streams composition edits), the import must end the link, keep the imported tokens as the saved
state whatever the page acknowledges next, say so, and show the reconnect banner when the page differs.

The first group uses the deterministic fake target (tests/fixtures/studio/fake-target.html), which can hold its
acknowledgements back so a request is still in flight when the import happens. The last group runs the real
Studio against the real fontkit-bridge.js through the real scripts/serve.py.

Run one module by name with PYTHONPATH=tests:  python -m unittest tests.test_studio_import_link
"""

import copy
import unittest

from support import ENGINES

from test_live_integration import LiveIntegrationCase
from test_studio_live import ARRANGE, FAKE, ArrangeCase, LiveCase

STATUS = 'Imported; the link to the page is off. Press Sync to Live App to send this composition.'
HEADING = 'Imported state differs from the target.'
COMPOSITION_UPDATES = ('window.__received.filter(item => item.data && item.data.type === "design:update"'
                       ' && !("targetId" in item.data))')


class ImportLinkCase(LiveCase):
    def composition_updates(self, frame):
        return [update for update in self.updates(frame) if 'targetId' not in update]

    def wait_composition_updates(self, frame, count):
        frame.wait_for_function(f'{COMPOSITION_UPDATES}.length === {count}')

    def sync(self, page):
        page.locator('#btnSyncToApp').click()
        self.wait_live(page)

    def linked_page(self, engine, **options):
        """Studio connected to the fake target and synced: the composition is linked, the page holds its tokens."""
        page, errors = self.open(engine, **options)
        self.wait_connected(page)
        frame = self.frame(page)
        self.sync(page)
        self.assertEqual(len(self.composition_updates(frame)), 1)
        return page, frame, errors

    def blank_document(self, engine):
        """A composition export from a separate, never-linked Studio, with no `live` field. Its display token is
        Inter (the default composition and Asteria use Fraunces) and its mono token IBM Plex Mono (Asteria uses
        JetBrains Mono). Both come from roles (Wordmark falls back to the first slot; Metadata matches "data"),
        so they do not depend on the rule that picks the serif token."""
        page, _ = self.open(engine, query=False)
        page.locator('#modeComposer').click()
        page.locator('#compositionPreset').select_option('blank')
        page.locator('#applyPreset').click()
        document = self.export(page)
        self.assertNotIn('live', document)
        return document

    def with_live_tokens(self, document):
        """The same file the way Studio exports it after a sync: the saved tokens ride in `live`."""
        document = copy.deepcopy(document)
        document['live'] = {'target': '', 'revision': 0, 'overrides': {},
                            'tokens': {'--font-display': '"Inter", sans-serif', '--font-mono': '"IBM Plex Mono", monospace'}}
        return document

    def page_tokens(self, frame):
        return frame.evaluate('window.fake.ledger().tokens')

    def banner_heading(self, page):
        return page.locator('#liveReconnectHeading').inner_text()


class ImportWhileLinkedTests(ImportLinkCase):
    def check_late_ack_keeps_the_imported_tokens(self, engine, with_live_field):
        page, frame, errors = self.linked_page(engine)
        document = self.blank_document(engine)
        if with_live_field:
            document = self.with_live_tokens(document)
        # A linked edit is still in flight (its acknowledgement is held) when the user imports.
        frame.evaluate('window.fake.hold = true')
        page.locator('#compositionPreset').select_option('asteria')
        page.locator('#applyPreset').click()
        self.wait_composition_updates(frame, 2)
        before_import = self.page_tokens(frame)
        self.assertIn('"Fraunces"', before_import['--font-display'])
        self.assertIn('"JetBrains Mono"', before_import['--font-mono'])

        status = self.import_document(page, document)
        self.assertEqual(status, STATUS)
        # The import sent nothing (it is the user's state, not a stream), and the page still holds its own tokens.
        self.assertEqual(self.page_tokens(frame), before_import)
        self.watch_handled(page)
        frame.evaluate('window.fake.release()')
        self.wait_handled(page, 1)
        page.wait_for_timeout(300)     # absence window: a stray send of the imported composition would arrive in it
        self.assertEqual(len(self.composition_updates(frame)), 2, 'the import sent nothing to the page')

        # The late acknowledgement carried the page's tokens; the imported ones are still the saved state.
        css = self.code(page, 'Css')
        self.assertIn('--font-display: "Inter"', css)
        self.assertIn('--font-mono: "IBM Plex Mono"', css)
        self.assertNotIn('JetBrains', css)
        self.assertNotIn('Fraunces', css)
        saved = self.export(page)['live']['tokens']
        self.assertTrue(saved['--font-display'].startswith('"Inter"'), saved)
        self.assertTrue(saved['--font-mono'].startswith('"IBM Plex Mono"'), saved)
        self.assertEqual(page.locator('#composerStatus').inner_text(), STATUS)
        # The page differs from what was imported: the banner offers the choice instead of replacing either side.
        self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
        self.assertEqual(self.banner_heading(page), HEADING)
        text = page.locator('#liveReconnectText').inner_text()
        self.assertIn('Reapply', text)
        self.assertIn('Accept target state', text)
        self.assertEqual(self.page_tokens(frame), before_import, 'nothing was applied to the page behind the user')
        self.assertEqual(errors, [])

    def test_a_late_ack_after_an_import_keeps_the_imported_tokens_and_raises_the_import_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_late_ack_keeps_the_imported_tokens(engine, with_live_field=False)

    def test_a_late_ack_after_an_import_with_saved_tokens_keeps_them_too(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_late_ack_keeps_the_imported_tokens(engine, with_live_field=True)

    def test_no_banner_when_the_page_already_holds_the_imported_tokens(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                sent = 1
                for with_live_field in (False, True):
                    # The file Studio itself exported while linked: the page holds exactly its tokens.
                    document = self.export(page)
                    document['composition']['canvasWidth'] = '720'
                    if not with_live_field:
                        del document['live']
                    status = self.import_document(page, document)
                    self.assertEqual(status, STATUS)
                    page.wait_for_timeout(200)     # absence window: the banner and a send would show within it
                    self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), with_live_field)
                    self.assertEqual(len(self.composition_updates(frame)), sent, 'the import sent nothing')
                    self.assertEqual(self.export(page)['live']['tokens'], self.page_tokens(frame))
                    # Press Sync to link again for the next round; the page already holds these tokens.
                    self.sync(page)
                    sent += 1
                    self.wait_composition_updates(frame, sent)
                    self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_reapply_from_the_import_banner_sends_the_imported_tokens(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertEqual(self.banner_heading(page), HEADING)
                self.assertIn('"Fraunces"', self.page_tokens(frame)['--font-display'])
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.ledger().tokens["--font-display"].startsWith(\'"Inter"\')')
                self.assertEqual(self.export(page)['live']['tokens'], self.page_tokens(frame))
                # Reapply sends the saved tokens (and saved overrides and DOM order); slots and text go with Sync.
                self.assertEqual(list(self.composition_updates(frame)[-1]['patch']), ['tokens'])
                self.assertEqual(errors, [])

    def test_accept_target_state_from_the_import_banner_takes_the_pages_tokens(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                page_tokens = self.page_tokens(frame)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(self.export(page)['live']['tokens'], page_tokens)
                self.assertEqual(self.page_tokens(frame), page_tokens)
                self.assertEqual(errors, [])

    def test_sync_after_an_import_relinks_and_sends_the_imported_composition(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertEqual(len(self.composition_updates(frame)), 1)
                self.sync(page)
                self.wait_composition_updates(frame, 2)
                update = self.composition_updates(frame)[-1]
                self.assertTrue(update['patch']['tokens']['--font-display'].startswith('"Inter"'), update['patch']['tokens'])
                self.assertEqual(len(update['patch']['slots']), 5)
                self.assertNotIn('fontStylesheets', update['patch'], 'no ask for free fonts yet: no stylesheets (D031/D032)')
                frame.wait_for_function('window.fake.ledger().tokens["--font-display"].startsWith(\'"Inter"\')')
                # The page now holds what was imported: the conflict is over.
                banner.wait_for(state='hidden')
                # Linked again: the next composition edit streams.
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.wait_composition_updates(frame, 3)
                self.assertEqual(errors, [])

    def test_sync_after_an_import_sends_the_complete_stylesheet_set_once_free_fonts_were_asked_for(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                page.locator('#loadFreeFonts').click()
                frame.wait_for_function('window.fake.ledger().imports.length > 0')
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                self.assertEqual(len([u for u in self.composition_updates(frame)]), 2, 'the consent re-sent once; the import sent nothing')
                self.sync(page)
                self.wait_composition_updates(frame, 3)
                sheets = self.composition_updates(frame)[-1]['patch']['fontStylesheets']
                families = [url.split('family=')[1].split(':')[0].split('&')[0] for url in sheets]
                # Blank preset slots in order: Inter, Instrument Serif, Source Serif 4, Inter, IBM Plex Mono.
                self.assertEqual(families, ['Inter', 'Instrument+Serif', 'Source+Serif+4', 'IBM+Plex+Mono'])
                self.assertEqual(frame.evaluate('window.fake.ledger().imports'), sheets)
                self.assertEqual(errors, [])


    def import_b(self, page, document, status=STATUS, names=('--font-display',)):
        """A second import, with its own saved tokens (Georgia for the named tokens)."""
        document = self.with_live_tokens(document)
        document['live']['tokens'] = {name: 'Georgia, serif' for name in names}
        self.assertIn(status, self.import_document(page, document))

    def assert_b_is_saved(self, page, frame, count, names=('--font-display',)):
        """Whatever the page acknowledged after the import, B's tokens are the saved state and the banner is up."""
        css = self.code(page, 'Css')
        self.assertIn('--font-display: Georgia, serif', css)
        self.assertNotIn('Inter', css)
        self.assertNotIn('Fraunces', css)
        self.assertNotIn('JetBrains', css)
        self.assertEqual(self.export(page)['live']['tokens'], {name: 'Georgia, serif' for name in names})
        self.assertEqual(len(self.composition_updates(frame)), count, 'nothing was sent after the import')
        self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
        self.assertEqual(self.banner_heading(page), HEADING)
        self.assertNotIn('Reapply stopped', page.locator('#liveReconnectText').inner_text())

    def release_held(self, page, frame):
        self.watch_handled(page)
        frame.evaluate('window.fake.hold = false')
        frame.evaluate('window.fake.release()')
        self.wait_handled(page, 1)
        page.wait_for_timeout(300)     # absence window: a stray send or a late adoption would show within it

    def test_a_reapply_running_at_import_time_does_not_replay_the_old_state(self):
        """Import A, Sync (its reply held), Reapply (queued behind it), import B: the Reapply was built from A and
        must not reach the page or replace B's saved tokens."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame.evaluate('window.fake.hold = true')
                page.locator('#btnSyncToApp').click()
                self.wait_composition_updates(frame, 2)
                page.locator('#liveReapply').click()          # queued behind the held Sync
                self.import_b(page, self.blank_document(engine))
                self.release_held(page, frame)
                self.assert_b_is_saved(page, frame, 2)
                self.assertEqual(errors, [])

    def test_a_reapply_in_flight_at_import_time_does_not_replace_the_imported_tokens(self):
        """The Reapply step already sent (its reply held) was built from the old state; its reply must not become
        the saved state. The composition is not linked here, so the second import says what it always said."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                # The import B saves the same token names the Reapply sends: the reply would be adopted as saved state.
                names = tuple(self.export(page)['live']['tokens'])
                frame.evaluate('window.fake.hold = true')
                page.locator('#liveReapply').click()          # the tokens step is sent and its reply held
                self.wait_composition_updates(frame, 2)
                self.import_b(page, self.blank_document(engine), status='Composition imported.', names=names)
                self.release_held(page, frame)
                self.assert_b_is_saved(page, frame, 2, names)
                self.assertEqual(errors, [])

    def test_a_reply_after_a_timeout_and_an_import_keeps_the_imported_tokens(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                frame.evaluate('window.fake.hold = true')
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.wait_composition_updates(frame, 2)
                self.wait_badge(page, r'^No response from target$', timeout=15000)    # the request timed out
                self.import_b(page, self.blank_document(engine))
                self.release_held(page, frame)       # the late reply of the superseded request
                self.assert_b_is_saved(page, frame, 2)
                self.assertEqual(errors, [])

    def test_a_queued_composition_edit_is_dropped_by_an_import_and_leaves_nothing_stale(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                frame.evaluate('window.fake.hold = true')
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.wait_composition_updates(frame, 2)
                page.locator('#compositionPreset').select_option('rowdemo')
                page.locator('#applyPreset').click()          # queued behind the held request
                page.wait_for_timeout(200)
                self.assertEqual(len(self.composition_updates(frame)), 2)
                self.import_b(page, self.blank_document(engine))
                self.release_held(page, frame)
                self.assert_b_is_saved(page, frame, 2)
                self.assertEqual(page.locator('#composerStatus').inner_text(), STATUS)
                self.assertEqual(errors, [])

    def saved_edit_dropped_by_import(self, engine):
        """The user's own acknowledged edit (hero.lead at 21px) is saved; the imported file has no overrides."""
        page, frame, errors = self.linked_page(engine)
        self.select(page, frame, 'hero.lead')
        self.set_value(page, '#liveFontSize', 21)
        frame.wait_for_function('window.fake.styleOf("hero.lead").fontSize === "21px"')
        self.wait_badge(page, r'^Live · rev 2$')      # the edit is acknowledged, so it is saved
        document = self.export(page)
        self.assertEqual(document['live']['overrides'], {'hero.lead': {'fontSize': 21}})
        document['live']['overrides'] = {}
        self.assertEqual(self.import_document(page, document), STATUS)
        return page, frame, errors

    def test_an_import_that_drops_a_saved_edit_the_page_still_holds_raises_the_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.saved_edit_dropped_by_import(engine)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertEqual(self.banner_heading(page), HEADING)
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.lead").fontSize'), '21px', 'the import changed nothing')
                self.assertEqual(self.export(page)['live']['overrides'], {})
                # Reapply puts the page back to what Studio saved: the edit goes.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('window.fake.styleOf("hero.lead").fontSize !== "21px"')
                self.assertEqual(self.export(page)['live']['overrides'], {})
                self.assertEqual(errors, [])

    def test_sync_after_an_import_that_dropped_a_saved_edit_ends_the_conflict(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.saved_edit_dropped_by_import(engine)
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.sync(page)
                banner.wait_for(state='hidden')
                self.assertEqual(errors, [])


class SupersededRejectionTests(ImportLinkCase):
    """A request sent before an import (a composition edit or a Reapply step) is superseded by it. If the page rejects
    it with a revision conflict after the import, Studio must not send it again: that would restyle the page with a
    state the user just replaced, without any action by the user (Rule 6). The rejection only redoes the comparison."""

    def hold_a_rejection(self, frame):
        """The next request is rejected with a revision conflict, and the rejection stays held until released."""
        frame.evaluate('window.fake.hold = true')
        frame.evaluate('window.fake.conflictAlways = true')

    def after_the_request_was_rejected(self, frame, count):
        """The fake has produced (and is holding) its rejection; a retry, if Studio made one, would be applied."""
        self.wait_composition_updates(frame, count)
        frame.evaluate('window.fake.conflictAlways = false')

    def assert_nothing_was_resent(self, page, frame, before, count, names=('--font-display',)):
        self.assertEqual(self.page_tokens(frame), before, 'the page keeps what it rendered')
        self.assert_b_is_saved(page, frame, count, names)
        self.assertNotIn('Rejected', page.locator('#bridgeStatusBadge').inner_text(), 'the superseded request is not reported')

    import_b = ImportWhileLinkedTests.import_b
    assert_b_is_saved = ImportWhileLinkedTests.assert_b_is_saved
    release_held = ImportWhileLinkedTests.release_held

    def test_a_reapply_step_rejected_with_a_conflict_after_an_import_is_not_sent_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.assertEqual(self.import_document(page, self.blank_document(engine)), STATUS)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                names = tuple(self.export(page)['live']['tokens'])
                before = self.page_tokens(frame)
                self.hold_a_rejection(frame)
                page.locator('#liveReapply').click()          # the tokens step is sent; its rejection is held
                self.after_the_request_was_rejected(frame, 2)
                self.import_b(page, self.blank_document(engine), status='Composition imported.', names=names)
                self.release_held(page, frame)
                self.assert_nothing_was_resent(page, frame, before, 2, names)
                self.assertEqual(errors, [])

    def test_a_composition_edit_rejected_with_a_conflict_after_an_import_is_not_sent_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                before = self.page_tokens(frame)
                self.hold_a_rejection(frame)
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.after_the_request_was_rejected(frame, 2)
                self.import_b(page, self.blank_document(engine))
                self.release_held(page, frame)
                self.assert_nothing_was_resent(page, frame, before, 2)
                self.assertEqual(errors, [])

    def test_a_rejection_after_a_timeout_and_an_import_is_not_reported_or_sent_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                before = self.page_tokens(frame)
                self.hold_a_rejection(frame)
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.after_the_request_was_rejected(frame, 2)
                self.wait_badge(page, r'^No response from target$', timeout=15000)    # the request timed out
                self.import_b(page, self.blank_document(engine))
                self.release_held(page, frame)       # the late rejection of the superseded request
                self.assert_nothing_was_resent(page, frame, before, 2)
                self.assertEqual(errors, [])

    def test_a_request_rejected_with_a_conflict_without_an_import_is_still_sent_again_once(self):
        """Characterization: the one retry of an ordinary request stays."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.hold_a_rejection(frame)
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.after_the_request_was_rejected(frame, 2)
                self.release_held(page, frame)
                self.wait_composition_updates(frame, 3)
                self.assertIn('"Fraunces"', self.page_tokens(frame)['--font-display'], 'the retry was applied')
                self.assertEqual(errors, [])


class ImportedTextWhitespaceTests(ImportLinkCase):
    """The bridge ledger reports text trimmed; Studio's saved override keeps what the user typed. The import comparison
    has to treat "Changed lead  " and "Changed lead" as the same text (as the reconnect comparison already does), or
    it raises a conflict that is not one, and misses a saved edit the page still holds."""
    TYPED = 'Changed lead  '

    def saved_text_edit(self, engine):
        page, frame, errors = self.linked_page(engine)
        self.select(page, frame, 'hero.lead')
        page.locator('#liveText').fill(self.TYPED)
        frame.wait_for_function('window.fake.ledger().targets.some(t => t.targetId === "hero.lead" && t.text === "Changed lead")')
        self.wait_badge(page, r'^Live · rev 2$')      # acknowledged, so saved
        document = self.export(page)
        self.assertEqual(document['live']['overrides'], {'hero.lead': {'text': self.TYPED}}, 'Studio keeps the whitespace')
        return page, frame, errors, document

    def test_importing_the_same_file_after_a_text_edit_with_trailing_spaces_shows_no_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.saved_text_edit(engine)
                self.assertEqual(self.import_document(page, document), STATUS)
                page.wait_for_timeout(300)     # absence window: a false conflict would show within it
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'the page holds what the file holds')
                self.assertEqual(self.export(page)['live']['overrides'], {'hero.lead': {'text': self.TYPED}})
                self.assertEqual(errors, [])

    def test_an_import_that_drops_a_text_edit_with_trailing_spaces_the_page_holds_raises_the_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.saved_text_edit(engine)
                document['live']['overrides'] = {}
                self.assertEqual(self.import_document(page, document), STATUS)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.assertEqual(self.banner_heading(page), HEADING)
                self.assertEqual(frame.evaluate('window.fake.ledger().targets.find(t => t.targetId === "hero.lead").text'), 'Changed lead')
                self.assertEqual(errors, [])

    def test_an_import_that_changes_a_text_edit_to_other_text_the_page_does_not_hold_still_differs(self):
        """Normalizing must not hide a real difference: the page holds the old text, the file has another."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.saved_text_edit(engine)
                document['live']['overrides'] = {'hero.lead': {'text': 'Another lead'}}
                self.assertEqual(self.import_document(page, document), STATUS)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.assertEqual(errors, [])

    def test_an_imported_override_the_page_lacks_raises_the_banner(self):
        """A property that is missing on the page is not the same as a present one."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.with_live_tokens(self.blank_document(engine))
                document['live']['tokens'] = {}
                document['live']['overrides'] = {'hero.lead': {'fontSize': 21}}
                self.assertEqual(self.import_document(page, document), STATUS)
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.assertEqual(self.banner_heading(page), HEADING)
                self.assertEqual(errors, [])


class ImportWhileNotLinkedTests(ImportLinkCase):
    """An import that is not linked behaves as it always did (characterization)."""

    def test_an_unlinked_import_keeps_its_status_sends_nothing_and_shows_no_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertIn('Composition imported.', self.import_document(page, self.blank_document(engine)))
                page.wait_for_timeout(300)     # absence window: an unlinked import never reaches the page
                self.assertEqual(self.composition_updates(frame), [])
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertNotIn('link to the page', page.locator('#composerStatus').inner_text())
                # It stays unlinked: the next composition edit sends nothing until the user syncs.
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                page.wait_for_timeout(300)
                self.assertEqual(self.composition_updates(frame), [])
                self.assertEqual(errors, [])

    def test_a_rejected_import_while_linked_keeps_the_link(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                status = self.import_document(page, {'composition': {'slots': 'nope'}})
                self.assertRegex(status, r'^Import failed')
                page.locator('#compositionPreset').select_option('asteria')
                page.locator('#applyPreset').click()
                self.wait_composition_updates(frame, 2)     # still linked: the edit streams
                self.assertEqual(errors, [])


class LateEditReplyTests(ImportLinkCase):
    """A user edit sent before an import and acknowledged after it must not replace the imported override (Rule 6):
    saved state keeps the imported value, the page still holds the edit, so the banner offers the choice."""

    IMPORTED = 30
    EDIT = 21

    def imported_document(self, page):
        """The file the user imports: hero.lead saved at a size other than the one the held edit will set."""
        document = self.export(page)
        document['live'] = {**document.get('live', {'target': FAKE, 'revision': 0}), 'overrides': {'hero.lead': {'fontSize': self.IMPORTED}}}
        return document

    def hold_an_edit(self, page, frame):
        self.select(page, frame, 'hero.lead')
        frame.evaluate('window.fake.hold = true')
        self.set_value(page, '#liveFontSize', self.EDIT)
        frame.wait_for_function(f'window.fake.styleOf("hero.lead").fontSize === "{self.EDIT}px"')   # sent, its reply held

    def saved_overrides(self, page):
        return self.export(page)['live']['overrides']

    def check_late_edit_ack(self, engine, linked):
        if linked:
            page, frame, errors = self.linked_page(engine)
        else:
            page, errors = self.open(engine)
            self.wait_connected(page)
            frame = self.frame(page)
        document = self.imported_document(page)
        self.hold_an_edit(page, frame)
        self.import_document(page, document)
        self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}})
        self.watch_handled(page)
        frame.evaluate('window.fake.hold = false')
        frame.evaluate('window.fake.release()')                      # the edit is acknowledged after the import
        self.wait_handled(page, 1)
        page.wait_for_timeout(300)     # absence window: a late adoption of the edit would show within it
        self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}}, 'the import is the saved state')
        self.assertEqual(frame.evaluate('window.fake.styleOf("hero.lead").fontSize'), f'{self.EDIT}px', 'nothing was applied behind the user')
        page.locator('#viewTargetApp').click()
        banner = page.locator('#liveReconnectBanner')
        self.assertTrue(banner.is_visible(), 'the page holds the edit, the import saved another value')
        self.assertEqual(self.banner_heading(page), HEADING)
        # Reapply puts the imported value on the page.
        page.locator('#liveReapply').click()
        banner.wait_for(state='hidden')
        frame.wait_for_function(f'window.fake.styleOf("hero.lead").fontSize === "{self.IMPORTED}px"')
        self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}})
        self.assertEqual(errors, [])

    def test_an_edit_acknowledged_after_a_linked_import_does_not_replace_the_imported_override(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_late_edit_ack(engine, linked=True)

    def test_an_edit_acknowledged_after_an_unlinked_import_does_not_replace_the_imported_override(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_late_edit_ack(engine, linked=False)

    def test_an_edit_rejected_after_an_import_keeps_the_imported_override_and_is_not_sent_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.imported_document(page)
                frame.evaluate('window.fake.conflictAlways = true')
                self.hold_an_edit_rejected(page, frame)
                self.import_document(page, document)
                frame.evaluate('window.fake.conflictAlways = false')
                self.watch_handled(page)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                self.wait_handled(page, 1)
                page.wait_for_timeout(300)     # absence window: a second send of the edit would arrive in it
                self.assertEqual(len([u for u in self.updates(frame) if u.get('targetId') == 'hero.lead']), 1, 'not sent again')
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}})
                self.assertNotIn('Rejected', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(errors, [])

    def hold_an_edit_rejected(self, page, frame):
        self.select(page, frame, 'hero.lead')
        frame.evaluate('window.fake.hold = true')
        self.set_value(page, '#liveFontSize', self.EDIT)
        frame.wait_for_function('window.__received.some(item => item.data && item.data.targetId === "hero.lead")')

    def test_an_edit_acknowledged_after_a_timeout_and_an_import_keeps_the_imported_override(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.imported_document(page)
                self.hold_an_edit(page, frame)
                self.wait_badge(page, r'^No response from target$', timeout=15000)    # the edit timed out
                self.import_document(page, document)
                self.watch_handled(page)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')                  # its late acknowledgement
                self.wait_handled(page, 1)
                page.wait_for_timeout(300)     # absence window: a late adoption of the edit would show within it
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}})
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_a_queued_edit_the_import_drops_is_reported_in_the_status_and_never_sent(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.imported_document(page)
                self.hold_an_edit(page, frame)
                self.set_value(page, '#liveLineHeight', 1.5)          # queued behind the held edit
                page.wait_for_timeout(200)     # absence window: the queued edit must not be sent while the first reply is held
                self.assertEqual([u['patch'] for u in self.updates(frame) if u.get('targetId') == 'hero.lead'], [{'fontSize': self.EDIT}])
                status = self.import_document(page, document)
                self.assertEqual(status, STATUS + ' 1 queued edit that had not reached the page was dropped.')
                self.watch_handled(page)
                frame.evaluate('window.fake.hold = false')
                frame.evaluate('window.fake.release()')
                self.wait_handled(page, 1)
                page.wait_for_timeout(300)     # absence window: the dropped edit would be sent within it
                self.assertEqual([u['patch'] for u in self.updates(frame) if u.get('targetId') == 'hero.lead'], [{'fontSize': self.EDIT}])
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.IMPORTED}})
                self.assertEqual(page.locator('#composerStatus').inner_text(), status, 'the report stays')
                self.assertEqual(errors, [])

    def test_an_unlinked_import_with_a_queued_edit_says_so_too(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                document = self.imported_document(page)
                self.hold_an_edit(page, frame)
                self.set_value(page, '#liveLineHeight', 1.5)
                page.wait_for_timeout(200)     # absence window: the queued edit must not be sent while the first reply is held
                status = self.import_document(page, document)
                self.assertEqual(status, 'Composition imported. Image assets must be reselected in v0.1.1.'
                                 ' 1 queued edit that had not reached the page was dropped.')
                self.assertEqual(errors, [])

    def test_an_import_without_queued_edits_keeps_its_status(self):
        """Characterization: nothing was dropped, so nothing is added to the status."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.imported_document(page)
                self.hold_an_edit(page, frame)
                self.assertEqual(self.import_document(page, document), STATUS)
                self.assertEqual(errors, [])


    # What an import without `live` keeps, what an empty `live` flags, and the other op kinds (reset, move).

    def release(self, page, frame):
        """Lets the held reply through and waits until Studio has handled it (and a stray send could have shown)."""
        self.watch_handled(page)
        frame.evaluate('window.fake.hold = false')
        frame.evaluate('window.fake.release()')
        self.wait_handled(page, 1)
        page.wait_for_timeout(300)     # absence window: a stray send or a late adoption would show within it

    def open_unlinked(self, engine):
        page, errors = self.open(engine)
        self.wait_connected(page)
        return page, self.frame(page), errors

    def test_a_linked_import_with_empty_overrides_flags_the_edit_the_page_still_holds(self):
        """The edit was sent before the import, which saves no overrides: the page keeps 21px, Studio saves nothing,
        so the page differs from the import and the banner offers the choice (Rule 6)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.export(page)
                self.assertEqual(document['live']['overrides'], {})
                self.hold_an_edit(page, frame)
                self.import_document(page, document)
                self.release(page, frame)
                self.assertEqual(self.saved_overrides(page), {}, 'the import is the saved state')
                self.assertEqual(frame.evaluate('window.fake.styleOf("hero.lead").fontSize'), f'{self.EDIT}px')
                banner = page.locator('#liveReconnectBanner')
                self.assertTrue(banner.is_visible(), 'the page holds an edit the import does not save')
                self.assertEqual(self.banner_heading(page), HEADING)
                page.locator('#liveReapply').click()          # the page goes back to the imported state
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'window.fake.styleOf("hero.lead").fontSize !== "{self.EDIT}px"')
                self.assertEqual(self.saved_overrides(page), {})
                self.assertEqual(errors, [])

    def check_no_live_import_keeps_the_edit(self, engine, linked):
        if linked:
            page, frame, errors = self.linked_page(engine)
        else:
            page, frame, errors = self.open_unlinked(engine)
        # Something is already saved, so the first acknowledgement of an empty saved state is not what keeps the edit.
        self.select(page, frame, 'hero.title')
        self.set_value(page, '#liveFontSize', 44)
        self.wait_badge(page, r'^Live · rev 2$' if linked else r'^Live · rev 1$')
        document = self.export(page)
        document.pop('live', None)       # a file without `live` does not replace Studio's overrides
        self.hold_an_edit(page, frame)
        self.import_document(page, document)
        self.release(page, frame)
        self.assertEqual(self.saved_overrides(page), {'hero.title': {'fontSize': 44}, 'hero.lead': {'fontSize': self.EDIT}},
                         'the edit is recorded normally')
        self.assertEqual(frame.evaluate('window.fake.styleOf("hero.lead").fontSize'), f'{self.EDIT}px')
        self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'the page holds exactly what Studio saved')
        self.assertEqual(errors, [])

    def test_an_edit_acknowledged_after_a_linked_import_without_live_is_still_saved(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_no_live_import_keeps_the_edit(engine, linked=True)

    def test_an_edit_acknowledged_after_an_unlinked_import_without_live_is_still_saved(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.check_no_live_import_keeps_the_edit(engine, linked=False)

    def test_a_queued_edit_is_kept_by_an_import_without_live(self):
        """The import does not replace overrides, so it does not drop the user's queued edit either."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.export(page)
                document.pop('live', None)
                self.hold_an_edit(page, frame)
                self.set_value(page, '#liveLineHeight', 1.5)          # queued behind the held edit
                page.wait_for_timeout(200)     # absence window: the queued edit must not be sent while the first reply is held
                self.assertEqual(self.import_document(page, document), STATUS)
                self.release(page, frame)
                frame.wait_for_function('window.__received.filter(item => item.data && item.data.targetId === "hero.lead").length === 2')
                self.wait_badge(page, r'^Live · rev 3$')
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT, 'lineHeight': 1.5}})
                self.assertEqual(errors, [])

    def test_an_unlinked_import_with_empty_overrides_after_a_held_edit(self):
        """Characterization of the unlinked path: with nothing saved on either side, Studio adopts what the page
        acknowledges (the same rule as a first connect), so the edit is saved and no banner shows."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.open_unlinked(engine)
                document = self.export(page)
                document['live'] = {'target': FAKE, 'revision': 0, 'overrides': {}}
                self.hold_an_edit(page, frame)
                self.import_document(page, document)
                self.release(page, frame)
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT}})
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def saved_edit_and_import(self, engine):
        """hero.lead is saved at 21px (acknowledged); the file imported later saves the same."""
        page, frame, errors = self.linked_page(engine)
        self.select(page, frame, 'hero.lead')
        self.set_value(page, '#liveFontSize', self.EDIT)
        self.wait_badge(page, r'^Live · rev 2$')
        document = self.export(page)
        self.assertEqual(document['live']['overrides'], {'hero.lead': {'fontSize': self.EDIT}})
        return page, frame, errors, document

    def hold_a_reset(self, page, frame):
        frame.evaluate('window.fake.hold = true')
        page.locator('#liveResetTarget').click()
        frame.wait_for_function('window.__received.some(item => item.data && item.data.type === "design:reset")')

    def resets(self, frame):
        return [item['data'] for item in self.received(frame, 'design:reset')]

    def test_a_reset_acknowledged_after_an_import_keeps_the_imported_override_and_flags_the_page(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.saved_edit_and_import(engine)
                self.hold_a_reset(page, frame)
                self.import_document(page, document)
                self.release(page, frame)
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT}}, 'the import is the saved state')
                banner = page.locator('#liveReconnectBanner')
                self.assertTrue(banner.is_visible(), 'the page lost an override the import saves')
                self.assertEqual(self.banner_heading(page), HEADING)
                page.locator('#liveReapply').click()          # the page gets the imported override back
                banner.wait_for(state='hidden')
                frame.wait_for_function(f'window.fake.styleOf("hero.lead").fontSize === "{self.EDIT}px"')
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT}})
                self.assertEqual(errors, [])

    def test_a_reset_rejected_after_an_import_is_not_sent_again(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.saved_edit_and_import(engine)
                frame.evaluate('window.fake.conflictAlways = true')
                self.hold_a_reset(page, frame)
                self.import_document(page, document)
                frame.evaluate('window.fake.conflictAlways = false')
                self.release(page, frame)
                self.assertEqual(len(self.resets(frame)), 1, 'not sent again')
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT}})
                self.assertNotIn('Rejected', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(errors, [])

    def arranged_page(self, engine, css_order):
        """Linked to the arrange fixture with card.b selected, a file exported (no saved order) and a move held."""
        page, errors = self.open(engine, target=ARRANGE)
        frame = ArrangeCase.wait_ready(self, page, 11)
        self.sync(page)
        self.select(page, frame, 'card.b')
        if css_order:
            page.locator('#liveMoveStrategyCss').click()
        document = self.export(page)
        self.assertNotIn('structure', document['live'])
        self.assertEqual(document['live']['overrides'], {})
        return page, frame, errors, document

    def hold_a_move(self, page, frame):
        frame.evaluate('window.fake.hold = true')
        page.locator('#liveMoveFirst').click()
        frame.wait_for_function('window.__received.some(item => item.data && item.data.type === "design:move")')

    def moved_order(self, frame, css_order):
        return frame.evaluate('(key) => window.fake.%s(key)' % ('visualOrder' if css_order else 'domOrder'), 'cards')

    def check_move_after_import(self, engine, css_order):
        page, frame, errors, document = self.arranged_page(engine, css_order)
        self.hold_a_move(page, frame)
        self.import_document(page, document)
        self.release(page, frame)
        self.assertEqual(self.moved_order(frame, css_order)[:2], ['card.b', 'card.a'], 'the page moved')
        saved = self.export(page)['live']
        self.assertNotIn('structure', saved, 'the import is the saved DOM order')
        self.assertEqual(saved['overrides'], {}, 'the import is the saved CSS order')
        banner = page.locator('#liveReconnectBanner')
        self.assertTrue(banner.is_visible(), 'the page holds an order the import does not save')
        self.assertEqual(self.banner_heading(page), HEADING)
        return page, frame, errors, banner

    def test_a_dom_move_acknowledged_after_an_import_is_not_saved_and_raises_the_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, banner = self.check_move_after_import(engine, css_order=False)
                # Accept target state clears the difference; a DOM order only the page holds is never adopted (Rule 6).
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertNotIn('structure', self.export(page)['live'])
                self.assertEqual(errors, [])

    def test_a_dom_move_acknowledged_after_an_import_is_cleared_by_reapply(self):
        """What Reapply does for a DOM move the import did not save: nothing is saved to put back, so it ends the
        difference without moving elements (a DOM move cannot be undone without a saved order)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, banner = self.check_move_after_import(engine, css_order=False)
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                page.wait_for_timeout(300)     # absence window: a move or reset sent by Reapply would arrive within it
                self.assertEqual(len(self.received(frame, 'design:move')), 1, 'Reapply sent no move')
                self.assertEqual(len(self.resets(frame)), 0, 'Reapply sent no reset')
                self.assertEqual(self.moved_order(frame, False)[:2], ['card.b', 'card.a'], 'the page keeps the move')
                self.assertNotIn('structure', self.export(page)['live'])
                self.assertEqual(errors, [])

    def test_a_css_order_move_acknowledged_after_an_import_is_not_saved_and_raises_the_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, banner = self.check_move_after_import(engine, css_order=True)
                self.assertEqual(self.moved_order(frame, False)[:2], ['card.a', 'card.b'], 'CSS order leaves the DOM alone')
                # Reapply puts the saved order (none) back: the page's CSS order goes.
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('JSON.stringify(window.fake.visualOrder("cards")) === JSON.stringify(["card.a","card.b","card.c","card.d"])')
                self.assertEqual(self.export(page)['live']['overrides'], {})
                self.assertEqual(errors, [])

    def test_accept_target_state_after_a_late_css_order_move_adopts_the_pages_order(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, banner = self.check_move_after_import(engine, css_order=True)
                page.locator('#liveAcceptTarget').click()
                banner.wait_for(state='hidden')
                self.assertEqual(self.export(page)['live']['overrides'],
                                 {'card.b': {'order': 0}, 'card.a': {'order': 1}, 'card.c': {'order': 2}, 'card.d': {'order': 3}})
                self.assertEqual(errors, [])

    def test_a_move_rejected_after_an_import_is_not_sent_again_and_changes_nothing(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.arranged_page(engine, css_order=False)
                frame.evaluate('window.fake.conflictAlways = true')
                self.hold_a_move(page, frame)
                self.import_document(page, document)
                frame.evaluate('window.fake.conflictAlways = false')
                self.release(page, frame)
                self.assertEqual(len(self.received(frame, 'design:move')), 1, 'not sent again')
                self.assertEqual(self.moved_order(frame, False), ['card.a', 'card.b', 'card.c', 'card.d'], 'the page did not move')
                self.assertNotIn('structure', self.export(page)['live'])
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'the page holds what the import saved')
                self.assertNotIn('Rejected', page.locator('#bridgeStatusBadge').inner_text())
                self.assertEqual(errors, [])

    def test_a_move_acknowledged_after_a_timeout_and_an_import_raises_the_banner(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors, document = self.arranged_page(engine, css_order=True)
                self.hold_a_move(page, frame)
                self.wait_badge(page, r'^No response from target$', timeout=15000)    # the move timed out
                self.import_document(page, document)
                self.release(page, frame)
                self.assertEqual(self.export(page)['live']['overrides'], {}, 'the import is the saved CSS order')
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible())
                self.assertEqual(errors, [])

    def test_a_saved_override_and_a_sent_edit_on_one_target_are_both_remembered(self):
        """lineHeight was saved before the import and the import drops it; the held fontSize edit equals what the
        import saves. The page ends up holding both, and only the dropped lineHeight differs from the import."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                self.select(page, frame, 'hero.lead')
                self.set_value(page, '#liveLineHeight', 1.5)
                self.wait_badge(page, r'^Live · rev 2$')
                document = self.export(page)
                document['live']['overrides'] = {'hero.lead': {'fontSize': self.EDIT}}
                self.hold_an_edit(page, frame)
                self.import_document(page, document)
                self.release(page, frame)
                self.assertEqual(self.saved_overrides(page), {'hero.lead': {'fontSize': self.EDIT}})
                self.assertTrue(page.locator('#liveReconnectBanner').is_visible(), 'the page still holds the dropped line height')
                self.assertEqual(errors, [])

    def test_two_dropped_queued_edits_are_reported_in_the_plural(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.linked_page(engine)
                document = self.imported_document(page)
                self.hold_an_edit(page, frame)
                self.set_value(page, '#liveLineHeight', 1.5)          # queued: hero.lead
                self.select(page, frame, 'hero.title')
                self.set_value(page, '#liveFontSize', 44)             # queued: another target
                page.wait_for_timeout(200)     # absence window: the queued edits must not be sent while the first reply is held
                status = self.import_document(page, document)
                self.assertEqual(status, STATUS + ' 2 queued edits that had not reached the page were dropped.')
                self.assertEqual(errors, [])


class ImportWhileLinkedRealBridgeTests(LiveIntegrationCase):
    """Real Studio, real bridge, real demo page: the import changes nothing on the page until the user syncs."""

    WORDMARK = '.wordmark'

    def blank_document(self, engine):
        page = self.open(engine, query=False)
        page.locator('#modeComposer').click()
        page.locator('#compositionPreset').select_option('blank')
        page.locator('#applyPreset').click()
        document = self.export(page)
        self.assertNotIn('live', document)
        return document

    def family(self, frame):
        return self.style(frame, self.WORDMARK, 'fontFamily')

    def test_import_while_linked_changes_nothing_on_the_page_until_sync(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                document = self.blank_document(engine)
                page = self.connected(engine)
                frame = self.frame(page)
                page.locator('#btnSyncToApp').click()
                self.wait_badge(page, r'^Live · rev \d+$')
                frame.wait_for_function(
                    f'getComputedStyle(document.querySelector({self.WORDMARK!r})).fontFamily.includes("Fraunces")', timeout=8000)
                revision = page.locator('#bridgeStatusBadge').inner_text()

                status = self.import_document(page, document)
                self.assertEqual(status, 'Imported; the link to the page is off. Press Sync to Live App to send this composition.')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                self.assertEqual(page.locator('#liveReconnectHeading').inner_text(), 'Imported state differs from the target.')
                page.wait_for_timeout(300)     # absence window: a send would restyle the page within it
                self.assertIn('Fraunces', self.family(frame), 'the import did not restyle the page')
                self.assertEqual(page.locator('#bridgeStatusBadge').inner_text(), revision, 'the import sent no request')
                self.assertIn('--font-display: "Inter"', self.tab(page, 'Css'))

                # Sync to Live App links again and sends what was imported.
                page.locator('#btnSyncToApp').click()
                frame.wait_for_function(
                    f'getComputedStyle(document.querySelector({self.WORDMARK!r})).fontFamily.includes("Inter")', timeout=8000)
                self.assertNotIn('Fraunces', self.family(frame))
                banner.wait_for(state='hidden')
                self.assertEqual(page.errors, [])


if __name__ == '__main__':
    unittest.main()
