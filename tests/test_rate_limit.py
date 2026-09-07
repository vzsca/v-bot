import pytest

import config
from rate_limit import CommandRateLimiter, RateLimitExceeded


def test_command_rate_limiter_blocks_repeated_command():
    limiter = CommandRateLimiter()
    for _ in range(max(2, config.GLOBAL_COMMAND_LIMIT // 2)):
        limiter.check(1, 2, "test")
    with pytest.raises(RateLimitExceeded):
        limiter.check(1, 2, "test")


def test_command_rate_limiter_allows_different_commands_until_global_limit():
    limiter = CommandRateLimiter()
    for index in range(config.GLOBAL_COMMAND_LIMIT):
        limiter.check(1, 2, f"test-{index}")
    with pytest.raises(RateLimitExceeded):
        limiter.check(1, 2, "another")


def test_rate_limits_are_guild_scoped():
    limiter = CommandRateLimiter()
    for _ in range(max(2, config.GLOBAL_COMMAND_LIMIT // 2)):
        limiter.check(1, 2, "test")
    limiter.check(3, 2, "test")
