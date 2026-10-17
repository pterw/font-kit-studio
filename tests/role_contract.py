"""The R2 role protocol's limits, enums and shapes, written once for the tests of both sides.

Every value comes from the plan's binding contract and Addenda 13-18 (17: template bytes; 18: signatures per check), 20
and 22 (families) (docs/plans/2026-10-03-r2-engine.md) and, where the
plan is silent, from the R2.5 brief (docs/implementation/tasks/r2-task-5-brief.md: pins and additions), the PR B fix brief
(r2-task-bfix-brief.md) and the PR B review (r2-pr-b-review.md). None comes from fontkit-bridge.js or fontkit-studio.html:
a test that reads this table checks a side against the contract, not against itself. A later change to a field, limit or
enum updates this table first, in the task the plan names. Lengths are UTF-16 code units, as the contract's strings are.
Tests import it as `import role_contract as table`.
"""
import json
import re
from urllib.parse import urlsplit

ROLES = 128                          # role/group count per scan and request, and in the session collection (limits table)
SELECTORS = 32                       # selectors per role (limits table)
SELECTOR_CHARS = 2000                # selector length (limits table)
NTH_MAX = 9999                       # :nth-of-type(n) is 1-9,999 (selector validation)
ROLE_ID_CHARS, NAME_CHARS = 100, 200  # role and group ids; label, suggested name and author-role name (limits table)
SAMPLE_CHARS, SHARED_CLASSES, CLASS_CHARS = 200, 16, 200   # sample text; shared classes (limits table)
VARIANTS = 8                         # signature variants per author role (limits table)
NEAR_DUPLICATES = ROLES - 1          # other groups in one reply (role identity algorithm)
CHECK_SIGNATURES = ROLES * VARIANTS  # style signatures per SelectorCheck (D070, Addendum 18); Studio accepts the same bound (R2.S3)
SELECTOR_CHECKS = ROLES * SELECTORS  # one check per known selector, at most 128 roles x 32 (Detect request)
ELEMENTS = 10000                     # detected text elements: scannedElements of a complete reply (limits table)
ELEMENTS_INCOMPLETE = ELEMENTS + 1   # scannedElements of an incomplete reply: element-limit reports the first element past it
TIME_BUDGET_MS = 2000                # elapsedMs of a complete reply (detection and performance)
CHECKED = 10000                      # checked per outcome (R2.5 pin 1); matched has no cap; a loss count is at most CHECKED
LOSSES_PER_PROPERTY, LOSSES = 16, 96  # loss groups per role and property; per outcome, 6 x 16 (R2.5 pin 6, PR B review F2)
WINNING_SELECTOR_CHARS = 2000        # winningSelector, no C0, DEL, C1, U+2028 or U+2029 character (R2.5 additions, F4)
REQUEST_ID_CHARS = DOCUMENT_ID_CHARS = 200   # requestId, documentId (envelope)
ROUTE_CHARS = 2000                   # route text: path, search and hash (route observation)
FAMILY_CHARS = 300                   # a trimmed RoleInput family (value validation)
REQUEST_BYTES, REPLY_BYTES, CSS_BYTES = 256 * 1024, 1024 * 1024, 128 * 1024   # UTF-8 JSON request and reply; canonical CSS
EMPTY_HASH = '811c9dc5'              # FNV-1a32 of the empty string

CASES = ('none', 'uppercase', 'lowercase', 'capitalize')                       # type Case
ADAPTERS = ('plain', 'bootstrap5-body', 'bootstrap5-mono', 'bootstrap5-heading')   # RoleInput.adapter
BINDING_REASONS = ('author-role', 'author-id', 'class', 'css-module', 'dom-path')  # SelectorBinding.reason
STABLE_REASONS = ('author-role', 'author-id', 'class')                         # a binding is stable exactly when its reason is one
LOSS_REASONS = ('author-rule', 'inline', 'inherited', 'unreadable-sheet', 'complex-cascade', 'stylesheet-blocked',
                'budget-exceeded')                                              # RoleOutcome loss reasons, in the contract's order
OUTCOME_REASONS = (None, 'page-changed', 'budget-exceeded')                    # roles-applied outcomeReason
DETECT_REASONS = ('time-budget', 'element-limit', 'group-limit', 'variant-limit', 'identity-limit', 'reply-limit',
                  'page-changed')                                               # an incomplete scan's seven reasons
REJECTION_REASONS = ('invalid-message', 'unsupported-value', 'revision-conflict', 'page-changed', 'stylesheet-blocked',
                     'size-limit')                                              # design:rejected for a role request
PROPERTY_ORDER = ('fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textTransform')   # canonical CSS order
# RoleInput properties only (requests, receipt roles, role state): (min, max, decimals). An observed StyleSignature family
# is unbounded and its measured size only nonnegative.
NUMBER_RULES = {'fontSize': (4, 400, 2), 'fontWeight': (1, 1000, 0), 'lineHeight': (0.5, 5, 3), 'letterSpacing': (-0.5, 2, 4)}

# Addendum 22 item 1 (D072), written from the contract text: a trimmed family that is exactly a CSS-wide keyword (any case) or
# holds ( or ) outside quotes is refused. "Outside quotes": one pass, " or ' opens a quote, only the same character closes it,
# no escapes (a backslash is refused elsewhere); a parenthesis counts only when no quote is open.
FAMILY_KEYWORDS = ('inherit', 'initial', 'unset', 'revert', 'revert-layer')
FAMILIES_REFUSED = (
    # keywords: both CSS engines accept all of these and a sheet would carry them, so only the rule refuses them
    'inherit', 'initial', 'unset', 'revert', 'revert-layer', 'INHERIT', 'Revert-Layer', '  inherit  ',
    # dashed functions: Chromium accepts them in CSS.supports (the case for killing a mutant there); Firefox already refuses them
    '--x(', '--x(a)', '--x()', 'Inter, --x(', 'if(media(all): Inter', '"Inter", --x(a)', '--x("a")',
    # table-only: CSS.supports already refuses these in both engines, so never use generic(kai) to kill a mutant; a lone ) is table-only
    'generic(kai)', 'Inter)', 'a), serif', 'Inter (Display)',
)
FAMILIES_ACCEPTED = (   # near misses that must still pass: quoted keywords and parentheses, longer words, one-pass quote scans
    '"inherit"', "'Inter (Display)'", '"Inter (Display)"', 'Initialism, serif', 'Inherit Sans', 'inherited', 'revert-layers',
    '"A)"', '"Inter\'s (x)"', '\'say "hi" (x)\'',
)

# Table names whose limit the real-bridge class (RoleContractTableTests) does not build, with where the bridge side is pinned.
STUDIO_SIDE_ONLY = {
    'ELEMENTS': 'a 10,000-element page: test_role_detection pins the bridge at 10,000 and 10,001',
    'ELEMENTS_INCOMPLETE': 'a 10,001-element page: test_role_detection pins element-limit at 10,001',
    'NTH_MAX': 'a dom path 9,999 siblings deep needs a 10,000-element page; test_role_stylesheet pins apply at 9,999 and 10,000',
    'CHECKED': 'a 10,000-element match: test_role_preview pins the bridge cap',
    'WINNING_SELECTOR_CHARS': 'a 2,000-character author selector: test_role_preview',
    'NUMBER_RULES': 'the minima 4, 1, 0.5 and -0.5: the bridge class builds only the maxima; test_role_stylesheet pins the bridge number ranges',
    'EMPTY_HASH': 'an empty role state: the bridge class checks the role state only after an apply; test_role_protocol pins the empty digest',
    'DOCUMENT_ID_CHARS': 'the bridge makes a short documentId; only a Studio-side reply carries 200 characters',
    'ROUTE_CHARS': 'a 2,000-character route: test_role_protocol pins 2,000 and 2,001 on the bridge',
    'REQUEST_BYTES': 'the exact 256 KiB boundary is pinned on neither side; the bridge is pinned over it, and Studio refuses a few bytes earlier',
    'REPLY_BYTES': 'the exact 1 MiB boundary: test_role_protocol.RoleProtocolTests pins the bridge reply near it',
    'CSS_BYTES': 'the exact 128 KiB boundary: test_role_stylesheet pins the bridge at 128 KiB and one byte more',
}


def fnv1a32(text):
    """The contract's digest: FNV-1a over the UTF-8 bytes (offset 2166136261, multiplier 16777619, modulo 2^32), eight hex digits."""
    value = 2166136261
    for byte in text.encode('utf-8'):
        value = ((value ^ byte) * 16777619) % 2 ** 32
    return f'{value:08x}'


def family_refused(value):
    """Whether the contract refuses the family: a trimmed CSS-wide keyword (any case) or a parenthesis outside quotes."""
    if value.strip().lower() in FAMILY_KEYWORDS:
        return True
    quote = None
    for char in value:
        if quote:
            quote = None if char == quote else quote
        elif char in ('"', "'"):
            quote = char
        elif char in '()':
            return True
    return False


def text(length, prefix='t'):
    """`prefix` padded with 'a' to exactly `length` characters."""
    return prefix[:length].ljust(length, 'a')


def class_selector(length):
    """A valid role selector of exactly `length` characters."""
    return '.' + 'a' * (length - 1)


def selectors(count):
    """`count` distinct valid class selectors."""
    return [f'.s{index}' for index in range(count)]


def class_names(count, length):
    """`count` distinct class names of exactly `length` characters."""
    return [text(length, f'c{index}') for index in range(count)]


def styles(count):
    """`count` distinct valid StyleSignature dicts."""
    return [{'fontFamily': 'sans-serif', 'fontSize': 10 + index, 'fontWeight': 400, 'textTransform': 'none', 'letterSpacing': 0}
            for index in range(count)]


def losses(per_property):
    """`per_property` author-rule losses (count 1, distinct winning selectors) for each property, in the contract's loss order."""
    return [{'property': prop, 'count': 1, 'winningSelector': f'.w{index:02d}', 'reason': 'author-rule'}
            for prop in PROPERTY_ORDER for index in range(per_property)]


def wire(message):
    """The UTF-8 bytes of the message as posted."""
    return len(json.dumps(message, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def violations(kind, message):
    """One string per value of `message` outside the table, for kind 'detected', 'roles-applied', 'rejected' or 'role-state'.

    It checks counts, lengths (UTF-16 units), bytes, enums, number ranges, families, the stable/reason rule and the contract's
    invariants. It does not compare key sets: both sides already validate exact field lists, so a missing field raises KeyError,
    except a group's `adapter` (read with `get`: a missing one is a violation like a wrong one).
    """
    if kind not in ('detected', 'roles-applied', 'rejected', 'role-state'):
        raise ValueError(f'unknown kind {kind!r}')
    found = []

    def need(ok, what):
        if not ok:
            found.append(what)

    def chars(value, high, what, low=1):
        units = sum(2 if ord(char) > 0xFFFF else 1 for char in value) if isinstance(value, str) else None
        need(units is not None and low <= units <= high, f'{what}: {value!r} has {units} UTF-16 units')

    def count(value, high, what, low=0):
        need(isinstance(value, int) and not isinstance(value, bool) and low <= value <= high, f'{what}: {value!r}')

    def selector(value, what):
        chars(value, SELECTOR_CHARS, what)
        for number in re.findall(r':nth-of-type\((\d+)\)', str(value)):
            count(int(number), NTH_MAX, f'{what} nth-of-type', low=1)

    def variants(items, total, high, what):
        count(len(items), high, f'{what} signatures')
        need(sum(item['count'] for item in items) == total, f'{what} counts do not sum to {total}')
        for item in items:
            need(item['style']['textTransform'] in CASES and item['style']['fontSize'] >= 0, f'{what} style: {item["style"]!r}')

    def roles_part():
        roles, css = message['roles'], message['canonicalCss']
        count(len(roles), ROLES, 'roles')
        need(len({role['id'] for role in roles}) == len(roles), 'role ids are not unique')
        for role in roles:
            chars(role['id'], ROLE_ID_CHARS, 'role id')
            chars(role['name'], NAME_CHARS, 'role name')
            need(role['adapter'] in ADAPTERS, f'adapter: {role["adapter"]!r}')
            count(len(role['selectors']), SELECTORS, 'role selectors', low=1)
            for value in role['selectors']:
                selector(value, 'role selector')
            for key, value in role['properties'].items():
                need(key in PROPERTY_ORDER, f'property {key!r}')
                if key == 'fontFamily':
                    chars(value, FAMILY_CHARS, 'family')
                    need(not isinstance(value, str) or not family_refused(value), f'family: {value!r} is a CSS-wide keyword or holds a parenthesis')
                elif key == 'textTransform':
                    need(value in CASES, f'textTransform: {value!r}')
                elif key in NUMBER_RULES:
                    low, high, places = NUMBER_RULES[key]
                    need(isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high and round(value, places) == value,
                         f'{key}: {value!r} outside {low}..{high} with {places} decimals')
        count(len(css.encode('utf-8')), CSS_BYTES, 'canonicalCss bytes')
        need(bool(roles) or (css == '' and message['cssHash'] == EMPTY_HASH), 'no roles must mean no CSS and the empty digest')

    count(wire(message), REPLY_BYTES, 'message bytes')
    for key, high in (('requestId', REQUEST_ID_CHARS), ('documentId', DOCUMENT_ID_CHARS)):
        if key in message:
            chars(message[key], high, key)
    for key in ('pageURL', 'currentPageURL'):
        if message.get(key) is not None:
            parts = urlsplit(message[key])
            chars(parts.path + ('?' + parts.query if parts.query else '') + ('#' + parts.fragment if parts.fragment else ''),
                  ROUTE_CHARS, f'{key} route', low=0)
    if kind == 'detected':
        need(message['reason'] in DETECT_REASONS + (None,), f'reason: {message["reason"]!r}')
        need(message['complete'] == (message['reason'] is None), 'complete must mean no reason')
        count(message['scannedElements'], ELEMENTS if message['complete'] else ELEMENTS_INCOMPLETE, 'scannedElements')
        need(not message['complete'] or 0 <= message['elapsedMs'] <= TIME_BUDGET_MS, f'elapsedMs: {message["elapsedMs"]!r}')
        ids = [group['id'] for group in message['groups']]
        count(len(ids), ROLES, 'groups')
        need(len(set(ids)) == len(ids), 'group ids are not unique')
        count(len(message['selectorChecks']), SELECTOR_CHECKS, 'selectorChecks')
        for group in message['groups']:
            chars(group['id'], ROLE_ID_CHARS, 'group id')
            need(group.get('adapter') in ADAPTERS, f'group adapter: {group.get("adapter")!r}')
            chars(group['suggestedName'], NAME_CHARS, 'suggestedName')
            if group['authorRole'] is not None:
                chars(group['authorRole'], NAME_CHARS, 'authorRole')
            chars(group['sampleText'], SAMPLE_CHARS, 'sampleText', low=0)
            count(len(group['sharedClasses']), SHARED_CLASSES, 'sharedClasses')
            for name in group['sharedClasses']:
                chars(name, CLASS_CHARS, 'shared class')
            count(len(group['selectors']), SELECTORS, 'group selectors')
            for binding in group['selectors']:
                selector(binding['value'], 'binding')
                need(binding['reason'] in BINDING_REASONS, f'binding reason: {binding["reason"]!r}')
                need(binding['reason'] not in BINDING_REASONS or binding['stable'] == (binding['reason'] in STABLE_REASONS),
                     f'binding {binding["reason"]!r} stable: {binding["stable"]!r}')
            variants(group['signatures'], group['elementCount'], VARIANTS, 'group variants')
            near = group['nearDuplicateIds']
            need(len(set(near)) == len(near), f'nearDuplicateIds of {group["id"]!r} repeat an id')
            need(all(other != group['id'] and other in ids for other in near), f'nearDuplicateIds of {group["id"]!r} name a group outside the reply')
        for check in message['selectorChecks']:
            chars(check['roleId'], ROLE_ID_CHARS, 'check roleId')
            selector(check['selector'], 'check selector')
            variants(check['signatures'], check['matchCount'], CHECK_SIGNATURES, 'check')
    elif kind == 'roles-applied':
        roles_part()
        need(message['outcomeReason'] in OUTCOME_REASONS, f'outcomeReason: {message["outcomeReason"]!r}')
        need(message['outcomesComplete'] == (message['outcomeReason'] is None), 'outcomesComplete must mean no reason')
        count(len(message['outcomes']), ROLES, 'outcomes')
        for item in message['outcomes']:
            need(0 <= item['mismatched'] <= item['checked'] <= item['matched'], f'outcome counts: {item["id"]!r}')
            count(item['checked'], CHECKED, 'checked')
            for prop in PROPERTY_ORDER:
                count(sum(1 for entry in item['losses'] if entry['property'] == prop), LOSSES_PER_PROPERTY, f'losses for {prop}')
            for entry in item['losses']:
                need(entry['property'] in PROPERTY_ORDER and entry['reason'] in LOSS_REASONS, f'loss: {entry["property"]!r} {entry["reason"]!r}')
                count(entry['count'], CHECKED, 'loss count', low=1)
                if entry['winningSelector'] is not None:
                    chars(entry['winningSelector'], WINNING_SELECTOR_CHARS, 'winningSelector')
                    need(not any(ord(c) < 0x20 or 0x7f <= ord(c) <= 0x9f or ord(c) in (0x2028, 0x2029) for c in entry['winningSelector']),
                         'winningSelector has a control character')
    elif kind == 'role-state':
        roles_part()
    else:
        need(message['reason'] in REJECTION_REASONS, f'reason: {message["reason"]!r}')
        detail = message.get('detail')
        conflict = message['reason'] == 'revision-conflict' and isinstance(detail, dict) and set(detail) == {'baseRevision', 'revision'}
        need('detail' not in message or isinstance(detail, str) or conflict and all(isinstance(v, int) and v >= 0 for v in detail.values()),
             f'detail: {detail!r}')
    return found


def _role(number, name, adapter, targets, **properties):
    return {'id': f'role-{number}', 'name': name, 'selectors': targets, 'adapter': adapter, 'properties': properties}


# Addendum 17 item 1, written out from its rules and never produced by code: a body or mono role that sets a family emits
# a :root block of its variables before its plain block; every role emits its own blocks in request order; blocks never merge.
TEMPLATE_CASES = (
    {'name': 'body', 'roles': [_role(1, 'Body', 'bootstrap5-body', ['.btn', '.nav-link'], fontFamily='Inter', fontSize=18)],
     'css': ':root {\n  --bs-body-font-family: Inter;\n  --bs-font-sans-serif: Inter;\n}\n.btn, .nav-link {\n  font-family: Inter;\n  font-size: 18px;\n}\n',
     'hash': 'bf7cd581'},
    {'name': 'mono', 'roles': [_role(1, 'Mono', 'bootstrap5-mono', ['code'], fontFamily='"JetBrains Mono"')],
     'css': ':root {\n  --bs-font-monospace: "JetBrains Mono";\n}\ncode {\n  font-family: "JetBrains Mono";\n}\n', 'hash': '3842c27b'},
    {'name': 'body-without-family', 'roles': [_role(1, 'Body', 'bootstrap5-body', ['.btn', '.nav-link'], fontWeight=500)],
     'css': '.btn, .nav-link {\n  font-weight: 500;\n}\n', 'hash': 'a06c14e7'},
    {'name': 'heading', 'roles': [_role(1, 'Heading', 'bootstrap5-heading', ['h2', '.h2'], fontFamily='Fraunces', fontSize=32)],
     'css': 'h2, .h2 {\n  font-family: Fraunces;\n  font-size: 32px;\n}\n', 'hash': 'b623dd3c'},
    {'name': 'mixed', 'roles': [_role(1, 'Lead', 'plain', ['.lead'], fontSize=20),
                                _role(2, 'Body', 'bootstrap5-body', ['.btn', '.nav-link'], fontFamily='Inter', fontSize=18),
                                _role(3, 'Mono', 'bootstrap5-mono', ['code'], fontFamily='"JetBrains Mono"'),
                                _role(4, 'Heading', 'bootstrap5-heading', ['h2', '.h2'], fontFamily='Fraunces', fontSize=32)],
     'css': ('.lead {\n  font-size: 20px;\n}\n'
             ':root {\n  --bs-body-font-family: Inter;\n  --bs-font-sans-serif: Inter;\n}\n.btn, .nav-link {\n  font-family: Inter;\n  font-size: 18px;\n}\n'
             ':root {\n  --bs-font-monospace: "JetBrains Mono";\n}\ncode {\n  font-family: "JetBrains Mono";\n}\n'
             'h2, .h2 {\n  font-family: Fraunces;\n  font-size: 32px;\n}\n'),
     'hash': '9672a774'},
)
