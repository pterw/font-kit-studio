"""Findings, report lines, the run tally and the exit-code rule.

Pure functions only, so the plain `unittest` suite can pin the output format
and the one rule that matters most: what changes the exit code. A gate whose
`REPORT` lines could flip CI red would be switched off within a week; a gate
whose `FAIL` lines could not would be decoration.

Line shapes (the controller and the CI log reader both grep for them):

    [frontend_gate] FAIL <check> [<profile>, <engine>]: <detail>
    [frontend_gate] REPORT <check> [<profile>, <engine>]: <detail>
    [frontend_gate] SKIP <check> [<profile>, <engine>]: <reason>
    [frontend_gate] ADVISORY <check> [<profile>, <engine>]: <detail>

ADVISORY is a FAIL on a run the enforcement policy does not block on
(desktop-first: only Chromium at the desktop profile blocks by default). It is
printed and counted, and never changes the exit code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.dev._frontend_gate_shared import KNOWN_ENGINES, VIEWPORTS, Outcome

PREFIX = "[frontend_gate]"

FAIL = "FAIL"
REPORT = "REPORT"
SKIP = "SKIP"
ADVISORY = "ADVISORY"

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


class PolicyError(ValueError):
    """The --enforce value names an engine or profile the gate does not have."""


@dataclass(frozen=True)
class EnforcementPolicy:
    """Which (engine, profile) runs can fail the gate; every other run is advisory.

    Font Kit Studio is a desktop-first tool, so the default blocks only
    Chromium at the desktop profile. Firefox and the phone and wide-touch
    profiles still run and still print what they find, but a problem there is
    something to read, not something that stops a release. `all` is the
    strict mode for a local run.
    """

    DEFAULT = "chromium:desktop"

    everything: bool = False
    pairs: frozenset = frozenset()
    #: `--enforce none`: every run is advisory, on purpose. Distinct from an
    #: empty selection by accident, which the gate refuses.
    advisory_only: bool = False

    @classmethod
    def parse(cls, text: str) -> EnforcementPolicy:
        """Parse `all`, `none` or a comma list of `engine:profile`.

        An unknown name is an error: a typo that silently made every run
        advisory would print a green summary for a gate that blocks nothing.
        The profile may contain a space ("wide touch"), so only the first
        colon splits.
        """
        if text.strip().lower() == "all":
            return cls(everything=True)
        if text.strip().lower() == "none":
            return cls(advisory_only=True)
        pairs = set()
        for part in text.split(","):
            if not part.strip():
                continue
            engine, _, profile = part.partition(":")
            engine, profile = engine.strip().lower(), profile.strip().lower()
            if engine not in KNOWN_ENGINES or profile not in VIEWPORTS:
                raise PolicyError(
                    f"bad --enforce entry {part.strip()!r}; use 'all', 'none' or engine:profile with "
                    f"engine in {', '.join(KNOWN_ENGINES)} and profile in {', '.join(VIEWPORTS)}"
                )
            pairs.add((engine, profile))
        if not pairs:
            raise PolicyError("--enforce is empty; use 'all', 'none' or e.g. chromium:desktop")
        return cls(pairs=frozenset(pairs))

    def blocking(self, engine: str, profile: str) -> bool:
        """True when a FAIL on this run must fail the gate."""
        return self.everything or (engine, profile) in self.pairs


def apply_policy(findings: list[Finding], blocking: bool) -> list[Finding]:
    """On an advisory run, relabel FAIL as ADVISORY; leave every other kind alone.

    One place decides it, so a raised check, an unopenable profile and an
    ordinary failed assertion are all treated the same way. REPORT and SKIP
    already never change the exit code.
    """
    if blocking:
        return findings
    return [
        Finding(ADVISORY, f.check, f.profile, f.engine, f.detail) if f.kind == FAIL else f
        for f in findings
    ]


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
    must not be counted as a pass. A REPORT or an ADVISORY does not change
    the status: the run measured everything and the finding cannot block.
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
    blocking_runs: list[bool] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    #: Planned runs that could not happen because their engine is unavailable
    #: and has no blocking runs. Counted so the planned-run accounting stays honest.
    not_run: int = 0
    engine_notes: int = 0

    def record_not_run(self, count: int, reason: str) -> None:
        """Declare `count` planned runs not run (one advisory note per engine)."""
        self.not_run += count
        self.engine_notes += 1

    def record(self, findings: list[Finding], blocking: bool = True) -> None:
        """Add one completed run, whether it was a blocking one, and its findings."""
        self.statuses.append(run_status(findings))
        self.blocking_runs.append(blocking)
        self.findings.extend(findings)

    def _count(self, status: str, blocking: bool) -> int:
        return sum(1 for s, b in zip(self.statuses, self.blocking_runs) if s == status and b == blocking)

    @property
    def blocking_total(self) -> int:
        """Runs the policy blocks on."""
        return self.blocking_runs.count(True)

    @property
    def advisory_total(self) -> int:
        """Runs that run and report but cannot fail the gate."""
        return self.blocking_runs.count(False)

    @property
    def passed(self) -> int:
        """Blocking runs that finished with no FAIL and no SKIP."""
        return self._count(PASSED, True)

    @property
    def failed(self) -> int:
        """Blocking runs with at least one FAIL."""
        return self._count(FAILED, True)

    @property
    def skipped(self) -> int:
        """Blocking runs that skipped part of their work."""
        return self._count(SKIPPED, True)

    def lines(self, kind: str) -> int:
        """How many findings of one kind were printed."""
        noted = self.engine_notes if kind == ADVISORY else 0
        return sum(1 for finding in self.findings if finding.kind == kind) + noted


def exit_code(tally: Tally) -> int:
    """0 when clean, 1 on any FAIL or when fewer runs finished than were planned.

    REPORT, SKIP and ADVISORY lines never change the result: they are
    visibility, not verdicts. (An advisory run's failures are relabelled
    before they are recorded, so only blocking runs can contribute a FAIL.)
    The planned-run comparison is the "silent skip" guard: a check
    that stopped running shows up as a shortfall rather than a smaller green
    number nobody notices. A prerequisite error (no Playwright, no browser)
    never reaches here; `main` returns 1 for it before any run exists.
    """
    if tally.failed or tally.lines(FAIL):
        return 1
    if len(tally.statuses) + tally.not_run != tally.planned:
        return 1
    return 0


def summary_line(tally: Tally) -> str:
    """The closing line: planned vs finished, blocking outcomes, advisory counts.

    Printing the planned count is what makes a silently dropped check
    visible. "30 of 30 planned" and "24 of 30 planned" read differently.
    Blocking and advisory are separate so a reader sees at once what could
    have failed the gate and what is only worth reading.
    """
    verdict = "FAIL" if exit_code(tally) else "OK"
    not_run = f", {tally.not_run} not run (engine unavailable)" if tally.not_run else ""
    return (
        f"{PREFIX} SUMMARY {verdict}: {len(tally.statuses)} of {tally.planned} "
        f"planned runs finished{not_run}. Blocking: {tally.blocking_total} runs, {tally.passed} passed, "
        f"{tally.failed} failed, {tally.skipped} skipped. Advisory: {tally.advisory_total} runs, "
        f"{tally.lines(ADVISORY)} ADVISORY lines. {tally.lines(REPORT)} REPORT lines, "
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
