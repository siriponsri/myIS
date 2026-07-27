# Literature Evidence

`validated-digests/` contains frozen imported digests U001-U040 and the
authorized U041-U153 metadata/full-text-section triage digests. The frozen
U001-U040 bytes remain validated by `IMPORT_MANIFEST.csv`.

`catalog/corpus_manifest.csv` is the one-row-per-unique-PDF index.
DOI and arXiv fields include evidence-source and confidence columns; accepted
identifiers come only from acquisition URLs, PDF metadata, or labeled
first-page front matter, never from bibliographies.
`catalog/legacy_aliases.csv` preserves all 169 historical App paths, including
16 exact-duplicate groups, after the App copies are removed.
`catalog/tier_assignments.csv` is the canonical A/B/C/N classification; the
four `tier_*.csv` files mirror the physical tier folders without duplicating
PDF bytes.

Raw PDFs are local-only canonical files under
`01_evidence/<A|B|C|N>-tier/Uxxx_<verified-title-slug>.pdf`. PDF files in all
four tier folders are ignored by Git; SHA-256 remains the byte-identity
authority in the manifest. Historical SHA-store paths are provenance only and
the catalog is the current locator. `qa-provenance/` contains identity, build,
migration, and historical QA records.
