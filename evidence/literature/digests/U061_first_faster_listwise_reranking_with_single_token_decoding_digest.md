---
paper_id: U061
title: "FIRST faster listwise reranking with single token decoding"
pdf_sha256: "fca02e77ff691f6de93cc21bfd5dfc56ea925b73c25f3e8dee50a1b67df67296"
object_path: "01_evidence/B-tier/U061_first_faster_listwise_reranking_with_single_token_decoding.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/62__first_faster_listwise_reranking_single_token_decoding_2024.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 11
record_type: "paper"
tier: "B"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U061: FIRST faster listwise reranking with single token decoding

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 11
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/62__first_faster_listwise_reranking_single_token_decoding_2024.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier B.** Transferable retrieval, RAG, evaluation, uncertainty, or knowledge-graph method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, contrastive, prompt optimization, agent, biomedical.

Abstract/summary section scan:

> Rank the passages below based on their relevance to the search query. All the passages should be listed Large Language Models (LLMs) have signif- using identifiers in descending order of relevance. icantly advanced the field of information re- Search Query trieval, particularly for reranking. Listwise A: <Candidate Passage> LLM rerankers typically showcase superior B: <Candidate Passage> C: <Candidate Passage> performance and generalizability over conven- tional supervised approaches. However, exist- ing LLM rerankers can be inefficient as they provide ranking output in the form of a gen- LLM Reranker erated ordered sequence of candidate passage (a) Generation Approach (b) FIRST Approach identifiers. Further, they are trained using the Generate Entire Sequence 'C' C Single Token standard language modeling objective, which Generation C Single Token treats all ranking errors uniformly, potentially LLM Generation at the cost of misranking highly relevant pas- CA Output Vocabulary Logits 'C' LLM sages. Addressing these limitations, we intro- CAB duce FIRST1 , a novel listwise LLM reranking Explicit Rank Order Output Vocabulary Logits 'B' 'C' approach that leverages the output logits of the C > A > B 'A' 'B' first generated identifier to directly obtain a Implicit Rank Order ranked ordering of the candidates. We further > Order > Rank Implicit C A B utilize a learning-to-rank loss for this model, Language C > A > B Modelling Loss which prioritizes ranking accuracy for the more relevant passages. Empirical results demon- strate that FIRST accelerates inference by 50% Relevance Supervision Learning to while maintaining robust ranking performance, Label A > C > B Rank Loss with gains across the BEIR benchmark. Finally, to illustrate the practical effectiveness of list- Figure 1

Conclusion/discussion section scan:

> No reliable conclusion section was extracted.

## Evidence Use

This record is indexed for source discovery and method/background triage. Any
numeric or comparative claim used in a paper, thesis, slide, or experiment
protocol must be checked against the canonical PDF object and cited to the
relevant page; this digest is not a substitute for claim-level verification.

## Limitations And Verification

- Review depth is metadata verification plus a full-text scan for abstract,
  conclusion, and controlled topic signals. Identifiers are recorded only from
  acquisition URLs, PDF metadata, or explicitly labeled first-page front
  matter; bibliographies are excluded from identifier discovery.
- Tables, figures, equations, appendices, and numeric results were not
  independently transcribed in this corpus migration pass.
- Legacy aliases remain in `catalog/legacy_aliases.csv`; misleading aliases do
  not create a second paper identity.
