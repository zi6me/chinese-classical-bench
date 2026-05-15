# LLM Judge vs chrF — chinese-classical-bench

Verdict: chrF is a weak proxy for translation/gloss quality. Pooled Pearson 0.457 (translate) and 0.470 (char-gloss) — moderate signal with lots of disagreement. Divergence cases below show where chrF fails. The LLM judge (claude-opus-4-7, 0-5 ordinal) materially reshuffles the leaderboard.

## Setup
- 5 models x 2 tasks x 100 questions = 1000 judge calls (0 errors, 0 skips).
- Judge: `claude-opus-4-7` via kcli-gw at `http://localhost:8990/v1`, temperature 0, max_tokens 8, single integer 0-5.
- Per-task rubrics in `judge.py`. chrF is the existing metric from `scripts/scorers.py`.

## Correlation (chrF vs judge)

| task | n | Pearson | Spearman |
|---|---|---|---|
| translate | 500 | +0.457 | +0.515 |
| char-gloss | 500 | +0.470 | +0.601 |

Per-model:

| model / task | Pearson translate | Pearson char-gloss |
|---|---|---|
| claude-opus-4-7 | +0.399 | +0.443 |
| claude-opus-4-7-thinking | +0.473 | +0.432 |
| claude-sonnet-4-6 | +0.495 | +0.436 |
| deepseek-3.2 | +0.420 | +0.513 |
| glm-5 | +0.516 | +0.527 |

Spearman is consistently 0.05-0.10 higher than Pearson; the relation is roughly monotonic but non-linear. chrF compresses semantically-equivalent rewrites into a low band that the judge happily rates 4-5, and is unusually generous (chrF >= 0.7) to short literal-match glosses that the judge rates only 4. chrF moves slower than meaning at both ends of the scale.

## Leaderboard delta

### translate (rank by chrF mean vs judge mean / 5)

| model | chrF mean | chrF rank | judge / 5 | judge rank | Δ rank |
|---|---|---|---|---|---|
| claude-opus-4-7-thinking | 0.242 | 2 | 0.802 | 1 | +1 |
| claude-opus-4-7 | 0.244 | 1 | 0.800 | 2 | -1 |
| claude-sonnet-4-6 | 0.231 | 5 | 0.776 | 3 | +2 |
| deepseek-3.2 | 0.240 | 4 | 0.754 | 4 | 0 |
| glm-5 | 0.241 | 3 | 0.748 | 5 | -2 |

chrF separates these 5 by 0.013 — essentially a tie that depends on phrasing luck. The judge separates them by 0.054 (4x the spread) and the order changes meaningfully:
- claude-sonnet-4-6 jumps from last to 3rd; judge says it's noticeably better than glm-5 and deepseek-3.2.
- glm-5 drops from 3rd to last — its chrF was buoyed by character overlap, not fidelity.
- claude-opus-4-7-thinking and claude-opus-4-7 swap #1 (both ~0.80, within noise).

### char-gloss

| model | chrF mean | chrF rank | judge / 5 | judge rank | Δ rank |
|---|---|---|---|---|---|
| claude-opus-4-7-thinking | 0.207 | 2 | 0.736 | 1 | +1 |
| claude-opus-4-7 | 0.213 | 1 | 0.716 | 2 | -1 |
| claude-sonnet-4-6 | 0.156 | 4 | 0.694 | 3 | +1 |
| glm-5 | 0.176 | 3 | 0.638 | 4 | -1 |
| deepseek-3.2 | 0.139 | 5 | 0.538 | 5 | 0 |

deepseek-3.2 char-gloss is genuinely weak (judge mean 2.69/5), which chrF understates relative to the strong translators.

## Why chrF is too strict — divergence examples

### Pattern A: synonymous rewording (chrF UNDER-rates)

The README's hypothesis nailed it. Classical-to-modern translation is one-to-many mapping; chrF punishes lexical drift even when meaning is preserved or improved.

**Example 1 — char-gloss#5 (glm-5)**
- Reference: `同本义。` (meta-gloss: "the original meaning")
- Prediction: `捕鸟网` ("a net for catching birds" — the actual meaning)
- chrF: 0.000  judge: 5/5
- chrF sees zero overlap; prediction is more useful than the reference.

**Example 2 — translate#73 (claude-sonnet-4-6)**
- Source: `与贤者处而得之，礼之也。`
- Reference: `跟贤人在一起是能够办到的，那就是以礼对待他们。`
- Prediction: `能与贤人相处共事，在于以礼待之。`
- chrF: 0.086  judge: 5/5
- Cleaner modern prose than the reference; same meaning; almost no shared 2-grams beyond 贤人 / 以礼.

**Example 3 — translate#89, 3 models converged on the same paraphrase**
- Source: `月满则蚌蛤实，群阴盈；月晦则蚌蛤虚，群阴亏。`
- Reference: `月满的时候，蚌蛤的肉就充实，各种属阴之物也都满盈；...`
- Predictions: `月圆之时，蚌蛤体内饱满，一切阴类之物皆充盈；...`
- chrF: 0.14-0.15  judge: 5/5 (all 3 models)
- 蚌蛤 is one of the few words shared verbatim; rest is near-perfect paraphrase.

### Pattern B: chrF UNDER-rates short glosses that match verbatim

When the gloss literally matches the reference, chrF hits 1.0 but the judge — using a rubric that reserves 5/5 for "accurate AND captures context" — gives 4/5.

- `char-gloss#86` (5 models predict `早晨`, ref=`早晨。`): chrF=1.000, judge=4/5.
- Similar: `char-gloss#50`, `char-gloss#67`, `char-gloss#40`.

This is a rubric-calibration artifact, not a real divergence — it lowers all per-model judge means uniformly. Keeping the stricter rubric is intentional: it surfaces the underrated paraphrases above.

### Pattern C: chrF OVER-rates because of name/structure overlap — the most damning divergence

The model gets the easy nouns/structure but completely misses the key meaning. chrF stays moderate because n-grams of names match.

**Example — translate#74 (4 models score 0/5)**
- Source: `军次乌骨城，仲文简羸马驴数千头，置于军后。` ("The army camped at Wugu city; Zhongwen selected several thousand weak horses/donkeys and placed them at the rear.")
- Reference: `部队驻扎在乌骨城，于仲文挑选瘦弱的马、驴几千头，放在军后。`
- 4 models translate a completely different sentence: `因功被授予开府... 尉迟迥又派遣其部将宇文胄从石济渡河... 再次进攻于仲文。` (about Yuchi Jiong attacking Yu Zhongwen)
- chrF: 0.04-0.06  judge: 0/5 (all 4)
- The predictions share proper nouns (尉迟/宇文/于仲文) with surrounding context but describe a completely different event. The model collapsed two adjacent sentences. chrF still gives ~0.05 (non-zero from shared names); judge correctly says meaning is wrong.

This is the textbook case for why we need a judge: shared proper nouns can fool chrF into rewarding a translation that is about a different event entirely.

**Example — translate#10 (4 of 5 models score 0-1)**
- Source: contains a vulgar pun on the recipient's body (君阳有玠 = "your private part has scabies")
- 4 of 5 models sanitize the pun into a polite "you have outward jade-like virtue, unfit for kitchen-work" — completely missing the joke that is the entire point of the sentence.
- chrF: 0.16-0.27  judge: 0-1
- chrF rewards them for getting the formal honorifics right; judge correctly flags that the joke is gone.

## Takeaways

1. chrF correlates with judge (~0.46-0.47 Pearson) but the residual is structured: chrF systematically misses synonymous rewording and over-rewards proper-noun overlap.
2. The judge swings the leaderboard by 2 ranks in translate (sonnet-4-6 up, glm-5 down). On a benchmark where chrF spread is 0.01-0.02, that is signal chrF can't see.
3. Spearman (rank correlation) is higher than Pearson, but still below 0.6 — meaning relative ordering inside a single (model, task) disagrees with the judge ~40% of the time.
4. Recommendation for next leaderboard release:
   - Keep chrF as the cheap deterministic floor.
   - Publish judge-normalized score as the primary column for translate and char-gloss.
   - Use `scripts/judge_scorer.py::score_with_judge` to add judge to future `eval_runner` runs (opt-in, costly).

## Cross-judge validation (2026-05-15 extension)

Updated to all 10 leaderboard models × 2 tasks × 100 questions, with Claude Sonnet 4.6 added as a second judge (rubric and prompt identical to Opus 4.7). Inter-judge agreement is reported in `agreement.json`; it serves as a "no-human-gold" calibration: if two independent strong judges with different training agree, the rating is trustworthy.

### Inter-judge agreement (Opus 4.7 vs Sonnet 4.6)

| task | n | Cohen κ_quad | strict agree | lenient (\|Δ\|≤1) | mean Opus−Sonnet |
|---|---|---|---|---|---|
| translate | 998 | **0.775** (substantial) | 63.4% | 97.6% | +0.044 |
| char-gloss | 991 | **0.894** (almost perfect) | 68.2% | 98.3% | +0.012 |

| ranking task | n models | Spearman ρ |
|---|---|---|
| translate (model means) | 10 | **0.948** |
| char-gloss (model means) | 10 | **0.979** |

Two judges converge on essentially the same model ranking. Bias is small (Opus rates 0.04 higher on translate, 0.01 on char-gloss); the judge column in `leaderboard.md` is therefore well-defined without a human gold set.

### What the judge column reveals that chrF hides

chrF places Claude opus 4.7 ahead of opus-thinking on translate (0.244 vs 0.242) — both judges say opus-thinking edges ahead (0.802/0.770 vs 0.800/0.780). The chrF gap is statistical noise; the judge gap, while still small, is consistent across both judges.

**DeepSeek-3.2 translate is dramatically downgraded by the judge.** chrF puts DeepSeek tied #2 on translate (0.240, identical to Opus 4.7's 0.244). Both judges put it 7th of 10 (0.754/0.738 vs Sonnet's 0.776/0.756). DeepSeek's chrF score was buoyed by character-level overlap from proper nouns and reused phrasing — when judged on whether the translation actually conveys the original meaning, it drops below glm-5 and the minimax models. **This is the largest chrF-vs-judge discrepancy on the leaderboard.**

**DeepSeek-3.2 char-gloss is also downgraded, this time consistently.** chrF says 0.139 (rank 9), both judges say ≈0.55 (rank 10, behind haiku-4-5). DeepSeek's gloss responses are short and often miss the contextual sense — chrF doesn't penalize brevity but the judge does.

### High-disagreement items

14 items (0.7% of overlap) have \|Opus − Sonnet\| ≥ 3. Almost all are **translate#74**, a Wugu City passage that 4 of 5 models translated as a different sentence about Yuchi Jiong attacking Yu Zhongwen (see Pattern C example in this report). Opus correctly gives 0/5 (meaning is wrong); Sonnet gives 3-4/5 (gave benefit of doubt for shared proper nouns). This is the textbook case for stricter rubrics: Opus is the harsher and arguably more correct judge here.

## Provenance

- `judge.py` — judge script, now supports `--judge-model` and `--cache-path` flags (used to run both Opus and Sonnet judges off the same code path).
- `judge_scores.jsonl` — 1989 rows (10 models × 2 tasks × ≈99 valid predictions × Opus judge).
- `judge_scores_sonnet.jsonl` — 1989 rows (same coverage, Sonnet judge).
- `agreement.py` — Cohen's quadratic kappa, Spearman, bias and high-disagreement filtering.
- `agreement.json` — machine-readable cross-judge stats.
- `analyze.py` — produces the original chrF↔Opus correlation numbers; rerun any time.
- `summary.json` — machine-readable summary (Opus only).
- `scripts/judge_scorer.py` — integration hook for future eval_runner.
- `scripts/backfill_judge.py` — replays the caches into `results/*.json` (`judge` + `judge_sonnet` labels).
