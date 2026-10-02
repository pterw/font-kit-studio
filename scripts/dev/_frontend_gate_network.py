"""Network checks: what the apps request on first load, and whether free fonts arrive.

Two opposite questions about the same boundary. The isolation check proves
the apps ask nothing of the outside world until a person asks them to (the
demo never does). The free-fonts check then turns the network on
and proves that when a person does ask, every library family really arrives
as a usable face. Global rule 7 is the reason for both: free generic
defaults, with paid or account-bound providers strictly opt-in.

The judgements are pure functions of URL lists and measured counts so the
plain unittest suite can pin them without a browser.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from scripts.dev._frontend_gate_live import connect_studio
from scripts.dev._frontend_gate_shared import (
    CONNECT_WAIT_MS,
    NOTHING_MORE_MS,
    GateContext,
    Outcome,
    wait_until,
)

GOOGLE_CSS_HOST = "fonts.googleapis.com"
GOOGLE_CSS_PATH = "/css2"

#: How long the free-fonts check waits for Google Fonts to answer for all
#: sixteen stylesheets. Studio itself gives up reporting "still waiting" at
#: 8 s, so 30 s covers a slow link without hiding a dead one.
FONTS_NETWORK_WAIT_MS = 30000

#: Studio's own status line once the load settles (it also reports partial
#: failure and a timeout). "Loading ..." is the in-progress text.
FONT_STATUS_SETTLED = (
    '() => /^(Loaded \\d+\\/\\d+|Still waiting)/.test('
    'document.querySelector("#freeFontStatus").textContent)'
)

#: Takes the family names; returns {family: [faces found, faces loaded]}.
FONT_FACES_JS = """async (families) => {
    await document.fonts.ready;
    const results = {};
    for (const family of families) {
        try {
            const faces = await document.fonts.load(`16px "${family}"`);
            results[family] = [faces.length, faces.filter(f => f.status === 'loaded').length];
        } catch (error) {
            results[family] = [0, 0];
        }
    }
    return results;
}"""


def is_google_stylesheet(url: str) -> bool:
    """True for a Google Fonts css2 stylesheet URL, the only third-party request Studio documents."""
    parts = urlsplit(url)
    return (
        parts.scheme == "https"
        and parts.hostname == GOOGLE_CSS_HOST
        and parts.path == GOOGLE_CSS_PATH
        and "family" in parse_qs(parts.query)
    )


def google_families(urls: list[str]) -> list[str]:
    """The family names a list of Google Fonts stylesheet URLs asks for, in order."""
    families = []
    for url in urls:
        for value in parse_qs(urlsplit(url).query).get("family", []):
            name = value.split(":")[0]
            if name not in families:
                families.append(name)
    return families


def isolation_outcome(surface: str, urls: list[str]) -> Outcome:
    """Judge the external requests one surface made on first load: every one is a FAIL.

    Studio is silent until asked (global rule 7): nothing is requested from
    Google Fonts, Adobe or anywhere else until the person presses Load free
    fonts, chooses a library family or enters a kit ID. So the demo and every
    Studio surface must make no request at all outside the two served
    origins. A Google stylesheet is named as such, because it is the likeliest
    regression (a card or the Composer asking for its font on load), and an
    Adobe kit is named as Adobe.
    """
    out = Outcome()
    google = [url for url in urls if is_google_stylesheet(url)]
    for url in urls:
        if url in google:
            continue
        if "typekit.net" in url:
            out.failures.append(
                f"{surface} requested Adobe Fonts ({url}) before any kit ID was entered"
            )
        else:
            out.failures.append(f"{surface} requested {url}, outside the served loopback origins")
    if google:
        families = ", ".join(google_families(google))
        out.failures.append(
            f"{surface} requested {len(google)} Google Fonts stylesheet(s) on first load "
            f"({families}) before the user asked for free fonts"
        )
    return out


def _settle(page) -> None:
    """Let first-load requests happen, bounded, then prove nothing more arrives.

    `networkidle` returns as soon as the page is quiet, and every external
    request is aborted at once, so this is fast. The short fixed wait is the
    allowed kind: it proves a negative (no late request) rather than waiting
    for a positive.
    """
    page.wait_for_load_state("networkidle", timeout=CONNECT_WAIT_MS)
    page.wait_for_timeout(NOTHING_MORE_MS)


def check_network_isolation(ctx: GateContext) -> Outcome:
    """Studio (Library, Composer, connected) and the demo load nothing external.

    Each surface is loaded fresh and judged on the requests it alone caused,
    by slicing the shared log, so a finding names the surface that leaked.
    """
    out = Outcome()
    page = ctx.page
    log = ctx.network.external

    start = len(log)
    page.goto(ctx.studio_url, wait_until="load")
    _settle(page)
    out.merge(isolation_outcome("Studio Library", log[start:]))

    # A fresh load, so the Composer's own requests are not hidden behind the
    # Library's (a stylesheet already requested is not requested twice).
    start = len(log)
    page.goto(ctx.studio_url, wait_until="load")
    page.locator("#modeComposer").click()
    _settle(page)
    out.merge(isolation_outcome("Studio Composer", log[start:]))

    start = len(log)
    connect_studio(ctx)
    _settle(page)
    out.merge(isolation_outcome("Studio connected to the demo", log[start:]))

    start = len(log)
    page.goto(ctx.demo_url, wait_until="load")
    _settle(page)
    out.merge(isolation_outcome("demo (standalone)", log[start:]))
    return out


#: Extra attempts for families that did not resolve a face, and the pause before
#: each. A stylesheet request can fail once on a lossy link or a busy runner
#: (Studio's own status line reports "N could not load" for the same reason),
#: while a family that was really renamed or removed fails every time. Two
#: retries tell the two apart without hiding the second kind.
FONT_RETRY_ATTEMPTS = 2
FONT_RETRY_BACKOFF_MS = (1000, 3000)


def free_font_failures(results: dict[str, list[int]]) -> list[str]:
    """Judge per-family face counts: every family needs at least one loaded face.

    `results` maps family to [faces found, faces loaded]. When none of the
    families produce a face the network (not the app) is the likely culprit,
    so the message says so, names the usual cause on sandboxes and CI behind a
    proxy, and names the way to skip the check, instead of printing sixteen
    identical lines.
    """
    missing = [family for family, (found, loaded) in results.items() if not (found and loaded)]
    if not results:
        return ["the library lists no families to check"]
    if len(missing) == len(results):
        return [
            f"none of the {len(results)} library families produced a face; Google Fonts is "
            f"probably unreachable from this machine, often because a TLS-intercepting proxy or "
            f"sandbox presents a certificate the browser does not trust "
            f"(rerun with --offline to skip this check)"
        ]
    return [f"family {family} resolved no loaded face from Google Fonts" for family in missing]


def settle_free_fonts(measure, retry, pause, attempts=FONT_RETRY_ATTEMPTS, backoff_ms=FONT_RETRY_BACKOFF_MS):
    """Measure every family, then retry only the missing ones, bounded.

    `measure(None)` returns {family: [found, loaded]} for all families and
    `measure(missing)` re-reads just those; `retry(missing)` asks Studio to
    request them again; `pause(ms)` waits. At most `attempts` retries run,
    each after its backoff, and the caller judges what is still missing. The
    three callables are parameters so the policy is unit-tested without a
    browser.
    """
    results = dict(measure(None))
    for attempt in range(attempts):
        missing = [family for family, (found, loaded) in results.items() if not (found and loaded)]
        if not missing:
            break
        pause(backoff_ms[min(attempt, len(backoff_ms) - 1)])
        retry(missing)
        results.update(measure(missing))
    return results


def check_free_fonts_load(ctx: GateContext) -> Outcome:
    """After the user presses Load free fonts, every library family resolves a real face.

    Asking `document.fonts.load` for each family is the proof: a stylesheet
    request that succeeded but declared no usable face would pass a
    "was requested" check and still render in the fallback. Families that
    miss are retried (see FONT_RETRY_ATTEMPTS) by pressing the button again,
    which Studio answers by re-creating any stylesheet link that errored.
    """
    out = Outcome()
    page = ctx.page
    page.goto(ctx.studio_url, wait_until="load")
    page.locator("#loadFreeFontsLibrary").click()
    wait_until(page, FONT_STATUS_SETTLED, None, FONTS_NETWORK_WAIT_MS)
    families = page.evaluate("[...document.querySelectorAll('#grid .card')].map(c => c._font.css)")

    def measure(only):
        return page.evaluate(FONT_FACES_JS, only or families)

    def retry(_missing):
        page.locator("#loadFreeFontsLibrary").click()
        wait_until(page, FONT_STATUS_SETTLED, None, FONTS_NETWORK_WAIT_MS)

    results = settle_free_fonts(measure, retry, page.wait_for_timeout)
    out.failures.extend(free_font_failures(results))
    return out
