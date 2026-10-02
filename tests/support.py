"""Shared Playwright test harness (development only).

Environment:
  FKS_ENGINES                comma list of engines to run (default: chromium,firefox)
  FKS_CHROMIUM_EXECUTABLE    optional explicit Chromium binary
  FKS_FIREFOX_EXECUTABLE     optional explicit Firefox binary
"""

import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / 'font_kit_studio_v0.1.1.html'
ENGINES = tuple(e.strip() for e in os.environ.get('FKS_ENGINES', 'chromium,firefox').split(',') if e.strip())


def launch(runtime, engine, **options):
    executable = os.environ.get(f'FKS_{engine.upper()}_EXECUTABLE')
    if executable:
        options.setdefault('executable_path', executable)
    return getattr(runtime, engine).launch(**options)


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
