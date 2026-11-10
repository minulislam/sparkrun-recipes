#!/usr/bin/env python3
"""Task-mix decode benchmark (prose / code / JSON) for an OpenAI-compatible endpoint.

Why: the DGX Spark Handbook points out that with speculative decoding, code and
JSON can run ~2x faster than prose, so a single "tok/s" number is misleading.
This reports per-task single-stream speed (c=1) and aggregate speed at c=N.

Speed = completion_tokens / wall time of a streaming request, measured from the
first content token (decode tok/s), plus TTFT reported separately.

Usage:
  task_mix_bench.py --url http://10.10.20.11:8899 --model qwen36-35b-a3b \
      [--runs 3] [--concurrency 8] [--max-tokens 512] [--label NAME] [--out results.json]
"""
import argparse
import json
import statistics
import threading
import time
import urllib.request

PROMPTS = {
    "prose": "Write a long, vivid short story (at least 600 words) about a lighthouse keeper "
             "who discovers that the light is attracting something from the deep sea. "
             "Use rich description and dialogue.",
    "code": "Write a complete, well-commented Python module implementing an LRU cache with TTL "
            "expiry, thread safety, a decorator interface, and a full pytest test suite. "
            "Output only the code.",
    "json": "Generate a JSON array of 15 fictional employee records. Each record must have: id "
            "(int), name, email, department, title, salary (int), start_date (YYYY-MM-DD), "
            "skills (array of 4 strings), manager_id (int or null), and address (object with "
            "street, city, country, postcode). Output only valid JSON.",
}


def one_request(url, model, prompt, max_tokens, result):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    t_first = None
    tokens = None
    with urllib.request.urlopen(req, timeout=600) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("usage"):
                tokens = chunk["usage"]["completion_tokens"]
            for ch in chunk.get("choices", []):
                d = ch.get("delta", {})
                if t_first is None and (d.get("content") or d.get("reasoning_content") or d.get("reasoning")):
                    t_first = time.perf_counter()
    t_end = time.perf_counter()
    t_first = t_first or t_end
    result.update(
        tokens=tokens or 0,
        ttft=t_first - t0,
        wall=t_end - t0,
        decode_tps=((tokens or 1) - 1) / max(t_end - t_first, 1e-6),
    )


def run_batch(url, model, prompt, max_tokens, n):
    results = [dict() for _ in range(n)]
    threads = [threading.Thread(target=one_request, args=(url, model, prompt, max_tokens, r)) for r in results]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.perf_counter() - t0
    total = sum(r.get("tokens", 0) for r in results)
    return results, total / wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--label", default="")
    ap.add_argument("--out")
    a = ap.parse_args()

    # warmup
    run_batch(a.url, a.model, PROMPTS["code"], 64, 1)

    report = {"label": a.label, "model": a.model, "url": a.url, "max_tokens": a.max_tokens, "tasks": {}}
    for task, prompt in PROMPTS.items():
        c1 = []
        for _ in range(a.runs):
            (r,), _agg = run_batch(a.url, a.model, prompt, a.max_tokens, 1)
            c1.append(r)
        _, agg = run_batch(a.url, a.model, prompt, a.max_tokens, a.concurrency)
        report["tasks"][task] = {
            "c1_decode_tps_median": round(statistics.median(r["decode_tps"] for r in c1), 1),
            "c1_ttft_s_median": round(statistics.median(r["ttft"] for r in c1), 3),
            "c1_tokens": [r["tokens"] for r in c1],
            f"c{a.concurrency}_aggregate_tps": round(agg, 1),
        }
        print(f"[{a.label}] {task:5s} c=1 {report['tasks'][task]['c1_decode_tps_median']:7.1f} tok/s "
              f"(ttft {report['tasks'][task]['c1_ttft_s_median']}s)  "
              f"c={a.concurrency} {agg:7.1f} tok/s total", flush=True)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
