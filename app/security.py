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


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def _load_codes() -> list[dict]:
    try:
        data = load_object(_ACTION_CODE_FILE, {})
    except JsonStoreError:
        return []
    if not isinstance(data, dict):
        return []
    codes = data.get("codes", [])
    if not isinstance(codes, list):
        return []
    return [item for item in codes if isinstance(item, dict)]


def _save_codes(codes: list[dict]) -> None:
    atomic_write(_ACTION_CODE_FILE, {"codes": codes}, mode=0o600 if config.IS_POSIX else None)


def issue_action_code(action: str) -> tuple[str, int]:
    """Create a short-lived one-time code bound to one sensitive action."""
    if not action or not isinstance(action, str):
        raise ValueError("action must be a non-empty string")
    code = f"{secrets.randbelow(900_000) + 100_000:06d}"
    expires_at = int(time.time() + config.ACTION_CODE_TTL)
    with _ACTION_CODE_LOCK:
        now = int(time.time())
        codes = [
            item
            for item in _load_codes()
            if isinstance(item.get("code_hash"), str)
            and isinstance(item.get("action"), str)
            and isinstance(item.get("expires_at"), int)
            and item["expires_at"] > now
        ]
        codes.append({
            "code_hash": _code_hash(code),
            "action": action,
            "expires_at": expires_at,
        })
        _save_codes(codes)
    return code, expires_at


def _consume_action_code(code: str, action: str) -> bool:
    if not _CODE_PATTERN.fullmatch(code) or not isinstance(action, str) or not action:
        return False
    with _ACTION_CODE_LOCK:
        now = int(time.time())
        codes = _load_codes()
        fresh_codes: list[dict] = []
        matched = False
        code_digest = _code_hash(code)
        for item in codes:
            expected = item.get("code_hash")
            expected_action = item.get("action")
            expires_at = item.get("expires_at")
            if (
                not isinstance(expected, str)
                or not isinstance(expected_action, str)
                or not isinstance(expires_at, int)
                or expires_at <= now
            ):
                continue
            if (
                not matched
                and expected_action == action
                and hmac.compare_digest(code_digest, expected)
            ):
                matched = True
                continue
            fresh_codes.append(item)
        if matched or len(fresh_codes) != len(codes):
            _save_codes(fresh_codes)
        return matched


async def require_action_code(ctx, action: str) -> bool:
    """Require a one-time six-digit code generated for the requested action."""
    await ctx.send(
        f"🔐 This action (`{action}`) requires a one-time 6-digit security code. "
        "Run `action_code` in the local panel, then send the code here within 60 seconds."
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
            await ctx.send(f"❌ Invalid security code. Attempt {attempts}/{config.ACTION_CODE_MAX_ATTEMPTS}.")
    await ctx.send("❌ Too many invalid security code attempts. Generate a new code in the local panel.")
    return False
