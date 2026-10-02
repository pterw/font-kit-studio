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
    ADVISORY, FAIL, REPORT, SKIP, FAILED, PASSED, SKIPPED,
    EnforcementPolicy, Finding, PolicyError, Tally, apply_policy, artifact_name, describe_exception,
    exit_code, findings_from_outcome, format_finding, run_status, summary_line,
)
from scripts.dev._frontend_gate_shared import Outcome  # noqa: E402


def finding(kind, check='overflow', profile='mobile', engine='firefox', detail='x'):
    return Finding(kind, check, profile, engine, detail)


def tally_of(planned, *runs):
    """A tally where each element of `runs` is the findings list of one finished (blocking) run."""
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
    def test_the_summary_counts_blocking_runs_advisory_findings_report_and_skip_lines_and_the_plan(self):
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
            '[frontend_gate] SUMMARY FAIL: 5 of 5 planned runs finished. Blocking: 5 runs, 3 passed, '
            '1 failed, 1 skipped. Advisory: 0 runs, 0 ADVISORY lines. '
            '2 REPORT lines, 1 SKIP lines, 2 FAIL lines')

    def test_advisory_runs_are_counted_apart_from_blocking_ones(self):
        tally = Tally(planned=4)
        tally.record([], blocking=True)
        tally.record([finding(FAIL)], blocking=True)
        tally.record([finding(ADVISORY), finding(ADVISORY)], blocking=False)
        tally.record([], blocking=False)
        self.assertEqual(
            summary_line(tally),
            '[frontend_gate] SUMMARY FAIL: 4 of 4 planned runs finished. Blocking: 2 runs, 1 passed, '
            '1 failed, 0 skipped. Advisory: 2 runs, 2 ADVISORY lines. '
            '0 REPORT lines, 0 SKIP lines, 1 FAIL lines')

    def test_a_clean_summary_says_ok_and_shows_a_shortfall_as_fail(self):
        self.assertIn('SUMMARY OK: 2 of 2 planned runs finished. Blocking: 2 runs, 2 passed',
                      summary_line(tally_of(2, [], [])))
        self.assertIn('SUMMARY FAIL: 1 of 2 planned runs finished', summary_line(tally_of(2, [])))


class PolicyTests(unittest.TestCase):
    def test_the_default_blocks_only_chromium_at_the_desktop_profile(self):
        policy = EnforcementPolicy.parse('chromium:desktop')
        self.assertTrue(policy.blocking('chromium', 'desktop'))
        for engine, profile in (('chromium', 'mobile'), ('chromium', 'wide touch'),
                                ('firefox', 'desktop'), ('firefox', 'mobile')):
            with self.subTest(engine=engine, profile=profile):
                self.assertFalse(policy.blocking(engine, profile))

    def test_all_makes_every_run_blocking(self):
        policy = EnforcementPolicy.parse('all')
        self.assertTrue(all(policy.blocking(e, p) for e in ('chromium', 'firefox')
                            for p in ('desktop', 'mobile', 'wide touch')))

    def test_a_comma_list_and_a_profile_with_a_space_parse(self):
        policy = EnforcementPolicy.parse(' chromium:desktop , firefox:wide touch ')
        self.assertTrue(policy.blocking('firefox', 'wide touch'))
        self.assertTrue(policy.blocking('chromium', 'desktop'))
        self.assertFalse(policy.blocking('firefox', 'desktop'))

    def test_a_bad_policy_is_an_error_not_a_silent_everything_advisory(self):
        for text in ('', 'chromium', 'safari:desktop', 'chromium:tablet', ',,', 'chromium:'):
            with self.subTest(text=text), self.assertRaises(PolicyError):
                EnforcementPolicy.parse(text)

    def test_the_default_policy_text_is_the_desktop_first_one(self):
        self.assertEqual(EnforcementPolicy.DEFAULT, 'chromium:desktop')


class NoneAndNotRunTests(unittest.TestCase):
    def test_none_is_an_explicit_advisory_only_policy_that_blocks_nothing(self):
        policy = EnforcementPolicy.parse('none')
        self.assertTrue(policy.advisory_only)
        self.assertFalse(any(policy.blocking(e, p) for e in ('chromium', 'firefox')
                             for p in ('desktop', 'mobile', 'wide touch')))
        self.assertFalse(EnforcementPolicy.parse('chromium:desktop').advisory_only)
        self.assertFalse(EnforcementPolicy.parse('all').advisory_only)

    def test_runs_that_could_not_happen_are_counted_as_not_run_and_keep_the_accounting_honest(self):
        tally = Tally(planned=5)
        tally.record([], blocking=True)
        tally.record([finding(ADVISORY)], blocking=False)
        tally.record_not_run(3, 'could not launch: firefox is missing')
        self.assertEqual(tally.not_run, 3)
        self.assertEqual(exit_code(tally), 0, 'finished + not run equals planned')
        self.assertEqual(tally.lines(ADVISORY), 2, 'the engine note counts as an advisory line')
        short = Tally(planned=5)
        short.record([], blocking=True)
        short.record_not_run(3, 'x')
        self.assertEqual(exit_code(short), 1, 'a run that neither finished nor was declared not run is a shortfall')

    def test_the_summary_names_the_runs_that_did_not_run(self):
        tally = Tally(planned=4)
        tally.record([], blocking=True)
        tally.record([], blocking=True)
        tally.record_not_run(2, 'could not launch')
        self.assertEqual(
            summary_line(tally),
            '[frontend_gate] SUMMARY OK: 2 of 4 planned runs finished, 2 not run (engine unavailable). '
            'Blocking: 2 runs, 2 passed, 0 failed, 0 skipped. Advisory: 0 runs, 1 ADVISORY lines. '
            '0 REPORT lines, 0 SKIP lines, 0 FAIL lines')


class AdvisoryTests(unittest.TestCase):
    def test_a_blocking_run_keeps_its_fail_lines(self):
        found = [finding(FAIL), finding(REPORT), finding(SKIP)]
        self.assertEqual([f.kind for f in apply_policy(found, blocking=True)], [FAIL, REPORT, SKIP])

    def test_an_advisory_run_turns_fail_into_advisory_and_leaves_other_kinds_alone(self):
        found = [finding(FAIL, detail='bad'), finding(REPORT), finding(SKIP)]
        out = apply_policy(found, blocking=False)
        self.assertEqual([f.kind for f in out], [ADVISORY, REPORT, SKIP])
        self.assertEqual(out[0].detail, 'bad')

    def test_the_advisory_line_has_the_same_shape_as_a_fail_line(self):
        out = apply_policy([finding(FAIL, 'live edit', 'mobile', 'firefox', 'Reset left 40px')], blocking=False)
        self.assertEqual(format_finding(out[0]),
                         '[frontend_gate] ADVISORY live edit [mobile, firefox]: Reset left 40px')

    def test_an_advisory_run_is_never_failed_and_a_blocking_fail_still_is(self):
        advisory = Tally(planned=2)
        advisory.record(apply_policy([finding(FAIL)], blocking=False), blocking=False)
        advisory.record([], blocking=True)
        self.assertEqual(exit_code(advisory), 0)
        self.assertEqual((advisory.failed, advisory.lines(FAIL), advisory.lines(ADVISORY)), (0, 0, 1))
        strict = Tally(planned=2)
        strict.record(apply_policy([finding(FAIL)], blocking=True), blocking=True)
        strict.record([], blocking=False)
        self.assertEqual(exit_code(strict), 1)

    def test_a_shortfall_in_advisory_runs_still_fails_because_a_check_stopped_running(self):
        tally = Tally(planned=3)
        tally.record([], blocking=True)
        tally.record([finding(ADVISORY)], blocking=False)
        self.assertEqual(exit_code(tally), 1)

    def test_run_status_ignores_advisory_for_passing(self):
        self.assertEqual(run_status([finding(ADVISORY)]), PASSED)


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
