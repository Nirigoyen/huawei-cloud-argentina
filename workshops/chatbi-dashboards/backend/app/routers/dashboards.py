"""Participant dashboards CRUD + layout."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_participant
from app.db.models import Dashboard, DashboardItem, Participant
from app.db.session import get_session

router = APIRouter(prefix="/me/dashboards", tags=["dashboards"])


class DashboardCreate(BaseModel):
    name: str = "Untitled dashboard"


class ItemCreate(BaseModel):
    title: str
    sql: str | None = None
    chart_spec: dict | None = None
    layout: dict


class ItemLayoutUpdate(BaseModel):
    layout: dict


class ItemOut(BaseModel):
    id: UUID
    title: str
    sql: str | None = None
    chart_spec: dict | None = None
    layout: dict

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    id: UUID
    name: str
    items: list[ItemOut]


@router.get("", response_model=list[DashboardOut])
async def list_dashboards(participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    rows = await session.scalars(
        select(Dashboard).where(Dashboard.participant_id == participant.id).options(selectinload(Dashboard.items))
    )
    return [DashboardOut(id=d.id, name=d.name, items=[ItemOut.model_validate(i, from_attributes=True) for i in d.items]) for d in rows]


@router.post("", response_model=DashboardOut)
async def create_dashboard(body: DashboardCreate, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    d = Dashboard(participant_id=participant.id, name=body.name)
    session.add(d)
    await session.commit()
    await session.refresh(d)
    return DashboardOut(id=d.id, name=d.name, items=[])


async def _load_owned_dashboard(did: UUID, participant: Participant, session: AsyncSession) -> Dashboard:
    d = await session.scalar(
        select(Dashboard).where(Dashboard.id == did, Dashboard.participant_id == participant.id).options(selectinload(Dashboard.items))
    )
    if not d:
        raise HTTPException(404, "Dashboard not found")
    return d


@router.get("/{did}", response_model=DashboardOut)
async def get_dashboard(did: UUID, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    d = await _load_owned_dashboard(did, participant, session)
    return DashboardOut(id=d.id, name=d.name, items=[ItemOut.model_validate(i, from_attributes=True) for i in d.items])


@router.delete("/{did}")
async def delete_dashboard(did: UUID, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    d = await _load_owned_dashboard(did, participant, session)
    await session.delete(d)
    await session.commit()
    return {"ok": True}


@router.post("/{did}/items", response_model=ItemOut)
async def add_item(did: UUID, body: ItemCreate, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    d = await _load_owned_dashboard(did, participant, session)
    item = DashboardItem(dashboard_id=d.id, title=body.title, sql=body.sql, chart_spec=body.chart_spec, layout=body.layout)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.put("/{did}/items/{item_id}", response_model=ItemOut)
async def update_item(did: UUID, item_id: UUID, body: ItemLayoutUpdate, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    item = await session.scalar(select(DashboardItem).where(DashboardItem.id == item_id, DashboardItem.dashboard_id == did))
    if not item:
        raise HTTPException(404, "Item not found")
    # Verify ownership
    d = await session.scalar(select(Dashboard).where(Dashboard.id == did, Dashboard.participant_id == participant.id))
    if not d:
        raise HTTPException(404, "Dashboard not found")
    item.layout = body.layout
    await session.commit()
    await session.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.delete("/{did}/items/{item_id}")
async def delete_item(did: UUID, item_id: UUID, participant: Participant = Depends(get_current_participant), session: AsyncSession = Depends(get_session)):
    d = await _load_owned_dashboard(did, participant, session)
    item = await session.scalar(select(DashboardItem).where(DashboardItem.id == item_id, DashboardItem.dashboard_id == d.id))
    if item:
        await session.delete(item)
        await session.commit()
    return {"ok": True}
