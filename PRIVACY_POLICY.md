# v-bot — Privacy Policy

**Last updated:** August 16, 2026

This Privacy Policy explains what information v-bot may process, why it is processed, and how it is handled.

By installing or using v-bot, you acknowledge this Privacy Policy.

## 1. About v-bot

v-bot is an open-source Discord bot that can provide moderation, server management, information, owner management, Twitch announcements, and other automation features.

v-bot is normally self-hosted by the user. The bot operator is responsible for the instance they operate and for the data processed by that instance.

## 2. Information Processed

Depending on the features enabled and how the bot is configured, v-bot may process the following information.

### Discord User Information

v-bot may process:

- Discord user IDs.
- Discord usernames and display names.
- Discord avatars.
- Discord server membership information.
- Discord roles and permissions.
- Discord message content when required by enabled features.

This information is processed only when required for the bot's functionality.

### Discord Server Information

v-bot may process:

- Server IDs.
- Server names.
- Channel IDs.
- Channel names.
- Role IDs and role names.
- Server member information required for moderation or administration features.

The bot may also maintain a local list of servers it is connected to.

## 3. Temporary Owner Data

v-bot includes a temporary owner system.

When a user is granted temporary owner access, the bot may store:

- The user's Discord ID.
- The expiration time of the temporary authorization.

Temporary authorizations are automatically removed after they expire.

## 4. Deleted Messages

v-bot includes a `snipe` feature.

When enabled, the bot temporarily stores information about recently deleted messages, which may include:

- Message content.
- Author information.
- Author avatar.
- Message creation time.
- Attachment URLs.

This information is stored locally in the bot's runtime memory and is limited to the configured number of recent messages.

It is not intended to be permanently stored.

## 5. Security Logs

v-bot may maintain a local security log containing security-related events, such as:

- Changes to owner permissions.
- Temporary owner grants.
- Kill switch activation or deactivation.
- Changes made through the control panel.
- Other security-related administrative actions.

These logs are stored locally by the operator of the bot.

## 6. Twitch Integration

If Twitch announcements are enabled, v-bot may process information related to configured Twitch channels.

This may include:

- Twitch channel identifiers or usernames.
- Twitch stream status.
- Twitch API information required to determine whether a configured channel is live.

v-bot does not require access to a Twitch user's private messages or account password.

Twitch API credentials are stored locally in the bot's `.env` configuration and should never be publicly shared.

## 7. Credentials

v-bot may require sensitive credentials such as:

- Discord bot tokens.
- Twitch Client IDs.
- Twitch Client Secrets.

These credentials are intended to be stored locally in the `.env` file.

v-bot does not intentionally send these credentials to the project's GitHub repository or to third parties.

Users are responsible for keeping their credentials secure.

## 8. Data Storage

v-bot is designed to process and store information locally on the machine where the bot is hosted.

Depending on the enabled features, local files may include:

- `.env`
- `bot.log`
- `security.log`
- `servers.txt`
- Configuration files such as `twitch_config.json`

The exact information stored depends on the features enabled by the bot operator.

## 9. Data Sharing

v-bot does not intentionally sell, rent, or otherwise monetize personal information.

The project itself does not operate a centralized database containing information from all v-bot installations.

Information processed by an individual v-bot instance may be transmitted to third-party services when required for functionality.

Examples include:

- Discord API — for Discord-related functionality.
- Twitch API — for Twitch-related functionality.

These services have their own privacy policies and terms.

## 10. Data Retention

Data retention depends on the feature and configuration.

Temporary data may be removed automatically when it expires or when the bot restarts.

Logs and configuration files may remain on the hosting machine until they are manually deleted by the bot operator.

The operator of a specific v-bot instance is responsible for managing locally stored data.

## 11. Data Security

Users operating v-bot are responsible for securing their installation.

Recommended measures include:

- Keeping `.env` private.
- Never sharing Discord or Twitch credentials.
- Restricting access to the machine hosting the bot.
- Using appropriate file permissions.
- Keeping dependencies updated.
- Using the minimum Discord permissions required.
- Disabling sensitive features when they are not needed.

No software can guarantee absolute security.

## 12. Third-Party Services

v-bot relies on third-party services, including Discord and Twitch.

Information sent to these services is subject to their respective policies.

v-bot does not control how these third-party services process information.

## 13. Children's Privacy

v-bot is not specifically designed to collect personal information from children.

The bot operator is responsible for ensuring that their use of v-bot complies with applicable privacy laws and platform requirements.

## 14. Your Rights

Depending on applicable law, individuals may have rights regarding their personal information, including rights to access, correct, or delete information.

Because v-bot is self-hosted, requests concerning data stored by a particular instance should generally be directed to the operator of that instance.

## 15. Changes to This Privacy Policy

This Privacy Policy may be updated when necessary.

The latest version will be published in this repository.

## 16. Contact

For questions regarding the v-bot project or this Privacy Policy, please use the project's GitHub repository:

https://github.com/vzsca/v-bot

## 17. Acceptance

By installing or using v-bot, you acknowledge that you have read and understood this Privacy Policy.
