#!/usr/bin/env python3
"""Objective correctness eval: GSM8K (grade-school math) and MMLU (knowledge).

The refusal eval answers "will it answer". This answers "is the answer right",
which is the question that actually decides whether a model is useful. Both
tasks are auto-gradeable against a gold label, so there is no judge model and no
keyword heuristic in the loop.

Abliteration is known to cost capability, so the number that matters is this
model's score against the SAME benchmark on the un-abliterated base checkpoint.
Run it twice, once per endpoint, and diff.

Writes records incrementally so a killed run keeps its work.
"""
import argparse, json, random, re, sys, threading, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

LETTERS = "ABCD"

def load_gsm8k(path, n, seed):
    import pyarrow.parquet as pq
    rows = pq.read_table(path).to_pylist()
    random.Random(seed).shuffle(rows)
    out = []
    for r in rows[:n]:
        gold = r["answer"].split("####")[-1].strip().replace(",", "")
        out.append(dict(task="gsm8k", subject="math", question=r["question"], gold=gold))
    return out

def load_mmlu(path, n, seed):
    import pyarrow.parquet as pq
    rows = pq.read_table(path).to_pylist()
    random.Random(seed).shuffle(rows)
    out = []
    for r in rows[:n]:
        ch = list(r["choices"])
        q = r["question"] + "\n" + "\n".join(f"{LETTERS[i]}. {c}" for i, c in enumerate(ch))
        out.append(dict(task="mmlu", subject=r["subject"], question=q,
                        gold=LETTERS[int(r["answer"])]))
    return out

PROMPT = {
 "gsm8k": "{q}\n\nSolve this. End your reply with the final numeric answer on its own line as: ANSWER: <number>",
 # Answer FIRST for multiple choice. Asking for it last loses every verbose
 # response to the token cap: a 512-token run had 38/150 unparsed, all of them
 # finish_reason=length with ~2.4k chars of explanation and no answer reached.
 "mmlu":  "{q}\n\nBEGIN your reply with the answer on its own line as: ANSWER: <letter>\n"
          "Then, if you wish, explain briefly.",
}

def extract(task, text):
    if not text: return None
    m = re.findall(r"ANSWER:\s*([A-Da-d0-9\-\.,/ ]+)", text)
    # mmlu is instructed to lead with the answer; gsm8k to end with it.
    cand = (m[0] if task == "mmlu" else m[-1]).strip() if m else None
    if task == "mmlu":
        if cand:
            c = re.search(r"[A-Da-d]", cand)
            if c: return c.group(0).upper()
        # fall back to a lone trailing letter
        t = re.findall(r"\b([A-D])\b", text.strip()[-80:])
        return t[-1] if t else None
    # gsm8k: last number anywhere in the tail if no tagged answer
    src = cand if cand else text[-160:]
    nums = re.findall(r"-?\d[\d,]*\.?\d*", src.replace(" ", ""))
    if not nums: return None
    v = nums[-1].replace(",", "").rstrip(".")
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return None

def norm_gold(task, g):
    if task == "mmlu": return g
    try:
        f = float(g)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return g

def chat(base, model, prompt, max_tokens, timeout, no_think):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0}
    if no_think:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        # Only Qwen3-style templates accept enable_thinking. Gemma / Nemotron /
        # DeepSeek templates 400 on it, so drop the kwarg and retry once.
        if e.code == 400 and "chat_template_kwargs" in json.dumps(body):
            body.pop("chat_template_kwargs", None)
            req2 = urllib.request.Request(base.rstrip("/") + "/chat/completions",
                                          data=json.dumps(body).encode(),
                                          headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req2, timeout=timeout) as r:
                d = json.load(r)
        else:
            raise
    msg = d["choices"][0]["message"]
    txt = msg.get("content") or ""
    think = msg.get("reasoning") or msg.get("reasoning_content") or ""
    if "</think>" in txt:
        pre, txt = txt.split("</think>", 1); think = (think + " " + pre).strip()
    return txt.strip(), think, d.get("usage", {}), time.time() - t0, \
           d["choices"][0].get("finish_reason")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--gsm8k"); ap.add_argument("--mmlu")
    ap.add_argument("-n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--no-think", action="store_true")
    ap.add_argument("--out", default="correctness.jsonl")
    a = ap.parse_args()

    items = []
    if a.gsm8k: items += load_gsm8k(a.gsm8k, a.n, a.seed)
    if a.mmlu:  items += load_mmlu(a.mmlu, a.n, a.seed)
    if not items: sys.exit("need --gsm8k and/or --mmlu")

    tally = defaultdict(lambda: defaultdict(int))
    lock, done, t0 = threading.Lock(), [0], time.time()
    fh = open(a.out, "w", buffering=1)

    def work(it):
        p = PROMPT[it["task"]].format(q=it["question"])
        try:
            txt, think, usage, el, fin = chat(a.base, a.model, p, a.max_tokens,
                                              a.timeout, a.no_think)
            got = extract(it["task"], txt) or extract(it["task"], think)
            gold = norm_gold(it["task"], it["gold"])
            ok = (got is not None and got == gold)
            return dict(task=it["task"], subject=it["subject"], gold=gold, got=got,
                        correct=ok, finish=fin, wall_s=round(el, 2),
                        completion_tokens=usage.get("completion_tokens"),
                        answer_chars=len(txt), thinking_chars=len(think),
                        tail=txt[-180:])
        except Exception as e:
            return dict(task=it["task"], subject=it["subject"], gold=it["gold"],
                        got=None, correct=False, error=f"{type(e).__name__}: {str(e)[:140]}")

    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        for fut in as_completed([ex.submit(work, it) for it in items]):
            r = fut.result()
            with lock:
                done[0] += 1
                fh.write(json.dumps(r) + "\n")
                tally[r["task"]]["n"] += 1
                tally[r["task"]]["ok"] += 1 if r["correct"] else 0
                if r.get("error"): tally[r["task"]]["err"] += 1
                if r["got"] is None and not r.get("error"): tally[r["task"]]["unparsed"] += 1
                print(f"  [{done[0]}/{len(items)}] {r['task']:<6} {r['subject'][:24]:<24} "
                      f"gold={str(r['gold'])[:8]:<8} got={str(r['got'])[:8]:<8} "
                      f"{'OK' if r['correct'] else 'x'}", flush=True)
    fh.close()

    print("\n=== CORRECTNESS ===")
    print(f"model: {a.model}  no_think: {a.no_think}  n per task: {a.n}  "
          f"seed: {a.seed}  wall: {time.time()-t0:.0f}s")
    for task in ("gsm8k", "mmlu"):
        t = tally.get(task)
        if not t: continue
        n, ok = t["n"], t["ok"]
        print(f"  {task:<7} {ok}/{n} = {100*ok/n:.1f}%   "
              f"unparsed={t.get('unparsed',0)}  errors={t.get('err',0)}")
    print(f"\nrecords -> {a.out}")

if __name__ == "__main__":
    main()
