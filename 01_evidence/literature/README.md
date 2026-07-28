# Literature Evidence

This tree preserves source identity, provenance, license/privacy status, aliases,
digests, and QA records for IS1 Research V0.1. Historical records may retain the
legacy name `Paper E`; do not rewrite them merely to match the active identity.

`validated-digests/` contains frozen imported U001-U040 digests and authorized
U041-U153 triage digests. `catalog/corpus_manifest.csv` is the unique-PDF index;
`catalog/legacy_aliases.csv` preserves historical paths and duplicate groups;
`catalog/tier_assignments.csv` is the canonical A/B/C/N classification.

Raw PDFs are local-only under the tier roots and are ignored by Git. SHA-256 is
the byte identity authority. PDFs must not be committed or mirrored to MLflow
until license/privacy review explicitly permits a different treatment. The
loopback viewer defaults to metadata/digests and streams only an exact
Owner-approved path/hash allowlist while writing a local tamper-evident access
receipt.

`qa-provenance/` contains identity, build, migration, and historical QA records.
Do not edit/delete these records during active-doc migration. The three BATCH_2A
hash decisions require producer/source provenance and semantic validation; never
update an expected hash solely to make a validator green.

Literature digests and evidence records retain source URI, version/date,
license/privacy status, content hash, retrieval/acquisition provenance, and
claim-to-source pointers. Brain and MLflow may hold allowlisted summaries or
pointers, but Git/validated evidence remains canonical.
