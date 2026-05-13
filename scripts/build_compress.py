"""Build the `compress` task: modern Chinese → classical Chinese (compression).

Source: classical-corpus output/instruct/translate.jsonl (m2c records only).
Filter: modern 100-300 Chinese chars, ratio 0.3-0.75, diverse sources.
Output: data/compress.jsonl (100 records).
"""

import json
import random
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "compress.jsonl"
SRC = Path("/Users/zion/Documents/zion/classical-corpus/output/instruct/translate.jsonl")

CN_RANGES = [(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0x20000, 0x2A6DF), (0x2A700, 0x2EBEF)]


def cn_len(s: str) -> int:
    n = 0
    for ch in s:
        cp = ord(ch)
        for lo, hi in CN_RANGES:
            if lo <= cp <= hi:
                n += 1
                break
    return n


INSTRUCTION = "将下列现代汉语压缩成等义的文言文，力求简洁，不要解释，直接输出文言文："


def main() -> None:
    random.seed(42)

    # Pass 1: collect eligible records grouped by category
    by_cat: dict[str, list[dict]] = defaultdict(list)
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("task") != "m2c":
                continue
            if r.get("_has_box"):
                continue
            mod = r["input"]
            cls = r["output"]
            mlen = cn_len(mod)
            clen = cn_len(cls)
            if not (100 <= mlen <= 300):
                continue
            if not (30 <= clen <= mlen):
                continue
            ratio = clen / mlen
            if not (0.30 <= ratio <= 0.75):
                continue
            cat = r.get("category") or "?"
            by_cat[cat].append({
                "modern": mod,
                "classical": cls,
                "source": r.get("source", "?"),
                "category": cat,
                "ref_ratio": round(ratio, 4),
            })

    print(f"eligible by category: {[(k, len(v)) for k, v in by_cat.items()]}")

    # Pass 2: stratified sample 100 records
    # target distribution: 经 25 / 史 35 / 子 25 / 集 15 (adjust to availability)
    targets = {"经": 25, "史": 35, "子": 25, "集": 15}
    sampled: list[dict] = []
    for cat, want in targets.items():
        pool = by_cat.get(cat, [])
        if len(pool) < want:
            print(f"WARN: only {len(pool)} records in {cat}, wanted {want}")
            sampled.extend(pool)
        else:
            sampled.extend(random.sample(pool, want))

    # backfill if short of 100
    if len(sampled) < 100:
        extra_pool = []
        for cat, recs in by_cat.items():
            if cat not in targets:
                extra_pool.extend(recs)
        random.shuffle(extra_pool)
        sampled.extend(extra_pool[: 100 - len(sampled)])

    sampled = sampled[:100]
    random.shuffle(sampled)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, r in enumerate(sampled, 1):
            rec = {
                "id": f"compress#{i}",
                "task": "compress",
                "instruction": INSTRUCTION,
                "input": r["modern"],
                "reference": r["classical"],
                "metadata": {
                    "source": r["source"],
                    "category": r["category"],
                    "ref_ratio": r["ref_ratio"],
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote → {OUT.relative_to(REPO)} ({len(sampled)} records)")
    ratios = [r["ref_ratio"] for r in sampled]
    print(f"ref_ratio: min={min(ratios):.3f} mean={sum(ratios)/len(ratios):.3f} max={max(ratios):.3f}")


if __name__ == "__main__":
    main()
