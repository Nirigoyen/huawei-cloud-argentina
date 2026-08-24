# Contribuir a Huawei Cloud Argentina

¡Gracias por tu interés en contribuir! Este repo es el repositorio oficial de Huawei Cloud Argentina y contiene workshops, demos, benchmarks, e infraestructura.

## Reglas generales

1. **Todo el desarrollo se hace con agentes de IA.** Leé `CLAUDE.md` para el contexto general antes de empezar.
2. **Cada workshop/demo/benchmark es self-contained.** Debe tener su propio `README.md`, `docker-compose.yml` (si aplica), y `.env.example`.
3. **No commitear secrets.** Los archivos `.env` están gitignored. Usar `.env.example` con valores placeholder.
4. **Sin menciones a herramientas de IA.** No incluir en ningún lugar del repositorio frases como "hecho con Claude", "built with Claude Code", "Co-Authored-By: Claude", ni ninguna referencia similar. Ninguna herramienta de IA debe figurar como colaborador en commits, PRs, issues, badges, o cualquier metadata del repositorio.
5. **Idioma:** Documentación en español. README del repo es trilingüe (ES/EN/ZH). Nombres de variables y funciones en inglés.

## Estructura de directorios

```
workshops/<nombre-workshop>/     # kebab-case
demos/<nombre-demo>/
demos/iac/{terraform,ansible}/<nombre>/
benchmarks/<nombre-benchmark>/
```

## Convenciones de naming

| Elemento | Convención | Ejemplo |
|---|---|---|
| Directorios | `kebab-case` | `chatbi-dashboards` |
| Python (files, funcs, vars) | `snake_case` | `chat_agent.py` |
| Python (classes) | `PascalCase` | `WrenToolkit` |
| TypeScript (vars, funcs) | `camelCase` | `streamChat` |
| TypeScript (components, files) | `PascalCase` | `ChatPanel.tsx` |
| CSS classes | `kebab-case` | `chat-panel` |
| Branches | `tipo/descripcion` | `feature/add-auth` |

## Code style

### Python
- Type hints obligatorias en todas las funciones públicas
- Linter: `ruff` (config en `ruff.toml`)
- Formatear: `ruff format`

### TypeScript/React
- Linter: `eslint` (config en `eslint.config.mjs`)
- Formatear: `prettier` (config en `.prettierrc`)
- Strict mode: sí (`tsconfig.json` con `"strict": true`)

## Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: agregar workshop de RAG
fix: corregir bug en streaming SSE
docs: actualizar guía de deploy
refactor: simplificar build del agente
chore: actualizar dependencias
test: agregar tests de chat flow
```

## Branches y PRs

1. Crear branch: `git checkout -b feature/mi-feature`
2. Commitear siguiendo Conventional Commits
3. Push y crear PR
4. El PR debe pasar CI (lint + tests)
5. Usar el template de PR (se completa automáticamente)

## CI

Los PRs disparan checks de:
- `ruff check` (Python lint)
- `eslint` + `prettier --check` (TS lint + format)
- `pytest` (tests de backend)
- `docker compose config` (validación de compose files)

## Agregar contenido nuevo

- **Workshop**: ver `docs/adding-a-workshop.md`
- **Demo**: ver `docs/adding-a-demo.md`
- **Benchmark**: seguir el patrón de workshops pero en `benchmarks/`

## Licencia

Al contribuir, aceptas que tus contribuciones se licencian bajo Apache-2.0.
