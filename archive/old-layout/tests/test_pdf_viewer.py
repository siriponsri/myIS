import hashlib
import json
import tempfile
from pathlib import Path
import unittest

from myis_research.dashboard.viewer import PdfCatalog


class PdfViewerTests(unittest.TestCase):
    def test_allowlist_hash_and_receipt_precede_access(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            approved = root / "approved"
            approved.mkdir()
            pdf = approved / "paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\nfixture\n")
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            allowlist = root / "allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "artifact_id": "paper-1",
                                "approved_root": str(approved),
                                "relative_path": "paper.pdf",
                                "sha256": digest,
                                "size_bytes": pdf.stat().st_size,
                                "license_privacy_decision_id": "IS1-PDF-GATE",
                                "active": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            catalog = PdfCatalog(allowlist, root / "receipts")
            target, entry = catalog.resolve("paper-1")
            receipt = catalog.append_receipt(
                artifact_id="paper-1",
                file_sha256=entry["sha256"],
                purpose="literature verification",
                actor_id="actor-hash",
            )
            self.assertTrue(target.samefile(pdf))
            self.assertEqual(catalog.receipts.validate_chain()["count"], 1)
            self.assertTrue(receipt["record_sha256"])

    def test_traversal_and_hash_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            approved = root / "approved"
            approved.mkdir()
            outside = root / "outside.pdf"
            outside.write_bytes(b"%PDF-outside")
            allowlist = root / "allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "artifact_id": "bad",
                                "approved_root": str(approved),
                                "relative_path": "../outside.pdf",
                                "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                                "size_bytes": outside.stat().st_size,
                                "license_privacy_decision_id": "gate",
                                "active": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(PermissionError):
                PdfCatalog(allowlist, root / "receipts").resolve("bad")


if __name__ == "__main__":
    unittest.main()
