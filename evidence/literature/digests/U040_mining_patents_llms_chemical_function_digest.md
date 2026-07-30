---
paper_id: U040
title: "Mining patents with large language models elucidates the chemical function landscape"
authors: "Clayton W. Kosonocky, Claus O. Wilke, Edward M. Marcotte, Andrew D. Ellington"
year: 2024
venue: "Digital Discovery 3, 1150-1159 (Royal Society of Chemistry)"
affiliation: "Departments of Molecular Biosciences / Integrative Biology / Center for Systems and Synthetic Biology, University of Texas at Austin"
pdf_sha256: "df93f5d3e50e9c77a91cca80d62dc5e7c3c5488b9756d9441f840e4d54b20796"
eb_status: "ingest_new"
tier: "C"
extraction_cache: "extraction-cache/U040.md"
digest_created: "2026-07-25"
schema_version: "PDF_DIGEST_SCHEMA_V1"
---

# U040: Mining Patents with LLMs Elucidates the Chemical Function Landscape

## Bibliographic Identity
Kosonocky, Wilke, Marcotte & Ellington 2024, Digital Discovery 3, 1150-1159, University of Texas at Austin. DOI: 10.1039/d4dd00011k. Open access (CC BY 3.0 Unported). Code/data: github.com/kosonocky/CheF, dataset at zenodo.org/8350175, interactive viz at chefdb.app. SHA-256 verified against manifest (exact match).

## Classification
**Tier C.** This is a **chemical/drug-discovery dataset-construction paper**, not a patent prior-art retrieval or reranking system. It uses patents purely as a **text-mining source** to extract chemical-function labels via LLM summarization (ChatGPT/gpt-3.5-turbo), building a dataset (CheF) for downstream molecular-function prediction and drug discovery. No retrieval task, no MAP/Recall@k/NDCG, no candidate generation over a document corpus, no ranking of patents by relevance to a query. Tier C, consistent with this batch's other domain-adjacent non-retrieval chemistry/patent-mining papers (U021 PatCID, U024 EvoPat).

## Research Problem / Method
Motivated by the observation that small-molecule drug discovery is dominated by structure-based methods (protein-ligand docking, binding-affinity prediction) that cannot explicitly target organism-wide biological effects, while the vast corpus of chemical patent literature implicitly encodes function-structure relationships that remain largely untapped due to sparse/irregular functional descriptions and excessive legal terminology. Builds the **Chemical Function (CheF) dataset**: starting from SureChEMBL (a database of text-mined molecule-patent associations), 100K molecules (from a filtered 28.2M-molecule pool, excluding over-patented molecules with ≥10 patents to avoid label dilution) were randomly selected; for each associated patent, title/abstract/first-3500-characters-of-description were scraped from Google Patents and summarized into 1-3 word functional descriptors using gpt-3.5-turbo (specific system/user prompts documented, $0.005/molecule, 6 sec/molecule on 16 CPUs parallel). Resulting labels were cleaned (lowercased, singularized, single-character labels removed) then semantically consolidated via OpenAI text-embedding-ada-002 embeddings + DBSCAN clustering (epsilon=0.34, tuned to avoid over-merging e.g. antiviral/antibacterial/antifungal), with GPT-4 generating representative labels per cluster. Final dataset: 99,182 molecules × 1,522 unique functional labels = 631K molecule-function pairs, from 188K unique underlying patents.

## Main Findings
**Extraction quality:** manual validation on 200 random molecules (1,738 ChatGPT-generated labels, 596 associated patents) found 99.6% correct syntax, 99.8% patent-relevant; considering SureChEMBL's molecule-patent linkage quirks (patents where the molecule is only a synthesis intermediate), 77.9% of labels correctly describe the molecule's own function directly, rising to 98.2% when synthesis-intermediate associations are also counted as valid. **Clustering validation:** of the top 500 largest label clusters, 99.2% contained semantically common elements and 97.6% of GPT-4 cluster summarizations were accurate/representative. **Structure-function congruence (core validation of the paper's hypothesis):** 1261/1522 (83%) of functional labels clustered significantly in molecular-fingerprint structure space (independent t-tests, FDR-corrected, p<0.05); separately, molecules sharing the 10 most co-occurring labels were structurally closer than random for 1520/1522 labels (99.9%) — presented as evidence that the LLM-extracted text-based function landscape approximates the true chemical function landscape. **Downstream prediction:** a multi-label logistic regression model trained on CheF (daylight fingerprints → functional labels) achieved positive predictive power for 1520/1522 labels, >0.90 ROC-AUC for 433/1522 labels, average test ROC-AUC 0.84 / PR-AUC 0.20. Demonstrated qualitative case studies: correctly inferred an undisclosed HCV drug's likely NS5A-targeting mechanism from label-confidence patterns; identified serotonin-receptor ligands via label-guided search (8/10 and 7/10 true positives in two related-label queries); applied to 3242 late-stage FDA-approved drugs for repurposing, with 15/16 top HCV-predicted drugs being approved HCV antivirals. A dual-use safety check found chemical-weapon compounds (VX, mustard gas) showed no anomalous malicious-intent label signals, while some drugs of abuse showed moderate-confidence mechanism labels alongside benign molecules sharing the same labels (limiting misuse utility).

## Limitations
Extensively self-acknowledged (dedicated Discussion section): CheF is inherently **biased toward patented molecules**, sparsely representing high-utility-but-low-patentability chemicals; excluding molecules with ≥10 patents (12% reduction) explicitly omits well-studied molecules like penicillin (though authors argue impact is "negligible," per Table S8 in supplementary, not independently re-verified in this digest); risk of **false functional relationships from prophetic patent claims** (claims describing untested/hypothetical uses); models trained on CheF learn a "coarse-grained map" of chemical function "rather than a fine-grained map with activity cliffs," so should not be used for precise activity-cliff predictions; label quality is bounded by LLM summarization/clustering artifacts (documented failure modes: grammatically-similar-but-not-semantically-similar merges e.g. "has-inhibiting"/"ikk-inhibiting"; averaging to wrong shared elements e.g. anti-fungal+anti-mycotic→"anti"). Additional (from digest analysis): validation relies on the same LLM family (ChatGPT/GPT-4) used for both extraction AND validation-adjacent summarization steps, a potential circularity risk not directly addressed; the paper is chemistry/drug-discovery focused — patents are a data source, not a retrieval target, so none of its evaluation protocol (structure-space clustering, ROC-AUC prediction) transfers to patent prior-art search relevance.

## Track C/R/S Relevance (proposed, NOT AUTHORIZED / execution-closed)
Track C: MINIMAL — the paper's LLM-based patent-text-to-concise-label summarization method (specific ChatGPT prompt engineering for extracting structured labels from patent title/abstract/description) is a tangentially relevant technique for query/metadata enrichment, but the underlying task (extracting chemical function for drug discovery) is unrelated to candidate generation for prior-art retrieval. Track R: NOT RELEVANT — no ranking or reranking of documents by query relevance. Track S: NOT RELEVANT — no multi-source retrieval synthesis; the "text-based functional landscape graph" (label co-occurrence network) is a chemistry visualization tool, not an IR evidence-fusion mechanism.

## Relationship to Papers A–D
No connection. Different domain entirely (chemistry/drug discovery using patents as raw text corpus, not patent prior-art retrieval), different task (multi-label structure-function prediction, not document ranking), different metrics (ROC-AUC/PR-AUC for molecular property prediction vs. DAPFAM/Papers A-D's family-level retrieval metrics). No cross-comparison made (per schema §15).

## Verification Warnings
Non-blocking. Full paper text (Introduction, Methods §2.1-2.9 including all documented LLM prompts, Results §3.1-3.5, Discussion §4, Data Availability) read directly in a single pass; all headline percentages/statistics (99.6%/99.8% label validation, 83%/99.9% structure-space clustering, ROC-AUC 0.84) extracted cleanly from prose, no table-structure damage requiring visual verification. Supplementary Information (ESI, referenced extensively as Fig. S1-S7, Table S1-S8) was not separately fetched/reviewed — no headline claim in this digest depends on ESI-only content beyond what's stated in the main text.

## EB Cross-Check
Query: "Mining patents with large language models elucidates chemical function landscape Kosonocky Wilke Marcotte Ellington CheF dataset Digital Discovery 2024" (narrow SHA/title/DOI-scoped check; DOI 10.1039/d4dd00011k). Result: NO_MATCH (returned only unrelated IS1 patent-retrieval papers — U014/Chikkamath, a reranking paper — and literature-matrix/plan records; no record for this SHA, title, or DOI). → **ingest_new**.

---
**Digest Author:** Batch 2A Processing Agent · **Batch ID:** BATCH_2A · **Processing Status:** ✅ COMPLETED · **Content Coverage:** Full main-text body read in a single pass (complete paper, ~9 pages including references); Supplementary Information (ESI) figures/tables referenced but not separately fetched — no headline claim depends on ESI-only content.

**END OF DIGEST — BATCH 2A COMPLETE (U021–U040, 20/20)**
