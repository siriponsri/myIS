# Reusable Asset Map

> Generated deterministically from `00_governance/config/reusable_assets.yaml`.
> Do not edit directly; run `myis-assets map`.

## Phase And Task Coverage

| Task | Purpose | Gate | Reusable assets |
|---|---|---|---|
| `F0.1` | Capture integrity baseline | `G0` | `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |
| `F0.2` | Migrate active docs and configuration | `G0` | `APP-PUBLICATION-TOOLING` (adapt, pointer); `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |
| `F0.3` | Update read-only projections | `G0` | `APP-PUBLICATION-TOOLING` (adapt, pointer); `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |
| `F1.1` | Reproduce B0, B1, and B2 | `G1` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-DAPFAM-TEXT-PRIMITIVES` (adapt, preport); `APP-LEGACY-DENSE-EMBEDDINGS` (reference_only, none); `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PATEMBED-CONTROL` (reuse, pointer); `APP-RETRIEVAL-ENGINEERING` (adapt, preport); `APP-SPARSE-FTS-INDEXES` (adapt, pointer) |
| `D0.1` | Freeze shared membership and dual firewalls | `G2` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `D0.2` | Run C-MARGIN and C-SOEI audits | `G2` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `C0.1` | Freeze and validate the C0 recipe | `G2` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-MULTIGRANULAR` (adapt, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-DAPFAM-TEXT-PRIMITIVES` (adapt, preport); `APP-PAPER-B-RERANKING` (adapt, preport); `APP-RETRIEVAL-ENGINEERING` (adapt, preport); `APP-SPARSE-FTS-INDEXES` (adapt, pointer) |
| `C1.1` | Search the typed C_TRAIN surface | `G2` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-MULTIGRANULAR` (adapt, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-DAPFAM-TEXT-PRIMITIVES` (adapt, preport); `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-B-RERANKING` (adapt, preport); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport); `APP-RETRIEVAL-ENGINEERING` (adapt, preport); `APP-SPARSE-FTS-INDEXES` (adapt, pointer) |
| `C1.2` | Evaluate one selection batch | `G2` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-MULTIGRANULAR` (adapt, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-B-RERANKING` (adapt, preport); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport); `APP-RETRIEVAL-ENGINEERING` (adapt, preport); `APP-SPARSE-FTS-INDEXES` (adapt, pointer) |
| `CF.1` | Freeze C0, C1, and the C1 harness | `G3` | `APP-PAPER-B-RERANKING` (adapt, preport); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `S0.1` | Lock provider, A0, and A1 | `G4` | `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport) |
| `S0.2` | Run the independent S-MARGIN audit | `G4` | `APP-PAPER-C-COST-PATTERNS` (reference_only, preport); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `S1.1` | Execute A2 SkillOpt | `G4` | `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport) |
| `S1.2` | Execute A2L SkillOpt-Lite | `G4` | `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport) |
| `S1.3` | Execute typed A3 HarnessOpt | `G4` | `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-C-COST-PATTERNS` (reference_only, preport) |
| `SF.1` | Select once and freeze one artifact per arm | `G5` | `APP-PAPER-B-GEPA` (reference_only, none); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `CT.1` | Run frozen PatenTEB retrieval_OUT transfer | `G7` | `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |
| `Q.1` | Evaluate the untouched joint test | `G6` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `Q.2` | Run Track C ranking diagnostic | `G6` | `APP-DAPFAM-MULTIGRANULAR` (adapt, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-PAPER-B-RERANKING` (adapt, preport); `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PAPER-D-METHOD-LESSONS` (reference_only, none) |
| `Q.3` | Run C0 full-benchmark descriptive evaluation | `G6` | `APP-DAPFAM-CORE` (reuse, pointer); `APP-DAPFAM-PAPER-VIEWS` (reuse, pointer); `APP-DAPFAM-TEXT-PRIMITIVES` (adapt, preport); `APP-LEGACY-DENSE-EMBEDDINGS` (reference_only, none); `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PATEMBED-CONTROL` (reuse, pointer); `APP-SPARSE-FTS-INDEXES` (adapt, pointer) |
| `PC.1` | Assemble the Track C manuscript | `G8` | `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PUBLICATION-TOOLING` (adapt, pointer); `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |
| `PS.1` | Assemble the Track S manuscript | `G8` | `APP-PAPER-D-FROZEN-RESULTS` (reference_only, fixture); `APP-PUBLICATION-TOOLING` (adapt, pointer); `APP-WIKI-GRAPH-POINTERS` (reference_only, pointer) |

## Asset Catalog

| Asset | Kind | Disposition | Compatibility | Copy | Savings |
|---|---|---|---|---|---|
| `APP-DAPFAM-CORE` | dataset_snapshot | `reuse` | `conditional` | `pointer` | time: avoids reacquisition and preprocessing; compute: avoids dataset conversion; storage: avoids duplicating about 3.3 GB of core files |
| `APP-DAPFAM-MULTIGRANULAR` | derived_dataset | `adapt` | `conditional` | `pointer` | time: avoids multi-granularity regeneration; compute: avoids claim and element parsing; storage: avoids about 7.8 GB of duplicate chunks |
| `APP-DAPFAM-PAPER-VIEWS` | derived_dataset | `reuse` | `conditional` | `pointer` | time: avoids rebuilding paper-aligned views; compute: avoids passage generation; storage: avoids about 396 MB of duplicate views |
| `APP-DAPFAM-TEXT-PRIMITIVES` | source_code | `adapt` | `conditional` | `preport` | time: reuses tested text conventions; compute: no impact; storage: negligible code-only port |
| `APP-LEGACY-DENSE-EMBEDDINGS` | dense_index | `reference_only` | `incompatible` | `none` | time: provides immediate incompatibility evidence; compute: prevents invalid reruns; storage: prevents duplicate legacy embeddings |
| `APP-PAPER-B-GEPA` | optimizer_reference | `reference_only` | `conditional` | `none` | time: captures adapter and feedback lessons; compute: prevents invalid optimizer trials; storage: no historical payload copies |
| `APP-PAPER-B-RERANKING` | source_code | `adapt` | `conditional` | `preport` | time: reuses parser failure lessons; compute: prevents malformed reranker calls; storage: excludes historical candidate payloads |
| `APP-PAPER-C-COST-PATTERNS` | methodology_reference | `reference_only` | `reference_only` | `preport` | time: avoids redesigning usage accounting; compute: enables preflight cap rejection; storage: keeps optimizer event payloads in App |
| `APP-PAPER-D-FROZEN-RESULTS` | frozen_evidence | `reference_only` | `reference_only` | `fixture` | time: provides parity anchors; compute: avoids historical reruns; storage: copies no metric payloads |
| `APP-PAPER-D-METHOD-LESSONS` | methodology_reference | `reference_only` | `reference_only` | `none` | time: preserves hard-won failure lessons; compute: avoids invalid oracle and MDE reruns; storage: no result duplication |
| `APP-PATEMBED-CONTROL` | dense_index | `reuse` | `conditional` | `pointer` | time: avoids secondary-control embedding generation; compute: saves a dense encoding pass; storage: keeps large embeddings in App |
| `APP-PUBLICATION-TOOLING` | publication_tooling | `adapt` | `conditional` | `pointer` | time: reuses QA and package structure; compute: reduces repeated render debugging; storage: references source assets without copying outputs |
| `APP-RETRIEVAL-ENGINEERING` | source_code | `adapt` | `conditional` | `preport` | time: avoids rediscovering FTS schemas; compute: avoids trial index builds; storage: negligible code-only port |
| `APP-SPARSE-FTS-INDEXES` | retrieval_index | `adapt` | `conditional` | `pointer` | time: avoids compatible index rebuilds; compute: avoids FTS population; storage: avoids roughly 0.9 GB of duplicate sparse indexes |
| `APP-WIKI-GRAPH-POINTERS` | project_knowledge | `reference_only` | `blocked` | `pointer` | time: preserves navigation context; compute: avoids unnecessary graph rebuilds; storage: keeps the one-megabyte graph in App |

## Known Gaps

- `GAP-B0-NEMOTRON` (`F1.1`): Locked B0 Nemotron artifact is absent from App - BGE-M3, Qwen, and patembed-base artifacts cannot replace Llama-Embed-Nemotron-8B revision aa3b43a495a9b280d1bdb716da37c54bb495d630.
- `GAP-CT-TRANSFER` (`CT.1`): PatenTEB transfer artifact and approval are absent - CT remains blocked by its G7 budget, license, and compatible-artifact requirements.
- `GAP-TRACK-S-ENGINES` (`S1.1`, `S1.2`, `S1.3`): Compatible SkillOpt, SkillOpt-Lite, and typed HarnessOpt engines are absent - Paper B GEPA code is reference-only and cannot execute the matched-budget Track S protocol.
