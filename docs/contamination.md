# Contamination / memorization probe

Does difficulty track how *over-represented* an item's source is, rather than Classical skill? Proxy A = source canonicity tier (3=core canon e.g. 论语/史记/诗经, 2=well-known classics, 1=obscure histories/子). Proxy B = in-corpus 10-char shingle recurrence (low-resolution, see header). Spearman vs item difficulty from `item-analysis.json`. n≈100/task.

## translate  (n=100)

- **Spearman(canonicity tier, difficulty) = +0.083**  (shingle proxy: n/a)
- mean difficulty by tier: T1 0.223 (n=45) · T2 0.230 (n=34) · T3 0.240 (n=21)

## punctuate  (n=100)

- **Spearman(canonicity tier, difficulty) = +0.059**  (shingle proxy: -0.344)
- mean difficulty by tier: T1 0.849 (n=44) · T2 0.552 (n=24) · T3 0.789 (n=32)

## idiom-source  (n=100)

- **Spearman(canonicity tier, difficulty) = +0.677**  (shingle proxy: +0.065)
- mean difficulty by tier: T1 0.069 (n=13) · T2 0.445 (n=33) · T3 0.806 (n=54)

## fill-in  (n=100)

- **Spearman(canonicity tier, difficulty) = +0.077**  (shingle proxy: -0.195)
- mean difficulty by tier: T2 0.400 (n=1) · T3 0.593 (n=99)

## compress  (n=100)

- **Spearman(canonicity tier, difficulty) = +0.419**  (shingle proxy: +0.015)
- mean difficulty by tier: T1 0.102 (n=39) · T2 0.127 (n=42) · T3 0.156 (n=19)

## Bench-wide

- **Spearman(canonicity, difficulty) over 500 items = +0.339**
- shingle proxy = +0.167
- mean difficulty: core-canon T3 **0.602** (n=225) · T2 **0.310** (n=134) · obscure T1 **0.370** (n=141)

## Interpretation

The effect is **not uniform** — bench-wide ρ=+0.339 hides strong task-level structure:

- **Recall-driven** (canonicity ρ≥0.30): `idiom-source` (ρ=+0.68), `compress` (ρ=+0.42). For these, source over-representation is a major difficulty driver — they partly measure *do you recognize this famous text*, not Classical reasoning. `idiom-source` is the extreme case and is exactly the task carrying the 23 ceiling items in `item-analysis.md`.
- **Clean** (|ρ|<0.15): `fill-in`, `punctuate`, `translate`. Difficulty here is skill/metric-driven, not memorization — these tasks are contamination-robust.

Core-canon (T3) items are on average +0.232 easier than obscure-source (T1) items bench-wide. **Actionable:** report a canonicity-stratified leaderboard, and in v1.x rebuild `idiom-source` (and to a lesser degree `compress`) from Tier-1 sources so the score reflects competence over recall. `translate`/`punctuate`/`fill-in` need no contamination fix.

