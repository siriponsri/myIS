---
paper_id: U031
title: "Report on the CLEF-IP 2011 Experiments: Exploring Patent Summarization"
authors: "Parvaz Mahdabi, Linda Andersson, Allan Hanbury, Fabio Crestani"
year: 2011
venue: "CLEF Workshop Notebook Papers"
affiliation: "University of Lugano, Switzerland; Vienna University of Technology, Austria"
pdf_sha256: "801f9f44e5e6a3f97f63a9dc2e7f74650250ee68ca6a51a42ac81f0abb25394a"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U031.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U031: Report on the CLEF-IP 2011 Experiments: Exploring Patent Summarization

## Bibliographic Identity
University of Lugano + TU Wien participant notebook paper for the CLEF-IP 2011 Prior Art Candidate (PAC) Search task — a companion/participant-side report to the U029 lab overview (both from CLEF-IP 2011; TU Wien authors overlap: Hanbury common to both). SHA-256 verified against manifest (exact match).

## Classification
**Tier B.** Contains genuine, extractable retrieval metrics (MAP, NDCG, P@k, Recall@k) on the real CLEF-IP 2011 PAC task — unlike U029's non-extractable bar charts, this paper reports its own numbers directly in text tables. However, absolute performance is low (best MAP 0.0896) and the paper is a single-institution query-modeling ablation (4 runs, English subset only, 1351 queries), not a canonical benchmark or SOTA contribution, and has no family-level or domain-split evaluation — consistent with the Tier B pattern already set for CLEF-IP methodology papers (U014, U015) in this batch.

## Research Problem / Method
Investigates two query-modeling strategies for the CLEF-IP 2011 PAC task (query topic = a full patent document; goal = retrieve all relevant prior-art documents): **summary-based (SM)** — a novel patent-adapted TextTiling variant ("PatTextTiling") builds a topic summary, from which query terms are sampled via weighted log-likelihood favoring terms similar to the summary/IPC-cluster language model but dissimilar to the collection model; and **description-based (DM)** — samples terms directly from the description section. Both are filtered to require ≥1 shared IPC class with the query document. Two further runs (**Cit+SM**, **Cit+DM**) linearly combine each with a regex-based direct-citation-extraction signal. Retrieval backend: Terrier BM25, English subset only (Porter stemming, stopword removal).

## Main Findings
Table 3 (1351 English queries): SM MAP 0.0871/NDCG 0.2305/Recall@1000 0.5254; DM MAP 0.088/NDCG 0.2318/Recall@1000 0.5261; Cit+SM MAP 0.0887; **Cit+DM (best) MAP 0.0896/NDCG 0.2344/Recall@1000 0.529**. Ranked 3rd of 6 participants and 4th of 30 runs on MAP; 3rd/8th on Recall@1000. Citation extraction succeeded for only 102/1351 topics (avg 1 citation each) — modest gain, poor recall alone (citation-only run MAP 0.07, Recall@100 0.0784). Post-hoc analysis: SM beats DM on 618 topics, DM beats SM on 628 (near-balanced, no consistent winner); 42 topics unretrievable by either method, correlated with relevant documents lacking English text beyond the title (0.48 of non-retrievable-set relevant docs vs 0.18 of easy-set) — attributed to retrievability bias (Bashir & Rauber 2009/2011), not a method flaw.

## Limitations
Single-language (English-only) subset of a multilingual collection; low absolute MAP typical of 2011-era BM25+query-modeling approaches; SM vs DM difference is not decisive (near 50/50 split across topics); citation extraction is a crude two-stage regex without patent-office API validation, limiting its contribution. Narrow scope — no domain-split (IN/OUT) evaluation, no family-level aggregation.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: MODERATE — PatTextTiling summarization-based query formulation and IPC-cluster relevance-model estimation are directly relevant analogues for Track C query-side candidate generation; the retrievability-bias finding (short/title-only documents systematically under-retrieved) is a useful caution for any candidate-generation design. Track R: NOT RELEVANT (no reranking stage). Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection. Historically part of the same CLEF-IP 2011 campaign as U029; no metric cross-comparison made (this paper's PAC MAP/Recall values are on a different collection/relevance definition than DAPFAM/Papers A–D and must not be treated as comparable).

## Verification Warnings
Non-blocking. All headline metrics (Table 3, Table 4, Table 5) are clean, directly-extractable text tables — no OCR/grid-damage issues encountered. Figure 1 (AP-difference plot) is described only qualitatively (image, not a data table); no numeric values were needed from it for the digest's main claims.

## EB Cross-Check
Query: "CLEF-IP 2011 Prior Art Candidate Search PatTextTiling patent summarization query modeling Mahdabi Andersson Hanbury Crestani" (narrow SHA/title/DOI-scoped check — no DOI/arXiv ID exists for this notebook paper). Result: NO_MATCH (returned only unrelated PatenTEB, DAPFAM, IS1-synthesis, and QaECTER records; no record for this SHA or title). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full inline extraction (~10 pages) read.

**END OF DIGEST**
