"""Rendered inputs for R2 React adapters; role preview belongs to F2b.

The literal oracle describes authored semantic selectors, not a compiler's hash
algorithm. CSS updates are HMR, not React Fast Refresh. Every browser uses an
isolated source copy and an offline HTTPS guard proved on a separate canary page.
"""

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import quote
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from fixture_support import FIXTURES, REPO, require_fixture, vite_bin
from support import ENGINES, new_context

FIXTURE_NAME = 'vite-react-css-modules'
FIXTURE = FIXTURES / FIXTURE_NAME
NODE = shutil.which('node')
HTTPS = re.compile(r'^https://')
SIGNATURE = """el => {
    const s = getComputedStyle(el), size = parseFloat(s.fontSize);
    return {
        fontFamily: s.fontFamily.trim().replace(/\\s+/g, ' '),
        fontSize: Math.round(size * 100) / 100,
        fontWeight: Math.round(Number(s.fontWeight)),
        textTransform: s.textTransform,
        letterSpacing: s.letterSpacing === 'normal' ? 0
            : Math.round(parseFloat(s.letterSpacing) / size * 10000) / 10000
    };
}"""
ELEMENTS = {
    'title': '[data-design-id="modules.title"]', 'first': '[data-design-id="modules.body.first"]',
    'second': '[data-design-id="modules.body.second"]', 'hash': 'aside > p', 'stable': 'p.stable-copy',
    'action': '[data-design-id="modules.replace"]'}
OWNED = "Array.from(document.querySelectorAll('#fontkit-role-styles'), s => s.textContent)"
STYLE_ATTRIBUTES = "document.querySelectorAll('[style]').length"
DISPLAY = {'fontFamily': 'Georgia, serif', 'fontWeight': 700}
BODY = {'fontFamily': 'Verdana, sans-serif', 'letterSpacing': 0.05}
HASH_ONLY = {'fontFamily': '"Courier New", monospace', 'fontSize': 15}
DISPLAY_CSS = '[data-design-role="display"] {\n  font-family: Georgia, serif;\n  font-weight: 700;\n}\n'
BODY_CSS = ('[data-design-id="modules.body.first"], [data-design-id="modules.body.second"] {\n'
            '  font-family: Verdana, sans-serif;\n  letter-spacing: 0.05em;\n}\n')
HASH_CSS = '{} {{\n  font-family: "Courier New", monospace;\n  font-size: 15px;\n}}\n'
EMPTY_HASH = '811c9dc5'
BRIDGE_ORIGIN_SCRIPT = """(() => {
    if (location.origin !== %s) return;
    addEventListener('DOMContentLoaded', () => {
        const script = document.createElement('script');
        script.src = '/fontkit-bridge.js';
        document.body.append(script);
    });
})();"""
# Hold the frame callbacks so the bridge measures from its 250 ms timer, and stamp the three moments of the premise.
HOLD_FRAMES = """() => {
    const stamps = window.stamps = {}, real = window.requestAnimationFrame, held = [];
    window.requestAnimationFrame = callback => held.push(callback);
    new MutationObserver(() => { if (stamps.hmr === undefined) stamps.hmr = performance.now(); })
        .observe(document.querySelector('style[data-vite-dev-id]'),
                 {childList: true, characterData: true, subtree: true});
    window.addEventListener('message', event => {
        if (!event.data || event.data.type !== 'design:roles-apply') return;
        stamps.commit = performance.now();
        window.requestAnimationFrame = real;
        setTimeout(() => { stamps.deadline = performance.now(); }, 250);
    });
}"""


def fnv1a32(text):
    value = 2166136261
    for byte in text.encode('utf-8'):
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return '%08x' % value


def role(identifier, name, selectors, **properties):
    return {'id': identifier, 'name': name, 'selectors': selectors, 'adapter': 'plain', 'properties': properties}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class FixtureInstallContractTest(unittest.TestCase):
    def test_existing_install_check_fails_closed_when_required(self):
        with tempfile.TemporaryDirectory() as directory:
            # Filesystem/environment seams of the existing helper, not a replacement wrapper.
            with patch('fixture_support.FIXTURES', Path(directory)), patch.dict(
                    os.environ, {'FKS_REQUIRE_FIXTURES': '1'}):
                with self.assertRaisesRegex(AssertionError, 'node_modules is missing'):
                    require_fixture(self, FIXTURE_NAME)


class ReactCorpusTest(unittest.TestCase):
    def start_vite(self, project):
        self.assertIsNotNone(NODE, 'node is required for the installed React corpus')
        flags = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {}
        proc = subprocess.Popen(
            [NODE, str(vite_bin(FIXTURE_NAME)), '--host', '127.0.0.1', '--port', '0'],
            cwd=project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', **flags)
        lines, output = queue.Queue(), []

        def pump():
            for line in proc.stdout:
                clean = re.sub(r'\x1b\[[0-9;]*m', '', line).strip()
                output.append(clean)
                lines.put(clean)

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    line = lines.get(timeout=max(0, deadline - time.monotonic()))
                except queue.Empty:
                    self.fail('Vite did not advertise its local URL:\n' + '\n'.join(output))
                found = re.search(r'Local:\s+(http://127\.0\.0\.1:(\d+)/)', line)
                if found:
                    return proc, reader, found[1], int(found[2])
        except BaseException:
            self.stop_vite(proc, reader)
            raise

    def stop_vite(self, proc, reader, port=None):
        try:
            if proc.poll() is None:
                proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                    self.fail('owned Vite process did not stop on interrupt')
            reader.join(timeout=5)
            self.assertFalse(reader.is_alive(), 'owned output reader did not stop')
            if port is not None:
                with socket.socket() as sock:
                    sock.settimeout(2)
                    self.assertNotEqual(sock.connect_ex(('127.0.0.1', port)), 0,
                                        'owned Vite listener still accepts connections')
        finally:
            proc.stdout.close()

    def guarded_context(self, engine, **options):
        context = new_context(engine, **options)
        counts = {'aborted': 0, 'fallback': 0}

        def local_fallback(route):
            counts['fallback'] += 1
            route.fulfill(status=200, content_type='text/plain', body='local fallback',
                          headers={'access-control-allow-origin': '*'})

        def abort_https(route):
            counts['aborted'] += 1
            route.abort()

        # Keep this earlier route installed even when the later guard is mutated out.
        context.route(HTTPS, local_fallback)
        context.route(HTTPS, abort_https)
        try:
            canary = context.new_page()
            try:
                results = []
                for url in ('https://offline-canary.invalid/',
                            'https://fonts.googleapis.com/css2?family=Fixture&display=swap'):
                    results.append(canary.evaluate(
                        '(url) => fetch(url).then(() => "fulfilled", () => "blocked")', url))
                self.assertEqual(counts['aborted'], 2,
                                 f'HTTPS-prefix guard must intercept both canaries: {counts}, {results}')
                self.assertEqual(results, ['blocked', 'blocked'])
                self.assertEqual(counts['fallback'], 0, 'the abort guard must take precedence')
            finally:
                canary.close()
            return context, counts
        except BaseException:
            context.close()
            raise

    def start_host(self):
        handler = partial(QuietHandler, directory=str(REPO / 'tests' / 'fixtures' / 'bridge'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def stop_host(self, server, thread):
        port = server.server_address[1]
        try:
            server.shutdown()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive(), 'owned host server did not stop')
        finally:
            server.server_close()
        with socket.socket() as sock:
            sock.settimeout(2)
            self.assertNotEqual(sock.connect_ex(('127.0.0.1', port)), 0,
                                'owned host listener still accepts connections')

    def bridge_source(self):
        """The bridge bytes served to the app; a mutant runner overrides this and nothing else."""
        return (REPO / 'fontkit-bridge.js').read_bytes()

    @contextmanager
    def app(self, engine):
        with self.session(engine) as (page, project, _):
            yield page, project

    @contextmanager
    def role_app(self, engine):
        """The app in an owned loopback host with the real bridge: hello sent, interact mode, first Detect read."""
        with self.session(engine, host=True) as (page, project, frame):
            origin = frame.evaluate('location.origin')
            page.evaluate("(o) => waitFor((d, e) => e.fromTarget && e.origin === o && d.type === 'design:bridge-ready')",
                          origin)
            page.evaluate('hello()')
            page.evaluate("control({type: 'design:mode', mode: 'interact'})")
            first = self.detect(page)
            yield page, frame, project, first

    @contextmanager
    def session(self, engine, host=False):
        require_fixture(self, FIXTURE_NAME)
        original = {path.relative_to(FIXTURE): path.read_bytes()
                    for path in FIXTURE.rglob('*') if path.is_file()
                    and not any(part in ('.git', 'node_modules', 'dist') for part in path.parts)
                    and not any(part.startswith('.fks-') for part in path.parts)}
        with tempfile.TemporaryDirectory(prefix='.fks-', dir=FIXTURE) as directory:
            project = Path(directory)
            for relative, data in original.items():
                target = project / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            proc, reader, url, port = self.start_vite(project)
            server = thread = None
            try:
                context, counts = self.guarded_context(engine, **({'viewport': {'width': 1500, 'height': 1000}}
                                                                  if host else {}))
                try:
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    frame = None
                    if host:
                        # Playwright fulfils neither document: Vite's WebSocket and the iframe need real loopback ones.
                        origin = url.rstrip('/')
                        context.add_init_script(BRIDGE_ORIGIN_SCRIPT % json.dumps(origin))
                        context.route(origin + '/fontkit-bridge.js', lambda route: route.fulfill(
                            status=200, body=self.bridge_source(), content_type='application/javascript'))
                        server, thread = self.start_host()
                        page.goto(f'http://127.0.0.1:{server.server_address[1]}/host-roles.html?target='
                                  + quote(url, safe=''))
                        frame = page.locator('#target').element_handle().content_frame()
                    else:
                        page.goto(url)
                    (frame or page).locator('h1').wait_for()
                    yield page, project, frame
                    self.assertEqual(errors, [], 'fixture must render without runtime errors')
                    self.assertEqual(counts, {'aborted': 2, 'fallback': 0}, 'app needs no HTTPS request')
                finally:
                    context.close()
            finally:
                try:
                    if server is not None:
                        self.stop_host(server, thread)
                finally:
                    self.stop_vite(proc, reader, port)
                for relative, data in original.items():
                    self.assertEqual((FIXTURE / relative).read_bytes(), data, 'shared fixture source changed')

    def oracle(self):
        data = json.loads((FIXTURE / 'expected-styles.json').read_text(encoding='utf-8'))
        self.assertEqual((data['schema'], data['version']), ('fontkit-fixture-styles', 1))
        return data['styles']

    def assert_styles(self, page):
        for expected in self.oracle():
            with self.subTest(style=expected['name']):
                elements = page.locator(expected['selector'])
                self.assertEqual(elements.count(), expected['count'])
                for index in range(expected['count']):
                    self.assertEqual(elements.nth(index).evaluate(SIGNATURE), expected['style'])

    def test_rendered_styles_match_the_independent_literal_oracle(self):
        for engine in ENGINES:
            with self.subTest(engine=engine), self.app(engine) as (page, _):
                self.assert_styles(page)

    def test_author_bindings_module_classes_and_stable_class_are_distinct_inputs(self):
        bindings = json.loads((FIXTURE / 'expected-styles.json').read_text(encoding='utf-8'))['bindings']
        for engine in ENGINES:
            with self.subTest(engine=engine), self.app(engine) as (page, _):
                for binding in bindings:
                    elements = page.locator(binding['selector'])
                    self.assertEqual(elements.count(), len(binding['authorIds']))
                    for index, author_id in enumerate(binding['authorIds']):
                        element = elements.nth(index)
                        self.assertEqual(element.get_attribute('data-design-id'), author_id)
                        self.assertEqual(element.get_attribute('data-design-role'), binding['authorRole'])
                        classes = element.evaluate('el => [...el.classList]')
                        self.assertEqual(len(classes), 1)
                        if 'stableClass' in binding:
                            self.assertEqual(classes, [binding['stableClass']])
                        else:
                            # Observe an uncertain generated binding; never predict Vite's hash algorithm.
                            self.assertNotEqual(classes[0], binding['sourceClass'])
                            self.assertNotEqual(classes[0], 'stable-copy')
                            self.assertEqual(page.evaluate(
                                'name => document.querySelectorAll("." + CSS.escape(name)).length',
                                classes[0]), elements.count())
                self.assert_styles(page)

    def test_keyboard_state_update_replaces_real_react_nodes_and_keeps_fonts(self):
        for engine in ENGINES:
            with self.subTest(engine=engine), self.app(engine) as (page, _):
                title = page.locator('[data-design-id="modules.title"]')
                first = page.locator('[data-design-id="modules.body.first"]')
                button = page.get_by_role('button', name='Replace text', exact=True)
                for generation, key in ((1, 'Enter'), (2, 'Space')):
                    old_elements = [title.element_handle(), first.element_handle()]
                    old_text = [element.evaluate_handle('el => el.firstChild') for element in old_elements]
                    try:
                        button.focus()
                        button.press(key)
                        page.wait_for_function(
                            '(n) => document.querySelector("h1").textContent === "Module title " + n',
                            arg=generation, timeout=3000)
                        self.assertEqual(title.text_content(), f'Module title {generation}')
                        self.assertEqual(first.text_content(), f'Body copy {generation}')
                        for old in old_elements + old_text:
                            self.assertFalse(old.evaluate('node => node.isConnected'))
                        self.assert_styles(page)
                    finally:
                        for handle in old_elements + old_text:
                            handle.dispose()

    def test_css_module_hot_update_changes_computed_font_without_losing_app_state(self):
        for engine in ENGINES:
            with self.subTest(engine=engine), self.app(engine) as (page, project):
                self.assert_styles(page)
                page.get_by_role('button', name='Replace text', exact=True).press('Enter')
                page.wait_for_function('document.querySelector("h1").textContent === "Module title 1"')
                page.evaluate('window.__r2HmrMarker = "same document"')
                css = project / 'src' / 'App.module.css'
                original = css.read_bytes()
                changed = original.replace(b'font-size: 40px;', b'font-size: 44px;')
                self.assertNotEqual(changed, original, 'the scratch title declaration must change')
                old_title = page.locator('h1').element_handle()
                try:
                    css.write_bytes(changed)
                    page.wait_for_function(
                        'getComputedStyle(document.querySelector("h1")).fontSize === "44px"', timeout=10000)
                    self.assertEqual(page.evaluate('window.__r2HmrMarker'), 'same document', 'CSS HMR must not reload')
                    self.assertTrue(old_title.evaluate('node => node.isConnected'), 'CSS HMR must retain the React node')
                    self.assertEqual(page.locator('h1').text_content(), 'Module title 1')
                    self.assertEqual(page.locator('[data-design-id="modules.body.first"]').text_content(), 'Body copy 1')
                    self.assertEqual(page.locator('p.stable-copy').inner_text(), 'Stable class comparison')
                    self.assertEqual(page.locator('h1').evaluate(SIGNATURE), {
                        'fontFamily': 'serif', 'fontSize': 44, 'fontWeight': 600,
                        'textTransform': 'uppercase', 'letterSpacing': 0.02})
                finally:
                    try:
                        self.restore_css(page, css, original)
                    finally:
                        old_title.dispose()
                self.assert_styles(page)

    def restore_css(self, target, css, original):
        # Vite coalesces changes to one file inside a short window: an immediate second write can
        # produce no hot update (seen on Windows with Vite 8.3.2). So write again until it arrives.
        # Short waits for the early writes; the last one keeps the old 10 s budget for slow hosts.
        waits = (1000, 1000, 1000, 1000, 10000)
        for wait in waits:
            css.write_bytes(original)
            self.assertEqual(css.read_bytes(), original, 'scratch CSS bytes must be restored')
            try:
                target.wait_for_function(
                    'getComputedStyle(document.querySelector("h1")).fontSize === "40px"', timeout=wait)
                break
            except PlaywrightTimeoutError:
                continue
        else:
            self.fail(f'the restored CSS never hot-updated after {len(waits)} writes; last computed size '
                      + target.evaluate('getComputedStyle(document.querySelector("h1")).fontSize'))

    # Role preview on a real React app (R2.7F2b): the real bridge, an authenticated host, one forward write at most.
    def rows(self):
        return {row['name']: row['style'] for row in self.oracle()}

    def detect(self, page):
        return page.evaluate("request({type: 'design:detect'})")

    def send(self, page, kind, detected, **extra):
        message = {'type': kind, 'documentId': page.evaluate('roleState.documentId'),
                   'pageVersion': detected['pageVersion'], **extra}
        return page.evaluate('(m) => request(m)', message)

    def rendered(self, frame):
        return {name: frame.locator(selector).evaluate(SIGNATURE) for name, selector in ELEMENTS.items()}

    def literal(self):
        rows = self.rows()
        return {'title': rows['display'], 'first': rows['body'], 'second': rows['body'], 'hash': rows['hash-only'],
                'stable': rows['stable-class'], 'action': rows['action']}

    def previewed(self):
        shown = self.literal()
        for name, values in (('title', DISPLAY), ('first', BODY), ('second', BODY), ('hash', HASH_ONLY)):
            shown[name] = {**shown[name], **values}
        return shown

    def group(self, detected, identity):
        found = [group for group in detected['groups'] if group['identity'] == identity]
        self.assertEqual(len(found), 1, f'one group for {identity}: {detected["groups"]}')
        return found[0]

    def preview_roles(self, detected):
        rows = self.rows()
        display = self.group(detected, {'kind': 'author-role', 'name': 'display'})
        body = self.group(detected, {'kind': 'author-role', 'name': 'body'})
        hashed = self.group(detected, {'kind': 'style', 'style': rows['hash-only']})
        return [role('display', 'Display', [display['selectors'][0]['value']], **DISPLAY),
                role('body', 'Body', [binding['value'] for binding in body['selectors']], **BODY),
                role('hash-only', 'Hash only', [hashed['selectors'][0]['value']], **HASH_ONLY)]

    def assert_rejected(self, reply, reason, detail=None):
        self.assertEqual(reply['type'], 'design:rejected', reply)
        self.assertEqual(reply['reason'], reason, reply)
        if detail is not None:
            self.assertEqual(reply['detail'], detail)

    def assert_untouched(self, page, frame, revision, owned, shown):
        self.assertEqual(page.evaluate('revision'), revision)
        self.assertEqual(frame.evaluate(OWNED), owned)
        self.assertEqual(self.rendered(frame), shown)

    def test_detect_groups_five_real_react_roles_and_binds_each_to_its_own_elements(self):
        """Given the real React app under the real bridge, when the host sends hello and a Detect, then the
        reply is complete over 6 scanned elements, four of them carrying data-design-role body, with five groups
        whose identity, counts, baseline rows, selectors and reasons equal the fixture's literals, each bound
        completely with the plain adapter."""
        rows = self.rows()
        for engine in ENGINES:
            with self.subTest(engine=engine), self.role_app(engine) as (page, frame, _, detected):
                self.assertEqual(frame.locator('[data-design-role="body"]').count(), 4)
                self.assertEqual((detected['type'], detected['complete'], detected['scannedElements']),
                                 ('design:detected', True, 6))
                self.assertEqual(len(detected['groups']), 5)
                hashed = self.hash_selector(frame)
                expected = (
                    ({'kind': 'author-role', 'name': 'display'}, 'display', 'display', 'display', 1,
                     [('[data-design-role="display"]', 'author-role', True)]),
                    ({'kind': 'author-role', 'name': 'body'}, 'body', 'body', 'body', 2,
                     [('[data-design-id="modules.body.first"]', 'author-id', True),
                      ('[data-design-id="modules.body.second"]', 'author-id', True)]),
                    ({'kind': 'style', 'style': rows['hash-only']}, 'Text', None, 'hash-only', 1,
                     [(hashed, 'css-module', False)]),
                    ({'kind': 'style', 'style': rows['stable-class']}, 'Text', None, 'stable-class', 1,
                     [('.stable-copy', 'class', True)]),
                    ({'kind': 'style', 'style': rows['action']}, 'Text', None, 'action', 1,
                     [('[data-design-id="modules.replace"]', 'author-id', True)]))
                for identity, name, author_role, row, count, bindings in expected:
                    with self.subTest(group=row):
                        group = self.group(detected, identity)
                        self.assertEqual((group['suggestedName'], group['authorRole'], group['elementCount']),
                                         (name, author_role, count))
                        self.assertEqual(group['signatures'], [{'style': rows[row], 'count': count}])
                        self.assertEqual([(b['value'], b['reason'], b['stable']) for b in group['selectors']], bindings)
                        self.assertTrue(group['bindingComplete'])
                        self.assertEqual(group['adapter'], 'plain')

    def hash_selector(self, frame):
        return '.' + frame.evaluate('name => CSS.escape(name)', frame.locator('aside > p').evaluate('el => el.className'))

    def scratch_css(self, project):
        css = project / 'src' / 'App.module.css'
        original = css.read_bytes()
        changed = original.replace(b'font-size: 40px;', b'font-size: 44px;')
        self.assertNotEqual(changed, original, 'the scratch title declaration must change')
        return css, original, changed

    def test_apply_previews_three_roles_from_one_owned_sheet_and_clear_restores_the_app(self):
        """Given hello and a first Detect on the real app, when hostile selectors are sent, then each is
        rejected unsupported-value with nothing written; when three roles are applied, then the receipt
        carries the literal css, digest and outcomes, only the bound elements render the role values from one
        owned node with no style attribute, a Detect under the preview reports exactly five groups with the
        baseline rows, and Clear empties the receipt, removes the node and leaves main's markup as it was."""
        rows = self.rows()
        for engine in ENGINES:
            with self.subTest(engine=engine), self.role_app(engine) as (page, frame, _, detected):
                plain = self.literal()
                before = frame.locator('main').evaluate('el => el.outerHTML')
                for selectors in (['body'], ['h1, p'], ['p:hover']):
                    with self.subTest(selectors=selectors):
                        reply = self.send(page, 'design:roles-apply', detected, roles=[role('x', 'X', selectors, fontSize=20)])
                        self.assert_rejected(reply, 'unsupported-value', 'Unsupported selector')
                        self.assert_untouched(page, frame, 0, [], plain)
                roles = self.preview_roles(detected)
                hashed = self.hash_selector(frame)
                css = DISPLAY_CSS + BODY_CSS + HASH_CSS.format(hashed)
                self.assertEqual(roles[2]['selectors'], [hashed])
                receipt = self.send(page, 'design:roles-apply', detected, roles=roles)
                self.assertEqual((receipt['type'], receipt['operation'], receipt['revision']),
                                 ('design:roles-applied', 'apply', 1), receipt)
                self.assertEqual((receipt['outcomesComplete'], receipt['roles']), (True, roles))
                self.assertEqual([(o['id'], o['matched'], o['checked'], o['mismatched'], o['losses'])
                                  for o in receipt['outcomes']],
                                 [('display', 1, 1, 0, []), ('body', 2, 2, 0, []), ('hash-only', 1, 1, 0, [])])
                self.assertEqual((receipt['canonicalCss'], receipt['cssHash']), (css, fnv1a32(css)))
                self.assertEqual(self.rendered(frame), self.previewed())
                self.assertEqual(frame.evaluate(STYLE_ATTRIBUTES), 0)
                self.assertEqual(frame.evaluate(OWNED), [css])
                under_preview = self.detect(page)
                self.assertEqual(len(under_preview['groups']), 5)
                for name, row, count in (('display', 'display', 1), ('body', 'body', 2)):
                    group = self.group(under_preview, {'kind': 'author-role', 'name': name})
                    self.assertEqual(group['signatures'], [{'style': rows[row], 'count': count}])
                for row in ('hash-only', 'stable-class', 'action'):
                    group = self.group(under_preview, {'kind': 'style', 'style': rows[row]})
                    self.assertEqual(group['signatures'], [{'style': rows[row], 'count': 1}])
                cleared = self.send(page, 'design:roles-clear', under_preview)
                self.assertEqual((cleared['type'], cleared['operation'], cleared['revision']),
                                 ('design:roles-applied', 'clear', 2), cleared)
                self.assertEqual((cleared['roles'], cleared['canonicalCss'], cleared['cssHash']), ([], '', EMPTY_HASH))
                self.assertEqual(frame.evaluate(OWNED), [])
                self.assertEqual(frame.locator('main').evaluate('el => el.outerHTML'), before)
                self.assertEqual(self.rendered(frame), plain)

    def test_replaced_react_nodes_keep_the_preview_and_clear_needs_a_fresh_detect(self):
        """Given three roles applied, when Enter then Space re-render the section, then the old nodes detach,
        the new nodes show the role values and literal rows with the fixture's attributes and no style
        attribute, the same single owned node keeps its text, a Clear with the receipt's version is rejected
        page-changed and writes nothing, a fresh Detect reports a greater version, and Clear then removes the
        node and shows literal rows."""
        for engine in ENGINES:
            with self.subTest(engine=engine), self.role_app(engine) as (page, frame, _, detected):
                receipt = self.send(page, 'design:roles-apply', detected, roles=self.preview_roles(detected))
                self.assertEqual(receipt['type'], 'design:roles-applied', receipt)
                owned = frame.locator('#fontkit-role-styles').element_handle()
                button = frame.get_by_role('button', name='Replace text', exact=True)
                title, first, second = (frame.locator(ELEMENTS[name]) for name in ('title', 'first', 'second'))
                for generation, key in ((1, 'Enter'), (2, 'Space')):
                    old = [title.element_handle(), first.element_handle(), second.element_handle()]
                    old += [element.evaluate_handle('el => el.firstChild') for element in old]
                    classes = [title.evaluate('el => el.className'), first.evaluate('el => el.className'),
                               second.evaluate('el => el.className')]
                    try:
                        button.focus()
                        button.press(key)
                        frame.wait_for_function(
                            '(n) => document.querySelector("h1").textContent === "Module title " + n',
                            arg=generation, timeout=3000)
                        for handle in old:
                            self.assertFalse(handle.evaluate('node => node.isConnected'))
                        self.assertEqual(self.rendered(frame), self.previewed())
                        self.assertEqual([title.get_attribute('data-design-role'), title.get_attribute('data-design-id'),
                                          title.evaluate('el => el.className')],
                                         ['display', 'modules.title', classes[0]])
                        self.assertEqual([first.get_attribute('data-design-role'), first.get_attribute('data-design-id'),
                                          first.evaluate('el => el.className')],
                                         ['body', 'modules.body.first', classes[1]])
                        self.assertEqual([second.get_attribute('data-design-role'), second.get_attribute('data-design-id'),
                                          second.evaluate('el => el.className')],
                                         ['body', 'modules.body.second', classes[2]])
                        self.assertEqual(frame.evaluate(STYLE_ATTRIBUTES), 0)
                        self.assertEqual(frame.evaluate(OWNED), [receipt['canonicalCss']])
                        self.assertTrue(owned.evaluate('node => node.isConnected'))
                    finally:
                        for handle in old:
                            handle.dispose()
                owned.dispose()
                stale = self.send(page, 'design:roles-clear', receipt)
                self.assert_rejected(stale, 'page-changed')
                self.assert_untouched(page, frame, 1, [receipt['canonicalCss']], self.previewed())
                fresh = self.detect(page)
                self.assertGreater(fresh['pageVersion'], receipt['pageVersion'])
                cleared = self.send(page, 'design:roles-clear', fresh)
                self.assertEqual((cleared['type'], cleared['operation']), ('design:roles-applied', 'clear'), cleared)
                self.assertEqual(frame.evaluate(OWNED), [])
                self.assertEqual(self.rendered(frame), self.literal())

    def test_hot_update_after_apply_keeps_the_role_and_shows_the_new_author_size(self):
        """Given a display role applied after one section replacement, when the title's 40px becomes 44px
        once, then the document, React text and title node survive, the title shows the role's family and
        weight at 44px, Clear and Apply carrying the receipt's version are rejected page-changed and change
        nothing, a fresh Detect reports a greater version and the serif 44px 600 baseline, Clear removes the
        node and shows it, and once the CSS is restored the title shows the literal 40px row."""
        for engine in ENGINES:
            with self.subTest(engine=engine), self.role_app(engine) as (page, frame, project, _):
                frame.get_by_role('button', name='Replace text', exact=True).press('Enter')
                frame.wait_for_function('document.querySelector("h1").textContent === "Module title 1"')
                detected = self.detect(page)
                display = self.group(detected, {'kind': 'author-role', 'name': 'display'})
                roles = [role('display', 'Display', [display['selectors'][0]['value']], **DISPLAY)]
                receipt = self.send(page, 'design:roles-apply', detected, roles=roles)
                self.assertEqual((receipt['type'], receipt['revision'], receipt['canonicalCss']),
                                 ('design:roles-applied', 1, DISPLAY_CSS), receipt)
                frame.evaluate('window.marker = "same document"')
                title = frame.locator(ELEMENTS['title'])
                node = title.element_handle()
                css, original, changed = self.scratch_css(project)
                shown = {**self.literal()['title'], **DISPLAY, 'fontSize': 44}
                try:
                    css.write_bytes(changed)
                    frame.wait_for_function(
                        'getComputedStyle(document.querySelector("h1")).fontSize === "44px"', timeout=10000)
                    self.assertEqual(frame.evaluate('window.marker'), 'same document')
                    self.assertTrue(node.evaluate('node => node.isConnected'))
                    self.assertEqual(title.text_content(), 'Module title 1')
                    self.assertEqual(title.evaluate(SIGNATURE), shown)
                    for kind, extra in (('design:roles-clear', {}), ('design:roles-apply', {'roles': roles})):
                        stale = self.send(page, kind, receipt, **extra)
                        self.assert_rejected(stale, 'page-changed')
                        self.assertEqual(page.evaluate('revision'), 1)
                        self.assertEqual(frame.evaluate(OWNED), [DISPLAY_CSS])
                        self.assertEqual(title.evaluate(SIGNATURE), shown)
                    fresh = self.detect(page)
                    self.assertGreater(fresh['pageVersion'], receipt['pageVersion'])
                    baseline = {**self.literal()['title'], 'fontSize': 44}
                    self.assertEqual(self.group(fresh, {'kind': 'author-role', 'name': 'display'})['signatures'],
                                     [{'style': baseline, 'count': 1}])
                    cleared = self.send(page, 'design:roles-clear', fresh)
                    self.assertEqual((cleared['type'], cleared['operation'], cleared['revision']),
                                     ('design:roles-applied', 'clear', 2), cleared)
                    self.assertEqual((cleared['roles'], cleared['canonicalCss'], cleared['cssHash'],
                                      cleared['outcomesComplete'], cleared['outcomes']), ([], '', EMPTY_HASH, True, []))
                    self.assertEqual(frame.evaluate(OWNED), [])
                    self.assertEqual(title.evaluate(SIGNATURE), baseline)
                finally:
                    try:
                        self.restore_css(frame, css, original)
                    finally:
                        node.dispose()
                self.assertEqual(title.evaluate(SIGNATURE), self.literal()['title'])

    def test_hot_update_between_apply_and_measurement_makes_a_committed_receipt_without_outcomes(self):
        """Given a display role applied while the frame callbacks are withheld, so the bridge measures from its
        250 ms timer, when a hot update lands after the commit and before that timer, then one receipt
        carries the committed role, css and digest with a newer current version, incomplete page-changed
        and no outcomes; Apply and Clear carrying the Detect's version are rejected page-changed
        and change nothing, and after a fresh Detect the same Clear is accepted."""
        for engine in ENGINES:
            with self.subTest(engine=engine), self.role_app(engine) as (page, frame, project, detected):
                display = self.group(detected, {'kind': 'author-role', 'name': 'display'})
                roles = [role('display', 'Display', [display['selectors'][0]['value']], **DISPLAY)]
                css, original, changed = self.scratch_css(project)
                message = {'type': 'design:roles-apply', 'documentId': page.evaluate('roleState.documentId'),
                           'pageVersion': detected['pageVersion'], 'roles': roles}
                title = frame.locator(ELEMENTS['title'])
                try:
                    frame.evaluate(HOLD_FRAMES)
                    page.evaluate('(m) => { window.pending = request(m); }', message)
                    frame.wait_for_function('window.stamps.commit !== undefined', polling=10)
                    css.write_bytes(changed)
                    frame.wait_for_function(
                        'getComputedStyle(document.querySelector("h1")).fontSize === "44px"', timeout=10000)
                    receipt = page.evaluate('window.pending')
                    frame.wait_for_function('window.stamps.deadline !== undefined', polling=10)
                    stamps = frame.evaluate('window.stamps')
                    self.assertTrue(stamps['commit'] < stamps['hmr'] < stamps['deadline'],
                                    f'the hot update must land between the commit and the timer: {stamps}')
                    self.assertEqual((receipt['type'], receipt['operation'], receipt['revision']),
                                     ('design:roles-applied', 'apply', 1), receipt)
                    self.assertEqual((receipt['roles'], receipt['canonicalCss'], receipt['cssHash']),
                                     (roles, DISPLAY_CSS, fnv1a32(DISPLAY_CSS)))
                    self.assertEqual(receipt['pageVersion'], detected['pageVersion'])
                    self.assertGreater(receipt['currentPageVersion'], detected['pageVersion'])
                    self.assertEqual((receipt['outcomesComplete'], receipt['outcomeReason'], receipt['outcomes']),
                                     (False, 'page-changed', []))
                    self.assertEqual(page.evaluate(
                        "(id) => messages('design:roles-applied').filter(m => m.requestId === id).length",
                        receipt['requestId']), 1)
                    shown = {**self.literal()['title'], **DISPLAY, 'fontSize': 44}
                    for kind, extra in (('design:roles-apply', {'roles': roles}), ('design:roles-clear', {})):
                        stale = self.send(page, kind, receipt, **extra)
                        self.assert_rejected(stale, 'page-changed')
                        self.assertEqual(page.evaluate('revision'), 1)
                        self.assertEqual(frame.evaluate(OWNED), [DISPLAY_CSS])
                        self.assertEqual(title.evaluate(SIGNATURE), shown)
                    fresh = self.detect(page)
                    cleared = self.send(page, 'design:roles-clear', fresh)
                    self.assertEqual((cleared['type'], cleared['operation']), ('design:roles-applied', 'clear'), cleared)
                finally:
                    self.restore_css(frame, css, original)


if __name__ == '__main__':
    unittest.main()
