# 🤖 v-bot

A Discord bot built with **Python and discord.py**, focused on moderation, server management, Twitch/YouTube announcements, and secure administration.

The project includes a cross-platform local control panel and targets Windows, Linux, and macOS.

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
- 🔑 One-time 6-digit security codes for sensitive actions
- 🧩 Modular Cogs and application modules
- 📚 Permission-aware help system
- 💬 Permission-aware bot mention responses
- 🖥️ Cross-platform local control panel

## 🚀 Installation

### Requirements

- Windows, Linux, or macOS
- Python **3.13**
- A Discord application/bot with the required intents enabled

```bash
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

### Launch

Windows:

```text
start_bot.bat
```

Linux/macOS:

```bash
./start_bot.sh
```

The launcher prepares the Python environment and starts the local control panel.

## 🖥️ Local control panel

The interactive panel provides:

```text
start
stop
restart
status
uptime
logs
security_logs
servers
add_secondary_owner
set_token
set_principal_owner
toggle_dangerous
action_code
set_prefix
set_twitch_api
set_youtube_api
```

`status` reports the version, platform, owner configuration, bot state, PID, uptime, CPU/RAM usage, and current Git commit.

### Security codes

`action_code` generates a temporary **6-digit, one-time code** for sensitive Discord actions.

Codes are stored only as SHA-256 hashes, expire automatically, and are consumed atomically. Multiple codes may be active at the same time, so generating a new code no longer invalidates an earlier active code. The code is never written to the security log.

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

Sensitive commands also use explicit confirmations, command-specific limits, permission checks, and a one-time security code.

Raid-test channels and roles are persisted as they are created. If persistence fails, the operation aborts and attempts to roll back the newly created resource. Cleanup removes a persistent resource reference only after the corresponding Discord resource has been deleted or is already absent.

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
│   ├── announcement_store.py
│   ├── api_access.py
│   ├── api_credentials.py
│   ├── audit.py
│   ├── checks.py
│   ├── config.py
│   ├── deps.py
│   ├── exceptions.py
│   ├── extensions.py
│   ├── integration_config.py
│   ├── metrics.py
│   ├── rate_limit.py
│   ├── safe_json.py
│   ├── security.py
│   ├── security_log.py
│   ├── state.py
│   ├── updater.py
│   ├── validators.py
│   └── version.py
├── cogs/
├── tests/
├── main.py
├── panel.py
├── bootstrap.py
├── start_bot.bat
├── start_bot.sh
└── requirements.txt
```

`main.py` handles startup, logging, global checks, and extension loading. Business logic lives in Cogs and application modules. `app/security.py` handles one-time sensitive-action authorization, while `app/audit.py` handles command/security auditing. Persistent runtime security state is handled by `app/state.py`.

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
