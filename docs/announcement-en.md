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
| 1 | claude-opus-4-7 | 0.549 |
| 2 | claude-opus-4-7 (thinking) | 0.548 |
| 3 | claude-sonnet-4-6 | 0.486 |
| 4 | deepseek-3.2 | 0.483 |
| 5 | glm-5 | 0.479 |
| 6 | minimax-m2.1 | 0.477 |
| 7 | minimax-m2.5 | 0.446 |
| 8 | qwen3-coder-next | 0.434 |
| 9 | Qwen3.5-35B-A3B | 0.407 |
| 10 | claude-haiku-4-5 | 0.350 |

**Findings that surprised me:**

1. **The "Claude is bad at Classical Chinese" meme is a size problem, not a data problem.** Opus 4.7 tops 4 of 5 tasks; Sonnet 4.6 is 0.486, Haiku 4.5 is 0.350 — same family, same training data, ~57% spread.
2. **Thinking mode doesn't help overall** (0.548 vs 0.549) and *hurts* allusion-ID (0.63 vs 0.65). Naming which book a quote comes from is pure recall — more reasoning tokens can't recover what wasn't pretrained.
3. **DeepSeek's allusion-ID moat got tied by GLM-5:** DeepSeek V3.2 (0.74) = GLM-5 (0.74) > MiniMax-2.1 (0.66) > Opus 4.7 (0.65). Last round DeepSeek was alone at the top; not anymore.
4. **Single-char cloze is an Anthropic clean sweep:** Opus-thinking 0.87 / Opus 0.84 / Sonnet 0.70 / DeepSeek 0.55.
5. **GLM-5 (0.479) and MiniMax-2.1 (0.477) are effectively tied for best open Chinese model** — GLM-5 top-3 on translate/punctuate/gloss/allusion, only weak on cloze.
6. **MiniMax M2.1 → M2.5 regressed on Classical Chinese** (0.477 → 0.446), mostly losing allusion-ID and cloze. Newer ≠ better here.

Known limitation: `translate` / `char-gloss` use chrF, which punishes valid paraphrase — an LLM judge is on the TODO. And the questions are sampled from public corpora most models have probably seen, so treat absolute numbers with a grain of salt; the *relative* ordering is the interesting bit.

Everything's open: questions + scorer + runner on GitHub, dataset + leaderboard on HF. PR your model's `results/<model>.json` and it shows up on the leaderboard.

- Code: https://github.com/gujilab/chinese-classical-bench
- Dataset: https://huggingface.co/datasets/gujilab/chinese-classical-bench
- Live leaderboard: https://huggingface.co/spaces/gujilab/chinese-classical-bench-leaderboard
- Source corpus (CC0): https://huggingface.co/datasets/gujilab/chinese-classical-corpus

Would love help filling in Llama-3.3, Yi-Lightning, ChatGLM, InternLM, GPT-4o, Gemini.
