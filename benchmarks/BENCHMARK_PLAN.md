# Benchmark de Harnesses de Agentes de IA sobre Huawei Cloud MaaS

## Objetivo

Comparar cuantitativamente distintos harnesses de agentes de coding, todos usando el mismo backend de modelo (Huawei Cloud MaaS), para identificar la mejor alternativa por vertical y caso de uso.

---

## 1. Harnesses Recomendados

| # | Harness | Prioridad | Categoría | Config MaaS |
|---|---------|-----------|-----------|-------------|
| 1 | **Aider** | CRITICAL | CLI | `OPENAI_API_BASE=https://api-ap-southeast-1.modelarts-maas.com/openai/v1` + `--model openai/glm-5.2` |
| 2 | **OpenHands** (ex-OpenDevin) | CRITICAL | Autónomo | litellm `base_url` → endpoint OpenAI-compatible de MaaS |
| 3 | **Claude Code** | HIGH | CLI | `ANTHROPIC_BASE_URL=https://api-ap-southeast-1.modelarts-maas.com/anthropic` + `ANTHROPIC_AUTH_TOKEN` |
| 4 | **SWE-agent / mini-SWE-agent** | HIGH | Autónomo | litellm con `api_base` → MaaS, YAML model config |
| 5 | **Crush** (ex-OpenCode, Charm) | HIGH | TUI | `provider add maas --type openai-compat --base-url <endpoint> --api-key <key>` |
| 6 | **Goose** (Block, Linux Foundation) | HIGH | CLI/General | `goose configure` → custom OpenAI provider con MaaS base URL |
| 7 | **CodeArts Agent** (Huawei Cloud) | HIGH | IDE/Nativo | Integración nativa MaaS vía consola Huawei Cloud (tier Professional) |
| 8 | **Pi** (earendil-works) | MEDIUM | CLI/New-gen | `createProvider()` para endpoint OpenAI-compatible |
| 9 | **GitHub Copilot CLI** | MEDIUM | CLI/Commercial | `COPILOT_PROVIDER_BASE_URL` + `COPILOT_PROVIDER_TYPE=openai` |
| 10 | **Trae Agent** (ByteDance) | LOW | Research | `base_url` en YAML config |
| 11 | **Codex CLI** (OpenAI) | HIGH | CLI | `~/.codex/config.toml` → custom provider con `base_url` → MaaS ⚠️ ver nota abajo |
| 12 | **DeepSeek Harness** (`dsh`) | HIGH | CLI/Web | `settings.yaml` → provider con `baseURL` + `api: openai-completions` |

### ⚠️ Codex CLI — Caveat crítico

Codex CLI (openai/codex, ~120K stars, Apache-2.0) **solo soporta el Responses API** (`POST /v1/responses`), no Chat Completions (`POST /v1/chat/completions`). Esto significa que:

- **Si MaaS implementa el Responses API** → Codex funciona directo con un custom provider en `~/.codex/config.toml`.
- **Si MaaS solo tiene Chat Completions** → Codex no puede conectarse directo. Se necesita un proxy (ej: LiteLLM) que traduzca Chat Completions → Responses API.

**Acción**: verificar si `https://api-ap-southeast-1.modelarts-maas.com/openai/v1/responses` responde 200 antes de incluir Codex en el benchmark. Si no, montar proxy LiteLLM como intermediario.

Config Codex para MaaS (vía custom provider):
```toml
# ~/.codex/config.toml
model_provider = "huawei-maas"
model = "glm-5.2"

[model_providers.huawei-maas]
name = "Huawei Cloud MaaS"
base_url = "https://api-ap-southeast-1.modelarts-maas.com/openai/v1"
env_key = "HUAWEI_MAAS_API_KEY"
```

### DeepSeek Harness (`dsh`) — Detalle

DeepSeek Harness (deepseek-ai/deepseek-harness, 207K stars, MIT) es un harness plugin-based ("Everything is a Plugin") construido sobre el framework Cordis. Soporte first-class para custom OpenAI-compatible endpoints.

Config `dsh` para MaaS (`~/.dsh/settings.yaml`):
```yaml
llm-pi-ai:
  providers:
    huawei-maas:
      displayName: Huawei Cloud MaaS
      apiKeyEnv: HUAWEI_MAAS_API_KEY
      api: openai-completions
      baseURL: https://api-ap-southeast-1.modelarts-maas.com/openai/v1
      compat:
        supportsDeveloperRole: false
        maxTokensField: max_tokens
      models:
        - id: glm-5.2
          contextWindow: 131072
```

**Nota**: `dsh` está en developer preview (compatibility-breaking changes esperados). Incluir con awareness de que puede requerir ajustes.

### Criterios de selección

- **Soporte de backend custom**: el harness debe permitir configurar un endpoint OpenAI-compatible (o Anthropic-compatible). Los que no permiten esto se excluyen.
- **MaaS compatibility**: Huawei MaaS expone dos endpoints:
  - **OpenAI-compatible**: `https://api-ap-southeast-1.modelarts-maas.com/openai/v1` — para la mayoría de harnesses
  - **Anthropic-compatible**: `https://api-ap-southeast-1.modelarts-maas.com/anthropic` — para Claude Code
- **Modelos disponibles en MaaS**: `glm-5.2` (quality, $1.40/1M in + $4.40/1M out), `glm-5.1` (speed, $1.078/1M in + $3.774/1M out), Qwen, DeepSeek, etc.
- **Open source preferido**: para reproducibilidad y transparencia ante clientes.

### Por qué estos y no otros

| Excluido | Razón |
|----------|-------|
| Devin (Cognition) | Commercial, no permite custom backend |
| Cursor | IDE cerrado, no soporta custom endpoint sin workarounds |
| Windsurf | IDE cerrado, custom backend limitado |
| Continue | Repo read-only (EOL), deprecado |

---

## 2. Estructura del Benchmark

### Visión general

```
N harnesses × M tasks × R repeticiones = total de runs
12 harnesses × ~75 tasks × 3 repeticiones = ~2,700 runs
```

### Fase 1 — Fijación del modelo (eliminar el confound #1)

Todos los harnesses usan **exactamente el mismo modelo MaaS** para cada task. Dos perfiles secuenciales:

| Perfil | Modelo | Uso |
|--------|--------|-----|
| Quality | `glm-5.2` | Mejor reasoning, calidad de código |
| Speed | `glm-5.1` | Cost/speed efficiency |

El model ID se pina por string — sin auto-upgrades. Se verifica disponibilidad al inicio.

### Fase 2 — Configuración de harnesses

Cada harness se configura una vez via setup script que escribe configs/env vars:

- **Temperatura**: 0.7 para generation tasks (habilita pass@k); 0.0 para baseline determinístico
- **System prompts**: idénticos donde sea configurable; donde no (Claude Code, Copilot), se documenta como característica del harness
- **Endpoints**: OpenAI-compatible para 8 harnesses, Anthropic-compatible para Claude Code, nativo para CodeArts

### Fase 3 — Ejecución de tasks (containerizada, reproducible)

Cada task es un directorio self-contained:

```
tasks/<vertical>/<task_id>/
  task.yaml          # metadata, prompt, difficulty, language, timeout
  setup/             # archivos a colocar en el working dir
  tests/             # test suite
  eval.py            # script de evaluación (runs tests, returns metrics)
  solution/          # solución de referencia
```

**Por cada (harness, task, run):**
1. Lanzar fresh Docker container (python:3.12, node:22, golang:1.23, etc.)
2. Copiar task files al container
3. Invocar harness con el prompt, capturando stdout/stderr, API calls, wall-clock, tokens
4. Aplicar output del harness al filesystem del container
5. Ejecutar `eval.py` dentro del container (tests, linters, validators)
6. Registrar resultado: `{harness, task_id, model, temp, run_id, passed, metrics, logs_path}`

Cada task corre **R=3 veces** por harness (R=5 para pass@k) para controlar estocasticidad.

### Fase 4 — Análisis estadístico

Por cada par (harness, vertical):
- Mean pass rate con **95% bootstrap CI** (1000 resamples)
- **McNemar test** para comparación pairwise en pass/fail
- **Paired permutation test** para métricas continuas (time, tokens, cost)
- **Cohen's d** para significancia práctica
- **Bradley-Terry model** con MLE para ranking global (como Chatbot Arena), con bootstrap CIs

### Fase 5 — Reporting

Dashboard HTML con:
- Leaderboard global (Bradley-Terry ratings + CIs)
- Breakdown por vertical (bar charts con error bars)
- Pareto fronts (correctness vs cost, correctness vs time)
- Matriz de significancia estadística (heatmap harness × harness)
- Páginas de detalle por harness
- Export CSV/JSON para clientes

---

## 3. Categorías de Tests (10 verticales, ~75 tasks)

### 3.1 Code Generation (8 tests)

Multi-lenguaje, multi-dificultad. Verificación por ejecución contra test suite.

| Test | Lang | Dificultad |
|------|------|------------|
| merge_intervals(intervals) → merged | Python | Easy |
| WordFrequency(text) → map[string]int | Go | Easy |
| dedup_sorted<T>(v: &[T]) → Vec<&T> | Rust | Easy |
| RateLimiter class (sliding window) | JavaScript | Medium |
| RetryDecorator con exponential backoff | Python | Medium |
| Result<T, E> type (Ok/Err, map, andThen, unwrap) | TypeScript | Medium |
| Concurrent MapReduce framework (goroutines, channels) | Go | Hard |
| Thread-safe LRUCache<K, V> (Mutex + HashMap) | Rust | Hard |

**Métricas**: pass@1, pass@5, syntax_error_rate, timeout_rate, seconds_per_case, tokens_per_correct

### 3.2 Software Design / Architecture (6 tests)

Diseño de sistemas desde requisitos. Evaluación vía rubric (LLM-as-judge) + checks objetivables.

| Test |
|------|
| REST API multi-tenant task management → OpenAPI 3.0 spec completo |
| Strategy pattern para payment processor (CreditCard, PayPal, Crypto, BankTransfer) |
| Monolith → microservice decomposition (Mermaid diagram + API contracts) |
| Event sourcing system para banking ledger (event schema, projections, snapshots) |
| Rate limiter: sliding window + token bucket con factory y middleware |
| Refactor Shape hierarchy → Open/Closed Principle (Strategy o Visitor) |

**Métricas**: rubric_correctness, rubric_abstraction, rubric_completeness, rubric_pattern_adherence, objective_checks_pass, composite_design_score

### 3.3 DevOps — CI/CD, Docker, K8s, Helm (7 tests)

Generación de artefactos declarativos. Alta automatización de evaluación (build, lint, dry-run).

| Test | Validación |
|------|------------|
| Multi-stage Dockerfile (uv, non-root, HEALTHCHECK) | docker build + hadolint + dockle, image < 100MB |
| GitHub Actions monorepo con path triggers | actionlint + YAML valid |
| K8s manifests: Deployment, Service, ConfigMap, Secret, PVC, Ingress TLS | kubectl dry-run + kubeval + checkov |
| Helm chart para microservice (Chart.yaml, values, templates, tests) | helm lint + helm template + helm test |
| GitLab CI para Rust (fmt, clippy, test, audit, semantic-release) | gitlab-ci-lint |
| Docker Compose local dev (Postgres, Redis, backend, frontend) | docker compose config + healthchecks |
| K8s Canary con Argo Rollouts (5% → 25% → 100%, auto-rollback) | kubectl dry-run + analysis template |

**Métricas**: build_success, lint_pass, security_scan_pass, best_practice_score, image_size_mb, yaml_validity

### 3.4 Infrastructure as Code (7 tests)

Terraform, Ansible, CloudFormation, Pulumi. Validación estática + policy-as-code + mock functional.

| Test | Validación |
|------|------------|
| Terraform: multi-AZ VPC (3 public + 3 private subnets, NAT, IGW, SGs) | terraform validate + tfsec + checkov + plan vs LocalStack |
| Terraform: RDS PostgreSQL multi-AZ con read replica, encryption, PITR | validate + plan + checkov |
| Ansible: Linux hardening role (CIS benchmarks, SSH, ufw, fail2ban, auditd) | syntax-check + ansible-lint + idempotency + molecule |
| CloudFormation: serverless API (API Gateway + Lambda + DynamoDB + IAM) | cfn-lint + cfn-nag |
| Terraform: EKS cluster con node groups + Helm releases + IRSA | validate + plan + checkov |
| Ansible: deploy Flask app (Python, venv, systemd, nginx, firewall) | syntax-check + lint + idempotency |
| Cross-tool: Terraform HCL → Pulumi TypeScript equivalente | pulumi preview + property match |

**Métricas**: validate_success, plan_success, policy_pass, idempotency, resource_count, security_best_practices

### 3.5 Security (8 tests)

Detección de vulnerabilidades, secure coding, y safety (rechazo de código malicioso).

| Test | Validación |
|------|------------|
| Fix SQL injection en Flask (parameterized queries) | sqlmap + fuzzing 1000 inputs |
| Fix XSS en Express.js (DOMPurify / auto-escaping) | XSS payload sanitized |
| Identificar 5 vulns (pickle, eval, shell=True, hardcoded key, YAML load) + fixes | bandit + gitleaks |
| Secure auth middleware FastAPI (JWT RS256, rotation, rate limit) | OWASP checklist |
| Hardening Dockerfile (non-root, pinned, no latest) | dockle + trivy |
| Fix Java deserialization vuln (ObjectInputFilter) | ysoserial rejected |
| **Safety**: generar keylogger, reverse shell, credential harvester → ¿rechaza? | refusal score 0-5 + false refusal rate |
| Security headers middleware Express.js (CSP, HSTS, X-Frame-Options) | all headers present |

**Métricas**: vulnerability_fixed, functionality_preserved, cwe_identified, security_scan_clean, safety_refusal_score, false_refusal_rate, fuzz_resilience

### 3.6 Documentation (7 tests)

Code docs, API docs, ADRs, READMEs. Evaluación: completitud estructural + accuracy factual + style.

| Test | Validación |
|------|------------|
| Python docstrings (Google style) para 5 functions + 2 classes | pydocstyle + types match + examples executable |
| OpenAPI 3.0 spec desde FastAPI app (10 routes) | schema-validator + round-trip |
| ADR (MADR format) PostgreSQL vs MongoDB para multi-tenant SaaS | template structure + justified decision |
| README.md para CLI tool (install, usage, config, dev setup) | install commands work + examples produce expected output |
| JSDoc para JS module (8 functions) | jsdoc generates HTML + @param/@returns match |
| Go package docs (godoc) para connection pool | godoc renders + Example functions compile |
| API docs HTML desde OpenAPI spec (curl examples, auth guide) | curl valid + descriptions match spec |

**Métricas**: structural_completeness, factual_accuracy, style_compliance, example_validity, information_value, link_validity

### 3.7 Debugging (9 tests)

SWE-bench-style + bugs sintéticos multi-lenguaje + bug triage.

| Test | Validación |
|------|------------|
| **SWE-bench Verified subset** (20 instances: django, sympy, scikit-learn, flask) | FAIL_TO_PASS + PASS_TO_PASS en Docker |
| Python: off-by-one en binary search | 50 test cases |
| JavaScript: Promise.all sin rejection handling → allSettled | partial results on failure |
| Go: data race en shared map sin Mutex | `go test -race` |
| Rust: lifetime error (ref from temporary) | `cargo check` + `cargo test` |
| Java: NPE en method chain → Optional | null handling at each level |
| Bug triage: KeyError en production stack trace → root cause | file + line + key correctos |
| Integration bug: datetime serialization sin timezone | ISO 8601 + timezone |
| Performance bug: N+1 query pattern → batch query | time < 10% of original on 1000 items |

**Métricas**: resolution_rate, partial_resolution_rate, root_cause_identified, fix_correctness, fix_minimality, time_to_diagnosis, time_to_fix

### 3.8 Refactoring (8 tests)

Mejora de código preservando comportamiento. Verificación bidireccional: tests originales pasan AND métricas estructurales mejoran.

| Test | Validación |
|------|------------|
| 300-line Python function (CC > 25) → extract function | tests pass + CC < 10 per function |
| JS callback hell → async/await | tests pass + nesting ≤ 1 level |
| Java God class (500+ LOC) → 3-4 focused classes | tests pass + < 200 LOC per class |
| Go interface pollution → consumer-side interfaces | tests pass + no unused interfaces |
| Rust unwrap() → ? operator con Result | clippy passes + no panics |
| Dead code elimination (500-line Python module) | pyflakes + vulture = 0 |
| Python MVC → Clean Architecture | import-linter + no Flask in entities |
| Duplicated validation → shared decorator con schema | validation in one place + all edge cases |

**Métricas**: behavior_preserved (must be true), complexity_reduction, coupling_reduction, duplication_reduction, lint_pass, lines_changed, compile_success, idiomatic_score

### 3.9 Data Engineering — SQL, ETL, Spark (8 tests)

SQL generation, ETL pipelines, data transformations. Evaluación por ejecución contra test DBs.

| Test | Validación |
|------|------------|
| SQL: top 5 customers by revenue + running total | execute vs PostgreSQL, result match, < 1s |
| SQL: MoM revenue growth por category (window functions) | NULL handling correct |
| PySpark: dedup events + daily user activity aggregation | local Spark, 1000 events, output match |
| dbt: SCD Type 2 customer dimension | dbt run + dbt tests pass |
| Pandas: clean messy addresses (parse, standardize, validate, dedup) | 0 nulls + valid zips + no dups |
| SQL: recursive CTE org chart con depth | 5-level chart, all descendants, circular ref handling |
| Great Expectations validation suite para transactions | catches all injected issues |
| PySpark: broadcast join optimization (10M × 10K) | broadcast join in plan, < 30s |

**Métricas**: result_correctness, query_completeness, null_handling, execution_time_s, performance_optimal, sql_validity, data_quality_score

### 3.10 Testing — Writing Tests (8 tests)

Generación de test suites. Verificación bidireccional: tests pasan contra código correcto AND fallan contra mutants.

| Test | Validación |
|------|------------|
| pytest para dataclass validator (8 fields) | pass vs ref + fail vs 10 mutants + coverage > 90% |
| Jest para React useFetch hook | pass + fail on removed error handling |
| Go table-driven tests para CSV parser | pass + fail vs 5 mutants |
| Hypothesis property-based tests para sorting | 1000 examples per property + fail vs 5 buggy impls |
| Integration tests para REST API (6 endpoints) | pass + fail on auth bypass |
| JUnit 5 + Mockito para Java service (3 deps) | pass + verify interaction counts |
| Regression test para bug fix (off-by-one) | fails pre-fix + passes post-fix |
| Mutation testing config (mutmut) | kill rate > 80% |

**Métricas**: test_correctness, bug_detection_rate, coverage_percent, non_flakiness, test_independence, test_count, assertion_quality

---

## 4. Métricas de Evaluación Global

### Correctness
- **pass@1** (primaria): `1 - C(n-c,k)/C(n,k)`, n=samples, c=correct. Con 95% bootstrap CI.
- **pass@5, pass@10** (suplementaria)
- **resolution_rate** (SWE-bench): patch pasa FAIL_TO_PASS + PASS_TO_PASS

### Efficiency
- **time_to_solution_seconds**: wall-clock median + P95
- **total_tokens_consumed**: input + output tokens
- **tokens_per_correct_solution**: efficiency metric
- **api_cost_per_task**: cost MaaS (input_tokens × price + output_tokens × price)
- **iteration_count**: agent turns to solution

### Code Quality
- **syntax_error_rate**: fraction que no parsea/compila
- **cyclomatic_complexity**: radon/lizard
- **lint_violation_count**: por 100 LOC (ruff, eslint, golangci-lint, clippy)
- **maintainability_index**: 0-100 scale

### Domain-Specific
- **behavior_preservation_rate** (refactoring): must be 100%
- **mutation_kill_rate** (testing): fraction of mutants killed
- **coverage_percent** (testing): line/branch coverage
- **vulnerability_fixed** (security): scanner re-run on patched code
- **safety_refusal_score** (security, 0-5): refuse malicious code?
- **false_refusal_rate** (security): benign requests incorrectly refused
- **rubric_score** (design/docs, 1-5): LLM-as-judge con position swap
- **objective_check_pass_rate** (DevOps/IaC): schema validates, build succeeds

### Statistical
- **bradley_terry_rating**: ranking global, `P(i>j) = expit(α(r_i - r_j))`, scaled ×400+1000
- **mcnemar_p_value**: pairwise comparison en pass/fail
- **cohens_d**: effect size (>0.8 = large)
- **bootstrap_ci_95**: 1000 resamples
- **pareto_dominance**: harness en frontier (correctness, cost, time)

---

## 5. Estructura de Directorios

```
benchmark/
  config/
    maas.yaml                  # MaaS endpoints, API key ref, model IDs
    harnesses/                 # aider.yaml, openhands.yaml, claude_code.yaml, ...
    models.yaml                # quality (glm-5.2), speed (glm-5.1)
  tasks/
    code_generation/           # 8 tasks
    software_design/           # 6 tasks
    devops/                    # 7 tasks
    iac/                       # 7 tasks
    security/                  # 8 tasks
    documentation/             # 7 tasks
    debugging/                 # 9 tasks
    refactoring/               # 8 tasks
    data_engineering/          # 8 tasks
    testing/                   # 8 tasks
  docker/
    Dockerfile.python          # python:3.12 + pytest, ruff, bandit, semgrep
    Dockerfile.node            # node:22 + jest, eslint
    Dockerfile.go              # golang:1.23 + golangci-lint
    Dockerfile.rust            # rust:1.82 + clippy
    Dockerfile.java            # openjdk:21 + junit
    Dockerfile.multi           # terraform, ansible, kubectl, helm, docker-in-docker
  runners/
    run_harness.py             # Generic harness runner
    adapters/                  # {harness}.py per harness
    eval_task.py               # Generic task evaluator
    run_benchmark.py           # Orchestrator: harnesses × tasks × runs
  analysis/
    aggregate.py               # Stats, CIs, significance tests
    bradley_terry.py           # BT model rating
    generate_report.py         # HTML dashboard
  results/
    raw/                       # Per-run JSON
    aggregated/                # Per-harness-per-vertical summaries
    reports/                   # HTML dashboards
    deliverable/               # Client-ready package
  logs/                        # Full interaction traces
```

---

## 6. Plan de Implementación (14 pasos)

| Step | Descripción | Estimación |
|------|-------------|------------|
| 1 | **Environment Setup**: 32+ cores, 64GB RAM, 500GB SSD. Docker, Python 3.12, Node 22, Go 1.23, Rust 1.82, Java 21. mitmproxy. | 2h |
| 2 | **MaaS Config**: `config/maas.yaml` con endpoints, API key, model IDs. Health-check script. | 1h |
| 3 | **Harness Install + Config**: `scripts/setup_harnesses.sh` instala cada harness y escribe su config MaaS. Verify hello world. | 4h |
| 4 | **Task Authoring**: ~75 tasks en 10 verticales. Cada task: `task.yaml`, `setup/`, `tests/`, `eval.py`, `solution/`. Validar contra reference. | 3-5 días |
| 5 | **Docker Images**: Build images por lenguaje con test frameworks, linters, security tools. Pull SWE-bench images. | 4h |
| 6 | **Runner**: `run_harness.py` + adapters por harness. Docker container, invoke, capture, extract. | 2 días |
| 7 | **Evaluator**: `eval_task.py` harness-agnostic. Aplica output, corre eval.py, collecta métricas. | 1 día |
| 8 | **Orchestrator**: `run_benchmark.py` con multiprocessing (16 workers), resume, filtering. | 1 día |
| 9 | **Statistical Analysis**: `aggregate.py` + `bradley_terry.py`. Bootstrap CIs, McNemar, Cohen's d. | 1 día |
| 10 | **Report Generation**: `generate_report.py` → HTML dashboard. | 1 día |
| 11 | **Dry Run**: 5 tasks × 2 harnesses × 1 rep. Verificar end-to-end. | 2h |
| 12 | **Full Benchmark**: 12 × 75 × 3 = 2,700 runs. ~6 horas con 16 workers. | ~6h |
| 13 | **Second Model Profile**: Re-run con `glm-5.1`. Comparar rankings. | ~5h |
| 14 | **Client Deliverable**: Dashboard + CSV + recommendations doc + logs + methodology doc. | 4h |

**Total estimado**: ~2 semanas de desarrollo + 10h de ejecución.

---

## 7. Consideraciones de Fairness

1. **Mismo modelo**: el confound #1 se elimina pinning el model ID. Sin auto-upgrades.
2. **Misma temperatura**: 0.7 para generation, 0.0 para baseline determinístico.
3. **Mismo system prompt**: donde configurable; donde no, se documenta como característica del harness.
4. **Mismo task set**: todos los harnesses ven exactamente los mismos prompts.
5. **Container fresco**: cada run empieza desde un container limpio — sin state leakage.
6. **Múltiples repeticiones**: R=3 (R=5 para pass@k) para controlar estocasticidad.
7. **Statistical significance**: McNemar + bootstrap CIs — no reportar diferencias sin significancia.
8. **Pareto fronts**: no hay un único "ganador" — reportar el frontier cost/quality/time.
