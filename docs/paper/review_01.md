# 🧑‍⚖️ Brutal Review — iSAI-NLP 2026

## Outline

1. Verdict ก่อน
2. Desk-reject / compliance
3. จุดแข็ง
4. Major weaknesses ที่อาจทำให้ Reject
5. Minor issues
6. Questions to authors
7. Reviewer scores
8. แผนแก้จาก Weak Reject → Accept

ผมอ่าน manuscript **“Beyond the Retriever: Representation Transfer in Cross-Domain Patent Retrieval”** ครบทั้ง 5 หน้าแล้ว โดยพยายามอ่านในฐานะ Reviewer #2 ที่ไม่ได้ช่วยผู้เขียน แต่กำลังหาเหตุผลว่าทำไม paper นี้ *ไม่ควร* ผ่านก่อนครับ 

---

# Reviewer #2

### Overall Recommendation

> **5/10 — Borderline / Weak Reject**

**Reviewer Confidence: 4/5**

แต่มีข่าวดีสำคัญ: ผมไม่ได้มองว่างานนี้ “อ่อน” เลย ตรงกันข้าม งานมี **idea ที่ดีมาก, experimental discipline ดีกว่าค่าเฉลี่ย conference paper และเขียนดี** ปัญหาคือมีประมาณ **3 จุดที่ claim วิ่งนำ evidence** ซึ่ง reviewer สาย IR/statistics สามารถใช้เป็นเหตุผล Reject ได้ง่าย

ถ้าแก้สามจุดใหญ่ด้านล่าง ผมจะขยับเป็นประมาณ:

> **7/10 — Accept**

โดยแทบไม่ต้องทำ experiment ขนาดใหญ่อีกชุด

---

# 1. Desk-Reject Check ✅

ส่วนนี้ผ่านค่อนข้างสวย

PDF มี **5 หน้า** จึงอยู่ภายในข้อกำหนดไม่เกิน 6 หน้า และ manuscript ใช้ `Anonymous Authors` ตาม double-anonymous process. ไม่เห็น acknowledgment หรือ author-identifying project URL ในเนื้อหาที่ให้ตรวจ ข้อกำหนดของงานระบุชัดว่าต้องใช้ IEEE template, ไม่เกิน 6 หน้า และรักษา anonymity มิฉะนั้นอาจ desk reject ได้ 

### Result

| Check                          | Verdict   |
| ------------------------------ | --------- |
| ≤ 6 pages                      | ✅ 5 pages |
| Anonymous author block         | ✅         |
| Obvious identifying URL        | ✅ ไม่พบ   |
| IEEE-like conference structure | ✅         |
| References included            | ✅         |
| Obvious anonymity violation    | ✅ ไม่พบ   |

**Desk rejection risk: Low**

ข้อเดียวที่ผมตรวจจาก parsed PDF ไม่สามารถรับรองได้ 100% คือ exact font/margin/spacing compliance แต่ไม่มี red flag ชัดเจนจากตัว manuscript

---

# 2. Summary of the Paper

Paper ตั้งคำถามที่ดี:

> เมื่อ benchmark เปรียบเทียบ retrievers โดยตรึง document representation ไว้ เราควรมอง representation เป็น neutral preprocessing จริงหรือไม่?

งานใช้ DAPFAM โดย freeze retrievers 5 ตัว และใช้ deterministic document constructions 5 แบบ จากนั้นศึกษาการ transfer ของ construction ที่เลือกด้วย retriever หนึ่งไปยัง retriever อื่นผ่าน 3×3 matrix

ผล development แสดงว่า nominal winner ของ representation เปลี่ยนตาม target retriever แต่ within-target Recall@100 spread ต่ำกว่า ~0.004 ขณะที่ retriever-to-retriever differences ใหญ่กว่ามาก จากนั้นผู้เขียนแยก development → selection → Final-872 confirmation และพบ selected complete configuration เพิ่ม Recall@100 จาก 0.331 เป็น 0.442, \(\Delta=0.111\), bootstrap CI \([0.102,0.120]\). สุดท้ายวิเคราะห์ Top-200 pool และพบว่า relevant-family incidences 78.3% ไม่ปรากฏใน pool เลย 

นี่เป็น storyline ที่ดีมาก

**representation → transfer → confirmation → failure diagnosis**

Reviewer อ่านแล้วเข้าใจว่า paper ต้องการพูดอะไร

---

# 3. Strengths ✅

## S1. Experimental hygiene แข็งแรงมาก

สิ่งที่ดีที่สุดใน paper ไม่ใช่ score แต่คือการแยก:

$$
\text{Development}
\rightarrow
\text{Selection}
\rightarrow
\text{Protected Confirmation}
\rightarrow
\text{Post-confirmatory Diagnosis}
$$

ผู้เขียนพยายามไม่ใช้ Final-872 เป็น tuning set และระบุชัดว่า development findings ไม่ควรได้รับ confirmatory authority จาก held-out result 

Reviewer สาย methodology น่าจะชอบมาก

โดยเฉพาะประโยคที่ยอมรับว่า:

> held-out improvement belongs to the **complete configuration**, not representation alone

นี่เป็น scientific restraint ที่ดี

---

## S2. Paired evaluation ถูกทาง

Final-872 ใช้ paired query-level differences + 10,000 paired bootstrap replicates และรายงาน CI ไม่ใช่แค่ absolute score

Recall@100:

$$
0.331\rightarrow0.442
$$

$$
\Delta R@100 = 0.111,\quad
95\%\,CI=[0.102,0.120]
$$

พร้อม wins/ties/losses:

* wins 619
* ties 158
* losses 95

ดังนั้น held-out difference ไม่ใช่ statistical fluke ง่าย ๆ 

**อันนี้แข็งจริง**

---

## S3. Paper รู้ขอบเขตตัวเอง

Related Work ทำสิ่งที่ดีมากอย่างหนึ่ง คือพูดถึง AutoIndex ซึ่งจริง ๆ แล้วสามารถใช้ “สวน” headline ของ paper นี้ได้

AutoIndex แสดงว่า richer learned representation programs สามารถให้ substantial retrieval gains แม้ retriever ถูก freeze และ dense probe ของ Qwen3 เพิ่ม Recall@100 จาก 0.739 เป็น 0.874. ([auto-index.github.io][1])

Paper ไม่หลบ conflict นี้ แต่บอกว่าของตัวเองศึกษาเฉพาะ:

> **coarse, field-level static constructions**

นี่ถูกต้องและช่วยรักษา contribution

---

## S4. Writing / figures ดี

Fig. 1 → experiment protocol
Fig. 2 → transfer result
Fig. 3 → held-out confirmation
Fig. 4 → exposure diagnosis

เป็น narrative sequence ที่ reviewer อ่านเร็วแล้วเข้าใจได้

โดยเฉพาะ Fig. 3 และ Fig. 4 สื่อ message ดีมาก

---

# 4. Major Weaknesses 🚨

นี่คือส่วนที่จะตัดสิน Accept/Reject

---

## 🔴 M1. “CI includes zero” ไม่ได้พิสูจน์ว่า representations equivalent

นี่คือ **ปัญหาใหญ่ที่สุด**

Paper เขียนประมาณว่า:

> paired CI includes zero → “The reordering is noise.”

จากนั้นขยายเป็น:

> “At the coarse, field level, representation is a passenger, not the driver.”

ข้อมูลที่ paper รายงานคือ best-vs-second-best CI:

$$
[-0.005,0.006]
$$

$$
[-0.005,0.011]
$$

$$
[-0.006,0.009]
$$

และ best-source probability ≤ 0.68 

แต่ทางสถิติ:

$$
p > .05
\not\Rightarrow
H_0\text{ is true}
$$

หรือในภาษาง่าย ๆ:

> **failure to detect a difference ≠ evidence that the difference is negligible**

### Reviewer attack

ผมจะเขียนใน review จริงว่า:

> *The manuscript interprets non-significant paired bootstrap contrasts as evidence that representation-induced reordering is noise. However, intervals containing zero only establish insufficient evidence of a directional difference; they do not establish practical equivalence.*

นี่สามารถเป็น **reject reason ที่ legitimate**

### วิธีแก้

ไม่จำเป็นต้อง run model ใหม่

ใช้ query-level outputs เดิมแล้วทำ **equivalence analysis**

กำหนด smallest effect size of interest เช่น:

$$
\delta = 0.01\ R@100
$$

แล้วถามว่า CI ทั้งหมดอยู่ใน

$$
[-\delta,+\delta]
$$

หรือทำ TOST:

$$
H_{01}: \Delta\le-\delta
$$

$$
H_{02}: \Delta\ge+\delta
$$

ถ้าปฏิเสธทั้งคู่ได้ → คุณมี evidence ว่า effect เล็กกว่า practically meaningful threshold

### ถ้าทำ equivalence test ไม่ทัน

ลด claim

อย่าเขียน:

> “The reordering is noise.”

เปลี่ยนเป็นประมาณ:

> “We find no statistically resolved representation winner, and observed within-target differences are small relative to between-retriever differences.”

ปลอดภัยกว่ามาก

---

# 🔴 M2. Independent variable ไม่ใช่ “representation” อย่างเดียว

นี่เป็น conceptual problem ที่ reviewer IR มีโอกาสจับ

Paper เรียก 5 สิ่งว่า representations/constructions แต่รายการประกอบด้วย:

* title + abstract + claims document
* title + abstract
* first independent claim
* **384-token passages + overlap + max aggregation**
* **multiple views + rank fusion**



ปัญหาคือสองรายการหลังไม่ใช่เพียง “what text is represented”

มันเปลี่ยนทั้ง:

$$
\text{segmentation}
+
\text{retrieval unit}
+
\text{aggregation}
+
\text{fusion}
$$

ดังนั้น manipulation จริงใกล้เคียง:

> **retrieval construction / indexing configuration**

มากกว่า pure representation

### Reviewer attack

> *The paper frames its independent variable as representation, yet several tested constructions modify retrieval granularity, family aggregation, and rank fusion. Consequently, the experiment does not isolate representation from ranking architecture.*

ตรงนี้กระทบ title และ central claim โดยตรง

### วิธีแก้

มีสองทาง

**ทาง A — ถูกและง่ายที่สุด**

นิยาม operational definition ตั้งแต่ Introduction:

> “We use representation construction to denote the full deterministic mapping from a patent family to retrievable units, including field selection, segmentation, and deterministic family-level aggregation.”

แล้วเลิกใช้ภาษา causal ว่า “representation alone”

**ทาง B — scientific clean กว่าแต่ต้อง experiment เพิ่ม**

สร้าง factorial comparison:

$$
\text{field choice}
\times
\text{segmentation}
\times
\text{retriever}
$$

โดย fix aggregation

แต่ผม **ไม่แนะนำก่อน deadline**

ทาง A เพียงพอสำหรับ iSAI-NLP ถ้าเขียนตรง ๆ

---

# 🔴 M3. Held-out result แข็งแรง แต่ comparator ไม่ convincing

Selected configuration:

**PatEmbed-large + passage retrieval + max-p**

Comparator:

**BM25 + Arctic Embed + RRF + document representation**



ทั้งสองต่างกันแทบทุก component:

$$
\text{encoder}
+
\text{representation}
+
\text{segmentation}
+
\text{aggregation}
+
\text{fusion}
+
\text{prompt}
$$

Paper ยอมรับเรื่องนี้อย่างถูกต้องและไม่ claim causal effect

แต่คำถาม reviewer ถัดมาคือ:

> **แล้วทำไมผมต้องสนใจว่าระบบ A ชนะระบบ B?**

เพราะ PatEmbed เป็น patent-specific model ที่มีผล DAPFAM ที่แข็งแรงอยู่แล้ว PatenTEB รายงาน PatEmbed-large บน DAPFAM ประมาณ 0.377 NDCG@100 overall. ([arXiv][2])

DAPFAM original paper เองก็ทดสอบถึง 249 configurations และพบ passage-level retrieval เหนือ document-level อย่างสม่ำเสมอ ([ScienceDirect][3])

ดังนั้น:

> PatEmbed + passages ชนะ Arctic/BM25 document configuration

อาจไม่ surprise เท่าไร

### ปัญหาที่ลึกกว่า

Contribution #2 ปัจจุบันคือ:

> preregistered held-out confirmation of a complete configuration

แต่ **held-out confirmation เป็น methodological virtue ไม่ใช่ scientific novelty โดยตัวมันเอง**

### สิ่งที่ควรเพิ่ม

ใช้ page 6 ที่ยังเหลือ

เพิ่ม table ขนาดเล็ก:

| Configuration                      | Standard DAPFAM OUT R@100 | OUT nDCG@100 |
| ---------------------------------- | ------------------------: | -----------: |
| BM25 published baseline            |                       ... |          ... |
| Arctic published baseline          |                       ... |          ... |
| PatEmbed published/config baseline |                       ... |          ... |
| Frozen comparator                  |                       ... |          ... |
| **Selected system**                |                   **...** |      **...** |

โดย evaluation ชุดนี้เป็น **post-confirmatory characterization**, ไม่ใช้ selection

ทันที paper จะตอบได้ว่า:

> “ระบบที่ confirm แล้วอยู่ตรงไหนเทียบกับ published DAPFAM landscape?”

ตอนนี้ตอบไม่ได้ชัด

---

# 🔴 M4. Final-872 กับ Full-benchmark 905-query strict OUT population ชวนสับสนมาก

นี่คือ issue ที่ผมส่ง update ไปก่อนหน้า

Final:

$$
R@100=0.442
$$

แต่ full-benchmark strict cross-domain:

$$
R@100=0.188
$$

ผู้อ่านเห็นเลขสองตัวนี้ใน paper เดียวกันและต้องหยุดว่า:

> **ทำไม model เดิมตกจาก .442 เหลือ .188?**

Paper บอกว่า population ต่างกัน ซึ่งถูกต้อง แต่ยังไม่พอ 

Table I มี:

* Final confirmation: 872
* full benchmark: 1,247
* strict cross-domain diagnostic: 905 judged queries

แต่ relationship ของสามชุดไม่ intuitive

### ต้องเพิ่ม bridge

อย่างน้อยเขียน equation:

$$
1247 = 250_{\text{dev}} +125_{\text{selection}}+872_{\text{final}}
$$

แล้วอธิบายว่า strict OUT evaluation excludes queries with no qualifying cross-domain relevant families และสุดท้ายได้ 905 queries

จากนั้นเพิ่มหนึ่งบรรทัด:

> “The 0.442 Final-872 score and 0.188 strict-OUT full-benchmark score are therefore not directly comparable.”

ตอนนี้แม้ caption จะเตือนแล้ว แต่ reviewer ยังต้อง reconstruct protocol เอง

---

# 🔴 M5. “Exposure-bound, not ordering-bound” กว้างเกินหลักฐาน

Fig. 4 เป็น finding ที่น่าสนใจ:

จาก 5,193 relevant incidences:

$$
796\;@1\text{-}100
$$

$$
332\;@101\text{-}200
$$

$$
4065\;\text{absent}
$$

ดังนั้น:

$$
78.3\%
$$

ไม่อยู่ใน Top-200 

และ perfect reorder ของ fixed Top-200 pool ให้:

$$
R@100_{\max}=R@200=0.260
$$

จาก observed:

$$
0.188
$$

headroom:

$$
0.072
$$

คณิตศาสตร์นี้สมเหตุสมผล

แต่ conclusion:

> **“Cross-domain patent retrieval is exposure-bound, not ordering-bound.”**

กว้างเกินไป

experiment แสดงได้จริงแค่:

> **selected system + this benchmark + Top-200 cutoff**

ไม่ใช่ cross-domain patent retrieval โดยทั่วไป

ที่ depth 500 หรือ 1000 exposure อาจต่างไปอย่างมาก

และ reranking อาจยังได้ gains ใน **nDCG@10** แม้ Recall@100 headroom จำกัด

ยิ่งประโยคใน Abstract:

> “effort spent tuning the ranker is wasted”

ผมจะวงแดงเลย

มันแรงเกิน evidence

### Better claim

ประมาณ:

> “For the selected first-stage configuration at depth 200, remaining Recall@100 error is predominantly exposure-limited.”

อันนี้ reviewer โต้ยากมาก

---

# 5. Missing Related Work ที่ควรแก้ก่อน submit

มีงาน May 2026 ที่เกี่ยวกับ DAPFAM โดยตรงคือ **PHAGE: Patent Heterogeneous Attention-Guided Graph Encoder for Representation Learning** ซึ่ง evaluate บน DAPFAM และเสนอ claim-level structural representations. ([arXiv][4])

ผมคิดว่า **ควร cite**

ไม่จำเป็นต้อง benchmark เพราะ scientific question ต่างกัน และ PHAGE เป็น learned encoder ไม่ใช่ frozen retriever/representation transfer

แต่ omission ค่อนข้าง conspicuous เพราะ:

* paper เป็นปี 2026
* ใช้ DAPFAM
* สนใจ patent representation
* ออกก่อน submission หลายเดือน

ควรเพิ่ม 1–2 ประโยคใน Related Work แยก:

> learned structural representation vs. coarse deterministic construction

นอกจากนี้ AutoIndex ถูก cite แล้วและ framing ค่อนข้างดี ซึ่งควรเก็บไว้ ([auto-index.github.io][1])

---

# 6. “Preregistered” ยังพิสูจน์ไม่ได้จาก manuscript

คำนี้ปรากฏหลายครั้ง:

> “preregistered complete configuration”

> “A per-system search then registers 52 configurations in advance.”

แต่ paper ไม่บอกชัดว่า:

* registered ที่ไหน
* timestamp เมื่อไร
* decision rule ที่ preregister คืออะไร
* 52 configurations คืออะไร
* conditional activation predicates คืออะไร

โดยเฉพาะข้อความ:

> “eight conditional reserves whose activation predicates never fired”

อ่านแล้ว reviewer มีคำถามมากกว่าความมั่นใจ 

### ผมแนะนำ

ถ้ามี timestamped external registration จริง → ให้รายละเอียดที่ anonymous-safe

ถ้าไม่มี formal preregistration → **อย่าใช้คำว่า preregistered**

ใช้:

> **pre-specified before observing the corresponding evaluation outcomes**

ซึ่งยังเป็น methodological strength อยู่ และไม่เปิดช่องให้ reviewer accuse ว่า misuse terminology

---

# 7. Full 3×3 Matrix ยัง opaque

Fig. 2 ใช้ row labels:

* PatEmbed source
* Arctic source
* Qwen3 source

แต่ reviewer อยากรู้ว่า:

> **actual transferred representation คืออะไร?**

คำว่า “PatEmbed-derived text” ไม่ใช่ representation specification

ผมต้องการเห็น:

| Source   | Selected construction |
| -------- | --------------------- |
| PatEmbed | ?                     |
| Arctic   | ?                     |
| Qwen3    | ?                     |

เพราะ central contribution คือ **representation transfer**

แต่ representation ที่ transfer กลับไม่ถูกชื่อใน figure หลัก

นี่แก้ง่ายมากและมี impact สูง

---

# 8. Variance decomposition จะทำ paper แข็งขึ้นมาก

Paper บอกว่า:

> retriever identity dominates construction choice

เพราะ within-target spread < .004 และ between-target difference ~.08

intuition ดี

แต่ถ้าต้องการให้ rigorous มากขึ้น สามารถใช้ query-level repeated measurements แล้ว estimate:

$$
Y_{q,r,c}
=
\mu+\alpha_r+\beta_c+(\alpha\beta)_{rc}+u_q+\epsilon
$$

โดย:

* \(r\) = retriever
* \(c\) = construction
* \(q\) = query

แล้วรายงาน variance/effect magnitude ของ:

$$
\text{Retriever}
$$

เทียบกับ

$$
\text{Construction}
$$

และ interaction

ไม่จำเป็นสำหรับ Accept แต่ถ้าทำได้ จะเปลี่ยน central claim จาก “ดูจากตัวเลขแล้ว retriever ใหญ่กว่า” เป็น quantitative evidence

---

# 9. Minor Weaknesses

### W1. Tone บางช่วง rhetoric เกิน IEEE

ตัวอย่าง:

> “representation is a passenger, not the driver”

> “What makes these claims worth trusting is discipline”

> “It does.”

> “effort spent tuning the ranker is wasted”

อ่านสนุก แต่ reviewer engineering conference บางคนอาจรู้สึก persuasive มากเกิน scientific

ผมไม่ต้องการให้ paper จืด แค่ลดลงประมาณ 20%

---

### W2. 52 configurations แต่ไม่มี visibility

การบอกว่า experiment preregister 52 แต่ execute 44 โดยไม่แสดง configuration list ทำให้ reproducibility ต่ำกว่าที่ paper claim

คุณมี **page 6 ว่างอยู่**

ใช้มัน

---

### W3. Exposure analysis ควรมี depth curve ถ้าทำได้

แทนเพียง:

$$
@100,\ @200
$$

ถ้ามี ranking deeper อยู่แล้ว ผมอยากเห็น:

$$
R@100,\ R@200,\ R@500,\ R@1000
$$

หรือ candidate exposure:

$$
E(k)=
\frac{\#\text{relevant incidences exposed by }k}
{\#\text{relevant incidences}}
$$

เพราะจะตอบว่า exposure bottleneck persists แค่ไหนเมื่อเพิ่ม candidate depth

**ถ้าต้อง rerun ใหญ่และไม่ทัน ไม่ต้องทำ**

เพียงลด generality ของ claim ก็ได้

---

# 10. Questions to Authors

ถ้าผมเป็น reviewer จริง ผมจะถาม 7 ข้อนี้:

1. **What exactly constitutes each “source-derived representation” in the 3×3 transfer matrix?** Please provide the deterministic specification of all three transferred constructions.

2. **Why is an interval containing zero interpreted as evidence that reordering is noise?** Did the authors predefine a practical equivalence margin?

3. **Why was the FAST system chosen as the frozen comparator?** How does it compare to the strongest published DAPFAM configurations?

4. **How exactly are the Final-872 and 905-query strict cross-domain populations related?** Why do their reported Recall@100 values differ so substantially?

5. **Was the study formally preregistered in a timestamped artifact?** If not, would “pre-specified” be more accurate?

6. **To what extent does the exposure-bound conclusion depend on the Top-200 cutoff?** Does the finding persist at deeper retrieval depths?

7. Since some “representations” modify segmentation, aggregation, and fusion, **what is the precise operational definition of representation used in this paper?**

ถ้าคุณตอบ 7 ข้อนี้ใน paper ได้ reviewer จะยิงยากขึ้นเยอะ

---

# 11. Reviewer Scorecard

| Criterion               |     Score | Comment                                                                                |
| ----------------------- | --------: | -------------------------------------------------------------------------------------- |
| **Relevance**           |   **5/5** | เข้ากับ AI/NLP/IR ชัด                                                                  |
| **Novelty**             | **3.5/5** | cross-retriever transfer question น่าสนใจ แต่ exposure diagnosis เป็น standard IR idea |
| **Technical Soundness** |   **3/5** | หลักดี แต่ equivalence inference เป็น concern                                          |
| **Experimental Rigor**  |   **4/5** | development/selection/holdout separation แข็ง                                          |
| **Results & Analysis**  |   **4/5** | strong held-out result; comparator/context ยังไม่พอ                                    |
| **Clarity**             | **4.5/5** | เขียนดีและ figures ดี                                                                  |
| **Reproducibility**     |   **3/5** | checkpoint details ดี แต่ 52-config protocol/transfer constructionsไม่พอ               |
| **Overall**             |  **5/10** | **Weak Reject / Borderline**                                                           |
| **Confidence**          |   **4/5** | ค่อนข้างมั่นใจ                                                                         |

---

# 12. ถ้ามีเวลาแก้แค่ 5 อย่าง เรียงตาม ROI

| Priority | แก้                                                                           | Impact        |
| -------: | ----------------------------------------------------------------------------- | ------------- |
| 🔥 **1** | เลิกตีความ non-significance เป็น equivalence หรือเพิ่ม equivalence test       | **Very High** |
| 🔥 **2** | ทำ bridge อธิบาย 250/125/872/905 populations                                  | **Very High** |
| 🔥 **3** | ระบุ actual constructions ใน 3×3 matrix                                       | **Very High** |
|    **4** | ลด claim “exposure-bound / ranker wasted” ให้ conditional on system + Top-200 | **High**      |
|    **5** | เพิ่ม published benchmark context + PHAGE citation                            | **High**      |

ถ้ายังเหลือเวลา:

**6.** ใช้ page 6 เพิ่ม protocol details
**7.** exposure curve @500/@1000
**8.** variance/effect decomposition

---

# 13. สามเวอร์ชันสำหรับแก้ Claim ที่อันตรายที่สุด

### Conservative — ปลอดภัยสุด

> *Across the tested coarse constructions, we find no statistically resolved representation winner for any target retriever, while observed within-target variation is small relative to between-retriever differences.*

### Balanced — ผมเลือกอันนี้

> *Within the tested coarse construction space, representation choice produces small and unstable changes in Recall@100 relative to the larger performance differences associated with retriever identity.*

### Strong — ใช้ได้ถ้ามี equivalence test

> *Equivalence analysis shows that representation-induced differences remain within a pre-specified practically negligible range, whereas retriever effects are substantially larger.*

**อย่าใช้ “reordering is noise” จนกว่าจะมี evidence แบบ version 3**

---

# Final Meta-Review

ผมมอง paper นี้เป็นกรณี **“good paper, vulnerable claims”**

ของที่มีอยู่แล้วและไม่ควรไปรื้อคือ:

* research question ดี
* DAPFAM fit ดี
* 5 heterogeneous retrievers
* held-out Final-872
* paired bootstrap
* model revision/runtime specification
* narrative development → confirmation → diagnosis
* Fig. 2–4
* การยอมรับว่า system-level win ไม่ใช่ representation-only effect

สิ่งที่กำลังทำให้ score ตกไม่ใช่ experiment อ่อน แต่เป็น **การตีความ null result แรงเกินไป + comparator/context + population definitions**

ดังนั้นผม **ไม่แนะนำทำ experiment ใหม่ครั้งใหญ่** ก่อน submission

ผมแนะนำใช้หน้าที่ 6 เพื่ออุด methodology/reproducibility และแก้ wording ให้ evidence กับ claim align กัน

ถ้าทำ 5 จุดด้านบน ผมในฐานะ Reviewer #2 คนเดิมจะเปลี่ยนจาก **Weak Reject → Accept** ได้ครับ 🙂

**ต่อได้ด้วย:** `Fix major` · `Rewrite paper` · `Final review`

[1]: https://auto-index.github.io/?utm_source=chatgpt.com "AutoIndex: Learning Representation Programs for Retrieval"
[2]: https://arxiv.org/abs/2510.22264?utm_source=chatgpt.com "PatenTEB: A Comprehensive Benchmark and Model Family for Patent Text Embedding"
[3]: https://www.sciencedirect.com/science/article/pii/S2590005626000433?dgcid=rss_sd_all&utm_source=chatgpt.com "DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross domain patent retrieval - ScienceDirect"
[4]: https://arxiv.org/abs/2605.10073?utm_source=chatgpt.com "PHAGE: Patent Heterogeneous Attention-Guided Graph Encoder for Representation Learning"
