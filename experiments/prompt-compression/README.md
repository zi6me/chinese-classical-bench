# Prompt Compression Experiment: 文言文 vs 现代中文 vs English

## Goal

Validate the headline claim: **using 文言文 as prompt language reduces token cost without hurting downstream accuracy.**

Tokenizer-level evidence (see `../../tokenizer_study/`) shows 文言文 ≈ 0.57× English tokens. This experiment tests **task-level accuracy** under the same compression.

## Design

- **50 multiple-choice questions** from C-Eval (val splits, has answer key):
  - `chinese_language_and_literature` (23 items, all)
  - `high_school_chinese` (19 items, all)
  - `middle_school_history` (8 items, first 8)
- **3 prompt versions** per question:
  - `modern_cn` — original C-Eval text (baseline)
  - `english` — Claude Sonnet 4.6 translation to natural English
  - `classical_cn` — Claude Sonnet 4.6 rewrite to 文言文 (literary Chinese)
- **3 evaluator models**: `claude-opus-4-7`, `deepseek-3.2`, `qwen3-coder-next`
- Total: 3 versions × 50 q × 3 models = **450 eval calls** + 100 translation calls

## Files

- `run.py` — single end-to-end script (load → translate → eval → analyze)
- `prompts.jsonl` — 150 rows: `{question_id, version, prompt, correct_letter, source_config}`
- `results.jsonl` — 450 rows: `{question_id, version, model, predicted, correct, input_tokens, output_tokens, latency_s}`
- `report.md` — final numbers + headline finding
- `.env.example` — config template

## Reproduce

```bash
cd /Users/zion/Documents/zion/chinese-classical-bench/experiments/prompt-compression
cp .env.example .env  # adjust if needed
pip install --user openai datasets --break-system-packages
python3 run.py            # full run (~10-15 min)
python3 run.py --analyze  # re-run analysis on existing results.jsonl
```

## Token Counting Note

kcli-gw returns `prompt_tokens` (includes kcli-gw's own system overhead, varies per model) and reports `completion_tokens=0` (bug/limitation). We use:

- **input chars** — local character count of user prompt as the version-independent compression metric
- **prompt_tokens** as reported by kcli-gw — relative comparison within the same model is meaningful (system overhead cancels)
- **output chars** — local character count of the model response (completion_tokens is unreliable here)

## Concurrency

`asyncio.Semaphore(2)` because kcli-gw is shared with other agents. Don't raise this.
