#!/usr/bin/env python3
"""Generate a self-contained HTML dashboard from aggregated results.

Reads per-vertical CSVs and per-harness detail JSONs from the aggregated
directory, plus the Bradley-Terry rankings JSON, and produces a single
HTML file with inline CSS and inline SVG charts (no external deps).
"""

import argparse
import base64
import csv
import html
import json
import sys
from pathlib import Path

import numpy as np


# -- Data loading ------------------------------------------------------------

def read_csvs(aggregated_dir):
    """Return {vertical: [row dicts]} from {vertical}_summary.csv files."""
    csvs = {}
    for p in sorted(Path(aggregated_dir).glob("*_summary.csv")):
        vert = p.stem.removesuffix("_summary")
        with open(p, newline="") as f:
            csvs[vert] = list(csv.DictReader(f))
    return csvs


def read_details(aggregated_dir):
    """Return {harness: detail dict} from {harness}_detail.json files."""
    details = {}
    for p in sorted(Path(aggregated_dir).glob("*_detail.json")):
        h = p.stem.removesuffix("_detail")
        details[h] = json.loads(p.read_text())
    return details


def compute_overall(csvs):
    """Aggregate per-harness totals across all verticals."""
    by_h = {}
    for vert, rows in csvs.items():
        for row in rows:
            h = row["harness"]
            if h not in by_h:
                by_h[h] = {"harness": h, "pass_rates": [], "times": [], "tokens": 0.0, "cost": 0.0, "n_tasks": 0, "n_runs": 0}
            d = by_h[h]
            pr = float(row.get("mean_pass_rate", 0))
            d["pass_rates"].append(pr)
            d["times"].append(float(row.get("median_time", 0)))
            d["tokens"] += float(row.get("total_tokens", 0))
            d["cost"] += float(row.get("total_cost", 0))
            d["n_tasks"] += int(row.get("n_tasks", 0))
            d["n_runs"] += int(row.get("n_runs", 0))
    for d in by_h.values():
        d["mean_pass_rate"] = float(np.mean(d["pass_rates"])) if d["pass_rates"] else 0.0
        d["median_time"] = float(np.median(d["times"])) if d["times"] else 0.0
    return by_h


# -- SVG helpers -------------------------------------------------------------

def esc(s):
    return html.escape(str(s))


def svg_bar_chart(title, labels, values, ci_los, ci_his, w=820, h=380):
    """Vertical bar chart with error bars. values in [0,1]."""
    n = len(labels)
    if n == 0:
        return f'<p class="empty">No data for {esc(title)}</p>'
    ml, mr, mt, mb = 70, 30, 50, 80
    cw, ch = w - ml - mr, h - mt - mb
    bw = cw / n * 0.65
    gap = cw / n
    parts = [f'<svg viewBox="0 0 {w} {h}" class="chart">']

    # title
    parts.append(f'<text x="{w/2}" y="22" text-anchor="middle" class="chart-title">{esc(title)}</text>')

    # gridlines + y-axis labels
    for i in range(5):
        yv = i / 4
        y = mt + ch * (1 - yv)
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+cw}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" class="axis">{yv:.2f}</text>')

    # bars + error bars
    for i, (label, val, lo, hi) in enumerate(zip(labels, values, ci_los, ci_his)):
        x = ml + gap * i + (gap - bw) / 2
        bh = ch * max(val, 0)
        y = mt + ch - bh
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" class="bar"/>')
        # error bar
        ey_lo = mt + ch * (1 - max(lo, 0))
        ey_hi = mt + ch * (1 - min(hi, 1))
        ex = x + bw / 2
        parts.append(f'<line x1="{ex:.1f}" y1="{ey_lo:.1f}" x2="{ex:.1f}" y2="{ey_hi:.1f}" class="errbar"/>')
        parts.append(f'<line x1="{ex-4:.1f}" y1="{ey_lo:.1f}" x2="{ex+4:.1f}" y2="{ey_lo:.1f}" class="errbar"/>')
        parts.append(f'<line x1="{ex-4:.1f}" y1="{ey_hi:.1f}" x2="{ex+4:.1f}" y2="{ey_hi:.1f}" class="errbar"/>')
        # value label
        parts.append(f'<text x="{ex:.1f}" y="{y-5:.1f}" text-anchor="middle" class="bar-val">{val:.2f}</text>')
        # x label (rotated)
        lx = ml + gap * i + gap / 2
        parts.append(f'<text x="{lx:.1f}" y="{mt+ch+18:.1f}" text-anchor="end" class="axis" transform="rotate(-35 {lx:.1f} {mt+ch+18:.1f})">{esc(label)}</text>')

    parts.append(f'<line x1="{ml}" y1="{mt+ch}" x2="{ml+cw}" y2="{mt+ch}" class="axis-line"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ch}" class="axis-line"/>')
    parts.append(f'<text x="{ml-50}" y="{mt+ch/2:.1f}" text-anchor="middle" class="axis" transform="rotate(-90 {ml-50} {mt+ch/2:.1f})">Pass Rate</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def _nice_scale(vals):
    """Axis max with a little headroom, rounded nicely."""
    if not vals or max(vals) <= 0:
        return 1.0
    m = max(vals) * 1.1
    mag = 10 ** np.floor(np.log10(m))
    return float(np.ceil(m / mag) * mag)


def svg_scatter(title, points, x_label, y_label="Pass Rate", w=820, h=460):
    """Scatter plot with Pareto front. points: [{label, x, y}]."""
    valid = [p for p in points if p["x"] is not None and p["y"] is not None]
    if not valid:
        return f'<p class="empty">No data for {esc(title)}</p>'
    ml, mr, mt, mb = 70, 30, 50, 60
    cw, ch = w - ml - mr, h - mt - mb
    x_max = _nice_scale([p["x"] for p in valid])
    y_max = 1.0

    def sx(v):
        return ml + cw * (v / x_max if x_max else 0)

    def sy(v):
        return mt + ch * (1 - v / y_max)

    parts = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    parts.append(f'<text x="{w/2}" y="22" text-anchor="middle" class="chart-title">{esc(title)}</text>')

    # gridlines
    for i in range(5):
        yv = i / 4
        y = mt + ch * (1 - yv)
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml+cw}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" class="axis">{yv:.2f}</text>')
    for i in range(5):
        xv = x_max * i / 4
        x = ml + cw * i / 4
        parts.append(f'<text x="{x:.1f}" y="{mt+ch+18:.1f}" text-anchor="middle" class="axis">{xv:.2g}</text>')

    # Pareto front (minimize x, maximize y)
    sorted_pts = sorted(valid, key=lambda p: (p["x"], -p["y"]))
    pareto = []
    best_y = -1
    for p in sorted_pts:
        if p["y"] > best_y:
            pareto.append(p)
            best_y = p["y"]
    if len(pareto) >= 2:
        pts_str = " ".join(f"{sx(p['x']):.1f},{sy(p['y']):.1f}" for p in pareto)
        parts.append(f'<polyline points="{pts_str}" class="pareto"/>')

    # points
    for p in valid:
        px, py = sx(p["x"]), sy(p["y"])
        is_pareto = p in pareto
        cls = "pareto-pt" if is_pareto else "scatter-pt"
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" class="{cls}"/>')
        parts.append(f'<text x="{px+9:.1f}" y="{py+4:.1f}" class="scatter-lbl">{esc(p["label"])}</text>')

    parts.append(f'<line x1="{ml}" y1="{mt+ch}" x2="{ml+cw}" y2="{mt+ch}" class="axis-line"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ch}" class="axis-line"/>')
    parts.append(f'<text x="{w/2}" y="{h-8}" text-anchor="middle" class="axis">{esc(x_label)}</text>')
    parts.append(f'<text x="{ml-50}" y="{mt+ch/2:.1f}" text-anchor="middle" class="axis" transform="rotate(-90 {ml-50} {mt+ch/2:.1f})">{esc(y_label)}</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def _p_color(p):
    """Green (significant, low p) -> red (not significant, high p)."""
    t = max(0.0, min(1.0, p))
    r = int(16 + t * (239 - 16))
    g = int(185 + t * (68 - 185))
    b = int(129 + t * (52 - 129))
    return f"rgb({r},{g},{b})"


def svg_heatmap(title, harnesses, p_matrix, w=620, h=620):
    """harness x harness heatmap colored by McNemar p-value."""
    n = len(harnesses)
    if n == 0:
        return f'<p class="empty">No data for {esc(title)}</p>'
    ml = 120
    cell = min((w - ml - 20) / n, (h - 50 - 20) / n)
    gw, gh = cell * n, cell * n
    parts = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    parts.append(f'<text x="{w/2}" y="22" text-anchor="middle" class="chart-title">{esc(title)}</text>')

    for i, hi in enumerate(harnesses):
        parts.append(f'<text x="{ml-6}" y="{50+cell*i+cell/2+4:.1f}" text-anchor="end" class="axis">{esc(hi)}</text>')
        parts.append(f'<text x="{ml+cell*i+cell/2:.1f}" y="44" text-anchor="middle" class="axis" transform="rotate(-45 {ml+cell*i+cell/2:.1f} 44)">{esc(hi)}</text>')
        for j, hj in enumerate(harnesses):
            x, y = ml + cell * j, 50 + cell * i
            if i == j:
                parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="#e5e7eb"/>')
                parts.append(f'<text x="{x+cell/2:.1f}" y="{y+cell/2+4:.1f}" text-anchor="middle" class="heatmap-val">-</text>')
            else:
                p = p_matrix.get((hi, hj), 1.0)
                parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="{_p_color(p)}" stroke="#fff"/>')
                parts.append(f'<text x="{x+cell/2:.1f}" y="{y+cell/2+4:.1f}" text-anchor="middle" class="heatmap-val">{p:.2f}</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


# -- HTML sections -----------------------------------------------------------

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#f5f5f5;color:#1f2937;line-height:1.5}
.container{max-width:1200px;margin:0 auto;padding:2rem}
h1{font-size:1.8rem;margin-bottom:.5rem}
h2{font-size:1.4rem;margin:2rem 0 1rem;border-bottom:2px solid #2563eb;padding-bottom:.3rem}
h3{font-size:1.1rem;margin:1rem 0 .5rem}
.card{background:#fff;border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:1.5rem}
.chart{width:100%;height:auto}
.chart-title{font-size:13px;font-weight:600;fill:#1f2937}
.bar{fill:#2563eb}
.bar-val{font-size:11px;fill:#374151;text-anchor:middle}
.errbar{stroke:#ef4444;stroke-width:1.5}
.grid{stroke:#e5e7eb;stroke-width:1}
.axis{font-size:11px;fill:#6b7280}
.axis-line{stroke:#374151;stroke-width:1.5}
.scatter-pt{fill:#6b7280;opacity:.7}
.pareto-pt{fill:#2563eb;stroke:#1e40af;stroke-width:2}
.pareto{fill:none;stroke:#10b981;stroke-width:2;stroke-dasharray:5,3}
.scatter-lbl{font-size:10px;fill:#374151}
.heatmap-val{font-size:9px;fill:#1f2937}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{padding:.5rem .75rem;text-align:left;border-bottom:1px solid #e5e7eb}
th{background:#f9fafb;font-weight:600}
tr:hover{background:#f9fafb}
.rank{font-weight:700;font-size:1.1rem;color:#2563eb}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:4px;font-size:.8rem;font-weight:600}
.badge-green{background:#d1fae5;color:#065f46}
.badge-amber{background:#fef3c7;color:#92400e}
.badge-red{background:#fee2e2;color:#991b1b}
.empty{color:#9ca3af;font-style:italic;padding:1rem}
.use-case{margin-bottom:1rem}
.use-case h3{color:#2563eb}
.strength{color:#065f46}
.weakness{color:#991b1b}
.export-link{display:inline-block;margin:.25rem .5rem;padding:.4rem .8rem;background:#2563eb;color:#fff;border-radius:4px;text-decoration:none;font-size:.85rem}
.export-link:hover{background:#1e40af}
"""


def section_executive(overall, rankings):
    """Top-3 per use case."""
    if not overall:
        return '<section id="exec"><h2>Executive Summary</h2><p class="empty">No data.</p></section>'

    items = list(overall.values())
    max_cost = max((d["cost"] for d in items), default=1) or 1

    def sort_key(d, mode):
        pr = d["mean_pass_rate"]
        cost = d["cost"]
        if mode == "cost-sensitive":
            return pr / (cost + 1e-9)
        if mode == "quality-first":
            return pr
        return pr - 0.15 * (cost / max_cost)

    cases = [
        ("cost-sensitive", "Cost-Sensitive (best value per dollar)"),
        ("quality-first", "Quality-First (highest pass rate)"),
        ("balanced", "Balanced (quality with cost penalty)"),
    ]
    parts = ['<section id="exec"><h2>Executive Summary</h2><div class="card">']
    for mode, label in cases:
        top3 = sorted(items, key=lambda d: sort_key(d, mode), reverse=True)[:3]
        parts.append(f'<div class="use-case"><h3>{label}</h3><table><tr><th>Rank</th><th>Harness</th><th>Pass Rate</th><th>Total Cost</th><th>Median Time</th></tr>')
        for i, d in enumerate(top3, 1):
            parts.append(f'<tr><td class="rank">#{i}</td><td>{esc(d["harness"])}</td><td>{d["mean_pass_rate"]:.1%}</td><td>${d["cost"]:.4f}</td><td>{d["median_time"]:.1f}s</td></tr>')
        parts.append('</table></div>')
    parts.append('</div></section>')
    return '\n'.join(parts)


def section_leaderboard(rankings):
    parts = ['<section id="leaderboard"><h2>Overall Leaderboard</h2><div class="card">']
    rks = rankings.get("rankings", [])
    if not rks:
        parts.append('<p class="empty">No rankings available.</p>')
    else:
        parts.append('<table><tr><th>Rank</th><th>Harness</th><th>BT Rating</th><th>95% CI</th></tr>')
        for r in rks:
            parts.append(f'<tr><td class="rank">#{r["rank"]}</td><td>{esc(r["harness"])}</td><td>{r["rating"]:.0f}</td><td>[{r["ci_low"]:.0f}, {r["ci_high"]:.0f}]</td></tr>')
        parts.append('</table>')
        # inline SVG error bar chart
        names = [r["harness"] for r in rks]
        vals = [(r["rating"] - 1000) / 400 for r in rks]  # back to raw for [0,1]ish
        los = [(r["ci_low"] - 1000) / 400 for r in rks]
        his = [(r["ci_high"] - 1000) / 400 for r in rks]
        # normalize to 0-1 for the bar chart
        all_v = vals + los + his
        mn, mx = min(all_v), max(all_v)
        rng = mx - mn if mx > mn else 1
        vals2 = [(v - mn) / rng for v in vals]
        los2 = [(v - mn) / rng for v in los]
        his2 = [(v - mn) / rng for v in his]
        parts.append(svg_bar_chart("BT Ratings (normalized)", names, vals2, los2, his2))
    parts.append('</div></section>')
    return '\n'.join(parts)


def section_verticals(csvs):
    parts = ['<section id="verticals"><h2>Per-Vertical Performance</h2>']
    for vert, rows in sorted(csvs.items()):
        if not rows:
            continue
        rows.sort(key=lambda r: float(r.get("mean_pass_rate", 0)), reverse=True)
        names = [r["harness"] for r in rows]
        vals = [float(r.get("mean_pass_rate", 0)) for r in rows]
        los = [float(r.get("ci_low", 0)) for r in rows]
        his = [float(r.get("ci_high", 0)) for r in rows]
        title = vert.replace("_", " ").title()
        parts.append(f'<div class="card">{svg_bar_chart(title, names, vals, los, his)}</div>')
    parts.append('</section>')
    return '\n'.join(parts)


def section_pareto(overall):
    parts = ['<section id="pareto"><h2>Pareto Fronts</h2>']
    if not overall:
        parts.append('<p class="empty">No data.</p></section>')
        return '\n'.join(parts)
    items = list(overall.values())
    parts.append('<div class="card">')
    pts_cost = [{"label": d["harness"], "x": d["cost"], "y": d["mean_pass_rate"]} for d in items]
    parts.append(svg_scatter("Correctness vs Cost", pts_cost, "Total API Cost ($)"))
    pts_time = [{"label": d["harness"], "x": d["median_time"], "y": d["mean_pass_rate"]} for d in items]
    parts.append(svg_scatter("Correctness vs Time", pts_time, "Median Time (s)"))
    parts.append('</div></section>')
    return '\n'.join(parts)


def section_heatmap(details):
    harnesses = sorted(details.keys())
    p_matrix = {}
    for ha, d in details.items():
        for hb, comp in d.get("comparisons", {}).items():
            p_matrix[(ha, hb)] = comp.get("mcnemar", {}).get("p_value", 1.0)
    parts = ['<section id="heatmap"><h2>Statistical Significance (McNemar p-values)</h2><div class="card">']
    parts.append('<p style="margin-bottom:1rem;font-size:.85rem;color:#6b7280">Green = significant difference (low p), Red = no significant difference (high p). p &lt; 0.05 suggests the difference is statistically meaningful.</p>')
    parts.append(svg_heatmap("McNemar p-values", harnesses, p_matrix))
    parts.append('</div></section>')
    return '\n'.join(parts)


def section_harness_detail(details, csvs):
    parts = ['<section id="detail"><h2>Per-Harness Detail</h2>']
    for h in sorted(details.keys()):
        d = details[h]
        parts.append(f'<div class="card"><h3>{esc(h)}</h3>')
        verts = d.get("verticals", {})
        if verts:
            # find strengths and weaknesses
            all_prs = []
            for vert, m in verts.items():
                all_prs.append((vert, m.get("mean_pass_rate", 0)))
            avg_pr = np.mean([pr for _, pr in all_prs]) if all_prs else 0
            strengths = [(v, pr) for v, pr in all_prs if pr > avg_pr]
            weaknesses = [(v, pr) for v, pr in all_prs if pr < avg_pr]
            strengths.sort(key=lambda x: -x[1])
            weaknesses.sort(key=lambda x: x[1])

            parts.append('<table><tr><th>Vertical</th><th>Pass Rate</th><th>95% CI</th><th>Median Time</th><th>Cost</th></tr>')
            for vert, m in sorted(verts.items()):
                parts.append(f'<tr><td>{esc(vert.replace("_"," ").title())}</td><td>{m["mean_pass_rate"]:.1%}</td><td>[{m["ci_low"]:.1%}, {m["ci_high"]:.1%}]</td><td>{m["median_time"]:.1f}s</td><td>${m["total_cost"]:.4f}</td></tr>')
            parts.append('</table>')

            if strengths:
                parts.append('<p style="margin-top:.75rem"><strong class="strength">Strengths:</strong> ' + ", ".join(f"{v.replace('_',' ').title()} ({pr:.0%})" for v, pr in strengths[:3]) + '</p>')
            if weaknesses:
                parts.append('<p style="margin-top:.25rem"><strong class="weakness">Weaknesses:</strong> ' + ", ".join(f"{v.replace('_',' ').title()} ({pr:.0%})" for v, pr in weaknesses[:3]) + '</p>')

            # pairwise comparisons
            comps = d.get("comparisons", {})
            if comps:
                parts.append('<table style="margin-top:.75rem"><tr><th>vs Harness</th><th>McNemar p</th><th>Cohen d (time)</th><th>Cohen d (tokens)</th></tr>')
                for hb in sorted(comps.keys()):
                    c = comps[hb]
                    mc = c.get("mcnemar", {})
                    cd = c.get("cohens_d", {})
                    p = mc.get("p_value", 1.0)
                    cls = "badge-green" if p < 0.05 else "badge-amber" if p < 0.1 else "badge-red"
                    parts.append(f'<tr><td>{esc(hb)}</td><td><span class="badge {cls}">{p:.3f}</span></td><td>{cd.get("time",0):.2f}</td><td>{cd.get("tokens",0):.2f}</td></tr>')
                parts.append('</table>')
        parts.append('</div>')
    parts.append('</section>')
    return '\n'.join(parts)


def section_exports(csvs):
    parts = ['<section id="exports"><h2>Raw Data Export</h2><div class="card">']
    for vert, rows in sorted(csvs.items()):
        if not rows:
            continue
        # rebuild CSV text
        cols = list(rows[0].keys())
        lines = [",".join(cols)]
        for r in rows:
            lines.append(",".join(str(r.get(c, "")) for c in cols))
        csv_text = "\n".join(lines)
        b64 = base64.b64encode(csv_text.encode()).decode()
        fname = f"{vert}_summary.csv"
        parts.append(f'<a href="data:text/csv;base64,{b64}" download="{fname}" class="export-link">{esc(fname)}</a>')
    parts.append('</div></section>')
    return '\n'.join(parts)


# -- Main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aggregated-dir", required=True)
    ap.add_argument("--rankings", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    csvs = read_csvs(args.aggregated_dir)
    details = read_details(args.aggregated_dir)
    try:
        rankings = json.loads(Path(args.rankings).read_text())
    except (OSError, json.JSONDecodeError):
        rankings = {}

    if not csvs:
        print("No aggregated CSVs found", file=sys.stderr)
        sys.exit(1)

    overall = compute_overall(csvs)

    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en"><head><meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>AI Coding Agent Benchmark Dashboard</title>',
        f'<style>{CSS}</style></head><body><div class="container">',
        '<h1>AI Coding Agent Benchmark Dashboard</h1>',
        '<p style="color:#6b7280;margin-bottom:1rem">Comparative evaluation of coding agent harnesses on Huawei Cloud MaaS</p>',
    ]
    html_parts.append(section_executive(overall, rankings))
    html_parts.append(section_leaderboard(rankings))
    html_parts.append(section_verticals(csvs))
    html_parts.append(section_pareto(overall))
    html_parts.append(section_heatmap(details))
    html_parts.append(section_harness_detail(details, csvs))
    html_parts.append(section_exports(csvs))
    html_parts.append('</div></body></html>')

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text('\n'.join(html_parts))
    print(f"Dashboard -> {args.output}")


if __name__ == "__main__":
    main()
