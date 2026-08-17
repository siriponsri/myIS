---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "6dbb1ccd555cfe39e52a3c6e16414da3d6fe2875127cc046e83b29b5fe560ff7"
read_model_sha256: "837b6e327f12b9273f6bee55d1d185fd946245f02ce62dd9d107a4449233b5ff"
source_commit: "69644e66678776dd15f0976974cf6576462eb209"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: ["03b2bce9ab001e2ce4a0fff218ac4dead89f9107cb64173fe56291a780bebb8c","b9c04d3fa753bbc1dcd53e29c9c9c15696fe4b1a946823f7f981d34d9a2eed9d"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "aggregate_safe_synthetic_runtime_preparation"
scientific_authority: false
claim_boundary: "This is a synthetic adapter-level preparation check. It contains no protected source text, query identifiers, memberships, qrels, rankings, per-query outcomes, credentials, raw provider payloads, or A1 retrieval result."
generated_from_revision: "6dbb1ccd555cfe39e52a3c6e16414da3d6fe2875127cc046e83b29b5fe560ff7"
last_material_update: "2026-08-17T21:26:45Z"
next_authorized_action: "Commit and push the hash-bound repair, build a clean v16 bundle, re-run provider admission and execution adoption, then resume only the frozen 25/25 A1.2 screen."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-17T21:26:45Z"
updated_at: "2026-08-17T21:26:45Z"
note_id: "A1-2-EXACT-TOKEN-ID-ADAPTER-PROBE"
note_type: "history_report"
phase_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING"
task_id: "A1.2"
workflow_status: "complete"
evidence_maturity: "engineering"
claim_level: "none"
---

# A1.2 v16 Exact-Token-ID Adapter Probe

## Objective

Validate the additive exact-token-ID transport repair at adapter level before resuming the frozen A1.2 screen.

## Starting State

Attempt `a12-v16-r8` stopped before measured retrieval because overflow windows could not safely survive tokenizer decode/re-tokenize round-tripping.

## Inputs and Frozen Bindings

- Audit: `outputs/audits/rigor/a1.2-v16-exact-token-id-adapter-probe-20260809.json` (`03b2bce9ab001e2ce4a0fff218ac4dead89f9107cb64173fe56291a780bebb8c`)
- Repair executor hash: `f3ae2fb2abf29e85f0a3ecfc619e6b2d3f4a8d5981a8429d1ae0512deaa4abce`
- Materializer bridge hash: `1195a2df11531714ae1503e94450d3f3e6b1257a4198762ab93533307e97d05f`

## Work Performed

The compiler-planned full token IDs were retained in Owner-local runtime memory and passed directly through the frozen SentenceTransformer path. The probe covered ARM-02 through ARM-05 without protected input access or retrieval.

## Artifacts Produced

- Aggregate-safe audit file: `outputs/audits/rigor/a1.2-v16-exact-token-id-adapter-probe-20260809.json` (`b9c04d3fa753bbc1dcd53e29c9c9c15696fe4b1a946823f7f981d34d9a2eed9d`)

## Metrics

| Arm | Status | Windows | Dimension | Finite |
|---|---|---:|---:|---|
| `ARM-02` | `PASS` | 2 | 1024 | `True` |
| `ARM-03` | `PASS` | 5 | 1024 | `True` |
| `ARM-04` | `PASS` | 2 | 768 | `True` |
| `ARM-05` | `PASS` | 2 | 1024 | `True` |

## Result

`PASS_PRE_MEASUREMENT`. All four dense adapter probes passed with exact token-ID windows and finite embeddings.

## Interpretation

This is an adapter-level synthetic preparation check; it does not establish encoder parity, retrieval quality, latency, cost, or publication impact.

## Supported Claims

The additive transport repair preserves the frozen scientific semantics and avoids lossy token-ID round-tripping for the tested synthetic inputs.

## Unsupported Claims

No measured A1 result, provider admission, execution adoption, Selection, Final, or publication claim is authorized.

## Failures and Recovery

The r8 overflow transport failure is retained as the trigger; recovery is additive exact-token-ID transport and remains pre-measurement.

## Governance and Safety

Protected inputs were not accessed, instance identity was preserved, measured retrieval did not start, and provider admission/adoption remain false.

## Decision

Accept the synthetic probe as preparation evidence only; keep the frozen 25/25 A1.2 screen gated on fresh provider admission and execution adoption.

## Next Action

Commit and push the hash-bound repair, build a clean v16 bundle, re-run provider admission and execution adoption, then resume only the frozen 25/25 A1.2 screen.

## Evidence Links

- Audit: `outputs/audits/rigor/a1.2-v16-exact-token-id-adapter-probe-20260809.json`
