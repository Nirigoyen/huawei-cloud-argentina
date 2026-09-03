#!/usr/bin/env python3
"""Aggregate raw benchmark results and compute statistics.

Loads per-run JSON results from {results-dir}/raw/{harness}/.../*.json,
computes per-(harness, vertical) aggregates with bootstrap CIs,
McNemar's test for pairwise pass/fail comparison, and Cohen's d for
continuous metrics.

Outputs:
  {output-dir}/aggregated/{vertical}_summary.csv
  {output-dir}/aggregated/{harness}_detail.json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2


# -- Result loading ----------------------------------------------------------

def _get(data, *names, default=None):
    for n in names:
        if n in data:
            return data[n]
    return default


def load_results(results_dir):
    """Load all raw result JSONs from {results_dir}/raw/{harness}/..."""
    raw = Path(results_dir) / "raw"
    if not raw.is_dir():
        return []
    results = []
    for hdir in sorted(raw.iterdir()):
        if not hdir.is_dir():
            continue
        harness = hdir.name
        for jf in sorted(hdir.rglob("*.json")):
            try:
                d = json.loads(jf.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            d.setdefault("harness", harness)
            if "task_id" not in d:
                d["task_id"] = str(jf.parent.relative_to(hdir))
            if "vertical" not in d:
                tid = d["task_id"]
                d["vertical"] = tid.split("/")[0] if "/" in tid else "unknown"
            d.setdefault("run_id", jf.stem)
            d["passed"] = bool(_get(d, "passed", default=False))
            d["time_to_solution"] = float(_get(d, "time_to_solution", "time_to_solution_seconds", default=0.0))
            d["tokens_total"] = int(_get(d, "tokens_total", "total_tokens_consumed", "tokens", default=0))
            d["api_cost"] = float(_get(d, "api_cost", "api_cost_per_task", "cost", default=0.0))
            results.append(d)
    return results


# -- Statistics --------------------------------------------------------------

def bootstrap_ci(values, n_resamples=1000, rng=None):
    """95% bootstrap CI for the mean of *values* (list of floats)."""
    if rng is None:
        rng = np.random.default_rng()
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    arr = np.asarray(values, dtype=float)
    means = [float(np.mean(rng.choice(arr, size=n, replace=True))) for _ in range(n_resamples)]
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def mcnemar_test(outcomes_a, outcomes_b):
    """McNemar's chi-squared test with continuity correction.

    outcomes_a / outcomes_b: aligned 0/1 arrays for the same task set.
    Returns (statistic, p_value, n_discordant).
    """
    a = np.asarray(outcomes_a)
    b = np.asarray(outcomes_b)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    discordant_b = int(np.sum((a == 1) & (b == 0)))  # A pass, B fail
    discordant_c = int(np.sum((a == 0) & (b == 1)))  # A fail, B pass
    n_disc = discordant_b + discordant_c
    if n_disc == 0:
        return (0.0, 1.0, 0)
    stat = (abs(discordant_b - discordant_c) - 1) ** 2 / n_disc
    p = float(chi2.sf(stat, df=1))
    return (float(stat), p, n_disc)


def cohens_d(a, b):
    """Cohen's d effect size (independent samples, pooled SD)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    if pooled == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled)


# -- Aggregation -------------------------------------------------------------

def aggregate(results, rng):
    """Per-(harness, vertical) aggregate metrics with bootstrap CIs."""
    # group runs by (harness, vertical, task_id)
    by_hvt = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in results:
        by_hvt[r["harness"]][r["vertical"]][r["task_id"]].append(r)

    agg = {}  # (harness, vertical) -> metrics dict
    for harness, by_vt in by_hvt.items():
        for vertical, by_task in by_vt.items():
            task_pass_rates = []
            all_times = []
            total_tokens = 0
            total_cost = 0.0
            n_runs = 0
            for task_id, runs in by_task.items():
                passed = [1 if r["passed"] else 0 for r in runs]
                task_pass_rates.append(np.mean(passed))
                all_times.extend(r["time_to_solution"] for r in runs)
                total_tokens += sum(r["tokens_total"] for r in runs)
                total_cost += sum(r["api_cost"] for r in runs)
                n_runs += len(runs)
            mean_pr = float(np.mean(task_pass_rates)) if task_pass_rates else 0.0
            ci_lo, ci_hi = bootstrap_ci(task_pass_rates, rng=rng)
            agg[(harness, vertical)] = {
                "mean_pass_rate": mean_pr,
                "ci_low": ci_lo,
                "ci_high": ci_hi,
                "median_time": float(np.median(all_times)) if all_times else 0.0,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "n_tasks": len(by_task),
                "n_runs": n_runs,
            }
    return agg


def compute_pairwise(results):
    """McNemar + Cohen's d for every harness pair.

    Returns dict: harness_a -> harness_b -> {mcnemar, cohens_d}
    """
    harnesses = sorted({r["harness"] for r in results})

    # per-harness, per-task pass outcome (majority vote across runs)
    by_ht = defaultdict(lambda: defaultdict(list))
    for r in results:
        by_ht[r["harness"]][r["task_id"]].append(1 if r["passed"] else 0)

    # per-harness, per-task continuous values (median across runs)
    by_ht_time = defaultdict(dict)
    by_ht_tokens = defaultdict(dict)
    for r in results:
        h, t = r["harness"], r["task_id"]
        by_ht_time[h].setdefault(t, []).append(r["time_to_solution"])
        by_ht_tokens[h].setdefault(t, []).append(r["tokens_total"])

    def majority(passed_list):
        return 1 if np.mean(passed_list) >= 0.5 else 0

    pairwise = defaultdict(dict)
    for i, ha in enumerate(harnesses):
        for hb in harnesses[i + 1:]:
            common = sorted(set(by_ht[ha]) & set(by_ht[hb]))
            if not common:
                continue
            out_a = [majority(by_ht[ha][t]) for t in common]
            out_b = [majority(by_ht[hb][t]) for t in common]
            stat, p, ndisc = mcnemar_test(out_a, out_b)

            times_a = [float(np.median(by_ht_time[ha][t])) for t in common if by_ht_time[ha].get(t)]
            times_b = [float(np.median(by_ht_time[hb][t])) for t in common if by_ht_time[hb].get(t)]
            toks_a = [float(np.median(by_ht_tokens[ha][t])) for t in common if by_ht_tokens[ha].get(t)]
            toks_b = [float(np.median(by_ht_tokens[hb][t])) for t in common if by_ht_tokens[hb].get(t)]

            entry = {
                "mcnemar": {"statistic": stat, "p_value": p, "n_discordant": ndisc},
                "cohens_d": {
                    "time": cohens_d(times_a, times_b),
                    "tokens": cohens_d(toks_a, toks_b),
                },
            }
            pairwise[ha][hb] = entry
            pairwise[hb][ha] = {
                "mcnemar": {"statistic": stat, "p_value": p, "n_discordant": ndisc},
                "cohens_d": {
                    "time": -entry["cohens_d"]["time"],
                    "tokens": -entry["cohens_d"]["tokens"],
                },
            }
    return dict(pairwise)


# -- Output ------------------------------------------------------------------

CSV_COLS = [
    "harness", "mean_pass_rate", "ci_low", "ci_high",
    "median_time", "total_tokens", "total_cost", "n_tasks", "n_runs",
]


def write_outputs(agg, pairwise, output_dir):
    out = Path(output_dir) / "aggregated"
    out.mkdir(parents=True, exist_ok=True)

    verticals = sorted({v for (_, v) in agg})
    harnesses = sorted({h for (h, _) in agg})

    # per-vertical CSV
    for vert in verticals:
        path = out / f"{vert}_summary.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS)
            w.writeheader()
            for h in harnesses:
                m = agg.get((h, vert))
                if m is None:
                    continue
                row = {"harness": h}
                row.update(m)
                w.writerow(row)

    # per-harness detail JSON
    for h in harnesses:
        detail = {
            "harness": h,
            "verticals": {},
            "comparisons": pairwise.get(h, {}),
        }
        for vert in verticals:
            m = agg.get((h, vert))
            if m is not None:
                detail["verticals"][vert] = m
        (out / f"{h}_detail.json").write_text(json.dumps(detail, indent=2))

    return out


# -- Main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    results = load_results(args.results_dir)
    if not results:
        print("No results found", file=sys.stderr)
        sys.exit(1)

    rng = np.random.default_rng(args.seed)
    agg = aggregate(results, rng)
    pairwise = compute_pairwise(results)
    out = write_outputs(agg, pairwise, args.output_dir)

    n_h = len({r["harness"] for r in results})
    n_v = len({v for (_, v) in agg})
    print(f"Aggregated {len(results)} runs across {n_h} harnesses, {n_v} verticals -> {out}")


if __name__ == "__main__":
    main()
