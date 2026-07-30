# iSAI-NLP 2026 Submission Plan

## 1. Venue snapshot

This document records the public submission requirements inspected on `2026-07-30`. Recheck the official site immediately before submission because conference instructions can change.

| Item | Working contract |
|---|---|
| Venue | The 21st International Joint Symposium on Artificial Intelligence and Natural Language Processing |
| Recommended track | Track 1 — Natural Language Processing |
| Paper deadline | `2026-08-15` |
| Notification | `2026-09-15` |
| Camera-ready deadline | `2026-09-30` |
| Conference | `2026-11-19` through `2026-11-21`, Bangkok, Thailand |
| Format | Official IEEE conference manuscript format |
| Length | Maximum six pages, conservatively treating figures, tables, appendices, and references as inside the limit |
| Review | Double anonymous |
| Submission | PDF through EasyChair |
| Attendance | In person; at least one author must register and present an accepted paper |
| Publication | Accepted and presented papers are planned for IEEE Xplore |

Authoring constraints:

- omit author names, affiliations, acknowledgements, and author-revealing URLs from the review PDF;
- cite the authors' prior work in the third person;
- do not identify an anonymous repository or institution in supplemental prose;
- use a different title for any public preprint during review;
- do not submit substantially the same work concurrently elsewhere;
- finalize the author list before review because adding authors later is restricted;
- prepare at least three EasyChair keywords, one per line;
- use plain text for EasyChair title and abstract fields;
- identify the corresponding author in the submission form.

Official sources: [conference home](https://isai-nlp2026.aiat.or.th/) and [submission instructions](https://isai-nlp2026.aiat.or.th/submission).

The EasyChair metadata details were also checked against the user-supplied `easychair.pdf` snapshot. Treat that PDF as dated evidence and recheck the live form before `D3`.

## 2. Outstanding-oriented positioning

The public site does not publish a separate “outstanding paper” rubric. The project therefore optimizes for the qualities that make a short conference paper stand out without claiming or promising an award:

1. one memorable problem;
2. one technically distinct method;
3. a fair causal comparison;
4. an independent transfer result;
5. evidence explaining why the method works;
6. a small, reproducible, inspectable artifact.

The one-sentence paper:

> SCOPE turns patent representation from fixed preprocessing into a grounded AutoIndex-style optimization target, then tests whether the learned compiler exposes cross-domain prior art and transfers to fine-grained evidence retrieval.

Recommended anonymous title:

> **SCOPE: Learning Grounded Evidence Compilers for Cross-Domain Patent Retrieval**

Do not put `AutoIndex`, `GPT-5.6`, `SkillOpt`, or an organization name in the title. AutoIndex should be prominent in the method lineage and comparison, while the contribution remains SCOPE.

## 3. Six-page scientific core

The iSAI-NLP paper is intentionally sharper than the full research program.

### Required

1. DAPFAM flat BM25 baseline under the frozen family-level protocol.
2. Train-selected deterministic-window BM25 control with fixed `maxP`.
3. Patent-native AutoIndex loop using Analysis and Structure Agents.
4. Constrained SCOPE-DSL candidates compiled by a frozen deterministic compiler.
5. Same-BM25 comparison of `R0` flat, `R0-W` windows, and `R1` learned representation.
6. Equal-budget random or enumerated search control.
7. Protected train, selection, and once-only final evaluation.
8. Zero-retuning transfer to FiNE-Patents with its official evidence-retrieval evaluator.
9. Three mechanism ablations selected before final evaluation.
10. Grounding, parser coverage, index size, latency, and cost.
11. Independent read-only Auditor and complete run manifests.

### Stretch only after the required package is safe

- one matched dense or hybrid transfer pair;
- selected PatenTEB retrieval tasks;
- multiple optimizer seeds beyond the minimum;
- SkillOpt or the full representation-by-policy factorial;
- an Auditor performance ablation.

PatenTEB and SkillOpt can strengthen an extended version, but neither may delay the DAPFAM-plus-FiNE submission core.

## 4. Claims the paper may make

Subject to measured results, the paper may claim:

- SCOPE is a patent-native constrained adaptation of representation optimization;
- it learns a compact grounded representation while the retriever and evaluator remain fixed;
- it improves, preserves, or fails to improve DAPFAM cross-domain candidate exposure by a reported amount;
- a frozen representation does or does not transfer to FiNE-Patents;
- ablations identify which structural decisions explain the measured effect;
- the method has explicit index-size, latency, cost, and grounding trade-offs.

The paper must not claim:

- a legal novelty determination;
- publication-level provenance not present in DAPFAM;
- universal patent-retrieval superiority;
- direct SOTA from incomparable published protocols;
- that the Auditor or GPT-5.6 model is the algorithmic contribution;
- that a positive result is caused by “better reasoning” without a controlled comparison.

## 5. Main visual and tables

Use only high-density assets.

### Figure 1 — Method

Show:

```text
train diagnostics
→ Analysis Agent
→ Structure Agent
→ SCOPE-DSL
→ frozen compiler
→ compact index
→ deterministic evaluator
→ read-only Auditor for eligible incumbents
```

The figure should also show the protected selection/final boundary.

### Table 1 — Main evidence

One table should contain:

- DAPFAM `ALL`, `IN`, and `OUT` Recall@100;
- DAPFAM-primary nDCG@100 as a prominent confirmatory endpoint;
- FiNE-Patents official feature- and claim-level measures;
- units per record, index bytes, and p95 latency where space permits.

### Table 2 or compact Pareto plot — Mechanism

Include:

- random/enumerated control;
- three structural ablations;
- grounding and fallback rates;
- index-growth or cost trade-off.

Do not spend paper space on dashboard screenshots, a full repository tree, agent transcripts, or every failed candidate.

## 6. Page budget

| Section | Pages |
|---|---:|
| Introduction and contributions | 1.00 |
| Related work | 0.45 |
| Method | 1.25 |
| Experimental protocol | 0.75 |
| Results and mechanism | 1.35 |
| Limitations and conclusion | 0.45 |
| References | 0.75 |
| **Total** | **6.00** |

This budget is a drafting control, not a formatting workaround. Do not reduce fonts, spacing, margins, or figure legibility to fit.

## 7. Experiment priority

Use this order when time, compute, or implementation risk competes:

1. protocol-correct DAPFAM `R0`;
2. deterministic compiler and DSL;
3. one complete AutoIndex-style pilot;
4. equal-budget simple-search control;
5. frozen selection;
6. FiNE-Patents transfer;
7. three ablations and efficiency diagnostics;
8. final freeze and final evaluation;
9. anonymous six-page manuscript;
10. dense/hybrid, PatenTEB, or SkillOpt stretch work.

Broad repository cleanup must not block this vertical slice. Preserve legacy evidence, but defer unrelated migration work until the submission-critical path runs.

## 8. Working calendar

The public deadline gives a short implementation window from the snapshot date. The Owner did not limit creative depth, but the submission artifact still has a fixed deadline.

| Date, Asia/Bangkok | Agent-owned outcome |
|---|---|
| Jul 30–31 | Freeze thesis, venue contract, novelty matrix, minimum vertical slice |
| Aug 1–3 | Reproduce `R0`; validate compiler, DSL, evaluator, and manifests |
| Aug 4–7 | Run bounded AutoIndex pilot and equal-budget control under `D1` |
| Aug 8 | Freeze shortlist and run selection once |
| Aug 9–10 | FiNE transfer, ablations, efficiency and grounding analysis |
| Aug 10–11 | Prepare freeze audit; request `D2` only when complete |
| Aug 11–12 | Run final once and populate paper tables |
| Aug 12–13 | Write and format anonymous manuscript |
| Aug 13–14 | Independent compliance and reproducibility audit |
| Aug 14, 18:00 | Internal submission target |
| Aug 15 | Official deadline; use only for controlled contingency |

The official page does not state a timezone in the inspected instructions. The internal target avoids making the Owner resolve that ambiguity at the last minute.

## 9. Owner burden

The Owner receives at most three decision packets:

| Decision | Packet contents |
|---|---|
| `D1 START_CAMPAIGN` | One bounded cost/provider/data/egress envelope and automatic stop rules |
| `D2 OPEN_FINAL` | Freeze hashes, Auditor verdict, selection result, contamination check |
| `D3 RELEASE` | Anonymous PDF, author metadata sheet, compliance checklist, artifact status |

Agents own routine choices, failed-candidate handling, formatting, parser fallbacks, report generation, and resubmission of internal drafts.

## 10. Submission checklist

### Scientific freeze

- final system and all baselines were frozen before final qrels were opened;
- reported numbers resolve to validated run manifests and MLflow records;
- every table value is generated from canonical metric exports;
- all negative results and deviations are retained;
- external dataset licenses and revisions are recorded.

### Anonymous PDF

- six pages or fewer under the official IEEE template;
- no names, affiliations, acknowledgements, self-identifying URLs, or hidden PDF metadata;
- third-person self-citations;
- figures and tables readable at 100% zoom;
- references complete and within the page limit;
- no unsupported “SOTA,” legal, or causality language.

### EasyChair

- title and abstract copied as plain text;
- at least three keywords, one per line;
- all authors entered in the intended order;
- corresponding author selected;
- uploaded PDF opens and matches the frozen checksum;
- no concurrent submission conflict.

### Presentation contingency

- at least one author can register and present in Bangkok;
- presentation deck is generated from the same canonical records;
- public artifact links are added only after `D3` and venue-policy review.

## 11. Recommended keywords

- patent retrieval
- representation optimization
- cross-domain information retrieval
- evidence grounding
- agentic document indexing

## 12. Camera-ready preparation

Keep an author-visible camera-ready branch separate from the anonymous review package. Do not merge identifying metadata into the review PDF.

After acceptance:

- apply the venue's camera-ready instructions;
- restore names, affiliations, acknowledgements, and approved artifact links;
- obtain chair approval before changing title or author list;
- verify IEEE PDF compliance;
- register and confirm the in-person presenter;
- regenerate the presentation from frozen results.
