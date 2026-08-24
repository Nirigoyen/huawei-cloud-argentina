import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models import ProcessRequest, ProcessResponse
from app.services.anonymizer import anonymize_text, deanonymize_text
from app.services.llm_client import call_llm

router = APIRouter(prefix="/api", tags=["process"])
logger = logging.getLogger(__name__)

session_store: dict[str, dict[str, str]] = {}


@router.post("/process_prompt", response_model=ProcessResponse)
async def process_prompt(request: ProcessRequest):
    original_prompt = request.prompt

    if not original_prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    session_id = str(uuid.uuid4())

    anonymized_prompt, mapping = anonymize_text(original_prompt)
    session_store[session_id] = mapping

    logger.info("Session %s - Anonymization complete. Mapping: %s", session_id, mapping)

    try:
        llm_raw_response = await call_llm(anonymized_prompt)
    except Exception as e:
        logger.error("LLM call failed for session %s: %s", session_id, str(e))
        llm_raw_response = f"[LLM Error] Could not reach the LLM service: {str(e)}"

    final_deanonymized_response = deanonymize_text(llm_raw_response, mapping)

    return ProcessResponse(
        original_prompt=original_prompt,
        anonymized_prompt=anonymized_prompt,
        llm_raw_response=llm_raw_response,
        final_deanonymized_response=final_deanonymized_response,
    )
