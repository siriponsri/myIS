"""Deterministic CPU-only ARM-01 adapter backed by the frozen bm25s package."""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_sha256


TOKEN_PATTERN = re.compile(r"(?u)\b\w+\b")
TOKENIZER_ID = "unicode_nfkc_casefold_word_v1"
BACKEND_ID = "bm25s_0.3.10_lucene_numpy_v1"


def tokenize(text: str) -> tuple[str, ...]:
    """Normalize Unicode without stopword removal or stemming."""

    normalized = unicodedata.normalize("NFKC", str(text)).casefold()
    return tuple(TOKEN_PATTERN.findall(normalized))


@dataclass
class BM25sIndex:
    retriever: Any
    document_ids: tuple[str, ...]
    families_by_document: Mapping[str, str]
    index_sha256: str


class BM25sAdapter:
    """Frozen ARM-01 scorer; suitable for offline parity and Owner-local execution."""

    arm_id = "ARM-01"
    k1 = 1.2
    b = 0.75
    method = "lucene"
    backend = "numpy"
    csc_backend = "numpy"

    def build_index(self, documents: Sequence[Mapping[str, Any]]) -> BM25sIndex:
        import bm25s

        rows = [dict(row) for row in documents]
        for row in rows:
            if set(row) != {"doc_id", "family_id", "text"}:
                raise ValueError("documents must contain exactly doc_id, family_id, text")
        document_ids = tuple(str(row["doc_id"]) for row in rows)
        if len(document_ids) != len(set(document_ids)):
            raise ValueError("document IDs must be unique")
        tokenized = [list(tokenize(str(row["text"]))) for row in rows]
        retriever = bm25s.BM25(
            k1=self.k1,
            b=self.b,
            method=self.method,
            backend=self.backend,
            csc_backend=self.csc_backend,
            dtype="float64",
            int_dtype="int32",
        )
        retriever.index(tokenized, create_empty_token=True, show_progress=False)
        commitment = {
            "backend_id": BACKEND_ID,
            "arm_id": self.arm_id,
            "k1": self.k1,
            "b": self.b,
            "method": self.method,
            "backend": self.backend,
            "csc_backend": self.csc_backend,
            "tokenizer_id": TOKENIZER_ID,
            "documents": [
                {
                    "doc_id": str(row["doc_id"]),
                    "family_id": str(row["family_id"]),
                    "tokens": tokens,
                }
                for row, tokens in zip(rows, tokenized, strict=True)
            ],
        }
        return BM25sIndex(
            retriever=retriever,
            document_ids=document_ids,
            families_by_document={
                str(row["doc_id"]): str(row["family_id"]) for row in rows
            },
            index_sha256=canonical_sha256(commitment),
        )

    def search(
        self,
        index: BM25sIndex,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[tuple[str, str, float]]:
        if limit is not None and (isinstance(limit, bool) or limit < 1):
            raise ValueError("limit must be a positive integer or None")
        query_tokens = sorted(set(tokenize(query)))
        if not query_tokens or not index.document_ids:
            return []
        documents, scores = index.retriever.retrieve(
            [query_tokens],
            corpus=list(index.document_ids),
            k=len(index.document_ids),
            sorted=False,
            show_progress=False,
        )
        rows: list[tuple[str, str, float]] = []
        for raw_document_id, raw_score in zip(documents[0], scores[0], strict=True):
            document_id = str(raw_document_id)
            score = float(raw_score)
            if not math.isfinite(score):
                raise ValueError("bm25s score must be finite")
            if score > 0.0:
                rows.append((document_id, index.families_by_document[document_id], score))
        rows.sort(key=lambda item: (-item[2], item[0]))
        return rows if limit is None else rows[:limit]


def adapter_lock_material() -> dict[str, Any]:
    """Return the deterministic adapter configuration used by A1.2 contracts."""

    return {
        "arm_id": "ARM-01",
        "backend_id": BACKEND_ID,
        "package": "bm25s==0.3.10",
        "k1": 1.2,
        "b": 0.75,
        "method": "lucene",
        "backend": "numpy",
        "csc_backend": "numpy",
        "dtype": "float64",
        "int_dtype": "int32",
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer": {
            "normalization": "NFKC",
            "case": "casefold",
            "pattern": r"(?u)\b\w+\b",
            "stopwords": False,
            "stemming": False,
            "query_term_deduplication": True,
        },
        "zero_score_rows": "filtered",
        "tie_break": "stable_document_id_lexical",
        "network_required": False,
        "gpu_required": False,
    }
