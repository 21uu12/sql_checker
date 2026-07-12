# SQL Review Skill

Use this skill when reviewing SQL for governance risk.

Core checks:
- Projection: flag `SELECT *`.
- Scan range: every large fact table should have a bounded time or partition predicate.
- Function filters: flag predicates like `date(column) = ...`, `substr(column, ...) = ...`, or `cast(column as ...) = ...`.
- Joins: multiple joins require cardinality review, even when syntax is valid.

Severity:
- P1: likely full scan, partition pruning failure, or missing WHERE on large tables.
- P2: inefficient but usually fixable before production execution.
- P3: style or maintainability issue.
