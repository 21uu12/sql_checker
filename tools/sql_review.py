from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.analyzer import analyze_sql
from tools.complexity import assess_complexity
from tools.metadata import TableMetadata


@dataclass(frozen=True)
class SqlFileReview:
    path: Path
    score: int
    evaluation: str
    route: str
    finding_count: int
    p1_count: int
    p2_count: int


def review_sql_text(path: Path, sql: str, metadata: dict[str, TableMetadata]) -> SqlFileReview:
    result = analyze_sql(sql, metadata)
    complexity = assess_complexity(result.parsed)
    p1_count = sum(finding.priority == "P1" for finding in result.findings)
    p2_count = sum(finding.priority == "P2" for finding in result.findings)
    score = max(0, 100 - p1_count * 25 - p2_count * 10)
    return SqlFileReview(
        path=path,
        score=score,
        evaluation=evaluate_score(score),
        route=complexity.route,
        finding_count=len(result.findings),
        p1_count=p1_count,
        p2_count=p2_count,
    )


def evaluate_score(score: int) -> str:
    if score >= 90:
        return "良好"
    if score >= 70:
        return "关注"
    if score >= 40:
        return "需要复核"
    return "高风险"
