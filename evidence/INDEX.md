# Evidence Index

Active literature evidence is owned by `evidence/literature/` and registered by
U-ID, path, and SHA-256. `U154` is the current AutoIndex Tier A source; its PDF
and digest are local, reproducible artifacts. Historical U001-U153 digests remain
reachable through explicit `archive/legacy-cs/` pointers until their source-byte
store is re-bound.

Protected and large artifacts remain outside Git under `MYIS_STORE`.
# Evidence Index

Canonical evidence is hash-bound and additive. Protected raw data remains in
the Owner-local store. Known missing evidence is represented by typed receipts
under `evidence/known-missing/` and never silently fabricated.

- Literature: `evidence/literature/`
- Known missing: `evidence/known-missing/`
- Run facts: `campaigns/scope-autoindex-v1/manifests/`
