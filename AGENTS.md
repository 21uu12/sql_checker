# SQL Governance Agent Instructions

You are working on a data-platform SQL governance assistant.

Primary goal:
- Help data engineers identify expensive or risky SQL patterns before sending a human-readable governance report.

Project rules:
- Do not auto-kill queries, modify production jobs, or send messages without an explicit human approval step.
- Prefer deterministic checks before LLM-style advice.
- Every report must include evidence, impact, recommendation, and priority.
- Keep domain rules in `skills/` and executable logic in `tools/`.
- Keep examples realistic but sanitized. Do not include company secrets, real user identifiers, or private table names unless explicitly approved.

Review order for SQL:
1. Scan range and partition pruning risk.
2. `SELECT *` or overly wide projection.
3. Function-wrapped filter columns.
4. Join cardinality and missing join predicates.
5. Output/report clarity.

Current v0 limitation:
- This is a local prototype. It reads SQL files and static table metadata. Future versions can connect to StarRocks query logs, Google Sheets, and notification systems.
