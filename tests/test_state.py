import pytest

from state import BotState


def test_temp_owner_rejects_invalid_duration():
    state = BotState()
    with pytest.raises(ValueError):
        state.add_temp_owner(123, 0)


def test_temp_owner_is_valid_until_expiry():
    state = BotState()
    state.add_temp_owner(123, 60)
    assert state.is_temp_authorized(123)


def test_snipe_bucket_respects_limit():
    state = BotState()
    for i in range(4):
        state.add_sniped(1, {"id": i}, 2)
    assert [x["id"] for x in state.sniped_messages[1]] == [3, 2]
