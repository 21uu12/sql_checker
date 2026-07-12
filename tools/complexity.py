from __future__ import annotations

from dataclasses import dataclass

from tools.sql_parser import ParsedSql


@dataclass(frozen=True)
class ComplexityAssessment:
    score: int
    route: str
    reasons: tuple[str, ...]


def assess_complexity(parsed: ParsedSql, review_mode: str = "auto") -> ComplexityAssessment:
    """将 SQL 路由到可重复执行的规则审查或更深入的 Agent 复核。

    分数设计为透明可解释，人工可调整阈值，无需让模型解释查询为何被判定为复杂。
    """
    score = 0
    reasons: list[str] = []

    if parsed.line_count > 30:
        score += 15
        reasons.append("超过 30 行")
    if parsed.join_count:
        points = min(parsed.join_count * 8, 32)
        score += points
        reasons.append("{0} 个 JOIN 子句".format(parsed.join_count))
    if parsed.cte_count:
        score += min(parsed.cte_count * 12, 36)
        reasons.append("{0} 个 CTE".format(parsed.cte_count))
    if parsed.subquery_count:
        score += min(parsed.subquery_count * 15, 45)
        reasons.append("{0} 个子查询".format(parsed.subquery_count))
    if parsed.union_count:
        score += min(parsed.union_count * 15, 30)
        reasons.append("{0} 个 UNION 操作".format(parsed.union_count))
    if parsed.window_function_count:
        score += 20
        reasons.append("窗口函数")
    if parsed.case_count:
        score += 8
        reasons.append("CASE 表达式")

    if review_mode == "rules":
        return ComplexityAssessment(score, "rules", tuple(reasons))
    if review_mode == "agent":
        return ComplexityAssessment(score, "agent", tuple(reasons))

    route = "agent" if score >= 40 else "rules"
    return ComplexityAssessment(score, route, tuple(reasons))
