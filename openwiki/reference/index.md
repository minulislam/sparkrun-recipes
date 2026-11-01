# Files

- [Container Images & Provenance](images-and-provenance.md) - The container-image selection order and provenance rules for recipes — the spark-arena-first tier list, the immutable-tag policy and why dated tags beat digest pins here, and the locally built deepseek-rank1 runtime-abliteration image.
- [Model Inventory & Weight Safety](model-inventory-and-weights.md) - What MODELS.md records about which checkpoints are complete, partial, or stubs on each node and which recipes use them, and the standing rules for handling weights safely (back up before delete, deletion is the operator's call, never hf cache prune without --dry-run).
