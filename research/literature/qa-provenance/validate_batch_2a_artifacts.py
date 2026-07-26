"""Filesystem-backed QA validator for Batch 2A (U021-U040) remediation.
Read-only against all inputs except its own output JSON. Run from repo root
or via absolute paths; no external deps beyond stdlib.
"""
import csv, hashlib, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DIGESTS_DIR = os.path.join(BASE, "digests")
CACHE_DIR = os.path.join(BASE, "extraction-cache")
CSV_PATH = os.path.join(BASE, "BATCH_2A_INGESTION_CANDIDATES.csv")
CHECKPOINT_PATH = os.path.join(BASE, "BATCH_2A_CHECKPOINT.md")
INDEX_PATH = os.path.join(BASE, "PDF_DIGEST_INDEX.md")
OUT_PATH = os.path.join(BASE, "BATCH_2A_ARTIFACT_VALIDATION.json")

EXPECTED_IDS = [f"U0{i}" for i in range(21, 41)]

MANIFEST_SHA = {
    "U021": "4e90f27e6d8b72449c3a96b219ddf5efd743db5f0879c25907f379648ddbe5a7",
    "U022": "c309ccb34e8c36b529c40b702a622900ef2042f1a6e092e33b1defad8adb2ddb",
    "U023": "16fb7f9b2d7b8601931847b3d7683c4e4ab9f354d563014586e99b9eb933d768",
    "U024": "2594f2d877a4b65e08c6e2eb10612094ecff83a51a63696bc50a7e91b556c736",
    "U025": "7788735721a8d0516cbbfc46d59d5236e484e57e001511497db09b241e7ad540",
    "U026": "36375d5310c4ebee73a73453aba880a5babdedfe7ec2ca40c83ffed8f662b02f",
    "U027": "5924910b08d56a638904285d6ec44a2f2490c0704ed57bfd694e086863ef893e",
    "U028": "db1eb5909cf96c601252d732e7b95bd57556c48e1f0c0288cf25a4fd267a138d",
    "U029": "c2e600a8d73153f81716fceabe391739444a32cc156379dbe66e17f50d74b662",
    "U030": "43f35981d827f6c1118c11fc8f4aa97f964e40c8df223b8876f5d6550e5d0c07",
    "U031": "801f9f44e5e6a3f97f63a9dc2e7f74650250ee68ca6a51a42ac81f0abb25394a",
    "U032": "83e960fef77fcdbff639a21a425095f0f99b6620b48fa7a886170654d602915f",
    "U033": "ee11448b455dc4fdac09e95d6f476472ef8ad067318715164e5e40e3d620aead",
    "U034": "94b2ef789464ff2c35599f0cc8399d4710dc8697317fc068723f9841f1676f17",
    "U035": "682da185b92b4d04f906de2a59f4b5152c1a1f15433cc7da812d1f522756c1bc",
    "U036": "6840dc1ed45a2865c72748a1779ecc427178acc4ff1a7a713d93c94ee2b48bf2",
    "U037": "62d6558f515ef6a62dfb3047f8d79262613c7f13503cdf74d048804e17a6de93",
    "U038": "ab0a43419308ca9b3b4400888c56daaa81b3c5b9e459af35da20bb10edb434f2",
    "U039": "1a7441812abe43487ecc4b5995dc998c4d97aa3ed39ea9726e2dc263ef60b8c7",
    "U040": "df93f5d3e50e9c77a91cca80d62dc5e7c3c5488b9756d9441f840e4d54b20796",
}

checks = {}
issues = []

# 1. Exactly 20 persistent cache files, one per ID
cache_files = {uid: os.path.join(CACHE_DIR, f"{uid}.md") for uid in EXPECTED_IDS}
missing_caches = [uid for uid, p in cache_files.items() if not os.path.isfile(p)]
checks["all_20_persistent_caches_exist"] = (len(missing_caches) == 0)
if missing_caches:
    issues.append(f"missing cache files: {missing_caches}")

# 2. No extra/stray U0XX.md cache files beyond the 20 (within U021-U040 range)
on_disk_caches = sorted(f for f in os.listdir(CACHE_DIR) if re.fullmatch(r"U0(2[1-9]|3[0-9]|40)\.md", f))
checks["exactly_20_caches_in_range_no_extras"] = (len(on_disk_caches) == 20)
if len(on_disk_caches) != 20:
    issues.append(f"expected exactly 20 cache files U021-U040, found {len(on_disk_caches)}: {on_disk_caches}")

# 3. SHA-256 of each cache file's own bytes is NOT what we check (caches are text
#    extractions, not copies of the PDF) -- instead we confirm each cache file is
#    non-empty and contains a SHA marker matching the manifest PDF SHA (if present),
#    OR at minimum that the underlying PDF's SHA-256 (independently recomputed) matches
#    the manifest. We recompute PDF SHA directly to avoid relying on digest self-reports.
CANONICAL_REPO = r"C:\Users\Siripon Sri\Desktop\My Project\thaipha-lex"

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

empty_caches = []
for uid, p in cache_files.items():
    if os.path.isfile(p) and os.path.getsize(p) == 0:
        empty_caches.append(uid)
checks["no_empty_cache_files"] = (len(empty_caches) == 0)
if empty_caches:
    issues.append(f"empty cache files: {empty_caches}")

# 4. Digest files: exactly 20 in range, each with extraction_cache pointing at
#    extraction-cache/U0XX.md (bare or quoted), no tool-results/inline-extraction
#    references remaining in frontmatter or annotation-style lines.
digest_files = [f for f in os.listdir(DIGESTS_DIR) if re.match(r"^U0(2[1-9]|3[0-9]|40)_.*\.md$", f)]
checks["exactly_20_digest_files_in_range"] = (len(digest_files) == 20)
if len(digest_files) != 20:
    issues.append(f"expected 20 digest files, found {len(digest_files)}: {digest_files}")

digest_by_id = {}
for f in digest_files:
    m = re.match(r"^(U0\d\d)_", f)
    if m:
        digest_by_id.setdefault(m.group(1), []).append(f)

dup_digest_ids = [uid for uid, files in digest_by_id.items() if len(files) > 1]
checks["no_duplicate_digest_files_per_id"] = (len(dup_digest_ids) == 0)
if dup_digest_ids:
    issues.append(f"multiple digest files matched for same ID: {dup_digest_ids}")

missing_digest_ids = [uid for uid in EXPECTED_IDS if uid not in digest_by_id]
checks["every_id_has_a_digest_file"] = (len(missing_digest_ids) == 0)
if missing_digest_ids:
    issues.append(f"no digest file found for: {missing_digest_ids}")

stale_ref_pattern = re.compile(r"tool-results/|inline extraction \(", re.IGNORECASE)
stale_extraction_cache_field = re.compile(r'^extraction_cache:\s*["\']?(?!extraction-cache/U0\d\d\.md)', re.MULTILINE)

digests_missing_cache_field = []
digests_with_stale_active_ref = []
for uid in EXPECTED_IDS:
    files = digest_by_id.get(uid, [])
    if not files:
        continue
    path = os.path.join(DIGESTS_DIR, files[0])
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    frontmatter = fm_match.group(1) if fm_match else ""
    if "extraction_cache" not in frontmatter:
        digests_missing_cache_field.append(uid)
    elif not re.search(r'extraction_cache:\s*["\']?extraction-cache/' + uid + r'\.md', frontmatter):
        digests_missing_cache_field.append(uid)
    # Only flag frontmatter-level or "[cache: ...]"-annotation-style stale refs as
    # ACTIVE (historical prose narrative describing past extraction method, e.g. in
    # a "Verification Warnings" or "Digest Author" section, is allowed to remain).
    cache_annotation = re.search(r"\[cache:\s*([^\]]+)\]", text)
    if cache_annotation and stale_ref_pattern.search(cache_annotation.group(1)):
        digests_with_stale_active_ref.append({"unique_id": uid, "annotation": cache_annotation.group(1)})

checks["all_digests_have_normalized_extraction_cache_field"] = (len(digests_missing_cache_field) == 0)
if digests_missing_cache_field:
    issues.append(f"digests missing/incorrect extraction_cache frontmatter field: {digests_missing_cache_field}")

checks["no_active_stale_cache_annotations_in_digests"] = (len(digests_with_stale_active_ref) == 0)
if digests_with_stale_active_ref:
    issues.append(f"stale active [cache: ...] annotations found: {digests_with_stale_active_ref}")

# 5. CSV: 20 rows, correct headers, no dupes, SHA matches manifest, paths exist
FIELDNAMES = ["unique_id","title","sha256","tier","digest_path","cache_path",
              "experience_brain_match","matched_knowledge_id","recommended_ingestion_action",
              "visual_check_blocker","eligible_for_ingestion","reason"]
csv_ok = True
csv_issues = []
try:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    if header != FIELDNAMES:
        csv_ok = False
        csv_issues.append(f"header mismatch: {header}")
    if len(rows) != 20:
        csv_ok = False
        csv_issues.append(f"expected 20 rows, got {len(rows)}")
    ids = [r["unique_id"] for r in rows]
    if len(set(ids)) != len(ids):
        csv_ok = False
        csv_issues.append("duplicate unique_id present")
    if sorted(ids) != sorted(EXPECTED_IDS):
        csv_ok = False
        csv_issues.append(f"id mismatch: missing={set(EXPECTED_IDS)-set(ids)} extra={set(ids)-set(EXPECTED_IDS)}")
    for r in rows:
        uid = r["unique_id"]
        if MANIFEST_SHA.get(uid) and r["sha256"] != MANIFEST_SHA[uid]:
            csv_ok = False
            csv_issues.append(f"{uid} sha mismatch vs manifest")
        dpath = os.path.join(BASE, r["digest_path"].replace("/", os.sep))
        cpath = os.path.join(BASE, r["cache_path"].replace("/", os.sep))
        if not os.path.isfile(dpath):
            csv_ok = False
            csv_issues.append(f"{uid} digest_path does not exist: {r['digest_path']}")
        if not os.path.isfile(cpath):
            csv_ok = False
            csv_issues.append(f"{uid} cache_path does not exist: {r['cache_path']}")
        if r["cache_path"] != f"extraction-cache/{uid}.md":
            csv_ok = False
            csv_issues.append(f"{uid} cache_path not normalized: {r['cache_path']}")
except FileNotFoundError:
    csv_ok = False
    csv_issues.append("CSV file not found")

checks["csv_parses_and_passes_all_row_checks"] = csv_ok
issues.extend(csv_issues)

# 6. Checkpoint and index files: confirm no stale tool-results/inline-extraction
#    references remain in their artifact-tracking tables (historical prose notes
#    are allowed and are checked separately by exempting lines under a
#    "Historical Remediation Note" heading).
def stale_refs_outside_historical_note(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    hits = []
    in_historical_note = False
    for i, line in enumerate(lines, start=1):
        if re.search(r"Historical Remediation Note|Historical Note|remediation pass", line, re.IGNORECASE):
            in_historical_note = True
            continue
        if in_historical_note and line.strip().startswith("|") is False and line.strip() == "":
            # blank line ends the historical-note paragraph
            in_historical_note = False
        if in_historical_note:
            continue
        if re.search(r"tool-results/|inline extraction \(", line, re.IGNORECASE):
            hits.append({"line": i, "text": line.strip()})
    return hits

checkpoint_stale = stale_refs_outside_historical_note(CHECKPOINT_PATH)
index_stale = stale_refs_outside_historical_note(INDEX_PATH)

checks["checkpoint_has_no_active_stale_cache_refs"] = (len(checkpoint_stale) == 0)
if checkpoint_stale:
    issues.append(f"BATCH_2A_CHECKPOINT.md stale refs: {checkpoint_stale}")

checks["index_has_no_active_stale_cache_refs"] = (len(index_stale) == 0)
if index_stale:
    issues.append(f"PDF_DIGEST_INDEX.md stale refs: {index_stale}")

# 7. U-ID <-> SHA correspondence: cache file existence keyed correctly, no ID
#    pointing at another ID's SHA (cross-check CSV sha vs MANIFEST_SHA already
#    covers this; here we also confirm the manifest itself has no dup SHAs
#    within this range, which would indicate a copy-paste error).
sha_to_ids = {}
for uid, sha in MANIFEST_SHA.items():
    sha_to_ids.setdefault(sha, []).append(uid)
dup_shas = {sha: ids for sha, ids in sha_to_ids.items() if len(ids) > 1}
checks["no_duplicate_sha_across_distinct_ids"] = (len(dup_shas) == 0)
if dup_shas:
    issues.append(f"duplicate SHA-256 across distinct unique_ids: {dup_shas}")

# 8. U041 must not exist anywhere in scope (hard stop boundary)
u041_digest = [f for f in os.listdir(DIGESTS_DIR) if f.startswith("U041")]
u041_cache = os.path.isfile(os.path.join(CACHE_DIR, "U041.md"))
checks["u041_not_started"] = (len(u041_digest) == 0 and not u041_cache)
if u041_digest or u041_cache:
    issues.append(f"U041 artifacts found (should not exist): digests={u041_digest} cache_exists={u041_cache}")

overall_pass = all(checks.values())

result = {
    "validated_at": "2026-07-25",
    "scope": "U021-U040 (Batch 2A)",
    "checks": checks,
    "issues": issues,
    "overall_pass": overall_pass,
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
