# spark-forge / sparkrun-recipes — project history

First-to-last record of the work on this repo and the two-node DGX Spark pair it
serves (head `gb10-spark` 10.10.20.10, worker `gx10-spark` 10.10.20.11, both
GB10 with about 121 GiB unified memory).

**Compiled 2026-10-13** from four sources: this repo's git log (50 commits), 52
Claude Code session transcripts dated 2026-07-17 to 2026-10-13, the daily notes
under `.remember/`, and the memory notes of earlier sessions. Nothing here was
re-measured while compiling; every number is quoted from the session or commit
that produced it. `MODELS.md` and `INDEX.md` hold the current state; this file
holds how it got there.

**Reading the dates.** Commit dates are local time (UTC+6). Session timestamps
are UTC, so late-evening work can appear one day earlier in a session than in
the commit or file name it produced (for example `FLEET-2026-09-27.md` was
mostly run on 09-26 UTC). Where a commit exists, its date is used.

**Keeping this file current.** Append a dated section for each new block of
work. Do not rewrite old sections; if an old claim turns out wrong, add
"Corrected <date>: …" under it. Vocabulary follows `CONTEXT.md` (*verified*
means the model answered a request on this pair).

## Phases at a glance

| Phase | Dates | What happened |
|---|---|---|
| 0 | before 2026-07-08 | Cluster built and operated from a separate ops repo; RoCE fabric verified |
| 1 | 07-08 to 07-25 | `gb10-lab` registry: 8, then 11 AEON NVFP4 recipes, first benchmarks and fixes |
| 2 | 08-21 to 09-07 | Published to GitHub, renamed `spark-forge`, repo moved, 28 MiaAI-Lab recipes imported |
| 3 | 09-10 to 09-20 | Refusal-dial, MiniMax-M3, five orcarouter uncensored recipes; two-node NCCL failures begin |
| 4 | 09-25 to 09-29 | DeepSeek at 1M context, fleet benchmark, image pinning, RoCE root cause fixed, NAS backup |
| 5 | 09-30 to 10-07 | Dead recipes purged, uncensored models measured and ranked, image policy, `MODELS.md`, `CONTEXT.md` |
| 6 | 10-07 to 10-13 | Pre-push gate designed (not built), live inventory recheck, five more recipes removed |

## Recipe count over time

| Date | Count | Change |
|---|---|---|
| 2026-07-08 | 8 | Initial commit `fbd2c7e` |
| 2026-07-25 | 11 | DiffusionGemma, batch and colocate variants |
| 2026-09-07 | 40 | 28 MiaAI-Lab recipes imported (README of `3bcabaa` states 40) |
| 2026-09-10 | 39 | Two dead recipes removed, refusal-dial added |
| 2026-09-17 | 40 | `minimax-m3-v0-nvfp4-reap25` added |
| 2026-09-20 | 45 | Five orcarouter recipes |
| 2026-09-26 | 45 | DeepSeek `-ep2` added, `exllamav3` recipe retired |
| 2026-09-27 | 55 | Coder profile, Flash-Next base, MiniMax Atlas EP2, seven registry copies |
| 2026-09-28 | 54 | `minimax-m2.5-awq-tp2` removed |
| 2026-10-01 | 53 | Three removed, two adopted from registries |
| 2026-10-02 | 54 | `glm-5.3-flash-exl3-1x-spark` recorded |
| 2026-10-06 | 53 | `glm-5.2-nvfp4-aqlm-tp3` deleted (needs three nodes) |
| 2026-10-13 | 48 | Five recipes with vanished model sources removed |

Counts for 09-27 and 09-28 are derived from the commits, not quoted from a
session.

## Timeline

### Phase 0 — before the repo (to 2026-07-08)

- The pair was first run from a separate ops repo (`nvidia-dgx-spark-cluster`)
  with vLLM on Ray, SGLang, TRT-LLM, LiteLLM, Ollama and LM Studio. The user's
  stated strategy from 2026-06-03: vLLM on the pair for heavy work, Ollama and
  LM Studio kept on every device.
- 2026-06-03: a `qwen3-1.7b-vllm --tp 2` run with `NCCL_DEBUG` confirmed that
  two-node inference uses the ConnectX-7 links over RoCEv2, not the management
  LAN.

### Phase 1 — `gb10-lab`: first recipes, first benchmarks (07-08 to 07-25)

**2026-07-08** — Repo created at `~/workspace/code` as sparkrun registry
`gb10-lab` with 8 NVFP4 recipes validated on the head (`fbd2c7e`). The cluster
was then called `default` in sparkrun 0.2.39.

**2026-07-18** — First head-to-head benchmark (`49b9e30`) and AEON-7 root-cause
analysis (`f1ccde6`).
- Five of eight recipes ran. Qwen3.6-27B, the "flagship", decoded at 9.5 tok/s
  against a claimed ~50. Gemma-4-26B AEON 76.8 tok/s, Qwen3.6-35B 43.4,
  Nemotron-3-Nano-Omni 72.7, Gemma-4-12B 21.7.
- Causes found in AEON-7's own repos: DFlash was commented out in both Qwen
  recipes; `VLLM_NVFP4_GEMM_BACKEND` was removed in vLLM 0.24.0 so the env
  block did nothing; Gemma-4-31B DECKARD is `NVFP4_AWQ` and only boots on
  AEON's dedicated container.
- sparkrun was found to re-pull a cached `:latest` image and block the launch.

**2026-07-25** — Fixes applied and validated (`3c6bda4`), variants and docs
(`1e3bf40`), merged to `main`.
- Qwen3.6-27B 9.5 → 23.7 tok/s, Qwen3.6-35B 43.4 → 82, Gemma-4-31B unbootable
  → 31.3. New DiffusionGemma recipe at about 358 tok/s single-stream.
- DFlash raised single-stream speed but lowered the 35B's 8-way throughput
  (224 → 149), which is why the drafterless `-batch` twin exists.
- Serve containers run `HF_HUB_OFFLINE=1`, so drafters must be cached on the
  node before launch.
- Added `qwen36-35b-a3b-heretic-nvfp4-batch`, `qwen36-27b-aeon-colocate`,
  `INDEX.md`, `benchmarks/README.md`, `VALIDATION-2026-07-25.md` and
  `GITHUB-RECIPES-COMPARE-2026-07-25.md`. Tool-call test: `qwen3_coder` and
  `qwen3_xml` work, `hermes` does not.

**2026-07-29 to 07-31** — `sparkarena/Minimax-M3-v0-NVFP4-REAP25` (175 GB)
downloaded on the head and synced to the worker. No recipe yet.

### Phase 2 — published, renamed, imported (08-21 to 09-07)

**2026-08-21** — Repo pushed to `github.com:minulislam/sparkrun-recipes`
(`5b68114`, `dd18e41`); registry renamed `gb10-lab` → `spark-forge` (`94adf52`).
The name mismatch between repo and registry is deliberate.

**2026-08-22** — Directory renamed `~/workspace/code` →
`~/workspace/sparkrun-recipes`; registry config rewired; usage note moved into
`benchmarks/` (`2e92c63`). Same day, outside the repo: stale AI-Q services
removed, AINode repaired and moved to port 8200, dashboards made user units.

**2026-08-25** — Synology NAS exported over NFS and mounted at
`/mnt/nas/dgx-spark` on both nodes (needs Squash "Map all users to admin").
sparkrun-ui dashboard fixed with a compose override.

**2026-08-30** — A MiniMax-M3 two-node recipe was written in a separate repo
(`projects/MiniMax-M3-2x-DGX-Spark-36-tok-s/sparkrun/`), never committed here
and never launched in that session.

**2026-09-01 / 09-02** — sparkrun purged and reinstalled from PyPI (it had been
a git `develop-next` install). This wiped every cluster definition; `spark-forge`
was re-added as a `file://` registry. The cluster has been named `dgx-pair`
since then.

**2026-09-07** — 28 MiaAI-Lab recipes imported (`27d55a3`, `9f26db1`,
`3bcabaa`); registry at 40 recipes. Both 200G links measured at about 104 Gbps
each with `ib_write_bw`.

### Phase 3 — uncensored lane and two-node trouble (09-10 to 09-20)

**2026-09-10 / 09-11** — Two dead recipes removed (`6299609`). Refusal-dial
recipe added from the pocharlies repo (`158c94d`) and set to λ=1 (`8789003`).
- Lesson learned the hard way: the `file://` registry cache is a git clone of
  `main`. A change on a branch or in the working tree is invisible to
  `sparkrun registry update`.
- User rule on the fabric: use `10.99.11.10` / `10.99.11.11` for inference,
  inter-node jobs and weight copies.

**2026-09-16 / 09-17** — Refusal-dial made to launch (`864b370`, `a6a9e92`,
`9f276a3`); `minimax-m3-v0-nvfp4-reap25` added (`e1674cb`).
- The dial image ignores `VLLM_REFUSAL_LAMBDA_INIT`; only the `post_exec` call
  to `/admin/refusal_lambda` turns ablation on, and `--no-follow` skips
  `post_exec`.
- An `apt upgrade` on the worker left the NVIDIA userspace ahead of the loaded
  kernel module; every GPU container failed with a misleading
  `No such container` until the user rebooted.
- Clusters `gx10-solo` and `gb10-solo` created at the user's request.

**2026-09-20** — Five orcarouter uncensored recipes shipped (`f09aed5`).
Two-node launches (`@eugr/glm-5.3-flash`, Step-3.7 AEON) died in
`ncclCommInitRank`. The working fix was to pin `NCCL_IB_HCA` to the two f1
ports. Step-3.7 AEON loaded and then produced garbage; its model card says
"KNOWN BROKEN".

### Phase 4 — verification at scale (09-25 to 09-29)

**2026-09-25 / 09-26** — AINode uninstalled from both nodes. DeepSeek
uncensored `-ep2` added and the orcarouter recipes reworked (`ac4ca9f`); NCCL
pin moved from recipes into the `dgx-pair` cluster definition (`f5807e3`); every
recipe aligned with the sparkrun 0.3 recipe format (`2918bb7`, `2fd9ef7`).
sparkrun upgraded 0.3.9 → 0.3.10. Headless NVIDIA PAIR installed, which moved
Ollama to port 11435 on both nodes.

**2026-09-26** — `deepseek-v4-flash-vision-uncensored-tp2` verified on the eugr
b12x image (`9303e9d`): 1,048,576 context, 57 tok/s, vision and tool calls
working.
- Its first attempt reported a 576-token context because another service held
  33 GB on the head. A co-tenant silently shrinks auto-sized context.
- After a 188k-token prompt the engine died; this led to the `-coder-tp2`
  profile.
- `.claude/skills/verify/SKILL.md` created (the definition of *verified*).

**2026-09-27** — Fleet benchmark (`52d342d`, `ead92a3`, `67df4c2`),
MiniMax-M2.7 on Atlas EP=2 (`c4776b1`), seven registry recipes adopted
(`379aa6f`).
- Measured (c=1 / 8-way tok/s): heretic-35B batch 41.5 / 193; Flash-Next base
  TP2 46–55 / ~92; Inkling TP2 32 / 67 at 1M context; Laguna-S 2.1 16.9 / 46.5;
  DeepSeek coder 30.2 / 45.6; MiniMax-M2.7 Atlas EP2 27.7 single-stream at 12k
  context.
- `max_num_batched_tokens: 2048` stopped the 8k prefills that froze the worker
  twice.
- `qwen3.8-flash-next-uncensored-nvfp4-tp2` marked UNFIT: its bf16 embedding
  table costs 47.68 GiB per rank and leaves negative KV headroom.
- New cluster `dgx-pair-ep` (scheduling cap 0.95) for EP-only recipes.
- Two sparkrun 0.3.10 defects documented: self-rsync deletes symlinked HF
  blobs, and digest-pinned images fail on the worker.
- User rule: check every registry before writing a custom recipe.

**2026-09-28** — Pass 8 banked four results (`925309c`): Nemotron-3-Nano 30B
58.4 / 154.6, GLM-4.7-Flash AWQ 42.2 / 110.2, Nemotron-3-Super 120B TP2
24.7 / 40.6, Qwen3.8-27B FP8+MTP 12.3 / 73.4. All recipe images pinned to
immutable tags (`476f388`). `minimax-m2.5-awq-tp2` removed (`582eab8`). The six
remaining pass-8 entries all failed (`a223087`).

**2026-09-29** — Root cause of the two-node failures found and fixed
(`c44b8ca`, `5236dbe`, `cacc10d`).
- The head's f1 ports had no static IPv4 (DHCP with no server), which broke
  RoCEv2 GID derivation. The user set static addresses and `eui64` with
  `nmcli`; afterwards three TP2 retries showed zero comm errors.
- `minimax-m2.7-nvfp4-vllm-tp2` verified at the full 196,608 context
  (utilization 0.82, FlashInfer autotune off).
- Remaining per-model blockers: M3 SGLang scheduler dies at init, Step-3.7 AEON
  still garbage, Flash-Next uncensored has no room for KV.
- The duplicate IPv4 on the f0 and f1 port of each NIC was confirmed
  intentional by the user. Do not "fix" it.
- Whole model inventory (2.3T) backed up to
  `/mnt/nas/dgx-spark/model-backup/huggingface-hub/`. Then deleted from disk:
  Step-3.7 AEON, gpt-oss-120b, Ornith-1.0, MiniMax-M2.5 AWQ.
- Knowledge base started at `~/workspace/knowledge-base`.

### Phase 5 — measure, rank, document (09-30 to 10-07)

**2026-10-01** — A long day, nine commits.
- Dead recipes dropped (`5e846b3`): `gpt-oss-120b-mxfp4-tp1`,
  `minimax-m3-v0-nvfp4-reap25`, `step37-flash-aeon-abliterated-nvfp4-tp2`.
- North-Mini-Code and DeepSeek-V4-Flash NVFP4 adopted from registries
  (`51a931e`). Both were later found to have no weights (`26d8146`), which is
  where the "metadata stub" warning comes from.
- `step-3.7-flash-nvfp4-tp2-miaai` made launchable (`49eb6a1`) and booted
  (`e83f665`): coherent for two requests, then a worker rank wedged. Step-3.7
  at TP=2 fails on the official quant as well as the AEON one.
- `qwen3.8-27b-uncensored-nvfp4-tp1` verified (`dd6632c`, `62584d0`,
  `0664f9f`): needle test 21/21 up to 247,670 tokens, zero refusals on
  JailbreakBench, GSM8K 96.0%, MMLU 83.3%. A prefill cliff appears past about
  150k tokens.
- Eval harnesses written under `benchmarks/redteam/`.
- `IMAGE-POLICY.md` written and four of its five actions done (`2897dd7`).
  Mirroring images into spark-arena is blocked: no GHCR token with
  `write:packages`.

**2026-10-02** — `glm-5.3-flash-exl3-1x-spark` recorded from a recipe the user
pasted (`1cc0afd`). Refusal-dial measured: 100% harmful compliance, GSM8K 96.0,
MMLU 86.0. DeepSeek uncensored crashed under 200 sustained requests with the
pair to itself; not retried since.

**2026-10-06** — Coverage audit and inventory (`ce50123`, `67ce269`).
- `glm-5.2-nvfp4-aqlm-tp3` deleted under the user's rule: keep what runs on two
  nodes, delete what needs three.
- `MODELS.md` created: 21 complete checkpoints serving 27 recipes.
- `CONTEXT.md` created: the glossary that separates *lints*, *serves*,
  *verified* and *benchmarked*.
- Research found: several upstream repos gone, six recipes with no
  `container:`, `hf cache prune` would delete 751.7 GB including verified
  checkpoints, vLLM's launch check reads MemFree rather than MemAvailable, and
  an external report that kernel `7.0.0-1019-nvidia` breaks RDMA.

**2026-10-07** — Nine uncensored models ranked (`a4fd78c`). Gemma-4-26B AEON
first (avg 91.3), refusal-dial second (91.0), Gemma-4-12B third (90.0).
Disqualified: Nemotron-3-Nano-Omni AEON (93% harmful compliance),
Qwen3.6-35B heretic (74%), DeepSeek (crashed). Full table in `INDEX.md` and
`benchmarks/redteam/RANKING-uncensored-2026-10-02.md`.

### Phase 6 — gate design and cleanup (10-07 to 10-13)

**2026-10-07 to 10-10** — Pre-push validation gate designed, not built.
- A strict gate would fail 25 of 53 recipes; the 22 missing models total
  1.63 TB against 1.21 TB free.
- Design: `tools/preflight.py`, `.githooks/pre-push`, `tools/PREFLIGHT.md`,
  with blocking checks (container present, immutable tag, weights known,
  schema valid, image pullable) and informing checks. Section 1 approved by the
  user; section 2 still awaiting an answer.
- A port of the refusal dial from Qwen3.8 to GLM-5.3-Flash was scoped, not
  started.

**2026-10-13** — Live recheck, SSH fix, cleanup (`4e12ab5`, pushed; registry
updated to 48 recipes).
- Inventory re-measured on both nodes: nothing lost since 10-06. New:
  `nvidia/Qwen3.6-35B-A3B-NVFP4` on the head, and a second stub on the worker.
- Five recipes removed because their Hugging Face repos return "not found":
  `glm-5.3-flash-exl3-tp2`, `mimo-v2.5-tp2`, `ornith-1.5-35b-a3b-nvfp4-tp1`,
  `qwen3.8-flash-next-nvfp4-tp1`, `qwen3.8-flash-next-nvfp4-tp2-sglang`.
  All weights were kept. `MODELS.md`, `INDEX.md` and `README.md` updated.
- The worker rebooted at 06:34. Two of its four ConnectX-7 ports came up with
  no IP, because two NetworkManager profiles there are not bound to an
  interface. The user repaired it at 10:34 with `sudo nmcli con up` for each
  profile on its own interface; afterwards all four worker ports were
  addressed, both pinned HCAs had IPv4 GIDs again, and `sparkrun setup check`
  was clean on both nodes. No two-node launch was run to confirm.
  The accompanying `nmcli con mod … connection.interface-name` did not
  survive the netplan round-trip (the field read back empty), so the two
  profiles are still unbound and the fault can return at the next worker
  reboot.
- `ssh 10.10.20.11` had been failing because an NVIDIA Sync block in the head's
  `~/.ssh/config` redirected it to `10.99.10.11`. The redirect was disabled;
  `sparkrun setup check` reaches both nodes again.
- Found, not changed: a `nemoclaw-vllm` container outside sparkrun holds head
  port 8000 and 46 GB while serving `nvidia/Qwen3.6-35B-A3B-NVFP4`; the proxy
  alias `default` points at `qwen3.8-27b-uncensored`, which nothing serves;
  the docs' `--cluster default` no longer names a cluster.
- A four-voice review of how far to prune agreed: move or remove recipes
  freely (git restores them), delete almost no weights (upstream repos are
  vanishing), and hardlink blobs before any cross-node copy.

## Standing rules from the user

| Date | Rule |
|---|---|
| 2026-07-25 | Keep one canonical copy of each recipe; put benchmark reports in the repo |
| 2026-09-10 | Use the 10.99.x fabric for inference, inter-node jobs and weight copies |
| 2026-09-16 | Manage single nodes as named clusters (`gb10-solo`, `gx10-solo`) |
| 2026-09-26 | Benchmark every recipe whose weights are on disk; run end to end without waiting; ask only when uncertain |
| 2026-09-27 | Before writing a recipe, search every registry; if upstream has one, copy it, validate it, then include it |
| 2026-09-28 | Pin container images to fixed release tags, never `:latest` or floating nightlies; reuse on-disk images instead of downloading new ones |
| 2026-09-29 | Back up the whole model inventory to `/mnt/nas` before deleting anything |
| 2026-09-29 | The duplicate IPv4 on f0 and f1 ports is intentional |
| 2026-10-01 | Image order: spark-arena/sparkrun builds, then eugr, then the model publisher's own docs, then official vLLM; prefer the most secure, long-lived option |
| 2026-10-01 | Rank uncensored models by measured quality and record the results in the repo |
| 2026-10-05 | Keep anything runnable on two nodes; delete anything that needs three or more |

## Technical facts worth not relearning

**Registry and git**
- `spark-forge` is a `file://` registry whose cache is a git clone of `main`.
  Commit to `main`, then run `sparkrun registry update spark-forge`.
- The integration path is direct commit and push to `main`; there is no PR
  step in this repo.
- sparkrun ignores unknown top-level recipe keys and still validates them.
- Do not renumber `INDEX.md` rows; other files cite them by number.

**Memory on GB10**
- One pool of about 121 GiB holds weights, KV cache and the host. Safe
  `gpu_memory_utilization` is 0.70–0.82; 0.85 has caused NVRM OOM at boot.
- Two engines on one node must start one after the other and sum below 1.0.
- vLLM's launch check reads MemFree; drop page caches before a large launch.
- Large two-node models need the pair to themselves.

**Launching**
- Images that bake `ENTRYPOINT ["vllm","serve"]` need
  `executor_config: {entrypoint: ""}`.
- Serve output is in `/tmp/sparkrun_serve.log` inside the container, not in
  `docker logs`.
- `--no-rm` does not keep crashed containers on sparkrun 0.3.10.
- Wait about 90 seconds between a stop and the next launch.
- `HF_TOKEN` is not set in non-interactive shells; pass it inline for gated
  repos (see the verify skill).
- Always use `--no-follow`; note that it skips `post_exec`.

**Two-node networking**
- NCCL and socket pins live in `~/.config/sparkrun/clusters/dgx-pair.yaml`
  under `env:`, not in recipes. They are load-bearing.
- `sparkrun setup cx7` and the setup wizard can rewrite the network layout or
  drop the pins; avoid both on `dgx-pair`.
- Worker "wedge" signature: ping answers, port 22 accepts, no SSH banner. It
  has cleared by itself in 45 minutes to 2 hours.
- After a worker reboot, run `sparkrun setup check --cluster dgx-pair` before
  any two-node launch (see 2026-10-13).

**Weights on disk**
- A cache directory can be a *stub* (config only) or *partial*. Size the
  snapshot; never trust the directory's existence or `du`.
- sparkrun 0.3.10 self-rsync deletes symlinked HF blobs; hardlink them first.
- Never run `hf cache prune` without `--dry-run`.
- orcarouter repos are gated with auto-approval; the HF account must accept
  each one once.

**Evaluation**
- "Uncensored" in a model name predicts nothing; measured harmful compliance
  ran from 74% to 100%. Always run the benign control split too.
- Method: JailbreakBench 100 harmful + 100 benign, GSM8K n=150, MMLU n=150,
  1400-token budget, results appended per record.

## Contradictions left in the record

These disagree across sessions and were not resolved by this compilation.

- **Which head ports lacked IPv4 before 2026-09-29.** One session says the f1
  ports had none while f0 did; another says the f0 ports had none from 09-20
  to 09-28.
- **Whether the partial GLM-5.3 EXL3 download can be completed.** The original
  repo is gone. One research note from 10-05 says a byte-identical mirror
  exists; this was never checked.
- **Heretic-35B harmful compliance.** 76% on the first pass, 74% on the re-run
  at the common token budget. The ranking uses 74%.
- **MiniMax-M2.7 prefill time at 196k.** Two messages a minute apart give
  "64k in 46 s" and "64k in under 5 s".
- **Padding size in the padded refusal run.** "About 100k tokens" and "about
  58k tokens" in the same session.
- **Repo visibility on GitHub.** Advised private, later called public.

## Open items as of 2026-10-13

1. Make the worker's ConnectX-7 profile binding permanent. The runtime repair
   on 10-13 holds until the next reboot; `netplan-enp1s0f1np1` and
   `netplan-enP2p1s0f1np1` still have no interface binding. Read
   `/etc/netplan/90-NM-422c4968-….yaml` and `90-NM-9d5a63e4-….yaml` on the
   worker (root only) before choosing a fix. Also run one two-node launch to
   confirm the fabric end to end.
2. Done 2026-10-13: the 10-13 changes were committed as `4e12ab5`, pushed,
   and the registry updated. Cause of item 1, seen in the two netplan files:
   each defines the port under its own name but carries `match: {}`, which
   matches any device. Proposed fix: delete that line in both files, then
   `sudo netplan generate && sudo nmcli connection reload`.
3. Decide whether `nemoclaw-vllm` keeps head port 8000, and what the proxy
   alias `default` should point at.
4. Rotate the Hugging Face token: it was printed in session transcripts on
   2026-09-25 and 2026-10-01 and no rotation is recorded. Other API keys were
   printed on 2026-10-10.
5. Build the pre-push gate; section 2 of the design is waiting on the user.
6. `glm-5.3-flash-exl3-1x-spark` cannot launch as written (wrong checkpoint,
   provisional container, runtime and entrypoint disagree). It is also missing
   from the `INDEX.md` tables.
7. Six recipes had no `container:` field on 10-05; two of them were removed
   on 10-13. Still affected: `deepseek-v4-flash-tp2`,
   `ling-3.0-flash-int4-tp1-sglang`, `muse-glimmer-30b-nvfp4-tp1`,
   `qwen3.8-27b-nvfp4-tp1-alt`.
8. Retry DeepSeek uncensored under sustained load; diagnose Step-3.7 at TP=2
   (a newer vLLM is the untried lever).
9. Decide on the 81.6 GiB partial GLM-5.3 EXL3 download, the 171 GiB-per-node
   UNFIT Flash-Next uncensored weights, and the abliterated orphans listed in
   `MODELS.md`.
10. Confirm or refute the kernel `7.0.0-1019-nvidia` RDMA report on this pair.
11. `.claude/workflows/validate-sparkrun-recipes.js` still defaults to the old
    path `/home/devops/workspace/code`.
12. Image mirroring into spark-arena waits on a GHCR token with
    `write:packages`.
