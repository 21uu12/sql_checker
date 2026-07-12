from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

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
    error: str = ""


@dataclass(frozen=True)
class CircleReview:
    source: Path
    score: Optional[int]
    evaluation: str
    sql_files: tuple[SqlFileReview, ...]


def review_sql_directory(source: Path, metadata: dict[str, TableMetadata]) -> CircleReview:
    reviews = tuple(review_sql_file(path, source, metadata) for path in find_sql_files(source))
    score = calculate_circle_score(reviews)
    return CircleReview(source=source, score=score, evaluation=evaluate_score(score), sql_files=reviews)


def find_sql_files(source: Path) -> Iterable[Path]:
    ignored_directories = {".git", ".venv", "venv", "node_modules", "outputs", "__pycache__"}
    for path in sorted(source.rglob("*.sql")):
        if not any(part in ignored_directories for part in path.relative_to(source).parts):
            yield path


def review_sql_file(path: Path, source: Path, metadata: dict[str, TableMetadata]) -> SqlFileReview:
    try:
        sql = path.read_text(encoding="utf-8")
        result = analyze_sql(sql, metadata)
        complexity = assess_complexity(result.parsed)
        p1_count = sum(finding.priority == "P1" for finding in result.findings)
        p2_count = sum(finding.priority == "P2" for finding in result.findings)
        score = max(0, 100 - p1_count * 25 - p2_count * 10)
        return SqlFileReview(
            path=path.relative_to(source),
            score=score,
            evaluation=evaluate_score(score),
            route=complexity.route,
            finding_count=len(result.findings),
            p1_count=p1_count,
            p2_count=p2_count,
        )
    except (OSError, UnicodeDecodeError) as error:
        return SqlFileReview(
            path=path.relative_to(source),
            score=0,
            evaluation="无法读取",
            route="rules",
            finding_count=0,
            p1_count=0,
            p2_count=0,
            error=str(error),
        )


def calculate_circle_score(reviews: tuple[SqlFileReview, ...]) -> Optional[int]:
    if not reviews:
        return None
    return round(sum(review.score for review in reviews) / len(reviews))


def evaluate_score(score: Optional[int]) -> str:
    if score is None:
        return "未评分"
    if score >= 90:
        return "良好"
    if score >= 70:
        return "关注"
    if score >= 40:
        return "需要复核"
    return "高风险"
