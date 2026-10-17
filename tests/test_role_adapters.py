"""Framework adapters through the real bridge: Bootstrap 5 suggestions, names, evidence, bytes and the Apply re-check."""
import json

import role_contract as table
from support import ENGINES
from role_support import REPO, ROLE_PAGE, TARGET
from test_role_stylesheet import RoleSheetCase, role

BS5 = TARGET + '/fixtures/bootstrap5-static/index.html'
BS4 = TARGET + '/fixtures/bootstrap4-static/index.html'
BODY_VARIABLES = ('--bs-body-font-family', '--bs-font-sans-serif')
VARIABLES = BODY_VARIABLES + ('--bs-font-monospace',)
BODY_IDS = ('bs.hero.cta', 'bs5.button', 'bs5.navigation', 'bs5.label')
BODY_SELECTORS = [f'[data-design-id="{name}"]' for name in BODY_IDS]
ROOT_VARIABLES = """(names) => { const style = getComputedStyle(document.documentElement);
  return Object.fromEntries(names.map(name => [name, style.getPropertyValue(name).trim()])); }"""
FONT = 'el => { const s = getComputedStyle(el); return [s.fontFamily, s.fontSize]; }'
STRIP_IDS = "() => document.querySelectorAll('[data-design-id]').forEach(el => el.removeAttribute('data-design-id'))"
ADD_STYLE = "(css) => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); }"
LINK_BOOTSTRAP5 = """(href) => new Promise((resolve, reject) => {
  const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = href;
  link.onload = resolve; link.onerror = reject; document.head.appendChild(link); })"""
BOOTSTRAP5_CSS = TARGET + '/fixtures/bootstrap5-static/vendor/bootstrap.min.css'
ADD_HTML = "(html) => document.querySelector('main, .type-corpus').insertAdjacentHTML('beforeend', html)"
SET_ROOT_STYLE = "(text) => document.documentElement.setAttribute('style', text)"
BOTH_VARIABLES = ':root { --bs-body-font-family: serif; --bs-font-sans-serif: sans-serif; }'
# (fontSize, fontWeight) -> suggested name for the 16 style groups of fixtures/bootstrap5-static/expected-styles.json.
FIXTURE_GROUPS = {
    (40, 500): 'Heading 1', (32, 500): 'Heading 2', (28, 500): 'Heading 3', (24, 500): 'Heading 4', (20, 500): 'Heading 5',
    (16, 500): 'Heading 6', (80, 300): 'Display 1', (72, 300): 'Display 2', (64, 300): 'Display 3', (56, 300): 'Display 4',
    (48, 300): 'Display 5', (40, 300): 'Display 6', (20, 300): 'Lead', (14, 400): 'Small', (16, 400): 'Body', (20, 400): 'Brand'}
# Which variables a TEMPLATE_CASES entry must change on the Bootstrap 5 page, and to what.
CASE_VARIABLES = {
    'body': {'--bs-body-font-family': 'Inter', '--bs-font-sans-serif': 'Inter'},
    'mono': {'--bs-font-monospace': '"JetBrains Mono"'},
    'body-without-family': {}, 'heading': {},
    'mixed': {'--bs-body-font-family': 'Inter', '--bs-font-sans-serif': 'Inter', '--bs-font-monospace': '"JetBrains Mono"'}}
DETECTED_CSS = (':root {\n  --bs-body-font-family: Inter;\n  --bs-font-sans-serif: Inter;\n}\n'
                + ', '.join(BODY_SELECTORS) + ' {\n  font-family: Inter;\n  font-size: 18px;\n}\n')


def adapted(rid, adapter, selectors, **properties):
    return {**role(rid, selectors, **properties), 'adapter': adapter}


def case_roles(name):
    return json.loads(json.dumps(next(case for case in table.TEMPLATE_CASES if case['name'] == name)['roles']))


class AdapterCase(RoleSheetCase):
    def start(self, engine, target=BS5, prepare=(), **options):
        """A fresh page with the author's changes made before hello (a later change would advance the page version)."""
        page, frame = self.open(engine, target=target, **options)
        for script, arg in prepare:
            frame.evaluate(script, arg)
        self.hello(page)
        return page, frame

    def groups(self, page):
        reply = self.detect(page)
        self.assertTrue(reply['complete'], reply)
        return reply['groups']

    def sample(self, groups, text):
        found = [group for group in groups if group['sampleText'] == text]
        self.assertEqual(len(found), 1, [g['sampleText'] for g in groups])
        return found[0]

    def variables(self, frame, names=VARIABLES):
        return frame.evaluate(ROOT_VARIABLES, list(names))

    def font(self, frame, design_id):
        return frame.locator(f'[data-design-id="{design_id}"]').evaluate(FONT)

    def received(self, group, **properties):
        """The role Studio would send for a detected group, as received."""
        return {'id': 'detected', 'name': group['suggestedName'], 'selectors': [b['value'] for b in group['selectors']],
                'adapter': group['adapter'], 'properties': properties}

    def rejected_adapter(self, reply):
        self.assertEqual((reply['type'], reply.get('reason'), reply.get('detail')),
                         ('design:rejected', 'unsupported-value', 'Unsupported adapter'), reply)


class SuggestionTests(AdapterCase):
    def test_the_bootstrap5_fixture_gets_the_body_suggestion_and_class_names_and_keeps_author_ids_first(self):
        """Given the Bootstrap 5 fixture, whose elements carry author ids, when Studio detects, then the 16 style groups carry the
        names of the oracle's sizes and weights, only the body-style group is bootstrap5-body (bound to the four body ids, in order)
        and the two author-role groups keep their role names, while every other group stays plain because author ids bind first."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                groups = self.groups(page)
                styled = {(g['identity']['style']['fontSize'], g['identity']['style']['fontWeight']): g
                          for g in groups if g['identity']['kind'] == 'style'}
                self.assertEqual({key: g['suggestedName'] for key, g in styled.items()}, FIXTURE_GROUPS)
                self.assertEqual({key: g['adapter'] for key, g in styled.items() if g['adapter'] != 'plain'},
                                 {(16, 400): 'bootstrap5-body'})
                self.assertEqual([b['value'] for b in styled[(16, 400)]['selectors']], BODY_SELECTORS)
                roles = {g['authorRole']: (g['suggestedName'], g['adapter']) for g in groups if g['authorRole']}
                self.assertEqual(roles, {'Editorial': ('Editorial', 'plain'), 'editorial': ('editorial', 'plain')})

    def test_one_element_per_remaining_class_is_named_by_its_class(self):
        """Given one element each of btn, nav-link, card-title (on a div) and form-label with its own inline size, when Studio
        detects, then each forms its own group named Button, Navigation link, Card title and Form label, all plain."""
        html = ''.join(f'<{tag} class="{cls}" style="font-size: {size}px">{cls}</{tag}>' for tag, cls, size in
                       (('button', 'btn', 41), ('a', 'nav-link', 43), ('div', 'card-title', 45), ('label', 'form-label', 47)))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(ADD_HTML, html)])
                groups = self.groups(page)
                self.assertEqual({g['sampleText']: (g['suggestedName'], g['adapter']) for g in groups
                                  if g['sampleText'] in ('btn', 'nav-link', 'card-title', 'form-label')},
                                 {'btn': ('Button', 'plain'), 'nav-link': ('Navigation link', 'plain'),
                                  'card-title': ('Card title', 'plain'), 'form-label': ('Form label', 'plain')})

    def test_without_author_ids_headings_bind_their_tag_and_class_and_are_heading_suggestions(self):
        """Given the Bootstrap 5 fixture without author ids, when Studio detects, then every heading group binds hN and .hN, every
        display group binds .display-N, all as stable class bindings and bootstrap5-heading, and the body-style group is
        bootstrap5-body."""
        expected = {f'Heading {n}': [f'h{n}', f'.h{n}'] for n in range(1, 7)}
        expected.update({f'Display {n}': [f'.display-{n}'] for n in range(1, 7)})
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(STRIP_IDS, None)])
                groups = self.groups(page)
                found = {g['suggestedName']: g for g in groups if g['suggestedName'] in expected}
                self.assertEqual(sorted(found), sorted(expected))
                for name, group in found.items():
                    self.assertEqual(([b['value'] for b in group['selectors']], {b['reason'] for b in group['selectors']},
                                      {b['stable'] for b in group['selectors']}, group['adapter']),
                                     (expected[name], {'class'}, {True}, 'bootstrap5-heading'), name)
                body = [g for g in groups if g['adapter'] == 'bootstrap5-body']
                self.assertEqual([(g['suggestedName'], g['elementCount']) for g in body], [('Body', 4)])

    def test_a_heading_tag_that_matches_a_non_member_binds_by_class_and_stays_plain(self):
        """Given the id-less page plus an h2 with class fs-6, when Studio detects, then the Heading 2 group binds only .h2 (a
        stable class binding) as a plain group named Heading 2, the mixed-level h6 and h2.fs-6 group is named Text and binds by
        dom path as a plain group, and applying the detected Heading 2 group as received renders 36px on .h2 and leaves the fs-6
        heading at 16px (the binding assertion, not that render check, proves the exclusion: .fs-6 is !important)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(STRIP_IDS, None), (ADD_HTML, '<h2 class="fs-6">Small h2</h2>')])
                groups = self.groups(page)
                two = next(g for g in groups if g['suggestedName'] == 'Heading 2')
                self.assertEqual(([(b['value'], b['reason'], b['stable']) for b in two['selectors']], two['adapter']),
                                 ([('.h2', 'class', True)], 'plain'))
                mixed = next(g for g in groups if g['sampleText'] == 'Heading 6')
                self.assertEqual((mixed['elementCount'], mixed['suggestedName'], mixed['adapter'], {b['reason'] for b in mixed['selectors']}),
                                 (2, 'Text', 'plain', {'dom-path'}))
                reply = self.apply(page, [self.received(two, fontSize=36)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual(frame.locator('.h2').evaluate(FONT)[1], '36px')
                self.assertEqual(frame.locator('h2.fs-6').evaluate(FONT)[1], '16px')

    def test_a_heading_role_renders_its_size_on_its_own_level_only(self):
        """Given the id-less page, when the detected Heading 2 and then Heading 3 roles are applied as received, then each
        receipt echoes the role, its own level renders the new size and the next level keeps its size."""
        for engine in ENGINES:
            for level, size, other in ((2, 36, 3), (3, 30, 2)):
                with self.subTest(engine=engine, level=level):
                    page, frame = self.start(engine, prepare=[(STRIP_IDS, None)])
                    group = next(g for g in self.groups(page) if g['suggestedName'] == f'Heading {level}')
                    request = [self.received(group, fontSize=size)]
                    reply = self.apply(page, request)
                    self.assertEqual(reply['type'], 'design:roles-applied', reply)
                    self.assertEqual(reply['roles'], request)
                    self.assertEqual(frame.locator(f'h{level}').evaluate(FONT)[1], f'{size}px')
                    self.assertEqual(frame.locator(f'h{other}').evaluate(FONT)[1], {2: '32px', 3: '28px'}[other])

    def test_two_code_elements_form_one_monospace_group_and_the_mono_template_renders(self):
        """Given two code elements, when Studio detects, then one group of 2 named Monospace is bootstrap5-mono by family name,
        it is the only mono group and the (16, 400) Get started group the only body group, every other group stays plain, and
        applying the mono template sets --bs-font-monospace to "JetBrains Mono" with the quotes and both elements render it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(ADD_HTML, '<p><code>one</code> <code>two</code></p>')])
                group = next(g for g in self.groups(page) if g['suggestedName'] == 'Monospace')
                self.assertEqual((group['elementCount'], group['adapter']), (2, 'bootstrap5-mono'))
                self.assertEqual({g['sampleText']: g['adapter'] for g in self.groups(page) if g['adapter'] != 'plain'},
                                 {'one': 'bootstrap5-mono', 'Get started': 'bootstrap5-body'})
                reply = self.apply(page, case_roles('mono'))
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual(self.variables(frame)['--bs-font-monospace'], '"JetBrains Mono"')
                self.assertEqual(frame.locator('code').evaluate_all('els => els.map(el => getComputedStyle(el).fontFamily)'),
                                 ['"JetBrains Mono"'] * 2)

    def test_bootstrap4_groups_are_plain_and_a_plain_role_renders_without_variables(self):
        """Given the Bootstrap 4 fixture, when Studio detects, then every group is plain, and a plain role with a family and a
        size on the body-style group renders on its three elements without a :root block or any --bs- variable, echoes its
        plain adapter, and clear restores the page byte for byte."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, BS4)
                before = self.snapshot(frame)
                groups = self.groups(page)
                self.assertEqual({g['adapter'] for g in groups}, {'plain'})
                body = next(g for g in groups if g['elementCount'] == 3 and g['authorRole'] is None
                            and any('bs4.button' in b['value'] for b in g['selectors']))
                request = [self.received(body, fontFamily='Inter', fontSize=18)]
                reply = self.apply(page, request)
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual((reply['roles'], ':root' in reply['canonicalCss']), (request, False))
                self.assertEqual([self.font(frame, f'bs4.{n}') for n in ('button', 'navigation', 'label')], [['Inter', '18px']] * 3)
                self.assertEqual(self.variables(frame), dict.fromkeys(VARIABLES, ''))
                self.assertEqual(self.clear(page)['type'], 'design:roles-applied')
                self.assertEqual(self.snapshot(frame), before)

    def test_bootstrap5_adapters_are_rejected_on_bootstrap4_and_write_nothing(self):
        """Given the Bootstrap 4 fixture, when each bootstrap5 adapter is applied, then each is rejected as unsupported with the
        adapter detail and nothing is written: no owned node, the same revision, no --bs- variable and an unchanged snapshot."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, BS4)
                before = self.snapshot(frame)
                for adapter, selectors in (('bootstrap5-body', ['.btn']), ('bootstrap5-mono', ['code']), ('bootstrap5-heading', ['h2'])):
                    reply = self.apply(page, [adapted('bad', adapter, selectors, fontFamily='Inter', fontSize=18)])
                    self.rejected_adapter(reply)
                    self.assertEqual((self.owned(frame), page.evaluate('revision')), ([], 0))
                    self.assertEqual(self.variables(frame), dict.fromkeys(VARIABLES, ''))
                self.assertEqual(self.snapshot(frame), before)

    def test_evidence_needs_both_variables(self):
        """Given the protocol page with a text parent that inherits the body style and a :root rule that defines only one of the
        two body variables, when Studio detects, then every group is plain and the inheriting group keeps the name Text."""
        for engine in ENGINES:
            for css in (':root { --bs-body-font-family: serif; }', ':root { --bs-font-sans-serif: sans-serif; }'):
                with self.subTest(engine=engine, css=css):
                    page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, css), (ADD_HTML, '<p>Inherits</p>')])
                    groups = self.groups(page)
                    self.assertEqual({g['adapter'] for g in groups}, {'plain'})
                    self.assertEqual(self.sample(groups, 'Inherits')['suggestedName'], 'Text')

    def test_a_page_that_defines_both_variables_gets_the_body_suggestion_without_bootstrap(self):
        """Given the protocol page with no Bootstrap but both body variables on :root and a text parent that inherits the body
        style, when Studio detects, then that group is bootstrap5-body named Body (the cost the evidence rule accepts)."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, BOTH_VARIABLES), (ADD_HTML, '<p>Inherits</p>')])
                group = self.sample(self.groups(page), 'Inherits')
                self.assertEqual((group['adapter'], group['suggestedName']), ('bootstrap5-body', 'Body'))

    def test_ties_and_precedence_between_the_body_mono_and_heading_suggestions(self):
        """Given the protocol page with both variables, when Studio detects four arrangements, then two groups equal to the body
        style, and two groups of the monospace family, each get no suggestion; a lone h2 equal to the body style is
        bootstrap5-heading and nothing is body; and a lone group equal to both is bootstrap5-mono and nothing is body."""
        mono = ':root { --bs-font-monospace: monospace; }'
        small = 'style="font-family: monospace; font-size: %dpx"'
        scenarios = (
            ('two groups equal to the body style', '', '<p data-design-role="Intro">Role</p><p>Auto</p>',
             {'Role': 'plain', 'Auto': 'plain'}),
            ('two monospace groups', mono, f'<code {small % 14}>Code</code><samp {small % 16}>Samp</samp>',
             {'Code': 'plain', 'Samp': 'plain'}),
            ('a heading equal to the body style', '', '<h2 style="font-size: 1em; font-weight: 400">Head</h2>',
             {'Head': 'bootstrap5-heading'}),
            ('one group equal to the body and the monospace family', mono + ' body { font-family: monospace; }', '<p>Both</p>',
             {'Both': 'bootstrap5-mono'}))
        for engine in ENGINES:
            for label, css, html, expected in scenarios:
                with self.subTest(engine=engine, scenario=label):
                    page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, BOTH_VARIABLES + css), (ADD_HTML, html)])
                    groups = self.groups(page)
                    self.assertEqual({text: self.sample(groups, text)['adapter'] for text in expected}, expected)
                    self.assertNotIn('bootstrap5-body', {g['adapter'] for g in groups})

    def test_without_heading_evidence_each_heading_group_binds_what_its_markup_allows(self):
        """Given the Bootstrap 4 fixture without author ids, when Studio detects, then the Heading 1 to 4 and 6 groups bind their
        one shared class .hN and the Display 1 to 4 groups bind .display-N, all as stable plain class bindings, while the Heading 5
        group (h5.h5 and h5.card-title share no class) binds two unstable dom paths, and none binds an hN tag."""
        expected = {f'Heading {n}': [(f'.h{n}', 'class', True)] for n in (1, 2, 3, 4, 6)}
        expected.update({f'Display {n}': [(f'.display-{n}', 'class', True)] for n in range(1, 5)})
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, BS4, prepare=[(STRIP_IDS, None)])
                groups = self.groups(page)
                for text, selectors in expected.items():
                    group = self.sample(groups, text)
                    self.assertEqual(([(b['value'], b['reason'], b['stable']) for b in group['selectors']], group['adapter']),
                                     (selectors, 'plain'), text)
                five = self.sample(groups, 'Heading 5')
                self.assertEqual((len(five['selectors']), {(b['reason'], b['stable']) for b in five['selectors']}, five['adapter']),
                                 (2, {('dom-path', False)}, 'plain'))

    def test_variables_defined_on_body_only_are_no_evidence(self):
        """Given the protocol page whose two body variables are defined on body and not on :root, a paragraph that inherits the
        body style and a btn button, when Studio detects, then both groups are plain and named Text, and a bootstrap5-body role
        is rejected as an unsupported adapter with no owned node."""
        css = 'body { --bs-body-font-family: serif; --bs-font-sans-serif: sans-serif; }'
        html = '<p>Inherits</p><button class="btn" style="font-size: 41px">Pressed</button>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, css), (ADD_HTML, html)])
                groups = self.groups(page)
                self.assertEqual({text: (self.sample(groups, text)['suggestedName'], self.sample(groups, text)['adapter'])
                                  for text in ('Inherits', 'Pressed')}, {'Inherits': ('Text', 'plain'), 'Pressed': ('Text', 'plain')})
                self.rejected_adapter(self.apply(page, [adapted('body', 'bootstrap5-body', ['p'], fontFamily='Inter')]))
                self.assertEqual(self.owned(frame), [])

    def test_adapter_precedence_and_name_priority_are_pinned_as_the_bridge_decides_them(self):
        """Given the protocol page with both variables, when Studio detects five arrangements, then an h2 of the monospace family
        is bootstrap5-heading and not mono; an author-role group of two variants whose first equals the body style stays plain and
        keeps its role name; an h2 bound by author id that equals the body style is bootstrap5-body named Heading 2 (the heading
        title beats the adapter name); a btn paragraph equal to the body style is named Body (the adapter name beats the class
        name); and a paragraph of classes btn and lead is named Lead (the first of the bridge's name list wins). These orders are
        pinned decisions of the bridge written as literals: the plan fixes no adapter precedence or name priority."""
        mono = ':root { --bs-font-monospace: monospace; }'
        scenarios = (
            ('a heading of the monospace family', mono, '<h2 style="font-family: monospace; font-size: 33px">Mono head</h2>',
             'Mono head', ('Heading 2', 'bootstrap5-heading')),
            ('an author-role group of two variants', '',
             '<p data-design-role="Intro">Alpha</p><p data-design-role="Intro" style="font-size: 43px">Beta</p>',
             'Alpha', ('Intro', 'plain')),
            ('a heading bound by author id', '', '<h2 data-design-id="x.head" style="font-size: 1em; font-weight: 400">Head</h2>',
             'Head', ('Heading 2', 'bootstrap5-body')),
            ('a btn paragraph equal to the body style', '', '<p class="btn">Bodied</p>', 'Bodied', ('Body', 'bootstrap5-body')),
            ('a paragraph of classes btn and lead', '', '<p class="btn lead" style="font-size: 41px">Led</p>', 'Led', ('Lead', 'plain')))
        for engine in ENGINES:
            for label, css, html, text, expected in scenarios:
                with self.subTest(engine=engine, scenario=label):
                    page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, BOTH_VARIABLES + css), (ADD_HTML, html)])
                    group = self.sample(self.groups(page), text)
                    self.assertEqual((group['suggestedName'], group['adapter']), expected)


HEADING_PAGE = [(ADD_STYLE, BOTH_VARIABLES)]


class HeadingClaimTests(AdapterCase):
    def one(self, engine, html, text):
        """The group of the sample text on the protocol page that has both variables plus the given elements."""
        page, frame = self.start(engine, ROLE_PAGE, HEADING_PAGE + [(ADD_HTML, html)])
        group = self.sample(self.groups(page), text)
        return group['suggestedName'], group['adapter'], [(b['value'], b['reason'], b['stable']) for b in group['selectors']]

    def test_a_tag_level_that_differs_from_its_class_level_is_not_a_heading(self):
        """Given an h2 with class h4 alone on a page with both variables, when Studio detects, then its group is plain named Text
        and binds only its shared class .h4, not h2."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, '<h2 class="h4" style="font-size: 41px">Mixed</h2>', 'Mixed'),
                                 ('Text', 'plain', [('.h4', 'class', True)]))

    def test_a_display_class_beside_a_heading_class_is_not_a_display_heading(self):
        """Given a paragraph with classes display-2 and h3 and a span with class h3 on a page with both variables, when Studio
        detects, then the paragraph's group is named Heading 3, .h3 fails because the span matches it, and the group is plain
        bound by its shared class .display-2, not a heading binding."""
        html = '<p class="display-2 h3" style="font-size: 41px">Both</p><span class="h3" style="font-size: 43px">Other</span>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'Both'), ('Heading 3', 'plain', [('.display-2', 'class', True)]))

    def test_two_display_classes_on_one_element_are_not_a_display_heading(self):
        """Given a paragraph with classes display-1 and display-2 alone on a page with both variables, when Studio detects, then
        its group is plain named Text and binds its shared class .display-1 as an ordinary class binding."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, '<p class="display-1 display-2" style="font-size: 41px">Twin</p>', 'Twin'),
                                 ('Text', 'plain', [('.display-1', 'class', True)]))

    def test_the_display_class_wins_over_the_heading_level_when_the_class_fits(self):
        """Given two h1 elements that both carry display-1, when Studio detects, then their group is named Heading 1 and is
        bootstrap5-heading bound to .display-1 alone as a stable class binding, not to h1."""
        html = ''.join(f'<h1 class="display-1" style="font-size: 41px">{n}</h1>' for n in ('First', 'Second'))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'First'),
                                 ('Heading 1', 'bootstrap5-heading', [('.display-1', 'class', True)]))

    def test_the_heading_level_is_tried_when_the_display_class_matches_a_non_member(self):
        """Given an h1 with class display-1 beside a paragraph with class display-1 of another size, when Studio detects,
        then the h1 group is named Heading 1 and is bootstrap5-heading bound to h1 alone as a stable class binding, because
        .display-1 does not fit."""
        html = ('<h1 class="display-1" style="font-size: 41px">Shown</h1>'
                '<p class="display-1" style="font-size: 43px">Other</p>')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'Shown'), ('Heading 1', 'bootstrap5-heading', [('h1', 'class', True)]))

    def test_the_display_class_is_tried_first_when_the_heading_tag_matches_a_non_member(self):
        """Given an h1 with class display-1 beside a plain h1 of another size, when Studio detects, then the display group is
        named Heading 1 and is bootstrap5-heading bound to .display-1, and the plain h1 group is named Heading 1, plain and
        bound by dom path."""
        html = '<h1 class="display-1" style="font-size: 41px">Shown</h1><h1 style="font-size: 43px">Plain</h1>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'Shown'),
                                 ('Heading 1', 'bootstrap5-heading', [('.display-1', 'class', True)]))
                self.assertEqual(self.one(engine, html, 'Plain')[:2], ('Heading 1', 'plain'))
                self.assertEqual({reason for _, reason, _ in self.one(engine, html, 'Plain')[2]}, {'dom-path'})

    def test_a_group_that_mixes_a_display_class_with_none_is_named_text(self):
        """Given a paragraph with class display-1 followed by a paragraph of the same style without it on a page with both
        variables, when Studio detects, then their one group is named Text."""
        html = '<p class="display-1" style="font-size: 41px">Shown</p><p style="font-size: 41px">Unshown</p>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'Shown')[0], 'Text')

    def test_a_group_equal_to_the_body_style_that_shares_it_with_a_heading_group_gets_no_body_suggestion(self):
        """Given a heading and an author-role paragraph that both equal the body style on a page with both variables, when Studio
        detects, then the heading group is bootstrap5-heading, the author-role group stays plain and no group is body."""
        html = '<h2 style="font-size: 1em; font-weight: 400">Head</h2><p data-design-role="Intro">Role</p>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, ROLE_PAGE, HEADING_PAGE + [(ADD_HTML, html)])
                groups = self.groups(page)
                self.assertEqual({text: self.sample(groups, text)['adapter'] for text in ('Head', 'Role')},
                                 {'Head': 'bootstrap5-heading', 'Role': 'plain'})
                self.assertNotIn('bootstrap5-body', {g['adapter'] for g in groups})

    def test_a_shared_class_past_the_sixteenth_still_names_the_group(self):
        """Given a button with sixteen utility classes and then btn on a page with both variables, when Studio detects, then
        its group is named Button, plain, although the reply carries only sixteen of its shared classes."""
        html = f'<button class="{" ".join(f"u{n}" for n in range(table.SHARED_CLASSES))} btn" style="font-size: 41px">Pressed</button>'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                self.assertEqual(self.one(engine, html, 'Pressed')[:2], ('Button', 'plain'))


class DisplayHeadingApplyTests(AdapterCase):
    def test_applying_a_detected_display_group_renders_its_size_and_weight_over_bootstraps_display_rule(self):
        """Given the protocol page with the vendored Bootstrap 5 stylesheet and two h1 elements of class display-1, when the
        detected group is applied as received with 41px, weight 700 and a family, then both headings compute 41px, 700 and that
        family, and the receipt reports no mismatch and no loss."""
        html = ''.join(f'<h1 class="display-1">Display {n}</h1>' for n in (1, 2))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, ROLE_PAGE, [(LINK_BOOTSTRAP5, BOOTSTRAP5_CSS), (ADD_HTML, html)])
                group = self.sample(self.groups(page), 'Display 1')
                self.assertEqual(group['adapter'], 'bootstrap5-heading')
                reply = self.apply(page, [self.received(group, fontFamily='Georgia, serif', fontSize=41, fontWeight=700)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual([(o['matched'], o['mismatched'], o['losses']) for o in reply['outcomes']], [(2, 0, [])])
                self.assertEqual(frame.locator('h1.display-1').evaluate_all(
                    'els => els.map(el => { const s = getComputedStyle(el); return [s.fontFamily, s.fontSize, s.fontWeight]; })'),
                    [['Georgia, serif', '41px', '700']] * 2)


class ApplyTests(AdapterCase):
    def test_every_template_case_emits_its_exact_bytes_and_changes_exactly_its_variables(self):
        """Given the Bootstrap 5 fixture, when each template case is applied, then the receipt is complete, echoes the roles with their
        adapters, the canonical CSS and digest equal the case, the owned node holds that CSS and the computed variables change
        exactly where the case says; the body case also reports matched 3, checked 3, mismatched 0 and no losses, renders Inter
        at 18px on its three elements and leaves the label at sans-serif and 16px."""
        for engine in ENGINES:
            for case in table.TEMPLATE_CASES:
                with self.subTest(engine=engine, case=case['name']):
                    page, frame = self.start(engine)
                    before = self.variables(frame)
                    reply = self.apply(page, case_roles(case['name']))
                    self.assertEqual(reply['type'], 'design:roles-applied', reply)
                    self.assertEqual((reply['roles'], reply['canonicalCss'], reply['cssHash']), (case['roles'], case['css'], case['hash']))
                    self.assertEqual(self.owned(frame), [case['css']])
                    after = self.variables(frame)
                    self.assertEqual({k: v for k, v in after.items() if v != before[k]}, CASE_VARIABLES[case['name']])
                    if case['name'] == 'body':
                        self.assertEqual(reply['outcomes'], [{'id': 'role-1', 'matched': 3, 'checked': 3, 'mismatched': 0,
                                                              'complete': True, 'losses': []}])
                        self.assertEqual([self.font(frame, name) for name in BODY_IDS[:3]], [['Inter', '18px']] * 3)
                        self.assertEqual(self.font(frame, 'bs5.label'), ['sans-serif', '16px'])

    def test_a_detected_body_group_applies_as_received_with_the_root_block_first(self):
        """Given the detected bootstrap5-body group, when it is applied as received with Inter at 18px, then all four elements
        compute them, the receipt echoes the request with matched 4, checked 4 and mismatched 0, and the canonical CSS is
        the :root block followed by the plain block."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                group = next(g for g in self.groups(page) if g['adapter'] == 'bootstrap5-body')
                request = [self.received(group, fontFamily='Inter', fontSize=18)]
                reply = self.apply(page, request)
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual([self.font(frame, name) for name in BODY_IDS], [['Inter', '18px']] * 4)
                self.assertEqual(reply['roles'], request)
                self.assertEqual([(o['matched'], o['checked'], o['mismatched']) for o in reply['outcomes']], [(4, 4, 0)])
                self.assertEqual(reply['canonicalCss'], DETECTED_CSS)

    def test_a_detected_body_role_changes_the_family_of_an_element_that_takes_it_only_from_the_variable(self):
        """Given the Bootstrap 5 page plus a transparent tooltip whose family comes only from --bs-font-sans-serif, when the
        detected Body group is applied with Inter and then cleared, then no group has the tooltip's text, the tooltip computes
        Inter while applied and its own family again after clear."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(ADD_HTML, '<div class="tooltip" role="tooltip">Tip text</div>')])
                groups = self.groups(page)
                self.assertNotIn('Tip text', [g['sampleText'] for g in groups])
                own = frame.locator('.tooltip').evaluate(FONT)[0]
                self.assertNotEqual(own, 'Inter')
                group = next(g for g in groups if g['adapter'] == 'bootstrap5-body')
                self.assertEqual(self.apply(page, [self.received(group, fontFamily='Inter')])['type'], 'design:roles-applied')
                self.assertEqual(frame.locator('.tooltip').evaluate(FONT)[0], 'Inter')
                self.assertEqual(self.clear(page)['type'], 'design:roles-applied')
                self.assertEqual(frame.locator('.tooltip').evaluate(FONT)[0], own)

    def test_clear_restores_the_variables_the_styles_and_the_dom(self):
        """Given the body, mono and mixed template cases applied in turn, when clear is sent after each, then the variables, every
        computed style and the document return to what they were before the apply and main's markup is byte-identical."""
        for engine in ENGINES:
            for name in ('body', 'mono', 'mixed'):
                with self.subTest(engine=engine, case=name):
                    page, frame = self.start(engine)
                    before = (self.variables(frame), self.snapshot(frame), frame.locator('main').evaluate('el => el.outerHTML'))
                    self.assertEqual(self.apply(page, case_roles(name))['type'], 'design:roles-applied')
                    self.assertNotEqual(self.variables(frame), before[0])
                    self.assertEqual(self.clear(page)['type'], 'design:roles-applied')
                    self.assertEqual((self.variables(frame), self.snapshot(frame), frame.locator('main').evaluate('el => el.outerHTML')),
                                     before)

    def test_an_inline_root_variable_beats_the_role_and_clear_keeps_the_attribute(self):
        """Given an html element whose inline style sets --bs-body-font-family, when the body template is applied, then the inline
        value still wins for that variable, the other variable and the elements take the role, and clear leaves the style
        attribute byte-identical."""
        inline = '--bs-body-font-family: Serif-Inline'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(SET_ROOT_STYLE, inline)])
                self.assertEqual(self.apply(page, case_roles('body'))['type'], 'design:roles-applied')
                self.assertEqual(self.variables(frame, BODY_VARIABLES), {'--bs-body-font-family': 'Serif-Inline', '--bs-font-sans-serif': 'Inter'})
                self.assertEqual(self.font(frame, 'bs5.button'), ['Inter', '18px'])
                self.assertEqual(self.clear(page)['type'], 'design:roles-applied')
                self.assertEqual(frame.evaluate("document.documentElement.getAttribute('style')"), inline)

    def test_bootstrap_declared_sizes_make_a_lost_size_one_complex_cascade_entry(self):
        """Given an author rule with higher specificity and a var() size on the four body elements, when the body adapter is
        applied to them at 18px, then all four checked elements mismatch and the receipt holds one fontSize complex-cascade entry of count 4 with
        no winning selector; without the rule the same apply has no mismatch and no loss."""
        css = 'main.container .btn, main.container .nav-link, main.container .form-label { font-size: var(--lost, 11px); }'
        for engine in ENGINES:
            for author, lost in ((css, True), ('', False)):
                with self.subTest(engine=engine, rule=bool(author)):
                    page, frame = self.start(engine, prepare=[(ADD_STYLE, author)] if author else [])
                    outcome = self.apply(page, [adapted('body', 'bootstrap5-body', BODY_SELECTORS, fontFamily='Inter', fontSize=18)])['outcomes'][0]
                    self.assertEqual((outcome['matched'], outcome['checked'], outcome['mismatched']), (4, 4, 4 if lost else 0))
                    self.assertEqual(outcome['losses'], [{'property': 'fontSize', 'count': 4, 'winningSelector': None,
                                                          'reason': 'complex-cascade'}] if lost else [])

    def test_a_body_sheet_with_its_root_block_is_exactly_128_kib_and_one_byte_more_is_refused(self):
        """Given a body role and two plain roles of 32 long selectors each, when the whole canonical sheet including the :root
        block is exactly 128 KiB, then it installs, and one byte more is rejected as size-limit leaving the first install."""
        root = ':root {\n  --bs-body-font-family: Inter;\n  --bs-font-sans-serif: Inter;\n}\n'

        def build(width, extra):
            roles = [adapted('big0', 'bootstrap5-body', [f'.c0-{j:02d}' + 'x' * (width + (j < extra)) for j in range(32)], fontFamily='Inter')]
            roles += [role(f'big{i}', [f'.c{i}-{j:02d}' + 'x' * (width + (i * 32 + j < extra)) for j in range(32)], fontSize=24) for i in (1, 2)]
            css = root + ', '.join(roles[0]['selectors']) + ' {\n  font-family: Inter;\n}\n'
            css += ''.join(', '.join(r['selectors']) + ' {\n  font-size: 24px;\n}\n' for r in roles[1:])
            return roles, css
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                width = 1000
                while len(build(width + 1, 0)[1].encode('utf-8')) <= table.CSS_BYTES:
                    width += 1
                slack = table.CSS_BYTES - len(build(width, 0)[1].encode('utf-8'))
                roles, css = build(width, slack)
                self.assertEqual(len(css.encode('utf-8')), table.CSS_BYTES)
                exact = self.apply(page, roles, timeout=8000)
                self.assertEqual((exact['type'], exact['canonicalCss'] == css), ('design:roles-applied', True), exact.get('reason'))
                over = self.apply(page, build(width, slack + 1)[0], timeout=8000)
                self.assertEqual((over['type'], over.get('reason')), ('design:rejected', 'size-limit'), over)
                self.assertEqual((self.owned(frame), page.evaluate('revision')), ([css], 1))

    def test_without_the_stylesheet_constructor_the_rule_count_is_the_block_count(self):
        """Given a bridge served without CSSStyleSheet and an author rule that beats the body template's size, when the body
        template is applied, then it installs, and the lost size is reported with its normal reason, not stylesheet-blocked."""
        shadow = "Object.defineProperty(window,'CSSStyleSheet',{value:undefined,configurable:true,writable:true});\n"
        source = shadow + (REPO / 'fontkit-bridge.js').read_text(encoding='utf-8')
        author = 'main.container .btn { font-size: 12px; }'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(ADD_STYLE, author)], bridge_source=source)
                self.assertEqual(frame.evaluate('typeof CSSStyleSheet'), 'undefined')
                reply = self.apply(page, case_roles('body'))
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertEqual(reply['outcomes'][0]['losses'], [{'property': 'fontSize', 'count': 2, 'winningSelector': None,
                                                                   'reason': 'complex-cascade'}])


class EvidenceTests(AdapterCase):
    def test_a_stale_adapter_is_rejected_after_the_bootstrap_link_is_gone(self):
        """Given a body suggestion detected on the Bootstrap 5 page, when its Bootstrap link is removed, a second detect sees
        plain groups and the earlier suggestion is applied with the new page version, then it is rejected as an unsupported
        adapter and nothing is written."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                request = [self.received(next(g for g in self.groups(page) if g['adapter'] == 'bootstrap5-body'), fontFamily='Inter')]
                frame.evaluate("document.querySelector('link[href*=\"bootstrap\"]').remove()")
                later = self.detect(page)
                self.assertEqual({g['adapter'] for g in later['groups']}, {'plain'})
                self.rejected_adapter(self.apply(page, request, pageVersion=later['currentPageVersion']))
                self.assertEqual((self.owned(frame), page.evaluate('revision')), ([], 0))

    def test_apply_evidence_needs_both_variables(self):
        """Given the protocol page that defines only one of the two body variables, each in turn, when a bootstrap5-body role is
        applied, then it is rejected as an unsupported adapter and no owned node is installed."""
        for engine in ENGINES:
            for css in (':root { --bs-body-font-family: serif; }', ':root { --bs-font-sans-serif: sans-serif; }'):
                with self.subTest(engine=engine, css=css):
                    page, frame = self.start(engine, ROLE_PAGE, [(ADD_STYLE, css), (ADD_HTML, '<p>Inherits</p>')])
                    self.rejected_adapter(self.apply(page, [adapted('body', 'bootstrap5-body', ['p'], fontFamily='Inter')]))
                    self.assertEqual(self.owned(frame), [])

    def test_a_heading_role_with_one_display_class_or_one_level_class_is_accepted_and_renders(self):
        """Given the Bootstrap 5 page, when a bootstrap5-heading role names only .display-1 or only .h3 at 30px, then each is
        applied and every matching element computes 30px."""
        for engine in ENGINES:
            for selector in ('.display-1', '.h3'):
                with self.subTest(engine=engine, selector=selector):
                    page, frame = self.start(engine)
                    reply = self.apply(page, [adapted('one', 'bootstrap5-heading', [selector], fontSize=30)])
                    self.assertEqual(reply['type'], 'design:roles-applied', reply)
                    self.assertEqual(frame.locator(selector).evaluate_all('els => els.map(el => getComputedStyle(el).fontSize)'), ['30px'])

    def test_a_heading_role_with_the_bare_tag_is_accepted_and_loses_to_bootstraps_class_rule(self):
        """Given the Bootstrap 5 page plus a bare h3, when a bootstrap5-heading role names only h3 at 30px, then it is applied, the
        owned node holds an h3 rule, the bare h3 computes 30px, h3.h3 keeps 28px because Bootstrap's .h3,h3 rule matched through
        .h3 outranks the bare tag, and the receipt holds one fontSize loss with one mismatch."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine, prepare=[(ADD_HTML, '<h3>Bare</h3>')])
                reply = self.apply(page, [adapted('one', 'bootstrap5-heading', ['h3'], fontSize=30)])
                self.assertEqual(reply['type'], 'design:roles-applied', reply)
                self.assertTrue(self.owned(frame)[0].startswith('h3 {'), self.owned(frame))
                self.assertEqual(frame.locator('h3:not(.h3)').evaluate(FONT)[1], '30px')
                self.assertEqual(frame.locator('h3.h3').evaluate(FONT)[1], '28px')
                self.assertEqual([(o['matched'], o['mismatched'], [loss['property'] for loss in o['losses']]) for o in reply['outcomes']],
                                 [(2, 1, ['fontSize'])])

    def test_a_heading_role_must_name_one_level_or_one_display_class(self):
        """Given the Bootstrap 5 page, when heading roles name two levels, a level and a display class, two display classes, a
        non-heading class or level 7, then each is rejected as an unsupported adapter with nothing written, while h2 and .h2
        in either order are accepted."""
        bad = (['h2', '.h3'], ['h2', '.display-1'], ['.display-1', '.display-2'], ['.lead'], ['h7'], ['h2', '.h2', '.h3'])
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                for selectors in bad:
                    self.rejected_adapter(self.apply(page, [adapted('bad', 'bootstrap5-heading', selectors, fontSize=30)]))
                    self.assertEqual((self.owned(frame), page.evaluate('revision')), ([], 0))
                self.assertEqual(self.apply(page, [adapted('ok', 'bootstrap5-heading', ['.h2', 'h2'], fontSize=30)])['type'],
                                 'design:roles-applied')

    def test_evidence_comes_from_the_page_and_not_from_the_live_preview(self):
        """Given the body template applied (its preview defines both variables) and the Bootstrap link then removed, when Studio
        detects and applies the body adapter, then every detected group is plain, the apply is rejected as an unsupported
        adapter and the preview, its owned node and the revision are unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                css = self.apply(page, case_roles('body'))['canonicalCss']
                frame.evaluate("document.querySelector('link[href*=\"bootstrap\"]').remove()")
                later = self.detect(page)
                self.assertEqual({g['adapter'] for g in later['groups']}, {'plain'})
                self.rejected_adapter(self.apply(page, case_roles('body'), pageVersion=later['currentPageVersion']))
                self.assertEqual((self.owned(frame), page.evaluate('revision')), ([css], 1))
                self.assertEqual(self.variables(frame, BODY_VARIABLES), dict.fromkeys(BODY_VARIABLES, 'Inter'))

    def test_no_transition_ban_survives_an_apply_over_a_live_preview(self):
        """Given a live body preview, when the body template is applied again, then no style element containing transition: none
        is left in the document and .btn still computes the vendored transition duration."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                self.assertEqual(self.apply(page, case_roles('body'))['type'], 'design:roles-applied')
                self.assertEqual(self.apply(page, case_roles('body'))['type'], 'design:roles-applied')
                self.assertEqual(frame.evaluate("Array.from(document.querySelectorAll('style')).filter(s => s.textContent.includes('transition: none')).length"), 0)
                self.assertEqual(frame.locator('.btn').first.evaluate('el => getComputedStyle(el).transitionDuration'),
                                 '0.15s, 0.15s, 0.15s, 0.15s')

    def test_detect_with_a_live_bootstrap_preview_returns_the_groups_of_a_detect_without_it(self):
        """Given the Bootstrap 5 page detected before and after the body template is applied, when the two replies are compared,
        then their groups are equal and every oracle group's identity and variants are among them."""
        oracle = json.loads((REPO / 'fixtures/bootstrap5-static/expected-styles.json').read_text(encoding='utf-8'))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.start(engine)
                plain = self.groups(page)
                self.assertEqual(self.apply(page, case_roles('body'))['type'], 'design:roles-applied')
                live = self.groups(page)
                self.assertEqual(live, plain)
                actual = {json.dumps(g['identity'], sort_keys=True): [v['style'] for v in g['signatures']] for g in live}
                for expected in oracle['groups']:
                    self.assertEqual(actual[json.dumps(expected['identity'], sort_keys=True)], [v['signature'] for v in expected['variants']])
