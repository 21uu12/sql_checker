from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TableMetadata:
    name: str
    owner: str
    partition_columns: tuple[str, ...]
    row_count: int | None = None
    notes: str = ""


def load_table_metadata(path: Path) -> dict[str, TableMetadata]:
    if not path.exists():
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))
    tables: dict[str, TableMetadata] = {}
    for item in raw.get("tables", []):
        table = TableMetadata(
            name=item["name"].lower(),
            owner=item.get("owner", "unknown"),
            partition_columns=tuple(col.lower() for col in item.get("partition_columns", [])),
            row_count=item.get("row_count"),
            notes=item.get("notes", ""),
        )
        tables[table.name] = table
    return tables
