"""Build punctuate task: 100 断句加标点 questions stratified by source."""

import json
import random
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = (
    Path.home()
    / "Documents/zion/classical-corpus/output/instruct/punctuate.jsonl"
)
OUT = REPO / "data" / "punctuate.jsonl"

N_TARGET = 100
LEN_MIN, LEN_MAX = 30, 200  # 输入(无标点) 长度


def main() -> None:
    rng = random.Random(42)
    pool: dict[str, list[dict]] = defaultdict(list)

    print(f"loading from {SOURCE.name}...")
    with SOURCE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("_has_box"):
                continue
            in_len = len(r["input"])
            if not (LEN_MIN <= in_len <= LEN_MAX):
                continue
            pool[r.get("source", "")].append(r)

    sources = sorted(pool.keys())
    print(f"  available sources: {len(sources)}, candidates per source: "
          f"{sorted([(s, len(pool[s])) for s in sources], key=lambda x: -x[1])[:5]}...")

    # round-robin sample to ensure source diversity
    samples: list[dict] = []
    src_iters = {s: iter(rng.sample(pool[s], len(pool[s]))) for s in sources}
    while len(samples) < N_TARGET:
        any_taken = False
        for s in sources:
            if len(samples) >= N_TARGET:
                break
            try:
                samples.append(next(src_iters[s]))
                any_taken = True
            except StopIteration:
                continue
        if not any_taken:
            break
    rng.shuffle(samples)

    LEADING_NOISE = "，。：；、！？「」『』《》（）()【】 　"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, r in enumerate(samples, 1):
            ref = r["output"].lstrip(LEADING_NOISE).strip()
            inp = r["input"].strip()
            # ensure input is still a stripped-version of ref (sanity)
            if not inp or not ref:
                continue
            out = {
                "id": f"punctuate#{i}",
                "task": "punctuate",
                "instruction": "为下列古文添加标点：",
                "input": inp,
                "reference": ref,
                "metadata": {"source": r["source"], "category": r.get("category", "")},
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    by_src: dict[str, int] = defaultdict(int)
    for s in samples:
        by_src[s["source"]] += 1
    print(f"\nwrote {len(samples)} questions → {OUT.relative_to(REPO)}")
    print(f"top sources: {dict(sorted(by_src.items(), key=lambda x: -x[1])[:5])}")


if __name__ == "__main__":
    main()
