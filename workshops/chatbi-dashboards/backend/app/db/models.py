"""SQLAlchemy models for the app metadata DB."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> UUID:
    return uuid4()


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    wren_project_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pg_source: Mapped[PgSource | None] = relationship(
        back_populates="workshop", uselist=False, cascade="all, delete-orphan"
    )
    participants: Mapped[list[Participant]] = relationship(
        back_populates="workshop", cascade="all, delete-orphan"
    )


class PgSource(Base):
    __tablename__ = "pg_sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    workshop_id: Mapped[UUID] = mapped_column(
        ForeignKey("workshops.id", ondelete="CASCADE"), index=True
    )
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(default=5432)
    database: Mapped[str] = mapped_column(String(255))
    user: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(Text)  # workshop scenario creds; rotate per event
    schema: Mapped[str] = mapped_column(String(255), default="public")

    workshop: Mapped[Workshop] = relationship(back_populates="pg_source")


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("workshop_id", "name", name="uq_workshop_participant_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    workshop_id: Mapped[UUID] = mapped_column(
        ForeignKey("workshops.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workshop: Mapped[Workshop] = relationship(back_populates="participants")
    threads: Mapped[list[Thread]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    dashboards: Mapped[list[Dashboard]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    participant_id: Mapped[UUID] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participant: Mapped[Participant] = relationship(back_populates="threads")
    messages: Mapped[list[Message]] = relationship(
        back_populates="thread", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    thread_id: Mapped[UUID] = mapped_column(
        ForeignKey("threads.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))  # user | assistant
    content: Mapped[str | None] = mapped_column(Text)
    sql: Mapped[str | None] = mapped_column(Text)
    chart_spec: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thread: Mapped[Thread] = relationship(back_populates="messages")


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    participant_id: Mapped[UUID] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), default="Untitled dashboard")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participant: Mapped[Participant] = relationship(back_populates="dashboards")
    items: Mapped[list[DashboardItem]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan"
    )


class DashboardItem(Base):
    __tablename__ = "dashboard_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid)
    dashboard_id: Mapped[UUID] = mapped_column(
        ForeignKey("dashboards.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    sql: Mapped[str | None] = mapped_column(Text)
    chart_spec: Mapped[dict | None] = mapped_column(JSONB)
    layout: Mapped[dict] = mapped_column(JSONB)  # {x, y, w, h}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dashboard: Mapped[Dashboard] = relationship(back_populates="items")
