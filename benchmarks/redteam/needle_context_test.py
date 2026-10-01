#!/usr/bin/env python3
"""Needle-in-a-haystack retrieval + latency across context depths.

Measures whether a served model can actually use the context length its recipe
claims, and what prefill costs at depth. Writes a TSV scorecard to stdout and
raw records to --out.

Usage:
  needle_context_test.py --base http://10.10.20.10:8000/v1 --model NAME \
      --depths 2048,8192,32768,131072,262144 --positions 0.1,0.5,0.9
"""
import argparse, json, random, time, urllib.request, sys

FILLER = (
    "The archive catalogues routine maintenance notes from the orbital station. "
    "Pressure readings held steady through the cycle. The crew logged no anomalies. "
    "Supply manifests were reconciled against the quartermaster ledger. "
)
NEEDLE = "The calibration passphrase for bay {n} is {code}."
QUESTION = ("Read the document above. What is the calibration passphrase for bay {n}? "
            "Reply with only the passphrase, nothing else.")

def build(depth_tokens, position, bay, code, chars_per_tok=3.6):
    target = int(depth_tokens * chars_per_tok)
    reps = max(1, target // len(FILLER))
    body = FILLER * reps
    needle = NEEDLE.format(n=bay, code=code)
    cut = int(len(body) * position)
    return body[:cut] + "\n\n" + needle + "\n\n" + body[cut:]

def chat(base, model, prompt, max_tokens, timeout):
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps({"model": model,
                         "messages": [{"role": "user", "content": prompt}],
                         "max_tokens": max_tokens, "temperature": 0}).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    el = time.time() - t0
    txt = d["choices"][0]["message"]["content"]
    if "</think>" in txt:
        txt = txt.split("</think>")[-1]
    return txt.strip(), d.get("usage", {}), el, d["choices"][0].get("finish_reason")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--depths", default="2048,8192,32768,131072")
    ap.add_argument("--positions", default="0.1,0.5,0.9")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", default="needle_records.jsonl")
    a = ap.parse_args()
    rng = random.Random(1234)
    depths = [int(x) for x in a.depths.split(",")]
    positions = [float(x) for x in a.positions.split(",")]
    print("depth\tpos\thit\tprompt_tok\twall_s\tprefill_tok_s\tfinish")
    recs = []
    for d in depths:
        for p in positions:
            bay = rng.randint(100, 999)
            code = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
            prompt = build(d, p, bay, code) + "\n\n" + QUESTION.format(n=bay)
            try:
                txt, usage, el, fin = chat(a.base, a.model, prompt, a.max_tokens, a.timeout)
                hit = code.lower() in txt.lower()
                pt = usage.get("prompt_tokens", 0)
                print(f"{d}\t{p}\t{'YES' if hit else 'no'}\t{pt}\t{el:.1f}\t{pt/el if el else 0:.0f}\t{fin}")
                recs.append(dict(depth=d, pos=p, hit=hit, prompt_tokens=pt, wall_s=round(el,2),
                                 finish=fin, expected=code, got=txt[:200]))
            except Exception as e:
                print(f"{d}\t{p}\tERR\t-\t-\t-\t{type(e).__name__}")
                recs.append(dict(depth=d, pos=p, hit=None, error=f"{type(e).__name__}: {e}"))
            sys.stdout.flush()
    with open(a.out, "w") as f:
        for r in recs: f.write(json.dumps(r) + "\n")
    ok = [r for r in recs if r.get("hit") is True]
    print(f"\nretrieval: {len(ok)}/{len(recs)} cells correct; records -> {a.out}")

if __name__ == "__main__":
    main()
