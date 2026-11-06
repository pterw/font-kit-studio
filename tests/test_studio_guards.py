"""Studio guards: an import that names a font the library lacks says so (v0.4.1 Task 9, row S08).

The fallback itself is pinned elsewhere (test_studio_live: an unknown family imports as the first library font);
these tests guard only that the replacement is no longer silent, and that it stays quiet when no family is lost.

Run one module by name with PYTHONPATH=tests:  python -m unittest test_studio_guards
"""

import unittest

from support import ENGINES

from test_studio_import_link import STATUS, ImportLinkCase

PLAIN = 'Composition imported. Image assets must be reselected.'
GHOST = 'ghost-face is not in the library, so the first library font is used.'


def text(family=None, **fields):
    slot = {'type': 'text', **fields}
    if family is not None:
        slot['family'] = family
    return slot


def document(*slots):
    return {'version': '0.1.0', 'composition': {'slots': list(slots)}}


class UnknownFamilyImportTests(ImportLinkCase):
    def imported(self, engine, *slots):
        page, errors = self.open(engine, query=False)
        page.locator('#modeComposer').click()
        status = self.import_document(page, document(*slots))
        return page, errors, status

    def test_an_unknown_family_is_named_once_and_the_first_library_font_is_used(self):
        """Given two slots naming ghost-face, when imported, then the status names it once and both export fraunces."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, status = self.imported(engine, text('ghost-face'), text('ghost-face'))
                self.assertEqual(status, f'{PLAIN} {GHOST}')
                self.assertEqual([s['family'] for s in self.export(page)['composition']['slots']], ['fraunces', 'fraunces'])
                self.assertEqual(errors, [])

    def test_a_row_child_is_named_and_distinct_families_follow_first_seen_order(self):
        """Given a top-level slot and a row child with different unknown families, then both are named in file order."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                row = {'type': 'row', 'childCount': 2, 'children': [text('row-ghost'), text('inter')]}
                _, errors, status = self.imported(engine, text('ghost-face'), row)
                self.assertEqual(status, f'{PLAIN} {GHOST} row-ghost is not in the library, so the first library font is used.')
                self.assertEqual(errors, [])

    def test_a_row_child_cut_by_the_row_count_is_not_named(self):
        """Given a row of two whose third child names an unknown family, then the cut child is not reported."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                row = {'type': 'row', 'childCount': 2, 'children': [text('inter'), text('inter'), text('cut-ghost')]}
                _, errors, status = self.imported(engine, row)
                self.assertEqual(status, PLAIN)
                self.assertEqual(errors, [])

    def test_no_warning_when_no_family_is_lost(self):
        """Given a library family, a legacy key, no family, a non-string and an empty family, then the status is unchanged."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors, status = self.imported(
                    engine, text('inter'), text('gotham'), text(), text(7), text(''))
                self.assertEqual(status, PLAIN)
                self.assertEqual(errors, [])

    def test_the_warning_follows_the_linked_import_status_too(self):
        """Given a linked Studio, when an import names ghost-face, then the link-off status carries the sentence."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, _, errors = self.linked_page(engine)
                status = self.import_document(page, document(text('ghost-face')))
                self.assertEqual(status, f'{STATUS} {GHOST}')
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
