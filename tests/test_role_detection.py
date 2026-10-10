"""Literal rendered detection, safe bindings and bounded cooperative work."""
import json

from support import ENGINES, REPO
from role_support import RoleBridgeCase, TARGET


class RoleDetectionTests(RoleBridgeCase):
    def test_valid_scan_becoming_unavailable_sends_null_and_no_partial_evidence(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                ready = self.hello(page)
                frame.evaluate("""() => addEventListener('message', function navigate(event) {
                    if (event.data.type !== 'design:detect') return;
                    removeEventListener('message', navigate);
                    setTimeout(() => history.replaceState(null, '', '/?' + 'z'.repeat(1999)), 0);
                })""")
                reply = self.detect(page)
                self.assertEqual(reply['type'], 'design:detected', reply)
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), reply)
                self.assertEqual(reply['pageURL'], ready['roleState']['pageURL'])
                self.assertIsNone(reply['currentPageURL'])
                self.assertEqual((reply['groups'], reply['selectorChecks']), ([], []))
                self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                self.assertGreater(reply['scannedElements'], 0)
                self.assertNotIn('z' * 1999, json.dumps(reply))
                self.assertEqual(frame.locator('.g00').first.evaluate('el => getComputedStyle(el).fontSize'), '20px')
                self.assertIsNone(self.hello(page, 'unavailable')['roleState']['pageURL'])
                self.assertEqual(self.detect(page)['reason'], 'unsupported-value')
                frame.evaluate("() => history.replaceState(null, '', '/fixtures/large-page/index.html?recovered#ok')")
                self.hello(page, 'recovered')
                self.assertTrue(self.detect(page)['complete'])
                self.assertEqual(frame.locator('[data-design-id="g19.249"]').inner_text(), 'Group 19 sample 249')

    def test_color4_zero_alpha_and_zero_height_clipping_have_no_eligible_text(self):
        for engine in ENGINES:
            for css in ('color:color(srgb 1 0 0 / 0)', 'height:0;overflow:hidden', 'height:0;overflow:hidden;border:2px solid'):
                with self.subTest(engine=engine, css=css):
                    page, frame = self.open(engine)
                    frame.evaluate("""css => {
                        const el = document.createElement('p'); el.id = 'excluded-probe';
                        el.textContent = 'Excluded probe'; el.style.cssText = css;
                        document.querySelector('main').appendChild(el);
                    }""", css)
                    self.hello(page)
                    if css.startswith('color'):
                        self.assertEqual(frame.locator('#excluded-probe').evaluate('el => getComputedStyle(el).color'), 'color(srgb 1 0 0 / 0)')
                    else:
                        self.assertEqual(frame.locator('#excluded-probe').evaluate('el => getComputedStyle(el).height'), '0px')
                        self.assertEqual(frame.locator('#excluded-probe').evaluate('el => el.clientHeight'), 0)
                    reply = self.detect(page)
                    self.assertTrue(reply['complete'], reply)
                    self.assertEqual(reply['scannedElements'], 2)
                    self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')
                    self.assertEqual(frame.locator('.body-copy').first.evaluate('el => getComputedStyle(el).fontSize'), '16px')

    def test_native_focus_style_and_eligibility_changes_invalidate_pending_measurement(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                frame.evaluate("""() => {
                    const style = document.createElement('style');
                    style.textContent = 'body:focus-within .g00 {font-size:35px} body:focus-within .g19 {visibility:hidden}';
                    document.head.appendChild(style);
                }""")
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                self.assertEqual(frame.locator('.g00').first.evaluate('el => getComputedStyle(el).fontSize'), '20px')
                start = self.mark(page)
                page.evaluate("() => { window.pendingDetect = request({type:'design:detect'}); }")
                field = frame.get_by_role('textbox', name='Responsiveness probe', exact=True)
                self.assertFalse(bool(self.messages(page, 'design:detected', start)), 'scan must be pending before native focus')
                field.focus()
                field.press_sequentially('x')
                self.assertEqual(field.input_value(), 'x')
                self.assertEqual(frame.locator('.g00').first.evaluate('el => getComputedStyle(el).fontSize'), '35px')
                self.assertFalse(frame.locator('.g19').first.is_visible())
                reply = page.evaluate('pendingDetect')
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), reply)
                self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                stable = self.detect(page)
                self.assertTrue(stable['complete'], stable)
                self.assertEqual(stable['scannedElements'], 4750)
                self.assertEqual(next(g for g in stable['groups'] if g['selectors'][0]['value'] == '.g00')
                                 ['signatures'][0]['style']['fontSize'], 35)

    def test_late_native_style_only_focus_invalidates_pending_measurement(self):
        self.check_late_native_focus('body:focus-within .g00 {font-size:35px}', 35, 5000)

    def test_late_native_eligibility_only_focus_invalidates_pending_measurement(self):
        self.check_late_native_focus('body:focus-within .g00 {visibility:hidden}', 20, 4750)

    def test_late_native_pointer_activation_invalidates_pending_measurement(self):
        self.check_late_native_focus('body:has(#responsiveness:active) .g00 {font-size:35px}', 35, 5000, 'pointerdown')

    def test_late_native_keyboard_activation_invalidates_pending_measurement(self):
        self.check_late_native_focus('body:has(#activation:active) .g00 {font-size:35px}', 35, 5000, 'keydown', 20)

    def test_late_native_hover_and_activation_release_invalidate_pending_measurement(self):
        self.check_late_native_focus('body:has(#responsiveness:hover) .g00 {font-size:35px}', 35, 5000, 'hover')
        self.check_late_native_focus('body:has(#responsiveness:active) .g00 {font-size:35px}', 20, 5000, 'pointerup')
        self.check_late_native_focus('body:has(#activation:active) .g00 {font-size:35px}', 20, 5000, 'keyup', 20)

    def check_late_native_focus(self, css, size, count, stimulus='focus', beats=16):
        for engine in ENGINES:
            with self.subTest(engine=engine, css=css):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                frame.evaluate("""css => {
                    const style = document.createElement('style'); style.textContent = css;
                    document.head.appendChild(style); window.probeTimes = {};
                    const button = document.createElement('button'); button.id = 'activation';
                    button.setAttribute('aria-label', 'Activation probe'); button.style.cssText = 'width:100px;height:32px';
                    document.body.insertBefore(button, document.body.firstChild);
                    addEventListener('message', event => {
                        if (event.data.type === 'design:detect') probeTimes.detect = performance.now();
                    }, true);
                    for (const el of document.querySelectorAll('#responsiveness,#activation')) {
                        for (const type of ['focus', 'pointerover', 'pointerdown', 'pointerup', 'keydown', 'keyup']) el.addEventListener(type, () => {
                            probeTimes.focus = performance.now();
                        });
                    }
                }""", css)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                field = frame.get_by_role('button', name='Activation probe', exact=True) if stimulus.startswith('key') else frame.get_by_role('textbox', name='Responsiveness probe', exact=True)
                if stimulus.startswith('pointer'):
                    field.hover(); field.focus()
                    if stimulus == 'pointerup':
                        page.mouse.down(); self.addCleanup(page.mouse.up)
                elif stimulus.startswith('key'):
                    field.focus()
                    if stimulus == 'keyup':
                        page.keyboard.down('Space'); self.addCleanup(page.keyboard.up, 'Space')
                hover_box = field.bounding_box() if stimulus == 'hover' else None
                before = frame.locator('main').evaluate('el => el.outerHTML')
                start = self.mark(page)
                page.evaluate("() => { window.pendingDetect = request({type:'design:detect'}); }")
                frame.evaluate("""beats => new Promise(resolve => {
                    const start = fixtureProbe.heartbeat;
                    function tick() {
                        if (fixtureProbe.heartbeat - start >= beats) resolve();
                        else requestAnimationFrame(tick);
                    }
                    requestAnimationFrame(tick);
                })""", beats)
                completed_before_native = bool(self.messages(page, 'design:detected', start))
                if stimulus == 'pointerdown':
                    page.mouse.down(); self.addCleanup(page.mouse.up)
                elif stimulus == 'pointerup':
                    page.mouse.up()
                elif stimulus == 'keydown':
                    page.keyboard.down('Space'); self.addCleanup(page.keyboard.up, 'Space')
                elif stimulus == 'keyup':
                    page.keyboard.up('Space')
                elif stimulus == 'hover':
                    page.mouse.move(hover_box['x'] + hover_box['width'] / 2, hover_box['y'] + hover_box['height'] / 2)
                else:
                    field.focus()
                reply = page.evaluate('pendingDetect')
                delay = frame.evaluate('probeTimes.focus - probeTimes.detect')
                rendered = frame.locator('.g00').first.evaluate('el => ({size:getComputedStyle(el).fontSize,visibility:getComputedStyle(el).visibility})')
                print('LATE_FOCUS ' + json.dumps({'css': css, 'stimulus': stimulus, 'completedBeforeNative': completed_before_native, 'focusDelayMs': delay,
                      'elapsedMs': reply['elapsedMs'], 'complete': reply['complete'], 'reason': reply['reason'],
                      'pageVersion': reply['pageVersion'], 'currentPageVersion': reply['currentPageVersion'],
                      'rendered': rendered}), flush=True)
                self.assertEqual(rendered, {'size': str(size) + 'px', 'visibility': 'visible' if count == 5000 else 'hidden'})
                self.assertEqual(frame.locator('.g00').first.text_content(), 'Outer prefix Nested sample outer suffix')
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(page.evaluate('revision'), 0)
                self.assertEqual(self.errors(frame), [])
                if reply['complete']:
                    old_size = 35 if stimulus in ('pointerup', 'keyup') else 20
                    group = next(g for g in reply['groups'] if g['selectors'][0]['value'] == '.g00')
                    self.assertEqual(group['signatures'], [{'style': {'fontFamily': 'serif', 'fontSize': old_size,
                                     'fontWeight': 400, 'textTransform': 'none', 'letterSpacing': 0}, 'count': 250}])
                    self.assertEqual(reply['scannedElements'], 5000)
                    self.assertFalse(not completed_before_native and delay < reply['elapsedMs'] - 30,
                                     'native change at least 30ms before completion cannot certify old rendering')
                else:
                    self.assertEqual(reply['reason'], 'page-changed', reply)
                    self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                stable = self.detect(page)
                self.assertTrue(stable['complete'], stable)
                self.assertEqual(stable['scannedElements'], count)
                if count == 5000:
                    group = next(g for g in stable['groups'] if g['selectors'][0]['value'] == '.g00')
                    self.assertEqual(group['signatures'][0]['style']['fontSize'], size)
                    self.assertEqual(group['elementCount'], 250)
                # A native transition after a completed scan must still advance the public epoch.
                if stimulus == 'focus':
                    field.blur()
                elif stimulus == 'hover':
                    page.mouse.move(0, 0)
                elif stimulus == 'pointerdown':
                    page.mouse.up()
                elif stimulus == 'pointerup':
                    page.mouse.down()
                elif stimulus == 'keydown':
                    page.keyboard.up('Space')
                else:
                    page.keyboard.down('Space')
                opposite_size = 35 if stimulus in ('pointerup', 'keyup') else 20
                self.assertEqual(frame.locator('.g00').first.evaluate('el => ({size:getComputedStyle(el).fontSize,visibility:getComputedStyle(el).visibility})'),
                                 {'size': str(opposite_size) + 'px', 'visibility': 'visible'})
                ready = self.hello(page, 'native-after-complete')
                self.assertGreater(ready['roleState']['pageVersion'], stable['currentPageVersion'])
                again = self.detect(page)
                self.assertTrue(again['complete'], again)
                self.assertEqual(again['scannedElements'], 5000)
                group = next(g for g in again['groups'] if g['selectors'][0]['value'] == '.g00')
                self.assertEqual(group['signatures'][0]['style']['fontSize'], opposite_size)
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(page.evaluate('revision'), 0)
                self.assertEqual(self.errors(frame), [])

    def test_escaped_author_bindings_hash_uncertainty_mixed_classes_and_reordering(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const main = document.querySelector('main');
                    function add(text, css, name = '', id = '', role = null) {
                        const el = document.createElement('span'); el.textContent = text;
                        el.style.cssText = css; el.className = name;
                        if (id) el.setAttribute('data-design-id', id);
                        if (role !== null) el.setAttribute('data-design-role', role);
                        main.appendChild(el); return el;
                    }
                    add('Escaped ID', 'font-size:17px', '', 'quoted"\\\\id');
                    add('Escaped role', 'font-size:18px', '', '', '  Text"\\\\role  ');
                    add('Hash one', 'font-size:19px', '_title_ab12c_1');
                    add('Hash two', 'font-size:19px', '_title_ab12c_1');
                    add('Broad one', 'font-size:20px', 'broad');
                    add('Broad two', 'font-size:21px', 'broad');
                    for (let i = 0; i < 40; i++) add('Unbound ' + i, 'font-size:22px', 'unique' + i);
                    add('Author duplicate name', 'font-size:23px', '', '', 'Text');
                    add('Quoted family', 'font-family:"Case Sensitive Family",serif;font-size:18.126px;letter-spacing:.333px;font-weight:399.5');
                }""")
                self.hello(page)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                reply = self.detect(page)
                self.assertTrue(reply['complete'], reply)
                by_text = {g['sampleText']: g for g in reply['groups']}
                escaped = by_text['Escaped ID']['selectors'][0]
                self.assertEqual(escaped['reason'], 'author-id')
                self.assertTrue(escaped['stable'])
                self.assertEqual(frame.locator(escaped['value']).inner_text(), 'Escaped ID')
                role = by_text['Escaped role']
                self.assertEqual(role['identity'], {'kind': 'author-role', 'name': 'Text"\\role'})
                self.assertEqual(frame.locator(role['selectors'][0]['value']).inner_text(), 'Escaped role')
                self.assertTrue(frame.locator('._title_ab12c_1').first.get_attribute('data-design-role'))
                self.assertEqual(by_text['Hash one']['authorRole'], None)
                self.assertEqual(by_text['Hash one']['identity']['kind'], 'style')
                self.assertEqual(by_text['Hash one']['selectors'], [
                    {'value': '._title_ab12c_1', 'stable': False, 'reason': 'css-module'}])
                for text in ('Broad one', 'Broad two'):
                    group = by_text[text]
                    self.assertTrue(group['bindingComplete'])
                    self.assertTrue(all(b['reason'] == 'dom-path' and not b['stable'] for b in group['selectors']))
                    self.assertEqual(frame.locator(group['selectors'][0]['value']).inner_text(), text)
                self.assertFalse(by_text['Unbound 0']['bindingComplete'])
                self.assertEqual(by_text['Unbound 0']['selectors'], [])
                self.assertEqual(by_text['Unbound 0']['elementCount'], 40)
                self.assertEqual(by_text['Quoted family']['identity'], {'kind': 'style', 'style': {
                    'fontFamily': '"Case Sensitive Family", serif', 'fontSize': 18.13, 'fontWeight': 400,
                    'textTransform': 'none', 'letterSpacing': 0.0184}})
                self.assertEqual(by_text['Author duplicate name']['suggestedName'], by_text['Ordinary body']['suggestedName'])
                self.assertNotEqual(by_text['Author duplicate name']['identity'], by_text['Ordinary body']['identity'])
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                reference = {json.dumps(g['identity'], sort_keys=True): g['elementCount'] for g in reply['groups']}
                frame.evaluate("""() => { const main = document.querySelector('main');
                    for (const child of Array.from(main.children).reverse()) main.appendChild(child); }""")
                reordered = self.detect(page)
                self.assertTrue(reordered['complete'], reordered)
                self.assertEqual({json.dumps(g['identity'], sort_keys=True): g['elementCount']
                                  for g in reordered['groups']}, reference)
                self.assertEqual(frame.get_by_text('Quoted family', exact=True).evaluate('el => getComputedStyle(el).fontSize'), '18.126px')

    def test_element_group_variant_identity_reply_and_time_limits_are_incomplete(self):
        for engine in ENGINES:
            for reason in ('element-limit', 'group-limit', 'variant-limit', 'identity-limit', 'reply-limit', 'time-budget'):
                with self.subTest(engine=engine, reason=reason):
                    page, frame = self.open(engine)
                    frame.evaluate("""reason => {
                        const main = document.querySelector('main');
                        if (reason === 'element-limit') {
                            main.replaceChildren();
                            const fragment = document.createDocumentFragment();
                            for (let i = 0; i < 10001; i++) {
                                const el = document.createElement('span'); el.className = 'limit-copy';
                                el.textContent = 'x '; fragment.appendChild(el);
                            }
                            main.appendChild(fragment);
                        }
                        if (reason === 'group-limit' || reason === 'variant-limit') {
                            main.replaceChildren();
                            for (let i = 0; i < (reason === 'group-limit' ? 129 : 9); i++) {
                                const el = document.createElement('p'); el.textContent = 'Limit ' + i;
                                el.style.fontSize = (10 + i) + 'px';
                                if (reason === 'variant-limit') el.setAttribute('data-design-role', 'Variants');
                                main.appendChild(el);
                            }
                        }
                        if (reason === 'identity-limit') main.firstElementChild.setAttribute('data-design-role', 'x'.repeat(201));
                        if (reason === 'time-budget') addEventListener('message', function busy(event) {
                            if (event.data.type !== 'design:detect') return;
                            removeEventListener('message', busy);
                            const until = performance.now() + 2100;
                            while (performance.now() < until) {} // Real app contention, no fake clock.
                        });
                    }""", reason)
                    self.hello(page)
                    before = frame.locator('main').evaluate('el => el.outerHTML')
                    roles = ([{'id': str(i).zfill(100), 'selectors': ['.body-copy'] * 32} for i in range(128)]
                             if reason == 'reply-limit' else [])
                    reply = self.detect(page, knownRoles=roles)
                    self.assertEqual((reply.get('complete'), reply.get('reason')), (False, reason), reply)
                    self.assertGreaterEqual(reply['scannedElements'], 0)
                    if reason == 'element-limit':
                        self.assertEqual(reply['scannedElements'], 10001)
                    elif reason == 'group-limit':
                        self.assertEqual(len(reply['groups']), 128)
                    elif reason == 'variant-limit':
                        self.assertEqual(len(reply['groups'][0]['signatures']), 8)
                    elif reason == 'reply-limit':
                        self.assertEqual(reply['selectorChecks'], [])
                    elif reason == 'time-budget':
                        self.assertGreater(reply['elapsedMs'], 2000)
                    self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                    self.assertTrue(frame.locator('main').inner_text())

    def test_latest_detect_hello_reset_and_dispose_suppress_old_jobs(self):
        for engine in ENGINES:
            for operation in ('detect', 'hello', 'reset', 'dispose'):
                with self.subTest(engine=engine, operation=operation):
                    page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                    self.hello(page)
                    start = self.mark(page)
                    if operation == 'dispose':
                        frame.evaluate("""() => addEventListener('message', function stop(event) {
                            if (event.data.type !== 'design:detect') return;
                            removeEventListener('message', stop); setTimeout(() => __fontkitBridge.dispose(), 0);
                        })""")
                    result = page.evaluate("""async operation => {
                        const old = request({type:'design:detect', requestId:'old'}, 250);
                        let barrier;
                        if (operation === 'detect') barrier = await request({type:'design:detect'});
                        if (operation === 'hello') barrier = await hello('s2');
                        if (operation === 'reset') barrier = await request({type:'design:reset'});
                        return {old:await old, barrier};
                    }""", operation)
                    self.assertEqual(result['old']['type'], 'timeout', result)
                    self.assertFalse([m for m in page.evaluate('log').copy()
                                      if m.get('data', {}).get('type') == 'design:detected'
                                      and m['data'].get('requestId') == 'old'])
                    self.assertEqual(frame.locator('[data-design-id="g19.249"]').inner_text(), 'Group 19 sample 249')
                    self.assertEqual(frame.locator('.g19').first.evaluate('el => getComputedStyle(el).fontSize'), '22px')
                    if operation != 'dispose':
                        self.assertTrue(self.detect(page)['complete'])
                        self.assertTrue(result['barrier']['type'].startswith('design:'))
                    else:
                        self.assertEqual(self.messages(page, 'design:detected', start), [])
                        self.assertTrue(frame.evaluate('__fontkitBridge.disposed'))

    def test_url_content_style_and_revision_changes_return_captured_stale_evidence(self):
        for engine in ENGINES:
            for action in ('url', 'content', 'style', 'revision'):
                with self.subTest(engine=engine, action=action):
                    page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                    self.hello(page)
                    captured = page.evaluate('roleState')
                    frame.evaluate("""action => {
                        addEventListener('message', function change(event) {
                            if (event.data.type !== 'design:detect') return;
                            removeEventListener('message', change);
                            setTimeout(() => {
                                if (action === 'url') history.pushState(null, '', '?route=B#section');
                                if (action === 'content') document.querySelector('.g00').textContent = 'Changed content';
                                if (action === 'style') {
                                    const sheet = document.styleSheets[0];
                                    sheet.insertRule('.g00 {font-size:31px}', sheet.cssRules.length);
                                }
                            }, 0);
                        });
                    }""", action)
                    if action == 'revision':
                        reply = page.evaluate("""async () => {
                            const detect = request({type:'design:detect'});
                            await request({type:'design:update', targetId:'g00.000', patch:{fontSize:32}});
                            return detect;
                        }""")
                    else:
                        reply = self.detect(page)
                    self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), reply)
                    self.assertEqual(reply['documentId'], captured['documentId'])
                    self.assertEqual(reply['pageURL'], captured['pageURL'])
                    self.assertGreater(reply['currentPageVersion'], reply['pageVersion'])
                    if action == 'url':
                        self.assertTrue(reply['currentPageURL'].endswith('?route=B#section'))
                        self.assertEqual(frame.locator('.g00').first.inner_text(), 'Outer prefix Nested sample outer suffix')
                    elif action == 'content':
                        self.assertEqual(frame.locator('.g00').first.inner_text(), 'Changed content')
                    else:
                        self.assertEqual(frame.locator('.g00').first.evaluate('el => getComputedStyle(el).fontSize'),
                                         '31px' if action == 'style' else '32px')
                    fresh = self.detect(page)
                    self.assertTrue(fresh['complete'], fresh)
                    self.assertEqual(fresh['pageURL'], reply['currentPageURL'])
                    self.assertEqual(fresh['pageVersion'], fresh['currentPageVersion'])

    def test_literal_bootstrap_identities_variants_and_counts_preserve_author_dom(self):
        for engine in ENGINES:
            for name in ('bootstrap4-static', 'bootstrap5-static'):
                with self.subTest(engine=engine, fixture=name):
                    oracle = json.loads((REPO / 'fixtures' / name / 'expected-styles.json').read_text(encoding='utf-8'))
                    page, frame = self.open(engine, target=TARGET + '/fixtures/' + name + '/index.html')
                    self.hello(page)
                    before = frame.locator('main').evaluate('el => el.outerHTML')
                    reply = self.detect(page)
                    self.assertTrue(reply['complete'], reply)
                    self.assertEqual(reply['scannedElements'], oracle['eligibleParentCount'])
                    actual = {json.dumps(g['identity'], sort_keys=True): g for g in reply['groups']}
                    self.assertEqual(len(actual), oracle['groupCount'])
                    for expected in oracle['groups']:
                        group = actual[json.dumps(expected['identity'], sort_keys=True)]
                        self.assertEqual(group['elementCount'], expected['elementCount'])
                        self.assertEqual(group['signatures'], [{'style': v['signature'], 'count': v['elementCount']}
                                                              for v in expected['variants']])
                        self.assertTrue(group['bindingComplete'], group)
                        matched = set()
                        for binding in group['selectors']:
                            matched.update(frame.locator(binding['value']).evaluate_all(
                                'els => els.map(el => el.getAttribute("data-design-id"))'))
                        expected_ids = set()
                        for binding in expected['bindings']:
                            expected_ids.update(frame.locator(binding['selector']).evaluate_all(
                                'els => els.map(el => el.getAttribute("data-design-id"))'))
                        self.assertEqual(matched, expected_ids)
                    self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                    self.assertEqual(frame.locator('.type-corpus .h1').evaluate('el => getComputedStyle(el).fontSize'), '40px')

    def test_near_duplicate_inclusive_boundaries_never_merge_or_transitively_collapse(self):
        oracle = json.loads((REPO / 'fixtures/large-page/expected-styles.json').read_text(encoding='utf-8'))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                self.hello(page)
                reply = self.detect(page)
                self.assertTrue(reply['complete'], reply)
                groups = {g['selectors'][0]['value'][1:]: g for g in reply['groups']}
                self.assertEqual(len(groups), 20)
                for case in oracle['thresholdCases']:
                    left, right = groups[case['left']], groups[case['right']]
                    self.assertEqual(right['id'] in left['nearDuplicateIds'], case['nearDuplicate'], case)
                    self.assertEqual(left['id'] in right['nearDuplicateIds'], case['nearDuplicate'], case)
                self.assertEqual(frame.locator('.g02').first.evaluate('el => getComputedStyle(el).letterSpacing'), '0.42px')
                self.assertEqual(frame.locator('.g03').first.evaluate('el => getComputedStyle(el).fontSize'), '21.01px')

    def test_first_complete_5000_scan_includes_bindings_and_allows_input_before_reply(self):
        oracle = json.loads((REPO / 'fixtures/large-page/expected-styles.json').read_text(encoding='utf-8'))
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=TARGET + '/fixtures/large-page/index.html')
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                field = frame.get_by_role('textbox', name='Responsiveness probe', exact=True)
                field.focus()
                before = frame.locator('main').evaluate('el => el.outerHTML')
                beat = frame.evaluate('fixtureProbe.heartbeat')
                start = self.mark(page)
                page.evaluate('() => { window.pendingDetect = request({type:"design:detect"}); }')
                field.press_sequentially('x')
                self.assertEqual(field.input_value(), 'x')
                observed = {'heartbeatBefore': beat, 'heartbeatDuring': frame.evaluate('fixtureProbe.heartbeat'),
                            'inputDuring': frame.evaluate('fixtureProbe.acknowledged'),
                            'replyAlreadyArrived': bool(self.messages(page, 'design:detected', start))}
                reply = page.evaluate('() => window.pendingDetect')
                print('FIRST_SCAN ' + json.dumps({**observed, 'elapsedMs': reply.get('elapsedMs'),
                      'complete': reply.get('complete'), 'scannedElements': reply.get('scannedElements')}), flush=True)
                self.assertFalse(observed['replyAlreadyArrived'], 'native input must render before completion')
                self.assertGreater(observed['heartbeatDuring'], beat)
                self.assertEqual(observed['inputDuring'], 'x')
                self.assertTrue(reply['complete'], reply)
                self.assertEqual(reply['scannedElements'], 5000)
                self.assertLessEqual(reply['elapsedMs'], 2000)
                actual = {json.dumps(g['identity'], sort_keys=True): g for g in reply['groups']}
                self.assertEqual(len(actual), 20)
                for expected in oracle['groups']:
                    group = actual[json.dumps(expected['identity'], sort_keys=True)]
                    self.assertEqual(group['elementCount'], 250)
                    self.assertEqual(group['signatures'], [{'style': expected['signature'], 'count': 250}])
                    self.assertEqual(group['selectors'], [{'value': '.' + expected['id'], 'stable': True, 'reason': 'class'}])
                    self.assertTrue(group['bindingComplete'])
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(frame.locator('[data-design-id="g19.249"]').inner_text(), 'Group 19 sample 249')
                self.assertEqual(frame.locator('[data-design-id="g19.249"]').evaluate('el => getComputedStyle(el).fontSize'), '22px')

    def test_safe_complete_bindings_and_known_selector_counts_keep_namespaces_distinct(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                self.hello(page)
                frame.locator('[data-design-id="ordinary.body"]').evaluate('el => el.classList.add("sm:text")')
                reply = self.detect(page, knownRoles=[{'id': 'known', 'selectors': [
                    '.body-copy', '.missing', r'.sm\:text', '[data-design-role="Body"]']}])
                self.assertTrue(reply['complete'], reply)
                author, automatic = reply['groups']
                self.assertEqual(author['identity'], {'kind': 'author-role', 'name': 'Body'})
                self.assertEqual(automatic['identity'], {'kind': 'style', 'style': automatic['signatures'][0]['style']})
                self.assertEqual(author['selectors'], [{'value': '[data-design-role="Body"]', 'stable': True, 'reason': 'author-role'}])
                self.assertEqual(automatic['selectors'], [{'value': '[data-design-id="ordinary.body"]', 'stable': True, 'reason': 'author-id'}])
                self.assertTrue(all(g['bindingComplete'] for g in reply['groups']))
                self.assertEqual([c['matchCount'] for c in reply['selectorChecks']], [2, 0, 1, 1])
                self.assertEqual(reply['selectorChecks'][0]['signatures'], [{'style': {
                    'fontFamily': 'sans-serif', 'fontSize': 16, 'fontWeight': 400,
                    'textTransform': 'none', 'letterSpacing': 0}, 'count': 2}])
                for group in reply['groups']:
                    for binding in group['selectors']:
                        self.assertEqual(frame.locator(binding['value']).inner_text(),
                                         'Author body' if group['authorRole'] else 'Ordinary body')
                        self.assertEqual(frame.locator(binding['value']).evaluate('el => getComputedStyle(el).fontSize'), '16px')

    def test_direct_text_population_visibility_and_nested_dedup(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => {
                    const main = document.querySelector('main');
                    function add(tag, id, text, parent = main, css = '') {
                        const el = document.createElement(tag); el.id = id;
                        el.textContent = text; el.style.cssText = css; parent.appendChild(el); return el;
                    }
                    const outer = add('div', 'outer', 'Prefix ');
                    add('span', 'inner', 'Nested', outer); outer.appendChild(document.createTextNode(' suffix'));
                    add('p', 'contents', 'Contents', main, 'display:contents');
                    add('p', 'below', 'Below viewport', main, 'margin-top:2000px');
                    add('p', 'hidden', 'Hidden', main, 'display:none');
                    add('p', 'invisible', 'Invisible', main, 'visibility:hidden');
                    add('p', 'collapse', 'Collapsed', main, 'visibility:collapse');
                    const hiddenParent = add('div', 'hidden-parent', '', main, 'visibility:hidden');
                    add('span', 'visible-child', 'Visible child', hiddenParent, 'visibility:visible');
                    const transparent = add('div', 'transparent', '', main, 'opacity:0');
                    add('p', 'transparent-child', 'Transparent child', transparent);
                    add('p', 'transparent-color', 'Transparent color', main, 'color:rgba(0,0,0,0)');
                    add('p', 'zero', 'Zero area', main, 'font-size:0;line-height:0');
                    add('p', 'fontkit-bridge-overlay', 'Overlay');
                    const asset = add('p', 'asset', 'Asset'); asset.className = 'fontkit-placed-asset';
                    add('textarea', 'value', 'Form value'); add('option', 'option', 'Option value');
                    const input = add('input', 'placeholder', ''); input.value = 'Value'; input.placeholder = 'Placeholder';
                    const nested = add('iframe', 'nested-frame', ''); nested.srcdoc = '<p>Nested frame text</p>';
                    const pseudo = add('style', 'pseudo-style', '#outer::before {content:"Generated text"}');
                    pseudo.setAttribute('data-author-css', 'true');
                    add('script', 'script', '/* script text */'); add('style', 'style', '/* style text */');
                    add('template', 'template', 'Template'); add('noscript', 'noscript', 'Noscript');
                    const shadow = add('div', 'shadow', '').attachShadow({mode:'open'});
                    add('p', 'shadow-text', 'Shadow', shadow);
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    const text = document.createElementNS(svg.namespaceURI, 'text');
                    text.textContent = 'SVG'; svg.appendChild(text); main.appendChild(svg);
                }""")
                self.hello(page)
                self.assertEqual(frame.locator('#inner').inner_text(), 'Nested')
                self.assertFalse(frame.locator('#hidden').is_visible())
                self.assertTrue(frame.locator('#visible-child').is_visible())
                self.assertGreater(frame.locator('#below').bounding_box()['y'], 900)
                before = frame.locator('main').evaluate('el => el.outerHTML')
                reply = self.detect(page)
                self.assertTrue(reply['complete'], reply)
                self.assertEqual(reply['scannedElements'], 7)
                self.assertEqual(sum(g['elementCount'] for g in reply['groups']), 7)
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
