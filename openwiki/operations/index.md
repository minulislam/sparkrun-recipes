# Files

- [Memory, Placement & Known Pitfalls](memory-placement-and-pitfalls.md) - The unified-memory operating envelope on the GB10 pair and the recurring failure modes — gpu_memory_utilization bounds, head-node earlyoom pressure, co-tenant context shrink, the one-model-per-node co-residency limit, 0.3.10-era sparkrun defects (now on 0.4.2), and HF-cache corruption from root-owned containers.
- [Proxy & Gateway Routing (SparkRoute)](proxy-and-gateway-routing.md) - How the SparkRoute gateway on the head node's port 4000 routes model requests — proxy.yaml as the single source of bindings, the sync-based workflow, the binding schema, cold_start and placement policy, the unauthenticated admin API, and the operator-route vs recipe-binding name conflict.
