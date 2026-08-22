# Estructura del Repositorio

Este documento describe la organización del repositorio **huawei-cloud-argentina**, cada directorio de nivel superior y su propósito. El repositorio agrupa workshops hands-on, demos de producto, benchmarks de rendimiento y guías de documentación, todos diseñados para ser autocontenidos.

## Diagrama de Árbol

```
huawei-cloud-argentina/
├── .github/
│   ├── workflows/          # Pipelines de CI (lint, test, build)
│   └── ISSUE_TEMPLATE/     # Plantillas de issues y PRs
├── docs/                   # Guías y documentación general
│   ├── repo-structure.md
│   ├── adding-a-workshop.md
│   ├── adding-a-demo.md
│   ├── conventions.md
│   └── deploy-guide.md
├── workshops/              # Workshops hands-on (cada uno autocontenido)
│   ├── README.md           # Índice de workshops
│   └── <name>/
│       ├── README.md
│       ├── CLAUDE.md
│       ├── docker-compose.yml
│       ├── .env.example
│       ├── Makefile
│       ├── src/
│       └── tests/
├── demos/                  # Demos de producto e IaC
│   ├── iac/
│   │   ├── terraform/
│   │   │   └── <name>/
│   │   └── ansible/
│   │       └── <name>/
│   └── <product-demo>/
│       ├── README.md
│       ├── docker-compose.yml
│       └── ...
├── benchmarks/             # Pruebas de rendimiento
│   └── <name>/
│       ├── README.md
│       ├── scripts/
│       └── results/
├── scripts/                # Scripts utilitarios compartidos
├── .gitignore
├── .editorconfig
├── LICENSE
└── README.md
```

## Directorios de Nivel Superior

### `.github/`

Contiene la configuración de GitHub Actions y plantillas:

- **`workflows/`**: Pipelines de integración continua. Ejecutan linting (ruff, eslint), tests, y validaciones de estructura en cada push y PR.
- **`ISSUE_TEMPLATE/`**: Plantillas para reportar bugs, solicitar features y describir PRs de forma estandarizada.

### `docs/`

Guías de documentación general del repositorio. Aquí viven los documentos sobre estructura, convenciones, cómo agregar workshops/demos y la guía de despliegue. No contiene código ejecutable.

### `workshops/`

Workshops prácticos y hands-on. Cada subdirectorio (`workshops/<name>/`) es un workshop **autocontenido** con su propio README, docker-compose, variables de entorno, Makefile y tests. Los workshops están diseñados para ejecutarse de forma aislada sin depender de otros workshops.

El archivo `workshops/README.md` funciona como índice que lista todos los workshops disponibles con una breve descripción y enlace a cada uno.

### `demos/`

Demos de producto y de infraestructura como código (IaC). Se divide en dos categorías:

- **`demos/iac/terraform/<name>/`**: Demos de Terraform. Cada uno contiene módulos de infraestructura, `variables.tf`, y scripts de ejecución.
- **`demos/iac/ansible/<name>/`**: Demos de Ansible. Cada uno contiene playbooks, `vars.yml`, y inventarios.
- **`demos/<name>/`**: Demos de producto (software). Siguen las mismas reglas de autocontención que los workshops: README, docker-compose, Makefile, etc.

### `benchmarks/`

Pruebas de rendimiento y benchmarks. Cada subdirectorio (`benchmarks/<name>/`) es autocontenido e incluye scripts de medición, configuración de escenarios y directorios para almacenar resultados. Los benchmarks comparan latencia, throughput o consumo de recursos entre configuraciones distintas.

### `scripts/`

Scripts utilitarios compartidos a nivel de repositorio (helpers de CI, herramientas de generación, scripts de sincronización). No son específicos de ningún workshop o demo.

## Principio Fundamental: Autocontención

Cada workshop, demo y benchmark es **autocontenido**. Esto significa:

1. **Dependencias locales**: Todo lo necesario para ejecutarlo vive dentro de su propio directorio.
2. **Sin dependencias cruzadas**: Un workshop no importa código de otro workshop.
3. **Docker aislado**: Los contenedores se nombran con el prefijo del workshop/demo para evitar colisiones.
4. **Variables de entorno propias**: Cada uno tiene su `.env.example` con las variables que necesita.
5. **Makefile propio**: Comandos `make up/down/logs` operan sobre ese workshop específico.

Este principio permite que cualquier persona pueda clonar el repo, entrar a un subdirectorio y ejecutarlo sin necesidad de entender el resto del repositorio.
