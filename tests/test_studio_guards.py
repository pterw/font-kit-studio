"""Studio guards (v0.4.1 Task 9): an import that names a font the library lacks says so (row S08), and a reload asks only
when edits would be lost (row C2-5c).

The fallback itself is pinned elsewhere (test_studio_live: an unknown family imports as the first library font);
these tests guard only that the replacement is no longer silent, and that it stays quiet when no family is lost.

Run one module by name with PYTHONPATH=tests:  python -m unittest test_studio_guards
"""

import unittest
from urllib.parse import quote

from support import ENGINES

from test_studio_controls import ControlsMixin
from test_studio_import_link import STATUS, ImportLinkCase
from test_studio_live import APP, ARRANGE, FAKE, ArrangeCase, LiveCase

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
SAVED = '''() => /Saved/.test(document.querySelector("#liveCodeStatus").textContent)'''


def synced(case, page):
    """Presses Sync to file and waits for the page to mark the save carried: it does so after reading the response body,
    a task later than the response that sync_file waits for, so a probe taken at once can still see the old state."""
    case.sync_file(page)
    page.wait_for_function(SAVED)


# Runs in every frame before the page's own scripts, so its capture listener comes first at the window: while
# `window.__withhold` names a message type it stops that message reaching the bridge, so the Live App never replies.
WITHHOLD = '''(() => { window.__withhold = null;
  window.addEventListener('message', e => { if (window.__withhold && e.data && e.data.type === window.__withhold) e.stopImmediatePropagation(); }, true); })()'''
NO_RESPONSE = '''() => /No response from the Live App/.test(document.querySelector("#bridgeStatusBadge").textContent)'''


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
                synced(self, page)
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

    def held_back(self, engine, kind):
        """A connected, synced Studio whose Live App will not answer a `kind` message."""
        context = self.context(engine, sync=True)
        context.add_init_script(WITHHOLD)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{APP}?target={quote(FAKE, safe="")}')
        self.wait_connected(page)
        frame = self.frame(page)
        frame.evaluate('(kind) => { window.__withhold = kind; }', kind)
        return page, frame, errors

    def reset_pressed_after_a_save(self, engine):
        """An edit the page has acknowledged and a save has taken, then Reset this element sent and left unanswered."""
        page, frame, errors = self.held_back(engine, 'design:reset')
        self.edit_size(page, frame)
        synced(self, page)
        self.assertFalse(self.prompts(page))
        page.locator('#liveResetTarget').click()
        return page, frame, errors

    def test_an_edit_in_flight_still_asks(self):
        """Given an edit the Live App has not answered, when the tab closes, then the page asks and holds nothing."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.held_back(engine, 'design:update')
                self.select(page, frame)
                self.set_value(page, '#liveFontSize', 50)
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_that_timed_out_still_asks(self):
        """Given an edit the Live App never answered, when the page reports no response, then it still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.held_back(engine, 'design:update')
                self.select(page, frame)
                self.set_value(page, '#liveFontSize', 50)
                page.wait_for_function(NO_RESPONSE, timeout=15000)
                self.assertEqual(page.locator('#liveChangeCount').inner_text(), '0')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_waiting_in_the_queue_asks(self):
        """Given a Reset left unanswered, when an edit waits behind it, then the page asks though nothing is in flight for it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.reset_pressed_after_a_save(engine)
                self.set_value(page, '#liveFontSize', 60)
                self.assertEqual(len(self.updates(frame)), 1)               # the second edit was never sent
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_reset_awaiting_its_reply_does_not_ask(self):
        """Given a saved edit and a Reset left unanswered with nothing behind it, then the page does not ask."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.reset_pressed_after_a_save(engine)
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_an_import_replaced_does_not_ask(self):
        """Given an edit that timed out, when an import carrying live state replaces it, then the page does not ask."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, errors = self.held_back(engine, 'design:update')
                self.select(page, frame)
                self.set_value(page, '#liveFontSize', 50)
                page.wait_for_function(NO_RESPONSE, timeout=15000)
                self.assertTrue(self.prompts(page))
                live = {'target': FAKE, 'revision': 0, 'overrides': {}}
                self.assertIn('Composition imported.', self.import_document(page, {**self.export(page), 'live': live}))
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_made_while_the_write_is_in_flight_still_asks(self):
        """Given a write held open, when a further edit lands before it answers, then the page asks after the write succeeds."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, dialogs = self.edited(engine)
                held = []
                page.route('**/__fontkit/overrides.css', lambda route: held.append(route))
                with page.expect_request(lambda request: request.method == 'PUT' and request.url.endswith('/__fontkit/overrides.css')):
                    page.locator('#liveCodeSync').click()
                page.wait_for_function('() => /Saving/.test(document.querySelector("#liveCodeStatus").textContent)')
                self.edit_size(page, self.frame(page), size=60)
                self.assertTrue(held, 'the write never reached the route')
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
        page.wait_for_function('() => /Downloaded/.test(document.querySelector("#liveCodeStatus").textContent)')

    def test_a_dom_move_still_asks_after_sync_to_file_because_the_file_has_no_moves(self):
        """Given a saved DOM move, when Sync to file succeeds, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.move(page, frame)
                self.assertTrue(self.prompts(page))
                synced(self, page)
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
                synced(self, page)
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_after_sync_to_file_a_live_app_reload_does_not_make_the_page_ask(self):
        """Given every override written to the file, when the Live App reloads, then closing Studio does not ask."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                synced(self, page)
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
                synced(self, page)
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

    def shows(self, page, tab, needle):
        """Opens a code tab and waits until its output prints `needle`: the cell then rests on what the tab shows."""
        page.locator(f'#codeTab{tab}').click()
        page.wait_for_function('(s) => document.querySelector("#liveCodeOutput").textContent.includes(s)', arg=needle)

    def test_the_html_tab_carries_a_move_the_page_ledger_prints(self):
        """Given a saved move the ledger still prints, when the HTML tab is downloaded, then the page stops asking."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.move(page, frame)
                self.shows(page, 'Html', 'child order: Card C, Card A')
                self.assertTrue(self.prompts(page))
                self.download(page, 'Html')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_the_html_tab_carries_a_text_edit_the_page_ledger_prints(self):
        """Given a saved text edit the ledger still prints, when the HTML tab is downloaded, then the page stops asking."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_text(page, frame)
                self.shows(page, 'Html', 'A new headline')
                self.assertTrue(self.prompts(page))
                self.download(page, 'Html')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_the_json_tab_carries_a_style_edit_only_while_no_tokens_are_saved(self):
        """Given a style edit, when the JSON tab is downloaded, then the page stops asking; with saved tokens it still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine, tokens='none'):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.assertTrue(self.prompts(page))
                self.download(page, 'Json')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])
            with self.subTest(engine=engine, tokens='saved'):
                page, errors, frame = self.arranged(engine)
                page.locator('#btnSyncToApp').click()
                self.wait_badge(page, r'^Live · rev 1$')
                self.edit_size(page, frame)
                self.assertIn('--font-display', self.export(page)['live']['tokens'])
                self.assertTrue(self.prompts(page))
                self.download(page, 'Json')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_failed_copy_still_asks_and_a_copy_by_the_fallback_stops_asking(self):
        """Given no clipboard API, when the fallback copy fails the page still asks; when it succeeds the page stops asking."""
        for engine in ENGINES:
            for outcome, status in (('false', 'Copy failed'), ('true', 'Copied')):
                with self.subTest(engine=engine, execCommand=outcome):
                    page, errors, frame = self.arranged(engine)
                    self.edit_size(page, frame)
                    page.evaluate(f"""() => {{ Object.defineProperty(navigator, 'clipboard', {{configurable: true, value: undefined}});
                        document.execCommand = () => {outcome}; }}""")
                    self.assertTrue(self.prompts(page))
                    page.locator('#liveCodeCopy').click()
                    page.wait_for_function('(s) => document.querySelector("#liveCodeStatus").textContent.startsWith(s)', arg=status)
                    self.assertEqual(self.prompts(page), outcome == 'false')
                    self.assertEqual(errors, [])

    # -- the Composer's composition JSON ---------------------------------------
    def open_export(self, page, button='exportJson'):
        page.locator(f'#{button}').click()
        page.locator('#exportDialog').wait_for(state='visible')

    def close_export(self, page):
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')

    def save_export(self, page):
        """Downloads the dialog's text. The download event fires inside the click handler, after which the ask can be read."""
        with page.expect_download():
            page.locator('#downloadExport').click()

    def test_a_downloaded_composition_file_stops_the_ask_for_a_style_edit_a_text_edit_and_a_move(self):
        """Given one saved edit, when Export JSON is downloaded from its dialog, then the page stops asking."""
        edits = (('style', lambda case, page, frame: case.edit_size(page, frame)),
                 ('text', lambda case, page, frame: case.edit_text(page, frame)),
                 ('move', lambda case, page, frame: case.move(page, frame)))
        for engine in ENGINES:
            for name, edit in edits:
                with self.subTest(engine=engine, edit=name):
                    page, errors, frame = self.arranged(engine)
                    edit(self, page, frame)
                    self.assertTrue(self.prompts(page))
                    self.open_export(page)
                    self.save_export(page)
                    self.assertFalse(self.prompts(page))
                    self.assertEqual(errors, [])

    def test_a_downloaded_composition_file_holds_saved_tokens_too(self):
        """Given saved tokens and a style edit, when Export JSON is downloaded, then the page stops asking."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                page.locator('#btnSyncToApp').click()
                self.wait_badge(page, r'^Live · rev 1$')
                self.edit_size(page, frame)
                self.assertIn('--font-display', self.export(page)['live']['tokens'])
                self.assertTrue(self.prompts(page))
                self.open_export(page)
                self.save_export(page)
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])

    def test_copying_the_composition_file_stops_the_ask_only_when_the_copy_worked(self):
        """Given a style edit, when the dialog's Copy works the page stops asking; with no clipboard and a false execCommand it asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine, clipboard='works'):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                page.evaluate("""() => { window.__copied = null; Object.defineProperty(navigator, 'clipboard', {configurable: true,
                    value: {writeText: async (text) => { window.__copied = text; }}}); }""")
                self.open_export(page)
                self.assertTrue(self.prompts(page))
                page.locator('#copyExport').click()
                page.wait_for_function('() => document.querySelector("#copyExport").textContent === "Copied"')
                self.assertFalse(self.prompts(page))
                self.assertEqual(errors, [])
            with self.subTest(engine=engine, clipboard='gone', execCommand='false'):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                page.evaluate("""() => { window.__tried = false; Object.defineProperty(navigator, 'clipboard', {configurable: true, value: undefined});
                    document.execCommand = () => { window.__tried = true; return false; }; }""")
                self.open_export(page)
                page.locator('#copyExport').click()
                page.wait_for_function('() => window.__tried')
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_export_css_carries_nothing_even_straight_after_an_unsaved_composition_export(self):
        """Given a style edit, when Export CSS is downloaded (also after a JSON export was shown and closed), then the page still asks."""
        for engine in ENGINES:
            for first in (False, True):
                with self.subTest(engine=engine, json_shown_first=first):
                    page, errors, frame = self.arranged(engine)
                    self.edit_size(page, frame)
                    if first:
                        self.open_export(page)
                        self.close_export(page)
                    self.open_export(page, 'exportCss')
                    self.save_export(page)
                    self.assertTrue(self.prompts(page))
                    self.assertEqual(errors, [])

    def test_opening_the_composition_export_and_closing_it_unsaved_still_asks(self):
        """Given a style edit, when Export JSON is opened and closed without saving, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.open_export(page)
                self.close_export(page)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_after_saving_the_composition_file_asks_again(self):
        """Given a saved composition file, when another edit is made, then the page asks again."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.open_export(page)
                self.save_export(page)
                self.close_export(page)
                self.assertFalse(self.prompts(page))
                self.edit_size(page, frame, 60)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_a_hand_edited_composition_text_is_never_counted_as_saved(self):
        """Given the export text edited by hand, when it is downloaded, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.open_export(page)
                page.locator('#exportDialogText').fill('{}')
                self.save_export(page)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])

    def test_an_edit_acknowledged_while_the_export_is_open_still_asks_after_its_download(self):
        """Given the export open, when an edit is acknowledged and the old text is downloaded, then the page still asks."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.arranged(engine)
                self.edit_size(page, frame)
                self.open_export(page)
                self.select(page, frame, 'hero.title')
                page.evaluate("""() => { const field = document.querySelector('#liveText'); field.value = 'Typed while open';
                    field.dispatchEvent(new Event('input', {bubbles: true})); field.dispatchEvent(new Event('change', {bubbles: true})); }""")
                self.wait_badge(page, r'^Live · rev 2$')
                self.save_export(page)
                self.assertTrue(self.prompts(page))
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
