"""ArmIndex retrieval-arm registry and fixture adapters."""

from .base import ArmCapabilities, ArmUnavailableError, FamilyHit, FamilyRanking
from .bm25 import BM25FixtureAdapter, BM25FixtureIndex, FIXTURE_BACKEND_ID
from .registry import ARM_IDS, ArmRegistry, UnavailableDenseAdapter

__all__ = [
    "ARM_IDS",
    "ArmCapabilities",
    "ArmRegistry",
    "ArmUnavailableError",
    "BM25FixtureAdapter",
    "BM25FixtureIndex",
    "FIXTURE_BACKEND_ID",
    "FamilyHit",
    "FamilyRanking",
    "UnavailableDenseAdapter",
]
