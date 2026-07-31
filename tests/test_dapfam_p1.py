from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc

from myis_research.dapfam_p1 import (
    _FTSRanker,
    _validate_package_shape,
    compose_tac,
    derive_split,
    iter_arrow_rows,
    load_package,
    load_source_contract,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def test_pinned_source_contract_is_offline_full_text_cpu() -> None:
    contract = load_source_contract(ROOT)
    assert contract["dataset"] == {
        "dataset_id": "datalyes/DAPFAM_patent",
        "dataset_url": "https://huggingface.co/datasets/datalyes/DAPFAM_patent",
        "revision": "a59a74ce31384165065af1823a83c6f94ccafd48",
        "license": "CC-BY-NC-SA-4.0",
        "live_fetch_allowed": False,
    }
    assert contract["protocol"]["query_view"]["fields"] == ["title_en", "abstract_en", "claims_text"]
    assert contract["protocol"]["corpus_view"]["id"] == "full_tac"
    assert contract["protocol"]["arms"]["R0-W"] == {
        "unit": "non_overlapping_full_tac_window",
        "window_tokens": 512,
        "stride_tokens": 512,
        "aggregation": "family_maxp",
    }


def test_tac_composition_and_seed42_split_are_deterministic() -> None:
    assert compose_tac({"title_en": " title ", "abstract_en": "abstract", "claims_text": " claims ", "description_en": "excluded"}) == "title\n\nabstract\n\nclaims"
    query_ids = [f"query-{index:04d}" for index in range(1247)]
    split = derive_split(reversed(query_ids))
    expected = sorted(query_ids, key=lambda value: (hashlib.sha256(f"42:{value}".encode()).hexdigest(), value))
    assert split["train"] == expected[:250]
    assert split["selection"] == expected[250:375]
    assert split["final"] == expected[375:]
    assert split["split_sha256"] == canonical_sha256({key: value for key, value in split.items() if key != "split_sha256"})
    assert not set(split["train"]) & set(split["selection"])
    assert not (set(split["train"]) | set(split["selection"])) & set(split["final"])


def test_arrow_reader_streams_selected_fields(tmp_path: Path) -> None:
    path = tmp_path / "fixture.arrow"
    table = pa.table({"query_id": ["q1", "q2"], "title_en": ["one", "two"], "ignored": [1, 2]})
    with path.open("wb") as handle:
        with ipc.new_stream(handle, table.schema) as writer:
            writer.write_table(table)
    assert list(iter_arrow_rows((path,), ("query_id", "title_en"))) == [
        {"query_id": "q1", "title_en": "one"},
        {"query_id": "q2", "title_en": "two"},
    ]


def test_fts_ranker_keeps_long_or_semantics_and_exact_family_maxp(tmp_path: Path) -> None:
    path = tmp_path / "index.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE VIRTUAL TABLE rows USING fts5(unit_id UNINDEXED, family_id UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')"
    )
    connection.executemany(
        "INSERT INTO rows VALUES (?, ?, ?)",
        [
            ("a-weak", "family-a", "alpha"),
            ("a-best", "family-a", "alpha alpha alpha beta"),
            ("b", "family-b", "beta"),
            ("c", "family-c", "gamma"),
        ],
    )
    connection.commit()
    connection.close()
    query = " ".join(["alpha", "beta", *(f"missing{index}" for index in range(20000))])
    with _FTSRanker(path, limit=100) as rank:
        result = rank(query)
    assert {row[1] for row in result} == {"family-a", "family-b"}
    assert len([row for row in result if row[1] == "family-a"]) == 1
    assert result[0][0] == "a-best"


def test_package_shape_requires_exact_four_slots() -> None:
    body = {
        "schema_version": "myis.p1-package.v1",
        "package_id": "package",
        "status": "validated_structural",
        "source_commit": "a" * 40,
        "request_uri": "requests/request.json",
        "request_sha256": "b" * 64,
        "receipt_uri": "evidence/receipt.json",
        "receipt_sha256": "c" * 64,
        "source_contract_sha256": "d" * 64,
        "slots": [
            {
                "arm": arm,
                "split": split,
                "run_id": f"{arm}-{split}",
                "manifest_uri": f"campaigns/scope-autoindex-v1/manifests/{arm}-{split}.json",
                "manifest_sha256": "e" * 64,
                "validation_report_uri": f"campaigns/scope-autoindex-v1/validation-reports/{arm}-{split}.json",
                "validation_report_sha256": "f" * 64,
            }
            for arm, split in (("R0", "train"), ("R0", "selection"), ("R0-W", "train"), ("R0-W", "selection"))
        ],
    }
    body["package_sha256"] = canonical_sha256(body)
    _validate_package_shape(body)


def test_package_loader_rejects_internal_commitment_used_as_file_hash(tmp_path: Path) -> None:
    package_dir = tmp_path / "campaigns/scope-autoindex-v1/packages"
    package_dir.mkdir(parents=True)
    body = {
        "schema_version": "myis.p1-package.v1",
        "package_id": "package",
        "status": "validated_structural",
        "source_commit": "a" * 40,
        "request_uri": "missing-request.json",
        "request_sha256": "b" * 64,
        "receipt_uri": "missing-receipt.json",
        "receipt_sha256": "c" * 64,
        "source_contract_sha256": "d" * 64,
        "slots": [
            {
                "arm": arm,
                "split": split,
                "run_id": f"{arm}-{split}",
                "manifest_uri": f"missing-{arm}-{split}.manifest.json",
                "manifest_sha256": "e" * 64,
                "validation_report_uri": f"missing-{arm}-{split}.report.json",
                "validation_report_sha256": "f" * 64,
            }
            for arm, split in (("R0", "train"), ("R0", "selection"), ("R0-W", "train"), ("R0-W", "selection"))
        ],
    }
    body["package_sha256"] = canonical_sha256(body)
    path = package_dir / "package.json"
    path.write_text(__import__("json").dumps(body), encoding="utf-8")
    try:
        load_package(path, tmp_path)
    except Exception as error:
        assert "escapes the repository" in str(error)
    else:
        raise AssertionError("missing package artifacts must fail closed")
