---
paper_id: U047
title: "Prior Art Retrieval using Patent Sections (CLEF-IP 2010 \u2013 Dhondt et al.)"
pdf_sha256: "41c973d35288702ee572061d7d35bfbd55e5267fa76ab03c7bf7790be81c9d9d"
object_path: "01_evidence/A-tier/U047_prior_art_retrieval_using_patent_sections_clef_ip_2010_dhondt_et_al.pdf"
legacy_primary_alias: "research/ref-paper/is1/pdfs/48_prior_art_retrieval_using_patent_sections_2010.pdf"
doi: ""
doi_source: ""
doi_confidence: "not_detected"
arxiv_id: ""
arxiv_source: ""
arxiv_confidence: "not_detected"
page_count: 6
record_type: "paper"
tier: "A"
identity_status: "verified_with_title_variation"
review_depth: "metadata_plus_full_text_section_scan"
digest_created: "2026-07-27"
schema_version: "LITERATURE_TRIAGE_DIGEST_V2"
---

# U047: Prior Art Retrieval using Patent Sections (CLEF-IP 2010 – Dhondt et al.)

## Bibliographic Identity

- Verified title source: `acquisition_metadata_verified_in_pdf`
- DOI: not detected (source: not detected; confidence: not_detected)
- arXiv ID: not detected (source: not detected; confidence: not_detected)
- Pages: 6
- Source collection: `is1`
- Legacy primary alias: `research/ref-paper/is1/pdfs/48_prior_art_retrieval_using_patent_sections_2010.pdf`
- Identity result: `verified_with_title_variation` (filename/title token overlap 0.82)

## Classification

**Tier A.** Direct patent retrieval, ranking, or representation method. Relevant surface: C, R.

## Content Triage

Controlled content signals found in the full-text extraction: retrieval, reranking, ranking, benchmark, patent, prior art.

Abstract/summary section scan:

> In this paper we describe our participation in the 2010 CLEF-IP Prior Art Retrieval task where we examined the impact of information in different sections of patent doc- uments, namely the title, abstract, claims, description and IPC-R sections, on the re- trieval and re-ranking of patent documents. Using a standard bag-of-words approach in Lemur we found that the IPC-R sections are the most informative for patent re- trieval. We then performed a re-ranking of the retrieved documents using a Logistic Regression Model, trained on the retrieved documents in the training set. We found indications that the information contained in the text sections of the patent document can contribute to a better ranking of the retrieved documents. The official results have shown that among the nine groups that participated in the Prior Art Retrieval task we achieved the eigth rank in terms of both Mean Average Precision (MAP) and Recall. Categories and Subject Descriptors H.3 [Information Storage and Retrieval]: H.3.1 Content Analysis and Indexing; H.3.3 Infor- mation Search and Retrieval General Terms Retrieval, Reranking

Conclusion/discussion section scan:

> In our contribution to the CLEF-IP 2010 Prior Art Retrieval task we examined the impact of different sections of patent documents on the retrieval and re-ranking of patent documents. Using a standard bag-of-words approach in Lemur we found that the IPC-R sections are more informative for patent retrieval than a full-text representation of the patent document. We then performed a re-ranking of the retrieved documents using a Logistic Regression Model, trained on the retrieved documents in the training set. Looking at the improved MAP scores, we found indications that the information contained in the separate text sections of the patent document can contribute to a better ranking of the retrieved documents.

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
