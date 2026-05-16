"""Apply metadata._audit_issue flags found by the item-level psychometrics
audit (negative-discrimination + floor analysis, 2026-05-16).

Idempotent: rewrites data/*.jsonl in place, only touching metadata._audit_issue.
Items are NOT removed — stored results stay comparable; downstream filters via
  ds.filter(lambda x: not x.get("metadata", {}).get("_audit_issue"))

Findings (all confirmed by reading gold + 10 models' stored predictions):
  - char-gloss: every item whose reference is the circular dictionary stub
    "同本义。" — placeholder for a 本义 defined elsewhere, not a usable gloss.
    These are exactly the floor items: chrF≈0 for every model regardless of
    answer quality. (~18 items; computed, not hardcoded.)
  - idiom-source#52 经邦论道 — gold 隋书; the idiom canonically originates from
    尚书·周官 "论道经邦". Multiple defensible sources → disputed gold.
  - fill-in#19 天_下民 — gold 降 (孟子 quoting 尚书); 佑 is an attested variant
    in transmitted 尚书 editions ("天佑下民"). Ambiguous cloze.
"""
from __future__ import annotations
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

CIRCULAR_GOLD = "同本义"
EXPLICIT = {
    "idiom-source#52": "disputed source: idiom canonically from 尚书·周官 "
                       "'论道经邦'; gold 隋书 is a later usage — multiple "
                       "defensible answers",
    "fill-in#19": "ambiguous cloze: gold 降 (孟子 quoting 尚书); 佑 is an "
                  "attested variant in transmitted 尚书 ('天佑下民')",
}


def patch(fname: str) -> tuple[int, int]:
    fp = DATA / fname
    recs = [json.loads(l) for l in fp.open(encoding="utf-8") if l.strip()]
    added = cleared = 0
    for r in recs:
        md = r.setdefault("metadata", {})
        want = None
        if r["task"] == "char-gloss":
            ref = re.sub(r"[，。、；：！？\s]", "", r["reference"].strip())
            if ref == CIRCULAR_GOLD:
                want = ("circular gold: reference is the dictionary stub "
                        "'同本义。' (a 本义 defined elsewhere), not a usable "
                        "gloss — every model scores ≈0 regardless of answer")
        if r["id"] in EXPLICIT:
            want = EXPLICIT[r["id"]]
        cur = md.get("_audit_issue")
        if want and cur != want:
            md["_audit_issue"] = want
            added += 1
        # do not clear pre-existing flags from the earlier 2026-05-13 audit
    fp.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
        encoding="utf-8")
    flagged = sum(1 for r in recs if r.get("metadata", {}).get("_audit_issue"))
    return added, flagged


if __name__ == "__main__":
    for f in ("char_gloss.jsonl", "idiom_source.jsonl", "fill_in.jsonl"):
        a, total = patch(f)
        print(f"{f}: +{a} new flags, {total} total flagged")
