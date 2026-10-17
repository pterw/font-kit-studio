"""Role stylesheet apply/clear through the real bridge: rendered styles, exact undo, honest receipts."""
import json

from support import ENGINES
from role_support import EVIL, ROLE_PAGE, STUDIO, TARGET, RoleBridgeCase

OWNED = "Array.from(document.querySelectorAll('style[data-fontkit-role-styles]')).map(s => s.textContent)"
SIZE = 'el => getComputedStyle(el).fontSize'
BODY = '.body-copy'
EMPTY_HASH = '811c9dc5'
GOLDEN_CSS = (r'''.md\:text-xl, [data-design-id="a\"b"], [data-design-role="H\e9 ro"] {
  font-family: "Zoë Sans", "日本語", serif;
  font-size: 32.46px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.body-copy {
  font-size: 18px;
}
''')
DEFAULT = object()
GOLDEN_HASH = '4435df78'
PLAIN_24 = '.body-copy {\n  font-size: 24px;\n}\n'
PLAIN_24_HASH = '226b1831'
SNAPSHOT = """() => ({
  html: document.documentElement.outerHTML,
  styles: Array.from(document.body.querySelectorAll('*'), el =>
    Array.from(getComputedStyle(el), name => name + ':' + getComputedStyle(el).getPropertyValue(name)).join(';'))
})"""


def role(rid='body', selectors=(BODY,), **properties):
    return {'id': rid, 'name': rid.title(), 'selectors': list(selectors), 'adapter': 'plain', 'properties': properties}


def fnv1a32(text):
    value = 0x811c9dc5
    for byte in text.encode('utf-8'):
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return '%08x' % value


class RoleSheetCase(RoleBridgeCase):
    def apply(self, page, roles, timeout=4000, **extra):
        message = {'type': 'design:roles-apply', 'documentId': page.evaluate('roleState.documentId'),
                   'pageVersion': page.evaluate('roleState.pageVersion'), 'roles': roles, **extra}
        reply = page.evaluate('([m, t]) => request(m, t)', [message, timeout])
        for outcome in reply.get('outcomes', []):
            self.assertTrue(0 <= outcome['mismatched'] <= outcome['checked'] <= outcome['matched'], outcome)
            for loss in outcome['losses']:
                self.assertIn(loss['property'], ('fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform'))
        return reply

    def clear(self, page, timeout=4000, **extra):
        message = {'type': 'design:roles-clear', 'documentId': page.evaluate('roleState.documentId'),
                   'pageVersion': page.evaluate('roleState.pageVersion'), **extra}
        return page.evaluate('([m, t]) => request(m, t)', [message, timeout])

    def current(self, page):
        """Identity after an author change: the current page version arrives in a read-only detect."""
        reply = self.detect(page)
        return {'documentId': page.evaluate('roleState.documentId'), 'pageVersion': reply['currentPageVersion']}

    def size(self, frame, selector=BODY, nth=0):
        return frame.locator(selector).nth(nth).evaluate(SIZE)

    def owned(self, frame):
        return frame.evaluate(OWNED)

    def snapshot(self, frame, drop_owned=False):
        data = frame.evaluate(SNAPSHOT)
        if drop_owned:
            data['html'] = frame.evaluate("""() => {
                const copy = document.documentElement.cloneNode(true);
                copy.querySelectorAll('style[data-fontkit-role-styles]').forEach(el => el.remove());
                return copy.outerHTML;
            }""")
        return data


class ApplyAndClearTests(RoleSheetCase):
    def test_apply_renders_canonical_css_and_replies_with_a_measured_receipt(self):
        """Given 16px body copy, when an authenticated apply asks for 24px, then both
        paragraphs render 24px from one owned style node and the receipt carries the
        canonical bytes, digest, one revision and honest measured outcomes."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                self.assertTrue(ready['capabilities']['roleStylesheet'])
                self.assertEqual(self.size(frame), '16px')
                before = frame.locator('main').evaluate('el => el.outerHTML')
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['operation'], reply['revision']), ('apply', 1))
                self.assertEqual((reply['documentId'], reply['pageVersion']),
                                 (ready['roleState']['documentId'], ready['roleState']['pageVersion']))
                self.assertEqual((reply['currentPageVersion'], reply['currentPageURL']), (reply['pageVersion'], frame.url))
                self.assertEqual((reply['canonicalCss'], reply['hashAlgorithm'], reply['cssHash']),
                                 (PLAIN_24, 'fnv1a32', PLAIN_24_HASH))
                self.assertEqual(reply['roles'], [role(fontSize=24)])
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                self.assertEqual(reply['outcomes'], [{'id': 'body', 'matched': 2, 'checked': 2, 'mismatched': 0,
                                                      'complete': True, 'losses': []}])
                self.assertEqual([self.size(frame, BODY, 0), self.size(frame, BODY, 1)], ['24px', '24px'])
                self.assertEqual(self.owned(frame), [PLAIN_24])
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(page.evaluate('revision'), 1)

    def test_clear_removes_only_the_owned_node_and_repeat_clear_is_idempotent(self):
        """Given an applied 24px role, when clear is sent twice, then rendering returns to
        16px, only the owned node is gone, and each clear gets its own empty receipt."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertEqual(self.apply(page, [role(fontSize=24)])['revision'], 1)
                self.assertEqual(self.size(frame), '24px')
                first = self.clear(page)
                self.assertEqual((first['type'], first['operation'], first['revision']), ('design:roles-applied', 'clear', 2), first)
                self.assertEqual((first['roles'], first['canonicalCss'], first['cssHash'], first['outcomes']), ([], '', EMPTY_HASH, []))
                self.assertEqual((first['outcomesComplete'], first['outcomeReason']), (True, None))
                self.assertEqual((self.size(frame), self.owned(frame)), ('16px', []))
                second = self.clear(page)
                self.assertEqual((second['operation'], second['revision'], second['canonicalCss'], second['outcomesComplete']),
                                 ('clear', 3, '', True), second)
                self.assertEqual((self.size(frame), self.owned(frame)), ('16px', []))

    def test_every_declaration_renders_in_fixed_order_with_canonical_golden_bytes(self):
        """Given a role with all six properties in scrambled order, when applied, then the
        target renders each computed value and the owned node holds the golden bytes."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                roles = [role('hero', ['.md\\:text-xl', '.md\\:text-xl', '[data-design-id="a\\"b"]', '[data-design-role="H\\e9 ro"]'],
                              textTransform='uppercase', letterSpacing=0.05, lineHeight=1.2, fontWeight=700,
                              fontSize=32.456, fontFamily=' "Zoë Sans", "日本語", serif '),
                         role('body', fontSize=18)]
                reply = self.apply(page, roles)
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual(reply['canonicalCss'], GOLDEN_CSS)
                self.assertEqual((reply['hashAlgorithm'], reply['cssHash']), ('fnv1a32', GOLDEN_HASH))
                self.assertEqual(fnv1a32(GOLDEN_CSS), GOLDEN_HASH)
                self.assertEqual(self.owned(frame), [GOLDEN_CSS])
                self.assertEqual(reply['roles'][0]['selectors'], ['.md\\:text-xl', '[data-design-id="a\\"b"]', '[data-design-role="H\\e9 ro"]'])
                self.assertEqual(reply['roles'][0]['properties']['fontSize'], 32.46)
                self.assertEqual([o['matched'] for o in reply['outcomes']], [0, 2])
                self.assertEqual(self.size(frame), '18px')
                # Properties on a rendered element: the same declarations reach computed style.
                full = self.apply(page, [role(fontFamily='Georgia, serif', fontSize=24, fontWeight=700, lineHeight=1.2,
                                              letterSpacing=0.05, textTransform='uppercase')])
                self.assertEqual((full['outcomesComplete'], full['outcomes'][0]['mismatched']), (True, 0), full)
                style = frame.locator(BODY).first.evaluate("""el => { const s = getComputedStyle(el);
                    return [s.fontFamily, s.fontSize, s.fontWeight, s.lineHeight, s.letterSpacing, s.textTransform]; }""")
                self.assertEqual(style, ['Georgia, serif', '24px', '700', '28.8px', '1.2px', 'uppercase'])

    def test_empty_roles_apply_removes_the_owned_node_with_an_empty_receipt(self):
        """Given an applied role, when apply carries roles: [], then it is an apply receipt
        with empty roles, CSS and outcomes, one revision, and the owned node is removed."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                reply = self.apply(page, [])
                self.assertEqual((reply['type'], reply['operation'], reply['revision']), ('design:roles-applied', 'apply', 2), reply)
                self.assertEqual((reply['roles'], reply['canonicalCss'], reply['cssHash'], reply['outcomes']), ([], '', EMPTY_HASH, []))
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                self.assertEqual((self.size(frame), self.owned(frame)), ('16px', []))

    def test_a_bootstrap5_adapter_is_rejected_where_the_page_has_no_bootstrap5_evidence(self):
        """Given a page without Bootstrap 5 variables, when each bootstrap5 adapter is applied,
        then it is rejected as unsupported with nothing emitted, while the plain adapter renders."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for adapter in ('bootstrap5-body', 'bootstrap5-mono', 'bootstrap5-heading'):
                    bad = role(fontFamily='Georgia', fontSize=24)
                    bad['adapter'] = adapter
                    reply = self.apply(page, [bad])
                    self.assertEqual((reply['type'], reply['reason'], reply['detail']),
                                     ('design:rejected', 'unsupported-value', 'Unsupported adapter'), reply)
                    self.assertEqual((self.size(frame), self.owned(frame), page.evaluate('revision')), ('16px', [], 0))
                    self.assertEqual(frame.evaluate("document.documentElement.style.getPropertyValue('--bs-body-font-family')"), '')
                self.assertEqual(self.apply(page, [role(fontSize=24)])['type'], 'design:roles-applied')
                self.assertEqual(self.size(frame), '24px')

    def test_zero_matches_are_a_real_measured_result_and_selectors_dedupe_across_the_union(self):
        """Given a selector matching nothing and a union matching visible paragraphs, when
        applied, then zero is reported as zero and hidden matches count as matched but not checked, and repeats are not counted twice."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const hidden = document.createElement('p'); hidden.className = 'body-copy';
                    hidden.hidden = true; hidden.textContent = 'Hidden copy';
                    document.querySelector('main').appendChild(hidden);
                }""")
                self.hello(page)
                reply = self.apply(page, [role('none', ['.no-such-class'], fontSize=24),
                                          role('union', [BODY, 'main > p', 'p.body-copy'], fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual([(o['id'], o['matched'], o['checked'], o['mismatched'], o['complete']) for o in reply['outcomes']],
                                 [('none', 0, 0, 0, True), ('union', 3, 2, 0, True)])
                self.assertTrue(reply['outcomesComplete'])
                self.assertEqual(len(self.owned(frame)), 1)

    def test_a_winning_author_rule_is_a_counted_loss_named_as_the_proven_winner(self):
        """Given an author rule with higher specificity, when a role sets another size, then
        the author's 18px renders and the receipt counts the loss as author-rule `.card p`."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const style = document.createElement('style');
                    style.textContent = '.card p { font-size: 18px; }';
                    document.head.appendChild(style);
                    const card = document.createElement('div'); card.className = 'card';
                    const p = document.createElement('p'); p.className = 'card-copy'; p.textContent = 'Card text';
                    card.appendChild(p); document.querySelector('main').appendChild(card);
                }""")
                self.hello(page)
                reply = self.apply(page, [role('body', fontSize=24), role('card', ['.card-copy'], fontSize=24, fontWeight=700)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                body, card = reply['outcomes']
                self.assertEqual((body['matched'], body['checked'], body['mismatched'], body['losses']), (2, 2, 0, []))
                self.assertEqual((card['matched'], card['checked'], card['mismatched'], card['complete']), (1, 1, 1, True))
                self.assertEqual(card['losses'], [{'property': 'fontSize', 'count': 1, 'winningSelector': '.card p',
                                                   'reason': 'author-rule'}])
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                self.assertEqual(self.size(frame, '.card-copy'), '18px')
                self.assertEqual(frame.locator('.card-copy').evaluate('el => getComputedStyle(el).fontWeight'), '700')
                self.assertEqual(self.size(frame), '24px')

    def test_more_than_ten_thousand_matching_parents_disclose_a_budget_with_the_real_checked_count(self):
        """Given 10,001 matching text parents, when applied, then the preview renders but the
        receipt discloses budget-exceeded with the 10,000 parents actually checked."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const host = document.createElement('div'), fragment = document.createDocumentFragment();
                    for (let i = 0; i < 10001; i += 1) {
                        const item = document.createElement('div'); item.className = 'bulk'; item.textContent = 'n' + i;
                        fragment.appendChild(item);
                    }
                    host.appendChild(fragment); document.querySelector('main').appendChild(host);
                }""")
                self.hello(page)
                reply = self.apply(page, [role('bulk', ['.bulk'], fontSize=24)], timeout=20000)
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (False, 'budget-exceeded'))
                outcome = reply['outcomes'][0]
                self.assertEqual((outcome['id'], outcome['checked'], outcome['complete'], outcome['losses']),
                                 ('bulk', 10000, False, []))
                self.assertEqual((self.size(frame, '.bulk', 0), self.size(frame, '.bulk', 10000)), ('24px', '24px'))


class AtomicRejectionTests(RoleSheetCase):
    def hostile_cases(self):
        good = role(fontSize=30)

        def with_role(**changes):
            return [{**good, **changes}]

        def with_properties(**properties):
            return [role(**properties)]

        # Duplicates dedupe to a tiny canonical CSS, so only the 256 KiB request limit can reject this.
        selector_limit = [role(f'r{i}', ['.' + 'a' * 1999] * 32, fontSize=30) for i in range(5)]
        return [
            ('stale-revision', {'baseRevision': 7}, DEFAULT, 'revision-conflict'),
            ('wrong-document', {'documentId': 'unknown-document'}, DEFAULT, 'page-changed'),
            ('wrong-page-version', {'pageVersion': 99}, DEFAULT, 'page-changed'),
            ('surprise-field', {'surprise': True}, DEFAULT, 'invalid-message'),
            ('constructor-key', {'constructor': {}}, DEFAULT, 'invalid-message'),
            ('prototype-key', {'prototype': {}}, DEFAULT, 'invalid-message'),
            ('empty-request-id', {'requestId': ''}, DEFAULT, 'invalid-message'),
            ('negative-version', {'pageVersion': -1}, DEFAULT, 'invalid-message'),
            ('roles-object', {}, {}, 'invalid-message'),
            ('roles-null', {}, None, 'invalid-message'),
            ('role-array', {}, [[]], 'invalid-message'),
            ('role-unknown-key', {}, with_role(extra=1), 'invalid-message'),
            ('role-prototype-key', {}, with_role(prototype={}), 'invalid-message'),
            ('role-missing-key', {}, [{k: v for k, v in good.items() if k != 'name'}], 'invalid-message'),
            ('properties-array', {}, with_role(properties=[]), 'invalid-message'),
            ('properties-null', {}, with_role(properties=None), 'invalid-message'),
            ('properties-empty', {}, with_role(properties={}), 'invalid-message'),
            ('property-unknown', {}, with_properties(color='#fff'), 'invalid-message'),
            ('property-custom', {}, with_properties(**{'--x': '1'}), 'invalid-message'),
            ('property-constructor', {}, with_properties(constructor=1), 'invalid-message'),
            ('duplicate-id', {}, [good, good], 'invalid-message'),
            ('id-empty', {}, with_role(id=''), 'invalid-message'),
            ('id-101', {}, with_role(id='x' * 101), 'invalid-message'),
            ('name-201', {}, with_role(name='x' * 201), 'invalid-message'),
            ('name-number', {}, with_role(name=3), 'invalid-message'),
            ('selectors-empty', {}, with_role(selectors=[]), 'invalid-message'),
            ('selectors-33', {}, with_role(selectors=[f'.s{i}' for i in range(33)]), 'invalid-message'),
            ('selectors-object', {}, with_role(selectors={}), 'invalid-message'),
            ('roles-129', {}, [role(f'r{i}', [f'.s{i}'], fontSize=30) for i in range(129)], 'invalid-message'),
            ('adapter-unknown', {}, with_role(adapter='bootstrap9'), 'invalid-message'),
            ('adapter-bootstrap-without-evidence', {}, with_role(adapter='bootstrap5-body'), 'unsupported-value'),
            ('case-unknown', {}, with_properties(textTransform='small-caps'), 'invalid-message'),
            ('size-nan', {}, with_properties(fontSize=float('nan')), 'unsupported-value'),
            ('size-infinity', {}, with_properties(fontSize=float('inf')), 'unsupported-value'),
            ('size-string', {}, with_properties(fontSize='24'), 'unsupported-value'),
            ('size-3', {}, with_properties(fontSize=3.99), 'unsupported-value'),
            ('size-401', {}, with_properties(fontSize=400.01), 'unsupported-value'),
            ('weight-0', {}, with_properties(fontWeight=0), 'unsupported-value'),
            ('weight-1001', {}, with_properties(fontWeight=1001), 'unsupported-value'),
            ('line-low', {}, with_properties(lineHeight=0.49), 'unsupported-value'),
            ('line-high', {}, with_properties(lineHeight=5.01), 'unsupported-value'),
            ('tracking-low', {}, with_properties(letterSpacing=-0.51), 'unsupported-value'),
            ('tracking-high', {}, with_properties(letterSpacing=2.01), 'unsupported-value'),
            ('family-semicolon', {}, with_properties(fontFamily='Arial; color: red'), 'unsupported-value'),
            ('family-brace', {}, with_properties(fontFamily='Arial}'), 'unsupported-value'),
            ('family-angle', {}, with_properties(fontFamily='Arial<'), 'unsupported-value'),
            ('family-escape', {}, with_properties(fontFamily='Arial\\41'), 'unsupported-value'),
            ('family-comment', {}, with_properties(fontFamily='Arial /* x */'), 'unsupported-value'),
            ('family-url', {}, with_properties(fontFamily='url(x)'), 'unsupported-value'),
            ('family-expression', {}, with_properties(fontFamily='expression(x)'), 'unsupported-value'),
            ('family-var', {}, with_properties(fontFamily='var(--x)'), 'unsupported-value'),
            ('family-important', {}, with_properties(fontFamily='Arial !important'), 'unsupported-value'),
            ('family-newline', {}, with_properties(fontFamily='Arial\nSerif'), 'unsupported-value'),
            ('family-unbalanced', {}, with_properties(fontFamily='"Arial'), 'unsupported-value'),
            ('family-unsupported', {}, with_properties(fontFamily='"Good", 1bad'), 'unsupported-value'),
            ('family-empty', {}, with_properties(fontFamily='   '), 'unsupported-value'),
            ('family-301', {}, with_properties(fontFamily='a' * 301), 'unsupported-value'),
            ('family-number', {}, with_properties(fontFamily=12), 'unsupported-value'),
            ('selector-list', {}, with_role(selectors=['.a, .b']), 'unsupported-value'),
            ('selector-root', {}, with_role(selectors=[':root']), 'unsupported-value'),
            ('selector-html', {}, with_role(selectors=['html']), 'unsupported-value'),
            ('selector-body', {}, with_role(selectors=['body']), 'unsupported-value'),
            ('selector-matches-body', {}, with_role(selectors=['.on-body']), 'unsupported-value'),
            ('selector-attribute', {}, with_role(selectors=['p[title="x"]']), 'unsupported-value'),
            ('selector-pseudo', {}, with_role(selectors=['p:hover']), 'unsupported-value'),
            ('selector-link-hover', {}, with_role(selectors=['a:hover']), 'unsupported-value'),
            ('selector-raw-open-brace', {}, with_role(selectors=['.a{']), 'unsupported-value'),
            ('selector-raw-semicolon', {}, with_role(selectors=['.a;']), 'unsupported-value'),
            ('selector-raw-close-brace', {}, with_role(selectors=['.a}']), 'unsupported-value'),
            ('selector-line-break', {}, with_role(selectors=['.a\n.b']), 'unsupported-value'),
            ('selector-expression', {}, with_role(selectors=['.a[data-design-id="expression(x)"]']), 'unsupported-value'),
            ('selector-nth-10000', {}, with_role(selectors=['p:nth-of-type(10000)']), 'unsupported-value'),
            ('selector-nth-zero', {}, with_role(selectors=['p:nth-of-type(0)']), 'unsupported-value'),
            ('request-id-201', {'requestId': 'r' * 201}, DEFAULT, 'invalid-message'),
            ('selector-comment', {}, with_role(selectors=['.a/*x*/']), 'unsupported-value'),
            ('selector-brace', {}, with_role(selectors=['.a{}']), 'unsupported-value'),
            ('selector-at-rule', {}, with_role(selectors=['@import']), 'unsupported-value'),
            ('selector-url', {}, with_role(selectors=['.a[data-design-id="url(x)"]']), 'unsupported-value'),
            ('selector-2001', {}, with_role(selectors=['.' + 'x' * 2000]), 'unsupported-value'),
            ('selector-number', {}, with_role(selectors=[123]), 'unsupported-value'),
            ('selector-empty', {}, with_role(selectors=['']), 'unsupported-value'),
            ('selector-native-invalid', {}, with_role(selectors=['.1']), 'unsupported-value'),
            ('partly-invalid', {}, [good, role('bad', ['.x'], fontSize=3)], 'unsupported-value'),
            ('partly-malformed', {}, [good, {'id': 'bad'}], 'invalid-message'),
            ('request-over-256kib', {}, selector_limit, 'size-limit'),
        ]

    def test_every_invalid_request_is_rejected_whole_and_keeps_the_previous_preview(self):
        """Given an accepted 24px preview, when each hostile or stale apply arrives, then it
        gets its own correlated rejection and CSS, revision, DOM and rendering stay as they were."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("document.body.classList.add('on-body')")
                self.hello(page)
                self.assertEqual(self.apply(page, [role(fontSize=24)])['revision'], 1)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                for label, top, roles, reason in self.hostile_cases():
                    with self.subTest(case=label):
                        roles_value = [role(fontSize=30)] if roles is DEFAULT else roles
                        reply = self.apply(page, roles_value, **top)
                        self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', reason), reply)
                        self.assertEqual(reply['revision'], 1)
                        self.assertEqual(self.owned(frame), [PLAIN_24])
                        self.assertEqual((self.size(frame), page.evaluate('revision')), ('24px', 1))
                        self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(self.errors(frame), [])

    def test_exact_selector_and_request_id_boundaries_are_accepted(self):
        """Given the longest legal selector, the highest nth-of-type and a 200-character
        request ID, when each is applied, then it is accepted and installed as sent."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                long_selector = '.' + 'x' * 1999
                self.assertEqual(len(long_selector), 2000)
                reply = self.apply(page, [role('edge', [long_selector, 'main > p:nth-of-type(9999)'], fontSize=24)],
                                   requestId='r' * 200)
                self.assertEqual((reply['type'], reply['requestId'], reply['revision']), ('design:roles-applied', 'r' * 200, 1), reply)
                self.assertEqual(reply['outcomes'][0]['matched'], 0)
                self.assertEqual(self.owned(frame), [long_selector + ', main > p:nth-of-type(9999) {\n  font-size: 24px;\n}\n'])

    def test_own_proto_key_in_the_request_or_a_role_rejects_the_whole_operation(self):
        """Given a literal JSON own __proto__ key, when apply carries it at the top level, in
        a role or in its properties, then it is rejected and the page keeps rendering 16px."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                state = page.evaluate('roleState')
                good = role(fontSize=30)
                variants = {
                    'top': {'type': 'design:roles-apply', 'documentId': state['documentId'], 'pageVersion': state['pageVersion'],
                            'roles': [good], '__proto__': {}},
                    'role': {'type': 'design:roles-apply', 'documentId': state['documentId'], 'pageVersion': state['pageVersion'],
                             'roles': [{**good, '__proto__': {}}]},
                    'properties': {'type': 'design:roles-apply', 'documentId': state['documentId'], 'pageVersion': state['pageVersion'],
                                   'roles': [{**good, 'properties': {'fontSize': 30, '__proto__': {}}}]}}
                for label, body in variants.items():
                    with self.subTest(where=label):
                        raw = json.dumps(body)
                        reply = page.evaluate('raw => request(JSON.parse(raw), 3000)', raw)
                        self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', 'invalid-message'), reply)
                        self.assertEqual((self.size(frame), self.owned(frame), page.evaluate('revision')), ('16px', [], 0))

    def test_unknown_field_on_clear_and_stale_clear_are_rejected_without_removing_the_preview(self):
        """Given an applied preview, when clear carries an extra field, a stale revision or
        another document, then each is rejected and the preview keeps rendering."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                for fields, reason in (({'surprise': 1}, 'invalid-message'), ({'baseRevision': 5}, 'revision-conflict'),
                                       ({'documentId': 'elsewhere'}, 'page-changed'), ({'pageVersion': 77}, 'page-changed'),
                                       ({'requestId': ''}, 'invalid-message')):
                    with self.subTest(fields=str(fields)):
                        reply = self.clear(page, **fields)
                        self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', reason), reply)
                        self.assertEqual((self.size(frame), self.owned(frame), page.evaluate('revision')), ('24px', [PLAIN_24], 1))

    def test_canonical_css_boundary_is_exactly_128_kib(self):
        """Given three roles of long distinct selectors, when canonical CSS is exactly 128 KiB
        it installs, and one byte more is rejected as size-limit leaving the first install."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)

                def build(width, extra):
                    roles = [role(f'big{i}', [f'.c{i}-{j:02d}' + 'x' * (width + (1 if i * 32 + j < extra else 0)) for j in range(32)],
                                  fontSize=24) for i in range(3)]
                    css = ''.join(', '.join(r['selectors']) + ' {\n  font-size: 24px;\n}\n' for r in roles)
                    return roles, css
                width = 1000
                while len(build(width + 1, 0)[1].encode('utf-8')) <= 131072:
                    width += 1
                slack = 131072 - len(build(width, 0)[1].encode('utf-8'))
                roles, css = build(width, slack)
                self.assertEqual(len(css.encode('utf-8')), 131072)
                exact = self.apply(page, roles, timeout=8000)
                self.assertEqual(exact['type'], 'design:roles-applied', exact)
                self.assertEqual((exact['canonicalCss'] == css, exact['revision']), (True, 1))
                self.assertEqual(self.owned(frame), [css])
                over_roles, over_css = build(width, slack + 1)
                self.assertEqual(len(over_css.encode('utf-8')), 131073)
                over = self.apply(page, over_roles, timeout=8000)
                self.assertEqual((over['type'], over.get('reason')), ('design:rejected', 'size-limit'), over)
                self.assertEqual((self.owned(frame), page.evaluate('revision')), ([css], 1))

    def test_untrusted_senders_cannot_apply_or_clear(self):
        """Given an applied 24px role, when wrong-session, wrong-protocol, same-origin-script
        and foreign-origin messages try apply and clear, then none changes the page."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                state = ready['roleState']
                before = frame.locator('main').evaluate('el => el.outerHTML')
                apply = {'type': 'design:roles-apply', 'protocolVersion': 1, 'sessionId': 's1', 'requestId': 'hostile-apply',
                         'baseRevision': 0, 'documentId': state['documentId'], 'pageVersion': state['pageVersion'],
                         'roles': [role(fontSize=33)]}
                clear = {'type': 'design:roles-clear', 'protocolVersion': 1, 'sessionId': 's1', 'requestId': 'hostile-clear',
                         'baseRevision': 0, 'documentId': state['documentId'], 'pageVersion': state['pageVersion']}
                page.evaluate("""([apply, clear]) => {
                    for (const m of [apply, clear]) { send({...m, sessionId: 'wrong'}); send({...m, protocolVersion: 2}); }
                }""", [apply, clear])
                frame.evaluate("""([apply, clear]) => { for (const m of [apply, clear]) postMessage(m, location.origin); }""", [apply, clear])
                with page.expect_event('framenavigated', predicate=lambda f: f.url.startswith(EVIL)) as navigation:
                    page.evaluate("""url => {
                        const child = document.createElement('iframe'); child.src = url; document.body.appendChild(child);
                    }""", EVIL + '/host-roles.html?target=' + frame.url)
                navigation.value.evaluate("""([messages, origin]) => { for (const m of messages) parent.frames[0].postMessage(m, origin); }""",
                                          [[apply, clear], frame.url.split('/tests/')[0]])
                # An ordered round trip proves the earlier hostile messages were already handled.
                self.assertTrue(self.detect(page)['complete'])
                self.assertEqual(page.evaluate('revision'), 0)
                self.assertEqual((self.size(frame), self.owned(frame)), ('16px', []))
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertFalse([m for m in self.messages(page, 'design:roles-applied')
                                  if m['requestId'] in ('hostile-apply', 'hostile-clear')])
                hostile = ('hostile-apply', 'hostile-clear')
                self.assertEqual([m for m in self.messages(page, 'design:rejected') if m['requestId'] in hostile], [])
                # A real trusted apply then clear still works, and untrusted clear cannot remove it.
                self.assertEqual(self.apply(page, [role(fontSize=24)])['type'], 'design:roles-applied')
                page.evaluate("clear => send({...clear, baseRevision: 1, sessionId: 'wrong'})", clear)
                self.assertTrue(self.detect(page)['complete'])
                self.assertEqual((self.size(frame), page.evaluate('revision')), ('24px', 1))


class OwnershipAndInstallTests(RoleSheetCase):
    AUTHOR_NODE = """() => {
        const style = document.createElement('style');
        style.id = 'fontkit-role-styles'; style.setAttribute('data-fontkit-role-styles', '');
        style.textContent = '.body-copy { font-size: 19px; }';
        document.head.appendChild(style);
    }"""

    def test_author_node_with_the_same_id_and_attribute_is_never_adopted_edited_or_removed(self):
        """Given an author style with the owned id and attribute, when roles apply, replace,
        clear and the bridge is disposed, then the author node keeps its text and 19px rule."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate(self.AUTHOR_NODE)
                self.hello(page)
                author_html = frame.evaluate("document.getElementById('fontkit-role-styles').outerHTML")
                self.assertEqual(self.size(frame), '19px')
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                sheets = self.owned(frame)
                self.assertEqual(sheets, ['.body-copy { font-size: 19px; }', PLAIN_24])
                self.assertEqual(self.size(frame), '24px')
                self.assertEqual(self.apply(page, [role(fontSize=26)])['type'], 'design:roles-applied')
                self.assertEqual(self.owned(frame), ['.body-copy { font-size: 19px; }', '.body-copy {\n  font-size: 26px;\n}\n'])
                self.clear(page)
                self.assertEqual(self.owned(frame), ['.body-copy { font-size: 19px; }'])
                self.assertEqual(self.size(frame), '19px')
                self.apply(page, [role(fontSize=24)])
                frame.evaluate('__fontkitBridge.dispose()')
                self.assertEqual(self.owned(frame), ['.body-copy { font-size: 19px; }'])
                self.assertEqual(frame.evaluate("document.getElementById('fontkit-role-styles').outerHTML"), author_html)
                self.assertEqual(self.size(frame), '19px')

    def test_the_owned_node_lives_in_head_with_the_documented_markers(self):
        """Given a page with no author style of that id, when a role is applied, then exactly
        one style in head carries the owned id and marker, and it is enabled with one rule."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                found = frame.evaluate("""() => Array.from(document.querySelectorAll('style#fontkit-role-styles')).map(s =>
                    [s.parentElement.tagName, s.getAttribute('data-fontkit-role-styles'), s.sheet.disabled, s.sheet.cssRules.length])""")
                self.assertEqual(found, [['HEAD', '', False, 1]])

    def test_csp_without_inline_styles_rejects_as_blocked_and_keeps_the_page(self):
        """Given a style-src policy refusing inline styles, when a role is applied, then it is
        rejected as stylesheet-blocked, no node or revision appears and rendering is unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, headers={'content-security-policy': "style-src 'self'"})
                ready = self.hello(page)
                before = frame.locator(BODY).first.evaluate("el => [getComputedStyle(el).fontSize, getComputedStyle(el).fontFamily]")
                html = frame.locator('main').evaluate('el => el.outerHTML')
                reply = self.apply(page, [role(fontSize=40)])
                self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'stylesheet-blocked'), reply)
                self.assertEqual(reply['revision'], 0)
                self.assertEqual(self.owned(frame), [])
                self.assertEqual(frame.locator(BODY).first.evaluate("el => [getComputedStyle(el).fontSize, getComputedStyle(el).fontFamily]"), before)
                self.assertNotEqual(before[0], '40px')
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), html)
                self.assertEqual(self.hello(page, 'after-blocked')['roleState']['canonicalCss'], '')
                self.assertEqual(ready['roleState']['roles'], [])

    def test_a_policy_added_after_an_accepted_apply_blocks_replacement_but_keeps_the_prior_preview(self):
        """Given an accepted 24px preview, when a meta policy then forbids inline styles and a
        replacement is applied, then it is blocked and the 24px CSS, roles and revision remain."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertEqual(self.apply(page, [role(fontSize=24)])['revision'], 1)
                frame.evaluate("""() => {
                    const meta = document.createElement('meta');
                    meta.httpEquiv = 'content-security-policy'; meta.content = "style-src 'self'";
                    document.head.appendChild(meta);
                }""")
                reply = self.apply(page, [role(fontSize=30)], **self.current(page))
                self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', 'stylesheet-blocked'), reply)
                self.assertEqual((self.owned(frame), self.size(frame), page.evaluate('revision')), ([PLAIN_24], '24px', 1))
                state = self.hello(page, 'retained')['roleState']
                self.assertEqual((state['canonicalCss'], state['cssHash'], len(state['roles'])), (PLAIN_24, PLAIN_24_HASH, 1))

    def test_dispose_removes_the_owned_node_and_suppresses_a_pending_receipt(self):
        """Given an apply whose receipt is still waiting for a frame, when the bridge is
        disposed, then the owned node is gone and no receipt arrives for that request."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                self.assertEqual(self.size(frame), '24px')
                start = self.mark(page)
                state = page.evaluate('roleState')
                frame.evaluate("""() => addEventListener('message', function once(event) {
                    if (event.data.type !== 'design:roles-apply') return;
                    removeEventListener('message', once); __fontkitBridge.dispose();
                })""")
                page.evaluate("""([doc, version]) => send({type:'design:roles-apply', protocolVersion:1, sessionId, requestId:'disposed',
                    baseRevision: 1, documentId: doc, pageVersion: version, roles: [{id:'body', name:'Body', selectors:['.body-copy'],
                    adapter:'plain', properties:{fontSize: 31}}]})""", [state['documentId'], state['pageVersion']])
                frame.evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                self.assertEqual(self.owned(frame), [])
                self.assertEqual(self.size(frame), '16px')
                self.assertFalse([m for m in self.messages(page, 'design:roles-applied', start) if m['requestId'] == 'disposed'])


class CommitReceiptAndQueueTests(RoleSheetCase):
    def mutate_after_commit(self, frame, script):
        frame.evaluate("""script => addEventListener('message', function once(event) {
            if (event.data.type !== 'design:roles-apply') return;
            removeEventListener('message', once); new Function(script)();
        })""", script)

    def test_author_dom_change_after_commit_is_an_applied_receipt_with_stale_outcomes(self):
        """Given an apply that commits, when the author adds a paragraph in the same task, then
        the 24px rendering stays, one receipt keeps the captured identity and outcomes are stale."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                start = self.mark(page)
                self.mutate_after_commit(frame, """const p = document.createElement('p'); p.textContent = 'Late author text';
                    document.querySelector('main').appendChild(p);""")
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['revision'], reply['pageVersion']), (1, ready['roleState']['pageVersion']))
                self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                self.assertEqual((reply['roles'], reply['canonicalCss'], reply['cssHash']), ([role(fontSize=24)], PLAIN_24, PLAIN_24_HASH))
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason'], reply['outcomes']), (False, 'page-changed', []))
                self.assertEqual((self.size(frame), self.owned(frame), page.evaluate('revision')), ('24px', [PLAIN_24], 1))
                self.assertEqual(len([m for m in self.messages(page, 'design:roles-applied', start) if m['requestId'] == reply['requestId']]), 1)
                self.assertFalse(self.messages(page, 'design:rejected', start))

    def test_history_change_after_commit_is_an_applied_receipt_with_the_current_url(self):
        """Given an apply that commits, when the page URL changes in the same task, then the
        receipt reports the new current URL beside the captured identity and stale outcomes."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                self.mutate_after_commit(frame, "history.replaceState(null, '', location.pathname + '?moved');")
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertTrue(reply['currentPageURL'].endswith('?moved'), reply['currentPageURL'])
                self.assertNotEqual(reply['currentPageURL'], ready['roleState']['pageURL'])
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason'], reply['outcomes']), (False, 'page-changed', []))
                self.assertEqual((self.size(frame), reply['revision']), ('24px', 1))

    def test_queued_inspector_edit_and_clear_each_settle_with_their_own_authenticated_reply(self):
        """Given an apply followed at once by an inspector edit, then a clear, when all three
        settle, then each has its own reply, revisions rise by one, and rendering matches each step."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                state = page.evaluate('roleState')
                start = self.mark(page)
                first, second = page.evaluate("""([doc, version]) => Promise.all([
                    request({type:'design:roles-apply', documentId: doc, pageVersion: version, baseRevision: 0,
                        roles: [{id:'body', name:'Body', selectors:['.body-copy'], adapter:'plain', properties:{fontSize: 24}}]}, 4000),
                    request({type:'design:update', targetId:'ordinary.body', patch:{fontSize: 27}, baseRevision: 1}, 4000)])""",
                                              [state['documentId'], state['pageVersion']])
                self.assertEqual((second['type'], second['revision']), ('design:applied', 2), second)
                self.assertEqual((first['type'], first['operation'], first['revision']), ('design:roles-applied', 'apply', 1), first)
                # The receipt's frame may land before or after the edit message: either way it is committed, and
                # its outcomes are either stale (edit first) or measured (frame first). The claim is the sequence.
                stale = (False, 'page-changed', [])
                measured = (True, None, [{'id': 'body', 'matched': 2, 'checked': 2, 'mismatched': 0, 'complete': True, 'losses': []}])
                self.assertIn((first['outcomesComplete'], first['outcomeReason'], first['outcomes']), (stale, measured))
                self.assertEqual((self.size(frame, '[data-design-id="role.body"]'), self.size(frame, '[data-design-id="ordinary.body"]')),
                                 ('24px', '27px'))
                # Bridge-originated inline writes never advance the wire page version: Studio's version is still current.
                cleared = self.clear(page)
                self.assertEqual((cleared['type'], cleared['operation'], cleared['revision']), ('design:roles-applied', 'clear', 3), cleared)
                self.assertEqual(cleared['pageVersion'], state['pageVersion'])
                self.assertEqual((self.size(frame, '[data-design-id="role.body"]'), self.size(frame, '[data-design-id="ordinary.body"]')),
                                 ('16px', '27px'))
                self.assertEqual(page.evaluate('revision'), 3)
                self.assertEqual(len(self.messages(page, 'design:roles-applied', start)), 2)

    def test_receipt_survives_a_detect_sent_during_the_frame_wait(self):
        """Given an apply whose measurement waits for a frame, when a detect is sent at once,
        then detect completes and the apply still gets exactly one measured receipt."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                state = page.evaluate('roleState')
                start = self.mark(page)
                receipt, detected = page.evaluate("""([doc, version]) => Promise.all([
                    request({type:'design:roles-apply', documentId: doc, pageVersion: version, baseRevision: 0,
                        roles: [{id:'body', name:'Body', selectors:['.body-copy'], adapter:'plain', properties:{fontSize: 24}}]}, 4000),
                    request({type:'design:detect', documentId: doc}, 4000)])""", [state['documentId'], state['pageVersion']])
                self.assertEqual(detected['type'], 'design:detected', detected)
                self.assertTrue(detected['complete'], detected)
                self.assertEqual(receipt['type'], 'design:roles-applied', receipt)
                self.assertEqual((receipt['outcomesComplete'], receipt['outcomeReason']), (True, None), receipt)
                self.assertEqual([(o['matched'], o['checked'], o['mismatched']) for o in receipt['outcomes']], [(2, 2, 0)])
                self.assertEqual(len(self.messages(page, 'design:roles-applied', start)), 1)
                self.assertEqual(self.size(frame), '24px')

    def test_hello_replacing_the_session_suppresses_the_old_receipt_and_ready_carries_the_snapshot(self):
        """Given an apply awaiting its frame, when the same session id says hello again, then
        no receipt reaches the new session and ready carries the accepted snapshot without replay."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                state = page.evaluate('roleState')
                start = self.mark(page)
                # The page re-sends hello in the same task as the commit, before any frame can paint.
                frame.evaluate("""studio => addEventListener('message', function once(event) {
                    if (event.data.type !== 'design:roles-apply') return;
                    removeEventListener('message', once);
                    dispatchEvent(new MessageEvent('message', {data: {type: 'design:hello', protocolVersion: 1, sessionId: 's1'},
                        origin: studio, source: parent}));
                })""", STUDIO)
                page.evaluate("""([doc, version]) => send({type:'design:roles-apply', protocolVersion:1, sessionId, requestId:'before-hello',
                    baseRevision: 0, documentId: doc, pageVersion: version, roles: [{id:'body', name:'Body', selectors:['.body-copy'],
                    adapter:'plain', properties:{fontSize: 24}}]})""", [state['documentId'], state['pageVersion']])
                ready = self.hello(page)
                self.assertEqual(ready['revision'], 1)
                frame.evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                self.assertFalse([m for m in self.messages(page, 'design:roles-applied', start) if m['requestId'] == 'before-hello'])
                snapshot = ready['roleState']
                self.assertEqual((snapshot['roles'], snapshot['canonicalCss'], snapshot['cssHash']), ([role(fontSize=24)], PLAIN_24, PLAIN_24_HASH))
                self.assertEqual((self.owned(frame), self.size(frame)), ([PLAIN_24], '24px'))
                later = self.mark(page)
                again = self.hello(page, 's2')
                self.assertEqual(again['roleState']['canonicalCss'], PLAIN_24)
                self.assertFalse(self.messages(page, 'design:roles-applied', later))


class UndoAndResetTests(RoleSheetCase):
    def test_apply_replace_repeat_clear_round_trip_restores_author_dom_and_computed_styles(self):
        """Given a frozen page, when roles apply, replace, repeat and clear twice, then the
        author DOM and every computed style equal the pre-apply snapshot byte for byte."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                before = self.snapshot(frame)
                self.assertEqual(self.apply(page, [role(fontSize=24)])['revision'], 1)
                self.assertEqual(self.snapshot(frame, drop_owned=True)['html'], before['html'])
                self.assertEqual(self.apply(page, [role(fontSize=30, fontWeight=700)])['revision'], 2)
                self.assertEqual(self.owned(frame), ['.body-copy {\n  font-size: 30px;\n  font-weight: 700;\n}\n'])
                self.assertEqual(self.apply(page, [role(fontSize=30, fontWeight=700)])['revision'], 3)
                self.assertEqual(len(self.owned(frame)), 1)
                self.assertEqual(self.snapshot(frame, drop_owned=True)['html'], before['html'])
                self.assertEqual(self.clear(page)['revision'], 4)
                self.assertEqual(self.clear(page)['revision'], 5)
                after = self.snapshot(frame)
                self.assertEqual(after['html'], before['html'])
                self.assertEqual(after['styles'], before['styles'])
                self.assertEqual(self.errors(frame), [])

    def test_global_reset_clears_roles_in_one_revision_and_replies_with_the_empty_snapshot(self):
        """Given an applied preview and an inspector edit, when the global reset runs, then one
        revision clears both and the legacy reply carries the authenticated empty roleState."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                ready = self.hello(page)
                self.apply(page, [role(fontSize=24)])
                self.update(page, 'ordinary.body', {'fontSize': 27})
                self.assertEqual(page.evaluate('revision'), 2)
                reply = self.request(page, {'type': 'design:reset'})
                self.assertEqual((reply['type'], reply['targetId'], reply['revision']), ('design:applied', 'global', 3), reply)
                identity = self.current(page)
                self.assertEqual(reply['roleState'], {'documentId': ready['roleState']['documentId'],
                                                      'pageVersion': identity['pageVersion'], 'pageURL': frame.url, 'roles': [],
                                                      'canonicalCss': '', 'hashAlgorithm': 'fnv1a32', 'cssHash': EMPTY_HASH})
                self.assertEqual((self.owned(frame), self.size(frame), self.size(frame, BODY, 1)), ([], '16px', '16px'))
                self.assertFalse(self.messages(page, 'design:roles-applied', 0)[1:], 'a reset never settles a role request')

    def test_target_reset_leaves_the_role_preview_and_state_untouched(self):
        """Given an applied preview and an inspector edit, when only that target resets, then
        the role CSS keeps rendering and the legacy reply carries no role snapshot."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                self.update(page, 'ordinary.body', {'fontSize': 27})
                reply = self.request(page, {'type': 'design:reset', 'targetId': 'ordinary.body'})
                self.assertEqual((reply['type'], reply['reset'], reply['revision']), ('design:applied', True, 3), reply)
                self.assertNotIn('roleState', reply)
                self.assertEqual((self.owned(frame), self.size(frame), self.size(frame, BODY, 1)), ([PLAIN_24], '24px', '24px'))
                state = self.hello(page, 'after-target-reset')['roleState']
                self.assertEqual((state['canonicalCss'], state['cssHash']), (PLAIN_24, PLAIN_24_HASH))

    def test_ready_after_rehello_carries_the_snapshot_and_nothing_is_replayed(self):
        """Given an accepted preview, when Studio says hello again, then ready reports the
        accepted roles, bytes and digest at the same revision and the target is not re-applied."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                receipt = self.apply(page, [role(fontSize=24)])
                node = frame.evaluate("(() => { window.__owned = document.querySelector('style[data-fontkit-role-styles]'); return true; })()")
                self.assertTrue(node)
                ready = self.hello(page, 'again')
                self.assertEqual(ready['revision'], 1)
                self.assertEqual({k: ready['roleState'][k] for k in ('roles', 'canonicalCss', 'hashAlgorithm', 'cssHash')},
                                 {k: receipt[k] for k in ('roles', 'canonicalCss', 'hashAlgorithm', 'cssHash')})
                self.assertTrue(frame.evaluate("window.__owned === document.querySelector('style[data-fontkit-role-styles]')"))
                self.assertEqual(page.evaluate('revision'), 1)


class UnavailableUrlTests(RoleSheetCase):
    PATH = '/tests/fixtures/bridge/target-role-protocol.html'

    def over_limit(self):
        return ROLE_PAGE + '?' + 'x' * (2000 - len(self.PATH))

    def test_apply_cannot_commit_under_an_unavailable_url_but_clear_and_reset_still_work(self):
        """Given a real 2,001-character route, when apply is sent, then it is rejected without
        installing anything, while clear and global reset return null-URL empty receipts."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=self.over_limit())
                self.assertEqual(frame.evaluate('location.pathname.length + location.search.length + location.hash.length'), 2001)
                ready = self.hello(page)
                self.assertIsNone(ready['roleState']['pageURL'])
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual((reply['type'], reply['reason'], reply['detail']),
                                 ('design:rejected', 'unsupported-value', 'Unsupported page URL'), reply)
                self.assertEqual((self.owned(frame), self.size(frame), page.evaluate('revision')), ([], '16px', 0))
                self.assertEqual(self.apply(page, [])['reason'], 'unsupported-value')
                cleared = self.clear(page)
                self.assertEqual((cleared['type'], cleared['operation'], cleared['revision'], cleared['currentPageURL']),
                                 ('design:roles-applied', 'clear', 1, None), cleared)
                self.assertEqual((cleared['canonicalCss'], cleared['outcomesComplete'], cleared['outcomeReason'], cleared['outcomes']),
                                 ('', True, None, []))
                reset = self.request(page, {'type': 'design:reset'})
                self.assertEqual((reset['type'], reset['revision']), ('design:applied', 2), reset)
                self.assertIsNone(reset['roleState']['pageURL'])
                self.assertEqual((reset['roleState']['roles'], reset['roleState']['canonicalCss'], reset['roleState']['cssHash']),
                                 ([], '', EMPTY_HASH))
                self.assertEqual(self.update(page, 'ordinary.body', {'fontSize': 27})['type'], 'design:applied')

    def test_exact_2000_character_route_applies_and_a_later_over_limit_route_gives_a_stale_receipt(self):
        """Given a route of exactly 2,000 characters, when apply commits and the URL then
        becomes unsupported, then the accepted CSS stays and the receipt has a null current URL."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=ROLE_PAGE + '?' + 'x' * (1999 - len(self.PATH)))
                self.assertEqual(frame.evaluate('location.pathname.length + location.search.length + location.hash.length'), 2000)
                ready = self.hello(page)
                self.assertEqual(ready['roleState']['pageURL'], frame.url)
                frame.evaluate("""() => addEventListener('message', function once(event) {
                    if (event.data.type !== 'design:roles-apply') return;
                    removeEventListener('message', once);
                    history.replaceState(null, '', '/?' + 'y'.repeat(1999));
                })""")
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['revision'], reply['currentPageURL'], reply['outcomesComplete'], reply['outcomeReason'],
                                  reply['outcomes']), (1, None, False, 'page-changed', []))
                self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                self.assertEqual((reply['canonicalCss'], self.owned(frame), self.size(frame)), (PLAIN_24, [PLAIN_24], '24px'))
                self.assertNotIn('y' * 1999, json.dumps(reply))
                cleared = self.clear(page, **self.current_unavailable(page))
                self.assertEqual((cleared['operation'], cleared['currentPageURL'], cleared['outcomesComplete']), ('clear', None, True))
                self.assertEqual((self.owned(frame), self.size(frame)), ([], '16px'))

    def current_unavailable(self, page):
        """A detect is refused under a null URL, so a fresh ready supplies the current page version."""
        ready = self.hello(page, 'unavailable-now')
        self.assertIsNone(ready['roleState']['pageURL'])
        return {'documentId': ready['roleState']['documentId'], 'pageVersion': ready['roleState']['pageVersion']}


class BaselineDetectTests(RoleSheetCase):
    def test_detect_reports_the_app_baseline_while_the_preview_keeps_rendering(self):
        """Given a 24px preview and a 27px inspector edit, when detect runs, then groups report
        the 16px baseline and the 27px edit, never the preview, and the target still renders 24px."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.apply(page, [role(fontSize=24)])
                self.update(page, 'ordinary.body', {'fontSize': 27})
                self.assertEqual(self.size(frame, '[data-design-id="role.body"]'), '24px')
                reply = self.detect(page, knownRoles=[{'id': 'body', 'selectors': [BODY]}], **{})
                self.assertTrue(reply['complete'], reply)
                sizes = sorted(s['style']['fontSize'] for g in reply['groups'] for s in g['signatures'])
                self.assertEqual(sizes, [16, 27])
                check = reply['selectorChecks'][0]
                self.assertEqual(sorted((s['style']['fontSize'], s['count']) for s in check['signatures']), [(16, 1), (27, 1)])
                self.assertEqual(check['matchCount'], 2)
                self.assertEqual(self.size(frame, '[data-design-id="role.body"]'), '24px')
                self.assertEqual(self.owned(frame), [PLAIN_24])
                self.assertFalse(frame.evaluate("document.querySelector('style[data-fontkit-role-styles]').sheet.disabled"))

    def test_detect_never_drops_the_preview_between_frames_on_the_5000_parent_corpus(self):
        """Given a 40px preview on the 5,000-parent page, when detect scans across many frames,
        then every sampled frame renders 40px, groups report the 20px baseline and D058 holds."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                self.hello(page)
                receipt = self.apply(page, [role('g00', ['.g00'], fontSize=40)], timeout=15000)
                self.assertEqual(receipt['type'], 'design:roles-applied', receipt)
                self.assertTrue(receipt['outcomesComplete'], receipt)
                self.assertEqual((receipt['outcomes'][0]['matched'], receipt['outcomes'][0]['mismatched']), (250, 0))
                self.assertEqual(self.size(frame, '.g00'), '40px')
                frame.evaluate("""() => {
                    window.samples = []; window.sampling = true;
                    const el = document.querySelector('.g00');
                    const tick = () => { samples.push(getComputedStyle(el).fontSize); if (sampling) requestAnimationFrame(tick); };
                    requestAnimationFrame(tick);
                }""")
                beat = frame.evaluate('fixtureProbe.heartbeat')
                reply = page.evaluate('() => request({type:"design:detect"}, 15000)')
                frame.evaluate('window.sampling = false')
                samples = frame.evaluate('samples')
                heartbeat = frame.evaluate('fixtureProbe.heartbeat')
                print('APPLY_THEN_DETECT ' + json.dumps({'elapsedMs': reply.get('elapsedMs'), 'complete': reply.get('complete'),
                      'scanned': reply.get('scannedElements'), 'frames': len(samples), 'heartbeat': [beat, heartbeat]}), flush=True)
                self.assertTrue(reply['complete'], reply)
                self.assertEqual(reply['scannedElements'], 5000)
                self.assertLessEqual(reply['elapsedMs'], 2000)
                self.assertGreater(len(samples), 2, 'the scan must span several animation frames')
                self.assertGreater(heartbeat, beat)
                self.assertEqual(set(samples), {'40px'})
                g00 = next(g for g in reply['groups'] if g['selectors'] and g['selectors'][0]['value'] == '.g00')
                self.assertEqual([s['style']['fontSize'] for s in g00['signatures']], [20])
                self.assertEqual(self.size(frame, '.g00'), '40px')
                self.assertFalse(frame.evaluate("document.querySelector('style[data-fontkit-role-styles]').sheet.disabled"))

    def test_detect_under_a_body_variable_preview_finishes_and_never_drops_the_preview(self):
        """Given a body preview with a family on the 5,000-parent page that defines both body variables, when detect scans across
        many frames, then the reply is complete with 5,000 elements within 2,000 ms, spans several frames while the heartbeat
        advances, every sampled frame shows the preview family on .g00 and on an element that takes its family only from the
        variable, and the .g00 group reports the page's own serif."""
        css = (':root { --bs-body-font-family: Arial, sans-serif; --bs-font-sans-serif: Arial, sans-serif; }'
               ' body { font-family: var(--bs-body-font-family); }')
        add_style = "(css) => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); }"
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                frame.evaluate(add_style, css)
                self.hello(page)
                preview = {**role('g00', ['.g00'], fontFamily='Georgia, serif'), 'adapter': 'bootstrap5-body'}
                receipt = self.apply(page, [preview], timeout=15000)
                self.assertEqual(receipt['type'], 'design:roles-applied', receipt)
                frame.evaluate("""() => {
                    window.samples = []; window.sampling = true;
                    const el = document.querySelector('.g00'), inherited = document.querySelector('#corpus');
                    const tick = () => {
                        samples.push([getComputedStyle(el).fontFamily, getComputedStyle(inherited).fontFamily]);
                        if (sampling) requestAnimationFrame(tick);
                    };
                    requestAnimationFrame(tick);
                }""")
                beat = frame.evaluate('fixtureProbe.heartbeat')
                reply = page.evaluate('() => request({type:"design:detect"}, 15000)')
                frame.evaluate('window.sampling = false')
                samples = frame.evaluate('samples')
                heartbeat = frame.evaluate('fixtureProbe.heartbeat')
                print('BODY_PREVIEW_DETECT ' + json.dumps({'elapsedMs': reply.get('elapsedMs'), 'complete': reply.get('complete'),
                      'reason': reply.get('reason'), 'scanned': reply.get('scannedElements'), 'frames': len(samples),
                      'heartbeat': [beat, heartbeat]}), flush=True)
                self.assertTrue(reply['complete'], reply.get('reason'))
                self.assertEqual(reply['scannedElements'], 5000)
                self.assertLessEqual(reply['elapsedMs'], 2000)
                self.assertGreater(len(samples), 2, 'the scan must span several animation frames')
                self.assertGreater(heartbeat, beat)
                self.assertEqual({tuple(pair) for pair in samples}, {('Georgia, serif', 'Georgia, serif')})
                g00 = next(g for g in reply['groups'] if g['selectors'] and g['selectors'][0]['value'] == '.g00')
                self.assertEqual([s['style']['fontFamily'] for s in g00['signatures']], ['serif'])
                self.assertFalse(frame.evaluate("document.querySelector('style[data-fontkit-role-styles]').sheet.disabled"))


class SplitPageVersionTests(RoleSheetCase):
    def test_native_hover_focus_and_press_between_detect_and_apply_do_not_reject_the_apply(self):
        """Given a detect result, when the user hovers and presses in the target, then
        apply with the detected page version is accepted and renders."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                detected = self.detect(page)
                frame.locator('[data-design-id="ordinary.body"]').hover()
                frame.locator('main').click(position={'x': 5, 'y': 5})
                reply = self.apply(page, [role(fontSize=24)], pageVersion=detected['pageVersion'], documentId=detected['documentId'])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual(self.size(frame), '24px')

    def test_author_dom_or_url_change_between_detect_and_apply_is_rejected_as_page_changed(self):
        """Given a detect result, when the author adds a node or changes the URL, then apply
        with the detected version is page-changed and nothing renders."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                for label, script in (('dom', "document.querySelector('main').appendChild(document.createElement('hr'))"),
                                      ('url', "history.replaceState(null, '', location.pathname + '?moved')")):
                    with self.subTest(change=label):
                        detected = self.detect(page)  # fresh identity, so each case can only fail on its own change
                        frame.evaluate(script)
                        reply = self.apply(page, [role(fontSize=24)], pageVersion=detected['pageVersion'],
                                           documentId=detected['documentId'])
                        self.assertEqual((reply['type'], reply.get('reason')), ('design:rejected', 'page-changed'), reply)
                        self.assertEqual((self.size(frame), self.owned(frame), page.evaluate('revision')), ('16px', [], 0))

    def test_inspector_edit_and_global_reset_do_not_advance_the_wire_page_version(self):
        """Given a known page version, when inspector edits and a global reset run, then the
        version stays and an apply with it is accepted."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                version = self.detect(page)['currentPageVersion']
                self.update(page, 'ordinary.body', {'fontSize': 27, 'text': 'Edited'})
                self.assertEqual(self.detect(page)['currentPageVersion'], version)
                self.request(page, {'type': 'design:reset'})
                self.assertEqual(self.detect(page)['currentPageVersion'], version)
                self.assertEqual(self.apply(page, [role(fontSize=24)], pageVersion=version)['type'], 'design:roles-applied')

    def test_author_callback_mutation_during_an_acknowledged_edit_still_advances_the_wire_page_version(self):
        """Given an onApplied callback that adds an author node, when an inspector edit is
        acknowledged, then the next detect reports a newer page version than before the edit."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                before = self.detect(page)['currentPageVersion']
                frame.evaluate("""() => {
                    __fontkitBridge.options.onApplied = () => {
                        const note = document.createElement('p'); note.textContent = 'Author callback text';
                        document.querySelector('main').appendChild(note);
                    };
                }""")
                self.assertEqual(self.update(page, 'ordinary.body', {'fontSize': 27})['type'], 'design:applied')
                self.assertEqual(frame.locator('main > p').last.inner_text(), 'Author callback text')
                after = self.detect(page)['currentPageVersion']
                self.assertGreater(after, before)

    def test_native_hover_during_a_scan_still_makes_it_page_changed_with_equal_versions(self):
        """Given a pending scan of the 5,000-parent page, when the user hovers in the target
        part-way through it, then the scan is incomplete as page-changed and its two versions
        are equal; a hover that lands outside the scan fails the premise instead of passing."""
        attempts = []
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for fraction in (0.3, 0.2, 0.1):
                    page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                    self.hello(page)
                    self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                    frame.evaluate("""() => {
                        window.probe = {};
                        addEventListener('message', event => { if (event.data.type === 'design:detect') probe.scan = performance.now(); }, true);
                        document.addEventListener('pointerover', () => { probe.hover = probe.hover || performance.now(); }, true);
                    }""")
                    box = frame.locator('#responsiveness').bounding_box()
                    calibration = self.detect(page)
                    self.assertTrue(calibration['complete'], calibration)
                    frame.evaluate('() => { probe.scan = undefined; probe.hover = undefined; }')
                    page.evaluate('() => { window.pendingDetect = request({type:"design:detect"}, 15000); }')
                    frame.evaluate("""wait => new Promise(resolve => {
                        const tick = () => (probe.scan !== undefined && performance.now() - probe.scan >= wait ? resolve() : requestAnimationFrame(tick));
                        requestAnimationFrame(tick);
                    })""", calibration['elapsedMs'] * fraction)
                    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    reply = page.evaluate('() => window.pendingDetect')
                    delay = frame.evaluate('probe.hover === undefined ? null : probe.hover - probe.scan')
                    attempts.append({'fraction': fraction, 'calibrationMs': round(calibration['elapsedMs'], 1), 'hoverDelayMs': delay,
                                     'replyMs': round(reply['elapsedMs'], 1)})
                    # Margin: the hover must land in the first half of the calibrated scan, well before it ends.
                    if delay is not None and delay <= calibration['elapsedMs'] / 2 and delay < reply['elapsedMs']:
                        break
                else:
                    self.fail('the hover never landed while the scan was pending: ' + json.dumps(attempts))
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), (reply, attempts))
                self.assertEqual(reply['currentPageVersion'], reply['pageVersion'])

    def test_writes_made_by_an_order_changed_listener_advance_the_page_version(self):
        """Given a legacy layout update, when the bridge reorders without a listener, then the
        version stays; and when a design:order-changed listener appends a node, then an apply with
        the version detected before it is rejected as page-changed, because the listener's write
        is an author change while the bridge's own reordering is not."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                patch = {'slots': [{'id': 'a', 'targetId': 'role.body', 'type': 'text', 'size': 16, 'textTouched': False},
                                   {'id': 'b', 'targetId': 'ordinary.body', 'type': 'text', 'size': 16, 'textTouched': False}],
                         'layout': {'order': [{'id': 'a', 'role': 'metadata', 'index': 1}, {'id': 'b', 'role': 'h1', 'index': 0}]}}
                before = self.detect(page)['currentPageVersion']
                self.assertEqual(self.request(page, {'type': 'design:update', 'patch': patch})['type'], 'design:applied')
                # Without a listener the bridge's own reordering is not an author change.
                self.assertEqual(self.detect(page)['currentPageVersion'], before)
                frame.evaluate("""() => addEventListener('design:order-changed', () => {
                    const note = document.createElement('p'); note.textContent = 'Listener node';
                    document.querySelector('main').appendChild(note);
                })""")
                detected = self.detect(page)
                reply = self.request(page, {'type': 'design:update', 'patch': patch})
                self.assertEqual(reply['type'], 'design:applied', reply)
                self.assertEqual(frame.locator('main > p').last.inner_text(), 'Listener node')
                rejected = self.apply(page, [role(fontSize=24)], pageVersion=detected['pageVersion'], documentId=detected['documentId'])
                self.assertEqual((rejected['type'], rejected.get('reason')), ('design:rejected', 'page-changed'), rejected)
                self.assertEqual(self.size(frame), '16px')

    def test_an_author_font_loading_after_a_commit_does_not_advance_the_wire_page_version(self):
        """Given a role naming an author @font-face whose file is held back, when the apply commits
        and the font then finishes loading, then a second apply and a clear carrying the receipt's
        version are both accepted, not rejected as page-changed."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                held = []
                page.context.route('**/held-font.woff2', lambda route: held.append(route))
                self.addCleanup(lambda: [route.abort() for route in held[1:]])
                frame.evaluate("""() => { const style = document.createElement('style');
                    style.textContent = "@font-face { font-family: Probe; src: url(/held-font.woff2) format('woff2'); }";
                    document.head.appendChild(style); }""")
                self.hello(page)
                first = self.apply(page, [role(fontFamily='Probe, serif')])
                self.assertEqual(first['type'], 'design:roles-applied', first)
                self.assertEqual(first['currentPageVersion'], first['pageVersion'])
                frame.wait_for_function("() => document.fonts.status === 'loading'")
                self.assertEqual(len(held), 1)
                held[0].fulfill(status=200, body=b'not a font', headers={'content-type': 'font/woff2'})
                frame.wait_for_function("() => document.fonts.status === 'loaded'")
                version = {'pageVersion': first['pageVersion'], 'documentId': first['documentId']}
                second = self.apply(page, [role(fontFamily='Probe, serif', fontSize=24)], **version)
                self.assertEqual((second['type'], second['revision']), ('design:roles-applied', 2), second)
                cleared = self.clear(page, **version)
                self.assertEqual((cleared['type'], cleared['revision']), ('design:roles-applied', 3), cleared)

    def test_a_font_load_during_a_pending_scan_makes_it_page_changed_with_equal_versions(self):
        """Given a pending scan of the 5,000-parent page, when a font starts loading part-way
        through it, then the scan is incomplete as page-changed and its two versions are equal."""
        attempts = []
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for fraction in (0.3, 0.2, 0.1):
                    page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                    self.hello(page)
                    frame.evaluate("""() => {
                        window.probe = {};
                        addEventListener('message', event => { if (event.data.type === 'design:detect') probe.scan = performance.now(); }, true);
                        document.fonts.addEventListener('loading', () => { probe.font = probe.font || performance.now(); });
                    }""")
                    calibration = self.detect(page)
                    self.assertTrue(calibration['complete'], calibration)
                    frame.evaluate('() => { probe.scan = undefined; probe.font = undefined; }')
                    page.evaluate('() => { window.pendingDetect = request({type:"design:detect"}, 15000); }')
                    frame.evaluate("""wait => new Promise(resolve => {
                        const tick = () => (probe.scan !== undefined && performance.now() - probe.scan >= wait ? resolve() : requestAnimationFrame(tick));
                        requestAnimationFrame(tick);
                    })""", calibration['elapsedMs'] * fraction)
                    frame.evaluate("""() => { const face = new FontFace('Late', 'url(data:font/woff2;base64,AAAA)');
                        document.fonts.add(face); face.load().catch(() => {}); }""")
                    reply = page.evaluate('() => window.pendingDetect')
                    delay = frame.evaluate('probe.font === undefined ? null : probe.font - probe.scan')
                    attempts.append({'fraction': fraction, 'fontDelayMs': delay, 'replyMs': round(reply['elapsedMs'], 1)})
                    if delay is not None and delay <= calibration['elapsedMs'] / 2 and delay < reply['elapsedMs']:
                        break
                else:
                    self.fail('the font load never landed while the scan was pending: ' + json.dumps(attempts))
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), (reply, attempts))
                self.assertEqual(reply['currentPageVersion'], reply['pageVersion'])

    def test_native_event_during_the_frame_wait_makes_the_receipt_stale_with_equal_versions(self):
        """Given a committed apply, when a pointer event (dispatched by the page, so it is not
        a trusted user event) reaches the page before the frame, then the receipt keeps the
        committed CSS but has stale outcomes and equal versions."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                frame.evaluate("""() => addEventListener('message', function once(event) {
                    if (event.data.type !== 'design:roles-apply') return;
                    removeEventListener('message', once);
                    document.querySelector('main').dispatchEvent(new PointerEvent('pointerover', {bubbles: true}));
                })""")
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason'], reply['outcomes']), (False, 'page-changed', []))
                self.assertEqual(reply['currentPageVersion'], reply['pageVersion'])
                self.assertEqual((self.size(frame), self.owned(frame)), ('24px', [PLAIN_24]))

    def test_render_only_change_during_a_scan_is_page_changed_without_a_wire_version_bump(self):
        """Given an author animation that changes rendering with no DOM or rule change, when a
        scan finishes, then it is incomplete as page-changed and the two versions are equal."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                frame.evaluate("""() => {
                    const style = document.createElement('style');
                    style.textContent = '@keyframes grow {from {font-size: 20px} to {font-size: 36px}} .g00 {animation: grow 4s linear}';
                    document.head.appendChild(style);
                }""")
                self.hello(page)
                reply = self.detect(page)
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), reply)
                self.assertEqual(reply['currentPageVersion'], reply['pageVersion'])


class BridgeFontLinkTests(RoleSheetCase):
    def test_inspector_font_stylesheet_and_global_reset_do_not_advance_the_wire_page_version(self):
        """Given a known page version, when an inspector edit injects a font stylesheet that
        then loads, and a global reset removes it, then apply and a queued clear carrying the
        pre-edit version are accepted."""
        css = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                # Registered last, so it runs first: a local fulfilment, no external contact.
                page.context.route('https://fonts.googleapis.com/**', lambda route: route.fulfill(
                    status=200, body='.inter-probe { color: red; }', content_type='text/css'))
                ready = self.hello(page)
                version = ready['roleState']['pageVersion']
                reply = self.update(page, 'ordinary.body', {'fontStylesheet': css})
                self.assertEqual(reply['type'], 'design:applied', reply)
                frame.wait_for_function("""() => Array.from(document.styleSheets).some(
                    sheet => sheet.ownerNode.hasAttribute('data-fontkit-font'))""")
                applied = self.apply(page, [role(fontSize=24)], pageVersion=version)
                self.assertEqual(applied['type'], 'design:roles-applied', applied)
                self.assertEqual(self.size(frame), '24px')
                cleared = self.clear(page, pageVersion=version)
                self.assertEqual((cleared['type'], cleared['revision']), ('design:roles-applied', 3), cleared)
                reset = self.request(page, {'type': 'design:reset'})
                self.assertEqual(reset['roleState']['pageVersion'], version)
                self.assertEqual(frame.locator('link[data-fontkit-font]').count(), 0)
                self.assertEqual(self.apply(page, [role(fontSize=24)], pageVersion=version)['type'], 'design:roles-applied')
