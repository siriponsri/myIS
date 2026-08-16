# ArmIndex Advisor Presentation

This is a minimal, offline-capable Reveal.js deck for an advisor update on A0 through A2. It is derived from the canonical report:

`docs/progress_report/ARMINDEX_A0_A1_A2_ADVISOR_PROGRESS_2026-08-16.md`

The deck uses only validated A1 REP-DEV figures. A2 is shown as a live controlled execution with results pending closeout; no A2 outcome, winner, or figure is projected.

## Build

From the repository root:

```powershell
.\scripts\build_armindex_advisor_presentation.ps1 -Build -Check
```

The command creates the ignored, portable bundle at:

```text
docs/presentation/dist/index.html
```

The build copies the two authoritative A1 PNG figures and the vendored Reveal.js runtime into `dist/`, then writes an SHA-256 manifest. It requires no network access after this repository checkout.

## Preview

```powershell
.\scripts\build_armindex_advisor_presentation.ps1 -Serve -Port 8765
```

Open `http://127.0.0.1:8765`. The deck uses Reveal.js keyboard navigation and can be presented entirely from the local bundle.

## Evidence Boundary

- A0 is engineering/reproducibility evidence, not retrieval evidence.
- A1 is measured aggregate evidence on REP-DEV, not Selection or Final.
- A2 outcomes remain unavailable until exact coverage, safe return, execution closeout, and independent result-integrity audit pass.
- The deck contains no qrels, membership, raw identifiers, rankings, per-query outcomes, credentials, or raw provider payloads.
