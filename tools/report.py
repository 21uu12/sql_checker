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
    owners = ", ".join(result.owners) if result.owners else "未知"
    risk_level = summarize_risk(result)

    lines = [
        "# SQL 治理报告",
        "",
        f"风险等级：**{risk_level}**",
        f"解析器：{parsed.parser_engine}",
        f"涉及表：{', '.join(parsed.tables) if parsed.tables else '未识别到'}",
        f"负责人：{owners}",
        f"JOIN 数量：{parsed.join_count}",
        f"复杂度分数：{complexity.score}",
        f"审查路由：**{complexity.route}**",
        "",
        "## 路由决策",
        "",
        "- 信号：{0}".format(", ".join(complexity.reasons) if complexity.reasons else "未发现复杂 SQL 信号。"),
        "- 决策：{0}".format(
            "执行确定性本地规则。" if complexity.route == "rules" else "准备更深入的 Agent 复核，并将通过校验的 JSON 发现项合并至本报告。"
        ),
        "",
        "## 发现项",
        "",
            ]

    if not result.findings:
        message = "本地规则未发现高风险模式。"
        if agent_review:
            message = "本地规则未发现高风险模式，Agent 复核仍待执行。"
        lines.extend([message, ""])
    else:
        for finding in result.findings:
            lines.extend(
                [
                    f"### {finding.priority} {finding.code}: {finding.title}",
                    "",
                    f"- 证据：{finding.evidence}",
                    f"- 影响：{finding.impact}",
                    f"- 建议：{finding.recommendation}",
                    "",
                ]
            )

    if agent_review:
        lines.extend(
            [
                "## Agent 复核任务",
                "",
                "状态：**{0}**".format(agent_review.status),
                "",
                agent_review.reason,
                "",
                "本地原型尚未调用模型。下方为受约束的 Prompt；未来的 API 适配器会提交该 Prompt，并在返回的 JSON 通过校验后才将其写入发现项。",
                "",
                "~~~~text",
                agent_review.prompt,
                "~~~~",
                "",
            ]
        )

    lines.extend(
        [
            "## 下一步人工检查",
            "",
            "- 确认识别到的表和负责人是否正确。",
            "- 检查实际 StarRocks 查询 Profile 中的扫描字节、峰值内存和 Shuffle 数据量。",
            "- 若报告将用于通知，请在发送前审核措辞。",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_risk(result: AnalysisResult) -> str:
    priorities = {finding.priority for finding in result.findings}
    if "P1" in priorities:
        return "高"
    if "P2" in priorities:
        return "中"
    return "低"
