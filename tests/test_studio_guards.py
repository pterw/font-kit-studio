"""Studio guards (v0.4.1 Task 9): an import that names a font the library lacks says so (row S08), and a reload asks only
when edits would be lost (row C2-5c).

The fallback itself is pinned elsewhere (test_studio_live: an unknown family imports as the first library font);
these tests guard only that the replacement is no longer silent, and that it stays quiet when no family is lost.

Run one module by name with PYTHONPATH=tests:  python -m unittest test_studio_guards
"""

import unittest

from support import ENGINES

from test_studio_controls import ControlsMixin
from test_studio_import_link import STATUS, ImportLinkCase
from test_studio_live import ARRANGE, ArrangeCase, LiveCase

PLAIN = 'Composition imported. Image assets must be reselected.'
GHOST = 'ghost-face is not in the library, so the first library font is used.'


def text(family=None, **fields):
    slot = {'type': 'text', **fields}
    if family is not None:
        slot['family'] = family
    return slot


def document(*slots):
    return {'version': '0.1.0', 'composition': {'slots': list(slots)}}


class UnknownFamilyImportTests(ImportLinkCase):
    def imported(self, engine, *slots):
        page, errors = self.open(engine, query=False)
        page.locator('#modeComposer').click()
        status = self.import_document(page, document(*slots))
        return page, errors, status

    def test_an_unknown_family_is_named_once_and_the_first_library_font_is_used(self):
        """Given two slots naming ghost-face, when imported, then the status names it once and both export fraunces."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, status = self.imported(engine, text('ghost-face'), text('ghost-face'))
                self.assertEqual(status, f'{PLAIN} {GHOST}')
                self.assertEqual([s['family'] for s in self.export(page)['composition']['slots']], ['fraunces', 'fraunces'])
                self.assertEqual(errors, [])

    def test_a_row_child_is_named_and_distinct_families_follow_first_seen_order(self):
        """Given a top-level slot and a row child with different unknown families, then both are named in file order."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                row = {'type': 'row', 'childCount': 2, 'children': [text('row-ghost'), text('inter')]}
                _, errors, status = self.imported(engine, text('ghost-face'), row)
                self.assertEqual(status, f'{PLAIN} {GHOST} row-ghost is not in the library, so the first library font is used.')
                self.assertEqual(errors, [])

    def test_a_row_child_cut_by_the_row_count_is_not_named(self):
        """Given a row of two whose third child names an unknown family, then the cut child is not reported."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                row = {'type': 'row', 'childCount': 2, 'children': [text('inter'), text('inter'), text('cut-ghost')]}
                _, errors, status = self.imported(engine, row)
                self.assertEqual(status, PLAIN)
                self.assertEqual(errors, [])

    def test_no_warning_when_no_family_is_lost(self):
        """Given a library family, a legacy key, no family, a non-string and an empty family, then the status is unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, status = self.imported(
                    engine, text('inter'), text('gotham'), text(), text(7), text(''))
                self.assertEqual(status, PLAIN)
                self.assertEqual(errors, [])

    def test_the_warning_follows_the_linked_import_status_too(self):
        """Given a linked Studio, when an import names ghost-face, then the link-off status carries the sentence."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, _, errors = self.linked_page(engine)
                status = self.import_document(page, document(text('ghost-face')))
                self.assertEqual(status, f'{STATUS} {GHOST}')
                self.assertEqual(errors, [])


PROBE = '''() => { const e = new Event('beforeunload', {cancelable: true}); window.dispatchEvent(e); return e.defaultPrevented; }'''
CLIPBOARD = '''() => Object.defineProperty(navigator, 'clipboard', {configurable: true, value: {writeText: async () => {}}})'''


class LeavePromptTests(ControlsMixin, LiveCase):
    """The probe is a synthetic cancelable beforeunload: it answers at once and leaves the page open. Only the positive
    control and the no-edit closes use a real close, and those wait for the page's close event."""

    def edited(self, engine):
        page, errors = self.open(engine, sync=True)
        self.wait_connected(page)
        dialogs = []
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.accept()))
        self.edit_size(page, self.frame(page))
        return page, errors, dialogs

    def prompts(self, page):
        return page.evaluate(PROBE)

    def assert_closes_silently(self, page, dialogs):
        with page.expect_event('close'):
            page.close(run_before_unload=True)
        self.assertTrue(page.is_closed())
        self.assertEqual([d for d in dialogs if d == 'beforeunload'], [])

    def test_closing_a_page_with_an_unsynced_edit_asks(self):
        """Given an edit that no carrier has taken, when the tab closes, then the browser raises a beforeunload dialog."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                self.edit_size(page, self.frame(page))
                page.locator('body').click(position={'x': 1, 'y': 1})          # the browser prompts only after a gesture
                seen = []
                page.on('dialog', lambda dialog: (seen.append(dialog.type), dialog.dismiss()))
                with page.expect_event('dialog'):
                    page.close(run_before_unload=True)
                self.assertEqual(seen, ['beforeunload'])
                page.close()
                self.assertEqual(errors, [])

    def test_nothing_held_closes_without_asking_even_after_reset_all(self):
        """Given a fresh Studio, then a close is silent; given an edit undone by Reset all page edits, a close is silent too."""
        for engine in ENGINES:
            with self.subTest(engine=engine, case='fresh'):
                page, errors = self.open(engine, sync=True)
                self.wait_connected(page)
                dialogs = []
                page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.accept()))
                self.assertFalse(self.prompts(page))
                self.assert_closes_silently(page, dialogs)
            with self.subTest(engine=engine, case='reset all'):
                page, errors, dialogs = self.edited(engine)
                self.assertTrue(self.prompts(page))
                page.get_by_role('button', name='Reset all page edits').click()
                page.wait_for_function('() => document.querySelector("#liveChangeCount").textContent === "0"')
                self.assertFalse(self.prompts(page))
                self.assert_closes_silently(page, dialogs)
                self.assertEqual(errors, [])

    def test_sync_takes_the_edit_and_a_further_edit_asks_again(self):
        """Given an unsynced edit, when Sync to file succeeds, then the page stops asking; a further edit makes it ask again."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, dialogs = self.edited(engine)
                self.assertTrue(self.prompts(page))
                self.sync_file(page)
                self.assertFalse(self.prompts(page))
                self.edit_size(page, self.frame(page), size=60)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_failed_write_still_asks(self):
        """Given an unsynced edit, when the dev server refuses the write, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, dialogs = self.edited(engine)
                page.context.route('**/__fontkit/overrides.css', lambda route: route.fulfill(
                    status=500, content_type='application/json', body='{"ok": false, "error": "disk full"}'))
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Sync failed/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertTrue(self.prompts(page))

    def test_an_edit_made_while_the_write_is_in_flight_still_asks(self):
        """Given a write held open, when a further edit lands before it answers, then the page asks after the write succeeds."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, dialogs = self.edited(engine)
                held = []
                page.route('**/__fontkit/overrides.css', lambda route: held.append(route))
                page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saving/.test(document.querySelector("#liveCodeStatus").textContent)')
                for _ in range(250):
                    if held:
                        break
                    page.wait_for_timeout(20)
                self.assertTrue(held, 'the write never reached the route')
                self.edit_size(page, self.frame(page), size=60)
                held[0].fulfill(status=200, content_type='application/json', body='{"ok": true, "bytes": 1, "path": "x.css"}')
                page.wait_for_function('() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_copy_and_download_each_take_the_edit(self):
        """Given an unsynced edit, when Copy or Download succeeds, then the page stops asking until the next edit."""
        for engine in ENGINES:
            for carrier in ('copy', 'download'):
                with self.subTest(engine=engine, carrier=carrier):
                    page, errors, dialogs = self.edited(engine)
                    page.evaluate(CLIPBOARD)
                    self.assertTrue(self.prompts(page))
                    if carrier == 'copy':
                        page.locator('#liveCodeCopy').click()
                        page.wait_for_function('() => /Copied/i.test(document.querySelector("#liveCodeStatus").textContent)')
                    else:
                        with page.expect_download():
                            page.locator('#liveCodeDownload').click()
                    self.assertFalse(self.prompts(page))
                    self.edit_size(page, self.frame(page), size=60)
                    self.assertTrue(self.prompts(page))
                    self.assertEqual(errors, [])


class LeavePromptCoverageTests(ControlsMixin, ArrangeCase):
    """Each save covers only the parts its output holds: Sync to file and the CSS tab carry styles; the JSON tab carries
    text and moves (and styles without tokens); the HTML tab carries moves and text only while the page ledger prints them.
    The page asks while a held part has not been carried."""

    def prompts(self, page):
        return page.evaluate(PROBE)

    def arranged(self, engine):
        page, errors = self.open(engine, target=ARRANGE, sync=True)
        frame = self.wait_ready(page, 11)
        return page, errors, frame

    def move(self, page, frame):
        self.select(page, frame, 'card.c')
        page.locator('#liveMoveFirst').click()
        self.wait_badge(page, r'^Live · rev 1$')

    def download(self, page, tab):
        page.locator(f'#codeTab{tab}').click()
        with page.expect_download():
            page.locator('#liveCodeDownload').click()

    def test_a_dom_move_still_asks_after_sync_to_file_because_the_file_has_no_moves(self):
        """Given a saved DOM move, when Sync to file succeeds, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.move(page, frame)
                self.assertTrue(self.prompts(page))
                self.sync_file(page)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_style_edit_stops_asking_after_sync_to_file_but_not_after_the_html_tab(self):
        """Given a style edit, Sync to file takes it; the HTML tab holds no styles, so Download there leaves the ask."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.assertTrue(self.prompts(page))
                self.download(page, 'Html')
                self.assertTrue(self.prompts(page))
                self.sync_file(page)
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_after_sync_to_file_a_live_app_reload_does_not_make_the_page_ask(self):
        """Given every override written to the file, when the Live App reloads, then closing Studio does not ask."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.sync_file(page)
                self.assertFalse(self.prompts(page))
                frame.evaluate('location.reload()')
                page.locator('#liveReconnectBanner').wait_for(state='visible')
                self.wait_ready(page, 11)
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def edit_text(self, page, frame):
        self.select(page, frame, 'hero.title')
        page.locator('#liveText').fill('A new headline')
        self.wait_badge(page, r'^Live · rev 1$')

    def reload_app(self, page, frame):
        frame.evaluate('location.reload()')
        page.locator('#liveReconnectBanner').wait_for(state='visible')
        self.wait_ready(page, 11)

    def test_a_text_edit_still_asks_after_sync_and_a_live_app_reload_because_the_file_has_no_text(self):
        """Given a saved text edit, when Sync to file succeeds and the Live App reloads, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_text(page, frame)
                self.assertTrue(self.prompts(page))
                self.sync_file(page)
                self.assertTrue(self.prompts(page))
                self.reload_app(page, frame)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_move_still_asks_after_a_live_app_reload_and_the_html_tab_that_no_longer_prints_it(self):
        """Given a saved move and a reloaded Live App, when the HTML tab is downloaded, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.move(page, frame)
                self.reload_app(page, frame)
                self.assertTrue(self.prompts(page))
                self.download(page, 'Html')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_the_json_tab_carries_a_text_edit(self):
        """Given a saved text edit, when the JSON tab is downloaded, then the page stops asking."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_text(page, frame)
                self.assertTrue(self.prompts(page))
                self.download(page, 'Json')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_the_json_tab_carries_a_dom_move(self):
        """Given a saved DOM move, when the JSON tab is downloaded, then the page stops asking."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.move(page, frame)
                self.assertTrue(self.prompts(page))
                self.download(page, 'Json')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
