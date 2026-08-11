---
title: "A1.2 rerun goal: ปิด common screen 25/25 แบบ long run"
phase_id: A1_BASELINES_AND_MULTI_ARM_SCREENING
task_id: A1.2
status: CLOSED_PASS
lifecycle: CLOSED
evidence_class: aggregate_safe_terminal_handoff
scientific_authority: false
claim_boundary: "goal นี้เป็นเอกสารส่งต่อ; authority อยู่ที่ terminal receipt, evaluator closeout และ aggregate result summary ของ attempt r15"
last_material_update: 2026-08-12
next_authorized_action: START_A2_IN_FRESH_SESSION_FROM_A2_GOAL
---

# A1.2 rerun: คู่มือให้ Luna Max ทำงานจนจบ

goal นี้ปิด `PASS` แล้ว ห้ามใช้เพื่อ launch หรือ rerun A1.2 งานถัดไปให้เริ่มจาก:

```text
/goal อ่าน docs/goal/A2_goal.md ตรวจ A1 terminal PASS แล้วทำงานตามขั้นตอนทั้งหมด โดยทำ fresh A2 provider admission/execution adoption และใช้ remote root ใหม่
```

ทำตามหมายเลขเรียงลำดับ ห้ามข้าม checkpoint เพื่อประหยัดเวลา หากเกิด hard
stop ให้หยุดแบบ fail-closed เก็บเฉพาะหลักฐาน aggregate-safe แล้วรายงาน blocker
เดียว ไม่เริ่ม A2, HARNESS-DEV, Selection หรือ Final ใน goal นี้

checkpoint ในเอกสารนี้เป็นจุดตรวจ/บันทึกความคืบหน้า ไม่ใช่ micro-gate ใหม่
อำนาจ launch และ measured work ยังมาจาก canonical receipts และ execution
contract เท่านั้น

## สถานะดำเนินงานปัจจุบัน

ตารางนี้เป็น progress projection จาก Owner-local ledger/checkpoint ของ attempt
`a12-v16-20260811-r15`; receipt และ artifact ที่ hash-bound ยังเป็น authority
ห้ามใช้ตารางนี้แทนผล evaluation

| ช่วงงาน | สถานะ | หลักฐาน/สิ่งที่เหลือ |
|---|---|---|
| ขั้น 0 ล็อกขอบเขตและ attempt | `COMPLETE` | attempt, instance และ remote root ใหม่ถูกบันทึกแล้ว |
| ขั้น 1 audit/repair engineering | `COMPLETE` | reliability path และ focused validation ผ่านโดยไม่เปลี่ยน frozen science |
| ขั้น 2 clean frozen bundle | `COMPLETE` | commit/tree/bundle hash ถูก bind ใน admission/adoption |
| ขั้น 3 provider admission | `COMPLETE` | authenticated provider identity, fresh all-fee quote และ v17 budget PASS |
| ขั้น 4 SSH/runtime/protected adoption | `COMPLETE` | SSH, 4xRTX3090, runtime, 48/48 model files และ protected boundary PASS |
| ขั้น 5 watchdog/TTL | `COMPLETE` | watchdog generation `r15-repair2` PASS และยัง active |
| ขั้น 6 Owner-local input manifest | `COMPLETE` | manifest READY, 25 cells และ 150 work tokens |
| ขั้น 7 execution adoption | `COMPLETE` | measured execution เปิดเฉพาะ attempt r15 แล้ว |
| ขั้น 8 common screen | `COMPLETE` | Owner-local ledger checkpoint ยืนยัน 25/25; ทุก arm = 5/5, dense worker success = 4/4, failure marker = 0 |
| ขั้น 9 bounded recovery | `COMPLETE` | transient SSH watchdog failure ถูกเก็บไว้และ recovery ไม่ restart measured workers |
| ขั้น 10 safe return | `COMPLETE` | production safe-return receipt เป็น `PASS`, archive ครบ 25 cells และ hash ของ archive/manifest ผ่านการตรวจ |
| ขั้น 11 frozen evaluation/promotion | `COMPLETE` | evaluator closeout `PASS`, aggregate receipts ครบ 25 และ deterministic promotion เลือก 3 arms |
| ขั้น 11E journal/presentation EDA | `COMPLETE` | EDA package ครบ 25 cells, local handoff 7 files และ remote mirror 8 files ผ่าน |
| ขั้น 11A A2 baseline handoff | `COMPLETE` | local handoff 28 source files และ remote mirror 29 files ผ่าน; `a2_execution_authorized=false` |
| ขั้น 12 terminal closeout/provider disposition | `COMPLETE` | terminal receipt `PASS`, ค่าใช้จ่ายรวม `$11.161632`, provider disposition `REUSE_ELIGIBLE`, remote mirrors `29/29 + 8/8 + 12/12` ผ่าน และ A2 ยังไม่เริ่ม |

ทุกขั้นของ goal นี้ปิดแล้ว ห้ามแก้สถานะกลับเป็น active หรือรวม partial attempt เก่า
เข้ากับผลนี้ งานถัดไปใช้ `A2_goal.md` และต้องทำ fresh A2 admission/adoption

## 1. เป้าหมายและคุณค่าต่อ publication

ตอบคำถามเดียวของ A1.2: ภายใต้ split, model, evaluator, cost และ protocol เดิม
representation programs `P00`-`P04` ทำให้ arm ใดมี candidate exposure บน REP-DEV
ที่ตรวจซ้ำได้ดีกว่า arm อื่นหรือไม่ ผลงานที่มีคุณค่าต่อ journal ต้องมี coverage
ครบ, provenance/hash ครบ, comparison แบบ matched protocol และ claim ที่ไม่เกิน
หลักฐาน ไม่เลือกเฉพาะผลที่ดูดี

ความสำเร็จเชิง execution คือหนึ่ง attempt ที่ admissible และมีครบ `25/25`
logical cells (5 arms x 5 programs) ใน attempt เดียว จากนั้นจึง safe-return,
Owner-local evaluation, aggregate receipts และ deterministic promotion ได้
ความสำเร็จเชิงวิทยาศาสตร์ยังไม่สามารถประกาศจากคู่มือนี้จนกว่า evaluator จะผ่าน

## 2. สถานะเริ่มต้นที่ต้องยึด

- `a12-v16-20260810-r13` เป็น failure evidence เท่านั้น: ได้ `24/25`, ARM-05
  ได้ `4/5`, watchdog เป็น `HARD_STOP/ssh_runtime_probe_failed`
- instance `47256937` ถูก Owner destroy แล้ว และ endpoint เดิมตรวจได้
  `connection_refused`; ห้าม reuse และห้ามรวม partial cells จาก r13
- audit aggregate-safe อยู่ที่
  `outputs/audits/armindex/a1.2-v16-r13-failure-audit-20260810.json`
- pre-admission audit ล่าสุดยืนยันว่า bundle ที่ freeze, assets ที่จะ transfer,
  wheelhouse/model checksums และ v15 protected bindings `25/25` ยังผ่าน; ดู
  `outputs/audits/armindex/a1.2-owner-local-transfer-readiness-20260810.json`
  ห้ามใช้ audit นี้แทน fresh provider admission หรือ execution adoption
- v17 Owner-approved limits ปัจจุบัน: common screen `$55`, A1 `$60`, campaign
  `$150`, TTL `40h`; ค่า v15 `$18/$23/$100` และ v16 `$27/$32/$150`
  เป็น historical เท่านั้น
- A1.1 complete, A2 และทุก phase หลัง A1 ยังปิดอยู่

ถ้าไฟล์ canonical ขัดกับข้อความนี้ ให้ยึด canonical receipt/control และบันทึก
conflict เป็น blocker แทนการเดา

## 3. Frozen science และขอบเขตการแก้

ห้ามเปลี่ยน v11-v15 semantics: split, qrels, membership, query reservation,
query IDs, programs, P02-FIRST-CLAIM boundary, dense-overflow composition,
tokenizer/model revision, evaluator metrics, candidate rule และ promotion rule
รวมถึงห้ามเปลี่ยน protected-data boundary, model weights หรือ claim boundary

อนุญาตเฉพาะ engineering ที่มีหลักฐานจาก r13 หรือ focused test รองรับ เช่น
SSH retry/backoff, watchdog/TTL liveness, worker lifecycle, checkpoint/resume,
safe-return collection, exact-token-ID transport และการอัปเดต source hashes กับ
`contract_sha256` ให้ตรง bytes จริง การแก้ทุกครั้งต้องมี test หรือ validation
ชี้ชัดว่าแก้ reliability ไม่ได้ปรับ outcome

## 4. ตัวแปรและพื้นที่ทำงาน

กำหนดค่าต่อไปนี้ใน Owner-local shell/secret store เท่านั้น ห้ามใส่ค่าจริงใน Git
หรือรายงาน:

```text
REPO=<01_Research root>
INSTANCE_ID=<Owner-provisioned Vast instance id>
SSH_HOST=<fresh public ip or hostname>
SSH_PORT=<fresh direct SSH port>
SSH_KEY=<Owner-local ed25519 key path>
ATTEMPT_ID=a12-v16-<UTC date>-<unique suffix>
OWNER_ROOT=<Owner-local protected input/output root>
REMOTE_ROOT=/opt/myis/<unique-a12-root>
EXTERNAL_ROOT=<Owner-local protected root outside the repository and outside synced/cloud folders>
```

ใช้ `ATTEMPT_ID` เดียวกันทุก receipt, manifest, lifecycle และ archive ห้ามใช้
directory ของ r13 หรือเขียน output ทับไฟล์ immutable เดิม

## 5. ขั้นตอนปฏิบัติแบบ numbered

### ขั้นที่ 0: อ่านและล็อกขอบเขต

1. อ่าน `AGENTS.md`, `PLAN.md`, `HANDOFF.md`, เอกสารนี้,
   `control/execution-envelope.yaml`, `control/execution-envelope-a1.2-v1.yaml`,
   `control/execution-envelope-a1.2-v2.yaml`,
   `control/runbooks/A1_2_GOVERNED_LONG_RUN_V16.md` และ audit r13 เฉพาะส่วนที่
   เกี่ยวข้อง โดยถือ envelope หลักเป็น safety/history mapping และ A1.2 v1/v2
   เป็น preserved topology lineage เท่านั้น; ค่า `launch_allowed=false` เดิม
   ห้ามแก้หรือใช้แทน fresh v16 admission/adoption ของ attempt ใหม่
2. ตรวจ `git status --short` และจด commit/tree ที่เป็นฐาน ห้ามทำ historical
   document sweep ก่อน measured path พร้อม หาก worktree มีการแก้ของ Owner หรือ
   งานอื่น ให้คงไว้ ห้าม reset, checkout, stash หรือ commit ข้ามขอบเขต ให้สร้าง
   clean disposable worktree/branch จาก `origin/main`, apply เฉพาะ reliability
   patch ที่จำเป็นใน worktree นั้น, test, commit/push แล้วจึงสร้าง worktree ใหม่
   จาก pushed commit สำหรับ bundle
3. ตรวจว่า A2/Selection/Final ยัง closed และ measured counter ของ attempt ใหม่
   ยังเป็นศูนย์

**Checkpoint 0:** มี attempt id ใหม่, ขอบเขต frozen ถูกบันทึกใน ledger และไม่มี
credential/protected payload ถูกอ่านออกสู่ log หากไม่ผ่านให้หยุด

### ขั้นที่ 1: audit reusable assets และแก้ reliability เท่าที่จำเป็น

1. ตรวจ source bindings ใน `control/armindex/a1.2/engineering-execution-contract.v16.json`
   เทียบ SHA-256 กับไฟล์ v16 ปัจจุบัน และบันทึก campaign revision, preserved
   A1.2 envelope v1/v2, scientific request v11, adoption inputs v15,
   engineering contract v16 และ budget extension/profile v16 พร้อม SHA-256
   ลงใน ledger/receipts ของ attempt ห้ามใช้ envelope P0/P1 CPU-only เป็น live
   A1 launch authority
2. ตรวจ reusable bundle, remote bootstrap, wheelhouse/model manifests และ
   checkpoint code ที่ยัง valid; ห้าม rebuild frozen scientific bundle จากผลลัพธ์
3. ถ้ามี drift ให้แก้เฉพาะ engineering file ที่เกี่ยวข้อง เพิ่ม focused test
   แล้วคำนวณ `contract_sha256` ใหม่ด้วย canonical JSON; ห้ามแก้ v11-v15 hash
4. รันชุดเล็กก่อน:

```powershell
uv run --no-sync python -m pytest -q `
  tests/test_armindex_a1_2_engineering_execution_bundle_v16.py `
  tests/test_armindex_a1_2_measured_executor_v16.py `
  tests/test_armindex_a1_2_raw_materializer_bridge_v16.py `
  tests/test_armindex_a1_2_execution_lifecycle_v16.py
```

**Checkpoint 1:** focused tests ผ่าน, contract self-hash ผ่าน และ diff ทุกบรรทัด
อธิบายได้ว่าเป็น reliability/transport เท่านั้น หาก test ไม่ผ่านให้ repair หรือ
fail-closed; ห้าม launch เพื่อดูว่า outcome จะดีขึ้นหรือไม่

### ขั้นที่ 2: ทำ clean pushed bundle

bundle ที่ใช้สำหรับ attempt ถัดไปถูก freeze แล้วที่ commit `69a056f7`, tree
`e18bb967f6857e5d913d13170ef2bbc44cf73a8f` และ SHA-256
`70077bfdbd7f821dc0ec67f99df90cdffe962f011ced3c3da2d50d76dd2e1bf5` ตาม
pre-admission audit ข้างต้น หาก `HEAD` ใหม่กว่าเพราะมีเฉพาะ goal/audit/report
aggregate-safe หลังสร้าง bundle ให้ตรวจ bundle จาก clean detached worktree ที่
commit นี้และใช้ receipt เดิม ห้าม rebuild หรือ substitute bundle เพียงเพื่อให้
ตรงกับ doc-only `HEAD`

1. หาก `read_model.py`, `report_records.py` หรือ canonical failure receipt เปลี่ยน
   ให้รัน generated report sync/check จาก read-model เดียวก่อน commit; อัปเดต
   เฉพาะ generated sinks ที่ drift และห้ามแก้ note generated ด้วยมือ
2. รัน `git diff --check` และ scoped Ruff ก่อน commit
3. หลัง reliability patch ถูก commit/push แล้ว ให้สร้าง disposable clean
   worktree ใหม่จาก updated `origin/main` และตรวจ bundle พร้อมใช้งานจาก
   commit/tree นั้นเท่านั้น:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_engineering_execution_bundle_v16 validate-ready --repository-root .
uv run --no-sync python -m myis_research.armindex.a1_2_engineering_execution_bundle_v16 bundle-paths --repository-root .
```

4. commit/push เฉพาะ engineering/control ที่จำเป็น, generated projection ที่
   sync ตรวจพบว่าจำเป็น และ docs goal นี้ตาม policy
   โดยห้ามรวม unrelated user changes; หาก clean pushed tree ทำไม่ได้ให้หยุด
   ก่อน provider admission และรายงาน blocker เดียว
5. ตรวจ `git status --short` ว่า clean และ `git rev-parse HEAD` ตรงกับ
   `origin/main`; สร้าง tar bundle และ receipt ไปที่ `EXTERNAL_ROOT` เท่านั้น:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_engineering_execution_bundle_v16 build-bundle `
  --repository-root . `
  --output <EXTERNAL_ROOT>/a12-v16-bundle-<hash>.tar.gz `
  --receipt-output <EXTERNAL_ROOT>/a12-v16-bundle-receipt.json
```

**Checkpoint 2:** bundle, manifest, commit, tree และทุก source hash ตรงกัน
ห้ามแก้ repository หลังสร้าง bundle; ถ้าต้องแก้ให้กลับไปขั้นที่ 1 และสร้าง
attempt/bundle ใหม่ตามกติกา immutable

### ขั้นที่ 3: fresh provider admission (ยังไม่วัด)

รอ Owner provision/approve instance แล้วเลือก provider observation mode เดียว
ตลอด attempt:

1. Preferred `AuthenticatedCli`: อ่านด้วย `vastai show instance $INSTANCE_ID
   --raw` ภายในตัวเก็บผลที่ parse/allowlist ใน memory เท่านั้น ห้ามปล่อย stdout
   เข้า transcript หรือ log
2. Fallback `OwnerDashboardSsh`: ใช้เมื่อ Vast TFA/API ใช้ไม่ได้และ Owner ยืนยัน
   ให้ใช้ SSH-only โดยส่งเฉพาะ instance ID, running/verified, total all-fee rate,
   provision/TTL time, dashboard evidence SHA-256 และ
   `OWNER_MANUAL_DASHBOARD_DESTROY_READY`; bind กับ pinned SSH hostname/runtime/
   GPU UUID-set hash ห้ามอ้าง `provider_authenticated=true` และห้ามเรียก API
   destroy อัตโนมัติ

ทั้งสอง mode เขียนเฉพาะ aggregate-safe provider receipt และ sanitized budget
input ใน `OWNER_ROOT`; ใช้ v17 whole-workload evaluator เป็น authority ของ
`40h/$55/$60/$150` โดยรวมค่าใช้จ่าย aggregate ของ attempt ก่อนหน้า:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_whole_workload_budget_extension_v17 evaluate `
  --repository-root . --input <OWNER_ROOT>/budget-input.v17.json `
  --receipt-id <a1.2-whole-workload-budget-extension-<attempt>-v17>
```

v12 provider template ใช้ได้เฉพาะตรวจรูปแบบ identity/quote ที่ไม่ขัดกับ v17
extension; ห้ามใช้ค่า TTL `6h` historical เป็น admission input. ห้ามเก็บ raw
provider payload ทั้งก้อน ตรวจและบันทึกเฉพาะ:

- instance/provider identity, `running/verified`, host/machine identity และ
  `linux/amd64`
- GPU เป็น RTX 3090 จำนวน 4 ใบ และ memory ต่อใบตาม contract
- image/runtime revision ตรงกับ frozen runtime
- fresh current price และ all-fee components (GPU, disk, storage, tax/other)
- whole-workload estimate รวม attempt ก่อนหน้าแล้วไม่เกิน common `$55`, A1 `$60`, campaign `$150`
- TTL จาก provision ไม่เกิน 40 ชั่วโมง และ watchdog deadline คำนวณได้
- management authority/destroy capability อยู่ในสถานะ
  `READY_NOT_EXECUTED` หรือ `OWNER_MANUAL_DASHBOARD_DESTROY_READY`

ห้ามเรียก destroy ในขั้น admission ห้ามคัดลอก TFA, token, credential หรือ raw
provider JSON ลง Git/receipt

**Checkpoint 3:** `provider-admission.receipt` มี `PASS`, fresh timestamp,
identity hash, all-fee quote hash, budget/TTL facts และ
`provider_destroy_capability` ตรง mode หาก quote หมดอายุหรือราคาเกินให้หยุดและ
ขอ Owner decision เรื่อง instance/budget ใหม่ หาก fallback ไม่มี dashboard hash,
all-fee rate หรือ manual destroy readiness ให้หยุดก่อน measured work

### ขั้นที่ 4: SSH, runtime และ protected-boundary adoption

1. ตรวจ host key จาก Owner connection file และทำ SSH probe แบบ BatchMode:

```powershell
ssh -i $SSH_KEY -p $SSH_PORT -o BatchMode=yes -o StrictHostKeyChecking=yes root@$SSH_HOST "hostname; uname -m; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits"
```

หาก Owner ต้องรัน probe เอง ให้ SSH เข้า instance แล้วรัน bash นี้; ส่งกลับเฉพาะ
JSON aggregate-safe และ hash ห้ามส่ง environment หรือ credential:

```bash
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import hashlib, json, platform, socket, subprocess, torch
rows = subprocess.check_output(
    ["nvidia-smi", "--query-gpu=uuid,name,memory.total", "--format=csv,noheader,nounits"],
    text=True,
).splitlines()
gpus = []
for row in rows:
    uuid, name, memory = [part.strip() for part in row.split(",", 2)]
    gpus.append({"uuid": uuid, "name": name, "memory_mib": int(memory)})
print(json.dumps({
    "hostname": socket.gethostname(),
    "arch": platform.machine(),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "gpu_count": len(gpus),
    "gpu_names_match": all(x["name"] == "NVIDIA GeForce RTX 3090" for x in gpus),
    "gpu_memory_min_mib": min(x["memory_mib"] for x in gpus),
    "gpu_uuid_set_sha256": hashlib.sha256(
        "\n".join(sorted(x["uuid"] for x in gpus)).encode()
    ).hexdigest(),
}, sort_keys=True))
PY
```

2. ตรวจว่าผลเป็น `linux/amd64`, RTX 3090 x4, 24576 MiB ต่อใบ และ UUID set
   ตรง provider identity receipt; ตรวจ disk/remote root ว่างและเป็น path ใหม่
3. ตรวจ runtime Python/CUDA, installed wheelhouse/model manifests และ frozen
   bundle hashes บน remote โดยตั้ง `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
   `PIP_NO_INDEX=1`; ห้าม download model/dependency ระหว่าง measured run
4. ตรวจ protected compiler receipt, transfer receipt, all 25 compiled bindings,
   split commitment และ token-map hash จาก Owner-local store โดยไม่เปิดค่า
5. รัน focused runtime/artifact/protected scans และสร้าง
   `execution-adoption.receipt` ที่ bind attempt, provider receipt, SSH/runtime
   identity, bundle/tree/hash และ `launch_allowed=false` จนทุก field PASS

**Checkpoint 4:** SSH identity, GPU/runtime, frozen hashes, protected boundary
และ adoption ทุกข้อเป็น `PASS`; ถ้าหนึ่งข้อ drift ให้เก็บ aggregate-safe marker,
หยุด และไม่เริ่ม worker

### ขั้นที่ 5: watchdog/TTL และ lifecycle readiness

เริ่ม watchdog ก่อนส่ง input และปล่อยให้ถือ advisory lock ตลอด run ใช้
`scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1` พร้อม `INSTANCE_ID`, SSH
host/port/key, Owner connection file, output directory, TTL deadline, expected
hostname/identity/GPU commitments และ live all-fee hourly rate ที่ bind ใน
provider admission receipt; A1 hard stop คือ `$60`. Mode หลักส่ง
`-ProviderObservationMode AuthenticatedCli -VastCliPath <path>`; fallback ส่ง
`-ProviderObservationMode OwnerDashboardSsh -OwnerDashboardTotalHourlyUsd <rate>
-OwnerDashboardEvidenceSha256 <sha256> -OwnerManualDestroyReady` โดยไม่ส่ง
`VastCliPath`
`IntervalSeconds` อยู่ในช่วง 10-300 ตรวจ heartbeat และ receipt เป็นระยะ 30 วินาที

**Checkpoint 5:** watchdog เป็น `PASS`, lock ถูกถือโดย process เดียว, TTL มีเวลา
พอสำหรับ 25 cells + safe return + closeout และ provider destroy dry-run พร้อม
ห้ามใช้ `os.kill(pid, 0)` บน Windows ตรวจ liveness ด้วย lock/process identity
ตาม runbook

### ขั้นที่ 6: สร้าง Owner-local input manifest

1. ใช้ `build_input_manifest()` ใน
   `src/myis_research/armindex/a1_2_owner_local_input_manifest_v16.py`
   ผ่าน adapter/harness ที่มีอยู่ ห้ามเขียน protected rows ลง manifest
2. bind exactly 25 cells, 150 work tokens, all five gates เป็น `PASS`, paths
   เป็น safe relative paths และทุก file SHA-256 ตรง
3. เขียน manifest ไป `OWNER_ROOT` หรือ `EXTERNAL_ROOT` ไม่ใช่ repository
4. ตรวจ manifest self-hash และ schema ก่อน launch

**Checkpoint 6:** manifest `status=READY`, `cells=25`, `work_token_count=150`,
`manifest_sha256` ตรวจซ้ำได้ และไม่มี forbidden path

### ขั้นที่ 7: execution adoption แล้วจึงเปิด measured work

ตรวจซ้ำว่า provider-admission, execution-adoption, watchdog/TTL,
protected-boundary และ frozen-bindings receipts เป็น `PASS` ใน attempt เดียว
จากนั้น append ledger checkpoint `MEASURED_EXECUTION_AUTHORIZED`. ก่อนจุดนี้
ห้ามเรียก launcher ที่ทำ retrieval จริง

**Checkpoint 7:** มี receipt สองใบและ ledger transition ครบ; นี่เป็นจุดเดียวที่
เปลี่ยนจาก preparation เป็น measured execution

### ขั้นที่ 8: stage และรัน common screen 25/25

1. ส่ง bundle, manifest และเฉพาะ model/dependency assets ที่ Owner เตรียมไว้ไป
   `REMOTE_ROOT`; verify hash ก่อน extract และใช้ remote root ใหม่ทุก attempt
2. รัน ARM-01 บน Owner-local CPU และ ARM-02..ARM-05 บน GPU คนละหนึ่งใบตาม
   `a1_2_remote_measured_launcher_v16.py`; ใช้ `local-arm01`, `remote-launch`,
   `remote-wait`, `remote-collect` ตาม signatures ใน module และ `runbook` เป็น
   source of truth สำหรับ argument จริง
3. ตั้ง environment allowlist/offline flags และเขียน stdout/stderr ลงไฟล์
   Owner-local หรือ remote attempt root; ห้ามพิมพ์ ranking/query IDs ใน chat
4. ตรวจ heartbeat, worker exit, checkpoint count, charge และ TTL อย่างน้อยทุก
   30 วินาที; ห้ามแก้ source หรือ restart ด้วย bundle คนละ hash กลาง run

**Checkpoint 8:** ทุก worker ใช้ attempt/bundle/manifest เดียวกัน และ ledger มี
progress aggregate เช่น `ARM-01=5/5`; partial result ยังไม่มี authority

### ขั้นที่ 9: recovery และ hard stop ระหว่างวัด

เมื่อ SSH probe ล้ม, worker fail, watchdog hard-stop, budget/TTL ไม่ปลอดภัย,
identity/hash/runtime drift หรือ protected scan fail ให้ทำตามลำดับ:

1. หยุดการส่งงานใหม่และให้ lifecycle cancel/reap siblings อย่างควบคุม
2. เก็บ failure marker, checkpoint count, exit class, watchdog reason และ
   hashes แบบ aggregate-safe
3. เก็บ remote attempt root และ allowlisted outputs ไว้ ห้ามลบ/overwrite ก่อน
   safe return หรือ audit เสร็จ
4. ห้าม merge cells จาก attempt อื่น, ห้าม evaluate/promotion และห้าม claim A1
5. แจ้ง Owner เฉพาะ blocker เดียวที่ทำให้ gate ไม่ผ่าน; การ retry ทุกครั้งต้อง
   สร้าง `ATTEMPT_ID` ใหม่, remote root ใหม่, ledger/checkpoint chain ใหม่,
   bundle/manifest/admission/adoption receipts ใหม่ และห้าม resume หรือรวม cell
   จาก attempt ที่ failed closed แม้แก้เฉพาะ infrastructure
6. สร้าง aggregate-safe failure audit, update read-model และ mark generated
   A1/A1.2 report เป็น failed-closed ก่อน terminal report; sync เฉพาะ projection
   ที่เปลี่ยนและห้ามทำ historical report sweep

`24/25` หรือจำนวนอื่นที่น้อยกว่า 25 ถือว่าไม่สำเร็จเสมอ แม้ metric บางส่วนดูดี

### ขั้นที่ 10: safe return และ validation

หลัง `25/25` เท่านั้น ให้ `finalize` launcher สร้าง lifecycle checkpoints,
teardown proof และ safe-return archive โดย bind transfer manifest, split
commitment, token-map และ checkpoint hash ของทุก cell จาก attempt เดียว:

```powershell
uv run --no-sync python -m myis_research.armindex.a1_2_remote_measured_launcher_v16 finalize `
  --manifest <OWNER_MANIFEST> --lifecycle-root <LIFECYCLE_ROOT> `
  --combined-runner-root <COMBINED_ROOT> --archive <EXTERNAL_ROOT>/safe-return.tar.gz `
  --attempt-id <ATTEMPT_ID> --executor-sha256 <EXECUTOR_SHA256> `
  --transfer-manifest-sha256 <TRANSFER_HASH> `
  --split-commitment-sha256 <SPLIT_HASH> `
  --ephemeral-token-map-sha256 <TOKEN_MAP_HASH> `
  --adoption-receipt <ADOPTION_RECEIPT> `
  --arm-output ARM-01=<ARM01_ROOT> --arm-output ARM-02=<ARM02_ROOT> `
  --arm-output ARM-03=<ARM03_ROOT> --arm-output ARM-04=<ARM04_ROOT> `
  --arm-output ARM-05=<ARM05_ROOT>
```

ตรวจ `validate_production_safe_return()` และ archive member hashes; ต้องได้
`cells=25`, `rows=150`, `top_k=100`, teardown children reaped และ
`safe_return_status=PASS` ก่อนลบหรือปิด remote root

### ขั้นที่ 11: Owner-local evaluation และ frozen promotion

1. เปิด archive ใน Owner-local protected store เท่านั้น
2. เรียก `evaluate_safe_return()` จาก
   `a1_2_owner_local_evaluator_v16.py` ผ่าน harness ที่มีอยู่ โดย output เป็น
   aggregate-only receipts 25 รายการ
3. ตรวจ `OUT Recall@100`, `OUT nDCG@100`, `OUT nDCG@10`, latency/cost และ
   failure/tie rates ตาม schema; ห้าม export qrels, membership, query IDs,
   rankings หรือ per-query outcomes
4. ใช้ promotion rule ที่ freeze เท่านั้น: เรียง Recall@100, nDCG@100,
   latency, cost, simplicity และ reject exact tie; promote ได้ไม่เกิน 3 arms
5. หลัง evaluator closeout ผ่าน ให้สร้าง
   `campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/<ATTEMPT_ID>.summary.v16.json`
   ด้วย `a1_2_measured_result_summary_v16`; summary นี้เป็น numeric source ของ
   รายงาน A1 โดยมีเฉพาะ aggregate ต่อ arm และ hash lineage ห้ามคัดลอก metric
   ไปแก้ด้วยมือในเอกสารอื่น

**Checkpoint 11:** มี 25 aggregate result receipts, promotion receipt self-hash
ผ่าน, measured-result summary self-hash/lineage ผ่าน, `scientific_authority=true`
เฉพาะ aggregate result และไม่มี protected field ใน projection หาก evaluator
ไม่ผ่านให้หยุด ไม่ซ่อมตาม outcome

### ขั้นที่ 11E: สร้าง EDA สำหรับ presentation และ journal

1. หลัง measured-result summary ผ่านเท่านั้น ให้รัน
   `a1_2_cell_eda_package_v16` จาก Owner-local aggregate result receipts ครบ 25
   รายการ ห้ามอ่านหรือ project raw qrels, membership, query IDs, rankings หรือ
   per-query outcomes
2. สร้าง canonical EDA JSON หนึ่งไฟล์, CSV ครบ 25 cells, quality figure แบบ
   PNG/SVG, efficiency figure แบบ PNG/SVG และคู่มือภาษาไทยสำหรับ Owner
3. Quality figure แสดง `OUT Recall@100`, `OUT nDCG@100`, `OUT nDCG@10` บนแกน
   0-1 พร้อมตัวเลขในทุก cell; efficiency figure แสดง search p95, wall time และ
   peak VRAM โดยระบุชัดว่าเป็น descriptive diagnostics ไม่ใช่ promotion override
4. ตารางแต่ละ cell ต้องมี arm/program labels, frozen metrics, latency,
   throughput, wall time, RAM/VRAM/index size, replay/retry/failure และ receipt
   hashes โดยไม่มีตัวอย่างข้อมูลจริงหรือ identifier จาก protected store
5. mirror exact EDA artifacts พร้อม manifest/SHA-256 ไปยัง Vast A1 remote root
   ใต้ `handoff/a1-journal-eda/<ATTEMPT_ID>/` โดยไม่เขียนทับ measured outputs

**Checkpoint 11E:** EDA package self-hash ผ่าน, artifacts ทุกไฟล์ hash ตรง,
CSV มี 25 rows, figures render ไม่ว่างและอ่านได้, Thai report ไม่มี mojibake,
protected scan ผ่าน และ remote mirror ตรงกับ local exact bytes

### ขั้นที่ 11A: สร้าง A1 baseline handoff สำหรับ A2 โดยยังไม่เปิด A2

1. ทำตาม `control/runbooks/A1_PROVIDER_REUSE_AND_A2_DATA_HANDOFF_V16.md`
2. คัดลอก exact bytes เฉพาะ safe-return archive, aggregate receipts 25 รายการ,
   promotion receipt และ evaluator-closeout receipt ไป Owner-local root
   `04_Owner_Stores/armindex-a2/a1-baseline-safe-return/<ATTEMPT_ID>/`
3. สร้าง `handoff-manifest.v16.json` ที่มี relative paths, sizes และ SHA-256;
   manifest ต้องมี `a2_execution_authorized=false`
4. ห้ามดึง embeddings, vector indexes, caches, tensor checkpoints, raw inputs,
   logs, environment dumps, provider payloads หรือ model weights ซ้ำ
5. ตรวจผ่าน SSH ว่า A1 remote root และ output ต้นฉบับยังอยู่บน instance ห้ามลบ
   หรือเขียนทับ และห้ามใช้ A1 root เป็น A2 output root
6. mirror handoff package ที่ผ่าน local validation ไปยัง
   `<REMOTE_A1_ROOT>/handoff/a1-baseline/<ATTEMPT_ID>/` แล้วตรวจให้ครบ `29/29`
   files และ SHA-256 ตรง; ห้าม upload protected evaluator inputs

**Checkpoint 11A:** handoff มี source files `28` รายการและ self-hash ผ่าน,
forbidden artifact classes ถูก exclude, remote mirror `29/29` hash ตรง, remote
A1 artifacts ยังอยู่ และ A2 measured counters ยังเป็นศูนย์

### ขั้นที่ 12: A1 closeout และ provider disposition

1. สร้างหรือ mark generated Phase/Task report หนึ่งฉบับจาก read-model เดียว
   เมื่อจบหรือ fail-closed พร้อม
   evidence class, claim boundary, metrics pointers และ next action
2. ตรวจ artifact graph/checksum/protected-path scan, focused tests, scoped Ruff,
   report validation/sync เฉพาะ projection ที่เปลี่ยน และ `git diff --check`
3. commit/push aggregate-safe evidence, receipts, hashes, goal/runbook/ledger
   ที่จำเป็นเท่านั้น; ห้าม commit protected archive หรือ credentials
4. Owner decision 2026-08-11 ยกเลิกการบังคับ destroy หลัง A1. หาก Owner ต้องการ
   reuse instance ให้ตรวจ provider identity/status, SSH, current all-fee quote,
   accrued A1 charge, remaining TTL, watchdog และ management authority ซ้ำหลัง
   safe return/evaluation PASS แล้วเขียน aggregate-safe provider-continuation
   receipt เป็น `REUSE_ELIGIBLE`; receipt ต้องระบุว่า A2 ยังต้องทำ fresh provider
   admission/execution adoption และต้องใช้ remote root ใหม่
5. `REUSE_ELIGIBLE` อนุญาตเพียงให้คง instance live ระหว่างส่งต่องาน ไม่อนุญาตให้
   เริ่ม A2 measured work, reuse A1 adoption receipt, เขียนทับ A1 remote root หรือ
   เปลี่ยน A1 scientific result หาก continuation validation ไม่ผ่าน, TTL/งบไม่พอ
   หรือ Owner ขอ destroy ให้ใช้ destruction path เดิมและบันทึก disposition ตามจริง

**Checkpoint 12:** A1 closeout receipt, push commit และ provider disposition
 (`REUSE_ELIGIBLE` หรือ `DESTROYED` ตามหลักฐานจริง)
ครบแล้วเท่านั้น จึงทำให้ A2 มีสิทธิ์วางแผนตาม campaign `D1_START_CAMPAIGN`;
การเปลี่ยน A2 จาก blocked เป็น ready ต้องมาจาก canonical receipt/read-model
และ goal refresh ไม่ใช่การแก้ตัวเลขในเอกสารนี้ และห้ามเปิด A2 ใน session นี้โดยอัตโนมัติ

## 6. รายการ artifact ที่ต้องมี

เก็บใน canonical/Owner-local ตาม schema ไม่สร้างสำเนาตัวเลขใน prose:

- `OWNER_ROOT`/`EXTERNAL_ROOT`: provider-admission, execution-adoption,
  watchdog/TTL, management dry-run, input manifest, transfer/protected
  compiler receipts, ledger/checkpoints, cell receipts, safe-return archive,
  evaluator and promotion receipts; these are Owner-local unless a schema marks
  a sanitized aggregate pointer safe for Git
- `04_Owner_Stores/armindex-a2/a1-baseline-safe-return/<ATTEMPT_ID>/`: exact
  safe-return archive, 25 aggregate receipts, promotion/evaluator-closeout และ
  `handoff-manifest.v16.json`; ห้ามสร้าง repository `data/` สำหรับ payload นี้
- Vast A1 remote root: เก็บ `current/`, `output/`, checkpoints และ artifacts เดิม
  ไว้แบบ read-only หลัง handoff จนกว่าจะมี provider disposition ใหม่
- `campaigns/armindex-multiretriever-v2/evidence/`: only validated
  aggregate-safe canonical receipts and hashes
- `campaigns/armindex-multiretriever-v2/evidence/a1.2-cell-eda/`,
  `outputs/tables/armindex/`, `outputs/figures/armindex/` และ
  `docs/operations/*CELL_EDA*_TH.md`: generated 25-cell aggregate EDA สำหรับ
  journal/presentation; numeric source ยังคงเป็น canonical JSON
- `outputs/audits/armindex/`: aggregate-safe failure/validation audits
- `obsidian_report/` and Brain projections: generated pointers/aggregates only
- `control/runbooks/` and `docs/goal/`: tracked execution instructions, not
  measured numbers

ห้ามเผยแพร่หรือ commit: qrels, membership, query IDs, raw rankings, per-query
outcomes, prompts, credentials, TFA material, SSH private key, tokens, raw
provider payloads และ model bytes

## 7. Terminal report เมื่อจบหรือถูกบล็อก

รายงานสั้นแต่ครบฟิลด์นี้:

```text
phase/task: A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.2
attempt_id: <id>
status: PASS | FAILED_CLOSED | BLOCKED
checks: provider, adoption, identity, gpu, runtime, hashes, protected, budget, ttl, watchdog, safe_return
coverage: <25/25 หรือ aggregate-safe count>
bindings: <campaign/envelope/budget/contract SHA-256>
artifacts: <receipt/hash/pointer เท่านั้น>
changed_files: <รายการ>
untouched_protected_surfaces: <รายการ>
blocker_or_decision: <หนึ่งรายการถ้ามี>
next_action: <A1 closeout หรือ Owner action ที่อนุญาต>
```

ห้ามรายงาน metric เป็น scientific result หาก `25/25`, safe return หรือ evaluator
ไม่ผ่าน และห้ามรายงานว่า A1 เสร็จเพราะมี partial cells

## 8. Final hard-stop checklist

### Owner decision: การกู้คืนบน instance เดิม

- หากเป็นปัญหา transfer, SSH หรือ process ชั่วคราว และ code/hash/runtime/input
  ไม่เปลี่ยน ให้ตรวจ checkpoint แล้ว resume attempt เดิมได้ทันที
- หากต้องแก้ code หรือ execution identity ใด ๆ ให้ปิด attempt เดิมเป็น failure
  evidence และเปิด `ATTEMPT_ID` ใหม่บน instance เดิมหลัง admission/adoption ผ่านซ้ำ
- ห้ามรวม cell จากคนละ attempt และห้ามแก้ตาม metric หรือ outcome ที่เห็น
- การกู้คืนแบบนี้ไม่อนุญาตให้ข้าม `25/25`, safe return หรือ Owner-local evaluation

หยุดทันทีเมื่อพบอย่างใดอย่างหนึ่ง: instance identity เปลี่ยน, GPU ไม่ครบ 4x
RTX3090, runtime/hash drift, quote/budget/TTL เกิน, watchdog ไม่ PASS, protected
boundary fail, adoption ไม่ PASS, worker failure, safe return ไม่ครบ 25/25,
archive checksum mismatch, evaluator/tie rule fail หรือยังไม่มี validated provider
disposition เป็น `REUSE_ELIGIBLE`/`DESTROYED` เมื่อถึง closeout gate ทุกกรณีต้อง
เก็บ aggregate-safe evidence และไม่เริ่ม A2 ต่อเอง
