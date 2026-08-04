# Production Profiles

| Profile | Arm policy | Runtime | Intended use | State |
|---|---|---|---|---|
| `FAST` | BM25 plus at most one commercial dense arm | bounded synchronous, one escalation | interactive retrieval | contract only |
| `BALANCED` | two or three commercial-capable arms | synchronous only if p95 passes | production RAG | contract only |
| `DEEP` | full selected research or commercial harness | asynchronous permitted | audit and deep search | contract only |

Profiles are frozen only from measured Pareto-frontier evidence. A profile must
bind its arm set, invocation order, depths, fusion, thresholds, caching,
fallbacks, latency/cost ceilings, representation hashes, and harness hash.
PatEmbed-large cannot enter a commercial profile automatically.
