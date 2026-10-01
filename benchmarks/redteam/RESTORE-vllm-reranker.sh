#!/bin/bash
# Restore the bge-reranker service on the worker (10.10.20.11).
# Stopped 2026-10-01 to give deepseek-v4-flash-vision-uncensored-tp2 (row 43) the
# pair to itself for its full-context run: the recipe warns that a co-tenant
# silently collapses its context. Config captured from `docker inspect` before stop.
ssh 10.10.20.11 'docker start vllm-reranker 2>/dev/null || docker run -d \
  --name vllm-reranker \
  --restart unless-stopped \
  --gpus all --ipc=host \
  -p 8085:8000 \
  -v /home/devops/.cache/huggingface:/root/.cache/huggingface \
  sparkrun-eugr-vllm-tf5:latest \
  vllm serve BAAI/bge-reranker-v2-m3 \
    --served-model-name bge-reranker-v2-m3 \
    --host 0.0.0.0 --port 8000 \
    --gpu-memory-utilization 0.10 --max-model-len 8192'
echo "check: curl -s http://10.10.20.11:8085/v1/models"
