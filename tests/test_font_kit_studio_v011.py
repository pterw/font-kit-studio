import json
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parents[1] / 'font_kit_studio_v0.1.1.html'


class BrowserCase(unittest.TestCase):
    def setUp(self):
        self.runtime = sync_playwright().start()
        self.browsers = []

    def tearDown(self):
        for browser in self.browsers:
            browser.close()
        self.runtime.stop()

    def page(self, engine):
        browser = getattr(self.runtime, engine).launch()
        self.browsers.append(browser)
        page = browser.new_page(viewport={'width': 1600, 'height': 1200})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(HTML.as_uri())
        page.locator('#modeComposer').click()
        return page, errors

    def import_slots(self, page, slots):
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json',
            'buffer': json.dumps({'version': '0.1.1', 'composition': {'slots': slots}}).encode(),
        })
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        self.assertIn('Composition imported.', page.locator('#composerStatus').inner_text())

    def export(self, page):
        page.locator('#exportJson').click()
        result = json.loads(page.locator('#exportDialogText').input_value())
        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
        return result

    def row_geometry(self, page):
        # Wait for the inherited grid transition to finish before measuring tracks.
        page.wait_for_timeout(220)
        return page.locator('.row-layout').evaluate('''layout => {
            const rect = element => {
                const r = element.getBoundingClientRect();
                return {x:r.x, y:r.y, width:r.width, height:r.height, bottom:r.bottom};
            };
            return {layout:rect(layout), collapsed:layout.classList.contains('is-collapsed'),
                children:[...layout.children].map(rect),
                order:[...layout.children].map(child => child.dataset.rowChild),
                gap:parseFloat(getComputedStyle(layout).gap)};
        }''')

    def test_unequal_child_alignment_geometry(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                for alignment in ('start', 'center', 'end', 'stretch'):
                    with self.subTest(alignment=alignment):
                        self.import_slots(page, [{'type':'row', 'alignItems':alignment,
                            'children':[{'type':'spacer', 'spacerHeight':40},
                                        {'type':'spacer', 'spacerHeight':140}]}])
                        geometry = self.row_geometry(page)
                        short, tall = geometry['children']
                        self.assertFalse(geometry['collapsed'])
                        if alignment == 'stretch':
                            self.assertAlmostEqual(short['height'], tall['height'], delta=1)
                        else:
                            self.assertAlmostEqual(tall['height'] - short['height'], 100, delta=1)
                            offset = {'start':0, 'center':50, 'end':100}[alignment]
                            self.assertAlmostEqual(short['y'] - tall['y'], offset, delta=1)
                self.assertEqual(errors, [])

    def test_weighted_columns_gaps_and_resize_observer_boundaries(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.assertEqual(page.locator('#canvasWidth').input_value(), '960')
                for count in (2, 3, 4):
                    self.import_slots(page, [{'type':'row', 'childCount':count,
                        'ratios':list(range(1, count + 1)), 'gap':17, 'collapseAt':680,
                        'children':[{'type':'spacer', 'spacerHeight':20 + i * 10}
                                    for i in range(count)]}])
                    # Change only container width: no window resize or app render event.
                    # Responsive updates must therefore come from ResizeObserver.
                    for width in (681, 680, 679, 681):
                        page.locator('#composerCanvas').evaluate(
                            '''(canvas, width) => {
                                const parent = canvas.parentElement;
                                const style = getComputedStyle(parent);
                                const edges = ['paddingLeft', 'paddingRight', 'borderLeftWidth', 'borderRightWidth']
                                    .reduce((sum, key) => sum + parseFloat(style[key]), 0);
                                parent.style.width = `${width + edges}px`;
                            }''', width)
                        page.wait_for_function('''expected => {
                            const canvas = document.querySelector('#composerCanvas');
                            return Math.abs(canvas.getBoundingClientRect().width - expected.width) < .1
                                && canvas.querySelector('.row-layout').classList.contains('is-collapsed') === expected.collapsed;
                        }''', arg={'width':width, 'collapsed':width <= 680})
                        geometry = self.row_geometry(page)
                        children = geometry['children']
                        self.assertEqual(geometry['order'], [str(i) for i in range(count)])
                        self.assertAlmostEqual(geometry['gap'], 17, delta=.1)
                        if width <= 680:
                            for child in children:
                                self.assertAlmostEqual(child['width'], geometry['layout']['width'], delta=1)
                                self.assertAlmostEqual(child['x'], children[0]['x'], delta=1)
                            for previous, child in zip(children, children[1:]):
                                self.assertAlmostEqual(child['y'] - previous['bottom'], 17, delta=1)
                        else:
                            usable = geometry['layout']['width'] - 17 * (count - 1)
                            total = sum(range(1, count + 1))
                            for index, child in enumerate(children):
                                self.assertAlmostEqual(child['width'], usable * (index + 1) / total, delta=1)
                            for previous, child in zip(children, children[1:]):
                                self.assertAlmostEqual(child['x'] - previous['x'] - previous['width'], 17, delta=1)
                self.assertEqual(errors, [])

    def test_valid_row_factory_and_child_selection(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                page.locator('#compositionPreset').select_option('rowdemo')
                page.locator('#applyPreset').click()
                row = next(s for s in self.export(page)['composition']['slots'] if s['type'] == 'row')
                self.assertEqual(row['childCount'], 2)
                self.assertEqual(row['ratios'], [1, 2])
                self.assertEqual([s['type'] for s in row['children']], ['image', 'text'])
                page.locator('.row-child').nth(1).click()
                self.assertIn('CHILD 2/2', page.locator('#slotInspector').inner_text())
                self.assertEqual(page.locator('#slotInspector select[data-bind="type"] option[value="row"]').count(), 0)
                self.assertEqual(errors, [])

    def test_fractional_inspector_count_without_import(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type': 'row', 'childCount': 2}])
                control = page.locator('[data-bind="rowChildCount"]')
                control.fill('2.5')
                control.dispatch_event('change')
                row = self.export(page)['composition']['slots'][0]
                self.assertEqual(row['childCount'], 3)
                self.assertEqual(len(row['children']), 3)
                self.assertEqual(len(row['ratios']), 3)
                self.assertEqual(errors, [])

    def test_fractional_child_counts(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type': 'row', 'childCount': 2.5}])
                row = self.export(page)['composition']['slots'][0]
                self.assertEqual(row['childCount'], 3)
                self.assertEqual(len(row['children']), 3)
                control = page.locator('[data-bind="rowChildCount"]')
                control.fill('3.5')
                control.dispatch_event('change')
                row = self.export(page)['composition']['slots'][0]
                self.assertEqual(row['childCount'], 4)
                self.assertEqual(len(row['children']), len(row['ratios']))
                self.assertEqual(errors, [])

    def test_malformed_row_values_are_normalized(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type': 'row', 'childCount': 'Infinity', 'gap': -99,
                    'alignItems': 'invalid', 'collapseAt': 'bad', 'ratios': ['Infinity', -2]}])
                row = self.export(page)['composition']['slots'][0]
                self.assertEqual(row['childCount'], 2)
                self.assertEqual(row['gap'], 0)
                self.assertEqual(row['alignItems'], 'center')
                self.assertEqual(row['collapseAt'], 680)
                self.assertEqual(row['ratios'], [1, .25])
                self.assertEqual(errors, [])

    def test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                leaves = [
                    {'type': 'row', 'text': 'converted', 'children': [{'type': 'image', 'assetDataUrl': 'SECRET'}]},
                    {'type': 'text', 'text': 'retained', 'size': 31, 'variables': {'wght': 600}},
                    {'type': 'rule', 'ruleWidth': 65, 'ruleThickness': 3},
                    {'type': 'spacer', 'spacerHeight': 77},
                ]
                self.import_slots(page, [{'type': 'row', 'childCount': 4, 'children': leaves}])
                data = self.export(page)
                children = data['composition']['slots'][0]['children']
                self.assertEqual([s['type'] for s in children], ['text', 'text', 'rule', 'spacer'])
                self.assertNotIn('children', children[0])
                self.assertNotIn('SECRET', json.dumps(data))
                self.assertEqual(children[1]['variables'], {'wght': 600})
                self.assertEqual(children[1]['size'], 31)
                self.assertEqual(children[2]['ruleWidth'], 65)
                self.assertEqual(children[3]['spacerHeight'], 77)
                self.assertEqual(len({s['id'] for s in children}), 4)
                self.assertEqual(errors, [])


class StructureTests(unittest.TestCase):
    def test_version_and_existing_model(self):
        source = HTML.read_text(encoding='utf-8')
        self.assertTrue('<title>Font Kit Studio v0.1.1</title>' in source, 'Document title must match version 0.1.1')
        for symbol in ('makeRowSlot', 'findSlotById', 'selectedLocation', 'LEAF_SLOT_TYPES'):
            self.assertIn(symbol, source)


if __name__ == '__main__':
    unittest.main()
