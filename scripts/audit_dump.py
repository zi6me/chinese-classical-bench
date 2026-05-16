"""Dump negative-discrimination items with gold + all model predictions,
so a human (or Claude) can decide: bad gold / ambiguous / metric artifact.

Reads docs/item-analysis.json for the per-item discrimination, joins the
benchmark record (data/*.jsonl) and every model's stored prediction.

Usage:
  python scripts/audit_dump.py --task fill-in
  python scripts/audit_dump.py --task idiom-source --max-disc -0.03
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK_FILES = {
    "translate": "translate.jsonl", "punctuate": "punctuate.jsonl",
    "char-gloss": "char_gloss.jsonl", "idiom-source": "idiom_source.jsonl",
    "fill-in": "fill_in.jsonl", "compress": "compress.jsonl",
}
HEADLINE = {"translate": "chrf", "punctuate": "punct_f1", "char-gloss": "chrf",
            "idiom-source": "book_em", "fill-in": "exact_match", "compress": "efficiency"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--max-disc", type=float, default=0.0,
                    help="only items with discrimination < this (default 0 = all negative)")
    args = ap.parse_args()
    task, key = args.task, HEADLINE[args.task]

    ia = json.loads((REPO / "docs" / "item-analysis.json").read_text("utf-8"))
    items = ia["tasks"][task]["items"]
    targets = sorted((r for r in items
                      if r["discrimination"] is not None and r["discrimination"] < args.max_disc),
                     key=lambda r: r["discrimination"])

    recs = {}
    with (REPO / "data" / TASK_FILES[task]).open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            recs[r["id"]] = r

    preds: dict[str, list[tuple[str, str, float]]] = {}
    for fp in sorted((REPO / "results").glob("*.json")):
        if fp.name.startswith("_"):
            continue
        d = json.loads(fp.read_text("utf-8"))
        m = d.get("model", fp.stem)
        for it in d.get("tasks", {}).get(task, {}).get("items", []):
            preds.setdefault(it["id"], []).append(
                (m, it.get("prediction", ""), it.get("scores", {}).get(key)))

    print(f"### {task}  ({len(targets)} items, disc < {args.max_disc})\n")
    for r in targets:
        iid = r["id"]
        rec = recs.get(iid, {})
        print(f"=== {iid}  disc={r['discrimination']:+.2f}  difficulty={r['difficulty']:.3f} ===")
        print(f"instruction: {rec.get('instruction','')}")
        print(f"input      : {rec.get('input','')}")
        print(f"GOLD       : {rec.get('reference','')}")
        md = rec.get("metadata", {})
        for mk in ("context", "source", "book", "book_full", "expected_quote", "explanation"):
            if md.get(mk):
                print(f"  meta.{mk}: {md[mk]}")
        for m, p, s in sorted(preds.get(iid, []), key=lambda x: -(x[2] or 0)):
            ss = f"{s:.3f}" if isinstance(s, (int, float)) else "—"
            print(f"  [{ss}] {m}: {p[:160]}")
        print()


if __name__ == "__main__":
    main()
