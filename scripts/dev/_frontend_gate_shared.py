"""Shared vocabulary for the frontend gate: profiles, findings, context, waits.

Every other gate module imports from here and this module imports from none
of them, so the dependency arrow only ever points one way. It holds what at
least three modules need (the rule of three): the viewport profiles, the
`Outcome` a check returns, the `GateContext` a check receives, and the
bounded-wait helpers.

Nothing here imports Playwright. The unit tests load this module in the plain
`unittest` suite, and a missing browser must not stop them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[2]

STUDIO_HTML = "font_kit_studio_v0.1.1.html"
DEMO_PATH = "/demo/"

#: The device profiles every check can ask for.
#:
#: Width is not the whole story. A tablet in landscape and a touch laptop are
#: both wide and both touched, so a touch-target rule written against a width
#: misses them. The third profile is a wide screen with a coarse pointer.
#: Chromium and Firefox both drive (pointer: coarse) from `has_touch`.
#:
#: `is_mobile` is deliberately off. It changes device scale and scrollbars,
#: which would move every measurement the gate takes.
DESKTOP = "desktop"
MOBILE = "mobile"
TOUCH_WIDE = "wide touch"
VIEWPORTS = {
    DESKTOP: {"viewport": {"width": 1280, "height": 720}},
    MOBILE: {"viewport": {"width": 390, "height": 844}, "has_touch": True},
    TOUCH_WIDE: {"viewport": {"width": 1280, "height": 800}, "has_touch": True},
}

#: Engines the gate knows how to launch, in the order they run.
KNOWN_ENGINES = ("chromium", "firefox")
DEFAULT_ENGINES = KNOWN_ENGINES

#: Studio's own selectors. One copy, because the live, layout, theme and
#: network checks all drive the same page.
HERO_TITLE = '[data-design-id="landing.hero.title"]'
HERO_TITLE_ID = "landing.hero.title"
CONNECTED_PATTERN = r"^Connected \(\d+ targets?\)$"

#: How long a check waits for something the page is expected to do. A wait
#: that succeeds returns at once, so a generous bound costs nothing on a
#: healthy page and only buys headroom on a loaded CI runner.
REQUEST_WAIT_MS = 5000
CONNECT_WAIT_MS = 15000

#: How often a page-side wait re-checks its condition, in milliseconds.
#:
#: Playwright's default polls on `requestAnimationFrame`, and a browser pauses
#: animation frames in a frame that is scrolled out of view. The demo iframe
#: sits above the inspector, so after a person scrolls down to edit (which is
#: exactly what the mobile profile does) a default wait on that frame never
#: fires, even though the condition is already true: a "timeout" that was
#: really a throttled poll. A fixed interval has no such dependency.
POLL_MS = 50

#: A short fixed wait kept only where a check must prove NOTHING MORE arrives.
NOTHING_MORE_MS = 150

#: Clicking budget for a control. Short, because a miss means the control is
#: absent or covered, and waiting 30 s does not change that.
ACTION_TIMEOUT_MS = 5000


class GateStateError(Exception):
    """A helper could not drive the page into the state a check needs.

    Raised, not returned, because there is nothing left to measure. The
    runner turns it into a FAIL that names the check, profile and engine, so
    "Studio never reported Connected" is a finding rather than a crash.
    """


@dataclass
class Outcome:
    """What one check run found, before the runner stamps it with a profile.

    `failures` are enforced findings (they change the exit code unless the
    check itself is report-only). `reports` are findings the check declares
    advisory on its own (legacy-surface contrast). `skips` say a part of the
    run could not happen and why. A run that returns an empty Outcome passed.
    """

    failures: list[str] = field(default_factory=list)
    reports: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)

    def merge(self, other: Outcome) -> None:
        """Fold another outcome into this one, for checks built from sub-checks."""
        self.failures.extend(other.failures)
        self.reports.extend(other.reports)
        self.skips.extend(other.skips)


@dataclass
class NetworkLog:
    """Every request a page tried to make beyond the two served loopback origins.

    The browser context routes everything else to this log and aborts it, so
    the gate is deterministic and offline by construction. The free-fonts
    check is the only one that lets Google Fonts through, and it still logs.
    """

    external: list[str] = field(default_factory=list)


@dataclass
class GateContext:
    """Everything a check needs, built fresh for each (check, profile, engine) run.

    A fresh browser context per run keeps checks independent: a stored
    preference, a route or a half-finished edit from one check cannot leak
    into the next, and touch emulation (which belongs to a context) matches
    the profile.
    """

    page: object
    browser_context: object
    studio_origin: str
    target_origin: str
    engine: str
    profile: str
    offline: bool
    network: NetworkLog
    #: Uncaught page exceptions, collected for the whole run. Checks that drive
    #: Studio assert this stays empty: a handler that throws mid-edit is a
    #: defect even when the visible result happens to look right.
    errors: list[str] = field(default_factory=list)

    @property
    def touch(self) -> bool:
        """True when the profile emulates a coarse pointer."""
        return bool(VIEWPORTS[self.profile].get("has_touch"))

    @property
    def studio_url(self) -> str:
        """Studio with no target: Library and Composer only."""
        return f"{self.studio_origin}/{STUDIO_HTML}"

    @property
    def demo_url(self) -> str:
        """The demo app on its own origin, cross-origin from Studio on purpose."""
        return f"{self.target_origin}{DEMO_PATH}"

    @property
    def live_url(self) -> str:
        """Studio opened with ?target=, which switches to Composer and connects."""
        return f"{self.studio_url}?target={quote(self.demo_url, safe=':/')}"

    def asset_url(self, repo_path: str) -> str:
        """A repository file as served from the Studio origin."""
        return f"{self.studio_origin}/{repo_path}"


def is_timeout(error: BaseException) -> bool:
    """True for a Playwright timeout, without importing Playwright here.

    Playwright's `TimeoutError` lives in a module this file must not import
    (the unit tests run without a browser), and its class is named plainly.
    """
    return type(error).__name__ == "TimeoutError"


def wait_until(page, expression: str, arg=None, timeout_ms: int = REQUEST_WAIT_MS) -> bool:
    """Wait, bounded, for a page condition. Returns whether it became true.

    Returns False instead of raising so the caller can read the page and
    report what it actually shows ("the badge says Disconnected") rather
    than a bare timeout. A condition that holds costs no time at all.
    """
    try:
        page.wait_for_function(expression, arg=arg, timeout=timeout_ms, polling=POLL_MS)
    except Exception as error:  # noqa: BLE001 - only a timeout is "not yet"
        if is_timeout(error):
            return False
        raise
    return True


def deadline_ms(page, wait_ms: int = REQUEST_WAIT_MS) -> int:
    """A ``Date.now()`` value `wait_ms` ahead, read from the page clock.

    For predicates that must stop waiting on their own. A page-side
    `|| Date.now() > deadline` lets a check read a state that never arrived
    and fail with what it saw, instead of timing out blind.
    """
    return page.evaluate("(ms) => Date.now() + ms", wait_ms)


def reach_state(page, actions) -> None:
    """Drive the page into one state, using real clicks and selections.

    Real interactions rather than dispatched events: a synthetic event can
    reach a listener that a genuine click could never trigger, and the gate
    is about what a person can do. Touch contexts still click with the mouse
    here; taps are used only where the touch itself is what is being proved.
    """
    for action in actions:
        kind, selector = action[0], action[1]
        target = page.locator(selector).first
        if kind == "click":
            target.click(timeout=ACTION_TIMEOUT_MS)
        elif kind == "select":
            target.select_option(action[2], timeout=ACTION_TIMEOUT_MS)
        else:  # pragma: no cover - a typo in a table, not a page fault
            raise ValueError(f"unknown state action {kind!r}")


def resolve_colour(page, value: str) -> str:
    """Resolve a CSS colour value through a probe element to a computed string.

    `getPropertyValue` on a custom property can return the unresolved
    `var(--other)` text rather than a colour, so comparing raw token text is
    unreliable. Painting a probe forces the cascade to resolve it, and the
    answer is exactly what the browser would paint.
    """
    return page.evaluate(
        """(value) => {
            const probe = document.createElement('div');
            document.body.appendChild(probe);
            probe.style.backgroundColor = value;
            const computed = getComputedStyle(probe).backgroundColor;
            probe.remove();
            return computed;
        }""",
        value,
    )
