"""Shared Playwright test harness (development only).

Environment:
  FKS_ENGINES                comma list of engines to run: chromium, firefox, webkit
                             (default: chromium; Firefox runs the canary in
                             firefox_canary.py, D037). An empty or unknown list is an
                             error at import: a loop over no engines passes without a browser.
  FKS_CHROMIUM_EXECUTABLE    optional explicit Chromium binary
  FKS_FIREFOX_EXECUTABLE     optional explicit Firefox binary

Tests take the Playwright driver from shared_runtime() and never call sync_playwright()
themselves: a second sync driver in the same process fails ("Sync API inside the asyncio
loop") whenever the shared one is live, so it would pass or fail with the module order.
"""

import atexit
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / 'font_kit_studio_v0.1.1.html'
KNOWN_ENGINES = ('chromium', 'firefox', 'webkit')


def parse_engines(value):
    names = tuple(name.strip().lower() for name in value.split(',') if name.strip())
    if not names:
        raise RuntimeError(f'FKS_ENGINES selects no browser engine (got {value!r}); '
                           f'use a comma list of {", ".join(KNOWN_ENGINES)} or unset it')
    unknown = [name for name in names if name not in KNOWN_ENGINES]
    if unknown:
        raise RuntimeError(f'FKS_ENGINES has an unknown engine: {", ".join(unknown)}; '
                           f'allowed: {", ".join(KNOWN_ENGINES)}')
    return names


ENGINES = parse_engines(os.environ.get('FKS_ENGINES', 'chromium'))


def launch(runtime, engine, **options):
    executable = os.environ.get(f'FKS_{engine.upper()}_EXECUTABLE')
    if executable:
        options.setdefault('executable_path', executable)
    return getattr(runtime, engine).launch(**options)


# One Playwright driver and one browser per engine for the whole test process. Launching costs
# about half a second per test, so the base classes borrow these and give every test its own
# context (cookies, storage and permissions stay per test). Tests that need their own browser
# keep calling launch(shared_runtime(), engine) and close it themselves.
_shared = {'runtime': None, 'browsers': {}}


def shared_runtime():
    """The process-wide Playwright driver, started on first use and stopped at interpreter exit."""
    if _shared['runtime'] is None:
        from playwright.sync_api import sync_playwright
        _shared['runtime'] = sync_playwright().start()
    return _shared['runtime']


def shared_browser(engine):
    """The process-wide browser for `engine`; a disconnected or crashed one is relaunched."""
    browser = _shared['browsers'].get(engine)
    if browser is None or not browser.is_connected():
        browser = _shared['browsers'][engine] = launch(shared_runtime(), engine)
    return browser


def new_context(engine, **options):
    """A fresh context in the shared browser. The caller closes it (see close_contexts).

    After a browser crash is_connected() can stay True until Playwright dispatches the event, so
    a Playwright error that means the browser or target is gone replaces the cached browser and
    retries once; a second failure is the caller's. Any other error (a bad option, say) propagates
    at once: it must not close a healthy browser that earlier contexts of the same test use.
    """
    from playwright.sync_api import Error
    browser = shared_browser(engine)
    try:
        return browser.new_context(**options)
    except Error as error:
        if browser.is_connected() and 'closed' not in str(error).lower():
            raise
    _shared['browsers'].pop(engine, None)
    try:
        browser.close()
    except Exception:
        pass  # already gone
    return shared_browser(engine).new_context(**options)


def close_contexts(contexts):
    """Close a test's contexts and clear the list.

    A context whose browser already went away (a crash the test caused) is not an error. A failure
    on a connected browser is: every context is still closed, then the first such error is raised.
    """
    first_error = None
    for context in contexts:
        try:
            context.close()
        except Exception as error:
            browser = context.browser
            if browser is not None and browser.is_connected() and first_error is None:
                first_error = error
    contexts.clear()
    if first_error is not None:
        raise first_error


def _close_shared():
    for browser in _shared['browsers'].values():
        try:
            browser.close()
        except Exception:
            pass  # already gone
    _shared['browsers'].clear()
    if _shared['runtime'] is not None:
        try:
            _shared['runtime'].stop()
        except Exception:
            pass
        _shared['runtime'] = None


atexit.register(_close_shared)


def route_virtual_origins(context, mapping):
    """Serve local directories at fake origins, e.g. {'http://studio.test': REPO}.

    Gives real cross-origin iframes without a network server. Unknown paths 404.
    """
    def make_handler(root):
        def handler(route, request=None):
            path = unquote(urlsplit(route.request.url).path).lstrip('/') or 'index.html'
            target = (root / path).resolve()
            if target.is_dir():
                target = target / 'index.html'
            if root not in target.parents and target != root or not target.is_file():
                route.fulfill(status=404, body='not found')
                return
            kind = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            route.fulfill(status=200, body=target.read_bytes(), headers={'content-type': kind})
        return handler

    for origin, root in mapping.items():
        context.route(f'{origin}/**', make_handler(Path(root).resolve()))
