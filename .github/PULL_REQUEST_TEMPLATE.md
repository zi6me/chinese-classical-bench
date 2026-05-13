<!-- For "add a model result" PRs, fill this in. For other changes, delete it. -->

## Adding a model: `<model-id>`

- **Endpoint**: <vLLM / OpenAI / Anthropic-compatible / DeepSeek / ...>
- **Decode params**: temperature=0.0, max_tokens=..., <anything non-default>
- **System prompt**: default / custom (paste it)
- **Reasoning / thinking mode**: no / yes (id suffixed accordingly)
- **Notes**: <quantization, provider, anything that affects reproducibility>

### Checklist
- [ ] `results/<model-id>.json` included, with `items[].prediction` kept (not stripped)
- [ ] All 5 tasks present, 100 items each
- [ ] `leaderboard.md` regenerated with `python scripts/aggregate.py --out leaderboard.md`
- [ ] CI green
