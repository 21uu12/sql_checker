from __future__ import annotations

from dataclasses import dataclass

from tools.sql_parser import ParsedSql


@dataclass(frozen=True)
class ComplexityAssessment:
    score: int
    route: str
    reasons: tuple[str, ...]


def assess_complexity(parsed: ParsedSql, review_mode: str = "auto") -> ComplexityAssessment:
    """Route SQL to repeatable rules or a higher-quality Agent review.

    The score is deliberately transparent: a human can tune thresholds without
    asking a model to explain why a query was considered complex.
    """
    score = 0
    reasons: list[str] = []

    if parsed.line_count > 30:
        score += 15
        reasons.append("more than 30 lines")
    if parsed.join_count:
        points = min(parsed.join_count * 8, 32)
        score += points
        reasons.append("{0} JOIN clause(s)".format(parsed.join_count))
    if parsed.cte_count:
        score += min(parsed.cte_count * 12, 36)
        reasons.append("{0} CTE(s)".format(parsed.cte_count))
    if parsed.subquery_count:
        score += min(parsed.subquery_count * 15, 45)
        reasons.append("{0} subquery/subqueries".format(parsed.subquery_count))
    if parsed.union_count:
        score += min(parsed.union_count * 15, 30)
        reasons.append("{0} UNION operation(s)".format(parsed.union_count))
    if parsed.window_function_count:
        score += 20
        reasons.append("window function")
    if parsed.case_count:
        score += 8
        reasons.append("CASE expression")

    if review_mode == "rules":
        return ComplexityAssessment(score, "rules", tuple(reasons))
    if review_mode == "agent":
        return ComplexityAssessment(score, "agent", tuple(reasons))

    route = "agent" if score >= 40 else "rules"
    return ComplexityAssessment(score, route, tuple(reasons))
