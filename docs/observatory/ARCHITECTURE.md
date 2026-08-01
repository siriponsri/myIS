# Research Evidence Observatory

The Observatory is an engineering-only evidence layer for future myIS runs. It
records a complete, hash-bound lifecycle while keeping the repository safe for
review and publication work.

## Two storage tiers

```text
future run -> capture session -> Owner-local vault (full content)
                       \
                        -> repository-safe registry (hashes, counts, pointers)
```

The Owner-local vault is represented by a caller-supplied root and is never
opened by the repository projection. The repository registry contains only
aggregate metadata, safe relative URIs, canonical hashes, and narrative
summaries. It must not contain query IDs, split membership, per-query outcomes,
credentials, raw provider payloads, or absolute personal paths.

## Record families

The engineering namespace is `myis.observatory-*.v1`. A registry binds request,
run, candidate, prompt, schema/config/environment, artifact, metric, result,
interpretation, decision, failure, recovery, and append-only event records.
Every record has a stable ID and a record hash. Parent references are hashes or
stable IDs, never filesystem paths.

## Lifecycle

1. `CaptureSession.start()` freezes request/config/environment bindings and
   records a planned run.
2. `event()` appends deterministic lifecycle events and updates stage/status.
3. `register_artifact()` and the typed helpers register safe records with
   content hashes before they can be promoted.
4. `finish()` validates the graph, checksums, metrics, and claim boundary and
   emits a final receipt.
5. `fail()` preserves a sanitized failure/recovery record without promoting
   incomplete metrics.

The fixture uses a fixed timestamp and synthetic IDs so a second run produces
the same canonical registry and receipt hashes.

## Evidence classes

`fixture` and `dry_run` are engineering evidence. They are useful for proving
capture and projection behavior but cannot support a scientific claim. Only a
future validated measured record may use a measured evidence class, and that
record must bind its immutable receipt. The Dashboard makes this distinction
visible as **Engineering evidence**, **Scientific evidence**, and **Not yet
measured**.

## Projection contract

The shared read model receives one additive `observatory` object. Dashboard,
MLflow, Obsidian, and presentation views consume that same object and expose its
revision. No projection writes source records or invents metrics.

## Local commands

```powershell
python -m myis_research.observatory.fixture --root . --check
pytest -q tests/test_observatory.py
```

The fixture writes only `outputs/observatory/fixture-v1/`. It does not change
P2 counters, open selection, access protected stores, or run a measured P2.
