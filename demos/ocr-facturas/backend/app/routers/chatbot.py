"""Chatbot API router - natural language query endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_chatbot_db, get_db
from app.core.exceptions import ChatbotError, CredentialsNotConfiguredError
from app.schemas.chatbot import ChatbotQueryRequest, ChatbotQueryResponse
from app.services.chatbot_service import process_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_model=ChatbotQueryResponse)
async def query_chatbot(
    request: ChatbotQueryRequest,
    db: AsyncSession = Depends(get_db),
    chatbot_db: AsyncSession = Depends(get_chatbot_db),
) -> ChatbotQueryResponse:
    """Submit a natural-language question about invoice data.

    The chatbot engine will:
    1. Classify the user's intent using MaaS LLM
    2. Extract parameters from the question
    3. Execute a safe, parameterized database query
    4. Generate a natural-language response

    Returns the response, identified intent, and query log ID.
    """
    try:
        return await process_query(db, chatbot_db, request.question)
    except CredentialsNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=e.message)
    except ChatbotError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("Chatbot query failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Chatbot is temporarily unavailable")
