# VERSION DIFF -- paper_00 -> paper_01

Generated mechanically. Scientific interpretation belongs in HANDOFF/IMPLEMENTATION_REPORT.

## Summary
- Added: 18
- Removed: 21
- Modified: 6
- Unchanged: 4

## Added
- `build/paper_isainlp2026.aux`
- `build/paper_isainlp2026.bbl`
- `build/paper_isainlp2026.blg`
- `build/paper_isainlp2026.fdb_latexmk`
- `build/paper_isainlp2026.fls`
- `build/paper_isainlp2026.log`
- `build/paper_isainlp2026.pdf`
- `figures/isainlp2026/evidence_chain.pdf`
- `figures/isainlp2026/evidence_chain.png`
- `figures/isainlp2026/out_domain_diagnosis.pdf`
- `figures/isainlp2026/out_domain_diagnosis.png`
- `manuscript/paper_isainlp2026.tex`
- `provenance/protected_ledger.md`
- `provenance/release-manifest-isainlp2026.json`
- `reports/BUILD_QA_01.md`
- `reports/SCIENTIFIC_REVIEW_01.md`
- `reports/VISUAL_REVIEW_01.md`
- `reports/paper_guard_01.json`

## Removed
- `build/paper_v08.aux`
- `build/paper_v08.bbl`
- `build/paper_v08.blg`
- `build/paper_v08.log`
- `build/paper_v08.pdf`
- `build/render-v08/page-1.png`
- `build/render-v08/page-2.png`
- `build/render-v08/page-3.png`
- `build/render-v08/page-4.png`
- `build/render-v08/page-5.png`
- `figures/source/a5_a6_evidence_state.png`
- `figures/source/candidate_exposure_decomposition.pdf`
- `figures/source/candidate_exposure_decomposition.png`
- `figures/source/evaluation_story_arc.pdf`
- `figures/source/evaluation_story_arc.png`
- `figures/source/exposure_curves_in_out_all.pdf`
- `figures/source/exposure_curves_in_out_all.png`
- `figures/source/final872_quality_comparison.png`
- `manuscript.zip`
- `manuscript/paper_v08.tex`
- `provenance/release-manifest-v08.json`

## Modified
- `README.md`
- `RULES_AND_TEMPLATE.md`
- `figures/generate_figures.py`
- `provenance/claim_to_evidence.csv`
- `provenance/safe-evidence-pointer.md`
- `provenance/story_arc.md`

## Diff: `README.md`
```diff
--- paper_00/README.md
+++ paper_01/README.md
@@ -1,27 +1,18 @@
-# ArmIndex Paper V08
+# ArmIndex iSAI-NLP 2026 Paper 01
 
-This is the pre-review manuscript workspace for the ArmIndex journal/conference
-paper. It contains only aggregate-safe material. The review manuscript stays
-double-blind until the Owner completes the venue submission record.
+This immutable sibling is a from-scratch iSAI-NLP 2026 rewrite grounded in the
+A5 held-out confirmation and A6/A7 frozen-pool audits. `paper_00` is preserved
+as historical context and is not an iSAI submission artifact.
 
-## Layout
+## Entry points
 
-- `manuscript/`: editable paper source and review notes.
-- `references/`: verified BibTeX records and citation audit.
-- `figures/source/`: immutable copies or links to canonical source figures.
-- `figures/review/`: figures selected for the anonymous review PDF.
-- `figures/final/`: camera-ready derivatives; empty until review decisions.
-- `tables/`: aggregate-safe generated tables.
-- `build/`: local compilation output; never scientific authority.
-- `provenance/`: release manifest, claim matrix, and checksums.
+- Manuscript: `manuscript/paper_isainlp2026.tex`
+- Review PDF: `build/paper_isainlp2026.pdf`
+- Figure source: `figures/generate_figures.py`
+- Figure data: `tables/a7-layer-aggregate-metrics.csv`
+- Claim map: `provenance/claim_to_evidence.csv`
+- Release manifest: `provenance/release-manifest-isainlp2026.json`
 
-## V08 workflow
-
-1. Freeze claims against canonical A0-A7 receipts.
-2. Edit `manuscript/paper_v08.tex` and keep author fields anonymous.
-3. Compile with the supplied `IEEEtran.cls`; target 4-6 pages for JCSSE 2027.
-4. Run the checks in `RULES_AND_TEMPLATE.md` before review.
-5. Put any reviewer revision in a new numbered sibling directory; preserve V01--V08.
-
-Protected qrels, membership, identifiers, rankings, per-query outcomes,
-credentials, model payloads, and provider payloads must not be copied here.
+The package contains aggregate-safe evidence only. Protected relevance data,
+identifiers, rankings, per-query outcomes, credentials, and provider payloads
+must remain outside the paper workspace.
```

## Diff: `RULES_AND_TEMPLATE.md`
```diff
--- paper_00/RULES_AND_TEMPLATE.md
+++ paper_01/RULES_AND_TEMPLATE.md
@@ -1,18 +1,17 @@
-# Paper V04 Rules and Template Contract
+# Paper 01 iSAI-NLP Rules and Template Contract
 
 ## Scientific rules
 
-- Use A0-A7 canonical receipts as the only numeric authority.
-- State A7 as post-confirmatory diagnosis of the immutable A6 Top-200 pool.
-- Label A7-L7 values as frozen-pool analytical bounds, never as reranker results.
-- Do not claim external protocol comparability when A7-L3 is `UNKNOWN`.
-- Do not claim causal representation ablation or query rescue; A7 records both
-  as unavailable/descriptive-only.
-- Preserve the A5 winner and do not add a new retrieval experiment.
+- Use canonical A5-A7 receipts as the only numeric authority.
+- Keep A5 confirmation separate from A6/A7 post-confirmatory diagnosis.
+- Label A7-L7 values as frozen-pool analytical bounds, never reranker results.
+- Keep raw incidence counts separate from macro-Recall quantities.
+- Do not claim external protocol comparability, causal attribution, reranker
+  efficacy, pool-expansion efficacy, or external generalization.
 
 ## Review rules
 
-- English, A4, IEEE conference two-column, 4-6 pages.
+- English, A4, official IEEE conference two-column, at most 6 pages.
 - Use the supplied `IEEEtran.cls`; do not edit margins, class, or font sizes.
 - Keep author, affiliation, funding, repository, and institution identifiers
   out of the review version.
@@ -21,16 +20,7 @@
 
 ## Build template
 
-```powershell
-cd paper_04
-New-Item -ItemType Directory -Force build | Out-Null
-pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build manuscript/paper_v04.tex
-Push-Location build
-bibtex paper_v04
-Pop-Location
-pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build manuscript/paper_v04.tex
-pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build manuscript/paper_v04.tex
-```
-
-The review artifact is `build/paper_v04.pdf`. Before release, check page count,
+Run PDFLaTeX from `paper_01`, BibTeX from `paper_01/build`, then PDFLaTeX twice
+from `paper_01`. The review artifact is `build/paper_isainlp2026.pdf`. Before
+release, check page count,
 anonymous metadata, no template guidance text, and `git diff --check`.
```

## Diff: `figures/generate_figures.py`
```diff
--- paper_00/figures/generate_figures.py
+++ paper_01/figures/generate_figures.py
@@ -1,217 +1,173 @@
-"""Generate V08 figures from the aggregate-safe A7 table.
+from __future__ import annotations
 
-The visual system is intentionally editorial: one takeaway per figure,
-direct labels, stable geometry, and restrained color that survives IEEE
-column scaling. PDF files are the manuscript authorities; PNG files support
-visual QA.
-"""
-
+import csv
+from decimal import Decimal
 from pathlib import Path
 
 import matplotlib.pyplot as plt
-import numpy as np
-import pandas as pd
 from matplotlib.patches import FancyArrowPatch, Rectangle
 
 
 ROOT = Path(__file__).resolve().parents[1]
-SOURCE = ROOT / "tables" / "a7-layer-aggregate-metrics.csv"
-OUT = ROOT / "figures" / "source"
-OUT.mkdir(parents=True, exist_ok=True)
+DATA = ROOT / "tables" / "a7-layer-aggregate-metrics.csv"
+OUTPUT = ROOT / "figures" / "isainlp2026"
 
-CHARCOAL = "#20252B"
-MUTED = "#626B75"
-GRID = "#E7EAEE"
-NAVY = "#163A5F"
-TEAL = "#007C83"
-CORAL = "#D85C54"
-OCHRE = "#C38B2E"
-PALE_BLUE = "#EAF1F7"
-PALE_TEAL = "#E8F3F2"
-PALE_CORAL = "#FBECE9"
-PALE_OCHRE = "#FBF4E5"
-
-plt.rcParams.update(
-    {
-        "font.family": "DejaVu Sans",
-        "font.size": 8.5,
-        "axes.titlesize": 10,
-        "axes.labelsize": 8.5,
-        "figure.dpi": 180,
-        "savefig.dpi": 320,
-        "pdf.fonttype": 42,
-        "ps.fonttype": 42,
-        "axes.spines.top": False,
-        "axes.spines.right": False,
-        "axes.spines.left": False,
-        "axes.spines.bottom": False,
-        "xtick.color": MUTED,
-        "ytick.color": MUTED,
-        "text.color": CHARCOAL,
-    }
-)
+CHARCOAL = "#252A2E"
+BLUE = "#2B5D7D"
+TEAL = "#3A7D78"
+GOLD = "#C49332"
+LIGHT_GRAY = "#D7DADD"
+MID_GRAY = "#7A8187"
+PAPER = "#FFFFFF"
 
 
-def read_metrics():
-    df = pd.read_csv(SOURCE)
-    df["value"] = pd.to_numeric(df["value"], errors="coerce")
-    return df
+def load_metrics() -> dict[tuple[str, str, str], Decimal]:
+    metrics: dict[tuple[str, str, str], Decimal] = {}
+    with DATA.open(newline="", encoding="utf-8") as handle:
+        for row in csv.DictReader(handle):
+            try:
+                value = Decimal(row["value"])
+            except Exception:
+                continue
+            metrics[(row["layer"], row["population"], row["metric"])] = value
+    return metrics
 
 
-def save(fig, name):
-    # Keep the declared canvas size.  Tight bounding boxes would grow the
-    # canvas around direct labels and then force IEEE to shrink the plot.
-    fig.savefig(OUT / name, bbox_inches=None, pad_inches=0.02, facecolor="white")
-    fig.savefig(OUT / Path(name).with_suffix(".pdf"), bbox_inches=None, pad_inches=0.02, facecolor="white")
+def checked(metrics: dict[tuple[str, str, str], Decimal], key, expected: str) -> float:
+    value = metrics[key]
+    if value != Decimal(expected):
+        raise ValueError(f"Canonical value changed for {key}: {value} != {expected}")
+    return float(value)
+
+
+def save(fig: plt.Figure, stem: str) -> None:
+    OUTPUT.mkdir(parents=True, exist_ok=True)
+    metadata = {"Title": stem, "Author": "Anonymous", "Creator": "Matplotlib"}
+    fig.savefig(OUTPUT / f"{stem}.pdf", bbox_inches="tight", metadata=metadata)
+    fig.savefig(OUTPUT / f"{stem}.png", dpi=300, bbox_inches="tight")
     plt.close(fig)
 
 
-def metric(df, population, name):
-    return float(df[(df.layer == "A7-L6") & (df.population == population) & (df.metric == name)].value.iloc[0])
+def evidence_chain() -> None:
+    fig, ax = plt.subplots(figsize=(7.16, 1.48))
+    ax.set_xlim(0, 1)
+    ax.set_ylim(0, 1)
+    ax.axis("off")
+
+    stages = [
+        (0.015, 0.28, 0.275, 0.56, BLUE, "A5  CONFIRM", "872 held-out OUT queries", "Frozen dense vs. BM25"),
+        (0.365, 0.28, 0.275, 0.56, TEAL, "A6  MATERIALIZE", "45,336 documents / 1,247 queries", "Immutable family Top-200 pool"),
+        (0.715, 0.28, 0.27, 0.56, GOLD, "A7  AUDIT", "Same pool; no reselection", "Exposure counts + oracle bound"),
+    ]
+
+    for idx, (x, y, w, h, color, title, line1, line2) in enumerate(stages):
... diff truncated by --max-diff-lines ...
```

## Diff: `provenance/claim_to_evidence.csv`
```diff
--- paper_00/provenance/claim_to_evidence.csv
+++ paper_01/provenance/claim_to_evidence.csv
@@ -1,9 +1,13 @@
-claim_id,claim,evidence,evidence_class,boundary
-C01,Five-family screening and staged selection produced one frozen dense configuration,01_Research/docs/progress_report/A1_common_screen_aggregate_eda_20260818.csv;01_Research/control/armindex/a5/final-r03-20260822/,development+confirmatory,No universal superiority claim
-C02,Held-out dense versus static Recall@100 delta is +0.111379 with CI [0.102294,0.120439],01_Research/control/armindex/a5/final-r03-20260822/A5_FINAL_OWNER_EVALUATION.json,confirmatory aggregate,Final-872 scope only
-C03,Full-corpus aggregate Recall@100 is 0.438964626214 and nDCG@100 is 0.362497103931,01_Research/control/armindex/a6/a6-result-integrity-audit-20260823.json;01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv,materialization+diagnostic,Aggregate-safe only
-C04,Full-corpus Recall@100 is 0.528164111236 in-domain and 0.188449898653 out-of-domain,01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv,diagnostic,No external generalization
-C05,"11,302 relevant-family incidences are absent at rank 200 overall and 4,065 are absent out of domain",01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv,exposure diagnosis,Raw incidence counts are not a macro-Recall decomposition
-C06,Bounded top-200 ordering headroom is 0.107868 overall and 0.071717 out of domain,01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv,analytical bound,Not a reranker result or pool expansion
-C07,External protocol comparison and causal or legal interpretation are unsupported,01_Research/control/armindex/a7/a7-result-integrity-audit-20260823.json,claim boundary,Unknown settings remain unknown
-C08,"A6 used two active GPUs and recorded peak VRAM of 1,773,727,744 bytes",04_Owner_Stores/armindex/a6/a6-goal001-20260823T052423Z-full09/A6_EXECUTION_CONFIG.json;01_Research/control/armindex/a6/a6-result-integrity-audit-20260823.json,receipt-bound execution identity,Run-specific operational description only
+claim_id,manuscript_claim,evidence,evidence_class,denominator_aggregation_boundary
+C01,"One frozen dense system was compared once with BM25 on 872 held-out OUT queries","01_Research/control/armindex/a5/final-r03-20260822/A5_FINAL_OWNER_EVALUATION.json;A5_FINAL_RESULT_INTEGRITY_AUDIT.json",confirmatory,"872 queries; one final access; aggregate-safe only"
+C02,"Dense versus BM25 Recall@100 was 0.442476 versus 0.331097 (delta +0.111379; 95% CI [0.102294,0.120438]); nDCG@100 was 0.365595 versus 0.279253 (delta +0.086342; 95% CI [0.078673,0.094077])","01_Research/control/armindex/a5/final-r03-20260822/A5_FINAL_OWNER_EVALUATION.json:systems,paired_effects",confirmatory,"Macro means over Final-872 OUT queries; paired percentile bootstrap; 10000 resamples"
+C03,"The frozen system materialized 45336 documents into a deterministic 1247-query family Top-200 pool with 249400 rows","01_Research/control/armindex/a6/a6-result-integrity-audit-20260823.json:coverage",post-confirmatory materialization,"Complete DAPFAM run; no winner change; aggregate-safe"
+C04,"Complete-scale Recall@100 was 0.528164 IN and 0.188450 OUT","01_Research/control/armindex/a6/a6-result-integrity-audit-20260823.json:aggregate_metrics",post-confirmatory measurement,"Receipt-defined strata; 1217 IN and 905 OUT judged queries; strata are not additive"
+C05,"Of 5193 OUT relevant-family incidences, 796 were exposed by rank 100, 332 first appeared at ranks 101-200, and 4065 were absent at rank 200","01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv:A7-L6-OUT",post-confirmatory diagnosis,"Raw incidence counts; mutually exclusive states; not macro-Recall components"
+C06,"Within the same OUT Top-200 pool, observed macro Recall@100 was 0.188450 and the fixed-pool oracle was 0.260167, for 0.071717 ordering headroom","01_Research/outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv:A7-L7-OUT",analytical bound,"Macro mean over 905 OUT queries; no pool expansion; not a reranker result"
+C07,"A6 and A7 used zero selection/final accesses and did not reopen model selection","01_Research/control/armindex/a6/a6-result-integrity-audit-20260823.json:boundary_checks;01_Research/control/armindex/a7/a7-result-integrity-audit-20260823.json:boundary_checks",governance boundary,"Post-confirmatory frozen pool only"
+C08,"No external protocol comparison, causal attribution, reranker efficacy, pool-expansion efficacy, or external generalization is claimed","01_Research/control/armindex/a7/a7-result-integrity-audit-20260823.json:result_checks,claim_boundary",claim boundary,"External configuration not fully verified; descriptive diagnosis only"
+C09,"A4 froze four finalists, used one complete Selection-125 access with OUT metric denominator n=90, and used zero final accesses","01_Research/control/armindex/a4/a4-selection-125-population-accounting-audit-20260823.json;04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-registry.json",selection lineage,"Selection-125 exposure and coverage; OUT metric denominator n=90; aggregate-safe only"
+C10,"Six preregistered A4 pairwise comparisons used 10000 bootstrap resamples, Holm-Bonferroni correction, and a predeclared lexicographic selection rule","04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-registry.json;04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-receipt.json;01_Research/docs/research/ARMINDEX_RESEARCH_PLAN_V02.md",selection protocol,"Primary OUT Recall@100; declared near-tie thresholds and operational tie-breakers"
+C11,"Selection-125 and Final-872 were separate frozen scopes under the same parent split commitment","01_Research/control/armindex/a4/a4-selection-125-population-accounting-audit-20260823.json;01_Research/control/armindex/a5/final-r03-20260822/A5_FINAL_RESULT_INTEGRITY_AUDIT.json",governance boundary,"No membership, protected identifier, or unverified disjointness claim"
+C12,"The A5 winner configuration, A6 model manifest, and A6 execution configuration were SHA-256 bound","04_Owner_Stores/armindex/a6/a6-goal001-20260823T052423Z-full09/A6_MODEL_MANIFEST.json;01_Research/control/armindex/a5/final-r03-20260822/A5_FINAL_RESULT_INTEGRITY_AUDIT.json;paper_01/provenance/release-manifest-isainlp2026.json",configuration binding,"Full hashes retained in the protected ledger and release manifest; prefixes reported in manuscript"
```

## Diff: `provenance/safe-evidence-pointer.md`
```diff
--- paper_00/provenance/safe-evidence-pointer.md
+++ paper_01/provenance/safe-evidence-pointer.md
@@ -1,10 +1,13 @@
 # Safe Evidence Pointer
 
-This anonymous package points to the aggregate-safe A6 result-integrity audit
-dated 2026-08-23. The frozen family-pool hash is
+The central diagnosis is bound to the aggregate-safe A6 and A7 integrity
+audits dated 2026-08-23. The immutable A6 family-pool SHA-256 is
+`9ede1cee084db346743eb7e3dcbf300ac013c60055403f58449169dd71041879`.
+The independent A6 determinism SHA-256 is
 `3c72d4ed8b7c69eeebb842df36ecc4e2832d8ad7108eb249ac7f3b16fd6dee23`.
 
+The public A7 aggregate CSV has SHA-256
+`ad869ef99254df10c2e155911a1aa1a975dc9e41f1203bffa1fac2ab66043c1e`.
 Protected query identifiers, family membership, rankings, relevance judgments,
-and full receipt values remain Owner-local. This pointer is a provenance aid;
-it is not a release of protected evidence or an independently rerunnable code
-bundle.
+and per-query outcomes remain Owner-local and are not part of the manuscript
+package.
```

## Diff: `provenance/story_arc.md`
```diff
--- paper_00/provenance/story_arc.md
+++ paper_01/provenance/story_arc.md
@@ -1,25 +1,29 @@
-# Publication Story Arc
+# iSAI-NLP 2026 Story Arc
 
 ## Title
 
-Where Does Recall Disappear? Diagnosing Candidate Exposure in Cross-Domain Patent Retrieval
+Diagnosing Candidate Exposure after Held-Out Confirmation in Cross-Domain Patent Retrieval
 
 ## Thesis
 
-The paper asks where recall disappears. It opens one question at a time and follows a frozen representation from screening to full benchmark scale. Relevant families may never enter the pool seen by a ranker. The diagnosis reports two complementary quantities: raw relevant-family incidence composition describes candidate availability, while a fixed-pool oracle bounds ordering recovery in macro-Recall units.
+After one held-out comparison freezes the system, a complete-benchmark audit
+separates two non-interchangeable views of out-of-domain failure: raw candidate
+availability and macro-Recall ordering headroom within the same Top-200 pool.
 
 ## Evidence sequence
 
-1. **Opening question:** Can a headline retrieval score tell us where recall is lost?
-2. **A1:** What is the representation frontier?
-3. **A2:** Can executable search change that frontier?
-4. **A3:** Can transfer or fusion close the domain gap?
-5. **A4:** Which operating point survives quality-latency tradeoffs?
-6. **A5:** Does the selected configuration confirm on held-out queries?
-7. **A6:** Does the confirmed configuration survive complete-corpus scale?
-8. **A7:** Is the remaining loss ordering or candidate exposure?
-9. **Answer:** The out-of-domain pool contains 4,065 absent incidences among 5,193 total incidences, while the same partition has 0.071717 macro-Recall ordering headroom. These quantities answer different questions and are not additive.
+1. **Problem:** Recall@100 alone cannot distinguish low ordering from absence.
+2. **Gap:** The distinction is often asserted but not bound to a frozen,
+   post-confirmatory family pool.
+3. **RQ:** What does the frozen OUT pool show about candidate absence and
+   within-pool ordering headroom?
+4. **Design:** A5 confirms once; A6 materializes; A7 audits without reselection.
+5. **Finding:** 4,065/5,193 OUT incidences are absent at rank 200; the same
+   population has 0.071717 macro-Recall ordering headroom.
+6. **Boundary:** Counts and macro averages are complementary, not additive.
 
 ## Claim boundary
 
-The paper reports aggregate-safe benchmark evidence only. It does not claim universal superiority, external generalization, a learned reranker result, pool expansion, causal or legal impact, or release of protected identifiers, rankings, or relevance judgments.
+The paper reports aggregate-safe benchmark evidence only. It does not claim
+universal superiority, external generalization, a learned reranker result,
+pool-expansion efficacy, causal or legal impact, or release of protected data.
```
