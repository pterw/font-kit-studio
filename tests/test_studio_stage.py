"""Studio preview stage: width buttons never crop the preview, and --font-serif names a serif family.

Run with PYTHONPATH=tests (python -m unittest tests.test_studio_stage). Studio is served at
http://studio.test and the fake bridge target at http://target.test, as in test_studio_live.
"""

import unittest

from support import ENGINES
from test_studio_live import LiveCase

VIEWPORTS = ((1440, 900), (1280, 800), (1024, 768))
BUTTONS = (('#btnDeviceDesktop', 1440), ('#btnDeviceLaptop', 1024))

# The nearest ancestor of the preview iframe that scrolls horizontally is the preview's own viewport.
SCROLLER = """() => {
  const frame = document.querySelector('#targetAppFrame');
  let node = frame.parentElement;
  while (node && !/^(auto|scroll)$/.test(getComputedStyle(node).overflowX)) node = node.parentElement;
  if (!node) return null;
  const rect = (el) => { const b = el.getBoundingClientRect(); return { left: b.left, right: b.right, top: b.top, bottom: b.bottom }; };
  return {
    tag: node.className || node.id || node.tagName,
    scrollWidth: node.scrollWidth, clientWidth: node.clientWidth,
    overflowX: getComputedStyle(node).overflowX,
    box: rect(node), container: rect(document.querySelector('#targetAppContainer')),
    frame: rect(frame), stage: rect(document.querySelector('.canvas-stage')),
    stageInner: document.querySelector('.canvas-stage').clientWidth
  };
}"""

SCROLL_TO_END = """() => {
  const frame = document.querySelector('#targetAppFrame');
  let node = frame.parentElement;
  while (node && !/^(auto|scroll)$/.test(getComputedStyle(node).overflowX)) node = node.parentElement;
  node.scrollLeft = node.scrollWidth;
  return node.scrollLeft;
}"""


class PreviewWidthTests(LiveCase):
    def measure(self, page):
        info = page.evaluate(SCROLLER)
        self.assertIsNotNone(info, 'the preview iframe sits inside a horizontal scroller')
        return info

    def test_fixed_widths_scroll_instead_of_cropping_at_common_window_sizes(self):
        for engine in ENGINES:
            for width, height in VIEWPORTS:
                for selector, chosen in BUTTONS:
                    with self.subTest(engine=engine, window=width, button=chosen):
                        page, errors = self.open(engine, viewport={'width': width, 'height': height})
                        self.wait_connected(page)
                        page.locator(selector).click()
                        info = self.measure(page)
                        self.assertEqual(info['scrollWidth'], chosen, f'the preview is {chosen}px wide, unscaled: {info}')
                        self.assertGreaterEqual(info['box']['left'], info['stage']['left'], 'inside the stage')
                        self.assertLessEqual(info['box']['right'], info['stage']['right'], 'inside the stage')
                        if chosen > info['stageInner'] - 44:
                            self.assertGreater(info['scrollWidth'], info['clientWidth'], f'a wider preview scrolls: {info}')
                            self.assertIn(info['overflowX'], ('auto', 'scroll'))
                            # The scrollbar sits under the preview, not at the far end of the stage.
                            self.assertLessEqual(info['box']['bottom'] - info['container']['bottom'], 24,
                                                 'the scrollbar is adjacent to the preview')
                            reached = page.evaluate(SCROLL_TO_END)
                            self.assertGreater(reached, 0, 'the user can scroll right')
                            after = self.measure(page)
                            self.assertLessEqual(after['frame']['right'], after['stage']['right'] + 0.5,
                                                 'the right edge of the iframe is reachable')
                            self.assertLessEqual(after['frame']['right'], after['box']['right'] + 0.5)
                        else:
                            self.assertEqual(info['scrollWidth'], info['clientWidth'], 'a preview that fits does not scroll')
                        self.assertEqual(errors, [])

    def test_fluid_never_scrolls_horizontally_and_narrow_widths_fit(self):
        for engine in ENGINES:
            for width, height in VIEWPORTS:
                with self.subTest(engine=engine, window=width):
                    page, errors = self.open(engine, viewport={'width': width, 'height': height})
                    self.wait_connected(page)
                    for selector in ('#btnDeviceDesktop', '#btnDeviceFluid'):
                        page.locator(selector).click()
                    info = page.evaluate("""() => { const c = document.querySelector('#targetAppContainer');
                        const s = document.querySelector('.canvas-stage');
                        return { cw: c.getBoundingClientRect().width, clientWidth: c.clientWidth,
                                 stageScroll: s.scrollWidth - s.clientWidth }; }""")
                    self.assertLessEqual(info['stageScroll'], 0, f'fluid fits the stage: {info}')
                    scroller = self.measure(page)
                    self.assertEqual(scroller['scrollWidth'], scroller['clientWidth'], 'fluid has nothing to scroll')
                    page.locator('#btnDeviceMobile').click()
                    scroller = self.measure(page)
                    self.assertEqual(scroller['scrollWidth'], 390)
                    self.assertEqual(scroller['scrollWidth'], scroller['clientWidth'])
                    self.assertEqual(errors, [])

    def test_a_wide_preview_in_fullscreen_still_fills_the_height_and_scrolls(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine, viewport={'width': 1280, 'height': 800})
                self.wait_connected(page)
                page.locator('#btnToggleFullscreen').click()
                page.wait_for_function('document.querySelector(".composer-shell").classList.contains("is-theater-fullscreen")')
                fluid = self.measure(page)
                self.assertGreater(fluid['container']['bottom'] - fluid['container']['top'], 500, 'fluid fills the layer too')
                self.assertEqual(fluid['scrollWidth'], fluid['clientWidth'])
                page.locator('#btnDeviceDesktop').evaluate('(button) => button.click()')
                info = self.measure(page)
                self.assertEqual(info['scrollWidth'], 1440)
                self.assertGreater(info['scrollWidth'], info['clientWidth'])
                self.assertGreater(info['container']['bottom'] - info['container']['top'], 500, 'the preview fills the layer')
                self.assertLessEqual(info['box']['bottom'], 800, 'the preview and its scrollbar stay on screen')
                page.evaluate(SCROLL_TO_END)
                after = self.measure(page)
                self.assertLessEqual(after['frame']['right'], after['stage']['right'] + 0.5)
                page.keyboard.press('Escape')
                self.assertEqual(errors, [])


class SerifTokenTests(LiveCase):
    ROWS = {
        'sans': ('Wordmark', 'inter'),
        'serif': ('H1', 'instrument-serif'),
        'mono': ('Metadata', 'ibm-plex-mono'),
    }

    def composition(self, page, text_slots):
        """Replace the preset's slots with the given (role, family) text slots; a 'row' entry is the Row slot."""
        document = self.export(page)
        template = {slot['type']: slot for slot in document['composition']['slots']}
        template['text'] = next(slot for slot in document['composition']['slots'] if slot['type'] == 'text')
        slots = []
        for index, entry in enumerate(text_slots):
            if entry == 'row':
                slots.append({**template['row'], 'id': f'row-{index}'})
                continue
            role, family = entry
            slots.append({**template['text'], 'id': f'text-{index}', 'role': role, 'family': family,
                          'variables': {}, 'styleIndex': 0})
        document['composition']['slots'] = slots
        document['composition']['selectedId'] = slots[0]['id']
        self.import_document(page, document)

    def synced_tokens(self, page, frame):
        before = len([u for u in self.updates(frame) if 'targetId' not in u])
        page.locator('#btnSyncToApp').click()
        self.wait_live(page)
        updates = [u for u in self.updates(frame) if 'targetId' not in u]
        self.assertEqual(len(updates), before + 1)
        return updates[-1]['patch']['tokens']

    def run_case(self, text_slots):
        results = {}
        for engine in ENGINES:
            page, errors = self.open(engine)
            self.wait_connected(page)
            frame = self.frame(page)
            self.composition(page, text_slots)
            results[engine] = (self.synced_tokens(page, frame), errors)
        return results

    def test_serif_token_is_the_first_serif_family_when_slot_two_is_a_row(self):
        slots = [self.ROWS['sans'], self.ROWS['serif'], 'row', self.ROWS['mono']]
        for engine, (tokens, errors) in self.run_case(slots).items():
            with self.subTest(engine=engine):
                self.assertIn('"Instrument Serif"', tokens['--font-serif'])
                self.assertEqual(errors, [])

    def test_no_serif_token_is_sent_when_no_slot_uses_a_serif_family(self):
        slots = [self.ROWS['sans'], ('H1', 'jetbrains-mono'), 'row', self.ROWS['mono']]
        for engine, (tokens, errors) in self.run_case(slots).items():
            with self.subTest(engine=engine):
                self.assertNotIn('--font-serif', tokens)
                self.assertIn('--font-display', tokens, 'the other tokens still travel')
                self.assertEqual(errors, [])

    def test_a_slot_whose_role_says_editorial_still_wins_the_serif_token(self):
        slots = [self.ROWS['sans'], ('Editorial', 'inter'), 'row', self.ROWS['mono'], self.ROWS['serif']]
        for engine, (tokens, errors) in self.run_case(slots).items():
            with self.subTest(engine=engine):
                self.assertTrue(tokens['--font-serif'].startswith('"Inter"'), tokens['--font-serif'])
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
