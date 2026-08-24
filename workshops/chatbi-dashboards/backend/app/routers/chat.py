"""Chat threads + streaming SSE endpoint."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.chat_agent import build_agent, stream_chat
from app.auth import get_current_participant
from app.db.models import Message, Participant, Thread
from app.db.session import SessionLocal, get_session
from app.wren.project import project_path_for

router = APIRouter(prefix="/chat", tags=["chat"])


class ThreadCreate(BaseModel):
    title: str = "New chat"


class ThreadOut(BaseModel):
    id: UUID
    title: str


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str | None = None
    sql: str | None = None
    chart_spec: dict | None = None


class SendMessage(BaseModel):
    content: str


@router.get("/threads", response_model=list[ThreadOut])
async def list_threads(
    participant: Participant = Depends(get_current_participant),
    session: AsyncSession = Depends(get_session),
):
    rows = await session.scalars(
        select(Thread)
        .where(Thread.participant_id == participant.id)
        .order_by(Thread.created_at.desc())
    )
    return [ThreadOut(id=t.id, title=t.title) for t in rows]


@router.post("/threads", response_model=ThreadOut)
async def create_thread(
    body: ThreadCreate,
    participant: Participant = Depends(get_current_participant),
    session: AsyncSession = Depends(get_session),
):
    t = Thread(participant_id=participant.id, title=body.title)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return ThreadOut(id=t.id, title=t.title)


async def _load_owned_thread(tid: UUID, participant: Participant, session: AsyncSession) -> Thread:
    t = await session.scalar(
        select(Thread)
        .where(Thread.id == tid, Thread.participant_id == participant.id)
        .options(selectinload(Thread.messages))
    )
    if not t:
        raise HTTPException(404, "Thread not found")
    return t


@router.get("/threads/{tid}/messages", response_model=list[MessageOut])
async def list_messages(
    tid: UUID,
    participant: Participant = Depends(get_current_participant),
    session: AsyncSession = Depends(get_session),
):
    t = await _load_owned_thread(tid, participant, session)
    return [
        MessageOut(id=m.id, role=m.role, content=m.content, sql=m.sql, chart_spec=m.chart_spec)
        for m in t.messages
    ]


@router.post("/threads/{tid}/messages")
async def send_message(
    tid: UUID,
    body: SendMessage,
    participant: Participant = Depends(get_current_participant),
    session: AsyncSession = Depends(get_session),
):
    t = await _load_owned_thread(tid, participant, session)

    # Save the user message.
    session.add(Message(thread_id=t.id, role="user", content=body.content))
    await session.commit()

    # Build langchain message history (prior turns + this question).
    lc_messages: list = []
    for m in t.messages:
        if m.role == "user" and m.content:
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant" and m.content:
            lc_messages.append(AIMessage(content=m.content))
    lc_messages.append(HumanMessage(content=body.content))

    project_path = project_path_for(str(participant.workshop_id))
    profile = f"workshop_{participant.workshop_id}"
    agent = build_agent(project_path, profile)

    async def event_stream():
        text_parts: list[str] = []
        last_sql: str | None = None
        last_chart: dict | None = None
        async for ev in stream_chat(agent, lc_messages):
            yield f"data: {json.dumps(ev, default=str)}\n\n"
            if ev.get("type") == "token":
                text_parts.append(ev.get("content", ""))
            elif ev.get("type") == "sql":
                last_sql = ev.get("content")
            elif ev.get("type") == "chart":
                last_chart = ev.get("content")
        # Persist the assistant turn.
        async with SessionLocal() as s:
            s.add(
                Message(
                    thread_id=t.id,
                    role="assistant",
                    content="".join(text_parts) or None,
                    sql=last_sql,
                    chart_spec=last_chart,
                )
            )
            await s.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
