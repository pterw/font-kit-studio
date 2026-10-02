"""Frontend gate: report lines, the tally and the exit-code rule (no browser).

These pin the part of the gate that decides whether CI goes red: which lines
change the exit code and which never do. They run in the normal suite and
launch nothing.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.dev._frontend_gate_report import (  # noqa: E402
    FAIL, REPORT, SKIP, FAILED, PASSED, SKIPPED,
    Finding, Tally, artifact_name, describe_exception, exit_code,
    findings_from_outcome, format_finding, run_status, summary_line,
)
from scripts.dev._frontend_gate_shared import Outcome  # noqa: E402


def finding(kind, check='overflow', profile='mobile', engine='firefox', detail='x'):
    return Finding(kind, check, profile, engine, detail)


def tally_of(planned, *runs):
    """A tally where each element of `runs` is the findings list of one finished run."""
    tally = Tally(planned=planned)
    for findings in runs:
        tally.record(findings)
    return tally


class FormatTests(unittest.TestCase):
    def test_a_failure_line_names_check_profile_and_engine(self):
        line = format_finding(finding(FAIL, 'no horizontal overflow', 'wide touch', 'chromium', 'Library is 1300px wide'))
        self.assertEqual(
            line, '[frontend_gate] FAIL no horizontal overflow [wide touch, chromium]: Library is 1300px wide')

    def test_report_and_skip_lines_use_the_same_shape(self):
        self.assertEqual(format_finding(finding(REPORT, 'touch targets', 'mobile', 'firefox', 'a is 30x30')),
                         '[frontend_gate] REPORT touch targets [mobile, firefox]: a is 30x30')
        self.assertEqual(format_finding(finding(SKIP, 'free fonts load', 'desktop', 'chromium', 'skipped by --offline')),
                         '[frontend_gate] SKIP free fonts load [desktop, chromium]: skipped by --offline')


class EnforcementTests(unittest.TestCase):
    def test_an_enforced_check_turns_failures_into_fail_lines(self):
        out = Outcome(failures=['a', 'b'])
        kinds = [f.kind for f in findings_from_outcome(out, 'live edit', 'mobile', 'chromium', enforced=True)]
        self.assertEqual(kinds, [FAIL, FAIL])

    def test_a_report_only_check_downgrades_its_failures_to_report(self):
        out = Outcome(failures=['a 30x30'])
        found = findings_from_outcome(out, 'touch targets', 'mobile', 'chromium', enforced=False)
        self.assertEqual([f.kind for f in found], [REPORT])
        self.assertEqual(found[0].detail, 'a 30x30')

    def test_a_checks_own_reports_and_skips_are_never_upgraded(self):
        out = Outcome(reports=['legacy'], skips=['why'])
        for enforced in (True, False):
            kinds = [f.kind for f in findings_from_outcome(out, 'c', 'p', 'e', enforced)]
            self.assertEqual(kinds, [REPORT, SKIP])

    def test_a_mixed_outcome_keeps_enforced_failures_and_reports_apart(self):
        out = Outcome(failures=['v0.2 fails'], reports=['legacy fails'])
        kinds = [f.kind for f in findings_from_outcome(out, 'theme contrast', 'desktop', 'chromium', True)]
        self.assertEqual(kinds, [FAIL, REPORT])


class StatusTests(unittest.TestCase):
    def test_failed_beats_skipped_beats_passed(self):
        self.assertEqual(run_status([]), PASSED)
        self.assertEqual(run_status([finding(REPORT)]), PASSED, 'a REPORT does not stop a run passing')
        self.assertEqual(run_status([finding(SKIP)]), SKIPPED)
        self.assertEqual(run_status([finding(SKIP), finding(REPORT)]), SKIPPED)
        self.assertEqual(run_status([finding(SKIP), finding(FAIL)]), FAILED)


class ExitCodeTests(unittest.TestCase):
    def test_clean_runs_exit_zero(self):
        self.assertEqual(exit_code(tally_of(2, [], [])), 0)

    def test_a_fail_line_exits_one(self):
        self.assertEqual(exit_code(tally_of(2, [], [finding(FAIL)])), 1)

    def test_report_lines_never_change_the_exit_code(self):
        reports = [finding(REPORT, detail=str(i)) for i in range(500)]
        self.assertEqual(exit_code(tally_of(2, reports, [])), 0)

    def test_skip_lines_never_change_the_exit_code(self):
        self.assertEqual(exit_code(tally_of(2, [finding(SKIP)], [])), 0)

    def test_fewer_runs_than_planned_exits_one_so_a_silent_skip_is_loud(self):
        self.assertEqual(exit_code(tally_of(3, [], [])), 1)

    def test_a_tally_with_no_runs_and_no_plan_is_clean(self):
        self.assertEqual(exit_code(Tally(planned=0)), 0)


class SummaryTests(unittest.TestCase):
    def test_the_summary_counts_runs_report_and_skip_lines_and_the_plan(self):
        tally = tally_of(
            5,
            [],
            [finding(REPORT), finding(REPORT)],
            [finding(FAIL), finding(FAIL)],
            [finding(SKIP)],
            [],
        )
        self.assertEqual(
            summary_line(tally),
            '[frontend_gate] SUMMARY FAIL: 5 of 5 planned runs finished: 3 passed, 1 failed, 1 skipped; '
            '2 REPORT lines, 1 SKIP lines, 2 FAIL lines')

    def test_a_clean_summary_says_ok_and_shows_a_shortfall_as_fail(self):
        self.assertIn('SUMMARY OK: 2 of 2 planned runs finished: 2 passed', summary_line(tally_of(2, [], [])))
        self.assertIn('SUMMARY FAIL: 1 of 2 planned runs finished', summary_line(tally_of(2, [])))


class ExceptionTests(unittest.TestCase):
    def test_a_raised_check_reads_as_one_line_with_its_type(self):
        error = KeyError('landing.hero.title')
        self.assertEqual(describe_exception(error), "raised KeyError: 'landing.hero.title'")

    def test_a_playwright_style_call_log_is_cut_to_its_first_line(self):
        error = RuntimeError('Timeout 5000ms exceeded.\nCall log:\n  - waiting for locator')
        self.assertEqual(describe_exception(error), 'raised RuntimeError: Timeout 5000ms exceeded.')

    def test_a_very_long_message_is_capped(self):
        text = describe_exception(ValueError('x' * 5000))
        self.assertLess(len(text), 400)
        self.assertTrue(text.endswith('...'))

    def test_an_empty_message_still_names_the_type(self):
        self.assertEqual(describe_exception(ValueError()), 'raised ValueError')

    def test_screenshot_names_are_filesystem_safe(self):
        self.assertEqual(artifact_name('live edit', 'wide touch', 'firefox'), 'live-edit-wide-touch-firefox.png')


if __name__ == '__main__':
    unittest.main()
