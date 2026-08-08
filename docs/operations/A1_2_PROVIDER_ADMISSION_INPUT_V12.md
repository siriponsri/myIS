# A1.2 Provider Admission Input v12

This local-only validator checks the shape of a future sanitized provider
identity and all-fee quote. It does not contact Vast, authenticate, reserve a
GPU, open SSH, adopt execution, or start retrieval. Every accepted synthetic or
Owner-local input remains `PENDING_LIVE_PROVIDER` with all execution authority
locked.

The input intentionally records only `instance_identity_sha256` and
`gpu_uuid_set_sha256`. Never include raw instance IDs, endpoints, SSH details,
credentials, qrels, split membership, query IDs, paths, or provider payloads.

The validator requires one Vast topology with four RTX 3090 GPUs, approximately
24 GiB VRAM per GPU, 16 vCPU, 64 GiB RAM, 250 GiB free disk, linux/amd64, and
the frozen PyTorch/CUDA image identity. Every fee field is mandatory and the
identity and quote must be no older than 900 seconds when evaluated.

Prepare the sanitized JSON outside Git, then run:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_provider_admission_input_v12 --repository-root . --input <SAFE_OWNER_LOCAL_INPUT_JSON>
```

A local validation PASS only means the candidate conforms to the frozen shape.
It is neither live admission nor authorization: `provider_contact_allowed`,
`launch_allowed`, and `adopted_for_execution` remain false. A later separately
authorized live-adoption goal must evaluate the real fresh quote against the
whole-workload budget contract and preserve provider destruction capability.
