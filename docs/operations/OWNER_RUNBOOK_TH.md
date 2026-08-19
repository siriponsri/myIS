# คู่มือ Owner — ArmIndex V02 NEW แบบ Beginner / Low-Code

เอกสารนี้สรุปเฉพาะสิ่งที่ Owner ต้องทำจริง รายละเอียดโมเดล representation, arm, fusion, routing, threshold และ GPU ให้ระบบตัดสินด้วย frozen defaults และ Research Flows

---

## 1. Owner ไม่ต้องเลือก

- embedding model;
- representation candidate;
- passage size;
- arm promotion;
- BGE dense/sparse/multi-vector;
- fusion;
- route depth;
- latency threshold;
- HarnessOpt candidate;
- GPU รุ่น;
- retry;
- ว่าผลลบควรลองเพิ่มหรือไม่;
- fine-tuning หรือ weight adaptation เพราะไม่มีในแผนนี้.

---

## 2. Owner มี 1 คำสั่งเริ่ม และ 2 review gates

### เริ่ม campaign

```text
/goal Execute Phase 0 of PLAN_V02_NEW.md only. Create the additive armindex-multiretriever-v2 campaign, preserve all historical evidence, freeze the evaluation, model, representation, budget, and protected-data contracts, run compute-feasibility fixtures, and stop with a Phase 0 completion card. Do not run measured retrieval, Selection, or Final.
```

การเริ่ม Phase 0 เป็น standing authorization สำหรับ REP-DEV, HARNESS-DEV, Selection หนึ่งครั้งหลัง freeze, Vast.ai รวมไม่เกิน USD 100 และ automatic Research Flow gates โดย Final ยังคงปิด

Owner ตรวจเพียง:

```text
CAMPAIGN = armindex-multiretriever-v2
MODEL_WEIGHT_CHANGE = disabled
FINAL_872 = locked
BUDGET_CEILING = USD 100
PROTECTED_BOUNDARY = PASS
COMPUTE_FEASIBILITY = PASS
```

### Gate 1 — `D2_OPEN_FINAL`

ใช้หลัง Phase 7 มี champion card ที่ freeze แล้ว

Owner อ่าน:

- research champion;
- commercial-capable champion;
- Selection OUT Recall@100;
- Selection OUT nDCG@100 และ nDCG@10;
- strongest comparator;
- paired delta/CI;
- p95 latency และ cost/query;
- total budget;
- frozen bundle hash;
- known risks.

หากพร้อม:

```text
D2_OPEN_FINAL
```

แล้วสั่ง:

```text
/goal Execute Phase 8 of PLAN_V02_NEW.md only after D2_OPEN_FINAL is recorded. Verify the frozen bundle, run the preregistered strongest comparator and exactly one research champion on Final-872 once, compute paired statistics and operational metrics, seal all evidence, and prohibit feedback into the system.
```

### Gate 2 — `D3_SUBMIT_RELEASE`

ใช้หลัง Phase 9 audit พร้อม

Owner ตรวจ:

- claim ตรงผล;
- ไม่มี legal decision claim;
- PatEmbed license ถูกอธิบาย;
- commercial champion ไม่ใช้โมเดล non-commercial;
- package ไม่มี credential/path/protected ID;
- venue/author/date ถูกต้อง.

หากพร้อม:

```text
D3_SUBMIT_RELEASE
```

---

## 3. คำสั่ง Phase

### Phase 1

```text
/goal Execute Phase 1 of PLAN_V02_NEW.md only. Reproduce the canonical family-level BM25 baseline and validate every frozen arm adapter on fixtures and REP-DEV. Resolve protocol or lineage failures before continuing and stop with a comparable-baseline report. Do not use HARNESS-DEV, Selection, or Final for optimization.
```

### Phase 2

```text
/goal Execute Phase 2 of PLAN_V02_NEW.md only. Compile the five frozen common representation programs, run them across all five retrieval arms on REP-DEV, measure quality, complementarity, latency, storage, and failure behavior, and automatically promote at most three arms to per-arm AutoIndex. Do not use HARNESS-DEV, Selection, or Final.
```

### Phase 3

```text
/goal Execute Phase 3 of PLAN_V02_NEW.md only. Run constrained AutoIndex representation-program search independently for each promoted frozen retriever arm on REP-DEV, using immutable four-candidate batches and aggregate-safe feedback. Freeze one program per promoted arm and stop before HARNESS-DEV.
```

### Phase 4

```text
/goal Execute Phase 4 of PLAN_V02_NEW.md only. Evaluate frozen winning representation programs across valid retrieval arms, build the cross-arm transfer matrix, measure same-depth complementarity on HARNESS-DEV, and freeze the best single arm plus the eligible complementary arm set. Do not optimize the harness or access Selection/Final.
```

### Phase 5

```text
/goal Execute Phase 5 of PLAN_V02_NEW.md only. Optimize the deterministic multi-arm retrieval harness on HARNESS-DEV over the frozen programs and eligible arms. Search only arm subset, order, depth, fusion, caching, and label-free early-stop surfaces. Freeze the best single, fixed-union, and HarnessOpt configurations. Do not access Selection or Final.
```

### Phase 6

```text
/goal Execute Phase 6 of PLAN_V02_NEW.md only. Benchmark the frozen single-arm and harness finalists under production-style latency, throughput, cache, failure, and cost conditions. Freeze FAST, BALANCED, and DEEP profiles only when non-dominated. Do not use Selection or Final.
```

### Phase 7

```text
/goal Execute Phase 7 of PLAN_V02_NEW.md only. Run the frozen legal structured-retrieval Research Flow without patent retuning, freeze at most four DAPFAM finalists, expose Selection-125 exactly once, select research and commercial champions by the preregistered rule, and stop before Final.
```

### Phase 8

ใช้หลัง `D2_OPEN_FINAL` เท่านั้น

### Phase 9

```text
/goal Execute A7_PUBLICATION_AND_RELEASE only. Read docs/goal/A7_PUBLICATION_AND_RELEASE_goal_001.md, use validated aggregate-safe A0-A6 evidence, write the manuscript and anonymous reproducibility package, audit claims, statistics, licenses, layout, and protected boundaries, and stop before submission unless D3_SUBMIT_RELEASE is recorded.
```

### A6 full-DAPFAM materialization

```text
/goal Execute A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY only. Read docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md, wait for a valid A5 closeout, then materialize exactly one A5-frozen winner over the full DAPFAM corpus with owner-local protected data, aggregate-safe return, and no tuning, Selection, or Final feedback.
```

---

## 4. วิธีอ่าน completion card

| ช่อง | ความหมาย |
|---|---|
| `STATUS` | PASS, STOP_WITH_EVIDENCE, BLOCKED |
| `PHASE / TASK` | งานปัจจุบัน |
| `RESEARCH_FLOW` | flow ที่เดินหรือหยุด |
| `PRIMARY_RESULT` | OUT Recall@100 หรือ not measured |
| `SECONDARY` | nDCG@100 / nDCG@10 |
| `ARMS` | arm ที่ promote/freeze |
| `PROGRAM` | representation winner hash |
| `HARNESS` | harness winner hash |
| `PRODUCTION_PROFILE` | FAST/BALANCED/DEEP |
| `BUDGET` | phase/cumulative/remaining |
| `INTEGRITY` | hashes/split/evaluator |
| `NEXT_COMMAND` | คำสั่งถัดไป |
| `OWNER_ACTION` | ปกติ none; มีเฉพาะ blocker จริง, D2, D3 |

`STOP_WITH_EVIDENCE` ไม่ใช่ความล้มเหลว หมายถึง flow ไม่มี leverage และระบบเก็บผลไว้ครบ

---

## 5. ระบบถาม Owner ได้เมื่อใด

1. หา protected data root ไม่พบ;
2. Vast.ai ใช้ไม่ได้เมื่อถึง GPU task;
3. canonical hash ขัดกันโดยไม่มี authority rule;
4. ต้องเพิ่มงบเกิน USD 100;
5. ต้องเปิด Final;
6. ต้อง submit/release.

ห้ามถาม Owner ให้เลือกโมเดล, arm, representation, parameter, fusion, threshold หรือ retry.

คำตอบมาตรฐาน:

```text
ใช้ automatic gate และ frozen default ตาม PLAN_V02_NEW.md ดำเนินการต่อโดยไม่ขอ Owner micro-decision และบันทึกเหตุผลใน receipt
```

---

## 6. สิ่งที่ต้องจำเรื่องสินค้า

- Research champion อาจใช้ PatEmbed-large.
- Commercial champion ห้ามใช้ PatEmbed-large โดยอัตโนมัติ เพราะ license non-commercial.
- FAST เหมาะ interactive.
- BALANCED เหมาะ RAG production.
- DEEP อาจเป็น asynchronous audit.
- ผล DAPFAM ไม่ใช่หลักฐานวินิจฉัย novelty หรือกฎหมาย.
- การขาย Legal RAG ต้องอ้างผล legal transfer แยกจาก patent benchmark.
