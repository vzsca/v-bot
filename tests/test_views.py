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
