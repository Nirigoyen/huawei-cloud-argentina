# OCR Facturas — Demo de Procesamiento de Facturas con OCR + LLM

> Pipeline de procesamiento de facturas argentinas usando OCR de Huawei Cloud, Dify workflows y GLM-5.2 vía MaaS.

## Descripción

Esta demo procesa facturas (PDF o imágenes) de forma automática:

1. **Upload** — el usuario sube una factura (PDF, PNG, JPG).
2. **OCR** — Huawei Cloud OCR extrae el texto de la factura.
3. **LLM Parsing** — un workflow de Dify con un LLM (GLM-5.2 vía MaaS) estructura los datos extraídos (emisor, receptor, items, totales, CUIT, fecha, etc.).
4. **Storage** — los datos estructurados se guardan en PostgreSQL.
5. **Chatbot** — un chatbot permite consultar las facturas procesadas en lenguaje natural.
6. **Dashboard** — visualizaciones de métricas: facturas por mes, por tipo, top proveedores, montos.

## Stack

| Componente        | Tecnología                                            |
| ----------------- | ----------------------------------------------------- |
| Backend           | Python 3.12, FastAPI, SQLAlchemy (async), Alembic     |
| Frontend          | React 19, TypeScript, Vite, Tailwind CSS, Zustand     |
| Database          | PostgreSQL 16                                         |
| Workflow Engine   | Dify 1.0.0 (API + Worker + Web + Sandbox + Plugins)   |
| OCR               | Huawei Cloud OCR (General Text Recognition)           |
| LLM               | GLM-5.2 vía Huawei Cloud MaaS (OpenAI-compatible API) |
| Vector DB         | Weaviate (para Dify)                                  |
| Containers        | Docker + docker-compose                               |

## Arquitectura

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│ Backend  │────▶│  Dify    │────▶│ Huawei   │
│ (React)  │     │ (FastAPI)│     │ Workflow │     │ OCR API  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                        │                │
                        ▼                ▼
                 ┌──────────┐    ┌──────────┐
                 │PostgreSQL│    │  GLM-5.2 │
                 │ (app DB) │    │  (MaaS)  │
                 └──────────┘    └──────────┘
```

## Quickstart

```bash
# 1. Clonar y configurar
cd demos/ocr-facturas
cp .env.example .env
# Editar .env con tus credenciales de Huawei Cloud y MaaS

# 2. Levantar todos los servicios
docker compose up -d

# 3. Importar el workflow de Dify
#    - Abrir http://localhost:3001 (Dify Web UI)
#    - Crear cuenta / login
#    - Importar "OCR Test.yml" como workflow
#    - Copiar el API key del workflow a .env (DIFY_API_KEY)
#    - Reiniciar backend: docker compose restart backend

# 4. Acceder a la aplicación
#    - Frontend: http://localhost:3000
#    - API:      http://localhost:8000
#    - Dify UI:  http://localhost:3001
```

## Servicios

| Servicio           | Puerto | Descripción                              |
| ------------------ | ------ | ---------------------------------------- |
| Frontend           | 3000   | React app (nginx)                        |
| Backend (API)      | 8000   | FastAPI REST API                         |
| Dify Web UI        | 3001   | Dify workflow management                 |
| Dify API           | 5001   | Dify workflow engine (internal)          |
| PostgreSQL (app)   | 5432   | Application database                     |

## Variables de entorno

Ver `.env.example` para la lista completa. Las variables clave:

- `HWCLOUD_IAM_USERNAME` / `HWCLOUD_IAM_PASSWORD` — credenciales IAM de Huawei Cloud
- `HWCLOUD_PROJECT_ID` — Project ID de Huawei Cloud
- `MAAS_API_KEY` — API key de MaaS para el chatbot
- `DIFY_API_KEY` — API key del workflow de Dify (se obtiene al importar el workflow)

## Estructura

```
ocr-facturas/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── core/         # config, database, auth, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # business logic (OCR, Dify, chatbot, etc.)
│   ├── alembic/          # DB migrations
│   ├── tests/            # pytest tests
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── api/          # API clients
│   │   ├── components/   # UI components
│   │   ├── pages/        # Route pages
│   │   ├── stores/       # Zustand stores
│   │   └── types/        # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml    # Full stack orchestration
├── dify-nginx.conf       # Nginx proxy for Dify services
├── OCR Test.yml          # Dify workflow definition (import manually)
├── dify_cleanup_node.py  # Dify cleanup node script
├── dify_llm_prompt.txt   # LLM prompt for invoice parsing
├── .env.example          # Environment variables template
└── CLAUDE.md             # Context for AI agents
```

## Desarrollo

### Backend

```bash
cd backend
pip install -e ".[dev]"
pytest                    # run tests
ruff check .              # lint
ruff format .             # format
```

### Frontend

```bash
cd frontend
npm ci
npm run dev               # dev server (Vite)
npm run build             # production build
npx eslint .              # lint
npx prettier --check "src/**/*.{ts,tsx,css}"  # format check
```

## Licencia

Apache-2.0
