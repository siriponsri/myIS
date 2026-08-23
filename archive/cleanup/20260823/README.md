# Temporary-file cleanup (2026-08-23)

The corresponding temporary investigation files removed from the `01_Research`
working root during the A6 pre-run hygiene audit are preserved in the
Owner Store at
`04_Owner_Stores/armindex/archive/cleanup/20260823/`. The files were
untracked, had no repository references, and were not canonical scientific
evidence, receipts, manifests, protected payloads, or failed-attempt outputs.

The tracked directory contains only this audit record and manifest; the
diagnostic payload remains Owner-local and non-distributable. It is retained
for forensic reproducibility and can be removed only after
the active A6 attempt has reached result-integrity closeout.

See `manifest.json` for original paths, SHA-256 hashes, sizes, and disposition.

Regenerable Python/test/tool caches were audited separately and removed from
the active workspaces. The aggregate counts and exclusions are recorded in
`cache_cleanup_manifest.json`; no canonical evidence, protected payload, or
active A6 transfer root was touched.
