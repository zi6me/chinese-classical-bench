"""Aggregate per-model results files into the leaderboard.

Reads results/*.json (per-item predictions + scores) and results/_bootstrap.json
(precomputed 95% CIs) and renders the leaderboard with ±CI per column.

Usage:
  python scripts/aggregate.py                  # print to stdout
  python scripts/aggregate.py --out leaderboard.md
"""

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
BOOTSTRAP = RESULTS / "_bootstrap.json"

HEADLINE = {
    "translate":     ("chrf",        "chrF"),
    "punctuate":     ("punct_f1",    "Punct F1"),
    "char-gloss":    ("chrf",        "chrF"),
    "idiom-source":  ("book_em",     "Book EM"),
    "fill-in":       ("exact_match", "Exact"),
    "compress":      ("efficiency",  "Compress Eff"),
}
TASK_ORDER = list(HEADLINE.keys())


def load_bootstrap() -> dict:
    if not BOOTSTRAP.exists():
        return {}
    return json.loads(BOOTSTRAP.read_text(encoding="utf-8")).get("models", {})


def fmt_with_ci(mean, ci) -> str:
    if mean is None:
        return "—"
    if ci and ci.get("half_width") is not None:
        return f"{mean:.3f} ±{ci['half_width']:.3f}"
    return f"{mean:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=RESULTS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    files = sorted(args.results_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]
    if not files:
        print(f"no result files in {args.results_dir}")
        return

    bootstrap = load_bootstrap()

    rows = []
    for fp in files:
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warning: skipping {fp.name} (invalid JSON: {e})")
            continue
        model = d.get("model", fp.stem)
        row: dict = {"model": model}
        boot = bootstrap.get(model, {})
        for t in TASK_ORDER:
            metric_key, _ = HEADLINE[t]
            tr = d.get("tasks", {}).get(t, {})
            summ = tr.get("summary", {})
            row[t] = summ.get(metric_key)
            row[f"{t}_ci"] = boot.get(t)
        row["_avg"] = (boot.get("_avg") or {}).get("mean")
        if row["_avg"] is None:
            vals = [row[t] for t in TASK_ORDER if row[t] is not None]
            row["_avg"] = round(sum(vals) / len(vals), 4) if vals else None
        row["_avg_ci"] = boot.get("_avg")
        rows.append(row)

    rows.sort(key=lambda r: -(r["_avg"] or 0))

    headers = ["Model"] + [f"{t} ({HEADLINE[t][1]})" for t in TASK_ORDER] + ["Avg"]
    lines = []
    lines.append("## Leaderboard (chrF-based, 95% CI from item bootstrap)")
    lines.append("")
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        cells = [r["model"]]
        for t in TASK_ORDER:
            cells.append(fmt_with_ci(r[t], r[f"{t}_ci"]))
        avg_str = fmt_with_ci(r["_avg"], r["_avg_ci"])
        cells.append(f"**{avg_str}**" if r["_avg"] is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")

    md = "\n".join(lines)
    print(md)
    if args.out:
        out_path = args.out if args.out.is_absolute() else (Path.cwd() / args.out)
        out_path.write_text(md + "\n", encoding="utf-8")
        try:
            shown = out_path.relative_to(REPO)
        except ValueError:
            shown = out_path
        print(f"\nwrote → {shown}")


if __name__ == "__main__":
    main()
