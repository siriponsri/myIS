# Patent Structure Design for DAPFAM

## 1. Decision

Use a **typed evidence graph with a hierarchical containment spine**, not a pure tree and not a page tree.

The graph must be:

- family-level;
- grounded in original DAPFAM text fields;
- deterministic after the representation specification and compiler are fixed;
- tolerant of irregular claim and description formatting;
- compact enough to compile into at most four searchable units per family;
- explicit about uncertainty and fallback behavior.

This document explains why that design fits both patent structure and the actual DAPFAM files.

## 2. What patent documents suggest

### 2.1 Document components

WIPO describes patent applications as broadly sharing a front page, specification/description, claims, drawings, and abstract. WIPO ST.96 provides standardized XML components and hierarchical document structures for industrial-property data.

This supports a top-level containment spine:

```text
patent_record
├── metadata
├── title
├── abstract
├── claims
├── description
└── drawings_if_available
```

DAPFAM has no drawing content and does not expose the source XML hierarchy, so those parts cannot simply be reconstructed from ST.96.

Sources:

- [WIPO overview of patent-document structure](https://www.wipo.int/en/web/wipo-magazine/articles/ip-and-business-patent-information-buried-treasure-34655)
- [WIPO ST.96 version 10.0](https://www.wipo.int/standards/en/st96/v10-0/)
- [WIPO ST.96 Annex III design rules](https://www.wipo.int/en/web/cws/taskforce/xml4ip/st96/cws2/st96-annex-iii)

### 2.2 Claims are not a strict tree

EPO guidance distinguishes independent claims, which state essential features, from dependent claims, which incorporate another claim and add limitations. A dependent claim may refer to multiple preceding claims. Consequently, the claim set can contain shared ancestry and multiple parent references.

Patent Claim Structure Recognition reaches the same modeling conclusion: a claim set has hierarchical organization, but its complete dependency structure is more accurately represented as a directed graph because one claim can belong to multiple groups.

Adopt:

```text
claims
└── claim_group
    └── claim
        └── limitation
```

Add graph edges:

```text
depends_on
narrows
```

Do not force every claim into a single-parent tree.

Sources:

- [EPO Guidelines: independent and dependent claims](https://www.epo.org/en/legal/guidelines-epc/2026/f_iv_3_4.html)
- [Patent Claim Structure Recognition](https://publikationen.bibliothek.kit.edu/1000069936/4168126)

### 2.3 Claim limitations are useful retrieval units

FiNE-Patents decomposes first claims into fine-grained features and links those features to prior-art passages. Its reported data contain an average of `6.2 ± 2.4` features per claim. This supports representing limitations below the claim level when the segmentation is grounded and reproducible.

It does not justify asking an LLM to paraphrase every DAPFAM claim. The useful transfer is the feature-level retrieval unit and evidence linkage, not uncontrolled corpus-wide generation.

Source:

- [FiNE-Patents](https://arxiv.org/abs/2605.02392)

### 2.4 PageIndex is useful as a schema seed, not a direct DAPFAM solution

PageIndex represents long documents with nodes such as:

- `title`
- `node_id`
- page start and end indices
- `summary`
- nested child nodes

That is useful inspiration for stable node IDs, containment, ranges, and traversal. DAPFAM provides flattened text fields rather than page images or page numbers, so SCOPE must use character offsets and source-field hashes instead of page indices.

PageIndex summaries are disabled by default because an abstractive summary may introduce ungrounded retrieval terms. Any later summary experiment must be separately labeled and trace every indexed statement to source spans.

Source:

- [PageIndex repository and tree schema](https://github.com/VectifyAI/PageIndex)

### 2.5 AutoIndex makes representation learnable

AutoIndex holds retrieval and evaluation fixed while agents propose executable document-to-chunk transformations. Its primary experiments use BM25, MaxP-style document aggregation, and iterative analysis/code agents. The paper reports improvement across eight CRUMB tasks and describes a preliminary dense-retrieval pilot, while leaving broad dense, hybrid, and reranking validation open.

The relevant design lessons are:

- optimize the representation, not one handcrafted tree;
- keep retrieval and evaluation fixed while testing representation;
- retain source document identity;
- limit index expansion;
- use a modest number of chunks per document, commonly one to four in the authors' guidance;
- test dense/hybrid transfer only after sparse leverage is established.

SCOPE preserves this AutoIndex agent loop but constrains its output to a patent-native DSL rather than unrestricted generated preprocessing code. It adds provenance, parser confidence, claim-graph constraints, family aggregation, protected split roles, and an independent read-only Auditor.

Sources:

- [AutoIndex paper](https://arxiv.org/abs/2607.18603)
- [AutoIndex implementation](https://github.com/auto-index/autoindex)
- [AutoIndex project page](https://auto-index.github.io/)

### 2.6 SCOPE-DSL is the AutoIndex candidate surface

The Analysis Agent and Structure Agent remain the core optimizer. The Structure Agent writes a declarative specification that selects only allowlisted parsing, graph, view, and aggregation operations. A frozen deterministic compiler executes that specification.

This choice:

- preserves AutoIndex's learned-representation premise;
- prevents arbitrary candidate code from reaching the evaluator or protected data;
- makes the search space enumerable for equal-budget random and grid controls;
- makes candidate differences compact enough for the Auditor to review;
- allows one frozen representation specification to be tested on DAPFAM and FiNE-Patents.

The DSL is scientifically useful only if patent-specific operations and external transfer explain results. It must not be presented as novelty merely because it uses JSON.

## 3. What DAPFAM actually contains

### 3.1 Benchmark unit

DAPFAM is a family-level benchmark with:

- 45,336 target patent families;
- 1,247 query families;
- 49,869 relevance judgments;
- English text;
- `ALL`, `IN`, and `OUT` evaluation scopes.

The paper states that family consolidation retains the most recent version for textual fields while metadata such as earliest claim date and jurisdiction use the earliest family information. Therefore, a row is a consolidated family record, not necessarily a coherent publication record.

Consequences:

- `family_id` is the canonical document identity;
- do not invent `publication_id`;
- do not claim that title, claims, and description came from one publication;
- preserve the source-field identity for every span;
- aggregate retrieval units back to families before evaluation.

Sources:

- [DAPFAM dataset card](https://huggingface.co/datasets/datalyes/DAPFAM_patent)
- [DAPFAM paper](https://arxiv.org/abs/2506.22141)
- [DAPFAM paper HTML](https://arxiv.org/html/2506.22141v2)

### 3.2 Actual Parquet fields

The public corpus schema exposes:

```text
relevant_id
earliest_claim_jusrisdiction
jurisdiction
ipcr_codes_str
earliest_claim_date
earliest_claim_year
classifications_ipcr_list_first_three_chars_list
title_en
abstract_en
claims_text
description_en
```

The public query file adds:

```text
query_id
abstract_keywords
```

The spelling `earliest_claim_jusrisdiction` is present in the actual Parquet schema. Ingestion may expose a canonical internal alias, but the original field name must remain in the source manifest.

Sources:

- [DAPFAM file tree](https://huggingface.co/datasets/datalyes/DAPFAM_patent/tree/main)
- [DAPFAM queries Parquet](https://huggingface.co/datasets/datalyes/DAPFAM_patent/blob/main/queries.parquet)

### 3.3 Direct query-file inspection

The public `queries.parquet` file was inspected locally on 2026-07-30 without opening qrels.

Bound file:

```text
rows: 1,247
size: 62,667,355 bytes
sha256: b5ad91a650349a0096911fadcb7bc35a0399eb12d1470fb2601d73af5fc2bcbe
query_id uniqueness: 100%
null rows in inspected columns: 0
```

Text-length distribution in characters:

| Field | Median | 95th percentile | Maximum |
|---|---:|---:|---:|
| `title_en` | 53 | — | 312 |
| `abstract_en` | 714 | — | 3,138 |
| `claims_text` | 5,910 | 19,802 | 114,709 |
| `description_en` | 65,685 | 370,248 | 3,147,889 |

The very long descriptions make full-record dense encoding and unrestricted node indexing expensive. A compact view compiler is necessary.

### 3.4 Claims are flattened and irregular

Observed on all 1,247 public query rows:

| Observation | Share |
|---|---:|
| Starts with a numeric claim marker | 71.05% |
| Contains a form similar to `claims 1` | 1.68% |
| Contains a form similar to `what is claimed` | 3.53% |
| Contains at least one dependent-claim reference | 91.50% |
| Contains a multiple-reference pattern | 84.68% |
| Contains a literal newline followed by `2.` | 0.00% |

A simple sequential claim-marker parser found:

| Parsed outcome | Share |
|---|---:|
| At least one claim | 78.51% |
| At least two claims | 76.82% |
| At least five claims | 73.86% |
| At least ten claims | 65.28% |

Failure patterns include:

- letter-spaced headings such as `c l a i m s`;
- cancelled claim ranges before the first active claim;
- inconsistent punctuation and spacing;
- unnumbered claim text;
- flattened text without reliable line boundaries.

Therefore, claim parsing must be multi-strategy, confidence-scored, and reversible. It must never silently drop an unparsed tail.

### 3.5 Description headings are useful but unreliable

Heading-like strings observed in the public query descriptions:

| Heading family | Share |
|---|---:|
| background | 93.10% |
| summary | 85.40% |
| detailed description | 84.44% |
| brief description of drawings | 73.94% |
| field | 65.76% |

Only 63.62% of records containing field, background, summary, and detailed-description headings placed them in the canonical order tested. Bracketed paragraph numbers such as `[0001]` occurred in only 6.34% of rows.

Therefore:

- heading matches require boundary and order checks;
- section nodes carry confidence;
- irregular records use deterministic windows;
- bare four-digit numbers are not paragraph markers by default.

### 3.6 DAPFAM already contains a strong passage baseline

The current dataset card registers 18 MTEB tasks across:

- `ALL`, `IN`, and `OUT`;
- title-plus-abstract or title-plus-abstract-plus-claims query views;
- title-plus-abstract, title-plus-abstract-plus-claims, or full-text target views.

`TAC -> FullText`, the initial SCOPE view, is therefore a registered DAPFAM task even though it is not one of the six configurations marked as directly evaluated in the original paper.

The DAPFAM paper also evaluates deterministic passage windows from 64 to 8,192 tokens with `maxP`, `avgP`, `avg_top3`, and `sumP` family aggregation. For BM25, its reported best `ALL` nDCG@100 passage setting uses `p=4096` with `maxP`; its best `ALL` Recall@100 setting uses `p=8192` with `maxP`. This is a materially stronger comparator than a single full-family document.

Consequences for SCOPE:

- retain the flat family baseline;
- add a deterministic-window control selected on train under a declared evaluation budget;
- keep family aggregation explicit and identical where a comparison requires it;
- report index growth and latency because passage retrieval trades efficiency for effectiveness;
- do not attribute a gain to patent structure if ordinary windowing explains it.

The dataset paper treats nDCG@100 as primary and Recall@100 as secondary. SCOPE may optimize `OUT Recall@100` because its causal target is candidate exposure, but the paper must report nDCG@100 prominently and explain this deliberate objective change.

Sources:

- [DAPFAM dataset card and MTEB task registry](https://huggingface.co/datasets/datalyes/DAPFAM_patent)
- [DAPFAM passage and aggregation study](https://arxiv.org/html/2506.22141v2)

## 4. DAPFAM-to-representation mapping

| DAPFAM field | Representation node | Default indexed use | Important limitation |
|---|---|---|---|
| `relevant_id` | `patent_record` identity | family aggregation only | Family, not publication |
| `title_en` | `title` | `core` | Short but high signal |
| `abstract_en` | `abstract` | `core` | Consolidated family text |
| `claims_text` | `claims`, `claim`, `limitation`, fallback block | `claims`, sometimes `core` | Flattened and irregular |
| `description_en` | `description`, `section`, `passage`, fallback windows | `support` | Can exceed three million characters |
| `ipcr_codes_str` | metadata | filtering/diagnostics only unless protocol allows | Must not leak relevance labels |
| IPC three-character list | metadata | `IN`/`OUT` evaluator only | Protected from candidate logic |
| earliest claim fields | metadata | reporting/filters if frozen | Mixed family-level semantics |
| `abstract_keywords` | query metadata | query diagnostics only | Not a corpus node |

Candidate representation specifications must not use IPC overlap or `IN`/`OUT` scope as an input feature. Those fields define evaluation strata and would leak the benchmark partition.

### 4.1 Cross-dataset identity

The compiler operates on a canonical patent record, while each benchmark adapter retains its native answer unit:

| Benchmark | Native answer unit | Representation use | Tuning role |
|---|---|---|---|
| DAPFAM | Patent family | Compile one to four family views and aggregate unit scores to `family_id` | Structure search, selection, final |
| FiNE-Patents | Cited prior-art passage | Compile grounded passage candidates inside each cited document and return native passage IDs | Zero-retuning external confirmation |
| PatenTEB | Task-specific document or pair | Map native fields to frozen views only where semantics are valid | Stretch transfer only |

Dataset adapters may translate field names and native identities. They may not silently alter the learned representation, inject labels, or redefine an official evaluator.

## 5. Adopted evidence graph

### 5.1 Containment spine

```text
patent_record
├── metadata
├── title
├── abstract
├── claims
│   ├── claim_group
│   │   └── claim
│   │       └── limitation
│   └── claim_block_unparsed
└── description
    ├── section
    │   └── passage
    └── description_block_unparsed
```

### 5.2 Edge types

| Edge | Meaning |
|---|---|
| `contains` | Hierarchical source containment |
| `depends_on` | A claim references another claim |
| `narrows` | A dependent claim adds limitations to an ancestor |
| `supported_by` | A claim or limitation maps to a grounded description span |
| `derived_from` | A node or searchable unit is constructed from source nodes |

`supported_by` is optional until a reliable grounded matcher exists. Do not infer it merely from semantic similarity and present it as legal support.

### 5.3 Required provenance

Every non-metadata textual node records:

```text
source_field
source_start
source_end
source_hash
parser_strategy
parser_confidence
fallback_used
```

Semantic validation must confirm:

- offsets are inside the source field;
- the sliced source text hashes to the recorded value;
- child spans do not claim to exceed parent spans;
- every searchable unit resolves to source nodes;
- no primary indexed text is ungrounded.

## 6. Parser design

### 6.1 Claim parser

Use an ordered strategy set:

1. normalize Unicode and whitespace while retaining an offset map;
2. detect claim preambles and cancelled ranges;
3. detect sequential numeric markers with punctuation variants;
4. validate monotonic numbering and plausible span lengths;
5. parse dependency references into a directed graph;
6. identify independent, dependent, or unknown claim kind;
7. segment limitations with deterministic syntax rules;
8. calculate confidence from marker consistency, coverage, and graph validity;
9. emit the structured graph above the configured confidence threshold;
10. otherwise emit one or more grounded `claim_block_unparsed` nodes.

The optimizer may choose among allowlisted strategies or thresholds. It may not discard text to improve a score.

### 6.2 Description parser

Use:

1. normalized text with offset preservation;
2. anchored heading patterns;
3. heading-order and minimum-span validation;
4. optional bracketed-paragraph segmentation where coverage is credible;
5. deterministic token or character windows for remaining text;
6. explicit confidence and fallback status.

Do not require a complete canonical section order.

### 6.3 Limitation parser

Begin with deterministic segmentation around:

- semicolon-delimited elements;
- enumerated subclauses;
- transitional phrases;
- relative/dependency clauses;
- component-function and process-step boundaries.

Keep the original text unchanged. A limitation is an evidence span, not an LLM-authored legal interpretation.

## 7. Searchable view compiler

Do not index every graph node independently. Compile one to four units per family:

| View | Contents | Default |
|---|---|---|
| `core` | title + abstract + bounded claim context | On |
| `claims` | grounded claim paths and limitations | Candidate-controlled |
| `mechanism` | exact source spans grouped by component, function, process, or relation rules | Candidate-controlled |
| `support` | selected grounded description sections or windows | Candidate-controlled |
| `fallback` | grounded unparsed blocks | Used when required |

A fallback may replace another view but may not increase the total above four.

Default text origin:

- exact source concatenation;
- extractive span grouping;
- deterministic labels from a fixed vocabulary.

Abstractive text is disabled in `R0` and `R1`. If studied later, it becomes a separate arm with term-level grounding and explicit hallucination diagnostics.

## 8. StructureOpt search space

### Optimizable

- claim-boundary strategy;
- parser confidence threshold;
- enabled node and view types;
- claim-path depth;
- limitation segmentation strategy;
- description heading strategy;
- window size and overlap;
- path-label serialization;
- exact field repetition;
- maximum text per view;
- unit-to-family aggregation from a fixed allowlist.

### Immutable

- family IDs and source text;
- source offsets and hashes;
- split and qrels;
- `IN`/`OUT` labels;
- query and corpus population;
- evaluator and metric definitions;
- model/retriever settings for the representation comparison;
- maximum four units per family;
- cost accounting;
- candidate-specification boundary and frozen compiler.

## 9. Why there is no human-tree arm

A manually optimized tree would:

- delay the measured campaign;
- make the Owner responsible for low-level structural choices;
- create another high-effort baseline that is not the central claim;
- blur whether the contribution is the human schema or the learned specification.

Instead:

- patent standards define permitted top-level concepts;
- EPO and claim-structure research require graph-capable claim dependencies;
- PageIndex contributes range-based node ideas;
- actual DAPFAM formatting determines parser fallbacks;
- AutoIndex-style search chooses the compact representation inside that envelope.

The mandatory experiment is therefore:

```text
R0: flat grounded representation + frozen BM25
R1: learned grounded representation + the same frozen BM25
```

This directly tests the proposed contribution.

## 10. Risks and required diagnostics

| Risk | Diagnostic | Safe response |
|---|---|---|
| Over-segmentation dilutes scores | units/family, score distributions | prefer compact candidate |
| Long descriptions dominate | field contribution and ablation | cap support view |
| Claim parser fails by jurisdiction/style | coverage by pattern and jurisdiction | fallback blocks |
| Agent learns train terminology | lexical overlap and held-out selection | reject or report |
| Grounded concatenation duplicates terms | token repetition report | cap repetition |
| BM25 gain does not transfer | frozen dense/hybrid test | report sparse-specific result |
| Family record is mistaken for publication | provenance audit | use family-only language |
| Index growth explains gain | budget-matched unit and storage report | Pareto analysis |
| Summary hallucinates | text-origin audit | keep summaries off |

## 11. Reproducibility checklist

- bind exact Hugging Face revision and file hashes;
- retain the original misspelled source field name in the manifest;
- publish parser strategy, confidence formula, and fallback rules;
- publish the representation specification, `schemas/scope-dsl.schema.json`, and deterministic compiler;
- report parser coverage on train, selection, and final without using protected feedback for tuning;
- report searchable-unit count and index size;
- freeze family aggregation and evaluator;
- retain per-query results;
- disclose model, prompts, reasoning effort, candidate budget, and cost;
- keep final split closed until the freeze package passes audit.

## 12. Source index

1. [DAPFAM dataset](https://huggingface.co/datasets/datalyes/DAPFAM_patent)
2. [DAPFAM paper](https://arxiv.org/abs/2506.22141)
3. [DAPFAM paper HTML](https://arxiv.org/html/2506.22141v2)
4. [EPO independent and dependent claims](https://www.epo.org/en/legal/guidelines-epc/2026/f_iv_3_4.html)
5. [WIPO patent-document overview](https://www.wipo.int/en/web/wipo-magazine/articles/ip-and-business-patent-information-buried-treasure-34655)
6. [WIPO ST.96](https://www.wipo.int/standards/en/st96/v10-0/)
7. [Patent Claim Structure Recognition](https://publikationen.bibliothek.kit.edu/1000069936/4168126)
8. [FiNE-Patents](https://arxiv.org/abs/2605.02392)
9. [PageIndex](https://github.com/VectifyAI/PageIndex)
10. [AutoIndex paper](https://arxiv.org/abs/2607.18603)
11. [AutoIndex implementation](https://github.com/auto-index/autoindex)
