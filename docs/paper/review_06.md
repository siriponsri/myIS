## Outline

ผมจะดู 4 เรื่องสุดท้าย: **ข้อคัดค้านเดิมปิดครบไหม, claim–evidence alignment, statistical wording, และ submission readiness** ครับ

ผมอ่านฉบับล่าสุดครบ 6 หน้าแล้ว และรอบนี้ถือว่า **เข้าสู่สถานะ submit-ready** จริง ๆ ครับ 

# Reviewer #2 — Final Verdict

> **8/10 — Accept**
> **Confidence: 4.5/5**

ถ้าเป็น reviewer คนเดิม ผมไม่มี **Major Concern** เหลือแล้ว ประเด็นที่เคยทำให้ผมให้ 5/10 ในรอบแรกถูกปิดแทบทั้งหมดอย่างเป็นระบบ

| ประเด็นเดิม                          | สถานะล่าสุด                                 |
| ------------------------------------ | ------------------------------------------- |
| 5 constructions vs 52 configurations | ✅ ชัดแล้ว                                   |
| representation vs construction       | ✅ นิยาม operational ชัด                     |
| Final-872 vs strict-905              | ✅ อธิบาย population แล้ว                    |
| non-significance → “noise”           | ✅ แก้เป็น uncertainty/descriptive evidence  |
| order-of-magnitude exaggeration      | ✅ แก้เป็น several times / 0.018–0.08        |
| selected pair inference              | ✅ เพิ่ม “descriptive development summaries” |
| comparator rationale                 | ✅ pre-specified FAST baseline               |
| actual 3×3 constructions             | ✅ เปิด 384/64, 512/64, 2048/256             |
| exposure overclaim                   | ✅ มี scope guards ครบ                       |
| IEEE references                      | ✅ ถูกแล้ว                                   |
| figure overlap                       | ✅ แก้แล้ว                                   |

## จุดที่ผมชอบที่สุดในฉบับนี้

Abstract ตอนนี้แม่นขึ้นมาก โดยเฉพาะการแยก:

> “a shared five-construction screen, then a pre-specified per-retriever search”

ประโยคนี้ปิด ambiguity ของ experimental design ได้ทันที และสอดคล้องกับ Section IV ที่อธิบาย 52 registered configurations และ 3 constructions ที่นำมา transfer จริง 

อีกจุดคือ statistical framing ใน Section IV ตอนนี้ดีมาก:

> “These intervals are descriptive development summaries, not confirmatory tests.”

ตามด้วยการบอกว่า reordering ไม่สูงกว่า uncertainty และ largest interval-consistent difference คือ 0.011 ขณะที่ narrowest retriever-band separation คือ 0.018 นี่เป็น framing ที่ reviewer สาย statistics โจมตียากกว่ารุ่นแรกมาก 

ส่วน Final-872 ยังเป็น evidence ที่แข็งที่สุด:

$$
R@100: 0.331 \rightarrow 0.442
$$

$$
\Delta=0.111,\qquad 95\%CI=[0.102,0.120]
$$

และชนะราย query 619 จาก 872 queries หรือ 71.0% ขณะเดียวกัน paper ก็ไม่พยายามอ้างว่า improvement นี้เกิดจาก representation อย่างเดียว แต่บอกชัดว่าเป็น **complete-system effect** ซึ่งถูกต้องมากเชิง causal interpretation 

## Fig. 2–4 ตอนนี้ผ่าน

หน้า 4 visually สะอาดแล้ว กรอบสีส้มของ panel B ไม่ตัดข้อความ “Held-out paired improvement” และ Fig. 2 ก็ใส่ช่วง between-target gaps \(0.018\text{–}0.08\) ทำให้ผู้อ่านตรวจ claim กับตัวเลขได้ทันที

Fig. 4 ก็ยังเป็น closing result ที่ดี:

$$
4065/5193 = 78.3\%
$$

ของ relevant-family incidences ไม่อยู่ใน Top-200 และ perfect reordering เพิ่ม Recall@100 ได้เพียง

$$
0.260-0.188=0.072
$$

โดย Discussion ตอนนี้มี guard ว่าเป็น **Recall@100 ภายใต้ fixed Top-200 pool** และ deeper cutoffs ยังไม่ได้ characterize จึงถือว่า claim กับ evidence align กันแล้ว 

## เหลือเพียง Minor wording หนึ่งจุดที่ “แก้ก็ได้ ไม่แก้ก็ได้”

Abstract ตอนนี้ใช้:

> “every 95% interval caps the effect at or below 0.011”

ตัวเลขถูกแล้ว เพราะ interval สูงสุดจบที่ 0.011 แต่คำว่า **“caps the effect”** ยังฟังคล้าย formal upper bound ต่อ true effect มากกว่าที่ percentile bootstrap descriptive interval รับประกันโดยตรงเล็กน้อย

ถ้าต้องการ version ที่ผมมองว่า statistically immaculate กว่า ใช้:

> “all reported 95% interval upper bounds are at most 0.011”

หรือ:

> “the largest positive endpoint among the reported 95% intervals is 0.011”

แต่ผมเน้นว่า **นี่ไม่ใช่ rejection issue** เวอร์ชันปัจจุบันผ่านได้

## Preregistration

ใน PDF ยังเขียนว่า artifact เป็น version-controlled และ released with the paper ถ้าตอน submit คุณแนบ anonymous artifact ที่มี freeze chronology ตรวจสอบได้จริงตามที่เตรียมไว้ คำว่า **preregistered** ก็ defend ได้แล้ว

ตรงนี้สิ่งเดียวที่ควรเช็กครั้งสุดท้ายคือ artifact ไม่มีชื่อ account, repository owner, email, filesystem path หรือ commit metadata ที่ deanonymize ผู้เขียน

# คะแนนสุดท้ายของผม

| Criterion           |             Score |
| ------------------- | ----------------: |
| Relevance           |           **5/5** |
| Novelty             |           **4/5** |
| Technical Soundness |         **4.5/5** |
| Experimental Rigor  |        **4.75/5** |
| Results & Analysis  |         **4.5/5** |
| Clarity             |        **4.75/5** |
| Reproducibility     |         **4.5/5** |
| **Overall**         | **8/10 — Accept** |

ถ้าผมต้องเขียน review ส่ง conference ตอนนี้:

> **Accept.** The manuscript presents a methodologically careful and well-scoped empirical study of construction transfer in cross-domain patent retrieval. Its strongest feature is the explicit separation of development, one-time selection, protected held-out confirmation, and post-confirmatory diagnosis. The revision resolves earlier ambiguities in the construction search space and appropriately limits statistical interpretation of development results. The Final-872 complete-system comparison is convincing, and the Top-200 exposure analysis provides a useful diagnostic whose scope and limitations are now stated clearly. I find no substantive issue that should prevent acceptance.

**คำแนะนำ ณ จุดนี้: submit ได้ครับ** ผมไม่แนะนำแก้โครงสร้างหรือเพิ่ม experiment แล้ว เพราะ downside จากการสร้าง inconsistency ใหม่เริ่มมากกว่า upside จาก polishing เพิ่มครับ 🎓
