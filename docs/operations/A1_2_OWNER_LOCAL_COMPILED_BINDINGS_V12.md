# A1.2 Owner-Local Compiled Bindings V12

## Purpose and boundary

V12 is an additive, Owner-local receipt contract for the 25 frozen A1.2
program-arm bindings. It does not change v11, create a provider authorization,
or make any scientific result. The protected corpus, query text, qrels, split
membership, identity map, model bytes, credentials, and private keys remain
outside Git and outside every generated projection.

The receipt records only hashes and aggregate counts. A `PASS` from this tool
means the binding receipt is structurally complete; it does not adopt v11,
open Vast, or start measured retrieval.

## What the receipt binds

There are exactly five logical programs for each of five arms, for 25 logical
bindings. `P04-SECTION-MULTIVIEW` has three physical views but remains one
logical binding per arm. Every completed binding supplies the frozen v11
request/program/compiler hashes, its arm's model-lock and tokenizer hash, an
adapter-contract hash, the compiled-representation and index hashes, and
aggregate counts.

The validator rejects a missing or duplicate matrix member, model/tokenizer or
compiler drift, a coverage gap, omitted unit, truncation, rendered input over
its effective input limit, protected payload key, credential-like value, or
absolute personal path.

## Owner command

From the repository root, create the pending template in the external
Owner-local protected store. The command deliberately refuses a repository
output path.

```powershell
$OwnerRoot = Join-Path (Resolve-Path '..') '04_Owner_Stores\a1.2-vast-20260806'
$BindingReceipt = Join-Path $OwnerRoot 'receipts\A1_2_COMPILED_BINDINGS_V12.json'

uv run --no-sync python -m myis_research.armindex.a1_2_compiled_bindings_v12 template `
  --repository-root . `
  --output $BindingReceipt
```

The output starts as `pending_owner_local_protected_compilation` with all 25
expected pairs and no completed binding. Do not change that status merely to
continue. Inside the protected Owner-local evaluator workflow, replace the
null receipt hashes and empty bindings only after compiling the frozen corpus
under run-scoped opaque tokens and measuring every rendered input with the
frozen arm tokenizer/adapter.

For each binding, record only the fields required by
`control/owner-local/a1.2-compiled-program-bindings-contract.v12.json`.
Set `coverage_gap_count`, `omitted_unit_count`, `truncation_count`, and
`overlength_count` to zero only when the protected workflow has verified those
facts. Compute `binding_set_sha256` as canonical SHA-256 of the whole object
excluding that field.

Validate the finished Owner-local receipt without copying it into Git:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_compiled_bindings_v12 validate `
  --repository-root . `
  --binding-set $BindingReceipt
```

## Required result

The completed receipt must report
`validated_owner_local_protected_compilation`, exactly 25 actual bindings,
and seven non-null Owner-local receipt hashes. It remains an adoption input.
Each dense binding must use the exact model-lock context limit and the frozen
adapter-contract and tokenizer hashes. ARM-01 has no neural context window, so
its `effective_input_limit` must equal the measured maximum rendered lexical
token count rather than an invented larger ceiling.

The distinct later adoption goal must still bind the clean execution
commit/tree and bundle, fresh provider identity and all-fee quote,
whole-workload budget admission, and watchdog/provider-destroy dry-run.
