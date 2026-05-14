# LLM-as-Judge Experiment

Compare chrF (current metric for `translate` and `char-gloss`) against an
LLM judge (claude-opus-4-7) to test the README's "chrF over-penalizes
synonymous rewording" hypothesis.

## Files

- `judge.py` — Calls claude-opus-4-7 via kcli-gw to score every (model, task,
  question) tuple on a 0-5 scale. Caches in `judge_scores.jsonl`.
- `analyze.py` — Computes per-task Pearson/Spearman correlation between chrF
  and judge scores, per-(model, task) means, and top-N divergence rows.
- `judge_scores.jsonl` — Append-only cache. Schema:
  `{model, task, id, chrf, judge, judge_raw, prediction, reference, input}`
- `summary.json` — Machine-readable analyze.py output.
- `report.md` — Human-readable findings: correlations, leaderboard delta,
  divergence examples.

## How to reproduce

```bash
cd /Users/zion/Documents/zion/chinese-classical-bench

# Smoke test (4 calls)
python3 experiments/llm-judge/judge.py --limit 2 --models claude-opus-4-7

# Full run (1000 calls, ~60-100 min at concurrency 2)
python3 experiments/llm-judge/judge.py --concurrency 2

# Analyze
python3 experiments/llm-judge/analyze.py
```

## Design choices

- **Judge model**: claude-opus-4-7 only — best Chinese understanding, single
  judge eliminates inter-judge variance. Reasonable for a baseline; multi-judge
  ensemble can be future work.
- **0-5 ordinal scale**: matches what humans typically produce; coarser than
  Likert-7 to keep judge decisions tractable.
- **Different rubrics per task**: translate rubric weighs fidelity + fluency;
  char-gloss rubric focuses on semantic accuracy of the single-character
  meaning.
- **Lenient parsing**: regex `[0-5]` over the response — claude almost always
  emits a clean integer but the parser tolerates accidental wrapping.
- **Concurrency 2**: gateway is shared with other agents; respect the cap.
- **Cache by (model, task, id)**: re-runs only call API for missing rows.

## Integration

Use `scripts/judge_scorer.py::score_with_judge(pred, rec, task)` if you want
to add a judge column to a future eval run. It's a thin wrapper that returns
`{judge, judge_norm}`. Not wired into `eval_runner.py` automatically because
of cost — opt in explicitly.
