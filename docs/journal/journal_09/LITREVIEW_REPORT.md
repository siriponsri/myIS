# Literature audit for journal_09

Date: 2026-09-01

## Scope and evidence rule

This audit searched the local research repository and its readable literature
digests for `candidate generation`, `recall ceiling`, `first-stage retrieval`,
`oracle reranking`, `Recall@k`, `pooling bias`, `prior art recall`, and `patent
retrieval evaluation`. Bibliographic facts and prior claims below are taken only
from files that were readable locally. No web-only result or memory-based
metadata was used.

The two requested PII targets were also checked. A readable local metadata
digest was found for the 2026 life-sciences survey. No readable local PDF or
metadata file for Rees and Wirz (PII `S0172219025000250`) was found, so its
TODO remains in `references.bib` and its unresolved entry is not cited in the
manuscript.

## Novelty / prior-claim check

Question: has a prior paper quantitatively reported that errors caused by
relevant items not entering the candidate pool (exposure) exceed errors caused
by ordering within the pool?

| Local file | Close claim previously made? | Difference from this paper | Cite? |
|---|---|---|---|
| `evidence/literature/digests/U002_prior_art_search_reranking_digest.md` | Qualitative bounded-recall statement: the authors note that BM25 can filter out suitable candidates before embedding reranking, so reranking cannot recover them. | No quantitative exposure-versus-ordering decomposition, no family-level benchmark, and no Recall@100 oracle bound. | Yes, as qualitative motivation if desired; not evidence for the numeric claim. |
| `evidence/literature/digests/U006_bert_bm25_combination_digest.md` | Reports Recall@100 and MAP gains for BM25/BERT score interpolation. | The gain is a reranking-side score blend over a BM25 pool; it does not measure absent candidates separately from within-pool ordering. | No additional citation needed for the present claim; it is already represented by the existing retrieval references. |
| `evidence/literature/digests/U014_rethinking_patent_retrieval_lms_digest.md` | Studies retrieve-then-rerank patent retrieval and reports MAP/efficiency results. | CLEF-IP and MAP conflate candidate exposure with ordering; no oracle reordering or absent-pair count. | Yes for recent WPI context; not a prior quantitative exposure claim. |
| `evidence/literature/digests/U033_survey_automated_ai_patent_retrieval_digest.md` | Synthesises patent-retrieval methods and notes generally weak recall. | A survey, not a controlled exposure decomposition; reported values are secondary and not comparable to DAPFAM family-level metrics. | Yes for field context; not for the exposure/order result. |
| `evidence/literature/digests/U039_fullrecall_semantic_search_ranking_digest.md` | Emphasises recall and reports 100% recall on five granted patents. | Very small evaluation, large returned sets, no ranking metric or pool-vs-order decomposition. | No: it does not close the novelty gap and is not comparable evidence. |
| `evidence/literature/digests/U064_guiding_retrieval_with_llm_listwise_rankers_digest.md` | Explicitly describes bounded recall in first-stage retrieval and reports adaptive-retrieval gains. | Non-patent LLM reranking study; its adaptive method changes retrieval, and it does not quantify the DAPFAM exposure/order partition. | No additional citation for this manuscript's patent-specific claim. |

### Finding

No locally readable prior work was found that reports the same quantitative
claim: an explicit exposure error and an explicit within-pool ordering bound on
the same population, showing exposure to be larger. The closest prior statement
is U002's qualitative bounded-recall warning. The present paper's comparison is
therefore a quantitative diagnostic result, bounded to DAPFAM, the frozen
Top-200 pool, and its stated pair- and query-level denominators. This is a
novelty gap, not a claim that no related retrieval paper exists anywhere.

## Bibliography actions

| Entry | Action | Readable source path |
|---|---|---|
| `poce2026survey` | Completed volume `85`, article `102439`, DOI, and retained the two authors listed in the verified digest; removed the TODO field. | `evidence/literature/digests/U033_survey_automated_ai_patent_retrieval_digest.md` |
| `chikkamath2026rethinking` | Retained as a directly relevant recent WPI citation; no new key was added in this revision. | `evidence/literature/digests/U014_rethinking_patent_retrieval_lms_digest.md` |
| `rees2025evaluating` | TODO retained; no readable local PDF/metadata was found for PII `S0172219025000250`. The manuscript citation was removed. | No source file found under the local research and literature-store search roots. |

No citation was added solely to lengthen the reference list. The revision adds
zero new bibliography keys and completes one previously unresolved metadata
entry. The manuscript retains the existing Chikkamath and Poce WPI citations;
both are supported by the local readable sources listed above.

## Word count

Counts use MiKTeX `texcount -inc -sum` on the manuscript source. The first line
is the full texcount sum; the second is texcount's body-text count (excluding
headers and captions).

| Version | Full sum | Body text | Change |
|---|---:|---:|---:|
| `journal_08/main.tex` before this audit | 5,363 | 4,750 | baseline |
| `journal_09/main.tex` | 5,315 | 4,702 | -48 full / -48 body |

The reduction comes from removing the unresolved Rees–Wirz and Krestel prose
references; no result, figure, table, section structure, or experimental number
was changed. The body remains below the 6,000-word journal ceiling.

## Build and integrity target

`journal_09/main.tex` is built with the local `elsarticle.cls` and bibliography
style. The final three-pass build produced a 20-page `main.pdf` with zero
undefined citations or references. The log contains one 2.43pt output-box
overflow and several underfull boxes from long monospace/model strings; no
overflow exceeds 5pt. Figure inputs were unchanged, and representative
rendered pages were checked for clipping, overlap, and legibility.
