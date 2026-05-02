"""Build char-gloss task: 100 字义解释 questions.

Source: chinese-dictionary char_detail.json — concatenated JSON objects
(not array, not JSONL). Each char has pronunciations[*].explanations[*].detail
which are 古文 quotations attesting that meaning.

For each Q: pick a char + a 古文 quote where this char appears + the modern
gloss for that meaning. Model has to output the meaning that captures the
char's role in the quote.
"""

import json
import random
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = (
    Path.home()
    / "Documents/zion/reference/Chinese/classical/corpora/chinese-dictionary/character/char_detail.json"
)
OUT = REPO / "data" / "char_gloss.jsonl"

N_TARGET = 100
STOPWORDS = set("之乎者也而其以为与于焉夫且乃则若所是非有无可不")

# 现代/民国作者及题材，明确排除（保证benchmark测的是文言文）
MODERN_AUTHORS = (
    "鲁迅", "毛泽东", "周恩来", "郭沫若", "茅盾", "巴金", "老舍",
    "朱自清", "闻一多", "胡适", "梁启超", "陈独秀", "李大钊",
    "孙中山", "瞿秋白", "夏衍", "冰心", "徐志摩", "戴望舒",
    "三元里",  # 近代史话题
    "辛亥革命", "太平天国",
)


def stream_json_objects(path: Path):
    """char_detail.json is concatenated `{...}{...}{...}` — yield each."""
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        # skip whitespace
        while pos < len(text) and text[pos] in " \n\t\r,":
            pos += 1
        if pos >= len(text):
            break
        try:
            obj, end = decoder.raw_decode(text, pos)
            yield obj
            pos = end
        except json.JSONDecodeError:
            # skip a char and retry
            pos += 1


def clean_explanation(s: str) -> str:
    """Strip parenthetical asides like '(指事...)' from gloss."""
    s = re.sub(r"^\([^)]*\)。?", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> None:
    rng = random.Random(42)
    print(f"streaming {SOURCE.name}...")

    candidates = []
    for entry in stream_json_objects(SOURCE):
        char = entry.get("char", "")
        if len(char) != 1 or not ("一" <= char <= "鿿"):
            continue
        if char in STOPWORDS:
            continue
        for pron in entry.get("pronunciations", []):
            for expl in pron.get("explanations", []):
                gloss = clean_explanation(expl.get("content", ""))
                if not gloss or len(gloss) < 2 or len(gloss) > 30:
                    continue
                # find a 古文 quote that contains the char
                for d in expl.get("detail", []):
                    quote = d.get("text", "").strip()
                    book = d.get("book", "").strip()
                    if char not in quote:
                        continue
                    if not (10 <= len(quote) <= 80):
                        continue
                    if any(m in book for m in MODERN_AUTHORS):
                        continue
                    candidates.append(
                        {
                            "char": char,
                            "gloss": gloss,
                            "quote": quote,
                            "book": book,
                        }
                    )
                    break  # one quote per gloss

    print(f"  total candidates: {len(candidates):,}")
    # dedupe by (char, gloss) — keep one quote per pair
    seen = set()
    uniq = []
    for c in candidates:
        key = (c["char"], c["gloss"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    print(f"  after dedup: {len(uniq):,}")

    sampled = rng.sample(uniq, min(N_TARGET, len(uniq)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, c in enumerate(sampled, 1):
            inp = f"字：{c['char']}\n出处：{c['quote']}（{c['book']}）"
            out = {
                "id": f"char-gloss#{i}",
                "task": "char-gloss",
                "instruction": "解释下列字在引用古文中的含义，用一个简短的现代汉语短语回答。",
                "input": inp,
                "reference": c["gloss"],
                "metadata": {
                    "char": c["char"],
                    "quote": c["quote"],
                    "book": c["book"],
                },
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"\nwrote {len(sampled)} questions → {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
