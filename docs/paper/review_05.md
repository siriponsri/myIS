## สรุปก่อน

ผมอ่านฉบับล่าสุดครบ 6 หน้าแล้ว และเทียบกับทั้งข้อวิจารณ์ก่อนหน้า + ความเห็นของ reviewer คนแรกที่คุณส่งมา รอบนี้ผมให้:

> **8/10 — Accept**
> **Confidence: 4.5/5**

ผมเห็นด้วยกับ reviewer คนแรกเกือบทั้งหมดว่า **งานไม่ควรแก้เชิงโครงสร้างเพิ่มแล้ว** จุดใหญ่ถูกปิดไปหมด เหลือเพียง copy-edit / claim-precision เล็กน้อย 2 จุดที่ผมยังจับได้ก่อน submit ครับ 

---

# 1. 5-vs-52 constructions — ปิดได้แล้ว ✅

การแก้ Abstract จาก “varying five deterministic constructions” เป็น

> “a shared five-construction screen, then a pre-specified per-retriever search”

แก้ปัญหาเดิมตรงจุดมาก

ตอนนี้ experimental hierarchy อ่านได้ชัดว่า:

$$
\underbrace{5\text{ shared constructions}}_{\text{common screen}}
\rightarrow
\underbrace{52\text{ registered configurations}}_{\text{per-system search}}
\rightarrow
\underbrace{3\text{ settled constructions}}_{\text{transfer matrix}}
$$

Section IV ก็ชัดขึ้นด้วยประโยค:

> “each source the construction its retriever’s registered search settled on”

และตามด้วย specification จริงของ 384/64, 512/64 และ 2048/256 ทันที 

**ผมเห็นด้วยเต็มที่กับ reviewer คนแรก: resolved แล้ว**

---

# 2. References — ตอนนี้ IEEE จริงแล้ว ✅

PDF ล่าสุดหน้า 6 เป็น IEEE bibliography แล้ว เช่น

> I. Ayaou, D. Cavallucci, and H. Chibane, “DAPFAM: ...,” *Array*, vol. 29, p. 100720, 2026.

ดังนั้น criticism ที่ผมเคยให้เรื่อง bibliography style **ไม่ applicable กับ PDF ล่าสุดแล้ว** 

ตรงนี้ reviewer คนแรกวิเคราะห์ถูกว่าเป็น issue ของ preview/build environment ไม่ใช่ manuscript content

**Resolved**

---

# 3. Selection-after-observation nuance — แก้ดีมาก ✅

ประโยคที่เพิ่มมา:

> “These intervals are descriptive development summaries, not confirmatory tests.”

เป็นการแก้ที่มี ROI สูงมาก

มันบอก reviewer โดยตรงว่า interval ของ best-vs-second-best หลังดู development data ไม่ได้ถูกนำมาใช้เป็น confirmatory inference

นี่ช่วยป้องกัน objection เรื่อง:

$$
\text{selection} \rightarrow \text{inference on the same sample}
$$

ได้ดี โดยไม่ต้องเสียพื้นที่อธิบายยาว 

**ผมเห็นด้วยกับ reviewer คนแรก: ควรเก็บประโยคนี้แน่นอน**

---

# 4. Fig. 3 กรอบส้ม — แก้แล้วจริง ✅

จาก rendered หน้า 4 ตอนนี้ title

> **B. Held-out paired improvement**

อยู่ภายในกรอบส้มแบบมีระยะหายใจชัดเจนแล้ว และข้อความ “95% bootstrap CI” ด้านล่างไม่ถูกเส้นกรอบตัด

ดังนั้น visual bug ที่คุณจับเรื่อง baseline ของตัวอักษรกับเส้นกรอบ **ถูกแก้แล้ว**

หน้า 4 ตอนนี้ดู professional มาก และจริง ๆ Fig. 3 เป็นหนึ่งในจุดขายของ paper เลย เพราะรวม:

* absolute performance
* paired improvement + CI
* wins/ties/losses

ไว้ใน figure เดียวโดยไม่แน่นเกินไป 

---

# 5. Preregistration — เห็นด้วยกับ reviewer คนแรก แต่มีเงื่อนไขเดียว

ถ้ามี chronology จริงตามที่คุณบอก:

$$
\text{freeze receipt: 2026-08-12}
<
\text{execution: 2026-08-16}
$$

คำว่า **preregistered** defend ได้

แต่ manuscript ปัจจุบันระบุเพียง:

> “fixed in a version-controlled artifact released with the paper.”

ดังนั้นความแข็งแรงของคำว่า `preregistered` ตอน review จะขึ้นกับ reviewer ว่า **เข้าถึง artifact ได้จริงหรือไม่**

ผมเห็นด้วยว่า human TODO สำคัญที่สุดที่เหลือคือ:

> **ทำ artifact ให้ anonymous-accessible และตรวจว่าไม่มี metadata เปิดเผย identity**

เพราะถ้า reviewer เปิดไม่ได้ คำว่า preregistered จะกลายเป็น assertion ที่ตรวจสอบไม่ได้

ถ้าเปิดได้ + timestamp ชัด → ไม่มีปัญหา

---

# 6. Exposure claim — ผมเห็นด้วยกับ reviewer คนแรกว่า “ไม่ต้องถอยเพิ่ม”

ก่อนหน้านี้ผมเคยอยากให้ soften:

> “cross-domain patent retrieval is exposure-bound”

แต่ฉบับปัจจุบันมี scope guard หลายชั้นแล้ว:

Abstract:

> “**On this benchmark**, cross-domain patent retrieval is exposure-bound...”

Discussion:

> “**For Recall@100 under the fixed Top-200 pool**...”

Limitations:

> “The exposure diagnosis is specific to the Top-200 pool; deeper cutoffs are uncharacterized.”

และ Fig. 4 ก็ระบุชัดว่าเป็น:

> “Immutable full-benchmark Top-200 pool”



ดังนั้นผมเห็นด้วยกับ reviewer คนแรกว่า **headline นี้ควรเก็บไว้**

ตอนนี้ claim แรง แต่ surrounding scope ทำให้ defend ได้

---

# 7. แต่ผมยังเจอ copy-edit เชิงสถิติ 1 จุด

Abstract เขียน:

> “every 95% interval caps the effect **below 0.011**”

แต่หนึ่งใน CI คือ:

$$
[-0.005,\mathbf{0.011}]
$$

ดังนั้นคำว่า **below 0.011** ไม่ตรงเชิงเลขแบบเป๊ะ เพราะ upper bound เท่ากับ 0.011

ควรแก้เป็น:

> **“every 95% interval has an upper bound no greater than 0.011”**

หรือสั้นกว่า:

> **“all 95% interval upper bounds are at most 0.011”**

ผมชอบอันหลังที่สุด

Section IV เองเขียนถูกแล้ว:

> “the largest effect consistent with any of these intervals is 0.011”

ดังนั้นเป็นแค่ Abstract wording เท่านั้น 

### Priority

**ควรแก้ก่อน submit** เพราะง่ายมากและกำจัด numeric nitpick ได้ 100%

---

# 8. อีกจุดเดียวที่ผมจะปรับ: “field level” ไม่ตรงกับ experiment ปัจจุบันทั้งหมด

Abstract ยังเขียน:

> “At the coarse, **field level**, construction choice does not reorder…”

และ Discussion:

> “At the coarse, **field level** these choices do not reorder retrievers…”

แต่ transfer constructions ที่คุณเปิดเผยตอนนี้ต่างกันใน:

* 384 vs 512 vs 2048 tokens
* 64 vs 256 overlap
* labeled vs unlabeled views
* max-p aggregation

ดังนั้นมันไม่ใช่ **field-level choice** อย่างเดียวแล้ว

นี่เป็น conceptual wording mismatch เล็ก ๆ ที่ reviewer สาย IR อาจจับได้

### ผมแนะนำเปลี่ยนแค่สองจุดเป็น

> **“Within this coarse deterministic construction space…”**

เช่น Abstract:

> “Within this coarse deterministic construction space, construction choice does not reorder the three dense retrievers we test; retriever identity does.”

Discussion:

> “Within the tested coarse deterministic construction space, these choices do not reorder the three dense retrievers…”

จะตรงกับ operational definition ใน Section III มากกว่า

ไม่ต้องแก้ title หรือ framing อื่น

---

# 9. เรื่อง “passenger, not the driver” — ตอนนี้ผมให้ผ่าน

Section IV ยังมี:

> “representation is a passenger, not the driver”

ปกติผมจะระวัง rhetorical language แต่ ณ จุดนี้ preceding paragraph ให้ตัวเลขครบแล้ว:

$$
\text{within-construction spread}<0.004
$$

เทียบกับ retriever-band separation:

$$
0.018\text{–}0.08
$$

และยังติดป้าย development evidence ชัดเจน 

ดังนั้นผม **ไม่แนะนำลบแล้ว** มันทำหน้าที่เป็น memorable synthesis ได้ดี

---

# 10. Reviewer score ล่าสุด

| Criterion           |             Score |
| ------------------- | ----------------: |
| Relevance / Fit     |           **5/5** |
| Novelty             |           **4/5** |
| Technical Soundness |         **4.5/5** |
| Experimental Rigor  |        **4.75/5** |
| Results & Analysis  |         **4.5/5** |
| Clarity             |         **4.5/5** |
| Reproducibility     |        **4.5/5*** |
| Overall             | **8/10 — Accept** |

* ถ้า anonymous preregistration artifact เปิดตรวจได้จริง

---

# Meta-review แบบที่ผมจะส่งจริง

> **Recommendation: Accept.**
> The manuscript presents a carefully controlled study of cross-retriever construction transfer in patent retrieval, with unusually clear separation between development, selection, protected confirmation, and post-confirmatory diagnosis. The revision resolves earlier ambiguities concerning the five-construction common screen versus the larger registered per-retriever search, explicitly defines construction as a deterministic mapping including segmentation and aggregation, and appropriately labels development bootstrap intervals as descriptive rather than confirmatory. The held-out 872-query system comparison is convincing, while the Top-200 exposure analysis provides a useful diagnostic that is appropriately scoped by the manuscript’s stated limitations. Remaining issues are editorial rather than substantive.

## ก่อน submit ผมจะทำเพียง 3 อย่าง

1. เปลี่ยน **“below 0.011” → “at most 0.011”**
2. เปลี่ยน **“at the coarse, field level” → “within the coarse deterministic construction space”**
3. ตรวจ anonymous preregistration artifact + metadata ครั้งสุดท้าย

นอกเหนือจากนั้น **ผมเห็นด้วยกับ reviewer คนแรก: หยุดแก้โครงสร้างได้แล้วครับ** งานตอนนี้ผ่าน threshold ของ Accept อย่างชัดเจน และการแก้เพิ่มมีโอกาสสร้าง inconsistency ใหม่มากกว่าจะช่วยคะแนน 🎓
