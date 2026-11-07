# Provenance

Copied 2026-11-07 from the untracked `sparkrun/` folder inside
`~/workspace/llm/models/minimax/MiniMax-M3-2x-DGX-Spark-36-tok-s/`
(tonyd2wild's community repo; the `sparkrun/` folder was agent-authored,
never committed anywhere).

Status: **not verified, not in INDEX.md**. MiniMax-M3 facts from the same
effort (already in HISTORY.md): 428B 4-bit, 36 tok/s on the pair, 262K real
context ceiling vs 1M advertised. Port `minimax-m3-w4a16-gptq-b12x-nvfp4-eagle3.yaml`
into `recipes/` only after a verify pass; `mods/` + `sync-mods.sh` are its
support scripts.
