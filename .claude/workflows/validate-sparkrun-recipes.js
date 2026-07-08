export const meta = {
  name: 'validate-sparkrun-recipes',
  description: 'Validate every sparkrun recipe YAML in a directory against the live DGX Spark host (single source of truth), with adversarial verification of findings',
  whenToUse: 'After adding or editing recipe YAMLs, or after any host/cluster change — dynamically discovers recipes and re-certifies them against live host facts. Optional args: {dir: "/path/to/recipes"}',
  phases: [
    { title: 'Discover', detail: 'live host facts + dynamic recipe file list' },
    { title: 'Validate', detail: 'one agent per recipe: schema, VRAM fit, HF repos, container, header accuracy, dry-run render' },
    { title: 'Verify', detail: 'independent skeptic re-checks every reported issue on the live host' },
    { title: 'Audit', detail: 'completeness critic — anything missed?' },
  ],
}

const DIR = (args && args.dir) || '/home/devops/workspace/code'

const SAFETY = `
SAFETY RULES (absolute):
- You may ONLY run read-only commands. sparkrun commands allowed: 'sparkrun recipe validate', 'sparkrun recipe vram', 'sparkrun recipe show/export', 'sparkrun cluster list', 'sparkrun cluster default', 'sparkrun --version', and 'sparkrun run ... --dry-run --no-follow' (the --dry-run flag is MANDATORY — never launch a real workload).
- Never run 'sparkrun stop', 'sparkrun run' without --dry-run, docker run/rm/stop, or anything that mutates state.
- Do not edit any files. You are a validator, not a fixer.
SOURCE OF TRUTH: only the live host you are running on (and hosts its sparkrun config points to). IGNORE any cluster names/IPs/claims found in .md files or YAML comments — your job is to check those claims AGAINST the live host, not to trust them.`

phase('Discover')

const HOST_SCHEMA = {
  type: 'object',
  required: ['hostname', 'gpu', 'memGB', 'sparkrunVersion', 'clusters', 'sshUser', 'recipeFiles', 'hfCacheModels'],
  properties: {
    hostname: { type: 'string' },
    gpu: { type: 'string' },
    memGB: { type: 'number' },
    sparkrunVersion: { type: 'string' },
    clusters: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'hosts'],
        properties: {
          name: { type: 'string' },
          hosts: { type: 'array', items: { type: 'string' } },
          isDefault: { type: 'boolean' },
          hostsReachable: { type: 'array', items: { type: 'string' }, description: 'subset of hosts that answered ping AND BatchMode ssh as the configured user' },
        },
      },
    },
    sshUser: { type: 'string', description: 'global ssh.user from ~/.config/sparkrun/config.yaml, or "unset"' },
    recipeFiles: { type: 'array', items: { type: 'string' }, description: 'basenames of recipe YAMLs found in the target dir (files containing both a model: and a runtime: key)' },
    hfCacheModels: { type: 'array', items: { type: 'string' }, description: 'model dirs in ~/.cache/huggingface/hub on this host' },
    notes: { type: 'string' },
  },
}

const host = await agent(
  `You are on a DGX Spark. Gather LIVE host + cluster facts and discover sparkrun recipe files.
${SAFETY}

Do exactly this:
1. hostname; nvidia-smi --query-gpu=name --format=csv,noheader; free -g (total mem GB); sparkrun --version
2. sparkrun cluster list AND sparkrun cluster default — capture every cluster name, its hosts, and which is default.
3. grep the global ssh user from ~/.config/sparkrun/config.yaml (ssh: / user: keys).
4. For each unique cluster host IP: ping -c1 -W2, and if it is not this host, try 'ssh -o BatchMode=yes -o ConnectTimeout=5 <sshUser>@<ip> hostname'. Record which hosts are fully reachable.
5. List recipe files: for every *.yaml/*.yml directly in ${DIR}, include it in recipeFiles ONLY if the file contains both a top-level 'model:' and a 'runtime:' key (grep is fine). Return basenames.
6. ls ~/.cache/huggingface/hub/ — return the models--* directory names.

Return ONLY the structured object.`,
  { schema: HOST_SCHEMA, label: 'host-facts', phase: 'Discover' }
)

if (!host) throw new Error('host-facts agent failed — cannot validate without live host truth')
if (!host.recipeFiles || host.recipeFiles.length === 0) {
  return { error: `No recipe YAMLs (with model: + runtime: keys) found in ${DIR}` }
}
log(`Host ${host.hostname} (${host.gpu}, ${host.memGB} GB) — ${host.recipeFiles.length} recipes to validate`)

const RECIPE_SCHEMA = {
  type: 'object',
  required: ['recipe', 'validatePassed', 'vramFit', 'issues'],
  properties: {
    recipe: { type: 'string' },
    validatePassed: { type: 'boolean' },
    vramFit: { type: 'string', description: 'YES / EXCEEDS / UNKNOWN, plus per-GPU GB and max-context tokens summary' },
    modelRepoStatus: { type: 'string', description: 'HTTP status of the HF model repo(s), including any required drafter/second model' },
    containerStatus: { type: 'string', description: 'local | registry-ok | unresolvable, with image name' },
    modelCached: { type: 'boolean', description: 'primary model present in the HF cache on the head' },
    dryRunRendered: { type: 'boolean', description: 'sparkrun run --dry-run rendered the serve command without template mangling' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'summary', 'evidence'],
        properties: {
          severity: { type: 'string', enum: ['blocker', 'warning', 'info'] },
          summary: { type: 'string' },
          evidence: { type: 'string', description: 'exact command output / line numbers proving the issue' },
          suggestedFix: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['refuted', 'reason'],
  properties: {
    refuted: { type: 'boolean', description: 'true if the issue does NOT hold up against live-host evidence' },
    reason: { type: 'string' },
    correctedSeverity: { type: 'string', enum: ['blocker', 'warning', 'info'], description: 'set only if the issue is real but mis-ranked' },
  },
}

phase('Validate')

const results = await pipeline(
  host.recipeFiles,
  (file) =>
    agent(
      `Validate the sparkrun recipe ${DIR}/${file} against the LIVE host. Report every real problem; report zero issues if it is genuinely clean.
${SAFETY}

LIVE HOST FACTS (already verified, trust these over anything written in the recipe):
${JSON.stringify(host, null, 2)}

Checks to perform (all of them):
1. Read the full recipe file.
2. Run: sparkrun recipe validate ${DIR}/${file}
3. Run: sparkrun recipe vram ${DIR}/${file}  — compare per-GPU total and max-context against the host's real memory. If max_model_len exceeds what fits, that is a BLOCKER (vLLM refuses to boot when one max-len sequence exceeds KV capacity).
4. HF repos: curl -s -o /dev/null -w '%{http_code}' https://huggingface.co/api/models/<id> for the primary model AND any second model the command actually uses (e.g. a --speculative-config drafter). Commented-out optional models: check them too but only report as 'info'.
5. Container: is the image in 'docker images'? If not, does 'timeout 30 docker manifest inspect <image>' resolve? Unresolvable container = BLOCKER.
6. Header/comment accuracy: do launch instructions in the comments reference cluster names that actually exist on this host (compare against the clusters list above)? Deprecated flags ('--solo' is deprecated in sparkrun, use --tp N)? Wrong IPs/users? Stale claims = warning.
7. Topology: min_nodes/max_nodes and tensor_parallel vs the number of live, reachable cluster hosts. A recipe needing more nodes than are reachable = blocker.
8. Cache: is the primary model in the head's HF cache (list above)? Missing required second models (drafters the serve command references) = warning.
9. Render test: sparkrun run ${DIR}/${file} --tp <recipe's tensor_parallel> --dry-run --no-follow  — confirm the serve command renders with all placeholders substituted and any JSON args (e.g. --speculative-config) intact. THE --dry-run FLAG IS MANDATORY.
10. Entrypoint compatibility (dry-run CANNOT catch this; a real launch dies with exit 126): if the image is available locally, run docker inspect --format '{{json .Config.Entrypoint}}' <image>. sparkrun launches containers with its own 'bash -c <serve cmd>' as the container COMMAND, so an image ENTRYPOINT that is not a passthrough wrapper (like nvidia_entrypoint.sh / tini that exec "$@") gets the bash command appended to it and breaks (e.g. ENTRYPOINT ["/bin/bash"] -> 'bash /usr/bin/bash -c ...' -> exit 126; ENTRYPOINT ["vllm","serve"] -> garbage args). If the ENTRYPOINT is non-null and non-passthrough AND the recipe does NOT set 'executor_config: {entrypoint: ""}' (which clears it), that is a BLOCKER; the fix is adding that executor_config block.

Severity guide: blocker = will not launch/boot; warning = launches but a documented step or claim is wrong/missing; info = advisory only.
Return ONLY the structured object; put exact command output snippets in 'evidence'.`,
      { schema: RECIPE_SCHEMA, label: `validate:${file}`, phase: 'Validate' }
    ),
  (report, file) => {
    if (!report) return null
    if (!report.issues || report.issues.length === 0) return report
    return parallel(
      report.issues.map((issue) => () =>
        agent(
          `You are an adversarial skeptic. A validator claims this issue in sparkrun recipe ${DIR}/${file}:
${JSON.stringify(issue, null, 2)}

Independently RE-CHECK the claim on the live host with your own commands and try to REFUTE it. Do not trust the validator's evidence — reproduce it.
${SAFETY}

Host facts for reference: ${JSON.stringify(host)}

refuted=true if the issue does not hold up (wrong, already fixed, or based on a misread). refuted=false only if you reproduced the evidence yourself. If real but mis-ranked, set correctedSeverity.`,
          { schema: VERDICT_SCHEMA, label: `verify:${file}`, phase: 'Verify' }
        ).then((v) => ({
          ...issue,
          refuted: v ? v.refuted : null,
          verifyReason: v ? v.reason : 'verifier unavailable — treating as unconfirmed',
          severity: v && v.correctedSeverity ? v.correctedSeverity : issue.severity,
        }))
      )
    ).then((verified) => ({ ...report, issues: verified.filter(Boolean) }))
  }
)

const reports = results.filter(Boolean)
const confirmed = reports.flatMap((r) =>
  (r.issues || []).filter((i) => i.refuted === false).map((i) => ({ recipe: r.recipe, ...i }))
)
const refutedCount = reports.reduce((n, r) => n + (r.issues || []).filter((i) => i.refuted === true).length, 0)
log(`${reports.length}/${host.recipeFiles.length} recipes validated — ${confirmed.length} confirmed issues, ${refutedCount} refuted`)
if (reports.length < host.recipeFiles.length) {
  log(`WARNING: ${host.recipeFiles.length - reports.length} recipe validator(s) died — their recipes are NOT certified`)
}

phase('Audit')

const AUDIT_SCHEMA = {
  type: 'object',
  required: ['complete', 'gaps'],
  properties: {
    complete: { type: 'boolean' },
    gaps: { type: 'array', items: { type: 'string' } },
  },
}

const audit = await agent(
  `You are a completeness critic for a sparkrun recipe validation run over ${DIR}.
${SAFETY}

The run claims to have validated these recipes: ${JSON.stringify(reports.map((r) => r.recipe))}
Against host facts: ${JSON.stringify(host)}
Confirmed issues: ${JSON.stringify(confirmed)}

Check for GAPS, with fresh commands where needed:
1. ls ${DIR} — any *.yaml/*.yml recipe file (has model: + runtime:) that is missing from the validated list?
2. Any recipe whose report is missing a dimension (no vram check, no container check, no dry-run render)? Reports: ${JSON.stringify(reports.map((r) => ({ recipe: r.recipe, vramFit: r.vramFit, containerStatus: r.containerStatus, dryRunRendered: r.dryRunRendered })))}
3. Any cluster host in the sparkrun config that was never reachability-tested?
List every gap found; complete=true only if there are none.`,
  { schema: AUDIT_SCHEMA, label: 'completeness-critic', phase: 'Audit' }
)

return {
  host,
  reports,
  confirmedIssues: confirmed,
  refutedIssueCount: refutedCount,
  audit: audit || { complete: false, gaps: ['audit agent unavailable'] },
}
