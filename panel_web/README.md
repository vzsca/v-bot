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

Run `python -m panel_web.server` from the repository root. The default address is `http://127.0.0.1:8765`.

On first launch, a random token is stored in `panel_web/.token` and printed to the terminal. You can instead set `PANEL_WEB_TOKEN` in `.env`.

The server refuses non-loopback bind addresses for this initial implementation. Do not expose it through port forwarding or a reverse proxy yet.

## Next implementation areas

The panel will progressively cover bot lifecycle, server overview, logs, configuration, API access, announcements, owner controls, and other administrative operations while keeping the existing security and confirmation model.
