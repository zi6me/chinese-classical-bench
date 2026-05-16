## Leaderboard (chrF-based, 95% CI from item bootstrap)

| Model | translate (chrF) | punctuate (Punct F1) | char-gloss (chrF) | idiom-source (Book EM) | fill-in (Exact) | compress (Compress Eff) | Avg |
|---|---|---|---|---|---|---|---|
| claude-opus-4-7 | 0.244 ±0.026 | 0.800 ±0.063 | 0.213 ±0.056 | 0.650 ±0.095 | 0.860 ±0.070 | 0.147 ±0.034 | **0.485 ±0.025** |
| claude-opus-4-7-thinking | 0.242 ±0.023 | 0.790 ±0.065 | 0.207 ±0.053 | 0.630 ±0.095 | 0.880 ±0.065 | 0.091 ±0.025 | **0.473 ±0.024** |
| claude-sonnet-4-6 | 0.231 ±0.022 | 0.785 ±0.065 | 0.157 ±0.044 | 0.560 ±0.100 | 0.700 ±0.090 | 0.163 ±0.022 | **0.432 ±0.027** |
| deepseek-3.2 | 0.240 ±0.025 | 0.745 ±0.069 | 0.139 ±0.046 | 0.740 ±0.085 | 0.550 ±0.095 | 0.163 ±0.019 | **0.429 ±0.027** |
| glm-5 | 0.241 ±0.026 | 0.799 ±0.063 | 0.176 ±0.049 | 0.740 ±0.085 | 0.450 ±0.095 | 0.153 ±0.018 | **0.427 ±0.026** |
| minimax-m2.1 | 0.216 ±0.023 | 0.709 ±0.070 | 0.173 ±0.049 | 0.660 ±0.090 | 0.630 ±0.090 | 0.094 ±0.011 | **0.414 ±0.027** |
| Qwen3.5-35B-A3B | 0.225 ±0.023 | 0.753 ±0.062 | 0.175 ±0.053 | 0.500 ±0.100 | 0.380 ±0.090 | — | **0.407 ±0.032** |
| minimax-m2.5 | 0.219 ±0.021 | 0.709 ±0.070 | 0.161 ±0.051 | 0.550 ±0.100 | 0.590 ±0.095 | 0.092 ±0.009 | **0.387 ±0.027** |
| qwen3-coder-next | 0.227 ±0.028 | 0.767 ±0.063 | 0.116 ±0.041 | 0.540 ±0.095 | 0.520 ±0.095 | 0.113 ±0.011 | **0.381 ±0.026** |
| claude-haiku-4-5-20251001 | 0.204 ±0.024 | 0.729 ±0.063 | 0.128 ±0.048 | 0.340 ±0.090 | 0.350 ±0.090 | 0.087 ±0.009 | **0.306 ±0.026** |

## Judge-rescored ranking — translate & char-gloss

Claude Opus 4.7 and Claude Sonnet 4.6 both used as judges, 0-5 ordinal rubric, normalized to 0-1. chrF rewards literal n-gram overlap and systematically under-rates synonymous paraphrase; the LLM judge sees meaning. Two-judge cross-validation substitutes for human gold labels — where Opus and Sonnet agree, the rating is trustworthy. See [`experiments/llm-judge/report.md`](experiments/llm-judge/report.md) for correlation analysis and [`experiments/llm-judge/agreement.json`](experiments/llm-judge/agreement.json) for inter-judge kappa.

| Model | translate (chrF) | translate (Opus) | translate (Sonnet) | char-gloss (chrF) | char-gloss (Opus) | char-gloss (Sonnet) |
|---|---|---|---|---|---|---|
| claude-opus-4-7-thinking | 0.242 | 0.802 | 0.770 | 0.207 | 0.736 | 0.706 |
| claude-opus-4-7 | 0.244 | 0.800 | 0.780 | 0.213 | 0.716 | 0.700 |
| claude-sonnet-4-6 | 0.231 | 0.776 | 0.756 | 0.157 | 0.694 | 0.700 |
| minimax-m2.1 | 0.216 | 0.704 | 0.708 | 0.173 | 0.695 | 0.685 |
| glm-5 | 0.241 | 0.748 | 0.750 | 0.176 | 0.638 | 0.644 |
| minimax-m2.5 | 0.219 | 0.704 | 0.688 | 0.161 | 0.654 | 0.662 |
| Qwen3.5-35B-A3B | 0.225 | 0.728 | 0.732 | 0.175 | 0.620 | 0.630 |
| qwen3-coder-next | 0.227 | 0.746 | 0.746 | 0.116 | 0.602 | 0.592 |
| deepseek-3.2 | 0.240 | 0.754 | 0.738 | 0.139 | 0.538 | 0.554 |
| claude-haiku-4-5-20251001 | 0.204 | 0.675 | 0.682 | 0.128 | 0.578 | 0.574 |

*Opus judge complete on 10/10 models, Sonnet judge complete on 10/10 models × 100 questions per task. `*` = partial (run in progress).*

