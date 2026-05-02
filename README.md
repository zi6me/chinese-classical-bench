# Chinese Classical Bench

中国古典语言能力评测基准 (Classical Chinese benchmark) — **5 个任务 × 100 题 = 500 道**，覆盖翻译、断句、字义、典故、续写填空。

> 🔗 配套数据集: [dzxr/chinese-classical-corpus](https://huggingface.co/datasets/dzxr/chinese-classical-corpus) (CC0 公有领域)

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
| claude-haiku-4-5 | 0.204 | 0.729 | 0.128 | 0.320 | 0.350 | **0.346** |

> 仅 1 个模型的 baseline。Sonnet/Opus 与开源 Qwen/DeepSeek 等正在补充中。
> 欢迎提交其他模型结果（开 PR 把 `results/<model>.json` 加进来即可）。

### 关于分数

- `chrF` 是字符级 n-gram F2 分数（n=1..6），同义改写会扣分但语义对的话主要靠 `char_f1` 兜底
- `idiom-source` 的 Book EM 较宽松：模型答 "《史记》" 就算对，不要求卷次/篇名匹配
- `fill-in` 单字答案，模型能从带引号或单字输出中抽取（详见 `scorers.py`）

## 已知 limitation

- `translate` / `char-gloss` 用 chrF 评分，对同义改写过严 — 后续会加 LLM judge
- 5 个 task 题目均从配套 corpus 抽样，可能与某些模型的训练数据有重合污染（开源模型大多训练过《十三经》《史记》）
- 100 题/task 是 trade-off：太少噪声大，太多跑评测贵 — 后续可能扩到 200/task

## License

题目和评分代码：**MIT**。源数据来自 [chinese-classical-corpus](https://huggingface.co/datasets/dzxr/chinese-classical-corpus) (CC0)。
