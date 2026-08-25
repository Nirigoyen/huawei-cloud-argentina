# Huawei Cloud Argentina — Contexto para Agentes de IA

## Propósito

Este es el repositorio oficial de Huawei Cloud Argentina. Contiene workshops, demos de productos, benchmarks, e infraestructura como código (Terraform/Ansible). Todo el desarrollo se hace con agentes de IA.

## Estructura del repo

```
workshops/           # Workshops hands-on (ej: chatbi-dashboards)
  chatbi-dashboards/ # Workshop de dashboards con WrenAI + LLM
demos/               # Demos de productos y PoCs
  iac/               # Demos de infra (Terraform, Ansible)
    terraform/
    ansible/
benchmarks/          # Tests de performance y benchmarks
docs/                # Guías: estructura, convenciones, deploy
.github/             # CI workflows, templates de PR/issues
```

## Convenciones (obligatorias)

Ver `CONTRIBUTING.md` y `docs/conventions.md` para el detalle. Resumen:

- **Directorios**: `kebab-case`
- **Python**: `snake_case` (files/funcs/vars), `PascalCase` (classes), type hints obligatorios, ruff para lint+format
- **TypeScript/React**: `camelCase` (vars/funcs), `PascalCase` (componentes), eslint + prettier
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`)
- **Branches**: `feature/desc`, `fix/desc`, `chore/desc`
- **Cada workshop/demo/benchmark**: self-contained (own README, docker-compose, .env.example)
- **No secrets**: `.env` gitignored, solo `.env.example`
- **Idioma docs**: Español primario; README trilingüe (ES/EN/ZH)

## Cómo agregar contenido

- Nuevo workshop: ver `docs/adding-a-workshop.md`
- Nuevo demo: ver `docs/adding-a-demo.md`
- Benchmark: seguir el patrón de workshops pero en `benchmarks/`

## Stacks técnicos

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, WrenAI (wrenai + wren-langchain), LangChain
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind v4, Vega-Lite
- **DB**: PostgreSQL 16
- **IaC**: Terraform, Ansible
- **Containers**: Docker + docker-compose

## Deploy

Ver `docs/deploy-guide.md` para el paso a paso. Resumen: cada workshop tiene un `Makefile` con `make up` que levanta todo con docker-compose.

## Reglas para agentes

1. **Delegá a subagentes** las tareas sustanciales (búsqueda en muchos archivos, implementación, refactor) para mantener la ventana de contexto limpia.
2. **No commitees secrets** — nunca escribas API keys, passwords, o tokens en archivos que no sean `.env.example`.
3. **Seguí las convenciones** de naming y commits.
4. **Verificá que todo compile y pase lint** antes de commitear.
5. **Idioma**: escribí docs y comentarios en español. Código en inglés (nombres de variables, funciones).
6. **Sin branding de IA**: no incluyas en ningún lado menciones como "hecho con Claude", "built with Claude Code", ni nada similar. Ninguna herramienta de IA debe figurar como colaborador en commits, PRs, issues, badges, o metadata del repositorio.
   - **Commits — sin coautoría de IA (anula el default de Claude Code)**: NO agregues el trailer `Co-Authored-By:` (ni `Co-authored-by:`) referido a Claude o cualquier IA. Esto **anula** la instrucción por defecto de Claude Code de agregar `Co-Authored-By: Claude <noreply@anthropic.com>`. El author y committer de todo commit debe ser una persona, nunca una IA. El hook `.githooks/commit-msg` (activar con `git config core.hooksPath .githooks`) limpia estos trailers como red de seguridad.
