# myIS Naming Rules

## 1. Principles

Names must be:

- deterministic;
- short enough to scan;
- stable across machines;
- independent of model marketing names and metric results;
- safe for POSIX paths, URIs, MLflow, and JSON;
- sufficient to trace a result through its manifest.

Use IDs for identity and manifests for detail. Do not encode the entire experiment in a filename.

## 2. Style

| Surface | Style | Example |
|---|---|---|
| Python package/module | `snake_case` | `family_aggregate.py` |
| Python class | `PascalCase` | `RepresentationCompiler` |
| Python function/variable | `snake_case` | `build_claim_graph` |
| Config and schema key | `snake_case` | `max_units_per_family` |
| Ordinary directory | `lowercase-kebab-case` | `candidate-workspaces/` |
| Ordinary Markdown file | `UPPERCASE.md` only for canonical root contracts; otherwise `lowercase-kebab-case.md` | `AGENTS.md`, `patent-structure.md` |
| Experiment ID | lowercase kebab case | `exp-20260730-structure-pilot` |
| JSON/YAML enum | lowercase snake case | `claim_block_unparsed` |

Do not use spaces, personal names, initials, or workstation names in machine identifiers.

## 3. Canonical root filenames

These names are fixed:

- `README.md`
- `PLAN.md`
- `INSTRUCTION.md`
- `NAMING.md`
- `AGENTS.md`
- `pyproject.toml`
- `uv.lock`

Supporting documents under `docs/` use the names defined in `docs/ARCHITECTURE.md`.

## 4. Dataset and split IDs

### Dataset snapshot

```text
<dataset>-<yyyymmdd>-<sha8>
```

Example:

```text
dapfam-20260730-b5ad91a6
```

The full repository revision, URLs, file sizes, and SHA-256 values belong in the dataset manifest.

### Split

```text
s<seed>-tr<train>-se<selection>-fi<final>-v<version>
```

Canonical initial split:

```text
s42-tr250-se125-fi872-v1
```

Do not include query IDs in filenames.

## 5. Protocol IDs

```text
<dataset>-family-<query-view>-to-<corpus-view>-v<version>
```

Examples:

```text
dapfam-family-tac-to-full-v1
dapfam-family-ta-to-tac-v1
```

Allowed compact view tokens:

- `ta`: title + abstract
- `tac`: title + abstract + claims
- `full`: title + abstract + claims + description

Results from different protocol IDs must not be merged into one leaderboard.

## 6. Representation IDs

```text
rep-<family>-v<two-digit-version>
```

Examples:

```text
rep-flat-v01
rep-structopt-v03
rep-structopt-v03-frozen
```

`family` describes the method, not its score. Candidate IDs are separate:

```text
cand-i<iteration>-c<candidate>
```

Examples:

```text
cand-i01-c01
cand-i03-c02
```

The manifest maps each candidate to its parent, specification hash, frozen compiler hash, hypothesis, and representation ID.

SCOPE-DSL specification:

```text
spec-<family>-v<two-digit-version>
```

Examples:

```text
spec-flat-v01
spec-claim-path-v02
```

Compiler:

```text
compiler-scope-v<two-digit-version>
```

The compiler ID changes only when executable compiler behavior changes. A candidate iteration changes the specification ID, not the compiler ID.

## 7. Retriever and policy IDs

Retriever:

```text
ret-<kind>-v<two-digit-version>
```

Examples:

```text
ret-bm25-v01
ret-dense-v01
ret-hybrid-v01
```

Policy:

```text
pol-<family>-v<two-digit-version>
```

Examples:

```text
pol-fixed-v01
pol-skillopt-v01
```

Provider, model, weights, tokenizer, and parameter details belong in the run manifest.

## 8. Experiment and run IDs

Experiment:

```text
exp-<yyyymmdd>-<short-purpose>
```

Example:

```text
exp-20260730-structure-pilot
```

Run:

```text
<utc-basic-time>__<stage>__<representation>__<retriever>__s<seed>__r<two-digit-repeat>
```

Example:

```text
20260730T091530Z__train__rep-structopt-v03__ret-bm25-v01__s42__r01
```

Use UTC in run IDs even when human reports show Asia/Bangkok time.

Allowed stage tokens:

- `smoke`
- `train`
- `selection`
- `transfer`
- `final`
- `report`

## 9. Freeze IDs

```text
freeze-<yyyymmdd>-<short-sha>
```

Example:

```text
freeze-20260814-a91c4e2d
```

A freeze manifest binds code, config, schemas, data snapshot, split, evaluator, representation, retriever, policy, prompts, models, environment, and dependency lock.

## 10. Metric names

Use the canonical structured form:

```text
<metric>_at_<k>/<scope>
```

Examples:

```text
recall_at_100/out
recall_at_100/all
ndcg_at_100/in
```

Additional canonical names:

```text
index/units_per_family_mean
index/bytes_total
latency/query_p50_ms
latency/query_p95_ms
parser/claim_parse_rate
parser/description_section_rate
parser/fallback_rate
provenance/grounded_unit_rate
cost/usd
```

Use lowercase scope tokens: `all`, `in`, and `out`.

Never put metric values in filenames.

## 11. Artifact names

Inside an external run directory:

```text
manifest.json
metrics-summary.json
metrics-per-query.parquet
rankings.parquet
parser-report.json
cost-report.json
audit-report.json
logs.jsonl
```

Representation artifacts:

```text
representation-spec.json
compiler-manifest.json
representation-sample.jsonl
index-manifest.json
```

Freeze artifacts:

```text
freeze-manifest.json
environment.json
dependency-lock.sha256
source-tree.sha256
```

Generated reports:

```text
<run-id>-summary.md
<run-id>-failure-analysis.md
<freeze-id>-final-report.md
<freeze-id>-presentation.pptx
```

iSAI-NLP submission artifacts:

```text
reports/submissions/isai-nlp-2026/isai-nlp-2026-anonymous-v01.pdf
reports/submissions/isai-nlp-2026/isai-nlp-2026-anonymous-v01.sha256
reports/submissions/isai-nlp-2026/isai-nlp-2026-compliance-v01.json
reports/submissions/isai-nlp-2026/isai-nlp-2026-camera-ready-v01.pdf
```

The review artifact must use `anonymous`; do not encode author names or institutions in its path or metadata. The camera-ready artifact is created only after acceptance and `D3`.

## 12. Source-span IDs

```text
<family-id>:<field>:<start>-<end>
```

Example:

```text
fam-00123:claims_text:481-903
```

Node IDs are local to one family record:

```text
n-<node-type>-<four-digit-index>
```

Examples:

```text
n-claim-0001
n-limitation-0007
n-passage-0012
```

Searchable unit IDs:

```text
u-<view-type>-<two-digit-index>
```

Examples:

```text
u-core-01
u-claims-01
u-support-01
```

## 13. Filesystem boundaries

Repository paths are relative to the Git root. External artifacts are relative to `MYIS_STORE`.

Never:

- embed absolute machine paths in committed configs;
- use a home directory as a recursive output target;
- store qrels, raw corpora, models, indexes, or MLflow databases in Git;
- use unresolved globs for deletion;
- name an artifact `final`, `new`, `best`, or `latest` without a stable ID.

Symlinks or pointer manifests may connect Git reports to external artifacts, but the manifest remains authoritative.

## 14. Supersession

Do not overwrite immutable results.

For a correction:

1. create a new version or run ID;
2. record `supersedes` in the new manifest;
3. mark the old record `superseded`;
4. preserve the old artifact and reason.

Human-readable indexes may point to the current recommended result, but they must not erase history.

## 15. Quick validation

Before accepting a new identifier:

- matches the documented pattern;
- contains no score, secret, personal name, or machine path;
- is unique in its registry;
- resolves to a manifest;
- uses UTC when time is encoded;
- does not claim `frozen` without a freeze manifest.
