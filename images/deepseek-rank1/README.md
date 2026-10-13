# spark-forge/vllm-dsv4-rank1

Local image behind `recipes/deepseek-v4-flash-0731-refusal-dial-tp2.yaml`. Upstream
publishes no image, so it was built here. It exists only on the two nodes.

| | |
|---|---|
| Tag | `spark-forge/vllm-dsv4-rank1:20261013` |
| Image ID | `976974ad7fd3` (18.9 GB), same on head and worker |
| Built | 2026-10-13 on `gb10-spark` |
| Source | `github.com/pocharlies/deepseek-v4-flash-rank1-refusal-projection` at commit `2e90d82119e47ffb9b7d919eeae35979ea686c83` |
| Dockerfile | `deploy/Dockerfile`, unmodified |
| Base | `ghcr.io/anemll/dspark-vllm-gx10:0.1.1` (image ID `3430d6614a8e`, vLLM `0.25.2.dev0+g752a3a504`) |
| Directions | `hf/refusal_dirs.safetensors`, 757,712 bytes, sha256 `665084995f0b8b82126e376b3aee8cdc97339b47f57c33a806320fe6b571cd21`, baked at `/opt/refusal/refusal_dirs.safetensors` |
| Build tests | all in-build checks passed (the CUDA-graph replay block is skipped at build time: no GPU in the build container) |

## Rebuild

```bash
git clone https://github.com/pocharlies/deepseek-v4-flash-rank1-refusal-projection && cd deepseek-v4-flash-rank1-refusal-projection
git checkout 2e90d82119e47ffb9b7d919eeae35979ea686c83
mkdir ctx && cp patches/0001-rank1-projection.patch hf/refusal_dirs.safetensors tools/test_refusal_per_request.py deploy/Dockerfile ctx/
docker build -t spark-forge/vllm-dsv4-rank1:<date> ctx
docker save spark-forge/vllm-dsv4-rank1:<date> | ssh devops@10.10.20.11 docker load
```

The image bakes `ENTRYPOINT ["vllm","serve"]`; the recipe clears it. The patch is inert
unless `VLLM_REFUSAL_DIRS` is set.
