"""Inter-judge agreement: Opus vs Sonnet on chinese-classical-bench.

Reads both judge caches (judge_scores.jsonl from Opus 4.7 + judge_scores_sonnet.jsonl
from Sonnet 4.6) and computes:
  - Cohen's quadratic-weighted kappa per (model, task)
  - Spearman correlation of model means across the 10 models
  - Per-item agreement: count of |opus - sonnet| <= 1 (lenient), == 0 (strict)
  - Disagreement examples (|diff| >= 3)

Writes summary to agreement.json and prints a markdown table.

Usage:
  python experiments/llm-judge/agreement.py
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPUS_CACHE = HERE / "judge_scores.jsonl"
SONNET_CACHE = HERE / "judge_scores_sonnet.jsonl"
OUT = HERE / "agreement.json"


def load_cache(path: Path) -> dict[tuple[str, str, str], int]:
    out: dict[tuple[str, str, str], int] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("judge") is None:
                continue
            out[(r["model"], r["task"], r["id"])] = r["judge"]
    return out


def quadratic_kappa(y1: list[int], y2: list[int], K: int = 6) -> float:
    """Cohen's quadratic-weighted kappa for ordinal ratings 0..K-1 (K=6 → 0..5)."""
    if not y1:
        return float("nan")
    O = [[0] * K for _ in range(K)]
    for a, b in zip(y1, y2):
        O[a][b] += 1
    n = len(y1)
    row = [sum(r) for r in O]
    col = [sum(O[i][j] for i in range(K)) for j in range(K)]
    E = [[row[i] * col[j] / n for j in range(K)] for i in range(K)]
    W = [[((i - j) ** 2) / ((K - 1) ** 2) for j in range(K)] for i in range(K)]
    num = sum(W[i][j] * O[i][j] for i in range(K) for j in range(K))
    den = sum(W[i][j] * E[i][j] for i in range(K) for j in range(K))
    return 1 - num / den if den else float("nan")


def spearman(a: list[float], b: list[float]) -> float:
    def rank(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0.0] * len(xs)
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra = rank(a)
    rb = rank(b)
    n = len(a)
    if n < 2:
        return float("nan")
    ma = sum(ra) / n
    mb = sum(rb) / n
    cov = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    va = sum((ra[i] - ma) ** 2 for i in range(n))
    vb = sum((rb[i] - mb) ** 2 for i in range(n))
    return cov / (va * vb) ** 0.5 if va and vb else float("nan")


def main() -> None:
    opus = load_cache(OPUS_CACHE)
    sonnet = load_cache(SONNET_CACHE)
    keys = set(opus) & set(sonnet)
    print(f"Opus cache: {len(opus)}  Sonnet cache: {len(sonnet)}  overlap: {len(keys)}")
    if not keys:
        return

    by_task: dict[str, list[tuple[int, int]]] = defaultdict(list)
    by_model_task: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    model_means_opus: dict[tuple[str, str], list[int]] = defaultdict(list)
    model_means_sonnet: dict[tuple[str, str], list[int]] = defaultdict(list)
    for (m, t, qid) in keys:
        o, s = opus[(m, t, qid)], sonnet[(m, t, qid)]
        by_task[t].append((o, s))
        by_model_task[(m, t)].append((o, s))
        model_means_opus[(m, t)].append(o)
        model_means_sonnet[(m, t)].append(s)

    print()
    print("## Agreement summary")
    print()
    print("| task | n | κ_quad | strict agree | lenient agree (|Δ|≤1) | mean(O−S) |")
    print("|---|---|---|---|---|---|")
    per_task: dict = {}
    for t in sorted(by_task):
        pairs = by_task[t]
        n = len(pairs)
        kappa = quadratic_kappa([a for a, _ in pairs], [b for _, b in pairs])
        strict = sum(1 for a, b in pairs if a == b) / n
        lenient = sum(1 for a, b in pairs if abs(a - b) <= 1) / n
        bias = statistics.fmean(a - b for a, b in pairs)
        per_task[t] = {"n": n, "kappa_quad": round(kappa, 4),
                       "strict_agree": round(strict, 4),
                       "lenient_agree": round(lenient, 4),
                       "bias_opus_minus_sonnet": round(bias, 4)}
        print(f"| {t} | {n} | {kappa:.3f} | {strict:.3f} | {lenient:.3f} | {bias:+.3f} |")

    print()
    print("## Model-mean Spearman (do both judges rank models the same way?)")
    print()
    print("| task | n_models | Spearman ρ |")
    print("|---|---|---|")
    per_model_corr = {}
    for t in sorted(by_task):
        models = sorted({m for (m, tt) in model_means_opus if tt == t})
        o_means = [statistics.fmean(model_means_opus[(m, t)]) for m in models]
        s_means = [statistics.fmean(model_means_sonnet[(m, t)]) for m in models]
        rho = spearman(o_means, s_means)
        per_model_corr[t] = {"n_models": len(models),
                             "spearman": round(rho, 4),
                             "per_model": {m: {"opus_mean": round(o_means[i], 3),
                                               "sonnet_mean": round(s_means[i], 3)}
                                           for i, m in enumerate(models)}}
        print(f"| {t} | {len(models)} | {rho:.3f} |")

    # disagreements (judge1 vs judge2 differ by >= 3 on 0-5 scale)
    print()
    print("## High-disagreement items (|Δ| ≥ 3)")
    high_disagree = []
    for (m, t, qid) in keys:
        o, s = opus[(m, t, qid)], sonnet[(m, t, qid)]
        if abs(o - s) >= 3:
            high_disagree.append({"model": m, "task": t, "id": qid,
                                  "opus": o, "sonnet": s, "diff": o - s})
    print(f"count: {len(high_disagree)} ({100*len(high_disagree)/max(len(keys),1):.1f}% of overlap)")
    if high_disagree:
        # show a few examples grouped by task
        for t in sorted({h["task"] for h in high_disagree}):
            ex = [h for h in high_disagree if h["task"] == t][:5]
            print(f"\n  {t}:")
            for h in ex:
                print(f"    {h['model']:30} {h['id']:18} O={h['opus']} S={h['sonnet']} Δ={h['diff']:+d}")

    summary = {
        "n_overlap": len(keys),
        "per_task": per_task,
        "model_spearman": per_model_corr,
        "high_disagreement_count": len(high_disagree),
        "high_disagreement_items": high_disagree,
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"\nwrote → {OUT.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
