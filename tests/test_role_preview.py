"""Honest role preview: counts, loss reasons and proven winners, checked against rendered styles."""
import json

from support import ENGINES
from role_support import EVIL
from test_role_stylesheet import BODY, RoleSheetCase, role

TEXT = '<div class="{c}"><p class="{c}-t">Text</p></div>'
SIZE_OF = 'el => getComputedStyle(el).fontSize'


def loss(prop, count, selector, reason):
    return {'property': prop, 'count': count, 'winningSelector': selector, 'reason': reason}


def case(css, losses, px, html=TEXT, extra=(), props=None, prop='fontSize'):
    return {'css': css, 'losses': losses, 'px': px, 'html': html, 'extra': extra, 'props': props or {'fontSize': 24}, 'prop': prop}


# One cascade situation per entry; `{c}` is a per-case class prefix so every case shares one page.
# Each role asks for 24px on `.{c}-t`, and every case loses, so the rendered size is the case's `px`.
CASCADE = {
    'author rule beats the role': case('.{c} p { font-size: 18px; }', [loss('fontSize', 1, '.{c} p', 'author-rule')], 18),
    'the candidate equal to the computed value wins': case(
        'p.{c}-t { font-size: 20px; } .{c} p { font-size: 18px; }', [loss('fontSize', 1, '.{c} p', 'author-rule')], 18),
    'an inactive @media is never named': case(
        '@media (min-width: 100000px) { div p.{c}-t { font-size: 18px; } } @media (min-width: 1px) { .{c} p { font-size: 18px; } }',
        [loss('fontSize', 1, '.{c} p', 'author-rule')], 18),
    'an unsupported @supports is never named': case(
        '@supports (no-such-property: 1) { div p.{c}-t { font-size: 18px; } } @supports (display: block) { .{c} p { font-size: 18px; } }',
        [loss('fontSize', 1, '.{c} p', 'author-rule')], 18),
    'a selector list is reported whole': case(
        '.{c} p, .{c} em { font-size: 18px; }', [loss('fontSize', 1, '.{c} p, .{c} em', 'author-rule')], 18),
    'inherit under a parent with the same value is inherited': case(
        '.{c} { font-size: 18px; } .{c} p { font-size: inherit; }', [loss('fontSize', 1, '.{c} p', 'inherited')], 18),
    'an author inline style is inline': case(
        '', [loss('fontSize', 1, None, 'inline')], 19, '<div class="{c}"><p class="{c}-t" style="font-size: 19px">Text</p></div>'),
    'an inline !important beats a running animation': case(
        '@keyframes {c}k { from { font-size: 20px; } to { font-size: 20px; } } .{c} p { animation: {c}k 100s infinite; }',
        [loss('fontSize', 1, None, 'inline')], 21, '<div class="{c}"><p class="{c}-t" style="font-size: 21px !important">Text</p></div>'),
    'an !important rule inside @layer is complex': case(
        '@layer {c}l { .{c} p { font-size: 18px !important; } }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'a running animation is complex even beside an equal plain rule': case(
        '@keyframes {c}k { from { font-size: 20px; } to { font-size: 20px; } } .{c} p { font-size: 20px; animation: {c}k 100s infinite; }',
        [loss('fontSize', 1, None, 'complex-cascade')], 20),
    'nested rules declaring other properties do not spoil a proof': case(
        '.{c} p { font-size: 18px; & em { color: red; } }', [loss('fontSize', 1, '.{c} p', 'author-rule')], 18),
    'an important author rule beats an inline normal declaration': case(
        '.{c} p { font-size: 18px !important; }', [loss('fontSize', 1, '.{c} p', 'author-rule')], 18,
        '<div class="{c}"><p class="{c}-t" style="font-size: 19px">Text</p></div>'),
    'an inline shorthand holding var hides the longhand': case(
        ':root { --f: 18px serif; } .{c} p { font-size: 18px; }', [loss('fontSize', 1, None, 'complex-cascade')], 18,
        '<div class="{c}"><p class="{c}-t" style="font: var(--f)">Text</p></div>'),
    'a rule with all hides the longhand': case(
        'p.{c}-t { font-size: 16px; } .{c} p { all: unset; }', [loss('fontSize', 1, None, 'complex-cascade')], 16),
    'a winning selector with a C1 control character is never named': case(
        'p.a\\85 { font-size: 18px; }', [loss('fontSize', 1, None, 'complex-cascade')], 18,
        '<div class="{c}"><p class="{c}-t a\u0085">Text</p></div>'),
    'unset inherits like inherit': case(
        '.{c} { font-size: 18px; } .{c} p { font-size: unset; }', [loss('fontSize', 1, '.{c} p', 'inherited')], 18),
    'two inheriting selectors are not a proof': case(
        '.{c} { font-size: 18px; } .{c} p { font-size: inherit; } .{c} > p { font-size: inherit; }',
        [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'inherited line height compares ratios': case(
        '.{c} { font-size: 20px; line-height: 1.5; } .{c} p { font-size: 10px; line-height: inherit; }',
        [loss('lineHeight', 1, '.{c} p', 'inherited')], '15px', props={'lineHeight': 2}, prop='lineHeight'),
    'an open shadow host has an unenumerated :host source': case(
        'p.{c}-t { font-size: 17px; }', [loss('fontSize', 1, None, 'complex-cascade')], 17,
        '<div class="{c}"><p class="{c}-t" data-host>Text</p></div>'),
    'two selectors declaring the computed value are not a proof': case(
        '.{c} p { font-size: 18px; } div > p.{c}-t { font-size: 18px; }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'em is not comparable': case('.{c} p { font-size: 1.125em; }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'rem is not comparable': case('.{c} p { font-size: 1.125rem; }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'percent is not comparable': case('.{c} p { font-size: 112.5%; }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'calc is not comparable': case('.{c} p { font-size: calc(10px + 8px); }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'var is not comparable': case(':root { --s: 18px; } .{c} p { font-size: var(--s); }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'a shorthand holding var leaves the longhand unreadable': case(
        ':root { --f: 18px serif; } .{c} p { font: var(--f); }', [loss('fontSize', 1, None, 'complex-cascade')], 18),
    'another role declaring the property in the owned sheet is not an author rule': case(
        '.{c} p { font-size: 30px; }', [loss('fontSize', 1, None, 'complex-cascade')], 30, extra=[('.{c} > p', {'fontSize': 30})]),
    'a slotted element has another cascade source': case(
        '.{c} p { font-size: 18px; }', [loss('fontSize', 1, None, 'complex-cascade')], 18,
        '<div class="{c}" data-slot><p class="{c}-t">Text</p></div>'),
}


class PreviewCase(RoleSheetCase):
    def author(self, frame, css='', html=''):
        frame.evaluate("""([css, html]) => {
            if (css) { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); }
            if (html) document.querySelector('main').insertAdjacentHTML('beforeend', html);
        }""", [css, html])

    def measure(self, engine, roles, css='', html='', before=None):
        """One fresh page with the author's CSS and markup, then one authenticated apply."""
        page, frame = self.open(engine)
        self.author(frame, css, html)
        if before:
            before(page, frame)
        self.hello(page)
        reply = self.apply(page, roles)
        self.assertEqual(reply['type'], 'design:roles-applied', reply)
        return page, frame, reply

    def rendered_lost(self, frame, selector, prop, expected):
        """Elements whose computed value the test reads itself and which differ from the role's value."""
        return frame.evaluate("""([selector, prop, expected]) => Array.from(document.querySelectorAll(selector))
            .filter(el => getComputedStyle(el)[prop] !== expected).length""", [selector, prop, expected])

    def one(self, engine, css, html, selector='.card-copy', **props):
        page, frame, reply = self.measure(engine, [role('card', [selector], **(props or {'fontSize': 24}))], css, html)
        return frame, reply['outcomes'][0], reply


CARD = '<div class="card"><p class="card-copy">Card text</p></div>'


class CascadeTests(PreviewCase):
    def test_each_cascade_situation_reports_its_reason_and_proven_winner(self):
        """Given one paragraph per cascade situation that each lose a 24px role, when applied
        together, then every loss is counted once with the reason and winner that the rendered
        cascade supports, and a selector is named only when a readable rule proves it."""
        names = list(CASCADE)
        prefix = lambda i: f'c{i}'  # noqa: E731
        sub = lambda text, i: text.replace('{c}', prefix(i))  # noqa: E731
        css = ''.join(sub(CASCADE[name]['css'], i) for i, name in enumerate(names))
        html = ''.join(sub(CASCADE[name]['html'], i) for i, name in enumerate(names))
        roles = []
        for i, name in enumerate(names):
            roles.append(role(prefix(i), [f'.{prefix(i)}-t'], **CASCADE[name]['props']))
            for selector, props in CASCADE[name]['extra']:
                roles.append(role(prefix(i) + 'x', [sub(selector, i)], **props))

        def slot(page, frame):
            frame.evaluate("""() => document.querySelectorAll('[data-slot]').forEach(host => {
                const child = host.firstElementChild; host.attachShadow({ mode: 'open' }).innerHTML = '<slot></slot>';
                host.appendChild(child);
            })""")

        def host(page, frame):
            slot(page, frame)
            frame.evaluate("""() => document.querySelectorAll('[data-host]').forEach(el => {
                el.attachShadow({ mode: 'open' }).innerHTML = '<style>:host { font-size: 17px !important; }</style><slot></slot>';
            })""")

        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, roles, css, html, host)
                outcomes = {o['id']: o for o in reply['outcomes']}
                for i, name in enumerate(names):
                    with self.subTest(case=name):
                        spec, outcome = CASCADE[name], outcomes[prefix(i)]
                        px = spec['px'] if isinstance(spec['px'], str) else f"{spec['px']}px"
                        self.assertEqual(frame.locator(f'.{prefix(i)}-t').evaluate(f"el => getComputedStyle(el).{spec['prop']}"), px)
                        self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched'], outcome['complete']), (1, 1, 1, True))
                        self.assertEqual(outcome['losses'], [dict(entry, winningSelector=sub(entry['winningSelector'], i)
                                                                  if entry['winningSelector'] else None) for entry in spec['losses']])

    def test_an_inspector_important_override_is_inline(self):
        """Given an inspector edit set 27px inline with !important on one paragraph, when a
        24px role is applied, then that paragraph's loss is inline with no selector."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                self.assertEqual(self.update(page, 'ordinary.body', {'fontSize': 27})['type'], 'design:applied')
                outcome = self.apply(page, [role(fontSize=24)])['outcomes'][0]
                self.assertEqual([self.size(frame, BODY, 0), self.size(frame, BODY, 1)], ['24px', '27px'])
                self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched']), (2, 2, 1))
                self.assertEqual(outcome['losses'], [loss('fontSize', 1, None, 'inline')])

    def test_the_selector_cap_names_2000_characters_and_nothing_longer(self):
        """Given winning rules whose selectors are exactly 2,000 and 2,002 characters, when
        applied, then the first is named verbatim and the longer one is unnamed complex-cascade."""
        exact, over = '.x' * 1000, '.x' * 1001
        page_html = '<div class="card"><p class="card-copy x">A</p></div>'
        for engine in ENGINES:
            for label, selector, expected in (('exact', exact, exact), ('over', over, None)):
                with self.subTest(engine=engine, cap=label):
                    frame, outcome, _ = self.one(engine, f'{selector} {{ font-size: 18px; }}', page_html)
                    self.assertEqual(frame.evaluate('document.styleSheets[1].cssRules[0].selectorText.length'), len(selector))
                    self.assertEqual(frame.locator('.card-copy').evaluate(SIZE_OF), '18px')
                    self.assertEqual(outcome['losses'], [loss('fontSize', 1, expected, 'author-rule' if expected else 'complex-cascade')])


class UnreadableAndBlockedTests(PreviewCase):
    def test_page_wide_sources_decide_whether_a_winner_can_be_named(self):
        """Given a readable `.card p` rule beside each page-wide source (a cross-origin sheet, a
        pending link or import, an adopted sheet, a namespaced selector that throws in matches(),
        a layered import, a nested declaration), when two paragraphs lose, then the count is exact
        and nothing is named; and disabled or inactive sheets are never named while `.card p` is."""
        html = '<div class="card"><p class="card-copy">One</p><p class="card-copy">Two</p></div>'
        readable = '.card p { font-size: 18px; }'
        data = 'data:text/css,div%20p%7Bfont-size%3A18px%7D'

        def add(frame, css, disable=False):
            frame.evaluate("""([css, disable]) => { const node = document.createElement('style'); node.textContent = css;
                document.head.appendChild(node); node.sheet.disabled = disable; }""", [css, disable])

        def imported(frame, css):
            add(frame, css)
            frame.wait_for_function("() => Array.from(document.styleSheets).some(sheet => sheet.cssRules[0] instanceof CSSImportRule && sheet.cssRules[0].styleSheet)")

        def hold(page, name):
            held = []
            page.context.route('**/' + name, lambda route: held.append(route))  # never answered: the load stays pending
            self.addCleanup(lambda: [route.abort() for route in held])

        def cross_origin(page, frame):
            frame.evaluate("""href => new Promise((resolve, reject) => {
                const node = document.createElement('link'); node.rel = 'stylesheet'; node.href = href;
                node.onload = resolve; node.onerror = () => reject(new Error('sheet did not load'));
                document.head.appendChild(node);
            })""", EVIL + '/role-preview-evil.css')
            self.assertEqual(frame.evaluate("""() => { try { document.styleSheets[document.styleSheets.length - 1].cssRules; return false; }
                catch (e) { return e.name; } }"""), 'SecurityError')

        def pending_link(page, frame):
            hold(page, 'pending-sheet.css')
            sheet = frame.evaluate("""href => {
                const node = document.createElement('link'); node.rel = 'stylesheet'; node.href = href;
                document.head.appendChild(node); return node.sheet === null ? null : 'has a sheet';
            }""", '/pending-sheet.css')
            self.assertIsNone(sheet, 'a pending link must have no sheet')

        def pending_import(page, frame):
            hold(page, 'pending-import.css')
            add(frame, '@import url("/pending-import.css");')
            self.assertIsNone(frame.evaluate('document.styleSheets[document.styleSheets.length - 1].cssRules[0].styleSheet'))

        def adopted(page, frame):
            frame.evaluate("""() => { const sheet = new CSSStyleSheet(); sheet.replaceSync('.card p { font-size: 18px; }');
                document.adoptedStyleSheets = [sheet]; }""")

        def namespaced(page, frame):
            add(frame, '@namespace x url(http://www.w3.org/1999/xhtml); x|p.card-copy { font-size: 18px; }')
            self.assertTrue(frame.evaluate("() => { try { document.querySelector('x|p'); return false; } catch (e) { return true; } }"))

        def layered_import(page, frame):
            imported(frame, '@import url("data:text/css,.card%20p%7Bfont-size%3A18px%7D") layer;')

        def nested(page, frame):
            add(frame, 'main .card { & p.card-copy { font-size: 18px; } }')

        def disabled(page, frame):
            add(frame, 'div p { font-size: 18px; }', disable=True)

        def inactive_imports(page, frame):
            imported(frame, f'@import url("{data}") print;')
            add(frame, f'@import url("{data}") supports(not (display: flex));')

        none = (None, 'complex-cascade')
        rows = [('cross-origin sheet', readable, cross_origin, (None, 'unreadable-sheet')),
                ('pending link', readable, pending_link, (None, 'unreadable-sheet')),
                ('pending import', readable, pending_import, (None, 'unreadable-sheet')),
                ('adopted sheet', readable, adopted, none), ('matches() throws', readable, namespaced, none),
                ('layered import', readable, layered_import, none),
                ('nested declaration', 'div p { font-size: 18px; }', nested, none),
                ('disabled sheet', readable, disabled, ('.card p', 'author-rule')),
                ('inactive imports', readable, inactive_imports, ('.card p', 'author-rule'))]
        for engine in ENGINES:
            for label, css, before, (selector, reason) in rows:
                with self.subTest(engine=engine, source=label):
                    page, frame, reply = self.measure(engine, [role('card', ['.card-copy'], fontSize=24)], css, html, before)
                    self.assertEqual(self.rendered_lost(frame, '.card-copy', 'fontSize', '24px'), 2)
                    outcome = reply['outcomes'][0]
                    self.assertEqual((outcome['checked'], outcome['mismatched']), (2, 2))
                    self.assertEqual(outcome['losses'], [loss('fontSize', 2, selector, reason)])

    def test_an_owned_sheet_that_the_page_disables_restricts_or_moves_is_stylesheet_blocked(self):
        """Given the page disables the owned sheet, gives it a print-only media attribute or moves
        it into a shadow root right after commit, when measured, then both paragraphs render 16px
        and each loss is stylesheet-blocked with an exact count."""
        for engine in ENGINES:
            for action in ('node.sheet.disabled = true', "node.setAttribute('media', 'print')",
                           'window.shadowHost.shadowRoot.appendChild(node)'):
                with self.subTest(engine=engine, action=action):
                    def watch(page, frame, action=action):
                        frame.evaluate("""action => {
                            window.shadowHost = document.createElement('div'); document.body.appendChild(window.shadowHost);
                            window.shadowHost.attachShadow({ mode: 'open' });
                            new MutationObserver(() => {
                                for (const node of document.querySelectorAll('style[data-fontkit-role-styles]')) new Function('node', action)(node);
                            }).observe(document.head, { childList: true });
                        }""", action)

                    page, frame, reply = self.measure(engine, [role(fontSize=24)], before=watch)
                    self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                    self.assertEqual(self.rendered_lost(frame, BODY, 'fontSize', '24px'), 2)
                    self.assertEqual(reply['outcomes'][0]['losses'], [loss('fontSize', 2, None, 'stylesheet-blocked')])

    def test_attribution_stops_at_its_deadline_and_the_losses_are_budget_exceeded(self):
        """Given a page whose clock jumps 1.2 s when attribution starts, or while its rules are being
        collected from a 70-rule sheet, when two paragraphs lose to a readable rule, then the counts
        stay exact, each loss is budget-exceeded and the outcome is incomplete."""
        hooks = {
            'before collection': ("""() => {
                const real = document.getAnimations.bind(document), now = performance.now.bind(performance);
                document.getAnimations = () => { performance.now = () => now() + 1200; return real(); };
            }""", ''),
            'during collection': ("""() => {
                const real = window.matchMedia.bind(window), now = performance.now.bind(performance);
                window.matchMedia = text => { if (text.includes('min-width: 0px')) performance.now = () => now() + 1200; return real(text); };
                const node = document.createElement('style'); node.media = 'all and (min-width: 0px)';
                node.textContent = Array.from({ length: 70 }, (_, i) => `.filler${i} { color: red; }`).join('') + '.card p { font-size: 18px; }';
                document.head.appendChild(node);
            }""", ''),
        }
        for engine in ENGINES:
            for label, (hook, css) in hooks.items():
                with self.subTest(engine=engine, skew=label):
                    page, frame, reply = self.measure(
                        engine, [role(fontSize=24)], css or '.card p { font-size: 18px; }',
                        '<div class="card"><p class="body-copy">One</p><p class="body-copy">Two</p></div>',
                        lambda page, frame, hook=hook: frame.evaluate(hook))
                    self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (False, 'budget-exceeded'))
                    outcome = reply['outcomes'][0]
                    self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched'], outcome['complete']), (4, 4, 2, False))
                    self.assertEqual(outcome['losses'], [loss('fontSize', 2, None, 'budget-exceeded')])
                    self.assertEqual(self.rendered_lost(frame, '.card .body-copy', 'fontSize', '24px'), 2)

    def test_a_csp_blocked_install_is_a_rejection_never_an_applied_success(self):
        """Given a policy refusing inline styles, when a role is applied, then the reply is a
        stylesheet-blocked rejection with no outcomes and the page renders 16px."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, headers={'content-security-policy': "style-src 'self'"})
                self.hello(page)
                reply = self.apply(page, [role(fontSize=24)])
                self.assertEqual((reply['type'], reply['reason']), ('design:rejected', 'stylesheet-blocked'), reply)
                self.assertNotIn('outcomes', reply)
                self.assertEqual(self.size(frame), '16px')


class CountTests(PreviewCase):
    def test_zero_matches_report_zero_and_complete(self):
        """Given a selector that matches nothing, when applied, then matched, checked and
        mismatched are all zero, the check is complete and nothing is lost."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, [role('none', ['.no-such-class'], fontSize=24)])
                self.assertEqual(reply['outcomes'], [{'id': 'none', 'matched': 0, 'checked': 0, 'mismatched': 0,
                                                      'complete': True, 'losses': []}])

    def test_matched_elements_without_rendered_text_are_not_checked_and_stay_complete(self):
        """Given two rendered paragraphs plus an empty one and a hidden one matching the role,
        when applied, then matched is 4, checked is 2, the check is still complete and the
        unchecked elements are not losses."""
        html = '<p class="body-copy"></p><p class="body-copy" hidden>Hidden</p>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, [role(fontSize=24)], html=html)
                self.assertEqual(frame.locator(BODY).count(), 4)
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                self.assertEqual(reply['outcomes'], [{'id': 'body', 'matched': 4, 'checked': 2, 'mismatched': 0,
                                                      'complete': True, 'losses': []}])
                self.assertEqual(self.rendered_lost(frame, f'{BODY}:not([hidden])', 'fontSize', '24px'), 0)

    def test_overlapping_selectors_and_roles_count_each_element_once_per_role(self):
        """Given two roles whose selector lists overlap three ways on the same two paragraphs,
        when one role loses fontWeight to an author rule, then each role matches exactly 2
        elements and the loss count is 2, not multiplied by the overlapping selectors."""
        css = 'main > p.body-copy { font-weight: 300 !important; }'
        roles = [role('a', [BODY, 'main > p', 'p.body-copy'], fontSize=24),
                 role('b', ['p.body-copy', BODY, 'main > p.body-copy'], fontSize=24, fontWeight=700)]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, roles, css)
                first, second = reply['outcomes']
                self.assertEqual((first['matched'], first['checked'], first['mismatched'], first['losses']), (2, 2, 0, []))
                self.assertEqual((second['matched'], second['checked'], second['mismatched']), (2, 2, 2))
                self.assertEqual(second['losses'], [loss('fontWeight', 2, 'main > p.body-copy', 'author-rule')])
                self.assertEqual(self.rendered_lost(frame, BODY, 'fontWeight', '700'), 2)

    def test_losses_group_by_property_reason_and_selector_in_contract_order(self):
        """Given five paragraphs losing through two rules and two inline styles across fontSize
        and fontWeight, when applied, then counts are grouped per property, reason and selector,
        ordered by property, then reason, then selector, and they match the rendered styles."""
        css = '.a p.t { font-size: 18px; font-weight: 400; } .b p.t { font-size: 19px; }'
        html = ('<div class="b"><p class="t">3</p></div><div class="a"><p class="t">1</p></div><div class="a"><p class="t">2</p></div>'
                '<p class="t" style="font-weight: 300">5</p><p class="t" style="font-size: 17px">4</p>')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, [role('t', ['.t'], fontSize=24, fontWeight=700)], css, html)
                outcome = reply['outcomes'][0]
                self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched']), (5, 5, 5))
                self.assertEqual(outcome['losses'], [
                    loss('fontSize', 2, '.a p.t', 'author-rule'), loss('fontSize', 1, '.b p.t', 'author-rule'),
                    loss('fontSize', 1, None, 'inline'),
                    loss('fontWeight', 2, '.a p.t', 'author-rule'), loss('fontWeight', 1, None, 'inline')])
                totals = {}
                for entry in outcome['losses']:
                    totals[entry['property']] = totals.get(entry['property'], 0) + entry['count']
                self.assertEqual(totals, {'fontSize': self.rendered_lost(frame, '.t', 'fontSize', '24px'),
                                          'fontWeight': self.rendered_lost(frame, '.t', 'fontWeight', '700')})

    def test_loss_groups_are_capped_at_16_per_property_and_the_counts_still_sum(self):
        """Given 40 paragraphs losing through 30 distinct 1,800-character selectors, when
        applied, then the receipt keeps 16 groups for the property, the 5 triple-winner
        selectors stay named, the remainder merges into one unnamed group, the counts sum to 40
        and the receipt stays under 1 MiB."""
        css, html = '', ''
        for i in range(30):
            tail = '.x' * 900
            css += f'.u{i:02d}{tail} {{ font-size: 18px; }}'
            html += ''.join(f'<p class="t x u{i:02d}">n</p>' for _ in range(3 if i >= 25 else 1))
        html = '<div class="card">' + html + '</div>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, [role('t', ['.t'], fontSize=24)], css, html)
                outcome = reply['outcomes'][0]
                losses = outcome['losses']
                self.assertEqual(self.rendered_lost(frame, '.t', 'fontSize', '24px'), 40)
                self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched']), (40, 40, 40))
                self.assertEqual(len(losses), 16)
                self.assertEqual(sum(entry['count'] for entry in losses), 40)
                # The five triple winners sort last by name, so keeping them proves the largest counts are kept first.
                self.assertEqual(sorted(entry['count'] for entry in losses if entry['reason'] == 'author-rule')[-5:], [3] * 5)
                self.assertEqual(losses[-1], loss('fontSize', 15, None, 'complex-cascade'))
                self.assertLess(len(json.dumps(reply).encode('utf-8')), 1024 * 1024)

    def test_named_selectors_are_bounded_across_the_whole_receipt(self):
        """Given 8 roles whose 16 paragraphs each lose all six properties to their own 1,996-character
        rule, when applied, then the named selector text across the receipt stays within 262,144
        characters, the remainder merges into unnamed groups, every property's counts still sum to
        16 per role and the serialized receipt stays under 1 MiB."""
        tail = '.x' * 995
        css, html, roles = '', '', []
        for r in range(8):
            for e in range(16):
                css += (f'.u{r}_{e:02d}{tail} {{ font-size: 18px; font-weight: 300; line-height: 2; letter-spacing: 1px;'
                        f' text-transform: lowercase; font-family: monospace; }}')
                html += f'<p class="r{r} x u{r}_{e:02d}">n</p>'
            roles.append(role(f'r{r}', [f'.r{r}'], fontSize=24, fontWeight=700, lineHeight=1.2, letterSpacing=0.05,
                              textTransform='uppercase', fontFamily='Georgia'))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, roles, css, '<div class="card">' + html + '</div>')
                named = 0
                for outcome in reply['outcomes']:
                    self.assertEqual((outcome['checked'], outcome['mismatched']), (16, 16))
                    for prop in ('fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform', 'fontFamily'):
                        entries = [entry for entry in outcome['losses'] if entry['property'] == prop]
                        self.assertLessEqual(len(entries), 16)
                        self.assertEqual(sum(entry['count'] for entry in entries), 16, (outcome['id'], prop))
                    named += sum(len(entry['winningSelector'] or '') for entry in outcome['losses'])
                self.assertEqual(self.rendered_lost(frame, '.x', 'fontSize', '24px'), 128)
                self.assertGreater(named, 200000)
                self.assertLessEqual(named, 262144)
                self.assertLess(len(json.dumps(reply).encode('utf-8')), 1024 * 1024)

    def test_a_receipt_with_thousands_of_entries_is_collapsed_to_fit_one_mebibyte(self):
        """Given 128 roles whose 16 paragraphs each lose all six properties to 16 short shared
        rules (12,288 loss entries), when applied, then the serialized receipt is at most 1 MiB,
        every role and property still sums to 16 lost elements, and the collapse started from the
        last role, so the first role keeps its names."""
        props = dict(fontSize=24, fontWeight=700, lineHeight=1.2, letterSpacing=0.05, textTransform='uppercase', fontFamily='Georgia')
        css = ''.join(f'p.e{k} {{ font-size: 18px; font-weight: 300; line-height: 2; letter-spacing: 1px;'
                      f' text-transform: lowercase; font-family: monospace; }}' for k in range(16))
        html = ''.join(f'<p class="r{r} e{k}">n</p>' for r in range(128) for k in range(16))
        roles = [role(f'r{r}', [f'.r{r}'], **props) for r in range(128)]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, roles, css, '<div class="card">' + html + '</div>')
                self.assertLessEqual(len(json.dumps(reply, separators=(',', ':'), ensure_ascii=False).encode('utf-8')), 1024 * 1024)
                for outcome in reply['outcomes']:
                    self.assertEqual((outcome['checked'], outcome['mismatched']), (16, 16))
                    for prop in props:
                        self.assertEqual(sum(entry['count'] for entry in outcome['losses'] if entry['property'] == prop), 16, (outcome['id'], prop))
                self.assertEqual(self.rendered_lost(frame, '.card p', 'fontSize', '24px'), 2048)
                self.assertGreater(len([entry for entry in reply['outcomes'][0]['losses'] if entry['winningSelector']]), 0)
                self.assertEqual([entry['winningSelector'] for entry in reply['outcomes'][-1]['losses']], [None] * len(reply['outcomes'][-1]['losses']))

    def test_the_receipt_fit_counts_utf8_bytes_and_leaves_room_for_the_posted_envelope(self):
        """Given 128 roles with 199-200-character CJK names whose receipt is under 1 MiB in string
        length but within a few bytes of 1 MiB in UTF-8, so that the fields added when posting
        would push it over, when applied, then the posted receipt is at most 1 MiB in bytes and
        every role and property still sums to 14 lost elements."""
        props = dict(fontSize=24, fontWeight=700, lineHeight=1.2, letterSpacing=0.05, textTransform='uppercase', fontFamily='Georgia')
        css = ''.join(f'p.e{k} {{ font-size: 18px; font-weight: 300; line-height: 2; letter-spacing: 1px;'
                      f' text-transform: lowercase; font-family: monospace; }}' for k in range(14))
        html = ''.join(f'<p class="r{r} e{k}">n</p>' for r in range(128) for k in range(14))
        roles = []
        for r in range(128):
            rid = f'r{r}' + '\u6f22' * (3 + (1 if r < 64 else 0))
            roles.append(dict(role(rid, [f'.r{r}'], **props), name='\u6f22' * (199 + (1 if r < 8 else 0))))

        def measure_fit(page, frame):
            frame.evaluate("""() => {
                const bridge = window.__fontkitBridge, fit = bridge.fitRoleReceipt.bind(bridge);
                bridge.fitRoleReceipt = message => {
                    const json = JSON.stringify(message);
                    window.beforeFit = { chars: json.length, bytes: new TextEncoder().encode(json).length };
                    return fit(message);
                };
            }""")

        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, reply = self.measure(engine, roles, css, '<div class="card">' + html + '</div>', measure_fit)
                before = frame.evaluate('window.beforeFit')
                # Premise: string length is under the limit, the UTF-8 length is over it once the posted fields are added.
                self.assertLess(before['chars'], 1024 * 1024 - 1024, before)
                self.assertGreater(before['bytes'] + 37, 1024 * 1024, before)
                self.assertLessEqual(before['bytes'], 1024 * 1024, before)
                self.assertLessEqual(len(json.dumps(reply, separators=(',', ':'), ensure_ascii=False).encode('utf-8')), 1024 * 1024)
                for outcome in reply['outcomes']:
                    for prop in props:
                        self.assertEqual(sum(entry['count'] for entry in outcome['losses'] if entry['property'] == prop), 14, (outcome['id'], prop))

    def test_a_page_beyond_the_element_budget_keeps_the_full_matched_count(self):
        """Given 10,001 matching text parents, when applied, then matched is 10,001, checked is
        10,000 and the receipt is incomplete rather than counting the unchecked one as a loss."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.bulk(frame, 10001)
                self.hello(page)
                reply = self.apply(page, [role('bulk', ['.bulk'], fontSize=24)], timeout=20000)
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (False, 'budget-exceeded'))
                self.assertEqual(reply['outcomes'], [{'id': 'bulk', 'matched': 10001, 'checked': 10000, 'mismatched': 0,
                                                      'complete': False, 'losses': []}])
                self.assertEqual(self.rendered_lost(frame, '.bulk', 'fontSize', '24px'), 0)

    def test_ten_thousand_attributed_losses_finish_inside_the_budget_with_exact_counts(self):
        """Given 10,000 paragraphs that all lose to one author rule, when applied, then the
        measurement completes within its budget and names the rule with the exact count."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.author(frame, 'main .bulk { font-size: 18px; }')
                self.bulk(frame, 10000)
                self.hello(page)
                reply = self.apply(page, [role('bulk', ['.bulk'], fontSize=24)], timeout=20000)
                self.assertEqual((reply['outcomesComplete'], reply['outcomeReason']), (True, None))
                self.assertEqual(reply['outcomes'], [{'id': 'bulk', 'matched': 10000, 'checked': 10000, 'mismatched': 10000, 'complete': True,
                                                      'losses': [loss('fontSize', 10000, 'main .bulk', 'author-rule')]}])
                self.assertEqual(self.rendered_lost(frame, '.bulk', 'fontSize', '24px'), 10000)

    def bulk(self, frame, count):
        frame.evaluate("""count => {
            const host = document.createElement('div'), fragment = document.createDocumentFragment();
            for (let i = 0; i < count; i += 1) {
                const item = document.createElement('div'); item.className = 'bulk'; item.textContent = 'n' + i;
                fragment.appendChild(item);
            }
            host.appendChild(fragment); document.querySelector('main').appendChild(host);
        }""", count)
