# 🤖 v-bot

A Discord bot built with **Python and discord.py**, focused on moderation, server management, Twitch/YouTube announcements, and secure administration.

v-bot includes a **local control panel** for process management, configuration, owners, logs, updates, and sensitive features. The project targets Windows, Linux, and macOS.

## ✨ Features

- 🛡️ Moderation commands
- ℹ️ Information commands
- 👑 Permanent owners and temporary authorizations
- 🔐 Kill Switch
- 🧹 Deleted-message snipe
- 🌐 Multi-server management
- ⚙️ Cross-platform local panel
- 🔄 Git-based code updates with automatic restart
- 🧯 Automatic code rollback on dependency or startup failure
- 📋 Standard and security logs
- 📢 Automatic Twitch and YouTube announcements
- 🔑 Global primary API + per-server API credentials
- 🔒 Sensitive commands disabled by default
- 🚦 Rate limiting, audit logging, and anti-spam/anti-raid detection
- 🧩 Modular Cogs and application modules
- 📚 Permission-aware help system with category buttons

---

# 🚀 Installation

## Requirements

- Windows, Linux, or macOS
- Python **3.13 recommended**
- A Discord bot created through the Discord Developer Portal
- Required Discord intents enabled
- Git installed for panel-based updates

```bash
git clone https://github.com/vzsca/v-bot.git
cd v-bot
```

Create `.env` from `.env.example`, then configure at least:

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

`BOT_VERSION` is no longer maintained manually: the application version is derived from Git tags, with a fallback for installations without Git history.

> 🔒 Never publish `.env`, the Discord token, or any API key.

## ▶️ Launch

### Windows

```text
start_bot.bat
```

### Linux / macOS

```bash
./start_bot.sh
```

The launcher prepares the Python environment and starts the local panel.

---

# 🖥️ Local panel

The panel is interactive and works on Windows, Linux, and macOS.

### Process management

```text
start
stop
restart
status
uptime
logs
security_logs
servers
```

### Configuration

```text
set_token
set_principal_owner
add_secondary_owner
set_prefix
set_twitch_api
set_youtube_api
toggle_dangerous
```

### Updates

```text
update
```

`update`:

1. checks whether `origin/main` actually contains new commits;
2. does not restart the bot when no update is available;
3. stops the bot only when an update is available;
4. performs a Git fast-forward without overwriting tracked local changes;
5. updates dependencies only when `requirements.txt` changed;
6. restarts the bot with the updated code;
7. restores the previous code commit when dependency installation or startup fails.

Git-ignored runtime and configuration files remain in place during the process: `.env`, `api_credentials.json`, `annonce_config.json`, `api_config_access.json`, logs, and PID/runtime files.

A divergent local branch or tracked local modifications block the automatic update to avoid destructive changes.

### `status`

`status` displays information including:

- version and platform;
- primary owner;
- secondary owners and the `X/5` counter;
- bot state, PID, and process information;
- uptime;
- CPU/RAM usage;
- Git repository state and available commit count;
- currently installed commit.

---

# 📚 Help system

The `v!help` command is permission-aware and separates commands into four categories:

- 📜 **General** — available to everyone;
- 🛡️ **Moderation** — available to users with moderation permissions;
- ⚙️ **Admin & Announcements** — requires the Discord `Administrator` permission;
- 👑 **Owner** — restricted to bot owners/authorized users.

When multiple categories are available, `v!help` displays a category menu with buttons. Buttons are restricted to the user who opened the menu and include a button to return to the category menu.

Specific categories can also be opened directly:

```text
v!help general
v!help mod
v!help admin
v!help owner
```

Users who only have access to General receive the General help embed directly.

---

# 👑 Owners

There is a maximum of **1 primary owner** and **5 secondary owners**.

```env
OWNER_PRINCIPAL_ID=123456789
OWNERS_SECONDARY_IDS=111111111,222222222
```

The panel prevents adding a sixth secondary owner and blocks duplicates or adding the primary owner as a secondary owner.

Temporary authorizations are limited to the relevant server and expire automatically.

---

# 🔑 Per-server API configuration

A server authorized in `api_config_access.json` automatically uses the **primary API** configured in `.env`.

A non-authorized server uses only its **own credentials**, configured from Discord.

### Twitch

```text
v!set_api twitch
```

The bot opens a private form for the Twitch Client ID and Twitch Client Secret.

### YouTube

```text
v!set_api yt
```

The form allows the user to enter the YouTube API Key.

### Check configuration

```text
v!api_status
```

The command displays the active API mode and configuration status without revealing secrets.

### Remove configuration

```text
v!clear_api twitch
v!clear_api yt
```

Per-server credentials are stored in `api_credentials.json`, isolated by `guild_id`, and written atomically. This file is ignored by Git.

> ⚠️ API secrets should never be sent directly in a Discord channel. `v!set_api` uses a private form.

---

# 📢 Twitch / YouTube announcements

## Creation

```text
v!create_annonce
```

The bot asks for the source URL, announcement message, and target channel. The announcement automatically uses the API associated with the server: the primary API for an authorized server, or local credentials for a non-authorized server.

## Management

```text
v!annonces
v!test_annonce <id>
v!delete_annonce <id>
```

### Twitch placeholders

- `{streamer}` — Twitch channel name
- `{title}` — live stream title
- `{game}` — category
- `{url}` — stream URL

### YouTube placeholders

- `{channel}` — channel name
- `{title}` — video title
- `{url}` — video URL

---

# ⚠️ Sensitive commands

The `spam`, `dmall`, `raid`, and `remove_raid` commands are isolated and disabled by default.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

Volume limits, confirmations, and permission checks help prevent accidental use.

---

# 🛡️ Security

- Permissions centralized in `app/checks.py`
- Global, per-user, and per-command rate limiting
- Audit logging and suspicious burst detection
- Anti-spam and anti-raid detection
- Temporary authorizations scoped to a server and automatically expired
- Secrets never written to security logs
- `.env` and persistent configuration files written atomically
- Corrupted JSON rejected instead of silently overwritten
- Bounded and rotating logs
- Per-server API credentials isolated by `guild_id`
- `api_credentials.json` excluded from Git
- Sensitive commands separated and disabled by default
- Git updates restricted to fast-forward operations
- Automatic code rollback on critical update failures

---

# 🧩 Architecture

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
│   ├── security_log.py
│   ├── state.py
│   ├── updater.py
│   └── version.py
├── cogs/
│   ├── events.py
│   ├── moderation.py
│   ├── info.py
│   ├── owner.py
│   ├── api_config.py
│   ├── annonce.py
│   ├── twitch.py
│   ├── youtube.py
│   ├── help_cog.py
│   └── dangerous_safe.py
├── tests/
├── main.py
├── panel.py
├── bootstrap.py
├── start_bot.bat
├── start_bot.sh
└── requirements.txt
```

`main.py` remains limited to bootstrap, logging, global checks, and extension loading. Business logic belongs in application modules and Cogs.

---

# 🏷️ Versioning

The version is derived from Git using:

```text
git describe --tags --match v[0-9]* --always --dirty
```

Use release tags such as:

```text
v3.8.2
v3.9.0
```

The version displayed by the bot and panel therefore follows Git instead of requiring several manual changes.

---

# 🧰 Technologies

- Python 3.13
- discord.py
- python-dotenv
- psutil
- aiohttp
- pytest
- ruff
- Git

---

# 🔒 Private / runtime files

Never publish:

```text
.env
api_credentials.json
annonce_config.json
api_config_access.json
security.log
bot.log
```

or any other file containing a token or API key.

---

# 📄 License

Personal project.
