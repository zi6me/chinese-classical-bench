# Are `punctuate` and `translate` redundant?

*2026-05-16. Follow-up to `item-analysis.md`, which flagged
`punctuate`↔`translate` Spearman ρ=+0.88 (the only task pair ≥0.8) as a
possible-redundancy candidate. Zero model calls — stored predictions only.*

## Verdict: collinear at n=10, but construct-distinct. Keep both.

The ρ=0.88 is **not** evidence of redundancy. It is what you get when 10
models spanning a wide ability range are scored on any two competence
measures — strong models are uniformly strong. Proof: `punctuate`'s
*character-preservation* sub-metric, a dimension `translate` cannot even
express, still correlates ρ=+0.86 with translate chrF. When even an
orthogonal-by-construction sub-signal correlates 0.86, inter-task ρ has no
power to resolve redundancy at this n. The question cannot be answered by
correlation here; it has to be answered by *what the tasks stress*.

## The tasks fail on opposite material

Mean item difficulty by source category (higher = easier):

- **translate** — 史 0.31 · 经 0.21 · 子 0.20 · 集 0.20. Spread across all
  four; hardest items are 经(5)/子(5)/集(4) of the bottom 15, almost no 史.
- **punctuate** — 经 0.86 · 史 0.68. Hardest 15 items are **14/15 from 史**
  (dynastic histories), almost none from 经.

So the hardest material is **disjoint**: `translate` is hardest on dense
philosophical/literary text (子/集) — it isolates *semantic transfer*.
`punctuate` is hardest on long unpunctuated narrative histories (史) — it
isolates *boundary segmentation*. A model can be strong at one and weak at
the other; the n=10 leaderboard just doesn't contain such a model yet
because the current 10 are good-at-everything frontier models.

**Recommendation:** do not drop or merge. Downgrade the item-analysis flag
from "possibly redundant" to "collinear at n=10, construct-distinct —
re-test when the model pool includes mid-tier models that can dissociate the
two skills." Redundancy is a claim about constructs, and the constructs here
are different.

## Bonus: `punctuate` surfaces a failure mode `translate` cannot

`punctuate` asks the model to insert punctuation **without changing the
text**. Its `char_preserved` sub-metric catches models that silently rewrite
instead. Rewrite/drop rate on the 100 items:

- minimax-m2.1 **38/100**, minimax-m2.5 **38/100**, qwen3-coder-next 34,
  Qwen3.5-35B-A3B 31, claude-haiku 28, sonnet-4-6 26, deepseek-3.2 23,
  glm-5 21, opus-4-7 18, opus-4-7-thinking 18.

This is a concrete instruction-fidelity behavior — the minimax models
rewrite over a third of inputs when told only to punctuate — that a
generative task like `translate` structurally cannot reveal (it has no
"preserve the input" constraint). It is rank-correlated with general ability
(so it doesn't reorder the headline at n=10), but it is a real, actionable
diagnostic. **Recommendation:** surface `char_preserved` as a labelled
secondary column on the leaderboard rather than burying it inside
`punct_f1`. It is the part of `punctuate` that is genuinely additive.

## Honest limitations

- n=10, n=100/task. Category-difficulty splits are directional.
- "Disjoint hardest material" is shown at the source-*category* level (4
  buckets); a finer source-level test would be stronger but the direction is
  unambiguous (punctuate hard-set is 93% 史; translate hard-set is 0% 史).
- The construct argument predicts the correlation will *drop* once the model
  pool includes models that are lopsided across the two skills. That is a
  falsifiable prediction, not a proof — revisit when more models are added.
