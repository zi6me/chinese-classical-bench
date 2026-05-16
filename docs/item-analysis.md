# Item-level psychometrics

Retroactive analysis over **10 models** on stored predictions — no new model calls. Headline metric per task matches `scripts/aggregate.py`.

- **Difficulty** = mean headline score across models (1.0 = every model solves it; low = hard).
- **Discrimination** = corrected item–total correlation (item score vs. the model's mean over *all other* items). High = separates strong/weak models; ≤0 = noise or bad gold.
- N=10 models is small — read these as directional, not significant. Caveat applies throughout.

## translate  (metric: `chrf`, n=100 items)

- mean difficulty **0.229**, mean discrimination **0.172**
- **dead items: 4** (0 ceiling — every model ≈solves, 1 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 26** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 11
- worst negative-disc items: `translate#93` (-0.74), `translate#52` (-0.68), `translate#8` (-0.58), `translate#66` (-0.53), `translate#76` (-0.50), `translate#9` (-0.47), `translate#86` (-0.44), `translate#70` (-0.38)

## punctuate  (metric: `punct_f1`, n=100 items)

- mean difficulty **0.758**, mean discrimination **0.257**
- **dead items: 12** (3 ceiling — every model ≈solves, 8 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 17** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 16
- worst negative-disc items: `punctuate#52` (-0.69), `punctuate#20` (-0.51), `punctuate#91` (-0.51), `punctuate#4` (-0.50), `punctuate#32` (-0.41), `punctuate#71` (-0.39), `punctuate#68` (-0.30), `punctuate#90` (-0.25)

## char-gloss  (metric: `chrf`, n=100 items)

- mean difficulty **0.164**, mean discrimination **0.256**
- **dead items: 27** (0 ceiling — every model ≈solves, 27 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 19** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 16
- worst negative-disc items: `char-gloss#19` (-0.70), `char-gloss#47` (-0.56), `char-gloss#39` (-0.47), `char-gloss#68` (-0.32), `char-gloss#67` (-0.25), `char-gloss#26` (-0.22), `char-gloss#22` (-0.21), `char-gloss#63` (-0.12)

## idiom-source  (metric: `book_em`, n=100 items)

- mean difficulty **0.591**, mean discrimination **0.424**
- **dead items: 36** (23 ceiling — every model ≈solves, 13 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 5** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 11
- worst negative-disc items: `idiom-source#52` (-0.12), `idiom-source#14` (-0.10), `idiom-source#38` (-0.09), `idiom-source#77` (-0.05), `idiom-source#64` (-0.05)

## fill-in  (metric: `exact_match`, n=100 items)

- mean difficulty **0.587**, mean discrimination **0.452**
- **dead items: 20** (14 ceiling — every model ≈solves, 6 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 8** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 7
- worst negative-disc items: `fill-in#4` (-0.51), `fill-in#19` (-0.40), `fill-in#31` (-0.31), `fill-in#34` (-0.19), `fill-in#41` (-0.10), `fill-in#60` (-0.10), `fill-in#87` (-0.03), `fill-in#24` (-0.02)

## compress  (metric: `efficiency`, n=100 items)

- mean difficulty **0.123**, mean discrimination **0.370**
- **dead items: 5** (0 ceiling — every model ≈solves, 4 floor — every model ≈fails) → carry no information, drop/replace candidates
- **negative discrimination: 15** (stronger models do *worse* — likely ambiguous prompt or bad gold; audit first)
- low |discrimination| (<0.1): 12
- worst negative-disc items: `compress#9` (-0.33), `compress#22` (-0.29), `compress#14` (-0.27), `compress#31` (-0.22), `compress#77` (-0.14), `compress#62` (-0.13), `compress#67` (-0.12), `compress#100` (-0.11)

## Bench-wide

- 600 items total; **104 dead (17%)**, **90 negative-discrimination (15%)**
- mean discrimination across all items: **0.314**

## Task redundancy (Spearman over model task-means)

Correlation of the 6 task scores across 10 models. High |ρ| ⇒ the two tasks rank models the same way and one may be redundant. n=10 — directional only.

- translate / punctuate / char-gloss / idiom-source / fill-in / compress
- **punctuate**: punctuate~translate=+0.88
- **char-gloss**: char-gloss~translate=+0.60 char-gloss~punctuate=+0.54 char-gloss~idiom-source=+0.40 char-gloss~fill-in=+0.49 char-gloss~compress=-0.02
- **idiom-source**: idiom-source~translate=+0.56 idiom-source~punctuate=+0.26
- **fill-in**: fill-in~translate=+0.55 fill-in~punctuate=+0.32 fill-in~idiom-source=+0.41
- **compress**: compress~translate=+0.43 compress~punctuate=+0.35 compress~idiom-source=+0.62 compress~fill-in=+0.03

**Possibly redundant (|ρ|≥0.8):**
- `punctuate` ↔ `translate`  ρ=+0.88

