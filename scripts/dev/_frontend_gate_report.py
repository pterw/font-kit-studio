"""Findings, report lines, the run tally and the exit-code rule.

Pure functions only, so the plain `unittest` suite can pin the output format
and the one rule that matters most: what changes the exit code. A gate whose
`REPORT` lines could flip CI red would be switched off within a week; a gate
whose `FAIL` lines could not would be decoration.

Line shapes (the controller and the CI log reader both grep for them):

    [frontend_gate] FAIL <check> [<profile>, <engine>]: <detail>
    [frontend_gate] REPORT <check> [<profile>, <engine>]: <detail>
    [frontend_gate] SKIP <check> [<profile>, <engine>]: <reason>
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.dev._frontend_gate_shared import Outcome

PREFIX = "[frontend_gate]"

FAIL = "FAIL"
REPORT = "REPORT"
SKIP = "SKIP"

PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"


@dataclass(frozen=True)
class Finding:
    """One line of output: what kind, from which check run, and the detail."""

    kind: str
    check: str
    profile: str
    engine: str
    detail: str


def format_finding(finding: Finding) -> str:
    """Render a finding as one greppable line that names its check, profile and engine.

    "The submit button is 38px" is not actionable until you know which device
    and browser produced it, so the three always travel with the detail.
    """
    return (
        f"{PREFIX} {finding.kind} {finding.check} "
        f"[{finding.profile}, {finding.engine}]: {finding.detail}"
    )


def findings_from_outcome(
    outcome: Outcome, check: str, profile: str, engine: str, enforced: bool
) -> list[Finding]:
    """Turn a check's raw outcome into findings, applying the enforcement rule.

    An enforced check's `failures` are FAIL. A report-only check (touch
    targets) declares that even its failures are advisory, so they become
    REPORT here, in one place, rather than every check re-implementing the
    downgrade. A check's own `reports` and `skips` are never upgraded.
    """
    failure_kind = FAIL if enforced else REPORT
    findings = [
        Finding(failure_kind, check, profile, engine, detail)
        for detail in outcome.failures
    ]
    findings.extend(
        Finding(REPORT, check, profile, engine, detail) for detail in outcome.reports
    )
    findings.extend(
        Finding(SKIP, check, profile, engine, detail) for detail in outcome.skips
    )
    return findings


def run_status(findings: list[Finding]) -> str:
    """Classify one check run: failed beats skipped beats passed.

    A run with a SKIP did not complete what it set out to measure, so it
    must not be counted as a pass. A REPORT does not change the status: the
    run measured everything and the finding is advisory.
    """
    kinds = {finding.kind for finding in findings}
    if FAIL in kinds:
        return FAILED
    if SKIP in kinds:
        return SKIPPED
    return PASSED


@dataclass
class Tally:
    """The running totals the final summary prints."""

    planned: int = 0
    statuses: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def record(self, findings: list[Finding]) -> None:
        """Add one completed run and its findings."""
        self.statuses.append(run_status(findings))
        self.findings.extend(findings)

    @property
    def passed(self) -> int:
        """Runs that finished with no FAIL and no SKIP."""
        return self.statuses.count(PASSED)

    @property
    def failed(self) -> int:
        """Runs with at least one FAIL."""
        return self.statuses.count(FAILED)

    @property
    def skipped(self) -> int:
        """Runs that skipped part of their work."""
        return self.statuses.count(SKIPPED)

    def lines(self, kind: str) -> int:
        """How many findings of one kind were printed."""
        return sum(1 for finding in self.findings if finding.kind == kind)


def exit_code(tally: Tally) -> int:
    """0 when clean, 1 on any FAIL or when fewer runs finished than were planned.

    REPORT and SKIP lines never change the result: they are visibility, not
    verdicts. The planned-run comparison is the "silent skip" guard: a check
    that stopped running shows up as a shortfall rather than a smaller green
    number nobody notices. A prerequisite error (no Playwright, no browser)
    never reaches here; `main` returns 1 for it before any run exists.
    """
    if tally.failed or tally.lines(FAIL):
        return 1
    if len(tally.statuses) != tally.planned:
        return 1
    return 0


def summary_line(tally: Tally) -> str:
    """The closing line: runs passed, failed and skipped, report and skip lines.

    Printing the planned count is what makes a silently dropped check
    visible. "30 of 30 planned" and "24 of 30 planned" read differently.
    """
    verdict = "FAIL" if exit_code(tally) else "OK"
    return (
        f"{PREFIX} SUMMARY {verdict}: {len(tally.statuses)} of {tally.planned} "
        f"planned runs finished: {tally.passed} passed, {tally.failed} failed, "
        f"{tally.skipped} skipped; {tally.lines(REPORT)} REPORT lines, "
        f"{tally.lines(SKIP)} SKIP lines, {tally.lines(FAIL)} FAIL lines"
    )


#: A Playwright error carries a multi-line call log. Keep the first line,
#: which names the cause, and cap the length so one raised check cannot
#: bury every other line in the output.
EXCEPTION_DETAIL_LIMIT = 300


def describe_exception(error: BaseException) -> str:
    """One line for a check that raised: its type and the start of its message.

    A check that raises is reported as a failure and the run continues. A bare
    call would let one TypeError skip every later check and surface as a
    traceback, which reads as "the gate crashed" rather than "the gate found
    a problem".
    """
    first = (str(error).strip().splitlines() or [""])[0]
    if len(first) > EXCEPTION_DETAIL_LIMIT:
        first = first[:EXCEPTION_DETAIL_LIMIT] + "..."
    return f"raised {type(error).__name__}: {first}" if first else f"raised {type(error).__name__}"


def artifact_name(check: str, profile: str, engine: str) -> str:
    """A filesystem-safe screenshot name for one run, e.g. ``live-edit-wide-touch-firefox.png``."""
    raw = f"{check}-{profile}-{engine}".lower()
    return "".join(char if char.isalnum() else "-" for char in raw).strip("-") + ".png"
