"""Aggregate per-model results files into the leaderboard.

Reads results/*.json (per-item predictions + scores) and results/_bootstrap.json
(precomputed 95% CIs) and renders:
  1. Headline leaderboard — chrF / Punct F1 / Book EM / etc. with ±CI
  2. Judge-rescored ranking for translate + char-gloss (Claude Opus 4.7 judge)

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

# headline metric per task
HEADLINE = {
    "translate":     ("chrf",        "chrF"),
    "punctuate":     ("punct_f1",    "Punct F1"),
    "char-gloss":    ("chrf",        "chrF"),
    "idiom-source":  ("book_em",     "Book EM"),
    "fill-in":       ("exact_match", "Exact"),
    "compress":      ("efficiency",  "Compress Eff"),
}
TASK_ORDER = list(HEADLINE.keys())
JUDGE_TASKS = ["translate", "char-gloss"]  # tasks where LLM judge applies


def load_bootstrap() -> dict:
    if not BOOTSTRAP.exists():
        return {}
    return json.loads(BOOTSTRAP.read_text(encoding="utf-8")).get("models", {})


def fmt_with_ci(mean: float | None, ci: dict | None) -> str:
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
            # judge fields (only present after backfill_judge.py)
            row[f"{t}_judge"] = summ.get("judge_norm")
            row[f"{t}_judge_n"] = summ.get("judge_n")
            row[f"{t}_judge_sonnet"] = summ.get("judge_sonnet_norm")
            row[f"{t}_judge_sonnet_n"] = summ.get("judge_sonnet_n")
        row["_avg"] = (boot.get("_avg") or {}).get("mean")
        if row["_avg"] is None:
            # fallback to local mean if bootstrap missing
            vals = [row[t] for t in TASK_ORDER if row[t] is not None]
            row["_avg"] = round(sum(vals) / len(vals), 4) if vals else None
        row["_avg_ci"] = boot.get("_avg")
        rows.append(row)

    rows.sort(key=lambda r: -(r["_avg"] or 0))

    lines: list[str] = []

    # ----- Headline leaderboard (chrF for translate/char-gloss) -----
    lines.append("## Leaderboard (chrF-based, 95% CI from item bootstrap)")
    lines.append("")
    headers = ["Model"] + [f"{t} ({HEADLINE[t][1]})" for t in TASK_ORDER] + ["Avg"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        cells = [r["model"]]
        for t in TASK_ORDER:
            cells.append(fmt_with_ci(r[t], r[f"{t}_ci"]))
        avg_str = fmt_with_ci(r["_avg"], r["_avg_ci"])
        cells.append(f"**{avg_str}**" if r["_avg"] is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # ----- Judge-rescored ranking for translate + char-gloss -----
    judge_rows = [r for r in rows if any(r.get(f"{t}_judge") is not None for t in JUDGE_TASKS)]
    if judge_rows:
        lines.append("## Judge-rescored ranking — translate & char-gloss")
        lines.append("")
        lines.append("Claude Opus 4.7 and Claude Sonnet 4.6 both used as judges, 0-5 ordinal "
                     "rubric, normalized to 0-1. chrF rewards literal n-gram overlap and "
                     "systematically under-rates synonymous paraphrase; the LLM judge sees "
                     "meaning. Two-judge cross-validation substitutes for human gold labels — "
                     "where Opus and Sonnet agree, the rating is trustworthy. "
                     "See [`experiments/llm-judge/report.md`](experiments/llm-judge/report.md) "
                     "for correlation analysis and "
                     "[`experiments/llm-judge/agreement.json`](experiments/llm-judge/agreement.json) "
                     "for inter-judge kappa.")
        lines.append("")
        judge_headers = ["Model",
                         "translate (chrF)", "translate (Opus)", "translate (Sonnet)",
                         "char-gloss (chrF)", "char-gloss (Opus)", "char-gloss (Sonnet)"]
        lines.append("| " + " | ".join(judge_headers) + " |")
        lines.append("|" + "|".join(["---"] * len(judge_headers)) + "|")

        # sort by mean Opus judge across two tasks (only count complete tasks);
        # partial rows (n<100) sink to bottom for ranking purposes
        def judge_avg(r: dict) -> float:
            js = [r[f"{t}_judge"] for t in JUDGE_TASKS
                  if r.get(f"{t}_judge") is not None
                  and (r.get(f"{t}_judge_n") or 0) >= 90]
            return sum(js) / len(js) if js else -1.0
        judge_rows.sort(key=lambda r: -judge_avg(r))

        for r in judge_rows:
            cells = [r["model"]]
            for t in JUDGE_TASKS:
                chrf = r[t]
                cells.append(f"{chrf:.3f}" if chrf is not None else "—")
                jo = r.get(f"{t}_judge")
                jon = r.get(f"{t}_judge_n") or 0
                if jo is not None and jon >= 90:
                    cells.append(f"{jo:.3f}")
                elif jo is not None:
                    cells.append(f"{jo:.3f}*")
                else:
                    cells.append("—")
                js_ = r.get(f"{t}_judge_sonnet")
                jsn = r.get(f"{t}_judge_sonnet_n") or 0
                if js_ is not None and jsn >= 90:
                    cells.append(f"{js_:.3f}")
                elif js_ is not None:
                    cells.append(f"{js_:.3f}*")  # partial
                else:
                    cells.append("—")
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
        n_opus = sum(1 for r in judge_rows
                     if all((r.get(f"{t}_judge_n") or 0) >= 90 for t in JUDGE_TASKS))
        n_sonnet = sum(1 for r in judge_rows
                       if all((r.get(f"{t}_judge_sonnet_n") or 0) >= 90 for t in JUDGE_TASKS))
        lines.append(f"*Opus judge complete on {n_opus}/{len(rows)} models, "
                     f"Sonnet judge complete on {n_sonnet}/{len(rows)} models "
                     f"× 100 questions per task. `*` = partial (run in progress).*")
        lines.append("")

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
