# Note Contract

## Required frontmatter

Generated notes use `myis.obsidian-note.v2`. The shared report validator
requires `schema_version`, `note_id`, `note_type`, `workflow_status`,
`evidence_maturity`, `claim_level`, `safe_to_present`, `managed_by`,
`edit_policy`, `read_model_revision`, `read_model_sha256`, `source_commit`,
`projection_schema_version`, `source_run_ids`, `source_manifest_sha256`,
`related_literature_ids`, and `related_decision_ids`. Source pointers must be
public repository documents or safe aggregate metadata; protected markers such
as `qrels`, `membership`, and `per_query` are rejected.

## Beginner closeout fields

Use these headings in a handoff or status note:

- สถานะตอนนี้: Phase, Task, Gate, and whether the Gate is pending, blocked, or ready for Owner decision.
- สิ่งที่ทำแล้ว: short method and evidence summary.
- สิ่งที่ Owner ต้องทำ: explicit actions, never implied approval.
- สิ่งที่จะขอจาก Owner: provider, compute, margin, budget, provenance, freeze, or exception decisions.
- ทรัพยากร Phase ถัดไป: CPU/GPU, time, cost, network/egress, and storage requirements.
- ขอบเขตที่ยังไม่แตะ: protected data, qrels, paid APIs, GPU, confirmation, and publication surfaces.
