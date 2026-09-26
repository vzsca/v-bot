# v-bot Web Panel

The dev-panel branch now contains the first local web-panel implementation.

## Current scope

- localhost-only aiohttp server
- token authentication with an HttpOnly session cookie
- bot status endpoint
- recent bot-log viewer
- action-specific one-time security-code generation
- small responsive dashboard

## Start

Use `start_bot.bat` on Windows or `./start_bot.sh` on Linux/macOS. The launcher starts both the Discord bot and the web panel. The default address is `http://127.0.0.1:8765/panel_web/signin`.

On first launch, a random token is stored in `panel_web/.token` and printed to the terminal. You can instead set `PANEL_WEB_TOKEN` in `.env`.

The server refuses non-loopback bind addresses for this initial implementation. Do not expose it through port forwarding or a reverse proxy yet.

## Next implementation areas

The panel will progressively cover bot lifecycle, server overview, logs, configuration, API access, announcements, owner controls, and other administrative operations while keeping the existing security and confirmation model.


## GitHub Pages demo

A public simulated version of the panel is available here:

**Demo panel:** https://vzsca.github.io/v-bot/panel_web/

**Demo token:**
```text
vbot-demo-token
```

When opened from `vzsca.github.io`, the frontend automatically enters demo mode. Status, logs, and security-code generation are simulated entirely in the browser; no request is sent to the real bot and no Discord action is executed. The demo token is fake and has no access to the real bot. The real local panel keeps using its actual token and API.


## Page routes

The panel uses a dedicated `/panel_web` namespace:

- `/panel_web/signin`
- `/panel_web/dashboard`
- `/panel_web/instance`
- `/panel_web/activity`
- `/panel_web/logs`
- `/panel_web/security`
