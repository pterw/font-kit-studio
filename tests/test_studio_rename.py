"""The old Studio file name forwards to fontkit-studio.html for one release (D041)."""
import unittest

from support import ENGINES, HTML, REPO, close_contexts, new_context

OLD = REPO / 'font_kit_studio_v0.1.1.html'


class OldNameForwards(unittest.TestCase):
    def setUp(self):
        self.contexts = []

    def tearDown(self):
        close_contexts(self.contexts)

    def open_old(self, engine, suffix):
        context = new_context(engine)
        self.contexts.append(context)
        page = context.new_page()
        page.goto(OLD.as_uri() + suffix)
        page.wait_for_url(lambda url: '/fontkit-studio.html' in url)
        return page

    def test_forwards_with_query_and_hash(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                suffix = '?target=http%3A%2F%2Flocalhost%3A9%2F&x=1#composer'
                page = self.open_old(engine, suffix)
                self.assertEqual(page.url, HTML.as_uri() + suffix)
                self.assertTrue(page.title().startswith('Font Kit Studio v'))

    def test_forwards_without_query(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_old(engine, '')
                self.assertEqual(page.url, HTML.as_uri())

    def test_stub_is_small_and_names_the_new_file(self):
        text = OLD.read_text(encoding='utf-8')
        self.assertLess(len(text.splitlines()), 20)
        self.assertIn('location.replace("fontkit-studio.html" + location.search + location.hash)', text)
        self.assertIn('<a href="fontkit-studio.html">', text)
