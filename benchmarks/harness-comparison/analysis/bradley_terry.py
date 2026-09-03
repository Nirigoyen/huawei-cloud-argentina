#!/usr/bin/env python3
"""Compute Bradley-Terry model ratings for overall harness ranking.

Constructs a pairwise battle matrix from task-level pass/fail outcomes,
fits P(i>j) = expit(alpha * (r_i - r_j)) via MLE (L-BFGS-B),
scales ratings to Elo-like range (raw * 400 + 1000),
and computes bootstrap 95% CIs.

Outputs JSON: {rankings: [...], battles: {...}}
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

ALPHA = np.log(10)  # logistic scale so 1 rating unit ~ 1:10 odds


# -- Result loading (same schema as aggregate.py) -----------------------------

def _get(data, *names, default=None):
    for n in names:
        if n in data:
            return data[n]
    return default


def load_results(results_dir):
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
            d["passed"] = bool(_get(d, "passed", default=False))
            results.append(d)
    return results


# -- Battle matrix -----------------------------------------------------------

def _task_outcomes(results):
    """Return {harness: {task_id: 0|1}} using majority vote across runs."""
    by_ht = defaultdict(lambda: defaultdict(list))
    for r in results:
        by_ht[r["harness"]][r["task_id"]].append(1 if r["passed"] else 0)
    outcomes = {}
    for h, tasks in by_ht.items():
        outcomes[h] = {t: (1 if np.mean(v) >= 0.5 else 0) for t, v in tasks.items()}
    return outcomes


def build_battle_matrix(results, harnesses):
    """Wins matrix W[i][j] = number of tasks where i beats j (ties = 0.5)."""
    outcomes = _task_outcomes(results)
    n = len(harnesses)
    W = np.zeros((n, n))
    for i, hi in enumerate(harnesses):
        for j, hj in enumerate(harnesses):
            if i == j:
                continue
            common = set(outcomes.get(hi, {})) & set(outcomes.get(hj, {}))
            for t in common:
                oi, oj = outcomes[hi][t], outcomes[hj][t]
                if oi == 1 and oj == 0:
                    W[i][j] += 1
                elif oi == 0 and oj == 1:
                    pass  # W[j][i] += 1 handled in the other iteration
                else:
                    W[i][j] += 0.5  # tie
    return W


# -- BT model fitting --------------------------------------------------------

def fit_bt(W, alpha=ALPHA):
    """Fit Bradley-Terry ratings via MLE.

    Returns raw ratings (sum-to-zero constraint).
    """
    n = len(W)
    if n <= 1:
        return np.zeros(n)

    def nll(params):
        r = np.append(params, 0.0)
        diff = alpha * (r[:, None] - r[None, :])
        log_p = -np.logaddexp(0.0, -diff)  # log sigmoid
        return -float(np.sum(W * log_p))

    res = minimize(nll, np.zeros(n - 1), method="L-BFGS-B")
    ratings = np.append(res.x, 0.0)
    ratings -= ratings.mean()  # center
    return ratings


def scale_ratings(raw):
    """Elo-like scaling: raw * 400 + 1000."""
    return raw * 400.0 + 1000.0


# -- Bootstrap ---------------------------------------------------------------

def bootstrap_bt(results, harnesses, n_resamples=1000, rng=None):
    """Bootstrap 95% CIs for BT ratings by resampling tasks."""
    if rng is None:
        rng = np.random.default_rng()

    outcomes = _task_outcomes(results)
    # collect all (task, {harness: outcome}) rows
    all_tasks = sorted(set().union(*(set(o) for o in outcomes.values())))
    task_rows = []
    for t in all_tasks:
        row = {h: outcomes.get(h, {}).get(t) for h in harnesses}
        task_rows.append((t, row))

    n = len(harnesses)
    boot_ratings = []
    for _ in range(n_resamples):
        idx = rng.integers(0, len(task_rows), size=len(task_rows))
        sampled = [task_rows[k] for k in idx]
        W = np.zeros((n, n))
        for i, hi in enumerate(harnesses):
            for j, hj in enumerate(harnesses):
                if i == j:
                    continue
                for _, row in sampled:
                    oi, oj = row[hi], row[hj]
                    if oi is None or oj is None:
                        continue
                    if oi == 1 and oj == 0:
                        W[i][j] += 1
                    elif oi == 0 and oj == 1:
                        pass
                    else:
                        W[i][j] += 0.5
        r = fit_bt(W)
        boot_ratings.append(scale_ratings(r))

    boot_ratings = np.array(boot_ratings)
    lo = np.percentile(boot_ratings, 2.5, axis=0)
    hi = np.percentile(boot_ratings, 97.5, axis=0)
    return lo, hi


# -- Main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-resamples", type=int, default=1000)
    args = ap.parse_args()

    results = load_results(args.results_dir)
    if not results:
        print("No results found", file=sys.stderr)
        sys.exit(1)

    harnesses = sorted({r["harness"] for r in results})
    rng = np.random.default_rng(args.seed)

    W = build_battle_matrix(results, harnesses)
    raw = fit_bt(W)
    scaled = scale_ratings(raw)

    ci_lo, ci_hi = bootstrap_bt(results, harnesses, args.n_resamples, rng)

    # rankings sorted by rating desc
    order = np.argsort(scaled)[::-1]
    rankings = []
    for rank, idx in enumerate(order, 1):
        rankings.append({
            "harness": harnesses[idx],
            "rating": round(float(scaled[idx]), 1),
            "ci_low": round(float(ci_lo[idx]), 1),
            "ci_high": round(float(ci_hi[idx]), 1),
            "rank": rank,
        })

    # battles dict (computed from outcomes for exact win/loss/tie counts)
    outcomes = _task_outcomes(results)
    battles = {}
    for i, hi in enumerate(harnesses):
        battles[hi] = {}
        for j, hj in enumerate(harnesses):
            if i == j:
                continue
            common = set(outcomes.get(hi, {})) & set(outcomes.get(hj, {}))
            w = l = t = 0
            for tk in common:
                oi, oj = outcomes[hi][tk], outcomes[hj][tk]
                if oi == 1 and oj == 0: w += 1
                elif oi == 0 and oj == 1: l += 1
                else: t += 1
            battles[hi][hj] = {"wins": w, "losses": l, "ties": t}

    output = {"rankings": rankings, "battles": battles}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"Bradley-Terry ratings -> {args.output}")
    for r in rankings:
        print(f"  #{r['rank']} {r['harness']}: {r['rating']:.0f} [{r['ci_low']:.0f}, {r['ci_high']:.0f}]")


if __name__ == "__main__":
    main()
