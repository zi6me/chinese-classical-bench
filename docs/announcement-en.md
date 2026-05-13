# Announcement draft — English (r/LocalLLaMA / Show HN)

**Title:** I benchmarked 10 LLMs on Classical Chinese (translation, punctuation, glossing, allusion-ID, cloze) — Claude Opus 4.7 leads, but DeepSeek still owns "name the source"

---

I kept seeing "Chinese open models are obviously best at Classical Chinese" stated as fact, with nothing to back it. So I built a small benchmark to actually check.

**chinese-classical-bench** — 5 tasks × 100 questions = 500, all sampled from a CC0 corpus I assembled (Thirteen Classics + Shuowen Jiezi + Zizhi Tongjian + first 15 of the Twenty-Four Histories):

- `translate` 古译今 — Classical → modern Chinese (chrF + char-F1)
- `punctuate` 断句 — restore punctuation to unpunctuated text (punctuation-position F1)
- `char-gloss` 字义 — explain a single character's meaning in context (chrF)
- `idiom-source` 典故 — given an allusion, name the book it comes from (book exact-match)
- `fill-in` 填空 — single-character cloze (exact match)

**Leaderboard (avg over 5 tasks):**

| # | Model | Avg |
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

**Findings that surprised me:**

1. **The "Claude is bad at Classical Chinese" meme is a size problem, not a data problem.** Opus 4.7 tops 4 of 5 tasks; Sonnet 4.6 is 0.486, Haiku 4.5 is 0.346 — same family, same training data, ~58% spread.
2. **Thinking mode doesn't help overall** (0.544 vs 0.547) and *hurts* allusion-ID (0.61 vs 0.64). Naming which book a quote comes from is pure recall — more reasoning tokens can't recover what wasn't pretrained.
3. **Allusion-ID is still the Chinese-model moat:** DeepSeek V3.2 (0.74) > GLM-5 (0.73) > MiniMax-2.1 / Opus 4.7 (0.64). But the gap narrowed a lot vs older rounds.
4. **Single-char cloze is an Anthropic clean sweep:** Opus-thinking 0.87 / Opus 0.84 / Sonnet 0.70 / DeepSeek 0.55.
5. **GLM-5 is the best open Chinese model overall** — top-3 on translate/punctuate/gloss/allusion, only weak on cloze.
6. **MiniMax M2.1 → M2.5 regressed on Classical Chinese** (0.473 → 0.436), mostly losing allusion-ID and cloze. Newer ≠ better here.

Known limitation: `translate` / `char-gloss` use chrF, which punishes valid paraphrase — an LLM judge is on the TODO. And the questions are sampled from public corpora most models have probably seen, so treat absolute numbers with a grain of salt; the *relative* ordering is the interesting bit.

Everything's open: questions + scorer + runner on GitHub, dataset + leaderboard on HF. PR your model's `results/<model>.json` and it shows up on the leaderboard.

- Code: https://github.com/gujilab/chinese-classical-bench
- Dataset: https://huggingface.co/datasets/gujilab/chinese-classical-bench
- Live leaderboard: https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard
- Source corpus (CC0): https://huggingface.co/datasets/gujilab/chinese-classical-corpus

Would love help filling in Llama-3.3, Yi-Lightning, ChatGLM, InternLM, GPT-4o, Gemini.
