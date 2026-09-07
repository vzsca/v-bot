import time

import pytest

from state import BotState


def test_temp_owner_rejects_invalid_duration():
    state = BotState()
    with pytest.raises(ValueError):
        state.add_temp_owner(123, 456, 0)


def test_temp_owner_is_valid_until_expiry():
    state = BotState()
    state.add_temp_owner(123, 456, 60)
    assert state.is_temp_authorized(123, 456)
    assert not state.is_temp_authorized(124, 456)


def test_temp_owner_expires():
    state = BotState()
    state.add_temp_owner(123, 456, 1)
    state.temp_authorized_users[(123, 456)] = time.time() - 1
    assert not state.is_temp_authorized(123, 456)
    assert (123, 456) not in state.temp_authorized_users


def test_snipe_bucket_respects_limit():
    state = BotState()
    for i in range(4):
        state.add_sniped(1, {"id": i}, 2)
    assert [x["id"] for x in state.sniped_messages[1]] == [3, 2]


def test_clean_snipes_discards_malformed_entries():
    state = BotState()
    state.sniped_messages[1] = [{"id": 1, "time": "not-a-date"}]
    assert state.clean_snipes(900) == 1
    assert 1 not in state.sniped_messages
