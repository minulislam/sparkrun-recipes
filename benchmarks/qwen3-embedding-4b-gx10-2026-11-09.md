# Qwen/Qwen3-Embedding-4B on gx10-solo — 2026-11-09

Recipe: `recipes/qwen3-embedding-4b-tp1.yaml`
Container: `ghcr.io/spark-arena/dgx-vllm-eugr-nightly-tf5:2026092702` (loaded onto gx10-spark from gb10-spark, 2m30s)
Weights: 7.5 GiB safetensors, copied to gx10-spark over CX7 (10.99.10.11), Xet symlinks hardlinked first.

| Check | Result |
|---|---|
| Co-tenants before launch (gx10) | none; 116 GiB available |
| `sparkrun recipe validate` | valid |
| `sparkrun run --dry-run` | planner ok |
| Live launch `--no-follow` | container up; weights 47.7 s, graphs 40 s |
| `/v1/models` | `max_model_len` 32768 |
| `/v1/embeddings` ("hello world") | 200, 2560-dim, L2 norm 1.0 |
| sparkrun startup probe | reported failure (chat-token probe; not applicable to pooling runners) |
| Teardown | `sparkrun stop` on gx10-solo; no leftover containers on either node |

Not measured: latency / throughput (single request only).
