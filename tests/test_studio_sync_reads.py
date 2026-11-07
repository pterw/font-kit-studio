"""Sync to Live App reads the composition by what a slot is, not by where it sits."""

import unittest

from support import ENGINES
from test_studio_live import LiveCase

FRAUNCES = '"Fraunces", serif'
JETBRAINS_MONO = '"JetBrains Mono", monospace'


class StudioSyncReadsTests(LiveCase):
    def composition_updates(self, frame):
        return [update for update in self.updates(frame) if 'targetId' not in update]

    def wait_updates(self, page, frame, count):
        for _ in range(100):
            if len(self.updates(frame)) >= count:
                break
            page.wait_for_timeout(50)
        self.assertEqual(len(self.updates(frame)), count)

    def test_display_token_ignores_a_row_placed_first(self):
        """Given the first text slot set to another family, when a Row is moved to the top and Sync runs,
        then the display token still carries that family's stack, not the Row's fallback."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, errors = self.open(engine)
                self.wait_connected(page)
                frame = self.frame(page)
                page.locator('#viewSpecimenCanvas').click()
                page.locator('#composerCanvas > .flow-slot').first.click(position={'x': 3, 'y': 3})
                page.locator('#slotInspector [data-bind="family"]').select_option('jetbrains-mono')
                page.locator('#btnSyncToApp').click()
                self.wait_updates(page, frame, 1)
                for _ in range(2):
                    page.locator('#composerCanvas > .flow-slot:has(.row-layout) button[title="Move up"]').click()
                self.wait_updates(page, frame, 3)
                page.locator('#btnSyncToApp').click()
                self.wait_updates(page, frame, 4)
                tokens = [update['patch']['tokens']['--font-display'] for update in self.composition_updates(frame)]
                self.assertNotEqual(tokens[0], FRAUNCES, 'the control must differ from the Row-without-family fallback')
                self.assertEqual(tokens[0], JETBRAINS_MONO, 'the control must carry the chosen family stack')
                self.assertEqual(tokens[-1], JETBRAINS_MONO)
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
