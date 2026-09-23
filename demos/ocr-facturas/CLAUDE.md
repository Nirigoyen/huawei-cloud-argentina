# OCR Facturas — Contexto para Agentes de IA

## Propósito

Demo de un pipeline de procesamiento de facturas argentinas que combina OCR de Huawei Cloud, workflows de Dify con LLM (GLM-5.2 vía MaaS), y un chatbot para consultar los datos extraídos.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), Alembic, asyncpg, httpx
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS 4, Zustand, Recharts
- **Workflow Engine**: Dify 1.0.0 (API + Worker + Web + Sandbox + Plugin Daemon)
- **OCR**: Huawei Cloud OCR (General Text Recognition) vía IAM auth
- **LLM**: GLM-5.2 vía Huawei Cloud MaaS (OpenAI-compatible API)
- **Database**: PostgreSQL 16 (app) + PostgreSQL 16 (Dify) + Redis 7 + Weaviate 1.25
- **Containers**: Docker + docker-compose

## Cómo correr

```bash
cp .env.example .env  # configurar credenciales de Huawei Cloud y MaaS
docker compose up -d  # levanta toda la stack
# Importar "OCR Test.yml" en Dify UI (http://localhost:3001)
# Copiar DIFY_API_KEY a .env y reiniciar backend
```

## Estructura clave

- `backend/app/services/ocr_service.py` — integración con Huawei Cloud OCR
- `backend/app/services/dify_service.py` — cliente del workflow de Dify
- `backend/app/services/dify_workflow_service.py` — orquestación del workflow OCR + LLM
- `backend/app/services/chatbot_service.py` — chatbot con intent classification vía MaaS
- `backend/app/services/invoice_service.py` — CRUD y procesamiento de facturas
- `backend/app/services/data_forward_service.py` — forward de datos a DB destino
- `backend/app/routers/invoices.py` — endpoints de upload y gestión de facturas
- `backend/app/routers/chatbot.py` — endpoint del chatbot
- `backend/app/routers/dashboard.py` — métricas para el dashboard
- `frontend/src/pages/` — páginas: Upload, Invoices, InvoiceDetail, Dashboard, Chatbot, Settings, Workflow
- `dify-nginx.conf` — proxy nginx para Dify (rutas /console/api/, /api/, /v1/, /files/)
- `OCR Test.yml` — definición del workflow de Dify (importar manualmente)

## Convenciones

- Python: `snake_case`, type hints obligatorias, ruff (line-length 100).
- TypeScript: `camelCase` vars/funcs, `PascalCase` componentes, eslint + prettier.
- Commits: Conventional Commits en español.
- Docs en español, código en inglés.

## Tests

```bash
cd backend && pytest
```

Los tests cubren modelos, schemas, security, routers de health e invoices, y chatbot intents.

## Reglas para agentes

1. No commitear secrets — `.env` está gitignored, solo `.env.example` con placeholders.
2. Verificar `ruff check`, `ruff format --check`, `eslint .`, `prettier --check` y `pytest` antes de commitear.
3. El workflow de Dify se importa manualmente — no automatizar la importación.
4. Las credenciales de Huawei Cloud (IAM, Project ID) se inyectan en el workflow de Dify en runtime, no se hardcodean.
5. El chatbot usa MaaS (OpenAI-compatible) — no confundir con el LLM del workflow de Dify.
