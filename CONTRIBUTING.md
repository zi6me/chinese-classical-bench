# Contributing

Two ways to help: **add a model to the leaderboard**, or **improve the benchmark**.

## Add a model result

1. Run the eval against any OpenAI-compatible endpoint (vLLM / OpenAI / Anthropic-compatible / DeepSeek / etc.):

   ```bash
   python scripts/eval_runner.py \
     --model <your-model-id> \
     --base-url <https://.../v1> \
     --api-key <KEY> \
     --concurrency 8
   ```

   This writes `results/<model>.json` with per-task summaries **and** per-question
   predictions (`tasks.<task>.items[].prediction`). Keep the predictions in the
   file — they let anyone re-score offline if the scorers change.

2. Regenerate the leaderboard:

   ```bash
   python scripts/aggregate.py --out leaderboard.md
   ```

3. Open a PR with **both** `results/<model>.json` and the updated `leaderboard.md`.
   (CI re-runs `aggregate.py` and will flag a mismatch.)

### Result file requirements

- Must parse as JSON with top-level keys: `model`, `tasks`.
- `tasks` must include all 5 tasks: `translate`, `punctuate`, `char-gloss`, `idiom-source`, `fill-in`.
- Each task needs a `summary` dict and an `items` list of 100 entries with `id`, `prediction`, `scores`.
- Decode params: `temperature=0.0` (or as close as the endpoint allows). Note any
  deviation (custom system prompt, reasoning/thinking mode, etc.) in the PR description.
- For reasoning models, append a suffix to the model id (e.g. `claude-opus-4-7-thinking`)
  so both variants can coexist on the leaderboard.

## Improve the benchmark

- **Better scorers** (`scripts/scorers.py`) — e.g. an LLM judge for `translate` / `char-gloss`
  (chrF over-penalizes valid paraphrase), or smarter book-name matching for `idiom-source`.
  Because result files store raw predictions, scorer changes can be applied retroactively
  to all existing models.
- **Fix bad questions** — wrong reference translations, ambiguous allusions, broken
  `metadata.expected_quote` fields. Edit the `data/*.jsonl` line and note it in the PR.
- **New tasks** — propose in an issue first; ideally auto-generatable from
  [chinese-classical-corpus](https://github.com/gujilab/chinese-classical-corpus) so the
  questions stay reproducible.

## Ground rules

- Source texts are public domain; benchmark code is MIT (see `LICENSE`).
- Don't game the leaderboard — submit honest runs.
- Be explicit about contamination risk: most questions are sampled from public corpora that
  models may have trained on. The point is *relative* comparison, not absolute capability.
