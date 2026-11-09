---
type: concept
title: Recipe Status Vocabulary
description: The authoritative status ladder for recipes in this registry — lints, serves, verified, benchmarked, and unfit — and why collapsing them into one word produced irreconcilable coverage counts.
tags: [vocabulary, status, verified, benchmarked, conventions]
sources:
  - id: openwiki-source-39c3295efc089133e87a9c80
    resource: repo://CONTEXT.md
  - id: openwiki-source-382af0b12a087a97295aa93b
    resource: repo://HISTORY.md
  - id: openwiki-source-d731ee870c7c4da596ac3b0a
    resource: repo://INDEX.md
generated: { by: "claude-code", at: "2026-11-08T21:00:19.321Z" }
verified:
  - by: openwiki/0.7.2
    at: 2026-11-08T21:00:19.321Z
---

# Recipe Status Vocabulary

This registry reports a recipe's status only **at the bar it has actually
reached**. The terms below are defined in `CONTEXT.md` and are load-bearing:
every status line in `INDEX.md`, every recipe header, and every coverage count
is meant in exactly these senses. The vocabulary exists because the repo once
used the single word "verified" for at least three different bars, which is how
a coverage count can produce several irreconcilable answers.

## The ladder

The states form a strict ladder of increasing confidence:

| Term | What it means | What it does **not** mean |
|---|---|---|
| **Recipe** | A YAML file in `recipes/` that fully specifies one served model — checkpoint, container, runtime flags, fit. | Not a "config", "manifest", or "profile". |
| **Lints** | Passes `sparkrun recipe validate`. A statement about the *file*. | Proves nothing about whether anything can serve. |
| **Serves** | The engine reached ready and the endpoint accepts requests. | Not "works" — a recipe can serve and still return garbage. |
| **Verified** | The model **answered a request** on this cluster. The authoritative bar. | A dry run or clean lint never qualifies. |
| **Benchmarked** | Has measured numbers from a harness run, recorded in `benchmarks/`. | — |
| **Unfit** | Serves on this pair but cannot be used — returns incoherent output, or otherwise fails to be usable. | — |

## Why the distinction is strict

Three properties make the ladder meaningful:

- **Lints, serves, and verified are genuinely different claims.** A file can
  lint and never serve; it can serve and still emit garbage (which is exactly
  the `unfit` case). Only an answered request clears the `verified` bar, which
  is why that bar is owned by a dedicated procedure
  (`.claude/skills/verify/SKILL.md`), not by a dry run.
- **Benchmarked is strictly stronger than verified.** Every benchmarked recipe
  is verified, but not every verified recipe is benchmarked — benchmarking adds
  measured numbers on top of a proven answer.
- **Unfit is a real, recorded outcome, not an absence of testing.** A model that
  serves but returns incoherent output is marked unfit so it is not mistaken for
  merely untested.

Because each word maps to one bar, a coverage statement ("N recipes verified")
has a single defensible meaning, and status can be reported honestly at whatever
level the evidence supports.

## The path to the answer is part of the record

`Verified` requires an answered request, but *how* the request reached the model
is recorded too, because the paths fail differently. The 2026-11-08 pooling
pair shows both forms: row 65 (`qwen3-embedding-4b-tp1`) is **verified through
the SparkRoute gateway** (`/v1/embeddings` 200 with a 2560-dim vector), while
row 66 (`qwen3-reranker-4b-tp1`) is **verified direct** against the container's
`/v1/rerank` — the gateway has no rerank route, so gateway-path verification is
impossible for it. Both clear the `verified` bar; the annotation tells a later
operator which access path was actually proven.

## Related

- [Launching & Verifying a Recipe](../workflows/launching-and-verifying.md)
- [Benchmarking & Context Verification](../workflows/benchmarking.md)
