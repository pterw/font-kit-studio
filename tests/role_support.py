"""Authenticated role fixtures around the real bridge; legacy harness is unchanged."""
import re
from urllib.parse import quote, unquote, urlsplit

from support import REPO, new_context, route_virtual_origins
from test_bridge_runtime import BridgeCase, ERROR_PROBE, FIXTURES, STUDIO, TARGET, EVIL

ROLE_PAGE = TARGET + '/tests/fixtures/bridge/target-role-protocol.html'
HTTPS = re.compile(r'^https://', re.I)


class RoleBridgeCase(BridgeCase):
    @classmethod
    def setUpClass(cls):
        pass  # open borrows the existing process-wide browser through new_context.

    @classmethod
    def tearDownClass(cls):
        pass

    def open(self, engine, host=STUDIO, target=ROLE_PAGE, headers=None, bridge_source=None):
        context = new_context(engine, viewport={'width': 1500, 'height': 1000})
        self.addCleanup(context.close)
        context.add_init_script(ERROR_PROBE)
        route_virtual_origins(context, {STUDIO: FIXTURES, EVIL: FIXTURES, TARGET: REPO})
        counts = {'abort': 0, 'fallback': 0}

        def fallback(route):
            counts['fallback'] += 1
            route.fulfill(status=200, body='local', headers={'access-control-allow-origin': '*'})

        def abort(route):
            counts['abort'] += 1
            route.abort()

        context.route(HTTPS, fallback)
        context.route(HTTPS, abort)
        canary = context.new_page()
        try:
            results = [canary.evaluate('(url) => fetch(url).then(() => "fulfilled", () => "blocked")', url)
                       for url in ('https://isolation.invalid/', 'https://fonts.googleapis.com/css2?family=Local')]
            self.assertEqual(counts, {'abort': 2, 'fallback': 0}, str(results))
            self.assertEqual(results, ['blocked', 'blocked'])
        finally:
            canary.close()

        # Only the exact role-test target document receives an external script tag.
        # Meta/header CSP remains intact and can refuse it normally.
        def document_route(route):
            path = (REPO / unquote(urlsplit(route.request.url).path).lstrip('/')).resolve()
            self.assertTrue(REPO.resolve() in path.parents)
            data = path.read_bytes()
            if b'fontkit-bridge.js' not in data:
                data = data.replace(b'</body>', b'<script src="/fontkit-bridge.js"></script></body>')
            route.fulfill(status=200, body=data, headers={'content-type': 'text/html', **(headers or {})})

        context.route(target, document_route)
        if bridge_source is not None:
            context.route(TARGET + '/fontkit-bridge.js', lambda route: route.fulfill(
                status=200, body=bridge_source, content_type='application/javascript'))
        page = context.new_page()
        page.goto(host + '/host-roles.html?target=' + quote(target, safe=''))
        frame = next(f for f in page.frames if f.url.startswith(TARGET))
        self.assertEqual(counts, {'abort': 2, 'fallback': 0})
        return page, frame

    def detect(self, page, **extra):
        return self.request(page, {'type': 'design:detect', **extra})
