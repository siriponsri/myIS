---
name: myis-autoresearch-notes
description: Build and maintain Thai-first, beginner-readable research notes and implementation handoffs from safe repository metadata. Use after CPU/GPU sprints, protocol repairs, dashboard work, or before commit/push when the Owner needs a clear status, evidence, Gate request, and next-action summary.
---

# Research Notes Workflow

Use this skill when a myIS session needs a durable explanation of what the
agent did, what is blocked, what the evidence means, and what the Owner must
decide. It is a projection workflow: Git, validated manifests, and immutable
Gate records remain authoritative.

## Workflow

1. Read `PLAN.md`, the active task files, the latest valid session capsule, and
   `HANDOFF.md`.
2. Run `myis-assets validate --mode quick` and the task-specific asset query.
3. Separate fixture, development, descriptive, and confirmation evidence.
   Never place qrels, protected IDs, membership, per-query outcomes, or
   credentials in a note.
4. Write or regenerate a note under `07_obsidian_note/generated/` with a YAML
   frontmatter contract and a Thai-first body. Explain difficult English terms
   in plain Thai on first use.
5. Close every implementation session with Phase, Task, Gate, status, checks,
   changed files, untouched protected surfaces, Owner actions, requested
   Owner decisions, and next-phase resources.
6. Validate the catalog, Dashboard response, session capsule, and `HANDOFF.md`
   before commit/push. If Brain cannot be updated through its serial-writer
   lease, stop before commit/push.

## Note contract

Generated notes must use `myis.research-note.v1`, contain only allowlisted source
paths, stay below 512 KiB, and expose pathless `obsidian://` links. Use the
repository helper:

```powershell
uv run --no-sync python -m myis_research.notes.cli build --repository-root .
uv run --no-sync python -m myis_research.notes.cli validate --repository-root .
```

See [note-contract.md](references/note-contract.md) for the field meanings and
the Owner-readable closeout template.

## GPU handoff rule

After a GPU Sprint, pull and validate all allowlisted artifacts locally, stop
remote processes, record local metrics/MLflow-safe artifacts and manifests,
then stop and tell the Owner:

> บันทึกข้อมูลครบทุกอย่างแล้ว เสนอ Owner destroy Vast Instance ทันที หลังจากนั้น ให้ Owner พิมพ์ “ดำเนินการต่อ” เพื่อทำงานต่อบน local project ครับ

Do not continue until the Owner confirms destruction and types `ดำเนินการต่อ`.
