// What the plugin and the proxy check on a page they are about to tag: a policy that would
// block the bridge, and a page that already loads its own copy of it. Nothing here changes
// a page or a header; it only decides whether to say something.

export const BRIDGE_TWICE_MESSAGE =
  'Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not connect, remove that script while you use npx fontkitstudio.';
export const CSP_MESSAGE =
  "Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the page's own scripts). Add 'self' to script-src while you develop.";

const SCRIPT_DIRECTIVES = ['script-src-elem', 'script-src', 'default-src'];

// One policy: the first of script-src-elem, script-src, default-src that it sets decides.
function policyBlocks(policy) {
  const directives = new Map();
  for (const part of policy.split(';')) {
    const [name, ...values] = part.trim().toLowerCase().split(/\s+/);
    if (name && !directives.has(name)) directives.set(name, values);
  }
  const key = SCRIPT_DIRECTIVES.find((name) => directives.has(name));
  if (key === undefined) return false;
  const values = directives.get(key);
  if (values.includes("'strict-dynamic'")) return true;
  return !values.some((value) => value === "'self'" || value === '*' || value === 'http:');
}

// policy: a header value (policies may be comma-separated) or a list of them. Several
// policies all apply, so one that blocks is enough.
export function blocksSameOriginScript(policy) {
  const list = Array.isArray(policy) ? policy : [policy];
  return list
    .filter((one) => typeof one === 'string')
    .flatMap((one) => one.split(','))
    .some(policyBlocks);
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
