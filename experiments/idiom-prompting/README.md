# Idiom Prompting Compression Experiment

Tests the second pillar of the **"Chinese in LLM era"** thesis:
> 典故 (Chinese idioms) are a semantic-level RAG compression — a 4-character idiom carries an entire backstory that frontier LLMs decode for free.

## Files
- `design.md` — methodology, hypothesis, limitations
- `scenarios_seed.txt` — curated list of 50 narrative-rich 典故 (seed)
- `scenarios.jsonl` — generated triples `(idiom, idiom_prompt, literal_prompt, question)`
- `gen_scenarios.py` — generates the triples using Claude Sonnet 4.6
- `run.py` — runs the 3 models × 2 versions × N scenarios experiment via kcli-gw
- `results.jsonl` — model responses + token counts per (idiom, model, version)
- `judge.py` — uses Claude Opus 4.7 as blind A/B judge
- `judge_results.jsonl` — preference judgments per (idiom, model)
- `analyze.py` — produces `report.md`
- `report.md` — final numbers + headline

## Run order
```bash
python3 gen_scenarios.py    # build scenarios.jsonl
python3 run.py              # build results.jsonl (300 calls)
python3 judge.py            # build judge_results.jsonl (150 calls)
python3 analyze.py          # build report.md
```

All scripts are idempotent / resumable — re-running skips already-completed cells.

## Config
- Endpoint: `http://localhost:8990/v1` (kcli-gw)
- Key: `sk-kiro-test-123456`
- Concurrency: 4 (shared cluster, set in each script)
- Token measurement: `tiktoken cl100k_base` on user prompt only (kcli-gw injects a large system prompt that confounds API-reported `prompt_tokens`).
