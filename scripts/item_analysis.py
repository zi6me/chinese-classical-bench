"""Item-level psychometrics on stored predictions — zero new model calls.

Every results/*.json keeps per-item headline scores, so the whole analysis is
a retroactive recompute (same spirit as scripts/rescore.py).

Produces, per task and overall:
  1. Item difficulty   — mean headline score across models (1 = everyone solves it)
  2. Item discrimination — corrected item-total correlation (does this item
     separate strong from weak models?)
  3. Dead items        — ~zero variance across models (no information; ceiling
     or floor) — candidates to drop or replace
  4. Negative-discrimination items — strong models do *worse*; usually a sign
     of an ambiguous prompt or a bad gold reference — candidates to audit
  5. Task redundancy   — Spearman correlation of the 6 task scores across the
     N models (are any two tasks measuring the same thing?)

Headline metric per task matches scripts/aggregate.py.

Usage:
  python scripts/item_analysis.py                       # writes docs/ + json
  python scripts/item_analysis.py --out docs/item-analysis.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"

HEADLINE = {
    "translate":    "chrf",
    "punctuate":    "punct_f1",
    "char-gloss":   "chrf",
    "idiom-source": "book_em",
    "fill-in":      "exact_match",
    "compress":     "efficiency",
}
TASK_ORDER = list(HEADLINE.keys())

# variance below this (on a 0-1 score) ⇒ the item gives ~no signal
DEAD_VAR = 1e-4
# |corrected item-total r| below this ⇒ effectively non-discriminating
LOW_DISC = 0.10


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def load_models() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for fp in sorted(RESULTS.glob("*.json")):
        if fp.name.startswith("_"):
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        out[d.get("model", fp.stem)] = d
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "docs" / "item-analysis.md")
    ap.add_argument("--json-out", type=Path, default=REPO / "docs" / "item-analysis.json")
    args = ap.parse_args()

    models = load_models()
    model_names = list(models)
    if not model_names:
        print("no result files")
        return

    # ---- collect per-(task, item) score vectors across models -------------
    # item_scores[task][item_id] = {model: headline_score}
    item_scores: dict[str, dict[str, dict[str, float]]] = {}
    # model_task_mean[model][task] = summary headline (for task-redundancy)
    model_task_mean: dict[str, dict[str, float]] = {m: {} for m in model_names}

    for m, d in models.items():
        for task, key in HEADLINE.items():
            tr = d.get("tasks", {}).get(task, {})
            summ = tr.get("summary", {})
            if key in summ and summ[key] is not None:
                model_task_mean[m][task] = float(summ[key])
            for it in tr.get("items", []):
                sc = it.get("scores", {})
                if key not in sc or sc[key] is None:
                    continue
                item_scores.setdefault(task, {}).setdefault(it["id"], {})[m] = float(sc[key])

    report: dict = {"models": model_names, "tasks": {}}
    md: list[str] = []
    md.append("# Item-level psychometrics")
    md.append("")
    md.append(f"Retroactive analysis over **{len(model_names)} models** "
              f"on stored predictions — no new model calls. "
              f"Headline metric per task matches `scripts/aggregate.py`.")
    md.append("")
    md.append(f"- **Difficulty** = mean headline score across models "
              f"(1.0 = every model solves it; low = hard).")
    md.append(f"- **Discrimination** = corrected item–total correlation "
              f"(item score vs. the model's mean over *all other* items). "
              f"High = separates strong/weak models; ≤0 = noise or bad gold.")
    md.append(f"- N={len(model_names)} models is small — read these as "
              f"directional, not significant. Caveat applies throughout.")
    md.append("")

    overall_disc: list[float] = []

    for task in TASK_ORDER:
        items = item_scores.get(task, {})
        if not items:
            continue
        ids = sorted(items)
        # per-model total = mean headline over this task's items
        model_tot: dict[str, float] = {}
        for m in model_names:
            vals = [items[i][m] for i in ids if m in items[i]]
            if vals:
                model_tot[m] = sum(vals) / len(vals)

        rows = []
        for i in ids:
            sm = items[i]
            vec_models = [m for m in model_names if m in sm]
            scores = [sm[m] for m in vec_models]
            n = len(scores)
            mean = sum(scores) / n
            var = sum((s - mean) ** 2 for s in scores) / n
            # corrected item-total: total excluding this item
            xs, ys = [], []
            for m in vec_models:
                others = [items[j][m] for j in ids if j != i and m in items[j]]
                if not others:
                    continue
                xs.append(sm[m])
                ys.append(sum(others) / len(others))
            disc = pearson(xs, ys)
            rows.append({"id": i, "difficulty": round(mean, 4),
                         "variance": round(var, 6),
                         "discrimination": None if disc is None else round(disc, 4)})

        diffs = [r["difficulty"] for r in rows]
        discs = [r["discrimination"] for r in rows if r["discrimination"] is not None]
        overall_disc.extend(discs)
        dead = [r for r in rows if r["variance"] < DEAD_VAR]
        ceil = [r for r in dead if r["difficulty"] >= 0.95]
        floor = [r for r in dead if r["difficulty"] <= 0.05]
        neg = sorted((r for r in rows if (r["discrimination"] or 0) < 0),
                     key=lambda r: r["discrimination"])
        low = [r for r in rows if r["discrimination"] is not None
               and abs(r["discrimination"]) < LOW_DISC]

        report["tasks"][task] = {
            "n_items": len(rows),
            "difficulty_mean": round(sum(diffs) / len(diffs), 4),
            "discrimination_mean": round(sum(discs) / len(discs), 4) if discs else None,
            "dead": len(dead), "ceiling": len(ceil), "floor": len(floor),
            "negative_disc": len(neg), "low_disc": len(low),
            "worst_negative": [r["id"] for r in neg[:8]],
            "items": rows,
        }

        md.append(f"## {task}  (metric: `{HEADLINE[task]}`, n={len(rows)} items)")
        md.append("")
        md.append(f"- mean difficulty **{sum(diffs)/len(diffs):.3f}**, "
                  f"mean discrimination **"
                  f"{(sum(discs)/len(discs)) if discs else float('nan'):.3f}**")
        md.append(f"- **dead items: {len(dead)}** "
                  f"({len(ceil)} ceiling — every model ≈solves, "
                  f"{len(floor)} floor — every model ≈fails) "
                  f"→ carry no information, drop/replace candidates")
        md.append(f"- **negative discrimination: {len(neg)}** "
                  f"(stronger models do *worse* — likely ambiguous prompt or "
                  f"bad gold; audit first)")
        md.append(f"- low |discrimination| (<{LOW_DISC}): {len(low)}")
        if neg:
            shown = ", ".join(f"`{r['id']}` ({r['discrimination']:+.2f})"
                              for r in neg[:8])
            md.append(f"- worst negative-disc items: {shown}")
        md.append("")

    if overall_disc:
        md.append("## Bench-wide")
        md.append("")
        tot = sum(len(report["tasks"][t]["items"]) for t in report["tasks"])
        dead_tot = sum(report["tasks"][t]["dead"] for t in report["tasks"])
        neg_tot = sum(report["tasks"][t]["negative_disc"] for t in report["tasks"])
        md.append(f"- {tot} items total; "
                  f"**{dead_tot} dead ({dead_tot/tot:.0%})**, "
                  f"**{neg_tot} negative-discrimination ({neg_tot/tot:.0%})**")
        md.append(f"- mean discrimination across all items: "
                  f"**{sum(overall_disc)/len(overall_disc):.3f}**")
        md.append("")

    # ---- task redundancy: Spearman over model task means ------------------
    md.append("## Task redundancy (Spearman over model task-means)")
    md.append("")
    present = [t for t in TASK_ORDER
               if sum(1 for m in model_names if t in model_task_mean[m]) >= 3]
    md.append(f"Correlation of the {len(present)} task scores across "
              f"{len(model_names)} models. High |ρ| ⇒ the two tasks rank models "
              f"the same way and one may be redundant. n={len(model_names)} — "
              f"directional only.")
    md.append("")
    md.append("- " + " / ".join(present))
    corr_mat: dict[str, dict[str, float | None]] = {}
    for a in present:
        corr_mat[a] = {}
        for b in present:
            ms = [m for m in model_names
                  if a in model_task_mean[m] and b in model_task_mean[m]]
            xs = [model_task_mean[m][a] for m in ms]
            ys = [model_task_mean[m][b] for m in ms]
            rho = 1.0 if a == b else spearman(xs, ys)
            corr_mat[a][b] = None if rho is None else round(rho, 3)
    for a in present:
        cells = " ".join(
            f"{a}~{b}={corr_mat[a][b]:+.2f}"
            for b in present if b > a and corr_mat[a][b] is not None)
        if cells:
            md.append(f"- **{a}**: {cells}")
    redundant = sorted(
        ((a, b, corr_mat[a][b]) for a in present for b in present
         if b > a and corr_mat[a][b] is not None and abs(corr_mat[a][b]) >= 0.8),
        key=lambda x: -abs(x[2]))
    md.append("")
    if redundant:
        md.append("**Possibly redundant (|ρ|≥0.8):**")
        for a, b, r in redundant:
            md.append(f"- `{a}` ↔ `{b}`  ρ={r:+.2f}")
    else:
        md.append("No task pair reaches |ρ|≥0.8 — the 6 tasks look "
                  "non-redundant (each adds ranking signal).")
    md.append("")
    report["task_corr"] = corr_mat

    args.out.write_text("\n".join(md) + "\n", encoding="utf-8")
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote → {args.out.relative_to(REPO)} , "
          f"{args.json_out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
