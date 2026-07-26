---
unique_id: U021
priority_tier: C
sha256: 4e90f27e6d8b72449c3a96b219ddf5efd743db5f0879c25907f379648ddbe5a7
canonical_path: research/ref-paper/is1/pdfs/21_patcid_chemical_structure_database_from_patent_2024.pdf
size_bytes: 1505975
title: "PatCID: an open-access dataset of chemical structures in patent documents"
authors: "Lucas Morin, Valéry Weber, Gerhard Ingmar Meijer, Fisher Yu, Peter W. J. Staar"
year: 2024
venue: "Nature Communications"
doi: 10.1038/s41467-024-50779-y
arxiv: null
extraction_cache: extraction-cache/U021.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: Batch_2A
authority: External Knowledge
---

# U021 — PatCID: Chemical Structure Database from Patent Documents

## Bibliographic Identity

**Title:** PatCID: an open-access dataset of chemical structures in patent documents  
**Authors:** Lucas Morin, Valéry Weber, Gerhard Ingmar Meijer, Fisher Yu, Peter W. J. Staar (IBM Research Zurich, ETH Zurich)  
**Venue:** Nature Communications (2024) 15:6532  
**DOI:** 10.1038/s41467-024-50779-y  
**arXiv ID:** null (published directly in Nature Communications)  
**Publication Date:** 02 August 2024  
**Document Type:** Research article — dataset construction and evaluation  
**Field:** Chemical informatics, document understanding, patent mining

## Research Problem

Existing chemical patent databases face critical limitations: manually-curated databases (Reaxys, SciFinder) provide high quality but cannot scale to cover all patent documents globally or process older publications and Asian Pacific patents; automatically-created databases (SureChEMBL, Google Patents) have poor coverage and quality compared to manual curation. The research problem is to automatically extract chemical structure information at scale from patent document images and create a searchable open-access database that bridges the quality gap between manual and automatic approaches, while enabling both molecule-to-document and document-to-molecule retrieval with explicit page-level provenance.

## Method

PatCID uses a three-component document understanding pipeline to extract chemical structures from patent images:

1. **DECIMER-Segmentation** — Mask-RCNN-based page segmentation to locate chemical images; trained on patent documents with optimized mask expansion algorithm
2. **MolClassifier** — Mask-RCNN classifier with three output classes (Molecular Structure, Markush Structure, Background) to filter Markush structures and segmentation errors; trained on 15,720 manually-labeled chemical images
3. **MolGrapher** — Graph-based keypoint detector plus graph neural network to convert 2D molecular structure images to SMILES strings (without stereo-chemistry); trained on synthetic RDKit-generated images, runs on CPU

The pipeline processes documents from five major patent offices (USPTO, EPO, JPO, KIPO, CNIPA) covering organic chemistry patents since 1978–2016 depending on office. Basic filtering verifies predicted structures contain only one fragment.

## Dataset / Evaluation Protocol

**PatCID database:**
- 80.7M molecule images → 13.8M unique chemical structures (canonical SMILES)
- 1.2M patent documents indexed (2.8M total processed)
- Coverage: US (1978+, 48.2M molecules), EP (1978+, 11.2M), JP (2004+, 12.9M), KR (1998+, 4.7M), CN (2016+, 3.8M)
- Document selection filter: mentions term "alkyl" (organic chemistry field)
- 93.5M pages processed, 151.2M images extracted

**Benchmark datasets (introduced by this paper):**
- **D2C-RND** (random): 325 pages, 378 images, 200 molecules — random distribution reflecting average PatCID quality, predominantly recent US patents
- **D2C-UNI** (uniform): 375 pages, 375 images, 164 molecules — uniform distribution over year (1978–2024) and office to assess challenging scenarios (older patents, non-US offices with less standardized display styles)
- Benchmarks contain three subsets each: segmentation (annotated bounding boxes), classification (labeled images), recognition (MOL files with precise molecular graphs)

**Evaluation metrics:**
- **Pipeline component evaluation:** Precision/recall for segmentation, classification; recognition precision via InChIKey equality (ignoring stereo-chemistry)
- **Search evaluation:** Molecule retrieval (% of molecules retrieved from correct reference documents) and document retrieval (% of documents retrieved with chemical annotation attached), using InChIKey equality without stereo-chemistry

**Compared systems:**
- Automatic image-only: SureChEMBL (visual), Google Patents (visual)
- Automatic text+image: SureChEMBL, Google Patents, Reaxys (automatic annotations)
- Manual text+image: SciFinder, Reaxys (manual annotations)
- Manual+automatic: Reaxys (combined)

## Main Findings

**Pipeline component performance (D2C-RND / D2C-UNI):**
- DECIMER-Segmentation: 88.0% precision, 86.3% recall / 81.1% precision, 80.8% recall (outperforms YoDe-Segmentation by >40% on both metrics)
- MolClassifier: 93.4% precision, 84.6% recall / 82.9% precision, 89.5% recall
- MolGrapher recognition: 63.0% precision / 57.1% precision (after filtering: 66.3% / 61.5%) — substantially higher than OSRA (45.6% / 41.0%), lower than MolScribe (75.9% / 62.7%) but MolScribe was not available at PatCID creation time
- Complete pipeline (after filtering): 54.5% precision, 46.0% recall (D2C-RND); 41.3% precision, 44.5% recall (D2C-UNI)

**Molecule retrieval performance (D2C-RND):**
- PatCID (image-only): **56.0%** molecule recall, 100% document recall
- Google Patents (image+text): 41.5% molecule recall, 68.2% document recall
- SureChEMBL (image+text): 23.5% molecule recall, 45.3% document recall
- Reaxys (manual+auto, image+text): 53.5% molecule recall, 68.8% document recall
- SciFinder (manual, image+text): **49.5%** molecule recall

**Molecule retrieval performance (D2C-UNI — challenging set):**
- PatCID: **47.6%** molecule recall, 98.2% document recall
- Google Patents (image-only): 9.8% molecule recall, 54.3% document recall
- SureChEMBL (image-only): 4.9% molecule recall, 11.6% document recall
- Reaxys (manual+auto): **51.2%** molecule recall, 67.0% document recall

**Document section coverage (example patents):**
- PatCID retrieves 78% of molecules from description-before-examples section (US20220127225), where SciFinder retrieves 2.0% and Reaxys manual 0% (those databases focus only on examples and claims sections due to manual labor constraints)
- For examples sections: PatCID 82–100%, SciFinder 94–100%, Reaxys manual 58–100%

**Database characteristics:**
- 88% of molecules in PatCID have <5 occurrences (counted once per document), confirming low abundance of irrelevant compounds (solvents, radicals, fragments) compared to text-based extraction in SureChEMBL
- 6.8M unique molecules in PatCID not found in PubChem (out of 13.8M total unique), confirming exclusive patent-only chemical information
- PatCID covers 8.7% of molecules from D2C-RND and 5.5% from D2C-UNI that are not in Reaxys even when restricted to Reaxys-annotated documents — serves as complementary tool

## Limitations and Observations

**Acknowledged limitations:**
- **Image-only coverage** — PatCID extracts only visual representations, not textual mentions of molecules (complementary to SureChEMBL/Google Patents which include text)
- **No stereo-chemistry** — MolGrapher does not capture stereo-chemical information
- **No Markush structures** — Markush structures (sets of molecules with positional/frequency variations) are filtered out as no reliable automatic recognition method exists at scale
- **Older patents and Asian offices underperform** — D2C-UNI (uniform year/office distribution) shows lower precision (41.3% vs 54.5%) and recognition (57.1% vs 63.0%) due to less standardized display styles and lower image resolution in older documents and non-US offices
- **Still trails Reaxys on challenging set** — For D2C-UNI, Reaxys (manual+auto) achieves 51.2% molecule recall vs PatCID 47.6%, partly because Reaxys leverages patent family grouping (e.g., retrieving a Korean molecule from its US family member where display style is more standardized)

**Visual verification note:** Tables 3, 4, 5, 6 lost grid structure in PDF→text extraction (columns/rows stacked or shifted). The prose-quoted headline figures (56.0% PatCID molecule recall D2C-RND, 88.0% segmentation precision, 63.0% recognition, 78% coverage of description-before-examples) are confirmed reliable through cross-checking abstract and discussion text. Precise table-cell values beyond these prose-quoted figures require visual PDF inspection.

**Computational note:** MolGrapher runs on CPU ~2× faster than DECIMER-AI (see Supplementary Table 1), enabling large-scale processing without GPU requirements.

## Track C Relevance (proposed, NOT AUTHORIZED)

**Minimal direct relevance to text-based patent retrieval.** PatCID addresses chemical structure **image** extraction and molecule-to-document retrieval, not text-embedding-based prior-art search. The "retrieval" evaluated is molecule retrieval (given a query molecule's chemical structure, find which patents depict it) and document retrieval (% of patents with chemical annotations found), using image similarity and SMILES matching — not the text-based semantic/lexical retrieval metrics (Recall@k, MAP, NDCG) central to IS1 Track C candidate generation.

**Potential tangential connection:** If IS1 Track C were extended to multi-modal candidate generation (combining text retrieval with chemical structure image similarity for pharmaceutical patents), PatCID's pipeline and benchmarks would provide a complementary channel. However, current IS1 Track C is text-based retrieval; this paper contributes domain-adjacent chemical informatics infrastructure, not a retrieval method for textual prior-art search.

## Track R Relevance (proposed, NOT AUTHORIZED)

**No reranking component.** PatCID is a database construction and evaluation paper. The system performs segmentation → classification → recognition, not a two-stage retrieve-then-rerank architecture. Document/molecule "retrieval" is exact SMILES matching after structure recognition, not learned ranking.

## Track S Relevance (revision-stage, EXECUTION CLOSED)

**No prompt optimization or skill evolution.** PatCID uses fixed document understanding models (DECIMER-Segmentation, MolClassifier, MolGrapher) without prompt engineering or LLM-based components. No meta-learning, self-improvement, or prompt evolution mechanism is described.

## Relationship to Papers A, B, C, D

**No direct connection to Papers A–D.** Papers A–D address text-based patent prior-art retrieval (Paper A: instruction-tuned reranking, Paper D: DAPFAM family-level text retrieval with domain-aware splits). PatCID operates in a completely orthogonal modality: chemical structure **image** extraction and molecule-centric search. PatCID does not evaluate text-embedding retrieval, citation-based relevance, or claim-level semantic similarity — it evaluates whether a molecule's 2D depiction can be automatically recognized and matched across patent documents.

**Shared patent-domain context only:** Both PatCID and Papers A–D work with patent documents, but PatCID focuses on organic chemistry patents and image-based chemical informatics, while IS1 focuses on pharmaceutical formulation text retrieval. There is no methodological or evaluation-metric overlap.

**Do not cross-compare:** PatCID's molecule retrieval recall (56.0% D2C-RND) is image-to-SMILES recognition performance, not text-based patent Recall@100. DAPFAM OUT Recall@100 ≈0.1655 measures family-level citation-relevance retrieval from text; these are fundamentally different tasks and metrics despite both being called "retrieval."

## Experience Brain Cross-Check

**Query:** "PatCID chemical structure database patent documents"  
**Top 3 results:** KNO-9F9F212D663E (IS1 project plan), KNO-20DDBF1D30A0 (IS1 candidate exposure synthesis), KNO-32D2DB87C6AB (IS1 literature review)  
**Match found:** No — no Knowledge record with SHA `4e90f27e6d8b72449c3a96b219ddf5efd743db5f0879c25907f379648ddbe5a7` or title "PatCID" in top 3 results or by DOI `10.1038/s41467-024-50779-y`.  
**Recommended action:** ingest_new

## Verification Warnings

Tables 3 (pipeline precision/recall), 4 (automatic DB comparison), 5 (manual vs automatic), 6 (document section coverage) lost grid structure during PDF→text extraction — columns and rows became vertically stacked or shifted. The prose-quoted headline figures are confirmed reliable:
- Pipeline: segmentation 88.0%/86.3% precision/recall (D2C-RND), recognition 63.0% → 66.3% filtered
- Retrieval: PatCID 56.0% molecule recall D2C-RND vs Google Patents 41.5%, SureChEMBL 23.5%, Reaxys 53.5%, SciFinder 49.5%
- Document recall: PatCID 100% (D2C-RND), 98.2% (D2C-UNI) vs Google Patents 68.2% / 67.0%
- Section coverage: 78% description-before-examples vs SciFinder 2.0%, Reaxys 0%

For precise table-cell values beyond these prose-quoted numbers (e.g., per-office molecule counts, individual model ablations, additional baseline comparisons), visually inspect the source PDF pages 4–6 before citation. This is a **non-blocking** visual-check caution — the paper's main claims are confirmed reliable from prose text.

---

**Tier C classification rationale:** PatCID is a dataset construction paper for chemical structure image extraction from patents, not a text-based patent retrieval method. The "retrieval" it evaluates is molecule-to-document matching via image recognition and SMILES comparison, not the text-embedding/lexical retrieval for prior-art search central to IS1. No MAP, NDCG, or Recall@k for patent text retrieval is reported. Tier C: domain-adjacent chemical informatics infrastructure, cited for understanding patent database landscape and multi-modal patent content, but not a primary contribution to text-based prior-art retrieval methods or benchmarks.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
