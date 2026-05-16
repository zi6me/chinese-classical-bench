# Findings: what a psychometric audit revealed about this benchmark

*2026-05-16. 10 models, 6 tasks × 100 questions, all analysis retroactive over
stored predictions (zero new model calls). Numbers from
[`item-analysis.md`](item-analysis.md), [`quality-audit.md`](quality-audit.md),
and [`../leaderboard.md`](../leaderboard.md).*

## TL;DR

Treating a benchmark's own stored predictions as data — item difficulty,
item–total discrimination, and metric cross-checks — is enough to find
problems that grep-style validation misses. For this benchmark it surfaced
one task whose gold is partly broken, quantified how badly chrF mis-measures
two tasks, and showed which tasks carry independent signal. None of it
required re-running a model.

## 1. `char-gloss` is broken at the gold level, not the model level

`char-gloss` has the lowest headline of all six tasks (chrF ≈ 0.12–0.21). The
naive reading is "models are bad at glossing Classical characters." The
psychometrics say otherwise:

- **27 of 100 items are floor items** — every one of the 10 models scores
  ≈0, so the item separates nothing.
- **18 of those 27 have gold = `"同本义。"`** — a dictionary cross-reference
  stub ("same as the original meaning", defined elsewhere), not a usable
  gloss. The build script sampled the placeholder sense instead of resolving
  it. Models produce *correct* glosses (`留宿`, `香气`, `从上取物`) and chrF
  against `同本义。` returns ≈0 for all of them.

This is the highest-value finding because it inverts the conclusion: the
char-gloss headline is not a measurement of model ability, it is an artifact
of broken gold plus a metric that cannot see paraphrase. The 18 items are now
flagged `metadata._audit_issue`; they are not deleted (stored results stay
comparable) but downstream consumers can filter them.

## 2. chrF and the LLM judge disagree by 4–5× on the open-ended tasks

On the two free-text tasks, the headline chrF and the (already-stored,
two-judge cross-validated) LLM-judge score tell completely different stories:

- **char-gloss**: chrF 0.12–0.21 vs judge 0.54–0.74.
- **translate**: chrF 0.20–0.24 vs judge 0.68–0.80.

chrF rewards literal character-n-gram overlap; a correct Classical gloss or
translation phrased differently from the reference scores near zero. The gap
is not a constant offset — it reorders models (e.g. on char-gloss `glm-5`
edges `minimax-m2.1` by chrF but trails it by judge). **chrF on these two
tasks is not a valid ranking signal on its own.** It remains useful only as a
cheap, reproducible floor; the judge-rescored table is the one to read. This
empirically confirms the long-suspected "chrF too strict on paraphrase"
concern with concrete numbers rather than intuition.

## 3. Scorer hygiene: a silent traditional-script penalty

`score_fill_in` did not apply the traditional→simplified normalization that
`idiom-source` already uses. Models answering in traditional script (e.g.
`饑` for gold `饥`) were marked wrong on a correct answer. Fixed and rescored
retroactively across all 10 models: opus-4-7 0.84→0.86,
opus-4-7-thinking 0.87→0.88, glm-5 0.44→0.45. Small in aggregate, but it is
pure measurement error and it was invisible until item-level inspection
showed strong models "failing" items weak models "passed." (Two latent
`rescore.py` bugs were fixed in passing — see quality-audit.)

## 4. Task structure: one redundant pair, one genuinely orthogonal task

Spearman correlation of the six task scores across the 10 models (n=10,
directional only):

- `punctuate` ↔ `translate` ρ = **+0.88** — the only pair above 0.8. They
  largely rank models the same way; a v2 could justify dropping or merging
  one, or keep both only if the *failure modes* differ (worth a follow-up).
- `compress` ↔ `char-gloss` ρ = **−0.02**, `compress` ↔ `fill-in` ρ =
  **+0.03** — `compress` (modern→Classical compression, the newest task) is
  near-orthogonal to the rest. It is the task that adds the most independent
  information; adding it was the right call.
- Everything else sits in a moderate 0.3–0.6 band: correlated (all tap
  Classical competence) but not redundant.

## 5. Difficulty distribution: the bench is bimodal, not calibrated

- `idiom-source` has **23 ceiling items** (every model solves) and 13 floor
  — only ~64% of items do any discriminating work.
- `translate`, `char-gloss`, `compress` are floor-heavy (mean difficulty
  0.23 / 0.16 / 0.12), partly real difficulty, partly metric artifact (§2).
- The healthiest tasks by item–total discrimination are `fill-in` (0.45) and
  `idiom-source` (0.42); `translate` is weakest (0.17) — again, mostly chrF.

A well-calibrated benchmark wants items clustered around 50% solve rate. This
one is bimodal (trivial or impossible), which inflates variance and wastes
question budget.

## Honest scope and limitations

- **n = 10 models, 100 questions/task.** Discrimination and task-correlation
  numbers are directional, not significant. Every section says so.
- **Excluding all 31 audit-flagged items** moves the bench-wide dead-item
  rate only 18% → 14% and leaves mean discrimination flat (0.317 → 0.319).
  Bad gold explains the *char-gloss floor specifically*, **not** the
  bench-wide dead mass. The remaining dead items are genuine
  ceiling/floor and need *harder replacement items*, not relabeling — do not
  oversell the audit.
- **The LLM judge is not ground truth.** It is two-model cross-validated
  (Opus + Sonnet agree), which is a reasonable proxy for these tasks but not
  a substitute for human adjudication on the contested items.

## Implications for v1.x

1. Regenerate the 18 circular-gold `char-gloss` items from the CC0 corpus
   with resolved senses (deterministic, no model calls) — but this
   invalidates stored predictions for those items, so it needs a *scoped
   rerun* (cost), not a free rescore. Defer until a rerun is funded.
2. Replace `idiom-source`'s 23 ceiling items with rarer allusions
   (deterministic from corpus).
3. Promote the judge-rescored table to the primary leaderboard for
   `translate`/`char-gloss`; keep chrF as a labelled secondary floor.
4. Decide `punctuate`/`translate` redundancy with a failure-mode comparison,
   not just the correlation.
