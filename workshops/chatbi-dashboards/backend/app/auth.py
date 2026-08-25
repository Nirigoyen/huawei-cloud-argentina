"""Participant session auth via signed cookie (workshop code + name)."""

from __future__ import annotations

import hashlib
import hmac
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Participant
from app.db.session import get_session

COOKIE_NAME = "wp_session"


def _sign(payload: str) -> str:
    sig = hmac.new(
        settings.session_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{sig}"


def _verify(token: str) -> str | None:
    try:
        payload, sig = token.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(
        settings.session_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return payload if hmac.compare_digest(sig, expected) else None


def create_session_token(participant_id: UUID) -> str:
    return _sign(str(participant_id))


def parse_session_token(token: str) -> UUID | None:
    payload = _verify(token)
    if not payload:
        return None
    try:
        return UUID(payload)
    except ValueError:
        return None


async def get_current_participant_id(
    wp_session: str | None = Cookie(default=None),
) -> UUID:
    if not wp_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    pid = parse_session_token(wp_session)
    if not pid:
        raise HTTPException(status_code=401, detail="Invalid session")
    return pid


async def get_current_participant(
    pid: UUID = Depends(get_current_participant_id),
    session: AsyncSession = Depends(get_session),
) -> Participant:
    p = await session.get(Participant, pid)
    if not p:
        raise HTTPException(status_code=401, detail="Participant not found")
    return p
