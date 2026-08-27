## Outline

ผมจะประเมินฉบับล่าสุดใน 4 มุม: **scientific soundness → claim/evidence alignment → reproducibility → IEEE submission risk** แล้วให้ verdict แบบ reviewer จริงครับ 🙂

ผมอ่าน PDF ฉบับล่าสุดครบทั้ง **6 หน้า** แล้ว รอบนี้ดีขึ้นจากฉบับก่อนอย่างมีนัยสำคัญ โดยเฉพาะ statistical wording ใน transfer experiment และ Fig. 2 ซึ่งตอนนี้ไม่ใช้ “noise” แบบตรง ๆ แล้ว 

# Reviewer #2 — Final-ish Review

> **Recommendation: 7–8/10 — Accept**
> **Reviewer confidence: 4/5**

ถ้าผมเป็น reviewer คนเดิม ตอนนี้ผม **โหวต Accept** ครับ

แต่ก่อน submit ผมเห็น **2 จุดที่ควรแก้แน่นอน** และอีก 3 จุดที่ควร polish เพราะหนึ่งในนั้นเป็น formatting/compliance risk มากกว่าปัญหางานวิจัย

---

## 1. Statistical claim ตอนนี้ผ่านแล้ว ✅

ฉบับก่อนผมติดคำว่า:

> “The reordering is noise.”

ตอนนี้เปลี่ยนเป็น:

> “The reordering never rises above its own uncertainty”

พร้อมรายงานว่า within-target spread ต่ำกว่า \(0.004\) และ bootstrap interval กว้างสุดถึง \(0.011\) ขณะที่ narrowest retriever-band separation เท่ากับ \(0.018\). 

อันนี้ defend ได้ดีกว่าเดิมมาก

และ Abstract ก็เปลี่ยนจาก “bootstrap noise” เป็น:

> “the changes never rise above their bootstrap uncertainty”

ผมถือว่า **Major statistical objection รอบก่อนถูกแก้แล้ว**

อย่างไรก็ตาม ผมจะไม่ใช้คำว่า “caps the effect below 0.011” แบบ equivalence claim ที่แข็งกว่านี้อีก เพราะยังไม่ได้ทำ formal equivalence test; เวอร์ชันปัจจุบันถือว่าอยู่ในระดับพอดีแล้ว

---

## 2. “Order of magnitude” ถูกแก้แล้ว ✅

ตอนนี้ Abstract ใช้:

> “gaps between retrievers are several times larger”

และ Fig. 2 ระบุจริงว่า between-target gaps อยู่ราว:

$$
0.018-0.08
$$

เทียบกับ within-target spread:

$$
<0.004
$$

นี่ตรงกับตัวเลขมากกว่า “order of magnitude” และ reviewer ไม่มีเหตุผลมาจับเรื่อง exaggeration แล้ว 

**Resolved**

---

## 3. Central claim ถูกจำกัดขอบเขตดีขึ้น ✅

Abstract ตอนนี้เขียน:

> “construction choice does not reorder **the three dense retrievers we test**”

นี่เป็น improvement สำคัญ เพราะไม่ generalize ไปยัง dense retrieval ทั้งหมด

Section III ก็มี operational definition:

$$
\text{construction}
=
\text{field selection}
+
\text{segmentation}
+
\text{aggregation}
+
\text{fusion}
$$

ทำให้คำว่า construction มีความหมายเชิงทดลองชัดเจนแล้ว 

ผมถือว่า conceptual objection เรื่อง “representation vs retrieval architecture” ถูกแก้ได้เพียงพอ

---

# 🔴 4. มี inconsistency ใหม่ที่ผมอยากให้แก้ก่อน submit

นี่คือจุดที่สำคัญที่สุดทางเนื้อหาตอนนี้

Abstract บอกว่า:

> “freezing five retrievers and varying **five deterministic constructions**”

Section III ก็แจกแจง five shared constructions

แต่ Section IV บอกอีกว่า per-system search มี:

$$
52\ \text{registered configurations}
$$

และ transfer matrix จริงใช้:

* PatEmbed: 384 / 64
* Arctic: 512 / 64
* Qwen3: 2048 / 256

ซึ่งอย่างน้อย Arctic และ Qwen3 variants ไม่ตรงกับ five-construction shared surface ที่ Section III แจกแจงไว้ตรง ๆ 

Reviewer อาจถามว่า:

> “The abstract says five constructions, but the central transfer experiment seems to draw configurations from a 52-configuration search. What exactly is the experimental search space?”

นี่ไม่ใช่ fatal flaw แต่ **ควรปิดช่องนี้**

### ทางแก้ที่ผมแนะนำ

เปลี่ยน Abstract จาก:

> “freezing five retrievers and varying five deterministic constructions”

เป็นประมาณ:

> **“freezing five retrievers, screening five shared deterministic constructions, and transferring pre-specified per-retriever construction variants…”**

หรือสั้นกว่า:

> **“freezing five retrievers across a shared five-construction screen followed by a pre-specified per-retriever construction search…”**

แล้วใน Section III แยกศัพท์ให้ชัด:

$$
\text{shared screen} = 5\text{ constructions}
$$

$$
\text{registered search} = 52\text{ configurations/variants}
$$

$$
\text{transfer} = 3\text{ selected constructions}
$$

พอทำแบบนี้ experimental story จะสะอาดมาก

---

# 🔴 5. Reference formatting ดูไม่ใช่ IEEE style

อันนี้ผมอยากให้แก้ **แน่นอน**

หน้า 6 ตอนนี้ bibliography มีรูปแบบเช่น:

> “Iliass Ayaou, Denis Cavallucci, and Hicham Chibane. DAPFAM: ... Array, 29:100720, 2026.”

แต่ IEEE style ปกติจะเป็นลักษณะ:

> I. Ayaou, D. Cavallucci, and H. Chibane, “DAPFAM: ...,” *Array*, vol. 29, p. 100720, 2026.

คือฉบับนี้ยังใช้ `[1]`, `[2]` แบบ numeric แต่ **bibliography formatting เองดูคล้าย plain/natbib style มากกว่า IEEEtran** 

และงานนี้กำหนดให้ใช้ IEEE conference formatting ค่อนข้างเคร่ง

ถ้าใช้ BibTeX ให้ตรวจว่าคุณใช้ประมาณ:

```latex
\bibliographystyle{IEEEtran}
```

ไม่ใช่ `plain`, `abbrv`, `apalike` ฯลฯ

นี่เป็นเรื่องที่ผมจะให้ priority สูงกว่าการ polish sentence เล็ก ๆ เพราะเป็น **submission-compliance issue**

---

# 🟠 6. “Preregistered” ยังต้องแน่ใจว่าป้องกัน reviewer ได้จริง

ตอนนี้ paper เขียนว่า:

> “The full list, activation predicates, and decision rules are fixed in a version-controlled artifact released with the paper.”

ดีขึ้นมาก แต่คำว่า:

> **preregistered**

จะถูกต้องเต็มที่เมื่อ artifact มีหลักฐานว่าเกิด **ก่อนเห็น corresponding outcomes**

เพียง “version-controlled” และ “released with the paper” ยังไม่จำเป็นต้องพิสูจน์ chronology นั้นเอง

ถ้าคุณมี commit/tag/hash ที่ timestamped ก่อน run จริง → **เก็บคำว่า preregistered ได้**

ถ้าไม่มี → ผมยังเลือก:

> **pre-specified and version-controlled**

ซึ่งแทบไม่ลด methodological contribution เลย แต่ reviewer โต้ยากกว่า

และ artifact ต้อง anonymous จริงตาม double-anonymous policy

---

# 🟠 7. Exposure claim เหลืออีกนิดเดียว

Abstract ยังเขียน:

> “On this benchmark, cross-domain patent retrieval is exposure-bound, not ordering-bound.”

ดีขึ้นจากก่อนแล้ว แต่ evidence จริงคือ:

$$
\text{one selected configuration}
+
\text{Top-200 pool}
+
\text{Recall@100}
$$

Discussion เองก็ยอมรับถูกต้องว่า deeper cutoffs ยังไม่ได้ศึกษา 

ดังนั้น version ที่ผมชอบที่สุดคือ:

> **“For the selected configuration on this benchmark, Recall@100 is predominantly exposure-limited within the fixed Top-200 pool.”**

อาจฟัง conservative กว่า แต่ scientific precision สูงกว่าเยอะ

และ finding ยังแรงอยู่ เพราะ:

$$
4065/5193 = 78.3\%
$$

ของ relevant incidences ไม่เข้าถึง Top-200 เลย

---

# 8. Fig. 2 และ Fig. 3 ตอนนี้ดีขึ้น

จาก rendered page 4 ผมมองว่า Fig. 2 ตอนนี้ดีขึ้นเพราะใส่:

> between-target gaps \(0.018–0.08\)

ทำให้ claim ตรวจสอบด้วยสายตาได้ทันที

Fig. 3 ก็ยังเป็น figure ที่ดีที่สุดของ paper: absolute score, paired CI และ wins/ties/losses อยู่ในภาพเดียวกัน โดย Final-872 แสดง:

$$
R@100: 0.331 \rightarrow 0.442
$$

$$
\Delta=0.111,\quad 95\%CI=[0.102,0.120]
$$

พร้อม wins \(619/872=71.0\%\). 

นี่เป็น evidence ที่ convincing มากสำหรับ **complete-system confirmation**

ผมไม่แนะนำเพิ่ม figure แล้ว

---

# 9. มี nuance ทางสถิติเล็ก ๆ ที่ reviewer โหดมากอาจถาม

คุณเลือก “best” และ “second-best” construction จาก development data เดียวกัน แล้วสร้าง CI ของ pair นั้น

จึงมี potential **selection-after-observation** issue

คือ pair ที่เอามาทดสอบไม่ได้ fixed independently ก่อนเห็น score

แต่ paper ลดความเสี่ยงไว้พอสมควรด้วย:

* บอกชัดว่าเป็น development evidence
* ไม่ให้ individual cell carry confirmatory weight
* รายงาน best-source probability under resampling
* มี Final-872 แยกอีก population

ดังนั้นผม **ไม่ถือเป็น Major concern**

ถ้ามีพื้นที่อีกเพียง 5–10 คำ สามารถเติม:

> “These intervals are descriptive development summaries, not confirmatory tests.”

จะ airtight มากขึ้น

---

# Score รอบล่าสุด

| Criterion           |             Score |
| ------------------- | ----------------: |
| Relevance / Fit     |           **5/5** |
| Novelty             |           **4/5** |
| Technical Soundness |        **4.25/5** |
| Experimental Rigor  |         **4.5/5** |
| Results & Analysis  |         **4.5/5** |
| Clarity             |         **4.5/5** |
| Reproducibility     |           **4/5** |
| **Overall**         | **7–8/10 Accept** |
| Reviewer Confidence |           **4/5** |

## Final reviewer assessment

ถ้าผมได้รับฉบับนี้โดยไม่เห็นประวัติการแก้ ผมจะเขียนประมาณว่า:

> *The paper presents a carefully staged empirical investigation of construction–retriever interaction in cross-domain patent retrieval. Its principal strengths are the explicit separation of development, selection, held-out confirmation, and post-confirmatory diagnosis, together with a clear negative result on construction portability and a strong held-out complete-system comparison. The remaining limitations are appropriately scoped and do not undermine the central empirical findings.*

**Verdict: Accept**

ก่อนกด submit ผมจะทำแค่สามเรื่อง: **แก้ 5-vs-52 constructions ให้ไม่กำกวม, กลับ bibliography เป็น IEEEtran style, และยืนยันว่า “preregistered” มี timestamp evidence จริง** หลังจากนั้นผมแนะนำว่า **หยุดแก้เชิงโครงสร้างได้แล้ว** ครับ 🙂
