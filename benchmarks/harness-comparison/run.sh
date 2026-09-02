#!/usr/bin/env bash
set -euo pipefail

# ---- configuration ----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"
MODEL_PROFILE=""
VERTICALS=""
HARNESSES=""
REPETITIONS=""

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --model-profile PROF   quality | speed | deterministic  (default: quality)
  --verticals LIST       comma-separated verticals to run (default: all)
  --harnesses LIST       comma-separated harnesses to run (default: all)
  --repetitions N        number of repetitions per task (default: 3)
  --help                 show this message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-profile) MODEL_PROFILE="$2"; shift 2 ;;
    --verticals)     VERTICALS="$2";     shift 2 ;;
    --harnesses)     HARNESSES="$2";     shift 2 ;;
    --repetitions)   REPETITIONS="$2";   shift 2 ;;
    --help|-h)       usage ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ---- prerequisite checks ----------------------------------------------------
check() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1"; exit 1; }; }

echo "=== Checking prerequisites ==="
check "$PYTHON"
check docker
check git

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon not running or no permission." >&2
  echo "  Start dockerd or add your user to the docker group:" >&2
  echo "  sudo usermod -aG docker \$USER && newgrp docker" >&2
  exit 1
fi

if [[ -z "${HUAWEI_MAAS_API_KEY:-}" ]]; then
  echo "ERROR: HUAWEI_MAAS_API_KEY env var is not set." >&2
  exit 1
fi

echo "  python:  $("$PYTHON" --version)"
echo "  docker:  $(docker --version)"
echo "  api key: set (${#HUAWEI_MAAS_API_KEY} chars)"
echo ""

# ---- venv -------------------------------------------------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  echo "=== Creating virtualenv ==="
  "$PYTHON" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
PYTHON=python  # use venv python from here on

# ---- verify MaaS ------------------------------------------------------------
echo "=== Verifying MaaS endpoints ==="
"$PYTHON" scripts/verify_maas.py

# ---- build docker images ----------------------------------------------------
echo ""
echo "=== Building Docker images ==="
for df in python node go rust java multi; do
  echo "  -> docker/Dockerfile.$df"
  docker build -q -f "docker/Dockerfile.$df" -t "bench-$df" docker/ || {
    echo "ERROR: failed to build Dockerfile.$df" >&2; exit 1; }
done

# ---- run benchmark ----------------------------------------------------------
echo ""
echo "=== Running benchmark ==="
ARGS=(--config config/maas.yaml)
[[ -n "$MODEL_PROFILE" ]] && ARGS+=(--model-profile "$MODEL_PROFILE")
[[ -n "$VERTICALS"     ]] && ARGS+=(--verticals "$VERTICALS")
[[ -n "$HARNESSES"     ]] && ARGS+=(--harnesses "$HARNESSES")
[[ -n "$REPETITIONS"   ]] && ARGS+=(--repetitions "$REPETITIONS")

"$PYTHON" runners/run_benchmark.py "${ARGS[@]}"

# ---- analyze + report -------------------------------------------------------
echo ""
echo "=== Analyzing results ==="
"$PYTHON" analysis/aggregate.py
"$PYTHON" analysis/bradley_terry.py
"$PYTHON" analysis/generate_report.py

echo ""
echo "=== Done ==="
echo "  Raw results:       results/raw/"
echo "  Aggregated stats:  results/aggregated/"
echo "  HTML report:       results/reports/"
