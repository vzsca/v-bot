# v-bot web panel

> Development feature for the `dev-panel` branch. Shared bot code is kept in sync with `main`; this document covers only the web-panel-specific setup and behavior.

The local web panel is a localhost-only administrative surface for v-bot.

## Start

Use the normal launcher:

- Windows: `start_bot.bat`
- Linux/macOS: `./start_bot.sh`

The launcher starts the web panel and the Discord bot in the same Python process so the web panel can directly manage the live bot instance.

Default URL:

`http://127.0.0.1:8765/panel_web/signin`

## Routes

- `/panel_web/signin`
- `/panel_web/dashboard`
- `/panel_web/instance`
- `/panel_web/activity`
- `/panel_web/logs`
- `/panel_web/manege` — server management equivalent to `v!servers`
- `/panel_web/security`
- `/panel_web/settings`

## Included administration features

- Bot start / stop / restart
- Runtime status, uptime, PID, CPU and RAM
- Bot and security logs
- Sensitive-action code generation
- Principal and secondary owner configuration
- Discord token replacement
- Prefix configuration
- Sensitive-command enable/disable
- Twitch and YouTube API credentials
- Shared moderation, security, and persistent warm-report functionality from the current bot code
- Server list and server details
- Per-server API access toggle
- Per-server invite generation
- Remove the bot from a server

The panel does not expose secret values through GET APIs. It is intentionally restricted to localhost and requires a session after token authentication. Keep it bound to loopback: do not expose port 8765 through port forwarding, a public reverse proxy, or an internet-facing tunnel. The GitHub Pages demo, if enabled, is simulated and does not control the live bot.
