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
