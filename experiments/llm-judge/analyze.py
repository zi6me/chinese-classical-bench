"""Compute correlation + divergence between chrF and LLM-judge scores."""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
JUDGE_PATH = HERE / "judge_scores.jsonl"


def load() -> list[dict]:
    rows = []
    with JUDGE_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    denom = math.sqrt(sxx * syy)
    if denom == 0:
        return float("nan")
    return sxy / denom


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank-based Pearson (ties broken by average rank)."""
    def ranks(vals):
        sorted_idx = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(sorted_idx):
            j = i
            while j + 1 < len(sorted_idx) and vals[sorted_idx[j + 1]] == vals[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[sorted_idx[k]] = avg_rank
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def main() -> None:
    rows = load()
    print(f"loaded {len(rows)} judge rows")

    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task"]].append(r)

    # ----- Correlation per task (pooled over all models) -----
    print("\n## Correlation (chrF vs judge), pooled across models")
    for task, rs in by_task.items():
        xs = [r["chrf"] for r in rs]
        ys = [float(r["judge"]) for r in rs]
        p = pearson(xs, ys)
        sp = spearman(xs, ys)
        print(f"  {task:12s} n={len(rs):4d}  pearson={p:+.3f}  spearman={sp:+.3f}")

    # ----- Per-model means (chrf raw, judge/5) -----
    print("\n## Per (model, task) means")
    by_mt = defaultdict(list)
    for r in rows:
        by_mt[(r["model"], r["task"])].append(r)
    headers = ["model", "task", "n", "chrf_mean", "judge_mean_norm"]
    print("  " + " | ".join(f"{h:>20s}" if i == 0 else f"{h:>16s}"
                            for i, h in enumerate(headers)))
    leaderboard = defaultdict(dict)
    for (m, t), rs in sorted(by_mt.items()):
        chrf_mean = statistics.mean(r["chrf"] for r in rs)
        judge_mean = statistics.mean(r["judge"] for r in rs) / 5.0
        leaderboard[m][t] = {"chrf": chrf_mean, "judge": judge_mean, "n": len(rs)}
        print(f"  {m:>20s} | {t:>16s} | {len(rs):>16d} | "
              f"{chrf_mean:>16.4f} | {judge_mean:>16.4f}")

    # ----- Per-model correlation -----
    print("\n## Per-model correlation (chrF vs judge)")
    by_m = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_m[r["model"]][r["task"]].append(r)
    for m, by_task_rows in sorted(by_m.items()):
        for t, rs in by_task_rows.items():
            xs = [r["chrf"] for r in rs]
            ys = [float(r["judge"]) for r in rs]
            p = pearson(xs, ys)
            sp = spearman(xs, ys)
            print(f"  {m:>25s} / {t:<11s} n={len(rs):3d}  "
                  f"pearson={p:+.3f}  spearman={sp:+.3f}")

    # ----- Divergence: pool by question id, average judge across models -----
    # Per task: top-10 high-chrf-low-judge AND top-10 low-chrf-high-judge.
    for task, rs in by_task.items():
        print(f"\n## Divergence ({task}) — across all (model, question) rows")
        # normalize chrf to 0..1 and judge to 0..1
        for r in rs:
            r["_chrf_n"] = r["chrf"]  # already 0..1 ish
            r["_judge_n"] = r["judge"] / 5.0
            r["_div"] = r["_judge_n"] - r["_chrf_n"]
        # judge-much-higher-than-chrf -> chrF underrates
        underrated = sorted(rs, key=lambda r: -r["_div"])[:10]
        # judge-much-lower-than-chrf -> chrF overrates
        overrated = sorted(rs, key=lambda r: r["_div"])[:10]
        print(f"  Top 10 chrF UNDER-rates (high judge, low chrF):")
        for r in underrated:
            print(f"    [{r['model']:>22s}] {r['id']:14s} chrf={r['chrf']:.3f} judge={r['judge']}  "
                  f"pred={r['prediction'][:60]!r} ref={r['reference'][:60]!r}")
        print(f"  Top 10 chrF OVER-rates (low judge, high chrF):")
        for r in overrated:
            print(f"    [{r['model']:>22s}] {r['id']:14s} chrf={r['chrf']:.3f} judge={r['judge']}  "
                  f"pred={r['prediction'][:60]!r} ref={r['reference'][:60]!r}")

    # ----- Save summary JSON -----
    summary = {
        "n_total": len(rows),
        "tasks": {},
        "models": {},
    }
    for task, rs in by_task.items():
        xs = [r["chrf"] for r in rs]
        ys = [float(r["judge"]) for r in rs]
        summary["tasks"][task] = {
            "n": len(rs),
            "pearson": pearson(xs, ys),
            "spearman": spearman(xs, ys),
            "chrf_mean": statistics.mean(xs),
            "judge_mean_norm": statistics.mean(ys) / 5.0,
        }
    for m, td in leaderboard.items():
        summary["models"][m] = td
    out = HERE / "summary.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
