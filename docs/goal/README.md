# Goal Documents

## Current goal registry

| Goal document | Lifecycle | Status | Authorized use |
|---|---|---|---|
| [A4_PRODUCTION_TRANSFER_AND_SELECTION_goal_001.md](A4_PRODUCTION_TRANSFER_AND_SELECTION_goal_001.md) | `CLOSED` | `CLOSED_WITH_EVIDENCE_SELECTION_HANDOFF_BLOCKED` | Complete A4 evidence; use the [Selection-125 Owner handoff](../operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md), then consume Selection at most once |
| [A5_FINAL_CONFIRMATION_goal_001.md](A5_FINAL_CONFIRMATION_goal_001.md) | `BLOCKED` | `BLOCKED_PRESELECTION_HANDOFF_AND_D2` | Tier-1 frozen two-system Final-872 confirmation; waits for validated handoff and `D2_OPEN_FINAL` or a hash-bound conditional receipt |
| [A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md](A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md) | `BLOCKED` | `BLOCKED_A5_CLOSEOUT` | Tier-1 post-confirmatory materialization of exactly one A5-frozen winner over full DAPFAM; operational scalability only |
| [A7_PUBLICATION_AND_RELEASE_goal_001.md](A7_PUBLICATION_AND_RELEASE_goal_001.md) | `BLOCKED` | `BLOCKED_OWNER_D3` | Publication and release from validated aggregate-safe A0-A6 evidence after `D3_SUBMIT_RELEASE` |

## Historical goal registry

| Goal document | Lifecycle | Status | Authorized use |
|---|---|---|---|
| [A1_2_goal.md](A1_2_goal.md) | `CLOSED` | `HISTORICAL_SUPERSEDED_BY_A1_2_RERUN_GOAL` | ประวัติ fail-closed ของ r13 เท่านั้น |
| [A1_2_rerun_goal.md](A1_2_rerun_goal.md) | `CLOSED` | `CLOSED_PASS` | หลักฐานส่งต่อ A1.2 r15; ห้าม launch ซ้ำ |
| [A2_official_codex_bridge_goal.md](A2_official_codex_bridge_goal.md) | `CLOSED` | `CLOSED_PASS` | Historical bridge and candidate freeze; preserved for provenance only |
| [A2_PER_ARM_AUTOINDEX_goal_004.md](A2_PER_ARM_AUTOINDEX_goal_004.md) | `CLOSED` | `CLOSED_PASS_A2_EXECUTION_CLOSEOUT` | Measured A2 closeout; preserved as immutable predecessor evidence |
| [A2_PER_ARM_AUTOINDEX_goal_001.md](A2_PER_ARM_AUTOINDEX_goal_001.md) | `CLOSED` | `HISTORICAL_PRELAUNCH_STOP` | Historical cyclic-provenance prelaunch stop |
| [A2_PER_ARM_AUTOINDEX_goal_002.md](A2_PER_ARM_AUTOINDEX_goal_002.md) | `CLOSED` | `HISTORICAL_PRELAUNCH_AUTHORITY_CONTRADICTION` | Historical v2 prelaunch stop; never reuse for execution |

## Documentation backlog disposition (2026-08-20)

- The A2 handoff chain is retained in place: audits `001`-`012`, implementation
  handoffs `im_001_001` through `im_010_001`, and long-run handoffs `lo_001_001`
  through `lo_003_001` remain readable provenance. They are referenced by the
  canonical source-of-truth record, validators, or successor documents, so none
  qualifies for archival under `docs/observatory/REPORTING_POLICY.md`.
- Goal 003 is the terminal record for the stopped A2 attempt. It must not be
  resumed or reused. Its attempt identity and receipts are closed lineage.
- Goal 004 completed the successor A2 measured closeout and is now immutable
  predecessor evidence. It must not be launched again or used as the A4
  attempt/root/receipt lineage.
- A4 Goal 001 is closed with evidence for the current `contract_only_ready`
  A4 handoff. It owns the recorded attempt lineage, measured production
  profiles, safe return, and Selection-handoff blocker:

  `docs/long_run/A4_PRODUCTION_TRANSFER_AND_SELECTION_lo_001_001.md`
- A5 Goal 001 is a separate handoff. It remains blocked until the missing
  hash-bound Selection-125 evaluator input is supplied and validated, followed
  by `D2_OPEN_FINAL` or the Owner's explicit hash-bound conditional auto-pass
  receipt after a complete, audited A4 PASS; its bundle may contain hashes,
  counts, receipts, and opaque pointers but never raw protected Final payloads.
- The current Owner input contract is
  `docs/operations/A4_SELECTION_125_OWNER_HANDOFF_20260820.md`. It is the only
  valid route for clearing the Selection blocker; HDEV-100 cannot substitute
  for Selection-125 vectors.
- A5/A6 code parity may be checked on the existing instance in a fresh
  non-measured code-check root. Measured A5 and A6 attempts require separate
  fresh roots and admissions even when instance `47790578` is reused.
- The approved continuation mode is conditional auto-continue with minimal
  receipt transitions: routine engineering faults are repaired internally;
  the real Selection-125 handoff remains the single pre-Selection Owner-input
  stop, and A5/A6 still fail closed on scientific, protected-data, budget,
  provider, or evidence-integrity boundaries.
- Generated Obsidian/report projections are rebuilt from the shared read model;
  no generated Markdown is edited by hand. No publication figure is generated
  from the stopped pre-authority attempt.

เมื่อ canonical receipt/ledger/checkpoint ยืนยันการปิดงาน ให้แก้ทั้ง frontmatter,
ตารางสถานะรายขั้น และทะเบียนนี้ใน session เดียวกัน ห้ามปิด goal จาก chat หรือ
preview เพียงอย่างเดียว

ทุกไฟล์ active `docs/goal/*_goal.md` เป็นคู่มือปฏิบัติงานแบบ executable สำหรับ long run
ไม่ใช่บันทึกความคืบหน้าหรือแหล่งตัวเลขวิทยาศาสตร์ ให้เริ่มงานด้วยคำสั่งนี้:

```text
/goal อ่าน docs/goal/<ชื่อไฟล์>.md แล้วทำงานตามขั้นตอนทั้งหมด
```

คู่มือ active แต่ละไฟล์ต้องอ่านแล้วทำงานต่อได้โดยไม่ต้องถามซ้ำ โดยต้องมีอย่างน้อย:

1. เป้าหมายเชิง publication และเกณฑ์ความสำเร็จที่ตรวจได้
2. สถานะเริ่มต้น, input/control ที่ freeze, และขอบเขต engineering ที่แก้ได้
3. ขั้นตอน numbered แบบทีละขั้น พร้อม checkpoint หลังช่วงสำคัญ
4. artifact ที่ต้องสร้าง, ตำแหน่งจัดเก็บ, hash/receipt และ validation command
5. recovery ที่อนุญาต, hard stop/fail-closed และข้อมูลที่ห้ามเผยแพร่
6. ขั้นตอน closeout, commit/push, รายงาน terminal และ next action

คำว่า checkpoint ใน goal เป็นจุดตรวจและบันทึกความคืบหน้าเท่านั้น ไม่ใช่
micro-gate ใหม่และไม่เพิ่มอำนาจ launch; การอนุญาตยังยึด canonical controls,
schemas, manifests และ receipts เดิม

กฎการเลือกไฟล์:

- session วางแผนใช้ reasoning สูงสร้างหรือปรับ goal เมื่อ phase/task หรือ
  objective เปลี่ยนอย่างมีสาระ
- session implement อ่าน goal ที่สั่ง, `PLAN.md`, และ control เฉพาะที่จำเป็น
  แล้วทำตาม numbered steps จนจบหรือหยุดตาม hard stop
- ใช้ runbook/ledger และ canonical receipts เป็นหลักฐานถาวร; goal เปลี่ยน
  เฉพาะเมื่อมี decision, blocker, recovery หรือ closeout ที่มีสาระ

active campaign, schemas, manifests, receipts และ protected Owner-local
evidence ยังคงเป็น canonical ห้ามใส่ raw protected data, ranking, qrels,
credentials, token หรือ provider payload ใน goal, Git, report หรือ projection
ไฟล์ที่มี `status: HISTORICAL_SUPERSEDED_*` เป็น redirect/history เท่านั้น
ห้ามใช้ launch และต้องชี้ไปยัง goal active ล่าสุด คู่มือมุ่งหลักฐานที่เพิ่ม publication impact เช่น measured coverage ครบ,
deterministic provenance, aggregate-safe artifacts และ claim boundary ที่ชัด
ไม่ใช่การเพิ่มปริมาณเอกสาร

ทุก goal ต้องมี `lifecycle: ACTIVE | BLOCKED | CLOSED` ใน frontmatter และ goal
ที่กำลังทำต้องมีตารางสถานะขั้นงานใกล้ต้นไฟล์ ใช้สถานะ `COMPLETE`,
`IN_PROGRESS`, `IMPLEMENTED_PENDING_RESULT`, `PENDING` หรือ `BLOCKED` เท่านั้น
อัปเดตจาก canonical receipt/ledger/checkpoint ที่ตรวจแล้ว ไม่ยกสถานะจาก chat,
preview หรือไฟล์ที่เพียงเตรียม implementation ไว้ งานที่ปิดหรือถูก supersede ต้อง
เปลี่ยน `lifecycle` ใน session เดียวกัน ส่วนตัวเลขวิทยาศาสตร์ยังอ้าง canonical
artifact เท่านั้น ห้ามคัดลอกเป็น numeric source of truth ชุดที่สองใน goal
