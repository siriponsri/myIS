# myIS Research

This repository is the governed research workspace for the myIS publication
program. It keeps evidence, research choices, experiment definitions, outputs,
and reusable code separate from the product application and the shared Brain.

## Start here

1. Read [PLAN.md](PLAN.md) for the phased research plan and track flows.
2. Read [AGENTS.md](AGENTS.md) before changing or running anything.
3. Use [00_governance/OPERATIONS.md](00_governance/OPERATIONS.md) for routine
   commands and Owner gates.
4. Open only the numbered folder that owns the work.

## Repository map

| Path | Purpose |
|---|---|
| `00_governance/` | Authority, gates, operating rules, templates, and tool pins |
| `01_evidence/` | Literature catalog, local-only tiered PDFs, digests and provenance |
| `02_tracks/` | Candidate exposure/HarnessOpt, ranking/evidence and optional skill evolution |
| `03_experiments/` | Configurations, manifests, and local runtime placeholders |
| `04_outputs/` | Generated reports, diagrams, and approved result packages |
| `05_code/` | Validation, bootstrap, library, and tests |

Numbering is limited to managed navigation boundaries. Third-party tools,
Python packages, the App repository, and the Obsidian Brain keep their native
internal names.

<!-- mermaid-id: 00-01-project-architecture -->
```mermaid
flowchart LR
    accTitle: myIS project architecture
    accDescr: The application supplies canonical source evidence, Research governs scientific work, the Brain records readable decisions, and MLflow stores experiment lineage.

    App["App: product and frozen historical evidence"] --> Evidence["Research literature and evidence"]
    Evidence --> Tracks["C/H, R and optional S tracks"]
    Tracks --> Experiments["Governed experiments"]
    Experiments --> Outputs["Publication outputs"]
    Tracks --> Brain["Obsidian Brain: decisions and status"]
    Experiments --> MLflow["MLflow: run lineage"]

    classDef source fill:#F1F3F5,stroke:#667085,color:#17222B
    classDef research fill:#DDF4EF,stroke:#0F766E,color:#17222B
    classDef control fill:#FCE8E3,stroke:#C95D42,color:#17222B
    classDef record fill:#FFF3CD,stroke:#B7791F,color:#17222B
    class App source
    class Evidence,Tracks,Experiments,Outputs research
    class Brain control
    class MLflow record
```

## Current boundary

The numbered filesystem cutover is complete and F0 implementation is active.
Full U041-U153 PDF triage, offline fixtures, local bootstrap checks, code and
notebook validation are Owner-authorized. Existing U001-U040 digests and 64
import artifacts remain frozen and hash-validated. Paid/API/GPU/Vast jobs,
scientific development runs and prospective-confirmation access remain separate
R3/R4 gates.

The minimal active tool stack is HyperResearch, MLflow, one Obsidian Brain,
Codex native live search, Claude Open-WebSearch, and Context7. Open Deep
Research and Experience Brain are retired from active operation. Loop
Engineering and Open Code Review are evaluation-only tools and may run only in
a disposable pilot workspace.

## Repositories

| System | Target workspace path | Role |
|---|---|---|
| App | `00_Projects/00_myIS/00_App/` | Product code and canonical historical evidence |
| Research | `00_Projects/00_myIS/01_Research/` | This repository |
| Brain | `00_Projects/00_myIS/02_Brain/` | Human-readable shared decisions and status |

See [00_governance/RESTRUCTURE_STATUS.md](00_governance/RESTRUCTURE_STATUS.md)
for completed cutover evidence and the remaining implementation/audit work.

## Brain-drive contract demo

`03_experiments/V01_brain_drive_agent_demo/` is a deterministic offline test of
PDF, web-pointer, and project-history registration, fixture retrieval,
synthesis, structlog runtime/progress events, the local MLflow mirror, immutable
manifest validation and a paper-table projection. It does not copy raw sources
into Brain and does not use network, paid API, GPU, or protected data.

The implementation is under `05_code/src/myis_research/`. External execution
remains gated: HyperResearch is Claude-only after an Owner decision, while the
Autoresearch adapter is pinned to upstream commit
`228791fb499afffb54b46200aca536f79142f117` and records hypothesis, patch,
command, metrics, artifacts, and decision.
