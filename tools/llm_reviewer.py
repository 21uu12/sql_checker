from __future__ import annotations

from dataclasses import dataclass

from tools.complexity import ComplexityAssessment
from tools.sql_parser import ParsedSql


@dataclass(frozen=True)
class AgentReview:
    status: str
    reason: str
    prompt: str


def create_agent_review(sql: str, parsed: ParsedSql, complexity: ComplexityAssessment) -> AgentReview:
    """准备受约束的 Agent 任务；当前本地原型不会调用模型。"""
    prompt = """你是一名资深 StarRocks SQL 治理审查人员。

审查以下 SQL。仅返回 JSON，格式如下：
{{
  \"findings\": [
    {{
      \"code\": \"LLM001\",
      \"priority\": \"P1|P2|P3\",
      \"title\": \"简短标题\",
      \"evidence\": \"具体的 SQL 证据\",
      \"impact\": \"可能的性能或正确性影响\",
      \"recommendation\": \"具体且安全的建议\"
    }}
  ],
  \"questions_for_human\": [\"必须从元数据或查询 Profile 确认的事实\"]
}}

除非输入中已提供，否则不得断言分区、分桶键、行数或查询 Profile 指标。

复杂度分数：{score}
涉及表：{tables}
SQL：
```sql
{sql}
```""".format(score=complexity.score, tables=", ".join(parsed.tables) or "未知", sql=sql.strip())

    return AgentReview(
        status="pending_model_call",
        reason="自动路由将此复杂 SQL 分配至 Agent 复核。",
        prompt=prompt,
    )
