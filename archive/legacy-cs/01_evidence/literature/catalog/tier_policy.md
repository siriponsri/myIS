# Literature Tier Policy

The tier is a research-priority index, not a quality score and not a statement
that every claim in a source has been independently validated.

| Tier | Use |
|---|---|
| A | Direct evidence for patent retrieval, ranking, patent representations, governed prompt/skill optimization, or the primary benchmarks used by those methods. |
| B | Transferable retrieval, RAG, knowledge-graph, evaluation, uncertainty, cross-lingual, Thai/legal, or adjacent method evidence. |
| C | Domain context, classification/extraction, model/system background, surveys, and sources without a direct experimental bridge to the active tracks. |
| N | Non-literature templates and confirmed acquisition mismatches. Retained for provenance; excluded from research synthesis until replaced or deliberately reclassified. |

`tier_assignments.csv` is canonical. `tier_A.csv`, `tier_B.csv`, `tier_C.csv`,
and `tier_N.csv` are generated index views of the matching physical folders
under `01_evidence/<A|B|C|N>-tier/`. Each U-ID has exactly one PDF.

U001-U040 retain their frozen digest tier assignments. U041-U153 were assigned
from verified PDF identity plus full-text abstract/conclusion/topic scans. A
numeric or comparative claim still requires page-level verification against the
canonical tier PDF identified by U-ID and SHA-256.
