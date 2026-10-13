# Credits

This recipe stands on other people's work. In order of how much of the result they own:

## Z.ai — the model
**[zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash)** (released 2026-08-26): 320B-total / 18B-active natively-multimodal MoE — 34 Kimi-Delta linear-attention (KDA) layers + 11 DeepSeek-sparse-attention (DSA) MLA layers with a kpool top-k lightning indexer, NoPE MLA, mHC hyper-connections, an in-checkpoint MTP head, and a BF16 vision tower. Everything here is about serving *their* model unchanged. The 2026-08-26 `chat_template.jinja` sync that turns multimodal input on (the previous template refused images) is theirs too.

## LibertAI — the NVFP4 quant and the day-0 image pointer
**[LibertAIDAI/GLM-5.3-Flash-NVFP4](https://huggingface.co/LibertAIDAI/GLM-5.3-Flash-NVFP4)**: weight-only NVFP4 (E2M1, group 16, FP8 block scales) on the routed-expert FFNs — 97 % of the parameters — with both attention families, the vision tower, shared experts, routers, dense MLPs, embeddings and norms kept in BF16. 598.5 GiB → ~181 GiB (−70 %), per-expert cosine ≈ 0.9967. Produced with NVIDIA ModelOpt 0.45 via a memory-frugal shard-streaming pass, calibration-free. Their model card is also where the `vllm/vllm-openai:glm53-flash-*` day-0 image and the GB10 `--moe-backend marlin --enforce-eager` fallback come from, and they synced the fixed chat template within hours of Z.ai. This checkpoint is what we serve, byte-for-byte (all 120 shards hash-verified against upstream).

## Abliteration — LibertAI body + Dealign L15–45 o_proj (0731 early-layer spare)

The "-Abliterated" checkpoint is **[drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45](https://huggingface.co/drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45)** (method + scripts: [GitHub](https://github.com/drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45)). Repo id is **ablit-l15-43-mtp-l45** (L15–43 + MTP L45; L44 stock).

We byte-copied **[dealignai/GLM-5.3-Flash-UNCENSORED-NVFP4](https://huggingface.co/dealignai/GLM-5.3-Flash-UNCENSORED-NVFP4)** `self_attn.o_proj` for **L15–45** (MTP included) onto LibertAI shards. **L0–14 stay stock** — that sparing is the [0731 DSpark](https://huggingface.co/drowzeys/keys-DeepSeekV4-Flash-GA-0731-Dspark-Abliterated-Anchored-Tensors) lesson. Residual refusal on GLM-5.3 lived late + MTP; a Blackfrost-V projection never passed 9/32.

**[Blackfrost-Research/GLM-5.3-Flash-DERISKED-NVFP4](https://huggingface.co/Blackfrost-Research/GLM-5.3-Flash-DERISKED-NVFP4)** is credited as a **measured direction reference**. We did not ship their NVFP4 or their L2–44 / MTP-BF16 mask.

## The serving stack

- **vLLM** ([PR #53906](https://github.com/vllm-project/vllm/pull/53906) authors) — `glm5_next` support and the day-0 `vllm/vllm-openai:glm53-flash-arm64-cu130` image (nightly `0.1.dev20051+g487ecf187`, FlashInfer 0.6.17, torch 2.13+cu130).
- **[tonyd2wild/GLM-5.3-Flash-NVFP4-262K-2x-DGX-Spark](https://github.com/tonyd2wild/GLM-5.3-Flash-NVFP4-262K-2x-DGX-Spark)** (Knox / Claude for @tonyd2wild, published the same evening) — the first public 2×Spark GLM-5.3 recipe. Two of their fixes are applied here verbatim with attribution: PDL gated off on SM12x (their v6), and the indexer top-k `-1` init + pool-id clamp (`patch_v7.py`). Their `--block-size` finding (kpool storage must tile by 64 for DeepGEMM's arch-12 fp8 paged-MQA) is the same wall we hit. They took the SM90-backend route at the NoPE fork; this repo is the packed-fp8 / trtllm route they documented as their un-built "Phase 3". **barrydeen**'s independent recipe (via tonyd2wild's credits) established GMU 0.85 as the floor.
- **Luke Alonso — [b12x](https://pypi.org/project/b12x/)** 1.2.6: the DGX Spark / RTX 6000-focused CuTeDSL + Triton kernel library. The `nvfp4_ds_mla` reader/writer (368-B `KV_FP8_ROPE=1` record) used for the NVFP4 KV cache is his `b12x.attention.sparse_mla` / `_shared.mla.kv_cache`.
- **eugr — `eugr/spark-vllm-b12x`** nightly tree: the `B12X_MLA_SPARSE` vLLM backend, `mla_cache_format.py`, and the `nvfp4_ds_mla` gate sites that this repo ports onto the glm53 image.
- **DeepGEMM `nv_dev` branch** (commit 8b1392b, v2.6.1) — native `sm120_*` MQA-logits / paged-MQA kernels, built inside the image (see `docs/BUILD-DEEPGEMM.md`). The vendored DeepGEMM in the day-0 image also carries arch-12 paths; nv_dev is what we validated with.
- **FlashInfer** — SM120 sparse-MLA (`trtllm_batch_decode_with_kv_cache_mla`, DSV3.2 dispatch table) and the autotuner.
- **NVIDIA ModelOpt** (quant format), **Marlin** (weight-only FP4 MoE on sm_121), **TileLang** (mHC kernels).

## Our own prior work this builds on
The zero-RoPE shim is the mirror image of our DSpark top-k padding fix (FlashInfer SM120 topk instantiation tables), and the NVFP4-MLA-KV lineage goes back to our GLM-5.2 `nvfp4_ds_mla` mod on sm_121a (2026-06). Recipe deployed and debugged by Claude for @drowzeys on a 5×DGX Spark GB10 fleet.
