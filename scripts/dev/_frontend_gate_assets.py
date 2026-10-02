"""Logo paint: the README logos render legibly on GitHub's light and dark pages.

The logos are the first thing a visitor to the repository sees, and an SVG can
look right in an editor and still paint badly in the place that matters: a
`<text>` element needs a font GitHub does not load, a script or external
reference is stripped, and a colour that reads on white can vanish on
`#0d1117`. This check does not trust the file. It loads each logo in a real
browser two ways: as an image (what GitHub's `<img>` shows, read back pixel by
pixel through a canvas) and as inline markup (the computed paint of every
shape), then measures contrast of every painted colour against the page
background the logo is designed for.

Static structure is checked by a pure function over the file text, so the
plain unittest suite pins it, and the real files are run through it there too.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from scripts.dev._frontend_gate_colour import (
    _composite_over,
    _contrast_ratio,
    _parse_rgb_string,
)
from scripts.dev._frontend_gate_shared import (
    REPO_ROOT,
    GateContext,
    Outcome,
    resolve_colour,
)

#: Smallest contrast a painted colour may have against its page. 3:1 is the
#: WCAG non-text and large-text threshold, which is the right bar for a
#: logotype that is drawn at display size, not for body copy.
LOGO_MIN_CONTRAST = 3.0

#: GitHub's page backgrounds. Each logo is designed for exactly one of them.
GITHUB_LIGHT = "#ffffff"
GITHUB_DARK = "#0d1117"

#: (file under docs/assets, the GitHub background it is designed for)
LOGOS = (
    ("fontkit-logo-light.svg", GITHUB_LIGHT),
    ("fontkit-logo-dark.svg", GITHUB_DARK),
)
LOGO_DIR = "docs/assets"

#: Elements that must not appear in a logo: text needs a font GitHub will not
#: load; scripts, foreign content, embedded images and links are stripped or
#: blocked by GitHub's sanitiser and by browsers when used as an <img>.
FORBIDDEN_ELEMENTS = frozenset(
    {"text", "tspan", "textpath", "script", "foreignobject", "image", "a", "iframe", "use", "link"}
)

#: The namespace declaration is the one absolute URL a clean SVG has.
SVG_NAMESPACES = ("http://www.w3.org/2000/svg", "http://www.w3.org/1999/xlink")

#: Pixels a colour must cover before it counts as "painted" in the image
#: read-back, at the render size below. Below this it is noise at an edge.
MIN_COLOUR_PIXELS = 30

#: Render the image at twice its intrinsic size so thin strokes still produce
#: fully opaque pixels to measure, not only anti-aliased ones.
IMAGE_SCALE = 2

INLINE_PAINT_JS = """() => {
    const shapes = [...document.documentElement.querySelectorAll(
        'path, rect, circle, ellipse, line, polyline, polygon')]
        .filter(el => !el.closest('mask, defs, clipPath, symbol'));
    const opacityOf = (el) => {
        let opacity = 1;
        for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
            opacity *= Number(getComputedStyle(node).opacity);
        }
        return opacity;
    };
    const seen = new Map();
    for (const el of shapes) {
        const style = getComputedStyle(el);
        const opacity = opacityOf(el);
        const paints = [];
        if (style.fill !== 'none') {
            paints.push(['fill', style.fill, opacity * Number(style.fillOpacity)]);
        }
        if (style.stroke !== 'none' && parseFloat(style.strokeWidth) > 0) {
            paints.push(['stroke', style.stroke, opacity * Number(style.strokeOpacity)]);
        }
        for (const [kind, colour, alpha] of paints) {
            const key = `${kind}|${colour}|${alpha}`;
            const entry = seen.get(key) || {kind, colour, alpha, count: 0};
            entry.count += 1;
            seen.set(key, entry);
        }
    }
    return [...seen.values()];
}"""

IMAGE_PAINT_JS = """async ([url, scale]) => {
    const image = new Image();
    image.src = url;
    await image.decode();
    const width = Math.round(image.naturalWidth * scale);
    const height = Math.round(image.naturalHeight * scale);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    context.drawImage(image, 0, 0, width, height);
    const data = context.getImageData(0, 0, width, height).data;
    const colours = {};
    let painted = 0;
    for (let i = 0; i < data.length; i += 4) {
        if (data[i + 3] === 0) continue;
        painted += 1;
        if (data[i + 3] !== 255) continue;
        const key = `rgb(${data[i]}, ${data[i + 1]}, ${data[i + 2]})`;
        colours[key] = (colours[key] || 0) + 1;
    }
    return {painted, total: width * height, colours};
}"""


def logo_static_failures(name: str, svg_text: str) -> list[str]:
    """Judge the SVG text: well-formed, and no text, script or external reference.

    Pure, so the real files are checked in the fast unittest suite as well as
    by the gate. Attribute checks run on the parsed tree; the `url(` scan
    runs on every attribute and `<style>` body, since a paint server or
    filter pointing off-document is as external as an href.
    """
    try:
        root = ElementTree.fromstring(svg_text)
    except ElementTree.ParseError as error:
        return [f"{name} is not well-formed SVG: {error}"]
    failures = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower() if isinstance(element.tag, str) else ""
        if tag in FORBIDDEN_ELEMENTS:
            failures.append(f"{name} contains a <{tag}> element")
        if tag == "style" and "@import" in (element.text or ""):
            failures.append(f"{name} imports a stylesheet")
        values = [(key.rsplit("}", 1)[-1], value) for key, value in element.attrib.items()]
        if tag == "style" and element.text:
            values.append(("style", element.text))
        for key, value in values:
            if key.lower() == "href" and not value.startswith("#"):
                failures.append(f"{name} has an external reference: {key}={value!r}")
            for reference in re.findall(r"url\(\s*['\"]?([^)'\"]*)", value):
                if not reference.startswith("#"):
                    failures.append(f"{name} has an external reference: url({reference})")
            for address in re.findall(r"https?://[^\s'\"<>)]+", value):
                if address not in SVG_NAMESPACES:
                    failures.append(f"{name} mentions an absolute address: {address}")
    return failures


def _rgb(colour: str) -> tuple[float, float, float]:
    """The opaque channels of a resolved colour string."""
    return _parse_rgb_string(colour)[:3]


def inline_paint_failures(name: str, background: str, paints: list[dict]) -> list[str]:
    """Judge computed paints from the inline SVG against the page background.

    Each `paints` entry is {kind, colour, alpha, count}. A translucent paint
    is composited over the background first: contrast is judged on the colour
    a visitor sees, never on the declared channels.
    """
    if not paints:
        return [f"{name} (inline) paints no fill or stroke at all"]
    page = _rgb(background)
    failures = []
    for paint in paints:
        red, green, blue, _ = _parse_rgb_string(paint["colour"])
        seen = _composite_over((red, green, blue, paint["alpha"]), page)
        ratio = _contrast_ratio(seen, page)
        if ratio < LOGO_MIN_CONTRAST:
            failures.append(
                f"{name} (inline) {paint['kind']} {paint['colour']} on {background} is "
                f"{ratio:.2f}:1 ({paint['count']} shapes), expected at least {LOGO_MIN_CONTRAST:.0f}:1"
            )
    return failures


def image_paint_failures(name: str, background: str, reading: dict) -> list[str]:
    """Judge the pixel read-back of the logo rendered as an image.

    Only fully opaque pixels are measured (anti-aliased edges blend with the
    page by definition) and only colours that cover enough pixels to be a
    deliberate part of the design.
    """
    if reading["painted"] < MIN_COLOUR_PIXELS:
        return [f"{name} (image) rendered {reading['painted']} painted pixels; it is blank"]
    page = _rgb(background)
    failures = []
    measured = 0
    for colour, count in reading["colours"].items():
        if count < MIN_COLOUR_PIXELS:
            continue
        measured += 1
        ratio = _contrast_ratio(_rgb(colour), page)
        if ratio < LOGO_MIN_CONTRAST:
            failures.append(
                f"{name} (image) {colour} on {background} is {ratio:.2f}:1 "
                f"({count} px), expected at least {LOGO_MIN_CONTRAST:.0f}:1"
            )
    if not measured:
        failures.append(f"{name} (image) has no opaque colour covering {MIN_COLOUR_PIXELS} pixels")
    return failures


def check_logo_paint(ctx: GateContext) -> Outcome:
    """Both logos: clean structure, and every painted colour reaches 3:1 on its GitHub page.

    The file is read from the repository and the paint is read from a real
    render served by the dev server, so what is judged is what ships.
    """
    out = Outcome()
    page = ctx.page
    for filename, background in LOGOS:
        path = Path(REPO_ROOT) / LOGO_DIR / filename
        out.failures.extend(logo_static_failures(filename, path.read_text(encoding="utf-8")))
        url = ctx.asset_url(f"{LOGO_DIR}/{filename}")

        # Resolve the GitHub background through the browser's own colour
        # parser, so the comparison colour is what a page would paint.
        page.goto(ctx.studio_url, wait_until="load")
        resolved = resolve_colour(page, background)
        reading = page.evaluate(IMAGE_PAINT_JS, [url, IMAGE_SCALE])
        out.failures.extend(image_paint_failures(filename, resolved, reading))

        # The SVG as a standalone document is the isolated inline render: no
        # page stylesheet can restyle its shapes.
        page.goto(url, wait_until="load")
        out.failures.extend(inline_paint_failures(filename, resolved, page.evaluate(INLINE_PAINT_JS)))
    return out
