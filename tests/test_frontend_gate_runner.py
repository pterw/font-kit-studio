"""Frontend gate: CLI parsing, the check table, the runner and exit codes (no browser).

Everything the gate does around its checks is covered here with fakes: how
flags and FKS_ENGINES resolve, how requests are routed, what the runner does
with a check that fails, raises, is report-only or needs the network, and
what `main` returns when Playwright or a browser is missing. The real browsers
are the gate's own job; none is launched in this file.
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.dev import frontend_gate as gate  # noqa: E402
from scripts.dev import _frontend_gate_runtime as runtime  # noqa: E402
from scripts.dev._frontend_gate_report import (  # noqa: E402
    ADVISORY, FAIL, REPORT, SKIP, EnforcementPolicy, Finding, Tally,
)
from scripts.dev._frontend_gate_shared import (  # noqa: E402
    DESKTOP, MOBILE, TOUCH_WIDE, VIEWPORTS, NetworkLog, Outcome,
)

SERVED = runtime.ServedApp('http://localhost:1111', 'http://localhost:2222')


class FakePage:
    def __init__(self):
        self.shots = []

    def screenshot(self, path):
        self.shots.append(path)
        Path(path).write_bytes(b'png')


class FakeContext:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class ArgumentTests(unittest.TestCase):
    def test_defaults(self):
        args = gate.parse_args([])
        self.assertFalse(args.headed)
        self.assertFalse(args.offline)
        self.assertIsNone(args.engines)
        self.assertEqual(args.enforce, 'chromium:desktop')

    def test_flags(self):
        args = gate.parse_args(['--headed', '--offline', '--engines', 'chromium'])
        self.assertTrue(args.headed)
        self.assertTrue(args.offline)
        self.assertEqual(args.engines, 'chromium')

    def test_enforce_flag(self):
        self.assertEqual(gate.parse_args(['--enforce', 'all']).enforce, 'all')
        self.assertEqual(gate.parse_args(['--enforce', 'chromium:desktop,firefox:desktop']).enforce,
                         'chromium:desktop,firefox:desktop')

    def test_an_unknown_flag_exits_with_argparse_status_two(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            gate.parse_args(['--nope'])
        self.assertEqual(raised.exception.code, 2)

    def test_the_flag_beats_the_environment_which_beats_the_default(self):
        self.assertEqual(gate.resolve_engines('firefox', {'FKS_ENGINES': 'chromium'}), ('firefox',))
        self.assertEqual(gate.resolve_engines(None, {'FKS_ENGINES': 'chromium'}), ('chromium',))
        self.assertEqual(gate.resolve_engines(None, {}), ('chromium', 'firefox'))
        self.assertEqual(gate.resolve_engines('', {'FKS_ENGINES': ' '}), ('chromium', 'firefox'))

    def test_engine_lists_are_trimmed_lowercased_and_deduplicated(self):
        self.assertEqual(runtime.parse_engines(' Chromium , firefox,chromium '), ('chromium', 'firefox'))

    def test_an_unknown_or_empty_engine_list_is_an_error_not_a_silent_no_op(self):
        for text in ('safari', 'chromium,webkit', ',,'):
            with self.subTest(text=text), self.assertRaises(runtime.GateError):
                runtime.parse_engines(text)

    def test_the_executable_comes_from_the_same_variable_the_tests_use(self):
        self.assertEqual(runtime.executable_for('chromium', {'FKS_CHROMIUM_EXECUTABLE': '/x/chrome'}), '/x/chrome')
        self.assertIsNone(runtime.executable_for('firefox', {'FKS_CHROMIUM_EXECUTABLE': '/x/chrome'}))
        self.assertIsNone(runtime.executable_for('firefox', {'FKS_FIREFOX_EXECUTABLE': ''}))


class RequestRoutingTests(unittest.TestCase):
    def test_the_two_served_origins_are_served_and_everything_else_is_blocked(self):
        origins = SERVED.origins
        self.assertEqual(runtime.classify_request('http://localhost:1111/a.html?x=1', origins, ()), 'serve')
        self.assertEqual(runtime.classify_request('http://localhost:2222/demo/', origins, ()), 'serve')
        for url in ('http://localhost:3333/', 'http://127.0.0.1:1111/', 'https://fonts.googleapis.com/css2?family=Inter',
                    'https://localhost:1111/'):
            with self.subTest(url=url):
                self.assertEqual(runtime.classify_request(url, origins, ()), 'block')

    def test_an_allowed_host_is_let_through_only_when_the_check_opted_in(self):
        url = 'https://fonts.gstatic.com/s/inter/x.woff2'
        self.assertEqual(runtime.classify_request(url, SERVED.origins, runtime.GOOGLE_FONTS_HOSTS), 'allow')
        self.assertEqual(runtime.classify_request(url, SERVED.origins, ()), 'block')

    def test_the_router_aborts_blocked_requests_and_logs_every_external_one(self):
        log = NetworkLog()
        handler = runtime.make_router(SERVED, runtime.GOOGLE_FONTS_HOSTS, log)
        for url, expected in (('http://localhost:1111/a', 'continue_'), ('https://evil.example/x', 'abort'),
                              ('https://fonts.googleapis.com/css2?family=Inter', 'continue_')):
            route = mock.Mock()
            route.request.url = url
            handler(route)
            with self.subTest(url=url):
                getattr(route, expected).assert_called_once()
        self.assertEqual(log.external, ['https://evil.example/x', 'https://fonts.googleapis.com/css2?family=Inter'])

    def test_the_router_takes_exactly_one_parameter_so_playwright_passes_only_the_route(self):
        handler = runtime.make_router(SERVED, (), NetworkLog())
        self.assertEqual(handler.__code__.co_argcount, 1)


class CheckTableTests(unittest.TestCase):
    NAMES = {'network isolation', 'free fonts load', 'no horizontal overflow', 'initial visibility', 'live edit',
             'logo paint', 'theme contrast', 'touch targets'}

    def test_the_eight_addendum_checks_are_all_present(self):
        self.assertEqual({check.name for check in gate.CHECKS}, self.NAMES)
        self.assertEqual(len(gate.CHECKS), len(self.NAMES), 'no duplicate names')

    def test_only_touch_targets_are_report_only_and_only_free_fonts_need_the_network(self):
        self.assertEqual({c.name for c in gate.CHECKS if not c.enforced}, {'touch targets'})
        self.assertEqual({c.name for c in gate.CHECKS if c.needs_network}, {'free fonts load'})

    def test_profiles_are_known_and_the_live_edit_covers_both_touch_profiles(self):
        for check in gate.CHECKS:
            with self.subTest(check=check.name):
                self.assertTrue(check.profiles)
                self.assertTrue(set(check.profiles) <= set(VIEWPORTS))
        by_name = {c.name: c for c in gate.CHECKS}
        self.assertEqual(set(by_name['live edit'].profiles), {DESKTOP, MOBILE, TOUCH_WIDE})
        self.assertEqual(set(by_name['touch targets'].profiles), {MOBILE, TOUCH_WIDE})

    def test_the_planned_run_count_is_profiles_per_check_times_engines(self):
        self.assertEqual(gate.planned_runs(['chromium']), 15)
        self.assertEqual(gate.planned_runs(['chromium', 'firefox']), 30)
        self.assertEqual(gate.planned_runs([]), 0)

    def test_touch_profiles_emulate_touch_and_the_phone_is_390_wide(self):
        self.assertTrue(VIEWPORTS[MOBILE]['has_touch'])
        self.assertTrue(VIEWPORTS[TOUCH_WIDE]['has_touch'])
        self.assertNotIn('has_touch', VIEWPORTS[DESKTOP])
        self.assertEqual(VIEWPORTS[MOBILE]['viewport']['width'], 390)


def run_one(check, offline=False, opener=None, artifacts=None, blocking=True):
    """Run one check through the real runner with a fake context factory."""
    context, page = FakeContext(), FakePage()
    opener = opener or mock.Mock(return_value=(context, page, NetworkLog(), []))
    with mock.patch.object(gate, 'new_run_context', opener):
        findings = gate.run_one(check, MOBILE, 'chromium', object(), SERVED, offline, artifacts or Path('/nonexistent'),
                                blocking=blocking)
    return findings, context, page, opener


class RunOneTests(unittest.TestCase):
    def test_a_passing_check_has_no_findings_and_its_context_is_closed(self):
        findings, context, _, _ = run_one(gate.Check('c', lambda ctx: Outcome(), (MOBILE,)))
        self.assertEqual(findings, [])
        self.assertTrue(context.closed)

    def test_an_enforced_failure_is_a_fail_with_check_profile_and_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            findings, _, _, _ = run_one(gate.Check('c', lambda ctx: Outcome(failures=['bad']), (MOBILE,)),
                                        artifacts=Path(folder))
        self.assertEqual(findings, [Finding(FAIL, 'c', MOBILE, 'chromium', 'bad')])

    def test_a_report_only_check_reports_its_failures_and_still_passes(self):
        findings, _, page, _ = run_one(gate.Check('c', lambda ctx: Outcome(failures=['small']), (MOBILE,), enforced=False))
        self.assertEqual([f.kind for f in findings], [REPORT])
        self.assertEqual(page.shots, [], 'a REPORT does not take a failure screenshot')

    def test_a_check_that_raises_is_a_fail_and_the_run_continues(self):
        def explode(ctx):
            raise KeyError('landing.hero.title')
        with tempfile.TemporaryDirectory() as folder:
            findings, context, _, _ = run_one(gate.Check('c', explode, (MOBILE,)), artifacts=Path(folder))
        self.assertEqual([f.kind for f in findings], [FAIL])
        self.assertEqual(findings[0].detail, "raised KeyError: 'landing.hero.title'")
        self.assertTrue(context.closed)

    def test_a_crash_in_a_report_only_check_is_still_a_fail_because_the_gate_could_not_see(self):
        def explode(ctx):
            raise RuntimeError('selector rotted')
        with tempfile.TemporaryDirectory() as folder:
            findings, _, _, _ = run_one(gate.Check('c', explode, (MOBILE,), enforced=False), artifacts=Path(folder))
        self.assertEqual([f.kind for f in findings], [FAIL])

    def test_the_network_check_is_skipped_offline_without_opening_a_browser_context(self):
        check = gate.Check('free fonts load', lambda ctx: Outcome(), (DESKTOP,), needs_network=True)
        findings, _, _, opener = run_one(check, offline=True)
        self.assertEqual([f.kind for f in findings], [SKIP])
        self.assertIn('--offline', findings[0].detail)
        opener.assert_not_called()

    def test_online_the_network_check_gets_the_google_hosts_and_other_checks_get_none(self):
        _, _, _, opener = run_one(gate.Check('free fonts load', lambda ctx: Outcome(), (MOBILE,), needs_network=True))
        self.assertEqual(opener.call_args.args[3], runtime.GOOGLE_FONTS_HOSTS)
        _, _, _, opener = run_one(gate.Check('c', lambda ctx: Outcome(), (MOBILE,)))
        self.assertEqual(opener.call_args.args[3], ())

    def test_a_profile_that_cannot_open_is_a_fail(self):
        opener = mock.Mock(side_effect=RuntimeError('has_touch unsupported'))
        findings, _, _, _ = run_one(gate.Check('c', lambda ctx: Outcome(), (MOBILE,)), opener=opener)
        self.assertEqual([f.kind for f in findings], [FAIL])
        self.assertIn('could not be opened', findings[0].detail)
        self.assertIn('has_touch unsupported', findings[0].detail)

    def test_a_failing_run_leaves_a_screenshot_named_for_the_run(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, page, _ = run_one(gate.Check('live edit', lambda ctx: Outcome(failures=['x']), (MOBILE,)),
                                    artifacts=Path(folder))
            self.assertEqual([Path(p).name for p in page.shots], ['live-edit-mobile-chromium.png'])
            self.assertTrue((Path(folder) / 'live-edit-mobile-chromium.png').is_file())

    def test_the_check_receives_the_profile_engine_and_origins(self):
        seen = []
        run_one(gate.Check('c', lambda ctx: seen.append(ctx) or Outcome(), (MOBILE,)))
        ctx = seen[0]
        self.assertEqual((ctx.profile, ctx.engine, ctx.touch), (MOBILE, 'chromium', True))
        self.assertEqual(ctx.live_url, 'http://localhost:1111/font_kit_studio_v0.1.1.html'
                                       '?target=http://localhost:2222/demo/')
        self.assertEqual(ctx.demo_url, 'http://localhost:2222/demo/')


class AdvisoryRunTests(unittest.TestCase):
    def test_an_advisory_run_prints_its_failure_as_advisory_and_keeps_the_screenshot(self):
        with tempfile.TemporaryDirectory() as folder:
            findings, _, page, _ = run_one(gate.Check('c', lambda ctx: Outcome(failures=['bad']), (MOBILE,)),
                                           artifacts=Path(folder), blocking=False)
        self.assertEqual(findings, [Finding(ADVISORY, 'c', MOBILE, 'chromium', 'bad')])
        self.assertEqual(len(page.shots), 1, 'the picture of an advisory failure is still useful')

    def test_a_check_that_raises_on_an_advisory_run_is_advisory_too(self):
        def explode(ctx):
            raise KeyError('landing.hero.title')
        with tempfile.TemporaryDirectory() as folder:
            findings, context, _, _ = run_one(gate.Check('c', explode, (MOBILE,)), artifacts=Path(folder), blocking=False)
        self.assertEqual([f.kind for f in findings], [ADVISORY])
        self.assertIn('raised KeyError', findings[0].detail)
        self.assertTrue(context.closed)

    def test_a_profile_that_cannot_open_is_advisory_on_an_advisory_run(self):
        opener = mock.Mock(side_effect=RuntimeError('has_touch unsupported'))
        findings, _, _, _ = run_one(gate.Check('c', lambda ctx: Outcome(), (MOBILE,)), opener=opener, blocking=False)
        self.assertEqual([f.kind for f in findings], [ADVISORY])

    def test_reports_and_skips_are_unchanged_on_an_advisory_run(self):
        check = gate.Check('c', lambda ctx: Outcome(reports=['r'], skips=['s']), (MOBILE,))
        findings, _, _, _ = run_one(check, blocking=False)
        self.assertEqual([f.kind for f in findings], [REPORT, SKIP])


class PolicyRunTests(unittest.TestCase):
    """The default policy at the runner level: only chromium at desktop can fail the gate."""

    def run_matrix(self, policy, failing=((('chromium', DESKTOP)),)):
        def fails_where_asked(ctx):
            return Outcome(failures=['bad']) if (ctx.engine, ctx.profile) in failing else Outcome()
        checks = (gate.Check('c', fails_where_asked, (DESKTOP, MOBILE, TOUCH_WIDE)),)
        lines = []
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
                gate, 'new_run_context', lambda *a, **k: (FakeContext(), FakePage(), NetworkLog(), [])):
            tally = gate.run_checks({'chromium': object(), 'firefox': object()}, SERVED, False, Path(folder),
                                    emit=lines.append, checks=checks, policy=EnforcementPolicy.parse(policy))
        return tally, lines

    def test_a_firefox_or_phone_failure_is_advisory_and_exits_zero_under_the_default(self):
        tally, lines = self.run_matrix('chromium:desktop', failing=(
            ('firefox', DESKTOP), ('firefox', MOBILE), ('chromium', MOBILE), ('chromium', TOUCH_WIDE)))
        self.assertEqual(gate.exit_code(tally), 0)
        self.assertEqual(sum(1 for line in lines if ' ADVISORY ' in line), 4)
        self.assertFalse(any(' FAIL ' in line for line in lines))
        self.assertEqual(tally.planned, 6, 'every run still happens and is counted')
        self.assertEqual(len(tally.statuses), 6)

    def test_a_chromium_desktop_failure_blocks_under_the_default(self):
        tally, lines = self.run_matrix('chromium:desktop', failing=(('chromium', DESKTOP),))
        self.assertEqual(gate.exit_code(tally), 1)
        self.assertIn('[frontend_gate] FAIL c [desktop, chromium]: bad', lines)

    def test_all_makes_the_same_firefox_failure_block(self):
        tally, lines = self.run_matrix('all', failing=(('firefox', MOBILE),))
        self.assertEqual(gate.exit_code(tally), 1)
        self.assertIn('[frontend_gate] FAIL c [mobile, firefox]: bad', lines)

    def test_an_advisory_run_with_findings_prints_no_pass_line(self):
        _, lines = self.run_matrix('chromium:desktop', failing=(('firefox', MOBILE),))
        self.assertIn('[frontend_gate] ADVISORY c [mobile, firefox]: bad', lines)
        self.assertNotIn('[frontend_gate] PASS c [mobile, firefox]', lines)
        self.assertIn('[frontend_gate] PASS c [desktop, firefox]', lines)

    def test_the_summary_separates_blocking_from_advisory(self):
        tally, _ = self.run_matrix('chromium:desktop', failing=(('firefox', DESKTOP), ('chromium', MOBILE)))
        self.assertEqual(
            gate.summary_line(tally),
            '[frontend_gate] SUMMARY OK: 6 of 6 planned runs finished. Blocking: 1 runs, 1 passed, 0 failed, '
            '0 skipped. Advisory: 5 runs, 2 ADVISORY lines. 0 REPORT lines, 0 SKIP lines, 0 FAIL lines')


class RunChecksTests(unittest.TestCase):
    def test_the_tally_counts_every_planned_run_and_prints_findings_and_pass_lines(self):
        checks = (
            gate.Check('ok', lambda ctx: Outcome(), (DESKTOP, MOBILE)),
            gate.Check('bad', lambda ctx: Outcome(failures=['broken']), (DESKTOP,)),
            gate.Check('small', lambda ctx: Outcome(failures=['tiny']), (MOBILE,), enforced=False),
        )
        lines = []
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
                gate, 'new_run_context', lambda *a, **k: (FakeContext(), FakePage(), NetworkLog(), [])):
            tally = gate.run_checks({'chromium': object(), 'firefox': object()}, SERVED, False, Path(folder),
                                    emit=lines.append, checks=checks, policy=EnforcementPolicy.parse('all'))
        self.assertEqual(tally.planned, 8)
        self.assertEqual((tally.passed, tally.failed, tally.skipped), (6, 2, 0))
        self.assertIn('[frontend_gate] FAIL bad [desktop, firefox]: broken', lines)
        self.assertIn('[frontend_gate] REPORT small [mobile, chromium]: tiny', lines)
        self.assertIn('[frontend_gate] PASS ok [mobile, firefox]', lines)
        self.assertEqual(gate.exit_code(tally), 1)

    def test_every_engine_runs_every_check(self):
        calls = []
        checks = (gate.Check('c', lambda ctx: calls.append((ctx.engine, ctx.profile)) or Outcome(), (DESKTOP, MOBILE)),)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
                gate, 'new_run_context', lambda *a, **k: (FakeContext(), FakePage(), NetworkLog(), [])):
            tally = gate.run_checks({'chromium': 1, 'firefox': 2}, SERVED, False, Path(folder), emit=lambda line: None,
                                    checks=checks, policy=EnforcementPolicy.parse('all'))
        self.assertEqual(calls, [('chromium', DESKTOP), ('chromium', MOBILE), ('firefox', DESKTOP), ('firefox', MOBILE)])
        self.assertEqual(gate.exit_code(tally), 0)


class ScreenshotFolderTests(unittest.TestCase):
    def test_stale_screenshots_are_cleared_and_other_files_are_left_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'old-failure.png').write_bytes(b'x')
            (root / 'notes.txt').write_text('keep')
            gate.clear_screenshots(root)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['notes.txt'])

    def test_a_missing_folder_is_not_an_error(self):
        gate.clear_screenshots(Path('/nonexistent/frontend-gate'))


class EngineAvailabilityTests(unittest.TestCase):
    def test_an_engine_has_blocking_runs_only_when_the_policy_selects_one_of_its_runs(self):
        default = EnforcementPolicy.parse('chromium:desktop')
        self.assertTrue(gate.engine_has_blocking(default, 'chromium'))
        self.assertFalse(gate.engine_has_blocking(default, 'firefox'))
        self.assertTrue(gate.engine_has_blocking(EnforcementPolicy.parse('all'), 'firefox'))
        self.assertTrue(gate.engine_has_blocking(EnforcementPolicy.parse('firefox:wide touch'), 'firefox'))
        self.assertFalse(gate.engine_has_blocking(EnforcementPolicy.parse('none'), 'chromium'))

    def test_an_unavailable_engine_is_one_advisory_line_and_its_runs_are_counted_as_not_run(self):
        lines = []
        checks = (gate.Check('c', lambda ctx: Outcome(), (DESKTOP, MOBILE)),)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
                gate, 'new_run_context', lambda *a, **k: (FakeContext(), FakePage(), NetworkLog(), [])):
            tally = gate.run_checks({'chromium': object()}, SERVED, False, Path(folder), emit=lines.append,
                                    checks=checks, unavailable={'firefox': 'firefox is not installed'})
        self.assertEqual(tally.planned, 4)
        self.assertEqual((len(tally.statuses), tally.not_run), (2, 2))
        self.assertIn('[frontend_gate] ADVISORY engine [firefox]: could not launch: firefox is not installed', lines)
        self.assertEqual(gate.exit_code(tally), 0)
        self.assertIn('2 of 4 planned runs finished, 2 not run', gate.summary_line(tally))


class MainTests(unittest.TestCase):
    def main(self, argv, **patches):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), contextlib.ExitStack() as stack:
            for name, value in patches.items():
                stack.enter_context(mock.patch.object(gate, name, value))
            code = gate.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_an_unknown_engine_exits_one_with_a_clear_error(self):
        code, _, err = self.main(['--engines', 'safari'])
        self.assertEqual(code, 1)
        self.assertIn('[frontend_gate] ERROR: unknown engine', err)

    def test_missing_playwright_exits_one_with_the_install_command(self):
        def missing():
            raise runtime.GateError(f'Playwright is not installed. Run: {runtime.SETUP_COMMAND}')
        code, _, err = self.main(['--engines', 'chromium'], load_playwright=missing)
        self.assertEqual(code, 1)
        self.assertIn('python -m playwright install chromium firefox', err)

    def test_a_missing_browser_exits_one_before_anything_is_served(self):
        served = mock.Mock()

        def no_browser(playwright, engine, headless=True):
            raise runtime.GateError(f'{engine} is not available to Playwright. Run: {runtime.SETUP_COMMAND}')

        fake_playwright = contextlib.nullcontext(object())
        code, _, err = self.main(['--engines', 'chromium'], load_playwright=lambda: (lambda: fake_playwright),
                                 launch_browser=no_browser, serve_app=served)
        self.assertEqual(code, 1)
        self.assertIn('chromium is not available to Playwright. Run: python -m playwright install', err)
        served.assert_not_called()

    def launch_only(self, working):
        """A launch_browser fake that works for `working` engines and raises GateError for the rest."""
        def launch(playwright, engine, headless=True):
            if engine not in working:
                raise runtime.GateError(f'{engine} is not available to Playwright. Run: {runtime.SETUP_COMMAND}')
            return mock.Mock()
        return launch

    def run_main(self, argv, working, tally_planned=None):
        seen = {}
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)

        def spy(browsers, served, offline, artifacts, policy=None, unavailable=None, **kwargs):
            seen['browsers'], seen['unavailable'] = list(browsers), dict(unavailable or {})
            tally = Tally(planned=0)
            return tally

        code, out, err = self.main([*argv, '--artifacts', scratch.name],
                                   load_playwright=lambda: (lambda: contextlib.nullcontext(object())),
                                   launch_browser=self.launch_only(working),
                                   serve_app=lambda: contextlib.nullcontext(SERVED), run_checks=spy)
        return code, out, err, seen

    def test_a_missing_firefox_is_advisory_under_the_default_policy_and_chromium_still_runs(self):
        code, out, err, seen = self.run_main(['--engines', 'chromium,firefox'], working={'chromium'})
        self.assertEqual(code, 0, err)
        self.assertEqual(seen['browsers'], ['chromium'])
        self.assertEqual(list(seen['unavailable']), ['firefox'])
        self.assertIn('firefox is not available', seen['unavailable']['firefox'])
        self.assertEqual(err, '')

    def test_a_missing_chromium_still_fails_because_it_has_blocking_runs(self):
        code, _, err, seen = self.run_main(['--engines', 'chromium,firefox'], working={'firefox'})
        self.assertEqual(code, 1)
        self.assertIn('[frontend_gate] ERROR: chromium is not available', err)
        self.assertNotIn('browsers', seen, 'nothing ran')

    def test_a_missing_firefox_blocks_when_the_policy_enforces_it(self):
        code, _, err, _ = self.run_main(['--engines', 'chromium,firefox', '--enforce', 'all'], working={'chromium'})
        self.assertEqual(code, 1)
        self.assertIn('firefox is not available', err)

    def test_a_policy_with_no_blocking_run_among_the_selected_engines_is_an_error(self):
        code, _, err, seen = self.run_main(['--engines', 'chromium', '--enforce', 'firefox:desktop'],
                                           working={'chromium'})
        self.assertEqual(code, 1)
        self.assertIn('[frontend_gate] ERROR: no blocking runs', err)
        self.assertIn('--enforce none', err)
        self.assertNotIn('browsers', seen, 'it fails before launching anything')

    def test_none_deliberately_makes_the_whole_gate_advisory(self):
        code, _, err, seen = self.run_main(['--engines', 'chromium', '--enforce', 'none'], working={'chromium'})
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(seen['browsers'], ['chromium'])

    def test_a_bad_enforce_value_exits_one_with_a_clear_error(self):
        code, _, err = self.main(['--engines', 'chromium', '--enforce', 'chromium:tablet'])
        self.assertEqual(code, 1)
        self.assertIn('[frontend_gate] ERROR:', err)

    def test_the_enforce_flag_reaches_the_runner_and_defaults_to_desktop_first(self):
        seen = []

        def spy(browsers, served, offline, artifacts, policy=None, **kwargs):
            seen.append(policy)
            return Tally(planned=0)

        for argv, wanted in ((['--engines', 'chromium', '--offline'], ('chromium', 'mobile', False)),
                              (['--engines', 'chromium', '--offline', '--enforce', 'all'], ('chromium', 'mobile', True))):
            scratch = tempfile.TemporaryDirectory()
            self.addCleanup(scratch.cleanup)
            self.main([*argv, '--artifacts', scratch.name],
                      load_playwright=lambda: (lambda: contextlib.nullcontext(object())),
                      launch_browser=lambda playwright, engine, headless=True: mock.Mock(),
                      serve_app=lambda: contextlib.nullcontext(SERVED), run_checks=spy)
            engine, profile, blocking = wanted
            self.assertEqual(seen[-1].blocking(engine, profile), blocking)
            self.assertTrue(seen[-1].blocking('chromium', 'desktop'))

    def test_a_clean_run_prints_the_summary_and_exits_zero(self):
        code, out = self.run_with(Tally(planned=0))
        self.assertEqual(code, 0)
        self.assertIn('SUMMARY OK', out)

    def test_a_failing_run_exits_one(self):
        tally = Tally(planned=1)
        tally.record([Finding(FAIL, 'c', MOBILE, 'chromium', 'x')])
        code, out = self.run_with(tally)
        self.assertEqual(code, 1)
        self.assertIn('SUMMARY FAIL', out)

    def test_report_lines_alone_leave_the_exit_code_at_zero(self):
        tally = Tally(planned=1)
        tally.record([Finding(REPORT, 'touch targets', MOBILE, 'chromium', 'x')])
        self.assertEqual(self.run_with(tally)[0], 0)

    def run_with(self, tally):
        browser = mock.Mock()
        scratch = tempfile.TemporaryDirectory()  # never touch the real work/frontend-gate
        self.addCleanup(scratch.cleanup)
        code, out, _ = self.main(
            ['--engines', 'chromium', '--offline', '--artifacts', scratch.name],
            load_playwright=lambda: (lambda: contextlib.nullcontext(object())),
            launch_browser=lambda playwright, engine, headless=True: browser,
            serve_app=lambda: contextlib.nullcontext(SERVED),
            run_checks=lambda *args, **kwargs: tally)
        browser.close.assert_called_once()
        return code, out


class ServerLifecycleTests(unittest.TestCase):
    def test_the_dev_server_starts_on_free_ports_serves_both_origins_and_is_gone_afterwards(self):
        import socket
        import urllib.request
        with runtime.serve_app() as served:
            studio = urllib.request.urlopen(served.studio_origin + '/__fontkit/status', timeout=5).read()
            self.assertIn(b'"sync": false', studio, 'the gate runs the server with --no-sync')
            self.assertEqual(urllib.request.urlopen(served.target_origin + '/demo/', timeout=5).status, 200)
            port = int(served.studio_origin.rsplit(':', 1)[1])
        with self.assertRaises(OSError), socket.create_connection(('127.0.0.1', port), timeout=1):
            pass


if __name__ == '__main__':
    unittest.main()
