#!/usr/bin/env bash
# Install and configure all 12 AI coding harnesses for MaaS backend.
# Idempotent: skips already-installed harnesses. Continues on failure.
# Prints a summary at the end.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/../config/harnesses" && pwd)"

OPENAI_BASE="https://api.modelarts-maas.com/openai/v1"
ANTHROPIC_BASE="https://api.modelarts-maas.com/anthropic"

# Track results: harness_name:status
declare -A RESULTS

log() { printf '\033[1m[%s]\033[0m %s\n' "$1" "$2"; }

check_cmd() { command -v "$1" &>/dev/null; }

# ---------------------------------------------------------------------------
# Individual harness setup functions
# ---------------------------------------------------------------------------

setup_aider() {
  local name="aider"
  if check_cmd aider; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  pip install aider-chat 2>/dev/null
  if check_cmd aider; then
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_openhands() {
  local name="openhands"
  if docker image inspect openhands/openhands &>/dev/null 2>&1; then
    RESULTS[$name]="skipped (image already present)"
    return
  fi
  docker pull openhands/openhands 2>/dev/null
  if docker image inspect openhands/openhands &>/dev/null 2>&1; then
    mkdir -p ~/.openhands
    cat > ~/.openhands/config.toml <<EOF
[core]
workspace_base = "/workspace"

[llm]
model = "openai/deepseek-v4-pro"
api_key = "\${HUAWEI_MAAS_API_KEY}"
base_url = "${OPENAI_BASE}"
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_claude_code() {
  local name="claude_code"
  if check_cmd claude; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @anthropic-ai/claude-code 2>/dev/null
  if check_cmd claude; then
    RESULTS[$name]="installed (set ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY env)"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_swe_agent() {
  local name="swe_agent"
  if python -m sweagent.run --help &>/dev/null 2>&1; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  pip install swe-agent 2>/dev/null
  if python -c "import sweagent" 2>/dev/null; then
    mkdir -p ~/.swe_agent
    cat > ~/.swe_agent/config.yaml <<EOF
agent:
  model:
    name: openai/deepseek-v4-pro
    api_base: ${OPENAI_BASE}
    api_key: \${HUAWEI_MAAS_API_KEY}
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_crush() {
  local name="crush"
  if check_cmd crush; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @anthropic-ai/crush 2>/dev/null || curl -fsSL https://crush.ai/install | bash 2>/dev/null
  if check_cmd crush; then
    crush provider add openai-compat \
      --base-url "$OPENAI_BASE" \
      --api-key "${HUAWEI_MAAS_API_KEY:-<set-key>" 2>/dev/null || true
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_goose() {
  local name="goose"
  if check_cmd goose; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  curl -fsSL https://github.com/block/goose/releases/download/stable/install.sh | bash 2>/dev/null
  if check_cmd goose; then
    goose configure --provider openai \
      --base-url "$OPENAI_BASE" \
      --api-key "${HUAWEI_MAAS_API_KEY:-<set-key>}" 2>/dev/null || true
    mkdir -p ~/.config/goose
    cat > ~/.config/goose/config.yaml <<EOF
GOOSE_PROVIDER: openai
GOOSE_MODEL: deepseek-v4-pro
OPENAI_API_KEY: \${HUAWEI_MAAS_API_KEY}
OPENAI_API_BASE: ${OPENAI_BASE}
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_codearts_agent() {
  local name="codearts_agent"
  if check_cmd codearts; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  pip install codearts-cli 2>/dev/null
  if check_cmd codearts; then
    mkdir -p ~/.codearts
    cat > ~/.codearts/agent.yaml <<EOF
endpoint: ${OPENAI_BASE}
api_key: \${HUAWEI_MAAS_API_KEY}
region: cn-east-3
model: deepseek-v4-pro
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_pi() {
  local name="pi"
  if check_cmd pi; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @pi-ai/cli 2>/dev/null
  if check_cmd pi; then
    pi provider config --name openai \
      --base-url "$OPENAI_BASE" \
      --api-key "${HUAWEI_MAAS_API_KEY:-<set-key>}" 2>/dev/null || true
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_copilot_cli() {
  local name="copilot_cli"
  if gh copilot --version &>/dev/null 2>&1; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @github/copilot-cli 2>/dev/null
  if gh copilot --version &>/dev/null 2>&1; then
    RESULTS[$name]="installed (set COPILOT_PROVIDER, OPENAI_API_BASE, OPENAI_API_KEY env)"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_trae_agent() {
  local name="trae_agent"
  if [[ -d /opt/trae-agent ]] && check_cmd trae; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  git clone https://github.com/trae-ai/trae-agent.git /opt/trae-agent 2>/dev/null
  pip install -e /opt/trae-agent 2>/dev/null
  if check_cmd trae; then
    mkdir -p ~/.trae
    cat > ~/.trae/config.yaml <<EOF
provider: openai
model: deepseek-v4-pro
api_base: ${OPENAI_BASE}
api_key: \${HUAWEI_MAAS_API_KEY}
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_codex() {
  local name="codex"
  if check_cmd codex; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @openai/codex 2>/dev/null
  if check_cmd codex; then
    mkdir -p ~/.codex
    cat > ~/.codex/config.toml <<EOF
[model_providers.maas]
name = "Huawei MaaS"
base_url = "${OPENAI_BASE}"
api_key = "\${HUAWEI_MAAS_API_KEY}"

[model]
provider = "maas"
name = "deepseek-v4-pro"
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

setup_dsh() {
  local name="dsh"
  if check_cmd dsh; then
    RESULTS[$name]="skipped (already installed)"
    return
  fi
  npm install -g @deepseek-ai/dsh 2>/dev/null
  if check_cmd dsh; then
    mkdir -p ~/.dsh
    cat > ~/.dsh/settings.yaml <<EOF
provider:
  name: openai
  base_url: ${OPENAI_BASE}
  api_key: \${HUAWEI_MAAS_API_KEY}
model: deepseek-v4-pro
EOF
    RESULTS[$name]="installed"
  else
    RESULTS[$name]="FAILED"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
  log "INFO" "Setting up 12 harnesses for MaaS backend"
  log "INFO" "OpenAI base:   ${OPENAI_BASE}"
  log "INFO" "Anthropic base: ${ANTHROPIC_BASE}"
  echo ""

  local harnesses=(
    setup_aider
    setup_openhands
    setup_claude_code
    setup_swe_agent
    setup_crush
    setup_goose
    setup_codearts_agent
    setup_pi
    setup_copilot_cli
    setup_trae_agent
    setup_codex
    setup_dsh
  )

  for fn in "${harnesses[@]}"; do
    local name="${fn#setup_}"
    log "SETUP" "Configuring ${name}..."
    $fn 2>/dev/null || RESULTS[$name]="FAILED (exception)"
  done

  # Summary
  echo ""
  echo "========================================"
  echo "  Harness Setup Summary"
  echo "========================================"
  local failed=0
  local skipped=0
  local installed=0
  for name in aider openhands claude_code swe_agent crush goose codearts_agent pi copilot_cli trae_agent codex dsh; do
    local status="${RESULTS[$name]:-NOT_RUN}"
    printf '  %-18s %s\n' "$name" "$status"
    case "$status" in
      installed*) ((installed++)) ;;
      skipped*)   ((skipped++)) ;;
      *)          ((failed++)) ;;
    esac
  done
  echo "========================================"
  echo "  Installed: $installed  Skipped: $skipped  Failed: $failed"
  echo "========================================"

  return $failed
}

main
