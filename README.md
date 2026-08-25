# Huawei Cloud Argentina — Repositorio Oficial / Official Repository / 官方仓库

[![Public Repository](https://img.shields.io/badge/repo-public-green.svg)]()
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

> Repositorio oficial del equipo de **Huawei Cloud Argentina**.
> Contiene talleres prácticos, demos de productos, pruebas de rendimiento y ejemplos de infraestructura como código.
>
> *Official repository of the **Huawei Cloud Argentina** team — hands-on workshops, product demos, benchmarks, and infrastructure-as-code examples.*
>
> *华为云阿根廷团队官方仓库 —— 包含实操工作坊、产品演示、性能基准测试及基础设施即代码示例。*

---

## Español

### Acerca de este repositorio

Este es el repositorio oficial del equipo de **Huawei Cloud Argentina**. Su propósito es centralizar y compartir los recursos técnicos que producimos: talleres hands-on, demos de productos y pruebas de concepto (PoC), benchmarks de rendimiento y ejemplos de infraestructura como código (Terraform y Ansible).

Una característica distintiva de este repositorio es que **todo el desarrollo se realiza con agentes de IA**. El repositorio incluye contexto para estos agentes —principalmente el archivo `CLAUDE.md` en la raíz y en cada subproyecto— de modo que cualquier colaborador pueda continuar el trabajo de forma consistente con la asistencia de un agente de IA.

### Estructura del repositorio

```
huawei-cloud-argentina/
├── workshops/     # Talleres hands-on (ej: chatbi-dashboards)
├── demos/         # Demos de productos y pruebas de concepto
│   └── iac/       # Demos de infraestructura (Terraform, Ansible)
├── benchmarks/    # Pruebas de rendimiento y benchmarks
├── docs/          # Guías: estructura, convenciones, despliegue
└── .github/       # Workflows de CI, plantillas de PR/issues
```

| Directorio     | Descripción                                                          |
| -------------- | -------------------------------------------------------------------- |
| `workshops/`   | Talleres prácticos guiados, cada uno autocontenido.                  |
| `demos/`       | Demos de productos y PoCs.                                           |
| `demos/iac/`   | Ejemplos de infraestructura como código (Terraform, Ansible).        |
| `benchmarks/`  | Pruebas de rendimiento y comparativas.                               |
| `docs/`        | Guías de estructura, convenciones y procedimientos de despliegue.    |
| `.github/`     | Workflows de integración continua y plantillas de PR/issues.         |

### Inicio rápido — Taller `chatbi-dashboards`

```bash
# 1. Clonar el repositorio
git clone git@github.com:Nirigoyen/huawei-cloud-argentina.git
cd huawei-cloud-argentina/workshops/chatbi-dashboards

# 2. Configurar variables de entorno
cp .env.example .env
#    Editar .env y definir:
#      OPENAI_API_KEY=<tu-clave>
#      OPENAI_BASE_URL=<endpoint-del-llm>

# 3. Levantar el entorno con Docker Compose
make up          # equivale a: docker compose up -d --build

# 4. Acceder a la aplicación
#    Frontend:  http://localhost:8080
#    API:       http://localhost:8000
```

### Talleres disponibles

| Nombre                | Descripción                                                                                                                                   | Stack                                             |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `chatbi-dashboards`   | Taller donde los participantes comparten construyendo el mejor dashboard sobre una base PostgreSQL, usando la capa semántica de WrenAI y un agente conversacional potenciado por LLM. | FastAPI + Next.js 16 + PostgreSQL 16 + WrenAI     |

### Cómo contribuir

1. **Lee la guía de contribución.** Antes de enviar un PR, revisa [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`docs/conventions.md`](docs/conventions.md).
2. **Desarrollo con agentes de IA.** Todo el desarrollo se realiza con agentes de IA. Lee [`CLAUDE.md`](CLAUDE.md) para entender el contexto del repositorio y cómo trabajar con el agente.
3. **Cada componente es autocontenido.** Cada taller, demo o benchmark debe ser autónomo: su propio `README.md`, su propio `docker-compose.yml` (o equivalente) y su propio `.env.example`.
4. **Sin secretos en el repositorio.** Nunca commits claves, credenciales ni tokens. Usa únicamente plantillas `.env.example` con valores de ejemplo.
5. **Conventional Commits.** Los mensajes de commit siguen la especificación [Conventional Commits](https://www.conventionalcommits.org/), por ejemplo: `feat(workshops): añade nuevo taller de RDS`.

### Licencia

Este proyecto está licenciado bajo la **Apache License 2.0**. Consulta el archivo [`LICENSE`](LICENSE) para más detalles.

### Contacto

**Huawei Cloud Argentina** — Equipo técnico.

Para consultas, abre un issue en este repositorio o contacta al equipo a través de los canales internos de Huawei Cloud Argentina.

---

## English

### About this repository

This is the official repository of the **Huawei Cloud Argentina** team. Its purpose is to centralize and share the technical resources we produce: hands-on workshops, product demos and proofs of concept (PoCs), performance benchmarks, and infrastructure-as-code examples (Terraform and Ansible).

A distinctive feature of this repository is that **all development is done with AI agents**. The repository includes context for these agents — primarily the `CLAUDE.md` file at the root and within each subproject — so any contributor can continue work consistently with the assistance of an AI agent.

### Repository structure

```
huawei-cloud-argentina/
├── workshops/     # Hands-on workshops (e.g., chatbi-dashboards)
├── demos/         # Product demos and PoCs
│   └── iac/       # Infrastructure demos (Terraform, Ansible)
├── benchmarks/    # Performance tests and benchmarks
├── docs/          # Guides: structure, conventions, deployment
└── .github/       # CI workflows, PR/issue templates
```

| Directory      | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `workshops/`   | Guided hands-on workshops, each self-contained.                    |
| `demos/`       | Product demos and PoCs.                                            |
| `demos/iac/`   | Infrastructure-as-code examples (Terraform, Ansible).              |
| `benchmarks/`  | Performance tests and benchmarks.                                  |
| `docs/`        | Guides on structure, conventions, and deployment procedures.       |
| `.github/`     | CI workflows and PR/issue templates.                               |

### Quickstart — `chatbi-dashboards` workshop

```bash
# 1. Clone the repository
git clone git@github.com:Nirigoyen/huawei-cloud-argentina.git
cd huawei-cloud-argentina/workshops/chatbi-dashboards

# 2. Configure environment variables
cp .env.example .env
#    Edit .env and set:
#      OPENAI_API_KEY=<your-key>
#      OPENAI_BASE_URL=<llm-endpoint>

# 3. Start the environment with Docker Compose
make up          # equivalent to: docker compose up -d --build

# 4. Access the application
#    Frontend:  http://localhost:8080
#    API:       http://localhost:8000
```

### Available workshops

| Name                | Description                                                                                                                              | Stack                                             |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `chatbi-dashboards` | Workshop where participants compete to build the best dashboard over a PostgreSQL database, using the WrenAI semantic layer and an LLM-powered chat agent. | FastAPI + Next.js 16 + PostgreSQL 16 + WrenAI     |

### How to contribute

1. **Read the contribution guide.** Before submitting a PR, review [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/conventions.md`](docs/conventions.md).
2. **AI agent development.** All development is done with AI agents. Read [`CLAUDE.md`](CLAUDE.md) to understand the repository context and how to work with the agent.
3. **Each component is self-contained.** Every workshop, demo, or benchmark must be standalone: its own `README.md`, its own `docker-compose.yml` (or equivalent), and its own `.env.example`.
4. **No secrets in the repository.** Never commit keys, credentials, or tokens. Use only `.env.example` templates with placeholder values.
5. **Conventional Commits.** Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification, e.g.: `feat(workshops): add new RDS workshop`.

### License

This project is licensed under the **Apache License 2.0**. See the [`LICENSE`](LICENSE) file for details.

### Contact

**Huawei Cloud Argentina** — Technical team.

For inquiries, open an issue in this repository or reach out to the team through the internal Huawei Cloud Argentina channels.

---

## 中文

### 关于本仓库

这是 **华为云阿根廷团队** 的官方仓库。其目的是集中并分享我们产出的技术资源：实操工作坊、产品演示与概念验证（PoC）、性能基准测试，以及基础设施即代码示例（Terraform 和 Ansible）。

本仓库的一个显著特点是 **所有开发工作均借助 AI 智能体完成**。仓库中包含供这些智能体使用的上下文信息 —— 主要是根目录及各子项目中的 `CLAUDE.md` 文件 —— 以便任何贡献者都能在 AI 智能体的辅助下一致地继续开展工作。

### 仓库结构

```
huawei-cloud-argentina/
├── workshops/     # 实操工作坊（例如：chatbi-dashboards）
├── demos/         # 产品演示与概念验证
│   └── iac/       # 基础设施演示（Terraform、Ansible）
├── benchmarks/    # 性能测试与基准测试
├── docs/          # 指南：结构、规范、部署
└── .github/       # CI 工作流、PR/Issue 模板
```

| 目录           | 说明                                                       |
| -------------- | ---------------------------------------------------------- |
| `workshops/`   | 引导式实操工作坊，各自独立。                               |
| `demos/`       | 产品演示与概念验证。                                       |
| `demos/iac/`   | 基础设施即代码示例（Terraform、Ansible）。                 |
| `benchmarks/`  | 性能测试与基准测试。                                       |
| `docs/`        | 关于结构、规范及部署流程的指南。                           |
| `.github/`     | 持续集成工作流及 PR/Issue 模板。                           |

### 快速开始 —— `chatbi-dashboards` 工作坊

```bash
# 1. 克隆仓库
git clone git@github.com:Nirigoyen/huawei-cloud-argentina.git
cd huawei-cloud-argentina/workshops/chatbi-dashboards

# 2. 配置环境变量
cp .env.example .env
#    编辑 .env 并设置：
#      OPENAI_API_KEY=<你的密钥>
#      OPENAI_BASE_URL=<LLM 端点地址>

# 3. 使用 Docker Compose 启动环境
make up          # 等同于：docker compose up -d --build

# 4. 访问应用
#    前端：  http://localhost:8080
#    API：   http://localhost:8000
```

### 可用工作坊

| 名称                | 说明                                                                                                        | 技术栈                                           |
| ------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `chatbi-dashboards` | 参与者竞赛式工作坊：基于 PostgreSQL 数据库构建最佳仪表盘，使用 WrenAI 语义层与 LLM 驱动的对话式智能体。     | FastAPI + Next.js 16 + PostgreSQL 16 + WrenAI    |

### 如何贡献

1. **阅读贡献指南。** 提交 PR 之前，请查阅 [`CONTRIBUTING.md`](CONTRIBUTING.md) 和 [`docs/conventions.md`](docs/conventions.md)。
2. **AI 智能体开发。** 所有开发工作均通过 AI 智能体完成。请阅读 [`CLAUDE.md`](CLAUDE.md) 以了解仓库上下文及如何与智能体协作。
3. **各组件独立自洽。** 每个工作坊、演示或基准测试都必须自成体系：拥有各自的 `README.md`、各自的 `docker-compose.yml`（或等价文件）以及各自的 `.env.example`。
4. **仓库中不存放密钥。** 切勿提交密钥、凭据或令牌。仅使用 `.env.example` 模板填写占位值。
5. **约定式提交。** 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范，例如：`feat(workshops): 新增 RDS 工作坊`。

### 许可证

本项目基于 **Apache License 2.0** 许可证开源。详情请参阅 [`LICENSE`](LICENSE) 文件。

### 联系方式

**华为云阿根廷** —— 技术团队。

如有疑问，请在本仓库中提交 Issue，或通过华为云阿根廷内部渠道与团队联系。
