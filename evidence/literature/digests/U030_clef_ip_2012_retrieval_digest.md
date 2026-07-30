---
paper_id: U030
title: "CLEF-IP 2012: Retrieval Experiments in the Intellectual Property Domain"
authors: "Florina Piroi, Mihai Lupu, Allan Hanbury, Walid Magdy, Alan P. Sexton, Igor Filippov"
year: 2012
venue: "CLEF (Conference and Labs of the Evaluation Forum) — Lab Overview Report"
affiliation: "Vienna University of Technology; Qatar Computing Research Institute; University of Birmingham; SAIC-Frederick Inc., Frederick National Lab (Maryland, USA)"
pdf_sha256: "43f35981d827f6c1118c11fc8f4aa97f964e40c8df223b8876f5d6550e5d0c07"
eb_status: "ingest_new"
tier: "B"
extraction_cache: "extraction-cache/U030.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U030: CLEF-IP 2012: Retrieval Experiments in the Intellectual Property Domain

## Bibliographic Identity
Official CLEF-IP 2012 lab overview (TU Wien + QCRI + Birmingham + SAIC-Frederick), direct sequel to U029 (CLEF-IP 2011, cited as ref [6]). SHA-256 `43f35981d8...5d0c07` verified against manifest (exact match).

## Classification
**Tier B.** Same structural pattern as U029: a multi-team benchmarking report with a genuine retrieval task, but headline numbers for that task are not extractable/not yet available at time of writing. Only the chemical-structure sub-task (classification/recognition, not retrieval) has clean numeric results.

## Research Problem / Method
Reuses the 2011 MAREC-derived EPO+WIPO XML collection (~1.5M patents) minus the 2011 image-classification data, and replaces 2011's 5 tasks with 3 new/refined ones:
1. **Passage Retrieval from Claims:** topics = claim sets from post-2001 applications with 2–12 X/Y-marked citations; participants retrieve documents AND mark relevant passages via XPath. 105 test topics (35 EN/DE/FR each). Evaluated at document level (Pres, Recall, MAP@100) and passage level (MAP(D)/Precision(D), averaged per relevant document then per topic).
2. **Flowchart Recognition:** patent flow-chart images → structured graph text (nodes/edges/labels); scored via maximum-common-subgraph distance at 3 levels (structure/node-types/text-labels).
3. **Chemical Structure Recognition:** segmentation (bounding-box extraction, pixel-tolerance P/R/F1) and recognition (OpenBabel/InChI auto-match on an 865-diagram "automatic set"; manual visual comparison on a 95-diagram Markush "manual set").
12 institutions, 31 runs total (13 Claims-to-Passage, 7 Flowchart, remainder chemical structure).

## Main Findings
- **Passage retrieval:** methodology defined; no extractable headline MAP/Pres numbers in the report text.
- **Flowchart recognition:** explicitly "results not available at time of writing" (evaluation not closed).
- **Chemical structure — segmentation:** best (saic, tolerance=55px) P 0.887 / R 0.860 / F1 0.873 (sole participant).
- **Chemical structure — recognition:** best overall uob-4, 886/960 (92%): 832/865 (96%) automatic set, 54/95 (57%) manual/Markush set; saic 799/960 (83%).

## Limitations
No single method under test — multi-team survey. Two of three tasks (the retrieval-relevant one and flowchart) have no extractable/available quantitative results at publication. Chemical-structure results are recognition/classification accuracy, not retrieval metrics — must not be cross-compared with DAPFAM/family-level metrics. 2012-era methods (BM25/Lucene/trigram, no dense retrieval).

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: LOW-MODERATE — defines the Passage-Retrieval-from-Claims task and citation+family-extended relevance construction, a precursor to family-level frameworks. Track R: LOW — no dedicated reranking stage described. Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection. Historical/methodological lineage only (CLEF-IP 2011→2012 series; dataset later reused by Tier B papers U014/U015 in this batch). No metrics cross-compared with Papers A–D or DAPFAM.

## Verification Warnings
Non-blocking: passage-retrieval and flowchart headline numbers are absent from the source text itself (not an OCR/table-damage issue — the paper states results were not yet available), so no numeric retrieval claim is asserted beyond methodology. Table 2 (segmentation) and Table 3 (recognition) numeric values were read cleanly from prose/table text.

## EB Cross-Check
Query: "CLEF-IP 2012 passage retrieval from patent claims flowchart recognition chemical structure recognition benchmark Piroi Lupu Hanbury Magdy Sexton" (narrow SHA/title/DOI check — no arXiv/DOI exists for this report). Result: NO_MATCH (returned only unrelated IS1 synthesis, DAPFAM, PatenTEB records; no record for this SHA or title). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full inline extraction (~12 pages) read.

**END OF DIGEST**
