---
title: "ArmIndex: Full Evidence-Grounded Technical Report"
language: "Thai"
audience: "Research advisor, graduate students, and researchers"
repository: "myIS Research / 01_Research"
branch: "main"
commit: "a8df5a83c958987bc12d1a382b9befc34e6c5bb6"
report_date: "2026-08-19"
remote_observation_cutoff_utc: "2026-08-19T12:27:22Z"
numeric_authority: "Canonical manifests, machine-readable result summaries, append-only receipts, and Owner Store aggregate-safe receipts"
evidence_boundary: "Development evidence is separated from Selection and Final held-out evidence. Protected qrels, membership, raw identifiers, rankings, and per-query outcomes are not reproduced."
---

# ArmIndex: รายงานเทคนิคฉบับเต็มแบบตรวจสอบย้อนกลับได้

รายงานนี้อธิบายโครงการ ArmIndex สำหรับผู้อ่านที่ไม่คุ้นกับชื่อ phase ภายใน
โครงการ ตัวเลขที่ปรากฏในรายงานยึดจากไฟล์ machine-readable และ receipt ที่ระบุไว้
ในตารางหลัก ไม่ใช้ presentation slide เป็นแหล่งตัวเลขหลัก หากข้อมูลไม่พอสำหรับ
การยืนยัน จะระบุ `NOT VERIFIED`, `INCONSISTENT` หรือ `MISSING` แทนการเติมข้อมูล
ด้วยการอนุมาน

## 1. บทสรุปผู้บริหาร

ArmIndex ศึกษาว่า representation ของเอกสารสิทธิบัตรที่เหมาะสมขึ้นกับ retriever
ที่ใช้ค้นหรือไม่ และ representation ที่ค้นพบจาก retriever หนึ่งจะถ่ายโอนไปยัง
retriever อื่นหรือรวมเป็นระบบที่อยู่บน quality--latency--cost frontier ได้หรือไม่
หน่วยวัดคือ patent family ของ DAPFAM และ metric หลักในช่วงพัฒนาคือ OUT-domain
Recall@100 โดยรายงาน OUT nDCG@100, OUT nDCG@10 และตัวชี้วัดการปฏิบัติการร่วมด้วย

สถานะที่ยืนยันได้จากหลักฐาน:

- **Migration Foundation (ระยะวางระบบและความปลอดภัย) เสร็จสมบูรณ์** แต่ไม่มี
  retrieval-quality result การวัด GPU เชิงวิทยาศาสตร์ หรือ paid API call
- **Common Multi-Arm Screening (การคัดกรองร่วม) เสร็จสมบูรณ์** ครบ 25/25
  combinations ของ 5 representation programs และ 5 retrieval arms บนบทบาท
  REP-DEV จำนวน 150 queries
- **Per-Arm AutoIndex (การค้น representation แยกตาม retriever) ปิดผลผ่าน**
  candidate accounting มี 52 candidates, 44 measured, 8 dormant และ 0 failed
  aggregate cost `54.52666666666665948 USD` ต่ำกว่า hard stop `60 USD`
- **Transfer, Complementarity, and Harness Optimization เสร็จสมบูรณ์** บน
  Train-250: 14/14 operations, 9 transfer cells, 5 fixed controls และ
  HarnessOpt 3 batches/12 candidates ผ่าน independent result-integrity audit
- **Production transfer บน Vast instance 47790578 ปิดด้วยหลักฐานครบ**
  FAST, BALANCED, DEEP และ ARM-03 research reference วัดครบ 100/100 หน่วย,
  deterministic และ failures=0; FAST และ DEEP เป็น commercial non-dominated
  frontier ส่วน ARM-03 แยกเป็น research-only
- **Selection และ Final confirmation ยังไม่เปิด** เนื่องจากไม่มี hash-bound
  Selection-125 paired-vector/evaluator handoff; จึงยังไม่มี production winner,
  Final-872 result หรือ full-corpus materialization result

ผลที่มีนัยสำคัญต่อ publication คือหลักฐาน interaction ระหว่าง representation กับ
retriever และผลเชิงลบที่ยังอธิบายได้: ARM-04 ดีขึ้นจาก A1 อย่างมี strict gain,
ARM-03 เป็น numerical tie ที่ precision ที่รายงาน, ARM-05 มีประโยชน์ใน transfer
แต่ไม่ชนะ A1 อย่าง strict, และ HarnessOpt พบ flat surface ใน workload พัฒนา
ไม่ควรสรุปว่า ARM ใดชนะ universal หรือว่า A3/A4 เป็นผล production/generalization
จนกว่าจะมี Selection และ Final evidence

## 2. ปัญหาวิจัยและช่องว่าง

ระบบ patent retrieval มักถือ representation ของเอกสารเป็น preprocessing คงที่
หรือเลือก embedding model เพียงตัวเดียว ขณะที่งาน multi-retriever มักใช้ view และ
fusion ที่ออกแบบด้วยมือ ช่องว่างที่ ArmIndex ตั้งเป้าทดสอบคือการแยกปัจจัยสองชั้น:

1. representation program ที่เหมาะสมอาจ **retriever-conditioned** ไม่ใช่สูตรเดียว
   สำหรับ lexical, generic dense และ patent-domain dense retrievers
2. representation ที่ชนะใน arm หนึ่งอาจไม่ถ่ายโอนได้ การวัด transfer matrix จึง
   เป็นหลักฐาน interaction ไม่ใช่เพียง leaderboard
3. arm ที่มีคุณภาพสูงสุดอาจไม่เหมาะกับ deployment และ union ของทุก arm อาจเสีย
   latency/cost โดยไม่ได้เพิ่ม relevant-family exposure
4. agentic optimization ต้องถูกจำกัดด้วย grammar, frozen evaluator, aggregate-only
   feedback และ deterministic runtime เพื่อให้ผลตรวจสอบและทำซ้ำได้

คำถามวิจัยที่ผูกกับ protocol:

| รหัส | คำถาม |
|---|---|
| RQ1 | การค้น representation ต่อ arm เพิ่ม OUT Recall@100 เหนือ static comparator หรือไม่ |
| RQ2 | representation ที่เหมาะสมขึ้นกับ retriever หรือไม่ |
| RQ3 | arm ใดเพิ่ม unique relevant-family coverage ภายใต้ OUT-domain shift |
| RQ4 | fixed/adaptive harness ดีกว่า best single arm เมื่อรวม quality, latency และ cost หรือไม่ |
| RQ5 | agent ช่วยพัฒนาได้โดยที่ deployed retrieval ยังคง deterministic และ reproducible หรือไม่ |
| RQ6 | โปรแกรม commercial-capable ถ่ายโอนไปยัง legal structured retrieval ได้หรือไม่ |

## 3. Related work และการสืบทอดแนวคิด

| งาน | เทคนิคที่สืบทอด | การปรับใช้ใน ArmIndex | สิ่งที่ยังต่าง | เปรียบเทียบตัวเลขโดยตรงได้หรือไม่ |
|---|---|---|---|---|
| DAPFAM | family-level cross-domain patent retrieval และ IN/OUT domain evaluation | ใช้ DAPFAM เป็น benchmark หลัก หน่วยวัดเป็น family และใช้ OUT Recall@100 เป็น primary exposure metric | relevance เป็น examiner-citation proxy ไม่ใช่ novelty, infringement หรือ FTO judgment | ไม่ได้ ตัวเลขของ paper เป็นคนละ protocol/split |
| AutoIndex | ค้น executable representation programs โดยตรึง retriever/evaluator | ใช้ grammar P00--P04, ค้นแยกตาม arm และตรวจ transfer | ArmIndex ใช้ DAPFAM, protected split, frozen model revisions และ receipt governance ของตนเอง | ไม่ได้ ผล CRUMB ของ AutoIndex ไม่ใช่ DAPFAM |
| GEPA | reflective prompt evolution และการใช้ feedback เพื่อแก้ artifact แบบ bounded | เป็นแนวคิดเชิง lineage ให้ reflection มีข้อจำกัดและมี evidence | ArmIndex ไม่อ้าง GEPA numeric result และไม่เปิดให้ prompt agent เห็น qrels/rankings | ไม่ได้ |
| SkillOpt-Lite / HarnessOpt | text-space skill/harness optimization, held-out gate, bounded edits และ stop เมื่อ flat | ใช้เฉพาะ development-time, frozen candidates, 3 batches, aggregate-only feedback | ไม่แก้ model weights และ A3 ใช้ fixed action signature; flat surface เป็นผล valid | ไม่ได้ |
| HarnessOpt-Bench | วัด agent/harness โดยแยกตัว executor และ optimizer | ใช้แนวคิดการประเมิน harness แยกจาก deterministic retriever path | benchmark ภายใน ArmIndex และ DAPFAM ไม่ใช่ benchmark เดียวกัน | ไม่ได้ |
| BEIR | heterogeneous IR benchmark, BM25 baseline, quality/compute trade-off | ใช้ BM25 เป็น transparent lexical anchor และรายงาน quality กับ operational metrics | DAPFAM เป็น patent-family, cross-domain และ protected protocol เฉพาะโครงการ | ไม่ได้ |
| Patent Embeddings / PatenTEB | ความแตกต่างของ patent-domain embedding และผลของ model/view | ใช้ PatEmbed เป็น research reference และแยก license จาก commercial frontier | revision, split และ evaluator เป็น ArmIndex-specific | ไม่ได้ |

แหล่งอ้างอิงหลักอยู่ใน `evidence/literature/digests/` โดยเฉพาะ
`U011_dapfam_digest.md`, `U154_autoindex_learning_representation_programs_for_retrieval_digest.md`,
`U058_gepa_reflective_prompt_evolution_can_outperform_reinforcement_learning_digest.md`,
`U082_skillopt_executive_strategy_for_self-evolving_agent_skills_digest.md` และ
`U083_beir_a_heterogeneous_benchmark_for_zero-shot_evaluation_of_information_r_digest.md`.
ตัวเลขจาก literature ใช้เป็น design inheritance เท่านั้น ไม่ใช่ผล ArmIndex

## 4. Benchmark และ evaluation protocol

### 4.1 หน่วยวัดและบทบาทข้อมูล

หน่วยวัดคือ DAPFAM patent family ผล retrieval ถูก aggregate เป็น family-level
rankings และประเมินด้วย frozen evaluator ขอบเขตข้อมูลมีบทบาทดังนี้:

| บทบาท | จำนวน | การใช้งาน | สถานะ |
|---|---:|---|---|
| REP-DEV | 150 queries | common screening และ representation search | วัดแล้วใน A1/A2 |
| HDEV-100 | 100 queries | transfer, complementarity และ harness development | ใช้ใน A3 Train-250 receipt |
| Train-250 | 250 queries | development pool รวม REP-DEV + HDEV-100 | A3 ครบ 250/250 ต่อ operation |
| Selection-125 | 125 queries | one-shot comparison ของ finalists | ยังไม่ยืนยันว่าเปิด |
| Final-872 | 872 queries | final confirmation หลัง Owner gate | ยังไม่เปิด |

นี่ไม่ใช่การแบ่ง generic development/validation/test แบบ 100/150/ที่เหลือ
โดยอัตโนมัติ แต่เป็น role-specific split ที่ commitment ถูกตรึงด้วย manifest
และ protected membership ใน Owner Store

### 4.2 Metrics

- primary: OUT Recall@100
- secondary: OUT nDCG@100 และ OUT nDCG@10
- guardrails: ALL และ IN metrics, failure rate, determinism และ coverage
- operations: p50/p95/p99 latency, throughput, wall time, cost, RAM, VRAM,
  index size, GPU/CPU use และ recovery lineage

Recall@100 วัด exposure ของ relevant families ใน 100 อันดับแรก ส่วน nDCG ให้
น้ำหนักอันดับที่เร็วกว่า ค่าเหล่านี้เป็น aggregate ตาม population ที่ระบุใน
receipt; ไม่ใช่ค่าเฉลี่ยที่นำมาจาก slide

### 4.3 Leakage และ access controls

qrels, protected membership, raw query/family IDs, rankings, per-query outcomes,
credentials และ provider payloads อยู่ Owner-local การส่งกลับเข้า Git/Paper/Brain
ทำได้เฉพาะ aggregate-safe metrics, hashes, counts, manifests, receipts และ pointers
ดังนั้นรายงานนี้ไม่สามารถแสดง concrete protected patent family example ได้อย่าง
ปลอดภัย: สถานะคือ **MISSING / NOT VERIFIED** ไม่ใช่การละเว้นโดยไม่ตั้งใจ

## 5. นิยาม patent representation

representation program คือ deterministic mapping จาก family source fields ไปยัง
หนึ่งหรือหลาย indexable units พร้อม family aggregation กฎร่วมคือ Unicode NFKC,
canonical whitespace, field labels ตาม contract, ordered family members และ
fail-closed เมื่อเกิด silent truncation

| Program | Fields/unitization | Segmentation และ aggregation | Enrichment/labels | Normalization |
|---|---|---|---|---|
| P00-TAC-DOC | title_en + abstract_en + claims_text | family-document เดียว, single-unit | labels TITLE/ABSTRACT/CLAIMS | unicode NFKC + canonical whitespace |
| P01-TA-DOC | title_en + abstract_en | family-document เดียว | labels TITLE/ABSTRACT | เดียวกัน |
| P02-CLAIM1 | structured independent claim แรกใน family order | one claim per family, max-p aggregation | CLAIM label; fallback forbidden | เดียวกัน |
| P03-PASSAGE | title+abstract+claims stream | 384 tokens, stride 320, overlap 64, retain final partial, max-p family score | field labels preserved | tokenizer `unicode_nfkc_whitespace.v1` |
| P04-SECTION-MULTIVIEW | title, abstract, claims เป็น views | 3 views, per-view depth 100, RRF k=60, lexical opaque-token tie break | section labels | เดียวกัน |

ไม่มี generated prose enrichment หรือ model-weight modification ในโปรแกรมเหล่านี้
ตัวอย่าง patent จริงที่ผูกกับ family ID ไม่ถูกนำเสนอเพราะ protected identifier boundary;
การยกตัวอย่าง DAPFAM เฉพาะรายโดยไม่มี safe pointer จะเป็น **NOT VERIFIED**

## 6. Candidate space และ retriever catalog

มี 5 arms และ 5 common programs ในการคัดกรองร่วม รวม 25 logical cells

| Arm | Model/retriever | Revision | Prompt/scoring | License |
|---|---|---|---|---|
| ARM-01 | BM25s lexical, implementation 0.3.10 | frozen implementation | no neural prompt; k1=1.2, b=0.75, Unicode/case fixed | commercial-capable |
| ARM-02 | `BAAI/bge-m3` | `5617a9f61b028005a4858fdac845db406aefb181` | query/document raw text, official pooling, normalized dot product, 1024d | MIT |
| ARM-03 | `datalyes/patembed-large` | `2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad` | query: `encode query for different document retrieval: {query}`; document: `encode document for different retrieval: {document}`; mean non-padding, L2, 1024d | CC-BY-NC-SA-4.0, research only |
| ARM-04 | `Snowflake/snowflake-arctic-embed-m-v2.0` | `95c2741480856aa9666782eb4afe11959938017f` | query: `query: {query}`; document raw; CLS/first-token, L2, 768d | Apache-2.0 |
| ARM-05 | `Qwen/Qwen3-Embedding-0.6B` | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | `Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:{query}`; document raw; left-padded last-token, L2, 1024d | Apache-2.0 |

Model bytes, tokenizer files, adapter hashes, runtime identity และ exact model
payloads remain Owner-local. The lock files are the repository-safe authority for
revision, dimensions, license and prompt binding.

## 7. Editable และ frozen components

**Editable within the preregistered development grammar:** representation program
choice, segmentation/view selection, family aggregation among P00--P04, arm subset
and fixed/adaptive harness configuration at the authorized phase, worker batch size,
retry/timeout/cache paths, and logging/recovery parameters.

**Frozen:** DAPFAM candidate universe and source bytes, split membership, qrels and
evaluator semantics, primary/secondary metric definitions, model weights/revisions,
tokenizer and pooling, license boundaries, no-fine-tuning policy, family identity,
protected output surface, and selection/final access policy. Runtime repairs may
change operational parameters only when scientific semantics remain unchanged.

## 8. Agentic representation optimization

AutoIndex supplies the representation-search hypothesis; the ArmIndex implementation
turns it into a bounded, hash-bound candidate space. A2 candidate accounting is not
an unconstrained LLM sweep. Candidate programs were frozen before measurement, and
the measured result is aggregate-safe. A3 HarnessOpt used three complete frozen
batches, four roles per batch, 12 candidates and one effective action signature.

The optimizer/agent model used for the official candidate-freeze bridge is recorded
as `gpt-5.6-sol`, official CLI/SDK `0.144.4`, reasoning effort `high` in
`campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json`.
Exact hidden conversational prompts are not projected; the reproducibility surface
is the frozen program set, prompt/config hashes, candidate manifests and receipts.
Therefore prompt text beyond the model-bound retrieval templates above is
**NOT VERIFIED / OWNER-LOCAL** and must not be reconstructed from memory.

Stopping rules were explicit: no candidate mutation after freeze, no Selection or
Final access, no protected per-query feedback to the optimizer, stop after complete
authorized batches, and stop HarnessOpt on a flat effective action surface.

## 9. Common screening

Common screening measured all 25 arm-by-program cells on REP-DEV (150 queries)
under one evaluator. The terminal summary is
`campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json`
with file SHA-256
`e092ff9b3d9436fc3cb1d738b04a5e766b9131151ff4756cbd36eeac8731bad1`.

| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | p95 ms | Disposition |
|---|---:|---:|---:|---:|---|
| ARM-01 BM25 | 0.191200 | 0.172717 | 0.160011 | 441.520 | diagnostic |
| ARM-02 BGE-M3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | diagnostic |
| ARM-03 PatEmbed | 0.413400 | 0.347812 | 0.289856 | 212.062 | advanced |
| ARM-04 Arctic | 0.340667 | 0.284546 | 0.235538 | 214.207 | advanced |
| ARM-05 Qwen3 | 0.363733 | 0.307930 | 0.256706 | 217.099 | advanced |

P03 fixed passages was the strongest common representation in each arm in this
screening table, but this is descriptive evidence only; A2 re-searched each arm
independently. A1 terminal coverage was 25/25, failure rate mean 0.0 for every arm,
and the run charged `11.161632 USD` according to the progress report projection.

## 10. Retriever-specific search

A2 closeout projection:
`control/armindex/a2/a2-goal004-closeout-projection.v1.json`.
The immutable accounting is 52 candidates, 40 matched candidates, 4 activated
reserve candidates, 8 dormant reserve candidates, 44 measured candidates, and 0
failed candidates. Total workload cost was `54.52666666666665948 USD` against a
forward hard stop of `60 USD`.

| Arm | A2 OUT Recall@100 | A2 OUT nDCG@100 | A2 OUT nDCG@10 | A1 comparator | A2 disposition |
|---|---:|---:|---:|---:|---|
| ARM-01 | 0.234667 | 0.210784 | 0.195024 | unavailable in A2 receipt | diagnostic tie/no winner |
| ARM-02 | 0.290000 | 0.249919 | 0.220057 | unavailable in A2 receipt | diagnostic tie/no winner |
| ARM-03 | 0.423000 | 0.357636 | 0.299444 | 0.423000 | numerical tie to A1 |
| ARM-04 | 0.358667 | 0.301868 | 0.253229 | 0.352667 | strict improvement |
| ARM-05 | 0.373667 | 0.321262 | 0.273664 | 0.380000 | no strict improvement |

### Accounting inconsistency audit

The numbers are internally consistent at the candidate-accounting level:
`52 = 40 matched + 12 conditional reserve`, and `44 measured + 8 dormant = 52`.
The phrase “44 measured” therefore means candidates with a valid aggregate result,
not 44 unique arm-level trials. The phrase “0 failed” means no candidate reached
the declared scientific failure state; dormant is a not-activated reserve state,
not a failed run and not a zero-valued metric.

The A2 projection does not contain a single authoritative ALL/IN/OUT triplet for
every candidate. It reports OUT values for the winning/diagnostic rows. Any value
near 0.41 in this report is explicitly OUT Recall@100 where the source says OUT;
it must not be relabelled as ALL Recall@100. The question of whether older slides
used 0.41 as ALL is **INCONSISTENT / NOT VERIFIED** until reconciled against the
underlying evaluator receipt.

Definitions used by the closeout:

- **strict improvement/gain:** prespecified primary metric exceeds frozen comparator
  under the declared precision and tie rule
- **numerical tie:** values equal at the recorded precision or within the declared
  numerical-tie rule; no secondary-metric or latency post-hoc tie breaker
- **dormant:** candidate remained in reserve and was not activated; no metric is
  implied
- **failure:** a scientific candidate run entered the declared failure state;
  infrastructure retries are preserved separately and are not silently mixed

## 11. Best representation profiles

The common-screen winner was P03 fixed passages for all five arms. The per-arm A2
winner records show a more nuanced picture: ARM-03 selected the matched-b2-orthogonal
program and tied its A1 comparator at `0.423`; ARM-04 selected matched-b1-orthogonal
and improved from `0.352667` to `0.358667`; ARM-05 remained below its A1 comparator
at `0.373667` versus `0.380000`. ARM-01 and ARM-02 are retained as diagnostic
negative/tie evidence, not promoted winners.

This is a retriever-conditioned result: the representation grammar is shared but
the best program and advancement status are not universal. Program hashes and
candidate receipt hashes are in the A2 closeout projection; protected per-query
rankings are not.

## 12. Transfer และ fusion experiments

A3 Extended used only ARM-03, ARM-04 and ARM-05 as primary advancement arms. It
completed 9 source-program-to-target-adapter transfer cells, 5 fixed controls,
250/250 Train-250 units per operation, 3 HarnessOpt batches and 12 candidates.
The numeric authority is the Owner-local aggregate-safe
`<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-result-integrity-audit.json`
and its paired safe-return receipt, not the presentation projection
`docs/progress_report/update_A3_19AUG2026.md`. The audit status is
`PASS_A3_RESULT_INTEGRITY_AUDIT`, its operation count is 14, and it binds the
runtime, stage, HarnessOpt and safe-return hashes listed in Appendix A. The
repository CSV files are derived EDA projections used for tables and figures;
their SHA-256 values are recorded in Appendix E. The corresponding Owner Store
paths and their role in the evidence chain are also registered in Appendix E.

### Transfer matrix (OUT Recall@100)

| Source program -> target adapter | PatEmbed | Arctic | Qwen3 |
|---|---:|---:|---:|
| PatEmbed | 0.418436 | 0.337430 | 0.362570 |
| Arctic | 0.418715 | 0.341341 | 0.359497 |
| Qwen3 | **0.419274** | 0.338268 | 0.360615 |

The strongest cell was Qwen3 program to PatEmbed adapter (`0.419274`). Arctic
target adapter was consistently lower in this workload, demonstrating adapter--
representation interaction rather than universal portability.

### Fixed controls

| Control | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Wall time (s) |
|---|---:|---:|---:|---:|
| best single | 0.418436 | 0.347098 | 0.290589 | 8782.83 |
| top-two RRF-60 | **0.418715** | **0.352747** | **0.293716** | 13607.22 |
| top-three RRF-60 | 0.415084 | 0.346250 | 0.284772 | 17484.52 |
| all-primary RRF-60 | 0.415084 | 0.346250 | 0.284772 | 18405.79 |
| commercial-only union | 0.369274 | 0.308967 | 0.258116 | 10647.75 |

The top-two fixed union had the strongest fixed-control quality; adding every
primary arm did not improve the frontier. HarnessOpt's 12 frozen candidates
compiled to one effective action signature, so the valid conclusion is
`PASS_A3_HARNESSOPT_FLAT_SURFACE`, not adaptive improvement.

## 13. Results by population: ALL / IN / OUT

The canonical primary result surface is OUT. A1 and A2 summaries provide OUT
metrics; A0 provides no retrieval metric. The report therefore does not fabricate
ALL or IN values. Where a machine-readable artifact does not expose those fields,
the status is `MISSING`, not zero.

| Phase/result | ALL Recall/nDCG | IN Recall/nDCG | OUT Recall/nDCG | Query count | Status |
|---|---|---|---|---:|---|
| A0 migration | -- | -- | -- | 0 retrieval | VERIFIED: no measurement |
| A1 aggregate | MISSING in summary | MISSING in summary | 0.1912--0.4134 Recall@100 by arm | 150 per cell | VERIFIED OUT; ALL/IN missing |
| A2 closeout | MISSING in projection | MISSING in projection | 0.234667--0.423000 Recall@100 by arm | candidate-dependent REP-DEV | VERIFIED OUT; ALL/IN missing |
| A3 transfer/fusion | MISSING | MISSING | 0.337430--0.419274 transfer; 0.369274--0.418715 controls | 250 per operation | VERIFIED OUT |
| A4 FAST | MISSING | MISSING | 0.345833 Recall@100; 0.292764 nDCG@100; 0.249337 nDCG@10 (HDEV OUT contract; receipt omits population field) | 100/100 | VERIFIED aggregate; deterministic; 0 failures |
| A4 BALANCED | MISSING | MISSING | 0.382639 Recall@100; 0.328777 nDCG@100; 0.278442 nDCG@10 (HDEV OUT contract; receipt omits population field) | 100/100 | VERIFIED aggregate; deterministic; 0 failures |
| A4 DEEP | MISSING | MISSING | 0.382639 Recall@100; 0.328777 nDCG@100; 0.278442 nDCG@10 (HDEV OUT contract; receipt omits population field) | 100/100 | VERIFIED aggregate; deterministic; 0 failures |
| A4 ARM-03 research reference | MISSING | MISSING | 0.463194 Recall@100; 0.372934 nDCG@100; 0.305775 nDCG@10 (HDEV OUT contract; receipt omits population field) | 100/100 | VERIFIED research-only aggregate; excluded from commercial claims |
| A4 profile coverage / audit | MISSING | MISSING | four profiles complete; no quality value added | 100/100 each | `PASS_A4_RESULT_INTEGRITY_AUDIT`; Selection/Final accesses 0 |
| A4 LegalBench mini transfer | MISSING | MISSING | UNSUPPORTED: required frozen mini dataset/evaluator/runtime absent | -- | Isolated diagnostic; no patent retuning |
| A4 Selection-125 | protected | protected | no valid hash-bound paired-vector/evaluator handoff | 125 required | BLOCKED; Selection not opened |
| A5 Final-872 | protected | protected | no result | 872 | NOT STARTED; pointer-only pending bundle, execution forbidden |

The apparent `0.41` discrepancy is thus explained only for the rows above: these
are OUT Recall@100 values in A1/A2/A3, not ALL values. Any document claiming the
same number as ALL without a corresponding manifest field must be corrected.

## 14. Local versus published evidence

Canonical controls, manifests and receipts under `control/`, `campaigns/` and
`outputs/` are the scientific source. `docs/progress_report/`, slides, dashboards,
Obsidian and MLflow are projections. Owner Store contains protected or large
artifacts and may contain the complete evaluator return; only aggregate-safe
projections are copied here.

The A3 Owner Store retains the complete attempt-scoped requests, stage receipts,
14 return receipts, result-integrity audit, safe-return receipt, HarnessOpt
evaluation, runtime assets and recovery logs. Only aggregate-safe evidence is
described here; protected rankings and per-query outcomes remain outside the
report. Complete A4 aggregate receipts are in
`<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/`.
The refreshed A4 publication artifact index is
`<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/A4_PUBLICATION_ARTIFACT_INDEX_REFRESHED_20260820.json`
with canonical `index_sha256` `337ed73bfdf0f5616a82081117e7243a0c0bab51c2b8f1224d54e4f3db9e58f1`
and file SHA-256 `ca5761a943ca75b03c26610a834d31b27c7750a523022f2fe2c6da71aef67ca0`.
It supersedes the earlier index hash `16a9f7e512eb7f36936aa7b62819aeb8a096713c1d96387ceec4d681efba1576`
while preserving that file as historical provenance. The refreshed index has
49 hash-bound records covering profile results, coverage/frontier/audit,
legal isolation, safe return, runtime/package identity, frozen representation
programs, adapter/model manifests, evaluator scope/handoff, launch and stage
receipts, and the current A5 pending transport. Protected payloads remain
outside the report and Git.

## 15. Cost, failures และ operational evidence

| Evidence | Value | Source/status |
|---|---:|---|
| A1 terminal cost | 11.161632 USD | progress report projection; receipt hash chain available |
| A2 whole-workload cost | 54.52666666666665948 USD | A2 closeout projection, VERIFIED |
| A2 forward hard stop | 60 USD | A2 closeout projection, VERIFIED |
| A3 hard cap | 35 USD | A3 goal/closeout, VERIFIED |
| Campaign amended ceiling | 180 USD | current project plan/control, VERIFIED as authorization, not spend |
| A1 failures | 0.0 mean per arm | A1 summary, VERIFIED |
| A2 failed candidates | 0 | A2 closeout, VERIFIED |
| A3 failure markers | 0 | A3 closeout, VERIFIED |
| A4 FAST cost | 0.6334513497072259 USD | Owner Store `FAST.json`, aggregate-safe |
| A4 BALANCED cost | 1.5818391125582612 USD | Owner Store `BALANCED.json`, aggregate-safe |
| A4 DEEP cost | 1.1815346193478262 USD | Owner Store `DEEP.json`, aggregate-safe |
| A4 ARM-03 research-reference cost | 1.2348912417435087 USD | Owner Store research-only receipt |
| A4 latency p50/p95/p99 (ms) | FAST 487.24/1524.23/1571.27; BALANCED 732.51/1771.50/2348.53; DEEP 314.43/1637.75/1817.28; ARM-03 327.71/1742.99/1899.35 | Four profile receipts |
| A4 throughput (qps) | FAST 0.02831; BALANCED 0.01134; DEEP 0.01518; ARM-03 0.01452 | Four profile receipts |
| A4 coverage / failures / determinism | 100/100 for each profile; 0 failures; deterministic=true | `A4_COMPLETE_PROFILE_COVERAGE.json`; `A4_RESULT_INTEGRITY_AUDIT.json` |

Known engineering repairs are preserved rather than counted as scientific
failures: A4 stale import repair, prepared-transport retry, and remote duplicate
request/output/log guard are present in the implementation and execution lineage.
The claim that their combined A4/A6 focused suite had exactly 21 tests is
**NOT VERIFIED** here because this report does not cite a machine-readable test
receipt. A3 local evaluator CLI mismatch was repaired and rerun against the same
14 receipts; no remote scientific operation was restarted.

## 16. Reproducibility และ leakage controls

Reproducibility is supported by frozen model revisions, program specs, source
hashes, candidate freeze receipt, append-only execution ledgers, isolated attempt
roots, safe-return receipts, deterministic family tie breaks, and result-integrity
audits. The controls require no model-weight change and fail closed on silent
truncation, incompatible partial results, protected export, Selection reuse, or
Final access.

No protected qrels, final labels, membership, rankings, per-query outcomes,
credentials or model/provider payloads were inspected for this report. The report
is therefore safe to commit, but it cannot replace the Owner-local evaluator return.

## 17. ข้อจำกัดและ threats to validity

1. A1/A2/A3 are development evidence; they do not estimate Final-872 performance.
2. ALL and IN aggregate metrics are missing from several canonical summaries;
   reporting OUT alone is intentional, but it limits subgroup interpretation.
3. DAPFAM relevance is citation-based and should not be interpreted as legal
   novelty, infringement, validity or freedom-to-operate.
4. ARM-03 has a research/non-commercial license and must be separated from a
   commercial deployment claim.
5. A3 Train-250 transfer results are bounded development evidence; they do not
   establish external generalization.
6. A4 profile coverage is complete and independently audited; Selection remains
   blocked by the missing hash-bound Selection-125 handoff, so no production
   winner can be claimed.
7. The protected concrete family example and exact hidden optimizer prompts are
   intentionally unavailable in Git (`MISSING`/`OWNER-LOCAL`).
8. A4 evidence is indexed in the refreshed Owner Store artifact index
   `A4_PUBLICATION_ARTIFACT_INDEX_REFRESHED_20260820.json` (index SHA-256
   `337ed73bfdf0f5616a82081117e7243a0c0bab51c2b8f1224d54e4f3db9e58f1`);
   use receipt paths and hashes as numeric authority.

## 18. สถานะปัจจุบันและ gates ถัดไป

| Gate | สถานะ | เงื่อนไขปิด |
|---|---|---|
| A4 profile transfer | PASS aggregate | four profiles complete; independent audit `PASS_A4_RESULT_INTEGRITY_AUDIT` |
| Commercial frontier | PASS diagnostic | FAST and DEEP are non-dominated; ARM-03 is research-only |
| Legal transfer | PASS isolated diagnostic / UNSUPPORTED | mini input/runtime unavailable; no full transfer; A5 reserve intact |
| Selection-125 | BLOCKED | blocker receipt `32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822`; required handoff absent |
| A5 Final-872 | NOT STARTED | `selection_accesses=0`, `final_accesses=0`; pointer-only bundle has `execution_permitted=false` |
| A6 full DAPFAM materialization | NOT STARTED | PASS A5 only; winner frozen, no feedback to selection |
| A7 publication/release | LOCKED | A6 closeout and Owner D3 |

At the current A4 closeout snapshot, instance `47790578` has completed all four
profile measurements and the workers have been torn down. A5/A6 must remain
closed until the missing hash-bound Selection-125 handoff is supplied and the
one-shot Selection preflight is independently validated.

# ภาคผนวก A: Evidence ledger

| Claim/metric | Value | Population | Queries | Run/attempt | Source | Hash/identity | Status |
|---|---|---|---:|---|---|---|---|
| A0 phase closeout | complete; no measurement | -- | 0 | `a0-phase-closeout-v1` | `campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json` | file SHA-256 `95614c498657a41f82fae9cf8f69b042773382cd714f91814524574b534a3a05` | VERIFIED |
| A1 coverage | 25/25 cells | OUT | 150/cell | `a12-v16-20260811-r15` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json` | summary file SHA-256 `e092ff9b3d9436fc3cb1d738b04a5e766b9131151ff4756cbd36eeac8731bad1`; terminal receipt SHA-256 `efd836c775b9bfabeadeb6d22c37cc16bfc3790d43d389ad1d277169a52b7bb7` | VERIFIED |
| A1 ARM-03 Recall@100 | 0.413400 | OUT | 150 | same | same summary | same hash-bound terminal receipt | VERIFIED |
| A1 ARM-04 Recall@100 | 0.340667 | OUT | 150 | same | same summary | same hash-bound terminal receipt | VERIFIED |
| A1 ARM-05 Recall@100 | 0.363733 | OUT | 150 | same | same summary | same hash-bound terminal receipt | VERIFIED |
| A2 candidate accounting | 52 total; 44 measured; 8 dormant; 0 failed | OUT aggregate | candidate-dependent | `a2-goal004-20260816-005` | `control/armindex/a2/a2-goal004-closeout-projection.v1.json` | observed file SHA-256 `6193e637bb070c01aa00f5f5ff2d1ebfb298a9d17a00dfd66d1669075bb1d209`; embedded `projection_sha256` `80ce52d3edcac62298b3b3ed96d685fe98d9bc8cd1e1f870147a2c742f40027a` | VERIFIED |
| A2 ARM-03 | 0.423000 Recall@100 | OUT | REP-DEV | same | same projection | result receipt SHA-256 `d1f8b55f6443d29539ccf8f051f7fd7169a9d47077306ac4b92da647db03f2ee` | VERIFIED tie |
| A2 ARM-04 | 0.358667 Recall@100 | OUT | REP-DEV | same | same projection | result receipt SHA-256 `a1446c06abbfe3d05fab3052f79af23b513146fd4c9d349b821dfc0c18b09416` | VERIFIED strict gain |
| A2 ARM-05 | 0.373667 Recall@100 | OUT | REP-DEV | same | same projection | result receipt SHA-256 `a2f1b0702e85d8df44e67df0085b407006d406f4620d3a71ef8cf337c419076a` | VERIFIED no strict gain |
| A3 strongest transfer | 0.419274 Recall@100 | OUT | 250 | `a3-goal003-20260818-028` | `<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-result-integrity-audit.json` | audit SHA-256 `3fbc601111b204d3d4829aab63cda2e4368f2b76fd08315c14f4c21abf820644`; observed file SHA-256 `02926c7e129e573ce4c14ccc2a86912d2b082609cc0da5cdf3a2758f41a29d75` | VERIFIED |
| A3 top-two RRF-60 | 0.418715 Recall@100 | OUT | 250 | same | same audit | safe-return receipt SHA-256 `48cb4c51680ec3e59a876dad9b3feaa0593c39585bf27ae4eaf1d50e950453dc`; observed file SHA-256 `6d11a589a1ff008a3d9b665e9a3c7deb5662f5bc1f2bd893569f3a59714bfc41` | VERIFIED |
| A3 HarnessOpt | 3/3 batches, 12 candidates, one signature | aggregate | 250 | same | `<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-harnessopt-owner-evaluation.json` | evaluation SHA-256 `547ed212febe8c70f6675ca9851e652d391940598fbfb39ec41394c8c453007a`; observed file SHA-256 `f163101a99792d1d98f7a9ad284ffbdd812c0ccb709daef82ddd794d607019dd` | VERIFIED flat |
| A4 FAST | 0.3458333333333334 Recall@100; 0.2927643693511339 nDCG@100; 0.24933704256908668 nDCG@10 | HDEV OUT contract; receipt population field MISSING | 100/100 | `a4-goal001-20260819T180000Z-a4x12` | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/FAST.json`; file SHA-256 `be9d7740c668882e2ed2f2ee36825be9d3b593eba0bacccf2a3242ebb7d419f9` | receipt field SHA-256 `965f4b8a72562ac29f3222e479842cfbfd9f6bae64aea95a753a3037c21502c8`; VERIFIED aggregate, deterministic, 0 failures |
| A4 BALANCED | 0.382638888888889 Recall@100; 0.32877720343200206 nDCG@100; 0.27844241266224945 nDCG@10 | HDEV OUT contract; receipt population field MISSING | 100/100 | same | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/BALANCED.json`; file SHA-256 `b7a2f5a3c24b47538fa3417f5de43b26cf911b998b522be0e41950be69b9333d` | receipt field SHA-256 `774477ea8f9cd550ff16eb70919eae1afe167e5b48186fb58d35433e17fbce5f`; VERIFIED aggregate, deterministic, 0 failures |
| A4 DEEP | 0.382638888888889 Recall@100; 0.32877720343200206 nDCG@100; 0.27844241266224945 nDCG@10 | HDEV OUT contract; receipt population field MISSING | 100/100 | same | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/DEEP.json`; file SHA-256 `287d17a7dd61d705ef12a30eeb00fe1af334fccbf6cd877eed79f160853dc5c1` | receipt field SHA-256 `886c29aeb2c14359a3e374b09a9f3a6f20d775b5f740bbbb686fde9f477dcbf0`; VERIFIED aggregate, deterministic, 0 failures |
| A4 ARM-03 research reference | 0.46319444444444446 Recall@100; 0.37293395839982973 nDCG@100; 0.3057748795608454 nDCG@10 | HDEV OUT contract; receipt population field MISSING | 100/100 | same | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/ARM-03_RESEARCH_REFERENCE.json`; file SHA-256 `98ca6d598c51cd5194baef59c9f922455dc7be9a026f568991b726ac0c5d8dca` | receipt field SHA-256 `53620ad3d2ec9637b684871384cb8b7462a52e37b63bc5547fdf0ade83de4157`; VERIFIED research-only, no commercial claim |
| A4 integrity / coverage | four profiles, each 100/100; deterministic; 0 failures | aggregate | 400 total units | same | `A4_COMPLETE_PROFILE_COVERAGE.json`; `A4_RESULT_INTEGRITY_AUDIT.json` | coverage SHA-256 `8e1e2e6a2e1a00a93ced7219f488ed9ebbc9bbfee8f79bb1f6796a7dabcb4653`; audit SHA-256 `08b83b848023c52967329b769d7b230cf7009290664e95ddd340d569bb0157b5` | `PASS_A4_RESULT_INTEGRITY_AUDIT` |
| A4 Selection handoff blocker | no hash-bound Selection-125 paired vectors/evaluator handoff; Selection/Final accesses 0 | OUT required | 125 required | same | `A4_SELECTION_HANDOFF_BLOCKER.json` | blocker receipt SHA-256 `32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822` | `BLOCKED_MISSING_SELECTION_125_HANDOFF` |
| Final-872 | unavailable | protected | 872 | none | no access | -- | CLOSED/NOT OPENED |

# ภาคผนวก B: Run inventory

| Phase | Terminal artifact | Scientific class | Coverage | Access |
|---|---|---|---|---|
| Migration Foundation | `a0-phase-closeout.receipt.v1.json` | engineering | 0 retrieval | no protected access |
| Common screening | `a12-v16-20260811-r15.summary.v16.json` | measured development aggregate | 25/25, 150 each | Selection/Final 0 |
| Per-arm search | `a2-goal004-closeout-projection.v1.json` | measured development aggregate | 44 measured of 52 | Selection/Final 0 |
| Transfer/HarnessOpt | `update_A3_19AUG2026.md` plus safe return/audit | measured development aggregate | 14/14, 250 each | Selection/Final 0 |
| Production transfer | A4 x12 four-profile receipts, coverage, frontier and integrity audit | development/production preparation | 4 x 100/100; 0 failures; deterministic | Selection not yet valid |
| Final confirmation | no receipt | protected final | 0 | Final closed |
| Full corpus materialization | no receipt | future post-confirmatory | 0 | requires A5 PASS |

# ภาคผนวก C: Metric dictionary

| Term | Definition |
|---|---|
| ALL | all benchmark families/queries in the declared evaluation population |
| IN | in-domain partition |
| OUT | held-out technical-domain partition; primary ArmIndex population |
| Recall@100 | relevant-family exposure among first 100 families |
| nDCG@k | discounted ranking gain through rank k |
| p50/p95/p99 | latency percentiles |
| strict gain | primary metric exceeds frozen comparator under preregistered rule |
| numerical tie | equality within recorded numerical tie rule; no post-hoc tiebreak |
| dormant | reserved, not activated, no result implied |
| failed | declared scientific failure state, distinct from recoverable infrastructure error |
| coverage | completed valid units divided by required units |
| determinism | repeated frozen execution yields identical aggregate/ranking behavior under contract |

# ภาคผนวก D: Model/configuration inventory

Canonical files:

- `control/armindex/a1.2/model-locks/ARM-01.v1.json` through `ARM-05.v1.json`
- `control/armindex/a1.2/common-program-set.v11.json`
- `control/armindex/a2/candidate-freeze.lock.v1.json`
- `control/armindex/a4/a4-readiness-contract.v1.json`
- `control/armindex/a6/a6-full-dapfam-execution-contract.v1.json`

The A2 official candidate-freeze bridge binds official model `gpt-5.6-sol`, CLI/SDK
`0.144.4`, and high reasoning effort. The retrieval model revisions and templates
are listed in Section 6. A3 fixed controls use RRF-60 where stated. A4 profile
contracts require FAST, BALANCED and DEEP to be distinct, commercial-capable
profiles; ARM-03 may appear only as a license-segregated research reference.

Exact agent conversation prompts, protected evaluator prompts, qrels-derived
diagnostics and model payloads are Owner-local and therefore **NOT VERIFIED in Git**.

# ภาคผนวก E: Publication-impact artifact register

ทะเบียนนี้รวบรวม artifacts ที่มีผลต่อการตีพิมพ์หรือการตรวจซ้ำ โดยไม่คัดลอก
protected payloads เข้ามาใน Git

| Artifact class | Canonical path / pointer | Role | Authority/status |
|---|---|---|---|
| Source-of-truth routing | `control/source-of-truth.yaml`; `control/campaigns/armindex-multiretriever-v2.yaml`; `control/program.yaml` | canonical authority ordering, campaign budget/gates and active eight-phase registry | control authority / VERIFIED |
| Research plan | `PLAN.md`; `docs/research/ARMINDEX_RESEARCH_PLAN_V02.md` | hypothesis, phase routing, split and metric intent | control authority / VERIFIED |
| A0 closeout | `campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json` | migration and safety boundary | engineering receipt / VERIFIED |
| A1 program grammar | `control/armindex/a1.2/common-program-set.v11.json` | exact P00--P04 fields, segmentation, aggregation and hashes | frozen control / VERIFIED |
| A1 model locks | `control/armindex/a1.2/model-locks/ARM-01.v1.json`, `control/armindex/a1.2/model-locks/ARM-02.v1.json`, `control/armindex/a1.2/model-locks/ARM-03.v1.json`, `control/armindex/a1.2/model-locks/ARM-04.v1.json`, `control/armindex/a1.2/model-locks/ARM-05.v1.json` | model IDs, revisions, license, prompt, pooling, dimensions | frozen control / VERIFIED |
| A1 machine result | `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json` | 25/25 aggregate arm results | numeric authority / VERIFIED |
| A1 EDA | `campaigns/armindex-multiretriever-v2/evidence/a1.2-cell-eda/a12-v16-20260811-r15.eda.v16.json`; `outputs/tables/armindex/a12-v16-20260811-r15.cell-eda.v16.csv` | cell-level aggregate EDA | derived evidence / VERIFIED |
| A1 figures | `outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.png`; `outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.svg`; `outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.png`; `outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.svg` | quality/efficiency figures | publication projection / VERIFIED |
| A2 candidate freeze | `campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json`; `control/armindex/a2/candidate-freeze.lock.v1.json` | 52-candidate premeasurement lock | frozen receipt / VERIFIED |
| A2 closeout | `control/armindex/a2/a2-goal004-closeout-projection.v1.json` | 52/44/8/0 accounting, arm outcomes, cost and claim boundary | canonical projection bound to Owner Store / VERIFIED |
| A2 measured authority | `control/armindex/a2/measured-authority/a2-goal004-20260816-005.authority.v4.json` | allowed evaluator, candidate and protected-output boundary | control receipt / VERIFIED |
| A2 figures | `outputs/figures/armindex/a2-goal004/` | coverage, reserve path, outcomes and frontier | publication projection / VERIFIED |
| A3 controls | `control/armindex/a3/a3-three-primary-preparation-manifest.v1.json`; `control/armindex/a3/a3-three-primary-preparation-authority.v1.json` | three-primary scope and HarnessOpt limits | preparation controls / VERIFIED |
| A3 result audit | `<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-result-integrity-audit.json` | 14-operation integrity, per-operation hashes and coverage | numeric authority / `PASS_A3_RESULT_INTEGRITY_AUDIT` |
| A3 safe return | `<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-safe-return-receipt.json` | aggregate-only return and protected-output scan | safe-return authority / `PASS_A3_AGGREGATE_SAFE_RETURN` |
| A3 aggregate results | `<MYIS_ROOT>/04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-return-receipts/` | 9 transfer + 5 control receipts | Owner-local measured evidence / VERIFIED |
| A3 EDA | `docs/progress_report/A3_transfer_matrix_eda_20260819.csv`; `docs/progress_report/A3_fixed_controls_eda_20260819.csv` | tables and figure inputs | derived projection; hashes below |
| A3 figures | `docs/progress_report/figures/a3-transfer-recall-heatmap-20260819.png`; `docs/progress_report/figures/a3-fixed-control-quality-20260819.png` | transfer/fusion publication figures | derived projection / VERIFIED |
| A3 code/audit | `scripts/audit_a3_three_primary_results.py`; `scripts/evaluate_a3_three_primary_owner_local.py`; `scripts/evaluate_a3_harnessopt_owner_local.py` | independent audit and aggregate evaluator | reproducibility code / VERIFIED |
| A4 readiness | `control/armindex/a4/a4-readiness-binding-20260819.json`; `control/armindex/a4/a4-readiness-contract.v1.json` | frozen A4 profiles, selection counters and legal isolation | contract-only authority / VERIFIED |
| A4 admission | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/admission/` | fresh identity, quote, TTL, budget and runtime probes | provider admission lineage / VERIFIED |
| A4 profile results | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/{FAST,BALANCED,DEEP,ARM-03_RESEARCH_REFERENCE}.json` | four 100/100 aggregate quality/resource receipts | Owner-local numeric authority / VERIFIED |
| A4 coverage/frontier/audit | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/{A4_COMPLETE_PROFILE_COVERAGE,A4_COMMERCIAL_FRONTIER,A4_RESULT_INTEGRITY_AUDIT}.json` | completeness, commercial frontier and independent integrity | canonical aggregate authority / VERIFIED; `PASS_A4_RESULT_INTEGRITY_AUDIT` |
| A4 publication artifact index | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/A4_PUBLICATION_ARTIFACT_INDEX_REFRESHED_20260820.json` | 49 publication/reproducibility pointers plus claim boundary | index SHA-256 `337ed73bfdf0f5616a82081117e7243a0c0bab51c2b8f1224d54e4f3db9e58f1` / VERIFIED |
| A4 Selection blocker | `<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations/A4_SELECTION_HANDOFF_BLOCKER.json` | missing hash-bound Selection-125 handoff | blocker SHA-256 `32e5a634b40226a9af2f766fb0f2949a539d3c869968d10324056f25ac839822` / BLOCKED |
| A5 pending bundle | `<MYIS_ROOT>/04_Owner_Stores/armindex/a5/a5-pending-a4-selection-20260820T174500Z/` | pointer-only template, validation, code identity, manifest, goal and safe-transport receipt | `execution_permitted=false`; Selection/Final accesses 0; VERIFIED pending-only |
| A4/A5 artifact-index validation | `A4_PUBLICATION_ARTIFACT_INDEX_REFRESHED_20260820.json` plus 49 referenced files | canonical self-hash and per-file SHA-256 validation | `PASS_INDEX_HASH_AND_ARTIFACT_VALIDATION` |
| A6/A7 phase amendment | `control/armindex/a6/a6-a7-phase-amendment.v1.json`; `docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md`; `docs/goal/A7_PUBLICATION_AND_RELEASE_goal_001.md` | moves publication/release to A7; preserves A6 as post-confirmatory, non-adaptive full-corpus materialization | owner-approved routing / VERIFIED |
| A6 pending bundle | `control/armindex/a6/a6-pending-a5-closeout-template.v1.json`; `control/armindex/a6/a6-full-dapfam-execution-contract.v1.json` | post-confirmatory full-corpus contract | execution forbidden until `PASS_A5_FINAL_CONFIRMATION` |
| Literature | `evidence/literature/digests/` and `evidence/literature/source/` | primary-source design inheritance | literature authority for related work |
| Advisor reports | `docs/progress_report/update_A0_A1_A2_18AUG2026.md`; `update_A3_19AUG2026.md` | human-readable projections | informative, not numeric authority |

### Publication figures and tables

Figures suitable for advisor or manuscript drafting are indexed by
`docs/progress_report/A0_A1_A2_figure_index_20260818.csv`,
`docs/progress_report/A0_A1_A2_phase_summary_figure_20260818.csv`,
`docs/progress_report/A1_A2_quality_frontier_figure_20260818.csv`,
`docs/progress_report/A1_common_screen_aggregate_eda_20260818.csv`,
`docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv`,
`docs/progress_report/A3_transfer_matrix_eda_20260819.csv` and
`docs/progress_report/A3_fixed_controls_eda_20260819.csv`. Companion figures
are under `docs/progress_report/figures/` and `outputs/figures/armindex/`.

### Safe evidence invariant

The following are intentionally absent from this report and all Git projections:
protected membership, qrels, raw query/family IDs, rankings, per-query outcomes,
credentials, raw provider payloads and model weights. Their absence is a
publication-safety property, not missing work. The corresponding safe hashes and
aggregate receipts remain available in Owner Store.

### EDA projection hashes

| File | SHA-256 |
|---|---|
| `docs/progress_report/A3_transfer_matrix_eda_20260819.csv` | `c624a77af1c1fdcd22adcf29a1720aaebefda2006a85197ebcf15fb525ab6d39` |
| `docs/progress_report/A3_fixed_controls_eda_20260819.csv` | `f8e280c1a2f3cc8683ffed2061d27c10fab9f2f3b8931f5c1b527dc4a4f6daf2` |
| `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json` | `e092ff9b3d9436fc3cb1d738b04a5e766b9131151ff4756cbd36eeac8731bad1` |
| `control/armindex/a2/a2-goal004-closeout-projection.v1.json` | `6193e637bb070c01aa00f5f5ff2d1ebfb298a9d17a00dfd66d1669075bb1d209` |

# ภาคผนวก F: References

1. DAPFAM, “A Domain-Aware Family-level Dataset to benchmark cross-domain patent retrieval,” primary source digest `evidence/literature/digests/U011_dapfam_digest.md`.
2. AutoIndex, “Learning Representation Programs for Retrieval,” arXiv:2607.18603, source digest `U154_autoindex_learning_representation_programs_for_retrieval_digest.md`.
3. GEPA, “Reflective Prompt Evolution Can Outperform Reinforcement Learning,” source digest `U058_gepa_reflective_prompt_evolution_can_outperform_reinforcement_learning_digest.md`.
4. SkillOpt, “Executive Strategy for Self-Evolving Agent Skills,” arXiv:2605.23904, source digest `U082_skillopt_executive_strategy_for_self-evolving_agent_skills_digest.md`.
5. Thakur et al., “BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models,” source digest `U083_beir_a_heterogeneous_benchmark_for_zero-shot_evaluation_of_information_r_digest.md`.
6. Patent embedding and patent retrieval references are catalogued under `evidence/literature/digests/U001`--`U054`, with PatenTEB-related material in the repository literature index.

## Verified conclusions

1. The project has a valid frozen, receipt-bound development pipeline from migration through A3.
2. Representation quality is retriever-conditioned in the measured development evidence; one universal representation claim is unsupported.
3. A2 has 44 valid measured candidates, 8 dormant reserves and 0 scientific failures; dormant is not null or failure.
4. A3 transfer and fixed-fusion evidence is complete and shows an adapter interaction plus a flat HarnessOpt surface.
5. A4 has complete four-profile aggregate coverage and a passing independent
   integrity audit; Selection/A5 remain closed because the Selection-125 handoff
   is missing.

## Unresolved inconsistencies

- Older projections/slides may use values near `0.41` without stating ALL versus OUT. Canonical summaries support OUT for the values quoted here; older unlabeled values remain **INCONSISTENT**.
- ALL and IN aggregates are not present in the A1/A2/A3 summary surfaces used here. They must not be inferred from OUT.
- The exact hidden optimizer conversation prompts and protected family example are not in the safe repository projection.
- A4 aggregate profile receipts are Owner-local and now projected here; the
  receipt schema omits an explicit ALL/IN/OUT field, so population labeling is
  retained as MISSING rather than inferred.

## Missing artifacts

- Selection-125 paired-vector/evaluator handoff and frozen finalist registry.
- Isolated legal-transfer mini/full receipts (mini is currently UNSUPPORTED).
- One-shot Selection preflight, registry hash, bootstrap confidence intervals and W/T/L evidence.
- A5 Final-872 receipt and immutable final registry.
- A6 full-corpus materialization receipt, coverage/failure taxonomy and resource ledger.
- ALL/IN metric fields for every development result where absent from canonical summaries.

## Claims that must not yet be made

- No claim of Final-872 or protected-test performance.
- No claim that ArmIndex improves DAPFAM universally or that ARM-03 is deployable commercially.
- No claim that HarnessOpt improved quality; the measured result is a flat surface.
- No claim that FAST or DEEP is a confirmed production winner; the four A4 profiles are complete, but Selection is still unopened.
- No claim of legal novelty, infringement, validity or freedom-to-operate from DAPFAM citation relevance.
- No claim that A6 full-corpus processing improves retrieval quality; it can only establish post-confirmatory operational scalability after A5.

## Recommended next experimental gates

1. Supply and independently validate the missing hash-bound Selection-125 paired-vector/evaluator handoff; do not synthesize it from HDEV-100 outputs.
2. Freeze the finalist registry and run the one-shot Selection only with zero pre-Selection counter violations.
3. Preserve the isolated legal-transfer UNSUPPORTED diagnostic and A5 reserve while preparing the valid handoff.
4. Open A5 Final-872 only after automatic A4 PASS, conditional D2, safe return, independent audit and pointer-only bundle checks pass.
5. Prepare A6 only after A5 closes: one frozen winner, full DAPFAM materialization, coverage/resource/failure/determinism receipts, and no feedback into winner selection.
6. Reconcile ALL/IN/OUT fields and unlabeled `0.41` values before publication drafting; preserve every negative and dormant outcome.
