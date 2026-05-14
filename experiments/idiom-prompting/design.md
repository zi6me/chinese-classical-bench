# Design — Idiom Prompting Compression Experiment

## Thesis (Chinese-in-LLM-era second pillar)

> 典故 = 语义级 RAG 压缩。
>
> 一个 4 字典故承载一整段历史故事 + 一个抽象策略原型。给 LLM 一句含典故的 prompt，
> 相当于免费灌进了那段背景知识 —— 因为模型预训练时已经吸收过几乎所有典故。
> 这是中文相比英文在 prompting 层独有的压缩通道。

要立住这个论点，需要同时证明：
1. **典故 prompt 比白话展开 prompt 短** (token 节省可测)
2. **典故 prompt 的下游答案不比白话版差** (质量保持)

如果二者同时成立，典故就是 prompting 层的 **free lunch**。

## Method

### Scenarios
50 个叙事性强的典故 (curated)，覆盖：
- 策略类: 图穷匕见、围魏救赵、退避三舍、背水一战、四面楚歌、请君入瓮、围魏救赵
- 性格/教化类: 卧薪尝胆、负荆请罪、三顾茅庐、悬梁刺股
- 反面教训类: 邯郸学步、画蛇添足、守株待兔、刻舟求剑、削足适履、东施效颦
- 哲理类: 塞翁失马、愚公移山、对牛弹琴
- 才情类: 七步成诗、入木三分、画龙点睛、洛阳纸贵
- ...

### Triple generation
对每个典故，用 Claude Sonnet 4.6 生成：
- **idiom_prompt**: 1-2 句现实场景 (商业/政治/管理/教育)，自然嵌入典故 4 字
- **literal_prompt**: 同一场景，但把那 4 字展开成 1-2 句白话描述，保留其他文字一致
- **question**: 1 句下游分析问题，对两个版本通用

### Run
3 models × 2 versions × 50 scenarios = **300 calls**
- claude-opus-4-7 (top frontier)
- deepseek-3.2 (open Chinese)
- qwen3-coder-next (Chinese-native, code-tuned)

通过 kcli-gw (`http://localhost:8990/v1`) 调用，concurrency=4。

### Measure
- **tt_prompt_tokens**: `tiktoken cl100k_base` 用户 prompt token 数 (fair, deterministic)
- **prompt_char_len**: 字符长度 (sanity)
- **api_prompt_tokens / api_completion_tokens**: 提供商上报的 token (包含 kcli-gw 注入的系统 prompt，不可直接比较)
- **answer text**: 长度 + 内容用于后续 judge

### Judge
对每个 (scenario, model) 对，把同一 scenario 的两个答案随机 A/B 配对，发给 Claude Opus 4.7 盲判：
- 输入: scenario + question + answer A + answer B (不告诉哪个是 idiom/literal 版)
- 输出: winner ∈ {A, B, Tie}
- A/B 顺序随机化 (用 hash 种子保证可重现)

3 models × 50 scenarios = **150 judge calls**

### Headline metric
- Mean token reduction (idiom vs literal)
- Quality preference rate: idiom_wins / tie / literal_wins
- **Decision rule**: 如果典故 prompt **token 节省 ≥ 25%** 且 **not-loss rate (idiom_wins + tie) ≥ 70%**，
  则第二支柱立住。

## Why this design (and what it leaves out)

### What it tests
- Compression in the **user prompt**, holding question constant.
- Whether frontier LLMs decode the 典故 → story → strategy mapping correctly.

### What it doesn't test (limitations)
1. **No coverage of rare/obscure 典故** — only well-known ones from textbooks. Frontier models may break down on rare ones; that's a separate experiment.
2. **No human evaluator** — judge is also Claude family, so a "Claude family agrees with itself" risk exists. Sonnet 4.6 generated scenarios → Opus 4.7 judges. Mitigated by blind A/B and asking for reason.
3. **No English baseline** — can't directly say "Chinese > English on prompting compression" without running an English-idiom or paraphrase analog. This experiment only validates "in Chinese, 典故 is a compression channel."
4. **No multi-trial variance** — single call per cell. Temperature=0.3 → some noise. 50 scenarios per model gives N=50 for per-model effect, which is enough to see direction but not high precision.
5. **Open models tokenization** — DeepSeek and Qwen tokenize Chinese characters more efficiently than cl100k_base, so the *real* token-saving for those providers may be smaller in absolute terms but the *ratio* should still hold.
