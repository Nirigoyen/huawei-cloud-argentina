# ChatBI Dashboards Workshop

Workshop donde participantes compiten construyendo el mejor dashboard sobre una base
PostgreSQL, usando **WrenAI** (semantic layer) + un **agente de chat con LLM**.

Los participantes se conectan a una base de datos real, chatean en lenguaje natural con
un agente que traduce sus preguntas a consultas SQL (validadas por la semantic layer de
WrenAI), y construyen dashboards visuales con gráficos Vega-Lite. Al final, todos los
dashboards se exponen en una galería para votar el mejor.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Navegador                            │
│  Next.js 16 (App Router) + Tailwind + Vega-Lite             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Chat (SSE)  │  │  Dashboard   │  │  Gallery / Vote  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼──────────────────┼───────────────────┼────────────┘
          │ HTTP / SSE        │ REST              │ REST
┌─────────▼──────────────────▼───────────────────▼────────────┐
│                  FastAPI (Python 3.12)                      │
│  ┌────────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐  │
│  │ workshops  │ │ setup    │ │ participants│ │  chat      │  │
│  │  router    │ │ router   │ │   router   │ │  router    │  │
│  └────────────┘ └────┬─────┘ └────────────┘ └─────┬──────┘  │
│                      │                        ┌────▼──────┐  │
│                      │                        │ chat_agent│  │
│  ┌───────────────────▼──────────┐             │ (LangCh.) │  │
│  │  WrenAI Integration          │             └─────┬─────┘  │
│  │  • introspect.py (schema)    │◄──────────────────┘        │
│  │  • project.py (semantic mdl) │                             │
│  └──────────────┬───────────────┘                             │
└─────────────────┼────────────────────────────────────────────┘
                  │
   ┌──────────────▼──────────────┐   ┌──────────────────────┐
   │  WrenAI Engine (container)  │   │  PostgreSQL 16        │
   │  • wren-ai CLI (venv)       │   │  • datos del workshop │
   │  • mdl / semantic models    │   │  • schema del sistema │
   └─────────────────────────────┘   └──────────────────────┘
```

**Stack:**

| Componente | Tecnología | Versión |
|---|---|---|
| Backend | FastAPI + Uvicorn | Python 3.12 |
| Frontend | Next.js (App Router) + Tailwind | Node 24 / Next 16 |
| Base de datos | PostgreSQL | 16 |
| Semantic layer | WrenAI (wren-ai CLI) | latest |
| Agente de chat | LangChain + LLM (OpenAI-compatible) | — |
| Gráficos | Vega-Lite | — |
| Contenedor | Docker + docker-compose | — |

---

## Prerrequisitos

- **Docker** + **docker-compose** (o Docker Desktop)
- Un **endpoint de LLM** compatible con la API de OpenAI (OpenAI, Azure OpenAI,
  un gateway propio, etc.) con su API key
- Para desarrollo local sin Docker:
  - Python 3.12 + [`uv`](https://github.com/astral-sh/uv)
  - Node.js 24 + npm

---

## Quickstart (Docker)

```bash
cd workshops/chatbi-dashboards

# 1. Configurar variables de entorno
cp .env.example .env
#    Editar .env y setear:
#      OPENAI_API_KEY=sk-...
#      OPENAI_BASE_URL=https://api.openai.com/v1   # o tu endpoint

# 2. Levantar todo el stack
make up
#    (equivalente: docker compose up --build -d)

# 3. Acceder
#    Frontend:  http://localhost:8080
#    API docs:  http://localhost:8000/docs
#    Postgres:  localhost:5432
```

Para ver logs:

```bash
make logs              # todos los servicios
make logs backend      # solo backend
```

Para detener y limpiar:

```bash
make down              # detiene contenedores (mantiene volúmenes)
make clean             # detiene + elimina volúmenes (borra datos)
```

---

## Quickstart (desarrollo)

Levanta solo Postgres y WrenAI con Docker, y corre backend y frontend en local
para hot-reload.

```bash
cd workshops/chatbi-dashboards

# 1. Configurar entorno
cp .env.example .env
#    Editar .env (ver arriba). Para dev, usar:
#      POSTGRES_HOST=localhost   # en vez de "postgres"

# 2. Levantar dependencias (postgres + wren)
docker compose up -d postgres wren

# 3. Backend
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 4. Frontend (otra terminal)
cd frontend
npm install
npm run dev          # http://localhost:3000
```

> **Nota:** En modo dev el frontend corre en el puerto 3000 (no 8080, que es el
> proxy de nginx en Docker).

---

## Variables de entorno

| Variable | Descripción | Default | Requerida |
|---|---|---|---|
| `OPENAI_API_KEY` | API key del LLM (OpenAI-compatible) | — | Sí |
| `OPENAI_BASE_URL` | URL base del endpoint LLM | `https://api.openai.com/v1` | No |
| `OPENAI_MODEL` | Modelo a usar | `gpt-4o-mini` | No |
| `POSTGRES_HOST` | Host de PostgreSQL | `postgres` (docker) / `localhost` (dev) | Sí |
| `POSTGRES_PORT` | Puerto de PostgreSQL | `5432` | No |
| `POSTGRES_USER` | Usuario de PostgreSQL | `wren` | Sí |
| `POSTGRES_PASSWORD` | Password de PostgreSQL | `wren` | Sí |
| `POSTGRES_DB` | Base de datos del sistema (schema del workshop) | `chatbi` | Sí |
| `WREN_HOME` | Directorio home de WrenAI (dentro del container) | `/opt/wrenai` | No |
| `WREN_PROJECTS_DIR` | Directorio de proyectos Wren (named volume) | `/opt/wrenai/projects` | No |
| `BACKEND_PORT` | Puerto del backend FastAPI | `8000` | No |
| `FRONTEND_PORT` | Puerto del frontend (nginx proxy) | `8080` | No |
| `CORS_ORIGINS` | Orígenes permitidos (comma-separated) | `http://localhost:8080,http://localhost:3000` | No |
| `SECRET_KEY` | Secret para firmar tokens/sesiones | — | Sí (prod) |

---

## Estructura del proyecto

```
workshops/chatbi-dashboards/
├── .env.example
├── Makefile
├── docker-compose.yml
├── README.md                 # este archivo
├── CLAUDE.md                 # contexto para agentes IA
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py           # FastAPI app factory
│   │   ├── config.py         # settings (pydantic-settings)
│   │   ├── database.py       # engine + session (SQLAlchemy)
│   │   ├── models.py         # ORM models (workshop, participant, dashboard...)
│   │   ├── schemas.py        # Pydantic schemas (API)
│   │   ├── routers/
│   │   │   ├── workshops.py
│   │   │   ├── setup.py      # introspección + conexión a DB del participante
│   │   │   ├── participants.py
│   │   │   ├── chat.py       # endpoint SSE del agente
│   │   │   └── dashboards.py
│   │   ├── wren/
│   │   │   ├── introspect.py # introspección de schema → modelos Wren
│   │   │   └── project.py    # gestión de proyectos Wren (crear, deploy, query)
│   │   ├── agent/
│   │   │   └── chat_agent.py # LangChain agent + stream_chat (SSE)
│   │   └── tests/
│   └── README.md
│
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── src/
    │   ├── app/              # App Router (pages)
    │   │   ├── (organizer)/  # admin: crear workshop, ver gallery
    │   │   ├── (participant)/# chat + dashboard builder
    │   │   └── layout.tsx
    │   ├── components/
    │   │   ├── chat/         # chat UI (SSE consumer)
    │   │   ├── dashboard/    # grid + widgets Vega-Lite
    │   │   └── gallery/      # galería de dashboards + voting
    │   ├── lib/              # API client, hooks, utils
    │   └── types/
    └── README.md
```

---

## Flujo del workshop

1. **El organizer crea un workshop** desde el panel de admin. Define nombre,
   descripción y configuración general.
2. **El organizer conecta una base de datos** (host, port, db, user, password).
   Al guardar, el backend ejecuta la **introspección automática** del schema
   (`wren/introspect.py`) y genera un modelo semántico en WrenAI
   (`wren/project.py`).
3. **Los participantes se unen** al workshop usando un código de acceso. Cada
   participante recibe una sesión aislada.
4. **Los participantes chatean** en lenguaje natural. El agente
   (`agent/chat_agent.py`) usa tools de WrenAI para traducir la pregunta a SQL,
   ejecutarla contra la base del workshop, y devolver resultados.
5. **Construyen dashboards** a partir de las consultas y resultados del chat.
   Los gráficos se renderizan con Vega-Lite. Cada dashboard se guarda asociado
   al participante.
6. **Galería y votación**: todos los dashboards se exponen en una galería
   pública del workshop. Los participantes pueden votar. El dashboard con más
   votos gana.

```
[Organizer] → crea workshop → conecta DB → introspección auto
                                              │
[Participante] → une con código → chatea → construye dashboard
                                              │
                                         [Galería] → votación → ganador
```

---

## Deploy con agente

Para instrucciones de deploy (producción, Huawei Cloud, etc.) usando el agente,
ver [`../../docs/deploy-guide.md`](../../docs/deploy-guide.md).

---

## Troubleshooting

### El agente responde pero no ejecuta queries
- Verificar que la introspección se completó correctamente (logs del backend:
  buscar `introspection complete`).
- Verificar que el proyecto Wren está deployado (`wren project deploy`). Si se
  re-introspeccionó, el proyecto puede necesitar re-deploy.

### `wren` CLI no encontrado
- El `wren-ai` CLI debe estar instalado en el venv del container. El backend lo
  localiza vía `sys.executable` parent. Si corres en dev sin Docker, asegúrate
  de tener `wren-ai` instalado en tu venv activo.

### Error de conexión a Postgres desde el admin form
- En Docker, el host es `postgres` (nombre del servicio). En dev local, usar
  `localhost`. El form tiene `postgres` como default — cambiarlo si corres en
  dev.

### Los cambios de schema no se reflejan
- El schema se crea con `Base.metadata.create_all` (no usa Alembic). Para
  aplicar cambios de schema: detener el stack, eliminar el volumen de la DB del
  sistema, y levantar de nuevo (`make clean && make up`). **Esto borra todos
  los datos del sistema** (workshops, participantes, dashboards).

### `ToolMessage.content` con `Decimal('...')` causa errores de parseo
- Las tools de Wren devuelven resultados como Python `repr()`, que incluye
  `Decimal('123.45')`. El backend parsea esto con regex + `ast.literal_eval`.
  Si ves errores de parseo en logs, verificar que el resultado no tenga tipos
  no soportados (ej: `datetime` custom).

### El frontend no conecta al backend (CORS)
- Verificar `CORS_ORIGINS` en `.env` incluye el origen del frontend
  (`http://localhost:8080` para Docker, `http://localhost:3000` para dev).

### Port 8080 ya en uso
- Cambiar `FRONTEND_PORT` en `.env` a otro puerto libre.

### WrenAI no levanta
- Verificar que el volumen `wren_home` no está corrupto: `docker volume rm
  chatbi-dashboards_wren_home` y recrear con `make up`.
- Verificar memoria disponible: WrenAI requiere al menos 2GB.
