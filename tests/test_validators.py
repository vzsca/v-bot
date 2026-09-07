import pytest

from validators import bounded_text, discord_id


def test_discord_id_accepts_snowflake_shape():
    assert discord_id("123456789012345678") == 123456789012345678


@pytest.mark.parametrize("value", ["0", "123", "abc", "-123", "12345678901234567890123"])
def test_discord_id_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        discord_id(value)


def test_bounded_text_rejects_nul():
    with pytest.raises(ValueError):
        bounded_text("hello\x00world")


def test_bounded_text_enforces_length():
    with pytest.raises(ValueError):
        bounded_text("", minimum=1)
