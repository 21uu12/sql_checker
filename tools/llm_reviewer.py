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
    """Prepare a bounded Agent task; no model is called by this local prototype."""
    prompt = """You are a senior StarRocks SQL governance reviewer.

Review the SQL below. Return JSON only, with this schema:
{{
  \"findings\": [
    {{
      \"code\": \"LLM001\",
      \"priority\": \"P1|P2|P3\",
      \"title\": \"short title\",
      \"evidence\": \"specific SQL evidence\",
      \"impact\": \"likely performance or correctness impact\",
      \"recommendation\": \"concrete and safe recommendation\"
    }}
  ],
  \"questions_for_human\": [\"facts that must be confirmed from metadata or query profile\"]
}}

Do not claim a partition, distribution key, row count, or query profile metric unless it is present in the input.

Complexity score: {score}
Tables: {tables}
SQL:
```sql
{sql}
```""".format(score=complexity.score, tables=", ".join(parsed.tables) or "unknown", sql=sql.strip())

    return AgentReview(
        status="pending_model_call",
        reason="Automatic routing selected Agent review for a complex SQL statement.",
        prompt=prompt,
    )
