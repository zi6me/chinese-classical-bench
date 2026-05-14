# Prompt Compression Experiment — Report
**Setup:** 50 C-Eval humanities multiple-choice questions × 3 prompt versions (modern_cn baseline, english translation, classical_cn rewrite) × 3 evaluator models (claude-opus-4-7, deepseek-3.2, qwen3-coder-next). Translations by `claude-sonnet-4-6` via kcli-gw at `http://localhost:8990/v1`. Concurrency cap = 5.
## Per-(model, version) summary
model | version | n | accuracy | mean prompt chars | mean output chars | mean prompt_tokens (kcli-reported)
--- | --- | --- | --- | --- | --- | ---
claude-opus-4-7 | modern_cn | 50 (err 0) | 86.0% | 121 | 1 | 1260
claude-opus-4-7 | english | 50 (err 0) | 76.0% | 450 | 1 | 1267
claude-opus-4-7 | classical_cn | 50 (err 0) | 80.0% | 115 | 1 | 1257
deepseek-3.2 | modern_cn | 50 (err 0) | 80.0% | 121 | 1 | 4879
deepseek-3.2 | english | 50 (err 0) | 60.0% | 450 | 1 | 4915
deepseek-3.2 | classical_cn | 50 (err 0) | 64.0% | 115 | 1 | 4884
qwen3-coder-next | modern_cn | 50 (err 0) | 78.0% | 121 | 1 | 3108
qwen3-coder-next | english | 50 (err 0) | 68.0% | 450 | 12 | 3128
qwen3-coder-next | classical_cn | 50 (err 0) | 66.0% | 115 | 1 | 3109

## Compression vs accuracy (classical_cn relative to baselines)
model | acc Δ vs modern_cn | char savings vs modern_cn | acc Δ vs english | char savings vs english
--- | --- | --- | --- | ---
claude-opus-4-7 | -6.0pp | +4.7% | +4.0pp | +74.4%
deepseek-3.2 | -16.0pp | +4.7% | +4.0pp | +74.4%
qwen3-coder-next | -12.0pp | +4.7% | -2.0pp | +74.4%

## Headline
Averaged across the 3 models, switching prompts from **现代中文 → 文言文** changes accuracy by **-11.3pp** while saving **+4.7%** of input characters. vs **English → 文言文**: accuracy **+2.0pp**, char savings **+74.4%**.

_Caveat:_ kcli-gw's reported `prompt_tokens` includes a per-model system overhead (≈1.2k–4.5k tokens) that dwarfs the question payload, so character count is the cleanest version-comparison metric here. The tokenizer-level study (`../../tokenizer_study/`) gives the per-language token ratios.
