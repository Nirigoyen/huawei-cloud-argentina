# Convenciones del Repositorio

Este documento define las convenciones de naming, código, commits, branching y organización de archivos para todo el repositorio **huawei-cloud-argentina**.

## Nombres de Directorios

- Usar **kebab-case**: todo en minúsculas, palabras separadas por guiones.
- Ejemplos correctos: `rag-pipeline`, `data-migration`, `chatbi-dashboards`.
- Ejemplos incorrectos: `RagPipeline`, `rag_pipeline`, `RAGPipeline`.

## Python

### Naming

- **Archivos**: snake_case — `data_loader.py`, `db_utils.py`
- **Funciones**: snake_case — `load_dataset()`, `get_connection()`
- **Variables**: snake_case — `batch_size`, `db_url`
- **Clases**: PascalCase — `DataLoader`, `PipelineRunner`
- **Constantes**: UPPER_SNAKE_CASE — `MAX_RETRIES`, `DEFAULT_TIMEOUT`

### Type Hints

Type hints son **obligatorios** en todas las funciones públicas:

```python
def load_dataset(path: str, batch_size: int = 32) -> list[dict]:
    ...
```

### Ruff

Configuración de ruff en `pyproject.toml` o `ruff.toml`:

```toml
[tool.ruff.linter]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

- **E**: Errores de pycodestyle (estilo)
- **F**: Errores de pyflakes (análisis estático)
- **I**: isort (orden de imports)
- **UP**: pyupgrade (sintaxis moderna)
- **B**: flake8-bugbear (bugs comunes)
- **SIM**: flake8-simplify (simplificaciones)

## TypeScript

### Naming

- **Variables**: camelCase — `batchSize`, `dbUrl`
- **Funciones**: camelCase — `loadDataset()`, `getConnection()`
- **Componentes**: PascalCase — `DataLoader`, `PipelineRunner`
- **Archivos de componentes**: PascalCase — `DataLoader.tsx`, `PipelineRunner.tsx`
- **Archivos no-componentes**: camelCase o kebab-case — `config.ts`, `db-utils.ts`
- **Constantes**: UPPER_SNAKE_CASE — `MAX_RETRIES`, `DEFAULT_TIMEOUT`

### ESLint + Prettier

Configuración de Prettier (`.prettierrc`):

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all"
}
```

- **Punto y coma**: `true` (siempre al final de sentencias)
- **Comillas simples**: `true`
- **Coma trailing**: `all`

ESLint configurado con reglas estrictas y integración con Prettier (`eslint-config-prettier`).

## Mensajes de Commit

Se sigue **Conventional Commits**. Formato:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Tipos

| Tipo | Descripción |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Cambios de formato (no afectan lógica) |
| `refactor` | Refactor de código (no nuevo feature ni bugfix) |
| `perf` | Mejoras de rendimiento |
| `test` | Adición o corrección de tests |
| `build` | Cambios en build system o dependencias |
| `ci` | Cambios en configuración de CI |
| `chore` | Tareas de mantenimiento |
| `revert` | Revertir un commit anterior |

### Ejemplos

```
feat: agregar workshop rag-pipeline
fix: corregir healthcheck de postgres en chatbi-dashboards
docs: actualizar guía de despliegue
refactor: simplificar lógica de conexión a BD
chore: actualizar dependencias de python
```

## Nombres de Branches

Formato: `<type>/<description-kebab-case>`

| Prefijo | Uso |
|---------|-----|
| `feature/` | Nuevas funcionalidades |
| `fix/` | Corrección de bugs |
| `chore/` | Mantenimiento |
| `docs/` | Documentación |
| `refactor/` | Refactor |

### Ejemplos

```
feature/rag-pipeline-workshop
fix/postgres-healthcheck
chore/update-dependencies
docs/deploy-guide
refactor/db-connection-logic
```

## Proceso de PR

1. **Branch**: Crear branch desde `main` con el naming correcto.
2. **Commit**: Hacer commits con mensajes Conventional Commits.
3. **Push**: `git push origin <branch>`
4. **PR**: Abrir Pull Request contra `main`.
5. **CI**: Esperar que pasen los checks de CI (lint, test, build).
6. **Review**: Solicitar review de al menos un revisor.
7. **Merge**: Hacer squash merge a `main` con el mensaje convencional.

```
main → feature/<branch> → commits → push → PR → CI ✓ → review → squash merge → main
```

## Organización de Archivos

Cada workshop, demo y benchmark es **autocontenido**:

- Todo lo necesario vive dentro de su directorio.
- No se importa código de otros workshops/demos.
- Cada uno tiene su propio `README.md`, `docker-compose.yml`, `.env.example`, y `Makefile`.
- Los contenedores se nombran con el prefijo del workshop/demo para evitar colisiones.

## Secretos

- **`.env`** está en `.gitignore` y **nunca** se commitea.
- **`.env.example`** es el único archivo de ejemplo de variables que se commitea, y contiene **placeholders**, nunca secretos reales.
- **Nunca** commitear credenciales reales (API keys, passwords, tokens).
- Para generar secretos de sesión:

```bash
openssl rand -hex 32
```

- Si se commitea un secreto por accidente, hacer `git rebase` para eliminarlo del historial y **rotar el secreto** inmediatamente.

## Idioma de Documentación

- **Documentación**: Español es el idioma primario. Todos los README, guías y comentarios en markdown se escriben en español.
- **Código**: En inglés. Nombres de variables, funciones, clases, comentarios en código y docstrings van en inglés.
- **Commits**: En español (descripción del cambio).
- **Issues y PRs**: En español.

## Sin Branding de Herramientas de IA

- **No incluir** en ningún lugar del repositorio menciones como "hecho con Claude", "built with Claude Code", "Co-Authored-By: Claude", o cualquier referencia similar a herramientas de IA.
- **Ninguna herramienta de IA debe figurar como colaborador** en commits, PRs, issues, badges, o cualquier metadata del repositorio.
- Esto aplica a: README, badges, commit messages, PR descriptions, issues, comentarios en código, y cualquier otro contenido del repositorio.

## Docker

### docker-compose.yml

- Los servicios se definen en `docker-compose.yml` dentro del directorio del workshop/demo.
- `container_name` se prefija con el nombre del workshop/demo para evitar colisiones:

```yaml
services:
  chatbi-postgres:        # prefijo "chatbi"
    container_name: chatbi-postgres
    image: postgres:16
    ...
  chatbi-app:             # prefijo "chatbi"
    container_name: chatbi-app
    build: .
    ...
```

### Healthchecks

Las bases de datos **deben** tener healthchecks:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U workshop"]
  interval: 5s
  timeout: 5s
  retries: 5
```

Los servicios que dependen de la BD deben esperar a que esté healthy:

```yaml
depends_on:
  <name>-postgres:
    condition: service_healthy
```

### Puertos

- Backend/API: `8000`
- Frontend: `8080`
- PostgreSQL: `5432`
- Si hay conflictos, mapear a puertos alternativos pero documentarlo en el README.
