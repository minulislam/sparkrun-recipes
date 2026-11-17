# Files

- [Memory, Placement & Known Pitfalls](memory-placement-and-pitfalls.md) - The unified-memory operating envelope on the GB10 pair and the recurring failure modes — gpu_memory_utilization bounds, head-node earlyoom pressure, co-tenant context shrink, the one-model-per-node co-residency limit, 0.3.10-era sparkrun defects (now on 0.4.2), and HF-cache corruption from root-owned containers.
- [Gateway Routing (spark-loader)](proxy-and-gateway-routing.md) - How requests reach served models on the head node — spark-loader on :4000 loads catalog recipes on demand and forwards to LiteLLM on 127.0.0.1:4001; the embedder and reranker run outside sparkrun; SparkRoute was removed on 2026-11-17.
