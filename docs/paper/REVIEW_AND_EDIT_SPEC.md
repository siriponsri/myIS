# EDIT_INSTRUCTIONS.md — "Beyond the Retriever" (iSAI-NLP 2026) revision spec

Target: move this paper from *weak/borderline* to *strong accept*.
Executor: a local coding agent with access to the paper source (LaTeX / IEEEtran) and the retrieval repo (`siriponsri/myIS`).

This file is written in English on purpose: it contains drop-in LaTeX and must be parsed unambiguously by the agent and compiled into the paper. Author-facing discussion happens in chat, in Thai.

Assumed source = LaTeX (`main.tex`, IEEEtran, two-column). If the source is actually `.docx`, translate every "drop-in LaTeX" block into the equivalent edit and keep all other rules identical.

---

## 0. HARD RULES — read before touching anything

These are non-negotiable. This paper's entire value proposition is preregistration + protected evaluation. One careless number change destroys that credibility. Treat integrity as more important than any wording improvement.

1. **Numbers are immutable.** You may change how a number is *displayed* (decimal places) and you may *add* new numbers that come from the STEP 1 statistics script. You may **never** change, "improve", recompute-away, or round-then-alter any existing reported result. If a computation contradicts a published number, STOP and write a `TODO(human)` — do not silently overwrite.
2. **Only STEP 1 may produce new numbers.** Every new number in the paper must be traceable to `analysis/transfer_stats.py` output (`stats.json`). No number may come from your own estimation or from prose reasoning.
3. **Golden-copy diff protocol.** Before editing, extract every numeric token from the current PDF into `golden_numbers.txt`. After editing, extract again into `new_numbers.txt` and produce `numbers_diff.md` showing every change. Every diff line must be classified as exactly one of: `DISPLAY_ROUNDING` (same value, fewer decimals), `NEW_STAT` (added by STEP 1), or `REMOVED` (deleted with the sentence). Any `VALUE_CHANGED` line is a bug — fix it or stop.
4. **Do not touch retrieval / selection / config code.** No re-selection, no config edits, no new runs beyond the *bounded* per-cell recompute allowed in STEP 0-B (which must reproduce the published cell means before you're allowed to use it).
5. **Never fabricate facts.** Anything you cannot verify from the repo or a real source (the comparator identity, an unresolved citation) becomes a clearly delimited `TODO(human)` block in the text. Do not invent a plausible-sounding methodology sentence.
6. **Keep a changelog.** `CHANGELOG.md`: one line per edit, `[STEP n] <file>:<location> — <what changed> — <why>`.
7. **Build command:** `latexmk -pdf main.tex` (or the repo's existing build). Fix all warnings you introduce; report any pre-existing ones you didn't cause.

Deliverables back to the author (see STEP 12): rebuilt `main.pdf`, `stats.json`, `numbers_diff.md`, `CHANGELOG.md`, and a bulleted list of every `TODO(human)` you inserted.

---

## STEP 0 — DATA GATE (do this first, it decides STEP 1)

The revision's single real analysis is making the transfer claim *inferential* instead of *hedged*. That needs per-query Recall@100 for the 9 transfer cells (3 sources × 3 targets, over the 250 development queries).

### 0-A. Locate saved per-query scores
Search the repo for saved per-query arrays for the transfer matrix. Likely names: `*per_query*`, `*transfer*`, `*3x3*`, `*.parquet`, `*.npy`, `*.jsonl` under `results/`, `eval/`, `dev/`, `outputs/`. You need, for each (source, target) cell, a vector of per-query Recall@100 aligned by query id over the 250 dev queries.

- If found → go to STEP 1, branch FOUND.
- If not found → go to 0-B.

### 0-B. Bounded recompute (only if not saved)
Re-run **only** the 9 transfer cells on the 250 dev queries to dump per-query Recall@100, using the **exact frozen configs already in the repo**. No new config, no selection, no full-benchmark run.

**Integrity gate (mandatory):** after recompute, verify each cell's *mean* Recall@100 reproduces the published Fig-2 value within `1e-4`:

| target \ source | PatEmbed | Arctic | Qwen3 |
|---|---|---|---|
| PatEmbed | 0.418436 | 0.418715 | 0.419274 |
| Arctic   | 0.337430 | 0.341341 | 0.338268 |
| Qwen3    | 0.362570 | 0.359497 | 0.360615 |

If any cell mean does **not** reproduce within `1e-4`, STOP and write `TODO(human): transfer recompute diverged at cell (…): got X, expected Y`. Divergence means the frozen config drifted — the author must resolve it, not you.

Also dump per-query nDCG@10 for the two Final-872 systems (selected, comparator) if not already saved — STEP 1.3 needs it.

---

## STEP 1 — Statistics: make the transfer claim inferential (`analysis/transfer_stats.py`)

Write one script, seed-logged, output to `stats.json`. Use 10,000 paired bootstrap resamples over queries, 95% percentile CIs, matching the method already used for Final-872. Log the RNG seed.

### 1.1 Within-target source differences (the core new evidence)
For each target t ∈ {PatEmbed, Arctic, Qwen3}: rank the 3 sources by mean Recall@100; compute the **paired** difference (best source − second-best source) over the 250 dev queries; bootstrap 95% CI. Report mean diff and CI, and whether the CI contains 0.
Expected outcome (state whatever is actually computed): the CIs contain 0 → within-target reordering is not statistically distinguishable from sampling noise.

### 1.2 Best-source stability
For each target, run 10,000 bootstrap resamples of the 250 queries; in each, record which source is the within-target argmax mean. Report, per target, the bootstrap probability that each source is best. Report `max_argmax_prob` per target. Low/spread-out probabilities → the "nominal best source" is unstable → the cross-target "best source changes" pattern is noise, not a stable ordering.

### 1.3 Fill the missing nDCG@10 CI
The current paper reports the Final-872 nDCG@10 change (0.233666 → 0.297459, diff 0.063794) with **no CI** — an inconsistency reviewers will flag ("why a CI for @100 but not @10?"). Compute the paired bootstrap 95% CI on per-query nDCG@10 (selected − comparator) with the same 10,000 resamples. Output to `stats.json` as `ndcg10_ci`.

### 1.4 (Optional, only if trivial) two-/three-system fusion CI
The composition control (two-system fusion 0.418715 vs single 0.418436; three-system 0.415084) currently rests on differences < 0.0004. If per-query fusion scores exist, add a bootstrap CI so the "adding retrievers doesn't help monotonically" line is inferential too. If the data isn't already saved, skip — do **not** recompute fusion.

`stats.json` schema (fill with real values):
```json
{
  "seed": 0,
  "within_target": {
    "PatEmbed": {"best_minus_second": 0.000, "ci": [0.000, 0.000], "contains_zero": true},
    "Arctic":   {"best_minus_second": 0.000, "ci": [0.000, 0.000], "contains_zero": true},
    "Qwen3":    {"best_minus_second": 0.000, "ci": [0.000, 0.000], "contains_zero": true}
  },
  "argmax_stability": {
    "PatEmbed": {"PatEmbed": 0.00, "Arctic": 0.00, "Qwen3": 0.00, "max_argmax_prob": 0.00},
    "Arctic":   {"...": "..."},
    "Qwen3":    {"...": "..."}
  },
  "ndcg10_ci": {"diff": 0.064, "ci": [0.000, 0.000]}
}
```

---

## STEP 2 — Reframe to one thesis (highest-leverage writing change)

The paper currently reads as three loosely-linked studies. Give it one sentence a reviewer can repeat.

**Thesis (put this in the intro, verbatim or near):**
> In cross-domain patent retrieval, retriever identity dominates representation choice, and first-stage candidate exposure — not within-pool ordering — is the binding constraint on recall.

Everything else is evidence for that one claim: transfer matrix → representation is not the lever; Final-872 → the selected system's advantage is real and system-level; A7 → exposure, not ordering, is what's left.

### 2.1 Drop-in Abstract (replace the current abstract)
Fill `{{...}}` slots from `stats.json` (STEP 1) and the comparator (STEP 3). Numbers are 3-decimal (STEP 5).

```latex
\begin{abstract}
A patent retriever never observes an invention; it scores a constructed
representation of that invention. Benchmark comparisons that hold this
representation fixed treat it as a model-independent control, yet the
representation is part of the evaluated system. On family-level cross-domain
patent retrieval (DAPFAM), we test this assumption by freezing five
heterogeneous retrievers and varying deterministic document constructions,
keeping development, one-time selection, and held-out confirmation as separate
evidence levels. In a $3\times3$ cross-retriever transfer matrix, retriever
identity accounts for essentially all variation in absolute quality:
within-target Recall@100 differences between representation sources are below
{{WITHIN_TARGET_MAX_DIFF}} with 95\% bootstrap intervals that contain zero, so
the nominal change of best source across consumers is not statistically
distinguishable from sampling noise. On 872 held-out queries, a preregistered
configuration improves Recall@100 from 0.331 to 0.442 (paired difference 0.111,
95\% CI [0.102, 0.120]) and nDCG@100 from 0.279 to 0.366 (0.086, [0.079, 0.094])
over a frozen comparator ({{COMPARATOR_ONE_LINE}}). Applying the fixed winner to
the full benchmark exposes the binding constraint: 78.3\% of strict cross-domain
relevant families never enter the Top-200 pool, and perfect within-pool ordering
would raise macro Recall@100 only from 0.188 to 0.260 (headroom 0.072).
Cross-domain patent retrieval is therefore exposure-bound rather than
ordering-bound, and retrieval quality should be reported at the
retriever--representation configuration level.
\end{abstract}
```

### 2.2 Rewrite the transfer-section conclusion (Section IV end) — make it inferential
Replace the paragraph that currently says the ranges are "narrow … descriptive … no cell-level confirmatory inference" with (fill slots):

```latex
Because the transfer cells share the 250 development queries, we test the
within-target source differences directly. For every target retriever, the
paired difference between its best and second-best representation source has a
95\% bootstrap interval that contains zero ({{PATEMBED_DIFF_CI}},
{{ARCTIC_DIFF_CI}}, {{QWEN3_DIFF_CI}}), and no source is a stable within-target
maximum under resampling (bootstrap best-source probability at most
{{MAX_ARGMAX_PROB}}). The apparent change of best source across consuming
retrievers is therefore not distinguishable from sampling noise. In contrast,
the between-target gaps in absolute Recall@100 (roughly 0.34 for Arctic, 0.36
for Qwen3, 0.42 for PatEmbed) are an order of magnitude larger. Representation
choice thus does not reorder retrievers; retriever identity does.
```

This converts the biggest reviewer objection ("you claim a finding you refuse to defend statistically") into a clean, defensible null.

### 2.3 Align intro contribution paragraph and Discussion opening
- Intro: state the thesis (2.0) and list contributions as (i) an inferential transfer null, (ii) protected held-out confirmation of a complete configuration, (iii) an exposure diagnosis showing the binding constraint. Drop language that sells "best source changes across retrievers" as a positive finding.
- Discussion: keep the configuration-level-reporting point, but lead the conclusion with the exposure result, not the transfer curiosity.

---

## STEP 2A — Position against AutoIndex [4] (CRITICAL — scope the central claim; now #1 priority)

AutoIndex (`arXiv:2607.18603`, Jul 2026) is this paper's nearest neighbour, it is already in the reference list, and it argues the **opposite** of the headline: document representation is a large, optimizable lever, not fixed preprocessing. It gets **+8.4% average Recall@100** over static BM25 by searching executable representation programs. A reviewer who knows this paper will read "representation barely moves retrievers; retriever identity dominates" as directly contradicted — unless the claim is scoped precisely. This outranks the comparator as the top acceptance risk.

**The reconciliation (true, defensible — put it in the paper):**
- This paper's representation space is **five coarse, static, field-level constructions**. AutoIndex searches a **rich space of executable, corpus-specific transforms** driven by failure analysis. Different question, different space.
- This paper's transfer matrix runs on **dense** retrievers (PatEmbed/Arctic/Qwen3), which are far more robust to surface representation than the BM25 backend where most of AutoIndex's gains sit.
- So the finding is: *within coarse field-level construction choices, representation does not reorder frozen dense retrievers on DAPFAM.* It is **not** "representation is inert in general."

**The detail you must confront (do not omit):** AutoIndex's preliminary dense result reuses a learned representation on **Qwen3-Embedding-0.6B — the exact model this paper uses — and improves Recall@100 from 0.739 to 0.874 (+18.3%)** on one task. On your own retriever, a rich representation transform moves recall a lot. Claiming "representation barely matters for dense retrievers" without this caveat lets a reviewer citing AutoIndex sink the paper.

**Required edits:**

1. **Scope the thesis.** In the STEP 2 thesis, abstract, and conclusion, change "retriever identity dominates representation choice" → "retriever identity dominates **coarse field-level** representation choice."

2. **Related Work — replace the AutoIndex sentence** (drop-in; adjust `\cite` key to the repo's):
```latex
AutoIndex learns executable representation programs---slicing, enriching,
reweighting, or normalizing documents---around a fixed BM25 backend, and reports
large recall gains from representation alone, including a preliminary dense result
in which a learned program improves Qwen3-Embedding-0.6B Recall@100 by 18.3\% on a
single task~\cite{autoindex}. Our study is complementary and deliberately narrower:
we hold five heterogeneous retrievers fixed and vary a small set of coarse,
field-level static constructions, asking not whether representation can be optimized
but whether a construction chosen around one retriever reorders another. Our finding
that it does not is a statement about the portability of coarse construction choices
across frozen dense retrievers, not a claim that representation is inert---AutoIndex
shows the opposite once the representation space is rich and corpus-adaptive.
```

3. **Add one limitations sentence** (drop-in):
```latex
Our representation surface is five coarse, static, field-level constructions; richer,
learned, corpus-adaptive representation programs can move even dense retrievers
substantially~\cite{autoindex}, so our null on representation reordering is bounded to
coarse construction choices and does not extend to representation optimization in general.
```

4. **Optional strong positioning (author's call).** AutoIndex names "program transfer" and "optimizer transfer" (applying a learned representation/procedure across datasets or retrievers) as open future work. This paper's cross-retriever transfer matrix is an early empirical probe of exactly that open question — reframing it this way converts a near-scoop into an adjacent contribution. `TODO(human): decide whether to foreground "we give a first empirical look at the transfer question AutoIndex leaves open."`

Agent: apply 1–3 (factual, drop-in). Leave 4 as `TODO(human)`.

---

## STEP 3 — Define the static comparator (agent must resolve or flag)

The paper's strongest number (0.331 → 0.442) is uninterpretable because the comparator is never named, and the paper concedes it "does not separate representation from other fixed components." Reviewers will ask: *is this just a strong dense retriever beating a weak baseline?*

Find the comparator definition in the repo (search: `comparator`, `baseline`, `static`, `predefined`, selection scripts, config for Final-872). Extract its **model checkpoint + representation construction + prompt (if any) + fusion (if any)**. Then insert one precise sentence in Section V-A where the comparator is introduced:

```latex
The static comparator is {{COMPARATOR_FULL_SPEC: model checkpoint, representation
construction, prompt, fusion}}, fixed at Selection-125 close.
```

Keep the existing honest caveat that the paired comparison is system-level and does not isolate representation — but now the reader can judge what the 0.111 gain does and does not attribute.

If the comparator cannot be determined unambiguously from the repo, insert:
`TODO(human): state exact comparator = model + representation + prompt + fusion. Do not submit without this.`
Do **not** guess.

---

## STEP 4 — Promote the exposure finding

Already improved in v2 (Fig. 4 title now says exposure limits recall — good). Finish the job:
- Abstract already carries it (STEP 2.1).
- Add one sentence to the intro so it's a headline, not a diagnostic afterthought: exposure (78.3% of relevant families absent from Top-200) is the binding constraint; within-pool ordering headroom is only 0.072.
- In Section V-B keep the numbers as-is (frozen); just make sure the framing matches the thesis.

---

## STEP 5 — Decimal normalization (display only, never the value)

Rule: all metric levels, differences, and CI bounds render at **3 decimals** in body text and tables. This is display rounding — the stored/underlying values do not change (HARD RULE 1).

Body replacements (old → display):
- 0.331097→0.331, 0.442476→0.442, 0.111379→0.111, CI [0.102294, 0.120438]→[0.102, 0.120]
- 0.279253→0.279, 0.365595→0.366, 0.086342→0.086, CI [0.078673, 0.094077]→[0.079, 0.094]
- 0.233666→0.234, 0.297459→0.297, 0.063794→0.064 (and add the STEP 1.3 CI)
- A2: 0.234667→0.235, 0.290000→0.290, 0.423000→0.423, 0.358667→0.359, 0.373667→0.374
- Exposure: 0.188450→0.188, 0.260167→0.260, 0.071717→0.072
- Integer counts stay integers: 619 / 158 / 95, 796 / 332 / 4065 / 5193, 67 / 297 / 86 / 455 / 905.

**Figure-2 exception:** at 3 decimals the within-target cells collapse (all ~0.419 for PatEmbed), which would look like a typo. In Fig. 2, either (a) keep the raw cell labels but add the bootstrap CI/range from STEP 1 as the headline annotation, or (b) replace cell labels with the STEP-1 differences+CIs. Do **not** show 6-decimal cell labels in body prose. The within-target *ranges* (0.000838 etc.) are better expressed as "< 0.004, CI contains zero" per STEP 2.2.

---

## STEP 6 — Cut redundant hedging (keep load-bearing caveats once)

The prose disclaims almost every sentence, which exhausts the reader and signals low confidence. Rule: **each caveat appears once, in Methods (Section III), then is trusted.**

Remove repeated instances of: "descriptive development evidence", "no causal before/after interpretation", "these values are reported only as a separate characterization", "no cell-level confirmatory inference is claimed". Keep exactly one clear statement of the development/confirmation/diagnosis separation in Section III.

**Load-bearing — keep (once, do not delete):**
- Final-872 "supports the complete selected system, not a representation-only causal effect" (this is the honest scope of the headline number — keep once, in V-A).
- The A7 note that incidences and macro Recall use different aggregation units (prevents a real misreading — keep once, in the Fig. 4 caption or V-B).
- The boundaries paragraph (license, citation-based ≠ legal FTO) — keep, it's correct and cheap.

Do not over-cut into dishonesty. The goal is fewer, stronger caveats, not zero.

---

## STEP 7 — Citations (verified — apply these exactly)

Verified against arXiv (Aug 2026):

- **[1] DAPFAM** — real: `arXiv:2506.22141`, Ayaou, Cavallucci, Chibane, INSA Strasbourg (v1 Jun 2025, v2 Sep 2025). The paper cites a journal version "Array, vol. 29, p. 100720, 2026." If that journal version is confirmed, keep it; **else** fall back to the arXiv cite. Action: `TODO(human): confirm Array vol.29 p.100720 (2026) exists; otherwise cite arXiv:2506.22141.`
- **[2] Benchmarking patent embeddings (22 models)** — real: `arXiv:2605.24297`, Yousefiramandi & Cooney (Clarivate). Correct as cited.
- **[3] PatenTEB** — real: `arXiv:2510.22264`, Ayaou & Cavallucci (Oct 2025). Correct. Useful anchor: PatenTEB reports **patembed-large = 0.377 nDCG@100 on DAPFAM** — consider one sentence sanity-checking your PatEmbed numbers against this external value.
- **[4] AutoIndex** — **VERIFIED real:** `arXiv:2607.18603v1` [cs.IR], 21 Jul 2026, O'Nuallain, Rajkumar, Narayanasamy, Jiang, Chaudhari (UMass Amherst) & Drozdov (Databricks Mosaic Research), "AutoIndex: Learning Representation Programs for Retrieval." Author list and ID as cited are correct — no citation fix needed. **BUT this paper's *content* is now the single biggest threat to the central claim — see STEP 2A, which is the top priority.**

Related Work positioning (add one sentence): DAPFAM [1], PatenTEB [3], and PatEmbed are the same group (Ayaou & Cavallucci, INSA Strasbourg). State explicitly how your contribution (an inferential cross-retriever *portability* test with protected selection/confirmation separation) differs from theirs, so novelty isn't assumed to be subsumed by PatenTEB.

---

## STEP 8 — Reproducibility block

Add a short reproducibility paragraph or table with exact values (read from repo config, don't guess; `TODO(human)` if missing):
- The 5 model checkpoints with **exact HF revision/commit** (BM25 impl + params; BGE-M3; PatEmbed-large; Arctic Embed M v2.0; Qwen3 Embedding 0.6B).
- Prompt/instruction templates for the instruction-tuned encoders (Qwen3, Arctic) — these materially affect scores.
- RRF fusion `k`; passage window 384 / overlap 64 (already stated) and max aggregation (stated).
- Bootstrap: 10,000 resamples, 95% percentile, seed.

---

## STEP 9 — Explain the preregistration reserve mechanism (the "52/44/8")

"52 prespecified configurations, 44 evaluated, 8 dormant reserves" reads as inside-baseball. Since preregistration is a *strength*, explain it in one sentence rather than cutting it:

```latex
The 52 configurations were registered in advance; 8 are conditional reserves
whose activation predicates were not triggered, so 44 were executed. Registering
the full set, including untriggered reserves, fixes the search space before any
result is seen.
```

---

## STEP 10 — Tables and captions

- Convert all tables to `booktabs` (`\toprule`/`\midrule`/`\bottomrule`, no vertical rules).
- Table II: keep, but make the caption state plainly that Shared-screen and Per-system-search columns are different decision rules (already noted) — one sentence, not repeated in body.
- Ensure every figure caption states its evidence level (development / confirmation / post-confirmatory) once.

---

## STEP 11 — Title (human decision — flag, don't change unilaterally)

The new thesis is "retriever dominates, exposure binds." "Beyond the Retriever" can read as under-selling that. It's defensible as a provocation the abstract resolves. Insert:
`TODO(human): confirm title. "Beyond the Retriever" works if the abstract resolves the irony (representation matters less than assumed). Alternatives if you want the thesis in the title: "Retriever Identity Dominates Representation in Cross-Domain Patent Retrieval" or "Exposure-Bound: Diagnosing Cross-Domain Patent Retrieval".`

---

## STEP 12 — Final self-check + handoff

Before declaring done:
1. `numbers_diff.md` produced; every line is `DISPLAY_ROUNDING`, `NEW_STAT`, or `REMOVED`. Zero `VALUE_CHANGED`.
2. Every `{{slot}}` is filled from `stats.json` or the repo — none left literal.
3. Every unresolved fact is a visible `TODO(human)` block, listed together at the top of `CHANGELOG.md`.
4. Abstract carries one thesis, the inferential transfer result, and the exposure result.
5. Comparator is named (or flagged).
6. Citation [4] resolved (or flagged); [1] journal-vs-arXiv resolved (or flagged).
7. `latexmk` builds with no new warnings; `main.pdf` present.

Hand back: `main.pdf`, `stats.json`, `numbers_diff.md`, `CHANGELOG.md`, and the consolidated `TODO(human)` list. The author will re-review against these.

---

### Priority if time is limited
1 (STEP 2A, scope vs AutoIndex) · 2 (STEP 1 + 2.2, inferential transfer) · 3 (STEP 3, comparator) · 4 (STEP 2.1, abstract/thesis) · 5 (STEP 4, exposure) · 6 (STEP 5, decimals) · 7 (STEP 6, de-hedge) · 8 (STEP 7–10) · 9 (STEP 11 title). Steps 1–5 remove ~90% of rejection risk. STEP 2A is non-negotiable — the paper already cites AutoIndex and uses the same model it improves, so an unscoped claim is the fastest path to reject.
