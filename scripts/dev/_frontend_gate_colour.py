"""Pure colour maths for the frontend gate.

Provenance: copied from ScrobbleScope's `scripts/dev/_frontend_gate_colour.py`
(a sibling project's gate) and trimmed for fontkit. The
parsing, alpha-compositing, relative-luminance and contrast-ratio functions
below are that file's text, unchanged. Left behind because they serve
ScrobbleScope's own checks: `_clamp_px` (a CSS `clamp()` mirror),
`_is_forbidden_surface`, `_worst_divider_contrast` and
`_divider_contrast_failure` (divider tokens named `--shell-border`). The one
addition is `flatten_layers`, which resolves a stack of translucent
backgrounds onto the first opaque one; it is pure, so it is unit-tested here
rather than in a browser.

The helpers take numbers and strings, never a `page`, so plain `unittest`
can pin them without launching anything. A WCAG contrast number that is
wrong by a rounding rule would make every contrast check lie in the same
direction, so this is the part of the gate that most deserves a fast test.

Source of the maths: WCAG 2.x relative-luminance and contrast-ratio
definitions.
"""

from __future__ import annotations

import re

__all__ = [
    "_composite_over",
    "_contrast_ratio",
    "_parse_rgb_string",
    "_relative_luminance",
    "flatten_layers",
]

#: The computed-colour serializations this module can read.
#:
#: Measured in both engines the gate runs, 2026-09-20: every design token the
#: gate reads comes back as `rgb()` or `rgba()`, except a `color-mix()`, which
#: both engines serialize as `color(srgb r g b)` with channels in 0-1 rather
#: than 0-255. Anything else -- `oklch()`, `lab()`, `hsl()`, or `color()` in a
#: wider gamut -- also leads with three numbers, and reading those as sRGB
#: channels yields a plausible ratio for a colour nobody painted.
_RGB_FUNCTION_RE = re.compile(r"^rgba?\(", re.IGNORECASE)
_COLOR_SRGB_RE = re.compile(r"^color\(\s*srgb\s", re.IGNORECASE)
#: One CSS number: optional sign, digits with an optional fraction, optional
#: exponent. A computed tiny channel serialises with an exponent (Chromium gives
#: `color(srgb 1.00000e-7 0.2 0.3)`), and splitting at the "e" would read it as
#: two numbers and shift every channel after it.
_NUMBER_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?", re.IGNORECASE)


def _parse_rgb_string(value: str) -> tuple[float, float, float, float]:
    """Parse a computed colour string into an (r, g, b, a) tuple of 0-255 channels.

    Handles ``rgb()``/``rgba()`` and the ``color(srgb r g b / a)`` form, which
    is how a browser serializes a computed ``color-mix()``. That form states
    its channels in 0-1, and reading them as 0-255 collapses any such colour
    to near black -- the results table's own surface is a ``color-mix()``, so
    a contrast measurement against it reported 1.19:1 for ink that plainly
    reads against it.
    """
    text = value.strip()
    if _COLOR_SRGB_RE.match(text):
        scale = 255.0
    elif _RGB_FUNCTION_RE.match(text):
        scale = 1.0
    else:
        raise ValueError(
            f"unsupported colour serialization {value!r}: this module reads "
            "rgb(), rgba() and color(srgb ...) only. Teach it the new form "
            "rather than letting a contrast measurement guess at one."
        )
    numbers = [float(part) for part in _NUMBER_RE.findall(text)]
    red, green, blue = (number * scale for number in numbers[:3])
    alpha = numbers[3] if len(numbers) > 3 else 1.0
    return red, green, blue, alpha


def _composite_over(
    foreground: tuple[float, float, float, float],
    background: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Alpha-composite a translucent foreground colour over an opaque one."""
    fg_red, fg_green, fg_blue, alpha = foreground
    bg_red, bg_green, bg_blue = background
    return (
        fg_red * alpha + bg_red * (1 - alpha),
        fg_green * alpha + bg_green * (1 - alpha),
        fg_blue * alpha + bg_blue * (1 - alpha),
    )


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance of an sRGB colour given as 0-255 channels."""

    def channel(value: float) -> float:
        normalised = value / 255
        if normalised <= 0.03928:
            return normalised / 12.92
        return ((normalised + 0.055) / 1.055) ** 2.4

    red, green, blue = rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(
    rgb_a: tuple[float, float, float], rgb_b: tuple[float, float, float]
) -> float:
    """WCAG contrast ratio between two opaque sRGB colours."""
    luminance_a = _relative_luminance(rgb_a) + 0.05
    luminance_b = _relative_luminance(rgb_b) + 0.05
    return max(luminance_a, luminance_b) / min(luminance_a, luminance_b)


# --- Added for fontkit (not in the ScrobbleScope original) -------------------

#: Painted underneath everything when no ancestor background is opaque. A
#: browser canvas is white unless the page says otherwise, and the pages this
#: gate measures all paint their own body background, so this is a floor that
#: should never decide a result.
CANVAS_RGB = (255.0, 255.0, 255.0)


def flatten_layers(
    layers: list[str], canvas: tuple[float, float, float] = CANVAS_RGB
) -> tuple[float, float, float]:
    """Resolve a stack of background colours to the one opaque colour a reader sees.

    ``layers`` runs from the element outwards (element, parent, grandparent...),
    already filtered to backgrounds that paint something. Colours are
    composited from the outside in: walk out until the first opaque layer,
    use it as the base, then paint every nearer translucent layer over it. A
    translucent sticky bar over a page background is judged against the
    blend, never against its own raw rgba() channels, which would claim a
    92%-opaque surface is whatever its rgb() says.

    If no layer is opaque the canvas colour is the base.
    """
    parsed = [_parse_rgb_string(layer) for layer in layers]
    base = canvas
    nearer: list[tuple[float, float, float, float]] = []
    for colour in parsed:
        if colour[3] >= 1.0:
            base = colour[:3]
            break
        nearer.append(colour)
    result = base
    for colour in reversed(nearer):
        result = _composite_over(colour, result)
    return result
