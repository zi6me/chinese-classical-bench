"""Build idiom-source task: 100 典故出处 questions.

Source: chinese-dictionary idiom.json. We only keep idioms whose `source.book`
references a classic from our 30-source corpus, so models that learned the
corpus have a fair shot.

Question format:
  input:  the idiom (e.g., "三人行必有我师")
  reference: book + chapter + quote
  metadata.book: for exact-match scoring on book name
  metadata.expected_quote: for chrF scoring on the quote
"""

import json
import random
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = (
    Path.home()
    / "Documents/zion/reference/Chinese/classical/corpora/chinese-dictionary/idiom/idiom.json"
)
OUT = REPO / "data" / "idiom_source.jsonl"

# books we have in our corpus (so model has fair access to ground truth)
KNOWN_BOOKS = {
    "论语", "孟子", "大学", "中庸", "诗经", "尚书", "礼记", "周易",
    "左传", "公羊传", "穀梁传", "孝经", "尔雅",
    "史记", "汉书", "后汉书", "三国志", "晋书", "宋书", "南齐书",
    "梁书", "陈书", "魏书", "北齐书", "周书", "南史", "北史", "隋书",
    "资治通鉴", "说文解字",
    # also common 子 集 部 books
    "庄子", "老子", "荀子", "韩非子", "孙子兵法", "墨子",
    "战国策", "国语", "吕氏春秋",
}

N_TARGET = 100


def extract_book(book_field: str) -> str | None:
    """Parse '宋·邵雍《观物外篇》' → '观物外篇' or '《论语·学而》' → '论语'."""
    if not book_field:
        return None
    # 《XX》 in the field
    m = re.search(r"《([^《》·]+?)(?:[·、].*)?》", book_field)
    if m:
        return m.group(1).strip()
    return None


def main() -> None:
    rng = random.Random(42)
    print(f"loading {SOURCE.name}...")
    data = json.load(SOURCE.open(encoding="utf-8"))
    print(f"  {len(data):,} idioms total")

    candidates: list[dict] = []
    for r in data:
        src = r.get("source")
        if not src or not src.get("text") or not src.get("book"):
            continue
        book = extract_book(src["book"])
        if not book or book not in KNOWN_BOOKS:
            continue
        # filter: idiom 4-8 chars, source quote 8-100 chars
        if not (3 <= len(r["word"]) <= 10):
            continue
        quote = src["text"].strip()
        if not (8 <= len(quote) <= 100):
            continue
        candidates.append(
            {
                "idiom": r["word"],
                "book": book,
                "book_full": src["book"],
                "quote": quote,
                "explanation": r.get("explanation", ""),
            }
        )

    print(f"  candidates with KNOWN_BOOKS source: {len(candidates):,}")
    if len(candidates) < N_TARGET:
        print(f"  ⚠ only {len(candidates)}, taking all")
        sampled = candidates
    else:
        sampled = rng.sample(candidates, N_TARGET)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, c in enumerate(sampled, 1):
            ref = f"出自《{c['book']}》：「{c['quote']}」"
            out = {
                "id": f"idiom-source#{i}",
                "task": "idiom-source",
                "instruction": "下列成语出自哪部典籍？请给出书名和原文引文。",
                "input": c["idiom"],
                "reference": ref,
                "metadata": {
                    "book": c["book"],
                    "book_full": c["book_full"],
                    "expected_quote": c["quote"],
                    "explanation": c["explanation"],
                },
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"\nwrote {len(sampled)} questions → {OUT.relative_to(REPO)}")
    from collections import Counter
    by_book = Counter(c["book"] for c in sampled)
    print(f"top 10 books:")
    for b, n in by_book.most_common(10):
        print(f"  {b}: {n}")


if __name__ == "__main__":
    main()
