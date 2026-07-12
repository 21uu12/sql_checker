from __future__ import annotations

from typing import Optional

from tools.analyzer import AnalysisResult
from tools.complexity import ComplexityAssessment
from tools.llm_reviewer import AgentReview


def render_report(
    result: AnalysisResult,
    complexity: ComplexityAssessment,
    agent_review: Optional[AgentReview] = None,
) -> str:
    parsed = result.parsed
    owners = ", ".join(result.owners) if result.owners else "unknown"
    risk_level = summarize_risk(result)

    lines = [
        "# SQL Governance Report",
        "",
        f"Risk level: **{risk_level}**",
        f"Parser: {parsed.parser_engine}",
        f"Tables: {', '.join(parsed.tables) if parsed.tables else 'none detected'}",
        f"Owners: {owners}",
        f"Join count: {parsed.join_count}",
        f"Complexity score: {complexity.score}",
        f"Review route: **{complexity.route}**",
        "",
        "## Routing Decision",
        "",
        "- Signals: {0}".format(", ".join(complexity.reasons) if complexity.reasons else "No complex SQL signals detected."),
        "- Decision: {0}".format(
            "Run deterministic local rules." if complexity.route == "rules" else "Prepare a higher-quality Agent review, then merge validated JSON findings into this report."
        ),
        "",
        "## Findings",
        "",
            ]

    if not result.findings:
        message = "No high-risk patterns were detected by the local rules."
        if agent_review:
            message = "No high-risk patterns were detected by the local rules. Agent review is still pending."
        lines.extend([message, ""])
    else:
        for finding in result.findings:
            lines.extend(
                [
                    f"### {finding.priority} {finding.code}: {finding.title}",
                    "",
                    f"- Evidence: {finding.evidence}",
                    f"- Impact: {finding.impact}",
                    f"- Recommendation: {finding.recommendation}",
                    "",
                ]
            )

    if agent_review:
        lines.extend(
            [
                "## Agent Review Task",
                "",
                "Status: **{0}**".format(agent_review.status),
                "",
                agent_review.reason,
                "",
                "The local prototype has not called a model. Its bounded prompt is below; a future API adapter will submit it and validate the returned JSON before it appears as findings.",
                "",
                "~~~~text",
                agent_review.prompt,
                "~~~~",
                "",
            ]
        )

    lines.extend(
        [
            "## Next Human Check",
            "",
            "- Confirm whether the detected tables and owners are correct.",
            "- Check the actual StarRocks query profile for scan bytes, peak memory, and shuffle volume.",
            "- If this report will become a notification, review the wording before sending.",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_risk(result: AnalysisResult) -> str:
    priorities = {finding.priority for finding in result.findings}
    if "P1" in priorities:
        return "High"
    if "P2" in priorities:
        return "Medium"
    return "Low"
