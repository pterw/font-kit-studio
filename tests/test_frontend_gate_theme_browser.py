"""The contrast gate's in-page colour reading, driven in a real browser.

Chromium serialises a tiny alpha with an exponent: a background of
`color(srgb 0 0 0 / 1e-7)` computes to `color(srgb 0 0 0 / 1.00000e-7)`. The page
script that collects the backgrounds behind a piece of text must read that as
near-transparent and keep walking outwards. Read as opaque, it stops at that
layer and the text is judged against the wrong surface.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ENGINES, launch  # noqa: E402
from scripts.dev import _frontend_gate_theme as theme  # noqa: E402

# Light text on a black page, under a layer that paints almost nothing.
PAGE = ('<!doctype html><body style="margin:0;background:rgb(0, 0, 0)">'
        '<div id="r" style="background:{layer}"><p style="margin:0;color:rgb(255, 255, 255)">Readable text</p></div>')
LAYERS = (
    'color(srgb 0 0 0 / 1e-7)',
    'color-mix(in srgb, transparent 99.99999%, white)',
)


class InPageAlphaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.runtime = sync_playwright().start()

    @classmethod
    def tearDownClass(cls):
        cls.runtime.stop()

    def samples(self, engine, layer):
        browser = launch(self.runtime, engine)
        self.addCleanup(browser.close)
        page = browser.new_page()
        page.set_content(PAGE.format(layer=layer))
        return page.evaluate(theme.CONTRAST_JS, [['#r'], []])

    def test_a_near_transparent_background_does_not_end_the_walk(self):
        for engine in ENGINES:
            for layer in LAYERS:
                with self.subTest(engine=engine, layer=layer):
                    samples = self.samples(engine, layer)
                    self.assertEqual(len(samples), 1)
                    layers = samples[0]['layers']
                    self.assertEqual(len(layers), 2, f'the walk reached the page behind {layers}')
                    self.assertEqual(layers[1], 'rgb(0, 0, 0)')

    def test_text_over_a_near_transparent_layer_is_judged_against_the_page_behind_it(self):
        for engine in ENGINES:
            for layer in LAYERS:
                with self.subTest(engine=engine, layer=layer):
                    failures, _, measured = theme.judge_samples('x', self.samples(engine, layer))
                    self.assertEqual((failures, measured), ([], 1))


if __name__ == '__main__':
    unittest.main()
