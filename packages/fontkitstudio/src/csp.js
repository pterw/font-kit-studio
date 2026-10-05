// What the plugin and the proxy check on a page they are about to tag: a policy that would
// block the bridge, and a page that already loads its own copy of it. Nothing here changes
// a page or a header; it only decides whether to say something.

export const BRIDGE_TWICE_MESSAGE =
  'Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not connect, remove that script while you use npx fontkitstudio.';
export const CSP_MESSAGE =
  "Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the page's own scripts). Add 'self' to script-src while you develop.";

const SCRIPT_DIRECTIVES = ['script-src-elem', 'script-src', 'default-src'];
const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';
const HOST_SOURCE = /^(?:([a-z][a-z0-9+.-]*):\/\/)?(\[[^\]]+\]|[^:/\s]+)(?::(\d+|\*))?(\/\S*)?$/i;

// The page's own origin, when it is a plain http one; anything else gives nothing to match.
function parseOrigin(pageOrigin) {
  if (typeof pageOrigin !== 'string') return undefined;
  try {
    const url = new URL(pageOrigin);
    if (url.protocol !== 'http:') return undefined;
    return { host: url.hostname, port: url.port || '80' };
  } catch {
    return undefined;
  }
}

// Whether one host-source names the page's origin and the bridge's path. Scheme and host
// compare without case; the path keeps its case, as browsers compare it case-sensitively.
// Anything that does not parse, or that is not clearly the page's origin, does not match.
function sourceAllowsBridge(value, origin) {
  const found = HOST_SOURCE.exec(value);
  if (!found) return false;
  const [, rawScheme, rawHost, port = '80', path] = found;
  const scheme = rawScheme?.toLowerCase();
  const host = rawHost.toLowerCase();
  if (scheme !== undefined && scheme !== 'http') return false;
  if (host !== origin.host) return false;
  if (port !== '*' && port !== origin.port) return false;
  if (path === undefined || path === '') return true;
  return path.endsWith('/') ? BRIDGE_PATH.startsWith(path) : path === BRIDGE_PATH;
}

// One policy: the first of script-src-elem, script-src, default-src that it sets decides.
function policyBlocks(policy, origin) {
  const directives = new Map();
  for (const part of policy.split(';')) {
    const [name, ...values] = part.trim().split(/\s+/);
    if (name && !directives.has(name.toLowerCase())) directives.set(name.toLowerCase(), values);
  }
  const key = SCRIPT_DIRECTIVES.find((name) => directives.has(name));
  if (key === undefined) return false;
  const values = directives.get(key);
  if (values.some((value) => value.toLowerCase() === "'strict-dynamic'")) return true;
  return !values.some(
    (value) =>
      ["'self'", '*', 'http:'].includes(value.toLowerCase()) ||
      (origin !== undefined && sourceAllowsBridge(value, origin)),
  );
}

// policy: a header value (policies may be comma-separated) or a list of them. Several
// policies all apply, so one that blocks is enough. pageOrigin (optional, such as
// 'http://localhost:5173'): a source that names it also allows the bridge.
export function blocksSameOriginScript(policy, pageOrigin) {
  const origin = parseOrigin(pageOrigin);
  const list = Array.isArray(policy) ? policy : [policy];
  return list
    .filter((one) => typeof one === 'string')
    .flatMap((one) => one.split(','))
    .some((one) => policyBlocks(one, origin));
}

function attribute(tag, name) {
  const pattern = String.raw`\s${name}\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))`;
  const found = new RegExp(pattern, 'i').exec(tag);
  return found ? (found[1] ?? found[2] ?? found[3]) : undefined;
}

// The content of every <meta http-equiv="Content-Security-Policy"> in a page.
export function metaPolicies(html) {
  if (typeof html !== 'string') return [];
  const policies = [];
  for (const [tag] of html.matchAll(/<meta\b[^>]*>/gi)) {
    if (attribute(tag, 'http-equiv')?.trim().toLowerCase() !== 'content-security-policy') continue;
    const content = attribute(tag, 'content');
    if (content !== undefined) policies.push(content);
  }
  return policies;
}

// Whether the page already has a <script src> that names fontkit-bridge.
export function loadsOwnBridge(html) {
  if (typeof html !== 'string') return false;
  for (const [tag] of html.matchAll(/<script\b[^>]*>/gi)) {
    if (attribute(tag, 'src')?.toLowerCase().includes('fontkit-bridge')) return true;
  }
  return false;
}
