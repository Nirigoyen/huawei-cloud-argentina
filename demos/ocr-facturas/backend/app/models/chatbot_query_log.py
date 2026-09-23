"""ChatbotQueryLog SQLAlchemy ORM model.

Stores a log of all chatbot queries for audit and analytics purposes.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ChatbotQueryLog(UUIDPrimaryKeyMixin, Base):
    """ORM model for the chatbot_query_logs table.

    Stores a record of each chatbot query for audit, debugging,
    and analytics purposes.

    Attributes:
        id: UUID primary key (server-generated).
        question: The user's natural-language question (max 1000 chars).
        identified_intent: The intent identified by the LLM (max 50 chars).
        query_parameters: JSONB object with extracted parameters.
        result_summary: Brief summary of the query result.
        response_text: The natural-language response sent to the user.
        created_at: Timestamp when the query was logged.
    """

    __tablename__ = "chatbot_query_logs"

    question: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="User's natural-language question",
    )
    identified_intent: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Intent identified by the LLM",
    )
    query_parameters: Mapped[Any] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="JSONB object with extracted parameters",
    )
    result_summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Brief summary of the query result",
    )
    response_text: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        doc="Natural-language response sent to the user",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when the query was logged",
    )

    # --- Table constraints and indexes ---
    __table_args__ = (
        Index(
            "ix_chatbot_logs_created_at",
            "created_at",
            postgresql_using="btree",
        ),
    )

    def __repr__(self) -> str:
        return f"<ChatbotQueryLog(id={self.id}, intent='{self.identified_intent}')>"
