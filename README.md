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
├── state.py                  # Internal bot state
├── exceptions.py             # Custom exceptions
├── security_log.py           # Security logging
├── twitch_api.py             # Twitch API integration
│
├── start_bot.bat             # Launches the panel
├── start_bot.sh              # Linux/macOS launcher
├── requirements.txt          # Python dependencies
├── .env                      # Private configuration
├── .env.example              # Configuration example
│
├── bot.log                   # Bot logs
├── security.log              # Security logs
├── servers.txt               # Server list
├── annonce_config.json       # Local announcement configuration
│
├── cogs/
    ├── events.py             # Discord events
    ├── moderation.py         # Moderation
    ├── info.py               # Information
    ├── owner.py              # Bot administration
    ├── dangerous.py          # Sensitive commands
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

Create a `.env` file from `.env.example.`

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
BOT_VERSION=3.7.5

OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=

DANGEROUS_COMMANDS_ENABLED=false

TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET

YOUTUBE_API_KEY=YOUR_API_KEY
```

### 🔑 Variables

| Variable                     | Description                            |
| ---------------------------- | -------------------------------------- |
| `DISCORD_TOKEN`              | Discord bot token                      |
| `BOT_PREFIX`                 | Command prefix                         |
| `BOT_VERSION`                | Version displayed by the bot           |
| `OWNER_PRINCIPAL_ID`         | Principal owner                        |
| `OWNERS_SECONDARY_IDS`       | Secondary owners separated by commas   |
| `DANGEROUS_COMMANDS_ENABLED` | Enables or disables sensitive commands |
| `TWITCH_CLIENT_ID`           | Twitch API Client ID                   |
| `TWITCH_CLIENT_SECRET`       | Twitch API Client Secret               |
| `YOUTUBE_API_KEY`            | YouTube Data API key                   |

> 🔒 **Never share your `.env` file or Discord bot token.**

---

# ▶️ Launch

v-bot includes platform-specific launchers that automatically prepare the Python environment and start the local control panel.

### 🪟 Windows

The recommended way to launch v-bot is:
```text
start_bot.bat
```
The launcher:

-Checks Python
-Creates the `venv` if necessary
-Installs dependencies
-Starts the control panel

### 🐧 Linux / 🍎 macOS

The recommended way to launch v-bot is:

```text
./start_bot.sh
```

If the script does not have execution permissions:

```bash
chmod +x start_bot.sh
```
Then:

```bash
./start_bot.sh
```
The launcher:

Checks Python
Creates the `venv` if necessary
Installs dependencies
Starts the control panel


## Manual launch

If you prefer to launch v-bot manually, create and activate the virtual environment first.

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python panel.py
```
## Linux / macOS

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

| Command               | Function                               |
| --------------------- | -------------------------------------- |
| `start`               | Start the bot                           |
| `stop`                | Stop the bot                            |
| `restart`             | Restart the bot                         |
| `status`              | View the bot status                     |
| `uptime`              | View how long the bot has been running |
| `update`              | Update dependencies                     |
| `logs`                | Open `bot.log`                          |
| `security_logs`       | Display the latest security events      |
| `servers`             | Display the bot's servers               |
| `add_secondary_owner` | Add a secondary owner                   |
| `set_token`           | Change the Discord token                |
| `set_principal_owner` | Change the principal owner              |
| `toggle_dangerous`    | Enable/disable sensitive commands       |
| `set_prefix`          | Change the command prefix               |
| `set_twitch_api`      | Configure the Twitch API credentials    |
| `set_youtube_api`     | Configure the YouTube API key           |

API credentials configured through the panel are saved to `.env`.

After changing API credentials, the bot must be restarted for the changes
to take effect.

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

You can change it from the panel using:

```text
set_prefix
```

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

```text
v!help
```

Categories can also be used.

```text
v!help owner
```

### `v!user_info`

Displays information about a member.

```text
v!user_info @member
```

### `v!server_info`

Displays information about the server.

```text
v!server_info
```

### `v!avatar`

Displays a user's avatar.

```text
v!avatar @member
```

### `v!snipe`

Displays a recently deleted message.

```text
v!snipe
```

You can also select a previous message:

```text
v!snipe 2
```

---

# 👑 Owner System

v-bot has multiple access levels.

### Principal Owner

A single principal owner is defined with:

```env
OWNER_PRINCIPAL_ID=123456789
```

### Secondary Owners

Multiple secondary owners can be defined:

```env
OWNERS_SECONDARY_IDS=123456789,987654321
```

They can also be added from the panel using:

```text
add_secondary_owner
```

### Temporary Owners

A permanent owner can temporarily grant permissions to a user:

```text
v!add_temp @user 3600
```

Here, the permission lasts for **3600 seconds**.

### Owner List

```text
v!owner_list
```

Displays permanent and temporary owners.

---

# 🔐 Kill Switch

The bot includes a **Kill Switch** system that can block protected commands.

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

The Kill Switch is particularly useful in case of a security issue or unexpected bot behavior.

---

# 🌐 Server Management

Owners can use:

```text
v!servers
```

to access the server management panel.

The local panel also provides:

```text
servers
```

which displays the list of servers the bot is connected to.

The list is automatically saved to:

```text
servers.txt
```

---

# 🗣️ `say` Command

Owners can make the bot send a message:

```text
v!say Hello everyone!
```

The message containing the command is then deleted.

---

# 💬 `embed` Command

Owners can make the bot send a custom Discord embed.

```text
v!embed <title> | <description>
v!embed Server Update | The server will be updated tonight.
```

The | character separates the embed title from its description.
The command is restricted to authorized owners.

---

## 📢 Announcements

v-bot includes an extensible announcement system for external platforms.

Announcements are managed through a central system, while each supported
platform has its own integration and background task.

### Supported platforms

- 🟣 Twitch
- 🔴 YouTube

### Announcement commands

| Command | Description |
|---|---|
| `v!create_annonce` | Create a Twitch or YouTube announcement |
| `v!annonces` | List configured announcements |
| `v!test_annonce <id>` | Test an announcement |
| `v!delete_annonce <id>` | Delete an announcement |

These commands are available to:

- Permanent and temporary bot owners
- Discord server administrators


### Twitch placeholders

When creating a Twitch announcement, you can use:

| Placeholder | Description |
|---|---|
| `{streamer}` | Twitch username |
| `{title}` | Stream title |
| `{game}` | Stream category |
| `{url}` | Twitch stream URL |

A Twitch announcement is automatically sent when the configured channel
changes from offline to live.

### YouTube placeholders

When creating a YouTube announcement, you can use:

| Placeholder | Description |
|---|---|
| `{channel}` | YouTube channel name |
| `{title}` | Video title |
| `{url}` | YouTube video URL |

A YouTube announcement is automatically sent when a new video is detected.

### Architecture

The announcement system is split into separate cogs:

```text
cogs/
├── annonce.py
├── twitch.py
└── youtube.py

```
`annonce.py` handles announcement management and commands.
`twitch.py` handles Twitch API requests, live detection and Twitch
announcements.
`youtube.py` handles YouTube API requests, new video detection and YouTube
announcements.

This structure makes it easier to add support for additional platforms in
the future without making the main announcement system unnecessarily large.

### Configuration

Announcements are stored in:
```text
annonce_config.json
```
Platform API credentials are configured through `.env`.
For Twitch:
```text
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
```
For YouTube:
```text
YOUTUBE_API_KEY=...
```


---

# ⚠️ Sensitive Commands

The following commands are intentionally separated into:

```text
cogs/dangerous.py
```

* `spam`
* `dmall`
* `raid`
* `remove_raid`

They are **disabled by default**.

```env
DANGEROUS_COMMANDS_ENABLED=false
```

When disabled, the `dangerous` Cog is not even loaded by the bot.

---

## Activation

From the panel:

```text
toggle_dangerous
```

The panel requires explicit confirmation:

```text
ENABLE
```

After activation, a restart is required:

```text
restart
```

---

## `v!spam`

Allows controlled sending of multiple messages.

```text
v!spam <amount> <message>
```

The maximum amount is limited by the bot configuration.

---

## `v!dmall`

Sends a direct message to server members.

```text
v!dmall <message>
```

This command is protected and should be used with caution.

---

## `v!raid`

A controlled test function that creates temporary channels and roles.

```text
v!raid 10
```

Created elements are tracked so they can later be removed with:

```text
v!remove_raid
```

---

# 🛡️ Security

v-bot includes several security protections.

### Centralized Permissions

Permissions are managed in:

```text
checks.py
```

with different access levels:

* Permanent owner
* Permanent or temporary owner
* Owner or server owner
* Owner or specific Discord permission
* Kill Switch

---

### Anti-Double-Execution Protection

Sensitive commands cannot be executed multiple times simultaneously on the same server.

This helps prevent:

* Multiple channel/role creations
* Duplicate operations
* Accidental simultaneous executions

---

### Security Logs

Sensitive actions are recorded in:

```text
security.log
```

Examples:

* Token changes
* Principal owner changes
* Secondary owner additions
* Temporary owner additions
* Sensitive command activation/deactivation
* Kill Switch activation/deactivation

The token itself is **never written to the logs**.

---

# 📝 Logs

## `bot.log`

Contains bot events and errors.

From the panel:

```text
logs
```

opens the file directly.

## `security.log`

Contains sensitive events only.

From the panel:

```text
security_logs
```

displays the latest entries.

---

# ⚙️ Architecture

The bot is organized into multiple **Cogs** to keep the project modular.

### `cogs/moderation.py`

All moderation commands.

### `cogs/info.py`

Information commands and the snipe system.

### `cogs/owner.py`

Bot administration and owner management.

### `cogs/events.py`

Discord event handling:

* Connection
* Server join/leave
* Bot mentions
* Deleted messages
* Errors
* Temporary owner cleanup

### `cogs/dangerous.py`

Sensitive commands, loaded only when enabled.

### `cogs/annonce.py`

Central announcement management system.

Handles:

* Creating announcements
* Listing announcements
* Testing announcements
* Deleting announcements
* Detecting the platform from the provided URL
* Managing shared announcement configuration

The platform-specific logic is handled by separate Cogs.

### `cogs/twitch.py`

Twitch integration.

Handles:

* Twitch API authentication
* Live stream detection
* Twitch stream information
* Automatic Twitch announcements

### `cogs/youtube.py`

YouTube integration.

Handles:

* YouTube API integration
* New video detection
* YouTube video information
* Automatic YouTube announcements

### `cogs/help_cog.py`

Help system.

---

# 🔧 Discord Configuration

The bot uses the following intents:

```text
guilds
members
messages
message_content
reactions
```

The required intents must be enabled in the **Discord Developer Portal**.

The bot also synchronizes its commands when connecting to Discord.

---

# 🧰 Technologies

* **Python 3.13**
* **discord.py**
* **python-dotenv**
* **psutil**
* **asyncio**
* **Windows Batch**
* **Bash**

---

# 🔒 Files That Should Never Be Published

Never publish:

```text
.env
```

or any file containing your Discord token.

The project uses `.env.example` to provide only the configuration template.

---

# 📌 Version

Current version:

```text
3.8.1
```

---

# 🐛 Bug Reports & Feedback

If you encounter a bug, have a suggestion, or would like to recommend an improvement for v-bot, you can report it through either of the following methods:

* 📧 **Email:** `support.v.bot@gmail.com`
* 💬 **Discord:** Open a support ticket in the [official Discord server](https://discord.gg/vgvFA7NJHg)

When reporting a bug, please provide as much information as possible, including:

* What happened
* What you expected to happen
* Steps to reproduce the issue
* Relevant error messages or logs

Your feedback and suggestions are welcome and can help improve v-bot.

---

# 📄 License

Personal project.

Any use, modification, or redistribution of the project must comply with the conditions defined by its owner.
