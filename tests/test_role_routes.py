"""Studio's session-only visited-page role evidence (R2.6S phases A to C): the collection, the roles-page reader, the limits,
the four page states, the new-document and new-origin notices and Clear visited pages.

Peers stand in for a bridge (the helpers of test_studio_roles); the last two classes run the real bridge on the multi-page
fixture. Expected values are literals, the contract table and the fixture oracle (fixtures/multi-page/expected-styles.json).

Unknown reply keys are never stored: no test here pins that by name. The tolerant-reply test of test_studio_roles runs a
roles-page through the same panel, request and export comparison as the other kinds, and the mutant "the snapshot keeps the
reply's groups as they came" changes nothing a user or the wire can observe, so it is recorded as equivalent, not covered.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

import role_contract as table
from support import REPO
from test_studio_roles import (APPLY, HERO_LEAD, HYBRID_URL, PEER, PEER_URL, STYLE, TARGET, UNAVAILABLE, UNREADABLE_DETECT,
                               UNSUPPORTED, StudioRoleCase, group, hybrid_page, per_engine)

CHANGED = 'The page changed since the last Detect; press Detect text styles. This page has not been checked.'
STALE_REPLY = "The page's reply to Detect was out of date; press Detect text styles again; this page has not been checked."
LIMIT = 'Collection limit reached; this page was not stored'
LIMIT_HINT = 'Collection limit reached, so Apply is disabled until you clear visited pages.'
NOT_APPLIED = 'Role preview is not applied on this page.'
NEW_ORIGIN = 'A new Live App origin started a new collection; visited pages from the previous origin were cleared.'
CLEARED = 'Visited pages cleared. The applied preview and inspector edits stay.'
CLEAR_VISITED = 'Clear visited pages'
WEIGHT = '() => getComputedStyle(document.querySelector(".shared-title")).fontWeight'
REJECTED = 'Role detection rejected (unsupported-value); this page has not been checked.'
READY = 'Ready to detect text styles.'
MULTI = '/fixtures/multi-page/'
INVENTORY = '''() => [...document.querySelectorAll('#roleInventory > li')].map(li => {
  const lists = [...li.querySelectorAll('ul[data-role-pages]')].map(ul => [ul.dataset.rolePages, {heading: ul.previousElementSibling.textContent,
    entries: [...ul.children].map(entry => ({route: entry.firstChild.textContent, lines: [...entry.querySelectorAll('p')].map(p => p.textContent)}))}]);
  return {id: li.dataset.inventoryRole, title: li.querySelector('strong').textContent, states: Object.fromEntries(lists),
    checked: Object.fromEntries(lists).checked?.entries ?? []};
})'''
HEADINGS = {'checked': 'Checked on:', 'no-match': 'No match on:', 'conflict': 'Different style on:', 'changed': 'Changed since checked:'}


def visited(count):
    return f'Checked on {count} visited page{"" if count == 1 else "s"}. Other pages have not been checked.'


def sel(*values):
    return [{'value': value, 'stable': True, 'reason': 'class'} for value in values]


def styled(size, **changes):
    return {**STYLE, 'fontSize': size, **changes}


def author(name, styles, *selectors, group_id=None):
    """An author-role group whose variants are `styles`, one element each."""
    found = group(group_id or 'g-' + name, name, name, styles[0], sel(*selectors))
    found['signatures'] = [{'style': style, 'count': 1} for style in styles]
    found['elementCount'] = len(styles)
    return found


def tuple_text(style):
    """The oracle's tuple text for a fixture signature (the format of the approved strings)."""
    return f'{style["fontFamily"]}: {style["fontSize"]}px / {style["fontWeight"]} / {style["textTransform"]} / {style["letterSpacing"]}em'


ORACLE = json.loads((REPO / 'fixtures' / 'multi-page' / 'expected-styles.json').read_text(encoding='utf-8'))['signatures']
BASE_TITLE, SAME_TITLE = tuple_text(ORACLE['base-title']), tuple_text(ORACLE['same-title'])


class RouteCase(StudioRoleCase):
    def peer(self, engine, **options):
        self.version = 0
        return self.open(engine, TARGET + '/peer', PEER, **options)

    def probes(self, request, found):
        """A complete reply's selector checks: for each (role, selector) the request named, the (style, count) pairs in `found`."""
        return [{'roleId': role['id'], 'selector': selector, 'matchCount': sum(count for _, count in found.get((role['id'], selector), [])),
                 'signatures': [{'style': style, 'count': count} for style, count in found.get((role['id'], selector), [])]}
                for role in request['knownRoles'] for selector in role['selectors']]

    def visit(self, page, frame, path, groups, found=None, **changes):
        """One complete Detect for the route `path`, one page version after the last; returns once Studio has handled it.
        With `found`, every known selector is checked as that dict says (nothing found unless listed)."""
        self.version += 1
        url = TARGET + path
        request = self.pending(page, frame)
        if found is not None:
            changes['selectorChecks'] = self.probes(request, found)
        self.send(frame, self.reply(request, groups, pageVersion=self.version, currentPageVersion=self.version,
                                    pageURL=url, currentPageURL=url, **changes))
        self.settle(page, frame)
        self.settle(page, frame)
        return request

    def page_message(self, frame, version, url=PEER_URL, **changes):
        self.send(frame, {'type': 'design:roles-page', 'documentId': 'peer-document', 'pageVersion': version, 'pageURL': url, **changes})

    def inventory(self, page):
        return page.evaluate(INVENTORY)

    def pages(self, page, role):
        """The routes listed as checked for `role` (the entries' own text)."""
        return [entry['route'] for item in self.inventory(page) if item['id'] == role for entry in item['checked']]

    def listed(self, page, role):
        """The route labels under each state heading of `role`'s inventory entry, by state."""
        found = [item for item in self.inventory(page) if item['id'] == role]
        self.assertEqual(len(found), 1, (role, found))
        for state, shown in found[0]['states'].items():
            self.assertEqual(shown['heading'], HEADINGS[state])
        return {state: [entry['route'] for entry in shown['entries']] for state, shown in found[0]['states'].items()}

    def lines(self, page, role, state):
        """The detail lines of every route entry under one state heading of `role`."""
        item = next(item for item in self.inventory(page) if item['id'] == role)
        return [entry['lines'] for entry in item['states'][state]['entries']]

    def reload_peer(self, page, frame):
        frame.evaluate('setTimeout(() => location.reload(), 0)')
        self.wait_status(page, READY)
        self.settle(page, frame)

    def status(self, page):
        return page.locator('#roleStatus').inner_text()

    def visited_text(self, page):
        node = page.locator('#roleVisited')
        return node.inner_text() if node.is_visible() else ''

    def apply_preview(self, page, frame):
        """Detect, then Apply a size on the Body role and let its receipt settle."""
        self.detected(page, frame)
        self.send(frame, self.receipt(self.apply_role(page, frame)))
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("Preview applied to 1 role")')

    def notice(self, page):
        node = page.locator('#roleNotice')
        return node.inner_text() if node.is_visible() else ''

    def frozen_clock(self, page):
        page.clock.install(time=0)
        page.clock.pause_at(1000)

    def wait_status(self, page, text):
        page.wait_for_function('(t) => document.querySelector("#roleStatus").textContent === t', arg=text, timeout=6000)

    def wait_not_detecting(self, page):
        page.wait_for_function('!document.querySelector("#roleStatus").textContent.startsWith("Detecting")', timeout=6000)


class RolesPageReaderTests(RouteCase):
    @per_engine
    def test_a_stale_valid_reply_says_so_stores_nothing_and_survives_the_timer(self, engine):
        """Given an Apply in flight and a Detect pending, when a receipt advances the page version and the Detect's valid
        reply for the older version arrives, then the status is the out-of-date sentence, still so after 9,000 ms, and the
        visited count and inventory are unchanged."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        self.frozen_clock(page)
        apply = self.apply_role(page, frame, '24')
        request = self.pending(page, frame)
        self.send(frame, self.receipt(apply, [], currentPageVersion=1, outcomesComplete=False, outcomeReason='page-changed'))
        self.wait_status_preview(page)
        self.send(frame, self.reply(request, [group(name='Stale', author='Stale')]))
        self.wait_status(page, STALE_REPLY)
        page.clock.run_for(9000)
        self.assertEqual(self.status(page), STALE_REPLY)
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual([item['id'] for item in self.inventory(page)], ['role-1'])
        self.assertEqual(errors, [])

    def wait_status_preview(self, page):
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("page changed before checks finished")')

    @per_engine
    def test_a_valid_roles_page_moves_the_page_version_and_says_the_page_changed(self, engine):
        """Given a stored Detect, when a valid roles-page arrives for the same URL at version 3, plain or with an unknown
        key, then the status is the page-changed sentence, the row stays, and the next Apply carries pageVersion 3."""
        for name, wrap in (('plain', lambda message: message), ('unknown key', lambda message: table.with_unknown_keys(message))):
            with self.subTest(message=name):
                page, frame, errors = self.peer(engine)
                self.detected(page, frame)
                self.send(frame, wrap({'type': 'design:roles-page', 'documentId': 'peer-document', 'pageVersion': 3, 'pageURL': PEER_URL}))
                self.wait_status(page, CHANGED)
                self.assertEqual(page.locator('#roleRows > li').count(), 1)
                self.assertEqual(self.apply_role(page, frame, '24')['pageVersion'], 3)
                self.assertEqual(errors, [])

    @per_engine
    def test_a_roles_page_during_a_pending_detect_leaves_the_pending_text_alone(self, engine):
        """Given a stored Detect and a pending one, when a roles-page for version 1 arrives, then the status stays
        'Detecting text styles…' and the Detect's reply for version 1 then renders."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        request = self.pending(page, frame)
        self.page_message(frame, 1)
        self.settle(page, frame)
        self.assertEqual(self.status(page), 'Detecting text styles…')
        self.send(frame, self.reply(request, pageVersion=1, currentPageVersion=1))
        page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected")')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_roles_page_repeating_the_stored_page_says_nothing_and_a_newer_one_says_changed(self, engine):
        """Given a stored Detect at version 0, when a roles-page repeats version 0 and the same URL and then one arrives for
        version 1, then after the first the status and the Checked on list are unchanged, and after the second the status
        is the page-changed sentence."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        before = self.status(page)
        self.assertTrue(before.startswith('Detected'))
        self.page_message(frame, 0)
        self.settle(page, frame)
        self.settle(page, frame)
        self.assertEqual(self.status(page), before)
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/peer']})
        self.page_message(frame, 1)
        self.wait_status(page, CHANGED)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_supported_page_after_an_unsupported_one_says_ready_without_a_route_and_changed_with_one(self, engine):
        """Given an unsupported-URL roles-page, when a roles-page with a supported URL follows, then with no stored route the
        status is 'Ready to detect text styles.' and Detect is enabled, and with a stored route it is the page-changed
        sentence and Detect is enabled."""
        for name in ('no stored route', 'a stored route'):
            with self.subTest(case=name):
                page, frame, errors = self.peer(engine)
                if name == 'a stored route':
                    self.detected(page, frame)
                self.page_message(frame, 1, None)
                self.wait_status(page, UNAVAILABLE)
                self.page_message(frame, 2)
                self.wait_status(page, CHANGED if name == 'a stored route' else READY)
                self.assertTrue(self.button(page, 'Detect text styles').is_enabled())
                self.assertEqual(errors, [])

    @per_engine
    def test_a_roles_page_before_any_valid_ready_is_ignored(self, engine):
        """Given a ready that failed validation, so Studio holds no page identity, when a valid-looking roles-page arrives,
        then the status stays the unsupported-bridge text, Detect stays disabled and the page raises no error."""
        page, frame, errors = self.peer(engine)
        self.ready_with(page, frame, self.snapshot_state([], cssHash='00000000'))
        self.wait_status(page, UNSUPPORTED)
        self.page_message(frame, 1)
        self.settle(page, frame)
        self.settle(page, frame)
        self.assertEqual(self.status(page), UNSUPPORTED)
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(errors, [])

    @per_engine
    def test_a_hostile_roles_page_changes_nothing(self, engine):
        """Given a stored route, a changed page at version 1 and a rejected Detect, when each hostile roles-page arrives,
        then the status stays the rejection text, and the next Apply still carries pageVersion 1."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        self.page_message(frame, 1)
        self.wait_status(page, CHANGED)
        request = self.pending(page, frame)
        self.send(frame, {'type': 'design:rejected', 'requestId': request['requestId'], 'revision': 0, 'reason': 'unsupported-value'})
        self.wait_status(page, REJECTED)
        session = frame.evaluate('session')
        sized = {'type': 'design:roles-page', 'protocolVersion': 1, 'sessionId': session, 'documentId': 'peer-document',
                 'pageVersion': 9, 'pageURL': PEER_URL}
        padding = table.REPLY_BYTES + 1 - table.wire({**sized, table.UNKNOWN_KEY: ''})
        base = {'type': 'design:roles-page', 'documentId': 'peer-document', 'pageVersion': 9, 'pageURL': PEER_URL}
        rows = {'the same version with another URL': ({'pageVersion': 1, 'pageURL': TARGET + '/other'}, {}),
                'an older version': ({'pageVersion': 0}, {}), 'another document': ({'documentId': 'other-document'}, {}),
                'a foreign origin': ({'pageURL': 'http://evil.test/peer'}, {}),
                'credentials in the URL': ({'pageURL': 'http://user:secret@target.test/peer'}, {}),
                'an array where the URL belongs': ({'pageURL': [PEER_URL]}, {}), 'a __proto__ key': ({'__proto__': {}}, {}),
                'a nonfinite number inside an unknown key': ({table.UNKNOWN_KEY: float('inf')}, {}),
                '__proto__ inside an unknown key': ({table.UNKNOWN_KEY: {'__proto__': {}}}, {}),
                'constructor inside an unknown key': ({table.UNKNOWN_KEY: {'constructor': {}}}, {}),
                'prototype inside an unknown key': ({table.UNKNOWN_KEY: {'prototype': {}}}, {}),
                'one byte over 1 MiB': ({table.UNKNOWN_KEY: 'x' * padding}, {}),
                'another session': ({}, {'sessionId': 'wrong-session'}), 'another protocol': ({}, {'protocolVersion': 2})}
        # The rows share one session: after a wrongly accepted row the later rows also fail, so the first failing row names the fault.
        for name, (change, envelope) in rows.items():
            with self.subTest(message=name):
                self.send(frame, {**base, **change}, **envelope)
                self.settle(page, frame)
                self.settle(page, frame)
                self.assertEqual(self.status(page), REJECTED)
        self.assertEqual(self.apply_role(page, frame, '24')['pageVersion'], 1)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_null_page_url_clears_the_rows_and_keeps_the_earlier_inventory(self, engine):
        """Given a stored route, when a roles-page with a null URL arrives, then the rows are gone, Detect and Apply are
        disabled with the unsupported-URL text, the visited count stays, and the role's route moves from the checked list
        to the changed list."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        self.page_message(frame, 1, None)
        self.wait_status(page, UNAVAILABLE)
        self.assertEqual(page.locator('#roleRows > li').count(), 0)
        self.assertTrue(self.button(page, 'Detect text styles').is_disabled())
        self.assertEqual(self.gate(page), (False, UNAVAILABLE))
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual(self.listed(page, 'role-1'), {'changed': ['/peer']})
        self.assertEqual(errors, [])

    @per_engine
    def test_a_detect_reply_for_an_older_request_stores_nothing(self, engine):
        """Given two Detects pressed in turn, when the reply to the first arrives, then no visited count or inventory
        shows; the reply to the second then stores the route."""
        page, frame, errors = self.peer(engine)
        old = self.pending(page, frame)
        current = self.pending(page, frame)
        self.send(frame, self.reply(old, [group(name='Old', author='Old')]))
        self.settle(page, frame)
        self.settle(page, frame)
        self.assertEqual((self.visited_text(page), self.inventory(page)), ('', []))
        self.send(frame, self.reply(current))
        page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected")')
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual(errors, [])


class CollectionTests(RouteCase):
    @per_engine
    def test_equal_styles_on_two_routes_keep_one_id_and_each_selector(self, engine):
        """Given the same style identity on two routes under different selectors, the second page showing that style at
        the selector the first route named, when the second route is stored, then one role-1 lists both routes as checked
        and the next Detect names role-1 with both selectors."""
        page, frame, errors = self.peer(engine)
        style = styled(22)
        self.visit(page, frame, '/one', [group('a', 'Heading', None, style, sel('.a'))])
        self.visit(page, frame, '/two', [group('b', 'Heading', None, style, sel('.b'))], found={('role-1', '.a'): [(style, 1)]})
        self.assertEqual([item['title'] for item in self.inventory(page)], ['sans-serif: 22px / 400 / none / 0em (role-1)'])
        self.assertEqual(self.pages(page, 'role-1'), ['/one', '/two'])
        self.assertEqual(self.pending(page, frame)['knownRoles'], [{'id': 'role-1', 'selectors': ['.a', '.b']}])
        self.assertEqual(errors, [])

    @per_engine
    def test_duplicate_names_reordering_and_near_duplicates_keep_distinct_stable_ids(self, engine):
        """Given two groups with one suggested name that flag each other as near duplicates, when a later route lists
        them reversed with a third, then they keep role-1 and role-2, the third is role-3, and the rows and the
        inventory use those ids."""
        page, frame, errors = self.peer(engine)
        alpha, beta = group('a', 'Body', 'Alpha'), group('b', 'Body', 'Beta')
        alpha['nearDuplicateIds'], beta['nearDuplicateIds'] = ['b'], ['a']
        self.visit(page, frame, '/one', [alpha, beta])
        self.assertEqual(page.locator('#roleRows > li').evaluate_all('els => els.map(e => e.dataset.roleId)'), ['role-1', 'role-2'])
        self.visit(page, frame, '/two', [beta, alpha, group('c', 'Body', 'Gamma')])
        self.assertEqual(page.locator('#roleRows > li').evaluate_all('els => els.map(e => e.dataset.roleId)'), ['role-2', 'role-1', 'role-3'])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Alpha (role-1)', 'Beta (role-2)', 'Gamma (role-3)'])
        self.assertEqual(self.pages(page, 'role-1'), ['/one', '/two'])
        self.assertEqual(errors, [])

    @per_engine
    def test_author_names_differing_by_case_or_unicode_form_are_separate_roles(self, engine):
        """Given author roles Body, body, a precomposed e-acute and a decomposed e plus accent, when they are detected,
        then four roles role-1 to role-4 are listed under their own names."""
        page, frame, errors = self.peer(engine)
        names = ['Body', 'body', 'é', 'é']
        self.visit(page, frame, '/one', [group(f'g{i}', name, name) for i, name in enumerate(names)])
        self.assertEqual([item['title'] for item in self.inventory(page)], [f'{name} (role-{i + 1})' for i, name in enumerate(names)])
        self.assertEqual(errors, [])

    @per_engine
    def test_author_role_variants_stay_visible_in_the_row_and_the_inventory(self, engine):
        """Given an author role with two variants, when it is stored, then its row and its route entry list both as
        'count x tuple' (the row with the multiplication sign)."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/one', [author('Lead', [styled(16), styled(24)], '.lead')])
        row = page.locator('#roleRows > li').inner_text()
        self.assertIn('1 × sans-serif: 16px / 400 / none / 0em', row)
        self.assertIn('1 × sans-serif: 24px / 400 / none / 0em', row)
        self.assertEqual(self.inventory(page)[0]['checked'], [{'route': '/one', 'lines': [
            '1 x sans-serif: 16px / 400 / none / 0em', '1 x sans-serif: 24px / 400 / none / 0em']}])
        self.assertEqual(errors, [])


class RouteKeyTests(RouteCase):
    @per_engine
    def test_query_order_and_hash_make_separate_routes_in_first_visit_order(self, engine):
        """Given the routes ?a=1&b=2 and ?b=2&a=1, the first also with #keep and #keep2 and the second also with #keep, when
        each is stored, then five routes are counted and role-1 lists the five route labels in first-visit order."""
        paths = ['/peer?a=1&b=2', '/peer?b=2&a=1', '/peer?a=1&b=2#keep', '/peer?b=2&a=1#keep', '/peer?a=1&b=2#keep2']
        page, frame, errors = self.peer(engine)
        self.assertEqual(self.visited_text(page), '')
        for path in paths:
            self.visit(page, frame, path, [group()])
        self.assertEqual(self.visited_text(page), visited(5))
        self.assertEqual(self.pages(page, 'role-1'), paths)
        self.assertEqual(errors, [])

    @per_engine
    def test_a_2000_character_route_is_accepted_and_its_label_wraps(self, engine):
        """Given a route whose path is 2,000 characters, when it is stored, then its label is listed and the roles panel
        does not scroll sideways at 1440 and at 390 pixels."""
        path = '/' + 'x' * 1999
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, path, [group()])
        self.assertEqual(self.pages(page, 'role-1'), [path])
        for width in (1440, 390):
            with self.subTest(width=width):
                page.set_viewport_size({'width': width, 'height': 1100})
                self.assertTrue(page.locator('#detectedRoles').evaluate('el => el.scrollWidth <= el.clientWidth'))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_revisit_replaces_the_route_and_keeps_its_place(self, engine):
        """Given a route listing roles X and Y and a later route listing X where Y is not found, when the first is detected
        again with only X and Y not found, then the count stays 2, Y lists neither route as checked (both under no match),
        and X lists /one before /two as checked."""
        page, frame, errors = self.peer(engine)
        x, y = group('x', 'X', 'X'), group('y', 'Y', 'Y')
        only_x = {('role-1', '.body-copy'): [(STYLE, 1)]}
        self.visit(page, frame, '/one', [x, y])
        self.visit(page, frame, '/two', [x], found=only_x)
        self.visit(page, frame, '/one', [x], found=only_x)
        self.assertEqual(self.visited_text(page), visited(2))
        self.assertEqual((self.pages(page, 'role-1'), self.pages(page, 'role-2')), (['/one', '/two'], []))
        self.assertEqual(self.listed(page, 'role-2'), {'no-match': ['/one', '/two']})
        self.assertEqual(errors, [])


class LimitTests(RouteCase):
    def refused(self, page, frame, groups, path, kept):
        """A complete Detect that must be refused: the limit text, the earlier count and the BASE Apply hint, rows still shown."""
        self.visit(page, frame, path, groups)
        self.assertEqual(self.status(page), LIMIT)
        self.assertEqual(self.visited_text(page), visited(kept))
        self.assertEqual(page.locator('#roleRows > li').count(), len(groups))
        self.assertEqual(self.gate(page), (False, LIMIT_HINT))

    @per_engine
    def test_each_limit_refuses_only_the_new_route_and_consumes_no_id(self, engine):
        """Given a collection at 32 routes, at 128 roles, at 32 selectors of one role and at 8 reference styles of one
        role, when one more arrives, then the limit text shows, the earlier count stays, Apply is disabled with the
        limit hint, the next accepted new role takes the next id, and a refused 33rd route lists the last stored route
        under the changed heading."""
        fresh = group('f', 'Fresh', 'Fresh')
        with self.subTest(limit='33rd route'):
            page, frame, errors = self.peer(engine)
            for index in range(32):
                self.visit(page, frame, f'/r{index}', [group()])
            self.refused(page, frame, [group(), fresh], '/r32', 32)
            self.assertEqual(self.listed(page, 'role-1'), {'checked': [f'/r{index}' for index in range(31)], 'changed': ['/r31']})
            self.visit(page, frame, '/r0', [group(), fresh])
            self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)', 'Fresh (role-2)'])
        with self.subTest(limit='129th role'):
            page, frame, errors = self.peer(engine)
            self.visit(page, frame, '/r0', [group(f'g{i}', f'R{i}', f'R{i}') for i in range(table.ROLES)])
            self.refused(page, frame, [fresh], '/r1', 1)
            self.assertEqual(len(self.inventory(page)), table.ROLES)
        with self.subTest(limit='33rd selector'):
            page, frame, errors = self.peer(engine)
            self.visit(page, frame, '/r0', [author('Body', [STYLE], *table.selectors(table.SELECTORS))])
            self.refused(page, frame, [author('Body', [STYLE], '.s0', '.extra'), fresh], '/r1', 1)
            self.visit(page, frame, '/r1', [author('Body', [STYLE], '.s0'), fresh])
            self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)', 'Fresh (role-2)'])
        with self.subTest(limit='9th reference style'):
            page, frame, errors = self.peer(engine)
            self.visit(page, frame, '/r0', [author('Body', [styled(10 + i) for i in range(4)], '.a')])
            self.refused(page, frame, [author('Body', [styled(20 + i) for i in range(5)], '.b'), fresh], '/r1', 1)
            self.visit(page, frame, '/r1', [author('Body', [styled(20 + i) for i in range(3)], '.b'), fresh])
            self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)', 'Fresh (role-2)'])
            self.assertEqual(errors, [])


class RequestBoundaryTests(RouteCase):
    def long(self, number, length=table.SELECTOR_CHARS):
        """A valid class selector of `length` characters, distinct for each `number`."""
        tag = f'.n{number}x'
        return tag + 'a' * (length - len(tag))

    def size(self, session, roles):
        """The UTF-8 bytes of the Detect request the candidate collection would produce (Python's own encoder)."""
        request = {'type': 'design:detect', 'protocolVersion': 1, 'sessionId': session, 'requestId': 'fks-detect-9007199254740991',
                   'documentId': '\u0000' * table.DOCUMENT_ID_CHARS, 'knownRoles': roles}
        return len(json.dumps(request, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))

    def roles_for(self, session, extra):
        """The seed role and 100 more with one 2,000-character selector each; role-2 also holds enough selectors for the
        whole request to be `extra` bytes over 256 KiB."""
        roles = [{'id': 'role-1', 'selectors': ['.body-copy']}]
        roles += [{'id': f'role-{i + 2}', 'selectors': [self.long(0)]} for i in range(100)]
        spare = table.REQUEST_BYTES + extra - self.size(session, roles) - 6      # two more selectors, 3 bytes of syntax each
        fulls = max(0, -(-(spare - 3998) // 2003))
        roles[1]['selectors'] += [self.long(1 + i) for i in range(fulls)]
        spare -= fulls * 2003
        self.assertTrue(4 <= spare <= 3998, spare)
        roles[1]['selectors'] += [self.long(90, spare // 2), self.long(91, spare - spare // 2)]
        self.assertEqual(self.size(session, roles), table.REQUEST_BYTES + extra)
        return roles

    def session_with(self, engine, extra):
        """A session holding the seed route, then the big route sized `extra` bytes over the contract's limit."""
        page, frame, errors = self.peer(engine)
        self.ready_with(page, frame, self.snapshot_state([], documentId='\u0000' * table.DOCUMENT_ID_CHARS))
        self.visit(page, frame, '/seed', [group('s', 'Seed', None, STYLE, sel('.body-copy'))])
        roles = self.roles_for(frame.evaluate('session'), extra)
        self.visit(page, frame, '/big', [author(f'Big{i}', [STYLE], *role['selectors']) for i, role in enumerate(roles[1:])])
        return page, frame, errors, roles

    @per_engine
    def test_a_request_of_exactly_256_kib_is_stored_and_one_byte_more_is_refused(self, engine):
        """Given a collection whose next Detect request, with a 200-unit document id and the longest request id, is
        exactly 256 KiB or one byte more, when the route arrives, then the first is stored and the next Detect sends all its
        roles, and the second shows the limit text and keeps the earlier count."""
        page, frame, errors, roles = self.session_with(engine, 0)
        self.assertEqual(self.visited_text(page), visited(2))
        self.assertTrue(self.status(page).startswith('Detected'))
        self.assertEqual(self.pending(page, frame)['knownRoles'], roles)
        page, frame, errors, roles = self.session_with(engine, 1)
        self.assertEqual(self.status(page), LIMIT)
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual([item['id'] for item in self.inventory(page)], ['role-1'])
        self.assertEqual(errors, [])


def expected(*sizes):
    return '; '.join(tuple_text(styled(size)) for size in sizes)


class FourStateTests(RouteCase):
    def found_line(self, selector, reference, outside):
        return f'{selector}: expected {expected(*reference)}, found 1 x {expected(outside)}'

    @per_engine
    def test_one_role_moves_between_checked_no_match_and_different_style_across_routes(self, engine):
        """Given a role seeded at 16px on /one, when /two finds nothing, /three finds 24px, /four holds 16px and 20px and
        /three is detected again finding 16px, then the lists read checked /one and /three, no match /two and different
        style /four with only the 20px line, under the approved headings, and four pages are counted."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/one', [author('Lead', [styled(16)], '.a')])
        self.visit(page, frame, '/two', [], found={})
        self.visit(page, frame, '/three', [], found={('role-1', '.a'): [(styled(24), 1)]})
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one'], 'no-match': ['/two'], 'conflict': ['/three']})
        self.assertEqual(self.lines(page, 'role-1', 'conflict'), [[self.found_line('.a', [16], 24)]])
        self.visit(page, frame, '/four', [author('Lead', [styled(16), styled(20)], '.a')],
                   found={('role-1', '.a'): [(styled(16), 1), (styled(20), 1)]})
        self.assertEqual(self.lines(page, 'role-1', 'conflict'), [[self.found_line('.a', [16], 24)], [self.found_line('.a', [16], 20)]])
        self.visit(page, frame, '/three', [], found={('role-1', '.a'): [(styled(16), 1)]})
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one', '/three'], 'no-match': ['/two'], 'conflict': ['/four']})
        self.assertEqual(self.visited_text(page), visited(4))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_route_is_listed_under_one_state_by_precedence(self, engine):
        """Given a role with selectors .a, .b and .c, when one route finds zero, inside and outside, another zero and
        inside, and a third zero and zero, then each route is listed under only different style, checked and no match."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/one', [author('Lead', [styled(16)], '.a', '.b', '.c')])
        self.visit(page, frame, '/mixed', [], found={('role-1', '.b'): [(styled(16), 1)], ('role-1', '.c'): [(styled(24), 1)]})
        self.visit(page, frame, '/inside', [], found={('role-1', '.b'): [(styled(16), 2)]})
        self.visit(page, frame, '/zero', [], found={})
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one', '/inside'], 'no-match': ['/zero'], 'conflict': ['/mixed']})
        self.assertEqual(self.lines(page, 'role-1', 'conflict'), [[self.found_line('.c', [16], 24)]])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_retained_role_without_a_row_shows_its_label_and_its_conflict(self, engine):
        """Given an author role and a style role seen on /one and a /three whose rows hold only a new style that reuses
        the selector .a, when /three finds 40px under both old roles, then both are listed by their label under different
        style, the new style is role-3, and the rows hold only role-3."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/one', [author('Lead', [styled(16)], '.a'), group('t', 'Title', None, styled(32), sel('.t'))])
        self.visit(page, frame, '/three', [group('n', 'New', None, styled(40), sel('.a'))],
                   found={('role-1', '.a'): [(styled(40), 1)], ('role-2', '.t'): [(styled(40), 1)]})
        self.assertEqual([item['title'] for item in self.inventory(page)],
                         ['Lead (role-1)', f'{tuple_text(styled(32))} (role-2)', f'{tuple_text(styled(40))} (role-3)'])
        self.assertEqual(page.locator('#roleRows > li').evaluate_all('els => els.map(e => e.dataset.roleId)'), ['role-3'])
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one'], 'conflict': ['/three']})
        self.assertEqual(self.listed(page, 'role-2'), {'checked': ['/one'], 'conflict': ['/three']})
        self.assertEqual(self.lines(page, 'role-2', 'conflict'), [[self.found_line('.t', [32], 40)]])
        self.assertEqual(self.listed(page, 'role-3'), {'checked': ['/three']})
        self.assertEqual(errors, [])


class ChangedStateTests(RouteCase):
    @per_engine
    def test_a_moved_page_lists_the_route_as_changed_until_a_new_detect_stores_it(self, engine):
        """Given a stored route, when a roles-page moves the version, the URL or to an unsupported URL, or the document
        reloads, then the route is listed only under the changed heading with the count unchanged; a roles-page during a
        pending Detect leaves the pending text; then a Detect that is stored (after a roles-page for a newer version, after
        the reload, or as the pending Detect's own reply) lists the route as checked again."""
        for name in ('a higher version', 'another URL', 'a null URL', 'a reload', 'a pending Detect'):
            with self.subTest(change=name):
                page, frame, errors = self.peer(engine)
                self.detected(page, frame)
                self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/peer']})
                if name == 'a reload':
                    self.reload_peer(page, frame)
                elif name == 'a pending Detect':
                    request = self.pending(page, frame)
                    self.page_message(frame, 1)
                    self.settle(page, frame)
                    self.assertEqual(self.status(page), 'Detecting text styles…')
                else:
                    self.page_message(frame, 1, None if name == 'a null URL' else TARGET + '/other' if name == 'another URL' else PEER_URL)
                    self.wait_status(page, UNAVAILABLE if name == 'a null URL' else CHANGED)
                self.assertEqual(self.listed(page, 'role-1'), {'changed': ['/peer']})
                self.assertEqual(self.visited_text(page), visited(1))
                if name == 'a pending Detect':
                    self.send(frame, self.reply(request, pageVersion=1, currentPageVersion=1))
                    page.wait_for_function('document.querySelector("#roleStatus").textContent.startsWith("Detected")')
                elif name == 'a reload':
                    self.detected(page, frame, documentId='peer-document-2')
                else:
                    self.page_message(frame, 2)
                    self.detected(page, frame, pageVersion=2, currentPageVersion=2)
                self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/peer']})
                self.assertEqual(self.visited_text(page), visited(1))
                self.assertEqual(errors, [])

    @per_engine
    def test_only_the_latest_route_turns_changed_and_changed_outranks_a_conflict(self, engine):
        """Given /one stored as checked and /two stored with a different style, when a roles-page moves the version on
        /two, then /two is listed only under the changed heading, not under different style, and /one stays checked."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/one', [author('Lead', [styled(16)], '.a')])
        self.visit(page, frame, '/two', [], found={('role-1', '.a'): [(styled(24), 1)]})
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one'], 'conflict': ['/two']})
        self.page_message(frame, 3, TARGET + '/two')
        self.wait_status(page, CHANGED)
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/one'], 'changed': ['/two']})
        self.assertEqual(self.visited_text(page), visited(2))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_ready_for_another_url_at_the_same_version_lists_the_route_as_changed(self, engine):
        """Given a stored route, when the same document announces ready at the same version with another URL, then the
        route is listed only under the changed heading and the count stays 1."""
        page, frame, errors = self.peer(engine)
        self.detected(page, frame)
        self.assertEqual(self.listed(page, 'role-1'), {'checked': ['/peer']})
        self.ready_with(page, frame, self.snapshot_state([], pageURL=TARGET + '/other'))
        self.assertEqual(self.listed(page, 'role-1'), {'changed': ['/peer']})
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual(errors, [])


class LateScanTests(RouteCase):
    @per_engine
    def test_a_late_scan_for_an_older_page_or_another_document_never_reaches_the_inventory(self, engine):
        """Given /a stored, a Detect pending for /b and a roles-page for /c at version 3, when the pending Detect's
        complete reply for version 2 arrives, or one naming another document, then the count stays 1, /a is listed only
        as changed and no role from the late reply appears; the older page shows the out-of-date text."""
        for name, change, status in (('an older page version', {}, STALE_REPLY),
                                     ('another document', {'documentId': 'other-document'}, 'Detecting text styles…')):
            with self.subTest(late=name):
                page, frame, errors = self.peer(engine)
                self.visit(page, frame, '/a', [group()])
                request = self.pending(page, frame)
                self.page_message(frame, 3, TARGET + '/c')
                self.settle(page, frame)
                late = self.reply(request, [group('l', 'Late', 'Late')], pageVersion=2, currentPageVersion=2,
                                  pageURL=TARGET + '/b', currentPageURL=TARGET + '/b', **change)
                self.send(frame, late)
                self.settle(page, frame)
                self.settle(page, frame)
                self.assertEqual(self.status(page), status)
                self.assertEqual(self.visited_text(page), visited(1))
                self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)'])
                self.assertEqual(self.listed(page, 'role-1'), {'changed': ['/a']})
                self.assertEqual(errors, [])


class NewDocumentNoticeTests(RouteCase):
    @per_engine
    def test_a_reloaded_page_says_the_preview_is_not_applied_and_keeps_the_inventory(self, engine):
        """Given a Detect and an acknowledged Apply, when the page reloads as a new document, then the notice reads exactly
        the not-applied sentence, the visited count and the inventory stay, and the peer received only hello."""
        page, frame, errors = self.peer(engine)
        self.apply_preview(page, frame)
        self.assertEqual(self.notice(page), '')
        self.reload_peer(page, frame)
        self.assertEqual(self.notice(page), NOT_APPLIED)
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)'])
        self.assertEqual(self.sent(frame), ['design:hello'])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_same_document_ready_or_route_message_shows_no_notice_and_keeps_a_shown_one(self, engine):
        """Given an acknowledged Apply, when the same document announces ready again without the role and a roles-page
        arrives, then no notice shows and no second Apply is sent; given the notice after a reload, when the same
        document announces ready again, then the notice stays."""
        with self.subTest(case='a ready without the role, then a roles-page'):
            page, frame, errors = self.peer(engine)
            self.apply_preview(page, frame)
            frame.evaluate('rev = 1; ready()')
            self.settle(page, frame)
            self.page_message(frame, 1)
            self.settle(page, frame)
            self.settle(page, frame)
            self.assertEqual(self.notice(page), '')
            self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:roles-apply'])
        with self.subTest(case='a ready after the notice'):
            page, frame, errors = self.peer(engine)
            self.apply_preview(page, frame)
            self.reload_peer(page, frame)
            self.assertEqual(self.notice(page), NOT_APPLIED)
            frame.evaluate('ready()')
            self.settle(page, frame)
            self.settle(page, frame)
            self.assertEqual(self.notice(page), NOT_APPLIED)
            self.assertEqual(errors, [])

    @per_engine
    def test_the_notice_needs_a_preview_the_page_held_and_a_new_page_that_lost_it(self, engine):
        """Given a new document, when no preview was ever applied, or the new page still reports the applied role, then
        no notice shows."""
        with self.subTest(case='no preview was applied'):
            page, frame, errors = self.peer(engine)
            self.detected(page, frame)
            self.reload_peer(page, frame)
            self.assertEqual(self.notice(page), '')
        with self.subTest(case='the new page still holds the role'):
            page, frame, errors = self.peer(engine)
            self.apply_preview(page, frame)
            self.ready_with(page, frame, self.snapshot_state([self.role_input()], documentId='peer-document-2'))
            self.settle(page, frame)
            self.assertEqual(self.notice(page), '')
            self.assertEqual(errors, [])

    @per_engine
    def test_the_notice_is_cleared_by_detect_and_by_an_acknowledged_apply_or_clear_preview(self, engine):
        """Given the not-applied notice after a reload, or the visited-pages-cleared notice, when Detect is pressed, or a
        Clear preview or an Apply is acknowledged, then the notice clears; a Clear preview that is only requested leaves
        it."""
        with self.subTest(clears='a Detect click'):
            page, frame, errors = self.peer(engine)
            self.apply_preview(page, frame)
            self.reload_peer(page, frame)
            self.assertEqual(self.notice(page), NOT_APPLIED)
            self.pending(page, frame)
            self.assertEqual(self.notice(page), '')
        with self.subTest(clears='an acknowledged Clear preview'):
            page, frame, errors = self.peer(engine)
            self.apply_preview(page, frame)
            self.button(page, CLEAR_VISITED).click()
            self.assertEqual(self.notice(page), CLEARED)
            request = self.clear_preview(page, frame)
            self.assertEqual(self.notice(page), CLEARED)
            self.send(frame, self.receipt(request))
            page.wait_for_function('document.querySelector("#roleNotice").hidden')
        with self.subTest(clears='an acknowledged Apply'):
            page, frame, errors = self.peer(engine)
            self.detected(page, frame)
            request = self.apply_role(page, frame)
            self.button(page, CLEAR_VISITED).click()
            self.assertEqual(self.notice(page), CLEARED)
            self.send(frame, self.receipt(request))
            page.wait_for_function('document.querySelector("#roleNotice").hidden')
            self.assertEqual(errors, [])


class OriginTests(RouteCase):
    @per_engine
    def test_a_new_origin_starts_an_empty_collection_with_a_notice_and_a_fresh_counter(self, engine):
        """Given a first connection and then two roles detected at that origin, when Studio connects to another origin and
        back, then the first connection shows no notice before any Detect, each later connection shows the new-origin
        sentence with no visited pages or inventory, and the first role detected there is role-1."""
        page, frame, errors = self.peer(engine)
        self.wait_status(page, READY)
        self.assertEqual(self.notice(page), '')
        self.detected(page, frame, [group(), group('o', 'Other', 'Other')])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)', 'Other (role-2)'])
        self.assertEqual(self.notice(page), '')
        other = self.switch_to(page, 'http://evil.test/peer', PEER)
        self.assertEqual((self.notice(page), self.visited_text(page), self.inventory(page)), (NEW_ORIGIN, '', []))
        self.detected(page, other, [group('f', 'Fresh', 'Fresh')])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Fresh (role-1)'])
        self.assertEqual(self.visited_text(page), visited(1))
        self.switch_to(page, PEER_URL, PEER)
        self.assertEqual((self.notice(page), self.visited_text(page), self.inventory(page)), (NEW_ORIGIN, '', []))
        self.assertEqual(errors, [])

    @per_engine
    def test_a_new_origin_keeps_no_role_of_an_applied_preview(self, engine):
        """Given a preview applied for Body as role-1 at one origin, when Studio connects to another origin whose document
        has a different id and Other is detected there, then that Detect request names no known roles and the row is
        Other (role-1)."""
        page, frame, errors = self.peer(engine)
        self.apply_preview(page, frame)
        other = self.switch_to(page, 'http://evil.test/peer', PEER.replace("n===1?'peer-document'", "n===1?'other-origin-document'"))
        request = self.detected(page, other, [group('o', 'Other', 'Other')])
        self.assertEqual(request['documentId'], 'other-origin-document')
        self.assertEqual(request['knownRoles'], [])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Other (role-1)'])
        self.assertEqual(errors, [])

    @per_engine
    def test_a_complete_reply_with_a_script_url_or_an_oversize_route_stores_nothing(self, engine):
        """Given a pending Detect, when a complete reply names a javascript: URL or a 2,001-character path, then Studio
        reports the reply unreadable and shows no visited pages or inventory; a 2,000-character path is stored."""
        for name, url, stored in (('a javascript: URL', 'javascript:alert(1)', False),
                                  ('a 2,001-character path', TARGET + '/' + 'a' * 2000, False),
                                  ('a 2,000-character path (control)', TARGET + '/' + 'a' * 1999, True)):
            with self.subTest(url=name):
                page, frame, errors = self.peer(engine)
                request = self.pending(page, frame)
                self.send(frame, self.reply(request, pageVersion=1, currentPageVersion=1, pageURL=url, currentPageURL=url))
                self.wait_not_detecting(page)
                self.assertEqual(self.status(page).startswith('Detected'), stored)
                self.assertEqual(self.status(page) == UNREADABLE_DETECT, not stored)
                self.assertEqual(self.visited_text(page), visited(1) if stored else '')
                self.assertEqual(len(self.inventory(page)), 1 if stored else 0)
                self.assertEqual(errors, [])


class ClearVisitedTests(RouteCase):
    @per_engine
    def test_clear_visited_pages_after_an_overflow_lifts_the_limit_hint_and_enables_apply(self, engine):
        """Given a full collection that refused a route, when Clear visited pages is pressed and a new role is detected,
        then the limit hint is gone, the new role is role-129 and Apply is enabled once it is ticked and sized."""
        page, frame, errors = self.peer(engine)
        self.visit(page, frame, '/r0', [group(f'g{i}', f'R{i}', f'R{i}') for i in range(table.ROLES)])
        LimitTests.refused(self, page, frame, [group('f', 'Fresh', 'Fresh')], '/r1', 1)
        self.button(page, CLEAR_VISITED).click()
        self.assertNotEqual(self.hint(page, 'roleApplyHint'), LIMIT_HINT)
        self.visit(page, frame, '/r2', [group('f', 'Fresh', 'Fresh')])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Fresh (role-129)'])
        self.control(page, 'Preview this role', 'role-129', 'Fresh').check()
        self.type_value(self.control(page, 'Size (px)', 'role-129', 'Fresh'), '24')
        self.assertEqual(self.gate(page), (True, ''))
        self.assertEqual(errors, [])

    @per_engine
    def test_clear_visited_pages_forgets_evidence_but_keeps_the_preview_and_the_applied_roles_id(self, engine):
        """Given an applied preview and a visited route, when Clear visited pages is pressed, then the button was enabled,
        the inventory, count and rows are gone, the notice and Ready status show, the preview text is unchanged, nothing
        more is sent, and the next Detect names role-1 with no selectors and lists Body as role-1."""
        page, frame, errors = self.peer(engine)
        self.assertTrue(self.button(page, CLEAR_VISITED).is_enabled())
        self.apply_preview(page, frame)
        shown = self.preview(page)
        self.button(page, CLEAR_VISITED).click()
        self.assertEqual((self.notice(page), self.status(page), self.visited_text(page), self.inventory(page)), (CLEARED, READY, '', []))
        self.assertEqual(page.locator('#roleRows > li').count(), 0)
        self.assertEqual(self.preview(page), shown)
        self.assertEqual(self.sent(frame), ['design:hello', 'design:detect', 'design:roles-apply'])
        request = self.detected(page, frame)
        self.assertEqual(request['knownRoles'], [{'id': 'role-1', 'selectors': []}])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)'])
        self.assertEqual(errors, [])

    @per_engine
    def test_after_clear_visited_pages_the_applied_role_keeps_its_id_and_other_roles_get_new_ones(self, engine):
        """Given Body applied as role-1 and Other detected as role-2 but not applied, when Clear visited pages is pressed,
        both roles are detected again and Other is sized and applied, then the Detect request names only role-1, the rows
        are Body (role-1) and Other (role-3), the Apply request carries role-1 at its applied size and role-3, and the
        preview shows no Removed line."""
        page, frame, errors = self.peer(engine)
        groups = [group(), group('o', 'Other', 'Other')]
        self.detected(page, frame, groups)
        self.send(frame, self.receipt(self.apply_role(page, frame)))
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("Preview applied to 1 role")')
        self.button(page, CLEAR_VISITED).click()
        request = self.detected(page, frame, groups)
        self.assertEqual(request['knownRoles'], [{'id': 'role-1', 'selectors': []}])
        self.assertEqual([item['title'] for item in self.inventory(page)], ['Body (role-1)', 'Other (role-3)'])
        self.control(page, 'Preview this role', 'role-3', 'Other').check()
        self.type_value(self.control(page, 'Size (px)', 'role-3', 'Other'), '30')
        sent = self.press_apply(page, frame)
        self.assertEqual([(role['id'], role['properties']) for role in sent['roles']],
                         [('role-1', {'fontSize': 24}), ('role-3', {'fontSize': 30})])
        self.send(frame, self.receipt(sent))
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("Preview applied to 2 roles")')
        self.assertEqual(self.preview(page)['removed'], '')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_detect_pending_when_visited_pages_are_cleared_is_not_stored_by_its_late_reply(self, engine):
        """Given a pending Detect, when Clear visited pages is pressed and the reply arrives, then no visited page, row or
        inventory appears and the status stays Ready."""
        page, frame, errors = self.peer(engine)
        request = self.pending(page, frame)
        self.button(page, CLEAR_VISITED).click()
        self.send(frame, self.reply(request))
        self.settle(page, frame)
        self.settle(page, frame)
        self.assertEqual((self.status(page), self.visited_text(page), self.inventory(page)), (READY, '', []))
        self.assertEqual(page.locator('#roleRows > li').count(), 0)
        self.assertEqual(errors, [])


class LegacyOutputTests(RouteCase):
    LEGACY = {'version': '0.1.1', 'composition': {'canvasWidth': '960', 'slots': [
        {'role': 'H1', 'family': 'Georgia', 'size': 41, 'weight': 600, 'tracking': 0.02}]}}
    ROUTES = ('/r0', '/r1?a=1', '/r2#top')
    # Slot ids are random per session and appear in the JSON export; a counter makes two sessions comparable byte for byte.
    COUNTED_IDS = """Object.defineProperty(crypto, 'randomUUID', {configurable: true, value: (() => {
        let count = 0; return () => `00000000-0000-4000-8000-${String(++count).padStart(12, '0')}`; })()})"""

    def edited(self, engine):
        """Studio on the legacy fake target with a saved inspector edit (9px on the hero lead), before any Detect."""
        self.version = 0
        page, frame, errors = self.open(engine, HYBRID_URL, hybrid_page(), sync=True, init=self.COUNTED_IDS)
        page.wait_for_function('() => !/^Checking/.test(document.querySelector("#liveCodeSync").title)')
        frame.evaluate('(id) => fake.select(id)', 'hero.lead')
        page.wait_for_function('(id) => document.querySelector("#liveTargetName")?.dataset.targetId === id', arg='hero.lead')
        self.type_value(page.locator('#liveFontSize'), '9')
        page.wait_for_function('/^Live · rev 1$/.test(document.querySelector("#bridgeStatusBadge").textContent)')
        return page, frame, errors

    def visit_routes(self, page, frame):
        for path in self.ROUTES:
            self.visit(page, frame, path, [group(selectors=HERO_LEAD)])

    def import_legacy(self, page):
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json', 'buffer': json.dumps(self.LEGACY).encode()})
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        return page.locator('#composerStatus').inner_text()

    @per_engine
    def test_exports_saved_edits_and_the_synced_file_are_unchanged_by_visited_pages_and_clear(self, engine):
        """Given a saved inspector edit on the legacy fake target and its outputs before any Detect, when three routes are
        detected and then visited pages are cleared, then the code tabs, their downloads, the JSON export (the import
        format) and the Sync body are byte-identical to those outputs after the routes (compared before Clear) and after
        Clear, the Sync body holds the 9px edit, and none of them names a route or role id."""
        page, frame, errors = self.edited(engine)
        before, before_sync = self.exports(page), self.sync_body(page)
        self.visit_routes(page, frame)
        self.assertEqual(self.exports(page), before)
        self.button(page, CLEAR_VISITED).click()
        after, after_sync = self.exports(page), self.sync_body(page)
        self.assertEqual(after, before)
        self.assertEqual(after_sync, before_sync)
        self.assertIn('font-size: 9px', before_sync)
        for text in (*after.values(), after_sync):
            self.assertNotIn('/r1', text)
            self.assertNotIn('role-', text)
        self.assertEqual(errors, [])

    @per_engine
    def test_an_imported_legacy_json_is_the_same_with_three_visited_pages_and_after_clear(self, engine):
        """Given the same saved inspector edit in two sessions, one holding three visited pages, when a legacy 0.1.1 JSON
        is imported in each, then the import changes the code tabs, the held session still counts three pages, and the
        status, code tabs, downloads, JSON export and Sync body are byte-identical between the sessions; a further Detect
        of a fourth route in the held session then names only role-1 with the hero lead selector, counts four visited
        pages and lists Body (role-1) and Other (role-2); the outputs are still identical after Clear visited pages."""
        plain, plain_frame, plain_errors = self.edited(engine)
        before = self.exports(plain)
        plain_status = self.import_legacy(plain)
        plain_after = self.exports(plain), self.sync_body(plain)
        held, held_frame, held_errors = self.edited(engine)
        self.visit_routes(held, held_frame)
        self.assertEqual(self.exports(held), before)
        self.assertEqual(self.import_legacy(held), plain_status)
        self.assertTrue(plain_status.startswith('Composition imported.'), plain_status)
        self.assertNotEqual(plain_after[0], before)
        self.assertEqual(self.visited_text(held), visited(3))
        self.assertEqual((self.exports(held), self.sync_body(held)), plain_after)
        request = self.visit(held, held_frame, '/r3', [group(selectors=HERO_LEAD), group('o', 'Other', 'Other')])
        self.assertEqual(request['knownRoles'], [{'id': 'role-1', 'selectors': ['[data-design-id="hero.lead"]']}])
        self.assertEqual(self.visited_text(held), visited(4))
        self.assertEqual([item['title'] for item in self.inventory(held)], ['Body (role-1)', 'Other (role-2)'])
        self.button(held, CLEAR_VISITED).click()
        self.assertEqual((self.exports(held), self.sync_body(held)), plain_after)
        self.assertEqual((plain_errors, held_errors), ([], []))


class RealBridgeCase(RouteCase):
    TAG = '<script src="/fontkit-bridge.js"></script>'

    def served(self, name):
        source = (REPO / 'fixtures' / 'multi-page' / name).read_text(encoding='utf-8')
        self.assertEqual(source.count('</body>'), 1)
        return source.replace('</body>', self.TAG + '</body>')

    def open_page(self, engine, name):
        """Studio on the multi-page fixture `name`, every fixture page carrying the real bridge, in Interact mode."""
        page, frame, errors = self.open(engine, TARGET + MULTI + name, self.served(name))
        page.context.route(TARGET + MULTI + '*.html', lambda route: route.fulfill(
            body=self.served(Path(urlsplit(route.request.url).path).name), content_type='text/html'))
        page.locator('#bridgeModeInteract').click()
        return page, frame, errors

    def go(self, page, frame, link):
        """Follows a fixture link in the target and waits until Studio has the new document ready."""
        frame.locator(f'[data-design-id="{link}"]').click()
        self.wait_status(page, READY)

    def role(self, page, label):
        """The inventory entry whose title starts with `label` (the oracle's tuple text or an author name)."""
        found = [item for item in self.inventory(page) if item['title'].startswith(label + ' (')]
        self.assertEqual(len(found), 1, (label, [item['title'] for item in self.inventory(page)]))
        return found[0]

    def apply_title(self, page, frame):
        """Detects, then previews weight 900 on the base-title role through the row's controls; returns once the page shows it."""
        self.assertTrue(self.detect(page).startswith('Detected'))
        role = self.role(page, BASE_TITLE)['id']
        name = page.locator(f'#roleRows > li[data-role-id="{role}"] strong').inner_text().rsplit(' (', 1)[0]
        self.control(page, 'Preview this role', role, name).check()
        self.type_value(self.control(page, 'Weight', role, name), '900')
        self.button(page, APPLY).click()
        frame.wait_for_function(f'{WEIGHT} === "900"', polling=50)
        page.wait_for_function('document.querySelector("#rolePreviewStatus").textContent.includes("Preview applied")')


class RealBridgeRouteTests(RealBridgeCase):
    @per_engine
    def test_pages_visited_by_links_are_listed_per_role_and_unvisited_ones_never(self, engine):
        """Given the real bridge on the multi-page fixture, when index, article, conflict and index again are detected
        through link clicks, then three visited pages are counted, the base-title role is checked on index and article and
        has a different style on conflict (expected and found tuples from the oracle), the conflict-title role is checked
        on conflict and has a different style on index, no entry names unvisited.html, the index title renders the
        oracle's font size and the conflict title its text transform."""
        page, frame, errors = self.open_page(engine, 'index.html')
        title = frame.locator('.shared-title')
        self.assertEqual(title.evaluate('el => getComputedStyle(el).fontSize'), f'{ORACLE["base-title"]["fontSize"]}px')
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.go(page, frame, 'nav.article')
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.go(page, frame, 'nav.conflict')
        self.assertEqual(frame.locator('.shared-title').evaluate('el => getComputedStyle(el).textTransform'), ORACLE['conflict-title']['textTransform'])
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.go(page, frame, 'nav.home')
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.assertEqual(self.visited_text(page), visited(3))
        conflict = tuple_text(ORACLE['conflict-title'])
        base = self.role(page, BASE_TITLE)['id']
        self.assertEqual(self.listed(page, base), {'checked': [MULTI + 'index.html', MULTI + 'article.html'], 'conflict': [MULTI + 'conflict.html']})
        self.assertEqual(self.lines(page, base, 'conflict'), [[f'[data-design-id="route.title"]: expected {BASE_TITLE}, found 1 x {conflict}']])
        self.assertEqual(self.listed(page, self.role(page, conflict)['id']), {'checked': [MULTI + 'conflict.html'], 'conflict': [MULTI + 'index.html']})
        self.assertNotIn('unvisited', page.locator('#roleInventory').inner_text() + self.visited_text(page))
        self.assertEqual(errors, [])


class RealBridgeSpaTests(RealBridgeCase):
    @per_engine
    def test_a_same_url_content_change_is_announced_and_a_new_detect_replaces_the_route(self, engine):
        """Given a Detect at /spa.html, when the page replaces its state at the same URL with other content and Detect is
        pressed again, then the status becomes the page-changed sentence and the home title role lists the route only as
        changed; after Detect the count stays 1, the home title role lists the route under different style and the
        same-view title role under checked."""
        page, frame, errors = self.open_page(engine, 'spa.html')
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.assertEqual(self.pages(page, self.role(page, BASE_TITLE)['id']), [MULTI + 'spa.html'])
        frame.locator('#replace-same').click()
        self.wait_status(page, CHANGED)
        self.assertEqual(self.listed(page, self.role(page, BASE_TITLE)['id']), {'changed': [MULTI + 'spa.html']})
        self.assertTrue(self.detect(page).startswith('Detected'))
        self.assertEqual(self.visited_text(page), visited(1))
        self.assertEqual(self.listed(page, self.role(page, BASE_TITLE)['id']), {'conflict': [MULTI + 'spa.html']})
        self.assertEqual(self.listed(page, self.role(page, SAME_TITLE)['id']), {'checked': [MULTI + 'spa.html']})
        self.assertEqual(errors, [])


class RealBridgeDriftTests(RealBridgeCase):
    @per_engine
    def test_a_conflict_under_a_live_preview_reports_the_baseline_not_the_previewed_weight(self, engine):
        """Given Detect at the SPA home and a weight 900 preview on its title role, when the page pushes the detail view in
        the same document (the detail rules set size and tracking, so the previewed weight still shows) and Detect runs
        again, then the title role's different-style line expects the home tuple and finds the oracle's detail-title
        tuple, and the text 900 appears nowhere in the inventory."""
        page, frame, errors = self.open_page(engine, 'spa.html')
        self.apply_title(page, frame)
        role = self.role(page, BASE_TITLE)['id']
        frame.locator('#push-detail').click()
        self.wait_status(page, CHANGED)
        self.assertEqual(frame.evaluate(WEIGHT), '900')
        self.assertTrue(self.detect(page).startswith('Detected'))
        detail = tuple_text(ORACLE['detail-title'])
        self.assertEqual(detail, 'serif: 36px / 700 / none / -0.01em')
        self.assertEqual(self.lines(page, role, 'conflict'), [[f'[data-design-id="route.title"]: expected {BASE_TITLE}, found 1 x {detail}']])
        self.assertEqual(self.listed(page, role), {'checked': [MULTI + 'spa.html'], 'conflict': [MULTI + 'spa.html?route=detail']})
        self.assertNotIn('900', page.locator('#roleInventory').inner_text())
        self.assertEqual(errors, [])


class RealBridgeNoticeTests(RealBridgeCase):
    @per_engine
    def test_a_reloaded_page_is_the_authors_until_an_explicit_apply_works_again(self, engine):
        """Given a weight 900 preview on the index title, when the page reloads, then the computed weight is the author's
        and the not-applied notice shows; a fresh Detect and Apply show 900 again and the notice is gone."""
        page, frame, errors = self.open_page(engine, 'index.html')
        self.apply_title(page, frame)
        self.reload_peer(page, frame)
        self.assertEqual(frame.evaluate(WEIGHT), str(ORACLE['base-title']['fontWeight']))
        self.assertEqual(self.notice(page), NOT_APPLIED)
        self.apply_title(page, frame)
        self.assertEqual(self.notice(page), '')
        self.assertEqual(errors, [])

    @per_engine
    def test_a_route_change_in_one_document_keeps_the_preview_and_shows_no_notice(self, engine):
        """Given a weight 900 preview at the SPA home, when the page pushes the detail view in the same document, then the
        title keeps weight 900 and no notice shows."""
        page, frame, errors = self.open_page(engine, 'spa.html')
        self.apply_title(page, frame)
        frame.locator('#push-detail').click()
        self.wait_status(page, CHANGED)
        self.assertEqual(frame.evaluate(WEIGHT), '900')
        self.assertEqual(self.notice(page), '')
        self.assertEqual(errors, [])

    @per_engine
    def test_pop_out_and_dock_keep_the_inventory_and_the_pop_out_shows_the_notice(self, engine):
        """Given a weight 900 preview and a visited index, when the target is popped out and docked back, then each keeps
        the visited count and inventory; the pop-out shows the author's weight and the notice, and the dock clears it."""
        page, frame, errors = self.open_page(engine, 'index.html')
        self.apply_title(page, frame)
        titles = [item['title'] for item in self.inventory(page)]
        with page.expect_popup() as info:
            page.locator('#bridgePopOut').click()
        popup = info.value
        self.wait_status(page, READY)
        self.assertEqual(popup.evaluate(WEIGHT), str(ORACLE['base-title']['fontWeight']))
        self.assertEqual(self.notice(page), NOT_APPLIED)
        self.assertEqual((self.visited_text(page), [item['title'] for item in self.inventory(page)]), (visited(1), titles))
        with popup.expect_event('close'):
            page.locator('#bridgeDock').click()
        self.wait_status(page, READY)
        self.assertEqual(self.notice(page), '')
        self.assertEqual((self.visited_text(page), [item['title'] for item in self.inventory(page)]), (visited(1), titles))
        self.assertEqual(errors, [])
