# Note Contract

## Required frontmatter

`schema_version`, `note_id`, `note_type`, `track`, `phase`, `task`, `gate`,
`status`, `evidence_level`, `git_commit`, `source_paths`, and `agent_generated`
are required. `source_paths` must point to public repository documents or safe
aggregate metadata. Protected markers such as `qrels`, `membership`, and
`per_query` are rejected.

## Beginner closeout fields

Use these headings in a handoff or status note:

- สถานะตอนนี้: Phase, Task, Gate, and whether the Gate is pending, blocked, or ready for Owner decision.
- สิ่งที่ทำแล้ว: short method and evidence summary.
- สิ่งที่ Owner ต้องทำ: explicit actions, never implied approval.
- สิ่งที่จะขอจาก Owner: provider, compute, margin, budget, provenance, freeze, or exception decisions.
- ทรัพยากร Phase ถัดไป: CPU/GPU, time, cost, network/egress, and storage requirements.
- ขอบเขตที่ยังไม่แตะ: protected data, qrels, paid APIs, GPU, confirmation, and publication surfaces.
