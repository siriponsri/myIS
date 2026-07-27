---
paper_id: U029
title: "CLEF-IP 2011: Retrieval in the Intellectual Property Domain"
authors: "Florina Piroi, Mihai Lupu, Allan Hanbury, Veronika Zenz"
year: 2011
venue: "CLEF (Conference and Labs of the Evaluation Forum) — Lab Overview Report"
affiliation: "Vienna University of Technology (Institute for Software Technology and Interactive Systems); max-recall Information Systems OG"
pdf_sha256: "c2e600a8d73153f81716fceabe391739444a32cc156379dbe66e17f50d74b662"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U029.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U029: CLEF-IP 2011: Retrieval in the Intellectual Property Domain

## Bibliographic Identity

**Title:** CLEF-IP 2011: Retrieval in the Intellectual Property Domain

**Authors:** Florina Piroi¹, Mihai Lupu¹, Allan Hanbury¹, Veronika Zenz²
¹Vienna University of Technology, Institute for Software Technology and Interactive Systems, Vienna, Austria
²max-recall Information Systems OG, Vienna, Austria

**Venue:** CLEF 2011 Lab Overview (notebook/proceedings paper for the CLEF-IP track)

**Year:** 2011

**PDF SHA-256:** `c2e600a8d73153f81716fceabe391739444a32cc156379dbe66e17f50d74b662`

**Page Count:** ~13 pages (including appendix run-name mapping tables)

---

## Classification

**Tier:** B

**Rationale:** This is the **official CLEF-IP 2011 lab overview report** — a benchmarking-campaign summary, not a single novel retrieval method. It defines and reports on the Prior Art Candidates Search (PAC) task using patent-family-extended citation relevance (a real prior-art retrieval task) evaluated across 12 participating teams and 77 submitted runs. It contains genuine retrieval metrics (Precision@k, Recall@k, MAP, NDCG) computed with `trec_eval`, but these headline numbers are presented only in bar-chart figures (Fig. 1–8), not as extractable numeric tables in the text — so precise MAP/NDCG values cannot be quoted with confidence. It is a multi-system survey (not one method), lacks IN/OUT domain-split evaluation, and several participant methodologies are qualitatively (not quantitatively) described. This combination — real retrieval task/metrics but non-extractable headline numbers and no domain-split protocol — places it at **Tier B**, consistent with sibling CLEF-IP evaluation papers already in this batch (U014, U015 both use the CLEF-IP 2011 collection and are Tier B).

---

## Research Problem

### Problem Statement
Patent prior art search requires efficient, effective retrieval of relevant patent documents from very large multilingual collections. CLEF-IP (following on from CLEF-IP 2009/2010) exists to (1) provide a large, clean, multilingual (English/German/French) patent test collection for reproducible research, and (2) benchmark the state of the art across the community via a shared evaluation campaign with automatically-derived relevance judgments.

### Proposed Solution
Not a method paper — the "solution" is the **evaluation infrastructure**: a ~3.5M-document XML patent collection (EPO + WIPO), five parallel tasks (retrieval, classification, image-based retrieval, image-based classification), citation-derived relevance judgments extended through patent families, and a shared submission/scoring protocol (`trec_eval` 9.0, DIRECT submission system).

---

## Method (Simplified Summary)

### 1. Collection
- **Source:** 2011 collection extends the 2010 collection, built from the **MAREC** corpus (>19M patent XML documents, made available by the IRF)
- **Size:** ~3.5 million XML documents referring to ~1.5 million unique patents (increase of 1.2M documents over 2010, via added WIPO/PCT equivalents)
- **Content:** EPO (and some WIPO) patent applications/search reports/granted patents; XML fields include bibliographic data, abstract, description, claims; content in English, German, or French (granted EP documents require claims in all three languages)
- **Image subset:** 47,000 documents across 3 IPC subclasses (A43B — footwear, A61B — medical diagnosis/surgery, H01L — semiconductors) with 290,880 TIFF images (5.4 GB), added for the new image tasks

### 2. Five Tasks
1. **PAC (Prior Art Candidates Search):** "Find all patents that potentially invalidate patent application EP-nnnnnnn-An." 3,973 test topics + 300 training topics; 1/3 of topic documents each in EN/DE/FR; participants could also reuse CLEF-IP 2010 topics for training. No language restriction on retrieval — participants encouraged to exploit the multilingual claims.
2. **CLS1 (Patent Classification):** Classify a given patent to the IPC **subclass** level; 3,000 distinct topic documents (disjoint from PAC topics).
3. **CLS2 (Refined Patent Classification):** Given the correct IPC subclass, classify to the **group/subgroup** level.
4. **IMG-PAC (pilot):** Same goal as PAC but restricted to the 3 image-bearing IPC subclasses; queries include both text and the complete image set of 211 topic patents — visual comparison is often how patent examiners screen for prior art in these domains.
5. **IMG-CLS:** Classify individual patent **images** (not full patents) into 9 visual classes: drawing, chemical structure, program listing, gene sequence, flow chart, graph, mathematics, table, symbol. Training set 300–6,000 images/class; test set 1,000 images.

### 3. Relevance Judgment Construction
- **PAC / IMG-PAC:** Fully automatic, derived from patent citations in the collection. Because direct citations per patent average <4 (too sparse), the relevance set is **extended**: direct citations of the topic patent, plus citations found in the topic patent's **family members**, plus citations of the **cited patents' family members**. This is a citation-based, family-aware relevance construction — methodologically related to (but distinct from, and pre-dating) DAPFAM's explicit family-level IN/OUT domain framework.
- **CLS1 / CLS2:** Automatic, from the actual IPC codes (subclass / group-subgroup) of the topic patent documents.
- **IMG-CLS:** Manually assessed by the organizers.

### 4. Participants and Submission Protocol
- 12 institutions submitted 77 runs total across the 5 tasks: PAC=30, CLS1=16, CLS2=9, IMG-PAC=10, IMG-CLS=12 (Table 1: Chemnitz, Hildesheim, HP-Russia, Hyderabad/IIIT, Joanneum, Lugano, Nijmegen, Spinque, TU Wien (×2 groups), WISEnut, Xerox-SAS).
- Submissions uploaded to the DIRECT evaluation system; scored with `trec_eval` 9.0 (NIST).

### 5. Participant Methods (qualitative survey, per report)
- **Hildesheim + Chemnitz** (Xtrieval framework): patent-specific stopword list, per-language indexing, IPC codes added to index, phrase extraction with a rule-based dependency parser; found **long queries outperform short precise queries**; linguistic phrases did **not** improve effectiveness.
- **Hyderabad:** Lemur toolkit + query translation to English; key-phrase extraction from topic patents; citation-derived document vectors incorporating IPC codes, used both as ranking features and directly injected into result lists; found IPC information helps only when citations are *not* used (combining both degrades results).
- **Joanneum** (IMG-CLS): Local Binary Patterns (LBP) + MPEG-7 features + OCR'd text; SVM classification with late fusion across feature types; best single-feature run used LBP alone.
- **Lugano + TU Wien-2** (PAC): query formulation via **PatTextTiling** (a TextTiling-based patent summarization method); IPC-defined relevance sets to bias toward a better relevance model; Terrier indexing + **BM25** ranking; citation-filtering by topic IPC code.
- **Nijmegen** (CLS1/CLS2): Linguistic Classification System (LCS) implementing Naive Bayes, Winnow, and SVM-light classifiers; metadata (IPC, applicant/inventor/address) tested — applicant/inventor/address contributed little; Aegir dependency-parser features added to abstract + first-400-words-of-description representations; citation-based re-ranking of classification results. For PAC, teamed with **Spinque**: bag-of-words enriched with syntactic-semantic info (Aegir), English-only content, IPC-relevance-weighted query term selection, retrieval via the Spinque graphical query-strategy framework.
- **WISEnut** (PAC + CLS): weighted-keyword extraction with POS tagging and co-occurrence term addition; German/French content machine-translated to English via MyMemory; Lucene-based indexing/search; PAC results reused as k-NN-like input for the classification tasks (chosen specifically to avoid large-model memory/compute costs of standard classifiers).
- **Xerox-SAS** (IMG-PAC + IMG-CLS): Fisher-vector image representations; linear classifiers for IMG-CLS (best result from **artificially rotating training images** to model real-world image rotation); for IMG-PAC, multiple image-set comparison strategies plus text-based retrieval with per-section weighting, IPC-similarity, and citation-graph similarity — **combined via weighted late fusion** (text weighted higher than images). Visual-only retrieval performed poorly alone but **improved results when fused with text retrieval**.

---

## Main Findings

### Reported metrics (no extractable exact headline numbers in text — only in bar-chart figures)
- **PAC:** Precision, P@5/10/20/50/100; Recall, R@5/10/20/50/100; MAP; NDCG — shown per-run in Figures 1–3 (bar charts across 30 anonymized run codes), including a per-language (EN/DE/FR) MAP breakdown (Fig. 3).
- **CLS1 / CLS2:** Precision@1, Precision@5, Recall@1, Recall@5, F1@1, F1@5 — Figures 5–8, including per-language breakdowns.
- **IMG-PAC:** MAP, P@5, R@5, R — Figure 4 (Xerox-SAS runs only; 10 runs).
- **IMG-CLS:** Equal Error Rate (EER), Area Under ROC Curve (AUC), True Positive Rate (TPR, averaged per class), confusion matrices — reported numerically in **Table 2** (the one table with precise values):
  - Best run overall: **xerox-sas.RUNORH_ROTRAIN** — EER 0.04, AUC 0.99, TPR 0.91 (rotation-augmented training)
  - Best Joanneum run: **joanneum.alphacentauri** — EER 0.15, AUC 0.91, TPR 0.66
  - Worst runs: joanneum.procyon (EER 0.37, AUC 0.67, TPR 0.27), joanneum.vega (EER 0.32, AUC 0.72, TPR 0.28)

### Qualitative conclusions
- Long queries outperformed short/precise queries for PAC (Hildesheim/Chemnitz finding)
- Linguistic phrase extraction did not improve retrieval effectiveness over term-based queries
- Combining IPC-code similarity with citation information degraded PAC results relative to citation-only (Hyderabad finding) — IPC alone + text search was the best non-citation combination
- Fusing weak image-only retrieval with text retrieval **outperformed text-only retrieval** in IMG-PAC (Xerox-SAS)
- Compared to CLEF-IP 2010, collaboration between research groups intensified and methods showed increasing maturity/consolidation, but at the cost of reduced methodological diversity; overall participation was lower than the prior year
- IMG-PAC (pilot) was seen as inherently challenging due to its multimodal, multi-image-per-patent nature
- IMG-CLS had very low uptake: 6 groups registered for the data, only 2 (Joanneum, Xerox-SAS) submitted runs

---

## Limitations

### Acknowledged (Discussion/Final Observations section)
1. Declining number of participating groups compared to 2010
2. Low participation in both image-based pilot tasks despite their acknowledged importance to real-world patent search practice
3. Detailed per-measure values were not published in this report itself — deferred to a forthcoming technical report

### Additional Concerns (from digest analysis)
1. **Not a single retrieval method:** This is a multi-team benchmarking overview; there is no one "CLEF-IP 2011 system" whose numbers can be cited as *the* result — 77 runs across 12 teams with heterogeneous methods
2. **No extractable headline MAP/NDCG values:** All PAC/CLS retrieval metrics are shown only in bar-chart figures with garbled/OCR-mangled run-name axis labels in the extracted text; only the IMG-CLS table (Table 2) yields clean numeric values
3. **No domain-split (IN/OUT) evaluation:** Relevance is citation-family-extended but not stratified by technology-domain shift, unlike DAPFAM (U011)
4. **Automatic relevance judgments are a proxy:** Citation-derived relevance (even family-extended) is a known weaker proxy for true prior-art relevance than manual patent-examiner assessment
5. **Historical/foundational relevance only:** As a 2011 benchmark report, it predates transformer-based dense retrieval entirely — all participant methods are BM25/Lucene/TF-IDF/SVM/rule-based; useful chiefly as the **origin definition of the CLEF-IP 2011 dataset** that later Tier B papers in this batch (U014, U015) evaluate against, not as a source of current SOTA numbers

---

## Relevance to ThaiPhaLex Track C/R/S

### Track C: Candidate Generation — MODERATE Relevance

**Applicable:** Defines the CLEF-IP dataset/task and relevance-construction methodology (citation + family-extension) still used as an evaluation benchmark by later works in this literature set (U014, U015). The query-formulation methods surveyed (PatTextTiling summarization, key-phrase extraction, citation-based document vectors) are directly relevant analogues for Track C query-side candidate generation. The family-extended citation relevance-construction technique is a precursor to more rigorous family-level cross-domain benchmarks like DAPFAM.

### Track R: Reranking — LOW Relevance

No dedicated reranking stage is described in any participant method surveyed; ranking is produced directly by the base retrieval/classification system (BM25, Lucene, SVM, k-NN). The Xerox-SAS late-fusion of text+image scores is the closest analogue to a fusion/rerank step, but operates within a multimodal retrieval pipeline, not a post-hoc reranker over a fixed candidate list.

### Track S: Synthesis — NOT RELEVANT

No multi-view fusion of retrieval channels at the synthesis/evidence level; no family-level aggregation beyond the relevance-judgment construction step.

---

## Connection to Papers A-D (Frozen Evidence Foundation)

### No Direct Connection to Any Paper

**Papers A-D focus on patent retrieval/reranking tasks with specific frozen protocols and metrics.** U029 predates and is methodologically unrelated to those specific systems — it is the **benchmark-defining lab report** for the CLEF-IP 2011 collection that some other papers in this literature review (U014, U015) use as their evaluation dataset.

**Governance note:** No metric or methodological comparisons are made between U029 and Papers A-D. U029's PAC/CLS metrics (shown only in uninterpretable bar charts) must not be cross-compared with DAPFAM/Paper D family-level metrics or any other paper's headline numbers in this batch.

---

## Verification Warnings

### Reproducibility
1. **No code/data release statement** in this report beyond the standard CLEF-IP data distribution channel (contemporary 2011 practice, pre-dating today's GitHub-first norms)
2. **Detailed metric values withheld:** the report explicitly states detailed values for each measure "were sent to lab participants and are soon to be published into a technical report" — i.e., this overview is intentionally incomplete on precise numbers
3. **OCR/table-extraction artifacts:** Figures 1–8 (bar charts) render as garbled reversed-text run-code sequences in the markdown extraction (e.g., "5.yH 3.hC 2.hC..." for run-name axis labels) — these are chart axis labels, not data values, and could not be reliably parsed into numeric MAP/NDCG figures. Only Table 2 (IMG-CLS) yielded clean, verifiable numeric values.

### Evaluation Concerns
1. **Citation-based relevance is automatic, not examiner-verified** for PAC/IMG-PAC — a known limitation flagged directly in the source (low citation density <4/patent necessitated the family-extension workaround)
2. **No statistical significance testing** reported between systems
3. **Heterogeneous, non-standardized participant pipelines** make head-to-head comparison across the 12 teams qualitative rather than strictly controlled

---

## EB Cross-Check

**EB Query:** "CLEF-IP 2011 patent retrieval benchmark prior art candidate search evaluation lab Piroi Lupu Hanbury"

**Match Result:** ❌ NO_MATCH (EB returned general IS1 candidate-exposure synthesis, DAPFAM, PatenTEB, and literature-matrix knowledge — not this specific 2011 lab overview report)

**Ingestion Recommendation:** ✅ INGEST_NEW

**Rationale:** No existing ThaiPhaLex IS1 knowledge entry documents the CLEF-IP 2011 lab overview specifically. It is useful background as the origin definition of a benchmark dataset already referenced by other Tier B papers in this batch (U014, U015), and its family-extended citation relevance-construction is a conceptual precursor to DAPFAM's domain-aware family-level framework (already `link_existing` in this project's knowledge base).

---

## Digest Metadata

**Digest Created:** 2026-07-25
**Digest Author:** Batch 2A Processing Agent
**Schema Version:** PDF_DIGEST_SCHEMA_V1
**Batch ID:** BATCH_2A
**Paper ID:** U029
**Processing Status:** ✅ COMPLETED
**EB Cross-Check:** ✅ PERFORMED (NO_MATCH → INGEST_NEW)
**Content Coverage:** Full inline extraction read (~13 pages including appendix); sufficient for Tier B lab-overview digest. Note: bar-chart figure values not numerically extractable from OCR text; Table 2 (IMG-CLS) values fully captured.

---

**END OF DIGEST**
