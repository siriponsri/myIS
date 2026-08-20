# Terra XHigh handoff: Canonical Owner Data Bundle A2-A6

ตรวจ `04_Owner_Stores/armindex/data-bundle/<bundle-id>/` และ receipt ก่อนทำงานทุกครั้ง ใช้ canonical source contract `control/assets/dapfam-p1-source.v1.json`, parent split seed `42`/algorithm `sha256-seed-colon-id-lexical-v1`, `Train=250`, `REP-DEV=150`, `HDEV-100=100`, `Selection=125`, `Final=872`, และ A6 full DAPFAM `45,336` rows เท่านั้น

1. ตรวจ source manifest, parent split, membership/split self-hash, disjointness/counts, A4 HDEV receipt, path boundary, symlink rejection และ receipt hash โดยไม่เผยแพร่ query IDs, qrels, membership, rankings หรือ raw corpus
2. ตรวจ gate states แยกกัน: Train/REP/HDEV `PREPARED_HASH_BOUND`; Selection `SEALED_PRE_MEASUREMENT` + `PENDING_PAIRED_VECTORS`; Final `SEALED_PRE_D2` + `PENDING_A5_D2`; A6 `SOURCE_HASHED` + `PENDING_A5_FROZEN_WINNER`. ต้องคง `selection_accesses=0`, `final_accesses=0`, `execution_permitted=false`
3. หาก Selection paired vectors/evaluator handoff ที่ hash-bound ยังไม่มี ให้ fail-closed ห้ามสร้างจาก HDEV, old IS1, fixture หรือ shared data
4. เมื่อ predicate ครบ ให้เปิด Selection ครั้งเดียว, ตรวจ receipt และ freeze exactly two finalists: static common baseline กับ research champion
5. ทำ A5 Final-872 ด้วย fresh admission/root บน instance `47790578`; ห้าม reuse A4 root/cache/worker/partial และห้ามเปิด Final ก่อน D2 ที่ถูกต้อง
6. หลัง `PASS_A5_FINAL_CONFIRMATION` ส่ง winner เดียวไป A6 ด้วย fresh admission/root โดย bind source manifest/hash และคง claim boundary เป็น materialization/scalability เท่านั้น
7. ทำ result audit, safe-return, provider disposition, receipt/hash validation, focused tests, `ruff`, `git diff --check`, commit/push `main`, ตรวจ `HEAD == origin/main` และ clean tree

ห้ามสร้าง Selection receipt/vector, D2, Final output หรือ winner ในขั้น preparation และห้ามเปลี่ยน protocol เป็น Selection-150 หรือเพิ่ม micro-gate/controller
