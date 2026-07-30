---
paper_id: U050
title: "Patent Language Model Pretraining with ModernBERT"
pdf_sha256: "9e0b48fff3b045e80795ba00d2cb3ee64c383c53348e523bbd9d1b0b2d85a677"
object_path: "01_evidence/A-tier/U050_patent_language_model_pretraining_with_modernbert.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/51_patent_language_model_pretraining_with_modernbert_2025.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: "2509.14926"
arxiv_source: "acquisition_url"
arxiv_confidence: "high"
page_count: 16
record_type: "paper"
tier: "A"
identity_status: "verified"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U050: Patent Language Model Pretraining with ModernBERT

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: 2509.14926 (source: acquisition_url; confidence: high)
- Pages: 16
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/51_patent_language_model_pretraining_with_modernbert_2025.pdf`
- Identity result: `verified` (filename/title token overlap 1.00)

## Classification

**Tier A.** Direct patent retrieval/search/embedding benchmark evidence. Relevant surface: C, R, IS2-adjacent.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, ranking, benchmark, patent, embedding, contrastive, retrieval-augmented, legal, biomedical, classification, summarization.

Abstract/summary section scan:

> such as legal or biomedical corpora (Beltagy Transformer-based language models such as et al., 2019; Limsopatham, 2021). Many such do- BERT have become foundational in NLP, yet mains—including patents—exhibit idiosyncratic their performance degrades in specialized do- lexical and syntactic features, warranting domain- mains like patents, which contain long, tech- specific adaptation. While fine-tuning on down- nical, and legally structured text. Prior ap- stream tasks remains a popular strategy, several proaches to patent NLP have primarily re- studies have demonstrated that extending pretrain- arXiv:2509.14926v3 [cs.CL] 18 Nov 2025 lied on fine-tuning general-purpose models or ing on domain-relevant corpora, or pretraining domain-adapted variants pretrained with lim- from scratch, can lead to substantial performance ited data. In this work, we pretrain 3 domain- specific masked language models for patents, gains (Chalkidis et al., 2020; Rasmy et al., 2021). using the ModernBERT architecture and a cu- Patent documents are a unique blend of legal rated corpus of over 60 million patent records. language and technical exposition, often structured Our approach incorporates architectural opti- and written in ways that differ sharply from general mizations, including FlashAttention, rotary em- web or news text. Tasks in this domain—including beddings, and GLU feed-forward layers. We evaluate our models on four downstream patent classification, retrieval, and paragraph highlight- classification tasks. Our model, ModernBERT- ing—have been addressed using both traditional base-PT, consistently outperforms the general- ML (Kamateri et al., 2022; Haghighian Roudsari purpose ModernBERT baseline on three out et al., 2022) and transformer-based approaches of four datasets and achieve

Conclusion/discussion section scan:

> 4 Limitations In this work, we presented ModernBERT-PT, a Language Our pretraining corpus is limited to domain-specific masked language model pretrained English-language patents. Given the global na- from scratch on a curated corpus of over 60 mil- ture of patent filings, expanding to multilingual lion patent documents. Leveraging architectural corpora could significantly improve model utility innovations such as FlashAttention, ALiBi posi- in international contexts. tional embeddings, and GLU-based feed-forward MLM-only objective Following Warner et al., layers, we demonstrated that pretraining on patent- we rely solely on the MLM objective for pretrain- specific data yields tangible benefits in both clas- ing. While MLM has proven effective, it does not sification accuracy and computational efficiency. capture sentence-level semantics or inter-document ModernBERT-base-PT outperformed a general- relationships. Future work could explore comple- purpose ModernBERT baseline on three out of mentary pretraining tasks such as contrastive objec- four downstream classification tasks and achieved tives, span prediction, or retrieval-based learning competitive performance with PatentBERT, while tailored for patent data. offering substantially faster inference speeds. Ad- Scaling Our model was trained on a compute ditional comparisons with ModernBERT-base-VX budget significantly smaller

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
