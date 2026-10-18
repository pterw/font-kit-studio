"""The bridge tells Studio when the page's route or content moved: design:roles-page, data only."""
from support import ENGINES
from role_support import EVIL, ROLE_PAGE, TARGET
from test_role_stylesheet import PLAIN_24, PLAIN_24_HASH, RoleSheetCase, role

SPA = TARGET + '/fixtures/multi-page/spa.html'
LARGE = TARGET + '/fixtures/large-page/index.html'
KEYS = {'type', 'protocolVersion', 'sessionId', 'documentId', 'pageVersion', 'pageURL'}
NAMES = "() => { const names = []; for (const name in history) names.push(name); return names.sort(); }"
BOTH = '() => [Object.getOwnPropertyNames(history), (' + NAMES + ')()]'


class RoleRouteCase(RoleSheetCase):
    def start(self, engine, target=ROLE_PAGE):
        page, frame = self.open(engine, target=target)
        ready = self.hello(page)
        return page, frame, ready, self.mark(page)

    def notices(self, page, start, timeout=3000, settle=500):
        """The roles-page messages from `start`: wait for the first (up to `timeout`), then `settle` for stragglers."""
        return page.evaluate("""([start, timeout, settle]) => new Promise(resolve => {
            const began = performance.now(), found = () => messages('design:roles-page', start);
            const poll = () => {
              if (found().length) setTimeout(() => resolve(found()), settle);
              else if (performance.now() - began > timeout) resolve([]);
              else setTimeout(poll, 20);
            };
            poll();
        })""", [start, timeout, settle])

    def silence(self, page, start, ms=600):
        """The 600 ms absence check the Test Quality Rules allow for proving that nothing was sent."""
        page.wait_for_timeout(ms)
        return self.messages(page, 'design:roles-page', start)

    def urls(self, notices):
        return [m['pageURL'] for m in notices]

    def proof(self, page, frame):
        """One history push shows this page can send; returns after its hold has passed."""
        start = self.mark(page)
        frame.evaluate("history.pushState(null, '', '?route=proof')")
        self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=proof'])


class RouteAnnouncementTests(RoleRouteCase):
    def test_url_only_routes_announce_each_literal_url_without_a_dom_change(self):
        """Given the role page after hello, when it pushes, replaces, sets a hash and goes back, then each yields one roles-page with the literal URL and a greater version while the body text is unchanged."""
        steps = [("history.pushState({a: 1}, '', '?route=x')", '?route=x'),
                 ("history.replaceState(null, '', '?route=y')", '?route=y'),
                 ("location.hash = '#z'", '?route=y#z'), ('history.back()', '?route=y')]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, _ = self.start(engine)
                version = ready['roleState']['pageVersion']
                for script, suffix in steps:
                    with self.subTest(step=script):
                        start = self.mark(page)
                        frame.evaluate(script)
                        got = self.notices(page, start)
                        self.assertEqual(self.urls(got), [ROLE_PAGE + suffix])
                        self.assertGreater(got[0]['pageVersion'], version)
                        version = got[0]['pageVersion']
                        self.assertEqual(frame.locator('.body-copy').first.inner_text(), 'Author body')

    def test_a_popstate_event_alone_announces_the_current_url(self):
        """Given a URL changed by the cached native pushState, when only a popstate event is dispatched, then nothing is sent before it and one roles-page for that URL follows."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("History.prototype.pushState.call(history, null, '', '?route=n')")
                self.assertEqual(self.silence(page, start, 300), [])
                frame.evaluate("dispatchEvent(new PopStateEvent('popstate'))")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=n'])

    def test_a_hashchange_event_alone_announces_the_current_url(self):
        """Given a hash changed by the cached native pushState, when only a hashchange event is dispatched, then nothing is sent before it and one roles-page for that URL follows."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("History.prototype.pushState.call(history, null, '', '#h')")
                self.assertEqual(self.silence(page, start, 300), [])
                frame.evaluate("dispatchEvent(new HashChangeEvent('hashchange'))")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '#h'])

    def test_a_change_inside_the_hold_is_announced_once_by_the_trailing_send(self):
        """Given a first route message, when a second change comes 50 ms later with no DOM change, then one more roles-page with the new identity and a greater version arrives within 600 ms and no third follows."""
        seconds = {
            'push': (lambda page, frame: frame.evaluate("history.pushState(null, '', '?route=b')"), '?route=b'),
            'resize': (lambda page, frame: page.evaluate("document.querySelector('#target').style.width = '1000px'"), '?route=a'),
            'hash': (lambda page, frame: frame.evaluate("location.hash = '#hh'"), '?route=a#hh'),
        }
        for engine in ENGINES:
            for kind, (change, suffix) in seconds.items():
                with self.subTest(engine=engine, second=kind):
                    page, frame, _, start = self.start(engine)
                    frame.evaluate("history.pushState(null, '', '?route=a')")
                    first = self.notices(page, start, settle=0)
                    self.assertEqual(self.urls(first), [ROLE_PAGE + '?route=a'])
                    page.wait_for_timeout(50)
                    mark = self.mark(page)
                    change(page, frame)
                    second = self.notices(page, mark, timeout=600, settle=700)
                    self.assertEqual(self.urls(second), [ROLE_PAGE + suffix])
                    self.assertGreater(second[0]['pageVersion'], first[0]['pageVersion'])

    def test_a_fast_sequence_of_route_kinds_ends_on_the_final_url_and_the_detect_version(self):
        """Given push, replace, hash and back about 50 ms apart, when the page is quiet, then the last roles-page carries the final URL and the pageVersion a Detect reports."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                for script in ("history.pushState(null, '', '?route=x')", "history.replaceState(null, '', '?route=y')",
                               "location.hash = '#z'", 'history.back()'):
                    frame.evaluate(script)
                    page.wait_for_timeout(50)
                got = self.notices(page, start, settle=800)
                self.assertEqual(got[-1:] and got[-1]['pageURL'], ROLE_PAGE + '?route=y')
                reply = self.detect(page)
                self.assertEqual((reply['pageURL'], reply['pageVersion']), (ROLE_PAGE + '?route=y', got[-1]['pageVersion']))

    def test_a_route_that_returns_to_the_same_url_in_one_window_advances_no_version(self):
        """Given a replace to another URL and back to the first in one task, when the page is quiet, then no roles-page is sent and a Detect reports the ready's pageVersion."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("() => { history.replaceState(null, '', '?route=b'); history.replaceState(null, '', location.pathname); }")
                self.assertEqual(self.silence(page, start), [])
                self.assertEqual(self.detect(page)['pageVersion'], ready['roleState']['pageVersion'])


class ContentAndStyleTests(RoleRouteCase):
    def test_content_only_change_sends_the_six_keys_and_the_version_a_detect_reports(self):
        """Given the ready's pageVersion, when body text changes with no history call, then one roles-page carries exactly the six keys, the same URL and document, a greater version, and the version a Detect reports."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("document.querySelector('.body-copy').textContent = 'Changed copy'")
                got = self.notices(page, start)
                self.assertEqual(self.urls(got), [ROLE_PAGE])
                message = got[0]
                self.assertEqual(set(message), KEYS)
                self.assertEqual((message['type'], message['protocolVersion'], message['sessionId'], message['documentId']),
                                 ('design:roles-page', 1, 's1', ready['roleState']['documentId']))
                self.assertGreater(message['pageVersion'], ready['roleState']['pageVersion'])
                self.assertEqual(self.detect(page)['pageVersion'], message['pageVersion'])

    def test_a_rendered_swap_on_the_spa_announces_with_the_same_url(self):
        """Given the SPA page after hello, when render('same') swaps the route content, then one roles-page keeps the URL and has a greater version."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine, SPA)
                frame.evaluate("render('same')")
                got = self.notices(page, start)
                self.assertEqual(self.urls(got), [SPA])
                self.assertGreater(got[0]['pageVersion'], ready['roleState']['pageVersion'])

    def test_style_node_media_change_and_host_resize_each_announce(self):
        """Given the role page after hello, when a style node is appended, a media attribute changes or the host iframe is resized, then each yields one roles-page with the same URL and a greater version."""
        causes = {
            'appended style': lambda page, frame: frame.evaluate(
                "() => { const s = document.createElement('style'); s.textContent = '.body-copy { color: red }'; document.head.appendChild(s); }"),
            'media attribute': lambda page, frame: frame.evaluate("document.querySelector('style').setAttribute('media', 'print')"),
            'host resize': lambda page, frame: page.evaluate("document.querySelector('#target').style.width = '1000px'"),
        }
        for engine in ENGINES:
            for label, change in causes.items():
                with self.subTest(engine=engine, cause=label):
                    page, frame, ready, start = self.start(engine)
                    change(page, frame)
                    got = self.notices(page, start)
                    self.assertEqual(self.urls(got), [ROLE_PAGE])
                    self.assertGreater(got[0]['pageVersion'], ready['roleState']['pageVersion'])

    def test_a_silent_cssom_insert_rule_sends_nothing_but_a_detect_notices_it(self):
        """Given a fresh page, when a CSSOM rule is inserted with no DOM change, then nothing is sent for 600 ms and a following Detect is followed by one roles-page carrying the Detect reply's pageVersion."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("() => { const sheet = document.styleSheets[0]; sheet.insertRule('.body-copy { letter-spacing: 1px }', sheet.cssRules.length); }")
                self.assertEqual(self.silence(page, start), [])
                reply = self.detect(page)
                got = self.notices(page, start)
                self.assertGreater(reply['pageVersion'], ready['roleState']['pageVersion'])
                self.assertEqual([m['pageVersion'] for m in got], [reply['pageVersion']])

    def test_an_unsupported_url_is_sent_as_null_and_the_supported_url_follows_inside_the_hold(self):
        """Given a 2,000-character URL, when it replaces the route, then one roles-page has pageURL null and a greater version, and replacing back 50 ms later sends the supported URL within 600 ms."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("history.replaceState(null, '', '/?' + 'x'.repeat(1999))")
                first = self.notices(page, start, settle=0)
                self.assertEqual(self.urls(first), [None])
                self.assertGreater(first[0]['pageVersion'], ready['roleState']['pageVersion'])
                page.wait_for_timeout(50)
                mark = self.mark(page)
                frame.evaluate("history.replaceState(null, '', '/tests/fixtures/bridge/target-role-protocol.html')")
                second = self.notices(page, mark, timeout=600, settle=0)
                self.assertEqual(self.urls(second), [ROLE_PAGE])
                self.assertGreater(second[0]['pageVersion'], first[0]['pageVersion'])


class QuietWritesTests(RoleRouteCase):
    def test_bridge_writes_and_native_state_send_nothing_after_a_push_proves_the_page_can(self):
        """Given a page that just sent for a push, when Studio applies, clears, detects under a preview, edits, or the user focuses and hovers, then no roles-page follows within 600 ms."""
        def nothing(page, frame, ident):
            return None

        def preview(page, frame, ident):
            self.assertEqual(self.apply(page, [role(fontSize=24)], **ident)['type'], 'design:roles-applied')

        def add_input(page, frame, ident):
            mark = self.mark(page)
            frame.evaluate("document.body.insertAdjacentElement('beforeend', Object.assign(document.createElement('input'), {ariaLabel: 'probe'}))")
            self.assertEqual(len(self.notices(page, mark)), 1)

        def focus_and_hover(page, frame):
            frame.locator('input').focus()
            frame.locator('input').hover()

        cases = {
            'apply': (nothing, lambda page, frame, ident: self.apply(page, [role(fontSize=24)], **ident)),
            'clear': (preview, lambda page, frame, ident: self.clear(page, **ident)),
            'detect under a preview': (preview, lambda page, frame, ident: self.detect(page)),
            'inspector edit': (nothing, lambda page, frame, ident: self.applied(page, 'role.body', {'fontSize': 20})),
            'native focus and hover': (add_input, lambda page, frame, ident: focus_and_hover(page, frame)),
        }
        for engine in ENGINES:
            for label, (setup, action) in cases.items():
                with self.subTest(engine=engine, action=label):
                    page, frame, _, _ = self.start(engine)
                    self.proof(page, frame)
                    ident = self.current(page)
                    setup(page, frame, ident)
                    start = self.mark(page)
                    action(page, frame, ident)
                    self.assertEqual(self.silence(page, start), [])

    def test_a_history_push_under_an_applied_preview_leaves_the_roles_unchanged(self):
        """Given an applied 24px preview, when the page pushes a URL, then one roles-page is sent while the owned sheet, revision, size and the re-greeted role state stay the applied ones."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, _ = self.start(engine)
                applied = self.apply(page, [role(fontSize=24)])
                self.assertEqual(applied['type'], 'design:roles-applied', applied)
                start = self.mark(page)
                frame.evaluate("history.pushState(null, '', '?route=p')")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=p'])
                self.assertEqual((self.owned(frame), self.size(frame)), ([PLAIN_24], '24px'))
                again = self.hello(page, 's2')
                self.assertEqual(again['revision'], applied['revision'])
                state = again['roleState']
                self.assertEqual((state['canonicalCss'], state['cssHash'], state['roles']), (PLAIN_24, PLAIN_24_HASH, [role(fontSize=24)]))


class ScheduleTests(RoleRouteCase):
    def test_a_burst_of_history_calls_yields_one_message_for_the_last_url(self):
        """Given 100 replaceState calls and pushes A, B and C in one task, when the page is quiet, then exactly one roles-page arrives and its URL is C's."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("""() => {
                    for (let i = 0; i < 100; i++) history.replaceState(null, '', '?r=' + i);
                    history.pushState(null, '', '?a'); history.pushState(null, '', '?b'); history.pushState(null, '', '?c');
                }""")
                self.assertEqual(self.urls(self.notices(page, start, settle=700)), [ROLE_PAGE + '?c'])

    def test_a_stream_of_edits_is_rate_limited_and_ends_on_the_detect_version(self):
        """Given text edits every 5 ms for about a second, when the page is quiet, then the message count is from 1 to floor(elapsed/250)+2 and the last version equals a Detect's."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                elapsed = frame.evaluate("""() => new Promise(resolve => {
                    const began = performance.now(); let n = 0;
                    const tick = setInterval(() => {
                        document.querySelector('.body-copy').textContent = 'edit ' + (++n);
                        if (performance.now() - began >= 1000) { clearInterval(tick); resolve(performance.now() - began); }
                    }, 5);
                })""")
                got = self.notices(page, start, settle=800)
                self.assertGreaterEqual(len(got), 1)
                self.assertLessEqual(len(got), elapsed // 250 + 2)
                self.assertEqual(self.detect(page)['pageVersion'], got[-1]['pageVersion'])

    def test_the_notice_follows_the_next_rendered_frame_not_the_history_call(self):
        """Given a push and a requestAnimationFrame marker registered after it, when both arrive, then the marker precedes the roles-page."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("""() => {
                    history.pushState(null, '', '?route=r');
                    requestAnimationFrame(() => parent.postMessage({type: 't6b1:marker'}, '*'));
                }""")
                self.notices(page, start)
                order = page.evaluate("start => log.slice(start).map(e => e.data && e.data.type)", start)
                self.assertEqual([t for t in order if t in ('t6b1:marker', 'design:roles-page')], ['t6b1:marker', 'design:roles-page'])

    def test_without_a_paint_the_notice_arrives_from_the_250ms_fallback(self):
        """Given requestAnimationFrame replaced by a no-op, when the page pushes a URL, then one roles-page still arrives within 1,500 ms."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("window.requestAnimationFrame = () => 0")
                frame.evaluate("history.pushState(null, '', '?route=nopaint')")
                self.assertEqual(self.urls(self.notices(page, start, timeout=1500, settle=300)), [ROLE_PAGE + '?route=nopaint'])


class WrapperTests(RoleRouteCase):
    def test_the_wrapper_keeps_receiver_arguments_return_value_and_state(self):
        """Given an app wrapper installed before hello, when the page calls pushState or replaceState with a state, then the earlier wrapper gets the same state, title, URL and receiver, the call returns undefined, history.state equals the state, and one roles-page follows."""
        for engine in ENGINES:
            for method in ('pushState', 'replaceState'):
                with self.subTest(engine=engine, method=method):
                    page, frame = self.open(engine)
                    frame.evaluate("""method => {
                        const original = history[method]; window.seen = [];
                        history[method] = function (...args) { window.seen.push({receiver: this === history, args}); return original.apply(this, args); };
                    }""", method)
                    self.hello(page)
                    start = self.mark(page)
                    result = frame.evaluate("""method => {
                        const state = {k: [1, 2]}, returned = history[method](state, 'Title', '?route=w');
                        const {receiver, args: [passed, title, url]} = window.seen[0];
                        return {same: passed === state, title, url, receiver, returned: returned === undefined,
                                state: JSON.stringify(history.state), search: location.search};
                    }""", method)
                    self.assertEqual(result, {'same': True, 'title': 'Title', 'url': '?route=w', 'receiver': True, 'returned': True,
                                              'state': '{"k":[1,2]}', 'search': '?route=w'})
                    self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=w'])

    def test_native_exceptions_pass_through_and_send_nothing(self):
        """Given a successful push that sent, when a cross-origin URL, an uncloneable state or a non-History receiver is used, then the page gets its own SecurityError, DataCloneError or TypeError, the URL is unchanged and nothing is sent."""
        failures = {
            'SecurityError': ("history.pushState(null, '', 'http://evil.test/x')", 'DOMException'),
            'DataCloneError': ("history.pushState(() => {}, '', '?bad')", 'DOMException'),
            'TypeError': ("history.pushState.call({}, null, '', '?bad')", 'TypeError'),
        }
        for engine in ENGINES:
            for name, (call, kind) in failures.items():
                with self.subTest(engine=engine, error=name):
                    page, frame, _, start = self.start(engine)
                    frame.evaluate("history.pushState(null, '', '?route=ok')")
                    self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=ok'])
                    mark = self.mark(page)
                    caught = frame.evaluate(f"() => {{ try {{ {call}; return null; }} catch (e) {{ return [e.name, e instanceof {kind}]; }} }}")
                    self.assertEqual(caught, [name, True])
                    self.assertEqual(frame.evaluate('location.href'), ROLE_PAGE + '?route=ok')
                    self.assertEqual(self.silence(page, mark), [])


class InstallAndRemovalTests(RoleRouteCase):
    def test_history_is_native_and_silent_before_hello(self):
        """Given a page before any hello, when it pushes a URL, then pushState and replaceState are the prototype's, history has no own State names, nothing is posted to Studio, and the later ready carries that URL."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                native = frame.evaluate("""() => ({same: history.pushState === History.prototype.pushState
                    && history.replaceState === History.prototype.replaceState, own: Object.getOwnPropertyNames(history)})""")
                self.assertEqual(native, {'same': True, 'own': []})
                frame.evaluate("history.pushState(null, '', '?route=pre')")
                page.wait_for_timeout(400)
                self.assertEqual(page.evaluate("log.filter(e => e.data && e.data.type === 'design:roles-page').length"), 0)
                self.assertEqual(self.hello(page)['roleState']['pageURL'], ROLE_PAGE + '?route=pre')

    def test_the_first_hello_installs_wrappers_once_and_keeps_the_enumerable_names(self):
        """Given a page before hello, when the first and a second hello arrive, then the methods differ from the prototype's after the first, are the same functions after the second, the for-in name set is unchanged, and each wrapper has the native method's name and length."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                before = frame.evaluate(NAMES)
                native = frame.evaluate("() => ['pushState', 'replaceState'].map(n => [History.prototype[n].name, History.prototype[n].length])")
                self.assertEqual([n for n, _ in native], ['pushState', 'replaceState'])
                self.hello(page)
                installed = frame.evaluate("""() => { window.kept = [history.pushState, history.replaceState];
                    return [history.pushState !== History.prototype.pushState, history.replaceState !== History.prototype.replaceState]; }""")
                self.assertEqual(installed, [True, True])
                self.assertEqual(frame.evaluate("() => window.kept.map(f => [f.name, f.length])"), native)
                self.hello(page, 's2')
                self.assertTrue(frame.evaluate('() => history.pushState === window.kept[0] && history.replaceState === window.kept[1]'))
                self.assertEqual(frame.evaluate(NAMES), before)

    def test_a_hello_from_a_sibling_frame_installs_nothing_and_it_hears_nothing(self):
        """Given a page with no Studio session, when a sibling frame from another origin says hello and the page then pushes, then history stays native and that frame receives no message."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                page.evaluate("""() => new Promise(resolve => {
                    const evil = document.createElement('iframe'); evil.title = 'evil'; evil.onload = () => resolve();
                    evil.src = 'http://evil.test/evil.html'; document.body.appendChild(evil);
                })""")
                evil = next(f for f in page.frames if f.url.startswith(EVIL))
                evil.evaluate("sendToTarget({type: 'design:hello', protocolVersion: 1, sessionId: 'evil'})")
                page.wait_for_timeout(400)
                self.assertTrue(frame.evaluate('() => history.pushState === History.prototype.pushState'))
                frame.evaluate("history.pushState(null, '', '?route=evil')")
                page.wait_for_timeout(600)
                self.assertEqual(evil.evaluate('received'), [])

    def test_dispose_restores_the_native_methods_and_leaves_no_own_names(self):
        """Given an installed bridge, when it is disposed, then the prototype's functions are back, the own and for-in names equal those before hello, and a push sends nothing."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                before = frame.evaluate(BOTH)
                self.hello(page)
                start = self.mark(page)
                frame.evaluate("history.pushState(null, '', '?route=one')")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=one'])
                frame.evaluate('__fontkitBridge.dispose()')
                after = frame.evaluate(BOTH)
                self.assertEqual(after, before)
                self.assertTrue(frame.evaluate('() => history.pushState === History.prototype.pushState && history.replaceState === History.prototype.replaceState'))

    def test_dispose_gives_an_app_owned_property_its_descriptor_back(self):
        """Given an own, non-enumerable pushState set by the app before hello, when the bridge is disposed, then that same function returns as an own non-enumerable, writable, configurable property."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine)
                frame.evaluate("""() => { const native = history.pushState;
                    Object.defineProperty(history, 'pushState', {value: function (...a) { return native.apply(this, a); },
                        enumerable: false, configurable: true, writable: true});
                    window.appOwn = history.pushState; }""")
                self.hello(page)
                start = self.mark(page)
                frame.evaluate("history.pushState(null, '', '?route=own')")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=own'])
                frame.evaluate('__fontkitBridge.dispose()')
                state = frame.evaluate("""() => { const d = Object.getOwnPropertyDescriptor(history, 'pushState');
                    return {enumerable: d.enumerable, configurable: d.configurable, writable: d.writable, same: d.value === window.appOwn}; }""")
                self.assertEqual(state, {'enumerable': False, 'configurable': True, 'writable': True, 'same': True})

    def test_a_frozen_history_does_not_stop_the_ready(self):
        """Given Object.freeze(history), or a non-writable own pushState, before hello, when Studio says hello, then design:ready arrives, the other method is still announced when one is not frozen, and the page's pushState works."""
        setups = {
            'frozen history': "Object.freeze(history)",
            'non-writable pushState': "Object.defineProperty(history, 'pushState', {value: history.pushState, writable: false, configurable: false})",
        }
        for engine in ENGINES:
            for label, setup in setups.items():
                with self.subTest(engine=engine, setup=label):
                    page, frame = self.open(engine)
                    frame.evaluate(setup)
                    self.hello(page)
                    start = self.mark(page)
                    frame.evaluate("history.pushState(null, '', '?route=frozen')")
                    self.assertEqual(frame.evaluate('location.search'), '?route=frozen')
                    if label == 'non-writable pushState':
                        frame.evaluate("history.replaceState(null, '', '?route=still')")
                        self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=still'])

    def test_dispose_leaves_a_later_app_wrapper_in_place_and_it_still_forwards(self):
        """Given an app wrapper added after hello, when the bridge is disposed, then that wrapper stays, forwards to the bridge's wrapper and returns undefined, the URL changes, and no roles-page follows."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                frame.evaluate("history.pushState(null, '', '?route=one')")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=one'])
                frame.evaluate("""() => { const previous = history.pushState; window.calls = [];
                    history.pushState = function (...a) { window.calls.push(a[2]); return previous.apply(this, a); };
                    window.appWrapper = history.pushState; __fontkitBridge.dispose(); }""")
                mark = self.mark(page)
                result = frame.evaluate("""() => ({kept: history.pushState === window.appWrapper,
                    returned: history.pushState(null, '', '?route=two') === undefined, calls: window.calls, search: location.search,
                    replaceNative: history.replaceState === History.prototype.replaceState})""")
                self.assertEqual(result, {'kept': True, 'returned': True, 'calls': ['?route=two'], 'search': '?route=two', 'replaceNative': True})
                self.assertEqual(self.silence(page, mark), [])


class SessionAndDetectTests(RoleRouteCase):
    HELLO_S2 = """() => window.dispatchEvent(new MessageEvent('message', {
        data: {type: 'design:hello', protocolVersion: 1, sessionId: 's2'}, origin: 'http://studio.test', source: parent}))"""

    def s2_ready(self, page, start):
        page.wait_for_function("start => log.slice(start).some(e => e.data && e.data.type === 'design:ready' && e.data.sessionId === 's2')", arg=start)

    def test_a_push_announces_under_s1_and_one_made_just_before_s2_is_not_announced_again(self):
        """Given a push announced under s1, when another push and a new hello arrive in one task, then no roles-page carries s1 afterwards and none follows under s2 because the s2 ready carried that version."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("history.pushState(null, '', '?route=s1')")
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=s1'])
                page.evaluate("window.sessionId = 's2'")
                mark = self.mark(page)
                frame.evaluate("() => { history.pushState(null, '', '?route=s2'); (%s)(); }" % self.HELLO_S2)
                self.s2_ready(page, mark)
                self.assertEqual(self.silence(page, mark), [])
                self.assertEqual(page.evaluate("start => log.slice(start).filter(e => e.data && e.data.type === 'design:roles-page').length", mark), 0)

    def test_a_change_made_right_after_a_new_hello_is_announced_once_under_s2(self):
        """Given a push, a new hello and a DOM change in one task, when the page is quiet, then exactly one roles-page arrives under s2 with the pushed URL."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, _, start = self.start(engine)
                page.evaluate("window.sessionId = 's2'")
                frame.evaluate("""() => { history.pushState(null, '', '?route=lost'); (%s)();
                    document.querySelector('.body-copy').textContent = 'after hello'; }""" % self.HELLO_S2)
                self.s2_ready(page, start)
                self.assertEqual(self.urls(self.notices(page, start, settle=700)), [ROLE_PAGE + '?route=lost'])

    def test_a_push_inside_a_running_detect_leaves_the_stale_reply_and_adds_the_notice(self):
        """Given a push inside the page's design:detect listener, when the Detect replies, then it is incomplete as page-changed with the captured URL and the new current URL, one roles-page names the new URL, and a fresh Detect is complete on it."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame, ready, start = self.start(engine)
                frame.evaluate("""() => addEventListener('message', function change(event) {
                    if (event.data.type !== 'design:detect') return;
                    removeEventListener('message', change);
                    history.pushState(null, '', '?route=B');
                })""")
                reply = self.detect(page)
                self.assertEqual((reply['complete'], reply['reason']), (False, 'page-changed'), reply)
                self.assertEqual((reply['pageURL'], reply['currentPageURL']), (ROLE_PAGE, ROLE_PAGE + '?route=B'))
                self.assertEqual(self.urls(self.notices(page, start)), [ROLE_PAGE + '?route=B'])
                fresh = self.detect(page)
                self.assertEqual((fresh['complete'], fresh['pageURL']), (True, reply['currentPageURL']))

    def test_a_push_during_a_multi_slice_scan_keeps_the_stale_reply_and_sends_the_notice(self):
        """Given a Detect still scanning the 5,000-element page, when the page pushes a URL, then the stale page-changed reply still arrives, a roles-page names the new URL and a fresh Detect is complete there."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=LARGE)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                start = self.mark(page)
                page.evaluate('() => { window.pending6b1 = request({type: "design:detect"}); }')
                self.assertEqual(self.messages(page, 'design:detected', start), [])
                frame.evaluate("history.pushState(null, '', '?route=B')")
                reply = page.evaluate('() => window.pending6b1')
                self.assertEqual((reply['type'], reply['complete'], reply['reason']), ('design:detected', False, 'page-changed'), reply)
                self.assertEqual(self.urls(self.notices(page, start)), [LARGE + '?route=B'])
                fresh = self.detect(page)
                self.assertEqual((fresh['complete'], fresh['pageURL']), (True, reply['currentPageURL']))

    def test_a_detect_started_before_the_announcement_is_sent_finishes_complete_and_is_not_cancelled(self):
        """Given a DOM change made in the very task that delivers a Detect on a page of 9,000 text elements, when the roles-page is sent mid-scan, then the roles-page arrives before the Detect reply, the reply is complete with no reason and exactly one roles-page arrives carrying the Detect reply's pageVersion."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=LARGE)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                frame.evaluate("""() => { const host = document.createElement('div'); host.className = 'extra6b1';
                    for (let i = 0; i < 4000; i++) { const p = document.createElement('p'); p.textContent = 'extra ' + i; host.appendChild(p); }
                    document.body.appendChild(host); }""")
                page.wait_for_timeout(600)
                start = self.mark(page)
                message = page.evaluate("() => ({type: 'design:detect', protocolVersion: 1, sessionId: window.sessionId, requestId: 'role-6b1', documentId: window.roleState.documentId, knownRoles: []})")
                frame.evaluate("""async (data) => {
                    document.body.firstElementChild.setAttribute('data-t6b1', '1');
                    await Promise.resolve();
                    window.dispatchEvent(new MessageEvent('message', {data, origin: 'http://studio.test', source: parent}));
                }""", message)
                page.wait_for_function("start => log.slice(start).some(e => e.data && e.data.requestId === 'role-6b1')", arg=start, timeout=6000)
                reply = page.evaluate("start => log.slice(start).map(e => e.data).find(d => d && d.requestId === 'role-6b1')", start)
                self.assertEqual((reply['type'], reply['complete'], reply['reason']), ('design:detected', True, None), reply)
                notices = self.notices(page, start)
                order = page.evaluate("start => log.slice(start).map(e => e.data && e.data.type).filter(t => t === 'design:roles-page' || t === 'design:detected')", start)
                self.assertEqual(order, ['design:roles-page', 'design:detected'], 'the scan ended before the announcement was sent, so the test cannot tell a cancelled Detect from a finished one')
                self.assertEqual([m['pageVersion'] for m in notices], [reply['pageVersion']])

    def test_spa_clicks_announce_the_rendered_route_literals(self):
        """Given the SPA page in interact mode, when the detail, note and hash controls are clicked, then each click renders its literal heading and one roles-page names that click's URL."""
        clicks = [('#push-detail', 'SPA detail evidence', '?route=detail'), ('#replace-note', 'SPA NOTE EVIDENCE', '?route=note'),
                  ('#hash-section', 'section evidence', '?route=note#section')]
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page, frame = self.open(engine, target=SPA)
                self.hello(page)
                self.control(page, {'type': 'design:mode', 'mode': 'interact'})
                frame.wait_for_function("() => window.__fontkitBridge && window.__fontkitBridge.mode === 'interact'")
                for selector, heading, suffix in clicks:
                    with self.subTest(click=selector):
                        start = self.mark(page)
                        frame.locator(selector).click()
                        self.assertEqual(frame.locator('#route-content h1').inner_text(), heading)
                        self.assertEqual(self.urls(self.notices(page, start)), [SPA + suffix])
