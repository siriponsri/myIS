---
source_unique_id: U154
title: "AutoIndex: Learning Representation Programs for Retrieval"
source_sha256: 418159e232318ed240ec36659f85942d481578968d6011f839bc8539c974306f
canonical_pdf_path: evidence/literature/source/U154_autoindex_learning_representation_programs_for_retrieval.pdf
source_url: https://arxiv.org/pdf/2607.18603
arxiv_id: 2607.18603
version: v1
published: 2026-07-21
authors: "Sam O'Nuallain, Nithya Rajkumar, Ramya Narayanasamy, Hanna Jiang, Shreyas Chaudhari, Andrew Drozdov"
categories: "cs.IR, cs.AI, cs.CL"
page_count: 27
priority_tier: A
record_type: paper
identity_status: verified
review_depth: metadata_plus_full_text_section_scan
status: curated
---

# U154 Digest: AutoIndex: Learning Representation Programs for Retrieval

## Scope and Identity

AutoIndex is a preprint proposing retrieval-aware optimization of the document representation exposed to a fixed retrieval system. The source is arXiv `2607.18603v1`, dated 2026-07-21. The downloaded PDF contains 27 pages and is stored at the canonical Research path recorded in the frontmatter.

## Problem and Contribution

The paper argues that chunking, context attachment, normalization, section weighting, and related indexing choices should be optimized as an explicit search target rather than treated as static preprocessing. AutoIndex searches over executable representation programs that map each source document to one or more indexable units while preserving the source-document identifier.

The main contribution is a validation-guided program-search loop with three components:

1. An Analysis Agent inspects concrete retrieval failures under the current representation program.
2. A Code Agent proposes executable candidate programs using the failure summary and search history.
3. A sandboxed evaluator rebuilds the index, runs a fixed retriever, and accepts only candidates that improve the validation objective.

The retriever and ranking backend are held fixed so that measured differences are attributed to the representation program. The paper uses BM25 as its primary instantiation and aggregates passage-level scores to source documents with MaxP.

## Method and Protocol

- Search object: executable document-to-index-unit program `f_theta`.
- Fixed retriever: BM25 (`bm25s` Lucene implementation in the reported setup).
- Unit aggregation: document score is the maximum score over units derived from that document.
- Failure categories: anchors, recall violations, and ranking violations, selected from a stratified query subset.
- Candidate search: four candidates per iteration, five iterations in the primary qwen3-coder setting, with search history enabled.
- Selection rule: keep candidates when validation Recall@100 improvement is at least `1e-5`; evaluate the best validation checkpoint once on held-out queries.
- Execution boundary: syntax validation and a 15-minute candidate execution timeout.

The primary benchmark is CRUMB, an eight-task heterogeneous retrieval benchmark covering ClinicalTrial, CodeRetrieval, LegalQA, PaperRetrieval, SetOpEntity, StackExchange, TheoremRetrieval, and TipOfTongue. Each task is split into validation and held-out evaluation queries at a 1:2 ratio. The paper reports Recall@100 as the optimization target and nDCG@10 as a secondary metric.

## Evidence and Reported Results

In the qwen3-coder, search-history-enabled setting, AutoIndex improves held-out Recall@100 over full-document BM25 on all eight CRUMB tasks. The abstract reports average gains of `+8.4%` Recall@100 and `+8.3%` nDCG@10, with largest reported gains of `+30.5%` Recall@100 and `+43.6%` nDCG@10. Table 1 reports per-task relative Recall@100 changes of approximately `+2.1%` (ClinicalTrial), `+10.4%` (LegalQA), `+30.5%` (SetOpEntity), `+4.1%` (StackExchange), `+6.7%` (TipOfTongue), `+0.1%` (CodeRetrieval), `+19.2%` (PaperRetrieval), and `+8.4%` (TheoremRetrieval). Table 2 reports the corresponding nDCG@10 changes, including `+42.5%` on LegalQA and `+43.6%` on SetOpEntity, with regressions on TipOfTongue and PaperRetrieval.

The paper also reports that learned representation programs outperform CRUMB's uniform passage-corpus baseline on every task where that baseline is available. A single dense-retrieval transfer experiment on StackExchange reuses the learned representation and reports Recall@100 increasing from `0.7391` to `0.8741` with Qwen3-Embedding-0.6B. This is preliminary evidence only, not a broad dense or hybrid evaluation.

## Ablations and Mechanistic Findings

The five-iteration loop is materially stronger than a one-iteration condition: the one-iteration ablation improves only 3 of 8 splits. Removing the Analysis Agent leaves 6 of 8 splits positive but reduces effect magnitudes, supporting the role of concrete failure analysis. Removing search history is mixed across splits and changes candidate trajectories. Worked examples show selective LaTeX cleanup and section reweighting emerging from observed retrieval failures rather than from a universal preprocessing rule.

## Limits and Claim Use

The reported evidence is a preprint result on CRUMB under a fixed BM25 retriever, limited iteration budget, and small seed count. The paper does not establish transfer across unseen datasets, broad dense/hybrid/reranking performance, cost or latency neutrality, or superiority under a family-level patent benchmark. It explicitly leaves convergence, index size, preprocessing cost, multi-objective selection, program transfer, adaptive per-corpus programs, and optimizer transfer for future work.

For myIS, AutoIndex is relevant as a representation/indexing hypothesis and as a design reference for the R1 SCOPE/AutoIndex interface. It does not authorize importing its benchmark numbers, query splits, or implementation assumptions into DAPFAM. Any myIS claim must be measured with the frozen DAPFAM evaluator, protected split boundary, and canonical run manifest.

## Controlled Content Signals

Controlled content signals found in the full-text extraction: retrieval, representation program, indexing, BM25, MaxP, chunking, failure analysis, program synthesis, validation selection, Recall@100, nDCG@10, benchmark, agent, cost/latency limitations.

## Source Pointers

- PDF: `evidence/literature/source/U154_autoindex_learning_representation_programs_for_retrieval.pdf`
- SHA-256: `418159e232318ed240ec36659f85942d481578968d6011f839bc8539c974306f`
- arXiv: `https://arxiv.org/abs/2607.18603v1`
- Repository cited by the paper: `https://github.com/auto-index/autoindex`
