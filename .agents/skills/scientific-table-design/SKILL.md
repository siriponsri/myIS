---
name: scientific-table-design
description: Use when creating, revising, auditing, or compressing scientific tables for IEEE/iSAI-NLP or World Patent Information manuscripts, especially benchmark comparisons, ablations, dataset summaries, error taxonomies, and patent/NLP evaluation results.
---

# Scientific Table Design

## Purpose
A table is for exact values and structured comparison.
If the reader needs a trend, consider a figure.
If only one or two numbers matter, consider prose.

## Start with the question
Write the one sentence the table answers.
Delete columns/rows that do not help answer it.

## Structure
Prefer:
- methods/conditions in meaningful groups;
- metrics in stable order;
- explicit split/domain labels;
- units in headers;
- compact abbreviations defined in caption/footnote;
- consistent precision.

Avoid:
- decorative shading;
- vertical-rule clutter;
- repeated text in every row;
- unnecessary decimals;
- columns containing one repeated value;
- bolding many cells.

## Emphasis
Bold/underline only when the comparison is fair and the meaning is explained.
Do not visually declare a winner across incomparable settings.

## Patent/NLP-specific tables
Common useful tables:
- dataset/query split summary;
- retrieval vs reranking performance;
- IN vs OUT domain result;
- ablation;
- efficiency/cost/runtime;
- error categories;
- claim-evidence summary for internal review only.

## Space economy
For a six-page IEEE paper:
- merge related metrics;
- abbreviate long method names consistently;
- move implementation trivia to prose;
- use a two-column table only if a one-column version is genuinely unreadable;
- delete low-value baselines rather than shrinking text below readable size.

## Caption
Caption must state:
- what is compared;
- split/setting;
- metric direction if ambiguous;
- special markers;
- statistical/averaging convention when relevant.

## QA
Check:
- final-size readability;
- overflow;
- decimal alignment;
- fair precision;
- missing baselines;
- inconsistent denominators/splits;
- caption-table agreement;
- values match source artifacts.
