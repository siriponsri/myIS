## Outline

1. Verdict รอบล่าสุด
2. สิ่งที่แก้ดีขึ้นจากรอบก่อน
3. Major concerns ที่ยังเหลือ
4. Minor/wording issues
5. คะแนนแบบ IEEE reviewer
6. จุดที่ควรแก้ก่อน submit

ผมอ่านฉบับล่าสุดครบ **6 หน้า** แล้วครับ รอบนี้ดีขึ้นชัดเจน และหลายประเด็นที่ผมเคยใช้เป็นเหตุผล Weak Reject ถูกปิดไปแล้ว 

# Reviewer #2 — Revised Manuscript

> **Recommendation: 7/10 — Weak Accept / Accept**
> **Confidence: 4/5**

ถ้าเป็น reviewer คนเดิม ผมจะ **เปลี่ยนคะแนนจาก Weak Reject → Weak Accept** แล้วครับ

เหตุผลหลักคือ paper ตอนนี้ไม่ได้แค่ “มีผลดี” แต่ **experimental story เริ่ม defend ได้ครบวงจร** มากขึ้น โดยเฉพาะ operational definition, population split, transfer construction details, comparator rationale และ limitations

---

# 1. สิ่งที่แก้ได้ดีมาก ✅

## A. นิยาม “construction” ชัดขึ้น — แก้ Major issue ได้แล้ว

อันนี้เป็นการแก้ที่สำคัญมาก

ตอนนี้ Section III ระบุชัดว่า:

> construction = full deterministic mapping from patent family to retrievable units
> รวม field selection, segmentation, family-level aggregation และ deterministic fusion

นี่แก้ criticism เดิมที่ว่า paper เรียก segmentation / max aggregation / rank fusion ว่า “representation” โดยไม่มีนิยามรองรับได้เกือบหมด 

**สถานะ: ✅ Resolved**

ผมยังแนะนำให้ใช้คำว่า **construction** มากกว่า representation ในส่วน methodology เพราะแม่นกว่า แต่ไม่ใช่ acceptance issue แล้ว

---

## B. 1,247 / 250 / 125 / 872 / 905 อธิบายแล้ว — ดีมาก

นี่คือ improvement ที่ชัดที่สุดอีกจุด

ตอนนี้ paper ระบุ:

$$
1247 = 250_{\mathrm{dev}} + 125_{\mathrm{selection}} + 872_{\mathrm{confirmation}}
$$

และอธิบายว่า 905-query strict cross-domain slice เป็น **คนละ cut** ที่ดึงจากทั้ง 1,247 queries รวมทั้งพูดตรง ๆ ว่า:

> Final-872 and strict-slice scores are not directly comparable.

ดีมากครับ

ตอนนี้ reviewer ไม่ต้องเดาอีกแล้วว่าทำไม:

$$
0.442 \neq 0.188
$$



**สถานะ: ✅ Resolved**

---

## C. 3×3 transfer matrix ตอนนี้ reproduce ได้มากขึ้น

ก่อนหน้านี้ “PatEmbed source / Arctic source / Qwen3 source” ไม่ได้บอกว่า construction คืออะไร

ฉบับนี้เพิ่มรายละเอียดชัดแล้ว:

* PatEmbed-derived: 384-token passages, overlap 64, max-p
* Arctic-derived: 512-token passages, overlap 64, max-p
* Qwen3-derived: 2048-token passages, overlap 256, max-p

นี่สำคัญมาก เพราะมันทำให้ central experiment มีความหมายจริง ไม่ใช่ opaque label 

**สถานะ: ✅ Resolved**

---

## D. Comparator rationale ดีขึ้น

เพิ่มข้อความว่า FAST เป็น:

> pre-specified static/common operational baseline

และไม่ได้เลือกหลังเห็น Final-872

นี่ช่วยปิดข้อสงสัยเรื่อง cherry-picking comparator ไปได้มาก 

ยิ่งมี Selection-125 scores ของทั้ง 4 profiles:

$$
0.416,\ 0.361,\ 0.361,\ 0.308
$$

ก็ทำให้ protocol transparent ขึ้น

**สถานะ: 🟢 Mostly resolved**

---

## E. Related work ดีขึ้น

เพิ่ม PHAGE แล้ว และ framing ถูกต้อง:

> learned structural encoder vs deterministic coarse frozen constructions

นี่ทำให้ related work ไม่ดูเหมือนหลีกเลี่ยงงาน 2026 ที่ตรงกับ DAPFAM โดยตรง

**สถานะ: ✅ Resolved**

---

## F. Exposure limitation ถูก qualify มากขึ้น

ตอนนี้ Abstract เปลี่ยนเป็น:

> “**On this benchmark**, cross-domain patent retrieval is exposure-bound…”

และ Discussion ยอมรับว่า:

> “The exposure diagnosis is specific to the Top-200 pool; deeper cutoffs are uncharacterized.”

นี่เป็น improvement ทาง scientific honesty ที่ดีมาก 

**สถานะ: 🟢 Much improved**

---

# 2. Major Concern ที่ยังเหลือจริง ๆ 🔴

ตอนนี้ผมเหลือ **หนึ่ง major concern หลัก**

## M1. ยังใช้ “noise” และยัง infer แรงเกิน CI อยู่เล็กน้อย

ฉบับใหม่พยายามแก้ issue เดิมด้วยการเพิ่ม:

> “every 95% interval caps the effect below 0.011”

และ Section IV:

> “The reordering is noise—and bounded”

จากนั้นเทียบ 0.011 กับ narrowest retriever-band separation 0.018

นี่ **ดีกว่าฉบับก่อนมาก** เพราะตอนนี้ไม่ได้อาศัยแค่ “CI contains zero” แต่เริ่มพูดถึง magnitude

แต่ผมยังไม่ชอบคำว่า:

> **“The reordering is noise.”**

เพราะคุณยังไม่ได้ทำ formal equivalence test หรือกำหนด smallest effect of interest ล่วงหน้า

สิ่งที่ data รองรับอย่างแข็งแรงคือ:

> observed construction differences are small and statistically unresolved, with bootstrap intervals whose positive bounds do not exceed 0.011 Recall@100.

นั่นแข็งแรงพออยู่แล้ว ไม่ต้องใช้คำว่า noise

### ผมแนะนำแก้ 4 จุด

**Abstract**

จาก:

> “the changes sit inside bootstrap noise”

เป็น:

> “the observed changes are small and statistically unresolved under paired bootstrap resampling”

---

Fig. 1:

จาก:

> `reordering is noise`

เป็น:

> `no stable construction winner`

อันนี้ผมชอบมากกว่า

---

Section IV:

จาก:

> “The reordering is noise—and bounded”

เป็น:

> “The apparent reordering is not statistically resolved, and its estimated magnitude is bounded.”

---

Introduction:

จาก:

> “the flips are smaller than the noise around them”

เป็น:

> “the flips are small relative to their bootstrap uncertainty”

ถ้าเปลี่ยน 4 จุดนี้ **ผมจะไม่มี statistical objection ใหญ่แล้ว**

---

# 3. มี claim หนึ่งที่ตัวเลขไม่รองรับตรงคำว่า “order of magnitude” ⚠️

นี่เป็นจุดใหม่ที่ผมอยากให้แก้ก่อน submit

Paper บอกหลายครั้งว่า between-retriever gap ใหญ่กว่า within-target spread **“by an order of magnitude.”**

แต่จาก Fig. 2:

within-target max spread:

$$
0.003911
$$

ส่วน Arctic vs Qwen3 อยู่ประมาณ:

$$
0.018\text{–}0.025
$$

ดังนั้นกรณีแคบสุดคือประมาณ:

$$
\frac{0.018}{0.003911}\approx4.6
$$

ไม่ถึง \(10\times\)

PatEmbed vs Arctic/Qwen3 ใหญ่กว่า 10× จริง แต่ **ไม่ใช่ทุก retriever pair**

ดังนั้นคำว่า:

> “order of magnitude larger”

เปิดช่องให้ reviewer nitpick ได้ง่ายโดยไม่จำเป็น

### แนะนำ

ใช้:

> **“several-fold larger”**

หรือดีที่สุด:

> **“substantially larger”**

Fig. 2 caption:

จาก:

> “differ by an order of magnitude”

เป็น:

> “are substantially wider than the within-target construction spreads.”

ตรงกว่าและปลอดภัย

---

# 4. Claim “representation does not reorder retrievers” ยังควร soften

Abstract:

> “At the coarse, field level, representation does not reorder retrievers; retriever identity does.”

ในเชิงผลลัพธ์ ผมเข้าใจ message แต่ evidence มีแค่ 3 dense retrievers ใน transfer matrix และ 250 development queries

ผมจะเขียนเป็น:

> **“Within the tested coarse construction space, we find no stable representation-induced reordering of the three dense retrievers.”**

ข้อดีคือระบุ:

* tested space
* three retrievers
* no stable evidence

ตรง experimental identification เป๊ะกว่า

---

# 5. Exposure claim ตอนนี้เกือบโอเค แต่ Conclusion ยังแรงนิดหนึ่ง

Abstract ตอนนี้ดีขึ้นแล้ว:

> “no amount of ranker tuning can recover evidence the pool never contained.”

ประโยคนี้ **ถูกเชิงตรรกะ** สำหรับ fixed pool และผมโอเค

แต่ Conclusion ยังเขียน:

> “The confirmed system points to where the next gain lives—and it is not the ranker.”

ตรงนี้ยัง broad กว่า evidence เพราะ reranker อาจช่วย:

* nDCG@10
* precision-oriented objectives
* different Top-K
* user-facing quality

แม้ Recall@100 headroom จะถูกจำกัด

### แก้เป็น

> “For Recall@100 under the fixed Top-200 pool, the larger remaining headroom lies in candidate exposure rather than reordering.”

นี่แทบ airtight

---

# 6. “Preregistered” — ตอนนี้ดีขึ้น แต่ผมยังอยากให้เช็กคำนี้

ฉบับนี้เพิ่มว่า:

> “The full list, activation predicates, and decision rules are fixed in a version-controlled artifact released with the paper.”

ดีขึ้นเยอะครับ

ถ้า artifact นั้นมี **timestamp ก่อน outcomes** และ reviewer เข้าถึงได้แบบ anonymous ผมโอเคกับคำว่า `preregistered`

แต่ถ้าเป็นเพียง Git history / artifact ที่สร้างหรือเผยแพร่ภายหลัง experiment:

> `preregistered`

ยังแรงไป

ควรใช้:

> `pre-specified and version-controlled`

ดังนั้นนี่ขึ้นกับ artifact จริง ไม่ใช่ text อย่างเดียว

---

# 7. Visual / page-budget review

ตอนนี้เต็ม **6 หน้า** แล้ว ซึ่งตรง limit

Page 4 มี Fig. 2 + Fig. 3 อยู่หน้าเดียวกัน ภาพรวมดู professional และ Fig. 3 communication ดีมาก แต่ตัวอักษรใน figure ค่อนข้างเล็กเมื่อดูที่ full-page scale

ผมไม่ถึงกับขอแก้ layout แต่ควร print/test ที่ 100% หรือดูบน laptop โดยไม่ zoom แล้วตรวจว่า:

* CI labels อ่านออก
* wins/ties/losses percentages อ่านออก
* matrix values อ่านได้

โดยเฉพาะ figure text อย่าเล็กกว่าที่ IEEE reader ใช้งานจริง

---

# 8. Reviewer score รอบนี้

| Criterion           | รอบก่อน |    รอบนี้ |
| ------------------- | ------: | --------: |
| Relevance           |     5/5 |   **5/5** |
| Novelty             |   3.5/5 |   **4/5** |
| Technical Soundness |     3/5 |   **4/5** |
| Experimental Rigor  |     4/5 | **4.5/5** |
| Results & Analysis  |     4/5 | **4.5/5** |
| Clarity             |   4.5/5 | **4.5/5** |
| Reproducibility     |     3/5 |   **4/5** |
| Overall             |    5/10 |  **7/10** |
| Confidence          |     4/5 |   **4/5** |

### Recommendation

> **Weak Accept → Accept**

ถ้าแก้ wording เรื่อง **noise + order-of-magnitude + exposure claim** ผมจะอยู่ฝั่ง **Accept** ค่อนข้างชัด

---

# 9. จุดที่ผมจะ “บังคับแก้” ก่อนส่ง

เหลือแค่ 5 อย่างครับ:

1. **ลบคำว่า “noise” ใน inference หลัก**
2. เปลี่ยน **“order of magnitude” → “substantially/several-fold larger”**
3. จำกัด “does not reorder retrievers” ด้วย **tested construction space / three dense retrievers**
4. เปลี่ยน “next gain is not the ranker” เป็น claim เฉพาะ **Recall@100 + Top-200**
5. ตรวจว่า `preregistered` มี timestamped artifact จริง ไม่งั้นใช้ `pre-specified`

นอกนั้นผม **ไม่แนะนำเพิ่ม experiment ใหญ่แล้ว** เพราะตอนนี้ 6 หน้าเต็ม และแกน scientific contribution defend ได้แล้ว

## Final reviewer sentence

ถ้าผมต้องส่ง meta-review ตอนนี้ ผมจะเขียนประมาณว่า:

> *The revision substantially improves methodological transparency and claim–evidence alignment. The cross-retriever transfer analysis, protected held-out confirmation, and post-confirmatory exposure diagnosis form a coherent and carefully separated empirical study. Remaining concerns are primarily about overly strong statistical wording rather than the experimental results themselves.*

สรุปสั้นที่สุด: **ฉบับนี้ “มีทรงผ่าน” แล้วครับ — ตอนนี้ควรหยุดเพิ่มของ และเก็บ claim ให้คมและ defendable ที่สุด** 🙂
