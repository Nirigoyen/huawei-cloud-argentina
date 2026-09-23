"""Chatbot service - orchestrates intent classification and query execution.

Flow:
1. Send user question to MaaS LLM for intent classification
2. Extract intent name and parameters from LLM response
3. Map intent to SQL template
4. Execute parameterized query via query_executor
5. Format natural-language response
6. Log the query for audit
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    ChatbotError,
    CredentialsNotConfiguredError,
)
from app.models.chatbot_query_log import ChatbotQueryLog
from app.schemas.chatbot import ChatbotQueryResponse, IntentClassification
from app.services.chatbot.intents import INTENT_DEFINITIONS, get_intent_descriptions_for_prompt
from app.services.chatbot.query_executor import execute_query

logger = logging.getLogger(__name__)


# System prompt for intent classification
INTENT_CLASSIFICATION_PROMPT = """
Eres un asistente de consulta de facturas. Tu trabajo es identificar la intención del usuario
a partir de su pregunta en lenguaje natural y extraer los parámetros relevantes.

INTENCIONES SOPORTADAS:
{intent_list}

RESPONDE EN FORMATO JSON:
{{
  "intent": "<nombre_de_intención o null>",
  "parameters": {{ <parámetros extraídos> }},
  "is_read_only": true
}}

REGLAS:
- Solo identifica intenciones de la lista INTENCIONES SOPORTADAS arriba
- Si la pregunta implica modificación de datos (eliminar, actualizar, insertar, crear), establece intent a null
- Si no puedes identificar una intención válida, establece intent a null
- Extrae parámetros de período como: {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
  cuando se dan fechas específicas
- Para períodos relativos como "este mes", usa:
  {{"start_date": "first day of current month", "end_date": "last day of current month"}}
- Para "este año", usa: {{"start_date": "YYYY-01-01", "end_date": "YYYY-12-31"}}
- Para "el mes pasado", usa el primer y último día del mes anterior
- Para top_suppliers, el límite por defecto es 5 si no se especifica
- Para supplier_spending, establece supplier_pattern a "%nombre_proveedor%" para coincidencia ILIKE
- Todas las intenciones son de solo lectura (is_read_only: true)
- Responde SIEMPRE en español. Las preguntas del usuario serán en español.
- Fecha de hoy: {today}
"""

# System prompt for response generation
RESPONSE_GENERATION_PROMPT = """
Eres un asistente de datos de facturas. Basándote en la pregunta del usuario y los resultados
de la consulta, generá una respuesta clara en lenguaje natural en español.

REGLAS:
- Usá SOLAMENTE los datos de los resultados. No inventes información.
- Formateá montos como "ARS X.XXX,XX" (punto como separador de miles, coma como decimal)
- Formateá fechas como "DD/MM/YYYY"
- Sé conciso pero informativo
- Si los resultados están vacíos, decí "No se encontraron facturas que coincidan con los criterios."
- Respondé en español
"""


async def process_query(
    db: AsyncSession,
    chatbot_db: AsyncSession,
    question: str,
) -> ChatbotQueryResponse:
    """Process a natural-language chatbot query.

    Args:
        db: Main database session (for logging).
        chatbot_db: Read-only chatbot database session.
        question: User's natural-language question.

    Returns:
        ChatbotQueryResponse with the natural-language answer.
    """
    settings = get_settings()

    # Step 1: Classify intent via LLM
    intent_result = await _classify_intent(question)

    if intent_result.intent is None or intent_result.intent not in INTENT_DEFINITIONS:
        # Intent not recognized - return helpful guidance
        response_text = _get_unrecognized_intent_response()
        log_id = await _log_query(db, question, None, {}, None, response_text)
        return ChatbotQueryResponse(
            response=response_text,
            intent=None,
            query_log_id=log_id,
        )

    intent_name = intent_result.intent
    intent_def = INTENT_DEFINITIONS[intent_name]
    params = intent_result.parameters

    # Step 2: Resolve date parameters
    params = _resolve_date_params(params)

    # Step 3: Add derived parameters (e.g., supplier_pattern from supplier_name)
    if intent_name == "supplier_spending" and "supplier_name" in params:
        name = params["supplier_name"]
        params["supplier_pattern"] = f"%{name}%"

    if intent_name == "top_suppliers" and "limit" not in params:
        params["limit"] = 5

    # Step 3b: Ensure numeric params are proper types (LLM may return strings)
    for numeric_key in ("limit", "amount"):
        if numeric_key in params and isinstance(params[numeric_key], str):
            try:
                # Remove commas/spaces from numbers like "1,000,000"
                cleaned = params[numeric_key].replace(",", "").replace(" ", "")
                params[numeric_key] = float(cleaned)
                if params[numeric_key] == int(params[numeric_key]):
                    params[numeric_key] = int(params[numeric_key])
            except (ValueError, TypeError):
                pass

    # Step 4: Execute the parameterized query
    try:
        rows = await execute_query(
            chatbot_db,
            intent_def.sql_template,
            params,
        )
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        log_id = await _log_query(db, question, intent_name, params, None, error_msg)
        return ChatbotQueryResponse(response=error_msg, intent=intent_name, query_log_id=log_id)

    # Step 5: Generate natural-language response
    result_summary = json.dumps(rows[:20], default=str) if rows else "No results"
    response_text = await _generate_response(question, rows, result_summary)

    # Step 6: Log the query (serialize params for JSONB storage)
    log_params = {k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in params.items()}
    log_id = await _log_query(db, question, intent_name, log_params, result_summary, response_text)

    return ChatbotQueryResponse(
        response=response_text,
        intent=intent_name,
        query_log_id=log_id,
    )


async def _classify_intent(question: str) -> IntentClassification:
    """Send question to MaaS LLM for intent classification.

    Args:
        question: User's question.

    Returns:
        IntentClassification with identified intent and parameters.
    """
    settings = get_settings()

    if not settings.is_maas_configured:
        raise CredentialsNotConfiguredError("MaaS API is not configured. Please set MAAS_API_KEY in Settings.")

    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        intent_list=get_intent_descriptions_for_prompt(),
        today=datetime.now().strftime("%Y-%m-%d"),
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.maas_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.maas_api_key}"},
                json={
                    "model": settings.maas_model_name,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": question},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"].get("content")

        if not content or not content.strip():
            logger.warning("LLM returned empty content for intent classification")
            return IntentClassification(intent=None, parameters={})

        # Parse JSON from LLM response
        # Handle cases where LLM wraps JSON in markdown code blocks
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)
        return IntentClassification(**parsed)

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to parse LLM intent response: %s", str(e))
        return IntentClassification(intent=None, parameters={})
    except httpx.HTTPError as e:
        logger.error("MaaS API call failed: %s", str(e))
        raise ChatbotError(f"Failed to classify intent: {str(e)}")


async def _generate_response(
    question: str,
    rows: list[dict[str, Any]],
    result_summary: str,
) -> str:
    """Generate a natural-language response using MaaS LLM.

    Args:
        question: Original user question.
        rows: Query result rows.
        result_summary: JSON string of results.

    Returns:
        Natural-language response string.
    """
    settings = get_settings()

    if not settings.is_maas_configured:
        # Fallback: return raw results
        return f"Query results: {result_summary}"

    system_prompt = RESPONSE_GENERATION_PROMPT

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.maas_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.maas_api_key}"},
                json={
                    "model": settings.maas_model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Pregunta: {question}\n\nResultados de la consulta:\n{result_summary}",
                        },
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
            )
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"].get("content")
        if not content or not content.strip():
            return f"Procesé tu consulta pero no pude generar una respuesta. Datos encontrados: {result_summary}"
        return content

    except Exception as e:
        logger.error("Response generation failed: %s", str(e))
        return f"Query results: {result_summary}"


def _resolve_date_params(params: dict[str, Any]) -> dict[str, Any]:
    """Resolve relative date parameters to absolute dates.

    Handles: "first day of current month", "last day of current month", etc.
    Also provides defaults for missing date parameters (wide range).
    """
    import calendar
    from datetime import date

    today = date.today()
    resolved = {}

    for key, value in params.items():
        # Skip non-string, non-dict values (keep as-is)
        if isinstance(value, dict):
            # LLM sometimes returns empty dict {} for dates — skip it
            continue
        if value is None:
            continue
        if not isinstance(value, str):
            resolved[key] = value
            continue

        v = value.lower().strip()

        if not v:
            continue
        elif v == "first day of current month":
            resolved[key] = date(today.year, today.month, 1).isoformat()
        elif v == "last day of current month":
            last_day = calendar.monthrange(today.year, today.month)[1]
            resolved[key] = date(today.year, today.month, last_day).isoformat()
        elif v == "first day of current year":
            resolved[key] = date(today.year, 1, 1).isoformat()
        elif v == "last day of current year":
            resolved[key] = date(today.year, 12, 31).isoformat()
        elif v == "first day of last month":
            if today.month == 1:
                resolved[key] = date(today.year - 1, 12, 1).isoformat()
            else:
                resolved[key] = date(today.year, today.month - 1, 1).isoformat()
        elif v == "last day of last month":
            if today.month == 1:
                last_day = calendar.monthrange(today.year - 1, 12)[1]
                resolved[key] = date(today.year - 1, 12, last_day).isoformat()
            else:
                last_day = calendar.monthrange(today.year, today.month - 1)[1]
                resolved[key] = date(today.year, today.month - 1, last_day).isoformat()
        else:
            # Keep the value as-is (might be a YYYY-MM-DD date or other param)
            resolved[key] = value

    # Default missing date parameters to wide range
    if "start_date" not in resolved:
        resolved["start_date"] = "2000-01-01"
    if "end_date" not in resolved:
        resolved["end_date"] = today.isoformat()

    # Convert string dates to date objects (asyncpg requires date objects for DATE columns)
    for date_key in ("start_date", "end_date"):
        if date_key in resolved and isinstance(resolved[date_key], str):
            try:
                resolved[date_key] = date.fromisoformat(resolved[date_key])
            except (ValueError, TypeError):
                pass

    return resolved


def _get_unrecognized_intent_response() -> str:
    """Return a helpful response when intent is not recognized."""
    examples = []
    for name, intent in INTENT_DEFINITIONS.items():
        if intent.example_questions:
            examples.append(f"- {intent.example_questions[0]}")

    return (
        "Lo siento, no pude entender tu pregunta. "
        "Aquí hay algunos ejemplos de lo que puedo responder:\n\n" + "\n".join(examples)
    )


async def _log_query(
    db: AsyncSession,
    question: str,
    intent: str | None,
    params: dict[str, Any],
    result_summary: str | None,
    response_text: str,
) -> uuid.UUID:
    """Log a chatbot query to the database.

    Returns the log entry ID.
    """
    log_entry = ChatbotQueryLog(
        question=question,
        identified_intent=intent,
        query_parameters=params if params else None,
        result_summary=result_summary[:500] if result_summary else None,
        response_text=response_text[:2000] if response_text else None,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry.id
