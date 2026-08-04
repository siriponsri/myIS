# Data and Evidence Boundary

Owner-local protected storage contains qrels, split membership, query IDs,
family IDs, per-query outcomes, rankings, raw patent payloads, provider
payloads, and credentials. These bytes must never enter Git, MLflow artifacts,
the Research Brain, Obsidian, the Dashboard, Paper, prompts, or logs.

Repository-safe artifacts may contain validated aggregate metrics, counts,
costs, latency distributions, safe IDs, SHA-256 commitments, claim boundaries,
and repository-relative or typed external pointers. Every numeric research fact
must resolve to a validated aggregate receipt; projections may not recompute it.

During migration, measured retrieval, REP-DEV, HARNESS-DEV, Selection, and
Final are closed. Synthetic fixtures must be clearly marked non-scientific.
