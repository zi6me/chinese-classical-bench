# Task Specifications

每个任务 100 道题，统一输出 JSONL，每行一条记录。

## 通用 Schema

```json
{
  "id": "<task>#<n>",
  "task": "translate | punctuate | char-gloss | idiom-source | fill-in",
  "instruction": "...",
  "input": "...",
  "reference": "...",      // 标准答案
  "metadata": { ... }      // 评分需要的额外字段
}
```

模型只看 `instruction + input`，输出与 `reference` 比较。

---

## Task 1: `translate` — 古译今

**输入**：一句古文 (10–60 字)
**输出**：现代汉语翻译

```json
{
  "id": "translate#1",
  "task": "translate",
  "instruction": "将下列古文翻译成现代汉语：",
  "input": "子曰：学而时习之，不亦说乎？",
  "reference": "孔子说：学了知识然后按一定的时间复习它，不也是很愉快吗？",
  "metadata": {"source": "论语·学而篇"}
}
```

**抽样策略**：从 `chinese-classical-corpus` translate.jsonl c2m 子集 stratified by category（经/史/子/集 各 25 题），长度均衡（10–60 字）。

**评分**：
- BLEU-4（chinese tokenizer，char-level）
- chrF（字符级 F-score）
- 可选：LLM-judge（让 GPT-5/Opus 打 1-5 faithfulness 分）

---

## Task 2: `punctuate` — 断句加标点

**输入**：连续无标点的古文（30–200 字）
**输出**：加好标点的古文

```json
{
  "id": "punctuate#1",
  "task": "punctuate",
  "instruction": "为下列古文添加标点：",
  "input": "夫天地者万物之逆旅也光阴者百代之过客也而浮生若梦为欢几何",
  "reference": "夫天地者，万物之逆旅也；光阴者，百代之过客也。而浮生若梦，为欢几何？",
  "metadata": {"source": "李白·春夜宴桃李园序"}
}
```

**抽样策略**：从 punctuate.jsonl 抽 100 条，覆盖正史 + 经传，长度 30–200 字。

**评分**：字符级 F1（正确添加的标点数 / 标准标点总数）。

---

## Task 3: `char-gloss` — 字义解释

**输入**：一个字 + 一句包含该字的古文
**输出**：该字在此句中的现代汉语义

```json
{
  "id": "char-gloss#1",
  "task": "char-gloss",
  "instruction": "解释下列字在引用古文中的含义：",
  "input": "字：道\n出处：吾道一以贯之。（《论语·里仁》）",
  "reference": "学说、思想",
  "metadata": {
    "char": "道",
    "source": "论语·里仁",
    "valid_answers": ["学说", "思想", "主张", "道理"]
  }
}
```

**抽样策略**：从 chinese-dictionary `char_detail.json` 抽含古文出处的字条，挑选 100 个高频实词（剔除虚词以避免歧义）。

**评分**：
- 软匹配：模型答案是否包含 `valid_answers` 任一同义项
- 严格：LLM-judge 是否捕捉到正确义项

---

## Task 4: `idiom-source` — 典故出处

**输入**：一个成语
**输出**：典故出自哪部典籍 + 原文引文

```json
{
  "id": "idiom-source#1",
  "task": "idiom-source",
  "instruction": "下列成语出自哪部典籍？请给出原文。",
  "input": "三人行必有我师",
  "reference": "出自《论语·述而》：「三人行，必有我师焉。择其善者而从之，其不善者而改之。」",
  "metadata": {
    "idiom": "三人行必有我师",
    "book": "论语",
    "chapter": "述而",
    "expected_quote": "三人行，必有我师焉"
  }
}
```

**抽样策略**：从 idiom.json 抽含 `source.book` 字段且 `book` 在我们 corpus 已有的 30 部典籍中的成语，100 个。

**评分**：
- 书名精确匹配（contains check on `book`）
- 引文 chrF ≥ 0.7 视为正确

---

## Task 5: `fill-in` — 字词填空

**输入**：一句古文，1 个字被替换为 `___`
**输出**：被遮住的字

```json
{
  "id": "fill-in#1",
  "task": "fill-in",
  "instruction": "下面这句古文中 ___ 处应填什么字？",
  "input": "学而时___之，不亦说乎？",
  "reference": "习",
  "metadata": {
    "source": "论语·学而篇",
    "context": "学而时习之，不亦说乎？",
    "alternatives": []
  }
}
```

**抽样策略**：从 corpus.jsonl 经类抽 100 句知名短句，遮蔽 1 个高信息量实词（剔除虚词如"也、之、其"等）。

**评分**：精确字符匹配。可选放宽到 `alternatives` 集合。

---

## 评分汇总

每个任务给出 0-1 分数，最后总榜按平均分排名。每个任务也独立排名供细看。

```json
{
  "model": "Qwen/Qwen3-7B-Instruct",
  "scores": {
    "translate":     {"bleu": 0.42, "chrf": 0.58},
    "punctuate":     {"f1": 0.81},
    "char-gloss":    {"soft_match": 0.67, "judge_score": 4.1},
    "idiom-source":  {"book_match": 0.55, "quote_chrf": 0.72},
    "fill-in":       {"exact": 0.34}
  },
  "overall": 0.58
}
```
