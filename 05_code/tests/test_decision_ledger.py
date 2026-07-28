import json
import tempfile
from pathlib import Path
import unittest

from myis_research.ledger import ImmutableJsonLedger


class DecisionLedgerTests(unittest.TestCase):
    def test_symlink_ledger_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            link = root / "ledger-link"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlinks are unavailable: {error}")
            ledger = ImmutableJsonLedger(link, prior_field="prior_record_hash")
            with self.assertRaises(ValueError):
                ledger.records()

    def test_append_is_immutable_and_hash_chained(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = ImmutableJsonLedger(Path(temp), prior_field="prior_record_hash")
            first = {"decision_id": "d1", "prior_record_hash": None}
            _, first_hash = ledger.append("d1", first)
            second = {"decision_id": "d2", "prior_record_hash": first_hash}
            ledger.append("d2", second)

            self.assertEqual(ledger.validate_chain()["count"], 2)
            with self.assertRaises(FileExistsError):
                ledger.append("d2", {"decision_id": "d2", "prior_record_hash": ledger.head()})

    def test_tamper_and_stale_head_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = ImmutableJsonLedger(root, prior_field="prior_record_hash")
            _, first_hash = ledger.append("d1", {"decision_id": "d1", "prior_record_hash": None})
            with self.assertRaises(RuntimeError):
                ledger.append("stale", {"decision_id": "stale", "prior_record_hash": None})
            path = root / "d1.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["decision_id"] = "changed"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertNotEqual(first_hash, ledger.records()[0][2])


if __name__ == "__main__":
    unittest.main()
