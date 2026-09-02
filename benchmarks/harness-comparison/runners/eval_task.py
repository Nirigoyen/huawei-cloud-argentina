#!/usr/bin/env python3
"""Generic task evaluator.

Launches a fresh Docker container, applies task setup files + harness output
files, runs eval.py, and captures the evaluation result.

Usage:
    python eval_task.py \
        --task-dir tasks/code_generation/merge_intervals \
        --harness-output results/raw/aider/merge_intervals/run_001.json \
        --output results/raw/aider/merge_intervals/run_001_eval.json
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

log = logging.getLogger("eval_task")

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
    return LANGUAGE_IMAGES.get(language.lower().strip(), "benchmark-python")


def create_container(image: str, name: str) -> str:
    result = subprocess.run(
        ["docker", "run", "-d", "--name", name, image, "sleep", "infinity"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create container: {result.stderr.strip()}")
    log.info("Created container %s", name)
    return name


def copy_to_container(container: str, src: str, dst: str) -> bool:
    result = subprocess.run(
        ["docker", "cp", src, f"{container}:{dst}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.warning("docker cp failed: %s", result.stderr.strip())
        return False
    return True


def remove_container(container: str) -> None:
    subprocess.run(["docker", "rm", "-f", container], capture_output=True, text=True)


def evaluate(task_dir: str, harness_output_path: str, output_path: str) -> dict:
    """Main evaluation logic. Returns the eval result dict."""
    task_path = Path(task_dir)
    task_id = task_path.name

    # Read task.yaml
    with open(task_path / "task.yaml") as f:
        task_config = yaml.safe_load(f)
    language = task_config.get("language", "python")
    timeout_seconds = task_config.get("timeout_seconds", 300)

    # Read harness output
    with open(harness_output_path) as f:
        harness_output = json.load(f)

    image = get_image(language)
    container_name = f"eval-{task_id}-{harness_output.get('run_id', 'run')}"[:63]

    start_time = time.monotonic()

    try:
        container_id = create_container(image, container_name)
    except RuntimeError as e:
        return _write_failed(output_path, task_id, str(e))

    try:
        # Copy setup files
        setup_dir = task_path / "setup"
        if setup_dir.exists():
            copy_to_container(container_id, f"{setup_dir}/.", "/workspace/")

        # Copy tests directory if it exists
        tests_dir = task_path / "tests"
        if tests_dir.exists():
            copy_to_container(container_id, f"{tests_dir}/.", "/workspace/tests/")

        # Apply harness output files (overwrite setup with harness-generated)
        workspace_dir = harness_output.get("workspace_dir", "")
        if workspace_dir and Path(workspace_dir).exists():
            copy_to_container(container_id, f"{workspace_dir}/.", "/workspace/")

        # Copy eval.py into container
        eval_script = task_path / "eval.py"
        if eval_script.exists():
            copy_to_container(container_id, str(eval_script), "/workspace/eval.py")
        else:
            return _write_failed(
                output_path, task_id, "eval.py not found in task directory"
            )

        # Run eval.py inside container
        log.info("Running eval.py for task %s", task_id)
        result = subprocess.run(
            ["docker", "exec", "-w", "/workspace", container_id, "python", "eval.py"],
            capture_output=True, text=True, timeout=timeout_seconds,
        )

        duration = time.monotonic() - start_time

        if result.returncode == 0:
            # Parse JSON from stdout
            try:
                eval_result = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                # eval.py might print non-JSON before the JSON
                lines = result.stdout.strip().splitlines()
                json_line = None
                for line in lines:
                    line = line.strip()
                    if line.startswith("{"):
                        try:
                            json.loads(line)
                            json_line = line
                            break
                        except json.JSONDecodeError:
                            continue
                if json_line:
                    eval_result = json.loads(json_line)
                else:
                    eval_result = {
                        "passed": False,
                        "metrics": {},
                        "details": f"eval.py produced non-JSON output: {result.stdout[:500]}",
                    }
        else:
            eval_result = {
                "passed": False,
                "metrics": {},
                "details": f"eval.py exited with code {result.returncode}: {result.stderr[:500]}",
            }

        # Enrich with metadata
        eval_result["task_id"] = task_id
        eval_result["harness"] = harness_output.get("harness", "")
        eval_result["run_id"] = harness_output.get("run_id", "")
        eval_result["model"] = harness_output.get("model", "")
        eval_result["eval_duration_seconds"] = round(duration, 3)
        eval_result["timestamp"] = datetime.now(timezone.utc).isoformat()
        eval_result.setdefault("passed", False)
        eval_result.setdefault("metrics", {})
        eval_result.setdefault("details", "")

        with open(output_path, "w") as f:
            json.dump(eval_result, f, indent=2)
        log.info(
            "Eval result: %s/%s passed=%s (%.1fs)",
            eval_result["harness"], task_id, eval_result["passed"], duration,
        )
        return eval_result

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start_time
        return _write_failed(
            output_path, task_id, f"Evaluation timed out after {timeout_seconds}s",
            harness_output, duration,
        )
    except Exception as e:
        log.exception("Evaluation failed for task %s", task_id)
        duration = time.monotonic() - start_time
        return _write_failed(output_path, task_id, str(e), harness_output, duration)
    finally:
        remove_container(container_id)


def _write_failed(
    output_path: str,
    task_id: str,
    error: str,
    harness_output: dict | None = None,
    duration: float = 0.0,
) -> dict:
    result = {
        "passed": False,
        "metrics": {},
        "details": error,
        "task_id": task_id,
        "harness": (harness_output or {}).get("harness", ""),
        "run_id": (harness_output or {}).get("run_id", ""),
        "model": (harness_output or {}).get("model", ""),
        "eval_duration_seconds": round(duration, 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate a single task run")
    parser.add_argument("--task-dir", required=True, help="Path to task directory")
    parser.add_argument("--harness-output", required=True, help="Path to harness output JSON")
    parser.add_argument("--output", required=True, help="Output path for eval result JSON")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    result = evaluate(args.task_dir, args.harness_output, args.output)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("passed") else 1)


if __name__ == "__main__":
    main()
