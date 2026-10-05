# spark-forge recipe registry

A registry of sparkrun recipes for serving LLMs on a two-node DGX Spark pair
(head `gb10-spark`, worker `gx10-spark`). This file fixes the vocabulary: the
repo previously used one word, "verified", for at least three different bars,
which is how a coverage count can produce several irreconcilable answers.

## Language

### Recipe status

**Recipe**:
A YAML file in `recipes/` that fully specifies one served model — checkpoint,
container, runtime flags, and fit.
_Avoid_: config, manifest, profile

**Lints**:
Passes `sparkrun recipe validate`. A statement about the file, not the model —
it proves nothing about whether anything can serve.
_Avoid_: validated, verified, checked

**Serves**:
The engine reached a ready state and the endpoint accepts requests. Necessary
for verified, but not sufficient — a recipe can serve and still return garbage.
_Avoid_: works, running, up

**Verified**:
The model **answered a request** on this cluster. This is the authoritative bar,
set by `.claude/skills/verify/SKILL.md`; a dry run or a clean lint never
qualifies.
_Avoid_: tested, working, validated

**Benchmarked**:
Has measured numbers from a harness run, recorded in `benchmarks/`. Strictly
more than verified: every benchmarked recipe is verified, not every verified
recipe is benchmarked.
_Avoid_: measured, profiled, scored

**Unfit**:
Serves on this pair but cannot be used — returns incoherent output, or will not
fit at any workable setting. Deliberately distinct from broken, because the
recipe itself may be correct and the hardware the constraint.
_Avoid_: broken, failed, bad

**Promoted**:
Lifted by hand into the headline table at the top of `INDEX.md`. An editorial
choice about prominence, carrying no evidential weight of its own.
_Avoid_: official, blessed, verified

**Evidence**:
The artifacts that substantiate a claim — a `results_*.json`, a `mem_*.txt`, a
row in `redteam/results/SWEEP.tsv`, or a dated note citing one. A `>>> VERIFIED`
header is a claim about evidence, never the evidence itself.
_Avoid_: proof, results

### Checkpoints on disk

**Checkpoint**:
The model weights a recipe serves, named in its `model:` field. No recipe here
loads from a local path.
_Avoid_: model (ambiguous between the weights and the thing being served), repo

**Complete**:
Every shard named in `model.safetensors.index.json` resolves to a real file and
the byte sum reaches `metadata.total_size`. The only status that means
launchable.
_Avoid_: downloaded, present, cached

**Partial**:
Some shards resolve but not all. Indistinguishable from complete by directory
size alone, and the reason a correct recipe can fail at load.
_Avoid_: incomplete, half-downloaded

**Stub**:
A cache entry holding config and tokenizer but **no weight files** — HF fetched
the metadata and stopped. Looks like a real checkpoint in a directory listing.
_Avoid_: empty, placeholder, metadata-only cache

**Orphan**:
A complete checkpoint on disk that no recipe references. Consumes the same disk
as a live one and is invisible to any recipe-driven audit.
_Avoid_: unused, stale

**Auxiliary artifact**:
Weights a recipe pulls in beside its checkpoint — a DFlash/DSpark drafter, or an
ablation tensor. Never servable alone, and must be pre-cached because serve
containers run `HF_HUB_OFFLINE=1`.
_Avoid_: drafter (that is one kind), extra model, side model

### Placement

**Rank**:
One process holding a shard of the model. Ranks needed is
`max(tensor_parallel, expert_parallel)`; a recipe needing more than two cannot
run on this pair at all.
_Avoid_: node, GPU, worker (a rank is a process, a node is a machine)

**Pair**:
The two-node cluster (`dgx-pair`) as a unit. A TP2 or EP2 recipe needs its
checkpoint complete on **both** nodes; a TP1 recipe on only one, so a
single-node checkpoint is not automatically a gap.
_Avoid_: cluster (`default` is also a cluster name), fleet
