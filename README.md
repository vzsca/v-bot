# 🤖 v-bot

Versatile Discord bot developed in **Python with discord.py**, designed for moderation, server management, and secure bot administration.

The project also includes a **local control panel** for managing the bot process, `.env` configuration, owners, logs, and sensitive features.

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
* 📺 Automatic Twitch stream announcements
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
├── exceptions.py            # Custom exceptions
├── security_log.py          # Security logging
├── twitch_api.py             # Twitch API integration
│
├── start_bot.bat            # Launches the panel
├── requirements.txt         # Python dependencies
├── .env                     # Private configuration
├── .env.example             # Configuration example
│
├── bot.log                  # Bot logs
├── security.log             # Security logs
├── servers.txt              # Server list
├── twitch_config.json      # Local Twitch announcement configuration
│
├── cogs/
    ├── events.py            # Discord events
    ├── moderation.py        # Moderation
    ├── info.py              # Information
    ├── owner.py             # Bot administration
    ├── dangerous.py         # Sensitive commands
    ├── twitch.py            # Twitch commands and stream monitoring
    └── help_cog.py          # Help system

```

> ⚠️ The `venv/` folder is generated locally and should not be uploaded to GitHub.

---

# 🚀 Installation

## Requirements

* Windows **recommended**
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

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Then configure:

```env
DISCORD_TOKEN=YOUR_TOKEN

BOT_NAME=v-bot
BOT_PREFIX=v!
BOT_VERSION=3.7.5

OWNER_PRINCIPAL_ID=YOUR_DISCORD_ID
OWNERS_SECONDARY_IDS=

DANGEROUS_COMMANDS_ENABLED=false

TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET
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
| `TWITCH_CLIENT_ID`            | Twitch API Client ID                   |
| `TWITCH_CLIENT_SECRET`        | Twitch API Client Secret               |

> 🔒 **Never share your `.env` file or Discord bot token.**

---

# ▶️ Launch

The recommended way to launch the bot is:

```text
start_bot.bat
```

To launch the bot manually:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

The script:

1. Checks Python
2. Creates the `venv` if necessary
3. Installs dependencies
4. Launches the panel
5. The panel can then be used to start the bot

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

# 📺 Twitch Announcements

v-bot can automatically announce when a configured Twitch channel starts a stream.

Twitch announcements are managed through the Twitch Cog:

```text
cogs/twitch.py
```

Each announcement configuration contains:

* Twitch channel URL
* Announcement message
* Discord channel

The bot periodically checks the configured Twitch channels and automatically sends the configured announcement when a stream starts.

## Twitch Commands

### v!create_annonce

Creates a new Twitch announcement configuration.
```text
v!create_annonce
```

The bot will interactively ask for:

The Twitch channel URL
The announcement message
The Discord channel where the announcement should be sent

Each step has a 1-minute timeout.

If no response is received within 1 minute, the setup is cancelled.

### v!annonces

Displays the Twitch announcement configurations currently registered.
```text
v!annonces
```

### v!test_annonce

Tests a configured Twitch announcement without waiting for the Twitch channel to start streaming.
```text
v!test_annonce
```
This can be used to verify that the announcement message and Discord channel are correctly configured.

### v!delete_annonce

Deletes an existing Twitch announcement configuration.
```text
v!delete_annonce
```
The corresponding Twitch announcement configuration is removed from the local configuration.

## Twitch API Configuration

Twitch announcements require Twitch API credentials.
The credentials are stored in `.env`:
```text
TWITCH_CLIENT_ID=YOUR_CLIENT_ID
TWITCH_CLIENT_SECRET=YOUR_CLIENT_SECRET
```
They can be configured from the local control panel using:
```text
set_twitch_api
```
The Twitch API credentials are private and should never be published or committed to GitHub.

## Twitch Configuration File

Twitch announcement configurations are automatically stored locally in:
```text
twitch_config.json
```
This file is created automatically when Twitch announcement functionality is used.

It should not be committed to GitHub if it contains private server configuration.


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

### `cogs/twitch.py`

Twitch integration and stream announcement system.

Handles:

* Twitch API integration
* Twitch announcement configuration
* Automatic stream detection
* Announcement testing
* Announcement deletion
* Announcement listing

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
