"""Organizer endpoints: create workshop, list participants, gallery."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Dashboard, Participant, PgSource, Workshop
from app.db.session import get_session
from app.wren.project import project_path_for

router = APIRouter(prefix="/workshops", tags=["workshops"])


class WorkshopCreate(BaseModel):
    name: str
    code: str


class WorkshopOut(BaseModel):
    id: UUID
    name: str
    code: str
    has_source: bool


class ParticipantOut(BaseModel):
    id: UUID
    name: str


class DashboardOut(BaseModel):
    id: UUID
    name: str
    items: list[dict]


class GalleryParticipant(BaseModel):
    id: UUID
    name: str
    dashboards: list[DashboardOut]


class GalleryOut(BaseModel):
    workshop: WorkshopOut
    participants: list[GalleryParticipant]


@router.post("", response_model=WorkshopOut)
async def create_workshop(body: WorkshopCreate, session: AsyncSession = Depends(get_session)):
    if await session.scalar(select(Workshop).where(Workshop.code == body.code)):
        raise HTTPException(409, "Workshop code already exists")
    w = Workshop(name=body.name, code=body.code, wren_project_path="placeholder")
    session.add(w)
    await session.flush()
    path = project_path_for(str(w.id))
    path.mkdir(parents=True, exist_ok=True)
    w.wren_project_path = str(path)
    await session.commit()
    await session.refresh(w)
    return WorkshopOut(id=w.id, name=w.name, code=w.code, has_source=False)


async def _load_workshop(code: str, session: AsyncSession) -> Workshop:
    w = await session.scalar(select(Workshop).where(Workshop.code == code))
    if not w:
        raise HTTPException(404, "Workshop not found")
    return w


@router.get("/{code}", response_model=WorkshopOut)
async def get_workshop(code: str, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(code, session)
    has_source = bool(await session.scalar(select(PgSource.id).where(PgSource.workshop_id == w.id)))
    return WorkshopOut(id=w.id, name=w.name, code=w.code, has_source=has_source)


@router.get("/{code}/participants", response_model=list[ParticipantOut])
async def list_participants(code: str, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(code, session)
    rows = await session.scalars(select(Participant).where(Participant.workshop_id == w.id).order_by(Participant.created_at))
    return [ParticipantOut(id=p.id, name=p.name) for p in rows]


@router.get("/{code}/gallery", response_model=GalleryOut)
async def gallery(code: str, session: AsyncSession = Depends(get_session)):
    w = await _load_workshop(code, session)
    has_source = bool(await session.scalar(select(PgSource.id).where(PgSource.workshop_id == w.id)))
    parts = await session.scalars(
        select(Participant)
        .where(Participant.workshop_id == w.id)
        .options(selectinload(Participant.dashboards).selectinload(Dashboard.items))
        .order_by(Participant.name)
    )
    out = []
    for p in parts:
        dbs = [
            DashboardOut(id=d.id, name=d.name, items=[{"id": str(i.id), "title": i.title, "layout": i.layout, "chart_spec": i.chart_spec} for i in d.items])
            for d in p.dashboards
        ]
        out.append(GalleryParticipant(id=p.id, name=p.name, dashboards=dbs))
    return GalleryOut(workshop=WorkshopOut(id=w.id, name=w.name, code=w.code, has_source=has_source), participants=out)
