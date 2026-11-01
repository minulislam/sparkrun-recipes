# Files

- [Abliteration & Refusal Evaluation](abliteration-and-refusal-eval.md) - The uncensored/abliterated recipe family on this pair — weight-baked abliteration vs. runtime refusal-projection — and the JailbreakBench-based refusal evaluation and full-context needle methodology used to characterize them.
- [Recipe Anatomy](recipe-anatomy.md) - The structure of a sparkrun v2 recipe YAML in this registry — identity (model/container/runtime), placement (min/max_nodes), readiness, the defaults block, the command template with its {placeholder} substitution, the env block, the executor_config entrypoint rule, and the memory-fit knobs.
- [Recipe Status Vocabulary](status-vocabulary.md) - The authoritative status ladder for recipes in this registry — lints, serves, verified, benchmarked, and unfit — and why collapsing them into one word produced irreconcilable coverage counts.
