# Data Quality Audit

> Last run: 2026-05-13. Method: programmatic checks + targeted inspection.

## Summary

11 records (2.2% of 500) have known quality issues. Each is annotated in the
data file with a `metadata._audit_issue` field — contributors can filter:

```python
ds = ds.filter(lambda x: not x.get("metadata", {}).get("_audit_issue"))
```

Items are **not removed** so historical model results (`results/<model>.json`)
remain comparable. Scoring metric impact is minor (≤2 percentage points on
any single task across any model).

## By task

### translate (1/100)
- `translate#51` — input "新招四会化蒙化注化穆" (a list of place names from 南齐书·志/卷十四) is identical to reference. Models get a free chrF point by echoing input. Affects all models equally; minimal rank impact.

### punctuate (8/100) — the biggest concentration
The benchmark accidentally sampled 8 items from 校勘记 (textual commentary),
calendar/almanac tables, or chronological enumerations rather than narrative
prose. These reference texts use whitespace formatting instead of 。，、 etc.,
so punctuation-position F1 is meaningless on them.
- `punctuate#18` — input contains Western commas leaked from `<史部,正史类,后汉书>` metadata residue.
- `punctuate#6, #26, #34, #62` — references are 校勘记 (textual commentary), no narrative punctuation.
- `punctuate#22` — 历法表 (calendar/almanac tabular data).
- `punctuate#46` — enumeration of titled officials.
- `punctuate#83` — chronological list of earthquake records.

**Impact**: punct_f1 is dragged down ~5% for all models (the wrong-genre items have very low F1 regardless of the model's answer). A v2 of `punctuate` should filter source records by `category in {本纪, 列传, 子, 经}` and minimum prose density.

### char-gloss (1/100)
- `char-gloss#95` — character "制" in the quote "先王之制,大都不过参国之一" (左传·隐公元年, meaning *system/regulation*) has reference "又" which is incorrect. The gloss generator failed for this record (the `book` field is also empty). Should be `制度` or `规定`.

### idiom-source (1/100)
- `idiom-source#70` — for 妙语解颐 (《汉书·匡衡传》"匡说《诗》，解人颐"), the `metadata.expected_quote` stores the colloquial annotation "使人笑不能止也" instead of the actual source passage. This only affects the *secondary* `quote_chrf` metric; the **headline `book_em` metric is unaffected** (the book "汉书" is correct).

### fill-in (0/100)
No issues found.

## Method

Automated checks (`grep`-able, see `scripts/validate_results.py` for the result-file equivalent):
- Duplicate IDs, missing required fields (`input`, `reference`, `metadata`)
- `input == reference` (degenerate test)
- References too short for the task (excluding fill-in's single-char design)
- Punctuation in `punctuate` inputs (should be stripped) and absence in references
- Character overlap between `idiom-source` `input` and `expected_quote`
- `fill-in` reference must be a single CJK character
- Source/book distribution balance per task

Manual inspection confirmed each automatic flag before annotation.

## How to fix in v1.x

Each issue is fixable individually but doing so would invalidate the stored
predictions in `results/*.json`. Plan:

1. v1.1 of `data/*.jsonl` would **replace** flagged items with cleaner samples
   regenerated from `chinese-classical-corpus`.
2. Existing result files would need a **rerun** of the affected questions only
   (not full benchmark) to keep historical comparisons intact.
3. Once all flagged items are replaced, leaderboard numbers will likely move
   by ≤2% per task per model — directionally similar, slightly cleaner.
