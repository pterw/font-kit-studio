"""Literal offline rendered oracles for the R2 static corpus."""

import hashlib
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from support import ENGINES, close_contexts, new_context, route_virtual_origins

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / 'fixtures'
HTTPS_PREFIX = re.compile(r'^https://', re.I)


# Read rendered direct text ranges, never a descendant-text count or a detector.
RENDERED_PARENTS = r"""() => {
    const byParent = new Map();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
        const text = walker.currentNode;
        if (!text.textContent.trim()) continue;
        const el = text.parentElement;
        if (el.closest('head,script,style,template,noscript,textarea,select,option,svg,#fontkit-bridge-overlay,#fontkit-bridge-hover,.fontkit-placed-asset')) continue;
        let hidden = false;
        for (let parent = el; parent; parent = parent.parentElement) {
            const style = getComputedStyle(parent);
            if (style.display === 'none' || ['hidden', 'collapse'].includes(style.visibility)
                || Number(style.opacity) === 0) hidden = true;
        }
        const style = getComputedStyle(el);
        if (/rgba\([^)]*,\s*0\)$/.test(style.color)) hidden = true;
        const range = document.createRange();
        range.selectNodeContents(text);
        if (hidden || ![...range.getClientRects()].some(rect => rect.width > 0 && rect.height > 0)) continue;
        if (byParent.has(el)) continue;
        byParent.set(el, {
            id: el.getAttribute('data-design-id') || el.id,
            authorRole: el.getAttribute('data-design-role'),
            signature: {
                fontFamily: style.fontFamily.replace(/\s+/g, ' ').trim(),
                fontSize: Number(parseFloat(style.fontSize).toFixed(2)),
                fontWeight: Math.round(Number(style.fontWeight)),
                textTransform: style.textTransform,
                letterSpacing: style.letterSpacing === 'normal' ? 0
                    : Number((parseFloat(style.letterSpacing) / parseFloat(style.fontSize)).toFixed(4))
            }
        });
    }
    return [...byParent.values()];
}"""


class StaticFixturesTest(unittest.TestCase):
    def setUp(self):
        self.contexts = []

    def tearDown(self):
        close_contexts(self.contexts)

    def open_fixture(self, engine, name, root=None):
        context = new_context(engine, viewport={'width': 1440, 'height': 900})
        self.contexts.append(context)
        # Route registration is last-in-first-out. This fallback makes the guard
        # canary and a removed-guard mutation safe without contacting a host.
        context.route(HTTPS_PREFIX, lambda route: route.fulfill(
            status=200, body='local fallback', headers={'access-control-allow-origin': '*'}))
        blocked = []

        def abort_https(route):
            blocked.append(route.request.url)
            route.abort()

        context.route(HTTPS_PREFIX, abort_https)
        canary = context.new_page()
        try:
            results = []
            for url in ('https://isolation.invalid/canary', 'https://isolation.invalid/css?family=Local'):
                result = canary.evaluate('(url) => fetch(url).then(() => "fulfilled", () => "blocked")', url)
                results.append(result)
            self.assertEqual(len(blocked), 2, 'the HTTPS abort guard must intercept both canaries')
            self.assertEqual(results, ['blocked', 'blocked'])
        finally:
            canary.close()
        route_virtual_origins(context, {'http://fixture.test': root or FIXTURES / name})
        page = context.new_page()
        page.goto('http://fixture.test/', wait_until='load')
        self.assertEqual(len(blocked), 2, 'fixtures must not request HTTPS')
        return page

    def test_existing_bootstrap5_hero_remains_rendered(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_fixture(engine, 'bootstrap5-static')
                self.assertEqual(page.locator('[data-design-id="bs.hero.title"]').inner_text(), 'Type that travels well')
                self.assertEqual(page.locator('[data-design-id="bs.hero.title"]').evaluate('el => getComputedStyle(el).fontSize'), '40px')
                self.assertEqual(page.locator('[data-design-id="bs.hero.lead"]').inner_text(), 'A static Bootstrap page that allows only its own scripts and styles.')
                self.assertEqual(page.locator('[data-design-id="bs.hero.cta"]').inner_text(), 'Get started')

    def test_bootstrap4_heading_is_rendered_from_local_vendor_css(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_fixture(engine, 'bootstrap4-static')
                self.assertEqual(page.locator('h1').count(), 1)
                self.assertEqual(page.locator('h1').evaluate('el => getComputedStyle(el).fontSize'), '40px')

    def test_bootstrap_semantic_class_corpus_is_rendered(self):
        for engine in ENGINES:
            for name, displays in (('bootstrap4-static', [96, 88, 72, 56]),
                                    ('bootstrap5-static', [80, 72, 64, 56, 48, 40])):
                with self.subTest(engine=engine, fixture=name):
                    page = self.open_fixture(engine, name)
                    self.assertEqual(page.locator('.type-corpus .h1').count(), 1)
                    cases = [(f'.type-corpus .h{i}', size) for i, size in
                             enumerate([40, 32, 28, 24, 20, 16], 1)]
                    cases += [(f'.type-corpus .display-{i}', size) for i, size in enumerate(displays, 1)]
                    cases += [('.type-corpus .lead', 20), ('.type-corpus .btn', 16),
                              ('.type-corpus .nav-link', 16), ('.type-corpus .navbar-brand', 20),
                              ('.type-corpus .card-title', 20), ('.type-corpus .form-label', 16)]
                    for selector, size in cases:
                        self.assertEqual(page.locator(selector).count(), 1, selector)
                        actual = page.locator(selector).evaluate('el => parseFloat(getComputedStyle(el).fontSize)')
                        self.assertEqual(actual, size, selector)

    def test_large_corpus_has_exactly_5000_rendered_direct_text_parents(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_fixture(engine, 'large-page')
                parents = page.evaluate(RENDERED_PARENTS)
                self.assertEqual(len(parents), 5000)
                self.assertEqual(len({item['id'] for item in parents}), 5000)
                counts = Counter(item['id'].split('.')[0] for item in parents)
                self.assertEqual(counts, {f'g{i:02}': 250 for i in range(20)})

    def test_nested_dedup_and_excluded_text_have_independent_range_geometry(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_fixture(engine, 'large-page')
                self.assertEqual(page.locator('[data-design-id="g00.000"] [data-design-id="g00.001"]').count(), 1)
                self.assertEqual(page.locator('[data-design-id="g00.000"]').evaluate(
                    'el => [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).length'), 2)
                parents = page.evaluate(RENDERED_PARENTS)
                ids = [item['id'] for item in parents]
                self.assertEqual(ids.count('g00.000'), 1)
                self.assertEqual(ids.count('g00.001'), 1)
                self.assertEqual(ids.count('g00.002'), 1)
                geometry = page.locator('[data-design-id="g00.002"]').evaluate("""el => {
                    const range = document.createRange(); range.selectNodeContents(el.firstChild);
                    return {box: el.getBoundingClientRect().width,
                        text: [...range.getClientRects()].some(r => r.width > 0 && r.height > 0)};
                }""")
                self.assertEqual(geometry, {'box': 0, 'text': True})
                excluded = ['hidden-direct', 'hidden-ancestor', 'invisible', 'collapsed',
                            'transparent-parent', 'transparent-color', 'zero-text', 'nested-hidden',
                            'fontkit-bridge-overlay', 'fontkit-bridge-hover', 'placed-asset',
                            'excluded-textarea', 'excluded-option', 'svg-text', 'shadow-host', 'pseudo-only']
                for identity in excluded:
                    self.assertEqual(page.locator('#' + identity).count(), 1, identity)
                    self.assertNotIn(identity, ids)
                geometry = page.locator('#exclusions').evaluate("""root => {
                    function area(id) {
                        const el = root.querySelector('#' + id);
                        const range = document.createRange(); range.selectNodeContents(el);
                        return [...range.getClientRects()].some(r => r.width > 0 && r.height > 0);
                    }
                    return {hidden: area('hidden-direct'), zero: area('zero-text'),
                        transparent: area('transparent-parent'), invisible: area('invisible')};
                }""")
                self.assertEqual(geometry, {'hidden': False, 'zero': False,
                                            'transparent': True, 'invisible': True})
                self.assertEqual(page.locator('#hidden-control').get_attribute('type'), 'hidden')
                self.assertFalse(page.locator('#excluded-textarea').is_visible())
                self.assertFalse(page.locator('#excluded-option').is_visible())
                self.assertGreater(page.locator('[data-design-id="g19.249"]').bounding_box()['y'], 900)
                self.assertIn('g19.249', ids)

    def test_heartbeat_and_real_typing_acknowledgement_preserve_corpus(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_fixture(engine, 'large-page')
                self.assertEqual(page.get_by_role('textbox', name='Responsiveness probe', exact=True).count(), 1)
                before = page.evaluate(RENDERED_PARENTS)
                beat = page.evaluate('window.fixtureProbe.heartbeat')
                field = page.get_by_role('textbox', name='Responsiveness probe', exact=True)
                field.click()
                for text in ('a', 'B', '7'):
                    field.press_sequentially(text)
                    expected = 'aB7'[:('a', 'B', '7').index(text) + 1]
                    self.assertEqual(field.input_value(), expected)
                    page.wait_for_function('(value) => window.fixtureProbe.acknowledged === value', arg=expected, timeout=5000)
                page.wait_for_function('(beat) => window.fixtureProbe.heartbeat > beat', arg=beat, timeout=5000)
                self.assertEqual(page.evaluate('window.fixtureProbe.inputEvents'), 3)
                self.assertEqual(page.evaluate(RENDERED_PARENTS), before)

    def oracle(self, name):
        return json.loads((FIXTURES / name / 'expected-styles.json').read_text(encoding='utf-8'))

    def assert_rendered_oracle(self, page, oracle):
        parents = page.evaluate(RENDERED_PARENTS)
        self.assertEqual(len(parents), oracle['eligibleParentCount'])
        self.assertEqual(len({item['id'] for item in parents}), len(parents))
        self.assertEqual(oracle['schema'], 'fontkit-static-style-oracle')
        self.assertEqual(oracle['schemaVersion'], 1)
        actual_by_id = {item['id']: item for item in parents}
        if 'elements' in oracle:
            self.assertEqual(set(actual_by_id), {item['id'] for item in oracle['elements']})
            for element in oracle['elements']:
                self.assertEqual(actual_by_id[element['id']]['signature'], element['signature'], element['id'])
                actual_role = actual_by_id[element['id']]['authorRole']
                self.assertEqual(actual_role.strip() if actual_role else None, element['authorRole'])
                self.assertEqual(page.locator(element['selector']).count(), 1, element['selector'])
        else:
            expected = {group['id']: group['signature'] for group in oracle['groups']}
            for item in parents:
                self.assertEqual(item['signature'], expected[item['id'].split('.')[0]], item['id'])
                self.assertIsNone(item['authorRole'])
        self.assertEqual(len(oracle['groups']), oracle['groupCount'])
        self.assertEqual(sum(group['elementCount'] for group in oracle['groups']), len(parents))
        for group in oracle['groups']:
            matched = {}
            for binding in group['bindings']:
                ids = page.locator(binding['selector']).evaluate_all(
                    'els => els.map(el => el.getAttribute("data-design-id"))')
                self.assertEqual(len(ids), binding['elementCount'], binding['selector'])
                matched.update({identity: actual_by_id[identity] for identity in ids})
            self.assertEqual(len(matched), group['elementCount'], group['id'])
            variants = Counter(json.dumps(item['signature'], sort_keys=True) for item in matched.values())
            self.assertEqual(variants, Counter({json.dumps(v['signature'], sort_keys=True): v['elementCount']
                                               for v in group['variants']}), group['id'])
            identity = group['identity']
            if identity['kind'] == 'author-role':
                self.assertEqual({item['authorRole'].strip() for item in matched.values()}, {identity['name']})
            else:
                self.assertEqual({json.dumps(item['signature'], sort_keys=True) for item in matched.values()},
                                 {json.dumps(identity['style'], sort_keys=True)})

    def test_all_literal_style_tuples_counts_roles_and_bindings_match_rendering(self):
        for engine in ENGINES:
            for name in ('bootstrap4-static', 'bootstrap5-static', 'large-page'):
                with self.subTest(engine=engine, fixture=name):
                    self.assert_rendered_oracle(self.open_fixture(engine, name), self.oracle(name))

    def assert_vendor_bytes(self, vendor, data):
        forms = vendor.get('allowedByteForms', [vendor])
        self.assertIn((hashlib.sha256(data).hexdigest(), len(data)),
                      [(form['sha256'], form['bytes']) for form in forms])

    def test_vendor_sources_and_existing_bootstrap5_variables(self):
        for name in ('bootstrap4-static', 'bootstrap5-static'):
            oracle = self.oracle(name)
            for vendor in oracle['metadata']['vendor']:
                data = (FIXTURES / name / vendor['path']).read_bytes()
                self.assert_vendor_bytes(vendor, data)
                if name == 'bootstrap5-static':
                    canonical = data.replace(b'\r\n', b'\n')
                    self.assert_vendor_bytes(vendor, canonical)
                    self.assert_vendor_bytes(vendor, canonical.replace(b'\n', b'\r\n'))
                    with self.assertRaises(AssertionError):
                        self.assert_vendor_bytes(vendor, canonical + b'\n')
                else:
                    with self.assertRaises(AssertionError):
                        self.assert_vendor_bytes(vendor, data.replace(b'\n', b'\r\n'))
                self.assertIn('/v' + oracle['metadata']['version'] + '/', vendor['sourceURL'])
            for engine in ENGINES:
                with self.subTest(engine=engine, fixture=name):
                    page = self.open_fixture(engine, name)
                    variables = page.locator('.navbar-brand').evaluate("""el => ({
                        brand: getComputedStyle(el).getPropertyValue('--bs-navbar-brand-font-size').trim(),
                        button: getComputedStyle(document.querySelector('.type-corpus .btn'))
                            .getPropertyValue('--bs-btn-font-size').trim()
                    })""")
                    self.assertEqual(variables, {'brand': '1.25rem', 'button': '1rem'}
                                     if name == 'bootstrap5-static' else {'brand': '', 'button': ''})

    def test_unknown_version_scratch_variant_preserves_literal_rendering(self):
        source = FIXTURES / 'bootstrap4-static'
        with tempfile.TemporaryDirectory(prefix='fks-r2-unknown-') as directory:
            scratch = Path(directory)
            (scratch / 'vendor').mkdir()
            css = (source / 'vendor/bootstrap.min.css').read_text(encoding='utf-8')
            css = re.sub(r'/\*![\s\S]*?\*/', '', css, count=1)
            (scratch / 'vendor/bootstrap.min.css').write_text(css, encoding='utf-8')
            for filename in ('index.html', 'app.css'):
                (scratch / filename).write_bytes((source / filename).read_bytes())
            self.assertFalse('Bootstrap v' in css, 'unknown variant must omit Bootstrap version banner')
            for engine in ENGINES:
                with self.subTest(engine=engine):
                    page = self.open_fixture(engine, 'bootstrap4-static', root=scratch)
                    self.assert_rendered_oracle(page, self.oracle('bootstrap4-static'))
                    # No adapter is implemented here: this is fallback input evidence.
                    self.assertEqual(page.locator('.btn').evaluate(
                        'el => getComputedStyle(el).getPropertyValue("--bs-btn-font-size").trim()'), '')

    def test_near_duplicate_literals_cover_inclusive_and_outside_boundaries(self):
        oracle = self.oracle('large-page')
        groups = {group['id']: group['signature'] for group in oracle['groups']}
        for group in oracle['groups']:
            self.assertEqual(group['identity']['style'], group['signature'], group['id'])
        self.assertEqual(len(groups), 20)
        self.assertEqual(len({json.dumps(style, sort_keys=True) for style in groups.values()}), 20)
        self.assertEqual(groups['g00'], {'fontFamily': 'serif', 'fontSize': 20, 'fontWeight': 400,
                                       'textTransform': 'none', 'letterSpacing': 0})
        self.assertEqual(groups['g02'], {'fontFamily': 'serif', 'fontSize': 21, 'fontWeight': 500,
                                       'textTransform': 'none', 'letterSpacing': 0.02})
        for case in oracle['thresholdCases']:
            left, right = groups[case['left']], groups[case['right']]
            near = (left['fontFamily'] == right['fontFamily']
                    and left['textTransform'] == right['textTransform']
                    and abs(left['fontSize'] - right['fontSize']) <= 1
                    and abs(left['fontWeight'] - right['fontWeight']) <= 100
                    and abs(left['letterSpacing'] - right['letterSpacing']) <= 0.02)
            self.assertEqual(near, case['nearDuplicate'], case['reason'])


if __name__ == '__main__':
    unittest.main()
