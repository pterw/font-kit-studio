"""Studio-side behaviour for the deep-review findings of Task A6 (v0.2.1).

Finding (a): a container child whose data-design-id another target already holds is not a target, and the bridge
reports '' at its place in `orderIds`. Studio keeps the container's saved order for the children it can track.
Finding (b): the bridge takes at most 16 stylesheets and treats the list as complete, so Studio says which library
families it could not send. The bridge side of (c) (case-only duplicate origins) is in test_bridge_runtime.py.

The fake target (tests/fixtures/studio/fake-target.html) reports the duplicate-id child through its
`mapStructure` hook, the way the real bridge reports it (see DuplicateIdOrderTests in test_bridge_runtime.py).
RealBridgeDuplicateIdTests runs the real Studio against the real bridge on a page with such a child.
"""

import re
import unittest

import test_live_integration as integration
import test_studio_live as studio
from support import ENGINES

CARDS = {'selector': '[data-design-id="cards"]', 'name': 'Cards'}
# The real bridge keeps the duplicate-id child in `order` (by name) and puts '' at its place in `orderIds`.
DUPLICATE_AFTER_FIRST_CARD = """() => {
    window.fake.mapStructure = e => ({...e,
        order: [e.order[0], 'DIV: "Card with a repeated id"', ...e.order.slice(1)],
        orderIds: [e.orderIds[0], '', ...e.orderIds.slice(1)]});
}"""


class DuplicateIdChildTests(studio.ArrangeCase):
    def assert_untracked_wording(self, status):
        """The child is described as not tracked (unregistered), with the possible causes named as possibilities: the
        bridge cannot tell a duplicate id from an empty or oversized one, so it never says another element uses it."""
        self.assertRegex(status, r'(?i)not tracked')
        self.assertRegex(status, r'(?i)unregistered')
        self.assertRegex(status, r'(?i)duplicate or invalid data-design-id')
        self.assertRegex(status, r'(?i)empty')
        self.assertNotRegex(status, r'(?i)another element (already )?uses')

    def move_card(self, page, frame, button, card, rev):
        self.select(page, frame, card)
        page.locator(button).click()
        self.wait_badge(page, rf'^Live · rev {rev}$')

    def test_a_dom_move_in_a_container_with_a_duplicate_id_child_is_saved_for_the_registered_children(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate(DUPLICATE_AFTER_FIRST_CARD)
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                expected = frame.evaluate('window.fake.domOrder("cards")')
                self.assertEqual(expected[0], 'card.c')
                exported = self.export(page)
                self.assertEqual(exported['live']['structure'], [{**CARDS, 'ids': expected}],
                                 'the container keeps its registered children in order and skips the untracked one')
                self.assertNotIn('', exported['live']['structure'][0]['ids'])
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible(), 'no conflict: the page holds the saved order')
                # The saved order survives export and import.
                self.assertIn('Composition imported.', self.import_document(page, exported))
                self.assertEqual(self.export(page).get('live'), exported.get('live'), 'Studio imports what it exported')
                self.assertEqual(errors, [])

    def test_reapply_after_a_reload_puts_the_registered_children_back_in_the_saved_order(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate(DUPLICATE_AFTER_FIRST_CARD)
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                saved = {**CARDS, 'ids': ['card.c', 'card.a', 'card.b', 'card.d']}
                self.assertEqual(self.export(page)['live']['structure'], [saved])
                frame.evaluate('location.reload()')
                banner = page.locator('#liveReconnectBanner')
                banner.wait_for(state='visible')
                frame = self.wait_ready(page, 11)
                frame.evaluate(DUPLICATE_AFTER_FIRST_CARD)   # the reloaded page still has the duplicate-id child
                self.assertEqual(self.dom(frame), ['card.a', 'card.b', 'card.c', 'card.d'])
                self.assertEqual(self.moves(frame), [], 'Reapply stays an explicit choice')
                page.locator('#liveReapply').click()
                banner.wait_for(state='hidden')
                frame.wait_for_function('JSON.stringify(window.fake.domOrder("cards")) === JSON.stringify(["card.c","card.a","card.b","card.d"])')
                self.assertEqual(self.export(page)['live']['structure'], [saved], 'the saved order is unchanged')
                self.assertEqual(errors, [])

    def test_the_status_says_once_per_container_that_an_element_with_a_duplicate_id_is_not_tracked(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate(DUPLICATE_AFTER_FIRST_CARD)
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assert_untracked_wording(status)
                self.assertIn('Card with a repeated id', status, 'it names the element')
                self.assertIn('Cards', status, 'and its container')
                self.assertRegex(status, r'(?i)kept in Studio', 'the move itself is still reported')
                # Once per container: the next move in the same container does not repeat it.
                self.move_card(page, frame, '#liveMoveLast', 'card.a', 2)
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assertRegex(status, r'(?i)kept in Studio')
                self.assertNotRegex(status, r'(?i)not tracked|unregistered|invalid data-design-id')
                self.assertEqual(errors, [])

    def test_a_child_with_an_empty_data_design_id_is_described_as_untracked_without_blaming_another_element(self):
        """The bridge reports '' for any child it did not register: a duplicate id, an empty one (`data-design-id=""`) or
        one over 300 characters. An empty slot does not prove a duplicate, so the status must not claim one."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate("""() => {
                    window.fake.mapStructure = e => ({...e,
                        order: [e.order[0], 'DIV: "Card with an empty id"', ...e.order.slice(1)],
                        orderIds: [e.orderIds[0], '', ...e.orderIds.slice(1)]});
                }""")
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assert_untracked_wording(status)
                self.assertIn('Card with an empty id', status)
                self.assertIn('Cards', status)
                self.assertEqual(errors, [])

    def test_a_container_without_a_duplicate_id_child_shows_no_such_text(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                self.assertNotRegex(page.locator('#liveCodeStatus').inner_text(), r'(?i)duplicate|not tracked')
                self.assertEqual(self.export(page)['live']['structure'][0]['ids'], frame.evaluate('window.fake.domOrder("cards")'))
                self.assertEqual(errors, [])

    def test_a_container_whose_every_child_is_untracked_is_not_saved(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame = self.open_arrange(engine)
                frame.evaluate("() => { window.fake.mapStructure = e => ({...e, order: e.order.map(() => 'DIV'),"
                               " orderIds: e.orderIds.map(() => '')}); }")
                self.move_card(page, frame, '#liveMoveFirst', 'card.c', 1)
                self.assertNotIn('live', self.export(page))
                self.assertRegex(page.locator('#liveCodeStatus').inner_text(), r'(?i)not saved')
                self.assertEqual(errors, [])


class RealBridgeDuplicateIdTests(integration.LiveIntegrationCase):
    """The real Studio against the real bridge (served by scripts/serve.py) on the bridge's arrangement fixture, with a
    second paragraph that repeats `arr.p.1`'s data-design-id added to the container `arr.plain`."""
    PAGE = 'tests/fixtures/bridge/target-arrange.html'
    FIRST = '<p data-design-id="arr.p.1">Plain one</p>'
    DUPLICATE = '<p data-design-id="arr.p.1">Plain one again</p>'
    # Registered children and the duplicate, in DOM order, as (id, text).
    CHILDREN = """() => [...document.querySelectorAll('[data-design-id="arr.plain"] > p')]
        .map(el => [el.getAttribute('data-design-id'), el.textContent.trim()])"""

    def setUp(self):
        super().setUp()
        self.target = f'http://localhost:{self.target_port}/{self.PAGE}'

        def inject(route):
            response = route.fetch()
            body = response.text()
            self.assertIn(self.FIRST, body)
            route.fulfill(response=response, body=body.replace(self.FIRST, self.FIRST + '\n    ' + self.DUPLICATE))

        self.runtime_context_hook = lambda context: context.route(f'{self.target}*', inject)

    def children(self, frame):
        return frame.evaluate(self.CHILDREN)

    def test_a_dom_move_beside_a_duplicate_id_child_is_saved_reported_and_reapplied_after_a_reload(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.connected(engine)
                frame = self.frame(page)
                self.assertEqual(self.children(frame), [['arr.p.1', 'Plain one'], ['arr.p.1', 'Plain one again'],
                                                        ['arr.p.2', 'Plain two'], ['arr.p.3', 'Plain three']])
                self.click_in_target(page, '[data-design-id="arr.p.3"]', 'arr.p.3')
                page.locator('#liveMoveFirst').click()
                self.wait_badge(page, r'^Live · rev 1$')
                after_move = self.children(frame)
                self.assertEqual(after_move[0], ['arr.p.3', 'Plain three'])

                structure = self.export(page)['live']['structure']
                self.assertEqual(len(structure), 1)
                self.assertEqual(structure[0]['ids'], ['arr.p.3', 'arr.p.1', 'arr.p.2'], 'the registered children, in order')
                name = structure[0]['name']
                status = ' '.join(page.locator('#liveCodeStatus').inner_text().split())
                self.assertRegex(status, r'(?i)not tracked')
                self.assertRegex(status, r'(?i)duplicate or invalid data-design-id')
                self.assertNotRegex(status, r'(?i)another element (already )?uses')
                self.assertIn(f'in "{name}"', status, 'the status names the container')
                self.assertIn('Plain one again', status, 'and the element')
                self.assertRegex(status, r'(?i)kept in Studio')
                self.assertFalse(page.locator('#liveReconnectBanner').is_visible())

                # After a reload the page has the original order; Reapply puts the registered children back.
                frame = self.reload_target(page)
                self.assertEqual([c[0] for c in self.children(frame)], ['arr.p.1', 'arr.p.1', 'arr.p.2', 'arr.p.3'])
                page.locator('#liveReapply').click()
                page.locator('#liveReconnectBanner').wait_for(state='hidden')
                self.wait_badge(page, r'^Live · rev \d+$')
                replayed = self.children(frame)
                self.assertEqual([c[1] for c in replayed if c[1] != 'Plain one again'],
                                 ['Plain three', 'Plain one', 'Plain two'], 'the registered children are in the saved order')
                self.assertEqual(self.export(page)['live']['structure'], structure, 'the saved order is unchanged')
                # The untracked child is not Studio's state: Reapply places the registered ids at indexes 0..n-1, so it
                # ends up after them rather than between arr.p.1 and arr.p.2 as before the reload.
                self.assertEqual([c[1] for c in replayed].index('Plain one again'), 3, 'observed: it was at index 2 before the reload')
                self.assertEqual(page.errors, [])


class SheetLimitTests(studio.LiveCase):
    """The bridge refuses more than 16 stylesheets. The library has exactly 16 families with a stylesheet today, so the
    page adds more to `fonts` (as a larger library would) before the composition names them."""
    NOTE = re.compile(r'Not sent to the page \(16-sheet limit\): ([^.]*)')

    def composition(self, count):
        """Up to four text slots (they name the composition's font tokens), then rows of up to four children: `count`
        distinct library families in composition order. A row never ends up with one child (it would be padded)."""
        families = [f'extra-{i}' for i in range(1, count + 1)]
        roles = ['Display', 'Body', 'Editorial', 'Mono']
        slots = [{'type': 'text', 'role': roles[at], 'family': family, 'text': family} for at, family in enumerate(families[:4])]
        rest = families[4:]
        while rest:
            size = 3 if len(rest) == 5 else min(4, len(rest))
            chunk, rest = rest[:size], rest[size:]
            slots.append({'type': 'row', 'childCount': len(chunk),
                          'children': [{'type': 'text', 'role': 'Body', 'family': family, 'text': family} for family in chunk]})
        return {'composition': {'canvasWidth': '960', 'slots': slots}}

    def sync_with(self, engine, count, ask=True):
        page, errors = self.open(engine)
        self.wait_connected(page)
        frame = self.frame(page)
        if ask:
            page.locator('#loadFreeFonts').click()
        page.evaluate("(count) => { for (let i = 1; i <= count; i++) fonts.push({ ...fonts[0], name: 'Extra ' + i,"
                      " family: 'extra-' + i, css: 'Extra ' + i, sheet: 'Extra+' + i + ':wght@400' }); }", count)
        self.assertIn('Composition imported.', self.import_document(page, self.composition(count)))
        page.locator('#btnSyncToApp').click()
        return page, errors, frame, self.wait_first_slot(frame, 1)

    def streamed(self, frame):
        return [u['patch'] for u in self.updates(frame) if 'targetId' not in u and 'slots' in u['patch']]

    def wait_first_slot(self, frame, index):
        """Waits for a streamed composition whose first slot uses library family `Extra <index>` and returns the last
        such patch. A condition, not a count: Studio may stream an unchanged update before the one that carries an edit."""
        pattern = rf'Extra {index}(?!\d)'
        frame.wait_for_function(
            '(re) => window.__received.some(i => i.data && i.data.type === "design:update" && i.data.targetId === undefined'
            ' && i.data.patch && i.data.patch.slots && i.data.patch.slots[0] && new RegExp(re).test(i.data.patch.slots[0].fontFamily || ""))',
            arg=pattern, polling=50)
        return [patch for patch in self.streamed(frame)
                if re.search(pattern, patch['slots'][0].get('fontFamily') or '')][-1]

    def sheet_for(self, index):
        return f'https://fonts.googleapis.com/css2?family=Extra+{index}:wght@400&display=swap'

    def test_seventeen_families_send_sixteen_sheets_in_composition_order_and_the_status_names_the_rest(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame, patch = self.sync_with(engine, 19)
                self.assertEqual(patch['fontStylesheets'], [self.sheet_for(i) for i in range(1, 17)], 'exactly 16, in composition order')
                status = page.locator('#composerStatus').inner_text()
                self.assertIn('Composition sent to the live app.', status)
                match = self.NOTE.search(status)
                self.assertIsNotNone(match, status)
                self.assertEqual(match.group(1).strip(), 'Extra 17, Extra 18, Extra 19')
                self.assertNotIn('Extra 16', match.group(1))
                self.assertEqual(errors, [])

    def test_the_family_past_the_limit_is_named_when_the_composition_has_exactly_seventeen(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame, patch = self.sync_with(engine, 17)
                self.assertEqual(len(patch['fontStylesheets']), 16)
                self.assertEqual(self.NOTE.search(page.locator('#composerStatus').inner_text()).group(1).strip(), 'Extra 17')
                self.assertEqual(errors, [])

    def test_a_linked_edit_stops_the_status_naming_families_once_everything_is_sent(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame, _ = self.sync_with(engine, 17)
                self.assertIn('Extra 17', page.locator('#composerStatus').inner_text())
                # The first slot takes the second slot's family: 16 distinct families are left, and all of them fit.
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
                page.locator('#slotInspector [data-bind="family"]').select_option('extra-2')
                sent = self.wait_first_slot(frame, 2)['fontStylesheets']
                self.assertEqual(len(sent), 16)
                self.assertIn(self.sheet_for(17), sent)
                page.wait_for_function("() => /sent to the page again/.test(document.querySelector('#composerStatus').textContent)")
                status = page.locator('#composerStatus').inner_text()
                self.assertIn('Composition sent to the live app.', status, 'what Sync said stays')
                self.assertIn('sent to the page again', status)
                self.assertNotIn('Extra 17', status)
                self.assertNotRegex(status, r'(?i)not sent')
                self.assertEqual(errors, [])

    def test_the_consent_re_send_keeps_the_families_left_out_in_the_status(self):
        """Synced before the ask, the first send has no sheets; Load free fonts re-sends the set and then reports its
        own progress, which must not hide the families that did not fit."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, frame, patch = self.sync_with(engine, 17, ask=False)
                self.assertNotIn('fontStylesheets', patch, 'nothing is sent before the ask')
                self.assertNotRegex(page.locator('#composerStatus').inner_text(), r'(?i)not sent to the page')
                page.locator('#loadFreeFonts').click()
                frame.wait_for_function(
                    '() => window.__received.some(i => i.data && i.data.type === "design:update" && i.data.patch'
                    ' && Array.isArray(i.data.patch.fontStylesheets) && i.data.patch.fontStylesheets.length === 16)', polling=50)
                # Offline, every stylesheet fails and the progress line settles on its last wording.
                page.wait_for_function("() => /could not load/.test(document.querySelector('#composerStatus').textContent)")
                status = page.locator('#composerStatus').inner_text()
                self.assertRegex(status, r'Loaded 0/\d+ free font stylesheets')
                match = self.NOTE.search(status)
                self.assertIsNotNone(match, status)
                self.assertEqual(match.group(1).strip(), 'Extra 17')
                self.assertEqual(errors, [])

    def test_sixteen_families_or_fewer_send_every_sheet_and_the_status_has_no_such_text(self):
        for engine in ENGINES:
            for count in (16, 3):
                with self.subTest(engine=engine, count=count):
                    page, errors, frame, patch = self.sync_with(engine, count)
                    self.assertEqual(patch['fontStylesheets'], [self.sheet_for(i) for i in range(1, count + 1)])
                    status = page.locator('#composerStatus').inner_text()
                    self.assertIn('Composition sent to the live app.', status)
                    self.assertNotRegex(status, r'(?i)not sent|sheet limit')
                    self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
