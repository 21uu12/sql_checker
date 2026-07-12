from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.analyzer import analyze_sql
from tools.metadata import TableMetadata


def load_owner_targets(path: Path) -> dict[str, tuple[dict[str, str], ...]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    targets: dict[str, tuple[dict[str, str], ...]] = {}
    for owner, item in raw.get("owners", {}).items():
        targets[owner] = tuple(item.get("notification_targets", []))
    return targets


def build_notification_payload(
    reviews: list[Any],
    source: Path,
    metadata: dict[str, TableMetadata],
    owner_targets: dict[str, tuple[dict[str, str], ...]],
    baseline_ref: str,
    report_markdown: str,
) -> dict[str, Any]:
    sql_files: list[dict[str, Any]] = []
    recipients: dict[str, list[dict[str, str]]] = {}

    for item in reviews:
        current_score = item.current.score if item.current else None
        baseline_score = item.baseline.score if item.baseline else None
        entry: dict[str, Any] = {
            "path": item.path.as_posix(),
            "change_type": item.status,
            "current_score": current_score,
            "baseline_score": baseline_score,
            "score_change": current_score - baseline_score if current_score is not None and baseline_score is not None else None,
            "owners": [],
            "findings": [],
        }
        if item.current is not None:
            result = analyze_sql((source / item.path).read_text(encoding="utf-8"), metadata)
            entry["tables"] = list(result.parsed.tables)
            entry["owners"] = list(result.owners)
            entry["route"] = item.current.route
            entry["findings"] = [
                {
                    "code": finding.code,
                    "priority": finding.priority,
                    "title": finding.title,
                    "evidence": finding.evidence,
                    "impact": finding.impact,
                    "recommendation": finding.recommendation,
                }
                for finding in result.findings
            ]
            for owner in result.owners:
                recipients.setdefault(owner, list(owner_targets.get(owner, ())))
        sql_files.append(entry)

    p1_change = sum(item.current.p1_count if item.current else 0 for item in reviews) - sum(
        item.baseline.p1_count if item.baseline else 0 for item in reviews
    )
    p2_change = sum(item.current.p2_count if item.current else 0 for item in reviews) - sum(
        item.baseline.p2_count if item.baseline else 0 for item in reviews
    )
    return {
        "schema_version": 1,
        "event_type": "sql_governance_review",
        "delivery_mode": "approval_required",
        "baseline_ref": baseline_ref,
        "summary": {
            "changed_sql_count": len(reviews),
            "p1_change": p1_change,
            "p2_change": p2_change,
            "worsened_sql_count": sum(
                1
                for item in reviews
                if item.current and item.baseline and item.current.score < item.baseline.score
            ),
        },
        "recipients": recipients,
        "sql_files": sql_files,
        "report_markdown": report_markdown,
    }
