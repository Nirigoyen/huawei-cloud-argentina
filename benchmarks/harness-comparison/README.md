# AI Coding-Agent Harness Benchmark

Quantitative comparison of AI coding-agent harnesses, all backed by the same
Huawei Cloud MaaS model endpoint, across 10 task verticals and ~75 tasks.

The benchmark pins the model, controls temperature and system prompts, runs
each task in a fresh Docker container, and applies statistical analysis
(Bradley-Terry, McNemar, bootstrap CIs, Pareto fronts) to produce a
reproducible ranking.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Orchestrator, analysis, adapters |
| Docker | 24+ | Task containerization |
| Node | 22 | JavaScript/TypeScript tasks |
| Go | 1.23 | Go tasks |
| Rust | 1.82 | Rust tasks |
| Java | 21 (OpenJDK) | Java tasks |

**Hardware:** 32+ cores, 64 GB RAM, 500 GB SSD.

**Credentials:** `HUAWEI_MAAS_API_KEY` env var set to a valid MaaS API key.

---

## Quick start

```bash
export HUAWEI_MAAS_API_KEY="your-key-here"

# 1. Install harnesses + verify MaaS + build images
make setup verify docker

# 2. Run the full benchmark (~2,700 runs, ~6 h with 16 workers)
make run

# 3. Analyze, rank, and generate the HTML report
make analyze rank report
```

Or do it all in one command:

```bash
make all
```

For a fast end-to-end smoke test (2 harnesses, 5 tasks, 1 repetition):

```bash
make dry-run
```

---

## Directory structure

```
benchmark/
  config/
    maas.yaml                  # MaaS endpoints, API key env var, region
    models.yaml                # Model profiles: quality, speed, deterministic
    harnesses/                 # One YAML per harness (aider.yaml, openhands.yaml, ...)
  tasks/
    _template/                 # Copy this to create a new task
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
    Dockerfile.python          # python:3.12 + pytest, ruff, bandit
    Dockerfile.node            # node:22 + jest, eslint
    Dockerfile.go              # golang:1.23 + golangci-lint
    Dockerfile.rust            # rust:1.82 + clippy
    Dockerfile.java            # openjdk:21 + junit
    Dockerfile.multi           # terraform, ansible, kubectl, helm, docker-in-docker
  runners/
    adapters/                  # {harness}.py per harness
    run_benchmark.py           # Orchestrator: harnesses x tasks x runs
  analysis/
    aggregate.py               # Stats, CIs, significance tests
    bradley_terry.py           # BT model rating
    generate_report.py         # HTML dashboard
  scripts/
    setup_harnesses.sh         # Install + configure all harnesses
    verify_maas.py             # Health-check MaaS endpoints
  results/
    raw/                       # Per-run JSON
    aggregated/                # Per-harness-per-vertical summaries
    reports/                   # HTML dashboards
    deliverable/               # Client-ready package
  logs/                        # Full interaction traces
  Makefile
  run.sh                       # Convenience wrapper with prerequisite checks
  requirements.txt
```

---

## How to add a new task

1. Copy the template directory:

   ```bash
   cp -r tasks/_template tasks/<vertical>/<task_id>
   ```

2. Edit `tasks/<vertical>/<task_id>/task.yaml`:
   - Set `id`, `vertical`, `difficulty` (easy/medium/hard), `language`.
   - Write the `prompt` the agent will receive.
   - Set `timeout_seconds` and `points`.

3. Add a `setup/` directory with files the agent's working directory should
   start with (source code to fix, test stubs, config files, etc.).

4. Add a `tests/` directory with the test suite that determines pass/fail.

5. Write `eval.py` — runs the tests and prints a JSON result:

   ```json
   {"passed": true, "metrics": {"test_exit_code": 0}, "details": ["..."]}
   ```

   The template `eval.py` shows the pattern with pytest.

6. (Optional) Add a `solution/` directory with a reference solution for
   validation and pass@k computation.

---

## How to add a new harness

1. **Create a harness config:**

   ```bash
   # config/harnesses/{name}.yaml
   name: my_harness
   category: cli              # cli | autonomous | tui | ide | native
   endpoint_type: openai      # openai | anthropic | native
   install_cmd: pip install my-harness
   invoke_template: 'my-harness --model {model} {prompt}'
   env_vars:
     OPENAI_API_BASE: https://api.modelarts-maas.com/openai/v1
     OPENAI_API_KEY: '${HUAWEI_MAAS_API_KEY}'
   config_steps:
     - type: env
       var: OPENAI_API_BASE
       value: https://api.modelarts-maas.com/openai/v1
   ```

2. **Create an adapter:**

   ```bash
   # runners/adapters/{name}.py
   ```

   The adapter is a Python module that knows how to invoke the harness inside
   a Docker container, capture stdout/stderr and token counts, and apply the
   harness output to the filesystem. See existing adapters for the interface.

3. **Add install steps** to `scripts/setup_harnesses.sh` if the harness needs
   system-level installation or config file generation.

---

## Configuration reference

### `config/maas.yaml`

```yaml
maas:
  openai_endpoint: https://api.modelarts-maas.com/openai/v1
  anthropic_endpoint: https://api.modelarts-maas.com/anthropic
  api_key_env: HUAWEI_MAAS_API_KEY
  region: cn-east-3
```

- `openai_endpoint` — used by most harnesses (Aider, OpenHands, Crush, etc.).
- `anthropic_endpoint` — used by Claude Code.
- `api_key_env` — name of the environment variable holding the API key.

### `config/models.yaml`

```yaml
profiles:
  quality:                    # deepseek-v4-pro, temp 0.7
    model_id: deepseek-v4-pro
    temperature: 0.7
    max_tokens: 8192
  speed:                      # deepseek-v4-flash, temp 0.7
    model_id: deepseek-v4-flash
    temperature: 0.7
    max_tokens: 8192
  deterministic:              # deepseek-v4-pro, temp 0.0
    model_id: deepseek-v4-pro
    temperature: 0.0
    max_tokens: 8192
```

The model ID is pinned by string — no auto-upgrades. This eliminates the
model as a confound: all harnesses use exactly the same model.

### Harness configs (`config/harnesses/*.yaml`)

Each file defines one harness: its install command, invocation template,
endpoint type, environment variables, and config steps. The 12 harnesses
currently configured:

| Harness | Category | Endpoint |
|---------|----------|----------|
| aider | cli | openai |
| openhands | autonomous | openai |
| claude_code | cli | anthropic |
| swe_agent | autonomous | openai |
| crush | tui | openai |
| goose | cli | openai |
| codearts_agent | ide | native |
| pi | cli | openai |
| copilot_cli | cli | openai |
| trae_agent | research | openai |
| codex | cli | openai |
| dsh | cli | openai |

---

## Running partial benchmarks

### By model profile

```bash
make run-quality    # deepseek-v4-pro
make run-speed      # deepseek-v4-flash
```

### By vertical

```bash
python runners/run_benchmark.py --config config/maas.yaml --verticals security,debugging
```

### By harness

```bash
python runners/run_benchmark.py --config config/maas.yaml --harnesses aider,openhands
```

### By difficulty

```bash
python runners/run_benchmark.py --config config/maas.yaml --difficulty easy
```

### Combinations

```bash
python runners/run_benchmark.py \
  --config config/maas.yaml \
  --model-profile speed \
  --verticals code_generation,testing \
  --harnesses aider,claude_code \
  --repetitions 5
```

### Via `run.sh`

```bash
./run.sh --model-profile speed --verticals security --harnesses aider --repetitions 1
```

---

## Understanding the results

Results are written under `results/`:

| Path | Contents |
|------|----------|
| `results/raw/` | One JSON file per run: `{harness, task_id, model, temp, run_id, passed, metrics, logs_path}` |
| `results/aggregated/` | Per-harness-per-vertical summaries with CIs and significance tests |
| `results/reports/` | HTML dashboard with leaderboard, breakdowns, Pareto fronts |
| `results/deliverable/` | Client-ready package (dashboard + CSV + recommendations) |

### Key metrics

**Correctness:**
- `pass@1` — primary. Probability at least one of k samples passes. With 95% bootstrap CI.
- `pass@5`, `pass@10` — supplementary.
- `resolution_rate` — SWE-bench style: patch passes FAIL_TO_PASS and PASS_TO_PASS.

**Efficiency:**
- `time_to_solution_seconds` — wall-clock median + P95.
- `total_tokens_consumed` — input + output tokens.
- `tokens_per_correct_solution` — efficiency metric.
- `api_cost_per_task` — MaaS cost (input_tokens x price + output_tokens x price).
- `iteration_count` — agent turns to solution.

**Code quality:**
- `syntax_error_rate` — fraction that does not parse/compile.
- `cyclomatic_complexity` — radon / lizard.
- `lint_violation_count` — per 100 LOC.
- `maintainability_index` — 0-100 scale.

**Domain-specific:**
- `behavior_preservation_rate` (refactoring) — must be 100%.
- `mutation_kill_rate` (testing) — fraction of mutants killed.
- `coverage_percent` (testing) — line/branch coverage.
- `vulnerability_fixed` (security) — scanner re-run on patched code.
- `safety_refusal_score` (security, 0-5) — does it refuse malicious code?
- `false_refusal_rate` (security) — benign requests incorrectly refused.
- `rubric_score` (design/docs, 1-5) — LLM-as-judge with position swap.
- `objective_check_pass_rate` (DevOps/IaC) — schema validates, build succeeds.

---

## Statistical methods

### Bradley-Terry model

Global ranking via pairwise win probabilities:

```
P(i > j) = expit(alpha * (r_i - r_j))
```

Ratings are scaled x400 + 1000 (Elo-like). Bootstrap CIs (1000 resamples)
on the ratings. This is the same approach used by Chatbot Arena.

### McNemar test

Pairwise comparison on pass/fail outcomes. For each harness pair, builds a
2x2 contingency table of (both pass, only A passes, only B passes, both fail)
and computes the McNemar chi-squared statistic and p-value. Detects whether
differences in pass rate are statistically significant, not just noise.

### Bootstrap confidence intervals

1000 resamples with replacement, computing the statistic on each. The 2.5th
and 97.5th percentiles form the 95% CI. Used on pass@1, mean time, mean
tokens, and Bradley-Terry ratings.

### Pareto fronts

A harness is Pareto-optimal if no other harness is better or equal on all
metrics (correctness, cost, time) and strictly better on at least one. The
frontier is reported instead of a single winner — there is no one best
harness, only trade-offs.

### Cohen's d

Effect size for continuous metrics. >0.8 is a large effect. Computed
alongside McNemar to distinguish "statistically significant" from
"practically significant."

---

## Troubleshooting

### MaaS connectivity

**Symptom:** `make verify` fails with HTTP 401/403.

- Confirm `HUAWEI_MAAS_API_KEY` is set and valid: `echo $HUAWEI_MAAS_API_KEY`.
- Check the key has access to the MaaS region in `config/maas.yaml` (`cn-east-3`).
- Verify network reachability:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" https://api.modelarts-maas.com/openai/v1/models \
    -H "Authorization: Bearer $HUAWEI_MAAS_API_KEY"
  ```

**Symptom:** HTTP 404 on the Anthropic endpoint.

- The Anthropic-compatible endpoint may not be enabled for your account.
  Claude Code will not work without it. Other harnesses use the OpenAI
  endpoint and are unaffected.

### Docker permissions

**Symptom:** `docker info` fails with "permission denied."

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Or start the Docker daemon if it is not running:

```bash
sudo systemctl start docker
```

### Harness install failures

**Symptom:** `make setup` fails on a specific harness.

- Check `scripts/setup_harnesses.sh` output for the failing harness.
- Some harnesses require Node (Copilot CLI), Rust (Crush), or Go (Goose)
  installed at the system level. Verify with `node --version`,
  `rustc --version`, `go version`.
- Install missing language runtimes or skip the harness:
  ```bash
  python runners/run_benchmark.py --config config/maas.yaml \
    --harnesses aider,openhands,claude_code
  ```

### Codex CLI — Responses API

Codex CLI only supports the Responses API (`POST /v1/responses`), not Chat
Completions. If MaaS does not implement the Responses API, Codex cannot
connect directly. Check:

```bash
curl -s -o /dev/null -w "%{http_code}" https://api.modelarts-maas.com/openai/v1/responses \
  -H "Authorization: Bearer $HUAWEI_MAAS_API_KEY"
```

If this returns 404, mount a LiteLLM proxy that translates Chat Completions
to the Responses API, or exclude Codex from the run.

### Out of disk space

Each run creates a Docker container. With ~2,700 runs, intermediate layers
accumulate. Clean up:

```bash
make clean          # removes results/ and logs/
docker system prune -f
```

---

## License

Internal use only. Not for redistribution.
