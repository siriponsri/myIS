# ArmIndex Advisor Presentation

This is a minimal, offline-capable Reveal.js deck for an advisor update on A0 through A3 planning. It is derived from the canonical report:

`docs/progress_report/ARMINDEX_A0_A1_A2_ADVISOR_PROGRESS_2026-08-16.md`

The deck uses validated A1 REP-DEV and A2 aggregate closeout figures. A2 is
closed with exact `52 = 44 measured + 8 dormant` accounting, three primary
transfer inputs, and two diagnostic no-winner ties. It does not make Selection
or Final claims.

## Updating the A2 snapshot

Append or revise A2 slides only from the aggregate-safe closeout projection,
receipts, and figure manifest. Use `DORMANT_CONDITIONAL_RESERVE` for a reserve candidate that was
not evaluated by the frozen admission rule; do not present it as a zero, null,
or failed metric.

All on-slide prose is English. The build check rejects Thai Unicode characters
in the deck source to prevent mixed-language regressions.

## Build

From the repository root:

```powershell
.\scripts\build_armindex_advisor_presentation.ps1 -Build -Check
```

The command creates the ignored, portable bundle at:

```text
docs/presentation/dist/index.html
```

The build copies the authoritative A1/A2 PNG figures and the vendored Reveal.js runtime into `dist/`, then writes an SHA-256 manifest. It requires no network access after this repository checkout.

## PowerPoint

Build the editable advisor deck and its inspection record from the same
receipt-bound A2 figures:

```powershell
.\scripts\build_armindex_advisor_talk_pptx.ps1
```

The deck is written to
`docs/presentation/ArmIndex_Advisor_Talk_A0_A3_2026-08-18.pptx`. The builder
rasterizes the local explanatory SVGs, embeds validated A1/A2 figure assets,
and records an object-level inspection beside the deck. Use
`-KeepBuildArtifacts` only while inspecting the ignored build workspace.

## Preview

```powershell
.\scripts\build_armindex_advisor_presentation.ps1 -Serve -Port 8765
```

Open `http://127.0.0.1:8765`. The deck uses Reveal.js keyboard navigation and can be presented entirely from the local bundle.

## Evidence Boundary

- A0 is engineering/reproducibility evidence, not retrieval evidence.
- A1 is measured aggregate evidence on REP-DEV, not Selection or Final.
- A2 outcomes are aggregate development evidence after exact coverage, safe return, execution closeout, and independent result-integrity audit pass.
- A3 Extended remains pending a fresh hash-bound Train-250 query/corpus/evaluator package and must use ARM-03/04/05 only.
- The deck contains no qrels, membership, raw identifiers, rankings, per-query outcomes, credentials, or raw provider payloads.
