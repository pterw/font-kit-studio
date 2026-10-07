"""Firefox canary: the few browser tests CI runs on Gecko (D037).

The full suite runs on Chromium only. Gecko gets a short canary of the
places an engine difference would hurt most: the bridge's trust boundary
(hostile frames, forged sessions and versions, handshake, origin list,
session lifecycle, targeted updates), real Studio
against the real bridge in a cross-origin frame (edit, code panel, sync,
reload), and Studio's own rendering. The frontend gate covers layout,
contrast, privacy and the live edit flow on Firefox separately.

The file name does not match `test*.py`, so `discover` never collects it.
Run it with:

    PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v

`test_support.CanaryListTest` fails the Chromium suite when a name here no
longer loads, so a renamed class cannot quietly empty the canary.
"""

CANARY = (
    'test_bridge_runtime.ConfirmedDefectTests',
    'test_bridge_runtime.HandshakeTests',
    'test_bridge_runtime.OriginListTests',
    'test_bridge_runtime.SessionLifecycleTests',
    'test_bridge_runtime.TargetedUpdateTests',
    'test_live_integration.EditAndCodePanelTests',
    'test_live_integration.SyncAndReloadTests',
    'test_font_kit_studio_v011.BrowserCase',
    'test_localhost_cookies.LocalhostCookiesTest',
)


def load_tests(loader, standard_tests, pattern):
    return loader.loadTestsFromNames(CANARY)
