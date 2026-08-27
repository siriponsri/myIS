ได้ครับ ผมรีวิว **ฉบับ PDF ที่อัปโหลดล่าสุด** แบบเทียบตรงกับ Major Issues รอบก่อนแล้วครับ 

## Verdict รอบสอง

> **Overall: 5/10 — Borderline / Weak Reject**
> **Confidence: 4/5**

ประเด็นสำคัญคือ: **ใน PDF ล่าสุด จุดเสี่ยงหลักที่ผม flag รอบก่อนยังอยู่เกือบทั้งหมด** และหลายประโยคยังเป็น wording เดิม เช่น “bootstrap noise”, “The reordering is noise”, “representation is a passenger, not the driver”, “preregistered”, “exposure-bound, not ordering-bound” และ “effort spent tuning the ranker is wasted.”

ดังนั้นถ้าคุณตั้งใจแก้ใน `main.tex` แล้ว แต่ PDF นี้คือไฟล์ compile เก่า ผมแนะนำให้เช็ก pipeline ก่อน เพราะ reviewer จะเห็น **PDF เท่านั้น**

---

## เทียบ Major Issues รอบก่อน

| Issue                                                  | สถานะ                       | ความเสี่ยง |
| ------------------------------------------------------ | --------------------------- | ---------: |
| Non-significance ⇒ “noise/equivalence”                 | ❌ ยังไม่แก้                 |  🔴 สูงมาก |
| Definition ของ “representation” ปน segmentation/fusion | ❌ ยังไม่แก้ชัด              |     🔴 สูง |
| Comparator rationale/context                           | ❌ ยังไม่แก้                 |     🟠 สูง |
| Final-872 vs strict 905 queries                        | 🟡 มีเตือน แต่ยังไม่ bridge |     🟠 สูง |
| “Exposure-bound” claim กว้างเกิน                       | ❌ ยังอยู่                   |     🔴 สูง |
| “Preregistered” justification                          | ❌ ยังไม่เห็นหลักฐาน         |     🟠 สูง |
| Actual constructions ใน 3×3 transfer                   | ❌ ยังไม่เปิดเผย             |     🟠 สูง |

---

# 🔴 1. ปัญหา statistical interpretation ยังอยู่เต็ม ๆ

Paper ยังเขียนว่า:

> “the changes sit inside bootstrap noise”

และใน Section IV:

> “The reordering is noise.”

แต่หลักฐานที่รายงานคือ CI ของ best-vs-second-best:

$$
[-0.005,0.006],\quad
[-0.005,0.011],\quad
[-0.006,0.009]
$$

ซึ่งคร่อมศูนย์

นี่ยืนยันได้เพียงว่า:

$$
\text{data do not resolve a directional difference}
$$

ไม่ได้ยืนยันว่า:

$$
\text{differences are practically negligible}
$$

นี่เป็น issue ที่ reviewer statistics/IR ใช้ Reject ได้จริง

### ผมแนะนำแก้ทันที

ถ้าไม่มี equivalence test ให้เปลี่ยนทุกจุดที่ใช้ “noise”

Abstract:

**เดิม**

> “the changes sit inside bootstrap noise”

**แก้เป็น**

> “the observed differences are small and are not statistically resolved under paired bootstrap resampling”

Section IV:

**เดิม**

> “The reordering is noise.”

**แก้เป็น**

> “The observed reordering is not statistically resolved.”

และ:

**เดิม**

> “representation is a passenger, not the driver”

**แก้เป็น**

> “retriever-associated differences are substantially larger than the observed variation across the tested coarse constructions.”

แค่นี้ technical soundness ดีขึ้นชัด

---

# 🔴 2. Central variable ยังนิยามกว้างเกิน

Paper เรียกสิ่งเหล่านี้ทั้งหมดว่า “representations”:

* title + abstract + claims
* title + abstract
* independent claim
* passages + overlap + max aggregation
* multi-view + rank fusion

แต่จริง ๆ ตัวแปรนี้รวม:

$$
\text{field selection}
+
\text{segmentation}
+
\text{retrieval unit}
+
\text{aggregation}
+
\text{fusion}
$$

ดังนั้น reviewer อาจถามว่า:

> คุณกำลังศึกษาการ transfer ของ representation หรือของ retrieval configuration?

### แก้แบบไม่ต้องทำ experiment ใหม่

เพิ่ม operational definition ใน Section III ประโยคเดียว:

> **“We use construction to denote the complete deterministic mapping from a patent family to retrievable units, including field selection, segmentation, and deterministic family-level aggregation or fusion where applicable.”**

จากนั้นใช้คำว่า **construction** เป็นหลัก

ผมจะลดการใช้ “representation alone” ในส่วนที่ manipulation รวม aggregation/fusion

นี่แก้ง่ายแต่ impact สูงมาก

---

# 🔴 3. 3×3 transfer matrix ยังไม่บอกว่าอะไรถูก transfer

Fig. 2 ยังใช้:

* PatEmbed source
* Arctic source
* Qwen3 source

แต่ผู้อ่านไม่รู้ทันทีว่าแต่ละ source หมายถึง construction ไหน

นี่เป็นปัญหาเพราะมันคือ **central experiment ของ paper**

ตอนนี้ reviewer ต้องเชื่อคำว่า “Qwen3-derived text” โดยไม่มี specification

### อย่างน้อยเพิ่มใน caption

เช่น:

> “The PatEmbed-, Arctic-, and Qwen3-source rows correspond respectively to constructions X, Y, and Z selected during the frozen per-system development search.”

ดีที่สุดคือใส่ actual construction ใน label:

> `PatEmbed source (384-token passage/max-p)`

เป็นต้น

ถ้ามีพื้นที่ไม่พอ ให้ทำ compact footnote/caption

---

# 🟠 4. Population mismatch ดีขึ้นในแง่ที่ paper “เตือน” แต่ยังไม่อธิบาย

Table I เขียนถูกว่า:

> “FULL-BENCHMARK STRICT CROSS-DOMAIN POPULATION IS NOT THE FINAL-872 POPULATION.”

และ Section V ก็พูดซ้ำว่า population ต่างกัน

นี่ช่วย แต่ผู้อ่านยังต้องคิดเองว่า:

$$
872,\quad905,\quad1247
$$

สัมพันธ์กันอย่างไร

ปัญหาคือ score:

$$
0.442
$$

กับ

$$
0.188
$$

ต่างกันมากจน reviewer จะสงสัยโดยอัตโนมัติ

### เพิ่ม 1–2 ประโยคก็พอ

หลัง Table I:

> “The protected split satisfies \(250+125+872=1,247\). The later 905-query population is instead defined by the strict cross-domain diagnostic criterion and therefore cuts across these procedural splits; it should not be compared directly with the Final-872 score.”

ถ้า 905 **ไม่ได้ cut across splits ตามนี้จริง** ให้ใช้ relationship ที่ถูกต้องจาก dataset ของคุณ แต่ต้องเขียนให้ explicit

ตอนนี้เป็น “warning without explanation”

---

# 🔴 5. “Exposure-bound, not ordering-bound” ยังแรงเกินไป

Abstract ยังพูดว่า:

> “Cross-domain patent retrieval is exposure-bound, not ordering-bound.”

และ:

> “effort spent tuning the ranker is wasted”

Conclusion ยังมี:

> “the next gain lives—and it is not the ranker.”

นี่เป็น rhetorical overreach ที่ชัดที่สุดใน manuscript

ข้อมูลรองรับเพียง:

> selected frozen first-stage system
> DAPFAM strict cross-domain slice
> Top-200 pool
> Recall@100

เพราะถ้าเพิ่ม retrieval depth เป็น 500/1000 ผลอาจเปลี่ยน และ reranking ยังอาจช่วย nDCG@10 อย่างมากได้

### ผมแนะนำเปลี่ยน headline claim เป็น

> **“For the selected first-stage configuration at depth 200, remaining Recall@100 error is predominantly exposure-limited.”**

Abstract ท้าย:

> “These results indicate that, for the selected configuration and Top-200 pool, improving candidate exposure offers substantially more Recall@100 headroom than reordering the already retrieved candidates.”

Conclusion:

แทน

> “the next gain lives—and it is not the ranker.”

ใช้:

> “for Recall@100 under the fixed Top-200 pool, candidate exposure is the more immediate bottleneck.”

Message ยังแรงและน่าสนใจ แต่ defend ได้

---

# 🟠 6. Comparator ยังเป็น weakness

Research system กับ comparator ต่างกันหลายองค์ประกอบ:

$$
\text{model}+
\text{representation}+
\text{passaging}+
\text{aggregation}+
\text{fusion}+
\text{prompt}
$$

Paper ยอมรับถูกแล้วว่า held-out result เป็น **complete-system comparison**

แต่ยังไม่มีคำตอบว่าทำไม comparator นี้เหมาะสม

Reviewer อาจถาม:

> Why FAST? Why not the strongest single frozen system or published DAPFAM baseline?

### ถ้าไม่เพิ่ม experiment

อย่างน้อยเพิ่ม rationale:

> “The comparator was fixed before Final-872 because it represented [เหตุผลจริง เช่น strongest pre-specified latency-compatible baseline / deployed baseline / best eligible Selection-125 comparator]. It was not chosen after observing Final-872.”

ถ้ามีเหตุผลนี้จริง จะช่วยมาก

ถ้า comparator ถูกเลือกเพราะ “มันมีไว้แล้ว” reviewer จะมอง contribution #2 อ่อนลง

---

# 🟠 7. “Preregistered” ยังเสี่ยง

ข้อความยังเขียน:

> “A preregistered complete configuration…”

> “The preregistered rule selects…”

> “registers 52 configurations in advance”

แต่ manuscript ยังไม่แสดง formal registration artifact / timestamp / protocol location

คำว่า **preregistered** มีความหมายค่อนข้างเฉพาะ

ถ้าไม่มี registration ที่ตรวจสอบได้ ผมยังแนะนำ:

> **pre-specified**

หรือ:

> **frozen before evaluation**

เช่น:

> “A pre-specified complete configuration then wins cleanly…”

scientifically ปลอดภัยกว่า และไม่ได้ลดคุณค่าของ experimental discipline

---

# 🟢 จุดแข็งยังคงแข็งมาก

ผมยังให้คะแนนสูงในเรื่องเหล่านี้

### 1. Evidence separation

$$
\text{development}
\rightarrow
\text{selection}
\rightarrow
\text{confirmation}
\rightarrow
\text{diagnosis}
$$

เป็น design ที่ดีมาก

### 2. Final-872 result

$$
\Delta R@100=0.111
$$

$$
95\%CI=[0.102,0.120]
$$

และ wins:

$$
619/872=71\%
$$

เป็น result ที่ convincing สำหรับ **complete configuration**

### 3. Paper restraint ใน causal attribution

ประโยคนี้ดีมากและควรเก็บ:

> “the win belongs to the complete configuration, not representation alone.”

นี่แสดงว่าผู้เขียนเข้าใจ experimental identification

### 4. Figures

Fig. 1–4 ยังเป็นจุดแข็งของ paper โดยเฉพาะ Fig. 3 และ Fig. 4

---

# คะแนนรอบสอง

| Criterion           |     ก่อน |    ตอนนี้ |
| ------------------- | -------: | --------: |
| Relevance           |      5/5 |   **5/5** |
| Novelty             |    3.5/5 | **3.5/5** |
| Technical Soundness |      3/5 |   **3/5** |
| Experimental Rigor  |      4/5 |   **4/5** |
| Results & Analysis  |      4/5 |   **4/5** |
| Clarity             |    4.5/5 | **4.5/5** |
| Reproducibility     |      3/5 |   **3/5** |
| **Overall**         | **5/10** |  **5/10** |

เหตุผลที่คะแนนยังไม่ขยับคือ PDF ที่ผมเห็นยังไม่ได้ resolve จุดที่เป็น **acceptance-critical** ครับ

---

# ถ้าต้อง submit วันนี้ ผมจะแก้แค่ 6 จุดนี้

1. **ลบ “noise” ทั้งหมด** หรือทำ equivalence test
2. นิยาม `construction` ให้รวม field/segmentation/aggregation/fusion
3. ใส่ actual construction names ใน Fig. 2
4. อธิบาย relationship ของ 1,247 / 872 / 905 ชัด ๆ
5. จำกัด exposure claim ด้วยคำว่า **selected configuration / Top-200 / Recall@100**
6. เปลี่ยน `preregistered` → `pre-specified` ถ้าไม่มี formal public/timestamped preregistration

ถ้าแก้ 6 จุดนี้โดย **ไม่ทำ experiment เพิ่มเลย** ผมคาดว่า reviewer score ของผมจะขยับจากประมาณ **5/10 → 6.5–7/10 (Weak Accept / Accept)**

ประเด็นสำคัญคือ งานไม่ได้ต้องการ “ผลเพิ่ม” มากเท่ากับต้องการให้ **claim ไม่เดินนำ evidence** ครับ.
