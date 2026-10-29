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
  profiles were still unbound at that point. Corrected the same day, about
  10:55: the binding was made permanent by editing the two netplan files
  (open item 1 has the detail).
- Two-node test launch at 11:17, after the binding fix:
  `nemotron-3-super-120b-nvfp4-tp2` on `dgx-pair` with
  `-o gpu_memory_utilization=0.5` (recipe default is 0.7; lowered because the
  head had about 72 GB free outside page cache). Served 4 minutes after
  launch at 262,144 context; 36.63 GiB per rank, KV 18.39 GiB. Answered
  correctly, 24.6 tok/s single-stream, 8 of 8 concurrent requests at 89 tok/s
  aggregate. `ethtool -S` RDMA counters went from 0 to about 25 GB on
  `enp1s0f1np1` and 24 GB on `enP2p1s0f1np1` on each node (head tx equal to
  worker rx) and stayed 0 on both f0 ports, so the traffic ran over the two
  pinned links. No NCCL or engine errors in either rank's log; the worker
  answered SSH straight after teardown. `nemoclaw-vllm` was stopped for the
  test at the user's request and left stopped.
- `ssh 10.10.20.11` had been failing because an NVIDIA Sync block in the head's
  `~/.ssh/config` redirected it to `10.99.10.11`. The redirect was disabled;
  `sparkrun setup check` reaches both nodes again.
- Found: a `nemoclaw-vllm` container outside sparkrun held head port 8000 and
  46 GB while serving `nvidia/Qwen3.6-35B-A3B-NVFP4` (stopped later that day,
  restart with `docker start nemoclaw-vllm`). Found, not changed: the proxy
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

1. Worker ConnectX-7 binding: fixed 2026-10-13 about 10:55. The user deleted
   the `match: {}` line from `/etc/netplan/90-NM-422c4968-….yaml` and
   `90-NM-9d5a63e4-….yaml`, then ran `netplan generate` and
   `nmcli connection reload`. All four worker profiles now report their own
   interface and no unbound ethernet profile is left (backup of the old files
   in `/root/netplan.bak-2026-10-13` on the worker). Closed: the user
   rebooted the worker at 11:15:58 the same day; all four ConnectX-7 profiles
   activated on their own ports at boot with no failures, and the two-node
   test launch at 11:17 (see the 10-13 entry) ran on that fresh boot.
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

## 2026-10-13 (afternoon): Flash-class uncensored recipes, in progress

Spec `docs/superpowers/specs/2026-10-13-flash-uncensored-recipes-design.md`, plan
`docs/superpowers/plans/2026-10-13-flash-uncensored-recipes.md`. State at 13:20,
nothing committed:

- Removed six recipes (`git rm`, staged): `qwen3.8-flash-next-uncensored-nvfp4-tp2`,
  `glm-5.3-flash-nvfp4-tp2`, `glm-5.3-flash-exl3-1x-spark`,
  `glm-5.3-flash-uncensored-nvfp4-tp2`, `deepseek-v4-flash-tp2`,
  `deepseek-v4-flash-vision-exp-tp2`. 42 recipes remained before the additions.
- Deleted nine config-only stubs on the head and one on the worker (largest 33 MB).
  Left alone: `nvidia/DeepSeek-V4-Flash-NVFP4` stub, the 81.6 GiB partial GLM EXL3
  download, the orcarouter Flash-Next weights (all three await the user), and the
  worker's 1.7 GiB partial `unsloth/Qwen3.8-Flash-Next-GGUF`.
- Added four recipes, all UNVERIFIED (lint and dry run only):
  `qwen3.8-flash-next-abliterated-nvfp4-tp2`, `deepseek-v4-flash-0731-tp2`,
  `deepseek-v4-flash-0731-refusal-dial-tp2`, `glm-5.3-flash-abliterated-nvfp4-tp2`,
  plus `recipes/mods/glm53-sm121-topk`.
- `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` copied worker to head: 206 shards,
  125.9 GiB, blobs are regular files on both nodes.
- Built `spark-forge/vllm-dsv4-rank1:20261013` (image ID `976974ad7fd3`) and loaded it
  on both nodes; provenance in `images/deepseek-rank1/README.md`.
- Downloads running on the head at about 12 MiB/s: `deepseek-ai/DeepSeek-V4-Flash-0731`
  (155 GiB), then `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` (184 GiB)
  and its DFlash2 drafter. Logs in `~/.cache/sparkrun-jobs/`. Each needs an rsync to
  the worker afterwards.
- Blocked: no launch has been attempted. `nemoclaw-vllm` was started on the head at
  12:55 (restart policy `unless-stopped`), holds port 8000 and 52 GiB, and answered
  requests at 12:59. Every TP2 launch needs it stopped.

### 2026-10-13 15:25 update

- `qwen3.8-flash-next-abliterated-nvfp4-tp2` VERIFIED (INDEX row 59): 262,144 context,
  40.4 tok/s c=1, peak 166 tok/s 8-way, JBB 100/100 harmful and 100/100 benign, engine
  alive after 200 requests, passkey at 90k tokens. The first boot, with the b12x RoCE
  all-reduce on, died 8.5 min into the same eval (`RoCE collective on rank 0 timed out
  waiting for rank 1`); the verified boot used `VLLM_ENABLE_ROCE_ALLREDUCE=0`.
- `glm-5.3-flash-abliterated-nvfp4-tp2` booted and reported 262,144 context but answered
  nothing: the first request hung and the engine died on a `sample_tokens` RPC timeout.
  Each rank held 105.2 GiB (86 % of the node); details in the recipe header.
- **Worker management NIC is unstable.** `enP7s7` (r8127) on `gx10-spark` logged link-down
  at 12:06:56, 12:08:21, 12:09:04, 12:09:14, 14:06:55, 14:08:13, 14:09:52, 14:10:59,
  14:11:36, 14:12:29, 14:14:23, 14:14:59, 14:20:04, 14:25:12, 14:29:11, 14:30:45, 14:32:39,
  14:45:42, 14:46:31, 14:48:01 and 15:11:38, and has stayed down since the last one
  (`carrier=0`, 43 carrier changes since the 11:16 boot; the head's NIC shows 2). The
  14:06-14:08 drops bracket the first Qwen engine death at 14:07:35 and the 15:11:38 drop
  coincides with the GLM hang. The worker stays reachable at `gx10-spark.local`
  (10.99.10.11, ConnectX-7). Cause not established; it may also bear on the Step-3.7 and
  orcarouter DeepSeek sustained-load failures. Root is needed to bounce the interface.
- `nemoclaw-vllm` (head) and `vllm-reranker` (worker) are stopped at the user's word and
  not yet restored.
- DeepSeek 0731 download restarted twice (a transfer setting stalled it, then it was paused
  to relieve head memory during the GLM boot); running again at 15:25. GLM checkpoint and
  drafter are complete on both nodes, blobs hardlinked on the head.
- sparkrun's planner compares `metadata.model_vram` against the node's 121 GiB, so the
  value must be GiB of weights; a decimal-GB figure made it refuse a launch that fits.

### 2026-10-13 19:05 update

- `glm-5.3-flash-abliterated-nvfp4-tp2` VERIFIED on its second boot (INDEX row 62): 3 GiB
  KV pin, 262,144 context, 21.9 tok/s c=1, JBB 100/100 and 100/100, alive after 81 min,
  about 102 GiB per rank. The management NIC dropped 12 times during that run with no
  effect, so the first boot's hang is more likely memory pressure than the NIC.
- `deepseek-v4-flash-0731-refusal-dial-tp2` serves at 393,216 context with a 1.35M-token
  KV pool, boots at lambda 0, and switches live: 7/8 sampled harmful prompts refused at 0,
  1/8 at 1.5, 7/8 after returning to 0; 44.1 tok/s c=1. Full JBB at lambda 1.5 with
  default thinking: 82/100 harmful (15 refusals, 3 truncated), 95/100 benign (5
  truncated), 0 errors, alive after 59 min, peak 117.5 tok/s 4-way. A lambda 2.0 run was
  in progress at commit time. The weights are revision `7872f01`; the directions were
  extracted against `9e165c3` and work regardless.
- `deepseek-v4-flash-0731-tp2` (stock) is lint and dry-run only.
- The worker was rebooted at 15:33 and 15:51 by the user. Its management NIC kept
  flapping (34 drops by 18:35) and failed one launch with an SSH timeout; the user
  reported fixing the port at 18:58 and no drop was logged after 18:35:11.
- Not done: GLM NVFP4-KV long-context recipe (mod and topk copy prepared, image not
  pulled), stock DeepSeek verification, full `MODELS.md` re-measure, weight deletions,
  restoring `vllm-reranker` (worker) and `nemoclaw-vllm` (head), row 48's RoCE setting.

### 2026-10-13 20:55 update

- `deepseek-v4-flash-0731-refusal-dial-tp2` VERIFIED (INDEX row 61). JBB at lambda 2.0:
  harmful 93 complied / 1 refused / 6 truncated, benign 93 / 1 / 6; at 1.5: 82 / 15 / 3
  and 95 / 0 / 5. Zero errors, alive after both hour-long runs, passkey at 130k tokens.
  Use lambda 2.0.
- `deepseek-v4-flash-0731-tp2` VERIFIED with a short test (row 60): 262k, 44.6 tok/s c=1,
  137 tok/s 8-way, KV 360k tokens, passkey at 60k. No soak.
- `glm-5.3-flash-abliterated-nvfp4kv-long-tp2` is UNFIT here. It boots at 524k and at
  368k and answers short and 40k prompts, but the head's earlyoom (`-m 2`) killed the
  vLLM worker on a 40k prompt at the 3 GiB pin and on a 250k prompt at the 2 GiB pin.
  The second kill also took an unrelated `llama-server` process on the head (pid 952844,
  26 MiB RSS). Details in the recipe header. Not in INDEX; not committed at this time.
- The 262k GLM recipe was never tested past 40k tokens either; its head low-water at
  40k was 5.6 GiB, about 3 GiB above the earlyoom line.
- sparkrun's planner rejects launches whose own KV estimate overshoots; `--no-auto-detect`
  skips the estimate.

## 2026-10-14: weight cleanup

- Deleted at the user's word ("Delete Orcarouter Flash-Next … And also delete which you
  must have to"): `orcarouter/Qwen3.8-Flash-Next-Uncensored-NVFP4` on both nodes (170.9 GiB
  each, plus 20 hardlinked shared-store copies on the head), the 82.3 GiB partial
  `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` on the head, and 16 leftover `.incomplete` files
  (6.4 GiB) from the stalled DeepSeek download. No backup was taken: `/mnt/nas` was not a
  mountpoint. The orcarouter repo is still published and can be re-downloaded.
- A dry run first confirmed no recipe referenced either model and no file was shared with
  another checkpoint. Afterwards the five kept Flash-family checkpoints on the head had
  zero broken shards. Free space: head 852 GiB, worker 1.3 TiB.
- Not deleted: the `nvidia/DeepSeek-V4-Flash-NVFP4` stub and `deepseek-v4-flash-nvfp4-atlas-ep2`
  (a runnable-in-principle stock route that only lacks its download), and the worker's
  1.7 GiB partial `unsloth/Qwen3.8-Flash-Next-GGUF`.
- `glm-5.3-flash-abliterated-nvfp4kv-long-tp2` and `mods/glm53-nvfp4kv-overlays` committed
  as UNFIT so the work is not lost; the recipe is deliberately absent from the INDEX tables.

### Open items carried forward

1. Worker management NIC `enP7s7` still dropped link at 19:45:29 and 19:55:31 on 10-13
   after the user's fix.
2. Head earlyoom (`-m 2`) killed an unrelated Hermes `llama-server` during the GLM
   long-context test on 10-13; it was not restarted.
3. `nemoclaw-vllm` on the head is still stopped (stopped 10-13 at the user's word).
4. Row 48 still sets `VLLM_ENABLE_ROCE_ALLREDUCE=1`, the transport that killed the first
   abliterated Flash-Next boot; not changed, not soak-tested.
5. The 262k GLM recipe was tested only to 40k-token prompts.
6. `MODELS.md` tables need a full re-measure; only its dated update block is current.
7. GSM8K/MMLU were not run on any of the four new recipes.

### 2026-10-14: vLLM #54150 exposure check

- #54150 (silent U+FFFD from ModelOpt NVFP4 MoE checkpoints) is caused by vLLM's marlin repack
  using the gate global scale for both halves of the fused gate/up GEMM. Only checkpoints whose
  per-expert gate and up `weight_scale_2` differ are affected.
- `dealignai/Qwen3.8-Flash-Next-ABLITERATED-NVFP4` is ModelOpt 0.46.0, but all 24,576 expert
  gate/up scale pairs are equal (plain safetensors header read), so it is not exposed.
  `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45` is compressed-tensors (immune).
  DeepSeek 0731 is the official FP8 checkpoint with the runtime refusal dial.
- Recheck any new ModelOpt NVFP4 MoE checkpoint the same way before adopting it.

### 2026-10-16: NAS mount check

- `/mnt/nas/dgx-spark` is an fstab `x-systemd.automount` with `idle-timeout=600`; it unmounts
  after 10 idle minutes and remounts on first access. Check with `ls` on the path, not
  `mountpoint` alone, before concluding it is down.
- Mounted on both nodes (NFSv4, 29T free), but not writable for backups: new files land as
  uid 1000, so "Map all users to admin" squash is no longer in effect, and `model-backup/` is
  `r-x` for uid 1024. Weight deletions stay blocked until the export squash is restored in DSM.
- Later the same day: squash was restored in DSM, and writes now land as uid 1024. `model-backup/`
  is still not writable because the directories have mode `r-x`.
- Decision: move `model-backup/` (2.3T) and `nodes/` (51G) to the new `ai-models` share
  (`/volume1/ai-models`, exported to 10.10.20.0/24), copying server-side in DSM. Proxmox,
  chaindata, template and dump stay in `dgx-spark`. Pre-move inventory:
  `~/nas-move-baseline-2026-10-16/` (model-backup: 2050 files, 1216 symlinks, 2,522,101,640,426 B;
  nodes: 138,761 files, 136 symlinks, 54,733,409,615 B).

## 2026-10-16: retry of the crashed / OOM-killed / unverified uncensored recipes

- `deepseek-v4-flash-vision-uncensored-tp2` RE-VERIFIED: full 1,048,576 context (6.4 GiB
  `vllm-reranker` co-tenant on the worker absorbed), 80/80 requests at 8-way over 5 min
  (~108 tok/s aggregate, 0 errors) — the 10-02 sustained-load crash does not reproduce —
  passkey at 66.5k, vision answers correctly. One caveat: on the first boot, the first
  vision request after a cold start killed the engine (RuntimeError: cancelled →
  EngineDead); a relaunch warmed with text served the identical request fine. Warm with a
  text request before the first image.
- `deepseek-v4-flash-vision-uncensored-ep2` UNFIT: b12x MoE kernel rejects EP at load —
  "Mxfp4 MoE backend 'B12X_MXFP4_BF16' does not support ... ep_size=2". Two identical
  deaths; crashed sparkrun containers auto-remove, so logs were captured by snapshotting
  /tmp/sparkrun_serve.log during boot.
- `glm-5.3-flash-abliterated-nvfp4kv-long-tp2` VERIFIED (new INDEX row 63): 368,640 ctx,
  passkey PASS up to 266k prompt tokens, 20.5 tok/s c=1, oversized prompt 400s correctly.
  Head low-water 3.3 GiB vs 2.49 GiB earlyoom line — the 10-13 kills were ~3 GiB of extra
  head residents, and the margin is still only ~0.8 GiB. 262k recipe remains the default.
- `nex-n2.5-mini-uncensored-nvfp4-tp1` still blocked: the HF account behind the token has
  not accepted the orcarouter/Nex-N2.5-mini-Uncensored-NVFP4 gate (403 on files). Also
  needs `-o entrypoint=''`. User action: accept the gate on the model page, then relaunch.
- The auto-mode classifier declined stopping `vllm-reranker` (worker co-tenant, up via
  restart policy after a ~35 h-ago reboot); all tests ran with it up. It did not matter.

### 2026-10-16 (later): Nex verification and the two-Qwen colocation experiment

- `nex-n2.5-mini-uncensored-nvfp4-tp1` UNFIT: gate accepted, 23.9 GiB downloaded, boots and
  serves 262k on `vllm/vllm-openai:v0.24.0` with `-o entrypoint=''` — but every completion
  is a run of `!` at temp 0 and 0.7. Stock image's NVFP4 path misfires on SM121; retest on
  a GB10-tuned image (eugr nightly) before any further use.
- Running Qwen3.8 Flash ablit (tp2) and a Qwen3.8-27B at the same time **does not work**:
  (1) 27B-vision (orcarouter) beside Flash on the head dies after its multi-modal warmup —
  at util ≤0.22 nothing is left for KV, at 0.24 vLLM's free-memory check fails (28.0 free
  < 29.2 asked); (2) the refusal-dial 27B booting on the worker memory-spiked Flash's rank1
  to death (executor shutdown; same cascade as the GLM earlyoom story); (3) the text-only
  dial DID boot beside Flash on the head at 0.22/16k, but Flash's tp2 job died during that
  boot window; (4) with the dial resident first, sparkrun's placement refuses to put a tp2
  rank on an occupied host (`only placed 1 of 2 ranks`), with or without --no-auto-detect.
  Flash itself needs gpu-mem 0.64 at 131k (0.58 and 0.60 leave no KV: fixed overhead is
  ~9-10 GiB/rank over the 63 GiB of weights).
- **What does work concurrently: one solo model per node.** Verified live: refusal-dial 27B
  on the head (16k) + Nex on the worker answered simultaneous requests (27B: 144 in 0.3 s).
  sparkrun places two tp1 jobs happily; only multi-node jobs demand exclusive hosts.
- End state: test jobs stopped; `qwen3.8-flash-next-abliterated-nvfp4-tp2` relaunched at
  its recipe defaults (0.7, 262k). A `sovereign-qdrant` container appeared on the worker at
  ~09:00 (not sparkrun's, left alone).

### 2026-10-24: ai-models move status

- Not yet verifiable: `/mnt/nas/ai-models` is not in the head's fstab or mounted, and the worker
  (10.10.20.11) does not answer ping or SSH.
- `model-backup/` grew after the 10-16 baseline (now 63 models). Current inventory:
  `~/nas-move-baseline-2026-10-24/` (model-backup: 3142 files, 2361 symlinks,
  3,401,563,523,114 B; nodes unchanged). Verify the copy against this one.

### 2026-10-24 (later): Flash-abliterated full benchmark + 214k context verification

- Worker mgmt outage root-caused: `enP7s7` (the wired mgmt NIC that holds 10.10.20.11) has
  NO-CARRIER — physical link down; the host itself was up 5 days. Temp fix (user-run, root):
  wifi `wlP9s9` joined "Rayan's Mesh" (same 10.10.20.0/24 L2, DHCP gave 10.10.20.197), then
  `ip addr add 10.10.20.11/24 dev wlP9s9`. **NON-PERSISTENT** — redo after any worker reboot,
  or promote to an nmcli profile. The wired NIC still needs a physical fix (cable/switch port).
- The 2026-10-22 ladder wedge (3/6 cells, stuck entering d8192×c8 for ~66 min) is explained by
  that NIC drop mid-run, not a recipe fault: the full ladder completed clean on 2026-10-24 over
  the wifi mgmt path. The stale wedged node_1 container (Up 45 h) was torn down once the worker
  was reachable again.
- `qwen3.8-flash-next-abliterated-nvfp4-tp2` benchmarked on the canonical quick ladder (profile
  reconstructed to match FLEET-2026-09-27 and the existing results_*.json: depth 0/8k/32k ×
  c=1/8, pp2048/tg128, 3 runs/cell): 39.1 tok/s c=1 / 78.5 8-way at d0; 35.2 / 76.0 at 8k;
  36.9 / 71.1 at 32k — within a few percent of row 48 across the ladder. Raw:
  `benchmarks/results_qwen38-flash-next-abliterated-tp2.{json,csv}` + mem file (model load
  41.41 GiB/rank in 344 s; KV 14.96 GiB; pool 1,015,984 tokens = 3.88× at 262k).
- Full-context needle: PASS at 329 / 35,553 / 133,670 / 214,568 prompt tokens (101 s at 214k,
  temp 0, thinking off), head low-water ≥21.3 GiB, no OOM — extends the 2026-10-13 "90k only"
  bar to ~214k. Large-codebase full-context use is proven near the 262k ceiling.
- Instance stopped afterwards; both nodes idle. INDEX row 59 and the recipe header updated to
  BENCHMARKED 2026-10-24. Not committed (commit only when asked).

### 2026-10-24 (later still): GLM-5.3-Flash-abliterated (row 62) benchmarked; context bar 40k → 211k

- Quick ladder complete (same profile as the collection): c=1 28.0 / 31.1 / 19.7 tok/s at
  d0/8k/32k; 8-way aggregate 19.8 / 13.2 / 5.4 with ttfr to 112 s — queuing against the 295k
  KV pool (1.13×) serializes 8-way at depth, confirming "one long request at a time" in
  practice. Boot 573 s; model load 90.77 GiB/rank in 432 s. Raw:
  `benchmarks/results_glm53-flash-abliterated-tp2.{json,csv}` + mem file.
- Full-context needle: PASS at 321 / 35,035 / 131,722 / 211,012 prompt tokens (148 s at 211k),
  head low-water 6.1 GiB vs the 2.49 GiB earlyoom line. The row-63 long-prefill earlyoom kills
  do not reproduce on row 62's fp8-KV profile with a quiet head (co-tenants: sparkrun-ui,
  searxng, worker qdrant — ~1-2 GiB total, tolerated). Engine alive; instance stopped after.
- Abliterated-fleet queue (user-requested): next DeepSeek vision-uncensored tp2 (1M, deep
  needle), DeepSeek 0731 refusal-dial (393k), DeepSeek coder tune (256k), Qwen3.8-27B-uncensored
  (ladder only; context already proven 2026-10-01).
- 05:33: the NAS-side rsync stopped at 2,299,595,538,352 B (no growth for 15 min). Missing:
  about 1.0 TiB of model-backup blobs across 22 models, and every file under `nodes/` (only
  root-owned `700` directory stubs exist). The copy must be re-run on the NAS before any
  verification or deletion.

### 2026-10-24 (abliterated-fleet sweep, cont.): DeepSeek-V4-Flash-Vision-Uncensored benchmarked; context bar 66.5k → 791k

- Row 43 quick ladder: 38.7 tok/s c=1 / 56.4 agg 8-way at d0; prefill-at-depth is the limiter
  (pp 2011 → 445 → 130 tok/s at d0/8k/32k; 32k×8 lands at 9.8 agg, ttfr 67 s). KV pool
  1,142,264 tokens (1.09× at 1M). Raw: `benchmarks/results_deepseek-v4-flash-vision-uncensored-tp2.{json,csv}`
  + mem file. Model load 81.19 GiB/rank in 190 s.
- Deep needle, all PASS: 398 / 34,990 / 131,071 / 210,301 / 438,966 / 790,846 prompt tokens.
  791k retrieved in 571 s — a long sequential prefill runs ~1.4k tok/s, much faster than the
  at-depth ladder cells suggest, so full-context large-codebase use is practical single-stream.
  Head low-water 7.0 GiB; engine alive; text-only throughout (vision cold-boot caveat respected).
- Instance stopped. Next in queue: deepseek-v4-flash-0731-refusal-dial-tp2 (393k).

### 2026-10-24 (sweep, cont.): DeepSeek-0731 refusal-dial benchmarked; context bar 130k → 316k

- Row 61 quick ladder: 46.2 c=1 / 57.5 agg at d0, holding 30.9 / 29.5 at 32k depth — the best
  8-way-at-depth behavior of the abliterated fleet (KV pool 1,368,481 tokens; load 79.17
  GiB/rank in 212 s). Raw: `benchmarks/results_deepseek-v4-flash-0731-refusal-dial-tp2.{json,csv}`
  + mem file.
- Needle all PASS: 319 / 34,911 / 130,992 / 210,222 / 315,767 prompt tokens (182 s at 316k),
  head low-water 7.6 GiB, engine alive. Run at boot lambda 0. Instance stopped.
- Next: deepseek-v4-flash-vision-uncensored-coder-tp2 (256k), then qwen3.8-27b-uncensored ladder.

### 2026-10-24 (sweep, cont.): DeepSeek coder tune benchmarked; 210k needle PASS, engine stays alive

- Row 47 quick ladder: 33.0 c=1 / 47.7 agg at d0; 30.5 / 6.8 at 32k depth (prefill pp
  1947 → 386 → 110 at d0/8k/32k). KV pool 1,241,755 tokens (4.74×); load 80.98 GiB/rank in
  187 s. Raw: `benchmarks/results_deepseek-v4-flash-vision-uncensored-coder-tp2.{json,csv}` + mem.
- Needle all PASS: 319 / 34,911 / 130,992 / 210,222 prompt tokens (115 s at 210k). Head
  low-water 11.1 GiB — the roomiest margin of the fleet, vindicating the 12 GiB KV pin: the
  09-26 post-long-prompt `sample_tokens` RPC engine death did not recur. Instance stopped.
- Last in queue: qwen3.8-27b-uncensored-nvfp4-tp1 ladder (context already proven 2026-10-01).

### 2026-10-24 (sweep complete): Qwen3.8-27B-uncensored ladder; abliterated fleet fully benchmarked

- Row 41 quick ladder (tp1, head): 10.1 tok/s c=1 (9.6 at 32k depth) / 67.1 agg 8-way at d0
  holding 43.7 at 32k — batch lane, consistent with the documented prefill cliff. pp
  2692 → 2019 → 869. KV pool 2,038,395 tokens (7.78×); instanttensor load 22.36 GiB in 7 s.
  Raw: `benchmarks/results_qwen38-27b-uncensored-tp1.{json,csv}` + mem. Needle skipped —
  full context proven 2026-10-01 (21/21 to 247,670 tokens).
- **Abliterated-fleet sweep summary (all on the canonical quick ladder + needle, one day):**
  Qwen Flash-ablit 39.1 c=1 / needle 214k; GLM-5.3-Flash-ablit 28.0 c=1 / needle 211k (8-way
  serializes, KV 1.13×); DeepSeek vision-uncensored 38.7 c=1 / needle **791k** of 1M; DeepSeek
  0731 refusal-dial 46.2 c=1 / needle 316k (best 8-way-at-depth); DeepSeek coder tune 33.0 c=1
  / needle 210k (11.1 GiB head margin); Qwen 27B-uncensored 10.1 c=1 / 67.1 agg (ladder only).
  Every needle cell PASSed; no engine deaths anywhere in the sweep. All instances stopped;
  worker mgmt still on the temporary wifi path (enP7s7 wired NIC awaits physical fix).

## 2026-10-29: GLM-5.3-Flash EXL3 abliterated adopted from the MiaAI-Lab set (row 64)

- The Antigravity agent's 2026-10-16 session left a validated 27-recipe set in
  `~/.config/sparkrun/recipes/miaai-lab/` (its RESULTS.md: 3 PASS serve-only, 4 blocked).
  `glm-5.3-flash-exl3-tp2` (bullerwins/GLM-5.3-Flash-exl3-4bpw-ablit, 850k ctx, weights already
  on both nodes) was the one worth promoting; benchmarked today and committed as
  `recipes/glm-5.3-flash-exl3-abliterated-tp2.yaml`.
- First ladder run died at the first 32k cell: `persistent_topk would oversubscribe ... requires
  >=128KB smem` → EngineDead. The prebuilt `:exl3` image (2026-09-07) lacks upstream's own
  overlay edit that disables GB10 persistent_topk. New `recipes/mods/glm53-exl3-gb10-topk/`
  applies the identical one-line edit pre-serve; full ladder then completed clean.
- Quick ladder (canonical profile): c=1 13.5 / 13.3 / 13.2 tok/s at d0/8k/32k; 8-way 20.5 /
  15.8 / 11.2. Slowest two-node GLM (row 62 does 28.0 c=1) but the flattest at-depth decode.
  Raw: `benchmarks/results_glm53-flash-exl3-tp2.{json,csv}` (no mem file — engine was already
  up from verification when the ladder ran).
- Evals, engine alive throughout (~3.5 h): needle 12/12 PASS to 495,234 actual prompt tokens
  (the script's 800k depth setting; chars-per-token underestimates on this tokenizer), 226 s at
  495k, sequential prefill ~2.1-2.7k tok/s; JBB 100/100 harmful + 100/100 benign, thinking off;
  HumanEval pass@1 87.2% (143/164), generated code executed in a --network none container.
  Head low-water 7 GiB, worker 10 GiB.
- Launched over CX7 addresses (`--hosts 10.99.10.10,10.99.10.11` + `HF_HUB_OFFLINE=1`, not
  committed) because the worker's enP7s7 mgmt link is physically down again (ARP INCOMPLETE
  from the head; worker can't reach head/router on 10.10.20.0/24 despite link-up at 10 Gb/s;
  the 10-24 wifi workaround is not active — wlP9s9 DOWN). Switch port / cable needs a look
  before `--cluster dgx-pair` works again.
- Same session, head cleanup at the user's word: spark-studio removed entirely (service,
  ~/spark-studio 8.9G, spark-searxng container+image; salvaged only
  docs/glm-5.3-flash-spark.yaml), sparkDash repo+container+image removed, kimi-k2.6 NIM image
  (34.5G) removed, nvpair-headless stopped+disabled, LM Studio user-side leftovers removed
  (root-owned lmstudio/nvpair-lmstudio-forward unit files handed to the user to rm).
  23G of parked LM Studio weights in ~/models-parked/lmstudio-2026-10-13 kept pending decision.
- GB10 Recipe Throughput artifact now at v5 with the EXL3 row (28 recipes).
