# 🤖 v-bot

A Discord bot built with **Python and discord.py**, focused on moderation, server management, Twitch/YouTube announcements, and secure administration.

The project includes a cross-platform local control panel and targets Windows, Linux, and macOS.

## ✨ Features

- 🛡️ Moderation and server-management commands
- 👑 Permanent owners and temporary server-scoped authorizations
- 🔐 Persistent kill switch and disabled-server state
- 🧹 Deleted-message snipe support
- 📢 Twitch, YouTube, and Instagram video announcements
- 🔑 Global primary API + per-server API credentials
- 🚦 Global/per-user/per-command rate limiting
- 🛡️ Anti-spam and anti-raid detection
- 📋 Standard and security logs with audit events
- 🔐 Sensitive commands disabled by default
- 🔑 One-time 6-digit security codes bound to a specific sensitive action
- 🧩 Modular Cogs and application modules
- 📚 Interactive, permission-aware help system with category buttons and direct category commands
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
INSTAGRAM_ACCESS_TOKEN=YOUR_INSTAGRAM_GRAPH_API_TOKEN
INSTAGRAM_USER_ID=YOUR_INSTAGRAM_PROFESSIONAL_ACCOUNT_ID
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
set_instagram_api
api_status
clear_api twitch
clear_api yt
clear_api instagram
clear_api instagram
```

`status` reports the version, platform, owner configuration, bot state, PID, uptime, CPU/RAM usage, and current Git commit.

### Security codes

`action_code` generates a temporary **6-digit, one-time code** for one selected sensitive Discord action:

```text
spam
dmall
raid
remove_raid
```

The panel asks which action the code is intended for. Codes expire after **60 seconds**. A code generated for one action cannot authorize another action. Multiple codes may be active at the same time, so generating a new code does not invalidate earlier active codes.

Codes are stored only as SHA-256 hashes with their intended action and expiration time. They are consumed atomically and removed after successful use or expiration. The plaintext code is never written to the security log.

## 👑 Owners and permissions

There is a maximum of **1 primary owner** and **5 secondary owners**:

```env
OWNER_PRINCIPAL_ID=123456789
OWNERS_SECONDARY_IDS=111111111,222222222
```

Owner checks, Discord permissions, kill-switch checks, and Discord role/member hierarchy checks are centralized in `app/checks.py`.

Temporary authorizations are scoped to a guild and automatically expire.

## 📢 Twitch / YouTube / Instagram announcements

Twitch and YouTube announcements can be configured and managed from Discord. Instagram supports automatic announcements for video/Reel media only; photo posts are ignored. Instagram requires an eligible professional account and the official Graph API. Configure Instagram through `v!set_api instagram` to store an isolated token and professional-account ID for that server. Servers authorized to use the primary API use `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_USER_ID` from `.env` (configure them with the panel's `set_instagram_api` command); other servers use their own credentials in `api_credentials.json`. The first poll establishes a baseline, so existing videos are not reposted. `v!api_status` shows whether Instagram credentials are configured, and `v!clear_api instagram` removes the server-specific credentials. Twitch and YouTube announcement messages suppress automatic Discord mentions, so text such as `@everyone` in a stream or video title does not trigger unwanted pings.

YouTube API usage is optimized with shared caching across servers: channel resolution is cached for 24 hours, latest-video results for 90 seconds, and repeated lookups for the same API key and channel are reused. The polling loop backs off after HTTP 403/429 responses to help avoid repeatedly hitting API limits.

Typical commands include:

```text
v!create_annonce
v!create_instagram_annonce
v!annonces
v!test_annonce <id>
v!delete_annonce <id>
v!set_api twitch
v!set_api yt
v!set_api instagram
v!api_status
v!clear_api twitch
v!clear_api yt
v!clear_api instagram
```

Per-server credentials are stored by `guild_id` in `api_credentials.json` and written atomically.

## 💬 Permission-aware help system

Use `v!help` to open the help menu. When multiple categories are available, buttons let you browse the categories you are allowed to access:

- **General** — commands available to everyone.
- **Moderation** — shown to members with relevant moderation permissions.
- **Admin & Announcements** — requires the Discord **Administrator** permission.
- **Owner** — restricted to permanent owners and users with a valid temporary authorization.

You can also open a category directly with `v!help general`, `v!help mod`, `v!help admin`, or `v!help owner`. Aliases include `user` for general, `moderation` / `modo` for mod, and `announcement(s)` for admin. Access is checked when the category is requested; a visible help category does not bypass the command's own permission checks.

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

`main.py` handles startup, logging, global checks, and extension loading. Business logic lives in Cogs and application modules. `app/security.py` handles action-specific one-time sensitive-action authorization, while `app/audit.py` handles command/security auditing. Persistent runtime security state is handled by `app/state.py`.

## 🏷️ Versioning

The application version comes from `git describe --tags --match "v[0-9]*" --always --dirty`. Create release tags in the form `vMAJOR.MINOR.PATCH` (for example, `v3.8.2`). When a matching tag is available, Git reports that tag and, if applicable, the number of commits since it and the current commit hash. A modified working tree adds the `-dirty` suffix.

If no matching tag is available, Git reports the current commit hash instead. The fallback version (`3.8.2`) is used only if Git cannot provide a version.

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
