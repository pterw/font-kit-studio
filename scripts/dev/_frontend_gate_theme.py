"""Theme contrast: Studio's text reads against its own surface in light and dark.

Studio has one dark switch (`body.dark`) and a few dozen colour tokens, and a
token pair that reads in one theme can fail in the other. Contrast is judged
on what the browser paints, never on the token text: each visible piece of
text reports its computed colour and the stack of backgrounds behind it, and
the pure maths flattens that stack onto the first opaque ancestor background
(a translucent sticky bar over the page is judged against the blend).

Two tiers (plan Addendum 4):

* v0.2 surfaces (bridge bar, Live Target inspector, code panel, reconnect
  banner, their warning states) are enforced: body text needs 4.5:1.
* legacy surfaces (Library, Composer setup, the slot inspector) are
  report-only: they predate this gate and are listed, not blocking.

The judgement functions are pure and unit-tested; the browser helpers only
read computed values.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_colour import (
    _composite_over,
    _contrast_ratio,
    _parse_rgb_string,
    flatten_layers,
)
from scripts.dev._frontend_gate_live import (
    connect_and_select,
    reach_reconnect_banner,
)
from scripts.dev._frontend_gate_shared import (
    GateContext,
    Outcome,
    resolve_colour,
)

#: WCAG 2.x thresholds: normal text 4.5:1, large text 3:1. Large is 24 px, or
#: 18.66 px (14 pt) and bold.
BODY_TEXT_RATIO = 4.5
LARGE_TEXT_RATIO = 3.0
LARGE_TEXT_PX = 24.0
LARGE_BOLD_TEXT_PX = 18.66

THEMES = ("light", "dark")

#: Studio surfaces by tier. Each entry is (name, root selectors, excluded
#: selectors). Excluded subtrees are measured elsewhere or are user content
#: (the Composer canvas paints whatever the person chose, so it is not
#: Studio's own contrast to judge).
LEGACY_LIBRARY = (
    ("Library header and controls", ("header", ".mode-nav", ".controls"), ()),
    ("Library cards and notes", ("main",), ()),
)
LEGACY_COMPOSER = (
    ("Composer setup", (".composer-toolbar",), ("#targetAppBridgeBar",)),
    ("Composer slot inspector", ("#slotInspector",), ()),
)
V02_IDLE = (("Bridge bar, idle", ("#targetAppBridgeBar",), ()),)
V02_CONNECTED = (
    ("Bridge bar, connected", ("#targetAppBridgeBar",), ()),
    ("Live Target inspector", ("#slotInspector",), ()),
    ("Code panel", ("#liveCodePanel",), ()),
)
V02_BANNER = (("Reconnect banner", ("#liveReconnectBanner",), ()),)
#: Warning and error colours exist only in states a healthy run never shows,
#: so they are the likeliest to have been tuned for one theme. Measured by
#: putting these elements in the state the app itself would (same attributes,
#: same visibility), then reading their computed paint.
V02_ERROR_STATES = (
    (
        "Error and warning states",
        ("#bridgeStatusBadge", "#bridgeWarning", "#liveCodeWarnings", "#liveCodeStatus"),
        (),
    ),
)

#: Puts the warning and error elements into the states the app puts them in.
FORCE_ERROR_STATES_JS = """() => {
    const badge = document.querySelector('#bridgeStatusBadge');
    badge.dataset.state = 'error';
    badge.textContent = 'No bridge detected';
    const warning = document.querySelector('#bridgeWarning');
    warning.hidden = false;
    warning.querySelector('#bridgeWarningText').textContent = 'The target reported a problem.';
    const warnings = document.querySelector('#liveCodeWarnings');
    warnings.hidden = false;
    const item = document.createElement('li');
    item.textContent = 'Runtime warning from the target.';
    warnings.replaceChildren(item);
    const status = document.querySelector('#liveCodeStatus');
    status.dataset.state = 'error';
    status.textContent = 'Could not save the overrides file.';
}"""

#: Reads every visible piece of text under the roots: its computed colour, the
#: backgrounds from the element outwards, and what decides the size class.
#: Disabled controls are exempt (WCAG exempts inactive components), as are
#: hidden and zero-size nodes, which nobody can read.
CONTRAST_JS = """([roots, excludes]) => {
    const TEXT_INPUTS = ['text', 'search', 'url', 'email', 'number', 'tel', 'password', ''];
    const visible = (el) => typeof el.checkVisibility === 'function'
        ? el.checkVisibility({checkVisibilityCSS: true})
        : el.getClientRects().length > 0;
    const describe = (el) => {
        const name = el.tagName.toLowerCase();
        if (el.id) return `${name}#${el.id}`;
        const cls = (el.getAttribute('class') || '').trim().split(/\\s+/)[0];
        return cls ? `${name}.${cls}` : name;
    };
    const ownText = (el) => {
        if (el.tagName === 'INPUT') {
            return TEXT_INPUTS.includes(el.type) ? el.value : '';
        }
        if (el.tagName === 'TEXTAREA') return el.value;
        if (el.tagName === 'SELECT') {
            return el.selectedOptions.length ? el.selectedOptions[0].textContent : '';
        }
        return [...el.childNodes].filter(n => n.nodeType === 3)
            .map(n => n.textContent).join(' ').trim();
    };
    const transparent = (value) => value === 'transparent' || /^rgba\\(.*,\\s*0\\)$/.test(value);
    // Alpha of a computed colour: rgb() is opaque, rgba() ends in it, and
    // color(srgb ...) (how a color-mix() serialises) carries it after a slash.
    // A tiny alpha serialises with an exponent (`/ 1.00000e-7`), so read a whole CSS number.
    const slashAlpha = /\\/\\s*([+-]?(?:\\d+\\.?\\d*|\\.\\d+)(?:e[+-]?\\d+)?)\\s*\\)$/i;
    const commaAlpha = /^rgba\\(.*,\\s*([+-]?(?:\\d+\\.?\\d*|\\.\\d+)(?:e[+-]?\\d+)?)\\)$/i;
    const alphaOf = (value) => {
        const slash = value.match(slashAlpha);
        if (slash) return Number(slash[1]);
        const comma = value.match(commaAlpha);
        return comma ? Number(comma[1]) : 1;
    };
    const samples = [];
    const seen = new Set();
    for (const rootSelector of roots) {
        for (const root of document.querySelectorAll(rootSelector)) {
            for (const el of [root, ...root.querySelectorAll('*')]) {
                if (seen.has(el) || !visible(el)) continue;
                seen.add(el);
                if (excludes.some(selector => el.closest(selector))) continue;
                if (el.closest('[disabled], [aria-disabled="true"]')) continue;
                const text = ownText(el);
                if (!text.trim()) continue;
                const style = getComputedStyle(el);
                // Walk outwards collecting backgrounds, stopping at the first
                // opaque one: nothing behind it shows. A background image met
                // before that point cannot be reduced to one colour.
                const layers = [];
                let image = false;
                let settled = false;
                let opacity = 1;
                for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
                    const nodeStyle = getComputedStyle(node);
                    opacity *= Number(nodeStyle.opacity);
                    if (settled) continue;
                    if (nodeStyle.backgroundImage !== 'none') image = true;
                    if (!transparent(nodeStyle.backgroundColor)) {
                        layers.push(nodeStyle.backgroundColor);
                        if (alphaOf(nodeStyle.backgroundColor) >= 1) settled = true;
                    }
                }
                samples.push({
                    what: describe(el),
                    text: text.trim().replace(/\\s+/g, ' ').slice(0, 28),
                    color: style.color,
                    layers,
                    opacity,
                    size: parseFloat(style.fontSize),
                    weight: parseInt(style.fontWeight, 10) || 400,
                    image,
                });
            }
        }
    }
    return samples;
}"""


def required_ratio(size_px: float, weight: int) -> float:
    """The WCAG threshold for text of this size: 3:1 when large, else 4.5:1."""
    if size_px >= LARGE_TEXT_PX or (size_px >= LARGE_BOLD_TEXT_PX and weight >= 700):
        return LARGE_TEXT_RATIO
    return BODY_TEXT_RATIO


def sample_ratio(sample: dict) -> tuple[float, tuple, tuple]:
    """Contrast of one text sample: (ratio, text rgb, background rgb).

    The background is every translucent layer composited onto the first
    opaque ancestor. The text colour's own alpha, and any ancestor opacity,
    are composited over that background too, so faded text is judged as
    faded.
    """
    background = flatten_layers(sample["layers"])
    red, green, blue, alpha = _parse_rgb_string(sample["color"])
    shown = _composite_over((red, green, blue, alpha * sample["opacity"]), background)
    return _contrast_ratio(shown, background), shown, background


def _rgb_text(rgb: tuple) -> str:
    """Compact rgb(r, g, b) text for messages."""
    return "rgb({}, {}, {})".format(*(round(channel) for channel in rgb))


def judge_samples(label: str, samples: list[dict]) -> tuple[list[str], list[str], int]:
    """Judge text samples against WCAG: (failing lines, unmeasurable lines, samples measured).

    Identical failures (same element kind, colours and ratio) collapse into
    one line with a count, so a dozen labels sharing one bad token read as one
    defect. Text on a background image cannot be measured from computed
    colours alone and is reported rather than guessed at.
    """
    failures: dict[tuple, list] = {}
    unmeasured: list[str] = []
    measured = 0
    for sample in samples:
        if sample["image"]:
            unmeasured.append(
                f"{label}: {sample['what']} {sample['text']!r} sits on a background image, "
                "so its contrast cannot be measured from computed colours"
            )
            continue
        measured += 1
        ratio, shown, background = sample_ratio(sample)
        needed = required_ratio(sample["size"], sample["weight"])
        if ratio >= needed:
            continue
        key = (sample["what"], _rgb_text(shown), _rgb_text(background), round(ratio, 2), needed)
        entry = failures.setdefault(key, [sample["text"], 0])
        entry[1] += 1
    lines = []
    for (what, shown, background, ratio, needed), (text, count) in failures.items():
        lines.append(
            f"{label}: {what} {text!r} {shown} on {background} is {ratio:.2f}:1, "
            f"expected at least {needed}:1" + (f" ({count} of them)" if count > 1 else "")
        )
    return lines, unmeasured, measured


def set_theme(ctx: GateContext, theme: str, back_to_composer: bool) -> None:
    """Switch to the requested theme with Studio's own toggle.

    The toggle lives in the Library view, so from Composer the helper goes
    there and returns. Using the real control (not setting a class) means a
    broken toggle is a finding of this check.
    """
    page = ctx.page
    dark = page.evaluate("document.body.classList.contains('dark')")
    if dark == (theme == "dark"):
        return
    if back_to_composer:
        page.locator("#modeLibrary").click()
    page.locator("#themeToggle").click()
    if back_to_composer:
        page.locator("#modeComposer").click()


def theme_failures(ctx: GateContext, theme: str, light_background: list) -> list[str]:
    """Prove the requested theme is the one being measured.

    A contrast result for the wrong theme is worse than none: it would say
    "dark passes" for a page still painted light. The body must carry the
    class, paint the token the theme defines, and (for dark) differ from the
    light background recorded earlier.
    """
    page = ctx.page
    has_class = page.evaluate("document.body.classList.contains('dark')")
    painted = page.evaluate("getComputedStyle(document.body).backgroundColor")
    token = resolve_colour(page, "var(--bg)")
    failures = []
    if has_class != (theme == "dark"):
        failures.append(f"{theme}: body.dark is {has_class} after toggling the theme")
    if painted != token:
        failures.append(f"{theme}: body paints {painted} but --bg resolves to {token}")
    if theme == "light":
        light_background.append(painted)
    elif light_background and painted == light_background[0]:
        failures.append("dark: the page background did not change from light")
    return failures


def _measure(ctx, theme, surfaces, enforced, out, expected_text=True) -> None:
    """Measure a group of surfaces and file the findings by tier.

    Enforced surfaces must also measure at least one piece of text: a
    selector that went stale would otherwise "pass" by measuring nothing.
    """
    for name, roots, excludes in surfaces:
        label = f"[{theme}] {name}"
        samples = ctx.page.evaluate(CONTRAST_JS, [list(roots), list(excludes)])
        lines, unmeasured, measured = judge_samples(label, samples)
        (out.failures if enforced else out.reports).extend(lines)
        out.reports.extend(unmeasured)
        if enforced and expected_text and measured == 0:
            out.failures.append(f"{label}: no visible text was measured, so nothing was checked")


def check_theme_contrast(ctx: GateContext) -> Outcome:
    """Light and dark: v0.2 surfaces enforced at 4.5:1, legacy surfaces reported.

    Each theme walks the same states: Library, Composer specimen, connected
    with a target selected, error and warning states, and the reconnect
    banner. v0.2 findings go to `failures`; legacy findings go to `reports`.
    """
    out = Outcome()
    page = ctx.page
    light_background: list = []
    for theme in THEMES:
        page.goto(ctx.studio_url, wait_until="load")
        set_theme(ctx, theme, back_to_composer=False)
        out.failures.extend(theme_failures(ctx, theme, light_background))
        _measure(ctx, theme, LEGACY_LIBRARY, False, out)

        page.locator("#modeComposer").click()
        _measure(ctx, theme, LEGACY_COMPOSER, False, out)
        _measure(ctx, theme, V02_IDLE, True, out)

        connect_and_select(ctx)
        set_theme(ctx, theme, back_to_composer=True)
        out.failures.extend(theme_failures(ctx, theme, light_background))
        _measure(ctx, theme, V02_CONNECTED, True, out)
        page.evaluate(FORCE_ERROR_STATES_JS)
        _measure(ctx, theme, V02_ERROR_STATES, True, out)

        reach_reconnect_banner(ctx)
        set_theme(ctx, theme, back_to_composer=True)
        _measure(ctx, theme, V02_BANNER, True, out)
    return out
