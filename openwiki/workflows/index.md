# Files

- [Authoring & Changing Recipes](authoring-recipes.md) - How to add or change a recipe in this registry — search upstream first, copy with attribution and minimal changes, apply the image policy, keep one canonical copy, and publish by committing to main and refreshing the registry.
- [Benchmarking & Context Verification](benchmarking.md) - How recipes get measured — the canonical quick throughput ladder, the needle-in-haystack full-context harness, the mem/results artifacts (the ground truth since nvidia-smi reports N/A on GB10), and the INDEX/benchmarks recording convention.
- [Launching & Verifying a Recipe](launching-and-verifying.md) - The launch-to-verified path — lint, dry-run fit check, run with --no-follow, inline HF_TOKEN for gated repos, poll readiness against the in-container serve log, and clear the verified bar by making the model answer a request.
