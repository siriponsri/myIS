---
unique_id: U001
priority_tier: A
sha256: 68dbc32b1cf5c86af2b0cf13da395c951387d4a038da14d1b928cd35f6a60583
canonical_path: research/ref-paper/is1/pdfs/01_patentmatch_a_dataset_for_matching_patent_2020.pdf
size_bytes: 580951
title: "PatentMatch: A Dataset for Matching Patent Claims & Prior Art"
authors: "Julian Risch; Nicolas Alder; Christoph Hewel; Ralf Krestel"
year: 2020
venue: "arXiv preprint arXiv:2012.13919 [cs.IR]"
doi: null
arxiv: "2012.13919"
extraction_cache: source-packet/03-priority-papers/extraction-cache/U001.md
experience_brain_match: no
matched_knowledge_id: null
recommended_ingestion_action: ingest_new
digest_status: completed
digest_prepared: 2026-07-24
pass_type: "Unique-PDF digestion Batch 1 (token-efficient two-stage protocol)"
authority: "External Knowledge"
---

# U001: PatentMatch Dataset Digest

**Unique ID:** U001  
**SHA-256:** 68dbc32b1cf5c86af2b0cf13da395c951387d4a038da14d1b928cd35f6a60583  
**Canonical path:** `research/ref-paper/is1/pdfs/01_patentmatch_a_dataset_for_matching_patent_2020.pdf`  
**Size:** 580,951 bytes

---

## Bibliographic Identity

**Title:** PatentMatch: A Dataset for Matching Patent Claims & Prior Art  
**Authors:** Julian Risch, Nicolas Alder, Christoph Hewel, Ralf Krestel  
**Affiliations:** Hasso Plattner Institute, University of Potsdam, Germany; BETTEN & RESCH Patent- und Rechtsanwälte PartGmbB, Munich, Germany  
**Year:** 2020  
**Venue:** arXiv preprint (arXiv:2012.13919v1)  
**DOI/URL:** https://hpi.de/naumann/s/patentmatch

---

## Research Problem

Patent examiners face a complex information retrieval task when assessing the novelty and inventive step of patent claims. Given a claim, they must search for prior art comprising all relevant publicly available information. This time-consuming task requires deep understanding of the technical domain and patent-specific language. The paper addresses computer-assisted prior art search by creating a supervised machine learning dataset called **PatentMatch** to support passage-level retrieval from patent documents.

---

## Dataset and Evaluation Setting

**Source data:** European Patent Office (EPO) full-text data for text analytics, containing XML-formatted full texts and meta-data of all filed patent applications and published patent documents processed by the EPO since 1978. Search reports available from 2012 onwards.

**Dataset construction:**
- Extracted claim-paragraph pairs from EPO search reports where patent examiners manually annotated which paragraphs from cited documents are relevant to specific claims
- "X" documents: novelty-destroying (positive samples, prejudicial to novelty)
- "A" documents: technical background only (negative samples, not prejudicial)
- "Y" documents: make invention obvious but don't destroy novelty alone

**PatentMatch statistics:**
- **Total samples:** 6,259,703 pairs of application claims and cited paragraphs
- **Document citations:** 3,492,987 "X" documents, 2,766,716 "A" documents
- **Distinct patent applications:** 31,238
- **Distinct cited documents:** 33,195
- **Distinct claim texts:** 297,147
- **Distinct cited paragraphs:** 520,376
- **Median claim length:** 274 characters
- **Median paragraph length:** 476 characters

**Two balanced variations provided:**
1. **Label-balanced:** 347,880 samples with equal "X" and "A" labels per claim text
2. **Claim-balanced:** 25,340 samples with exactly one "X" and one "A" sample per claim text

**Split:** 80% training, 20% test (time-wise split by application filing date)

**License:** Creative Commons Attribution 4.0 International Public License

---

## Method

The paper presents a **dataset creation pipeline**, not a novel retrieval method:

1. **XML parsing:** Extract full text and meta-data from EPO patent documents
2. **Citation extraction:** Parse search reports to extract claim numbers, patent application IDs, paragraph numbers, and citation types ("X", "A", "Y")
3. **Reference standardization:** Convert diverse paragraph reference formats (e.g., "[paragraph 23]-[paragraph 28]", "0023-28") to complete enumerations
4. **Text resolution:** Use Elasticsearch index to resolve paragraph numbers and claim numbers to actual text passages
5. **Filtering:** Discard references to figures, figure captions, or whole documents (not text paragraphs)

**Storage:** Elasticsearch for indexing ~210GB of text data

---

## Baselines

**Preliminary experiment:** BERT-based text pair classification using `bert-base-uncased` model fine-tuned on the PatentMatch dataset via the FARM framework.

**Task:** Given a claim text and a cited paragraph text, predict whether the paragraph corresponds to an "X" document (positive) or "A" document (negative).

**Architecture:** Bidirectional Transformer encoder (12 layers), similar to BERT's next sentence prediction task. Input: claim + paragraph as token sequence; output: [CLS] token hidden state encodes binary class label.

---

## Metrics

**Test accuracy:**
- **Label-balanced variation:** 54%
- **Claim-balanced variation:** 52%

Both only slightly better than random guessing (50%), indicating the task's difficulty. Validation loss stopped decreasing after 6 training epochs.

---

## Principal Findings

1. **Dataset contribution:** PatentMatch is the first large-scale, expert-labeled dataset for patent claim-to-paragraph passage retrieval, containing 6.26 million claim-paragraph pairs from real EPO search reports.

2. **Task difficulty:** The complex linguistic patterns, legal jargon, and patent-domain-specific language make the task extremely challenging. Fine-tuned BERT achieves only 52-54% accuracy, barely above random baseline.

3. **Expert annotation quality:** Labels come from professional patent examiners' actual search reports with rich-format citations indicating which specific paragraphs are relevant for assessing claim novelty.

4. **Comparison to CLEF-IP:** Unlike CLEF-IP 2012 claims-to-passage shared task (2.3M documents, 2,700 relevance judgments), PatentMatch provides 6.26M manually extracted expert-labeled passage pairs.

5. **Precision-focused task:** Patent search emphasizes precision over recall—finding even one "X" document is sufficient to refuse a claim, so search reports typically cite only ~5 documents with at least one novelty-destroying reference if possible.

---

## Limitations

1. **No search reports before 2012:** Search reports with paragraph-level citations only available from 2012 onwards in the EPO dataset, though older documents remain in corpus as cited prior art.

2. **Filtered references:** References to figures, figure captions, or whole documents (not text paragraphs) were discarded during standardization.

3. **Baseline performance:** The preliminary BERT experiment shows the task is extremely difficult, with accuracy barely above random. The paper does not present a strong baseline system.

4. **Patent-domain specificity:** The dataset requires substantial patent-domain knowledge to understand document types (applications vs granted patents vs search reports), classification schemes (IPC, CPC, USPC), and the patenting process.

5. **English-only:** The paper does not specify language filtering, but EPO documents include multilingual content.

6. **No retrieval corpus provided:** While the dataset provides claim-paragraph pairs, it does not package the full retrieval corpus needed for end-to-end prior art search experiments.

7. **No "Y" document analysis:** The dataset focuses on "X" (novelty-destroying) and "A" (background) documents but does not systematically include "Y" documents (render invention obvious).

---

## Relevance to Proposed Track C (Candidate Expansion)

**Moderate relevance.** PatentMatch addresses **passage retrieval** (given a claim, find relevant paragraphs in prior art), which is conceptually related to candidate expansion but operates at a different granularity:

- **Track C (proposed)** targets **document-level retrieval improvement** via query expansion, hybrid retrieval, or domain adaptation to increase candidate exposure (Recall@100).
- **PatentMatch** targets **paragraph-level passage retrieval** within already-identified documents (search reports cite documents, then annotate which paragraphs within those documents are relevant).

**Potential connections:**
- PatentMatch's expert-labeled passage judgments could inform **claim-level query formulation** (which claim elements are most discriminative for retrieval).
- The dataset's focus on precision-oriented search (finding at least one "X" document) aligns with patent search workflows, but Track C aims to improve the upstream candidate pool, not downstream passage selection.

**Gap:** PatentMatch does not address candidate expansion directly—it assumes documents are already retrieved and focuses on passage-level relevance within those documents.

---

## Relevance to Proposed Track R (Fixed-Pool Ranking)

**High relevance.** PatentMatch directly addresses **passage-level reranking** within a fixed pool of cited documents:

- **Track R (proposed)** targets **document-level reranking** within a frozen top-K candidate pool to exploit ranking headroom.
- **PatentMatch** provides **paragraph-level reranking labels** within documents already cited by examiners.

**Alignment:**
- PatentMatch's "X" vs "A" labels are analogous to Track R's goal of distinguishing high-relevance from low-relevance items within a fixed pool.
- The dataset's passage retrieval task could generalize to **claim-to-document** matching if aggregated to document level.
- The focus on **semantic matching** (claim text vs paragraph text) is the core challenge Track R would address via instruction optimization for rerankers.

**Differences:**
- **Granularity:** PatentMatch is passage-level; Track R (as tested in Paper D) is document-level (family-level in DAPFAM).
- **Metric:** PatentMatch uses binary classification accuracy; Track R uses nDCG@100 or MAP.
- **Corpus:** PatentMatch uses EPO documents; DAPFAM uses pharmaceutical patents from multiple sources.

**Potential application:** PatentMatch could serve as a **transfer learning** or **pre-training** dataset for patent-domain rerankers before fine-tuning on DAPFAM or other domain-specific benchmarks.

---

## Relevance to Proposed Track S / SkillOpt

**Moderate relevance.** PatentMatch is a **fixed dataset** with expert-labeled ground truth, not a dynamic prompt-optimization scenario:

- **Track S (proposed, not authorized)** targets **prompt/skill evolution** via methods like GEPA, testing whether prompts improve over iterations.
- **PatentMatch** provides a **static supervised learning task** (claim-paragraph matching) that could serve as a testbed for prompt-based rerankers, but does not inherently require prompt optimization.

**Potential connection:** If Track S were authorized, PatentMatch could be used to evaluate whether prompt optimization (e.g., optimizing claim rewriting or paragraph summarization prompts) improves passage retrieval accuracy. However, the dataset's binary classification format and low baseline accuracy (54%) suggest limited headroom for prompt-based gains.

---

## Relationship to Papers A-D

**No direct relationship.** PatentMatch (2020) predates Papers A/B/C/D and addresses a different task:

- **Papers A/B/D** test prompt optimization for **document-level retrieval/reranking** on DAPFAM.
- **Paper C** tests multi-module audit framework, not passage retrieval.
- **PatentMatch** provides a **passage-level retrieval dataset** with expert labels, but is not cited or used in Papers A/B/C/D.

**Potential indirect relationship:** PatentMatch's finding that **BERT achieves only 54% accuracy** on patent claim-paragraph matching aligns with Papers A/B/C/D's theme that **patent retrieval is a low-leverage domain** for standard NLP methods (prompt optimization, dense retrieval). Both suggest that patent-domain tasks resist standard neural approaches.

**Gap:** Papers A/B/C/D do not use PatentMatch for training or evaluation. DAPFAM (Papers A/B/D dataset) is family-level retrieval; PatentMatch is paragraph-level passage matching within already-cited documents.

---

## Evidence Supporting or Challenging Current Publication Plan

**Supporting evidence:**
1. **Low baseline performance (54% BERT accuracy)** aligns with Papers A/B/C/D's finding that patent retrieval is difficult for standard neural methods.
2. **Expert-labeled passage judgments** demonstrate that even human experts find passage retrieval challenging, supporting the claim that automated approaches face inherent domain difficulty.
3. **Large-scale dataset (6.26M samples)** shows that data availability is not the bottleneck—PatentMatch has massive supervision, yet BERT barely exceeds random guessing.

**Challenging/neutral evidence:**
1. **Different task granularity:** PatentMatch's passage-level task does not directly validate or challenge Papers A/B/C/D's document-level findings.
2. **No direct comparison:** PatentMatch uses EPO data; Papers A/B/C/D use DAPFAM. No cross-corpus evaluation exists.
3. **No prompt optimization tested:** PatentMatch evaluates BERT fine-tuning, not GEPA/MIPROv2/HyDE-style prompt optimization, so it does not inform Papers A/B/C's specific claims about prompt leverage.

**Implication for IS1 Hyperresearch study:** PatentMatch is a complementary resource that could enrich web-based evidence about patent retrieval difficulty, but it does not supersede or contradict Papers A/B/C/D's findings.

---

## Verification Warnings

1. **Passage-level vs document-level:** PatentMatch addresses passage retrieval within cited documents, not document retrieval from a corpus. Do not conflate it with document-level prior art search.
2. **EPO-specific:** Labels come from European Patent Office examiners; generalization to USPTO, JPO, or other jurisdictions is unknown.
3. **Post-retrieval task:** PatentMatch assumes documents are already retrieved (via search reports). It does not address the upstream document retrieval task Papers A/B/D target.
4. **No query expansion:** PatentMatch does not test query rewriting or candidate expansion methods relevant to Track C.
5. **Baseline weakness:** The 54% BERT accuracy suggests either (a) the task is extremely difficult, (b) the labels are noisy, or (c) the model is inadequate. The paper attributes it to task difficulty but does not rule out label noise.

---

## Experience Brain Cross-Check

**experience_brain_match:** no  
**matched_knowledge_ids:** None (query returned general DAPFAM and project governance knowledge, not PatentMatch-specific records)  
**memory_conflict:** none  
**recommended_ingestion_action:** ingest_new

**Rationale:** The Experience Brain contains no existing knowledge record for PatentMatch (2020, Risch et al.). The returned results were about DAPFAM (U011, a different paper) and general IS1 project governance. PatentMatch should be ingested as new External Knowledge if the project's scope expands to passage-level retrieval tasks.

---

## Status

✅ **completed** — Full PDF extraction via markdownify successful, all sections reviewed, digest complete.

---

**Digest prepared:** 2026-07-24  
**Pass type:** Unique-PDF digestion Batch 1  
**Authority:** External Knowledge (not Grounded Experience, not Paper D evidence)
