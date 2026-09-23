"""Pydantic schemas for Chatbot API requests and responses."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ChatbotQueryRequest(BaseModel):
    """Request body for chatbot query endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural-language question about invoice data",
    )


class IntentClassification(BaseModel):
    """Result of LLM intent classification."""

    intent: str | None = Field(
        default=None,
        description="Identified intent name, or null if unrecognized",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted parameters for the intent",
    )
    is_read_only: bool = Field(
        default=True,
        description="Whether the query is read-only (always true)",
    )


class QueryResult(BaseModel):
    """Result of executing a parameterized query."""

    intent: str
    parameters: dict[str, Any]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float | None = None


class ChatbotQueryResponse(BaseModel):
    """Response from the chatbot query endpoint."""

    response: str = Field(description="Natural-language response to the user's question")
    intent: str | None = Field(default=None, description="Identified intent, if any")
    query_log_id: uuid.UUID = Field(description="ID of the chatbot query log entry")


class ChatbotIntentInfo(BaseModel):
    """Information about a supported chatbot intent."""

    name: str
    description: str
    example_questions: list[str] = Field(default_factory=list)


class ChatbotCapabilitiesResponse(BaseModel):
    """Response listing supported chatbot capabilities."""

    supported_intents: list[ChatbotIntentInfo]
    message: str = "Here are the types of questions I can answer:"
