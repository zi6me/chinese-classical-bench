# Tokenizer 横评：中文古典 vs 现代中文 vs 英文

测试集：30 对中文古典 + 现代中文 + 英文翻译三联对照。
中文古典 + 现代中文来自 [gujilab/chinese-classical-corpus](https://huggingface.co/datasets/gujilab/chinese-classical-corpus) 的 m2c 翻译对，英文版由 Claude Sonnet 4.6 翻译。

## TL;DR

- **文言文比英文省 37% token**（7 个 tokenizer 平均）
- **现代中文比英文省 20% token**
- **文言文比现代中文再省 20% token**
- 最省 token 的 tokenizer：**Qwen2.5**（文言/英文 0.57×）
- 最费 token 的 tokenizer：**GPT-3.5 / GPT-4 (cl100k_base)**（文言/英文 0.87×）

## 主表：每条样本平均 token 数（按文言/英文比升序）

| Tokenizer | 文言文 | 现代中文 | 英文 | 文言/英文 | 现代/英文 | 文言/现代 |
|---|---|---|---|---|---|---|
| **Qwen2.5** 🥇 | 52.0 | 64.6 | 91.2 | **0.57×** | 0.71× | 0.81× |
| **Qwen3** | 52.0 | 64.6 | 91.2 | **0.57×** | 0.71× | 0.81× |
| **DeepSeek-V3** | 51.2 | 61.1 | 89.3 | **0.57×** | 0.69× | 0.84× |
| **GLM-4** | 52.3 | 63.2 | 90.9 | **0.58×** | 0.70× | 0.83× |
| **Yi-1.5** | 57.7 | 68.7 | 95.4 | **0.60×** | 0.72× | 0.84× |
| **GPT-4o / GPT-4.1 / o1 (o200k_base)** | 57.6 | 76.3 | 89.0 | **0.65×** | 0.86× | 0.76× |
| **GPT-3.5 / GPT-4 (cl100k_base)** | 79.4 | 108.6 | 91.0 | **0.87×** | 1.19× | 0.73× |

> **比例越小，token 越省。** `文言/英文 = 0.50` 表示同样语义文言文比英文少用一半 token。

## 关键发现

1. **国产模型 tokenizer 对中文显著优于 OpenAI** —— DeepSeek-V3 / Qwen / GLM-4 文言/英文 ≈ 0.57，GPT-4o 0.65，老 cl100k_base 0.87。差距来自字表里给中文留多少 vocabulary slots。
2. **GPT-3.5/4 (cl100k_base) 切中文居然比英文还费 19% token** （现代/英文 1.19×）—— 老 GPT 用户为中文付了双倍的钱。GPT-4o 的 o200k_base 已经修复（0.86×），但仍逊于国产 tokenizer。
3. **文言文是 free lunch** —— 几乎所有 tokenizer 上，文言文都比现代中文再省 17-27% token，比英文省 35-43%。本项目 corpus 的 197 万 m2c/c2m 指令对就是用来训练这种压缩-恢复能力的。
4. **数字直观感受**：用 DeepSeek-V3 tokenizer，1000 个英文 token 大致 ≈ 685 个现代中文 token ≈ 574 个文言文 token。长上下文 / 长 system prompt / RAG 场景下，**用文言文做提示词压缩能直接降本 ~45%**。

## 字符级密度（chars per token）

Token 切得越粗 → 每 token 承载的字符越多 → 越适合该语言。

| Tokenizer | 文言文 | 现代中文 | 英文 |
|---|---|---|---|
| **GPT-4o / GPT-4.1 / o1 (o200k_base)** | 0.95 | 1.04 | 4.61 |
| **GPT-3.5 / GPT-4 (cl100k_base)** | 0.69 | 0.73 | 4.50 |
| **Qwen2.5** | 1.05 | 1.23 | 4.49 |
| **Qwen3** | 1.05 | 1.23 | 4.49 |
| **DeepSeek-V3** | 1.07 | 1.29 | 4.59 |
| **GLM-4** | 1.04 | 1.25 | 4.51 |
| **Yi-1.5** | 0.95 | 1.15 | 4.29 |

## 示例

**来源**: 汉书·传/张冯汲郑传

- 文言文 (47 字): 左右皆曰： 善。 释之前曰： 使其中有可欲，虽锢南山犹有隙；使其中亡可欲，虽亡石椁，又何戚焉？
- 现代中文 (71 字): 张释之上前说道： 假使它裹面有能够引起贪欲的东西，即使封闭南山作为棺，也还有缝隙；如果裹面没有能够引起贪欲的东西，即使没有石棺，又何必忧虑呢？
- 英文 (292 字符): Zhang Shizhi stepped forward and said: If there is anything inside worth coveting, then even if you sealed up the whole of Mount Nan to serve as a coffin, there would still be gaps; but if there is nothing inside to tempt greed, then even without a stone coffin, what is there to worry about?

**来源**: 明史·志/卷四十三

- 文言文 (48 字): 凡教坊司官常服冠带，与百官同；至御前供奉，执粉漆笏，服黑漆幞头，黑绿罗大袖襕袍，黑角偏带，皂靴。
- 现代中文 (76 字): 凡是教坊司官员日常穿的衣服，与各级官员相同；到皇帝跟前侍奉，持着漆成白色的朝板，戴漆成黑色的幞头，穿黑绿色绫罗大袖栏袍，黑色角质材料装饰的偏带，黑色靴。
- 英文 (372 字符): All officials of the Jiaofang Bureau wear the same everyday attire as officials of corresponding ranks. When attending upon the emperor, they carry white-lacquered court tablets, wear black-lacquered futou headwear, and are dressed in dark greenish-black silk robes with wide sleeves and horizontal trim, with a side belt adorned with black horn fittings, and black boots.

**来源**: 宋史·列传/卷七十五

- 文言文 (123 字): 皇祐中，颇多灾异，奎极言其徵曰： 今冬令反燠，春候反寒，太阳亏明，五星失度，水旱作沴，饥馑荐臻，此天道之不顺也。自东徂西，地震为患，大河横流，堆阜或出，此地道之不顺也。邪曲害政，阴柔蔽明，群小纷争，众情壅塞，西、北贰敌，求欲无厌，此人事之不和也。
- 现代中文 (152 字): 皇年间，天灾颇多，吴奎分析其症候说 ：今年冬暖春寒，太阳不够明亮，五大行星运行失度，水旱二灾作恶，饥荒接踵而至，这是天道不顺；从东到西，地震为患，黄河改道，地面还冒出山来，这是地道不顺；邪恶势力妨害朝政，阴险小人挡住了皇上的光明，尔虞我诈，明争暗斗，下情难以上达，西夏、辽国二敌，欲壑难填，这是人事不和。
- 英文 (903 字符): During the reign period, natural disasters were frequent. Wu Kui analyzed the signs and said: This winter was warm and the spring cold; the sun lacked its usual brightness; the five planets moved out of their proper courses; floods and droughts brought havoc; and famines followed one upon another — this is the way of Heaven falling into disorder. From east to west, earthquakes caused suffering; the Yellow River changed its course; and mountains rose up from the ground — this is the way of Earth falling into disorder. Wicked forces obstructed the affairs of court; treacherous men blocked the light of the sovereign; deceit and scheming ran rampant; open strife and covert maneuvering went unchecked; the conditions of the people below could not reach those above; and the two enemies, Western Xia and Liao, were insatiable in their greed — this is the way of human affairs falling into disharmony.

## 方法

- 样本：从 corpus 抽样 30 条文言文 + 现代中文翻译对（文言 40-150 字，现代 60-300 字）
- 英文版：把现代中文用 Claude Sonnet 4.6 翻译为流畅英文（temperature=0）
- Tokenizer 加载：tiktoken 官方编码，或 HuggingFace `AutoTokenizer.from_pretrained`（trust_remote_code=True）
- 计数：`add_special_tokens=False`（不算 BOS/EOS）
- 重新跑：`python scripts/tokenizer_study.py`（结果在 `tokenizer_study/`）