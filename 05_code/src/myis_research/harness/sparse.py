"""Deterministic FTS5 query and schema compatibility primitives."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


TOKEN_RE = re.compile(r"[\w][\w\-_.]*", re.UNICODE)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Fts5SchemaContract:
    table_name: str
    text_column: str
    id_columns: tuple[str, ...]
    tokenizer: str = "unicode61"

    def validate(self) -> None:
        for value in (self.table_name, self.text_column, *self.id_columns):
            if not _IDENTIFIER_RE.fullmatch(value):
                raise ValueError(f"invalid SQLite identifier: {value}")
        if not self.id_columns:
            raise ValueError("FTS5 schema requires at least one ID column")
        if self.tokenizer != "unicode61":
            raise ValueError("only the frozen unicode61 tokenizer is supported")


@dataclass(frozen=True)
class Fts5SchemaInspection:
    table_name: str
    columns: tuple[str, ...]
    create_sql: str
    compatible: bool
    issues: tuple[str, ...]


APP_PASSAGE_FTS5 = Fts5SchemaContract("passages", "text", ("chunk_id", "patent_id"))
APP_DOCUMENT_FTS5 = Fts5SchemaContract("docs", "text", ("unit_id", "patent_id"))


def build_fts5_match_query(text: str, *, max_terms: int = 128) -> str:
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")
    terms: list[str] = []
    seen: set[str] = set()
    for match in TOKEN_RE.finditer(text.casefold()):
        term = match.group(0).strip("-_")
        if len(term) < 2 or term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= max_terms:
            break
    if not terms:
        return '""'
    return " OR ".join(f'"{term}"' for term in terms)


def inspect_fts5_schema(
    connection: sqlite3.Connection, contract: Fts5SchemaContract,
) -> Fts5SchemaInspection:
    contract.validate()
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (contract.table_name,),
    ).fetchone()
    create_sql = "" if row is None or row[0] is None else str(row[0])
    columns = tuple(
        str(item[1])
        for item in connection.execute(f'PRAGMA table_info("{contract.table_name}")').fetchall()
    )
    issues = []
    if "using fts5" not in create_sql.casefold():
        issues.append("table is not an FTS5 virtual table")
    expected = (contract.text_column, *contract.id_columns)
    if columns != expected:
        issues.append(f"columns {columns} do not match {expected}")
    if contract.tokenizer not in create_sql.casefold():
        issues.append(f"tokenizer {contract.tokenizer} is not declared")
    return Fts5SchemaInspection(
        contract.table_name, columns, create_sql, not issues, tuple(issues)
    )


def inspect_fts5_database(path: Path, contract: Fts5SchemaContract) -> Fts5SchemaInspection:
    uri = f"file:{quote(path.resolve().as_posix(), safe='/:')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        return inspect_fts5_schema(connection, contract)
    finally:
        connection.close()


def assert_fts5_compatible(
    connection: sqlite3.Connection, contract: Fts5SchemaContract,
) -> Fts5SchemaInspection:
    inspection = inspect_fts5_schema(connection, contract)
    if not inspection.compatible:
        raise ValueError("; ".join(inspection.issues))
    return inspection
