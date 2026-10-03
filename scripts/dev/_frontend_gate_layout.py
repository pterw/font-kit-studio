"""Layout checks: horizontal overflow, initial visibility and touch targets.

Each check measures in a thin browser helper and judges in a pure `*_failures`
function, so the judgements are pinned by the plain unittest suite and the
measurements stay too small to hide a bug. Every measurement is a computed
value or a bounding box, never a class name: a class name passes against a
stylesheet the browser never applied.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_live import (
    connect_and_select,
    open_popout,
    reach_reconnect_banner,
    target_frame,
)
from scripts.dev._frontend_gate_shared import (
    GateContext,
    Outcome,
)

#: A scrollbar-free page can still measure one pixel wider than its viewport
#: from sub-pixel rounding. Anything beyond that is a horizontal scrollbar.
OVERFLOW_TOLERANCE_PX = 1

#: Reads how wide the document is against how wide it may be, plus the first
#: few elements that stick out past the viewport and are not inside a clipping
#: or scrolling ancestor (those are allowed to be wider than the page).
OVERFLOW_JS = """() => {
    const root = document.documentElement;
    const limit = root.clientWidth;
    const clips = (node) => {
        for (let el = node.parentElement; el && el !== document.body; el = el.parentElement) {
            const x = getComputedStyle(el).overflowX;
            if (x === 'auto' || x === 'scroll' || x === 'hidden' || x === 'clip') return true;
        }
        return false;
    };
    const describe = (node) => {
        const name = node.tagName.toLowerCase();
        if (node.id) return `${name}#${node.id}`;
        const cls = (node.getAttribute('class') || '').trim().split(/\\s+/)[0];
        return cls ? `${name}.${cls}` : name;
    };
    const offenders = [];
    for (const node of document.body.querySelectorAll('*')) {
        const rect = node.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0 || rect.right <= limit + 1) continue;
        if (getComputedStyle(node).position === 'fixed' || clips(node)) continue;
        offenders.push(`${describe(node)} ends at ${Math.round(rect.right)}px`);
        if (offenders.length === 3) break;
    }
    return {scrollWidth: root.scrollWidth, clientWidth: limit, offenders};
}"""

#: What a script reveals later must compute `display: none` before then.
#:
#: A class name or a `hidden` attribute is not evidence: a rule such as
#: `.live-banner { display: flex }` outranks the user-agent's `[hidden]`, so
#: the element renders under a flag that says it is hidden, and a probe that
#: read the attribute would pass. Assert the computed value on the node
#: itself, in the view where the node's own ancestors are visible, so an
#: ancestor's `display: none` cannot hide a leak.
#:
#: Each entry is (surface, [actions to reach it], [selectors]).
HIDDEN_ON_LOAD = (
    ("Studio Library", (), ("#composerView", "#exportDialog")),
    (
        "Studio Composer",
        (("click", "#modeComposer"),),
        (
            "#targetAppContainer",
            "#liveCodePanel",
            "#liveCodeWarnings",
            "#liveReconnectBanner",
            "#bridgePopoutPlaceholder",
            "#bridgeOverlayHover",
            "#bridgeOverlaySelected",
            "#bridgeWarning",
            "#bridgeHint",
            "#importJsonFile",
        ),
    ),
)

#: Smallest side the interactive-element guideline allows on touch, in CSS px
#: (Apple HIG 44pt, WCAG 2.5.5 AAA). Report-only for now: see plan Addendum 4.
MIN_TOUCH_TARGET_PX = 44

#: Everything a person can tap. [tabindex="-1"] is excluded: it is focusable
#: by script only and is not a target.
#:
#: label[for] is in the list and has to be. Where an input is clipped to 1x1
#: and styled through its label, the label is the only thing a finger can land
#: on. Skipping the input without measuring the label would measure neither.
INTERACTIVE_SELECTOR = (
    "a[href], button, input, select, textarea, summary, label[for], "
    '[tabindex]:not([tabindex="-1"])'
)

#: The measurement. See check_touch_targets for the pairing rule it applies.
TOUCH_TARGETS_JS = """([selector, minimum]) => {
    const describe = (node) => {
        const name = node.tagName.toLowerCase();
        if (node.id) return `${name}#${node.id}`;
        const cls = (node.getAttribute('class') || '').trim().split(/\\s+/)[0];
        if (cls) return `${name}.${cls}`;
        // No id and no class. A form control's textContent is its options, so
        // use its label text instead; anything else is named by its own text.
        const label = node.getAttribute('aria-label') || node.getAttribute('name');
        if (label) return `${name}[${label}]`;
        if (['SELECT', 'INPUT', 'TEXTAREA'].includes(node.tagName)) {
            return node.type ? `${name}[type=${node.type}]` : name;
        }
        const text = (node.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 24);
        return text ? `${name} "${text}"` : name;
    };
    // Clipped to a pixel or two by the visually-hidden pattern, so a finger
    // cannot land on it and its partner is the real target.
    const CLIPPED_PX = 2;
    const side = (node) => {
        const rect = node.getBoundingClientRect();
        return Math.min(rect.width, rect.height);
    };
    const found = [];
    for (const node of document.querySelectorAll(selector)) {
        const rect = node.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;
        const smaller = Math.min(rect.width, rect.height);
        // An input styled through its label: the label is hit.
        if (smaller <= CLIPPED_PX && node.labels && node.labels.length) continue;
        // A label whose input is visible: the input is hit.
        if (node.tagName === 'LABEL') {
            if (!node.control) continue;
            if (side(node.control) > CLIPPED_PX) continue;
        }
        // An inline link inside a run of prose is exempt from target size.
        if (node.tagName === 'A' && getComputedStyle(node).display === 'inline') continue;
        if (smaller < minimum) {
            found.push([describe(node), Math.round(rect.width), Math.round(rect.height)]);
        }
    }
    return found;
}"""


def overflow_failures(surface: str, measured: dict) -> list[str]:
    """Judge one overflow reading: the document must not be wider than its viewport.

    The offenders (when the measurement found any) are the first elements
    sticking out, because "the page scrolls sideways" is not actionable
    without a place to look.
    """
    extra = measured["scrollWidth"] - measured["clientWidth"]
    if extra <= OVERFLOW_TOLERANCE_PX:
        return []
    detail = (
        f"{surface} scrolls horizontally: document is {measured['scrollWidth']}px wide "
        f"in a {measured['clientWidth']}px viewport"
    )
    if measured["offenders"]:
        detail += f" ({'; '.join(measured['offenders'])})"
    return [detail]


def check_no_horizontal_overflow(ctx: GateContext) -> Outcome:
    """No Studio view or the demo needs a horizontal scrollbar at this profile.

    Covers the Library, the Composer specimen, the Composer target view with
    the demo connected and a target selected (and the demo's own document
    inside its frame), the pop-out placeholder, and the demo standalone.
    """
    out = Outcome()
    page = ctx.page

    page.goto(ctx.studio_url, wait_until="load")
    out.failures.extend(overflow_failures("Studio Library", page.evaluate(OVERFLOW_JS)))

    page.locator("#modeComposer").click()
    out.failures.extend(overflow_failures("Composer specimen", page.evaluate(OVERFLOW_JS)))

    connect_and_select(ctx)
    out.failures.extend(
        overflow_failures("Composer target view (target selected)", page.evaluate(OVERFLOW_JS))
    )
    out.failures.extend(
        overflow_failures("demo inside the preview frame", target_frame(page).evaluate(OVERFLOW_JS))
    )

    popup = open_popout(ctx)
    try:
        out.failures.extend(
            overflow_failures("Composer pop-out placeholder", page.evaluate(OVERFLOW_JS))
        )
    finally:
        popup.close()

    page.goto(ctx.demo_url, wait_until="load")
    out.failures.extend(overflow_failures("demo (standalone)", page.evaluate(OVERFLOW_JS)))
    return out


def hidden_failures(surface: str, readings: dict[str, str | None]) -> list[str]:
    """Judge computed `display` for each selector: absent or not "none" is a failure.

    `readings` maps selector to the node's computed display, or None when the
    node is not in the page at all. A missing node is a finding too: a
    renamed id would otherwise turn this check into a no-op that passes.
    """
    failures = []
    for selector, display in readings.items():
        if display is None:
            failures.append(f"{surface}: {selector} is not in the page at all")
        elif display != "none":
            failures.append(
                f"{surface}: {selector} should start hidden but computes display: {display}"
            )
    return failures


def check_initial_visibility(ctx: GateContext) -> Outcome:
    """Everything a script reveals later is really invisible on load.

    Reads computed display, not the `hidden` attribute or a class name; see
    HIDDEN_ON_LOAD for why.
    """
    out = Outcome()
    page = ctx.page
    page.goto(ctx.studio_url, wait_until="load")
    for surface, actions, selectors in HIDDEN_ON_LOAD:
        for _, selector in actions:
            page.locator(selector).click()
        readings = page.evaluate(
            """(selectors) => Object.fromEntries(selectors.map(selector => {
                const node = document.querySelector(selector);
                return [selector, node ? getComputedStyle(node).display : null];
            }))""",
            list(selectors),
        )
        out.failures.extend(hidden_failures(surface, readings))
    return out


def touch_target_lines(state: str, small: list[list], already: set | None = None) -> list[str]:
    """One line per distinct undersized target in a state, duplicates collapsed.

    Targets collapse when they are the same kind of element with the same
    smaller side: four identical stepper buttons, or nine filter chips whose
    widths differ by label but whose 33px height is one defect. The count says
    how many places to fix without printing nearly the same line nine times,
    and the first size seen stays in the line as an example.

    `already` holds what earlier states of the same run reported. The Composer
    toolbar is on screen in three of the states, and printing its forty
    controls three times would bury the rest, so each distinct target is
    reported in the first state that shows it.
    """
    seen = already if already is not None else set()
    groups: dict[tuple, list] = {}
    for what, width, height in small:
        key = (what, min(width, height))
        if key in seen:
            continue
        group = groups.setdefault(key, [width, height, 0])
        group[2] += 1
    seen.update(groups)
    return [
        f"{state}: {what} is {width}x{height}"
        + (f" ({count} of them)" if count > 1 else "")
        + f", smaller side under {MIN_TOUCH_TARGET_PX}px"
        for (what, _), (width, height, count) in groups.items()
    ]


def _library(ctx: GateContext) -> None:
    ctx.page.goto(ctx.studio_url, wait_until="load")


def _composer_specimen(ctx: GateContext) -> None:
    _library(ctx)
    ctx.page.locator("#modeComposer").click()


def _demo(ctx: GateContext) -> None:
    ctx.page.goto(ctx.demo_url, wait_until="load")


#: The states the touch-target check drives before measuring.
#:
#: Measuring only what is on screen at load measures almost nothing: the
#: inspector, the code panel and the reconnect banner all start hidden, and
#: a control a person has not reached yet is still a control. Each state is a
#: real interaction away: a click, or the live flow.
TOUCH_TARGET_STATES = (
    ("Studio Library", _library),
    ("Composer specimen", _composer_specimen),
    ("Composer target view, title selected", connect_and_select),
    ("Composer reconnect banner", reach_reconnect_banner),
    ("demo (standalone)", _demo),
)


def check_touch_targets(ctx: GateContext) -> Outcome:
    """Every tappable element reaches 44px on its smaller side. Report-only.

    An element with no box is not rendered, so there is nothing to hit and it
    is skipped.

    A label and its input are one target, and the measurement takes whichever
    of the pair a finger actually lands on. Where the input is visible, the
    input is the target and the caption is skipped. Where the input is clipped
    to a pixel and styled through its label, the label is the target and the
    input is skipped. Measuring both would fail correct markup every time;
    measuring neither is how small targets ship.

    The runner downgrades these failures to REPORT: touch targets are
    visibility for now, not a gate (plan Addendum 4).
    """
    out = Outcome()
    reported: set = set()
    for state, reach in TOUCH_TARGET_STATES:
        reach(ctx)
        small = ctx.page.evaluate(TOUCH_TARGETS_JS, [INTERACTIVE_SELECTOR, MIN_TOUCH_TARGET_PX])
        out.failures.extend(touch_target_lines(state, small, reported))
    return out
