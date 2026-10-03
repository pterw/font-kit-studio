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
from test_studio_live import LiveCase

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
