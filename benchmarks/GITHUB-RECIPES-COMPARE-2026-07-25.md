# GitHub sparkrun-recipe survey + compare (2026-07-25)

Question asked: does *our* GitHub have a sparkrun recipe repo, and if any repo
covers the same models, which version is best?

## 1. Our GitHub: no recipe repo

Authenticated as **rehanpatwary** (via the workstation's API token) and swept
all 26 repos plus a code search for "sparkrun": **zero hits**. The only
DGX-related repo, `rehanpatwary/dgx-agent`, holds a LiteLLM config and a
systemd unit — no recipes. Conclusion: the gb10-lab registry in
`/home/devops/workspace/code` (this repo) is the only registry we author, and
it lives solely on this workstation (no git remote configured). If it should
be on GitHub, that's a one-command push once a remote is created.

## 2. Third-party GitHub recipe repos already registered in sparkrun

`sparkrun registry list` carries four GitHub-hosted registries. Two overlap our
models: **eugr/spark-vllm-docker** (heavily) and **spark-arena
community-recipe-registry** (three Qwen3.6-35B variants). Registries updated
2026-07-25 before comparing.

## 3. Per-model comparison and verdicts

| Model | Ours | Theirs (eugr unless noted) | Verdict |
|---|---|---|---|
| DiffusionGemma-26B (same `nvidia/…-NVFP4` checkpoint) | pinned AEON image, 32K ctx cap, no parsers; **measured 358 tok/s c=1** | `vllm-node` self-built image + `mods/diffusiongemma`; 262K ctx; gemma4 parsers; `--diffusion-config '{"canvas_length":256}'`; thinking toggled via `--default-chat-template-kwargs '{"enable_thinking": false}'` + fixed chat template | **Ours** (validated on our stack; theirs needs their docker-compose builder). **Adopt from theirs**: the thinking toggle is the likely fix for our "thought"-marker leak, plus canvas_length + gemma4 parsers + 262K ctx — all flagged as next-boot experiments below. |
| Qwen3.6-35B | AEON heretic NVFP4, DFlash n=11, **82 tok/s c=1 measured**; batch twin 224 @ 8-way | (a) `nvidia/Qwen3.6-35B-A3B-NVFP4`, TP=2, MTP n=3, marlin MoE, fp8 KV; (b) `Qwen/…-FP8` + DFlash **n=15**, flash_attn; community: fp8-mtp, int4-dflash | **Ours** — single-node beats TP=2 for a ~22 GB model on GB10 (NCCL overhead, and TP=2 would consume both Sparks). **Adopt-maybe**: try n up to 15 (eugr runs 15 on FP8; AEON's n-sweep picked 11 for this body — test before changing). |
| Gemma-4-26B | AEON uncensored NVFP4 + DFlash, single node, **76.8 tok/s measured** | `nvidia/Gemma-4-26B-A4B-NVFP4`, TP=2 @ 0.7, MTP n=4 via `google/gemma-4-26B-A4B-it-assistant`, fp8 KV, instanttensor load | **Ours** — same-size model served on one node with better latency economics; theirs burns both Sparks. MTP-with-fp8-KV is a legit alternative lane if we ever want fp8 KV (DFlash forbids it). |
| Step-3.7-Flash | AEON abliterated NVFP4, TP=2, 65536 ctx placeholder, **untested** | `stepfun-ai/Step-3.7-Flash-NVFP4` (stock), TP=2, `mods/step-3.7-flash`, **262144 ctx**, 0.8 util | **Different models** (abliterated vs stock) — not interchangeable. **Adopt from theirs**: 262K context works on 2 Sparks → raise our placeholder when we get the TP=2 test window; their 0.8 util is a safer starting point than our 0.88. |
| Nemotron-3 | Nano-**Omni** NVFP4 (audio/video), **265 tok/s @ 8-way measured** | `nemotron-3-nano-nvfp4` / `-super-nvfp4` (text-only lines) | **Ours** — different model line; omni is the point. |
| Qwen3.6-27B, Gemma-31B, Gemma-12B | ours (validated) | — none | **Ours by default.** |

**Overall**: keep the gb10-lab registry as-is (every overlapping verdict went to
our versions, all live-measured on this hardware); adopt three eugr techniques
as experiments:

1. `--default-chat-template-kwargs '{"enable_thinking": false}'` (+ their fixed
   chat template) on DiffusionGemma → should kill the "thought"-marker leak.
   Flag support on our AEON 0.24 build must be boot-tested.
2. `--diffusion-config '{"canvas_length":256}'` on DiffusionGemma → tuning knob
   we don't set; test effect on the 358 tok/s baseline and on TTFT.
3. DFlash `num_speculative_tokens` sweep to 15 on Qwen-35B (eugr default) vs
   AEON's 11 — measure acceptance before adopting.

## 4. Parser question settled (was a conflict between sources)

- 2026-07-09 (our llm/ toolcall variants): `qwen3_xml` parses Qwen3.6's
  XML-style tool calls; `hermes` does NOT (raw text in content).
- AEON GitHub: documents `qwen3_coder`.
- eugr: uses `qwen3_xml`.
- **2026-07-25 live test** (35B, this registry's image): `qwen3_coder` returns
  `finish_reason: tool_calls` with correct structured arguments and separated
  reasoning. **Both `qwen3_xml` and `qwen3_coder` work; only `hermes` fails.**
  Registry standardizes on `qwen3_coder` (AEON-documented, freshest
  verification).

## 5. Filesystem consolidation (recipes authored by us)

Found and resolved to a single canonical copy — `recipes/` in this repo:

| Location | What | Action |
|---|---|---|
| `/home/devops/workspace/code/recipes/` (branch main) | pre-fix versions | fast-forwarded to the fixed branch — the sparkrun gb10-lab registry reads this path |
| `/home/devops/workspace/llm/recipes/qwen36-27b-aeon-toolcall.yaml` | co-location + tool-call variant (2026-07-09) | ported into repo as `recipes/qwen36-27b-aeon-colocate.yaml` (digest pin, dead env dropped, parser standardized); original deleted |
| `/home/devops/workspace/llm/recipes/qwen36-35b-a3b-heretic-nvfp4-toolcall.yaml` | 35B + parsers (2026-07-09) | redundant — base recipe now ships DFlash + parsers, batch variant ships drafterless + parsers; qwen3_xml evidence preserved here and in the colocate recipe; original deleted |
| `/home/devops/spark-vllm-docker/`, `/home/devops/workspace/llm/spark-vllm-docker/` | clones of eugr's third-party repo | left alone — not ours, and sparkrun keeps its own registry caches |
| `~/.cache/sparkrun/registries/*`, `~/.config/sparkrun/cache/*` | sparkrun-managed caches | left alone — regenerated by `sparkrun registry update` |
| `/tmp/sparkrun-ui-drafts/d_qrmko8cwmrwtdfb3.yaml` | someone's live UI-launched job on the worker | untouched (running workload, not ours) |
