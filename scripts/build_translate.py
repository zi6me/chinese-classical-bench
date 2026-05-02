"""Build translate task: 100 古译今 questions stratified by category.

Source: chinese-classical-corpus translate.jsonl (c2m records).
Output: data/translate.jsonl
"""

import json
import random
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = (
    Path.home()
    / "Documents/zion/classical-corpus/output/instruct/translate.jsonl"
)
OUT = REPO / "data" / "translate.jsonl"

N_PER_CATEGORY = 25  # 25 × 4 = 100
CATEGORIES = ("经", "史", "子", "集")
LEN_MIN, LEN_MAX = 10, 60


def main() -> None:
    rng = random.Random(42)
    pool: dict[str, list[dict]] = defaultdict(list)

    print(f"loading c2m records from {SOURCE.name}...")
    with SOURCE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("task") != "c2m":
                continue
            if r.get("_has_box"):
                continue  # exclude □-flagged records
            src_len = len(r["input"])
            if not (LEN_MIN <= src_len <= LEN_MAX):
                continue
            cat = r.get("category", "")
            if cat not in CATEGORIES:
                continue
            pool[cat].append(r)

    print(f"  pool sizes: {[(c, len(pool[c])) for c in CATEGORIES]}")

    samples: list[dict] = []
    for cat in CATEGORIES:
        items = pool.get(cat, [])
        if len(items) < N_PER_CATEGORY:
            print(f"  ⚠ {cat}: only {len(items)} candidates, taking all")
            picked = items
        else:
            picked = rng.sample(items, N_PER_CATEGORY)
        samples.extend(picked)
    rng.shuffle(samples)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, r in enumerate(samples, 1):
            out = {
                "id": f"translate#{i}",
                "task": "translate",
                "instruction": "将下列古文翻译成现代汉语：",
                "input": r["input"],
                "reference": r["output"],
                "metadata": {"source": r["source"], "category": r["category"]},
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"\nwrote {len(samples)} questions → {OUT.relative_to(REPO)}")
    print(f"breakdown: {dict((c, sum(1 for s in samples if s['category']==c)) for c in CATEGORIES)}")


if __name__ == "__main__":
    main()
