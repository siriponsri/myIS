---
title: "รายงานความก้าวหน้า ArmIndex: A0 ถึง A2"
audience: "อาจารย์ที่ปรึกษา"
language: "th"
report_date: "2026-08-16"
reporting_cutoff_utc: "2026-08-16T14:09:47Z"
status: "A0 complete; A1 complete with measured REP-DEV evidence; A2 active with result pending closeout"
numeric_authority: "A0 audit receipts and A1 validated aggregate receipts; A2 contains aggregate-safe live telemetry only"
a2_update_rule: "เติมผล A2 ได้เมื่อ exact coverage, safe return, execution closeout, and result-integrity audit ผ่านครบเท่านั้น"
protected_data: "No qrels, membership, query identifier, ranking, per-query outcome, credential, or raw provider payload"
---

# รายงานความก้าวหน้า ArmIndex: A0 ถึง A2

## สรุปสำหรับอาจารย์

งาน ArmIndex ศึกษาว่า **วิธีสร้าง representation ของเอกสารสิทธิบัตรควรเลือกให้เหมาะกับ retriever แต่ละชนิดหรือไม่** และในระยะถัดไปการถ่ายโอน representation ข้าม retriever จะให้จุดสมดุลด้านคุณภาพ ความเร็ว และต้นทุนที่ดีกว่าหรือไม่ การทดลองถูกออกแบบเป็นลำดับขั้นเพื่อไม่ให้การเลือกในระยะต้นปะปนกับผลยืนยันในระยะหลัง

สถานะ ณ จุดตัดรายงานคือ:

| Phase | สถานะ | หลักฐานที่ใช้รายงานได้ | ข้อสรุประดับที่ปรึกษา |
|---|---|---|---|
| A0_MIGRATION_FOUNDATION | เสร็จ | Engineering validation | โครงสร้างการทดลอง, provenance, และขอบเขตข้อมูล protected พร้อมใช้งาน แต่ไม่มีผล retrieval คุณภาพใด ๆ |
| A1_BASELINES_AND_MULTI_ARM_SCREENING | เสร็จ | Measured aggregate บน REP-DEV | เปรียบเทียบ 5 retriever กับ 5 representation programs ครบ 25 cells; ARM-03 เด่นที่สุดใน aggregate quality |
| A2_PER_ARM_AUTOINDEX | กำลังรัน | Operational telemetry เท่านั้น | กำลังค้นหา representation ที่เหมาะเฉพาะแต่ละ arm; ยังไม่มี metric, winner, หรือ claim ที่ตีความได้ |
| A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT | เตรียมแล้ว แต่ยังไม่เริ่ม | Hash-only pending bundle | bundle ครบ 5 arms แต่ถูกล็อกไว้จนกว่า A2 จะ closeout ผ่าน |
| A4-A6 | ปิด | ไม่มีผล | Selection, Final และ release ยังไม่ถูกเปิด |

ข้อค้นพบที่รายงานได้ในขณะนี้มาจาก A1 เท่านั้น: ภายใต้ common representation programs เดียวกัน ARM-03 มีค่า OUT Recall@100 สูงสุด (`0.413400`), ตามด้วย ARM-05 (`0.363733`) และ ARM-04 (`0.340667`) ผลนี้เป็นหลักฐานบน development split (`REP-DEV`) สำหรับกำหนดงาน A2 ไม่ใช่ผลยืนยันบน Selection หรือ Final

## คำถามวิจัยและขอบเขตการวัด

| รายการ | ข้อตกลงที่ตรึงไว้ |
|---|---|
| หน่วยข้อมูลและหน่วยประเมิน | DAPFAM, patent family |
| Metric หลัก | OUT Recall@100 |
| Metric รอง | OUT nDCG@100 และ OUT nDCG@10 |
| Metric เชิงปฏิบัติการ | latency, throughput, charged cost, index size, RAM และ VRAM |
| บทบาทของผลในรายงานนี้ | REP-DEV เท่านั้น; ไม่เข้าถึง Selection หรือ Final |
| Retrievers | ARM-01 BM25, ARM-02 BGE-M3, ARM-03 PatEmbed, ARM-04 Arctic Embed, ARM-05 Qwen3 Embedding |
| วัตถุประสงค์ A1 | screen แบบ common representation: 5 programs x 5 arms = 25 logical cells |
| วัตถุประสงค์ A2 | AutoIndex แบบ per-arm ภายใน candidate universe ที่ตรึงแล้ว |

ARM-03 เป็น research/non-commercial arm ส่วน ARM-01, ARM-02, ARM-04 และ ARM-05 ถูกบันทึก license/provenance ไว้สำหรับการพิจารณาเชิงผลิตภัณฑ์ในระยะถัดไป ความแตกต่างนี้ไม่เปลี่ยนการเปรียบเทียบเชิงวิทยาศาสตร์บน REP-DEV

## A0: Migration Foundation

### เป้าหมายและสิ่งที่สร้างเสร็จ

A0 เป็นระยะสร้างฐานงานวิจัย ไม่ใช่ระยะสร้างผล retrieval โดยจัดระเบียบ authority, schema, manifest, receipt, report projection และเส้นแบ่งข้อมูล protected ก่อนเริ่มวัดจริง

| ช่วงงาน | สิ่งที่ส่งมอบ |
|---|---|
| A0.1-A0.2 | ย้าย repository/evidence และกำหนด canonical source of truth |
| A0.3-A0.5 | สร้าง Brain, read model, Obsidian, MLflow, Dashboard และลำดับ phase/Owner gate |
| A0.6-A0.7 | ตรึง scientific contract, schema, five-arm declaration และ license registry |
| A0.8 | ทำ CPU-only compute/storage feasibility fixtures |
| A0.9 | ปิด phase ด้วย validation, safety และ projection checks |
| A0.10 | เก็บเกี่ยว legacy code และจัด scaffolding ให้พร้อมสำหรับ phase ถัดไป |

### หลักฐานและความน่าเชื่อถือ

Receipt ปิด A0.9 มีสถานะ `PASS` และบันทึกว่า contract validation พบ 5 registered arms, 1 runnable fixture arm และ 4 dense arms ที่ยังไม่ถูกเปิดใน A0 ตามเจตนา การตรวจ focused ArmIndex ผ่าน 44 tests, full suite ผ่าน 387 tests, Dashboard/API policy ผ่าน 66 tests, asset registry มี error เท่ากับ 0, และไม่มี layout/read-model drift

A0.10 ได้รับ independent review ระดับ `ACCEPT` (mean score `4.33/5`) พร้อมหลักฐาน focused tests 20 ผ่าน, Ruff ผ่าน, report sync/check ผ่านโดยไม่มี drift, และตรวจ source components 14 ส่วนได้ครบ จุดสำคัญคือหลักฐานทุกส่วนใน A0 เป็น engineering/reproducibility evidence เท่านั้น

| ขอบเขตความปลอดภัย A0 | สถานะใน A0.9 receipt |
|---|---|
| Measured retrieval | 0 runs |
| GPU scientific run | 0 |
| Paid API | 0 |
| Protected payload | ไม่เปิด |
| Selection / Final | ไม่เปิด |
| Charged cost | USD 0 |

ดังนั้น A0 สนับสนุนคำกล่าวว่าโครงการมีระบบควบคุมและทำซ้ำได้ แต่ไม่สนับสนุนคำกล่าวด้าน retrieval quality หรือ superiority ของ model ใด

### หลักฐาน A0 สำหรับสไลด์

ไม่มี performance figure สำหรับ A0 เพราะไม่มี performance experiment สิ่งที่เหมาะกับสไลด์ methodology/rigor คือ:

| ใช้ประกอบสไลด์ | Path |
|---|---|
| A0.9 validation and safety closeout | [JSON receipt](../../outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json) |
| A0.10 independent acceptance | [JSON review](../../outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json) |
| A0.8 compute/storage fixture | [JSON receipt](../../outputs/fixtures/armindex/a0.8/compute-storage-v1/receipt.json) |

## A1: Baselines and Common Multi-Arm Screening

### การออกแบบ

A1 วัด retriever ทุก arm ด้วย representation programs เดียวกันครบทั้ง matrix เพื่อแยกผลของ retriever ออกจากผลของ representation โปรแกรมถูกตรึงใน `a1.2-common-five-programs-v11` และไม่อนุญาตให้ silent truncation หรือเปลี่ยน logical unitization ระหว่างการทดลอง

| Program | ความหมายที่ตรึงไว้ | Aggregation |
|---|---|---|
| P00-TAC-DOC | family document จาก title, abstract และ claims | single unit |
| P01-TA-DOC | family document จาก title และ abstract | single unit |
| P02-CLAIM1 | structured independent claim แรกตามลำดับที่กำหนด | maxP |
| P03-PASSAGE | logical token passages จาก title, abstract และ claims; window 384, stride 320, overlap 64 | maxP |
| P04-SECTION-MULTIVIEW | title, abstract และ claims เป็น 3 views | view-RRF, `k=60` |

ผล A1 ที่มี authority มาจาก terminal attempt `a12-v16-20260811-r15` ซึ่งมี coverage `25/25` และ charged attempt cost `USD 11.161632` ความหมายของตัวเลขในตารางต่อไปนี้คือค่าเฉลี่ยจาก 5 programs ต่อ arm ยกเว้น total wall time ซึ่งเป็นผลรวมของ 5 programs ต่อ arm

### ผล A1 ที่วัดแล้ว

| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Search p95 (ms) | Total wall time (s) |
|---|---:|---:|---:|---:|---:|
| ARM-01, BM25 lexical | 0.191200 | 0.172717 | 0.160011 | 441.520 | 762.533 |
| ARM-02, BGE-M3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | 19,847.315 |
| ARM-03, PatEmbed | 0.413400 | 0.347812 | 0.289856 | 212.062 | 29,444.640 |
| ARM-04, Arctic Embed | 0.340667 | 0.284546 | 0.235538 | 214.207 | 15,878.488 |
| ARM-05, Qwen3 Embedding | 0.363733 | 0.307930 | 0.256706 | 217.099 | 40,309.513 |

ข้อสังเกตที่รองรับด้วย aggregate evidence:

- ARM-03 สูงสุดทั้ง metric หลักและ metric รองทั้งสองตัว แต่เป็น research/non-commercial arm
- ARM-05 เป็นอันดับสองด้าน OUT Recall@100 และใช้ total wall time สูงสุดของ five-arm screen
- ARM-04 เป็น dense arm ที่ commercial-capable ซึ่งได้ quality แข็งแรงและ total wall time ต่ำสุดใน dense arms
- ARM-01 เป็น lexical CPU anchor: คุณภาพต่ำสุดของชุด aggregate แต่เป็น baseline ที่จำเป็นต่อการตรวจสอบ non-neural behavior
- ARM-02 ดีกว่า lexical anchor แต่ไม่ผ่าน frozen promotion rule

Frozen promotion rule จึง advance `ARM-03`, `ARM-05`, และ `ARM-04` ไปเป็น promoted arms ขณะที่ ARM-01 และ ARM-02 คงบทบาท diagnostic/non-advancing ใน A2

### ความสมบูรณ์ของผลและบทเรียนจาก failure

มี attempt ก่อนหน้า `a12-v16-20260811-r14` ที่ failed closed เพราะ performance/resource/reliability instrumentation ที่บังคับยังไม่ครบ attempt นั้นมีเฉพาะ 5 lexical cells และ 0 dense cell จึงไม่ได้ถูก promote หรือผสมกับผล `r15` หลังจากซ่อม instrumentation แล้วจึงวัด clean `r15` ใหม่ครบ 25 cells แนวทางนี้สำคัญต่อ publication เพราะรักษา attempt lineage และไม่สร้างผลจาก partial/incompatible outputs

Cell-level EDA ชี้ว่าการเลือก representation มีผลภายใน arm โดย `Fixed passages` ให้ Recall@100 สูงสุดในทุก arm ของ A1 ข้อนี้เป็น descriptive pattern ไม่ใช่ข้อพิสูจน์ว่าควร reuse representation เดียวกันข้าม retrievers ซึ่งเป็นคำถามที่ A2 จะทดสอบโดยตรง

### Figures A1 สำหรับนำเสนอ

| Figure | ใช้ตอบคำถามบนสไลด์ | PNG | SVG |
|---|---|---|---|
| Quality cell EDA | quality ของ 25 retriever-program cells ต่างกันอย่างไร | [PNG](../../outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.png) | [SVG](../../outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.svg) |
| Efficiency cell EDA | แลกเปลี่ยน latency, wall time และ peak VRAM อย่างไร | [PNG](../../outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.png) | [SVG](../../outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.svg) |
| REP-DEV / HARNESS-DEV split | แยก development role เพื่อป้องกัน leakage อย่างไร | [PNG](../../outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.png) | [SVG](../../outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.svg) |
| Dense-overflow EDA | windowing/recomposition ของ dense inputs ถูกตรึงและตรวจสอบอย่างไร | [PNG](../../outputs/figures/armindex/a1.2-dense-overflow-eda-v1.png) | [SVG](../../outputs/figures/armindex/a1.2-dense-overflow-eda-v1.svg) |

ตาราง 25 cells ฉบับเต็ม: [A1 cell EDA](../operations/A1_2_R15_CELL_EDA_20260811_TH.md)  
Receipt ปิด A1: [A1.2 measured closeout](../operations/A1_2_R15_MEASURED_CLOSEOUT_20260811_TH.md)

## A2: Per-Arm AutoIndex

### เป้าหมายเชิงวิทยาศาสตร์

A2 เปลี่ยนจาก common screen ใน A1 ไปเป็นการค้นหา representation candidate แบบอิสระต่อ arm เพื่อทดสอบว่าคำตอบที่ดีที่สุดสำหรับ ARM-03, ARM-04 และ ARM-05 แตกต่างกันหรือไม่ และเพื่อเก็บ diagnostic comparison สำหรับ ARM-01/02 โดยไม่อนุญาตให้สอง arm หลัง advance ผล

Candidate universe ถูกตรึงที่ **52 candidates = 40 matched candidates + 12 conditional reserve candidates** reserve จะเริ่มได้ต่อเมื่อ matched barrier และเงื่อนไขเวลา/งบประมาณที่ตรึงไว้ผ่าน ไม่ได้ถือว่าต้องรันครบ 52 โดยอัตโนมัติ

### Snapshot การปฏิบัติการ ณ จุดตัดรายงาน

| รายการ | สถานะที่ตรวจได้ |
|---|---|
| Attempt ที่กำลังรัน | `a2-goal004-20260816-005` |
| Runtime authority | `myis.armindex-a2-measured-execution-authority.v4`, สถานะ `PASS_A2_MEASURED_EXECUTION_AUTHORIZED`; เก็บ Owner-local ใน clean execution worktree |
| Provider topology | Vast instance `47790578`, 4 x RTX 3090; ARM-01 ทำ retrieval บน CPU และ ARM-02 ถึง ARM-05 ใช้ GPU topology |
| Budget authority | whole-workload quote `USD 54.5266667`, อยู่ภายใต้ hard cap `USD 60` ณ fresh provider observation |
| Durable remote progress signal | พบ `23` ไฟล์ `result.json` โดยนับเฉพาะการมีอยู่ของไฟล์ ไม่ได้เปิดอ่านผล |
| Coordinator | local recovery coordinator PID `34464` ยังมีชีวิต |
| ทรัพยากรที่ตรวจล่าสุด | GPU ทั้ง 4 ใบมีงานทำงานอยู่; disk ว่างประมาณ `242 GiB` |
| ผลวิทยาศาสตร์ | **ยังไม่มี canonical metric, winner, reserve decision หรือ claim** |

ค่า `23` เป็น telemetry ความคืบหน้าของ remote filesystem เท่านั้น ไม่ใช่ coverage receipt, ไม่ใช่ denominator ของการเปรียบเทียบ และไม่สามารถตีความเป็น A2 outcome ได้ การเปิดไฟล์ result, ranking, qrels, membership, per-query output และ worker logs ถูกห้ามใน reporting path นี้เพื่อรักษา protected-data boundary

### Recovery ที่ทำโดยไม่เปลี่ยนวิทยาศาสตร์

ARM-03 เคยชน operational timeout เดิม `7,200` วินาที ขณะที่ diagnostics แบบปลอดภัยยังเห็น process/heartbeat และ model load ที่ปกติ การแก้ไขจึงเพิ่มเฉพาะ timeout ต่อ candidate เป็น `21,600` วินาที โดยคง candidate bytes, model weights, adapter, evaluator, metric, representation semantics และ decision policy เดิมทั้งหมด partial/failed lineage ถูกเก็บเป็น forensic evidence และห้ามผสมเป็น coverage ของผลรอบนี้

### เงื่อนไขที่จะประกาศผล A2 ได้

ก่อนเพิ่มตัวเลขผล A2 หรือ figure จริงลงรายงาน ต้องผ่านครบตามลำดับนี้:

1. coverage ที่ validate exact `52/40/12` และ winner receipt hashes ของครบทั้ง 5 arms
2. allowlisted aggregate safe return พร้อม hash-bound receipt
3. terminal checkpoint และหลักฐาน worker reaping
4. independent aggregate-only result-integrity audit
5. render figures จาก closeout/audit ที่ผ่านแล้ว พร้อม publication-figure manifest
6. ตรวจ read model, Obsidian, MLflow และ projection links ก่อนสรุปต่ออาจารย์

จนกว่าจะครบเงื่อนไขนี้ ข้อสรุปที่ถูกต้องคือ: **A2 เป็น controlled live execution ที่มีความคืบหน้า แต่ยังไม่ใช่ finding**

### Figures A2 ที่จะเพิ่มหลัง closeout

ยังไม่มี A2 figure ที่วัดจริงในจุดตัดรายงาน และจะไม่สร้าง placeholder ที่อาจถูกเข้าใจผิดว่าเป็นผล แผน renderer จะเขียนเฉพาะหลัง closeout ผ่านไปที่ `outputs/figures/armindex/a2-goal004/` และสร้าง PNG, SVG และ PDF พร้อม manifest

| Figure ที่จะสร้าง | คำถามที่ figure ตอบ |
|---|---|
| Coverage and recovery completeness | candidate universe ถูก execute และ recover ได้ครบและทำซ้ำได้หรือไม่ |
| Per-arm quality outcomes | representation ใดของแต่ละ arm มี aggregate evidence รองรับ |
| Quality-latency-cost frontier | trade-off ด้าน effectiveness และ operation เป็นอย่างไร |
| Matched versus reserve path | reserve ถูกใช้, dormant หรือชี้ boundary finding แบบใด |
| Appendix provenance and claim boundary | receipt ใดรองรับแต่ละ claim และส่วนใดที่ยังไม่อ้าง |

Implementation สำหรับสร้าง figure หลัง A2 closeout: [a2_publication_figures.py](../../src/myis_research/armindex/a2_publication_figures.py)

## A3 และความพร้อมของงานถัดไป

ได้เตรียม A3.1 train-headroom diagnostic bundle ครบ 5 arms แบบ hash-only แล้ว เพื่อใช้เวลาระหว่าง A2 รันอย่างมีประสิทธิภาพ แต่ bundle มีสถานะ `PENDING_A2_CLOSEOUT` และไม่มี winner/diagnostic hash ที่ materialized การเตรียมนี้ไม่ใช่การเริ่ม A3 และไม่สามารถใช้ A2 partial outputs ได้

หลัง A2 closeout ที่ถูกต้อง จึงจะทำ A3 per-arm train-headroom diagnostic ได้โดยใช้ frozen A2 tuple เดียวกัน ผลนั้นจะช่วยตอบว่าชุด training/representation ของแต่ละ arm ยังมี headroom พอสำหรับ transfer/harness optimization หรือไม่

## ข้อจำกัดและ claim boundary สำหรับการนำเสนอ

- A0 เป็น engineering evidence เท่านั้น ไม่มี retrieval-quality result
- A1 เป็น measured development aggregate บน REP-DEV ไม่ใช่ Selection/Final confirmation
- A2 ยังไม่มี valid outcome แม้ remote work จะคืบหน้า
- ไม่ควรกล่าวว่า representation ใดชนะ per-arm จนกว่า A2 closeout และ integrity audit ผ่าน
- ไม่ควรกล่าวเชิง causal, legal, infringement, novelty หรือ production superiority จากผลในรายงานนี้
- ไม่มี qrels, protected membership, raw identifier, ranking, per-query metric, credential หรือ raw provider payload ในรายงาน

## ลำดับงานและจุดอัปเดตรายงานถัดไป

1. ปล่อย A2 coordinator ทำงานต่อภายใต้ timeout ที่ปรับแล้วโดยไม่ restart worker ที่ healthy
2. safe-return เฉพาะ aggregate allowlist และสร้าง execution closeout
3. audit result integrity แบบอิสระ
4. render A2 figures จาก evidence ที่ผ่านแล้ว
5. เติม section A2 ด้วย receipt-bound result, arm winners, reserve disposition และ figure manifest paths
6. จากนั้นจึงเริ่ม A3.1 ที่เตรียมไว้ และอัปเดตรายงานฉบับเดียวกัน

## หลักฐานอ้างอิง

- [A0.9 validation and safety closeout](../../outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json)
- [A0.10 independent acceptance](../../outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json)
- [A1 r15 aggregate closeout](../operations/A1_2_R15_MEASURED_CLOSEOUT_20260811_TH.md)
- [A1 r15 cell-level EDA](../operations/A1_2_R15_CELL_EDA_20260811_TH.md)
- [A1 r14 failed-closed audit](../../outputs/audits/armindex/a1.2-v16-r14-instrumentation-failure-20260811.json)
- [A2 Goal 004](../goal/A2_PER_ARM_AUTOINDEX_goal_004.md)
- [A2 execution runbook](../../control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V2.md)
- [A3.1 train-headroom staging note](../research/A3_1_TRAIN_HEADROOM_STAGING.md)

รายงานนี้เป็น synthesis สำหรับอาจารย์จาก aggregate-safe evidence เท่านั้น A0 สนับสนุน readiness/reproducibility, A1 สนับสนุน development-level comparison, และ A2 ยังอยู่ในสถานะรอ receipt-bound closeout จึงไม่มีการกล่าวผลเกินหลักฐาน
