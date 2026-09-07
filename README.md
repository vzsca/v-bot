# 🤖 v-bot

Versatile Discord bot developed in **Python with discord.py**, designed for moderation, server management, and secure bot administration.

The project also includes a **local control panel** for managing the bot process, `.env` configuration, owners, logs, and sensitive features.

v-bot is designed to be **cross-platform** and can be self-hosted on **Windows, Linux, or macOS**.

---

## 🤖 Installation

You have two options to use v-bot:

### Option 1 — Use the official v-bot instance

You can add the official v-bot instance directly to your Discord server:

[**➜ Add v-bot to your server**](https://discord.com/oauth2/authorize?client_id=1335588735794024499)

> **PS:** v-bot may not be hosted 24/7 and may be offline for an undetermined period of time. During these periods, only the public source code and documentation will remain available.

### Option 2 — Run your own v-bot instance

You can also run your own instance of v-bot using the public source code.

You **do not need to use the invitation link above**. Simply create your own Discord bot through the [Discord Developer Portal](https://discord.com/developers/applications), configure its token and owner settings in `.env`, then follow the installation steps below.

This allows you to:

* Run your own independent instance
* Use your own Discord bot
* Configure your own prefix and owners
* Manage your own Twitch API credentials
* Enable or disable sensitive features
* Keep your bot and configuration under your own control

The invitation link is only for the hosted v-bot instance. **If you install v-bot yourself, you must create and configure your own Discord bot.**

## ✨ Features

* 🛡️ Full moderation
* ℹ️ Information commands
* 👑 Permanent and temporary owner system
* 🔐 Global Kill Switch
* 🧹 Deleted message snipe
* 🌐 Multi-server management
* ⚙️ Local control panel
* 📋 Standard and security logs
* 🔒 Sensitive commands disabled by default
* 🔄 Automatic startup and shutdown management
* 🧩 Modular architecture with Cogs
* ⚡ Prefix commands and slash/hybrid commands for compatible commands
* 📢 Automatic Twitch and YouTube announcements
* 💬 Custom Discord embeds

---

# 📁 Project Structure

```text
v-bot/
├── main.py                  # Bot entry point
├── panel.py                 # Local control panel
├── bootstrap.py             # Initial setup
├── deps.py                  # Dependency management
├── config.py                # Bot configuration
├── checks.py                # Permission system
├── state.py                 # Internal bot state
├── exceptions.py             # Custom exceptions
├── security_log.py           # Security logging
├── integration_config.py     # Dynamic API credential configuration
├── announcement_store.py     # Atomic announcement storage
├── api_access.py             # API configuration access control
│
├── start_bot.bat             # Launches the panel
├── start_bot.sh              # Linux/macOS launcher
├── requirements.txt          # Python dependencies
├── .env                      # Private configuration
├── .env.example              # Configuration example
│
├── cogs/
    ├── events.py             # Discord events
    ├── moderation.py         # Moderation
    ├── info.py               # Information
    ├── owner.py              # Bot administration
    ├── dangerous_safe.py     # Sensitive commands
    ├── annonce.py            # Announcement management commands
    ├── twitch.py             # Twitch integration and stream monitoring
    ├── youtube.py            # YouTube integration and video monitoring
    └── help_cog.py           # Help system
```

> ⚠️ The `venv/` folder is generated locally and should not be uploaded to GitHub.

---

# 🚀 Self-Hosting

## Requirements

* Windows, Linux, or macOS
* Python **3.13 recommended**
* A Discord bot created through the [Discord Developer Portal](https://discord.com/developers/applications)
* The required intents enabled for the Discord bot

Dependencies are installed automatically during the first launch.

---

## 1. Clone the project

```bash
git clone https://github.com/vzsca/v-bot.git
cd v-bot
```

---

## 2. Configure `.env`

Create a `.env` file from `.env.example`.

### Windows
```text
copy .env.example .env
```

### Linux / macOS
```text
cp .env.example .env
```

Then configure:

```env
DISCORD_TOKEN=YOUR_TOKEN

BOT_PREFIX=v!
BOT_VERSION=3.8.2

OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=

DANGEROUS_COMMANDS_ENABLED=false

TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET

YOUTUBE_API_KEY=YOUR_API_KEY
```

### 🔑 Variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Discord bot token |
| `BOT_PREFIX` | Command prefix |
| `BOT_VERSION` | Version displayed by the bot |
| `OWNER_PRINCIPAL_ID` | Principal owner |
| `OWNERS_SECONDARY_IDS` | Secondary owners separated by commas |
| `DANGEROUS_COMMANDS_ENABLED` | Enables or disables sensitive commands |
| `TWITCH_CLIENT_ID` | Twitch API Client ID |
| `TWITCH_CLIENT_SECRET` | Twitch API Client Secret |
| `YOUTUBE_API_KEY` | YouTube Data API key |

> 🔒 **Never share your `.env` file or Discord bot token.**

---

# ▶️ Launch

v-bot includes platform-specific launchers that automatically prepare the Python environment and start the local control panel.

### 🪟 Windows

The recommended way to launch v-bot is:
```text
start_bot.bat
```

The launcher checks Python, creates the `venv` if necessary, installs dependencies, and starts the control panel.

### 🐧 Linux / 🍎 macOS

The recommended way to launch v-bot is:
```text
./start_bot.sh
```

If the script does not have execution permissions:
```bash
chmod +x start_bot.sh
```

The launcher checks Python, creates the `venv` if necessary, installs dependencies, and starts the control panel.

## Manual launch

### Windows
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python panel.py
```

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python panel.py
```

The control panel can then be used to start the bot.

---

# 🖥️ Control Panel

The panel displays:

```text
v-bot>
```

Available commands:

| Command | Function |
|---|---|
| `start` | Start the bot |
| `stop` | Stop the bot |
| `restart` | Restart the bot |
| `status` | View the bot status |
| `uptime` | View how long the bot has been running |
| `update` | Update dependencies |
| `logs` | Display `bot.log` |
| `security_logs` | Display security events |
| `servers` | Display connected servers |
| `add_secondary_owner` | Add a secondary owner |
| `set_token` | Change the Discord token |
| `set_principal_owner` | Change the principal owner |
| `toggle_dangerous` | Enable/disable sensitive commands |
| `set_prefix` | Change the command prefix |
| `set_twitch_api` | Configure Twitch API credentials |
| `set_youtube_api` | Configure the YouTube API key |

API credentials configured through the panel are saved atomically to `.env`.

Twitch and YouTube credentials are reloaded automatically while the bot is running. Discord token, prefix, owner, and sensitive-command setting changes require a bot restart.

Use:
```text
help
```
to display the list directly in the panel.

---

# 📜 Discord Commands

The default prefix is:
```text
v!
```

You can change it from the panel using `set_prefix`.

---

## 🛡️ Moderation

### `v!mute`
Temporarily mutes a member.
```text
v!mute @member 10 reason
```

### `v!unmute`
Removes a member's mute.
```text
v!unmute @member
```

### `v!kick`
Kicks a member.
```text
v!kick @member reason
```

### `v!ban`
Bans a member.
```text
v!ban @member reason
```

### `v!unban`
Unbans a user by ID.
```text
v!unban 123456789012345678
```

### `v!give_role`
Gives a role to a member.
```text
v!give_role @member @role
```

### `v!lock`
Locks the current channel.
```text
v!lock
```

### `v!unlock`
Unlocks the current channel.
```text
v!unlock
```

### `v!slowmode`
Configures slow mode.
```text
v!slowmode 10
```

### `v!clear`
Deletes messages.
```text
v!clear 50
```

Moderation commands check the corresponding Discord permissions or owner privileges.

---

# ℹ️ Information

### `v!help`
Displays the bot's help menu.

### `v!user_info`
Displays information about a member.

### `v!server_info`
Displays information about the server.

### `v!avatar`
Displays a user's avatar.

### `v!snipe`
Displays a recently deleted message.
```text
v!snipe
v!snipe 2
```

---

# 👑 Owner System

### Principal Owner
```env
OWNER_PRINCIPAL_ID=123456789
```

### Secondary Owners
```env
OWNERS_SECONDARY_IDS=123456789,987654321
```

They can also be added from the panel using `add_secondary_owner`.

### Temporary Owners

A permanent owner can temporarily grant permissions to a user:
```text
v!add_temp @user 3600
```

The permission lasts for **3600 seconds** and is scoped to the current server.

### Owner List
```text
v!owner_list
```

---

# 🔐 Kill Switch

Check its status:
```text
v!killswitch
```

Enable:
```text
v!killswitch on
```

Disable:
```text
v!killswitch off
```

The Kill Switch can block protected commands in case of a security issue or unexpected behavior.

---

# 🌐 Server Management

Owners can use:
```text
v!servers
```

to access the server management panel.

The local panel also provides `servers`, which displays the connected servers.

---

# 🗣️ `say` Command

Owners can make the bot send a message:
```text
v!say Hello everyone!
```

The command message is then deleted.

---

# 💬 `embed` Command

Owners can create a custom Discord embed:
```text
v!embed <title> | <description>
```

The `|` character separates the title from the description.

---

## 📢 Announcements

v-bot includes an extensible announcement system for Twitch and YouTube.

### Commands

| Command | Description |
|---|---|
| `v!create_annonce` | Create an announcement |
| `v!annonces` | List configured announcements |
| `v!test_annonce <id>` | Test an announcement |
| `v!delete_annonce <id>` | Delete an announcement |

These commands are available to permanent/temporary owners and Discord server administrators.

### Twitch placeholders

| Placeholder | Description |
|---|---|
| `{streamer}` | Twitch username |
| `{title}` | Stream title |
| `{game}` | Stream category |
| `{url}` | Twitch stream URL |

A Twitch announcement is sent when the configured channel changes from offline to live.

### YouTube placeholders

| Placeholder | Description |
|---|---|
| `{channel}` | YouTube channel name |
| `{title}` | Video title |
| `{url}` | YouTube video URL |

A YouTube announcement is sent when a new video is detected.

### Architecture

```text
cogs/
├── annonce.py
├── twitch.py
└── youtube.py
```

`annonce.py` manages configuration. `twitch.py` and `youtube.py` contain the platform-specific API monitoring logic.

Announcements are stored atomically in `annonce_config.json` and isolated by guild.

---

# ⚠️ Sensitive Commands

Sensitive commands are intentionally isolated in:
```text
cogs/dangerous_safe.py
```

Available commands:

* `spam`
* `dmall`
* `raid`
* `remove_raid`

They are **disabled by default** and the cog is not loaded unless enabled.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

### Activation

From the panel:
```text
toggle_dangerous
```

The panel requires explicit confirmation with:
```text
ENABLE
```

A restart is required after changing this setting.

### Safety limits

Sensitive operations are deliberately capped by configuration. `dmall` is additionally restricted by a maximum member count and requires explicit confirmation.

---

# 🛡️ Security

v-bot centralizes permission checks in `checks.py`.

Access levels include:

* Permanent owner
* Permanent or temporary owner
* Owner or server owner
* Owner or specific Discord permission
* Kill Switch

Temporary owner authorization is scoped to a guild and automatically expires.

Sensitive commands are separated from the normal command set and disabled by default.

### Atomic configuration

`.env` and announcement configuration use atomic file replacement/transactional updates to avoid partially written configuration files.

### Security Logs

Sensitive actions are recorded in:
```text
security.log
```

The Discord token and API secrets are never written to security logs.

---

# 📝 Logs

`bot.log` contains bot events and errors. It is rotated to prevent unbounded growth.

`security.log` contains sensitive events and is also bounded/rotated.

The panel can display both through `logs` and `security_logs`.

---

# ⚙️ Architecture

The bot is organized into modular Cogs.

### `cogs/events.py`
Connection, server join/leave, mentions, deleted messages, errors, and periodic state cleanup.

### `cogs/moderation.py`
Moderation commands.

### `cogs/info.py`
Information commands and snipe functionality.

### `cogs/owner.py`
Owner management and server administration.

### `cogs/dangerous_safe.py`
Sensitive commands loaded only when enabled.

### `cogs/annonce.py`
Announcement management and guild-isolated configuration.

### `cogs/twitch.py`
Twitch authentication, live detection, bounded caching, and announcements.

### `cogs/youtube.py`
YouTube API integration, new-video detection, bounded caching, and announcements.

---

# 🔧 Discord Configuration

The bot uses the following intents where required:

```text
guilds
members
messages
message_content
reactions
```

The required intents must be enabled in the **Discord Developer Portal**.

---

# 🧰 Technologies

* **Python 3.13**
* **discord.py**
* **python-dotenv**
* **psutil**
* **aiohttp**
* **pytest**
* **ruff**

---

# 🔒 Files That Should Never Be Published

Never publish:
```text
.env
```

or any file containing your Discord token or API secrets.

The project uses `.env.example` to provide only the configuration template.

---

# 📌 Version

Current version:
```text
3.8.2
```

---

# 🐛 Bug Reports & Feedback

If you encounter a bug, have a suggestion, or would like to recommend an improvement for v-bot, report it through the project's configured support channels.

When reporting a bug, provide:

* What happened
* What you expected to happen
* Steps to reproduce the issue
* Relevant error messages or logs

---

# 📄 License

Personal project.

Any use, modification, or redistribution of the project must comply with the conditions defined by its owner.
