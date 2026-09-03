#!/usr/bin/env python3
"""Generic harness runner.

Launches a Docker container, copies task setup files, invokes the specified
harness adapter, captures results, and writes a JSON summary.

Usage:
    python run_harness.py \
        --harness aider \
        --task-dir tasks/code_generation/merge_intervals \
        --model-config config/models.yaml \
        --run-id run_001 \
        --output-dir results/raw
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Make adapters package importable
sys.path.insert(0, str(Path(__file__).parent))

log = logging.getLogger("run_harness")

LANGUAGE_IMAGES = {
    "python": "benchmark-python",
    "node": "benchmark-node",
    "javascript": "benchmark-node",
    "typescript": "benchmark-node",
    "go": "benchmark-go",
    "golang": "benchmark-go",
    "rust": "benchmark-rust",
    "java": "benchmark-java",
    "multi": "benchmark-multi",
    "terraform": "benchmark-multi",
    "ansible": "benchmark-multi",
    "yaml": "benchmark-multi",
    "sql": "benchmark-multi",
    "dockerfile": "benchmark-multi",
    "helm": "benchmark-multi",
    "bash": "benchmark-python",
    "shell": "benchmark-python",
}


def get_image(language: str) -> str:
    """Determine Docker image from task language."""
    lang = language.lower().strip()
    return LANGUAGE_IMAGES.get(lang, "benchmark-python")


def resolve_value(val):
    """Resolve ${ENV_VAR} references in a string."""
    if not isinstance(val, str):
        return val
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), val)


def resolve_env_vars(env_vars: dict) -> dict:
    return {k: resolve_value(v) for k, v in env_vars.items()}


def load_adapter(harness_name: str):
    """Dynamically load the adapter module for a harness."""
    module = importlib.import_module(f"adapters.{harness_name}")
    return module.Adapter()


def load_model_config(model_config_path: str, harness: str, model_profile: str = "quality") -> dict:
    """Load model config and harness-specific config.

    The model_config_path points to models.yaml which has profiles.
    We also load the harness config from config/harnesses/{harness}.yaml.
    """
    config = {}

    # Load models.yaml
    with open(model_config_path) as f:
        models_doc = yaml.safe_load(f)
    profiles = models_doc.get("profiles", {})
    selected = profiles.get(model_profile, profiles.get("quality", {}))
    config["model_id"] = selected.get("model_id", "")
    config["temperature"] = selected.get("temperature", 0.7)
    config["max_tokens"] = selected.get("max_tokens", 8192)

    # Load harness config
    harness_config_path = (
        Path(model_config_path).parent
        / "harnesses"
        / f"{harness}.yaml"
    )
    if harness_config_path.exists():
        with open(harness_config_path) as f:
            harness_doc = yaml.safe_load(f)
        config["env_vars"] = resolve_env_vars(
            harness_doc.get("env_vars", {})
        )
        config["invoke_template"] = harness_doc.get("invoke_template", "")
        config["harness_category"] = harness_doc.get("category", "")
        config["endpoint_type"] = harness_doc.get("endpoint_type", "")
    else:
        config["env_vars"] = {}

    return config


def create_container(image: str, name: str, env_vars: dict) -> str:
    """Create a detached Docker container."""
    cmd = ["docker", "run", "-d", "--name", name]
    for k, v in env_vars.items():
        cmd.extend(["-e", f"{k}={v}"])
    cmd.extend([image, "sleep", "infinity"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create container {name} from {image}: {result.stderr.strip()}"
        )
    log.info("Created container %s from %s", name, image)
    return name


def copy_to_container(container: str, src: str, dst: str) -> bool:
    """Copy files into the container."""
    result = subprocess.run(
        ["docker", "cp", src, f"{container}:{dst}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.warning("docker cp %s -> %s:%s failed: %s", src, container, dst, result.stderr.strip())
        return False
    return True


def copy_from_container(container: str, src: str, dst: str) -> bool:
    """Copy files out of the container."""
    result = subprocess.run(
        ["docker", "cp", f"{container}:{src}", dst],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.warning("docker cp %s:%s -> %s failed: %s", container, src, dst, result.stderr.strip())
        return False
    return True


def remove_container(container: str) -> None:
    """Force-remove a container."""
    subprocess.run(["docker", "rm", "-f", container], capture_output=True, text=True)
    log.info("Removed container %s", container)


def run(
    harness: str,
    task_dir: str,
    model_config_path: str,
    run_id: str,
    output_dir: str,
) -> dict:
    """Main run logic. Returns the result dict."""
    task_path = Path(task_dir)
    task_id = task_path.name

    # Read task.yaml
    task_yaml_path = task_path / "task.yaml"
    if not task_yaml_path.exists():
        raise FileNotFoundError(f"task.yaml not found in {task_dir}")
    with open(task_yaml_path) as f:
        task_config = yaml.safe_load(f)

    prompt = task_config.get("prompt", "")
    language = task_config.get("language", "python")
    timeout_seconds = task_config.get("timeout_seconds", 600)
    difficulty = task_config.get("difficulty", "unknown")

    log.info(
        "Task: %s | lang=%s | difficulty=%s | timeout=%ds",
        task_id, language, difficulty, timeout_seconds,
    )

    # Load model config
    model_profile = os.environ.get("MODEL_PROFILE", "quality")
    model_config = load_model_config(model_config_path, harness, model_profile)
    model_config["timeout_seconds"] = timeout_seconds

    # Determine Docker image
    image = get_image(language)

    # Container name
    container_name = f"bench-{harness}-{task_id}-{run_id}"[:63]

    # Output paths
    result_dir = Path(output_dir) / harness / task_id
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / f"{run_id}.json"
    workspace_dir = result_dir / f"{run_id}_workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Launch container
    try:
        container_id = create_container(image, container_name, model_config.get("env_vars", {}))
    except RuntimeError as e:
        log.error("Container creation failed: %s", e)
        return _write_error_result(result_path, harness, task_id, model_config, run_id, str(e))

    start_time = time.monotonic()

    try:
        # Copy setup files into container
        setup_dir = task_path / "setup"
        if setup_dir.exists():
            copy_to_container(container_id, f"{setup_dir}/.", "/workspace/")

        # Create marker file for change detection
        subprocess.run(
            ["docker", "exec", container_id, "touch", "/workspace/.benchmark_marker"],
            capture_output=True, text=True,
        )

        # Initialize git for adapters that need it
        subprocess.run(
            ["docker", "exec", "-w", "/workspace", container_id, "git", "init"],
            capture_output=True, text=True,
        )

        # Load and invoke adapter
        adapter = load_adapter(harness)
        adapter_result = adapter.invoke(prompt, container_id, model_config)

        duration = time.monotonic() - start_time

        # Copy workspace out of container for the evaluator
        copy_from_container(container_id, "/workspace/.", f"{workspace_dir}/")

        # Build result
        result = {
            "harness": harness,
            "task_id": task_id,
            "model": model_config.get("model_id", ""),
            "temperature": model_config.get("temperature", 0.7),
            "run_id": run_id,
            "exit_code": adapter_result["exit_code"],
            "duration_seconds": round(duration, 3),
            "stdout": adapter_result["stdout"],
            "stderr": adapter_result["stderr"],
            "output_files": adapter_result["output_files"],
            "workspace_dir": str(workspace_dir),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        log.info("Result written to %s (exit=%d, %.1fs)", result_path, result["exit_code"], duration)

        return result

    except Exception as e:
        log.exception("Run failed for %s/%s/%s", harness, task_id, run_id)
        duration = time.monotonic() - start_time
        return _write_error_result(
            result_path, harness, task_id, model_config, run_id, str(e), duration
        )
    finally:
        remove_container(container_id)


def _write_error_result(
    result_path: Path,
    harness: str,
    task_id: str,
    model_config: dict,
    run_id: str,
    error: str,
    duration: float = 0.0,
) -> dict:
    result = {
        "harness": harness,
        "task_id": task_id,
        "model": model_config.get("model_id", ""),
        "temperature": model_config.get("temperature", 0.7),
        "run_id": run_id,
        "exit_code": -1,
        "duration_seconds": round(duration, 3),
        "stdout": "",
        "stderr": error,
        "output_files": [],
        "workspace_dir": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description="Run a single harness on a single task")
    parser.add_argument("--harness", required=True, help="Harness name (e.g. aider)")
    parser.add_argument("--task-dir", required=True, help="Path to task directory")
    parser.add_argument("--model-config", required=True, help="Path to models.yaml")
    parser.add_argument("--run-id", required=True, help="Unique run identifier")
    parser.add_argument("--output-dir", required=True, help="Output directory for results")
    parser.add_argument("--model-profile", default="quality", help="Model profile name (quality/speed/deterministic)")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    os.environ["MODEL_PROFILE"] = args.model_profile

    result = run(
        harness=args.harness,
        task_dir=args.task_dir,
        model_config_path=args.model_config,
        run_id=args.run_id,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["exit_code"] == 0 else 1)


if __name__ == "__main__":
    main()
