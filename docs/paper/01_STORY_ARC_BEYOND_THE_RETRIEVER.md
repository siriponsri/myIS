# Story Arc — Beyond the Retriever

## Core question
**When we compare retrievers, are we really comparing the retrievers—or the retriever–representation configurations they consume?**

The paper should not argue that representation “matters” in the generic sense. That is already known. The stronger and more defensible story is that representation should not automatically be treated as model-independent neutral preprocessing when interpreting retriever comparisons.

## Arc 1 — The comfortable assumption
Retrieval benchmarks often hold document representation fixed and compare retrievers. This appears fair: same benchmark, same metrics, same text construction, different retrieval models.

Patent documents complicate that assumption. The same invention can be presented as title+abstract, claims, an independent claim, overlapping passages, or section-specific views. A retriever never scores an invention in the abstract; it scores a constructed view of it.

**Narrative hook:**
> Does fixing one representation for every retriever necessarily make the comparison model-independent?

**Figure role:** A simple conceptual figure: one patent family → several possible representations → heterogeneous retrievers. Avoid equations.

## Arc 2 — Change the view, freeze the retriever
Use A1-A2 as controlled evidence, not as a winner leaderboard. Five frozen systems are exposed to shared/deterministic representation changes while weights and core adapter behavior remain fixed.

The important result is mixed response rather than universal improvement: one strict improvement, a within-search winner/tie, a no-strict-improvement case, and diagnostic ties.

**Scientific claim:**
> Frozen retrievers did not respond uniformly to the same representation changes.

**Data-story role:** Show heterogeneity visually. Do not imply that one representation improves every retriever.

## Arc 3 — Best representation, for whom?
A skeptical reader can still ask whether there is one generally good representation. A3 answers this with cross-retriever transfer.

The 3×3 transfer matrix does not show a stable universal source/diagonal advantage. The highest Recall@100 cell occurs when a Qwen3-derived representation is consumed by PatEmbed; the highest nDCG@100 cell occurs when an Arctic-derived representation is consumed by PatEmbed.

**Hero question:**
> Best representation — for whom?

**Scientific claim:**
> Representation advantages did not transfer consistently across retrievers on development data.

**Do not claim:** every retriever requires a unique representation.

## Arc 4 — The mental-model shift
At this point the paper asks the reader to reinterpret the unit of comparison:

> The retriever is only part of the retrieval configuration; its observed performance depends on the representation it consumes.

This is a conceptual interpretation of A1-A3, not a universal causal law.

## Arc 5 — Development stories are easy. Does the selected system survive?
Explicitly downgrade the preceding results before the reviewer does:

> Everything above is development evidence.

Use the one-time Selection-125 only as a bridge. Freeze the selected research configuration and comparator. Then open A5 Final-872.

**Scientific climax:**
- Recall@100: 0.331097 → 0.442476
- paired difference: +0.111379
- 95% bootstrap CI: [0.102294, 0.120438]
- wins/ties/losses: 619 / 158 / 95
- nDCG@100 difference: +0.086342
- 95% CI: [0.078673, 0.094077]

**Climax sentence:**
> The selected complete configuration survived held-out confirmation.

Immediately add the guardrail: this is a comparison of complete frozen systems and does not isolate representation as the sole cause.

## Arc 6 — Confirmation is not the end: scale the frozen system
A6 should be a bridge, not a second climax. Apply the A5-frozen winner unchanged to the complete benchmark:
- 45,336 candidate families
- 1,247 queries
- depth 200
- 249,400 ranked rows
- 100% coverage
- 0 failures

Narrative function:
> We confirmed it. Then we scaled the unchanged system to create a stable full-benchmark evidence pool.

Do not compare A5’s 0.442476 directly with A6 strict cross-domain Recall@100=0.188450; the populations differ.

## Arc 7 — What does even the confirmed system still fail to retrieve?
Now interrogate the immutable A6 Top-200 pool with A7.

Strict cross-domain relevant family pairs: 5,193
- found at ranks 1-100: 796
- found only at ranks 101-200: 332
- absent from Top-200: **4,065**

Among 905 judged cross-domain queries, 455 have no relevant candidate in Top-200.

The analytical perfect-ordering bound within the existing Top-200 pool raises Recall@100 only from 0.188450 to 0.260167 (+0.071717). This is not a reranker result.

**Aftershock sentence:**
> A ranker cannot recover evidence that retrieval never supplies.

## Arc 8 — Close where the paper started
The opening asks what evidence the retriever is allowed to see. The ending asks what evidence a downstream ranker ever gets the chance to see.

**Resolution:**
> Cross-domain retrieval depends not only on the model that scores evidence, but also on how that evidence is represented and whether relevant evidence enters the candidate pool at all.

A slightly sharper final line may be used if tone remains academic:
> Better retrieval begins not only with how evidence is ranked, but with what evidence the system is allowed to see.

## Evidence hierarchy to preserve
1. **A1-A3 — Development finding:** heterogeneous representation behavior and inconsistent transfer advantage.
2. **A5 — Confirmatory finding:** the selected complete configuration outperformed the frozen comparator on Final-872.
3. **A6-A7 — Post-confirmatory characterization/diagnosis:** the frozen winner scaled to the full benchmark, where candidate exposure remained a major constraint.

## Suggested figure-led narrative
- **Fig. 1 — What the Retriever Actually Sees:** patent family → alternative representations → frozen retrievers.
- **Fig. 2 — Best for Whom?:** A3 transfer matrix/heatmap as the conceptual hero figure.
- **Fig. 3 — Held-Out Confirmation:** compact paired/CI visualization for A5.
- **Fig. 4 — What Never Reached the Ranker:** 796 / 332 / 4,065 candidate-exposure anatomy, optionally with the perfect-ordering bound.

For six pages, prefer 3 strong figures rather than 4 if layout becomes crowded; combine protocol/scale annotations into Fig. 1 or Fig. 3.
