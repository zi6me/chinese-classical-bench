"""Build fill-in task: 100 字词填空 from canonical 经 sentences.

Strategy: pull short famous sentences from 论语/孟子/大学/中庸 (the corpus
records are short and well-known). Mask one high-information character.

Avoid masking:
  - 虚词 (之/也/乎/者/焉/而/其/以/为/与/于/于是/...)
  - 数字 / 标点
  - First or last char of input
  - Repeated chars in same sentence (ambiguous answer)

Prefer masking:
  - 实词 (verbs, nouns, adjectives)
  - chars unique within the sentence (deterministic answer)
"""

import json
import random
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = Path.home() / "Documents/zion/classical-corpus/output/corpus.jsonl"
OUT = REPO / "data" / "fill_in.jsonl"

N_TARGET = 100

# 虚词 + 不该被 mask 的高频字
STOPWORDS = set("之乎者也而其以为与于焉夫且乃则若所是非有无可不")
PUNCT = set("，。：；、！？「」『』《》（）()【】 　“”‘’\n")


def good_sentences(text: str) -> list[str]:
    """Split a long passage into clean classical sentences, 8-25 chars."""
    parts = re.split(r"[。！？]", text)
    out = []
    for p in parts:
        p = p.strip()
        # remove brackets / parentheses content
        p = re.sub(r"[【].*?[】]", "", p)
        p = re.sub(r"[（(].*?[)）]", "", p)
        p = p.replace("　", "").strip()
        # collapse whitespace + commas
        p = re.sub(r"\s+", "", p)
        # length filter
        # count only Chinese chars
        cn_chars = [c for c in p if "一" <= c <= "鿿"]
        if 8 <= len(cn_chars) <= 25:
            out.append(p)
    return out


def pick_mask_position(sentence: str) -> int | None:
    """Pick a 1-char position to mask. Returns -1 if no good candidate."""
    chars = list(sentence)
    n = len(chars)
    candidates = []
    for i, c in enumerate(chars):
        if i == 0 or i == n - 1:
            continue
        if not ("一" <= c <= "鿿"):
            continue
        if c in STOPWORDS or c in PUNCT:
            continue
        # avoid masking chars that repeat in this sentence (ambiguous answer)
        if sentence.count(c) > 1:
            continue
        candidates.append(i)
    return candidates[len(candidates) // 2] if candidates else None


def main() -> None:
    rng = random.Random(42)
    # focus on 经 sources for high signal-to-noise
    PREFERRED_SOURCES = {"论语", "孟子", "大学", "中庸", "周易",
                          "诗经", "尚书", "礼记", "孝经", "尔雅"}

    print(f"loading corpus from {CORPUS.name}...")
    candidates: list[dict] = []
    with CORPUS.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("source") not in PREFERRED_SOURCES:
                continue
            for sent in good_sentences(r.get("content", "")):
                pos = pick_mask_position(sent)
                if pos is None:
                    continue
                candidates.append(
                    {
                        "sentence": sent,
                        "position": pos,
                        "answer": sent[pos],
                        "source": r["source"],
                        "chapter": r.get("chapter", ""),
                    }
                )

    print(f"  candidates: {len(candidates):,}")
    sampled = rng.sample(candidates, min(N_TARGET, len(candidates)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, c in enumerate(sampled, 1):
            sent = c["sentence"]
            pos = c["position"]
            masked = sent[:pos] + "___" + sent[pos + 1 :]
            out = {
                "id": f"fill-in#{i}",
                "task": "fill-in",
                "instruction": "下面这句古文中 ___ 处应填什么字？只需回答一个字。",
                "input": masked,
                "reference": c["answer"],
                "metadata": {
                    "source": f"{c['source']}·{c['chapter']}".strip("·"),
                    "context": sent,
                },
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"\nwrote {len(sampled)} questions → {OUT.relative_to(REPO)}")
    from collections import Counter
    print(f"top sources: {dict(Counter(s['source'] for s in sampled).most_common(5))}")


if __name__ == "__main__":
    main()
