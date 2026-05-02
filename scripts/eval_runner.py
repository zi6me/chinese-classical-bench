"""Eval runner: query an OpenAI-compatible endpoint (vLLM / Anthropic / OpenAI)
on all 5 benchmark tasks and compute per-task metrics.

Usage:
  python eval_runner.py --model Qwen/Qwen3-7B-Instruct \
      --base-url http://localhost:8000/v1 --api-key EMPTY

  python eval_runner.py --model claude-sonnet-4-5 \
      --base-url https://api.anthropic.com/v1 --api-key $ANTHROPIC_API_KEY \
      --tasks translate fill-in
"""

import argparse
import concurrent.futures as cf
import json
import statistics
import sys
import time
from pathlib import Path

# Make stdout line-buffered so progress lines flush when redirected
sys.stdout.reconfigure(line_buffering=True)

import urllib.request
import urllib.error

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from scorers import score  # noqa: E402

DATA_DIR = REPO / "data"
RESULTS_DIR = REPO / "results"

TASK_FILES = {
    "translate": "translate.jsonl",
    "punctuate": "punctuate.jsonl",
    "char-gloss": "char_gloss.jsonl",
    "idiom-source": "idiom_source.jsonl",
    "fill-in": "fill_in.jsonl",
}

SYSTEM_PROMPT = (
    "你是中国古典文献专家。回答力求简洁准确，不要解释，不要附加多余文字。"
)


def load_task(task: str) -> list[dict]:
    path = DATA_DIR / TASK_FILES[task]
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def make_prompt(rec: dict) -> str:
    return f"{rec['instruction']}\n\n{rec['input']}"


def chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: int = 60,
    max_tokens: int = 512,
    extra_headers: dict | None = None,
) -> str:
    """Call OpenAI-compatible /chat/completions, return assistant content."""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def run_task(
    task: str,
    base_url: str,
    api_key: str,
    model: str,
    concurrency: int,
    limit: int | None,
    extra_headers: dict | None = None,
) -> dict:
    records = load_task(task)
    if limit:
        records = records[:limit]
    print(f"[{task}] {len(records)} questions, concurrency={concurrency}")

    preds = [None] * len(records)
    errors = 0
    t0 = time.time()

    def worker(i: int, rec: dict):
        try:
            prompt = make_prompt(rec)
            return i, chat_completion(
                base_url, api_key, model, prompt,
                extra_headers=extra_headers,
            ), None
        except Exception as e:
            return i, "", str(e)

    with cf.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [pool.submit(worker, i, r) for i, r in enumerate(records)]
        done = 0
        for fut in cf.as_completed(futs):
            i, pred, err = fut.result()
            preds[i] = pred
            if err:
                errors += 1
                if errors <= 3:
                    print(f"  [err] q{i}: {err}", file=sys.stderr)
            done += 1
            if done % 25 == 0 or done == len(records):
                print(f"  {done}/{len(records)}  ({time.time()-t0:.0f}s, {errors} err)")

    # score
    items = []
    metric_acc: dict[str, list[float]] = {}
    for rec, pred in zip(records, preds):
        s = score(rec, pred)
        for k, v in s.items():
            metric_acc.setdefault(k, []).append(v)
        items.append(
            {
                "id": rec["id"],
                "input": rec["input"],
                "reference": rec["reference"],
                "prediction": pred,
                "scores": s,
            }
        )

    summary = {
        m: round(statistics.fmean(v), 4) for m, v in metric_acc.items()
    }
    return {
        "task": task,
        "n": len(records),
        "errors": errors,
        "elapsed_sec": round(time.time() - t0, 1),
        "summary": summary,
        "items": items,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="model id (e.g., Qwen/Qwen3-7B-Instruct)")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument(
        "--tasks",
        nargs="*",
        default=list(TASK_FILES.keys()),
        choices=list(TASK_FILES.keys()),
    )
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None,
                    help="limit questions per task (debug)")
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--header", action="append", default=[],
                    help="extra header K:V (repeat). e.g. --header 'x-skip-sanitize:true'")
    args = ap.parse_args()

    extra_headers = {}
    for h in args.header:
        k, _, v = h.partition(":")
        if k.strip() and v.strip():
            extra_headers[k.strip()] = v.strip()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = args.model.replace("/", "_")
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{safe_name}.json"

    all_results = {
        "model": args.model,
        "base_url": args.base_url,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tasks": {},
    }

    for task in args.tasks:
        result = run_task(
            task=task,
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            concurrency=args.concurrency,
            limit=args.limit,
            extra_headers=extra_headers or None,
        )
        all_results["tasks"][task] = result
        print(f"  ⇒ {task} summary: {result['summary']}")

    out_path.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nwrote → {out_path.relative_to(REPO)}")
    print("\n=== summary ===")
    for t, r in all_results["tasks"].items():
        print(f"  {t:<14}  {r['summary']}  (errors={r['errors']})")


if __name__ == "__main__":
    main()
