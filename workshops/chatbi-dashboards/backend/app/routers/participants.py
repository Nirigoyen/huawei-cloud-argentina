"""Participant join: workshop code + name -> signed session cookie."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import COOKIE_NAME, create_session_token
from app.db.models import Participant, Workshop
from app.db.session import get_session

router = APIRouter(prefix="/participants", tags=["participants"])


class JoinBody(BaseModel):
    code: str
    name: str


class JoinOut(BaseModel):
    participant_id: str
    name: str
    workshop_id: str
    workshop_name: str
    workshop_code: str


@router.post("/join", response_model=JoinOut)
async def join(body: JoinBody, response: Response, session: AsyncSession = Depends(get_session)):
    w = await session.scalar(select(Workshop).where(Workshop.code == body.code))
    if not w:
        raise HTTPException(404, "Workshop code not found")
    # Create or retrieve the participant (unique per workshop+name).
    p = await session.scalar(
        select(Participant).where(Participant.workshop_id == w.id, Participant.name == body.name)
    )
    if not p:
        p = Participant(workshop_id=w.id, name=body.name)
        session.add(p)
        await session.commit()
        await session.refresh(p)

    response.set_cookie(
        key=COOKIE_NAME,
        value=create_session_token(p.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,  # 1 day
        path="/",
    )
    return JoinOut(
        participant_id=str(p.id),
        name=p.name,
        workshop_id=str(w.id),
        workshop_name=w.name,
        workshop_code=w.code,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
