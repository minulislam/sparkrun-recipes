# Refusal / red-team eval harness

Two scripts for characterising a served model on this pair. Both talk plain
OpenAI-compatible HTTP, so they work against any sparkrun workload.

## `needle_context_test.py`
Needle-in-a-haystack retrieval plus prefill cost across context depths. Answers
"can this model actually use the context its recipe advertises", which a recipe's
`max_model_len` alone does not tell you. Prints a TSV and writes per-cell records.

## `run_refusal_eval.py`
Measures refusal versus compliance using **JailbreakBench JBB-Behaviors**: 100
harmful behaviours across 10 policy categories, plus 100 category-matched benign
controls.

Two design notes that matter:

1. **Both splits are scored.** Harmful compliance alone is not a useful number.
   An abliterated checkpoint should show high compliance on harmful *and* high
   compliance on benign. High harmful with low benign means the abliteration
   damaged the model rather than removing its refusals, and the benign controls
   are the only way to see that.
2. **`--pad-tokens` runs the same split at depth.** Run a split short, then run
   it padded, and diff the rates to test whether safety behaviour degrades with
   context length. That is the documented many-shot effect and it is the reason
   to care about full-context numbers for an uncensored model.

Prompts come from the published benchmark rather than being written here, so
results are comparable to the numbers in the JailbreakBench literature.

The grader is keyword refusal detection, the standard cheap method. It
over-counts refusals when a model declines in novel phrasing. Treat the
scorecard as a screen and read the raw JSONL for anything surprising.

Raw generations are gitignored on purpose.

## Usage
```
./needle_context_test.py --base http://10.10.20.10:8000/v1 --model NAME \
    --depths 2048,8192,32768,131072,262144 --out results/needle.jsonl

./run_refusal_eval.py --base http://10.10.20.10:8000/v1 --model NAME \
    --data <jbb>/data --split both --out results/refusal.jsonl
```
