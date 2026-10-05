import { describe, test } from 'node:test';
import assert from 'node:assert/strict';

import {
  BRIDGE_TWICE_MESSAGE,
  CSP_MESSAGE,
  blocksSameOriginScript,
  loadsOwnBridge,
  metaPolicies,
} from '../src/csp.js';

describe('blocksSameOriginScript', () => {
  const cases = [
    ["script-src 'self'", false],
    ["default-src 'self'", false],
    ["script-src 'nonce-x'", true],
    ["script-src 'self' 'strict-dynamic'", true],
    ["default-src 'none'", true],
    ["script-src-elem 'self'; script-src 'none'", false],
    ["script-src-elem 'none'; script-src 'self'", true],
    ["script-src 'none'; default-src 'self'", true],
    ["style-src 'none'", false],
    ["img-src 'none'; default-src 'self'", false],
    ['', false],
    ['   ', false],
    ['script-src *', false],
    ['script-src http:', false],
    ['script-src https:', true],
    ["script-src 'self'; script-src 'none'", false],
    ["SCRIPT-SRC 'SELF'", false],
    ["Script-Src 'Nonce-x' 'STRICT-DYNAMIC'", true],
    ["script-src 'self', script-src 'none'", true],
    ["script-src 'self', style-src 'none'", false],
  ];
  for (const [policy, blocked] of cases) {
    test(`${JSON.stringify(policy)} -> ${blocked}`, () => {
      assert.equal(blocksSameOriginScript(policy), blocked);
    });
  }

  test('a list of policies blocks when any one blocks', () => {
    assert.equal(blocksSameOriginScript(["script-src 'self'", "script-src 'nonce-x'"]), true);
    assert.equal(blocksSameOriginScript(["script-src 'self'", "default-src 'self'"]), false);
    assert.equal(blocksSameOriginScript([]), false);
  });

  test('anything that is not text or a list does not block', () => {
    for (const value of [undefined, null, 5]) assert.equal(blocksSameOriginScript(value), false);
  });
});

describe('blocksSameOriginScript with the page origin', () => {
  const ORIGIN = 'http://localhost:5173';
  const allows = [
    'script-src http://localhost:5173',
    'script-src localhost:5173',
    'script-src HTTP://LOCALHOST:5173',
    'script-src http://localhost:*',
    'script-src localhost:*',
    'script-src http://localhost:5173/',
    'script-src http://localhost:5173/@fontkit/',
    'script-src localhost:5173/@fontkit/fontkit-bridge.js',
    "script-src-elem localhost:5173; script-src 'none'",
    "default-src 'none'; script-src 'nonce-q' localhost:5173",
  ];
  for (const policy of allows) {
    test(`allows ${JSON.stringify(policy)}`, () => {
      assert.equal(blocksSameOriginScript(policy, ORIGIN), false);
    });
  }

  const blocks = [
    'script-src http://localhost:5174',
    'script-src localhost',
    'script-src http://127.0.0.1:5173',
    'script-src https://localhost:5173',
    'script-src https://localhost:*',
    'script-src localhost:5173/js/',
    'script-src localhost:5173/@fontkit/other.js',
    'script-src localhost:5173/@fontkit',
    'script-src localhost:5173/@FONTKIT/',
    'script-src localhost:5173/@fontkit/Fontkit-Bridge.js',
    'script-src *.localhost:5173',
    'script-src *.localhost',
    'script-src',
    'script-src ;;',
    "script-src 'strict-dynamic' localhost:5173",
    'script-src http://:5173',
    'script-src localhost:abc',
    'script-src ://localhost:5173',
    'script-src https:',
    "script-src-elem 'none'; script-src localhost:5173",
  ];
  for (const policy of blocks) {
    test(`blocks ${JSON.stringify(policy)}`, () => {
      assert.equal(blocksSameOriginScript(policy, ORIGIN), true);
    });
  }

  test('two policies: the second blocks', () => {
    assert.equal(
      blocksSameOriginScript("script-src localhost:5173, script-src 'nonce-q'", ORIGIN),
      true,
    );
    assert.equal(blocksSameOriginScript(['script-src localhost:5173', "script-src 'none'"], ORIGIN), true);
    assert.equal(blocksSameOriginScript(['script-src localhost:5173', 'script-src localhost:*'], ORIGIN), false);
  });

  test('a source for the default port matches a page without a port, and only that', () => {
    assert.equal(blocksSameOriginScript('script-src localhost:80', 'http://localhost'), false);
    assert.equal(blocksSameOriginScript('script-src localhost', 'http://localhost'), false);
    assert.equal(blocksSameOriginScript('script-src localhost:80', ORIGIN), true);
  });

  test('IPv6 loopback matches by name, and not the other loopbacks', () => {
    assert.equal(blocksSameOriginScript('script-src [::1]:5173', 'http://[::1]:5173'), false);
    assert.equal(blocksSameOriginScript('script-src localhost:5173', 'http://[::1]:5173'), true);
  });

  test('without an origin, or with an unusable one, only self, * and http: allow', () => {
    for (const origin of [undefined, 'nonsense', 'https://localhost:5173', 5]) {
      assert.equal(blocksSameOriginScript('script-src localhost:5173', origin), true);
      assert.equal(blocksSameOriginScript("script-src 'self'", origin), false);
    }
  });
});

describe('metaPolicies', () => {
  test('reads Content-Security-Policy meta tags only, in any case and quoting', () => {
    const html = [
      `<meta http-equiv="Content-Security-Policy" content="script-src 'self'">`,
      `<META CONTENT="default-src 'none'" HTTP-EQUIV='content-security-policy'>`,
      `<meta http-equiv="Content-Security-Policy-Report-Only" content="default-src 'none'">`,
      `<meta http-equiv="refresh" content="5">`,
      `<meta name="x" content="script-src 'none'">`,
    ].join('\n');
    assert.deepEqual(metaPolicies(html), ["script-src 'self'", "default-src 'none'"]);
  });

  test('a page without such a tag, or a non-string, yields nothing', () => {
    assert.deepEqual(metaPolicies('<p>hi</p>'), []);
    assert.deepEqual(metaPolicies(undefined), []);
  });
});

describe('loadsOwnBridge', () => {
  test('finds a script whose src names fontkit-bridge', () => {
    for (const html of [
      '<script src="/vendor/fontkit-bridge.js"></script>',
      "<SCRIPT async src='https://x.test/fontkit-bridge.min.js'>",
      '<script src=fontkit-bridge.js></script>',
      '<script\n  type="module"\n  src = "./fontkit-bridge.js?v=2"></script>',
    ]) {
      assert.equal(loadsOwnBridge(html), true, html);
    }
  });

  test('ignores other scripts, text and non-strings', () => {
    for (const html of [
      '<script src="/app.js"></script>',
      '<script>var s = "fontkit-bridge.js";</script>',
      '<p>fontkit-bridge.js</p>',
      '<link href="fontkit-bridge.js">',
      undefined,
    ]) {
      assert.equal(loadsOwnBridge(html), false, String(html));
    }
  });
});

test('the messages are the exact texts', () => {
  assert.equal(
    BRIDGE_TWICE_MESSAGE,
    'Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not connect, remove that script while you use npx fontkitstudio.',
  );
  assert.equal(
    CSP_MESSAGE,
    "Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the page's own scripts). Add 'self' to script-src while you develop.",
  );
});
