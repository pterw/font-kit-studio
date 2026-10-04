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


# What Studio derives from the canvas width instead of from the composition. syncRowLayouts() runs after every render,
# on window resize and from a ResizeObserver on the canvas: a row at or below its collapseAt gets the is-collapsed class
# and one 1fr track, a wider row gets its ratios as tracks. The canvas is hidden (width 0) until the Composer is shown,
# so every row starts collapsed and expands a frame after the Composer opens. Add to these lists when the canvas markup
# gains another width-derived class or inline style; test_support sweeps widths to catch one that is missing.
WIDTH_DERIVED_CLASSES = ('is-collapsed',)
WIDTH_DERIVED_STYLES = ('grid-template-columns',)

_CANVAS_SNAPSHOT = '''(canvas, derived) => {
    const copy = canvas.cloneNode(true);
    for (const node of [copy, ...copy.querySelectorAll('*')]) {
        for (const name of derived.classes) {
            if (!node.classList.contains(name)) continue;
            node.classList.remove(name);
            if (!node.classList.length) node.removeAttribute('class');
        }
        for (const name of derived.styles) {
            if (!node.style.getPropertyValue(name)) continue;
            node.style.removeProperty(name);
            if (!node.getAttribute('style').trim()) node.removeAttribute('style');
        }
    }
    return copy.outerHTML;
}'''


def canvas_snapshot(page):
    """The canvas markup as the composition describes it, without what its current width derives.

    Compare this, not the raw `inner_html()`, when a test asserts that an action did or did not touch the canvas. The raw
    markup also changes with the width alone (see WIDTH_DERIVED_CLASSES), so a snapshot read in the frame before the
    ResizeObserver ran differs from the settled one although nothing was edited. Slot ids, text and every other style stay
    in the result, so a real re-render (Apply regenerates the ids) still changes it. So does the canvas element's own
    declared style (its width and background): it follows the composition, not the layout width, so a leaked canvas
    width or colour is seen at any width, not only when it happens to flip a row's collapse. The row's ratios are dropped
    with its tracks: a collapsed row no longer carries them in the DOM, so assert ratios through the JSON export.
    """
    return page.locator('#composerCanvas').evaluate(
        _CANVAS_SNAPSHOT, {'classes': list(WIDTH_DERIVED_CLASSES), 'styles': list(WIDTH_DERIVED_STYLES)})
