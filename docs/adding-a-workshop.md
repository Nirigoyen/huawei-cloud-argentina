# Cómo Agregar un Workshop

Guía paso a paso para agregar un nuevo workshop al repositorio. Cada workshop es autocontenido y sigue una estructura estandarizada.

## Pasos

### 1. Crear el directorio

Crear el directorio del workshop usando **kebab-case**:

```bash
mkdir -p workshops/<name-kebab-case>
```

Ejemplo: `workshops/rag-pipeline`, `workshops/data-migration`.

### 2. Agregar `README.md`

El README debe incluir las siguientes secciones:

```markdown
# <Name del Workshop>

## Descripción
Breve descripción de qué se aprende y qué se construye.

## Prerrequisitos
- Docker + docker-compose
- Git
- Endpoint LLM (URL compatible con OpenAI + API key + nombre del modelo)

## Quickstart
\`\`\`bash
cp .env.example .env
# Editar .env con tus valores
make up
\`\`\`

## Variables de Entorno
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| OPENAI_BASE_URL | URL del endpoint LLM | https://api.openai.com/v1 |
| OPENAI_API_KEY | API key del LLM | sk-... |
| OPENAI_MODEL | Nombre del modelo | gpt-4o |
| SESSION_SECRET | Secreto de sesión | (generar con openssl rand -hex 32) |

## Arquitectura
Descripción de los componentes y cómo interactúan. Incluir diagrama si es posible.
```

### 3. Agregar `CLAUDE.md`

Crear un archivo `CLAUDE.md` con el contexto específico del workshop para agentes de IA:

```markdown
# <Name del Workshop> — Contexto del Agente

## Propósito
Qué hace este workshop y qué tecnologías usa.

## Estructura
- `src/`: Código fuente
- `tests/`: Tests
- `docker-compose.yml`: Orquestación de contenedores

## Comandos
- `make up`: Levantar servicios
- `make down`: Detener servicios
- `make logs`: Ver logs
- `make rebuild`: Reconstruir imágenes

## Convenciones
Notas específicas del workshop (puertos, nombres de contenedores, etc.).
```

### 4. Agregar `docker-compose.yml` (si usa contenedores)

```yaml
services:
  <name>-postgres:
    image: postgres:16
    container_name: <name>-postgres
    environment:
      POSTGRES_USER: workshop
      POSTGRES_PASSWORD: workshop
      POSTGRES_DB: scenario
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U workshop"]
      interval: 5s
      timeout: 5s
      retries: 5

  <name>-app:
    build: .
    container_name: <name>-app
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      <name>-postgres:
        condition: service_healthy
```

### 5. Agregar `.env.example`

Incluir **todas** las variables de entorno requeridas, sin secretos reales:

```bash
# Endpoint LLM
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Sesión
SESSION_SECRET=generate-with-openssl-rand-hex-32

# Base de datos
POSTGRES_USER=workshop
POSTGRES_PASSWORD=workshop
POSTGRES_DB=scenario
```

### 6. Agregar `Makefile`

```makefile
.PHONY: up down logs rebuild clean

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

rebuild:
	docker compose build --no-cache

clean:
	docker compose down -v --remove-orphans
```

### 7. Seguir convenciones de código

- **Python**: snake_case para archivos, funciones y variables. PascalCase para clases. Type hints obligatorios. Linting con `ruff` (line-length 100, reglas E/F/I/UP/B/SIM).
- **TypeScript**: camelCase para variables y funciones. PascalCase para componentes y archivos. Linting con `eslint` + `prettier` (semi true, printWidth 100).

Ver `docs/conventions.md` para el detalle completo.

### 8. Agregar tests

Crear el directorio `tests/` con tests que cubran la funcionalidad principal del workshop:

```
<name>/
├── src/
└── tests/
    ├── __init__.py
    ├── test_main.py
    └── conftest.py
```

Los tests deben poder ejecutarse de forma aislada sin depender de servicios externos (usar mocks o fixtures).

### 9. Actualizar el índice `workshops/README.md`

Agregar una entrada al índice de workshops:

```markdown
## <Name del Workshop>

Breve descripción de una línea.

- **Directorio**: [`workshops/<name>/`](../workshops/<name>/)
- **Tecnologías**: Docker, PostgreSQL, Python
- **Duración estimada**: 30 min
```

### 10. Commit

Hacer commit siguiendo Conventional Commits:

```bash
git add workshops/<name>
git commit -m "feat: agregar workshop <name>"
```

## Plantilla de Estructura

```
workshops/<name>/
├── README.md
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── Makefile
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── conftest.py
└── requirements.txt
```

## Checklist Final

- [ ] Directorio en kebab-case
- [ ] README con todas las secciones
- [ ] CLAUDE.md con contexto del agente
- [ ] docker-compose.yml con healthchecks
- [ ] .env.example sin secretos reales
- [ ] Makefile con targets up/down/logs/rebuild/clean
- [ ] Código pasa linting (ruff/eslint)
- [ ] Tests pasan
- [ ] Índice workshops/README.md actualizado
- [ ] Commit con mensaje convencional
