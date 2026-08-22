# CLAUDE.md — ChatBI Dashboards Workshop

> Contexto para agentes IA (Claude Code) trabajando en este workshop.

## Propósito del workshop

Workshop competitivo donde participantes construyen dashboards sobre una base
PostgreSQL chateando en lenguaje natural con un agente LLM. El agente usa
WrenAI como semantic layer para traducir preguntas → SQL válido → resultados.
Los dashboards (gráficos Vega-Lite) se exponen en una galería para votación.

## Stack técnico

| Capa | Tecnología | Detalle |
|---|---|---|
| Backend | **FastAPI** + Uvicorn | Python 3.12, async, SSE para chat streaming |
| ORM | **SQLAlchemy** 2.x | session async, `Base.metadata.create_all` (sin Alembic) |
| Validation | **Pydantic** v2 + pydantic-settings | schemas de API + config |
| LLM framework | **LangChain** | `ChatOpenAI` + tools, agent executor |
| Semantic layer | **WrenAI** (`wren-ai` CLI) | introspección de schema, modelos semánticos (MDL), query engine |
| Frontend | **Next.js 16** (App Router) | React Server Components + client components para SSE |
| Styling | **Tailwind CSS** | — |
| Gráficos | **Vega-Lite** | specs generadas por el LLM o construidas en frontend |
| DB | **PostgreSQL 16** | datos del workshop + schema del sistema |
| Containers | **Docker Compose** | named volumes para persistencia |

## Arquitectura

### Routers (FastAPI)

- **`routers/workshops.py`** — CRUD de workshops (organizer). Crear, listar,
  obtener por código de acceso.
- **`routers/setup.py`** — Conexión a la DB del workshop + introspección.
  Recibe credenciales de la DB del organizador, valida conexión, dispara
  `wren.introspect.introspect_schema()`, crea el proyecto Wren, y hace deploy.
- **`routers/participants.py`** — Registro y sesión de participantes. Se unen
  con código de acceso del workshop.
- **`routers/chat.py`** — Endpoint SSE (`GET /chat/stream`). Recibe el mensaje
  del participante, invoca `agent.chat_agent.stream_chat()`, y streamaea
  eventos (tokens, tool calls, resultados, errores) como SSE.
- **`routers/dashboards.py`** — CRUD de dashboards (guardar, listar, gallery,
  votar).

### Wren Integration (`wren/`)

- **`introspect.py`** — `introspect_schema(engine)`: lee tablas, columnas, tipos
  y relaciones del schema de la DB conectada. Genera el modelo semántico (MDL)
  inicial para WrenAI.
- **`project.py`** — Gestión del ciclo de vida del proyecto Wren:
  `create_project()`, `deploy_project()`, `query(sql)`. Usa el CLI `wren-ai`
  (localizado vía `sys.executable` parent — debe estar en el venv).

### Agent (`agent/chat_agent.py`)

- `ChatAgent`: wrapper sobre LangChain. Construye un agent con tools de WrenAI
  (query, introspect, mdl info).
- `stream_chat(message, project_path, history)`: generator async que yielda
  eventos SSE. Maneja el loop del agent, tool calls, y formatea resultados.
- **Cachea toolkits por project path** para evitar re-crearlos en cada mensaje.
  Si se re-introspecciona un proyecto, el toolkit se invalida pero **la cache
  del agent no** — ver Gotchas.

## Cómo correr

### Docker (recomendado)

```bash
cp .env.example .env
# editar .env: OPENAI_API_KEY, OPENAI_BASE_URL
make up
# Frontend: http://localhost:8080
# API docs: http://localhost:8000/docs
```

### Dev local

```bash
# 1. Dependencias con Docker
docker compose up -d postgres wren

# 2. Backend
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000
```

> En dev, cambiar `POSTGRES_HOST` a `localhost` en `.env` (el default
> `postgres` es el nombre del servicio en Docker).

## Tareas comunes

### Agregar un endpoint

1. Definir el schema Pydantic en `app/schemas.py` (request + response).
2. Si necesita persistencia, agregar el modelo en `app/models.py` y crear
   schema con `Base.metadata.create_all` (drop + recreate si hay cambios).
3. Implementar el router en `app/routers/<recurso>.py`.
4. Registrar el router en `app/main.py` (`app.include_router(...)`).
5. Test en `app/tests/`.

### Modificar el agente

- Lógica del agent: `app/agent/chat_agent.py`.
- Para cambiar el system prompt: editar el prompt template en `chat_agent.py`.
- Para agregar tools: definirlas con `@tool` de LangChain y agregarlas al
  toolkit. Las tools de Wren están en `app/wren/project.py`.
- El streaming SSE se formatea en `stream_chat()` — cada evento es un dict
  serializado a `data: {json}\n\n`.

### Cambiar el modelo LLM

- Variable de entorno: `OPENAI_MODEL` (ej: `gpt-4o`, `gpt-4o-mini`).
- Para usar un endpoint distinto (Azure, gateway): `OPENAI_BASE_URL`.
- Para cambiar parámetros (temperature, etc.): editar la inicialización de
  `ChatOpenAI` en `chat_agent.py`.

### Agregar un modelo Wren (semantic layer)

- La introspección automática genera el MDL inicial. Para agregar relaciones o
  métricas calculadas a mano: editar el MDL del proyecto en
  `WREN_PROJECTS_DIR/<project>/manifest.json` y re-deployar con
  `wren project deploy`.
- Para re-introspeccionar: llamar al endpoint de setup que dispara
  `introspect_schema()`.

## Gotchas

1. **Docker usa named volumes** (`wren_projects`, `wren_home`) — no confiar en
   archivos del host. Los proyectos Wren viven dentro del volumen, no en el
   filesystem del host. Para inspeccionar: `docker compose exec wren ls
   /opt/wrenai/projects`.

2. **El `wren` CLI se encuentra via `sys.executable` parent** — el backend
   busca el binario en el directorio padre del intérprete Python actual. En
   Docker esto funciona porque `wren-ai` se instala en el venv. En dev local,
   asegúrate de tener `wren-ai` instalado en el venv activo (no global).

3. **`ToolMessage.content` de wren tools es Python `repr()`** — los resultados
   de queries vienen como strings con `Decimal('123.45')`, `datetime(...)`, etc.
   Parsear con regex para limpiar + `ast.literal_eval`. No usar `json.loads`
   directo (falla con `Decimal`).

4. **El admin form default host es `postgres`** (docker service name) —
   cambiar a `localhost` para dev local. Si el organizer no puede conectar,
   este es el primer chequeo.

5. **Schema se crea con `Base.metadata.create_all`** (no Alembic) — cambios de
   schema requieren drop + recreate del volumen de la DB del sistema
   (`make clean`). Esto borra workshops, participantes y dashboards. No hay
   migraciones incrementales.

6. **El agente cachea toolkits por project path** — re-introspect invalida el
   toolkit en Wren pero **no la cache del agent**. Si se re-introspecciona,
   reiniciar el backend (o implementar invalidación de cache en
   `chat_agent.py`).

## Estructura de archivos

### Backend

```
backend/
├── pyproject.toml
├── app/
│   ├── main.py               # FastAPI app, include_router
│   ├── config.py             # Settings (pydantic-settings, .env)
│   ├── database.py           # engine + sessionmaker async
│   ├── models.py             # Workshop, Participant, Dashboard, Vote
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── routers/
│   │   ├── workshops.py
│   │   ├── setup.py          # POST /setup → introspect + deploy Wren
│   │   ├── participants.py
│   │   ├── chat.py           # GET /chat/stream (SSE)
│   │   └── dashboards.py
│   ├── wren/
│   │   ├── introspect.py     # introspect_schema(engine) → MDL
│   │   └── project.py        # create/deploy/query Wren project
│   ├── agent/
│   │   └── chat_agent.py     # ChatAgent + stream_chat (SSE generator)
│   └── tests/
│       ├── conftest.py
│       ├── test_workshops.py
│       ├── test_setup.py
│       └── test_chat.py
└── README.md
```

### Frontend

```
frontend/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── eslint.config.mjs
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── (organizer)/
│   │   │   ├── page.tsx              # lista de workshops
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx          # detail + setup DB
│   │   │   │   └── gallery/page.tsx  # galería + voting
│   │   └── (participant)/
│   │       ├── join/page.tsx         # unirse con código
│   │       └── [workshopId]/
│   │           ├── page.tsx          # chat
│   │           └── dashboard/page.tsx # builder
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx        # consume SSE
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── dashboard/
│   │   │   ├── DashboardGrid.tsx
│   │   │   ├── Widget.tsx            # render Vega-Lite spec
│   │   │   └── WidgetPalette.tsx
│   │   └── gallery/
│   │       ├── GalleryGrid.tsx
│   │       └── VoteButton.tsx
│   ├── lib/
│   │   ├── api.ts                   # fetch wrapper
│   │   ├── sse.ts                   # SSE consumer helper
│   │   └── hooks/
│   └── types/
│       └── index.ts
└── README.md
```
