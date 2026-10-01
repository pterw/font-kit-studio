import json
import re
import struct
import unittest
import zlib
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
        status = self.import_document(page, {'version': '0.1.1', 'composition': {'slots': slots}})
        self.assertIn('Composition imported.', status)

    def import_document(self, page, data):
        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
        page.locator('#importJsonFile').set_input_files({
            'name': 'composition.json', 'mimeType': 'application/json',
            'buffer': json.dumps(data).encode(),
        })
        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
        return page.locator('#composerStatus').inner_text()

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

    def test_task4_failed_import_is_transactional(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                before = self.export(page)
                before_canvas = page.locator('#composerCanvas').inner_html()
                for malformed in ([None], [42], [[]], [{'type':'row', 'children':{}}],
                                  [{'type':'row', 'children':[{'type':'text'}, None]}]):
                    status = self.import_document(page, {'composition': {'canvasWidth':'640',
                        'background':{'source':'custom', 'hex':'#ffffff'}, 'slots':malformed}})
                    self.assertTrue(status.startswith('Import failed:'), status)
                    self.assertIn('slot', status.lower())
                    self.assertEqual(self.export(page), before)
                    self.assertEqual(page.locator('#composerCanvas').inner_html(), before_canvas)
                # A malformed background previously throws after live state assignments.
                status = self.import_document(page, {'composition': {'canvasWidth':'640',
                    'background':42, 'slots':[{'type':'text', 'text':'replacement'}]}})
                self.assertTrue(status.startswith('Import failed:'), status)
                self.assertEqual(self.export(page), before)
                self.assertEqual(errors, [])

    def test_task4_css_roles_are_valid_and_collision_free(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
                    {'type':'text', 'role':12}, {'type':'text', 'role':'Body'},
                    {'type':'text', 'role':'Body'}, {'type':'text', 'role':'Body-2'}]},
                    {'type':'text', 'role':'Body-size'}])
                page.locator('#exportCss').click()
                self.assertEqual(errors, [], 'CSS export must not throw for accepted roles')
                self.assertTrue(page.locator('#exportDialog').evaluate('dialog => dialog.open'))
                css = page.locator('#exportDialogText').input_value()
                declarations = re.findall(r'^\s*(--[a-z0-9-]+):', css, re.M)
                self.assertEqual(len(declarations), len(set(declarations)), css)
                families = re.findall(r'^\s*--font-[a-z0-9-]+: [^;]*,', css, re.M)
                self.assertEqual(len(families), 5, css)
                self.assertIn('--row-1-columns:', css)

    def test_task4_failed_background_import_preserves_state(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                before = self.export(page)
                status = self.import_document(page, {'composition': {'canvasWidth':'640',
                    'background':42, 'slots':[{'type':'text', 'text':'replacement'}]}})
                self.assertTrue(status.startswith('Import failed:'), status)
                self.assertEqual(self.export(page), before)
                self.assertEqual(errors, [])

    def test_task4_css_slug_and_property_suffix_collisions(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
                    {'type':'text', 'role':role} for role in ('Body','Body','Body-2','Body-size')]}])
                page.locator('#exportCss').click()
                css = page.locator('#exportDialogText').input_value()
                declarations = re.findall(r'^\s*(--[a-z0-9-]+):', css, re.M)
                self.assertEqual(len(declarations),len(set(declarations)),css)
                self.assertEqual(errors, [])

    def test_task4_known_leaf_fields_have_safe_shapes(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'children':[
                    {'type':'text', 'role':'__proto__'},
                    {'type':'text', 'role':{}, 'size':'bad', 'variables':[{'wght':500}],
                     'text':{}, 'fontStyle':'italic; --bad: red', 'element':'script'}]}])
                for child in self.export(page)['composition']['slots'][0]['children']:
                    self.assertIsInstance(child['role'], str)
                    self.assertIsInstance(child['text'], str)
                    self.assertIsInstance(child['size'], (int,float))
                    self.assertIsInstance(child['variables'],dict)
                    self.assertIn(child['fontStyle'], ('normal','italic','oblique'))
                    self.assertNotEqual(child['element'],'script')
                page.locator('#exportCss').click()
                self.assertNotIn('--bad:',page.locator('#exportDialogText').input_value())
                self.assertEqual(errors, [])

    def test_task4_recursive_asset_privacy_and_old_json_round_trip(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                old = {'version':'0.1.0', 'composition': {'slots':[
                    {'type':'text', 'role':'Body', 'text':'legacy', 'size':31},
                    {'type':'image', 'imageName':'logo.svg', 'imageWidth':123, 'assetDataUrl':'SECRET',
                     'metadata':{'owner':'retained', 'nested':[{'assetDataUrl':'HIDDEN'}]}}]}}
                self.assertIn('Composition imported.', self.import_document(page, old))
                exported = self.export(page)
                self.assertEqual(exported['version'], '0.1.1')
                self.assertEqual(exported['composition']['slots'][0]['text'], 'legacy')
                self.assertEqual(exported['composition']['slots'][0]['size'], 31)
                image = exported['composition']['slots'][1]
                self.assertEqual((image['imageName'], image['imageWidth']), ('logo.svg',123))
                self.assertEqual(image['metadata']['owner'], 'retained')
                self.assertNotIn('SECRET', json.dumps(exported))
                self.assertNotIn('HIDDEN', json.dumps(exported))
                self.import_slots(page, [{'type':'row', 'gap':33, 'ratios':[2,3], 'children':[
                    {'type':'image', 'imageName':'nested.png', 'assetDataUrl':'NESTED',
                     'extra':{'assetDataUrl':'DEEP'}}, {'type':'text', 'role':'Accent', 'text':'inside'}]}])
                first = self.export(page)
                self.assertNotIn('NESTED', json.dumps(first))
                self.assertNotIn('DEEP', json.dumps(first))
                self.assertIn('Composition imported.', self.import_document(page, first))
                second = self.export(page)
                def without_ids(value):
                    if isinstance(value, dict):
                        return {k:without_ids(v) for k,v in value.items() if k not in ('id','selectedId')}
                    if isinstance(value, list):
                        return [without_ids(v) for v in value]
                    return value
                self.assertEqual(without_ids(first), without_ids(second))
                self.assertEqual(errors, [])

    def test_task4_image_upload_decode_rejection_and_selection_race(self):
        def chunk(kind, data):
            return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR',struct.pack('!2I5B',1,1,8,6,0,0,0))
               + chunk(b'IDAT',zlib.compress(b'\x00\xff\x00\x00\xff')) + chunk(b'IEND',b''))
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="3" height="2"><rect width="3" height="2" fill="red"/></svg>'
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'children':[{'type':'image'}, {'type':'text', 'text':'safe'}]}])
                page.locator('.row-child').first.click()
                for name, mime, buffer, dimensions in (
                    ('pixel.png','image/png',png,(1,1)), ('logo.svg','image/svg+xml',svg,(3,2))):
                    page.locator('#assetFile').set_input_files({'name':name,'mimeType':mime,'buffer':buffer})
                    page.wait_for_function('''name => document.querySelector('#composerStatus').textContent.includes(`${name} loaded`)''', arg=name)
                    image = page.locator('.row-child img')
                    image.evaluate('image => image.decode()')
                    self.assertEqual(image.evaluate('image => [image.naturalWidth,image.naturalHeight]'), list(dimensions))
                    data = self.export(page)['composition']['slots'][0]['children'][0]
                    self.assertEqual(data['imageName'], name)
                    self.assertEqual(data['assetDataUrl'], '')
                page.locator('#assetFile').set_input_files({'name':'photo.jpg','mimeType':'image/jpeg','buffer':png})
                self.assertIn('Asset rejected:', page.locator('#composerStatus').inner_text())
                self.assertEqual(page.locator('.row-child img').get_attribute('alt'), 'logo.svg')
                # Hold an actual FileReader until selection changes, then release it.
                page.evaluate('''() => { const NativeReader = FileReader;
                    window.FileReader = class extends NativeReader {
                        readAsDataURL(file) { document.addEventListener('test-release-asset-read',
                            () => super.readAsDataURL(file), {once:true}); }
                    }; }''')
                page.locator('#assetFile').set_input_files({'name':'delayed.png','mimeType':'image/png','buffer':png})
                page.locator('.row-child').nth(1).click()
                page.evaluate("document.dispatchEvent(new Event('test-release-asset-read'))")
                page.wait_for_function("document.querySelector('#composerStatus').textContent.includes('delayed.png loaded')")
                children = self.export(page)['composition']['slots'][0]['children']
                self.assertEqual(children[0]['imageName'], 'delayed.png')
                self.assertNotIn('imageName', children[1])
                self.assertEqual(children[1]['text'], 'safe')
                page.locator('.row-child img').evaluate('image => image.decode()')
                self.assertEqual(errors, [])

    def test_row_inspector_normalized_values_and_labels(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'gap':99999, 'collapseAt':99999,
                    'ratios':[99999, -99999]}])
                row = self.export(page)['composition']['slots'][0]
                self.assertEqual((row['gap'], row['collapseAt'], row['ratios']), (96, 1600, [12, .25]))
                for selector, event, cases, key in (
                    ('[data-bind="rowChildCount"]', 'change', [('1',2), ('5',4), ('2.5',3), ('',2)], 'childCount'),
                    ('[data-bind="rowCollapseAt"]', 'input', [('99999',1600), ('1',240), ('',680)], 'collapseAt'),
                    ('[data-row-ratio="0"]', 'input', [('99999',12), ('0',.25), ('',1)], 'ratios'),
                ):
                    for value, expected in cases:
                        control = page.locator(selector)
                        control.fill(value)
                        control.dispatch_event(event)
                        control.dispatch_event("change")
                        row = self.export(page)['composition']['slots'][0]
                        actual = row[key][0] if key == 'ratios' else row[key]
                        self.assertEqual(actual, expected)
                        self.assertEqual(page.locator(selector).input_value(), str(expected))
                breakpoint = page.locator('[data-bind="rowCollapseAt"]')
                breakpoint.fill('')
                breakpoint.press_sequentially('680')
                self.assertEqual(breakpoint.input_value(), '680')
                breakpoint.press('Tab')
                self.assertEqual(breakpoint.input_value(), '680')
                weight = page.locator('[data-row-ratio="0"]')
                weight.fill('')
                weight.press_sequentially('2.5')
                weight.press('Tab')
                self.assertEqual(weight.input_value(), '2.5')
                for selector in ('[data-bind="rowChildCount"]', '[data-bind="rowGap"]',
                                 '[data-bind="rowAlignItems"]', '[data-bind="rowCollapseAt"]', '[data-row-ratio="0"]'):
                    self.assertTrue(page.locator(selector).evaluate('el => el.labels.length > 0'))
                self.assertEqual(errors, [])

    def test_row_controls_and_leaf_inspectors(self):
        for engine in ('chromium', 'firefox'):
            with self.subTest(engine=engine):
                page, errors = self.page(engine)
                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
                    {'type':'text', 'text':'before'}, {'type':'image'}, {'type':'rule'}, {'type':'spacer'}]},
                    {'type':'text', 'text':'outside'}])
                for alignment in ('start','center','end','stretch'):
                    page.locator('[data-bind="rowAlignItems"]').select_option(alignment)
                    self.assertEqual(self.export(page)['composition']['slots'][0]['alignItems'], alignment)
                    self.assertEqual(page.locator('.row-layout').evaluate('el => getComputedStyle(el).alignItems'), alignment)
                gap = page.locator('[data-bind="rowGap"]')
                gap.fill('37')
                gap.dispatch_event('input')
                self.assertEqual(self.export(page)['composition']['slots'][0]['gap'], 37)
                self.assertAlmostEqual(self.row_geometry(page)['gap'],37,delta=.1)
                for index, selector, value, key, expected in (
                    (0,'[data-bind="text"]','edited','text','edited'),
                    (1,'[data-bind="imageWidth"]','123','imageWidth',123),
                    (2,'[data-bind="ruleThickness"]','7','ruleThickness',7),
                    (3,'[data-bind="spacerHeight"]','88','spacerHeight',88),
                ):
                    page.locator('.row-child-jump').nth(index).click()
                    self.assertIn(f'ROW 1 · CHILD {index+1}/4',page.locator('.inspector-index').inner_text())
                    self.assertEqual(page.locator('[data-bind="type"] option[value="row"]').count(),0)
                    self.assertEqual(page.locator('.row-child .slot-movers').count(),0)
                    control=page.locator(selector)
                    control.fill(value)
                    control.dispatch_event('input')
                    self.assertEqual(self.export(page)['composition']['slots'][0]['children'][index][key], expected)
                    page.locator('#composerCanvas > .flow-slot').first.click(position={'x':3,'y':3})
                page.locator('#composerCanvas > .flow-slot').first.locator('.slot-movers button').nth(1).click()
                slots=self.export(page)['composition']['slots']
                self.assertEqual([s['type'] for s in slots], ['text','row'])
                self.assertEqual(slots[1]['children'][0]['text'],'edited')
                self.assertEqual(errors, [])

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
