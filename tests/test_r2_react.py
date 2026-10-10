"""Rendered inputs for R2 React adapters; role preview belongs to F2b.

The literal oracle describes authored semantic selectors, not a compiler's hash
algorithm. CSS updates are HMR, not React Fast Refresh. Every browser uses an
isolated source copy and an offline HTTPS guard proved on a separate canary page.
"""

from contextlib import contextmanager
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

from fixture_support import FIXTURES, require_fixture, vite_bin
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

    def guarded_context(self, engine):
        context = new_context(engine)
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

    @contextmanager
    def app(self, engine):
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
            try:
                context, counts = self.guarded_context(engine)
                try:
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(url)
                    page.locator('h1').wait_for()
                    yield page, project
                    self.assertEqual(errors, [], 'fixture must render without runtime errors')
                    self.assertEqual(counts, {'aborted': 2, 'fallback': 0}, 'app needs no HTTPS request')
                finally:
                    context.close()
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
                        css.write_bytes(original)
                        self.assertEqual(css.read_bytes(), original, 'scratch CSS bytes must be restored')
                        page.wait_for_function(
                            'getComputedStyle(document.querySelector("h1")).fontSize === "40px"', timeout=10000)
                    finally:
                        old_title.dispose()
                self.assert_styles(page)


if __name__ == '__main__':
    unittest.main()
