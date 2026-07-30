---
paper_id: U033
title: "A survey on automated and AI-based tools for patent retrieval with a special focus on the life sciences domain"
authors: "Sara Poce, Gianni Cerro"
year: 2026
venue: "World Patent Information 85 (2026) 102439"
affiliation: "Department of Medicine and Health Sciences 'Vincenzo Tiberio', University of Molise, Italy"
pdf_sha256: "ee11448b455dc4fdac09e95d6f476472ef8ad067318715164e5e40e3d620aead"
eb_status: "ingest_new"
tier: "A"
extraction_cache: "extraction-cache/U033.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U033: A Survey on Automated and AI-Based Tools for Patent Retrieval, with Special Focus on Life Sciences

## Bibliographic Identity
Poce & Cerro 2026, *World Patent Information* 85, 102439 (Elsevier, open access CC BY 4.0), received Sept 2025, accepted Feb 2026. SHA-256 verified against manifest (exact match). ~26 pages.

## Classification
**Tier A.** A directly on-topic, comprehensive review of automated/AI-based patent retrieval methods (query expansion, metadata-based, ML-based, NLP/deep-learning-based), presenting a new taxonomy (Fig. 1) and formally defining the standard retrieval evaluation metrics used across this entire literature set (Precision, Recall, F-score, MAP, nDCG, and the PRES score — the same PRES metric already encountered via Magdy & Jones in U030's reference list). Not itself an empirical system with new experiments, but its scope, recency (2026), and role as a canonical reference/taxonomy for interpreting every other patent-retrieval paper in this batch place it at Tier A rather than B — it functions as connective infrastructure for the whole literature review, not a narrow domain-adjacent finding.

## Research Problem / Method
Motivated by a perceived gap: prior surveys cover deep learning OR NLP OR ML for patent analysis individually, but none comprehensively organizes traditional-to-advanced patent retrieval methods in one place, and none gives dedicated treatment to the life-sciences domain's specific challenges (nomenclature ambiguity/polysemy, high dependency on visual/structural representations like chemical structures and biological sequences). The paper surveys: (1) general vs. life-sciences patent databases (PATENTSCOPE, Espacenet, USPTO, DEPATISnet, Google Patents, Derwent WPI; plus CLEF-IP, NTCIR, TREC-Chem, CHEMDNER as thematic test collections; plus BindingDB, PubChem, ChemSpider, GENESEQ, PatentsView-style chemical/biological sources); (2) formal retrieval metrics (Precision/Recall/F-score/MAP/nDCG/PRES, with PRES defined per Magdy & Jones 2010 as combining recall with early-rank concentration of relevant results); (3) four automated-method categories — query expansion (semantic/dictionary/ontology/corpus-based and pseudo-relevance feedback), metadata-based (citation/classification-based), machine learning (traditional ML and deep learning), and NLP-based (statistical/semantic, hybrid NLP+ML, hybrid NLP+DL); (4) a dedicated life-sciences section covering chemical/biological/biomedical NER, chemical structure extraction, and biological sequence retrieval.

## Main Findings
Reports numerous prior systems' own metrics as secondary evidence (not the survey's own results), e.g.: Mahdabi et al.'s IPC-lexicon proximity-based query expansion on CLEF-IP 2010/2011 reaching 65.95% recall but weak MAP; Gurulingappa's TREC-Chem noun-phrase+entity+co-citation system reaching MAP 0.2336; Pasche et al.'s TWINC system reaching MAP 8.9% (MeSH-only) to 18.2% (with query expansion); the PAtentPilot pharmaceutical retrieval system's optimized configuration reaching only 6.76% precision / 4.22% MAP; PatCID (already digested as U021 in this batch) achieving 56.0% D2C-RND molecule retrieval, outperforming Google Patents (41.5%), Reaxys (53.5%), SciFinder (49.5%) on chemical-structure-image retrieval but not integrating text. The survey's own cross-cutting conclusion: life-sciences patent retrieval systems, across all four method categories, consistently show suboptimal recall (often "rarely exceeding 20%" precision with recall "around 50%") and remain unready for real-world/high-stakes use; information is fragmented across many non-interoperable databases (general, thematic/test, and chemical/biological-specific); no unified multimodal (text+image+structure+sequence) architecture yet exists, though foundation-model analogues (ChemBERTa, DNABERT/ProtBERT, Text2Mol, MolLM, TxGemma) suggest a path forward.

## Limitations
Acknowledged: many life-sciences-specific systems (TWINC, PAtentPilot, PEMT, Shimizu et al.'s RNN-based molecule generator) are not publicly documented/reproducible; biological sequence retrieval is fragmented across databases with inconsistent WIPO ST.25→ST.26 migration; BERT-family models' 512-token limit forces lossy segmentation of long patent text; document-level vs. family-level processing tradeoffs (redundancy/noise vs. loss of jurisdictional nuance) are unresolved. Additional: as a survey, all quantitative figures are secondhand summaries of cited primary studies, several of which (per the survey's own critique) use non-standardized or incompletely-reported evaluation protocols — these numbers must trace back to their original papers before precise citation, not to this survey.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: HIGH — the taxonomy of query-expansion/metadata/ML/NLP candidate-generation approaches and their documented failure modes (noise from over-broad expansion, citation/classification incompleteness, 512-token truncation) directly informs Track C design choices and known pitfalls to avoid. Track R: LOW — no dedicated reranking taxonomy beyond citation-based re-ranking mentions (e.g., co-citation re-ranking in TWINC/PAtentPilot). Track S: NOT RELEVANT.

## Relationship to Papers A–D
No direct connection; this survey does not evaluate DAPFAM-style family-level cross-domain retrieval and its PRES/MAP figures for individual cited systems are not comparable to Papers A–D's or DAPFAM's metrics (different corpora/relevance definitions per §15 — no cross-comparison made). Notably corroborates/cross-references U021 (PatCID, already in this batch) directly by name, confirming consistency of that digest's headline figures (56.0%/41.5%/53.5%/49.5%) with an independent secondary source.

## Verification Warnings
Non-blocking. Extraction (~7,388 lines) was read via targeted section reads (TOC, intro, metrics section incl. PRES formula, life-sciences NER/structure/sequence sections, discussion/conclusions, acronym appendix) rather than exhaustive linear reading, per schema §3 (targeted reads for large caches) — full method-by-method tables in Sections 4.1–4.4 (Tables 1–3, query-expansion/metadata/ML results) were not individually transcribed but their presence and general content (metrics reported "when provided," per-method result tables) were confirmed via section-header verification. No headline claim in this digest depends on those untranscribed table cells; any future precise-cell citation from Tables 1–3 requires a fresh targeted read per schema §16.

## EB Cross-Check
Query: "survey automated AI-based tools patent retrieval life sciences domain Poce Cerro World Patent Information 2026" (narrow SHA/title/DOI-scoped check; DOI 10.1016/j.wpi.2026.102439). Result: NO_MATCH (returned only unrelated IS1 literature-matrix/research-gaps records and two distinct other WPI papers — U070/U079-equivalent reranking and novelty-prediction papers, not this survey). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Targeted section reads across ~26-page/7,388-line extraction; TOC, intro, metrics, life-sciences sections, and discussion/conclusion read in full; method-comparison tables (1–3) confirmed present but not cell-by-cell transcribed.

**END OF DIGEST**
