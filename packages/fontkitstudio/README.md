# fontkitstudio

Font Kit Studio lets you try type on your own running web app, in development only. Change fonts, sizes, colours and layout in the live page, then copy the CSS and HTML.

## Use it

In a Vite project (Vite 7 or 8), from the project folder:

```bash
npx fontkitstudio
```

In front of any other local dev server, such as Next.js:

```bash
npx fontkitstudio http://localhost:3000
```

For a permanent setup, add the plugin to `vite.config`:

```js
import { fontkitStudio } from 'fontkitstudio/vite'

export default { plugins: [fontkitStudio()] }
```

The command opens Studio in your browser and prints its address on a line that starts with `Open:`. Nothing is written to your project.

| Flag | What it does |
|---|---|
| `--no-open` | Print the address instead of opening the browser. |
| `--studio-port <n>` | Keep Studio on one port, so its settings stay. |

## Requirements

- Node 22.12 or later.
- Vite 7 or 8 in Vite mode.
- Proxy mode accepts only an `http:` address on `localhost`, `127.0.0.1` or `[::1]`.

## If Studio does not connect

The terminal where the command runs says what it found: a page that loads its own `fontkit-bridge.js`, a Content-Security-Policy that blocks the bridge, or an address that is not local. The [repository README](https://github.com/pterw/font-kit-studio#if-studio-does-not-connect) lists each one.

## Cookies and storage

Studio and the proxy use `localhost` for localhost apps and `127.0.0.1` for IP targets. Sign in using the same host name you give the command. Cookies ignore ports; the proxy passes `Set-Cookie` through unchanged. IPv6 `[::1]` targets still use IPv4 Studio/proxy addresses, so their same-site cookies can be missing.

Proxy mode gives the app a random proxy port each run. Its localStorage, sessionStorage, IndexedDB and service workers start separate from its usual origin. Vite mode keeps the app's own origin and storage.

Studio's settings belong to its own host and port. `--studio-port` keeps the port unless it is busy. Users of a localhost app with that flag in 0.3.0 start fresh once in 0.3.1 because Studio's host changes; without the flag its port was already random each run.

Vite config changes restart Studio in both command and plugin mode. Open the latest `Open:` URL printed in the terminal. A pinned port keeps settings when the host stays the same and the port is available.

## Sync to file

The npm command does not serve Sync to file, and Studio says so. Use Copy or Download in Studio, or run the repository's dev server (`python scripts/serve.py`) to write a stylesheet.

## The name

`fontkit-bridge.js` belongs to Font Kit Studio. It is not part of, and has no relation to, the `fontkit` font engine on npm.

See the [repository README](https://github.com/pterw/font-kit-studio#readme) for what Font Kit Studio does and how to use it.
