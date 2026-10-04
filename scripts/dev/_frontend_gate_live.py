"""Live-preview flow: connect Studio to the demo, select a target, edit, reset.

This is the product's headline path, so it gets a real run on every profile:
real Studio, real `fontkit-bridge.js` in the real demo app, real `postMessage`
across two loopback origins. The helpers here (connect, select, type, pop out,
reconnect) are also what the layout, theme and touch-target checks use to put
Studio into its v0.2 states, which is why they live in one module instead of
being copied into each (the rule of three).

The flow mirrors `tests/test_live_integration.py`: keystroke-level typing,
selecting by clicking inside the iframe, reading the CSS tab, and proving
Reset returns the page byte for byte. A fake counterpart would pass while the
real pair is broken, so nothing here is faked.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_shared import (
    ACTION_TIMEOUT_MS,
    CONNECT_WAIT_MS,
    CONNECTED_PATTERN,
    HERO_TITLE,
    HERO_TITLE_ID,
    REQUEST_WAIT_MS,
    GateContext,
    GateStateError,
    Outcome,
    wait_until,
)

BADGE_MATCHES = (
    '(re) => new RegExp(re).test('
    'document.querySelector("#bridgeStatusBadge").textContent)'
)
INSPECTOR_SHOWS = (
    '(id) => { const el = document.querySelector("#liveTargetName");'
    " return Boolean(el) && el.dataset.targetId === id; }"
)
STYLE_IS = (
    "([selector, prop, value]) => { const el = document.querySelector(selector);"
    " return Boolean(el) && getComputedStyle(el)[prop] === value; }"
)
CODE_HAS = (
    '(needle) => document.querySelector("#liveCodeOutput").textContent.includes(needle)'
)


def connect_studio(ctx: GateContext) -> None:
    """Open Studio with ?target= and wait until it reports Connected and the demo loaded.

    `?target=` switches Studio to Composer's Live App view and connects. The
    iframe load and the bridge handshake race, and a re-hello after load
    starts a fresh session, so the badge is awaited twice around the frame's
    own readiness, as the real-integration tests do.
    """
    page = ctx.page
    page.goto(ctx.live_url, wait_until="load")
    if not wait_until(page, BADGE_MATCHES, CONNECTED_PATTERN, CONNECT_WAIT_MS):
        badge = page.locator("#bridgeStatusBadge").text_content()
        raise GateStateError(f"Studio never reported Connected; the badge says {badge!r}")
    if not wait_until(
        target_frame(page), 'document.readyState === "complete"', None, CONNECT_WAIT_MS
    ):
        raise GateStateError("the demo never finished loading inside the preview frame")
    if not wait_until(page, BADGE_MATCHES, CONNECTED_PATTERN, CONNECT_WAIT_MS):
        raise GateStateError("Studio lost the connection after the demo finished loading")


def target_frame(page):
    """The iframe's Frame, for reading computed style inside the demo."""
    frame = page.locator("#targetAppFrame").element_handle().content_frame()
    if frame is None:
        raise GateStateError("#targetAppFrame has no content frame")
    return frame


def select_in_target(ctx: GateContext, selector: str, target_id: str) -> None:
    """Select a demo element by interacting with it inside the iframe.

    A tap on touch profiles and a click otherwise, because the pointer a
    person uses there is a finger. One retry covers the load-time re-hello,
    which starts a fresh session and clears the selection.
    """
    page = ctx.page
    locator = page.frame_locator("#targetAppFrame").locator(selector)
    for attempt in (1, 2):
        if ctx.touch:
            locator.tap(timeout=ACTION_TIMEOUT_MS)
        else:
            locator.click(timeout=ACTION_TIMEOUT_MS)
        if wait_until(page, INSPECTOR_SHOWS, target_id, REQUEST_WAIT_MS):
            return
    raise GateStateError(f"the inspector never showed {target_id} after {selector} was selected")


def connect_and_select(ctx: GateContext) -> None:
    """The common v0.2 state: connected, with the hero title selected."""
    connect_studio(ctx)
    select_in_target(ctx, HERO_TITLE, HERO_TITLE_ID)


def type_into(page, selector: str, text: str, delay_ms: int = 60) -> None:
    """Replace a field's value with real keystrokes.

    Keystroke-level typing, not `fill()`: the intermediate values ("5", then
    "56") are real updates a person causes, and some handlers react to them.
    """
    page.locator(selector).click(timeout=ACTION_TIMEOUT_MS)
    page.keyboard.press("Control+A")
    page.keyboard.type(text, delay=delay_ms)


def read_code_tab(page, name: str, needle: str | None = None) -> str:
    """Open a code tab ("Css", "Html", "Json") and return its text.

    With `needle`, waits (bounded) until the tab shows it, so the read sees
    the acknowledged state and not the one before the bridge answered.
    """
    page.locator(f"#codeTab{name}").click(timeout=ACTION_TIMEOUT_MS)
    if needle is not None:
        wait_until(page, CODE_HAS, needle, REQUEST_WAIT_MS)
    return page.locator("#liveCodeOutput").text_content()


def open_popout(ctx: GateContext):
    """Pop the Live App out into its own window and return the popup page.

    The caller closes the popup. Studio replaces the iframe with a
    placeholder once the window opens, which is the state the overflow check
    needs to see.
    """
    with ctx.browser_context.expect_page() as popup_info:
        ctx.page.locator("#bridgePopOut").click(timeout=ACTION_TIMEOUT_MS)
    popup = popup_info.value
    ctx.page.locator("#bridgePopoutPlaceholder").wait_for(
        state="visible", timeout=CONNECT_WAIT_MS
    )
    return popup


def reach_reconnect_banner(ctx: GateContext) -> None:
    """Edit the title, reload the demo, and wait for Studio's reconnect banner.

    The banner appears only when Studio holds saved overrides that differ
    from a freshly reloaded Live App. It is a v0.2 surface that a plain
    connect never shows.
    """
    page = ctx.page
    connect_and_select(ctx)
    type_into(page, "#liveFontSize", "37")
    frame = target_frame(page)
    wait_until(frame, STYLE_IS, [HERO_TITLE, "fontSize", "37px"], REQUEST_WAIT_MS)
    frame.evaluate("location.reload()")
    page.locator("#liveReconnectBanner").wait_for(state="visible", timeout=CONNECT_WAIT_MS)


def check_live_edit(ctx: GateContext) -> Outcome:
    """Select, resize, see the iframe follow and the CSS tab say so, then Reset.

    The assertions read rendered results: the demo's computed font-size, the
    generated CSS rule and the page's bytes after Reset. Asserting that a
    message was sent would pass with the bridge deleted.
    """
    out = Outcome()
    page = ctx.page
    connect_and_select(ctx)
    frame = target_frame(page)
    body_before = frame.evaluate("document.body.outerHTML")
    original = frame.evaluate(
        "(s) => getComputedStyle(document.querySelector(s)).fontSize", HERO_TITLE
    )
    # Any size the demo does not already use at this width, so a change is visible.
    size = 37 if original != "37px" else 38

    type_into(page, "#liveFontSize", str(size))
    if not wait_until(frame, STYLE_IS, [HERO_TITLE, "fontSize", f"{size}px"]):
        now = frame.evaluate(
            "(s) => getComputedStyle(document.querySelector(s)).fontSize", HERO_TITLE
        )
        out.failures.append(
            f"typing {size} into Size left the demo title at {now}, expected {size}px"
        )
        return out

    css = read_code_tab(page, "Css", f"font-size: {size}px !important;")
    if f"font-size: {size}px !important;" not in css:
        out.failures.append(f"the CSS tab does not show font-size: {size}px: {css[:120]!r}")
    if f'[data-design-id="{HERO_TITLE_ID}"] {{' not in css:
        out.failures.append("the CSS tab has no rule for the hero title's data-design-id")
    count = page.locator("#liveChangeCount").text_content()
    if count != "1":
        out.failures.append(f"the change counter says {count!r} after one edit, expected '1'")

    page.locator("#liveResetTarget").click(timeout=ACTION_TIMEOUT_MS)
    reset_ok = wait_until(
        frame,
        "(s) => document.querySelector(s).style.fontSize === ''",
        HERO_TITLE,
    )
    now = frame.evaluate(
        "(s) => getComputedStyle(document.querySelector(s)).fontSize", HERO_TITLE
    )
    if not reset_ok or now != original:
        out.failures.append(f"Reset left the demo title at {now}, expected {original}")
    body_after = frame.evaluate("document.body.outerHTML")
    if body_after != body_before:
        out.failures.append("Reset did not return the demo's body markup to its original bytes")
    count = page.locator("#liveChangeCount").text_content()
    if count != "0":
        out.failures.append(f"the change counter says {count!r} after Reset, expected '0'")
    if ctx.errors:
        out.failures.append(f"uncaught page errors during the edit: {ctx.errors[:3]}")
    return out
