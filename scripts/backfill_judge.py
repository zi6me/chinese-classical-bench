"""Backfill judge scores from experiments/llm-judge/judge_scores*.jsonl
into results/<model>.json at items[].scores.{judge,judge_norm}, and recompute
the per-task summary to include judge_mean.

Usage:
  python scripts/backfill_judge.py
  python scripts/backfill_judge.py --cache experiments/llm-judge/judge_scores.jsonl
  python scripts/backfill_judge.py --label judge_sonnet --cache .../judge_scores_sonnet.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
DEFAULT_CACHE = REPO / "experiments" / "llm-judge" / "judge_scores.jsonl"


def load_cache(path: Path) -> dict[tuple[str, str, str], dict]:
    """Last entry per (model, task, id) wins."""
    cache: dict[tuple[str, str, str], dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("judge") is None:
                continue
            cache[(rec["model"], rec["task"], rec["id"])] = rec
    return cache


def backfill(label: str, cache: dict, dry_run: bool = False) -> None:
    norm_label = f"{label}_norm"
    files = sorted(RESULTS.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]

    for fp in files:
        doc = json.loads(fp.read_text(encoding="utf-8"))
        model = doc.get("model", fp.stem)
        changed = False
        for task, tdata in doc.get("tasks", {}).items():
            judges: list[float] = []
            for it in tdata.get("items", []):
                key = (model, task, it["id"])
                rec = cache.get(key)
                if not rec:
                    continue
                j = rec["judge"]
                jn = j / 5.0
                it.setdefault("scores", {})
                if it["scores"].get(label) != j or it["scores"].get(norm_label) != jn:
                    changed = True
                it["scores"][label] = j
                it["scores"][norm_label] = jn
                judges.append(jn)
            if judges:
                summ = tdata.setdefault("summary", {})
                new_mean = round(statistics.fmean(judges), 4)
                if summ.get(norm_label) != new_mean:
                    summ[norm_label] = new_mean
                    summ[f"{label}_n"] = len(judges)
                    changed = True
        if changed:
            if not dry_run:
                fp.write_text(
                    json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            print(f"{fp.name}: updated ({label})")
        else:
            print(f"{fp.name}: no change for {label}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--label", default="judge",
                    help="score key written to items[].scores (e.g. judge, judge_sonnet)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.cache.exists():
        raise SystemExit(f"cache not found: {args.cache}")

    cache = load_cache(args.cache)
    try:
        shown = args.cache.resolve().relative_to(REPO)
    except ValueError:
        shown = args.cache
    print(f"loaded {len(cache)} judge records from {shown}")
    backfill(args.label, cache, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
