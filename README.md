# Chinese Classical Bench

[![license](https://img.shields.io/badge/code-MIT-yellow)](LICENSE) [![data](https://img.shields.io/badge/questions-from%20CC0%20corpus-lightgrey)](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) [![HF dataset](https://img.shields.io/badge/%F0%9F%A4%97-dataset-blue)](https://huggingface.co/datasets/gujilab/chinese-classical-bench) [![HF leaderboard](https://img.shields.io/badge/%F0%9F%A4%97-leaderboard-orange)](https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard)

中国古典语言能力评测基准 (Classical Chinese benchmark) — **5 个任务 × 100 题 = 500 道**，覆盖翻译、断句、字义、典故、续写填空。

> 📊 在线排行榜: [🤗 Space — chinese-classical-bench-leaderboard](https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard)
> 🤗 本评测集也在 HuggingFace: [gujilab/chinese-classical-bench](https://huggingface.co/datasets/gujilab/chinese-classical-bench) — `load_dataset("gujilab/chinese-classical-bench", "translate")`
> 🔗 配套语料集: [gujilab/chinese-classical-corpus](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) (CC0 公有领域)

## 为什么做这个

短答：**中文（尤其文言文）在 LLM 时代有一个被严重低估的优势 —— 信息密度。**

- **Token 经济学**：同一句话用文言文表达，token 数约为现代英文的 1/2，比现代白话还再压缩 30-40%。在 1M 上下文卷成本的今天，这是 free lunch
- **典故 = 语义级 RAG 压缩**："图穷匕见"四字承载一整段故事 —— 典故是嵌在语言里的、人类沉淀 2000+ 年的"超浓缩 token"，英文几乎没有等价机制
- **3000+ 年单一书写系统**：跨时代知识图谱、概念演化建模、长时间窗文本相似度学习，所需的时间深度训练信号只有中文有

但现状是：训练语料古典占比极低，公开 benchmark（CMMLU / C-Eval）几乎只评白话，没人针对古典的"高密度短文本"优化 tokenizer 或评测体系。本仓库 + 配套语料集是想把这条赛道做扎实的两个基础设施 —— 让 LLM 中文古典能力变得**可量化、可对比、可训练**。

具体到这个 bench，500 题在回答两个问题：

1. **哪些模型在中文古典任务上已经达到可用水平？** —— 给做古籍/教育/出版/法律/中医等应用的人选模型用
2. **不同能力维度（理解 / 操控 / 记忆 / 推理）的 ceiling 和 bottleneck 在哪？** —— 给训练/微调的人定方向用

主要面向 Qwen / DeepSeek / GLM / MiniMax / Yi / InternLM 等中文模型横评，也扩展到 Claude / GPT / Gemini 作为对照组。

## 5 个任务

| Task | 名称 | 题数 | 主要指标 |
|------|------|------|------|
| `translate` | 古译今 | 100 | chrF (n=1..6, F2) |
| `punctuate` | 断句加标点 | 100 | 标点位置 F1 + 字符保留率 |
| `char-gloss` | 字义解释 | 100 | chrF (punct-stripped) + char-F1 |
| `idiom-source` | 典故出处 | 100 | 书名 EM + 引文 chrF |
| `fill-in` | 字词填空 | 100 | 单字精确匹配 |

详见 [docs/tasks.md](docs/tasks.md)。

## Quick Start

```bash
# 1. 重生成题目（可选，已 commit 的题目就在 data/）
python scripts/build_translate.py
python scripts/build_punctuate.py
python scripts/build_char_gloss.py
python scripts/build_idiom_source.py
python scripts/build_fill_in.py

# 2. 跑评测（需先启动 vLLM endpoint）
python scripts/eval_runner.py \
  --model Qwen/Qwen3-7B-Instruct \
  --base-url http://localhost:8000/v1 \
  --api-key EMPTY \
  --concurrency 8

# 调试可加 --limit 5 --tasks translate fill-in
# 也支持 OpenAI / Anthropic 兼容端点

# 3. 看单模型结果
cat results/Qwen_Qwen3-7B-Instruct.json | jq '.tasks | to_entries[] | {task: .key, summary: .value.summary}'

# 4. 跑完多个模型后聚合排行榜
python scripts/aggregate.py --out leaderboard.md
```

## 文件布局

```
data/                  # 5 × 100 道题 (jsonl)
scripts/
  build_*.py           # 各 task 题目生成脚本
  eval_runner.py       # OpenAI 兼容 API 调用 + 打分
  scorers.py           # chrF / char-F1 / 标点 F1 / EM
  aggregate.py         # 多模型结果 → markdown 排行榜
results/               # 每个模型一个 json
docs/tasks.md          # 任务详细说明
```

## Leaderboard

| Model | translate (chrF) | punctuate (Punct F1) | char-gloss (chrF) | idiom-source (Book EM) | fill-in (Exact) | Avg |
|---|---|---|---|---|---|---|
| **claude-opus-4-7** | **0.244** | **0.800** | **0.213** | 0.650 | 0.840 | **0.549** |
| claude-opus-4-7-thinking | 0.242 | 0.790 | 0.207 | 0.630 | **0.870** | 0.548 |
| claude-sonnet-4-6 | 0.231 | 0.785 | 0.157 | 0.560 | 0.700 | 0.486 |
| deepseek-3.2 | 0.240 | 0.745 | 0.139 | **0.740** | 0.550 | 0.483 |
| glm-5 | 0.241 | 0.799 | 0.176 | **0.740** | 0.440 | 0.479 |
| minimax-m2.1 | 0.216 | 0.709 | 0.173 | 0.660 | 0.630 | 0.477 |
| minimax-m2.5 | 0.219 | 0.709 | 0.161 | 0.550 | 0.590 | 0.446 |
| qwen3-coder-next | 0.227 | 0.767 | 0.116 | 0.540 | 0.520 | 0.434 |
| Qwen3.5-35B-A3B | 0.225 | 0.753 | 0.175 | 0.500 | 0.380 | 0.407 |
| claude-haiku-4-5 | 0.204 | 0.729 | 0.128 | 0.340 | 0.350 | 0.350 |

**核心发现**：

1. **Claude Opus 4.7 接管榜首**（0.549）—— 5 项中 4 项第一（翻译 / 断句 / 字义 / 单字填空），唯一短板是典故识别。同代 Sonnet 4.6 仅 0.486、Haiku 4.5 仅 0.350 —— 同代差距 57%，说明"Claude 中文古典弱"是尺寸问题，不是数据问题
2. **Thinking 模式无总体增益** —— Opus 4.7 thinking 0.548 vs 非 thinking 0.549，4/5 任务 thinking 都略差。**典故识别 thinking 反而退步**（0.63 vs 0.65），印证：典故识别是纯记忆任务，延长推理无法弥补预训练语料
3. **典故识别国产模型已被 GLM-5 追平** —— DeepSeek V3.2 / GLM-5 并列 (0.74) > MiniMax-2.1 (0.66) > Opus 4.7 (0.65)；老一轮 DeepSeek 独占第一的护城河没了，但相对 Claude 旗舰仍领先 9 个百分点
4. **fill-in（单字填空）Claude 全家通吃** —— Opus thinking 0.87 / Opus 0.84 / Sonnet 0.70 / MiniMax-2.1 0.63 / DeepSeek 0.55，单字级中文古文恢复 Anthropic 系压倒性优势
5. **GLM-5 是综合最好的国产开源**（0.479）—— 翻译/断句/字义/典故四项均进前三，仅 fill-in (0.44) 弱；与 MiniMax-2.1 (0.477) 仅差千分位，基本并列
6. **Sonnet 4.6 性价比意外** —— avg 0.486 紧贴 DeepSeek (0.483)，比所有 MiniMax / Qwen 都高，仅次于自家 Opus
7. **MiniMax M2.1 → M2.5 是中文古典 retrograde** —— 新版 m2.5 (0.446) 反而低于老版 m2.1 (0.477)，主要回退在 idiom-source (0.55 vs 0.66) 和 fill-in (0.59 vs 0.63)。新版可能针对其他能力做了优化但损伤了中文古典记忆

> 欢迎提交其他模型结果（开 PR 把 `results/<model>.json` 加进来即可）。
> Sonnet/Opus、DeepSeek、Llama、ChatGLM 等正在补充中。

### 关于分数

- `chrF` 是字符级 n-gram F2 分数（n=1..6），同义改写会扣分但语义对的话主要靠 `char_f1` 兜底
- `idiom-source` 的 Book EM 较宽松：模型答 "《史记》" 就算对，不要求卷次/篇名匹配
- `fill-in` 单字答案，模型能从带引号或单字输出中抽取（详见 `scorers.py`）

## 已知 limitation

- `translate` / `char-gloss` 用 chrF 评分，对同义改写过严 — 后续会加 LLM judge
- 5 个 task 题目均从配套 corpus 抽样，可能与某些模型的训练数据有重合污染（开源模型大多训练过《十三经》《史记》）
- 100 题/task 是 trade-off：太少噪声大，太多跑评测贵 — 后续可能扩到 200/task
- **11 题（2.2%）有数据质量问题**（主要在 punctuate：误从 校勘记/历法表 抽样），已用 `metadata._audit_issue` 字段标注。详见 [docs/quality-audit.md](docs/quality-audit.md)。可通过 `ds.filter(lambda x: not x['metadata'].get('_audit_issue'))` 过滤。这些题目未删除以保持已有 result 文件兼容

## Contributing

想让你的模型上榜：跑 `scripts/eval_runner.py` → 把 `results/<model>.json` + 重新生成的 `leaderboard.md` 一起开 PR。CI 会自动校验 schema 并核对 `leaderboard.md`。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。也欢迎改进打分器（chrF 对同义改写偏严、典故书名匹配可以更聪明）—— 结果文件里存了每题原始 prediction，打分器改了能对所有已有模型回溯重打分。

## License

题目和评分代码：**MIT**（见 [LICENSE](LICENSE)）。源数据来自 [chinese-classical-corpus](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) (CC0)。
