# 传播帖草稿 — 中文（知乎 / 即刻）

**标题：《国产开源 LLM 在中国古典文献上谁最强？我跑了 10 个模型 500 道题》**

---

"国产模型在文言文上肯定比 Claude/GPT 强" —— 这话我见过无数次，但从没人拿数字说话。于是我做了个小评测，真去测了一下。

**chinese-classical-bench**：5 个任务 × 100 题 = 500 道，全部从我整理的一份 CC0 语料（完整十三经 + 说文解字 + 资治通鉴 + 二十四史前 15 部）里抽样：

- **古译今** — 文言译白话（chrF + 字符 F1）
- **断句加标点** — 给无标点古文加标点（标点位置 F1）
- **字义解释** — 解释某字在句中的含义（chrF）
- **典故出处** — 给一句典故，答出自哪本书（书名精确匹配）
- **字词填空** — 单字 cloze（精确匹配）

**排行榜（5 项平均）：**

| 排名 | 模型 | Avg |
|---|---|---|
| 1 | claude-opus-4-7 | 0.547 |
| 2 | claude-opus-4-7 (thinking) | 0.544 |
| 3 | claude-sonnet-4-6 | 0.486 |
| 4 | deepseek-3.2 | 0.483 |
| 5 | glm-5 | 0.477 |
| 6 | minimax-m2.1 | 0.473 |
| 7 | minimax-m2.5 | 0.436 |
| 8 | qwen3-coder-next | 0.426 |
| 9 | Qwen3.5-35B-A3B | 0.407 |
| 10 | claude-haiku-4-5 | 0.346 |

**几个反直觉的发现：**

**1.「Claude 文言文差」其实是尺寸问题，不是数据问题。** Opus 4.7 五项里四项第一；同一家同一代，Sonnet 4.6 只有 0.486、Haiku 4.5 只有 0.346 —— 训练数据一样，差距 58%。所以"Claude 没读过古文"这个说法站不住，小模型记不住而已。

**2. Thinking 模式没有总体增益**（0.544 vs 0.547），而且在**典故识别上反而退步**（0.61 vs 0.64）。"这句话出自哪本书"是纯记忆任务，延长推理弥补不了预训练里没有的东西。

**3. 典故识别仍是国产模型的护城河：** DeepSeek V3.2（0.74）> GLM-5（0.73）> MiniMax-2.1 / Opus 4.7（0.64）。不过相对老一轮，差距明显收窄了。

**4. 单字填空是 Anthropic 全家通吃：** Opus-thinking 0.87 / Opus 0.84 / Sonnet 0.70 / DeepSeek 0.55。单字级的古文字恢复，Claude 系压倒性。

**5. GLM-5 是综合最好的国产开源** —— 翻译/断句/字义/典故四项都进前三，只有填空弱。要在国产里选一个跑古文任务，GLM-5。

**6. MiniMax M2.1 → M2.5 是中文古典上的退步**（0.473 → 0.436），主要丢在典故识别和填空。新版可能为别的能力优化，但损伤了中文古典记忆 —— "越新越好"在这个维度不成立。

**已知局限：** 古译今/字义用 chrF 打分，对同义改写偏严（下一步会加 LLM judge）；题目从公开语料抽样，大模型大概率训练过，所以**绝对分数别太当真，看相对排序就行**。

全部开放：题目 + 打分器 + runner 在 GitHub，数据集 + 在线排行榜在 HuggingFace。欢迎 PR 自己模型的结果上榜。

- 代码：https://github.com/gujilab/chinese-classical-bench
- 数据集：https://huggingface.co/datasets/gujilab/chinese-classical-bench
- 在线排行榜：https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard
- 源语料（CC0）：https://huggingface.co/datasets/gujilab/chinese-classical-corpus

求人帮忙补：Llama-3.3、Yi-Lightning、ChatGLM、InternLM、GPT-4o、Gemini。
