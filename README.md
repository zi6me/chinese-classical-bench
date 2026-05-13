# Chinese Classical Bench

中国古典语言能力评测基准 (Classical Chinese benchmark) — **5 个任务 × 100 题 = 500 道**，覆盖翻译、断句、字义、典故、续写填空。

> 📊 在线排行榜: [🤗 Space — chinese-classical-bench-leaderboard](https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard)
> 🤗 本评测集也在 HuggingFace: [gujilab/chinese-classical-bench](https://huggingface.co/datasets/gujilab/chinese-classical-bench) — `load_dataset("gujilab/chinese-classical-bench", "translate")`
> 🔗 配套语料集: [gujilab/chinese-classical-corpus](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) (CC0 公有领域)

## 评测目的

回答一个具体问题：**国产开源 LLM 在中国古典文献理解上谁更强？**

主要面向 Qwen / DeepSeek / Llama / Yi / ChatGLM / Baichuan / InternLM 等开源模型的横向对比，可选扩展到 Claude / GPT / Gemini。

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
| **claude-opus-4-7** | **0.244** | **0.800** | **0.213** | 0.640 | 0.840 | **0.547** |
| claude-opus-4-7-thinking | 0.242 | 0.790 | 0.207 | 0.610 | **0.870** | 0.544 |
| claude-sonnet-4-6 | 0.231 | 0.785 | 0.157 | 0.560 | 0.700 | 0.486 |
| deepseek-3.2 | 0.240 | 0.745 | 0.139 | **0.740** | 0.550 | 0.483 |
| glm-5 | 0.241 | 0.799 | 0.176 | 0.730 | 0.440 | 0.477 |
| minimax-m2.1 | 0.216 | 0.709 | 0.173 | 0.640 | 0.630 | 0.473 |
| minimax-m2.5 | 0.219 | 0.709 | 0.161 | 0.500 | 0.590 | 0.436 |
| qwen3-coder-next | 0.227 | 0.767 | 0.116 | 0.500 | 0.520 | 0.426 |
| Qwen3.5-35B-A3B | 0.225 | 0.753 | 0.175 | 0.500 | 0.380 | 0.407 |
| claude-haiku-4-5 | 0.204 | 0.729 | 0.128 | 0.320 | 0.350 | 0.346 |

**核心发现**：

1. **Claude Opus 4.7 接管榜首**（0.547）—— 5 项中 4 项第一（翻译 / 断句 / 字义 / 单字填空），唯一短板是典故识别。同代 Sonnet 4.6 仅 0.486、Haiku 4.5 仅 0.346 —— 同代差距 58%，说明"Claude 中文古典弱"是尺寸问题，不是数据问题
2. **Thinking 模式无总体增益** —— Opus 4.7 thinking 0.544 vs 非 thinking 0.547，4/5 任务 thinking 都略差。**典故识别 thinking 反而退步**（0.61 vs 0.64），印证：典故识别是纯记忆任务，延长推理无法弥补预训练语料
3. **典故识别仍是国产模型护城河** —— DeepSeek V3.2 (0.74) > GLM-5 (0.73) > MiniMax-2.1 / Opus 4.7 (0.64)；DeepSeek 优势从 24 个百分点收窄到与 GLM-5 持平，但相对 Claude 旗舰仍领先 10 个百分点
4. **fill-in（单字填空）Claude 全家通吃** —— Opus thinking 0.87 / Opus 0.84 / Sonnet 0.70 / MiniMax-2.1 0.63 / DeepSeek 0.55，单字级中文古文恢复 Anthropic 系压倒性优势
5. **GLM-5 是综合最好的国产开源** —— 翻译/断句/字义/典故四项均进前三，仅 fill-in (0.44) 弱
6. **Sonnet 4.6 性价比意外** —— avg 0.486 紧贴 DeepSeek (0.483)，比所有 MiniMax / Qwen 都高，仅次于自家 Opus
7. **MiniMax M2.1 → M2.5 是中文古典 retrograde** —— 新版 m2.5 (0.436) 反而低于老版 m2.1 (0.473)，主要回退在 idiom-source (0.50 vs 0.64) 和 fill-in (0.59 vs 0.63)。新版可能针对其他能力做了优化但损伤了中文古典记忆

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

## License

题目和评分代码：**MIT**。源数据来自 [chinese-classical-corpus](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) (CC0)。
