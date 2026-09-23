from types import SimpleNamespace

import discord

from views import ConfirmLeaveView, GuildActionsView


def test_guild_actions_view_has_quit_button():
    guild = SimpleNamespace(id=123)
    view = GuildActionsView(guild, owner_id=456)

    assert any(
        isinstance(item, discord.ui.Button) and item.label == "Quit"
        for item in view.children
    )


def test_confirm_leave_view_has_cancel_and_quit_buttons():
    guild = SimpleNamespace(id=123)
    view = ConfirmLeaveView(guild, owner_id=456)

    labels = {
        item.label
        for item in view.children
        if isinstance(item, discord.ui.Button)
    }

    assert labels == {"Cancel", "Quit"}


def test_server_details_embed_shows_owner_members_and_bot_join_date():
    from datetime import datetime, timezone

    from views import _server_details_embed

    owner = SimpleNamespace(mention="<@111>", __str__=lambda self: "ServerOwner")
    bot_member = SimpleNamespace(
        joined_at=datetime(2026, 9, 23, 9, 30, tzinfo=timezone.utc),
    )
    guild = SimpleNamespace(
        id=123,
        name="Test Server",
        owner_id=111,
        owner=owner,
        member_count=42,
        me=bot_member,
    )

    embed = _server_details_embed(guild)

    assert embed.title == "📌 Test Server"
    assert embed.description == "ID: 123"
    fields = {field.name: field.value for field in embed.fields}
    assert fields["Owner"] == "<@111> (ServerOwner)"
    assert fields["Members"] == "42"
    assert "Bot added" in fields
    assert "2026" in fields["Bot added"]
    assert fields["API configuration"] == "🔴 Disabled"
