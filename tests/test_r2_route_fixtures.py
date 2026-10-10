"""Real document/history transitions with independent literal rendered oracles."""

import json
import re
import unittest
from contextlib import contextmanager
from pathlib import Path

from support import ENGINES, close_contexts, new_context, route_virtual_origins

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'multi-page'
ORIGIN = 'http://routes.test'
HTTPS_PREFIX = re.compile(r'^https://', re.I)


RENDERED_PARENTS = r"""() => {
    const parents = new Map();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
        const text = walker.currentNode;
        if (!text.textContent.trim()) continue;
        const el = text.parentElement;
        if (el.closest('script,style,template,noscript')) continue;
        let visible = true;
        for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
            const css = getComputedStyle(ancestor);
            if (css.display === 'none' || ['hidden', 'collapse'].includes(css.visibility)
                || Number(css.opacity) === 0) visible = false;
        }
        const range = document.createRange(); range.selectNodeContents(text);
        if (!visible || ![...range.getClientRects()].some(r => r.width > 0 && r.height > 0)) continue;
        const css = getComputedStyle(el);
        parents.set(el, {
            id: el.getAttribute('data-design-id') || el.id,
            authorRole: el.getAttribute('data-design-role'),
            signature: {
                fontFamily: css.fontFamily.replace(/\s+/g, ' ').trim(),
                fontSize: Number(parseFloat(css.fontSize).toFixed(2)),
                fontWeight: Math.round(Number(css.fontWeight)),
                textTransform: css.textTransform,
                letterSpacing: css.letterSpacing === 'normal' ? 0
                    : Number((parseFloat(css.letterSpacing) / parseFloat(css.fontSize)).toFixed(4))
            }
        });
    }
    return [...parents.values()];
}"""


class RouteFixturesTest(unittest.TestCase):
    def setUp(self):
        self.contexts = []
        self.request_lists = []

    def tearDown(self):
        close_contexts(self.contexts)

    @contextmanager
    def open(self, engine, path='/index.html'):
        context = new_context(engine, viewport={'width': 1440, 'height': 900})
        self.contexts.append(context)
        try:
            # Retain this earlier local fulfillment even when mutating the abort guard.
            context.route(HTTPS_PREFIX, lambda route: route.fulfill(
                status=200, body='local canary fallback', headers={'access-control-allow-origin': '*'}))
            intercepted = []

            def abort_https(route):
                intercepted.append(route.request.url)
                route.abort()

            context.route(HTTPS_PREFIX, abort_https)
            canary = context.new_page()
            try:
                results = [canary.evaluate(
                    '(url) => fetch(url).then(() => "fulfilled", () => "blocked")', url)
                    for url in ('https://isolation.invalid/route', 'https://isolation.invalid/css?family=Local')]
                self.assertEqual(len(intercepted), 2, 'the owned HTTPS guard must intercept both canaries')
                self.assertEqual(results, ['blocked', 'blocked'])
            finally:
                canary.close()
            route_virtual_origins(context, {ORIGIN: FIXTURE})
            requests = []
            self.request_lists.append(requests)
            context.on('request', lambda request: requests.append(request.url))
            page = context.new_page()
            page.set_default_timeout(5000)
            page.set_default_navigation_timeout(5000)
            page.goto(ORIGIN + path, wait_until='load')
            self.assertEqual(len(intercepted), 2, 'fixture navigation must not request HTTPS')
            yield page, requests
        finally:
            close_contexts(self.contexts)

    def oracle(self):
        return json.loads((FIXTURE / 'expected-styles.json').read_text(encoding='utf-8'))

    def assert_snapshot(self, page, key):
        oracle = self.oracle()
        self.assertEqual((oracle['schema'], oracle['schemaVersion']), ('fontkit-route-style-oracle', 1))
        expected = next(snapshot for snapshot in oracle['snapshots'] if snapshot['key'] == key)
        page.wait_for_url(ORIGIN + expected['url'])
        self.assertEqual(page.url, ORIGIN + expected['url'])
        self.assertEqual(page.locator('body').get_attribute('data-page'), expected['page'])
        if 'view' in expected:
            page.wait_for_function("""expected => {
                const content = document.querySelector('#route-content');
                return content.dataset.view === expected.view
                    && content.dataset.renderState === expected.renderState;
            }""", arg=expected)
            self.assertEqual(page.locator('#route-content').get_attribute('aria-busy'),
                             'true' if expected['renderState'] == 'pending' else 'false')
        rows = oracle['chrome'][expected['chromeRef']] + expected['content'] + expected.get('extra', [])
        actual = page.evaluate(RENDERED_PARENTS)
        self.assertEqual(len(actual), expected['eligibleParentCount'])
        self.assertEqual(sum(row['elementCount'] for row in rows), expected['eligibleParentCount'])
        actual_by_id = {item['id']: item for item in actual}
        self.assertEqual(len(actual_by_id), len(actual), 'eligible direct-text parents are counted once')
        self.assertEqual(set(actual_by_id), {row['id'] for row in rows})
        for row in rows:
            element = page.locator(row['selector'])
            self.assertEqual(element.count(), row['elementCount'], row['selector'])
            self.assertEqual(element.inner_text(), row['text'], row['selector'])
            self.assertEqual(actual_by_id[row['id']]['signature'], oracle['signatures'][row['signatureRef']], row['id'])
            self.assertEqual(actual_by_id[row['id']]['authorRole'], row['authorRole'])
        for check in expected['selectorChecks']:
            self.assertEqual(page.locator(check['selector']).count(), check['elementCount'])
            matching = page.locator(check['selector']).evaluate_all(
                'els => els.map(el => el.getAttribute("data-design-id"))')
            self.assertEqual([actual_by_id[identity]['signature'] for identity in matching],
                             [oracle['signatures'][ref] for ref in check['signatureRefs']])
        self.assertTrue(all(url.startswith(ORIGIN + '/') for urls in self.request_lists for url in urls),
                        'all fixture requests must remain locally served HTTP')

    def test_ordinary_links_navigate_real_documents_with_rendered_typography(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine) as (page, requests):
                    self.assert_snapshot(page, 'index')
                    self.assertEqual(page.locator('.shared-title').count(), 1)
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'Home evidence')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '32px')
                    page.get_by_role('link', name='Article', exact=True).click()
                    page.wait_for_url(ORIGIN + '/article.html')
                    self.assert_snapshot(page, 'article')
                    self.assertEqual(page.locator('.article-title').inner_text(), 'Article evidence')
                    self.assertEqual(page.locator('.article-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '32px')
                    self.assertIn(ORIGIN + '/article.html', requests)

    def test_conflict_zero_match_and_unvisited_navigation_inputs(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/conflict.html') as (page, requests):
                    self.assert_snapshot(page, 'conflict')
                    self.assertEqual(page.locator('.shared-title').count(), 1)
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'CONFLICT EVIDENCE')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '40px')
                    page.get_by_role('link', name='Article', exact=True).click()
                    page.wait_for_url(ORIGIN + '/article.html')
                    self.assert_snapshot(page, 'article')
                    self.assertEqual(page.locator('.shared-title').count(), 0)
                    self.assertEqual(page.locator('.article-title').inner_text(), 'Article evidence')
                    page.get_by_role('link', name='Home', exact=True).click()
                    page.wait_for_url(ORIGIN + '/index.html')
                    self.assert_snapshot(page, 'index')
                    self.assertEqual(page.get_by_role('link', name='Unvisited', exact=True).get_attribute('href'), 'unvisited.html')
                    self.assertFalse(any('/unvisited.html' in request for request in requests), requests)

    def test_explicit_unvisited_baseline_is_separate_from_default_navigation(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/unvisited.html') as (page, requests):
                    self.assert_snapshot(page, 'unvisited')
                    self.assertEqual(page.locator('.shared-title').count(), 1)
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'Unvisited evidence')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '24px')
                    self.assertIn(ORIGIN + '/unvisited.html', requests)

    def test_native_history_cross_origin_exception_preserves_rendered_document(self):
        # Existing browser behavior is characterized GREEN, not treated as a fixture defect.
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine) as (page, _):
                    self.assert_snapshot(page, 'index')
                    self.assertEqual(page.evaluate("""() => {
                        try { history.pushState({}, '', 'http://other.invalid/'); return 'unexpected success'; }
                        catch (error) { return error.name; }
                    }"""), 'SecurityError')
                    self.assertEqual(page.url, ORIGIN + '/index.html')
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'Home evidence')

    def test_spa_push_replace_back_forward_are_real_ui_history_transitions(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/spa.html') as (page, requests):
                    self.assert_snapshot(page, 'spa-home')
                    self.assertEqual(page.get_by_role('button', name='Push detail', exact=True).count(), 1)
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA home evidence')
                    initial_length = page.evaluate('history.length')
                    page.get_by_role('button', name='Push detail', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=detail')
                    self.assert_snapshot(page, 'spa-detail')
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA detail evidence')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '36px')
                    self.assertEqual(page.evaluate('history.length'), initial_length + 1)
                    page.get_by_role('button', name='Replace note', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note')
                    self.assert_snapshot(page, 'spa-note')
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA NOTE EVIDENCE')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '26px')
                    self.assertEqual(page.evaluate('history.length'), initial_length + 1)
                    page.get_by_role('button', name='Back', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html')
                    self.assert_snapshot(page, 'spa-home')
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA home evidence')
                    page.get_by_role('button', name='Forward', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note')
                    self.assert_snapshot(page, 'spa-note')
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA NOTE EVIDENCE')
                    self.assertFalse(any('?route=' in request for request in requests), requests)

    def test_hash_link_and_history_restore_actual_query_hash_and_styles(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/spa.html') as (page, _):
                    self.assert_snapshot(page, 'spa-home')
                    self.assertEqual(page.get_by_role('link', name='Hash section', exact=True).count(), 1)
                    page.get_by_role('button', name='Replace note', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note')
                    self.assert_snapshot(page, 'spa-note')
                    page.get_by_role('link', name='Hash section', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note#section')
                    self.assert_snapshot(page, 'spa-hash')
                    page.wait_for_function('document.querySelector(".shared-title").textContent === "section evidence"')
                    self.assertEqual(page.locator('.shared-title').evaluate(
                        'el => getComputedStyle(el).fontSize'), '28px')
                    page.get_by_role('button', name='Back', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note')
                    self.assert_snapshot(page, 'spa-note')
                    page.wait_for_function('document.querySelector(".shared-title").textContent === "SPA NOTE EVIDENCE"')
                    page.get_by_role('button', name='Forward', exact=True).click()
                    page.wait_for_url(ORIGIN + '/spa.html?route=note#section')
                    self.assert_snapshot(page, 'spa-hash')
                    page.wait_for_function('document.querySelector(".shared-title").textContent === "section evidence"')

    def test_delayed_replacement_exposes_pending_then_real_new_rendered_nodes(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/spa.html') as (page, requests):
                    self.assert_snapshot(page, 'spa-home')
                    self.assertEqual(page.get_by_role('button', name='Load delayed content', exact=True).count(), 1)
                    original = page.locator('.shared-title').element_handle()
                    try:
                        page.get_by_role('button', name='Load delayed content', exact=True).click()
                        page.wait_for_url(ORIGIN + '/spa.html?route=delayed')
                        self.assert_snapshot(page, 'spa-pending')
                        self.assertEqual(page.locator('#route-content').get_attribute('data-render-state'), 'pending')
                        self.assertEqual(page.locator('#route-content').get_attribute('aria-busy'), 'true')
                        self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA home evidence')
                        self.assertTrue(page.get_by_role('button', name='Resolve delayed content', exact=True).is_visible())
                        page.get_by_role('button', name='Resolve delayed content', exact=True).click()
                        page.wait_for_function('document.querySelector("#route-content").dataset.renderState === "settled"')
                        self.assert_snapshot(page, 'spa-delayed')
                        self.assertEqual(page.locator('.shared-title').inner_text(), 'Delayed evidence')
                        self.assertEqual(page.locator('.shared-title').evaluate(
                            'el => getComputedStyle(el).fontSize'), '30px')
                        self.assertEqual(page.locator('#route-content').get_attribute('aria-busy'), 'false')
                        self.assertFalse(original.evaluate('el => el.isConnected'))
                        self.assertFalse(any('?route=delayed' in request for request in requests), requests)
                    finally:
                        original.dispose()

    def test_same_url_state_replacement_preserves_exact_query_order_and_hash(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                exact = '/spa.html?route=detail&b=2&a=1#keep'
                with self.open(engine, exact) as (page, requests):
                    self.assert_snapshot(page, 'spa-exact-detail')
                    self.assertEqual(page.get_by_role('button', name='Replace same URL', exact=True).count(), 1)
                    self.assertEqual(page.locator('.shared-title').inner_text(), 'SPA detail evidence')
                    initial_length = page.evaluate('history.length')
                    original = page.locator('.shared-title').element_handle()
                    try:
                        page.get_by_role('button', name='Replace same URL', exact=True).click()
                        self.assert_snapshot(page, 'spa-exact-same')
                        self.assertEqual(page.url, ORIGIN + exact)
                        self.assertEqual(page.evaluate('history.length'), initial_length)
                        self.assertEqual(page.locator('.shared-title').inner_text(), 'Same URL evidence')
                        self.assertEqual(page.locator('.shared-title').evaluate(
                            'el => getComputedStyle(el).fontFamily'), 'cursive')
                        self.assertEqual(page.evaluate('history.state'), {'view': 'same'})
                        self.assertFalse(original.evaluate('el => el.isConnected'))
                        self.assertEqual(requests.count(ORIGIN + '/spa.html?route=detail&b=2&a=1'), 1)
                    finally:
                        original.dispose()

    def test_canonical_same_url_snapshot_is_rendered_without_navigation(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                with self.open(engine, '/spa.html') as (page, requests):
                    self.assert_snapshot(page, 'spa-home')
                    page.get_by_role('button', name='Replace same URL', exact=True).click()
                    self.assert_snapshot(page, 'spa-same')
                    self.assertEqual(requests.count(ORIGIN + '/spa.html'), 1)


if __name__ == '__main__':
    unittest.main()
