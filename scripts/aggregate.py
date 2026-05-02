"""Aggregate per-model results files into a single leaderboard table.

Usage:
  python scripts/aggregate.py            # uses results/*.json
  python scripts/aggregate.py --out leaderboard.md
"""

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"

# pick one headline metric per task
HEADLINE = {
    "translate":     ("chrf",      "chrF"),
    "punctuate":     ("punct_f1",  "Punct F1"),
    "char-gloss":    ("chrf",      "chrF"),
    "idiom-source":  ("book_em",   "Book EM"),
    "fill-in":       ("exact_match", "Exact"),
}
TASK_ORDER = list(HEADLINE.keys())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=RESULTS)
    ap.add_argument("--out", type=Path, default=None,
                    help="optional markdown output path")
    args = ap.parse_args()

    files = sorted(args.results_dir.glob("*.json"))
    if not files:
        print(f"no result files in {args.results_dir}")
        return

    rows = []
    for fp in files:
        d = json.loads(fp.read_text(encoding="utf-8"))
        model = d.get("model", fp.stem)
        row = {"model": model}
        for t in TASK_ORDER:
            metric_key, _ = HEADLINE[t]
            tr = d.get("tasks", {}).get(t, {})
            summ = tr.get("summary", {})
            row[t] = summ.get(metric_key)
        # avg across tasks (skip None)
        vals = [v for v in (row[t] for t in TASK_ORDER) if v is not None]
        row["_avg"] = round(sum(vals) / len(vals), 4) if vals else None
        rows.append(row)

    rows.sort(key=lambda r: -(r["_avg"] or 0))

    # render
    headers = ["Model"] + [f"{t} ({HEADLINE[t][1]})" for t in TASK_ORDER] + ["Avg"]
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        cells = [r["model"]]
        for t in TASK_ORDER:
            v = r[t]
            cells.append(f"{v:.3f}" if v is not None else "—")
        cells.append(f"**{r['_avg']:.3f}**" if r["_avg"] is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")

    md = "\n".join(lines)
    print(md)
    if args.out:
        args.out.write_text(md + "\n", encoding="utf-8")
        print(f"\nwrote → {args.out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
