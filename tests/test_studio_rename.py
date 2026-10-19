"""Studio opens directly at fontkit-studio.html; the old name is gone (D052)."""
import unittest

from playwright.sync_api import Error

from support import ENGINES, HTML, REPO, close_contexts, new_context

OLD = REPO / 'font_kit_studio_v0.1.1.html'


class StudioFileName(unittest.TestCase):
    def setUp(self):
        self.contexts = []

    def tearDown(self):
        close_contexts(self.contexts)

    def new_page(self, engine):
        context = new_context(engine)
        self.contexts.append(context)
        return context.new_page()

    def test_new_name_opens_directly_and_keeps_query_and_hash(self):
        """Given Studio's file with a query and a hash, when it is opened,
        then the page URL equals the file URL plus that suffix at once and
        the title starts 'Font Kit Studio v'."""
        suffix = '?target=http%3A%2F%2Flocalhost%3A9%2F&x=1#composer'
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.new_page(engine)
                page.goto(HTML.as_uri() + suffix)
                self.assertEqual(page.url, HTML.as_uri() + suffix)
                self.assertTrue(page.title().startswith('Font Kit Studio v'))

    def test_new_name_opens_without_query(self):
        """Given the bare file URL of Studio, when it is opened, then the
        page URL equals that file URL and the title starts
        'Font Kit Studio v'."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.new_page(engine)
                page.goto(HTML.as_uri())
                self.assertEqual(page.url, HTML.as_uri())
                self.assertTrue(page.title().startswith('Font Kit Studio v'))

    def test_old_name_is_absent_and_does_not_load(self):
        """Given the old file name font_kit_studio_v0.1.1.html, when the tree
        is checked and each engine opens it, then the file does not exist
        and the navigation raises a load error."""
        self.assertFalse(OLD.exists())
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.new_page(engine)
                with self.assertRaises(Error):
                    page.goto(OLD.as_uri())
