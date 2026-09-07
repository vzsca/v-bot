# Security notes

## Permissions

Moderation commands use centralized checks plus Discord member/role hierarchy validation. The bot never exposes raw exception text to Discord users.

## Owner UI

Interactive owner panels verify both permanent-owner status and the owner ID that created the session on every interaction.

## Announcements

Announcement records are isolated by `guild_id`. A platform integration also verifies that the destination channel belongs to the configured guild before sending. Storage uses atomic replacement and a shared store module.

Existing legacy announcement records without `guild_id` are intentionally ignored for safety; recreate them from the server where they belong.

## Snipe

Deleted-message snapshots are only available to users with `Manage Messages` (or owner authorization) and are retained in memory for a limited period.

## Sensitive commands

`raid`, `remove_raid`, `dmall`, and `spam` are in a separate Cog and are disabled by default. Invalid amounts are rejected rather than silently clamped.

## Local panel

The local panel can modify the bot's `.env` and therefore must be treated as a full administrative surface. Do not expose it through an unauthenticated network service.
