"""Sensitive-action authorization and security helpers."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from pathlib import Path

import discord

from safe_json import JsonStoreError, atomic_write, load_object

import config
import security_log


_ACTION_CODE_FILE = Path(__file__).resolve().parent.parent / "action_codes.json"
_ACTION_CODE_LOCK = threading.RLock()
_CODE_PATTERN = re.compile(r"^\d{6}$")
_ALLOWED_ACTIONS = frozenset({"spam", "dmall", "raid", "remove_raid"})


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def _load_codes() -> dict:
    try:
        data = load_object(_ACTION_CODE_FILE, {})
    except JsonStoreError:
        return {}
    if not isinstance(data, dict):
        return {}
    codes = data.get("codes", {})
    return codes if isinstance(codes, dict) else {}


def _save_codes(codes: dict) -> None:
    atomic_write(_ACTION_CODE_FILE, {"codes": codes}, mode=0o600 if config.IS_POSIX else None)


def issue_action_code(action: str) -> tuple[str, int]:
    """Create a short-lived one-time code scoped to one sensitive action."""
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported sensitive action: {action}")
    code = f"{secrets.randbelow(900_000) + 100_000:06d}"
    expires_at = int(time.time() + config.ACTION_CODE_TTL)
    with _ACTION_CODE_LOCK:
        codes = _load_codes()
        codes = {
            key: value
            for key, value in codes.items()
            if isinstance(value, dict) and isinstance(value.get("expires_at"), int) and value["expires_at"] > int(time.time())
        }
        codes[action] = {"code_hash": _code_hash(code), "expires_at": expires_at}
        _save_codes(codes)
    return code, expires_at


def _consume_action_code(code: str, action: str) -> bool:
    if action not in _ALLOWED_ACTIONS or not _CODE_PATTERN.fullmatch(code):
        return False
    with _ACTION_CODE_LOCK:
        codes = _load_codes()
        data = codes.get(action)
        if not isinstance(data, dict):
            return False
        expected = data.get("code_hash")
        expires_at = data.get("expires_at")
        if not isinstance(expected, str) or not isinstance(expires_at, int):
            return False
        if expires_at <= int(time.time()):
            codes.pop(action, None)
            try:
                _save_codes(codes)
            except JsonStoreError:
                pass
            return False
        valid = hmac.compare_digest(_code_hash(code), expected)
        if valid:
            codes.pop(action, None)
            _save_codes(codes)
        return valid


async def require_action_code(ctx, action: str) -> bool:
    """Require a one-time six-digit code generated for this exact sensitive action."""
    await ctx.send(
        "🔐 This action requires a one-time 6-digit security code. "
        f"Run `action_code {action}` in the local panel, then send the code here within 60 seconds."
    )
    attempts = 0
    deadline = time.monotonic() + config.ACTION_CODE_INPUT_TIMEOUT
    while attempts < config.ACTION_CODE_MAX_ATTEMPTS:
        attempts += 1
        remaining = max(0.1, deadline - time.monotonic())
        try:
            message = await ctx.bot.wait_for(
                "message",
                timeout=remaining,
                check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
            )
        except TimeoutError:
            await ctx.send("⏰ Security code entry timed out.")
            return False
        code = message.content.strip()
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        try:
            valid = _consume_action_code(code, action)
        except JsonStoreError:
            valid = False
        if valid:
            security_log.log_security_event(
                f"Sensitive action authorized: {action}",
                actor=f"{ctx.author} ({ctx.author.id})",
            )
            return True
        if attempts < config.ACTION_CODE_MAX_ATTEMPTS:
            await ctx.send(f"❌ Invalid security code for `{action}`. Attempt {attempts}/{config.ACTION_CODE_MAX_ATTEMPTS}.")
    await ctx.send("❌ Too many invalid security code attempts. Generate a new code in the local panel.")
    return False
