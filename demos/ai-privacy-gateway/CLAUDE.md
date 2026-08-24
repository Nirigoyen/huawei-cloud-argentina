# AI Privacy Gateway — Contexto para Agentes de IA

## Propósito

Demo de un gateway de privacidad que anonimiza PII antes de enviarla a un LLM y reconstruye la respuesta. El LLM nunca recibe datos sensibles.

## Stack

- **Backend**: Python 3.12, FastAPI, Presidio + spaCy (NLP es/en), httpx
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Containers**: Docker + docker-compose

## Cómo correr

```bash
cp .env.example .env  # configurar LLM_API_KEY
make up               # levanta backend (:8000) + frontend (:8080)
```

## Estructura clave

- `backend/app/services/anonymizer.py` — lógica de anonimización (Presidio). El analyzer es **lazy**: no carga modelos de spaCy al importar, solo cuando se usa.
- `backend/app/services/llm_client.py` — cliente HTTP al LLM (API compatible con OpenAI).
- `backend/app/routers/process.py` — endpoint `/api/process_prompt` que orquesta el pipeline.
- `frontend/src/components/` — UI que muestra el pipeline de 4 pasos.

## Convenciones

- Python: `snake_case`, type hints obligatorias en funciones públicas, ruff (line-length 100).
- TypeScript: `camelCase` vars/funcs, `PascalCase` componentes, eslint + prettier.
- Commits: Conventional Commits en español.
- Docs en español, código en inglés.

## Tests

```bash
cd backend && pytest
```

Los tests cubren funciones puras (`detect_language`, `deanonymize_text`) sin necesidad de modelos de spaCy.

## Reglas para agentes

1. No commitear secrets — `.env` está gitignored, solo `.env.example` con placeholders.
2. El analyzer es lazy: si se agregan tests, no requieren modelos de spaCy para funciones puras.
3. Verificar `ruff check`, `eslint .`, `prettier --check` y `pytest` antes de commitear.
