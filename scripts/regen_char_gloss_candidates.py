"""Stage replacement *candidates* for the 18 circular-gold char-gloss items.

NOT an in-place fix. The original modern-gloss dictionary
(chinese-dictionary char_detail.json) is gone, so a faithful modern gloss
cannot be reconstructed deterministically. We do the most honest thing
possible without spending money:

  - For each flagged item whose target char exists in 说文解字
    (corpus/output/shuowen.json), extract Xu Shen's definitional head
    (the "<gloss>也" clause before 从/聲/凡/《) and t2s-normalize it. This is
    a *mechanical first-pass candidate*, NOT verified gold — 说文 gives the
    本义 in terse Classical, which is close to but not identical to the
    modern phrase the task expects.
  - Items whose char is not in 说文 are marked blocked (no deterministic
    source).

Output: data/char_gloss.candidates.jsonl — every record carries
`_status` (candidate | blocked), `_provenance`, and `_needs`. Adoption
requires human/judge review AND a scoped model rerun (cost), because
replacing items invalidates the stored predictions in results/*.json.
Tracked in docs/quality-audit.md.

Usage:  python scripts/regen_char_gloss_candidates.py
"""
from __future__ import annotations
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SHUOWEN = Path.home() / "Documents/zion/classical-corpus/output/shuowen.json"
OUT = REPO / "data" / "char_gloss.candidates.jsonl"

try:
    from opencc import OpenCC
    _t2s = OpenCC("t2s").convert
except Exception:
    def _t2s(s: str) -> str:
        return s

# 说文 definitional head: take text up to the first structural marker.
_CUT = re.compile(r"[，。]?\s*(?:从|從|凡|《|讀若|读若|聲|声|象)")


def shuowen_gloss(content: str) -> str | None:
    """First definitional clause, e.g. '窮也。从穴弓聲。' -> '穷'."""
    if not content:
        return None
    head = _CUT.split(content, 1)[0].strip()
    head = re.sub(r"[，。、；：！？\s]+$", "", head)
    head = re.sub(r"也$", "", head)            # '窮也' -> '窮'
    head = _t2s(head).strip("，。、；：！？ ")
    return head or None


def main() -> None:
    sw = {}
    for e in json.loads(SHUOWEN.read_text(encoding="utf-8")):
        sw.setdefault(e["char"], e["content"])

    recs = [json.loads(l) for l in
            (REPO / "data" / "char_gloss.jsonl").open(encoding="utf-8")
            if l.strip()]
    flagged = [r for r in recs
               if r.get("metadata", {}).get("_audit_issue")
               and r["metadata"]["_audit_issue"].startswith("circular gold")]

    out, n_cand, n_block = [], 0, 0
    for r in flagged:
        ch = r["metadata"].get("char", "")
        cand = shuowen_gloss(sw.get(ch, "")) if ch in sw else None
        rec = {
            "id": r["id"], "task": "char-gloss",
            "instruction": r["instruction"], "input": r["input"],
            "metadata": {k: v for k, v in r["metadata"].items()
                         if k != "_audit_issue"},
        }
        if cand and len(cand) <= 8:
            rec["reference"] = cand
            rec["_status"] = "candidate"
            rec["_provenance"] = f"说文解字「{ch}」: {sw[ch][:40]}"
            rec["_needs"] = "human/judge review + scoped rerun before adoption"
            n_cand += 1
        else:
            rec["reference"] = r["reference"]
            rec["_status"] = "blocked"
            rec["_provenance"] = (f"char {ch!r} not in 说文 / no clean head"
                                  if ch else "no target char")
            rec["_needs"] = "manual gloss from a modern Classical dictionary"
            n_block += 1
        out.append(rec)

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                            for r in out), encoding="utf-8")
    print(f"{len(out)} flagged items → {n_cand} candidates, "
          f"{n_block} blocked  →  {OUT.relative_to(REPO)}")
    for r in out:
        tag = "CAND" if r["_status"] == "candidate" else "BLOCK"
        print(f"  [{tag}] {r['id']} 字{r['metadata'].get('char','?')} "
              f"→ {r['reference']!r}")


if __name__ == "__main__":
    main()
