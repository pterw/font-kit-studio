"""Helpers for tests that run against the Vite fixtures under fixtures/.

Deliberately does not import `support`: that module starts Playwright.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / 'fixtures'


def require_fixture(test_case, name):
    """Skip the test when fixtures/<name>/node_modules is missing; fail instead when
    FKS_REQUIRE_FIXTURES=1 (CI), so a fixture test can never pass by skipping."""
    if (FIXTURES / name / 'node_modules').is_dir():
        return
    if os.environ.get('FKS_REQUIRE_FIXTURES') == '1':
        test_case.fail(
            f'fixtures/{name}/node_modules is missing and FKS_REQUIRE_FIXTURES=1: '
            f'run npm ci in fixtures/{name}'
        )
    test_case.skipTest(f'run npm ci in fixtures/{name}')


def vite_bin(name):
    return FIXTURES / name / 'node_modules' / 'vite' / 'bin' / 'vite.js'
