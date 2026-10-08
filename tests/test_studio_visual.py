"""Visual quick wins and current version labels (v0.2.1 Task 8).

Every test asserts what the person sees: computed style, geometry, contrast ratios computed from
computed colours, and text. Nothing asserts that a rule exists in the stylesheet.

Two groups:
  * Studio-only tests (StudioCase): Studio on http://studio.test, nothing connected.
  * Real-bridge tests (LiveAppCase): the real scripts/serve.py, Studio and the real demo over
    `postMessage` across two origins, at 1440 x 900.
"""

import re
import unittest

from support import ENGINES, HTML
from test_live_integration import LiveIntegrationCase
from test_studio_live import APP, FAKE, LiveCase

# Computed colours reach the page as rgb(), rgba() or color(srgb ...) (colour-mix), so the
# helpers read both. Every ratio is WCAG 2.x relative luminance.
COLOUR_JS = r"""
const parse = (css) => {
  let m = css.match(/^rgba?\(([^)]+)\)$/);
  if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
  m = css.match(/^color\(srgb ([^)]+)\)$/);
  if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
  throw new Error('unparsed colour ' + css);
};
const over = (fg, bg) => [0, 1, 2].map(i => fg[i] * fg[3] + bg[i] * (1 - fg[3])).concat([1]);
const backdrop = (el) => {
  const chain = [];
  for (let node = el; node; node = node.parentElement) chain.push(node);
  let bg = [255, 255, 255, 1];
  for (const node of chain.reverse()) bg = over(parse(getComputedStyle(node).backgroundColor), bg);
  return bg;
};
const lum = ([r, g, b]) => {
  const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
};
const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
const opacityOf = (el) => { let o = 1; for (let n = el; n; n = n.parentElement) o *= Number(getComputedStyle(n).opacity); return o; };
const label = (el) => el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '');
"""

FIELDS = 'input[type="text"], input[type="number"], select, textarea'
EMOJI = re.compile('[\U0001F000-\U0001FFFF⚡️]')
# The names the user's page must not go by, in any visible text, title, label or placeholder.
OLD_NAMES = re.compile(r'target app\b|live target\b|target application', re.I)
# The user's page called "the target" (the editable-element sense, "All targets" or "pick a target", is a different word).
PAGE_AS_TARGET = re.compile(r"\bthe target\b|\btarget (page|URL)s?\b", re.I)
SCALE = (28, 34)   # the control-height scale: compact and standard, in px


def evaluate(page, expression, arg=None):
    return page.evaluate('(arg) => {' + COLOUR_JS + expression + '}', arg)


def visible_names(page):
    """Every visible text, title, aria-label and placeholder in the open mode."""
    return evaluate(page, r"""
      const found = [];
      document.querySelectorAll('body *').forEach((el) => {
        if (el.getClientRects().length === 0 || getComputedStyle(el).visibility === 'hidden') return;
        ['title', 'aria-label', 'placeholder'].forEach((name) => { const v = el.getAttribute(name); if (v) found.push(v); });
        if (el.childElementCount === 0 && el.textContent.trim()) found.push(el.textContent.trim());
      });
      return found;""")


class StudioCase(LiveCase):
    def studio(self, engine, viewport=None, dark=False, mode='composer'):
        """Studio alone on studio.test. `dark` switches the theme from the Library, as a person would."""
        context = self.context(engine, viewport=viewport)
        page = context.new_page()
        page.errors = []
        page.on('pageerror', lambda error: page.errors.append(str(error)))
        page.goto(APP)
        if dark:
            page.locator('#themeToggle').click()
        if mode == 'composer':
            page.locator('#modeComposer').click()
        return page

    def select_slot(self, page, index=0):
        page.locator('#composerCanvas > .flow-slot').nth(index).click(position={'x': 3, 'y': 3})
        page.wait_for_selector('#slotInspector [data-bind]')


class LiveAppCase(LiveIntegrationCase):
    def live(self, engine, viewport=None):
        return self.connected(engine, viewport=viewport)

    def select_title(self, page):
        self.select_hero_title(page)

    def names_in_view(self, page):
        return visible_names(page)


def control_heights(page, scope):
    """The height of every visible button, text field, number field and select inside `scope`.

    The Studio/Library mode tabs are page-level navigation, not form controls, so they are left out."""
    return evaluate(page, r"""
      const out = [];
      document.querySelectorAll(arg + ' button, ' + arg + ' input, ' + arg + ' select').forEach((el) => {
        if (el.matches('.mode-tab, input[type="checkbox"], input[type="range"], input[type="file"], input[type="color"], [hidden]')) return;
        const box = el.getBoundingClientRect();
        if (!box.width || !box.height || getComputedStyle(el).visibility === 'hidden') return;
        out.push([label(el), Math.round(box.height * 10) / 10]);
      });
      return out;""", scope)


def tab_stops(page, container, limit=40):
    """Press Tab from the control before `container` and record the ring on every stop inside it."""
    stops = []
    for _ in range(limit):
        page.keyboard.press('Tab')
        stop = evaluate(page, r"""
          const el = document.activeElement;
          if (!el || !el.closest(arg)) return null;
          const style = getComputedStyle(el);
          const ring = parse(style.outlineColor);
          return { name: label(el), keyboard: el.matches(':focus-visible'), style: style.outlineStyle,
                   width: parseFloat(style.outlineWidth), offset: parseFloat(style.outlineOffset),
                   // The ring sits outside the control, so what it is seen against is the panel around it.
                   ratio: ratio(over(ring, backdrop(el.parentElement)), backdrop(el.parentElement)) };""", container)
        if stop is None:
            break
        stops.append(stop)
    return stops


class PrimaryActionTests(StudioCase):
    def test_each_panel_has_one_primary_action_and_it_looks_primary(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                panels = {'#targetAppBridgeBar': '#btnConnectTarget', '.composer-actions': '#btnSyncToApp'}
                for panel, primary in panels.items():
                    found = page.locator(f'{panel} .btn.primary').evaluate_all('els => els.map(el => "#" + el.id)')
                    self.assertEqual(found, [primary], panel)
                looks = evaluate(page, r"""
                  const plain = document.querySelector('#exportJson'), primary = document.querySelector('#btnSyncToApp');
                  const p = getComputedStyle(primary), q = getComputedStyle(plain);
                  return { bg: p.backgroundColor, plainBg: q.backgroundColor, weight: Number(p.fontWeight),
                           text: ratio(parse(p.color), backdrop(primary)), plainWeight: Number(q.fontWeight) };""")
                self.assertNotEqual(looks['bg'], looks['plainBg'], 'the primary button has its own fill')
                self.assertGreaterEqual(looks['text'], 4.5, 'its label stays readable on that fill')
                page.locator('#modeLibrary').click()
                library = page.locator('.controls .btn.primary').evaluate_all('els => els.map(el => "#" + el.id)')
                self.assertEqual(library, ['#loadFreeFontsLibrary'])
                dark = self.studio(engine, dark=True)
                text = evaluate(dark, r"""
                  const el = document.querySelector('#btnSyncToApp');
                  return ratio(parse(getComputedStyle(el).color), backdrop(el));""")
                self.assertGreaterEqual(text, 4.5, 'the primary label stays readable in dark mode')


class ControlScaleTests(StudioCase):
    def assert_scale(self, heights, where):
        self.assertGreater(len(heights), 4, f'{where}: the scan found its controls')
        off = [(name, height) for name, height in heights if not any(abs(height - step) <= 0.6 for step in SCALE)]
        self.assertEqual(off, [], f'{where}: every control is {SCALE[0]} or {SCALE[1]} px tall')

    def test_library_and_composer_controls_share_one_height_scale(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine, mode='library')
                self.assert_scale(control_heights(page, '#libraryView'), 'Library')
                page.locator('#modeComposer').click()
                self.assert_scale(control_heights(page, '.composer-toolbar'), 'Composer toolbar')
                self.select_slot(page)
                self.assert_scale(control_heights(page, '#slotInspector'), 'slot inspector')
                self.assert_scale(control_heights(page, '#composerCanvas'), 'canvas movers')

    def test_selects_and_textareas_use_the_page_font_like_every_other_field(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                self.select_slot(page)
                fonts = evaluate(page, r"""
                  const pick = (el) => { const s = getComputedStyle(el); return [s.fontFamily, s.fontSize]; };
                  return { text: pick(document.querySelector('#canvasBgHex')), select: pick(document.querySelector('#kitPreset')),
                           textarea: pick(document.querySelector('#slotInspector textarea')),
                           inspectorSelect: pick(document.querySelector('#slotInspector select')) };""")
                self.assertEqual(fonts['select'], fonts['text'])
                self.assertEqual(fonts['textarea'], fonts['text'])
                self.assertEqual(fonts['inspectorSelect'], fonts['text'])
                self.assertNotIn('Arial', fonts['select'][0])


class LiveAppControlScaleTests(LiveAppCase):
    def test_live_app_controls_share_the_scale(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                bar = control_heights(page, '#targetAppBridgeBar')
                self.assertEqual([item for item in bar if not any(abs(item[1] - s) <= 0.6 for s in SCALE)], [], 'bridge bar')
                self.select_title(page)
                for scope in ('#slotInspector', '.live-code-panel'):
                    heights = control_heights(page, scope)
                    self.assertGreater(len(heights), 5, scope)
                    self.assertEqual([item for item in heights if not any(abs(item[1] - s) <= 0.6 for s in SCALE)], [], scope)


class LiveAppViewTests(LiveAppCase):
    def test_the_live_page_starts_in_the_top_half_of_a_900px_window(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                top = page.locator('#targetAppContainer').evaluate('el => el.getBoundingClientRect().top + window.scrollY')
                self.assertLess(top, 450, 'the live page starts in the top half of a 900 px window')
                self.assertTrue(page.locator('#targetAppContainer').is_visible())

    def test_composition_only_fields_hide_in_the_live_app_view_and_return_in_specimen(self):
        only_composition = ['#slotCount', '#canvasWidth', '#canvasBgSource', '#canvasBgHex']
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                for selector in only_composition:
                    self.assertFalse(page.locator(selector).is_visible(), f'{selector} is hidden in the Live App view')
                for selector in ('#targetAppUrl', '#btnSyncToApp', '#exportJson'):
                    self.assertTrue(page.locator(selector).is_visible(), f'{selector} stays')
                header = page.locator('header').bounding_box()
                self.assertLess(header['height'], 120, 'the header is compact in the Live App view')
                page.locator('#viewSpecimenCanvas').click()
                for selector in only_composition:
                    self.assertTrue(page.locator(selector).is_visible(), f'{selector} returns in Specimen')
                self.assertGreater(page.locator('header').bounding_box()['height'], 200, 'the full header returns')
                page.locator('#modeLibrary').click()
                self.assertGreater(page.locator('header').bounding_box()['height'], 200, 'the Library keeps the full header')

    def test_the_inspector_is_a_300px_column_that_stays_beside_the_preview_down_to_900px(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                geometry = '''() => { const i = document.querySelector('#slotInspector').getBoundingClientRect(),
                  s = document.querySelector('.canvas-stage').getBoundingClientRect();
                  return { width: Math.round(i.width), beside: i.left >= s.right - 1 }; }'''
                self.assertEqual(page.evaluate(geometry), {'width': 300, 'beside': True})
                for width, beside in ((1000, True), (901, True), (880, False)):
                    page.set_viewport_size({'width': width, 'height': 900})
                    page.wait_for_function(f'() => window.innerWidth === {width}')
                    self.assertEqual(page.evaluate(geometry)['beside'], beside, f'{width}px')

    def test_a_long_inspector_is_bounded_and_scrolls(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                self.select_title(page)
                info = page.evaluate('''() => { const el = document.querySelector('#slotInspector');
                  return { height: el.getBoundingClientRect().height, scrolls: getComputedStyle(el).overflowY,
                           overflow: el.scrollHeight > el.clientHeight, window: innerHeight }; }''')
                self.assertIn(info['scrolls'], ('auto', 'scroll'))
                self.assertLessEqual(info['height'], info['window'] - 60, 'the inspector fits the window')
                self.assertTrue(info['overflow'], 'the Arrange controls are long enough to need the scroll')

    def test_the_target_list_is_bounded_and_grouped(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                info = page.evaluate('''() => { const list = document.querySelector('.live-target-list');
                  const groups = [...list.querySelectorAll('.live-target-group')].map(group => ({
                    title: group.querySelector('h3').textContent.trim(), count: group.querySelectorAll('[data-live-target]').length }));
                  return { height: list.getBoundingClientRect().height, overflow: getComputedStyle(list).overflowY,
                           scrolls: list.scrollHeight > list.clientHeight, groups,
                           total: list.querySelectorAll('[data-live-target]').length }; }''')
                self.assertLessEqual(info['height'], 440)
                self.assertIn(info['overflow'], ('auto', 'scroll'))
                self.assertTrue(info['scrolls'], 'the demo has more targets than fit')
                self.assertEqual([g['title'] for g in info['groups']],
                                 ['Marked with data-design-id', 'Auto-discovered'])
                self.assertEqual([g['count'] for g in info['groups']], [12, info['total'] - 12])
                self.assertGreater(info['total'], 30)


def assert_rings(test, stops, where, minimum):
    test.assertGreaterEqual(len(stops), minimum, f'{where}: tabbed through its controls')
    for stop in stops:
        test.assertTrue(stop['keyboard'], f"{where}: {stop['name']} is a keyboard stop")
        test.assertNotEqual(stop['style'], 'none', f"{where}: {stop['name']} shows a ring")
        test.assertGreaterEqual(stop['width'], 2, f"{where}: {stop['name']} ring is at least 2px")
        test.assertGreaterEqual(stop['ratio'], 3, f"{where}: {stop['name']} ring contrast {stop['ratio']:.2f}")


def start_tabbing_before(page, selector):
    """Move keyboard focus to the control before `selector`'s first stop, so the next Tab lands in it."""
    page.locator(selector).first.focus()
    page.keyboard.press('Shift+Tab')


class FocusRingTests(StudioCase):
    def test_every_stop_in_the_bridge_bar_and_the_slot_inspector_shows_a_ring(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for dark in (False, True):
                    page = self.studio(engine, dark=dark)
                    page.locator('#targetAppUrl').fill('http://localhost:8001/demo/')   # enables Connect
                    start_tabbing_before(page, '#targetAppUrl')
                    assert_rings(self, tab_stops(page, '#targetAppBridgeBar'), 'bridge bar', 6)
                    self.select_slot(page)
                    start_tabbing_before(page, '#slotInspector select, #slotInspector input, #slotInspector button, #slotInspector textarea')
                    assert_rings(self, tab_stops(page, '#slotInspector'), 'slot inspector', 8)

    def test_text_fields_show_the_ring_as_well_as_the_accent_border(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                start_tabbing_before(page, '#canvasBgHex')
                page.keyboard.press('Tab')
                ring = page.locator('#canvasBgHex').evaluate('el => getComputedStyle(el).outlineStyle')
                self.assertNotEqual(ring, 'none', 'the field no longer sets outline: none')


class LiveAppFocusRingTests(LiveAppCase):
    def test_every_stop_in_the_live_inspector_and_the_connected_bridge_bar_shows_a_ring(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                start_tabbing_before(page, '#targetAppUrl')
                assert_rings(self, tab_stops(page, '#targetAppBridgeBar'), 'connected bridge bar', 10)
                self.select_title(page)
                start_tabbing_before(page, '#slotInspector select, #slotInspector input, #slotInspector button, #slotInspector textarea')
                assert_rings(self, tab_stops(page, '#slotInspector', 60), 'live inspector', 12)


class ContrastTests(StudioCase):
    def test_field_borders_reach_3_to_1_against_the_field_and_its_surroundings(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for dark in (False, True):
                    page = self.studio(engine, dark=dark, mode='library')
                    library = evaluate(page, r"""
                      return [...document.querySelectorAll('#libraryView ' + arg)].filter(el => el.offsetParent && !el.disabled).map(el => {   // a disabled control is exempt from 1.4.11
                        const border = parse(getComputedStyle(el).borderTopColor); border[3] *= opacityOf(el);
                        return [label(el), ratio(over(border, backdrop(el)), backdrop(el)), ratio(over(border, backdrop(el.parentElement)), backdrop(el.parentElement))]; });""", FIELDS)
                    page.locator('#modeComposer').click()
                    self.select_slot(page)
                    composer = evaluate(page, r"""
                      return [...document.querySelectorAll('.composer-toolbar ' + arg + ', #slotInspector ' + arg)].filter(el => el.offsetParent && !el.disabled).map(el => {   // a disabled control is exempt from 1.4.11
                        const border = parse(getComputedStyle(el).borderTopColor); border[3] *= opacityOf(el);
                        return [label(el), ratio(over(border, backdrop(el)), backdrop(el)), ratio(over(border, backdrop(el.parentElement)), backdrop(el.parentElement))]; });""", FIELDS)
                    for where, rows, minimum in (('Library', library, 2), ('Composer', composer, 8)):
                        self.assertGreaterEqual(len(rows), minimum, where)
                        weak = [(name, round(min(own, around), 2)) for name, own, around in rows if min(own, around) < 3]
                        self.assertEqual(weak, [], f'{where} {"dark" if dark else "light"}: field borders under 3:1')

    def test_tags_and_placeholders_reach_4_5_to_1(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for dark in (False, True):
                    page = self.studio(engine, dark=dark, mode='library')
                    tags = evaluate(page, r"""
                      return [...document.querySelectorAll('.tag')].map(el => {
                        const fg = parse(getComputedStyle(el).color); fg[3] *= opacityOf(el);
                        return ratio(over(fg, backdrop(el)), backdrop(el)); });""")
                    self.assertGreater(len(tags), 10)
                    self.assertGreaterEqual(min(tags), 4.5, f'.tag {"dark" if dark else "light"}')
                    page.locator('#modeComposer').click()
                    fields = evaluate(page, r"""
                      return [...document.querySelectorAll('input[placeholder]')].filter(el => el.offsetParent).map(el => {
                        const style = getComputedStyle(el, '::placeholder');
                        const fg = parse(style.color); fg[3] *= opacityOf(el) * Number(style.opacity);
                        return [label(el), ratio(over(fg, backdrop(el)), backdrop(el)), Number(style.opacity)]; });""")
                    self.assertGreaterEqual(len(fields), 2)
                    for name, value, opacity in fields:
                        self.assertEqual(opacity, 1, f'{name} placeholder is not faded')
                        self.assertGreaterEqual(value, 4.5, f'{name} placeholder {"dark" if dark else "light"}: {value:.2f}')
                    page.locator('#modeLibrary').click()
                    library = evaluate(page, r"""
                      return [...document.querySelectorAll('#libraryView input[placeholder]')].map(el => {
                        const style = getComputedStyle(el, '::placeholder');
                        const fg = parse(style.color); fg[3] *= opacityOf(el) * Number(style.opacity);
                        return [label(el), ratio(over(fg, backdrop(el)), backdrop(el))]; });""")
                    self.assertEqual([name for name, value in library if value < 4.5], [])

    def test_the_asset_placeholder_reaches_4_5_to_1(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                found = evaluate(page, r"""
                  const el = document.querySelector('.asset-placeholder');
                  if (!el) return null;
                  const canvas = document.querySelector('#composerCanvas');
                  const fg = parse(getComputedStyle(el).color);
                  fg[3] *= opacityOf(el);
                  return { ratio: ratio(over(fg, backdrop(canvas)), backdrop(canvas)), opacity: opacityOf(el) };""")
                self.assertIsNotNone(found, 'the Editorial preset shows an asset placeholder')
                self.assertGreaterEqual(found['ratio'], 4.5)


class CopyTests(StudioCase):
    def test_the_users_page_has_one_name_before_anything_connects(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                names = visible_names(page)
                self.assertEqual([name for name in names if OLD_NAMES.search(name)], [])
                self.assertEqual(page.locator('#viewTargetApp').inner_text(), 'Live App')
                self.assertIn('Live App Bridge', names)
                page.locator('#viewTargetApp').click()
                self.assertEqual(page.locator('#slotInspector h2').inner_text(), 'Live App')
                self.assertEqual(page.locator('#slotInspector').get_attribute('aria-label'), 'Live App inspector')
                self.assertEqual(page.locator('#targetAppFrame').get_attribute('title'), 'Live App preview')
                self.assertEqual([name for name in visible_names(page) if OLD_NAMES.search(name)], [])

    def test_the_bridge_bar_has_no_emoji_and_no_two_actions_share_a_glyph(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                labels = page.locator('#targetAppBridgeBar button').evaluate_all(
                    'els => els.map(el => [el.id, el.textContent.trim(), el.title])')
                self.assertGreater(len(labels), 8)
                for ident, text, title in labels:
                    self.assertIsNone(EMOJI.search(text + title), f'{ident}: {text!r}')
                glyphs = [text[0] for ident, text, title in labels if not text[0].isalnum()]
                self.assertEqual(len(glyphs), len(set(glyphs)), f'one glyph per action: {glyphs}')
                self.assertNotIn('⚡', page.locator('#btnSyncToApp').inner_text())


class LiveAppCopyTests(LiveAppCase):
    def test_the_users_page_has_one_name_once_connected(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                self.assertEqual(page.locator('#slotInspector h2').inner_text(), 'Live App')
                self.assertEqual([name for name in visible_names(page) if OLD_NAMES.search(name)], [])
                self.select_title(page)
                self.assertEqual(page.locator('#slotInspector').get_attribute('aria-label'), 'Live App inspector')
                self.assertEqual([name for name in visible_names(page) if OLD_NAMES.search(name)], [])


class ModeButtonTests(StudioCase):
    def test_select_and_interact_look_disabled_when_they_are(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                state = evaluate(page, r"""
                  const pick = (id) => { const el = document.getElementById(id), s = getComputedStyle(el);
                    return { disabled: el.disabled, opacity: Number(s.opacity), cursor: s.cursor }; };
                  return { select: pick('bridgeModeSelect'), interact: pick('bridgeModeInteract'), specimen: pick('viewSpecimenCanvas') };""")
                for name in ('select', 'interact'):
                    self.assertTrue(state[name]['disabled'], name)
                    self.assertLessEqual(state[name]['opacity'], 0.6, f'{name} is faded')
                    self.assertEqual(state[name]['cursor'], 'not-allowed', name)
                self.assertEqual(state['specimen']['opacity'], 1, 'an enabled segmented button is not faded')


class SyncHintTests(LiveAppCase):
    def test_the_sync_to_file_hint_sits_on_its_own_line_apart_from_auto_sync(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                page.wait_for_function('() => !document.querySelector("#liveCodeSyncHint").hidden')
                boxes = page.evaluate('''() => { const r = (s) => { const b = document.querySelector(s).getBoundingClientRect();
                  return { top: b.top, bottom: b.bottom, left: b.left, right: b.right }; };
                  return { auto: r('.live-autosync'), hint: r('#liveCodeSyncHint'), sync: r('#liveCodeSync') }; }''')
                self.assertGreaterEqual(boxes['hint']['top'], boxes['auto']['bottom'], 'the hint starts below the Auto-sync row')
                self.assertEqual(page.locator('#liveCodeSyncHint').inner_text(), 'No changes to save yet.')


class VersionLabelTests(StudioCase):
    def test_the_title_and_the_eyebrow_name_this_release(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine, mode='library')
                self.assertEqual(page.title(), 'Font Kit Studio v0.3.1')
                self.assertEqual(page.locator('.eyebrow').text_content(), 'Font Kit Studio · v0.3.1')   # CSS upper-cases the display

    def test_limits_are_stated_without_a_version(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                page.locator('#composerCanvas .row-layout').first.click(position={'x': 2, 'y': 2})
                page.wait_for_selector('.row-child-list')
                self.assertIn('Rows cannot contain rows.', page.locator('#slotInspector').inner_text())
                page.locator('.row-child-jump').first.click()
                self.assertIn('Session-local. SVG is previewed', page.locator('#slotInspector').inner_text())
                page.locator('#assetFile').set_input_files({'name': 'photo.jpg', 'mimeType': 'image/jpeg', 'buffer': b'x'})
                self.assertEqual(page.locator('#composerStatus').inner_text(), 'Asset rejected: only PNG and SVG are accepted.')
                page.locator('#exportJson').click()
                exported = page.locator('#exportDialogText').input_value()
                page.locator('#exportDialog').evaluate('dialog => dialog.close()')
                page.locator('#importJsonFile').set_input_files(
                    {'name': 'composition.json', 'mimeType': 'application/json', 'buffer': exported.encode()})
                page.wait_for_function('() => /^Composition imported\\./.test(document.querySelector("#composerStatus").textContent)')
                self.assertEqual(page.locator('#composerStatus').inner_text(), 'Composition imported. Image assets must be reselected.')
                self.assertEqual(page.errors, [])

    def test_comment_headers_name_the_version_that_introduced_the_block(self):
        """A comment that names a version says "added in vX.Y.Z" (or points at a plan file), never the current one.
        The title and the eyebrow are the two places that do name the current release."""
        lines = [line.strip() for line in HTML.read_text(encoding='utf-8').splitlines() if re.search(r'v0\.\d+\.\d+', line)]
        comments = [line for line in lines if not line.startswith('<title>') and 'class="eyebrow"' not in line]
        self.assertGreaterEqual(len(comments), 4, 'the scan found the section headers')
        self.assertEqual([line for line in comments if not re.search(r'added in v0\.\d+\.\d+|docs/', line)], [])


def all_names(page):
    """Every text, title, aria-label and placeholder in the markup right now, shown or hidden."""
    return evaluate(page, r"""
      const found = [];
      document.querySelectorAll('body *').forEach((el) => {
        if (el.closest('script, style')) return;
        ['title', 'aria-label', 'placeholder'].forEach((name) => { const v = el.getAttribute(name); if (v) found.push(v); });
        if (el.childElementCount === 0 && el.textContent.trim()) found.push(el.textContent.trim());
      });
      return found;""")


def from_the_page(frame, message, page):
    """The Live App posts `message` to Studio, with the session it was given, as the real bridge would."""
    sid = frame.evaluate('window.__received.filter(i => i.data && i.data.type === "design:hello").pop().data.sessionId')
    frame.evaluate('([m, sid]) => parent.postMessage({protocolVersion: 1, sessionId: sid, ...m}, "*")', [message, sid])


class PageNameTests(StudioCase):
    def bad_names(self, page):
        return [name for name in all_names(page) if PAGE_AS_TARGET.search(name) or OLD_NAMES.search(name)]

    def test_no_text_in_any_state_calls_the_users_page_the_target(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, target=None, query=False)
                page.locator('#modeComposer').click()
                self.assertEqual(self.bad_names(page), [], 'nothing connected, markup shown and hidden')
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                self.assertEqual(self.bad_names(page), [], 'connected, nothing selected')
                from_the_page(frame, {'type': 'design:warning', 'kind': 'runtime-error', 'message': 'boom', 'targetId': 'hero.title'}, page)
                page.wait_for_selector('#bridgeWarning:not([hidden])')
                self.assertEqual(self.bad_names(page), [], 'after a runtime warning')
                self.assertIn('Runtime error in the Live App', page.locator('#bridgeWarningText').inner_text())
                self.select(page, frame, 'stat.badge')
                self.assertIn('Live App snaps to the nearest', page.locator('#liveWeightNote').inner_text())
                self.assertEqual(self.bad_names(page), [], 'a target with allowed weights selected')
                page.evaluate("window.open = () => ({ closed: false, focus() {}, close() {}, postMessage() {} })")
                page.locator('#bridgePopOut').click()
                page.wait_for_selector('#bridgePopoutPlaceholder:not([hidden])')
                self.assertEqual(self.bad_names(page), [], 'popped out')
                self.assertIn('The Live App is open in its own window', page.locator('#bridgePopoutText').inner_text())
                # The window's name is plumbing (window.open's second argument), not something to read.
                self.assertNotIn('fontkit-target', page.locator('#bridgePopoutText').inner_text())
                page, errors = self.open(engine)
                self.wait_connected(page)
                from_the_page(self.frame(page), {'type': 'design:targets', 'targets': []}, page)
                page.wait_for_selector('.live-target-list .inspector-note')
                self.assertEqual(self.bad_names(page), [], 'a Live App with no editable elements')
                self.assertEqual(page.locator('.live-target-list .inspector-note').inner_text(), 'The Live App exposed no editable elements.')

    def test_a_target_without_a_stable_flag_is_listed_with_the_marked_ones(self):
        """The bridge says `stable: false` for scanned targets; a manifest without the flag is not "found automatically"."""
        entries = [{'id': 't.marked', 'name': 'Marked one', 'stable': True},
                   {'id': 't.unflagged', 'name': 'Unflagged one'},
                   {'id': 't.scanned', 'name': 'Scanned one', 'stable': False}]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                targets = [{**entry, 'role': 'title', 'kind': 'text', 'tag': 'h2', 'editable': {'text': True, 'typography': True}} for entry in entries]
                from_the_page(self.frame(page), {'type': 'design:targets', 'targets': targets}, page)
                page.wait_for_selector('[data-live-target="t.scanned"]')
                groups = page.evaluate("""() => [...document.querySelectorAll('.live-target-group')].map(group => [
                  group.querySelector('h3').textContent.trim(), [...group.querySelectorAll('[data-live-target]')].map(b => b.dataset.liveTarget)])""")
                self.assertEqual(groups, [['Marked with data-design-id', ['t.marked', 't.unflagged']], ['Auto-discovered', ['t.scanned']]])
                self.assertEqual(errors, [])


class ToolbarFitTests(StudioCase):
    def test_the_fields_of_a_toolbar_row_share_a_top_edge(self):
        """A wrapped label must not push its field below the fields beside it."""
        rows = {1440: [['kitPreset', 'composerKitIds', 'compositionPreset', 'slotCount', 'canvasWidth']],
                1280: [['kitPreset', 'composerKitIds', 'compositionPreset', 'slotCount', 'canvasWidth']],
                1024: [['kitPreset', 'composerKitIds'], ['compositionPreset', 'slotCount', 'canvasWidth']]}
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for width, groups in rows.items():
                    page = self.studio(engine, viewport={'width': width, 'height': 800})
                    for ids in groups:
                        tops = page.evaluate('(ids) => ids.map(id => Math.round(document.getElementById(id).getBoundingClientRect().top))', ids)
                        self.assertEqual(len(set(tops)), 1, f'{width}px {ids}: tops {tops}')


    def test_no_toolbar_select_clips_its_text(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for width in (1280, 1024):
                    page = self.studio(engine, viewport={'width': width, 'height': 800})
                    rows = evaluate(page, r"""
                      const ctx = document.createElement('canvas').getContext('2d');
                      return [...document.querySelectorAll('.composer-toolbar select')].filter(el => el.offsetParent).map(el => {
                        const s = getComputedStyle(el);
                        ctx.font = `${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
                        const text = el.selectedOptions[0].textContent;
                        const room = el.clientWidth - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight) - 20;   // the arrow
                        return [label(el), text, Math.round(ctx.measureText(text).width), Math.round(room)]; });""")
                    self.assertGreaterEqual(len(rows), 5)
                    self.assertEqual([row for row in rows if row[2] > row[3]], [], f'{width}px: selected text wider than its select')


# The longest address the dev server offers: its own port is up to five digits, as in http://localhost:12345/demo/.
OFFERED_ADDRESS = 'http://localhost:12345/demo/'
URL_BOX_SIZES = ((1440, 900), (1280, 800), (1024, 768))
# How many characters of the box's own (monospace) font fit between its padding, and whether the page scrolls sideways.
URL_BOX_JS = """() => {
  const el = document.getElementById('targetAppUrl'), style = getComputedStyle(el);
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
  const room = el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  return { chars: Math.floor(room / ctx.measureText('0').width), scrollsSideways: document.documentElement.scrollWidth > innerWidth };
}"""


class UrlBoxFitTests(LiveAppCase):
    def fit(self, page, width, state):
        """One subTest per width and state, so a failing run names every state that squeezes the box."""
        with self.subTest(width=width, state=state):
            measured = page.evaluate(URL_BOX_JS)
            self.assertGreaterEqual(measured['chars'], len(OFFERED_ADDRESS), f'the address box fits {measured["chars"]} characters')
            self.assertFalse(measured['scrollsSideways'], 'the page scrolls sideways')

    def test_the_address_box_holds_an_address_in_every_state_of_the_bar(self):
        """The badge text and the button label decide how many controls share the first row, so the box is measured
        in each state: the bar's other controls must not squeeze it into a sliver."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                for width, height in URL_BOX_SIZES:
                    size = {'width': width, 'height': height}
                    page = self.open(engine, viewport=size, query=False)
                    page.locator('#modeComposer').click()
                    page.wait_for_function('(url) => document.getElementById("targetAppUrl").value === url', arg=self.target)
                    self.fit(page, width, 'idle, the demo offered')
                    page.locator('#targetAppUrl').fill('')
                    self.fit(page, width, 'idle, empty box')

                    page = self.live(engine, viewport=size)
                    self.fit(page, width, 'Connected (N targets)')
                    self.select_title(page)
                    self.type_into(page, '#liveFontSize', '70')
                    self.wait_badge(page, r'^Live')
                    self.fit(page, width, 'Live · rev N')
                    with self.subTest(width=width, state='page errors'):
                        self.assertEqual(page.errors, [])


class ExportCommentTests(StudioCase):
    def test_a_saved_edit_for_an_unknown_id_says_to_connect_the_live_app(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                document = self.export(page)
                document['live'] = {**document.get('live', {'target': FAKE, 'revision': 0}), 'overrides': {'ghost.title': {'fontSize': 33}}}
                self.import_document(page, document)
                css = self.code(page, 'Css')
                self.assertIn('selector assumed from the id; connect the Live App to confirm', css)
                self.assertNotIn('connect the target', css)


class TargetRowTitleTests(StudioCase):
    def test_a_row_title_holds_the_whole_name_and_id_as_text(self):
        name = 'A very long heading name that no 300px row can show <b>in full</b> without cutting it'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                entry = {'id': 'long.one', 'name': name, 'stable': True, 'role': 'title', 'kind': 'text', 'tag': 'h2',
                         'editable': {'text': True, 'typography': True}}
                from_the_page(self.frame(page), {'type': 'design:targets', 'targets': [entry]}, page)
                page.wait_for_selector('[data-live-target="long.one"]')
                button = page.locator('[data-live-target="long.one"]')
                self.assertEqual(button.get_attribute('title'), f'{name} \u2014 long.one')
                self.assertEqual(button.locator('b').count(), 0, 'the name is text, not markup')
                self.assertTrue(button.locator('span').evaluate('el => el.scrollWidth > el.clientWidth'), 'the row does cut this name')
                self.assertEqual(errors, [])


class LiveAppListTests(LiveAppCase):
    def test_every_stop_in_the_target_list_keeps_its_whole_ring_inside_the_scrolling_boxes(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                total = page.locator('[data-live-target]').count()
                start_tabbing_before(page, '[data-live-target]')
                stops = []
                for _ in range(total + 3):
                    page.keyboard.press('Tab')
                    stop = evaluate(page, r"""
                      const el = document.activeElement;
                      if (!el.matches('[data-live-target]')) return null;
                      const s = getComputedStyle(el);
                      const grow = parseFloat(s.outlineOffset) + parseFloat(s.outlineWidth);
                      const b = el.getBoundingClientRect();
                      const ring = { left: b.left - grow, top: b.top - grow, right: b.right + grow, bottom: b.bottom + grow };
                      const outside = [];
                      for (let node = el.parentElement; node; node = node.parentElement) {
                        const o = getComputedStyle(node), a = node.getBoundingClientRect();
                        const box = { left: a.left + node.clientLeft, top: a.top + node.clientTop };
                        box.right = box.left + node.clientWidth; box.bottom = box.top + node.clientHeight;
                        if (o.overflowX !== 'visible' && (ring.left < box.left - 0.5 || ring.right > box.right + 0.5)) outside.push([label(node), 'x']);
                        if (o.overflowY !== 'visible' && (ring.top < box.top - 0.5 || ring.bottom > box.bottom + 0.5)) outside.push([label(node), 'y']);
                      }
                      return { id: el.dataset.liveTarget, style: s.outlineStyle, width: parseFloat(s.outlineWidth), outside };""")
                    if stop is None:
                        break
                    stops.append(stop)
                self.assertEqual(len(stops), total, 'every target in the list is a keyboard stop')
                for stop in stops:
                    self.assertNotEqual(stop['style'], 'none', stop['id'])
                    self.assertGreaterEqual(stop['width'], 2, stop['id'])
                    self.assertEqual(stop['outside'], [], f"{stop['id']}: the ring is clipped by a scrolling box")

    def test_a_target_name_is_never_cut_while_its_id_keeps_room(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.live(engine)
                cut = page.evaluate("""() => [...document.querySelectorAll('[data-live-target] > span')]
                  .filter(span => span.scrollWidth > span.clientWidth).map(span => span.textContent)""")
                self.assertEqual(cut, [], 'every name in the 300px column is fully visible')
                self.assertGreater(page.locator('[data-live-target]').count(), 30)


class RowChildListTests(StudioCase):
    def test_row_child_names_are_fully_visible(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.studio(engine)
                page.locator('#composerCanvas .row-layout').first.click(position={'x': 2, 'y': 2})
                page.wait_for_selector('.row-child-list')
                cut = page.evaluate("""() => [...document.querySelectorAll('.row-child-jump > span')]
                  .filter(span => span.scrollWidth > span.clientWidth).map(span => span.textContent)""")
                self.assertEqual(cut, [])
                self.assertGreaterEqual(page.locator('.row-child-jump').count(), 2)


if __name__ == '__main__':
    unittest.main()
