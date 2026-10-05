"""The friction test (R1.7a): the one command, run with no person in the loop, within a time budget.

It runs the real `fontkitstudio` command on the Vite + React fixture with stdin closed, and times
the run from just before the process starts until Studio shows the page connected and the page's
own title is inside the frame. The bundle step is not timed: an installed package is already bundled.
"""

import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
import unittest

import support
from fixture_support import FIXTURES, require_fixture
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from support import ENGINES, close_contexts, new_context

NODE = shutil.which('node')
PACKAGE = support.REPO / 'packages' / 'fontkitstudio'
BIN = PACKAGE / 'bin' / 'fontkitstudio.js'
CONNECTED = r'^Connected \(\d+ targets?\)$'
TITLE = '[data-design-id="vite.hero.title"]'

# Seconds from starting the command to a connected Studio. In CI the budget is the slowest
# fixtures cell of the first green run (0.8 s, Windows) plus 50 percent, rounded up (R1 plan,
# question 4). A developer machine running other work is slower and noisier (1.2 to 4.6 s seen),
# so locally the budget only catches a stuck or prompting start (owner, 2026-10-04).
FRICTION_BUDGET_S = 2 if os.environ.get('CI') == 'true' else 10
BADGE_WAIT_MS = 90000   # longer than the budget, so a slow start fails as a budget miss with its time


@unittest.skipIf(NODE is None, 'node is not on PATH; the friction test needs it')
class FrictionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([NODE, str(PACKAGE / 'scripts' / 'bundle.js')], cwd=support.REPO, check=True)

    def setUp(self):
        self.contexts = []
        self.addCleanup(lambda: close_contexts(self.contexts))

    def pump(self, stream, name):
        for line in stream:
            self.lines.put((name, line.rstrip('\r\n')))

    def stop(self, proc):
        """Stop only the command this test started."""
        try:
            if proc.poll() is None:
                proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    self.fail('the command did not stop')
        finally:
            proc.stdout.close()
            proc.stderr.close()

    def start(self, collected):
        """Spawn the command with stdin closed; return (process, Open: url) or fail with its output."""
        flags = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {}
        self.lines = queue.Queue()
        proc = subprocess.Popen(
            [NODE, str(BIN), '--no-open'], cwd=FIXTURES / 'vite-react', stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', **flags)
        self.addCleanup(self.stop, proc)   # a safety net; each engine also stops its own command
        threads = [threading.Thread(target=self.pump, args=(stream, name), daemon=True)
                   for stream, name in ((proc.stdout, 'out'), (proc.stderr, 'err'))]
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + BADGE_WAIT_MS / 1000
        while True:
            try:
                name, line = self.lines.get(timeout=0.5)
            except queue.Empty:
                if proc.poll() is not None:
                    for thread in threads:
                        thread.join(timeout=2)
                    while not self.lines.empty():
                        name, line = self.lines.get_nowait()
                        collected.append(f'{name}: {line}')
                    self.fail(f'the command exited ({proc.returncode}) before "Open:"; output:\n'
                              + '\n'.join(collected))
                if time.monotonic() > deadline:
                    self.fail('no "Open:" line in time; output so far:\n' + '\n'.join(collected))
                continue
            collected.append(f'{name}: {line}')
            if name == 'out' and line.startswith('Open: '):
                return proc, line[len('Open: '):]

    def test_the_one_command_connects_within_the_budget(self):
        require_fixture(self, 'vite-react')
        for engine in ENGINES:
            with self.subTest(engine=engine):
                collected = []
                # Each engine runs its own command with its own clock. The browser launch and the
                # context stay inside the timed region: a user's browser launch is part of the friction.
                started = time.perf_counter()
                proc, url = self.start(collected)
                try:
                    context = new_context(engine)
                    self.contexts.append(context)
                    context.route('https://**/*', lambda route: route.abort())   # no third-party contact
                    page = context.new_page()
                    page.goto(url)
                    try:
                        page.wait_for_function(
                            '(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)',
                            arg=CONNECTED, timeout=BADGE_WAIT_MS)
                        page.frame_locator('#targetAppFrame').locator(TITLE).wait_for(
                            state='attached', timeout=BADGE_WAIT_MS)
                    except PlaywrightTimeout:
                        try:
                            badge = page.locator('#bridgeStatusBadge').text_content(timeout=1000)
                        except PlaywrightTimeout:
                            badge = '<unreadable>'
                        self.fail(f'Studio never showed {CONNECTED!r} with the page title in the frame; '
                                  f'badge says {badge!r}; output:\n' + '\n'.join(collected))
                    elapsed = time.perf_counter() - started
                    print(f'friction: {elapsed:.1f} s (budget {FRICTION_BUDGET_S} s)', file=sys.stderr)
                    self.assertRegex(page.locator('#bridgeStatusBadge').text_content(), CONNECTED)
                    self.assertLessEqual(
                        elapsed, FRICTION_BUDGET_S,
                        f'the one command took {elapsed:.1f} s to connect; the budget is {FRICTION_BUDGET_S} s')
                finally:
                    self.stop(proc)


if __name__ == '__main__':
    unittest.main()
