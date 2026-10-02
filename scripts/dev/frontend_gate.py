"""Repository-owned frontend gate for Font Kit Studio.

`unittest` proves behaviour and `verify.py` proves text. Neither can see what a
real browser computes across devices, so the things that decide whether the
product looks and works right on a phone, in dark mode, offline or in a
README have nothing enforcing them: horizontal overflow, elements that
should start hidden, the live edit flow on touch, text contrast, third-party
requests, and the logos.

This script closes that gap. It starts the real `scripts/serve.py` on two
loopback ports it owns, drives real browsers (Chromium and Firefox) through
every viewport profile each check declares, and prints one line per finding:

    [frontend_gate] FAIL <check> [<profile>, <engine>]: <detail>
    [frontend_gate] REPORT <check> [<profile>, <engine>]: <detail>
    [frontend_gate] SKIP <check> [<profile>, <engine>]: <reason>

FAIL lines change the exit code. REPORT lines are advisory and never do.
SKIP lines say a check could not run and why. The closing SUMMARY line counts
the runs that passed and failed against the number planned, so a check that
silently stops running shows up as a smaller number.

    python scripts/dev/frontend_gate.py                      # chromium + firefox
    python scripts/dev/frontend_gate.py --engines chromium   # one engine
    python scripts/dev/frontend_gate.py --offline            # skip the font download check
    python scripts/dev/frontend_gate.py --headed             # watch it run

Exit codes: 0 clean; 1 on any FAIL, any prerequisite error (no Playwright, no
browser), or fewer runs than planned. The gate never downloads a browser; when
one is missing it prints the exact install command.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

# Run as a script, the repository root is not on sys.path, so `scripts.dev.*`
# is unimportable. A direct CLI run needs this; `python -m` and the unit tests
# already have it.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.dev._frontend_gate_assets import check_logo_paint  # noqa: E402
from scripts.dev._frontend_gate_layout import (  # noqa: E402
    check_initial_visibility,
    check_no_horizontal_overflow,
    check_touch_targets,
)
from scripts.dev._frontend_gate_live import check_live_edit  # noqa: E402
from scripts.dev._frontend_gate_network import (  # noqa: E402
    check_free_fonts_load,
    check_network_isolation,
)
from scripts.dev._frontend_gate_report import (  # noqa: E402
    FAIL,
    PASSED,
    PREFIX,
    SKIP,
    Finding,
    Tally,
    artifact_name,
    describe_exception,
    exit_code,
    findings_from_outcome,
    format_finding,
    run_status,
    summary_line,
)
from scripts.dev._frontend_gate_runtime import (  # noqa: E402
    GOOGLE_FONTS_HOSTS,
    GateError,
    ServedApp,
    launch_browser,
    load_playwright,
    new_run_context,
    parse_engines,
    serve_app,
)
from scripts.dev._frontend_gate_shared import (  # noqa: E402
    DESKTOP,
    MOBILE,
    TOUCH_WIDE,
    GateContext,
    Outcome,
)
from scripts.dev._frontend_gate_theme import check_theme_contrast  # noqa: E402

#: Where failing runs leave a screenshot. `work/` is git-ignored scratch, and
#: the CI workflow uploads this folder when the gate fails.
DEFAULT_ARTIFACTS_DIR = REPO_ROOT / "work" / "frontend-gate"


@dataclass(frozen=True)
class Check:
    """One check: its name, function, the profiles it runs at and how it is enforced.

    `enforced=False` means every failure the check finds is printed as REPORT
    (a scoping choice, not a weakness: touch targets are visibility for now).
    `needs_network` marks the one check that turns the network on; it is
    skipped, with a counted SKIP line, under --offline.
    """

    name: str
    run: Callable[[GateContext], Outcome]
    profiles: tuple[str, ...]
    enforced: bool = True
    needs_network: bool = False


#: Every check the gate runs, with the viewport profiles each one runs at.
#:
#: Width changes nothing for requests, fonts or logo paint, so those use the
#: smallest useful set. Layout, visibility and theme run where the layout
#: changes. The live edit and overflow run on all three profiles, because
#: selecting by finger rather than mouse is part of what they prove. Touch
#: targets run only where a finger is the pointer.
CHECKS = (
    Check("network isolation", check_network_isolation, (DESKTOP,)),
    Check("free fonts load", check_free_fonts_load, (DESKTOP,), needs_network=True),
    Check("no horizontal overflow", check_no_horizontal_overflow, (DESKTOP, MOBILE, TOUCH_WIDE)),
    Check("initial visibility", check_initial_visibility, (DESKTOP, MOBILE)),
    Check("live edit", check_live_edit, (DESKTOP, MOBILE, TOUCH_WIDE)),
    Check("logo paint", check_logo_paint, (DESKTOP,)),
    Check("theme contrast", check_theme_contrast, (DESKTOP, MOBILE)),
    Check("touch targets", check_touch_targets, (MOBILE, TOUCH_WIDE), enforced=False),
)


def planned_runs(engines: Sequence[str], checks: Sequence[Check] = CHECKS) -> int:
    """How many check runs a clean pass performs: profiles per check, per engine.

    Printed in the summary so a check that silently stops running shows up as
    a smaller number instead of a green line nobody questions.
    """
    return len(engines) * sum(len(check.profiles) for check in checks)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the developer-facing options."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--headed", action="store_true", help="show the browser windows while the checks run"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip the one check that needs the network (free fonts load); it prints SKIP",
    )
    parser.add_argument(
        "--engines",
        default=None,
        help="comma list of engines (default: $FKS_ENGINES, else chromium,firefox)",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=DEFAULT_ARTIFACTS_DIR,
        help="folder for screenshots of failing runs (default: work/frontend-gate)",
    )
    return parser.parse_args(argv)


def resolve_engines(requested: str | None, environ=None) -> tuple[str, ...]:
    """The flag wins, then FKS_ENGINES (shared with the test suite), then both engines."""
    environ = os.environ if environ is None else environ
    return parse_engines(requested if requested else environ.get("FKS_ENGINES"))


def clear_screenshots(directory: Path) -> None:
    """Delete screenshots left by an earlier run, so the folder shows only this run's failures.

    Only `*.png` files in the gate's own scratch folder are touched. A stale
    picture of a defect that has since been fixed is worse than none: it
    sends the reader after a failure that is no longer there.
    """
    if directory.is_dir():
        for stale in directory.glob("*.png"):
            stale.unlink()


def _save_screenshot(page, directory: Path, name: str) -> None:
    """Best-effort screenshot of a failing run; never allowed to mask the failure."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / name))
    except Exception:  # noqa: BLE001 - the finding matters more than its picture
        pass


def run_one(
    check: Check,
    profile: str,
    engine: str,
    browser,
    served: ServedApp,
    offline: bool,
    artifacts: Path,
) -> list[Finding]:
    """Run one check at one profile in a fresh browser context; return its findings.

    A fresh context per run keeps checks independent and matches touch
    emulation to the profile. A check that raises is reported as a FAIL and
    the run continues, so one fault never hides the rest of the gate.
    """
    if check.needs_network and offline:
        detail = "skipped by --offline: this check needs fonts.googleapis.com"
        return [Finding(SKIP, check.name, profile, engine, detail)]
    allowed = GOOGLE_FONTS_HOSTS if check.needs_network else ()
    try:
        context, page, network, errors = new_run_context(browser, profile, served, allowed)
    except Exception as error:  # noqa: BLE001 - same rule as a check fault
        detail = f"the profile could not be opened: {describe_exception(error)}"
        return [Finding(FAIL, check.name, profile, engine, detail)]
    try:
        gate_context = GateContext(
            page=page,
            browser_context=context,
            studio_origin=served.studio_origin,
            target_origin=served.target_origin,
            engine=engine,
            profile=profile,
            offline=offline,
            network=network,
            errors=errors,
        )
        try:
            findings = findings_from_outcome(
                check.run(gate_context), check.name, profile, engine, check.enforced
            )
        except Exception as error:  # noqa: BLE001 - any check fault is a failure
            # A crash is never downgraded: the gate could not see, which is
            # not a finding about the app, and hiding it would hide a rotted check.
            findings = [Finding(FAIL, check.name, profile, engine, describe_exception(error))]
        if any(finding.kind == FAIL for finding in findings):
            _save_screenshot(page, artifacts, artifact_name(check.name, profile, engine))
        return findings
    finally:
        context.close()


def run_checks(
    browsers: dict,
    served: ServedApp,
    offline: bool,
    artifacts: Path,
    emit: Callable[[str], None] = print,
    checks: Sequence[Check] = CHECKS,
) -> Tally:
    """Run every check at every profile it claims, on every engine, printing as it goes.

    Findings print the moment their run finishes, so a long run shows progress
    and a hang shows where it stopped. Every finished run is recorded in the
    tally, which is what the summary and the exit code are computed from.
    """
    tally = Tally(planned=planned_runs(list(browsers), checks))
    for engine, browser in browsers.items():
        for check in checks:
            for profile in check.profiles:
                findings = run_one(check, profile, engine, browser, served, offline, artifacts)
                for finding in findings:
                    emit(format_finding(finding))
                if run_status(findings) == PASSED:
                    emit(f"{PREFIX} PASS {check.name} [{profile}, {engine}]")
                tally.record(findings)
    return tally


def main(argv: Sequence[str] | None = None) -> int:
    """Start the app, run every check on every engine, print findings and the summary."""
    args = parse_args(argv)
    try:
        engines = resolve_engines(args.engines)
        sync_playwright = load_playwright()
        with ExitStack() as stack:
            playwright = stack.enter_context(sync_playwright())
            # Launch every engine before serving or running anything, so a
            # missing browser fails in a second with an install command, not
            # halfway through a run.
            browsers = {}
            for engine in engines:
                browser = launch_browser(playwright, engine, headless=not args.headed)
                stack.callback(browser.close)
                browsers[engine] = browser
            served = stack.enter_context(serve_app())
            clear_screenshots(args.artifacts)
            print(f"{PREFIX} engines: {', '.join(engines)}; planned runs: {planned_runs(engines)}")
            tally = run_checks(browsers, served, args.offline, args.artifacts)
    except GateError as error:
        print(f"{PREFIX} ERROR: {error}", file=sys.stderr)
        return 1
    print(summary_line(tally))
    return exit_code(tally)


if __name__ == "__main__":
    raise SystemExit(main())
