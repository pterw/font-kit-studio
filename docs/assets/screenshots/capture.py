"""Regenerate the README screenshots (development only).

Starts scripts/serve.py on free ports, opens the real Studio connected to the real demo
app, and writes PNGs next to this file. Run from anywhere:

    FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium \
        python3 docs/assets/screenshots/capture.py

Google Fonts requests are answered with empty CSS so the capture works offline. The
demo falls back to its system font stacks, which is also what the screenshots show.
"""

import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tests'))
from playwright.sync_api import sync_playwright  # noqa: E402
from support import launch  # noqa: E402

OUT = Path(__file__).resolve().parent
TITLE = '[data-design-id="landing.hero.title"]'
CTA = '[data-design-id="landing.hero.cta"]'
# Poll on a timer, not on requestAnimationFrame (Playwright's default): a frame scrolled
# offscreen (the mobile capture) or a backgrounded page may never run a rAF callback, which
# stalls the wait. The same value as the gate's POLL_MS in scripts/dev/_frontend_gate_shared.py.
POLL_MS = 50
SIZES = {'desktop': {'width': 1440, 'height': 900}, 'mobile': {'width': 390, 'height': 844}}


def free_ports():
    socks = [socket.socket() for _ in range(2)]
    for sock in socks:
        sock.bind(('127.0.0.1', 0))
    ports = [sock.getsockname()[1] for sock in socks]
    for sock in socks:
        sock.close()
    return ports


def main():
    work = REPO / 'work'
    work.mkdir(exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='screenshots-', dir=work))
    studio_port, target_port = free_ports()
    rel = (scratch / 'overrides.css').relative_to(REPO).as_posix()
    log = open(scratch / 'serve.log', 'w+')
    proc = subprocess.Popen([sys.executable, str(REPO / 'scripts' / 'serve.py'), '--quiet', '--studio-port', str(studio_port),
                             '--target-port', str(target_port), '--overrides', rel], cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(200):
            log.seek(0)
            if 'Press Ctrl-C' in log.read():
                break
            time.sleep(0.05)
        studio = f'http://localhost:{studio_port}'
        target = f'http://localhost:{target_port}/demo/'
        with sync_playwright() as runtime:
            browser = launch(runtime, 'chromium')
            try:
                for name, viewport in SIZES.items():
                    capture(browser, studio, target, rel, target_port, name, viewport)
            finally:
                browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
        shutil.rmtree(scratch, ignore_errors=True)


def badge(page, pattern):
    page.wait_for_function('(re) => new RegExp(re).test(document.querySelector("#bridgeStatusBadge").textContent)', arg=pattern, polling=POLL_MS)


def capture(browser, studio, target, rel, target_port, name, viewport):
    context = browser.new_context(viewport=viewport)
    context.route('https://**/*', lambda route: route.fulfill(status=200, content_type='text/css', body='') if 'fonts.googleapis' in route.request.url else route.abort())
    context.route(f'http://localhost:{target_port}/demo/fontkit-overrides.css',
                  lambda route: route.continue_(url=f'http://localhost:{target_port}/{rel}'))
    page = context.new_page()
    page.goto(f'{studio}/font_kit_studio_v0.1.1.html?target={target}')
    badge(page, r'^Connected \(\d+ targets\)$')
    frame = page.locator('#targetAppFrame').element_handle().content_frame()
    frame.wait_for_function('document.readyState === "complete"', polling=POLL_MS)
    badge(page, r'^Connected \(\d+ targets\)$')

    def to_top(selector, block='start'):
        page.evaluate('([s, b]) => document.querySelector(s).scrollIntoView({block: b})', [selector, block])

    def select(selector, text):
        locator = page.frame_locator('#targetAppFrame').locator(selector)
        for _ in range(2):
            locator.click()
            try:
                page.wait_for_function('(t) => (document.querySelector("#liveTargetName") || {}).textContent === t', arg=text, timeout=3000, polling=POLL_MS)
                return
            except Exception:
                pass
        raise RuntimeError(f'could not select {selector}')

    def type_into(selector, text):
        page.locator(selector).click()
        page.keyboard.press('Control+A')
        page.keyboard.type(text, delay=30)

    def below_sticky_tabs(selector, block='start'):
        """Scroll so `selector` is not hidden behind Studio's sticky Library/Composer tabs."""
        to_top(selector, block)
        if block == 'start':
            page.evaluate('window.scrollBy(0, -64)')

    def outline_follows_title():
        """Wait until the selection outline is as tall as the edited title.

        The bridge reports an element's bounds from an animation frame. A preview scrolled out of view runs none,
        so after edits typed in the inspector below it the outline still has the old size until the preview is
        visible again and its first frame has run (about 30 to 100 ms). A shot taken before that shows a stale outline.
        """
        height = frame.evaluate(f'document.querySelector({TITLE!r}).getBoundingClientRect().height')
        page.wait_for_function('(h) => { const o = document.querySelector("#bridgeOverlaySelected"); '
                               'return !o.hidden && Math.abs(o.getBoundingClientRect().height - h) < 2; }', arg=height, polling=POLL_MS)

    if name == 'desktop':
        # Pop-out first, before any edit, so the screenshot shows the plain docked placeholder.
        with page.expect_popup() as info:
            page.locator('#bridgePopOut').click()
        popup = info.value
        page.locator('#bridgePopoutPlaceholder').wait_for(state='visible')
        badge(page, r'^Connected \(\d+ targets\)$')
        below_sticky_tabs('#targetAppBridgeBar')
        page.screenshot(path=str(OUT / f'pop-out-{name}.png'))
        with popup.expect_event('close'):
            page.locator('#bridgeDock').click()
        page.locator('#targetAppFrame').wait_for(state='visible')
        badge(page, r'^Connected \(\d+ targets\)$')
        frame = page.locator('#targetAppFrame').element_handle().content_frame()
        frame.wait_for_function('document.readyState === "complete"', polling=POLL_MS)
        badge(page, r'^Connected \(\d+ targets\)$')

    # Edit the hero title so the panels show real changes. The values differ from the demo's own
    # (60.96px, -0.02em, #14213d), so the screenshots show a visible edit.
    select(TITLE, 'Hero title')
    type_into('#liveFontSize', '72')
    frame.wait_for_function(f'getComputedStyle(document.querySelector({TITLE!r})).fontSize === "72px"', polling=POLL_MS)
    type_into('#liveLetterSpacing', '-0.04')
    frame.wait_for_function(f'parseFloat(getComputedStyle(document.querySelector({TITLE!r})).letterSpacing) < -2.5', polling=POLL_MS)
    type_into('#liveColorHex', '#0b6e4f')
    page.keyboard.press('Tab')
    frame.wait_for_function(f'getComputedStyle(document.querySelector({TITLE!r})).color === "rgb(11, 110, 79)"', polling=POLL_MS)
    page.wait_for_function('() => /^Live/.test(document.querySelector("#bridgeStatusBadge").textContent)', polling=POLL_MS)
    page.locator('#codeTabCss').click()
    page.wait_for_function('() => document.querySelector("#liveCodeOutput").textContent.includes("color: #0b6e4f")', polling=POLL_MS)
    page.locator('#liveCodeOutput').evaluate('el => el.scrollTop = 0')

    page.mouse.move(0, 0)
    if name == 'desktop':
        page.locator('#targetAppBridgeBar').screenshot(path=str(OUT / f'bridge-bar-{name}.png'))
        page.locator('#liveCodePanel').screenshot(path=str(OUT / f'code-panel-{name}.png'))
        # The first screen of Studio at the top of the page: its title and eyebrow, the bridge bar, the preview
        # with the edited hero, and the inspector.
        page.evaluate('window.scrollTo(0, 0)')
        outline_follows_title()
        page.screenshot(path=str(OUT / f'live-app-{name}.png'))
    else:
        below_sticky_tabs('#targetAppContainer')
        page.evaluate('window.scrollBy(0, 40)')
        outline_follows_title()
        page.screenshot(path=str(OUT / f'live-app-{name}.png'))
        to_top('#liveCodePanel', 'center')
        page.screenshot(path=str(OUT / f'code-panel-{name}.png'))

    # Arrange: the call to action next to its sibling. Desktop uses theater mode so nothing is cropped or covered.
    if name == 'desktop':
        page.locator('#btnToggleFullscreen').click()
    select(CTA, 'Hero call to action')
    page.wait_for_selector('#liveArrange')
    to_top('#liveArrange', 'center')
    page.screenshot(path=str(OUT / f'arrange-{name}.png'))

    if name == 'desktop':
        # A guard in action: a form control cannot leave its form.
        select('.signup button[type="submit"]', 'BUTTON: "Subscribe"')
        solo = page.locator('#liveMoveContainer option', has_text='Solo').get_attribute('value')
        page.locator('#liveMoveContainer').select_option(solo)
        page.locator('#liveMoveInto').click()
        page.locator('#liveMoveGuard').wait_for(state='visible')
        to_top('#liveMoveGuard', 'center')
        page.screenshot(path=str(OUT / f'arrange-guard-{name}.png'))
        page.keyboard.press('Escape')
    context.close()


if __name__ == '__main__':
    main()
