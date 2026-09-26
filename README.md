# 🤖 v-bot

A Discord bot built with **Python and discord.py**, focused on moderation, server management, Twitch/YouTube announcements, and secure administration.

The project targets Windows, Linux, and macOS.

## ✨ Features

- 🛡️ Moderation and server-management commands
- 👑 Permanent owners and temporary server-scoped authorizations
- 🔐 Persistent kill switch and disabled-server state
- 🧹 Deleted-message snipe support
- 📢 Twitch and YouTube announcements
- 🔑 Global primary API + per-server API credentials
- 🚦 Global/per-user/per-command rate limiting
- 🛡️ Anti-spam and anti-raid detection
- 📋 Standard and security logs with audit events
- 🔐 Sensitive commands disabled by default
- 🔑 One-time 6-digit security codes bound to a specific sensitive action
- 🧩 Modular Cogs and application modules
- 📚 Permission-aware help system
- 💬 Permission-aware bot mention responses
- 🌐 Local web control panel

## 🚀 Installation

### Requirements

- Windows, Linux, or macOS
- Python **3.13**
- A Discord application/bot with the required intents enabled

```text
git clone https://github.com/vzsca/v-bot.git
cd v-bot
```

Create `.env` from `.env.example` and configure at least:

```env
DISCORD_TOKEN=YOUR_TOKEN
BOT_PREFIX=v!
OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=
DANGEROUS_COMMANDS_ENABLED=false
TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET
YOUTUBE_API_KEY=YOUR_API_KEY
```

Never publish `.env`, the Discord token, or API credentials.

## ▶️ Launch

The project no longer uses the legacy terminal control panel.

Use the launcher directly:

**Windows**
```text
start_bot.bat
```

**Linux/macOS**
```bash
./start_bot.sh
```

The launcher:
1. Creates the virtual environment if needed.
2. Installs dependencies on first setup.
3. Starts the local web panel.
4. Starts the Discord bot.

The web panel is available by default at `http://127.0.0.1:8765`.

## 🌐 Web panel

The `dev-panel` branch contains the web control panel.

Current scope:
- localhost-only aiohttp server
- token authentication with an HttpOnly session cookie
- bot status
- recent bot logs
- action-specific one-time security-code generation

On first launch, a random token is stored in `panel_web/.token` and printed by the web-panel process. You can instead set `PANEL_WEB_TOKEN` in `.env`.

The panel remains loopback-only. Do not expose it through port forwarding or a reverse proxy while this implementation is being expanded.

## 🔐 Security codes

The web panel can generate a temporary **6-digit, one-time code** for one selected sensitive Discord action:

```text
spam
dmall
raid
remove_raid
```

A code generated for one action cannot authorize another action. Multiple codes may be active at the same time.

Codes are stored only as SHA-256 hashes with their intended action and expiration time. They are consumed atomically and removed after successful use or expiration. The plaintext code is never written to the security log.

## 👑 Owners and permissions

There is a maximum of **1 primary owner** and **5 secondary owners**:

```env
OWNER_PRINCIPAL_ID=123456789
OWNERS_SECONDARY_IDS=111111111,222222222
```

Owner checks, Discord permissions, kill-switch checks, and Discord role/member hierarchy checks are centralized in `app/checks.py`.

Temporary authorizations are scoped to a guild and automatically expire.

## 📢 Twitch / YouTube announcements

Announcements can be configured and managed from Discord. The bot supports a primary API configuration plus isolated per-server credentials.

Typical commands include:

```text
v!create_annonce
v!annonces
v!test_annonce <id>
v!delete_annonce <id>
v!set_api twitch
v!set_api yt
v!api_status
v!clear_api twitch
v!clear_api yt
```

Per-server credentials are stored by `guild_id` in `api_credentials.json` and written atomically.

## ⚠️ Sensitive commands

The following commands are isolated and disabled by default:

```text
v!spam
v!dmall
v!raid
v!remove_raid
```

Enable them only when required:

```env
DANGEROUS_COMMANDS_ENABLED=false
```

Sensitive commands also use explicit confirmations where appropriate, command-specific limits, permission checks, and an action-specific one-time security code.

## 💾 Persistence and data safety

Security-critical JSON state is handled through `app/safe_json.py` and `app/state.py`.

- JSON stores reject corruption instead of silently treating it as empty data.
- Writes use unique temporary files in the destination directory.
- File contents are flushed and `fsync`ed before replacement.
- POSIX directory metadata is synchronized after replacement when supported.
- Runtime state mutations are synchronized with a re-entrant lock.
- Failed state writes roll back the in-memory change where applicable.
- Sensitive state files use restrictive `0600` permissions on POSIX systems.

Runtime files such as `.env`, `bot_state.json`, `action_codes.json`, API credential stores, and logs must not be committed when they contain local secrets or state.

## 🛡️ Security tooling

CI runs:

- `ruff` for linting
- `pytest` for automated tests
- Gitleaks for secret scanning
- **GitHub CodeQL** with the `security-extended` query suite for Python security analysis

CodeQL runs on pushes to `main`, `dev`, and `dev-panel`, pull requests targeting `main`, and weekly on the scheduled workflow.

## 🧩 Architecture

```text
v-bot/
├── app/
├── cogs/
├── tests/
├── main.py
├── bootstrap.py
├── panel_web/
├── start_bot.bat
├── start_bot.sh
└── requirements.txt
```

`main.py` handles startup, logging, global checks, and extension loading. Business logic lives in Cogs and application modules. `app/security.py` handles action-specific one-time sensitive-action authorization, while `app/audit.py` handles command/security auditing.

## 🏷️ Versioning

The application version is derived from Git tags, with a fallback when Git history is unavailable. Release tags use the form:

```text
v3.8.2
v3.9.0
```

## 🧰 Technologies

- Python 3.13
- discord.py
- python-dotenv
- psutil
- aiohttp
- pytest
- ruff
- GitHub Actions
- GitHub CodeQL

## 📄 License

MIT License. See [`LICENSE`](LICENSE).

Copyright (c) 2026 vzsca.
