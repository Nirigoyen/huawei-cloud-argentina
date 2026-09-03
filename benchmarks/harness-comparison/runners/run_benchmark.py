#!/usr/bin/env python3
"""Top-level benchmark orchestrator.

Runs N harnesses against M tasks with R repetitions, using parallel workers.
Each run consists of: run_harness.py (invoke harness) + eval_task.py (evaluate output).

Usage:
    python run_benchmark.py \
        --config config/benchmark.yaml \
        --harnesses aider,claude_code \
        --verticals code_generation,debugging \
        --model-profile quality \
        --repetitions 3 \
        --workers 8 \
        --resume
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import yaml

log = logging.getLogger("run_benchmark")

BENCHMARK_ROOT = Path(__file__).parent.parent
RUNNERS_DIR = Path(__file__).parent


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_task_list(verticals: list[str], tasks_root: Path) -> list[dict]:
    """Scan tasks/{vertical}/ directories for task.yaml files."""
    tasks = []
    for vertical in verticals:
        vertical_dir = tasks_root / vertical
        if not vertical_dir.exists():
            log.warning("Vertical directory not found: %s", vertical_dir)
            continue
        for task_yaml in sorted(vertical_dir.glob("*/task.yaml")):
            task_dir = task_yaml.parent
            with open(task_yaml) as f:
                task_config = yaml.safe_load(f)
            tasks.append({
                "task_dir": str(task_dir),
                "task_id": task_dir.name,
                "vertical": vertical,
                "language": task_config.get("language", "python"),
                "difficulty": task_config.get("difficulty", "unknown"),
            })
    return tasks


def _run_single(item: dict) -> dict:
    """Worker function: run one (harness, task, run_id) triple.

    Calls run_harness.py then eval_task.py as subprocesses.
    Returns a combined result dict.
    """
    harness = item["harness"]
    task_dir = item["task_dir"]
    task_id = item["task_id"]
    vertical = item["vertical"]
    run_id = item["run_id"]
    model_config = item["model_config"]
    output_dir = item["output_dir"]
    model_profile = item["model_profile"]
    timeout = item.get("timeout", 600)

    result = {
        "harness": harness,
        "task_id": task_id,
        "vertical": vertical,
        "run_id": run_id,
        "passed": False,
        "harness_exit_code": -1,
        "duration_seconds": 0,
        "error": None,
    }

    start = time.monotonic()

    # Step 1: Run harness
    harness_output_path = Path(output_dir) / harness / task_id / f"{run_id}.json"
    harness_cmd = [
        sys.executable, str(RUNNERS_DIR / "run_harness.py"),
        "--harness", harness,
        "--task-dir", task_dir,
        "--model-config", model_config,
        "--run-id", run_id,
        "--output-dir", output_dir,
        "--model-profile", model_profile,
    ]
    try:
        harness_proc = subprocess.run(
            harness_cmd, capture_output=True, text=True, timeout=timeout * 2,
        )
        result["harness_exit_code"] = harness_proc.returncode
        if harness_proc.returncode != 0:
            log.warning(
                "run_harness.py failed for %s/%s/%s (exit %d)",
                harness, task_id, run_id, harness_proc.returncode,
            )
    except subprocess.TimeoutExpired:
        result["error"] = f"Harness runner timed out after {timeout * 2}s"
        result["duration_seconds"] = round(time.monotonic() - start, 3)
        return result

    # Step 2: Run evaluation
    eval_output_path = Path(output_dir) / harness / task_id / f"{run_id}_eval.json"
    eval_cmd = [
        sys.executable, str(RUNNERS_DIR / "eval_task.py"),
        "--task-dir", task_dir,
        "--harness-output", str(harness_output_path),
        "--output", str(eval_output_path),
    ]
    try:
        eval_proc = subprocess.run(
            eval_cmd, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result["error"] = f"Evaluation timed out after {timeout}s"
        result["duration_seconds"] = round(time.monotonic() - start, 3)
        return result

    # Load eval result
    if eval_output_path.exists():
        try:
            with open(eval_output_path) as f:
                eval_result = json.load(f)
            result["passed"] = eval_result.get("passed", False)
            result["metrics"] = eval_result.get("metrics", {})
            result["details"] = eval_result.get("details", "")
        except json.JSONDecodeError as e:
            result["error"] = f"Failed to parse eval result: {e}"
    else:
        result["error"] = "Eval output file not created"

    result["duration_seconds"] = round(time.monotonic() - start, 3)
    return result


def print_summary(results: list[dict], harnesses: list[str], verticals: list[str]) -> None:
    """Print a summary table of pass rates by harness x vertical."""
    # Aggregate: pass_rate[harness][vertical] = passed/total
    stats = defaultdict(lambda: defaultdict(lambda: {"passed": 0, "total": 0}))
    for r in results:
        s = stats[r["harness"]][r["vertical"]]
        s["total"] += 1
        if r["passed"]:
            s["passed"] += 1

    # Also per-harness totals
    harness_totals = defaultdict(lambda: {"passed": 0, "total": 0})
    for r in results:
        harness_totals[r["harness"]]["total"] += 1
        if r["passed"]:
            harness_totals[r["harness"]]["passed"] += 1

    # Column widths
    harness_w = max(len(h) for h in harnesses) if harnesses else 10
    harness_w = max(harness_w, 8)  # "Harness" header
    col_w = 10

    # Header
    header = f"{'Harness':<{harness_w}} |"
    for v in verticals:
        header += f" {v[:col_w]:>{col_w}} |"
    header += f" {'Total':>{col_w}}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))

    # Rows
    for h in harnesses:
        row = f"{h:<{harness_w}} |"
        for v in verticals:
            s = stats[h][v]
            if s["total"] == 0:
                row += f" {'--':>{col_w}} |"
            else:
                pct = s["passed"] / s["total"] * 100
                row += f" {pct:>6.1f}% |"
        ht = harness_totals[h]
        if ht["total"] == 0:
            row += f" {'--':>{col_w}}"
        else:
            pct = ht["passed"] / ht["total"] * 100
            row += f" {pct:>6.1f}%"
        print(row)

    print("=" * len(header))

    # Overall stats
    total_runs = len(results)
    total_passed = sum(1 for r in results if r["passed"])
    total_errors = sum(1 for r in results if r.get("error"))
    if total_runs > 0:
        print(f"\nTotal: {total_passed}/{total_runs} passed ({total_passed/total_runs*100:.1f}%), {total_errors} errors")


def main():
    parser = argparse.ArgumentParser(description="Run benchmark: N harnesses x M tasks x R repetitions")
    parser.add_argument("--config", default=str(BENCHMARK_ROOT / "config" / "benchmark.yaml"),
                        help="Path to benchmark config YAML")
    parser.add_argument("--harnesses", default=None,
                        help="Comma-separated harness names (overrides config)")
    parser.add_argument("--verticals", default=None,
                        help="Comma-separated vertical names (overrides config)")
    parser.add_argument("--model-profile", default="quality",
                        help="Model profile name (quality/speed/deterministic)")
    parser.add_argument("--model-config", default=str(BENCHMARK_ROOT / "config" / "models.yaml"),
                        help="Path to models.yaml")
    parser.add_argument("--repetitions", type=int, default=None,
                        help="Number of repetitions per run (overrides config)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers (overrides config)")
    parser.add_argument("--output-dir", default=str(BENCHMARK_ROOT / "results" / "raw"),
                        help="Output directory for raw results")
    parser.add_argument("--resume", action="store_true",
                        help="Skip runs that already have eval results")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load config
    config = load_config(args.config)
    defaults = config.get("defaults", {})

    # Determine harnesses
    if args.harnesses:
        harnesses = [h.strip() for h in args.harnesses.split(",")]
    else:
        harnesses = config.get("harnesses", [])

    # Determine verticals
    if args.verticals:
        verticals = [v.strip() for v in args.verticals.split(",")]
    else:
        verticals = config.get("verticals", [])

    # Other params
    repetitions = args.repetitions or defaults.get("repetitions", 3)
    workers = args.workers or defaults.get("workers", 8)
    timeout = defaults.get("timeout_seconds", 600)

    # Build task list
    tasks_root = BENCHMARK_ROOT / "tasks"
    tasks = build_task_list(verticals, tasks_root)
    log.info("Found %d tasks across %d verticals", len(tasks), len(verticals))

    # Build run list
    runs = []
    for harness in harnesses:
        for task in tasks:
            for rep in range(repetitions):
                run_id = f"run_{rep + 1:03d}"
                eval_path = Path(args.output_dir) / harness / task["task_id"] / f"{run_id}_eval.json"

                if args.resume and eval_path.exists():
                    log.debug("Skipping (resume): %s/%s/%s", harness, task["task_id"], run_id)
                    continue

                runs.append({
                    "harness": harness,
                    "task_dir": task["task_dir"],
                    "task_id": task["task_id"],
                    "vertical": task["vertical"],
                    "run_id": run_id,
                    "model_config": args.model_config,
                    "output_dir": args.output_dir,
                    "model_profile": args.model_profile,
                    "timeout": timeout,
                })

    total = len(runs)
    if total == 0:
        print("No runs to execute (all skipped via --resume or no tasks found).")
        return

    log.info("Total runs: %d (harnesses=%d, tasks=%d, reps=%d, workers=%d)",
             total, len(harnesses), len(tasks), repetitions, workers)
    print(f"\nStarting {total} runs with {workers} workers...\n")

    # Run log
    run_log_path = BENCHMARK_ROOT / "results" / "run_log.jsonl"
    run_log_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    completed = 0
    start_time = time.monotonic()

    with open(run_log_path, "a") as run_log, Pool(min(workers, total)) as pool:
        for result in pool.imap_unordered(_run_single, runs):
            completed += 1
            results.append(result)
            elapsed = time.monotonic() - start_time

            # Write to run log
            log_entry = {
                **result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "completed": completed,
                "total": total,
            }
            run_log.write(json.dumps(log_entry) + "\n")
            run_log.flush()

            # Progress output
            status = "PASS" if result["passed"] else "FAIL"
            avg = elapsed / completed
            remaining = (total - completed) * avg / workers
            print(
                f"[{completed}/{total}] {result['harness']}/{result['task_id']}/{result['run_id']} "
                f"-> {status} ({result['duration_seconds']:.1f}s) "
                f"| ETA: {remaining:.0f}s ({remaining/60:.1f}m)"
            )

    total_elapsed = time.monotonic() - start_time
    print(f"\nCompleted {completed}/{total} runs in {total_elapsed:.1f}s ({total_elapsed/60:.1f}m)")

    # Print summary table
    print_summary(results, harnesses, verticals)

    # Write summary JSON
    summary_path = BENCHMARK_ROOT / "results" / "summary.json"
    summary = {
        "total_runs": total,
        "completed": completed,
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "errors": sum(1 for r in results if r.get("error")),
        "duration_seconds": round(total_elapsed, 3),
        "model_profile": args.model_profile,
        "harnesses": harnesses,
        "verticals": verticals,
        "repetitions": repetitions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info("Summary written to %s", summary_path)


if __name__ == "__main__":
    main()
