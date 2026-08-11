---
title: "A1.2 เป้าหมายการรันระยะยาว"
phase_id: A1_BASELINES_AND_MULTI_ARM_SCREENING
task_id: A1.2
status: HISTORICAL_SUPERSEDED_BY_A1_2_RERUN_GOAL
lifecycle: CLOSED
evidence_class: aggregate_safe_live_attempt_failure
scientific_authority: false
claim_boundary: "เอกสารนี้บันทึกแผนปฏิบัติการและ failure state แบบ aggregate-safe ไม่ใช่ผลการทดลองหรือแหล่งตัวเลขอ้างอิง"
last_material_update: 2026-08-12
next_authorized_action: READ_A2_GOAL
---

> ประวัติ r13 แบบ fail-closed เท่านั้น ห้ามใช้เป็นแผน launch หรือรวม partial
> result ข้าม attempt การ rerun ใน [A1_2_rerun_goal.md](A1_2_rerun_goal.md)
> ปิด `PASS` แล้ว งานถัดไปใช้ [A2_goal.md](A2_goal.md)

# A1.2 historical redirect

r13 หยุดแบบ fail-closed ที่ `24/25`; cell ที่ขาดคือ
`ARM-05--P04-SECTION-MULTIVIEW`. Instance `47256937` ถูกทำลายแล้ว ผลบางส่วน
ไม่มี scientific authority และห้ามนำมารวมกับ attempt ใหม่

หลักฐาน aggregate-safe อยู่ที่
`outputs/audits/armindex/a1.2-v16-r13-failure-audit-20260810.json` ส่วน A1.2
rerun ปิด `PASS` แล้วตาม [A1_2_rerun_goal.md](A1_2_rerun_goal.md) และ goal active
ถัดไปคือ [A2_goal.md](A2_goal.md)
