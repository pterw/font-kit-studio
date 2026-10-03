"""Frontend gate: the pure judgements behind each check (no browser).

Colour maths, contrast and layout judges, network judges and the logo checks
take numbers, strings and file text, so they are pinned here in the normal
suite. The browser measurements that feed them are exercised by the gate
itself (`scripts/dev/frontend_gate.py`); nothing here launches a browser.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.dev import _frontend_gate_assets as assets  # noqa: E402
from scripts.dev import _frontend_gate_layout as layout  # noqa: E402
from scripts.dev import _frontend_gate_network as network  # noqa: E402
from scripts.dev import _frontend_gate_theme as theme  # noqa: E402
from scripts.dev._frontend_gate_colour import (  # noqa: E402
    _composite_over, _contrast_ratio, _parse_rgb_string, _relative_luminance, flatten_layers,
)

REPO = Path(__file__).resolve().parents[1]
WHITE = (255.0, 255.0, 255.0)
BLACK = (0.0, 0.0, 0.0)


class ColourMathTests(unittest.TestCase):
    def test_black_on_white_is_the_wcag_maximum(self):
        self.assertAlmostEqual(_contrast_ratio(BLACK, WHITE), 21.0, places=6)

    def test_identical_colours_have_ratio_one(self):
        self.assertAlmostEqual(_contrast_ratio((10, 20, 30), (10, 20, 30)), 1.0, places=9)

    def test_ratio_is_symmetric(self):
        grey = (119.0, 119.0, 119.0)
        self.assertAlmostEqual(_contrast_ratio(grey, WHITE), _contrast_ratio(WHITE, grey), places=9)

    def test_the_wcag_reference_greys_land_either_side_of_4_5(self):
        # #767676 is the lightest grey that passes 4.5:1 on white; #777777 just fails.
        self.assertGreaterEqual(_contrast_ratio((0x76,) * 3, WHITE), 4.5)
        self.assertLess(_contrast_ratio((0x77,) * 3, WHITE), 4.5)

    def test_relative_luminance_endpoints(self):
        self.assertAlmostEqual(_relative_luminance(BLACK), 0.0)
        self.assertAlmostEqual(_relative_luminance(WHITE), 1.0)

    def test_compositing_half_black_over_white_is_mid_grey(self):
        self.assertEqual(_composite_over((0, 0, 0, 0.5), WHITE), (127.5, 127.5, 127.5))

    def test_a_fully_transparent_foreground_leaves_the_background(self):
        self.assertEqual(_composite_over((9, 9, 9, 0.0), (1, 2, 3)), (1.0, 2.0, 3.0))


class ColourParsingTests(unittest.TestCase):
    def test_rgb_and_rgba(self):
        self.assertEqual(_parse_rgb_string('rgb(1, 2, 3)'), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(_parse_rgb_string('rgba(1, 2, 3, 0.5)'), (1.0, 2.0, 3.0, 0.5))

    def test_color_srgb_channels_are_zero_to_one_and_scaled(self):
        # How both engines serialise a computed color-mix(): channels in 0-1.
        red, green, blue, alpha = _parse_rgb_string('color(srgb 1 0.5 0)')
        self.assertEqual((red, green, blue, alpha), (255.0, 127.5, 0.0, 1.0))
        self.assertEqual(_parse_rgb_string('color(srgb 0 0 0 / 0.25)')[3], 0.25)

    def test_exponent_notation_is_read_as_one_number(self):
        # Chromium serialises a tiny channel with an exponent: color(srgb 1e-7 ...) computes to
        # color(srgb 1.00000e-7 ...), and color-mix() with a tiny share gives 1.19209e-7.
        red, green, blue, alpha = _parse_rgb_string('color(srgb 1.00000e-7 0.2 0.3 / 0.5)')
        self.assertAlmostEqual(red, 255e-7)
        self.assertAlmostEqual(green, 51.0)
        self.assertAlmostEqual(blue, 76.5)
        self.assertEqual(alpha, 0.5)
        self.assertAlmostEqual(_parse_rgb_string('color(srgb 1.19209e-7 0 1)')[0], 1.19209e-7 * 255)
        self.assertAlmostEqual(_parse_rgb_string('color(srgb 0.2 0.2 0.2 / 5e-1)')[3], 0.5)
        self.assertAlmostEqual(_parse_rgb_string('color(srgb 0.2 0.2 0.2 / 1.5E-3)')[3], 0.0015)
        self.assertAlmostEqual(_parse_rgb_string('rgba(1, 2, 3, 1e-2)')[3], 0.01)
        self.assertEqual(_parse_rgb_string('color(srgb .5 0 0)')[0], 127.5)

    def test_an_unknown_serialisation_is_refused_not_guessed(self):
        for text in ('oklch(0.5 0.2 30)', 'hsl(10 20% 30%)', '#ffffff', 'lab(50 10 10)'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                _parse_rgb_string(text)


class FlattenLayersTests(unittest.TestCase):
    def test_no_layers_paints_on_the_white_canvas(self):
        self.assertEqual(flatten_layers([]), WHITE)

    def test_the_first_opaque_layer_wins_and_outer_layers_are_ignored(self):
        self.assertEqual(flatten_layers(['rgb(10, 20, 30)', 'rgb(200, 200, 200)']), (10.0, 20.0, 30.0))

    def test_a_translucent_layer_is_composited_over_the_next_opaque_one(self):
        # 50% black over an opaque white page reads as mid grey, not as black.
        self.assertEqual(flatten_layers(['rgba(0, 0, 0, 0.5)', 'rgb(255, 255, 255)']), (127.5, 127.5, 127.5))

    def test_several_translucent_layers_stack_nearest_last(self):
        near, far, page = 'rgba(0, 0, 0, 0.5)', 'rgba(255, 255, 255, 0.5)', 'rgb(0, 0, 0)'
        # far over black = 127.5 grey; near (50% black) over that = 63.75.
        self.assertEqual(flatten_layers([near, far, page]), (63.75, 63.75, 63.75))

    def test_a_color_mix_layer_in_color_srgb_form_is_read_in_the_right_scale(self):
        flattened = flatten_layers(['color(srgb 1 1 1 / 0.92)', 'rgb(0, 0, 0)'])
        self.assertAlmostEqual(flattened[0], 255 * 0.92)


def sample(color='rgb(0, 0, 0)', layers=('rgb(255, 255, 255)',), size=14, weight=400, opacity=1, image=False,
           what='span.x', text='hello'):
    return {'what': what, 'text': text, 'color': color, 'layers': list(layers), 'size': size, 'weight': weight,
            'opacity': opacity, 'image': image}


class ThemeContrastJudgeTests(unittest.TestCase):
    def test_body_text_needs_4_5_and_large_text_needs_3(self):
        self.assertEqual(theme.required_ratio(14, 400), 4.5)
        self.assertEqual(theme.required_ratio(24, 400), 3.0)
        self.assertEqual(theme.required_ratio(18.66, 700), 3.0)
        self.assertEqual(theme.required_ratio(18.66, 400), 4.5, 'bold is what makes 14pt large')
        self.assertEqual(theme.required_ratio(18, 700), 4.5)

    def test_good_text_has_no_findings_and_is_counted_as_measured(self):
        lines, unmeasured, measured = theme.judge_samples('[light] Code panel', [sample()])
        self.assertEqual((lines, unmeasured, measured), ([], [], 1))

    def test_the_muted_on_chip_pair_found_in_studio_fails_at_4_30(self):
        # Studio's --muted (#6f6b63) on --chip (#ece7dc), measured in light mode.
        bad = sample(color='rgb(111, 107, 99)', layers=['rgb(236, 231, 220)'])
        lines, _, _ = theme.judge_samples('[light] Code panel', [bad])
        self.assertEqual(len(lines), 1)
        self.assertIn('4.30:1, expected at least 4.5:1', lines[0])
        self.assertIn('[light] Code panel: span.x', lines[0])

    def test_the_same_text_passes_when_it_is_large(self):
        big = sample(color='rgb(111, 107, 99)', layers=['rgb(236, 231, 220)'], size=24)
        self.assertEqual(theme.judge_samples('x', [big])[0], [])

    def test_identical_failures_collapse_into_one_line_with_a_count(self):
        bad = sample(color='rgb(119, 119, 119)')
        lines, _, measured = theme.judge_samples('x', [bad, dict(bad, text='other'), dict(bad, text='third')])
        self.assertEqual(measured, 3)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith('(3 of them)'))

    def test_translucent_text_is_judged_as_faded(self):
        faded = sample(color='rgb(0, 0, 0)', opacity=0.4)
        self.assertEqual(len(theme.judge_samples('x', [faded])[0]), 1, 'black at 40% opacity is mid grey on white')

    def test_text_colour_alpha_is_judged_as_faded(self):
        # Characterisation: unlike the logo paint judge, the text path already folds the
        # colour's own alpha in, alone and together with an ancestor's opacity.
        for colour, opacity in (('rgba(0, 0, 0, 0.1)', 1), ('rgba(0, 0, 0, 0.5)', 0.2)):
            with self.subTest(colour=colour, opacity=opacity):
                faded = sample(color=colour, opacity=opacity)
                ratio, shown, _ = theme.sample_ratio(faded)
                self.assertLess(ratio, 1.5)
                self.assertGreater(shown[0], 200)
                self.assertEqual(len(theme.judge_samples('x', [faded])[0]), 1)
        solid = sample(color='rgba(0, 0, 0, 0.9)')
        self.assertEqual(theme.judge_samples('x', [solid])[0], [])

    def test_a_translucent_surface_is_judged_against_the_blend(self):
        # Grey text over a 92%-opaque page tint reads against the blend.
        ratio, _, background = theme.sample_ratio(
            sample(color='rgb(0, 0, 0)', layers=['rgba(255, 255, 255, 0.5)', 'rgb(0, 0, 0)']))
        self.assertEqual(background, (127.5, 127.5, 127.5))
        self.assertAlmostEqual(ratio, _contrast_ratio(BLACK, (127.5, 127.5, 127.5)))

    def test_text_on_a_background_image_is_reported_not_guessed(self):
        lines, unmeasured, measured = theme.judge_samples('[dark] Banner', [sample(image=True)])
        self.assertEqual((lines, measured), ([], 0))
        self.assertIn('background image', unmeasured[0])


class LayoutJudgeTests(unittest.TestCase):
    def test_no_overflow_within_one_pixel_of_rounding(self):
        self.assertEqual(layout.overflow_failures('Library', {'scrollWidth': 391, 'clientWidth': 390, 'offenders': []}), [])

    def test_overflow_names_the_surface_the_widths_and_the_offenders(self):
        lines = layout.overflow_failures(
            'Composer specimen', {'scrollWidth': 520, 'clientWidth': 390, 'offenders': ['div.toolbar ends at 520px']})
        self.assertEqual(len(lines), 1)
        self.assertIn('Composer specimen scrolls horizontally: document is 520px wide in a 390px viewport', lines[0])
        self.assertIn('div.toolbar ends at 520px', lines[0])

    def test_a_node_that_is_not_hidden_or_not_present_is_a_failure(self):
        readings = {'#a': 'none', '#b': 'flex', '#c': None}
        lines = layout.hidden_failures('Studio Composer', readings)
        self.assertEqual(len(lines), 2)
        self.assertIn('#b should start hidden but computes display: flex', lines[0])
        self.assertIn('#c is not in the page at all', lines[1])

    def test_a_correctly_hidden_surface_is_clean(self):
        self.assertEqual(layout.hidden_failures('s', {'#a': 'none', '#b': 'none'}), [])

    def test_touch_targets_collapse_by_kind_and_smaller_side(self):
        small = [['button.filter', 36, 33], ['button.filter', 48, 33], ['button#go', 80, 30], ['button.filter', 70, 33]]
        lines = layout.touch_target_lines('Studio Library', small)
        self.assertEqual(lines, [
            'Studio Library: button.filter is 36x33 (3 of them), smaller side under 44px',
            'Studio Library: button#go is 80x30, smaller side under 44px',
        ])

    def test_a_target_already_reported_in_an_earlier_state_is_not_repeated(self):
        reported = set()
        first = layout.touch_target_lines('Library', [['button#a', 40, 30]], reported)
        again = layout.touch_target_lines('Composer', [['button#a', 40, 30], ['button#b', 20, 20]], reported)
        self.assertEqual(len(first), 1)
        self.assertEqual(again, ['Composer: button#b is 20x20, smaller side under 44px'])

    def test_the_selector_measures_labels_and_inputs_and_the_threshold_is_44(self):
        self.assertIn('label[for]', layout.INTERACTIVE_SELECTOR)
        self.assertEqual(layout.MIN_TOUCH_TARGET_PX, 44)

    def test_every_hidden_on_load_selector_exists_in_studio(self):
        html = (REPO / 'font_kit_studio_v0.1.1.html').read_text(encoding='utf-8')
        for _, _, selectors in layout.HIDDEN_ON_LOAD:
            for selector in selectors:
                with self.subTest(selector=selector):
                    self.assertIn(f'id="{selector.lstrip("#")}"', html)

    def test_every_theme_surface_root_that_is_an_id_exists_in_studio(self):
        html = (REPO / 'font_kit_studio_v0.1.1.html').read_text(encoding='utf-8')
        groups = (theme.V02_IDLE, theme.V02_CONNECTED, theme.V02_BANNER, theme.V02_ERROR_STATES, theme.LEGACY_COMPOSER)
        for group in groups:
            for _, roots, excludes in group:
                for selector in (*roots, *excludes):
                    if selector.startswith('#'):
                        with self.subTest(selector=selector):
                            self.assertIn(f'id="{selector[1:]}"', html)


GOOGLE_INTER = 'https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap'
GOOGLE_PLEX = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,100;1,700&display=swap'


class NetworkJudgeTests(unittest.TestCase):
    def test_only_a_google_css2_stylesheet_counts_as_the_documented_request(self):
        self.assertTrue(network.is_google_stylesheet(GOOGLE_INTER))
        for url in ('https://fonts.gstatic.com/s/inter/v1/x.woff2', 'http://fonts.googleapis.com/css2?family=Inter',
                    'https://fonts.googleapis.com/css2', 'https://example.com/css2?family=Inter',
                    'https://fonts.googleapis.com/css?family=Inter'):
            with self.subTest(url=url):
                self.assertFalse(network.is_google_stylesheet(url))

    def test_family_names_are_read_from_the_query(self):
        self.assertEqual(network.google_families([GOOGLE_INTER, GOOGLE_PLEX, GOOGLE_INTER]), ['Inter', 'IBM Plex Mono'])

    def test_a_third_party_request_is_a_failure_on_every_surface(self):
        out = network.isolation_outcome('Studio Library', ['https://tracker.example/pixel.gif'])
        self.assertEqual(len(out.failures), 1)
        self.assertIn('https://tracker.example/pixel.gif', out.failures[0])
        self.assertIn('outside the served loopback origins', out.failures[0])

    def test_an_adobe_kit_request_is_named_as_adobe(self):
        out = network.isolation_outcome('Studio Composer', ['https://use.typekit.net/abc.css'])
        self.assertIn('Adobe Fonts', out.failures[0])

    def test_a_google_stylesheet_on_first_load_is_an_enforced_failure(self):
        # Studio is silent until the user asks for free fonts (global rule 7).
        out = network.isolation_outcome('Studio Library', [GOOGLE_INTER, GOOGLE_PLEX])
        self.assertEqual(out.reports, [])
        self.assertEqual(len(out.failures), 1)
        self.assertIn('2 Google Fonts stylesheet(s) on first load', out.failures[0])
        self.assertIn('Inter, IBM Plex Mono', out.failures[0])
        self.assertIn('before the user asked', out.failures[0])

    def test_the_demo_gets_the_same_rule(self):
        out = network.isolation_outcome('demo (standalone)', [GOOGLE_INTER])
        self.assertEqual(len(out.failures), 1)

    def test_no_requests_is_clean(self):
        out = network.isolation_outcome('Studio Library', [])
        self.assertEqual((out.failures, out.reports), ([], []))

    def test_every_family_needs_a_loaded_face(self):
        self.assertEqual(network.free_font_failures({'Inter': [1, 1], 'Fraunces': [2, 2]}), [])
        failures = network.free_font_failures({'Inter': [1, 1], 'Fraunces': [0, 0], 'Archivo': [1, 0]})
        self.assertEqual(failures, ['family Fraunces resolved no loaded face from Google Fonts',
                                    'family Archivo resolved no loaded face from Google Fonts'])

    def test_when_nothing_arrives_the_message_blames_the_network_and_offers_offline(self):
        failures = network.free_font_failures({'Inter': [0, 0], 'Fraunces': [0, 0]})
        self.assertEqual(len(failures), 1)
        self.assertIn('unreachable', failures[0])
        self.assertIn('--offline', failures[0])

    def test_the_all_missing_message_names_tls_intercepting_proxies_as_a_likely_cause(self):
        message = network.free_font_failures({'Inter': [0, 0], 'Fraunces': [0, 0]})[0]
        self.assertIn('TLS', message)
        self.assertIn('proxy', message)

    def test_missing_families_are_retried_with_backoff_and_a_late_arrival_passes(self):
        calls = []
        attempts = iter([{'Inter': [1, 1], 'Fraunces': [0, 0]},       # first measure: Fraunces missing
                         {'Fraunces': [1, 1]}])                       # after one retry it arrived

        def measure(only):
            calls.append(('measure', only))
            return next(attempts)

        results = network.settle_free_fonts(
            measure, lambda missing: calls.append(('retry', missing)), lambda ms: calls.append(('pause', ms)))
        self.assertEqual(results, {'Inter': [1, 1], 'Fraunces': [1, 1]})
        self.assertEqual(calls, [('measure', None), ('pause', network.FONT_RETRY_BACKOFF_MS[0]),
                                 ('retry', ['Fraunces']), ('measure', ['Fraunces'])])
        self.assertEqual(network.free_font_failures(results), [])

    def test_a_family_still_missing_after_the_last_retry_is_a_failure(self):
        measured = []

        def measure(only):
            measured.append(only)
            return {'Inter': [1, 1], 'Fraunces': [0, 0]} if only is None else {'Fraunces': [0, 0]}

        pauses = []
        results = network.settle_free_fonts(measure, lambda missing: None, pauses.append)
        self.assertEqual(len(measured), 1 + network.FONT_RETRY_ATTEMPTS, 'two extra attempts, no more')
        self.assertEqual(pauses, list(network.FONT_RETRY_BACKOFF_MS[:network.FONT_RETRY_ATTEMPTS]))
        self.assertEqual(network.free_font_failures(results),
                         ['family Fraunces resolved no loaded face from Google Fonts'])

    def test_nothing_is_retried_when_every_family_arrives_first_time(self):
        retried = []
        network.settle_free_fonts(lambda only: {'Inter': [1, 1]}, retried.append, retried.append)
        self.assertEqual(retried, [])

    def test_an_empty_family_list_is_a_failure_not_a_pass(self):
        self.assertEqual(len(network.free_font_failures({})), 1)


CLEAN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>t</title>'
             '<mask id="m"><rect width="10" height="10" fill="#fff"/></mask>'
             '<g mask="url(#m)"><path fill="#000" d="M0 0h10v10z"/></g></svg>')


class LogoStaticTests(unittest.TestCase):
    def failures(self, svg):
        return assets.logo_static_failures('x.svg', svg)

    def test_a_clean_logo_passes(self):
        self.assertEqual(self.failures(CLEAN_SVG), [])

    def test_text_script_and_foreign_content_are_refused(self):
        for tag in ('<text>hi</text>', '<script>alert(1)</script>', '<foreignObject/>', '<image/>', '<a/>'):
            with self.subTest(tag=tag):
                bad = CLEAN_SVG.replace('</svg>', f'{tag}</svg>')
                self.assertTrue(self.failures(bad), tag)

    def test_external_references_are_refused(self):
        cases = ('<path href="https://example.com/a.svg" d="M0 0"/>',
                 '<path fill="url(https://example.com/p.svg#g)" d="M0 0"/>',
                 '<style>@import url(https://example.com/a.css);</style>')
        for fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertTrue(self.failures(CLEAN_SVG.replace('</svg>', f'{fragment}</svg>')))

    def test_external_references_are_refused_whatever_their_case(self):
        # CSS and URL syntax are case-insensitive, so the scan has to be too.
        cases = ('<style>@IMPORT "HTTPS://evil.example/logo.css";</style>',
                 '<style>@Import url(Https://evil.example/logo.css);</style>',
                 '<path fill="URL(HTTPS://evil.example/paint.svg)" d="M0 0"/>',
                 '<path fill="Url( \'hTTp://evil.example/paint.svg#g\' )" d="M0 0"/>',
                 '<path data-x="HTTPS://evil.example/x" d="M0 0"/>',
                 '<path HREF="HTTPS://evil.example/a.svg" d="M0 0"/>')
        for fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertTrue(self.failures(CLEAN_SVG.replace('</svg>', f'{fragment}</svg>')), fragment)

    def test_an_internal_fragment_reference_is_allowed(self):
        self.assertEqual(self.failures(CLEAN_SVG.replace('</svg>', '<path fill="url(#m)" d="M0 0"/></svg>')), [])

    def test_malformed_svg_is_a_failure(self):
        self.assertIn('not well-formed', self.failures('<svg><path></svg>')[0])

    def test_the_shipped_logos_pass(self):
        for name, _ in assets.LOGOS:
            with self.subTest(logo=name):
                text = (REPO / assets.LOGO_DIR / name).read_text(encoding='utf-8')
                self.assertEqual(assets.logo_static_failures(name, text), [])


class LogoPaintJudgeTests(unittest.TestCase):
    def test_dark_ink_on_white_and_light_ink_on_dark_pass_in_both_renderings(self):
        inline = [{'kind': 'fill', 'colour': 'rgb(31, 35, 40)', 'alpha': 1, 'count': 3},
                  {'kind': 'fill', 'colour': 'rgb(220, 20, 60)', 'alpha': 1, 'count': 2}]
        self.assertEqual(assets.inline_paint_failures('l.svg', 'rgb(255, 255, 255)', inline), [])
        image = {'painted': 5000, 'total': 20000, 'colours': {'rgb(240, 246, 252)': 3000, 'rgb(232, 38, 75)': 900}}
        self.assertEqual(assets.image_paint_failures('d.svg', 'rgb(13, 17, 23)', image), [])

    def test_a_colour_that_vanishes_on_the_page_fails(self):
        inline = [{'kind': 'fill', 'colour': 'rgb(31, 35, 40)', 'alpha': 1, 'count': 4}]
        lines = assets.inline_paint_failures('light.svg', 'rgb(13, 17, 23)', inline)
        self.assertEqual(len(lines), 1)
        self.assertIn('expected at least 3:1', lines[0])
        image = {'painted': 5000, 'total': 20000, 'colours': {'rgb(31, 35, 40)': 4000}}
        self.assertEqual(len(assets.image_paint_failures('light.svg', 'rgb(13, 17, 23)', image)), 1)

    def test_translucent_paint_is_judged_after_compositing(self):
        faint = [{'kind': 'stroke', 'colour': 'rgb(0, 0, 0)', 'alpha': 0.1, 'count': 1}]
        self.assertEqual(len(assets.inline_paint_failures('l.svg', 'rgb(255, 255, 255)', faint)), 1)

    def test_a_translucent_colour_is_judged_by_its_own_alpha_too(self):
        # rgba(0, 0, 0, 0.1) on white paints about 1.25:1, not the 21:1 of opaque black.
        page = 'rgb(255, 255, 255)'
        for colour, alpha in (('rgba(0, 0, 0, 0.1)', 1), ('rgba(0, 0, 0, 0.5)', 0.2), ('rgba(0, 0, 0, 0.1)', 0.1)):
            with self.subTest(colour=colour, alpha=alpha):
                paint = [{'kind': 'fill', 'colour': colour, 'alpha': alpha, 'count': 2}]
                lines = assets.inline_paint_failures('l.svg', page, paint)
                self.assertEqual(len(lines), 1)
                self.assertIn(colour, lines[0])
        faint = assets.inline_paint_failures(
            'l.svg', page, [{'kind': 'fill', 'colour': 'rgba(0, 0, 0, 0.1)', 'alpha': 1, 'count': 1}])
        self.assertIn('1.2', faint[0], 'the ratio reported is the composited one')

    def test_a_translucent_colour_that_still_reaches_the_bar_passes(self):
        paint = [{'kind': 'stroke', 'colour': 'rgba(0, 0, 0, 0.8)', 'alpha': 1, 'count': 1},
                 {'kind': 'fill', 'colour': 'rgba(0, 0, 0, 0.8)', 'alpha': 0.9, 'count': 1}]
        self.assertEqual(assets.inline_paint_failures('l.svg', 'rgb(255, 255, 255)', paint), [])

    def test_a_blank_render_fails_instead_of_passing_vacuously(self):
        self.assertIn('blank', assets.image_paint_failures('l.svg', 'rgb(255, 255, 255)',
                                                           {'painted': 0, 'total': 100, 'colours': {}})[0])
        self.assertIn('no fill or stroke', assets.inline_paint_failures('l.svg', 'rgb(255, 255, 255)', [])[0])

    def test_only_colours_covering_enough_pixels_count_as_painted(self):
        reading = {'painted': 5000, 'total': 20000, 'colours': {'rgb(250, 250, 250)': 3, 'rgb(0, 0, 0)': 900}}
        self.assertEqual(assets.image_paint_failures('l.svg', 'rgb(255, 255, 255)', reading), [])


if __name__ == '__main__':
    unittest.main()
